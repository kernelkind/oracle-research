# NMP-Jev-v1 — mask-based node merging

Status: tested on all 55 original pairs in the approved eleven-branch comparison;
not frozen or adopted.
The unchanged title-only NSP-Jev-v3 remains the saved comparison baseline.
The separate [NMP-Jev-v2 trials](../node-merge-prompt-jev-v2/prompt.txt) below use
Jev and Astra low. They are tested, not adopted. The completed Astra view is
available beside the unchanged saved Jev-v1 comparison.
The user accepted the completed Astra merge result on September 28, 2026.
That acceptance was not a production freeze. The user subsequently approved
the separate wider HDBSCAN diagnostic HR02-NMP07 below, followed by the
six-group cross-branch Coffee comparison HR02-NMP08. The subsequent bounded
cross-branch pass HR02-NMP09 is complete and browsable below. Seven later Jev
cycle contractions conflict with mask-merge No answers; these are flagged,
not manually repaired. None of these experiments adopts a production pipeline.

The user approved the wording of the separate
[NSP-Astra-Masks-v1 parent–child prompt](../node-subsumption-prompt-astra-masks-v1/prompt.txt)
below. The prompt is tested experimentally, not frozen. HR02-NSP-MASKS02 expands
the completed 12-pair test to 48 comparisons, with 36 new calls and 12 reuses.
The earlier user-confirmed rejection remains recorded; Preservation remains
unresolved. Initial agent review flagged seven of the 36 new answers. The user
resolved the three linked meat comparisons and confirmed the missed Positive
emotions parent of Enjoyment of food. Fire/Ash, Pizza and Ice/ice cream remain
unresolved; the agent withdrew its likely-miss assessment of Ice/ice cream.
The subsequent HR02-NSP-MASKS03 pass completed all 566 existing candidate pairs
and exported a separate 148-node hierarchy, with 101 reduced links and 76 roots.
It has no cycles; 39 uncertain pairs and three path contradictions remain
unresolved. Existing merges, titles, direct memberships and earlier hierarchies
stay fixed; combining equivalence and placement in one prompt is deferred.

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
agent judgments of this selected sample, not an accuracy score.

On September 28 the user clarified that the Astra merge result looks good.
Record that as acceptance of the overall diagnostic result, not separate
ground-truth labels for all 55 pairs. No answers, prompts or hierarchy data
change with this approval; production adoption and wider testing remain open.

The earlier agent uncertainties remain visible through `?` as provenance,
not prerequisites to accepting the result:

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

## Wider HDBSCAN diagnostic — HR02-NMP07

The user approved applying the accepted NMP-Jev-v2 / Astra-low approach across
the saved HR02 HDBSCAN groups. This does not select M06, rerun clustering,
change prompts, expand memberships or judge new semantic parent placements.
The saved HR02 hierarchy and the accepted eleven-branch comparison stay intact.
Production adoption remains open.

The reproducible selection keeps all 129 original EOM groups and, inside each,
every smaller raw group whose formation distance is strictly lower than its
immediate raw parent's formation distance. An EOM root is always retained.
Each retained group attaches to its nearest retained ancestor. The result is
487 groups and 358 adjacent non-root comparisons, with a synthetic navigation
root above the 129 EOM groups. Cluster IDs are mapped to raw groups by exact
canonical membership, not treated as raw-tree IDs.

hdbscan_nested_groups.py (`03bd9e45:sse_multivector/hdbscan_nested_groups.py`) prepares and exports this
diagnostic offline. hdbscan-nested-hr02-v1.json (`03bd9e45:sse_multivector/hdbscan-nested-hr02-v1.json`)
identifies its saved inputs and approved result sources. Preparation reproduces
all 43 previously tested HDBSCAN groups and all 129 original packets, preserving
mask IDs, vector-sorted instance order and the title adapter's exact same-post
mask deduplication. It verifies the historical source hashes and validates saved
experiment receipts before binding an answer to an identical rendered prompt.
For multiple matching answers, the same original group/pair ID takes precedence,
then the manifest's saved-report order. No matching-title heuristic is used.

