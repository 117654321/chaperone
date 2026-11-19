"""RFD4 reward-guided search block: host execution plumbing.

The block exists because upstream's AF3 oracle cannot run inside the RFD4
runtime SIF -- ``af3_oracle.py`` shells out to ``apptainer``, and a container
cannot start a nested one. Everything here is about getting a *host* RFD4
process launched correctly; the search itself is upstream's.

These tests use a fake interpreter so they never touch a GPU or the real
checkout.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

def _load_block_module():
    """Import normally, not by file path.

    The block uses `from __future__ import annotations`, so pydantic resolves its
    field types through the module's entry in ``sys.modules``. Loading by path
    leaves no such entry and pydantic fails with "class not fully defined".
    """
    import blocks.networks.design.rfd4_search as module

    return module


def test_block_is_inline_and_unchunked():
    """It must run on the host; a containerised block cannot reach apptainer.

    ``_inline=True`` keeps it in the host Python process. ``_chunked=False``
    because search is inherently sequential -- branches are compared against
    each other within one run.
    """
    module = _load_block_module()
    assert module.RFD4SearchBlock._inline is True
    assert module.RFD4SearchBlock._chunked is False


def test_missing_checkout_fails_loudly(monkeypatch):
    """A wrong RFD4_REPO must not silently fall back to a container run."""
    module = _load_block_module()
    monkeypatch.setattr(module, "get_setting_field", lambda name, default="": str(Path("/nope")))
    with pytest.raises(FileNotFoundError, match="no .project-root marker"):
        module._rfd4_repo()


def test_missing_interpreter_lists_both_candidates(monkeypatch, tmp_path):
    """The error must say which env name and which venv were tried."""
    module = _load_block_module()
    monkeypatch.setattr(module.shutil, "which", lambda name: None)
    monkeypatch.setattr(module, "get_setting_field", lambda name, default="": "NoSuchEnv")
    with pytest.raises(FileNotFoundError, match="NoSuchEnv"):
        module._rfd4_python(tmp_path)


def test_weights_must_be_a_bundle_dir(tmp_path):
    module = _load_block_module()
    block = module.RFD4SearchBlock(ckpt_path=str(tmp_path))
    with pytest.raises(ValueError, match="model.safetensors"):
        block._resolve_weights()

    (tmp_path / "model.safetensors").write_bytes(b"x")
    assert block._resolve_weights() == tmp_path.resolve()


def test_search_config_is_copied_into_the_package(tmp_path):
    """Hydra resolves `inference_experiment=` only inside rfproteina/configs.

    A config living anywhere else has to be copied in, or the run dies at
    config composition with "Could not load".
    """
    module = _load_block_module()
    repo = tmp_path / "repo"
    (repo / "configs" / "inference_experiment").mkdir(parents=True)
    external = tmp_path / "my_search.yaml"
    external.write_text("search: {}\n")

    block = module.RFD4SearchBlock(search_config=str(external))
    name = block._search_config_name(repo)

    assert name == "my_search"
    assert (repo / "configs" / "inference_experiment" / "my_search.yaml").is_file()


def test_default_config_name_needs_no_copy(tmp_path):
    module = _load_block_module()
    repo = tmp_path / "repo"
    (repo / "configs" / "inference_experiment").mkdir(parents=True)
    block = module.RFD4SearchBlock()
    assert block._search_config_name(repo) == "inference_beam_example"


def test_spec_siblings_are_staged_with_the_spec(tmp_path):
    """A spec's `input:` values are relative to it, so the structures must follow."""
    module = _load_block_module()

    source_dir = tmp_path / "src"
    source_dir.mkdir()
    spec = source_dir / "binder.yaml"
    spec.write_text("x:\n  input: target.cif\n")
    (source_dir / "target.cif").write_text("data_t\n#\n")

    sandbox = tmp_path / "sandbox"
    block = module.RFD4SearchBlock(inputs=str(spec), ckpt_path=None)

    # The staging copy happens before the repo is resolved, so making repo
    # lookup raise stops the run right after the files are in place.
    class _Stop(Exception):
        pass

    def _boom():
        raise _Stop()

    mp = pytest.MonkeyPatch()
    mp.setattr(module, "_rfd4_repo", _boom)
    try:
        with pytest.raises(_Stop):
            block({}, sandbox)
    finally:
        mp.undo()

    staged = sandbox / "inputs"
    assert (staged / "binder.yaml").is_file()
    assert (staged / "target.cif").is_file()


def test_compile_reads_reward_from_per_example_metrics(tmp_path):
    """Each structure row must carry the reward it was selected for."""
    module = _load_block_module()

    out = tmp_path / "search_run"
    sample = out / "inference_samples" / "design_1" / "design_1_generated.cif"
    sample.parent.mkdir(parents=True)
    sample.write_text("data_x\n#\n")
    metrics_dir = out / "inference_metrics"
    metrics_dir.mkdir()
    (metrics_dir / "run_per_example_metrics.csv").write_text(
        "example_id,designed_structure_path,search.reward,oracle_ppi.min_ipae_coi\n"
        "design_1,/x/design_1_generated.cif,43.6,0.98\n"
    )

    block = module.RFD4SearchBlock(output_subdir="search_run")
    handler = block.compile(str(tmp_path))
    # unpack() flattens the nested metrics JSON into dot-separated columns.
    frame = handler.unpack()

    assert len(frame) == 1
    assert frame["rfd4_search.search.reward"].iloc[0] == pytest.approx(43.6)
    assert frame["rfd4_search.oracle_ppi.min_ipae_coi"].iloc[0] == pytest.approx(0.98)


def test_compile_without_structures_names_the_log(tmp_path):
    module = _load_block_module()
    block = module.RFD4SearchBlock()
    with pytest.raises(RuntimeError, match="produced no structures"):
        block.compile(str(tmp_path))
