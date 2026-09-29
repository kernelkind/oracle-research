# BCPv2 — one-pair subject comparison

Status: **draft, untested, not frozen**. The user authorized drafting this
prompt for review, not inference or changes to the saved hierarchy.

[BCPv2.md](BCPv2.md) compares two supplied hierarchy nodes, A and B. It returns
one relationship judgment and a short justification, not a rewritten hierarchy.
Equivalent, either parent direction, neither and uncertain are separate outcomes.

[BCPv1.md](BCPv1.md) is the unchanged, untested whole-branch draft used as the
delta baseline, not a previously approved prompt or the proposed test prompt.
BCPv2 removes its whole-branch proposal and conflict-resolution tasks while
retaining its subject-generality and empty-mask guidance. Its revision receipt
records the exact baseline and changes.

The proposed candidate source is distinct pairs of immediate parents of an
LG01 node shared across posts, deduplicated by node identity. Sharing a child
nominates a comparison; it does not establish equivalence or containment.
The read-only investigation of the [LG01 100-post run](../subject-order-probe.md#smv2-100--unchanged-rules-on-all-100-posts)
did not adopt this as a construction rule or authorize model calls.

## Input and output

Use the shared experiment runner's generic adapter with one `INPUT_JSON`
variable. The proposed JSON input contains nodes `A` and `B`. Serialize it as
JSON; do not manually render batches. For each node include:

- Stable node IDs and all original subject entries represented by each node.
- Each entry's post ID, SP number, exact subject wording and saved `context`.
- Its mask ID and complete source post with that individual mask marked inline.
  Preserve separate masks, including repeated posts. Represent an empty mask
  explicitly while retaining the subject and full post.

Supply source evidence, not expected answers, previous model decisions or
cosine scores. Do not send the whole branches or graph. Keep the shared-child
references that nominated the pair in review evidence, outside the model input.
The model compares the supplied subjects, not a new subject inferred only from
their masks or a subject narrowed to the examples in the source posts.

The output is one of the prompt's five decision labels followed by a short
justification. There is no graph-update parser or automatic application stage
in this draft. A pairwise judgment does not check global graph consistency or
authorize overriding an SP relationship. LG01's preservation rules are unchanged.

## Next review

Review the full BCPv1 → BCPv2 delta before preparing a small pairwise test.
No test cases, execution model or application policy have been selected by this
draft. Do not run the whole candidate set or alter the saved LG01 hierarchy.

## Design references

The draft follows the existing
[SP hierarchy rules](../../docs/planning/release-decisions.md#sp-based-hierarchy-rules),
particularly HD08–11 and the open placement question HD21. Drafting a one-pair
prompt does not settle the placement question or change those rules.

The [official OpenAI reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively)
informed the direct task, delimited evidence and explicit output choices, without
worked examples or a prescribed reasoning trace. This is guidance for the draft,
not evidence that it works.
