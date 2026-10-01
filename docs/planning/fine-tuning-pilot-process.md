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
Account for every requested mask response for valid subjects. Invalid subject
answers prevent the mask stage; its size may be unknown. Valid empty masks
remain saved answers.

A bad model answer is a measured failure. Missing work or a parser bug blocks
the affected comparison from advancing.

## 3. Train and evaluate each data size — Vast

Each run starts from the original model weights with a fresh adapter and
optimizer. The 500-note set includes the first 250; the 1,000-note set includes
the 500. Keep each candidate's recipe fixed and compare matched training work.

In the two-task format, training examples are **note → teacher hierarchy** and
**note + subject → teacher mask**, using their respective prompts. Both tasks
train one adapter per candidate.

Save the adapter, verify reload, and generate validation outputs with the same
prompts, settings, and checks as its baseline. Log training loss, time, GPU
utilization, memory, power, and generation speed.

## 4. Retrieve verified results — Vast to local

Copy completed stage results locally as execution progresses. Before explicit
deletion, verify expected work and transferred files: responses, failures,
adapters, settings, and telemetry. File hashes alone do not prove completeness.
I observe the rental throughout; automatic deletion stays off.

After interruption, check whether the worker still runs before resuming. Reuse
verified saved work with the original settings. Preserve evidence of workflow
defects; prepare code changes locally.

## 5. Score and compare — locally, after the rental

Measure mask agreement and output reliability mechanically. One semantic review
prompt per note and model version sees the full note, task prompt, subjects,
hierarchy, and masks. It returns separate **correctness** and **coverage** scores
with evidence. The rubric, scale, and reviewer model remain open.

Compare quality before/after training and across data sizes, with failures,
speed, and cost visible. Missing reviewer judgments are evaluation failures.
Check a small hierarchy built from candidate outputs before model selection.

## 6. Confirm on the final test

After model and training choices are settled, use the reserved test to confirm
gains over the corresponding untuned baseline. Whether GPU test outputs are
collected during the main rental and kept sealed, or generated later, is open.
Rental grouping, duration, and spending also remain open.

[Technical details and prerequisites](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md)
· [Decision record](release-decisions.md#two-separate-model-pilots).
