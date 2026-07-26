# Corpus-Induced Weighted Note-Topic Map

## Status

Current hypothesis and approved prerequisite experiment, tracked by CREC-113.
This is not an approved product architecture.

The neutral literature record is
[Corpus-Induced Semantic Region Discovery](../research/semantic-region-discovery-and-labeling.md).

## Why

The proposed subject-navigation direction requires a public relation learned
from the Nostr corpus:

```text
w(note, topic)
```

The same relation must support both views:

```text
NoteId  -> {TopicId -> Weight}
TopicId -> {NoteId  -> Weight}
```

Topics must emerge from public note content. They are not predefined, and
private ratings do not create them.

Before considering labels, hierarchy, navigation, or personalization, we must
establish that this base relation can represent the subjects people recognize
in Nostr notes.

## Current Hypothesis

Use one strong whole-note embedding representation and train an
SAE-TM-style sparse autoencoder with BatchTopK sparsity over a disjoint learning
sample.

- One non-dead learned feature is one topic candidate.
- One note may activate several topic candidates.
- A feature becomes a `TopicId` only if it activates on at least one learning
  note.
- Evaluation-only activations cannot create new topics.
- All such learning features remain in the result, including singleton,
  incoherent, or non-semantic features. Those failures must be counted.
- Compact `TopicId` values retain a mapping to the original SAE feature IDs.

[SAE-TM](https://arxiv.org/abs/2511.16309) supports treating sparse learned
features as unnamed topic atoms. [BatchTopK](https://arxiv.org/abs/2412.06410)
supports variable active-feature counts per note while controlling average
sparsity. Neither paper establishes that this combination will recover
human-recognized topics from short Nostr notes.

The existing Oracle retrieval matrix is not forced into this experiment. It
was built for semantic retrieval, not topic recovery.

## Frozen Relation Semantics

For a positive inferred activation `a(note, topic)`, the experiment stores:

```text
w(note, topic) = a(note, topic) / sum(a(note, every active topic))
```

This is the SAE-TM document-topic proportion. An all-zero note remains
addressable but unassigned.

Only ordinal meaning is claimed: within the learned relation, a larger weight
means stronger membership. Numeric calibration is not claimed.

The note-major and topic-major indexes are derived from this one sparse matrix.
They are not learned or generated independently.

## Experiment Boundary

The formal experiment must:

- split learning and evaluation notes before training;
- keep evaluation notes disjoint by author and duplicate family;
- bind every matrix row to its actual 32-byte `NoteId`;
- freeze corpus, encoder, model, runtime, seed, and evaluation identities;
- use a batch-independent frozen inference threshold;
- select formal cases without inspecting attractive examples;
- count dead, singleton, universal, duplicate, incoherent, and non-semantic
  topics rather than hiding them;
- report topic-to-note and note-to-topic judgments separately.

CREC-113 contains the formal human evaluation and supplementary audit.

## Not in Scope

- predefined topics;
- topic labels;
- a hierarchy or graph;
- navigation UI;
- a contextual-span or multi-vector competitor;
- private ratings or a personalizer;
- recommendation or feed quality;
- a complete-corpus map.

Those parts are considered only if the base weighted relation works.

## Resource Preflight

A discarded synthetic preflight exercised the production numerical and
artifact path with:

- 4,096 learning rows and 512 held-out rows;
- 768-dimensional FP32 inputs;
- 3,072 BatchTopK features and average `k = 32`;
- batch size 1,000 and 20 training steps.

It read 14,303,232 bytes from RAM, wrote a 2,785,550-byte relation to RAM, and
completed in 10.0 seconds on CPU. This is resource evidence only. Synthetic
vectors provide no topic-quality evidence.

The guarded runner requires RAM-backed output and verifies cgroup limits of
8 MiB/s reads, 2 MiB/s writes, 256 read IOPS, and 64 write IOPS before opening
experiment input. It also caps memory, CPU, and runtime.

The next stage requires a real, disjoint Nostr sample and fresh embeddings from
the selected topic-recovery encoder. It must not begin until its model download
and host I/O are reviewed separately.

## Main Risks

- Whole-note embeddings may blend meanings before the sparse model sees them.
- Features may represent author, language, style, syntax, format, or
  boilerplate instead of semantic topics.
- A coherent global feature may still be assigned incorrectly to individual
  notes.
- Generic features may obscure narrow meanings.
- Rare meanings may be absorbed or left unassigned.
- Row-normalized topic proportions may not order representative notes as a
  person expects.

A failure rejects this corpus, representation, and method. It does not prove
that every possible corpus-induced topic model is impossible.
