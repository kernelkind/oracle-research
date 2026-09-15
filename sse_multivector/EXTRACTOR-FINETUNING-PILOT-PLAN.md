# Extractor fine-tuning pilot

## Status and scope

This document contains our experimental plan, decisions, preparation findings,
and open questions. Published model evidence belongs in
[Model research](EXTRACTOR-FINETUNING-MODEL-RESEARCH.md); published data-volume
evidence belongs in [Training-data research](SUBJECT-MASK-TRAINING-DATA-RESEARCH.md).

Approved requirements:

- Compare Qwen3.8-27B, Gemma 4 31B instruction-tuned, and T5Gemma 9B–9B
  PrefixLM instruction-tuned.
- Include a baseline without task-specific fine-tuning for every model.
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

## Task and frozen teacher

```text
complete original note → complete set of grouped source-text masks → unchanged SSE
```

The extractor must discover subjects as well as locate their evidence. The
input does not supply a subject list. Masks may contain separated fragments,
overlap other masks, and vary in number. The production output need not include
the intermediate English subject descriptions.

Training annotations come from the frozen
[ASv6.23](subject-prompt-goal-v1/asv6.23/frozen.json) and
[MPv3.5](mask-prompt-goal-v1/frozen.json) packages, both using Astra low. The
existing annotation policy defines the task; this is not a switch to factual
propositions, named entities, or a predefined taxonomy. Preserve the subjects
and review history for diagnosis even when only masks become training targets.

The experiment excludes title generation, SSE changes, and segmentation.
Mask quality alone would not establish the quality of a complete discovery
hierarchy.

## Models and required untuned baselines

| Model | Proposed adaptation | Role |
|---|---|---|
| Qwen3.8-27B | QLoRA | General-model candidate |
| Gemma 4 31B instruction-tuned | QLoRA | Different pretrained foundation |
| T5Gemma 9B–9B PrefixLM instruction-tuned | LoRA | Encoder–decoder alternative |

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
Gemma or T5Gemma's training setup works.

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
uncertain decisions. Preserve teacher outputs separately from corrections.

## Proposed run sequence and controls

1. **Check each training setup on a small sample.** Verify complete-note input,
   grouped-mask output, source alignment, working training, GPU memory use, and
   measured speed. Training loss and successful parsing are setup diagnostics,
   not evidence of semantic quality.
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

### Other measurements and interpretation

Measure separately on the same validation notes:

- **Coverage:** which supported subjects received a faithful mask?
- **Mask errors:** which masks omit necessary meaning or add unrelated meaning?
- **Mechanical failures:** which outputs are malformed or cannot be located
  correctly in the original note?
- **Cost and speed:** actual training cost, output length, generation time per
  note, and serving requirements on the tested hardware.

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

The pilot should identify which candidates merit further investment, how
quickly they improve, and what errors remain. No universal accuracy threshold
or claim of production readiness has been approved.

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
new topic.

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

The following are planning estimates, not measured runtimes for our task. They
assume 1,000 short training notes, three passes, compact mask outputs, and no
CPU offloading:

| Model | Proposed GPU | Estimated training time |
|---|---|---:|
| Qwen3.8-27B, QLoRA | One A6000 48GB | 1–4 hours |
| Gemma 4 31B, QLoRA | One A6000 48GB | 2–6 hours |
| T5Gemma 9B–9B, LoRA | One H100 80GB | 0.5–3 hours |

Allow an additional 1–3 hours per model for downloading, loading, checkpointing,
and evaluation, excluding annotation work and troubleshooting. T5Gemma's setup
is the least certain. The [published hardware evidence](EXTRACTOR-FINETUNING-MODEL-RESEARCH.md#published-training-hardware-and-weight-storage)
does not establish measured memory use for this particular workload.

Read-only Vast offer searches on 2026-09-15 returned approximately $0.56/hour
for an A6000 48GB and $2.59/hour for an H100 80GB, each including 200GB storage
and excluding transfers. At those quotes, 24 hours on each proposed machine
would total about $89 across the three candidates. This was an illustrative
rental-duration calculation, not the cost of the complete pilot or a training
runtime forecast. Quotes can change. See [Vast pricing](https://docs.vast.ai/guides/instances/pricing).

The [repository budget rules](../AGENTS.md) govern every paid action. The $1,000
ceiling covers the entire effort, including previous costs, failed runs,
evaluation, storage, and transfers. It is not a per-model allowance or a target.
There is no separate parameter-count, GPU-memory, or single-machine ceiling.

The spending code and ledger still enforce the previous $500 cap. Reconcile
the ledger and separately approve the enforcement change before spending;
the new policy does not bypass existing checks. Every paid run needs an
explicitly approved maximum charge and a provider-side limit that enforces it.

## Next approval

The next proposed step is to approve the experimental design, then select and
freeze the note splits and annotation format. Exact run settings and charges
follow the setup and cost checks; this document does not authorize paid work.
