# Fine-tuning pilot: process walkthrough

**Status: prepared for design review, September 30, 2026.** This document explains
the whole process so we can discuss the design before implementing changes,
generating more annotations, or renting hardware. It does not authorize those
actions. Decisions and open questions belong in
[release-decisions.md](release-decisions.md#two-separate-model-pilots); the
[technical pilot plan](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md)
contains implementation details and preliminary-run evidence.

## Goal and your involvement

The pilot compares candidates for **the distilled model**: what each can do
before training, how training changes quality, and the total cost of training
and generation. Choosing the **teachers** that supply answers is a separate
comparison. A teacher answer is a training target or reference; it is not the
candidate's untuned baseline.

Your involvement is in **designing the experiment**: its tasks, data, evaluation,
training comparisons, and handling of failures. This process does not assign
you example labeling or semantic adjudication. Proposed evaluation methods must
be discussed with you before being treated as agreed requirements.

The assistant prepares and executes the agreed work, observes the rental, and
reports results and failures. Teachers supply training answers and, if selected
for that role, evaluation judgments. We discuss changes to the experiment's
design together before they are applied.

Working prompts can be used before production wording is final. Record the
chosen versions and keep them fixed within each comparison. Later changes to
task meaning or output structure need a new check; wording similarity alone
cannot guarantee identical behavior.

## The complete sequence

| Stage | Where it happens | What it produces |
|---|---|---|
| 1. Agree the experiment | Local workspace, with your design input | Tasks, working prompt versions, comparison rules, and open choices resolved for this run |
| 2. Prepare the data | Local workspace; calls to hosted teachers if needed | Separate training, validation, and final test notes, plus saved teacher answers |
| 3. Prepare and rehearse execution | Local VM | Tested immutable image, frozen inputs/settings, and automatic execution/retrieval |
| 4. Proposed short confirmation | GPU rental | Check of the actual candidates and chosen format within the pilot job |
| 5. Generate each baseline | GPU rental | Untuned candidate answers, checked as they arrive and before that candidate trains |
| 6. Train and reload | GPU rental | Checkpoints, saved adapter, training logs, and reload check |
| 7. Generate trained answers | GPU rental | Answers on the same evaluation notes, with continuing validation |
| 8. Retrieve and end the rental | Rental and local workspace | Verified local files and confirmed explicit deletion |
| 9. Review meaning and compare | Local workspace; proposed calls to hosted teachers | Quality findings, before/after comparisons, costs, and a recommendation |

Local calls to hosted teachers can incur provider charges. They do not require
keeping the GPU rental alive. The rental budget and teacher-call budget both
count toward the project budget.

The larger pilot can include several training comparisons. Review each round's
saved validation results before deciding on more data or changed settings;
later rounds need their own execution and spending approval. Keep the final
test for the comparison after development decisions stop.

## 1. Agree what we are comparing

The candidates already selected for comparison are Qwen3.8-27B, Gemma 4 31B,
and Gemma 4 26B-A4B. Their selection does not select training settings or a winner.
Before model selection, confirm permission to release the adapted weights.

The preliminary run trained **one adapter per candidate on two prompted tasks**:

- Complete note → subject hierarchy.
- Complete note + one supplied subject → mask response.

At evaluation, each version generated its own subjects before generating masks.
Its historical prompt versions were **ASv6.48** and **MPv3.43**, frozen for that
experiment. These are not selections for the next run.

For the larger pilot we must agree the tasks and answer format. Whether it
retains the two-step format or tests direct mask generation remains a design
choice. The note-sorting mechanism is being developed; whether it needs
prominence or other additional teacher/model outputs is also open. Decide which
of those outputs, if any, this comparison includes and what their quality means.
The intended release model takes a complete note and returns its masks without
a supplied subject list; the preliminary two-step setup does not establish that
this direct format works.

Keep evaluation notes, task instructions, output format, parsing, and decoding
settings the same before and after training. Apply any later parser correction
to both saved sets and record it as a separate re-evaluation.

## 2. Prepare examples and keep evaluation separate

Choose a broader mix of real notes than the preliminary food/coffee-heavy set,
including long notes, ambiguous language, named tags, and many-subject notes.
Split before training; keep the same author, duplicate text, and closely related
notes in one split.

- **Training notes:** teacher answers are what the candidate learns to predict.
- **Validation notes:** compare development runs and settings.
- **Final test notes:** remain untouched by development decisions; evaluate
  selected candidates after those decisions stop.

A training example contains the chosen task instruction, its inputs, and a saved
teacher answer. For the two-step format, the mask example also contains the
supplied subject. Preserve teacher answers and any review findings separately.
Mechanically valid teacher answers still need checks for suitability.

The release plan requires teacher selection and successful 500-note hierarchy
validation before full training-data generation. The selected teachers supply
both the larger pilot's training answers and the later full training data.
Local preparation that does not consume labels can proceed independently.

The technical plan proposes 250 then 500 training notes, a possible expansion to
1,000, 100 validation notes, and 200 final test notes. **These counts are proposals,
not agreed requirements.** The annotation-review method and treatment of unsuitable
answers are also open.

## 3. Make execution reproducible locally

Prepare the image, dependencies, prompts, data, and settings locally. Rehearse
the actual launch, execution, reconnect, and retrieval path in the VM. Include
saved examples of the parsing and missing-call failures from the preliminary run.

The rental receives the tested image and frozen package and runs automatically.
Code edits and dependency installs belong in local preparation. The VM can test
the process with small models; it cannot establish full-size GPU memory use,
speed, or candidate quality.

Define the training-work budget and checkpoint rule before running. Record the
adapter targets as well as rank: the preliminary MoE adapter trained far fewer
parameters than the dense adapters and left its experts frozen. Dataset-size
comparisons should start from the same original weights and control training
work within each model.

Before launch, present the concrete package, GPU configuration, expected duration,
maximum charge, and configured runtime limits. New paid work requires spending
authorization and budget-ledger admission. The preliminary $25 approval does not
authorize the larger pilot.

## 4–5. Confirm the setup and measure the baseline

The proposed short confirmation belongs inside the first approved pilot job,
using the actual candidates and chosen format. It checks generation, actual
weight updates, save/reload, and evaluation, including difficult long outputs.
Use development cases and keep the final test separate. Its exact size and pass
conditions must be agreed. It is not another complete 100-note preliminary
comparison.

For each candidate, its **baseline** uses the original released weights before
our training. Save the actual prompts, raw responses, token counts, timing, and
parsing results. When the format has separate subject and mask calls, confirm
that valid subject answers lead to the expected mask requests.

**Check every response when it arrives, and check baseline coverage before
training starts.** A failed subject answer must be visible immediately, together
with the mask calls it prevented. A systematic failure such as all Gemma
baseline answers being rejected must not silently become a completed baseline.
The exact conditions for continuing or stopping remain to be designed.

## 6. Train and verify the saved adapter

For each training example, the model reads the instruction and inputs and learns
to predict the teacher answer. Prediction errors on answer tokens guide updates
to adapter weights. Prompt tokens supply context and are excluded from the
current recipe's training loss. If both prompted tasks are retained, they train
the same adapter.

Save checkpoints and record training loss, task sampling, elapsed time, and GPU
memory. Loss falling shows better fit to training answers; it does not establish
quality on unseen notes. Task balance must account for answer length and loss
normalization: in the preliminary run, 20% subject rows supplied about 73% of
target tokens.

Save the adapter, reload it, and check that a recorded probe still produces the
same result. The probe is a limited save/reload check, not proof that all future
batched answers will be identical. Log utilization, memory, power, stage progress,
and any sampling gaps throughout the rental.

## 7. Evaluate the trained candidate while validation continues

Run the trained candidate on the same evaluation notes using the agreed settings.
Validate each saved response and each note's call accounting immediately. Report
truncation, malformed selections, missing requests, and legitimate empty masks
separately. A valid empty mask is different from a missing or failed response.

The full pipeline uses the candidate's own generated subjects. A separate mask
diagnostic can supply identical subjects before and after training to isolate
changes in mask generation. That diagnostic does not replace full-pipeline quality.

The proposed handling of identical post-and-subject requests is to reuse one mask
answer across repeated hierarchy branches. Training duplicates also need deliberate
weighting. These changes and the batch size still need design agreement and tests.

Model-output errors are useful evidence of candidate quality. Execution failures
that skip required work are a different problem. Agree the continuation rules
in advance, preserve failed answers, and do not introduce automatic retries for
malformed model responses. Problems requiring changed code or settings return to
local preparation; they are not repaired manually on the rental.

## 8. Retrieve results and explicitly delete

The operator observes startup, execution, retrieval, and deletion. Automatic
deletion remains disabled. Configured worker limits can still stop work; their
behavior must be visible in the launch settings. Observation and explicit
deletion must fit the approved spending and rental limits.

Expected response counts and parsing failures have already been checked during
generation and between stages. At retrieval, verify the transferred files and
retain the outputs, adapters/checkpoints required by the design, logs, settings,
and telemetry. A worker exit code or matching hashes alone cannot establish a
usable comparison.

Once required results are safely retrieved, explicitly end the rental and confirm
its deletion through provider inventory. Record rental, storage, transfer, and
failed-attempt costs, identifying any charges awaiting final billing.

## 9. Review meaning after the rental

The current overlap score compares selected source words and characters. It
ignores subject wording and hierarchy relationships. It can therefore match an
age-milestone passage even when its subject claims a birthday celebration.
The approved initial mask-matching rule uses at least 80% token overlap, with
exact matches reported separately. That is a rule for matching two masks, not
a requirement that a model achieve 80% accuracy.

The **proposed semantic reviewer** is an existing teacher receiving the complete
post, the chosen task prompt, and the candidate output. For subject hierarchies,
it would identify unsupported subjects, missing supported meanings, and incorrect
parent relationships, with evidence. It should allow valid paraphrases and
alternative hierarchies. Masks require interpretation in their original post
context. Any additional outputs included in the comparison need their own
agreed quality criteria.

These are evaluation calls from the local workspace after retrieval. The reviewer
is not fine-tuned, and its judgments do not update candidate weights. They also
do not become training labels automatically. Reviewer selection, exact inputs,
criteria, repeat checks, uncertainty handling, and influence on model selection
remain proposals for our design discussion. Test reliability on clear examples
before relying on its findings; model judgments are not independent ground truth.

Keep mechanical failures, semantic findings, overlap scores, and resource costs
separate in the report. Compare each candidate with its own baseline and across
the tested data sizes. Report improvements and regressions, including long-note
failures. Small differences may need confirmation before selecting a model.

After development decisions stop, compare the selected candidates and their
untuned baselines on the reserved final test. Before model selection, the larger
pilot also requires a small hierarchy built from candidate outputs using the
validated construction and sorting methods. Check its quality and distinguish
candidate errors from failures in the shared hierarchy pipeline. The execution
and cost of that check belong in the agreed pilot design.

## What is implemented, and what still needs work

The preliminary workflow has working training, checkpointing, reload checks,
saved responses, parsing, overlap reporting, VM deployment rehearsal, telemetry,
retrieval, and explicit deletion. Markdown-fenced JSON is now accepted for
subjects and masks while structural validation remains in place.

However, the current evaluation records failures and continues through notes;
it can seal a completed directory even when subject failures prevented mask
generation. **The immediate operator reporting, baseline acceptance checks, and
stage progression rules described above require implementation and verification.**
The proposed semantic reviewer is also not implemented by this document.

In the preliminary run, all three candidates trained successfully, but neither
Gemma generated baseline masks. All three trained candidates exhausted the
subject output limit on the longest note. Qwen's corrected overlap F1 was about
0.344 before and 0.346 after training. These findings explain the new checks;
they do not select a candidate or a better training recipe.

## Design choices to discuss next

| Choice | What we need to settle |
|---|---|
| Tasks and prompt versions | Which working versions to use, output structure, and whether sorting-related outputs are included |
| Data | Topic/length mix, split sizes, annotation checks, and handling of unsuitable answers |
| Evaluation | Subject/hierarchy review, mask and any additional output criteria, reviewer reliability, and use in selection |
| Failure handling | What constitutes usable baseline coverage, which failures allow continuing, and when to stop progression |
| Training comparisons | Steps, sampling, adapter targets, checkpoints, and controls across data sizes |
| Execution | Output headroom, duplicate requests, batch size, confirmation cases, and monitoring |
| Spending | Actual GPU offer, runtime limits, teacher-call costs, and the maximum approved charge |

This walkthrough is the basis for that discussion. Record decisions before
turning open choices into implementation or a paid run.
