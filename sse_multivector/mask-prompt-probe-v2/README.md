# Revised single-subject mask prompt probe

The same twelve ASv6.8 subjects and four original notes as `../mask-prompt-probe-v1/`, in the same order. Only the mask instructions changed. The tested prompt matches the reviewed draft byte-for-byte.

Each subject received one fresh isolated `gpt-5.6-sol` / `low` call through the unchanged `codex_exec.py` wrapper and pinned Codex binary. All twelve calls succeeded on their first attempt. Their twelve thread IDs and working directories are distinct; no thread was reused from the first probe. Tools, web search, repository context, and conversation reuse were disabled. Inputs contain only the fixed subject, full original post, and approved mask instructions.

## Review

From the Oracle MVP repository:

```sh
./target/release/sse-mask-review review-masks \
  sse_multivector/mask-prompt-probe-v2/mask-review.json \
  target/atomic-subject-mask-probe-v2/review-session.json
```

The new review starts without any decisions. Previous approvals and rejections have not been copied into it. A/R records a decision, C adds an optional comment, left/right browses all items, up/down scrolls the note, and Ctrl-C saves and exits. You can stop at any time. Append `--start-at M02` to open that item directly.

## What changed

M06 now includes the missing Krishnamurti attribution. M02 drops the other astronauts, but still includes participation wording. M07 drops Iran launching the platform but keeps state backing. M03 is substantively unchanged; M05 and M09 retain the previously identified problems. M01, M04, M08, and M10 preserve their previously approved meanings. M11 and M12 had no prior human judgment.

These are assistant observations, not automatic approvals. A single run does not establish a reliable success rate or prove which changes were caused by the prompt.

## Evidence

- `mask-prompt.md`: exact prompt used; not a newly frozen default.
- `selection.json`: byte-identical selection from the first probe.
- `config.json`: all twelve exact rendered prompts and unchanged model settings.
- `run/`: untouched generation manifest, raw responses, event records, usage, and minimal model instructions.
- `mask-review.json`: generated strings mechanically located in their original notes; no text corrections.
- `mechanical-checks.json`: exact-source, source-order, non-overlap, location, and identifier checks.
- `assistant-review.json`: item-by-item comparison with the original masks and baseline human decisions.
- `verification.json`: reproduction, isolation, usage, resource limits, and review-tool verification.

All twelve arrays contain exact source fragments with one valid non-overlapping placement in source order. M02's first fragment, `Zhang Lu`, occurs twice on its own; the order of all three fragments uniquely places it at the earlier occurrence. Mechanical validity is not semantic correctness.

Generation consumed 26,840 input tokens (1,920 cached) and 831 output tokens, including 402 reasoning tokens. The service ran for 71.113 seconds with a 2 GiB memory cap and no swap allowance; systemd reported a 16.7M memory peak and 0B swap. This used existing Codex subscription allowance, not paid API calls. No SSE, segmentation, or subject generation was run.
