# Experiment 5: unequal density and sparsity

Status: **draft; notes, masks, and expected relationships require human
approval before encoding**.

## Assumption under test

> Region recovery survives unequal density and sparsity.

In particular, a rare repeated subject must not disappear into a common nearby
subject, and one unmatched subject instance must not be forced into an
incorrect recurring segment.

## Question

After one frozen candidate recovers three nearby subjects under equal support,
does changing which frozen instances remain—and therefore each subject's
density—cause incorrect splits or merges?

## Why this fixture exists

All three subjects are stages of coffee preparation, making density pressure
meaningful rather than trivial:

- roasting coffee beans;
- grinding coffee beans;
- extracting espresso.

Each subject has six frozen formulations. SSE runs only once. The
experiment then presents different subsets of those same frozen vectors to the
same candidate. No note, mask, vector, candidate setting, or preprocessing
changes between runs.

## Synthetic notes and masks

Every note uses the same neutral carrier. Only the masked subject phrase
changes.

### Subject `R`: roasting coffee beans

**R1**

> This note concerns ⟦roasting green coffee beans⟧.

**R2**

> This note concerns ⟦coffee-bean roasting⟧.

**R3**

> This note concerns ⟦turning green coffee beans into roasted coffee⟧.

**R4**

> This note concerns ⟦home-roasting a batch of coffee beans⟧.

**R5**

> This note concerns ⟦heating green coffee beans through a full roast cycle⟧.

**R6**

> This note concerns ⟦roasting unprocessed coffee beans until browned and
> aromatic⟧.

### Subject `G`: grinding coffee beans

**G1**

> This note concerns ⟦grinding roasted coffee beans⟧.

**G2**

> This note concerns ⟦crushing roasted coffee beans in a burr grinder⟧.

**G3**

> This note concerns ⟦turning roasted coffee beans into coffee grounds⟧.

**G4**

> This note concerns ⟦grinding beans for coffee brewing⟧.

**G5**

> This note concerns ⟦grinding a batch of whole roasted coffee beans⟧.

**G6**

> This note concerns ⟦reducing roasted coffee beans to coarse grounds⟧.

### Subject `E`: extracting espresso

**E1**

> This note concerns ⟦extracting espresso under pressure⟧.

**E2**

> This note concerns ⟦pulling an espresso shot⟧.

**E3**

> This note concerns ⟦forcing hot water through fine coffee grounds to make
> espresso⟧.

**E4**

> This note concerns ⟦brewing espresso with a pressurized machine⟧.

**E5**

> This note concerns ⟦extracting a shot of espresso from compacted grounds⟧.

**E6**

> This note concerns ⟦making espresso by pressurized extraction⟧.

The three subject identities are scoring data. The candidate does not receive
them.

## Frozen hypothesis

1. With six vectors from every subject, all three subjects will be cleanly
   recovered and remain separate.
2. With support changed to `6:2:1`, the six-vector subject and the two-vector
   subject will each remain cleanly recovered.
3. The one unmatched vector will share no fine segment with either recurring
   subject.
4. The result will hold regardless of which subject is dense, rare, or
   unmatched and regardless of which wording supplies the rare pair or
   singleton.

A currently present subject is **cleanly recovered** when one returned segment
contains every currently present vector from that subject and no vector from
another declared subject. The candidate may return overlapping segments and
leave vectors unassigned, but no returned fine segment may cross a declared
subject boundary.

## Frozen system boundary

Use the shared 768-dimensional Sentence-T5-base SSE checkpoint identified in
the [suite index](README.md). Preserve its raw outputs exactly. Any
normalization, distance, or other preprocessing belongs to the candidate's
frozen configuration.

The candidate receives only opaque IDs and vectors. Scoring consumes only its
predeclared fine-segment collection; coarser parents are excluded.

This is a visible development fixture, not held-out confirmation.

## Protocol

