# Experiments and results

This index connects the experiments to their inputs, settings and final saved
results, including failed trials and superseded approaches. Code and source
history belong in Git; selected data and all 17 evaluated adapters will be on
Hugging Face. Downloads are not available yet. See [contents and formats](downloads.md).

## Where to start

| Goal | Read |
| --- | --- |
| Generate a hierarchy from posts | [Generation guide](../generate-hierarchy.md) |
| Browse a saved hierarchy without models | [HR39 browsing instructions](reproduce.md#browse-hr39-without-running-models) |
| Understand hierarchy outcomes | [Official run overview](hierarchy.md) and [detailed findings](hierarchy/runs.md) |
| Inspect subject fine-tuning | [Methods and results](subject-extraction/fine-tuning.md) and [saved comparison](reproduce.md#inspect-the-fine-tune-comparison) |
| Use an adapter or repeat training | [Adapter loading](reproduce.md#use-a-subject-adapter) and [training instructions](reproduce.md#run-subject-fine-tuning) |
| Understand representation experiments | [Mask/context controls](representation/mask-context.md), [communicated meanings](representation/communicated-meaning.md) and [partition pilot](representation/partition-pilot.md) |
| Understand controlled segmentation tests | [Results](fine-segmentation/controlled-run-v1-results.md) and [frozen methods](fine-segmentation/README.md) |
| Inspect content ordering experiments | [Prominence and sorting findings](content-ranking.md) |
| Understand resource limits | [Scaling evidence](scalability.md) and [hierarchy performance](hierarchy/performance.md) |
| Locate another recorded study | [Study index](experiments.csv) and [result-bundle catalog](publications.csv) |
| Check what can be reproduced | [Reader instructions](reproduce.md) and [evidence limits](open-items.md) |

The generation guide describes the current implementation. Earlier trials may
need their recorded code and prompts. A higher prompt number does not establish
approval. Results derived from subjects older than **ASv6.100** remain historical
evidence; that rule does not deprecate the original source posts.

## Reading the research records

[experiments.csv](experiments.csv) identifies 2,488 selected entries: 2,351 native
prompt entries, 37 official hierarchies, four training runs, 92 historical
collections and four historical prompt studies. These categories overlap and
are not an additive count of independent experiments. Reused answers are not
new trials. 196 preparations proven never executed are excluded; three snapshots
retain unknown execution status.

A study's `publication` field identifies its compact input/result bundle in
[publications.csv](publications.csv). The catalog has 2,989 selected bundles plus
one shared-content row. Find that ID in the dataset's `dataset.json`, then
[verify and restore](reproduce.md#verify-and-restore-the-dataset) its files.
Shared values appear once in the physical dataset; restoration recovers the
original compact JSON for ordinary inspection and supported consumers.

Restoration does not recreate whole original workspaces, native plans or receipt
directories. Scientific records distinguish original observations, agent
assessments and actual user judgments. A completed run or successful integrity
check does not establish semantic quality.

## Settings and provenance

| Record | Contents |
| --- | --- |
| [Hierarchy runs](hierarchy.csv) and [parameters](hierarchy/parameters.csv) | Recorded outcomes, code/prompt versions and exact ordered note selections |
| [Corpora](corpora.csv) | Nine original subject-corpus identities and run associations |
| [Runtime inputs](runtime-inputs.csv) | Encoder/checkpoint/configuration bindings; all 62 recorded hashes match located originals |
| [Models](models.csv) | All 17 adapters, matching configurations, pinned base revisions and training manifests |
| [Input alternatives](dependency-alternatives.csv) and [reference resolutions](reference-resolutions.csv) | Exact historical input versions and unresolved replay constraints |
| [Code versions](code-versions.csv) and [commit map](commit-map.txt) | Original producer identities and available source-revision mappings |
| [Inventory](inventory.json) | Dataset and exporter code pins, counts and category sizes |

Original revision IDs and hashes remain evidence. Source preserved at the
pre-cleanup commit is a later retained copy unless verified as the actual
producer. See [source lookup](reproduce.md#which-code-is-being-repeated) and its
[known gaps](open-items.md#source-versions).

## Availability and tested scope

Hugging Face Models will contain all 17 evaluated adapters (6.78 GiB). Hugging Face
Datasets will contain used inputs, parameters and final results: 844.00 MiB prepared
locally, with repeated content stored once. Full upstream models, optimizer
state, unused corpora, intermediate vectors and whole native run directories are
outside this selection. The [format reference](downloads.md) explains each output.

A small complete generation/browsing workflow passed in a fresh Linux VM.
HR39 browsing, saved fine-tune comparison and recorded-input preparation also
passed locally. Hosted downloads and fresh GPU reader runs remain unverified.
[Evidence limits](open-items.md) identify missing input versions and scientific
qualifications. Public repository revisions and publication approval remain open.
