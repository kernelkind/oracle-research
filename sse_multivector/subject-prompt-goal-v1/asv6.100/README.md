# ASv6.100 Individual action copies under a condition participant

Status: experimental draft; 169 focused offline checks pass; fixed screen pending.
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
