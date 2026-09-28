# NMP-Jev-v1 — mask-based node merging

Status: tested on all 55 original pairs in the approved eleven-branch comparison;
not frozen or adopted.
The unchanged title-only NSP-Jev-v3 remains the saved comparison baseline.
The separate [NMP-Jev-v2 trials](../node-merge-prompt-jev-v2/prompt.txt) below use
Jev and Astra low. They are tested, not adopted. The completed Astra view is
available beside the unchanged saved Jev-v1 comparison.

This separate prompt asks whether two groups express the same topic at the same
level of generality. It replaces generated title inputs with the masks in each
group. It does not generate titles, place parents or change the saved tree.

## Input and output

- `A_MASKS_JSON` and `B_MASKS_JSON`: JSON-serialized arrays of masks, each mask
  represented by its ordered array of exact fragment strings. Preserve the
  existing title adapter's exact same-post mask deduplication and instance order.
  The placeholders are unquoted because the values are arrays, not JSON strings.
- Supply the two groups separately. Do not combine them, flatten fragments
  across masks, or add titles, source-post text, IDs or tree positions.
- Use the shared generic adapter's literal variable substitution; serialize
  arrays with a JSON encoder. Never concatenate unescaped source text into JSON.
- V1 transport: `typesafe/jev-1.13` through the existing System One runner,
  with `provider-default` reasoning. The separate V2/Astra diagnostic is below.
- Native choice question: `same_topic`, with `yes`, `no`, or `uncertain`.
  This is one symmetric equivalence question, not a directed containment answer.
  Do not relabel it as two native `contains` answers or feed it unchanged to the
  old directional-result validator.

## Scope and review

The initial comparison used the same ten saved Sleep group pairs from
HR02-NT02-C01, tested separately as HR02-NT02-C02. The user then approved a
small diverse sample, tested as HR02-NMP02 with twelve other saved pairs.
Both use the shared experiment runner without baseline reruns. Only a direct
Yes permits a collapse; No and Uncertain remain distinct. HR02-NMP02 examines
pairwise decisions only and performs no contraction. Saved groups and masks
stay fixed. No new titles, parent placement or production adoption.

`merge_tree_nesting.mask_pair_cases` prepares the mask inputs through the
existing title adapter. `validate_equivalence_decisions` checks the exact
question, inputs, native choice and receipt-backed report;
`contract_equivalence` preserves direct answers separately from containment
answers. Both decision types reuse the same reversible edge-contraction code.
The original title-only results still replay exactly.

This changes both evidence (titles to masks) and question framing (two directed
containment answers to one equivalence answer). It is a comparison of those
complete approaches, not an isolation of the effect of adding masks alone.

The criterion is semantic scope, not identical masks, common words, group size
or a merely shared broader topic. Differing examples need not create different
topics; a genuinely narrower topic must remain distinguishable.

## Sleep comparison result

All ten requests completed with valid native answers: nine Yes, one No, no
retries or reused answers. Direct equivalence collapses eleven original groups
to two, versus six with the saved title-only approach. All twelve masks and
eleven original-group mappings remain recoverable. Input hashes are unchanged,
and both prior title-only consolidation results still replay exactly.

The two surviving groups retain their saved titles, **Sleep and tiredness**
(twelve masks) and **Sleep** (three masks). Their nesting comes from the saved
mask sets; this test did not validate semantic parent placement or generate titles.

Agent review accepts nine decisions and flags one as uncertain, not as a
user-approved error: the five-mask combined group was judged equivalent to the
two-mask group containing `[tired, 😴]` and `[fell asleep, very tired]`. The added
masks concern adequate/good sleep and sleep alone, so the merge may erase a useful
sleepiness distinction. Native probabilities were Yes 0.52, No 0.47, Uncertain
0.01; no threshold or output override was applied. Removing redundant levels is
encouraging, but this possible loss prevents claiming overall success or accuracy.

Receipts and separate agent assessments are in
`sse_multivector/experiments/hr02-sleep-mask-merge-jev-v1/`.
Derived consolidation and verification are in
`target/hierarchy-build-v1/hr02-sleep-mask-merge-v1/`.
Provider-reported cost was $0.000287994.
Subsequent read-only inspection judged this an incorrect merge: the two masks
express tiredness, while the added sleep-only masks do not require tiredness.
That is an agent assessment, not a user verdict; the saved run-time uncertainty
and native answer remain intact. The user approved the diverse test below.

## Diverse comparison result — HR02-NMP02

Twelve original saved edges were selected before inference: six expected to
merge and six expected to remain separate. Seven pairs come from the earlier
food/nonfood diagnostics, five from the saved M06 tree. Their grouping/title
provenance differs; all model inputs contain only the exact grouped masks.
The purposive sample covers Dinner, Recipes, Coffee, Art, Children, Tea, Food,
Animals, Emotions and Morning greetings. It is not a representative accuracy
estimate, and pre-run expectations are agent judgments, not human ground truth.

