# ACv1 — mask-to-ancestor cosine curves

This diagnostic plots `cosine(saved mask vector, saved subject-text vector)`
along a selected, original per-post SP path, from its root (depth zero) through
B itself. It uses SOv1's existing subject encodings and HR02's original mask
vectors. It performs no inference, grouping, merging or placement.

Each case specifies an exact mask ID and one SP occurrence of B. Other
occurrences of the same subject wording may have different ancestor paths;
this diagnostic does not silently combine them or claim to search all branches.
Paths are chosen explicitly for illustration, not by nearest-neighbor retrieval.
All tied maxima are reported. A maximum is not a containment/equivalence
judgment or an approved parent. No threshold has been selected.

The six initial cases were selected before reading their cosine curves: three
bread masks against the same sourdough branch, the rave post's Coffee shops
mask against two different branches, and a Cranberries mask against an
ingredient branch. These are examples, not a scored accuracy benchmark.

Run from the repository root, using a fresh output directory (the initial
artifacts use `ancestor-curves-v1`; this command uses `ancestor-curves-replay`):

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
env LD_LIBRARY_PATH=/nix/store/1xw5xccqqh1xw3mvd70hyil6x418wxcm-gcc-14.3.0-lib/lib \
  uv run --offline --no-project --python python3.13 \
  --with 'numpy==2.5.2' --with 'matplotlib==3.11.1' \
  python -m sse_multivector.ancestor_cosine_probe \
  --source sse_multivector/hierarchy-refresh-v1 \
  --probe target/subject-order-v1/run \
  --case V0216:N037:1.1.1 --case V0217:N037:1.1.1 \
  --case V1146:N037:1.1.1 --case V0070:N065:1.1.1 \
  --case V0070:N065:5.1.1 --case V0517:N072:4.2.1 \
  --output target/subject-order-v1/ancestor-curves-replay
```

Outputs stay ignored under `target/`: `curves.json` contains exact scores and
source hashes; `curves.png` and `curves.svg` label every subject and mask ID;
`index.html` adds each complete source post with the mask marked inline.
Inputs, raw-vector hashes, SSE identity, and mask/subject provenance are checked
before plotting. Existing output directories are refused.

Run the standard-library tests with
`python3 -m unittest sse_multivector.test_ancestor_cosine_probe` from the repo
root. The initial run also received a visual inspection of the rendered PNG.
