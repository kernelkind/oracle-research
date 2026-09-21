# PPv7 — score the fixed mask directly

Status: draft, not model-tested, frozen or adopted in production.

This is the whole-prompt rewrite proposed in the discussion. The task is to
assess how strongly the complete post is about the selected content. It no longer
instructs the scorer to reconstruct a subject, preserve an abstraction level or
restrict context to avoid expanding that subject. Understanding the selected
text in context remains necessary; evaluating extraction correctness is not
part of this task.

The two input views, placeholders, numeric score bands and JSON output field
are preserved. The [PPv6 rendering contract](../ppv6-draft-v1/README.md) still
applies: both views must come from the same saved selections. No renderer,
production integration or model call is added here.

The rewrite removes repeated safeguards and uses a direct task statement,
consistent with the [official OpenAI guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively).
That guidance does not establish this prompt's performance or calibrate its
scores. The exact edit and hashes are recorded by the offline revision tool in
`PPv7.md.revision.json`. PPv6 and frozen PPv2 remain unchanged.

Next suggested step after review: a small saved-note ranking test comparing
notes about the same selected content. Assess resulting orderings, not whether
a particular uncalibrated integer is uniquely correct.
