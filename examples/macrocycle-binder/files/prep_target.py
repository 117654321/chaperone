#!/usr/bin/env -S bash -c '"${CHAPERONE_REPO:-.}/.venv/bin/python" "$0" "$@"'
"""Stage the PD-1 target for the macrocycle example, optionally caching its MSA.

The upstream repository ships a conditioned input for the cyclic-peptide task
(``docs/examples/inputs/cyclic_binders/01_PD1_head_tail_12.cif.zst``): 115
residues of PD-1 on chain B plus a placeholder peptide on chain P, with the
closing bond and four side-chain hotspots already declared. Only the target is
kept here -- this example builds a 20-residue ring, not upstream's 12, so the
peptide is discarded.

The four hotspot atoms are still upstream's, and they are the same residues the
12-residue example uses, which keeps the two comparable: only the ring length
changes between them.

Always writes ``files/pd1_target.cif`` (chain B only).

With ``--msa``, also runs the AF3 genetic search and writes
``files/.cache/pd1_msa.json``. That takes ~30 minutes against the 411 GB
database and is what makes AF3's scores meaningful: without it the receptor is
folded in single-sequence mode and pLDDT sits in the 30-50 range for every
design. The result is reused by every later run.

    # stage the target (fast)
    python examples/macrocycle-binder/files/prep_target.py

    # stage the target and cache the MSA (slow, once)
    python examples/macrocycle-binder/files/prep_target.py --msa
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Upstream ships this input inside the RFD4-Proteina checkout. RFD4_REPO names
# that checkout; the rfd4 block reads the same setting.
_REPO = os.environ.get("RFD4_REPO", "")
DEFAULT_SOURCE = Path(_REPO) / "docs/examples/inputs/cyclic_binders/01_PD1_head_tail_12.cif.zst" if _REPO else None
# AF3 database directory; set AF3_DB_DIR.
_DB = os.environ.get("AF3_DB_DIR", "")
DB = Path(_DB) if _DB else None
KEEP_CHAIN = "B"

ONE_LETTER = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}


def read_zst(path: Path) -> bytes:
    import zstandard as zstd

    with path.open("rb") as handle:
        return zstd.ZstdDecompressor().stream_reader(handle).read()


def target_sequence(atoms) -> str:
    mask = atoms.chain_id == KEEP_CHAIN
    return "".join(
        ONE_LETTER.get(str(atoms.res_name[mask & (atoms.res_id == r)][0]), "X")
        for r in sorted(set(atoms.res_id[mask]))
    )


def run_msa_search(sequence: str, cpus: int):
    """One AF3 genetic search for the target chain."""
    from alphafold3.common import folding_input
    from alphafold3.data import pipeline

    config = pipeline.DataPipelineConfig(
        jackhmmer_binary_path="/usr/bin/jackhmmer",
        nhmmer_binary_path="/usr/bin/nhmmer",
        hmmalign_binary_path="/usr/bin/hmmalign",
        hmmsearch_binary_path="/usr/bin/hmmsearch",
        hmmbuild_binary_path="/usr/bin/hmmbuild",
        small_bfd_database_path=str(DB / "bfd-first_non_consensus_sequences.fasta"),
        mgnify_database_path=str(DB / "mgy_clusters_2022_05.fa"),
        uniprot_cluster_annot_database_path=str(DB / "uniprot_all_2021_04.fa"),
        uniref90_database_path=str(DB / "uniref90_2022_05.fa"),
        pdb_database_path=str(DB / "mmcif_files"),
        ntrna_database_path=str(
            DB / "nt_rna_2023_02_23_clust_seq_id_90_cov_80_rep_seq.fasta"
        ),
        rfam_database_path=str(DB / "rfam_14_9_clust_seq_id_90_cov_80_rep_seq.fasta"),
        rna_central_database_path=str(
            DB / "rnacentral_active_seq_id_90_cov_80_linclust.fasta"
        ),
        seqres_database_path=str(DB / "pdb_seqres_2022_09_28.fasta"),
        jackhmmer_n_cpu=cpus,
        nhmmer_n_cpu=cpus,
        hmmsearch_n_cpu=cpus,
        max_template_date=date(2024, 1, 1),
    )
    # MSA/template fields must stay None: an empty *string* means "already has no
    # MSA, skip the search", which returns in 0 s.
    chain = folding_input.ProteinChain(id=KEEP_CHAIN, sequence=sequence, ptms=[])
    return pipeline.DataPipeline(config).process_protein_chain(chain)


def template_to_dict(template) -> dict:
    """Serialize a Template the way AF3's JSON dialect spells it."""
    mapping = dict(template.query_to_template_map or {})
    return {
        "mmcif": template.mmcif,
        "queryIndices": [int(k) for k in mapping],
        "templateIndices": [int(v) for v in mapping.values()],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=HERE / "pd1_target.cif")
    parser.add_argument(
        "--msa", action="store_true", help="Also run and cache the target MSA (~30 min)."
    )
    parser.add_argument("--msa-out", type=Path, default=HERE / ".cache" / "pd1_msa.json")
    parser.add_argument("--cpus", type=int, default=os.cpu_count())
    args = parser.parse_args()

    if args.source is None:
        raise SystemExit(
            "no source structure: set RFD4_REPO to the RFD4-Proteina checkout "
            "(the example input ships there) or pass --source"
        )
    if not args.source.is_file():
        raise SystemExit(
            f"upstream example input not found: {args.source}\n"
            "This file ships with the RFD4-Proteina checkout."
        )

    import tempfile

    from biotite.structure.io.pdbx import CIFFile, get_structure, set_structure

    handle = tempfile.NamedTemporaryFile(suffix=".cif", delete=False)
    handle.write(read_zst(args.source))
    handle.close()
    try:
        atoms = get_structure(CIFFile.read(handle.name), model=1)
    finally:
        Path(handle.name).unlink(missing_ok=True)

    target = atoms[atoms.chain_id == KEEP_CHAIN]
    if target.array_length() == 0:
        raise SystemExit(f"chain {KEEP_CHAIN} not found in {args.source}")

    cif = CIFFile()
    set_structure(cif, target, data_block="pd1_target")
    cif.write(str(args.out))
    print(
        f"wrote {args.out}: {target.array_length()} atoms, "
        f"{len(set(target.res_id))} residues"
    )

    if not args.msa:
        print("\nSkipped the MSA search (pass --msa to run it, ~30 min).")
        print("Without it AF3 folds the target in single-sequence mode.")
        return

    sequence = target_sequence(target)
    if DB is None:
        raise SystemExit(
            "AF3 database directory not set: export AF3_DB_DIR to the directory "
            "holding bfd-first_non_consensus_sequences.fasta, uniref90_2022_05.fa, ..."
        )
    print(f"\nRunning the AF3 genetic search for {len(sequence)} residues...", flush=True)
    result = run_msa_search(sequence, args.cpus)
    rows = len(result.unpaired_msa.splitlines()) if result.unpaired_msa else 0
    templates = [template_to_dict(t) for t in (result.templates or [])]
    print(f"MSA rows: {rows}, templates: {len(templates)}", flush=True)

    args.msa_out.parent.mkdir(parents=True, exist_ok=True)
    # Write before anything else can fail: losing a 30-minute search because the
    # process exited without serialising has happened on this project before.
    args.msa_out.write_text(
        json.dumps(
            {
                "chain": KEEP_CHAIN,
                "sequence": sequence,
                "unpairedMsa": result.unpaired_msa,
                "pairedMsa": result.paired_msa or "",
                "templates": templates,
            }
        )
    )
    print(f"wrote {args.msa_out} ({args.msa_out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
