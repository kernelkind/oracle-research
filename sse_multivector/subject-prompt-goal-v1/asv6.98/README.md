# ASv6.98 Enclosing recipe example

Status: experimental draft; offline checks pass; fixed regression screen pending.
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
Pinned native [source edits](prompt-edits.json) and [template edits](edits.json)
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
