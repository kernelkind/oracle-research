# Fresh instruction-consolidation comparison

Status: frozen before inference; results pending.

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
