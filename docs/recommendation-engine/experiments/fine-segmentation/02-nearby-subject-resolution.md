# Experiment 2: nearby-subject organization under changing support

Status: **draft; the crossed wording fixture and every atomic proposition and
mask require human approval before encoding**.

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
2. Does the same balanced local collection organize differently when the other
   three semantic neighborhoods are present?
3. Holding the local collection size at twelve, how does changing support from
   `4:4:4` to `8:2:2`, `6:5:1`, or `8:3:1` change those segments?

## Design

Encoding, candidate construction, candidate I/O, fine-output selection, and
artifact freezing follow the [shared contract](README.md). This document adds
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
They also mean every 48-vector combined balanced run contains exactly six
instances of each wording form. Necessary subject words may repeat; incidental
carrier phrases or writing styles may not identify one subject. Freeze the
numeric schedule index, subject phase, and wording form as fixture metadata.

The candidate sees four kinds of run:

1. one balanced twelve-vector collection from one neighborhood;
2. the same local collection embedded in a combined 48-vector collection;
3. local twelve-vector collections with unequal support;
4. local collections containing a singleton subject instance.

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
| `SOFTWARE-D4` | ⟦I'm in the process of debugging a program.⟧ |
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
4. the result of a binary-unigram TF-IDF leave-one-out classifier within each
   24-mask neighborhood, including its complete cosine and confusion matrices;
5. subject-by-wording-form and support-role-by-wording-form tables, tokenizer
   lengths, and repeated incidental n-grams.

For the lexical diagnostic, lowercase and tokenize contiguous Unicode letters
and numbers, form binary unigram vectors, weight a term with document frequency
`df` as `ln((1 + 24) / (1 + df)) + 1`, and L2-normalize. Fit those weights once
on all 24 masks in the neighborhood. Classify each mask against the three
normalized mean subject centroids while excluding that mask from its own
centroid; preserve a tie as unresolved. Reuse these lexical vectors for every
support condition. The result shows how easily wording alone can recover the
declared subjects; it is not an eligibility rule. High lexical accuracy
prevents attributing functional recovery uniquely to semantic geometry, but
does not invalidate the observed segmentation.

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
configurations. The eight combined balanced configurations contribute four
more appearances, so every one of the 96 vectors appears in exactly 68 of the
520 unique configurations and 136 of the repeated invocations. No formulation
is systematically assigned to common, rare, or singleton support.

For any one subject position, the four neighborhoods' balanced length-four
windows contain each wording form twice because their form orders are shifted
by `0`, `2`, `4`, and `6`. Across all three subject positions, every combined
balanced run therefore contains six instances of each form.

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

For each `s`, also form one **combined balanced** 48-vector configuration by
taking the union of that schedule's four local balanced configurations. These
eight configurations expose the exact same local vectors in the presence of
the other three semantic areas.

The complete protocol therefore defines 520 unique input/run configurations per
frozen candidate and seed: 512 local allocation configurations plus eight
combined balanced configurations. Each configuration is invoked twice from
fresh candidate state, for 1,040 invocations total. The 96 SSE vectors are
generated once. No candidate invocation re-encodes text.

## Blinding and run isolation

Use `02-nearby-subject-resolution` as the shared blinding namespace. The HMAC
mapping and order in `README.md` define every opaque ID and its frozen global
rank. Order each local or combined run by filtering that global order.

The candidate receives no condition name, role, support count, subject name, or
human-readable ID. Dense, rare, and singleton vectors are never deliberately
placed in contiguous blocks.

Create two invocation records for each of the 520 configurations and freeze one
random execution order over all 1,040 records. Represent one configuration as
compact UTF-8 JSON with no trailing newline:

- a local run is
  `["local", neighborhood, condition, s, role_assignment]`; and
- a combined run is `["combined-balanced", s]`.

Use the neighborhood codes `coffee`, `photograph`, `rose`, and `software`; the
condition codes `balanced`, `imbalanced`, `singleton`, and
`dense-singleton`; and JSON integers `1` through `8` for `s`. For balanced,
`role_assignment` is `["q1","q2","q3"]`. For imbalanced it is the one-element
array containing the dense subject. For singleton it lists the `6`, `5`, and
`1` subjects in that order. For dense-singleton it lists the `8`, `3`, and `1`
subjects in that order.

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
state and declared candidate seed. No invocation can train or prime another.

