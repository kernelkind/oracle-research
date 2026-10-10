# Candidate-selection tests from the completed ASv6.100 build

Current selection results and corrected original-call accounting are recorded in
[the ASv6.100 selection study](candidate-ranking-as100-study-v1.md). The frozen
cases and expected outcomes are unchanged.

**Prepared:** `selection-as100-fifty-v2`, 120 placement cases from the completed
50-note ASv6.100 / Bootstrap-v96 / Compare-v48 construction. These are added
alongside the [177 historical ASv6.48 cases](selection-regressions-v1.md), which
remain deprecated for current-pipeline validation. Both builds use the same
50 source notes; 297 saved placement cases do not mean 100 independent notes.

Each case selects canonical nodes for comparison with one incoming local node.
It contains several saved pair answers, rather than being a single pair test.
There are 98 additions, eight equivalences and fourteen held placements. The
initial bootstrap and three producer-review holds have no comparison selection;
they remain fixed within the ordered 124-entry construction check.

Expected relationships and holds come from the saved construction, not new
human judgments. No case is labeled human-reviewed. ASv6.100 source provenance
is established, but reproducing its construction is not semantic certification
or acceptance of its browsing hierarchy. No teacher calls or new encodings were
made to prepare this suite. Construction, prompts and the hierarchy UI were
not changed.

## Frozen inputs and checks

The raw completed source is
`target/hierarchy-as100-b96-c48-fifty-note-v1/regrouping-roots-v1/state.json` in
`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-bootstrap-v88-three-note-v1`.
Its immutable native snapshots preserve the local heading, meaning, original
post and ancestor evidence, existing canonical graph, original comparison
answers and receipts. Protected source hashes are checked before evaluation.
The shaped browsing menu is not used to derive expected relationships.

The [existing evaluator](selection_regressions.py) still runs the production
placement, contradiction, implication and receipt-accounting functions. It
checks each case against its original graph, then checks the construction in
order using only retained answers. The ordered check stops at the first graph
difference or required unknown answer. Ancestor routes can preserve a relationship
without retaining every redundant direct edge. Unqueried pairs stay unknown.

Preparation now accepts saved construction without requiring auxiliary vectors.
The new suite therefore uses the original shortlist through `--method baseline`,
or accepts a new ordered selection through `--selection-report FILE`. Such a
report must contain the frozen `state_sha256` and `steps`, each with its original
`index` and unique, eligible `queried` canonical IDs. All 120 cases must be present
exactly once. The existing mapped-parent rule is preserved. Built-in alternative
vector rankings require qualified auxiliary vectors; old ASv6.48 vectors must
not be attached to this ASv6.100 suite.

[`--method graph-search`](canonical-graph-search-v1.md) traverses the canonical
graph using reached saved comparison labels instead of a ranked shortlist. It
needs no vectors and has no shortlist cap. The same eligible/mapped-parent and
native placement checks remain in force; unsaved frontier comparisons stay
pending and prevent an overall savings claim. The active constructor has not
yet adopted this selector.

## The explicit agent-review hold

Entry 20, incoming **Food**, was held by an explicit agent review of sixteen
saved answers. The incoming meaning was treated as excluding drinks against
C001 and C019, while including Coffee against C006. The reviewer preserved the
graph rather than forcing a preferred answer or changing meanings.

This review stopped placement before another implied comparison was requested.
The missing comparison is not assigned a guessed answer. The suite separately
records the original review reason, comment, agent attribution and evidence IDs.
It carries the stop as `source_review_hold` only when every original comparison
supporting that review survives the new selection. A native contradiction can
independently preserve the hold. Otherwise, missing review evidence is unresolved.
This is neither an automatic native guard success nor human semantic gold.

## Cost measurement

The frozen native `usage-v2.json` supplies the original generation accounting.
The evaluator verifies its inventory hash, comparison-phase coverage and exact
original receipt lines, then recomputes its token counts and cost using native
functions. The known original API-equivalent subtotal is **$7.296504**; fourteen
failed attempts lack usage, so the full total remains unknown.

A proposed selection is priced from its saved comparison/verification attempts.
All other recorded original work remains in the denominator and candidate total,
including meaning generation, warmups and archived/replayed construction work.
Reuse is not counted as new sampling or policy savings. These are conditional
saved-token cost projections, not measured savings from a new complete build.
Do not pool this cost with the historical build's different accounting scope.

## Offline verification and repeatable use

The original sixteen-candidate selection reproduces 119 cases through native
checks and one through its explicit source review. All 124 entries reproduce in
order. The old suite still reproduces all 177 cases and 181 entries. Forty-four
related unit tests pass. Baseline projected cost change is zero.

The new immutable suite and baseline report are ignored artifacts in
`target/selection-regressions-v2/as100-fifty/`, named `suite-v2.json` and
`baseline-16-v2.json`. Earlier preparation/replay artifacts are preserved there
separately. The historical baseline recheck is
`target/selection-regressions-v2/historical-baseline-16.json`.
The research worktree remains because frozen sources use its absolute paths.

Repeat the new baseline with a fresh output path:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-candidate-rankings-v1
env LD_LIBRARY_PATH=/nix/store/1xw5xccqqh1xw3mvd70hyil6x418wxcm-gcc-14.3.0-lib/lib:/nix/store/ri9paa3mri4kqakljak8ldvbcp7lpmif-zlib-1.3.1/lib OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
  ../oracle-mvp-scalable-hierarchy-v12/target/sh3-worker-env/bin/python \
  sse_multivector/selection_regressions.py evaluate \
  --suite target/selection-regressions-v2/as100-fifty/suite-v2.json \
  --method baseline --limit 16 \
  --output target/selection-regressions-v2/as100-fifty/baseline-16-repeat.json
```

Use `--selection-report FILE` instead of `--method`/`--limit` to test a new
selection. Both suites are visible development data, not untouched final tests.
Any end-hierarchy quality claim still needs semantic and browsing review.
