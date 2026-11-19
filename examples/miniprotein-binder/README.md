# Miniprotein binder design with RFO

Design a de novo 50–120 residue protein binder against PD-L1, then let
RFOptimization re-design its sequence against a Boltz-2 refold before AF3 refolds
and scores the interface.

Target and conditioning are upstream's own binder recipe
(`docs/how-to/binder-in-10-lines.md`): PD-L1 chain A from PDB 5O45, residues
17–131, with three side-chain hotspots on the PD-1/PD-L1 interface. Binder length
and hotspot atoms are upstream's numbers, so a poor result is attributable to the
pipeline rather than to guessed parameters.

## Pipeline

```text
rfd4(spec) → rfoptimization → af3 → filter
```

RFD4 samples backbones against the target, RFO runs `total_cycles` of "Boltz
refold → MPNN redesign" on the designed chain, AF3 refolds the optimised complex,
and a metric filter gates on interface confidence.

## Why a spec instead of block fields

RFD4 accepts two input shapes. The cyclic-peptide example drives it with block
fields because a ring is expressed through the peptide chain and its closing
bond. A linear binder has no such structure; it needs a contig and per-condition
selections, which is the condition-spec (YAML) form:

```yaml
pdl1_binder:
  input: pdl1_target.cif
  contig: "50-120, /0, B1-115"
  conditions:
    C_CRDGRP: {1: [{select: "sel('B/*/*/[N,CA,C,O]')"}]}   # target backbone, pose free
    C_SEQ:    {true: [{select: "sel('B')"}]}                # target sequence known
    C_HOT:    {true: [{select: "sel('B/*/40/[CG,OH]')"}, ...]}
```

`files/prep_target.py` generates that file, so the residue numbers stay correct
if the crop ever changes.

## Chain naming and residue numbering

Two adjustments, both forced:

| Adjustment | Why |
|---|---|
| Target moves A → B | RFOptimization raises unless the designed chain is literally named `A`. The contig builds the binder first, so it takes `A`. |
| Residues renumber −16 | The shipped crop starts at PDB residue 17, so PDB Y56 / M115 / Y123 become B40 / B99 / B107. `prep_target.py` derives these and verifies each hotspot's atoms exist before writing the spec. |

Upstream's hotspots, verified against the structure:

| Local | PDB | Residue | Atoms |
|---|---|---|---|
| B40 | Y56 | Tyr | CG, OH |
| B99 | M115 | Met | CG, SD |
| B107 | Y123 | Tyr | CD2, OH |

## Run

```bash
# once, to stage the target and write the spec
python examples/miniprotein-binder/files/prep_target.py

# once, to cache PD-L1's MSA (~30-35 minutes; every later run reuses it)
python examples/miniprotein-binder/files/prep_target.py --msa

# smoke test: one design, one RFO cycle
python examples/miniprotein-binder/pipeline.py --test --local --rundir=/abs/path/miniprotein-smoke

# production
python examples/miniprotein-binder/pipeline.py --local --rundir=/abs/path/miniprotein \
    --replicates 4 --cycles 3

# reward-guided search instead of RFD4 + RFO (see below)
python examples/miniprotein-binder/pipeline.py --search --local \
    --rundir=/abs/path/miniprotein-search --replicates 1
```

Drop `--local` to submit to Slurm.

## Two ways to iterate

The default pipeline generates first and evaluates afterwards: RFD4 produces
backbones, RFO redesigns their sequences against a Boltz refold, AF3 scores the
result. Improvement happens *between* rounds.

`--search` uses upstream's reward-guided beam search, which improves *inside*
generation: at each configured integration step it branches, folds every branch
with an AF3 oracle, and continues only from the branches that dock well.

```bash
python examples/miniprotein-binder/pipeline.py --search --local --rundir=...
```

The reward config lives in `files/search/pdl1_beam.yaml`:

| Checkpoint | Metric | Reward |
|---|---|---|
| 20 | `interchain_interactions` | H-bonds + hydrophobic contacts, no oracle yet |
| 40 | `oracle_ppi` | minimises interface PAE; keeps branches under 5 Å |
| 60 | `oracle_ppi` | interface PAE plus pTM |

