# Evidence and reproduction limits

The selected inputs, parameters and final results are prepared locally.
[Contents and hosting](downloads.md) describe the selection; public repository
names, pinned Hugging Face revisions, hosted reader tests and publication
approval remain open. Complete original working files remain private.

## Input versions

All nine official subject corpora match their recorded hashes. Of 26 input
bindings whose current contents differ, [exact alternatives](dependency-alternatives.csv)
identify 23 matching historical versions or recoveries. **Three versions of
one hierarchy state file remain unlocated.** Frozen plans retain their original
paths and hashes; current contents must not replace historical versions.

Some absent paths are intentional: maintained hierarchy specifications use
`unused-source.json`, which the generator replaces with a saved step source.
Four older comparison specifications reference an intermediate never created
because the producer was held. Their defaults cannot be run directly; see
[reference resolutions](reference-resolutions.csv).

### Historical input recovery

Eleven exact versions were recovered from saved log prefixes, case definitions,
Git blobs or the original prompt text in a frozen plan. The recovery procedures
and full hashes are in [dependency alternatives](dependency-alternatives.csv).
Three state versions were not found within the indexed source roots, saved
copies, relevant Git path history and bounded historical-blob search. This is
not proof that no copy exists anywhere.

Affected experiments retain their available final evidence. The missing state
versions prevent full original-source verification or faithful preparation of
those cases; a current state file is not a substitute.

### Remaining input hash checks

All indexed recorded input bindings were checked. Five mismatches required
historical `hr02-m06-muse-titles-v1.json`, `luna-complete-note-masks-v1.json`,
`lg01-bcpv4-six-pairs-astra-low-v1.json` or the exact saved
`asv6.100-hr01-post-template.txt` text. Their alternative hashes match. All 62
recorded encoder checkpoint/configuration bindings also match; directory hashes
use production `canonical_tree_sha256`. See [runtime inputs](runtime-inputs.csv).

### Large experiment plans

The source audit streamed all 42 plans above its initial JSON read limit.
All 34,091 recorded source references resolve to matching inputs. Results were
located for 33; nine lacked results at their recorded or adjacent locations.
That absence alone does not establish execution, failure or lost answers.
Unexecuted preparations proven by bound evidence are excluded from the dataset;
three ambiguous snapshots retain unknown execution status.

## Saved results and verification

No reviewed conversion gaps remain in the selected evidence. Selection does not
assert that every historical directory is a separate experiment, that all saved
plans were executed, or that original native receipts can be reconstructed from
compact final results. Warmups, internal construction work and reused answers
are not independent trials. Missing usage and unknown authorship remain unknown.

### Historical collection review

The review covered 109 older collection groups. Thirty-two needed no separate
export (already retained source/findings, blocked work without answers, or
inputs duplicating an executed sibling); 77 now have selected final evidence.
Scientific findings remain in their study records and [bundle catalog](publications.csv).
ASv6.100's final quality summary and four frozen agent rubrics accompany its
180 valid saved answers. Closed packaging gaps do not resolve source-replay or
semantic-quality limitations.

### Selected hierarchy, navigation and performance evidence

