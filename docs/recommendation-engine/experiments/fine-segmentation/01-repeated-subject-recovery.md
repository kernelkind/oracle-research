# Experiment 1: repeated fine-subject recovery

Status: **run completed on 2026-09-01; HDBSCAN* recovered five of six cohorts,
while SNN recovered all six**. See the
[controlled-run results](controlled-run-v1-results.md).

## Assumption

> Repeated instances of the same fine subject form recoverable groups.

## Program role

Run this experiment separately for both frozen candidates over the same vector
artifact and input order. For each candidate, a valid, repeatable output that
misses the pass rule is a **recovery failure**. An integrity failure supplies no
recovery verdict for that candidate and exact input. A recovery failure does
not suppress later local runs. An integrity failure blocks only its affected
candidate scope, exact input, and dependent conclusions; it does not block the
other candidate.

The result is not a substitute for a later experiment's exact-fixture baseline.
Every downstream comparison must still meet its own declared local prerequisite.
Changing any candidate-identity field creates a new suite instance with its own
Experiment 1 artifacts and verdict.

Experiment 6 later reuses each candidate's exact default input and output as
that candidate's combined-collection artifact. A combined-collection verdict is
available only when the imported output is valid, repeatable, and passes this
experiment's recovery-and-purity rule. That prerequisite establishes the
imported collection's six-group structure; it does not replace Experiment 6's
two subset baselines or preservation comparisons. The Experiment 6 protocol
and duplicate-ID commitment must therefore be frozen before either candidate's
default output is generated.

## Fixture

The fixture contains 36 vectors: six clearly different fine subjects with six
independently worded instances each. Density is balanced. Each complete note is
also its complete mask, so unmasked context cannot affect this experiment. The
wordings vary without adding a distinct method to only some instances of one
declared atomic subject.

The candidate receives only opaque IDs and vectors. It does not receive the
subject names or expected groups.

### `ORIGAMI`: folding an origami paper crane

| ID | Complete note and exact mask |
|---|---|
| `ORIGAMI-1` | ⟦I folded a paper crane using origami.⟧ |
| `ORIGAMI-2` | ⟦A square sheet of paper became an origami crane through folding.⟧ |
| `ORIGAMI-3` | ⟦I made an origami crane by folding paper.⟧ |
| `ORIGAMI-4` | ⟦I folded paper into the shape of an origami crane.⟧ |
| `ORIGAMI-5` | ⟦I used paper folding to construct an origami crane.⟧ |
| `ORIGAMI-6` | ⟦My origami project was folding a sheet of paper into a crane.⟧ |

### `BIKE-TUBE`: repairing a punctured bicycle inner tube

| ID | Complete note and exact mask |
|---|---|
| `BIKE-TUBE-1` | ⟦I repaired a punctured bicycle inner tube.⟧ |
| `BIKE-TUBE-2` | ⟦I fixed a puncture in my bike's inner tube.⟧ |
| `BIKE-TUBE-3` | ⟦I repaired my bicycle's punctured inner tube.⟧ |
| `BIKE-TUBE-4` | ⟦I mended the puncture in the tube inside my bicycle tire.⟧ |
| `BIKE-TUBE-5` | ⟦I repaired a puncture in the inner tube from my bike.⟧ |
| `BIKE-TUBE-6` | ⟦I fixed a bicycle inner tube that had been punctured.⟧ |

### `ECLIPSE`: observing a lunar eclipse

| ID | Complete note and exact mask |
|---|---|
| `ECLIPSE-1` | ⟦I observed a lunar eclipse.⟧ |
| `ECLIPSE-2` | ⟦I watched Earth's shadow move across the Moon during an eclipse.⟧ |
| `ECLIPSE-3` | ⟦I viewed an eclipse of the Moon.⟧ |
| `ECLIPSE-4` | ⟦I watched the Moon pass through Earth's shadow.⟧ |
| `ECLIPSE-5` | ⟦I observed Earth darken the full Moon by blocking sunlight.⟧ |
| `ECLIPSE-6` | ⟦I watched the Moon become eclipsed by Earth.⟧ |

### `STARTER`: feeding a sourdough starter

| ID | Complete note and exact mask |
|---|---|
| `STARTER-1` | ⟦I fed my sourdough starter with flour and water.⟧ |
| `STARTER-2` | ⟦I refreshed the sourdough culture by mixing in fresh flour and water.⟧ |
| `STARTER-3` | ⟦I added new flour and water to maintain my bread starter.⟧ |
| `STARTER-4` | ⟦My active sourdough culture received its regular flour-and-water feeding.⟧ |
| `STARTER-5` | ⟦I fed the fermented sourdough starter with fresh flour and water.⟧ |
| `STARTER-6` | ⟦I refreshed the wild-yeast sourdough starter with flour and water.⟧ |

