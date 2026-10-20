# Token estimate for 1 million notes

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../docs/experiments/README.md#reading-the-research-records).

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

## Lower-cost annotation models

Research saved September 15, 2026. The question is whether another hosted model can generate subject and mask training labels at approximately Astra-low quality for less money. This is **teacher-model selection**, not selection of the smaller model we will fine-tune. The user accepted this shortlist as reasonable; no candidate has been tested on our task and no paid run is authorized by this record.

The research screened the public Artificial Analysis and OpenRouter catalogs, including discounted tiers and provider-specific routes. Artificial Analysis supplies capability signals; **all prices below come from OpenRouter**. The current frozen prompts, ASv6.23 and MPv3.5, and the Astra-low baseline remain unchanged.

### Ranked shortlist

This is a ranking of candidates worth testing, not a demonstrated ranking of annotation accuracy.

| Priority | Model and AA benchmark setting | AA Intelligence Index | AA knowledge accuracy | OpenRouter dollars per million input / output tokens | Same-token cost per 1,000 notes |
|---|---|---:|---:|---:|---:|
| 1 | [Muse Spark 1.3, max](https://artificialanalysis.ai/models/muse-spark-1-3), using Contributor | 48.2 | 43.6% | [0.10 / 0.20](https://openrouter.ai/meta/muse-spark-1.3-contributor) | **$3.00** |
| 2 | [DeepSeek V4.1 Flash, max](https://artificialanalysis.ai/models/deepseek-v4-1-flash) | 39.5 | 46.4% | [0.15 / 0.60](https://openrouter.ai/deepseek/deepseek-v4.1-flash) | **$4.95** |
| 3 | [GLM 5.3 Flash](https://artificialanalysis.ai/models/glm-5-3-flash) | 41.9 | 27.5% | [0.075 / 0.25, promotional](https://openrouter.ai/z-ai/glm-5.3-flash) | **$2.40** |
| 4 | [DeepSeek V4 Flash 0731, max](https://artificialanalysis.ai/models/deepseek-v4-flash) | 34.5 | 40.4% | [0.04 / 0.10, via OpenInference](https://openrouter.ai/deepseek/deepseek-v4-flash-0731) | **$1.23** |

For comparison, [Astra low](https://artificialanalysis.ai/models/gpt-6-astra-low) scores 46.0 on the Intelligence Index and 59.5% on knowledge accuracy.

**Why this order:** Muse offers the strongest combination of general capability and price. DeepSeek V4.1 offers a promising balance of capability, knowledge coverage and cost. GLM has particularly attractive economics and strong general scores, but weaker knowledge coverage could matter on varied notes. DeepSeek 0731 is an inexpensive comparison that may be adequate despite lower general scores. These are hypotheses about transfer to our task.

### Cost assumptions

The table reuses the measured subject-plus-mask totals above, scaled from 248 to 1,000 notes:

- Input: **26.899234 million tokens**, including the current execution path's overhead.
- Output: **1.532319 million tokens**, including reasoning once.
- Cost: `26.899234 × input price + 1.532319 × output price`.

These scenarios charge **all input at the uncached rate**, exclude fees, and exclude node titles. They do not predict a future cache-hit rate. Different tokenizers, reasoning usage, subject counts, retries or request overhead can change actual costs substantially. A model benchmarked at maximum reasoning effort must not be assumed to use the same output volume as Astra low.

### Access and benchmark caveats

- **Muse Contributor:** AA benchmarked the standard model, not independently the Contributor endpoint. OpenRouter identifies Contributor as a tier of Muse Spark 1.3 but does not establish identical behavior in our configuration. Prompts and outputs may be used to improve Meta's products. Check the applicable output-use terms before generating extractor-training data at scale. [Route and terms description](https://openrouter.ai/meta/muse-spark-1.3-contributor).
- **GLM:** the $2.40 scenario uses DeepInfra's promotional, FP4 deployment. It should not be assumed identical to the benchmarked deployment. The listed first-party $0.15 / $0.50 route gives approximately **$4.80** under the same token assumptions. [Providers](https://openrouter.ai/z-ai/glm-5.3-flash).
- **DeepSeek:** prices vary by provider, and the V4.1 first-party rate can vary by time. The table uses the listed lower-priced routes. For the older candidate, use the exact OpenRouter ID `deepseek/deepseek-v4-flash-0731`; the unversioned `deepseek/deepseek-v4-flash` route refers to an older revision. [V4.1 providers](https://openrouter.ai/deepseek/deepseek-v4.1-flash), [0731 providers](https://openrouter.ai/deepseek/deepseek-v4-flash-0731).
- **Evidence:** the Intelligence Index measures general capability, not extraction accuracy. AA-Omniscience knowledge accuracy may help gauge interpretation of unfamiliar subjects, but does not measure faithfulness to the note. No IFBench score was found for the exact four benchmark variants above. IFBench itself tests instruction following, not our semantic annotation policy. Long-context scores and context-window size were not used to rank this shortlist. [AA methodology](https://artificialanalysis.ai/methodology/intelligence-benchmarking), [Omniscience](https://artificialanalysis.ai/evaluations/omniscience), [IFBench](https://artificialanalysis.ai/evaluations/ifbench).

### Other candidates retained

- **MiniMax M3:** 82.9% IFBench provides instruction-following evidence missing for the four candidates above. Its weaker knowledge results make it more interesting for masking an already supplied subject than for discovering subjects. Approximately **$9.91 per 1,000 notes** at $0.30 / $1.20. [AA](https://artificialanalysis.ai/models/minimax-m3), [OpenRouter](https://openrouter.ai/minimax/minimax-m3).
- **Qwen 3.8 Flash:** approximately **$4.76** at $0.15 / $0.47. A reasonable alternative family, but the AA result is for the related Flash-Next checkpoint rather than the exact hosted model. The official model card describes hosted Flash as based on Flash-Next, with additional production features. [Model relationship](https://huggingface.co/Qwen/Qwen3.8-Flash-Next), [OpenRouter](https://openrouter.ai/qwen/qwen3.8-flash).
- **Gemini 3.8 Flash:** strong knowledge results, but approximately **$25.92**, or **$12.96 through batch**, at the same token volumes. [AA](https://artificialanalysis.ai/models/gemini-3-8-flash), [OpenRouter](https://openrouter.ai/google/gemini-3.8-flash).

**Planned comparison, not yet run:** compare Muse Contributor, DeepSeek V4.1 Flash and GLM 5.3 Flash with a fresh subscription-backed Astra low baseline on the same inputs, initially keeping ASv6.23 and MPv3.5 unchanged for every model. The active English selection contains 676 unique notes from 555 authors (`frontier-model-comparison-v1/english-selection-v2/selection.json`). The [comparison adapter](frontier_runner/runner.mjs) calls the [general model runner](model-runner.md), which uses pi-ai for **both** Astra's subscription route and OpenRouter. It does not use normal OpenAI API billing, Codex CLI, or the full pi agent. A subscription compatibility call succeeded. The saved probe results (`frontier-model-comparison-v1/compatibility-probe-v1/results.json`) are not a comparison baseline. Final comparison settings and spending approval remain open.

This comparison requires readable English text. The full frozen 1,000-note sample was manually audited: 931 met that requirement, including 84 known prompt-development notes that are excluded from this comparison. Removing obvious repeated bodies left 814 possible inputs. The main agent then read 604 additional corpus candidates for missing forms and retained 231. The reviewed originals and decisions (`frontier-model-comparison-v1/english-selection-v2/reviewed-pool.json`) preserve the complete text, classifications, and exclusions. Additional rejected candidates include wrong-form search hits and repeated templates, not just language failures. All 1,604 stored texts and authors were checked against the source database with zero mismatches. The provenance record (`frontier-model-comparison-v1/english-selection-v2/provenance.json`) describes both supplemental sources and their limitations.

Selection takes 60 distinct notes from each of 16 overlapping forms, spreading each draw across authors before reusing authors. Their union contains 676 notes, each processed once; there is no extra general/random quota. Of these, 459 come from the original 1,000, and 217 fill coverage gaps from the same corpus. The actual coverage counts (`frontier-model-comparison-v1/english-selection-v2/coverage.json`) are: news 94; opinions 169; structured reports 64; personal updates 126; promotions 83; captions/fragments 68; resource previews 64; quotations 78; explanations 76; advice 62; social messages 71; questions/requests 60; humor 65; creative writing 62; other factual descriptions 60; and publishing/account information 67. Counts overlap. The sample includes 127 posts of at most 10 words after removing pointers for counting, and 60 exceeding 100 words. Saved original text is unchanged. Subject requests retain the frozen long-NIP19 removal, which affects 74 selected notes; mask requests receive the untouched original text.

This is deliberately balanced coverage screening, not a population-accuracy estimate. It does not guarantee 60 examples of every subtype or combination, and author/template diversity does not prove independence. The earlier 327-note selection and original 26-note input-review set remain unchanged, but neither is the active comparison sample. [The replay script](frontier-model-comparison-v1/english-selection-v2/select.py) verifies the frozen inputs and reconstructs every draw and saved artifact without model calls.

Only 12 selected notes (`frontier-model-comparison-v1/english-selection-v2/sampler.json`) are presented for spot-checking in the existing read-only viewer. From the repository root, run:

```bash
bash sse_multivector/frontier-model-comparison-v1/english-selection-v2/run-review.sh
```

The viewer shows full original text and selection reasons only. Opening it makes no model calls. Those reasons are not model instructions, and Astra's outputs will not be an answer key. No subject/mask-generation calls or prompt changes were made during this selection work.

Assess subject generation and mask generation separately, using the same fixed subjects across models for the mask comparison; they need not have the same winning model. Record the exact provider, model revision, reasoning setting, actual inputs, tokens and cost. The research justifies this comparison, not a claim that any candidate already matches Astra's annotation quality.

### Comparison runner

[The comparison launcher](run-frontier-comparison.sh) accepts `preview` or `run`, with one JSON config supplied on stdin or in a file. Each invocation handles one note or one fixed subject, independently. It loads ASv6.23/MPv3.5 by verified hash and preserves the subject object schema (`context`, then `subject`) and bare-array mask output. It does not choose subjects for the mask comparison, run a batch, repair outputs, or retry failures. It delegates execution to the [general runner](run-model.sh); arbitrary prompts belong there, not in this frozen experiment adapter. The general runner replaces the deleted `codex_exec.py` tool. The earlier token measurements in this document remain historical Codex-runner measurements, not measurements of the new pi-ai runner.

The dependency is pinned to pi-ai 0.85.1 in [package-lock.json](../../experiment-runner/experiment_runner/frontier_runner/package-lock.json). Install it once with Node 24's `npm ci --ignore-scripts --no-audit --no-fund` in the shared `experiment-runner/experiment_runner/frontier_runner` directory. The launcher uses Node 24+ if available, otherwise Nix's `nodejs_24`. DeepSeek V4.1 Flash is absent from that pi-ai catalog, so the runner explicitly supplies its exact model ID and metadata from OpenRouter's September 16 catalog; it does not substitute an older DeepSeek model.

`preview` invokes the actual pi-ai serializers with fabricated authentication and a transport that records the request without sending it. It shows the decoded HTTP body, redacted headers, model/settings, and hashes. Pi-ai's default subscription instruction, “You are a helpful assistant,” is explicitly cleared. Astra requests also omit pi-ai's `text.verbosity: low` and `reasoning.summary: auto` defaults, while retaining `reasoning.effort: low`. Neither route receives AGENTS.md, agent instructions, tools, previous calls, or coverage annotations. The preview cannot establish server acceptance or hidden service-side instructions. Subject JSON-schema enforcement is requested on both routes; unsupported parameters must fail rather than trigger a format fallback.

`run` additionally requires `--send`. Both providers use the local credential-service route documented in [the general runner](model-runner.md#execution-and-credentials); do not supply upstream keys or credential files. The [repository budget rules](../AGENTS.md) authorize user-requested OpenRouter work roughly estimated at $1 or less without another approval question or provider-side cap. Other paid work requires explicit spending approval, but not a provider-enforced cap; ledger accounting and the lifetime ceiling always apply. OpenRouter output-token caps are optional; pi-ai's subscription transport does not enforce such a cap. Timeouts are not monetary limits. OpenRouter reasoning settings are explicit, including a `provider-default` option; implementing this interface did not select the comparison settings.

Results retain the exact request, raw answer, provider-returned model/provider/usage metadata when supplied, pi-ai usage, and local JSON/source-integrity checks. Those checks are not semantic evaluation. Pi-ai's `input` excludes `cacheRead`/`cacheWrite`, whereas `output` already includes reasoning. Its cost calculation is a catalog estimate, not an invoice or subscription charge. No model calls or credential reads were made during implementation: tests use intercepted HTTP requests and simulated streams, including a run in a network-isolated namespace.

An offline preview of one selected note, with no credential access or model request:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
printf '%s\n' '{"provider":"openai-codex","model":"gpt-6-astra","reasoning":"low","stage":"subjects","note_id":"E0002"}' \
  | bash sse_multivector/run-frontier-comparison.sh preview
```

## Saved evidence

- [Frozen ASv6.23 package](subject-prompt-goal-v1/asv6.23/frozen.json) and final-validation verification (`subject-prompt-goal-v1/asv6.23-validation-v1/final/verification.json`).
- [Frozen MPv3.5 package](mask-prompt-goal-v1/frozen.json).
- [Real-note experiment record](real-note-fine-segmentation-v1/README.md). Raw usage is in each call's `run/results.jsonl`, under `subjects-001-010`, `subjects-011-100`, `masks-001-010` and `masks-011-100`.
- Music usage comes from `real-note-fine-segmentation-v1/music-generation-v1`, including its two mechanical mask retries. Extraction integrity (`real-note-fine-segmentation-v1/music-generation-v1/extraction-integrity.json`).
- Coverage-expansion usage comes from `real-note-fine-segmentation-v1/coverage-expansion-v1/subjects` and `masks`. [Experiment record](real-note-fine-segmentation-v1/coverage-expansion-v1/README.md).
- v21 comparison (`hdbv2-node-description-probe-v21/comparison.json`) and v21 additional groups (`hdbv2-node-description-probe-v21-additional-v1/comparison.json`), with raw usage under their `calls` directories. [Exact v21 prompt](hdbv2-node-description-probe-v21/prompt.txt).

For extraction, sum the successful calls' `usage.input_tokens` and `usage.output_tokens` separately by stage, then multiply each total by `1,000,000 / 248`. For titles, divide the 24-call totals by 24 and multiply by the assumed node count. This reproduces the unrounded total of approximately 29.90 billion tokens when assuming 610,000 nodes.
