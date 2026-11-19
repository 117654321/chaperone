#!/usr/bin/env -S bash -c '"${CHAPERONE_REPO:-.}/.venv/bin/python" "$0" "$@"'
"""Large macrocycle binder design against PD-1, with RFO sequence optimisation.

Pipeline: rfd4(cyclic=True) -> rfoptimization(cyclic=True) -> af3 -> filter

Same target, chemistry and hotspots as ``cyclic-peptide-rfo``, but a 20-residue
ring instead of 12. Upstream measured head-to-tail closure over ring lengths
6-20 and got 360/360 (median 1.308 A, no length dependence), so 20 is the top of
the validated range rather than a guess.

The trade this explores: a longer ring covers more interface (a 12-residue
macrocycle reaches iptm 0.34-0.56 on this target, a 69-residue miniprotein
0.82-0.90), but every added residue also adds conformational freedom that the
closure has to hold. Whether the extra reach pays for itself is what the two
examples are meant to show side by side.

Target, chemistry and hotspot atoms come from RFD4's own cyclic-peptide example
(``docs/examples/inputs/cyclic_binders/01_PD1_head_tail_12.cif.zst``).

Two settings are not cosmetic:

* ``peptide_chain="A"`` -- RFOptimization raises unless the designed chain is
  literally named ``A``. The block defaults to this.
* ``backprop_fraction=0.0`` -- RFO's ``cyclic`` flag only reaches the Boltz
  branch. Any RF3 fraction leaves the ring unconstrained and it drifts open.

Run:
    python examples/macrocycle-binder/pipeline.py --test --local --rundir=/abs/path/macrocycle-smoke
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from blocks import Blocks
from blocks.util_blocks.filter import MetricFilter
from chaperone import ExecutionEngine, init_cli
from chaperone.engine.resolve import RuntimeArgs

SCRIPT_DIR = Path(__file__).resolve().parent
FILES_DIR = SCRIPT_DIR / "files"
TARGET_CIF = FILES_DIR / "pd1_target.cif"

# ── Macrocycle ──────────────────────────────────────────────────────────────
# 20 residues is the top of the range upstream validated for head-to-tail
# closure (360/360 over lengths 6-20).
PEPTIDE_LENGTH = 40
PEPTIDE_CHAIN = "A"
TARGET_CHAINS = ("B",)
CYCLIC_CHEMISTRY = "head_tail"

# Same side-chain atoms upstream marks on PD-1.
HOTSPOTS = {
    "B33": "CG1,CG2",              # Ile
    "B95": "CB,CG2",               # Thr
    "B97": "CB,CD1,CD2,CG",        # Leu
    "B102": "CD,CG,NE2,OE1",       # Gln
}

IDEAL_CLOSURE = 1.33
CLOSURE_TOLERANCE = 0.30


def measure_closure(cif_path: Path, chain: str = PEPTIDE_CHAIN):
    """Return (N1-CN distance, closed?) for the ring."""
    import numpy as np
    from biotite.structure.io.pdbx import CIFFile, get_structure

    atoms = get_structure(CIFFile.read(str(cif_path)), model=1)
    peptide = atoms[atoms.chain_id == chain]
    if peptide.array_length() == 0:
        return float("nan"), False

    res_ids = sorted(set(peptide.res_id))
    n_term = (peptide.res_id == res_ids[0]) & (peptide.atom_name == "N")
    c_term = (peptide.res_id == res_ids[-1]) & (peptide.atom_name == "C")
    if not (n_term.any() and c_term.any()):
        return float("nan"), False

    distance = float(np.linalg.norm(peptide.coord[n_term][0] - peptide.coord[c_term][0]))
    return distance, abs(distance - IDEAL_CLOSURE) <= CLOSURE_TOLERANCE


def parse_args(argv: list[str]):
    """Split this script's own flags from the ones absl owns.

    ``init_cli()`` parses the whole argv through absl, which rejects any flag it
    did not define -- so our flags have to be consumed first and only the rest
    handed over.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", action="store_true", help="One replicate end to end.")
    parser.add_argument("--rundir", type=Path, default=None, help="Absolute run directory.")
    parser.add_argument("--local", action="store_true", help="Run on this GPU instead of Slurm.")
    parser.add_argument("--replicates", type=int, default=8, help="Macrocycles to sample.")
    parser.add_argument("--cycles", type=int, default=3, help="RFO redesign cycles.")
    parser.add_argument("--length", type=int, default=PEPTIDE_LENGTH, help="Ring length.")
    return parser.parse_known_args(argv)


