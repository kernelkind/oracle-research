Compare hierarchy nodes A and B, whose subjects were extracted from social-media posts. Decide whether they express equivalent subjects, whether one is a parent of the other, or neither.

Each node is represented by its subject wordings and saved context descriptions from the posts.

Interpret each subject at its stated level of generality. Use the context descriptions to resolve its meaning and references, without narrowing a broader subject to the particular examples described.

Choose one relation:

- equivalent: A and B express the same subject at the same level of generality.
- a_parent_of_b: B's whole subject is a more specific topic within A's scope.
- b_parent_of_a: A's whole subject is a more specific topic within B's scope.
- neither: the subjects are not equivalent and neither contains the other in full. They may still overlap.
- uncertain: the supplied evidence leaves their meaning or relationship unresolved.

Compare only A and B as supplied; do not rename their subjects or propose changes to other nodes. Return only a JSON object with exactly two string fields: "relation", containing one of the labels above, and "reason", containing one short justification.

<input>
{INPUT_JSON}
</input>
