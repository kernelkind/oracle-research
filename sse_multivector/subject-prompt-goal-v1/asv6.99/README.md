# ASv6.99 Individual action copies under a shared tool

Status: tested experimental draft; both focused targets pass; whole-answer failures
remain; not adopted.
The user approves the next N096 target after the [ASv6.98 results](../asv6.98/README.md#completed-results).
Production adoption remains a separate decision.

[ASv6.99](ASv6.99.md) extends existing C1 instead of adding another example:

> Cutting it and them with a knife.

Every complete individual and shared cutting subject now names the knife.
All previous numbered placements remain; five entries add Knife and both
individual actions, with the shared action beneath each. The Knife branch
therefore retains three distinct source meanings. Its shared action alone
cannot replace the individual copies. A general Knife heading does not impose
a purpose absent from those source strings. The tool example differs from
the regression's olive-oil participant while demonstrating the existing copy rule.

The instructions and C2–C8, including the successful recipe example, remain
byte-identical. The [34 primary assignments and five implications](../asv6.96/README.md#actual-instruction-and-example-coverage)
remain intact. C1 adds a focused R20–R23 compatible-copy witness; complete
partial/shared sources and tool reference resolution also retain R01/R02/R04/R16.
No new requirement or production step is introduced.

C1 grows from 56 to 61 entries; eight examples total 154 entries, up from 149.
The exact addition is 2,002 characters per request, not a measured token increase.
The same single prompt/post inference remains. Repeating example context across
the corpus still costs input; adoption needs demonstrated benefit.
The minimal authored tool-copy check first fails on ASv6.98 because no shared
tool branch is demonstrated. ASv6.99 passes 158 focused consolidation, example,
revision and attempt-budget checks using production subject validation. C1's
copy grouping is checked; C8's reviewed branch ordering is preserved verbatim.
Static validation does not establish model correctness.

Pinned native [source edits](prompt-edits.json) and [template edits](edits.json)
produce separate revision receipts. Source SHA256:
`e87bc404c65bd911b789d9c88d9b8d3e13f10f0ba97805ab6dfc10a55eb7acc0`.
The change follows [official OpenAI guidance on direct instructions and aligned examples](https://developers.openai.com/api/docs/guides/reasoning-best-practices).

## Fixed regression screen

Three native six-case plans under `experiments/sp-autonomous-v1/shared-tool-v1/`
U1/U2/U3 inherit ASv6.98 T1/T2/T3 through `prepare --from`, with the new template,
`--repeat` and the same history root `experiments/sp-autonomous-v1`.
Complete POST/evidence and settings remain unchanged: subscription
openai-codex/gpt-6.1-sol/medium, WebSocket, 1,800-second timeout, no output cap
and concurrency one per runner. Three runners permit three in-flight requests.
Freeze all plans and source before inference. Finish all 18 intentional first
calls regardless of quality: N063, N074, N096, N100, S006 and D006 in each trial.

Each `run --max-new-attempts 12` uses the unchanged shared counter
`target/sp-autonomous-v1/attempt-budget.json`, initially 1,523/2,000.
Existing provider-transient retries alone qualify, at most two total attempts
per case; no quality retry, model switch or paid fallback. Subscription calls
add no incremental cash charge; quota remains unmeasured. The eight prospective
posts stay unused.

Primary target: first retain three complete individual N096 sauté sources—onion,
celery and carrot—with supported quantities/modifiers, two tablespoons olive oil,
large pan, medium heat and the enclosing author's easy, never-fail recipe feeding
five people. Then require each formed source under every compatible returned
oil occurrence. Never-formed sources are source loss, not additionally missing
copies. Retain the complete shared sauté separately. Optional Oil headings need
not be added. Sauce-qualified pan compatibility stays open and is not decisive.

Native historical review finds this narrow target already passes ASv6.98 T1
and T2, and fails T3: **2/3**, not 0/3. T3 forms individual sources at
1.1.1.1.1.1/1.1.1.1.2.1/1.1.1.1.3.1, while olive oil 1.1.1.1.11 contains
only the combined sauté. This baseline is historical, not a contemporaneous
causal control. Repeated development cases do not establish unseen accuracy.

S006 recipe source retention/placement is the separate preservation target;
ASv6.98 passes 3/3. Whole-answer A/R/U uses the unchanged [bounded ASv6.98 criteria](../asv6.98/README.md#review-corrections-and-limits):
Food is not an exclusive-use class, SP supports action/relationship aboutness,
and unresolved readings stay separate from decisive defects. Review complete
unchanged POST and parsed answers via native `show`; preserve actual individual
reviewer reasons and corrections through native `review`, then broker adjudicate.
Agent assessments are not human whole-answer gold or independent accuracy proof.

## Completed results

All 18 planned medium calls return valid first answers with no failures, invalid
receipts, retries, reuse or unrun cases. The shared counter moves from
1,523 to **1,541/2,000**, leaving **459 attempts**. Native source/template and
plans remain frozen at checkpoint `683c97d8`; saved SDK requests and receipts
retain the exact prompt, provider/model, effort and schema. All 158 focused
offline checks pass; static correctness is separate from teacher correctness.

**N096 source retention and individual sauté copies under olive oil pass 3/3.**
All three complete individual actions retain material quantities, fine chopping,
oil amount, pan, heat and full recipe scope. Each answer returns one oil occurrence
and includes all three individual actions there, alongside their complete shared
sauté. U3's feeding-five paraphrase preserves the recipe capacity. Sauce-qualified
pan compatibility is not used to establish this target.

| Trial | Individual source locations (onion / celery / carrot) | Oil occurrence | Individual copies under oil |
| --- | --- | --- | --- |
| U1 | 1.1.1.1 / 1.1.2.1 / 1.1.3.1 | 1.1.11 | .1 / .2 / .3 |
| U2 | 1.1.1.1.1 / 1.1.1.2.1 / 1.1.1.3.1 | 1.1.1.11 | .1 / .2 / .3 |
| U3 | 1.1.1.1.1 / 1.1.1.2.1 / 1.1.1.3.1 | 1.1.1.11 | .1 / .2 / .3 |

The shared sauté appears beneath each of these oil-branch individual actions.
The saved same-criterion ASv6.98 result is 2/3; fresh ASv6.99 is 3/3. This small
historical contrast supports a bounded repair signal, not causal proof.

**S006 recipe-retention and placement also remain 3/3.** Complete salt and pepper
sources occur at 1.1.1/1.1.2 and their combination at 1.1.1.1. Salt repeats at
2.1.1/3.1/5.1; pepper at 2.1.2/4.1/5.2; the combination appears beneath all eight
individual occurrences. All retain seasoning food, to taste, author, reliability,
dish and five-person capacity. No absent easy claim is required.

| Case | U1 | U2 | U3 | Remaining finding |
| --- | --- | --- | --- | --- |
| N063 | U | U | R | U1/U2 Foodstr community/platform reading open; U3 Cooking lacks formed ingredient/list copies. |
| N074 | U | R | U | U2 individual quantity advice lacks Food copy; other advice/Unless readings remain open. |
| N096 | R | R | R | Sauté target passes; U1/U2 individual tomato additions lack beef-condition copies, U3 individual additions never form. |
| N100 | R | R | R | U1/U3 whole shared trimming source never forms; U2 loses finally and nests generic recommendation below specific purchased unit. |
| S006 | A | A | A | Complete recipe-qualified seasoning sources and copies retained. |
| D006 | R | R | R | U1/U3 reciprocal material-action copies missing; U2 improves those copies but omits separate complete individual material sources. |

Whole-answer totals are **3 bounded accepts, 11 rejects, 4 uncertain**.
The twelve original answers are 0/8/4; the six diagnostics are 3/3/0.
Historical ASv6.98 labels remain 3/14/1; neither total is a causal quality score
comparison. Optional returned headings and unresolved readings affect whole-answer
assessment. Prospective posts remain unused; no unseen/general accuracy claim.

Three native `show` witnesses describe the clearest remaining target:

- U1 N096 forms individual chopped-tomato addition 1.1.7.2, explicitly conditioned
  on the 500 g beef being uniformly coloured. Beef 1.1.6 contains only the combined
  tomato/purée/water addition, not this complete individual source.
- U2 N096 forms the analogous individual source 1.1.1.7.1, but beef 1.1.1.6 again
  receives only the combined addition. Its own beef-condition wording establishes
  the relationship; the copy requirement does not come from adjacency or context.
- U3 N096 forms combined addition 1.1.1.6.4 but no complete individual chopped-tomato,
  purée or water addition source. This is source loss, not extra missing-copy counts.

## Review corrections and limits

Two whole-answer reviewers inspect unchanged complete POST and parsed answers
with prompt/version definitions withheld. Reviewer B's first readiness command
accidentally exposes truncated baseline-containing metadata, so a fully blinded
claim is unavailable. Later judgments use actual full POST/parsed projections.
Each reviewer's actual reasons are recorded separately, not substituted with the
broker's selected witness. The separate fixed-target audit matches the complete
source/copy evidence above; reviewer agreement is not independent accuracy proof.

Native history preserves ten initial/superseded events, 36 final individual
reviewer events and 18 broker adjudications: **64 hash-current events**. Score
the latest broker verdict per case. Both reviewers initially miss U3 N063's
returned Cooking branch and change A→R. Reviewer B changes U2 N074 U→R on the
individual Food-quantity copy. Reviewer A proposes vegetable/plant-food rejections
for U1/U3 N074, then withdraws them as uncalibrated; U1 follows U→proposed R→U.
Reviewer A changes U1/U3 N100 U→R after applying explicit shared-predicate
combination coverage. Both change U2 D006 A→R: correctly copied individual
trimming events do not replace separate complete individual material subjects,
as the existing event-versus-subject clause requires. No extra copy count is
charged for these never-formed material sources.

Foodstr membership, N074 advice/Unless and vegetable/plant-food readings,
mother-instruction/Dietary-advice compatibility, dinner/purchase attachment,
sauce membership, implicit sirloin origin, duplicated some and vacuum-sealer
food-preservation purpose remain separate uncertainties. Neither nonfood uses
nor a universal culinary-purpose restriction establishes a rejection here.
Human edge calibration is not whole-answer gold.

The useful next target is N096's individual tomato/purée/water additions and
their copies under compatible beef-condition headings. It repeats across all
three answers as either source loss or missing copies. Preserve both successful
demonstrations while investigating this next existing-rule transfer. This is a
proposal for a subsequent iteration, not another run or production adoption.

The user approves this target. [ASv6.100](../asv6.100/README.md) adds a separately
named condition participant to existing C1 while preserving Knife and C8.
Its [completed fixed screen](../asv6.100/README.md#completed-results) keeps the
individual-addition/beef-copy target at 0/3 and full sauté preservation at 2/3;
S006 remains 3/3. ASv6.100 is not a promotion candidate. Source completeness and
conditional copies remain separately reported.
