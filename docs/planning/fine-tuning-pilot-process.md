# Fine-tuning pilot process

Compare **Qwen3.8-27B, Gemma 4 31B, and Gemma 4 26B-A4B**: how much does
learning from teacher answers improve quality, and what does it cost?

**Subjects only, approved October 2:** train and evaluate subject discovery and
hierarchy. Generate no masks for this pilot. Thinking stays **off** throughout
preparation, training and evaluation, approved October 2.

**GPU selected:** one **96GB RTX PRO 6000** for preparation and the pilot.
Keep each complete model on that GPU and run the three students sequentially.

The execution flow below is a draft. Prompt versions, remaining output format details,
execution settings, and review rubric remain open.

**Local preparation → separate paid GPU preparation → Vast
baselines/training/evaluation → verified retrieval → local scoring and comparison.**

Prepare candidate settings and rehearse automation locally before booking the
separate preparation rental, confirmed in principle October 3. Use existing
notes while the pilot data is pending. The proposed small check covers an
adapter update, checkpoint save/reload/merge, brief batched generation at tested
memory bounds, and restored training. The local package now uses two updates
over 16 existing notes per student and saves brief subject responses separately.
The VM rehearsal passed; actual GPU fit is pending. Check the pilot data and
planned batch shapes against the measured bounds when ready. Future answer
completeness, the rental offer and spending approval remain open.

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

## 1. Freeze shared inputs — locally

Freeze shared training, validation, and final test notes, checked teacher
answers, prompts, model revisions, and training settings. Keep authors and duplicates
within one split.

**1,000 training notes**, with validation checkpoints at **200, 400, 600, 800,
and 1,000**, are approved. **100 validation** and **200 final test** notes remain
proposals. Keep final test notes out of development.

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
   **same validation notes** (100 proposed); save raw and parsed outputs and
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
as soon as saving finishes, while the experiment continues. Verify local copies
and retain remote originals at least until verification. Limit transfer bandwidth
and disk activity. The copier starts automatically beside the observer; final
retrieval reuses verified copies. A transfer failure is reported without stopping
training.

Before explicit deletion, verify both expected work and required local files.
I inspect baseline and trained responses as they arrive and monitor training
and GPU telemetry until explicit deletion. Automatic deletion stays off.

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

## Serial cost reference — October 2

Assuming 100 validation notes, 200 final test notes, and the previous
**$1.4167/hour** GPU's measured single-note subject-generation speed:

- **Ordinary evaluation:** about **$108–113**, including three baselines,
  fifteen checkpoints, and the winner's thinking-off final comparison.
- **Main rental:** roughly **$149–178**, including training, checkpoint
  transitions, transfers and 25% headroom.
- **Separate preparation, October 3 proposal:** roughly **1–3 hours / $2–5** on a compatible offer with cheap transfers.
  Saved telemetry measured about 14 minutes fetching all three models and
  3 minutes startup. Those times are included, not added again. The local
  rehearsal passed; new GPU paths remain unmeasured. The latest search found
  no compatible offer within the proposed $5 cap; spending remains unapproved.

These amounts price serial evaluation, not the approved batched pilot. Revise
the pilot estimate from measured batched throughput and actual output lengths
on the intended hardware.
Memory arithmetic selects each batch's size; it does not establish
runtime or imply dividing serial time by batch size.
The thinking-on evaluations and their cost allowance have been removed.
The specific rental offer, spending and preparation scope remain open.
Teacher labeling and local review assume the existing Codex subscription;
paid API work would be additional. See the technical plan for assumptions.

[Technical details and prerequisites](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md)
· [Decision record](release-decisions.md#two-separate-model-pilots).
