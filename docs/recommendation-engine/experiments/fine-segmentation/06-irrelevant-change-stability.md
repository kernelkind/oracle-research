# Experiment 6: stability under irrelevant changes

Status: **draft; notes, masks, subject identities, and expected outputs require
human approval before encoding**.

## Assumption under test

> Results remain stable under irrelevant changes.

This experiment tests four exact changes:

1. permuting input order;
2. appending exact duplicate vectors;
3. appending one unrelated fine subject;
4. combining two semantic areas in one collection.

## Question

After one frozen candidate produces the exact expected fine segments for a
baseline, does each condition preserve that structure? Exact duplicates must
inherit their originals' memberships, and added subjects must not contaminate
the preserved segments.

The experiment tests invariance to each complete change. It does not attempt
to identify the internal mechanism behind a failure. In particular:

- adding duplicates necessarily changes local density;
- adding a subject necessarily changes collection size;
- combining areas necessarily changes both collection size and semantic
  composition.

Those changes are part of the intervention, not separate causal claims.

## Fixture design

The fixture contains two nine-vector baselines:

- baseline `L`: three fine subjects within coffee preparation;
- baseline `R`: three fine subjects within photography work.

Each fine subject has three independently worded instances. The complete note
is also the complete mask, so unmasked carrier text cannot affect this
experiment.

The readable IDs `A1` through `F3` are scoring aliases only. The candidate
never receives them.

## Synthetic notes and masks

The brackets show the exact selected text. The brackets are not sent to SSE.

### Baseline `L`: coffee preparation

#### Subject `A`: roasting coffee beans

**A1**

> ⟦I roasted green coffee beans in a small drum roaster.⟧

**A2**

> ⟦I used a home roaster to turn raw coffee beans brown.⟧

**A3**

> ⟦I applied heat to green coffee beans until they were roasted.⟧

#### Subject `B`: grinding coffee beans

**B1**

> ⟦I ground whole coffee beans with a burr grinder.⟧

**B2**

> ⟦I used a hand mill to turn roasted coffee beans into grounds.⟧

**B3**

> ⟦I crushed whole coffee beans into an even grind before brewing.⟧

#### Subject `C`: brewing pour-over coffee

**C1**

> ⟦I brewed pour-over coffee by slowly pouring hot water over grounds in a
> filter.⟧

**C2**

> ⟦I made coffee with a cone dripper and a controlled hand pour.⟧

**C3**

> ⟦I prepared a pour-over by passing hot water through coffee grounds and a
> paper filter.⟧

### Baseline `R`: photography work

#### Subject `D`: taking portrait photographs

**D1**

> ⟦I took a portrait photograph of my friend using soft window light.⟧

**D2**

> ⟦I made a head-and-shoulders portrait with the person facing the camera.⟧

**D3**

> ⟦I photographed a person's face for a formal portrait.⟧

#### Subject `E`: cropping photographs

**E1**

> ⟦I cropped a photograph to remove empty space around the subject.⟧

**E2**

> ⟦I trimmed the edges of a photo to improve its composition.⟧

**E3**

> ⟦I reframed an image by cutting away unnecessary parts around its subject.⟧

#### Subject `F`: backing up photograph files

**F1**

> ⟦I backed up my photo library to an external drive.⟧

**F2**

> ⟦I copied my photographs to separate storage for safekeeping.⟧

**F3**

> ⟦I made a second copy of my photo files in case the originals were lost.⟧

## Human approval required

Before encoding, human review must confirm:

1. each note communicates only its declared atomic subject;
2. all three instances under one letter have the same fine subject;
3. `A`, `B`, and `C` are distinct fine subjects within coffee preparation;
4. `D`, `E`, and `F` are distinct fine subjects within photography work;
5. the coffee and photography areas are semantically unrelated at the intended
   fine resolution;
6. the exact expected baseline collections below are correct.

These judgments apply only to this fixture. They do not impose a global
partition requirement on the architecture.

## Frozen system boundary

Use the shared 768-dimensional Sentence-T5-base SSE checkpoint identified in:

