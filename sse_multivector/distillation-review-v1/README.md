# Distillation semantic review — evidence and matching-only preview

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
verbatim ASv6.100 paragraph to matching. Its wording is approved, but it remains
untested; no DSMv3 experiment or calls exist yet.
The agreed process and selected reviewer are recorded
in the [pilot process](../../docs/planning/fine-tuning-pilot-process.md#5-score-and-compare--locally-after-the-rental).
This package preserves [DSRv1](prompt.md), drafts [DSRv2](prompt-v2.md), and
specifies their [report schema](response-schema.json) and qualification cases.
Offline source preparation, report validation, scoring
and qualification checks are implemented in the shared experiment workflow.
The full semantic reviewer has not been qualified; bulk pilot grading is not implemented here.

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
displayed in the conversation on October 9. The unchanged prompt remains an
untested draft; qualification is pending. Wording approval does not qualify the
reviewer or authorize new calls. No experiment has been prepared and no calls
have been made for DSMv3. Previous DSMv2 results do not qualify this new
version. Existing controls, expected labels and saved trials are preserved;
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
maintained copy. No adapter currently supplies the variable, and the draft has
not been prepared or rendered as an experiment request. The user approved the
rule-reuse decision, then accepted the revised wrapper's exact wording after
the full DSSv1 instructions were displayed in the conversation on October 9.
This accepts the instructions without qualifying the reviewer or authorizing
new calls.

For the trusted cable post, `Lengths` passing and `4 m cable A` failing are
proposed authored controls, not model verdicts or approved qualification cases.
They are input examples for human review, not worked examples embedded in DSSv1.
No experiment has been prepared and no model calls have been made for DSSv1.
The accepted prompt remains an untested draft. The proposed inheritance of post
support from correct complete teacher matches still needs process approval;
relying on semantic matches also requires qualifying the matcher. Existing
matching/review prompts, schemas, adapters, scoring and saved trials are
unchanged; only this unused support draft and its documentation are revised.

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
original source. No adapter currently supplies either DSLv1 variable, and no
support/link experiment, schema or scoring change is added by this draft.

The human example uses TC04's already-agreed invalid edge: `3 m cables` beneath
`2 m cables`. Its expected `valid: false` is an authored illustration of that
accepted case judgment, not a model result or newly prepared qualification
case. It remains outside the prompt instructions. At most one semantic verdict
is requested per actual immediate link; the input grows with the two subject
strings plus the fixed rule, without a whole hierarchy or all-pairs comparison.
This is draft call sizing, not approval of bulk execution or an optimization.

The user approved the exact DSLv1 wording after the full instructions were
displayed in the conversation on October 9. The unchanged prompt remains an
untested draft. Drafting and wording approval add no model calls, qualification
result, support-inheritance decision or final rubric adoption. ASv6.100, DSMv2,
DSSv1, existing adapters, schemas, scores and saved trials are unchanged.

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

The next step is to settle the unresolved meaning boundaries and independently
verify the expected answers before calls. Do not hide ambiguous sampled cases
by substituting easier ones or treat another Sol answer as gold. These inputs
test matching only; subject support, parent restrictions and required coverage
within every branch remain outside this preview. Reliability on actual outputs
has not yet been measured.

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