Measured on this target: 4 replicates produced 8 designs in about 6.5 minutes
(32 AF3 folds). Four passed the same gate the default pipeline uses
(iptm ≥ 0.70, pLDDT ≥ 70):

| Design | iptm | pLDDT | interface PAE | reward | Passed |
|---|---|---|---|---|---|
| binder_0_bsc2_2 | **0.910** | 92.75 | **0.885 Å** | 42.1 | ✅ |
| binder_0_bsc2_3 | 0.900 | 92.25 | 0.875 Å | 41.6 | ✅ |
| binder_1_bsc2_0 | 0.860 | **93.06** | 1.34 Å | 42.2 | ✅ |
| binder_2_bsc2_0 | 0.860 | 91.45 | 1.16 Å | 42.3 | ✅ |
| binder_3_bsc2_1 | 0.670 | 89.48 | 2.47 Å | 39.5 | |
| binder_2_bsc2_2 | 0.660 | 87.24 | 2.56 Å | 38.4 | |
| binder_3_bsc2_3 | 0.620 | 89.82 | 3.07 Å | 38.9 | |
| binder_1_bsc2_3 | 0.450 | 81.31 | 4.19 Å | 36.3 | |

Caveat on units: `oracle_ppi.iptm_coi` and `ptm_coi` are percentages in the CSV
(`91.0` is iptm 0.910); `plddt_coi` is already 0–100 and `min_ipae_coi` is ångström.

Survival is uneven per replicate — replicate 0 kept both branches, replicate 3
kept neither:

| Replicate | Designs | Passed |
|---|---|---|
| 0 | 2 | 2 |
| 1 | 2 | 1 |
| 2 | 2 | 1 |
| 3 | 2 | 0 |

An earlier 1-replicate run produced 2 survivors at iptm 0.83–0.89 / PAE
0.98–1.39 Å, so the pattern repeats: search reaches the same ~0.91 ceiling as the
default RFD4+RFO pipeline.

The difference is cost, not quality. Branching turns 4 replicates into 8
candidates, of which 4 pass — the same absolute yield as RFD4+RFO run 2 (4/4)
and better than run 1 (3/4), but at twice the generated designs and 32 AF3 folds
inside generation. The pass *rate* drops (4/8 versus 3/4 and 4/4) because the
second branch of each replicate is a divergence, not an independent draw. On
this target beam search did **not** beat generate-then-filter.

What it does buy: every surviving design has already been folded, so the reward
and the score come from the same run, and the discarded branches are visible in
the log rather than silently absent.

**`--search` runs on the host, not in the runtime SIF.** Upstream's AF3 oracle
builds an `apptainer run` command, and a container cannot start a nested one —
inside the SIF the search dies at warmup with
`[Errno 2] No such file or directory: 'apptainer'`. The block therefore shells
out to a host RFD4 install: point `RFD4_REPO` at that checkout and `RFD4_ENV` at
a conda environment inside it that has `apptainer` on PATH. Both are settings;
the block's defaults suit this machine only.

Cost: up to 6–12 AF3 refolds per replicate (3 checkpoints × `n_branch=2`). The
measured 4-replicate run took 32 folds and about 6.5 minutes wall clock. Much
more expensive per design than plain RFD4.

Those refolds do **not** each start a container. `AF3Oracle.setup()` spawns one
warm worker (`af3_daemon.py`): a single `apptainer run ... --serve` process loads
AF3 once and reads manifests off stdin, with `_dispatch_fold` routing through a
Unix socket. Measured here, the first fold pays a 27 s warm-up and each later one
costs 4–6 s. RFO achieves the same thing differently — its SIF bundles RF3, Boltz
and MPNN, so `boltz_runner.py` finds `boltz_sif=""` and calls the in-image binary
directly. RFD4 cannot copy that: its image is NVIDIA's prebuilt one and the oracle
hardcodes `apptainer run`, so a merged image would not change the call path.

If the run log says `via direct apptainer call` instead of `via daemon at ...`,
the daemon declined to start — `AF3_IMAGE` / `AF3_MODEL_DIR` / `AF3_JAX_CACHE_DIR`
were unset and `serve --skip-if-no-env` exited. That is a 27 s cost per refold.

