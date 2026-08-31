# Experiment 2: nearby-subject organization under changing support

Status: **draft; all 96 fixture notes, masks, and declared atomic subjects
require human approval before encoding**.

## Characterization target

> Organization of nearby but meaningfully distinct fine subjects.

> Changes in organization under unequal density and sparsity.

The experiment first observes how one frozen candidate organizes nearby
subjects under balanced support. It then changes only which already-encoded
vectors enter the collection. The balanced observations provide the baseline
for describing what changes under unequal support and singleton sparsity.

This is a characterization protocol. It has no confirmation verdict, model
ranking, or selection threshold. It does not prescribe one universally correct
boundary between nearby subjects.

## Questions

1. With four vectors from each of three nearby subjects, what segments does the
   candidate return?
2. Holding the local collection size at twelve, how does changing support from
   `4:4:4` to `8:2:2`, `6:5:1`, or `8:3:1` change those segments?

## Program role

Experiment 2 is a late characterization sibling of the targeted hypothesis
tests. The default spending graph schedules it only after the exact candidate
identity has passed the earlier qualification and focal tests in `README.md`.
Those upstream results are only scheduling gates: none can supply a semantic
baseline for an Experiment 2 comparison.

Within Experiment 2, every unequal-support comparison is scientifically gated
by its matched local balanced configuration for the same neighborhood and
schedule. Experiment 2 neither qualifies the candidate nor gates a targeted
hypothesis test.

## Design

Encoding, candidate construction, candidate I/O, fine-output selection, and
artifact freezing follow the [`README.md`](README.md). This document adds
only the fixture, schedule, blinding, replay, and evaluation rules specific to
Experiment 2.

The fixture contains four independent semantic neighborhoods:

1. processing coffee beans;
2. editing photographs;
3. caring for rose bushes;
4. developing software.

Each neighborhood contains three nearby but meaningfully different atomic
subjects, with eight formulations per subject. This gives 24 vectors per
neighborhood and 96 frozen vectors total.

Every complete note is also its complete mask. Each heading is the frozen
atomic subject represented by all eight masks beneath it. A mask is valid only
when it clearly expresses that subject and contains no additional substantive
subject or narrower method, motivation, setting, quantity, or outcome.
Grammatical person, tense, and voice are carrier form, not separate subjects.

Each subject uses the same eight wording forms:

| Form | Structure |
|---|---|
| A | active, canonical wording |
| B | active, equivalent paraphrase |
| C | passive, canonical wording |
| D | passive, equivalent paraphrase |
| E | object-focus, canonical wording |
| F | object-focus, equivalent paraphrase |
| G | ongoing-process, canonical wording |
| H | ongoing-process, equivalent paraphrase |

The eight formulations for every subject remain one frozen pool. Within a
neighborhood, the three subjects begin at different positions in that pool;
the exact phase rule is defined under **Frozen formulation schedule**. Across
neighborhoods, the form order is also staggered:

| Neighborhood | Forms at indices 1 through 8 |
|---|---|
| Coffee | A, B, C, D, E, F, G, H |
| Photograph | C, D, E, F, G, H, A, B |
| Rose bush | E, F, G, H, A, B, C, D |
| Software | G, H, A, B, C, D, E, F |

The neighborhood staggering and subject phases prevent subjects with the same
support role from automatically receiving identical wording-form windows.
Necessary subject words may repeat; incidental carrier phrases or writing
styles may not identify one subject. Freeze the numeric schedule index, subject
phase, and wording form as fixture metadata.

The candidate sees three kinds of local run:

1. one balanced twelve-vector collection from one neighborhood;
2. twelve-vector collections with unequal support; and
3. twelve-vector collections containing a singleton subject instance.

Because every local support-stress run contains twelve vectors, its counts are
a complete support **allocation**: increasing one subject's support necessarily
reduces another's. The experiment compares behavior under each allocation. It
does not claim to identify the independent causal effect of one subject's
support count.

## Fixture

### Coffee processing

#### `COFFEE-R`: roasting green coffee beans

| ID | Complete note and exact mask |
|---|---|
| `COFFEE-R1` | ⟦I'm roasting green coffee beans.⟧ |
| `COFFEE-R2` | ⟦I'm roasting unroasted coffee beans.⟧ |
| `COFFEE-R3` | ⟦Green coffee beans are being roasted.⟧ |
| `COFFEE-R4` | ⟦Unroasted coffee beans are undergoing roasting.⟧ |
| `COFFEE-R5` | ⟦Green coffee beans are what I'm roasting.⟧ |
| `COFFEE-R6` | ⟦Unroasted coffee beans are what I'm roasting.⟧ |
| `COFFEE-R7` | ⟦Roasting green coffee beans is underway.⟧ |
| `COFFEE-R8` | ⟦I'm in the middle of roasting unroasted coffee beans.⟧ |

