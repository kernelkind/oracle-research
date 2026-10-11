

State the meaning directly, without referring to the supplied nodes or explaining how it was derived.

# Output

Return only JSON `null` if no useful parent with a coherent meaning can be established. Otherwise, return one JSON object with exactly these fields:
- `title`: the proposed parent's topic name.
- `meaning`: its concise, standalone explicit meaning.
- `children`: the distinct IDs of all supplied siblings the proposed parent is intended to contain; at least two and fewer than the whole group.

The proposal will undergo comparison before its relationships and placement are established.

<input>
{INPUT_JSON}
</input>
