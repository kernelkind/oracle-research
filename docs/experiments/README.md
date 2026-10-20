# Experiments and release files

This index connects the research to its inputs and saved results, including
unsuccessful trials and superseded approaches. Code and history will be published
on GitHub; reusable models and datasets will be hosted on Hugging Face. The
[publication plan](downloads.md) records the agreed contents and hosting split:
all 17 evaluated adapters on Hugging Face Models, and used inputs, parameters
and final experiment results on Hugging Face Datasets. Compact exporters cover
hierarchies, native prompt studies, validation answers, grading results and
explicit numerical result families. Supported historical results have been
converted locally; [selected exports](publications.csv), their
[exact files](publication-files.csv) and [checksums](publication.sha256) are now
indexed. [Legacy review items](publication-gaps.csv) remain explicit. Downloads
are not available yet.

Start with the [37 official hierarchy runs](hierarchy.md). The index also covers
four training runs, 17 adapter checkpoints, individual prompt jobs and older
research collections. All nine subject corpora recorded for the official runs
have been located and checked against their recorded SHA-256 hashes.

## Where to start

| Work | Read first | Index |
| --- | --- | --- |
| Find converted final results | [Measured selection](downloads.md#measured-local-exports) | [Exports](publications.csv), [files](publication-files.csv) and [remaining review items](publication-gaps.csv) |
| Generate a hierarchy from posts | [Generation guide](../generate-hierarchy.md) | [Official hierarchy runs](hierarchy.csv) |
| Inspect or repeat recorded experiments | [Reproduction guide](reproduce.md) | [Five example input files and checksums](reproduction.sha256) |
| Understand the recorded hierarchy experiments | [Run overview](hierarchy.md) and [detailed findings](../recommendation-engine/hierarchy-runs.md) | [Run settings, source versions and corpus identities](hierarchy.csv) |
| Use or study the subject fine-tunes | [Training process and evaluation](../planning/fine-tuning-pilot-process.md) | [Adapter checkpoints and base versions](models.csv) |
| Study subject, mask, title, comparison and prominence trials | [Experiment workflow](../../sse_multivector/model-runner.md) | [Selected studies](experiments.csv) |
| Check publication coverage and limitations | [Open items](open-items.md) | [Remaining review items](publication-gaps.csv) |

The generation guide describes the current implementation. Historical trials
may require earlier code and prompt versions. A higher prompt version number is
not evidence of approval. Outputs derived from subjects older than **ASv6.100**
remain historical evidence; raw source posts are not deprecated by that rule.

## What the lists record

- [Publications](publications.csv): selected compact outputs, their source and
  trial identities, format, measured size and selection evidence. Saved hierarchy
  branches are outputs, not a count of independent trials.
- [Publication files](publication-files.csv) and [checksums](publication.sha256):
  every selected local payload and metadata file, including exact prepared inputs.
  The [remaining items](publication-gaps.csv) distinguish unsupported results,
  one missing configuration and older inventory groups needing review. An older
  group may include code/prompts already retained in Git; it is not automatically
  a missing public dataset.
- [Experiments](experiments.csv): 2,595 entries linked to selected results:
  2,547 standalone prompt preparations, 37 official hierarchy runs, four training
  runs and seven historical collections. These are different kinds of entries,
  not an additive count of independent experiments. Prompt IDs, model settings,
  case counts, provenance and plan/manifest identities are preserved. The
  publication columns link the corresponding compact exports. Internal jobs,
  warmups and other unselected entries remain in the local audit; outstanding
  historical evidence remains in [publication gaps](publication-gaps.csv).
- [Hierarchy runs](hierarchy.csv): recorded outcomes, generator versions, corpus
  identities and original generation code versions for each run. Status and
  input/output counts are transcribed from the comparison workbook; they have
  not been reevaluated here. The existing
  [parameter ledger](../recommendation-engine/hierarchy-parameters.csv) holds
  each run's exact ordered note selection. Sharing a corpus does not imply
  sharing a selection. [Shared corpora](corpora.csv) connect those identities to
  the located input files; [code versions](code-versions.csv) record the
  pre-rewrite availability check for the original generation commit IDs.
- [Input recovery findings](open-items.md#historical-input-recovery),
  [exact alternatives](dependency-alternatives.csv) and
  [reference resolutions](reference-resolutions.csv): recovered input identities,
  source locations and recovery procedures. A located file with a different hash
  does not replace an experiment's original input. The findings preserve the
  eleven recoveries and three state versions still unlocated. Selected exported
  input files and their hashes appear in [publication files](publication-files.csv).
- [Runtime inputs](runtime-inputs.csv): hierarchy recipes and the encoder assets
  they reference, including recorded checkpoint and tokenizer/configuration
  hashes. Expected hashes and newly measured hashes are recorded separately;
  all 62 encoder bindings with recorded hashes match.
- [Models](models.csv): adapter weights, configurations and the separate
  optimizer/training state needed to resume training. Using an adapter requires
  its pinned base model; it does not require optimizer state.
- [Historical files](historical-files.csv): artifact blobs identified in the
  original Git-history audit but absent from its index. Each row identifies the
  exact blob and its size. The reported path is one historical name, not a complete
  record of every location where that content appeared. [Historical changes](historical-uses.csv)
  connect those blobs to their original commits and paths.
- [Source roots](source-roots.csv): names used to describe original artifact
  locations without embedding this machine's absolute home paths in the index.
- [Open items](open-items.md): missing references, provenance checks and work
  remaining before publication. [Publication gaps](publication-gaps.csv) retain
  the individual outstanding conversion and collection-review items.

## Reading the research records

Research READMEs and findings retain the investigation's measurements,
interpretations and recorded judgments. Unlinked data file references identify
original saved artifacts outside this checkout. Historical inspection and replay
commands may require those originals.

Where a record has selected release data, it names the bundle's `publication`
ID in the [publication catalog](publications.csv). Search that exact ID in the
[file list](publication-files.csv) for its exported filenames and checksums.
The catalog records the source and export format; a selected bundle can cover
part of a study without recreating its original working directory.

These exports are still local. [Hosting and download preparation](downloads.md#before-downloads-become-available)
remains open. Some older collections still need
[conversion review](publication-gaps.csv); their maintained findings remain
readable here while that work is pending.

## Release layout

The agreed [public Git layout](downloads.md#public-git-contents) keeps code and
its history, tests, prompts and their provenance, authored findings, useful
documentation and a selected-study index. After the
[generated-data rewrite](downloads.md#generated-data-history-rewrite), local Git
object storage measured 32.87 MiB across both repositories at checkpoint
`d2e3a88c`, before subsequent documentation and lookup-support commits.
Compressed download size has not been measured.
The selected-study index is now in place. The exhaustive workspace catalogs
are preserved in the [local audit](downloads.md#local-audit-copy). The reviewed
28,307 generated run files are now untracked and remain locally at the same
paths. Source, prompts, authored plans and findings, reusable specifications and
fixtures stay tracked, along with 196 ambiguous files awaiting review. The
generated-data rewrite is complete; privacy and identity review remains open.

Hugging Face Models holds all 17 evaluated
adapters (6.78 GiB). Hugging Face Datasets holds used posts, prepared training
data, final unsigned hierarchies, standalone prompt answers, evaluation and
numerical results, and each experiment's parameters. The selected local files
currently measure 1.04 GiB; older-format review items remain explicit.

The [publication plan](downloads.md) defines those contents. The new
[publication file list](publication-files.csv) describes the exact local
selection. Hugging Face repository names, published revisions and download
testing remain open. The [implemented export formats](downloads.md#automated-outputs)
serve normal workflows and selected saved results. Unsupported historical
schemas need an explicit adapter; local conversion does not establish coverage
of the entire inventory. Original research files and the original Git history
are preserved locally.

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
documents the compact result exporters; published-download testing remains open.
Downloads, portable training/L1 recomputation and replay of historical
collections remain unfinished.
Fresh model answers need not match saved answers.

Research records now distinguish original file references from selected result
exports, as explained [above](#reading-the-research-records). The reviewed links
to removed generated files have been repaired. Some saved-result tests and
replay scripts still require original artifacts; their
[clean-checkout replay plan](open-items.md#original-file-links-and-replay)
remains open. Missing reports and unfinished conversions are recorded there too.

Generation commits, later audit/export commits and the publication commit serve
different purposes. Their original IDs remain in the evidence. The
[bundled Oracle commit mapping](commit-map.txt) supports historical source reads;
the [reproduction guide](reproduce.md#which-code-is-being-repeated) explains its
use and the remaining limits.

## Inventory method and limits

The [inventory record](inventory.json) separates the original discovery snapshot
from the current selected-study index. The full discovery catalogs are retained
locally with their hashes and original commit. Discovery started with tracked
research files,
maintained specifications, the official hierarchy ledger, referenced artifact
directories and saved native experiment plans. Native plans provide source
bindings; saved request-history entries identify original response producers.
Discovery includes recorded paths on mounted external storage. Equivalent mount
and workspace paths were matched by device and inode, retaining one listed
location for each of those files; the relocated input contents were also hashed.

The original file list recorded sizes without loading file contents. Identified
inputs were hashed in 1 MiB chunks. The discovery pass capped input hashing at
128 MiB;
the larger official HR39 corpus was checked separately. The follow-up checked
all 9,556 remaining indexed input bindings, including the 15 oversized inputs,
and all 62 recorded encoder bindings. Five additional historical-version
mismatches were resolved using exact Git copies or recoveries from saved plans.
The 42 plans exceeding the initial 32 MiB JSON read limit were then indexed
with a streaming reader. Their 34,091 source references all match located inputs;
[large-plan findings](open-items.md#large-experiment-plans) describe that check
and the nine plans without located result files. No discovered native plans
remain unparsed. Other evidence and final archives still need checksum
verification. The original checks compared file sizes and modification times
again at the end to detect concurrent edits.

The historical-input checks add eleven recovered files to the explicit list.
Their complete contents were checked against the original expected hashes;
original source paths and expected hashes remain unchanged. The inventory record
separates the follow-ups from the discovery snapshot and lists their scope.
The public file list contains only the selected compact exports, rather than
every candidate file encountered during that audit.

Build caches, virtual environments, runtime lock files, known credential containers and
unreviewed symlink targets are excluded. Known unit/integration fixture outputs
are excluded from the research catalogue. Original base-model download caches
are not selected simply because a training run used them. This is an inventory,
not a completed sensitive-information review: the actual proposed archive
contents still need that review before release.