All twelve fresh requests completed successfully, with no reuse or retries.
Nine matched pre-run expectations. Agent review accepts nine decisions, rejects
two and flags one as uncertain:

- **Art: missed merge.** Both groups retain explicit art masks; adding painting
  supplies another art example, not a different overall topic. Jev answered No.
- **Dinner: incorrect merge.** The smaller group always expresses dinner;
  added standalone grilling out and Barbecue Chain do not require dinner.
  Jev answered Yes, losing the narrower distinction if applied.
- **Children: uncertain missed merge.** Adding baby to kid/kids/son masks was
  expected to preserve the overall children topic. Jev answered No. The agent
  still leans toward merging, but colloquial age boundaries make this less clear.

The five other narrower distinctions were preserved: Hot tea, Processed food,
Dogs, Happiness and Morning greetings. Four repetition/example additions also
received the expected Yes. This tests scope preservation, not just node-count
reduction. The saved title-only decisions agreed with the agent's expectations
on the three disputed pairs; the mask approach is not uniformly better.

Receipts and separate agent assessments:
`sse_multivector/experiments/hr02-diverse-mask-merge-jev-v1/`.
Pre-run selection, exact input provenance, results and verification:
`target/hierarchy-build-v1/hr02-diverse-mask-merge-v1/`.
Provider-reported cost was $0.000293118.
All source hashes and the prompt are unchanged; 83 regression tests pass.

The subsequent read-only audit found that NMP-Jev-v1 already states the relevant
scope and example distinctions; these outputs do not establish a missing
instruction or a contradiction. The recommendation was to leave it unchanged
and inspect the saved merge decisions in the hierarchy UI. The user approved
that comparison, not a revision or adoption. Additional inference was approved
separately for the missing pairs below.

## Completed comparison — HR02-NMP03

The user reviewed Sleep and said it looked fine, then asked why same-title
nesting remained elsewhere. The first UI applied only 22 tested pairs, leaving
33 pairs untested. The user approved testing all remaining pairs with unchanged
NMP-Jev-v1 and refreshing the comparison, not another Sleep trial or UI redesign.
That review does not establish individual human labels for the Sleep decisions.

All 33 new calls completed with valid native answers: 16 Yes and 17 No, no
Uncertain, failures, retries or reused requests. The prior 22 mask answers and
all title answers were reused without inference. Selection is exactly the
`untested` original links from the v2 verification, prepared through
`merge_tree_nesting.mask_pair_cases`; no hand-selected exclusions were added.

Both methods now cover all 55 original links across the same eleven branches.
The 66 original groups become 36 with mask-based merging and 26 with title-based
merging. Counts are not quality scores. In the mask view, Coffee becomes one
group, Art remains four, and Children becomes six. Sixteen same-title links
remain (ignoring capitalization), all because of native No answers, not missing
checks. Dinner becomes one group, applying the previously flagged broad/narrow
merge without an override. Sleep is unchanged. No new titles or semantic parent
placement are included.

Receipts: `sse_multivector/experiments/hr02-remaining-mask-merge-jev-v1/`.
Exact selection and derived inputs:
`target/hierarchy-build-v1/hr02-remaining-mask-merge-v1/`.
Provider-reported cost was $0.000785778.
The original partial comparison remains preserved; canonical HR02 is unchanged.

## Shared-topic wording test — HR02-NMP04

The user approved testing whether the task statement was inviting comparison of
all group content rather than each group's shared topic. NMP-Jev-v2 replaces
only the two central task sentences with:

> For each group separately, identify the most specific topic shared by all its
> masks, rather than a summary of their contents. Are those two topics the same?

The exact v1-based delta is recorded in
`../node-merge-prompt-jev-v2/prompt.txt.revision.json`. Input formatting, choices,
broader/narrower distinction, remaining instructions, model and settings stay
fixed. The known My son / son failure was reproduced from its validated saved
receipt before the revision; no baseline inference was repeated.

The shared runner inherited all seven Children pairs, all three Art pairs, and
Tea/Hot tea from two saved baselines. Eight cases are in
`sse_multivector/experiments/hr02-shared-topic-merge-jev-v2-a/` (from the remaining
pair run), and three in `hr02-shared-topic-merge-jev-v2-b/` (from the diverse run).
Both directories preserve the exact selection, settings, baseline receipts and
new outputs. All eleven calls completed successfully, with no retries or reuse.

