# Hierarchy selection by traversal — draft v25

**Status: approved traversal baseline implemented by the standalone
`traversal-v24` constructor, including the v25 single-note-leaf stopping check.
Restricted refinement and automatic redundant-step removal below remain
approved design, not yet implemented.** Stopping-check timing remains
provisional. Comparison prompts and previously frozen experiments retain their
existing contracts. The limited three-note trial is recorded below.

## Goal and inputs

Place one selected local node in the canonical hierarchy with fewer comparisons.
Each comparison is local versus canonical, using the existing compare prompt.

When starting from an empty canonical hierarchy, promote the first selected
local root, with its independently established explicit meaning, as the initial
canonical node. Subsequent selected nodes go through ordinary traversal.

The local node's explicit meaning stays fixed. Each traversal uses a fixed
snapshot of the canonical graph. Other local nodes may be placed while that
traversal runs; its results must be checked against the updated graph before
placement. Canonical nodes retain their immutable meanings. Selection trusts
the returned comparison labels.

The hierarchy assumption is: **each canonical node has a fixed meaning, and
each parent contains its child's entire meaning.** This supplies two shortcuts:

- A local node contained by a canonical node is also contained by all that
  canonical node's ancestors.
- A local node containing a canonical node also contains all that canonical
  node's descendants.

## Agreed next-local-node selection

**Select local roots first, then L2, then L3, continuing one local level at a
time across all notes.** L1 is the root level; each local child is one level
below its parent. These levels belong to the original local hierarchies, not
the resulting canonical graph.

**Rotate across notes, taking one local node per note per round at the current
level.** A round means one pass through the notes.
Preserve saved note order within each pass and each note's saved node order.
Take the next unprocessed node at that level from each note; skip notes with
none remaining. Move to the next local level once the current level is exhausted
across all notes, unless the stopping conditions end selection first.

This rotation sets selection order. Searches can overlap without waiting for
a pass to finish.

Use the selected order to start up to three local-node searches under the
concurrent policy below. Apply placements in that same order, finishing
triggered consolidation before applying the next placement.

Do not skip a local child merely because its original parent's canonical node
represents one note. The local child may have useful relationships elsewhere
in the canonical graph, so it remains eligible for ordinary traversal.

The initial selection order is implemented. The refinement restriction below
is newly approved and not yet implemented.

### Agreed refinement after note coverage

**Once every selected note is represented, select only unused, deeper local
nodes from notes represented by canonical leaves containing multiple notes.**
A canonical leaf has no canonical children. Count its distinct supporting note
IDs; do not count duplicate entries as separate notes. Take the union of note
IDs across all leaves containing more than one note. Only those notes supply
subsequent deeper local selections. Preserve the saved level and round-robin
order within that eligible set, and use ordinary traversal for each selected
node. Recompute eligibility from the current graph as construction proceeds.

A note remains eligible if it belongs to any leaf containing multiple notes,
even when it is individually accessible elsewhere. Before every note is
represented, retain the initial selection rules; this restriction must not
prevent admission of uncovered notes. It changes later-level selection, not
separately required initial L1 processing in a workflow such as the prominence
selection draft.

If a leaf containing multiple notes has no remaining eligible local nodes that
produce a valid split, report it as unresolved rather than claiming completion.
This rule is not implemented by the current constructor.

## Agreed traversal rules

**`neither` stops traversal down that branch. Continue with other branches.**

Stopping one branch does not prevent reaching a shared descendant through a
different branch. **Compare each canonical node at most once while the
comparison inputs remain unchanged** for this local node; reuse its answer if
another path reaches it again. Changed inputs before placement are handled by
the concurrent-search policy below.

Descendants not reached through another branch remain unchecked. The selection
policy does not assign them comparison labels. It does not search the stopped
branch for possible children of the incoming local node.

### Shared-node example

```text
Food
├── Meals
│   └── Breakfast (C3)
└── Morning food
    └── Breakfast (C3)
```

Both occurrences of C3 are the same canonical node. If the local node returns
`neither` with Meals but `canonical_contains_local` with Morning food, stop
at Meals and reach Breakfast through Morning food. Compare with Breakfast once.

If Breakfast returns `canonical_contains_local`, that conflicts with the Meals
answer: Meals would also contain the local node by transitivity.

### Equivalence

**`equivalent` stops only the matched branch. Continue searching other branches.**

