# Mask generation: low versus medium reasoning

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

**Medium improved some identifying-word selections in this small comparison. It did not solve mask scope or source order.**

I ran 36 fresh calls: the same 12 fixed ASv6.8 subjects three times, using the unchanged current mask prompt and `gpt-5.6-sol`. The only changed generation setting was reasoning effort, from low to medium. The comparison uses the three existing low-effort runs.

## What changed

Each count is out of three runs. A recovered word is not automatically a completely correct mask.

| Item | Low | Medium |
| --- | --- | --- |
| M05: meditation as understanding life | Life absent in 3/3 | Life present in 2/3, but both arrays are out of source order; absent in the third |
| M09: Bitcoin's value under restrictions | Bitcoin present in 1/3 | Bitcoin present in 3/3, but all three add settlement activity outside the subject |
| M11: CEO incident changing the commentator's thesis | Two omit the incident; one includes extra call setup | Two identify the incident without the call setup; the third includes the extra setup |
| M07: cryptocurrency maritime-insurance settlements | Extra state backing in 2/3 | Extra state backing in 3/3 |
| M12: CEO gossip expressed as investment analysis | Extra call setup in 1/3 | Extra call setup in 1/3 |
| M10: questions at the end of all-employee calls | One invalid response | All three return the accepted exact-source selection |

M01, M04, M06, and M08 returned the same fragment arrays at both settings. Two medium M02 outputs remove the participation wording while preserving the mission and command role. The other M02 output and all M03 outputs retain older unresolved scope questions; they have not acquired automatic human approvals.

The answer to the test question is therefore **partial improvement**: fewer missing identifying words in these notes, without a corresponding reliable reduction in additional meanings. M09 recovered Bitcoin but still fails scope in all three medium runs. The M05/M07/M11 errors also remain; the prompt stays unfrozen.

This is not a population success rate or proof of the cause of each difference. The notes are already-used development examples, and the low runs were collected before the medium runs rather than interleaved randomly. No overall accuracy score is assigned.

## M09 review: rejected

M09's fixed subject is:

> Bitcoin’s value to restricted actors lies in its continued usability under financial restrictions rather than its ordinary monetary superiority.

The previously approved low mask selected **restricted actors**. All medium masks additionally select **are shifting toward it for settlement**.

The user rejected **trial 3** in the review tool and confirmed “yea reject” in chat. The added words describe actors actually moving their settlements to Bitcoin, beyond the supplied subject about Bitcoin's value under restrictions. Restoring Bitcoin does not make the complete mask correct.

Trials 1–2 contain the same added activity. Applying this ruling to them is my judgment, not two additional independent user reviews. The original review decision and its provenance are preserved in `human-review.json`.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./target/release/sse-mask-review review-masks \
  sse_multivector/mask-prompt-medium-reasoning-v1/review-needed.json \
  target/mask-prompt-medium-reasoning-v1-review-session.json
```

Bitcoin appears twice in the source. The model did not specify which occurrence it meant. The review highlights the first occurrence for display only, following the earlier low review convention. The scope rejection does not resolve that occurrence ambiguity. Both possible highlights are recorded in `masks.md` and `review-preparation.json`.

## Time and tokens

These totals include every response, including the invalid low-effort response.

| Measurement, 36 calls per setting | Low | Medium |
| --- | ---: | ---: |
| Input tokens | 82,572 | 82,572 |
| Output tokens, including reasoning | 2,773 | 3,980 |
| Reasoning output tokens | 1,636 | 2,785 |
| Sum of service runtimes | 215.660 seconds | 232.753 seconds |
| Median call elapsed time | 5.05 seconds | 5.13 seconds |

Medium used about **44% more output tokens** and **8% more total service time** in this comparison. These are observed totals, not a general latency or pricing estimate. Most calls still reported zero reasoning output tokens: 25/36 at medium and 31/36 at low. The setting does not establish that each individual response received more measured reasoning.

The three new batches peaked at 16.8M, 16.7M, and 16.7M of service memory, with zero swap. Calls remained sequential under the existing 2 GiB and 900-second per-batch limits. Only the existing Codex subscription was used; no paid API or rented compute.

## Validation and evidence

- All 36 new calls used distinct fresh threads and empty workdirs, none shared with the 96 earlier calls checked.
- The three configurations differ from the baseline only in `reasoning_effort`. Exact prompt strings, original notes, subjects, model, wrapper, binary, minimal instructions, and isolation remain equal.
- Tools and web were disabled. No earlier answers, examples, or review comments were added to the calls.
- All 36 responses are JSON arrays of exact source strings. Two M05 arrays violate source order. Three M09 outputs have two possible source placements. These checks are separate from semantic correctness.
- No retries, repairs, manual output edits, or new human approvals.
- One later user rejection is recorded in `human-review.json`. The original TUI session is unchanged; no new model calls were made to record the decision.
- Rendered-prompt and raw-output hashes were verified across all 72 low/medium records.
- The production review tool opened the single M09 review with its full note and inline mask, then exited without decisions or comments in a separate smoke session.
- Original prompts, low results, user reviews, frozen registries, production code, and the user's notes documents remain unchanged. No SSE encoding or hierarchy work.

Files:

- All masks with complete notes and analysis (`./masks.md`)
- `assistant-review.json`: every low and medium judgment, including the unresolved ones.
- `mechanical-checks.json`: source matching, order, and occurrence checks.
- `verification.json`: configuration comparison, isolation, hashes, resources, and review smoke check.
- `review-needed.json` and `review-preparation.json`: the preserved input and preparation record for the now-completed M09 review.
- `human-review.json`: the trial-3 rejection, chat confirmation, and explicitly separate assistant application to trials 1–2.
- `plan.json` and `selection.json`: the authorized question and unchanged inputs.
- `trial-1/run/`, `trial-2/run/`, and `trial-3/run/`: exact rendered prompts and raw outputs.

The [official GPT-5.6 reasoning guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6#reasoning-effort) informed the single-setting comparison. It does not establish that medium is a fix; the observations above are the evidence for this task.

Selected inputs, final answers, recorded reviews and parameters: `historical-studies/mask-prompt-medium-reasoning-v1`. See the [publication catalog](../../docs/experiments/publications.csv) and [dataset manifest](../../docs/experiments/downloads.md#dataset-manifest).
