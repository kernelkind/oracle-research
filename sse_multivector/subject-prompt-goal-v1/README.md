# Subject-prompt goal

Continue from ASv6.11. The assistant now makes routine semantic judgments and can revise/test the subject prompt independently. The latest agreed requirements, Sol low, isolated runner and earlier evidence remain unchanged.

The [validation plan](./plan.json) was recorded before new generation. It fixes 28 development notes, eight repeated difficult notes, and a final test of 60 previously unused notes with 12 repeated notes. Passing requires at least 54 of the 60 final notes to have no identified error or unresolved judgment, at least 95% of subjects accepted, and no recurring failure under the plan's exact definitions. These are pilot acceptance limits, not a population accuracy estimate.

Current state: 84 isolated calls completed. ASv6.12 and ASv6.13 failed full-development review; ASv6.14 and ASv6.15 failed the focused repeated diagnostics. ASv6.16 is prepared but untested. ASv6.8 remains the frozen default. No final-validation calls have been made.

ASv6.12 incorrectly turned fee-priority values into counts in all three trials. Its publication-label problem occurred in two of three trials. ASv6.13 removed the targeted publication label in its first run, but the numeric error remained and commentary about truncated text returned in all three trials. Later revisions stopped inventing counts, but still produced items without their source context. The financial diagnostic also exposed incorrect or unresolved source attribution. These are difficult-case diagnostics, not estimates of corpus-wide accuracy.

The I/O-pressure guard temporarily paused admission before the ASv6.13 repeat calls. Generation resumed only after pressure fell below the fixed limit. All launched calls completed; no generation process remains live. The next action is the three ASv6.16 diagnostic trials, subject to the same resource guard.

- [Current checkpoint](./status.json)
- [ASv6.12 full review](./asv6.12/review.json) and [diagnostic review](./asv6.12/diagnostic-review.json)
- [ASv6.13 full review](./asv6.13/review.json)
- [ASv6.13 repeated diagnostics](./asv6.13/diagnostic-review.json) and [reference-resolution review correction](./asv6.13/review-corrections.json)
- [ASv6.14 repeated diagnostics](./asv6.14/diagnostic-review.json)
- [ASv6.15 repeated diagnostics](./asv6.15/diagnostic-review.json)
- [ASv6.16 proposal](./asv6.16/proposal.json) and [exact untested prompt](./asv6.16/ASv6.16.md)
- [Explicit review correction](./review-corrections.json): mirroring-only provenance is not the linked post's content. This changes ASv6.12's first-pass result from 24/28 to 23/28 clean notes; its historical judgments are retained.
- [Latest isolation and preservation verification](./verification-development-2.json)

Every generated subject is preserved verbatim in each run's `output.json` and `results.jsonl`. The JSON reviews record subject-level decisions and whole-note coverage separately. These are assistant judgments, not new user approvals.

No personal notes, previous prompt text, raw output or user decision is to be edited. Masks and downstream processing are outside this goal.