Reuse the matched canonical node and its known ancestor and descendant
relationships. Finding an equivalent node does not establish that every useful
parent has already been found elsewhere in the graph.

For example, suppose the existing graph is:

```text
Food
├── Meals
│   └── Breakfast (C3)
└── Morning food
```

An incoming local node is equivalent to Breakfast (C3). If the Morning food
branch remains unsearched, continue there. If Morning food returns
`canonical_contains_local`, it becomes another proposed parent of C3. Reuse C3
rather than creating a second canonical node. Placement still goes through the
existing constructor checks.

### Local contains canonical

**`local_contains_canonical` stops descent at the contained canonical node.
Continue searching other branches.**

Record the canonical node as a proposed child of the local node. The local
also contains that canonical node's descendants by transitivity, so skip those
comparisons. Reuse this known relationship if a descendant is reached through
another branch.

For example, suppose the existing graph is:

```text
Food
├── Breakfast (C3)
│   └── Pancake breakfasts (C4)
└── Dinner (C5)
```

The incoming local node is Meals. If Meals contains Breakfast, record
Breakfast as a proposed child. Skip comparing with Pancake breakfasts: Meals
contains it through Breakfast. Continue with Dinner and other remaining
branches.

### Canonical contains local

**`canonical_contains_local` leads to comparisons with all immediate children
of the containing canonical node.**

Record the canonical node as a possible parent, then follow its children to
find more specific parents. Follow every containing branch: the local node
may have multiple valid parents. The containing canonical node's ancestors
also contain the local node by transitivity.

For example, suppose the existing graph is:

```text
Food
└── Meals (C2)
    ├── Breakfast (C3)
    └── Dinner (C5)
```

The incoming local node is Pancake breakfasts. If Meals contains it, compare
with Breakfast and Dinner. If Breakfast contains it, continue down Breakfast;
if Dinner returns `neither`, stop that branch. If Breakfast has no children,
it becomes a proposed direct parent. Meals and Food remain ancestors through
Breakfast.

### Uncertain

**`uncertain` stops the search for this local node and holds it for review.
Preserve the existing graph and continue processing other local nodes.**

Save the comparison answers and uncertainty reason for review. The uncertain
answer supplies no relationship for traversal or placement.

For example:

```text
Food — contains the local node
└── Meals — uncertain
```

The local node remains unplaced despite the positive Food answer. Stop its
search and retain the answers for review; construction continues with other
local nodes. This retains the current constructor's hold behavior.

## Agreed comparison order within one traversal

**Traverse top to bottom. Compare independent reached nodes concurrently
through the experiment runner.**

Start at the roots. Apply returned labels and exact reusable answers before
sending further comparisons; skip relationships established by valid transitive
inference. The original-parent requirement below also accepts these established
relationships.

For a shared node, resolve unfinished traversal work on its ancestors first.
An already stopped branch has no remaining work along that path and stays
stopped. Independent branches keep moving. Among ready comparisons, preserve
the saved graph's node order. Ordering uses existing parent links; the experiment
runner handles request concurrency.

## Agreed concurrent-search policy

**Allow up to three active local-node searches. Apply placements one at a time,
in the local-node selection order.**

Each search uses a fixed graph snapshot and the agreed traversal rules. A
finished search waits for earlier selected local nodes to be placed or held.
Before placing its result:

1. Check the search against the current canonical graph, including earlier
   local-node placements and synthetic additions made since its snapshot was
   taken.
2. Reuse exact saved comparisons whose inputs remain unchanged.
3. Compare with newly added canonical nodes where traversal requires it, and
   repeat required comparisons whose canonical inputs changed.
4. Keep the graph fixed during these checks and application of this placement.
   Other local-node searches can continue using their own snapshots.
5. Apply the placement through the existing constructor checks, or preserve
   the graph and hold the local node when those checks prevent placement.
6. After a canonical-node addition, finish its triggered consolidation attempts
   as described below before applying the next local-node placement.

For example, three local nodes search concurrently. The first becomes
canonical. Before placing the second, account for the new canonical node and
changed comparison inputs. Before placing the third, account for both earlier
placements. Every comparison remains local versus canonical.

The experiment runner controls model-request concurrency. The traversal policy
limits active local-node searches; it adds no separate comparison-call limiter.
While construction continues, placing or holding a local node makes its slot
available for another selected local node. The provisional stopping policy below
can end scheduling before another search starts.

