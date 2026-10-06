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
Preliminary cost was **$2.543**.
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
The rebuilt VM passes 101 checks, including container replacement with saved
answers/checkpoints unchanged and an offline cache hit. The inputs match the
rebuilt runtime. The latest VM image is published and verified private; MoE
CUDA confirmation remains pending. The storage rate was **$0.0833/hour**. Vast rejected the first download GPU create request
with HTTP 400; complete inventory checks confirm no instance and zero GPU charge.
 The
launcher discarded the error reason; bounded credential-redacted capture is now
locally tested and the updated VM rehearsal passed before another attempt.
The quoted download-only rate was $1.4278/hour including storage. Local preflight passes; this retry has not started GPU execution.
Actual Vast attachment remains untested; check the mount before setup or
training. The VM has verified recovery across container replacement.

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

The October 3 prep passed on older, shorter inputs. The ASv6.100 checks are
implemented locally; actual CUDA execution, memory fit and timing remain open.

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
loss are implemented and checked locally. Actual GPU fit and timing remain
unverified; check the longest complete examples before launch.

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

Measure output reliability mechanically. One semantic review
prompt per note and model version sees the full note, task prompt, subjects,
and hierarchy. It returns separate **correctness** and **coverage** scores
with evidence. Prompt and grading details are deferred; reviewer selection is open.

Compare quality before/after training and across data sizes, with failures,
speed, and cost visible. Missing reviewer judgments are evaluation failures.
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
