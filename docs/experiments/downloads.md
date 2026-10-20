# Publication contents and hosting

**The hosting split and the following data categories are agreed.** Compact
exporters cover the result families below. The supported historical selection
has been converted locally and its exact files/checksums are indexed. Older
formats, repository names and published download paths still need review.
Nothing has been uploaded, and this plan does not authorize uploading,
deleting original research or rewriting history.

| Where | What |
| --- | --- |
| GitHub | Code and its history, documentation, prompts, reusable experiment specifications and the experiment index |
| Hugging Face Models | All 17 evaluated adapters, with configurations and pinned base-model references: **6.78 GiB** |
| Hugging Face Datasets | Posts actually used, prepared training data, final unsigned hierarchies, standalone prompt answers, evaluation results, final numerical results and each experiment's parameters: **1.04 GiB currently staged**, with legacy review items remaining |

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

## Measured local exports

[Publications](publications.csv) identifies the selected results;
[publication-files.csv](publication-files.csv) lists every file, size and SHA-256.
[publication.sha256](publication.sha256) is the corresponding checksum list.
The ignored local staging root is `target/publication-exports/`. No public
download or Hugging Face revision has been created.

| Data | Selected outputs | Uncompressed size |
| --- | ---: | ---: |
| Standalone prompt studies: inputs, final answers and reviews | 2,547 prepared trials | 249.46 MiB |
| Fine-tune, grading and effort evaluations | 67 final/last reports, including 20 validation stages | 665.12 MiB |
| Historical numerical results | 73 | 78.85 MiB |
| Performance measurements | 9 | 0.02 MiB |
| Unsigned hierarchies, selections and parameters | 37 official runs plus 203 saved branch outputs | 5.35 MiB |
| Used posts, prepared training inputs and adapter hash records | 10,571 posts, four prepared files, split/settings records and 17 adapter bindings | 67.87 MiB |
| **Selected non-model files** | **8,812 files** | **1,066.67 MiB (1.04 GiB)** |
| **All 17 evaluated adapters, weights and configurations** | **34 original files, hashed without copying weights** | **6.78 GiB** |

The exact selected non-model total is **1,118,483,825 bytes**. Together with
the adapter weights/configurations it is **8,398,571,594 bytes (7.82 GiB)**.
Code and cleaned Git history are additional. Measured gzip level-6 compression
of each non-model file totals **156,711,874 bytes (149.45 MiB)**; no compressed
downloads were created and the staged files remain in their original export
formats.

These are measured selected outputs, not an exhaustive all-history size claim.
[Remaining items](publication-gaps.csv) identify 33 unsupported result files,
one result missing its configuration, and older inventory groups still needing
review. Those groups can include code/prompts already in Git or results covered
elsewhere; they are not automatically additional missing datasets. All 27,032
native jobs have been classified: 2,547 standalone trials are retained; warmups,
internal execution jobs, manual construction intermediates and input-only
preparations are excluded. Independent repeats remain distinct, and reused
answers retain their reuse records. The 203 saved hierarchy branches are not
claimed to be independent trials.

Every selected file was rehashed and every payload binding checked. All selected
evaluation answers and supporting judgments were located. Older judgments bound
only by receipt hashes are explicitly labeled `receipt_only`; missing actor
attribution stays `not_recorded`. Privacy review, unsupported-format review and
testing the reader workflow against this exact selection remain open.

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

### Hierarchies

`run-hierarchy` exports the saved hierarchy after completion or blockage and
attempts the same export after failure or interruption, once submitted jobs have
stopped. It writes these three files under the run's `publication/` directory:

| File | Contents |
| --- | --- |
| `experiment.json` | Format/schema version, experiment identity, recorded input/code/prompt/model settings, graph and execution status, counts and SHA-256 hashes of the two payload files |
| `input-note-ids.txt` | The exact ordered input selection, including notes absent from the resulting hierarchy |
| `hierarchy.jsonl` | Final or last partial hierarchy, retaining titles, definitions, ordered roots/children and direct post references |

The JSONL records contain only `kind`, `tags` and `content`: kind `8680` for
nodes and a final kind `18680` entry for the roots. Node tags are `d` (UUID),
`title`, `child` (UUID only) and `e` (source post ID); node `content` retains the
saved meaning. UUIDs derive from a fixed namespace and local node ID and are
scoped to that file. There are no event IDs, author keys, signatures or
timestamps. These unsigned records are not relay-ready signed events.

Post references use the existing outside-children rule: an ancestor omits a post
present in any child subtree, while siblings can retain shared posts. An empty
hierarchy still has an empty entry record. `experiment.json` reports represented
notes separately from the full input count; completion does not imply coverage
of every selected note or semantic approval.

New preparation captures a persistent publication UUID, selected subject-prompt
versions, effective clustering settings and Oracle/runner Git provenance.
`code.preparation` describes preparation-time commits and modified-source flags;
saved code hashes, upgrade hashes and the numerical executable hash identify
the saved construction code and its changes. Separate exporter hashes identify
the serialization code. Unavailable historical provenance remains unknown.

`input.deprecated` is `true` when any known subject-prompt version predates
ASv6.100, `null` when provenance is insufficient, and `false` otherwise. A false
value does not establish approval of a later prompt or semantic quality. Graph
`status` is separate from `execution_status`; exporting an old snapshot without
execution evidence records `not_recorded` rather than guessing whether it
completed, stopped or failed.

