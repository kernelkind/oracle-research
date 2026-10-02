# Fine-tuning pilot process

Compare **Qwen3.8-27B, Gemma 4 31B, and Gemma 4 26B-A4B**: how much does
learning from teacher answers improve quality, and what does it cost?

The execution flow below is a draft. Prompt versions, remaining output format details,
remaining adapter/optimizer settings, and review rubric remain open.

**Local preparation → separate paid GPU preparation → Vast
baselines/training/evaluation → verified retrieval → local scoring and comparison.**

Settle the remaining configuration and rehearse automation locally before booking
the preparation rental. Verify the chosen GPU configuration before the pilot begins.
Preparation checks, hardware, and maximum charge remain open.

## 1. Freeze shared inputs — locally

Freeze shared training, validation, and final test notes, checked teacher
answers, prompts, model revisions, and settings. Keep authors and duplicates
within one split.

**1,000 training notes**, with validation checkpoints at **200, 400, 600, 800,
and 1,000**, are approved. **100 validation** and **200 final test** notes remain
proposals. Keep final test notes out of development.

## 2. Generate untuned baselines — Vast

Save one baseline per candidate on the shared validation notes. Each model
generates its own subjects, then requests one mask response per subject in a
separate prompt. Preserve original responses.

**Check every response and dependent call immediately, before training.**
Account for every mask response for valid subjects. Invalid subject answers
prevent the mask stage; its size may be unknown. Valid empty masks remain answers.

A bad model answer is a measured failure. Missing work or a parser bug blocks
the affected comparison from advancing.

## 3. Continue training and evaluate checkpoints — Vast

Start **one continuing training run per student**:

1. Initialize its adapter and optimizer from the original model once.
2. Learn from **note → teacher hierarchy** and **note + one teacher subject →
   its teacher mask response** examples. Both tasks update the same adapter.
3. After using every training example from the first 200 notes, save the complete
   training checkpoint.
   Verify the saved adapter reloads correctly. Generate subjects and their masks
   on the **same 100 separate validation notes**, using one mask prompt per
   generated subject; save raw and parsed outputs.
4. Continue from that training state through **400, 600, 800, and 1,000 notes**.
   Save and evaluate at each milestone, giving five trained points per student
   plus its untuned baseline. Preserve the optimizer and learning-rate schedule.
   Validation answers do not update the weights.

**One complete pass is approved:** use every subject and mask training example
once, without replacement, in five new 200-note blocks. Earlier notes and labels
remain saved; their examples are not repeated at later milestones. Within each
block, shuffle all subject and mask examples together using a fixed random seed.
Use the next **8 prompt–answer examples for one adapter update**, total across
all GPUs, retaining a smaller final batch when needed. The subject/mask mix
varies between batches. **Starting settings approved October 1:** learning rate
**0.0001, constant with no warmup; LoRA rank 16 / alpha 32** for ordinary adapters.
**Gemma MoE also adapts its routed experts at rank 2 / alpha 32**, retaining
rank 16 / alpha 32 for attention and shared MLP adapters. Original model and router
weights stay frozen. These are starting choices, not established optima.
**Training loss:** average prediction error over all teacher-answer and native
turn-ending tokens in each update, excluding prompts and padding. No extra
subject or mask weighting; longer answers contribute more tokens within an update.
Block membership, the seed value, and remaining model settings stay open.
Record per-task loss, resource telemetry, and actual example coverage at each stage.
This compares
the tested configurations under a modest budget; one pass is not established as
optimal training for every student.

## 4. Retrieve verified results — Vast to local

One background copier transfers subject responses, mask batches, and checkpoints
as soon as saving finishes, while the experiment continues. Verify local copies
and retain remote originals at least until verification. Limit transfer bandwidth
and disk activity.

Before explicit deletion, verify both expected work and required local files.
I inspect baseline and trained responses as they arrive and monitor training
and GPU telemetry until explicit deletion. Automatic deletion stays off.

After interruption, reconcile the existing worker first. Reuse verified saved
work under original settings; preserve defect evidence and prepare fixes locally.

## 5. Score and compare — locally, after the rental

Measure mask agreement and output reliability mechanically. One semantic review
prompt per note and model version sees the full note, task prompt, subjects,
hierarchy, and masks. It returns separate **correctness** and **coverage** scores
with evidence. Prompt and grading details are deferred; reviewer selection is open.

Compare quality before/after training and across data sizes, with failures,
speed, and cost visible. Missing reviewer judgments are evaluation failures.
Check a small hierarchy built from candidate outputs before model selection.

## 6. Confirm on the final test

After model and training choices are settled, use the reserved test to confirm
gains over the corresponding untuned baseline. Whether GPU test outputs are
collected during the main rental and kept sealed, or generated later, is open.
Rental grouping, duration, and spending also remain open.

## Provisional cost — October 1

At the previous GPU's measured speed, generating validation answers for three
baselines and fifteen checkpoints, plus the selected model's final comparison,
projects to **133–142 GPU hours / $188–200 before training, setup and transfers**.
Full cost and elapsed time must include the approved complete pass, checkpoint
checks, and the still-open model settings and GPU schedule. Teacher labeling and
review assume the existing Codex subscription, whose quota is finite; paid API
work would be additional.

[Technical details and prerequisites](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md)
· [Decision record](release-decisions.md#two-separate-model-pilots).
