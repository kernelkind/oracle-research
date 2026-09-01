# Experiment 6: stability under irrelevant changes

Status: **reused fixture semantics, baseline qualification, intervention
rules, and scoring approved on 2026-08-31; technical freeze incomplete; do not
encode or run yet**.

## Assumption under test

> Results remain stable under irrelevant changes.

This experiment owns the suite's stability qualification for three exact
changes:

1. adding exact duplicate vectors;
2. adding one unrelated fine subject;
3. combining two independently recovered collections that together span six
   deliberately separated semantic areas.

## Question

For each frozen candidate, after it recovers the required subjects in a clean,
repeatable baseline, does each condition preserve that candidate's complete
observed structure? Exact duplicates must inherit their originals' memberships,
and added subjects must not contaminate the preserved segments.

The experiment tests invariance to each complete change. It does not attempt
to identify the internal mechanism behind a failure. In particular:

- without the shared alias adapter, adding duplicates would change local
  density; this condition verifies that the complete candidate boundary
  prevents that change and restores every alias afterward;
- adding a subject necessarily changes collection size;
- combining collections necessarily changes both collection size and semantic
  composition.

Those changes are part of the intervention, not separate causal claims.
Input-order conformance belongs to the suite eligibility contract in
[README.md](README.md); it is not an empirical arm of this experiment.

## Reused fixture and aliases

This experiment introduces no new base note, mask, or SSE encoding. Its 36
base vectors are the exact approved fixture from
[`01-repeated-subject-recovery.md`](01-repeated-subject-recovery.md), with the same frozen bytes,
opaque runtime IDs, and default input order.

The readable labels below are scorer-only aliases:

| Experiment 6 aliases | Experiment 1 fixture IDs | Atomic subject |
|---|---|---|
| `A1 ... A6` | `ORIGAMI-1 ... ORIGAMI-6` | folding an origami paper crane |
| `B1 ... B6` | `BIKE-TUBE-1 ... BIKE-TUBE-6` | repairing a punctured bicycle inner tube |
| `C1 ... C6` | `ECLIPSE-1 ... ECLIPSE-6` | observing a lunar eclipse |
| `D1 ... D6` | `STARTER-1 ... STARTER-6` | feeding a sourdough starter |
| `E1 ... E6` | `PIANO-1 ... PIANO-6` | tuning an acoustic piano |
| `F1 ... F6` | `TOMATO-1 ... TOMATO-6` | transplanting tomato seedlings into garden soil |

For example, `A1` refers to the immutable vector and opaque runtime ID already
assigned to `ORIGAMI-1`; it is not a second copy or a new candidate feature.
The candidate never receives the aliases.

Each atomic subject represents a deliberately separated semantic area for this
controlled fixture. Baseline `L` is `A` through `C`. Baseline `R` is `D`
through `F`.
The full `L + R` input is therefore literally Experiment 1's default
36-vector input, not a semantically equivalent rerun under different IDs.
Only the six duplicate aliases introduced by the duplicate condition need new
opaque runtime IDs; they reuse their originals' vector bytes and require no SSE
encoding.

## Approved semantic decisions

The 2026-08-31 human approval confirms:

1. the six subjects are separated enough to represent six distinct semantic
   areas for this controlled stability test;
2. `A` through `C` form baseline `L`, and `D` through `F` form baseline `R`;
3. the baseline qualification rules below are correct;
4. each exact duplicate must inherit every membership of its original;
5. adding subject `D` to baseline `L` must preserve `L` without placing a `D`
   vector in an `A`–`C` segment; and
6. the imported full collection receives a combined-condition verdict only
   after that candidate's Experiment 1 artifact passes the recovery-and-purity
   rule.

These judgments apply only to this fixture. They do not impose a global
partition requirement on the architecture.

Before execution, separately verify two technical facts: the approved
Experiment 1 fixture and its frozen hashes are the sole source of the 36 base
notes, masks, subjects, and vectors, and the `A1 ... F6` alias table maps
exactly onto that fixture. These are provenance checks, not additional semantic
judgments.

## Frozen system boundary

Use the shared 768-dimensional Sentence-T5-base SSE checkpoint identified in
[README.md](README.md).

Follow the lifecycle, candidate-identity, blinding, output-validation, and
canonicalization contract in `README.md`.