Elapsed time and API cost for this policy have not been measured.

## Agreed best-effort sibling grouping

**Keep root and child choice counts manageable on a best-effort basis. Six is
not a hard maximum for a finished hierarchy.**

A group exceeding six choices does not by itself prevent stopping or make the
hierarchy unfinished. The agreed trigger below still calls consolidation after
a canonical-node addition leaves six or more siblings. A `null` result or a
rejected proposal leaves the group unchanged; a later qualifying addition can
trigger another attempt.

The constructor uses this best-effort requirement. Audit reports record crowded
groups as warnings; six is not a structural completion requirement.

## Agreed stopping conditions

**Stop selecting further local nodes when the finished browsing hierarchy meets
both conditions:**

- Every note is reachable individually, and every canonical leaf represents
  exactly one distinct note.
- Every downward step strictly reduces the distinct-note set.

Count a node's own supporting notes and recursive canonical descendants,
deduplicating note IDs. Grouping remains best effort under the consolidation
trigger below. No additional final review or search for unused regroupings or
shortcuts is required before stopping.

**Remove a redundant step when its parent and child represent exactly the same
notes in the finished hierarchy.** Preserve individual note access and valid
containment when reconnecting the retained nodes. Equal observed note sets do
not establish equivalent meanings; do not merge meanings or transfer local
support merely because note sets match. Choosing which node to retain and
handling its other branches still require a concrete worked example. Automatic
removal is not yet implemented. The constructor and structural audit now require
every leaf to contain one distinct note. Individual access elsewhere does not
waive an unfinished multi-note leaf; exhausted inventory reports unresolved
construction rather than completion.

These conditions do not claim global optimality or establish relationships for
unchecked deeper local nodes.

## Provisionally approved stopping-check timing

**After each placement and all consolidation it triggered, check both stopping
conditions against the current browsing hierarchy and every note in the selected
corpus.** A complete local level is not required before checking.

Check from L1 onward. If L1 already provides individual access to every note,
every canonical leaf represents one note, and all canonical edges strictly
narrow the note set, stop there. Remaining L1 roots and deeper local nodes
stay unprocessed.

If either condition fails, continue construction under the selection and
concurrent-search rules. When both pass:

- Stop starting new local-node searches and dispatching comparison calls.
- Let already-dispatched calls finish and save their answers.
- Keep the current graph unchanged. Save unfinished searches and their existing
  results for later resumption, including completed searches awaiting placement.

On later resumption, reuse exact unchanged answers and check a search against
the then-current graph before placement, as required by the concurrent-search
policy. The current constructor implements this timing for individual access,
strict edges and single-note leaves. It does not yet automatically remove
redundant steps. The limited trial below does not
establish general hierarchy quality.

## Agreed consolidation trigger

**After every canonical-node addition, call the consolidation prompt for each
of the added node's sibling groups containing six or more nodes, including the
added node itself.**

For a node with a parent, its sibling group is that parent's immediate children.
For a root, the sibling group is all canonical roots. A node with multiple
parents belongs to a sibling group under each parent.

The prompt proposes a synthetic parent to group some of the siblings. A
proposal still needs normal validation before it can change the graph. If the
prompt returns `null`, leave the group unchanged and continue construction.
Try that group again after a later node addition meets the same trigger; do not
retry immediately just because it still contains six or more nodes.

**Adding a synthetic parent follows exactly the same trigger.** Count the
synthetic node together with its own siblings. If that group still contains six
or more nodes, call consolidation again. Repeat after successful additions
while the trigger holds; a `null` result ends attempts for that group until a
later qualifying addition.

The constructor implements this trigger.

## Agreed consolidation timing

**Finish the consolidation attempts triggered by a placement before applying
the next local-node placement.**

1. Apply the local-node placement through the existing checks.
2. For each sibling group meeting the agreed trigger, call consolidation using
   the current parent and immediate siblings with their fixed meanings. For
   roots, there is no parent.
3. If the prompt returns `null`, or its proposal fails normal validation, leave
   that group unchanged and finish this attempt. Preserve the local-node
   placement already made. A later qualifying addition can trigger another
   attempt.
4. If validation permits adding a synthetic parent, apply it and check that
   addition's sibling groups using the same trigger. Complete any further
   attempts triggered by synthetic additions.
5. Once these attempts finish, allow the next local-node placement. Check its
   search against the current graph, including the synthetic additions and
   changed branches, before applying it.

