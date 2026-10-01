Select promising existing hierarchy nodes for a separate subject comparison, independently for each supplied query node. A candidate may represent an equivalent subject or an ancestor of the query's subject. This is candidate selection, not a judgment or permission to merge nodes or add relationships.

Each query supplies original SP subject wordings paired with their original context descriptions. Interpret each subject at its stated level of generality. Use the context descriptions to resolve meaning and references, without narrowing a broader subject to the particular examples described. Original entry indices identify saved evidence, not importance.

The first entry fixes the query subject to search for. A second entry may corroborate or question that reading; it must not redefine the subject. If the entries conflict or leave the fixed subject unresolved, do not force nominations.

Candidates supply their IDs and original subject wordings only. Their wording is a clue, not authority; their contexts will be checked separately. Do not assume that matching words establish equivalence, or that related topics establish whole-subject containment.

For each query, select zero through three supplied candidates worth that separate comparison. Never select the query itself or an ID listed in that query's excluded_candidates. Prefer useful candidates; do not fill a quota, invent nodes or relationships, rename subjects, or force a placement when no supplied candidate is promising.

Return only a JSON object with exactly the field "queries", containing one item for every supplied query, in supplied order. Each item has exactly "id" and "candidates". Each candidate has exactly "id" and "reason", with one short reason for checking it. An empty candidates array is valid. Use only supplied IDs, and do not repeat a candidate within a query.

<input>
{INPUT_JSON}
</input>
