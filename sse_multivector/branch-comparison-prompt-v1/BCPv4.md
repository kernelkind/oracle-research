Compare the subjects represented by hierarchy nodes A and B. Decide whether the nodes represent equivalent subjects, whether one is a parent of the other, or neither.

Each node is supplied as a list of subject entries from one or more social-media posts. Each entry pairs a subject wording with a saved description of that subject in its source post. The source posts themselves are not being compared.

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
