# Saved teacher mask comparison

`teacher_mask_neighbors.py` compares two saved teachers without generating
subjects, masks, titles, or a hierarchy. It uses the ordinary experiment receipt
validation, hierarchy mask preparation, and local SSE worker. No API spending.

The baseline is a saved hierarchy-refresh vector inventory. The candidate is a
completed mask experiment on an exact-text subset of its notes. Empty masks
remain recorded; identical nonempty masks are deduplicated by source positions.
Exact baseline matches reuse vectors. One baseline mask per nonempty candidate
note is replayed to check encoder parity.

For each query note and each reference mask, collection records the highest
cosine over that note's baseline masks and over its candidate masks, retaining
both winning mask IDs. Every query note is excluded from the reference. These
scores are opportunities for connection, not accepted edges, correctness labels,
or a hierarchy-quality metric. More masks provide more chances for a high score.
Resolve the two winning IDs against their respective inventories: identical masks
can have different subject labels in the two arms.

## Usage

Prepare a fresh ignored output directory:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 -m sse_multivector.teacher_mask_neighbors prepare \
  --source sse_multivector/hierarchy-refresh-v1 \
  --candidate sse_multivector/experiments/luna-complete-note-v1/masks \
  --output target/teacher-mask-neighbors-v1
```

Run `worker.py` on the resulting `worker-config.json`, using the baseline's
recorded local CPU environment. The pinned invocation is documented in
[subject-order-probe.md](subject-order-probe.md). Do not substitute another
checkpoint or runtime. Then collect once:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
env LD_LIBRARY_PATH=/nix/store/1xw5xccqqh1xw3mvd70hyil6x418wxcm-gcc-14.3.0-lib/lib \
  OPENBLAS_NUM_THREADS=4 \
  uv run --offline --no-project --python python3.13 --with 'numpy==2.5.2' \
  python -m sse_multivector.teacher_mask_neighbors collect \
    --output target/teacher-mask-neighbors-v1
```

Outputs and experimental interpretation belong in the ignored output directory,
not Git. Preparation and collection refuse existing output files and preserve
the original teacher and reference artifacts.

## September 29 diagnostic

The saved ten-note Astra-low / Luna-max comparison is in
`target/teacher-mask-neighbors-v1/`. It has 301 distinct candidate masks: 77 reused,
224 newly encoded, plus ten replay controls. Controls matched exactly. The fixed
reference consists of 1,461 masks from the other 90 notes. Full numerical results
are in `connections.json`; interpretation and supplemental coffee-shop checks are
in `analysis.md` alongside it.

The diagnostic exposed a shared encoder boundary issue, not evidence that the
teacher chose different text: adjacent `grow` and `nostr` fragments cover the
same bytes as `grownostr`, but `worker.select_token_indices` tests complete-token
containment separately within each fragment. A token crossing that internal
boundary is dropped. This comparison did not change that behavior or repair any
candidate masks. Do not attribute that loss to teacher semantics.