1. Obtain human approval of all eighteen notes, masks, subject identities, and
   expected boundaries.
2. Freeze this document and the candidate's implementation, preprocessing,
   configuration, fine-output rule, and seed.
3. Generate all eighteen SSE vectors once and preserve their exact bytes.
4. Run the balanced baseline.
5. If the baseline fails, record that prerequisite failure and stop. The
   candidate did not recover the subjects before density changed, so this
   fixture cannot attribute the failure to unequal density.
6. If the baseline passes, run all 540 frozen `6:2:1` variants below without
   retuning or re-encoding.
7. Preserve and score every returned fine-segment collection separately. Do
   not average failures away.

## Balanced baseline

The baseline contains all eighteen vectors:

```text
R1 R2 R3 R4 R5 R6
G1 G2 G3 G4 G5 G6
E1 E2 E3 E4 E5 E6
```

It passes only when each six-vector subject is cleanly recovered and no segment
contains vectors from two subjects.

## The 540 skewed runs

Every skewed run has:

- every vector from one **dense** subject;
- one of the fifteen possible two-vector subsets from one **rare** subject;
- one of the six vectors from the **unmatched** subject.

Run all six assignments of `R`, `G`, and `E` to the three roles:

| Assignment | Dense | Rare | Unmatched |
|---|---|---|---|
| A1 | `R1–R6` | `G` | `E` |
| A2 | `R1–R6` | `E` | `G` |
| A3 | `G1–G6` | `R` | `E` |
| A4 | `G1–G6` | `E` | `R` |
| A5 | `E1–E6` | `R` | `G` |
| A6 | `E1–E6` | `G` | `R` |

Within each assignment, enumerate:

1. every rare pair `(i, j)` for `1 <= i < j <= 6`;
2. every unmatched index `k` from `1` through `6`.

That gives `15 × 6 = 90` runs per role assignment and `6 × 90 = 540`
runs total.

The exact candidate input order in every run is:

1. all six dense IDs in ascending numeric order;
2. the two rare IDs in ascending numeric order;
3. the unmatched ID last.

For example:

```text
A1 / pair 1,2 / singleton 1:
R1 R2 R3 R4 R5 R6 G1 G2 E1

A2 / pair 2,5 / singleton 6:
R1 R2 R3 R4 R5 R6 E2 E5 G6

A6 / pair 5,6 / singleton 4:
E1 E2 E3 E4 E5 E6 G5 G6 R4
```

This exhausts every assignment of subjects to roles, every possible rare pair,
and every possible unmatched wording. These runs are cheap FSA calls over nine
already-generated vectors; they do not rerun SSE.

## Pass rule for one skewed run

A skewed run passes only when:

1. one segment contains all six dense vectors and no other subject;
2. one segment contains both rare vectors and no other subject;
3. no segment contains vectors from two declared subjects;
4. the unmatched vector shares no fine segment with any other vector.

The complete experiment passes only if the balanced baseline and all 540
skewed runs pass.

## Required record

For every run, preserve:

- the exact input IDs and order;
- every returned segment, overlap, and omission;
- dense- and rare-subject recovery;
- every cross-subject membership;
- whether the unmatched vector was absorbed;
- whether the exact rare pair belonged to the correct six-member segment in
  the balanced baseline but failed when only that pair remained;
- the fixed cosine matrix for all eighteen immutable raw SSE outputs;
- the candidate configuration and seed;
- the raw SSE artifact and hashes.

For a failure, show whether the same vectors were correctly grouped in the
balanced baseline. Cosine is diagnostic evidence, not the pass rule.

## What a result means

A pass supports the specific claim that changing support from balanced `6:6:6`
to all tested `6:2:1` views did not destroy these nearby coffee-preparation
subjects or absorb the unmatched instance.

It does not establish production-scale density behavior, every real frequency
ratio, how unmatched vectors should later be surfaced, automatic mask quality,
or hierarchy quality.
