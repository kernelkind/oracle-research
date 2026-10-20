# Experiments and release files

This index connects the research to its inputs and saved results, including
unsuccessful trials and superseded approaches. Code and history will be published
on GitHub; reusable models and datasets will be hosted on Hugging Face. The
[publication plan](downloads.md) records the agreed contents and hosting split:
all 17 evaluated adapters on Hugging Face Models, and used inputs, parameters
and final experiment results on Hugging Face Datasets. The hierarchy exporter
now writes unsigned results and a small parameter/status record; other result
formats and exact file selections remain unfinished. Download links are not
available yet.

Start with the [37 official hierarchy runs](hierarchy.md). The index also covers
four training runs, 17 adapter checkpoints, individual prompt jobs and older
research collections. All nine subject corpora recorded for the official runs
have been located and checked against their recorded SHA-256 hashes.

## Where to start

| Work | Read first | Inventory |
| --- | --- | --- |
| Generate a hierarchy from posts | [Generation guide](../generate-hierarchy.md) | [Official hierarchy runs](hierarchy.csv) |
| Inspect or repeat recorded experiments | [Reproduction guide](reproduce.md) | [Five example input files and checksums](reproduction.sha256) |
| Understand the recorded hierarchy experiments | [Run overview](hierarchy.md) and [detailed findings](../recommendation-engine/hierarchy-runs.md) | [Run settings, source versions and corpus identities](hierarchy.csv) |
| Use or study the subject fine-tunes | [Training process and evaluation](../planning/fine-tuning-pilot-process.md) | [Adapter weights and training state](models.csv) |
| Study subject, mask, title, comparison and prominence trials | [Experiment workflow](../../sse_multivector/model-runner.md) | [Individual saved experiments and historical collections](experiments.csv) |
| Find an input or result file | [Collection sizes](collections.csv) | [Exact file list](files/README.md) |
| Review what to publish or find a reader's requirements | [Publication plan](downloads.md) | [Candidate bundles](bundles.csv) and [task requirements](download-targets.csv) |

The generation guide describes the current implementation. Historical trials
may require earlier code and prompt versions. A higher prompt version number is
not evidence of approval. Outputs derived from subjects older than **ASv6.100**
remain historical evidence; raw source posts are not deprecated by that rule.

## What the lists record

- [Experiments](experiments.csv): native saved experiment plans, the official
  hierarchy runs, and collections predating the native runner. These are
  different kinds of entries, not an additive count of independent experiments.
  Native entries retain prompt IDs, model settings, case counts and plan/manifest
  identities. Their source file contains the complete frozen settings.
- [Hierarchy runs](hierarchy.csv): recorded outcomes, generator versions, corpus
  identities and original generation code versions for each run. Status and
  input/output counts are transcribed from the comparison workbook; they have
  not been reevaluated here. The existing
  [parameter ledger](../recommendation-engine/hierarchy-parameters.csv) holds
  each run's exact ordered note selection. Sharing a corpus does not imply
  sharing a selection. [Shared corpora](corpora.csv) connect those identities to
  the located input files; [code versions](code-versions.csv) record whether
  the cited generation commits are available in the publication clones.
- [Inputs](inputs.csv): source files, measured SHA-256 identities where available,
  and example locations and consumers. Counts summarize repeated references;
  the exact file lists retain the individual source locations. These include
  collected subjects and other prepared inputs, not only raw post corpora.
  A blank consumer count means only an example consumer was indexed, not zero
  consumers.
