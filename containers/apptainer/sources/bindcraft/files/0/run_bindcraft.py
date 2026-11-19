"""Prepare BindCraft presets and execute the upstream entry point.

This script is copied into the BindCraft container.  Keeping preset resolution
inside the image lets the Chaperone block expose small override dictionaries
without vendoring BindCraft's large JSON files into Chaperone itself.

BindCraft's ``max_trajectories`` counts only trajectories that reach the relax
step (``Trajectory/Relaxed/``); trajectories rejected for low pLDDT or clashes
are not counted, so a target that keeps failing makes the loop unbounded.  The
Slurm ``time_limit`` would kill the job and lose the accepted designs with it,
so the run is wrapped in a wall-clock budget instead: at the deadline the child
is stopped and whatever reached ``Accepted/`` is kept.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

BINDCRAFT_HOME = Path("/opt/BindCraft")


def _read_json(path: Path) -> dict:
    with path.open() as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise TypeError(f"Expected a JSON object in {path}")
    return value


def _preset_path(value: str, category: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or candidate.parent != Path("."):
        return candidate
    if candidate.suffix != ".json":
        candidate = candidate.with_suffix(".json")
    return BINDCRAFT_HOME / category / candidate.name


def _merge_config(source: Path, overrides_path: Path, destination: Path) -> Path:
    config = _read_json(source)
    config.update(_read_json(overrides_path))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")
    return destination


def _accepted_count(design_path: Path) -> int:
    accepted = design_path / "Accepted"
    if not accepted.is_dir():
        return 0
    return sum(1 for p in accepted.glob("*.pdb") if not p.name.startswith("."))


def render_configs(
    settings: Path,
    filters_arg: str,
    advanced_arg: str,
    filter_overrides: Path,
    advanced_overrides: Path,
    config_dir: Path,
) -> None:
    """Resolve presets and overrides in place, keeping caller paths absolute.

    BindCraft changes directory to its own install root, so any relative input
    path in the settings file would be resolved against that root.  Rewriting
    them here keeps the caller's paths valid.
    """
    filters = _merge_config(
        _preset_path(filters_arg, "settings_filters"),
        filter_overrides,
        config_dir / "filters.json",
    )
    advanced = _merge_config(
        _preset_path(advanced_arg, "settings_advanced"),
        advanced_overrides,
        config_dir / "advanced.json",
    )

    # BindCraft fills blank values similarly, but explicit in-image paths make
    # the generated run configuration self-describing and deterministic.
    advanced_config = _read_json(advanced)
    advanced_config.update(
        {
            "af_params_dir": str(BINDCRAFT_HOME / "params"),
            "dssp_path": str(BINDCRAFT_HOME / "functions" / "dssp"),
            "dalphaball_path": str(BINDCRAFT_HOME / "functions" / "DAlphaBall.gcc"),
        }
    )
    advanced.write_text(json.dumps(advanced_config, indent=2, sort_keys=True) + "\n")

    settings_config = _read_json(settings)
    for key in ("starting_pdb", "design_path"):
        value = settings_config.get(key)
        if isinstance(value, str) and value:
            settings_config[key] = str(Path(value).expanduser().resolve())
    settings.write_text(json.dumps(settings_config, indent=2) + "\n")
    return filters, advanced


def run_with_budget(
    settings: Path, filters: Path, advanced: Path, seconds: float | None
) -> int:
    """Run the upstream entry point, stopping it at the deadline.

    Returns 0 when at least one design reached ``Accepted/`` -- including runs
    that were cut short -- so the block can still compile what was produced.
    """
    design_path = Path(_read_json(settings)["design_path"])
    command = [
        "/opt/bindcraft-env/bin/python",
        "-u",
        str(BINDCRAFT_HOME / "bindcraft.py"),
        "--settings",
        str(settings),
        "--filters",
        str(filters),
        "--advanced",
        str(advanced),
    ]
    os.chdir(BINDCRAFT_HOME)
    child = subprocess.Popen(command)
    try:
        returncode = child.wait(timeout=seconds)
    except subprocess.TimeoutExpired:
        print(
            f"BindCraft exceeded its {seconds / 3600:.2f} h budget; stopping it and "
            "keeping whatever reached Accepted/.",
            flush=True,
        )
        child.send_signal(signal.SIGTERM)
        try:
            child.wait(timeout=600)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
        returncode = None

    if _accepted_count(design_path):
        return 0
    if returncode is None:
        print(
            "No design reached Accepted/ before the budget expired. Raise "
            "trajectory_budget_hours, add trajectories, or relax the filters.",
            file=sys.stderr,
            flush=True,
        )
        return 1
    return returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Run BindCraft with merged presets")
    parser.add_argument("--settings", required=True)
    parser.add_argument("--filters", default="default_filters")
    parser.add_argument("--advanced", default="default_4stage_multimer")
    parser.add_argument("--filter-overrides", required=True)
    parser.add_argument("--advanced-overrides", required=True)
    parser.add_argument("--config-dir", required=True)
    parser.add_argument(
        "--trajectory-budget-hours",
        type=float,
        default=None,
        help=(
            "Wall-clock budget. BindCraft's max_trajectories counts only successful "
            "trajectories, so failing targets run indefinitely without this."
        ),
    )
    args = parser.parse_args()

    config_dir = Path(args.config_dir).resolve()
    settings = Path(args.settings).resolve()
    filters, advanced = render_configs(
        settings,
        args.filters,
        args.advanced,
        Path(args.filter_overrides),
        Path(args.advanced_overrides),
        config_dir,
    )
    seconds = (
        args.trajectory_budget_hours * 3600
        if args.trajectory_budget_hours is not None
        else None
    )
    sys.exit(run_with_budget(settings, filters, advanced, seconds))


if __name__ == "__main__":
    main()
