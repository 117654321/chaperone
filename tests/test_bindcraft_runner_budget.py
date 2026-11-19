"""The BindCraft runner must honour a wall-clock budget and keep accepted work.

BindCraft's ``check_n_trajectories`` counts only trajectories that reach
``Trajectory/Relaxed/``.  A target whose early attempts fail the pLDDT>=0.7 gate
therefore never increments the counter and the loop runs until something else
kills it -- on Slurm that is the time limit, which takes the accepted designs
with it.  The runner wraps the upstream entry point in a budget and reports
success when anything reached ``Accepted/``.
"""

import importlib.util
import json
import signal
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

RUNNER = (
    Path(__file__).resolve().parents[1] / "src/blocks/scripts/run_bindcraft.py"
)


def load_runner(monkeypatch, tmp_path):
    """Import the runner with BINDCRAFT_HOME pointed at a temporary install."""
    spec = importlib.util.spec_from_file_location("run_bindcraft", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    home = tmp_path / "opt" / "BindCraft"
    (home / "functions").mkdir(parents=True)
    (home / "settings_filters").mkdir()
    (home / "settings_advanced").mkdir()
    (home / "settings_filters/default_filters.json").write_text(
        json.dumps({"Average_pLDDT": {"threshold": 0.8, "higher": True}})
    )
    (home / "settings_advanced/default_4stage_multimer.json").write_text(
        json.dumps({"max_trajectories": 100, "af_params_dir": None})
    )
    monkeypatch.setattr(module, "BINDCRAFT_HOME", home)
    return module, home


def write_configs(tmp_path, home):
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    (config_dir / "filter_overrides.json").write_text(
        json.dumps({"Average_pLDDT": {"threshold": 0.5, "higher": True}})
    )
    (config_dir / "advanced_overrides.json").write_text(
        json.dumps({"max_trajectories": 2})
    )
    design_path = tmp_path / "designs"
    design_path.mkdir()
    settings = tmp_path / "target.json"
    settings.write_text(
        json.dumps(
            {
                "design_path": "relative/designs",
                "binder_name": "b",
                "starting_pdb": "relative/target.pdb",
            }
        )
    )
    return settings, config_dir


def test_overrides_are_merged_and_paths_made_absolute(monkeypatch, tmp_path):
    module, home = load_runner(monkeypatch, tmp_path)
    settings, config_dir = write_configs(tmp_path, home)

    filters, advanced = module.render_configs(
        settings,
        "default_filters",
        "default_4stage_multimer",
        config_dir / "filter_overrides.json",
        config_dir / "advanced_overrides.json",
        config_dir / "resolved",
    )

    assert json.loads(filters.read_text())["Average_pLDDT"]["threshold"] == 0.5
    advanced_config = json.loads(advanced.read_text())
    assert advanced_config["max_trajectories"] == 2
    # The in-image executables and parameter dir are pinned, never inherited.
    assert advanced_config["af_params_dir"] == str(home / "params")
    assert advanced_config["dssp_path"] == str(home / "functions/dssp")

    resolved = json.loads(settings.read_text())
    assert Path(resolved["design_path"]).is_absolute()
    assert Path(resolved["starting_pdb"]).is_absolute()


def _fake_popen(monkeypatch, module, *, timeout_when=None, accepted=0):
    """Install a Popen stand-in that either finishes or hangs until terminated."""
    created = {}

    class FakeChild:
        def __init__(self, command):
            self.command = command
            created["command"] = command
            self.terminated = False

        def wait(self, timeout=None):
            if timeout is not None and timeout == timeout_when:
                raise subprocess.TimeoutExpired(self.command, timeout)
            if self.terminated:
                return -signal.SIGTERM
            return 0

        def send_signal(self, sig):
            created["signal"] = sig
            self.terminated = True

        def kill(self):
            created["killed"] = True
            self.terminated = True

    monkeypatch.setattr(module.subprocess, "Popen", FakeChild)
    monkeypatch.setattr(module.os, "chdir", lambda path: None)
    counters = {"accepted": accepted}
    monkeypatch.setattr(module, "_accepted_count", lambda path: counters["accepted"])
    return created


def test_budget_stop_succeeds_when_a_design_was_accepted(monkeypatch, tmp_path):
    module, home = load_runner(monkeypatch, tmp_path)
    settings, config_dir = write_configs(tmp_path, home)
    created = _fake_popen(monkeypatch, module, timeout_when=60, accepted=1)

    status = module.run_with_budget(
        settings, config_dir / "filters.json", config_dir / "advanced.json", 60
    )

    assert status == 0
    assert created["signal"] == signal.SIGTERM


def test_budget_stop_fails_when_nothing_was_accepted(monkeypatch, tmp_path, capsys):
    module, home = load_runner(monkeypatch, tmp_path)
    settings, config_dir = write_configs(tmp_path, home)
    _fake_popen(monkeypatch, module, timeout_when=60, accepted=0)

    status = module.run_with_budget(
        settings, config_dir / "filters.json", config_dir / "advanced.json", 60
    )

    assert status == 1
    assert "No design reached Accepted/" in capsys.readouterr().err


def test_no_budget_is_unbounded(monkeypatch, tmp_path):
    """Without a budget the upstream exit status is passed straight through."""
    module, home = load_runner(monkeypatch, tmp_path)
    settings, config_dir = write_configs(tmp_path, home)
    _fake_popen(monkeypatch, module, timeout_when=None, accepted=0)

    status = module.run_with_budget(
        settings, config_dir / "filters.json", config_dir / "advanced.json", None
    )

    assert status == 0


def test_accepted_count_ignores_hidden_and_other_dirs(tmp_path):
    module = SimpleNamespace()
    spec = importlib.util.spec_from_file_location("run_bindcraft_count", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    design = tmp_path / "designs"
    (design / "Accepted").mkdir(parents=True)
    (design / "Accepted" / "a.pdb").write_text("x")
    (design / "Accepted" / ".hidden.pdb").write_text("x")
    (design / "Trajectory" / "Relaxed").mkdir(parents=True)
    (design / "Trajectory" / "Relaxed" / "b.pdb").write_text("x")

    assert module._accepted_count(design) == 1
