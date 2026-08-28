# Experiment 2: nearby fine-subject resolution

Status: **draft; notes, masks, and expected relationships require human
approval before encoding**.

## Assumption under test

> Nearby but meaningfully distinct fine subjects are resolved.

In particular:

- instances that are similar enough to express the same fine subject should be
  grouped;
- instances that are distinct enough to represent different fine subjects
  should remain separate.

## Question

Can one frozen candidate recover repeated subjects while preserving two
predeclared, close-sibling boundaries?

## Why this fixture exists

The phrases “similar enough” and “distinct enough” have no universal numeric
definition. This experiment makes two concrete human judgments before vectors
exist:

- roasting coffee beans is a different fine subject from grinding them;
- tuning existing guitar strings is a different fine subject from replacing
  them.

Using two semantic areas prevents one vocabulary family from determining the
result. Each fine subject has three independent formulations so the candidate
must both recover recurrence and preserve the boundary.

## Synthetic notes and masks

### Coffee preparation

#### Subject `ROAST`: roasting coffee beans

**ROAST-1**

> I ⟦roasted green coffee beans⟧ in a small drum machine.

**ROAST-2**

> The garage smelled incredible while I ⟦roasted a batch of green coffee beans
> in a drum roaster⟧.

**ROAST-3**

> Rather than buying finished beans, we ⟦roasted our own batch of coffee
> beans⟧.

#### Subject `GRIND`: grinding coffee beans

**GRIND-1**

> Right before brewing, I ⟦ground the roasted coffee beans⟧.

**GRIND-2**

> The burr mill hummed as I ⟦reduced roasted coffee beans to grounds⟧.

**GRIND-3**

> For tomorrow's pot, we ⟦milled roasted beans into coarse coffee particles⟧.

### Guitar maintenance

#### Subject `TUNE`: tuning guitar strings

**TUNE-1**

> Before rehearsal, I ⟦tuned the guitar strings to standard pitch⟧.

**TUNE-2**

> The instrument sounded flat, so I ⟦adjusted each guitar string until it was
> in tune⟧.

**TUNE-3**

> Using a tuning fork, she ⟦brought all six guitar strings to the correct
> pitch⟧.

#### Subject `RESTRING`: replacing guitar strings

**RESTRING-1**

> Before rehearsal, I ⟦replaced all six strings on the guitar⟧.

**RESTRING-2**

> One string snapped, so I ⟦put a fresh set of strings on the guitar⟧.

**RESTRING-3**

> The old set had corroded, and I ⟦restrung the guitar with new strings⟧.

The subject identities and boundaries are scoring data. The candidate does not
receive them.

## Frozen hypothesis

1. Each of the four three-vector subjects will appear as one complete fine
   segment with no member of another subject.
2. No `ROAST` vector will share a fine segment with a `GRIND` vector.
3. No `TUNE` vector will share a fine segment with a `RESTRING` vector.
4. No coffee vector will share a fine segment with a guitar vector.

The first condition tests grouping at the chosen resolution. The remaining
conditions test separation at that same resolution.

The coffee-versus-guitar condition is a coarse anti-collapse control. Evidence
about nearby-subject resolution comes specifically from `ROAST` versus `GRIND`
and `TUNE` versus `RESTRING`.

## Frozen system boundary

Use the shared 768-dimensional Sentence-T5-base SSE checkpoint identified in:

README.md

Preserve its raw outputs exactly. Any normalization, distance, or other
preprocessing belongs to the candidate's frozen configuration.

The candidate receives only opaque IDs and vectors. It may return overlapping
fine segments and leave vectors unassigned. Scoring consumes only the
candidate's predeclared fine-segment collection, represented as sets of opaque
IDs. Coarser parent regions are excluded.

This is a visible development fixture, not held-out confirmation.

## Protocol

1. Obtain human approval of every note, mask, subject identity, and declared
   boundary.
2. Freeze this document and the candidate's implementation, preprocessing,
   configuration, fine-output selection rule, and seed.
3. Generate the twelve SSE vectors once and preserve their exact bytes.
4. Give the candidate only opaque vector IDs and the vectors in one frozen
   shuffled order.
5. Preserve the complete returned fine-segment collection.
6. Reveal the fixture identities and score every declared relationship.
7. Display every failed relationship with both full notes, both masks, every
   connecting segment, and the cosine between the vectors.

## Scoring definitions

Two vectors **share** when at least one returned fine segment contains both.

A subject is **cleanly recovered** when one segment contains all three of its
vectors and no vector belonging to another declared subject. Pairwise chains
without one complete segment do not count.

A **false split** is a same-subject pair that shares no segment. A **false
merge** is a different-subject pair that shares a segment.

## Pass rule

The experiment passes only with:

```text
clean subject recoveries: 4 of 4
ROAST versus GRIND false merges: 0 of 9 pairs
TUNE versus RESTRING false merges: 0 of 9 pairs
coarse coffee-versus-guitar merges: 0
```

Clean recovery already implies zero within-subject false splits. The pair count
is retained as a diagnostic rather than a redundant pass condition. One error
fails the controlled experiment. False splits, close-sibling false merges, and
coarse anti-collapse failures must be reported separately; averaging them
would hide whether the selected resolution is too fine or too coarse.

## Required record

Preserve:

- clean recovery for every subject;
- every false split and false merge;
- all segment memberships, including overlaps and omissions;
- segment counts and sizes;
- the exact shuffled input order;
- the cosine matrix and nearest-neighbor order computed from immutable raw SSE
  outputs;
- the raw SSE artifact and hashes;
- the complete candidate configuration and seed.

Cosine is diagnostic evidence, not the pass criterion.

## What a result means

A pass supports only the two human-approved sibling boundaries in this
fixture. It does not define one global meaning of “similar enough,” prove the
full attainable resolution, or establish later hierarchy quality.

The aligned action words also make this a relatively easy nearby-subject test.
A pass does not establish that the candidate relied on semantic structure
rather than lexical cues; Experiment 3 tests that separately.

A failure shows where this frozen system loses one of the declared boundaries.
It does not, by itself, attribute the problem to SSE or the candidate
segmentation procedure.
