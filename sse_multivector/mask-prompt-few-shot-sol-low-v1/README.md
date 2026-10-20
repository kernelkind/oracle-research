# Worked-example mask test — Sol low

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

The six examples did not produce a reliable improvement on these four notes. The insurance mask improved in one more trial, while the Bitcoin and gossip masks became worse. No prompt or model default is being changed.

This is a completed development test, not a prompt freeze or an unseen holdout.

## What changed

The same 12 fixed ASv6.8 subjects were tested three times each. All 36 new calls used `gpt-5.6-sol`, low reasoning, and Codex CLI 0.153.0. They are compared against the saved 36 Sol-low outputs from [the earlier run](../mask-prompt-astra-vs-sol-low-v1/README.md), using the same CLI and wrapper—not Sol medium or Astra.

Only the approved six-example block was added to the prompt. The original instructions, subjects, and complete notes remained identical. The example posts are synthetic teaching inputs, not additional test notes.

## What the masks show

These are my assessments against the fixed subjects and existing review decisions. Each number counts three trials, not three different notes. Click an ID to see every original note and mask.

| Item and observation | Original prompt | Revised prompt |
| --- | --- | --- |
| M05 (`./masks.md#m05`): “life” missing from the understanding-life mask | 1/3 | 2/3 |
| M07 (`./masks.md#m07`): extra state-backing meaning in the insurance mask | 2/3 | 1/3 |
| M09 (`./masks.md#m09`): mask matches the approved Bitcoin value-under-restrictions scope | 2/3 | 0/3 |
| M11 (`./masks.md#m11`): CEO incident identified without the extra call setup | 0/3 | 0/3 |
| M12 (`./masks.md#m12`): extra call-setup meaning in the gossip/framing mask | 1/3 | 2/3 |

M09 now omits “restricted actors” in two trials. The third omits “Bitcoin” and adds the actors' actual shift toward settlement. The earlier prompt produced the previously approved semantic scope twice, although “Bitcoin” could refer to either of two source occurrences.

M11 illustrates the remaining tradeoff: the earlier prompt left the incident unidentified twice and selected the entire quote once. The revised prompt selected the entire quote all three times. That identifies the incident but also includes the all-employee calls, anonymous chat, question timing, and invitation to ask a hard question. I judge that setup outside this fixed subject.

M01, M04, M06, M08, and M10 retained the previously accepted meaning in all three trials with either prompt. M02 and M03 remain unresolved scope questions because earlier rejections had no recorded explanation. No overall accuracy score is assigned.

## Output checks

All 36 revised outputs were JSON arrays of exact source strings. The original had 35 such arrays and one response incorrectly claiming the post was missing.

Source order still failed:

- Revised M05 trial 1 puts “life” after “understanding,” although the note has them in the opposite order.
- Revised M09 trials 1 and 2 put “remains usable…” before “Not because…,” reversing their order in the note.
- Original M05 trials 2 and 3 also put “life” last.

Thus 33/36 outputs from each prompt met the JSON, exact-string, and source-order checks. This does not mean 33 masks had correct meaning. Neither prompt produced an M05 response with both complete meaning and valid source order.

Two original M09 masks permit two source occurrences of “Bitcoin.” The two out-of-order revised M09 masks also permit two placements if array order is disregarded for display. Both are shown in `./masks.md`; no occurrence is silently chosen. Revised M02 trial 2 is different: source order uniquely selects the first “Zhang Lu.”

## What this establishes

The specific examples did not consistently teach the required boundary between supplying context and adding another meaning. The observed changes do not justify replacing the original prompt.

This does not establish that worked examples cannot help. There are only four previously used notes and three trials per subject. The original outputs were collected earlier, not interleaved with these calls. No stronger model, additional examples, or further prompt revisions were tested.

## Reproduction and resources

- [Prompt snapshot](./mask-prompt.md), approved in commit `128985ac1a2d44d903fa51e345a4621b48864d57`.
- [Plan](./plan.json) and unchanged notes/subjects (`./selection.json`).
- New raw outputs: trial 1 (`./trial-1/run/output.json`), trial 2 (`./trial-2/run/output.json`), trial 3 (`./trial-3/run/output.json`). Each run also preserves its rendered inputs, process arguments, thread ID, raw event log, usage, and response hashes.
- Every mask inline (`./masks.md`), individual assistant assessments (`./assistant-review.json`), mechanical checks (`./mechanical-checks.json`), verification (`./verification.json`).

Every new call used a separate process, thread, and empty workdir. All 36 thread/workdir IDs were distinct and absent from 205 earlier records checked. Local manifests show prior conversation, repository instructions, user configuration, tools, and web access disabled or excluded; raw events contain no tool calls or errors. Prompt/output hashes match all 72 saved records. These checks establish local harness isolation, not visibility into undisclosed service internals.

The three new trials ran sequentially with a 2 GiB local memory cap, zero swap allowance, and a 900-second limit each. Their combined service runtime was 230.185 seconds; the largest recorded local service memory peak was 17 MiB, with no service swap. All exited successfully and no trial service remains running. Host I/O pressure rose during the final trial; its cause was not established.

Reported usage:

| | Original, already saved | Revised, new calls |
| --- | ---: | ---: |
| Input tokens | 78,216 | 93,084 |
| Cached input tokens, included above | 4,096 | 4,736 |
| Output tokens | 2,261 | 1,549 |
| Reasoning output tokens, included above | 1,143 | 287 |
| Median call time | 5.407 seconds | 5.727 seconds |

Timing is observational, not a controlled latency benchmark. The calls used the existing Codex subscription; no paid API, rented resources, or account switch was used. Prompts, registries, budget ledger, saved baseline results, and user review decisions were not modified. There were no retries or output repairs.

Selected inputs, final answers, recorded reviews and parameters: `historical-studies/mask-prompt-few-shot-sol-low-v1`. See the [publication catalog](../../docs/experiments/publications.csv) and [file checksums](../../docs/experiments/publication-files.csv).
