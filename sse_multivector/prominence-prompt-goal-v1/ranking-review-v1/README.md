# PPv10 ranking review v1

Read-only review UI for the **mask-based prominence** work. It groups
already-saved PPv10 scores by selection meaning so the ordering question can be
read directly: when a category is opened, do the notes most directly about it
sort first?

Prompt reviewed: **PPv10 — user-approved, tested experimentally, not
production-frozen** (source `../ppv10-draft-v1/PPv10.md`, sha256
`d40835fb0b104865727c0b0a2bde4074afb642991d9bddc424d5379ef4b038ea`, verified at
build time). The production registry still freezes PPv2 and is untouched.

## What this is

- A grouping of the saved scores from `../ppv10-ranking-v1/` and
  `../ppv10-mixed-notes-v1/` (19 mask/post pairs across 13 notes) into eight
  groups with comparable selections, plus singletons and the separately saved
  one-call Muse probe `../ppv10-mpv3.43-muse13high-v1/` shown on its own.
- Mechanical order checks on the comparisons predeclared in each study's
  `plan.json`. Verdicts are computed from the saved scores: ordered, tie, or
  reversed, with the gap. Tentative and related-content pairs are informational.
- Per-case drill-down: exact mask fragments, the complete marked post with
  selections highlighted, predeclared expectations where recorded, and
  provenance back to the saved artifacts.

## What this is not

- Not an accuracy percentage, benchmark, or user-approved gold labels. The
  expectations are assistant predeclarations preserved from the study plans.
- Not new inference. Building the page reads saved artifacts only; no model
  calls are made and none are implied.
- Not evidence for cross-note ranking outside coffee. Only the coffee group and
  the reading pair compare different notes, and the reading masks differ in
  scope. All other pairs are within one note.
- Not a prompt change, mask change, score-combination rule, or production
  integration. PPv10 is unchanged; how several masks' scores combine for one
  note under a node remains undecided.

The preserved disagreement (M03 vacuum sealer: predeclared major focus, scored
58/secondary) is shown on the page deliberately. It is not a license for a
prompt rule.

## Files

- `build_review.py` — builder. Reads the study plans, saved inputs, saved
  results, and the layout definition; refuses to build on hash mismatches,
  unplaced cases, duplicate placements, or comparisons split across groups.
- `review-groups.json` — review layout and commentary: groups, predeclared-kind
  notes, preserved disagreements, open questions. This is source, not run data.
- `test_build_review.py` — unit tests plus integration tests over the real saved
  artifacts (skipped when the local-only run data is absent).
- `review.html` — generated, self-contained, read-only page. A derived artifact
  embedding corpus notes and model outputs; excluded from commits by
  `.gitignore`. Regenerate it locally.

## Commands

Run the tests:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 -m unittest discover \
  -s sse_multivector/prominence-prompt-goal-v1/ranking-review-v1 \
  -p test_build_review.py
```

Build the review page:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/prominence-prompt-goal-v1/ranking-review-v1/build_review.py
```

Then open `sse_multivector/prominence-prompt-goal-v1/ranking-review-v1/review.html`
in a browser. Rebuild after any edit to `review-groups.json` or the saved study
artifacts; the footer records every build input with its sha256.

## Reuse

This is a generic prompt-development review pattern: saved cases, predeclared
expectations, mechanical verdicts, and drill-down to exact inputs. To review
another prompt version, add its study artifacts and a new layout definition with
its own version ID; do not revise PPv10 or its grouping in place to fit new
results.