Ten native choices stayed the same; changes to probabilities alone are not
answer changes. The only changed choice was the previously ambiguous addition
of baby to a Children group: No became Yes (Yes 0.47, No 0.45). The agent keeps
that case uncertain rather than calling it a clear improvement. The motivating
addition of My son / son still receives No, and all three Art pairs remain No.
Tea/Hot tea correctly remains separate. Agent assessments are distinct from
human decisions; this targeted sample is not an accuracy estimate.

This Jev trial did not fix the motivating failure. It does not support replacing
v1 with v2 or establish why Jev failed. No prompt promotion, new titles, group
changes, contraction or hierarchy-view update was performed. The user then
separately approved the Astra-low comparison below.

The reports record provider charges of $0.000195132 and $0.000069930. All exact input/settings comparisons and frozen
hierarchy source hashes pass verification; 85 prompt-revision, nesting and
experiment regression tests pass. These mechanical checks do not imply that
the semantic merge answers passed.

## Astra-low comparison — HR02-NMP05

The user approved Astra low for this small diagnostic. All eleven HR02-NMP04
pairs were run through the shared experiment workflow with `openai-codex` /
`gpt-6-astra` / `low`, using the subscription route with no paid fallback.
Every rendered prompt and input variable is byte-for-byte identical to its
saved Jev-v2 baseline. The original prompt ID NMP-Jev-v2 is retained to identify
that exact text; no Astra-specific semantic prompt revision was made.