Other local-node searches can continue on their fixed snapshots throughout
consolidation, within the agreed limit of three active searches. Only applying
the next placement waits. The experiment runner still controls model-request
concurrency.

For example, a local-node addition leaves seven siblings. Consolidation groups
two beneath a synthetic parent, leaving six siblings including that new parent.
That synthetic addition triggers consolidation again. If this attempt returns
`null`, keep the six siblings and proceed to the next placement. Its search must
account for the synthetic parent and the changed branches first.

This ordering keeps consolidation's inputs current and makes its resulting
graph available to the next placement. Its effect on elapsed time and comparison
cost has not been measured.

## Agreed synthetic-parent validation

**Use the proposed synthetic topic as the incoming node in the same traversal.
Its proposed children are claims to check, not automatic edges.**

Freeze the consolidation output's title and explicit meaning before comparison.
Supply the title as `local.subject` and the definition as `local.meaning`; each
comparison's canonical side uses the existing node and its canonical branches.
No Bootstrap call is needed: consolidation has already written the definition.
Do not invent an original note or local branch for a synthetic topic.

Start at the canonical roots and use the agreed comparison actions, including
branch stopping, equivalence reuse and transitive inference. Keep the graph
fixed for this traversal and placement, while other local-node searches
continue on their snapshots. The comparison labels establish the relationships;
the consolidation output does not prescribe positive answers.

Before insertion, require all of the following:

- When the offered siblings have a parent, traversal establishes that this
  parent strictly contains the proposed topic. Equivalence with that parent
  would merely add another name for the same level. Roots have no such parent
  requirement.
- The proposed topic strictly contains each nominated child, through a direct
  comparison or valid inference under the agreed hierarchy assumption. A
  pruned or unreached child remains unchecked and cannot supply this approval.
- The established grouping covers at least two of the offered siblings and
  fewer than the whole group. Include any additional offered siblings that
  traversal establishes are contained; do not ignore them to manufacture a
  useful subset.
- The prospective graph passes the existing placement checks, reduces the
  target group's immediate choices, and makes the new grouping edges strictly
  narrow distinct-note sets. Count existing supporting notes and recursive
  descendants once per note; the synthetic topic adds no invented note support.

Check the prospective graph before changing the real one. Route grouped
siblings through the proposed parent instead of retaining their redundant
direct edges in the target group; preserve their other parent branches and
existing ancestry. Existing equivalent nodes are reused under the agreed
equivalence rule, retaining their fixed meanings.

An `uncertain` comparison, an unsupported nominated relationship or a failed
placement/shaping check ends this proposal without graph changes. Save the
proposal and its comparison results for review, preserve the local-node
placement that triggered consolidation, and continue the approved timing
sequence. Do not rewrite the synthetic meaning during validation to force fit.

The constructor implements this validation policy. It
adds no separate semantic-review prompt or exhaustive comparison pass. Required
relationships can reuse exact answers and the same transitive inferences as
ordinary traversal.

## Agreed same-note eligibility

**A canonical node sharing the incoming local node's source note remains
eligible for normal traversal.**

We are comparing the local node's fixed meaning with a canonical node's fixed
meaning. Sharing an original note establishes neither containment nor
equivalence. A canonical node may also carry support from many other notes.
Use the agreed branch rules, exact answer reuse and transitive inference to
avoid comparisons; do not exclude a reached node merely because one of its
supporting entries has the incoming note's ID.

Suppose a canonical node is supported by N001 and N063, and the incoming
local node comes from N063. Normal traversal compares their fixed meanings;
the shared source note does not exclude the canonical node.

The constructor removes this exclusion.
Its API cost and hierarchy effects have not been measured.

## Agreed original-parent handling

**Retain the original-parent placement requirement, accepting a relationship
established by normal traversal or valid inference.**

When present, `mapped_parent` identifies the canonical node representing the
incoming local node's original local parent. Before placing the incoming node,
establish that this canonical parent contains it or is equivalent to it. An
exact saved comparison or valid transitive inference can discharge the
requirement; a new direct comparison is not mandatory.

Do not reopen a stopped branch or append a forced mapped-parent comparison
after traversal. If the required parent relationship is contradicted or remains
unchecked, hold the incoming local node and preserve the graph. A local root
has no mapped-parent requirement. Synthetic proposals retain their separately
agreed target-parent and nominated-child checks.