- [Dependencies](dependencies.csv): recorded source locations, located copies,
  expected hashes and verification status, with repeated bindings consolidated.
  Each row gives an example consumer; the complete bindings remain in the saved
  experiment plans. [Specification inputs](spec-inputs.csv) retain the individual
  maintained-spec references. A located file with a different hash is not a
  substitute for the original input. [Exact alternatives](dependency-alternatives.csv)
  identify saved copies or recoveries with the expected hash without changing a
  frozen experiment's original binding. Recovery entries record their sources
  and exact procedure. [Input recovery findings](open-items.md#historical-input-recovery)
  explain the eleven recovered files and the three state versions still unlocated.
- [Runtime inputs](runtime-inputs.csv): hierarchy recipes and the encoder assets
  they reference, including recorded checkpoint and tokenizer/configuration
  hashes. Expected hashes and newly measured hashes are recorded separately;
  all 62 encoder bindings with recorded hashes match.
- [Models](models.csv): adapter weights, configurations and the separate
  optimizer/training state needed to resume training. Using an adapter requires
  its pinned base model; it does not require optimizer state.
- [Files](files/README.md): one row per candidate local file, its size, source location,
  proposed archive member path and any measured hash or existing Git blob ID.
  This is an explicit list, not permission to archive entire directories.
- [Historical files](historical-files.csv): additional artifact blobs found in
  Git history but absent from the current index. Each row identifies the exact
  blob and its size. The reported path is one historical name, not a complete
  record of every location where that content appeared. [Historical changes](historical-uses.csv)
  connect those blobs to their original commits and paths.
- [Source roots](source-roots.csv): names used to describe original artifact
  locations without embedding this machine's absolute home paths in the index.
- [Open items](open-items.md): missing references, provenance checks and work
  remaining before publication. [Detailed issues](issues.csv) preserve the
  individual findings.

## Release layout

GitHub holds code and its history, documentation, prompts, reusable experiment
specifications and this index. Hugging Face Models holds all 17 evaluated
adapters (6.78 GiB). Hugging Face Datasets holds used posts, prepared training
data, final unsigned hierarchies, standalone prompt answers, evaluation and
numerical results, and each experiment's parameters (roughly 0.5–1 GiB).

The [publication plan](downloads.md) defines those contents. The index will link
to exact published revisions and checksums. [Bundle assignments](bundle-collections.csv)
and other inventory tables still describe the broader original artifacts; they
have not been converted into the final export list. Dataset layout and the
remaining result schemas are open. The [hierarchy export format](downloads.md#automated-outputs)
is implemented for normal runs and [saved snapshots](reproduce.md#export-compact-hierarchy-results).
Existing research files and history have not been changed.

Preserve original frozen plans, answers and receipts locally. Their complete
working directories are not required public downloads. The current native
receipt verifier checks original files; it is not a verifier for the intended
compact outputs. Review exported data for sensitive information before release.

## Reproduction status

The [reproduction guide](reproduce.md) covers browsing HR39, preparing ASv6.100
on a recorded HR36 post, repeating HR36 construction with its saved subjects,
and reading the fine-tune comparison. It also explains `verify` for checking
saved prompt receipts after extraction using bundled location metadata.
Those checks describe current tools and original file formats. The guide also
documents the compact hierarchy export; published-download testing remains open.
Downloads, portable training/L1 recomputation and replay of historical
collections remain unfinished.
Fresh model answers need not match saved answers.

Generation commits, later audit/export commits and the publication commit serve
different purposes. Preserve their distinction when history cleanup changes
commit IDs, and provide a mapping for references affected by that cleanup.

## Inventory method and limits

The [inventory record](inventory.json) identifies the publication code snapshot,
counts and resource bounds. Discovery starts with tracked research files,
maintained specifications, the official hierarchy ledger, referenced artifact
directories and saved native experiment plans. Native plans provide source
bindings; saved request-history entries identify original response producers.
Discovery includes recorded paths on mounted external storage. Equivalent mount
and workspace paths were matched by device and inode, retaining one listed
location for each of those files; the relocated input contents were also hashed.

The file list records sizes without loading file contents. Identified inputs
are hashed in 1 MiB chunks. The discovery pass capped input hashing at 128 MiB;
the larger official HR39 corpus was checked separately. The follow-up checked
all 9,556 remaining indexed input bindings, including the 15 oversized inputs,
and all 62 recorded encoder bindings. Five additional historical-version
mismatches were resolved using exact Git copies or recoveries from saved plans.
The 42 plans exceeding the initial 32 MiB JSON read limit were then indexed
with a streaming reader. Their 34,091 source references all match located inputs;
[large-plan findings](open-items.md#large-experiment-plans) describe that check
and the nine plans without located result files. No discovered native plans
remain unparsed. Other evidence and final archives still need checksum
verification. File sizes and modification times are checked again at the end
to detect concurrent edits.

The historical-input checks add eleven recovered files to the explicit list.
Their complete contents were checked against the original expected hashes;
original source paths and expected hashes remain unchanged. The inventory record
separates the follow-ups from the discovery snapshot and lists their scope.

Build caches, virtual environments, runtime lock files, known credential containers and
unreviewed symlink targets are excluded. Known unit/integration fixture outputs
are excluded from the research catalogue. Original base-model download caches
are not selected simply because a training run used them. This is an inventory,
not a completed sensitive-information review: the actual proposed archive
contents still need that review before release.
