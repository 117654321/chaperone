#!/usr/bin/env -S bash -c '"${CHAPERONE_REPO:-.}/.venv/bin/python" "$0" "$@"'
"""Stage PD-L1 as a binder target, write the RFD4 spec, and optionally cache its MSA.

Target: PDB 5O45 chain A residues 17-131 (PD-L1 IgV domain), the same cropped
structure upstream's `docs/how-to/binder-in-10-lines.md` designs against.

Always writes:

* ``files/pdl1_target.cif`` -- chain B, renumbered per chain. RFD4 names the
  binder chain in the contig, so the target has to occupy a different id; RFO
  also requires the designed chain to be literally ``A``.
* ``files/binder.yaml`` -- the condition spec. Binder length, target
  conditioning and hotspot atoms are upstream's numbers:

  - contig ``"50-120, /0, B1-115"``: a new 50-120 residue chain, then the target
  - ``C_CRDGRP`` pins the target's backbone geometry while leaving its pose free
  - ``C_SEQ`` fixes the target's identity
  - ``C_HOT`` marks three interface residues at side-chain atom precision

  Hotspots were verified against the structure: B56 is Tyr (CG, OH), B115 is Met
  (CG, SD), B123 is Tyr (CD2, OH). Residue numbers shift by -16 relative to the
  raw PDB because the crop starts at 17.

With ``--msa``, also runs the AF3 genetic search and writes
``files/.cache/pdl1_msa.json``. That takes ~30 minutes against the 411 GB
database and is what makes AF3's scores meaningful: without it the receptor is
folded in single-sequence mode and pLDDT sits in the 30-50 range for every
design. The result is reused by every later run, so it is worth doing once.

    # stage the target (fast)
    python examples/miniprotein-binder/files/prep_target.py

    # stage the target and cache the MSA (slow, once)
    python examples/miniprotein-binder/files/prep_target.py --msa
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = Path(
    "/home/user/software/RFD4-Proteina/docs/examples/inputs/5o45_cropped.cif.zst"
)
DB = Path("/home/user/data/models/alphafold3_models/public_databases")

KEEP_CHAIN = "A"
NEW_CHAIN = "B"
RESIDUE_OFFSET = 16  # crop starts at PDB residue 17 -> local numbering starts at 1
BINDER_LENGTH = (50, 120)

# Upstream's hotspots, in PDB numbering.
HOTSPOTS_PDB = ((56, "CG,OH"), (115, "CG,SD"), (123, "CD2,OH"))

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


def find_residue(atoms, chain: str, res_id: int) -> tuple[str, list[str]]:
    mask = (atoms.chain_id == chain) & (atoms.res_id == res_id)
    if not mask.any():
        raise SystemExit(f"residue {chain}{res_id} not found")
    return str(atoms.res_name[mask][0]), sorted(set(map(str, atoms.atom_name[mask])))


def target_sequence(atoms) -> str:
    mask = atoms.chain_id == NEW_CHAIN
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
    chain = folding_input.ProteinChain(id=NEW_CHAIN, sequence=sequence, ptms=[])
    return pipeline.DataPipeline(config).process_protein_chain(chain)


def template_to_dict(template) -> dict:
    """Serialize a Template the way AF3's JSON dialect spells it.

    In memory a template holds ``query_to_template_map`` (a dict), but the JSON
    form is two parallel arrays.
    """
    mapping = dict(template.query_to_template_map or {})
    return {
        "mmcif": template.mmcif,
        "queryIndices": [int(k) for k in mapping],
        "templateIndices": [int(v) for v in mapping.values()],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--cif", type=Path, default=HERE / "pdl1_target.cif")
    parser.add_argument("--spec", type=Path, default=HERE / "binder.yaml")
    parser.add_argument(
        "--msa", action="store_true", help="Also run and cache the target MSA (~30 min)."
    )
    parser.add_argument(
        "--msa-out", type=Path, default=HERE / ".cache" / "pdl1_msa.json"
    )
    parser.add_argument("--cpus", type=int, default=os.cpu_count())
    args = parser.parse_args()

    if not args.source.is_file():
        raise SystemExit(f"upstream input not found: {args.source}")

    import tempfile

    from biotite.structure.io.pdbx import CIFFile, get_structure, set_structure

    handle = tempfile.NamedTemporaryFile(suffix=".cif", delete=False)
    handle.write(read_zst(args.source))
    handle.close()
    try:
        atoms = get_structure(CIFFile.read(handle.name), model=1)
    finally:
        Path(handle.name).unlink(missing_ok=True)

    target = atoms[atoms.chain_id == KEEP_CHAIN].copy()
    if target.array_length() == 0:
        raise SystemExit(f"chain {KEEP_CHAIN} not found in {args.source}")

    # Renumber to 1..N and move to a fresh chain id so the binder can take "A".
    old_ids = sorted(set(int(r) for r in target.res_id))
    mapping = {old: new for new, old in enumerate(old_ids, start=1)}
    target.res_id = np.array([mapping[int(r)] for r in target.res_id], dtype=np.int64)
    target.chain_id = np.array([NEW_CHAIN] * target.array_length())

    cif = CIFFile()
    set_structure(cif, target, data_block="pdl1_target")
    cif.write(str(args.cif))
    print(
        f"wrote {args.cif}: {target.array_length()} atoms, "
        f"{len(old_ids)} residues on chain {NEW_CHAIN}"
    )

    # Confirm each hotspot's atoms exist before writing them into a spec.
    selections = []
    for pdb_res_id, atom_list in HOTSPOTS_PDB:
        local = pdb_res_id - RESIDUE_OFFSET
        res_name, present = find_residue(target, NEW_CHAIN, local)
        wanted = atom_list.split(",")
        missing = [a for a in wanted if a not in present]
        if missing:
            raise SystemExit(
                f"hotspot {NEW_CHAIN}{local} ({res_name}) lacks {missing}; "
                f"available: {present}"
            )
        selections.append(
            f"{{select: \"sel('{NEW_CHAIN}/*/{local}/[{atom_list}]')\"}}"
        )

    spec = (
        f"# PD-L1 binder -- upstream's recipe from docs/how-to/binder-in-10-lines.md,\n"
        f"# with the target renumbered onto chain {NEW_CHAIN} and shifted by "
        f"-{RESIDUE_OFFSET}\n"
        f"# (the shipped crop starts at PDB residue 17).\n"
        f"pdl1_binder:\n"
        f"  input: {args.cif.name}\n"
        f'  contig: "{BINDER_LENGTH[0]}-{BINDER_LENGTH[1]}, /0, '
        f'{NEW_CHAIN}1-{len(old_ids)}"\n'
        f"  conditions:\n"
        f'    C_CRDGRP: {{1: [{{select: "sel(\'{NEW_CHAIN}/*/*/[N,CA,C,O]\')"}}]}}\n'
        f'    C_SEQ: {{true: [{{select: "sel(\'{NEW_CHAIN}\')"}}]}}\n'
        f"    C_HOT: {{true: [{', '.join(selections)}]}}\n"
    )
    args.spec.write_text(spec)
    print(f"wrote {args.spec}")

    if not args.msa:
        print("\nSkipped the MSA search (pass --msa to run it, ~30 min).")
        print("Without it AF3 folds the target in single-sequence mode.")
        return

    sequence = target_sequence(target)
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
                "chain": NEW_CHAIN,
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
