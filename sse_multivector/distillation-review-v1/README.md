# DSRv1 — distillation semantic review specification

Status: **draft**, prepared October 7, 2026; no qualification calls or pilot
semantic reviews have run. The agreed process and selected reviewer are recorded
in the [pilot process](../../docs/planning/fine-tuning-pilot-process.md#5-score-and-compare--locally-after-the-rental).
This package specifies [DSRv1](prompt.md), its [report schema](response-schema.json),
and qualification cases. Application code, case preparation, scoring and
execution are a subsequent task after review of this specification.

## Reviewer and inputs

Use exactly `openai-codex` / `gpt-6.1-sol` / `xhigh` through the existing
subscription transport. The user selected this as the reviewer: if it cannot
perform the review reliably, rethink the approach before bulk review. There is
no model substitution or paid API fallback. The setting is supported by
[official OpenAI documentation](https://developers.openai.com/api/docs/models/gpt-6.1-sol);
availability and task performance still require actual qualification.

Render the template through the existing `experiment_inputs.render` contract:

| Variable | Content |
| --- | --- |
| `TASK_PROMPT` | Complete frozen [ASv6.100](../subject-prompt-goal-v1/asv6.100/ASv6.100.md), unchanged. |
| `REVIEW_INPUT` | JSON object containing `post`, `teacher`, `student`, `exact_matches`, and `teacher_meanings`. |

`post` is the full original text. `teacher` and `student` are the structurally
validated `subjects` arrays, preserving every number, context and subject.
`exact_matches` contains every identical-string pair as `{teacher_number,
student_number}`; a match establishes meaning, not correct placement.
`teacher_meanings` is initially null, or contains previously accepted
`{teacher_numbers, required}` groups for this same teacher answer. These groups
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
grouping and requirement flags for all versions of a note; resolve conflicting groupings as evaluation
failures before comparison, using the teacher reference independently of which
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

## Qualification cases and expected results

The definitions below are maintained case specifications, not rendered batches
or model outputs. C1–C8 refer to the eight complete `<example>` blocks in the
unchanged ASv6.100 source. Use their complete posts and outputs as trusted
controls; do not regenerate or audit the examples. Change only the specified
candidate fields. Preserve the original teacher and post. Keep the expectations
outside the model input. Preparation must use the shared experiment workflow;
add minimal reusable input support before running if source-bound preparation
is not yet supported. Do not hand-build experiment artifacts or execution scripts.

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

Use only the training split for the following three cases. A mechanically
selected existing teacher answer has **145 entries, 130 immediate edges and
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
multiple comparisons. Qualification, bulk-review implementation and test
unsealing have not been performed or authorized by this draft.
