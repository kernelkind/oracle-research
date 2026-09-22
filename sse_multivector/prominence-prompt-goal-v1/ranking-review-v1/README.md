# PPv10 prominence ranking review v1

Read-only review of the saved PPv10 scores grouped by selection meaning, in the
existing `model-output-review` UI. The question it presents: when a category is
opened, do the notes most directly about it sort first?

Prompt reviewed: **PPv10 — user-approved, tested experimentally, not
production-frozen** (source [PPv10.md](../ppv10-draft-v1/PPv10.md), sha256
`d40835fb0b104865727c0b0a2bde4074afb642991d9bddc424d5379ef4b038ea`, verified at
build time). The production registry still freezes PPv2 and is untouched.

## Open the review

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./sse_multivector/prominence-prompt-goal-v1/ranking-review-v1/run-review.sh
```

The launcher opens the saved batch with the prebuilt `model-output-review`
binary — no downloads, no model calls; the UI is read-only and saves no
decisions. If that binary is missing, the launcher first builds it through Nix
with two build jobs (large toolchain download); set `REVIEW_REBUILD=1` to force
that build.

- One card per saved mask/post pair, 19 cards across 13 notes. Left/right moves
  through the score-sorted sets; `--start-at R03` reopens a card by case ID.
- The card title names the group, the case label identifying the selection, its
  rank in the score-sorted set, the saved score, and its PPv10 anchor band. The
  first pane is the complete source note.
- `i` shows the exact scorer input: the one JSON object with `mask` and
  `marked_post`. The output pane is the saved model output verbatim. Tab picks
  which pane up/down scrolls.
- The comment pane is assistant text, separate from the saved output: which
  selection this card scores first, then the post-hoc assessment, the group's
  predeclared order checks with their mechanical verdicts, the predeclared
  expectation recorded before inference, scorer provenance, and the standing
  limits.
- Score-sorted display order is a viewing choice, not a claim that any order is
  uniquely correct.

## What is grouped

Eight groups with comparable saved selections, cross-note groups first, each
sorted by saved score, plus one singleton. Full layout and commentary in
[review-groups.json](review-groups.json).

- G1 coffee across notes (95, 95, 88 vs 2) — the three clear cross-note
  comparisons order as expected with large gaps; the hashtag control holds.
- G2 coffee shops across notes (86 vs 85) — predeclared tentative; the gap
  establishes no meaningful separation.
- G3 reading across notes (92 vs 18) — ordered, but the masks differ in scope;
  informational only, not a controlled identical-meaning test.
- G4–G8 within-note pairs (94/3, 43/22, 58/19, 73/18, 78/47) — clear pairs all
  ordered as expected; the meal/workshop pair was tentative.
- M09 (96) has no predeclared comparison and supports nothing about ordering.

Mechanical tally on the seven clear predeclared pairs: 7 ordered, 0 ties, 0
reversed. This is not an accuracy measurement; the expectations are assistant
predeclarations, not user-approved gold labels.

The preserved disagreement stays visible: M03's vacuum sealer was predeclared as
a major focus and scored 58, which is secondary. Not a license for a prompt rule.

## What this is not

- Not new inference. The builder reads saved artifacts only; nothing regenerates
  masks, scores, or requests.
- Not evidence for cross-note ranking outside coffee. Only G1 and G3 compare
  different notes; every other pair is within one note. Comparable saved masks
  outside coffee remain the missing evidence.
- Not a prompt change, score-combination rule, or production integration.
  How several masks' scores combine for one note under a node is undecided.
- The separate one-call Muse probe in
  [ppv10-mpv3.43-muse13high-v1](../ppv10-mpv3.43-muse13high-v1/README.md) is not
  in this batch; it has no predeclared expectation and stays in its own context.

## Files

- `review-groups.json` — review layout and commentary (source, tracked).
- `build_review.py` — builder; refuses to build on prompt-hash mismatches,
  unplaced cases, duplicate placements, comparisons split across groups, or any
  schema-1 violation the review tool would reject.
- `test_build_review.py` — unit tests plus integration tests over the real saved
  artifacts and the release review binary (skipped where local-only).
- `run-review.sh` — launcher used above.
- `review.json` — generated batch; derived run data, excluded from commits.
  Regenerate after any change to the layout or saved artifacts.

## Commands

Regenerate the batch:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/prominence-prompt-goal-v1/ranking-review-v1/build_review.py
```

Validate without opening a terminal:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
./target/release/model-output-review \
  sse_multivector/prominence-prompt-goal-v1/ranking-review-v1/review.json --check
```

Run the tests:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 -m unittest discover \
  -s sse_multivector/prominence-prompt-goal-v1/ranking-review-v1 \
  -p test_build_review.py
```
