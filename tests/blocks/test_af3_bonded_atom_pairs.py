"""AF3 ``bondedAtomPairs`` extraction for cyclic peptides.

AF3 folds a chain as a linear polymer unless the closing bond is declared, so a
head-to-tail macrocycle is scored as if its ends were free. Measured on a
14-residue ring against CD8alpha: iptm 0.09 without the closure, 0.88 from Boltz
with it.

The bond has to survive an intermediate that cannot store it: RFO writes PDB,
which has no ``struct_conn`` category, so a perfectly closed ring arrives with
``atom_array.bonds is None``. These tests pin both routes -- the bond list when
present, the geometric fallback when not.
"""

from __future__ import annotations

import json

import numpy as np
import pytest
from biotite.structure import AtomArray, BondList

from blocks.networks.prediction.helpers import (
    create_af3_json_from_design,
    extract_bonded_atom_pairs,
)


def _chain(n_res: int, chain_id: str, *, closed: bool):
    """A backbone-only peptide; `closed` puts the termini a bond length apart."""
    names = ("N", "CA", "C")
    n_atoms = n_res * len(names)
    atoms = AtomArray(n_atoms)
    atoms.chain_id = np.array([chain_id] * n_atoms)
    atoms.res_id = np.repeat(np.arange(1, n_res + 1), len(names)).astype(np.int64)
    atoms.res_name = np.array(["GLY"] * n_atoms)
    atoms.atom_name = np.array(list(names) * n_res)
    atoms.element = np.array(["N", "C", "C"] * n_res)
    # create_af3_json_from_design reads these to classify each chain.
    from atomworks.enums import ChainType

    atoms.set_annotation(
        "chain_type", np.full(n_atoms, ChainType.POLYPEPTIDE_L, dtype=np.int32)
    )
    atoms.set_annotation("is_polymer", np.ones(n_atoms, dtype=bool))
    atoms.set_annotation("is_protein", np.ones(n_atoms, dtype=bool))

    # Lay residues along x, 3.8 A apart; a closed ring brings the last C back to
    # within 1.33 A of the first N.
    coords = np.zeros((n_atoms, 3), dtype=np.float32)
    for i in range(n_res):
        base = i * 3
        coords[base + 0] = [i * 3.8, 0, 0]
        coords[base + 1] = [i * 3.8 + 1.4, 0, 0]
        coords[base + 2] = [i * 3.8 + 2.6, 0, 0]
    if closed:
        coords[n_res * 3 - 1] = coords[0] + np.array([1.33, 0, 0], dtype=np.float32)
    atoms.coord = coords
    return atoms


def test_geometric_fallback_recovers_a_ring_without_bonds():
    """RFO's PDB output has no bonds; the closed geometry must still be found."""
    atoms = _chain(14, "A", closed=True)
    assert atoms.bonds is None

    pairs = extract_bonded_atom_pairs(atoms)

    assert pairs == [[["A", 1, "N"], ["A", 14, "C"]]]


def test_open_chain_declares_no_bonds():
    atoms = _chain(14, "A", closed=False)
    assert extract_bonded_atom_pairs(atoms) is None


def test_bond_list_is_used_when_present_and_intra_residue_skipped():
    atoms = _chain(10, "A", closed=True)
    atoms.bonds = BondList(atoms.array_length())
    # intra-residue: must not be emitted
    atoms.bonds.add_bond(0, 1)
    atoms.bonds.add_bond(1, 2)
    # the ring closure
    atoms.bonds.add_bond(0, 9 * 3 + 2)

    pairs = extract_bonded_atom_pairs(atoms)

    assert pairs == [[["A", 1, "N"], ["A", 10, "C"]]]


def test_residue_numbers_follow_per_chain_renumbering():
    """AF3 numbers residues 1..N per chain, so original res_id must not leak."""
    atoms = _chain(6, "A", closed=True)
    atoms.res_id = atoms.res_id + 100  # a structure numbered from 101

    pairs = extract_bonded_atom_pairs(atoms)

    assert pairs == [[["A", 1, "N"], ["A", 6, "C"]]]


def test_duplicate_pairs_are_collapsed():
    """A bond list that already records the ring plus the geometric check must
    not emit the same pair twice -- AF3 rejects duplicates outright."""
    atoms = _chain(10, "A", closed=True)
    atoms.bonds = BondList(atoms.array_length())
    atoms.bonds.add_bond(0, 9 * 3 + 2)

    pairs = extract_bonded_atom_pairs(atoms)

    assert len(pairs) == 1