There are 37 saved merge answers and 321 new comparisons. The shared experiment
runner uses unchanged NMP-Jev-v2 / `openai-codex` / `gpt-6-astra` / `low`, ten
concurrent calls, with the existing strict choice schema and no output-token
cap or paid fallback. Only Yes contracts an original edge. No and Uncertain
keep both groups; failed or invalid answers block export rather than becoming
No. No newly adjacent pair is rejudged after a contraction. The larger group's
membership already contains its children and is preserved; the original-to-
surviving mapping records every contraction.

Only surviving groups lacking exact saved TPv38/Astra-low titles are submitted
for titles, at the existing six-call concurrency. Removed groups are not titled.
Before merging, 168 groups have saved titles; the other 319 represent at most
313 unique title inputs. Model execution, retries, usage and reviews remain in
`experiment.py`; the offline helper does not execute models or fabricate reports.

Generated artifacts are isolated under
`target/hierarchy-build-v1/hr02-hdbscan-merge-v1/`. Merge and title receipts use
`sse_multivector/experiments/hr02-hdbscan-{merge,titles}-astra-low-v1/`.
The dedicated launcher is run-hdbscan-merge.sh (`03bd9e45:sse_multivector/run-hdbscan-merge.sh`), using
the existing category browser without equal-note or single-child collapsing.
The links are saved HDBSCAN nesting, **not validated semantic parent placement**.
The groups cover 629 of 1,674 source masks; the other 1,045 remain accessible at
the navigation root rather than being silently discarded.

The run completed with all 321 new merge answers and all 27 required new titles
valid, without retries or baseline reruns. Together with the 37 saved answers,
the 358 comparisons contain 326 Yes, 23 No and nine Uncertain. Yes-only
contraction leaves **161 groups**: the 129 original roots and 32 retained
subdivisions. The other 134 surviving titles use exact saved answers. This is
a diagnostic output, not a user-approved full hierarchy.

Agent inspection confirms Dinner under Food and dining and separate
Sleep/Sleepiness under Sleep and tiredness. Seven parent-child links still have
the same title ignoring capitalization; titles alone do not justify merging
them. Separate original roots, including multiple Coffee and Nostr groups,
remain separate because cross-branch merging and placement were not tested.

The agent recorded two title concerns through `experiment.py review`, separately
from user judgments and without changing generated outputs:

- **Mountain passes in Afghanistan** invents a shared geographic interpretation
  for `Kreik` and `Khyber Pass`. Their full posts concern a Belgian drink and a
  restaurant. This title is rejected in agent review.
- **gianguja and guarani** repeats two names without establishing a shared topic.
  The source posts concern a food product and a language. Agent review marks
  this uncertain rather than assuming a better common title exists.

The 93 offline selection, comparison, nesting, title-input and experiment tests
pass. Source-hash checks preserve the canonical HR02 files and accepted sample;
the export replays every merge from validated receipts. The actual browser
passes `--check`. An interactive check confirms that leaf navigation opens
full posts and O displays individual masks with IDs. Generated artifacts and
reviews remain ignored; subscription catalog estimates are not paid invoices.

```bash
cd /home/dev/src/notedeck_worktrees/algos && \
bash oracle-mvp/sse_multivector/run-hdbscan-merge.sh
```

The user requested a smaller review rather than inspecting all 32 subdivisions.
The subsequent cross-branch Coffee comparison is recorded below; it does not
introduce parent placement or change this saved view.

## Cross-branch Coffee comparison — HR02-NMP08

The user approved comparing six surviving original groups: four titled Coffee
(case-insensitive), Coffee beans and coffee shop. They have disjoint mask-ID
sets and no children. Their titles identify this selection for the reader;
the model receives only the two separate arrays of masks, as before.

