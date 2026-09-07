# Mask-prompt development

Status: plan approved; initial six-call batch prepared. No mask calls have run yet.

Keep ASv6.23 frozen. Each Astra-low call receives the complete original note and one fixed subject, using the existing mask prompt unchanged initially. No auxiliary context field is sent.

## Start small

The first batch is three notes, two subjects from each: six calls, with no automatic repeats.

| Note | What the two subjects let us inspect |
| --- | --- |
| H01: Bitcoin status fields | Connecting the shared Bitcoin context to the block-height and network-fee fields. |
| H02: Self-driving trucks | Selecting a short meaning from a longer sentence, then selecting the fuller route-and-human-driver comparison. |
| H03: “My Salvadorans” | A call for people to respond, and the author's expressed affinity with them. |

The six subjects are unchanged accepted ASv6.23 outputs. Their source notes, exact subjects and provenance are in [initial-inputs.json](./initial-inputs.json). These inputs were inspected before generating any masks. They do not establish broad coverage by themselves.

Review all six results before deciding whether a focused diagnostic or another small batch would help more. An isolated acceptable imperfection does not require an endless repair loop.

## Approved completion checks

Development grows from 3 to 6 to 12 notes, with two fixed subjects per note. Only missing calls are added while the prompt remains unchanged. Six predesignated subjects also receive two additional calls: 36 outputs in the completed development check.

Only after development passes, use 20 separate notes with two subjects each. Repeat six predesignated subjects twice: 52 final outputs. The final notes may have been used for subject work, but must not have informed mask-prompt development.

Acceptance: at least 35/36 development outputs and 50/52 final outputs accepted, and no same demonstrated error in two of three calls for a repeated input. Unresolved judgments and malformed or missing outputs are not passes. Upstream subject concerns are recorded separately. Different faithful masks are allowed.

This is the approved practical pilot target of at least 95% acceptance, not proof of population accuracy or an effort cap. Remaining errors stay visible; the standard cannot be weakened after results.

[plan.json](./plan.json) records selection, repeat, judgment and execution rules. No final set or later development batches have been opened or selected for this mask effort yet.

## Scope

No prompt edit, model comparison, new subject generation, production change, SSE encoding or segmentation. No overall attempt/token cap; choose each next batch for its expected information gain. User review uses the existing tool only when consequential semantic questions need input.

The task-specific evidence and review design follows [OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices). The particular sample sizes and acceptance tolerance are our approved experimental choices, not numbers prescribed by that guidance.
