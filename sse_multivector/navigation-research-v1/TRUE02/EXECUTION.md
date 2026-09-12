# TRUE02 execution and verification

Run locally on September 12, 2026. No training, paid resources, downloads, GPU, quantization, or remote model code. TRUE01 and all earlier artifacts remain byte-for-byte unchanged.

## Frozen identity

- Model: `google/t5_xxl_true_nli_mixture`, revision `aa6cfe1dd4257853bfdd772992045f41bfc14988`.
- 11,307,321,344 parameters; CPU float32; evaluation/inference mode.
- Four threads, batch four, seed zero, deterministic algorithms, unchanged native greedy decoding with at most three new tokens.
- Exact tokenizer: `0` maps to `[3,632]`; `1` maps to `[209]`. Complete generated text with EOS determines native Yes/No. Whitespace token `3` alone is not a No answer.
- Score: full-vocabulary probability of first token `209`. Frozen cutoff: strictly greater than `0.142`.
- Fixture SHA256: `a514757d32adc0c31f859d0d8a912870cec4c7296ee07d231d9edc7608098e21`.
- Inputs SHA256: `cad6f8c463afc25108ebf42f93093773b3c3026601e62d5168bb0b441f171948`.
- Unchanged TRUE01 scorer SHA256: `334f5d7fc2e0ce390be049d828499dd130553ca981544df5a4656953fc525228`.

The 150 prepared inputs, exact fixture bytes, source snapshots, and source hashes were saved before checkpoint hashing or inference. The command required the fixture hash above and refused an existing output directory. The separate fixture review was completed before launch. No pair from TRUE01 was repeated. All five pinned weight hashes match; all checkpoint loading-error lists are empty. Model-file hashes and inference configuration match TRUE01. Maximum input length was 32 tokens; no truncation occurred.

Package versions: torch 2.8.0+cpu, transformers 4.57.1, huggingface_hub 0.36.2, numpy 2.3.4, safetensors 0.6.2.

## Resources

The host had approximately 100 GiB available RAM before launch. One model process ran inside a systemd scope capped at **60 GiB RAM**, **zero swap**, and **four CPUs**. Other processes were not stopped or changed.

- Total runner time, including checkpoint hashing/loading: **266.81 seconds**.
- Generation and packaging: **219.80 seconds**.
- Peak process RSS: **45,542,088 KiB**, about **43.43 GiB**.
- Observed scope swap: **zero**. The configured no-swap limit remained in force.
- Exit status: **0**. The inference scope is inactive; no model process remains.

[Raw completion measurements and output hashes](completion.json). The approximately 19 MiB result directory retains all 150 full-vocabulary first-token logit arrays.

## Tests and independent checks

The new test module first failed with `ModuleNotFoundError: No module named 'true_holdout_probe'`, before the new runner existed. The implementation then passed **12 new tests plus 35 unchanged regression tests: 47 total**. Tests exercise the actual input preparation, serialization, freeze checks, decision rule, aggregation, and report generation. No approved tests were modified. The agent's interim message called the new count thirteen; direct method count and the final full-suite execution establish twelve.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector
env LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib /tmp/oracle-nli-probe-venv/bin/python -m unittest test_true_holdout_probe test_true_category_probe test_rse_category_probe test_hierarcaps_category_probe test_hierarcaps_mask_probe
```

The separate [verifier](verify.py) imports no production scoring code and loads no neural model. It independently reconstructs all 150 expected directions and input strings, checks saved source/model/artifact hashes against TRUE01, retokenizes the inputs, decodes native answers, recomputes full-vocabulary probabilities using NumPy, checks the frozen cutoff, and recounts per-domain/per-kind errors, complete-pair correctness, and score inversions.

All checks pass; maximum score-replay difference is **4.44e-16**. The verifier ran in its own 2 GiB, no-swap, two-CPU scope. [Complete verification result](verification.json).

A separate reviewer also checked all semantic expectations before scoring and, after scoring, inspected every error and the input/scoring snapshots. It found no required answer-key correction or implementation/scoring mismatch. This verifies the executed protocol, not universal semantic truth or a second independent model run.

## Repeat the inference

From `/home/dev/src/notedeck_worktrees/algos/oracle-mvp`, using a new output directory:

```bash
systemd-run --user --scope --quiet --unit=oracle-true02-repeat -p MemoryMax=60G -p MemorySwapMax=0 -p CPUQuota=400% env HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib /tmp/oracle-nli-probe-venv/bin/python sse_multivector/true_holdout_probe.py --fixture sse_multivector/navigation-research-v1/true02-fixture.json --fixture-sha256 a514757d32adc0c31f859d0d8a912870cec4c7296ee07d231d9edc7608098e21 --output sse_multivector/navigation-research-v1/TRUE02-repeat --snapshot /home/dev/.cache/huggingface/hub/models--google--t5_xxl_true_nli_mixture/snapshots/aa6cfe1dd4257853bfdd772992045f41bfc14988
```

The recorded source snapshots support auditing; use the repository runner for this command so its unchanged imports resolve normally.

To verify the saved result without inference:

```bash
systemd-run --user --scope --quiet --unit=oracle-true02-verify -p MemoryMax=2G -p MemorySwapMax=0 -p CPUQuota=200% env HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib /tmp/oracle-nli-probe-venv/bin/python sse_multivector/navigation-research-v1/TRUE02/verify.py
```
