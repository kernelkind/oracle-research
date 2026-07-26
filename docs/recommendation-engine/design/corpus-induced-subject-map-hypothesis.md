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

The synthetic runner requires RAM-backed output and verifies fixed cgroup
limits of 8 MiB/s reads, 2 MiB/s writes, 256 read IOPS, and 64 write IOPS before
opening experiment input. It also caps memory, CPU, and runtime.

The real-note sampler is a separate bounded path:

- it consumes only a prefix of the deterministically hash-ordered semantic
  event-ID order;
- one pressure permit covers one logical 32-byte event-ID read, one read-only
  LMDB lookup, and copying that note into memory;
- the source `data.mdb` is opened read-only, while the sampler's LMDB lock,
  mutable files, and artifacts stay on tmpfs;
- learning and evaluation authors are assigned by one frozen deterministic
  hash;
- a retained note is rejected if it is a high-confidence textual copy of a
  retained note in the opposite split;
- it stops as soon as both quotas fill and also has hard examined-row and
  serialized-byte limits;
- it records the hash of the exact ID prefix it consumed;
- the complete-corpus hashes in its output are explicitly declarations copied
  from the previously verified semantic manifest. It does not reread 3.9 GiB
  merely to repeat that verification.

The sampler uses the adaptive cgroup `io.pressure` policy in
[Disk I/O Pressure-Control Guidance](../disk-io-pressure-control.md). It does
not stack fixed device throttles on that controller because an artificial
throttle can itself create pressure and prevent recovery.

The copy rule is deliberately textual rather than semantic:

- normalize to Unicode NFC, lowercase, and collapse whitespace;
- normalized-equal notes are copies at every length;
- notes shorter than 100 Unicode characters receive no fuzzy matching;
- notes of at least 100 Unicode characters are copies only when their
  character-count ratio is at least 90% and their unique
  five-character-shingle Jaccard overlap is at least 90%;
- punctuation, URLs, Nostr identifiers, and all other meaning-bearing text
  remain in the normalized comparison rather than being stripped. Lowercasing
  may alter case-sensitive URL paths;
- notes are compared only across learning and evaluation. Semantic neighbors
  and notes merely discussing the same subject remain separate.

This operationalizes the experiment's duplicate-family requirement as pairwise
high-confidence textual-copy isolation. The rule prevents copied text from
crossing the held-out boundary. It does not delete or rewrite source notes,
perform semantic clustering, or construct transitive families. Byte-identical
content was already removed upstream. Lowercasing and whitespace collapsing can
conflate case- or indentation-sensitive code; the rule therefore establishes
copy isolation, not semantic identity.

The pinned tiny real-note materialization preflight completed:

- 82 ordered IDs were consumed to retain 64 learning and 16 evaluation notes;
- the run was bounded to at most 256 consumed IDs and a 2 MiB serialized
  sample;
- those notes represented 56 learning authors and 14 evaluation authors, with
  no author overlap;
- no high-confidence textual copy crossed the split;
- the learning-first JSONL contained 80 records and 31,493 bytes;
- the exact consumed ID-prefix hash was
  `594aaf66e537654729de8a5a1935da2f14b7144b2bde3b6daddcd869b156f3ea`;
- the sample hash was
  `da9c38b4141d062b1c4ecfb242182a2c532f9fa83cf3659866b985a5679fb8b7`;
- the source `data.mdb` size, inode, modification time, and change time were
  unchanged before and after the read-only container run;
- the artifact was produced in a dedicated tmpfs directory from the frozen
  configuration in
  `topic_map/crec-113-real-sample-preflight.json`.

This establishes only that bounded real-note materialization works under the
pressure controller and that this tiny split satisfies the frozen author and
textual-copy isolation rules. No real note has yet been encoded or used to
train the topic model. It supplies no topic-quality evidence.

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
