# Proposed publication contents

**Hosting and inclusion of all 17 evaluated adapters are agreed. Other contents
remain a proposal for review.** Keep code, Git history, prompts, documentation
and the experiment index on GitHub. Publish
reusable adapters on Hugging Face Models and experiment datasets on Hugging Face
Datasets. The index will link each experiment to the exact published versions.
Nothing in this proposal authorizes uploading, deleting originals or rewriting
history. Downloads have not been packaged or published.

The aim is to let readers inspect what was tried, check the evidence behind the
results, use the trained models and repeat experiments. Include unsuccessful
and superseded work. Publish every evaluated adapter checkpoint so readers can
run the intermediate training stages as well as the final comparisons.

## Recommended contents

| Item | Why publish it | Measured size and limits |
| --- | --- | --- |
| Both repositories' code and histories, prompts, specifications and experiment index | Explain the methods and show their development over time | Already in Git; history size is not included in the data measurements below |
| The original posts actually used, with exact experiment selections and training/validation/test splits | Supply the same inputs without republishing unused Nostr collections | **10,571 confirmed used note IDs; 3.80 MiB** as compact ID/text JSONL. This representation has been measured, not packaged; signed-event metadata and media are additional |
| Saved subject inputs for the 37 official hierarchy runs | Reuse the actual generated subjects consumed by those runs | **Nine distinct files, 407.17 MiB**; exact files are listed below |
| Prepared fine-tuning data and its source records | Repeat the training with the same teacher answers and splits | The four prepared JSONL files total **63.74 MiB**; dataset manifest, teacher responses and receipts are additional |
| Frozen experiment inputs/settings, saved answers, failed attempts and producer receipts | Show exactly what was submitted, returned and reused | Existing plans, configurations, manifests and result ledgers total **58.85 GiB**. This is a candidate-file measurement, not a completed publication selection |
| Final or last partial hierarchies, run status and failure evidence | Show the outcome of each construction experiment | Complete selection not yet isolated; the exported HR39 viewer files are **1.80 MiB** |
| Evaluation answers, raw judgments, final grades, per-note scores and recorded reviews | Allow inspection of why results received their scores, including intermediate training stages | Complete selection not yet isolated. The L1 summary is **3.37 MiB**; its 117 directly declared sources total **441.33 MiB**, with upstream dependencies additional |
| Saved vectors, their source bindings and consequential clustering results | Preserve the numerical evidence used to construct hierarchies | Existing binary vectors/numeric arrays total **3.80 GiB**; the clustering-file decision is separate below |
| All 17 evaluated adapters, with configurations and training records | Let readers run every evaluated training stage and compare the models behind the reported results | **6.78 GiB** of weights; exact checkpoints below. Base models remain upstream dependencies |
| Qwen checkpoint-1000 training state and parent-checkpoint metadata | Preserve the starting point of the recorded two-pass continuation | **0.87 GiB** for `training-state.pt`; metadata additional |
| Research artifacts found only in Git history | Preserve their evidence and original commit associations before history cleanup | **294 blobs, 19.45 MiB**; potential overlap with current files is not subtracted |

Sizes are uncompressed logical bytes. Rows overlap: posts occur inside prepared
inputs, and evaluation sources occur among the saved experiment records. **Do
not add the rows to obtain a release total.** A final total needs the remaining
file selection and duplicate-content checks. The earlier **534.71 GiB** measures
the broad candidate inventory, not the proposed download size.

The used-post count comes from recorded attempts, official hierarchy selections,
training/validation selections and saved evaluations. Preparation alone does not
establish use. Some older unstructured records remain incompletely linked, so
10,571 is the confirmed set rather than a claim of exhaustive coverage.

## Start small

| Task | Planned download | Selected contents | Size |
| --- | --- | --- | ---: |
| Browse the saved HR39 hierarchy | `hr39-viewer` | `hierarchy.json` and `notes.json` | 1.80 MiB |
| Try subject identification or repeat HR36 construction | `corpus-42d5ce5211a1` | HR36's 1,000 posts and saved **ASv6.100** answers | 41.37 MiB |
| Read the fine-tune comparison | `fine-tune-comparison` | `analysis.json` and `verification.json` | 3.37 MiB |

These are the five files in the [reproduction guide](reproduce.md) and
[checksum list](reproduction.sha256). Each row is independently useful; the
combined selected contents total 48,809,988 bytes (46.55 MiB).

