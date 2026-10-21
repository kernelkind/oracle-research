# Subject-extraction grading

The grader compares saved subject hierarchies with source-bound teacher
references. It checks whether subjects are supported by the post, whether
parent–child relationships are valid, and whether required meanings remain
reachable. Teacher agreement, mechanical validity and semantic correctness
remain distinct.

See the [completed fine-tuning results](../../docs/experiments/subject-extraction/fine-tuning.md)
for model scores, and [controlled grading comparisons](../../docs/experiments/subject-extraction/grading-findings.md)
for reviewer failures, prompt development and measured resource use. The
[reproduction guide](../../docs/experiments/reproduce.md) describes supported
saved-result and training workflows.

## Checks and prompts

| Check | Version | Role |
| --- | --- | --- |
| Meaning matching | [DSMv3](matching-prompt-v3.md) | Match a student subject to a complete teacher meaning, using the original post to disambiguate wording. |
| Source support | [DSSv2](support-prompt-v2.md) | Determine whether the student's subject is supported by its original post. |
| Relationship validity | [DSLv10](relationship-prompt-v10.md) | Check actual parent–child restrictions and compatible placements. |
| Coverage search | [DCSv1](coverage-search-prompt-v1.md) | Find a valid student route expressing each required teacher meaning, or return a complete negative search. |

Prompts and response schemas are retained beside this file. DSLv2 and DSLv4
also remain because production fallback/evaluation paths still reference them.
Selecting a later filename alone does not upgrade frozen experiments; explicit
alternate relationship-prompt options bind the version used by a new trial.

The grader operates on numbered occurrences, rather than merging every repeated
subject string. It checks support and immediate relationships even when matching
succeeds. Optional teacher headings are not mandatory coverage targets. Invalid
or truncated student answers remain in their evaluated cohort; damaged source
bindings or missing reviewer work are technical failures, not invented zeros.

## Mechanical evidence and final decisions

Trusted exact teacher subjects establish a meaning match and same-post support.
Actual trusted teacher links or numbered ancestor paths establish the
corresponding ordered relationship. Identical parent/child wording preserves
the same restrictions. These cases carry explicit mechanical evidence and need
no model request; lack of an exact proof leaves a semantic question.

Matching affects which coverage questions are valid. A disputed match receives
one unchanged DSMv3 request at `gpt-6.1-sol` / `xhigh`; that final decision is
retained. Dependent coverage questions are rebuilt after matching changes.
A disputed coverage result receives one unchanged DCSv1 request at `xhigh`,
including disputed candidates. Its complete-search decision is final, rather
than being reopened by another relationship verifier. This accepts residual
reviewer error; agreement between fresh calls is not independent ground truth.

The automatic workflow runs missing judgments and retains completed decisions.
Temporary provider failures may retry with backoff in the same native experiment;
source, receipt and output-schema failures stop the workflow. Agent corrections
and audit vetoes remain development evidence, not hidden changes to the
published automatic scoring path. The final run has numeric grades for every
selected answer and no manual review queue.

## Saved-answer workflow

`distillation_review_preview.py` verifies the frozen dataset, checkpoint and
stage identities before counting mechanical and semantic work. Only the
selected split is decoded for review; validation preparation does not open
reserved test content or model weights.

`distillation_review_trial.py` freezes selected complete answers with their
reference meanings and generation identities. Four retained development source
files identify notes already exposed during earlier reviewer work:

- `matching-actual-v2-source.json`
- `actual-three-check-matching-source.json`
- `actual-three-check-support-source.json`
- `actual-three-check-relationship-source.json`

These are current sampling inputs, not unused qualification files.

Native evaluation prepares matching, support and relationship requests; the
coverage adapter uses completed matching and relationship evidence to form
coverage searches. The shared Experiment runner owns execution, reuse, retries
and immutable receipts. Collection keeps model judgments, mechanical proofs,
agent assessments and user decisions separate. Reused answers are not fresh
samples; an intentional independent trial requires its own recorded setup.

The published dataset contains final grades, assessments and source bindings.
It does not reconstruct every native intermediate evaluation directory. For
old development commands or retired qualification presets, use the preserved
source at `03bd9e45` and the study's recorded evidence, without changing frozen
hashes or claiming that later source was its original producer.

## Interpretation limits

The exposed development panels contain correlated questions and disputed source
interpretations. They do not establish an independent reviewer error rate or
training-seed variance. A successful parser, exact receipt, matching prefix or
low training loss does not establish semantic quality.

The completed original test grading covered 1,200 answers and 40,607 semantic
judgments in 911 native batches. Execution took about nine hours including
handovers/provider waits; it did not prove the earlier eight-hour fresh-run
target. Full-hierarchy scores and the later L1-only analysis answer different
questions; their definitions and comparisons are in the completed results.
