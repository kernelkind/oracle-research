# ASv6.100 Individual action copies under a condition participant

Status: experimental, tested; 169 focused offline checks pass; fixed target 0/3.
The user approves this next N096 target after the [ASv6.99 results](../asv6.99/README.md#completed-results).
Production adoption remains a separate decision.

[ASv6.100](ASv6.100.md) extends C1's shared instruction:

> Cutting it and them with a knife when a bowl is empty.

Each complete individual and shared cutting subject retains the named bowl
condition. Five entries add A bowl being empty, both individual actions beneath
it, and the shared action beneath each. The state participates through a condition,
while the knife is the tool and tissue/scraps are cutting objects. Those distinct
relationships all come from the action's own wording; they are not adjacency
inferences. The condition is a topic, without asserting actual emptiness, following
C2's existing conditional-blocking treatment. Optional generic Bowls is omitted.

Every existing placement remains. Knife copies are preserved; instructions and
C2–C8, including the recipe example, remain byte-identical. The [34 primary
assignments and five implications](../asv6.96/README.md#actual-instruction-and-example-coverage)
remain intact. C1 extends existing complete individual/shared source and compatible
copy demonstrations (R01/R02/R04/R16/R20–R23), without a new requirement or stage.

C1 grows from 61 to 66 entries; eight examples total 159, up from 154. The exact
addition is 2,829 characters per request, not a measured token increase. The same
single prompt/post inference remains. Repeated context still costs input at corpus
scale, so the experimental example is not adopted without demonstrated benefit.
The minimal condition-copy check first fails on ASv6.99 for its absent condition
participant. ASv6.100 passes 169 focused consolidation, example, revision and
attempt-budget checks through production subject validation. Static correctness
does not establish teacher correctness.

Pinned native [source edits](prompt-edits.json) and [template edits](edits.json)
generate separate revision receipts. Source SHA256:
`76aa2c831ab6d65802de4c76a960f8618c7ec7ee4cd62e619621ec8a453b095d`.
Static review catches and removes a duplicated phrase in two context fields
before inference. Superseded source/receipts/edits and unrun plans are preserved
as ignored artifacts; final source/template and all three plans are regenerated
through native commands. No calls use the superseded draft.
This continues [official OpenAI guidance on direct instructions and aligned examples](https://developers.openai.com/api/docs/guides/reasoning-best-practices).

## Fixed regression screen

Three native six-case plans under
`experiments/sp-autonomous-v1/conditional-participant-v1/` V1/V2/V3 inherit
ASv6.99 U1/U2/U3 through `prepare --from`, new template, `--repeat` and unchanged
history root `experiments/sp-autonomous-v1`. Full POST/evidence/settings remain:
subscription openai-codex/gpt-6.1-sol/medium, WebSocket, 1,800-second timeout,
no output cap and concurrency one per runner. Three runners allow three in-flight
requests. Freeze all source/plans before inference; finish all 18 intentional
first calls regardless of quality, with N063/N074/N096/N100/S006/D006 in each trial.

Each `run --max-new-attempts 12` uses the unchanged shared
`target/sp-autonomous-v1/attempt-budget.json`, initially 1,541/2,000. Only existing
provider-transient retries qualify, at most two total attempts per case; no quality
retry, model switch or paid fallback. Subscription adds no incremental cash charge;
quota is unmeasured. Eight prospective posts remain unused.

The focused primary N096 check has two parts. First form all three individual
additions of one 400 g tin of chopped tomatoes, one 400 g tin of tomato purée and
one tin of water, retaining the 500 g ground-beef uniform-colour condition and
the author's easy, never-fail spaghetti Bolognaise recipe feeding five. Retain
the shared addition separately. Then copy each individual source beneath every
compatible returned beef occurrence; its explicit condition establishes that
relationship. The shared action cannot replace an individual source. Source loss
is not also counted as missing copies of never-formed targets.

The separate full-source vessel check requires resolving the pan to the supported
large pan. Passing the focused ingredient/condition/recipe-and-copy subset does
not prove full source completeness. Do not automatically extend the initial
sauté's medium heat to later additions. Sauce-purpose compatibility remains open.
Optional generic Beef or Pan headings need not be added.

Native ASv6.99 historical witnesses establish the baseline:

| Trial | Beef occurrence | Individual tomato / purée / water additions | Shared addition under beef |
| --- | --- | --- | --- |
| U1 | 1.1.6 | 1.1.7.2 / 1.1.8.2 / 1.1.13.1, all three beef copies absent | 1.1.6.3 |
| U2 | 1.1.1.6 | 1.1.1.7.1 / 1.1.1.8.1 / 1.1.1.13.1, all three beef copies absent | 1.1.1.6.3 |
| U3 | 1.1.1.6 | No complete individual additions form | 1.1.1.6.4 |

The chosen ingredient/condition/recipe source subset is 2/3 retained; placement
for formed sources is 0/2; the joint focused target is 0/3. Shared-source beef
placement is 3/3. Full large-pan retention is separately 0/3: U1 omits the pan,
U2 says the pan without large, and U3 forms no individual additions. Preserve
these distinctions before testing. Saved controls are historical, not causal
comparisons; repeated development cases do not establish unseen accuracy.

Preservation targets remain N096 complete individual/shared sautés and all oil
copies (ASv6.99 3/3), plus S006 complete recipe-qualified individual/combined
seasonings and copies (3/3). Whole-answer A/R/U uses the unchanged [bounded
criteria](../asv6.99/README.md#review-corrections-and-limits), including distinct
event/material meanings, Food's nonexclusive-use classification and action/
relationship aboutness. Keep unresolved readings separate from decisive defects.
Review native full POST and parsed outputs with prompt/baseline/old-label projections
withheld, preserve actual reviewer reasons/corrections in native `review`, then
broker adjudicate. Agent assessments are not human whole-answer gold.

## Completed results

All 18 planned medium calls return valid first answers. There are no failures,
invalid receipts, retries, reused answers or unrun cases. All three native runners
exit successfully; the shared counter moves from 1,541 to **1,559/2,000**, leaving
**441 attempts**. Source/template and plans remain frozen at checkpoint
`d6ef62a1`. All 169 focused offline checks pass; aligned examples and mechanical
validity do not establish teacher correctness.

**The individual-addition/beef-copy target remains 0/3.** V1 and V3 never form
the three individual addition sources. V2 forms them, including the large pan,
but puts none below its returned beef occurrence. All three retain a separate
shared addition beneath every actual beef occurrence. That shared source does
not replace an individual source.

| Trial | Individual tomato / purée / water addition sources | Actual beef occurrences | Individual copies under beef | Shared addition under beef |
| --- | --- | --- | --- | --- |
| V1 | None form | 1.1.1.1.6; 2.1.1.6 | Not separately counted for absent sources | 1.1.1.1.6.3; 2.1.1.6.3 |
| V2 | 1.1.1.7.1 / 1.1.1.8.1 / 1.1.1.13.1 | 1.1.1.6 | All three absent | 1.1.1.6.3 |
| V3 | None form | 1.1.1.6; 7.1; broad Ground beef 7 | Not separately counted for absent sources | 1.1.1.6.3; 7.1.3 also covers 7 |

V2's individual chopped-tomato source at 1.1.1.7.1 is:

> Adding the 400 g tin of chopped tomatoes to the large pan once the 500 g ground beef is all the same colour for the author's easy, never-fail spaghetti bolognaise dinner recipe feeding five people

The analogous purée source retains its 400 g tin, and water retains one tin.
All retain the complete focused recipe and beef condition in their own wording;
all also occur beneath the pan at 2.1.7/8/9, with the shared addition below each.
Beef 1.1.1.6 contains only the shared addition, not these three individual sources.
The condition relationship establishes compatibility without an adjacency inference.

| Frozen check | Historical ASv6.99 | Fresh ASv6.100 |
| --- | --- | --- |
| All three ingredient/condition/recipe individual sources form | 2/3 | 1/3 |
| All beef copies, given formed individual source set | 0/2 | 0/1 |
| Individual formation plus beef copies jointly | 0/3 | 0/3 |
| Separate shared addition copied under every returned beef occurrence | 3/3 | 3/3 |
| All three individuals retain large pan in their own wording | 0/3 | 1/3 |
| Complete individual sautés and all oil copies | 3/3 | 3/3 |
| Complete individual/shared sauté sources and all oil copies | 3/3 | 2/3 |
| S006 full recipe-qualified individual/shared seasoning sources and copies | 3/3 | 3/3 |

Large-pan retention is a separate source check, not a successful joint repair.
V1's shared addition retains large pan; V3's shared addition omits it. Neither
forms individual additions. No extra missing-copy count is charged for those
absent individual targets. These small historical contrasts are not causal
comparisons or estimates of unseen accuracy.

**Full sauté preservation is 2/3.** V1 and V3 keep the three complete individual
actions and complete shared action beneath every oil occurrence. V1's oil sources
are 1.1.1.1.11 and 2.1.1.11; V3's are 1.1.1.11 and 11.1. Each has all three
individual actions with the shared action beneath each.

V2 also retains the three individual actions at 1.1.1.1.1, 1.1.1.2.1 and
1.1.1.3.1 and all oil copies beneath 1.1.1.11. Definite singular onion/celery/
carrot wording preserves each single ingredient; fine chopping, two tablespoons
of oil, large pan, medium heat and full recipe remain in the individual actions.
But its repeated shared action at 1.1.1.1.1.1 begins:

> Sautéing the finely chopped medium onion, one celery stick and medium carrot together in two tablespoons of olive oil

That wording explicitly qualifies the onion. The intervening one before celery
prevents safely distributing finely chopped to celery and carrot. Correct
individual entries cannot supply missing modifiers to the shared source. This
loss fails the predeclared full individual/shared preservation check, even though
individual source retention and oil placement remain 3/3.

**S006 remains 3/3.** In every trial complete salt and pepper sources occur at
1.1.1/1.1.2, 2.1.1/2.1.2, 3.1/4.1 and 5.1/5.2. The separate shared source is
a child of all eight individual occurrences. Each retains food-seasoning purpose,
to taste, author, never-fail recipe, dish and five-person capacity. No absent easy
claim is required; bare Salt remains a separate broader root.

The following are saved broker verdicts under the criteria used for this run.
The N074 vegetable-copy reason is withdrawn by the user calibration below;
N074's grades and aggregate totals await reassessment and must not be presented
as current three-of-three failures.

| Case | V1 | V2 | V3 | Historical broker finding |
| --- | --- | --- | --- | --- |
| N063 | U | U | U | Ingredient source/copy check passes; Foodstr/Nostr membership coverage remains open. |
| N074 | R | R | R | V1 qualified vegetable source absent; V2/V3 vegetable copies under children/mothers were required by the review, but that requirement is now withdrawn. V2's Food-quantity copy finding remains separately uncalibrated by this decision. |
| N096 | R | R | R | V1/V3 individual additions never form; V2 formed additions lack beef copies. V2 also loses shared-sauté fine chopping. |
| N100 | R | R | R | V1/V3 full fat-plus-quarter-pound shared trimming never forms; V2 full shared source lacks copies under repeated partial occurrences. |
| S006 | A | A | A | Complete individual/shared recipe-qualified seasoning meanings and all copies retained. |
| D006 | R | R | R | V1/V3 joint-qualified individual material sources lack reciprocal member copies; V2 separate materials never retain the joint quantity enclosure. |

Saved whole-answer totals under the then-used criteria are **3 bounded accepts,
12 rejects, 3 uncertain**. They are historical evidence, not current calibrated
scores. The twelve original answers were 0/9/3; diagnostics were 3/3/0. Historical ASv6.99
labels remain unchanged. These totals include optional returned headings and
unresolved meanings, and are not a causal quality score. Eight prospective posts
remain unused. Food is not rejected because its members can have nonfood uses.

## Review corrections and limits

Two independent reviewers inspect only complete native POST and parsed outputs
for quality, with prompt/version definitions, baseline answers and old labels
withheld. Readiness reads project only status/summary. A later read-only provenance
audit is separate from their completed quality judgments. Broker follow-ups point
to exact actual sources and existing criteria; corrected judgments are not new
independent evidence or user whole-answer gold.

Native history preserves **61 hash-current agent review events**: seven initial/
superseded assessments, 36 final individual reviewer assessments and 18 broker
adjudications. Actual reviewer reasons remain separate from broker-selected
witnesses. The latest broker verdict records the assessment under its criteria;
apply subsequent user calibration before reporting it as a current quality grade.

Reviewer A initially overextends event-versus-participant retention into a
mandatory child-centered rewrite, then withdraws it: Ten-year-old children already
retains the age. N074 subsequently changes from uncertainty-only to reject for
a qualified vegetable-source omission, the assumed vegetable-copy requirement,
and V2's separate Food-quantity copy. The vegetable-copy requirement is withdrawn
by the subsequent user calibration below.
Both reviewers change V3 N100 U→R after checking the full shared fat/quarter-pound
trimming conjunction. Reviewer B changes V1 D006 U→R after checking exact
reciprocal copies of the sources' explicit joint enclosure.

For V3 D006, A withdraws a provisional trim/save-state-only rejection and uses
the missing reciprocal joint-qualified material copies. B retains the state-loss
reason. The broker uses the explicit joint-enclosure copy gap, without deciding
the state-only question. A accepts all N063 answers; B keeps Foodstr/Nostr
membership coverage uncertain, and the broker preserves that uncertainty.

Advice/Unless/real-food and vegetable/plant-food readings, mother instruction
versus Dietary advice, dinner/purchase attachment, sauce membership, implicit
sirloin origin, duplicated some, usual vacuum-sealer purpose and dog-recipient
versus explicit food purpose remain open. They do not supply the decisive reject
witnesses above. The reviews expose concrete source and copy failures; reviewer
agreement is not proof of general correctness.

ASv6.100 does not earn promotion: the focused repair remains 0/3, full sauté
preservation loses one trial, and each request adds 2,829 characters. Keep
ASv6.99 as the experimental comparison prompt; this does not change production.
The user-approved controlled minimal-post investigation tests the same individual
additions and beef condition, then adds recipe scope and surrounding steps. The
[ASv6.99 condition source diagnostic](../asv6.99/README.md#condition-source-diagnostic-v1)
completes all 18 fresh medium calls with the comparison prompt unchanged.
Individual and shared formation and pan copying each pass 18/18; beef individual
copying passes 16/18, with both failures in the nearby-steps variant C005.
The scope-plus-steps variant passes 3/3, so these results do not establish a
monotonic post-length effect. The user approves separating frying, mixing and
simmering with fresh reference/all-steps controls. The
[ASv6.99 condition step diagnostic](../asv6.99/README.md#condition-step-diagnostic-v1)
completes all 15 fresh medium first calls without retries or errors. Individual
and separate shared formation and pan copying each pass 15/15; beef individual
copying passes 14/15. Mixing alone reproduces one copying failure (T3/S003),
while fresh reference, frying, simmering and all-steps controls each pass 3/3.
Two additional returned-edge defects remain separate from this bounded metric.
The fresh all-steps result differs from the previous C005 cohort; it establishes
variability, not a prompt improvement or unique cause. The shared counter is
1,592/2,000 with 408 attempts remaining. ASv6.100 is not rerun or promoted.

## User calibration: vegetable placement

The user explicitly rejects requiring **Vegetables a mother tells her ten-year-old
child to eat** beneath **Mothers** and **Ten-year-old children**. Naming those
participants in that vegetable description does not require those placements.
The V2/V3 vegetable-copy failure reason is withdrawn. The prior current-status
claim that N074 fails three of three trials is withdrawn pending reassessment;
this correction does not establish whole-answer accepts.

Saved posts, outputs, frozen prompts and native review history remain evidence
of what was generated and how it was assessed. No teacher calls or prompt changes
are made for this correction. Whether other action/material/tool placements,
the V1 qualified vegetable-source requirement or the V2 Food-quantity advice
placement follow the intended hierarchy needs separate calibration. This decision
does not resolve those broader requirements.
