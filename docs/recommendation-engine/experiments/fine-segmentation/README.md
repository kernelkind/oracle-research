# Fine-segmentation assumption experiments

Status: **draft; do not encode or run yet**.

Five active protocols cover the six canonical assumptions recorded in
[MY-NOTES.md](../../../notes/MY-NOTES.md). Each experiment uses purpose-built
synthetic notes and manually specified masks; the old 53-vector collection is
not reused merely because it exists.

The active experiments are:

1. [Experiment 1](01-repeated-subject-recovery.md) — repeated instances of one
   fine subject;
2. [Experiment 2](02-nearby-subject-resolution.md) — nearby subjects under
   balanced, unequal, and sparse support;
3. [Experiment 3](03-lexical-coincidence.md) — lexical coincidences;
4. [Experiment 4](04-unmasked-context.md) — changes to unmasked material; and
5. [Experiment 6](06-irrelevant-change-stability.md) — irrelevant-change
   stability.

[Experiment 5](05-density-and-sparsity.md) is a retired pointer. Its question
is covered by Experiment 2.

## Shared execution contract

### Fixture and SSE boundary

Before any experiment runs, a human must approve every complete synthetic
note, exact mask, declared atomic subject, expected relationship, scoring rule,
and experiment-specific prerequisite. Approval applies to exact UTF-8 bytes,
not rendered text alone.

Each SSE input is one complete note plus one fixed byte span. SSE processes the
complete note, averages the contextual token representations selected by that
span, and applies its learned output transformation. The brackets `⟦...⟧` in
the experiment documents show selected text; the brackets are not input bytes.

All experiments use this checkpoint:

```text
Sentence-T5-base SSE
SHA-256 ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d
```

Before encoding, freeze the exact note bytes and spans and an encoder manifest
containing the worker source, model and tokenizer artifacts, their hashes, the
byte-span-to-token rule, and
`selected-contextual-token-mean-linear-relu-linear-v1` as the pooling and
learned-output-transform contract. Encode each unique input once. Then preserve
the raw `f32` output bytes and record each output's element count, byte count,
and SHA-256. The expected element count is 768; a mismatch is an encoder
failure, not a candidate result.

Cosine and other representation diagnostics use only these immutable raw
outputs. Any normalization, distance function, or other candidate-side
preprocessing belongs to the frozen candidate boundary.

### Candidate identity and order

Freeze the candidate before encoding or inspecting any fixture vector. Its
**identity tuple** is:

```text
(candidate-source-tree hash,
 executable or container hash,
 dependency-lock or runtime hash,
 configuration-bytes hash,
 preprocessing contract and parameters hash,
 candidate seed,
 fine-output selector,
 deterministic tie-rule contract)
```

Record the exact tuple fields in a canonical manifest and record its SHA-256.
Changing any field creates a different candidate whose results must be kept
separate.

The candidate must be permutation-invariant by construction: permuting the
same `(opaque ID, vector bytes)` pairs must produce the same unordered
fine-segment collection. Initialization, batching, traversal, and tie breaking
must not depend on arrival position. An input-order experiment may diagnose an
implementation, but it does not replace this design requirement.

The candidate receives only opaque IDs and vector bytes. It receives no notes,
masks, readable fixture IDs, subject names, conditions, support roles, expected
relationships, or scoring rules. The selected fine output may overlap and may
leave vectors unassigned; no shared rule requires a partition, exhaustive
coverage, a fixed segment count, or one membership per vector.

### Opaque-ID blinding

Use the experiment document's filename without `.md` as its UTF-8 namespace.
After fixture approval and candidate freeze, draw one 32-byte seed from the
operating-system CSPRNG. For every readable fixture ID, derive:

```text
opaque_id = HMAC-SHA-256(
  seed,
  "fine-segmentation-id-v1\0" || namespace || "\0" || fixture_id
)

order_key = HMAC-SHA-256(
  seed,
  "fine-segmentation-order-v1\0" || namespace || "\0" || fixture_id
)
```

Represent an opaque ID as the 32 digest bytes encoded as 64 lowercase
hexadecimal characters. The default global input order is ascending
`order_key`, breaking a collision by opaque-ID bytes; a run containing a subset
filters that global order. An experiment may declare an order intervention,
but every exact order must be frozen before encoding.

Before encoding, record this commitment:

```text
SHA-256(
  "fine-segmentation-blinding-commit-v1\0" || namespace || "\0" || seed
)
```

Because the approved readable IDs and derivation are already frozen, this
commits the complete mapping and default order. Keep the seed, mapping, and
order in a private scorer artifact. Reveal them only after every candidate
output is immutable, then verify the commitment and every derivation before
scoring.

### Output validity and canonicalization

The selected fine output is an unordered collection of unordered member-ID
sets. Validate each raw output before projection, identity reveal, or scoring:

- every segment must be nonempty;
- every member must be a 64-character lowercase hexadecimal opaque ID present
  in that exact input;
- a raw segment must not repeat a member ID; and
- two segments must not have the same member set.

A duplicate member set is invalid and must never be silently deduplicated.
Singletons, overlaps, and an empty outer collection remain valid under the
shared contract; an experiment-specific rubric may still reject them.

Canonicalize a valid output as follows:

1. decode and sort member IDs by their 32-byte values;
2. encode each segment as a compact JSON array of its lowercase-hex strings;
3. use those encodings as sort keys and sort the segment arrays
   lexicographically by the keys' UTF-8 bytes;
4. encode the resulting array of segment arrays—not an array of quoted JSON
   strings—as compact UTF-8 JSON with no trailing newline;
   and
5. compute SHA-256 over those exact bytes.

Canonicalization removes only member and segment ordering. Preserve the raw
output, canonical JSON bytes, and hash.

### Lifecycle

Run every active experiment in this order:

1. obtain human approval of the fixture, rubric, and prerequisite graph;
2. freeze the candidate identity tuple and document its construction-level
   permutation invariance;
3. derive the opaque-ID mapping and order and record their private artifact and
   public commitment;
4. freeze the SSE artifacts, exact input bytes, spans, and all exact run-input
   specifications;
5. encode each unique SSE input once, then record output dimensions and hashes
   and freeze the vector bytes;
6. run every exact candidate input twice from fresh candidate state with the
   same identity tuple, opaque IDs, vector bytes, and order;
7. preserve both raw outputs, validate them independently, canonicalize valid
   outputs, and require their canonical bytes—not only hashes—to match;
8. after all outputs are immutable, reveal and verify the blinding artifact;
   and
9. restore readable identities and apply the approved scoring rules.

No invocation may train, prime, or provide mutable cached state to another.
Two matching repetitions establish repeatability only for that exact input.

### Prerequisite scope

Missing approval, boundary drift, an ineligible order-dependent candidate, an
encoder failure, or failed blinding verification invalidates the experiment;
it supplies no semantic verdict. An invalid raw output is an output-contract
failure for that exact input. Two valid but unequal canonical outputs are a
repeatability failure for that exact input. Either blocks that input and every
comparison that depends on it from semantic scoring.

An experiment-specific baseline or other semantic prerequisite blocks only the
conditions that explicitly depend on it. Independent conditions may retain
their own scoped results. A prerequisite failure is not evidence that the
dependent hypothesis is false; report it separately from a scored failure.

These are controlled development experiments, not corpus-wide validation. If
their results are used to modify a candidate, later validation requires newly
frozen holdout fixtures.
