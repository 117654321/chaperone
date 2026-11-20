"""RFD4-Proteina reward-guided beam search block.

Wraps upstream's ``rfd4-generate inference_experiment=<beam config>``, which
evaluates candidates *during* generation rather than only after it: at each
configured integration step it branches, scores every branch with the configured
rewards, and continues only from the survivors. With an AF3 interface reward that
means the sampler is steered toward poses that actually dock.

Why this runs on the host rather than in the RFD4 SIF
-----------------------------------------------------
The AF3 oracle does not run inside the RFD4 runtime. ``af3_oracle.py`` builds an
``apptainer run <AF3_IMAGE> ...`` command, so the process needs ``apptainer`` on
PATH. Inside the RFD4 SIF there is no apptainer, and a container cannot start a
nested one -- the search dies at warmup with::

    AF3 daemon error: AF3 worker failed during warmup:
    [Errno 2] No such file or directory: 'apptainer'

So this block is ``_inline``: it shells out to a host RFD4 installation
(``rfd4_generate`` / a conda env's ``rfd4-generate``), which has apptainer, and
lets the oracle spawn its own SIF per refold. That is the deployment upstream
documents; it is also why upstream's docs never mention running search from a
container.

Cost
----
One oracle call per branch per checkpoint. The default config below has three
checkpoints at ``n_branch=2``, so roughly 6-12 AF3 refolds per design. Budget GPU
time accordingly; this is far more expensive per design than plain ``rfd4``
generation.

The per-refold cost is *not* a container start. ``AF3Oracle.setup()`` spawns a
warm worker (``af3_daemon.py``) once per process: a single ``apptainer run ...
--serve`` process loads AF3 and then reads manifest paths off stdin, while
``_dispatch_fold`` sends each batch through a Unix socket. Measured on this
target, the first fold pays the warm-up (27 s) and every later one costs 4-6 s.

That daemon needs ``AF3_IMAGE`` / ``AF3_MODEL_DIR`` / ``AF3_JAX_CACHE_DIR``, which
reach it from the checkout's ``.env.local`` via ``rfproteina.utils.env``. When any
is missing, ``serve --skip-if-no-env`` exits immediately and the oracle silently
falls back to spawning one apptainer per refold. The run log says which route was
taken: ``routing N designs via daemon at ...`` or ``via direct apptainer call``.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from pydantic import Field

from chaperone import BlockFunction, JobArgs, PipelineDataHandler, get_setting_field
from chaperone.block_config import TIER_PRIMARY
from chaperone.common import tail_block_log
from chaperone.data import make_row

logger = logging.getLogger(__name__)

# The host RFD4 checkout and its conda env are both required settings: search
# needs a real checkout with apptainer, and guessing a path here would only fail
# later with a confusing error.
RFD4_DEFAULT_ENV = "RFD4_Proteina"


def _rfd4_repo() -> Path:
    configured = get_setting_field("RFD4_REPO", "") or ""
    if not configured:
        raise FileNotFoundError(
            "rfd4_search needs RFD4_REPO: the path to an RFD4-Proteina checkout "
            "whose environment has apptainer. Search runs on the host, not in the "
            "runtime SIF."
        )
    path = Path(configured).expanduser()
    if not (path / ".project-root").is_file():
        raise FileNotFoundError(
            f"RFD4 checkout not found at {path} (no .project-root marker). "
            "Set RFD4_REPO to the checkout used for host-side search."
        )
    return path


def _rfd4_python(repo: Path) -> Path:
    """Interpreter to run ``rfd4-generate`` with.

    A conda env name (``RFD4_ENV``) wins; otherwise the checkout's own ``.venv``.
    Search needs apptainer on PATH, so this must be a *host* environment, not the
    runtime SIF.
    """
    env_name = get_setting_field("RFD4_ENV", "") or RFD4_DEFAULT_ENV
    conda = shutil.which("conda")
    if conda and env_name:
        candidate = Path(conda).parent.parent / "envs" / env_name / "bin" / "python"
        if candidate.is_file():
            return candidate
        # `conda info --base` handles installs whose envs live elsewhere.
        try:
            base = subprocess.run(
                [conda, "info", "--base"], capture_output=True, text=True, check=True
            ).stdout.strip()
            candidate = Path(base) / "envs" / env_name / "bin" / "python"
            if candidate.is_file():
                return candidate
        except subprocess.SubprocessError:
            pass
    venv = repo / ".venv" / "bin" / "python"
    if venv.is_file():
        return venv
    raise FileNotFoundError(
        f"No host RFD4 interpreter found for env {env_name!r} or {venv}. "
        "Search runs on the host because its AF3 oracle needs apptainer."
    )


class RFD4SearchBlock(BlockFunction):
    """Reward-guided beam search with RFD4-Proteina, on the host.

    Emits the surviving designs after search, with ``search.reward`` and the
    oracle metric columns (``oracle_ppi.min_ipae_coi``, ``.iptm_coi``, ...) on
    each row.
    """

    _name = "rfd4_search"
    _display_name = "RFD4-Proteina Search"
    _description = "RFD4 reward-guided beam search with an AF3 refolding oracle"
    _inline = True
    _chunked = False
    _requires_input = False

    _resources = JobArgs(
        partition="gpu",
        gpu_class="large",
        mem_gb=64,
        cpus_per_task=8,
        time_limit="12:00:00",
    )

    inputs: Optional[str] = Field(
        None,
        description=(
            "Condition spec (YAML/JSON) or conditioned CIF to search over. A spec "
            "is resolved and staged by RFD4 itself."
        ),
    )
    search_config: Optional[str] = Field(
        None,
        description=(
            "Path to a beam-search experiment YAML (an ``inference_experiment`` "
            "config). None uses the checkout's ``inference_beam_example``."
        ),
    )
    ckpt_path: Optional[str] = Field(
        None,
        json_schema_extra={"tier": TIER_PRIMARY},
        description=(
            "Local model bundle. Search must not download weights: the oracle "
            "spawns containers on a host that is typically offline, and HF hub "
            "access fails before search starts. Defaults to RFD4_WEIGHTS_DIR."
        ),
    )
    num_replicates: int = Field(1, description="Designs to search per input.")
    batch_size: int = Field(1, description="Sampler batch size.")
    seed: Optional[int] = Field(None, description="Base seed.")
    extra_overrides: list[str] = Field(
        default_factory=list,
        description="Extra Hydra overrides, e.g. ['search.beam_width=4'].",
    )
    output_subdir: str = Field(
        "search_run", description="Directory under the block sandbox for RFD4 output."
    )

    # ── helpers ────────────────────────────────────────────────────────────

    def _resolve_weights(self) -> Path:
        if self.ckpt_path:
            candidate = Path(self.ckpt_path).expanduser()
            if candidate.is_dir() and (candidate / "model.safetensors").is_file():
                return candidate.resolve()
            raise ValueError(
                f"ckpt_path must be a directory holding model.safetensors: {candidate}"
            )
        configured = get_setting_field("RFD4_WEIGHTS_DIR", "") or ""
        if not configured:
            raise FileNotFoundError(
                "rfd4_search needs a local weight bundle: set RFD4_WEIGHTS_DIR or "
                "ckpt_path. Search must not download weights -- the oracle host is "
                "usually offline and an HF fetch fails before search starts."
            )
        path = Path(configured).expanduser()
        if not (path / "model.safetensors").is_file():
            raise FileNotFoundError(
                f"RFD4 weights not found in {path}. Set RFD4_WEIGHTS_DIR or ckpt_path."
            )
        return path.resolve()

    def _search_config_name(self, repo: Path) -> str:
        """Name of an ``inference_experiment`` config visible to Hydra.

        Hydra resolves ``inference_experiment=`` against the packaged
        ``rfproteina/configs`` directory only, so an arbitrary path will not
        load. A config outside the checkout is copied in before running, and
        removed again afterwards.
        """
        if self.search_config is None:
            return "inference_beam_example"
        source = Path(self.search_config).expanduser()
        if not source.is_file():
            raise FileNotFoundError(f"search_config not found: {source}")
        target = repo / "configs" / "inference_experiment" / source.name
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
            logger.info(f"staged search config {source} -> {target}")
        return source.stem

    # ── main entry point ───────────────────────────────────────────────────

    def __call__(self, handler, sandbox_dir, **kwargs):
        root = Path(sandbox_dir).resolve()
        root.mkdir(parents=True, exist_ok=True)
        out_dir = root / self.output_subdir

        if self.inputs is None:
            raise ValueError("rfd4_search needs inputs=<spec or conditioned CIF>")
        # Inline blocks have no `stage_file` (that lives on CompiledBlockFunction),
        # so copy the input next to the run ourselves. A spec resolves its own
        # `input:` paths relative to the spec file, so keep the structures that
        # sit beside it too.
        source = Path(self.inputs).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"inputs not found: {source}")
        staged_inputs = root / "inputs" / source.name
        staged_inputs.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, staged_inputs)
        if source.suffix.lower() in (".yaml", ".yml", ".json"):
            for sibling in source.parent.iterdir():
                if sibling.is_file() and sibling.suffix.lower() in (".cif", ".bcif", ".pdb"):
                    shutil.copy2(sibling, staged_inputs.parent / sibling.name)

        repo = _rfd4_repo()
        python = _rfd4_python(repo)
        weights = self._resolve_weights()

        config_name = self._search_config_name(repo)
        # Copied configs must not outlive the run: a stale copy would shadow the
        # next run's file and silently disappear from the checkout's git status.
        staged_config = (
            repo / "configs" / "inference_experiment" / Path(self.search_config).name
            if self.search_config
            else None
        )

        command = [
            str(python), "-m", "rfproteina.generate",
            f"inference_experiment={config_name}",
            f"inputs={staged_inputs}",
            f"out_dir={out_dir}",
            f"num_replicates={self.num_replicates}",
            f"batch_size={self.batch_size}",
            # A local bundle: the oracle host is usually offline, and an HF hub
            # fetch fails before search ever starts.
            f"hf_ckpt_path={weights}",
            "compress_outputs=false",
            *self.extra_overrides,
        ]
        if self.seed is not None:
            command.append(f"seed={self.seed}")

        env = os.environ.copy()
        env["PYTHONPATH"] = f"{repo / 'src'}:{env.get('PYTHONPATH', '')}"
        env.setdefault("PROJECT_ROOT", str(repo))
        env.setdefault("ALLOW_BIOTITE_CCD", "True")
        # The oracle shells out to apptainer; a proxy env leaks in and breaks
        # httpx (missing socksio) or DNS inside the child container.
        for key in ("http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY",
                    "HTTPS_PROXY", "ALL_PROXY"):
            env.pop(key, None)
        env["no_proxy"] = "*"
        env["NO_PROXY"] = "*"

        log_path = root / "rfd4_search.log"
        logger.info("running: %s", " ".join(command))
        try:
            with log_path.open("w") as log:
                completed = subprocess.run(
                    command, cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT
                )
            if completed.returncode != 0:
                raise RuntimeError(
                    f"rfd4-search exited {completed.returncode}. "
                    f"Log tail:\n{tail_block_log(str(root))}"
                )

            return self.compile(str(root))
        finally:
            if staged_config is not None and staged_config.is_file():
                staged_config.unlink()
                logger.info("removed staged search config %s", staged_config)

    # ── output compilation ────────────────────────────────────────────────

    def compile(self, sandbox_dir):
        """One row per surviving design, carrying reward and oracle metrics."""
        import csv
        import json

        root = Path(sandbox_dir)
        out_dir = root / self.output_subdir
        samples = sorted(out_dir.glob("inference_samples/**/*_generated.cif"))
        if not samples:
            raise RuntimeError(
                f"rfd4_search produced no structures under {out_dir}. "
                f"Log tail:\n{tail_block_log(str(root))}"
            )

        # per_example_metrics.csv holds one row per surviving design, keyed by
        # the sample directory name. Join on that so each structure carries the
        # reward it was selected for.
        metrics_by_id: dict[str, dict] = {}
        for csv_path in out_dir.glob("inference_metrics/*per_example_metrics.csv"):
            with csv_path.open(newline="") as handle:
                for row in csv.DictReader(handle):
                    key = row.get("example_id") or ""
                    metrics_by_id[key] = row

        rows = []
        for path in samples:
            sample_id = path.parent.name
            raw = metrics_by_id.get(sample_id, {})
            metrics: dict[str, float] = {}
            for name, value in raw.items():
                if name in ("example_id", "designed_structure_path", ""):
                    continue
                try:
                    metrics[name] = float(value)
                except (TypeError, ValueError):
                    continue
            rows.append(
                make_row(
                    name=self.name,
                    path=str(path),
                    metadata={"task": sample_id, "generated_file": path.name},
                    metrics={self.name: metrics} if metrics else {self.name: {}},
                    path_handle=None,
                )
            )
        return PipelineDataHandler(rows)