Reuse the 36 immutable raw SSE vectors, opaque IDs, and global order already
frozen for Experiment 1, and verify their hashes against that artifact. Every
condition reuses those bytes and IDs. Duplicate aliases receive new opaque IDs
under the Experiment 6 blinding namespace; they reuse their originals' vector
bytes and are never encoded again. Freeze and commit those new IDs and their
order keys before Experiment 1's default output is generated. The duplicate
input sorts the union of Experiment 1's base order keys and Experiment 6's six
new order keys under the shared ordering rule.

The candidate receives only opaque IDs and vectors. It does not receive notes,
masks, subject names, scoring aliases, expected segment counts, expected
segment sizes, or relationships between duplicate IDs.

The shared `opaque-id-order-bitwise-vector-alias-v1` adapter may infer only
what the supplied opaque IDs and vector coordinates reveal directly. In the
duplicate condition it detects each byte-identical vector group, passes one
representative to the frozen SNN or HDBSCAN* core, and expands that
representative's selected memberships or unassigned state to every alias after
the core returns. The core never receives the duplicate relationship or an
extra geometric point.

For each candidate, its identity and verified execution-profile hash must equal
that candidate's Experiment 1 values. A change creates a new suite instance and
invalidates that candidate's artifact reuse. Coarser hierarchy output is
excluded.

## What counts as one output

Validate and canonicalize the opaque-ID output exactly as specified in
`README.md`, before projection or semantic scoring. An invalid segment cannot
disappear through projection and allow a run to pass. Reveal the six new
duplicate aliases only after both raw outputs for every new exact input are
immutable and their opaque canonical bytes and hashes have been recorded.
Experiment 1's base mapping may already be known to the scorer, but the frozen
candidate executable receives only opaque IDs and vector bytes.

Baseline `L` must contain these three complete subject segments:

```text
{A1 A2 A3 A4 A5 A6}
{B1 B2 B3 B4 B5 B6}
{C1 C2 C3 C4 C5 C6}
```

Baseline `R` must contain these three complete subject segments:

```text
{D1 D2 D3 D4 D5 D6}
{E1 E2 E3 E4 E5 E6}
{F1 F2 F3 F4 F5 F6}
```

Every other returned segment containing two or more baseline vectors must be a
subset of one declared subject. Extra same-subject subsegments and singletons
are allowed, matching the architecture's shared output contract. The complete
profile-verified, valid, repeatable baseline output—including every allowed
extra segment—then becomes that branch's local reference output.

A baseline qualification failure withholds verdicts for its dependent
comparisons because there is no clean local output to preserve. It does not
suppress an independent baseline or its conditions, and it does not cancel
already frozen runs.

## Projection used by addition conditions

Let `U` be all IDs from one baseline. To inspect the baseline portion of an
augmented result:

1. intersect every returned segment with `U`;
2. discard empty intersections;
3. retain every nonempty intersection, including singletons;
4. fail if two projected segments have identical members;
5. compare the unordered projected collection with the complete local
   reference output.

Projection alone can hide a segment that also contains newly added vectors.
The unrelated-addition condition therefore scores cross-subject contamination
separately from projection equality. The imported combined artifact's purity
is already an exact prerequisite owned by Experiment 1; Experiment 6 does not
score it again.

## Fresh-run requirement

Apply the shared two-invocation fresh-process requirement to every exact input.
Repeatability gates only that input and comparisons that depend on it. Two
matching invocations establish repeatability only for those exact runs, not
general determinism.

## Integrity and local prerequisites

The construction and conformance-integrity requirements in
[README.md](README.md) are evaluated separately for each candidate. A
construction violation or repeatable cross-order difference is a conformance
failure. An invalid or non-repeatable conformance input is an integrity failure
with no conformance or semantic verdict. A conformance failure blocks semantic
scoring for that candidate instance. An exact-input integrity failure blocks
only that input and its dependent comparisons. Neither blocks the other
candidate.

This experiment records a candidate-specific stability result for exact
duplicates, unrelated-subject addition, and combined recovered collections. A
scored failure in any of those three conditions is a stability failure for that
candidate. It does not rewrite the scoped observations already preserved by
another experiment or stop remaining local runs.

`L0` and `R0` are **local prerequisites**. They establish the exact positive
output that a dependent intervention must preserve in this fixture. An
Experiment 1 pass cannot replace either local baseline: each local input is a
strict subset with a different collection context. A failed local prerequisite
gives its dependent condition no verdict; it is not itself a stability failure
and does not suppress any configured run. An unresolved local branch leaves
that candidate's overall stability result incomplete without converting the
no-verdict state into a focal failure.

## Protocol

1. Verify the recorded 2026-08-31 human approval and freeze this protocol
   before the shared Experiment 1 default output is generated.
