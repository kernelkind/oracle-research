# Publication contents and hosting

**The hosting split and the following data categories are agreed.** Exact export
schemas, repository names and download paths still need implementation and
review. Nothing has been uploaded, and this plan does not authorize uploading,
deleting original research or rewriting history.

| Where | What |
| --- | --- |
| GitHub | Code and its history, documentation, prompts, reusable experiment specifications and the experiment index |
| Hugging Face Models | All 17 evaluated adapters, with configurations and pinned base-model references: **6.78 GiB** |
| Hugging Face Datasets | Posts actually used, prepared training data, final unsigned hierarchies, standalone prompt answers, evaluation results, final numerical results and each experiment's parameters: **roughly 0.5–1 GiB** |

The GitHub index will link each experiment to its inputs and results at exact
Hugging Face revisions, with checksums. Readers should be able to download the
experiments they need independently. Model and dataset files will be hosted on
Hugging Face; GitHub Release attachments are not the delivery plan.

## What belongs

Publish the inputs, parameters and final outputs needed to understand what was
tried and its outcome, including failed, interrupted and superseded work.

- **Inputs:** original posts actually used, exact selections and splits, prepared
  training data and any task-specific test inputs needed to interpret a result.
  Do not republish unused Nostr collections.
- **Parameters:** small records of actual settings, input selections,
  code/prompt/model versions and outcomes. Reference shared content rather than
  embedding expanded requests or complete working plans in every record.
- **Hierarchy results:** the final hierarchy, or last partial hierarchy when a
  run stopped or failed, in unsigned Nostr-format data. No signing key, event
  signing or relay publication is required.
- **Standalone prompt experiments:** final per-case answers for each tested
  variant/trial, failures and recorded reviews. A prompt answer is a final result
  when the experiment tests that prompt; answers used internally while building
  a hierarchy are construction intermediates.
- **Evaluations:** evaluated model answers, judgments, per-note measurements and
  final comparisons. Distinguish mechanical checks, agent assessments and actual
  user decisions. Keep independently repeated trials distinct from reused answers.
- **Historical numerical studies:** final groups, graphs, memberships,
  comparisons and assessments. Preserve fuzzy memberships when they are the
  method's actual output. Intermediate vectors and distance tables are not a
  blanket publication requirement.
- **Performance studies:** workload/settings, final timing and memory
  measurements, and outcomes.

Keep caches, expanded requests, transport and scheduling logs, grading snapshots,
internal construction responses, optimizer state and upstream model copies
outside the publication by default. Preserve their originals locally. Complete
original-run verification does not determine which files belong in the public
results. Missing historical evidence and incomplete runs must remain explicit.

## Estimated data size

These are planning estimates before compression, not measured download sizes
or an exact export list. Code and cleaned Git history are additional.

| Data | Estimated size |
| --- | ---: |
| Standalone prompt studies, including inputs, final answers and reviews | 150–300 MiB |
| Fine-tune and grading-method evaluations | 150–250 MiB |
| Historical numerical studies | 100–300 MiB |
| Performance and scaling results | 1–20 MiB |
| Final hierarchies and parameter records | 1–20 MiB |
| Used posts and prepared training data | About 68 MiB |
| **Non-model data total, rounded** | **0.5–1 GiB** |
| **All evaluated adapter weights** | **6.78 GiB** |

Allow roughly **8 GiB** for the data and adapters together before compression.
The estimate uses bounded samples of native answers: about 124 MiB for prompt
research and 127 MiB for grading after removing repeated requests and envelopes.
The 3,400 identified fine-tune answers measure about 22 MiB in compact records.
Identified historical numerical result files total about 189 MiB before removing
overlap. These measurements guide the ranges; they are not a finished export.

The confirmed used-post set contains 10,571 IDs and measures 3.80 MiB as compact
ID/text JSONL. Some older unstructured records remain incompletely linked, so
that count is not a claim of exhaustive coverage. The four prepared training
files below add 63.74 MiB. Media and complete signed source-event envelopes are
not included in these measurements.

## Corpora and fine-tunes

[corpora.csv](corpora.csv) identifies the nine original subject corpora used by
the official hierarchy runs; [hierarchy.csv](hierarchy.csv) records their
selections. The original files contain generated subjects and expanded data as
well as posts. Their combined 407.17 MiB is not a requirement to publish those
files unchanged. Export the used inputs and final results according to their
role above. Keep data derived from subject prompts older than **ASv6.100**
clearly labeled as historical evidence.

Publish **all 17 evaluated subject fine-tune adapters on Hugging Face**. Each includes
`adapter_model.safetensors` and `adapter_config.json`, with its pinned base-model
revision and a model card linking its training data, results and loading instructions.

