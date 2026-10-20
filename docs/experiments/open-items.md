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
the missing configuration and older groups still needing review. Duplicate
native jobs, warmups and reused answers must not be counted as independent trials.

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
selected local exports: **1.04 GiB**, plus **6.78 GiB** for all 17 evaluated
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
  files, one result without its required local configuration, and older inventory
  groups needing review for final data versus material already retained in Git.
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
