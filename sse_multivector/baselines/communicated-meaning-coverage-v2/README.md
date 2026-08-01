# TEv3.1 Failure #3 coverage extension

This immutable baseline preserves the second TEv3.1 coverage stage.

The first stage's 44 notes and 106 vectors remain preserved separately in
`communicated-meaning-coverage-v1`. This extension appends six real
learning-split notes from distinct new authors, selected from raw text without
consulting SSE vectors, scores, or ranks. Their 25 takeaways cover surveillance,
systemic control, loss of autonomy, and closely related meanings.

`baseline.tar.zst` contains the exact note selection, generated takeaways and
masks, source-bound worker request, configuration, raw vectors, receipt, and
complete analysis from `target/sse-communicated-meaning-coverage-v2`.

The original v1 archive was not modified. The target Failure #3 vector and its
previous leading neighbors are byte-identical in this extension. The final
four v1 vectors were recomputed in a different batch shape and differ slightly;
they are unrelated to the Failure #3 ranking.

The checkpoint is excluded. Its pinned SHA-256 is recorded in the archived
configuration and analysis manifest:

`ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d`

Verify and inspect the archive with:

```sh
cd sse_multivector/baselines/communicated-meaning-coverage-v2
sha256sum --check SHA256SUMS
tar --zstd -tf baseline.tar.zst
```

Do not replace this archive. A changed selection, prompt, mask, model, or
worker is a new baseline.
