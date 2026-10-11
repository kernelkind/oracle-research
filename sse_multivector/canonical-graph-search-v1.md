# Graph-search selection

The user approved testing graph traversal in place of global shortlist selection,
trusting the comparison model's returned labels. Selection owns which local–
canonical comparisons to request; prompt development belongs to its own effort.

**Status: failed scalability experiment; work terminated by the user.** The
eight-note construction increased original-call API-equivalent cost by 9.5123%.
The incomplete fifty-note test did not establish lower cost or preserved
hierarchy quality. Its scheduling remained dependent on the chat session,
causing avoidable idle gaps. The user rejected that process and the duplicate
baseline, then ended the work. No construction or automation work remains
active. The selector remains an opt-in experimental implementation; it is not
an adopted replacement for guarded16.

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
counter admits three actual requests; two were used. These are integration
checks. The matched automatic construction screen below supplies cost and
placement evidence; finished-hierarchy quality remains unqualified.

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

The automatic screen completed on 2026-10-10. Both methods processed 32 original
entries from eight notes: 29 admissions, three holds and no equivalence merges.
All transitions have `reviewer: automatic`. Local selections, independently
established meanings, dispositions and complete canonical node arrays match
exactly. No prompt, expected relationship, note membership or finished menu was
edited to produce that match. Both methods reached the entry cap; neither
passed the structural stopping check.

### Result and cost

Graph traversal is **not qualified as a cheaper replacement** by this screen.
Its original-call API-equivalent cost is **9.5123% higher**, despite identical
placement results. The earlier 22-entry snapshot was 3.9914% cheaper; that
partial result did not survive graph growth.

| Measured work | Guarded16 | Graph traversal |
| --- | ---: | ---: |
| Independently established local meanings | 32 | 32 |
| Local-versus-canonical comparisons | 365 | 399 |
| Original provider calls behind the answers, including warmups | 460 | 521 |
| Recorded original warmups | 63 | 90 |
| Original-call API-equivalent cost | $1.3855436 | $1.5173408 |
| Fresh provider attempts during this matched screen | 460 | 76 |
| Exact answer reuses | 0 | 382 |
| Fresh-execution API-equivalent cost | $1.3855436 | $0.1674052 |

The cost ratio is `(1.5173408 / 1.3855436 - 1) * 100`. Native
`summarize-experiments` supplies both totals from validated receipts, including
the original generation behind reused answers. The graph method's lower fresh
execution cost reflects reuse and is **not** an operational-policy saving.
These are saved catalog estimates, not reported subscription cash charges or
quotes for two independently executed future builds.

The complete union reconciles with the irreversible shared counter: **536
actual provider attempts**, zero failed attempts, zero retries, zero missing
usage, and **$1.5529488 API-equivalent**. The counter's 1,024-attempt bound was
not exhausted. All input, cached input, reported cache-write and output tokens
are accounted for; reasoning is included in output rather than charged twice.

| Original-call token type | Guarded16 | Graph traversal |
| --- | ---: | ---: |
| Input tokens | 317,314 | 349,449 |
| Cached input tokens | 825,856 | 908,928 |
| Reported cache-write tokens | 0 | 0 |
| Output tokens, including reasoning | 66,833 | 72,755 |
| Reasoning tokens, already included above | 11,414 | 12,396 |

Traversal avoids 15 baseline comparisons: twelve `neither`, two
`local_contains_canonical` and one `uncertain` answers. It introduces **49
additional comparisons, all answered `neither`**, giving 34 more comparisons
overall. The baseline's bounded shortlist already avoids these additional
negative checks. The graph method keeps unrelated branches available for
possible children, so a `neither` answer does not end the full search.

Batch overhead is also material. There are 63 warmup-eligible native experiments
in the baseline and 145 in graph traversal, sharing just two fixed instruction
prefixes. Native execution warms before a batch's first new provider request;
an all-reused batch dispatches no warmup. The 90 recorded warmups behind graph
answers therefore do not measure every warmup of a fresh, separately executed
graph build. No speculative cost for those absent calls is included. This
qualification cannot turn the observed cost increase into a demonstrated
saving.

### Automatic hierarchy quality

Both untouched graphs have 29 canonical nodes, 30 edges and six roots. All eight
notes are reachable. They contain 23 strictly narrowing edges and seven
equal-note-set edges; six single-note parents remain. C001 has seven children
and C012 has eight, exceeding K = 6. The native audit records 15 structural
violations in each method. Their node meanings, supports, edges, topic groups
and individual routes are identical, but the finished-hierarchy requirements
are **not met**. Existing observed groups are not an independently validated
semantic gold set, and no claim of minimum decisions or global optimality is
made.

