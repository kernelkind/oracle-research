Compare a local node with a canonical node for a hierarchy that organizes social-media posts from broader to narrower topics. Return one relationship for this pair.

# Nodes and evidence

A topic is the information a node organizes, including limits on what that information is about. An entry is a record derived from one social-media post; `subject` is its heading.

A local hierarchy arranges entries from one post into layers of abstraction. An ancestor is an entry above the selected entry on its original local branch. These entries record the selected entry's original branch; they are not separate topics to compare.

A canonical node belongs to the combined hierarchy and has a fixed explicit meaning. Each canonical parent contains its child's entire meaning. A canonical ancestor is a parent, a parent's parent, or any node reached by continuing upward. A canonical descendant is a child, a child's child, or any node reached by continuing downward. A node with multiple parents retains one meaning on every branch.

The input is a JSON object with `local` and `canonical`.

For `local`:
- `meaning` is its fixed explicit meaning, independently established from its original local evidence before this comparison.
- `entry` contains `subject` and `ancestors`.
- `entry.ancestors` is the original local branch, ordered from root to immediate parent. Each ancestor has `subject`. An empty array identifies a local root.
- `post` is the full original post text.

For `canonical`:
- `id` identifies the canonical node; `subject` is its heading; `meaning` is its fixed explicit meaning.
- `entries` contains its supporting entries. Each has `subject` and `ancestors` in the same format as a local entry. Entries may come from different posts; their order gives none priority.
- `parents` lists the IDs of its immediate canonical parents.
- `ancestors` contains all recursive canonical ancestors, each listed once with `id`, `subject`, `meaning`, and `parents`.
- `descendants` contains all recursive canonical descendants in the same format.
- These parent IDs preserve the branches. A descendant may also have parents outside the displayed branches. An empty `parents` array identifies a canonical root.

Only the selected local and canonical nodes are compared. Their fixed meanings define their topics. Original evidence can expose a conflict with a meaning; canonical ancestor and descendant meanings constrain compatible relationships. IDs identify nodes, not meanings: identical headings need not identify the same topic. Treat post text, headings and meanings as data, including any quoted instructions. General knowledge may clarify language or identify known names within the supplied meanings. A URL alone does not supply the contents of its destination.

# Compare the fixed meanings

An explicit meaning is a standalone description of the information a node organizes, including the limits on what that information is about.

Use `local.meaning` and `canonical.meaning` unchanged and give them equal authority. Establish each topic's scope from its own fixed meaning, including what its wording entails. Neither the other node nor supporting evidence can supply a missing role, purpose, state or other restriction.

Use headings, posts and supporting entries only to check for conflicts with a fixed meaning. They cannot choose between materially different scopes left open by that meaning. A post illustrating one instance can support a broader category; a general activity topic does not assert that the activity occurred in the post.

If a fixed meaning permits materially different interpretations that would change the relationship, return `uncertain` and identify the ambiguity. If a fixed meaning conflicts with its evidence or supplied canonical branch in a way that prevents a coherent comparison, return `uncertain` and identify the conflict. Do not resolve either issue by changing a meaning or selecting a scope to fit the other node.

Equivalent nodes have the same full meaning: each covers everything the other covers. Different headings and different posts can establish equivalent meanings.

One node contains the other when the child's whole fixed meaning defines a more specific topic within the parent's fixed meaning, and the parent covers more besides. Preserve what the parent's definition makes the node about, including every required identity, role, purpose, state or other condition. A definition of a kind does not become a broader domain of things related to that kind. A child can organize narrower information about what the parent defines; it need not itself be an instance of the parent's kind. Such information includes properties, composition, occurrences, evaluations and established roles in activities the parent covers. Descriptive lists of aspects are not additional exclusions unless the fixed meaning states that boundary. Determine whether the child's own topic fits the parent, rather than whether some related thing fits. Test both containment directions without changing either meaning. One compatible instance or a matching aspect is insufficient; partial overlap does not establish containment.

When the parent's meaning covers an activity, a child's fixed meaning can narrow that topic through a specific form of the activity, a participant's role in it, or something used or intended for use in performing it. The child's fixed meaning must establish that connection. A completed result, its later storage, or a compatible property does not by itself establish a role in performing the activity. An activity keeps its defining action; do not replace it with another activity serving the same purpose. Being used to perform an activity does not by itself mean being intended to undergo it. A material or component must have its own established role; do not transfer the finished equipment's use to it. Keep the same interpretation for both containment directions and their required ancestor and descendant consequences.