#### `COFFEE-G`: grinding roasted coffee beans

| ID | Complete note and exact mask |
|---|---|
| `COFFEE-G1` | ⟦I'm grinding roasted coffee beans.⟧ |
| `COFFEE-G2` | ⟦I'm grinding coffee beans that were previously roasted.⟧ |
| `COFFEE-G3` | ⟦Roasted coffee beans are being ground.⟧ |
| `COFFEE-G4` | ⟦Coffee beans that were previously roasted are undergoing grinding.⟧ |
| `COFFEE-G5` | ⟦Roasted coffee beans are what I'm grinding.⟧ |
| `COFFEE-G6` | ⟦Previously roasted coffee beans are what I'm grinding.⟧ |
| `COFFEE-G7` | ⟦Grinding roasted coffee beans is underway.⟧ |
| `COFFEE-G8` | ⟦I'm in the middle of grinding previously roasted coffee beans.⟧ |

#### `COFFEE-E`: extracting espresso

| ID | Complete note and exact mask |
|---|---|
| `COFFEE-E1` | ⟦I'm extracting espresso.⟧ |
| `COFFEE-E2` | ⟦I'm pulling espresso.⟧ |
| `COFFEE-E3` | ⟦Espresso is being extracted.⟧ |
| `COFFEE-E4` | ⟦Espresso is being pulled.⟧ |
| `COFFEE-E5` | ⟦Espresso is what I'm extracting.⟧ |
| `COFFEE-E6` | ⟦Espresso is what I'm pulling.⟧ |
| `COFFEE-E7` | ⟦Extracting espresso is underway.⟧ |
| `COFFEE-E8` | ⟦I'm in the middle of pulling espresso.⟧ |

### Photograph editing

#### `PHOTO-C`: cropping a photograph

| ID | Complete note and exact mask |
|---|---|
| `PHOTO-C1` | ⟦A photograph is being cropped.⟧ |
| `PHOTO-C2` | ⟦A photograph's crop is being changed.⟧ |
| `PHOTO-C3` | ⟦A photograph is what I'm cropping.⟧ |
| `PHOTO-C4` | ⟦A photograph's crop is what I'm changing.⟧ |
| `PHOTO-C5` | ⟦Cropping a photograph is underway.⟧ |
| `PHOTO-C6` | ⟦I'm in the middle of changing a photograph's crop.⟧ |
| `PHOTO-C7` | ⟦I'm cropping a photograph.⟧ |
| `PHOTO-C8` | ⟦I'm changing a photograph's crop.⟧ |

#### `PHOTO-A`: adjusting a photograph's colors

| ID | Complete note and exact mask |
|---|---|
| `PHOTO-A1` | ⟦A photograph's colors are being adjusted.⟧ |
| `PHOTO-A2` | ⟦The colors in a photograph are being changed.⟧ |
| `PHOTO-A3` | ⟦A photograph's colors are what I'm adjusting.⟧ |
| `PHOTO-A4` | ⟦A photograph's colors are what I'm changing.⟧ |
| `PHOTO-A5` | ⟦Adjusting a photograph's colors is underway.⟧ |
| `PHOTO-A6` | ⟦I'm in the middle of changing a photograph's colors.⟧ |
| `PHOTO-A7` | ⟦I'm adjusting a photograph's colors.⟧ |
| `PHOTO-A8` | ⟦I'm changing the colors in a photograph.⟧ |

#### `PHOTO-S`: straightening a tilted photograph

| ID | Complete note and exact mask |
|---|---|
| `PHOTO-S1` | ⟦A tilted photograph is being straightened.⟧ |
| `PHOTO-S2` | ⟦The tilt in a photograph is being corrected.⟧ |
| `PHOTO-S3` | ⟦A tilted photograph is what I'm straightening.⟧ |
| `PHOTO-S4` | ⟦A photograph's tilt is what I'm correcting.⟧ |
| `PHOTO-S5` | ⟦Straightening a tilted photograph is underway.⟧ |
| `PHOTO-S6` | ⟦I'm in the middle of correcting a photograph's tilt.⟧ |
| `PHOTO-S7` | ⟦I'm straightening a tilted photograph.⟧ |
| `PHOTO-S8` | ⟦I'm correcting the tilt in a photograph.⟧ |

### Rose-bush care

#### `ROSE-P`: pruning a rose bush

