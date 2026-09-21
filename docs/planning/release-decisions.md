# October 18 release decisions

Updated September 20, 2026. This is the written record of the planning discussion.
Agreed requirements, tentative choices and existing-data facts are distinguished
below. The overall plan is not approved. Approval of an individual requirement
or diagram edit does not approve the whole plan. The diagram incorporates the
approved scheduling changes below; other weekly targets and exact dates remain
proposals.

This discussion is for planning: outcomes, dependencies, open decisions and
timing. It does not select implementation methods or experimental procedures.
Readiness is not authorization to research, implement, assign agents or spend;
each task requires explicit approval to begin.

Current status, confirmed by the user on September 20: the subject and mask
prompts are finished (01 complete). The 100-note hierarchy is being generated
(02 in progress); its review and validation remain pending. Mask-prominence work
(04) was paused for the mask prompt. That prerequisite is now satisfied, but
resumption has not been confirmed. It need not wait for the 100-note hierarchy;
its prompt and validation are not complete. The user reports work on 19 underway,
comparing Muse high and Astra low; no training-data generator is selected.
This does not establish completion of the subject/mask/prominence comparison (17).
Dates and dependency relationships are unchanged; completing 01 satisfies that
prerequisite without completing downstream work. This update does not start
another workstream or approve the plan.

## Agreed release goal

By October 18, 2026, release:

- A public service hosting a genuinely useful hierarchy for discovering Nostr content,
  served through a custom Nostr protocol.
- Notedeck browsing integration, implemented by agents under the user's direction.
- An open-weight fine-tuned model for generating masks and prominence.
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

Judge complete browsing paths: do categories offer understandable choices,
narrow meaningfully, and lead to relevant notes? Occasional errors can be
acceptable; repeatedly misleading navigation cannot. Concrete examples from
the builds should inform acceptance, not an invented accuracy percentage.

The 100-note build establishes an initial useful hierarchy. The planned
200-note / 2-topic, 300-note / 3-topic and 500-note / 5-topic builds test whether
that browsing quality survives increasing subject coverage. They are not merely
tests of handling more notes. Validate prominence in the 500-note hierarchy.

Runtime, memory and million-note processing cost require separate measurements.
Success at 500 notes does not by itself establish production-scale feasibility.

The [extractor pilot](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md)
must measure unseen-note mask and prominence quality before and after training,
improvement with more training data, actual training resources and cost, and
batched generation speed on representative notes. Compare quality against total
training-and-generation cost. This does not estimate the other hierarchy-build
stages or approve a dataset size, hardware rental or spending allocation.

## Two separate model pilots

- **Annotation-model pilot:** choose the model that generates the training data.
  The current comparison is Muse high versus Astra low; no model is selected.
  Assess subjects, masks and prominence with the validated prompts, along with
  generation time, cost and feasibility. How unsuitable annotations are handled
  remains open; repairing them is not an assumed workflow. Check the provider's
  data-use and output-use terms before producing training data at scale.
- **Fine-tuning pilot:** compare the pretrained models that we will train on
  those annotations and release as the mask/prominence extractor. This is the
  [existing extractor pilot](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md),
  not the annotation-model selection.

