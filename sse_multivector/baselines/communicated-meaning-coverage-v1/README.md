# TEv3.1 communicated-meaning coverage diagnostic

This immutable baseline preserves the first stage of TEv3.1, the coverage-only
follow-up to TEv2.

The original 32 notes, 73 takeaways, masks, model, and worker are unchanged.
Twelve real learning-split notes from distinct new authors were appended after
selection from raw text without consulting SSE scores. Six cover autonomy and
self-direction. Six cover retirement, leaving work, low consumption, and
self-provision.

Failure #3 was added later and is preserved separately in
`communicated-meaning-coverage-v2`.

`baseline.tar.zst` contains the exact note selection, generated takeaways and
masks, source-bound worker request, configuration, raw vectors, receipt, and
complete analysis from `target/sse-communicated-meaning-coverage-v1`.

The first 73 vectors and receipt rows were verified as exact matches to TEv2
before the expanded result was interpreted.

The checkpoint is excluded. Its pinned SHA-256 is recorded in the archived
configuration and analysis manifest:

`ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d`

Verify and inspect the archive with:

```sh
cd sse_multivector/baselines/communicated-meaning-coverage-v1
sha256sum --check SHA256SUMS
tar --zstd -tf baseline.tar.zst
```

Do not replace this archive. A changed selection, prompt, mask, model, or
worker is a new baseline.