| ID | Complete note and exact mask |
|---|---|
| `ROSE-P1` | ⟦A rose bush is what I'm pruning.⟧ |
| `ROSE-P2` | ⟦A rose bush is what I'm cutting back.⟧ |
| `ROSE-P3` | ⟦Pruning a rose bush is underway.⟧ |
| `ROSE-P4` | ⟦I'm in the middle of cutting back a rose bush.⟧ |
| `ROSE-P5` | ⟦I'm pruning a rose bush.⟧ |
| `ROSE-P6` | ⟦I'm cutting back a rose bush.⟧ |
| `ROSE-P7` | ⟦A rose bush is being pruned.⟧ |
| `ROSE-P8` | ⟦A rose bush is being cut back.⟧ |

#### `ROSE-W`: watering a rose bush

| ID | Complete note and exact mask |
|---|---|
| `ROSE-W1` | ⟦A rose bush is what I'm watering.⟧ |
| `ROSE-W2` | ⟦A rose bush is what I'm supplying water to.⟧ |
| `ROSE-W3` | ⟦Watering a rose bush is underway.⟧ |
| `ROSE-W4` | ⟦I'm in the middle of supplying water to a rose bush.⟧ |
| `ROSE-W5` | ⟦I'm watering a rose bush.⟧ |
| `ROSE-W6` | ⟦I'm supplying water to a rose bush.⟧ |
| `ROSE-W7` | ⟦A rose bush is being watered.⟧ |
| `ROSE-W8` | ⟦Water is being supplied to a rose bush.⟧ |

#### `ROSE-F`: fertilizing a rose bush

| ID | Complete note and exact mask |
|---|---|
| `ROSE-F1` | ⟦A rose bush is what I'm fertilizing.⟧ |
| `ROSE-F2` | ⟦A rose bush is what I'm applying fertilizer to.⟧ |
| `ROSE-F3` | ⟦Fertilizing a rose bush is underway.⟧ |
| `ROSE-F4` | ⟦I'm in the middle of applying fertilizer to a rose bush.⟧ |
| `ROSE-F5` | ⟦I'm fertilizing a rose bush.⟧ |
| `ROSE-F6` | ⟦I'm applying fertilizer to a rose bush.⟧ |
| `ROSE-F7` | ⟦A rose bush is being fertilized.⟧ |
| `ROSE-F8` | ⟦Fertilizer is being applied to a rose bush.⟧ |

### Software development

#### `SOFTWARE-C`: compiling source code

| ID | Complete note and exact mask |
|---|---|
| `SOFTWARE-C1` | ⟦Compiling source code is underway.⟧ |
| `SOFTWARE-C2` | ⟦I'm in the middle of putting source code through compilation.⟧ |
| `SOFTWARE-C3` | ⟦I'm compiling source code.⟧ |
| `SOFTWARE-C4` | ⟦I'm putting source code through compilation.⟧ |
| `SOFTWARE-C5` | ⟦Source code is being compiled.⟧ |
| `SOFTWARE-C6` | ⟦Source code is undergoing compilation.⟧ |
| `SOFTWARE-C7` | ⟦Source code is what I'm compiling.⟧ |
| `SOFTWARE-C8` | ⟦Source code is what I'm putting through compilation.⟧ |

#### `SOFTWARE-T`: running automated software tests

| ID | Complete note and exact mask |
|---|---|
| `SOFTWARE-T1` | ⟦Running automated software tests is underway.⟧ |
| `SOFTWARE-T2` | ⟦I'm in the middle of executing automated software tests.⟧ |
| `SOFTWARE-T3` | ⟦I'm running automated software tests.⟧ |
| `SOFTWARE-T4` | ⟦I'm executing automated software tests.⟧ |
| `SOFTWARE-T5` | ⟦Automated software tests are being run.⟧ |
| `SOFTWARE-T6` | ⟦Automated software tests are being executed.⟧ |
| `SOFTWARE-T7` | ⟦Automated software tests are what I'm running.⟧ |
| `SOFTWARE-T8` | ⟦Automated software tests are what I'm executing.⟧ |

#### `SOFTWARE-D`: debugging a program

| ID | Complete note and exact mask |
|---|---|
| `SOFTWARE-D1` | ⟦Debugging a program is underway.⟧ |
| `SOFTWARE-D2` | ⟦I'm in the middle of debugging a program.⟧ |
| `SOFTWARE-D3` | ⟦I'm debugging a program.⟧ |
| `SOFTWARE-D4` | ⟦I'm finding and fixing bugs in a program.⟧ |
| `SOFTWARE-D5` | ⟦A program is being debugged.⟧ |
| `SOFTWARE-D6` | ⟦Debugging work is being done on a program.⟧ |
| `SOFTWARE-D7` | ⟦A program is what I'm debugging.⟧ |
| `SOFTWARE-D8` | ⟦A program is what I'm doing debugging work on.⟧ |

