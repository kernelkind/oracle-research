# Publication contents and hosting

Code and history belong on GitHub; used inputs and final results belong on
Hugging Face Datasets; all evaluated adapters belong on Hugging Face Models.
The selected dataset is prepared locally. Nothing has been uploaded, and public
repository names, revision links and download tests remain open.

| Where | What | Prepared size |
| --- | --- | ---: |
| GitHub | Code/history, tests, prompts, reusable specifications, authored findings, reader guides and experiment index | Download size unmeasured |
| Hugging Face Models | All 17 evaluated adapters, configurations and pinned base-model references | 6.78 GiB |
| Hugging Face Datasets | Used posts, prepared training inputs, selected subjects, unsigned hierarchies, prompt answers, evaluations, numerical results and parameters | 844.00 MiB (0.82 GiB) |

## Public Git contents

Keep source code, tests and fixtures, reusable specifications, versioned prompts,
prompt revision/assembly receipts, useful research findings and the selected
experiment index in Git. Generated experiment data is supplied separately.
Complete original working directories are not additional required downloads.

### Original source revisions

The publication history omits generated data and reviewed private material.
Original revision IDs remain in scientific records. The bundled
[commit map](commit-map.txt) resolves original source revisions to their public
counterparts through `generation_history.source_at_revision`; raw Git commands
need the mapped ID. See [historical source lookup](reproduce.md#which-code-is-being-repeated).
Removed generated blobs still require original evidence rather than source lookup.

## What belongs

Publish the inputs, parameters and final outputs needed to understand what was
tried and its outcome, including failed, interrupted and superseded work.

- **Inputs:** original posts actually used, exact selections and splits, prepared
  training data and any task-specific test inputs needed to interpret a result.
  Do not republish unused Nostr collections.
  HR36 also includes its saved starting subject trees, needed to repeat hierarchy
  construction from the same inputs. Preserve their local numbering, wording,
  contexts and order; bind them to exact post text rather than copying posts.
- **Parameters:** small records of actual settings, input selections,
  code/prompt/model versions and outcomes. Reference shared content rather than
  embedding expanded requests or complete working plans in every record.
- **Hierarchy results:** the final hierarchy, or last partial hierarchy when a
  run stopped or failed, in unsigned Nostr-format data. No signing key, event
  signing or relay publication is required.
- **Standalone prompt experiments:** final per-case answers for each tested
  variant/trial, failures and recorded reviews. A prompt answer is a final result
  when the experiment tests that prompt; answers used internally while building
  a hierarchy are construction intermediates. Saved subjects explicitly selected
  as reproduction inputs belong with the inputs rather than standalone results.
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
internal construction responses (apart from selected reproduction inputs),
optimizer state and upstream model copies outside the publication by default.
Preserve their originals locally. Complete original-run verification does not
determine which files belong in the public results. Missing historical evidence
and incomplete runs must remain explicit.
Preparations proven never executed are excluded. An all-unrun saved report alone
is insufficient proof: packaging requires bound execution evidence, rechecked
against originals, and refuses unclassified or changed evidence.

## Measured local exports

[Publications](publications.csv) identifies 2,989 output/input bundles and one
shared-content catalog row. The [dataset manifest](#dataset-manifest) describes the **physical upload files** under
`target/publication-dataset/`. The original compact exports remain local. No public download or Hugging Face revision exists.

Repeated values are stored once in `shared/`. Numeric references such as
`{"$ref":123}` identify shared records containing `id`, full `sha256` and `value`.
The 256 shared files contain 58,232 values used by 402,200 references.
`dataset.json` binds both physical file hashes and the original compact-export
hashes. Verification checks references and reconstructed bytes; restoration
recovers the original compact files exactly. See the
[verify and restore commands](reproduce.md#verify-and-restore-the-dataset).
The category sizes below exclude content charged once to the shared row.

| Data | Selected outputs | Uncompressed size |
| --- | ---: | ---: |
| Standalone prompt studies: inputs, final answers and reviews | 2,351 entries, including three execution-unknown snapshots | 145.09 MiB |
| Historical subject-prompt studies: posts, answers, assessments and measurements | Four studies, 78 calls and 10 distinct posts | 0.36 MiB |
| Additional historical subject/mask evidence: inputs, answers, assessments, corrections and parameters | Six collections, 123 study/review entries and 1,965 saved responses | 13.45 MiB |
| Early/standalone prompt and manual prominence evidence | 22 collections, 24 entries and 514 saved final answers | 2.33 MiB |
| Historical title/description studies: inputs, answers, recorded reviews, final selections and parameters | 35 collections, 556 saved answers and 24 failed attempts | 2.86 MiB |
| Frontier model comparisons: answers, inputs, parameters, reviews and measurements | 13 entries, 233 completed answers and three saved partial answers | 3.98 MiB |
| SSE representation studies: final comparisons, fixed inputs and encoder settings | 11 collections, 381 encoded row identities | 0.84 MiB |
| ASv6.100 evaluation documents | Final quality summary and four frozen agent rubrics, shared by three trials | 0.09 MiB |
| Fine-tune, grading and effort evaluations | 67 final/last reports, including 20 validation stages | 418.56 MiB |
| Historical numerical results, including segmentations, archived baselines, Infomap partitions and navigation studies | 91 bundles | 109.79 MiB |
| Performance measurements | 13 bundles | 0.12 MiB |
| Unsigned hierarchies, selections and parameters | 37 official runs, 203 saved branch outputs and 10 further historical hierarchies | 7.23 MiB |
| Used posts, prepared training inputs, manual reference fixtures and adapter hash records | 10,571 shared posts, four prepared files, two reference fixtures, split/settings records and 17 adapter bindings | 67.89 MiB |
| HR36 starting subjects | 1,000 ordered posts; 25,258 local entries, including 5,378 top-level subjects | 4.76 MiB |
| Shared content and dataset manifest | 256 shared files plus `dataset.json` | 66.65 MiB |
| **Physical dataset files** | **9,686 files** | **844.00 MiB (0.82 GiB)** |
| **All 17 evaluated adapters, weights and configurations** | **34 original files, hashed without copying weights** | **6.78 GiB** |

The exact physical dataset total is **885,002,003 bytes**, including the
**3,442,482-byte** dataset manifest. Together with the unchanged adapter files,
it is **8,165,089,772 bytes (7.60 GiB)**. Code and cleaned Git history are additional.
Measured per-file gzip level-6 compression totals **162,436,389 bytes
(154.91 MiB)**; no compressed downloads were created.

The package restores 9,429 compact-export files and stores repeated content
once. It excludes 196 preparations proven never executed; three snapshots with
unknown execution history remain included. These counts describe bundles and
saved records, not independent trials.

## Corpora and fine-tunes

[corpora.csv](corpora.csv) identifies the nine original subject corpora used by
the official hierarchy runs; [hierarchy.csv](hierarchy.csv) records their
selections. The original files contain generated subjects and expanded data as
well as posts. The selected downloads contain the used inputs and final results according to
their roles above. Results derived from subject prompts older than **ASv6.100**
remain labeled as historical evidence.

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
revisions. The selected `inputs/adapter-hashes/adapters.jsonl`, bound by the
[dataset manifest](#dataset-manifest), binds each weight/configuration pair
to its hashes and sizes. Publication does not designate any checkpoint as
production-approved.
The [final L1 comparison](subject-extraction/fine-tuning.md#l1-only-test-results-october-15)
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
dependencies. The [reader guide](reproduce.md#prepare-the-fine-tuning-inputs)
now checks all three saved recipes directly from published metadata and provides
local GPU and Qwen continuation commands. The
[adapter-use instructions](reproduce.md#use-a-subject-adapter) describe loading a
downloaded checkpoint with its pinned base and extracting subjects from one post.
Fresh GPU execution of the training and inference instructions still needs
validation. These workflows add no datasets or weights to the upload selection.

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
Native exporters still preserve preparation snapshots. Dataset preparation is
the separate step that excludes proven never-executed preparations. All-unrun
snapshots require fresh bound evidence through `--selection`; unknown evidence
remains explicit, and unclassified or stale evidence stops preparation.

Historical export streams the saved report and binds its hash and ordered input
selection. It requires that report and does not reconstruct missing outcomes.
Metadata explicitly records that later receipt/review-sidecar changes have not
been incorporated and receipt validation has not been performed.

The offline `export-evaluation-results --kind prompt-study` adapter handles older
subject-prompt studies saved before the native experiment format. It keeps used
posts once per study in `inputs.jsonl`, final answers in `answers.jsonl`, recorded
assessments in `judgments.jsonl`, and final summary measurements in `results.jsonl`.
Its `experiment.json` binds saved sources, parameters, prompt versions, diagnostic
definitions and review caveats. Opaque review IDs are joined to their original
calls; recorded agent assessments remain distinct from user decisions. Original
working directories, rendered requests, credentials and transport logs are
excluded. This is an explicit historical export; current native experiments
continue using their automatic three-file format above.

With `--spec SELECTION --study ID`, the same command exports the explicitly
hash-bound atomic subject and subject/mask goal studies. The source argument is
their original repository root. It writes the five files above, retaining exact
saved responses, scientific methods and recorded corrections/decisions. See the
[three selections and checks](reproduce.md#verify-and-restore-the-dataset).
The [early prompt and manual prominence selections](reproduce.md#verify-and-restore-the-dataset)
use the same explicit command with their own study IDs. Receipt-only partial
answers, unknown outcomes, final scores and recorded review history remain
source-bound; preparation calls do not become additional standalone results.

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
another source's destination are refused. The [selected outputs](#measured-local-exports) are prepared locally. Hosted
download verification remains unfinished.

## Start small

The [HR39 browsing instructions](reproduce.md#browse-hr39-without-running-models)
use the restored compact hierarchy and used-posts collection. Local checks
reproduced six roots, 200 nodes and 2,693 represented posts, including interactive
browsing. No native run files, model downloads or login are needed. Hosted
download checks remain pending.

The [fine-tune comparison](reproduce.md#inspect-the-fine-tune-comparison) also
uses its restored two-file compact bundle. All seven saved rows match the
published per-note scores, without original research directories or models.

The [HR36 examples](reproduce.md#try-asv6100-on-a-recorded-post) use its compact
ordered selection and the shared posts. Construction additionally uses
`inputs/hr36-subjects`: about 4.76 MiB preserving the full local subject trees
and exact-post hashes. Transport logs, receipts and other extraction-run internals are outside the
compact selection. The recorded-input preparation checks matched all 5,378
Bootstrap inputs without model inference, encoding or clustering.

## Catalogs and manifest

| Record | Purpose |
| --- | --- |
| [experiments.csv](experiments.csv) | Selected studies, settings, provenance and associated publications |
| [publications.csv](publications.csv) | Included bundle identities and coverage qualifications, plus shared-content row |
| `dataset.json` in the dataset | Exact physical and restored paths, sizes and SHA-256 hashes |
| [models.csv](models.csv) | All adapter identities and pinned base-model revisions |

### Dataset manifest

The dataset's `dataset.json` is the authoritative file manifest. It records
physical paths, sizes and SHA-256 hashes, shared-content bindings and the exact
compact-export bytes recoverable by restoration. Use the
[dataset verification and restoration commands](reproduce.md#verify-and-restore-the-dataset)
before opening restored results with consumers that expect their original JSON.
The [inventory](inventory.json) pins the prepared manifest hash and category totals.

## Availability

The dataset and adapters are prepared locally. Public repository names, pinned
Hugging Face revisions and hosted reader tests remain pending. See
[evidence limits](open-items.md) for the tested scope and unresolved historical
bindings. Nothing has been uploaded.
