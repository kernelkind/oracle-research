# Fine-tuning pilot

## Status and scope

This document contains our experimental plan, decisions, preparation findings,
and open questions. Published model evidence belongs in
[Model research](EXTRACTOR-FINETUNING-MODEL-RESEARCH.md); published data-volume
evidence belongs in [Training-data research](SUBJECT-MASK-TRAINING-DATA-RESEARCH.md).

This pilot selects the model we will fine-tune and release (the distilled
model), not the teachers that write its training data. The separate
[teacher-comparison pilot](../docs/planning/release-decisions.md#two-separate-model-pilots)
has Muse Spark 1.3 Contributor as its leading, unselected candidate. Existing
[teacher research](TOKEN-USAGE-ESTIMATE-1M-NOTES.md#lower-cost-annotation-models)
and the [12-note subject diagnostic](frontier-model-comparison-v1/asv6.23-diagnostic-v2/results.md)
inform that choice; they do not establish mask or prominence quality.
The [teacher-comparison pilot](../docs/planning/release-decisions.md#teacher-comparison-pilot-evaluation-plan)
compares candidates for quality, speed, cost and training-data feasibility; its
experimental procedure and treatment of unsuitable annotations remain open.
This fine-tuning pilot informs the training-volume decision and schedule check;
the teacher comparison does not determine how much training data the distilled
model needs.

Approved requirements:

- Compare Qwen3.8-27B, Gemma 4 31B instruction-tuned, and Gemma 4 26B-A4B
  instruction-tuned.
- Include a baseline without task-specific fine-tuning for every model.
- Check a small hierarchy built from pilot-model outputs before model selection,
  rather than leaving the first downstream check until after final training.
- Confirm permission to release fine-tuned weights during model selection (06),
  before committing to the larger training run. Training-data provider
  permissions remain part of the teacher-comparison pilot (17).
- Measure unseen-note quality before and after training, improvement as training
  data increases, actual training resources and cost, and batched generation
  speed. Include both masks and prominence in the release-model evaluation.
- Start automatic mask matching with an 80% token-overlap cutoff, alongside
  separate exact-match scores. Details are in [Evaluation and decisions](#evaluation-and-decisions).
- The total oracle MVP spending ceiling is $1,000, replacing—not supplementing—
  the old $500 ceiling. Existing spending and commitments still count.
- Protect the larger fine-tune's budget with a provisional pilot spending
  ceiling. See [Pilot budget](#pilot-budget--approved-approach); no amount or
  percentage is approved yet.

The staged experimental design below is proposed, not fully approved. Dataset
sizes, exact training settings, hardware allocations, and individual spending
authorizations remain open. No rental or training run has started for this pilot.

The release plan's **18 · Prepare training code for the fine-tuning pilot** is
ready for preparing code to fine-tune each candidate, save/reload its trained
weights and generate evaluation outputs. Final training-example formatting and
mask/prominence quality evaluation remain in **06 · Choose the model to train**,
which waits for the agreed output format, prominence criteria and reviewed pilot
data as well as the training setup. Readiness is not authorization to begin work;
this planning decision selects no framework or training method.

The later final fine-tune (08) also prepares trained weights, necessary
supporting files, usage instructions and evaluation results for publication.
Verify that the intended release files load and generate masks and prominence;
the pilot setup's internal save/reload check does not establish that release
usability. Preparation can accompany development, with final verification on
the actual release artifacts. Node 16 publishes these prepared outputs. File
formats and publishing locations remain open, and publishing the training
dataset is not required. See [publication preparation](../docs/planning/release-decisions.md#publication-preparation).

## Task and training annotations

```text
complete original note → complete set of grouped source-text masks + prominence per mask
```

The distilled model must discover subjects as well as locate their evidence. The
input does not supply a subject list. Masks may contain separated fragments,
overlap other masks, and vary in number. The production output need not include
the intermediate English subject descriptions. Masks feed unchanged SSE;
prominence supports ordering notes within nodes.

Assess prominence from the complete note and the particular mask, without
requiring a generated subject description. Prominence prompt development and
scoring calibration are a separate workstream from release planning.

Use the subject and mask prompts validated by the current extraction work, not
the superseded ASv6.23 / MPv3.5 commitment. Freeze the exact prompt versions,
teacher model settings, output format and reviewed labels for each controlled
comparison. This plan does not select successor prompt versions. Preserve the
per-note subject hierarchies, raw annotations and review findings for diagnosis;
do not silently mix outputs from different annotation policies.

The prominence definition, annotation prompt, output representation and evaluation
criteria still need to be settled. Report any earlier mask-only results as
mask-only evidence; they cannot establish prominence quality or the cost of
generating both outputs. Generating the full training data requires both the
500-note hierarchy validation and the teacher selection in the
[release plan](../docs/planning/release-decisions.md). The same teachers must
write both the pilot training data and the full training data, per the user's
direction of September 21, 2026. Work that consumes no labels may use any data
and need not wait for the teacher selection.

The agreed readiness target for the larger fine-tune's training data is
**September 27, 2026**, including masks and prominence, with training/evaluation
separation. The checks and handling of unsuitable annotations remain open;
a correction workflow is not assumed. Dataset size and the time required to
produce suitable data also remain open. The target does not establish
feasibility or change the pilot's proposed sizes.

The pilot includes a small hierarchy built from its masks and prominence before
model selection, using the hierarchy construction being validated. This does not
authorize changes to the title prompt, SSE, grouping method or segmentation. Distinguish
distilled-model errors from failures in the shared downstream pipeline; a parsing or
mask-overlap score alone does not establish hierarchy quality. Release-plan
task 11 still checks the final distilled model. This early check does not replace
the separate scale measurements or establish the full build's cost.

## Models and required untuned baselines

| Model | Proposed adaptation | Role |
|---|---|---|
| Qwen3.8-27B | QLoRA | General-model candidate |
| Gemma 4 31B instruction-tuned | QLoRA | Different pretrained foundation |
| Gemma 4 26B-A4B instruction-tuned | Open; published adapter-training path | Mixture-of-experts quality–cost comparison |

The user approved these three candidates on September 24, 2026, replacing
T5Gemma 9B–9B PrefixLM instruction-tuned with Gemma 4 26B-A4B instruction-tuned.
The MoE candidate tests whether lower active computation can reduce corpus
generation cost while preserving mask and prominence quality. Its actual
batched speed and task quality remain unmeasured; fewer active parameters do
not establish lower training memory or cost. See the
[published evidence](EXTRACTOR-FINETUNING-MODEL-RESEARCH.md#gemma-4-26b-a4b).
This selects candidates, not a training recipe or spending amount.

For each model, evaluate its original released checkpoint before training on
our annotations. Its existing pretraining and instruction tuning remain intact.

Within that model's before/after comparison, keep these unchanged:

- Evaluation notes and task instruction.
- Output format and input preprocessing.
- Decoding settings and inference precision.
- Semantic review criteria and mechanical checks.

Both versions receive the original note, without reference subjects or masks.
Preserve all original outputs. The untuned result is the zero-training-note
point on that model's learning curve. The Astra pipeline is a separate reference,
not a replacement for these three baselines.

Different models can use appropriate training settings and native input
formatting. Comparing their practical quality and cost does not isolate the
effect of architecture alone. A Qwen-only setup test cannot establish that
either Gemma checkpoint's training setup works.

## Proposed data

| Set | Distinct notes | Purpose |
|---|---:|---|
| Initial training set | 250 | First comparison across all three models |
| Expanded training set | 500 | Measure improvement from more notes |
| Further expansion | 1,000 | Conditional on the preceding results |
| Validation set | 100 | Compare development runs and select settings |
| Final test set | 200 | Evaluate selected candidates after development stops |

These counts are proposed measurement points, not demonstrated requirements.
One thousand notes is not a prerequisite for the first training experiment.

The 500-note set retains the original 250; the 1,000-note set retains the 500.
All models receive the same sets. Choose broadly varied real notes while keeping
topic, writing-style, and length mixtures similar across sizes. Do not simply
use our food/music-heavy existing annotations as the initial training set.

Split before training. Keep duplicate, closely related, and same-author material
within one split. Reserve the final test notes now, but defer their annotation
until needed. Do not use test outputs to revise the experiment.

Mechanically check every training mask and deduplicate exact masks. Semantically
review a varied sample of training annotations and every validation/test
annotation. The assistant performs the review and asks the user about genuinely
uncertain decisions. This review policy is proposed, not a release requirement.
How unsuitable annotations are handled remains open; preserve teacher outputs
separately from review findings and any subsequent changes.

## Proposed run sequence and controls

1. **Check each training setup on a small sample.** Verify complete-note input,
   the agreed output format, source alignment, working training, GPU memory use,
   and measured speed. Record whether prominence is included. Training loss and
   successful parsing are setup diagnostics, not evidence of semantic quality.
2. **Measure the three untuned baselines.** Use the shared validation notes and
   preserve their outputs before fine-tuning.
3. **Train all three models on 250 notes, then on 500.** Start each dataset-size
   experiment from the same original pretrained weights, not from the previous
   experiment's adapted model.
4. **Control training work within each model.** Keep its recipe fixed across
   dataset sizes and compare checkpoints after matched amounts of training.
   Otherwise, more notes also means more training, and an improvement cannot
   be attributed to additional distinct notes alone. Preserve earlier
   checkpoints so overtraining a small set does not manufacture that effect.
5. **Expand to 1,000 when justified.** Do not eliminate a model merely because
   its 250-note result is weaker. Examine its improvement at 500, remaining
   errors, training behavior, and cost before deciding on further investment.
6. **Confirm decision-critical comparisons.** Repeat with a different random
   seed when a small gain or model difference would determine the next action.
   Keep the same evaluation notes and report uncertainty rather than treating
   each mask as an independent observation.
7. **Use the final test after selection.** Compare selected fine-tuned
   candidates with their corresponding untuned baselines on the reserved notes.

The exact training-work budget, checkpoint schedule, and checkpoint-selection
rule must be specified before runs. The earlier three-pass runtime estimates
are not a frozen training protocol. Any recipe change needed to repair a
training problem must be recorded; it cannot silently enter a data-size
comparison as though only the number of notes changed.

At most nine main fine-tuning runs are proposed across the three dataset sizes,
in addition to untuned baselines, setup checks, and limited confirmation runs.
The 1,000-note stage and confirmations are conditional, not a mandate to spend
the remaining budget.

## Evaluation and decisions

### Initial automatic mask scoring — approved

Within each note, match generated masks to reference masks one-to-one,
independently of their list order. Treat all fragments of each mask together
as a set of source-token positions.

```text
overlap = tokens selected by both masks / tokens selected by either mask
```

Count a match when overlap is at least 0.80. For example, five selected tokens
versus four of those same tokens gives 4/5 = 80%. Calculate precision, recall,
and F1 using this rule, with exact-match scores calculated separately.

This follows the matching approach in
[PropSegmEnt, sections 3.2 and 5.1](https://aclanthology.org/2023.findings-acl.565.pdf).
The 80% cutoff is an initial mask-matching rule, not a required model accuracy.
Source tokenization, how scores are averaged across notes, and which score
selects training checkpoints remain open.

### Required pilot measurements

| Measurement | Required evidence | Decision it informs |
|---|---|---|
| Quality on unseen notes | Before/after subject coverage, mask correctness and prominence quality on the same held-out notes | Whether training improves the intended task |
| Improvement with more training data | Quality at each tested data size, under the controls above | Which models and additional annotations merit investment |
| Actual training resources and cost | GPU configuration, peak memory, training time and total rental cost, including setup and evaluation | Feasible hardware and measured inputs to larger-training estimates |
| Batched generation speed | Notes processed per second, output lengths, peak memory and failures on representative notes | Time and cost to process the proposed launch corpus |

Measure semantic quality separately from mechanical correctness:

- **Coverage:** which supported subjects received a faithful mask?
- **Mask errors:** which masks omit necessary meaning or add unrelated meaning?
- **Prominence:** how well do scores reflect the agreed meaning of prominence?
  Freeze its review criteria before comparing models; do not infer correctness
  from valid numbers or combine its errors with mask errors into one score.
- **Mechanical failures:** which outputs are malformed or cannot be located
  correctly in the original note?

For resource measurements, record the exact checkpoint, training or inference
configuration, batch size, input/output lengths and billed rental interval.
Separate training time from downloading, loading, checkpointing and evaluation;
include all of them in total cost. Record failed attempts and retries rather than
reporting only the successful run.

Measure generation in batches on a representative mix of real notes, including
long notes and notes producing many masks. Report those cases separately as well
as the overall rate. Include failed outputs and retries in elapsed time, and
report unresolved failures separately; do not count them as completed notes.
Repeat the measurement with the selected release model and final output format
before committing the full corpus build.

Valid alternative masks and harmless redundancy are acceptable. Exact copying
is necessary for source alignment, but agreement with one teacher mask list is
not the definition of semantic correctness. Teacher mistakes remain annotation
issues rather than automatically becoming student errors.

The assistant reviews outputs with model identities hidden and preserves
concrete examples of improvements and regressions. Summaries must distinguish
semantic findings from parsing success, training loss, and token-overlap scores.

For each model, show quality before fine-tuning and as training data increases,
including the gain from each added batch. Do not extrapolate a final required
dataset size from two or three points. If improvement shrinks, examine label
quality, missing coverage, model capability, and training behavior before
generating more of the same data.

Compare quality against total training-and-generation cost at the proposed
launch volume, not training cost alone. Keep annotation, storage and transfer
costs visible, and distinguish measured costs from extrapolations. Do not project
one corpus-wide rate from only short, easy notes or infer the final data
requirement from a small learning curve. No universal accuracy threshold or
claim of production readiness has been approved.

## Preparation findings

The read-only annotation audit found these complete-note packages:

| Package | Notes | Distinct accepted masks after exact deduplication |
|---|---:|---:|
| [Food/drink](real-note-fine-segmentation-v1/reviewed-input.json) | 100 | 918 |
| [Coverage expansion](real-note-fine-segmentation-v1/coverage-expansion-v1/masks-reviewed/reviewed-input.json) | 48 | 400 |
| [Music](real-note-fine-segmentation-v1/music-generation-v1/masks-effective-mapped/reviewed-input.json) | 100 | 1,058 |
| Total | 248 | 2,376 |

The files contain 2,434 accepted masks before deduplication and 58 exact
duplicates. Their byte ranges match their source fragments. That is mechanical
validity, not semantic approval of every annotation: one food subject remains
unresolved without a saved mask, and the music review records semantic concerns.
The packages are starting material, not 248 automatically approved training
examples. Do not silently turn an incomplete annotation set into a complete
training target by dropping the unresolved item.

The notes average about 312 characters; original note plus compact grouped-mask
JSON averages about 841 characters after exact deduplication. These are character
counts from a selected corpus, not model-token counts or a forecast for every
new topic. These older annotations and counts do not establish the coverage,
output lengths or prominence labels required by the current extraction work.

## Compute estimates and spending constraints

### Pilot budget — approved approach

Reserve enough of the remaining budget to train the selected model on more
data and evaluate it, with room for reruns. Set a provisional ceiling for the
three-model pilot around that reserve. Reassess the proposed allocation using
measured costs and whether further comparisons could change the model choice.
Any spending still requires the approvals specified below.

Distinguish reusable expenditure, such as training annotations and working
infrastructure, from the additional compute spent comparing candidates. Count
all paid expenditure against the lifetime ceiling, regardless of reuse.

The pilot ceiling is a financial guardrail, not a spending target or evidence
that the pilot is scientifically sufficient. Its amount, the final-training
reserve, and the dataset-size schedule remain open; no fixed pilot/rest ratio
has been adopted.

### Runtime estimates — not measured

The following September 15 estimates predate the current subject hierarchy and
the addition of prominence. They are not measured runtimes for the release task.
They assume 1,000 short training notes, three passes, compact mask-only outputs,
and no CPU offloading. Use pilot measurements to replace these assumptions before
allocating larger-run spending:

| Model | Proposed GPU | Estimated training time |
|---|---|---:|
| Qwen3.8-27B, QLoRA | One A6000 48GB | 1–4 hours |
| Gemma 4 31B, QLoRA | One A6000 48GB | 2–6 hours |
| Gemma 4 26B-A4B, method open | Open | Not estimated |

Allow an additional 1–3 hours per model for downloading, loading, checkpointing,
and evaluation, excluding annotation work and troubleshooting. The earlier
T5Gemma runtime estimate does not transfer to Gemma 4 26B-A4B. The
[published hardware evidence](EXTRACTOR-FINETUNING-MODEL-RESEARCH.md#published-training-hardware-and-weight-storage)
does not establish measured memory use for this particular workload.

Read-only Vast offer searches on 2026-09-15 found A6000 48GB offers around
$0.54–0.56/hour and H100 80GB offers around $2.19–2.59/hour, including 200GB
storage and excluding transfers. The remaining calculations below use a rounded
planning rate of $0.60/hour for an A6000. Availability and
prices can change; no offer was reserved. See [Vast pricing](https://docs.vast.ai/guides/instances/pricing).

### Larger-training cost scenarios — provisional

Saved on 2026-09-15 for reference, not as approved dataset sizes or spending.
Each cell estimates one training run with three passes through the data,
using the model and GPU pairing above.

| Training notes | Qwen3.8-27B | Gemma 4 31B | Gemma 4 26B-A4B |
|---:|---:|---:|---:|
| 10,000 | $6–24 | $12–36 | Not estimated |
| 25,000 | $15–60 | $30–90 | Not estimated |
| 50,000 | $30–120 | $60–180 | Not estimated |

These are linear extrapolations from the unmeasured runtime ranges above:

```text
training cost = hours per 1,000 notes × (training notes / 1,000) × hourly rate
```

They assume similar note and mask lengths and unchanged training throughput.
The ranges are not measured confidence intervals or guaranteed upper bounds.
Three passes is a costing assumption, not a frozen training protocol. Setup,
evaluation, transfers, troubleshooting, and annotation generation are additional.

### Approved allocation

The user approved one shared **$1,000 lifetime budget** and **$0 reserved for
future work**. Nothing is currently earmarked for the pilot or larger fine-tune.
The previously proposed $500 fine-tuning reserve was not approved. Model and
training-cost estimates above remain planning scenarios, not spending authority.
Any paid annotation work shares the same lifetime budget.

Use [budget-ledger.json](../budget-ledger.json) for current spending and
outstanding commitments for this pilot. Hosting costs and reserves stay outside
that ledger, as recorded in the [release decisions](../docs/planning/release-decisions.md#compute-hosting-and-budget).
No per-run spending approval is implied by the training estimates or the
unallocated budget.

### Spending constraints

The [repository budget rules](../AGENTS.md) govern every paid action. The $1,000
ceiling covers the entire effort, including previous costs, failed runs,
evaluation, storage, and transfers. It is not a per-model allowance or a target.
There is no separate parameter-count, GPU-memory, or single-machine ceiling.

The spending code and ledger enforce the approved $1,000 cap. The repository
rules give standing approval for user-requested OpenRouter work roughly estimated
at $1 or less, without a provider-side cap. Other paid runs need an explicitly
approved maximum charge. Provider-enforced spending caps are not required;
ledger accounting and the lifetime ceiling still apply.

## Next approval

The measurement requirements above are approved. Next settle the remaining
experimental design, note splits and annotation format, including prominence.
The dataset-size schedule, exact run settings and spending amounts remain open;
this document does not authorize rentals, annotation calls or training runs.