The subject names and human-readable IDs are scoring data. The candidate never
receives them.

## Representation diagnostics

The declared neighborhoods express the human-designed semantic relationships
that this experiment asks the candidate to explore. They are not selected or
rejected using SSE cosine. Doing so would preselect the geometry whose behavior
we are trying to observe.

After the wording and masks are approved and frozen, preserve these descriptive
diagnostics:

1. the complete raw-vector cosine matrix;
2. same-subject and cross-subject cosine distributions in each neighborhood;
3. every vector's nearest same-subject rank and margin;
4. subject-by-wording-form and support-role-by-wording-form tables.

After candidate output is revealed, flag any cross-subject segment whose
members share a wording form. This is a wording-form diagnostic, not a
different scoring rule. Experiment 3 remains the controlled test of whether a
specific lexical collision causally changes the output.

For every returned segment, also record whether its members cross canonical
and equivalent-paraphrase forms. A segment containing only one wording stratum
does not demonstrate that the candidate recovered the shared subject across
the paraphrase change.

## Fixed support conditions

Every local allocation run contains exactly twelve vectors:

| Condition | Support | Primary contrast |
|---|---:|---|
| Balanced | `4:4:4` | Equal-support control |
| Imbalanced | `8:2:2` | One common subject and two rare repeated subjects |
| Singleton | `6:5:1` | One unmatched instance with two similarly supported subjects |
| Dense and singleton | `8:3:1` | A common subject, a rare repeated subject, and a singleton |

The `6:5:1` condition runs both orders of the recurring subjects. The one-vector
role is the only intentionally unmatched subject.

The frozen support role is the literal condition-and-count slot, not a derived
category such as `low-support`:

| Condition | Frozen support roles |
|---|---|
| Balanced | `balanced-4` |
| Imbalanced | `imbalanced-8`, `imbalanced-2` |
| Singleton | `singleton-6`, `singleton-5`, `singleton-1` |
| Dense and singleton | `dense-singleton-8`, `dense-singleton-3`, `dense-singleton-1` |

Subjects with equal counts in one configuration share the same role. Every
result records both this exact role and its numeric support count.

## Frozen formulation schedule

Number each subject's formulations `1` through `8`. Within every neighborhood,
call the subjects `q1`, `q2`, and `q3` in the order in which they appear in the
fixture. Give them these frozen phase offsets:

| Subject position | Phase offset |
|---|---:|
| `q1` | `0` |
| `q2` | `3` |
| `q3` | `6` |

For subject `q`, schedule index `s`, and support length `k`, start at
`s + phase(q)` and take `k` consecutive formulations, wrapping after `8`.
Call that set `Wq(k, s)`. For example, at `s = 1`:

| Subject | `Wq(2, 1)` |
|---|---|
| `q1` | formulations `1–2` |
| `q2` | formulations `4–5` |
| `q3` | formulations `7–8` |

Thus, in an `8:2:2` run where `q1` is dense, `q1` contributes all eight
formulations while the two rare subjects contribute formulations `4–5` and
`7–8`. The two rare subjects do not share one wording-form pair merely because
they share one support role.

Run every condition for `s = 1 ... 8`:

- Balanced `4:4:4`: all three subjects use `Wq(4, s)`.
- Imbalanced `8:2:2`: each subject takes one turn as the eight-vector subject;
  each other subject uses `Wq(2, s)`.
- Singleton `6:5:1`: run all six ordered assignments to the three roles, using
  `Wq(6, s)`, `Wq(5, s)`, and `Wq(1, s)`.
- Dense-and-singleton stress `8:3:1`: run all six ordered role assignments,
  using all eight vectors, `Wq(3, s)`, and `Wq(1, s)`.

All index arithmetic wraps into `1 ... 8`. The same subject phase is used in
every matched balanced and unequal run. Therefore, when `k <= 4`, the unequal
run's vectors are a subset of the matched balanced run's vectors; when
`k >= 4`, the balanced vectors are a subset of the unequal run's vectors.

Across the eight schedules, every one of a subject's eight frozen vectors
appears exactly `k` times whenever that subject occupies a support role of
length `k`. Consequently:

- balanced `4:4:4` contributes four appearances per vector;
- imbalanced `8:2:2` contributes twelve appearances per vector: `8 + 2 + 2`;
- singleton `6:5:1` contributes twenty-four appearances per vector:
  `2 × (6 + 5 + 1)`;
- dense and singleton `8:3:1` contributes twenty-four appearances per vector:
  `2 × (8 + 3 + 1)`.

