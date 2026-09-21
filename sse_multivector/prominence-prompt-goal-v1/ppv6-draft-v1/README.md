# PPv6 — two views of one mask

Status: draft, not model-tested, frozen or adopted in production.

The user approved presenting the selected fragments separately from the full
note, while also marking their exact occurrences within that note. PPv6 changes
only the input explanation and placeholders from PPv5. Its scoring instructions,
score bands and output format remain unchanged.

## Input contract for a future test

Both views must be rendered by code from the same saved, validated, nonempty
mask and original note, not generated or paraphrased by a model:

- `MARKED_POST`: the complete original note with each selected source range
  enclosed in `⟦` and `⟧`.
- `MASK_FRAGMENTS`: those exact fragments, in source order, each enclosed in
  `⟦` and `⟧`, separated by newlines. Preserve separate fragment boundaries and
  repeated selections; do not deduplicate identical text from distinct source
  positions or add connecting words.

These are two presentations of one mask, not two masks. The separate view makes
the fragments available together; the annotated note preserves which source
occurrences were selected and provides their context. No subject description is
added as an input.

This draft does not implement the renderer or change stored masks, extraction,
SSE, prominence integration or production defaults. Handling literal input
collisions with the display delimiters remains a renderer concern to settle
before testing; no supported case is silently repaired here.

The [PPv3 rationale and remaining limitations](../ppv3-draft-v1/README.md) still
apply except for its single-view input description. The numerical scale remains
provisional. Two views do not resolve cases where identical masks represent
different supported interpretations.

The [official OpenAI guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively)
supports clear input delimiters. It does not establish that this two-view format
outperforms PPv5. No model calls accompany this draft.

`PPv6.md.revision.json` records the exact edits and source/output hashes from the
offline revision tool. PPv5 and frozen PPv2 remain unchanged.

Next suggested step after prompt review: prepare the small saved-note comparison
and verify that both input views contain exactly the same selections before
running a prominence test.
