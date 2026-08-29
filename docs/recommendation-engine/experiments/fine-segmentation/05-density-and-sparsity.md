# Experiment 5: unequal subject support and sparsity

Status: **draft; every note, mask, subject identity, and expected relationship
requires human approval before encoding**.

## Assumption under test

> Region recovery survives unequal density and sparsity.

This experiment operationalizes density as the number of distinct vectors
supporting one subject inside a fixed-size local collection. It tests unequal
subject support and singleton sparsity. It does not claim to manipulate every
possible geometric notion of density.

## Question

> Holding the collection size at twelve vectors, how does changing subject
> support from `4:4:4` to `8:2:2`, `6:5:1`, or `8:3:1` change recovery,
> absorption, omission, and fragmentation?

## Design

The fixture contains four independent semantic neighborhoods:

1. processing coffee beans;
2. editing photographs;
3. caring for rose bushes;
4. developing software.

Each neighborhood contains three nearby but meaningfully different atomic
subjects, with eight independently worded instances per subject. This gives 24
vectors per neighborhood and 96 vectors total.

Each candidate run contains vectors from one neighborhood only. Experiment 6
separately tests mixing unrelated semantic areas.

Every complete note is also its complete mask. The formulations avoid aligned
sentence templates across sibling subjects. Shared words remain only where they
directly express the subject.

Because every run contains twelve vectors, these are complete support
**allocations**: increasing one subject's support necessarily reduces another's.
The experiment compares behavior under each allocation. It does not claim to
identify the independent causal effect of one subject's support count.

## Fixture

### Coffee processing

#### `COFFEE-R`: roasting green coffee beans

| ID | Complete note and exact mask |
|---|---|
| `COFFEE-R1` | ⟦I’m roasting green coffee beans.⟧ |
| `COFFEE-R2` | ⟦Green coffee beans are turning brown under roasting heat.⟧ |
| `COFFEE-R3` | ⟦I put unroasted coffee beans through a roast.⟧ |
| `COFFEE-R4` | ⟦The green beans in my coffee roaster are being roasted.⟧ |
| `COFFEE-R5` | ⟦A batch of green coffee beans is going through the roasting process.⟧ |
| `COFFEE-R6` | ⟦I’ve got raw coffee beans roasting.⟧ |
| `COFFEE-R7` | ⟦Heat is roasting these unroasted coffee beans.⟧ |
| `COFFEE-R8` | ⟦The beans I roasted were green coffee beans.⟧ |

#### `COFFEE-G`: grinding roasted coffee beans

| ID | Complete note and exact mask |
|---|---|
| `COFFEE-G1` | ⟦I grind roasted coffee beans.⟧ |
| `COFFEE-G2` | ⟦Roasted coffee beans are going through the grinder.⟧ |
| `COFFEE-G3` | ⟦The grinder is reducing roasted beans into coffee grounds.⟧ |
| `COFFEE-G4` | ⟦It’s roasted coffee beans that I’m grinding.⟧ |
| `COFFEE-G5` | ⟦I’ve ground the roasted coffee beans.⟧ |
| `COFFEE-G6` | ⟦The roasted beans are being milled into grounds.⟧ |
| `COFFEE-G7` | ⟦I’m breaking roasted coffee beans into smaller particles with a grinder.⟧ |
| `COFFEE-G8` | ⟦I reduced roasted coffee beans to grounds.⟧ |

#### `COFFEE-E`: extracting espresso

| ID | Complete note and exact mask |
|---|---|
| `COFFEE-E1` | ⟦I pulled a shot of espresso.⟧ |
| `COFFEE-E2` | ⟦Pressurized water is extracting coffee from fine grounds into a small shot.⟧ |
| `COFFEE-E3` | ⟦Espresso is being extracted.⟧ |
| `COFFEE-E4` | ⟦What I’m pulling from the machine is espresso.⟧ |
| `COFFEE-E5` | ⟦I extracted the espresso.⟧ |
| `COFFEE-E6` | ⟦The espresso machine is extracting a concentrated shot of espresso.⟧ |
| `COFFEE-E7` | ⟦The machine is pulling espresso from compacted grounds.⟧ |
| `COFFEE-E8` | ⟦I am making espresso by pressure-extracting coffee grounds.⟧ |

### Photograph editing

#### `PHOTO-C`: cropping a photograph

| ID | Complete note and exact mask |
|---|---|
| `PHOTO-C1` | ⟦I cropped the photograph.⟧ |
| `PHOTO-C2` | ⟦The picture has been cropped.⟧ |
| `PHOTO-C3` | ⟦We changed the crop on this photo.⟧ |
| `PHOTO-C4` | ⟦She trimmed the image.⟧ |
| `PHOTO-C5` | ⟦This photograph is being cropped.⟧ |
| `PHOTO-C6` | ⟦He adjusted the picture’s crop.⟧ |
| `PHOTO-C7` | ⟦I am trimming the photo.⟧ |
| `PHOTO-C8` | ⟦They made a crop adjustment to the image.⟧ |

