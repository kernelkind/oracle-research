# PPv10 node-note order review v1

The **node-note walk**: one complete note per card, stepped in the order the
saved PPv10 scores produce for each saved HDBv2 node. This is the product
experience under review — open a hierarchy node, read its notes in order — so
the judgment is exactly: do the most-about-the-node notes come first? The
consumer of prominence is plan task **27 · Order node notes using mask
prominence**.

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

- 19 cards, one complete note each. `←/→` steps the walk; `--start-at ID`
  reopens a card. The note pane is the complete, unchanged note.
- The card title is its place in the walk: `node · position n of m · note ·
  score`. The comment is a few lines only: the mask line
  (`V244  ⟦coffee⟧ — score 88`, the verified fragment form), at most one
  flag (multi-mask combination undecided, or position unknown), and any
  predeclared check that involves this note.
- `i` shows the exact scorer input (the mask/marked-post JSON). The output
  pane is the saved model response verbatim.
- Analysis lives here in the README, not in the cards.

## The walk

- **S9c440e7f47 "Coffee"** — 2 notes in this packet, order complete:
  second-coffee post (88) then the animal-ethics-quotation post (2).
- **Sbb8511308a "Coffee"** — 3 notes, order partial: two posts at 95 (no order
  predeclared between them), dog-coffee post unscored, and one post carries two
  overlapping masks (V276 scored, V277 unscored).
- **S68ce4fd21f** (no saved title) — 4 notes, order mostly unknown: only the
  today-is-a-gift mask is scored (18); three posts carry multiple masks.
- **Unassigned** — 5 notes / 8 masks in no node (task 24). Their scores order
  nothing until membership recovery places them.
- **Outside the corpus** — 5 notes / 6 control masks, including the baby/Nostr
  within-note control (94 vs 3 on one note). No node placement exists.

Node titles are the saved ones, not paraphrases: `hdbv2-node-titles-v21-astra-low`
records `Coffee` for both coffee nodes (assistant-accepted, no user approval on
record); the TRUE14 hierarchy label for S9c440e7f47 is also `Coffee`. S68ce4fd21f
has no saved title — it is one of three groups excluded from the v15 title runs
(61 of 64 accepted). Saved user semantic-review verdicts
(`real-note-fine-segmentation-v1/review-handoff/baseline/user-response.json`):
S9c440e7f47 valid, Sbb8511308a valid, S68ce4fd21f none on record.

Hierarchy context worth knowing while reviewing: in the TRUE14 navigation
hierarchy, `Coffee` (S9c440e7f47) is a parent node with four child nodes and 22
notes including descendants, while this packet's own membership is 2 masks / 2
notes. Ordering a node's notes across shared descendants is part of task 27 and
is not decided by this walk.

## Analysis (kept out of the cards)

Mechanical checks on the predeclared pairs: 7 ordered, 0 ties, 0 reversed —
not an accuracy rate; the expectations were assistant predeclarations recorded
before inference, not user-approved gold labels.

| Predeclared pair | Result | Note |
| --- | --- | --- |
| R03 > R04 | holds (88 vs 2) | the only check inside one node |
| R01 > R04, R02 > R04 | holds (95 vs 2) | spans two nodes — not a node-note order |
| R07 > R08 | holds (94 vs 3) | within one note; control only |
| M01 > M02, M03 > M04, M05 > M06, M11 > M10 | hold | all unassigned or crossing placements |
| M08 > M07 | holds (92 vs 18) | different mask scopes; informational |
| R05 > R06 | holds (86 vs 85) | predeclared tentative; gap means nothing |

Preserved disagreement: M03's vacuum sealer was predeclared as a major focus
(70–89) and scored 58/secondary. The post also covers meat preparation and
animal feed, so the boundary is arguable, and no node-note order is affected
yet. Not a license for a prompt rule.

Open questions: eight scored masks are in no node (task 24) and order nothing;
only S9c440e7f47 has complete saved scores, so comparable scores for each
node's remaining masks are the missing evidence; and how one note's several
masks in a node combine is undecided (task 27) — no sum/max/average is applied
anywhere here.

Limits: one saved call per mask (gpt-6-astra low via openai-codex); masks and
node membership are unchanged saved inputs from several extraction versions;
prominence is not mask correctness, category membership, truth, quality,
usefulness, or personal interest; this review changes no membership and
validates neither clustering nor titles; PPv10 is not production-frozen.

## Files

- `review-groups.json` — walk layout: node ids, gap sections, preserved
  disagreements (source, tracked).
- `build_review.py` — builder; joins study scores to HDBv2 membership and
  loads saved node titles and user verdicts; refuses to build on prompt-hash
  mismatches, undeclared placements, coverage gaps, or any schema-1 violation
  the review tool would reject.
- `test_build_review.py` — unit tests plus integration tests over the real
  saved artifacts and the release review binary (skipped where local-only).
  Pins include: every card is one complete note byte-verbatim with no marks or
  crammed blocks, and comments stay short.
- `run-review.sh` — launcher used above.
- `review.json` — generated batch; derived run data, excluded from commits.

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