The offline `prepare-pairs` command validates the original sources and selected
surviving memberships, then prepares every unordered pair in sorted group-ID
order. It saves selection/source provenance without adding tree edges, applying
merges or changing titles. The default adjacent-pair preparation is unchanged.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/hdbscan_nested_groups.py prepare-pairs \
  target/hierarchy-build-v1/hr02-hdbscan-merge-v1 \
  target/hierarchy-build-v1/hr02-cross-branch-coffee-v1 \
  --groups S2f31604022 S54b2843dd5 S64fcf6c1d7 S794ece942d S6dde8fffb9 Sec383f12a1
```

That output already exists; preparation refuses to overwrite it. The tracked
experiment spec (`03bd9e45:sse_multivector/experiment_specs/hr02-cross-branch-coffee-astra-low-v1.json`)
uses unchanged NMP-Jev-v2 / Astra low with the HR02-NMP07 settings. The shared
runner completed all **15 new calls** with valid answers, no retries or reuse:

- All six comparisons between the four Coffee groups: **Yes**.
- All nine other comparisons: **No**, keeping coffee shop and Coffee beans
  distinct from Coffee and from each other.
- No Uncertain answers or inconsistent equivalence chains in this sample.

Agent inspection agrees with these decisions; they are not human-reviewed
ground truth or a general accuracy estimate. Combining only the four Coffee
groups would retain 17 masks from 14 posts, but **no merges were applied**.
No containment judgments, new titles or hierarchy changes were made.

Receipts and native usage are under
`sse_multivector/experiments/hr02-cross-branch-coffee-astra-low-v1/`.
All 95 relevant regression tests pass; original source replay and the saved
merged-tree hash remain unchanged. This test did not settle general comparison
selection or conflict handling; the subsequent approved diagnostic rule is
recorded below. It does not establish that merging separate branches can repair
earlier bad merges.

## Bounded cross-branch pass — HR02-NMP09

Approved September 28: retain the 161 HR02-NMP07 surviving groups and perform
one fixed comparison pass before generating an actual Jev-placed hierarchy.
The purpose is a useful browsing result with acceptable errors, not perfect
grouping. Subjects, masks, SSE vectors, HDBSCAN groups and all prompts stay fixed.
No independent regrouping model, manual answer overrides or repeated rounds.

cross_branch_merge.py (`03bd9e45:sse_multivector/cross_branch_merge.py`) provides offline preparation,
consolidation and placement preparation; only the shared experiment runner
performs inference. It replays the prior in-branch merge from verified receipts,
validates the saved titles, and freezes inputs in
`target/hierarchy-build-v1/hr02-cross-branch-v1/`.

Selection is the union of two lists for each group:

- Five nearest separate groups, ranked by cosine of the mean of unit mask
  vectors. Exact same-post masks use the existing deduplication rule.
- Up to five nearest separate groups whose titles match after trimming and
  case folding. Titles nominate comparisons; they do not decide equivalence.

Groups sharing masks are not cross-branch candidates. Either group can nominate
a pair; unordered pairs are deduplicated. Ties use stable group IDs. The two
lists cap nominations at ten per group. They do not guarantee completeness,
bound mask-input sizes, or establish production-scale token costs. Five is a
fixed diagnostic choice, not a learned semantic threshold.

This preparation produces **593 pairs**: initially 579 new and 14 reusable.
The unchanged NMP-Jev-v2/Astra-low configuration has ten concurrent calls,
300-second timeouts and no paid fallback. The run bound is 1,158 new attempts,
including at most two total attempts per case under the provider-only retry
policy. Exact-request reuse remains enabled; reused answers are not new trials.

The approved consolidation rule joins Yes-connected groups unless a recorded
No opposes any pair within the proposed combination. In that case, the entire
combination remains separate for this run. No chooses neither an alternative
subset nor a preferred Yes edge. Uncertain creates no merge edge; untested pairs
are not No. Prior No answers from the accepted Astra in-branch stage and the
Coffee comparison remain constraints. Original groups, exact masks and aliases
remain recoverable; merged IDs derive from sorted original group IDs.

Only new combined groups need v38/Astra-low titles. Untouched groups retain their
verified titles. The next stage uses the existing NSP-Jev-v3/Jev directional
placement workflow and its existing provisional graph rules, not HDBSCAN
nesting as semantic parent placement. All outputs are isolated from prior views.

**Current result:** all 593 comparisons are valid: 26 Yes, 525 No and 42
Uncertain. The runner records 580 new attempts and 17 reused cases. Three HTTP
503 failures and one explicit Codex processing error were retried successfully.
The user approved narrowly recognizing that HTTP-200 stream failure; local
aborts, validation failures, unknown errors and the two-attempt limit are
unchanged. No completed answer was rerun or missing answer invented.

The approved rule leaves **148 groups**, combining 20 groups into seven and
keeping one four-group meat-related combination separate because recorded No
answers oppose it. All seven combined titles validated with unchanged
v38/Astra low: two new calls and five exact-request reuses. Other titles are
unchanged. Placement has 21,756 directed cases with unchanged NSP-Jev-v3/Jev,
ten concurrent calls and exact-request reuse. The user approved fixing repeated
source-file reads in the shared runner after offline preparation spent over
19 minutes checking reuse. Operation-scoped file loading
retains the existing receipt, schema, invocation and provenance checks. The
pre-run 21,756-case inspection completed in 5.5 seconds: 15,052 reusable cases
and 6,704 new requests. The saved experiment resumed with an explicit runner
upgrade reason and a 13,408-new-attempt allowance, including provider retries.

All **21,756 decisions validated**, with 6,358 new calls and 15,398 reused answers;
no failures, retries or unknown charges. The shared report records
**$0.111736548** in native Jev charges.

The existing Jev cycle-contraction stage leaves **137 nodes, 99 reduced links
and 57 top-level nodes**. Nine combined titles required nine new unchanged
v38/Astra-low calls; all validated. No Luna calls, prompt revisions, manual
relationship repairs or membership expansion were introduced. The separate
placement-title spec (`03bd9e45:sse_multivector/experiment_specs/hr02-cross-branch-placement-titles-astra-low-v1.json`)
selects Astra explicitly; the older generic naming helper's Luna default was
not used.

**Unresolved stage conflict:** seven combined nodes include a pair that the
mask-based stage judged not equivalent: Meat consumption, Eggs, grownostr and
food growing, Chickens and chicken products, Food preservation, Peace, and Food
preparation (the final displayed names). Six opposing No answers came from the
accepted in-branch comparisons and one from this cross-branch pass. The later
title-only Jev stage nevertheless connected each pair in a cycle and combined
it under the pre-existing graph rule. Thus this combined result does not enforce
the mask-stage No constraints throughout placement. This disagreement remains
open, not resolved by changing either answer or inventing a cycle-repair rule.
The root and affected nodes' `?` analysis disclose it; exact source pairs and
stage mappings are in `view/verification.json`.

The isolated browser export retains all **100 posts and 1,674 original mask
IDs**: 629 grouped masks and 1,045 ungrouped masks at the navigation root.
It uses Jev edges, not HDBSCAN nesting, and adds no display-only collapsing.
Original sources and earlier views are unchanged. The browser's `--check`
passes; interactive checks confirm leaf `l` opens full posts and `O` displays
individual masks with IDs. These are mechanical checks, not semantic approval.

```bash
cd /home/dev/src/notedeck_worktrees/algos && \
bash oracle-mvp/sse_multivector/run-cross-branch-hierarchy.sh
```

All 247 relevant offline tests pass, covering capped deterministic selection,
No-vetoed Yes chains, exact-mask provenance, saved/new title binding, existing
Jev graph/export integration, individual-mask export, the new launcher's
arguments/refusals, root-only ungrouped masks, conflict reporting without graph
changes, and shared-runner regressions. Generated artifacts remain ignored.
Subsequent read-only inspection identified missing browsing routes and the
flagged stage conflicts. The user approved the parent–child prompt wording
below, not another hierarchy run or production adoption.

The reusable specs are
merges (`03bd9e45:sse_multivector/experiment_specs/hr02-cross-branch-merge-astra-low-v1.json`),
new titles (`03bd9e45:sse_multivector/experiment_specs/hr02-cross-branch-titles-astra-low-v1.json`) and
placement (`03bd9e45:sse_multivector/experiment_specs/hr02-cross-branch-placement-jev-v1.json`).
Receipts are in `sse_multivector/experiments/hr02-cross-branch-merge-astra-low-v1/`.

## Parent–child prompt — NSP-Astra-Masks-v1

The user approved drafting a separate mask-based parent–child question before
combining placement and equivalence. [NSP-Astra-Masks-v1](../node-subsumption-prompt-astra-masks-v1/prompt.txt)
is **wording approved September 28, 2026; tested experimentally; not frozen**.
Its revision base is the
accepted NMP-Jev-v2 text, not a new combined prompt or the title-only Jev prompt.
The existing groups, merge answers, titles and browser exports are unchanged.

Keep NMP-Jev-v2's grouped-mask inputs and interpretation instructions verbatim.
Change the question to `parent_child`, with one choice per pair:
`a_parent`, `b_parent`, `neither`, or `uncertain`. Containment must be strict:
the narrower topic necessarily concerns the broader topic, not merely a related
topic. Equivalent topics produce `neither` for this placement-only question;
this does not reject equivalence or trigger a new merge. `uncertain` remains
unresolved, not a negative answer. No title, full-post context, tree position,
model explanation, confidence score or example is added to the model input.
The JSON question envelope is retained from the successful Astra mask trials.

The intended diagnostic keeps the 148 pre-Jev HR02-NMP09 groups fixed, using
Astra low and the shared experiment runner. Mapping the saved in-branch links
and cross-branch shortlist onto those groups yields 32 in-branch pairs and
535 cross-branch pairs, with one pair in both lists: **566 unique pairs**.
This is the full candidate inventory, not a full-pass call approval.
It excludes retries and extra ancestor comparisons; request reuse may reduce
actual calls. This count does not describe a combined merge/placement run.

The wording, initial 12-pair run and subsequent 48-pair expansion were approved.
The prepared sample and output schema are described below. Offline construction
was subsequently approved and implemented: strict-containment cycles stop
export, while other path contradictions are retained and reported. How to
resolve conflicts and whether to add ancestor comparisons remain open. No
existing Jev validator or cycle-merging code is reused for the new answer type.
Any later full pass requires separate authorization. Human review evaluates
the automated result; it does not supply undisclosed placement repairs.

The [official OpenAI prompting guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively)
informed the short task, explicit answer meanings and absence of examples or
requested chain-of-thought. It does not establish semantic accuracy. The shared
`experiment.py revise` command records the exact base hash and edits in the
adjacent `.revision.json`; the accepted merge prompt is unchanged.

### Placement test — HR02-NSP-MASKS01

Status: **complete, 12 structurally valid answers, 12 new calls, no retries or reuse**.
Uses unchanged
NSP-Astra-Masks-v1 and `openai-codex / gpt-6-astra / low`, four concurrent calls
and 300-second timeouts. This is the existing subscription route: no additional
API charge and no paid fallback. The user authorized at most 24 new
attempts, including the existing provider-only retry allowance; no independent
repetitions. Request reuse remains enabled; preparation found no reusable answers.
The run used 12 attempts; further inference is not authorized by that allowance.

The offline `prepare-parent-child` command in
cross_branch_merge.py (`03bd9e45:sse_multivector/cross_branch_merge.py`) replays and verifies the saved
merge decisions and title receipts. It maps both endpoints of each saved pair
onto the 148 surviving groups, removes self-pairs and deduplicates unordered
pairs. A pair in both sources belongs to the in-branch sample. Within each source,
sort by the SHA-256 of compact JSON `["parent-child-v1", source, A, B]`, with
sorted surviving IDs for A/B and stable ID tie-breaking, then take six pairs.
This gives six of 32 in-branch pairs and six of 534 cross-branch-only pairs.
It is a fixed sample without semantic selection or expected-answer filtering,
not proof of representativeness or candidate coverage. No new pairs are invented.

Each comparison receives the complete deduplicated masks of its current groups,
including masks added by accepted merges. Human-readable titles, mask IDs,
full posts and the original pair sources remain review evidence only. The
spec (`03bd9e45:sse_multivector/experiment_specs/hr02-parent-child-astra-masks-v1.json`) uses the accepted
choice envelope, now requiring `parent_child.type = "choice"` and one of
`a_parent`, `b_parent`, `neither`, `uncertain`. No equivalence or graph rule is
applied to these answers. Agent assessments are recorded separately through
`experiment.py review` in `experiments/hr02-parent-child-astra-masks-v1/`:
10 accept, one reject and one uncertain. The user separately confirmed the
rejection below; no verdict is inferred for the other cases.

The user-confirmed error is **Food consumption → Clean, simple dishes**: the masks
describe meal qualities and a dish's appearance, which need not discuss eating.
The agreed answer is **neither**, not B-parent. This is saved as a user review,
without modifying the model answer or any hierarchy. The user subsequently
left Preservation unresolved and approved
expanding the experiment instead of forcing a verdict.
The uncertain assessment is **Preservation → Preservation**: both groups have
the same generic preservation masks, while B adds `foodpreservation`. That
does not clearly settle whether B is narrower or expresses the same broad topic.
The remaining assessments are agent-only, not a ground-truth score. The model's separate
`uncertain` answer for the mixed food/Paraguay group is considered reasonable.
No prompt revision, manual placement, merge or browser change follows from
this test. The separately approved expansion is recorded below.

Preparation commands already completed (they refuse to overwrite existing artifacts):

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/cross_branch_merge.py prepare-parent-child \
  target/hierarchy-build-v1/hr02-cross-branch-v1 \
  target/hierarchy-build-v1/hr02-parent-child-astra-masks-v1 --per-source 6 && \
python3 sse_multivector/experiment.py prepare \
  sse_multivector/experiments/hr02-parent-child-astra-masks-v1 \
  --spec sse_multivector/experiment_specs/hr02-parent-child-astra-masks-v1.json \
  --history-root sse_multivector/experiments
```

