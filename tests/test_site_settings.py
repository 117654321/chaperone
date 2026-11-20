"""Optional site files retain IPD behavior without imposing it on new installs."""

import os

import chaperone.settings as module
from chaperone.settings import ChaperoneSettings, _find_env_files


def test_supplied_ipd_file_loads_and_environment_map_merges(tmp_path, monkeypatch):
    root = tmp_path / "checkout"
    source = root / "src/chaperone"
    source.mkdir(parents=True)
    (root / ".env").write_text("CHAPERONE_COMPUTE_BACKEND=auto\n")
    (root / ".env.ipd").write_text(
        "CHAPERONE_DEFAULT_PARTITION=cpu\nCHAPERONE_GPU_PARTITION=gpu\n"
        'CHAPERONE_GRES_MAP=\'{"small":"gpu:small:1","large":"gpu:large:1"}\'\n'
    )
    monkeypatch.setattr(module, "__file__", str(source / "settings.py"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("CHAPERONE_SITE", raising=False)
    monkeypatch.delenv("CHAPERONE_ENV_FILE", raising=False)
    monkeypatch.setenv("CHAPERONE_GRES_MAP", '{"small":"gpu:t4:1"}')
    settings = ChaperoneSettings(_env_file=_find_env_files())
    assert settings.CHAPERONE_DEFAULT_PARTITION == "cpu"
    assert settings.CHAPERONE_GPU_PARTITION == "gpu"
    assert settings.CHAPERONE_GRES_MAP == {"small": "gpu:t4:1", "large": "gpu:large:1"}


def test_no_site_file_is_portable(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "__file__", str(tmp_path / "package/settings.py"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    for name in os.environ:
        if name.startswith("CHAPERONE_"):
            monkeypatch.delenv(name, raising=False)
    settings = ChaperoneSettings(_env_file=_find_env_files())
    assert settings.CHAPERONE_DEFAULT_PARTITION is None
    assert settings.CHAPERONE_GPU_PARTITION is None
    assert settings.CHAPERONE_GRES_MAP == {}
    assert settings.CHAPERONE_ROOT == tmp_path
    assert settings.ESM_WEIGHTS_DIR.startswith(str(tmp_path))


def test_installed_package_accepts_supplied_working_directory_ipd(
    tmp_path, monkeypatch
):
    install = tmp_path / "installed/chaperone/settings.py"
    monkeypatch.setattr(module, "__file__", str(install))
    work = tmp_path / "work"
    work.mkdir()
    (work / ".env.ipd").write_text("CHAPERONE_GPU_PARTITION=gpu\n")
    monkeypatch.chdir(work)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("CHAPERONE_SITE", raising=False)
    monkeypatch.delenv("CHAPERONE_ENV_FILE", raising=False)
    assert str(work / ".env.ipd") in _find_env_files()


def test_installed_package_loads_working_directory_local_overrides(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "__file__", str(tmp_path / "installed/chaperone/settings.py"))
    work = tmp_path / "work"
    work.mkdir()
    (work / ".env.local").write_text("CHAPERONE_GPU_PARTITION=accelerated\n")
    monkeypatch.chdir(work)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("CHAPERONE_SITE", raising=False)
    monkeypatch.delenv("CHAPERONE_ENV_FILE", raising=False)
    settings = ChaperoneSettings(_env_file=_find_env_files())
    assert settings.CHAPERONE_GPU_PARTITION == "accelerated"


def test_rfd4_fields_are_declared():
    """RFD4 keys must be fields, or extra="ignore" silently drops them.

    The rfd4 and rfd4_search blocks read these through get_setting_field, which
    is a getattr with a default: an undeclared field always resolves to the
    default, so a value written to .env.local looks set but never arrives.
    """
    assert {"RFD4_SIF", "RFD4_WEIGHTS_DIR", "RFD4_REPO", "RFD4_ENV"} <= set(
        ChaperoneSettings.model_fields
    )


def test_env_local_rfd4_values_survive(tmp_path, monkeypatch):
    root = tmp_path / "checkout"
    source = root / "src/chaperone"
    source.mkdir(parents=True)
    # A .env at the checkout root stops the upward search for one, exactly as the
    # real repository layout does. Without it _find_env_files() would walk on to
    # whatever directory above tmp_path happens to contain a .env (for example
    # /tmp/.env on a developer machine) and .env.local would never be read.
    (root / ".env").write_text("")
    (root / ".env.local").write_text("RFD4_REPO=/tmp/x\nRFD4_SIF=/tmp/y.sif\n")
    monkeypatch.setattr(module, "__file__", str(source / "settings.py"))
    monkeypatch.chdir(root)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("CHAPERONE_SITE", raising=False)
    monkeypatch.delenv("CHAPERONE_ENV_FILE", raising=False)
    for name in ("RFD4_REPO", "RFD4_SIF", "RFD4_WEIGHTS_DIR", "RFD4_ENV"):
        monkeypatch.delenv(name, raising=False)

    settings = ChaperoneSettings(_env_file=_find_env_files())

    assert settings.RFD4_REPO == "/tmp/x"
    assert settings.RFD4_SIF == "/tmp/y.sif"
    assert settings.RFD4_WEIGHTS_DIR is None
    assert settings.RFD4_ENV is None
