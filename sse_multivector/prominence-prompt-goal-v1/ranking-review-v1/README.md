# PPv10 node-note order review v1

Read-only review of the saved PPv10 scores in the units the goal actually uses:
**hierarchy nodes and their node-note order**. The consumer of prominence is
task **27 · Order node notes using mask prominence** — when a user opens a
hierarchy node, the notes most directly about it should come first. Each card
shows one saved HDBv2 node with its member masks across notes and the order the
saved scores produce, so the judgment is node-note order, not isolated scores.

Prompt reviewed: **PPv10 — user-approved, tested experimentally, not
production-frozen** (source [PPv10.md](../ppv10-draft-v1/PPv10.md), sha256
`d40835fb0b104865727c0b0a2bde4074afb642991d9bddc424d5379ef4b038ea`, verified at
build time). The production registry still freezes PPv2 and is untouched.

Node membership is the saved **HDBv2** (`hdbscan-cross-note`) assignment of
[real-note-fine-segmentation-v1](../real-note-fine-segmentation-v1/). This
review reads that membership and changes nothing about it.

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

- Five cards: the three nodes that contain saved scores, then the two placement
  gaps. Left/right moves between cards; `--start-at S9c440e7f47` reopens one.
- Each node card title states its size and whether its order is supported:
  complete, partial, or unscored. The first pane follows the verified review-UI
  conventions: each member mask on its own line as `V276  ⟦coffee⟧` (bracketed
  fragments separated by spaces, blank lines between masks), above the note's
  complete, unchanged text. The exact scorer input is under `i`.
- `i` shows the exact scorer inputs for the card's scored masks. The output
  pane is the saved model output verbatim, one line per scored mask. The
  comment pane is assistant text: assessment, the produced order, predeclared
  order checks with mechanical verdicts, predeclared expectations, scorer
  provenance, and the standing limits.
- The displayed order is a **mechanical display of saved scores**. Where one
  note contributes multiple masks to a node, no sum/max/average is applied:
  task 27's combination rule is undecided and is flagged on the card.

## The five cards

- **S9c440e7f47** (2 notes, 2 masks) — order complete: second-coffee hashtag
  post 88 ahead of the animal-ethics-quotation post 2. The only node whose
  order is fully backed by saved scores; the predeclared cross-note check is
  ordered with gap 86.
- **Sbb8511308a** (3 notes, 4 masks) — order partial: two notes scored at 95
  (no order predeclared between them), one note unscored, and N035 contributes
  two overlapping masks (V276 scored, V277 unscored) — the undecided task-27
  combination case in the flesh.
- **S68ce4fd21f** (4 notes, 9 masks) — order unscored: only the today-is-a-gift
  mask has a score (18); three notes carry multiple masks. Saved scores cannot
  order this node at all.
- **Unassigned masks** (8 scored masks in no node) — the task-24 membership gap.
  These scores currently order nothing. The M05/M06 within-note pair even
  crosses placements: one mask is unassigned, its sibling sits in S68ce4fd21f.
- **Outside the hierarchy corpus** (6 control masks) — notes from earlier
  mask-prompt assessments, including the baby/Nostr within-note control. No
  node placement exists for them; prompt-behavior evidence only.

The preserved disagreement stays visible: M03's vacuum sealer was predeclared
as major focus and scored 58/secondary. It is not a license for a prompt rule.

## What this is not

- Not new inference, and not a membership or clustering change. Nothing
  regenerates masks, scores, or requests; no node assignment is edited.
- Not a combination rule. Multiple masks per note per node, and notes arriving
  through shared descendants, are shown as open task-27 questions.
- Not an accuracy rate. Predeclared expectations and order checks are assistant
  judgments, not user-approved gold labels.
- Not evidence where placement is missing: outside S9c440e7f47 the saved
  coverage cannot produce a full node order. Comparable saved scores for each
  node's remaining masks are the missing evidence.

## Files

- `review-groups.json` — node card order, per-node commentary, gap sections,
  preserved disagreements, open questions (source, tracked).
- `build_review.py` — builder; joins study scores to HDBv2 membership and
  refuses to build on prompt-hash mismatches, undeclared placements, coverage
  gaps, or any schema-1 violation the review tool would reject.
- `test_build_review.py` — unit tests plus integration tests over the real
  saved artifacts and the release review binary (skipped where local-only).
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
