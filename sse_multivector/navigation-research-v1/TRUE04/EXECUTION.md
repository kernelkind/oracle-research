# TRUE04 execution record

The approved [TRUE04 plan](../TRUE04-PLAN.md) completed one offline CPU run over all 3,660 ordered pairs of distinct source group IDs. This record documents execution and provenance, not a new semantic assessment.

## Frozen inputs and decisions

The source was `sse_multivector/hdbv2-node-titles-v20-astra-low/titles.json`, preserved byte-for-byte as [titles.json](titles.json), SHA256 `424ffe683fe5fdb3de152cfc6fa09496dfef9fdef422e7a22618b28cc1e20716`. Its 61 groups have 58 distinct title strings: repeated Food, Coffee and Bitcoin titles remain separate groups. There are 1,830 unordered group pairs and 3,309 unique model-input strings. No titles or memberships were changed.

Each row asks **A contains B?**: does belonging to B warrant belonging to A? B is the premise and A the hypothesis, with the exact input:

```text
premise: This text is about {B}. hypothesis: This text is about {A}.
```

Only the exact title strings enter this text. IDs remain row metadata; masks, source notes, expected answers and review explanations are absent. [inputs.json](inputs.json) has SHA256 `e4e118d4ac430ea74dade05f6c3135a8ecce574490f47af9b2463df7609ac17c`.

[started.json](started.json) records the input and four source-file hashes. The runner froze those files before checkpoint hashing/loading and refused an existing output directory. The frozen copies are `true_all_titles_probe.py`, `true_holdout_probe.py`, `true_category_probe.py` and `hierarcaps_mask_probe.py`. Verification found the inference function, scorer and threshold behavior unchanged from TRUE03.

The model was cached `google/t5_xxl_true_nli_mixture`, revision `aa6cfe1dd4257853bfdd772992045f41bfc14988`, with 11,307,321,344 float32 parameters. [model-files.json](model-files.json) records checkpoint/tokenizer hashes; the runner checked all five weight-shard hashes before loading. [config.json](config.json) records no missing, unexpected or mismatched keys, or loading errors.

Two decisions were retained separately:

- Native: complete greedy output `0` or `1`, with EOS required and no cutoff. Tokenization is `0` → `[3, 632]`, `1` → `[209]`; the initial token `3` alone is not a complete No answer.
- Cutoff: `entailment_score > 0.142`, strictly greater than. The score is the full-vocabulary first-output-token probability of token `209`, not the binary-renormalized label-prefix score or a calibrated probability of containment.

Generation used no sampling, one beam, at most three new tokens and seed 0. No input truncation was allowed; the largest input was 43 tokens against a 512-token limit.

## Runtime and resources

The existing Python 3.11.14 runtime used torch `2.8.0+cpu`, transformers `4.57.1`, huggingface_hub `0.36.2`, numpy `2.3.4` and safetensors `0.6.2`. Inference used CPU float32, four threads, one inter-op thread and batches of four (915 batches). No external paid API, model/package download, training or rental was used for this execution.

[resources.json](resources.json) records launch at `2026-09-14 20:27:58 UTC`, 107 GiB available host memory at preflight, and no concurrent large model process. The launch required at least 70 GiB available, then applied a 60 GiB memory limit, zero permitted scope swap and a four-CPU quota. All recorded active-scope samples reported `MemorySwapCurrent=0`. About 12 GiB of host swap was already in use before launch; that is not swap used by this run.

[completion.json](completion.json) records 3,660 completed rows, 4,542.877 seconds for the inference interval and 4,568.646 seconds total (76 minutes 8.646 seconds), including a 25.769-second startup/load interval from `config.json`. These are runner timers, not launch-to-last-observation wall time; the inference interval also includes result-artifact construction. Peak process RSS was 46,387,100 KiB (44.24 GiB). The smaller sampled scope `MemoryPeak` values in `resources.json` are a separate accounting observation, not a replacement for process RSS. The resource record reports successful process exit and an inactive scope, observed at `21:47:27 UTC`.

The exact successful launch command from `resources.json`, run from `oracle-mvp/`, was:

