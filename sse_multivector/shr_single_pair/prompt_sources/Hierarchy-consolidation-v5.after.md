

State the meaning directly, without referring to the supplied nodes or explaining how it was derived.

# Check the proposal

Use the final `meaning` unchanged in each check.

Set `children` to all supplied siblings whose entire fixed meanings are covered by the proposed meaning. Check every sibling, including the activities and uses its meaning covers. Exclude a sibling only when some part of its meaning falls outside the proposed meaning.

When `parent` is present, its fixed meaning must cover the proposed meaning in full, and the proposed meaning must be narrower rather than equivalent.

Return a proposal only when these checks pass and `children` contains at least two siblings but fewer than the whole group. Placing another parent above the entire group merely adds a step. If the proposed topic cannot meet these conditions, choose another topic; return JSON `null` if no useful, coherent parent meeting them can be established.

# Output

Return only JSON `null` if no useful parent with a coherent meaning can be established. Otherwise, return one JSON object with exactly these fields:
- `title`: the proposed parent's topic name.
- `meaning`: its concise, standalone explicit meaning.
- `children`: the distinct IDs of all supplied siblings whose entire fixed meanings are covered by the proposed meaning; at least two and fewer than the whole group.

The proposal will undergo comparison before its relationships and placement are established.

<input>
{INPUT_JSON}
</input>
