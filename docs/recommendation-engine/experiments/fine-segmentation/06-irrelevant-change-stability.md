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

The shared contract already requires a candidate whose construction is
permutation-invariant. The two order conditions here are concrete
implementation checks for two frozen permutations; they are not evidence that
arbitrary order-sensitive candidates may enter the other experiments.

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

> ⟦I roasted green coffee beans.⟧

**A2**

> ⟦I turned raw coffee beans into roasted beans.⟧

**A3**

> ⟦I applied heat to green coffee beans until they were roasted.⟧

#### Subject `B`: grinding coffee beans

**B1**

> ⟦I ground whole coffee beans.⟧

**B2**

> ⟦I turned roasted coffee beans into grounds.⟧

**B3**

> ⟦I crushed roasted coffee beans into an even grind.⟧

#### Subject `C`: brewing pour-over coffee

**C1**

> ⟦I brewed pour-over coffee.⟧

**C2**

> ⟦I made coffee using the pour-over method.⟧

**C3**

> ⟦I prepared coffee by pouring hot water through grounds in a filter.⟧

### Baseline `R`: photography work

#### Subject `D`: taking portrait photographs

**D1**

> ⟦I took a portrait photograph.⟧

**D2**

> ⟦I photographed a person for a portrait.⟧

**D3**

> ⟦I made a photographic portrait of a person.⟧

#### Subject `E`: cropping photographs

**E1**

> ⟦I cropped a photograph.⟧

**E2**

> ⟦I trimmed the edges of a photo.⟧

**E3**

> ⟦I reframed an image by cutting away its outer parts.⟧

#### Subject `F`: backing up photograph files

**F1**

> ⟦I backed up my photograph files.⟧

**F2**

> ⟦I copied my photographs to separate storage.⟧

**F3**

> ⟦I made backup copies of my photo files.⟧

## Human approval required

Before encoding, human review must confirm:

1. each note communicates only its declared atomic subject;
2. all three instances under one letter have the same fine subject;
3. `A`, `B`, and `C` are distinct fine subjects within coffee preparation;
4. `D`, `E`, and `F` are distinct fine subjects within photography work;
5. the coffee and photography areas are semantically unrelated at the intended
   fine resolution;
6. the exact expected baseline collections below are correct;
7. permuting a baseline must preserve every membership;
8. each exact duplicate must inherit every membership of its original;
9. adding subject `D` to baseline `L` must preserve `L` without placing a `D`
   vector in an `A`–`C` segment;
10. combining `L` and `R` must preserve both baselines without creating a
    cross-subject segment.

These judgments apply only to this fixture. They do not impose a global
partition requirement on the architecture.

## Frozen system boundary

Use the shared 768-dimensional Sentence-T5-base SSE checkpoint identified in
[README.md](README.md).

Follow the lifecycle, candidate-identity, blinding, output-validation, and
canonicalization contract in `README.md`.

Generate each of the eighteen vectors once and preserve its raw bytes. Every
condition reuses those bytes. Duplicate aliases also reuse their original
vector bytes and are never encoded again.

Before encoding, create and commit to the mapping from readable scoring aliases
to unrelated opaque runtime IDs. The same runtime ID follows each vector
through every condition. Duplicate aliases receive new opaque IDs that do not
reveal which originals they duplicate. Do not reveal the mapping until all raw
candidate outputs are immutable.

The candidate receives only opaque IDs and vectors. It does not receive notes,
masks, subject names, scoring aliases, expected segment counts, expected
segment sizes, or relationships between duplicate IDs.

Freeze the candidate identity defined by `README.md` before encoding. Coarser
hierarchy output is excluded.

## What counts as one output

Validate and canonicalize the opaque-ID output exactly as specified in
`README.md`, before projection or semantic scoring. An invalid segment cannot
disappear through projection and allow a run to pass. Reveal the alias mapping
only after both raw outputs for every exact input are immutable and their
opaque canonical bytes and hashes have been recorded.

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

