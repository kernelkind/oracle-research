# Publication contents and hosting

**The hosting split and the following data categories are agreed.** Compact
exporters cover the result families below. The supported historical selection
has been converted locally and its exact files/checksums are indexed. Older
formats, repository names and published download paths still need review.
Nothing has been uploaded. The [generated-data history rewrite](#generated-data-history-rewrite)
is complete; privacy and identity review remains open.

| Where | What |
| --- | --- |
| GitHub | Code and its history, tests, prompts and their provenance, authored findings, useful documentation, the selected-study index and commit mapping; download size unmeasured |
| Hugging Face Models | All 17 evaluated adapters, with configurations and pinned base-model references: **6.78 GiB** |
| Hugging Face Datasets | Posts actually used, prepared training data, final unsigned hierarchies, standalone prompt answers, evaluation results, final numerical results and each experiment's parameters: **1.08 GiB currently staged**, with unsupported/missing result review remaining |

The GitHub index will link each experiment to its inputs and results at exact
Hugging Face revisions, with checksums. Readers should be able to download the
experiments they need independently. Model and dataset files will be hosted on
Hugging Face; GitHub Release attachments are not the delivery plan.

## Public Git contents

The agreed layout keeps source code, tests and fixtures, reusable specifications,
versioned prompts, prompt revisions and assembly receipts, and authored research
findings in Git. Generated run files and exhaustive lists of the original
workspace stay outside public Git. Selected inputs and final evidence go to
Hugging Face; preserve the complete original working files locally.

The read-only review at Oracle commit `a45639d2` and runner commit `34d7eb7`
recorded the original sizes below. The selected-study index is now simplified,
and the reviewed generated files are removed from the Oracle publication clone's
commit trees. Original working files remain locally at the same paths, with the
original Git history preserved in a private backup.

| Contents | At the reviewed commits | After the generated-data rewrite |
| --- | ---: | ---: |
| Both Git object databases | About 504 MiB | 32.87 MiB local storage at rewrite checkpoint `d2e3a88c` |
| Both repositories' tracked file contents | About 2.67 GiB | About 60 MiB planning estimate; unchanged by the rewrite |
| `docs/experiments/` | 1,286 files, 192.89 MiB | 23 files, about 7.68 MiB, including the bundled commit map |

At the rewrite checkpoint, Oracle's local Git objects measured **24.50 MiB** and
the unchanged runner's objects **8.37 MiB**, including loose objects. Their
**32.87 MiB** total preceded later documentation and lookup-support commits.
It measures local object storage, not a compressed transfer or public download.

The ordinary untracking change covers **28,307 reviewed generated files**,
totaling **2,608,765,945 bytes (2.43 GiB)**: requests/responses, execution state
and logs, intermediate arrays, rendered displays and working archives. Source,
prompts, authored plans and findings, manually supplied definitions/controls,
fixtures, reusable usage specifications and frozen package contracts remain
tracked. This includes the 17 navigation `RESULTS.md` files and pinned HiDeF
runtime lock. All **196 ambiguous files** remain tracked
pending review. Existing workspace files keep their paths and occupy the same
local storage; a fresh checkout omits the untracked files.

For the public index, retain the maintained guides, selected-result catalog,
checksums, hierarchy/corpus/model summaries and useful provenance/recovery
tables. Retain `historical-files.csv` and `historical-uses.csv` because they bind
evidence to original blobs, commits and paths. `experiments.csv` now retains the
2,595 initially selected rows from the reviewed index, preserving their study
identities, settings and order, plus 33 later-selected title/description
collections, 11 SSE representation collections, six subject/mask collections,
22 early/standalone prompt collections, four segmentation/title/frontier
collections, one archived-baseline collection and four later-located historical
prompt studies. Six ASv6.100 rows additionally link
the shared evaluation documents in their publication notes.
`publications.csv` also indexes the selected
numerical and other
results; `publication-gaps.csv` keeps outstanding evidence review explicit.

The full original job index is preserved in the [local audit copy](#local-audit-copy).
`files/**`, `dependencies.csv`,
`inputs.csv`, `issues.csv`, `spec-inputs.csv`, `collections.csv`, `file-lists.csv`,
`bundles.csv`, `bundle-files.csv`, `bundle-collections.csv` and
`download-targets.csv` are also local audit material. These exhaustive
file/dependency
catalogs and earlier packaging tables are not additional Hugging Face downloads.
Their meaningful conclusions remain in the maintained findings and gap records.
The public index and its navigation links have been updated. Research records
now identify original artifact paths explicitly and name verified selected
exports separately; see [reading the research records](README.md#reading-the-research-records).
The reviewed links to removed generated files have been repaired.
[Original-file replay dependencies and missing evidence](open-items.md#original-file-links-and-replay)
remain open before publication.

### Generated-data history rewrite

The verified Oracle rewrite maps original head
`4476b94b5ef74f4a2ee50dd6b867b783ad242ac5` to
`d2e3a88cca7acf52c657810198611762ff1b53e5`. It removes **29,580 exact paths**
from historical trees: 28,307 reviewed generated-file paths, 1,264 exhaustive
discovery-catalog paths and nine additional historical generated-file paths.
All **3,148 commits**, including empty commits and **398 merges**, are retained
one-to-one. Authors, committers, timestamps, messages and parent order are
unchanged; every tree matches the exact path filter, and the rewritten head's
tree is identical to the original head's tree. Code, prompts, authored findings
and uncertain sources are retained.
The runner's history was not rewritten. Original files were not altered.

The original Git backup is local under
`target/publication-audit/history-cleanup-4476b94b/original.git`. The exact
old-to-new mapping is bundled as [commit-map.txt](commit-map.txt), with identical
copies at `.git/filter-repo/commit-map` and
`target/publication-audit/history-cleanup-4476b94b/commit-map.txt`.
Original generation, export and audit IDs remain unchanged in the research
records. Historical source readers use `generation_history.source_at_revision`
to resolve full original IDs or unique 7–40-character hexadecimal prefixes.
They read the bundled map without Git replacement refs; named/current refs pass
through. An original commit is preferred when its raw object is available,
otherwise its mapped commit is read. Raw `git show` commands still require the
corresponding rewritten ID. See the [reader example](reproduce.md#which-code-is-being-repeated).
At code commit `3ecbc0d4`, six revision tests and the legacy automatic-workflow
test passed in a fresh ordinary clone without replacement refs, private audit
files or saved research inputs. Generated files removed from history remain
unavailable in rewritten commits.

This rewrite removes generated data. Final privacy and identity review, and any
separately approved cleanup it requires, remain before publication. Repeat checks
against the final contents and preserve mappings across any further rewrite.

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
| Historical subject-prompt studies: posts, answers, assessments and measurements | Four studies, 78 calls and 10 distinct posts | 0.36 MiB |
| Additional historical subject/mask evidence: inputs, answers, assessments, corrections and parameters | Six collections, 123 study/review entries and 1,965 saved responses | 13.46 MiB |
| Early/standalone prompt and manual prominence evidence | 22 collections, 24 entries and 514 saved final answers | 2.33 MiB |
| Historical title/description studies: inputs, answers, recorded reviews, final selections and parameters | 35 collections, 556 saved answers and 24 failed attempts | 2.86 MiB |
| Frontier model comparisons: answers, inputs, parameters, reviews and measurements | 13 entries, 233 completed answers and three saved partial answers | 4.00 MiB |
| SSE representation studies: final comparisons, fixed inputs and encoder settings | 11 collections, 381 encoded row identities | 0.84 MiB |
| ASv6.100 evaluation documents | Final quality summary and four frozen agent rubrics, shared by three trials | 0.09 MiB |
| Fine-tune, grading and effort evaluations | 67 final/last reports, including 20 validation stages | 665.12 MiB |
| Historical numerical results, including nine real-note segmentations and four archived baselines | 78 bundles | 99.01 MiB |
| Performance measurements | 9 | 0.02 MiB |
| Unsigned hierarchies, selections and parameters | 37 official runs plus 203 saved branch outputs | 5.35 MiB |
| Used posts, prepared training inputs and adapter hash records | 10,571 posts, four prepared files, split/settings records and 17 adapter bindings | 67.87 MiB |
| **Selected non-model files** | **9,870 files** | **1,110.76 MiB (1.08 GiB)** |
| **All 17 evaluated adapters, weights and configurations** | **34 original files, hashed without copying weights** | **6.78 GiB** |

The exact selected non-model total is **1,164,713,832 bytes**. Together with
the adapter weights/configurations it is **8,444,801,601 bytes (7.86 GiB)**.
Code and cleaned Git history are additional. Measured gzip level-6 compression
of each non-model file totals **165,925,266 bytes (158.24 MiB)**; no compressed
downloads were created and the staged files remain in their original export
formats.

The five original evaluation documents retain their Markdown bytes and relative
paths under `evaluations/asv6.100-generalization-v1/`. Their checksums are listed
directly; they have no `experiment.json` wrapper. The six existing ASv6.100 native
bundles retain the 180 answers and reviews, and their study-index notes link
these shared documents. No additional trial or duplicated answer bundle is added.

The six subject/mask collections add **615 files, 14,109,305 bytes**, or
**2,899,941 bytes** measured with gzip level 6. They preserve exact saved answers
and recorded methods, assessments, corrections and user decisions. Reused answers
remain identifiable; the 1,965 responses are not a count of independent calls.
The four previously selected studies and existing ASv6.100 evidence are not
duplicated. See the [subject/mask checks](reproduce.md#historical-subject-and-mask-study-checks).

The 22 early/standalone collections add **120 files, 2,440,074 bytes**, or
**370,563 bytes** with gzip level 6. Their 24 entries retain 494 early/standalone
answers and 20 manual prominence answers with exact scores and mask contexts.
Original user-review states and later rereviews remain distinct; embedded copies
are references. Existing native prominence outputs are not duplicated. See the
[early prompt and prominence checks](reproduce.md#early-prompt-and-manual-prominence-study-checks).

The four segmentation, fine-region title and frontier collections add **80 files,
19,415,582 bytes (18.52 MiB)**, or **3,633,143 bytes (3.46 MiB)** with gzip level 6.
They retain nine segmentations, 50 title answers and 233 frontier answers, plus
three saved failed partial answers. Original structured reviews, later authored
corrections and interim comparison outcomes remain distinct. Reused baseline
answers link their existing publications. See the
[title/segmentation checks](reproduce.md#fine-region-title-and-real-note-segmentation-checks)
and [frontier checks](reproduce.md#frontier-comparison-checks).

The four archived-baseline bundles add **20 files, 6,196,469 bytes (5.91 MiB)**,
or **1,218,841 bytes (1.16 MiB)** with gzip level 6. They retain parsed assembled
CREC answers and final segments, plus 36,112 unique pairwise cosine measurements
and their diagnostics. TEv4.1's existing answer inputs are referenced without
duplication. Complete original archives remain outside these downloads. See the
[archived-baseline checks](reproduce.md#archived-baseline-checks).

These are measured selected outputs, not an exhaustive all-history size claim.
[Remaining items](publication-gaps.csv) identify 33 unsupported result files,
and one result missing its configuration. The
[109-group historical review](open-items.md#historical-collection-review)
resolved 32 groups needing no separate result export. The other 77 are now
selected: 33 title/description groups, 11 SSE representation groups, six
subject/mask groups, 22 early/standalone prompt groups, four
segmentation/title/frontier groups and one archived-baseline group.
All 27,032 native jobs have been classified: 2,547 standalone trials are retained; warmups,
internal execution jobs, manual construction intermediates and input-only
preparations are excluded. Independent repeats remain distinct, and reused
answers retain their reuse records. The 203 saved hierarchy branches are not
claimed to be independent trials.

Every selected file was rehashed and every payload binding checked. All selected
evaluation answers and supporting judgments were located. Older judgments bound
only by receipt hashes are explicitly labeled `receipt_only`; missing actor
attribution stays `not_recorded`. Privacy review, unsupported-format review and
testing the reader workflow against this exact selection remain open.

The shared used-post file contains 10,571 IDs and measures 3.80 MiB as compact
ID/text JSONL. The four historical prompt studies also include their 10 used
posts in their own inputs; three are absent from that shared file. Some older
unstructured records remain incompletely linked, so
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
revisions. The selected `inputs/adapter-hashes/adapters.jsonl`, listed in
[publication files](publication-files.csv), binds each weight/configuration pair
to its hashes and sizes. Publication does not designate any checkpoint as
production-approved.
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
[three selections and checks](reproduce.md#historical-subject-and-mask-study-checks).
The [early prompt and manual prominence selections](reproduce.md#early-prompt-and-manual-prominence-study-checks)
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

Use the selected-result tables to identify the inputs and final evidence needed
for a study:

| Table | Current role |
| --- | --- |
| [experiments.csv](experiments.csv) | Selected studies with prompt/model settings, provenance and links to compact exports; rows are not an additive count of independent trials |
| [publications.csv](publications.csv) | Selected output formats, source/trial identities, sizes and coverage qualifications |
| [publication-files.csv](publication-files.csv) and [publication.sha256](publication.sha256) | Exact selected payload and metadata paths, sizes and checksums |
| [publication-gaps.csv](publication-gaps.csv) | Unsupported results, missing configuration and identified historical evidence needing export |
| [models.csv](models.csv) | All 17 evaluated adapter checkpoints and their pinned base-model references |
| [historical-files.csv](historical-files.csv) and [historical-uses.csv](historical-uses.csv) | Original artifact blobs and commit associations from the pre-rewrite audit |

These tables describe local selected exports. Final Hugging Face repository
names, revision links, hosted file layout and compression choices remain open.

## Local audit copy

The original discovery audit measured **534.71 GiB** of candidate source files
and indexed 27,032 native jobs. Those working-storage totals and internal job
counts do not describe the selected downloads or independent trials.

For publication maintainers, the complete pre-simplification index is preserved
under ignored `target/publication-audit/index-before-simplification-1f3d541c/`.
Its `docs/experiments/` subtree contains all 1,286 original files, including the
27,193-row job/collection index and exhaustive file/dependency tables.
`manifest.jsonl` records each file's original Git blob, byte count and SHA-256;
the copy was rehashed against that manifest. The recorded source commit is
`1f3d541c`. This local audit copy is outside the public repository and download set.

The generated-file untracking has separate before/after integrity records under
ignored `target/publication-audit/generated-untracking-bfbdc288/`, binding paths,
original Git blobs, byte counts and SHA-256 hashes. The generated files themselves
stay at their original workspace paths.

The public `experiments.csv` retains the selected rows' identities, settings and
original order, with publication notes linking later-selected evidence.
Outstanding older collection/result
exports remain in `publication-gaps.csv`; the retained findings and provenance
tables preserve meaningful recovery and missing-evidence qualifications.

## Before downloads become available

Review the remaining unsupported historical formats using the shared exporters.
Check that exported inputs,
parameters, result identities and status agree with the saved evidence, including
reuse and incomplete runs. Review the selected data for sensitive information.
Test reader instructions using only the proposed downloads and documented
upstream dependencies, with the original storage unavailable. Preserve the
original research throughout. The generated-data rewrite is complete. Finish
privacy and identity review before publication, then check the final contents,
commit mappings and reader workflows.
