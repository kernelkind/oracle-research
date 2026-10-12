# Bootstrap evidence review: reset conclusions, retain data

The user clarified the reset: **disregard all conclusions previously drawn from
the evidence**, rather than discard the evidence itself. This supersedes the
earlier physical test-case removal. Prompts and original records remain intact.

## Evidence restored

All 94 datasets/collections and 179 associated experiment specifications removed
from the Bootstrap worktree have been restored byte-for-byte from the local tag
`bootstrap-tests-before-reset-20261012-cb8c51e0` (`cb8c51e0`). The 33 files formerly
present on main are restored there; the other 240 remain in their original task
history rather than being newly introduced into main. No case payload was lost.

Frozen original posts, subject hierarchies, model inputs, outputs, receipts,
reviews and accounting records remain available. The unbacked artifacts under
`target/` were never deleted. Other agents' worktrees are untouched. The backup
tag remains available for provenance; restoration required no inference.

## Current interpretation and evaluation policy

- Use original evidence for fresh examination. Saved model outputs are
  observations of what a model returned, not certified topic definitions.
- Disregard prior semantic labels, expected meanings, accept/reject assessments,
  fault assignments, causal diagnoses and recommendations derived from them.
  This includes previously agreed case conclusions; the record that someone
  expressed a judgment does not make that judgment current gold.
- Retain old review metadata and quotations as historical records. Do not pass
  their conclusions into the model or use them to seed a fresh evaluator.
- Inspect original inputs without old assessments, using the native
  `show --inputs-only` view. Assess outputs and counterexample hypotheses anew;
  do not import a former acceptance, rejection or inferred restriction.
- Preserve provenance requirements: only verified ASv6.100 subject data can
  support current-pipeline testing. Restoring older historical files does not
  make deprecated or unverified data eligible.

No previous semantic qualification or accuracy claim is active merely because
its case data is restored. Fresh expectations must be established independently.
The prompts, general experiment code and shared runner are unchanged. This
clarification does not select a new prompt, run inference or change a hierarchy.

## Verification

All 273 restored data/specification files match their original Git blobs.
Pre-existing prompt hashes remain unchanged, and native raw experiment records
remain on disk. No model calls were made for the restoration.
