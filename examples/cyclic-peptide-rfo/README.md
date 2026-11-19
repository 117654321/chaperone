# Cyclic peptide binder design with RFO

Design a head-to-tail macrocyclic peptide against PD-1, then let RFOptimization
re-design its sequence against a Boltz-2 refold before AF3 refolds and scores the
interface.

The target, peptide length, chemistry and hotspots all come from RFD4's own
cyclic-peptide example (`docs/examples/inputs/cyclic_binders/01_PD1_head_tail_12.cif.zst`),
where this configuration closes 16/16 over 16 replicates. Starting from upstream's
measured baseline keeps a poor result attributable to the pipeline rather than to
guessed parameters.

## Pipeline

```text
rfd4(cyclic=True) → rfoptimization(cyclic=True) → af3 → filter
```

RFD4 samples the ring, RFO runs `total_cycles` of "Boltz refold → MPNN redesign"
on it, AF3 refolds the optimised complex, and a metric filter gates on interface
confidence.

## How cyclization is expressed

RFD4 has no cyclization flag and needs no cyclic template. The ring reaches the
model as one `_struct_conn` `covale` record joining the first and last residue,
and the peptide chain is a run of placeholder residues whose backbone is zeroed
with sequence and coordinates both left to the model (`C_SEQ = <M>`, no
`C_CRD`). That is exactly the layout upstream ships in
`docs/examples/inputs/cyclic_binders/`.

`cyclic=True` on the rfd4 block writes that conditioned CIF for you:

```python
RFD4(
    inputs="pd1_target.cif",
    cyclic=True,
    peptide_length=12,
    peptide_chain="A",
    target_chains=["B"],
    hotspots={"B33": "CG1,CG2", ...},
    cyclic_chemistry="head_tail",
)
```

Upstream names the designed chain `P`; this pipeline renames it to `A` because
RFOptimization requires that, and rebuilds the peptide rather than reusing
upstream's placeholder so the two agree.

Three settings are not cosmetic:

| Setting | Why |
|---|---|
| `peptide_chain="A"` | RFOptimization raises unless the designed chain is literally named `A`. The block defaults to this. |
| `backprop_fraction=0.0` | RFO's `cyclic` flag only reaches the Boltz branch. Any RF3 fraction leaves the ring unconstrained, and it drifts open. |
| `cyclic_chemistry="head_tail"` | The only chemistry upstream measures at 100% closure (16/16). Disulfide manages 12/16 and isopeptide 1/16 when the ring has no input coordinates. |

## Hotspots are atom-level

`C_HOT` is an atom-level condition. Naming only a residue number lets the model
pick any atom of it, and with a handful of residues that leaves it free to dock
on the wrong face — observed on a previous target as designs landing on the back
of the receptor while nominally "using" the hotspots. Name the side-chain atoms:

```python
HOTSPOTS = {"B33": "CG1,CG2", "B95": "CB,CG2", "B97": "CB,CD1,CD2,CG", "B102": "CD,CG,NE2,OE1"}
# or equivalently ["B33:CG1,CG2", ...]
```

The four entries are the exact atoms upstream marks on PD-1 in its cyclic-peptide
input.

## Measuring closure

Closure is `|d − ideal| ≤ 0.3 Å` against the 1.33 Å head-to-tail amide, and the
test is two-sided on purpose. A one-sided "closed if under 2.3 Å" cut scores an
impossible overshoot — atoms inside each other — as a success.

`pipeline.py` prints the measured distance for every design before spending GPU
time on RFO, so a broken ring is visible immediately.

## Run

```bash
# once, to stage the target from the RFD4 checkout
python examples/cyclic-peptide-rfo/files/prep_target.py

# once, to cache PD-1's MSA (~34 minutes; every later run reuses it)
python examples/cyclic-peptide-rfo/files/prep_target.py --msa

# smoke test: one replicate, one RFO cycle
python examples/cyclic-peptide-rfo/pipeline.py --test --local --rundir=/abs/path/cyclic-rfo-smoke

# production
python examples/cyclic-peptide-rfo/pipeline.py --local --rundir=/abs/path/cyclic-rfo \
    --replicates 8 --cycles 3 --length 12
```

Drop `--local` to submit to Slurm. `--replicates`, `--cycles` and `--length` are
the knobs worth varying.

## Filters and results

The default gate is `af3.iptm >= 0.5 and af3.plddt >= 60`. That is a ranking
cut, not a success criterion.

Full run — 8 replicates, 3 RFO cycles, PD-1 MSA supplied:

| Stage | Result |
|---|---|
| RFD4 closure | 8/8 closed, 1.22–1.41 Å |
| RFO | 8/8 completed 3 cycles |
| AF3 | iptm 0.32–0.77, pLDDT 86.2–90.0, interface PAE 2.2–7.1 Å |
| filter | **3/8 passed** |

Best design: **iptm 0.770, pLDDT 90.0, interface PAE 2.21 Å**.

Note the sign convention on `AF3_iPTM` in RFO's records: despite the name it holds
**Boltz's** iptm (`boltz_runner.py` reads it from Boltz confidence), not AF3's.
Treat the two as independent opinions, not as one pipeline agreeing with itself.

## The MSA is not optional

The same run without a target MSA:

| | no MSA | with MSA |
|---|---|---|
| iptm | 0.09–0.21 | **0.32–0.77** |
| pLDDT | 37–47 | **86–90** |
| interface PAE | 9.5–14.7 Å | **2.2–7.1 Å** |
| passed | 0/8 | **3/8** |

Every design improved; pLDDT roughly doubled. AF3 in single-sequence mode has no
evolutionary signal for the receptor, so it cannot fold the receptor confidently
regardless of how good the peptide is. **Scores from a no-MSA run say nothing
about design quality** — they measure AF3's ignorance of the target.

The designed peptide correctly stays MSA-free: a novel sequence has no homologs,
so scanning 411 GB for it returns nothing. Only the target needs a search. One
`prep_target.py --msa` run (~30 min) serves every later AF3 call.

## What this example does not establish

An earlier version of this example targeted the CD8α αα dimer (PDB 1AKJ chains
D/E) and scored iptm 0.07–0.12 with PAE 16 Å — but that run also had no MSA, so
the low scores were misread at the time as "a 12-residue macrocycle cannot span
a 2000 Å² interface". That conclusion is unsupported: the confound was never
removed. Whether small rings work against larger, flatter interfaces is still an
open question, and answering it would need the same MSA-controlled comparison
run on CD8α.

The numbers above are computational screening scores. Nothing here is
experimentally validated, and passing the filter means AF3 finds the designed
complex plausible — not that the peptide binds.

## Files

| File | Purpose |
|---|---|
| `pipeline.py` | The four-stage pipeline |
| `files/prep_target.py` | Extract PD-1 (chain B) from RFD4's cyclic-peptide example input |
| `files/prep_target.py --msa` | Run the AF3 genetic search once and cache PD-1's MSA |
| `files/pd1_target.cif` | The target as RFD4 reads it (generated) |
| `files/.cache/pd1_msa.json` | Cached MSA, 2570 rows + 4 templates (generated, ~1.6 MB) |
