# RSE01 execution

Run on local CPU, September 12, 2026. No training or paid resources.

## Source and input identity

- Checkpoint: `binwang/RSE-RoBERTa-large-10-relations` at `b1da9ad30f7c5f943ea35d3c2685df0862ad3cb5`.
- Weight file SHA256: `76ae8a51d65f60b70b526954ad047bc72398d80681ba5b80a8c8dcfa39b87e39`.
- Author source revision: `2fc202227bf95bd12ce3b41acbbfefb1a45c983f`.
- Fixture SHA256: `d3efece72ebf6f03e4c0b5fe9b1c588fbece361b00599b34389c242a699c2c35`.
- Input-record SHA256: `886ea3f362d95c02077f2c7b7c7cd45370e29d86b7120f4de29c9d4a7d3ed277`, identical to HRC03.

Package versions and every downloaded-file hash are in [config.json](config.json). The 1.42 GB weight download used one worker, a 2 GiB/no-swap scope, and no authentication token. No GPU or paid provider was used.

## Test-first check

The new test module initially failed because `rse_category_probe` did not exist. After implementation, all six new tests and 17 unchanged regression tests passed:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector
env LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib /tmp/oracle-nli-probe-venv/bin/python -m unittest test_rse_category_probe test_hierarcaps_category_probe test_hierarcaps_mask_probe
```

## Main invocation

Executed from `/home/dev/src/notedeck_worktrees/algos/oracle-mvp`:

```bash
systemd-run --user --scope --quiet --unit=oracle-rse01 -p MemoryMax=6G -p MemorySwapMax=0 -p CPUQuota=200% env HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib /tmp/oracle-nli-probe-venv/bin/python sse_multivector/rse_category_probe.py --fixture sse_multivector/navigation-research-v1/hrc03-fixture.json --output sse_multivector/navigation-research-v1/RSE01 --snapshot /home/dev/.cache/oracle-rse/models--binwang--RSE-RoBERTa-large-10-relations/snapshots/b1da9ad30f7c5f943ea35d3c2685df0862ad3cb5
```

The command now refuses to overwrite RSE01. Use a new output directory for reproduction. Its output recorded 355,369,984 parameters, 1,024 dimensions, 5.64810058567673 seconds encoding, 13.347875773906708 seconds total, and 3,133,396 KiB peak RSS.

## Compatibility and numerical details

The runner reproduces author inference with the standard `RobertaModel` plus the checkpoint's trained linear/tanh projection. All encoder tensors load strictly; exactly the three expected head tensors remain. The old persisted position-ID buffer is validated against the architecture's fixed sequence before omitting it from the modern nonpersistent state. No trained tensor is discarded or replaced by a random initialization.

The model runs in float32, with eager attention and evaluation/inference mode. Raw embeddings are saved before any normalization. Saved pair scores use Python double-precision arithmetic on those float32 values; the author's example uses float32 tensor cosine. Independent verification records the numerical difference rather than claiming bit-identical scores across arithmetic implementations.

No relation or threshold selection is performed. Relation 0 is the released entailment relation, and scoring uses child-to-parent direction. The symmetric SentEval maximum-of-both-directions helper is deliberately not used.

## Rebuild summaries

```bash
python3 sse_multivector/navigation-research-v1/RSE01/analyze.py
```

This reconstructs `analysis.json` and `CASES.md` from saved inputs and scores; it does not run a model. Interpretation remains separately written in `RESULTS.md`. The independent verifier and its output are saved alongside these files.

## Independent author-implementation verification

`verify.py` loads pinned, hash-checked author `model.py` and `model_utils.py`. The unused `from turtle import forward` import is removed only in memory to avoid the irrelevant GUI dependency; inference code is otherwise unchanged. It instantiates `RoBERTaForRSE`, loads the full checkpoint strictly, and invokes `sentemb_forward` through the author class. The legacy fixed position buffer receives the same explicit value check as in the primary runner.

All 180 embeddings and the relation are bit-identical. Independent double-precision score replay differs by at most 3.997e-15. Float32 author cosine differs by at most 2.385e-7; every matched and mixed-wording decision retains the same sign. Original artifact hashes are unchanged. The verifier's model process ran only after the primary process exited.

```bash
systemd-run --user --scope --quiet --unit=oracle-rse01-verify-replay -p MemoryMax=6G -p MemorySwapMax=0 -p CPUQuota=200% env HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib /tmp/oracle-nli-probe-venv/bin/python sse_multivector/navigation-research-v1/RSE01/verify.py
```

The verifier fetches and hash-checks the small pinned author source files on each run; model weights remain offline. It prints its report without overwriting the saved verification. Full details are in `verification.json`.
