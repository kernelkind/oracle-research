# Experiments and results

This index connects the research to its used inputs, settings and final saved
results, including unsuccessful trials and superseded approaches. Code and
history will be on GitHub; datasets and all 17 evaluated adapters will be on
Hugging Face. The files are prepared locally; downloads are not available yet.
See [contents, hosting and sizes](downloads.md).

## Where to start

| Goal | Read |
| --- | --- |
| Generate a hierarchy from posts | [Generation guide](../generate-hierarchy.md) |
| Browse a saved hierarchy without models | [HR39 browsing instructions](reproduce.md#browse-hr39-without-running-models) |
| Understand official hierarchy outcomes | [Run overview](hierarchy.md) and [detailed findings](../recommendation-engine/hierarchy-runs.md) |
| Inspect the fine-tune comparison | [Saved scores](reproduce.md#inspect-the-fine-tune-comparison) and [training process/results](../planning/fine-tuning-pilot-process.md) |
| Use an adapter or repeat training | [Adapter loading](reproduce.md#use-a-subject-adapter) and [training instructions](reproduce.md#run-subject-fine-tuning) |
| Inspect historical trials | [Study index](experiments.csv), [bundle catalog](publications.csv) and [reproduction guide](reproduce.md) |
| Check evidence limits | [Open items](open-items.md) |

The generation guide describes the current implementation. Historical trials
may need earlier code and prompts. A higher prompt version is not evidence of
approval. Outputs derived from subjects older than **ASv6.100** remain historical
evidence; raw source posts are not deprecated by that rule.

## What the lists record

- [Experiments](experiments.csv): 2,488 selected entries: 2,351 native prompt
  entries, 37 official hierarchies, four training runs, 92 historical collections
  and four historical prompt studies. These kinds overlap and are not an
  additive count of independent experiments. Frozen settings and provenance
  connect entries to their final evidence. The dataset excludes 196 proven
  unexecuted preparations and retains three execution-unknown snapshots.
- [Publications](publications.csv): 2,989 selected input/result bundles plus one
  shared-content row. The dataset's `dataset.json` contains exact physical-file
  and restored-file hashes; see [the manifest](downloads.md#dataset-manifest).
- [Hierarchy runs](hierarchy.csv): recorded status, coverage, generator versions,
  corpora and original code versions. [Parameters](../recommendation-engine/hierarchy-parameters.csv)
  preserve each exact ordered note selection; [corpora](corpora.csv) identify the
  nine original subject corpora. All nine recorded corpus hashes match located files.
- [Runtime inputs](runtime-inputs.csv): encoder checkpoint/configuration bindings.
  Expected hashes and measured hashes remain separate; all 62 recorded hashes match.
- [Models](models.csv): all 17 adapter/configuration pairs and pinned upstream
  models. Optimizer state and upstream model copies are outside the selection.
- [Exact input alternatives](dependency-alternatives.csv) and
  [reference resolutions](reference-resolutions.csv): matching historical
  versions, recoveries and expected absent intermediates. Three state-file
  versions remain unlocated; a current file cannot replace them.
- [Code versions](code-versions.csv) and [commit map](commit-map.txt): original
  source provenance and rewritten-source resolution. The code-version table
  records its original pre-rewrite availability check.
- [Historical files](historical-files.csv) and [changes](historical-uses.csv):
  original artifact blobs and commit associations. Removed generated blobs are
  not recovered by looking up public source history.
- [Source roots](source-roots.csv): names for original artifact locations.
- [Inventory](inventory.json): current selection counts, category sizes,
  provenance hashes and prepared dataset pin.

## Reading the research records

Research READMEs and findings preserve measurements, interpretations and
attributed judgments. Unlinked data-file paths identify original artifacts
outside this checkout; historical inspection commands may require those files.
A study with selected data names its `publication` ID in the
[bundle catalog](publications.csv). Find that ID in the dataset manifest to locate
its files. A bundle may cover part of a study without recreating the original
working directory.

Physical files can contain numeric `$ref` values pointing to shared content.
[Verify and restore](reproduce.md#check-the-converted-local-selection) before
using a consumer that expects the original compact JSON. Restoration recreates
compact exports, not native experiment directories or complete receipt packages.

## Release layout

Git contains code, prompts, findings, useful instructions and this index.
Hugging Face Models will contain all 17 evaluated adapters (6.78 GiB).
Hugging Face Datasets will contain used inputs, parameters and final results:
844.00 MiB prepared locally, with repeated content stored once. Exact category
sizes and format contracts are in the [publication contents](downloads.md).

## Reproduction status

The [reproduction guide](reproduce.md) covers HR39 browsing, ASv6.100 preparation
on a recorded post, HR36 construction from saved subjects, fine-tune comparison,
adapter use and training. The [tested scope](reproduce.md#what-has-been-tested)
distinguishes preparation and saved arithmetic from fresh inference or grading.
Hosted downloads, fresh GPU reader runs and some historical replay paths remain
unverified. Fresh model answers need not match saved answers.

Original source revisions resolve through the bundled commit map; see
[which code is being repeated](reproduce.md#which-code-is-being-repeated).
Some historical tests require original artifacts absent from compact exports.
The [remaining limitations](open-items.md) identify these cases. Closed conversion
gaps do not establish exhaustive all-history coverage or complete reproduction.
Final release-content review and publication approval remain open.

## Inventory method and limits

Discovery used tracked research findings/specifications, the official hierarchy
ledger, saved native plans and referenced artifact locations. Recorded source
hashes distinguish exact historical inputs from current files. Recovery findings
and unresolved versions remain explicit in [open items](open-items.md#input-versions).
The public selection contains used inputs and final evidence, rather than the
full working-source inventory. Build caches, environments, credential containers,
unused corpora and intermediate arrays are outside it.
