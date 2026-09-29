# BCPv4 — one-pair subject comparison

Status: **user-approved wording, tested on six pairs, not frozen**. The user
approved BCPv4 after reviewing the prompt filled with real saved data, then
authorized six Astra-low calls. All six returned valid JSON and were accepted
in agent review. These are agent assessments, not user decisions or a measured
general accuracy rate. No judgments were applied to the saved hierarchy.

[BCPv4.md](BCPv4.md) compares the subjects represented by two hierarchy nodes,
A and B. Each node is represented by subject/context entries originating in one
or more posts; the source posts themselves are not being compared. JSON output
is required. Whether the saved context
descriptions improve the judgments remains untested; including them is a trial
input choice, not a validated requirement.

[BCPv3.md](BCPv3.md) is the unchanged, untested delta baseline. BCPv4 clarifies
the distinction between a hierarchy node, its subject entries and their source
posts; the input fields, relation definitions and JSON output remain unchanged.
Earlier [BCPv2.md](BCPv2.md) and [BCPv1.md](BCPv1.md) remain the baselines for the
input reduction and narrowing from whole branches to one pair. These are not
previously approved prompts. Revision receipts record the exact changes.

The proposed candidate source is distinct pairs of immediate parents of an
LG01 node shared across posts, deduplicated by node identity. Sharing a child
nominates a comparison; it does not establish equivalence or containment.
The read-only investigation of the [LG01 100-post run](../subject-order-probe.md#smv2-100--unchanged-rules-on-all-100-posts)
did not adopt this as a construction rule or authorize model calls.

## Input and output

Use the shared experiment runner's generic adapter with one `INPUT_JSON`
variable. The proposed JSON input uses keys `A` and `B` to identify the two nodes.
Serialize it as JSON; do not manually render batches. Each key's value is a list
of subject-entry objects containing only `subject` and its saved `context`.
Keep every distinct subject/context pair;
remove only exact duplicate pairs, without selecting a representative wording
or rewriting descriptions.

Keep node/post IDs, SP numbers, masks, byte spans, full posts and the mapping of
`A`/`B` to the original nodes in review evidence, outside the model input. Do not
send empty mask arrays or image URLs as separate fields. This reduces the model
input; it does not delete source data or omit subjects with empty masks.

Supply source evidence, not expected answers, previous model decisions or
cosine scores. Do not send the whole branches or graph. Keep the shared-child
references that nominated the pair in review evidence, outside the model input.
The model compares the subjects represented by the two nodes, not the source
posts, a new subject inferred only from masks, or a subject narrowed to the
examples in the context descriptions.

The output is a JSON object with exactly two string fields:

- `relation`: `equivalent`, `a_parent_of_b`, `b_parent_of_a`, `neither`, or
  `uncertain`.
- `reason`: one short justification.

The [six-pair experiment spec](../experiment_specs/lg01-bcpv4-six-pairs-astra-low-v1.json)
uses the shared runner's existing JSON Schema validation; no validation code
was added. There is no graph-update parser or automatic application stage. A
pairwise judgment does not check global graph consistency or authorize
overriding an SP relationship. LG01's preservation rules are unchanged.

## Six-pair test

Unchanged BCPv4 was run with `openai-codex / gpt-6-astra / low`, concurrency 3,
and six maximum new attempts. Six calls completed, without retries, reused
answers, earlier-prompt baseline calls or paid API fallback.

The six pairs were selected from the 49 distinct immediate-parent pairs found
in the saved LG01 100-post run. They cover same-wording and different-wording
equivalence, broader/narrower subjects, and overlapping subjects. The Food node
retained all 27 distinct subject/context entries. Expected relations and shared
children were not sent to the model.

The ignored artifact directory is
`target/branch-comparison-v1/bcpv4-six-pairs-v1/`. Its `cases.json` preserves the
source entries, full posts, node IDs, shared-child evidence and source hashes;
`experiment/` contains frozen inputs/settings, raw receipts, runner-generated
reports and separate agent reviews. The prompt and saved LG01 inputs/results
were hash-checked unchanged. No new subjects, masks, vectors or hierarchy
were generated.

The judgments preserved the Food ingredients / Baking ingredients distinction
despite both contexts discussing bread, and did not mistake shared subjects for
full containment. This selected sample supports further testing, not freezing
the prompt or claiming a validated placement stage. Whether context descriptions
help remains untested: there was no context-free comparison. No case exercised
the `uncertain` response.

## Next step

Review the six saved judgments before expanding. A proposed next test is the
remaining 43 pairs with unchanged BCPv4/Astra low; that expansion is not yet
authorized. It would still only save judgments, not apply them. An application
policy remains open; do not alter the saved LG01 hierarchy.

## Design references

The draft follows the existing
[SP hierarchy rules](../../docs/planning/release-decisions.md#sp-based-hierarchy-rules),
particularly HD08–11 and the open placement question HD21. Drafting a one-pair
prompt does not settle the placement question or change those rules.

The [official OpenAI reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively)
informed the direct task, delimited evidence and explicit output choices, without
worked examples or a prescribed reasoning trace. This is guidance for the draft,
not evidence that it works.
