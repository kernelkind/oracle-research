# Experiment 2: nearby-subject organization under changing support

Status: **draft; the crossed wording fixture and every atomic proposition and
mask require human approval before encoding**.

## Assumptions explored

> Nearby but meaningfully distinct fine subjects are resolved.

> Region recovery survives unequal density and sparsity.

The experiment first observes how one frozen candidate organizes nearby
subjects under balanced support. It then changes only which already-encoded
vectors enter the collection. This establishes the balanced behavior before
showing how that behavior changes under unequal support and singleton
sparsity.

It is exploratory. It does not prescribe one universally correct boundary
between nearby subjects or one binary pass threshold.

## Questions

1. With four vectors from each of three nearby subjects, what segments does the
   candidate return?
2. Does the same balanced local collection organize differently when the other
   three semantic neighborhoods are present?
3. Holding the local collection size at twelve, how does changing support from
   `4:4:4` to `8:2:2`, `6:5:1`, or `8:3:1` change those segments?

## Design

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

Every frozen vector therefore appears exactly 64 times across the 512 local
runs. The eight combined balanced runs contribute four more appearances, so
every one of the 96 vectors appears exactly 68 times in the complete protocol.
No formulation is systematically assigned to common, rare, or singleton
support.

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

These local schedules produce 128 runs per neighborhood and 512 inexpensive
candidate calls total:

| Condition | Runs per neighborhood |
|---|---:|
| Balanced | 8 |
| Imbalanced | 24 |
| Singleton | 48 |
| Dense and singleton | 48 |

For each `s`, also form one **combined balanced** 48-vector run by taking the
union of that schedule's four local balanced runs. These eight runs expose the
exact same local vectors in the presence of the other three semantic areas.

The complete protocol therefore makes 520 candidate calls per frozen candidate
and seed: 512 local allocation calls plus eight combined balanced calls. The 96
SSE vectors are generated once. No candidate run re-encodes text.

## Blinding and run isolation

After the final fixture is frozen and before any candidate run:

1. map every human-readable fixture ID to a frozen random opaque ID;
2. assign every opaque ID one frozen random global rank;
3. order every local or combined run by filtering the global master rank order.

The candidate receives no condition name, role, support count, subject name, or
human-readable ID. Dense, rare, and singleton vectors are never deliberately
placed in contiguous blocks.

Freeze one random execution order over all 520 run specifications. Every run
starts from the same fresh candidate state and declared seed. No run can train
or prime another run.

This experiment uses one frozen within-run order and therefore requires the
candidate either to be permutation-invariant by construction or to have passed
Experiment 6's input-order stability check. Otherwise the results are not
interpretable; do not duplicate that separate test by adding ad hoc order
variants here.

## Evaluation

This is a characterization experiment, not an all-runs-must-pass test. The
balanced local runs establish the behavior that the two later comparisons may
change. The declared subjects are reference cohorts, not prescribed segment
boundaries.

For each run, record these separate outcomes:

1. **Reference-cohort recovery:** for each declared subject with at least two present
   vectors, whether one segment contains all of them and no vector from another
   declared subject.
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
overlapping subjects that differ from the declared reference cohorts. Review
each unique
cross-subject member set with its run, condition, support roles, fixture IDs,
and declared subjects hidden. Show only its complete masks under neutral labels
and ask:

> What is the narrowest recognizable subject for which every instance is a
> valid refinement?

Freeze one random instance order for each unique member set. The reviewer must
either supply that subject or record `no valid fine subject`.

The neighborhood umbrella alone—`coffee processing`, `photograph editing`,
`rose-bush care`, or `software development`—is too broad to validate a fine
segment. Record `invalid cross-subject membership` when no more specific valid
fine subject covers every member. When an invalid member set contains a rare or
singleton vector, additionally record `false absorption`; this does not assert
which vector entered which pre-existing segment. Review an identical member set
once and reuse that frozen judgment wherever it recurs.

This review is metadata-blind, not source-blind: the synthetic wording may be
recognizable. Declared-cohort recovery and alternative semantic validity remain
separate measurements. An accepted alternative segment never changes the
declared allocation used to describe that run.

### Balanced local organization

For the 32 balanced local runs, preserve every returned member set and the
metadata-blind semantic judgment above. Describe whether the candidate tends to
recover the three declared cohorts, combine nearby cohorts into valid broader
fine subjects, fragment them, overlap them, or omit vectors. No one of those
shapes is declared correct in advance.