### Expanded placement test — HR02-NSP-MASKS02

Status: **complete, 48 structurally valid comparisons: 36 new calls and 12
exact-request reuses, no failures or retries**. The user approved keeping
NSP-Astra-Masks-v1 unchanged and expanding the sample while leaving Preservation
unresolved. Model, concurrency and timeout match HR02-NSP-MASKS01. The run used
`--max-new-attempts 72`; it sent only 36 subscription calls, with no paid fallback.
The runner's $0.28714 catalog estimate is not a subscription bill.

The new spec (`03bd9e45:sse_multivector/experiment_specs/hr02-parent-child-astra-masks-v2.json`) changes
only the dataset path. The same deterministic selection uses `--per-source 24`,
adding 18 in-branch and 18 cross-branch pairs. The original 12 inputs are
identical and reused, not independent new observations. Every input still
contains its groups' complete deduplicated masks. Saved artifacts are under
`target/hierarchy-build-v1/hr02-parent-child-astra-masks-v2/` and
`sse_multivector/experiments/hr02-parent-child-astra-masks-v2/`.

All 36 new cases have separate initial agent reviews: **29 accept, two reject,
five uncertain**. These are not measured accuracy. Subsequent user verdicts on
the three meat comparisons and the positive-emotions comparison are recorded
separately, without replacing the initial reviews. Updated agent reviews retain
Fire/Ash and Pizza as uncertain and change Ice/ice cream to uncertain. Titles
below identify the groups for human review; the model saw masks, not titles.