def test_pairs_are_json_serialisable():
    """numpy scalars would break json.dump inside the block."""
    atoms = _chain(12, "A", closed=True)
    assert json.dumps(extract_bonded_atom_pairs(atoms))


def test_json_omits_bonded_atom_pairs_unless_requested():
    atoms = _chain(12, "A", closed=True)

    without = create_af3_json_from_design(atoms, name="x")
    assert "bondedAtomPairs" not in without

    with_bonds = create_af3_json_from_design(atoms, name="x", include_bonds=True)
    assert with_bonds["bondedAtomPairs"] == [[["A", 1, "N"], ["A", 12, "C"]]]


def test_include_bonds_on_an_unbonded_complex_stays_absent():
    """A plain binder complex should not gain a spurious field."""
    atoms = _chain(30, "A", closed=False)
    data = create_af3_json_from_design(atoms, name="x", include_bonds=True)
    assert "bondedAtomPairs" not in data


# ── Cached MSA injection ────────────────────────────────────────────────────


def _block_with_msa(tmp_path, cache: dict):
    from blocks.networks.prediction.alphafold3 import AlphaFold3Block

    path = tmp_path / "msa.json"
    path.write_text(json.dumps(cache))
    return AlphaFold3Block(msa_json=str(path))


def test_cached_msa_lands_on_matching_chains_only(tmp_path):
    """Matching on sequence, not chain id, is what lets a designed peptide skip it.

    A peptide built by RFD4 has no entry in the cache, and giving it one would be
    wrong: AF3 would treat a novel sequence as if it had homologs.
    """
    target = "ACDEFGHIKLMNPQRSTVWY"
    block = _block_with_msa(
        tmp_path,
        {
            "sequence": target,
            "unpairedMsa": ">q\nACDEFGHIKLMNPQRSTVWY\n",
            "pairedMsa": "",
            "templates": [],
        },
    )
    json_data = {
        "sequences": [
            {"protein": {"id": "A", "sequence": "GGGG", "unpairedMsa": ""}},
            {"protein": {"id": "B", "sequence": target, "unpairedMsa": ""}},
        ]
    }

    assert block._inject_cached_msa(json_data) == 1
    assert json_data["sequences"][0]["protein"]["unpairedMsa"] == ""
    assert "ACDEFGHIKLMNPQRSTVWY" in json_data["sequences"][1]["protein"]["unpairedMsa"]


def test_cached_msa_serves_every_copy_of_a_homomer(tmp_path):
    """Two identical chains share one cache entry."""
    target = "ACDEFGHIKLMNPQRSTVWY"
    block = _block_with_msa(
        tmp_path,
        {"sequence": target, "unpairedMsa": ">q\nACDEFGHIKLMNPQRSTVWY\n",
         "pairedMsa": "", "templates": []},
    )
    json_data = {
        "sequences": [
            {"protein": {"id": "D", "sequence": target}},
            {"protein": {"id": "E", "sequence": target}},
        ]
    }
    assert block._inject_cached_msa(json_data) == 2


def test_cached_msa_carries_templates(tmp_path):
    target = "ACDEFGHIKLMNPQRSTVWY"
    templates = [{"mmcif": "DATA", "queryIndices": [1], "templateIndices": [5]}]
    block = _block_with_msa(
        tmp_path,
        {"sequence": target, "unpairedMsa": ">q\nX\n", "pairedMsa": "",
         "templates": templates},
    )
    json_data = {"sequences": [{"protein": {"id": "B", "sequence": target}}]}
    block._inject_cached_msa(json_data)
    assert json_data["sequences"][0]["protein"]["templates"] == templates


def test_missing_msa_json_raises(tmp_path):
    from blocks.networks.prediction.alphafold3 import AlphaFold3Block

    block = AlphaFold3Block(msa_json=str(tmp_path / "nope.json"))
    with pytest.raises(FileNotFoundError, match="msa_json not found"):
        block._inject_cached_msa({"sequences": []})


def test_msa_json_forces_the_json_mode(tmp_path):
    """The mmCIF route lets AF3 compute its own MSA; a supplied cache needs JSON."""
    from blocks.networks.prediction.alphafold3 import AlphaFold3Block

    assert AlphaFold3Block()._use_mmcif_input()  # default stays mmcif
    assert not AlphaFold3Block(msa_json="/tmp/x.json")._use_mmcif_input()
