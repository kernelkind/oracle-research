# Single-subject mask prompt test: fragment boundaries

This tests the approved draft in `target/atomic-subject-mask-prompt-proposal-v3/single-subject-mask-draft.md` against the same 12 fixed ASv6.8 subjects and four original notes used in `../mask-prompt-probe-v2/`.

Only the paragraph about fragment boundaries changed. It permits individual words and says that the fragments need not form grammatical prose. The question is whether that helps select the supplied subject's complete meaning without extra meaning. Preserving readable clauses is a possible explanation of the earlier errors, not an established cause.

## Result

This run does not establish an overall improvement.

- M05 selects meditation, understanding, and life without the separate withdrawal claim. However, its raw JSON puts the fragments in the wrong source order.
- M07 still includes state backing, outside the supplied cryptocurrency-settlement subject.
- M09 still omits the identifying word Bitcoin.
- M11 now omits the CEO incident entirely. Its v2 mask included too much incident detail; this output includes none.
- M02 and M03 mostly change conjunctions or fragment boundaries. M12 has mixed changes. More fragments do not necessarily mean better scope selection.
- M01, M04, M06, M08, and M10 are byte-identical to v2.

These are independent assistant observations across the whole batch, not user approvals. There was one call per subject, so this does not establish a reliable success rate or prove that the prompt change caused each difference. The per-item analysis is in `assistant-review.json`.

## Review

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./target/release/sse-mask-review review-masks \
  sse_multivector/mask-prompt-probe-v3/mask-review.json \
  target/atomic-subject-mask-probe-v3/review-session.json \
  --start-at M05
```

Every item contains its fixed subject, full original note, and inline mask. Left/right changes items; up/down scrolls within the note. Stop at any time. The review starts without copied decisions. The separate `ui-smoke-session.json` was used only to open M05, navigate to M06 and M07, and exit; it contains no decisions or comments.

M05 display preparation is explicit: the raw response lists Meditation, the understanding phrase, then life. The source places life before the understanding phrase. Every fragment has one exact occurrence, so the review batch sorts these unchanged fragments into source order for display only. No words were added, removed, or rewritten. The raw response is unchanged, and `mechanical-checks.json` records its source-order failure. `review-preparation.json` records the mapping.

## Controls and validation

All 12 calls used fresh isolated contexts through the existing subscription-authenticated Codex runner. The model stayed `gpt-5.6-sol` with `low` reasoning. The pinned Codex binary, wrapper, minimal instructions, and isolation settings match v2. Calls were sequential, with no retries. Twelve distinct threads and working directories were recorded; no threads were shared with v1 or v2, and no tool actions were recorded.

All 12 outputs are JSON string arrays containing exact source text. Eleven comply with source order; M05 does not. All mapped ranges are non-overlapping. Mechanical checks do not establish semantic correctness. The production review tool validated the prepared batch before rendering it.

The run used 27,248 input tokens and 492 output tokens, including 131 reasoning output tokens. Service runtime was 65.146 seconds. The process ran under a 2 GiB memory cap, zero swap allowance, and a 900-second timeout. Systemd reported a 16.8M memory peak and 0B swap. Calls consumed the existing Codex subscription allowance; no paid API or rented compute was used.

ASv6.8, the mask registry, prior results, and prior user review files were not changed. No subject generation, SSE encoding, fine segmentation, or production-code changes were performed. This mask prompt is not frozen.

## Files

- `mask-prompt.md`: exact approved prompt used for the run.
- `selection.json`: unchanged input subjects and original notes.
- `config.json` and `run/`: exact rendered inputs, raw outputs, and execution records.
- `mask-review.json`: full-note review presentation.
- `mechanical-checks.json` and `review-preparation.json`: source matching, order validation, and the M05 display-only reorder.
- `assistant-review.json`: independent analysis of all 12 outputs against v2.
- `verification.json`: identity checks, isolation, usage, resource limits, and production-TUI smoke result.

Selected inputs, final answers, recorded reviews and parameters: `historical-studies/mask-prompt-probe-v3`. See the [publication catalog](../../docs/experiments/publications.csv) and [dataset manifest](../../docs/experiments/downloads.md#dataset-manifest).
