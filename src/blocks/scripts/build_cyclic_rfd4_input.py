"""Build a cyclic-peptide annotated CIF for RFD4, per the official recipe.

RFD4 does not cyclize from a flag, and it does not need template coordinates.
The ring reaches the model as one ``_struct_conn`` ``covale`` record, and the
peptide chain itself is a run of residue slots with zeroed backbone atoms whose
sequence and coordinates are both left to the model (``C_SEQ = <M>``, no
``C_CRD``). That is exactly what ``docs/examples/inputs/cyclic_binders`` ships.

This script runs INSIDE the RFD4 runtime (it needs atomworks + rfproteina), and
takes a plain JSON request so the caller does not need to know the API:

    python build_cyclic_input.py request.json

request.json::

    {
      "input": "/abs/target.cif",          # target structure, any CIF/PDB
      "output": "/abs/cyclic_input.cif",
      "target_chains": ["D", "E"],
      "hotspots": [40, 45, 47, 86, 91, 95],
      "peptide_chain": "A",
      "peptide_length": 12,
      "chemistry": "head_tail"             # head_tail | disulfide | isopeptide
    }

Two things are deliberately not done here:

* The closing bond is NOT added to the in-memory bond list. biotite's
  ``_filter_canonical_links`` has an operator-precedence bug --
  ``A & d == 1`` evaluates as ``(A & d) == 1``, which is True for any odd
  ``d`` -- so a ``C1..N12`` bond (residue distance N-1) is classified as an
  ordinary peptide bond and dropped on write. The record is injected into the
  CIF text after writing instead, which is what upstream does by hand.
* Nothing is "repaired". The peptide stays atomized-at-zero on purpose; a
  finite coordinate would need ``C_CRD`` and would stop being designed.
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np

# The atomworks/rfproteina imports live inside the functions that need them so
# this module still imports on a host without the RFD4 runtime, which is what
# lets the pure-Python helpers (placeholder builder, struct_conn injection) be
# unit-tested. The composer executes this file inside the runtime image.

BACKBONE = ("N", "CA", "C", "O")

# chemistry -> (residue name at both ends, atom 1, atom 2, ideal distance, note)
CHEMISTRY = {
    "head_tail": ("GLY", "N", "C", 1.33),
    "disulfide": ("CYS", "SG", "SG", 2.05),
    "isopeptide": ("LYS", "NZ", "C", 1.33),
}

# Head-to-tail binds the first residue's N to the last residue's C. The other two
# crosslink side chains, so those atoms must exist on the placeholder residues
# or the parse has nothing to bond.
_EXTRA_ATOMS = {
    "GLY": (),
    "CYS": (("CB", "C"), ("SG", "S")),
    "LYS": (("CB", "C"), ("CG", "C"), ("CD", "C"), ("CE", "C"), ("NZ", "N")),
}


def _build_placeholder_peptide(
    length: int, chain_id: str, chemistry: str
):
    """A peptide chain with zeroed atoms and no conditioning at all."""
    from atomworks.io.utils.atom_array_plus import AtomArrayPlus

    res_name, _, _, _ = CHEMISTRY[chemistry]
    extra = _EXTRA_ATOMS[res_name]
    atoms = [(n, e) for n, e in zip(BACKBONE, ("N", "C", "C", "O"))] + list(extra)
    per_res = len(atoms)

    n_atoms = length * per_res
    arr = AtomArrayPlus(n_atoms)
    arr.coord = np.zeros((n_atoms, 3), dtype=np.float32)
    arr.chain_id = np.array([chain_id] * n_atoms)
    arr.res_id = np.repeat(np.arange(1, length + 1), per_res).astype(np.int64)
    arr.res_name = np.array([res_name] * n_atoms)
    arr.atom_name = np.array([name for _ in range(length) for name, _ in atoms])
    arr.element = np.array([elem for _ in range(length) for _, elem in atoms])
    arr.hetero = np.zeros(n_atoms, dtype=bool)
    arr.ins_code = np.array([""] * n_atoms)
    return arr


def parse_hotspots(hotspots):
    """Normalise a hotspot spec into ``{(chain_or_None, res_id): atoms_or_None}``.

    C_HOT is an ATOM-level condition, so naming the side-chain atoms that form the
    interface is what pins the binder to the intended epitope. A residue-level
    entry lets the model choose any atom of that residue and, with only a handful
    of residues given, leaves it free to dock on the wrong face -- observed as
    designs landing on the back of the receptor while nominally "using" the
    hotspots.

    Accepted forms::

        [40, 45]                       # residue numbers, any chain
        ["D40", "D45"]                 # explicit chain
        ["D40:NH1,NH2", "D45:OG"]      # chain + side-chain atoms (preferred)
        {"D40": "NH1,NH2", "D45": "OG"}  # same, as a mapping
    """
    if isinstance(hotspots, dict):
        items = list(hotspots.items())
    else:
        items = [(entry, None) for entry in (hotspots or [])]

    parsed: dict[tuple[str | None, int], tuple[str, ...] | None] = {}
    for entry, atoms in items:
        if isinstance(entry, int):
            parsed[(None, entry)] = None
            continue
        if not isinstance(entry, str):
            raise TypeError(f"hotspot entry must be int or str, got {type(entry).__name__}")

        spec = entry.strip()
        # "D40:NH1,NH2" -- atoms given inline after the colon.
        if atoms is None and ":" in spec:
            spec, atoms = spec.split(":", 1)
        atoms = atoms.strip() if isinstance(atoms, str) else None
        atom_names = (
            tuple(a.strip() for a in atoms.split(",") if a.strip()) if atoms else None
        )

        # Split trailing digits (residue number) from the leading chain id.
        idx = len(spec)
        while idx > 0 and spec[idx - 1].isdigit():
            idx -= 1
        chain_part, digits = spec[:idx], spec[idx:]
        if not digits:
            raise ValueError(f"hotspot {entry!r} has no residue number")
        parsed[(chain_part or None, int(digits))] = atom_names
    return parsed


def _hotspot_mask(atoms, hotspots) -> "np.ndarray":
    """Build the per-atom C_HOT mask from a normalised hotspot spec."""
    mask = np.zeros(atoms.array_length(), dtype=bool)
    chains = np.array([str(c) for c in atoms.chain_id])
    for (chain, res_id), atom_names in parse_hotspots(hotspots).items():
        sel = atoms.res_id == res_id
        if chain is not None:
            sel &= chains == chain
        if atom_names:
            sel &= np.isin(atoms.atom_name, atom_names)
        mask |= sel
    return mask


def build(request: dict) -> Path:
    # Imported here, not at module scope: these only exist inside the RFD4
    # runtime image, and the module must stay importable for host-side tests.
    import rfproteina.conditions  # noqa: F401  -- registers condition classes before parse
    from atomworks.io import parse
    from atomworks.io.utils.annotator import ensure_annotations
    from atomworks.io.utils.atom_array_plus import as_atom_array_plus
    from atomworks.io.utils.io_utils import to_cif_file
    from atomworks.ml.conditions import C_CRD, C_IDX, C_SEQ
    from rfproteina.conditions import C_HOT
    from rfproteina.utils.parse_presets import ANNOTATED_CIF

    source = Path(request["input"])
    output = Path(request["output"])
    target_chains = list(request.get("target_chains") or [])
    # Keep a mapping intact: list() would drop the atom names and silently
    # downgrade every hotspot to residue-level.
    hotspots = request.get("hotspots") or []
    peptide_chain = request.get("peptide_chain", "A")
    peptide_length = int(request.get("peptide_length", 12))
    chemistry = request.get("chemistry", "head_tail")
    if chemistry not in CHEMISTRY:
        raise ValueError(
            f"unknown chemistry {chemistry!r}; expected one of {sorted(CHEMISTRY)}"
        )

    parsed = parse(str(source), config=ANNOTATED_CIF)
    target = as_atom_array_plus(parsed["asym_unit"][0])
    ensure_annotations(target, "is_protein", "is_ligand")

    if target_chains:
        keep = np.isin(target.chain_id, target_chains)
        if not keep.any():
            raise ValueError(
                f"target_chains {target_chains} matched nothing; input has "
                f"{sorted(set(map(str, np.unique(target.chain_id))))}"
            )
        target = as_atom_array_plus(target[keep].copy())

    # A peptide chain id colliding with a kept target chain would silently merge
    # the designed ring into the receptor. Do NOT auto-rename: downstream
    # RFOptimization hard-requires the designed chain to be named "A", so a
    # silent rename to "B" would pass here and fail there with a confusing
    # message. Fail loudly with the fix instead.
    taken = set(map(str, np.unique(target.chain_id)))
    if peptide_chain in taken:
        free = next(
            (chr(code) for code in range(ord("A"), ord("Z") + 1) if chr(code) not in taken),
            None,
        )
        raise ValueError(
            f"peptide_chain {peptide_chain!r} collides with a target chain; target "
            f"chains are {sorted(taken)}. Rename the target chain in the input "
            f"structure (free ids include {free!r}) or pass target_chains to drop it. "
            f"Auto-renaming is not applied because RFOptimization requires the "
            f"designed chain to be named 'A'."
        )

    # Target: backbone coordinates fixed, identity fixed, hotspots marked.
    backbone = np.isin(target.atom_name, BACKBONE) & np.isfinite(target.coord).all(axis=1)
    C_CRD.set_annotation_from_ground_truth(target, backbone)
    C_SEQ.set_annotation_from_ground_truth(
        target, np.ones(target.array_length(), dtype=bool)
    )
    C_HOT.set_annotation(target, _hotspot_mask(target, hotspots))
    C_IDX.set_annotation(target, np.ones(target.array_length(), dtype=bool))

    peptide = _build_placeholder_peptide(peptide_length, peptide_chain, chemistry)
    # Sequence stays masked and no coordinate is conditioned: both are designed.
    # Width 3 so the literal "<M>" survives the CIF round-trip.
    C_SEQ.set_annotation(peptide, np.full(peptide.array_length(), "<M>", dtype="<U3"))
    C_CRD.set_annotation(peptide, np.full((peptide.array_length(), 3), np.nan))
    C_HOT.set_annotation(peptide, np.zeros(peptide.array_length(), dtype=bool))
    C_IDX.set_annotation(peptide, np.ones(peptide.array_length(), dtype=bool))

    combined = target + peptide

    output.parent.mkdir(parents=True, exist_ok=True)
    to_cif_file(combined, output)

    res_name, atom1, atom2, ideal = CHEMISTRY[chemistry]
    _inject_struct_conn(
        output,
        chain=peptide_chain,
        comp=res_name,
        res1=1,
        atom1=atom1,
        res2=peptide_length,
        atom2=atom2,
    )

    print(
        f"wrote {output}: chains={sorted(set(map(str, combined.chain_id)))} "
        f"atoms={combined.array_length()} ring={atom1}1-{atom2}{peptide_length} "
        f"(ideal {ideal} A)"
    )
    return output


_STRUCT_CONN_TEMPLATE = """#
_struct_conn.id                        1
_struct_conn.conn_type_id              covale
_struct_conn.pdbx_value_order          sing
_struct_conn.ptnr1_label_asym_id       {chain}
_struct_conn.ptnr2_label_asym_id       {chain}
_struct_conn.ptnr1_label_comp_id       {comp}
_struct_conn.ptnr2_label_comp_id       {comp}
_struct_conn.ptnr1_label_seq_id        {res1}
_struct_conn.ptnr2_label_seq_id        {res2}
_struct_conn.ptnr1_label_atom_id       {atom1}
_struct_conn.ptnr2_label_atom_id       {atom2}
_struct_conn.pdbx_ptnr1_PDB_ins_code   .
_struct_conn.pdbx_ptnr2_PDB_ins_code   .
#
"""


def _inject_struct_conn(
    path: Path, *, chain: str, comp: str, res1: int, atom1: str, res2: int, atom2: str
) -> None:
    """Insert one covale record before the atom_site loop.

    The parse preset (``ANNOTATED_CIF``) maps ``covale`` records onto atom bonds,
    and the model recognises a ring by a same-chain bond whose residue ids
    differ by more than one. Nothing else in the record is consumed.

    The idempotency check looks for *this* ring, not for any ``_struct_conn``
    category: real targets carry their own records (1AKJ has two disulfides on
    the CD8alpha chains), and treating those as "already injected" silently
    leaves the peptide linear -- the run then produces 20+ A end-to-end
    distances while every log line looks healthy.
    """
    text = path.read_text()
    if _already_has_ring(text, chain=chain, res1=res1, atom1=atom1, res2=res2, atom2=atom2):
        return
    block = _STRUCT_CONN_TEMPLATE.format(
        chain=chain, comp=comp, res1=res1, atom1=atom1, res2=res2, atom2=atom2
    )
    marker = "loop_\n_atom_site.group_PDB"
    if marker not in text:
        raise RuntimeError(f"unexpected CIF layout in {path}")
    path.write_text(text.replace(marker, block + marker, 1), encoding="utf-8")


def _already_has_ring(
    text: str, *, chain: str, res1: int, atom1: str, res2: int, atom2: str
) -> bool:
    """Whether the CIF already declares this exact closing bond.

    Matches on the record's partner fields rather than searching for the string
    ``_struct_conn.``, because a target's own disulfide/metal records are
    irrelevant to the peptide ring.
    """
    import re

    # Loop form: each record is one whitespace-separated row under the header.
    for match in re.finditer(r"^(\d+)\s+covale\b.*$", text, re.MULTILINE):
        fields = match.group(0).split()
        # id conn_type order chain1 chain2 comp1 comp2 seq1 seq2 atom1 atom2 ...
        if len(fields) < 11:
            continue
        if (
            fields[3] == chain
            and fields[4] == chain
            and fields[7] == str(res1)
            and fields[8] == str(res2)
            and fields[9] == atom1
            and fields[10] == atom2
        ):
            return True

    # Single-record form (the layout this function writes).
    def field(name: str) -> str | None:
        m = re.search(rf"^_struct_conn\.{name}\s+(\S+)\s*$", text, re.MULTILINE)
        return m.group(1) if m else None

    return (
        field("ptnr1_label_asym_id") == chain
        and field("ptnr2_label_asym_id") == chain
        and field("ptnr1_label_seq_id") == str(res1)
        and field("ptnr2_label_seq_id") == str(res2)
        and field("ptnr1_label_atom_id") == atom1
        and field("ptnr2_label_atom_id") == atom2
    )


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <request.json>", file=sys.stderr)
        return 2
    request = json.loads(Path(argv[1]).read_text())
    build(request)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
