# Fine-tuning pilot process

Compare **Qwen3.8-27B, Gemma 4 31B, and Gemma 4 26B-A4B**: how much does
learning from teacher answers improve quality, and what does it cost?

**Subjects only, approved October 2:** train and evaluate subject discovery and
hierarchy. Generate no masks for this pilot. Thinking stays **off** throughout
preparation, training and evaluation, approved October 2.

**Two-GPU execution approved October 5:** keep each complete student on one
**96GB RTX PRO 6000**. GPU 0 runs Gemma dense; GPU 1 runs Qwen, then Gemma MoE.
All three prep checks and all three baselines must pass before training starts.
Keeping both GPUs on one main rental was reconfirmed October 6 after comparing
separate rentals; retain the locally tested deployment and shared checks.

The collection and recovery flow is implemented locally. The combined prep→pilot
inputs are frozen and match the rebuilt, tested VM runtime. The user approved
private image publication and a **$285 combined prep→pilot budget** on October 5.
The image is published and verified private. The preparation failed: Qwen passed, dense Gemma exceeded its cache-memory guard, and Gemma MoE failed gradient agreement. No
main baseline or training started. All 86 available files (4.35 GB) were retrieved and independently rehashed.
Preliminary charges are **$1.974** against the original $285 total. Local repairs
pass 94 VM tests and six native tokenizer preflights; one VM tokenizer test was
skipped and covered by the separate preflights. The corrected image is published
and verified private. A replacement failed during container startup because host DNS prevented SSH. One reboot did not fix it. All necessary startup evidence was saved and hashed; no inputs, baseline or training reached the worker. Its preliminary cost was **$0.76**, bringing the two failed attempts to **$2.74**, within the original $285 experiment maximum. Both attempts failed.  A different compatible two-card configuration quotes $2.9389/hour.
Native launch preparation passed. The preparation configuration cost **$2.9389/hour** and was observed through startup, prep and verified retrieval; no pilot work started.
Machine 146170 is excluded. The local $1 startup gate counted the complete
transfer allowance and refused worker admission after successful SSH/input
verification. The refusal was reproduced, then admission was retried with a $5 local setup allowance. Worker attempt 001 started; no remote code, frozen inputs or experimental recipe changed.
Qwen prep passed. Dense completed its updates but hit an erroneous **88 GiB**
training cutoff; MoE failed its gradient check. All **101 available files / 5.85 GB** were verified.
Preliminary cost was **$2.543**, subsequently updated to **$2.687**. 
The local fix removes the training cutoff and keeps inference checks. The MoE
reference also now matches Liger’s gradient-scaling order; the local regression
passes without relaxing tolerances. The local workflow suite passes 89 tests;
12 VM-only checks were skipped. Full CUDA confirmation remains pending;
the runtime is rebuilt below.

**Recovery storage approved:** keep model downloads and compatible saved work
on a persistent local volume. Use a compatible two-GPU configuration for the next attempt, approved October 6; check current GPU and volume availability before booking. The launcher now preserves model downloads and verified work
across replacement, using the same image/data/recipe
and continuing the saved worker attempts. It requires verified retrieval and
confirmed deletion of the previous instance. If a repair changes the runtime,
retain downloads, archive the previous work and start a fresh comparison.
The storage rate was **$0.0833/hour**.
The download requests were rejected before allocating a GPU; no GPU charge or
training. The retry identified an invalid mount path. The launcher now mounts
at `/workspace`, keeping files under `/workspace/oracle-full-build`; local
checks and all 109 VM checks pass. The private runtime passes native preparation.
**Download stage completed October 6:** actual mounting and write/read checks
passed. All **42 files / 169.8 GB** were checksum verified on the volume; local completion review passed.  The preliminary GPU/transfer cost was **$0.455**. Full concurrent CUDA prep and MoE confirmation are still next.
The controller now retries slow image startup on the same instance. Local
regressions, VM rehearsal and private publication pass. Main launch reattaches
this volume to two GPUs for prep.

