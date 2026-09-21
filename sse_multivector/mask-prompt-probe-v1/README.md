# Single-subject mask prompt probe

Twelve masks for twelve unchanged ASv6.8 subjects, selected from four existing notes before mask generation. Three subjects each cover the spaceflight announcement, meditation quotation, Iran/Bitcoin post, and CEO post.

Each subject received one fresh, isolated `gpt-5.6-sol` / `low` call through `codex_exec.py`. Calls ran sequentially. The run used 12 distinct sessions and working directories, with tools and web search disabled. No subject generation, SSE encoding, or segmentation was run.

## Review

From the Oracle MVP repository:

```sh
./target/release/sse-mask-review review-masks \
  sse_multivector/mask-prompt-probe-v1/mask-review.json \
  target/atomic-subject-mask-probe-v1/review-session.json
```

The subject is fixed. Review its mask inline in the full-width original note. When the review input supplies an `assessment`, it appears in a separate “My reasoning” panel below the note; it is not a saved decision. `←` and `→` move between items, including reviewed items, without changing any decisions. `Tab` switches panels; `↑`/`↓` or `j`/`k` scroll the active panel. The heading shows the current item's saved decision.

`A` approves, `R` disapproves, `C` edits an optional comment, `S` records a skip, and `Ctrl-C` saves and exits. A new decision replaces only the current item's decision, then advances to an unfinished item. No requirement to finish the batch. Resuming normally starts at the first unfinished item.

To open M08 directly, including after the batch is complete, append `--start-at M08`:

```sh
./target/release/sse-mask-review review-masks \
  sse_multivector/mask-prompt-probe-v1/mask-review.json \
  target/atomic-subject-mask-probe-v1/review-session.json \
  --start-at M08
```

Use `target/atomic-subject-mask-probe-v1/review-session-rereview-v1.json` instead of the original session path for the fresh rereview. This keeps the original review separately preserved.

## Preserved evidence

- `mask-prompt.md`: exact tested prompt; not a new frozen default.
- `selection.json`: original notes, unchanged subjects, and source indices.
- `config.json`: all twelve exact prompts and model settings.
- `run/`: original generation manifest, raw responses, event records, usage, and model instructions.
- `mask-review.json`: generated fragments mapped mechanically to their exact occurrences in the original notes. No manual corrections.
- `mechanical-checks.json`: all twelve outputs are exact source text, in source order, with unambiguous locations and no prohibited identifiers selected.
- `assistant-review.json`: observations for discussion, not user decisions or an automatic acceptance result.

The raw files were copied byte-for-byte from `target/atomic-subject-mask-probe-v1/`; paths recorded inside the original provenance still refer to that location. Reproduction should use a new run directory, not overwrite this run.

Generation used 26,840 input tokens and 591 output tokens over 62.6 seconds. It consumed existing Codex subscription allowance, not paid API calls. The generation process had a 2 GiB memory limit and no swap allowance.

Mask correctness still awaits user review. Mechanical validity is not semantic correctness.