The constructor implements this original-parent handling.
It changes neither a supplied meaning nor a returned comparison label.

## Agreed walk

The local-node selection order, stopping conditions, comparison actions,
shared-node rule, top-to-bottom order, concurrent-search policy, same-note
eligibility, original-parent handling and consolidation rules above are agreed.
The walk below combines them with the provisionally approved stopping-check
timing.

1. Select the next local node in the agreed order. When the canonical hierarchy
   is empty, promote the first selected local root with its established meaning
   as the seed and proceed to consolidation and stopping checks in steps 6–7.
   Otherwise, start its traversal at the canonical roots.
2. Compare the local node with a reached, eligible canonical node in the
   top-to-bottom order above.
3. Follow the returned label using the table below.
4. Continue until no comparisons remain along the branches being searched,
   or an `uncertain` answer holds this local node for review.
5. If the local node is not held, wait for its placement turn and check its
   results against the updated graph as specified above. Require original-parent
   fit when applicable, using direct answers or valid inference. Use the resulting
   relationships for placement, retaining the existing constructor's checks.
6. After a canonical-node addition, finish its triggered consolidation attempts
   before applying the next placement. Other searches can keep running on
   their fixed snapshots.
7. After the placement and its consolidation finish, check the stopping
   conditions using the provisional timing above. Stop scheduling and preserve
   the graph when both pass; otherwise continue construction.

| Returned label | Traversal action |
| --- | --- |
| `canonical_contains_local` | Record the canonical node as a possible parent. Follow all its immediate children to find more specific parents. Its ancestors also contain the local node. |
| `local_contains_canonical` | Record the canonical node as a possible child. Stop descending there; containment of its descendants follows from the existing graph. |
| `equivalent` | Use the existing canonical node. Its ancestor and descendant relationships apply. Stop descending there and continue other branches. |
| `neither` | Stop descending this branch. Continue other branches. |
| `uncertain` | Stop this local node's search, preserve the graph and hold it for review. Continue processing other local nodes. |

## Food / Meals example

Existing canonical branch:

```text
Food
└── Meals
    ├── Breakfast
    └── Dinner
```

For an incoming local node:

1. Food returns `canonical_contains_local`: descend to Meals.
2. Meals returns `neither`: stop this branch.
3. Do not compare with Breakfast or Dinner through this branch.
4. Continue with other children of Food and other roots, if present.

The Food relationship remains a possible placement. The final placement depends
on the other comparisons. If Breakfast were to contain the local node, Meals
would also contain it by transitivity, conflicting with the Meals answer.

## Current implementation

[canonical_traversal.py](canonical_traversal.py) implements this policy through
the shared experiment runner's `prepare-canonical-traversal`,
`run-canonical-traversal` and `advance-canonical-traversal` commands. Preparation
and explicit advancement are offline. Preparation starts up to three local
searches; advancement collects native answers, applies guarded placements in
selection order and prepares the reached comparisons. The run command performs
this loop automatically using ordinary native runner execution, with one
existing persistent attempt budget shared across all batches and resumes.
It advances when each batch completes, allowing other searches and consolidation
to remain in flight. Graph mutations stay serialized, and a second automatic
driver for the same directory is refused.

Terminal failed or malformed results hold their local entry while other work
continues. Native eligible retries remain unresolved until they finish; an
allowance or pause that interrupts a retry preserves it for resume. Never
relaunch an unfinished batch repeatedly within one invocation. Execution
blockage drains active work, records errors and pending experiment paths in
`run-summary.json`, and returns nonzero without claiming a finished hierarchy.
Resume with the same run command and attempt-budget path. Every failed,
interrupted or retry reservation counts; successful receipts and exact reuse
remain intact. Individual placements need no interactive approval.

After a crash, resume from the atomically saved graph and native receipts with
the same run command. Requests interrupted before their result was saved may
need another attempt; their reservations remain counted. An explicitly reviewed
code fix can resume with `--runner-upgrade-reason TEXT`: record changed code
hashes alongside the unchanged graph hash and use the native execution-upgrade
audit. This does not permit changing frozen posts, prompts, schemas or inputs,
and is refused while native experiments remain active. Existing meanings,
decisions and completed receipts are preserved.

