# TRUE03 execution and verification

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

Run locally on September 14, 2026. No training, paid compute, API call, model download or GPU. Previous raw experiment artifacts are preserved.

## Identity and environment

- Model: `google/t5_xxl_true_nli_mixture`, revision `aa6cfe1dd4257853bfdd772992045f41bfc14988`, 11,307,321,344 parameters.
- Same TRUE02 CPU float32 inference, four threads, batch four, seed zero, deterministic algorithms and complete native greedy generation. All checkpoint loading-error lists are empty.
- Same topic input, label tokenization and strictly-greater-than-0.142 score rule. Native labels and cutoff decisions remain separate.
- Same installed torch 2.8.0+cpu, transformers 4.57.1, NumPy 2.3.4, huggingface_hub 0.36.2 and safetensors 0.6.2.
- The old environment's Python 3.11.15 executable was missing. An already-installed Python 3.11.14 interpreter used the existing Python 3.11 package directory through an explicit existing NixOS loader. No environment, shared interpreter, package or library was overwritten. This runtime difference is saved in `started.json`; the complete environment is not claimed byte-identical to TRUE02.
- All five released weight hashes and the model-file manifest match TRUE02. No model configuration or threshold was fitted to these outputs.

The 22 pairs were fixed after an independent blind semantic review and before inference. Two ambiguous pairs were excluded at that stage. The runner saved the exact fixture, full title artifact, 44 prepared inputs and source snapshots before checkpoint hashing/loading.

## Resources

Before launch, approximately 107 GiB of host memory was available. The command refused to start below 70 GiB. One model process ran in `oracle-true03.scope`, with 60 GiB RAM maximum, zero scope swap and four-CPU quota. These limits and zero swap were observed while it was active; no other process was stopped.

- Total runner time including hashing/loading: **128.25 seconds**.
- Inference and packaging: **84.09 seconds**.
- Peak process RSS: **45,492,116 KiB**, approximately **43.4 GiB**.
- Exit status: **0**. The scope was inactive after completion; no model process remained.
- Artifact size before this explanatory documentation: approximately **5.7 MiB**.

Global host swap already contained unrelated data before the run. The zero-swap observation concerns this inference scope, not the whole machine.

## Implementation and tests

A small new runner resolves actual titles from their original group IDs and validates the frozen source/fixture hashes. It prepares both directions with explicit pre-scoring expectations but sends only the serialized topic sentences to the model. It refuses duplicate/self/unknown pairs, non-Boolean expectations, missing rationale, changed source bytes and existing output directories.

The existing TRUE02 inference block was extracted into a shared function so the new runner does not maintain a duplicate model implementation. An executable-AST comparison against the frozen TRUE02 source confirms only the experiment name, output path and batch-size references were parameterized. The default TRUE02 entrypoint remains supported.

Tests first failed with the new runner missing, then exercised the actual input preparation, freezing, CLI and shared inference source. The runtime-metadata assertion also failed before the metadata was added. **56 distinct tests pass: nine new tests and 47 existing TRUE, RSE and HierarCaps regression tests.** The main agent separately reran the 33 TRUE-specific tests successfully. Existing approved tests were not changed. Tests never loaded a neural model.

## Independent verification

A separate read-only agent reconstructed every input from the frozen title file and pair list without importing the production preparation code. It checked all source hashes, exact title strings, directions, expectations, exclusions and model-only inputs.

It then replayed the saved 44 × 32,128 first-token logits using NumPy, independently verified tokenization/native decoding/EOS, all recorded score diagnostics, cutoff decisions, aggregate counts, score orderings and completion hashes. Maximum numerical discrepancy was **8.88e-16**; maximum input length was **30 tokens**, without truncation. No second neural-model load or weight rehash was used; verification peak RSS was approximately 140 MiB.

Verification record (`verification.json`), raw runtime measurements and output hashes (`completion.json`).

## Exact inference command

This is the command used. The original output path now exists, so repeating it intentionally refuses to overwrite results; use a new output path and unused scope name for any separately authorized rerun.

```bash
awk '/MemAvailable/ { if ($2 < 70 * 1024 * 1024) { print "Insufficient available memory for TRUE03"; exit 1 } }' /proc/meminfo && systemd-run --user --scope --quiet --unit=oracle-true03 -p MemoryMax=60G -p MemorySwapMax=0 -p CPUQuota=400% env HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 PYTHONPATH=/tmp/oracle-nli-probe-venv/lib/python3.11/site-packages LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib /nix/store/5m9amsvvh2z8sl7jrnc87hzy21glw6k1-glibc-2.40-66/lib/ld-linux-x86-64.so.2 /home/dev/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11 sse_multivector/true_generated_title_probe.py --fixture sse_multivector/navigation-research-v1/true03-fixture.json --fixture-sha256 46867f4041dfd002b22414e802953d702c2b7064b7410c7a2a355c0f3873328e --titles sse_multivector/hdbv2-node-titles-v20-astra-low/titles.json --output sse_multivector/navigation-research-v1/TRUE03 --snapshot /home/dev/.cache/huggingface/hub/models--google--t5_xxl_true_nli_mixture/snapshots/aa6cfe1dd4257853bfdd772992045f41bfc14988
```

Plane tools were unavailable, so no external card status or comment was changed.

**Selected data:** Compact pair-score results, inputs and parameters for `TRUE03` are selected for release as `numerical/pair-scores-cc65be11ce8ebfa5` in the [publication catalog](../../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.
