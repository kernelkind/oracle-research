

State the meaning directly, without referring to the supplied nodes or explaining how it was derived. Distinguish required features from optional variations. Apply each defining restriction consistently to the kinds it concerns. If the proposed topic remains materially ambiguous, return JSON `null`.

# Output

Return only JSON `null` if no proposal meets the requirements. Otherwise, return one JSON object with exactly these fields:
- `title`: the proposed parent's topic name.
- `meaning`: its concise, standalone explicit meaning.
- `children`: the distinct IDs of all supplied siblings the proposed parent is intended to contain; at least two and fewer than the whole group.

The proposal will undergo comparison before its relationships and placement are established.

<input>
{INPUT_JSON}
</input>
