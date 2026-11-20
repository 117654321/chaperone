"""RFD4-Proteina design block.

Wraps the official RFD4-Proteina runtime image, which upstream publishes as a
prebuilt Apptainer SIF on Hugging Face rather than as a recipe. The image pins
its own Python 3.12 environment (atomworks 3.0.4, torch 2.14.1+cu126), which does
not coexist with the Foundry image's atomworks 3.0.1, so this block references
that SIF directly instead of building a container.

The CLI is a Hydra app, not a flag-based one:

    rfd4-generate inputs=<cif> num_replicates=N out_dir=<dir> hf_ckpt_path=<bundle>

Outputs land under ``<out_dir>/inference_samples/<input-stem>/`` as
``*_generated.cif`` plus a metrics CSV under ``<out_dir>/inference_metrics/``.
"""

from __future__ import annotations

import logging
import json
import os
import shutil
from pathlib import Path
from typing import Optional, Union

from pydantic import Field, model_validator

from chaperone import CompiledBlockFunction, JobArgs, PipelineDataHandler, get_setting_field
from chaperone.block_config import TIER_PRIMARY, ScriptSpec
from chaperone.common import tail_block_log
from chaperone.containers import Image
from chaperone.data import make_row

logger = logging.getLogger(__name__)

# Upstream publishes these; keep the URL in one place so the error message and
# the default setting agree.
RFD4_SIF_URL = (
    "https://huggingface.co/nvidia/RFD4-Proteina/resolve/main/"
    "runtime/rfd4-proteina-cu12-amd64.sif"
)
SIF_FILENAME = "rfd4-proteina-cu12-amd64.sif"


def _default_sif() -> Path:
    """Where the SIF lands when RFD4_SIF is unset.

    Images live in the container search path, so honour CHAPERONE_CONTAINER_DIRS
    (the same setting every other block resolves images through) rather than
    hardcoding one machine's layout. The SIF is a runtime, not model data, so it
    does not sit beside the weights.
    """
    from chaperone.containers import get_container_dirs

    dirs = get_container_dirs()
    return (dirs[0] if dirs else Path.home() / ".chaperone" / "containers") / SIF_FILENAME


def _default_weights() -> Path:
    """Model bundle directory when RFD4_WEIGHTS_DIR is unset."""
    return Path.home() / ".chaperone" / "models" / "rfd4"


def _rfd4_sif_path() -> Path:
    """Resolve the RFD4 runtime SIF.

    ``RFD4_SIF`` overrides; otherwise the first container search directory is
    used.
    """
    configured = get_setting_field("RFD4_SIF", "") or ""
    path = Path(configured).expanduser() if configured else _default_sif()
    if not path.is_file():
        raise FileNotFoundError(
            f"RFD4 runtime image not found: {path}\n"
            f"Download it with:\n"
            f"  curl -L -o {path} \\\n    {RFD4_SIF_URL}"
        )
    return path


def _rfd4_weights_dir() -> Path:
    """Resolve the directory holding config.json and model.safetensors."""
    configured = get_setting_field("RFD4_WEIGHTS_DIR", "") or ""
    path = Path(configured).expanduser() if configured else _default_weights()
    if not (path / "model.safetensors").is_file():
        raise FileNotFoundError(
            f"RFD4 weights not found in {path} (expected model.safetensors). "
            "Download config.json and model.safetensors from nvidia/RFD4-Proteina, "
            "or point RFD4_WEIGHTS_DIR at the bundle directory."
        )
    return path


def _container_spec() -> Image:
    """Image spec for the prebuilt runtime SIF.

    Resolved lazily: the path comes from a setting, so evaluating it at import
    time would freeze one machine's layout. ``build_command`` re-checks the file
    when a job actually runs.
    """
    return Image.from_existing("rfd4", _rfd4_sif_path())