No adoption, automatic menu repair or prompt change follows from this screen.
The production default remains guarded16; graph traversal remains opt-in.
Further savings work needs to avoid unnecessary negative comparisons as well
as duplicate batch warmups. This is a next-work suggestion, not authorization
to change construction or dispatch more requests.

### Deferred original-parent pruning

On 2026-10-10 the user agreed that reusing the original parent's known
relationships is worth preserving, but explicitly deferred it:

> we should save it for later, when we can establish transitivity in the compare prompt reliably

The proposed shortcut uses saved comparison answers involving the local node's
mapped canonical parent, alongside the current traversal. For example, suppose
Cooking contains the incoming Steaming vegetables node, Jokes contains Puns,
and saved answers establish both Cooking versus Puns and Jokes versus Steaming
vegetables as `neither`. Transitivity then rules out both possible containment
directions between Steaming vegetables and Puns, allowing that comparison to be
skipped. This is a hypothetical example, not a measured trial result.

Cooking versus Puns being `neither` alone would rule out only Steaming
vegetables containing Puns; it would not rule out the reverse or justify
skipping every descendant of Puns. Missing graph edges are not saved negative
answers. Reused judgments must concern the same fixed meanings.

This remains unimplemented and untested. Revisit it only after reliable Compare
transitivity has been established. No reliability threshold or follow-up test
has been approved. Current selection behavior and prompt ownership are
unchanged; this decision authorizes recording the idea, not implementing it or
making model calls.

### Constructor fix and retained evidence

During `graph-selection-09`, Morning coffee, original entry `5.1`, encountered
an uncertain Food-root comparison before reaching its required mapped Coffee
parent C006. The constructor looked up that unvisited parent's answer and
stopped with `KeyError: C006`. The production fix in `3f9e329e` checks uncertainty
first, preserving the graph and recording an incomplete traversal and a hold.
Its native CLI regression failed with the expected missing-parent error before
the fix. The 79 relevant construction/continuation/policy tests passed at that
source checkpoint.

The final check after synchronizing with oracle main `90c3b61b` encountered a
separate shared-runner interface change. All 79 native integration checks stop
while preparing their old fixtures with `runner.concurrency is no longer
configurable; the internal queue shares 30 requests across experiments`.
They do not reach placement. No broad fixture migration or shared-runner change
was made in this task. All 14 production selector tests pass on the synchronized
source. The failed final integration check is retained in
`/tmp/graph-search-uncertainty-main-tests.log`; the earlier passing check is
`/tmp/graph-search-uncertainty-tests.log`.

The experiment itself completed before that runner update. Every one of the
536 original receipts uses executor SHA-256
`39d9be310f4e375537fd3a29b43eece004c878829a001d58278bddf9985cc5c8`,
matching shared-runner commit `e27660d`; native execution logs retain concurrency
four in both methods. Graph continuation completed at 22:48:24 UTC, and the
shared-runner main reflog records `89cc9e6` landing at 22:51:16 UTC. Thus the
new global queue did not change the trial's model dispatches. Current fresh
preparation requires separately adapting the old concurrency fixtures/specs;
the retained results are not rerun under that new scheduling policy.

The blocked stage resumed automatically through that patched runtime, with
**zero new provider attempts** and unchanged model inputs and receipts. All
other preparation/execution used the retained original task code. The frozen
experiment worktree remains at `4cd99115`; its source bindings were not rewritten
when the runtime fix landed on main. The initial note-limit and automatic
graph-mode inheritance tests failed before their implementation; 109 related
tests plus 38 additional growth/guard/runtime checks passed for that feature.

Ignored native evidence is retained in
`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-canonical-graph-construction-v1/target/graph-search-eight-b98-c69-v1/`:

- `baseline-selection-24/state.json` and `graph-selection-24/state.json` retain
  every automatic placement and held entry.
- Each final stage's `audit-stage.json` retains the exact structural failures
  and routes; earlier stages retain the construction progression.
- `baseline-usage-final.json` and `graph-usage-final.json` retain independent
  native summaries with original-generation sources.
- `all-usage-final.json` reconciles the complete attempt counter;
  `*-usage-final.spec.json` retain the native accounting inputs.