#### `PHOTO-A`: adjusting a photograph’s colors

| ID | Complete note and exact mask |
|---|---|
| `PHOTO-A1` | ⟦I changed the picture’s color balance.⟧ |
| `PHOTO-A2` | ⟦I am tuning the colors in this photograph.⟧ |
| `PHOTO-A3` | ⟦I’m applying color correction to this image.⟧ |
| `PHOTO-A4` | ⟦Editing altered this picture’s colors.⟧ |
| `PHOTO-A5` | ⟦The hues in this image are being adjusted.⟧ |
| `PHOTO-A6` | ⟦I color-graded the photo.⟧ |
| `PHOTO-A7` | ⟦The photograph underwent a color adjustment.⟧ |
| `PHOTO-A8` | ⟦Color editing changed the photo.⟧ |

#### `PHOTO-S`: straightening a tilted photograph

| ID | Complete note and exact mask |
|---|---|
| `PHOTO-S1` | ⟦Correcting its tilt brought this picture level.⟧ |
| `PHOTO-S2` | ⟦The picture is now straight after I corrected its tilt.⟧ |
| `PHOTO-S3` | ⟦They are straightening a crooked image.⟧ |
| `PHOTO-S4` | ⟦I took the tilt out of the photograph.⟧ |
| `PHOTO-S5` | ⟦I leveled the picture by correcting its slant.⟧ |
| `PHOTO-S6` | ⟦Straightening removed the photograph’s tilt.⟧ |
| `PHOTO-S7` | ⟦Rotation brought this tilted photograph back to level.⟧ |
| `PHOTO-S8` | ⟦Leveling removed the slant from this photo.⟧ |

### Rose-bush care

#### `ROSE-P`: pruning a rose bush

| ID | Complete note and exact mask |
|---|---|
| `ROSE-P1` | ⟦I pruned the rose bush.⟧ |
| `ROSE-P2` | ⟦I gave the rose bush a trim.⟧ |
| `ROSE-P3` | ⟦The rose bush got pruned.⟧ |
| `ROSE-P4` | ⟦I cut back a rose bush.⟧ |
| `ROSE-P5` | ⟦I did some pruning on the rose bush.⟧ |
| `ROSE-P6` | ⟦The bush I trimmed was a rose bush.⟧ |
| `ROSE-P7` | ⟦I was the one who pruned the rose bush.⟧ |
| `ROSE-P8` | ⟦What I cut back was the rose bush.⟧ |

#### `ROSE-W`: watering a rose bush

| ID | Complete note and exact mask |
|---|---|
| `ROSE-W1` | ⟦I watered the rose bush.⟧ |
| `ROSE-W2` | ⟦The rose bush received watering.⟧ |
| `ROSE-W3` | ⟦I supplied water to a rose bush.⟧ |
| `ROSE-W4` | ⟦Watering is underway for the rose bush.⟧ |
| `ROSE-W5` | ⟦A rose bush is being irrigated.⟧ |
| `ROSE-W6` | ⟦I irrigated the rose bush.⟧ |
| `ROSE-W7` | ⟦The watering I did was for a rose bush.⟧ |
| `ROSE-W8` | ⟦This rose bush has been watered.⟧ |

#### `ROSE-F`: fertilizing a rose bush

| ID | Complete note and exact mask |
|---|---|
| `ROSE-F1` | ⟦Fertilizer now feeds my rose bush.⟧ |
| `ROSE-F2` | ⟦My rose bush got a dose of plant nutrients.⟧ |
| `ROSE-F3` | ⟦Feeding the rose bush required adding fertilizer.⟧ |
| `ROSE-F4` | ⟦The fertilizer went onto my rose bush.⟧ |
| `ROSE-F5` | ⟦Plant food is nourishing this rose bush.⟧ |
| `ROSE-F6` | ⟦Fertilizer application is complete for the rose bush.⟧ |
| `ROSE-F7` | ⟦I treated the rose bush with plant nutrients.⟧ |
| `ROSE-F8` | ⟦Adding nutrients fertilized my rose bush.⟧ |

### Software development

#### `SOFTWARE-C`: compiling source code

