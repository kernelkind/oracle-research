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

The later SSE test asks whether separate masks from one note lead to
meaningfully separate semantic representations. That test does not cover
corpus-wide subject discovery, hierarchy construction, content recommendation,
or ranking.

The numerical SSE evaluation design and pass threshold remain undecided. They
must be frozen before any similarity result is inspected.
