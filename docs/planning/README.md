# Release-plan task graph

[Release decisions and open questions](release-decisions.md) records the planning
discussion, including corpus scope, validation, Vast.ai compute and rented hosting.
[Scalability findings and decisions](scalability.md) records the separate
read-only investigation, the low-memory HDBSCAN discussion and unapproved next steps.

[Fine-tuning pilot process](fine-tuning-pilot-process.md) describes the experiment:
shared data, untuned baselines, three continuing student training runs with
one complete pass through subject-hierarchy training examples, checkpoints at
200, 400, 600, 800, and 1,000 training notes, and model comparison.
The larger pilot is subjects only, approved October 2: one teacher hierarchy
per training note and no mask generation. Each checkpoint generates its own
subject hierarchies on the same held-out validation notes. Thinking stays off
throughout preparation, training, baselines, checkpoints and the final test.
**Pilot status — October 8:** all three students completed training through
1,000 notes. Qwen's response collection is complete; dense Gemma and Gemma MoE
are still collecting evaluation responses. Pilot training data is complete;
model selection is in progress, not accepted. The pilot-specific label teacher
was approved independently of the still-open release teacher selection.
Semantic review happens outside the GPU rental. The agreed reviewer is
GPT-6.1 Sol / xhigh; [DSRv1](../../sse_multivector/distillation-review-v1/README.md)
drafts its prompt, report format and qualification cases. October 8 qualification
completed with 28 complete reports and one interrupted report, failing known
semantic and cross-version checks. Subsequent runs use the user-directed
concurrency 8 with existing backoff. Bulk review has not run.
Source preparation, report checks and scoring
are implemented offline; DSRv1 includes a concrete preview before model calls.
Its 29 cases include eight large training hierarchies selected by entry count
and answer length from the 1,300 saved ASv6.100 generations.
The user subsequently authorized the [DSRv2 offline preview](../../sse_multivector/distillation-review-v1/README.md#dsrv2-draft-and-offline-preview):
worked-example authority is explicit, and Q20–Q22 share provisional fixed
meaning groups. The user then authorized DSRv2 qualification: the trusted URL
control passes `8/8` correctness and `2/2` coverage. The small set finishes with
17 passes, Q14's semantic regression and Q01's ungraded stream interruption.
The large trial at concurrency 8 completes four of eight unchanged hierarchies
and both controlled variants, with four ungraded stream interruptions. Both
variants change judgments about untouched links and placements despite fixed
groups and required flags. DSRv2 qualification has failed; adoption remains
open and bulk review has not run.
The user next authorized a [matching-only offline preview](../../sse_multivector/distillation-review-v1/README.md#matching-only-offline-preview)
before calls: one generated subject against its fixed teacher list, with
authored expectations outside the prompt and separate-note confirmation
controls. The subsequent authorized DSMv1 development trial passes all 16
controls on their first attempt with Sol / xhigh and concurrency 8. The user
then accepted the unchanged 16-control confirmation run, which also passes
16/16 on first attempts. Both sets pass 32/32 distinct authored controls. A
subsequently authorized independent confirmation repeat passes 16/16 with
unchanged verdicts and no saved-answer reuse. The authorized
[actual-wording offline preview](../../sse_multivector/distillation-review-v1/README.md#actual-distilled-wording-offline-preview-october-8)
prepares 22 distinct validation inputs with zero calls: eight assessed matches,
thirteen assessed nonmatches and one unresolved case after the accepted
`Fakery` assessment. Expected answers still
need independent verification. Actual distilled-output reliability remains
untested. DSMv1
has not replaced the full review process. See the
[repeat results](../../sse_multivector/distillation-review-v1/README.md#dsmv1-independent-confirmation-repeat-october-8).
The user accepted adding the original post to clarify existing wording while
forbidding it from supplying missing restrictions. The
[DSMv2 draft](../../sse_multivector/distillation-review-v1/README.md#dsmv2-post-interpretation-draft-october-8)
prepares the same 22 targets with zero reviewer calls. The authorized offline club assessment
sets R19's expected match to T06 for DSMv2; it remains unverified.
DSMv1's context-free expectation remains unresolved.
The subsequent offline self-custody check retains R16's expected nonmatch:
Bitcoin remains a missing asset restriction. The authorized
[two-case DSMv2 trial](../../sse_multivector/distillation-review-v1/README.md#dsmv2-two-case-post-interpretation-trial-october-8)
now returns T06 for the club case and null for self-custody, agreeing with both
expectations. These two fresh Sol / xhigh calls do not establish general
reliability. The authorized
[remaining post checks](../../sse_multivector/distillation-review-v1/README.md#dsmv2-remaining-post-visible-expectations-october-8)
retain all 20 expected verdicts and clarify their recorded reasons, with no new
reviewer calls. All 22 expectations remain agent assessments requiring independent
verification; broader qualification is pending.
The subsequent authorized
[20-case DSMv2 trial](../../sse_multivector/distillation-review-v1/README.md#dsmv2-remaining-20-case-trial-october-8)
returns 20 valid reports: nineteen agree with the recorded expectations, while
R05 matches `Fakery` to `Inauthenticity` despite expected null. Agent review marks
that disagreement uncertain pending adjudication. One provider-overload retry
succeeds; no answers are reused. Prompts and expectations are preserved.
The authorized [eight action/property controls](../../sse_multivector/distillation-review-v1/README.md#dsmv2-actionproperty-controls-october-8)
also pass with unchanged DSMv2 / Sol / xhigh and concurrency 8. Their explicit
wording and smaller catalogs leave R05's disputed verdict and broader
qualification unresolved.
Freeze prep and pilot stages
locally, then continue on the same rental with fresh pilot adapters only after
prep checks pass. The October 3 separate preparation passed on older inputs;
its hardware evidence does not cover the longer ASv6.100 data. The paired mode
checks complete training, reload/merge/restore, brief subject generation, full
validation cache shapes and actual fused/native loss agreement. Rehearse this
package locally before booking. All three ASv6.100 CUDA preps passed October 6,
as recorded below.
The primary comparison uses all three final 1,000-note adapters and their
untuned baselines on 200 reserved test notes: 1,200 responses collected during
the main rental and kept sealed through local validation review. Earlier
checkpoints show learning progress. Test collection and completeness checks are
verified in the local VM; automatic reports exclude test answers and semantic scores.
The October 5 final audit added recorded continuation on the existing rental,
fresh retrieval after recovery, early provenance/receipt copies and bounded
copier retries. Mechanical progress and GPU/memory/disk observations are saved
locally. Older attempts and reviews cannot authorize deletion of newer work.
Minimize preparation's total billed cost, approved October 3. Collect pilot
timing estimates during those same checks; keep parser/recovery testing local.
Use two 96GB RTX PRO 6000 cards, with a complete model on each. Gemma dense
runs on GPU 0; Qwen followed by Gemma MoE runs on GPU 1. The earlier separate
preparation was approved for $5 on October 3; its image was published and
verified private. A refreshed compatible 600 W quote is $1.4522/hour,
with $4.41 planned for three hours including transfer allowances, within the
approved $5. The $7 request is withdrawn. Its first creation request was rejected
with HTTP 400; complete inventory recovery confirmed no instance and no charge.  The specific provider explanation was not retained. That rejected creation ran no GPU checks. The user approved revised selection filters and proceeding
within $5. A better refreshed 96GB/600 W quote is offer [private ID removed] on machine
[private ID removed] at $1.4656/hour, or $4.40 for three planned hours including transfers.
The unchanged private image and native package use a new frozen operation. All 125 available work files and six startup files were reverified before the run ended on October 3.
 Qwen completed both updates,
20 brief responses and four cache checks; Gemma dense has its first checkpoint,
and MoE did not start. The local per-layer dimension fix is committed and its
rebuilt VM passes all 56 tests. Reuse was approved, then cancelled by the deletion
instruction before implementation. This attempt left the Gemma checks incomplete; the repaired run below completed them.
Preliminary charges were $1.56.
For prep rentals, repair straightforward failures immediately. If recovery needs
substantial work, preserve and verify the available data, then delete under the
user's standing approval; completion of all prep checks is not required.
The full pilot still requires complete, verified local data or explicit user
approval before stopping incomplete work. No automatic timeout or deletion.
**GPU preparation completed October 3:** all three students passed the measured
training, checkpoint restoration, merge and generation/cache checks on the
96GB card. Qwen evidence was reused; the repaired Gemma rental lasted 65.5 minutes.
All 210 work files and six startup files were verified.  The two preparation runs cost $1.620 and $1.756, $3.376 combined. 
The shared launcher now selects the provider SSH proxy by default and prioritizes
saved responses before checkpoints. Completion markers follow their files.
Checkpoint streams are limited to 64 MiB, with new response discovery between
streams. Future data must fit measured bounds.

Subject evaluation batching is implemented: each batch's size follows token
lengths and a frozen per-GPU memory budget, with separate saved raw/parsed
answers. Subjects-only training now continues through retained checkpoints,
with disposable merged evaluation and full training-state restoration. The
preparation now supplies measured cache bounds for the old ASv6.48 inputs.
The user froze full ASv6.100 for the pilot on October 4, including all worked
examples in training and every evaluation. The October 5 audit of all 1,300
teacher labels finds training sequences up to 18,114 Qwen / 18,396 Gemma tokens.
The old 8K context, 4K output and 128-node limits do not cover this dataset.
The old memory rule also rejects Qwen and dense Gemma even at batch size one;
these are planner estimates, not observed GPU failures. The new subjects-only
candidates use 20,480-token context / 10,240-token output, with no node-count
cap. The worker enforces efficient SDPA and uses training-only Liger fused loss.
Pinned-container integration and SSH checks passed locally. Actual ASv6.100
CUDA execution and fit passed October 6; baseline throughput is being measured.
The combined prep→pilot
two-GPU input package is frozen and matches the rebuilt VM, which passed
91 tests with one optional native-tokenizer check skipped. The 149 controller
regressions passed, including both GPUs' identified utilization/memory observations. All six
pilot/prep configurations and their data are byte-identical to the passed native
preflights. A saved two-card 96GB/600 W RTX PRO 6000 Server quote is $2.99/hour
including 300 GB storage. Conditional arithmetic projects 40–66 hours / $122–197,
with a slower 80-hour / $239 sensitivity case. Older workstation timings are
proxies; actual server-card throughput remains unmeasured. The draft allows
200 GB inbound and 60 GB outbound. The user approved private image publication
and a **$285 combined prep→pilot budget** on October 5. The exact tested image is published and verified private.
The preparation completed only Qwen prep; dense Gemma exceeded the cache memory guard and Gemma MoE failed gradient agreement. The prep gate blocked all
main baselines and training. All 86 available files (4.35 GB), saved checkpoints and failure logs were retrieved and independently rehashed.
Preliminary charges were **$1.974**. Local repairs
preserve
failed measurements and align Gemma's numerical reference with Liger's FP32
softcap. Dense inference reserves 12 GiB scratch under the same 88 GiB budget.
94 VM tests and six native tokenizer preflights pass; one VM tokenizer test is
skipped and covered separately. The corrected VM export is published and verified
private. A replacement failed before SSH or experiment work because container DNS failed. Startup diagnostics were saved and hashed. Its preliminary cost was **$0.76**, bringing the two failed attempts to **$2.74**. Both attempts failed.  A different compatible host
quotes $2.9389/hour.

Native preparation passed. The two-GPU preparation used a $2.9389/hour configuration and was observed through startup, prep and retrieval; no pilot work started. Machine
146170 is excluded. A local $1 setup gate refused worker admission after
successful startup/input verification because it counted the full planned
transfer allowance. A $5 local setup allowance resumed attempt 001 without changing remote code, inputs or the model recipe. Qwen prep passed; dense completed both updates but was
wrongly rejected at **88.43 GiB** against the **88 GiB inference budget**, without
CUDA OOM. MoE failed native gradient agreement before its first update. All **101 available files / 5.85 GB** were independently verified. Preliminary charges were **$2.543**.
The local fix removes the training cutoff and preserves
inference checks; 73 local tests passed, 12 VM-only checks were skipped. The
MoE reference now applies token weighting after LM-head backward, matching
Liger’s BF16 rounding order; its local regression passes without relaxing
tolerances. The local workflow suite passes 89 tests; 12 VM-only checks are
skipped. Full CUDA confirmation remains pending; the runtime is rebuilt below.
Persistent-volume mounting and verified replacement are implemented locally.
A controller-crash regression proves that live children block result sealing;
replacement preserves work paths and requires the same image/data/recipe,
verified retrieval and prior instance deletion. A changed runtime keeps downloads
but archives prior work and starts fresh. The rebuilt VM passes 101 checks,
including actual container replacement, unchanged saved answers/checkpoints and
an offline cache hit. The frozen package matches this runtime and all six
previous configurations/data. Full MoE CUDA confirmation remains pending.
The storage rate was $0.0833/hour. Both download create requests were rejected before allocation, with no GPU charge.
The retry revealed an invalid mount path. Use `/workspace`, retaining experiment
paths beneath it. Local CLI/controller/cache/workload checks pass; the updated
VM rehearsal passed 109 checks; the private image and unchanged packages pass
native prepare. The quoted download-only rate was $1.4278/hour including storage. The download completed: all **42 files / 169.8 GB** were checksum verified on the volume, and all completion evidence was verified locally. 
The preliminary download-stage cost was $0.455. No baseline/training yet. Slow image
startup now stays pending
and retries on the same instance; 176 local tests succeed (three VM-only skips).
The updated VM passes 109 checks and stops cleanly; the rebuilt private image
and both unchanged-input packages verify against it. Read-only pull succeeds
and anonymous access is rejected. Deleted-rental accounting now releases unused
run budgets immediately after verified deletion, retaining only bounded unbooked
charges. It releases $848.37 and keeps $2.63 pending; actual spend is $68.50.
 Full concurrent CUDA/MoE confirmation
remains pending.
  Repeat the tested one-GPU download stage, then attach its verified cache to the two-GPU prep/pilot.
The download cache held all **42 files / 169.8 GB**, checksum verified. The download completed successfully; local completeness review verified the retrieved evidence.
Its preliminary bill is $1.22, with 28 cents retained under the $1.50 bound.
The two-GPU run passed cache attachment and offline verification. Qwen and
Gemma dense passed full CUDA prep; Gemma MoE still failed gradient agreement.
**No pilot baseline or training started.** All **97 work files / 5.85 GB** and six preparation files were retrieved and independently rehashed. Preliminary charges were **$1.445**.
 The one-GPU diagnostic completed both cases without training updates. All **20 files / 3.17 MB**, including all four saved head-state/gradient pairs, were retrieved, independently rehashed and opened.  The preliminary diagnostic cost was **$0.21**.
 Head relative L2 error is **0.294–0.321%** with identical inputs;
296 of 156,119,040 adapter-gradient elements fail pointwise tolerance after
backpropagation. Disabling reduced-precision reductions improves head agreement
but does not resolve the deep comparison. A locally tested reference correction
checks head gradients separately, then compares native/fused adapter gradients
using the identical incoming head gradient. It adds a relative L2 check using
the existing rtol, so absolute tolerance cannot hide corrupted tiny gradients.
Both new production-path regressions failed before repair and pass afterward;
all five fused-loss tests pass. Full VM validation now passes: 10 candidate,
46 workflow, 48 deployment, four cache and four explicit replacement/handoff
checks; all four deployment skips are covered separately. Candidate tokenizer
preflight uses verified offline metadata. Caching reuses passed stages; the exact
VM export and refreshed package are published privately and verified, at image
digest `afa90bc64233b227da5db36f1336d7395138d9528bfb8c0d3a7dadc5f7256bad`.
All three actual CUDA loss/head/adapter-gradient checks now pass, with zero
backbone-gradient differences using the verified identical head gradient.
The preparation passed Qwen and dense Gemma full prep. MoE stopped on its
seven-note native generation-cache probe: **88.080 GiB reserved versus 88 GiB
budget**, without OOM. **No pilot baseline or training started.** All **116 work files / 6.82 GB**, six preparation files, five sealed checkpoints and the three gradient-check reports were retrieved, independently rehashed and reviewed.  Preliminary charges were **$1.361**.  The corrected two-GPU configuration cost **$2.8139/hour**. Only MoE inference workspace changes **4 → 12 GiB**, consistently
in prep and pilot; total inference budget stays 88 GiB and the widest predicted
batch falls **seven → five**. Exact image, code, prompts, data, models and
training recipe are unchanged. Package verification and native preparation pass.
The replacement passed all three full CUDA preps and started baselines in the same run. The widest real cache probes reserve **76.28 GiB Qwen
(seven notes), 77.07 GiB dense Gemma (one), and 76.80 GiB MoE (five)**, all below
88 GiB. Loss/gradient checks, merge/generation, long-input updates and saved
continuation checks pass for every student. No pilot training starts until
all three baselines pass. Observe continuously and progressively retrieve
frozen responses/checkpoints. Archive all verified prior work and retain the
model cache. No automatic stop or deletion. Evidence:
`target/distillation-pilot-v1/main-pilot-loss-boundary-20261006/` and
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/`.

**Baseline integrity, October 7 00:07 UTC:** Qwen and dense Gemma's 100-note
validation baselines are retrieved and verified locally: hashes, full inputs,
raw/parsed answers and batch receipts agree. Qwen's 13 and Gemma's two invalid
answers remain counted. Both 200-note test collections are underway and sealed.
MoE is queued; no main training has started. Receipts:
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/qwen-validation-baseline-integrity.json` and
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/gemma-dense-validation-baseline-integrity.json`.

**Qwen and dense Gemma baselines complete, October 7 05:36 UTC:** each
student has 100 validation and 200 reserved test responses verified locally by
the production checks. Full prompts, raw/parsed answers, batch receipts and
checksums agree. Reserved test content and quality remain unreviewed. MoE is
starting its baseline; no main training has started. Receipts:
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/qwen-reserved-baseline-integrity.json` and
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/gemma-dense-reserved-baseline-integrity.json`.

**All baselines verified, October 7 08:23 UTC:** each student has 100 validation
and 200 reserved test responses retrieved and checked locally by the production
validators. Prompts, raw/parsed answers, batch receipts and hashes agree; all invalid
answers remain counted. Reserved test semantics remain unreviewed. The pipeline
advanced to Qwen and dense Gemma training concurrently; MoE follows Qwen. Receipts:
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/gemma-moe-validation-baseline-integrity.json` and
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/gemma-moe-reserved-baseline-integrity.json`.

**Training progress verified, October 7 13:58 UTC:** Qwen has completed
400 distinct notes in 50 continuing updates; dense Gemma has completed 200 notes
in 25 updates. All three saved checkpoints, including adapter and optimizer/RNG
state, are local and passed hashes, exact note coverage and counter checks.
Qwen's two training blocks took 34.9 and 33.2 minutes; dense Gemma's first took
92.9 minutes. Both Qwen validation sets are fully retrieved and verified against
the same 100 inputs and batch plan as baseline. Each has 2 parsing failures,
versus 13 untuned; the two failures at 400 notes hit the output limit. Generation
took 121.4 and 143.1 minutes, versus 128.1 untuned. Semantic correctness/coverage
remain ungraded. Qwen continued training toward 600 notes; dense Gemma is
validating after 200 and MoE remains queued. Reserved test semantics remain
unreviewed. Receipts:
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/qwen-checkpoint-400-integrity.json`,
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/gemma-dense-checkpoint-200-integrity.json`,
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/qwen-checkpoint-200-validation-integrity.json` and
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/qwen-checkpoint-400-validation-integrity.json`.


Preliminary backup storage charges were **$0.884**.   
No automatic stop or deletion.
The approved one-card stage verified actual attachment and downloaded all three
pinned models. Reattach the retained volume for offline verification and full
concurrent prep on two cards. Missing/corrupt files block every worker before
prep. The full handoff passes in the VM, including verified local retrieval,
container replacement and two-worker prep→pilot. Both packages preserve all six
configurations and data. Current runtime/publication evidence:
`target/distillation-pilot-v1/startup-retry-20261006/`; actual download evidence:
`target/distillation-pilot-v1/download-launch-20261006-v3/`.
The user reconfirmed one main rental with two GPUs on October 6 after comparing
separate rentals; keep the tested deployment and shared prep/baseline checks.
Paired prep/pilot execution and completeness checks are implemented locally:
all three baselines precede training; raw/parsed answers reconcile with receipts;
local verification accounts for all checkpoint comparisons before deletion review.
The user approved autonomous pilot error repair, including necessary code/recipe
corrections: preserve evidence, record changes, restore saved state and rerun
affected comparisons. Complete-data deletion and spending rules still apply.
Prep covers the longest example and validation/reserved-test input cache shapes,
with actual CUDA loss/gradient agreement required on hardware. Semantic grading remains local.
The historical winner-only ASv6.48 projection of 36–40 hours / $51–58 does not
price the frozen pilot or the now-approved six-version test collection.
Pilot data selection and label generation are approved: **1,000 train / 100
validation / 200 final test**, extending the existing fresh-corpus random draw
with hierarchy input exclusions and author/copy protections. Full ASv6.100
teacher labels use **GPT-6.1 Sol / medium** through the subscription runner at
**32 concurrent calls**, reducing to 24 if needed. Selection and generation are
authorized. The 1,300-note selection and three splits are frozen; original texts,
lengths and author/development exposure checks passed. All **1,300 teacher labels**
are saved and structurally verified: 1,000 train / 100 validation / 200 final test.
The approved completion over SSE transport at 24 concurrency passed without
failures; original answers and receipts are preserved. See the [pilot process](fine-tuning-pilot-process.md#1-freeze-shared-inputs--locally).
The background copier transfers completed responses
and checkpoints, verifies local copies and reuses them during final retrieval.

`release-plan.json` is the current task-and-dependency source for the focused
graph. Agents update it from explicitly approved planning changes; the user
does not need to edit it. Each task has a two-digit `id`, `title`, `status`,
`track`, and plain-text `description`. Links run from prerequisite `source` to
dependent `target`, with `kind` set to `required` (needed to finish) or `helpful` (an
input that does not block finishing); `label` is optional. The browser rejects
missing endpoints, duplicate IDs or links, and unknown statuses, tracks or
link kinds.
The written decision record remains the source for requirements, rationale,
approvals, and open questions. Task readiness is not authorization to begin.

The September 28 [release-shape revision](release-decisions.md#release-shape-revision--september-28-2026)
re-cut the deliverables: the release is the only must-deliver package — a
fully automated snapshot with code and tested local serving
instructions. The open-weight model is the nice-to-have model track, and
operating the service is an optional demo. Task texts and statuses reflect
that revision.

The October 8 corpus-size revision makes 2–5k notes a target, not a hard minimum.
Ship the largest genuinely useful hierarchy that passes the user's review by
October 18, without relaxing quality or automation. Exact size remains open;
the existing validation milestones are unchanged.

The October 8 publication clarification leaves two distribution options:
publish hierarchy events to a paid relay or put them in an online ZIP. Choose
after reviewing hierarchy quality; Notedeck integration remains required with
either route. No publication or spending is authorized by this planning choice.

Task 03 covers validation at 200 / 300 / 500 notes and the ~1–2k-note user-review
rung. Task 12 alone owns the final teacher-labeled, fully automated release build
and its user browsing review. Completion of 03 does not accept the release
snapshot; 12 requires the user's acceptance of that final snapshot.
Task 28 supplies the validated launch-scale implementation and is required to
complete 12; it does not own a separate release snapshot or select a workflow.
Corpus and Notedeck preparation started September 30. The earlier frontier-based
200-note candidate became cycle-free without establishing browsing quality.
The subsequent sequential run exhausted its allowance before broader placement
finished and did not meet the quality goal. Equivalence-aware reuse is now
implemented in its worktree; relationship-prompt testing and saved-run checks
continue. No complete hierarchy is accepted.
ASv6.100 is the approved subject baseline after diverse-input testing, with
measured omissions and relationship errors still reported. Its designation
does not clear the broader-generation hold or select a production workflow.
The Notedeck browser UI is approved and committed; task 15 waits
for protocol agreement and service implementation before integration.
The reviewed-100-note prerequisite for the planned validation ladder remains open.

On October 1, the user is undertaking prompt stress-testing. Shared task 30,
**Stress-test prompts**, is in progress and blocks new generation for broader
corpus inputs in 03. Corpus selection and offline preparation may continue;
completed prompt-development task 01 remains complete. Task 03 stays in progress
for corpus preparation and experimental 200-note construction using saved outputs.
The experiment retains saved outputs from 100 food/drink and 100 music notes
with their original provenance; it has not been regenerated with ASv6.100.
It does not establish acceptance of the validation ladder or freeze the release corpus.
Stress-testing completion does not authorize generation calls.

Whether HDBSCAN will be used remains open (September 29 clarification).
Task 21 is required only if the chosen workflow uses it. Its links to 20 and 28
are helpful while the choice is open; make them required if HDBSCAN is selected.
The chosen workflow's time and cost checks remain required. No algorithm is
selected by this tracking change.

Task 24's membership-recovery work waits for the workflow choice and is needed
only if HDBSCAN is used. Its link to 03 is helpful while the choice is open;
make it required if HDBSCAN is selected. Relevant-content coverage remains part
of 03's required validation for whichever workflow is used.

Task 23's completed title-prompt work is required for 02 only if the chosen
workflow uses separate node-title generation. Its link to 02 is helpful while
that choice is open; make it required if that stage is used. This does not
select a workflow or reopen the completed HR02 title work.

Task 25 remains complete for HR02. Its links to 02 and 03 have been removed:
the earlier exact-mask-set and TRUE-cycle rules do not gate the newer hierarchy.
Current merging and conflict decisions remain within 02; no replacement policy
is selected by this tracking change.

Task 26's earlier equal-note navigation collapse remains validation pending;
its link to 03 has been removed. Any reuse in the newer hierarchy needs an
explicit decision within 02. Understandable choices, meaningful narrowing and
relevant-content coverage remain required in 03, without mandating that rule.

Task 04 defines and validates one sorting score per note within a hierarchy
node; task 27 implements and validates ordering using that definition. Both
are paused as nice-to-have work, as directed October 5. Node sorting no longer
blocks broader hierarchy validation, teacher selection or pilot training data.
The 04 → 27 dependency remains within that optional effort; 27 → 03 is helpful,
not required. The proposed ranking of hierarchy work and the SP pilot was
explicitly clarified as tentative, not fixed. The pilot informs later
fine-tuning; SHR fine-tuning still needs validation in a generated hierarchy.
The October 2 finite audit froze the experimental PPv35-post-meaning-v1 method
for a browsing build: full-post prominence against a fixed saved node
meaning, multiplied by SP subject-plus-context relevance to the existing title;
a post takes its highest related entry sorting score. Retain SSE's final learned
layers. The earlier 11 clear Coffee/Eggs/Music preferences, Photography's
three-post order, accepted seven-post Eggs order and four permitted about-equal
Coffee swaps remain separate reference evidence, not general accuracy claims.

Two agent-reviewed passes across twelve meanings and 101 diagnostic post/node
assignments from 62 fresh-to-sorting posts found no substantial recurring
browsing failure. Isolated mistakes and close/mixed swaps are acceptable;
percentages and exact neighboring orders need not repeat. Stop prompt and
architecture search, reopening only for a concrete substantial recurring
browsing failure. Smaller cohorts, music-heavy coverage and meaning boundaries
limit generalization claims. Production implementation, actual hierarchy
browsing and any additional teacher/model outputs remain open, but are deferred.
The candidate and evidence are preserved, not mandated for the next build. See
[the stopping rule and result](release-decisions.md) and
[the native evidence](../../sse_multivector/model-runner.md).

Teacher comparison (17) remains in progress. Sol low is provisionally favored
for subject generation after assessment on 20 posts. The user also provisionally
favors GPT-6.1 Sol medium for grouped masks: one call for all subjects in a post.
Sol xhigh grouped masks were assessed on 20 posts (684 masks), using saved Astra
subjects. Agent reviews found broadly comparable quality to Astra, with minor
omissions and unresolved cases; they do not establish corpus-wide parity or
select teachers. The combined
Sol subject-and-mask process and resulting hierarchy comparison remain
unvalidated. Subscription quota use is unmeasured; final teacher selection
stays open. Final teacher selection waits for prompt stress-testing
(30), with evidence for the prompts we will actually use. Comparison work may
continue; any rechecking belongs to that workstream.

Task 22 measures SSE and the construction stages used in the chosen workflow.
Separate node-title generation, its input-growth measurements and the
corresponding large-input work in 28 are required only if that stage is used.
LG01 retains SP subject names; no production workflow is selected by this change.

Task 20 keeps separate estimates: teacher generation plus construction for the
required release, and pilot/distilled-model generation for the optional model
track. Shared construction measurements can inform both where applicable.
Model-track measurements do not block completing the release estimate. Checks
10 and 11 belong to the model track; neither blocks the teacher-built snapshot.

Task 02 tracks acceptance of a useful 100-note hierarchy. Planning centers on
the compare-prompt hierarchy builder; vector work remains a parallel experiment,
not a prerequisite or an equally expected release path. The builder's completed
nine-note menu has bounded choices and strictly narrowing note sets; semantic
contradictions and meaningful-group coverage remain unresolved. A fresh nine-note
construction has completed root placement and is testing deeper placements.
The vector investigation has run model fits without qualifying transfer. Its latest
213-note browsing prototype covers all notes with at most six choices per
step, but agent review finds misleading labels and missed requests. Neither
trial passes user acceptance. Older builds remain historical evidence;
the current results and limitations are linked in
[the decision record](release-decisions.md). Neither construction approach is
selected or accepted; release tracks and dependencies are unchanged.

The earlier
[bounded build](../../sse_multivector/bounded-hierarchy-v1/README.md#completed-build-and-browser-handoff)
completed three scheduled passes on September 30, with 522 new model attempts
and two exact-request reuses. Its final browsing export contains 1,651 hierarchy
nodes and 220 roots, retaining all 100 posts, 2,383 original subject entries and
1,674 masks. Mechanical completion does not establish browsing quality.

Some original subject links make unrelated posts reachable beneath specific
recipes after nodes are combined. Remaining roots and duplicate branches also
need review. The October 1 six-link diagnostic rejected both problematic risotto
links and accepted four valid controls, matching agent expectations; this is
not corpus-wide validation. The bounded build's full original-link check is
prepared only: 1,755 comparisons in 110 batches, all unrun. No filtering or
construction-policy change is selected by this status update, and further
inference needs separate authorization.

Task 02 stays in progress until the user accepts a useful 100-note hierarchy,
not finished launch-scale construction. Track, dependencies and production
workflow choices are unchanged. The original LG01 hierarchy and earlier
HR02/Astra tests remain preserved as evidence; task 25 stays complete for HR02.

Task 18 is complete for the preliminary experiment's setup. The rebuilt image
is published and verified; local VM rehearsals cover all three candidate families.
This does not verify the newer larger-pilot worker or configuration. Further
larger-run preparation remains within 06.

Task 29 tracks the preliminary 100-note fine-tuning experiment in progress. Its
replacement GPU run completed all three baseline attempts, 128-step training runs,
matching adapter reloads and trained evaluations. Results were hash-verified locally. The user requested accepting Markdown
JSON fences to recover the Gemma baselines. The parser now accepts them for
subjects and masks; all 40 saved Gemma subject answers validate, but their 618
baseline masks still need generation. Reparsed Qwen teacher-agreement F1 is
0.344 before and 0.346 after training. Semantic review remains pending; this does not complete candidate-quality review in 29 or model selection in the larger pilot, 06. That larger pilot remains waiting for its data and
includes a comparison trained on 1,000 notes, approved September 30. Its approved
starting recipe uses 8 subject examples per update total across GPUs, constant learning
rate 0.0001 with no warmup, and LoRA rank 16 / alpha 32 for ordinary adapters.
One pass through 1,000 notes now requires 125 updates per student.
Gemma MoE also receives rank 2 / alpha 32 routed-expert adapters with original
model and router weights frozen. Training loss averages all teacher-answer and
native turn-ending tokens per update, without extra task weighting. Numerical
settings retain AdamW defaults with no weight decay and clipping 1, an unquantized
BF16 base/mixed computation and FP32 adapter/optimizer state, plus LoRA dropout 0,
frozen biases and standard initialization. Each milestone retains a complete
training checkpoint, evaluates a disposable BF16 base with the saved adapter
baked in, then restores the full training state. Answer-only training and
every evaluation use thinking off. Pilot data is frozen; final-test collection
is implemented locally. Scoring and hardware execution remain open; see the
[pilot process](fine-tuning-pilot-process.md).

Task 13 remains in progress. The [protocol draft](../recommendation-engine/design/hierarchy-serving-protocol-decisions.md)
now covers opening a hierarchy, node events, note lists and indexes. Proposals
remain under review; service implementation and client integration await
agreement. The Notedeck browser UI is approved and committed; task 15 is waiting
for service integration. Dependencies are unchanged; no protocol design is
selected by this planning update.

The user confirmed separate GPU preparation in principle October 3 because the
pilot data is not ready. Existing notes can exercise the hardware workflow;
they cannot certify the lengths or completeness of future pilot answers.
The local package and VM rehearsal are ready. Its exact cases and memory
allowances are a concrete proposal; rental approval remains open. No compatible
low-transfer offer met the proposed $5 cap in the latest October 3 search.
The larger pilot data is frozen and packaged. Final-test collection on the main
rental is approved and implemented locally. Private publication and a $285
combined rental budget are approved; actual hardware fit/timing remains pending.

The task graph is the only release-plan viewer. The root URL opens it; the
obsolete draw.io diagram, viewer and renderer have been removed. Earlier
versions remain recoverable from Git, not as a competing planning view.

## Focused task graph

The track selector defaults to **Required release**. **Optional model** shows the
distillation work; **Both** includes the entire plan. Tasks marked **Shared**
appear in both track views as the same task, not duplicate records. Earlier
cycle/navigation experiments are marked **Historical experiment** and remain
accessible in Both, without becoming current prerequisites.

Each node shows its task title prominently above a divider. The track and any
hidden-link count sit below it in a smaller, muted footer, not in the title.

The `track` field is `release`, `model`, `shared`, or `historical`. It describes
which views include the task, not its readiness or dependency strength. Shared
HDBSCAN and separate-title work remains conditional on the chosen workflow.
Statuses, arrows, task scope and open method choices are unchanged.

Track selection filters the task picker and graph, including step expansion
and the all-matching view. It preserves the steps, direction and helpful-input
settings and composes with completed-task filtering. The details panel still
lists every direct link and labels tasks outside the selected track. Following
one switches to its track; Previous task restores the prior task and track.

Open [the planning root](index.html) on the tailnet host for the
read-only dependency view. It loads `release-plan.json` on every visit and
arranges the graph automatically. It does not change the draft plan.

ELK calculates both task positions and orthogonal connection routes. The viewer
uses those routes and attachment points so arrows entering a task remain
separate. Refocusing or changing filters recalculates the visible graph; no
task-specific coordinates are stored in the plan.

The graph initially focuses on task 02. Choose another task or click a
node to refocus. Show zero to three steps in either or both directions, or
show all tasks. A `+N other links` label means the node has arrows not drawn in
the current view. The right panel always lists the selected task's direct links,
including those outside the view. Solid arrows mean prerequisites for finishing;
dashed arrows mean helpful inputs. Start conditions remain in task descriptions
because task links do not encode them separately. No user choice
or approval is inferred from a task's status.

The browser uses local copies of Cytoscape.js 3.34.3 and ELK.js 0.12.0;
no external service or build step is needed. The bundles come from their
npm source tarballs:
[Cytoscape.js](https://registry.npmjs.org/cytoscape/-/cytoscape-3.34.3.tgz),
[ELK.js](https://registry.npmjs.org/elkjs/-/elkjs-0.12.0.tgz).
Their licenses are retained in `vendor/`.
SHA-256 (in that order):

```text
5f3b5b529546d5af1fc5628590af033b74511a5b6f789f5f4682845863228b91  cytoscape.min.js
1222e44f953ce7746af23801e723708f8e6f436b8b377a6a5fc7552f34a307b3  elk.bundled.js
```

## Planning conventions

Each task's title and description must identify the work and intended result
without tracing arrows. Name the model's role—teachers or the distilled model—
rather than saying only “the model.” Arrows explain prerequisites; they should
not supply a task's missing meaning.

Keep descriptions to short summaries of the outcome, current state and real
blockers or start conditions. Experiment counts, model settings, run histories
and detailed findings belong in linked workstream records, not the task UI.
Shortening a summary must not change the task's scope, status, dependencies or
approval. Do not repeat status or dependency information already clear in the
view unless a start condition or conditional requirement needs explanation.

Only add approved decisions to the task data and views. Permission to
investigate or draft a proposal does not approve its contents. Keep proposals
in the written plan until the user explicitly approves them for the graph.
The overall plan remains unapproved; approving a card or wording change does
not approve the full plan. Task readiness is not authorization to research,
implement, assign agents or spend.

Green means ready to start or resume, blue means in progress, grey means waiting,
and muted grey means complete. If preparation can start but later work cannot,
show them as separate tasks linked by a dependency.

## Earlier diagram-tooling investigation — September 20, 2026

The September 20 decision kept draw.io while no replacement had been selected.
The later focused graph now uses Cytoscape and ELK with JSON task data. The
findings below explain why other renderers were not selected at that point;
they do not describe the current graph's data source.

Retain these findings for a future upgrade:

- Standard Mermaid 12.0.0 with bundled ELK passed six layout cases without a
  renderer patch, preserving text, statuses and dependencies. Repeated SVGs were
  identical with fixed inputs and environment. Global wrapping and label-background
  settings were sufficient, but the baseline used about 24% more canvas at the
  same font size than the visually accepted patched beautiful-mermaid result.
- beautiful-mermaid 1.1.3 damaged valid ELK routes in two later cosmetic passes.
  Skipping those passes fixed the tested cases, but required a code change;
  maintaining that patch has not been approved.
- Direct ELK reproduced the accepted geometry but would require owning the
  text-measurement and rendering layer. It was not built into a complete renderer.

A future replacement should accept task content and dependencies without manual
coordinates or routing, preserve legibility, and produce
repeatable output. The tests do not guarantee every future graph will render well.
Detailed temporary evidence is in `/tmp/planning-mermaid-elk/` and
`/tmp/planning-beautiful-mermaid/`; those paths are not durable repository storage.

## Local access

From this directory, serve the planning files locally:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Open `http://127.0.0.1:8000/` in a browser on the same machine.

## Browser verification

`tests/test_planning_graph_prototype.py` opens the planning root in isolated
headless Firefox and verifies rendering, focus and step expansion, track views,
cross-track navigation, completed-task filtering, live task-data refresh and
invalid-input errors. It also checks that
the obsolete draw.io files and navigation link are absent. The test requires
Firefox and Python's `websocket-client` package; it uses only local resources.
