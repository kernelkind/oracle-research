# HRC02 — Harder broader–narrower relationships on saved masks

Test the same released HierarCaps CLIP-L checkpoint and paper-defined angle as HRC01. No training, rewritten model inputs, generated subjects, full-note context, new hierarchy, or parameter search. Reuse the unchanged runner and preserve HRC01.

## Questions

1. Does broader-to-narrower ordering survive without repeating the broader subject's words? Examples include bread → bagels and art → photography.
2. Does a real broader subject score better than a related but different subject for the same mask? Examples include food preservation versus growing beets as possible parents of freezing beets, and coffee versus grinding as possible parents of roasting coffee.
3. Does the score favor the intended broader subject when it is described using more words? Examples include general kitchen work versus preparing sourdough.

The selected source corpus is already familiar and mostly food/lifestyle. This is a more discriminating follow-up, not a representative accuracy estimate, unseen-corpus holdout, or technical-domain qualification.

## Freeze before scoring

The [fixture](hrc02-fixture.json) contains 51 exact saved masks and 27 direction comparisons, with 28 fixed-child comparisons against other proposed parents. Two independent clean-context readers proposed candidates from text only. The main agent inspected the masks and selected cases. A third clean-context reader reviewed them before inference.

That review moved an ambiguous painting mask and a fragmented food-growing mask out of the clearer category group. It also identified the preserved/preservation word-family cue and a mask that omits the source's reversal about squirrels giving up attacks. The saved masks remain unchanged. All selection caveats and reasons are in the fixture.

Report groups separately:

- Thirteen clearer category relationships. Twelve lack a shared subject-word family; the century-eggs case has preserved/preservation overlap.
- Five broader-activity or fragmented-phrase tests, including longer broader wording.
- Seven qualified examples for inspecting ambiguity, advice, diet, and sleep; no mandatory correct direction.
- Two dependent shared-word coffee controls with closely related alternatives.

These are not 27 independent semantic families: several comparisons reuse bread, art, preservation, or advice from the same note. A child may have more than one valid broader subject. Do not prescribe an entire hierarchy or force a unique closest parent.

## Analysis

Preserve all 2,601 ordered pair scores and all 51 embeddings, plus the empty-string origin. Use the same scoring formula and exact-input constraints as [HRC01](HRC01-PLAN.md). Model tokenization is allowed; semantic text rewriting and silent truncation are not.

For every fixed direction, show forward and reverse angles, token counts, and the result of the simple assumption that the shorter text is broader. Equal lengths leave that baseline undecided. Direction and distance-from-origin ordering are the same evidence, not separate confirmations.

For every fixed-child comparison, compare both exterior angle and ordinary cosine on the same two proposed parents. This tests whether the directional score adds useful ordering beyond relatedness on these cases. The shorter-parent baseline is reported here too, with ties undecided. Do not interpret its correlation with successes as proof that model behavior is caused by length.

Inspect every scored case, not only aggregate counts. Keep qualified examples separate, and preserve any disagreement with the fixed judgments instead of relabeling failures to improve a score. Do not fit an acceptance cutoff, claim universal error rates, or treat missing candidate parents as model failures.

The exact notes and individual masks must be available with the scores. Validation will replay calculations, verify source and checkpoint hashes, check the unchanged runner tests, and independently reproduce the embeddings. A separate reader will review interpretation after scoring.

## Resources and boundary

Use the already cached checkpoint, CPU only, two threads, batches of four, and the same 6 GiB RAM/no-swap/two-CPU-equivalent systemd limit. No paid resources. The old runner's ru_maxrss field is retained as raw historical telemetry, not asserted as an isolated workload peak. No original artifacts, model parameters, hierarchy memberships, browser, or other agents' files change.
