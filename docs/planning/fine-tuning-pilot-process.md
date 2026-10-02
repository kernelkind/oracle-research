# Fine-tuning pilot process

Compare **Qwen3.8-27B, Gemma 4 31B, and Gemma 4 26B-A4B**: how much does
learning from teacher answers improve quality, and what does it cost?

The execution flow below is a draft. Prompt versions, remaining output format details,
execution settings, and review rubric remain open.

**Local preparation → separate paid GPU preparation → Vast
baselines/training/evaluation → verified retrieval → local scoring and comparison.**

Prepare candidate settings and rehearse automation locally before booking the
preparation rental. Test subject/mask output limits, including thinking on, on
representative and long notes: check complete answers, truncation, GPU memory,
and runtime. Choose and freeze the pilot limits after those checks.
Preparation scope, hardware, and maximum charge remain open.

## 1. Freeze shared inputs — locally

Freeze shared training, validation, and final test notes, checked teacher
answers, prompts, model revisions, and training settings. Keep authors and duplicates
within one split.

**1,000 training notes**, with validation checkpoints at **200, 400, 600, 800,
and 1,000**, are approved. **100 validation** and **200 final test** notes remain
proposals. Keep final test notes out of development.

## 2. Generate untuned baselines — Vast

Save one **thinking-off** baseline per candidate on the shared validation notes.
Each model
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
3. After using every training example from the first 200 notes, save and verify
   the complete training checkpoint. Unload training from the GPU; load the
   saved adapter on a fresh BF16 base and bake its changes into this evaluation copy.
   Verify reloads under that policy. Generate subjects and their masks on the
   **same validation notes** (100 proposed), using one mask prompt per generated
   subject; save raw and parsed outputs and check dependent calls immediately.
4. Discard the evaluation copy and restore the complete training state, including
   the exact next example. Continue through **400, 600, 800, and 1,000 notes**,
   saving and evaluating at each milestone. Keep all five complete checkpoints.
   Validation leaves the saved adapter, optimizer, schedule, and random state intact.
5. Keep thinking **off** at all five checkpoints. After the final checkpoint,
   evaluate that same 1,000-note adapter once more with thinking **on**, on the
   same validation notes. Compare its subjects and masks against the saved
   thinking-off answers. This adds three evaluations, with no further training.

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
**Numerical setup:** AdamW with no weight decay and gradient clipping 1;
unquantized BF16 base and mixed precision computation, FP32 adapter weights,
gradients, and optimizer state. LoRA dropout 0, frozen biases, standard initialization.
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

After model, checkpoint, and thinking mode are settled from validation, use the
reserved test to confirm gains over the corresponding untuned baseline, using
the same thinking mode for both. Whether GPU test outputs are
collected during the main rental and kept sealed, or generated later, is open.
Rental grouping, duration, and spending also remain open.

## Provisional cost — October 1

At the previous GPU's measured speed, generating validation answers for three
baselines and fifteen checkpoints, plus the selected model's final comparison,
projects to **133–142 GPU hours / $188–200 before training, setup and transfers**.
That thinking-off forecast excludes the added thinking-on evaluation: **300
extra note/model outputs and reviews** if validation has 100 notes. Its extra
GPU time and cost are unmeasured. Full cost must also include training, checkpoint
checks, and the remaining settings and GPU schedule. Teacher labeling and
review assume the existing Codex subscription, whose quota is finite; paid API
work would be additional.

[Technical details and prerequisites](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md)
· [Decision record](release-decisions.md#two-separate-model-pilots).