### Local versus combined balanced organization

For each neighborhood and schedule `s`, compare its local balanced output with
the combined balanced output for the same `s`:

1. project each combined-output segment onto that neighborhood's twelve IDs;
2. compare the resulting nonempty member sets with the local output's member
   sets;
3. separately preserve every combined-output segment that crosses semantic
   neighborhoods.

Projection shows whether the local organization changed. The separate
cross-neighborhood record prevents projection from hiding contamination. This
comparison uses identical local vectors, schedule indices, and relative order;
only the other three balanced neighborhoods were added.
Retain the source combined segment for every projection; do not deduplicate
identical projected member sets.

### Balanced versus unequal support

For every neighborhood, schedule `s`, and role assignment, pair the unequal
run with that neighborhood's balanced run for the same `s`. Record:

1. the IDs shared by the two inputs;
2. each run's complete output;
3. both outputs projected onto the shared IDs;
4. the exact set difference between those projected member-set collections;
5. the ordinary semantic review of every new cross-subject member set.

Retain the source segment for every projection and treat projected outputs as
source-linked lists; never deduplicate identical projected member sets.

Analysts may describe a change as a gain, loss, split, merge, omission, or
absorption, but those are qualitative annotations. The preserved inputs,
outputs, projections, and exact set difference are the authoritative record.

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
schedule as a repeated block; do not treat the 520 overlapping runs as 520
independent samples. Do not average away a neighborhood-specific failure. Raw
cosine and lexical measurements are diagnostics, not semantic verdicts.

## Protocol

1. Audit every mask against its declared atomic subject. Correct any missing
   subject evidence, extra substantive meaning, or narrower qualification.
2. Counterbalance the eight wording forms inside every neighborhood and across
   the combined run.
   Correct clear incidental-template imbalances without purging necessary
   subject words or forcing unnatural synonyms.
3. Obtain human approval of all 96 notes, masks, atomic propositions, and the
   intended nearby relationships.
4. Freeze the fixture wording before encoding or inspecting candidate output.
5. Freeze the SSE contract, candidate source and build, preprocessing,
   configuration, fine-output selector, seed, and diagnostics.
6. Encode the 96 inputs once, then freeze the vector bytes, opaque-ID mapping,
   global master rank, all 520 run specifications, and randomized run order.
7. Execute every run from fresh candidate state without retuning or
   re-encoding, and preserve every output before restoring fixture identities.
8. Compute the frozen representation and lexical diagnostics.
9. Complete the metadata-blind semantic reviews, local-versus-combined
   comparisons, and matched support-allocation comparisons.

## Required record

Preserve:

- every complete note, mask, raw vector, and artifact hash;
- the atomic-subject equivalence audit for every mask;
- every numeric schedule index, subject phase, wording form, and recorded
  structural attribute;
- the opaque-ID mapping and global master rank order;
- the frozen execution order and every run’s condition, roles, schedule, exact
  inputs, and candidate order;
- every complete returned segment, overlap, singleton, and omission;
- reference-cohort recovery, all cross-subject memberships, false absorption,
  omission, fragmentation, extra segments, and singleton disposition fields;
- every blind-review judgment and the masks supporting it;
- every local-versus-combined projection and cross-neighborhood segment;
- every balanced-versus-unequal shared-ID projection and membership change;
- the immutable raw-vector cosine matrix and all lexical diagnostics;
- candidate source, build, configuration, preprocessing, selector, and seed
  hashes.

## What a result means

The result describes how one frozen SSE-plus-segmentation system organizes four
controlled collections of nearby subjects under balanced support, whether that
organization changes when unrelated neighborhoods are present, and how it
changes under the complete unequal-support and singleton allocations. It does
not attribute those changes to support count alone.

Evidence is stronger when declared cohorts that recover under balanced support
continue to recover under stress allocations without new invalid membership,
omission, or fragmentation involving low-support vectors. The document does
not impose one binary threshold; it preserves the full failure profile for
candidate comparison and later threshold selection.

It does not establish one universally correct fine-subject boundary,
production-scale behavior, every geometric density pattern, natural-corpus
mask quality, or hierarchy quality. The combined run is one controlled global
composition check; Experiment 6 separately tests broader irrelevant-change
stability.