class RFD4Block(CompiledBlockFunction):
    """RFD4-Proteina structure generation."""

    _name = "rfd4"
    _display_name = "RFD4-Proteina"
    _description = "RFD4-Proteina flow-matching biomolecular design"
    _script_spec = ScriptSpec(
        command=["rfd4-generate"],
        # Placeholder: the real spec is resolved per run by _get_image, because
        # the SIF path comes from a setting.
        image=Image(name="rfd4"),
        source_url="https://github.com/RosettaCommons/RFD4-Proteina",
    )

    @classmethod
    def _get_image(cls) -> Image:
        """Resolve the prebuilt runtime SIF from RFD4_SIF at use time.

        Resolving it when the class is defined would freeze one machine's layout
        into the import path, and the file is not present on every host that
        merely imports the block registry.
        """
        return _container_spec()
    _resources = JobArgs(
        partition="gpu",
        gpu_class="large",
        mem_gb=48,
        cpus_per_task=4,
        time_limit="6:00:00",
        rows_per_job=50,
    )
    _inline = False
    _chunked = True
    # RFD4 reads a conditioned CIF per input, so an upstream handler is optional:
    # pass either ``inputs=<cif>`` or a data handler with structures.
    _requires_input = False

    inputs: Union[str, dict, None] = Field(
        default=None,
        description=(
            "Path to a conditioned CIF/PDB, a directory of them, a JSON/YAML design "
            "spec, or a spec dict written inline. When a data handler is supplied "
            "instead, each row's structure is used as its own input. Relative "
            "``input:`` paths inside a dict resolve against the working directory."
        ),
    )
    ckpt_path: Optional[str] = Field(
        default=None,
        json_schema_extra={"tier": TIER_PRIMARY},
        description=(
            "Model bundle: an HF repo id or a local directory holding "
            "config.json and model.safetensors. None uses RFD4_WEIGHTS_DIR."
        ),
    )
    num_replicates: int = Field(
        1,
        description="Designs generated per input.",
    )
    batch_size: int = Field(
        1,
        description="Sampler batch size (RFD4 config key ``batch_size``).",
    )
    seed: Optional[int] = Field(
        None,
        description="Base seed; each chunk offsets it by the chunk index.",
    )
    extra_overrides: list[str] = Field(
        default_factory=list,
        description=(
            "Additional Hydra overrides passed verbatim, e.g. "
            "['recycle_strategy=high'] or ['length=120']."
        ),
    )

    # ── cyclic peptide design ───────────────────────────────────────────
    # RFD4 has no cyclization switch. The ring goes in as a condition on the
    # input structure: a placeholder peptide chain whose sequence and
    # coordinates are both designed, plus one _struct_conn covale record
    # joining its first and last residue.
    cyclic: bool = Field(
        False,
        description=(
            "Design a macrocyclic peptide binder. Rewrites each input into a "
            "conditioned CIF carrying a placeholder peptide chain and a closing "
            "_struct_conn record, then designs against it."
        ),
    )
    peptide_length: int = Field(
        12,
        gt=1,
        description="Residues in the cyclic peptide (used only when cyclic=True).",
    )
    peptide_chain: str = Field(
        "A",
        description=(
            "Chain id for the designed peptide. Defaults to 'A' because downstream "
            "RFOptimization hard-requires the designed chain to be named A. A "
            "collision with a target chain is an error, not an auto-rename."
        ),
    )
    target_chains: Optional[list[str]] = Field(
        default=None,
        description=(
            "Target chains to keep and condition on. None keeps every chain in "
            "the input."
        ),
    )
    hotspots: Optional[Union[list[int | str], dict[str, str]]] = Field(
        default=None,
        description=(
            "Target atoms the peptide should contact (C_HOT). C_HOT is an "
            "atom-level condition, so naming the side-chain atoms is what pins "
            "the binder to the intended epitope; a bare residue number lets the "
            "model pick any atom of that residue. Accepts 40, 'D40', "
            "'D40:NH1,NH2', or {'D40': 'NH1,NH2'}."
        ),
    )
    cyclic_chemistry: str = Field(
        "head_tail",
        description=(
            "Ring chemistry: 'head_tail' (N1-C12 amide, closes reliably), "
            "'disulfide' (Cys SG-SG), or 'isopeptide' (Lys NZ-C). Head-to-tail "
            "is the only chemistry upstream measures at 100% closure."
        ),
    )
    # ── optional motif pinning (added for the alphaVbeta6 RGD work) ──────
    cyclic_motif_template: Optional[str] = Field(
        default=None,
        description=(
            "Requires cyclic_builder: only a custom builder pins the ring. The "
            "CIF holds the motif's measured coordinates, in the SAME frame as the "
            "input structure; the ring's first residues are then conditioned on "
            "them (C_CRD + C_SEQ) instead of designed. Setting this without "
            "cyclic_builder is an error, not a silent no-op."
        ),
    )
    cyclic_motif_chain: str = Field(
        "E", description="Chain id of the motif inside cyclic_motif_template."
    )
    cyclic_motif_res_ids: Optional[list[int]] = Field(
        default=None,
        description="Residue ids of the motif in the template, in ring order.",
    )
    cyclic_builder: Optional[str] = Field(
        default=None,
        description=(
            "Path to an alternative cyclic-input builder supporting 'motif'. "
            "Defaults to the bundled build_cyclic_rfd4_input.py."
        ),
    )

    @model_validator(mode="after")
    def _motif_needs_a_builder_that_reads_it(self):
        """Reject motif pinning the bundled builder cannot honour.

        ``_prepare_cyclic_inputs`` writes the motif block into the builder
        request, but ``build_cyclic_rfd4_input.py`` never reads it: its
        placeholder peptide is fully designed (``C_SEQ = <M>``, ``C_CRD`` NaN
        everywhere). Accepting the setting would produce an unpinned ring while
        the docs promised pinned coordinates — a silent scientific error, not a
        cosmetic one. Fail here instead, before any GPU time is spent.
        """
        if self.cyclic_motif_template and not self.cyclic_builder:
            raise ValueError(
                "cyclic_motif_template is set but cyclic_builder is not: the "
                "bundled builder does not read 'motif', so the ring would be "
                "designed instead of pinned. Pass cyclic_builder=<a builder "
                "that applies C_CRD + C_SEQ to the motif residues>, or drop "
                "cyclic_motif_template and condition on hotspots only."
            )
        return self

    # ── command construction ────────────────────────────────────────────

    def init_handler(self):
        """Seed one structure row per input.

        RFD4 is a source block whose conditioned structures are its inputs.
        Creating real structure rows (rather than empty placeholders) lets the
        chunk machinery slice them and keeps ``create_command`` able to read each
        row's staged path.

        An inline spec dict has no structure file to point at yet, so it gets one
        row per design entry with the row left pathless; ``create_command`` stages
        the structures and writes the spec.
        """
        from chaperone.data import make_row

        if isinstance(self.inputs, dict):
            rows = [
                make_row(name=self.name, path="", metadata={"source_input": key}, metrics={})
                for key in self.inputs
            ]
            return PipelineDataHandler(rows)

        paths = self._input_paths()
        rows = [
            make_row(
                name=self.name,
                path=str(p),
                metadata={"source_input": p.stem},
                metrics={},
            )
            for p in paths
        ]
        return PipelineDataHandler(rows)

    def _input_paths(self, sandbox_dir: Path | None = None) -> list[Path]:
        """Expand ``inputs`` into concrete input files.

        A spec (file or inline dict) is returned as a single path; the caller
        stages it. Structure files return one path each.

        An inline dict is written to ``<sandbox>/inputs/design.json`` with every
        ``input:`` rewritten to an absolute path inside the sandbox, mirroring
        what RFD3 does. Staging the structures locally means the container never
        needs the caller's directory bound.
        """
        if not self.inputs:
            raise ValueError(
                "rfd4 needs inputs=<cif|pdb|yaml|json|dir|dict> when no data "
                "handler is given."
            )

        if isinstance(self.inputs, dict):
            if sandbox_dir is None:
                raise ValueError(
                    "Inline dict inputs need a sandbox to stage the spec into; "
                    "this is supplied automatically during a run."
                )
            return [self._materialise_spec_dict(self.inputs, Path(sandbox_dir))]

        source = Path(self.inputs).expanduser()
        if source.is_dir():
            paths = sorted(
                p
                for p in source.iterdir()
                if p.suffix in (".cif", ".pdb", ".gz", ".yaml", ".yml", ".json")
            )
            if not paths:
                raise ValueError(f"No RFD4 inputs found in {source}")
            return paths
        if source.is_file():
            return [source]
        raise FileNotFoundError(f"RFD4 input path does not exist: {source}")

    def _materialise_spec_dict(self, spec: dict, sandbox_dir: Path) -> Path:
        """Write an inline spec dict to the sandbox with absolute structure paths.

        Every ``input:`` is resolved (relative paths against the working
        directory, like RFD3) and copied into the sandbox, so the value written
        to the spec is a path the container can actually see.
        """
        import json

        staging = sandbox_dir / "inputs"
        staging.mkdir(parents=True, exist_ok=True)

        resolved: dict = {}
        for name, entry in spec.items():
            if not isinstance(entry, dict):
                raise TypeError(
                    f"RFD4 spec {name!r} must map to a dict, got "
                    f"{type(entry).__name__}"
                )
            entry = dict(entry)
            source = entry.get("input")
            if source:
                src_path = Path(source).expanduser()
                if not src_path.is_absolute():
                    src_path = Path.cwd() / src_path
                if not src_path.is_file():
                    raise FileNotFoundError(
                        f"RFD4 spec {name!r} refers to a missing structure: "
                        f"{src_path}"
                    )
                entry["input"] = str(
                    Path(self.stage_file(str(src_path), str(staging), subdir="structures"))
                )
            resolved[name] = entry

        spec_path = staging / "design.json"
        spec_path.write_text(json.dumps(resolved, indent=2, sort_keys=False) + "\n")
        return spec_path

    @staticmethod
    def _is_spec(path: Path) -> bool:
        """True for a YAML/JSON condition spec rather than a structure file.

        A spec describes its own designs (possibly several) and receives
        ``num_replicates`` up front, so it runs once per file instead of once
        per row.
        """
        return path.suffix.lower() in (".yaml", ".yml", ".json")

    def _resolve_bundle(self) -> tuple[str, Path]:
        """Return (bundle argument for the CLI, host path to bind)."""
        if self.ckpt_path:
            candidate = Path(self.ckpt_path).expanduser()
            if candidate.is_dir():
                if not (candidate / "model.safetensors").is_file():
                    raise ValueError(
                        f"ckpt_path directory has no model.safetensors: {candidate}"
                    )
                return str(candidate), candidate.resolve()
            # Otherwise treat it as an HF repo id; weights are read from HF_HOME.
            return self.ckpt_path, _rfd4_weights_dir()
        weights = _rfd4_weights_dir()
        return str(weights.resolve()), weights.resolve()

    def _collect_inputs(self, handler, sandbox_dir: Path) -> list[Path]:
        """Resolve each input row's file, staging only plain structure files.

        A condition spec is left where it lives: its ``input:`` paths resolve
        relative to the spec file, so copying the spec elsewhere would silently
        break them. The spec's own directory is bound into the container instead.
        """
        staged: list[Path] = []

        for loaded in handler.get_data(which="last"):
            if not loaded.path:
                # Placeholder row from an inline spec; handled before this point.
                continue
            source = Path(loaded.path).expanduser()
            if self._is_spec(source):
                staged.append(source.resolve())
                continue
            staged.append(
                Path(self.stage_file(str(source), str(sandbox_dir), subdir="inputs"))
            )

        if not staged:
            raise ValueError("RFD4 received no input structures to design against.")
        return staged

    # ── cyclization ─────────────────────────────────────────────────────

    def _prepare_cyclic_inputs(
        self, inputs: list[Path], sandbox_dir: Path
    ) -> list[Path]:
        """Rewrite each input into a conditioned cyclic CIF.

        RFD4 has no cyclization flag. The ring is expressed the way upstream's
        ``docs/examples/inputs/cyclic_binders`` inputs do it: an extra peptide
        chain of residue slots with zeroed backbone atoms, whose sequence and
        coordinates are both left to the model, plus one ``_struct_conn``
        ``covale`` record joining the first and last residue.

        The builder needs atomworks + rfproteina, which only exist inside the
        runtime image, so it is staged next to the inputs, bound into the
        container, and run there under the same environment as the generator.
        """
        builder = (
            Path(self.cyclic_builder).expanduser().resolve()
            if self.cyclic_builder
            else Path(__file__).resolve().parents[2] / "scripts"
            / "build_cyclic_rfd4_input.py"
        )
        if not builder.is_file():
            raise FileNotFoundError(f"cyclic input builder missing: {builder}")

        cyclic_dir = sandbox_dir / "cyclic_inputs"
        cyclic_dir.mkdir(parents=True, exist_ok=True)
        staged_builder = cyclic_dir / builder.name
        shutil.copy2(builder, staged_builder)

        rewritten: list[Path] = []
        for entry in inputs:
            if self._is_spec(entry):
                raise ValueError(
                    "cyclic=True takes structure inputs (CIF/PDB), not a "
                    f"condition spec: {entry}. Point inputs= at the target "
                    "structure and set target_chains/epitope hotspots instead."
                )
            request_name = f"{entry.stem}_cyclic.json"
            request_path = cyclic_dir / request_name
            output_path = cyclic_dir / f"{entry.stem}_cyclic.cif"
            request_path.write_text(
                json.dumps(
                    {
                        "input": str(entry),
                        "output": str(output_path),
                        "target_chains": list(self.target_chains or []),
                        # Keep a mapping as-is: the builder accepts both the list
                        # and dict forms, and list() would drop the atom names.
                        "hotspots": self.hotspots or [],
                        "peptide_chain": self.peptide_chain,
                        "peptide_length": self.peptide_length,
                        "chemistry": self.cyclic_chemistry,
                        **(
                            {
                                "motif": {
                                    "template": str(
                                        Path(self.cyclic_motif_template)
                                        .expanduser()
                                        .resolve()
                                    ),
                                    "chain": self.cyclic_motif_chain,
                                    "res_ids": list(self.cyclic_motif_res_ids or []),
                                }
                            }
                            if self.cyclic_motif_template
                            else {}
                        ),
                    },
                    indent=2,
                )
                + "\n"
            )
            rewritten.append(request_path)

        return rewritten

    def _cyclic_design_runs(
        self,
        requests: list[Path],
        sandbox_dir: Path,
        bundle_arg: str,
        seed: int | None,
    ) -> tuple[str, list[str]]:
        """Bash that builds each cyclic CIF, then generates against it.

        The builder runs inside the same image as the generator, so the build
        and every design can share one container invocation. A builder failure
        aborts the chunk: designing against the raw target would silently
        produce linear peptides instead of a ring.
        """
        build_lines = []
        design_lines = []
        # The builder was staged next to the requests; use whichever file is
        # actually there rather than assuming the bundled name.
        builder_name = (
            Path(self.cyclic_builder).name
            if self.cyclic_builder
            else "build_cyclic_rfd4_input.py"
        )
        for idx, request in enumerate(requests):
            cif = request.with_suffix(".cif")
            build_lines.append(f"python {request.parent / builder_name} {request}\n")
            out_dir = sandbox_dir / f"sample_{idx}"
            args = [
                "rfd4-generate",
                f"inputs={cif}",
                f"num_replicates={self.num_replicates}",
                f"batch_size={self.batch_size}",
                f"out_dir={out_dir}",
                f"hf_ckpt_path={bundle_arg}",
            ]
            if seed is not None:
                args.append(f"seed={seed}")
            args.extend(self.extra_overrides)
            design_lines.append(" ".join(args) + "\n")
        return "".join(build_lines), design_lines

    def create_command(self, handler, sandbox_dir, chunk_id):
        sandbox_dir = Path(os.path.abspath(sandbox_dir))

        if isinstance(self.inputs, dict):
            # Inline spec: stage the structures and write the spec into the
            # sandbox. `init_handler` produced pathless placeholder rows, so the
            # normal structure-staging path below does not apply.
            inputs = [self._materialise_spec_dict(self.inputs, sandbox_dir)]
        else:
            inputs = self._collect_inputs(handler, sandbox_dir)

        bundle_arg, weights_dir = self._resolve_bundle()
        seed = (self.seed + chunk_id) if self.seed is not None else None

        # A cyclic run rewrites every input into a conditioned CIF first, inside
        # the same container (the builder needs atomworks + rfproteina). Both
        # trees live under the sandbox, which the engine already binds.
        if self.cyclic:
            inputs = self._prepare_cyclic_inputs(inputs, sandbox_dir)

        # RFD4's Hydra CLI takes one ``inputs=`` per invocation. A condition spec
        # already describes every design it wants, so it runs once; a plain
        # structure file yields one run per file.
        if self.cyclic:
            # Each entry is a builder request; the CIF it writes is what gets
            # designed against, so the build step comes first in the script.
            build_lines, design_lines = self._cyclic_design_runs(
                inputs, sandbox_dir, bundle_arg, seed
            )
            script_body = build_lines + "".join(f"{r}\n" for r in design_lines)
        else:
            runs: list[str] = []
            for idx, entry in enumerate(inputs):
                out_dir = sandbox_dir / f"sample_{idx}"
                args = [
                    "rfd4-generate",
                    f"inputs={entry}",
                    f"num_replicates={self.num_replicates}",
                    f"batch_size={self.batch_size}",
                    f"out_dir={out_dir}",
                    f"hf_ckpt_path={bundle_arg}",
                ]
                if seed is not None:
                    args.append(f"seed={seed}")
                args.extend(self.extra_overrides)
                runs.append(" ".join(args))
            script_body = "\n".join(runs) + "\n"

        script = sandbox_dir / f"run_rfd4_chunk{chunk_id}.sh"
        script.write_text("#!/bin/bash\nset -euo pipefail\n" + script_body)
        script.chmod(0o755)

        # Bind the weight bundle so hf_ckpt_path resolves to real files inside
        # the container, and bind each spec's directory so its relative input
        # paths resolve as authored.
        binds = [(str(weights_dir), str(weights_dir))]
        for entry in inputs:
            if self._is_spec(entry):
                spec_dir = entry.parent.resolve()
                if (str(spec_dir), str(spec_dir)) not in binds:
                    binds.append((str(spec_dir), str(spec_dir)))

        # Host-backed compiler cache. The sandbox lives inside the run directory,
        # which the engine already binds, so writing here survives the tmpfs layer.
        cache_root = (sandbox_dir / ".cache").resolve()
        for sub in ("inductor", "triton", "torch", "xdg"):
            (cache_root / sub).mkdir(parents=True, exist_ok=True)

        # Resolve the real SIF here, not the placeholder in _script_spec: the
        # container run path would otherwise look the image up in
        # CHAPERONE_CONTAINER_DIRS and ignore RFD4_SIF entirely, failing with
        # "Run 'chaperone install rfd4'" even though the file exists.
        container_cmd = self._get_image().build_command(
            "bash",
            str(script),
            binds=binds,
            env={
                # --containall --no-mount home leaves HOME on the container's
                # small writable-tmpfs layer. RFD4's inductor/Triton compile
                # caches are hundreds of MB at batch>1 and overflow it with
                # "OSError: [Errno 28] No space left on device". Point HOME and
                # every cache at the work folder, which the engine binds.
                "HF_HOME": "/tmp/hfhome",
                "HOME": str(cache_root),
                "TORCHINDUCTOR_CACHE_DIR": str(cache_root / "inductor"),
                "TRITON_CACHE_DIR": str(cache_root / "triton"),
                "TORCH_HOME": str(cache_root / "torch"),
                "XDG_CACHE_HOME": str(cache_root / "xdg"),
            },
        )
        return container_cmd

    # ── output compilation ──────────────────────────────────────────────

    def compile(self, sandbox_dir):
        return compile_rfd4(sandbox_dir, name=self.name)


def compile_rfd4(sandbox_dir, name="rfd4"):
    """Collect generated CIFs from every per-input ``inference_samples`` tree."""
    sandbox = Path(sandbox_dir)
    paths = sorted(
        p
        for p in sandbox.rglob("inference_samples/**/*.cif")
        if p.is_file()
    )
    if not paths:
        raise RuntimeError(
            f"RFD4 finished but produced no structures under {sandbox}. "
            "Check the per-sample directories and the job log."
            + tail_block_log(str(sandbox))
        )

    rows = []
    for path in paths:
        # inference_samples/<input-stem>/<input-stem>_generated.cif
        input_stem = path.parent.name
        metadata = {
            "task": input_stem,
            "generated_file": path.name,
            "source_input": input_stem,
        }
        metrics = {
            "path": str(path),
            "n_generated": 1,
        }
        rows.append(
            make_row(
                name=name,
                path=str(path),
                metadata=metadata,
                metrics={name: metrics},
            )
        )
    return PipelineDataHandler(rows)
