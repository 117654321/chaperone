#!/usr/bin/env -S bash -c '"${CHAPERONE_REPO:-.}/.venv/bin/python" "$0" "$@"'
"""Miniprotein binder design against PD-L1, with RFO sequence optimisation.

Pipeline: rfd4 -> rfoptimization -> af3 -> filter

RFD4 builds a de novo 50-120 residue binder against PD-L1's IgV domain, RFO
re-designs its sequence against a Boltz-2 refold, AF3 refolds the result, and a
metric filter gates on interface confidence.

Target and conditioning follow upstream's own binder recipe
(`docs/how-to/binder-in-10-lines.md`): PD-L1 chain A from PDB 5O45 residues
17-131, three side-chain hotspots on the PD-1/PD-L1 interface (Y56, M115, Y123),
target backbone geometry fixed, target sequence known.

Unlike the cyclic-peptide example, RFD4 expresses a linear binder through a
condition spec rather than block fields: the contig declares a new 50-120
residue chain, and the conditions pin the target. `files/prep_target.py` writes
that spec.

Two things this script assumes, both measured:

* RFOptimization hard-requires the designed chain to be named `A`. The spec
  builds the binder on A.
* AF3 must receive PD-L1's MSA. Without it the receptor is folded in
  single-sequence mode and pLDDT sits in the 30-50 range for every design; the
  same designs on the cyclic-peptide example scored iptm 0.09-0.21 without the
  MSA and 0.32-0.77 with it. Run `files/prep_msa.py` once.

Run:
    python examples/miniprotein-binder/pipeline.py --test --local --rundir=/abs/path/miniprotein-smoke
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
DESIGN_SPEC = FILES_DIR / "binder.yaml"


def parse_args(argv: list[str]):
    """Split this script's own flags from the ones absl owns.

    ``init_cli()`` parses the whole argv through absl, which rejects any flag it
    did not define -- so our flags have to be consumed first and only the rest
    handed over.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", action="store_true", help="One design end to end.")
    parser.add_argument("--rundir", type=Path, default=None, help="Absolute run directory.")
    parser.add_argument("--local", action="store_true", help="Run on this GPU instead of Slurm.")
    parser.add_argument("--replicates", type=int, default=4, help="Backbones to sample.")
    parser.add_argument("--cycles", type=int, default=3, help="RFO redesign cycles.")
    parser.add_argument(
        "--search",
        action="store_true",
        help=(
            "Use upstream's reward-guided beam search instead of RFD4+RFO. It "
            "scores branches with an AF3 oracle *during* generation, so it needs "
            "a host RFD4 install with apptainer (not the runtime SIF)."
        ),
    )
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

    if not DESIGN_SPEC.is_file():
        raise SystemExit(
            f"missing design spec: {DESIGN_SPEC}\n"
            f"Run {FILES_DIR / 'prep_target.py'} first."
        )

    RFD4, RFO, AF3, Filter = Blocks.getall("rfd4", "rfoptimization", "af3", "filter")

    # ── search path: upstream's reward-guided beam search ──────────────────
    # A single block doing RFD4 generation *and* AF3-based pruning inside the
    # sampler. It runs on the host, not in the runtime SIF: the oracle spawns its
    # own apptainer per refold, and a container cannot start a nested one.
    if args.search:
        Search = Blocks.get("rfd4_search")
        searched = engine.run(
            Search(
                inputs=str(DESIGN_SPEC),
                search_config=str(FILES_DIR / "search" / "pdl1_beam.yaml"),
                num_replicates=replicates,
                batch_size=1,
                seed=42,
            ),
            run_args=run_args,
        )
        found = searched.unpack()
        print(f"\nbeam search produced {len(found)} designs")
        columns = [
            c
            for c in found.columns
            if c.endswith(("search.reward", "min_ipae_coi", "iptm_coi", "plddt_coi"))
        ]
        if columns:
            print(found[columns].to_string(index=False))
        found.to_csv(rundir / "results.csv", index=False)
        print(f"metrics: {rundir / 'results.csv'}")
        return searched

    # ── 1. RFD4: build the binder ──────────────────────────────────────────
    # The spec carries contig, length range and conditions; RFD4's block fields
    # only cover cyclic peptides.
    design = engine.run(
        RFD4(
            inputs=str(DESIGN_SPEC),
            num_replicates=replicates,
            batch_size=1,
            seed=42,
            extra_overrides=["recycle_strategy=medium/front_loaded"],
        ),
        run_args=run_args,
    )

    frame = design.unpack()
    print(f"\nRFD4 produced {len(frame)} designs")

    # ── 2. RFO: redesign the sequence against a Boltz refold ───────────────
    optimized = engine.run(
        RFO(
            total_cycles=cycles,
            backprop_fraction=0.0,
            mpnn_model_type="ligand_mpnn",
            seed=42,
        ),
        data=design,
        run_args=run_args,
    )

    # ── 3. AF3: refold and score the interface ─────────────────────────────
    # The MSA cache is a computed artifact (4.5 MB, ~30 min to build), so it
    # lives under files/.cache/ rather than in the source tree.
    msa_cache = FILES_DIR / ".cache" / "pdl1_msa.json"
    if not msa_cache.is_file():
        print(
            f"\nWARNING: {msa_cache} missing -- AF3 will run single-sequence "
            "and pLDDT will be suppressed.\n"
            f"Generate it once with: python {FILES_DIR / 'prep_target.py'} --msa\n"
        )
    refolded = engine.run(
        AF3(
            diffusion_batch_size=1,
            read_most_confident_model=True,
            msa_json=str(msa_cache) if msa_cache.is_file() else None,
        ),
        data=optimized,
        run_args=run_args,
    )

    # ── 4. Filter ──────────────────────────────────────────────────────────
    # A 50-120 residue binder reaches the same ipTM range as a conventional
    # protein binder, so this keeps upstream's 0.7 rather than the relaxed cut
    # the cyclic-peptide example needs.
    threshold = 0.5 if args.test else 0.7
    passed = engine.run(
        Filter(expr=f"af3.iptm >= {threshold} and af3.plddt >= 70"),
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