**Deleted-rental accounting approved October 6:** after verified deletion, release
the unused run budget immediately. Retain only unbooked rent for elapsed time at
the approved maximum rate plus the full transfer allowance, floored by posted
charges. Final invoices are reconciled separately and do not block the next
rental.  
The original $285 experiment total still includes every attempt and storage;
its remaining allowance is conservatively **$274.48** before a new commitment.

  Each 300GB volume costs $0.0833/hour.
 Repeat the tested one-GPU download and
verified retrieval stage on the new host, then launch its two-GPU prep/pilot
with unchanged prompts, data, models and training recipe.
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

**Download stage approved October 6:** rent one GPU on the chosen machine,
verify attachment, and download all three pinned models onto the persistent
volume. Verify every required file and retrieve the evidence before deleting
that container. Keep the volume. Reattach it to the two-GPU rental, verify the
cache offline, then run full concurrent prep and the pilot. The one-GPU stage
collects no baseline or training results.
Save the download log, file sizes/checksums and a volume/machine receipt with
write/read and free-space checks. Verify the retrieved evidence locally before
deleting the download container. The two-card startup rejects missing or corrupt
cached files before prep; model loading stays offline throughout prep and pilot.

**October 6 recovery planning estimate:** singleton dense-Gemma evaluation gives
roughly **53–83 hours / $159–248** at the saved **$2.99/hour** two-card quote,
including storage, transfer and prep. A slower sensitivity case gives
**93 hours / $279**; including the failed prep’s preliminary bill gives $281.
These use older workstation timings and teacher-length proxies. Prep must
establish actual server-card fit and throughput; student answer lengths remain
unknown. The replacement uses the remaining original $285 approval.

**Local rehearsal → one-GPU downloads and volume verification → two-GPU Vast
prep → baselines/training/validation and sealed test
answers on the same rental → verified retrieval → local validation review →
unseal and score test answers.**

Freeze both stages locally. Prep checks the longest complete training example,
two continuing updates, save/reload/merge, brief generation, and full native
caches covering validation and reserved-test input shapes, using synthetic
continuations. It also checks the fused CUDA loss and adapter gradients against
native computation on short inputs, with Liger's FP32 softcap reference.
If all checks pass, discard prep adapters and start fresh pilot adapters on the
same rental. If prep needs substantial repair, retrieve and verify its evidence,
delete, and fix locally before renting again. Keep prep cheap and capture timing.

The October 3 prep used older, shorter inputs. Full ASv6.100 CUDA preparation
passed October 6 on the current two-GPU rental; full-run timing is being measured.

**Dynamic subject evaluation batches are approved.** Before each batch,
tokenize the waiting notes and choose how many fit the frozen per-GPU memory
budget. Account for resident weights, padding, caches through the allowed
output length, temporary buffers and headroom. Short notes can form larger
batches; long notes get smaller ones. The worker now implements this calculation
and saves batch receipts plus separate raw/parsed answers per note. GPU
preparation checks numeric memory allowances. Brief generation timing alone does
not establish the full pilot's runtime.

**Hardware preparation completed October 3:** all three students passed the
tested save/reload/merge/generate/restore cycle on the 96GB card. Results were
verified before explicit deletion. Check actual pilot data against the measured
lengths and memory bounds. See the technical plan for measurements.

## 1. Freeze shared inputs — locally

Freeze shared training, validation, and final test notes, checked teacher
answers, prompts, model revisions, and training settings. Keep authors and duplicates
within one split.

**SP frozen October 4:** use full
[ASv6.100](../../sse_multivector/subject-prompt-goal-v1/asv6.100/ASv6.100.md),
including every worked example, in training and every evaluation. The technical
plan records its source hash.

**Input check, October 5:** the actual dataset needs up to **18,396 tokens**
per training example; some answers exceed the old 4,096-token output limit.
Seven training hierarchies also exceed the old 128-node limit. The new candidate
settings use **20,480-token context / 10,240-token output**, with no node-count
cap for subjects-only evaluation. Memory-efficient attention and fused training
loss are implemented and checked locally. The current CUDA preparation passed
long-input training and full native cache checks October 6; full-run timing
is being measured.

