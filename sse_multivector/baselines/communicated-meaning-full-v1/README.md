# Communicated-meaning SSE baseline v1

This immutable baseline preserves the complete 32-note SSE run using the
locked communicated-takeaway and exact takeaway-mask prompts.

`baseline.tar.zst` contains the exact worker request, run configuration, raw
and normalized vectors, worker receipt, complete pairwise analysis, rendered
analysis, and analysis manifest from
`target/sse-communicated-meaning-full-v1`.

The 1.3 GB SSE checkpoint is deliberately excluded. Its SHA-256 is pinned in
both `config.json` and `analysis/manifest.json` inside the archive:

`ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d`

The independently tracked human-readable inputs and interpretation are:

- `sse_multivector/communicated-meaning-full-proposal-v1.json`
- `docs/recommendation-engine/experiments/sse-multivector-note-set-v2.json`
- `docs/recommendation-engine/experiments/sse-communicated-meaning-full.md`

Verify and inspect it with:

```sh
cd sse_multivector/baselines/communicated-meaning-full-v1
sha256sum --check SHA256SUMS
tar --zstd -tf baseline.tar.zst
```

Do not replace this archive. A changed prompt, mask set, model, or worker is a
new baseline.