Use the same `export-hierarchy-results` command to export a saved historical run
or refresh a resumed run; see the [instructions](reproduce.md#export-compact-hierarchy-results).
`source_id` uses the saved publication UUID for new runs. Legacy runs use an
opaque source-location hash; moving one requires a fresh export destination.
An unchanged re-export preserves file bytes and modification times. The exporter
streams the saved state once while hashing its bytes, retaining graph, selection
and settings while skipping construction working data. It does not change saved
state, scan the source corpus or receipt history, call models, or export internal
construction prompt jobs separately. The existing signed `export-canonical-nostr`
command remains separate.

A local HR39 preview exports its 200-node, six-root graph representing
2,693 of 5,000 inputs as **804,511 bytes (about 786 KiB)**: 475,058 bytes of
hierarchy, 325,000 bytes of input IDs and 4,453 bytes of metadata. Original post
text belongs in the shared posts dataset. Exporting the 250.61 MiB saved state
used about 46 MiB peak resident memory under a 512 MiB address-space limit.
This is one local export check, not a published download or a validation of
million-note generation.

### Prompt studies

New standalone native experiments save compact results during preparation,
execution and review. `export-results` uses the same implementation for an
explicitly selected historical experiment:

| File | Contents |
| --- | --- |
| `experiment.json` | Frozen trial identity, prompt/model/code bindings, settings, repeat/import provenance, case counts and payload checksums |
| `inputs.jsonl` | Exact template-variable inputs, stored once per input hash |
| `results.jsonl` | Case/input identities, final answer and status, reuse or mechanical origin, comparison and attributed reviews |

Rendered requests, nested baseline reports, arbitrary evidence wrappers and
transport details are excluded. User comments remain comments; agent assessments
and user judgments keep their recorded roles. Equal answers do not establish
reuse, and independent repeats retain different trial identities.

New plans freeze `publication_role`. Normal standalone preparation selects
`standalone`; hierarchy construction children, coordinator-created grading jobs
and cache warmups use `internal` and are excluded from separate prompt
publication. Final evaluation exports retain their supporting judgments.
Revisions inherit their source role.
Unmarked historical plans require explicit export or an explicit role when
preparing a new revision; their frozen originals are not changed.

Historical export streams the saved report and binds its hash and ordered input
selection. It requires that report and does not reconstruct missing outcomes.
Metadata explicitly records that later receipt/review-sidecar changes have not
been incorporated and receipt validation has not been performed.

### Evaluations

Fine-tune evaluation writes compact raw answers and parsed per-note measurements
outside its sealed stage directories, under `publication/evaluations/STAGE/`.
Baseline and all evaluated validation checkpoints are eligible. Whole `test/`
directories are excluded; reviewed grading selections supply the exact evaluated
test answers separately, preserving the sealed Qwen pass-two exclusion.

Final automatic grades and assembled grading-method reports retain selected
raw model answers, per-answer scores/proofs and their supporting judgments:

| File | Contents |
| --- | --- |
| `experiment.json` | Settings, selected-input/source bindings, status, limitations and payload checksums |
| `answers.jsonl` | The selected evaluated answers with note/model/version identities |
| `results.jsonl` | Final per-answer scores, checks, qualification and premise references |
| `judgments.jsonl` | Referenced native judgment outputs and agent adjudications, with source hashes and actor distinctions |

Judgment receipts are stored once and joined by hash; aliases retain their own
case/input/output bindings. Missing or mismatched evidence stays explicit.
Final L1, paired-grade and effort comparisons have dedicated projections.
Partial runs export available evidence without changing frozen originals or
claiming unfinished scores are complete. Expanded prompts, messages and repeated
grading snapshots are excluded.

### Numerical studies and performance

`export-numerical-results` supports explicit geometric hierarchy, fuzzy,
HiDeF, merge-rule, comparison, performance, fine-region and pair-score profiles.
Each writes `experiment.json`, `inputs.jsonl` and `results.jsonl`. Parameters use
known-setting allowlists; omitted unknown settings are counted without copying
their values. Inputs retain canonical row/alias mappings to source notes and
subjects where the original format supplies them.

Results retain native groups, graphs, merge histories, fuzzy memberships/final
interpolation, comparisons, assessments and measurements. Numerical graphs keep
their native meanings and IDs. Coordinates, vectors and working distance tables
are excluded. The geometric/fuzzy, HiDeF, merge-rule and benchmark final writers
automatically invoke the same exporter. Saved Rust reports and older diagnostic
profiles use explicit offline export; their original commands are unchanged.
Unsupported historical schemas fail explicitly.

All these exports use staged, managed output directories and payload hashes.
An unchanged refresh preserves bytes and modification times; unrelated files or
another source's destination are refused. The [local historical selection](#measured-local-exports)
has been backfilled; unsupported formats and final download verification remain
unfinished. These local exports have not published the collection.

## Start small

The [reproduction guide](reproduce.md) documents checks already performed on five
existing files: HR39 viewer data, HR36 saved subject inputs and the L1 comparison.
Those files total 46.55 MiB and are listed in [reproduction.sha256](reproduction.sha256).
They demonstrate the current tools; they do not prescribe the new download
layout or require publishing all five original files unchanged. Update the
reader instructions and checksums once the public selections and paths are final.

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