def main():
    args, remaining = parse_args(sys.argv[1:])
    # Anything we did not consume belongs to absl (`--block.param=`, `--config=`).
    init_cli(["prog", *remaining])
    replicates = 1 if args.test else args.replicates
    cycles = 1 if args.test else args.cycles

    rundir = (args.rundir or (SCRIPT_DIR / "run")).expanduser().resolve()
    engine = ExecutionEngine(rundir=rundir)
    run_args = RuntimeArgs(use_local_gpus=True) if args.local else None

    if not TARGET_CIF.is_file():
        raise SystemExit(
            f"missing target structure: {TARGET_CIF}\n"
            f"Run {FILES_DIR / 'prep_target.py'} first."
        )

    RFD4, RFO, AF3, Filter = Blocks.getall("rfd4", "rfoptimization", "af3", "filter")

    # ── 1. RFD4: build the macrocycle ──────────────────────────────────────
    design = engine.run(
        RFD4(
            inputs=str(TARGET_CIF),
            cyclic=True,
            peptide_length=args.length,
            peptide_chain=PEPTIDE_CHAIN,
            target_chains=list(TARGET_CHAINS),
            hotspots=HOTSPOTS,
            cyclic_chemistry=CYCLIC_CHEMISTRY,
            num_replicates=replicates,
            batch_size=1,
            seed=42,
            extra_overrides=["recycle_strategy=medium/front_loaded"],
        ),
        run_args=run_args,
    )

    frame = design.unpack()
    print(f"\nRFD4 produced {len(frame)} designs")
    path_column = "rfd4.path" if "rfd4.path" in frame.columns else None
    if path_column is None:
        print("  (no structure paths in this run; skipping closure measurement)")
    closed = 0
    for path in (frame[path_column].to_list() if path_column else []):
        distance, ok = measure_closure(Path(path))
        closed += ok
        print(
            f"  {Path(path).parent.name}: N1-C = {distance:.2f} A "
            f"{'closed' if ok else 'OPEN'}"
        )
    print(f"closed {closed}/{len(frame)}")

    # ── 2. RFO: redesign the sequence against a Boltz refold ───────────────
    optimized = engine.run(
        RFO(
            total_cycles=cycles,
            backprop_fraction=0.0,
            mpnn_model_type="ligand_mpnn",
            seed=42,
            cyclic=True,
        ),
        data=design,
        run_args=run_args,
    )

    # ── 3. AF3: refold and score the interface ─────────────────────────────
    # include_bonds carries the ring closure into AF3 as `bondedAtomPairs`;
    # without it AF3 folds the chain as a linear polymer. msa_json supplies
    # PD-1's precomputed MSA, without which pLDDT sits in the 30-50 range
    # regardless of design quality.
    msa_cache = FILES_DIR / ".cache" / "pd1_msa.json"
    if not msa_cache.is_file():
        print(
            f"\nWARNING: {msa_cache} missing -- AF3 will run single-sequence "
            "and pLDDT will be suppressed.\n"
            f"  python {FILES_DIR / 'prep_target.py'} --msa\n"
        )
    refolded = engine.run(
        AF3(
            diffusion_batch_size=1,
            read_most_confident_model=True,
            include_bonds=True,
            msa_json=str(msa_cache) if msa_cache.is_file() else None,
        ),
        data=optimized,
        run_args=run_args,
    )

    # ── 4. Filter ──────────────────────────────────────────────────────────
    # Same cut as the 12-residue example so the two are directly comparable.
    threshold = 0.4 if args.test else 0.5
    passed = engine.run(
        Filter(expr=f"af3.iptm >= {threshold} and af3.plddt >= 60"),
        data=refolded,
        run_args=run_args,
    )

    result = passed.unpack()
    print(f"\npassed {len(result)} / {len(refolded.unpack())}")
    if len(result):
        columns = [
            c
            for c in ("design_id", "af3.iptm", "af3.ptm", "af3.plddt", "af3.min_pae_interaction")
            if c in result.columns
        ]
        print(result[columns].to_string(index=False))

    result.to_csv(rundir / "results.csv", index=False)
    print(f"metrics: {rundir / 'results.csv'}")
    return result


if __name__ == "__main__":
    main()