The preparation spec contains `schema_version: 1`, `corpus`, saved `note_ids`
in selection order, `local_schema_version` (1, 3 or 4), `bootstrap_spec`,
`comparison_spec` and `consolidation_spec`. Prompt and schema paths resolve
relative to their original specs and are frozen. Bootstrap and comparison
specs require JSON output schemas. The configured comparison schema selects
either the local/canonical format or the symmetric A/B format. For Compare-v179,
A is the incoming local or synthetic node and B is the selected canonical node;
each receives only its subject and immutable meaning. Translate A/B containment
labels for traversal and graph checks without changing the raw native answers.
Local/canonical prompts retain their recursive canonical ancestor and descendant
input. Graph checks remain active in both formats.
Consolidation uses the `canonical_consolidation` project adapter, which validates
either JSON null or `title`, `meaning` and a proper subset of sibling IDs. Its
spec omits a runner output schema because the runner requires an object at the
top level; the adapter validates the null-or-object contract after the native
response is received.

Unchanged answers are reused before further preparation. Before placement,
searches restart traversal on the latest graph and reuse only identical input
payloads. The prospective graph passes the existing cycle, returned-relation
and settled-answer checks in [`_placement`](canonical_trial.py). Synthetic
nodes retain their native proposal receipt, with no invented note support.
Pending consolidation uses the current siblings. If a synthetic addition changes
a group before its queued attempt starts, that attempt uses the updated group;
it does not leave a duplicate retry queued for after a null result.

After placement and triggered consolidation, the workflow checks individual
note access and strict note-set narrowing across the whole selected corpus.
When both pass, it pauses active runner queues, exposes no new experiments for
dispatch, and retains unfinished searches and already-returned answers. Later
advancement can collect in-flight results without modifying the finished graph.
Exhausting the local inventory while a stopping condition fails reports
`exhausted`, rather than claiming completion. The workflow does not automatically
remove existing equal-note-set intermediates.

There is one constructor and one traversal behavior. `GraphSearch(nodes)` uses
these rules directly, without policy, eligibility or forced-comparison switches.
The former root/child/growth, shortlist and continuation construction paths have
been removed; their implementations remain in Git history. Shared graph checks,
receipt validation and saved-data review tools remain available.

### Three-note automatic trial with Bootstrap-v109 and Compare-v179

The user selected these exact prompts for the first real automatic trial on
2026-10-11. The saved ASv6.100 corpus is an unchanged copy of
`oracle-mvp-shr-pair-correctness-v1/target/bootstrap-asv6.100-regression-refresh-v1/collected/subjects.json`.
Selected original notes, in order: rocket-stove cooking (`99e6a514…`), lamb dinner
(`26749e4b…`) and shrimp risotto (`a7475c94…`). Full IDs and frozen bindings are in
`oracle-mvp-canonical-traversal-three-note-v1/target/canonical-traversal-three-note-v1/traversal.spec.json`
and `trial/state.json`. Execution used the shared stable launcher, GPT-6.1 Sol
medium subscription requests and a persistent 100-attempt safety limit. The
Consolidation-v4 text was copied unchanged from the shaping task; no prompt was
edited or broadly activated.

The automatic command finished with three independent canonical roots: Cooking,
Dinner and Food. Each represents one distinct note, so individual access passes
and the zero-edge graph has no note-set violations. Compare-v179 returned
neither for all three root pairs; its reasons distinguish the required cooking
activity, evening-meal restriction and Food's human-consumer restriction. These
are saved model judgments, not new human gold. Five local entries were selected;
three were placed and two concurrent searches were preserved without placement.
The run stopped during L1. It exercised neither descendant placement nor
consolidation, and therefore does not qualify those behaviors or hierarchy
quality generally.

Native accounting reconciles 15 fresh attempts, including warmups and one
recovered failure, plus two exact answer reuses. There were zero terminal
failures or held placements. Two unrun comparison cases remain paused following
the stopping decision. Known fresh API-equivalent catalog cost is $0.067084;
the complete total is unknown because the failed attempt lacks usage. Receipts,
`run-summary.json`, `audit.json`, `usage.json` and resume state remain in the
ignored task artifacts. The task worktree must remain for those frozen paths.

**Current shaping limitation:** strict note-set narrowing is a stopping check;
the L1-first round-robin selector has no rule targeting equal-note-set edges.
The six-sibling consolidation trigger addresses option count, and cannot be
assumed to remove such edges. This trial has no edges and does not exercise that
limitation. The user subsequently approved the redundant-step removal and
restricted refinement selection recorded above. These updates have not been implemented.
