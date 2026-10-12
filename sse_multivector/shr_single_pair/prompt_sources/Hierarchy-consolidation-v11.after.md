
State the meaning directly, without referring to the supplied nodes or explaining how it was derived.

# Check the proposal

Use the final `meaning` unchanged in these checks. If it covers associated activities, products or participants, the meaning must state the relationship required for them to belong. Apply that full scope to every supplied sibling:
- It must cover every selected child's entire fixed meaning.
- When `parent` is present, it must fit wholly within the parent's fixed meaning and be narrower rather than equivalent.
- `children` must list all supplied siblings whose entire fixed meanings it covers, with at least two distinct IDs and fewer than the whole group. Grouping the whole set merely adds a step.

Judge containment from required features, actions, roles, purposes and states. A required condition must follow from the contained meaning or its topic identity; customary uses, association and existing placement cannot supply a missing condition. Naming a child as an illustrative member does not exempt it from the proposed meaning's conditions.

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