| Groups | Model answer | Review status |
|---|---|---|
| Ice and ice cream / ice cream | Neither | Uncertain; the agent withdrew the likely-miss assessment. Additional ice masks do not by themselves establish a broader shared topic. |
| Enjoyment of food / Positive emotions | Neither | User rejected: expected B-parent, Positive emotions containing Enjoyment of food. |
| Fire and ashes / Ash | Neither | Uncertain. Source wording supports literal fire, but the topic-containment boundary remains unsettled. No firm user verdict. |
| Pizza and restaurants / pizza | Neither | Uncertain. Chain comes from a barbecue-chain post; the additional generic masks leave A's shared topic unclear. |
| meat / Meat consumption | A parent | User rejected: same topic, so expected neither. |
| Food consumption / Meat consumption | A parent | User rejected: expected neither. |
| Beef / Meat consumption | B parent | User accepted. |

The last three comparisons use the exact same group titled Meat consumption,
whose masks mix plain `meat`, `carnivore`, `diet`, `meat eaters` and explicit
`eat meat` wording. The user agreed that the most specific shared topic is Meat,
not specifically eating meat: the bare `meat` masks do not specify eating.
This makes the two meat groups equivalent in topic, rejects Food consumption
as parent of the disputed group, and accepts the disputed group as parent of
Beef. The three user verdicts were saved through the shared review CLI. They
do not authorize a merge, rename or graph change. The choices alone do not
reveal whether the model inferred inconsistent topics or misjudged containment.
The user also confirmed Positive emotions as the missed parent of Enjoyment
of food: pleasure or satisfaction concerning food is narrower than the positive
feelings expressed by B's happiness, joy and gratitude masks. This user rejection
was saved through the shared review CLI, without editing the model answer.

