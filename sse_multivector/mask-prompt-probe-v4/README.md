# Single-subject mask prompt test: identifying references

This runs the approved draft from `target/atomic-subject-mask-prompt-proposal-v4/single-subject-mask-draft.md` on the same 12 fixed ASv6.8 subjects and four original notes as `../mask-prompt-probe-v3/`.

Only the interpretation/completeness paragraph changed. It distinguishes understanding a reference through the complete post from selecting the source words that identify what the reference means. Fragment flexibility and the other prompt rules remain unchanged.

## Result

Mixed result; the new instruction is not consistently followed.

- M09 now includes Bitcoin, which the previous mask omitted.
- M05 now omits life and selects the understanding of it. Its source order is valid, but its identifying text is worse than the previous selection.
- M07 still includes state backing, outside the supplied settlement subject.
- M11 still selects only this development changes my entire thesis, without identifying the CEO incident.
- M12 drops the all-employee-call setup and retains the CEO/gossip evidence and investment-style language. This addresses an assistant concern about the previous output; the user had not supplied a rejection reason.
- Nine of the 12 generated fragment arrays are unchanged from v3, including M07 and M11.

These are assistant observations, not new human approvals. Each subject received one call. This does not establish a reliable success rate or prove that a particular difference was caused by the prompt edit. All 12 items are assessed separately in `assistant-review.json`.

## Review

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./target/release/sse-mask-review review-masks \
  sse_multivector/mask-prompt-probe-v4/mask-review.json \
  target/atomic-subject-mask-probe-v4/review-session.json \
  --start-at M05
```

The review shows each fixed subject above its full original note with inline masks. Left/right changes items; up/down scrolls within the note. Stop at any time. Earlier decisions are not copied. The separate terminal-smoke session contains no decisions or comments.

M09 has a source-position ambiguity: the returned string Bitcoin appears twice before the other fragments. The model did not identify which occurrence it intended. The review shows the first compatible occurrence for display only. Both valid assignments and the display choice are recorded in `review-preparation.json`. No generated words or fragment order were changed, and no SSE encoding was performed.

## Controls and validation

The 12 calls were sequential, with no retries, using the existing subscription-authenticated Codex runner. Model `gpt-5.6-sol`, reasoning `low`, pinned Codex binary, wrapper, minimal instructions, and isolation settings match v3. The exact prompt matches the reviewed draft, SHA-256 `564c860a3be5f8eb6e90c404184ef467f24004276dbb535f637ba0a8ded7ff9e`.

The records contain 12 distinct threads and 12 distinct working directories, none shared with v1, v2, or v3. Tools and web were disabled; no tool actions were recorded. Raw responses, exact rendered prompts, and execution records are preserved under `run/`.

All 12 responses are JSON string arrays with exact source fragments, no prohibited identifiers, and at least one non-overlapping placement in source order. Eleven have a unique placement; M09 has two. Mechanical validity does not establish semantic correctness. The production review tool validated all items, opened M05, navigated through M06–M09, and exited without recording decisions.

The run used 27,524 input tokens and 488 output tokens, including 127 reasoning output tokens. Service runtime was 61.754 seconds. The service was limited to 2 GiB RAM, zero swap, and 900 seconds; systemd reported 16.7M peak memory and 0B swap. Only existing Codex subscription allowance was used; no paid API or rented compute.

ASv6.8, prior prompts/results/reviews, and prompt registries remain unchanged. No production-code changes, subject generation, SSE vectors, segmentation, or hierarchy work. This mask prompt is not frozen.

## Files

- `mask-prompt.md`: exact approved prompt.
- `selection.json`: unchanged fixed subjects and full source notes.
- `config.json` and `run/`: exact generation inputs and raw responses.
- `mask-review.json`: review input with full original notes.
- `mechanical-checks.json` and `review-preparation.json`: source validation and M09's occurrence ambiguity.
- `assistant-review.json`: independent per-item analysis against v3.
- `verification.json`: execution identity, isolation, usage, resources, and terminal smoke checks.
