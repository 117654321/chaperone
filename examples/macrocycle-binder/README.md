# Large macrocycle binder design

Design a 40-residue head-to-tail macrocycle against PD-1, then let
RFOptimization re-design its sequence against a Boltz-2 refold before AF3 refolds
and scores the interface.

This is the third of three ring/protein examples against the same target, and it
exists to answer a question the other two cannot: **does a longer ring buy enough
interface to be worth the added conformational cost?**

| Example | Designed chain | iptm | Passed |
|---|---|---|---|
| `cyclic-peptide-rfo` | 12-residue ring | 0.34–0.56 | 1/4 |
| **`macrocycle-binder`** | **40-residue ring** | **0.38–0.83** | **1/4** |
| `miniprotein-binder` | 69–111 linear | 0.82–0.90 | 4/4 |

## Pipeline

```text
rfd4(cyclic=True) → rfoptimization(cyclic=True) → af3 → filter
```

Same stages, same target, same chemistry and hotspots as
`cyclic-peptide-rfo`. Only `peptide_length` changes.

## Does RFD4 close a 40-residue ring?

Yes, and reliably. Upstream documents closure over ring lengths **6–20**
(360/360 for head-to-tail), which reads as an upper bound but was only ever a
tested range. On this target, 40 residues closed **4/4** at 1.34–1.39 Å, and RFO
held the ring at 1.33 Å after three redesign cycles.

The mechanism is unchanged: the ring is a `_struct_conn` `covale` record in the
conditioned input, and the peptide is a run of placeholder residues whose
sequence and coordinates are both designed. `cyclic=True` writes that input for
you:

```python
RFD4(
    inputs="pd1_target.cif",
    cyclic=True,
    peptide_length=40,
    peptide_chain="A",
    target_chains=["B"],
    hotspots={"B33": "CG1,CG2", ...},
    cyclic_chemistry="head_tail",
)
```

Three settings are not cosmetic:

| Setting | Why |
|---|---|
| `peptide_chain="A"` | RFOptimization raises unless the designed chain is literally named `A`. The block defaults to this. |
| `backprop_fraction=0.0` | RFO's `cyclic` flag only reaches the Boltz branch. Any RF3 fraction leaves the ring unconstrained and it drifts open. |
| `cyclic_chemistry="head_tail"` | The only chemistry upstream measures at 100%; disulfide manages 12/16 and isopeptide 1/16 when the ring has no input coordinates. |

## Hotspots are atom-level

`C_HOT` is an atom-level condition. Naming only a residue number lets the model
pick any atom of it. The four entries are the exact atoms upstream marks on PD-1:

```python
HOTSPOTS = {
    "B33": "CG1,CG2",              # Ile
    "B95": "CB,CG2",               # Thr
    "B97": "CB,CD1,CD2,CG",        # Leu
    "B102": "CD,CG,NE2,OE1",       # Gln
}
```

## Measuring closure

Closure is `|d − ideal| ≤ 0.3 Å` against the 1.33 Å head-to-tail amide, and the
test is two-sided on purpose. A one-sided "closed if under 2.3 Å" cut scores an
impossible overshoot — atoms inside each other — as a success.

`pipeline.py` prints the measured distance for every design before spending GPU
time on RFO, so a broken ring is visible immediately.

## Run

```bash
# once, to stage PD-1 from the RFD4 checkout
python examples/macrocycle-binder/files/prep_target.py

# once, to cache PD-1's MSA (~30 min; every later run reuses it)
python examples/macrocycle-binder/files/prep_target.py --msa

# smoke test: one macrocycle, one RFO cycle
python examples/macrocycle-binder/pipeline.py --test --local --rundir=/abs/path/macrocycle-smoke

# production
python examples/macrocycle-binder/pipeline.py --local --rundir=/abs/path/macrocycle \
    --replicates 4 --cycles 3 --length 40
```

`--length` is the knob this example exists to vary. Drop `--local` to submit to
Slurm.

## Results

Full run — 4 replicates, 3 RFO cycles, ring length 40, PD-1 MSA supplied:

| Design | iptm | ptm | pLDDT | interface PAE | Passed |
|---|---|---|---|---|---|
| rep3 | **0.830** | 0.850 | 89.3 | **1.24 Å** | ✅ |
| rep2 | 0.480 | 0.760 | 83.0 | 4.50 Å | |
| rep1 | 0.380 | 0.720 | 79.3 | 6.38 Å | |
| rep0 | 0.380 | 0.700 | 78.3 | 4.49 Å | |

**RFD4 closed 4/4 at 1.34–1.39 Å; 1/4 passed the `iptm >= 0.5 and plddt >= 60`
gate.**

## What the longer ring actually does

Comparing the two ring examples at n=4 each:

| | 12 residues | 40 residues |
|---|---|---|
| iptm range | 0.34–0.56 | **0.38–0.83** |
| iptm median | ~0.45 | ~0.43 |
| pLDDT range | 86.1–87.7 | 78.3–89.3 |
| passed | 1/4 | 1/4 |

The **ceiling** rises (0.56 → 0.83) while the **median does not** (~0.45 → ~0.43),
and the spread widens on both iptm and pLDDT. That is the shape you would expect
if a longer ring can reach more interface but only sometimes finds a good pose:
more upside, more variance, no shift in the typical outcome. At n=4 this is a
hypothesis, not a measurement — ranking the two would need 20+ designs each.

Against the linear miniprotein example (0.82–0.90, 4/4), both rings trail
clearly. Cyclization costs affinity here; the question is whether the rigidity
buys something the scores do not capture, which these numbers cannot answer.

## The MSA is not optional

Measured on the 12-residue example with the same pipeline: eight designs scored
iptm 0.09–0.21 / pLDDT 37–47 without a target MSA, and iptm 0.32–0.77 /
pLDDT 86–90 with one. Nothing about the designs changed between those runs.

AF3 in single-sequence mode has no evolutionary signal for the receptor, so it
cannot fold it confidently regardless of peptide quality. The designed ring
correctly stays MSA-free — a novel sequence has no homologs to find — so only the
target needs a search.

## Files

| File | Purpose |
|---|---|
| `pipeline.py` | The four-stage pipeline, `--length` configurable |
| `files/prep_target.py` | Extract PD-1 (chain B) and optionally cache its MSA |
| `files/pd1_target.cif` | The target as RFD4 reads it (generated) |
| `files/.cache/pd1_msa.json` | Cached MSA (generated, ~30 min) |
