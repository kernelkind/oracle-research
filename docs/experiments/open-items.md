# Before publication

This records findings from the source audit and remaining publication work. The
[publication plan](downloads.md) now selects used inputs, parameters and final
results, with all 17 evaluated adapters. The public [study index](experiments.csv)
contains selected studies, runs and collections. The complete original index
and discovery tables are preserved locally under
`target/publication-audit/index-before-simplification-1f3d541c/docs/experiments/`.
The audit counts below describe that broader source inventory. Nothing has been
uploaded or approved for public release.

## Input versions

All nine official subject corpus hashes match located files. The 151 input
bindings to relocated storage were also checked against their recorded hashes.

There are **26 source bindings whose current contents differ from the recorded
hash**. [Exact alternatives](dependency-alternatives.csv) identify a matching
saved or recovered copy for **23** of them. The remaining **three versions of
one hierarchy state file** were not located in the recovery check below.
Keep the current and historical versions distinguishable; do not change frozen
plans to conceal a mismatch. These counts describe bindings, not necessarily
distinct files.

Some absent filenames are expected:

- **65 maintained-spec references** use `unused-source.json`. The hierarchy
  generator replaces that placeholder with a saved `source.json` before
  preparing each step; these are not missing corpora.
- **Four older comparison specs** point to an intermediate that was never
  created because the producer step was held before comparison. Those defaults
  cannot be run directly. The saved state and the reference-specific explanation
  are recorded in [reference resolutions](reference-resolutions.csv).

### Historical input recovery

The first recovery check on 2026-10-19 recovered nine additional input versions,
totaling 1,424,669 bytes. Each complete recovered file matches the SHA-256
recorded by its original experiment:

- **Eight review logs:** the required version is an exact prefix of the current
  log, ending at a complete JSON line. Later reviews had been appended. The
  alternatives list records the source, full-source hash and exact prefix length.
  Both the complete current logs and the recovered earlier versions are retained.
- **One qualification configuration:** `qualification-20261007` preserved its
  case definitions in its plan. Replacing only the one-line Q06 and Q08 case
  objects in Git blob `91b0a023d8dd9969f91a1394906bed97336b19f7` with those
  saved definitions recovers the exact file. The alternatives list records the
  plan location and hash, serialization and resulting hash. This is a verified
  recovery, not a separately discovered backup.

These nine files are saved under the publication checkout's ignored
`target/publication-inputs/` directory. Their identities and recovery procedures
remain in [exact alternatives](dependency-alternatives.csv); their contents are
not committed to Git. Original files, plans and receipts were not modified.

Three earlier versions of
`oracle-mvp-shr-pair-correctness-v1:target/hierarchy-nine-note-children-v3/state.json`
remain unlocated. They affect these eight saved experiments beneath
`target/hierarchy-iteration-v1/` in that source root:

| Expected SHA-256 | Affected experiment directories |
| --- | --- |
| `8170a1ada66e1a95d7a22a3ba5171f96bc36647bf3c998b722b49359034200a1` | `ingredient-heat-guards-v32-baseline`, `ingredient-heat-guards-v34-draw1` |
| `3c684cdbedb8f8aeec8894267ca009e0ae4fba8fc20dcf7cc3f678dce5a90c0b` | `ingredient-heat-v32-baseline`, `ingredient-heat-v34-draw1`, `ingredient-heat-v34-draw2` |
| `0e7eaab5e9f7154ace1478c6998f2164fde65e58c3e63b946ec398456a9541c6` | `preparation-storage-v32-baseline`, `preparation-storage-v35-draw1`, `preparation-storage-v35-draw2` |

All eight retain prepared cases and saved responses. Their missing state
versions prevent complete source verification and regeneration of those cases
from the original state. Preserve the available evidence with this limitation;
the current state file is not a substitute. The complete local audit retains the
affected bindings; [selected studies](experiments.csv) and
[publications](publications.csv) identify the retained results.

The search checked 658 indexed state/configuration files, 167 additional direct
copies under known source roots, indexed historical hashes, the configuration's
Git path history and 18,285 Git blobs within bounded size ranges. It included
inventoried files on relocated storage. [Inventory metadata](inventory.json)
records the search bounds. This establishes that these versions were not found
in those locations, not that no copy exists anywhere.