### `PIANO`: tuning an acoustic piano

| ID | Complete note and exact mask |
|---|---|
| `PIANO-1` | ⟦I tuned an acoustic piano.⟧ |
| `PIANO-2` | ⟦I corrected the pitch of an acoustic piano.⟧ |
| `PIANO-3` | ⟦I brought an acoustic piano back into tune.⟧ |
| `PIANO-4` | ⟦I tuned an acoustic piano to correct its notes.⟧ |
| `PIANO-5` | ⟦I restored the proper pitch of an acoustic piano.⟧ |
| `PIANO-6` | ⟦I brought an acoustic piano to the correct tuning.⟧ |

### `TOMATO`: transplanting tomato seedlings into garden soil

| ID | Complete note and exact mask |
|---|---|
| `TOMATO-1` | ⟦I transplanted tomato seedlings into a garden bed.⟧ |
| `TOMATO-2` | ⟦I moved young tomato plants into garden soil.⟧ |
| `TOMATO-3` | ⟦I replanted tomato starts in the outdoor vegetable bed.⟧ |
| `TOMATO-4` | ⟦I transferred tomato seedlings into garden soil.⟧ |
| `TOMATO-5` | ⟦I moved young tomato starts into their garden rows.⟧ |
| `TOMATO-6` | ⟦I planted tomato seedlings out in the garden.⟧ |

## Pass rule

Shared execution integrity is a prerequisite. Any integrity failure, including
an execution-profile mismatch, invalid output, or unequal canonical
repetitions, produces no Experiment 1 recovery verdict. There is no semantic
baseline prerequisite.

After both exact-input runs agree and the identities are revealed, the
candidate's predeclared fine-segment output must contain these six exact member
sets:

```text
{ORIGAMI-1 ... ORIGAMI-6}
{BIKE-TUBE-1 ... BIKE-TUBE-6}
{ECLIPSE-1 ... ECLIPSE-6}
{STARTER-1 ... STARTER-6}
{PIANO-1 ... PIANO-6}
{TOMATO-1 ... TOMATO-6}
```

Every returned fine segment containing at least two fixture vectors must be a
subset of one of those six sets. This permits additional overlapping or
partial same-subject segments and singleton segments. It rejects one giant
segment, mixed-subject segments, and an algorithm that emits every possible
subset. Recovering all six exact sets necessarily assigns every fixture vector.
This is an objective set-membership verdict; no post-run semantic review may
reinterpret an alternative grouping as a pass.

## Run

Use `01-repeated-subject-recovery` as the shared blinding namespace. Freeze both
candidate identity tuples before encoding any of the 36 notes or inspecting a
fixture vector or cosine diagnostic. Encode and freeze one shared 36-vector
artifact. This experiment has one exact input shared by both candidates: all 36
opaque ID/vector pairs in the committed HMAC order. Run that exact input twice
from fresh state for each candidate and complete the shared lifecycle in
[README.md](README.md#shared-execution-contract).

The suite-level order-conformance preflight in `README.md` separately reuses
these same 36 opaque ID/vector pairs in its frozen alternate order. Its two
outputs are candidate-specific conformance artifacts, not additional
Experiment 1 semantic inputs. Any shared execution integrity failure in a
conformance input has no conformance or recovery verdict for that candidate. If
both orders are profile-verified, valid, and repeatable but differ, record a
conformance failure and do not apply the recovery pass rule to that candidate's
output.

For each candidate, preserve its two complete default-order outputs, every
returned membership and unassigned ID, and the pass/fail result for each
expected group and for the experiment. Preserve the shared raw-vector cosine
matrix for diagnosis; it does not determine either verdict. For each candidate,
also preserve its two alternate-order outputs and their comparison with that
candidate's default-order canonical output in the suite conformance record.
Preserve each candidate's default pair as the exact candidate-specific artifact
consumed by Experiment 6's combined-collection comparison. The experiment
therefore records four raw outputs per candidate and eight across both
candidates, while encoding the 36 vectors only once.

These results do not select or final-freeze a candidate. They become evidence
for the user's later decision.

## Scope

A pass supports repeated-subject recovery for six balanced and deliberately
separated subjects. Experiment 2 jointly explores nearby subjects and unequal
support; Experiments 3, 4, and 6 separately test lexical traps, unmasked
context, and irrelevant changes.