For replay comparison, first validate and then canonicalize each complete
opaque-ID output under the shared contract. A duplicate raw member set is an
output-contract failure, not multiplicity to preserve. The two valid canonical
outputs for a configuration must match byte for byte. If they do not, mark it
`non-repeatable`, preserve both outputs, and mark every outcome or comparison
that depends on that configuration `unevaluable`; never choose one invocation
as authoritative.

This experiment uses one frozen within-invocation input order. The candidate
must meet the shared contract's construction-level permutation-invariance
requirement. An empirical input-order result from Experiment 6 is not a
substitute for that invariant, and this experiment does not add ad hoc order
variants.

## Evaluation

This is a characterization experiment, not an all-runs-must-pass test. The
balanced local configurations establish the baseline behavior that the two
later comparisons may change. The declared subjects are reference cohorts,
not prescribed segment boundaries.

For each repeatable configuration, record these separate outcomes:

1. **Reference-cohort recovery:** for each declared subject with at least two
   present vectors, whether one returned member set is exactly the set of its
   present vectors. A one-vector subject has no cohort-recovery verdict.
2. **Cross-subject membership:** every segment containing vectors from more
   than one declared subject, plus whether it contains a low-support vector.
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
procedure, and review shuffle seed before candidate execution. After all
candidate outputs are immutable, pool all unique segments from valid raw
outputs across both invocations of the one frozen candidate. Uniqueness is the
canonical fixture-member set, so an identical member set is reviewed once and
its frozen verdict is reused for every occurrence. Segments from a valid but
non-repeatable output may receive diagnostic review, but they cannot make a
dependent comparison evaluable.

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

### Balanced-baseline conditioning

For each neighborhood, declared subject, and schedule `s`, its repeatable local
balanced configuration is the balanced baseline. Describe recovery as
**surviving** a combined or unequal-support condition only when that subject's
reference cohort recovered in this matched balanced baseline and the compared
configuration is also repeatable. If the balanced baseline did not recover the
cohort, record all later recovery, fragmentation, omission, membership, and
semantic-review outcomes, but make no survival claim. If either required
configuration is non-repeatable, the dependent survival comparison is
`unevaluable`. For an eligible comparison, record `survived` exactly when the
cohort also meets the reference-cohort recovery rule in the compared
configuration; otherwise record `did not survive`. A one-vector subject has
disposition fields rather than a recovery-survival claim.

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
repeatable configuration, describe whether the candidate recovers the three
declared cohorts, combines nearby cohorts into valid broader fine subjects,
fragments them, overlaps them, or omits vectors. No one of those shapes is
declared correct in advance.

### Local versus combined balanced organization

For each neighborhood and schedule `s`, compare its local balanced output with
the combined balanced output for the same `s`:

1. apply the canonical projection rule to the combined output with that
   neighborhood's twelve IDs as `K`;
2. represent the local output as the canonical member-set multiset on those
   same IDs;
3. compare the two multisets, including every member-set multiplicity and the
   exact signed difference `combined projection count - local count`;
4. retain source-segment provenance separately for every projected occurrence;
5. separately preserve every combined-output segment that crosses semantic
   neighborhoods.

Projection shows whether the local organization changed. The separate
cross-neighborhood record prevents projection from hiding contamination. This
comparison uses identical local vectors, schedule indices, and relative order;
only the other three balanced neighborhoods were added. Empty projections are
discarded; identical nonempty projections remain present through their
multiplicity.

### Balanced versus unequal support

For every neighborhood, schedule `s`, and role assignment, pair the unequal
run with that neighborhood's balanced run for the same `s`. Record:

1. the IDs shared by the two inputs;
2. each run's complete output;
3. each output's canonical projected member-set multiset on those shared IDs,
   after discarding empty projections;
4. the exact signed difference `unequal projection count - balanced projection
   count` for every member set;
5. source-segment provenance for every projected occurrence, retained
   separately from the canonical multisets;
6. every new cross-subject member-set occurrence and its frozen blinded
   semantic-review verdict.

