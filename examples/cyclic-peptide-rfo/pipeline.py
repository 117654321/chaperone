#!/usr/bin/env -S bash -c '"${CHAPERONE_REPO:-.}/.venv/bin/python" "$0" "$@"'
"""Cyclic peptide binder design with RFO sequence optimisation.

Pipeline: rfd4(cyclic) -> rfoptimization -> af3 -> filter

RFD4 builds a macrocyclic peptide against a hotspot patch on the target, RFO
re-designs its sequence against a Boltz-2 refold for a few cycles, AF3 refolds
the result, and a metric filter gates on interface confidence.

RFD4 has no cyclization switch and needs no cyclic template. The ring is a
`_struct_conn` covale record in the conditioned input, and the peptide chain is
placeholder residues with zeroed backbone whose sequence and coordinates are
both designed. `cyclic=True` on the rfd4 block writes that input for you.

Two constraints this script encodes, both learned the hard way:

* `peptide_chain="A"` is not cosmetic -- RFOptimization raises unless the
  designed chain is literally named A.
* RFO's `cyclic` flag only reaches the Boltz branch, so `backprop_fraction` must
  be 0.0. With any RF3 fraction the ring is unconstrained and drifts open.

Target: PD-1. The peptide length, chemistry and hotspot atoms all come from
RFD4's own cyclic-peptide example
(`docs/examples/inputs/cyclic_binders/01_PD1_head_tail_12.cif.zst`), where this
configuration closes 16/16 over 16 replicates. They are given at side-chain atom
precision because C_HOT is an atom-level condition -- naming only a residue lets
the model pick any atom of it.

Run `files/prep_msa.py` once before using this: without a target MSA, AF3 folds
PD-1 in single-sequence mode and pLDDT sits in the 30-50 range for every design,
which reads as "the design failed" when it only means AF3 had no evolutionary
signal. The same 8 designs scored iptm 0.09-0.21 / pLDDT 37-47 without the MSA
and iptm 0.32-0.77 / pLDDT 86-90 with it. The designed peptide stays MSA-free on
purpose -- a novel sequence has no homologs to find.

Run:
    python examples/cyclic-peptide-rfo/pipeline.py --test --rundir=/abs/path/cyclic-rfo-smoke
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from blocks import Blocks
from blocks.util_blocks.filter import MetricFilter
from chaperone import ExecutionEngine, init_cli
from chaperone.data.schema import SELECTIONS
from chaperone.engine.resolve import RuntimeArgs

SCRIPT_DIR = Path(__file__).resolve().parent
FILES_DIR = SCRIPT_DIR / "files"
TARGET_CIF = FILES_DIR / "pd1_target.cif"

# ── Cyclic peptide ──────────────────────────────────────────────────────────
# 12 residues and the four hotspots below are upstream's own numbers from
# `docs/examples/inputs/cyclic_binders/01_PD1_head_tail_12.cif.zst`, where this
# chemistry closes 16/16 over 16 replicates. Starting from a measured baseline
# keeps a bad result attributable to the pipeline rather than to our guesses.
PEPTIDE_LENGTH = 12
PEPTIDE_CHAIN = "A"
TARGET_CHAINS = ("B",)

# Ring chemistry. head_tail is the only one upstream measures at 100% closure
# (16/16 over 16 replicates); disulfide manages 12/16 and isopeptide 1/16 when
# the ring has no input coordinates.
CYCLIC_CHEMISTRY = "head_tail"

# PD-1 residues the peptide should engage, with the exact side-chain atoms
# upstream marks (C_HOT is an atom-level condition; a bare residue number lets
# the model pick any atom of it).
HOTSPOTS = {
    "B33": "CG1,CG2",              # Ile
    "B95": "CB,CG2",               # Thr
    "B97": "CB,CD1,CD2,CG",        # Leu
    "B102": "CD,CG,NE2,OE1",       # Gln
}

# Closure = |d - ideal| <= tolerance. Two-sided on purpose: a one-sided "under
# 2.3 A" cut scores an impossible overshoot (atoms inside each other) as success.
IDEAL_CLOSURE = 1.33
CLOSURE_TOLERANCE = 0.30


def measure_closure(cif_path: Path, chain: str = PEPTIDE_CHAIN):
    """Return (N1-CN distance, closed?) for the peptide ring."""
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
    parser.add_argument("--replicates", type=int, default=8, help="Cyclic peptides to sample.")
    parser.add_argument("--cycles", type=int, default=3, help="RFO redesign cycles.")
    parser.add_argument("--length", type=int, default=PEPTIDE_LENGTH, help="Peptide length.")
    return parser.parse_known_args(argv)


def main():
    args, remaining = parse_args(sys.argv[1:])
    # Anything we did not consume belongs to absl (`--block.param=`, `--config=`).
    init_cli(["prog", *remaining])
    replicates = 1 if args.test else args.replicates
    cycles = 1 if args.test else args.cycles

    rundir = args.rundir or (SCRIPT_DIR / "run")
    rundir = rundir.expanduser().resolve()
    engine = ExecutionEngine(rundir=rundir)
    # `--local` keeps every block on this GPU instead of submitting to Slurm.
    run_args = RuntimeArgs(use_local_gpus=True) if args.local else None

    if not TARGET_CIF.is_file():
        raise SystemExit(
            f"missing target structure: {TARGET_CIF}\n"
            f"Run examples/cyclic-peptide-rfo/files/prep_target.py first."
        )

    RFD4, RFO, AF3, Filter = Blocks.getall(
        "rfd4", "rfoptimization", "af3", "filter"
    )

    # ── 1. RFD4: build the cyclic peptide ──────────────────────────────────
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
    # The smoke-mode harness runs blocks with mocked outputs, which do not carry
    # a `rfd4.path` column. Skip the measurement there rather than crash: the
    # real value of this check is on a GPU run, where the column is present.
    path_column = "rfd4.path" if "rfd4.path" in frame.columns else None
    if path_column is None:
        print("  (no structure paths in this run; skipping closure measurement)")
    closed = 0
    for path in (frame[path_column].to_list() if path_column else []):
        distance, ok = measure_closure(Path(path))
        closed += ok
        print(f"  {Path(path).parent.name}: N1-C = {distance:.2f} A "
              f"{'closed' if ok else 'OPEN'}")
    print(f"closed {closed}/{len(frame)}")

    # ── 2. RFO: redesign the sequence against a Boltz refold ───────────────
    # cyclic=True only reaches the Boltz branch, so backprop_fraction must be 0.
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
    # include_bonds carries the ring closure into AF3 as `bondedAtomPairs`.
    # Without it AF3 folds the peptide as a linear polymer: a closed 12-residue
    # ring scores iptm 0.09, while Boltz -- which does receive the closure --
    # scores the same design 0.88. The bond is recovered geometrically when the
    # intermediate lost it, which RFO's PDB output always does.
    #
    # msa_json supplies PD-1's precomputed MSA. Without it AF3 folds the receptor
    # in single-sequence mode and pLDDT sits in the 30-50 range regardless of
    # design quality. The designed peptide never matches the cached sequence, so
    # it correctly stays MSA-free.
    # The MSA cache is a computed artifact (~30 min, several MB), so it lives
    # under files/.cache/ rather than in the source tree.
    msa_cache = FILES_DIR / ".cache" / "pd1_msa.json"
    if not msa_cache.is_file():
        print(
            f"\nWARNING: {msa_cache} missing -- AF3 will run single-sequence "
            "and pLDDT will be suppressed.\n"
            f"  python {FILES_DIR / 'prep_target.py'} --msa\n"
            "A full search takes ~30 minutes.\n"
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
    # ipTM is the interface-confidence gate, set below the 0.7 a 60+ residue
    # binder reaches: a 12-residue macrocycle covers far less interface. The
    # measured ceiling here is 0.77, so 0.5 keeps the top ~3 of 8 as a ranking
    # cut rather than a success criterion.
    threshold = 0.4 if args.test else 0.5
    passed = engine.run(
        Filter(expr=f"af3.iptm >= {threshold} and af3.plddt >= 60"),
        data=refolded,
        run_args=run_args,
    )

    result = passed.unpack()
    print(f"\npassed {len(result)} / {len(refolded.unpack())}")
    if len(result):
        columns = [c for c in ("design_id", "af3.iptm", "af3.ptm", "af3.plddt",
                               "af3.min_pae_interaction") if c in result.columns]
        print(result[columns].to_string(index=False))

    # unpack() returns a pandas DataFrame, so `to_csv` (not polars' `write_csv`).
    result.to_csv(rundir / "results.csv", index=False)
    print(f"metrics: {rundir / 'results.csv'}")
    return result


if __name__ == "__main__":
    main()
