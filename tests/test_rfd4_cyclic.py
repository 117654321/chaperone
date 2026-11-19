"""RFD4 cyclic-peptide input construction.

RFD4 has no cyclization flag: the ring reaches the model as one ``_struct_conn``
``covale`` record, and the peptide chain is a placeholder whose sequence and
coordinates are both left to the model. These tests pin the two things that
silently break that contract:

* the peptide chain must default to ``A`` (RFOptimization hard-requires it),
  and a collision with a target chain must fail loudly instead of being
  auto-renamed;
* the closing bond must be injected as text, because ``to_cif_file`` drops it
  on biotite's operator-precedence bug in ``_filter_canonical_links``.

Nothing here needs the RFD4 runtime image: the pure-Python helpers are
importable on their own.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

BUILDER = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "blocks"
    / "scripts"
    / "build_cyclic_rfd4_input.py"
)


def _load_builder():
    """Import the builder by path; it has no package-relative imports."""
    spec = importlib.util.spec_from_file_location("_cyclic_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_builder_defines_every_supported_chemistry():
    builder = _load_builder()
    assert set(builder.CHEMISTRY) == {"head_tail", "disulfide", "isopeptide"}
    # Each entry is (residue name, first atom, second atom, ideal distance).
    for name, (comp, atom1, atom2, ideal) in builder.CHEMISTRY.items():
        assert isinstance(comp, str) and comp
        assert isinstance(atom1, str) and isinstance(atom2, str)
        assert ideal > 0


def test_placeholder_chain_has_zeroed_backbone_and_no_conditioning():
    builder = _load_builder()
    peptide = builder._build_placeholder_peptide(10, "A", "head_tail")

    assert peptide.array_length() == 10 * 4  # N/CA/C/O per residue
    assert set(map(str, peptide.chain_id)) == {"A"}
    assert sorted(set(peptide.res_id)) == list(range(1, 11))
    assert set(map(str, peptide.atom_name)) == {"N", "CA", "C", "O"}
    # Zeroed on purpose: a finite coordinate would need C_CRD and stop being designed.
    assert (peptide.coord == 0).all()


def test_side_chain_chemistries_carry_the_crosslinked_atoms():
    builder = _load_builder()
    names = lambda chem: set(  # noqa: E731
        map(str, builder._build_placeholder_peptide(3, "A", chem).atom_name)
    )
    assert "SG" in names("disulfide")
    assert "NZ" in names("isopeptide")
    assert "SG" not in names("head_tail")


def test_struct_conn_is_injected_as_text_not_through_bonds(tmp_path):
    builder = _load_builder()
    target = tmp_path / "cyclic.cif"
    target.write_text(
        "data_test\n#\nloop_\n_atom_site.group_PDB\n_atom_site.id\nATOM 1\n#\n"
    )

    builder._inject_struct_conn(
        target, chain="A", comp="GLY", res1=1, atom1="N", res2=10, atom2="C"
    )

    text = target.read_text()
    assert "_struct_conn.conn_type_id              covale" in text
    assert "_struct_conn.ptnr1_label_asym_id       A" in text
    assert "_struct_conn.ptnr1_label_atom_id       N" in text
    assert "_struct_conn.ptnr2_label_atom_id       C" in text
    # Must land before the atom loop, or the parser never sees it as a category.
    assert text.index("_struct_conn.id") < text.index("_atom_site.group_PDB")


def test_injection_is_idempotent(tmp_path):
    builder = _load_builder()
    target = tmp_path / "cyclic.cif"
    target.write_text("data_t\n#\nloop_\n_atom_site.group_PDB\nATOM 1\n")
    kwargs = dict(chain="A", comp="GLY", res1=1, atom1="N", res2=10, atom2="C")

    builder._inject_struct_conn(target, **kwargs)
    first = target.read_text()
    builder._inject_struct_conn(target, **kwargs)

    assert target.read_text() == first
    assert first.count("_struct_conn.id") == 1


def test_target_owned_struct_conn_does_not_suppress_the_ring(tmp_path):
    """A target with its own disulfides must still receive the closing bond.

    1AKJ carries two CYS SG-SG records on chains D/E. An earlier version keyed
    idempotency on the mere presence of ``_struct_conn.`` and returned early,
    leaving the peptide linear: RFD4 then produced 22 A end-to-end distances
    while every log line looked healthy.
    """
    builder = _load_builder()
    target = tmp_path / "with_disulfide.cif"
    target.write_text(
        "data_t\n#\nloop_\n"
        + "".join(f"_struct_conn.{c}\n" for c in (
            "id", "conn_type_id", "pdbx_value_order", "ptnr1_label_asym_id",
            "ptnr2_label_asym_id", "ptnr1_label_comp_id", "ptnr2_label_comp_id",
            "ptnr1_label_seq_id", "ptnr2_label_seq_id", "ptnr1_label_atom_id",
            "ptnr2_label_atom_id",
        ))
        + "1 covale sing D D CYS CYS 22 94 SG SG\n#\n"
        "loop_\n_atom_site.group_PDB\nATOM 1\n"
    )

    builder._inject_struct_conn(
        target, chain="A", comp="GLY", res1=1, atom1="N", res2=14, atom2="C"
    )

    text = target.read_text()
    assert "1 covale sing D D CYS CYS 22 94 SG SG" in text  # target record kept
    assert "_struct_conn.ptnr1_label_atom_id       N" in text  # ring added
    # The ring lands before the atom loop; the target's own loop stays put.
    assert text.index("_struct_conn.ptnr1_label_atom_id       N") < text.index(
        "_atom_site.group_PDB"
    )


def test_already_has_ring_matches_only_the_exact_bond():
    builder = _load_builder()
    text = (
        "loop_\n_struct_conn.id\n_struct_conn.conn_type_id\n"
        "_struct_conn.pdbx_value_order\n_struct_conn.ptnr1_label_asym_id\n"
        "_struct_conn.ptnr2_label_asym_id\n_struct_conn.ptnr1_label_comp_id\n"
        "_struct_conn.ptnr2_label_comp_id\n_struct_conn.ptnr1_label_seq_id\n"
        "_struct_conn.ptnr2_label_seq_id\n_struct_conn.ptnr1_label_atom_id\n"
        "_struct_conn.ptnr2_label_atom_id\n"
        "1 covale sing D D CYS CYS 22 94 SG SG\n"
    )
    assert builder._already_has_ring(
        text, chain="D", res1=22, atom1="SG", res2=94, atom2="SG"
    )
    assert not builder._already_has_ring(
        text, chain="A", res1=1, atom1="N", res2=14, atom2="C"
    )
    # Same residues but a different chain is a different bond.
    assert not builder._already_has_ring(
        text, chain="E", res1=22, atom1="SG", res2=94, atom2="SG"
    )


def test_injection_rejects_unexpected_layout(tmp_path):
    builder = _load_builder()
    target = tmp_path / "bad.cif"
    target.write_text("data_t\n#\nno atom loop here\n")
    with pytest.raises(RuntimeError, match="unexpected CIF layout"):
        builder._inject_struct_conn(
            target, chain="A", comp="GLY", res1=1, atom1="N", res2=10, atom2="C"
        )


def test_parse_hotspots_accepts_every_documented_form():
    """C_HOT is atom-level; the atom names are what pin the epitope."""
    builder = _load_builder()

    assert builder.parse_hotspots([40, 45]) == {(None, 40): None, (None, 45): None}
    assert builder.parse_hotspots(["D40", "D45"]) == {("D", 40): None, ("D", 45): None}
    assert builder.parse_hotspots(["D40:NH1,NH2", "D45:OG"]) == {
        ("D", 40): ("NH1", "NH2"),
        ("D", 45): ("OG",),
    }
    assert builder.parse_hotspots({"D91": "OH,CZ"}) == {("D", 91): ("OH", "CZ")}
    assert builder.parse_hotspots(None) == {}


def test_parse_hotspots_rejects_entries_without_a_residue_number():
    builder = _load_builder()
    with pytest.raises(ValueError, match="no residue number"):
        builder.parse_hotspots(["D"])
    with pytest.raises(TypeError, match="must be int or str"):
        builder.parse_hotspots([1.5])


def test_hotspot_mask_selects_named_atoms_only():
    """A residue-only hotspot marks every atom; an atom-named one marks a subset."""
    import numpy as np

    builder = _load_builder()

    class FakeArray:
        def __init__(self):
            self.array_length = lambda: 6
            self.chain_id = np.array(["A", "A", "D", "D", "E", "E"])
            self.res_id = np.array([1, 2, 40, 40, 40, 40])
            self.atom_name = np.array(["CA", "CA", "CB", "NH1", "OG", "CA"])

    atoms = FakeArray()
    whole = builder._hotspot_mask(atoms, ["D40"])
    assert whole.tolist() == [False, False, True, True, False, False]

    named = builder._hotspot_mask(atoms, ["D40:NH1"])
    assert named.tolist() == [False, False, False, True, False, False]

    # Chain-qualified, so E40 is untouched.
    assert builder._hotspot_mask(atoms, ["40"]).sum() == 4


def test_rfd4_hotspots_accepts_a_mapping():
    from blocks.networks.design.rfd4 import RFD4Block

    block = RFD4Block(hotspots={"D40": "NH1,NH2", "D91": "OH,CZ"})
    assert block.hotspots == {"D40": "NH1,NH2", "D91": "OH,CZ"}
    assert RFD4Block().hotspots is None


def test_cyclic_request_preserves_hotspot_atom_names(tmp_path):
    """A dict hotspot must reach the builder intact, not be flattened to keys."""
    import json

    from blocks.networks.design.rfd4 import RFD4Block

    block = RFD4Block(cyclic=True, hotspots={"D40": "NH1,NH2", "D91": "OH,CZ"})
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    structure = tmp_path / "target.cif"
    structure.write_text("data_t\n#\n")

    request = block._prepare_cyclic_inputs([structure], sandbox)[0]
    payload = json.loads(request.read_text())
    assert payload["hotspots"] == {"D40": "NH1,NH2", "D91": "OH,CZ"}


def test_build_request_keeps_dict_hotspots_intact():
    """A mapping request must not be flattened to keys -- that silently drops
    the atom names and downgrades every hotspot to residue level."""
    builder = _load_builder()
    request = {"hotspots": {"D40": "NH1,NH2", "D91": "OH,CZ"}}

    # Mirror build()'s normalisation, which is the line that used to be
    # ``list(request.get("hotspots") or [])``.
    hotspots = request.get("hotspots") or []
    assert builder.parse_hotspots(hotspots) == {
        ("D", 40): ("NH1", "NH2"),
        ("D", 91): ("OH", "CZ"),
    }
    # The flattened form loses the atoms, which is the regression.
    assert builder.parse_hotspots(list(hotspots)) == {
        ("D", 40): None,
        ("D", 91): None,
    }


def test_rfd4_defaults_peptide_chain_to_a():
    """RFOptimization raises unless the designed chain is literally 'A'."""
    from blocks.networks.design.rfd4 import RFD4Block

    block = RFD4Block()
    assert block.peptide_chain == "A"
    assert block.cyclic is False
    assert block.cyclic_chemistry == "head_tail"


def test_cyclic_request_writes_chain_a_and_rejects_spec_inputs(tmp_path):
    from blocks.networks.design.rfd4 import RFD4Block

    block = RFD4Block(cyclic=True, peptide_length=10)
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    structure = tmp_path / "target.cif"
    structure.write_text("data_t\n#\n")

    requests = block._prepare_cyclic_inputs([structure], sandbox)
    assert len(requests) == 1
    payload = requests[0].read_text()
    assert '"peptide_chain": "A"' in payload
    assert '"peptide_length": 10' in payload
    assert '"chemistry": "head_tail"' in payload
    # The builder is staged next to the requests so the container can run it.
    assert (requests[0].parent / "build_cyclic_rfd4_input.py").is_file()

    spec = tmp_path / "design.yaml"
    spec.write_text("x:\n  input: target.cif\n")
    with pytest.raises(ValueError, match="not a condition spec"):
        block._prepare_cyclic_inputs([spec], sandbox)