**1,000 training notes**, with validation checkpoints at **200, 400, 600, 800,
and 1,000**, plus **100 validation** and **200 final test** notes, are approved.
Keep final test notes out of development.

**Data selection approved October 4:** extend the existing random hash draw from
the fresh English corpus. Keep readable English root posts with no quote/reply
tags or inline references to other notes, and at most 512 SSE tokens in the full
original text. Preserve ordinary short and difficult posts. Use natural writing-form
proportions; check coverage with the existing 16-form review. Keep authors and
related copies within one split, with known prompt-development authors in training.
Freeze all 1,300 notes and splits before labels. The October 4 selection is now
frozen and verified; all 16 writing forms occur in the full sample.
Validation has no CREATIVE-form notes in this natural draw.

Generate all subject teacher labels using full frozen **ASv6.100**, **GPT-6.1 Sol /
medium**, through the subscription runner. Start at **32 concurrent calls**,
reducing to 24 if provider limits or transport errors arise. Save original responses,
parsed hierarchies and receipts; no masks or paid API fallback. Student thinking
stays off. This selects the teacher for these pilot labels; general teacher
comparison remains separate.

**Labels complete October 5:** all 1,300 passed structural and receipt checks:
1,000 train / 100 validation / 200 final test. Original responses and receipts
are saved; semantic review has not been performed.

## 2. Generate untuned baselines — Vast

Save one **thinking-off** baseline per candidate on the shared validation notes.
Each model generates its own subject hierarchy. Preserve original responses.
Also collect each baseline's answers on the 200 reserved test notes; keep those
answers sealed through local validation review.
Generate independent notes in batches whose size follows the memory budget.
Freeze the thinking-off batching policy per student; use it for that
student's baseline and trained checkpoints. Check and save each answer separately.

**Verify all three complete baselines before any pilot training.**
Check each answer as it arrives. Reparse raw responses and reconcile each note
with its generation receipt; count invalid/truncated model answers as failures.
The parser is checked against saved teacher answers, including JSON fences,
before weights load. Missing work, broken metadata or inconsistent parsing blocks progress.

A bad model answer is a measured failure. Missing work or a parser bug blocks
the affected comparison from advancing.

## 3. Continue training and evaluate checkpoints — Vast

Start **one continuing training run per student**:

1. Initialize its adapter and optimizer from the original model once.
2. Learn from **note → teacher subject hierarchy**: one training example per note.
3. After using every training example from the first 200 notes, save and verify
   the complete training checkpoint. Unload training from the GPU; load the
   saved adapter on a fresh BF16 base and bake its changes into this evaluation copy.
   Verify reloads under that policy. Generate subject hierarchies on the
   **same 100 validation notes**; save raw and parsed outputs and
   check response accounting immediately.
4. Discard the evaluation copy and restore the complete training state, including
   the exact next example. Continue through **400, 600, 800, and 1,000 notes**,
   saving and evaluating at each milestone. Keep all five complete checkpoints.
   Validation leaves the saved adapter, optimizer, schedule, and random state intact.

While each final 1,000-note evaluation copy is loaded, also generate its answers
on the 200 reserved test notes and keep them sealed. Earlier checkpoints generate
validation answers only. The primary comparison uses the three final adapters
and their corresponding untuned baselines.

**One complete pass is approved:** use every subject training example
once, without replacement, in five new 200-note blocks. Earlier notes and labels
remain saved; their examples are not repeated at later milestones. Within each
block, shuffle the subject examples using a fixed random seed.
Use the next **8 prompt–answer examples for one adapter update** on the selected
GPU, retaining a smaller final group when needed. With 1,000 notes, this
is **125 updates per student, 25 per checkpoint block**. Physical training groups
may vary with memory while preserving the same eight-example update and loss.
**Starting settings approved October 1:** learning rate
**0.0001, constant with no warmup; LoRA rank 16 / alpha 32** for ordinary adapters.
**Gemma MoE also adapts its routed experts at rank 2 / alpha 32**, retaining
rank 16 / alpha 32 for attention and shared MLP adapters. Original model and router
weights stay frozen. These are starting choices, not established optima.
**Numerical setup:** AdamW with no weight decay and gradient clipping 1;
unquantized BF16 base and mixed precision computation, FP32 adapter weights,
gradients, and optimizer state. LoRA dropout 0, frozen biases, standard initialization.
**Training loss:** average prediction error over all teacher-answer and native
turn-ending tokens in each update, excluding prompts and padding. No extra
answer or note weighting; longer answers contribute more tokens within an update.
Block membership, seed **17**, and the model settings are frozen in the candidate configurations.
Record loss, resource telemetry, and actual example coverage at each stage.
This compares
the tested configurations under a modest budget; one pass is not established as
optimal training for every student.

