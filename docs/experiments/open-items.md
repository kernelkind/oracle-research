# Evidence and reproduction limits

The selected inputs, parameters and final results are prepared locally.
[Contents and hosting](downloads.md) describe the selection. The dataset
repository name is `KernelKind/oracle-research`; public code repository names,
pinned Hugging Face revisions, hosted reader tests and publication approval
remain open. Complete original working files remain private.

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
runtime required for full replay. [Commands and limits](reproduce.md#verify-and-restore-the-dataset).

### Selected archived baseline evidence

CREC's assembled answers and reused work remain identified. TEv4.1 and
narrowest-subject geometry retain their final measurements. Unknown AS lineage
remains unknown; these are historical results. [Commands](reproduce.md#verify-and-restore-the-dataset).

### Selected segmentation, title and frontier evidence

Final segmentations, title answers and recorded decisions remain separate from
later authored corrections. Frontier partial answers/failures and reused
baselines remain distinct. Teacher-parity results are interim: its summary
counts eight answers where receipts retain ten, and no final parity verdict is
recorded. [Segmentation/title](reproduce.md#verify-and-restore-the-dataset)
and [frontier](reproduce.md#verify-and-restore-the-dataset) commands preserve these limits.

### Selected early prompt and prominence evidence

Saved answers, partial outcomes, original scores/masks and attributed reviews
are selected. Later rereviews do not overwrite original decisions. Known
pre-ASv6.100 derivatives remain historical; unknown lineage remains unknown.
[Commands and interpretation](reproduce.md#verify-and-restore-the-dataset).

### Selected subject/mask evidence

Original assessments, corrections and user decisions remain separate. Reused
responses are not fresh calls; original answer bodies remain verbatim. Known
old-AS derivatives are historical. [Commands](reproduce.md#verify-and-restore-the-dataset).

### Selected title/description evidence

Saved answers, final title selections and failed attempts remain distinct.
Unattributed review comments do not imply user decisions. The exports preserve
input order, exact masks and deduplication/hashtag conditions.
[Commands](reproduce.md#verify-and-restore-the-dataset).

### Selected SSE representation evidence

These studies use manually supplied spans, rather than subject/mask prompt
outputs, so AS classification does not apply. Final comparisons and fixed
inputs are retained; the compound-subject result includes its required complete
45-by-45 cosine table. The context-counterfactual compiled worker-request bytes
are absent: agreement among recorded hashes does not reconstruct those bytes.
[Commands and checks](reproduce.md#verify-and-restore-the-dataset).

## Source versions

Original producer revisions remain in scientific records. The bundled
[commit map](commit-map.txt) supports source lookup after publication-history
cleanup. Some historical producer bindings remain incomplete:

- HR34's recorded construction revision
  `bf7801bc1d92491b20eab8d075fb8d57b83d6b3e` has no public mapping in the reviewed
  source selection. A later source copy does not establish those producer bytes.
- TRUE10's retained source identity includes a hash mismatch. Its published final
  graph and assessments remain evidence; that mismatch limits exact producer replay.
- A source path and SHA-256 identify bytes but do not identify a Git revision.
  Some original verifiers also require generated blobs deliberately omitted from
  public source history.

The [source guide](reproduce.md#which-code-is-being-repeated) distinguishes
original producer revisions from the later pre-cleanup source preserved at
`03bd9e4595fbbf6be18cd08e7d273e69ff563a9b`. Do not substitute a current or later
implementation while claiming an exact historical replay.

## Tested reader paths

A complete 12-post generation/browsing path passed in a fresh Debian 13 VM with
8 GiB RAM and four CPU cores. HR39 browsing, saved fine-tune comparison,
recorded-post preparation and HR36 preparation also passed using compact files.
These check the documented workflows and saved arithmetic; they do not establish
semantic quality, a fresh historical model draw or million-note scaling.

Native subject/claim review passes the Python-to-Rust saved-artifact test,
including pause/resume and rejection of a substituted compatibility-shim hash.
Source verification follows the same shared-runner selection as generation;
use the [generation Python environment](../../sse_multivector/model-runner.md#review-and-local-models).

Hosted download tests and fresh GPU training/adapter-inference runs remain
unverified. Public code repository names, pinned dataset/model revisions and final
publication approval remain open. The [reproduction guide](reproduce.md#what-has-been-tested)
records the tested scope.
