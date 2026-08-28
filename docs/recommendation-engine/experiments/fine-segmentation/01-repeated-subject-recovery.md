# Experiment 1: repeated fine-subject recovery

Status: **draft; every subject identity and mask requires human approval before
encoding**.

## Assumption

> Repeated instances of the same fine subject form recoverable groups.

## Fixture

The fixture contains 36 vectors: six clearly different fine subjects with six
independently worded instances each. Density is balanced. Each complete note is
also its complete mask, so unmasked context cannot affect this experiment.

The candidate receives only opaque IDs and vectors. It does not receive the
subject names or expected groups.

### `ORIGAMI`: folding an origami paper crane

| ID | Complete note and exact mask |
|---|---|
| `ORIGAMI-1` | ⟦I folded a paper crane using origami.⟧ |
| `ORIGAMI-2` | ⟦A square sheet of paper became an origami crane through folding.⟧ |
| `ORIGAMI-3` | ⟦I made the traditional origami crane from one piece of paper.⟧ |
| `ORIGAMI-4` | ⟦Careful creases turned my paper square into an origami crane.⟧ |
| `ORIGAMI-5` | ⟦I constructed an origami crane with a sequence of paper folds.⟧ |
| `ORIGAMI-6` | ⟦My origami project was folding a sheet of paper into a crane.⟧ |

### `BIKE-TUBE`: repairing a punctured bicycle inner tube

| ID | Complete note and exact mask |
|---|---|
| `BIKE-TUBE-1` | ⟦I patched a punctured bicycle inner tube.⟧ |
| `BIKE-TUBE-2` | ⟦I sealed a hole in my bike's inner tube with a repair patch.⟧ |
| `BIKE-TUBE-3` | ⟦I fixed a flat bicycle tube by applying a vulcanizing patch.⟧ |
| `BIKE-TUBE-4` | ⟦I mended the puncture in the tube inside my bicycle tire.⟧ |
| `BIKE-TUBE-5` | ⟦I repaired a puncture in the inner tube from my bike.⟧ |
| `BIKE-TUBE-6` | ⟦A patch closed the leak caused by a puncture in my bicycle tube.⟧ |

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
| `PIANO-2` | ⟦I adjusted an acoustic piano's string tension to correct its pitch.⟧ |
| `PIANO-3` | ⟦I brought the strings of the piano back into tune.⟧ |
| `PIANO-4` | ⟦I corrected the piano's notes by tuning its strings.⟧ |
| `PIANO-5` | ⟦I set each string in the acoustic piano to the proper pitch.⟧ |
| `PIANO-6` | ⟦I used the tuning pins to bring every piano note to pitch.⟧ |

### `TOMATO`: transplanting tomato seedlings into garden soil

| ID | Complete note and exact mask |
|---|---|
| `TOMATO-1` | ⟦I transplanted tomato seedlings into a garden bed.⟧ |
| `TOMATO-2` | ⟦I moved young tomato plants from seed trays into garden soil.⟧ |
| `TOMATO-3` | ⟦I replanted tomato starts in the outdoor vegetable bed.⟧ |
| `TOMATO-4` | ⟦I transferred tomato seedlings from nursery cells into prepared ground.⟧ |
| `TOMATO-5` | ⟦I moved young tomato starts from pots into their final garden rows.⟧ |
| `TOMATO-6` | ⟦I planted nursery-grown tomato seedlings out in the garden.⟧ |

## Pass rule

The candidate's predeclared fine-segment output must contain these six exact
member sets:

```text
{ORIGAMI-1 ... ORIGAMI-6}
{BIKE-TUBE-1 ... BIKE-TUBE-6}
{ECLIPSE-1 ... ECLIPSE-6}
{STARTER-1 ... STARTER-6}
{PIANO-1 ... PIANO-6}
{TOMATO-1 ... TOMATO-6}
```

Every returned fine segment containing at least two fixture vectors must be a
subset of one of those six sets. This still permits additional overlapping or
partial same-subject segments and singleton segments. It rejects one giant
segment, mixed-subject segments, and an algorithm that emits every possible
subset. Recovering all six exact sets necessarily assigns every fixture vector.

## Run

1. Approve and freeze every note, mask, and expected group.
2. Encode all 36 inputs once under the shared contract in README.md.
3. Freeze the candidate, configuration, seed, fine-output selector, and one
   shuffled opaque-ID order.
4. Run the candidate and preserve its complete output before restoring the
   fixture identities.
5. Apply the pass rule.

Record the frozen inputs and hashes, raw vectors, input order, candidate
configuration, complete returned memberships, unassigned IDs, and the verdict
for each expected group. Preserve the raw-vector cosine matrix for diagnosis;
it does not determine the verdict.

## Scope

A pass supports repeated-subject recovery for six balanced and deliberately
separated subjects. Experiments 2–6 separately test nearby subjects, lexical
traps, unmasked context, unequal density, and irrelevant changes.
