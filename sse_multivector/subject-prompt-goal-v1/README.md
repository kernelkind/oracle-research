# Subject-prompt goal

Continue from ASv6.11. The assistant now makes routine semantic judgments and can revise/test the subject prompt independently. The latest agreed requirements, Sol low, isolated runner and earlier evidence remain unchanged.

The [validation plan](./plan.json) was recorded before new generation. It fixes 28 development notes, eight repeated difficult notes, and a final test of 60 previously unused notes with 12 repeated notes. Passing requires at least 54 of the 60 final notes to have no identified error or unresolved judgment, at least 95% of subjects accepted, and no recurring failure under the plan's exact definitions. These are pilot acceptance limits, not a population accuracy estimate.

Current state: no prompt has passed. All 158 isolated calls have been reviewed and verified, including a fresh 56-call ASv6.13/ASv6.17 comparison across all 28 development notes. ASv6.18 is prepared for a controlled instruction test, not frozen. ASv6.8 remains the frozen default. No final-validation calls have been made.

The original plan remains byte-identical as predeclared evidence. Its self-imposed revision, call and final-attempt caps, and the historical verification reports' permission-blocking conclusions, are superseded by the revised goal. They are not current authorization limits. The semantic requirements, source data, validation criteria and resource safeguards remain fixed. Current operational authority is recorded in [status.json](./status.json).

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

ASv6.17 was the strongest of these focused results, but those diagnostics alone left its broader performance unmeasured. The earlier audited full runs gave ASv6.13 24 clean notes and ASv6.12 23; accepted subjects were 257/269 and 255/264 respectively. Both failed the fixed criteria. Those historical results remain preserved separately from the fresh comparison below.

The [review audit](./semantic-review-audit-v1.json) corrects four judgments that treated plausible implications too strictly. It separately records unresolved slang and non-English interpretation as reviewer uncertainty, not established extractor failures. These corrections do not make either prompt pass.

The [completed full-development comparison](./representative-comparison-v1/README.md) used unchanged ASv6.13 and ASv6.17 on the same 28 notes, with one fresh isolated output each. ASv6.13 had 21/28 clean notes and 254/271 accepted subjects; ASv6.17 had 19/28 and 147/172. ASv6.17 improved four notes but regressed on six, notably presentation metadata and URL-only names. It did not establish a best overall prompt or the causal effect of individual instructions. The final notes stay unused.

Next is the [ASv6.18 controlled diagnostic](./asv6.18/proposal.json): restore only ASv6.13's content-versus-presentation sentence in ASv6.17, with three fresh trials of both versions on nine fixed notes. Metadata targets test the suspected mechanism; URL, event-reference and numerical cases check adjacent effects and regressions. This is a diagnostic, not a replacement for the fixed validation criteria.

The I/O-pressure guard temporarily paused earlier admission. All previously launched calls completed; the resumption check found no active generation unit. Host-pressure checks and sequential call admission remain mandatory.

- [Current checkpoint](./status.json)
- [ASv6.12 full review](./asv6.12/review.json) and [diagnostic review](./asv6.12/diagnostic-review.json)
- [ASv6.13 full review](./asv6.13/review.json)
- [ASv6.13 repeated diagnostics](./asv6.13/diagnostic-review.json) and [reference-resolution review correction](./asv6.13/review-corrections.json)
- [ASv6.14 repeated diagnostics](./asv6.14/diagnostic-review.json)
- [ASv6.15 repeated diagnostics](./asv6.15/diagnostic-review.json)
- [ASv6.16 repeated diagnostics](./asv6.16/diagnostic-review.json)
- [ASv6.17 repeated diagnostics](./asv6.17/diagnostic-review.json), [exact tested prompt](./asv6.17/ASv6.17.md), and [proposal](./asv6.17/proposal.json)
- [Explicit review correction](./review-corrections.json): mirroring-only provenance is not the linked post's content. This changes ASv6.12's first-pass result from 24/28 to 23/28 clean notes; its historical judgments are retained.
- [Earlier isolation and preservation verification](./verification-development-3.json): 102 distinct threads and working directories, one turn each, no tool events, exact prompts and unedited raw outputs.
- [Comparison review](./representative-comparison-v1/review.json) and [latest verification](./representative-comparison-v1/verification.json): 56 further distinct threads/workdirs, paired sequential admission, exact prompts, unchanged inputs and unedited outputs; no reuse across the 217 earlier calls checked.

Every generated subject is preserved verbatim in each run's `output.json` and `results.jsonl`. The JSON reviews record subject-level decisions and whole-note coverage separately. These are assistant judgments, not new user approvals.

No personal notes, previous prompt text, raw output or user decision is to be edited. Masks and downstream processing are outside this goal.
