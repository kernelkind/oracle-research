# GDC09 navigation research

The original GDC09 tree, masks, vectors, labels, and browser remain unchanged.
The objective is a repeatable construction method, not a hand-repaired 100-note tree.

## Required hierarchy-processing stages

These are requirements for the formal construction process, not optional review
cleanups. They do not authorize a new run or change the frozen experiment data.

1. **Deduplicate identical masks within each post before SSE.** Treat masks with
   the same post ID and identical ordered source-byte ranges as one encoder
   input. Preserve every originating subject and mask ID as provenance. Equal
   wording at different positions or in different posts is not this identity
   rule; overlapping but different selections remain distinct. Title generation
   and review must also use the same deduplicated mask inventory, so aliases do
   not become repeated evidence. Keep valid empty subject masks recorded without
   generating vectors for them; invalid outputs are not empty masks.
2. **Merge nodes with identical mask sets before hierarchy generation.** Compare
   sets of mask identities defined in stage 1, after resolving duplicate-mask
   aliases, rather than labels, post sets or vector equality. Preserve every
   original node ID and its provenance in the merged node's record. Retain
   strict subsets: a smaller mask set can represent a useful narrower category,
   so containment alone does not authorize merging.
3. **Collapse equal-note parent–child steps before publishing the browsable
   hierarchy.** After obtaining an acyclic category graph and computing each
   category's complete post set, including descendants, collapse parent–child
   navigation steps whose complete sets are equal. Equality is of post IDs, not
   just counts or directly assigned posts. Different masks do not justify a
   click that returns exactly the same posts. Preserve all source categories,
   masks, IDs and their mapping to the displayed hierarchy, and preserve the
   surviving destinations' post memberships and mask evidence. Keep the raw
   category graph separately; this is not a claim of semantic equivalence.

Beyond exact mask-set identity, semantic consolidation remains provisional.
The opt-in HD02 experiment merges mutually reachable nodes; it does not establish
that cycles mean genuine semantic equivalence. Identical labels or equal post
sets alone do not authorize merging.
The existing `true_graph_equivalence.py` replays explicit reviewed approvals;
it does not generate them. Its cutoff-based checks also must not silently be
substituted for the current native-answer graph rule.

**Merged-node naming — implemented, HR02 six-node naming complete:** after a
merge, use the [frozen v38 title prompt](../hdbv2-node-description-probe-v38/prompt.txt)
with the approved teacher configuration on the combined masks, deduplicated by
the same-post exact-mask identity above. Generate a displayed title rather than
arbitrarily selecting a member's title; preserve all original titles and node
IDs. This is a naming call only, not a merge decision or a change to the saved
links. It does not trigger another TRUE pass. The approval does not authorize
inference or rewrite historical titles, scores or hierarchy artifacts. HR02
now uses Astra low for its six merged titles, as explicitly approved; the
earlier Luna-max naming results remain unchanged.