Jev uses its native System One choice interface; Astra uses the existing
structured-output transport. The output shape keeps `same_topic.type = choice`
and `same_topic.choice = yes|no|uncertain`. The Astra schema closes both objects
with `additionalProperties: false` and specifies string enums; it requests no
generated probabilities or confidence. The offline SDK preview verified the
exact model, low effort and strict schema without credentials or network calls.
The [official model page](https://developers.openai.com/api/docs/models/gpt-6-astra)
confirms low effort, and the
[structured-output requirements](https://developers.openai.com/api/docs/guides/structured-outputs#additionalproperties-false-must-always-be-set-in-objects)
require closed objects. This is a model/transport comparison, not a claim that
the native classifiers and generative responses have identical mechanics.

All eleven new subscription calls completed with valid outputs, no retries,
failures or reused calls. No Jev baseline was rerun:

| Pair set | Saved Jev v2 | Astra low |
| --- | --- | --- |
| Seven Children links | 3 Yes, 4 No | 7 Yes |
| Three Art links | 3 No | 3 Yes |
| Tea / Hot tea | No | No |

Seven choices changed; four stayed the same. The motivating My son / son case
now receives Yes. Applying the Children and Art answers would collapse their
eight and four original groups to one each, removing the repeated-title chains;
this was subsequently applied in HR02-NMP06 below. Tea/Hot tea remains a
successful narrower-topic control. The agent still flags the baby age-boundary
case as uncertain: model agreement does not establish a human judgment.

This supports keeping the task wording fixed while investigating the model's
ability to perform it. It is a targeted diagnostic, not general accuracy or a
production adoption decision. The user subsequently approved the remaining
44 saved original pairs with Astra low, completed as HR02-NMP06 below.

Reusable specs: `../experiment_specs/hr02-shared-topic-merge-astra-low-v1-a.json`
and `../experiment_specs/hr02-shared-topic-merge-astra-low-v1-b.json`.
Receipts, immutable baselines and separate agent assessments:
`sse_multivector/experiments/hr02-shared-topic-merge-astra-low-v1-a/` and
`sse_multivector/experiments/hr02-shared-topic-merge-astra-low-v1-b/`.
These inherit the eight/three case split solely to bind each exact Jev baseline.
Catalog cost estimates are not subscription invoices; no paid API commitment
was created. All 68 experiment regression tests and exact prompt/input checks
pass. The motivating semantic regression now passes; all saved hierarchy source
hashes remain unchanged.

## Completed Astra comparison — HR02-NMP06

The remaining 44 pairs completed with unchanged NMP-Jev-v2 / Astra low through
the same subscription configuration. All 44 new calls were valid, with no
retries or reused requests. The eleven NMP05 answers were used directly, not
rerun. No titles, source groups, masks or canonical HR02 artifacts changed.

Across all 55 pairs, Astra answered 44 Yes, ten No and one Uncertain. Reversible
contraction leaves 22 of the 66 original groups, versus 36 with Jev masks and
26 with title-only judgments:

| Branch | Original | Title-based | Jev masks v1 | Astra masks v2 |
| --- | ---: | ---: | ---: | ---: |
| Sleep | 11 | 6 | 2 | 3 |
| Dinner | 8 | 2 | 1 | 2 |
| Art | 4 | 1 | 4 | 1 |
| Children | 8 | 1 | 6 | 1 |
| Coffee | 7 | 1 | 1 | 1 |
| Recipes | 5 | 3 | 2 | 2 |
| Tea | 3 | 2 | 3 | 2 |
| Food | 5 | 2 | 4 | 2 |
| Animals | 6 | 3 | 6 | 3 |
| Emotions | 3 | 2 | 3 | 2 |
| Morning greetings | 6 | 3 | 4 | 3 |

Agent inspection finds a substantially more useful comparison: repeated Children
and Art chains collapse; Dinner remains below Food and dining, Hot tea below
Tea, Processed food below Food, and Sleep/Sleepiness remain distinct. These are
judgments of this selected sample, not an accuracy score or user approval.

Uncertainties remain visible through `?`, without changing any answers:

- The sole repeated-title link is Morning → Morning. The smaller group has
  `Woke up` / `up`, `sunrise`, and `got up early`; Astra rejects equivalence
  with the larger group that also includes greetings. It then merges that
  smaller group with the sunrise/early group. The appropriate scope of the
  waking mask remains unclear; identical saved titles do not settle it.
- The recipe boundary receives Uncertain. The larger group adds only
  `Made` / `made` to recipe masks, which does not say what was made. It remains
  separate, producing Cooking → recipe with the unchanged saved titles.
- The previously recorded baby/Children age-boundary uncertainty remains.

The full Jev-v1 versus Astra-v2 comparison changes both wording and model;
only the earlier eleven-pair Jev-v2 comparison held task text identical across
models. No causal model-only claim is made for the other 44 pairs.

Reusable specs are `../experiment_specs/hr02-{sleep,diverse,remaining}-merge-astra-low-v2.json`.
Receipts and reviews are under the corresponding `sse_multivector/experiments/`
directories. The exporter checks their exact inputs against the saved source
groups and combines them with NMP05 only when prompt/settings agree and every
pair appears exactly once. It records receipt bindings and keeps each model's
assessments separate. Subscription catalog estimates are not invoices.

## Saved hierarchy comparison

The existing category browser exposes Original groups, Title-based merges,
Jev masks · NMP-Jev-v1 and Astra low masks · NMP-Jev-v2 for each tested topic.
The saved Jev-v2 eleven-pair trial is not a full branch view.
Sleep, Dinner, Art and Children
appear first; seven further topics are under Other tested topics. These are
navigation menus, not newly generated hierarchy nodes.

All three methods apply the same **55 tested original pairs**, with **no untested
links** in the displayed branches. The title view now applies all saved title
decisions within those branches; each mask view combines its saved runs.
View labels show tested/total counts; `?` exposes native answers and saved agent
concerns. Native mask answers are never relabeled as containment answers.

All original groups remain in the Original view. Surviving groups retain their
saved titles and masks; no renamed nodes, inferred memberships, semantic parent
repairs or model calls are involved. Links show saved mask-set nesting, not a
validated semantic hierarchy. Browser equal-note and single-child collapsing
are disabled here so they cannot conceal differences between the methods.

```bash
cd /home/dev/src/notedeck_worktrees/algos && \
bash oracle-mvp/sse_multivector/run-merge-comparison.sh
```

Enter/l opens a topic, view or node; Backspace returns. N shows posts, D shows
direct posts, and O shows masks outside the children, individually with IDs;
`[` and `]` switch masks. `?` shows analysis. The UI is read-only: nothing is
approved, edited or merged by browsing.

The reusable offline exporter is [merge_tree_comparison.py](../merge_tree_comparison.py),
configured by [merge-comparison-hr02-v3.json](../merge-comparison-hr02-v3.json).
It validates the saved title/mask experiment receipts through the shared runner,
reuses existing contraction and mask rendering, and refuses to overwrite an
export. Generated categories, source hashes and reversible mappings are ignored
under `target/hierarchy-build-v1/hr02-merge-comparison-v5/`.
Earlier manifests and exports remain intact as comparison provenance.

All 89 comparison, nesting, title-input and experiment regression tests pass.
Verification covers receipt/model binding, split-run coverage, separate model
views and assessments, exact masks, full posts and reversible mappings. The
actual browser accepts the completed export with `--check`. All 66 original
groups and prior decisions remain available; the original and Jev views match
their saved projections. No browser equal-note or single-child collapse is used.
An interactive check verified the four-view menu, the single Children node,
full-post display and individual masks with IDs in O view.

The full delta against NSP-Jev-v3 and its exact edits are reproducible from
`prompt.txt.revision.json`, generated by `experiment.py revise`. The prompt is
versioned separately because its input and question contracts materially differ.

Drafting follows the general principles of concise instructions, separated
inputs and starting without examples from the official OpenAI
[prompting guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively).
That guidance is not evidence of effectiveness for Jev; no OpenAI-model-specific
parameters or reasoning instructions were transferred to this prompt.
