Connect the supplied query hierarchy nodes to the existing global hierarchy. Propose combinations of equivalent nodes and missing ancestor relationships; do not create or rename subjects.

A hierarchy node represents one or more SP subject entries. Each catalogue entry pairs an original subject wording with its saved context description from a social-media post. The query identifies existing hierarchy nodes in this same catalogue, not posts to compare.

Interpret subjects at their stated level of generality. Context resolves meaning and references; it does not narrow a broad subject to the particular examples described. Use all entries represented by a node, rather than choosing only those that support a proposed relationship.

- Equivalent nodes express the same whole subject at the same level of generality. Identical wording alone is not sufficient.
- An ancestor contains the descendant's whole subject as a more specific topic. Association or partial overlap is not containment. An ancestor need not be an immediate parent, and a node can have multiple parents.

Preserve the supplied relationships as ancestor-or-equal: combining equivalent nodes may collapse a step, but must not reverse an existing relationship or create a cycle among distinct resulting nodes. The local hierarchies came from different posts; their top-level subjects need not have the same generality.

Consider every query node against the catalogue. Every proposed equivalent group or ancestor link must include at least one query node. Leave unresolved relationships unproposed. Omission is not a judgment that two nodes are unrelated. Do not return links already implied by the supplied hierarchy or your other proposals.

Return only a JSON object with these two arrays:

- "equivalences": objects with "nodes" (two or more supplied node IDs) and "reason" (one short justification).
- "ancestors": objects with "ancestor", "descendant" (supplied node IDs), and "reason" (one short justification).

Use catalogue IDs even when proposing combinations; code will map them to the combined nodes. If no changes are warranted, return {"equivalences":[],"ancestors":[]}.

<catalogue>
{CATALOGUE_JSON}
</catalogue>

<query>
{QUERY_JSON}
</query>
