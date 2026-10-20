# Sol low versus Astra low

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

**Astra improved several recurring mask errors, but it did not solve the task. It was also less consistent on the gossip/market-thesis example.**

Both models ran on Codex CLI **0.153.0**, with the unchanged mask prompt, the same 12 fixed ASv6.8 subjects and four complete notes, and low reasoning. Each subject ran three times per model: **72 fresh, isolated calls**. The new Sol runs are the comparator, not the older runs on CLI 0.150.1.

## What changed

Each count is out of three. These describe particular errors or selections, not an overall accuracy score.

| Item | Sol low | Astra low |
| --- | --- | --- |
| M05: meditation as understanding life | Life missing once; selected twice, but both arrays have the wrong source order | Life selected in all three, with correct source order |
| M07: cryptocurrency insurance settlements | Extra state-backing meaning in 2/3 | No extra state backing in 3/3 |
| M09: Bitcoin's value under restrictions | Matches the approved semantic scope in 2/3; the other omits Bitcoin and adds settlement activity | Matches that semantic scope in 3/3 |
| M11: CEO incident changing a thesis | Extra call setup once; incident unidentified twice | Incident identified without setup in 2/3; extra setup once |
| M12: gossip framed as an investment thesis | Extra call setup in 1/3 | Extra call setup in 2/3 |

The improvement is concrete: Astra selected the needed identifying words while excluding unrelated clauses more consistently in M05, M07, and M09. M11 improved but still failed once. **M12 prevents calling this a uniform improvement.**

Both models kept the expected meaning in M01 (crew assignment), M04 (withdrawal from life), M06 (Krishnamurti's attributed view), M08 (Bitcoin's issuer/blacklist mechanisms), and M10 (questions at the end of calls). Fragment count and punctuation differences are not counted as errors.

For M02, Astra selected only the mission name and Zhang Lu's command role in all three runs. Two Sol outputs retained the participation wording whose scope was already unsettled; the third did not return a mask. M03 retains the earlier unresolved scope question under both models. I have not silently turned those earlier rejections into approvals.

## One invalid response

Sol, trial 3, M02 returned:

> Cannot select a mask because the social-media post text was not supplied.

That call's saved prompt contains the complete astronaut post and the fixed subject. It is identical to the M02 input used in the other five calls. The runner hashes the same prompt string it passes to the fresh process. This verifies the local input; it cannot establish undisclosed service internals.

That response remains in the data. It was not retried, repaired, or replaced.

## Remaining distinction: meaning versus exact source position

Five M09 outputs select the bare word **Bitcoin**, which occurs twice in the note: all three Astra outputs and two Sol outputs. Their selected words match the approved semantic scope, but the model does not specify which occurrence to use.

That ambiguity remains unresolved. It is not silently repaired or counted as a new problem introduced by Astra. Both possible highlights appear in all masks (`./masks.md`).

All 36 Astra responses are JSON arrays of exact source fragments in source order. Sol returned 35 such arrays; two are out of source order, leaving 33 order-valid outputs. These are mechanical checks, not semantic accuracy.

## Time and tokens

| Measurement, 36 calls per model | Sol low | Astra low |
| --- | ---: | ---: |
| Reported input tokens | 78,216 | 92,724 |
| Reported cached input tokens | 4,096 | 36,224 |
| Output tokens, including reasoning | 2,261 | 3,378 |
| Reasoning output tokens | 1,143 | 2,156 |
| Sum of batch service runtimes | 238.751 seconds | 324.763 seconds |
| Median individual call time | 5.41 seconds | 8.39 seconds |

Astra used about **49% more output tokens** and **36% more batch service time** here. These are observed totals, not general pricing or latency estimates. The same submitted text does not imply identical model-reported token counts, and the low setting does not impose equal inference compute across models. Cache usage also differed; no earlier responses were inserted into any prompt.

Local batch peaks ranged from **16.7 to 17.1 MiB**, with **zero swap**, under sequential 2 GiB/900-second limits. Only the existing subscription was used; no paid API or rented compute.

## What this establishes

On these four development notes, Astra is a promising alternative for following the current mask instructions. It handled several recurring problems more consistently, without any prompt additions.

It is **not** evidence that the prompt is ready to freeze, that Astra is uniformly better, or that these results generalize to unseen notes. Every new semantic judgment above is my analysis using the earlier review decisions, not a new user approval.

## Evidence and controls

- `plan.json`: the approved question, unchanged inputs, and declared execution order.
- `selection.json`: the fixed subjects and complete original notes.
- `astra-trial-1/` through `astra-trial-3/`, and `sol-trial-1/` through `sol-trial-3/`: exact configurations, rendered prompts, manifests, minimal instructions, and raw outputs.
- All masks with complete notes and analysis (`./masks.md`): every output, grouping only identical fragment arrays.
- `assistant-review.json`: all 72 assistant assessments and their reasons.
- `mechanical-checks.json`: exact-source, source-order, and occurrence checks.
- `verification.json`: configuration/argv checks, prompt/output hashes, isolation, resources, and token totals.

All 72 calls have distinct new threads and empty workdirs, with no overlap against 133 earlier mask-generation records checked. Prompt strings, low reasoning, the CLI, wrapper, output contract, and isolation match across the two arms; only the model and fresh run-specific paths differ. Tools and web were disabled. There were no retries, manual generated-output edits, or new user decisions.

The earlier CLI 0.150.1 rejection remains preserved in `../mask-prompt-astra-low-v1/` and is excluded from this comparison. Historical results, frozen prompts/registries, user reviews, production code, and user notes documents are unchanged. No SSE encoding, subject regeneration, hierarchy work, or default-model change occurred.

The runtime-only migration followed [OpenAI's model-parameter guidance](https://developers.openai.com/api/docs/guides/latest-model#gpt-6-astra-update-api-and-model-parameters); it supplied compatibility checks, not the semantic verdict.

See [conversion gaps](../../docs/experiments/publication-gaps.csv) for `collection:tracked-mask-prompt-astra-vs-sol-low-v1`.
