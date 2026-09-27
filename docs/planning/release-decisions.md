# October 18 release decisions

Updated September 26, 2026. This is the written record of the planning discussion.
Agreed requirements, tentative choices and existing-data facts are distinguished
below. The overall plan is not approved. Approval of an individual requirement
or task-view edit does not approve the whole plan. The earlier draw.io diagram
incorporates the approved scheduling changes below; other weekly targets and
exact dates remain proposals.

The user approved a read-only focused task graph backed by
[`release-plan.json`](release-plan.json). Agents maintain its task text, status
and dependencies from explicit instructions; Cytoscape and ELK render it without
manual coordinates. This document remains the source for decisions and their
rationale. The original draw.io viewer remains available for its proposed
weekly-targets page, but may lag current task status. Whether to make the graph
the default URL or retire that older view remains open.

This discussion is for planning: outcomes, dependencies, open decisions and
timing. It does not select implementation methods or experimental procedures.
Readiness is not authorization to research, implement, assign agents or spend;
each task requires explicit approval to begin.

The subject and mask prompts are finished (01 complete), confirmed by the user
on September 20. On September 24, the user confirmed that the node-title prompt
is finished (23 complete). The [frozen v38/Luna max title pass](../../sse_multivector/navigation-research-v1/README.md#current-title-prompt-experiment) has produced
valid titles for all 129 groups in the 100-note build: 108 new calls and 21
reused results. The saved HRv1 hierarchy still uses the older v21 titles.
The subsequent authorized HR02 Astra-low pass used unchanged v38 and identical
groups: 129 valid titles, 128 new calls and one reused result. Agent inspection
is complete with seven flagged cases. The user accepted `grownostr` and
`guarani`, rejected `Daily painting` and `Brands`, and approved proceeding to
TRUE with all Astra titles, retaining all nodes and flagging the two failures.
The Luna-title run is stopped with 5,092 completed answers preserved.
Task 02 resumed with the user's approval on September 25. The construction path
validated those saved v38 titles and prepared all 16,512 directed TRUE inputs.
Local Astra-title scoring completed: 12,896 fresh inputs and 1,629 reused
inputs cover all 16,512 directions. The provisional graph has 116 nodes and
56 reduced links. All six merged titles are now generated with unchanged
v38/Astra low, as subsequently approved, without changing merges or links.
The historical HRv1 runner and artifacts remain on v21. HR02 browser export
is complete. The user reviewed it and found it promising, but judged TRUE's
relationship decisions unsuitable. Task 02 stays open: a frontier-call
replacement is the next diagnostic for whether the other stages hold up, not
yet a production choice or validation of those stages. The 23 → 02 and 25 → 02
implementation prerequisites are satisfied; 25 stays complete.
The user subsequently approved the simplified
[NSPv2 diagnostic prompt and four-pair pilot](../../sse_multivector/navigation-research-v1/README.md).
Eight Astra-low subscription calls checked both directions: all outputs were
valid and matched pre-run agent expectations, versus four of the saved TRUE
answers. This selected smoke test does not establish general accuracy or a
validated hierarchy. The user then approved eight further calls on real HR02
nodes, with judgments retained for reuse in the diagnostic. All were valid;
six matched pre-run agent expectations. Both coffee shop / coffeechain answers
assumed coffeechain meant a chain of coffee businesses; their justifications
are rejected in agent review and the intended title-only boundary remains
unresolved. No answer used the available `uncertain` option. The prompt,
settings and hierarchy are unchanged; neither batch reran earlier calls.
The user identified a title issue: this node should have retained `#coffeechain`,
not `coffeechain`. Some source masks already include the hashtag marker, so this
is not solely a masking issue. The authorized two-call test changed only this
title to `#coffeechain`, with NSPv2 / Astra low unchanged. Both valid answers
remained Yes / No and still justified them as coffee-shop business chains.
Preserving the marker did not prevent that interpretation in this draw; both
justifications are rejected in agent review. No baseline was rerun, and no
prompt, saved original title or hierarchy was changed.
The user then requested explicit social-media source context in the subsumption
prompt and approved NSPv3, which adds only "derived from social media posts"
to NSPv2's opening description. The authorized two-call Astra-low comparison
used the same hashtag titles and saved NSPv2 baseline without rerunning it.
Both outputs were valid: coffee shop contains #coffeechain changed from Yes to
Uncertain, recognizing that the hashtag alone does not establish containment.
The reverse stayed No with an unsupported coffee-shop-chain justification.
Agent review accepts the uncertainty and rejects the reverse explanation.
This is partial improvement in one draw, not resolved placement or general
validation; NSPv3 is tested, not production-frozen.
The next authorized small batch used three other original HR02 node pairs:
brisket / Brisket on a smoker, Meat consumption / Attitudes toward meat
consumption, and Good morning greetings / Early morning. Six new NSPv3 /
Astra-low calls were valid and matched the expectations recorded before
inference: Yes/No, Yes/No and No/No respectively. Agent review accepted all six
explanations; saved TRUE matched five of the six expectations. No retries,
reused calls, baseline reruns or prompt changes occurred. Original node IDs
and receipts are retained for later diagnostic reuse. This selected sample
does not establish general accuracy or graph consistency.
The user approved Luna max on the eight saved NSPv3 directions, assessing
semantics and token usage before any larger run. Both model-comparison batches
completed with eight valid new subscription calls, no retries or reuse, and no
Astra reruns. Luna matched five of the six clear pre-run expectations, missing
Meat consumption containing Attitudes toward meat consumption by treating the
parent as an action instead of a subject topic. Its reverse explanation calls
attitudes narrower, conflicting with that interpretation. The hashtag answers
remain Uncertain/No with unresolved or unsupported coffee-business-chain
reasoning. Luna remains a candidate, not an adopted relationship model.
Runner-reported output tokens (including reasoning) were 1,177 versus Astra's
331 on the six clear cases, and 961 versus 147 on the two hashtag cases; input
counts were unchanged at 562 and 184 respectively. Catalog estimates were
about 34x and 18x cheaper for Luna on these batches, not 100x cheaper per call.
These are subscription runs, not paid invoices or measured quota ratios.
The user approved testing a Luna-only wording change clarifying topic containment.
[NSP-Luna-v1](../../sse_multivector/node-subsumption-prompt-luna-v1/prompt.txt)
is tested, not adopted. It is scoped to
`gpt-6-luna` / `max`; do not use it for Astra. Astra retains unchanged NSPv3.
The eight-call comparison used saved Luna/NSPv3 answers without rerunning them.
All outputs were valid, with no retries or reuse. Five of six clear expectations
still matched: the meat-consumption miss and conflicting reverse explanation
persisted. Coffee shop containing #coffeechain regressed from Uncertain to Yes,
asserting a coffee-business-chain meaning; the reverse stayed No with the same
unsupported interpretation. The intended hashtag boundary remains unresolved.
This draw provides no semantic improvement supporting adoption of NSP-Luna-v1;
it does not establish Luna's general accuracy. Prompts and hierarchy are unchanged.
The user then approved a small fresh-pair check with unchanged NSPv3 / Luna max.
Six previously untested HR02 pairs were checked in both directions, covering
cuisine, exercise, psychology, enjoyment of food, temporal overlap and related
coffee topics. All 12 decisions matched agent expectations recorded before
inference, including Food and drink containing Enjoyment of food. All calls
were valid and new, with no retries, reuse, baseline reruns or Astra calls.
One explanation loosely called Early morning broader than Morning coffee,
although both directions correctly rejected containment. The fresh sample is
encouraging, not a general accuracy estimate or resolution of earlier failures.
No prompt or model is production-adopted by this result.
The user deferred the proposed connected-hierarchy test. Discussion of harder
pairs exposed title-interpretation ambiguity; those proposed expectations are
not agreed ground truth. After reviewing the TPv38-inspired NSP-Luna-v2 draft,
the user requested a task-specific rewrite rather than transplanted title rules.
[NSP-Luna-v3](../../sse_multivector/node-subsumption-prompt-luna-v3/prompt.txt)
asks: would every post about B also be
about A? It adds an uncertainty condition when title meanings do not establish
the answer, retaining the output contract. It is approved and tested, not frozen,
and only for
`gpt-6-luna` / `max`, not Astra. NSP-Luna-v2 remains a superseded, untested
draft; TPv38, NSPv3 and saved results are unchanged.
The authorized comparison checked the 20 existing Luna cases against saved
NSPv3 answers, with no baseline reruns. All 20 new calls validated without
retries or reuse. All 18 clear expectations matched, versus 17 in the saved
NSPv3 results: Meat consumption containing Attitudes toward meat consumption
changed to Yes with a consistent reverse No explanation. The two hashtag
directions remain Uncertain/No with unresolved or unsupported business-chain
reasoning. This is a single-draw improvement on reused cases, not general
validation. No harder-pair tests or connected-hierarchy work were performed.
The user then approved testing `typesafe/jev-1.13` through OpenRouter and
adding its separate System One transport to the shared runner. 
[NSP-Jev-v1](../../sse_multivector/node-subsumption-prompt-jev-v1/prompt.txt)
preserves NSP-Luna-v3's containment question and exact title inputs, replacing
generated JSON/reasons with native Yes/No/Uncertain Choice answers. It is
tested, not frozen or adopted. Twenty new calls completed with valid receipts,
no retries, reuse or baseline calls. Jev matched 17/18 previously recorded
clear expectations, versus saved Luna's 18/18; it rejected Psychology and
philosophy containing Psychological distress. Both hashtag directions were
No but remain unscored because their expectations are unresolved. Jev does
not explain its decisions; probability values do not establish calibration
or identify its interpretation of a title. The sample is reused and small.
The original prompts, hierarchy and construction rules remain unchanged.
The user approved a small harder sample with unchanged NSP-Jev-v1. Thirteen
new judgments covered six original HR02 title pairs in both directions plus
one identical Foods-title control. Nine expectations were recorded by the
agent before inference; four directions involving Christmas/Festive gatherings
and Food and cooking/Food and dining remained explicitly unscored. Jev matched
8/9 expectations, rejecting Food and drink containing Fasting (No 0.88 versus
the intended topic-containment Yes). On unresolved pairs it placed Christmas
under Festive gatherings, rejected the reverse, and rejected both directions
between the two food-topic titles. These are not user-approved relationships.
All 13 calls were valid without retries, reuse or baseline calls; native charge
was $0.000206136. No prompt or hierarchy change followed. Comparing Luna on
this sample was suggested but not run. The user subsequently accepted Jev's
No for Food and drink containing Fasting, correcting the agent's expected
boundary. With that human correction all nine scored judgments match the
current expectations; this does not make the other agent labels user-approved.
Four scope ambiguities remain unresolved. The user approved instead a small
connected Jev section in the existing hierarchy UI: nine original food/cooking,
cuisine and bread nodes, all 72 directed pairs, unchanged NSP-Jev-v1 and no
membership expansion. Every selected node is retained; this is a selected
diagnostic, not the complete food hierarchy or a full HR02 run. Cycles are
reported without silently deleting links or merging nodes.
The approved v1 section was built: 72 valid decisions (70 new calls and two
reused), 20 Yes links reduced to 11, one root and no cycles or Uncertain answers.
One rejected relationship is nevertheless reachable: Food and drink → Cooking
was No, while Food and drink → Food and cooking → Cooking was accepted. No
repair was applied. All nine nodes and original memberships are visible in the
existing viewer, whose check passed. Native charge was $0.001113504.
The user then approved NSP-Jev-v3 and its same-section comparison. All 72 new
calls validated without retries or baseline reruns ($0.001269072 native charge).
Four choices changed from Yes to No: Food and drink → Food and cooking, and
Cooking → Chinese cuisine / sourdough bread / Cranberry and rosemary bread.
The graph now has 16 raw links, 10 reduced links, two roots, no cycles and no
rejected-but-reachable pairs. Food and drink → Cooking remains No: the original
contradiction disappeared by removing a link, not accepting that relationship.
Consistency does not establish semantic improvement. All original nodes and
memberships are retained, and the v3 viewer check passed. The user subsequently
rejected using the assembled hierarchy to validate Jev's prompt. The approved
next direction is pairwise validation first: agree on expected answers for a
small set of actual node-title pairs, keep disputed labels separate, then test
the prompt with repetitions before returning to hierarchy evaluation. The
candidate pairs in the navigation research README were checked against saved
titles, and the user confirmed all proposed labels. The repeated test completed
with unchanged NSP-Jev-v3: 17 unique inputs, three observations each, two saved
v3 answers reused and 49 new valid calls, without retries. Each trial matched
16/17 labels. Meat consumption → Attitudes toward meat consumption was the
sole failure, returning No in all three trials against the agreed Yes. All
17 inputs retained their choices across repetitions; this is selected-sample
consistency, not general accuracy. The identical Foods/Foods directions count
as one input. Disputed labels remain separate and unscored. No prompt change
or hierarchy construction followed. The user rejected further investigation
of that single miss and approved a fresh balanced sample instead. The completed
test has twelve previously untested directions, six expected Yes and six No,
across art, emotions, cooking and coffee, with unchanged NSP-Jev-v3 and one
initial call per input. Expectations are recorded by the agent before inference,
not represented as new user approvals. The Daily painting label assumes its
ordinary artistic meaning; this assumption was disclosed before inference.
All twelve new calls validated without retries, reuse or baseline reruns.
Jev matched four of six expected Yes and all six expected No. It rejected
Coffee → Coffee flavor and Positive emotions and attitudes → Enjoyment of food.
The two discrepancies are against agent expectations, not newly user-confirmed
ground truth; Daily painting remains explicitly conditional. Cooking ideas and
Cooking times were accepted beneath Cooking, so this does not demonstrate a
blanket inability to recognize topic aspects. Those labels remain unresolved;
the user then approved proceeding with all 16,512 directional judgments across
the same 129 original nodes, using unchanged NSP-Jev-v3 and Jev provider-default
at ten concurrent calls. The completed experiment is
`sse_multivector/experiments/nsp-jev-v3-hr02-full-v1/`; preparation found 100
matching saved answers to reuse and 16,412 initially new requests. Execution
completed all 16,512 judgments: 14,426 new calls and 2,086 exact-request reuses,
including matches becoming available during the run. No calls failed or needed
retry; every response passed format and receipt checks. Native choices were
241 Yes, 16,271 No and zero uncertain; these are not accuracy measurements.
Native cost was $0.253775508. Runtime including local reporting was 45 minutes 25 seconds.
All original Astra-low TPv38 titles and upstream artifacts remain unchanged. Every answer,
probability and uncertainty is retained; uncertainty is not a No. The user
subsequently approved constructing the Jev hierarchy using the existing
provisional merge, naming and navigation rules. The reversible merge kernel
now accepts receipt-validated Jev decisions without fabricating TRUE scores;
HD01 uses native Jev Yes, while HD02–05 stay unchanged. The five cycle groups
involve repeated morning-greetings, Bitcoin, Nostr, Coffee and Foods titles.
Merged names used the existing v38/Astra-low workflow with reuse enabled:
five new valid subscription calls, no retries, produced Bitcoin, coffee,
nostr, Foods and Good morning greetings. The completed separate browser is
`target/hierarchy-build-v1/hr02-jev-browser-v1/`: 118 hierarchy nodes, 84 reduced
links, 52 roots and 98 represented posts. All 129 original nodes, 629 source
masks and 16,512 decisions remain traceable; the 27 rejected-but-reachable
pairs were recorded, not repaired. Naming preserved links and reachability.
The viewer passed `--check` and interactive leaf-note/O-view checks with the
existing equal-note navigation collapse. Saved TRUE artifacts are unchanged.
This is ready for user quality review, not a validated hierarchy or production
adoption. Scalable relationship inference and downstream gates remain open.

**HR02 placement diagnostic (approved September 26):** use Jev as the initial
node-placement solution, then correct its failures by hand in a separate
hierarchy so the other stages can be evaluated without placement errors
obscuring them. Preserve the untouched Jev baseline. Keep the same nodes,
titles and memberships; record every changed relationship reversibly, without
quietly repairing other stages. The user's “90% / 10%” framing is not a
measured accuracy claim. The 118-node parent audit is an agent assessment,
not approval of its proposed corrections. Review those proposals and unresolved
boundaries with the user before applying agreed corrections. The corrected
hierarchy is not built or validated yet. This does not adopt Jev/manual repair
as the scalable production method or authorize additional inference.

Approved placement corrections for that separate hierarchy (not yet applied):

| Parent | Child | User decision |
| --- | --- | --- |
| Eggs | Duck eggs | Add. The visible path becomes Foods → Eggs → Duck eggs; the direct Foods → Duck eggs shortcut becomes redundant. The Jev baseline remains unchanged. |
| coffee | Coffee beans | Add while retaining the existing Seeds and seed-derived products parent. Coffee beans will have both parents in the corrected hierarchy. The Jev baseline remains unchanged. |
| coffee | Coffee flavor | Add as the more-specific parent. Food and drink remains an ancestor; its direct Coffee flavor shortcut becomes redundant. The Jev baseline remains unchanged. |
| Foods | Clean, simple dishes | Add. The currently parentless node describes prepared food, not tableware, as supported by its dinner/dish masks. The Jev baseline remains unchanged. |
| Positive emotions and attitudes | Enjoyment of food | Add. Enjoyment denotes pleasure or satisfaction, so the child necessarily concerns a positive experience; the post need not itself express a positive emotion. The Jev baseline remains unchanged. |
| Food and drink | Enjoyment of food | Add alongside Positive emotions and attitudes. Discussing enjoyment of food necessarily concerns food. Both parents are approved for the corrected hierarchy; the Jev baseline remains unchanged. |
| Art | Music | Add. Music is an art form; the parent is Art, not Visual art. The currently parentless Music node gains this parent in the corrected hierarchy only. |
| Cooking | crockpot | Add. A crockpot is a cooking appliance, so it falls within the cooking topic; this is topic containment, not treating an appliance as an action. The Jev baseline remains unchanged. |
| Psychology and philosophy | Psychological distress | Add. Psychological distress falls within the psychology side of this parent; the masks express unhealthy stress and anxiety. The Jev baseline remains unchanged. |
| Personal habit changes | Fasting | Remove. Fasting can be an established practice rather than a change of habits, so containment is not necessary. Leave Fasting parentless for now in the corrected hierarchy; the Jev baseline remains unchanged. |
| Meat consumption | Chickens and chicken products | Remove. The child includes living hens and egg-laying, which do not necessarily concern meat consumption. Retain its existing Animals parent for now; the Jev baseline remains unchanged. |
| Meat consumption | Attitudes toward meat consumption | Add. The user reconfirmed carrying the previously approved relationship into this corrected hierarchy: discussing attitudes toward eating meat necessarily concerns meat consumption. The Jev baseline remains unchanged. |
| Foods | coffee | Remove. The user agreed to interpret Foods as excluding drinks. Its already-accepted Food and drink relationship becomes the direct displayed parent, alongside tea and Wine. Other affected placements still require review; the Jev baseline remains unchanged. |

Mask-prominence work (04) is paused, reconfirmed by the user on September 23.
Its mask-prompt prerequisite is satisfied. It need not wait for the 100-note
hierarchy or title correction. Its prompt and validation are not complete.
The user plans to revisit its open questions during the 100-note hierarchy
build, using what that hierarchy reveals. The exact point remains open; this
does not mark 04 active or authorize work to resume.
The user confirms 17 is underway, comparing Muse high and Astra low;
no teacher is selected.
This does not establish completion of the subject/mask/prominence comparison (17).
Dates are unchanged. The additional construction dependencies below expose
unfinished work. Completing 01 and 23 does not complete the hierarchy. This
records work and planning requirements, not authorization to start another
workstream or approval of the overall plan.

### Status checkpoint — September 25

Tasks 02, 18, 22 and 25 were updated on September 25; 23 on September 24.
Other rows were last confirmed with the user on September 23.
This is a dated checkpoint; current task status appears in `release-plan.json`.

| Task | Status at checkpoint |
| --- | --- |
| 01 · Subject and mask prompts | Finished. |
| 02 · Build and review 100-note hierarchy | In progress; HR02 was generated and reviewed. Promising, but TRUE's relationship decisions prevent validation. Frontier replacement is the next diagnostic; task 25's implementation gate is satisfied. |
| 23 · Fix and validate node-title prompt | Finished; 129 titles saved. |
| 04 · Define mask prominence | Paused. Earlier experimental results do not establish that work is active now. |
| 17 · Compare teachers | In progress; no completed selection established. |
| 26 · Collapse equal-note navigation steps | Implemented and regression-tested; validation on the rebuilt hierarchy is waiting. |
| 13 · Define Nostr hierarchy protocol | Not started. |
| 18 · Prepare training code for the fine-tuning pilot | Candidate recipes and Vast limits frozen locally; VM tests training and SSH deployment. Image remains unpublished. |
| 24 · Recover missing node memberships | Not started. |
| 25 · Handle node equivalence and TRUE cycles | Complete for HR02: exact-mask consolidation and reversible cycle handling are implemented and tested, with naming/browser integration. The merge rules remain provisional; hierarchy-quality review belongs to 02. |
| 21 · Assess HDBSCAN at launch scale | No further progress; earlier investigation remains evidence, not launch-scale validation. |
| 22 · Measure SSE, node-title and relationship-check costs | No further progress; TRUE timing remains baseline evidence, not an assumed launch method. |

This checkpoint records statuses. The later approved correction adds 25 → 02
as a finish dependency; dates, methods and authorization remain unchanged.
Green cards identify work ready now, not work currently underway.

## Vocabulary

Naming approved by the user on September 21, 2026:

| Name | Meaning |
| --- | --- |
| **teachers** | The models that write the training data by running the prompts. More than one teacher is allowed. Replaces "annotation model", "training-data generator" and "annotator". |
| **the distilled model** | Takes a complete note and returns its masks and prominence. Trained in 06/08 and released in 16. Replaces "extractor", "fine-tuned model", "mask/prominence model", "embedding model" and "student". |
| **hierarchy node** | A grouping of masks that appears in the hierarchy. Replaces "category", "fine subject" and "segment"; compounds use "node": node titles, node descriptions, node links, node-note ordering. |
| subjects, masks, prominence | Unchanged. The older "takeaway" and "relevance" wording is retired. |
| **pilot training data** (05) and **full training data** (07) | Always qualify; avoid bare "training data". |

Task titles approved with this vocabulary: 17 · Compare teachers; 05 · Prepare
pilot training data; 06 · Choose the model to train; 07 · Generate full training
data; 08 · Distill and package the model; 11 · Test hierarchy with the distilled
model; titles using "category" use "node" (22, 23, 24, 25, 27). This record uses
the new names, as do both diagram pages. Frozen experiment and research evidence keeps
the wording of its time.

## Agreed release goal

By October 18, 2026, release:

- A public service hosting a genuinely useful hierarchy for discovering Nostr content,
  served through a custom Nostr protocol.
- Notedeck browsing integration, implemented by agents under the user's direction.
- An open-weight distilled model for generating masks and prominence.
- The full hierarchy-generation architecture and code.

A static launch snapshot is acceptable. Continual updates are not required for
launch, but the release documentation must describe a path to supporting them.
Agents write the code; the user directs their work and reviews results rather
than coding personally. The user can oversee overlapping efforts while agents
are working, though parallel capacity is not unlimited or quantified. Individual
agent assignments remain open.

## Corpus scope and size

The launch is intended to cover subjects broadly, not a fixed list of topics.
Include English kind-1 top-level posts; exclude replies and quote posts.

The corpus must be large enough to plausibly provide useful content discovery.
More than one million notes was an initial estimate, not a fixed acceptance
threshold. Breadth and depth of useful coverage matter; raw note count does not
establish either. The final processed count and exact subset remain open.

Use the existing corpus as the starting point. Processing the whole candidate
pool is not committed, and additional collection is not currently a prerequisite.
Reconsider collection if a demonstrated coverage gap warrants it.

### Data already available

These are saved artifact counts, not claims of manually verified English or
adequate subject coverage:

| Collection or filtering stage | Available records |
| --- | ---: |
| Nine-relay acquisition, September 24, 2025–July 24, 2026; kind 1 before filtering | 15,782,558 |
| After root/non-quote and length filtering | 11,595,958 |
| After exact-content deduplication | 9,108,872 |
| After English-or-language-neutral classification | 3,774,156 |
| Same pool with usable text; source of the frozen 1,000-note sample | 3,510,335 |
| Separate older April 2025 Damus archive's English-or-language-neutral pool | 3,530,470 |

The current pool already excludes replies and quote posts. It also carries a
512-token ceiling from earlier embedding-model experiments, and its language
filter accepts language-neutral content and can make classification mistakes.
Those existing filter policies are not newly approved release requirements.
Do not add the older and newer counts together as a verified combined corpus.

Sources: [acquisition and derivation receipts](../../../damus_snapshot/runs/crec-105-fresh-corpus-v9/derivation/derivation-ledger.json),
[deduplication](../../../damus_snapshot/runs/crec-105-fresh-corpus-v9/publication/10m-adcf8f016f6a-v1/global-deduplicated/manifest.json),
[language filtering](../../../damus_snapshot/runs/crec-105-fresh-corpus-v9/publication/10m-adcf8f016f6a-v1/english-eligible/manifest.json),
[usable-text sample provenance](../../semantic_map/crec-120-sample-v1/manifest.json),
[older pool](../../../damus_snapshot/runs/crec-9-complete-cpu-audit-v6/work/english-eligible/manifest.json).

## What the hierarchy runs must validate

Judge complete browsing paths: do nodes offer understandable choices,
narrow meaningfully, and lead to relevant notes? Occasional errors can be
acceptable; repeatedly misleading navigation cannot. Concrete examples from
the builds should inform acceptance, not an invented accuracy percentage.

The 100-note work tests hierarchy correctness at minimal scope and must
establish an initial useful hierarchy; HR02 has not yet met that gate. The
planned 200-note / 2-topic build checks
correctness and prominence-based note ordering. The 300-note / 3-topic build
checks correctness while testing scalable construction choices; candidate-pair
filtering must preserve useful parent–child links, not just reduce relationship
checks.
The 500-note / 5-topic build checks the combined pipeline and profiles build
time and memory to find bottlenecks. All three increase subject coverage; none
is merely a test of handling more notes.

Runtime, memory and million-note processing cost still require separate
measurements. Profiling 500 notes does not establish launch-scale feasibility.

The [fine-tuning pilot](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md)
must measure unseen-note mask and prominence quality before and after training,
improvement with more training data, actual training resources and cost, and
batched generation speed on representative notes. Compare quality against total
training-and-generation cost. This does not estimate the other hierarchy-build
stages or approve a dataset size, hardware rental or spending allocation.

## Two separate model pilots

**September 25 informal start:** the user approved beginning the fine-tuning
pilot with available data from the latest subject and mask prompts, excluding
prominence for now and establishing untuned baselines. The teachers generate
subjects and masks. The user subsequently approved one fine-tune per candidate
on both existing prompted tasks: note → subject hierarchy, then note + subject
→ mask. Both tasks train the same model or adapter. Baseline and trained
evaluation each use that candidate's own generated subjects for the mask calls.
The user approved batching independent evaluation mask requests, with the same
batching and generation settings before and after training. The current recipe
uses up to four masks from one note per batch; training settings are unchanged.
Direct-mask generation is deferred for this informal pilot.
This initial informal experiment may use current saved annotations before
prominence and final teacher selection are ready. Local data is prepared;
no candidate baseline, training run or rental has run. See the
[current pilot preparation](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md#status-and-scope).
The release model still requires prominence. Candidate selection, the larger
pilot's evaluation requirements, full-data gates and paid-resource approval
rules remain in force; the informal result does not complete 06.
The user approved automating and testing the complete workflow in a local VM
before deploying on rented hardware. The local test uses a tiny model and
synthetic data, including actual weight updates, checkpoint interruption/resume,
save/reload and two-step evaluation. The local workflow tests passed;
interrupted training reproduced the uninterrupted adapter weights exactly.
The user clarified that the VM must rehearse the deployment process used on
Vast: prepare an immutable image and frozen inputs locally, upload the inputs,
start the experiment automatically, reconnect and retrieve verified results.
Follow the existing GTE Vast deployment pattern; no manual code edits on the
rented server. The distillation SSH operator runs against a separate container
inside the VM, using the image's installed code and dependencies. Deployment
now uses the image's own SSH entrypoint in Vast args mode, preserving
the tested startup. A reproduced SSH GPU-package lookup defect was fixed; the
VM exercises CUDA preflight over SSH. The local rental controller automates
creation, bounded reconnect, result retrieval and verified destruction, with
provider responses simulated in local lifecycle tests. No code edits or package
installs belong on a running rental. These tests cannot guarantee GPU execution
or provider availability. Candidate
quality, full-model memory use and CUDA compatibility are checked during
the actual pilot, without a separate throwaway GPU training run. Candidate
recipes and Vast limits are now frozen locally: BF16 LoRA, 128 steps per
candidate, one 96 GB GPU, and at most $24.60 under the approved $25 total.
The user explicitly withheld publication. The candidate configurations and
launch procedure are recorded in the pilot plan; no paid launch has occurred.
The user accepted a $25 total maximum for GPU setup, baselines and initial
fine-tunes across the three candidates, including storage, transfers and failed
attempts. No rental has started; ledger admission precedes any paid commitment.

- **Teacher-comparison pilot (17):** choose the teachers that write the training
  data. The current comparison is Muse high versus Astra low; no teacher is
  selected. Assess subjects, masks, prominence and the resulting hierarchies,
  along with generation time, cost and feasibility. How unsuitable annotations
  are handled remains open; repairing them is not an assumed workflow. Check the
  provider's data-use and output-use terms before producing training data at
  scale.
- **Fine-tuning pilot (06):** compare the pretrained models that we will train
  on those annotations and release as the distilled model. This is the
  [existing fine-tuning pilot](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md),
  not the teacher selection.

**Approved fine-tuning candidates (September 24, 2026):** Qwen3.8-27B,
Gemma 4 31B instruction-tuned, and Gemma 4 26B-A4B instruction-tuned. The third
candidate replaces T5Gemma 9B–9B PrefixLM instruction-tuned. Compare its mask
and prominence quality and total training-and-generation cost with the dense
candidates; lower active parameter count does not establish a cost advantage.
The larger pilot's training settings, final example format, prominence criteria
and spending amounts remain open. The informal subject/mask settings and $25
approval above apply only to the current short experiment.

The [teacher research](../../sse_multivector/TOKEN-USAGE-ESTIMATE-1M-NOTES.md#lower-cost-annotation-models)
already identifies Muse. A later [12-note diagnostic](../../sse_multivector/frontier-model-comparison-v1/asv6.23-diagnostic-v2/results.md)
found it promising on subjects with ASv6.23, but with some context omissions.
That diagnostic tested neither masks nor prominence, and did not establish
equivalence to Astra. Its subject-only cost is not a complete labeling estimate.

Selecting the teachers and successfully completing the 500-note / 5-topic
hierarchy validation are both prerequisites for starting full training-data
generation (07). A finished but unsuccessful run does not clear this gate.
For the larger pilot, the same teachers must write both the pilot training data
(05) and the full training data (07), as the user directed on September 21, 2026.
The informal start above may reuse existing annotations before selection. Work that
consumes no labels, such as 18's training-code preparation, may use any data and
need not wait for the teacher selection.

### Teacher-comparison pilot evaluation plan

Node 17 covers the teacher comparison, including its planning.
The user confirms it is in progress, comparing Muse high and Astra low.
Coverage and results of that current comparison have not yet been reported here;
it does not establish completion of 17 or selection of a teacher.

The comparison needs to establish:

- Whether candidates produce suitable subjects, masks and prominence under the
  validated requirements. Subject-only evidence does not establish mask or
  prominence quality.
- Whether hierarchies built from each candidate's own subjects, masks and
  prominence on the same notes, with downstream construction held fixed, offer
  useful browsing paths.
  Compare the hierarchies before selecting teachers; distinguish differences
  caused by teacher outputs from failures shared by the construction pipeline.
  Label-only parity does not settle the selection.
- Whether the selected teachers can supply the intended training data
  within the available time and budget.
- Whether provider data-use and output-use terms permit the intended training
  and open-weight release.

Completing 17 needs the validated subject/mask prompts from 01 and prominence
requirements and prompt from 04. These are completion prerequisites; independent
comparison work is already underway.

The hierarchy A/B comparison is part of 17, not a separate task. The sample,
comparison procedure, review coverage, treatment of unsuitable annotations and
acceptance decisions remain open. No generate–repair–train workflow is
prescribed. Those details belong to the evaluation workstream, not to
assumptions made by this release plan.

Completing the full training data (07) also requires an agreed training volume,
informed by the fine-tuning pilot (06). Its evidence is an input to that decision;
this does not make completion of all of 06 a prerequisite for starting 07.
The September 27 target must be checked against the chosen volume and the
selected teachers. No model calls, experimental procedures or spending are
authorized here.

## Hierarchy construction and service dependencies

Training-data generation uses subject descriptions to guide mask generation,
with prominence assessed for each mask in its note. The intended distilled
model instead takes a complete note and produces grouped source-text masks
plus prominence. It must discover subjects, but its output need not include
English subject descriptions. The plan does not require a separate
subject-generation call for each final-corpus note.

The shared hierarchy construction is masks → SSE vectors → flat HDBSCAN groups →
node descriptions → cosine-filtered candidate pairs → subsumption judgments →
directed node hierarchy. Prominence supports note ordering. The relationship
method remains open: TRUE generated HR02, but its judgments were not good
enough. The separate Jev hierarchy is now the diagnostic baseline; the approved
next step is a separately recorded manual placement correction for evaluating
the other stages, not a production choice.
The cosine cutoff and its implementation remain open. Existing all-pairs
experiments do not establish filtered behavior; filtering must preserve useful
parent–child links, not merely reduce calls.

The formal process also requires identical same-post masks to be deduplicated
before SSE, nodes with identical mask sets to be merged before hierarchy
generation, and parent–child navigation steps with identical complete post sets
to be collapsed before hierarchy publication. Retain strict mask-set subsets;
they can represent useful narrower nodes. Preserve source references and
original node IDs. These rules do not decide semantic equivalence between
different mask sets. The
[required stages and their limits](../../sse_multivector/navigation-research-v1/README.md#required-hierarchy-processing-stages)
record the requirements. Shared-child collapse is implemented and tested in the
node browser, and enabled for both HRv1 comparison views without changing
saved memberships. Repeatable semantic-equivalence decisions remain open.
This is not a claim that the existing experimental pipeline implements all
these stages end to end.

**Merged-node naming (approved September 24):** once nodes are merged, generate
the merged node's displayed title from their combined, deduplicated masks using
the frozen v38 prompt. HR02 now uses Astra low for merged titles as well as
individual titles, explicitly approved after scoring completed; earlier
Luna-max artifacts remain unchanged. Do not arbitrarily
choose a member's title. Preserve every original title and node ID. This call
only names the merged node: it does not decide the merge, change its links or
trigger another round of TRUE comparisons. The offline preparation, verified
title collection and browser export are implemented; a four-node live check
is complete. TRUE's relationship quality prevented HR02 validation; the separate
Jev baseline and approved manual-placement diagnostic above are the current
direction. This does not authorize further model calls or settle the provisional
merge policy.

### Reversible hierarchy design decisions

The user requested this register on September 24 so uncertain choices remain
explicit and can be unwound. These are experiment choices, not claims of
correctness or completion. Alternatives listed here are not approved work.
Bring changes to these choices, and newly discovered design choices, to the
user before implementation; do not resolve them through per-node exceptions.

| ID | Choice and status | Uncertainty / tradeoff | How to revisit it |
| --- | --- | --- | --- |
| HD01 | **Current experiment rule:** native TRUE Yes creates an edge; no score cutoff. | Native answers miss useful links; the tested cutoff adds both useful and incorrect links. Neither is assumed correct. | Preserve exact title inputs, generated answers, scores and runtime identity; rebuild edges from saved outputs under another explicitly selected rule. |
| HD02 | **Provisional merge rule:** merge mutually reachable nodes (strongly connected components). Implemented and tested; HR02 is exported for quality review under task 02. | Correct subsumption cycles imply equivalence, but predicted cycles can be wrong. The user identified Beef / Beef products as an incorrect NEv2 merge. Saved examples have pairwise mutual Yes answers; a synthetic regression also covers longer cycles without them. | Keep the original nodes, masks, titles, edges and component membership. Rebuild from the pre-merge graph instead of trying to split a merged record after originals were discarded. |
| HD03 | **Current HR02 experimental rule, mechanically tested but not settled:** retain any accepted incoming/outgoing connection of a merged member, preserving existing paths. | This favors accepted paths over contradictory direct No answers. The contradiction can exist before merging: Beef -> Beef products -> Steak, alongside a direct No for Beef -> Steak. Record the disagreement; do not silently repair it. | Preserve every Yes and No and the original edge contributors. A different conflict policy starts from those answers and may require recomputing merges and descendants, not merely editing the displayed links. |
| HD04 | **Implemented:** generate merged titles through the frozen title workflow; bind returned names to exact combined-mask inputs and change labels only. Four-node live check and all six HR02 merged titles are complete. | The new wording may suggest a different scope from the original titles used by TRUE. The naming call does not establish new relationship evidence. | Save member titles, combined-mask input, prompt/model settings and generated title. A naming-only alternative need not rerun extraction or TRUE; using new titles for relationships would be a separate design change. |
| HD05 | **Implemented and tested:** derive a new merged-node ID from the SHA-256 of the sorted original member-ID list, preserving every original ID. | The same members produce the same merged ID regardless of member order or displayed title. This identifies the merge, not independently verified semantic equivalence. | Keep the original-member mapping and ID-rule version. A different membership or ID rule can be rebuilt from that mapping; changing only the displayed title must not change the ID. |
| HD06 | **Approved comparison design, not implemented:** preserve the first run's original reviewed view and create a separate reprocessed view from its saved nodes and TRUE answers using the new run's merging and navigation rules. Compare the new run primarily against the reprocessed view. | The first run included manual extraction corrections, group exclusions and a title override. Matching downstream rules does not make those inputs an untouched automatic baseline. | Freeze the original subjects, masks, node titles, answers and reviewed artifacts; do not regenerate them. Record the reprocessing policies and historical interventions separately so the original and reprocessed views remain inspectable. |

**NEv2 user review (September 25):** Coffee, Food, and morning-greetings merges
accepted ("the other 3 look fine"); Beef / Beef products remains rejected.
These four case decisions do not settle the provisional merge/link rules or
authorize another run. The selected stress sample is not an accuracy estimate.
The saved graph remains unchanged; no per-node correction was applied.

Before a future run, record the selected decision IDs, their exact policy
versions and source hashes in its manifest. Preserve raw outputs separately
from derived graphs and browser views; later experiments must not overwrite
earlier evidence. Reuse unaffected saved stages, but recompute downstream
merges, memberships and navigation when their inputs change. This is a build
requirement, not a claim that the current runner already implements it.
The [offline merge stage](../../sse_multivector/navigation-research-v1/README.md#reversible-merge-stage)
records policy versions, source hashes and reversible inputs. Saved NEv2 and
TRUE10 replays preserve paths and post membership. The [offline construction
path](../../sse_multivector/navigation-research-v1/README.md#offline-construction-path)
now connects exact-mask-set consolidation, receipt-validated v38 titles, TRUE
input preparation, cycle merging, naming and browser export. HD04's subsequent
four-case naming run produced four valid titles without changing the sample's
links. The 19-node browser passed mechanical and interactive checks. Node IDs
are now hidden during browsing to avoid title truncation and remain available
in `?` analysis; stored IDs and displayed mask IDs are unchanged. HD06 still lacks a
published reprocessed browser view.

**HR02 — second 100-post hierarchy:** the existing goal, reaffirmed by the user on
September 25, is to generate a hierarchy the user is pleased with, not to
optimize cost, speed or teacher selection. Model comparisons are not its success
criterion. The user subsequently authorized individual title generation and
inspection with Astra low and unchanged v38, reusing all upstream data, then
approved TRUE scoring of those titles with all nodes retained and the two
user-rejected titles flagged. After scoring, the user also approved Astra low
for the six merged titles with unchanged v38. This does not authorize an
all-Luna comparison. The architecture is unchanged.
HR02 is the experiment's discussion ID; existing artifact paths and frozen
internal run IDs are retained; the new scoring run is `HR02-v38-gpt-6-astra`.

**HR02 execution (authorized September 25):** local TRUE scoring completed
for all 129 saved nodes, with exact-input cache reuse. The frozen plan
is `target/hierarchy-build-v1/astra-true-v1/plan.json`; it records policy versions,
source/input hashes and cache provenance. HD01–05 remain unchanged, including
the provisional HD02/03 rules. No membership expansion or Beef-specific repair
is included. The earlier Luna-title run is stopped, not complete; its saved
prefix supplied only verified exact-input answers to the new run. Six merged
titles completed in `experiments/hr02-merged-titles-v38-astra-low/` with six
subscription calls, no retries, and verified unchanged links/reachability.
The 116-node graph and 56 reduced links remain provisional. Browser export is
saved in `target/hierarchy-build-v1/hr02-browser-v1/`; the existing viewer passed
`--check` and interactive navigation/mask checks. It shows 98 represented posts
and adds an All notes entry. Both user-rejected titles remain flagged in analysis.
The user reviewed the hierarchy and found it promising but not validated:
TRUE's relationship decisions were not a good fit. The subsequent Jev baseline
and approved manual-placement diagnostic are recorded above. Completed inference
and this review do not settle the provisional merge policies.

**Hierarchy execution recovery (clarified September 24):** retry failed model
calls and reuse successful results. Preserve failed-attempt receipts and the
original inputs/settings; failure is not a No answer or permission to drop a
node. This is routine recovery, not an unresolved hierarchy-design choice. It
does not authorize a new run, unlimited retries or changes to the general
runner's current retry implementation.

For HD06, original node titles remain frozen; naming a newly merged node is
the separate HD04 operation, not regeneration of those original titles. Keep
the new comparison free of the excluded membership-expansion experiment.
Recording these designs, or HD03 as a candidate, does not authorize
implementation, inference or another hierarchy run.

Recovering missing node memberships is a separate operation. HDBSCAN's raw
tree is not the specified launch hierarchy.

### Remaining construction work and completion dependencies

The user approved surfacing the audit findings in the dependency map. These are
required outcomes, not selected implementation methods or new dates:

| Task | Required result | Completion dependency |
| --- | --- | --- |
| **24 · Recover missing node memberships** | A repeatable recovery process beyond the six Coffee/Tea nodes, covering masks left unassigned or grouped elsewhere. Measure its work and cost. | Required to finish 03; available measurements inform 20 without waiting for all of 24. |
| **25 · Handle node equivalence and TRUE cycles** | Apply exact mask-set consolidation and a reversible, repeatable rule for HR02's equivalence candidates and cyclic TRUE answers. Provisional contraction does not prove that a cycle or equal title means semantic equivalence. | Implemented for HR02; its finish dependency for 02 is satisfied. Quality validation remains in 02. |
| **26 · Collapse equal-note navigation steps** | Implement and validate the required navigation simplification, including shared children, while preserving note sets, masks and provenance. | Required to finish 03. |
| **27 · Order node notes using mask prominence** | Define and implement how relevant mask scores produce node-note order, including multiple masks and shared descendants. | Needs prominence definition 04; required to finish 03. |
| **28 · Implement and validate the launch-scale build** | Turn the strategies tested in 03 and the scale findings into a runnable launch-scale build preserving validated hierarchy behavior, including cosine-filtered relationship checks and large-group title inputs. The relationship method is open. | Needs 03 + 21 + 22; required to finish full-build feasibility 10. |

24 can start from saved artifacts and remains unstarted. 25 is complete for
HR02: both merge stages, provenance-preserving naming and browser export are
implemented and tested. The four-merge user review accepted three and rejected
Beef; it was not blanket approval of the provisional rule. Further quality
validation of the rebuilt hierarchy remains in 02.
For 26, the [browser implementation and regression checks](../../sse_multivector/navigation-research-v1/README.md#shared-child-collapse)
are complete; validation of this simplification in a rebuilt hierarchy remains
pending.
27 waits for 04, which remains paused. 28 waits for the validated small-corpus
workflow and scale findings. Readiness does not authorize execution. Membership
methods, final node-equivalence/cycle policy, ranking rules and scale
implementation choices remain open.

The 100-note build exposed a relationship-quality blocker at minimal scope,
without membership expansion or a claim to exercise scalable construction.
Task 25's implementation gate is satisfied. Task 02 remains open while a
frontier-call diagnostic tests whether the other stages support a useful
hierarchy. Preliminary 200-note construction can follow 02 while prominence
is paused, but its note-ordering check needs 04 and 27. The 300-note
scalable-construction work can proceed without waiting for that ordering
check. Completing the combined 500-note validation (03) requires
24–27. The prominence dependency remains 04 → 27 → 03. The stages' internal
processing order must respect their inputs, but this does not impose a serial
development schedule.

Pilot **06** also includes a small hierarchy built from pilot-model outputs before
model selection. Use that check to detect downstream consequences of extraction
errors; distinguish those from failures in the shared hierarchy pipeline. **11**
still verifies the final distilled model before the launch build. The new pilot
check belongs within 06 rather than a separate node or a dependency on finishing
the final fine-tune.

Early scale assessment 20 includes membership-recovery and graph-processing
costs, not only model calls. It can use available evidence from 24 and the growing
hierarchy builds; it does not wait for the finished implementation in 28.

Service testing needs both the protocol and a saved hierarchy snapshot. The
100-note hierarchy can supply the initial snapshot; service development need
not wait for the final corpus build. Public launch requires the final snapshot.

Pilot-model measurements can inform scaling work before the release model is
trained. They are useful early input, not a requirement to start investigating
scaling and not a substitute for release-model measurements.

### Publication preparation

Publication preparation belongs to the existing tasks, not a new workstream:

| Task | Required result for publication |
| --- | --- |
| **06 · Choose the model to train** | Confirm permission to release fine-tuned weights before selecting the base model and committing to the larger training run. Teacher provider permissions remain in 17. |
| **08 · Distill and package the model** | Prepare trained weights, necessary supporting files, usage instructions and evaluation results. Verify that the intended release files load and generate masks and prominence. |
| **12 · Build launch hierarchy snapshot** | Prepare runnable hierarchy-generation code and instructions, architecture documentation matching the actual build, and the agreed continual-update path. |
| **16 · Launch public hierarchy** | Publish the prepared model, code and documentation alongside the service and Notedeck integration. |

Preparation can accompany development; final verification requires the actual
release artifacts. Checking an internal training checkpoint alone does not
establish that the intended public files and instructions work together.
File formats, publishing locations and implementation methods remain open.
Publishing the training dataset is not an additional release requirement.
No dates, dependency arrows, model choices or spending approvals change.

### Scale measurements and final validation

The [scalability record](scalability.md) distinguishes findings, user decisions
and proposed next steps from the separately authorized read-only investigation.
It does not approve implementation, benchmarks, spending or diagram changes.

- **21 · Assess HDBSCAN at launch scale:** determine whether HDBSCAN can form our
  mask-vector groups at the intended corpus size within budget and deadline,
  preserving our grouping rules, and identify any work required. This assessment
  has had a separately authorized read-only code/evidence investigation;
  launch-scale feasibility remains unproven. Implementation and performance
  runs have not been authorized by that investigation.
  It does not presume that HDBSCAN or its implementation must be replaced. Its
  findings are needed for the HDBSCAN portion of 20; they do not block independent
  measurements of other stages.
- **22 · Measure SSE, node-title and relationship-check costs:** use existing
  masks and nodes to measure time, memory and cost. Preserve TRUE's historical
  rate as a baseline, but include the eventually selected relationship method
  before completing build-cost estimates. Include how title input length grows
  with group size, not only cost per call.
  This is ready independently of 21's HDBSCAN assessment. No measurement
  procedure, hardware choice or spending is approved here.
- **20 · Assess full hierarchy-build resources:** combine stage measurements
  from 22, HDBSCAN requirements from 21, mask/prominence generation measurements
  from the fine-tuning pilot (06), and mask/node/cosine-filtered-pair counts
  from the growing hierarchy builds (03). Estimate launch-build time, memory and
  cost to inform an affordable corpus size while preserving hierarchy quality.
  Include membership-recovery and graph-processing costs; available recovery
  measurements from 24 are an additional dashed input.
  It stays grey pending inputs from 21 and 22. The dashed 06 and 03 inputs allow
  available evidence to be used without waiting for those workstreams to finish.
  Per-pair relationship cost alone does not establish total hierarchy-build cost.
- **09 · Choose notes for launch hierarchy:** use the early measurements, agreed
  corpus scope and useful-coverage requirements to choose the intended corpus and
  freeze its IDs. Corpus size is not fixed before feasibility is investigated;
  the selected size still needs final validation.
- **10 · Check full-build time and cost:** establish whether the distilled model
  can generate masks and prominence for the selected launch corpus, and the
  remaining pipeline can construct its full hierarchy, within the remaining
  budget and before October 18. This needs the trained model, corpus selection,
  resource measurements and the runnable build from 28; early estimates alone
  do not establish feasibility.
- **11 · Test hierarchy with the distilled model:** build a sample hierarchy from
  that model's masks and prominence; check browsing and whether the complete
  pipeline works before processing the full launch corpus.

10 and 11 are distinct checks: whether the full launch build fits the budget
and deadline, and whether the distilled model's outputs produce a useful
hierarchy. Both need evidence before 12; neither is required to finish before
the other. They may share measurements, but that does not merge their purposes
or require another planning decision. How they share work belongs to execution.

**18 · Prepare training code for the fine-tuning pilot** is ready within the
draft. Its scope is code to fine-tune each specified candidate model, save and
reload its trained weights, and generate outputs for evaluation. This preparation
does not require the final prominence definition or training-output format and
does not select a framework or training method.

Final training-example formatting and mask/prominence quality evaluation remain
within **06 · Choose the model to train**. Its completion needs the agreed output
format, prominence criteria, reviewed pilot data and training setup (05 + 18).
The September 25 informal subject-and-mask experiment can start preparation
using available data while those completion requirements remain outstanding.
The subsequent $25 informal-pilot approval above bounds paid execution;
training settings and ledger admission still need to be established.

These are planning dependencies, not approval for measurements, model calls or
paid runs in this discussion. Measurement procedures, sample sizes, the cosine
cutoff, measured rates and counts, and the final corpus size remain open.

## Approved scheduling changes

1. After the good 100-note hierarchy, use 200 notes to test correctness and
   prominence-based ordering, 300 to test correctness and scalable construction,
   and 500 to validate them together and profile the build. The 200-note
   construction can start while prominence is paused, but its ordering check
   cannot finish without 04 and 27. The 300-note work need not wait for that
   check. The combined 500-note validation still needs 24–27.
2. Start scale measurements during Week 2. Measure the complete build, including
   SSE, HDBSCAN, node titles and cosine-filtered relationship checks, rather
   than relying only on distilled-model training or generation speed. Node 22
   measures SSE, node titles and relationship checks using existing masks and
   nodes, independently of 21's HDBSCAN assessment. Node 20 combines those
   findings with pilot-model measurements and growing-build counts as they
   become available. The combined assessment informs corpus selection in 09.
   Node 10 then checks time and cost for mask and prominence generation with the
   distilled model and hierarchy construction across the intended launch corpus.
3. Bring protocol work and basic service/Notedeck integration forward, using a
   small saved hierarchy snapshot rather than waiting for the final corpus.
   Do not leave the first complete integration to Week 5; preserve time then
   for verification and fixes. Show this work as an explicit parallel track on
   the weekly diagram, alongside hierarchy/model development rather than mainly
   under Weeks 4–5. Service development can begin after the protocol; testing
   with the saved hierarchy needs the 100-note snapshot as well.
   Notedeck can start from the protocol and finish integration with the service.
   Launch still needs the final snapshot. The track adds no week assignments or
   dates; the earlier integration date remains open.
4. Include a separate teacher-comparison pilot before generating the full
   training data, alongside the fine-tuning pilot. Muse is the leading teacher
   candidate to evaluate, not an approved production choice. Week 2 is the proposed window for both
   pilots; their exact schedules remain open.
5. Target **September 27, 2026** for training-data readiness: suitable masks and
   prominence data available for training, with training/evaluation separation.
   The volume, quality checks and handling of unsuitable annotations remain
   open; the target does not prescribe a correction workflow.

The October 18 deadline and release requirements are unchanged. Full
training-data generation starts only after successful completion of the
500-note hierarchy validation and teacher selection; the September 27 target
does not override this gate. Starting the final fine-tune requires both the
selected base model and sufficient reviewed training data. September 27 is an
agreed readiness target, not a demonstrated completion forecast. Training
volume and the time required to produce suitable data remain unresolved. These
timing decisions do not authorize work to begin or establish that the full
schedule fits.

## Compute, hosting and budget

| Work | Agreed location |
| --- | --- |
| Model fine-tuning, including the planned pilot fine-tunes | Vast.ai |
| GPU work for generating the hierarchy snapshot | Vast.ai |
| Local processing and orchestration | The user's own servers; detailed allocation remains open |
| Public service serving the completed snapshot through the Nostr protocol | Rented hosting |

Do not assume that training or snapshot GPU work will run on the user's own
GPUs. The rented public endpoint serves completed data; it does not build the
hierarchy or require live model inference for browsing.

Six months of public hosting is a **provisional planning target**, not a finalized
commitment. If launch occurs on October 18, that would extend through April 18,
2027. The hosting provider, capacity and cost remain open.

The $1,000 lifetime paid-resource cap still applies, including prior spending,
Vast.ai training and snapshot GPU costs, hosting, storage, transfers and reruns.
Account for the intended hosting period before allocating the remaining budget.

Keep hosting costs and reserves out of `budget-ledger.json`. Hosting estimates
belong in release planning, separately from that ledger. This accounting decision
does not change the overall cap or approve the proposed $200 hosting reserve.
No allocation or new spending is approved by this document.

## Still open

- Final corpus subset and processed count; whether existing length and language
  filtering policies meet the release scope.
- Concrete release-quality judgments, informed by the expanding hierarchy builds.
- Teacher selection, the base model for the distilled model, both pilots' details and final training volume.
- Teacher-output quality checks and treatment of unsuitable outputs.
- Scale-measurement procedures, measured rates and counts, and the cosine cutoff.
- Measured costs and budget allocations; rented-host capacity and confirmed duration.
- Detailed task ownership and a feasible calendar within the proposed five-week sequence.

The diagram's page 2 incorporates these approved scheduling changes into the
weekly targets. Other targets remain provisional until their dependencies,
durations and owners are settled.
