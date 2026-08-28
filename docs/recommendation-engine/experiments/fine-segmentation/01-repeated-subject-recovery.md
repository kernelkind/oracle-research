# Experiment 1: repeated fine-subject recovery

Status: **draft; notes, masks, and expected relationships require human
approval before encoding**.

## Assumption under test

> Repeated instances of the same fine subject form recoverable groups.

## Question

Can one frozen fine-segmentation candidate recover a complete segment from
three differently worded vectors representing the same fine subject?

## Why this fixture exists

A pair could match accidentally. Three instances require a recurring group.
Two unrelated subjects prevent a candidate from passing by putting every input
in one segment.

The fixture therefore contains two subjects with three independently worded
instances each: six vectors total. Every note uses a simple carrier so this
experiment does not intentionally vary surrounding context. This is an easy
recurrence control: its subjects retain recognizable shared vocabulary. It
does not independently establish that grouping is semantic rather than
lexical; Experiment 3 tests that separately.

## Synthetic notes and masks

### Subject `STARTER`: feeding a sourdough starter

**STARTER-1**

> This note concerns ⟦feeding a sourdough starter with fresh flour and water⟧.

**STARTER-2**

> This note concerns ⟦refreshing a sourdough starter with fresh flour and
> water⟧.

**STARTER-3**

> This note concerns ⟦adding flour and water to maintain a sourdough starter⟧.

### Subject `CHAIN`: lubricating a bicycle chain

**CHAIN-1**

> This note concerns ⟦putting fresh lubricant on a bicycle chain⟧.

**CHAIN-2**

> This note concerns ⟦oiling the links of a bike chain⟧.

**CHAIN-3**

> This note concerns ⟦applying lubricant to the drive chain on a bicycle⟧.

The subject IDs and descriptions are scoring data. The candidate does not
receive them.

## Frozen hypothesis

The candidate will return:

1. at least one fine segment containing all three `STARTER` vectors and no
   `CHAIN` vector;
2. at least one fine segment containing all three `CHAIN` vectors and no
   `STARTER` vector.

The required group must appear as one segment. Three separate two-vector
segments do not count as recovery.

A separate segment containing members of both subjects is recorded as a
coarse false merge, but it does not change this assumption's verdict. This
experiment asks whether the two correct groups are recoverable; it does not
assume that a vector may belong to only one segment.

## Frozen system boundary

Use the shared 768-dimensional Sentence-T5-base SSE checkpoint identified in:

README.md

Preserve its raw outputs exactly. Any normalization, distance, or other
preprocessing belongs to the candidate's frozen configuration.

The candidate receives only opaque IDs and vectors. It may return overlapping
fine segments and leave vectors unassigned. If it also returns coarser levels,
the rule selecting the claimed fine-segment collection must be frozen before
results are inspected; parent regions are not scored as fine segments.

This is a visible development fixture, not held-out confirmation.

## Protocol

1. Obtain human approval of every note, mask, subject identity, and expected
   relationship in this document.
2. Freeze this document, the candidate implementation, its complete
   configuration, and any random seed.
3. Generate the six SSE vectors once and preserve their exact bytes and
   provenance.
4. Replace the fixture IDs with opaque IDs and apply a frozen shuffled order.
5. Give only those IDs and vectors to the candidate.
6. Preserve the candidate's complete fine-segment output before revealing the
   fixture identities.
7. Score the frozen hypothesis and render every returned segment using the
   original IDs, notes, and masks.

## Pass rule

The experiment passes only if both frozen recovery hypotheses pass.

A failure is one of:

- **split:** no segment contains every vector belonging to a subject;
- **contamination:** a segment needed to recover a subject also contains the
  other subject;
- **omission:** a required vector receives no membership that completes its
  subject's segment.

Extra overlapping segments, including cross-subject segments, are reported as
diagnostics but do not change Assumption 1's verdict.

## Required record

Preserve:

- every returned segment and membership;
- whether each subject was completely recovered;
- the best partial segment for any unrecovered subject;
- every cross-subject membership as a non-scoring diagnostic;
- unassigned vectors;
- the exact shuffled input order;
- the cosine matrix and nearest-neighbor order computed from the immutable raw
  SSE outputs;
- the candidate version, configuration, preprocessing, and seed;
- the raw SSE artifact and its hashes.

Cosine is diagnostic evidence. It does not determine the verdict.

## What a result means

A pass supports this assumption only for these two controlled subjects. It
does not establish resolution between nearby subjects, lexical robustness,
context robustness, density robustness, stability, or corpus-wide behavior.

A failure applies to the complete SSE-vector-plus-candidate system. This
experiment alone cannot determine whether the repeated meaning was absent from
the vectors or present but missed by the segmentation algorithm.