| ID | Complete note and exact mask |
|---|---|
| `SOFTWARE-C1` | ⟦The compiler is processing my source code.⟧ |
| `SOFTWARE-C2` | ⟦I’m compiling the program from source.⟧ |
| `SOFTWARE-C3` | ⟦My source files are being passed through the compiler.⟧ |
| `SOFTWARE-C4` | ⟦The program’s source is undergoing compilation.⟧ |
| `SOFTWARE-C5` | ⟦I’m putting the source code through a compiler.⟧ |
| `SOFTWARE-C6` | ⟦I’ve run the program’s source files through a compiler.⟧ |
| `SOFTWARE-C7` | ⟦The source code is in the process of being compiled.⟧ |
| `SOFTWARE-C8` | ⟦I compiled the program’s source.⟧ |

#### `SOFTWARE-T`: running automated software tests

| ID | Complete note and exact mask |
|---|---|
| `SOFTWARE-T1` | ⟦I kicked off the software’s automated test suite.⟧ |
| `SOFTWARE-T2` | ⟦Automated test cases are running against the program.⟧ |
| `SOFTWARE-T3` | ⟦I have the software going through its automated tests.⟧ |
| `SOFTWARE-T4` | ⟦The program is being tested automatically.⟧ |
| `SOFTWARE-T5` | ⟦I’m executing the automated software tests.⟧ |
| `SOFTWARE-T6` | ⟦The software’s test suite is running automatically.⟧ |
| `SOFTWARE-T7` | ⟦An automated test run is under way for the program.⟧ |
| `SOFTWARE-T8` | ⟦I ran the software’s automated test suite.⟧ |

#### `SOFTWARE-D`: debugging a program

| ID | Complete note and exact mask |
|---|---|
| `SOFTWARE-D1` | ⟦I’m investigating a defect in the program.⟧ |
| `SOFTWARE-D2` | ⟦I’m tracing bugs through the program.⟧ |
| `SOFTWARE-D3` | ⟦I’ve got a program that I’m debugging.⟧ |
| `SOFTWARE-D4` | ⟦Debugging is what I’m doing with the program.⟧ |
| `SOFTWARE-D5` | ⟦I’m working the bugs out of the program.⟧ |
| `SOFTWARE-D6` | ⟦I have been debugging the program.⟧ |
| `SOFTWARE-D7` | ⟦I’m doing some debugging on a program.⟧ |
| `SOFTWARE-D8` | ⟦I debugged the program.⟧ |

The subject names and human-readable IDs are scoring data. The candidate never
receives them.

## Neighborhood eligibility

Human semantic proximity does not prove proximity in the frozen SSE geometry.
During fixture development, before any segmentation output exists, rank every
provisional vector against the other 23 vectors in its neighborhood by raw
cosine similarity.

A neighborhood is eligible only when, for each of its three subjects, at least
two of the eight vectors have a different-subject vector among their seven
nearest neighbors. Seven is used because each vector has exactly seven
same-subject peers. This requires cross-subject proximity to displace at least
one same-subject peer and prevents one isolated outlier from qualifying an
otherwise trivial neighborhood.

This screen excludes an obviously separated neighborhood; it does not prove
that every subject pair or every scheduled run is difficult. Preserve the
cross-subject neighbor ranks for each run as diagnostics. Cosine does not
determine the returned segments or their verdicts.

The SSE contract, segmentation candidate, and eligibility rule are frozen
before this screen. If a provisional neighborhood is ineligible, replace and
rescreen it without changing those frozen components. Only the final eligible,
human-approved 96-vector fixture enters the experiment.

## Fixed support conditions

Every candidate run contains exactly twelve vectors:

| Condition | Support | Primary contrast |
|---|---:|---|
| Balanced | `4:4:4` | Equal-support control |
| Imbalanced | `8:2:2` | One common subject and two rare repeated subjects |
| Singleton | `6:5:1` | One unmatched instance with two similarly supported subjects |
| Combined | `8:3:1` | A common subject, a rare repeated subject, and a singleton |

The `6:5:1` condition runs both orders of the recurring subjects. The one-vector
role is the only intentionally unmatched subject.

## Frozen formulation schedule

Number each subject’s formulations `1` through `8`. For start index `s` and
length `k`, let `W(k, s)` be the `k` consecutive indices beginning at `s`,
wrapping after `8`. For example:

```text
W(3, 7) = {7, 8, 1}
```

Run every condition for `s = 1 ... 8`:

- Balanced: the three subjects use `W(4, s)`, `W(4, s+2)`, and `W(4, s+4)`.
- Imbalanced: each subject takes one turn as the eight-vector subject; the
  other two use `W(2, s)` and `W(2, s+4)` in fixed subject order.
- Singleton: run all six ordered assignments to the `6`, `5`, and `1` roles,
  using `W(6, s)`, `W(5, s+2)`, and `{s+4}` respectively.
