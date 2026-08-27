# Real-note SSE transfer experiment

## Status

This draft defines the procedure that must be approved before holdout notes are
selected. No holdout SSE vectors or cosine results may be inspected until the
procedure and complete fixture have both been reviewed and frozen.

The earlier nine-note pilot and its follow-ups are development evidence. Their
notes and results cannot be used in this holdout.

## Question

Do the mask behaviors demonstrated with controlled synthetic text remain
present when SSE receives real Nostr notes and manually approved
atomic-subject masks?

This experiment tests SSE. It does not test automatic mask generation, fine
segmentation, subject labels, prominence, or hierarchy construction.

## Holdout source

Read notes from the frozen CREC-105 ten-month English-eligible corpus:

`../damus_snapshot/runs/crec-105-fresh-corpus-v9/derivation/cumulative-filtered.ndb`

The source `data.mdb` SHA-256 is
`3b19f650035fbb71c09bc51e06957f64ca421df948bac3b4751fa4809ffe73e4`.

Exclude:

1. every event ID in the frozen CREC-120 1,000-note sample; and
2. every real event ID used by an earlier SSE experiment.

Order the remaining eligible event IDs with a new, versioned,
domain-separated SHA-256 key. Review text in that order. If the first candidate
batch is insufficient, extend the same order rather than drawing a new sample.
Candidate selection may inspect note text and source metadata needed to resolve
the note. It may not inspect an SSE vector, cosine, neighborhood, or segment.

## Fixture construction

All subjects, masks, controls, and expected comparisons are human-approved from
the text before encoding.

### Controlled comparisons using real source text

Use source-exact text. Do not invent or paraphrase note content.

Create at least three independent comparisons for every applicable change
below. A note may support more than one comparison, but a comparison is omitted
when the source text cannot isolate its required change.

#### Mask boundaries

Keep the complete note fixed. Change only the exact boundary of a valid mask
without changing its human-defined atomic subject.

Compare that same-subject change with a mask from the same note that identifies
a different atomic subject.

#### Text outside the mask

Keep the mask text and its atomic subject fixed. Compare the complete note with
a source-exact version from which clearly unrelated text outside the mask has
been removed. Human review must confirm that the removal does not change the
meaning of the masked subject.

Compare that change with selecting a different atomic subject from the complete
note.

#### Redundant mask fragments

Use a real note that expresses the same atomic subject more than once. Compare
the baseline mask with a mask that also includes the redundant expression.

The control adds a source-exact fragment expressing a different atomic subject
from that same note.

#### Changed atomic subject

Keep the complete note fixed. For a single-fragment mask, select a different
source fragment whose human-defined atomic subject is different. For a
multi-fragment mask, change one content-bearing fragment so the complete mask
has a different human-defined atomic subject.

Fragment count alone is not repeated here. When two masks select the same token
indices, SSE receives the same token mask and deterministically produces the
same vector; the synthetic experiment already verified the raw bytes.

### Untouched real-note comparisons

Freeze eight sets: four using single-fragment masks and four using
multi-fragment masks. Every set contains three untouched real notes:

- A and B express the same human-defined atomic subject with meaningfully
  different wording and surrounding text.
- C is related enough to be a useful comparison but expresses a different
  atomic subject.

C must not merely express a broader subject or one component of the subject
shared by A and B. Each note must be understandable from its stored text; a URL
or unavailable conversation cannot supply the subject being judged.

These untouched comparisons test the combined effect of natural wording and
context. They do not attribute a failure to either factor individually; the
controlled comparisons above provide that isolation.

## Review and freeze

For every proposed comparison, review:

1. the complete source note;
2. the human-defined atomic subject;
3. the exact mask rendered over the note;
4. what changes between the control and changed input; and
5. why the different-subject control is actually different.

The review must not reveal SSE output. Rejections and their reasons remain in
the selection record. Replacements come from the continuing frozen candidate
order.

Before encoding, freeze:

- source and exclusion identities;
- candidate-order rule and reviewed prefix;
- accepted and rejected event IDs;
- exact note text and its hash;
- mask byte ranges;
- human-defined atomic subjects;
- every comparison and expected ordering; and
- the exact SSE worker, checkpoint, model tree, and container identities.

## Evaluation

Every controlled comparison uses the same rule:

> The same-subject change must have a higher cosine to its control than the
> subject-changing input has to that control.

For each untouched set:

```text
cosine(A, B) > cosine(A, C)
cosine(A, B) > cosine(B, C)
```

No absolute cosine is called "high" or "low." Report every cosine and margin.
Do not remove, relabel, or replace a comparison after results are visible. Any
corrective follow-up is a new experiment with its own frozen input.

A requirement is supported by this holdout only if every predeclared comparison
testing it passes. A failure leaves that requirement unresolved; it is not
converted into a pass by explaining the result afterward.
