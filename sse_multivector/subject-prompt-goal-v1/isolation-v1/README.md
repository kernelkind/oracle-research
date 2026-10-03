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
