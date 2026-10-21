# ASv6.98 Enclosing recipe example

Status: tested experimental draft; S006 target passes; other clear failures remain;
not adopted.
The user approves targeting S006 after the [ASv6.97 results](../asv6.97/README.md#completed-results).
Production adoption remains a separate decision.

[ASv6.98](ASv6.98.md) appends one ten-entry example to ASv6.97. The instructions,
C1–C7 and POST wrapper remain byte-identical. No rule or production step changes.
C8 uses a different recipe, seasoning and serving capacity from S006:

> My reliable lentil soup recipe serving four people.
> Cumin for seasoning food, to taste.

The recipe introduction and following seasoning instruction support their
relationship in this example. The cumin subject retains the full recipe identity,
ownership, reliability and serving capacity, together with its own purpose and
to-taste amount. The example demonstrates contextual enclosure; it does not turn
adjacent sentences into a general relationship rule. Period-ended prose mirrors
S006 instead of requiring formal heading punctuation.

C8 retains two complete source meanings: the recipe appears under Recipes and
Lentil soup, and the fully qualified cumin appears under both recipe occurrences,
Cumin and Food seasoning. Six direct edges and all compatible copies are checked.
Optional Food, feeding and author headings need not be added. The explanation
distinguishes a broader heading from the complete source wording and shows why
the recipe's separate entry or cumin's placement cannot supply missing details.

The [34 primary clause assignments and five implications](../asv6.96/README.md#actual-instruction-and-example-coverage)
remain intact. C8 adds a focused witness for R01/R02/R04/R16 (whole-post resolution
and complete enclosing relationships), R20–R23 (valid edges and compatible copies)
and R29–R31/R34 (general headings alongside complete specific sources). It adds no
new primary assignments or requirements. C1–C7 still demonstrate every existing
rule; this experiment tests whether the explicit recipe witness improves transfer.

Eight examples contain 149 entries, up from 139. The addition is 2,398 characters
per request, with one prompt and one post in the same single inference step.
Its inference token increase is not established by the character count. Repeated
context at corpus scale is a reason to avoid adoption without demonstrated benefit.

The minimal authored check first fails on ASv6.97 for the missing recipe example;
ASv6.98 passes all 148 focused example, consolidation, revision and attempt-budget
checks through production validation. Static correctness is not model success.
Pinned native source edits (`03bd9e45:sse_multivector/subject-prompt-goal-v1/asv6.98/prompt-edits.json`) and template edits (`03bd9e45:sse_multivector/subject-prompt-goal-v1/asv6.98/edits.json`)
produce separate revision receipts. Source SHA256:
`d16de526a08dc286dba4c28dfbd77bf7185321425e93e904654fc21c99707681`.
The change follows [official guidance on direct instructions and aligned examples](https://developers.openai.com/api/docs/guides/reasoning-best-practices).

## Fixed regression screen

Prepare three six-case native plans under
`experiments/sp-autonomous-v1/recipe-enclosure-v1/T1`, T2 and T3, inherited from
ASv6.97 Food-classification Q1/Q2/Q3 respectively. Keep the complete unchanged
POST/evidence and settings: subscription openai-codex/gpt-6.1-sol/medium,
WebSocket, 1,800-second timeout, no output cap and concurrency one per runner.
Three runners allow three in-flight requests. Native `prepare --from` uses the
new template and `--repeat`; all 18 first calls are intentional fresh trials.
History remains `experiments/sp-autonomous-v1`. Freeze all plans before inference.

Cases remain N063, N074, N096, N100, S006 and D006. Finish all three trials,
regardless of quality. Each `run --max-new-attempts 12` uses the unchanged shared
`target/sp-autonomous-v1/attempt-budget.json`, initially 1,505/2,000. Only existing
provider-transient retries qualify, at most two total attempts per case; no
quality retry, model switch or paid fallback. Subscription calls add no incremental
cash charge; quota is unmeasured. The eight prospective posts remain unused.

The fixed primary target is S006 source retention. The individually qualified
salt, individually qualified pepper and their expressed combination must retain
seasoning-food purpose, to taste and the full enclosing author's never-fail
Spaghetti Bolognaise recipe feeding five people. Reliable or reliably successful
paraphrases remain acceptable; no absent easy-preparation claim is demanded.
Report the three source meanings separately. Only when a complete source forms
does placement assessment count its copies beneath every compatible returned
heading. A never-formed source is source loss, not an additional missing-copy count.

Whole-answer A/R/U remains a separate bounded agent assessment using the
[corrected ASv6.97 criteria](../asv6.97/README.md#fixed-regression-test): Food is
not an exclusive-use class, optional broader headings are unnecessary, and SP
allows topics about parents through actions or relationships. Keep unresolved
readings separate from decisive source/edge/copy defects. Review unchanged full
POST and parsed answers through native `show`; preserve reviewer reasons and
disagreements individually in native `review`, followed by broker adjudication.
No human whole-answer labels or independent agreement-rate claim is implied.

Historical target audit through native `show` finds S006 source retention 0/3
in ASv6.96 E03/E04/E01 as well as ASv6.97 Q1/Q2/Q3. The older whole-answer
S006 labels A/R/A remain historical labels; they did not establish this target.
The omission is not a newly introduced ASv6.97 regression. Saved baselines are
historical controls, not a contemporaneous causal comparison. Repeatedly inspected
development posts do not establish unseen generalization or population accuracy.
A 3/3 target pass would support a bounded repair signal; remaining original-post
defects still prevent a reliable SP-fix claim.

## Completed results

All 18 planned medium calls complete with valid first answers, zero failures,
invalid receipts, retries, reuse or unrun cases. The persistent counter moves
from 1,505 to 1,523/2,000, leaving 477 attempts. Native saved SDK requests match
the exact frozen prompt, model, effort and schema; outputs/receipts validate.
Source and template remain at pre-inference checkpoint `8257bed6`. All 148
focused offline checks pass; static validation does not imply teacher correctness.

**S006 passes source retention and placement in all three trials.** Each answer
forms complete salt at 1.1.1, pepper at 1.1.2 and their combination at 1.1.1.1,
retaining food-seasoning purpose, to taste and the full recipe relationship.
Never-failing, reliable and never-fail are the accepted reliability paraphrases;
serving/feeding five people retains the capacity. No absent easy claim is added.

Each trial copies salt beneath both recipe occurrences, Salt and Food seasoning;
pepper beneath both recipe occurrences, Pepper and Food seasoning; and the
combination beneath every returned compatible component occurrence. No clear
whole-answer defect is found within this bounded assessment. The recipe's
separate entry alone is no longer being used to supply omitted seasoning details.
The 3/3 result contrasts with the same-criterion 0/3 saved ASv6.97 target results;
it is a concrete development-case repair signal, not causal proof or unseen accuracy.

| Case | T1 | T2 | T3 | Remaining finding |
| --- | --- | --- | --- | --- |
| N063 | R | U | R | All fifteen ingredient roles and full-list meanings retained; T1 food-sharing/Cooking copies and T3 Cooking copies missing. T2 platform membership remains open. |
| N074 | R | R | R | T1 mother instruction missing Eating advice; T2 individual quantity/plant advice missing Food; T3 individual quantity advice missing Real food. |
| N096 | R | R | R | T1 full list lacks ingredient copies; T2 full list never forms and packet instructions lack spaghetti copies; T3 individual sautés lack oil copies. |
| N100 | R | R | R | T1 component-portion sources lack reciprocal material copies; T2 loses eventual-use qualification; T3 lacks complete individual tissue/scrap trimming actions. |
| S006 | A | A | A | All three complete seasoning sources and required copies retained. |
| D006 | R | R | R | T1/T3 complete component actions lack reciprocal material copies; T2 individual actions omit measured-group membership. |

Whole-answer totals are 3 bounded accepts, 14 rejects and 1 uncertain. The
original-post subset is 0/11/1 among twelve; the six diagnostics are 3/3/0.
ASv6.97's historical whole-answer labels remain 2/15/1. Different returned
headings and assessment history make that total unsuitable as a causal score
comparison. Its accepted N063 Q1/Q3 answers have no Cooking heading; ASv6.98
T1/T3 return one and must therefore retain its compatible descendants. There
is no demand to add an optional Cooking heading. Original-post failures still
prevent a reliable whole-prompt claim. The eight prospective posts remain unused.

Concrete native `show` witnesses distinguish three remaining defects:

- T3 N096 forms the individual onion sauté at 1.1.1.1.1.1, celery at
  1.1.1.1.2.1 and carrot at 1.1.1.1.3.1. Olive oil 1.1.1.1.11 receives their
  combined sauté, but none of the three individual actions. Combination retention
  does not replace individual-source copies. The pan heading 1.1.1.2 specifically
  names sauce preparation; source strings without that purpose need a separate
  compatibility decision. That question stays open with sauce interpretations,
  without changing the independently supported oil-copy rejection.
- T2 N100 parent 16.1.1 says the author's eventual use of the new sealer bought
  on the Amazon deal; child 16.1.1.1 says love after using it and omits eventual
  qualification. The same omission occurs under 3.2.1 and 17.1.1. Context cannot
  restore a parent restriction missing from the child wording.
- T2 D006 individual tissue action 2.1.2 and scrap action 3.1.2 omit their
  membership in the shared approximate-quarter-pound portion. Their child
  describes the combined portion's trimming, not the complete individual action.
  This is source loss, without also counting copies of never-formed targets;
  no individual quarter-pound weight is required.

## Review corrections and limits

Two answer reviewers receive only unchanged complete POST and parsed subjects,
without prompt, baseline or old labels. Their actual reasons are recorded
separately in native `review`. Initial disagreements expose individual-versus-
combined source mistakes: reviewer A changes N074 T2/T3 A→R and D006 T2 U→R;
reviewer B changes D006 T1 A→R after checking the explicit shared-portion
relationship. Reviewer agreement after that discussion is not independent
accuracy evidence. Native history preserves eight initial/superseded events,
36 final reviewer events and 19 broker adjudications (including the pan-purpose
clarification): 63 hash-current events.
Scoring uses the latest broker verdict per case, not all hash-current events.

Food-preservation compatibility in N100 stays open: a usual device purpose and
post domain alone do not establish every instance's food-use restriction, while
a general topic/device-class reading is distinct. Initial reviewer claims are
preserved; final N100 rejections use clearer component/action/qualifier witnesses.
N074 readings, Foodstr membership, dinner/purchase attachments, sauce membership,
implicit sirloin origin and the duplicated some remain separate uncertainties.
No Food-other-use exclusion or Seasonings→bare-Salt rejection is used here.
Agent calibration does not create human whole-answer gold.

The useful next target is N096's missing individual sauté copies under
the oil heading in T3; the narrow target already passes T1/T2 (2/3). Preserve
the recipe-retention example and demonstrate
that each complete individual action, as well as the shared action, retains every
compatible participant/tool occurrence. This is a proposal for a subsequent
prompt iteration, not a new production pass. The user approves this target;
[ASv6.99](../asv6.99/README.md) extends C1 with a shared knife while preserving C8.
Its 18-answer medium screen completes at 3 bounded accepts/11 rejects/4 uncertain.
N096's individual sauté/oil-copy target passes 3/3 and S006's recipe-retention
target remains 3/3; whole-answer failures still prevent adoption.
