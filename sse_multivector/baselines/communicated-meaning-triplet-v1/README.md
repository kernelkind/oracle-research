# Communicated-meaning SSE triplet v1

This immutable baseline preserves the complete three-note, seven-takeaway SSE
run using the approved communicated-meaning and mask prompts. The run is a
small diagnostic data point; it is not a gate for the 32-note experiment.

`baseline.tar.zst` contains the exact worker request, run configuration, raw
and normalized vectors, worker receipt, complete 21-pair analysis, rendered
analysis, and analysis manifest.

The 1.3 GB SSE checkpoint is deliberately excluded. Its SHA-256 is pinned in
the archived configuration and manifest:

`ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d`

The independently tracked source-bound inputs are:

- `docs/recommendation-engine/experiments/sse-communicated-meaning-triplet-note-set-v1.json`
- `sse_multivector/communicated-meaning-triplet-proposal-v1.json`

Verify and inspect the archive with:

```sh
cd sse_multivector/baselines/communicated-meaning-triplet-v1
sha256sum --check SHA256SUMS
tar --zstd -tf baseline.tar.zst
```