The [reversible design-decision register](../../docs/planning/release-decisions.md#reversible-hierarchy-design-decisions)
tracks the native-answer rule (HD01), provisional cycle merging (HD02), the
candidate rule for preserving links despite conflicting answers (HD03),
merged-node naming (HD04), and stable merged IDs derived from original member
IDs (HD05). These statuses must remain distinct: a candidate is
not an adopted rule. Future run manifests must identify the selected policy
versions and retain the pre-merge nodes, all TRUE answers, mask origins and title
inputs/outputs so alternatives can reuse unchanged work. Both merge stages,
title collection and browser export are connected in the offline construction
path below. The four-node naming check is complete; validation on the full
rebuilt hierarchy remains. This register authorizes no new run.

### Reversible merge stage

`true_graph_merge.py` implements HD01–03 and HD05 as a separate derived graph.
It requires complete native TRUE answers, contracts strongly connected
components, and preserves every accepted external edge with its original score
IDs. It retains all original titles, answers, packets and cycle/conflict
diagnostics, plus policy versions and SHA-256 hashes of canonical JSON inputs.
Singleton IDs survive; merged IDs hash the sorted original member-ID list.
Rebuild from the saved `source` payload to try another policy; no raw data is
rewritten and no synthetic TRUE answers are created for merged titles.

Masks are deduplicated within each output node by post ID and ordered byte
spans, retaining every contributing instance. Merged titles are explicitly
`null`/`pending`, with `naming_source_packets` ready for the existing title
adapter and frozen v38 prompt. The saved default spec uses Luna max; HR02
overrides model/effort to Astra low through `experiment.py prepare` without
editing that saved spec. No naming inference is performed by merge preparation.
Do not pass this artifact off as scored titles to the historical exporter:
`hierarchy_build.py package` validates the merge and its naming experiment
separately, then uses the shared browser renderer. `hierarchy_build.py nodes`
implements pre-TRUE identical-mask-set node consolidation; it is distinct from
deduplicating masks within a node.

The September 24 offline replay matched the saved NEv2 component partition,
edge contributors and reduced edges: **24 → 19 nodes**, 14 external edges,
12 reduced edges, all 177 mask origins and 75 posts preserved. Reprocessing
original TRUE10 matched TRUE11's partition and edges modulo new IDs:
**60 → 58 nodes**, 48 external edges, 36 reduced edges, 232 mask origins and
77 posts preserved. Every original node's recursive post set and external
reachability are checked by the implementation. The known wrong Beef / Beef
products merge remains visible; this is mechanical validation, not approval of
every merge. No new model calls or full hierarchy run were made.

For example, replay NEv2 into a new ignored artifact (the command refuses to
overwrite an existing output):

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/true_graph_merge.py \
  target/node-equivalence-graph-v2/titles.json \
  target/node-equivalence-graph-v2/scores.json \
  sse_multivector/hierarchy-refresh-v1/source-packets.json \
  target/node-equivalence-graph-v2/reversible-merge-v1.json
```

For original TRUE10, recover original source packets from
`TRUE10/derived/canonical.json`: start with `source_packets.packets`, then replace
packets by ID with each `consolidations[].source_packets` entry. Use the original
`TRUE10/titles.json` and `TRUE10/graph/scores.json`, not the manually consolidated
scores. Keep original reviewed artifacts untouched. This offline check is not
yet the separate published comparison view required by HD06.

### Offline construction path

`hierarchy_build.py` connects the saved-data stages without executing models:

1. `nodes SOURCE_PACKETS OUTPUT_DIRECTORY` compares sets of post IDs and ordered
   byte spans. Equal sets merge; strict subsets stay. Original packets and ID
   mappings are saved, together with a v38/Luna-max title experiment spec.
2. Use the existing `experiment.py prepare/run` workflow for titles. `true-inputs
   NODES_JSON TITLE_EXPERIMENT OUTPUT_DIRECTORY` revalidates receipts, frozen
   settings, complete inventory and exact inputs, then emits all directed TRUE
   inputs. It can collect existing matching results without rerunning titles.
3. After the existing TRUE scorer/reuse workflow supplies complete scores,
   `merge TITLE_DIRECTORY SCORES_JSON OUTPUT_DIRECTORY` applies HD01–03. IDs
   use original members across both stages, not intermediate merged IDs. The
   artifact retains pre-TRUE consolidation and all original TRUE evidence.
4. Its naming spec goes through the same `experiment.py` workflow. `package
   MERGE_JSON SOURCE MAPPING OUTPUT_DIRECTORY --naming-experiment EXPERIMENT`
   binds those results to the combined masks and changes labels only. Pending
   names block publication. With no cycle merges, omit the naming experiment.
   `naming MERGE_JSON OUTPUT_DIRECTORY` also prepares naming for an existing
   standalone reversible-merge artifact.

Output directories are exclusive and locally ignored. The package contains
`categories.json`, named graph/membership evidence and original provenance.
The existing browser opens it with `--categories`, the original source file,
and `--collapse-equal-note-steps`; individual masks retain original IDs and
aliases. The historical `hierarchy_refresh.py` v21 path and its artifacts are
unchanged. Model execution, cache identity checks and spending approval stay
with their existing tools, not this offline module.

September 24 checks: all **129** HRv1 packets remain distinct; all saved v38
titles match and produce **16,512 prepared inputs, not scored comparisons**.
Preparation of the four-case NEv2 merged-naming experiment made zero model calls.
Tests cover both merges through naming and browser export, using synthetic
responses. Separately, an export of the saved acyclic 58-node baseline passed
the actual browser's `--check` with equal-note collapse. That is an integration
check, not the new HD06 reprocessed baseline or live merged-title validation.

**HR02 — second 100-post hierarchy:** generate a hierarchy the user is pleased
with. The user reaffirmed that this experiment is not an optimization exercise
or teacher-selection comparison. Keep the architecture unchanged; model
changes and comparison runs require separate approval. HR02 names the experiment
for discussion, without renaming existing artifacts or changing frozen run IDs.
The earlier scoring manifest retains `HRv1-full-v38`; the current Astra-title
run uses `HR02-v38-gpt-6-astra`.

**NSPv2 — diagnostic subsumption prompt, tested, not production-frozen:** the
user approved the shorter [NSPv2](../node-subsumption-prompt-v2/prompt.txt) and a
four-pair pilot, both directions, with Astra low. The shared runner completed
eight subscription calls: eight valid outputs, no retries or reuse. All eight
matched the agent expectations recorded before inference; the corresponding
saved TRUE answers matched four. These deliberately selected failures and one
working control do not estimate general accuracy. No uncertainty answers
occurred in that first batch.

The pairs were Food and drink / Bread, nostr / Food and drink, coffee / Coffee,
and Amusement / Having a good day. All titles exactly match original HR02
inputs before TRUE's semantic merges. Only the two titles and the prompt went
to the model; saved TRUE decisions and agent expectations stayed in review-only
evidence. TRUE and NSPv1 were not run. The experiment and receipts are in
`experiments/nspv2-hr02-four-pairs-v1/`; the reusable
[spec](../experiment_specs/nspv2-hr02-four-pairs-astra-low.json) fixes the prompt,
model and output contract. Agent assessments are saved through the runner,
separately from user judgments. NSPv1 remains an untested, rejected draft kept
as NSPv2's revision source, not a current candidate.

The user approved a second four-pair batch only on the condition that its
judgments be reusable in the eventual diagnostic hierarchy. Unchanged NSPv2 /
Astra low completed eight new subscription calls, all structurally valid, with
no retries or reuse. Cooking / Food and cooking, Animals / Dogs, and Music /
Festive gatherings matched all six pre-run agent expectations; saved TRUE
matched four of those six. These are selected cases, not an accuracy estimate.
For coffee shop / coffeechain, both pre-run expectations were unresolved. Astra
answered Yes / No by interpreting coffeechain as a chain of coffee businesses.
The source node instead contains `#coffeechain` / `coffeechain` masks. Both
justifications are rejected in agent review; the reverse No is not counted as
verified correct merely because it may be a defensible link decision. No model
answer used `uncertain`, so offering that option did not prevent an unsupported
interpretation. The intended title-only boundary remains unresolved.

The user subsequently confirmed that the node title should have preserved
`#coffeechain`. The source masks include both `#coffeechain` and `coffeechain`,
but TPv38 returned `coffeechain`; NSPv2 saw only that title. Record this as a
title issue, not solely a mask issue. The intended title is `#coffeechain`.
The authorized two-call diagnostic changed only that title in both directions,
keeping NSPv2 / Astra low unchanged. Both outputs were valid, with no reuse,
retries or baseline calls: coffee shop contains #coffeechain = Yes; reverse = No.
Both explanations still treated the hashtag as coffee-shop business chains.
Agent review rejects both unsupported justifications, without inventing gold
binary answers for the pre-recorded unresolved boundaries. This single draw
does not establish repeatability, but the marker alone did not fix this result.

The diagnostic and receipts are in `experiments/nspv2-hr02-hashtag-v1/`; the
reusable [spec](../experiment_specs/nspv2-hr02-hashtag-astra-low.json) retains
NSPv2. Original node IDs and an explicit title override bind the new inputs
without rewriting the original titles, prompts or relationship outputs.
The runner correctly reports `input_mismatch` against the saved additional-pair
batch because adding # changes the input; the old answers were inspected as an
input-change comparison, not presented as identical-input trials. No hierarchy
was rebuilt.

**NSPv3 — approved and tested, not production-frozen:** the user requested that the subsumption prompt
identify social media posts as the source, so hashtag syntax has that context.
[NSPv3](../node-subsumption-prompt-v3/prompt.txt) adds only "derived from social
media posts" to NSPv2's first sentence. The shared revision tool preserves the
baseline hash and exact delta. The remaining instructions and output contract
are unchanged; no extra uncertainty instruction is added.

The approved `experiments/nspv3-hr02-hashtag-v1/` comparison was prepared with
`--from experiments/nspv2-hr02-hashtag-v1`, changing only to the NSPv3 prompt.
It completed two new Astra-low subscription calls, both valid, with no retries,
reuse or baseline reruns. Coffee shop contains #coffeechain changed from Yes to
Uncertain: the reason recognizes that the hashtag alone does not establish that
its posts all fall under coffee shop. Agent review accepts that calibrated
uncertainty, not a binary graph decision. The reverse remained No because
"Coffee shops include independent businesses, not just coffee chains"; that
unsupported interpretation is still rejected. The source context helped in one
direction in this draw, but did not resolve the name or establish repeatability.
Original node IDs, both exact inputs, saved baseline receipts and separate
agent reviews remain available. No user result verdicts were invented. Existing
specs, original titles, previous outputs and the hierarchy remain unchanged.

The subsequently authorized `experiments/nspv3-hr02-diverse-pairs-v1/` batch
tested three other original HR02 pairs in both directions with unchanged
NSPv3 / Astra low. All six new subscription calls were valid, with no retries,
reuse or baseline reruns. Results matched the pre-run agent expectations:
brisket / Brisket on a smoker = Yes/No; Meat consumption / Attitudes toward
meat consumption = Yes/No; Good morning greetings / Early morning = No/No.
Agent review accepted all six explanations. The saved native TRUE answers
matched five expectations, missing Meat consumption containing Attitudes
toward meat consumption. TRUE was review-only evidence, not a rerun or a
fabricated experiment baseline. The reusable
[spec](../experiment_specs/nspv3-hr02-diverse-pairs-astra-low.json) and retained
original node IDs make the inputs reproducible and the exact answers reusable.
This is a selected six-direction check, not a general accuracy estimate or
a test of how the decisions combine into a graph. No hierarchy was built.

**NSPv3 / Luna max — eight-direction comparison, tested, not adopted:** the
user approved testing the eight existing NSPv3 cases and assessing semantics
and usage. The shared runner prepared
`experiments/nspv3-hr02-diverse-pairs-luna-max-v1/` and
`experiments/nspv3-hr02-hashtag-luna-max-v1/` from their corresponding Astra
experiments with `--model gpt-6-luna --reasoning-effort max`. Exact prompts,
title inputs, original IDs and output schema were verified unchanged. The
eight new subscription calls all validated, with no retries, reuse or Astra
reruns. No paid-provider fallback, prompt change or graph construction occurred.

Luna matched five of six clear pre-recorded expectations. It rejected Meat
consumption containing Attitudes toward meat consumption, restricting the
parent to the behavior itself instead of the subject topic. Its correct
reverse No explanation calls attitudes narrower, implying the forward link
that the other call rejected. Agent review flags the forward miss and records
the reasoning conflict; Astra agreement is not the quality criterion.
For coffee shop / #coffeechain, Luna answered Uncertain/No. The first answer
still starts from a coffee-chain interpretation and is marked uncertain in
agent review; the reverse explanation remains unsupported and is rejected.
The intended hashtag boundary is not converted into a gold binary label.

Runner-reported usage is retained per batch below. Output includes reasoning;
the reasoning column is a subset, not additional tokens.

| Batch | Model / effort | Input | Output | Reasoning within output | Catalog estimate, USD |
| --- | --- | ---: | ---: | ---: | ---: |
| Six clear directions | Astra low, saved | 562 | 331 | 144 | 0.02217 |
| Six clear directions | Luna max | 562 | 1,177 | 988 | 0.0006447 |
| Two hashtag directions | Astra low, saved | 184 | 147 | 76 | 0.00919 |
| Two hashtag directions | Luna max | 184 | 961 | 889 | 0.0004989 |

The batch estimates are approximately 34x and 18x lower for Luna, respectively.
More reasoning tokens mean the 100x per-token price difference did not become
a 100x per-call reduction. These subscription runs incurred no measured API
bill, and catalog estimates do not establish subscription quota consumption.
This small selected comparison does not establish model-wide accuracy,
repeatability or graph quality. The 16,512-direction run remains unapproved.

**NSP-Luna-v1 — Luna-only, approved and tested, not adopted:** the user requested a minimal
topic-containment clarification, explicitly separate from Astra's prompt.
[NSP-Luna-v1](../node-subsumption-prompt-luna-v1/prompt.txt) is for
`gpt-6-luna` / `max` only; do not use it for Astra. NSPv3 remains unchanged.
The shared revision tool changes only the question to ask whether the entire
topic named by B falls within the topic named by A, as a subtopic or the same
topic. Social-media context, output format and title placeholders are unchanged.
The revision receipt preserves the NSPv3 baseline hash and exact edit.
Following the official [prompting guidance](https://developers.openai.com/api/docs/guides/prompt-engineering),
the prompt states the intended relation directly, with no additional examples
or reasoning procedure. The user approved the full delta and its eight-case test.

The shared runner prepared `experiments/nsp-luna-v1-hr02-diverse-pairs-v1/`
and `experiments/nsp-luna-v1-hr02-hashtag-v1/` from their saved Luna/NSPv3
baselines. Only the approved question changed; title inputs, original IDs,
model/effort and output contract stayed fixed. All eight new subscription
calls validated, with no retries, reuse, baseline reruns or Astra calls.

Five of six clear expectations still matched. Meat consumption containing
Attitudes toward meat consumption remained No, again justified by restricting
the parent to the practice itself. Its reverse No explanation still called
meat consumption broader, contradicting the forward reasoning. Coffee shop containing
#coffeechain changed from Uncertain to an unsupported Yes: "A coffee chain is
a type of coffee shop." The reverse remained No with a business-chain
interpretation. Both hashtag explanations are rejected in agent review; the
intended binary boundary remains unresolved, not a fabricated gold label.
The other five clear judgments are accepted. All eight agent assessments are
saved separately from user verdicts. No semantic improvement supports adopting
this revision on this draw; the sample does not establish general model quality.

Runner-reported usage, with reasoning already included in output:

| Batch | Input | Output | Reasoning within output | Catalog estimate, USD |
| --- | ---: | ---: | ---: | ---: |
| Six clear directions | 664 | 1,053 | 849 | 0.0005929 |
| Two hashtag directions | 218 | 390 | 324 | 0.0002168 |

These are subscription calls, not API bills or measured subscription-quota
ratios. The original NSPv3 prompts, saved outputs and hierarchy are unchanged;
no additional inference or graph construction is approved.

**NSPv3 / Luna max — fresh-pair check, tested:** the user approved a small
fresh sample after NSP-Luna-v1 failed to improve the earlier cases. The shared
runner used [this spec](../experiment_specs/nspv3-hr02-fresh-pairs-luna-max.json)
and `experiments/nspv3-hr02-fresh-pairs-luna-max-v1/`. Inputs are exact original
HR02 titles and IDs from `target/hierarchy-build-v1/astra-titles-v1/titles.json`.
Both directions of six pairs were selected before inference; none had appeared
in the preceding NSP experiments. Expectations are agent assessments, not user
verdicts. The prompt, model, effort and output schema match the saved NSPv3 /
Luna-max configuration, with no title overrides or masks sent to the model.

| A | B | Expected and returned: A contains B / B contains A |
| --- | --- | --- |
| Asian cuisine | Chinese cuisine | Yes / No |
| Physical movement | Workouts | Yes / No |
| Psychology and philosophy | Psychological distress | Yes / No |
| Food and drink | Enjoyment of food | Yes / No |
| Morning coffee | Early morning | No / No |
| coffee shop | Coffee beans | No / No |

All 12 outputs were valid and matched the pre-recorded expectations. Agent
review accepts the decisions, while noting that the Morning coffee / Early
morning explanation loosely calls the latter broader despite correctly
rejecting containment both ways. The coffee-shop/beans place/product
distinction is true but is not by itself a general test of topic containment.
Food and drink containing Enjoyment of food shows the earlier meat-consumption
error does not occur for every feeling-about-a-topic case; it does not erase
that failure. This selected sample is not a random accuracy estimate,
repeatability test or validation of graph consistency.

The 12 new subscription calls used 1,100 input tokens and 2,185 output tokens,
including 1,816 reasoning tokens. The runner's catalog estimate is $0.0012025,
not a paid invoice or subscription-quota measurement. No retries, reuse,
baseline reruns, Astra calls, prompt changes or graph construction occurred.
All 12 reviews and original receipts are retained for later diagnostic reuse.
Further inference and hierarchy construction remain unapproved.

**NSP-Luna-v3 — Luna-only, approved and tested, not frozen:** the user requested a task-specific
rewrite after finding the [NSP-Luna-v2](../node-subsumption-prompt-luna-v2/prompt.txt)
draft too dependent on title-generation wording. NSP-Luna-v2 remains preserved
as a superseded, untested prompt version, not an inference baseline.
[NSP-Luna-v3](../node-subsumption-prompt-luna-v3/prompt.txt) is for
`gpt-6-luna` / `max` only; do not use it for Astra. The base and full review
delta are NSPv3. The shared revision receipt records the exact edit and hashes.
The task now asks: "Would every post about B also be about A?" This concerns
the topics' possible coverage, not merely current attached posts. It instructs
`uncertain` when title meanings do not establish the answer. The output
contract and title placeholders remain unchanged; no title-generation rules,
examples or reasoning steps are added.
The [official reasoning-model guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively)
informed the single direct question, not a claim that the wording is effective.

The user approved testing the draft. The shared runner prepared three
comparisons from the corresponding saved NSPv3/Luna-max experiments:
`experiments/nsp-luna-v3-hr02-diverse-pairs-v1/` (six directions),
`experiments/nsp-luna-v3-hr02-hashtag-v1/` (two), and
`experiments/nsp-luna-v3-hr02-fresh-pairs-v1/` (12). Despite the retained batch
name, the last 12 are reused evaluation cases in this comparison, not fresh
holdout data. Exact title inputs, original IDs, model/settings and output
schema were verified unchanged; only the approved prompt delta was sent.
All 20 new subscription calls validated, with no retries, reuse, Astra calls
or baseline reruns.

All 18 clear expectations matched, versus 17 for saved NSPv3. Meat consumption
containing Attitudes toward meat consumption changed from No to Yes, correctly
calling attitudes a subtopic; the reverse remained No with a consistent
explanation. The remaining 17 clear decisions stayed correct. The two hashtag
directions remained Uncertain/No. The forward uncertainty still refers to a
coffee chain without establishing the hashtag's meaning; agent review leaves
it uncertain. The reverse still assumes a coffee-business chain and its
explanation is rejected. Neither direction is converted to a gold binary label.
All 20 agent reviews are recorded separately from user verdicts. This draw
shows a useful improvement, not repeatability or general hierarchy accuracy.

Runner-reported usage, with reasoning already included in output:

| Batch | Input | Output | Reasoning within output | Catalog estimate, USD |
| --- | ---: | ---: | ---: | ---: |
| Six earlier clear directions | 658 | 1,349 | 1,157 | 0.0007403 |
| Two hashtag directions | 216 | 528 | 462 | 0.0002856 |
| Twelve reused evaluation directions | 1,292 | 2,861 | 2,493 | 0.0015597 |

These catalog estimates are not paid invoices or subscription-quota ratios.
At that checkpoint the proposed harder-pair expectations remained under
discussion, particularly where titles admit different scopes. No harder-pair
inference or connected hierarchy construction had been approved. TPv38, NSPv3, earlier
variants, baseline experiments and model routing remain unchanged.

**NSP-Jev-v1 — approved and tested, not frozen:** the user requested
`typesafe/jev-1.13` through OpenRouter. The shared runner now supports its
separate `/api/v1/systemone` transport through the service-owned local
credential route. No upstream key was read and no alternate credential path was used. The
[versioned prompt](../node-subsumption-prompt-jev-v1/prompt.txt) preserves
NSP-Luna-v3's containment question and uncertainty condition. It puts A/B in
state and offers native Yes/No/Uncertain Choice options instead of requesting
generated JSON and reasons. Jev returns probabilities, not explanations.
This is an adapted-format comparison, not byte-identical prompting across models.

The three completed experiments are
`experiments/nsp-jev-v1-hr02-diverse-pairs-v2/` (6),
`experiments/nsp-jev-v1-hr02-hashtag-v2/` (2), and
`experiments/nsp-jev-v1-hr02-fresh-pairs-v2/` (12). Exact title inputs and IDs
match the saved NSP-Luna-v3 baselines. Earlier `-v1` preparations made no calls;
the transport changed before inference, so new immutable preparations were
made. The first live case used a one-attempt allowance, then the same run
resumed without repeating it. All 20 calls were valid with no retries or reuse.
No Luna or Astra calls were made.

Jev matched 17/18 clear expectations, versus saved Luna's 18/18. The sole
mismatch was Psychology and philosophy containing Psychological distress:
Jev returned No (0.67), Yes (0.17), Uncertain (0.16). That is a failure against
the saved broad-topic expectation; without an explanation we cannot establish
whether Jev interpreted the compound title differently. Meat consumption
containing Attitudes toward meat consumption was Yes, but probabilities were
0.54 Yes / 0.39 No / 0.07 Uncertain. These are reported model values, not
measured calibration. No cutoff was fitted.

The two hashtag directions returned No: coffee shop containing #coffeechain
had 0.48 No / 0.34 Yes / 0.18 Uncertain; the reverse had 0.96 No / 0.01 Yes /
0.03 Uncertain. Both remain unresolved and excluded from the clear-expectation
score, not silently counted as correct. All 20 agent assessments are recorded
through the shared review command, separately from user decisions.

Provider-reported costs, as totaled by the experiment runner, were $0.000095676
for six earlier directions, $0.000031752 for two hashtag directions, and
$0.000190596 for twelve reused evaluation directions. Every attempt has a
native charge. This single draw does not establish repeatability, general accuracy or a
production replacement for TRUE. The subsequent harder-pair test below keeps
NSP-Jev-v1 unchanged; no full hierarchy run is authorized.

Implementation verification: all 144 experiment/extraction Python tests passed.
The JavaScript suite passed 71/72 tests, including all seven System One tests;
the remaining proxy test calls the retired `extraction_pipeline.py prompt`
batch CLI and fails before any provider request. That unrelated test was not
changed. The 20 live cases also validated through the production runner.

**NSP-Jev-v1 harder sample — completed:** after the user approved a small
harder test, `experiments/nsp-jev-v1-hr02-harder-pairs-v1/` checked 13 new
directions using [this spec](../experiment_specs/nsp-jev-v1-hr02-harder-pairs.json).
The nine pre-run agent expectations cover Foods/Foods (one identical-input
control), Raw food/Veganism, Seeds and seed-derived products/Coffee beans,
Food and drink/Fasting, and Workouts/Personal habit changes (both directions
for each non-control pair). Exact titles and node IDs were verified against
the original HR02 title snapshot. The other four directions concern
Christmas/Festive gatherings and Food and cooking/Food and dining; they were
marked unresolved before inference, not relabeled after seeing outputs.
No masks, expected answers, or review comments were sent to Jev.

Jev matched 8/9 pre-run expectations (7/8 excluding the identical-title control).
The mismatch was Food and drink containing Fasting: No 0.88 / Yes 0.08 /
Uncertain 0.04, against the intended topic interpretation that abstention from
food/drink is itself a food/drink topic. Jev provides no explanation, so its
reason for rejecting that interpretation is unknown. This is an agent-labeled
expectation, not a new user decision about the hierarchy's scope.

All four unscored outputs remain visible:

| A (proposed parent) | B | Jev choice | Yes / No / Uncertain |
| --- | --- | --- | --- |
| Christmas | Festive gatherings | No | 0 / 0.99 / 0.01 |
| Festive gatherings | Christmas | Yes | 0.66 / 0.28 / 0.05 |
| Food and cooking | Food and dining | No | 0.20 / 0.66 / 0.14 |
| Food and dining | Food and cooking | No | 0.36 / 0.49 / 0.15 |

Probabilities are preserved as reported; one distribution sums to 0.99 through
provider rounding. They are not calibrated accuracy measurements. Christmas
as an entire holiday versus celebrations remains an interpretation issue;
neither food-topic title has an agreed boundary here. None of these four
decisions is counted as correct or incorrect. All 13 agent assessments are
stored separately through the shared review command; no user verdicts were
invented. No prompt edits, cutoff fitting or hierarchy construction followed.

All 13 calls validated, with no retries, reuse or baseline/Astra/Luna calls.
Runner totals: 4,908 input tokens, 520 output tokens, provider-reported charge
$0.000206136; every receipt includes billing. The suggested next step is comparing unchanged NSP-Luna-v3
on these same inputs before changing either prompt; that inference is not
authorized by this completed Jev test. The user then explicitly accepted No
for Food and drink containing Fasting. The user review and superseding agent
assessment are recorded separately; the original pre-run expectation remains
as history. Under that corrected boundary all nine scored decisions are
accepted, with the other four judgments still unresolved.

**Jev connected-section diagnostic — completed, awaiting user inspection:** the user chose to inspect
a small connected section in the existing hierarchy UI rather than run the
suggested Luna comparison. `decision_hierarchy.py prepare` takes an explicit
list of original node IDs, retains their exact titles and masks, and generates
every directed pair for the shared experiment runner. `package` revalidates
experiment receipts and exact titles before reusing the existing graph
analysis, note memberships and individual-mask renderer. It accepts only
native Yes choices as edges, preserving No/Uncertain decisions and all
probabilities; it does not fabricate TRUE scores. Cycles and rejected-but-
reachable pairs remain diagnostic data. A cycle blocks DAG browser export
instead of invoking an unapproved repair or merge. There is no new title
generation or membership expansion. On a DAG, transitive reduction preserves
reachability. The default browser package retains every selected node.

The fixed selection was Food and drink (`S83f8d64ef6`), Food and cooking
(`S8d84647626`), Cooking (`Se064318ca3`), Asian cuisine (`S314f23bffc`),
Chinese cuisine (`Se0ed29476c`), Italian foods (`S6c57981668`), Bread
(`Se2208ea404`), sourdough bread (`S5be72f875b`), and Cranberry and rosemary
bread (`S14ab091413`). All 72 decisions validated: 70 new calls, two reused,
no retries. Runner usage was 26,512 input and 2,800 output tokens; all new
receipts report charges, totaling $0.001113504 (ledger rounded up to one cent).

The graph has 20 Yes edges, 11 after transitive reduction, one root, no cycles
and no Uncertain answers. One direct No is contradicted by an accepted chain:
Food and drink → Cooking is No, but Food and drink → Food and cooking → Cooking
is accepted. This remains recorded, without repair. The browser preserves all
nine nodes and original masks across 49 posts; equal-note collapse is off.
Its `--check` passed. Adapter verification passed 145 workflow tests and 43
graph/browser/merge tests. No full HR02 run or additional inference followed.
Next: inspect the placements in the existing UI:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
target/infomap-review-build/debug/sse-subject-navigation \
  --categories target/hierarchy-build-v1/jev-section-browser-v1/categories.json \
  sse_multivector/hierarchy-refresh-v1/masked-posts.json
```

**NSP-Jev-v3 — wording approved, not tested or adopted:** the user requested fixing
the relationship prompt after examining whether the v2 draft stood on its own.
The [approved wording](../node-subsumption-prompt-jev-v3/prompt.txt) is based directly
on tested NSP-Jev-v1. It asks whether B falls entirely within A's subject matter:
discussing B must necessarily discuss A, not merely something associated with
A. Equivalent subjects count as Yes; partial overlap is insufficient. V2's
subject-index analogy and classification language are omitted; v2 remains a
superseded, untested prompt version, not a baseline. State inputs, choices and
output format are unchanged, with no examples or additional input data.
V1's question can already express subject containment; there is no evidence
that Jev required explicit mentions or confused source-post contents with
subject scope. The contradictory chain establishes inconsistent decisions,
not a proven prompting cause. V1, saved outputs and graphs remain unchanged.
The user approved this wording. No new inference has been performed or
authorized. The suggested next test compares the same nine-node section against
its saved v1 baseline without rerunning that baseline.

The second batch is in `experiments/nspv2-hr02-additional-pairs-v1/`, with a
reusable [spec](../experiment_specs/nspv2-hr02-additional-pairs-astra-low.json).
Both batches retain original pre-merge node IDs, exact title inputs, expectations,
receipts and separate agent assessments. Matching requests can be reused by the
shared runner; rejected judgments are not validated graph links, and no frontier
result adapter has been added to the hierarchy builder. No baseline calls,
prompt changes, TRUE calls or hierarchy construction were performed. The small,
diverse-case test follows the official [evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices#example-qa-over-docs).

Outside the selected Jev diagnostic above, no hierarchy was rebuilt. A full comparison would start with the same 129
original titled nodes, not the 116 nodes produced by TRUE's merges, and retain
subjects, masks, vectors, groups, titles and existing construction rules.
Further inference and graph construction require approval. Uncertainty is not
a No; its handling remains open before graph construction. A useful diagnostic
would not establish ground truth, a scalable placement method, or completion
of later production-validation gates. Existing TRUE artifacts and provisional
HD01–HD06 rules are unchanged. NSPv2 uses the direct, example-free starting point
recommended in the official [reasoning-model prompting guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively).

**September 25 full-run checkpoint:** the user authorized building the full
second 100-post hierarchy with the existing provisional rules, without
membership expansion or a Beef-specific repair. `hierarchy_true_scoring.py`
wraps the unchanged local TRUE scorer: `prepare` freezes titles, inputs,
verified cache receipts, implementation hashes and policy versions; `infer`
executes only missing inputs; `collect` requires complete, verified answers
before reconstructing all pairs; `verify` checks frozen files without inference.
The user subsequently approved switching to the reviewed Astra titles while
retaining every node. The 129 nodes yield 16,512 directed pairs and 14,525
distinct inputs: 1,629 reused, 12,896 fresh, no cache disagreements. The frozen
run lives at `target/hierarchy-build-v1/astra-true-v1/`; its title inputs are in
`target/hierarchy-build-v1/astra-titles-v1/`.

Scoring completed under `oracle-hr02-astra-true-v1.service`, CPU float32, four
threads, batch size four, 60 GiB memory limit and no swap. This service collects
answers and built `target/hierarchy-build-v1/astra-merge-v1/` after successful
inference: 116 nodes, 56 reduced links, six merged nodes. The earlier Luna-title
service is stopped with 5,092 completed rows
preserved in `target/hierarchy-build-v1/full-true-v1/`, not marked complete.
`prepare --partial-cache` verifies that stopped run's frozen requests, model
and scorer, then reuses only fully written exact-input answers. It rejects
malformed/mismatched rows and freezes their hashes against later changes;
unfinished comparisons never become No. Current user reviews are retained
through merging, and browser analysis flags rejected original titles even
when their nodes merge. Reviews do not alter scoring text or filter nodes.
The user approved Astra low for the six merged titles, keeping v38 unchanged.
`experiments/hr02-merged-titles-v38-astra-low/` completed with six valid titles,
six subscription calls and no retries: `Bitcoin`, `coffee`, `nostr`,
`Positive mood`, `Food and drink`, and `Good morning greetings`. Exact combined
mask inputs and receipts validate; applying the names preserves all links and
reachability. Agent inspection found broadly reasonable names, not proof of
valid merges; the food group's `Khyber Pass` instance remains for review.
The complete package is in `target/hierarchy-build-v1/hr02-browser-v1/`.
The existing `sse-subject-navigation` viewer passed `--check` with equal-note
navigation collapse and interactive navigation/mask checks. It displays 116
hierarchy nodes plus All notes, covering 98 represented posts. Both rejected
original titles remain flagged in analysis; O retains separate masks and IDs.
No nodes, memberships or links were removed to improve the display. The older
launcher remains on its original artifacts. Open HR02 directly:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
target/infomap-review-build/debug/sse-subject-navigation \
  --categories target/hierarchy-build-v1/hr02-browser-v1/categories.json \
  sse_multivector/hierarchy-refresh-v1/masked-posts.json \
  --collapse-equal-note-steps
```

The user reviewed HR02 and found it promising, but TRUE's relationship
judgments were not good enough to validate the hierarchy. The two NSPv2 batches
above did not rebuild it; the full frontier diagnostic remains pending.
Opening a leaf with `l`, Right or Enter now shows its notes immediately,
including when equal-note collapse leaves no displayed children. Escape or
Backspace returns directly to the parent selection. N/D/O remain available
to switch the automatically opened leaf's note view; O still shows individual
masks and IDs. Opening a non-leaf still shows its children. A root with no
displayed children also opens notes with `l`; returning keeps that root.
This is navigation only, not a hierarchy or membership change.
HD02/03 remain provisional; no graph repair or new merge approval is implied.
The earlier launch failed before inference because systemd expanded a shell
array; the restart disables that expansion and repeats no successful inference.
The updated wrapper and six related regression suites passed 63 tests. This verifies
mechanics, not semantic quality or completion of hierarchy review or HD06.

The earlier authorized four-case naming run completed with four valid
v38/Luna-max responses, four subscription calls and no retries: `coffee`,
`Beef and beef products`, `Food items`, and `Good morning greetings`.
Receipts remain in `experiments/hierarchy-merged-names-nev2-v1/`; the resulting
19-node, 75-post sample is in `target/hierarchy-build-v1/nev2-browser/`.
All 12 reduced links and complete reachability remain unchanged by naming.
The actual browser passed `--check`; interactive inspection covered navigation,
direct notes and the outside-children view with separate masks and original IDs.
The agent found the titles reasonable for the combined masks, not proof of
equivalence: the known Beef / Beef products merge and Coffee shop → coffeechain
link remain. Node IDs are hidden from browsing lists and headings to avoid title
truncation; full IDs remain available in `?` analysis. Stored IDs and displayed
mask IDs are unchanged. That four-case naming run performed no full hierarchy
inference or graph repair and established no new user semantic approvals.

### Reviewing a merge before browsing the hierarchy

The combined title can sound sensible even when distinct nodes were wrongly
merged. Use `hierarchy_merge_review.py PACKAGE OUTPUT` to derive a read-only
before/after review from a `hierarchy_build.py package` directory. It replays
the saved merge and naming evidence before export; it does not run models,
change the graph or record approvals. The output path must be new.

The main screen shows only the original group titles, their combined title,
“Should they stay separate?”, and any known user decision. Masks (`m`) and
the reason for merging (`w`) open separately in one full-width view; Escape
returns to the question. Counts, links and model inputs do not crowd the main
screen. Within masks, `i` switches to full posts with each mask marked. Within
the explanation, `c` shows resulting connections. All saved native TRUE answers
remain available, including direct No answers that conflict with accepted
paths. Connections are saved graph links, before equal-post navigation collapse.
TRUE compared original titles, not the newly generated combined title.

Optional `--decisions FILE` imports display-only prior user decisions. The
file has a `decisions` list; each entry supplies the exact original `members`,
`decision` (`keep_separate` or `merge`), and a nonempty `source` citing the user
decision. Unknown/duplicate member sets and unsupported decisions are rejected.
This labels the review; it does not alter the graph. On September 25 the user
accepted the Coffee, Food, and morning-greetings merges ("the other 3 look
fine"); Beef / Beef products remains rejected. All four sample merges are now
reviewed. These are case decisions on a selected stress sample, not an accuracy
estimate or blanket approval of HD02/HD03. No graph repairs or new inference
were performed. The decisions are saved in the package's `review-decisions.json`.

The existing `model-output-review` viewer accepts optional `labels` for
`source`, `alternate_source`, `output`, `comment`, `item` and `variant`;
omitting them preserves its normal post/model comparison labels. An optional
nonempty per-item `summary`, with one saved result, enables the decision-first
merge view. Existing comparisons without summaries retain their pane layout.
Group numbers distinguish identical titles without displaying long node IDs;
original mask IDs remain visible in the mask view.
Identical same-post masks within a group share one row retaining their aliases.

The four-merge sample can be opened with:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
target/infomap-review-build/debug/model-output-review \
  target/hierarchy-build-v1/nev2-browser/merge-review-v3.json
```

Use Left/Right for merges, Up/Down to scroll detail views and `q` to quit.
Review whether a merge removes a redundant distinction or erases a useful one;
inspect overall browsing separately.

The earlier GDC09 equal-note collapse operates on a tree. The current category
browser also implements [shared-child collapse](#shared-child-collapse) as a
navigation-only option, enabled for both sides of the HRv1 comparison.
It does not delete a shared child globally.
Unconditional single-child absorption is a separate earlier experiment, not
part of the equal-note requirement.

Use the same declared processing rules for both sides of an old/new comparison,
recording any remaining differences. **HD06, approved design with implementation
pending:** keep the first run's original reviewed view unchanged and create a
separate reprocessed view from its saved nodes and TRUE answers. Apply the new
run's merging and navigation rules to that copy; use it as the primary baseline
for the new run. Do not regenerate old subjects, masks or original node titles.
Disclose the first run's manual corrections, group exclusions and title override;
reprocessing does not remove that curation. Titles for newly merged nodes follow
HD04 separately. Membership expansion remains excluded from the new comparison.
The existing launcher does not yet provide this three-view comparison.

Existing saved hierarchies are historical evidence, not proof that these
requirements were applied. No prompt, grouping,
relationship, membership-expansion or title-repair policy changes are approved
by these requirements.

## Current title-prompt experiment

The frozen title configuration used by the **currently running TRUE job** is
[v38](../hdbv2-node-description-probe-v38/prompt.txt) with `gpt-6-luna`, reasoning
effort `max`. The user approved generating titles for all 129 HRv1 source groups
with the unchanged prompt, reusing the twenty saved matching v38 results.
`experiment_specs/title-v38-full-luna-max.json` defines the full run, saved under
`experiments/title-v38-full-luna-max/`. No title-based filtering, semantic merging,
membership changes or hierarchy construction is authorized by this title pass.
The existing v21 hierarchy and all earlier outputs remain comparison evidence.

The full pass completed with **129 valid titles, 108 new calls, 21 reused
results and no retries**. Reuse comprises the twenty prior v38 outputs plus
one identical request already answered during this run; this reuses inference,
not node identity. Every source group remains present. Receipts, parsed titles
and provenance are in the experiment's `report.json` and `run/` outputs.
All 129 are available through `experiment.py review ... --ui`.

Spot checks identified `Coffee and beans` losing the coffee-bean relationship,
`Food and food containers` losing the shared lunch topic, and `Beer` failing to
cover a mixed group containing brekkie and Khyber Pass. `Bread baking` and
`Sunday greetings` have unresolved scope questions. These observations are
recorded as agent reviews, not user decisions or an exhaustive semantic audit;
unreviewed titles are not implicitly approved. No outputs were repaired, nodes
excluded, or frozen prompt rules changed. The saved Luna titles and v21 baseline
remain untouched; the subsequent switch to Astra-title scoring is described above.

**HR02 Astra-low title pass (authorized September 25):** individual titles were
generated with unchanged v38 and identical groups, using `experiment.py prepare
--from` the full Luna experiment with only model/effort overridden. The saved
experiment is `experiments/hr02-title-v38-astra-low/`. It completed with 129 valid
titles, 128 new subscription calls, one identical-request reuse and no inference
failures or retries. Subjects, masks, SSE, HDBSCAN and the running TRUE job were
unchanged. No new TRUE comparisons or merged-title calls were started.

Agent inspection covered all 129 outputs against their quoted masks, with
source-post checks for questionable meanings. Seven current agent assessments
are saved through the runner: scope failures in `Daily painting`, `grownostr`,
`guarani` and `Brands`; uncertainties in `Fog and haze`, `Chemical substances
and operating systems`, and `Food and Paraguay`. Several concerns already
exist in the groups: growing food mixed with grownostr, chocolate mixed with
Guarani, Linux with chemicals, and Paraguay with food ingredients. They are not
evidence that title rewriting alone will solve the problem. `Coffee beans` and
`Lunch` address the earlier relationship-loss examples. These are agent
judgments, not user approvals or an accuracy estimate.

The user reviewed the four agent-rejected cases: `grownostr` and `guarani`
accepted; `Daily painting` and `Brands` rejected, with no comments. Those
decisions do not imply approval of the three agent-uncertain cases or establish
a general title policy. The user then approved proceeding to TRUE with all
Astra titles, retaining every node and visibly flagging the two failures.
No prompt edits or per-node repairs are included. The user subsequently approved
v38/Astra low for merged titles too; the full hierarchy still requires review.

[Title prompt v25](../hdbv2-node-description-probe-v25/prompt.txt) is tested but
not promoted. The approved bounded comparison replaces v24's instruction against
definition-style expansion with ASv6.48's name-handling instruction, including
retaining the name of an unresolved named subject. All other title instructions
and the masks-only input contract remain unchanged.

[Title prompt v26](../hdbv2-node-description-probe-v26/prompt.txt) is a separate,
tested but unpromoted diagnostic candidate. It preserves v25's semantic rules
and replaces only the output instruction: brief numbered instance meanings
precede a final `Title:` line in the same response. It does not add a second
model stage or change the production title-output contract. V25 remains intact;
v26's local comparison records are in
`hdbv2-node-description-probe-v26/comparison-v1/`, with a MiMo V2.6 Pro
within-model reference in `hdbv2-node-description-probe-v26/comparison-mimo-v1/`
whose prompts are byte-identical to the Astra run's.

[Title prompt v29](../hdbv2-node-description-probe-v29/prompt.txt) is a tested
but unpromoted rewrite: name the most specific category to which every instance
belongs, rather than a subject shared by the instances. It consolidates the
semantic instructions around category membership, retaining name
interpretation, supported restrictions and explicit defining relationships. It
changes only [v28](../hdbv2-node-description-probe-v28/prompt.txt)'s output
instruction: return a JSON object with one string field, `title`, without
per-instance explanations. The masks-only input and category-membership
instructions remain unchanged. This is a prompt-only change, not a runner or
schema-enforcement change. Its comparison records are under
`hdbv2-node-description-probe-v29/`, including low- and high-effort MiMo
runs and a high-effort variety expansion to ten groups.

The v25-v37 comparison sequence used Xiaomi MiMo V2.6 Pro
(`xiaomi/mimo-v2.6-pro`) through OpenRouter instead of Astra, per the user's
decision. The saved v21 and v25-v26 outputs were produced by Astra, so
cross-model differences mix prompt and model changes. Earlier versions are
preserved; no promotion or production change is implied.

[Title prompt v30](../hdbv2-node-description-probe-v30/prompt.txt) is an untested
draft built on v29, informed by the v26/v29 MiMo references: retain unresolved
names without literal component readings or defining glosses, name the category
rather than the mentions, and return the JSON object without Markdown fences.
It changes no other instruction and is not tested or promoted.

[Title prompt v31](../hdbv2-node-description-probe-v31/prompt.txt) is a tested
but unpromoted draft: v29 plus two changes only — name the category itself
rather than the texts or mentions, and return the JSON object without Markdown
fences or commentary. Its ten-group paired comparison records are under
`hdbv2-node-description-probe-v31/`. V30's broader three-change draft is
preserved, untested.

[Title prompt v32](../hdbv2-node-description-probe-v32/prompt.txt) is a tested
but unpromoted draft: v31 plus the two-case title rule — when every instance
expresses the same named thing, use that name exactly as written and without a
gloss; otherwise name the smallest genuine category containing every instance's
referent. It replaces the opening's "most specific category" framing. Its
paired comparison records are under `hdbv2-node-description-probe-v32/`.

[Title prompt v34](../hdbv2-node-description-probe-v34/prompt.txt) is a partially
tested, unpromoted draft based on v32. It folds the existing distinction between
naming the node and describing the instances as text into the main task
statement, removing the duplicate sentence. It also requires each instance to
support the title's full meaning on its own. It replaces
[v33](../hdbv2-node-description-probe-v33/prompt.txt)'s application-specific
opening without adding browsing context. Name handling, masks-only inputs and
JSON output remain unchanged. Its comparison uses the same 20 v32 robustness
groups and MiMo high-effort settings, importing saved v32 results without new
baseline calls. Records and agent assessments are under
`experiments/title-v34-vs-v32/`, managed through `experiment.py`.

The approved provider-only resume reached all 14 previously unstarted cases
and successfully retried beef once. It preserved the four completed outputs
and did not retry the local vegetable timeout. The combined run now contains
16 valid JSON titles and four unresolved cases, with none unstarted. Vegetables,
garlic and kitchen/worktop have local timeouts; fog/haze returned an empty
answer after 131,072 reported completion tokens. Its recorded stop reason is
`stop`, not an explicit token-limit error. These failures were not retried.

All completed titles have agent assessments in the existing review UI. The user
accepted `satoshi` and `chocolate` and rejected `Words relating to preservation`.
New clear concerns are `Statements about coffee` replacing `coffee`, `tallow`
excluding the `Tbone` instance, and `Cooked meals prepared to eat` losing the
shared potato detail. The last is a loss of specificity, not a membership
contradiction. `Tips for personal well-being` remains uncertain. For
`Book-related topics`, the user suggested `Literature`, motivating v37's
organizing-topic framing below rather than requiring a shared type. This does
not establish `Literature` as the uniquely correct title.

This single-draw comparison does not establish an overall improvement over v32;
the observed regressions argue against promotion. Transport failures are not
counted as incorrect titles. V34 and production titles remain unchanged.

[Title prompt v37](../hdbv2-node-description-probe-v37/prompt.txt) has
user-approved wording and is tested, not promoted. Based on v34, it asks for
the most specific topic containing every instance rather than independent
support for the title's full meaning. It removes only "in a topic hierarchy"
from [v36](../hdbv2-node-description-probe-v36/prompt.txt) and does not include
[v35](../hdbv2-node-description-probe-v35/prompt.txt)'s extra interpretive
permissions. V35 and v36 remain untested. Name handling, masks-only inputs and
JSON output are unchanged; there are no added examples.

`experiments/title-v37-vs-v34/` uses the same 20 cases and MiMo V2.6 Pro high
settings, with saved v34 answers and no baseline inference. All cases were
attempted: 19 valid JSON titles and one unresolved kitchen/worktop case across
24 attempts. Four explicit provider 502 errors each received one retry; three
recovered, while kitchen/worktop's retry ended with a socket closure classified
as unknown. That failure was not retried again or counted as an incorrect title.

Agent assessments, separate from user decisions, are saved through the shared
review CLI: 14 acceptable, three rejected and two uncertain titles. Coffee and
preservation stop describing the input as text. However, the book group becomes
`Book, reading, and writing terminology`; `tallow` still excludes Tbone; and
`Home-cooked meals` adds an unsupported home restriction while still omitting
the shared potato detail. The raw-food title is wordier, and `mental health`
loses specificity relative to psychological distress without a clear membership
error. The uncertain advice group may be loosely grouped; the fog group mixes
mental fog and literal haze, with disambiguating source context absent from the
model's masks-only input. These are not clean title-prompt-only failures.

This single comparison is mixed and does not establish overall improvement.
There are only 16 usable v34 answers for paired semantic comparison. The
existing UI contains all 19 valid titles and agent comments; the unresolved
case remains visible through the CLI. Production titles remain unchanged.

The user then approved testing unchanged v37 with **GPT-6 Sol, low**, through
the subscription runner. `experiments/title-v37-sol-low-vs-mimo/` preserves the
same 20 inputs and prompt bytes and uses saved MiMo v37 outputs without baseline
inference. One case first verified live model acceptance; resuming preserved it.
All 20 cases completed in 20 attempts with no retries. This changes model,
provider and effort together; it is not a prompt-only comparison.

Agent review records 15 acceptable, one rejected and four uncertain titles.
`Meals with potatoes and vegetables` restores the shared detail and removes
the unsupported home restriction. `Beef products and processing` no longer
drops Tbone, but the beef-only scope is uncertain because tallow need not come
from beef. `Food preservation` similarly narrows generic preservation masks.
The book title now names subject matter rather than terminology, but remains
a long enumeration: `Books, their authorship, and ways of reading or listening
to them`. The advice and mixed mental/literal fog groups remain uncertain.
All 20 titles, comparisons and agent comments are saved through the experiment
CLI. The title review UI now accepts equal candidate and baseline prompt versions
(both legitimately v37 in this model comparison). Candidate means Sol low;
baseline means the saved MiMo run. No user decisions or production promotion are
inferred. Review those scope choices before another prompt revision or broader run.

The runner now recognizes exact `gpt-6-sol` metadata without substituting
GPT-5.6 Sol or changing existing routes. Its regression was observed failing
before implementation and passing afterward, including actual SDK request
serialization and offline response decoding. The Python workflow suites passed
147 tests. The Node runner suite passed 61 of 62: the remaining existing proxy
test invokes the retired saved-batch command and was left unchanged. Live
comparison succeeded through the subscription service; catalog cost estimates
are not incremental API charges, and no paid fallback was used.

The next authorized sample switched to **GPT-6 Luna, max** at the user's request,
before any new Sol calls. Unchanged v37 was tested on ten groups outside the
previous twenty, selected before inference for diversity: a publication name,
kindness, photography, exercise, sleep, bread ingredients, coffee flavor, peace,
controversy and coffee shops. The reusable spec is
`experiment_specs/title-v37-diverse-luna-max.json`; saved outputs and attributed
reviews are under `experiments/title-v37-diverse-luna-max/`. All ten completed
in ten attempts without retries, through the existing subscription route.

Agent assessment: five acceptable, one rejected, four uncertain. The clear
failure is `Granting privileges based on kindness, goodness, and generosity
rather than status`: most instances express virtues without that relationship.
Photography, exercise, sleep and controversy titles cover their masks but
unnecessarily enumerate subtopics; these are borderline concision judgments,
not four established membership failures. All ten are available in the review
UI with reasoning and no inferred user decisions. There is no paired baseline
on these new inputs, so this cannot rank Luna against Sol.

The user subsequently approved the wording and test of [title prompt
v38](../hdbv2-node-description-probe-v38/prompt.txt), based directly on v37.
It is now **frozen for the next hierarchy experiment**. It distinguishes naming
a shared topic from
summarizing the group's contents, and retaining category-defining details from
appending subtopics already covered by its name. Specificity, inclusion of every
instance, name handling, masks-only inputs and JSON output remain requirements.
It does not reinstate v34's independent-support requirement. No new examples,
word limit or production changes were added.

`experiments/title-v38-vs-v37-luna-max/` compares the same ten inputs and Luna-max
settings against saved v37 outputs, with no baseline inference. All ten completed
in ten attempts without retries. The preselected checks were the kindness scope
failure, redundant enumeration, and retention of the shared bread ingredients.
Agent assessment accepts all ten: `Kindness, goodness, and generosity` removes
the privileges restriction; `Photography`, `Workouts`, and `Sleep` replace
contents summaries; `Cranberry rosemary bread` preserves both ingredient details.
`Coffee taste and flavor` uses the group collectively to interpret the generic
flavor mask, consistent with v37/v38 rather than independent entailment.
The controversy title is less enumerative; Dezeen, peace and Coffee shop are
unchanged. No clear regression was identified in this sample.

This is a promising single-draw diagnostic comparison, not proof of reliability
or downstream hierarchy improvement. All ten outputs and agent reasoning are
in the review UI, with user decisions separate. The user accepted proceeding
with v38 unchanged to the fresh sample below.
The agreed stopping rule remains: if further comparisons merely trade errors,
stop this wording sequence instead of immediately drafting the next version.

The fresh sample uses `experiment_specs/title-v38-fresh-luna-max.json`, with
outputs and agent reviews in `experiments/title-v38-fresh-luna-max/`. Its ten
groups were selected before inference and do not overlap the preceding thirty
group IDs. They still come from the same source corpus, not an independent
corpus or a statistically representative sample. Prompt bytes and Luna-max
settings match the v38 comparison. All ten completed in ten attempts without
retries; no baseline was run.

Agent assessment: nine acceptable, one uncertain. Titles include `Morning
coffee`, `Vacuum sealing`, `Christmas`, `Asian cuisine`, `Excessive food and
beverage consumption`, `Children`, `homesteading`, `Pantry food storage`, and
`gift`. They cover varied instances without long subtopic enumerations. The
remaining title, `Movement`, covers its masks but may be unnecessarily broad:
three instances mention walking and one says motion. That is a specificity
question, not an established membership failure. All ten remain in the review
UI with reasoning. The user accepted proceeding without another wording change,
then approved freezing v38/Luna max and generating the remaining titles as
described above. This is not a blanket approval of every generated title.

HRv1's saved titles still use v21. The new full title pass does not overwrite
them, change memberships or hierarchy edges, or consolidate categories.
The saved v24 baseline and v25 comparison inputs,
receipts and assessment remain local experiment data under
`hdbv2-node-description-probe-v25/comparison-v1/`.

## Shared-child collapse

The user approved implementing this behavior independently of the title-prompt
work. `--categories --collapse-equal-note-steps` enables it in
`sse-subject-navigation`; `run-hierarchy-refresh.sh` passes that option for both
the refreshed hierarchy and `--baseline`. Other launchers retain their previous
behavior. `true_graph_categories.py` still exports every saved reduced edge;
the browser derives its displayed choices without rewriting those edges.
Existing single-child absorption is a different operation, refuses shared
categories, and cannot be combined with this option.

**Keep the raw hierarchy; simplify only the displayed child choices.** Compute
each category's complete post-ID set from its original direct memberships and
raw descendants, before deciding which navigation steps to skip. Require an
acyclic graph. Do not recompute these memberships from the simplified menus.

For each displayed parent P:

1. Walk its raw children in saved order. If child C has exactly P's complete
   post set, omit that navigation step and examine C's children in its place.
   Repeat through equal-set chains. Retain a child with a strict subset,
   including a one-post child; this adds no minimum-size filter.
2. Apply this decision separately for every parent. If another parent Q has
   more posts than C, keep C under Q. Do not remove C from the raw inventory,
   transfer its memberships to P, or rename either category.
3. If several skipped routes reach the same displayed category ID, list that
   ID once at its first occurrence. Distinct IDs remain separate, even when
   their labels or post sets match. Keep the raw edges and a per-parent record
   of skipped category IDs so all original routes remain traceable. A single
   global original-to-surviving-node mapping cannot represent shared children.
4. Keep the navigation root. Apply the same child-step rule there; do not
   replace the root or suppress unrelated top-level choices.

The note actions must remain distinct:

- **N:** unchanged original recursive posts and their category-specific masks.
- **D:** unchanged original direct assignments, including posts also in children.
  Skipping a child must not turn its posts into direct assignments to its parent.
- **O:** original recursive posts minus the union of the displayed
  children's complete post sets. O may gain posts after collapse; it describes
  the choices currently shown. Keep the current category's original individual
  masks and IDs, without importing masks belonging only to another branch.

The current category's `?` analysis lists skipped labels and IDs, its saved
children, and each skipped category's saved children. Categories skipped on
every route remain in the raw graph and its evidence. `--check` reports the
displayed children, skipped IDs and outside-child posts for each raw category.
This operation does not make categories semantically equivalent.

### Verification

The saved TRUE13 **pre-membership-expansion** baseline was reconstructed through
`build_graph(..., decision_rule='native')` and `derive_note_memberships`, matching
the saved graph and memberships exactly. Its 59 categories have 37 reduced
edges, four shared categories, and 77 represented posts. **None of those edges
has equal complete post sets**, so the collapse leaves that baseline
unchanged. `category_mask_instances.reconstruct` also recovered the original
mask IDs without changing the saved combined highlights. The existing browser's
`--check` accepted the baseline with and without collapse: all nonempty child
lists and all 77 posts remain unchanged. The saved input files are unchanged.

A structural example was checked through the production graph and membership
functions, using synthetic relation answers, not model inference:

- Raw edges: A → C, B → C, C → D.
- Direct posts: A={1}, B={3}, C={2}, D={1}.
- Complete posts: A=C={1,2}, B={1,2,3}, D={1}.
- Displayed edges with collapse: A → D, B → C, C → D.

Changing the **raw** A → C edge to A → D loses post 2 from A. Transferring C's
post 2 into A instead changes A's direct membership. Retaining the raw graph
avoids both: A's N remains {1,2}, its D action remains {1}, and O becomes {2}.
C remains available under B with its own masks and identity.

The new CLI regression first failed because the option did not exist. All 80
selected Rust browser/hierarchy tests and 37 Python refresh/TRUE tests now pass.
The ten dedicated tests in `tests/category_equal_note_collapse.rs` exercise
production loading, projection, CLI and rendered keyboard navigation: shared
routes, equal-set chains and leaves, root retention, strict-subset children,
distinct siblings with equal post sets, promoted-ID deduplication and ordering,
unchanged N/D and branch-local masks, O's displayed-child behavior, inspectable
skipped IDs, cycle rejection, and opt-in compatibility. An integration test
runs the actual refresh launcher and browser on fixtures for both views.

HR02 has now completed TRUE inference and merged naming through the construction
path above and its browser package is ready. The user reviewed it and found it
promising, but TRUE's relationship judgments were not good enough to validate
the hierarchy. A frontier-call replacement is planned as a diagnostic of the
other stages. The two eight-answer NSPv2 batches above have not rebuilt the hierarchy.
Reprocessing the older HRv1 comparison under HD06 is still pending. No title,
relation, membership or saved artifact was changed to implement this navigation
rule.

## Current evaluation decisions — September 15, 2026

**Coffee → Music at Coffee Shops is approved for evaluation.** The user explicitly
approved this category relationship, superseding the earlier No in
[TRUE06/U02](./TRUE06/user-review.json). The parent is `S9c440e7f47`; the child is
`S8ea08f1aff`, with these masks:

- N004 · V035: ⟦Rave at a coffee shop⟧
- N038 · V295: ⟦playing⟧ ⟦coffee shop⟧ ⟦music⟧

The [saved TRUE output](./TRUE10/graph/scores.json) for
`premise: This text is about Music at Coffee Shops. hypothesis: This text is about Coffee.`
is native No, with score `0.009861395630151667`. The fixed `> 0.142` rule also
rejects it. Under the updated user judgment, both rules miss this relationship.
Repeated rows for equivalent Coffee titles are the same model input, not
independent failures. No new inference was performed.

This approval concerns this pair only. The reverse direction was not adjudicated;
the earlier Food consumption → Having drunk coffee rejection remains unchanged.
That evaluation approval did not change a hierarchy edge, category title, mask,
or score. How to recover this missing relationship automatically remains open.

Separately, the user approved all six notes in the
[TRUE12 membership review](./TRUE12/membership-review.json): N004, N005, N017,
N024, N038, and N065. These are note-level membership decisions, not approvals of
every individual mask or of other category relationships. The saved review
session had state SHA-256
`2aabc553e6cd68d9fb63f610fd79e63a76bffb4a08ca48e1eab5c77fe6583667`.

The [TRUE06 report](./TRUE06/RESULTS.md) and
[TRUE12 report](./TRUE12/RESULTS.md) remain frozen experiment evidence. Their
original judgments and pending-review language predate these decisions; they
are not the current evaluation verdicts for the items above.

## Complete category inventory — TRUE13

A failed title is not a rejected group. TRUE10 incorrectly excluded
`Sf5a4b23523` because its generated title, “Coffee shop chains,” was rejected.
The underlying seven-mask group had not been rejected. TRUE13 restores it as
`#coffeechain`, the user's category name, with explicit title-override provenance.
Its masks and original generated-title record are preserved.

The inventory is now checked against the original source packets:

- HDBv2 selected 64 groups. Three earlier user grouping rejections remain unchanged.
- All 61 remaining groups must be represented, regardless of title-review status.
- Two previously reviewed equivalent pairs are consolidated without losing masks.
- This leaves 59 categories, with no title-based exclusions.

[TRUE13](./TRUE13/categories.json) shows every category, including disconnected
ones under the root. It preserves the 3,306 existing relationship scores and
checks only the 116 directions involving the restored category. Native TRUE
answers determine links; no Coffee link is inserted manually. Cycles would stop
publication, not trigger silent deletion or consolidation.

The 116 new checks produced one accepted relationship: Coffee → `#coffeechain`
(native Yes; score 0.7825745). The other 115 were native No. The graph has no
cycles. All 48 original accepted relationships remain unchanged.

The full view also preserves the saved TRUE12 Coffee/Tea membership additions.
It contains 79 distinct notes; notes and highlights remain visible recursively.
The other 21 original notes have neither retained HDBSCAN membership nor an
accepted Coffee/Tea membership in these results. This is not a new exclusion.
The known missing Coffee → Music at Coffee Shops link remains uncorrected;
the Music category itself is present, not hidden.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./sse_multivector/run-true13-hierarchy.sh
```

Enter descends; N shows the current category's notes and all descendants.
D shows only directly assigned notes, including direct notes also present in
children. O shows notes that appear in none of the current category's children
or deeper descendants. N and D combine the category's masks on each full note.
O highlights one original mask at a time on the full note, showing its original
vector ID and mask count. Use [ and ] to change masks; left/right changes notes
and returns to the first mask. Identical masks list their original IDs together.
Empty results stay empty;
Escape returns to the category menu and preserves its selection.
Category IDs identify the original groups. `--check` validates the saved view
without opening the UI.

[The plan](./TRUE13/plan.json) records inventory and preservation hashes;
[the completion record](./TRUE13/completion.json) records graph and output hashes.
The current handoff checks the full source inventory before generating inputs,
accounting only for explicit consolidations. Missing titles/groups cause an
error instead of filtering. TRUE10–12 remain frozen comparison evidence.

In the TRUE13 baseline, Coffee's N shows 22 notes, D shows 18 directly assigned
notes, and O shows 13 notes absent from all descendants. O excludes a whole note when it appears
below the category, even if its masks differ. This action works for every
category in the existing UI; it does not change memberships or saved masks.

The launcher uses [categories-with-mask-ids.json](./TRUE13/categories-with-mask-ids.json),
which adds original individual masks and IDs to the unchanged saved view.
The IDs come from native matched instances and the saved TRUE12 membership
results, not from guessing how combined highlights were formed. Their combined
ranges must exactly reproduce every category's saved highlights. The original
categories.json, graph, scores and source notes remain unchanged. Coffee's O
view contains 41 distinct masks across its 13 notes (43 IDs including aliases).
Older category files without individual-mask records retain their previous
combined display with an explicit “Individual masks unavailable” notice in O.

## Completed Coffee/Tea membership checks — TRUE14

TRUE14 checks all 945 original masks from 100 notes against Coffee, Tea as a
beverage, and all four Coffee children. It reuses the 1,796 unchanged Coffee/Tea
inputs and scores and runs the 3,592 missing child inputs. Identical model inputs
share a score while retaining every original mask ID: 5,388 inputs cover all
5,670 mask/category pairs. No parent decision filters the child checks.

The masks, titles, checkpoint, input wording, strict `score > 0.142` membership
rule, and category relationships remain unchanged. All original memberships
remain; accepted child masks are added and inherited upward. The full hierarchy
still contains all 59 categories and 79 represented notes. No category or
uncertain addition was hidden, and no separate review queue was created.

| Coffee child | Notes before → after | Added individual masks |
|---|---:|---:|
| Coffee Bean Preparation | 2 → 2 | 3 |
| Having drunk coffee | 2 → 7 | 19 |
| Appreciating Coffee for Its Flavour | 2 → 2 | 2 |
| #coffeechain | 7 → 8 | 1 |

These are 25 added category/mask memberships, not 25 new notes. Coffee remains
22 notes overall; its children now contain 13 distinct notes rather than nine.
Coffee's O view therefore changes from 13 notes to nine. Its D view remains 18.
Tea remains four notes, with no existing children. The other 21 source notes
were checked but acquired no membership in these branches.

The agent inspected every addition against its masks and source note. The
grinding/roasting, explicit drinking, decaf-flavour, and returning-to-coffeechain
matches are coherent. Some consumption additions are looser: V351 says
“Fetching coffee” alongside stretching and bowing, not that coffee was drunk.
Those decisions are preserved for inspection, not manually repaired.

Two results clarify the earlier missing-child problem:

- N018/V132, “back coffeechain tomorrow,” passes #coffeechain at 0.310519 despite
  scoring only 0.080228 for Coffee. It is added to the child and inherited by
  Coffee. Checking children independently therefore recovers this mask.
- N004/V034, “Weird #coffeechain,” was finally checked but scores 0.056464 for
  #coffeechain. N029/V243, the plain hashtag, scores 0.074444. Both remain outside
  that child. These are model misses now, not missing checks. Some original
  hashtag and flavour masks also fall below the cutoff; their existing
  memberships are preserved. Complete checks do not establish complete recall.

[Analysis](./TRUE14/analysis.json), [all additions](./TRUE14/membership-changes.json),
[verification](./TRUE14/verification.json), and the
[packaging manifest](./TRUE14/packaging-manifest.json) preserve the evidence.
The unchanged inference implementation still writes `experiment: TRUE12` in its
config; TRUE14's plan, execution record, verification, and outputs identify the
new experiment explicitly. Frozen inputs and score/configuration identity were
verified before packaging. Inference ran locally with no paid resources.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./sse_multivector/run-true14-hierarchy.sh
```

The same launcher accepts `--baseline` for unchanged TRUE13 and `--check` for
validation. N/D/O behavior is unchanged, including separate original masks and
IDs in O. The next step is user inspection of this corrected hierarchy, especially
Having drunk coffee and Coffee's remaining O notes. No further inference or
semantic repairs are authorized by that recommendation.

## Earlier focused Coffee and Tea review — TRUE12

The [expanded view](./TRUE12/hierarchy/categories.json) packages the saved
TRUE12 membership additions: Coffee has 22 notes and Tea as a beverage has four.
It shows only these two branches, with all three original Coffee children and
their contents unchanged. It does not add the approved Music at Coffee Shops
edge or create subcategories for the newly included notes.

Membership is additive: every original note remains, and every saved mask score
strictly above 0.142 contributes its source note and exact highlights. The
browser overlays the union of those masks and the existing category/descendant
masks. Source notes, titles, model scores, category links and the original
TRUE11 browser are unchanged. This is a candidate to inspect, not an assertion
that its navigation is adequate.

Open the expanded view:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./sse_multivector/run-true12-hierarchy.sh
```

Use the same command with `--baseline` for the original Coffee (nine notes) and
Tea (two notes) branches. Enter descends; N displays all notes at the current
category, including descendants; D displays direct notes only; h returns to the
parent from the category menu. `--check` validates either view without opening
the terminal UI.

[The packaging manifest](./TRUE12/hierarchy/manifest.json) records the input and
output hashes. Packaging uses no inference and refuses to replace an existing
output directory. This focused view remains available for comparison; use TRUE13
above to inspect all categories without this branch filter.

## Earlier construction research

[USC01 — source meanings and pairs](./USC01-RESULTS.md).
All fifteen unchanged descriptions and all 128 nonempty USM02 word assignments
produce singleton and same-description pair hierarchies. Cooking → Cooking with
meat supplies a supported new local destination; transformation with seasoning
is another plausible distinction. These are not complete-navigation results.

The full 202-pair semantic audit also exposes artificial narrowing: Cooking plus
Act excludes two cooking notes merely because they lack a second eligible word,
although Cooking already entails Act under the fixed dictionary. Forty-two
most-specific pairs have identical or ancestor-overlapping endpoints; nineteen
lose notes relative to the narrower singleton. Existing wrong senses, lexical
ancestry gaps, and description omissions cause separate errors. The next
justified control is same-description conjunction that can reuse an occurrence,
not another sense-matching sweep. It has not run or been adopted.

All original notes, inline masks, word scores, source witnesses, two complete
audit partitions and reconstruction evidence are preserved. Seventy-six tests
pass, and all result/graph/lexicon/input files replay byte-for-byte. The browser
and original GDC09 remain unchanged; no review UI is packaged before wrap-up.

Preceding construction experiment: [SGC03 — broader concepts](./ONTOLOGY-CONSTRUCTION.md).
Adding pinned SUMO noun and verb mappings to the unchanged eleven source graphs
creates locally useful Food → food/process → preservation/preparation/cooking
paths. The shared activity parent includes brisket cooking, which WordNet-only
construction missed there. A new Food/preservation pattern joins stock and beets.
This is actual candidate construction, not merely static ancestor lookup.

It is not a dependable semantic order or a complete browsing improvement.
Generalization also introduces shipping containers from generic containers
and learning processes from coffee experience. Some occupation/attribute
derivations are formally problematic without being bad topical destinations:
a chef note can reasonably concern occupations. Existing wrong source senses remain;
correct local food results also rely on a globally imperfect animal/human Food
mapping. Class-only mapping admission is insufficient. The connection controls
show different behavior from co-occurrence, not demonstrated better membership.

All three conditions replay, all original WordNet patterns and witnesses remain
unchanged, and complete masks, native graphs, paths, controls and all candidate
patterns are preserved. The 157 final recurring representatives are not approved
categories. Repeated note sets, source omissions and menu selection remain open.
The completed [mapping and source-meaning audit](./MAPPING-VALIDATION.md)
finds no justified drop-in mapping repair. The authors' correction release
changes ontology definitions as well as noun mappings and supplies no matching
final verb table. Learned methods examined predict supplied ontology
relationships; they do not establish independent correction of these errors.
Five fixed-witness dependency checks identify affected destinations without
rebuilding or adopting a mapping blacklist.

The [source-occurrence audit](./SOURCE-OCCURRENCE-GROUNDING.md) now separates
candidate availability from contextual sense selection. Existing token offsets
are usable, but the saved parser turns beet into boot and supplies nonexistent
lemmas for tomatoes and simmering. Removing those restrictions is a different
question from repairing a generated DRS graph. The edge-control audit finds no
demonstrated semantic advantage requiring that graph; it does not prove that
relationships never matter. The beets/preparation omission also has two
independent barriers: a missing direct edge and missing lexical ancestry.

[USM01](./USM01-PLAN.md) selects a bounded direct-occurrence comparison using
one released LMMS sense representation: saved-lemma filtering, original-word
morphological lookup, and unrestricted matching. The original-word control
tests whether bypassing faulty lemmas explains any apparent improvement.
The [completed comparison](./USM01-RESULTS.md) processes all fifteen descriptions
and 134 lexical targets, including the four descriptions the DRS parser could
not process. Original-word lookup explains the main lemma-error recoveries;
unrestricted matching additionally finds a useful frying meaning for sautéing
but introduces unsupported specifics such as beef broth for chicken stock.
Dropping POS also lets bread become breading and beef become complaining.
Neither condition resolves every source meaning; preparing beets still maps to
preparing a speech. All originals, masks, scores and judgments are preserved.
The completed [USM02 control](./USM02-RESULTS.md) reuses those frozen vectors
and retains saved POS during original-word lookup. It preserves useful tomato,
beet and simmer recoveries and avoids bread/beef grammatical misreadings, but
blocks useful decaffeination, canning and homemade meanings. All 402 previous
comparisons and 1,579 scores reproduce exactly. This fixed condition supplies
USC01 above; it is not accepted as a final representation. Current source
identity checks and a corrected process-memory measurement are documented;
historical run files remain unchanged.

Preceding construction experiment: [SGC02 — connected patterns](./CONNECTED-PATTERN-CONSTRUCTION.md).
With SGC01's eleven accepted graphs and dictionary fixed, relaxing exact
relationship labels/directions produces two genuinely shared food-activity
patterns. One joins beet preservation with the three food-preparation notes;
the other joins stock preservation with bread preparation. Both note sets are
new, but neither establishes better complete navigation. Food activities still
misses brisket cooking; its Preparation child misses the preparing-beets note.
Two ordinary food senses remain split into overlapping destinations.

All 25 recurring connected representatives and their source witnesses are
audited. Generic pattern growth is not credited as semantic progress. The
generalized inventories each have 32 recurring note sets, with ten gained and
ten lost—not identical sets. Existing singletons remain unchanged. All 89
relevant tests pass; exact and relaxed construction replay, and originals,
inline masks, all witnesses and five complete inspection paths are preserved.
No browser is adopted. The comparison weakens the case for requiring precise
event roles before proceeding, but leaves lexical generalization, source errors,
category selection and complete-note coverage unresolved.

The [semantic-order investigation](./SEMANTIC-ORDER-RESOURCES.md) found a
direct construction precedent and concrete SUMO paths across the missing
noun/verb and Food distinctions. It also finds scope mismatches: the resource
is not a verified semantic order. [SGC03's pre-run design](./SGC03-PLAN.md)
separates approximate construction from mapping validity using noun-only and
noun-plus-verb conditions and same-order singleton controls. The completed
comparison and collateral-admission audit are linked above.

Preceding construction experiment: [SGC01 — contextual semantic graphs](./SEMANTIC-GRAPH-CONSTRUCTION.md).
Fifteen unchanged descriptions from thirteen notes were given to a native
text-to-DRS parser. Eleven outputs pass local sequence/reference checks; four
are malformed despite ending themselves below the allowed output length.
Generic graph generalization produces useful food-preparation and meat-cut
paths, but no improved complete browsing arrangement. The preparation group
retains the same three notes as its literal counterpart. Wrong dish, stock and
smoker senses coexist with useful local patterns; neither whole-graph rejection
nor accepting a correct final note set would be a sufficient semantic audit.

All originals, inline masks, native outputs, numbered senses, source witnesses
and construction paths are preserved. Seventy-five relevant tests pass, and
construction replays byte-for-byte. Both constructed graphs are acyclic; this
does not certify their meanings or category choices. No browser is adopted.

A static source/dictionary check finds one baking/brisket grouping recoverable
through better input, but several cross-form preparation/preservation links
remain unavailable under the fixed hypernym and exact-role rules. Do not run
a full annotation control merely to repeat that known limitation.
[NounAtlas/VerbAtlas lookup research](./PREDICATE-FRAME-RESOURCES.md) verifies
shared noun/verb activity classes. But adding them alone to the saved graphs
would not repair the missing beet participant or create a new shared
preparation/material pattern. That lookup question is now answered; a further
test needs contextual argument evidence and must exercise actual construction,
not just produce cleaner frame names. Category selection and complete-note
coverage remain open. No replacement model, frame hierarchy or browser is adopted.
The directly related release chain also leaves joint nominal/verbal inference
unverified: NounAtlas's joint release is described as forthcoming, and the
inspected MultiSRL text interface selects verbs only. No substitute model is run.
Precise event-role recovery must not become a requirement without showing its
value for the browsing construction.
The resulting controlled comparison is complete in SGC02 above. It retains
actual source edges rather than combining arbitrary words from a description.
That construction constraint has not been shown superior to co-occurrence in
this small run; the earlier coffee-shop counterexample was malformed and
remains excluded.

Preceding construction experiment: [SPC02 — phrase structure and broader meanings](./STRUCTURAL-GENERALIZATION.md).
Using all frozen SPC01 expressions, structural lexical matching recovers three
Food-preparation notes through bread preparation, steak preparation and outdoor
grilling. It also interprets washed dishes as food, and rejects valid cooking
and preservation topics whose grammatical arrangements differ. All 18 new links
into existing recurring multiword destinations and the 79 further word-only
links are audited; fewer links are not equated with better semantics.

Ambiguous dictionary paths also create a 271-expression cycle. Food → Sake
uses a drink sense; Sake → Interest switches to a purpose/interest sense. Food
then reaches all 100 notes through the graph. A relevant destination note can
hide a wrong source witness, so memberships and derivations are evaluated
separately. Neither graph is adopted. This motivated the contextual
representation experiment SGC01 above, including relationships across different
phrasing—not another word-matching or grammar tweak.
Seventy-two tests pass; final artifacts replay byte-for-byte across hash seeds.
The original inputs and browser remain unchanged.

Preceding construction experiment: [SPC01 — source phrases and category paths](./SOURCE-PHRASE-PATHS.md).
The unchanged 945 descriptions generate 2,129 expressions and 1,268 observed
head-extension links. Requiring two distinct notes leaves 234 choices, 204 roots
and 30 links; eight links return identical note sets. The complete source audit
finds useful Diet → Carnivore diet and Tea → Hot tea refinements, but also
reporting-language choices and incomplete destinations. Food preparation omits
bread and steak preparation; Food preservation omits the beet-freezing note.
Sea salt flakes does not contribute to the recurring Sea salt category because
that semantic subexpression is absent from the saved grammatical structure.

This establishes partial phrase-based construction, not a sufficient hierarchy.
No browser, parser revision, threshold or semantic repair is adopted. All source
occurrences, menus, native parses and the 30-link audit are preserved; 49 tests
pass and construction replays exactly. This motivated contextual generalization
of complete expressions into broader paths with justified memberships. SPC02
above tests one grammatical/lexical approximation and exposes its unresolved
context and binding requirements. [Method-fit research](./CONSTRUCTION-MECHANISMS.md)
records the construction precedents and qualifications; no independent cutoff
or stopword tweak is adopted.

Preceding construction diagnostic: [CPC01–CPC02 — memberships and paths](./CATEGORY-PATH-COMPATIBILITY.md).
CPC01 scores all 945 saved descriptions from 100 notes against 12 frozen
source-derived category candidates. Both fixed classifier cutoffs remove all
three clearly meaningful existing refinements. At the development cutoff,
wrong child admissions break Bread → Sourdough bread and Chicken → Chicken stock;
a missed parent admission breaks Salt → Sea salt. Malformed and duplicate
candidates remain. Better memberships alone do not establish better construction.

CPC02's fixed word-form control recovers the classifier's only two development
gains, Chicken/N080 and N100, without its incorrect additions. Across the six
judged complete categories it retains 28/31 supported assignments, adds none of
557 unsupported assignments, and preserves all three paths. The three missing
Bread notes require more than inflection matching. This is a stronger simple
reference, not a solved taxonomy: incomplete choices and duplicate children
remain. No cutoff, classifier or new browser is adopted. All evidence, source
overlays and deterministic replays are preserved; 47 tests pass.

SPC01 above tests complete source-phrase proposals and observed extensions,
using these failures as controls. Independently predicted note containment
cannot be the sole evidence for meaning; automatically propagating child errors
upward is not a demonstrated repair. No additional normalizer or threshold
sweep is justified by CPC01–CPC02.

Preceding transfer diagnostic: [TCC04 — the frozen cutoff](./CATEGORY-CUTOFF-TRANSFER.md).
On 12 different notes with all 145 saved descriptions, the TCC03 cutoff misses
10/13 supported Bread, Chicken and Salt assignments; native 0.5 misses none and
incorrectly adds one bread-baking note to Chicken. All missed assignments have
genuine supporting masks. All 90 judged within-category positive–negative
comparisons are correctly ordered. The fixed cutoff fails transfer; useful
rankings remain. No cutoff or hierarchy is adopted. All 435 scores, originals,
inline masks, judgments, hashes and an exact offline replay are preserved.

A separate retrospective check of combined TCC03+TCC04 scores finds a shared
tradeoff retaining 30/32 supported assignments with six incorrect additions,
all Morning greetings. Both misses concern the bagel note, under Bread and Salt.
This is development feasibility, not validation or an adopted rule. It motivated
the now-completed CPC01 family/path test above before adding calibration.
Category generation, meaningful relations and overall browsing remain open.

Preceding decision-method research: [literature and shared-cutoff tradeoffs](./CATEGORY-DECISION-METHODS.md).
The TCC03-only development cutoff was 0.9969531560953688; its full derivation,
alternatives and source-supervision audit are preserved unchanged as frozen
TCC04 inputs. TCC04 above supersedes that report's pending-transfer prescription,
not its measured development counts. Neither result justifies probability
calibration solely to make scores look less extreme.

Preceding note-membership diagnostic: [TCC03 — complete available evidence](./COMPLETE-NOTE-CATEGORY-EVIDENCE.md).
Scoring all 181 existing descriptions from the same 20 TCC02 notes restores
the judged Coffee note ordering and preserves Morning greetings ordering.
The cafe recovery has a genuine venue witness; it does not depend on its
hashtag-derived maximum. But maximum pooling worsens the native 0.5 decisions:
Morning greetings admits all 20 notes. No cutoff or hierarchy is adopted.
The shared-cutoff transfer test is now complete in TCC04 above; fitting only
these two labels was development, not general success.
Category generation and meaningful parent relations remain unresolved.
Full scores, all note maxima, source
judgments, originals/masks and exact offline replay are preserved. No browser
or baseline change; pending HiT files remain untouched.

Preceding discrimination diagnostic: [TCC02 — individual categories](./INDIVIDUAL-CATEGORY-DISCRIMINATION.md).
With the model and category wording fixed, 25 descriptions from 20 notes
outside TCC01 produce five Coffee witness inversions; greeting witness scores
remain separated. Frozen pre-score judgments retain ambiguous scopes. Witness
errors do not all add irrelevant notes, and unscored descriptions can recover
missed notes. TCC03 above tests that architectural distinction instead of
incorrectly extrapolating selected-witness errors to complete note retrieval.
All 50 scores and an exact replay are saved. All 72 regression tests pass;
the runner's old defaults reproduce TCC01 scores and tokens exactly.

Preceding membership diagnostic: [TCC01 — native classification](./NATIVE-CATEGORY-MEMBERSHIP.md).
All 25 predeclared supported assignments are recognized across the 14 frozen
records, but the native 0.5 rule also accepts unsupported meanings. Reversing
the same eight category choices turns chicken-with-yogurt into Bread membership;
adding other labels turns rosemary bread into Coffee. Single-category scoring
removes many interaction errors but still accepts greeting/coffee associations.
Its supported/unsupported scores remain separated in this small complete audit,
which motivated the different-record TCC02 check above. No cutoff, membership
rule or hierarchy is adopted. All 336 scores and complete originals/masks are
preserved; 71 tests pass and the complete offline replay is exact. Category generation and meaningful
parent relations remain separate unresolved requirements. No browser change.

Preceding representation diagnostic: [DSP01 — grammatical connections](./DEPENDENCY-DESCRIPTIONS.md).
On 14 frozen subject/mask records, dependency parsing retains useful local
phrases and separates coffee experience from the coffee-shop internet dispute.
But valid common subjects also have different grammatical paths; correcting
the rosemary/bread attachment does not make those paths identical. Native
parsing errors are recorded separately. Do not build an exact-tree miner as
a sufficient category rule. All parses, 1,121 paths, full originals/masks and
analytical controls are preserved, with an exact offline replay. No hierarchy
or browser changed. TCC01 above audits and tests native text-to-category
classification that can accept different grammatical witnesses. It does not
provide a category-generation solution.

Preceding representation diagnostic: [PPR01 — complete subject descriptions](./PHRASE-DESCRIPTION-NEIGHBORHOODS.md).
On the same 945 records, the base Sentence-BERT recovers the nine other known
morning-greeting notes within ten neighbors and the rosemary/bread note at position
two under Euclidean distance. Both models distinguish coffee-taste experience
from operators experiencing internet loss. Phrase-BERT improves preservation
matches but regresses elsewhere; neither supplies a membership or containment
rule. The audit separates correct notes from incorrect winning masks. All 90
inspected records and 50 full notes, both vector sets and scores are preserved;
41 tests pass and offline replays are exact. No hierarchy or browser changed.
Retain base affinity as possible proposal evidence, not a grouping rule. Next,
investigate explicit compositional relationships as evidence for shared and
broader meanings. DSP01 above tests grammatical structure without adopting it
as a construction rule.

Preceding construction diagnostic: [CAP04 — order and adjacency](./ORDERED-PHRASE-CANDIDATES.md).
The same 945 subject records yield useful repeated phrases, including ten morning
greetings omitted by CAP03. Word order removes the specific More-coffee collision;
adjacency also loses the valid rosemary/bread combination. Repeated reporting
language remains, and equivalent greeting expressions select different note sets.
Neither pattern family is a sufficient semantic representation. All patterns and
154 inspected source records are saved; 38 tests pass, with an exact replay.
No hierarchy, baseline or browser changed. PPR01 above tests complete grounded
subject expressions. Cross-gap attachment, wording equivalence and containment
remain separate questions; do not extend pair enumeration or tune frequency as
a semantic solution.

Preceding construction control: [CAP03 — existing subject descriptions](./SUBJECT-DESCRIPTION-CONSTRUCTION.md).
The mask control reproduces CAP02 exactly. Using saved per-mask subjects adds
useful Food abstractions and local preservation/harmful-food refinements, but
also produces 556 candidates and 359 links dominated by reporting/function words.
The meaningful relationship in `more complete disconnection` is lost when its
words are grouped with `more coffee`. Explicit good-morning, processed-food and
sea-salt combinations are present in the input but missed by the single-feature
seed family. This separates candidate availability from missing interpretation.
No browser is adopted. CAP04 above tests retaining shared multiword descriptions
and bounds what order/adjacency can establish. Attachment, equivalent meanings
and broader membership remain open; no new extractor has been selected.
All inputs, both outputs, source snapshots and the complete link audit are saved.

Preceding representation audit: [CSA01 — contextual attributes](./CONTEXTUAL-ATTRIBUTES.md).
Contextual word senses can add lexical abstractions such as Bread → Food, but
do not alone encode phrase relationships or every legitimate topical parent.
The two `experience` uses already differ in part of speech; separating them
would not establish deeper interpretation. Chicken meat and live chickens have
only physical entity/entity as shared hypernym ancestors. This limits a
sense-only route, not the validity of either separate or combined browsing topics.
Ten source masks and all queried dictionary entries are preserved. No WSD or
SPLADE model was run. CAP03 checks the existing descriptions before selecting
another component; word senses remain a possible component.

Preceding construction test: [CAP02 — shared candidates](./SHARED-CANDIDATE-CONSTRUCTION.md).
Keeping source features and the relation rule fixed, shared-feature closures
add five source-supported topical links, including Bread → Bread with rosemary
and Coffee → Coffee shops. The full output has 336 candidates, 43 links and 304
roots; grammatical structure, mixed word meanings and membership omissions
remain. All old candidates are unchanged. This is not an adopted browser.
Next, investigate source-grounded phrase/relationship attributes that distinguish
shared meanings from shared spelling, without discarding valid dispersed masks.
CSA01 above narrows the role of word-sense models in that investigation.
CAP03 above refines the immediate question. No parser, extraction rule or model
has been selected.

Preceding construction audit: [CAP01 — candidate coverage](./CANDIDATE-COVERAGE.md).
MDH02's complete-mask seed rule excludes `food` despite 45 matching masks from
15 notes, and also excludes recurring recipe, processed-food and chicken-stock
evidence. All 22 saved candidates reproduce exactly. The 315 excluded recurrent
features are not 315 valid subjects: grammatical words and ambiguous uses remain.
CAP02 tests bounded shared-feature proposals with source evidence and the
relation rule fixed. No original category, mask, vector, membership or browser changed.
HiT remains an unrun alternative rather than the automatic next experiment.

Latest task-trained relation evidence: [SRR01–SRR03](./SENSE-RELATIONS.md).
A WordNet definition-relation classifier preserves Bread → Sourdough but also
produces false Coffee/greeting and human-diet/Dog parents. Explicit definitions
change the errors rather than reliably removing them, adding Music → greetings
and Bread → Coffee. Retaining both names and definitions also fails. Neither a
new hierarchy nor another description rewrite is adopted. These input variants
do not isolate why the classifier failed. HiT's shared learned representation
was a subsequent lead, but it does not itself supply absent category candidates;
the construction-level reassessment above takes priority.

Earlier contextual-relation evidence: [GDR02](./EXISTING-SUBJECT-RELATIONS.md) and
[GDR03](./SUBJECT-INPUT-RENDERING.md). Existing generated subjects recover greeting
equivalence without GDR01's manual descriptions, but one seed's subject often
does not describe its whole group. A controlled input-format change fixes some
coverage misses and introduces incorrect associated-topic relations, including
Coffee → morning greetings. No automatic classifier, group description or new
hierarchy is adopted. All inputs and scores are preserved. The task-trained
follow-up is recorded above. Earlier [GDR01](./CONTEXTUAL-GROUP-RELATIONS.md) remains the manual-input
control.

Prior group-relation evidence: [lexical broader and equivalent relations](./GROUP-RELATIONS.md).
LGR01 checks all 462 ordered pairs of the 22 frozen MDH02 groups. It proposes
the existing Bread → Sourdough bread link and an animal-sense Carnivore → Dog
link that does not fit the human-diet parent group. It finds no equivalences;
GM resolves to the unit of mass, not the greeting. No new defensible parent
link or browser change results. Full evidence and an offline replay are saved.

Earlier learned-membership evidence: [entailment and relevance models](./MODEL-MEMBERSHIP.md).
NLI01/NLI02 show some useful broader-subject recognition but also abbreviation,
negation and greeting-association errors. RER01/RER02 do not fix membership:
for Coffee, the reranker puts `Good morning` above explicit coffee masks.
All inputs and scores are preserved. No classifier, membership rule or new
hierarchy is adopted by these component tests.

Latest parent-construction evidence: [mask descriptions and hierarchy relations](./MASK-DESCRIPTION-HIERARCHY.md).
MDH02 removes the old-tree dependency and finds three immediate relations, but
literal matching confuses word senses and leaves twenty roots. It is not a new
browser candidate. The record also corrects an `I` candidate caused by stripping
a sleep emoji from its source mask.

Latest membership evidence: [explicit masks and missing notes](./LITERAL-MEMBERSHIP.md).
NMR03 finds four notes outside broad Coffee and two outside Bitcoin through
literal subject evidence. It is an audited diagnostic, not an adopted assignment
rule or a new hierarchy. Source snapshots and all proposed masks are preserved.

Latest browser comparison: [mask distinctions and middle-level scoring](./MASK-DISTINCTIONS.md).
ND02-NP01 removes three repeated textual choices from NP01 while preserving all
retained evidence. It is a small inspectable improvement, not a solved hierarchy.

## NMR01 — original-vector membership

**Question:** Can fixed examples from an existing group recover omitted subject
vectors without admitting unrelated meanings?

The six groups are native GDC09 nodes 1614, 1533, 1551, 1325, 1671, and 1598.
Their masks respectively suggest exercise, sleep, cooking times, coffee-shop
music, kitchen equipment, and coffee/tea. These descriptions select diagnostic
destinations; they are not input features or certified labels. In particular,
1598 already contains a dog emoji, an ice-only mask, and a soda-bread mask.
These are preserved, not silently cleaned before the test.

**Hypothesis:** Original-coordinate support from independent notes can recover
the known exercise omission V620 and additional defensible memberships. Any
unrelated admission is counterevidence to the assignment rule's selectivity.
All proposed masks, not just newly reached notes, require semantic inspection.

For each vector, find its highest cosine to an example from each source note.
Exclude examples from its own note. Average those note scores so repeated masks
from one note do not receive repeated votes. For each existing note, take its
best mask's score against the other notes. The smallest of these scores is the
group's provisional acceptance threshold. An outside vector must clear it and
have at least two other source notes available. Examples remain frozen; new
admissions cannot recruit further members.

This threshold is a hypothesis, **not** a calibrated probability or a statistical
guarantee. Two-note groups are especially weak calibration cases: an existing
mask is scored against one other note, whereas an outside mask is scored against
two. The experiment records this asymmetry rather than claiming independent
validation. Additional held-out-note work is needed before adopting the rule.

The runner records all outside scores, per-note witnesses, every proposed
addition, and full original notes/masks for all proposals and the top twelve
outside vectors. Existing non-members are unlabeled, not presumed negatives.

The design borrows separation of discovery and later assignment from
[Dynamic Hybrid Tree Cut](https://academic.oup.com/bioinformatics/article/24/5/719/200751),
and the use of multiple examples from
[HDBSCAN soft clustering](https://hdbscan.readthedocs.io/en/latest/soft_clustering_explanation.html).
The note-balanced score and threshold above are experimental adaptations, not
those papers' published algorithms. No moved diffusion coordinates, titles, or
text embeddings generated from labels enter the calculation.

Run from the repository root with the existing NumPy environment:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib \
/tmp/crec100-plscan-venv/bin/python sse_multivector/category_membership.py \
  --data sse_multivector/real-note-fine-segmentation-v1 \
  --hierarchy sse_multivector/geometric-hierarchy-v1/GDC09/hierarchy.json \
  --groups 1614 1533 1551 1325 1671 1598 \
  --output sse_multivector/navigation-research-v1/NMR01
```

The output directory must not exist. A reproduction should choose a new output
directory. Configuration records hash the frozen inputs and source code.

## NMR02 — local agreement instead of a group-wide threshold

NMR01's exercise threshold was 0.5498 and rejected V620 at 0.3898. Its kitchen
threshold was 0.2951 and proposed 88 masks, including dinner ingredients and
the word `chef`. Group-wide average affinity and an internal threshold did not
give a reliable boundary. Coffee/tea also proposed plain sourdough-bread masks.
An audit of all proposed additions is retained separately.

**New hypothesis:** Requiring the two nearest examples from different notes to
both belong to the frozen group will retain local subject support while rejecting
the broad spillover seen in NMR01. The nearest examples are found across the
complete original corpus, excluding every vector from the query's own note.
Membership of a note does not transfer to its other masks: the actual nearest
vector must belong to the group. No new member recruits another during the pass.

This changes assignment only. The groups, masks, vectors, and six destinations
stay frozen. Two is the smallest number requiring independent source-note support;
it is not a tuned cosine cutoff. Unknown examples do not supply group support,
but are not presumed semantically negative. The procedure can still miss a valid
point whose neighbors are themselves missing from the group, or accept a weak
point whose nearest available examples are both misleading. Those outcomes must
be inspected rather than assumed away. In particular, no nearest-neighbor rule
alone establishes an absolute semantic confidence.

Run the command above with `--method local` and output directory `NMR02`.
The original mean scores remain available as diagnostics, but no longer decide
admission. This is not a reproduction of a published classifier; it tests the
specific local-support mechanism revealed by NMR01.

The rejection problem also motivated a follow-up reading of
[Tax's nearest-neighbor data description, Appendix B](https://rduin.nl/papers/thesis_01_tax.pdf).
It compares a query's distance to its nearest example with that example's own
nearest-training-example distance. This gives a local reference scale instead
of a group-wide radius. However, the saved exercise numbers already show why
the default acceptance boundary would be too restrictive here: V620 has cosine
0.4452 to V122, whereas V122 has cosine 0.5498 to its closest other-note anchor.
V620 is farther away. This does not invalidate the published method; it rejects
the assumption that adding its default local-density gate automatically solves
our omissions. No new fitted run or tuned ratio threshold was adopted.

## NP01 — bounded descendant promotion

**Question:** Can navigation skip low-value intermediates without losing access
to notes, changing retained category masks, or creating unwieldy menus?

This experiment uses the unchanged GDC09 categories, not NMR01/NMR02 membership
proposals. For each parent, it considers replacing an internal child with that
child's own children. A count-based gain trades one less step against more
choices: `child_notes * (1 + child_count) - parent_notes * (child_count - 1)`.
It performs the highest positive-gain replacement, breaking ties by saved order,
and repeats. The resulting menu is bounded to eight choices. Existing larger
menus may remain but cannot grow. Eight is a prototype setting, not an empirically
validated cognitive limit. `NP00` removes this bound as a mechanism control.

**Hypothesis:** Promotion shortens the repetitive routes while leaving useful
destinations available and keeping menus readable. Every original leaf must
remain; every retained category must have exactly its original complete notes
and mask ranges. Notes no longer covered by promoted children remain directly
accessible at the retained parent.

Preserving leaves does not prove that removed intermediate destinations were
expendable. The review must check the removed groups and newly adjacent
parent/child pairs, including Coffee, Exercise, Sleep, and Kitchen equipment.
The rule cannot validate category meaning, repair membership, or distinguish
two Coffeechain children with effectively the same meaning. Shorter paths alone
will not establish success.

This is a simple experimental cost proxy inspired by
[BioNav](https://www.cs.ucr.edu/~vagelis/publications/BioNav%20TKDE2009.pdf),
not its published optimizer. BioNav assumes an already-valid semantic hierarchy.
Overlapping memberships here also prevent interpreting raw note counts as
calibrated browsing probabilities.

```sh
python3 sse_multivector/select_note_categories.py \
  sse_multivector/geometric-hierarchy-v1/GDC09/categories.json \
  --output sse_multivector/navigation-research-v1/NP01 --run-id NP01
```

The unbounded control uses `--max-choices 0`, `--run-id NP00`, and its own output
directory. Neither run changes the original browser's default artifact.

## ND02 — repeated masked words

The follow-up [research record](./MASK-DISTINCTIONS.md) contains the rejected
common-word-intersection hypothesis, the stricter tested rule, every removal,
preservation controls, provenance, and inspection commands. It also records a
separate category-utility diagnostic that changes no category or membership.
The follow-up NMR03 tests missing explicit subject evidence elsewhere in the
corpus, not another arbitrary pruning threshold.

## NMR03 — literal subject membership

[The record](./LITERAL-MEMBERSHIP.md) separates seed-union growth from omissions
in existing broad destinations, inspects all additions, and preserves uncertain
scope and literal-matching misses. No browsing membership changed. MDH01/MDH02
now test descriptions independent of the old groups; shared wording yields a
few useful relationships but does not supply semantic parent construction.
