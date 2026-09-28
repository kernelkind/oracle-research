# Subject-order diagnostic (SOv1)

Isolated feasibility test of combining saved per-post SP hierarchies using
subject-text SSE vectors and OPHAC. It does not change HR02, its masks, node
memberships, prompts, or saved vectors. No LLM calls or paid resources are used.
This is diagnostic code, not an adopted production hierarchy algorithm.

## Fixed scope

- Source: `hierarchy-refresh-v1`; posts N004, N015, N037, N038, N065, N072.
  Three bread posts and three coffee-shop posts; **all** their subjects remain.
- Each saved subject occurrence starts separately, including empty-mask subjects.
  Original post text, SP numbering, masks and mask-vector IDs remain traceable.
- Exact subject strings share one SSE encoding, not one graph entry. All graph
  merges are made by the same algorithm; no equality decisions are supplied.
- Standalone subject text, fully selected, goes through the existing
  `worker.py` with HR02's checkpoint, model, CPU settings and runtime versions.
  Original contextual mask vectors are not recomputed or used as distances.
- Distance: `1 - cosine`, float64 computation from the worker's float32 vectors.
  Distances below `1e-12` become zero to remove numerical roundoff.
- OPHAC 0.5.4, upstream `HACUntied_python`, complete linkage: group distance is
  the largest constituent pair distance. Ties use first minimum in stable input
  index order. This is one deterministic sequence, not exhaustive tie exploration
  or optimization of the paper's global objective.
- Constrained run: saved immediate SP edges, with transitive reachability checked
  by OPHAC after every merge. Multiple parents survive.
- Control: identical vectors, ordering and linkage, but no ordering constraints.
  Saved SP edges are mapped onto its groups **for diagnostics only**.
- Save every merge, membership, mapped SP edge, original-ancestor collapse, cycle
  check and newly implied relationship. Repeat computation to check determinism.
  Fixed distance snapshots are observations, not an approved stopping threshold.

Stock OPHAC treats arrows as **strict**: it cannot combine an ancestor with its
descendant even if those subjects are equivalent. SOv1 does not implement the
more permissive ancestor-or-equal requirement or edit the SP to work around it.
Preserved ordering does not prove that merged subjects have equivalent scope;
a merge can introduce semantically wrong relationships without making a cycle.
It also cannot invent missing broad subjects or independently discover new
parent placements. Its merge-history tree is **not** the browsing hierarchy.
The dense, small-sample implementation is not a million-post scale proposal.

## Reproduction

Generated artifacts and the external dependency belong under ignored `target/`.
Prepare refuses an existing output directory; collect refuses existing results.
Use a fresh output directory for an intentional independent execution. Source
hashes, worker receipts, Python/NumPy versions and OPHAC source hashes accompany
the outputs. The package is LGPL-3.0 and is not vendored into Git.

On Anvil, obtain the upstream Python implementation without compiling its
optional C++ extension:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
mkdir -p target/subject-order-v1/deps && \
curl --fail --location --silent --show-error \
  https://files.pythonhosted.org/packages/1f/68/151ced1b2dbebc3fbae4fc5a29dfd7367da23ad1005fc13b32cc7ad96a6f/ophac-0.5.4.tar.gz \
  -o target/subject-order-v1/deps/ophac-0.5.4.tar.gz && \
test "$(sha256sum target/subject-order-v1/deps/ophac-0.5.4.tar.gz | cut -d ' ' -f 1)" = \
  3e370da1af44bfb3b3be6baccb2eaacb8fc9c3eed962deff3898fe68a88df1ed && \
tar -xzf target/subject-order-v1/deps/ophac-0.5.4.tar.gz -C target/subject-order-v1/deps
```

Prepare and encode (existing SOv1 uses `run`; this reproduction uses `replay`):

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 -m sse_multivector.subject_order_probe prepare \
  --source sse_multivector/hierarchy-refresh-v1 \
  --posts N004 N015 N037 N038 N065 N072 \
  --output target/subject-order-v1/replay \
  --protect target/hierarchy-build-v1/hr02-parent-child-astra-masks-v3-view/graph.json \
    target/hierarchy-build-v1/hr02-parent-child-astra-masks-v3-view/memberships.json \
    target/hierarchy-build-v1/hr02-parent-child-astra-masks-v3-view/categories.json && \
env LD_LIBRARY_PATH=/nix/store/1xw5xccqqh1xw3mvd70hyil6x418wxcm-gcc-14.3.0-lib/lib \
  OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false \
  uv run --offline --no-project --python python3.13 \
  --index https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match \
  --with 'torch==2.13.0+cpu' --with 'transformers==4.57.1' \
  --with 'tokenizers==0.22.2' --with 'numpy==2.5.2' --with 'networkx==3.6.1' \
  python sse_multivector/worker.py target/subject-order-v1/replay/worker-config.json
```

Collect and test:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
export LD_LIBRARY_PATH=/nix/store/1xw5xccqqh1xw3mvd70hyil6x418wxcm-gcc-14.3.0-lib/lib && \
export PYTHONPATH="$PWD/target/subject-order-v1/deps/ophac-0.5.4/src" && \
uv run --offline --no-project --python python3.13 --with 'numpy==2.5.2' \
  python -m sse_multivector.subject_order_probe collect --output target/subject-order-v1/replay && \
uv run --offline --no-project --python python3.13 --with 'numpy==2.5.2' \
  python -m unittest sse_multivector.test_subject_order_probe \
    sse_multivector.test_worker sse_multivector.test_fine_segmentation_encoder
```

The existing run's machine-generated evidence is in
`target/subject-order-v1/run/{inputs,results,summary}.json`, with its worker
receipt in `worker-result/worker-receipt.json`. Agent interpretation is separate
in `assessment.md`; it is not ground truth or user approval.

Sources: [paper](https://arxiv.org/abs/2004.12488),
[upstream implementation](https://github.com/danielbakkelund/ophac),
[pinned release](https://pypi.org/project/ophac/0.5.4/).