The flagged-case walkthrough is complete. Fire/Ash, Pizza and Ice/ice cream
remain unresolved alongside the earlier Preservation comparison. The source
inspections did not establish a definitive parent relationship for those pairs;
in particular, mask-set inclusion is not proof of topic containment. The user
subsequently approved the offline construction below with the unchanged prompt.
No further calls or prompt changes are authorized by these review decisions.

Verification: 18 relevant tests passed; frozen prompt/settings, the 12 reused
inputs, all 48 complete group-mask inputs, source hashes and saved receipts
were checked. No model answers, merges, links, titles or masks were changed.

### Offline parent–child construction

The approved `package-parent-child` command in
cross_branch_merge.py (`03bd9e45:sse_multivector/cross_branch_merge.py`) replays the fixed groups,
titles, source hashes and deterministic sample before consuming saved experiment
receipts. It refuses incomplete, duplicated or changed selected comparisons,
prompt text or model settings. It makes no model calls and requires a new output
directory, preserving previous experiments.

The native four-choice answer explicitly determines both strict-containment
directions. Only its accepted direction creates a link. Neither may mean
equivalence, but never authorizes a merge. Uncertain creates no link and remains
recorded as unresolved. Untested pairs receive no fabricated decisions. Agent
or user review verdicts do not override native choices.

