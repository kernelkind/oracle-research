# Distillation semantic review — process and evidence

**Latest wording approval:** [DSLv3](relationship-prompt-v3.md) has user-approved
wording and remains untested. Its [approval and scope](#dslv3-wording-approval-october-10)
are recorded below; existing experiments remain bound to DSLv2.

[DSLv2](relationship-prompt-v2.md) still rejects the repeated A21 pair in the
approved [bounded trial](#dslv2-bounded-parent-child-trial-october-9). It agrees
with **24/25 assessed expectations**; interpretation-sensitive A12 is reported
separately. Fresh unchanged DSLv1 also rejects A21, agreeing on 3/4 comparisons.
The clarification has not resolved this disagreement; reviewer qualification stays
pending. All 30 calls complete on first attempts without caching or warmup.

The approved [mechanical decisions for all three checks](#mechanical-decisions-for-all-three-checks-october-9)
are implemented in source-bound preparation and the shared runner. Exact trusted
subjects and actual ordered teacher links produce native zero-attempt results;
remaining questions still use semantic calls. A21 adds a student parent absent
from the teacher and has no complete child match; its expected true label remains an
agent assessment, rather than a relationship certified by the teacher.
The [complete validation workload preview](#complete-validation-workload-preview-october-9)
now measures the mechanical savings and remaining distinct input questions offline.
The [offline token and runtime estimate](#validation-review-token-and-runtime-estimate-october-9)
projects about 15.34 hours for those questions at eight continuously occupied
slots, using 59 selected fresh saved verdicts. It excludes coverage-placement
comparisons and is not a complete-evaluation runtime estimate. The complete-answer
trial has finished at xhigh after the approved mechanical changes: 43 answers
have complete scores, 13 remain ungraded because reviewer decisions conflict,
and four have invalid student outputs. All 1,735 comparison-panel decisions are
verified and frozen; reviewer qualification remains pending. The lower-effort study is recorded in
[reasoning-level comparison](#reasoning-level-comparison-approved-october-9).

[DSSv2](support-prompt-v2.md) matches **20/20 existing support expectations and
3/3 same-post controls** in the approved
[bounded trial](#dssv2-bounded-support-trial-october-9). All 27 verdicts, including
four fresh DSSv1 comparisons, pass attributed agent review of their decisions
and reasons. Fresh DSSv1 also correctly rejects the original Nostr case after
two earlier failures with identical request bodies, so this trial does not
establish that DSSv2 caused an improvement. Qualification remains pending.

Fresh confirmation result: **two of the four rejected decisions repeat; two
change to the expected correct verdict**. All four previously accepted contrasts
stay accepted. The [unchanged-input repeat](#fresh-confirmation-of-four-rejected-cases-october-9)
completes eight fresh first attempts, with no answer reuse or warmup. The current
prompts show repeated errors and inconsistent decisions; qualification stays
pending. Agent expectations remain separate from independently adjudicated gold.

Initial actual-output development result: **DSMv3 17/19 assessed verdicts, DSSv1 19/20
and DSLv1 17/20** agree with the frozen agent expectations in the
[bounded validation trial](#actual-output-trial-results). Matching A15 remains
unscored. All 60 verdicts and two eligible warmups complete on first attempts,
without answer reuse or mechanical failures. Matching caching produces hits;
support caching produces none. Semantic disagreements remain, so this does
not qualify the reviewers for bulk pilot grading.

Authored training-control result: **DSMv3 6/6, DSSv1 6/6 and DSLv1 4/4**
match expectations in both the [larger training trial](#larger-three-check-trial-october-9)
and its [fresh repeat with eligible prefixes](#larger-three-check-repeat-with-eligible-prefixes-october-9).
All 16 fresh reasons pass native agent review; every request completed on its
first attempt, with no answer reuse. The two large matching prefixes produce
cache hits; the eligible support prefix produces none. Short shared prefixes
and singleton cases receive no explicit caching or warmup. The user accepted
LC03, LC04 and LC07 expectations and delegated LC01, LC02, LC05 and LC06
expectation review to the agent before authorizing these trials.
The [initial warmed trial](#initial-warmed-three-check-trial-october-9) remains
separate small-control evidence. These are repeated judgments on the same
authored training controls; broader qualification and lower-effort comparison
remain open.
The completed [actual-output trial](#actual-validation-preparation-approved-october-9)
tested all three checks at xhigh through source-bound preparation. Its selection
and agent expectations were frozen before calls and remain unchanged.

Status: **DSRv1 and DSRv2 qualification failed; DSMv1 passes 32/32 distinct controls and a fresh 16/16 confirmation repeat**, October 8, 2026.
DSRv1 attempted all 29 cases: 28 complete reports and one interrupted report.
DSRv2 produces 24 complete reports and five ungraded interruptions across its
preserved subsets; it fails semantic and cross-version checks. Bulk pilot
semantic review has not run. **DSMv2's latest actual-wording trial agrees with
19/20 agent expectations**, with `Fakery`→`Inauthenticity` remaining disputed.
Both cases in the preceding two-case trial agree. The full-set offline preview
makes zero calls. **DSMv2 also passes eight authored action/property controls**;
these explicit, small-catalog examples do not resolve R05 or qualify the reviewer.
An identical-input fresh R05 repeat again returns T17; both saved calls make
the disputed match with different explanations. Its expected null remains an
agent assessment, and qualification remains pending.
The [DSMv3 draft](#dsmv3-asv6100-wording-guidance-draft-october-9) adds one
verbatim ASv6.100 paragraph to matching. Its wording is approved and its two
initial development cases now pass below; broader qualification remains pending.
The agreed process and selected reviewer are recorded
in the [pilot process](../../docs/planning/fine-tuning-pilot-process.md#5-score-and-compare--locally-after-the-rental).
This package preserves [DSRv1](prompt.md), drafts [DSRv2](prompt-v2.md), and
specifies their [report schema](response-schema.json) and qualification cases.
Offline source preparation, report validation, scoring
and qualification checks are implemented in the shared experiment workflow.
The full semantic reviewer has not been qualified; bulk pilot grading is not implemented here.

## Mechanical decisions for all three checks (October 9)

The user directs using mechanical decisions whenever possible for every review
prompt. Each check still needs a recorded result; a result established from
trusted inputs does not require a model call. Apply this to matching, post
support and parent-child validity, keeping the existing semantic criteria.

| Check | Sufficient mechanical evidence | Result |
| --- | --- | --- |
| DSM complete-meaning matching | The student subject exactly equals a subject in the frozen teacher answer for the same note. | Record the teacher match without a matching call. |
| DSM complete-meaning matching | The validated teacher catalog is empty. | Record no teacher match without a matching call. A missing or invalid reference is a preparation failure instead. |
| DSS post support | The student subject exactly equals a trusted teacher subject for the same original post. | Record supported without a support call. |
| DSL parent-child validity | The student pair has the exact ordered parent and child strings of an actual immediate link in the trusted teacher answer. | Record valid without a relationship call. |
| DSL parent-child validity | The exact parent and child strings are endpoints of a numbered ancestor path in the trusted teacher answer. | Record valid with the complete teacher path as evidence; restrictions are retained through every hop. |
| DSL parent-child validity | Parent and child strings are identical. | Every parent restriction is retained; record this local pair as valid. This does not establish teacher agreement or correct placement. |

Trust the teacher answer as directed; do not re-audit it to obtain these
results. Finding the parent and child separately somewhere in the teacher
catalog is insufficient: their ordered relationship must be established.
Apart from a validated empty catalog, absence of an exact teacher subject or
link leaves a semantic question, not a mechanical rejection.
Substring overlap, shared keywords and broader or narrower wording are not
complete-meaning matches. Paraphrase matching remains a semantic task; this
decision does not make model-assessed equivalence a deterministic fact.

Record the mechanical origin and supporting source reference, with zero model
attempts; do not fabricate a model receipt. Identical rendered review requests
may share a saved result with the same settings, schema and worker identity.
Preserve the relevant post, task, reference and prompt bindings and every
numbered occurrence for coverage and placement; reuse is not fresh reliability
evidence. An explicitly requested fresh repeat must still make fresh calls.
Output parsing, numbering, completeness and score arithmetic stay mechanical.
Keep malformed student outputs and incomplete reviewer judgments under their
existing distinct failure rules.

Source-bound matching and support/relationship preparation now indexes trusted
wording and actual immediate links once per selected reference. Ancestor proofs
walk original numbered paths when queried, without storing a quadratic closure.
Every selected
student occurrence remains a separate case. Sufficient evidence adds a generic
`mechanical: {output, evidence}` result; it never reads the expected label to
choose that result. DSS checks the effective authored subject override when present.

The shared runner validates mechanical output through the selected adapter,
seals its evidence with the prepared inputs and exposes `origin: "mechanical"`,
`mechanical_evidence`, `mechanical_sha256` and `attempts: 0` in native reports.
Such cases require no model job, warmup, request-budget allowance, usage or
receipt. Mixed runs send only residual semantic cases. Complete prompts and
runtime bindings remain available, and `prepare ... --repeat` deliberately
bypasses mechanical completion for fresh model qualification calls.

Native qualification lists `mechanical_cases` and `model_checked` when mechanical
results are present. `checked` includes all completed expectation comparisons;
only model results contribute to `model_checked`. Mechanical success is not
evidence of model accuracy. Matching input-call/token estimates exclude mechanical
cases. Conflicting frozen expectations remain visible failures, and assessed or
unresolved expectations remain unverified. Historical experiments without the
new metadata retain their original model execution and receipts. This implements
selected-case routing, not bulk pilot grading or new semantic qualification.

The index is built once per bound reference and looks up trusted subject strings
and ordered pairs, retaining actual numbered witnesses without a cross-product of
duplicate occurrences. Model prompts remain complete for fresh repeats;
mechanical evidence needs only the applicable witnesses. The complete validation
preview below measures savings on changed student answers; reliability of the
remaining semantic calls still requires evidence.

A21 cannot be accepted this way: the teacher has no `Proof setup` parent, and
the child's complete-meaning match is null. Its frozen true expectation stays
agent-assessed and unadjudicated. The repeated discrepancy is not conclusive
evidence that Sol is wrong or incapable. The routing implementation leaves this
case for semantic review and preserves its saved expectations and judgments.
Further trials remain separate work.

## Complete validation workload preview (October 9)

The user's subsequent `proceed` authorizes an offline preview of all saved
validation outputs. The reusable `preview-distillation-review` project command
runs through the shared launcher, verifies the frozen ASv6.100 dataset and
saved stage receipts, and applies the same production teacher index used by
DSM/DSS/DSL preparation. It creates no prompts, model calls or scores.

The [native report](../../target/distillation-review-v1/work-preview-20261009/preview.json)
contains **1,800 outputs across 18 versions**, with **142 invalid answers** kept
separate from review work, **five valid empty answers**, **44,284 subject
occurrences** and **33,817 immediate parent-child occurrences**.

| Check | All occurrences | Mechanical | Remaining semantic occurrences | Distinct remaining inputs |
| --- | ---: | ---: | ---: | ---: |
| DSMv3 matching | 44,284 | 7,446 | 36,838 | 9,820 |
| DSSv2 support | 44,284 | 7,446 | 36,838 | 9,820 |
| DSLv2 relationships | 33,817 | 1,841 | 31,976 | 16,670 |

Mechanical rules settle **16,733 occurrences**. Of the relationship results,
1,187 reproduce actual ordered teacher links and 654 have identical parent and
child wording. No nonexact subject or relationship is rejected mechanically.
The **105,652 remaining occurrences** contain **36,310 distinct input questions**
under one fixed prompt and settings per check. These are theoretical input
groups, not prepared requests or a count of fresh executions: saved-answer reuse,
prefix warmups and retries are outside this preview. Matching keys include the
full post, complete ordered teacher catalog with stable IDs, and student wording;
support keys include the full post and student wording; relationship keys include
the ordered parent and child wording. Every numbered occurrence remains in the
per-note, per-version and per-model accounting.

The manifest and mixed reference ledger are hashed as opaque bytes. All reference
identity headers are checked against train/evaluation/test order before decoding
only evaluation row content. Reserved files and checkpoint weights are not
opened. Model manifests, training plans and sealed checkpoint metadata establish
version identity; production stage verification checks each raw answer against
its saved batch receipt and parsed result. Missing, changed or mismatched sources
abort the preview. Invalid model answers remain output failures; a valid empty
answer requires no semantic call and does not establish coverage.

Reproduce from the repository root using the collected pilot output directory:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
pilot_results=target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/result/work/results
../experiment-runner/bin/experiment-runner preview-distillation-review \
  target/distillation-pilot-v1/pilot-data-asv6.100-20261004/prepared/manifest.json \
  --model-output "$pilot_results/qwen" \
  --model-output "$pilot_results/gemma-dense" \
  --model-output "$pilot_results/gemma-moe" \
  --output target/distillation-review-v1/work-preview-20261009/reproduction.json
```

Model stages come from each sealed training plan rather than recursive file
discovery. The command rejects duplicate model directories and existing report
destinations. The ignored report binds source and counting-code hashes and saves
all denominators. This workload result does not qualify the semantic reviewers,
adjudicate A21, authorize inference or change final scoring.

## Validation review token and runtime estimate (October 9)

The subsequently authorized offline estimate extends the same preview command
with `--estimate` and repeated `--timing-experiment` paths. It verifies current
DSMv3/DSSv2/DSLv2 template bytes, frozen sources and native saved receipts without
new model calls. Estimation requires `tiktoken` in the command's Python runtime.
The [native report](../../target/distillation-review-v1/work-estimates-20261009/estimates.json)
retains all workload denominators, source hashes and timing strata.

The **36,310 distinct questions** contain **24,195,497 rendered input-text tokens**
(24.195 million), compared with **79,399,475** (79.399 million) across the 105,652
remaining occurrences. These `o200k_base` sizes exclude provider instructions,
message framing and output-schema overhead; they are not provider input receipts.
Saved-answer reuse is not resolved by this estimate.

| Current prompt | Fresh verdict samples | Mean runner seconds | Mean output tokens |
| --- | ---: | ---: | ---: |
| DSMv3 | 20 | 12.34 | 391.8 |
| DSSv2 | 20 | 12.46 | 421.0 |
| DSLv2 | 19 | 11.90 | 424.0 |

These **59 valid first-attempt calls** retain false and uncertain semantic
judgments. The DSSv2 warmup is excluded; no retries or saved-answer reuse enter
the samples. Output includes reasoning once. Runner duration includes process
startup, admission waiting and receipt validation, rather than only provider
generation. The weighted sample means project **15,049,776 output tokens**
(15.050 million) and **15.34 service hours** with eight continuously occupied
slots. Applying each check's median gives **10.86 hours**; applying each check's
p90 gives **24.94 hours**. These scenarios are not confidence bounds.

The selected development samples are small and include three prefix-role calls
per matching/support check; all three matching calls hit the cache, while support
has no hits. Other samples use ordinary full-user requests. Several batches have
fewer than eight cases, so configured concurrency does not establish occupied
slots or measured batch wall time. No additional cache speedup is applied;
samples retain their observed cache mix. Warmups, throttling, retries and review
work are additional and can make elapsed time longer.

Current automatic template prefixes contain **468 matching, 112 support and
71 relationship proxy tokens**, all below the 1,024-token threshold. Separate
natural-prefix analysis finds **19 matching and two support groups**, with no
eligible relationship group. Their **21 hypothetical warmups** contain **25,410
input-text tokens**, before unknown output and request overhead. Up to **4,757,034
proxy tokens** could be cache reads; a cold first use reduces that opportunity to
**4,731,624**. Eligibility promises no hits, as the saved support sample shows.
This analysis adopts no cache policy, grouping mode or optimization.

Reproduce from the repository root with the collected outputs and five saved
native timing experiments. The destination must not already exist:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
pilot_results=target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/result/work/results
review_results=target/distillation-review-v1
nix shell --impure --expr 'let pkgs = import <nixpkgs> {}; in pkgs.python3.withPackages (p: [ p.tiktoken ])' \
  --command ../experiment-runner/bin/experiment-runner preview-distillation-review \
  target/distillation-pilot-v1/pilot-data-asv6.100-20261004/prepared/manifest.json \
  --model-output "$pilot_results/qwen" \
  --model-output "$pilot_results/gemma-dense" \
  --model-output "$pilot_results/gemma-moe" \
  --estimate \
  --timing-experiment "$review_results/actual-three-check-20261009/matching-other" \
  --timing-experiment "$review_results/actual-three-check-20261009/matching-note27" \
  --timing-experiment "$review_results/support-scope-dssv2-trial-20261009/actual-other" \
  --timing-experiment "$review_results/support-scope-dssv2-trial-20261009/actual-note27" \
  --timing-experiment "$review_results/parent-restriction-dslv2-trial-20261009/actual" \
  --output "$review_results/work-estimates-20261009/reproduction-estimates.json"
```

Prompts, mechanical criteria, qualification, A21 and scoring retain their existing
state. The estimate prepares no experiment, sends no inference and opens no
reserved content or checkpoint weights.

## Coverage-matching qualification scope agreed October 8

Qualify matching of **required complete teacher meanings**. Optional derived
teacher headings are not mandatory coverage targets. Every student heading
still needs a subject-support verdict, and every immediate parent-child link
still needs a relationship verdict. Required meanings must occur at every
compatible student heading occurrence, including general headings; excluding
an optional teacher heading as a target does not exclude student headings from
placement review. Complete-meaning matching criteria are unchanged.

Establish required/optional flags from the trusted teacher answer and post,
independently of candidate answers, and freeze them across versions of each
note. Those flags and revised qualification cases remain to be established.
The current `distillation_matching` adapter still bypasses required flags and
supplies all distinct teacher strings. Existing prompts, expectations and trials
are preserved; this scope decision neither changes them nor qualifies the
reviewer. In particular, R05's requirement flags are not frozen and its expected
null remains a disputed agent assessment. Further preparation, implementation,
model calls, bulk review and test unsealing remain separate work.

## Teacher-relative qualification case preview (October 8)

After questioning the required/optional distinction, the user authorized a
concrete teacher-relative example and then preparation of qualification cases,
with exact inputs and expected judgments shown before new calls. The proposed
comparison preserves teacher meanings and parent-child relationships, allowing
equivalent wording, renumbering and sibling reordering. Missing headings and
changed relationships are recorded as disagreements; structural allowances and
the final pilot scoring rule remain open. The user subsequently reviewed the
cases in conversation, accepting all six expected judgments. These approvals
establish the expected findings below, not a replacement pilot rubric, model
qualification or a change to existing prompts, scores or saved trials.

[teacher-relative-source.json](teacher-relative-source.json) defines six
variants of ASv6.100's trusted cable example, binding the unchanged task hash.
Each case specifies matches for all ten distinct teacher wordings, including
general headings and every repeated pair/comparison occurrence. Expectations
are authored from controlled edits and remain outside the prompt. They contain
no required/optional labels or numerical scores. No pilot data or final-test
answers are read. These worked-example controls appeared in earlier development;
they are not fresh independent confirmation or evidence of pilot-wide accuracy.

| Case | Student change | Expected finding | User review |
| --- | --- | --- | --- |
| TC01 | None. | All three checks pass by definition because the complete trusted teacher answer is unchanged. Check this mechanically, without a semantic model call. | Agreed. |
| TC02 | `2 m cable A` becomes `Cable A, two metres long`. | Teacher agreement, post support and parent-child validity all pass. | Agreed. |
| TC03 | Remove `not` from all four comparison copies. | Teacher agreement and post support fail: no complete match for the original comparison and four unsupported subjects. Incoming links remain valid. | Agreed. |
| TC04 | Move the complete `3 m cables` subtree beneath `2 m cables`. | Teacher agreement fails because the parent changed. All subject meanings remain present and supported; the new incoming link to `1.1.1.2` is invalid. | Agreed. |
| TC05 | Remove `2 m cables` and promote its subtree. | Teacher agreement fails because the separate general heading is missing. Remaining subjects and incoming links are valid. | Accepted with “ok”. |
| TC06 | Renumber the complete root/subtree from `1` to `9`; the adapter orders entries by the new numbers. | All meanings and parent-child relationships preserved; all three checks pass. Check this renumbering mechanically, without a semantic model call. | Agreed. |

The review order was TC05, TC04, TC03, TC02, TC06, then TC01. These are user
decisions about authored expectations, not measured model verdicts. The
renumbering example does not independently test arbitrary sibling reordering.
The unchanged-answer and renumbering controls should be checked mechanically.
See the [decision record](../../docs/planning/release-decisions.md).

TC05 preserves Q12's original transformation, not its existing acceptance as a
full-coverage answer. A missing teacher match and an invalid returned subject
are separate findings. The current scorer still excludes optional rows; these
new definitions do not make the omission an AS subject/link error or change
that scorer. A general teacher-edge agreement check is not implemented here.

[teacher-relative-preview-spec.json](teacher-relative-preview-spec.json) uses
the **unchanged DSRv2 draft** solely to inspect the complete bound post,
teacher/student arrays, exact matches and expectations through the existing
adapter. `teacher_meanings` is null. This legacy rendering is not adoption of
DSRv2, its call shape or its requirement-classification instructions for the
proposed comparison. Further reviewer/rubric work must precede a full trial.

The separate [matching source](teacher-relative-matching-source.json) binds
that same case source by SHA256. Its [specification](teacher-relative-matching-spec.json)
uses **unchanged DSMv2** for exactly two non-exact targets: TM01 selects TC02's
paraphrase (expected T04), and TM02 selects TC03's changed comparison (expected
null). Each request retains the original post and complete ten-wording teacher
catalog. Exact targets stay out of model requests. These calls would test only
meaning matching, not subject support, links or structural disagreement scoring.
Both specifications retain Sol / xhigh, subscription SSE and concurrency 8.

Use the shared CLI in an environment providing `tiktoken==0.14.0`:

```sh
../experiment-runner/bin/experiment-runner prepare target/distillation-review-v1/teacher-relative-preview-20261008 --spec sse_multivector/distillation-review-v1/teacher-relative-preview-spec.json --repeat
../experiment-runner/bin/experiment-runner prepare target/distillation-review-v1/teacher-relative-matching-20261008 --spec sse_multivector/distillation-review-v1/teacher-relative-matching-spec.json --repeat
../experiment-runner/bin/experiment-runner show target/distillation-review-v1/teacher-relative-preview-20261008 --case TC05 --json
../experiment-runner/bin/experiment-runner show target/distillation-review-v1/teacher-relative-matching-20261008 --case TM01 --prompt-only
```

Preparation authorizes no inference. Exact inputs and expected findings can be
inspected without new reviews; prompts, implementation, full qualification,
bulk grading and test unsealing remain separate work.

## DSMv2 matching instructions approved (October 9)

The user reviewed [DSMv2](matching-prompt-v2.md), confirmed its scope as
complete-meaning matching, and approved the instructions. Each call receives
one generated subject, the original post and all distinct teacher wordings.
The shown cable JSON is the input being judged; expected T04/null results
remain outside the prompt. It returns exactly one JSON object containing
`teacher_id` (a supplied ID or JSON `null`) and `reason` (a brief explanation).
That format is already specified by the unchanged prompt and
[response schema](matching-response-schema.json).

This is approval of the wording, not model qualification or bulk adoption.
Subject support and parent-child validity remain separate judgments. No new
calls or changes to case sources or scoring followed from this approval; both
prepared teacher-relative requests remain unrun and R05 remains disputed.

## DSMv3 ASv6.100 wording guidance draft (October 9)

The user accepted adding relevant ASv6.100 subject-wording guidance verbatim to
the matching prompt before qualifying the revised version. The shared CLI's
`revise` command produced [DSMv3](matching-prompt-v3.md) from approved DSMv2,
with native [revision provenance](matching-prompt-v3.md.revision.json). Only the
version label and one interpretive block change. The task still compares one
student subject with the trusted teacher's complete distinct-wording list.
`POST`, `MATCH_INPUT`, matching criteria and the existing `teacher_id` / `reason`
response contract are unchanged. No adapter, schema or case-source edits are
needed for this draft.

The inserted paragraph comes directly from
[ASv6.100](../subject-prompt-goal-v1/asv6.100/ASv6.100.md), beginning “Make each
`subject` concise” and ending “complete source subjects retain those details in
their own specific headings.” Its original bytes are preserved. The passage
explains subject wording, comparison sides and broader headings. A short wrapper
limits its role to interpreting entries for complete-meaning matching against
the trusted teacher list. Other generation, numbering and placement instructions
and worked examples are excluded. The original ASv6.100 file remains unchanged;
the prompt's quoted block is verified against that fixed source rather than
maintained as a paraphrased standard. This adds fixed input text per comparison,
without changing the candidate catalog, call count or batching policy. No token,
cached-token, cost or accuracy measurement is claimed by drafting.

The user approved the exact DSMv3 wording after the full instructions were
displayed in the conversation on October 9. The unchanged prompt now passes two
initial development cases in the subsequently authorized
[initial warmed trial](#initial-warmed-three-check-trial-october-9); broader
qualification is pending. Wording approval alone did not authorize those calls.
Previous DSMv2 results do not qualify this new version. Existing controls, expected labels and saved trials are preserved;
R05's disputed match remains unresolved. The amendment does not change support
or link judgments, final pilot scoring, bulk adoption or test sealing.

## DSSv1 subject-support prompt draft (October 9)

The user authorized drafting [DSSv1](support-prompt-v1.md) for review in the
conversation. It asks whether every meaning expressed by one unmatched subject
is supported by the complete post, applying ASv6.100's subject-support rules.
Supported broader headings can pass; one unsupported detail makes the subject
fail. The input is one JSON object with `post` and `student_subject`, inserted
at `SUPPORT_INPUT`. The output is exactly `valid` (Boolean) and `reason` (string).
Teacher coverage and parent-child validity remain separate checks.

The user approved reusing ASv6.100's authoritative rules unchanged rather than
maintaining a paraphrased support rulebook. DSSv1 now adds a narrow review task
and output format around `ASV6_100_SUPPORT_RULES`. This variable is the verbatim
opening text of [ASv6.100](../subject-prompt-goal-v1/asv6.100/ASv6.100.md), from
its first sentence through “Derive broader headings by generalizing source
meanings without adding restrictions.” The contiguous excerpt includes the
support rules and broader-heading allowance; it ends before parent-child,
placement and output instructions or worked examples. Future shared-workflow
preparation must load it from that original source, rather than a separately
maintained copy. The `distillation_verdict` adapter now supplies this variable
from the source and prepares the development inputs below. The user approved the
rule-reuse decision, then accepted the revised wrapper's exact wording after
the full DSSv1 instructions were displayed in the conversation on October 9.
This accepts the instructions without qualifying the reviewer or authorizing
new calls.

For the trusted cable post, `Lengths` passing and `4 m cable A` failing are
proposed authored controls, not model verdicts or approved qualification cases.
They are input examples for human review, not worked examples embedded in DSSv1.
Both development inputs now pass in the subsequently authorized
[initial warmed trial](#initial-warmed-three-check-trial-october-9). The accepted
prompt remains unqualified for bulk use. The proposed inheritance of post support from correct complete teacher matches still needs process approval;
relying on semantic matches also requires qualifying the matcher. Existing
matching/review prompts, scoring and saved trials remain unchanged. The
subsequent development preparation below adds source preparation and schema
validation without adopting support inheritance.

## DSLv1 parent-child validity prompt draft (October 9)

The user authorized drafting [DSLv1](relationship-prompt-v1.md) as the next
step, for review in the conversation before model calls. Each request judges
one actual immediate parent-child pair. `RELATIONSHIP_INPUT` contains only
`parent_subject` and `child_subject`, both complete subject strings. The rule
uses those strings across possible posts in any domain; the original post,
contexts, ancestors, siblings and teacher catalog are not supplied. Post
support and agreement with the teacher's relationships remain separate checks.
The output is exactly Boolean `valid` and string `reason`. An invalid verdict's
reason names the missing parent restriction and gives a possible post fitting
the child but failing to fit the parent. The supplied pair stays unchanged.

`ASV6_100_PARENT_CHILD_RULES` is the verbatim text in
[ASv6.100](../subject-prompt-goal-v1/asv6.100/ASv6.100.md) starting with “Judge
each parent-child pair” and ending with “The post's domain, `context` and other
entries cannot supply a missing heading restriction.” It excludes the preceding
sentence about deriving broader headings and the following placement rules.
Future shared-workflow preparation must load this contiguous text from the
original source. The `distillation_verdict` adapter now supplies both variables,
deriving the immediate parent from the selected child's student number. A shared
Boolean response schema validates support/link output mechanics. Pilot scoring
is unchanged.

The human example uses TC04's already-agreed invalid edge: `3 m cables` beneath
`2 m cables`. Its expected `valid: false` is an authored illustration of that
accepted case judgment, not a model result or newly prepared qualification
case. It remains outside the prompt instructions. At most one semantic verdict
is requested per actual immediate link; the input grows with the two subject
strings plus the fixed rule, without a whole hierarchy or all-pairs comparison.
This is draft call sizing, not approval of bulk execution or an optimization.

The user approved the exact DSLv1 wording after the full instructions were
displayed in the conversation on October 9. The unchanged prompt now passes its
three initial cases in the subsequently authorized
[initial warmed trial](#initial-warmed-three-check-trial-october-9). Drafting and
wording approval alone added no model calls, qualification result,
support-inheritance decision or final rubric adoption. ASv6.100, DSMv2,
DSSv1, existing adapters, schemas, scores and saved trials are unchanged.

## First three-check development inputs (October 9)

The user authorized offline preparation and presentation of test inputs before
model calls. These seven requests reuse TC02, TC03 and TC04's already-accepted
judgments. They are a first development preview, not sufficient evidence to
qualify the reviewer. The unchanged-answer and consistent-renumbering controls
remain mechanical; no semantic calls are prepared for them. The proposed
`Lengths` / `4 m cable A` controls are not included.

The trusted source post is: “2 cables: cable A is 2 m long and cable B is 3 m
long. A is not longer than B.” Matching receives that post, the full ten-wording
teacher catalog, and one student subject. Support receives the post and one
subject. Parent-child review receives only the two subject strings from the
student, with their immediate relationship derived from student numbering.

| Case | Prompt | Model input to judge | Expected verdict |
| --- | --- | --- | --- |
| TM01 | DSMv3 | `Cable A, two metres long` against the complete teacher list | `teacher_id: T04` (`2 m cable A`) |
| TM02 | DSMv3 | `2 m cable A longer than 3 m cable B` against the same list | `teacher_id: null` |
| TS01 | DSSv1 | Post + `Cable A, two metres long` | `valid: true` |
| TS02 | DSSv1 | Post + `2 m cable A longer than 3 m cable B` | `valid: false` |
| TL01 | DSLv1 | `2 m cables` → `Cable A, two metres long` | `valid: true` |
| TL02 | DSLv1 | `Pair consisting of 2 m cable A and 3 m cable B` → `2 m cable A longer than 3 m cable B` | `valid: true` |
| TL03 | DSLv1 | `2 m cables` → `3 m cables` | `valid: false` |

TS02 and TL02 intentionally have different judgments: losing the comparison's
negation breaks post support and teacher matching, but retains both cable
descriptions required by the parent. TL03 isolates the wrong relationship;
its subject strings remain trusted and individually supported.

[Support selectors](teacher-relative-support-source.json) and
[relationship selectors](teacher-relative-relationship-source.json) hash-bind
the unchanged [agreed source cases](teacher-relative-source.json). The adapter
loads their student wording and derives Boolean expectations from
`incorrect_subjects` or `invalid_relationship_children`; selectors cannot
rewrite subjects or override those expectations. Expected verdicts and reasons
stay in evidence and never enter the prompt. ASv6.100's contiguous rule excerpts
are loaded verbatim from its hash-bound original. The
[Boolean response schema](boolean-response-schema.json) and mechanical validator
require exactly Boolean `valid` and nonempty string `reason`, rejecting duplicate
JSON keys. A wrong Boolean verdict remains a mechanically valid response and
fails the prepared set's separate qualification comparison. That comparison
does not validate the reason's semantic quality or adopt pilot scoring.

Reusable specifications pin OpenAI Codex / GPT-6.1 Sol / xhigh, subscription SSE,
concurrency 8 and the existing timeout. From this checkout, with the documented
`tiktoken==0.14.0` environment:

```sh
../experiment-runner/bin/experiment-runner prepare target/distillation-review-v1/teacher-relative-matching-v3-20261009 \
  --spec sse_multivector/distillation-review-v1/teacher-relative-matching-v3-spec.json
../experiment-runner/bin/experiment-runner prepare target/distillation-review-v1/teacher-relative-support-20261009 \
  --spec sse_multivector/distillation-review-v1/teacher-relative-support-spec.json
../experiment-runner/bin/experiment-runner prepare target/distillation-review-v1/teacher-relative-relationship-20261009 \
  --spec sse_multivector/distillation-review-v1/teacher-relative-relationship-spec.json
```

The original offline preparations contain two matching, two support and three
relationship cases and remain unrun. Separate native-prefix preparations below
execute the same seven inputs with no answer reuse. Matching inputs total
1,371 `o200k_base` proxy tokens (683–688 each); these are offline rendered-text
sizes, not provider usage or measured cost. Support repeats one complete post
per selected subject; relationship input grows only with the two strings and
fixed rule. No whole hierarchy or all-pairs comparison is added. Actual
input/cached/output and reasoning tokens from the authorized initial trial are
reported below. Source changes are covered by production-path preparation,
validation and native CLI tests using an offline executable fixture.

The exact seven inputs and expectations were displayed in conversation and the
user accepted them, then authorized the initial xhigh trial with prefix warming.
That trial passes all seven cases below; the larger training trial extends this
evidence to 16 checks on three training extremes, now repeated below. Broader
qualification remains necessary before bulk use. No
support-inheritance policy, structural allowances,
teacher-edge agreement implementation, final rubric, bulk grading or final-test
unsealing is adopted by this preparation. R05 remains unresolved.

The user also requested a later comparison of lower reasoning levels. Establish
reliability with GPT-6.1 Sol / xhigh first, then hold prompts, cases and expected
judgments fixed while comparing semantic errors, latency and actual token usage,
including cached tokens. This records future intent; no lower-effort settings,
experiment preparation or new calls are added by that future-effort request.
All three current prompts have initial and larger training development evidence
below; broader qualification and independent repeats remain open.

## Initial warmed three-check trial (October 9)

The user authorized running the seven accepted inputs and explicitly requested
prefix warming. The shared `experiment-runner/bin/experiment-runner` prepared
new immutable experiments from the original offline preparations, with the exact
fixed beginning of each rendered prompt as its prefix. Approved prompt bytes,
inputs and expectations are preserved. Three stable keys separate DSMv3, DSSv1
and DSLv1; each instructions-only warmup inherits its batch's key, prefix,
model, effort, schema and SSE settings. No warmup answer enters a verdict call.
The settings remain subscription `openai-codex` / `gpt-6.1-sol` / `xhigh`, with
batch concurrency 8. Seven available verdicts ran concurrently across the three
batches after all warmups finished; this small set cannot saturate eight slots.

All ten requests completed on their first attempt, with no reuse, interruption,
mechanical failure or retry. The persistent shared counter records 10/20 used;
the unused capacity was reserved for the existing provider-only retry allowance.
Native qualification reporting passes 2/2 matching, 2/2 support and 3/3 links.
Agent reviews, recorded with native `review --role agent`, additionally accept
all seven reasons. These are agent assessments, not additional user approvals
or independent repetitions.

| Case | Actual verdict | Agent assessment of reason | Request latency |
| --- | --- | --- | --- |
| TM01 | `T04` | Preserves cable A and its two-metre length. | 5.75 s |
| TM02 | `null` | Identifies the removed negation; no complete teacher comparison matches. | 6.02 s |
| TS01 | `true` | Cites the post's explicit two-metre cable A. | 7.18 s |
| TS02 | `false` | Cites the post's explicit “not longer” contradicted by the subject. | 5.56 s |
| TL01 | `true` | Preserves the cable and two-metre parent restrictions. | 6.72 s |
| TL02 | `true` | Retains both named cables and their lengths despite the unsupported added comparison. | 39.03 s |
| TL03 | `false` | Identifies the lost two-metre restriction and gives a possible three-metre-cable post. | 6.29 s |

The following values are copied from each native `report.json`; warmup overhead
is shown separately and must be included in any later savings comparison.
Output tokens already include reasoning tokens. The cost column is the runner's
API-equivalent catalog estimate, **not a subscription charge**; all provider
cash-cost fields are null. No paid API fallback was used.

| Native experiment under `target/distillation-review-v1/` | Calls | Input | Cached input | Cache writes | Output | Reasoning | API-equivalent USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `teacher-relative-matching-v3-warmup-20261009` | 1 | 509 | 0 | 0 | 221 | 182 | 0.003228 |
| `teacher-relative-matching-v3-warmed-20261009` | 2 | 1,461 | 0 | 0 | 213 | 131 | 0.005052 |
| `teacher-relative-support-warmup-20261009` | 1 | 669 | 0 | 0 | 182 | 150 | 0.003158 |
| `teacher-relative-support-warmed-20261009` | 2 | 1,435 | 0 | 0 | 252 | 171 | 0.005390 |
| `teacher-relative-relationship-warmup-20261009` | 1 | 333 | 0 | 0 | 329 | 292 | 0.003956 |
| `teacher-relative-relationship-warmed-20261009` | 3 | 1,087 | 0 | 0 | 1,435 | 1,291 | 0.016524 |

Every request reports zero cache reads and zero cache writes. This is consistent
with the small inputs: verdict requests report only 355–733 input tokens each,
and the shared prefixes are shorter still. Official OpenAI documentation gives
GPT-5.6 and later a minimum cacheable prefix of 1,024 visible input tokens. See
[Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching#summary-of-model-differences).
The experiment verifies warmup execution and accounting, but demonstrates no
cache savings. There is no cold comparison, and the approved prompts were not
padded to force eligibility. Warmups took 10.06 s, 8.03 s and 15.09 s respectively.

The original three offline preparations remain unused. Actual receipts, native
reports, prefix files and the irreversible attempt counter remain ignored
artifacts in the canonical checkout. Inspect a verdict with native `show`, for
example:

```sh
../experiment-runner/bin/experiment-runner show \
  target/distillation-review-v1/teacher-relative-relationship-warmed-20261009 \
  --case TL02 --json
```

These seven small development controls establish only initial prompt behavior.
The larger training trial below adds source-bound controls on selected training
extremes, with a subsequent fresh repeat using eligible shared prefixes.
Broader qualification remains necessary to establish reliability; lower-effort
comparison remains future work. No support-inheritance policy, structural allowance, teacher-edge
implementation, numerical scoring, bulk grading or final-test unsealing is
adopted. R05 remains unresolved. The subsequent authorized repeat measures
naturally eligible shared prefixes and includes warmup overhead below.

## Larger training controls prepared (October 9)

After the initial seven-case trial, the user authorized preparing harder
controlled changes from the largest ASv6.100 training answers and presenting
them before further model calls. The teacher answers remain trusted. The user
accepted LC03, LC04 and LC07 after presentation, then said they did not want to
inspect every remaining case personally. The agent completed LC01, LC02, LC05
and LC06 expectation review against the frozen inputs through native
`show --case`. These are agent assessments under the agreed rules, separate
from the three explicit user acceptances. All authored expectations stand.
The user subsequently authorized the bounded trial; its completed model
verdicts and reason assessments are recorded below.

The existing source-bound ranking selected eight training extremes from all
1,300 answers. This preview uses three of them, spanning the maximum entry
count, maximum distinct-wording catalog and longest saved answer. Their training
identities, saved line numbers and file hash agree with that ranking. No held-out
post or subject is used as development input.

| Reference | Existing case / note prefix | Why selected | Entries | Distinct teacher wordings | Answer bytes |
| --- | --- | --- | ---: | ---: | ---: |
| L1 | Q20 / `af8e33af` | Most entries | 145 | 66 | 32,021 |
| L3 | Q24 / `166d3861` | Largest distinct catalog | 137 | 72 | 25,845 |
| L6 | Q27 / `9affd0a1` | Longest saved answer | 130 | 47 | 35,966 |

[large-training-source.json](large-training-source.json) binds the original
ASv6.100 prompt and complete saved training responses by SHA256, training line
and note ID. It defines six exact wording edits and one subtree move. Each
wording edit touches one selected leaf; the teacher catalog and post are loaded
unchanged. LC07 moves the existing Dr. Abu Safiya subtree beneath the subject
about other health workers. Student numbering derives that actual immediate
pair; its subject strings remain exact trusted teacher wording.

| Variant | Source / selected student number | Exact change | Matching expectation | Post-support expectation | Selected link expectation |
| --- | --- | --- | --- | --- | --- |
| LC01 (**agent reviewed**) | L3 / `1.1.5` | `kills two people` → `kills 2 people` | LM01: T07 | LS01: true | No link call |
| LC02 (**agent reviewed**) | L3 / `1.1.5` | `kills two people` → `kills three people` | LM02: null | LS02: false | No link call |
| LC03 (**agreed**) | L3 / `18.1.1.1` | Remove ` in three days` | LM03: null | LS03: true | LL01: false |
| LC04 (**agreed**) | L1 / `2.3.1` | `rather than printing money` → `and printing money` | LM04: null | LS04: false | No link call |
| LC05 (**agent reviewed**) | L6 / `1.2.2.1.1` | `released to mark YouTube’s renewed account ban` → `released to mark the renewed banning of the group’s account by YouTube` | LM05: T07 | LS05: true | LL02: true |
| LC06 (**agent reviewed**) | L6 / `1.2.2.1.1` | `YouTube’s renewed account ban` → `YouTube’s first account ban` | LM06: null | LS06: false | LL03: false |
| LC07 (**agreed**) | L3 / `6.2.2.2` after move | Move subtree `6.2.1` beneath `6.2.2` as `6.2.2.2` | Exact teacher wording; no call | Trusted wording; no call | LL04: false |

`Agreed` marks explicit user acceptance; `agent reviewed` marks delegated
expectation assessment, not a model result or individual user approval.

T07 is local to each teacher catalog: LM01 names the complete dated attacker
headline; LM05 names the complete video description and its combined mocking
clauses. Different notes do not share a global teacher ID. All other matching
expectations are null after inspecting the complete catalog; no closest or
partial match is accepted. Four wording edits reuse previously authored DSMv1
controls (M21/M22/M27/M28). All three source notes have appeared in development
before; this preview is not an independent confirmation partition.

The agent’s remaining expectation assessments are:

- **LC01:** `two` → `2` preserves the complete dated headline and the post’s
  stated count. LM01 matches T07; LS01 passes. No link call is prepared.
- **LC02:** `two` → `three` changes the count. The complete catalog has no
  matching three-person headline, and the post says `Kills 2`. LM02 returns
  null; LS02 fails. No link call is prepared.
- **LC05:** the paraphrase retains Explosive Media as the account owner,
  YouTube as the banning platform, the renewed ban, the video’s release purpose
  and every unchanged description and mocking clause. The post states that
  YouTube has `(again)` removed the group’s account and that the video marked
  that occasion. LM05 matches T07; LS05 and LL02 pass. The actual immediate
  child preserves every restriction in its supplied parent string.
- **LC06:** `renewed` → `first` changes the ban for which the video was released.
  No complete teacher entry matches; the post’s `(again)` contradicts that
  change. The child also loses the parent’s renewed-ban restriction: a possible
  post about the same video and mocking clauses released to mark a first-ever
  ban fits the child while failing the parent. LM06 returns null; LS06 and LL03
  fail.

These assessments inspect the complete catalogs, posts and selected actual
parent-child pairs supplied to the respective checks. They do not re-audit
ASv6.100, add calls or change frozen labels, prompts or settings. No material
ambiguity remains in these four controls.

For LC03, the original teacher subject is:

> December 29, 2025 headline: the United Nations reports that violence in Sudan displaced more than 10,000 people in three days

The edited student subject is:

> December 29, 2025 headline: the United Nations reports that violence in Sudan displaced more than 10,000 people

Its unchanged immediate student parent is:

> More than 10,000 people displaced by violence in Sudan in three days

Agreed judgments: no complete teacher match because the time window is lost;
post support passes because the remaining meaning is expressed by the post;
the link fails because the child omits the parent's three-day restriction.
The user accepted these three judgments with “ok” after seeing the complete
teacher subject, edited student subject and unchanged immediate parent. This
approves LM03: null, LS03: true and LL01: false, not new model calls. A possible
December 29 headline reporting that displacement over a month fits the child
without supporting the parent. The full post is preserved in matching
and support inputs. The parent-child prompt receives only these two strings.

For LC04, the original teacher subject is:

> The Bank for International Settlements designing monetary rules rather than printing money

The edited student subject is:

> The Bank for International Settlements designing monetary rules and printing money

The original post states:

> The BIS doesn’t print money; it designs the rules of the game.

The user accepted both proposed judgments with “ok”: no complete teacher match
(LM04: null), because `and` reverses the exclusion expressed by `rather than`;
post support fails (LS04: false), because the added claim of printing money
contradicts the post’s explicit negation. This accepts those two expectations
and adds no model calls. This preview includes no separate link call for LC04.

LC05/LC06 retain the full long composite about the Loser 2 video, its release
purpose and all three mocking clauses. LL02 checks that the passive paraphrase
preserves the complete parent; LL03 checks that a first ban cannot supply a
renewed ban. Its possible counterexample describes the same video and mocking
clauses released to mark a first-ever account ban. For LL04, the parent is
`Health workers other than Dr. Abu Safiya abducted from Gaza`, while the child
is `Dr. Abu Safiya, a health worker abducted from Gaza`. A post describing only
Dr. Abu Safiya's abduction fits that child without supporting the excluded-person
parent. The user accepted LL04: false with “ok” after seeing this actual student
pair: the parent explicitly excludes the person named by the child. LC07
changes the relationship while preserving all subject wordings, so matching
and support calls remain unnecessary for those trusted exact strings. This
approval adds no model calls, general teacher-edge comparison or final scoring
implementation.

The unchanged `distillation_matching` and `distillation_verdict` adapters prepare
**six DSMv3, six DSSv1 and four DSLv1 inputs**, initially unrun with zero
attempts/reuse. The same preparations now hold the completed trial below.
The source-bound selectors and specifications are:

- [matching selectors](large-training-matching-source.json) and [spec](large-training-matching-spec.json);
- [support selectors](large-training-support-source.json) and [spec](large-training-support-spec.json);
- [relationship selectors](large-training-relationship-source.json) and [spec](large-training-relationship-spec.json).

Expected verdicts and reasons remain outside prompts. DSMv3 receives the complete
66/72/47-wording catalog, post and one changed student subject. DSSv1 receives
the complete post and that same subject. DSLv1 receives one actual immediate
student pair, with the unchanged authoritative rule. Generic incoming pairs
for LC01/LC02 add no link calls in this preview; LC04 focuses on matching and
post support. LC07 adds no semantic
matching or support work for exact trusted strings.

All specifications preserve `openai-codex` / `gpt-6.1-sol` / `xhigh`, subscription
SSE, concurrency 8 and unchanged response schemas. Native matching sizing reports
14,208 total rendered `o200k_base` proxy tokens, 2,260–2,441 per request, with at
most 72 distinct teacher wordings. These are offline text sizes, not provider
usage, latency, cache hits or measured costs. Preparation adds no warmup request
or claim of caching benefit. No whole hierarchy or all-pairs model review is
added: this set defines 16 verdict requests before warmups or any permitted
provider retries. The authorized trial below used these exact preparations.

Original preparation commands, using an environment with `tiktoken==0.14.0`:

```sh
../experiment-runner/bin/experiment-runner prepare \
  target/distillation-review-v1/large-training-matching-20261009 \
  --spec sse_multivector/distillation-review-v1/large-training-matching-spec.json
../experiment-runner/bin/experiment-runner prepare \
  target/distillation-review-v1/large-training-support-20261009 \
  --spec sse_multivector/distillation-review-v1/large-training-support-spec.json
../experiment-runner/bin/experiment-runner prepare \
  target/distillation-review-v1/large-training-relationship-20261009 \
  --spec sse_multivector/distillation-review-v1/large-training-relationship-spec.json
```

Native `show --case LM03 --prompt-only` on the matching experiment displays the
complete model input; `show --case LL01 --json` on the relationship experiment
displays its exact pair and separate expected evidence. Prompt bytes, paired
student wording, source hashes and actual parents are verified through the
existing production preparation paths. The 36 relevant preparation/validation
regressions pass with `tiktoken`; the default Python initially failed because
that dependency was absent. No adapter or prompt implementation changes were
needed. Ignore exceptions keep the seven reusable source/spec JSON files tracked,
while generated experiments and the temporary training fixture stay ignored.

Expectation review was completed before calls: three variants have explicit
user acceptance and four have delegated agent assessments. The subsequent
authorized trial and fresh repeat match all 16 expected verdicts below. Broader
qualification and later lower-effort comparison remain open. Support inheritance,
structural allowances, teacher-edge implementation, final scoring, bulk grading
and test unsealing are not adopted by preparing these inputs. Existing cases, prompts, expected labels and saved trials remain
unchanged; R05 remains unresolved.

## Larger three-check trial (October 9)

After expectation review was completed and the bounded 16-request trial was
proposed, the user replied “proceed”. The shared stable launcher ran the three
existing preparations without changing prompts, subjects, source bindings,
labels or settings: `openai-codex` / `gpt-6.1-sol` / `xhigh`, subscription SSE,
concurrency 8. Batches ran sequentially with six, six and four available cases;
concurrency 8 was the configured ceiling, not eight occupied slots. Native
`run --max-new-attempts` allowances were 12, 12 and 8 respectively, admitting
only the existing provider-only retry policy. All 16 requests completed on
first attempts, with no retry, failure, interruption or answer reuse.

Native qualification reports pass **DSMv3 6/6, DSSv1 6/6 and DSLv1 4/4**.
Native `review --role agent` additionally records acceptance of all 16 reasons
after case inspection. In particular, the lost three-day restriction receives
no teacher match, retains post support, and fails the parent-child link. LL01’s
counterexample explicitly keeps displacement below 10,000 in every three-day
period while exceeding it over a month. The long paraphrase preserves meaning
and parent restrictions; the first-ban change fails all three selected checks.
The wrong-parent move fails the exclusion test. These reason assessments are
separate from mechanical schema validation and prior user acceptances.

| Native experiment under `target/distillation-review-v1/` | Verdicts matching expectations | Request latency |
| --- | ---: | --- |
| `large-training-matching-20261009` | 6/6 | 6.51–8.55 s |
| `large-training-support-20261009` | 6/6 | 5.98–17.24 s |
| `large-training-relationship-20261009` | 4/4 | 7.68–12.76 s |

The following values are copied from each native report. Output already includes
reasoning. Costs are the runner’s API-equivalent catalog estimates, not
subscription charges; provider cash-cost fields remain null. No paid API
fallback was used.

| Native experiment | Calls | Input | Cached input | Cache writes | Output | Reasoning | API-equivalent USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `large-training-matching-20261009` | 6 | 14,430 | 0 | 0 | 1,129 | 817 | 0.040150 |
| `large-training-support-20261009` | 6 | 6,360 | 0 | 0 | 1,560 | 1,208 | 0.028320 |
| `large-training-relationship-20261009` | 4 | 1,655 | 0 | 0 | 1,346 | 1,060 | 0.016770 |

Every request reports zero cached input and cache-write tokens. These frozen
larger preparations have no explicit cache-affinity key or prefix warmup; this
trial neither demonstrates savings nor compares warmed and cold requests.
The earlier instructions-only warmup trial remains separate evidence.

Receipts, model outputs, native reports and attributed agent reviews stay
ignored in the canonical checkout. Inspect exact saved evidence with:

```sh
../experiment-runner/bin/experiment-runner show \
  target/distillation-review-v1/large-training-relationship-20261009 \
  --case LL01 --json
```

This is one successful development trial of authored changes on three previously
used training notes, including the largest teacher catalogs and answers. It
establishes behavior on these controls, not reliability on arbitrary distilled
answers or an independent confirmation partition. The separately authorized
fresh repeat below checks stability on the same controls and measures eligible
prefix caching. Broader qualification and lower-effort comparison remain open.
No support inheritance, structural allowance,
teacher-edge implementation, final scoring, bulk grading or test unsealing is
adopted. R05 remains unresolved.

## Larger three-check repeat with eligible prefixes (October 9)

The user authorized a fresh xhigh consistency repeat with caching, then required
skipping caching and warmups for prefixes that are too small. Native
`prepare --from ... --repeat --only ...` creates six subsets of the saved three-check trial. All
16 rendered prompts, source inputs, input hashes and expected judgments remain
identical to their baselines. GPT-6.1 Sol, xhigh, subscription SSE, schemas and
the concurrency-8 ceiling remain fixed. The fixed shared reference text ends
just before `student_subject`; the variable student wording follows it.

Before calls, `tiktoken` 0.14.0 / `o200k_base` measures the naturally shared
prefixes. These are rendered-text proxies, not provider token counts. Only
prefixes meeting OpenAI's documented [1,024-token minimum](https://developers.openai.com/api/docs/guides/prompt-caching)
with more than one use receive an explicit key, exact prefix and native warmup.
No padding or additional examples are added. The all-case shared prefixes are
only 469 matching, 635 support and 300 relationship proxy tokens.

| Shared prefix | Proxy tokens | Verdict calls using it | Explicit caching and warmup |
| --- | ---: | ---: | --- |
| Matching L3: instructions, full post and complete teacher catalog | 2,324 | 3 | Yes |
| Matching L6: instructions, full post and complete teacher catalog | 2,361 | 2 | Yes |
| Support L6: instructions and full post | 1,073 | 2 | Yes |
| Support L3: instructions and full post | 932 | 3 | No: below minimum |
| Matching L1: instructions, full post and complete teacher catalog | 2,243 | 1 | No: no repeated use within this trial |
| Support L1: instructions and full post | 943 | 1 | No: below minimum and used once |
| Relationship: instructions | 300 | 4 | No: below minimum |

Each qualifying group has one native `--cache-warmup` request, completed before
its verdict batch. Warmup output never enters a review input. The other nine
verdicts have no explicit key, prefix or warmup. Batches run sequentially, with
one to four verdicts each; eight is the ceiling, not measured saturation.
The persistent stage attempt budget allows 38 attempts for 16 verdicts and
three warmups under the existing provider-only two-attempt limit. It finishes
at **19/38**: every call completes on its first attempt, with no failure,
interruption or answer reuse. No further caching probe is run.

**All 16 fresh verdicts agree with their saved baseline verdicts and authored
expectations: DSMv3 6/6, DSSv1 6/6, DSLv1 4/4.** Native `show --case` verifies
each case-level qualification; all 16 reasons have current, hash-bound native
agent acceptances. Matching/support subset reports retain their full original
expectation sets, so each reports `pending` for cases assigned to other subsets;
this is not a semantic failure or full reviewer qualification. The relationship
report passes its complete four-case set. The decisive reasons remain correct:
numeric and long paraphrases pass; changed counts, first-ban wording and
printing-money claims fail their respective checks; removing the time
restriction retains post support but loses teacher meaning and parent validity;
the moved child violates its new parent's exclusion. Invalid links include
possible-post counterexamples.

The following values are copied from the nine native reports under
`target/distillation-review-v1/large-repeat-caching-20261009/`. Native `input_tokens`
is the uncached portion; cached input is reported separately. Output includes
reasoning. API-equivalent catalog estimates are not subscription charges;
provider cash-cost fields remain null and no paid fallback is used. Every
report records zero cache-write tokens. Warmup overhead is preserved separately.

| Native experiment | Calls | Uncached input | Cached input | Output | Reasoning | API-equivalent USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `warmup-matching-l3` | 1 | 2,365 | 0 | 219 | 185 | 0.0069200 |
| `matching-l3` | 3 | 681 | 6,528 | 324 | 187 | 0.0052548 |
| `warmup-matching-l6` | 1 | 2,402 | 0 | 226 | 196 | 0.0070640 |
| `matching-l6` | 2 | 489 | 4,480 | 364 | 233 | 0.0050660 |
| `matching-rest` | 1 | 2,297 | 0 | 163 | 113 | 0.0062240 |
| `warmup-support-l6` | 1 | 1,111 | 0 | 189 | 155 | 0.0041120 |
| `support-l6` | 2 | 2,387 | 0 | 617 | 488 | 0.0109440 |
| `support-rest` | 4 | 3,991 | 0 | 974 | 756 | 0.0177220 |
| `relationship` | 4 | 1,655 | 0 | 1,315 | 1,030 | 0.0164600 |

Matching L3 and L6 demonstrate actual cache reads. Support L6 is eligible by
the proxy measure but returns no cache reads after its warmup; the reason is
not established. Size eligibility does not guarantee a hit. Matching verdicts
take 4.75–7.09 s, support 5.51–18.34 s and relationships 9.01–12.41 s.
The three warmups take 9.30 s, 7.74 s and 8.44 s respectively.

For the seven prefix-configured verdicts, the native runner puts the shared
prefix in a developer message and the remaining student field in a user
message. Concatenated prompt text is unchanged, but this role split differs
from the original trial's single user message. The other nine retain the
original format. This demonstrates agreement under the cached route; it does
not isolate caching as the cause of cost or latency differences. No aggregate
saving or independent-partition accuracy is claimed.

Exact prefix files, the persistent attempt counter, receipts, responses and
attributed reviews remain ignored in the canonical checkout. Inspect with:

```sh
../experiment-runner/bin/experiment-runner show \
  target/distillation-review-v1/large-repeat-caching-20261009/matching-l3 \
  --case LM01 --json
```

This is a second trial on the same 16 authored training checks, not 16 new
controls. Broader qualification on real distilled answers and later lower-effort
comparison remain open. No bulk grading, test unsealing, support inheritance,
structural allowance, teacher-edge implementation or final scoring is adopted;
R05 remains unresolved. Further calls require separate authorization.

## Actual validation preparation approved (October 9)

After the fresh training-control repeat, the user agreed to testing a broader
sample of actual distilled outputs at xhigh and explicitly selected all three
checks: teacher matching, post support and actual immediate parent-child
validity. The existing DSMv3/DSSv1/DSLv1 prompts, trusted ASv6.100 reference and
Sol / xhigh / subscription SSE / concurrency-8 settings stay fixed. Caching
and warmups remain conditional on naturally eligible repeated prefixes.
Reserved test outputs and lower-effort comparisons remain outside this trial.

The existing matching loader already accepts saved validation answers.
`distillation_verdict` now accepts a schema-version-2 source with a bound
`dataset_manifest` and cases naming `generation`, `student_number`,
`expected_valid`, `expected_reason`, `expectation_status` and `selection`.
Matching, support and relationship preparation share the original source
checks through `distillation_review.load_saved_generations`: frozen split,
hash, note identity, complete original prompt and production answer parsing.
Test generation paths are rejected before opening; malformed or truncated
answers are rejected. Student wording is untouched. Support receives the full
post and one subject; relationships derive the actual student parent and
receive only the two strings. Verbatim ASv6.100 rules come from the bound task.

Actual-output expectations are agent assessments, separate from independently
adjudicated gold. Native qualification stays pending for `agent_assessed`
cases even when verdicts agree, while still listing disagreements. An
`unresolved` expectation has a null placeholder and no semantic pass/fail;
it is not an expected invalid subject or link. Existing authored-control
sources and their qualification behavior remain supported unchanged.

The sample is frozen under seed `DS-three-check-actual-20261009`: one eligible
subject from each of 18 model/checkpoint versions, plus one large-catalog subject
from each final adapter. Candidate notes exclude the 15 notes in the earlier
actual matching sample. Within each version, seeded hash order selects the first
valid, untruncated answer with a nonexact subject and an actual immediate parent;
seeded subject order chooses the subject. The large-catalog additions prioritize
catalog size, then the longest eligible subject. This deliberately mixed sample
is a development challenge set, not a population accuracy estimate or checkpoint
ranking. Root-only, exact-match and malformed answers are outside this semantic
sample; their mechanical failures are not repaired or hidden.

The 21 selection hits span 16 previously unused validation notes. A17 (MoE
checkpoint 400) has the same complete rendered inputs as A01 (Qwen baseline)
for all three checks, including the actual parent. A01 serves both hits, leaving
20 distinct cases per check: **60 verdict calls**. The three note-27 additions
share the largest eligible unseen teacher catalog (42 distinct wordings).

Reusable definitions: [matching source](actual-three-check-matching-source.json)
and [DSMv3 spec](actual-three-check-matching-spec.json),
[support source](actual-three-check-support-source.json) and
[DSSv1 spec](actual-three-check-support-spec.json),
[relationship source](actual-three-check-relationship-source.json) and
[DSLv1 spec](actual-three-check-relationship-spec.json).
All selections preserve saved wording and bind generation hashes. Expectations
were assessed against each complete post, complete teacher catalog and actual
parent before calls. Matching has five expected matches, 14 expected nulls and
one unresolved case; support has 17 expected valid and three invalid subjects;
relationships have 18 expected valid and two invalid links. Matching A15 remains
unresolved: whether a match featuring late penalty drama has the complete meaning
of the drama in that match. Its null placeholder is not an expected nonmatch.

Native unassessed previews are preserved under
`target/distillation-review-v1/actual-three-check-preview-20261009/`; those
previews make zero calls. Assessed native inputs are prepared separately from
the committed specs under `target/distillation-review-v1/actual-three-check-20261009/`.
Independent agent inspection covers all 60 expected judgments before inference:
58 of 59 assessed labels agree, with matching A19's abbreviation/gloss reading
disputed and A15 still unresolved. These agents are not human gold adjudicators;
their agreement does not provide independent accuracy certification. Final native
case variables match the original previews exactly after duplicate removal;
assessed evidence adds the frozen expectations outside the prompts.

### Actual-output trial results

Native qualification remains **pending**. Case-level agreement with frozen
agent expectations is recorded below; it is not a population accuracy estimate.
Matching A15 returns T04 but has `passed: null` and no error label. Matching
A19's mismatch was disputed before calls and is not established reviewer error.
No source expectation is changed after seeing reviewer answers.

| Check | Agreement with assessed expectations | Native disagreement IDs |
| --- | --- | --- |
| DSMv3 matching | 17/19; A15 unscored | A01, A19 |
| DSSv1 post support | 19/20 | A20 |
| DSLv1 parent-child | 17/20 | A03, A06, A21 |

Native attributed agent review records **53 accept, four reject and three
uncertain**. These verdicts assess response reasoning, separately from native
agreement with a frozen label. Matching has 17 accept / one reject / two uncertain;
support has 19 accept / one reject; relationships have 17 accept / two reject /
one uncertain. No user judgments are invented or recorded.

The four rejected responses are:

- **Matching A01:** `Decentralized worlds` returns null against T02
  `Decentralized world`, treating generic noun plurality as a quantity
  restriction. Neither wording states a count. The same prompt accepts the
  generic singular/plural paraphrase in A18.
- **Support A20:** accepts `Social-media likes not being love` despite the
  post's `NOT ON NOSTR` exception. Its reason acknowledges the exception but
  wrongly permits expanding a negative claim's scope as a broader heading.
- **Relationship A03:** rejects a child about operations resuming after the
  complete parent clause about currently held MIA-bound aircraft. Its café
  counterexample still includes those aircraft and their full parent restrictions;
  it adds a requirement that the operations themselves have the aircraft type.
- **Relationship A21:** rejects a proof child explicitly including its setup
  with directed univalence under `Proof setup`. The counterexample assumes setup
  was already established, which does not remove the expressed setup subject.
  The parent requires neither explaining nor performing that setup.

Three response assessments remain uncertain: matching A19's abbreviation versus
gloss; matching A15's match-versus-drama referent; and relationship A06's
anticipated-versus-realized `eventual entry`. The A06 counterexample describes
an opportunity never taken; whether it fails the parent depends on that reading.
Its expected true label remains frozen rather than changed after the response.
Independent agent inspection agrees that A03/A21's counterexamples fail to remove
parent restrictions, while A06 needs adjudication. These four rejected reasons
are agent-assessed errors, not an independently measured error rate.

All 60 verdicts have mechanically valid, receipt-bound JSON. Both warmups also
complete: **62/124 stage attempts used**, no retry, failure, interruption or
answer reuse. Verdict settings remain Sol / xhigh / subscription SSE / concurrency
8; native warmups use concurrency 1. Five verdict batches run sequentially,
with concurrency 8 within each. Three-case groups naturally use three slots.
The two full matching/support preparations are selection evidence only; execution
uses disjoint subsets, not extra copies of their verdict calls.

Caching eligibility is measured on the unchanged rendered text with
`tiktoken 0.14.0 / o200k_base`, a proxy rather than provider billing. Prefixes
end before the `student_subject` JSON value; no padding is added. Note-27 cases
A07, A14 and A21 share each eligible prefix.

| Shared prefix | Proxy tokens | Uses | Explicit key/prefix and warmup |
| --- | ---: | ---: | --- |
| Matching note 27: instructions, post and full teacher catalog | 2,062 | 3 | Yes |
| Support note 27: rules and full post | 1,041 | 3 | Yes |
| Other repeated matching groups | 763 / 836 | 2 each | No |
| Other repeated support groups | 678 / 693 | 2 each | No |
| Relationship instructions | 300 | 20 | No |

Singleton prefixes receive no explicit caching or warmup. Each eligible native
warmup completes before its group; it inherits exact prefix/key/model/schema
settings and supplies no answer to verdicts. The matching group reports 5,760
cached-input tokens; support reports zero despite the eligible proxy length.
As in the earlier repeat, this native route uses a developer prefix and user
suffix instead of a single user message. Request format therefore changes;
these measurements do not isolate a causal cache saving.

The table copies each native `report.json` usage without summing groups. Input
means uncached input; cached input is separate. Output already includes reasoning.
Reported cache-write tokens are zero in every experiment, with no missing usage
or catalog estimate. Catalog costs are API-equivalent estimates, not subscription
cash charges; provider cash-cost fields remain null. No paid fallback or ledger
change occurs.

| Native experiment | Attempts | Input | Cached input | Output | Reasoning | Catalog estimate USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `warmup-matching-note27` | 1 | 2,103 | 0 | 228 | 192 | 0.006486 |
| `matching-note27` | 3 | 728 | 5,760 | 1,078 | 880 | 0.012812 |
| `matching-other` | 17 | 13,941 | 0 | 6,758 | 5,835 | 0.095462 |
| `warmup-support-note27` | 1 | 1,079 | 0 | 246 | 217 | 0.004618 |
| `support-note27` | 3 | 3,416 | 0 | 1,198 | 960 | 0.018812 |
| `support-other` | 17 | 12,766 | 0 | 6,438 | 5,650 | 0.089912 |
| `relationship` | 20 | 7,350 | 0 | 9,444 | 8,399 | 0.109140 |

Warmups take 7.26 s and 9.33 s respectively. Per-case verdict elapsed times are
8.36–11.94 s for matching note 27, 5.33–45.97 s for other matching,
11.42–14.65 s for support note 27, 5.25–29.45 s for other support and
6.19–67.19 s for relationships. These are individual native case latencies,
not batch wall time or a speedup comparison.

Inspect the preserved failures without new calls:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
uv run --no-project --with tiktoken==0.14.0 \
  ../experiment-runner/bin/experiment-runner show \
  target/distillation-review-v1/actual-three-check-20261009/matching-other \
  --case A01
../experiment-runner/bin/experiment-runner show \
  target/distillation-review-v1/actual-three-check-20261009/support-other \
  --case A20
../experiment-runner/bin/experiment-runner show \
  target/distillation-review-v1/actual-three-check-20261009/relationship \
  --case A03
```

The trial exposes semantic disagreements despite complete execution. The user
subsequently approves fresh confirmation of the four rejected cases with unchanged
prompts; the repeat below includes four previously accepted contrasts. Ambiguous
expectations remain separate. Bulk qualification, final scoring, reserved-test
access and lower-effort comparison remain open.

### Fresh confirmation of four rejected cases (October 9)

The user explicitly authorizes proceeding with the proposed fresh confirmation.
Native `prepare --from ... --repeat --only ...` preserves the exact saved
DSMv3/DSSv1/DSLv1 prompts, original inputs, schemas, source hashes and frozen
agent expectations. Sol / xhigh / subscription SSE / concurrency 8 remain fixed.
The baseline responses stay outside model inputs. The three ambiguous cases
from the initial trial are excluded, with their evidence and labels unchanged.

Native experiments live under
`target/distillation-review-v1/actual-error-confirmation-20261009/`:
`matching` repeats A01/A18 from `matching-other`, `support` repeats A08/A20
from `support-other`, and `relationship` repeats A03/A13/A16/A21 from the
initial trial's relationship batch. These are eight repeated inputs, not new
controls or an independent validation partition. The accepted contrasts test
that permitted generalization and preserved restrictions remain accepted; their
different inputs are not matched counterfactuals and cannot isolate a context or
wording cause.

| Rejected case | Expected | Initial verdict | Fresh verdict | Agent assessment |
| --- | --- | --- | --- | --- |
| DSMv3 A01: generic decentralized-world wording | T02 | null | T02 | Now correct; initial missed match does not recur |
| DSSv1 A20: negative claim without Nostr exception | false | true | true | Error repeats |
| DSLv1 A03: resumption with complete held-aircraft clause | true | false | true | Now correct; initial invalid-link verdict does not recur |
| DSLv1 A21: proof explicitly including directed-univalence setup | true | false | false | Error repeats |

All four contrasts preserve their accepted verdicts: matching A18 returns T05;
support A08 returns true; relationships A13/A16 return true. Native case-level
agreement is 2/2 matching, 1/2 support and 3/4 links. Attributed native agent
reviews record six accept and two reject. The fresh A20 reason quotes
`Likes aren’t love` but omits `NOT ON NOSTR`. The fresh A21 reason again
requires presenting the setup, although `Proof setup` imposes no such requirement
and the child explicitly names the setup. A13's sound preservation reasoning
has a recorded imprecision: the child names an original article, rather than
requiring the post itself to be that article.

All eight calls are mechanically valid and receipt-bound, complete on first
attempts, and have no response reuse, retries or interruptions. The persistent
stage counter finishes at **8/16 attempts**. Three native batches run concurrently;
their two/two/four case counts keep total initial in-flight calls at most eight.
No request is truncated or repaired.

The exact naturally shared prefixes are 469 matching, 635 support and 300
relationship `o200k_base` proxy tokens (`tiktoken 0.14.0`). All are below 1,024;
no explicit prefix, key or warmup is configured. Native cache-read and cache-write
counts are zero. All recorded request bodies, URLs and methods match their
baselines exactly. The shared runner is now 1.2.0 (`4718b19`); its code/worker
identity change is preserved in provenance. Its unchanged uncached serializer,
transport, pinned pi-ai 0.85.1 and retry classification preserve these requests;
the new automatic warming path is inactive without a configured prefix.

The following figures are copied separately from each native report; no total
usage or measured savings is inferred. Output already includes reasoning.
There is no missing usage or catalog estimate. Provider cash-cost fields remain
null; catalog prices are API-equivalent estimates, not subscription charges.
No paid fallback or budget-ledger change occurs.

| Native experiment | Attempts | Input | Cached input | Output | Reasoning | Catalog estimate USD | Case latency s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `matching` | 2 | 1,495 | 0 | 1,046 | 948 | 0.013450 | 12.25–17.16 |
| `support` | 2 | 1,436 | 0 | 1,075 | 996 | 0.013622 | 5.27–25.02 |
| `relationship` | 4 | 1,537 | 0 | 3,505 | 3,260 | 0.038124 | 7.41–61.78 |

Qualification remains **pending**, including unverified agent expectations and
unselected cases from the original full sources. Two repeated failures and two
corrected decisions do not establish a population error rate or qualify the
reviewers. The user subsequently authorizes drafting the proposed exception
clarification below for review before further calls. No lower-effort comparison,
bulk scoring, structural policy or reserved-test access is adopted by this result.

### DSSv2 exception clarification draft (October 9)

The user directs proceeding with the recommendation to address the repeated
support exception failure first and show a proposed prompt change before calls.
[DSSv2](support-prompt-v2.md) changes DSSv1's version header and adds only this
paragraph after the authoritative ASv6.100 excerpt:

```text
Apply qualifications from the complete post to any claim retained in
student_subject. Omitting an exception or condition while keeping that claim
is unsupported if it extends the claim beyond the cases the post supports.
Broader subjects that omit the claim itself can still be supported.
```

Both A20 failures retain the negative claim while discarding its Nostr exception;
the initial reason expressly treats this as permitted broader naming. The draft
clarifies why that broader negative claim lacks support. It preserves ASv6.100's
permission to name broader topics and actions without asserting that an event
occurred or importing every detail of its particular instance. A08's omission
of the hot-springs location and discovery time remains permissible under the
frozen expectation. These examples explain the draft here; they are not included
in the reviewer instructions.

Two agents independently find the paragraph consistent with the existing
ASv6.100 standard. This is an agent assessment of proposed wording, not a user
approval of DSSv2 or evidence that the reviewer will apply it correctly. The
known over-rejection risk is reading a topic, conditional or event heading as
an assertion; the unchanged authoritative heading guidance still applies.
The narrow clarification follows [OpenAI's guidance on straightforward reasoning
prompts](https://developers.openai.com/api/docs/guides/reasoning-best-practices).

Native `revise` preserves the complete diff and hash-bound provenance in
[the revision record](support-prompt-v2.md.revision.json). The two template
variables, verbatim AS rules, data handling and Boolean/reason output contract
are unchanged. DSSv1 and every previous experiment stay intact. No teacher
wording, source, expectation or model setting changes.

The offline A08/A20 preview uses the saved confirmation's exact cases and
settings under `target/distillation-review-v1/support-scope-dssv2-preview-20261009/`.
Native preparation validates the new template and source bindings without
inference. It cannot establish that the error is fixed or measure over-rejection;
the preview has no DSSv2 verdicts. These reused development cases cannot provide
an independent accuracy estimate.

The user subsequently approves the wording and bounded trial below. The earlier
offline preview stays unrun and intact. DSMv3, DSLv1, reviewer qualification,
final scoring, bulk adoption and sealed test data retain their existing status.

### DSSv2 bounded support trial (October 9)

After seeing the exact proposed paragraph, the user directs proceeding with the
bounded semantic test. DSSv2 is the approved wording for this test; its source
is unchanged from the draft. The scope is the 20 existing actual-output support
cases, three same-post controls, and a fresh DSSv1 comparison on the original
failure plus those controls. ASv6.100 remains trusted and is loaded verbatim.
Matching, parent-child review, lower-effort comparison, bulk grading, scoring
and reserved-test access are outside this trial.

The original support labels remain fixed at 17 true and three false; an
independent pre-call agent audit finds no new disagreement. The
[exception-control source](support-exception-controls-source.json) binds all four
definitions to A20's original saved generation and student number. Only the
authored `student_subject` varies; native preparation supplies the complete
original post and authoritative AS rules. Its labels are agent assessments,
not independently adjudicated gold:

| Case | Subject | Expected | Use |
| --- | --- | --- | --- |
| C00 | Social-media likes not being love | false | Fresh DSSv1 baseline; DSSv2 uses identical A20 |
| C01 | Social-media likes not being love, except on Nostr | true | Both versions |
| C02 | Social-media likes | true | Both versions |
| C03 | Social-media likes not being love, except outside Nostr | false | Both versions |

Schema-v2 `distillation_verdict` support definitions now accept an optional
nonempty `student_subject` variant. Original generation/number/source bindings
are checked first; the saved wording and authored variant stay separate in
review evidence. The variant changes only the supplied support subject, not
the source post or saved hierarchy. Relationship sources reject this option.
The [native spec](support-exception-controls-spec.json) reuses the Boolean/reason
schema and existing source loader. Expectations remain outside model input.

The new production-path tests first fail because the old adapter rejects the
variant field; the 12 verdict tests then pass, including native CLI preparation,
source/AS binding, malformed variants and separate expectations. The relevant
workflow run contains 164 tests: 158 pass and six optional artifact/UI checks
are skipped. Two matching tests initially lack the ignored training fixture in
the worktree; linking the unchanged canonical fixture makes both reruns pass.
Cached `uv` with `tiktoken==0.14.0` supplies the dependency missing from plain
Python. An earlier unscoped runtime run is stopped; no runtime suite pass is
claimed and no runtime dependency is installed.

The four experiments are under
`target/distillation-review-v1/support-scope-dssv2-trial-20261009/`:
`actual-other` has 17 DSSv2 cases; `actual-note27` has the three DSSv2 long-post
cases A07/A14/A21; `controls-v1` has C00–C03 with intentional fresh repetition;
`controls-v2` has C01–C03. These are 27 verdict calls, with one eligible native
warmup and a shared **56-attempt** budget allowing provider-only retries.
Sol / xhigh / subscription SSE / concurrency 8 remain fixed; batches never
exceed eight total initial in-flight calls.

Only A07/A14/A21's naturally shared prefix qualifies for warming (1,094
`o200k_base` proxy tokens). The A20/control prefix and other repeated posts are
below 1,024; none are padded or warmed. Current runner 1.2.1 (`e4550ea`) adds
post-response cost statistics, preserving request construction, retries, SDK
pin and warming behavior. Fresh preparations record its identity; the earlier
unrun DSSv2 preview is not resumed.

All experiments complete: **DSSv2 matches 20/20 actual support labels and 3/3
authored controls; fresh DSSv1 matches 4/4 controls.** All 27 decisions and their
decisive reasons receive current native agent reviews: 27 accept, zero reject,
zero uncertain. The same-post results are:

| Subject | Expected | Fresh DSSv1 | DSSv2 |
| --- | --- | --- | --- |
| Social-media likes not being love | false | false (C00) | false (A20) |
| Social-media likes not being love, except on Nostr | true | true | true |
| Social-media likes | true | true | true |
| Social-media likes not being love, except outside Nostr | false | false | false |

DSSv2's A20 reason correctly says that the subject retains the likes-not-love
claim while omitting its Nostr exception. The other reasons retain the exception,
allow the broader topic without that claim, and reject the reversed exception.
Previously accepted subjects remain accepted; A06/A12's unsupported actor and
response relationship remain rejected.

Fresh unchanged DSSv1 now also rejects A20/C00 correctly. Its request body,
method and URL are identical to the two earlier incorrect A20 calls. This is
further baseline inconsistency, not evidence that the clarification caused the
successful result. Both versions pass these controls on this trial; there is
no measured superiority between them.

The stage finishes at **28/56 attempts**: 27 verdicts and one native warmup,
all first attempts, without failure, retry, reuse or truncation. Frozen source
hashes, settings, strict JSON and receipt bindings verify against runner 1.2.1.
The earlier two-case preview and `note27-preview` remain unrun. Native usage is
copied separately for each experiment; output already includes reasoning:

| Experiment | Calls | Input tokens | Output tokens | Reasoning tokens | Catalog API-equivalent USD | Per-call seconds |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `actual-other` | 17 | 13,667 | 6,809 | 5,990 | 0.095424 | 4.522437–37.142527 |
| `actual-note27`, including warmup | 4 | 4,705 | 1,973 | 1,718 | 0.029140 | 10.860161–17.142386 |
| `controls-v1` | 4 | 2,875 | 2,906 | 2,712 | 0.034810 | 9.417157–54.902481 |
| `controls-v2` | 3 | 2,317 | 772 | 626 | 0.012354 | 6.467486–9.169293 |

Native per-request cost distributions, including warmup where present:

| Experiment | Mean USD | Median USD | p95 USD |
| --- | ---: | ---: | ---: |
| `actual-other` | 0.005613176470588236 | 0.004106 | 0.015720 |
| `actual-note27` | 0.007285 | 0.007292 | 0.008672 |
| `controls-v1` | 0.0087025 | 0.004904 | 0.021754 |
| `controls-v2` | 0.004118 | 0.004204 | 0.004210 |

Cache reads and writes are zero in every experiment. Note27's sole eligible
warmup uses 1,132 input, 362 output and 326 reasoning tokens; its catalog estimate
is **$0.005884**, included in the note27 totals above, with latency 13.511795
seconds. Native net cache savings are **−$0.005884 (−25.301%)**: zero comparison
hits, solely warmup overhead. The native uncached-comparison counterfactual is
$0.023256 versus the observed warmup-inclusive $0.029140. This holds observed
comparison tokens fixed; it is not a separately executed cold comparison.
Usage and catalog pricing are complete, but provider-reported cash charges are
unavailable. The subscription route has no paid API fallback and this stage
does not mutate the monetary ledger.

This is development evidence on previously used cases and authored controls.
Agent assessments are not independently adjudicated gold. Native qualification
remains pending on unverified expectations; split actual batches also retain
their unselected IDs as pending. This result establishes neither independent
population accuracy, repeat consistency for DSSv2 nor qualification for bulk
use. Matching and parent-child status remain unchanged. The remaining repeated
DSLv1 A21 error concerns adding a requirement to present the setup under
`Proof setup`. The user subsequently directs proceeding with the draft below,
for review before model calls.

### DSLv2 parent-restriction clarification draft (October 9)

The user authorizes the recommended clarification for the repeated DSLv1 A21
error, with proposed wording shown before calls.
[DSLv2](relationship-prompt-v2.md) changes only the version header and adds this
paragraph after the unchanged authoritative ASv6.100 rule:

```text
Do not add a requirement to present, explain or perform the parent's subject
unless the parent wording requires that action. A parent restriction may be
preserved anywhere in the child's meaning, including a clause or modifier;
a shared topic or mention that drops or changes a parent restriction is
insufficient.
```

Both A21 failures reject a proof subject that includes “after the setup with
directed univalence” beneath `Proof setup`. Their proposed counterexamples
assume the setup was already established or not presented. The parent adds
no presenting, explaining or performing action, so those changes do not remove
an expressed parent restriction. The clarification addresses that added
requirement and the retention of a restriction within a longer child's meaning.
This selected development example explains the draft here; it is not included
in the model instructions.

The paragraph does not permit keyword overlap to substitute for retained
meaning. An expressed action, purpose, modifier, negation or relationship still
restricts the child. Two independent agents find no conflict with trusted
ASv6.100; this is wording assessment, not a model result or user approval.
The practical risk remains accepting a mention that drops the parent's actual
meaning. Existing invalid controls for missing duration, renewed bans, excluded
people and cable length remain relevant to later testing.

Native `revise` records the exact full-context diff and hash-bound provenance in
[the revision record](relationship-prompt-v2.md.revision.json). The two template
variables, source-loaded verbatim rule, Boolean/reason contract and requirement
for an invalid verdict's counterexample remain unchanged. No adapter, source,
gold expectation, scoring rule, model setting or prior experiment is altered.
Each eventual call still contains one immediate pair plus fixed instructions;
this adds constant instruction text without new calls or hierarchy comparisons.
The narrow wording follows [OpenAI's guidance on straightforward reasoning
prompts](https://developers.openai.com/api/docs/guides/reasoning-best-practices).

Revision hash/variable checks pass; no experiment is prepared and no model is
called for this draft. Wording approval precedes a bounded semantic test of the
repeated failure, accepted contrasts and invalid controls. Actual A06's
anticipated-versus-realized ambiguity remains unresolved and its label stays
frozen. Qualification, DSSv2/DSMv3 status, bulk grading, lower-effort comparison
and sealed test data retain their existing status. The user subsequently approves
the displayed wording and bounded trial below.

### DSLv2 bounded parent-child trial (October 9)

After seeing the exact added instructions, the user directs proceeding with
the bounded semantic test. DSLv2 remains byte-for-byte the shown draft. ASv6.100
is trusted; support/matching prompts, sources, labels, scoring and sealed tests
are unchanged. Sol / xhigh / subscription SSE / concurrency 8 stay fixed.

The frozen scope is 19 original actual-output pairs, excluding already-ambiguous
A06, and all seven existing training controls TL01–TL03/LL01–LL04. A fresh
unchanged DSLv1 comparison uses the same A02/A13/A16/A21 pairs: one clear
invalid pair, two accepted contrasts and the repeated failure. This is 30
verdict calls, bounded by a shared 60-attempt counter allowing provider-only
retries with at most two attempts per case. No prompt or case is truncated.

The pre-call audit supports 18 actual labels and all seven training labels.
It additionally identifies interpretation-sensitive A12: “with David Marcus's
response” can naturally refer to the named warning, while the frozen false
label treats its target as unspecified. A12 keeps its saved label and is called
as separate evidence, outside the 25 uncontested DSLv2 assessments. This caution
is recorded before responses; neither A12 nor A06 is relabelled. Actual-output
expectations remain agent assessments, not independently adjudicated gold.

Native `prepare --from ... --repeat` preserves each exact pair, authoritative
rule, evidence and expectation, with the current runner 1.2.1 worker explicitly
selected. Experiments are under
`target/distillation-review-v1/parent-restriction-dslv2-trial-20261009/`:
`actual`, `teacher-controls`, `large-controls`, and `baseline-v1-paired`.
The initially inherited `baseline-v1` has A03 rather than intended A02 and stays
unrun; the paired preparation uses explicit selectors. A legacy cached teacher
plan rejects the revised prefix before preparation or inference; native
preparation instead reuses the uncached saved plan with identical pairs. Its
immediate baseline is unrun; earlier warmed results remain separate evidence.
All natural prefixes are below the warming threshold; there is no padding,
explicit prefix or warmup. Runtime/source binding checks precede calls.

The completed trial agrees with **24/25 assessed DSLv2 expectations**: 17/18
actual pairs excluding interpretation-sensitive A12, and all seven training
controls. A12 returns false, agreeing with its frozen label, but receives an
uncertain agent review and remains outside the assessed count. Native frozen-label
agreement includes it and is 18/19 actual pairs. Fresh unchanged DSLv1 agrees
with 3/4 paired expectations. Both versions still reject A21:

| Pair | Expected | Fresh DSLv1 | DSLv2 |
| --- | --- | --- | --- |
| A02: return lacking departure preparation and Dragon | false | false | false |
| A13: original article about the complete organization subject | true | true | true |
| A16: departure delay for the named airport | true | true | true |
| A21: proof after its directed-univalence setup | true | false | false |

DSLv2's new A21 reason says the child describes a proof rather than a setup and
that mentioning the preceding setup loses the parent's setup type. Its proposed
post nevertheless includes the same assumed directed-univalence setup. Root
and an independent agent reject this rationale under the approved clarification:
a clause may retain the restriction, and changing the main subject does not
demonstrate losing it. A03/A13/A16 provide accepted contrasts involving retained
clauses or modifiers. The wider distinction between a topical noun heading and
a main-referent type remains an interpretation question; neither this review
nor the frozen agent expectation independently adjudicates it.

Fresh DSLv1 again assumes setup without presenting it, repeating its earlier
presentation requirement. Its three successes and A21 failure match DSLv2 on
the identical paired inputs. The same original pair has now failed three fresh
DSLv1 calls and this DSLv2 call. This is no observed correction or measured
superiority from the clarification. All four invalid training controls retain
sound counterexamples for the missing duration, changed renewed ban, excluded
person and changed cable length.

All 30 returned decisions and reasons have current native agent reviews:
**27 accept, two reject, one uncertain**. Both rejects are A21, one per version;
A12 is the uncertain case. Mechanical validation and source/settings/receipt
checks pass. The persistent counter finishes at **30/60 attempts**; all calls
complete on first attempts, without reuse, retry, truncation or warmup. Native
review writes are refused while their experiment is active; the initially
refused root write changes no review and is recorded successfully after the
run closes. This is a workflow guard, not an inference failure.

Native usage is copied per experiment; output already includes reasoning:

| Experiment | Calls | Input tokens | Output tokens | Reasoning tokens | Catalog API-equivalent USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| `actual` | 19 | 8,133 | 8,056 | 7,107 | 0.096826 |
| `teacher-controls` | 3 | 1,243 | 1,815 | 1,681 | 0.020636 |
| `large-controls` | 4 | 1,895 | 1,417 | 1,114 | 0.017960 |
| `baseline-v1-paired` | 4 | 1,527 | 1,796 | 1,549 | 0.021014 |

Native per-request cost distributions:

| Experiment | Mean USD | Median USD | p95 USD |
| --- | ---: | ---: | ---: |
| `actual` | 0.005096105263157895 | 0.003098 | 0.021494 |
| `teacher-controls` | 0.0068786666666666675 | 0.002224 | 0.016192 |
| `large-controls` | 0.004490000000000001 | 0.004832 | 0.005312 |
| `baseline-v1-paired` | 0.0052535 | 0.005231 | 0.007394 |

Natural prefixes are 360 proxy tokens for each DSLv2 batch and 300 for DSLv1;
even the largest complete prompt is 482. No prefix reaches 1,024, so explicit
caching and warming are unused. Cache reads/writes and native net savings are
zero. Usage/catalog pricing are complete, while provider-reported cash charges
are unavailable. The subscription route has no paid API fallback; no monetary
ledger change occurs. The superseded `baseline-v1` preparation remains unrun.

The seven training controls pass native qualification; the actual and paired
baseline batches remain pending with A21 mismatches, unverified actual
expectations and unselected IDs. This reused development set cannot measure
independent population accuracy or establish bulk reliability. The approved
clarification has not resolved the observed failure at Sol/xhigh. The recommended
next step is to revisit how parent-child review uses the trusted teacher
hierarchy, including its already-correct examples of retained subject meanings.
This recommends investigation, not another prompt revision or model trial;
no new structural policy or review method is adopted here.

## Matching-only offline preview

The October 8 approval authorizes drafting and offline preparation of
[DSMv1](matching-prompt.md), before model calls. Each request contains one
generated subject and the fixed list of distinct saved teacher wordings for
that note. The task is to return the complete matching meaning's ID, or null,
with a brief reason. This isolates semantic matching from subject support,
parent restrictions and placement scoring. It does not replace the agreed
whole review process or establish that this call shape is best.

The `distillation_matching` adapter uses the existing hash-bound worked examples
and saved training answers. It bypasses earlier reviewer-generated groups and
required flags. Identical teacher strings share one opaque ID in first-occurrence
order; original numbers stay in evidence. Every distinct teacher wording,
including general headings and near matches, appears in the catalog. Matching
does not decide which meanings are required. Nonidentical teacher wordings are
not semantically regrouped here; these authored controls expect one unambiguous
match or none. Resolving equivalent nonidentical reference wordings would be
needed before using this as a production coverage procedure.

`MATCH_INPUT` contains only `teacher_subjects: [{id, subject}, ...]` followed by
one `student_subject`. The prompt excludes posts, ancestors, contexts, original
numbers, checkpoint/model identity, control labels and expected answers. It
requires the subject's own complete meaning: no filling gaps from other strings,
pooling partial matches, or choosing the nearest topic. Exact student strings
are excluded from model controls because code can preselect those matches.
Full teacher wording remains authoritative; ASv6.100 is not re-audited.

[matching-source.json](matching-source.json) defines 32 controls through source
references and explicit edits, with gold IDs and reasons kept in evidence.
There are 16 development controls and 16 confirmation controls, each with eight
matches and eight nonmatches. Their source notes are disjoint. Both sets include
worked examples and together cover all eight previously selected large training
answers, including the largest 72-wording catalog and the longest saved answer.
Edits test paraphrases, lost restrictions, quantities, polarity, attribution,
purpose and long nested/composite subjects. Expectations come from the authored
change, not a Sol response. These training references appeared in earlier
whole-note trials; confirmation is reserved for this new matching prompt,
not claimed as never-seen data for the entire investigation. Pilot final-test
answers remain sealed.

Prepare and inspect with `../experiment-runner/bin/experiment-runner` from
this Oracle checkout. The examples below use the shared launcher selected
by the user. Use an environment providing `tiktoken==0.14.0`, also used by
the existing bounded comparison workflow:

```sh
../experiment-runner/bin/experiment-runner prepare target/distillation-review-v1/matching-development-20261008 --spec sse_multivector/distillation-review-v1/matching-development-spec.json --repeat
../experiment-runner/bin/experiment-runner prepare target/distillation-review-v1/matching-confirmation-20261008 --spec sse_multivector/distillation-review-v1/matching-confirmation-spec.json --repeat
../experiment-runner/bin/experiment-runner show target/distillation-review-v1/matching-development-20261008 --case M01
../experiment-runner/bin/experiment-runner show target/distillation-review-v1/matching-development-20261008 --case M01 --prompt-only
```

Both specifications pin Sol / xhigh, subscription transport and concurrency 8.
`--repeat` prevents exact-response reuse from being mistaken for an independent
sample; later repeats would use separate preparations. Preparation alone does
not authorize inference; the subsequent authorized development trial is below.
Native reports count false matches, missed matches
and wrong IDs separately; malformed, incomplete and failed requests are ungraded
mechanical failures. Native usage accounting will retain actual input, cached,
output and reasoning tokens. Offline token counts
are an `o200k_base` rendered-text proxy, not provider usage or a cost estimate.
The fixed catalog precedes the varying target, but cache hits are not assumed.

At offline preparation, the two October 8 sets each had 16 pending cases, zero
attempts and zero reused answers. Development inputs total 16,518 proxy tokens
(439–1,849 per request); confirmation inputs total 16,000 (386–1,805).
The maximum catalog has 72 teacher wordings. These are the actual narrowed
inputs, not the full saved hierarchy's JSON size. Exact M01 uses the ten-item
cable catalog and `Cable A, two metres long`, with expected `T04` outside the
prompt. M05 uses the same catalog and `2 m cable A longer than 3 m cable B`,
with expected null because it loses the reference comparison's negation.

Passing 32 controlled examples would not establish pilot-wide accuracy or a
production error rate. Keep confirmation results out of
prompt development; any revision after inspecting them needs fresh independent
controls. Effort/batching comparisons and bulk grading remain subsequent
decisions. DSMv1 has not been adopted for bulk review.

## DSMv1 development trial (October 8)

After seeing the exact prompt and expected-answer preview, the user authorized
running the 16 development controls with Sol / xhigh and concurrency 8. The
frozen DSMv1 prompt, source edits and gold expectations were unchanged. The
shared CLI ran `matching-development-20261008` with an allowance of 32 attempts
for the existing provider-only retry policy; actual execution used 16 first
attempts, no retries and no response reuse.

All 16 reports are complete, mechanically valid and correct against the authored
expectations: all eight paraphrases match the correct ID and all eight near
misses return null. There are no false matches, missed matches, wrong IDs or
mechanical failures. Reasons were inspected individually: missing length,
changed quantities, reversed polarity, substituted identity and changed
prioritization remain decisive differences, including in the large catalogs.
Recorded per-request elapsed time ranges from 3.84 to 9.62 seconds.

Native usage reports 17,110 input tokens, zero cached input tokens and 1,822
output tokens, including 1,066 reasoning tokens. All attempts have saved SDK
usage. The catalog-price estimate is $0.05244; this subscription trial has no
provider-reported dollar charge, so that estimate is not an invoice. Raw provider
model/usage telemetry is present for 15 cases and reports Sol with zero cached
tokens; M30 retains complete normalized SDK usage but only HTTP status in its
raw response metadata. Requested model/effort and source-bound receipts remain
recorded for every case. Do not infer cache savings or batch/effort comparisons
from this trial.

Inspect the saved findings and measured usage without new calls:

```sh
../experiment-runner/bin/experiment-runner show target/distillation-review-v1/matching-development-20261008 --json
../experiment-runner/bin/experiment-runner show target/distillation-review-v1/matching-development-20261008 --case M06
```

This passes the initial controlled matching check, not production qualification
or an estimate of accuracy on actual distilled outputs. The user subsequently
accepted running the 16 separate-note confirmation controls with the unchanged
DSMv1 prompt and the same Sol / xhigh, concurrency 8 settings; see below.

## DSMv1 confirmation trial (October 8)

The accepted next step ran `matching-confirmation-20261008` through the shared
CLI. Its frozen prompt, teacher catalogs, edits and gold expectations were
unchanged after the development trial. All 16 reports are complete and match
the authored expectations: eight correct matches and eight correct nonmatches.
There are no semantic or mechanical failures, retries or reused answers.
The inspected reasons correctly preserve or reject the recipe restrictions,
ingredient/purpose, capital-flow origin, monetary limit, renewed-versus-first
ban, and age, including the long composite subject. Per-request elapsed time
ranges from 3.50 to 6.95 seconds.

Native usage reports 16,592 input tokens, zero cached input tokens and 2,007
output tokens, including 1,217 reasoning tokens. All attempts have saved SDK
usage. The catalog-price estimate is $0.053254, not a subscription invoice;
provider-reported dollar charge is unavailable.

```sh
../experiment-runner/bin/experiment-runner show target/distillation-review-v1/matching-confirmation-20261008 --json
../experiment-runner/bin/experiment-runner show target/distillation-review-v1/matching-confirmation-20261008 --case M13
```

Development and confirmation now pass 32/32 authored controls across separate
source notes, without prompt tuning on confirmation outcomes. This supports
the narrow matching approach on these controls; it does not establish an error
rate on actual distilled outputs or qualify the full review process. The user
subsequently authorized the proposed independent confirmation repeat; see below.

## DSMv1 independent confirmation repeat (October 8)

The user explicitly directed proceeding with the repeat to check whether fresh
calls stay correct. The shared CLI prepared
`matching-confirmation-repeat-01-20261008` from the first confirmation experiment
with `--repeat`. Offline checks verified identical prompt, case inputs and
expectations, source bindings, model/effort, schema and concurrency. All 16
requests were new; the saved baseline stayed outside the model input.

All 16 fresh reports are complete and correct, with the same teacher IDs/null
as the first confirmation trial. There are no semantic/mechanical failures,
retries or reused answers. Native text comparison marks 15 reports changed and
one unchanged: the explanations were reworded, while all semantic verdicts
stayed the same. Per-request elapsed time ranges from 4.43 to 8.45 seconds.

Native usage reports 16,592 input tokens, zero cached input tokens and 2,121
output tokens, including 1,353 reasoning tokens. Every attempt has saved SDK
usage. The catalog-price estimate is $0.054394, not a subscription invoice;
provider-reported dollar charge remains unavailable. This repeat measures
another generation on identical requests; it is not 16 new distinct controls
or an effort/batching comparison.

```sh
../experiment-runner/bin/experiment-runner show target/distillation-review-v1/matching-confirmation-repeat-01-20261008 --json
../experiment-runner/bin/experiment-runner show target/distillation-review-v1/matching-confirmation-repeat-01-20261008 --case M13
```

The 32 distinct controls pass, and the 16 confirmation verdicts remain correct
across two independent trials. Repeatability on these cases does not establish
accuracy on actual distilled wording or qualify subject support, parent
restrictions or branch coverage. The recommended next step is to prepare a
more realistic matching preview from actual distilled wording, with independently
verified expected matches fixed before Sol calls. The user subsequently authorized
offline preparation, documented below. Additional calls, effort/batching
experiments, full review adoption and final-test unsealing remain open.

## Complete-answer reviewer trial (October 9)

The user authorizes **50 randomized complete validation answers and ten difficult
complete answers**, using the actual mechanical decisions, semantic requests,
reuse and scoring process. **DSMv3/DSSv2/DSLv2**, trusted **ASv6.100**, **GPT-6.1
Sol / xhigh / subscription SSE / concurrency 8** remain fixed. This reviewer
trial uses validation data; the pilot's reserved test stays sealed.

The sealed [selection](../../target/distillation-review-v1/final-trial-20261009/selection/selection.json)
uses seed `DS-final-20261009`. Version quotas differ by at most one: two or three
answers from each of 18 versions. Random selection favors distinct notes absent
from earlier actual-output trials; all 50 chosen notes are previously unused.
Four truncated answers remain in the 50-answer denominator. The ten challenges
use ten distinct notes and cycle largest teacher catalog, nonexact composite
wording, deepest student hierarchy and same-note answer variation. Four challenge
notes were used before. Selection uses structural complexity without consulting
reviewer judgments. The cohorts are reported separately, and the randomized
cohort is not a uniform draw from all 1,800 answer outputs.

Teacher meanings are grouped and marked required independently of candidates,
using the approved complete-source-versus-derived-heading distinctions. Exact
teacher duplicates can be grouped mechanically; nonidentical paraphrases require
explicit assessment. Candidate judgments are separately assessed and frozen
before calls. These references are **agent-assessed**, not independently
adjudicated gold. Null support/link verdicts, null compatibility assessments and
explicit unresolved matching labels remain outside error denominators.

The complete workflow retains every subject and actual immediate edge. Exact
trusted subject wording settles matching and post support; exact trusted ordered
pairs, numbered ancestor paths or identical parent/child wording settle local validity. The remaining
questions use native requests and typed responses. Coverage additionally compares
each required teacher meaning, as child, with candidate headings, as parent,
using **unchanged DSLv2**. Identical requests share native results, while all
numbered placements remain visible. The existing scorer checks full matches
beneath every compatible occurrence, gives invalid outputs zero scores, and
keeps incomplete or inconsistent reviews pending. New evaluations apply the
[approved stopping rules](#additional-mechanical-review-work-approved-october-9)
instead of requiring every score-irrelevant placement verdict. The original
frozen evaluation retains its exhaustive contract. The earlier 36,310-question
estimate counted primitive checks and excludes these compatibility comparisons.

Caching follows the earlier trial's manual natural-prefix/key approach. Native
preparation selects prefixes only when they meet the existing 1,024-token policy
and have more than one distinct semantic request; native warmups precede their
comparisons. Automatic `--prompt-cache` is not used. The shared runner owns
execution and receipt accounting; eligible prefixes do not guarantee hits.
One native evaluation command executes the prepared groups sequentially, with
eight requests per group and one shared new-attempt allowance including warmups
and provider retries. Usage counts original receipt lines once rather than
counting copied judgments as calls.

The reusable native commands are available through
`experiment-runner/bin/experiment-runner` with a `tiktoken`-enabled Python:

```sh
experiment-runner prepare-distillation-review-trial MANIFEST \
  --model-output QWEN --model-output GEMMA_DENSE --model-output GEMMA_MOE \
  --random-count 50 --hard-count 10 --seed DS-final-20261009 --output SELECTION_DIR
experiment-runner show-distillation-review-trial SELECTION_JSON --answer R01 --teacher-only
experiment-runner assess-distillation-review SELECTION_JSON --answer R01 \
  --directory ASSESSMENTS --teacher-meanings GROUPS_JSON --reason REASON
experiment-runner assess-distillation-review SELECTION_JSON --answer R01 \
  --directory ASSESSMENTS --wording-expectations LABELS_JSON --reason REASON
experiment-runner freeze-distillation-review-assessments SELECTION_JSON --directory ASSESSMENTS
experiment-runner prepare-distillation-review-evaluation SELECTION_JSON \
  --assessments ASSESSMENTS --output EVALUATION_DIR
experiment-runner run-distillation-review-evaluation EVALUATION_DIR --max-new-attempts LIMIT
experiment-runner show-distillation-review-evaluation EVALUATION_DIR --output REPORT_JSON
```

`--required-numbers` with `--optional-numbers` is a compact alternative for
explicitly classifying every distinct exact teacher wording. No unlisted meaning
defaults to optional. `--wording-expectations` expands only identical student
wording or identical ordered edge inputs; every distinct input still needs a
judgment. `--expectations` accepts complete numbered arrays. Existing source
files and frozen assessments cannot be overwritten.

Preparation and all references are sealed before calls. The 60 answers share
54 distinct teacher contexts: six challenge notes also occur in the randomized
cohort, with different answers. All **958 mechanical decisions** have independently
verified exact teacher witnesses or identical-string rule proofs. Thirty-four
compatibility occurrences retain unresolved agent labels despite their valid
mechanical proofs; those labels remain excluded from reference-agreement denominators.

**Completed matching and support; relationships paused.** The unchanged
native trial has these frozen-reference results, excluding mechanical cases:

| Check | Resolved distinct agreement | Distinct disagreements | Unresolved distinct inputs | Resolved occurrence agreement |
| --- | --- | --- | --- | --- |
| DSMv3 | 569/591 | 22 | 24 | 1,753/1,810 |
| DSSv2 | 585/600 | 15 | 15 | 1,724/1,808 |

Each check additionally passes all 258 mechanically settled occurrences.
Independent cross-author audits classify matching's 22 disagreements as eight
reference mistakes, four clear reviewer errors and ten ambiguities; support's
15 as seven reference mistakes, four clear reviewer errors and four ambiguities.
The **37 native agent reviews** preserve input/output hashes and attribution.
Frozen labels are unchanged: these later classifications do not rewrite raw
qualification or turn ambiguous reference agreement into accuracy.

Matching errors include dropping a literal grid representation and accepting
added recipient/speech-act restrictions. Support errors include rejecting the
audience nickname `Cupcakes` and the information sense of `Intelligence`, while
accepting two specifically attributed constructions with the unresolved pointer
`the relevant categories`. Relationship auditing has also found two disjoint
logical-inconsistency families, each guaranteeing at least one wrong verdict
without identifying every involved call as erroneous. Scoring blockers remain
explicit `inconsistent_verdicts`; no score is invented for them. Full score
assembly and final qualification await the relationship phase.

The completed checks used **1,230 semantic calls, nine warmups and one failed
transport attempt followed by its allowed successful retry**, plus 2,528 reused
judgment copies. Matching reports 288,768 cached input tokens: **42.14%** of
comparison input, or **41.44%** including its eight warmups. Support reports no
cache hits despite its eligible warmup. Across both checks and nine warmups,
cached tokens are 23.70% of **reported** input tokens; the interrupted attempt
has unknown usage and is excluded, rather than counted as zero. Complete cost
remains unknown. Subscription SSE, prompts, effort and caching policy are
unchanged; bulk review and the pilot's reserved test remain unapproved/sealed.

**User-requested pause for scalability:** the coordinator stopped new dispatch,
allowed its already-submitted workers to finish, then exited. All receipts and
frozen inputs are retained; no worker remains. The
[paused native report](../../target/distillation-review-v1/final-trial-20261009/evaluation/paused-report.json)
records 870 distinct successful relationship inputs. Only 808 are joined to
every selected occurrence: 62 further inputs can reuse existing receipts, and
9,664 require new model work. Relationship execution used 875 original attempts:
870 distinct successes, two extra successful duplicate dispatches following
transient failures, and three failed attempts with successful allowed retries.
All checks together used 2,115 original receipts, including nine warmups, plus
3,674 reused copies. Four failed attempts have unknown usage. Reported
input is 1,306,730 uncached plus 288,768 cached tokens (18.10% cached), with
753,026 output tokens including 637,606 reasoning tokens. The known catalog
estimate is $10.1725968; complete cost remains unknown.

The original frozen 60-answer plan needs 2,086 distinct primitive requests, plus 9,678
additional coverage-placement requests: 11,764 total. Required teacher meanings
are compared against every returned subject, before mechanical settlement and
identical-request reuse. Those additional requests account for 82.27% of the
trial workload and were absent from the earlier full-validation runtime estimate.

Read-only investigation of the existing coverage score law finds 278 of 513
required-meaning/answer groups have no complete match under the saved DSM
decisions. Their coverage fails regardless of compatibility. Omitting only their
compatibility work would reduce the entire selected workload by 5,764 distinct
requests, retaining uses needed for actual edges: 11,764 to 6,000. This is a
conditional whole-workload count, not outstanding work saved or proof that DSM
is correct. Current exhaustive compatibility diagnostics and reviewer
qualification also depend on those judgments. The subsequent approval and
implementation follow; the trial remains paused and its original receipts are
unchanged.

## Additional mechanical review work approved (October 9)

The user directs doing all sensible mechanical work. New evaluation preparations
use schema 2 and apply these score-preserving rules, conditional on completed
matching/support and any saved semantic verdict used as evidence:

- No complete student match: the required teacher meaning's coverage is zero;
  omit its remaining compatibility questions.
- A full match already occurs below a student subject: that subject's
  compatibility cannot change coverage; omit that question. Retain compatibility
  checks for the matching entries themselves to detect DSM/DSL contradictions.
- A compatible student subject has no full match beneath it: coverage is zero;
  stop the other placement questions for that meaning, retaining matching-self
  checks. A trusted teacher proof can provide this witness without inference.
- Post support is false: that student's correctness contribution is zero;
  omit its incoming-edge question. This does not settle descendants' correctness.

Exact trusted ancestor paths additionally supply positive DSL verdicts. On the
same 60 selected answers, they prove 325 additional distinct inputs across 393
numbered occurrences; 28 already have outputs and 297 remain uncalled. A frozen
C01 agent expectation conflicts with one path proof; the raw label is preserved.
Teacher absence does not prove a negative when an equivalent paraphrase might
appear elsewhere: 1,635 investigated negative candidates remain unproven and
are not used. DSM matches do not settle DSS support or post-free DSL validity.

The shared runner's `run(..., only=..., warm_cache=...)` dispatches selected
frozen cases and retains its complete native report. The evaluator completes
matching and support first, then checks required actual edges, matching-self
guards and one remaining placement per unresolved meaning per wave. It retains
concurrency 8, native exact-request reuse and provider-only lifetime retries.
Before fresh DSL work, it joins every receipt-validated reusable DSL input with
a zero allowance. A cached positive witness can therefore settle coverage before
a fresh earlier case is queried. The shared request preview supplies verified
case IDs; unknown first cases cannot block later reusable witnesses.
An eligible prefix is warmed at most once per group in one evaluation invocation;
later waves retain the same cache identity without additional warmups.

Skipped rows have `status: "skipped"`, a rule and dependency evidence, no semantic
Boolean and no successful qualification. Native records and already completed
judgments remain intact. Required aliases of the same request are dispatched
together; another occurrence can obtain a native reused result at no extra
call. `score_partial` applies the unchanged score law without inventing a complete
DSR report. Reports distinguish complete scores from incomplete diagnostics and
reviewer qualification; matching-self contradictions still block scores.

The [saved workload investigation](../../target/distillation-review-v1/final-trial-20261009/analysis/score-law-eliminations.json)
projects 11,764 original distinct requests to 5,201 with all measured reductions,
given the paused matching/support decisions and known DSL witnesses. This is
whole-workload potential, not past calls refunded or an accuracy/runtime estimate.
It leaves 3,565 genuinely new DSL inputs rather than 9,664, before additional
stopping on future outputs, warmups and retries. Frozen teacher groups, required
flags, prompts, reasoning effort and cache eligibility are unchanged.

Original schema-1 selections retain immediate-edge/equality accounting during
verification; new schema-2 selections count ancestor proofs. Original selections,
assessment seals, evaluations and receipts are never rewritten. Prepare a new
evaluation with the same selection/assessments and the previous history root.
Frozen schema-1 answer assessments retain their original immediate/equality
proof validation, including labels newly contradicted by ancestor proofs. New
schema-2 answer assessments validate the expanded proofs before freezing.
`run-distillation-review-evaluation --max-new-attempts 0` joins verified saved
receipts with no new model attempts; a later positive allowance is required for
new inference. At that checkpoint the trial remained paused; bulk qualification
remained open and the reserved test stayed sealed.

Production-path tests first reproduced unnecessary dispatch and frozen-selection
accounting failures. The integrated review suites now pass 112 tests; selected
runner dispatch and verified reuse pass 67 Python and 74 Node tests with local
workers. Tests cover
positive and negative witness termination, required self guards, actual/placement
aliases, shared budgets and resume, eligible caching, zero-allowance reuse, frozen
byte preservation and the original exhaustive scorer. These checks establish
mechanical behavior, not semantic reviewer accuracy.

**Native confirmation, October 9:** prepared a separate schema-2
[`evaluation-mechanical`](../../target/distillation-review-v1/final-trial-20261009/evaluation-mechanical/evaluation.json)
from the original 50 random and 10 challenge answers, frozen assessments and
previous history root. The stable runner joined verified saved answers with
`--max-new-attempts 0`. Its
[`receipt-only-report.json`](../../target/distillation-review-v1/final-trial-20261009/evaluation-mechanical/receipt-only-report.json)
confirms 3,565 distinct new DSL inputs remain, versus 9,664 at the original
pause: 6,099 fewer, or 63.1%, before further stopping and retries. Matching and
support have no remaining requests. There are 19,968 explicitly skipped DSL
occurrences; these are numbered rows, not distinct calls. New model attempts,
tokens and warmups are zero. Existing reviewer contradictions and the C01
expectation conflict remain visible; this receipt join does not qualify semantic
accuracy. The original selection, assessment seal, paused native receipts and
bound source files are unchanged. At the receipt-only checkpoint the actual
trial remained paused; the next approval resumes it.

## Reasoning-level comparison approved (October 9)

The user authorizes completing the same 50 random and 10 challenge answers at
`gpt-6.1-sol/xhigh`, then testing lower reasoning levels on a small subset and
expanding the lowest promising level until all 60 answers are complete. If
performance degrades significantly during expansion, stop that level, step up
one level and continue. The user explicitly accepts at most **2 percentage
points of correctness loss versus xhigh**. This replaces the earlier pause;
bulk pilot grading and reserved-test access remain unapproved.
The final choice is one reasoning level used for all three checks.

Compare reviewer decisions against source evidence and assessed references.
The student `correctness` score is a different quantity. Exact mechanical
decisions and repeated occurrences cannot inflate the semantic accuracy
denominator. Report matching, support, actual edges and compatibility separately,
with random and challenge cohorts distinguished. Xhigh is a comparison baseline,
not an independent gold reference: investigate substantive disagreements using
the trusted teacher, original post and approved rules. Existing frozen labels,
unresolved judgments and known reference contradictions remain intact.

The implementation will screen high, medium and low on the same prespecified
small subset, then expand through nested subsets to all 60. Adaptive stopping
can change which DSL inputs each effort executes; a fixed paired diagnostic pool
and targeted native checks of differing inputs must accompany pipeline results.
An unpaired agreement percentage is insufficient to select an effort. Small
screens identify candidates; they do not establish the final loss bound.

Keep the model, prompt versions, post/teacher/student wording, semantic rules,
concurrency 8, provider-only retries and natural-prefix caching policy fixed.
Request identity includes reasoning effort, so xhigh answers cannot substitute
for lower-effort inference. Report actual cached tokens, warmups, reasoning
tokens and runtime separately. OpenAI documents
[model-dependent effort support](https://developers.openai.com/api/docs/guides/reasoning)
and recommends
[task-specific comparisons with typical and difficult examples](https://developers.openai.com/api/docs/guides/evaluation-best-practices).
Source preparations and study choices freeze before lower-effort calls.

Native preparation accepts `--reasoning-effort high|medium|low|xhigh`; absent
that option it preserves the selection's original effort. The run command
accepts repeated `--answer-id` values using stable source answer IDs, not the
`R01`/`C01` display aliases. It dispatches only those answers while retaining
the complete 60-answer report. Unknown or duplicate IDs fail before calls.
This permits nested subsets without rewriting a frozen selection or native
case manifest. Supplemental paired diagnostic cases use native `run --only`
in the corresponding prepared check group; the scorer's stopping rules and
frozen labels stay unchanged. The effort override and subset production paths
passed all 117 tests across the seven distillation-review modules.

The prespecified screen uses `R01`, `R02`, `R03`, `C01` and `C06`: three random
answers covering all three distilled-model families, plus two challenge
answers with both supported and unsupported wording. Remaining answer order
uses the fixed `DS-effort-screen-20261009` hash seed, independently of lower
effort outputs. Nested stages contain 5, 10, 20, 40 and 60 answers, with
random/challenge counts 3/2, 8/2, 16/4, 32/8 and 50/10.

Every stage includes all distinct nonmechanical DSMv3 and DSSv2 inputs for its
answers. The initial DSLv2 screen deliberately covers positive and negative
assessed examples. For each later answer, sample up to four distinct actual
edge inputs and four compatibility inputs by source-seeded hash, without
consulting labels, reference status or model outputs. Deduplicate exact
rendered prompts while retaining every alias, role and source. The nested
paired panels contain 297, 405, 713, 1,253 and 1,735 prompts. The full panel contains
615 matching, 615 support and 505 relationship prompts; the actual-edge and
compatibility subsets overlap and are not additional overall samples.
The fixed panel supplements the approved adaptive pipeline; it does not
require a full Cartesian set of compatibility comparisons.

Save each stage's native pipeline report before supplemental diagnostics,
then a separate report afterward. Some diagnostic questions were unnecessary
for the pipeline's scores; their tokens and runtime must not inflate estimates
of production review work. Bridge only exact panel inputs that still lack a
verified receipt after each pipeline finishes. The receipt-only snapshot's
potential xhigh bridge count is a worst case, not the final paid call count.
Unknown reference aliases remain unknown even when another identical input
has a resolved assessment. The initial label-balanced stress panel, uniform
extension, random cohort and challenge cohort need separate summaries.

Freeze the chosen xhigh verdict and verified receipt for every full-panel
prompt before lower-effort calls. Later stages subset that frozen baseline;
they cannot select a more favorable successful receipt. Preserve conflicting
alias outputs and require complete paired responses. Normalize matching IDs
only within the frozen teacher-meaning groups. Source-adjudicate every
normalized disagreement, including those where existing labels favor xhigh.
Identical verdicts cancel in relative accuracy even when both are wrong;
absolute accuracy is a separate, unqualified claim.

Offline receipt validation and paired comparison live in the tracked
[effort analysis module](../distillation_review_effort_analysis.py). Invoke
`python3 -m sse_multivector.distillation_review_effort_analysis` with an explicit
`--panel PANEL.json`. To compact and freeze a complete xhigh native report, add
`--compact REPORT.json.gz --effort xhigh --freeze-baseline --output BASELINE.compact.json.gz`;
the output path must be new and every panel prompt must have a valid receipt.
For a paired stage, use `--stage 5 --report xhigh=BASELINE.compact.json.gz --report high=HIGH.json.gz --output PAIRED.json.gz`.
Reports and compact snapshots support JSON or gzip. The output preserves receipt
references, selected alias note IDs, role/cohort overlap and unresolved references;
`missing_native_pool_cases` lists native experiment paths and case IDs for
supplemental `run --only`. Missing responses or conflicting normalized verdicts
block comparison. Run its checks through
`python3 -m unittest sse_multivector.test_distillation_review_effort_analysis`.

For paired count `N`, let `H` be baseline-correct/candidate-wrong decisions,
`G` baseline-wrong/candidate-correct decisions and `A` unresolved discordant
truths. Report relative loss `(H-G)/N` and conservative truth range
`[(H-G-A)/N, (H-G+A)/N]`. This range is not a statistical confidence interval.
At the full panel, its upper endpoint must be at most 2 percentage points, requiring
`H-G+A <= 34` on the 1,735-prompt panel. Report sampling uncertainty separately;
this selected panel does not establish population noninferiority.

Before promotion, investigate a role whose source-adjudicated relative loss
exceeds 2 points, or a new specific restriction error recurring on at least
two distinct notes. Record the pattern and higher-effort comparison. This is
an investigation trigger, not a stricter per-role numerical margin. A large
relationship regression cannot pass unnoticed because matching/support
contribute most of the panel. Clear recurring failures require stepping up;
small screens and borderline losses justify further investigation or
expansion, never a final qualification claim.

For composition sensitivity, group answers by source teacher context, join
contexts sharing an exact panel prompt, and delete each whole connected
component in turn. Recompute loss and truth bounds on the remaining distinct
prompts; report their range and largest change, without calling it a confidence
interval. The full panel has 51 valid source contexts and 50 such components.
Four invalid student answers remain pipeline cases, not semantic accuracy
successes. [Paired NLP evaluation guidance](https://aclanthology.org/P18-1128.pdf)
discusses bootstrap representativeness and dependent observations; this
selected, partly deliberate panel does not justify a population guarantee.
Composition sensitivity also cannot measure fresh-call variability or remove
the optimism from selecting the lowest promising effort across repeated stages.

### Xhigh completion and baseline freeze (October 10)

The resumed native pipeline finished with **43 complete scores, 13
`inconsistent_verdicts` answers and four invalid student outputs** across the
same 60 selected answers. All requested native judgments have validated
receipts; a validated JSON response does not establish semantic correctness.
The score guard refuses to grade an answer when matching accepts a required
teacher meaning but its DSL compatibility judgment rejects the same teacher
wording/student wording pair. These 13 answers contain 140 conflicting
occurrences, deduplicated to 30 matching prompts and 30 relationship prompts.
Independent source-only diagnosis is in progress. Existing references, prompts
and the guard remain unchanged.

Finishing the mechanical pipeline made 3,250 fresh successful attempts for
3,242 distinct request identities and 24 transient provider failures, all
recovered by the native second attempt. Eight alias/retry identities have
duplicate successful receipts with agreeing normalized verdicts; preserve
their paid attempts. The 6,963 saved-answer reuse rows are neither fresh calls
nor prompt-cache hits. The recorded coordinator birth and terminal observation
span **4 h 7 min 51 s**. These counts describe the completion phase, excluding
the earlier calls behind saved-answer reuse.

The completed pipeline still lacked 187 exact prompts required by the fixed
full comparison panel because its scoring rules had skipped them. Native
history supplied 25 verified answers; the supplementary dispatch made 162
fresh successful calls and recovered one transient failure on its second
attempt. Its coordinator birth and terminal observation span **8 min 32 s**.
Keep this diagnostic work separate from production pipeline work.

At **2026-10-10 08:15:24 UTC**, before any lower-effort inference, offline
validation froze **all 1,735 chosen xhigh decisions**, with zero missing or
conflicting normalized responses. This completeness does not qualify xhigh's
absolute accuracy or resolve the 13 scoring contradictions. Lower efforts
compare against these exact chosen receipts.

The separate read-only
[mechanical proof audit](../../target/distillation-review-v1/final-trial-20261009/analysis/baseline-mechanical-proof-audit.json)
found no violations in the checked records: **1,351 positive proofs and 20,376
skip dependencies** retain the required source bindings, equality or ordered
teacher-path evidence, and recorded dependency states. It also checked **573
full-match compatibility guards**; 140 false occurrences preserve the 13
ungraded answers. The 43 complete, 13 inconsistent and four invalid answer
counts remain unchanged. These checks do not adjudicate semantic model
decisions or audit the trusted teacher semantics.

The audit found 148 skips with recorded reused-positive witnesses. The sealed
final snapshot does not establish historical zero-budget join counts, timing
or pre-stopping transitions. No inference, replay, source fix or rubric change
was made. The audit SHA-256 is
`cf40e810c7730aecb6aa4b6eb295dbb0a4d1a32e15e3394d3cd12c84a5086785`.

Evidence lives in ignored trial artifacts: the
[pipeline report](../../target/distillation-review-v1/final-trial-20261009/evaluation-mechanical/baseline-xhigh-report.json),
[post-bridge report](../../target/distillation-review-v1/final-trial-20261009/evaluation-mechanical/baseline-xhigh-post-bridge-report.json),
[freeze seal](../../target/distillation-review-v1/final-trial-20261009/analysis/baseline-freeze-complete.json)
and [source-diagnosis queue](../../target/distillation-review-v1/final-trial-20261009/analysis/baseline-source-adjudication-queue.json).
The frozen compact snapshot SHA-256 is
`004f0beaeba8043041056289286704607ee131f6a5de417588fa86f11cdc585e`.

## Initial high-effort screen (October 10)

The fixed five-answer screen at Sol/high is complete: **289 of 297 decisions
agree with the frozen xhigh baseline**, with eight discordances and zero missing
or conflicting panel decisions. Agreement is not correctness. Revised
source adjudication finds **six high-only errors and two unresolved differences
(H=6, G=0, A=2)**. Overall correctness loss is bounded by **4–8 of 297 decisions**,
or **1.35–2.69 percentage points**. Matching has two unresolved differences over
89 decisions, giving a possible loss of −2.25 to 2.25 points. Support loses
2/89 decisions (2.25 points), teacher/student compatibility loses 3/64
(4.69 points), and actual student parent-child pairs lose 1/61 (1.64 points).
The distinct DSLv2 pool combines
the latter two roles with six overlapping prompts: 4/119 losses (3.36 points).
High has not cleared the conservative two-point margin and has role-level
concerns.
At this checkpoint lower-effort screening continued; no reasoning level had
qualified. The
[revised source assessment](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-5-high-source-assessment-revision-2.json)
preserves each exact-prompt truth and original evidence. Its SHA-256 is
`939820622a81cdc8b792ef8e0c433aa4734384c176e574fede21a4d02b139a39`.
Its bounds express truth uncertainty, not statistical confidence or reliability
beyond these five deliberately selected source contexts.

The first assessment counted J73d2851a623d930327631f02 as a high correction:
`Price-sensitive industrial users` matched T39,
`Price-sensitive industrial electricity users`. A fresh exact-prompt policy
audit could not settle whether the post interprets what `users` implicitly use
or supplies an omitted electricity restriction. The
[revised adjudication](../../target/distillation-review-v1/final-trial-20261009/analysis/semantic-adjudication/adjudications/J73d2851a623d930327631f02-revision-2.json)
therefore counts this difference as unresolved; its SHA-256 is
`8b804142243eec1c0553847c7593ae2365f7d3bfce8a832e7863ed377db13051`.
All original judgments, reviews and the first assessment remain preserved.
This correction changes no prompt, reference or mechanical rule.

The high production pipeline took **1 h 6 min 42 s**, with 718 successful
comparison attempts, three transient failures recovered on the second attempt,
two eligible-prefix warmups and 1,869 saved-answer reuse rows. Its known catalog
subtotal is **$1.717396**; missing failed-attempt usage prevents a complete cost.
The separate fixed-panel supplement took **1 min 48 s**, with 48 successful
calls and a catalog estimate of **$0.163702**. These are API-equivalent catalog
estimates, not subscription charges. Dependency processing and verdict-dependent
branching also affect wall time; these observations do not isolate reasoning
effort's effect on cost or runtime.

All 60 original source-only diagnostic judgments have been saved. Those initial
votes are not gold: independent review and concrete counterexamples can revise
them. Final exact-prompt adjudications are separate artifacts, preserve every
original, and can be reused across efforts. Unresolved differences contribute
the conservative accuracy bound; they are never forced into a verdict. Student
scores and raw agreement cannot substitute for this process.

The [high screen seal](../../target/distillation-review-v1/final-trial-20261009/evaluation-high/stage-5-complete-execution.md)
binds the separate pipeline, supplement and final paired reports. The paired
report SHA-256 is
`006553bc45f5a5915967931666cecc4b399f9d5205740f94fe95def3e761dd6f`.
Prompts, mechanical rules, frozen references, concurrency 8 and natural-prefix
caching remain fixed. Correctness qualification and bulk adoption remain open.

## Initial medium-effort screen (October 10)

The same fixed five-answer screen at Sol/medium is complete: **285 of 297
decisions agree with the frozen xhigh baseline**, with 12 discordances and zero
missing or conflicting panel decisions. Source adjudication finds **H=8, G=2,
A=2**, giving a correctness-loss range of **4–8 of 297 decisions**, or
**1.35–2.69 percentage points**. This is the same overall range as high;
agreement does not establish correctness. Role results are:

| Role | N | H | G | A | Loss in percentage points |
| --- | ---: | ---: | ---: | ---: | ---: |
| Matching | 89 | 0 | 0 | 1 | −1.12 to 1.12 |
| Post support | 89 | 1 | 0 | 0 | 1.12 |
| Actual student parent-child pairs | 61 | 3 | 0 | 1 | 3.28–6.56 |
| Teacher/student compatibility | 64 | 5 | 2 | 0 | 4.69 |

The relationship roles share six exact inputs; the overall count includes each
once. The
[source assessment](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-5-medium-source-assessment.json)
has SHA-256
`9bb53e5476200db1ed257dd88138f0cb3d805d275cfa35bd15c3ef5abde28da3`.
Its bounds express truth uncertainty, not confidence intervals or population
reliability; the five deliberately balanced source contexts remain a small
screen, and initial reference labels are not gold.

The medium pipeline took **58 min 39 s**, with 714 successful comparison
attempts, one transient failure recovered on the second attempt, two eligible
prefix warmups and 1,866 saved-answer reuse rows. The five selected answers
yield two complete scores and three ungraded `inconsistent_verdicts`; none is
operationally pending or invalid. The separate panel bridge took **1 min 27 s**
and made 49 fresh successful calls, with no failures, reuse or warmups. See the
[medium screen seal](../../target/distillation-review-v1/final-trial-20261009/evaluation-medium/stage-5-complete-execution.md)
for the separate pipeline, supplement and paired reports. Missing usage for
the pipeline failure prevents a complete pipeline cost.

For the identical 297 frozen chosen responses, the catalog estimate falls from
**$1.4758404 at xhigh to $0.6227392 at medium**, or **57.8% lower**. Both contain
243,833 total observed input tokens. Cached input is 33.23% at xhigh and 28.82%
at medium; output falls 76.48% and reasoning falls 88.81%. Output already
includes reasoning. These are API-equivalent catalog estimates, not actual
provider charges. The
[fixed-panel cost analysis](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-5-medium-fixed-panel-cost-analysis.json)
has SHA-256
`39274eccb6c80addd3e1276091f735dd6b763cf47967428f4528cf93e0c2c4d3`.
It preserves original paid receipts, historical baseline calls and shared
warmups separately. Complete costs including xhigh's failed attempt remain
unknown. Cache availability, history and adaptive branching differ, so these
observations do not isolate reasoning effort's effect on cost or wall time.

The [high/medium gate audit](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-5-high-medium-gate-audit.json)
records the role concerns and found no specific recurring failure across two
distinct notes in this screen. Its SHA-256 is
`1953c597a39601a48cce8dd418f4a1e9ecedfe14215d2a9ccd0b8eea051d1714`.
This is an investigation record, not promotion authorization. The completed
low screen and selected next investigation follow below. The approved study
controls and full xhigh freeze remain unchanged.

## Initial low-effort screen and next-stage selection (October 10)

The same fixed five-answer screen at Sol/low is complete: **283 of 297
decisions agree with the frozen xhigh baseline**, with 14 discordances and no
missing or conflicting panel decisions. All 14 differences have final source
assessments: **H=10, G=1, A=3**. The correctness-loss range is **6–12 of 297
decisions**, or **2.02–4.04 percentage points**. Even the optimistic endpoint
exceeds the agreed two-point margin. Role results are:

| Role | N | H | G | A | Loss in percentage points |
| --- | ---: | ---: | ---: | ---: | ---: |
| Matching | 89 | 0 | 1 | 1 | −2.25 to 0 |
| Post support | 89 | 1 | 0 | 0 | 1.12 |
| Actual student parent-child pairs | 61 | 6 | 0 | 1 | 8.20–11.48 |
| Teacher/student compatibility | 64 | 5 | 0 | 1 | 6.25–9.38 |

The relationship roles share six exact prompts, including two harmful
differences; each counts once overall. Their distinct combined pool contains
119 decisions, with H=9, G=0, A=2 and a 5.88–9.24-point loss range. The
[low source assessment](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-5-low-source-assessment.json)
has SHA-256
`7e3d7964ce5e2f089ae1a16f9c3065f4671653448d65c7bd6ebaf74d44be407e`.
These bounds retain unresolved source truth; they are not confidence intervals
or population guarantees. Initial reference votes are not gold.

J73's latest revision and J804/J001 remain unresolved. The
[provisional-to-final reconciliation](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-5-low-provisional-final-reconciliation.json)
verifies all 178 matching/support chosen decisions and receipt sets against
the final panel, allowing Jd806's accepted source correction to count as G.
Original judgments, receipts and reconciliation flags remain preserved;
the separate proof closes the final-receipt requirement. Its SHA-256 is
`9e3d619650a853a6fc766cc44ee689d8983c1028afb501cd3eff2331b6f5043f`.

The [specific failure audit](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-5-low-restriction-pattern-audit.json)
finds low adding a requirement that a post be, present or perform the parent
subject, although the child preserves that meaning in a clause or instruction
object. Three distinct harmful prompts establish this error across **R01 and
R02**, two distinct notes. Repeated paths within R02 and two prompts within
R01 do not add independent notes. Medium and high also fail some R01 cases,
but preserve the R02 pair; this specific two-note recurrence is established
for low. The audit SHA-256 is
`c1d778efb639806716cd48f25053c88d3a70813ed9bfbcfc6f941ae6dfb21ee8`.
The [final independent three-effort audit](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-5-effort-selection-audit.json)
checks every current disagreement, revision and role count; its SHA-256 is
`aa661fd7351f2281ea5bf527d0c3d28a4847cbf5f9ea4bc36ecc4f5bc230ec83`.

The low pipeline took **58 min 43 s**, with 714 successful comparison attempts,
one transient failure recovered on the second attempt, two eligible-prefix
warmups and 1,866 saved-answer reuse rows. The separate panel bridge took
**64 s**, with 49 fresh successful calls and no failures, reuse or warmups.
Its [execution seal](../../target/distillation-review-v1/final-trial-20261009/evaluation-low/stage-5-complete-execution.md)
preserves separate reports. The five pipeline answers yield two complete
scores and three ungraded `inconsistent_verdicts`; none is pending or invalid.

For the identical 297 frozen chosen responses, the API-equivalent catalog
estimate falls from **$1.4758404 at xhigh to $0.552834 at low**, or **62.54%
lower**. Total observed input is 243,833 tokens at both efforts; cached input
is 33.23% at xhigh and 30.71% at low. Output falls 81.84% and reasoning falls
94.95%; output already includes reasoning. The
[low fixed-panel cost analysis](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-5-low-fixed-panel-cost-analysis.json)
has SHA-256
`349da31c2e160225fa4a37d6db2964937c56492b418942c6cd5693d8d6cacd56`.
The recovered low failure is within this panel and lacks usage, so complete
costs for all paid attempts remain unknown. Two shared warmups cost $0.007096
separately; reuse aliases add no paid attempt. These estimates are not actual
provider charges. Summed chosen model-worker durations fall 66.54%; that sum
is not wall time. Historical cache availability and adaptive branch counts
differ, so these observations do not isolate reasoning effort's cost or runtime
effect.

The [recorded selection](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-5-effort-selection-decision.json)
selects **medium for the frozen 10-answer investigation**, with **405 distinct
questions**. Low will not expand. Medium's borderline five-answer result and
relationship losses require further source assessment; this is investigation,
not qualification. High was retained as the fallback if medium degraded
significantly or showed a new recurring failure. The selection SHA-256 is
`a4f97ec416736b44bb6b020035386877dfe726d3089f2bfc12399482648edb08`.
The five added source answers followed the frozen order and preserved prior
chosen outputs and receipts. Their shared prefixes were below the warming
threshold, so no new warmups were needed. One native coordinator, concurrency 8,
provider-only two-attempt retries, prompts and mechanical rules remain fixed.
No effort has qualified, and bulk grading and reserved-test access remain
unapproved. This checkpoint changes no prompt, rubric or release policy.

## Ten-answer medium investigation (October 10)

Sol/medium has completed the frozen 10-answer, **405-question** comparison:
**387 decisions agree with xhigh**, with 18 discordances and no missing or
conflicting panel decisions. All 18 have current source assessments, giving
**H=11, G=3, A=4** and a correctness-loss range of **4–12 of 405 decisions**,
or **0.99–2.96 percentage points**. All prior 297 chosen answers and original
receipts are unchanged; the added 108 questions contribute H=3, G=1, A=2.
Role results are:

| Role | N | H | G | A | Loss in percentage points |
| --- | ---: | ---: | ---: | ---: | ---: |
| Matching | 123 | 0 | 0 | 1 | −0.81 to 0.81 |
| Post support | 123 | 3 | 0 | 2 | 0.81–4.07 |
| Actual student parent-child pairs | 81 | 3 | 0 | 1 | 2.47–4.94 |
| Teacher/student compatibility | 84 | 6 | 3 | 0 | 3.57 |

The relationship roles share six exact inputs, including one harmful
difference; each counts once overall. The
[medium ten-answer source assessment](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-10-medium-source-assessment.json)
has SHA-256
`2a2503e8f2e9fd950c4e7e82b0957db8179d9bd0d22670ee1430859f816f5bd4`.
These are truth-uncertainty bounds from agent source assessment, not confidence
intervals, human-certified gold or population reliability. Fresh-call variance
and the effects of selecting an effort across nested stages remain unmeasured.

The current-AI-wave modifier comparison Jec359 is accepted true, producing H.
Both original source-only judgments were false and revised to true after
anonymous reason review under the unchanged clause/modifier rule; all originals
remain preserved. J6dc's English-practice-purpose comparison is accepted false,
producing G after independent review. Both new hashtag support differences
remain unresolved and contribute A; no source uncertainty is forced into a
verdict.

The [medium recurring-failure audit](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-10-medium-restriction-pattern-audit.json)
has SHA-256
`9a7b2541332b8bb25afd7f1bd85bfebafa10e823bdfc4361f5396eb9be43c8e2`.
Four accepted harmful prompts show the same added requirement for the parent
meaning to be the post's main subject, occurrence or performed action, despite
that meaning surviving in a clause, modifier or object. Compatibility alone
establishes recurrence across **R01 and R21**, two distinct notes. The actual
student parent-child failures for this mechanism remain on R01 only; repeated
R01 questions do not add independent notes. The separate actual People → Mothers
error on C06 remains in the role totals. The initial high screen does not
establish that high fixes the new R21 pair.

The extension pipeline took **18 min 40 s**, followed by a separate **48 s**
bridge for 16 missing panel inputs, all successful on their first attempts.
No new warmups were needed. The
[medium ten-answer execution seal](../../target/distillation-review-v1/final-trial-20261009/evaluation-medium/stage-10-complete-execution.md)
keeps pipeline and supplement reports separate; cumulative native costs include
prior stage-five work and are not extension-only expenses.

For the same 405 chosen successful answers, the API-equivalent catalog estimate
is **$1.9585544 at xhigh and $0.8435832 at medium**, or **56.93% lower**.
Both contain 312,530 total observed input tokens; cached input is 25.93% at
xhigh and 22.48% at medium. Output falls 76.33% and reasoning falls 88.99%;
output already includes reasoning. The
[405-question cost audit](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-10-medium-fixed-panel-cost-analysis.json)
has SHA-256
`e3f8d4451c08ef02651736281a70e3706321ae824f5a386216b8fa09611ee2d0`.
Complete costs including all paid attempts remain unknown: xhigh has two failed
attempts without usage and medium has one within this panel. Previously paid
shared warmups remain separate; reuse aliases add no paid attempt. Actual
provider charges are unknown. Summed chosen model-worker durations fall 57.92%,
but include all 405 questions across both stages and are not extension wall time.
Cache availability, history and adaptive branches prevent a causal effort-only
cost or runtime conclusion.

The [independent medium gate audit](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-10-medium-effort-gate-audit.json)
has SHA-256
`980ee2cd4c9fbeee451f19e1c202ea87acade7ed5572fe86bda615e833c33b70`.
The numerical loss range alone is borderline. The independently verified
specific two-note recurrence requires stepping up under the approved interim
rule. Support and both relationship roles also require investigation and a
higher-effort comparison; these are not new per-role acceptance thresholds.

The [recorded next-effort decision](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-10-effort-selection-decision.json)
selects **high on the same frozen 10 answers and 405 questions**, with dispatch
authorized. Its SHA-256 is
`5271afdc5abbdcd1654ae8d09a5a6652524265497abac881a9102233e6239534`.
The high ten-answer investigation started at **13:18:53 UTC on October 10**
under one native coordinator. Its five added answers retained prior high-screen
outputs and receipts, used concurrency 8 and needed no new warmups. The pipeline,
exact missing-panel bridge and source assessments are complete, with the
[result and subsequent selection recorded below](#ten-answer-high-result-and-xhigh-selection-october-10).
Medium remains unexpanded. No effort is qualified or established as the minimum.
Prompts,
frozen data, references, mechanical rules, concurrency 8, provider-only
two-attempt retries and natural-prefix eligibility
remain unchanged. Bulk grading and reserved-test access remain unapproved.

## Ten-answer high result and xhigh selection (October 10)

Sol/high has completed the same frozen ten-answer, **405-question** comparison:
**392 decisions agree with xhigh**, with 13 discordances and no missing or
conflicting panel decisions. Current source adjudication gives **H=8, G=1,
A=4**, bounding relative correctness loss by **3–11 of 405 decisions**, or
**0.74–2.72 percentage points**. The net loss excluding unresolved truths is
**7/405 = 1.73 points**, within the accepted two-point margin. The prior 297
chosen outputs and original receipts are unchanged; the added 108 questions
contribute H=2, G=1, A=2. The provisional 246 matching/support chosen outputs,
normalized decisions and original receipts match the final results exactly;
alias identities are unchanged.

| Role | N | H | G | A | Loss in percentage points |
| --- | ---: | ---: | ---: | ---: | ---: |
| Matching | 123 | 0 | 0 | 2 | −1.63 to 1.63 |
| Post support | 123 | 3 | 0 | 2 | 0.81–4.07 |
| Actual student parent-child pairs | 81 | 1 | 0 | 0 | 1.23 |
| Teacher/student compatibility | 84 | 4 | 1 | 0 | 3.57 |

The relationship roles share six exact inputs, all agreeing with xhigh, and
count each once overall. The
[high ten-answer source assessment](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-10-high-source-assessment.json)
has SHA-256
`c25f849db66336abac527d0b07bf4d15f67fe8a91d5a7cf8d82643edbcc6788b`.
The four unresolved cases remain unresolved, including J73 revision 2 and the
two new support-boundary cases; original judgments and review histories remain
preserved. These are agent source assessments and truth-uncertainty bounds,
not human-certified gold, confidence intervals or population guarantees.

The [high recurring-failure audit](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-10-high-restriction-pattern-audit.json)
has SHA-256
`920cccd6d98ab6c29084053f4f25f5544ddb404312e2228f09959c3186acd724`.
Three accepted harmful prompts repeat the same explicit added requirement:
high requires an invitation itself to be a claim on R01, and requires the
current AI wave to be the main subject on R21, despite its complete meaning
surviving as a temporal reference. The actual reasons add the same main-subject
or action requirement absent from the parent wording. Compatibility alone spans
both distinct notes; actual student parent-child failures **for this mechanism**
remain on R01 only. The two R01 prompts come from one note. High fixes
the separate R01 prediction case, but retains the two-note Claims/current-wave
failure; frozen xhigh is correct on all three accepted cases.

The [independent high gate audit](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-10-high-effort-gate-audit.json)
has SHA-256
`7b8b1882f99e2752cabbc172c58d63be4fe452c6476f3baa5e1029d8ecd0e825`.
The borderline numerical range alone would prompt expansion, not confident
rejection. The independently verified recurring mechanism triggers the existing
interim step-up rule. Support and compatibility losses required investigation
and the frozen higher-effort comparison; they add no per-role acceptance margin.

The [direct high-versus-medium source comparison](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-10-high-versus-medium-direct-source-comparison.json)
has SHA-256
`f5d8be78d1a94be88ba1fc278571c1bc8c0df50d14eb1e406478181861812df1`.
On the same 405 questions, 394 decisions agree. Relative to medium, high has
H=4, G=5, A=2, giving a loss range of **−0.74 to +0.25 points**. This does not
qualify either effort or establish a population advantage.

The high extension pipeline had **181 fresh successes**, followed by a strict
bridge of **16 first-attempt successes**, with no new failures or warmups.
The separate observed wall times were **19 min 39 s** and **38 s**. The
[high execution and reconciliation seal](../../target/distillation-review-v1/final-trial-20261009/evaluation-high/stage-10-complete-execution.md)
verifies the retained outputs/receipts and both launch snapshots' JSONL byte
prefixes. Native coordinators are drained; cumulative pipeline accounting
includes the earlier screen and is not extension-only cost.

For the same 405 chosen successes, the API-equivalent catalog estimate is
**$1.10529 at high**, **43.57% below xhigh's $1.9585544** and **31.02% above
medium's $0.8435832**. All three contain 312,530 total observed input tokens;
high caches **21.50%**, versus 25.93% at xhigh and 22.48% at medium. High output
is 59.13% lower and reasoning 69.13% lower than xhigh; output includes reasoning.
The added 108 chosen successes cost $0.268014 by the same catalog. The
[high fixed405 receipt cost audit](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-10-high-fixed-panel-cost-analysis.json)
has SHA-256
`7ed983698227f901fe58f931e8a0e5eaf85f1dffb0e457efd5ec542efa86d929`.
All paid high comparison attempts retain 407 successes, including two duplicate
successes beyond the chosen 405, and three older failures without usage.
Their known catalog subtotal is $1.111332; complete paid cost remains unknown.
The two unchanged shared warmups cost $0.007556 separately; reuse aliases add
no paid attempt and actual provider charges remain unknown. Chosen model-worker
durations sum to 2,927.825 s, 36.93% below xhigh, which is not elapsed wall time.
History, cache availability and adaptive branches prevent a causal effort-only
cost or runtime conclusion.

The [sealed next-effort decision](../../target/distillation-review-v1/final-trial-20261009/analysis/stage-10-high-effort-selection-decision.json)
has SHA-256
`23f032958d3035545667f3ecef325f7fa5dc7491585c3a8aecea23b4a539eb8b`.
It retains the **already-complete frozen Sol/xhigh baseline of 60 answers and
1,735 questions**, requiring no new model calls. Low stopped at five answers;
medium and high stopped at ten. **No lower effort qualified, and no lower-effort
20/40/60 expansion is authorized by this decision.** Early stopping does not
prove that any lower effort would exceed two points of loss on the full 60 or
in deployment. The requested lower-than-xhigh outcome remains **unachieved**;
this checkpoint is not goal completion or reviewer qualification. Prompts,
source data, mechanics, controls and the stopping rule remain unchanged. Bulk
pilot grading and reserved-test access remain unapproved.

## DSLv3 wording approval (October 10)

After the high-effort screen repeated an added main-subject/action requirement,
the user authorized drafting a clarification for review before new model calls.
After reviewing the displayed wording and confirming that DSLv3 includes the
ASv6.100 parent-child section verbatim, the user approved the wording.
[DSLv3](relationship-prompt-v3.md) has **approved wording, untested behavior**.
This approval does not authorize model
calls or change existing experiments, mechanical rules, source judgments or
the accepted two-point comparison margin. The lower-reasoning goal remains open.

The clarification makes preservation of the parent's complete meaning in an object,
modifier or temporal reference explicit. Its invalid-verdict counterexample
must fail a restriction actually expressed by the parent, rather than an added
main-subject or performance requirement. Actual action, purpose and timing
restrictions still apply: a goal for an activity does not establish that the
activity occurred. No failing trial examples are included in the prompt.

The shared runner's offline `revise` command generated DSLv3 against the unchanged
approved DSLv2 template, with a [native revision receipt](relationship-prompt-v3.md.revision.json).
Only the version header, clarification paragraph and counterexample wording
change. The quoted ASv6.100 rule, input variables and JSON decision schema are
unchanged. The approved template and native revision receipt retain their exact
draft bytes. No new model calls were made. The recommended next step is a
bounded trial of preserved meanings and genuinely missing restrictions; that
trial needs separate authorization.

## Actual distilled wording: offline preview (October 8)

The original actual-wording preview prepared saved validation wording with
**DSMv1 unchanged**, before further reviewer calls. The shared adapter supports
[matching-actual-source.json](matching-actual-source.json): a hash-bound prepared
dataset manifest and references to individual saved `subjects.json` generations.
It reads evaluation inputs and trusted teacher references, checks the saved note
identity and complete generation prompt against the corresponding evaluation
row, and reparses the untouched answer through production `subject_result`.
Malformed/truncated answers and exact-string targets cannot enter this matching
preview. Reserved test-generation paths are rejected before opening them;
training/test input files are not opened. All source bytes used are protected.
Model/checkpoint identity, selected hierarchy numbers, reasons and expectations
remain outside the prompt. ASv6.100 is trusted without another audit.

The preview uses Qwen, dense Gemma and MoE Gemma, each at baseline and the final
1,000-note validation checkpoint. Intermediate checkpoints are outside this
preview. Four selections per version were made before assigning expectations:

- The lowest SHA-256 of `DSMv1-actual-preview-01`, model, stage, note ID and
  subject, separated by NUL characters, among unique nonexact subjects in valid,
  untruncated answers. This is a deterministic subject sample, not a uniform
  sample of notes.
- The nonexact subject with highest `difflib.SequenceMatcher` similarity to
  any teacher wording (`autojunk=False`), with highest selection hash breaking
  ties. Similarity selects a case; it does not determine its expected answer.
- The largest distinct teacher catalog, then the longest selected subject,
  then highest selection hash.
- The longest selected subject, then highest selection hash.

The 24 selection hits reduce to **22 distinct note/subject inputs**: Qwen's
final largest-catalog and longest-subject selections coincide, and both Gemma
baselines produce identical longest wording on the same note. First selection
wins; duplicate hits are not extra cases. The set includes long actual
paraphrases, omitted restrictions, added identities and combinations of facts.
This deliberate mixture is a challenge preview, not a population accuracy
sample or a comparison of models/checkpoints.

Expectations were assessed from the complete catalog before reviewer calls:
**eight assessed matches, thirteen assessed nonmatches and one unresolved case**.
These are agent assessments, **not independently adjudicated gold**. Even
agreement with every assessed answer cannot qualify the reviewer: native
qualification remains pending and lists `unverified_expectations`. An unresolved
case has no semantic pass/fail or false-match count; its null placeholder does
not mean an expected nonmatch. The source format explicitly preserves that
distinction. At this preview stage, no adjudication policy or rubric change had
been adopted. The subsequent post-interpretation decision is recorded below.

| Case | Actual wording and comparison | Offline expectation |
| --- | --- | --- |
| R06 | `Silver winner of Weekly Competition #51 with 12 videos and a 12-satoshi reward` versus the teacher's identical wording with a comma after `#51` | Assessed match, T08 |
| R16 | `Self-custody` versus `Bitcoin self-custody`; all other corresponding teacher entries also specify Bitcoin | Assessed nonmatch: missing restriction |
| R05 | `Fakery` with `Inauthenticity` and `Deception` in the teacher catalog | Accepted assessed nonmatch: overlap is insufficient for complete equivalence |
| R19 | `Club symbols` versus `Clubs suit symbol` | Unresolved: whether the standalone wording preserves the suit restriction |

The [specification](matching-actual-spec.json) pins Sol / xhigh,
subscription transport and concurrency 8. Native preparation reports **zero
calls, zero attempts and zero reused answers**; all 22 cases are unrun. Inputs
total 19,624 `o200k_base` proxy tokens, with 364–1,282 per request and at most 46
teacher wordings. These are offline text sizes, not actual usage/caching/cost.

```sh
../experiment-runner/bin/experiment-runner prepare target/distillation-review-v1/matching-actual-fakery-20261008 --spec sse_multivector/distillation-review-v1/matching-actual-spec.json --repeat
../experiment-runner/bin/experiment-runner show target/distillation-review-v1/matching-actual-fakery-20261008 --json
../experiment-runner/bin/experiment-runner show target/distillation-review-v1/matching-actual-fakery-20261008 --case R06 --prompt-only
../experiment-runner/bin/experiment-runner show target/distillation-review-v1/matching-actual-fakery-20261008 --case R05
```

The initial preparation had twelve assessed nonmatches and two unresolved cases.
The user subsequently accepted the assessed nonmatch for R05, `Fakery`, under
the existing DSMv1 rule. [Oxford](https://www.oxfordlearnersdictionaries.com/definition/english/fakery)
describes fakery as making something that differs from what is claimed;
[Cambridge's deception entry](https://dictionary.cambridge.org/dictionary/english/deception)
also includes concealment, while its
[inauthentic entry](https://dictionary.cambridge.org/us/dictionary/english/inauthentic)
describes a lack of authenticity. The assessment is that their overlap does not
preserve identical complete meaning. User acceptance records an assessment,
not independent gold verification. The fresh offline preparation above retains
all 22 identical prompts/settings and changes only R05's expectation status
and reason. The original preparation remains preserved; no reviewer was called.

These inputs test matching only; support, parent restrictions and required
branch coverage are outside this preview. Later actual-wording trials below
and the broader three-check trial above record agreement and disagreements
with agent assessments. They do not independently verify the expected labels;
overall qualification remains pending.

Verification: the new production-workflow tests first failed because saved
generation sources were unsupported, and because unresolved expectations could
not be represented separately. They now check untouched wording, source/input
identity, changed hashes, truncation, test-path rejection before opening, and
unresolved/unverified qualification behavior. The matching, review, shared
experiment, selection and extraction regression suites pass. Re-reading the
saved confirmation-repeat report still gives 16/16 passing controls; no new
reviewer calls were needed for these checks.

## DSMv2: post interpretation draft (October 8)

The user accepted supplying the original post to clarify wording. Draft
[DSMv2](matching-prompt-v2.md) lets the post distinguish meanings of words or
phrases already present in either subject. It still forbids adding a restriction
absent from the subject merely because it appears in the post. Complete-meaning
matching, trusted ASv6.100 wording and the response schema remain unchanged.
The prompt contains no case-specific examples or expected verdicts.

The club case exposed why withholding all post context was too broad: R19's
post is `welcome to underground…♣`, its teacher wording is `Clubs suit symbol`,
and the actual generated wording is `Club symbols`. The post can identify the
card-suit sense of "club" without importing a new fact.

The authorized offline assessment now sets **R19's expected verdict to T06**,
teacher number `4`, `Clubs suit symbol`. [Unicode](https://www.unicode.org/charts/PDF/U2600.pdf)
identifies `♣` as the black club-suit symbol;
[Merriam-Webster](https://www.merriam-webster.com/dictionary/club) also defines
"clubs" as a card suit. Our assessment is that the post selects that meaning
already present in `Club symbols`, so omitting "suit" loses no restriction.
Here "symbols" is interpreted as a generic subject label rather than an added
count. The saved teacher and generated context fields both identify `♣`;
these fields support the offline assessment and are withheld from the reviewer.
This remains an agent-assessed expectation, not independently verified gold.
The subsequent two-case trial below agrees with it. The context-free DSMv1
expectation remains unresolved.

The authorized offline check of **R16 retains an expected null**. Its post
begins `The Bitcoin Beginner Guide is live.` and describes progression to
self-custody, while the generated subject is only `Self-custody`. Teacher T12,
original number `3`, is `Bitcoin self-custody`. Bitcoin specifies the asset;
self-custody specifies the custody relationship. The same relationship can
apply to other assets: [Ethereum's account guide](https://ethereum.org/guides/how-to-create-an-ethereum-account/)
also discusses self-custody for Ethereum wallets. Our assessment is that adding
Bitcoin from the post would supply a missing restriction, rather than clarify
the existing wording. Every other teacher custody entry also specifies Bitcoin
or the particular guide, so none has the same complete meaning. This is a
matching assessment; a general heading can still be supported by the post.
Subject support and whole-note coverage remain unjudged. The two-case trial
below checks this one matching verdict. The expectation and assessment status
are unchanged; only the recorded reason is clarified for DSMv2.

The shared adapter supplies `POST` as a JSON string when the prompt requests
`{POST}`. It uses the already verified original post from either source format.
`MATCH_INPUT` retains the identical one-subject / full-teacher-catalog input.
DSMv1 preparation and its frozen trials are preserved. Parent wording, generated
explanations, source/model identities and expected answers remain outside DSMv2.
The revision receipt records the exact delta from DSMv1.

[matching-actual-v2-spec.json](matching-actual-v2-spec.json) now binds
[matching-actual-v2-source.json](matching-actual-v2-source.json), keeping the
post-dependent assessment separate from DSMv1's original definitions. It
prepares the same 22 targets with Sol / xhigh and concurrency 8. The assessment-stage
offline artifact is `target/distillation-review-v1/matching-actual-custody-20261008/`.
All 22 prompts and settings are identical to the original DSMv2 preview;
R19's expected match, reason and assessment status change, and R16's reason is
clarified. The earlier previews remain frozen and preserved.
Native reporting confirms **zero calls, attempts and reused answers**; all
22 cases are unrun. Rendered inputs total 25,043 `o200k_base` proxy tokens,
with 445–1,569 per request and at most 46 teacher wordings. These are text sizes,
not measured usage, caching or cost. There are now nine assessed matches,
thirteen assessed nonmatches and no unresolved placeholders. All 22 expectations
remain unverified; qualification is pending. At this stage the other 20 inherited
assessments needed checking with the supplied posts; that check is completed below.

Inspect the exact draft club request without inference:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
../experiment-runner/bin/experiment-runner show \
  target/distillation-review-v1/matching-actual-custody-20261008 \
  --case R19 --prompt-only
```

The new production-path test first failed because `POST` was unavailable. It
checks both source formats, exact original-post content, unchanged catalog and
subject inputs, preserved source bindings and exclusion of expected answers.
The matching, review, shared experiment, selection and extraction regression
suites pass 244 tests. The saved DSMv1 confirmation repeat still reports 16/16
passing controls.
After the assessment-only update, all 14 matching tests pass. Native inspection
confirms T06 as the expected R19 ID, all expectations still unverified and all
22 cases unrun; it also confirms unchanged prompts/settings and preserves the
DSMv1 source definitions.
The subsequent R16 reason-only update also passes all 14 matching tests. Native
preparation preserves all 22 prompts, expected IDs and assessment statuses,
with zero calls and pending qualification. This does not test whether a model
actually follows the post-interpretation restriction.
These mechanical checks do not establish semantic reliability. The user next
authorized the two assessed cases below, then the remaining offline post checks.
Full review adoption and final-test unsealing remain open.

## DSMv2 two-case post-interpretation trial (October 8)

The user authorized testing whether Sol / xhigh distinguishes wording
interpretation from supplying a missing restriction. The shared CLI prepared
`target/distillation-review-v1/matching-post-pair-20261008/` from the existing
DSMv2 spec with `--only R16 --only R19 --repeat`, then ran it with
`--max-new-attempts 4` to allow the existing provider-only retry policy. Both
complete prompts, inputs, evidence and runner settings match the assessed
offline preview exactly. Concurrency remains 8; only two cases are selected.
Expected answers and their reasons were not supplied to the model.

Both fresh calls are mechanically valid and agree with the expectations:

| Case | Reviewer verdict | Decisive reason |
| --- | --- | --- |
| R16: `Self-custody` | null | It lacks the Bitcoin restriction in T12, `Bitcoin self-custody`. |
| R19: `Club symbols` | T06 | The post's `♣` selects the playing-card suit meaning of "club". |

There are two first attempts, zero retries, zero reused answers and no
mechanical or expected-verdict errors. Saved elapsed times are 6.21 seconds
for R16 and 28.68 seconds for R19. Native usage reports 1,735 input tokens,
zero cached input tokens and 1,129 output tokens, including 1,025 reasoning
tokens. The $0.01476 catalog estimate is not a subscription invoice;
provider-reported dollar charges are unavailable.

Native `review` records agent acceptance of each saved verdict separately
from user decisions. Neither expectation becomes independently verified gold.
Native qualification remains pending, with both selected expectations
unverified and the other 20 source cases pending. This trial shows the desired
distinction in these two calls, not repeat stability or general reliability.
The prompt, source expectations, DSMv1 trials and sealed final-test answers
are preserved. All 14 matching tests pass.

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
../experiment-runner/bin/experiment-runner show \
  target/distillation-review-v1/matching-post-pair-20261008 --case R19
```

## DSMv2 remaining post-visible expectations (October 8)

The user authorized checking the remaining 20 expected verdicts with the posts
visible, before further reviewer calls. Each subject was compared with its full
fixed teacher catalog and original post using native `show --case` evidence.
ASv6.100 remains authoritative; this does not audit the teacher answers.
Because the prior labels were already known, this is an agent recheck, not
independent gold adjudication.

All 20 expected verdicts are retained: eight matches and twelve nonmatches.
The eight matches are R02→T09, R03→T07, R06→T08, R09→T02, R13→T02, R14→T07,
R17→T16 and R20→T08. They preserve meaning through generic singular/plural
labels, punctuation changes, complete causal paraphrases or the same attributed
claim. The post resolves existing wording without adding restrictions.

The nonmatches are R01, R04, R05, R07, R08, R10, R11, R12, R15, R18, R21 and
R22. Missing universal scope, quantities, purpose or causal relationships are
not restored from the post. Added regime or identity restrictions are not
erased, and several teacher entries cannot be pooled into a single match.
R05 remains null: [fakery](https://www.merriam-webster.com/dictionary/fakery)
names the practice or products of faking;
[inauthenticity](https://www.merriam-webster.com/dictionary/inauthentic) names
a lack of authenticity, while
[deception](https://www.merriam-webster.com/dictionary/deception) includes
other ways of misleading people. Our assessment is that the post does not make
these related general subjects completely equivalent. These distinctions
concern matching, not whether the generated subjects are supported by the post.

Only the 20 `expected_reason` fields in the reusable DSMv2 source are updated.
Expected IDs and assessment statuses stay unchanged, including R16 and R19.
The full set still contains nine assessed matches, thirteen assessed nonmatches
and no unresolved placeholders. All expectations remain unverified.

The current offline preview is
`target/distillation-review-v1/matching-actual-postchecked-20261008/`, prepared
through the shared CLI with zero model calls, attempts or reused answers.
All 22 complete prompts and inputs match the earlier preview exactly. Provider,
model, effort, schema and concurrency are unchanged; the separate shared-runner
migration in commit `3008f537` changed the recorded runner executable path.
Input sizing remains 25,043 `o200k_base` proxy tokens, 445–1,569 per request,
with at most 46 teacher wordings. Native qualification remains pending.
All 14 matching tests pass. The user subsequently authorized the remaining
20-case trial below. The two-case trial and other frozen previews remain preserved;
bulk review and final-test unsealing remain separate decisions.

## DSMv2 remaining 20-case trial (October 8)

The user authorized running the remaining 20 cases through
`../experiment-runner/bin/experiment-runner`, with unchanged Sol / xhigh,
subscription transport and concurrency 8. The shared CLI prepared
`target/distillation-review-v1/matching-post-remaining-20261008/` from the existing
spec with the 20 selected IDs and `--repeat`, excluding the already tested R16
and R19. All complete prompts, inputs, evidence and runner settings match the
post-checked preview exactly. Expected answers and reasons were withheld.
The run used `--max-new-attempts 40` for the existing provider-only retry policy.

All 20 final reports are mechanically valid. Nineteen verdicts agree with their
recorded expectations: all eight expected matches and eleven of the twelve
expected nonmatches. The sole disagreement is **R05: `Fakery`→T17,
`Inauthenticity`, versus expected null**. Native scoring records `false_match`
for R05, with no missed matches or wrong matched IDs. These are agreements and
disagreements with agent labels, not an independently measured accuracy rate.

R05's response says both headings express the same general concept of being
fake or not genuine. Our expectation distinguishes the practice or products
of faking from a lack of authenticity. The response does not address that
distinction. Both headings are general and the post mentions fake imagery and
a fake societal paradigm, so their equivalence in this context needs adjudication.
Native `review` records nineteen agent acceptances and one **uncertain** R05.
The disagreement is preserved; no prompt or expected label is changed to make
the results agree. It does not by itself establish that Sol cannot perform
the matching task. ASv6.100 remains authoritative.

There are 21 new attempts, including one successful retry of R15 after a
structured `server_is_overloaded` / `service_unavailable_error` response.
There are no reused answers or unresolved request failures. Native usage reports
24,122 input tokens, zero cached input tokens and 5,703 output tokens, including
4,598 reasoning tokens. The failed attempt's SDK usage fields are zero;
these do not establish its actual upstream token consumption. The $0.105274
catalog estimate is not a subscription invoice; provider-reported charges are
unavailable. Final saved request elapsed times range from 5.18 to 104.77 seconds
and include admission waits; they do not include R15's earlier failed attempt.

Native qualification remains pending because all 20 selected expectations are
unverified. Its source-wide pending list contains R16 and R19, excluded from
this run and preserved in the separate completed two-case trial. No combined
usage report or population accuracy is inferred from these separate trials.
All 14 matching tests pass. Prompts, source expectations, earlier receipts and
sealed final-test answers remain unchanged. Further calls, prompt revisions,
bulk review and review adoption remain separate decisions. The subsequent
action/property controls below test an explicit version of R05's distinction.

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
../experiment-runner/bin/experiment-runner show \
  target/distillation-review-v1/matching-post-remaining-20261008 --case R05
```

## DSMv2 action/property controls (October 8)

The user authorized testing clear examples after the offline assessment of
R05 favored retaining its expected nonmatch. [Merriam-Webster's fakery entry](https://www.merriam-webster.com/dictionary/fakery)
names the practice or products of faking; [Oxford's inauthenticity entry](https://www.oxfordlearnersdictionaries.com/definition/english/inauthenticity)
names a lack of authenticity. That assessment remains a judgment about the
wordings, not an independently verified label or an audit of ASv6.100.

[The eight authored controls](matching-meaning-source.json) express the
action/property distinction explicitly in two domains. Each domain has a
two-entry catalog with an action and a property, two faithful paraphrases,
and two cases removing the complete match. Within each positive/negative
pair, the post, student wording and remaining catalog entry are identical;
only the matching entry is removed. The claims catalog reverses the action
and property order used by the images catalog. No student wording is an exact
catalog match. These controls were authored after observing R05's disagreement;
they are focused diagnostics, not held-out confirmation or independent gold.

| Case | Student wording | Expected and returned |
| --- | --- | --- |
| B01 | Creation of fake images | T01: Creating fake images |
| B02 | Images not being genuine | T02: Images being fake |
| B03 | Creation of fake images | null; only Images being fake remains |
| B04 | Images not being genuine | null; only Creating fake images remains |
| B05 | Fabrication of false claims | T02: Inventing false claims |
| B06 | Claims being false | T01: The falsity of claims |
| B07 | Fabrication of false claims | null; only The falsity of claims remains |
| B08 | Claims being false | null; only Inventing false claims remains |

The shared CLI prepared and ran [the spec](matching-meaning-spec.json) in
`target/distillation-review-v1/matching-meaning-20261008/`, using unchanged
**DSMv2 / Sol / xhigh / subscription SSE / concurrency 8**. The existing generic
adapter freezes the authored inputs and expectations as separate evidence;
it does not apply the source-bound matching adapter's qualification scoring.
Before calls, the native preview confirmed all eight cases were unrun, the
expected reasons were withheld and each positive/negative pair differed only
by removing its complete match. The source SHA256 is
`487681efa720687733db3d90d82dda5f378c85d7cb408cfa0ea660980f44b538`.
Execution used `--max-new-attempts 16` under the existing provider-only retry
policy. All eight reports are schema-valid and agree with the frozen
expectations; each explanation addresses the action/property distinction.
Native `review` records eight agent acceptances. There are eight new attempts,
no retries and no reused answers. All returned IDs belong to their supplied
catalogs and all reasons are nonblank.

Native usage reports 3,333 input tokens, zero cached input tokens and 1,023
output tokens, including 689 reasoning tokens. The $0.016896 catalog estimate
is not a subscription invoice; provider-reported charges are unavailable.
The 14 matching regression tests pass in the cached `tiktoken==0.14.0`
environment; the initial plain-Python attempt lacked that dependency.

This establishes that Sol preserves the distinction in these explicit controls.
Their catalogs contain one or two entries, versus eighteen in R05, and their
wording differs, so they do not isolate the cause of R05's match. Its saved
uncertain review and expected null are preserved. DSMv2 is unchanged and
broader qualification remains pending. The fresh R05 repeat below checks
whether its disputed verdict recurs with identical inputs. Its semantic
correctness remains unverified.
Further calls, prompt changes, bulk review and test unsealing require their own
authorization.

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
../experiment-runner/bin/experiment-runner show \
  target/distillation-review-v1/matching-meaning-20261008 --case B03
```

## DSMv2 R05 fresh repeat (October 8)

The user authorized one fresh R05 call with identical inputs and settings.
The shared CLI prepared
`target/distillation-review-v1/matching-post-r05-repeat-20261008/` with
`--from` the saved remaining 20-case trial, `--only R05` and `--repeat`.
It inherits the original answer as its baseline and excludes response reuse.
Before execution, native inspection verified identical complete prompts,
inputs, evidence, input SHA256 and settings: **DSMv2 / Sol / xhigh /
subscription SSE / concurrency 8**. Only one selected case can run concurrently.
No expected reason is sent to the reviewer. Execution used
`--max-new-attempts 2` under the existing provider-only retry policy.

The repeat returns **T17, Inauthenticity**, matching the original teacher ID.
Its new explanation is:

> “Fakery” names the general concept of fakeness or inauthenticity, without adding a specific entity, time, or attribution.

Both fresh calls equate Fakery with general fakeness; neither addresses the
practice/products versus property distinction in the frozen expected reason.
Native text comparison says `changed` because the explanations differ, while
the teacher ID is identical. This reproduces the disputed match in two saved
calls; it does not establish a general stability rate or independently settle
the correct semantic label. Native scoring still records `false_match` against
the agent-assessed expected null. Native `review` records **agent-uncertain**
for the repeat. The original receipt and review, prompt and source expectation
are preserved. ASv6.100 remains authoritative.

There is one mechanically valid report from one new attempt, with no retry or
reused answer. Native usage is 859 input tokens, zero cached input and 339
output tokens, including 290 reasoning tokens. The $0.005108 catalog estimate
is not a subscription invoice; provider-reported charges are unavailable.
The source-wide qualification report remains pending: one checked case out of
22 and one unverified expectation. Its other 21 pending cases are outside this
single-case repeat; no combined usage or accuracy report is inferred.

No code, reusable prompt or expectation changed. Verification checks the
native receipt and baseline binding, byte-identical supplied strings/settings,
withheld expected reason, distinct fresh receipt and current attributed review.
The subsequent read-only score trace confirms that optional teacher groups are
excluded from coverage and correctness depends on subject and incoming-link
verdicts. The user then agreed to the
[required-meaning qualification scope](#coverage-matching-qualification-scope-agreed-october-8).
R05's requirement flags and semantic expectation remain unverified; the scope
decision does not relabel this saved trial. Required/optional flags and revised
qualification cases are the next prerequisite. Further calls, prompt revisions,
bulk review and test unsealing remain separate authorizations.

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
../experiment-runner/bin/experiment-runner show \
  target/distillation-review-v1/matching-post-r05-repeat-20261008 --case R05
```

## Reviewer and inputs

Use exactly `openai-codex` / `gpt-6.1-sol` / `xhigh` through the existing
subscription transport. The user selected this as the reviewer: if it cannot
perform the review reliably, rethink the approach before bulk review. There is
no model substitution or paid API fallback. The setting is supported by
[official OpenAI documentation](https://developers.openai.com/api/docs/models/gpt-6.1-sol).
DSRv1/DSRv2 whole-answer qualification completed real calls but failed known
semantic and consistency checks; see the evidence below.

Render the template through the existing `experiment_inputs.render` contract:

| Variable | Content |
| --- | --- |
| `TASK_PROMPT` | Complete frozen [ASv6.100](../subject-prompt-goal-v1/asv6.100/ASv6.100.md), unchanged. |
| `REVIEW_INPUT` | JSON object containing `post`, `teacher`, `student`, `exact_matches`, and `teacher_meanings`. |

`post` is the full original text. `teacher` and `student` are the structurally
validated `subjects` arrays, preserving every number, context and subject.
`exact_matches` contains every identical-string pair as `{teacher_number,
student_number}`; a match establishes meaning, not correct placement.
`teacher_meanings` is initially null, or contains fixed
`{teacher_numbers, required}` groups for this same teacher answer. In a pilot
comparison these must be accepted groups; the DSRv2 qualification preview uses
provisional Q20 groups only to test consistency. These groups
index existing teacher entries; they are not a second extraction or teacher
audit. Qualification cases may fix them through the expectations below.

Each review has a fresh context with one student answer. Model identity,
checkpoint, previous scores and expected qualification results stay outside
the reviewer input. Keep source IDs, hashes, schema/prompt versions, requested
and returned model settings, original answers, attempts, timings and usage in
the existing workflow's provenance. Retain subscription usage as usage, not
an invented API bill. Rendered inputs, responses and reports remain ignored
artifacts. The reusable specification and qualification definitions are source.

## Report validation and scoring

The schema checks shape and field types. Application validation must also check
that every candidate number has exactly one subject verdict, every actual
immediate edge has exactly one relationship verdict, and all cited numbers exist
in the appropriate answer. Reject blank reasons, duplicate JSON keys, missing
or duplicate rows, invented edges, and overlapping or omitted teacher numbers.
Coverage rows partition teacher entries by meaning; exact duplicates belong to
one row. Optional rows have empty compatibility lists. Preserve every mechanical
exact match in its coverage row. Every full match of a required meaning must
also be a compatible equal-meaning occurrence. Freeze the accepted teacher
grouping and requirement flags for all versions of a note; resolve conflicting
groupings as evaluation failures before comparison, using the teacher reference independently of which
candidate wins. No separate source-inventory call is introduced.

For each required coverage row, code checks that `student_numbers` is nonempty
and that each compatible heading is either itself a full match or has a full
match among its descendants. Compare number segments, so `1.1` is not an
ancestor of `1.10`. Keep absent meanings, missing details and missing branch
occurrences visible in the findings. The reviewer supplies compatibility and
meaning judgments; numbering alone cannot establish those judgments.

- **Correctness:** correct returned entries / all returned entries. An entry
  needs a valid subject and, for a non-root, a valid incoming edge. Each entry
  contributes once; retain its separate subject and relationship verdicts.
- **Coverage:** fully covered required teacher meanings / all required teacher
  meanings. Each meaning contributes once, including all required placements.
  Optional derived headings do not enter the denominator.

Keep fractions unrounded until presentation and average per-note scores with
equal weight. Keep correctness and coverage separate. A valid empty answer to
a task requiring subjects scores zero on both; a correct empty answer with no
required subjects scores one on both. When no meaning is required, coverage is
one; unsupported nonempty output still fails correctness (Q19 below).
Invalid or truncated saved model output scores zero on both without repair or
regeneration. A missing output or integrity mismatch blocks evaluation; it is
not evidence that the model returned a bad answer. Missing, invalid, truncated
or incomplete reviewer reports remain ungraded evaluation failures, resolved
under the existing workflow's attempt rules before a completed comparison.

The pilot comparison remains 100 validation notes across three baselines and
fifteen checkpoints, with the final 1,000-note versions primary. Report paired
uncertainty respecting related-note groups, output failures, speed and cost.
Freeze planned comparisons and account for multiple comparisons in claims of
improvement. Preserve tradeoffs or inconclusive results. Freeze the reviewer,
rubric, scoring and validation decision before opening the saved 200-note test;
score all three final adapters and all three baselines, keeping selection fixed.

## Offline preparation and preview

[qualification-source.json](qualification-source.json) records the source hashes,
exact candidate changes and expected findings for all 29 cases. It contains
definitions, not generated teacher or student batches.
[qualification-spec.json](qualification-spec.json) now pins the DSRv2 draft, its schema,
GPT-6.1 Sol / xhigh, concurrency **8** and a one-hour overall request deadline.
The user directed concurrency 8 during the October 8 trial; the initial frozen
experiment used concurrency 1 and had only its final request in flight when
this setting changed. Its execution receipts remain unchanged. Subsequent
preparations use 8 with the existing provider backoff and retry rules.
That deadline is an allowance, not measured completion time or reliability.
The provider schema uses OpenAI's supported structured-output subset. Duplicate
teacher numbers, matches and compatible headings are rejected by the application
validator, rather than the unsupported `uniqueItems` provider constraint.

**October 8 request compatibility:** the initial `stress-preview` run preserved
29 HTTP 400 rejection receipts with no generated review text. The request schema
contained `uniqueItems`, outside the documented supported array constraints.
Remove that keyword while retaining all duplicate checks in production code;
the request-schema regression and duplicate-reference checks pass. A separately
frozen experiment, `qualification-compatible-schema-20261008`, uses the same
29 inputs, DSRv1 prompt, model and xhigh setting with the corrected schema. The
old failed receipts remain intact. The corrected requests generate reports;
their semantic qualification result is recorded below.
See [OpenAI's schema subset](https://developers.openai.com/api/docs/guides/structured-outputs).

### October 8 qualification evidence

The saved experiment is
`target/distillation-review-v1/qualification-compatible-schema-20261008`.
Its native receipts and `show --json` preserve complete inputs, generated reports,
validation, scores, known expectations and cross-version checks. All 29 cases
have one real generation attempt, with no reuse or retries: 28 complete reports
and Q23's interrupted report. Qualification has **failed**. This is evidence
about the current DSRv1 process with Sol / xhigh, not a teacher audit or approval
to change the process or reviewer.

- **Q04, trusted unchanged worked example:** all eight subjects and four links
  are valid, but coverage is `1/2` instead of the known `2/2`. The reviewer
  requires another Profile URLs occurrence beneath Identifiers, producing a
  missing-placement penalty on the trusted example. Preserve the disagreement
  for resolution under the accepted ASv6.100 standard.
- **Q21, faithful full-size rewording:** all 145 subjects, 130 links and 66
  teacher groups are reported. The two changed strings remain full matches,
  but thirteen untouched groups change from optional to required, moving the
  coverage denominator from 44 to 57. Compatible headings change for fifteen
  groups, including two with unchanged requirement flags. The untouched
  `4.2` → `4.2.1` link also changes from valid to invalid. Q21 takes 849.8 seconds;
  its targeted checks pass while the full cross-version checks fail.
- **Q22, remove one duplicate leaf:** all 144 remaining subjects, 129 links
  and 66 teacher groups are reported. The intended absent placements beneath
  `1` and `1.1` are found; remaining subject and link verdicts stay equivalent
  to Q20. Nevertheless, thirteen requirement flags and compatible-heading
  lists for twenty-four groups differ from Q20 after accounting for the deleted
  occurrence. It takes 899.1 seconds and fails the cross-version checks.
- **Q23, interrupted stream:** HTTP 200 is followed by a body transport error,
  `UND_ERR_SOCKET` / `other side closed`, after about 900 seconds. The saved
  46,108-byte report ends inside a coverage row and is ungraded. The local
  one-hour deadline has not expired; no provider output-limit stop is recorded.
  Final token usage is unavailable, so receipt placeholders must not be treated
  as measured zero usage. The failed request is not retried.

Seven of the eight unchanged largest generations return complete, structurally
valid reports, including both the 145-entry maximum and the longest saved
answer. The large cases and controlled variants retain these measured receipts:

| Case | Subject / link verdicts | Teacher meaning groups | Seconds | Input tokens | Output tokens, including reasoning | Report UTF-8 bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Q20 | 145 / 130 | 66 | 875.1 | 39,615 | 29,628 | 57,652 |
| Q21 | 145 / 130 | 66 | 849.8 | 39,523 | 29,196 | 58,604 |
| Q22 | 144 / 129 | 66 | 899.1 | 39,516 | 30,616 | 62,158 |
| Q23 | Incomplete | — | 904.3 | Unavailable | Unavailable | 46,108, partial |
| Q24 | 137 / 101 | 72 | 869.6 | 31,272 | 28,716 | 58,280 |
| Q25 | 136 / 126 | 47 | 712.0 | 46,072 | 28,085 | 52,086 |
| Q26 | 136 / 107 | 67 | 803.1 | 32,440 | 29,248 | 55,097 |
| Q27 | 130 / 118 | 47 | 595.7 | 47,975 | 28,005 | 49,198 |
| Q28 | 115 / 101 | 42 | 491.6 | 36,576 | 23,080 | 45,823 |
| Q29 | 106 / 96 | 34 | 557.6 | 37,614 | 21,886 | 39,691 |

Every receipt records requested `xhigh` and returned `gpt-6.1-sol`; Q23's model
identity is retained in its stream metadata. Complete stress reports establish
completion at those sizes, not correctness of every unlabeled judgment.
Eighteen of the nineteen small known controls pass; Q04 is the exception.
The saved workflow's observed usage is 592,639 input and 318,820 output tokens,
including 137,164 reasoning tokens. Q23's unavailable usage is additional to
those observed counts. The $4.373478 catalog estimate is not a subscription bill
or measured quota; no paid API fallback was used.

Inspect the preserved evidence without new calls:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
../experiment-runner/bin/experiment-runner show \
  target/distillation-review-v1/qualification-compatible-schema-20261008 --json
```

The cross-version controls initially supply `teacher_meanings: null` to test
classification consistency. Freezing accepted groups remains the agreed design,
but the changed placement and link judgments also require resolution. The
largest-input calls assess completion; they cannot erase these known
failures or establish semantic accuracy without labels. Bulk review remains
unqualified. The user subsequently authorized the DSRv2 draft and offline
preview below, then qualification calls. Adoption remains pending.

### DSRv2 draft and offline preview

The user authorized preparing this revision after the read-only diagnosis.
DSRv2 adds one paragraph to the reviewer; its five review steps and scoring
rules remain unchanged:

> The worked examples inside ASv6.100, including their outputs, are authoritative
> applications of its rules. Apply the subject, parent and coverage-placement tests
> consistently with those examples. Saved teacher generations outside the worked
> examples provide coverage references, without gold verdicts for every subject,
> link or placement.

[Prompt edits](prompt-edits.json) and the generated
[revision provenance](prompt-v2.md.revision.json) bind the full-context revision
to DSRv1. ASv6.100 is unchanged. The clarification was untested at preparation;
the completed qualification below passes Q04 but fails other controls.

The existing 29 qualification cases remain. Q20–Q22 now receive the same
66 teacher groups and 44 required flags from the original Q20 receipt. These
flags are **provisional consistency inputs**, not accepted pilot labels or
known correct classifications. No old subject/link verdicts, matching decisions,
compatibility lists, reasons or scores enter the new prompts. Q06 and Q08 still
test initial classification against their trusted worked-example labels.

| Case | Candidate | Subjects / links | Fixed teacher groups |
| --- | --- | ---: | --- |
| Q04 | Trusted AS URL example, unchanged | 8 / 4 | Initial classification; known correctness and coverage remain 100%. |
| Q20 | Largest saved training hierarchy, unchanged | 145 / 130 | 66 groups, 44 required. |
| Q21 | Two faithful Carstens rewordings | 145 / 130 | Same as Q20. Unchanged judgments must stay equivalent. |
| Q22 | Remove only leaf `1.1.1` | 144 / 129 | Same as Q20. Detect the lost placements under `1` and `1.1`; preserve unrelated judgments. |

The shared adapter reads the original saved experiment through native receipt
validation and requires the same full task, post and teacher. The source
definition pins the exact Q20 receipt. Preparation protects the saved experiment,
configuration, manifest and result ledger by hash, and rejects per-candidate
overrides of these shared groups. It does not promote them to known gold.

The original frozen preview is
`target/distillation-review-v1/qualification-v2-preview-final-20261008`, initially
29 unrun cases with zero attempts and zero reused answers. Q20–Q22's
inputs intentionally differ from DSRv1 because groups are now supplied; their
normal baseline comparison reports `input_mismatch`. Assess invariance among
the new Q20–Q22 results rather than comparing aggregate scores across different
reference inputs. The original failed trial and receipts remain intact.

Inspect DSRv2's exact rendered Q04 prompt without inference:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
../experiment-runner/bin/experiment-runner show \
  target/distillation-review-v1/qualification-v2-preview-final-20261008 \
  --case Q04 --prompt-only
```

Use `--case Q20`, `Q21` or `Q22` to inspect the complete stress inputs, including
their fixed groups. Preparation itself authorizes no calls. The user subsequently
authorized qualification in the order below; bulk review and test unsealing
remain outside that authorization.

### DSRv2 qualification, October 8

After seeing the draft and testing sequence, the user authorized real Sol / xhigh
qualification with concurrency 8 and existing provider backoff. Test Q04 first,
then the other small known controls, then all eight large training hierarchies
and Q21/Q22's controlled variants. Compare individual findings and reasons,
including required flags, rather than accepting aggregate scores alone.
Incomplete reviewer reports remain ungraded qualification failures. Preserve
the failed DSRv1 trial and the provisional status of the 44 large-case flags.

**Q04 passed:** `qualification-v2-url-check-20261008` records one real call,
no retry or reuse, 63.1 seconds, correctness `8/8` and coverage `2/2`. All eight
subject and four link verdicts are valid. Both Profile URLs and Event identifiers
remain required and fully covered; Profile URLs no longer demands an extra
occurrence beneath Identifiers. This resolves the observed disagreement on this
control without marking a required meaning optional. The receipt records 10,709
input and 1,987 output tokens, including 935 reasoning tokens.

`target/distillation-review-v1/qualification-v2-small-controls-20261008` prepares
Q01–Q19 with unchanged preview inputs. Its completed run preserves 18 new
attempts and one exact Q04 reuse: 18 complete, mechanically valid reports and
one interrupted report. **Seventeen controls pass, Q14 fails semantically,
and Q01 remains ungraded.** No request is retried.

- **Q14:** removing ` serving four people` from four cumin subjects correctly
  loses complete-source coverage (`1/2`) and invalidates their two incoming
  recipe links. The established control treats the shortened subjects as
  supported generalizations, so correctness should be `8/10`. DSRv2 instead
  marks all four shortened subjects incorrect for omitting the serving size,
  producing `6/10`. DSRv1 passed this control. Preserve the known expectation;
  this new result fails the agreed distinction between subject correctness,
  link correctness and complete-source coverage.
- **Q01:** HTTP 200 is followed by a body transport error,
  `UND_ERR_SOCKET` / `other side closed`, after 365.2 seconds. The native receipt
  preserves 21,883 UTF-8 bytes of partial review text. The one-hour local deadline
  has not expired and no provider output-limit stop is recorded. This is an
  ungraded interruption, not a semantic verdict. SDK zero usage placeholders
  are not measured zero usage; final usage is unavailable. Do not retry it.

Native `show --generation-costs --json` traces 19 original calls across the URL
check and small-control experiment, counting Q04 once. Their observed usage is
209,845 input and 53,919 output tokens, including 20,139 reasoning tokens;
Q01's unavailable usage is additional. The transport is the existing subscription,
not a new paid API bill.

`target/distillation-review-v1/qualification-v2-large-cases-20261008` completes
Q20–Q29 at concurrency 8, with ten real attempts and no retries or reuse.
Four of the eight unchanged largest hierarchies return complete reports, as do
both controlled variants. Four other large requests are interrupted and remain
ungraded. Supported case selection preserves the small controls without
resending Q01. **Both Q21 and Q22 fail cross-version consistency**, despite
passing their targeted Carstens checks and preserving all 66 supplied groups
and 44 required flags.

- **Q21, faithful rewording:** both changed Carstens subjects remain valid full
  matches and their incoming links remain valid. The untouched Money transfers
  link `4.2` → `4.2.1` changes from valid in Q20 to invalid in Q21. Its identical
  child says every transfer becomes visible and traceable as a consequence of
  Carstens's proposed central bank digital currencies. Q20 interprets that
  restriction as money transfers; Q21 allows a counterexample involving data
  transfers. The required transfer meaning also loses compatible headings `4`
  (Financial transactions) and `4.2` (Money transfers). These are changes in
  judgments about identical wording, independent of the Carstens rewording.
- **Q22, remove only leaf `1.1.1`:** the surviving Carstens subject and link stay
  valid. Sol detects the intended missing placements beneath `1` and `1.1`.
  Nevertheless, the same untouched Money transfers link flips to invalid and
  the transfer meaning loses the same compatible headings. Coverage stays
  `10/44` in all three reports: the Carstens meaning was already uncovered
  beneath other headings. Aggregate equality does not establish consistency.
- **Q23, Q26, Q28 and Q29:** each HTTP 200 response ends with a body transport
  error, `UND_ERR_SOCKET` / `other side closed`. Q23 and Q26 preserve partial
  report text; Q28 and Q29 return no review text. No local one-hour deadline
  expires and no provider output-limit stop is recorded. These are ungraded
  interruptions, without final usage, and are not retried.

| Case | Complete subject / link verdicts | Teacher meaning groups | Seconds | Report UTF-8 bytes |
| --- | ---: | ---: | ---: | ---: |
| Q20 | 145 / 130 | 66 | 695.4 | 60,070 |
| Q21 | 145 / 130 | 66 | 733.8 | 59,654 |
| Q22 | 144 / 129 | 66 | 643.6 | 58,636 |
| Q23 | Incomplete | — | 758.3 | 49,256, partial |
| Q24 | 137 / 101 | 72 | 461.5 | 51,715 |
| Q25 | 136 / 126 | 47 | 730.0 | 54,382 |
| Q26 | Incomplete | — | 758.4 | 35,703, partial |
| Q27 | 130 / 118 | 47 | 678.1 | 52,742 |
| Q28 | No review text | — | 296.4 | 0 |
| Q29 | No review text | — | 114.2 | 0 |

Every large receipt records requested `xhigh` and returned `gpt-6.1-sol`.
Native `show --generation-costs --json` records ten original calls, six completed
reports and four calls with unavailable usage. Observed counts are 177,085
uncached input, 72,192 cached input and 159,114 output tokens, including 63,221
reasoning tokens. The four interrupted calls' unavailable usage is additional;
SDK zero placeholders are not measured zeros. This uses the existing subscription.

Across the URL check, small controls and large cases, all 29 distinct cases
were attempted once. Q04 is reused in the small set; it is not another draw.
There are 24 complete reports and five ungraded interruptions. The native subset
reports retain the original 29-case catalogue, so each lists cases outside its
own selection as pending; inspect the two completed subsets separately.
DSRv2 fails Q14 and both large consistency controls. Large-case completion
does not establish accuracy of their unlabeled judgments or the provisional
requirement flags. Bulk review remains unqualified; adoption remains open.
Inspect preserved native evidence with `show --case ID --json`. No prompt,
known expectation, scoring rule or teacher standard changes during this trial.

Reproduce the DSRv2 preparation in a new destination, without inference:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
../experiment-runner/bin/experiment-runner prepare \
  target/distillation-review-v1/qualification-v2-preview-copy \
  --spec sse_multivector/distillation-review-v1/qualification-spec.json \
  --baseline target/distillation-review-v1/qualification-compatible-schema-20261008 \
  --history-root target/distillation-review-v1
```

Inspect the preserved DSRv1 rendered prompt for Q17, including the unchanged task,
full post, teacher, candidate and exact matches:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
../experiment-runner/bin/experiment-runner show \
  target/distillation-review-v1/stress-preview \
  --case Q17 --prompt-only
```

[Q17-report.json](tests/fixtures/Q17-report.json) is an **authored expected report**
for the missing Cumin copy, not a model response. Validate and score it against
the frozen inputs:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
../experiment-runner/bin/experiment-runner score-review \
  target/distillation-review-v1/stress-preview --case Q17 \
  --report sse_multivector/distillation-review-v1/tests/fixtures/Q17-report.json
```

The result retains the supplied report and source hashes, with `source_kind:
supplied_report` and zero inference calls. Correctness is `9/9`; coverage is
`1/2`, with heading `3` missing its complete cumin occurrence. This preview
does not create a model receipt, mark the experiment run, or establish reviewer
capability. After real qualification, `show --json` reports known-control
disagreements, teacher-group consistency and the large-case comparisons;
missing cases keep qualification pending.

## Qualification cases and expected results

The definitions below are maintained case specifications, not rendered batches
or model outputs. C1–C8 refer to the eight complete `<example>` blocks in the
unchanged ASv6.100 source. Use their complete posts and outputs as trusted
controls; do not regenerate or audit the examples. Change only the specified
candidate fields. Preserve the original teacher and post. Keep the expectations
outside the model input. Preparation must use the shared experiment workflow;
the `distillation_review` adapter provides this source-bound preparation.
Do not hand-build experiment artifacts or execution scripts.

For C6, fix four required teacher meaning groups:

| Complete source meaning | Teacher numbers |
| --- | --- |
| 2 m cable A | `1.1.1.1` |
| 3 m cable B | `1.1.2.1` |
| Pair consisting of 2 m cable A and 3 m cable B | `1.1.1.1.1`, `1.1.2.1.1`, `1.2.1` |
| 2 m cable A not longer than 3 m cable B | `1.1.1.1.1.1`, `1.1.2.1.1.1`, `1.1.3.1`, `1.2.1.1` |

Its other teacher meanings are optional broader headings. For C8, fix two
required groups: the complete recipe (`1.1`, `2.1`) and the complete recipe-bound
cumin subject (`1.1.1`, `2.1.1`, `3.1`, `4.1`). Its other headings are optional.
These are annotations of the existing trusted examples for qualification, not
independently extracted replacements for pilot teacher answers.
Q06 and Q08 receive `teacher_meanings: null` so their initial grouping and
required/optional classifications are tested against these known labels, kept
outside the prompt. The controlled variants receive the fixed groups; their
reports must also preserve them.

For Q01–Q19, all unmentioned returned subjects and actual edges retain valid
verdicts. Expected scores are exact fractions; compare individual findings as
well as the totals, because compensating mistakes can produce the same score.

| Case | Candidate change | Expected findings and scores |
| --- | --- | --- |
| Q01–Q08 | Each C1–C8 output unchanged. | Every subject and edge valid; every required meaning covered. Correctness and coverage both 100%, including C3's empty output. |
| Q09 | C6: change `1.1.1.1` to `Cable A, two metres long`. | Semantic match to 2 m cable A; all subjects and edges valid. Correctness `15/15`; coverage `4/4`. |
| Q10 | C6: replace `not longer than` with `longer than` in all four comparison copies. | Four unsupported comparison subjects; incoming links remain valid. Correctness `11/15`; coverage `3/4`. |
| Q11 | C6: remove leaf `1.2.1.1`. | All remaining entries correct. Comparison meaning still exists, but is missing beneath `1.2` and `1.2.1`. Correctness `14/14`; coverage `3/4`. |
| Q12 | C6: remove optional `1.1.1` and replace prefix `1.1.1.1` with `1.1.1` throughout its remaining subtree. | Removing a broader heading is acceptable; all remaining subjects and links valid. Correctness `14/14`; coverage `4/4`. |
| Q13 | C6: replace prefix `1.1.2` with `1.1.1.2` for the whole 3 m subtree, moving it beneath 2 m cables. Preserve parent-before-child order. | All subjects valid; the incoming edge to `1.1.1.2` is invalid because 3 m cables need not be 2 m cables. Correctness `14/15`; coverage `4/4`. |
| Q14 | C8: remove ` serving four people` from all four complete cumin subjects; keep context unchanged. | Shortened subjects are supported generalizations. Their links beneath recipe entries `1.1` and `2.1` lose the servings restriction. Context cannot restore complete cumin meaning. Correctness `8/10`; coverage `1/2`. |
| Q15 | C8: replace `for seasoning food` with `for painting walls` in all four complete cumin subjects. | Four unsupported subjects; the link beneath Food seasoning also invalid. Count each bad entry once. Correctness `6/10`; coverage `1/2`. |
| Q16 | C8: append root `5` named `Spices`, then `5.1` containing an unchanged complete cumin subject and its source context. Give `5` context identifying the cumin seasoning. | Valid new generalization, with its required source copy. All subjects and links valid. Correctness `12/12`; coverage `2/2`. |
| Q17 | C8: remove leaf `3.1`. | Complete cumin meaning remains elsewhere but not beneath Cumin at `3`. Correctness `9/9`; coverage `1/2`. |
| Q18 | C8: return a valid empty subjects array. | Unanswered required task. Correctness and coverage both 0%. |
| Q19 | C3: return one root `Birds`, with context citing the URL host. | URL component words supply no subject evidence. Correctness `0/1`; coverage 100% because no meaning is required. |

### Full-size qualification

Use only the training split for the following cases. The Q20–Q22 teacher answer
has **145 entries, 130 immediate edges and
66 distinct exact strings**, exceeding the previously observed 134-entry
validation workload. This is a size measurement, not a semantic audit. Before
execution, compare this size with all then-collected validation answers; larger
workloads need representative qualification without truncating the hierarchy.

- Source: `target/distillation-pilot-v1/pilot-data-asv6.100-20261004/prepared/train.jsonl`.
- Source SHA256: `f166371c5051b2ea95eb9591510544ade59ef8b1ef3b94826ed4baab92d1e681`.
- One-based line: `269`; task: `subjects`.
- Note ID: `af8e33afa7157affe406b4d534f2fe7086109e353b290f19c67ae78b558702ac`.
- Preserve the exact complete post from the training prompt and the saved
  completion. No validation or final-test content is used as this control.

| Case | Candidate change | Expected findings and scores |
| --- | --- | --- |
| Q20 | Full saved teacher answer unchanged. | Complete explicit verdicts for 145 subjects and 130 edges. The two targeted subjects and their incoming links are valid; their shared meaning is required. Record all other findings and computed scores as the baseline for the following controls. |
| Q21 | In `1.1.1` and `2.1.1`, replace `as one of the world's most powerful men` with `among the world's most powerful men`; retain every other word. | Both entries still match their complete original meaning. Subject, link and coverage findings remain equivalent to Q20; both scores are unchanged. |
| Q22 | Remove only leaf `1.1.1`; retain the same complete meaning at `2.1.1`. | The target still has a full match, but is now missing beneath `1` and `1.1` and fails coverage. All remaining subject and link verdicts stay unchanged: correctness is `(B - 1) / 144`, where `B` is Q20's count of correct entries. Recompute total coverage from the same fixed meaning groups after removing the deleted match and heading occurrence. |

The Q22 target is the teacher meaning shared by `1.1.1` and `2.1.1`: Mexican
BIS head Agustín Carstens as one of the world's most powerful men, contrary to
the audience's expectations. Its full wording retains the restrictions of its
parents, and the post supports it directly. It must be classified as required.
Check all missing compatible ancestors, not just the directly named parent.
The remaining teacher grouping must stay fixed across these variants.

These three controls test completion and known semantic changes at full size;
they do not assume that every saved teacher entry or link is correct. ASv6.100
is the trusted standard, while a generated completion is not a fully labeled
correctness control. The unchanged large case therefore has no blanket 100%
gold score. Removing a heading can also remove a placement requirement for
other meanings; total coverage must follow the preserved report judgments,
rather than assuming that exactly one aggregate point is lost. Unlabeled
baseline findings are retained for inspection, not treated as qualification
errors merely because they are negative. These controls do not establish
accuracy for every unmodified judgment in a large answer.

### Largest saved generations

The October 7 stress selection sizes all **1,300 ASv6.100 teacher answers**,
checks frozen split identities and prepared-file hashes, and checks that training
completions match their saved references. Validation and final-test labels
contribute aggregate sizes only; their posts and subjects are not displayed or
prepared as development inputs.

Select the union of the **top five training answers by entry count** and the
**top five by canonical answer length**, breaking ties by note ID. Length means
UTF-8 bytes of saved subject JSON, not tokens or original transport formatting.
The union contains eight notes and includes both maxima across all 1,300:
145 entries and 35,966 answer bytes. Q20 already covers one selected note;
Q23–Q29 add the other seven without duplicate requests.

| Case | Note ID prefix | Entries | Immediate edges | Distinct subject strings | Answer bytes |
| --- | --- | ---: | ---: | ---: | ---: |
| Q20 | `af8e33af` | 145 | 130 | 66 | 32,021 |
| Q23 | `fb8214f6` | 138 | 125 | 50 | 33,678 |
| Q24 | `166d3861` | 137 | 101 | 72 | 25,845 |
| Q25 | `bc953a16` | 136 | 126 | 47 | 27,874 |
| Q26 | `d8582d21` | 136 | 107 | 68 | 25,886 |
| Q27 | `9affd0a1` | 130 | 118 | 47 | 35,966 |
| Q28 | `e3a37b07` | 115 | 101 | 42 | 29,426 |
| Q29 | `83ea7d44` | 106 | 96 | 34 | 28,409 |

Reproduce the offline ranking through the shared workflow:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
../experiment-runner/bin/experiment-runner rank-distillation-generations \
  target/distillation-pilot-v1/pilot-data-asv6.100-20261004/prepared/manifest.json \
  --top 5 --output target/distillation-review-v1/largest-generation-sizes.json
```

The saved ranking contains source hashes, size statistics and exact training
references; it contains no posts or subject text. The maintained qualification
definitions bind those references by hash, line and complete note ID. Preparation
preserves full hierarchies and posts, with the unchanged answer as the candidate.
The eight full DSRv1 rendered inputs range from **114,888 to 159,612 bytes**;
the mechanical exact matches contain 417–898 pairs. All subject and immediate
edge verdicts and a complete teacher-meaning partition are still required.
Inspect Q27, which has the longest rendered input:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
../experiment-runner/bin/experiment-runner show \
  target/distillation-review-v1/stress-preview --case Q27 --prompt-only
```

Q23–Q29 have no invented gold scores or semantic labels: they test completion
and mechanical report consistency at observed size limits. The trusted worked
examples and deliberate Q21/Q22 changes test known semantic behavior. A complete
stress report alone does not establish semantic accuracy. The October 8 trial
completed with the failures recorded above. These saved teacher maxima do not bound future student outputs;
larger collected answers require corresponding qualification before bulk review.

### Mechanical refusal cases

Before running a model, check rejection of malformed student JSON, a truncated
student response and invalid numbering: each saved output failure receives both
zeros. Separately check malformed/truncated reviewer JSON, an omitted subject
verdict, an omitted actual edge verdict, an unknown cited number, and an omitted
teacher number: each is an ungraded evaluation failure. These checks exercise
the eventual production preparation/validation/scoring path, not a second grader.

### Qualification decision

Compare every known verdict, match, missing placement and computed fraction
against these expectations. A correct aggregate does not excuse incorrect
findings. Record actual input/output lengths, completion, time, usage and
failures for the full-size cases. Resolve any unexpected result before bulk
review. If GPT-6.1 Sol / xhigh cannot perform the task reliably, report the
concrete failure and rethink the approach with the user. Changes require a new
prompt version, regression checks and fresh qualification cases; agreement
between repeated calls alone does not establish correctness. Passing these
controls supplies initial evidence of capability, not a universal accuracy claim.

## Research basis and boundary

[FineSurE](https://aclanthology.org/2024.acl-long.51/) supports individual error
and coverage judgments followed by explicit ratios. Our whole-entry correctness
and complete-meaning-plus-all-placements coverage are AS-specific adaptations.
[ContextualJudgeBench](https://aclanthology.org/2025.acl-long.470/) motivates
checking contextual judges against labeled cases and controlled perturbations.
[Paired NLP evaluation guidance](https://aclanthology.org/P18-1128/) supports
paired comparisons and cautions about dependent examples, small samples and
multiple comparisons. Qualification completed October 8 after the user
approved proceeding from the prepared preview and failed the checks above. Bulk pilot grading and test
unsealing have not been performed.
