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

## Second diagnostic results

All 138 new answers completed on their first attempt, with no runner failures,
retries or reuse. Every answer has exactly one current native agent review:
132 bounded accepts and six source rejections. The diagnostic phase closes at
676 of 2,000 attempts. Native show validates receipts and preserved preparation;
input/output-bound review hashes and exact interventions were checked. The
56 offline prompt/workflow checks pass. ASv6.76 screening subsequently begins
from this counter; the diagnostic prompts are not adopted SP replacements.

E2's forty-eight heading-pair decisions match every positive/negative witness,
including the previously unanswered first-use/newness/book-attribution cases.
P2's twenty-four collections match every supplied parent occurrence, including
all repeated advice and joint-trimming parents; incompatible Dog food
collections remain empty. These results establish competence on these bounded
operations with the full SP prompt present. They do not establish reliable
joint discovery, relation selection and hierarchy rendering.

| Flat source case | R1, with C1 | R2, without C1 | Observation |
| --- | --- | --- | --- |
| S002, recipe title plus original salt line | A/A/A | A/A/A | Full named-recipe/to-taste relationship retained. |
| S006, same title plus explicit food purpose | R/R/R | R/R/R | Every complete pair loses its named-recipe relationship. Removing C1 does not repair it. |
| B001, S006 title ending with a colon | A/A/A | A/A/A | Full recipe and culinary/to-taste relationship retained; equivalent complete-action wording counts. |
| B002/B004, explicit recipe reference | A/A/A each | A/A/A each | Full recipe relationship and title qualifications retained. |
| B003, separately marked seasoning | A/A/A | A/A/A | No recipe association is added. |
| B005, counted action under recipe heading | A/R/A | A/R/A | Trial 2 in each version drops serving-five/reliability qualifiers from the complete action. |
| B006, same action with explicit recipe purpose | A/A/A | A/A/A | Complete counted action and full recipe qualifications retained. |
| B007, counted repair action under heading | A/A/A | R/A/A | R2 trial 1 drops the blue-boiler workshop-repair purpose from the tube-fitting action. Alternative boiler-fitting readings remain outside the focal acceptance. |
| B008, repair action with explicit purpose | A/A/A | A/A/A | Complete counted tube-fitting action retains the named repair purpose. |
| B009/B010, book advice as heading/in-clause | A/A/A each | A/A/A each | Joint advice retains both gates, quiet entry, book and author. |

The source interventions show a reproducible enclosing-relationship loss when
the local line also states a complete food purpose. A colon or explicit
reference changes that behavior. They do not reveal hidden reasoning or prove
the unique internal cause. C1 is not the demonstrated cause: its removal
leaves S006 unchanged and introduces a repair-purpose omission in one other
case. Source qualifier retention can also fail with a colon, as B005 shows.
The candidate [ASv6.76](../asv6.76/README.md) therefore clarifies carrying
supported enclosing and local meanings together, rather than deleting C1 or
changing the output contract. All seven worked examples remain unchanged.

