# SSE Multi-Vector Isolation Experiment

## Status

The neutral 32-note input is frozen in
[`sse-multivector-note-set-v2.json`](./sse-multivector-note-set-v2.json). It
contains 32 real Nostr notes from 32 authors and presupposes no subjects.

Subject enumeration and independent mask generation have run over the raw
notes. Their complete, source-bound output is
[`subject-mask-proposal-v2.json`](../../../sse_multivector/subject-mask-proposal-v2.json):

- 113 proposed subjects;
- 172 exact text fragments;
- zero `unsupported` mask results.

The prompts used for both generation steps are recorded verbatim in that
artifact.

Human review is not complete. The subjects and masks are therefore not frozen,
and SSE inference has not run.

## Current Question

Given human-approved subjects and their exact supporting text, can SSE produce
a useful separate vector for each subject expressed within a note?

This requires more than broad topical similarity. A subject vector must retain
the meaning of its selected text while excluding the note's other meanings.

## Review Gate

The review proceeds in this order:

1. Review every proposed subject for a note individually.
2. Confirm explicitly that the note has no missing subject.
3. Only after every note's subject list passes, review every proposed mask
   individually.
4. Publish one approved subject-and-mask artifact only when both stages pass.

A rejected subject or missing-subject report blocks all mask review. A rejected
mask blocks publication. An `unsupported` result from the mask generator is a
generation failure and must stop the run before the review interface opens.

The complete note remains encoder context. Only the approved exact span or
spans are pooled into that subject's vector. Discontinuous spans are allowed
only when every span directly expresses the same subject.

## What This Establishes

Human review determines whether the generated subject list and masks are valid
enough to use as controlled inputs. It does not establish that subject
enumeration or masking can operate autonomously.

If the inputs pass review, the later SSE test asks whether separate masks from
one note lead to meaningfully separate semantic representations. That test does
not cover corpus-wide subject discovery, hierarchy construction, content
recommendation, or ranking.

The numerical SSE evaluation design and pass threshold remain undecided. They
must be frozen before any similarity result is inspected.
