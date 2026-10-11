# Hierarchy selection by traversal — draft v10

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

## Agreed concurrent-search policy

**Allow up to three active local-node searches. Apply placements one at a time,
in the original local-node selection order.**

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
When a local node is placed or held, its slot becomes available for another
selected local node.

Elapsed time and API cost for this policy have not been measured.

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

## Proposed walk

The comparison actions, shared-node rule, concurrent-search policy and
consolidation rules above are agreed. The walk below combines them with the
current root-start and eligibility behavior as a starting point for further
discussion.

1. Start at the canonical roots.
2. Compare the local node with a reached, eligible canonical node.
3. Follow the returned label using the table below.
4. Continue until no comparisons remain along the branches being searched,
   or an `uncertain` answer holds this local node for review.
5. If the local node is not held, wait for its placement turn and check its
   results against the updated graph as specified above. Use the resulting
   relationships for placement, retaining the existing constructor's checks.
6. After a canonical-node addition, finish its triggered consolidation attempts
   before applying the next placement. Other searches can keep running on
   their fixed snapshots.

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

## Decisions still open

- How to order canonical comparisons within each local-node search.
- How existing same-note exclusions and the required mapped-parent comparison
  should interact with branch stopping.

## Current implementation

[canonical_graph_search.py](canonical_graph_search.py) currently descends after
`neither`, and the constructor processes one local node at a time. These differ
from this draft's agreed rules. The implementation and its historical results
remain documented in
[canonical-graph-search-v1.md](canonical-graph-search-v1.md).

No implementation changes or model calls have been made for this draft.
