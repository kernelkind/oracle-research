# Planned research downloads

Choose downloads by what you want to do. Browsing a result, generating a new
hierarchy and checking the original experiment records need different files.
**These downloads have not been packaged or published yet.** Sizes below are
selected file sizes before compression, additional dependencies and packaging.

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

There is one download for each of the **nine recorded hierarchy corpora**.
Names use the first twelve characters of the corpus SHA-256; the full hash and
exact file are in [bundle-files.csv](bundle-files.csv). [corpora.csv](corpora.csv)
identifies the runs using each corpus, and [hierarchy.csv](hierarchy.csv)
identifies their ordered selections and source versions. A shared corpus does
not imply that two runs used the same notes or order. These corpora contain
posts and prepared subjects; they are distinct from the fine-tuning datasets.

Each of the **17 adapter checkpoints** has its own download containing
`adapter_model.safetensors` and `adapter_config.json`:

| Adapter family | Checkpoints | Selected size per adapter, approximately |
| --- | --- | ---: |
| Qwen pilot | 200, 400, 600, 800, 1000 | 445.41 MiB |
| Qwen continuation | 2000, 3000 | 445.41 MiB |
| Gemma dense pilot | 200, 400, 600, 800, 1000 | 467.14 MiB |
| Gemma MoE pilot | 200, 400, 600, 800, 1000 | 297.85 MiB |

Names distinguish the training run as well as the checkpoint, for example
`adapter-qwen-pilot-checkpoint-1000`. Every adapter requires its pinned base
model, recorded in [models.csv](models.csv) and [bundles.csv](bundles.csv).
Base models remain upstream downloads. Portable inference instructions still
need validation.

Optimizer/training state has **17 separate downloads**. It is needed to resume
training, not to use the adapters. Four small `training-records-*` downloads
hold the corresponding training manifests, including frozen configuration,
data identities, code hashes and environment records. Resuming also needs the
exact prepared training data and runtime. Selecting those complete dependencies
and testing portable training remain unfinished; a manifest alone is not a
training dataset. The two later Qwen checkpoints belong to the continuation
run, whose additional starting-state requirements remain in its manifest.

## Full experiment evidence

The remaining files are grouped into **232 evidence bundles**. Related trials
share a bundle; large hierarchy runs retain separate groups. The original
collection names and file paths remain available, including failed, interrupted
and superseded work. Grouping does not establish approval or change the
deprecated status of outputs derived from subjects earlier than **ASv6.100**.

Use an experiment's `collection` in [experiments.csv](experiments.csv), then
[bundle-collections.csv](bundle-collections.csv), to locate its evidence group.
Collections containing only Git-delivered files have no evidence download.
Official hierarchy entries span multiple collections: the run's history,
inputs and original response producers can be in different groups. An
`evidence-hrNN` name identifies that group of artifacts; it is not a claim
that the complete run can already be verified from that download alone.

Shared corpora, adapters, training states, training manifests and the small
saved results above are selected separately. Evidence groups name those
downloads where their file lists refer to them. A separate
`historical-git-artifacts` bundle retains the **294 artifact blobs** in
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

The plan is based on inventory commit
`10f1f94385bfa17d163c00d59cda23427a1988c1`. Four tables define it:

| Table | Meaning |
| --- | --- |
| [bundles.csv](bundles.csv) | Bundle IDs, selected file counts/bytes, known dependencies and remaining verification work |
| [bundle-files.csv](bundle-files.csv) | 68 explicitly selected files for the small results, nine corpora, adapters, training state and training manifests |
| [bundle-collections.csv](bundle-collections.csv) | Assignment of all 1,186 original collections to evidence groups or Git |
| [download-targets.csv](download-targets.csv) | Required downloads and additional runtime/model requirements for 74 reader tasks |

For an evidence bundle, take only `delivery=archive` rows from the collections
assigned to it, using [file-lists.csv](file-lists.csv) and the
[exact member-path rules](files/README.md). Exclude members selected separately
in `bundle-files.csv`; those are supplied by the named shared downloads.
Deduplicate identical member paths within each bundle. No directory glob or
whole-checkout copy replaces the explicit file list. Files delivered through
Git remain in Git.

All **850,995 inventory rows** have a disposition under those rules. There are
**282 planned bundles** in total, including the historical Git artifacts.
The selected contents total 826,198 member occurrences and 573,370,600,900
bytes across bundles. This includes a small amount of shared content in more
than one evidence group; it is not the inventory's globally deduplicated total.
Neither figure includes unselected producer dependencies, generated release
metadata or archive overhead. It is not an estimate of compressed downloads.

The table checks covered every inventory row, bundle totals, dependency
references, all nine corpus identities and the 17 adapter/base-model pairings.
They checked the five reproduction-file hashes against the existing checksum
list. This was a metadata check with a peak memory use of about 387 MiB;
artifact bytes were not rehashed. Blank hashes still require measurement before
packaging.

Within the release, keep the existing `datasets/`, `evidence/` and `history/`
paths. All pieces required for one verification package share an extraction
root. Supply one consistent `experiment-locations.json` for that package; do
not overwrite it with a different bundle's mapping. Independent packages with
different mappings need independent extraction roots. The three small examples
can still share the root used by the reproduction guide.

Use `.tar.gz` for each completed bundle. Split an oversized compressed stream
into numbered parts of at most **1,900,000,000 bytes**; all parts are required
to reconstruct that archive. Publish exact part names, sizes and SHA-256 hashes,
with the complete extraction command beside the download links. A bundle and
a GitHub attachment are therefore not necessarily the same thing.

GitHub allows up to 1,000 assets per release and requires each to be under
2 GiB. Check actual compressed sizes and the final attachment count, including
checksum and metadata files. The 282 logical groups do not prove that the
finished release fits those limits. See [GitHub's release limits](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).

## Before downloads become available

Complete the missing input/producer selections, review the selected contents
for sensitive information, and prepare the verification metadata. Then build
and test one bundle at a time, with the original storage unavailable during
the extraction test. Add URLs, archive checksums and measured download sizes
only for the files actually assembled. Preserve the original records throughout;
history cleanup remains the final publication preparation step.
