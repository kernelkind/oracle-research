# CREC-119 500-note vector baseline

This immutable baseline preserves the accepted CREC-119 generation ledger,
all 1,311 communicated-meaning vectors, and the fixed-floor fine segments
derived from the first 500 notes of the frozen CREC-120 sample.

## Result

- 500 source notes; 12 produced no takeaway.
- 1,311 takeaways, prominence scores, validated masks, and normalized
  768-dimensional SSE vectors. No prominence cutoff was applied.
- 584 complete-link partition regions at cosine floor
  `0.44995143471140225`.
- 150 maximal cross-note fine segments retained, representing 579 vectors
  from 254 notes.
- 434 singleton or same-note-only regions excluded.

The segment rule is
`fixed-floor-complete-linkage-maximal-cross-note-segments-v1`.

## Frozen inputs and models

- Source NostrDB `data.mdb` SHA-256:
  `3b19f650035fbb71c09bc51e06957f64ca421df948bac3b4751fa4809ffe73e4`
- Frozen sample order SHA-256:
  `8b0ce45049ed10cfebccab6db15c665f3e2598f5efbb5ef0fc5813dba899bfd5`
- Materialized 500-note input SHA-256:
  `b5e4665644c2229698cc795399c3510a8ce1535ce13b45382d2d76f50dbdc8d4`
- Generation: Codex CLI 0.146.0, `gpt-5.6-sol`, max reasoning,
  TPv3.82, PPv2, and MPv3.4. Each call used a fresh isolated context.
- SSE checkpoint SHA-256:
  `ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d`
- Sentence-T5 base-model tree SHA-256:
  `bba50abbbb7de6165ee3828c4e4abb0c88a6386bd4754374469246cde5017e5d`
- SSE worker SHA-256:
  `fe4dc92d834c5aa6e2c15072cd2cb57db3c03ea0062cde32bcb84b4a466f9421`
- Container image:
  `sha256:a6c9674dca720e1f094b7feeb1397b6e6b0a97e10f13e0a6555deebf4b70ddaa`

## Generation ledger

The append-only ledger contains 3,147 attempts for 3,122 final jobs. All
3,122 latest results succeeded. There were 25 additional attempts across 21
retried jobs; the ledger retains all 10 failed attempts and every superseded
successful result.

Cumulative recorded usage across every attempt:

- 7,900,202 input tokens
- 2,645,248 cached input tokens
- 1,914,767 output tokens
- 1,788,295 reasoning-output tokens

`runner-upgrades.jsonl` authenticates both runner transitions against the
exact preceding result-ledger byte prefix. The earlier runner sources are
identified by SHA-256 but were not separately snapshotted; the final runner
implementation is pinned by the enclosing Git commit.

The optional one-hour calibration recorded 169 model calls. During that window, 27 notes and 55 takeaways completed, using 434,652 input tokens, 91,648
cached input tokens, 83,447 output tokens, and 77,216 reasoning-output tokens.

## Archive

`baseline.tar.zst` contains exactly the 36 repo-relative paths listed in
`ARCHIVE-FILES`. It includes the frozen sample metadata, prompt registries,
complete model-call ledger, accepted generation output, SSE request and
receipt, raw and normalized vectors, and fine segments.

The 14 GB source NostrDB, the SSE checkpoint, the base-model tree, and the
container image are deliberately excluded; their identities are pinned
above and inside the archived manifests. Remote Codex generation is
nondeterministic: the archive preserves the accepted outputs and complete
call history, not a promise of byte-identical regeneration.

The archived config and receipt record the container digest, but the archive
cannot independently prove which Docker command produced that receipt.

Verify the archive from the repository root:

```sh
baseline=sse_multivector/baselines/crec-119-500-note-vector-v1
(cd "$baseline" && sha256sum --check SHA256SUMS)
diff -u "$baseline/ARCHIVE-FILES" \
  <(tar --zstd -tf "$baseline/baseline.tar.zst" | LC_ALL=C sort)
```

Deeply verify the live extracted artifacts when the pinned source NDB,
checkpoint, model tree, and container are present:

```sh
nix develop -c cargo run --release \
  --bin materialize-semantic-map-input -- \
  semantic_map/crec-119-generation-input-v1.json
nix develop -c python3 sse_multivector/scaled_vector_artifact.py \
  verify sse_multivector/crec-119-vector-v1.json
nix develop -c cargo run --release --bin scaled-fine-segments -- \
  verify sse_multivector/crec-119-segments-v1.json
```

Do not replace this archive. Any change to the sample, prompts, accepted
generation output, encoder, floor, or implementation requires a new
baseline.

## Publication files

`historical-studies/crec-119-500-note-vector-v1` retains 500 posts, 1,311 takeaways
and 150 final segments. Answers are parsed assembled note results, not raw
per-call response strings. See the [catalog](../../../docs/experiments/publications.csv),
[dataset manifest](../../../docs/experiments/downloads.md#dataset-manifest) and
[export commands and checks](../../../docs/experiments/reproduce.md#verify-and-restore-the-dataset).
The files are prepared locally for Hugging Face Datasets; nothing is uploaded.
AS lineage remains unknown. The full archive remains local and unchanged;
the inspection commands above require those originals.
