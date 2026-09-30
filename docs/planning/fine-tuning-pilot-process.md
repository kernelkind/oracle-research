# Fine-tuning pilot: process

**Design draft · September 30, 2026.** Open choices below need discussion before
implementation or paid work.

## Goal and your role

Compare Qwen3.8-27B, Gemma 4 31B, and Gemma 4 26B-A4B: does learning from
teacher answers improve quality on unseen notes, and at what cost?

**You participate in the design.** I prepare, execute, monitor, and report the
agreed experiment. Teachers supply answers and proposed evaluation judgments.

## Process

| Step | Where | What happens |
|---|---|---|
| 1. Agree the design | Local | Agree tasks, prompts, data, evaluation, training, spending, and runtime limits. Fix prompts within comparisons. |
| 2. Prepare data | Local + teachers | Gather varied notes and checked teacher answers. Separate training, validation, and final test sets; keep authors and duplicates within one split. |
| 3. Rehearse | Local VM | Test automatic deployment, execution, checks, and retrieval. Freeze the image and inputs; fix problems locally. |
| 4. Measure baselines | GPU rental | Generate untuned answers. **Check responses immediately and expected calls before training.** Report mask calls prevented by subject failures. |
| 5. Train | GPU rental | The model predicts teacher answers; errors update adapter weights. Save/reload and log progress, GPU utilization, memory, power, and time. |
| 6. Measure trained models | GPU rental | Use the same validation notes, prompts, and settings. Check responses and expected calls as they happen. |
| 7. Retrieve and delete | Rental → local | Verify usable results and transferred files, then explicitly delete and confirm deletion. I observe throughout; automatic deletion stays off. |
| 8. Review and compare | Local + proposed teacher calls | Compare meaning, overlap, failures, speed, and cost. Proposed semantic review uses saved outputs after the rental and never updates weights. |

Review each round before deciding on more data or changed settings. After
development stops, compare selected candidates and untuned baselines on the
reserved final test. Check a small hierarchy from candidate outputs before
selection. Include both checks in execution and budget.

## Decisions we need to make together

- **Tasks:** retain subject → mask calls or test direct masks; whether sorting
  needs additional outputs remains open. The previous run used one adapter per
  model for both subject and mask tasks.
- **Data and training:** note mix, split sizes, training work, task balance,
  adapter targets, and checkpoints.
- **Evaluation:** how a proposed teacher reviewer assesses subject meaning,
  hierarchy, and masks; how we check its reliability and use its findings.
- **Execution:** continuation rules for failures, output limits, batching,
  any short confirmation, hardware, maximum charge, and runtime limits.

## What is implemented, and what still needs work

Training, saved responses, telemetry, VM rehearsal, and retrieval work.
Immediate failure reporting and baseline acceptance checks still need
implementation and verification. The semantic reviewer is also a proposal.
A successful worker exit does not establish a complete comparison.

Details and prerequisites: [technical pilot plan](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md).
Decisions: [release record](release-decisions.md#two-separate-model-pilots).
