# SP failure isolation and prompt correction

Status: authorized, in progress. On 2026-10-02 the user instructed us to
isolate why SP fails, fix the prompt and work for five hours with a 2,000-call
cap. Start: 2026-10-03 02:38:46 UTC; deadline: 07:38:46 UTC. Preserve the exact
subscription `gpt-6.1-sol` low/medium route, SP JSON schema, source meanings,
all 34 instruction clauses and five tracked implications. MP, production
adoption, paid fallback and pushes are outside scope.

The persistent campaign counter starts at 430. Its ceiling increases from
1,000 to 2,000 without resetting/refunding use, conservatively leaving 1,570
new attempts. Failed and interrupted attempts count; only native provider
failures permit a second total attempt. Use native `experiment.py` throughout,
the existing campaign history and budget, and ignored native experiment output.
No production pass, grader, repair stage or component is introduced.

## Questions fixed before the first calls

ASv6.75 improves food qualification but still omits complete source subjects,
reverses group/member scope and misses numbered placements. Its correct C1/C6/C7
outputs do not establish reliable transfer. Avoid another wording sweep without
identifying which operation an intervention changes.

1. Does complete-subject retention improve when hierarchy generation is removed,
   while the entire ASv6.75 specification and examples remain available?
2. Does the model correctly judge supplied heading pairs, including the exact
   combined-parent/single-member pattern, in isolation?
3. Can it collect supplied complete source subjects under supplied compatible
   parents, including repeated occurrences, without discovering subjects or
   choosing hierarchy structure?

These interventions test behavior under changed demands. They cannot reveal
hidden internal reasoning or prove a model capability ceiling. Passing isolated
checks alongside failing SP supports an interaction problem; failing one isolates
a concrete operation needing correction. Prompt length/context also differs in
the standalone pair/placement tests; preserve that limit when interpreting them.

## First diagnostic comparison

All prompts are explicitly diagnostic versions, not replacement SP candidates.
Three independent medium trials per case, frozen before calls:

| Diagnostic | Cases | Fresh answers | Contract |
| --- | --- | --- | --- |
| SP-Isolation-R1 | Native inherited N063/N074/N096/N100; S002/S004/S006/D004/D005/D006/D007/D008 | 36 | ASv6.75 plus a final diagnostic-mode instruction: flat specific subjects only, still number/context/subject and production subjects validation. |
| SP-Isolation-E1 | Sixteen authored heading pairs | 48 | Exact existing heading-alone restriction rule; valid/reason response. Eight positive and eight negative witnesses span groups, purpose, counts, first use, newness and attribution. |
| SP-Isolation-P1 | Eight authored fixed subject/parent collections | 24 | Exact existing scope and every-parent collection rules; return supplied subject IDs per parent number. Four families, each with single versus repeated parent occurrences. |

Plan 108 fresh answers; all first-attempt success reaches 538 of 2,000.
Original-retention concurrency is one per trial; minimized retention two;
pair judgment two; placement one. Twelve independent native runners permit
at most eighteen simultaneous requests. Each native runner owns scheduling.
Timeout is 1,800 seconds, WebSocket, no output cap or paid fallback. Native
preparation preserves complete inherited inputs/evidence and saved ASv6.75
outputs without rerunning them. Author-defined pair/placement cases are source
fixtures with agent rubrics, not gathered original answers or user labels.

## Frozen assessment

Use current output-bound native agent reviews. Preserve all failures and
uncertainties; do not select trials or rerun poor answers. Judge equivalent
wording by meaning. Source evidence or a correct copy elsewhere cannot restore
a missing heading qualifier or placement. Do not introduce exact-phrase or
optional-tree requirements. Derived broader-heading closure, uncertain ingredient
membership, C2 help/appreciation and N063's alternative group representation
remain outside confirmed rejection counts.

Retention reviews focus on the expressed salt/pepper/recipe relationships,
the full counted sautéing action with named recipe purpose, the quantified
joint fat/tissue trimming, explicit dog-feeding material, named-book attributed
three-part advice, and individual source participants. Inspect complete original
posts under the earlier bounded source criteria. Separate source retention from
the discarded hierarchy obligations; flat diagnostic output is not an SP pass.

Pair judgments must agree with the supplied agent-defined semantic witness,
and their public reason must support it. Reject a missing required parent
restriction even when the current post could have supplied it. Actions can
concern an object topic; this is a subject index, not physical subtype testing.

Placement reviews compare complete ID collections at every supplied parent
number. Order is immaterial. Do not add source meanings, omit a parent occurrence
or infer qualification from a parent. Empty collections for incompatible dog-food
parents are required. These cases bound placement to supplied meanings; they do
not test discovery or full hierarchy rendering.

## Iteration and validation

Use diagnostic findings to choose a minimal, versioned SP revision with native
revision receipts. First retain a minimal production-path failing case, audit
each changed worked example against its rules and every numbered parent, then
test the revision on the failing contrast. Preserve all clause/implication
demonstrations. Expand to independent full-original repeats, repair cases and
fresh cross-topic validation only when the results justify it. Cases used to
choose a revision become development evidence; hold later validation inputs
fixed before generation and report their status honestly.

