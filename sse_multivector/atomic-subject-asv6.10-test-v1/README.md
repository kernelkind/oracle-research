# ASv6.10 test

The original ambiguity comment and calculated time gap did not recur. This is progress on those examples, not a complete fix: one Iran output still adds commentary about what is not asserted, and one Katie output leaves the possible contact/ticket connection unexpressed.

Follow-up: the [20-note ASv6.8 versus ASv6.10 comparison](../atomic-subject-asv6.8-vs-asv6.10-holdout-v1/README.md) is complete. Both prompts stayed unchanged; ASv6.8 remains frozen. The review wording now permits broad and repeated subjects. Questionable outputs still await human review.

[Full original notes, every ASv6.9 and ASv6.10 subject, and analysis](./results.md)

Six fixed notes, three fresh ASv6.10 calls per note, Sol low. The comparison uses the 18 saved ASv6.9 calls; it does not rerun them. All 18 new calls completed on their first attempt.

## What changed

Each count is out of three calls for the indicated note. These are assistant judgments on development examples, not a corpus accuracy score.

| Observation | ASv6.9 | ASv6.10 |
| --- | --- | --- |
| Katie: adds commentary about ambiguous meaning | 1/3 | 0/3 |
| Iran: calculates a new two-week gap | 1/3 | 0/3 |
| Sports: adds an unclear-connection comment | 0/3 | 0/3 |
| AI: adds commentary about unstated meaning | 0/3 | 0/3 |
| Kremlin: retains the source's “nothing to add” statement | 3/3 | 3/3 |
| Iran: retains the stated reason, normal-conditions contrast and future question | 3/3 | 3/3 |

## What still concerns me

Iran, trial 3, subject 18:

> Bitcoin is not asserted to be better money under normal conditions.

The source says:

> This is why restricted actors are shifting toward it for settlement. Not because it is better money in normal conditions, but because it remains usable when every other rail can be cut.

That distinguishes reasons for adoption. The extra subject instead describes an absent assertion. I would flag that as added commentary, pending your judgment. Subject 17 in the same output already preserves the actual contrast correctly. This extra item appears in 1/3 ASv6.10 Iran calls and none of the saved ASv6.9 calls.

Katie trials 1 and 2 give possible conditions linking direct contact with an unwanted ticket. Trial 3 lists the contact and ticket separately, losing that possible connection. The same omission occurred in ASv6.9 trial 2, so it is not an established new regression. Katie's information-recipient wording and the LLC and smile/repair interpretations remain review questions; they are not counted as proven failures.

Reasonable implications, alternative interpretations, broad subjects and duplicate subjects remain allowed. The presence of “may,” “possibly,” or “not” is not itself a failure.

## Execution and limits

The [approved prompt](../atomic-subject-asv6.10-proposal-v1/ASv6.10.md), [pre-run plan](./plan.json), [original input](../atomic-subject-asv6.8-vs-asv6.9-v1/input.json) and existing runner were unchanged during the test. No output edits, repair calls, retries, masks, SSE runs or default changes. ASv6.8 remains frozen; ASv6.10 awaits user review.

Verification found 18 distinct threads and working directories, one turn per call, no tools, no overlap with the 36 prior comparison threads/workdirs, exact prompt and raw-output hashes, and unchanged exported subjects. All 65 protected files matched at the end of generation. A later documentation-only update links this follow-up from the previous comparison README; its measured results and all other protected files remain unchanged. [Verification](./verification.json)

New usage: 39,753 input tokens, including 3,840 cached; 8,039 output tokens, including 5,131 reasoning. Calls ran sequentially through the existing subscription, without a new paid API or rental commitment. Periodic OS checks showed no memory or I/O pressure. The service reported launcher memory as 16.6M per trial; that does not measure the separate Codex scopes. [Runtime details](./runtime.json)

These are six previously used notes with three calls each and a saved, nonconcurrent baseline. The result does not establish broad reliability or isolate the effects of the two prompt edits. Detailed judgments remain separate from raw outputs in [assistant-analysis.json](./assistant-analysis.json).
