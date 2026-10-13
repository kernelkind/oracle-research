
State the meaning directly, without referring to the supplied nodes or explaining how it was derived.

# Check the proposal

Use the final `meaning` unchanged in these checks. When `parent` is present, the proposed meaning must fit wholly within the parent's fixed meaning.

If the proposed meaning covers associated activities, products or participants, it must state the relationship required for them to belong.

Interpret every supplied node from its fixed `meaning` and that meaning's necessary implications. General knowledge may clarify language; a node's title, customary uses, association or existing placement cannot add a condition absent from that meaning. Naming a child as an illustrative member does not exempt it from the proposed meaning's conditions.

An activity topic includes information about plans to perform that activity unless its meaning explicitly requires the activity to have happened. Plans do not establish that the activity happened.

# Check both nodes

Apply the final proposed `meaning` unchanged to both supplied nodes. For each node, look for a case admitted by its fixed meaning that falls outside every kind or relationship covered by the proposed meaning (a counterexample). Check that the case satisfies the node's requirements and necessary implications while failing the proposed meaning's required conditions. If such a case is possible, revise the proposed meaning to cover that node. Both nodes must be covered: every admitted kind, role or alternative must necessarily satisfy the required conditions of at least one covered kind or relationship; failure to find a counterexample alone does not establish coverage.

Establish each node's required consumers, purposes, roles and states from its own fixed meaning and necessary implications. A restriction stated by one node does not restrict the other node. If a proposed condition is established for only one node, choose a coherent broader meaning that covers both; recheck both nodes against that final meaning. Apply each condition to the kind or relationship it qualifies. Cover both nodes' entire meanings. Illustrative examples and conventional associations cannot supply a missing condition.

Check specificity as well as coverage. If a more specific coherent meaning still covers both supplied meanings in full and fits the supplied parent when present, use it and repeat the coverage checks. The proposed meaning may have the same scope as a supplied meaning.

# Synthetic example

Input:
```json
{
  "parent": {"title": "Display panels", "meaning": "Display panels are devices that present visual information. The topic includes these panels and components installed in them."},
  "nodes": [
    {"title": "Blue text panels", "meaning": "Blue text panels are display panels that show text against a uniformly blue background."},
    {"title": "Red indicator lights in blue display panels", "meaning": "Red indicator lights in blue display panels are lights that emit red light and are installed as components in display panels with uniformly blue backgrounds."}
  ]
}
```

Output:
```json
{"title": "Blue display panels", "meaning": "Blue display panels are display panels with uniformly blue backgrounds. The topic includes these panels and their composition: the components installed in them."}
```

The text panels meet the blue-background condition. The indicator lights are covered through the proposed meaning's composition scope: its lights must be installed in panels with blue backgrounds. The lights emit red light; the blue condition applies to the panels' backgrounds.

# Output

Return one JSON object with exactly these fields:
- `title`: the proposed parent's topic name.
- `meaning`: its concise, standalone explicit meaning.

<input>
{INPUT_JSON}
</input>
