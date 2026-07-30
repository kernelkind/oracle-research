# SSE Multi-Vector Isolation Experiment

## Status

This is the approved high-level plan for the first atomic-vector experiment.
It has not been executed.

The 32-note set is approved and frozen in
[`sse-multivector-note-set-v1.json`](./sse-multivector-note-set-v1.json).
Token masks and the numerical pass threshold remain unfrozen.

The approved constraints are:

- use 32 real English Nostr notes;
- use the released full-dimensional SSE model with the Sentence-T5-large
  encoder;
- run inference locally rather than renting compute;
- test SSE independently from subject-span extraction.

The token masks and numerical pass threshold must be frozen before any result
is generated.

## Question

Given correct subject-supporting token masks, does SSE produce a separate
useful semantic vector for each subject expressed within a note?

More concretely, does a vector made from one masked subject:

- align with the same fine subject expressed using different words;
- remain distinct from the note's other masked subjects;
- distinguish that subject from closely related subjects rather than only from
  obviously unrelated ones?

## What This Does Not Test

This experiment does not test:

- automatic subject-span extraction;
- discovery or labeling of corpus-wide fine-subject regions;
- clustering;
- hierarchy construction;
- note recommendation or ranking.

Human-approved masks deliberately remove extractor uncertainty. Failure can
therefore be attributed to the masks or SSE representation rather than an
unknown upstream extractor.

## The 32 Notes

Choose eight test subjects. They are evaluation cases, not a proposed subject
ontology.

Use:

- 24 reference notes: three independently worded examples for each test
  subject;
- 8 mixed notes: each supplies two primary subject masks, producing 16 primary
  test vectors.

Arrange the mixed-note cases so that every test subject appears in two primary
masks.

The set must include:

- subjects that are clearly unrelated;
- closely related subjects that share vocabulary;
- paraphrases that express the same subject with different vocabulary;
- mixed notes whose two tested subjects are both material to the note.

For example, general enjoyment of Rust programming, a rust-analyzer feature,
and borrow-checker troubleshooting must not be treated as interchangeable just
because all three concern Rust.

No note may serve as both a reference and a mixed-note test case.

## Masks

Every evaluated subject has a human-approved binary token mask over its complete
source note. A mask may select discontinuous tokens when those tokens jointly
support one subject.

SSE still encodes the complete note. For each mask, it selectively pools the
masked contextual token representations and emits one vector. Multiple masks
from the same note share the encoder pass but produce separate vectors.

Automatic extraction is not used in this experiment.

For a small predetermined subset, approve both a tight mask and a slightly
expanded mask that express the same subject. This measures whether harmless
boundary variation changes the resulting semantic neighborhood.

## Computation

1. Pin the released SSE checkpoint, tokenizer, and exact revision.
2. Tokenize each complete note and record the approved binary masks.
3. Produce one SSE vector for every reference mask and mixed-note mask.
4. L2-normalize the vectors.
5. Compute cosine similarity between each of the 16 primary mixed-note vectors
   and all 24 reference vectors.
6. For each mixed note, also produce a control vector using an all-content mask
   through the same SSE model.
7. Repeat the same comparisons with each all-content control.

The evaluation code performs these comparisons. Vectors do not retrieve other
vectors themselves.

Cosine similarity is used because SSE was contrastively trained to give
semantically equivalent masked propositions higher cosine similarity and
different propositions lower cosine similarity. Whether that learned geometry
generalizes from propositions to subjects is the question being tested.

## Recorded Results

For each primary masked vector, record:

- the cosine similarity to every reference vector;
- the rank of the nearest reference for the intended test subject;
- whether the nearest reference belongs to the intended test subject;
- the difference between the nearest intended reference and nearest
  unintended reference;
- the same measurements for the all-content control;
- the nearest reference notes themselves for human inspection.

Also record:

- confusion between closely related test subjects;
- similarity between tight-mask and expanded-mask results;
- results by test subject, so one easy subject cannot conceal another subject's
  failure.

## Interpretation

Evidence for SSE would require all of the following:

- intended-subject references consistently outrank unrelated references;
- close subject distinctions survive, not merely broad domain distinctions;
- separate masks from one mixed note lead toward their respective subjects;
- subject masks improve isolation relative to the all-content control;
- small valid mask-boundary changes do not radically change the result.

The result argues against SSE for this architecture if masked vectors remain
blended, collapse neighboring fine subjects, or add no useful isolation over
the all-content control.

An ambiguous result justifies expanding this representation test. It does not
justify proceeding to extraction, clustering, or hierarchy construction.

The precise numerical pass threshold must be agreed before inspecting the
similarity results.