Every frozen vector therefore appears in exactly 64 of the 512 unique local
configurations and 128 of the repeated invocations. No formulation is
systematically assigned to common, rare, or singleton support.

The eight cyclic schedules are the complete frozen schedule family and every
one is reported. They provide balanced individual-vector coverage, but they
are not independent statistical replicates and do not exhaust every possible
subset or every possible pairing of formulations. The fixed phases eliminate
identical wording-form windows between subjects; they do not equalize every
pairwise co-occurrence of forms. Preserve that residual limitation when
interpreting a form-specific output difference.

These local schedules produce 128 unique configurations per neighborhood and
512 unique local configurations total:

| Condition | Unique configurations per neighborhood |
|---|---:|
| Balanced | 8 |
| Imbalanced | 24 |
| Singleton | 48 |
| Dense and singleton | 48 |

The complete protocol therefore defines 512 unique input/run configurations per
frozen candidate and seed. Each configuration is invoked twice from fresh
candidate state, for 1,024 invocations total. The 96 SSE vectors are generated
once. No candidate invocation re-encodes text.

## Blinding and run isolation

Use `02-nearby-subject-resolution` as the shared blinding namespace. The HMAC
mapping and order in `README.md` define every opaque ID and its frozen global
rank. Order each local run by filtering that global order.

The candidate receives no condition name, role, support count, subject name, or
human-readable ID. Dense, rare, and singleton vectors are never deliberately
placed in contiguous blocks.

Create two invocation records for each of the 512 configurations and freeze one
random execution order over all 1,024 records. Represent one configuration as
compact UTF-8 JSON with no trailing newline:

```text
["local", neighborhood, condition, s, role_assignment]
```

Use the neighborhood codes `coffee`, `photograph`, `rose`, and `software`; the
condition codes `balanced`, `imbalanced`, `singleton`, and
`dense-singleton`; and JSON integers `1` through `8` for `s`. For balanced,
`role_assignment` is `["q1","q2","q3"]`. For imbalanced it is the one-element
array containing the dense subject. For singleton it lists the `6`, `5`, and
`1` subjects in that order. For dense-singleton it lists the `8`, `3`, and `1`
subjects in that order.

Derive each subject's frozen support-role code from the condition and that
subject's position in `role_assignment` using the support-role table above. For
imbalanced configurations, subjects absent from the one-element array receive
`imbalanced-2`.

Represent an invocation record as compact JSON
`[configuration, repetition]`, where repetition is integer `1` or `2`. Derive:

```text
execution_key = HMAC-SHA-256(
  shared_blinding_seed,
  "fine-segmentation-exp2-execution-order-v1\0" ||
  "02-nearby-subject-resolution\0" || invocation_record_bytes
)
```

Sort by the 32 digest bytes, breaking a collision by the invocation-record
bytes. Every invocation starts in a fresh process from the same candidate
state, declared candidate seed, and frozen execution profile. Before accepting
an output, capture the invocation's actual profile using the shared canonical
schema and verify its hash. A missing or mismatched profile is an integrity
failure for that configuration. No invocation can train or prime another.

For replay comparison, first validate and then canonicalize each complete
opaque-ID output under the shared contract. A duplicate raw member set is an
output-contract failure, not multiplicity to preserve. The two valid canonical
outputs for a configuration must match byte for byte. If they do not, record a
**repeatability failure**, preserve both outputs, and give every outcome or
comparison that depends on that configuration **no verdict**; never choose one
invocation as authoritative.

For the rest of this protocol, a configuration is **eligible** only when every
shared integrity check affecting it has passed: both invocations match the
frozen execution profile, both raw outputs pass the output contract, the two
canonical outputs are byte-for-byte equal, and the shared approval, encoding,
and blinding prerequisites remain valid.

This experiment uses one frozen within-invocation input order. The candidate
must meet the shared contract's construction-level permutation-invariance
requirement. The suite-level conformance preflight in `README.md` owns the
empirical order check; this experiment does not add ad hoc order variants.

## Evaluation

This is a characterization experiment, not an all-runs-must-pass test. The
balanced local configurations establish the baseline behavior that later
unequal-support conditions may change. The declared subjects are reference
cohorts, not prescribed segment boundaries.

For each eligible configuration, record these separate outcomes:

1. **Reference-cohort recovery:** for each declared subject with at least two
   present vectors, whether one returned member set is exactly the set of its
   present vectors. A one-vector subject has no cohort-recovery verdict.
2. **Cross-subject membership:** every segment containing vectors from more
   than one declared subject, plus every member's exact support count and
   frozen support role in that configuration. Do not derive or score an
   additional `low-support` category.
