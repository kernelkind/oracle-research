# Fresh instruction-consolidation comparison

Status: fresh comparison complete; clear failures remain; neither prompt is a
reliable correction and ASv6.96 is not adopted.

The user authorized applying current prompting and evaluation guidance after
the audit found repeated/scattered instructions and weak saved, unblinded
comparisons. ASv6.96 consolidates ASv6.95 instructions before its seven unchanged
examples. The predicted effect is improved source retention, scope and complete
collection. No hidden procedure or root cause is inferred from prompt length.

This follows [direct instructions and aligned examples](https://developers.openai.com/api/docs/guides/reasoning-best-practices),
[organized prompt structure](https://developers.openai.com/api/docs/guides/prompt-engineering)
and [task-specific, controlled and calibrated evaluation](https://developers.openai.com/api/docs/guides/evaluation-best-practices).
Current GPT-6 family suggestions are starting points to evaluate on the chosen
model and workload, not certification of an SP prompt. The single-user-message
delivery remains an untested harness choice; role changes are not combined with
this text-only revision.

## Frozen design

Collect four completed ASv6.94 trial-1 family experiments (original/min/late/guard)
through native `experiment.py collect` into ignored
`target/sp-autonomous-v1/consolidation-inputs-v1`. This preserves eleven complete
posts with receipt provenance. The subjects input adapter reads only their post
texts; saved subject arrays are not teacher input. Original text is unchanged;
new native origin evidence is matched between the two fresh arms, not asserted
byte-identical to historical evidence.

Prepare six native eleven-case plans: three independent trials each of ASv6.95
and ASv6.96. Every plan uses `--repeat`, subscription
openai-codex/gpt-6.1-sol/medium, WebSocket, 1,800-second timeout, no output cap,
and concurrency one. Start the six native runners together, giving at most six
requests overall without external waves or new execution code. Source-case order
is shared. Random assignment of version/trial to runner slots is frozen below;
this is not paired provider seeds or randomized case order.

| Native slot | Prompt | Trial |
| --- | --- | --- |
| E01 | ASv6.96 | 3 |
| E02 | ASv6.95 | 1 |
| E03 | ASv6.96 | 1 |
| E04 | ASv6.96 | 2 |
| E05 | ASv6.95 | 2 |
| E06 | ASv6.95 | 3 |

There are 66 new first attempts, predicting 1,487/2,000 total after the existing
1,421. Each native runner has a maximum 22 new attempts to reserve one permitted
provider-transient retry per case; all attempts share the existing persistent
`target/sp-autonomous-v1/attempt-budget.json`. Unknown/access/local/validation
failures receive no quality retry. Finish all fixed cases; no quality stopping,
model switch, paid fallback or refund/reset follows any outcome. Subscription
calls have zero incremental cash charge; quota use and provider billing remain
unmeasured. No additional inference pass is proposed for production.

Both arms are frozen before inference, so the candidate's snapshot baseline is
unrun. Native text-comparison baseline fields are not the fresh control and are
not scored. Compare actual completed fresh answers by identical case ID and POST.

## Blinded assessment and calibration

The root is an unblinded broker. Fresh reviewers receive only the complete POST,
unchanged parsed answer and a randomly assigned neutral answer token, plus the
frozen semantic criteria below. Root supplies an exact read-only native `show`
projection command; its neutral E01–E06 runner alias is visible, but the prompt,
version, version-bearing paths, snapshot baseline, earlier verdicts and token key
are excluded. Reviewers must not inspect repository files or other metadata.
This refinement was recorded before the first answer assessment and avoids
custom review-packet files. Lock assessment before decoding. Root records each verdict with
native `review --case`; every review binds the actual input/output hashes.
Randomize answer presentation separately from runner-slot assignment.

Apply existing source/full/partial/scope/copy rules with numbered witnesses:

- Source: retain complete supported referents, roles, modifiers, amounts,
  negation, expressed groups and full/partial actions. Match semantic meaning,
  including passive paraphrases, rather than exact expected text. Do not require
  arbitrary combinations across topics. A complete shared action can represent
  its participant group without a separate non-action group node.
- Scope: each actual child heading preserves every restriction of its actual
  parent, judging the two subject strings alone across possible posts. Generic
  entities do not acquire food purpose, newness, origin or roles from context.
  Optional missing general headings are not repaired or failed edges.
- Copy: inspect every actually returned compatible numbered parent occurrence.
  A source never correctly formed is source loss, not an independent missing
  copy. Equal meaning at a source's own entry represents itself. Otherwise all
  compatible more-general copies collect it; another branch cannot repair a gap.
- Preserve existing uncertainty about dinner/purchase attachment, ambiguous
  ingredient membership and K002 chronology versus separate unpacking. Later
  stable qualifications remain relevant; a changed temporal state is not
  retroactively imported. Generic advice components may have complete attributed
  conditional joint descendants under the existing calibration.
- N100 narrative sirloin origin is an inferred boundary, not explicit source
  wording. A human calibration question is pending before inference. Record it
  separately; until answered, an origin-only objection is uncertain rather than
  a decisive reject. Do not regrade historical answers. Existing S006 accepts
  colloquial reliable for never-fail and does not require an absent easy claim.

Confirmed failures dominate accept/uncertain differences. Report each dimension
and unavailable answer separately. A candidate with any clear original-post
reject is not a reliable fix. Inspect assessment disagreements and obtain human
feedback on ambiguous judgments; independent agent agreement is not measured
human agreement. A single answered calibration item cannot establish a general
grader-agreement rate.

The eleven reused development posts and three trials per case provide a bounded
diagnostic comparison, not representative population accuracy. Reserve all eight
unused prospective-v2 posts until a candidate passes development; repeated tuning
must not consume the holdout. Further independent replication and representative
validation remain necessary before adoption or generalization claims.

## Pre-inference verification

Before answer assessment, all three blinded reviewers independently reject
Food seasonings → Salt and accept Food seasonings → Salt for food seasoning,
matching the user's earlier explicit Salt judgment. Each supplies road-deicing
salt as the counterexample. Agreement is 3/3 for each of two related heading
pairs; this checks one calibrated restriction distinction, not whole-answer
agreement or representative grader accuracy. The N100 origin question remains
pending and separate from that existing human label.

Commit prompt, exact edits/receipts, reusable spec, checks and maintained plan
before calls. Verify all six prepared plans have the same eleven complete input
texts, matched evidence/settings, frozen renders, zero reuse and unchanged source
hashes. Validate every example through the production subjects adapter, retain
all 34 primary clauses/five tracked implications, and audit their actual semantic
preservation separately from static assignment counting.

The instruction-order check first fails on ASv6.95. All 137 focused/existing
example, native revision and attempt-budget checks pass after the revision.
Two independent semantic audits find all seven exact blocks and output
requirements preserved. The six-plan read-only audit confirms eleven identical
original POST inputs, matched evidence/settings, exact frozen renders and zero
reuse in each plan. Artifacts are ignored from creation.

ASv6.96 source SHA256:
`4899be460978c5b561975d507b8a584b9c65e15f2b5cdd3c2229b42c34e2195b`.
POST-template SHA256:
`5464710b08999eae75617526a250c873a22a8748aa0331fdb8d908a9d868bdfd`.

## Completed fresh results

All six runners finish their eleven fixed cases: 66 valid first answers, zero
errors, retries, reused answers or unrun cases. The persistent counter reaches
1,487/2,000, leaving 513 attempts; it is not reset or refunded. The exact
subscription Sol 6.1 medium route is preserved. No paid fallback, cash-ledger
increment or production adoption follows this result.

Read-only audits verify that each of the 66 actual request bodies contains its
exact frozen prompt, model and effort. Each has one HTTP attempt and normal
completion. The raw final answer equals the response and adapter raw text;
parsed JSON equals the validated model output. This excludes observed prompt
substitution and output rewriting. It does not establish that single-user-message
delivery, instruction organization or any hidden model procedure causes failure.
Both committed ASv6.96 source hashes remain unchanged.

All 66 primary assessments and 24 independent original-post assessments are
locked without prompt versions. After explicit corrections under the existing
joint-amount and purchase-attachment calibration, the paired reviewers agree on
the whole-answer verdict in 20/24 cases. Disagreements are T001/S001,
T013/S005, T030/S013 and T035/S015. The additional K001 cross-check below is
outside those 24 pairs. Agent agreement is not human accuracy; the prior Salt
calibration still covers only one related restriction distinction.

The unblinded broker appends a final assessment separately from the blind locks.
Native `review` stores 158 hash-bound events: 90 fixed blind assessments, one
initial judgment subsequently corrected, one extra blind cross-check, and 66
explicitly marked final broker verdicts. Live native `show` verifies all events
against the same current inputs and outputs. Its `current` field means matching
hashes, not latest or adjudicated; scoring uses the single event per case whose
comment starts `Final broker adjudication`. No human-role whole-answer review
is invented.

| Assessment | ASv6.95 accept / reject / uncertain | ASv6.96 accept / reject / uncertain |
| --- | --- | --- |
| Locked primary, after existing-calibration corrections | 22 / 9 / 2 | 20 / 13 / 0 |
| Final broker, retaining disputed boundaries as uncertainty | 22 / 9 / 2 | 19 / 10 / 4 |

Final bounded verdicts by repeated development post:

| Post | ASv6.95 accept / reject / uncertain | ASv6.96 accept / reject / uncertain |
| --- | --- | --- |
| N063 | 2 / 1 / 0 | 2 / 1 / 0 |
| N074 | 0 / 2 / 1 | 0 / 0 / 3 |
| N096 | 0 / 3 / 0 | 0 / 3 / 0 |
| N100 | 0 / 2 / 1 | 0 / 3 / 0 |
| S006 | 3 / 0 / 0 | 2 / 1 / 0 |
| D006 | 3 / 0 / 0 | 3 / 0 / 0 |
| J001 | 3 / 0 / 0 | 3 / 0 / 0 |
| J002 | 2 / 1 / 0 | 1 / 2 / 0 |
| K001 | 3 / 0 / 0 | 2 / 0 / 1 |
| K002 | 3 / 0 / 0 | 3 / 0 / 0 |
| K003 | 3 / 0 / 0 | 3 / 0 / 0 |
| Total | 22 / 9 / 2 | 19 / 10 / 4 |

The original-post subset is 2 accepts/8 rejects/2 uncertain for ASv6.95 and
2 accepts/7 rejects/3 uncertain for ASv6.96. Both fail the frozen reliable-fix
gate. Counts are not independent-post accuracy estimates or evidence of a
statistically established regression. There is no demonstrated benefit from
the shorter instruction block in this comparison. All eight prospective-v2
posts remain unused.

## Concrete failures and assessment boundaries

- **Scope, revised N063 E01:** Food `1` contains Sea salt `1.13` without a food
  restriction. Both blind reviewers identify this Salt-like failure; food context
  cannot supply the missing restriction in the child heading.
- **Source, revised N100 E03:** `9.1` retains trimming about 3 lb of fat for
  tallow; `9.2`/`9.3.1` retain the joint quarter-pound tissue-and-scrap portion for
  the dog. No complete subject joins those two main portions in the shared
  trimming action. Both reviewers reject this omission. No subdivision inside
  the joint quarter-pound group is required.
- **Copy, revised N100 E01:** the formed Saving excess beef myoglobin for
  addition to dog food `6.1.1` is absent from compatible Beef `2.1`.
- **Copy, revised N096 E03:** complete individual onion sautéing `1.2.1.1.1`
  is missing under the first Large pan `1.1.1.2`; that occurrence contains only
  the joint sauté, while another large-pan occurrence contains individual actions.
  Separate source omissions also remain. Every N096 trial rejects in both arms.
- **Copy, revised S006 E04:** the formed complete qualified recipe is missing
  under Food `6`; its context cannot narrow Food to seasonings.
- **Source, revised J002 E03 and E04:** packing subjects `5.1`, `5.2` and
  `5.1.1` omit the stable non-waterproof property; separate waterproofness
  branches omit packing. The complete meanings are never formed, so these are
  source losses rather than a second independent copy failure.

The following reconsiderations remain visible alongside their original locks;
they are not retrospectively applied to historical experiments:

- **N074 T001, T006, T013 and T035 become uncertain.** Reviewers disagree about
  comparative controversy plus its exception, the diet restriction in Bitcoin
  carnivore narrative, colloquial vegetable references and Plants membership.
  Some primary objections paraphrased an actually comparative parent as absolute.
  These do not establish a confirmed independent failure. Human questions about
  the diet and conditional-comparison boundaries remain unanswered at closure.
  ASv6.95 T007 still rejects for a separate confirmed Dietary advice copy gap;
  T032 still rejects for an absolute no-click heading above comparative wording.
- **N100 T030 initially rejects, then becomes uncertain, then finally rejects
  for a different confirmed copy gap.** The primary inner-material subdivision
  objection is withdrawn under the existing joint-amount calibration. The peer's
  Amazon/30%-off propagation objection is also withdrawn under the purchase
  attachment exclusion. Cutting `2.1.2` explicitly includes purchased for $10
  per lb, so empty priced Purchase `2.1.1` is compatible and lacks the copy;
  duplicate Purchase `15.1` contains it. No global price propagation is required.
- **N100 S020 retains reject after withdrawing purchase-detail propagation.**
  The independent finally-using parent `7.1.1.1` has a love-after-use child
  `7.1.1.1.1` that omits finally. Implicit physical origin remains uncertain.
- **K001 T034 becomes uncertain after an extra blind cross-check S025.** The
  primary treats author's river walk as unsupported; the other reviewer accepts
  it as reasonably implied by I packed boots for the river walk. Source evidence
  permits reasonable implications; the stricter across-possible-post test governs
  parent-child restrictions. No scope/copy failure is found. This newly identified
  source-ownership boundary is not a calibrated human label.

These post-inference adjudications are disclosed assessment uncertainty, not a
preregistered human gold set. The already-pending N100 implicit-origin question
also remains unanswered; origin alone does not decide rejection. Clear failures
remain without resolving any of these questions. Consolidation satisfies the
authored checks but does not repair SP behavior; no unique internal cause or
generalization claim follows.

Native results and append-only reviews remain ignored under
`sse_multivector/experiments/sp-autonomous-v1/guidance-consolidation-v1/E01`–`E06`.
Inspect them with native `experiment.py show EXP --case ID --json`; snapshot
baseline text differences are not fresh quality results. Prompt/source changes
were committed as `f8358e00` before inference; neutral access and the Salt
calibration were recorded before assessment and committed as `9784e6e1`.
