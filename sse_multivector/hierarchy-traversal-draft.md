# Hierarchy selection by traversal — draft v23

**Status: algorithm draft.** This records the discussion; it does not change
the constructor, comparison prompt or existing experiments.

## Goal and inputs

Place one selected local node in the canonical hierarchy with fewer comparisons.
Each comparison is local versus canonical, using the existing compare prompt.

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

## Agreed local-level selection order

**Select local roots first, then L2, then L3, continuing one local level at a
time across all notes.** L1 is the root level; each local child is one level
below its parent.

Processing one note's whole level before moving to another note is rejected.
**The proposed replacement is to rotate across notes, taking one local node per
note per round at the current level.** A round means one pass through the notes.
Preserve saved note order within each pass and each note's saved node order.
Take the next unprocessed node at that level from each note; skip notes with
none remaining. Move to the next local level once the current level is exhausted
across all notes, unless the stopping conditions end selection first.

This rotation is a proposal awaiting approval. It sets selection order, not
execution batches; searches can overlap without waiting for a pass to finish.

Use the selected order to start up to three local-node searches under the
concurrent policy below. Apply placements in that same order, finishing
triggered consolidation before applying the next placement.

Do not skip a local child merely because its original parent's canonical node
represents one note. The local child may have useful relationships elsewhere
in the canonical graph, so it remains eligible for ordinary traversal.

The local-level order and stopping conditions below are agreed. Stopping-check
timing is provisionally approved; within-level order remains open. No selection
code or model calls change here.

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

This changes the intended requirement, not the existing implementation or saved
experiment assessments.

## Agreed stopping conditions

**Stop selecting further local nodes when the finished browsing hierarchy meets
both conditions:**

- Every note is reachable individually.
- Every downward step strictly reduces the distinct-note set.

Count a node's own supporting notes and recursive canonical descendants,
deduplicating note IDs. Grouping remains best effort under the consolidation
trigger below. No additional final review or search for unused regroupings or
shortcuts is required before stopping.

These conditions do not claim global optimality or establish relationships for
unchecked deeper local nodes.

## Provisionally approved stopping-check timing

**After each placement and all consolidation it triggered, check both stopping
conditions against the current browsing hierarchy and every note in the selected
corpus.** A complete local level is not required before checking.

If either condition fails, continue construction under the selection and
concurrent-search rules. When both pass:

- Stop starting new local-node searches and dispatching comparison calls.
- Let already-dispatched calls finish and save their answers.
- Keep the current graph unchanged. Save unfinished searches and their existing
  results for later resumption, including completed searches awaiting placement.

On later resumption, reuse exact unchanged answers and check a search against
the then-current graph before placement, as required by the concurrent-search
policy. This timing is approved provisionally for the draft; it is not
implemented or measured.

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

This is an agreed construction rule for the draft, not an implemented change.

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

This validation policy is agreed draft design, not an implemented change. It
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
local node comes from N063. The current filter excludes that canonical node
unless it is the incoming node's mapped original parent. The approved rule lets
normal traversal establish their relationship instead.

Removal of the exclusion is approved draft design, not an implemented change.
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

This original-parent handling is agreed draft design, not an implemented change.
It changes neither a supplied meaning nor a returned comparison label.

## Agreed walk

The local-level selection order, stopping conditions, comparison actions,
shared-node rule, top-to-bottom order, concurrent-search policy, same-note
eligibility, original-parent handling and consolidation rules above are agreed.
The walk below combines them with the provisionally approved stopping-check
timing; within-level selection order remains open.

1. Select the next local node in the selected order. Start its traversal at the
   canonical roots.
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

## Decision still open

- Whether to adopt the proposed rotation across notes within each local level.

## Current implementation

[canonical_graph_search.py](canonical_graph_search.py) currently descends after
`neither`, and the constructor processes one local node at a time. These differ
from this draft's agreed rules. The implementation and its historical results
remain documented in
[canonical-graph-search-v1.md](canonical-graph-search-v1.md).

The existing [`prepare_selection`](canonical_selective_trial.py) prioritizes
missing note coverage, then individual-note access, then similarity-ranked
discovery in schema 2. The approved draft instead uses local levels and saved
order within each note; rotation across notes remains a proposal.

The current selector exposes the whole queued set of eligible comparisons. It
does not defer a queued descendant when a queued ancestor could first settle
its relationship. The draft's top-to-bottom order adds that dependency rule.

[`_eligible`](canonical_trial.py) currently excludes canonical nodes with any
supporting entry from the incoming note, except its mapped original parent.
The graph selector requires that parent to be directly compared even when a
relationship is inferred or ordinary traversal would not reach it. Placement
requires a containing or equivalent answer. The approved draft removes the
same-note filter and the forced direct comparison while retaining the required
parent fit, established by normal traversal or valid inference.

The fixed-meaning comparison input already accepts `local.subject` and
`local.meaning` without original-note evidence. The constructor's
[`_placement` function](canonical_trial.py), however, still builds new nodes
from original note entries. The design above reuses the comparison contract;
synthetic insertion is not currently implemented by this draft.

No implementation changes or model calls have been made for this draft.
