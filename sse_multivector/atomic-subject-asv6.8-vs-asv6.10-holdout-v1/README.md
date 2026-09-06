# ASv6.8 versus ASv6.10: 20-note holdout

ASv6.10 improved the targeted calculation and commentary examples, but the user rejected both subjects in the focused review: the chart-link item and the execution-interpretation item. Unclear slang and non-English coverage remain unresolved. ASv6.8 remains the frozen default.

[Complete notes, all 305 subjects, and per-note analysis](./results.md)

## What happened

The next 20 unused development notes were selected from the frozen 500-note order before generation. Both unchanged prompts ran once on every note: **40 fresh isolated Sol-low calls**, sequentially. All completed on their first attempt. No output edits, masks, SSE, repair calls or default changes.

“Unused” means absent from the saved subject/claim-development inputs and mask-comparison selections listed in [selection.json](./selection.json). It does not mean that no earlier corpus-wide pipeline ever encoded the notes. The audit covered 38 input/selection files; 93 of the 500 corpus notes were excluded, leaving 407 eligible. Selection was mechanical, not based on content.

## What the comparison shows

| Note | ASv6.8 | ASv6.10 |
| --- | --- | --- |
| N12 — additional satoshis | Adds “equivalent to 0.005 bitcoin.” | Keeps 500,000 satoshis; no conversion. |
| N01 — GPU compatibility | Adds that the post does not specify AMD Anti-Lag’s relationship to the other tools. | Names AMD Anti-Lag without that explanation. |
| N02 — previous action | Adds that the action’s exact meaning is uncertain. | “The previous action was up.” |
| N05 — Bitcoin poem | Discusses uncertainty about what “appears” means. | Gives direct literal and metaphorical subjects. |
| N17 — Venezuela | Discusses whether the post describes a plan or urges one. | Gives possible intent and an exhortation directly. |
| N19 — dashboard | Appends an explanation that interpreting “pipes” is uncertain. | Qualifies the actual maintenance subject with “appears.” |
| N18 — exchange listing | Describes the active instruments. | Also adds 12 subjects describing individual chart-link destinations. |

N12 also loses ASv6.8’s proposed interpretation of “Hos Kasi Laguma Karo.” I cannot validate that phrase, so this is **unresolved coverage**, not a demonstrated success or failure. The six notes N01/N02/N05/N12/N17/N19 show the intended wording change, but that is not a measured accuracy rate.

The straightforward text examples retain their main communicated meanings. That does not establish complete coverage across all 20 notes: the slang and non-English phrase remain unresolved. More outputs are not inherently worse: ASv6.8 returned 140 subjects and ASv6.10 returned 165; duplicates and broad/nested subjects are allowed.

## Focused review: both subjects rejected

The saved TUI session records these two rejections, with empty comments. The user supplied the reasons in chat:

1. **N18, ASv6.10 subject 3 — rejected:** “The linked Xport chart page concerns the BX:ABCH pair.” The user stated: “we should not be inferring things in links.”
2. **N03, ASv6.10 subject 2 — rejected:** “Execution” may mean how an unspecified plan or strategy is implemented during the next quarter. The user stated: “we should not be encoding uncertainty INSIDE the subject.”

These requirements led to the separate [ASv6.11 draft](../atomic-subject-asv6.11-proposal-v1/ASv6.11.md), which is untested and awaiting wording approval. The draft excludes URLs from source evidence and replaces ASv6.10's instruction to phrase interpretations as possibilities with direct wording. It also removes the general instruction to preserve uncertainty. All other subject requirements remain unchanged. ASv6.8 remains frozen; the tested ASv6.10 prompt is untouched. No generation was rerun, no output was edited, and no decision was copied to other subjects.

N08's Snow/snow interpretations and N12's non-English phrase remain unresolved, but are not requested in this review. Neither is automatically approved or rejected.

The [review focus](./review-focus.json) preserves all four original review questions, complete source notes and exact subject strings. Its empty decision fields are not the live review session. [Assistant analysis](./assistant-analysis.json) also records the less clear provenance questions in N07, N14 and N20 rather than treating every URL-related subject as invalid.

### Existing review tool

The subject question is “Is this subject supported by the note?” Help explicitly allows broad, narrow, nested, overlapping and duplicate subjects, including reasonable implications. The full-note review retains its coverage and distinctness rows: coverage checks for missing meaning; distinctness only records repetition and does not reject subjects.

The tool verifies the complete original generation run, then `--only` selects which subjects to display. Each screen contains one subject and its full original note. Coverage and distinctness questions are absent from this filtered view. Both original runs remain intact; no fabricated or rebound generation records are used. Saved decisions still use the ordinary full-run session, so excluded subjects are preserved rather than silently approved, rejected or removed.

Reopen only the two ASv6.10 subjects with:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./target/release/sse-mask-review iterate \
  sse_multivector/atomic-subject-asv6.8-vs-asv6.10-holdout-v1/asv6.10/run \
  target/atomic-subject-asv6.8-vs-asv6.10-holdout-v1/asv6.10-review-session.json \
  --only 18:3,3:2
```

`--only` lists note:subject numbers, starting at 1, in display order. A/R records only the displayed subject's decision; C adds an optional comment. Left/right moves between these two subjects; up/down and Ctrl-D/U scroll the note. S moves on without deciding, leaving the subject available next time. Ctrl-C saves and exits. Reopening resumes with the first undecided selected subject; if both are decided, it opens the first for re-review. Removing `--only` opens the unchanged full-note review, including its coverage/distinctness rows.

The earlier wording change passed 78 review regression tests, including a new minimum-size screen/help test. Its rebuilt TUI opened ASv6.10, navigated to N03, scrolled help and paused with zero decisions. The ASv6.8 review session and all 24 non-status comparison artifacts remained byte-for-byte unchanged.

The subject filter passed 84 review tests, including six new tests covering CLI selection, full-note display, decisions, navigation, comments, pause/resume, re-review, invalid selections and generation identity. A terminal check opened exactly the two requested subjects, navigated between them and opened help, then paused with zero decisions. Both existing review-session files and all generation artifacts remained unchanged. No generation calls were made.

## Verification and limits

[Verification](./verification.json) checked 40 distinct threads and working directories, no reuse of the 54 prior comparison calls, one turn per call, no tool activity, exact rendered prompts, raw-output hashes, unchanged exported subject strings and all 93 prior protected files. The seven new frozen input/config/plan files also stayed unchanged. A subsequent documentation-only follow-up link in the prior test README is recorded separately; it does not alter any prior result.

[Runtime](./runtime.json): 4m23.457s for ASv6.8 and 4m28.746s for ASv6.10. Host memory and I/O pressure stayed quiet at sampled checks; available memory remained above 109 GiB. Launcher memory reports of 17M and 16.8M exclude the separate Codex scopes. Existing subscription only; no paid API/rental or credential changes.

| Version | Input tokens | Cached input | Output tokens | Included reasoning tokens |
| --- | ---: | ---: | ---: | ---: |
| ASv6.8 | 41,968 | 1,792 | 7,108 | 4,532 |
| ASv6.10 | 45,136 | 7,680 | 7,149 | 4,564 |

This is one paired generation per note, in two sequential blocks, from an existing frozen corpus—not a repeatability estimate, a random sample of all Nostr, or evidence that every prompt change caused its observed difference. No new default has been approved.
