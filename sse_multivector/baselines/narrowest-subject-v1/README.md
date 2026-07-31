# Narrowest-subject SSE baseline v1

This immutable baseline preserves the complete 32-note SSE run that used the
instruction to enumerate the narrowest recognizable subjects. It exists so a
later, consistently regenerated subject representation can be compared with
the original geometry without rerunning or reconstructing this experiment.

`baseline.tar.zst` contains the exact worker request, run configuration, raw
and normalized vectors, worker receipt, complete pairwise analysis, rendered
analysis, and analysis manifest from
`target/sse-multivector-diagnostic-v1`.

The 1.3 GB SSE checkpoint is deliberately excluded. Its SHA-256 is pinned in
both `config.json` and `analysis/manifest.json` inside the archive:

`ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d`

The archive is self-contained with respect to the 32 raw notes, 187 subject
labels, exact masks, vector rows, and every reported cosine. The independently
tracked human-readable inputs remain at:

- `docs/recommendation-engine/experiments/sse-multivector-note-set-v2.json`
- `sse_multivector/subject-mask-proposal-v3.json`

Verify and inspect it with:

```sh
cd sse_multivector/baselines/narrowest-subject-v1
sha256sum --check SHA256SUMS
tar --zstd -tf baseline.tar.zst
```

Do not replace this archive when producing the broader, navigation-useful
subject run. Store that run as a separate baseline.
