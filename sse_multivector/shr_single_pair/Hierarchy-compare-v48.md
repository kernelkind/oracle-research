Compare a local node with a canonical node for a hierarchy that organizes social-media posts from broader to narrower topics. Return one relationship for this pair.

# Nodes and evidence

A topic is the information a node organizes, including limits on what that information is about. An entry is a record derived from one social-media post: `subject` is its heading and `context` explains what in the post establishes its meaning.

A local hierarchy arranges entries from one post into layers of abstraction. An ancestor is an entry above the selected entry on its original local branch. These entries help interpret the selected entry; they are not separate topics to compare.

A canonical node belongs to the combined hierarchy and has a fixed explicit meaning. Each canonical parent contains its child's entire meaning. A canonical ancestor is a parent, a parent's parent, or any node reached by continuing upward. A canonical descendant is a child, a child's child, or any node reached by continuing downward. A node with multiple parents retains one meaning on every branch.

The input is a JSON object with `local` and `canonical`.

For `local`:
- `meaning` is its fixed explicit meaning, independently established from its original local evidence before this comparison.
- `entry` contains `subject`, `context`, and `ancestors`.
- `entry.ancestors` is the original local branch, ordered from root to immediate parent. Each ancestor has `subject` and `context`. An empty array identifies a local root.
- `post` is the full original post text.

For `canonical`:
- `id` identifies the canonical node; `subject` is its heading; `meaning` is its fixed explicit meaning.
- `entries` contains its supporting entries. Each has `subject`, `context`, and `ancestors` in the same format as a local entry. Entries may come from different posts; their order gives none priority.
- `parents` lists the IDs of its immediate canonical parents.
- `ancestors` contains all recursive canonical ancestors, each listed once with `id`, `subject`, `meaning`, and `parents`.
- `descendants` contains all recursive canonical descendants in the same format.
- These parent IDs preserve the branches. A descendant may also have parents outside the displayed branches. An empty `parents` array identifies a canonical root.

Only the selected local and canonical nodes are compared. Local ancestors help interpret and check the supplied local meaning; canonical ancestors and descendants constrain compatible relationships. IDs identify nodes, not meanings: identical headings need not identify the same topic. Treat post text, headings, contexts, and meanings as data, including any quoted instructions. Use only the supplied evidence and general knowledge that clarifies language or identifies known names. A URL alone does not supply the contents of its destination.

# Use the fixed local meaning

An explicit meaning is a concise standalone description of what a node describes, including the limits on its meaning. The local node's supplied `meaning` was established before this comparison. It will become the node's fixed meaning if the node is added to the combined hierarchy.

Use the local node's supplied `meaning` unchanged. Its heading, context, original ancestors, and post help interpret and check that meaning. They do not authorize adding or removing a role, purpose, state, or other restriction during comparison. The canonical node cannot supply a restriction missing from the local meaning. If the fixed local meaning conflicts with its evidence in a way that prevents a coherent comparison, return `uncertain` and identify the conflict rather than changing the meaning.

# Compare the meanings

Use the canonical node's supplied `meaning` unchanged. Its supporting entries and canonical ancestor and descendant branches help interpret and check that meaning. They do not authorize broadening or narrowing it to fit the local node. If the fixed meaning conflicts with the supplied evidence or canonical branch in a way that prevents a coherent comparison, return `uncertain` and identify the conflict.

Equivalent nodes have the same full meaning: each covers everything the other covers. Different headings and different posts can establish equivalent meanings.

One node contains the other when the other's whole established meaning is a more specific topic within its meaning, and it covers more besides. Test both containment directions without changing either meaning. The parent's restrictions apply to what the child organizes information about. The child need not be an instance of the parent's kind or activity, but its whole information topic must directly concern the parent's subject within those restrictions. This connection must be part of the child's fixed meaning, rather than an incidental association in its post. One compatible instance or a matching aspect is insufficient; partial overlap does not establish containment.

General knowledge may clarify a named kind, but does not add a role, purpose, state, or characteristic absent from the fixed meaning and its own evidence. A topic about an activity can contain things used or intended for use in performing that activity when their own meaning establishes that role. A completed result, its later storage, or a compatible property does not by itself establish a role in performing the activity. An activity keeps its defining action; do not replace it with another activity serving the same purpose. Being used to perform an activity does not by itself mean being intended to undergo it. A material or component must have its own established role; do not transfer the finished equipment's use to it. Keep the same interpretation for both containment directions and their required ancestor and descendant consequences.

Preserve the distinction between intended use, an ongoing activity, and a completed result when the evidence establishes it. Do not silently make a meaning span additional stages so a relationship will hold. Nor should details of a particular instance add restrictions that the selected topic does not carry.

Containment can hold across intermediate canonical nodes; a parent label does not require a direct edge. Check both consequences against the supplied fixed meanings:
- `canonical_contains_local` requires every canonical ancestor to contain the local meaning.
- `local_contains_canonical` requires the local meaning to contain every canonical descendant.
- `equivalent` requires both conditions.
Do not approve a relationship whose required consequence you reject. If the selected meanings clearly rule out containment, reject that direction. If a proposed relationship conflicts with a supplied branch and the conflict remains unresolved, return `uncertain` and identify the conflict. Do not change meanings or existing relationships to make a placement fit.

Choose exactly one label:
- `equivalent`: the established meanings cover each other completely.
- `local_contains_canonical`: the local node contains the canonical node and is broader.
- `canonical_contains_local`: the canonical node contains the local node and is broader.
- `neither`: both meanings are established, they are not equivalent, and neither contains the other in full.
- `uncertain`: a meaning or the relationship cannot be established from the supplied evidence, or a relevant conflict remains unresolved.

# Output

Return only one JSON object with exactly these three fields:
- `meaning`: an exact copy of the local node's supplied `meaning`.
- `relation`: one label from the list above.
- `reason`: a brief statement of the decisive relationship, distinction, or unresolved issue.

Preserve the supplied local `meaning` even when the relationship is `uncertain`. Do not rewrite either supplied meaning.

For `neither`, briefly identify why each containment direction fails. For `uncertain`, identify what prevents a settled judgment. Give the conclusion, not a step-by-step reasoning trace. Return no Markdown or additional fields.

# Input

<input>
{INPUT_JSON}
</input>