2. Freeze both complete candidate identities and execution profiles and the
   readable membership specifications for the four new Experiment 6 inputs:
   `L0`, `R0`, duplicate, and unrelated addition. Each identity must include
   the shared input-adapter version and its applicable SNN or HDBSCAN*
   fine-output-selector version from `README.md`.
3. Reuse Experiment 1's opaque IDs and committed order for every base-vector
   subset. Generate and commit only the six new duplicate IDs.
4. Verify and reuse the one shared 36-vector Experiment 1 artifact, including
   its dimensions and hashes. Materialize and freeze the four exact ordered
   `(opaque ID, vector bytes)` inputs once. For each candidate, verify that its
   imported default output has that candidate's identity and verified
   execution-profile hash plus the shared IDs, vector bytes, and order, a valid
   result, two equal canonical repetitions, and an Experiment 1
   recovery-and-purity pass.
5. For each candidate, run each of the four new exact inputs twice in fresh
   processes, even if one baseline later fails. Verify every invocation's
   actual execution profile before accepting its output. This produces eight
   new raw outputs per candidate and sixteen total, plus each candidate's two
   imported Experiment 1 outputs.
6. Preserve each run's canonical representative order and complete alias
   groups. Validate and canonicalize every expanded opaque output. The readable
   mapping may be known to the scorer after Experiment 1, but it must never be
   exposed to the already frozen candidate executable.
7. Score each condition using the dependency graph below.

## Verdict dependency graph

- Baseline `L0` gates the duplicate and unrelated-addition conditions.
- Baseline `L0` gates the imported combined artifact's `L`-side verdict;
  baseline `R0` independently gates its `R`-side verdict. Experiment 1's pass
  already establishes the exact imported artifact's cross-subject purity, so
  each Experiment 6 side checks only preservation of its own complete local
  reference output. The complete combined-collection verdict requires both
  side verdicts.
- An execution-profile, output-validity, or repeatability integrity failure for
  one exact input gates that input and comparisons depending on it, but not
  independent branches.

Always record every raw run and the imported Experiment 1 pair. A gated
condition is reported as **no verdict**, not as a stability pass or failure.
The alias lists below define input membership for readability, not arrival
order. Executable inputs replace each alias with its mapped opaque ID and use
the shared committed order; the candidate never receives an alias.

## Baselines

### Baseline `L0`

```text
A1 A2 A3 A4 A5 A6 B1 B2 B3 B4 B5 B6 C1 C2 C3 C4 C5 C6
```

It qualifies only when both fresh runs match the frozen execution profile, are
valid and repeatable, and the agreed output meets baseline `L`'s
subject-recovery and purity rule. Preserve that complete agreed output as local
reference `L`.

### Baseline `R0`

```text
D1 D2 D3 D4 D5 D6 E1 E2 E3 E4 E5 E6 F1 F2 F3 F4 F5 F6
```

It qualifies only when both fresh runs match the frozen execution profile, are
valid and repeatable, and the agreed output meets baseline `R`'s
subject-recovery and purity rule. Preserve that complete agreed output as local
reference `R`.

## Exact-duplicate condition

Create six aliases with exact vector bytes:

```text
A1' = A1
A2' = A2
A3' = A3
A4' = A4
A5' = A5
A6' = A6
```

The duplicate input contains the complete `L0` baseline plus the six new
aliases:

```text
A1 A2 A3 A4 A5 A6 B1 B2 B3 B4 B5 B6 C1 C2 C3 C4 C5 C6
A1' A2' A3' A4' A5' A6'
```

Construct the expected output from local reference `L`: for each occurrence of
an original `Ai` in a reference segment, add its corresponding alias `Ai'` to
that segment. Leave every other reference segment unchanged. For the three
required complete subject segments, this transformation produces:

```text
{A1 A1' A2 A2' A3 A3' A4 A4' A5 A5' A6 A6'}
{B1 B2 B3 B4 B5 B6}
{C1 C2 C3 C4 C5 C6}
```

Any allowed extra reference segments undergo the same transformation. Both
fresh runs must return exactly the complete transformed reference output. Do
not collapse aliases in the selected output before scoring. The shared adapter
collapses them only while running the algorithm core, then must restore them
before output validation and scoring.

This condition tests one subject whose six instances are each duplicated
once. It does not establish invariance to every possible duplicate pattern.

## Unrelated-subject addition

Add subject `D` to the complete `L0` baseline:

