# Fine-tuning pilot process

Compare **Qwen3.8-27B, Gemma 4 31B, and Gemma 4 26B-A4B**: how much does
learning from teacher answers improve quality, and what does it cost?

The execution flow below is a draft. Prompt versions, task format, training
settings, and review rubric remain open.

**Local preparation → Vast baselines/training/evaluation → verified retrieval
→ local scoring and comparison.**

## 1. Freeze shared inputs — locally

Freeze shared training, validation, and final test notes, checked teacher
answers, prompts, model revisions, and settings. Keep authors and duplicates
within one split.

**1,000 training notes** are included; **250/500 training**, **100 validation**,
and **200 final test** remain proposals. Keep final test notes out of development.

## 2. Generate untuned baselines — Vast

Save one baseline per candidate on the shared validation notes. Each model
generates its own subjects, then their masks. Preserve original responses.

**Check every response and dependent call immediately, before training.**
Account for every mask response for valid subjects. Invalid subject answers
prevent the mask stage; its size may be unknown. Valid empty masks remain answers.

A bad model answer is a measured failure. Missing work or a parser bug blocks
the affected comparison from advancing.

## 3. Continue training and evaluate checkpoints — Vast

Start **one continuing training run per student**:

1. Initialize its adapter and optimizer from the original model once.
2. Learn from **note → teacher hierarchy** and **note + subject → teacher mask**
   examples. Both tasks update the same adapter.
3. At the proposed 250-note milestone, save the complete training checkpoint.
   Verify the saved adapter reloads correctly. Generate subjects and their masks
   on the **same 100 separate validation notes**; save raw and parsed outputs.
4. Continue from that training state as the data grows to 500, then 1,000 notes.
   Save and evaluate a checkpoint at each milestone, preserving the optimizer
   and learning-rate schedule. Validation answers do not update the weights.

Larger sets retain earlier notes and labels. Continuing does not automatically
require another pass over earlier notes. **Training amount, note ordering and
revisiting, and exact save/evaluation schedule remain open.** Record loss,
resource telemetry, and the examples used at each stage.

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
baselines and nine checkpoints, plus the selected model's final comparison,
projects to **91–100 GPU hours / $130–140 before training, setup and transfers**.
Full cost and elapsed time depend on the cumulative training amount and GPU
schedule, which remain open. Three continuing runs do not automatically reduce
training work by two thirds. Teacher labeling and review assume the existing
Codex subscription, whose quota is finite; paid API work would be additional.

[Technical details and prerequisites](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md)
· [Decision record](release-decisions.md#two-separate-model-pilots).