The viewer needs the Oracle viewer build. Subject identification needs the
runner and provider authentication. HR36 construction additionally needs the
[SSE checkpoint and tokenizer/configuration files](../generate-hierarchy.md#3-obtain-the-encoder-files)
and performs new model calls. Reading the saved comparison needs no models.
The small downloads do not include the underlying experiment receipts.

## Corpora and fine-tunes

Keep one copy of each of these **nine recorded hierarchy corpora**. The names
below identify existing inventory entries, not published Hugging Face URLs.
The full SHA-256 and exact source file are in [bundle-files.csv](bundle-files.csv).
[corpora.csv](corpora.csv) identifies their runs, and [hierarchy.csv](hierarchy.csv)
records the ordered selections. Shared inputs do not imply identical selections.

| Corpus ID | Existing file size |
| --- | ---: |
| `corpus-18370b4772fe` | 2.14 MiB |
| `corpus-1f87b7c853be` | 1.37 MiB |
| `corpus-42d5ce5211a1` | 41.37 MiB |
| `corpus-69ac6d8baaba` | 4.29 MiB |
| `corpus-6b8fa763d117` | 19.67 MiB |
| `corpus-8328bfb1e3ff` | 82.05 MiB |
| `corpus-d0c063c163c6` | 41.08 MiB |
| `corpus-da35889c86fa` | 8.76 MiB |
| `corpus-dbec79575b8a` | 206.45 MiB |

These files contain posts and generated subjects. Every post ID in these nine
files has evidence of use somewhere in the audited experiments, although an
individual hierarchy may use only a subset. Preserve historical/deprecated
labels for generated data derived from subject prompts older than **ASv6.100**.

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
this proposed publication;
this does not exclude its validation results.

All three pilots use the same 1,000 training, 100 validation and 200 test notes.
Qwen's continuation repeats the same training notes. Preserve the four prepared
files identified by the training manifests: `train.jsonl` (44,000,367 bytes),
`evaluation.jsonl` (3,661,939), `references.jsonl` (11,847,618) and `test.jsonl`
(7,328,857), totaling **66,838,781 bytes**. The prepared test inputs are distinct
from the sealed pass-two generated answers. Include the dataset manifest, exact
split/order records, teacher answers and their producer receipts as well.

Keep each run's `manifest.json`, `training-plan.json`, report, checkpoint metadata
and saved validation/unsealed test results. The four manifests already named by
`training-records-*` total 402,563 bytes; they are only part of those records.
For repeating the recorded Qwen continuation, also retain checkpoint-1000's
`training-state.pt` (**934,812,685 bytes**) and the complete parent-checkpoint
metadata. Inference does not read optimizer state. Portable inference and training
instructions still need validation against the complete dependencies.

## Files proposed to stay offline

These are proposed publication omissions, not deletion instructions. Keep the
originals. Retain an otherwise omitted file whenever it is a required frozen
input or the only evidence explaining a result or failure.

| Files | Existing size | Proposed treatment |
| --- | ---: | --- |
| Eight preparation adapters, at steps 1 and 3 | **3.23 GiB** | Keep weights offline; publish preparation measurements and relevant results. These checked GPU/numerical operation rather than model quality |
| Other optimizer/training states, including preparation states | **19.17 GiB** | Keep offline unless resuming those additional checkpoints is a public requirement. Keep the Qwen continuation parent state above |
| Routine `scheduling.jsonl` histories | **98.66 GiB** | Keep offline, except records supporting performance findings or otherwise unexplained failures |
| 1,737 successive `collection-*.json` grading snapshots | **49.58 GiB** | Propose omission after checking historical/transitive consumers. All seven current grading states point to final `grades.json`; keep final grades, raw judgments and source answers |
| Three identical upstream SSE encoder weight copies | **3.72 GiB** stored; **1.24 GiB** distinct | Refer to the pinned upstream checkpoint. Mirror one copy only if needed for availability |
| Unused Nostr collections, dependency caches and rebuildable executables | Not separately totaled | Exclude; preserve exact historical source or runtime files when they are otherwise unrecoverable or required by frozen checks |

Omitting optimizer files means the unchanged complete-training-run verifier
cannot validate every original checkpoint seal. Adapter use and resuming the
published continuation have different file requirements; document only the
checks actually supported by the published selection.

## Clustering files: decision still open

There are **117.69 GiB of requests** and **109.98 GiB of results** across the
candidate inventory. These repeat expanded numerical inputs and include large
diagnostic data. Propose publishing raw vectors, exact settings/state mappings,
cluster memberships and trees, while omitting reproducible expanded requests
and unused diagnostics only after validating that reduction for the selected runs.

Two read-only checks support investigating this reduction:

- An HR22 request containing 728 vectors was reconstructed with production code;
  all **11,872,508 bytes** matched the original SHA-256.
- The fields retained by the existing hierarchy reader for one HR30 result
  occupy **2,361,438 bytes**, compared with **901,125,385 bytes** in the original.

These samples do not establish a smaller size for every historical run. The
current whole-hierarchy verifier hashes the original complete files; a smaller
result cannot pass merely because it contains the fields used later. Keep
original hashes and distinguish inspection of a reduced result from verification
of the full original run. No reduction has been applied to the artifacts.

The HR22 `trial-baseline-restored-v1/hdbscan-00000/request.json` and `result.json`
are also direct inputs to native experiments, with 13 bindings each. Retain their
exact bytes (**22,205,200 bytes combined**) unless validated reconstruction
supplies identical files. Other frozen-input exceptions must also survive the
selection; omitting all files by basename would be incorrect.

## Full experiment evidence

The inventory groups the remaining candidates into **232 evidence bundles**.
These are discovery groups, not an instruction to publish their entire contents.
Select evidence by its role above. Keep the original collection names and file
associations, including failed, interrupted and superseded work.

Use an experiment's `collection` in [experiments.csv](experiments.csv), then
[bundle-collections.csv](bundle-collections.csv), to locate its evidence group.
Collections containing only Git-delivered files have no evidence download.
Official hierarchy entries span multiple collections: the run's history,
inputs and original response producers can be in different groups. An
`evidence-hrNN` name identifies that group of artifacts; it is not a claim
that the complete run can already be verified from that download alone.

Shared corpora, adapters, training records and the small saved results above
have separate inventory entries. Evidence groups name those entries where their
file lists refer to them. The `historical-git-artifacts` entry identifies the
**294 artifact blobs** in
[historical-files.csv](historical-files.csv), with their original associations
in [historical-uses.csv](historical-uses.csv), before eventual history cleanup.

### What a complete evidence download must include

For each native experiment, retain the frozen plan and prepared files, its run
manifest, result ledger and recorded runner/worker upgrades. Resolve each
source binding using both its original path and expected hash. Include the
exact inputs and the original responses and receipts used by reused answers.
Add required inputs read by project adapters as well; the runner's `verify`
command does not check every transitive adapter input.

The publisher must finish that selection before publishing a bundle as
verifiable. Add required evidence to that bundle or name a shared download
containing it. Readers should receive a complete list of required downloads,
including the total download size, and extract them together. They should not
have to follow the research machine's paths or discover missing producer files.

The current `known_required_bundles` lists record only the separate downloads
identified by the selected file lists and explicit adapter/training relations.
**They are not complete dependency lists for the native experiments.**
[dependencies.csv](dependencies.csv) consolidates bindings and retains only an
example consumer, so it cannot establish every experiment's dependencies.
Complete lists must come from the frozen plans and producer receipts, followed
by [staged verification](open-items.md#prepare-verification-metadata).

Historical inputs sharing an original path can have different bytes. Keep each
required version and its hash. The current location metadata supports one
destination per original path; conflicting versions cannot share that mapping.
Such groups need separate compatible packages or a separately implemented and
tested runner change before verification can be completed. Three historical
state versions remain unlocated; keep the affected experiments' limitation
visible instead of substituting today's files.

## File selection and archive layout

The broad inventory comes from commit
`10f1f94385bfa17d163c00d59cda23427a1988c1`; its grouping tables were added in
`38b7d64552023e1ea4edcc5ffe722b9d4d9b8bdf`. They identify candidates and existing
reader dependencies. They have not been narrowed to this proposal:

| Table | Meaning |
| --- | --- |
| [bundles.csv](bundles.csv) | Candidate bundle IDs, file counts/bytes, known dependencies and remaining verification work |
| [bundle-files.csv](bundle-files.csv) | 68 exact candidate files for the small results, nine corpora, adapters, training state and training manifests |
| [bundle-collections.csv](bundle-collections.csv) | Assignment of all 1,186 original collections to evidence groups or Git |
| [download-targets.csv](download-targets.csv) | Required downloads and additional runtime/model requirements for 74 reader tasks |

After the contents are agreed, use [file-lists.csv](file-lists.csv) and the
[member-path rules](files/README.md) to name the exact selected files. Retain
bound exceptions and mark unresolved files separately. A `delivery=archive` row
records the earlier delivery classification, not approval to upload that file.
Likewise, the **282 inventory bundles** are not a promise of 282 public downloads.
No directory glob or whole-checkout copy replaces the reviewed file list.

The size audit checked 844,229 candidate source files, including relocated data:
574,140,019,176 bytes (**534.71 GiB**) before compression. Counts differ from
shared archive-member counts because multiple source copies can map to one
member. All 53 adapter/state/encoder binaries were hashed in bounded chunks.
Known identities establish **3.34 GiB** of exact extra copies; most evidence has
not been fully compared for duplication. Equal names or sizes do not establish
equal contents. None of these measurements is a final publication total.

Within the release, keep the existing `datasets/`, `evidence/` and `history/`
paths. All pieces required for one verification package share an extraction
root. Supply one consistent `experiment-locations.json` for that package; do
not overwrite it with a different bundle's mapping. Independent packages with
different mappings need independent extraction roots. The three small examples
can still share the root used by the reproduction guide.

Publish adapter weights/configurations as directly usable model files on Hugging
Face. Dataset repository layout, evidence archive boundaries and compression
remain open until the contents are settled. GitHub release-attachment limits
do not determine this layout. Preserve the paths required by the reproduction
guide, and link exact file versions and checksums from the GitHub index.

## Before downloads become available

Resolve the remaining evidence selection, particularly the clustering files,
then complete the exact input/producer selections. Review the selected contents
for sensitive information, and prepare the verification metadata. Then build
and test one bundle at a time, with the original storage unavailable during
the extraction test. Add URLs, archive checksums and measured download sizes
only for the files actually assembled. Preserve the original records throughout;
history cleanup remains the final publication preparation step.