- Combined: run all six ordered assignments to the `8`, `3`, and `1` roles,
  using all eight vectors, `W(3, s)`, and `{s+4}` respectively.

All index arithmetic wraps into `1 ... 8`. Across the eight schedules, every
formulation appears equally often in each role that its subject occupies.
Subject order means the order in which the three subject cohorts appear in the
fixture. The cyclic blocks provide controlled wording coverage; they are not
independent statistical replicates and do not exhaust every possible subset.

This produces 128 runs per neighborhood and 512 inexpensive FSA calls total:

| Condition | Runs per neighborhood |
|---|---:|
| Balanced | 8 |
| Imbalanced | 24 |
| Singleton | 48 |
| Combined | 48 |

The final 96 SSE vectors are generated once. No candidate run re-encodes text.

## Blinding and run isolation

After the final fixture is frozen and before any candidate run:

1. map every human-readable fixture ID to a frozen random opaque ID;
2. assign every opaque ID one frozen random rank within its neighborhood;
3. order each run by filtering the neighborhood’s master rank order.

The candidate receives no condition name, role, support count, subject name, or
human-readable ID. Dense, rare, and singleton vectors are never deliberately
placed in contiguous blocks.

Freeze one random execution order over all 512 run specifications. Every run
starts from the same fresh candidate state and declared seed. No run can train
or prime another run.

This experiment uses one frozen within-run order and therefore requires the
candidate either to be permutation-invariant by construction or to have passed
Experiment 6's input-order stability check. Otherwise Experiment 5 is not
interpretable; do not duplicate that separate test by adding ad hoc order
variants here.

## Evaluation

This is a characterization experiment, not an all-runs-must-pass test. Its unit
of comparison is a complete support allocation, not one support count in
isolation.

For each run, record these separate outcomes:

1. **Reference recovery:** for each declared subject with at least two present
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

A segment spanning declared subjects does not count as reference recovery, but
it is not automatically invalid: the candidate may return overlapping subjects
that differ from the declared reference cohorts. Review each unique
cross-subject member set with its run, condition, support roles, fixture IDs,
and declared subjects hidden. Show only its complete masks under neutral labels
and ask:

> What is the narrowest recognizable subject for which every instance is a
> valid refinement?

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

Compare outcome rates by neighborhood, declared subject, support count, role,
allocation, and formulation schedule. Report every schedule and aggregate only
with schedule as a repeated block; do not treat the 512 overlapping runs as 512
independent samples. Do not average away a neighborhood-specific failure. The
fixed raw-vector cosine matrix is diagnostic evidence, not the verdict.

## Protocol

1. Obtain provisional human approval of all 96 notes, masks, subject
   identities, nearby relationships, and wording independence.
2. Freeze the SSE contract, candidate source and build, preprocessing,
   configuration, fine-output selector, seed, and eligibility rule.
3. Encode and screen the provisional neighborhoods. Replace and rescreen an
   ineligible neighborhood without changing the frozen system. Rejected
   provisional vectors are development artifacts, not experiment inputs.
4. Obtain final human approval, then freeze this document, the final 96 vector
   bytes, opaque-ID mapping, master ranks, and randomized run order.
5. Execute every run from fresh candidate state without retuning or
   re-encoding, and preserve every output before restoring fixture identities.
6. Score all allocations. Balanced outcomes establish the reference behavior;
   they do not gate execution or create an exact counterfactual for a stress
   run. Do not attribute a difference solely to one support count.
7. Complete the metadata-blind reviews and condition comparisons.

## Required record

Preserve:

- every complete note, mask, raw vector, and artifact hash;
- every provisional eligibility result and replacement;
- the opaque-ID mapping and master rank order;
- the frozen execution order and every run’s condition, roles, schedule, exact
  inputs, and candidate order;
- every complete returned segment, overlap, singleton, and omission;
- reference recovery, all cross-subject memberships, false absorption,
  omission, fragmentation, extra segments, and singleton disposition fields;
- every blind-review judgment and the masks supporting it;
- the immutable raw-vector cosine matrix;
- candidate source, build, configuration, preprocessing, selector, and seed
  hashes.

## What a result means

The result describes how one frozen SSE-plus-segmentation system responds to
subject-support imbalance and singleton sparsity across four controlled local
semantic neighborhoods.

Evidence is stronger when declared cohorts that recover under balanced support
continue to recover under stress allocations without new invalid membership,
omission, or fragmentation involving low-support vectors. The document does
not impose one binary threshold; it preserves the full failure profile for
candidate comparison and later threshold selection.

It does not establish production-scale behavior, every geometric density
pattern, natural-corpus mask quality, mixed-area stability, or hierarchy
quality.
