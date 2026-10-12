
State the meaning directly, without referring to the supplied nodes or explaining how it was derived.

# Check the proposal

Use the final `meaning` unchanged in these checks. When `parent` is present, the proposed meaning must fit wholly within the parent's fixed meaning and be narrower rather than equivalent.

If the proposed meaning covers associated activities, products or participants, it must state the relationship required for them to belong.

Judge containment from required features, actions, roles, purposes and states. A required condition must follow from the contained meaning or its topic identity; customary uses, association and existing placement cannot supply a missing condition. Naming a child as an illustrative member does not exempt it from the proposed meaning's conditions.

An activity topic includes information about plans to perform that activity unless its meaning explicitly requires the activity to have happened. Plans do not establish that the activity happened.

# Identify the children

Build `children` by comparing every supplied sibling's entire fixed meaning with the final proposed meaning. Include exactly the IDs of wholly covered siblings, including covered siblings beyond those that suggested the topic. Apply all of the proposed meaning's scope, including any stated coverage of associated activities, products or participants.

`children` must contain at least two distinct IDs and fewer than the whole sibling group. Grouping the whole set merely adds a step.

# Synthetic example

Input:
```json
{
  "parent": {"id": "E0", "title": "Display panels", "meaning": "Display panels are devices that present visual information. The topic includes these panels and components installed in them."},
  "siblings": [
    {"id": "E1", "title": "Blue text panels", "meaning": "Blue text panels are display panels that show text against a uniformly blue background."},
    {"id": "E2", "title": "Blue image panels", "meaning": "Blue image panels are display panels that show images against a uniformly blue background."},
    {"id": "E3", "title": "Indicator lights in display panels", "meaning": "Indicator lights in display panels are lights installed as components in display panels."},
    {"id": "E4", "title": "Red display panels", "meaning": "Red display panels are display panels with uniformly red backgrounds."},
    {"id": "E5", "title": "Red indicator lights in blue display panels", "meaning": "Red indicator lights in blue display panels are lights that emit red light and are installed as components in display panels with uniformly blue backgrounds."}
  ]
}
```

Output:
```json
{"title": "Blue display panels", "meaning": "Blue display panels are display panels with uniformly blue backgrounds. The topic includes these panels and their composition: the components installed in them.", "children": ["E1", "E2", "E5"]}
```

E1 and E2 meet the blue-background condition. E5 is covered through the proposed meaning's composition scope: its lights must be installed in panels with blue backgrounds. The lights emit red light; the blue condition applies to the panels' backgrounds.

E3 does not require a blue panel background, so its entire fixed meaning is not covered. E4 requires a red background. Removing the blue-background condition while covering panels and their installed components would reproduce the supplied parent's scope rather than establish a narrower topic.

# Output

If no useful proposal satisfies the checks, or a material ambiguity prevents establishing one coherent meaning, return JSON `null`. Otherwise, return one JSON object with exactly these fields:
- `title`: the proposed parent's topic name.
- `meaning`: its concise, standalone explicit meaning.
- `children`: the distinct IDs of the covered siblings.

The proposal will undergo comparison before its relationships and placement are established.

<input>
{INPUT_JSON}
</input>
