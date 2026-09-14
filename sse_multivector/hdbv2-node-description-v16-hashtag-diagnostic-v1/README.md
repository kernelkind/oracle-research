# V16 hashtag diagnostic

Restoring the original hashtag markers produced “Dogs” in all three calls. Without them, one call produced “Dogs” and two produced string-based titles.

## Inputs and complete results

The only changed input was the two `#` characters:

- Original: instance 1 ⟦dogstr⟧; instance 2 ⟦dog⟧.
- Restored: instance 1 ⟦#dogstr⟧; instance 2 ⟦#dog⟧.

| Trial | Original input | Hashtag markers restored |
|---|---|---|
| 1 | Text strings beginning with “dog” | Dogs |
| 2 | Dogs | Dogs |
| 3 | Strings Beginning with “dog” | Dogs |

These are all six exact outputs. Trial numbers identify independent repetitions, not shared model contexts. No output was selected as the best response.

## What this tells us

The result supports omitted hashtag context as a contributor to this group's failure. V16 can name the intended subject without a prompt rewrite when that clue is present.

The original-input success also matters: the model is not consistently unable to interpret `dogstr`. Its output is unstable on that input. Three calls per condition do not establish a reliable success rate, rule out chance, or prove hashtag omission is the sole cause. This has not tested other tags or shown that restoring syntax is always helpful.

No permanent mask or title-input change follows automatically. V16 remains unfrozen. The earlier dog failures remain valid observations of the original input; they were not overwritten.

## What stayed fixed

- Exact approved v16 template and numbered quoted-instance format; no new prompt instruction or example.
- gpt-5.6-sol / low, pinned Codex 0.153.0 and unchanged isolated wrapper.
- Six fresh processes, threads and empty workspaces; all succeeded on attempt 1. Concurrency capped at three.
- No full notes, group IDs, expected titles, previous outputs or reviewer comments in model input. No tools, web or response schema.
- Only the original source `#` markers were restored. UTF-8 bytes confirm them immediately before spans [1002,1008) and [276,279). Canonical masks, vectors and HDBSCAN groups were untouched.
- Existing subscription only; no new API billing, credentials changes, downloads or rentals.
- Usage: 10,776 input tokens, zero reported cached input tokens; 407 output tokens including 358 reasoning tokens.

## Saved evidence

[run-plan.json](./run-plan.json) was saved before the six calls. [source-packet.json](./source-packet.json) preserves both full original notes and masks. [results.json](./results.json) records every output, assessment, usage and integrity checks. Each condition's `trial-{1,2,3}/` preserves its exact config, raw output and execution record.

An independent audit confirmed exact inputs, source-byte adjacency, settings, hashes, fresh threads/workspaces and all six outputs. Its assessment agrees with the conclusion above. The invoking executor used `max_workers=3`; per-call records alone lack the timestamps needed to independently reconstruct peak concurrency.

The two [earlier v16 dog results](../hdbv2-node-description-probe-v16/comparison.json) are preserved separately, not counted as fresh trials here. The [v16 run record](../hdbv2-node-description-probe-v16/README.md) retains the user's accepted titles and original assessments.

The [official GPT-5.6 guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6#prompt-migration-workflow) informed changing one input feature while keeping the prompt and execution settings fixed. It does not establish the semantic interpretation or generalizability of this result.
