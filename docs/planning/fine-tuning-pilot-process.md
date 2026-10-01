# Fine-tuning pilot process

Compare **Qwen3.8-27B, Gemma 4 31B, and Gemma 4 26B-A4B**: how much does
learning from teacher answers improve quality, and what does it cost?

This is the proposed experiment. Counts, prompt versions, task format, training
settings, and semantic-review criteria remain to be settled.

## 1. Use shared data

Give all candidates the same varied notes and saved teacher answers. Separate
training, validation, and final test notes; keep authors and duplicates within
one split. Check teacher answers before using them.

Training sizes under discussion: **250, 500, and 1,000 notes**; inclusion of
1,000 and any rule for making it conditional remain open. **100 validation**
and **200 final test** notes are also proposals. Validation guides comparisons;
the final test stays untouched during development.

## 2. Measure untuned baselines

Run each original model on the validation notes and save its answers. In a
two-step setup, each model generates its own subjects, then their masks.

**Check responses immediately and expected calls before training.** Report
parsing failures and any mask calls they prevent. Teacher answers are references;
the baseline is the untuned candidate's actual output.

## 3. Train on the first dataset

In a two-step setup, examples are **note → teacher's subject hierarchy** and
**note + subject → teacher's masks**, each using the relevant prompt. The model
predicts the teacher answer; prediction errors update adapter weights. Both
tasks train one adapter per candidate.

Save checkpoints, verify adapter reload, and log loss, elapsed time, GPU
utilization, memory, and power.

## 4. Evaluate trained models

Use the same validation notes, prompts, and generation settings as the baseline.
Continue checking responses and call counts as they arrive.

Measure mask overlap separately from subject meaning, hierarchy relationships,
and whether masks preserve the intended meaning. A proposed teacher reviewer
examines the full note, task prompt, and saved output for unsupported or missing
meanings and incorrect relationships. This review happens **after retrieval,
outside the rental**, and is evaluation only.

Verify required results and transferred files before explicitly deleting the
rental. I observe it throughout; automatic deletion stays off.

## 5. Repeat with more training data

The 500-note set contains the first 250 notes plus 250 new notes. Train each
candidate from its original weights. Keep its recipe fixed and compare after
matched amounts of training,
so additional training time does not explain an apparent benefit from more notes.

Which sizes we run and how jobs are grouped into rentals remain open.

## 6. Compare and select

For each candidate, report **baseline quality, quality at each training size,
failures, generation speed, and total cost**. Show improvements and regressions.

Check a small hierarchy built from candidate outputs before model selection.
After development decisions stop, use the reserved final test to confirm the
selected candidates' gains over their untuned baselines.

[Technical details and prerequisites](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md)
· [Decision record](release-decisions.md#two-separate-model-pilots).
