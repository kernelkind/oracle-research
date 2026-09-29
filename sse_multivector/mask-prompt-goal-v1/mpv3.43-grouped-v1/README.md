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
(169 original calls, 32 reused answers). With caching included, the user's
Astra-equivalent rates give $0.030651492 grouped versus $0.152696832 individual,
about 80% lower. Catalog API estimates are $0.88079 versus $4.38784. Both are
cost references, not subscription invoices or measured weekly quota. Failed
generation usage is unknown and excluded from this matched comparison;
subject generation and prominence are not included. Historical and current
cache/transport conditions differ, so this is not a randomized billing trial.

The prompt is unchanged after this test. Per-note assessments are saved through
`experiment.py review --case`; the ignored experiment `assessment.md` records
the eight issues and five uncertainties. A single independent repeat of the
interrupted long note is a proposed next step, not authorized or run.