## 4. Retrieve verified results — Vast to local

One background copier transfers subject responses and checkpoints
as soon as saving finishes, while the experiment continues. Use Vast's SSH proxy
and copy small response files first. Check for new results between checkpoint
chunks. Completion markers follow verified files. Verify local copies
and retain remote originals at least until verification. Limit transfer bandwidth
and disk activity. The copier starts automatically beside the observer; final
retrieval reuses verified copies. Frozen run metadata, batch plans, started-call
records and saved batch receipts transfer before whole stages finish. The copier
automatically retries up to three times after failure; exhausted retries stay
visible and require inspection. Transfer failures never stop training.

For the full pilot, complete all necessary work before stopping the job or
deleting its rental
and verify that its data is fully retrieved locally. A successful transfer
alone does not establish completeness. Offline verification must account for all
three baselines, fifteen checkpoint evaluations, continuing training coverage,
all saved checkpoints, and six complete 200-note test collections before recording
the completion review required for deletion. If something is missing, keep the
resource and add that work. If stopping is preferable, ask for user approval
first. Automatic job timeouts, stops on watcher errors, and deletion are disabled;
time/cost thresholds call for review. I inspect validation responses as they
arrive and monitor training and GPU telemetry until explicit deletion. Test
responses receive mechanical accounting, parsing and file checks; their content
and semantic scores stay out of review and selection until validation review ends.

**Prep only:** repair straightforward failures immediately. If recovery needs
substantial work, retrieve and verify available data, then delete the rental
under the user's standing approval. Completing all prep checks is not required.

**Pilot recovery approved October 5:** diagnose and repair errors autonomously,
including necessary code or recipe corrections. Record changes and interruptions,
resume from verified saved state, and rerun affected comparisons when a repair
changes their conditions. Repair itself needs no further user approval. Preserve
original evidence; the completeness/deletion and spending rules still apply.

After interruption, reconcile the existing worker first. A failed worker needs
an explicit, recorded continuation on the same rental. Preserve its evidence,
reuse saved answers and complete training checkpoints, and verify a fresh
retrieval and completion review. Never regenerate a saved bad answer. An
interrupted call with no saved answer can run again only through that recorded
continuation. Keep monitoring GPU use, memory, disk space, updates and response
counts; save observations locally without opening test content.

## 5. Score and compare — locally, after the rental

Measure output reliability mechanically. The agreed semantic review uses
**GPT-6.1 Sol / xhigh** through the existing subscription transport. One fresh
review per note and model version sees the complete post, frozen ASv6.100,
trusted teacher answer, candidate hierarchy and mechanical exact subject matches;
model/checkpoint identities stay outside the prompt. Treat ASv6.100 as correct.
Explicit subject, immediate-link and coverage findings feed code-calculated
**correctness** and **coverage** scores. Correctness counts entries with valid
subjects and incoming links; coverage counts required teacher meanings preserved
completely at every compatible returned heading occurrence. Optional broader
headings are not mandatory; equivalent wording and valid extra headings are allowed.
Keep teacher meaning groups fixed across versions and average per-note scores equally.

