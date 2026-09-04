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

The subject is fixed. Review its mask in the full original note. `A` approves, `R` disapproves, `C` edits an optional comment, `S` skips, and `Ctrl-C` saves and exits. No requirement to finish the batch. Resuming uses the same session file and does not repeat recorded decisions.

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