Analysts may describe a change as a gain, loss, split, merge, omission, or
absorption, but those are qualitative annotations. The preserved inputs,
outputs, projected multisets, and exact multiplicity difference are the
authoritative record.

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
schedule as a repeated block; do not treat the 520 overlapping configurations
as 520 independent samples. Do not average away a neighborhood-specific
outcome. Raw cosine and lexical measurements are diagnostics, not semantic
verdicts.

## Protocol

1. Audit every mask against its declared atomic subject. Correct any missing
   subject evidence, extra substantive meaning, or narrower qualification.
2. Counterbalance the eight wording forms inside every neighborhood and across
   the combined run.
   Correct clear incidental-template imbalances without purging necessary
   subject words or forcing unnatural synonyms.
3. Obtain human approval of all 96 notes, masks, atomic propositions, intended
   nearby relationships, and the semantic-review rubric and procedure.
4. Freeze the fixture wording and every scoring rule.
5. Freeze the candidate identity and document its construction-level
   permutation invariance.
6. Derive and commit the shared opaque-ID mapping and global order. Freeze all
   520 unique configurations, two invocation records per configuration, and
   the randomized execution order of all 1,040 invocations. Draw and freeze the
   independent review seed.
7. Freeze the SSE boundary and exact input bytes, then encode the 96 inputs
   once and record the vector dimensions and hashes.
8. Invoke every configuration twice in separate fresh processes without
   retuning or re-encoding. Make all 1,040 raw outputs immutable before
   restoring fixture identities.
9. Validate and compare the two canonical complete outputs for every
   configuration and mark
   non-repeatable configurations and all dependent outcomes `unevaluable`.
10. Compute the frozen representation and lexical diagnostics.
11. Fix the unique-segment pool, build the blinded packets in their frozen
    random order, and complete the three-way semantic review.
12. For repeatable configurations, complete the balanced-baseline-conditioned
    recovery descriptions, local-versus-combined comparisons, and matched
    support-allocation comparisons.

## Required record

Preserve:

- every complete note, mask, raw vector, and artifact hash;
- the atomic-subject equivalence audit for every mask;
- every numeric schedule index, subject phase, wording form, and recorded
  structural attribute;
- the opaque-ID mapping and global master rank order;
- the 520 unique configurations, all 1,040 invocation records in their frozen
  execution order, and every condition, role, schedule, exact input, and
  within-invocation order;
- all 1,040 raw outputs, canonical outputs and hashes for every valid raw
  output, and every output-contract, repeatability, or `unevaluable` finding;
- every complete returned segment, overlap, singleton, and omission from both
  invocations;
- reference-cohort recovery, all cross-subject memberships, false absorption,
  omission, fragmentation, extra segments, and singleton disposition fields;
- the frozen semantic-review rubric, procedure, shuffle seed, its commitment
  and verification, unique-segment pool, packet and member orders, every
  `valid`, `invalid`, and `uncertain` judgment, the valid subject text, and the
  masks supporting each judgment;
- every balanced-baseline recovery prerequisite and every resulting survival,
  no-survival-claim, or `unevaluable` record;
- every local-versus-combined canonical projected multiset, exact multiplicity
  difference, separate source-segment provenance row, and cross-neighborhood
  segment;
- every balanced-versus-unequal shared-ID set, canonical projected multiset,
  exact multiplicity difference, separate source-segment provenance row, and
  membership change;
- the immutable raw-vector cosine matrix and all lexical diagnostics;
- every artifact and candidate identity required by the shared contract.

## What a result means

The result characterizes how one frozen SSE-plus-segmentation system organizes
four controlled collections of nearby subjects under balanced support, whether
that organization changes when unrelated neighborhoods are present, and how it
changes under the complete unequal-support and singleton allocations. It does
not attribute those changes to support count alone.

For a declared subject that recovered in its matched balanced baseline, the
record can state whether recovery survived a repeatable stress or combined
condition. When balanced recovery was absent, the later output remains an
observation but supports no survival statement. Non-repeatable configurations
leave their dependent comparisons unevaluable.

The protocol has no binary confirmation result and does not rank or select
candidates. Its returned shapes, semantic verdicts, and changes are reported
as characterization data.

It does not establish one universally correct fine-subject boundary,
production-scale behavior, every geometric density pattern, natural-corpus
mask quality, or hierarchy quality. The combined run is one controlled global
composition check; Experiment 6 separately tests broader irrelevant-change
stability.