README.md

Generate each of the eighteen vectors once and preserve its raw bytes. Every
condition reuses those bytes. Duplicate aliases also reuse their original
vector bytes and are never encoded again.

Before the first candidate run, create and freeze a mapping from the readable
scoring aliases to unrelated opaque runtime IDs. The same runtime ID follows
each vector through every condition. Duplicate aliases receive new opaque IDs
that do not reveal which originals they duplicate.

The candidate receives only opaque IDs and vectors. It does not receive notes,
masks, subject names, scoring aliases, expected segment counts, expected
segment sizes, or relationships between duplicate IDs.

Freeze the candidate implementation, preprocessing, configuration, seed,
fine-output rule, and deterministic tie rules before inspecting any result.
Coarser hierarchy output is excluded.

## What counts as one output

A segment is a set of opaque vector IDs. A candidate output is an unordered
collection of those member sets.

- Every segment must be nonempty.
- Every member ID must occur in that run's input.
- A raw segment must not repeat one member ID.
- Segment IDs and output order have no meaning.
- One-member segments remain part of the output.
- Two segments with exactly the same members make the output invalid; the
  scorer must not silently remove one.
- The scorer maps opaque IDs back to readable aliases only after the run.

Validate those rules before projection. An invalid segment cannot disappear
through projection and allow a run to pass.

To canonicalize one valid output for comparison and hashing:

1. map each runtime ID back to its scoring alias;
2. sort the aliases within each segment;
3. sort the complete segments by their sorted alias lists;
4. serialize the resulting nested lists as canonical JSON;
5. compute SHA-256 over those exact JSON bytes.

Although the architecture may allow overlap or unassigned vectors generally,
this purpose-built fixture has exact expected outputs.

Baseline `L` must return exactly:

```text
{A1 A2 A3}
{B1 B2 B3}
{C1 C2 C3}
```

Baseline `R` must return exactly:

```text
{D1 D2 D3}
{E1 E2 E3}
{F1 F2 F3}
```

No additional segment is allowed. A baseline failure ends its dependent
comparisons because there is no correct output to preserve.

## Projection used by addition conditions

Let `U` be all IDs from one baseline. To inspect the baseline portion of an
augmented result:

1. intersect every returned segment with `U`;
2. discard empty intersections;
3. retain every nonempty intersection, including singletons;
4. fail if two projected segments have identical members;
5. compare the unordered projected collection with the exact baseline output.

Projection alone can hide a segment that also contains newly added vectors.
Every addition condition therefore separately rejects a segment containing
vectors from two declared subjects.

## Fresh-run requirement

Run every exact input twice. Each repetition must start a fresh candidate
process with no mutable cache or state from another run. Vector bytes,
configuration, seed, tie rules, and input order remain identical.

Canonical output hashes from the two repetitions must match. If they differ,
record a reproducibility failure and do not attribute any between-condition
difference to the tested intervention.

Two matching repetitions establish only repeatability for those two runs, not
general determinism.

## Protocol

1. Obtain the required human approval.
2. Freeze this document and the complete system boundary.
3. Generate and preserve all eighteen vector bytes once.
4. Generate and freeze the opaque runtime-ID mapping.
5. Run each exact input below twice in fresh processes.
6. Validate both baselines before scoring their dependent conditions.

The sequences below use scoring aliases for readability. Executable inputs use
only their mapped opaque IDs.

## Baselines

### Baseline `L0`

```text
A1 A2 A3 B1 B2 B3 C1 C2 C3
```

It passes only when both fresh runs return the exact expected baseline `L`
collection.

### Baseline `R0`

```text
D1 D2 D3 E1 E2 E3 F1 F2 F3
```

It passes only when both fresh runs return the exact expected baseline `R`
collection.

## Input-order conditions

Only input order changes. IDs, vector bytes, and the complete candidate
boundary remain fixed.

### Permuted `L`

```text
B2 A1 C3 B1 A3 C1 B3 C2 A2
```

Both fresh runs must exactly reproduce baseline `L`.

### Permuted `R`

