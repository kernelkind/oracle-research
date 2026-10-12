

State the meaning directly, without referring to the supplied nodes or explaining how it was derived.

# Check the proposal

Use the final `meaning` unchanged in each check. Check its required conditions: defining features, actions, roles, purposes and states.

- For each selected child, every condition required by the proposed meaning must already follow from that child's entire fixed meaning.
- When `parent` is present, every condition required by its fixed meaning must follow from the entire proposed meaning. The proposed meaning must also be narrower rather than equivalent.

A condition can follow from topic identity or the definition even when the wording differs. A customary use, association or illustrative included kind is not enough. If the meaning being contained permits anything without a required condition, containment fails. Naming a child as an included kind does not exempt it from the proposed meaning's conditions. Do not add a missing condition to a fixed meaning or infer it from existing placement.

Set `children` to all supplied siblings whose entire fixed meanings are covered by the proposed meaning. Check every sibling, including the activities and uses its meaning covers. Exclude a sibling only when some part of its meaning falls outside the proposed meaning.

Return a proposal only when these checks pass and `children` contains at least two siblings but fewer than the whole group. Placing another parent above the entire group merely adds a step. If the proposed topic cannot meet these conditions, choose another topic; return JSON `null` if no useful, coherent parent meeting them can be established.

# Synthetic example

Input:
```json
{
  "parent": {"id": "E0", "title": "Blue shapes", "meaning": "Blue shapes are geometric shapes colored blue."},
  "siblings": [
    {"id": "E1", "title": "Squares", "meaning": "Squares are shapes bounded by four equal straight sides meeting at right angles. They may have any color."},
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

Squares cannot be selected because their fixed meaning allows other colors; their placement beneath Blue shapes does not restrict their color. Blue circles fit the supplied parent but not the proposed meaning. A proposed meaning allowing polygons of any color would also be invalid because it would extend beyond Blue shapes.

# Output

Return only JSON `null` if no useful parent with a coherent meaning can be established. Otherwise, return one JSON object with exactly these fields:
- `title`: the proposed parent's topic name.
- `meaning`: its concise, standalone explicit meaning.
- `children`: the distinct IDs of all supplied siblings whose entire fixed meanings are covered by the proposed meaning; at least two and fewer than the whole group.

The proposal will undergo comparison before its relationships and placement are established.

<input>
{INPUT_JSON}
</input>