- `*-usage-entry22.json` retain the partial cost result for comparison.
- `graph-roots` is an unused preparation; the executed root candidate is
  `graph-roots-v2`. Unrun preparation is not counted as dispatched inference.

The original task worktree must remain because frozen sources and receipt
references use its absolute paths. No UI was refreshed, no agent was messaged,
and no push was made.

## Matched fifty-note trial

The user authorized the larger automatic construction comparison on 2026-10-10,
specifying **50 notes and ASv6.100**. The
[source definition](shr_single_pair/hierarchy-graph-search-fifty-b98-c69-roots-v1.json)
preserves all fifty original root selections and the same collected corpus.
Every note's original ASv6.100 attribution and every collected source hash were
checked before preparation. Bootstrap-v98 and Compare-v69 retain the exact
prompt bytes and output schemas used by the eight-note trial. New
[bootstrap](shr_single_pair/hierarchy-graph-search-fifty-bootstrap-v1.spec.json)
and [comparison](shr_single_pair/hierarchy-graph-search-fifty-compare-v1.spec.json)
specs omit the retired `runner.concurrency` option; the current shared runner
owns dispatch scheduling for both methods.

Both methods start empty and use the same automatic nomination and existing
placement checks. The
[selection definition](shr_single_pair/hierarchy-graph-search-fifty-selection-v1.json)
scales the earlier four-entry-per-note screen to **200 processed entries**,
including fifty initial roots. Inventory exhaustion or this finite cap is not
finished-menu acceptance. Guarded16 remains the baseline; the candidate uses
the existing opt-in graph traversal. Deferred original-parent pruning is not
implemented. No prompt edits, selected destinations, manual placements or menu
repairs are part of this experiment.

Exact answers are reused through the retained graph-construction worktree's
`target` history, including the earlier eight-note evidence. Fresh execution
and original generation costs remain separate; saved source warmups do not
establish a hypothetical fresh independent build's complete warmup cost.
Native checkpoint accounting includes observed token types, warmups and failures,
and retains missing usage as unknown. The intended full comparison covered graph size,
additional and avoided comparisons, held entries, note groups/routes and the
existing six-choice/strict-narrowing audit alongside total cost.

Status: the user terminated this failed experiment before completion; there
will be no final fifty-note result from this run. The first preflight ran
38 checks: 36 passed and two failed solely because the shared queue changed
parallel dispatch order.
Their production-CLI assertions now allow permutation within a frontier while
retaining the required next-frontier ordering; no selector behavior changed.
All **38 checks pass** on repetition, including native cost summaries. Both
methods share one irreversible 32,768-attempt technical counter; an entry cap
or attempt cap remains an incomplete construction result, not acceptance.
No paid API fallback or rented compute is used.

The additional automatic-selection/policy suite passes **41 checks** after one
equivalent dispatch-order assertion update. Its first run passed 40 checks and
failed only the legacy one-batch assertion's arrival order. The expected two
canonical IDs, completed placement and receipt checks remain enforced; no
production selection or placement code changed. Together the preflight suites
cover 79 passing checks.

Native artifacts remain under
`../oracle-mvp-canonical-graph-construction-v1/target/graph-search-fifty-b98-c69-v1/`.
The task code/spec worktree is
`../oracle-mvp-graph-search-fifty-b98-c69-v1/`; retain it while source hashes and
receipts depend on those paths. The initial unexecuted preparation under that
task worktree's `target/` is not counted as inference. No UI has been refreshed.

The baseline's fifty-root phase has completed. Its saved native root audit
reports 35 nodes, 34 strictly narrowing edges, ten roots, nine unreachable
notes and 30 structural violations. The native root accounting reports two
recovered failures with missing usage; the complete cost is therefore unknown,
and any known-subtotal comparison must retain that limitation.

Once the baseline roots were complete, the graph-root continuation was started
alongside the baseline's deeper-entry construction. It can reuse all completed
baseline root requests; each method's graph and entry order remain independent.
The native continuation ownership lock prevents duplicate execution when the
completed graph-root phase is revisited. Its separate log is
`native-cli-logs/graph-roots-overlap.log`.

