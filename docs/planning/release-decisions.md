# October 18 release decisions

Updated September 25, 2026. This is the written record of the planning discussion.
Agreed requirements, tentative choices and existing-data facts are distinguished
below. The overall plan is not approved. Approval of an individual requirement
or diagram edit does not approve the whole plan. The diagram incorporates the
approved scheduling changes below; other weekly targets and exact dates remain
proposals.

This discussion is for planning: outcomes, dependencies, open decisions and
timing. It does not select implementation methods or experimental procedures.
Readiness is not authorization to research, implement, assign agents or spend;
each task requires explicit approval to begin.

The subject and mask prompts are finished (01 complete), confirmed by the user
on September 20. On September 24, the user confirmed that the node-title prompt
is finished (23 complete). The [frozen v38/Luna max title pass](../../sse_multivector/navigation-research-v1/README.md#current-title-prompt-experiment) has produced
valid titles for all 129 groups in the 100-note build: 108 new calls and 21
reused results. The saved HRv1 hierarchy still uses the older v21 titles.
Task 02 resumed with the user's approval on September 25. The construction path
validated those saved v38 titles and prepared all 16,512 directed TRUE inputs.
Local scoring is underway: 14,207 distinct inputs need fresh inference, with
559 distinct inputs reused from verified saved results.
The historical HRv1 runner and artifacts remain on v21. TRUE placement, merged
naming and hierarchy review remain. The solid 23 → 02 prerequisite is satisfied;
25 is required to finish 02, not to start its TRUE work.
The full pass was mechanically valid; spot checks found some questionable
titles, and the user has not approved every output. Prompt changes and
validation procedures belong to that workstream, not this planning discussion.
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

Tasks 02 and 25 were updated on September 25; 23 on September 24. Other rows
were last confirmed with the user on September 23.

| Task | Current status |
| --- | --- |
| 01 · Subject and mask prompts | Finished. |
| 02 · Build and review 100-note hierarchy | In progress; full v38 TRUE scoring underway. Merged naming, browser export and minimal-scope correctness review remain. Task 25 is a finish gate. |
| 23 · Fix and validate node-title prompt | Finished; 129 titles saved. |
| 04 · Define mask prominence | Paused. Earlier experimental results do not establish that work is active now. |
| 17 · Compare teachers | In progress; no completed selection established. |
| 26 · Collapse equal-note navigation steps | Implemented and regression-tested; validation on the rebuilt hierarchy is waiting. |
| 13 · Define Nostr hierarchy protocol | Not started. |
| 18 · Prepare training code for the fine-tuning pilot | Not started. |
| 24 · Recover missing node memberships | Not started. |
| 25 · Handle node equivalence and TRUE cycles | Both merge stages and naming/browser integration implemented; four-merge user review complete (three accepted, Beef rejected). Full rebuilt-hierarchy validation remains. |
| 21 · Assess HDBSCAN at launch scale | No further progress; earlier investigation remains evidence, not launch-scale validation. |
| 22 · Measure SSE, node-title and TRUE processing costs | No further progress. |

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

The 100-note build tests hierarchy correctness at minimal scope and establishes
an initial useful hierarchy. The planned 200-note / 2-topic build checks
correctness and prominence-based note ordering. The 300-note / 3-topic build
checks correctness while testing scalable construction choices; candidate-pair
filtering must preserve useful parent–child links, not just reduce TRUE calls.
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
Training settings, final example format, prominence criteria and spending
amounts remain open. This candidate selection authorizes no training or rentals.

The [teacher research](../../sse_multivector/TOKEN-USAGE-ESTIMATE-1M-NOTES.md#lower-cost-annotation-models)
already identifies Muse. A later [12-note diagnostic](../../sse_multivector/frontier-model-comparison-v1/asv6.23-diagnostic-v2/results.md)
found it promising on subjects with ASv6.23, but with some context omissions.
That diagnostic tested neither masks nor prominence, and did not establish
equivalence to Astra. Its subject-only cost is not a complete labeling estimate.

Selecting the teachers and successfully completing the 500-note / 5-topic
hierarchy validation are both prerequisites for starting full training-data
generation (07). A finished but unsuccessful run does not clear this gate.
The same teachers must write both the pilot training data (05) and the full
training data (07), as the user directed on September 21, 2026. Work that
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
node descriptions → cosine-filtered candidate pairs → TRUE subsumption
checks → directed node hierarchy. Prominence supports note ordering. The
cosine cutoff and its implementation remain open. This describes the intended
build, not a claim that existing all-pairs experiments already implement
filtering. Fewer TRUE comparisons alone do not establish success: filtering
must preserve useful parent–child links.

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
the existing frozen title configuration (v38/Luna max). Do not arbitrarily
choose a member's title. Preserve every original title and node ID. This call
only names the merged node: it does not decide the merge, change its links or
trigger another round of TRUE comparisons. The offline preparation, verified
title collection and browser export are implemented; a four-node live check
is complete. Full hierarchy review remains. This does not authorize further
model calls or settle the provisional merge
policy.

### Reversible hierarchy design decisions

The user requested this register on September 24 so uncertain choices remain
explicit and can be unwound. These are experiment choices, not claims of
correctness or completion. Alternatives listed here are not approved work.
Bring changes to these choices, and newly discovered design choices, to the
user before implementation; do not resolve them through per-node exceptions.

| ID | Choice and status | Uncertainty / tradeoff | How to revisit it |
| --- | --- | --- | --- |
| HD01 | **Current experiment rule:** native TRUE Yes creates an edge; no score cutoff. | Native answers miss useful links; the tested cutoff adds both useful and incorrect links. Neither is assumed correct. | Preserve exact title inputs, generated answers, scores and runtime identity; rebuild edges from saved outputs under another explicitly selected rule. |
| HD02 | **Provisional merge rule:** merge mutually reachable nodes (strongly connected components). Offline construction stages integrated and tested; rebuilt-hierarchy validation pending. | Correct subsumption cycles imply equivalence, but predicted cycles can be wrong. The user identified Beef / Beef products as an incorrect NEv2 merge. Saved examples have pairwise mutual Yes answers; a synthetic regression also covers longer cycles without them. | Keep the original nodes, masks, titles, edges and component membership. Rebuild from the pre-merge graph instead of trying to split a merged record after originals were discarded. |
| HD03 | **Candidate, mechanically tested but not settled:** retain any accepted incoming/outgoing connection of a merged member, preserving existing paths. | This favors accepted paths over contradictory direct No answers. The contradiction can exist before merging: Beef -> Beef products -> Steak, alongside a direct No for Beef -> Steak. Record the disagreement; do not silently repair it. | Preserve every Yes and No and the original edge contributors. A different conflict policy starts from those answers and may require recomputing merges and descendants, not merely editing the displayed links. |
| HD04 | **Implemented, four-node live check complete:** generate the merged title through the frozen title workflow; bind returned names to exact combined-mask inputs and change labels only. | The new wording may suggest a different scope from the original titles used by TRUE. The naming call does not establish new relationship evidence. | Save member titles, combined-mask input, prompt/model settings and generated title. A naming-only alternative need not rerun extraction or TRUE; using new titles for relationships would be a separate design change. |
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

**Full rebuilt hierarchy (authorized September 25):** local TRUE scoring is
underway for all 129 saved nodes, with exact-input cache reuse. The frozen plan
is `target/hierarchy-build-v1/full-true-v1/plan.json`; it records policy versions,
source/input hashes and cache provenance. HD01–05 remain unchanged, including
the provisional HD02/03 rules. No membership expansion or Beef-specific repair
is included. Scoring completion, full merged naming, browser export and review
remain pending; starting this run does not settle the merge policies.

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
| **25 · Handle node equivalence and TRUE cycles** | Apply exact mask-set consolidation and establish repeatable handling of semantic equivalents and cyclic TRUE answers. A cycle or equal title alone does not justify merging. | Required to finish 02 and therefore 03; 02 can begin TRUE work first. |
| **26 · Collapse equal-note navigation steps** | Implement and validate the required navigation simplification, including shared children, while preserving note sets, masks and provenance. | Required to finish 03. |
| **27 · Order node notes using mask prominence** | Define and implement how relevant mask scores produce node-note order, including multiple masks and shared descendants. | Needs prominence definition 04; required to finish 03. |
| **28 · Implement and validate the launch-scale build** | Turn the strategies tested in 03 and the scale findings into a runnable launch-scale build preserving validated hierarchy behavior, including cosine-filtered TRUE and large-group title inputs. | Needs 03 + 21 + 22; required to finish full-build feasibility 10. |

24 can start from saved artifacts and remains unstarted. 25 has an offline
construction path checked against saved results and a completed four-node
live naming/UI check and four-merge user review (three accepted, Beef rejected);
validation on the full rebuilt hierarchy remains.
For 26, the [browser implementation and regression checks](../../sse_multivector/navigation-research-v1/README.md#shared-child-collapse)
are complete; validation on the rebuilt HRv1 hierarchy awaits graph packaging.
27 waits for 04, which remains paused. 28 waits for the validated small-corpus
workflow and scale findings. Readiness does not authorize execution. Membership
methods, node-equivalence/cycle handling, ranking rules and scale
implementation choices remain open.

The current 100-note diagnostic checks correctness at minimal scope, without
membership expansion or a claim to exercise scalable construction. It can
start TRUE work before 25 is finished, but cannot finish if equivalence or
cycles prevent a valid browsable graph. Preliminary 200-note construction can
follow 02 while prominence is paused, but its note-ordering check needs 04 and
27. The 300-note scalable-construction work can proceed without waiting for
that ordering check. Completing the combined 500-note validation (03) requires
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
- **22 · Measure SSE, node-title and TRUE processing costs:** use existing
  masks and nodes to measure time, memory and cost for these three stages.
  Include how title input length grows with group size, not only cost per call.
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
  Per-pair TRUE cost alone does not establish total hierarchy-build cost.
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
within **06 · Choose the model to train**, once the agreed output format,
prominence criteria and reviewed pilot data are available. Node 06 still depends
on 05 and 18; no extra node or new dependency is needed. Marking 18 ready does not
authorize implementation or pilot runs.

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
   SSE, HDBSCAN, node titles and cosine-filtered TRUE comparisons, rather
   than relying only on distilled-model training or generation speed. Node 22
   measures SSE, node titles and TRUE using existing masks and nodes,
   independently
   of 21's HDBSCAN assessment. Node 20 combines those findings with pilot-model
   measurements and growing-build counts as they become available. The combined
   assessment informs corpus selection in 09. Node 10
   then checks time and cost for mask and prominence generation with the
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
