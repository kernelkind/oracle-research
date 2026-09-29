# BCPv3 — one-pair subject comparison

Status: **draft, untested, not frozen**. The user authorized drafting this
prompt for review, not inference or changes to the saved hierarchy.

[BCPv3.md](BCPv3.md) compares two supplied hierarchy nodes, A and B, using only
their subject/context pairs. JSON output is required. Whether the saved context
descriptions improve the judgments remains untested; including them is a trial
input choice, not a validated requirement.

[BCPv2.md](BCPv2.md) is the unchanged, untested one-pair draft used as the delta
baseline. [BCPv1.md](BCPv1.md) remains the baseline for that earlier narrowing
from whole branches to one pair. Neither baseline is a previously approved
prompt or the proposed test prompt. Revision receipts record the exact changes.

The proposed candidate source is distinct pairs of immediate parents of an
LG01 node shared across posts, deduplicated by node identity. Sharing a child
nominates a comparison; it does not establish equivalence or containment.
The read-only investigation of the [LG01 100-post run](../subject-order-probe.md#smv2-100--unchanged-rules-on-all-100-posts)
did not adopt this as a construction rule or authorize model calls.

## Input and output

Use the shared experiment runner's generic adapter with one `INPUT_JSON`
variable. The proposed JSON input contains nodes `A` and `B`. Serialize it as
JSON; do not manually render batches. Each node is a list of objects containing
only `subject` and its saved `context`. Keep every distinct subject/context pair;
remove only exact duplicate pairs, without selecting a representative wording
or rewriting descriptions.

Keep node/post IDs, SP numbers, masks, byte spans, full posts and the mapping of
`A`/`B` to the original nodes in review evidence, outside the model input. Do not
send empty mask arrays or image URLs as separate fields. This reduces the model
input; it does not delete source data or omit subjects with empty masks.

Supply source evidence, not expected answers, previous model decisions or
cosine scores. Do not send the whole branches or graph. Keep the shared-child
references that nominated the pair in review evidence, outside the model input.
The model compares the supplied subjects, not a new subject inferred only from
their masks or a subject narrowed to the examples in the source posts.

The output is a JSON object with exactly two string fields:

- `relation`: `equivalent`, `a_parent_of_b`, `b_parent_of_a`, `neither`, or
  `uncertain`.
- `reason`: one short justification.

This draft specifies the output contract; no inference setup or new validation
code has been added. There is no graph-update parser or automatic application
stage. A pairwise judgment does not check global graph consistency or authorize
overriding an SP relationship. LG01's preservation rules are unchanged.

## Next review

Review the full BCPv2 → BCPv3 delta before preparing a small pairwise test.
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
