# Subject-to-source mask test — Sol low

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

The mapping format did not reliably fix mask completeness and scope. It removed the extra state-backing detail from all three insurance masks, but all three understanding-life masks omitted “life.” The CEO-incident masks still selected extra background. No prompt or model default is changed.

This is a completed development test, not a prompt freeze or an unseen holdout.

## What changed

The same 12 fixed ASv6.8 subjects from four notes were tested three times each. All 36 new calls used `gpt-5.6-sol`, low reasoning, Codex CLI 0.153.0, and the existing isolated CLI wrapper.

The original output was a list of source fragments. The revised output pairs excerpts of the fixed subject with source fragments that express them. All returned source fragments still form one mask. The subject excerpts are not new subjects, and the mapping is not an automatic approval.

Only the approved output requirement changed. The remaining prompt, complete notes, fixed subjects, model, reasoning effort, wrapper, and isolation settings stayed identical. There were no worked examples. The comparison uses the 36 saved **fragment-only Sol-low** calls from [the earlier run](../mask-prompt-astra-vs-sol-low-v1/README.md), not the worked-example, Sol-medium, or Astra runs.

## What the masks show

These are my assessments against the fixed subjects and existing decisions. Each count is three trials of one subject, not three different notes. Click an ID for the full note, every mask, and every returned mapping.

| Observation | Original, fragment-only | Revised, mapping |
| --- | --- | --- |
| M05 (`./masks.md#m05`): “life” missing from the understanding-life mask | 1/3 | 3/3 |
| M07 (`./masks.md#m07`): extra state-backing description in the insurance mask | 2/3 | 0/3 |
| M09 (`./masks.md#m09`): “Bitcoin” missing | 1/3 | 0/3 |
| M09 (`./masks.md#m09`): actual settlement-shift activity added to the value-under-restrictions subject | 1/3 | 1/3 |
| M11 (`./masks.md#m11`): CEO incident left unidentified | 2/3 | 0/3 |
| M11 (`./masks.md#m11`): whole quoted setup selected along with the incident | 1/3 | 3/3 |

M05 shows why a populated mapping is not proof of coverage. Its subject excerpt names “life,” but its source fragments select only `Meditation` and `the very understanding of it`. “Life” remains outside the mask. The two original trials that did select life returned their fragments out of source order; neither prompt produced a fully satisfactory M05 output in these runs.

M11 shows the unresolved scope problem. Selecting the whole quote identifies the CEO incident, but also selects employee calls, anonymous chat, question timing, and the invitation to ask something hard. I judge that setup outside the thesis-change subject. This is my assessment, not a new user rejection.

M12 (`./masks.md#m12`) remains variable. Revised trial 1 includes the full `CEO has all employee calls` assertion; trial 2 excludes it and matches the previously accepted scope. Trial 3 selects only `employee calls` alongside the gossip and rhetoric. The word employee supplies workplace context, while calls adds the medium of the incident. I leave that third trial borderline rather than count it as a definite failure.

M01, M04, M06, M08, and M10 retain the previously accepted meaning with both prompts. M02 and M03 remain unresolved because earlier rejections had no recorded reason. No overall accuracy score is assigned.

## Output checks

All 36 revised responses had the expected object-array shape, exact source strings, and valid source order within each array. Two M03 responses rewrote one `subject_text` rather than copying an exact excerpt, leaving 34/36 compliant with those mechanical checks. This does not mean 34 masks had correct meaning.

The original had 35 JSON arrays and one response incorrectly claiming the post was missing. Two original arrays put fragments out of source order, leaving 33/36 compliant with their mechanical checks.

The formats impose different order constraints: the original has one source-ordered array; the revised has source order within each entry, not across entries. This difference is intentional, so the order counts alone do not demonstrate better semantic selection.

Eleven revised outputs permit more than one combined mask placement, compared with two original outputs. Repeated names and short fragments such as `he` cause this. The mapping identifies strings, not positions. Every possible placement is shown (`./masks.md`); none was silently chosen or encoded with SSE. Per-entry ambiguity that leaves the combined mask unchanged is recorded separately in the checks (`./mechanical-checks.json`).

## What this establishes

This particular output change made one recurring scope error disappear, but did not consistently make the selected source text complete or correctly scoped. The subject side can state the right meaning while the source side still omits it. More output structure has not solved that problem on these notes.

The result does not establish that explicit mappings cannot help. These are four reused development notes, with three calls per subject. The original calls were collected earlier, not interleaved or paired by random seed. No broader reliability claim or causal explanation for each individual change is warranted.

## Records and resources

- [Approved prompt snapshot](./mask-prompt.md), from commit `cc949ec195a9f6a08992b442210f1391c3262aff`.
- [Plan](./plan.json) and unchanged notes and subjects (`./selection.json`).
- Full notes, inline masks, and mappings (`./masks.md`); individual assistant assessments (`./assistant-review.json`).
- Raw outputs: trial 1 (`./trial-1/run/output.json`), trial 2 (`./trial-2/run/output.json`), trial 3 (`./trial-3/run/output.json`). Each run also preserves rendered prompts, process arguments, thread IDs, events, usage, and hashes.
- Mechanical checks (`./mechanical-checks.json`) and integrity/isolation verification (`./verification.json`).

All 36 new thread IDs and workdirs were distinct and absent from 241 prior records checked. Wrapper records show fresh processes and empty workdirs, with conversation history, repository instructions, user configuration, tools, and web access excluded or disabled. No tool or error events were returned. Prompt/output hashes matched all 72 comparison records. These checks establish local harness isolation, not access to undisclosed service-level context.

Trials ran sequentially, each with a 2 GiB local memory cap, zero swap allowance, and a 900-second limit. Recorded local peaks for trials 1 and 2 were 16.8 and 16.7 MiB, with zero service swap. Trial 3 completed all 12 calls; its transient unit's peak counter was no longer available when checked. No experiment service remained active. Host memory-pressure averages were zero at the final check.

| Reported usage | Original, already saved | Revised, new calls |
| --- | ---: | ---: |
| Input tokens | 78,216 | 82,644 |
| Cached input tokens, included above | 4,096 | 4,224 |
| Output tokens | 2,261 | 6,291 |
| Reasoning output tokens, included above | 1,143 | 2,523 |
| Median call time | 5.407 seconds | 6.907 seconds |

Timing is observational, not a latency benchmark. Calls used the existing Codex subscription; no paid API, rented compute, or account switch was used. All 39 protected files were unchanged, including prompts, registries, the budget ledger, baseline results, and user review decisions. There were no retries, output repairs, SSE runs, or production-code changes.

Selected inputs, final answers, recorded reviews and parameters: `historical-studies/mask-prompt-subject-source-sol-low-v1`. See the [publication catalog](../../docs/experiments/publications.csv) and [file checksums](../../docs/experiments/publication-files.csv).
