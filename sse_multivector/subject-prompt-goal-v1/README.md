# Subject-prompt goal

Continue from ASv6.11. The assistant now makes routine semantic judgments and can revise/test the subject prompt independently. The latest agreed requirements, Sol low, isolated runner and earlier evidence remain unchanged.

The [validation plan](./plan.json) was recorded before new generation. It fixes 28 development notes, eight repeated difficult notes, and a final test of 60 previously unused notes with 12 repeated notes. Passing requires at least 54 of the 60 final notes to have no identified error or unresolved judgment, at least 95% of subjects accepted, and no recurring failure under the plan's exact definitions. These are pilot acceptance limits, not a population accuracy estimate.

Current state: 62 isolated calls completed across ASv6.12, its diagnostic repeats, and ASv6.13. Neither candidate passed the fixed development gate. ASv6.8 remains the frozen default. No final-validation calls have been made.

ASv6.12 incorrectly turned fee-priority values into counts in all three trials. Its publication-label problem occurred in two of three trials. ASv6.13 removed the targeted publication label in its first run, but the numeric error remained and commentary about truncated text returned. The next action is repeating those two ASv6.13 cases before another prompt edit.

Generation is temporarily paused because host I/O pressure exceeded the recorded admission limit before any of those repeat calls started. This is not a failed model call or a finished goal.

- [Current checkpoint](./status.json)
- [ASv6.12 full review](./asv6.12/review.json) and [diagnostic review](./asv6.12/diagnostic-review.json)
- [ASv6.13 full review](./asv6.13/review.json)
- [Explicit review correction](./review-corrections.json): mirroring-only provenance is not the linked post's content. This changes ASv6.12's first-pass result from 24/28 to 23/28 clean notes; its historical judgments are retained.
- [Isolation and preservation verification](./verification-development-1.json)

Every generated subject is preserved verbatim in each run's `output.json` and `results.jsonl`. The JSON reviews record subject-level decisions and whole-note coverage separately. These are assistant judgments, not new user approvals.

No personal notes, previous prompt text, raw output or user decision is to be edited. Masks and downstream processing are outside this goal.
