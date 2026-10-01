Suggest broader subject names to help find possible ancestors, independently for each supplied hierarchy node. These names will be used to search existing nodes; a separate comparison will check their actual relationship.

Each query supplies original SP subject entries from social-media posts. Interpret the subject at its stated level of generality. Use the saved context descriptions to resolve meaning and references without narrowing a broader subject to the particular examples described.

The first entry fixes the subject. A second entry may corroborate or question that reading; it must not redefine the subject. If the entries conflict or leave its meaning unresolved, suggest no names.

For each query, suggest zero through three broader subjects whose scope contains the query's whole subject. Prefer close broader subjects over very general ones. Related topics, particular examples, and equivalent wordings are not broader subjects. Use concise subject names, each at most 160 characters, rather than explanations. Do not fill a quota.

Return only a JSON object with exactly the field "queries", containing one item for every supplied query, in supplied order. Each item has exactly "id", containing the supplied query ID, and "parents", containing the proposed subject names as distinct strings. An empty parents array is valid.

<input>
{INPUT_JSON}
</input>
