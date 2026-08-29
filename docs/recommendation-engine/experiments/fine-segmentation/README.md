# Fine-segmentation assumption experiments

Status: **draft; do not encode or run yet**.

Five active protocols cover the six canonical assumptions recorded in:

../../../notes/MY-NOTES.md

Each experiment has its own purpose-built synthetic notes and manually
specified masks. The old 53-vector collection is not reused merely because it
already exists.

Before any experiment runs, the user must approve:

1. every complete synthetic note;
2. every exact mask;
3. the declared atomic subject represented by each mask;
4. every expected relationship used for scoring.

The experiments are:

1. 01-repeated-subject-recovery.md — repeated instances of the same fine
   subject
2. 02-nearby-subject-resolution.md — nearby but distinct fine subjects under
   balanced, unequal, and sparse support
3. 03-lexical-coincidence.md — lexical coincidences
4. 04-unmasked-context.md — changes to unmasked material
6. 06-irrelevant-change-stability.md — irrelevant-change stability

`05-density-and-sparsity.md` is a retired pointer. Its fixture and purpose were
merged into Experiment 2 so balanced organization and changing support use the
same frozen vectors.

## Boundary shared by all active experiments

Each input is one complete synthetic note plus one manually fixed mask. SSE
processes the complete note, averages the contextual token representations at
the selected positions, and applies its learned output transformation. The raw
768-dimensional output is preserved exactly.

Any normalization, distance function, or other preprocessing belongs to the
candidate fine-segmentation algorithm's frozen configuration. The candidate
receives only opaque vector IDs and vectors. It does not receive notes, masks,
subject names, or expected relationships.

The candidate may return overlapping segments and may leave vectors
unassigned. These experiments do not assume a partition, exhaustive coverage,
a fixed segment count, or one membership per vector. If the candidate produces
several resolutions or a hierarchy, the rule selecting its fine-segment output
must be frozen before results are inspected.

The same frozen SSE checkpoint is used for every input:

```text
Sentence-T5-base SSE
SHA-256 ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d
```

Before encoding, the executable experiment artifact must additionally freeze
and record:

- the exact SSE worker source hash;
- the model and tokenizer artifact hashes;
- `selected-contextual-token-mean-linear-relu-linear-v1` as the pooling and
  learned-output-transform contract;
- the byte-span-to-token selection rule;
- every complete input note and byte span;
- the raw `f32` vector dimension and output hashes.

Cosine diagnostics in every experiment are computed from these immutable raw
SSE outputs. A candidate may derive a different representation internally, but
that preprocessing is part of its separately frozen configuration.

The brackets `⟦...⟧` in the documents show the exact selected text. The
brackets themselves are not part of the note sent to SSE.

These are controlled development experiments, not corpus-wide validation. If
their results are used to modify a candidate, later validation requires newly
frozen holdout fixtures.
