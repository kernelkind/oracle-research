
State the meaning directly, without referring to the supplied nodes or explaining how it was derived.

# Check the proposal

Use the final proposed `meaning` unchanged when checking both nodes.

When `parent` is supplied, the proposed meaning must fit wholly within its fixed meaning. Apply this boundary to the complete proposed definition, including every admitted kind or relationship. Revise a proposal that extends beyond it while preserving coverage of both supplied meanings.

If the proposed meaning covers associated activities, products or participants, it must state the relationship required for them to belong.

Interpret each supplied node from its fixed `meaning` and that meaning's necessary implications. General knowledge may clarify language; a node's title, customary uses or association cannot add a condition absent from that meaning. Naming a node as an illustrative member does not exempt it from the proposed meaning's conditions.

An activity topic includes information about plans to perform that activity unless its meaning explicitly requires the activity to have happened. Plans do not establish that the activity happened.

For each node, look for a case admitted by its fixed meaning that falls outside every kind or relationship covered by the proposed meaning (a counterexample). Check that the case satisfies the node's requirements and necessary implications while failing the proposed meaning's required conditions.

Both nodes' entire meanings must be covered. Every admitted kind, role or alternative must necessarily satisfy the required conditions of at least one covered kind or relationship. Failure to find a counterexample alone does not establish coverage.

A restriction stated by one node does not restrict the other. If a proposed condition is established for only one node, choose a coherent broader meaning covering both and recheck them against that final meaning. Illustrative examples and conventional associations cannot supply a missing condition.

# Output

Always return one JSON object with exactly these fields:
- `title`: the proposed parent's topic name.
- `meaning`: its concise, standalone explicit meaning covering both supplied meanings.

<input>
{INPUT_JSON}
</input>