```text
A1 A2 A3 A4 A5 A6 B1 B2 B3 B4 B5 B6 C1 C2 C3 C4 C5 C6
D1 D2 D3 D4 D5 D6
```

The condition passes only when:

1. projection onto `A1` through `C6` exactly reproduces local reference `L`;
2. no segment contains both an `A`–`C` vector and a `D` vector.

Subject to the general output contract, pure `D`-only output is recorded but
does not affect this verdict. Subject `D` is not required to reproduce its
behavior from baseline `R`, because its surrounding collection is different
here.

## Combined-collection condition

Use the already profile-verified, valid, repeatable Experiment 1 default output.
Its exact input is the complete `L0` and `R0` collection:

```text
A1 A2 A3 A4 A5 A6 B1 B2 B3 B4 B5 B6 C1 C2 C3 C4 C5 C6
D1 D2 D3 D4 D5 D6 E1 E2 E3 E4 E5 E6 F1 F2 F3 F4 F5 F6
```

For each qualified local reference, score one independent side verdict:

- the `L` side passes only when projection onto `A1` through `C6` exactly
  reproduces local reference `L`;
- the `R` side passes only when projection onto `D1` through `F6` exactly
  reproduces local reference `R`.

A missing local reference gives only its side no verdict. It does not erase
the other side's qualified projection result. Preserve every segment from the
imported artifact. The complete combined-collection verdict exists only when
the imported Experiment 1 artifact passed its recovery-and-purity rule under
the same frozen candidate identity and verified execution-profile hash and both
side verdicts exist; it passes only when both sides pass.

## Overall pass rule

The suite stability qualification passes only if:

1. both baselines qualify and establish their complete local reference
   outputs;
2. every invocation matches the frozen execution profile and every repeated
   exact input is repeatable;
3. the exact-duplicate condition passes;
4. the unrelated-subject addition passes;
5. the combined-collection condition passes.

Do not average verdicts.

Classify a non-pass before interpreting it:

- **integrity failure:** one of the shared execution checks failed, including
  an execution-profile mismatch, an invalid raw output, or unequal canonical
  repetitions; that exact input and its dependents receive no verdict;
- **local prerequisite failure:** both valid baseline repetitions agree but the
  output misses a required subject segment or contains a cross-subject
  multi-vector segment;
- **stability failure:** every prerequisite for that condition is valid,
  exact, and repeatable, but the repeatable intervention output violates
  its frozen expectation.

An integrity or local prerequisite failure does not support a stability
conclusion for the affected branch. Record the exact integrity cause and every
independent branch verdict, but do not reinterpret one as another. A scored
failure in any of the three owned conditions fails the suite stability
qualification.

## Required record

Preserve:

- the Experiment 1 manifest, hashes of the approved protocol, verified hashes
  of its 36 reused vector artifacts, and its exact default input/output pair;
- the scorer-only alias mapping, the six duplicate-ID derivations, their
  private mapping, order keys, and pre-run commitment;
- candidate implementation and configuration identities, the execution-profile
  manifest and hash, the input-adapter and fine-output-selector versions, and
  every invocation's actual-profile verification;
- every run's canonical representative order and complete alias groups;
- all four new exact ordered inputs;
- both raw outputs, canonical JSON, and SHA-256 hashes for each new input, plus
  the imported pair's corresponding records;
- both complete qualified local reference outputs and the complete transformed
  duplicate expectation derived from reference `L`;
- every projected collection;
- both independent combined-collection side verdicts, their projections, and
  their local dependency states;
- every added, removed, split, merged, duplicated, or cross-subject segment;
- every prerequisite, repeatability, and condition verdict; and
- the overall suite stability qualification and the dependency reason when it
  fails or is withheld.

Do not copy the 36 notes, masks, raw vector bytes, or cosine matrix into a
second Experiment 6 artifact. Experiment 1 remains their canonical source;
Experiment 6 records and verifies the referenced hashes.

## What a result means

A pass supports exact output stability for these frozen subjects and exact
perturbations. It does not establish production-scale stability, arbitrary
duplicate patterns, streaming updates, natural near-duplicates, changes to
configuration or seed, every semantic area in a production corpus, automatic
mask quality, or hierarchy quality.

A baseline failure does not disprove stability. It means the candidate failed
that branch's semantic prerequisite, so only its dependent stability
conditions cannot be interpreted.

A condition failure proves that its complete frozen intervention changed the
output under one verified candidate execution profile and fails the suite
stability qualification. Duplicate, addition, and combined-collection failures
do not identify which bundled mechanism—such as density, collection size, or
semantic composition—caused the change.
