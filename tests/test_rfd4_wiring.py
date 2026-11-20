"""RFD4 wiring that unit tests can pin without a GPU or the runtime SIF.

Three failures here are silent by nature, so each gets a test:

* a motif parameter the bundled builder never reads (while the docs promised
  the ring would be pinned to those coordinates);
* ``RFD4_SIF`` being honoured by the registry but not by the command that runs;
* one host-side image lookup aborting discovery of every other block.

Blocks are imported normally, not by file path: they use
``from __future__ import annotations``, so pydantic resolves field types through
``sys.modules`` and a path-loaded module fails with "class not fully defined".
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def test_motif_without_custom_builder_is_rejected():
    """The bundled builder ignores 'motif'; accepting it ships a linear ring."""
    import blocks.networks.design.rfd4 as module

    with pytest.raises(Exception, match="cyclic_builder"):
        module.RFD4Block(
            cyclic=True,
            cyclic_motif_template="/tmp/motif.cif",
            cyclic_motif_chain="E",
            cyclic_motif_res_ids=[1, 2, 3],
        )


def test_motif_with_custom_builder_is_accepted():
    import blocks.networks.design.rfd4 as module

    block = module.RFD4Block(
        cyclic=True,
        cyclic_motif_template="/tmp/motif.cif",
        cyclic_builder="/tmp/custom_builder.py",
    )
    assert block.cyclic_motif_template == "/tmp/motif.cif"


def test_command_resolves_the_image_through_the_setting(monkeypatch, tmp_path):
    """create_command must use _get_image, which honours RFD4_SIF.

    Before this, the command kept the placeholder Image from _script_spec and
    the run path looked the container up in CHAPERONE_CONTAINER_DIRS only: a
    valid RFD4_SIF was ignored and the job died with "Run 'chaperone install
    rfd4'", which has no recipe to run.
    """
    import blocks.networks.design.rfd4 as module

    def _sentinel(cls=None):
        raise RuntimeError("resolved via _get_image")

    monkeypatch.setattr(module.RFD4Block, "_get_image", classmethod(_sentinel))

    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "model.safetensors").write_bytes(b"x")
    structure = tmp_path / "input.cif"
    structure.write_text("data_x\n")

    block = module.RFD4Block(inputs=str(structure), ckpt_path=str(bundle))
    with pytest.raises(RuntimeError, match="resolved via _get_image"):
        block.create_command(block.init_handler(), tmp_path / "sandbox", 0)


def test_one_broken_image_does_not_abort_container_discovery(monkeypatch):
    """A missing SIF warns and skips; other blocks must still enumerate."""
    import blocks as blocks_pkg

    class Fine:
        name = "fine"

        class _image:
            name = "fine"

        @staticmethod
        def _get_image():
            return Fine._image()

    class Broken:
        @staticmethod
        def _get_image():
            raise FileNotFoundError("no sif on this host")

    monkeypatch.setattr(
        blocks_pkg,
        "Blocks",
        {"broken": Broken, "fine": Fine},
        raising=True,
    )
    monkeypatch.setattr(blocks_pkg, "_CONTAINER_VARIANTS", {}, raising=True)

    containers = blocks_pkg.get_all_containers()

    assert "fine" in containers
    assert "broken" not in containers


def test_config_inside_the_checkout_is_never_staged_or_deleted(tmp_path):
    """_staged_config_path must mirror the copy: in-place configs stay put.

    The cleanup runs in a finally block, so a wrong answer here deletes the
    user's own search config after a successful run.
    """
    import blocks.networks.design.rfd4_search as module

    repo = tmp_path / "repo"
    configs = repo / "configs" / "inference_experiment"
    configs.mkdir(parents=True)
    inside = configs / "mine.yaml"
    inside.write_text("search: {}\n")

    block = module.RFD4SearchBlock(search_config=str(inside))
    assert block._staged_config_path(repo) is None

    outside = tmp_path / "elsewhere.yaml"
    outside.write_text("search: {}\n")
    copied = module.RFD4SearchBlock(search_config=str(outside))
    assert copied._staged_config_path(repo) == configs / "elsewhere.yaml"

    assert module.RFD4SearchBlock()._staged_config_path(repo) is None
