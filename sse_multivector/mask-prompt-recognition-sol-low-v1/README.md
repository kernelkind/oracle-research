# Mask recognition — Sol low

Sol low recognized some added meaning, but did not reliably recognize the mask errors we tested.

| Fixed mask problem | Trial 1 | Trial 2 | Trial 3 |
| --- | --- | --- | --- |
| M05-2: “it” is highlighted, but “life” is not | Missed | Missed | Missed |
| M07-2: state backing is added to the insurance subject | Detected | Detected | Detected |
| M09-2: actual settlement activity is added to Bitcoin’s value under restrictions | Missed | Detected | Detected |

The three acceptable masks produced **no false alarms in nine calls**. Two of those masks were previously approved by you; the clean insurance mask was checked by me. There were no invented reasons among the reported issues.

The full notes, inline masks, all returned judgments, and my analysis are in [judgments.md](./judgments.md).

## What we tested

Can the same model recognize missing or additional meaning in existing masks, when it does not have to generate a mask?

The approved [prompt](./recognition-prompt.md) assessed six existing masks for three fixed ASv6.8 subjects across two original notes. Each subject had one acceptable and one incorrect mask. We ran three independent trials per mask: **18 fresh calls**, all **gpt-5.6-sol, low reasoning**. Every call saw exactly one highlighted mask in its complete note and the subject. It saw no competing masks, expected judgments, review comments, or earlier answers.

The [plan](./plan.json) and [expected judgments](./expected-judgments.json) are pre-inference snapshots of the approved proposal. Nothing was repaired or rerun after seeing an answer. These are reused development examples, not an unseen holdout or a population-accuracy estimate.

## What follows

The state-backing result shows that this model and prompt can recognize one error that appears during generation. But the missing-life result shows that providing an existing mask does not by itself solve the evidence-selection problem. The settlement result is inconsistent even with unchanged input.

I would not add an automatic checker to the pipeline on this evidence. This does not prove that checking cannot work; it shows that this particular checker is not yet reliable. It also does not establish the cause of generation failures.

ASv6.8, mask defaults, SSE, segmentation, production code, and all saved human decisions are unchanged. New judgments remain my analysis pending your review.

## Run record

- All 18 calls completed on their first attempt and returned the requested JSON object. No repairs or retries.
- Verified 18 distinct threads and working directories, with no overlap against 277 earlier call records. Exact prompt, response, manifest, configuration, and wrapper hashes matched.
- The existing pinned CLI was 0.153.0. Tools, web search, inherited rules, user configuration, and conversation history were disabled through the existing wrapper. This does not claim visibility into undisclosed service-level context.
- Trials ran sequentially with a 2 GiB local memory limit, zero permitted swap, and a 15-minute limit per six-call trial. Reported local memory peaks were 16.4, 16.7, and 16.9 MiB; all used zero swap. Total call time was 111.2 seconds.
- Usage: 40,371 input tokens, including 2,176 cached input tokens; 1,140 output tokens, including 741 reasoning tokens. Cached input did not add previous responses to the recorded prompt. Existing subscription only; no new paid API or rented-compute commitment.
- All 50 protected files remained unchanged, including prompts, registries, source data, user reviews, the runner, and the budget ledger.

Raw input/output and event records are in `trial-{1,2,3}/run/`. [assistant-review.json](./assistant-review.json) contains the per-call semantic judgments; [verification.json](./verification.json) contains the execution, isolation, resource, and integrity checks. [cases.json](./cases.json) preserves exact note text and source occurrences.
