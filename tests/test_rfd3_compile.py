import pytest
from chaperone import get_settings
from blocks.networks.foundry.mpnn import FoundryMPNNBlock
from blocks.networks.foundry.rfdiffusion3 import RFD3Block, RFD3PartialBlock
from blocks.networks.foundry.rfd3na import RFD3NABlock
from blocks.networks.prediction.rosettafold3 import RosettaFold3Block
from chaperone_cli.warmup import main


@pytest.mark.parametrize("cls", [RFD3Block, RFD3PartialBlock])
def test_compile_and_seed_zero_reach_runtime(cls, tmp_path):
    block = cls(command_template=["rfd3", "design"], compile_model=True, seed_offset=0)
    command = block._build_command(str(tmp_path), "input.json", 1, 0)
    assert "compile_model=true" in command
    assert "seed=0" in command
    default = cls(command_template=["rfd3", "design"])
    assert not any(
        x.startswith("compile_model=")
        for x in default._build_command(str(tmp_path), "input.json", 1, 0)
    )


def test_compile_cache_bound_for_rfd3_only(monkeypatch, tmp_path):
    """RFD3 honours RFD3_COMPILE_CACHE_DIR, and its siblings get a host cache too.

    Every Foundry block compiles torch code, so every one of them needs a cache
    outside the container's 64 MB writable tmpfs -- a cache only on RFD3 would
    still let rfd3na / rf3 / foundry_mpnn die with "OSError: No space left on
    device". RFD3 is the only one that reads the explicit
    RFD3_COMPILE_CACHE_DIR setting; the others fall back to the workspace.
    """
    settings = get_settings()
    monkeypatch.setattr(settings, "CHAPERONE_CONTAINER_BACKEND", "apptainer")
    monkeypatch.setattr(settings, "RFD3_COMPILE_CACHE_DIR", str(tmp_path))
    command = RFD3Block(cloud=False).command_template
    assert f"{tmp_path}:/tmp/chaperone-rfd3" in command
    assert "TORCHINDUCTOR_CACHE_DIR=/tmp/chaperone-rfd3/inductor" in command
    assert "TRITON_CACHE_DIR=/tmp/chaperone-rfd3/triton" in command
    assert "TMPDIR=/tmp/chaperone-rfd3" in command

    # Siblings must still redirect their compiler caches off the tmpfs, even
    # though they do not read RFD3_COMPILE_CACHE_DIR. RFD3PartialBlock subclasses
    # RFD3Block, so it inherits the explicit setting and is checked separately.
    for cls in (RFD3NABlock, RosettaFold3Block, FoundryMPNNBlock):
        sibling = cls(cloud=False).command_template
        assert any("TORCHINDUCTOR" in x for x in sibling), cls.__name__

    assert RFD3Block(command_template=["custom"]).command_template == ["custom"]
    monkeypatch.setattr(settings, "RFD3_COMPILE_CACHE_DIR", str(tmp_path / "missing"))
    with pytest.raises(ValueError, match="Create RFD3_COMPILE_CACHE_DIR"):
        RFD3Block(cloud=False)


def test_warmup_preview_is_side_effect_free(tmp_path):
    assert (
        main(
            [
                "--cache-dir",
                str(tmp_path / "cache"),
                "--rundir",
                str(tmp_path / "run"),
                "--dry-run",
            ]
        )
        == 0
    )
    assert list(tmp_path.iterdir()) == []


def test_warmup_uses_engine_with_compile_and_bounded_gpu_request(monkeypatch, tmp_path):
    import chaperone
    from types import SimpleNamespace

    calls = []
    monkeypatch.setattr(chaperone, "init_cli", lambda **kw: None)
    monkeypatch.setattr(get_settings(), "RFD3_COMPILE_CACHE_DIR", None)

    class Engine:
        def __init__(self, **kwargs):
            assert kwargs["rundir"] == str(tmp_path / "run")

        def run(self, block, *, run_args):
            calls.append((block, run_args))
            import numpy as np

            return SimpleNamespace(
                get_data=lambda **kwargs: [
                    SimpleNamespace(atom_array=SimpleNamespace(coord=np.zeros((4, 3))))
                ]
            )

    monkeypatch.setattr(chaperone, "ExecutionEngine", Engine)
    main(
        [
            "--cache-dir",
            str(tmp_path / "cache"),
            "--rundir",
            str(tmp_path / "run"),
            "--local",
        ]
    )
    block, runtime = calls[0]
    assert block.compile_model is True
    assert block.inputs == {"warmup": {"length": "64"}}
    assert (block.n_batches, block.batch_size, block.seed_offset) == (2, 1, 0)
    assert runtime.mode == "local"
    assert runtime.max_retries == 0
    assert runtime.job_args.mem_gb == 32


@pytest.mark.parametrize("mode", ["backend", "modal_context"])
def test_cloud_does_not_mount_host_compile_cache(monkeypatch, tmp_path, mode):
    """Remote runs must not bind a host path that will not exist on the worker.

    The Foundry cache env is emitted for every run (each block compiles torch
    code), but under cloud execution it must point inside the image. Two things
    put a run in that mode: the site backend setting, and an active Modal command
    context. The ``cloud=True`` block flag alone does not -- it only affects
    cmdline arguments such as RFD3's own compile-model switch.
    """
    settings = get_settings()
    monkeypatch.setattr(
        settings, "RFD3_COMPILE_CACHE_DIR", str(tmp_path / "not-created")
    )

    if mode == "backend":
        monkeypatch.setattr(settings, "CHAPERONE_COMPUTE_BACKEND", "modal")
        command = RFD3Block(cloud=False).command_template
    else:
        from chaperone.orchestration import modal_backend

        monkeypatch.setattr(settings, "CHAPERONE_COMPUTE_BACKEND", "local")
        token = modal_backend._COMMAND_CONTEXT.set(modal_backend.CommandContext())
        try:
            command = RFD3Block(cloud=False).command_template
        finally:
            modal_backend._COMMAND_CONTEXT.reset(token)

    # RFD3_COMPILE_CACHE_DIR must never be bound: it is the host-only path.
    assert not any(str(tmp_path / "not-created") in item for item in command)
    # Any cache env that survives must be a container path.
    for item in command:
        if "TORCHINDUCTOR" in item or "TRITON_CACHE_DIR" in item:
            assert "/tmp/" in str(item), item
