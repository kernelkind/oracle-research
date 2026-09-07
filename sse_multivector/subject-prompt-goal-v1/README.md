# Subject-prompt goal

Continue from ASv6.11. The assistant now makes routine semantic judgments and can revise/test the subject prompt independently. The latest agreed requirements, Sol low, isolated runner and earlier evidence remain unchanged.

The [validation plan](./plan.json) was recorded before new generation. It fixes 28 development notes, eight repeated difficult notes, and a final test of 60 previously unused notes with 12 repeated notes. Passing requires at least 54 of the 60 final notes to have no identified error or unresolved judgment, at least 95% of subjects accepted, and no recurring failure under the plan's exact definitions. These are pilot acceptance limits, not a population accuracy estimate.

Current state: the six-revision limit has been reached without a passing candidate. All 102 isolated calls were reviewed and verified. ASv6.12 and ASv6.13 failed full-development review; ASv6.14 through ASv6.17 failed the focused repeated diagnostics. ASv6.8 remains the frozen default. No final-validation calls have been made.

ASv6.12 incorrectly turned fee-priority values into counts in all three trials. Its publication-label problem occurred in two of three trials. ASv6.13 removed the targeted publication label in its first run, but the numeric error remained and commentary about truncated text returned in all three trials. Later revisions stopped inventing counts, but still produced items without their source context. The financial diagnostic also exposed incorrect or unresolved source attribution. These are difficult-case diagnostics, not estimates of corpus-wide accuracy.

ASv6.17 handled the clipped CEO passage correctly in all three trials. It omitted the unfinished word and included CEO context in the later subjects. Two failures still recurred in all three trials:

- Fee-priority entries such as “For Bitcoin block 923432, high priority is paired with 3” omit the fee/mempool context that another item supplies.
- The financial report's “Sector: Insurance | Confidence: 94%” becomes a subject about the report's classification rather than its content.

One financial trial also explicitly assigned the two-model analysis to CIAB, the source of the earlier survey. Another left that source ambiguous. These are difficult-case results, not a corpus-wide error rate. Broad, overlapping and duplicate subjects were not counted as errors.

The four latest candidates used the same three diagnostic notes, each generated three times. A clean output means every subject was accepted and no missing meaning was identified.

| Prompt | Clean outputs out of 9 |
| --- | ---: |
| ASv6.14 | 1 |
| ASv6.15 | 0 |
| ASv6.16 | 0 |
| ASv6.17 | 3 |

ASv6.17 is the strongest of these focused results, but was not submitted to the 28-note test because its failures recurred. There is no established best overall candidate. Of the two candidates tested on all 28 notes, ASv6.13 had more clean notes (24 versus 23 after recorded review corrections), while ASv6.12 had a higher accepted-subject fraction; both failed.

The I/O-pressure guard temporarily paused earlier admission. All launched calls completed; no generation process remains live. Further prompt revision requires authorization to extend the recorded six-revision limit. The acceptance criteria and unused final data remain unchanged. A failed candidate will not be frozen merely because the iteration limit was reached.

- [Current checkpoint](./status.json)
- [ASv6.12 full review](./asv6.12/review.json) and [diagnostic review](./asv6.12/diagnostic-review.json)
- [ASv6.13 full review](./asv6.13/review.json)
- [ASv6.13 repeated diagnostics](./asv6.13/diagnostic-review.json) and [reference-resolution review correction](./asv6.13/review-corrections.json)
- [ASv6.14 repeated diagnostics](./asv6.14/diagnostic-review.json)
- [ASv6.15 repeated diagnostics](./asv6.15/diagnostic-review.json)
- [ASv6.16 repeated diagnostics](./asv6.16/diagnostic-review.json)
- [ASv6.17 repeated diagnostics](./asv6.17/diagnostic-review.json), [exact tested prompt](./asv6.17/ASv6.17.md), and [proposal](./asv6.17/proposal.json)
- [Explicit review correction](./review-corrections.json): mirroring-only provenance is not the linked post's content. This changes ASv6.12's first-pass result from 24/28 to 23/28 clean notes; its historical judgments are retained.
- [Latest isolation and preservation verification](./verification-development-3.json): 102 distinct threads and empty working directories, one turn each, no tool events, exact prompts and unedited raw outputs.

Every generated subject is preserved verbatim in each run's `output.json` and `results.jsonl`. The JSON reviews record subject-level decisions and whole-note coverage separately. These are assistant judgments, not new user approvals.

No personal notes, previous prompt text, raw output or user decision is to be edited. Masks and downstream processing are outside this goal.