| Adapter family | Checkpoints | Count | Weights and configuration per checkpoint |
| --- | --- | ---: | ---: |
| Qwen3.8-27B pilot | 200, 400, 600, 800, 1000 | 5 | 445.41 MiB |
| Qwen3.8-27B continuation | 2000, 3000 | 2 | 445.41 MiB |
| Gemma 4 31B dense pilot | 200, 400, 600, 800, 1000 | 5 | 467.14 MiB |
| Gemma 4 26B-A4B MoE pilot | 200, 400, 600, 800, 1000 | 5 | 297.85 MiB |

Their weights total **7,280,022,320 bytes**; configurations add 65,449 bytes.
[models.csv](models.csv) records all 17 exact checkpoint identities and base
revisions; [bundle-files.csv](bundle-files.csv) identifies the weight/configuration
pairs. Publication does not designate any checkpoint as production-approved.
The [final L1 comparison](../planning/fine-tuning-pilot-process.md#l1-only-test-results-october-15)
uses Qwen checkpoints 1000 and 3000 and each Gemma model's checkpoint 1000;
the other evaluated checkpoints will also be published.

Retain saved validation answers and available evaluations for **all 17** training
checkpoints. Qwen's pass-two test answers remain sealed/unreviewed and are outside
publication; this does not exclude its validation results.

All three pilots use the same 1,000 training, 100 validation and 200 test notes.
Qwen's continuation repeats the same training notes. Preserve the four prepared
files identified by the training manifests: `train.jsonl` (44,000,367 bytes),
`evaluation.jsonl` (3,661,939), `references.jsonl` (11,847,618) and `test.jsonl`
(7,328,857), totaling **66,838,781 bytes**. The prepared test inputs are distinct
from the sealed pass-two generated answers. Retain the exact split/order records,
training settings and source/version references alongside these data. Avoid
repeating teacher answers already present in the prepared files.

Training instructions must distinguish repeating training from resuming an exact
checkpoint with its optimizer state. Optimizer state is not part of this
publication plan. Base models and the SSE encoder remain pinned upstream
dependencies. Portable training and adapter-use instructions still need testing.

## Automated outputs

The normal experiment workflow must produce these publication outputs. Historical
runs should use the same export path against saved results, without rerunning
inference or changing frozen evidence. The output formats and automatic export
integration are not implemented yet.

The current hierarchy workflow writes its native working outputs; its separate
Nostr exporter signs events. That signing exporter does not satisfy the agreed
unsigned output requirement. Define and test the unsigned hierarchy serialization,
small experiment records, prompt/evaluation outputs and numerical results before
backfilling the collection. Preserve source identities and recorded outcomes.

## Start small

The [reproduction guide](reproduce.md) documents checks already performed on five
existing files: HR39 viewer data, HR36 saved subject inputs and the L1 comparison.
Those files total 46.55 MiB and are listed in [reproduction.sha256](reproduction.sha256).
They demonstrate the current tools; they do not prescribe the new download
layout or require publishing all five original files unchanged. Update the
reader instructions and checksums once the exports are implemented.

## File selection and archive layout

The existing inventories describe source research artifacts. They are useful
for locating evidence and preserving its associations, but are broader than the
agreed publication:

| Table | Current role |
| --- | --- |
| [experiments.csv](experiments.csv) | Locate native jobs, official runs and historical collections; entries are not a count of independent trials |
| [files/README.md](files/README.md) and [file-lists.csv](file-lists.csv) | Locate original files and their measured identities |
| [bundles.csv](bundles.csv), [bundle-files.csv](bundle-files.csv) and [bundle-collections.csv](bundle-collections.csv) | Earlier candidate groupings and original file selections, not the final Hugging Face layout |
| [download-targets.csv](download-targets.csv) | Earlier reader-task dependencies; revise for the new exports |
| [historical-files.csv](historical-files.csv) and [historical-uses.csv](historical-uses.csv) | Artifact blobs in Git history and their original commit associations |

The broad inventory measured **534.71 GiB** of candidate source files. That is
working storage, not the amount to publish. A `delivery=archive` row or a whole
original directory does not define a public download. Final repository names,
file layout and any compression choices remain open. Add exact file lists,
revision links and checksums for the outputs actually exported.

## Before downloads become available

Implement and review a representative export for each result type, then apply
that same workflow to the historical experiments. Check that exported inputs,
parameters, result identities and status agree with the saved evidence, including
reuse and incomplete runs. Review the selected data for sensitive information.
Test reader instructions using only the proposed downloads and documented
upstream dependencies, with the original storage unavailable. Preserve the
original research throughout. History cleanup remains the final publication
preparation step, followed by checks of the final contents and commit references.