3. **Omission:** which vectors receive no fine-segment membership.
4. **Fragmentation and extra segments:** every same-subject member set,
   including partial sets that coexist with a complete recovered segment.
5. **Singleton disposition:** independently record whether a one-member segment
   exists, whether the singleton has no membership, every multi-member segment
   it joins, and whether any such membership is invalid. These fields are not
   mutually exclusive.

A segment spanning declared subjects does not count as reference-cohort
recovery, but it is not automatically invalid: the candidate may return
overlapping subjects that differ from the declared reference cohorts.

Freeze the semantic-review rubric, one primary human reviewer, reviewer
procedure, review shuffle seed, and finite packet budget before candidate
execution. After all candidate outputs are immutable and readable identities
are restored, form the review pool from every unique segment in an eligible
configuration that contains vectors from at least two declared subjects.
Uniqueness is the canonical fixture-member set, so an identical member set is
reviewed once and its frozen verdict is reused for every occurrence. Preserve
segments from ineligible configurations in the execution record, but do not
send them to semantic review or use them in semantic characterization. The
execution-profile, output-contract, or repeatability cause itself remains part
of the final candidate-decision record.

If the complete pool exceeds the frozen packet budget, do not review a subset.
Record a **review-capacity failure** and preserve all automated configuration,
membership, and support-stress observations. Cross-subject semantic verdicts,
including invalid membership and false absorption, are unavailable, and the
suite's final review cannot choose `proceed` for this candidate.

Do not send singleton or same-declared-subject segments to semantic review.
Human fixture approval already establishes the common atomic subject for every
same-subject subset; singleton disposition is recorded directly. Reviewing
either again would add work without resolving an unknown relationship.
Cross-subject segments are reviewed because they may still express a valid
alternative fine subject not represented by the declared cohorts.

Build the review packets only after that pool is fixed. Hide the candidate,
invocation, run configuration, condition, schedule, support roles, declared
subject and neighborhood labels, fixture IDs, opaque IDs, and the opaque-ID
mapping. A packet contains only the segment's complete masks under packet-local
neutral labels. Draw and freeze one independent 32-byte review seed before
candidate execution and record:

```text
review_seed_commitment = SHA-256(
  "fine-segmentation-exp2-review-seed-v1\0" ||
  "02-nearby-subject-resolution\0" || review_seed
)
```

For ordering only, a packet's canonical opaque member-set bytes are the compact
JSON array of its lowercase opaque IDs sorted by decoded 32-byte ID value, with
no trailing newline. Derive:

```text
packet_key = HMAC-SHA-256(
  review_seed,
  "fine-segmentation-exp2-review-packet-v1\0" ||
  "02-nearby-subject-resolution\0" || packet_member_set_bytes
)

member_key = HMAC-SHA-256(
  review_seed,
  "fine-segmentation-exp2-review-member-v1\0" ||
  "02-nearby-subject-resolution\0" || packet_member_set_bytes || "\0" ||
  member_opaque_id_bytes
)
```

Sort packets and members by their 32 digest bytes. Break a packet-key collision
by packet-member-set bytes and a member-key collision by opaque-ID bytes. The
primary reviewer sees only those fixed orders.

For each packet, ask whether all members are recognizable as refinements of one
fine subject. The verdict must be exactly one of:

- **valid:** record one recognizable fine subject in a non-disjunctive form,
  and every member is a valid refinement of it;
- **invalid:** no one recognizable, non-disjunctive fine subject covers every
  member;
- **uncertain:** the reviewer cannot decide between `valid` and `invalid` from
  the masks.

A disjunction or list of member subjects is not one subject. Do not coerce
`uncertain` to `invalid`; report uncertain segments and every occurrence of
them separately. The primary reviewer completes each packet once; there is no
post-output adjudication or replacement reviewer.

The neighborhood umbrella alone—`coffee processing`, `photograph editing`,
`rose-bush care`, or `software development`—is too broad to validate a fine
segment. Record `invalid cross-subject membership` when a cross-subject segment
receives `invalid`. When such a segment contains a rare or singleton vector,
additionally record `false absorption`; this does not assert which vector
entered which pre-existing segment. An `uncertain` cross-subject segment is
reported separately and is not counted as invalid or false absorption.

This review is metadata-blind, not source-blind: the synthetic wording may be
recognizable. Declared-cohort recovery and alternative semantic validity remain
separate measurements. A valid alternative segment never changes the declared
allocation used to describe that configuration.

### Final decision report