## The MSA is not optional

Measured on the cyclic-peptide example with the same pipeline: eight designs
scored iptm 0.09–0.21 / pLDDT 37–47 without a target MSA, and iptm 0.32–0.77 /
pLDDT 86–90 with one. Nothing about the designs changed between those runs.

AF3 in single-sequence mode has no evolutionary signal for the receptor, so it
cannot fold the receptor confidently regardless of binder quality. Scores from a
no-MSA run measure AF3's ignorance of the target, not the design.

The designed binder correctly stays MSA-free: a novel sequence has no homologs to
find.

## Results

Two full runs with the same configuration — 4 replicates, 3 RFO cycles, PD-L1 MSA
supplied (15944 rows, 4 templates). Reported separately because the spread
between them shows what n=4 can and cannot tell you.

Run 1:

| Design | Length | iptm | ptm | pLDDT | interface PAE | Passed |
|---|---|---|---|---|---|---|
| binder_2 | 69 | 0.910 | 0.920 | 92.0 | 0.88 Å | ✅ |
| binder_0 | 61 | 0.820 | 0.880 | 89.8 | 1.39 Å | ✅ |
| binder_3 | 111 | 0.770 | 0.840 | 90.9 | 1.86 Å | ✅ |
| binder_1 | 101 | 0.390 | 0.660 | 85.0 | 5.50 Å | |

Run 2:

| Design | Length | iptm | ptm | pLDDT | interface PAE | Passed |
|---|---|---|---|---|---|---|
| binder_2 | 69 | **0.900** | 0.920 | 92.5 | **0.87 Å** | ✅ |
| binder_1 | 101 | 0.840 | 0.880 | 92.1 | 1.37 Å | ✅ |
| binder_0 | 61 | 0.840 | 0.880 | 90.1 | 1.33 Å | ✅ |
| binder_3 | 111 | 0.820 | 0.870 | 91.8 | 1.71 Å | ✅ |

**Run 1 passed 3/4, run 2 passed 4/4.** iptm 0.39–0.91 across both.

The two runs differ in seed and in the lengths RFD4 sampled, and the same design
index lands in very different places: binder_1 was 0.390 in run 1 and 0.840 in
run 2; binder_3 was 0.770 then 0.820. Four designs is enough to see the pipeline
working and not enough to rank binders — treat a single 4-design run as a smoke
test, and run 20+ before drawing conclusions about which designs are better.

Run 2's distribution is tight — iptm 0.82–0.90, pLDDT 90.1–92.5, PAE 0.87–1.71 Å —
so ~0.8 is a reproducible level for this setup, not a lucky draw.

The same pipeline without the MSA scored iptm 0.210 / pLDDT 67.8 on a single
design, so the comparison is directionally clear even at n=1:

| | no MSA | with MSA |
|---|---|---|
| iptm | 0.210 | 0.39–0.91 |
| pLDDT | 67.8 | 85.0–92.5 |
| interface PAE | 9.73 Å | 0.87–5.50 Å |
| passed | 0/1 | 3/4 and 4/4 |

Note the sign convention on `AF3_iPTM` in RFO's records: despite the name it holds
**Boltz's** iptm (`boltz_runner.py` reads it from Boltz confidence), not AF3's.
Treat the two as independent opinions, not as one pipeline agreeing with itself.

These are computational screening scores. Passing the filter means AF3 finds the
designed complex plausible, not that the binder binds.

## Files

| File | Purpose |
|---|---|
| `pipeline.py` | The four-stage pipeline |
| `files/prep_target.py` | Extract PD-L1 (chain B, renumbered) and write `binder.yaml` |
| `files/prep_target.py --msa` | Run the AF3 genetic search once and cache the target MSA |
| `files/pdl1_target.cif` | The target as RFD4 reads it (generated) |
| `files/binder.yaml` | The condition spec driving RFD4 (generated) |
| `files/search/pdl1_beam.yaml` | Beam-search reward config for `--search` |
| `files/.cache/pdl1_msa.json` | Cached MSA (generated, ~30 min) |
