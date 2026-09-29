# BCPv4 — one-pair subject comparison

Status: **user-approved wording, tested on 49 pairs, not frozen**. The user
approved six Astra-low calls, then the remaining 43 nominated comparisons.
All 49 returned valid JSON. Agent review accepted the first six; of the next
43, 36 were accepted and seven flagged as uncertain across four issues below.
These are agent assessments, not user decisions or a measured general accuracy
rate. No judgments were applied to the saved hierarchy.

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

## Hierarchy generation stages

The user approved **HG1–HG7** as stable labels for this SP-based investigation.
They identify process stages, independently of prompt versions, experiment IDs
and post count. Approval of the labels does not approve the proposed operations
at HG6–HG7 or select a production hierarchy-generation policy.

| Label | Stage | Current status |
| --- | --- | --- |
| HG1 — SP + MP | Generate each post's local subject hierarchy and masks. | Saved inputs. |
| HG2 — SSE | Encode subjects and masks into separate vectors. | Saved vectors. |
| HG3 — LG01 | Combine matching subjects across posts, preserving SP relationships. | Implemented experiment; see the [LG01 rules](../subject-order-probe.md#lg01--subject-hierarchy-merging). |
| HG4 — Select comparisons | Select pairs of distinct immediate parents of a shared cross-post node; deduplicate by node identity. | Nominated the 49 tested pairs; not a complete construction rule. |
| HG5 — Compare parents | Prompt BCPv4 for each selected pair using the two nodes' subject/context entries; save its relation and reason. | 49 pairs tested; answers not applied to the hierarchy. |
| HG6 — Combine equivalent nodes | Combine parents judged equivalent at HG5, retaining original entries, relationships and answers. | Proposed; unapproved and unimplemented. |
| HG7 — Recompare changed nodes | Remap and deduplicate affected pairs, then prompt BCPv4 using the combined entries. | Proposed; unapproved and unimplemented. |

For example, the Dining/Meals inconsistency was observed at **HG5**. The
proposed follow-up combines the equivalent Dining nodes and the equivalent
Meals nodes at **HG6**, then compares the combined nodes at **HG7**. Graph
application, cycle handling and uncertain-equivalence policies remain open.
LG01 names the technique at HG3, not the whole process or a particular run.

### Proposed HG8 — apply ancestor relationships

Status: **ancestor interpretation and browsing-link rule agreed; remaining
application policy is a draft, not approved or implemented**. HG8 is a proposed
label, not an extension of the approved HG1–HG7 labels. The current code does not
apply BCPv4 answers.
The prompt, response labels and saved hierarchy remain unchanged.

BCPv4 calls its answers `a_parent_of_b` and `b_parent_of_a`, but defines them
as one subject being a more specific topic within the other's scope. The user
agreed to treat these as **ancestor relationships**, not proof of immediate
parenthood. Other hierarchy nodes may sit between the compared nodes.

1. Start from the combined nodes and mapped SP links after HG6. Retain every
   original subject, mask and SP relationship as provenance. Check that SP
   ancestry is preserved as ancestor-or-equal and that distinct nodes form no
   cycle. If the merges already violate these conditions, stop and report the
   problem; the link-application stage must not repair those merges.
2. Use HG5 answers for unchanged inputs and HG7 answers for changed inputs.
   An answer must match the current A/B subject/context entries and the fixed
   prompt/model settings. Reusing a node's old answer merely by replacing its
   ID is not valid. Missing, invalid or stale answers remain unjudged; they
   are not treated as `neither`.
3. Translate the current answers into proposed ancestor relationships:

   | Answer | Action at HG8 |
   | --- | --- |
   | `a_parent_of_b` | Record A as an ancestor of B; not necessarily its immediate parent. |
   | `b_parent_of_a` | Record B as an ancestor of A; not necessarily its immediate parent. |
   | `neither` | Propose no additional ancestor relationship; retain the answer. |
   | `uncertain` | Propose no additional ancestor relationship; retain the unresolved answer. |
   | `equivalent` | Belongs to HG6, not an ancestor relationship. Newly returned HG7 equivalences remain pending; no automatic repeat of HG6–HG7 has been selected. |

4. Check all proposed ancestor relationships together with the existing SP
   relationships. Arrows in this check represent ancestry, not immediate
   parent placement. Withhold every new relationship that participates in a
   directed cycle, retaining the answers and the conflicting paths for review.
   Keep all existing SP relationships and all other proposals; deduplicate
   identical relationships. Do not select a winner by call order, delete an SP
   link, or infer an equivalence from a cycle of strict-ancestor answers.
5. Save the resulting ancestor relationships separately from the LG01 baseline.
   Record which answer supplied each new relationship, which proposals were
   withheld, and any disagreements between answers and the resulting ancestor paths.
   No node removal, replacement titles, membership expansion or display
   collapsing is part of this draft.

For example, the saved Food ingredients / Baking ingredients parent answer
would record **Food ingredients as an ancestor of Baking ingredients**. It
does not establish that Baking ingredients belongs immediately beneath Food
ingredients. Both nodes retain their SP relationships. If SP supplies A → B
and the model proposes B → A, withhold the new B → A relationship and record
the disagreement. If two new relationships jointly form a cycle, withhold
both rather than accepting whichever was processed first.

The proposed conflict policy needs explicit approval: a `neither` answer does
not remove an SP path or veto a path supplied by other parent answers. Such
disagreements are recorded, not silently resolved. Cycle checks establish
structural validity, not semantic correctness. HG6 merge handling and any
repeat rule for equivalences found at HG7 remain separate open decisions.

The user agreed to the following browsing-link rule, recorded as
[HD22](../../docs/planning/release-decisions.md#sp-based-hierarchy-rules):
omit a direct link A → B from the browsing view when another path of at least
two links connects A to B. Derive the view from the complete acyclic ancestor
graph, not by selecting one longest chain. Retain every node, multiple parent
routes, and all original relationships and provenance in the underlying data.
This is a browsing simplification, not deletion of source relationships.

For N037's saved Food → Bread → Sourdough bread branch, a separate
Food → Sourdough bread browsing link is redundant. Keep the route through
Bread and preserve Food's ancestor relationship with Sourdough bread.
The rule is agreed but not yet implemented in this investigation; earlier
LG01 browser outputs remain unchanged.

## Input and output

Use the shared runner's [saved subject-pair adapter](../model-runner.md#saved-subject-pair-preparation)
with saved source paths and explicit A/B node IDs. It assembles `INPUT_JSON`
automatically; do not copy source entries into a case file. Keys `A` and `B`
identify the two nodes. Each value is a list containing only `subject` and its
saved `context`. The adapter retains every distinct subject/context pair and
removes only exact duplicates, without choosing a representative wording or
rewriting descriptions.

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
uses the shared runner's existing output JSON Schema validation. There is no
graph-update parser or automatic application stage. A
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

The original test used the generic adapter. The reusable spec now uses
`subject_pairs` and a [small source/pair selection file](../experiment_specs/lg01-bcpv4-six-pairs-v1.json).
Offline preparation under `target/branch-comparison-v1/bcpv4-six-pairs-adapter-v1/`
reproduced all six prompts byte-for-byte with unchanged model settings and
identified six reusable saved answers. No new calls or results were generated.
Deriving review evidence from SP edges corrected B04's previously swapped
shared-child A/B post labels (Meals: N023; Food: N096). That metadata was never
sent to the model; the original experiment remains untouched.

The judgments preserved the Food ingredients / Baking ingredients distinction
despite both contexts discussing bread, and did not mistake shared subjects for
full containment. This selected sample supports further testing, not freezing
the prompt or claiming a validated placement stage. Whether context descriptions
help remains untested: there was no context-free comparison. No case exercised
the `uncertain` response.

## Remaining 43-pair test

The user authorized the remaining comparisons with unchanged BCPv4/Astra low.
The [spec](../experiment_specs/lg01-bcpv4-remaining-pairs-astra-low-v1.json) uses
the subject-pair adapter and [explicit source/pair selection](../experiment_specs/lg01-bcpv4-remaining-pairs-v1.json).
Offline checks confirmed that the six prior pairs plus these 43 exactly cover
the 49 pairs nominated by distinct immediate parents of cross-post shared LG01
nodes. Selection, source data, prompt and model settings were not changed.

All 43 subscription calls completed with valid JSON, no retries or reuse, and
no paid API fallback. Earlier pairs were not rerun. The runner-generated report,
receipts and separate agent reviews are under
`target/branch-comparison-v1/bcpv4-remaining-pairs-v1/experiment/`.

Agent review accepts 36 judgments and flags seven for user review:

| Cases | Issue |
| --- | --- |
| B20, B21, B30, B46 | Dining contains Meals twice, but neither contains the other twice. B22 equates the Dining nodes and B29 equates the Meals nodes, so these judgments are jointly inconsistent. The correct relation is not yet adjudicated. |
| B17 | Coffee / Coffee shops: neither was selected. Review whether beverage versus establishment is too narrow a reading of topic containment; B27 accepts dedicated food-smoking equipment beneath Food smoking. |
| B37 | Dietary practices / Diets: equivalence may erase a broader practices-versus-diets distinction; both can also mean approaches to eating. |
| B49 | Food ingredients / Vegetables: the parent judgment may be reasonable, but its justification narrows Vegetables to those "used in cooking." Review the full supplied scope. |

The seven flags are not seven proven failures. The model itself used no
`uncertain` answers; these flags are the reviewing agent's judgments. No prompt
revision, graph changes or new application rule follows automatically.

## Next step

Review the four issues above, starting with the Dining/Meals inconsistency,
before applying judgments or revising the prompt. The saved outputs support
that review. HG6–HG7 are an unapproved proposal for testing combined inputs,
not authorization for additional calls. The [HG8 ancestor-application draft](#proposed-hg8--apply-ancestor-relationships)
records the agreed ancestor interpretation and browsing-link rule. Its remaining
application policy, including cycle handling, needs user review. Do not alter
the saved LG01 hierarchy.

## Design references

The draft follows the existing
[SP hierarchy rules](../../docs/planning/release-decisions.md#sp-based-hierarchy-rules),
particularly HD08–11 and the open placement question HD21. Drafting a one-pair
prompt does not settle the placement question or change those rules.

The [official OpenAI reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively)
informed the direct task, delimited evidence and explicit output choices, without
worked examples or a prescribed reasoning trace. This is guidance for the draft,
not evidence that it works.
