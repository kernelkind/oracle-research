# Experiment 6: stability under irrelevant changes

Status: **draft; notes, masks, and expected relationships require human
approval before encoding**.

## Assumption under test

> Results remain stable under irrelevant changes.

The canonical changes are input order, exact duplicates, unrelated added
subjects, and mixing semantic areas into one collection.

## Question

After one frozen candidate correctly segments a collection, do those changes
alter the fine segments formed by the original vectors?

## Why this fixture exists

Stability requires a correct result to preserve. This fixture defines two
disjoint nine-vector baselines. Each contains three clearly different
subjects with three paraphrases each. Later runs reorder them, duplicate one
subject, add an unrelated subject, or combine both baselines.

All eighteen notes are purpose-built for this experiment. No existing vector
artifact is reused.

## Synthetic notes and masks

### Subject `A`: folding origami cranes

**A1**

> The workshop introduces ⟦folding origami paper cranes⟧.

**A2**

> I am learning about ⟦folding square paper into an origami crane⟧.

**A3**

> This guide explains ⟦making an origami crane from a sheet of paper⟧.

### Subject `B`: leveling a 3D-printer bed

**B1**

> The workshop introduces ⟦leveling a 3D printer's build plate⟧.

**B2**

> I am learning about ⟦calibrating a 3D-printer bed so the nozzle gap is even⟧.

**B3**

> This guide explains ⟦adjusting a 3D-printer bed until its nozzle gap is
> uniform⟧.

### Subject `C`: pruning apple trees

**C1**

> The workshop introduces ⟦pruning branches on an apple tree⟧.

**C2**

> I am learning about ⟦cutting back an apple tree's limbs⟧.

**C3**

> This guide explains ⟦trimming an apple tree to remove excess growth⟧.

### Subject `D`: interpreting medieval manuscripts

**D1**

> The workshop introduces ⟦interpreting the meaning of a medieval manuscript⟧.

**D2**

> I am learning about ⟦explaining the meaning of text in a medieval
> manuscript⟧.

**D3**

> This guide explains ⟦analyzing what a medieval manuscript's text means⟧.

### Subject `E`: practicing the butterfly swimming stroke

**E1**

> The workshop introduces ⟦practicing complete butterfly-stroke technique⟧.

**E2**

> I am learning about ⟦training the arm, kick, and breathing timing for the
> butterfly stroke⟧.

**E3**

> This guide explains ⟦improving complete butterfly swimming technique⟧.

### Subject `F`: composing ambient music

**F1**

> The workshop introduces ⟦composing ambient music⟧.

**F2**

> I am learning about ⟦composing an atmospheric ambient-music track⟧.

**F3**

> This guide explains ⟦creating an ambient musical soundscape⟧.

The six subject identities are scoring data. The candidate does not receive
them.

Human approval must explicitly confirm that all six are different subjects at
the intended fine resolution. The cross-subject checks below encode only those
fixture-specific judgments; they do not impose a global partition requirement.

## Frozen hypothesis

Holding vector bytes and the complete candidate configuration fixed:

1. changing input order will not change the returned fine segments;
2. unevenly adding exact duplicates will not change the segments of the
   original vectors;
3. each duplicate will receive the same memberships as its original;
4. adding one unrelated subject will not change existing segments;
5. combining both heterogeneous baselines will preserve each baseline's
   segments;
6. no augmented run will create a segment spanning declared subjects.

One subject is **cleanly recovered** when one segment contains all three of its
vectors and no vector from another declared subject.

## Frozen system boundary

Use the shared 768-dimensional Sentence-T5-base SSE checkpoint identified in
the [suite index](README.md). Preserve its raw outputs exactly. Any
normalization, distance, or other preprocessing belongs to the candidate's
frozen configuration.

The candidate receives only opaque IDs and vectors. It may return overlapping
fine segments and leave vectors unassigned. Scoring consumes only its
predeclared fine-segment collection; coarser parents are excluded.

This is a visible development fixture, not held-out confirmation.

## Comparing outputs

Segment IDs and output order have no meaning. Let `U` be the original vector
IDs from the baseline being compared.

To project an augmented result onto `U`:

1. replace every duplicate alias with its original ID;
2. intersect every returned segment with `U`;
3. discard empty intersections;
4. retain one-member intersections;
5. remove duplicate member sets;
6. compare the resulting collection of member sets without using segment IDs
   or output order.

Two results are stable only when those projected collections are exactly equal.
An additional cross-subject rule is required because projection would hide an
added vector contaminating an otherwise unchanged original segment.

