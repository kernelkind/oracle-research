# ASv6.13 versus ASv6.21: context examples

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

ASv6.21 is not promoted. The candidate preserved the CEO note's context in two of three outputs; ASv6.13 did not in any. The candidate did not meet the predeclared improvement condition across two notes. Both prompts had 7 of 18 fully accepted outputs.

## What changed

ASv6.21 is the exact ASv6.13 instruction text plus two invented source-to-subject examples about a swimming pool and tapestry restoration. The examples demonstrate putting an observation's source context inside each subject. No test-note answers appear in them.

Six previously used development notes were held fixed. Each prompt generated three independent outputs per note: 36 calls, all with Sol low, fresh context, the existing runner and no tools. After 24 calls, neither of the two potentially improved notes was ruled out, so the declared final 12 calls were run. No retries or extra trials occurred.

## What happened

Numbers below count outputs with missing per-subject context, not all other defects.

| Note | ASv6.13 | ASv6.21 |
| --- | ---: | ---: |
| D10 — OpenAI hiring Riley Walz | 3/3 | 2/3 |
| D23 — Bitcoin fee-priority values | 3/3 | 3/3 |
| D25 — CEO question and the author's reaction | 3/3 | 1/3 |

Only D25 met the required change from at least two failing control outputs to at most one failing candidate output. The proposal required two such notes.

The D25 result is limited: one of the two context-complete candidate outputs still contains an unresolved paraphrase of the source's unfinished wording. It is not a fully accepted output.

Other findings:

- Both versions repeatedly turned the fee-note values into counts of items. ASv6.21 avoided the count interpretation once, but still omitted the fee context in that output.
- ASv6.21 named the Bitcoin dashboard from its URL in two outputs; ASv6.13 did not in these three trials.
- One ASv6.21 output explicitly assigned the two-model insurance analysis to CIAB. Each prompt also had one unresolved “Council” attribution.
- One ASv6.13 output calculated an unstated two-week interval.
- No distinct missing source meaning was identified in these 36 outputs. That does not repair incorrect individual subjects.

| Review measure | ASv6.13 | ASv6.21 |
| --- | ---: | ---: |
| Fully accepted outputs | 7/18 | 7/18 |
| Accepted subjects | 264/303 | 274/307 |
| Subjects judged erroneous | 38 | 31 |
| Unresolved subjects | 1 | 2 |

“Fully accepted” means all subjects and whole-note coverage were accepted. Broad, overlapping and repeated subjects remain allowed. Unresolved judgments are neither proven failures nor passes.

These totals include the later review correction (`../semantic-review-audit-v3.json`): B24's eighth subject refers to “the quoted employee’s question” without identifying the CEO context. It was incorrectly accepted. The original review and decision retain their initial totals, 265 accepted and 37 erroneous control subjects. This correction changes no clean-output count, target count or comparison decision.

## Decision

Close this example-only comparison. Do not replace the examples or rerun the same comparison to seek a better outcome. The result supports a limited context improvement on one note, not a reliable overall extractor.

ASv6.13 remains the earlier broadly tested reference; ASv6.8 remains the frozen default. The development/final validation rules are unchanged. No final notes were used and no prompt is eligible for final validation. A new experiment needs a materially different, defensible hypothesis from the cumulative evidence; this report does not select one.

## Evidence

- Full notes, every output, and judgments (`./results.md`)
- [Exact candidate prompt](../asv6.21/ASv6.21.md) and [frozen comparison proposal](./proposal.json)
- Decision (`./assessment.json`) and complete review (`./review.json`)
- Artifact and review verification (`./verification.json`)
- First 24-call decision (`./first-two-decision.json`)
- Blind reviews: first two trials (`./blind-review-first-two.json`), third trial (`./blind-review-third.json`)

Prompt/trial identities were hidden until each review was saved. Those original review files remain unchanged. The later correction is disclosed separately and was made with identities known; it is not a new blinded judgment. These selected difficult notes do not estimate corpus-wide accuracy. The comparison isolates the added example group, not either example separately or the value of examples in general.

See conversion gaps (`03bd9e45:docs/experiments/publication-gaps.csv`) for `collection:tracked-subject-prompt-goal-v1`.
