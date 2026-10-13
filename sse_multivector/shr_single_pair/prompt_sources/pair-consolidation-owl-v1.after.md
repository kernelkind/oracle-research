# Check the final result

Use the final formal definitions and `meaning` unchanged in these checks. Every English definition must agree with the formal conditions stated for that class or relation. The English definition of `Consolidated` must be an exact copy of the final `meaning`.

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

Each `owl` value is a string containing the named topic definition (`Node1`, `Node2` or `Consolidated`) and any additional formal definitions or background relationships it needs. Use newlines between statements. Each `definitions` value is a JSON object mapping every named class and relation used in that `owl` string to an English definition, including the named topic itself. Repeated names must have identical definitions across the supplied parent and all returned objects.

Return the formal definitions and final title and meaning without a reasoning narrative. Do not return a parent object.

<input>
{INPUT_JSON}
</input>