After every automated outcome, semantic-review judgment, and matched comparison
is immutable, generate the decision report and coverage manifest required by
`README.md`. The manifest must enumerate every one of the 512 unique
configurations exactly once and bind each to its two invocation records. For
each invocation, record the actual-profile result, raw-output validity, and
canonical-output hash when available. Record one configuration-level canonical
hash only when the configuration is eligible and both hashes agree. Also bind
the configuration to its declared-cohort outcomes, singleton disposition, and
every matched comparison that consumes it.

The report may aggregate repeated results by neighborhood, condition, schedule,
support role, and result class. It must separately enumerate every invalid or
uncertain reviewed segment, false absorption, integrity failure,
local-prerequisite failure, unavailable survival statement, and
neighborhood-specific exception. Each aggregate and exception links back to
the immutable configuration records in the coverage manifest.

The primary reviewer examines this generated report rather than manually
opening all 512 configuration records or all 1,024 raw invocation outputs.
Review is incomplete, and `proceed` is unavailable, unless the coverage
manifest validates and every required exception has a recorded disposition and
is addressed by the written rationale.

### Balanced-baseline conditioning

For each neighborhood, declared subject, and schedule `s`, its eligible local
balanced configuration is the balanced baseline. Describe recovery as
**surviving** an unequal-support condition only when that subject's reference
cohort recovered in this matched balanced baseline and the compared
configuration is also eligible. If the balanced baseline did not recover the
cohort, record a **local prerequisite failure** for that matched comparison and
preserve all later recovery, fragmentation, omission, membership, and
semantic-review outcomes, but record **no survival verdict because matched
baseline did not recover**. If either required configuration has an
execution-profile, output-contract, or repeatability integrity failure, record
**no survival verdict because `<configuration ID>` had `<integrity failure
class>`** for each affected configuration. For an eligible comparison, record
`survived` exactly when the cohort also meets the reference-cohort recovery rule
in the compared configuration; otherwise record `did not survive`. A
one-vector subject has disposition fields rather than a recovery-survival
claim.

### Canonical projection rule

For an output and retained-ID set `K`, intersect each source segment with `K`
and discard every empty projection. Canonicalize each remaining projected
member set by the frozen global ID rank. The projected output is the multiset
of those canonical member sets: identical projected sets retain one count per
source-segment occurrence.

Compare projected outputs as multisets, including multiplicity. For every
canonical member set, the exact signed difference is its count in the first
multiset minus its count in the second. Separately retain a provenance row for
each projected occurrence containing its complete unprojected source segment,
source configuration, and source invocation. Source provenance is not part of
the canonical multiset and must not be used to make otherwise equal
projections unequal.

### Balanced local organization

For the 32 unique balanced local configurations, preserve both invocations,
every returned member set, and the blinded semantic judgment above. For each
eligible configuration, describe whether the candidate recovers the three
declared cohorts, combines nearby cohorts into valid broader fine subjects,
fragments them, overlaps them, or omits vectors. No one of those shapes is
declared correct in advance.

### Balanced versus unequal support

For every neighborhood, schedule `s`, and role assignment, pair the unequal
run with that neighborhood's balanced run for the same `s`. Produce the
projected-output comparison only when both exact configurations are eligible.
Otherwise record **no projected-output verdict because
`<configuration ID>` had `<integrity failure class>`** for each affected
configuration. For an available comparison, record:

1. the IDs shared by the two inputs;
2. each run's complete output;
3. each output's canonical projected member-set multiset on those shared IDs,
   after discarding empty projections;
4. the exact signed difference `unequal projection count - balanced projection
   count` for every member set;
5. source-segment provenance for every projected occurrence, retained
   separately from the canonical multisets.

Analysts may describe a change as a gain, loss, split, merge, omission, or
absorption, but those are qualitative annotations. The preserved inputs,
complete outputs, projected multisets, exact multiplicity differences,
provenance rows, and frozen semantic-review verdicts are the authoritative
record.

The matched comparison measures how segmentation changes under each complete
support allocation. It does not isolate the causal effect of support count:
adding distinct examples necessarily changes both the number and the sampled
vector geometry, total size remains twelve, and several subject counts change
together. Exact duplicate vectors would hold the set of distinct vector
locations fixed while changing their multiplicities, but that would test
duplicate sensitivity rather than realistic unequal subject support;
Experiment 6 owns duplicate stability.

Compare results by neighborhood, declared subject, support role, allocation,
and formulation schedule. Report every schedule and aggregate only with
schedule as a repeated block; do not treat the 512 overlapping configurations
as 512 independent samples. Do not average away a neighborhood-specific
outcome. Raw cosine measurements and wording-form audits are diagnostics, not
semantic verdicts.

## Protocol

1. Audit every mask against its declared atomic subject. Correct any missing
   subject evidence, extra substantive meaning, or narrower qualification.