The existing graph analyzer now supports explicitly partial coverage; its
default all-pairs completeness requirement remains unchanged for earlier
callers. It retains all nodes, reports cycles and rejected-but-reachable
directions, and reduces redundant links only in acyclic graphs. A cycle saves
`graph.json` and `provenance.json`, then stops browser export. No link is chosen
for deletion and no node is merged. Other path contradictions remain visible
in the graph diagnostics and affected nodes' analysis.

The saved-answer construction at
`target/hierarchy-build-v1/hr02-parent-child-astra-masks-v2-view-verified/` retains all
**148 nodes and 100 posts**. Its **48 comparisons** yield **20 links, 22 neither
answers and six uncertain answers**; **518 candidate pairs remain untested**.
Only 70 nodes occur in the sample's comparisons; the other 78 remain present.
There are no cycles or rejected-but-reachable directions. The 96 directed rows
are the two meanings of each saved choice, not 96 calls. Original direct masks,
mask IDs and root-only masks are preserved; memberships are not expanded.

The existing hierarchy browser passes `--check`. Five new production-path tests
cover sparse coverage, all answer meanings, review independence, mismatched
inputs, source-mask export, and saving cycle evidence without exporting a
browser view. The broader 168-test regression suite passed. A second offline
export reproduced identical graph and browser files; its provenance records
HD07 (`strict-mask-parent-child-v1`). This is a partial
construction check, not a finished hierarchy or approval of its placements.

