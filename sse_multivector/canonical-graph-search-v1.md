# Graph-search selection

The user approved replacing global shortlist selection with graph traversal,
trusting the comparison model's returned labels. Selection owns which local–
canonical comparisons to request; prompt development belongs to its own effort.

[The selector](canonical_graph_search.py), its saved-comparison evaluator and
opt-in native constructor integration are implemented. `--graph-search` selects
this method in a separate raw trial; it does not change another agent's active
generation trial. Prompts and fixed meanings retain their existing contracts.

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

## Native construction

The constructor accepts `--graph-search` on `prepare-canonical-trial`,
`prepare-canonical-child-trial` and `fork-canonical-trial`. Each frontier gets a
separate native experiment. All frontiers use the same graph, original local
evidence and independently fixed local meaning. Completed phase sources and
receipts are checked again before application. Existing eligibility, mapped-parent,
uncertainty and placement checks remain in place. Positive graph inferences are
recorded separately from actual model answers; they do not create receipts.

An uncertain answer in an earlier frontier holds the incoming entry without
changing the graph, including when its required mapped parent has not yet been
visited. Uncertainty is checked before looking up that parent's answer; no
extra comparison is needed to establish a hold. The retained traversal remains
incomplete rather than claiming answers for unvisited nodes.

`prepare-canonical-trial --note-limit N` takes the first N distinct notes in
the source definition's order, retaining their original root order. It does
not alter the source corpus or choose topics by hand.
`prepare-canonical-selection-trial --graph-search` uses the existing automatic
local-entry nomination and then graph traversal. Subsequent selection trials
inherit graph traversal rather than restoring the nomination configuration's
canonical shortlist. The shortlist still supplies saved subject vectors for
the common local-entry selection rules.

`fork-canonical-trial --at-step INDEX --graph-search` starts before one saved
construction step, retaining the original history and independent meaning. It
preserves the source trial, records its state hash and replaces its active
shortlist configuration only in the new trial. Exact native requests are reused
through the inherited history root. The default preparation mode is unchanged.

For example, this prepares the saved Food dishes placement without inference:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
../experiment-runner/bin/experiment-runner fork-canonical-trial \
  ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/regrouping-roots-v1 \
  --output target/graph-search-placement-new \
  --at-step 19 --graph-search
```

Native GPT-6.1 Sol medium qualification used two saved ASv6.100 placements:

- **Food dishes, entry 19:** four frontiers; sixteen exact answer reuses and
  one new Stockpots comparison. The answer was `neither`; the resulting graph
  exactly matches the original placement. Two provider attempts, including one
  automatic prefix warmup, cost **$0.0066468 API-equivalent** in total. No failures
  or retries occurred. All token types are included by the native usage report.
- **Food preparation, entry 8:** two frontiers; six exact answer reuses, zero
  provider attempts. Equivalence with C005 supplies the existing descendant
  relationship to C008 without another comparison. The resulting graph exactly
  matches the original seven-comparison placement. This demonstrates one
  comparison avoided, not a measured whole-hierarchy API-cost reduction.

Five native CLI tests cover pruning, multiple rounds/resumption, exact reuse,
source tampering and an explicitly required mapped parent that was already
inferable. Sixty-five relevant tests pass. The first behavior test failed on
the absent CLI option before implementation. An initial full test run also had
a fixture setup timeout under concurrent machine load; the rerun passed.

Ignored native artifacts and their frozen task-code references remain in
`../oracle-mvp-canonical-graph-construction-v1/target/graph-search-placement-v1/`
and `target/graph-search-pruning-control-v1/` in that worktree. The shared attempt
counter admits three actual requests; two were used. No additional construction
was dispatched. These are integration checks; full-build cost and hierarchy
quality still need a matched construction trial.

## Matched eight-note trial

The user approved experimental Bootstrap-v98 and Compare-v69 in both methods,
with current ASv6.100 inputs and automated selection. The
[source definition](shr_single_pair/hierarchy-graph-search-eight-b98-c69-roots-v1.json)
preserves the existing fifty-note root definition; native `--note-limit 8`
selects its first eight distinct notes. Bootstrap-v98 is read unchanged from
its owner's retained worktree. The
[bootstrap spec](shr_single_pair/hierarchy-graph-search-b98-bootstrap-v1.spec.json)
and [comparison spec](shr_single_pair/hierarchy-graph-search-c69-compare-v1.spec.json)
freeze GPT-6.1 Sol medium, SSE, prefix caching and concurrency four.

Both arms start empty, establish meanings independently of placement and use
exact native reuse under the same history root. The baseline uses guarded16;
the candidate uses graph traversal. Their common
[local-entry selection definition](shr_single_pair/hierarchy-graph-search-eight-selection-v1.json)
uses the existing schema-2 nomination rules without expected destinations or
memberships. Its finite screen processes at most 32 entries per arm, including
the eight initial roots. An entry cap or inventory exhaustion does not prove
finished-hierarchy quality.

The trial evaluates the untouched automatic graphs: reachability, strict
note-set narrowing, six-choice limits, note routes and meaningful group
membership. The existing finished-menu command needs selected node IDs and
does not automatically optimize menus; no hand-picked menu repairs will be
introduced into this comparison. Structural failures remain failures. Token
and API-equivalent cost accounting must include all token types, retries,
warmups and the original generation behind exact reuse. Lower fresh execution
cost from reuse alone is not a selection-policy saving.

Preparation artifacts are ignored under
`target/graph-search-eight-b98-c69-v1/`. At this checkpoint no model calls have
been made for this trial. The two production CLI tests failed on the absent
options before implementation; all 109 related construction, selection,
graph-search and continuation tests pass.
