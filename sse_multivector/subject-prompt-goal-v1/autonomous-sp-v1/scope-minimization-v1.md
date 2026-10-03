# ASv6.74 salt/dog scope minimization

Status: authorized, criteria fixed before generation; not yet run. The user
approved minimizing the original failures after the ASv6.74 comparison.
ASv6.74 stays fixed, as does production ASv6.48. Prompt revision, MP and
adoption remain outside this task.

## Question and source

The saved original ASv6.74 answers return Seasonings → Salt in three of five
N096 trials and a food/feeding parent → material merely "for the dog" in all
five N100 trials. Earlier short dog controls never exposed a food/feeding
parent. Earlier salt controls use Sea salt and soup wording rather than the
original Salt and pepper to taste line. These contrasts do not identify why
the original answers fail.

The [sixteen authored cases](scope-minimization-cases-v1.json) deliberately
select and edit N096/N100 passages. They are human-readable experimental inputs,
not mechanically gathered original-post artifacts. Original wording comes from
native `show --case N096` in `as74-original-medium-r2` and `show --case N100` in
`as74-original-medium-r3`. Line-ending/trailing-space normalization and the
purpose/Sea salt edits are deliberate. Source provenance and rubrics remain
review-only; only each case's text enters POST. Interpret each edited post on
its own: deleted source clauses cannot supply its missing referents or meanings.

Fresh full-post controls use native `prepare --from` with only N096/N100 from
`as74-original-medium-r2`; native preparation preserves complete original text
and evidence without assembling a second source corpus.

| Cases | Comparison |
| --- | --- |
| S001/S002 | Salt and pepper to taste alone versus the same line under the original recipe title. |
| S002/S003 | Isolated salt/pepper line versus the complete original ingredient list, with the same title. |
| S002/S004 | Same title and line, without versus with original final hashtags. |
| S001/S005, S002/S006 | Original wording versus explicit food-seasoning purpose, without and with the title. |
| S001/S007, S002/S008 | Salt versus Sea salt, without and with the title. |
| D001/D002, D003/D004 | Same trimming/recipient statement, without versus with the source myoglobin-to-dog-food clause. |
| D001/D003, D002/D004 | Recipient wording versus explicit feeding purpose, without and with the dog-food clause. |
| D001/D005 | Trimmed dog material alone versus the original parallel fat-for-tallow clause. |
| D005/D006/D007 | Original trimming sentence, plus dog-food clause, plus the complete original chicken clause. |
| D005/D008 | Original trimming sentence, without versus with original hashtags. |

This is a fixed contrast set, not a binary-search algorithm or a claim to find
the globally shortest failing post. A successful reduction retains the same
concrete failing relationship in a shorter post; its repeatability and parent
exposure must be reported. Original controls test whether that relationship
still appears under the same frozen prompt and settings.

## Pre-generation criteria

Use the existing heading-alone scope rule and numbered-copy requirement.
Judge meaning rather than exact wording or a required tree shape.

1. **Salt scope:** inspect each returned occurrence of the focal salt topic
   and its salt/pepper combination. Unrestricted Salt or Sea salt cannot inherit
   a food, ingredient or seasoning restriction from context or ancestors.
   De-icing supplies a counterexample. A heading that states food-seasoning or
   recipe-ingredient purpose may belong beneath the corresponding parent.
   Retain salt, pepper, their expressed combination and supported to-taste/role
   meaning; do not require a named optional derived heading.
2. **Dog scope:** inspect each returned occurrence of the connective-tissue/
   scrap-meat material, its combined approximate quarter-pound amount, trimming
   and recipient. Material merely "for the dog" cannot inherit feeding/food
   purpose: material for a chew toy fits that heading. Explicit feeding forms
   retain feeding purpose. In recipient-only forms feeding may be reasonably
   implied; a qualified interpretation is permitted, not mandatory. The separate
   myoglobin clause does not supply a missing restriction inside another heading.
3. **Source and placement:** retain the focal counts, modifiers, participants,
   relationships and complete combinations supported by the edited post. Inspect
   every numbered occurrence of compatible returned source-component parents,
   including repeated copies. Descendants count. Check alternative complete
   subject strings before declaring a source omission; context alone is
   insufficient. Derived broader-heading closure remains excluded. Ancillary
   recipe/fat/myoglobin/chicken subjects are boundedly inspected for obvious
   changes, not certified as full-SP gold. The ambiguous chicken reading and
   ingredient-group memberships remain outside confirmed rejection counts.
4. **Exposure:** separately record food/seasoning/feeding parents actually
   returned, the focal child meaning and every failing numbered edge. An absent
   parent is no scope error but provides zero observations of its relationship;
   do not count it as a successful edge test. An action itself concerning dog
   feeding is a different subject from material merely for the dog.

Record current output-bound native agent reviews for every answer. Reject only
with a concrete focal source omission, placement omission or heading-alone
counterexample. Preserve material semantic uncertainty. Acceptance concerns
these focal checks, not all SP rules, optional hierarchy shapes or user labels.
For fresh full originals, also retain the earlier bounded original-post review
criteria and separate a focal scope failure from other confirmed errors.

Report every trial and case, exposure counts and the particular failing edges.
Do not equate a wording change with improvement, or infer causation from a
single stochastic pair. These previously examined posts and authored contrasts
are development evidence; none is unseen validation or an example revision.

## Execution and scale

Use the [native subjects spec](scope-minimization-spec-v1.json) for trial 1;
trials 2 and 3 inherit cases/settings with `--from` and `--repeat`. Prepare
three full-post control experiments with N096/N100 only and `--repeat`.
All use subscription `openai-codex`, exact `gpt-6.1-sol`, medium, WebSocket,
1,800-second timeout, no output-token cap and no paid fallback. Diagnostic
concurrency is four per trial; full-post concurrency is one per trial, changed
from the earlier four solely to bound concurrent work. The six independent
native experiments together permit at most fifteen in-flight requests. Each
native run owns scheduling; no separate waves or execution scripts are added.

Plan 48 diagnostic answers and six full-original answers: 54 fresh calls, with
no quality-based early stopping or prompt/criteria changes. Every run shares
`target/sp-autonomous-v1/history` and persistent
`target/sp-autonomous-v1/attempt-budget.json`, starting at 302 of 1,000. Bound
each diagnostic run to 32 new attempts and each control run to four, including
eligible provider-only retries, at most two attempts per case. Failures remain
visible and count. All-first-attempt success would reach 356; never reset or
refund the counter.

Native directories under the ignored campaign experiment root are
`as74-scope-min-medium-r1` through `r3` and `as74-scope-original-medium-r1`
through `r3`. Verify exact rendering, inputs, settings, receipts and review
bindings after completion. Commit these criteria and inputs before inference.

This finite investigation adds no production component, grader or inference
stage. SP still makes one call per post; fixed prompt and repeated-branch
output costs are unchanged. The shorter posts reduce this experiment's variable
input and most output work. Subscription incremental cash is zero, quota use
is unmeasured and catalog estimates are not bills. The monetary ledger was
inspected before launch; no paid commitment is introduced.