Exact collection equality is intentional. Fine segments are the direct input
to later hierarchy construction, so adding or removing even a redundant pure
subset changes that downstream input. A weaker pairwise-only comparison would
not test stability of the returned result itself.

## Protocol

1. Obtain human approval of all eighteen notes, masks, subject identities, and
   expected boundaries.
2. Freeze this document and the candidate's implementation, preprocessing,
   configuration, fine-output rule, and seed.
3. Generate all eighteen SSE vectors once and preserve their exact bytes.
4. Run and validate both semantic baselines.
5. If a baseline is not correctly segmented, record that prerequisite failure;
   there is no correct result for the associated stability variants to
   preserve.
6. Run every applicable variant below without retuning or re-encoding.
7. Exact duplicates reuse vector bytes under alias IDs. They are never encoded
   again.

## Baseline `L`

Input:

```text
A1 A2 A3 B1 B2 B3 C1 C2 C3
```

Baseline `L` is valid only when each of `A`, `B`, and `C` is cleanly recovered
and no segment crosses those subject boundaries.

## Baseline `R`

Input:

```text
D1 D2 D3 E1 E2 E3 F1 F2 F3
```

Baseline `R` is valid only when each of `D`, `E`, and `F` is cleanly recovered
and no segment crosses those subject boundaries.

## Order variants

### Baseline `L`

Reverse order:

```text
C3 C2 C1 B3 B2 B1 A3 A2 A1
```

Interleaved order:

```text
A1 B1 C1 A2 B2 C2 A3 B3 C3
```

Each passes only when its projected segment collection exactly equals baseline
`L`.

### Baseline `R`

Reverse order:

```text
F3 F2 F1 E3 E2 E1 D3 D2 D1
```

It passes only when its projected segment collection exactly equals baseline
`R`.

## Uneven duplicate variant

Create aliases using exact vector bytes:

```text
A1' = A1
A2' = A2
A3' = A3
```

Input:

```text
A1 A1' B1 C1 A2 A2' B2 C2 A3 A3' B3 C3
```

This duplicates only subject `A`, deliberately changing local density.
Therefore a failure establishes sensitivity to the exact-duplicate
intervention as a whole; this experiment does not separate duplicate identity
from the density change that duplication causes.

The variant passes only when:

1. collapsing the aliases and projecting onto `A1–C3` exactly reproduces
   baseline `L`;
2. each alias has the same complete incident-segment structure as its original;
3. no segment crosses a declared subject boundary.

For alias `A1'`, compare every segment containing `A1` with every segment
containing `A1'` after removing both `A1` and `A1'` from those segments. The two
collections of remaining member sets must be identical. Apply the same rule to
`A2/A2'` and `A3/A3'`. This compares full overlapping membership rather than
only pairwise neighbors; a segment containing an original and its alias can
satisfy both sides of the comparison.

## Unrelated-addition variant

Input:

```text
A1 B1 C1 D1 A2 B2 C2 D2 A3 B3 C3 D3
```

It passes only when:

1. projection onto `A1–C3` exactly reproduces baseline `L`;
2. projection onto `D1–D3` exactly reproduces baseline `R` projected onto
   `D1–D3`;
3. no segment crosses a subject boundary.

## Mixed-area variant

Input:

```text
A1 B1 C1 D1 E1 F1 A2 B2 C2 D2 E2 F2 A3 B3 C3 D3 E3 F3
```

It passes only when:

1. projection onto `A1–C3` exactly reproduces baseline `L`;
2. projection onto `D1–F3` exactly reproduces baseline `R`;
3. no segment crosses any of the six subject boundaries.

## Overall pass rule

The experiment passes only if both baselines and every variant pass. Do not
average the verdicts.

## Required record

Preserve:

- both baseline segment collections;
- every projected variant collection;
- segments added, removed, split, merged, or contaminated;
- duplicate aliases whose memberships differ from their originals;
- every cross-subject membership;
- the cosine matrix computed from the immutable raw SSE outputs;
- the raw SSE artifact and hashes;
- the candidate configuration and seed;
- a repeat of any exact run that behaves nondeterministically.

## What a result means

A pass supports exact output stability for these frozen perturbations and
subjects. It does not establish production-scale stability, streaming updates,
natural near-duplicates, changes to candidate configuration or seed, automatic
mask quality, or hierarchy quality.

A baseline failure does not disprove stability; it means the candidate failed
the prerequisite semantic recovery. A variant failure after a valid baseline
is direct evidence that the tested irrelevant change altered the result.
