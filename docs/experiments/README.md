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
  The [conversion-gap list](publication-gaps.csv) is now empty. TRUE10's final
  graph is selected with its existing run configuration and plan.
  The 33 formerly unsupported entries now have selected final evidence or an
  explicit intermediate/duplicate disposition.
  The [109-group review](open-items.md#historical-collection-review) resolved 32
  groups needing no separate result export; the other 77 now have selected evidence.
  ASv6.100's final quality summary and four frozen agent rubrics are selected as
  original Markdown; the [study record](../../sse_multivector/subject-prompt-goal-v1/asv6.100-generalization-v1/README.md#publication-files)
  identifies their paths alongside the six existing answer/review bundles.
- [Experiments](experiments.csv): 2,684 entries linked to selected results:
  2,547 standalone prompt preparations, 37 official hierarchy runs, four training
  runs, 92 historical collections and four later-located historical prompt
  studies. These are different kinds of entries,
  not an additive count of independent experiments. Prompt IDs, model settings,
  case counts, provenance and plan/manifest identities are preserved. The
  publication columns link the corresponding compact exports. Internal jobs,
  warmups and other unselected entries remain in the local audit; outstanding
  historical evidence remains in [publication gaps](publication-gaps.csv).
  The historical collections include 33 title/description study groups with 506
  saved answers, recorded reviews and final selections. Their 24 failed attempts
  and reused answers remain distinguishable; see the
  [publication checks](reproduce.md#historical-title-study-checks).
  Six subject/mask collections add 123 study and review entries with 1,965 saved
  responses, recorded assessments, corrections and parameters. These responses
  include reused answers; they are not a count of independent trials. See the
  [subject/mask checks](reproduce.md#historical-subject-and-mask-study-checks).
  Another 22 collections link 21 early/standalone prompt entries and three manual
  prominence studies, retaining 514 final answers and their recorded reviews.
  They preserve partial outcomes and reused baselines; the existing native
  prominence bundles stay separate. See the
  [early prompt and prominence checks](reproduce.md#early-prompt-and-manual-prominence-study-checks).
  Four further collections retain nine real-note segmentations, two fine-region
  title studies and 13 frontier comparison entries. They add 283 completed
  answers and three saved partial answers, with reused baselines and original
  review states kept distinct. See the [title/segmentation checks](reproduce.md#fine-region-title-and-real-note-segmentation-checks)
  and [frontier checks](reproduce.md#frontier-comparison-checks).
  The archived-baseline collection adds four bundles of final CREC answers,
  segments and geometry measurements. Assembled answers and reused work remain
  explicitly identified; see the [archived-baseline checks](reproduce.md#archived-baseline-checks).
  The hierarchy/navigation/performance batch adds 28 bundles of saved hierarchies, partitions,
  manual reference fixtures, navigation measurements and performance results.
  See the [shared export command and limits](reproduce.md#saved-hierarchy-navigation-and-performance-checks).
  Eleven SSE representation studies also retain their final numerical comparisons
  and fixed inputs; these used manually supplied spans, without subject or mask
  prompt generation. See the [representation checks](reproduce.md#sse-representation-study-checks).
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
remains open. [All reviewed conversion gaps](publication-gaps.csv) are closed;
this does not resolve the separate reproduction and privacy limits.

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

Hugging Face Models will host all 17 evaluated
adapters (6.78 GiB). Hugging Face Datasets will host used posts, prepared training
data, final unsigned hierarchies, standalone prompt answers, evaluation and
numerical results, and each experiment's parameters. The selected local files
currently measure 1.10 GiB; missing evidence and reproduction limits remain explicit.

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
remains open. The four located ASv6.26–ASv6.28 reports and their selected compact
results are now included; broader historical conversion gaps remain explicit.

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
