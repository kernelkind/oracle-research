# Removing the two relationship warnings

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

ASv6.20 did not improve the context failures this comparison targeted. Stop this change after the first 24 calls; the remaining 12 calls cannot rescue its predeclared acceptance condition.

ASv6.20 is exactly ASv6.13 with two special warnings about statement proximity and co-mention removed. The general requirement for stated or reasonably implied relationships remains. No other prompt, source, model or runner setting changed.

## The result that determines the decision

Each cell counts outputs with missing source context, out of two independent outputs.

| Source note | ASv6.13 | ASv6.20 |
| --- | ---: | ---: |
| D10 — Riley Walz hiring | 2/2 | 2/2 |
| D19 — Bitcoin dashboard | 0/2 | 0/2 |
| D25 — CEO anecdote | 2/2 | 2/2 |

D10 repeatedly produced an item such as “One analyst differed from the others by using predictive phrasing.” It omitted what the analyst was analyzing: Riley Walz’s hiring by OpenAI. Other items in the same output correctly included that hiring context.

D25 repeatedly left at least one thesis, tracking, trajectory or fundamentals item attached only to “the development,” “the situation” or “the quoted account.” Other items sometimes supplied the CEO context correctly.

D19 retained the Bitcoin-dashboard context under both prompts. It therefore provides no evidence of a benefit from the change.

The [predeclared condition](./proposal.json) required repeatable improvement on at least two target notes. D10 and D25 already have two candidate failures each. Even if both were clean in a third trial, each would still fail the allowed one-in-three limit. This is why the comparison stops now, not a decision based on a convenient individual output.

## What else happened

| Across the six notes and two trials | ASv6.13 | ASv6.20 |
| --- | ---: | ---: |
| Outputs with no error or unresolved judgment | 4/12 | 6/12 |
| Accepted subjects | 197/209 | 173/188 |
| Subjects judged erroneous | 11 | 14 |
| Subjects with unresolved judgments | 1 | 1 |
| Outputs with missing source meanings | 0 | 1 |
| Outputs with unresolved coverage | 1 | 1 |

These selected notes cannot measure corpus-wide accuracy. Different subject counts also reflect permitted overlapping and duplicate output.

- ASv6.20’s second D24 output omitted most of the insurance note, including the survey figures and much of the interpretation. The independent audit found no wrong source or local input truncation: both trials have the same full rendered prompt hash and 2,361 input tokens. This is one observed coverage failure, not a demonstrated recurring regression. Only the second trial reports cached input tokens; that does not establish the cause.
- ASv6.13’s first D28 output calculated a new two-week interval and changed the reason-for-selection negation into “Bitcoin is not better money under normal conditions.” ASv6.20 did neither in these two outputs. That does not establish a general fix or support the context hypothesis.
- ASv6.13’s second D24 output attributed the separate two-model interpretation to CIAB. ASv6.20 did not, but one of its outputs omitted most of that material; losing content cannot count as solving attribution.
- Some Katie interpretations remain uncertain. The direct smile antecedent is a plausible reading, not automatically an invented connection. Ticket availability and whether the opening is a greeting or a presentation heading remain unresolved. These judgments do not affect the stopping decision.

All complete notes, exact outputs and individual judgments (`./results.md`) are available together. No subject was edited.

## What we learned

Removing these warnings did not reduce the repeated context omissions. It does not prove the warnings never matter, nor establish the actual cause of those omissions.

This is diagnostic progress, not an improved extractor. ASv6.20 is not promoted. ASv6.13 remains an earlier broadly tested reference; neither it nor the later candidates has passed the fixed validation. ASv6.8 stays frozen.

Do not rerun this comparison or reword these same warnings automatically. A different hypothesis must be supported and predeclared before further generation. No next comparison is selected in this record.

## Execution and review

- 24 successful independent Sol-low calls; no retries, tool calls or shared conversation threads.
- All 24 outputs were reviewed against complete notes under opaque prompt/trial IDs. Judgments were saved before revealing identities. The reviewer knew prior prompts and results, so this is limited identity hiding, not independent review.
- Exact prompt/input/raw-output checks and review completeness passed. The verifier checked thread/workdir reuse against 1,001 earlier recorded calls. Its scope is documented in `./verification.json`.
- Host I/O pressure delayed the first admission; calls started after it fell below the fixed limit. Calls remained sequential. No new paid resource or credential change.
- Recorded usage: 53,244 input tokens, including 2,176 cached; 15,525 output tokens, including 8,999 reasoning tokens. Subcounts are included, not additional.
- No final-validation note was used. The original validation plan and canonical prompt registry are unchanged.

The proposal/configs were committed before generation at `bd0fb4089a09d908c4516ace1b29718d9c333c39`. The verifier reports generation as partial because the optional third trial was not run; the bounded comparison itself is finished by its stopping rule.

Machine-readable decision (`./assessment.json`) · Review (`./review.json`) · Runtime (`./runtime.json`) · [Verifier](./verify.py) · Independent audit (`./independent-audit.json`)

See [conversion gaps](../../../docs/experiments/publication-gaps.csv) for `collection:tracked-subject-prompt-goal-v1`.
