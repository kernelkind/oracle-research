# Mask generation: six additional notes

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

Astra low repeated its earlier advantage on three of these six notes. This supports continuing with it, but does not establish a final model choice.

| Fixed subject | Sol low | Astra low |
| --- | --- | --- |
| T02: Benefits of tokenization | Omits what the benefits concern, 3/3 | Includes tokenization, 3/3 |
| T04: The Kremlin's statement | Adds Medinsky's two job titles, 3/3 | Excludes both job titles, 3/3 |
| T08: Investigating cartoon complaints | Omits the cartoon title, 3/3 | Includes the cartoon title, 3/3 |

One Astra T04 mask also names the spokesman, Dmitry Peskov. Whether that is unnecessary extra detail remains a scope judgment for the user. It is not silently counted as correct.

Both models handled the other supplied subjects without an issue I could identify, including reference resolution in the Sora and giraffe notes. These are assistant judgments, not new user approvals.

Every mask with its full original note and analysis (`./masks.md`)

## What changed

Only the requested model changed between the two sets of mask calls: `gpt-5.6-sol` versus `gpt-6-astra`, both at `low`. Each call received one complete note and one fixed subject and returned one mask. No checker or second mask-generation call was added.

The [original fragment-only mask prompt](./mask-prompt.md) is unchanged from `mask-prompt-probe-v4/mask-prompt.md` (SHA-256 `564c860a3be5f8eb6e90c404184ef467f24004276dbb535f637ba0a8ded7ff9e`). Inputs did not contain earlier answers, sibling subjects, expected masks, review criteria or user decisions.

There were six notes and two subjects per note, with three planned calls per subject and model. Four notes reused existing ASv6.8 subjects. The other two received one frozen-ASv6.8 setup call each; selected subjects were then fixed before any masks were generated. No generated subject or mask was edited.

These notes were new to the earlier four-note mask comparison, not globally unseen: they came from subject-prompt development data. The six notes were selected for different extraction challenges, not sampled to estimate corpus-wide accuracy. The twelve chosen subjects do not evaluate every ASv6.8 output in those notes.

OpenAI Docs informed the controlled comparison: the prompt and inputs stayed fixed while the model changed. No new prompt wording was introduced. [Official GPT-5.6 guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6).

## Execution

72 mask calls were attempted. Astra returned 36 masks; Sol returned 35 masks and one service-capacity error.

Sol trial 3 stopped on its first subject, T05: “Selected model is at capacity. Please try a different model.” That call was not retried. Astra trial 3 then ran, followed by the eleven Sol calls that had not yet been attempted. The failed batch's original config, manifest and error remain intact; the continuation retains the remaining prompts unchanged. Recorded deviation (`./execution-deviation.json`).

All 71 masks are valid arrays of exact source substrings in source order. This mechanical check does not imply semantic correctness.

Fifteen returned arrays have multiple possible placements because a selected fragment appears more than once in its note. The report shows all source-order-valid placements instead of silently choosing an occurrence. This comparison did not encode them with SSE or resolve which occurrence should be used later.

## Isolation and resources

All 74 calls, including the two subject-setup calls, have distinct CLI threads and sterile working directories, with no overlap against 295 earlier mask-call records. Each used a fresh process. Recorded CLI settings disable tools, web search, inherited rules, user configuration and injected workspace/agent context. The same minimal model instruction was used: “Follow the user's instructions.”

These checks cover the wrapper and recorded events; they cannot inspect undisclosed service-level instructions. Reported prefix-cache usage is not conversation-history reuse.

The pinned CLI was 0.153.0. Calls were sequential, with a 2 GiB local memory cap, zero permitted swap and a 900-second per-batch limit. Reported local service peaks ranged from 16.3 to 17.0 MiB; every batch used zero swap. Existing subscription only, with no new paid API or rental commitment.

| Calls | Returned | Reported input tokens | Reported output tokens |
| --- | ---: | ---: | ---: |
| Sol low: 36 attempted | 35 | 74,348 | 648 |
| Astra low: 36 attempted | 36 | 90,906 | 1,715 |
| Subject setup: 2 attempted | 2 | 4,135 | 714 |

The failed Sol call reported no usage; its usage is unknown, not zero. Cached input is included in input counts. Reasoning output is included in output counts. Per-call tokens and elapsed times are in `./verification.json`; model tokenization and compute can differ despite the same `low` setting.

## Review in the existing TUI

This eight-screen sample shows the three consequential differences. `S1` means Sol trial 1; `A1` and `A3` mean Astra trials 1 and 3. T02's Astra output appears twice because its identical fragment strings allow two placements, not because the model ran twice.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./target/release/sse-mask-review review-masks \
  sse_multivector/mask-prompt-astra-vs-sol-transfer-v1/review-sample.json \
  target/mask-prompt-astra-vs-sol-transfer-v1-review-session.json
```

The command uses the existing binary and needs no Cargo build. You can stop at any point; no review is pre-approved. The full output set remains in `./masks.md`.

## Evidence files

- `./selection.json`: full notes, fixed subjects and their source outputs.
- `./scope-before-generation.json`: assistant scope notes frozen before mask generation and never sent to the models.
- `./assistant-review.json`: all new judgments and the explicit post-run T04 scope clarification.
- `./mechanical-checks.json`: every fragment, exact source occurrences and possible placements.
- `./verification.json`: hashes, actual call settings, freshness, token usage and service completion records.
- `./review-preparation.json`: exact provenance of each TUI screen.
- Each run directory retains its config, manifest and complete `results.jsonl`, including raw output, CLI events and errors. Successful batches also retain `output.json`.
- `./subject-setup/run/output.json`: all newly generated ASv6.8 subjects, including ones not selected for this comparison.

Fifty-seven protected files were unchanged, including existing prompts, inputs and review histories. No production code, prompt registry, model default, user decision, SSE artifact or segment was changed. CREC-125 remains awaiting user review.

Selected inputs, final answers, recorded reviews and parameters: `historical-studies/mask-prompt-astra-vs-sol-transfer-v1`. See the [publication catalog](../../docs/experiments/publications.csv) and [file checksums](../../docs/experiments/publication-files.csv).
