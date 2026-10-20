# Repeated comparison of the two mask prompts

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

The latest clarification did not produce a repeatable improvement. Both prompts still alternate between omitting identifying text and selecting additional meaning.

I ran the previous and current prompts two more times each on the same 12 fixed ASv6.8 subjects and four notes: **48 fresh calls**. Including the original runs, each subject has three outputs per prompt.

“Previous” means `../mask-prompt-probe-v3/`; “current” means `../mask-prompt-probe-v4/`. These are experiment directory names, not new frozen MP registry versions. Neither prompt was edited or frozen.

## What repeated

Every number below is out of three runs. These describe specific observations, not an overall accuracy score.

| Fixed subject | Previous prompt | Current prompt |
| --- | --- | --- |
| M05: meditation as understanding life | Selected meditation, understanding, and life in 3/3; wrong array order in all three | Omitted life in 3/3; one output was only “understanding” |
| M07: cryptocurrency maritime-insurance settlements | Included extra state-backing meaning in 2/3 | Included extra state-backing meaning in 2/3 |
| M09: Bitcoin's value under restrictions | Omitted Bitcoin in 2/3; the other selected the full issuer/blacklist/seizure statement | Correct semantic scope in the first run, then omitted Bitcoin in both repeats |
| M11: CEO incident changing the commentator's thesis | One omitted the incident; one focused selection; one included the full call setup | Two omitted the incident; one included the full call setup |
| M12: CEO gossip expressed as investment analysis | Extra call setup in 1/3 | Extra call setup in 1/3 |
| M10: questions at the end of all-employee calls | Two correct masks; one invalid response | Two correct masks; one invalid response |

M07's clean mask appeared under **both** prompts in trial 3. M12's improvement also appeared under the previous prompt in later runs. Those successes are not evidence that the added sentence reliably caused the improvement.

M01, M04, M06, and M08 returned the same fragment arrays throughout. M02 and M03 retain earlier unresolved scope questions; changing fragment count or dropping “and” does not establish that a rejected selection was fixed. I have not silently marked them approved or calculated an overall score.

## Two invalid responses

Both came from M10 in trial 2:

- Previous: “No text can be selected because the supplied post is empty.”
- Current: “CEO” … “ask me anything” … “at the end of all hands calls”

The first claim is false. The second response is not a JSON array, and its last two phrases are not exact source substrings. Both rendered prompts contain the full original CEO post and exactly match their respective original inputs. The runner hashes that prompt and passes the same variable to the fresh process. This verifies the local input, not undisclosed service internals.

These responses remain in the data, without retries or repairs. The runner's process-level “succeeded” status means it received nonempty output; it does not certify a valid mask.

## Interpretation

The repeated failures are sufficiently clear to reject the claim that the current wording has solved reference selection. The data do **not** establish that the extra sentence caused each difference or that one prompt has a better population success rate.

The recurring problem is scope: the model sometimes understands a reference from the whole note without highlighting what it refers to, and sometimes selects a whole supporting passage when only part belongs to the supplied subject.

No new user review is necessary to establish that conclusion. New judgments are mine; original user decisions are preserved separately. The unresolved M02/M03 scope questions remain open. No subject generation, SSE encoding, segmentation, hierarchy work, or prompt editing was done.

## Evidence

- All masks with full original notes inline (`./masks.md`): all six outputs per subject, grouping only identical fragment arrays.
- `selection.json`: unchanged subjects and complete original notes.
- `review-evidence.json`: snapshots of the two existing user reviews; no fabricated comments or new approvals.
- `assistant-review.json`: independent judgment for each output, including unresolved scope.
- `mechanical-checks.json`: exact substring, source-order, and occurrence checks.
- `verification.json`: settings, isolation, resources, preserved-file hashes, and raw-input checks.
- `v3-trial-2/run/`, `v4-trial-2/run/`, `v4-trial-3/run/`, `v3-trial-3/run/`: exact prompts, raw responses, and execution records. This is the execution order.

## Controls and resources

Model `gpt-5.6-sol`, reasoning `low`; the existing subscription-authenticated CLI runner and pinned binary were unchanged. Each new configuration is byte-identical to its corresponding original configuration; only its containing directory differs.

All 48 calls had distinct fresh threads and empty working directories, none shared with the 48 earlier v1–v4 calls checked. Prompts and execution arguments matched their baselines after accounting for fresh file paths. Tools and web were disabled. No previous answers or review comments were added. There were no retries or reused result records.

Of the 48 new responses, 46 were JSON string arrays of exact source fragments. Two of those had the already-known M05 source-order problem; 44 had a unique source-order-compatible placement. These are mechanical counts, not semantic accuracy. The original current-prompt M09 response still has two possible locations for “Bitcoin”; its first-trial semantic approval did not resolve that position ambiguity.

The new calls used **109,544 input tokens and 4,220 output tokens**, including 2,622 reasoning output tokens. Service runtimes summed to 305.915 seconds. Calls were sequential under a 2 GiB memory cap, zero swap, and 900-second batch limit. Highest reported service memory peak was **17.3M**, with **0B swap**. Only the existing Codex subscription was used; no paid API or rented compute.

The runner, both original prompts/results/reviews, and frozen subject/mask registries retained their pre-run hashes. Production code and the user's notes documents were not edited.

The controlled setup follows the [GPT-5.6 guidance on preserving other variables during comparison](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6#prompt-migration-workflow). No new prompt-engineering claim is inferred from these three trials.

Selected inputs, final answers, recorded reviews and parameters: `historical-studies/mask-prompt-repeatability-v1`. See the [publication catalog](../../docs/experiments/publications.csv) and [file checksums](../../docs/experiments/publication-files.csv).