No additional segment is allowed. A baseline failure withholds verdicts for
its dependent comparisons because there is no correct output to preserve. It
does not suppress an independent baseline or its conditions, and it does not
cancel already frozen runs.

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

Apply the shared two-invocation fresh-process requirement to every exact input.
Repeatability gates only that input and comparisons that depend on it. Two
matching invocations establish repeatability only for those exact runs, not
general determinism.

## Protocol

1. Obtain the required human approval.
2. Freeze this document and the complete candidate identity.
3. Generate the opaque runtime-ID mapping and record its commitment. Freeze
   every explicit order listed below as an Experiment 6 order intervention.
4. Freeze the SSE boundary and exact input bytes.
5. Generate and preserve all eighteen vector bytes once, then record their
   dimensions and hashes.
6. Run every exact input below twice in fresh processes, even if one baseline
   later fails.
7. Validate and canonicalize every opaque output before revealing the mapping.
8. Score each condition using the dependency graph below.

## Verdict dependency graph

- Baseline `L0` gates permuted `L`, the duplicate condition, and the unrelated
  addition condition.
- Baseline `R0` gates permuted `R`.
- Both baselines gate the combined-area condition.
- A validity or repeatability failure for one exact input gates that input and
  comparisons depending on it, but not independent branches.

Always record every raw run. A gated condition is reported as **no verdict**,
not as a stability pass or failure.

The sequences below use scoring aliases for readability. They override the
shared default HMAC order for this experiment only. An executable input replaces
each alias with its mapped opaque ID while preserving the listed sequence; the
candidate never receives an alias.

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
2. every repeated exact input is repeatable;
3. both order conditions pass;
4. the exact-duplicate condition passes;
5. the unrelated-subject addition passes;
6. the combined-area condition passes.

Do not average verdicts.

Classify a non-pass before interpreting it:

- **output-contract failure:** any raw output contains an empty segment, an
  unknown ID, a repeated member, or a duplicate member set;
- **repeatability failure:** two valid fresh-process outputs for one exact
  input have different canonical bytes;
- **prerequisite failure:** both valid baseline repetitions agree but do not
  return the exact expected baseline collection;
- **permutation-invariance contract failure:** a valid, repeatable permuted
  input differs from its valid, repeatable baseline; this invalidates the
  candidate's construction-level eligibility rather than supplying a semantic
  stability verdict;
- **stability failure:** every prerequisite for that condition is valid,
  exact, and repeatable, but the repeatable intervention output violates
  its frozen expectation. This class applies to the duplicate, unrelated-addition,
  and combined-area conditions, not the two order checks.

An output-contract, repeatability, or prerequisite failure does not support
a stability conclusion for the affected branch. Record all applicable
failures and every independent branch verdict, but do not reinterpret one as
another. A permutation-invariance contract failure invalidates the candidate
for this entire suite, even when other recorded branches happen to match their
expectations.

## Required record

Preserve:

- every note, mask, declared subject, and human approval;
- raw SSE bytes, artifact hashes, and the cosine matrix;
- the private scoring-alias-to-runtime-ID mapping and its pre-run commitment;
- candidate implementation and configuration identities;
- every exact ordered input;
- both raw outputs, canonical JSON, and SHA-256 hashes for every condition;
- every projected collection;
- every added, removed, split, merged, duplicated, or cross-subject segment;
- every prerequisite, repeatability, and condition verdict.

## What a result means

A pass supports exact output stability for these frozen subjects and exact
perturbations. It does not establish production-scale stability, arbitrary
duplicate patterns, all permutations, streaming updates, natural
near-duplicates, changes to configuration or seed, automatic mask quality, or
hierarchy quality.

A baseline failure does not disprove stability. It means the candidate failed
that branch's semantic prerequisite, so only its dependent stability
conditions cannot be interpreted.

A condition failure proves that its complete frozen intervention changed the
output. An input-order difference demonstrates that the implementation violates
the suite's required construction-level permutation invariance, so the
candidate is ineligible and the experiment has no semantic stability verdict.
Duplicate, addition, and combined-area failures do not identify which bundled
mechanism—such as density, collection size, or semantic composition—caused the
change.
