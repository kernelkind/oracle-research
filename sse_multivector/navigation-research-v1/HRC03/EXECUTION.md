# HRC03 execution

Working directory: `/home/dev/src/notedeck_worktrees/algos/oracle-mvp`.

Pre-score hashes:

- Fixture: `d3efece72ebf6f03e4c0b5fe9b1c588fbece361b00599b34389c242a699c2c35`
- Plan: `f871a4bf1712f24b74a970267d1bd400e0bace12817bc6359b14ab42a999b442`
- Pre-score review: `f05dfec76955fb88779c12aa399b40d652933fd467fa44873c4b5e7360014c28`

The new preparation/scoring tests first failed because the category runner did not yet exist. After implementation, eight category tests and nine unchanged mask tests passed. The category runner uses the original pair-scoring function, and no earlier experiment was rerun or changed.

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector
python3 -m unittest test_hierarcaps_category_probe test_hierarcaps_mask_probe
```

One inference invocation (exit code 0):

```sh
systemd-run --user --scope --quiet --unit=oracle-hrc03 -p MemoryMax=6G -p MemorySwapMax=0 -p CPUQuota=200% env HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib /tmp/oracle-nli-probe-venv/bin/python sse_multivector/hierarcaps_category_probe.py --fixture sse_multivector/navigation-research-v1/hrc03-fixture.json --output sse_multivector/navigation-research-v1/HRC03 --snapshot /home/dev/.cache/oracle-hierarcaps/models--malper--hierarcaps-clip-l/snapshots/e3aa199d94c438f98628c9697a0b64ef5760b03c
```

No network access was needed: the exact checkpoint was already cached. 180 input records plus the empty-string root were encoded. All 32,400 ordered description pairs were saved. Encoding took 1.543 seconds; total runner time, including checkpoint hashing/loading and all-pair scoring, was 10.189 seconds. The process's `/proc/self/status` high-water memory was 741,348 KiB (about 724 MiB). These numbers exclude planning and semantic review. No training, external API inference, or paid compute.

The analysis used only saved embeddings and pair scores. `analysis.json` contains every matched and crossed-wording check with a key explaining each field. For each case, independently varying the broader, narrower, and alternative wording gives 2×2×2 combinations. A positive alternative-minus-intended angle favors the intended parent; a positive intended-minus-alternative cosine favors it by symmetric similarity. Baselines use only token count or distance from the empty-string root. Exact ties are reported separately (numerical comparison tolerance 1e-8); none of the model parent-angle or direction checks were near that tolerance. These diagnostics and their scope were stated in the pre-score plan.

Independent verification is recorded in `verify.py` and `verification.json`; it reconstructs the inputs and numerical results rather than reusing either runner's scoring functions.
