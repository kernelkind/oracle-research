# Graph-search selection

The user approved replacing global shortlist selection with graph traversal,
trusting the comparison model's returned labels. Selection owns which local–
canonical comparisons to request; prompt development belongs to its own effort.

[The selector](canonical_graph_search.py) and its saved-comparison evaluator are
implemented. The active hierarchy constructor has **not** adopted this method.
Its existing sixteen-candidate policy remains unchanged. This work makes no
model requests and does not modify prompts or saved canonical meanings.

## Traversal

Create `GraphSearch(nodes, eligible=eligible, required=required)` for one local
node against a fixed canonical graph. Use the constructor's existing eligible
IDs and include its mapped original parent in `required` when applicable.

`candidates()` returns the current frontier. Obtain or reuse source-bound native
comparisons for those IDs, then call `record({id: relation, ...})`. Partial
batches are supported, including a selected request returning after another
answer made its relationship inferable. The caller still accounts for every
dispatched request. Repeat until the frontier is empty. There is no ranking
or shortlist cap. The caller owns native preparation, receipts, concurrency,
graph/meaning bindings and placement checks.

- Start at every canonical root. An ineligible root is traversed without a
  comparison, so its eligible children remain reachable.
- `canonical_contains_local`: follow children to find narrower parents.
- `local_contains_canonical`: skip comparisons with its descendants; the local
  contains them through the existing graph.
- `equivalent`: reuse its ancestor and descendant relationships. Other branches
  remain searchable.
- `neither` or `uncertain`: leave children available. Neither with a parent does
  not exclude the local containing a descendant. Uncertain supplies no
  containment inference; native placement retains its existing hold handling.
- A canonical node is compared at most once, including shared children reached
  through several parents. Explicitly required comparisons still occur even
  when their labels could be inferred.

`result()` separates `queried`, positive graph-derived `inferred` relationships,
and unanswered `pending` candidates. Inferences are **not** fabricated model
outputs or receipts. The selector uses graph storage proportional to nodes and
edges, avoids recursive traversal and does not precompute every node's complete
ancestor/descendant sets. Worst-case comparison count is every eligible node.

## Saved ASv6.100 evaluation

The existing [120-case suite](selection-regressions-v2.md) can now be evaluated
with `--method graph-search`. It requires no auxiliary vectors and ignores the
ranking methods' `--limit`. The selector reads only saved answers it reaches.
Missing answers remain pending and prevent a completed placement/cost claim.
Completed searches go through the same native placement and verification checks
as the other selection methods; those verification requests are still counted.

Results on the frozen ASv6.100 / Bootstrap-v96 / Compare-v48 fifty-note source:

- All **17** searches that finish from existing answers preserve the saved
  placement relationships and graph.
- **103** searches require unsaved comparisons. Across their fixed snapshots,
  2,133 pair slots remain pending; this is not a forecast for a new live build.
- The ordered check reproduces the first **19 of 124** construction entries,
  including non-comparison entries, then stops at the first missing answer.
- The existing sixteen-candidate baseline still reproduces all 124 entries:
  119 cases through native checks and one through its saved source-review hold.
- Total graph-search API-equivalent cost and percent reduction remain unknown.
  No new teacher calls, encodings or semantic review were performed. Saved
  placement preservation is not human approval of hierarchy quality.

For example, the selected local node **Hope that breakfast will energize the
author**, entry 108, now requests canonical **Mental states · C003**. The old
shortlist omitted that pair. Its relationship remains pending, rather than being
assigned a guessed label.

Fourteen selector tests cover branching, multiple parents, eligibility, required
comparisons, equivalence, pending answers, invalid inputs, a finite exact
containment oracle and a 5,000-node branch skipped after one comparison. Fifty-
four related tests pass. Native saved-answer evaluation validates original
source hashes and receipts. Reports are ignored artifacts under
`target/graph-search-as100-v1/`; the current graph-search result is
`graph-search-v3.json` and the baseline is `baseline-16-v1.json`.

Repeat without inference, using a fresh output filename:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
env LD_LIBRARY_PATH=/nix/store/1xw5xccqqh1xw3mvd70hyil6x418wxcm-gcc-14.3.0-lib/lib:/nix/store/ri9paa3mri4kqakljak8ldvbcp7lpmif-zlib-1.3.1/lib OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
  ../oracle-mvp-scalable-hierarchy-v12/target/sh3-worker-env/bin/python \
  sse_multivector/selection_regressions.py evaluate \
  --suite ../oracle-mvp-hierarchy-candidate-rankings-v1/target/selection-regressions-v2/as100-fifty/suite-v2.json \
  --method graph-search \
  --output target/graph-search-as100-v1/graph-search-repeat.json
```