**Coverage-matching qualification scope agreed October 8:** target required
complete teacher meanings; optional derived teacher headings are not mandatory
coverage targets. Still review every student heading and immediate parent-child
link, and every compatible occurrence for placement of required meanings,
including general student headings. Establish required/optional flags from the
trusted teacher answer and post independently of candidates, then freeze them
across note versions. Those flags and revised cases remain to be established;
the current matching adapter, prompts and saved trials are unchanged. See the
[agreed scope](../../sse_multivector/distillation-review-v1/README.md#coverage-matching-qualification-scope-agreed-october-8).

The subsequently authorized
[teacher-relative qualification case preview](../../sse_multivector/distillation-review-v1/README.md#teacher-relative-qualification-case-preview-october-8)
compares all teacher wordings in six controlled cable variants, without new
requirement labels or scores. It includes the omitted-heading disagreement and
two separate DSMv2 non-exact matching inputs. The legacy DSRv2 renderer is used
only for whole-case inspection. This preview does not adopt a revised pilot
rubric or change the scorer/prompts; structural allowances, adoption and new
calls remain open.

The user subsequently accepted the expected judgments for all six cases in
conversation: equivalent wording passes all three checks; reversed negation
fails teacher agreement and post support; a wrong parent fails teacher
agreement and link validity; a missing general teacher heading fails teacher
agreement while remaining subjects/links stay valid; consistent renumbering
passes and should be checked mechanically. The unchanged-answer control passes
all three checks by definition because the teacher is trusted, and should also
be checked mechanically. These authored expectations are not
measured model verdicts or adoption of a revised scoring rule; no new calls,
prompt changes or scorer changes occurred. See the
[decision record](release-decisions.md).

On October 9 the user approved the unchanged
[DSMv2 meaning-matching instructions](../../sse_multivector/distillation-review-v1/README.md#dsmv2-matching-instructions-approved-october-9).
One generated subject is compared with the complete distinct teacher list;
the decision is one JSON object with `teacher_id` and `reason`. Subject support
and parent-child validity remain separate judgments. Qualification, new calls
and final scoring remain open; R05 is not resolved by approving the wording.

The subsequently authorized [DSSv1 draft](../../sse_multivector/distillation-review-v1/README.md#dssv1-subject-support-prompt-draft-october-9)
judges post support for one unmatched subject from the full post, returning
Boolean `valid` and string `reason`. The controls and proposed support
inheritance from teacher matches await approval; no support experiment or
model calls have been prepared. Existing review/scoring behavior is unchanged.
The user then approved reusing ASv6.100's support rules unchanged instead of
paraphrasing them. The revised DSSv1 wrapper adds only the narrow review task
and output format around `ASV6_100_SUPPORT_RULES`, to be loaded verbatim from
the original source during future shared-workflow preparation. No adapter
currently supplies that variable. The user subsequently accepted the revised
wrapper's exact wording after seeing it in full. DSSv1 remains untested;
controls, qualification and proposed support inheritance remain open. No
inference or bulk adoption is authorized by accepting the instructions.

The user then authorized drafting
[DSLv1 for parent-child validity](../../sse_multivector/distillation-review-v1/README.md#dslv1-parent-child-validity-prompt-draft-october-9)
before qualification. Its input is one actual immediate pair's parent and child
subject strings; ASv6.100's parent-child rule is supplied verbatim from the
original source. The post and surrounding hierarchy are excluded under that
rule. It returns Boolean `valid` and string `reason`, with a lost restriction
and possible counterexample for invalid pairs. Post support and teacher
agreement remain separate checks. The user subsequently approved the unchanged
DSLv1 wording after seeing the full instructions. The unused draft remains
untested; no adapter, schema, prepared experiment, inference or scoring change
is added. Wording approval does not qualify the reviewer or authorize new calls.

The user then accepted adding ASv6.100's subject-wording guidance verbatim to
complete-meaning matching before qualifying a new version. Native `revise`
creates [DSMv3](../../sse_multivector/distillation-review-v1/README.md#dsmv3-asv6100-wording-guidance-draft-october-9)
from approved DSMv2, changing only the version label and an interpretive block
containing the original subject-wording paragraph. The trusted teacher reference,
inputs, matching criteria, response contract, case expectations and saved
evidence are unchanged. The exact draft is shown for review before calls;
no DSMv3 experiment is prepared and no accuracy/cost measurement is claimed.
Previous results do not qualify DSMv3, and the disputed R05 match remains open.

[DSRv1](../../sse_multivector/distillation-review-v1/README.md) is the draft prompt,
report schema and qualification specification. Qualification checks trusted
examples, controlled valid/invalid changes and full-size training hierarchies
before bulk review. If GPT-6.1 Sol / xhigh cannot perform this reliably, rethink
the approach. Drafting this specification does not authorize qualification calls,
bulk reviews or test unsealing; reusable implementation and actual reliability
were still pending when the draft was recorded. The subsequent authorized
offline implementation adds source-bound preparation, report validation,
scoring and qualification checks through the shared experiment workflow.
All 29 cases can be prepared without inference, and an authored Q17 report
provides a concrete preview. The user requested stress inputs from the largest
saved ASv6.100 generations. Offline sizing of all 1,300 labels selects eight
training notes: the union of the top five by entry count and canonical answer
length. They include the overall maxima of 145 entries and 35,966 answer bytes;
final-test labels contribute aggregate sizes only. Complete stress reports
establish completion, while known-result controls test semantic behavior.
After seeing the preview,
the user authorized qualification calls October 8. Initial requests were rejected
with HTTP 400 and no generated reports; the request schema was corrected while
retaining application duplicate checks. The corrected requests produce complete
large reports, but qualification has failed: Q04 penalizes a trusted unchanged
example, and Q21/Q22 change unrelated judgments across controlled variants.
Q23's stream closes with an unfinished report near fifteen minutes; this is
an ungraded transport failure, not evidence of a model output limit.
All 29 cases were attempted once: 28 complete reports and one interrupted
report. Seven of eight largest generations completed. The user subsequently
directed concurrency 8 with existing exponential backoff; the original trial's
concurrency 1 receipts remain unchanged.
The [DSRv1 qualification evidence](../../sse_multivector/distillation-review-v1/README.md#october-8-qualification-evidence)
records the findings. Bulk grading remains unqualified; process revisions and
test unsealing require separate authorization.

The user subsequently authorized drafting and preparing
[DSRv2](../../sse_multivector/distillation-review-v1/README.md#dsrv2-draft-and-offline-preview)
before further model calls. It makes the authority of ASv6.100's worked examples
explicit and supplies the original Q20 receipt's same 66 groups / 44 required
flags to Q20–Q22. These are provisional consistency inputs, not accepted pilot
classifications. The shared adapter verifies the receipt and exact task, post
and teacher binding; the existing all-placements scoring remains unchanged.
DSRv1's failed trial is preserved. After receiving the preview and test sequence,
the user authorized real DSRv2 qualification with Sol / xhigh and concurrency 8.
Q04 passes `8/8` correctness and `2/2` coverage with both meanings required.
The small set finishes with 17 passes, Q14's semantic regression (`6/10` instead
of `8/10` correctness), and Q01's ungraded stream interruption. DSRv2 qualification
has failed. At concurrency 8, four of eight unchanged large hierarchies and both
controlled variants complete; four large streams are interrupted and ungraded.
Both variants fail consistency: the untouched Money transfers link and
compatible headings change despite the fixed groups / flags. All 29 distinct
cases are attempted once across the preserved subsets, yielding 24 complete
reports and five ungraded interruptions. No failed request is retried.
Adoption remains open; bulk review and test unsealing are not authorized.

The October 8 matching discussion next authorizes an offline
[DSMv1 preview](../../sse_multivector/distillation-review-v1/README.md#matching-only-offline-preview)
before calls: one generated subject against its fixed teacher list, with exact
matches handled mechanically and authored expectations outside the prompt.
Separate-note development and confirmation controls include the largest saved
training generations. This tests complete-meaning matching alone; it does not
audit ASv6.100, accept provisional required flags, or replace the full review
process. Sol / xhigh and concurrency 8 stay fixed. After seeing the preview,
the user authorized running the 16 development controls. All 16 pass on their
first attempt: eight matches and eight nonmatches, with no failures, retries or
reuse. This initial controlled result does not establish pilot-wide reliability.
The [DSMv1 development evidence](../../sse_multivector/distillation-review-v1/README.md#dsmv1-development-trial-october-8)
records actual usage and findings. The user then accepted running the reserved
confirmation set with DSMv1 unchanged: all 16 pass on their first attempt,
without failures, retries or reuse. Both sets pass 32/32 authored controls on
separate source notes. See the [confirmation evidence](../../sse_multivector/distillation-review-v1/README.md#dsmv1-confirmation-trial-october-8).
The user subsequently authorized an independent repeat of the confirmation set
with identical inputs/settings and saved-response reuse disabled. All 16 fresh
calls pass and preserve the original teacher IDs/null; only explanation wording
changes in 15 reports. The [repeat evidence](../../sse_multivector/distillation-review-v1/README.md#dsmv1-independent-confirmation-repeat-october-8)
records measured usage. This supports repeatability on the controls, not
accuracy on actual distilled wording or the other semantic review questions.
The accepted next step prepares an offline matching preview from actual saved
validation wording, with DSMv1 and settings unchanged. Baseline and final
checkpoint selections across all three models yield 22 distinct inputs: eight
agent-assessed matches, thirteen agent-assessed nonmatches and one unresolved
case. The user accepted the assessed nonmatch for `Fakery` under DSMv1's
existing complete-meaning rule; `Club symbols` remains unresolved. Acceptance
does not independently verify gold. Native
qualification remains pending, and unresolved placeholders are not nonmatches.
Preparation made zero reviewer calls. See the
[actual-wording preview](../../sse_multivector/distillation-review-v1/README.md#actual-distilled-wording-offline-preview-october-8).
Independent verification, resolving the meaning boundaries, additional calls,
effort/batching comparisons, full review adoption and final-test unsealing remain
subsequent decisions.

The user then accepted allowing the original post to clarify the sense of
wording already present in either subject, while still forbidding missing
restrictions to be supplied from the post. Draft
[DSMv2](../../sse_multivector/distillation-review-v1/README.md#dsmv2-post-interpretation-draft-october-8)
implements this distinction and prepares the same 22 targets offline with
zero calls. DSMv1's tested prompt remains preserved. Sol / xhigh, concurrency 8,
complete-meaning matching and trusted ASv6.100 references remain unchanged.
The authorized offline club assessment sets R19's expected match to T06 for
DSMv2, with no lost restriction in the card-suit sense selected by the post's
`♣`. A separate source definition preserves DSMv1's unresolved expectation.
The authorized offline self-custody check retains R16's expected nonmatch:
`Self-custody` omits the Bitcoin asset restriction even when the post identifies
the guide as about Bitcoin. Its DSMv2 reason is clarified without changing the
expected ID or assessment status. This matching judgment does not judge support
for the general heading. All expectations remain unverified and qualification
is pending.
The user subsequently authorized the
[two-case DSMv2 trial](../../sse_multivector/distillation-review-v1/README.md#dsmv2-two-case-post-interpretation-trial-october-8).
Two fresh Sol / xhigh calls return the expected T06 for R19 and null for R16,
with valid reports, no retries and no response reuse. This shows the intended
distinction in these calls; repeat stability and general reliability remain
open. It does not authorize the other 20 calls, bulk review or test unsealing.
The user then authorized the
[remaining offline post checks](../../sse_multivector/distillation-review-v1/README.md#dsmv2-remaining-post-visible-expectations-october-8).
All 20 expected verdicts are retained: eight matches and twelve nonmatches.
Their recorded reasons now account for the visible posts; all complete inputs,
expected IDs and assessment statuses remain unchanged. A fresh full-set preview
makes zero calls. This completes the post recheck, not independent gold
verification or semantic qualification. Further reviewer calls remain a separate
decision.
The user then authorized the
[remaining 20-case trial](../../sse_multivector/distillation-review-v1/README.md#dsmv2-remaining-20-case-trial-october-8)
using the shared launcher and unchanged Sol / xhigh, concurrency 8 settings.
All 20 final reports are valid; nineteen agree with the recorded expectations.
R05 returns `Inauthenticity` for `Fakery` instead of expected null and is marked
agent-uncertain pending adjudication. There is one successful provider-overload
retry and no response reuse. Prompts and expected labels are preserved;
qualification remains pending. This does not select a revised prompt or
authorize additional calls, bulk review or test unsealing.
The subsequent authorized [eight action/property controls](../../sse_multivector/distillation-review-v1/README.md#dsmv2-actionproperty-controls-october-8)
pass all four paraphrase matches and four nonmatches with unchanged DSMv2 /
Sol / xhigh, concurrency 8. Their explanations preserve the explicit action
versus property distinction. These small-catalog diagnostics were authored
after R05's disagreement; they do not settle its short-wording equivalence,
establish production reliability or change the prompt. R05's expected null
and uncertain review remain preserved. Further calls remain a separate decision.
The subsequently authorized [single-case fresh repeat](../../sse_multivector/distillation-review-v1/README.md#dsmv2-r05-fresh-repeat-october-8)
inherits R05's identical prompt, inputs, evidence and settings with response
reuse excluded. It again returns T17 with a different explanation, without
retry. This reproduces the disputed verdict in two calls but does not settle
its semantic correctness or independently qualify the reviewer. The repeat
has an agent-uncertain review; expected null remains unchanged. Further calls,
prompt revisions and bulk review remain separate decisions.

Compare quality before/after training and across data sizes, with failures,
speed, and cost visible. Invalid/truncated output and an empty answer to a
required task receive both zeros; a correct empty answer passes. Missing or
incomplete reviewer judgments are ungraded evaluation failures. Missing output
or provenance mismatches block evaluation rather than becoming model-output zeros.
Assess the returned subject hierarchies before model selection.
Use the final 1,000-note validation versions for primary model selection; the
five checkpoints show learning progress and regressions. Check the semantic
grader locally and freeze the review criteria before unsealing test answers.

## 6. Confirm on the final test

After validation review and model selection are fixed, unseal the saved test
answers. Score **all three final 1,000-note adapters and all three untuned
baselines** on the same 200 notes: **1,200 test responses**, collected during
the main rental with thinking off. Report each student's gains, failures, speed
and cost, with uncertainty; a close or unconfirmed gain can remain inconclusive.

This compares the tested recipes after the same 1,000 training notes. It does
not establish each student's best possible checkpoint. An earlier validation
peak remains evidence in the learning curve; confirming that earlier version
on the test notes would require additional inference. Test results do not revise
the experiment or choose another checkpoint.

Test collection and completeness checks passed the local VM rehearsal. Separate test
files stay outside content review; automatic reports expose only their counts
and locations. The combined rental is approved up to $285; actual GPU fit and
duration remain unmeasured.

## Historical conditional batched cost reference — October 3

Using prep's **ASv6.48** input/batch shapes, saved historical answer lengths,
**100 validation / 200 final test notes** (proposed), and only the winner's
final comparison:

- **Training:** about **5.6 GPU hours** across all three continuing runs.
- **Baselines and evaluations:** about **22–24.5 GPU hours**, including all
  five checkpoints per student and the winner's final baseline/trained comparison.
- **Total planning allowance:** about **36–40 hours / $51–58** at the prep's
  **$1.4153/hour**, including 1–2 hours extra overhead, 25% headroom and $1
  transfer fees. At an illustrative $1.60/hour, this is **$58–65**.

These historical projections use the former winner-only test scope and brief
generation/one-token decode measurements. They are not a measured full pilot or
a spending cap and **do not price the frozen ASv6.100 pilot or the now-approved
six-version test collection**. Update and validate the context/output/memory
setup and reprice that complete workload before launch.
Teacher labels and local review assume the existing subscription; paid APIs add cost.

The earlier October 3 preparation cost **$3.376**, including its failed attempt; those already-incurred charges are separate.


[Technical details and prerequisites](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md)
· [Decision record](release-decisions.md#two-separate-model-pilots).