The first root divergence occurs at original queue index 24, a Food entry from
note `d54600b5dc41b080741e8eca59156909269d821e05536ab994ce96af4da9c492`.
The preceding 24-root graphs are identical. Guarded16 queries Cookware C008 and
receives `neither`, then holds the incoming entry because another positive
answer would imply containment along the existing canonical path. Graph search
does not query C008: its saved traversal infers `local_contains_canonical` and
admits the entry. Both use the same independently generated local meaning.
This is a concrete difference in observed-versus-inferred coverage, not proof
that either semantic interpretation is correct. Final graph quality and cost
remain pending; matching early roots does not establish final preservation.

Both fifty-root phases are now complete. Native reports retain the following
checkpoint, before either method's deeper-entry construction is complete:

| Measure | Guarded16 | Graph traversal |
| --- | ---: | ---: |
| Original roots processed | 50 | 50 |
| Canonical nodes | 35 | 35 |
| Canonical edges | 34 | 28 |
| Roots / maximum children | 10 / 10 | 9 / 9 |
| Held original entries | 9 | 9 |
| Valid cases, including meaning generation | 707 | 913 |
| Original source calls, including warmups and failures | 809 | 1,133 |
| Original source warmups | 100 | 218 |
| Known original-generation catalog cost | $2.4585984 | $2.9999648 |
| Original calls with unknown cost | 2 | 2 |

The known original-generation subtotal is **22.0193% higher** for traversal.
Complete costs remain unknown; this is not a precise total-cost percentage or
a savings result. Graph's 372 exact answer reuses reduce new execution, not the
observed operational work represented by those answers. Source warmups remain
included, with the fresh-standalone warming qualification above. The graphs
differ despite equal admission counts, and neither root graph meets the final
structural requirements. Evidence: `baseline-roots-audit.json`,
`graph-roots-audit.json` and the two `*-roots-usage.json` native reports.

The completed baseline 100-entry checkpoint reaches all fifty notes, but its
raw graph has fifteen roots, up to sixteen children, five equal-note-set edges
and fourteen structural violations. `baseline-entry100-audit.json` retains
that bounded offline audit; coverage alone is not finished-menu acceptance.

Deeper construction was scheduled concurrently across methods. The coordinator
still depended on this chat session advancing and introduced idle gaps; one
observed gap before fresh requests was approximately 7.5 minutes. The earlier
sequential coordinator was stopped while the
baseline's 60th selected-entry continuation was active. Native ownership
locking rejected the immediate resume while that process was still active;
it does not wait for another owner. The original continuation then finished
normally. After verifying its process had exited, construction continued from
the completed state and the already prepared graph entry; no model call was
canceled or redispatched. Each method still processes its own
automatic entry order sequentially, uses the same frozen inputs and guards,
and shares exact-request history and the irreversible attempt counter.
`native-cli-logs/*-v2.log` retain the lock rejection and preparation;
`*-v3.log` retain the resumed native invocations. The 200-entry comparison was
not completed. The root result is a partial measurement, not a final result.

### Failure and cleanup

The user required uninterrupted automated construction, rejected running a
duplicate baseline when a saved fifty-note hierarchy was already available,
and then instructed this task to stop and be marked as a failure. The
chat-driven coordinator was terminated. Active native continuations finished
their current selected entries; neither arm started another entry. Process
inspection confirmed that no matching construction job remained running.

| Saved stopping checkpoint | Guarded16 duplicate baseline | Graph traversal |
| --- | ---: | ---: |
| Original entries processed | 131 | 65 |
| Canonical nodes | 97 | 47 |
| Held entries | 26 | 12 |
| Latest saved trial | `baseline-selection-081` | `graph-selection-015` |

The shared irreversible attempt counter retains **3,621 charged claims**. It
was not reset or refunded. Saved requests, responses, receipts, intermediate
graphs and logs remain unchanged. Complete fifty-note cost and quality
preservation are unestablished; the higher root-stage known subtotal and its
missing-usage limitation remain as measured evidence above.

The existing ASv6.100 fifty-note benchmark is
`../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/`.
Its completed raw trial is `regrouping-roots-v1`, using Bootstrap-v96 and
Compare-v48. It shares the fifty original root selectors and corpus with this
test, but its prompts and construction history differ. It remains saved
historical evidence; this cancelled task does not claim an isolated policy-cost
percentage against it.

No automated cross-selection command was implemented. The unused automation
worktree contained no task source changes and was removed. The two frozen
experiment worktrees named above remain because source hashes, receipts and
saved evidence use their absolute paths. All earlier task changes are already
integrated into main. No prompt changes, UI refresh, agent-session messages or
push were performed during closeout. This task must not automatically resume.
