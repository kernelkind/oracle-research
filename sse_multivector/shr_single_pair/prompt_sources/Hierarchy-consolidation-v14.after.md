
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
  "parent": {"id": "E0", "title": "Blue shapes", "meaning": "Blue shapes are geometric shapes colored blue."},
  "siblings": [
    {"id": "E1", "title": "Squares", "meaning": "Squares are shapes bounded by four equal straight sides meeting at right angles."},
    {"id": "E2", "title": "Blue triangles", "meaning": "Blue triangles are blue shapes bounded by exactly three straight sides."},
    {"id": "E3", "title": "Blue rectangles", "meaning": "Blue rectangles are blue shapes bounded by four straight sides meeting at right angles."},
    {"id": "E4", "title": "Blue circles", "meaning": "Blue circles are blue shapes with a circular boundary."}
  ]
}
```

Output:
```json
{"title": "Blue polygons", "meaning": "Blue polygons are geometric shapes colored blue and bounded by a closed chain of straight sides.", "children": ["E2", "E3"]}
```

Squares' fixed meaning does not require them to be blue; existing placement cannot supply that missing condition. Blue circles fit the supplied parent but not the proposed meaning. A proposed meaning allowing polygons of any color would extend beyond Blue shapes.

# Output

If no useful proposal satisfies the checks, or a material ambiguity prevents establishing one coherent meaning, return JSON `null`. Otherwise, return one JSON object with exactly these fields:
- `title`: the proposed parent's topic name.
- `meaning`: its concise, standalone explicit meaning.
- `children`: the distinct IDs of the covered siblings.

The proposal will undergo comparison before its relationships and placement are established.

<input>
{INPUT_JSON}
</input>