Completed command (refuses to overwrite its output):

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/cross_branch_merge.py package-parent-child \
  target/hierarchy-build-v1/hr02-cross-branch-v1 \
  target/hierarchy-build-v1/hr02-parent-child-astra-masks-v2 \
  sse_multivector/experiments/hr02-parent-child-astra-masks-v2 \
  target/hierarchy-build-v1/hr02-parent-child-astra-masks-v2-view-verified
```

### Full candidate pass — HR02-NSP-MASKS03

The user approved completing the remaining 518 candidate pairs with unchanged
NSP-Astra-Masks-v1 / Astra low and exact-request reuse, then checking the graph
and exporting to the existing browser only if acyclic. The separate
spec (`03bd9e45:sse_multivector/experiment_specs/hr02-parent-child-astra-masks-v3.json`) differs from
the 48-pair spec only in its dataset path. Concurrency remains four, with the
existing provider-only retry policy and at most two attempts per new case.
These use the subscription route, without paid API fallback.

Preparation selected all **566 existing unique pairs**: 32 nominated by tree
links and 534 additional cross-branch pairs. One pair occurs in both sources
and is counted with the tree links. `--per-source 566` exhausts the existing
selection rule; it introduces no new pairs or ranking. The shared runner
confirmed **48 reusable requests and 518 new requests**, without inference
during preparation. Inputs are saved separately under
`target/hierarchy-build-v1/hr02-parent-child-astra-masks-v3/`; the experiment is
`sse_multivector/experiments/hr02-parent-child-astra-masks-v3/`.

HD07 remains unchanged: native answers only, no review overrides, new merges,
renaming or membership expansion. A cycle saves evidence and stops browser
export; it does not authorize repairs. Earlier experiments remain untouched.

The run completed with **566 valid answers**, **48 exact-request reuses** and
**520 new attempts**: 518 new requests plus two successful retries after
HTTP 503. No malformed responses, terminal failures or unrun cases remain.
The runner reported 187,395 input tokens and 27,088 output tokens, including
15,984 reasoning tokens. These are subscription calls, not a paid API bill.

The native answers produced 129 strict-parent links, 398 neither answers and
39 uncertain answers. All 148 nodes were compared. Offline construction reduced
the accepted links to **101**, with **76 roots**, **no cycles**, and all **100
posts** retained. The browser adds one synthetic root above those 148 nodes;
it is not a new inferred topic.

Three rejected directions remain reachable through accepted links. Using the
unchanged titles as labels, the shortest conflicting paths are:

- Positive emotions → Happiness and joy → Enjoyment of food.
- Positive emotions and attitudes → Positive emotions → Happiness and joy → Enjoyment of food.
- nostr → foodstr → Preservation → Vacuum sealing.

Each endpoint comparison answered neither. These are internal contradictions,
not proof of which comparison is wrong. They are flagged in the graph and node
analysis; no review correction or repair was applied.

The view is saved at
`target/hierarchy-build-v1/hr02-parent-child-astra-masks-v3-view/`. The existing
browser's `--check` passed. A second offline build at the `-view-verified` path
produced byte-identical graph and browser files. The 137-test runner/graph
regression suite passed. The separate planning-page browser test could not
start because Python's `websocket-client` dependency is unavailable.

Open the completed diagnostic view:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
target/infomap-review-build/debug/sse-subject-navigation \
  --categories target/hierarchy-build-v1/hr02-parent-child-astra-masks-v3-view/categories.json \
  sse_multivector/hierarchy-refresh-v1/masked-posts.json
```

Next: review this hierarchy's browsing result before changing individual
components. Completion and structural validation do not establish semantic
quality or production adoption.

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

The reusable offline exporter is merge_tree_comparison.py (`03bd9e45:sse_multivector/merge_tree_comparison.py`),
configured by merge-comparison-hr02-v3.json (`03bd9e45:sse_multivector/merge-comparison-hr02-v3.json`).
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
