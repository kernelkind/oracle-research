# Token estimate for 1 million notes

Estimate saved September 14, 2026. Model: **Astra low** (`gpt-6-astra`, reasoning effort `low`). This records the estimate discussed in chat, using existing measurements; no new model calls were made.

**Working estimate: approximately 30 billion tokens**, using the current subject, mask and node-title prompts through our existing isolated Codex runner. This is a rough planning estimate, not the minimum tokens these tasks inherently require.

## Estimate

| Step | Prompt | Calls | Input tokens | Output tokens |
|---|---|---:|---:|---:|
| Generate subjects | ASv6.23 | 1 million | 2.62 billion | 405 million |
| Generate masks | MPv3.5 | 9.8 million | 24.28 billion | 1.13 billion |
| Generate node titles | v21 | 610,000, illustrative | 1.41 billion | 60 million |
| **Total** | | **11.4 million** | **28.31 billion** | **1.59 billion** |

Before titles, subject and mask generation account for approximately **28.43 billion tokens**. The illustrative title allowance adds **1.47 billion**, giving **29.90 billion** overall. Totals use unrounded averages.

Masking accounts for about 85% of that total. The subject generator produces all subjects in one call per note, but the mask generator receives the complete note again in a separate call for every subject. Title generation takes one call per node; the two trials used in our prompt experiments do not imply two calls per production node.

## Measured basis

The extraction measurements cover 248 real notes: the original 100 food/drink notes, 100 music notes, and 48 coverage-expansion notes. All calls below used Astra low.

| Step | Recorded calls | Average input per call | Average output per call |
|---|---:|---:|---:|
| Subjects | 248 | 2,618.4 | 404.9 |
| Masks | 2,436 | 2,471.9 | 114.8 |
| Node titles, v21 | 24 | 2,310.3 | 99.2 |

The subject calls generated 2,435 subjects: **9.82 subjects per note** on average. One subject was excluded before masking. There were 2,434 distinct mask jobs plus two additional mechanical-retry calls, giving the 2,436 recorded mask calls used above. Quota failures without reported token usage were not included or assumed to have a measured zero cost.

Extraction totals used for the calculation:

| Dataset | Subject input | Subject output | Mask input | Mask output |
|---|---:|---:|---:|---:|
| Food/drink, 100 notes | 262,180 | 37,939 | 2,342,547 | 95,269 |
| Music, 100 notes | 262,680 | 44,959 | 2,687,175 | 134,366 |
| Coverage expansion, 48 notes | 124,509 | 17,516 | 991,919 | 49,966 |
| **Total** | **649,369** | **100,414** | **6,021,641** | **279,601** |

The title measurements are the 12 v21 calls in the first comparison plus the 12 v21 calls on six additional groups: **55,448 input and 2,380 output tokens**. The v20 comparison calls and later deduplication reruns are excluded from this title average.

As a separate cross-check, the subject prompt's 60 first-trial final-validation calls averaged 9.68 subjects per note, 2,646.7 input tokens and 434.1 output tokens. They are not added to the 248-note calculation.

## Assumptions and uncertainty

**Subjects per note.** The sample average is not a population estimate for all Nostr content. These are selected, mostly short notes concentrated in food/drink and music. Other lengths, languages and subject mixtures can change both the number of mask calls and their input/output lengths.

Holding the measured per-call lengths fixed illustrates the effect of subject count:

| Average subjects per note | Subject and mask tokens for 1 million notes, before titles |
|---:|---:|
| 5 | 16.0 billion |
| 10 | 28.9 billion |
| 15 | 41.8 billion |

This is a sensitivity calculation, not a confidence interval. Longer notes may produce both more subjects and longer mask inputs, so those quantities need not vary independently.

**Number and size of nodes.** The 610,000-node allowance simply scales the original 61 accepted nodes from 100 notes. It is **not a prediction** of how categories will grow with the corpus. At the measured small-group sizes, every 100,000 title calls adds approximately **241 million tokens**. Larger groups contain more masks and require longer title inputs; the measured per-node average cannot be assumed unchanged for them.

## What the token counts include

These are the **total input and output counts reported by Codex**, not a local token count of only our written prompts and notes.

The earlier phrase “runner input overhead” was too specific: we have **not separately measured the overhead amount or established exactly where it comes from**. Input accounting includes request formatting, such as message roles and boundaries, in addition to the supplied text. Our wrapper uses fresh contexts and excludes conversation history, AGENTS.md, tools and optional injected instructions; it retains the minimal instruction “Follow the user's instructions.” This does not establish the full service-side request contents. [OpenAI token-counting documentation](https://developers.openai.com/api/docs/guides/token-counting)

Consequently, the 30-billion figure estimates the current execution path. It is not a verified minimum for a direct API implementation, and it does not establish how many tokens a different execution path would save.

Output counts already include reasoning tokens. Cached input tokens are already included in input counts. Neither should be added again. No future cache-hit rate or monetary cost is assumed. [Output-token accounting](https://developers.openai.com/api/docs/guides/token-counting#understand-output-token-counts)

There is no additional allowance for future retries, semantic review, prompt-development work, subsumption checks or other hierarchy-generation calls. SSE encoding and clustering are outside this LLM-token estimate.

## Saved evidence

- [Frozen ASv6.23 package](subject-prompt-goal-v1/asv6.23/frozen.json) and [final-validation verification](subject-prompt-goal-v1/asv6.23-validation-v1/final/verification.json).
- [Frozen MPv3.5 package](mask-prompt-goal-v1/frozen.json).
- [Real-note experiment record](real-note-fine-segmentation-v1/README.md). Raw usage is in each call's `run/results.jsonl`, under `subjects-001-010`, `subjects-011-100`, `masks-001-010` and `masks-011-100`.
- Music usage comes from `real-note-fine-segmentation-v1/music-generation-v1`, including its two mechanical mask retries. [Extraction integrity](real-note-fine-segmentation-v1/music-generation-v1/extraction-integrity.json).
- Coverage-expansion usage comes from `real-note-fine-segmentation-v1/coverage-expansion-v1/subjects` and `masks`. [Experiment record](real-note-fine-segmentation-v1/coverage-expansion-v1/README.md).
- [v21 comparison](hdbv2-node-description-probe-v21/comparison.json) and [v21 additional groups](hdbv2-node-description-probe-v21-additional-v1/comparison.json), with raw usage under their `calls` directories. [Exact v21 prompt](hdbv2-node-description-probe-v21/prompt.txt).

For extraction, sum the successful calls' `usage.input_tokens` and `usage.output_tokens` separately by stage, then multiply each total by `1,000,000 / 248`. For titles, divide the 24-call totals by 24 and multiply by the assumed node count. This reproduces the unrounded total of approximately 29.90 billion tokens when assuming 610,000 nodes.
