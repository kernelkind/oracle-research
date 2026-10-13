# Check the final result

Use the final formal definitions and `meaning` unchanged in these checks. The final meaning must preserve every condition of `consolidated.owl.expression` and add none.

If the consolidated topic covers associated activities, products or participants, express the relationship required for them to belong in both its formal definition and its meaning.

Interpret each supplied node from its fixed `meaning` and its necessary implications. General knowledge may clarify language; titles, customary uses, associations and existing placement cannot add conditions absent from that meaning. An activity topic includes information about plans to perform that activity unless its meaning explicitly requires the activity to have happened. Plans do not establish that the activity happened.

For each node, check for a possible case admitted by its fixed meaning but excluded by the consolidated definition. A counterexample must satisfy the node's requirements while failing the consolidation's requirements. If one is possible, revise the consolidation and its English definitions, title and meaning together; do not change the supplied parent or either node's translation to make the check pass. Recheck coverage of both nodes and containment within the supplied parent, when present.

State the final meaning directly, without referring to the supplied nodes or explaining how it was derived.

# Output

Return only one JSON object with exactly these fields, in this order:
1. `node1`: an object with `owl` followed by `definitions`, for the first supplied node.
2. `node2`: an object with `owl` followed by `definitions`, for the second supplied node.
3. `consolidated`: an object with `owl` followed by `definitions`, for the proposed consolidated topic.
4. `title`: the consolidated topic's natural-language name.
5. `meaning`: its concise, standalone natural-language definition.

Each `owl` value is a JSON object with exactly two fields, in this order: `expression`, the topic's own expression string, then `classes`, a JSON object mapping supporting class names to expression strings. The entrypoint is always `owl.expression`; do not repeat it as a named class inside `owl.classes`. Use an empty `classes` object when no supporting definitions are needed. Each expression string contains one expression, without an outermost pair of parentheses, a `Name =` prefix or embedded newlines. Reused supporting class definitions must be identical.

Each `definitions` value is a JSON object mapping referenced class and relation names without a formal definition anywhere in the supplied parent's or returned objects' `owl.classes` to their English definitions. Include every such name referenced by that object's expressions. A class defined in `owl.classes` must not also appear in an English `definitions` glossary. The topic's own expression has no separate glossary entry. Reused English definitions must be identical. An empty glossary is `{}`.

Return the formal definitions and final title and meaning without a reasoning narrative. Do not return a parent object.