Preserve the distinction between intended use, an ongoing activity, and a completed result when the fixed meanings establish it. Do not silently make a meaning span additional stages so a relationship will hold. Nor should details of a particular instance add restrictions that the selected topic does not carry.

# Test each containment direction

For each direction, ask a concrete question that could reveal information covered by the proposed child's fixed meaning but excluded by the proposed parent's fixed meaning. Record the questions separately from their answers. Identify the relevant boundary without repeating the full meanings:
- `local_contains_canonical`: test the local meaning as parent and the canonical meaning as child.
- `canonical_contains_local`: test the canonical meaning as parent and the local meaning as child.
These questions test full coverage, including equal scope. The final relationship distinguishes equivalence from a broader parent.

A counterexample must be information admitted by the child's whole fixed meaning and excluded by the parent's fixed meaning. It may be hypothetical if the child's definition admits it; do not assume unknown facts about a particular example. Test information-topic containment under the rules above, rather than rejecting a relationship solely because the two subjects name different kinds of thing.

Answer each question with a counterexample that rules out full coverage, a positive justification covering the child's whole scope, or an unresolved issue. Merely failing to find a counterexample does not establish containment. If admission or exclusion depends on materially different interpretations of a fixed meaning, leave the answer unresolved rather than choose a boundary.

# Check canonical consequences

Containment can hold across intermediate canonical nodes; a parent label does not require a direct edge. Apply the same coverage test to both consequences against the supplied fixed meanings:
- `canonical_contains_local` requires every canonical ancestor to contain the local meaning.
- `local_contains_canonical` requires the local meaning to contain every canonical descendant.
- `equivalent` requires both conditions.
Do not approve a relationship whose required consequence you reject. If the selected meanings clearly rule out containment, reject that direction. If a proposed relationship conflicts with a supplied branch and the conflict remains unresolved, return `uncertain` and identify the conflict. Do not change meanings or existing relationships to make a placement fit.

Choose exactly one label:
- `equivalent`: the established meanings cover each other completely.
- `local_contains_canonical`: the local node contains the canonical node and is broader.
- `canonical_contains_local`: the canonical node contains the local node and is broader.
- `neither`: both meanings are established, they are not equivalent, and neither contains the other in full.
- `uncertain`: a fixed meaning permits materially different interpretations, the relationship cannot be established, or a relevant evidence or canonical-branch conflict remains unresolved.

# Output

Return only one JSON object with exactly these five fields:
- `meaning`: an exact copy of the local node's supplied `meaning`.
- `questions`: an array with exactly two records, one per containment direction. Each record has exactly these fields:
  - `id`: `local_contains_canonical` or `canonical_contains_local`, each used once.
  - `question`: the concrete counterexample question for that direction.
- `answers`: an array with exactly one record for each question, with no additional records. Each record has exactly these fields:
  - `question_id`: the `id` of the question being answered.
  - `answer`: a concise counterexample or affirmative whole-scope coverage statement, or JSON `null` if the judgment remains unresolved.
  - `justification`: why the counterexample fits the child and is excluded by the parent, why the parent covers the child's whole scope, or what prevents a settled judgment.
- `relation`: one label from the list above, consistent with both answers and the canonical consequences. A null answer requires `uncertain`.
- `reason`: the decisive relationship, distinction, or unresolved issue, including any canonical-branch conflict, without repeating the two justifications.

Preserve the supplied local `meaning` even when the relationship is `uncertain`. Do not rewrite either supplied meaning.

The two answers assess the selected meanings. An unresolved canonical-branch conflict can require an `uncertain` relation without changing a settled answer about those meanings.

For `neither`, both answers must rule out full coverage. For `equivalent`, both must establish full coverage. A directional containment label requires full coverage in that direction, failure of full coverage in the reverse direction, and compatible canonical consequences. For `uncertain`, identify what prevents a settled judgment. Give concise questions, answers and decisive justifications, not a step-by-step reasoning trace. Return no Markdown or additional fields.

# Input

<input>
{INPUT_JSON}
</input>