```sh
awk '/MemAvailable/ { if ($2 < 70 * 1024 * 1024) { print "Insufficient available memory for TRUE04"; exit 1 } }' /proc/meminfo && systemd-run --user --scope --quiet --unit=oracle-true04 -p MemoryMax=60G -p MemorySwapMax=0 -p CPUQuota=400% env HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 PYTHONPATH=/tmp/oracle-nli-probe-venv/lib/python3.11/site-packages LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib /nix/store/5m9amsvvh2z8sl7jrnc87hzy21glw6k1-glibc-2.40-66/lib/ld-linux-x86-64.so.2 /home/dev/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11 sse_multivector/true_all_titles_probe.py --titles sse_multivector/hdbv2-node-titles-v20-astra-low/titles.json --titles-sha256 424ffe683fe5fdb3de152cfc6fa09496dfef9fdef422e7a22618b28cc1e20716 --output sse_multivector/navigation-research-v1/TRUE04 --snapshot /home/dev/.cache/huggingface/hub/models--google--t5_xxl_true_nli_mixture/snapshots/aa6cfe1dd4257853bfdd772992045f41bfc14988
```

## Saved evidence and verification

Inputs, frozen source, scores/native token sequences, decisions, configuration, resource records and review/analysis JSON are retained in Git. `first-token-logits.npy` remains local and explicitly Git-ignored: 470,354,048 bytes (about 449 MiB), shape `(3660, 32128)`, float32. Its SHA256 is `f5b4eddd88edb02ccbd970e58cdb02283053190111b6d82877264678f4b7f7c4`, recorded in `completion.json` and [verification.json](verification.json). A Git checkout alone does not include these raw logits or the cached model weights.

The independent integrity review passed without discrepancies. It reconstructed all inputs and input tokens, checked artifact/source hashes and every machine-produced decision/report row, and replayed all 117,588,480 saved finite logits using full-vocabulary softmax in float64. Numeric differences from stored diagnostics were within `2e-15`; every cutoff decision matched the strict rule. It also checked semantic-analysis arithmetic, not the correctness of semantic judgments. No model, torch or transformers was imported for verification, and no inference was repeated.

Verification limits remain explicit:

- First-token logits establish the first greedy token and displayed score. Later-token logits were not saved; complete labels/EOS were checked against saved generated sequences and tokenizer decoding, not independent later-token inference.
- The review checked nonweight model files and the recorded manifest but did not reread or rehash weight shards. Their hashes were checked by the original runner.
- All 44 reused TRUE03 inputs/tokenizations and native/cutoff decisions matched. Only 19 logits rows were bit-identical; the maximum score difference was `6.700754752175797e-7`. This is not a claim of bit-for-bit inference reproducibility or independent new validation.
- Scope exit/resource observations are recorded separately from numerical replay. Arithmetic/integrity checks do not establish semantic correctness or general population accuracy.

Before implementation, the new unlabeled-summary test failed with `KeyError: 'expected'`: the existing report assumed every row had an answer key. The reporting change accepts wholly unlabeled rows while rejecting partial or non-Boolean answer keys. It does not change the shared inference function. New tests exercise the production input builder, source freezing, CLI and reporting paths; no existing approved tests were changed.

Regression checks passed: 42 new/prior TRUE tests under system Python 3; 35 related TRUE01/RSE/Hierarcaps tests under the existing offline cached Python 3.11 environment. With 12 overlapping TRUE01 tests, these cover 65 distinct tests. The module sets were:

```text
python3 -m unittest test_true_all_titles_probe test_true_generated_title_probe test_true_holdout_probe test_true_category_probe
python3.11 -m unittest test_true_category_probe test_rse_category_probe test_hierarcaps_category_probe test_hierarcaps_mask_probe
```

Both ran from `sse_multivector/`; the second used the cached interpreter, explicit loader and package/library paths recorded above, with `OMP_NUM_THREADS=1`. Neither suite loads the TRUE checkpoint.

For reproduction of this record, inspect the frozen inputs/source and recorded hashes first; numerical replay requires the local logits file and does not require loading model weights. Preserve all original artifacts. The command above is historical provenance, not a request to rerun: it must not be executed against this completed output directory. Any separately authorized future inference reproduction needs an unused output path and the same verified cached runtime/model/resources; it must not silently download dependencies or overwrite TRUE04.
