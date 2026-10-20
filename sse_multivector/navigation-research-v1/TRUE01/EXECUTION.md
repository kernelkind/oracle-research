# TRUE01 execution and verification

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

Run locally on September 12, 2026. No training, paid resources, GPU, quantization, or remote model code. Earlier experiment files were not changed.

## Model and input identity

- Model: `google/t5_xxl_true_nli_mixture`, revision `aa6cfe1dd4257853bfdd772992045f41bfc14988`.
- Loaded parameters: **11,307,321,344**, all float32, evaluation/inference mode.
- All five checkpoint weight hashes matched the published pinned manifest. Every missing/unexpected/mismatched/error list was empty.
- Original HRC03 fixture SHA256: `d3efece72ebf6f03e4c0b5fe9b1c588fbece361b00599b34389c242a699c2c35`.
- Exact prepared inputs and runner hash: `started.json`.
- Model file hashes: `model-files.json`. Packages and loading diagnostics: `config.json`.

Input lengths were at most 39 tokens for the sentence format and 29 for bare descriptions. Nothing was truncated. Each pair’s actual model text and token IDs are preserved in `scores.jsonl`.

## Binary generation detail

The pinned tokenizer encodes `0` as `[3,632]` and `1` as `[209]`. A tokenizer-only preflight caught this before model inference. The original single-token-label assumption was corrected before any prediction was observed.

Classification therefore uses complete native greedy generation, with EOS required: `0` means No and `1` means Yes. Three new tokens allow either canonical answer plus EOS. Other or unterminated output would be unresolved; none occurred.

The same generation call returns raw first-token logits. Their argmax agrees with the first generated token for all 180 inputs. The displayed score is full-vocabulary probability of token `209`. A separate normalized comparison of prefixes `209` and `3` is saved only as a diagnostic; whitespace token `3` is not itself treated as a complete No answer.

## Resource use

The approximately 45.5 GB public checkpoint download used one weight-file worker, a 2 GiB/no-swap scope, and no authentication token. A separate brief, bounded tokenizer-only fetch checked the output encoding while weights downloaded. The weight download took about 32 minutes. No existing cache was deleted.

Inference used one CPU process, four threads, batch size four, a **60 GiB memory limit**, and **no swap**. The 28-logical-CPU host had about 100 GiB available RAM before launch. Four threads were selected before inference, replacing the initial two-thread proposal to avoid unnecessary delay on a lightly loaded host.

- Total runner time including hashing/loading: **428.02 seconds**.
- Generation and result packaging: **385.35 seconds**.
- First batch: **171.1 seconds**, including demand-loading weight pages. Subsequent batches generally took about 4–6 seconds.
- Peak process RSS: **43.62 GiB**. Observed scope memory stayed below its 60 GiB limit, with zero scope swap.

The model process exited successfully and is no longer running. Raw completion measurements (`completion.json`).

## Test-first checks and independent replay

The new test module first failed because the runner did not exist. Added renderer and complete-generation tests likewise failed before those production functions existed. **Twelve new tests and 23 unchanged regression tests pass.** The frozen fixture and all previously tracked experiment artifacts were preserved.

A clean-context independent agent reviewed the frozen expectations before outputs existed, audited the runner, and later reviewed every primary-format disagreement. No subagent performed model inference or altered data.

The separate read-only [verifier](verify.py) imports no production scoring code and loads no neural model. It reconstructs every pair’s direction and serialization from the frozen fixture, retokenizes the actual input strings, decodes complete saved outputs, checks EOS and raw-logit argmax, recomputes scores with NumPy, and independently recounts decisions. All 180 match. Maximum probability replay difference: **5.55e-16**. Artifact hashes and the runner’s recorded hash match. Verification results (`verification.json`).

This verifies the saved calculation and protocol; it is not an independent second model run or proof that our expected semantic labels are universally correct.

## Reproduce

From `/home/dev/src/notedeck_worktrees/algos/oracle-mvp`:

```bash
systemd-run --user --scope --quiet --unit=oracle-true01-repeat -p MemoryMax=60G -p MemorySwapMax=0 -p CPUQuota=400% env HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib /tmp/oracle-nli-probe-venv/bin/python sse_multivector/true_category_probe.py --fixture sse_multivector/navigation-research-v1/hrc03-fixture.json --output sse_multivector/navigation-research-v1/TRUE01-repeat --snapshot /home/dev/.cache/huggingface/hub/models--google--t5_xxl_true_nli_mixture/snapshots/aa6cfe1dd4257853bfdd772992045f41bfc14988
```

Use a new output directory. The runner refuses to overwrite an existing or interrupted run. Run `TRUE01/verify.py` with the same Python/LD_LIBRARY_PATH environment to replay the saved result without model inference.

**Selected data:** Compact pair-score results, inputs and parameters for `TRUE01` are selected for release as `numerical/pair-scores-44261922841cf8b2` in the [publication catalog](../../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.
