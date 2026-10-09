# Distillation semantic review — evidence and matching-only preview

Status: **DSRv1 and DSRv2 qualification failed; DSMv1 passes 32/32 distinct controls and a fresh 16/16 confirmation repeat**, October 8, 2026.
DSRv1 attempted all 29 cases: 28 complete reports and one interrupted report.
DSRv2 produces 24 complete reports and five ungraded interruptions across its
preserved subsets; it fails semantic and cross-version checks. Bulk pilot
semantic review has not run. **DSMv2 is an untested draft** allowing the original
post to clarify wording; its offline preview makes zero reviewer calls.
The agreed process and selected reviewer are recorded
in the [pilot process](../../docs/planning/fine-tuning-pilot-process.md#5-score-and-compare--locally-after-the-rental).
This package preserves [DSRv1](prompt.md), drafts [DSRv2](prompt-v2.md), and
specifies their [report schema](response-schema.json) and qualification cases.
Offline source preparation, report validation, scoring
and qualification checks are implemented in the shared experiment workflow.
The full semantic reviewer has not been qualified; bulk pilot grading is not implemented here.

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

Prepare and inspect through the shared CLI in an environment providing
`tiktoken==0.14.0`, also used by the existing bounded comparison workflow:

```sh
python3 sse_multivector/experiment.py prepare target/distillation-review-v1/matching-development-20261008 --spec sse_multivector/distillation-review-v1/matching-development-spec.json --repeat
python3 sse_multivector/experiment.py prepare target/distillation-review-v1/matching-confirmation-20261008 --spec sse_multivector/distillation-review-v1/matching-confirmation-spec.json --repeat
python3 sse_multivector/experiment.py show target/distillation-review-v1/matching-development-20261008 --case M01
python3 sse_multivector/experiment.py show target/distillation-review-v1/matching-development-20261008 --case M01 --prompt-only
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
python3 sse_multivector/experiment.py show target/distillation-review-v1/matching-development-20261008 --json
python3 sse_multivector/experiment.py show target/distillation-review-v1/matching-development-20261008 --case M06
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
python3 sse_multivector/experiment.py show target/distillation-review-v1/matching-confirmation-20261008 --json
python3 sse_multivector/experiment.py show target/distillation-review-v1/matching-confirmation-20261008 --case M13
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
python3 sse_multivector/experiment.py show target/distillation-review-v1/matching-confirmation-repeat-01-20261008 --json
python3 sse_multivector/experiment.py show target/distillation-review-v1/matching-confirmation-repeat-01-20261008 --case M13
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
python3 sse_multivector/experiment.py prepare target/distillation-review-v1/matching-actual-fakery-20261008 --spec sse_multivector/distillation-review-v1/matching-actual-spec.json --repeat
python3 sse_multivector/experiment.py show target/distillation-review-v1/matching-actual-fakery-20261008 --json
python3 sse_multivector/experiment.py show target/distillation-review-v1/matching-actual-fakery-20261008 --case R06 --prompt-only
python3 sse_multivector/experiment.py show target/distillation-review-v1/matching-actual-fakery-20261008 --case R05
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
card-suit sense of "club" without importing a new fact. The final complete-meaning
judgment remains ungraded; omitting the explicit word "suit" does not by itself
establish a lost restriction.

The shared adapter supplies `POST` as a JSON string when the prompt requests
`{POST}`. It uses the already verified original post from either source format.
`MATCH_INPUT` retains the identical one-subject / full-teacher-catalog input.
DSMv1 preparation and its frozen trials are preserved. Parent wording, generated
explanations, source/model identities and expected answers remain outside DSMv2.
The revision receipt records the exact delta from DSMv1.

[matching-actual-v2-spec.json](matching-actual-v2-spec.json) prepares the same
22 targets with Sol / xhigh and concurrency 8. The offline artifact is
`target/distillation-review-v1/matching-actual-context-20261008/`.
Native reporting confirms **zero calls, attempts and reused answers**; all
22 cases are unrun. Rendered inputs total 25,043 `o200k_base` proxy tokens,
with 445–1,569 per request and at most 46 teacher wordings. These are text sizes,
not measured usage, caching or cost. The inherited DSMv1 assessments remain
unverified evidence, not newly adjudicated DSMv2 expectations. They need checking
with the supplied posts before calls; R19 remains unresolved and qualification
is pending.

Inspect the exact draft club request without inference:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py show \
  target/distillation-review-v1/matching-actual-context-20261008 \
  --case R19 --prompt-only
```

The new production-path test first failed because `POST` was unavailable. It
checks both source formats, exact original-post content, unchanged catalog and
subject inputs, preserved source bindings and exclusion of expected answers.
The matching, review, shared experiment, selection and extraction regression
suites pass 244 tests. The saved DSMv1 confirmation repeat still reports 16/16
passing controls.
These mechanical checks do not establish semantic reliability. Expected-answer
verification and checks of interpretation versus missing restrictions precede
any proposed reviewer calls. Full review adoption and final-test unsealing
remain open.

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
python3 sse_multivector/experiment.py show \
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
python3 sse_multivector/experiment.py show \
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
python3 sse_multivector/experiment.py prepare \
  target/distillation-review-v1/qualification-v2-preview-copy \
  --spec sse_multivector/distillation-review-v1/qualification-spec.json \
  --baseline target/distillation-review-v1/qualification-compatible-schema-20261008 \
  --history-root target/distillation-review-v1
```

Inspect the preserved DSRv1 rendered prompt for Q17, including the unchanged task,
full post, teacher, candidate and exact matches:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py show \
  target/distillation-review-v1/stress-preview \
  --case Q17 --prompt-only
```

[Q17-report.json](tests/fixtures/Q17-report.json) is an **authored expected report**
for the missing Cumin copy, not a model response. Validate and score it against
the frozen inputs:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py score-review \
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
python3 sse_multivector/experiment.py rank-distillation-generations \
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
python3 sse_multivector/experiment.py show \
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
