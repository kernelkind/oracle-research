# ASv6.99 Individual action copies under a shared tool

Status: experimental draft; 158 focused offline checks pass; fixed screen pending.
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