Keep changes to examples/instructions separate in controlled comparisons.
Record direct numbered witnesses, source/scope/placement dimensions, actual
parent exposure, runner errors, model/settings and current review bindings.
Commit meaningful source/documentation checkpoints. Do not adopt a candidate
merely because a narrower diagnostic improves.

The five-hour interval is a work limit, not a request to consume the call cap.
Inspect the lifetime monetary ledger before inference. Subscription incremental cash
is zero; quota and provider billing remain unmeasured. Native usage reports are
retained without manual token/cost aggregation. Production SP remains one model
call per post; diagnostic decomposition is a finite experiment, not a proposed
corpus-wide workflow.

Official guidance used: [prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering)
and [evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices).
These support explicit instructions, correct examples and scoped evaluation;
they do not establish the cause of this repository's observed failures.

## First diagnostic results

All 108 attempts completed; 61 produced valid answers and 47 failed in the
runner. The persistent counter is 538 of 2,000. There were no retries, reused
answers, malformed outputs or unrun cases. Every valid answer has a current
native agent review. The failed cases have no prompt-quality verdict.

Thirty completed pair judgments (E001–E010, three trials each) match their
frozen witnesses. Twelve completed fixed collections (P001–P004, three trials
each) match every supplied parent occurrence. The combined-parent/member
direction, purpose qualifications, counted object/action restrictions and
repeated collections work in these bounded tasks. E011–E016 and P005–P008
received no answers; first-use, newness, attribution and the other collection
families remain unobserved in this first phase.

Flat retention has nineteen valid answers: thirteen bounded accepts, five
confirmed source omissions and one uncertainty. These are source checks,
not SP hierarchy judgments. N063's fifteen ingredients and their complete
dish-qualified combination survive in all three answers. The sole completed
N074 answer retains the named-book three-part advice. The sole completed
N100 answer retains the quantified joint trimming at subject 20, unlike its
saved ASv6.75 answer; whether “Finally using” fully conveys first use remains
open. One sample does not establish a reliable repair.

The sole completed N096 answer still omits the named recipe purpose from its
complete counted sautéing subject 29. S006 omits the salt/pepper relationship
with the named recipe in all three flat trials, while S002 retains it in all
three. Those posts differ only by adding “for seasoning food” to the salt
line. S004 trial 3 also drops serving-five/reliability qualifications from the
complete pair. Separate qualified recipe headings cannot repair the missing
complete subject. The failure therefore persists without hierarchy generation.

The runner failures occurred in a burst with zero response frames, WebSocket
closure 1006 and native failure kind `unknown`. The credential proxy remained
running; its journal reports upstream HTTP 403 responses without a detailed
provider reason. Later requests succeeded through the same selected account
and route without intervention. Quota, rate limiting and authorization causes
are not established. No account was changed and the unknown failures were not
retried. Preserve this infrastructure loss separately from the model findings.

## Second diagnostic comparison, frozen before generation

The first phase supports two specific questions, rather than a general model
ceiling claim. Does an explicit food-purpose phrase displace the enclosing
recipe association? Does relationship competence persist with the full SP
instructions and seven worked examples present?

The ten authored `binding-cases-v1.json` posts vary enclosing headings versus
explicit in-clause reference, with a separately-marked recipe control, counted
actions, a repair topic and book-attributed advice. These edited posts are new
development diagnostics, not untouched validation. Require the complete focal
combination to retain its enclosing named subject, quantities, purpose and
attribution when supported; the “Separately” control must not acquire a recipe
relationship. Judge equivalent wording, not an exact phrase. Individual source
participants must remain. Hierarchy checks are excluded in the flat tasks.

Compare R1 with SP-Isolation-R2, which deletes only C1 from R1 while preserving
the other examples, instructions, schema and final flat-mode instruction.
Removing C1 is a diagnostic intervention, not a proposed production prompt;
the production candidate must retain every rule demonstration. Three trials
of ten posts per version require sixty fresh answers. This tests C1's effect
as a whole, not which sentence inside C1 causes a difference.

SP-Isolation-E2 and P2 preserve the complete ASv6.75 prompt and append the
unchanged isolated operation from E1/P1 in place of the POST input. Their
diagnostic output instructions explicitly override hierarchy generation.
Repeat all sixteen pair cases and eight collection cases in three trials:
seventy-two new answers. Comparing the completed E1/P1 cases isolates adding
the full SP context; the previously unanswered cases have no earlier outcome
to compare. These changed prompts are new interventions, not retries of the
unknown runner failures.

Before any R2 generation, add six native inherited S002/S006 checks (three
trials per case) under R2. Their completed R1 answers supply the direct contrast
for the original failing period/title wording; the ten edited binding posts
alone would not test that failure. This amendment does not alter the running
R1/E2/P2 plans or their criteria.

Plan 138 calls; all-first-attempt success reaches 676. Keep medium, subscription
Sol 6.1, WebSocket, 1,800 seconds and no output cap. Native runners own their
scheduling. Bound aggregate concurrency to six during this phase and record
any failures unchanged. A lower burst size is an operational choice, not a
claim that concurrency caused the upstream rejection. Commit this plan and
authored sources before inference.