```text
E2 F1 D3 E1 D1 F3 E3 D2 F2
```

Both fresh runs must exactly reproduce baseline `R`.

## Exact-duplicate condition

Create three aliases with exact vector bytes:

```text
A1' = A1
A2' = A2
A3' = A3
```

Append them without changing the order of the original baseline:

```text
A1 A2 A3 B1 B2 B3 C1 C2 C3 A1' A2' A3'
```

Construct the expected output by adding each alias to every baseline segment
containing its original. The complete expected output is therefore:

```text
{A1 A1' A2 A2' A3 A3'}
{B1 B2 B3}
{C1 C2 C3}
```

Both fresh runs must return exactly that collection. Do not collapse aliases
before scoring.

This condition tests one subject whose three instances are each duplicated
once. It does not establish invariance to every possible duplicate pattern.

## Unrelated-subject addition

Append subject `D` without changing baseline `L0`'s order:

```text
A1 A2 A3 B1 B2 B3 C1 C2 C3 D1 D2 D3
```

The condition passes only when:

1. projection onto `A1` through `C3` exactly reproduces baseline `L`;
2. no segment contains both an `A`–`C` vector and a `D` vector.

Subject to the general output contract, pure `D`-only output is recorded but
does not affect this verdict. Subject `D` is not required to reproduce its
behavior from baseline `R`, because its surrounding collection is different
here.

## Combined-area condition

Append baseline `R0` after the complete unchanged baseline `L0`:

```text
A1 A2 A3 B1 B2 B3 C1 C2 C3 D1 D2 D3 E1 E2 E3 F1 F2 F3
```

The condition passes only when:

1. projection onto `A1` through `C3` exactly reproduces baseline `L`;
2. projection onto `D1` through `F3` exactly reproduces baseline `R`;
3. no segment contains vectors from more than one declared subject.

Concatenation preserves each baseline's original internal order. An
interleaved combined run would test an order-by-combination interaction and is
not part of this experiment.

## Overall pass rule

The experiment passes only if:

1. both baselines produce their exact expected collections;
2. every repeated exact input is reproducible;
3. both order conditions pass;
4. the exact-duplicate condition passes;
5. the unrelated-subject addition passes;
6. the combined-area condition passes.

Do not average verdicts.

Classify a non-pass before interpreting it:

- **output-contract failure:** any raw output contains an empty segment, an
  unknown ID, a repeated member, or a duplicate member set;
- **reproducibility failure:** two valid fresh-process outputs for one exact
  input have different canonical hashes;
- **prerequisite failure:** both valid baseline repetitions agree but do not
  return the exact expected baseline collection;
- **stability failure:** both baselines are valid, exact, and reproducible, but
  a reproducible intervention output violates its frozen expectation.

An output-contract, reproducibility, or prerequisite failure does not support
a conclusion about stability. Record all applicable failures, but do not
reinterpret one as another.

## Required record

Preserve:

- every note, mask, declared subject, and human approval;
- raw SSE bytes, artifact hashes, and the cosine matrix;
- the private scoring-alias-to-runtime-ID mapping;
- candidate implementation and configuration identities;
- every exact ordered input;
- both raw outputs, canonical JSON, and SHA-256 hashes for every condition;
- every projected collection;
- every added, removed, split, merged, duplicated, or cross-subject segment;
- every prerequisite, reproducibility, and condition verdict.

## What a result means

A pass supports exact output stability for these frozen subjects and exact
perturbations. It does not establish production-scale stability, arbitrary
duplicate patterns, all permutations, streaming updates, natural
near-duplicates, changes to configuration or seed, automatic mask quality, or
hierarchy quality.

A baseline failure does not disprove stability. It means the candidate failed
the semantic prerequisite, so the dependent stability conditions cannot be
interpreted.

A condition failure proves that its complete frozen intervention changed the
output. An input-order failure isolates order and therefore establishes order
sensitivity. Duplicate, addition, and combined-area failures do not identify
which bundled mechanism—such as density, collection size, or semantic
composition—caused the change.
