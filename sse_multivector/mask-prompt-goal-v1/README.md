# Mask-prompt development

Status: the subject-conditioned removal prompt is frozen with Astra low. It passed development at 36/36 accepted masks and separate final validation at 52/52. Every predesignated repeated subject passed all three trials. Inputs, raw outputs, judgments, usage and isolation checks are preserved.

[Frozen package](./frozen.json) · [Exact prompt](./subject-deletion-v1/mask-prompt.md)

[Final results: every complete note and inline mask](./subject-deletion-v1/final/results.md) · [Final verification](./subject-deletion-v1/final/verification.json)

[Development results with full notes and inline masks](./subject-deletion-v1/development-results.md)

[Initial results with complete notes and inline masks](./initial/results.md)

[Second batch with complete notes and inline masks](./batch-2/results.md)

[M05 repeat results](./m05-repeats/results.md)

[Direct-instruction probe](./scope-v1/results.md) · [Contrastive-example probe](./scope-examples-v1/results.md)

Both revisions returned the same M05 and M06 masks. Neither demonstrated an improvement, so neither was expanded. [The decision history](./m05-scope-review/correction.json) preserves the original error judgment, its reopening, and the user's resolution across all three versions.

For “A call for Salvadorans to make their presence known,” “My” must be excluded: affinity is additional meaning. For M06, “The poster's expressed affinity with Salvadorans,” it belongs. This is a scope distinction, not a general ban on that word or on overlapping masks.

The subject-conditioned removal candidate replaces the baseline's ambiguous “preserve the same meaning” wording. The initial pair, two M05 repeats, four coverage regressions and six remaining fixed subjects all passed. That is an observed improvement on this development set, not proof of a general success rate or the failure's cause.

No further prompt revisions or generation calls are required for this approved goal. ASv6.23 and the acceptance thresholds remained unchanged; production behavior was not changed. The user answered the M05 question in chat; the existing TUI session was left untouched.

Each call uses the frozen prompt with the complete original note and one fixed ASv6.23 subject. No auxiliary context field, sibling subjects or prior answers are sent.

These results do not establish population accuracy, SSE quality or segmentation quality. Some returned words have multiple source positions, including matches inside URLs; all alternatives are recorded without claiming which one the model intended. An ambiguous abbreviation can support the supplied interpretation without proving unique author intent.

## Development started small

The first batch used three notes, two subjects from each: six calls, with no automatic repeats.

| Note | What the two subjects let us inspect |
| --- | --- |
| H01: Bitcoin status fields | Connecting the shared Bitcoin context to the block-height and network-fee fields. |
| H02: Self-driving trucks | Selecting a short meaning from a longer sentence, then selecting the fuller route-and-human-driver comparison. |
| H03: “My Salvadorans” | A call for people to respond, and the author's expressed affinity with them. |

The six subjects are unchanged accepted ASv6.23 outputs. Their source notes, exact subjects and provenance are in [initial-inputs.json](./initial-inputs.json). These inputs were inspected before generating any masks. They do not establish broad coverage by themselves.

Each batch was reviewed before choosing the next. The candidate retained its earlier outputs and added only missing coverage and repeat calls.

## Approved completion checks

Development grows from 3 to 6 to 12 notes, with two fixed subjects per note. Only missing calls are added while the prompt remains unchanged. Six predesignated subjects also receive two additional calls: 36 outputs in the completed development check.

Only after development passes, use 20 separate notes with two subjects each. Repeat six predesignated subjects twice: 52 final outputs. The final notes may have been used for subject work, but must not have informed mask-prompt development.

Acceptance: at least 35/36 development outputs and 50/52 final outputs accepted, and no same demonstrated error in two of three calls for a repeated input. Unresolved judgments and malformed or missing outputs are not passes. Upstream subject concerns are recorded separately. Different faithful masks are allowed.

This is the approved practical pilot target of at least 95% acceptance, not proof of population accuracy or an effort cap. Remaining errors stay visible; the standard cannot be weakened after results.

[plan.json](./plan.json) records selection, repeat, judgment and execution rules. The twenty final notes and forty subject indices came unchanged from [final-reservation.json](./final-reservation.json), with no replacements or overlap with the twelve development notes. All 88 candidate calls succeeded on their first attempt. Candidate generation used 219,298 input tokens and 8,062 output tokens; cached/reasoning tokens are included, not additional.

## Scope

Mask-prompt development only: no model comparison, new subject generation, production change, SSE encoding or segmentation. No overall attempt/token cap; choose each next batch for its expected information gain. User review uses the existing tool only when consequential semantic questions need input.

The task-specific evidence and review design follows [OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices). The particular sample sizes and acceptance tolerance are our approved experimental choices, not numbers prescribed by that guidance.
