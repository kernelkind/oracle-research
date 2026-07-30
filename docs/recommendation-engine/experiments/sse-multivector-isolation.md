# SSE Multi-Vector Isolation Experiment

## Status

The neutral 32-note input is frozen in
[`sse-multivector-note-set-v2.json`](./sse-multivector-note-set-v2.json). It
contains 32 real Nostr notes from 32 authors and presupposes no subjects.

Subject enumeration and independent mask generation have run over every raw
note using the approved minimal prompts. Each note used a fresh subject call,
and every resulting subject used a separate fresh mask call. Their audited,
source-bound output is
[`subject-mask-proposal-v3.json`](../../../sse_multivector/subject-mask-proposal-v3.json):

- 190 subjects generated;
- 187 subjects retained after the primary agent inspected every proposal;
- 248 exact text fragments;
- zero `unsupported` mask results.

The audit removed three incidental subjects, corrected four labels, and
narrowed masks that contained text belonging to another subject. The prompts
are recorded verbatim in the artifact. SSE inference has not run.

## Current Question

Given audited subjects and their exact supporting text, can SSE produce
a useful separate vector for each subject expressed within a note?

This requires more than broad topical similarity. A subject vector must retain
the meaning of its selected text while excluding the note's other meanings.

## Input Preparation

The controlled inputs were prepared in this order:

1. One isolated call enumerated the subjects for each complete note.
2. One isolated call generated the mask for each subject.
3. The coordinator rejected schema errors, changed note text, absent
   substrings, and out-of-order substrings.
4. The primary agent read every subject and mask, then corrected only concrete
   overstatement, negation, incidental-subject, and cross-subject-mask errors.

The complete note remains encoder context. Only the audited exact span or
spans are pooled into that subject's vector. Discontinuous spans are allowed
only when every span directly expresses the same subject.

## What This Establishes

This audit makes the set usable as controlled inputs. It does not establish
that subject enumeration or masking can operate autonomously.

The SSE analysis asks whether separate masks from one note lead to
meaningfully separate semantic representations. That analysis does not cover
corpus-wide subject discovery, hierarchy construction, content recommendation,
or ranking.

## Diagnostic Analysis

This is exploratory analysis, not a pass/fail evaluation. It characterizes the
geometry produced by SSE so that a later experiment can ask a precise question
without inventing a threshold first.

The first analysis uses only the 187 audited subject masks:

1. Pin the SSE checkpoint, tokenizer, revision, pooling behavior, runtime
   configuration, and artifact hashes.
2. Generate one vector for each subject by giving SSE the complete note and
   that subject's mask. Subject labels are report metadata and must never be
   encoder input.
3. Verify one consistent dimension, finite values, and nonzero norms, then
   retain both the raw and L2-normalized vectors.
4. Calculate the complete exact cosine matrix: 17,391 unordered pairs,
   consisting of 638 same-note pairs and 16,753 cross-note pairs.
5. For every same-note pair, record its cosine and selected-token overlap.
   Disjoint masks must be interpreted separately from overlapping or nested
   masks.
6. For every subject, report its five nearest subjects from other notes with
   their labels, exact fragments, cosine values, and global cross-note
   percentile.
7. Summarize the raw same-note and cross-note similarity distributions. Split
   same-note pairs by mask overlap, and report whether each subject's nearest
   overall neighbor came from its own note or another note.
8. Retain the complete matrix and rankings so the five-neighbor display is not
   a data cutoff.

The written report must keep measurements separate from interpretation. It
should identify concrete examples of:

- useful separation: subjects from one note lead to different external
  neighborhoods;
- useful convergence: independently worded subjects from different notes are
  close;
- blending: distinct masks from one note remain effectively inseparable;
- context or lexical leakage: neighbors reflect surrounding or shared wording
  instead of the masked subject.

Same-note subjects may legitimately be related, and overlapping masks
mechanically share evidence. The generated labels are audited descriptions,
not independent ground truth. The 32 notes are diagnostic cases, not a
representative Nostr sample, and cosine has no universal semantic cutoff.

Do not add a pass threshold, expected-positive pair labels, clustering,
hierarchy construction, model comparison, whole-note or span-only baselines,
or dimensionality-reduction plots to the first analysis. Add a narrower
follow-up only when the first report exposes a specific ambiguity it can
resolve.
