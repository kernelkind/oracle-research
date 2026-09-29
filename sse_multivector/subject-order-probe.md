# Subject-order diagnostic (SOv1)

Isolated feasibility test of combining saved per-post SP hierarchies using
subject-text SSE vectors and OPHAC. It does not change HR02, its masks, node
memberships, prompts, or saved vectors. No LLM calls or paid resources are used.
This is diagnostic code, not an adopted production hierarchy algorithm.

Decision status is centralized in the
[SP-based hierarchy rule register](../docs/planning/release-decisions.md#sp-based-hierarchy-rules)
(HD08–17). HD11's exact same-post combination and HD15's corresponding cycle
policy are implemented in SMv2 below. Saved SOv1 and SMv1 results remain unchanged.
The procedures here document those experiments, not a production policy.

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

## SMv1 — separate mutual subject-matching experiment

For the original conversational explanation, read the
[step-by-step walkthrough](subject-matching-walkthrough.md).

The user approved an isolated end-to-end experiment on the **same six posts**,
using SOv1's saved subject vectors and HR02's original mask vectors. SMv1 does
not run OPHAC, HDBSCAN, a placement model, or a title model. It does not change
SOv1, HR02, the prompts, or any saved source masks. Its settings are provisional
development choices, not validated thresholds or a production architecture.

The saved SMv1 procedure is below. The current
[`subject_matching_probe.py`](subject_matching_probe.py) adds the SMv2 changes
described in the next section; its cross-post search and comparisons are unchanged.

1. For each unique nonempty mask, find the closest mask from another post.
   Keep numerical ties and deduplicate the resulting **post pairs**. This
   uses mask-to-mask cosine only; empty-mask subjects do not supply searches.
2. Within each selected post pair, compare every SP subject-text vector on
   one side against every SP subject-text vector on the other. Empty-mask
   subjects still participate here. Each subject selects its best counterpart
   **within that other post**, not across the entire corpus. Keep ties.
3. A pair must select each other and have subject cosine **>= 0.90** and mask
   cosine **>= 0.80**. Find best choices before checking cutoffs or mask
   availability; do not fall back to a weaker counterpart. If either mask is
   empty, the pair is not merged. The two scores are not blended.
4. Combine connected passing pairs. A–B and B–C can combine A, B, C without
   requiring A–C to pass. Retain every constituent subject, mask, and source
   reference. Matching titles alone never authorize merging. The procedure
   does not repeatedly rematch merged groups or relax its cutoffs.
5. Map the original SP parent–child links onto those groups, deduplicating
   identical links. Links internal to one group remain in the provenance but
   are not displayed as self-loops: the preserved ordering is ancestor-or-equal,
   not SOv1's stricter ancestor-only requirement. If distinct groups form a
   directed cycle, split **every merged group participating in any cycle** back
   into its original subjects, then check again. Do not discard SP links,
   choose one merge to blame, or force additional merges.
6. Export all remaining subjects/groups and their mapped SP links to the
   existing hierarchy browser. There is no additional parent-placement step,
   transitive-edge reduction, equal-post collapse, or membership expansion.
   Disconnected branches and unmatched subjects remain visible. Distinct names
   within a merged group are displayed together, not replaced with a new title.

All 18 empty-mask subject occurrences in this saved sample remain inspectable.
Their original post references are retained; they do not acquire synthetic masks
or vector IDs. The browser accepts explicitly empty selections and displays
"No selected fragments (empty mask)" with the complete source post. Missing
note-mask entries, invalid byte ranges, and missing child highlights still fail
validation. Individual nonempty masks retain their original IDs and byte spans.

The current diagnostic computes small, exhaustive cosine tables locally. This
is not an approved million-post retrieval implementation. The familiar six-post
sample tests mechanical behavior and browsing, not generalization. New posts
would be needed before claiming that the proposed matching rule generalizes.
Whether to adopt the rule or change its cutoffs remains open.

## SMv2 — exact same-post combination

SMv2 adds HD11 before the unchanged cross-post matching procedure:

1. Combine entries only when their post ID, exact subject wording and ordered,
   nonempty source-byte ranges match. Vector IDs or equal selected words alone
   are not the identity test. Empty-mask entries remain separate.
2. Map all original SP links onto these exact combinations. Internal links are
   ancestor-or-equal, not self-loops. If distinct combined nodes form a cycle,
   stop before creating output and report the involved posts and SP numbers.
3. Compute cross-post candidates and passing pairs from the original entries,
   with SMv1's unchanged search, mutual-best rule and cutoffs. Combine their
   connected chains together with the exact same-post combinations.
4. If a cycle appears, undo every participating cross-post merge back to its
   constituent exact same-post groups or singleton entries, then check again.
   Never split an exact combination, discard an SP link, or merge more nodes
   to resolve a cycle. Unrelated cross-post merges remain intact.

Every parent, child, source SP reference and mask ID remains traceable. Shared
children do not create links between their parents. Exact same-post agreement
is not independent confirmation: identical mask requests may reuse one answer.
All remaining export and preservation checks are unchanged. This is an isolated
experiment, not adoption of the matching thresholds or a missing-parent method.
The original SMv1 output remains the input to the separate AVv1 diagnostic.

### Run and inspect

Outputs are ignored artifacts and an existing output directory is never
overwritten. `results.json` contains the nearest-mask searches, post shortlist,
every within-post-pair comparison, accepted cross-post pairs, cycle rollbacks,
and final groups/links. SMv2 also records `same_post_groups` separately, keyed
by original subject indices, and identifies HD11/HD15 in its settings.
`provenance.json` binds the run to source/vector hashes and keeps
all original subject occurrences, SP links, and masks. `summary.json` reports
mechanical counts and checks. `categories.json` is the existing browser format.
The runner verifies source hashes and SSE identities, repeats the calculation
for determinism, and checks that every original SP ancestor relationship is
still represented or internal to a merged group. It performs no inference.

Use a fresh output path for a replay; the saved SMv2 experiment is `run`:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 -m sse_multivector.subject_matching_probe \
  --source sse_multivector/hierarchy-refresh-v1 \
  --probe target/subject-order-v1/run \
  --output target/subject-matching-v2/replay
```

The browser must include the explicit-empty-mask support. Build it if needed:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
nix develop --command cargo build \
  --target-dir target/infomap-review-build \
  --bin sse-subject-navigation
```

Open SMv2 (the earlier baseline remains under `target/subject-matching-v1/run`):

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
target/infomap-review-build/debug/sse-subject-navigation \
  --categories target/subject-matching-v2/run/categories.json \
  sse_multivector/hierarchy-refresh-v1/masked-posts.json
```

Append `--check` for noninteractive validation. Do not enable either display
collapse option. `?` shows original SP references and mask IDs for a node;
`N`, `D`, and `O` retain the existing browser meanings.

Tests exercise the implementation and CLI with small source-bound fixtures:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 -m unittest \
  sse_multivector.test_subject_matching_probe \
  sse_multivector.test_ancestor_cosine_probe
```

`tests/category_empty_masks.rs` covers actual loading and N/D/O rendering of an
empty selection. The existing category/mask/DAG suites cover the preserved
validation and navigation behavior.

## SMv2-100 — unchanged rules on all 100 posts

The user approved expanding the combination experiment before deciding whether
to add a placement stage. SMv2-100 is a separate run of the same SMv2 rules, not
a new matching algorithm. It reuses the saved 100-post SP/MP outputs and 1,674
mask vectors. All 2,383 subject occurrences remain, including 252 empty masks.
There are 1,702 distinct subject texts: 91 existing SSE encodings are reused and
only the remaining 1,611 are encoded locally. No SP, MP, title or frontier
placement calls are part of this experiment. The six-post outputs stay fixed.

`subject_matching_probe prepare` now prepares source-bound inputs and missing
subject encodings without running inference. Omit `--posts` to include every
post; an unidentifiable post causes an error rather than silent omission.
`--reuse-probe` references existing vector batches and their original receipts.
It does not create a synthetic combined worker receipt. Both reused and new
batches are checked for matching SSE model/runtime identity and source hashes.
A fully cached preparation needs no worker run.

The saved inputs are under `target/subject-matching-100-v1/inputs`; the combined
hierarchy is written separately under `target/subject-matching-100-v1/run`.
The algorithm ID remains `SMv2`; `SMv2-100` identifies this corpus-sized run.
Preparation and matching can be reproduced in fresh directories:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 -m sse_multivector.subject_matching_probe prepare \
  --source sse_multivector/hierarchy-refresh-v1 \
  --reuse-probe target/subject-matching-100-v1/inputs \
  --output target/subject-matching-100-v1/replay-inputs && \
python3 -m sse_multivector.subject_matching_probe \
  --source sse_multivector/hierarchy-refresh-v1 \
  --probe target/subject-matching-100-v1/replay-inputs \
  --output target/subject-matching-100-v1/replay
```

For the initial new encodings, the worker was recovered byte-for-byte from
Git commit `6b788656eeb46c03c19ff0540d53092e5a336f97`, with SHA-256
`6e1eb74c1d89fff98bd2196ddea6a6af32d62c5395a664a34afe2bfbea7224cb`.
The ignored snapshot is `target/subject-matching-100-v1/encoder-source/worker.py`.
This is the version used for the saved mask and six-post subject vectors; the
current worker has since changed. The same CPU configuration, checkpoint,
base-model files and recorded runtime versions were used. The original input
protection correctly refuses a replay against changed worker source; no old
hashes were rewritten. A fresh fully cached six-post preparation reproduced
the saved SMv2 results, summary and browser input byte-for-byte.

The next evaluation is the larger hierarchy's browsing structure. No new
parent links, head-comparison policy, display collapsing or manual repairs are
approved by this expansion. More data can change nearest-mask post selection
and matching chains under the unchanged rules; the six-post graph is a saved
baseline, not a constraint that its merges must survive the larger run.
