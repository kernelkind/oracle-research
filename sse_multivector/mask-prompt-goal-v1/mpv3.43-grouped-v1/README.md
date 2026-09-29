# MPv3.43-G1

Status: approved for testing and experimentally tested with Astra low;
not frozen or adopted. Frozen MPv3.43 remains unchanged.

Based on frozen MPv3.43, SHA-256
`75cf99011d0b35e4f62f5157834cc953cfd11bba913b9a4db602e8c151af8c03`.
The new input supplies all subjects for one post as a JSON array of `id` and
`subject` entries in `{SUBJECTS}`. The output retains a separate assessment and
mask for every subject, including empty masks, in a `results` array. Different
subjects may select overlapping text. Existing semantic rules and all example
subjects, explanations and selections are preserved; example envelopes change
to demonstrate the grouped input/output contract.

Created through `experiment.py revise`; the generated revision receipt is an
ignored artifact. Frozen MPv3.43 and its results remain unchanged. This draft
does not by itself establish that grouped generation improves cost or preserves
quality.

## Ten-note experiment, September 29

`experiments/astra-grouped-masks-v1` used the same ten teacher-comparison notes
and 287 saved Astra subjects, with individual HRv1 masks retained as evidence.
The shared `grouped_masks` adapter prepared and checked every result through
the production position decoder. No subjects or baselines were regenerated,
and no UI was created.

Nine calls completed: 201 mechanically valid masks (172 nonempty, 29 empty).
The longest note's 86-subject call was interrupted after approximately 110
seconds, with partial output and an unclassified `terminated` error. It was not
automatically retried. Reported zero usage for that failed call is not evidence
of zero tokens or quota use. Completed calls took 17–97 seconds; no malformed
IDs or positions occurred in those nine responses.

Agent inspection found eight masks with clear issues (six regressions and two
shared baseline issues), including five extra-looking-behavior selections in
the baby post, a missed growing repetition, an unsupported specific-vegetable
selection, and an erroneous empty coffee-motivation mask. Five further masks
remain uncertain. These are agent assessments of a small correlated sample,
not user decisions or a representative accuracy estimate. Forty-nine selections
changed; punctuation/fragment-boundary changes are not treated as semantic errors.

For the same nine completed notes, the shared reporter imported and verified
all original receipts and selected exactly their 201 individual-mask cases
(169 new calls, 32 reused answers). The initial new-attempt totals excluded
reused answers' earlier generation costs. The read-only `show --generation-costs`
view now traces nine additional source calls, counting duplicate references
once: 178 original individual calls in total. With observed caching included,
the user's Astra-equivalent rates give $0.030651492 grouped versus $0.16206534
individual, about 81% lower. Catalog API estimates are $0.88079 versus $4.65705.
Both are cost references, not subscription invoices or measured weekly quota.
Failed generation usage is unknown and excluded from this successful-output
comparison; subject generation and prominence are not included. Historical and
current cache/transport conditions differ, so this is not a randomized billing
trial or the cost of completing the entire batch.

## Sol max comparison: corrected generation accounting

The subsequent `sol61-max-grouped-masks-v1` experiment used the same ten posts
and 287 fixed subjects with GPT-6.1 Sol max. Seven calls completed 122 masks;
three calls were interrupted. No baseline was regenerated. The matched seven
posts cost $0.72715 in Sol catalog references versus $2.647964 for ungrouped
Astra low, including 22,144 cached Astra input tokens and the nine earlier source
calls. The 25 reused answers map to nine external originals plus duplicates
already counted, not 25 additional generations. This is about 72.5% lower for
the completed subset, not a complete-job or subscription-quota saving.

Across all ten posts, ungrouped Astra completed all 287 masks with 251 distinct
original calls at a $6.96967 catalog reference. Sol's three interrupted calls
have only normalized zero usage, so the complete Sol estimate is unknown, with
$0.72715 as its known subtotal. The generation report explicitly retains those
failures instead of labeling their costs zero. Completing or diagnosing the
interrupted work remains open; no replacement calls were sent for this audit.

The prompt is unchanged after this test. Per-note assessments are saved through
`experiment.py review --case`; the ignored experiment `assessment.md` records
the eight issues and five uncertainties. A single independent repeat of the
interrupted long note is a proposed next step, not authorized or run.
