# Hierarchy selection by traversal — draft v5

**Status: algorithm draft.** This records the discussion; it does not change
the constructor, comparison prompt or existing experiments.

## Goal and inputs

Place one selected local node in the canonical hierarchy with fewer comparisons.
Each comparison is local versus canonical, using the existing compare prompt.

The local node's explicit meaning and the canonical graph stay fixed during
the search. Canonical nodes retain their immutable meanings. Selection trusts
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
different branch. **Compare each canonical node at most once** for this local
node; reuse its answer if another path reaches it again.

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

## Proposed walk

The containment, `neither`, shared-node and equivalence rules above are agreed.
The other steps below carry forward the current traversal behavior as a
starting point for further discussion.

1. Start at the canonical roots.
2. Compare the local node with a reached, eligible canonical node.
3. Follow the returned label using the table below.
4. Continue until no comparisons remain along the branches being searched.
5. Use the resulting relationships for placement, retaining the existing
   constructor's placement checks.

| Returned label | Traversal action |
| --- | --- |
| `canonical_contains_local` | Record the canonical node as a possible parent. Follow all its immediate children to find more specific parents. Its ancestors also contain the local node. |
| `local_contains_canonical` | Record the canonical node as a possible child. Stop descending there; containment of its descendants follows from the existing graph. |
| `equivalent` | Use the existing canonical node. Its ancestor and descendant relationships apply. Stop descending there and continue other branches. |
| `neither` | Stop descending this branch. Continue other branches. |
| `uncertain` | Retain the current constructor's hold behavior: preserve the graph and flag the local node for review. |

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

- Which reached node to compare next, and which comparisons to run concurrently.
- How existing same-note exclusions and the required mapped-parent comparison
  should interact with branch stopping.

## Current implementation

[canonical_graph_search.py](canonical_graph_search.py) currently descends after
`neither`. That differs from this draft's agreed rule. The implementation and
its historical results remain documented in
[canonical-graph-search-v1.md](canonical-graph-search-v1.md).

No implementation changes or model calls have been made for this draft.