### Remaining input hash checks

The subsequent check completed all **9,556 previously unchecked input bindings**:
9,551 match their current files, including all 15 large inputs. Five require
older versions of these files under `research-main:sse_multivector/experiment_specs/`:

| File | Exact historical version |
| --- | --- |
| `hr02-m06-muse-titles-v1.json` | Two versions: one in Git; the other recovered by changing only `max_output_tokens` from 6500 to the saved plan's 8192 in that Git version. |
| `luna-complete-note-masks-v1.json` | Found in Git history. |
| `lg01-bcpv4-six-pairs-astra-low-v1.json` | Found in Git history. |
| `asv6.100-hr01-post-template.txt` | Recovered by UTF-8 encoding the exact `plan.prompt.text` saved in the `asv6.100-context-draft/V1` experiment. |

All five match their original recorded hashes. The pre-rewrite audit located
the three Git blobs and their commits in the publication clone. The two recovered
files are saved under ignored `target/publication-inputs/`. [Exact alternatives](dependency-alternatives.csv)
records each source, hash and recovery procedure. No additional unresolved
versions were found; the three state versions above remain unlocated.

All **62 recorded encoder bindings** also match: two checkpoint copies and two
configuration/tokenizer directory copies shared by the hierarchy runs. Directory
hashes use the production worker's `canonical_tree_sha256` function. Measured
hashes are recorded in [runtime inputs](runtime-inputs.csv).

Files were hashed in 1 MiB chunks, with size and modification checks to detect
concurrent edits. No concurrent changes were detected. This completes checking
the recorded input hashes already indexed. The large-plan follow-up below also
checks their newly indexed inputs. Verification of all saved responses remains
unfinished.

### Large experiment plans

The source audit indexed all **42 plans** that exceeded the initial 32 MiB read
limit. Its native experiment entries contain prompt versions, provider/model
settings, case counts, saved plan and manifest identities, code-provenance
references and located result files. Complete frozen settings remain in each
original plan.

Their **34,091 source references** resolve to **6,092 input files**, all matching
the recorded hashes. Of these, 6,067 had measured hashes and unchanged file
metadata; the remaining 25 were hashed in 1 MiB chunks. The local audit added
25 dependency rows and one previously unlisted file: a saved **DSLv2**
relationship prompt. No new source mismatches or missing inputs were found.

That audit located result files for **33 plans**. The other nine had no result
file at their recorded or adjacent locations. They remain evidence of preparation;
absence of that file alone does not establish a failed run or lost results.
Their individual findings remain in the complete local audit.

The streaming JSON pass read 8,200,509,108 bytes with a peak parser memory use
of about 24 MiB. Raw plan-file hashes were also measured. This checked metadata
and source bindings; it did not perform inference, assess answers or verify all
response receipts. Saved case counts do not represent independent trials.
Original plans and results were not modified.

## Saved results and verification

- The discovery snapshot found **3,182 native plans** without `results.jsonl` at
  the recorded location or beside their saved plan. Some may be prepared jobs
  that never ran. Their individual findings remain in the local audit; absence
  of that file alone does not establish a failed run or lost results.
- Indexed input and encoder hashes have been checked as described above. The
  three unlocated state versions remain a source-verification limitation.
- Adapter configurations identify pinned base-model revisions. Check eventual
  hosted downloads against their selected file hashes; having a saved file is
  not a completed reproduction test.

[Remaining publication items](publication-gaps.csv) record unsupported results,
the missing configuration and final evidence identified by the historical
collection review below. Duplicate native jobs, warmups and reused answers must
not be counted as independent trials.

### Historical collection review

The 2026-10-20 review checked all **109 older inventory groups**, comparing their
listed files and exact related source directories with the selected exports.
**32 groups need no separate result export:** 30 have their listed material
retained in Git, one records a blocked attempt with no generated answers, and
one is a proposal whose inputs duplicate its executed sibling. The executed
sibling still needs an export. This resolves those collection-level gaps; it
does not resolve the separate placement review of the 196 ambiguous Git files.

The 33 HDB title/description groups, 11 SSE representation studies, six
subject/mask collections, 22 early/standalone prompt collections and four
segmentation/title/frontier collections are now selected as described below.
The remaining **one group needs a final-evidence export**:

