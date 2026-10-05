# Fine-tuning pilot process

Compare **Qwen3.8-27B, Gemma 4 31B, and Gemma 4 26B-A4B**: how much does
learning from teacher answers improve quality, and what does it cost?

**Subjects only, approved October 2:** train and evaluate subject discovery and
hierarchy. Generate no masks for this pilot. Thinking stays **off** throughout
preparation, training and evaluation, approved October 2.

**GPU selected:** one **96GB RTX PRO 6000** for preparation and the pilot.
Keep each complete model on that GPU and run the three students sequentially.

The execution flow below is a draft. Remaining output format details,
execution settings, and review rubric remain open.

**Local preparation → separate paid GPU preparation → Vast
baselines/training/evaluation → verified retrieval → local scoring and comparison.**

Prepare candidate settings and rehearse automation locally before booking the
separate preparation rental, confirmed in principle October 3. Use existing
notes while the pilot data is pending. The proposed small check covers an
adapter update, checkpoint save/reload/merge, brief batched generation at tested
memory bounds, and restored training. The local package now uses two updates
over 16 existing notes per student and saves brief subject responses separately.
The VM rehearsal and hardware checks passed on the existing notes. Check the pilot data and
planned batch shapes against the measured bounds when ready. Future pilot answer
completeness, its rental offer and spending approval remain open.

**Keep preparation cheap, approved October 3:** collect pilot timing estimates
during the same hardware checks. Keep parser/recovery tests and automation
rehearsal local. Compare qualifying offers by total expected charge, including
startup and transfers; retrieve, verify and explicitly delete promptly after checks.

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

**Input check:** the existing notes need up to **13,747 tokens** including the
current output allowance. A 16K context passes local token checks, but the old
memory policy rejects Qwen and dense Gemma even at batch size one. Context,
memory settings and the pilot estimate remain to be finalized for ASv6.100.

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
Generate independent notes in batches whose size follows the memory budget.
Freeze the thinking-off batching policy per student; use it for that
student's baseline and trained checkpoints. Check and save each answer separately.

**Check every response immediately, before training.**
Account for one subject response per validation note and save parsing failures.

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
Block membership, the seed value, and remaining model settings stay open.
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
retrieval reuses verified copies. A transfer failure is reported without stopping
training.

For the full pilot, complete all necessary work before stopping the job or
deleting its rental
and verify that its data is fully retrieved locally. A successful transfer
alone does not establish completeness. If something is missing, keep the
resource and add that work. If stopping is preferable, ask for user approval
first. Automatic job timeouts, stops on watcher errors, and deletion are disabled;
time/cost thresholds call for review. I inspect responses as they arrive and
monitor training and GPU telemetry until explicit deletion.

**Prep only:** repair straightforward failures immediately. If recovery needs
substantial work, retrieve and verify available data, then delete the rental
under the user's standing approval. Completing all prep checks is not required.

After interruption, reconcile the existing worker first. Reuse verified saved
work under original settings; preserve defect evidence and prepare fixes locally.

## 5. Score and compare — locally, after the rental

Measure output reliability mechanically. One semantic review
prompt per note and model version sees the full note, task prompt, subjects,
and hierarchy. It returns separate **correctness** and **coverage** scores
with evidence. Prompt and grading details are deferred; reviewer selection is open.

Compare quality before/after training and across data sizes, with failures,
speed, and cost visible. Missing reviewer judgments are evaluation failures.
Assess the returned subject hierarchies before model selection.

## 6. Confirm on the final test

After model and checkpoint are settled from validation, use the reserved test
to confirm gains over the corresponding untuned baseline, with thinking off
for both. Whether GPU test outputs are
collected during the main rental and kept sealed, or generated later, is open.
Rental grouping, duration, and spending also remain open.

## Conditional batched cost reference — October 3

Using prep's **ASv6.48** input/batch shapes, saved historical answer lengths,
**100 validation / 200 final test notes** (proposed), and only the winner's
final comparison:

- **Training:** about **5.6 GPU hours** across all three continuing runs.
- **Baselines and evaluations:** about **22–24.5 GPU hours**, including all
  five checkpoints per student and the winner's final baseline/trained comparison.
- **Total planning allowance:** about **36–40 hours / $51–58** at the prep's
  **$1.4153/hour**, including 1–2 hours extra overhead, 25% headroom and $1
  transfer fees. At an illustrative $1.60/hour, this is **$58–65**.

These are projections from brief generation and one-token decode measurements,
not a measured full pilot or a spending cap. They **do not price the frozen
ASv6.100 pilot**. Update the memory/throughput setup, check actual pilot data,
and settle final-test collection before a launch estimate.
Teacher labels and local review assume the existing subscription; paid APIs add cost.

Completed prep's preliminary charges are **$3.26**, including the failed attempt;
those already-incurred charges are separate. 

[Technical details and prerequisites](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md)
· [Decision record](release-decisions.md#two-separate-model-pilots).
