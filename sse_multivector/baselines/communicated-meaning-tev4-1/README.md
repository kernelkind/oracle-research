# TEv4.1 self-contained extraction diagnostic

This immutable baseline preserves TEv4.1: the TPv3.81 and MPv3.3 extraction
pipeline applied to TEv3.1's final ordered 50-note corpus.

`baseline.tar.zst` contains:

- the exact 50-note input and generation configurations;
- the accepted output of every fresh-context model call;
- the raw generation logs, including one mechanically rejected mask attempt;
- the source-bound proposal and SSE worker request;
- the raw 768-dimensional vectors and worker receipt;
- the complete deterministic cosine analysis and manifests.

The checkpoint is excluded. Its pinned SHA-256 is recorded in the archived
configuration and analysis manifest:

`ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d`

The measured comparison with TEv3.1 is documented in
[`../../../docs/recommendation-engine/experiments/sse-communicated-meaning-extraction.md`](../../../docs/recommendation-engine/experiments/sse-communicated-meaning-extraction.md).

Verify and inspect the archive with:

```sh
cd sse_multivector/baselines/communicated-meaning-tev4-1
sha256sum --check SHA256SUMS
tar --zstd -tf baseline.tar.zst
```

Do not replace this archive. A changed note set, prompt, mask, checkpoint,
worker, or inference setting is a new baseline.

## Publication files

`historical-studies/communicated-meaning-tev4-1` retains geometry for 194 subjects:
18,721 unique pairwise cosine measurements, analysis headers and subject
diagnostics. Its 194 answer inputs are already selected in
`numerical/fine-region-00d974f22ed8935f/inputs.jsonl` and are not duplicated.
See the [catalog](../../../docs/experiments/publications.csv),
[dataset manifest](../../../docs/experiments/downloads.md#dataset-manifest) and
[export commands and checks](../../../docs/experiments/reproduce.md#archived-baseline-checks).
The files are prepared locally for Hugging Face Datasets; nothing is uploaded.
AS lineage remains unknown. The full archive remains local and unchanged;
the inspection commands above require those originals.