The [annotation-model research](../../sse_multivector/TOKEN-USAGE-ESTIMATE-1M-NOTES.md#lower-cost-annotation-models)
already identifies Muse. A later [12-note diagnostic](../../sse_multivector/frontier-model-comparison-v1/asv6.23-diagnostic-v2/results.md)
found it promising on subjects with ASv6.23, but with some context omissions.
That diagnostic tested neither masks nor prominence, and did not establish
equivalence to Astra. Its subject-only cost is not a complete labeling estimate.

Selecting the annotation model and completing the 500-note validation are both
prerequisites for bulk training-data generation. Earlier fine-tuning preparation
and pilots can use reviewed data from the existing annotation process; they do
not automatically have to wait for the cheaper annotator to be selected.

### Annotation-model pilot evaluation plan

Node 19 defines how candidate models will be compared; node 17 provides evidence
for selection. The user reports 19 in progress, comparing Muse high and Astra low.
Coverage and results of that current comparison have not yet been reported here;
it does not establish completion of 17 or selection of a model.

The comparison needs to establish:

- Whether candidates produce suitable subjects, masks and prominence under the
  validated requirements. Subject-only evidence does not establish mask or
  prominence quality.
- Whether the selected annotation process can supply the intended training data
  within the available time and budget.
- Whether provider data-use and output-use terms permit the intended training
  and open-weight release.

Node 17 needs the validated subject/mask prompts from 01 and prominence
requirements and prompt from 04, as well as the comparison design from 19.
These are completion prerequisites, not a requirement to wait before doing any
independent preparation.

Samples, comparison procedures, review coverage, treatment of unsuitable
annotations and acceptance decisions remain open. No generate–repair–train
workflow is prescribed. Those details belong to the evaluation workstream, not
to assumptions made by this release plan.

Completing bulk training data (07) also requires an agreed training volume,
informed by the fine-tuning pilot (06). Its evidence is an input to that decision;
this does not make completion of all of 06 a prerequisite for starting 07.
The September 27 target must be checked against the chosen volume and annotation
process. No model calls, experimental procedures or spending are authorized here.

## Hierarchy construction and service dependencies

Training-data generation uses subject descriptions to guide mask generation,
with prominence assessed for each mask in its note. The intended released
extractor instead takes a complete note and produces grouped source-text masks
plus prominence. It must discover subjects, but its output need not include
English subject descriptions. The plan does not require a separate
subject-generation call for each final-corpus note.

The shared hierarchy construction is masks → SSE vectors → flat HDBSCAN groups →
category descriptions → cosine-filtered candidate pairs → TRUE subsumption
checks → directed category hierarchy. Prominence supports note ordering. The
cosine cutoff and its implementation remain open. This describes the intended
build, not a claim that existing all-pairs experiments already implement
filtering. Fewer TRUE comparisons alone do not establish success: filtering
must preserve useful parent–child links.

The formal process also requires identical same-post masks to be deduplicated
before SSE, nodes with identical mask sets to be merged before hierarchy
generation, and parent–child navigation steps with identical complete post sets
to be collapsed before hierarchy publication. Retain strict mask-set subsets;
they can represent useful narrower categories. Preserve source references and
original node IDs. These rules do not decide semantic equivalence between
different mask sets. The
[required stages and their limits](../../sse_multivector/navigation-research-v1/README.md#required-hierarchy-processing-stages)
record the requirements; shared-child collapse and repeatable semantic-equivalence
decisions remain open implementation questions. This is not a claim that the
existing experimental pipeline implements all these stages end to end.

Recovering missing category memberships is a separate operation. HDBSCAN's raw
tree is not the specified launch hierarchy.

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
| **06 · Compare models to fine-tune** | Confirm permission to release fine-tuned weights before selecting the base model and committing to the larger training run. Training-data provider permissions remain in 17. |
| **08 · Fine-tune the model we'll release** | Prepare trained weights, necessary supporting files, usage instructions and evaluation results. Verify that the intended release files load and generate masks and prominence. |
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
- **22 · Measure SSE, category-title and TRUE processing costs:** use existing
  masks and categories to measure time, memory and cost for these three stages.
  This is ready independently of 21's HDBSCAN assessment. No measurement
  procedure, hardware choice or spending is approved here.
- **20 · Assess full hierarchy-build resources:** combine stage measurements
  from 22, HDBSCAN requirements from 21, mask/prominence generation measurements
  from the fine-tuning pilot (06), and mask/category/cosine-filtered-pair counts
  from the growing hierarchy builds (03). Estimate launch-build time, memory and
  cost to inform an affordable corpus size while preserving hierarchy quality.
  It stays grey pending inputs from 21 and 22. The dashed 06 and 03 inputs allow
  available evidence to be used without waiting for those workstreams to finish.
  Per-pair TRUE cost alone does not establish total hierarchy-build cost.
- **09 · Choose notes for launch hierarchy:** use the early measurements, agreed
  corpus scope and useful-coverage requirements to choose the intended corpus and
  freeze its IDs. Corpus size is not fixed before feasibility is investigated;
  the selected size still needs final validation.
- **10 · Check full-build time and cost:** establish whether our fine-tuned model
  can generate masks and prominence for the selected launch corpus, and the
  remaining pipeline can construct its full hierarchy, within the remaining
  budget and before October 18. This needs the trained model, corpus selection
  and resource measurements; early estimates alone do not establish feasibility.
- **11 · Test hierarchy with fine-tuned model:** build a sample hierarchy from
  that model's masks and prominence; check browsing and whether the complete
  pipeline works before processing the full launch corpus.

10 and 11 are distinct checks: whether the full launch build fits the budget
and deadline, and whether the fine-tuned model's outputs produce a useful
hierarchy. Both need evidence before 12; neither is required to finish before
the other. They may share measurements, but that does not merge their purposes
or require another planning decision. How they share work belongs to execution.

**18 · Prepare training code for the fine-tuning pilot** is ready within the
draft. Its scope is code to fine-tune each specified candidate model, save and
reload its trained weights, and generate outputs for evaluation. This preparation
does not require the final prominence definition or training-output format and
does not select a framework or training method.

Final training-example formatting and mask/prominence quality evaluation remain
within **06 · Compare models to fine-tune**, once the agreed output format,
prominence criteria and reviewed pilot data are available. Node 06 still depends
on 05 and 18; no extra node or new dependency is needed. Marking 18 ready does not
authorize implementation or pilot runs.

These are planning dependencies, not approval for measurements, model calls or
paid runs in this discussion. Measurement procedures, sample sizes, the cosine
cutoff, measured rates and counts, and the final corpus size remain open.

## Approved scheduling changes

1. Start the 200/300-note validation after the good 100-note hierarchy, while
   prominence is developed in parallel. Prominence is required to complete the
   combined 500-note validation, not to start every broader-corpus test.
2. Start scale measurements during Week 2. Measure the complete build, including
   SSE, HDBSCAN, category titles and cosine-filtered TRUE comparisons, rather
   than relying only on extractor training or generation speed. Node 22 measures
   SSE, category titles and TRUE using existing masks and categories, independently
   of 21's HDBSCAN assessment. Node 20 combines those findings with pilot-model
   measurements and growing-build counts as they become available. The combined
   assessment informs corpus selection in 09. Node 10
   then checks time and cost for fine-tuned mask/prominence generation and
   hierarchy construction across the intended launch corpus.
3. Bring protocol work and basic service/Notedeck integration forward, using a
   small saved hierarchy snapshot rather than waiting for the final corpus.
   Do not leave the first complete integration to Week 5; preserve time then
   for verification and fixes. Show this work as an explicit parallel track on
   the weekly diagram, alongside hierarchy/model development rather than mainly
   under Weeks 4–5. Service testing still needs the protocol and 100-note snapshot;
   Notedeck can start from the protocol and finish integration with the service.
   Launch still needs the final snapshot. The track adds no week assignments or
   dates; the earlier integration date remains open.
4. Include a separate annotation-model pilot before bulk training-data generation,
   alongside the fine-tuning pilot. Muse is the leading candidate to evaluate,
   not an approved production choice. Week 2 is the proposed window for both
   pilots; their exact schedules remain open.
5. Target **September 27, 2026** for training-data readiness: suitable masks and
   prominence data available for training, with training/evaluation separation.
   The volume, quality checks and handling of unsuitable annotations remain
   open; the target does not prescribe a correction workflow.

The October 18 deadline and release requirements are unchanged. Bulk training
data follows the 500-note validation and annotation-model selection. Starting
the final fine-tune requires both the selected model and sufficient reviewed
training data. September 27 is an agreed readiness target, not a demonstrated
completion forecast. Training-data volume and the time required to produce
suitable data remain unresolved. These timing decisions do not authorize work
to begin or establish that the full schedule fits.

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
- Annotation model, fine-tuning model, both pilots' details and final training-data volume.
- Annotation quality checks and treatment of unsuitable outputs.
- Scale-measurement procedures, measured rates and counts, and the cosine cutoff.
- Measured costs and budget allocations; rented-host capacity and confirmed duration.
- Detailed task ownership and a feasible calendar within the proposed five-week sequence.

The diagram's page 2 incorporates these approved scheduling changes into the
weekly targets. Other targets remain provisional until their dependencies,
durations and owners are settled.
