Compare the subjects represented by the supplied hierarchy-node pairs. Decide independently for every pair whether the nodes represent equivalent subjects, whether one is a parent of the other, or neither.

The nodes array supplies original SP subject entries from social-media posts. Each entry pairs a subject wording with a saved description of that subject in its source post. These are selected original references, not complete lists of every entry represented by a combined node. The source posts themselves are not being compared. Original entry indices identify saved evidence, not importance. Each pair supplies its ID and identifies its A and B nodes; the same node evidence can be reused by several pairs.

Interpret each subject at its stated level of generality. Use the context descriptions to resolve its meaning and references, without narrowing a broader subject to the particular examples described.

The first entry fixes the subject being compared. The second entry may corroborate or question that reading; it must not redefine the subject. If the entries conflict or leave the fixed subject unresolved, return uncertain.

Choose one relation for each supplied pair:

- equivalent: A and B express the same subject at the same level of generality.
- a_parent_of_b: B's whole subject is a more specific topic within A's scope.
- b_parent_of_a: A's whole subject is a more specific topic within B's scope.
- neither: the subjects are not equivalent and neither contains the other in full. They may still overlap.
- uncertain: the supplied evidence leaves their meaning or relationship unresolved.

Compare only the supplied pairs as given; do not rename their subjects, judge other pairs, infer a relation from nomination or shared words, or force a placement. Use uncertain when the selected references leave a combined node's meaning unresolved. Parent labels express ancestor containment, not necessarily immediate parenthood.

Return only a JSON object with exactly the field "comparisons", containing one item for every supplied pair, in supplied order. Each item has exactly three string fields: "id", containing the supplied pair ID; "relation", containing one of the labels above; and "reason", containing one short justification.

<input>
{INPUT_JSON}
</input>