The evaluation distinction is also supported as a research method by
[FollowBench](https://aclanthology.org/2024.acl-long.257/), which incrementally
adds constraints, and [ComplexBench](https://arxiv.org/abs/2407.03978), which
evaluates how constraints compose and depend on one another. These older
benchmarks do not measure this exact Sol model or explain its particular
answers; the repository's controlled inputs provide that evidence.
# Full-post joint-action controls, frozen before generation

The first two prompt screens both omit N100's complete quantified joint trim
in all three original-post trials. The first completed ASv6.78 original answer
also omits it. The short shared trimming sentence is retained in all D005
answers of ASv6.76/77. This contrast warrants a narrowly targeted integration
check; it does not establish an internal attention or reasoning cause.

SP-Isolation-R3 and R4 append the exact unchanged R1 flat-response operation to
the complete ASv6.76 and ASv6.78 templates respectively. Keep the source rules,
examples, original N100 input, evidence and medium settings. Use three trials
per diagnostic, with native same-trial ASv6.76 inputs and saved outputs. This
is six fresh answers, testing complete source retention while removing only
the hierarchy response obligation. No production multi-pass change is proposed.

T001 deletes only N100's independent vacuum-sealer paragraph, retaining every
other source byte, including the purchase/cutting context, shared trim,
myoglobin/chicken clause, hashtags and image URL. Use the unchanged ASv6.76
full SP prompt for three fresh medium trials. This tests whether that exact
additional paragraph changes retention of the unchanged focal joint action;
it does not separate input length from topic/constraint interference.

Before any of these nine generations, freeze the focal criterion: at least one
subject heading must retain the full shared trim of about 3 lb fat for tallow
and about a quarter pound of connective tissue and scrap meat for the dog from
the sirloin strip subprimal. Counts attach to the fat and the combined tissue/
scraps respectively. Check equivalent complete wording throughout the array.
Partial actions, contexts and other headings cannot replace the combination.
Flat diagnostics are graded only for bounded source retention, not hierarchy
placements. T001 additionally preserves the ordinary scope and compatible
source-parent placement criteria. Do not certify unrelated clauses as gold.

Use only native prepare/run/show/review, subscription Sol 6.1 medium, unchanged
WebSocket/1,800-second/no-output-cap settings and persistent history/budget.
The next nine first attempts after ASv6.78 would reach 793, still below 2,000.
Count every failure, retry only explicit transient provider failures once and
retain unknown failures. At most six requests are active across all runners;
these diagnostics wait for capacity rather than exceeding the screen's bound.
Review every answer and preserve all receipts; no quality reruns or early stop.

## Matched hierarchy control, frozen before generation

The complete original N100 joint trim appears in all three ASv6.76 flat R3
answers. Removing the sealer paragraph leaves it absent in all three T001 full
hierarchies. R3 also adds an explicit source-retention reminder, so this alone
does not isolate hierarchy obligation from that wording/position change.

SP-Isolation-R5 changes only R3's response-mode sentences back to hierarchy
construction, repeated compatible branches and section-style numbering. Its
opening enumeration sentence, complete-retention sentence, JSON fields, full
ASv6.76 prompt and original post remain identical. Freeze three fresh medium
N100 trials with same-trial ASv6.76 native inputs/baselines before generation.
Reuse the preceding focal joint-action criterion, recording scope/placement
failures separately; source presence is not overall acceptance. All attempts
count, every answer is reviewed and no quality retry is allowed. This brings
the additional control total to twelve calls and first-attempt completion to
796 after ASv6.78. The same subscription/native/history/timeouts and six-active
bound apply. This is a finite diagnostic, not a production prompt or extra pass.

## Completed full-post controls

All twelve R3/R4/T001/R5 first attempts completed with valid native receipts,
without errors, retries or reuse; the persistent counter reached 796. All have
current output-bound native agent reviews. R3 and R4 each retain the complete
original N100 joint trim in 3/3 flat answers. T001 retains it in 0/3 ordinary
hierarchies after removing only the independent sealer paragraph. Matched R5
retains it in 3/3 hierarchies: bounded reviews reject trial 1 for missing copies
below partial trimming actions 2.1.2.1/2.1.2.2 and accept trials 2/3.

The flat/hierarchy contrast alone therefore cannot identify hierarchy obligation
as the cause: explicit late source-retention wording also changes the result.
Removing the sealer paragraph does not repair the omission. Source retention
and compatible placement can fail separately. These controlled behavioral
findings do not reveal a unique internal attention or reasoning mechanism.

The ASv6.78 D006 trial-3 five-row answer also has normal raw completion:
`status=succeeded`, `raw_stop_reason=completed`, `stop_reason=stop`, one HTTP
attempt, no provider/validation error, and no requested output cap. The request
records the exact Sol model and medium effort. Its missing participants are
therefore a semantic coverage failure in a normally completed answer, not a
reported transport failure or output-limit termination. This witness does not
rule out every possible provider problem in other calls.

ASv6.79 clarifies that each expressed combination gets its own complete heading;
ASv6.80 moves the unchanged enumeration paragraph nearer the post. Their twelve
original answers each complete on first attempts, taking the counter to 820.
ASv6.79 retains N100's complete trim in 1/3; ASv6.80 in 0/3. Bounded original
reviews are 7 accept/5 reject and 5 accept/6 reject/1 uncertain respectively. Neither is a
reliable fix. The complete trial tables and concrete witnesses are maintained
in their candidate READMEs. All seven examples and the ordinary schema remain
unchanged in both.

The next comparison replaces the existing combination-retention sentence with
the complete-source wording used in the successful R5 control. ASv6.81 places
that paragraph at the end as ASv6.80 does; ASv6.82 keeps its ASv6.76 position.
This isolates the same wording at two positions without a duplicated footer.
Each gets twelve original-post answers with frozen unchanged bounded criteria,
three medium trials, native same-trial baselines, and every answer reviewed.
The 24 first attempts would reach 844. These remain development inputs.

Eight fresh posts and prospective criteria are frozen in
[validation-v1.md](validation-v1.md). Select and freeze the exact candidate from
development evidence before generating any validation answers. Production SP
remains one pass and no candidate is adopted.

### Selection and regression rule, before ASv6.81/82 reviews

Choose among ASv6.76–82 using their complete three-trial original-post screens:
fewest confirmed bounded rejections, then fewest uncertainties, then most N100
complete-joint retention, then the smaller source change from ASv6.76. This is
a development selection rule, not statistical proof of model ranking. Do not
change frozen criteria to select a winner. Candidate answers to ASv6.81/82
have not yet been semantically inspected at this freeze.

Before fresh validation, run the exact selected candidate on the eight frozen
minimized cases and I011/I012 repair cases in three trials: thirty first
attempts, inheriting saved same-trial inputs/settings/evidence. Judge existing
criteria, review every result and preserve all errors/uncertainties. The
original examples remain audited through the production subjects adapter.
If this screen exposes a regression requiring another edit, freeze and finish
that edit's development screen before candidate selection for validation;
these eight fresh posts remain ungenerated meanwhile.

## Completed wording comparison and next fixed screen

ASv6.81 completes with 8/12 bounded accepts and four confirmed failures;
ASv6.82 with 4 accepts, 7 failures and one uncertainty. All 24 answers have
valid first receipts and current native reviews, with no errors, retries or
reuse; the counter is 844. Under the frozen selection rule ASv6.81 wins among
ASv6.76–82. It names N100's joined trim in 3/3, preserving its full enclosing
sirloin source in 2/3. N063/N074 pass the bounded checks in 3/3 each; all N096
answers still fail, two solely through concrete compatible placement omissions.
This is development improvement, not reliable full-SP completion.

Before fresh validation, ASv6.83 clarifies only the existing collection sentence:
complete actions and combinations involving a heading's subject belong in its
collection when their own wording passes the parent check. The ASv6.81 N096
trial-2 missing onion/celery/carrot/oil placements are the saved production-path
failing case. C1's mixing action and C6's full cable combination already
correctly demonstrate that existing implication; examples remain unchanged.

Freeze three full-original trials and the planned three eight-case minimized
plus two-case repair trials for ASv6.83: 42 first attempts. Inherit same-trial
ASv6.81 originals, ASv6.76 minimized cases and ASv6.75 repair inputs/settings,
with all existing criteria unchanged. Review every answer, keep errors and
uncertainties, no quality reruns/early stopping. At most six requests remain
active. First-attempt completion reaches 886. Compare originals with ASv6.81;
keep the same selection ordering, extending eligibility to the exact ASv6.83
only after its entire screen completes. Validation remains ungenerated.

Also freeze ASv6.81 on the same eight minimized and two repair cases in three
trials: thirty first attempts, following the 42-answer screen. This gives the
provisional best candidate its required regression checks and a matched input
control for ASv6.83's collection edit. Keep all exact inputs and criteria, no
quality reruns or stopping. Completing both fixed screens reaches 916 before
the planned 48 fresh validation answers. Do not treat the additional baseline
as a new candidate or use validation results to revise the selected prompt.