| Collections | Groups | Evidence to retain |
| --- | ---: | --- |
| Archived baselines | 1 | Four CREC119 answer/segment files and two geometry diagnostics; the TEv4.1 answers are already covered by selected inputs |

The current-baseline omission found in this review is now resolved. The six
selected **ASv6.100** native bundles retain 180 valid answers and their saved
reviews. `quality-summary.md` and four frozen evaluation rubrics are now selected
verbatim under `evaluations/asv6.100-generalization-v1/`, totaling **91,107 bytes**
(**34,369 bytes** with gzip level 6). They explain the per-input/per-trial
measurements and the criterion IDs used by the reviews. All 60 summary/rubric
case IDs match the selected answers; the 119 unrun plan rows are not additional
answers. See the [study's file list](../../sse_multivector/subject-prompt-goal-v1/asv6.100-generalization-v1/README.md#publication-files).
Older AS results remain historical; unknown provenance or reviewer identity
stays unknown.

Final evidence is often much smaller than its original container. The 506 HDB
answer files total **94,310 bytes** before their comparisons and assessments.
The nine real-note response files contain large working arrays, but their final
segment/unassigned fields serialize to **678,060 bytes**, before required input,
tree and review evidence. Neither measurement is a completed export-size estimate.
Exclude intermediate embeddings, clustering distance arrays and duplicate answer
views. Numerical measurements that are themselves a study's result still belong.

A saved hash reference does not publish the referenced content. The earlier
fine-region numerical bundle retained only a title-review hash; the separate
title bundles now retain all 50 answers and 49 recorded judgments. The later
frontier result files were located in the original main checkout and are now
included with their source bindings. Teacher-parity results remain interim.
A missing aggregate file also does not
erase successful individual responses in a partial run. Preserve actual user
decisions separately from agent assessments.

The review itself made no additional exports or changes to original records.
The five ASv6.100 documents, 33 title/description study groups, 11 SSE
representation studies, six subject/mask collections, 22 early/standalone
prompt collections and four segmentation/title/frontier collections were selected afterward; the
[measured totals](downloads.md#measured-local-exports) include them. The
remaining-items table names concrete export requirements rather than treating
every old directory as an unexamined missing dataset.

### Selected segmentation, title and frontier evidence

The four collections now link **16 bundles, 80 files and 19,415,582 bytes
(18.52 MiB)**, or **3,633,143 bytes (3.46 MiB)** with gzip level 6.

The two fine-region title bundles retain 50 exact answers and 49 recorded user
decisions. H000019 stays unreviewed. Generated wording, reviewed wording and the
exact supplied input order remain separate. The real-note bundle retains nine
final segmentations, complete hierarchy outputs for two tested runs, 248 curated
posts, fixed parameters and review evidence. Repeated mask/context fields use
validated input references; working embeddings and distance arrays are excluded.
Its 132 structured user rows are the original states, with 215 unrecorded baseline
outcomes. The later garden/allotment retraction remains in separately bound
authored findings; it does not overwrite those frozen response files.

The 13 frontier entries retain 233 completed raw answers, three failed partial
answers, 73 failed attempts, final measurements and source-bound review evidence.
Sixty Muse answers and 22 Astra baselines reference already-selected exact bodies.
The 437 review cells and 258 blinded-packet membership rows are not user-judgment
counts. The teacher comparison stays interim: its original summary counts eight
subject answers while native receipts retain ten, and no final parity verdict
is recorded.

All **172 relevant tests** pass. All 16 real-file exports pass under a 512 MiB
worker address-space limit. The 366 selected sources (302,177,599 bytes) retain
their original hashes, bytes, modes and modification times; all 9,770 previously
selected files remain unchanged. No models ran and nothing was uploaded. See
the [title/segmentation checks](reproduce.md#fine-region-title-and-real-note-segmentation-checks)
and [frontier checks](reproduce.md#frontier-comparison-checks).
Known old-AS derivatives remain deprecated historical evidence, and unknown
lineage remains unknown. Final publication privacy review remains open.

### Selected early prompt and prominence evidence

The 22 collections now link 24 entries: **120 files, 2,440,074 bytes (2.33 MiB)**,
or **370,563 bytes (0.35 MiB)** measured with gzip level 6. They retain 494 exact
early/standalone prompt answers and 20 manual prominence answers with their final
scores, original posts, masks, scientific parameters and recorded assessments.
The 93 already-selected native prominence bundles remain unchanged.

Seven source review states preserve 35 decided state rows (19 approved, 16
rejected) and 31 undecided rows. They concern 34 distinct decided batch/items:
one approval appears again in a later rereview. Three identical embedded
snapshots reference the original states. The medium-reasoning user's rejection
applies to trial 3; the assistant's application to trials 1 and 2 stays separate.
The probe-v3 M05 display permutation does not change the raw answer's order.

Reused baselines remain references. The transfer study's recorded failure is
separate from its 71 final answers; the partial TP study retains two answers and
three unknown outcomes among five configured cases. Setup source outputs validate
used subjects without publishing complete preparation answers or unused subjects.
All 12 standalone mask studies have proven ASv6.8 lineage and remain deprecated
historical evidence. The nine early TP/MP studies retain unknown AS lineage;
manual prominence provenance is recorded per case. Raw posts are not deprecated.

All 113 relevant tests pass. All 24 real-file exports pass under a 512 MiB worker
address-space limit, including stable missing-case order across fresh processes.
All 302 selected sources (9,128,919 bytes) retain their hashes, bytes, modes and
modification times; all 9,650 previously selected files are unchanged. No models
ran and nothing was uploaded. The [commands and source checks](reproduce.md#early-prompt-and-manual-prominence-study-checks)
describe the exact selection. Final publication privacy review remains open.

### Selected subject/mask evidence

The six subject/mask collections now link 123 additional study/review entries:
**615 files, 14,109,305 bytes (13.46 MiB)**, or **2,899,941 bytes (2.77 MiB)**
measured with gzip level 6. Their 1,965 exact saved responses remain bound to
used inputs, prompts, receipts and recorded settings. Saved reuse and independent
trials remain distinguishable; the response total is not a fresh-call count.

The 197 scientific assessment, comparison, measurement and correction records
retain their recorded attribution. Two explicit user rejections are preserved;
undecided subjects stay undecided. Original reviews and later corrections remain
separate. The four previously selected subject studies, ASv6.100's 180 native
answers and its five evaluation documents remain linked without duplication.

The [shared offline command](reproduce.md#historical-subject-and-mask-study-checks)
checks exact source hashes and preserves scientific methods while excluding
credentials, account locations and private execution identifiers. All 85 relevant
tests pass. All 123 real-file exports also pass under a 512 MiB worker address-space
limit. The 3,266 selected source files (57,992,724 bytes) retain their bytes,
hashes, modes and modification times. No models ran and nothing was uploaded.
Known old-AS derivatives remain deprecated historical evidence; unknown lineage
stays unknown. Final publication privacy review remains open.

### Selected title/description evidence

All 33 reviewed title/description groups now have local publication files under
`title-studies/`: **165 files, 2,717,003 bytes (2.59 MiB)**, or **818,640 bytes
(0.78 MiB)** measured with gzip level 6. Their 506 exact saved answers, final
comparisons, recorded assessments and selections are bound to the used masks,
source posts, prompt text and saved model settings. The inputs contain **89
distinct posts**, totaling 27,506 UTF-8 text bytes. AS lineage remains unknown.

The three 61-group final title sets preserve their original selections, including
**32 reused answers**. Reuse references do not add new answers or trials. The
**24 failed attempts** remain separate, with unreported usage recorded as unknown.
All **480 review-comment entries** retain unknown authorship and carry no inferred
user decision. Explicit saved decisions and agent judgments remain separate.

The shared offline command and maintained selection are documented in the
[reproduction guide](reproduce.md#historical-title-study-checks). All 62 relevant
tests pass, and all 33 original collections export successfully. Verification
reconstructed all 506 requests from the published templates and inputs and
checked every raw answer hash. The 2,262 read source files, totaling 5,128,111
bytes, retain their original bytes, modes and modification times. Worker peak
memory was about 31 MiB under a 512 MiB address-space limit. No models were run
and nothing was uploaded. Privacy review and the remaining historical formats
remain open.

### Selected SSE representation evidence

The 11 SSE representation studies now have local publication files under
`representations/`: **33 files, 880,381 bytes (0.84 MiB)**, or **146,702 bytes
(0.14 MiB)** measured with gzip level 6. They retain their original final
comparisons and outcomes: six studies passed their frozen criteria and five did
not. Their fixed inputs
include controlled fixtures, manually supplied text spans and source-post
provenance. No subject or mask prompt generated these inputs, so AS version
classification is not applicable. They remain historical diagnostic evidence.

The compound-subject study retains its required full 45-by-45 cosine table.
The other studies retain their saved comparisons, rankings, medians and verdicts;
raw vectors and duplicate all-pairs CSV views are excluded. Existing scientific
interpretations remain in Git unchanged. A modified fixture derived from a real
post retains its own encoded-input identity separately from the source post.

For the context-counterfactual study, the original fixture hash is verified and
the recorded worker-request hash agrees across the analysis, manifest and
receipt. The original compiled worker-request bytes are absent, so this does
not claim to have reconstructed that hash. See the
[publication commands and checks](reproduce.md#sse-representation-study-checks).

All 40 relevant tests and all 11 real-file publication commands pass. Independent
checks preserve all 381 encoded identities, every native result value and all
2,025 compound-matrix cells. The 99 original files, totaling 2,575,740 bytes,
retain their hashes, bytes, modes and modification times. Workers peaked at about
28 MiB under a 512 MiB address-space limit. No models were run or files uploaded.

## Current Oracle/runner compatibility

Oracle's numerical validation now calls `_stamp(path)` on its active
`ReceiptFiles` instance, as required by the shared runner. All 177 relevant
construction, adapter and publication checks pass, including the 42 that
previously failed at this call. See the
[reproduction guide](reproduce.md#hierarchy-publication-checks) for the check
scope. These local fixtures do not establish successful reproduction of every
archived experiment or validation with a live provider.

Compact prompt, evaluation and numerical exports have additional local checks,
documented in [the reproduction guide](reproduce.md#other-compact-export-checks).
Two evaluation-workflow regression failures remain: the native attempt-allowance
test receives an additional stopped-before-dispatch error, and the effort-analysis
fixture disagrees with the runner's concurrency setting. Both reproduce using
the unchanged Oracle code with the same runner. They remain unresolved; passing
export checks do not establish that every evaluation workflow is compatible.

## Original-file links and replay

The reviewed generated files are untracked but remain at their original local
paths. The initial scan found **745 direct local-file link occurrences across
143 retained Markdown files**, pointing to **613 generated files** absent from
a clean checkout. A follow-up check of all tracked Markdown found five more
occurrences, for **750 links across 145 documents** to those same 613 files.
These counts exclude fenced examples and other pre-existing missing or
outside-repository links.

Those 750 links now show their exact original paths as text instead of broken
hyperlinks. Another 88 unavailable or outside-checkout references were labeled,
and two relative links to retained source documents were corrected. Verified
selected exports are identified separately by publication ID; the findings,
measurements and original provenance are unchanged. For example, the
[scalability findings](../planning/scalability.md) identify their local resource
records, and the [TRUE07 findings](../../sse_multivector/navigation-research-v1/TRUE07/RESULTS.md)
distinguish original review files from the selected score export.
See [reading the research records](README.md#reading-the-research-records).
The check found no remaining links to the reviewed removed files and no newly
missing file destinations. Other pre-existing missing links remain outside this
repair's scope.

The four authored ASv6.26–ASv6.28 reports linked from the
[subject-prompt investigation](../../sse_multivector/subject-prompt-goal-v1/README.md)
are now included in Git. The original `full-outputs.md` views for
`asv6.28-fresh-v1` and `asv6.28-comparison-v1` remain local; their source posts
and final answers are included in the compact dataset exports.

All six originals were located on 2026-10-20 in the `research-main` checkout
under `sse_multivector/subject-prompt-goal-v1/`; see [source roots](source-roots.csv).
They total **63,170 bytes**: **26,613 bytes** for the four authored `RESULTS.md`
reports and **36,557 bytes** for the two complete-output files. They were never
tracked in the original repository or its preserved pre-rewrite Git backup;
the generated-data rewrite did not remove them.

The four studies' saved outputs account for **78 calls and 809 subjects** from
**10 distinct source posts**, matching the reported counts. All 78 outputs
identify saved preparation manifests whose hashes match their recorded bindings.
The two referenced complete-output files reproduce the saved subject strings.
These checks establish agreement with the saved records, not independent
semantic validation.
ASv6.26–ASv6.28 results remain historical evidence under the ASv6.100 rule.

The four selected bundles appear under `prompt-studies/` in the
[publication catalog](publications.csv), with exact filenames and hashes in
[publication files](publication-files.csv). Their **20 files total 380,086 bytes**,
or **91,193 bytes** measured with gzip level 6. They retain all 78 raw answers,
78 per-call assessments, three shared interpretation notes, all four final
summaries and the parameters needed to interpret their probes. Actor labels
remain unknown where the saved review does not record them. Source files are
unchanged in bytes, modification times and modes. These exports are still local;
upload and privacy review remain pending.

This covers these four studies only. The older collection's broader
[conversion gap](publication-gaps.csv) remains open.

Some existing code also requires original artifacts:

- The [saved Infomap tests](../../sse_multivector/test_infomap_saved_results.py)
  read the saved I01–I04 graphs, configurations, hierarchies and original source
  files.
- The [omission-call tests](../../sse_multivector/real-note-fine-segmentation-v1/test_omission_calls.py)
  read saved omission-call records and the original `N001-AS/config.json`.
- The legacy [segmentation preparation loader](../../sse_multivector/real-note-fine-segmentation-v1/generation.py)
  still requires original example/reference configurations in addition to the
  retained frozen package contracts. Those configurations remain local.
- `run-fine-region-scc-preflight.sh`, `run-fine-region-partition-pilot.sh` and
  `run-fine-region-hierarchy-pilot.sh` require the original
  `sse_multivector/baselines/communicated-meaning-tev4-1/baseline.tar.zst`.

These tests and historical entry points still need a clean-checkout replay plan.
The compact exports do not supply their original file layouts. No claim that
all tests or historical workflows run with only the public selection has been
established.

## Preserve the source history

The pre-rewrite audit located 40 of 41 original generation commits in the
publication clones.
HR34's Oracle construction commit,
`bf7801bc1d92491b20eab8d075fb8d57b83d6b3e`, exists in the original repository
but is absent from the publication clone. Preserve that history before release.
[Code versions](code-versions.csv) preserves that check and affected run. Its
availability columns describe the pre-rewrite snapshot; original commit IDs
remain unchanged in the evidence.

The original audit also identified **294 artifact blobs in Git history but
absent from its index**, with measured SHA-256 hashes and original commit
associations. [Historical files](historical-files.csv) and
[historical uses](historical-uses.csv) retain those original identities. The
original history is preserved locally; generated blobs removed by the rewrite
are no longer available in the rewritten trees.

The [generated-data rewrite](downloads.md#generated-data-history-rewrite) is
verified. Its exact [commit mapping](commit-map.txt) is now bundled with the
source. Historical source reads, legacy prompt verifiers and the
[legacy automatic-workflow test](../../sse_multivector/test_distillation_review_automatic.py)
use `generation_history.source_at_revision` for full original IDs and unique
7–40-character hexadecimal prefixes, without replacement refs. All 30 revision
lookup and automatic-workflow regression tests pass. The separate
generation-history suite retains one pre-existing saved-manifest `config_path`
mismatch, also reproduced against original history. At code commit `3ecbc0d4`,
all six revision tests and the legacy automatic-workflow test also passed in a
fresh ordinary clone without replacement refs, private audit files or saved
research inputs.
Raw Git commands require a rewritten ID from the map. Some verifiers also read
generated blobs intentionally removed from history; those checks still require
the preserved original evidence.

## Assemble and test the release

Review the actual selected contents for credentials and personal information
before packaging. Known credential containers were excluded from discovery;
that is not a completed privacy review of the evidence.

The [publication plan](downloads.md#measured-local-exports) now measures the
selected local exports: **1.08 GiB**, plus **6.78 GiB** for all 17 evaluated
adapters. [Publications](publications.csv), [exact files](publication-files.csv)
and [checksums](publication.sha256) record this selection. The 534.71 GiB source
inventory and old bundle tables do not define the public download size or layout.

Before publication:

- Continue the agreed [public Git layout](downloads.md#public-git-contents):
  the selected-study index and reviewed generated-file untracking are in place;
  local files retain their original paths. The 196 ambiguous files
  remain tracked. Review them and resolve the remaining
  [original-file replay and evidence gaps](#original-file-links-and-replay).
- Review [remaining conversion items](publication-gaps.csv): 33 unsupported result
  files, one result without its required local configuration, and the final
  evidence identified in the [historical collection review](#historical-collection-review).
  The supported selection has been backfilled through the normal exporters;
  all 27,032 native jobs were classified in the local audit, and the public
  index retains the 2,547 selected standalone native studies.
  Do not substitute guessed outcomes or entire working directories for
  unsupported formats.
- Preserve experiment identity, exact selections, versions, reuse and recorded
  outcomes. Report missing evidence without changing original records.
- Review the existing exact export list and checksums, then link the GitHub index
  to pinned Hugging Face revisions after repository names are chosen. No upload
  is authorized by generating this local list.
- Update the [reproduction guide](reproduce.md) for those outputs and test it in
  a clean environment, including a complete hierarchy run with public
  authentication. Its existing local checks use the earlier original-file layout.
- Provide a maintained, tested command for L1 analysis from saved judgments and
  validate portable training and adapter-inference instructions with the selected
  data and pinned upstream models.

The generated-data rewrite is complete. Final privacy and identity review
remains before publication; any further history cleanup needs its own approval.
Repeat publication checks against the final contents, preserving original
generation IDs and an old-to-new mapping across any further rewrite. Preserve
original working artifacts locally; complete native receipt packages are not a
condition for publishing the compact final results.

## Prepare verification metadata

This describes the implemented verifier for complete original native experiment
files, including the locally tested HR39 package. It is not a requirement to
include those files in the agreed compact publication. It cannot verify reduced
exports against the original whole-file hashes. When using a complete local
package, readers run `verify` without supplying research-machine paths.

Stage the selected native experiments and their required files under one
extraction root. Include each plan, prepared configuration, run manifest,
results and any runner/worker upgrade ledgers, all bound source versions, and
the producer receipts needed by reused answers. Resolve historical input
versions using the inventory before staging. Use copies of the frozen bytes.
The command checks only the complete native files staged for this workflow;
it does not select publication contents, copy evidence or export final results.

An original path can require different historical contents in different plans.
The current location file maps each original path to one destination, so a
single shared mapping cannot verify conflicting versions. Resolve that packaging
limitation before preparing a shared package for those experiments.

Use the private original-to-staged locations from file selection and copying.
For the HR39 example, with the setup variables from the reproduction guide and
that private file saved outside the staging root:

```bash
cd "$ORACLE_ROOT"
source target/hierarchy-env/bin/activate
python sse_multivector/experiment.py prepare-release "$RELEASE_ROOT" \
  --locations target/reproduction/private-locations.json \
  --experiment evidence/hierarchy-run-store/hr39-v53-auto-5000-note-v1/HR39-resumed-1/batch-00025/experiment
```

Repeat `--experiment` for all selected native experiments sharing that extraction
root. Preparation verifies them and writes `experiment-locations.json` only
after they pass. The generated file contains relative destinations for only the
locations those checks use, including original producers of reused responses.
Shared sources are hashed once per invocation. No model calls are made.
The private location format is documented in the runner's publisher instructions.

Preparation rejects dependencies outside the staging root and does not overwrite
an existing locations file. Missing files, changed source bytes and invalid
receipts must be resolved before packaging. A successful integrity check may
still include failed or unrun cases; preserve their recorded status.

Include the generated file at the extraction root and add it to the final
archive file list and checksums. Keep the private staging locations outside the
archive. When splitting a collection into several archives, preserve the common
extraction layout and supply the same complete metadata with the pieces. Do not
overwrite it with independently generated partial mappings. Check the required
downloads together after extraction elsewhere, with original storage unavailable,
using the reader command without `--locations`.