2. Counterbalance the eight wording forms inside every neighborhood. Correct
   clear incidental-template imbalances without purging necessary subject
   words or forcing unnatural synonyms.
3. Obtain human approval of all 96 notes, masks, declared atomic subjects,
   intended nearby relationships, and the semantic-review rubric, procedure,
   and finite packet budget.
4. Freeze the fixture wording and every scoring rule.
5. Freeze the candidate identity and execution profile and document its
   construction-level permutation invariance.
6. Derive and commit the shared opaque-ID mapping and global order. Freeze all
   512 unique configurations, two invocation records per configuration, and
   the randomized execution order of all 1,024 invocations. Draw and freeze the
   independent review seed.
7. Freeze the SSE boundary and exact input bytes, then encode the 96 inputs
   once and record the vector dimensions and hashes.
8. Invoke every configuration twice in separate fresh processes without
   retuning or re-encoding. Verify the actual execution profile and preserve
   every raw output while fixture identities remain hidden.
9. While identities remain hidden, validate each raw output, canonicalize every
   valid output, compare the two canonical outputs for each configuration, and
   record every execution-profile, output-contract, or repeatability failure.
   Give every dependent outcome no verdict. After all 1,024 raw outputs and
   integrity results are immutable, reveal and verify the blinding artifact;
   only then restore fixture identities.
10. Compute the frozen representation diagnostics and wording-form/support-role
    audits.
11. Fix the cross-subject segment pool. If its size is within the frozen
    packet budget, build every blinded packet in the frozen random order and
    complete the three-way semantic review. Otherwise, review none and record
    a review-capacity failure.
12. For eligible configurations, complete the balanced-baseline-conditioned
    recovery descriptions and matched support-allocation comparisons.
13. Generate and validate the frozen decision report and complete coverage
    manifest. The final reviewer may choose `proceed` only after completing the
    shared review procedure.

## Required record

Preserve:

- every complete note, mask, raw vector, and artifact hash;
- the atomic-subject equivalence audit for every mask;
- every numeric schedule index, subject phase, wording form, and recorded
  structural attribute;
- the opaque-ID mapping and global master rank order, plus the shared blinding
  seed, commitment, and post-run verification;
- the 512 unique configurations, all 1,024 invocation records in their frozen
  execution order, and every condition, role, schedule, exact input, and
  within-invocation order;
- all 1,024 raw outputs, canonical outputs and hashes for every valid raw
  output, every execution-profile, output-contract, or repeatability finding,
  and every resulting no-verdict dependency;
- every complete returned segment, overlap, singleton, and omission from both
  invocations;
- reference-cohort recovery, all cross-subject memberships, false absorption,
  omission, fragmentation, extra segments, and singleton disposition fields;
- the frozen semantic-review rubric, procedure, shuffle seed, its commitment
  and verification, cross-subject segment pool, packet and member orders, every
  `valid`, `invalid`, and `uncertain` judgment, the valid subject text, and the
  masks supporting each judgment;
- every balanced-baseline recovery prerequisite, its local-prerequisite state,
  and every resulting survival or no-verdict record;
- the frozen semantic-review packet budget, complete pool size, and any
  review-capacity failure;
- every balanced-versus-unequal shared-ID set, canonical projected multiset,
  exact multiplicity difference, and separate source-segment provenance row;
- the generated decision report, its coverage manifest and validation result,
  every aggregate-to-configuration link, every required exception disposition,
  and the final review-completion state;
- the immutable raw-vector cosine matrix, cosine summaries, and every
  wording-form/support-role audit;
- every artifact, candidate identity, execution-profile manifest and hash, and
  per-invocation actual-profile verification required by the shared contract.

## What a result means

The result characterizes how one frozen SSE-plus-segmentation system organizes
four controlled collections of nearby subjects under balanced support and how
that organization changes under the complete unequal-support and singleton
allocations. It does not attribute those changes to support count alone.

For a declared subject that recovered in its eligible matched balanced
baseline, the record can state whether recovery survived an eligible support
stress. When balanced recovery was absent, the later output remains an
observation but supports no survival statement. Any integrity failure leaves
its dependent comparisons with no verdict.

The protocol has no binary confirmation result and does not rank or select
candidates. Its returned shapes, semantic verdicts, and changes are reported
as characterization data.

A review-capacity failure is a resource result, not a semantic segmentation
failure. It prevents a final `proceed` decision because the required semantic
evidence is incomplete.

It does not establish one universally correct fine-subject boundary,
production-scale behavior, every geometric density pattern, natural-corpus
mask quality, hierarchy quality, or stability under unrelated additions or
combined collections. Experiment 6 owns those stability tests.