Final graphs, partitions, memberships, navigation measurements and performance
results are selected. TRUE10 retains its raw/canonical cycles and two agent
assessments without treating them as user decisions. The performance evidence
still lacks the exact admitted 180-case training selection and frozen fitter
runtime required for full replay. [Commands and limits](reproduce.md#saved-hierarchy-navigation-and-performance-checks).

### Selected archived baseline evidence

CREC's assembled answers and reused work remain identified. TEv4.1 and
narrowest-subject geometry retain their final measurements. Unknown AS lineage
remains unknown; these are historical results. [Commands](reproduce.md#archived-baseline-checks).

### Selected segmentation, title and frontier evidence

Final segmentations, title answers and recorded decisions remain separate from
later authored corrections. Frontier partial answers/failures and reused
baselines remain distinct. Teacher-parity results are interim: its summary
counts eight answers where receipts retain ten, and no final parity verdict is
recorded. [Segmentation/title](reproduce.md#fine-region-title-and-real-note-segmentation-checks)
and [frontier](reproduce.md#frontier-comparison-checks) commands preserve these limits.

### Selected early prompt and prominence evidence

Saved answers, partial outcomes, original scores/masks and attributed reviews
are selected. Later rereviews do not overwrite original decisions. Known
pre-ASv6.100 derivatives remain historical; unknown lineage remains unknown.
[Commands and interpretation](reproduce.md#early-prompt-and-manual-prominence-study-checks).

### Selected subject/mask evidence

Original assessments, corrections and user decisions remain separate. Reused
responses are not fresh calls; original answer bodies remain verbatim. Known
old-AS derivatives are historical. [Commands](reproduce.md#historical-subject-and-mask-study-checks).

### Selected title/description evidence

Saved answers, final title selections and failed attempts remain distinct.
Unattributed review comments do not imply user decisions. The exports preserve
input order, exact masks and deduplication/hashtag conditions.
[Commands](reproduce.md#historical-title-study-checks).

### Selected SSE representation evidence

These studies use manually supplied spans, rather than subject/mask prompt
outputs, so AS classification does not apply. Final comparisons and fixed
inputs are retained; the compound-subject result includes its required complete
45-by-45 cosine table. The context-counterfactual compiled worker-request bytes
are absent: agreement among recorded hashes does not reconstruct those bytes.
[Commands and checks](reproduce.md#sse-representation-study-checks).

## Current Oracle/runner compatibility

The [reproduction guide](reproduce.md#what-has-been-tested) separates checked
reader paths from untested ones. Local exporter/fixture checks do not establish
successful replay of all archived studies or live-provider compatibility.
Two broader evaluation-workflow fixtures previously failed at allowance/resume
and effort-analysis concurrency; those failures were also present with unchanged
Oracle source and the same runner. They are not reported as successful replays.

## Original-file links and replay

Study records name original data paths as text and selected exports by
publication ID. Compact restoration does not recreate original run layouts.
These historical checks still require original artifacts:

- [Saved Infomap tests](../../sse_multivector/test_infomap_saved_results.py):
  original I01–I04 graphs, configurations, hierarchies and source files.
- [Omission-call tests](../../sse_multivector/real-note-fine-segmentation-v1/test_omission_calls.py):
  saved calls and the original `N001-AS/config.json`.
- [Legacy segmentation preparation](../../sse_multivector/real-note-fine-segmentation-v1/generation.py):
  original example/reference configurations beyond retained package contracts.
- Fine-region SCC/partition/hierarchy launchers: the original
  `sse_multivector/baselines/communicated-meaning-tev4-1/baseline.tar.zst`.

A clean-checkout replay plan for these paths remains open. The four authored
ASv6.26–ASv6.28 reports and their 78 raw answers are retained in source/selected
results; the two full-output display files are local originals. These derivatives
remain historical under the ASv6.100 rule.

## Preserve the source history

Original generation IDs remain in evidence, with public-source resolution via
[commit-map.txt](commit-map.txt). [Code versions](code-versions.csv) records the
original availability audit: HR34 construction revision
`bf7801bc1d92491b20eab8d075fb8d57b83d6b3e` was found in the original repository
but absent from that publication-clone snapshot. Do not claim its source was
published without checking the mapped history. Some verifiers also need removed
generated blobs, available only in the preserved originals.

## Assemble and test the release

Before publication, choose public repositories and pin revisions in the index,
review the final physical contents, and run the reader commands with original
research storage unavailable. The [dataset manifest](downloads.md#dataset-manifest)
binds the selected files. Preserve experiment identities, exact selections,
versions, reuse, incomplete outcomes and all replay limits.

A complete 12-post generation/browsing path passed in a fresh Debian 13 VM with
8 GiB RAM and four CPU cores. This is a workflow check, not semantic approval or
million-note scaling evidence. HR39 and compact fine-tune comparison browsing
also passed locally. Hosted reader tests and fresh GPU training/adapter-use
instructions remain unverified. No upload is authorized by preparing files.

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
