# CREC-119 corrected 500-note vector baseline

This immutable baseline replaces eight machine-generated JSON records in the
original 500-note sample with the next eight eligible notes from the same
frozen order. The original v1 baseline remains unchanged.

## Correction

- The materializer scans the frozen sample in order, skips the eight exact
  rejected event IDs, and stops after retaining 500 notes.
- The resulting input contains 500 unique notes after scanning rows 1–508.
- Frozen rows 501–508 are the eight replacements.
- The corrected input SHA-256 is
  `af1f82719003ed73aea0f569c0a936733a95f6c366d4d95e1436c7cebae9b5d1`.
- None of the eight rejected event IDs is present.

## Result

- 500 source notes; 12 produced no takeaway.
- 1,268 takeaways, prominence scores, validated masks, and normalized
  768-dimensional SSE vectors. No prominence cutoff was applied.
- 147 maximal cross-note fine segments at cosine floor
  `0.44995143471140225`, representing 531 vectors from 252 notes.

The segment rule is
`fixed-floor-complete-linkage-maximal-cross-note-segments-v1`.

## Generation reuse

The 492 unchanged notes were not sent to the model again. Their 3,004 prior
jobs were imported only after validating the pinned v1 input, manifest,
append-only ledger, runner-upgrade chain, output, stage contracts, rendered
prompts, responses, and note text. Every imported result is explicitly marked
`execution: reused`, records its source ledger line and hash, and records zero
new usage.

Only the eight replacement notes received fresh calls:

- 8 takeaway calls;
- 12 prominence calls;
- 12 mask calls.

All 32 fresh calls succeeded. They recorded 76,397 input tokens, 7,168 cached
input tokens, 21,597 output tokens, and 20,503 reasoning-output tokens. The
archive includes both the pinned v1 reuse source and the complete corrected
v2 ledger, so the reuse provenance does not depend on mutable live files.
The v2 runner-upgrade ledger binds the completed result prefix to the later
reuse-validation hardening without replaying any model call.

## Frozen inputs and models

- Source NostrDB `data.mdb` SHA-256:
  `3b19f650035fbb71c09bc51e06957f64ca421df948bac3b4751fa4809ffe73e4`
- Frozen sample order SHA-256:
  `8b0ce45049ed10cfebccab6db15c665f3e2598f5efbb5ef0fc5813dba899bfd5`
- Generation: Codex CLI 0.146.0, `gpt-5.6-sol`, max reasoning,
  TPv3.82, PPv2, and MPv3.4. Every fresh call used a clean isolated context.
- SSE checkpoint SHA-256:
  `ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d`
- Sentence-T5 base-model tree SHA-256:
  `bba50abbbb7de6165ee3828c4e4abb0c88a6386bd4754374469246cde5017e5d`
- SSE worker SHA-256:
  `fe4dc92d834c5aa6e2c15072cd2cb57db3c03ea0062cde32bcb84b4a466f9421`
- Container image:
  `sha256:a6c9674dca720e1f094b7feeb1397b6e6b0a97e10f13e0a6555deebf4b70ddaa`

## Archive

`baseline.tar.zst` contains exactly the repo-relative paths listed in
`ARCHIVE-FILES`. It includes the frozen sample metadata, prompt registries,
the pinned v1 generation source, the corrected v2 generation ledger and
output, the SSE request and receipt, raw and normalized vectors, and the fine
segments.

The source NostrDB, SSE checkpoint, base-model tree, and container image are
excluded; their identities are pinned above and in the archived manifests.

Verify the archive from the repository root:

```sh
baseline=sse_multivector/baselines/crec-119-500-note-vector-v2
(cd "$baseline" && sha256sum --check SHA256SUMS)
diff -u "$baseline/ARCHIVE-FILES" \
  <(tar --zstd -tf "$baseline/baseline.tar.zst" | LC_ALL=C sort)
```

Deeply verify the live extracted artifacts when the pinned source NDB,
checkpoint, model tree, and container are present:

```sh
nix develop -c cargo run --release \
  --bin materialize-semantic-map-input -- \
  semantic_map/crec-119-generation-input-v2.json
nix develop -c python3 sse_multivector/scaled_vector_artifact.py \
  verify sse_multivector/crec-119-vector-v2.json
nix develop -c cargo run --release --bin scaled-fine-segments -- \
  verify sse_multivector/crec-119-segments-v2.json
```

Do not replace this archive. Any change to the corrected sample, prompts,
accepted generation output, encoder, floor, or implementation requires a new
baseline.

## Publication files

`historical-studies/crec-119-500-note-vector-v2` retains 500 posts, 1,268 takeaways
and 147 final segments as parsed assembled note results. Reuse of 492 notes and
3,004 final jobs stays separate from eight new notes and 32 new final jobs.
See the [catalog](../../../docs/experiments/publications.csv),
[dataset manifest](../../../docs/experiments/downloads.md#dataset-manifest) and
[export commands and checks](../../../docs/experiments/reproduce.md#archived-baseline-checks).
The files are prepared locally for Hugging Face Datasets; nothing is uploaded.
AS lineage remains unknown. The full archive remains local and unchanged;
the inspection commands above require those originals.
