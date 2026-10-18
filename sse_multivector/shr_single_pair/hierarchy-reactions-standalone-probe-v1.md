# Reactions without context v1 — experimental findings

Encoding only the text **reactions** reduces its People-group score to
**0.012325**, versus 0.044577 and 0.041539 when pooling that same word in the
two original contexts. That is a further 70–72% reduction. Context contributes
substantially to the match, but the standalone score still exceeds five of the
six saved contextual-title people-class controls.

This is a context diagnostic, not an admission improvement or uniform
standalone-title evaluation. References and useful controls retain their saved
contextual-title representations. No boundary, membership, meaning or hierarchy
is changed, and no semantic labels are added.

## Controlled comparison

Continue the [reactions pooling probe](hierarchy-reactions-selection-probe-v1.md).
Keep L04535 and L07783, their original source-note identities, and all seven
C00006 reference groups containing 69 entries. The primary People group remains
fused-002: 15 People entries and one Individuals entry.

Reuse all four saved contextual query vectors: each complete title and each
reactions-only selection in its original `title + "\n\n" + meaning` context.
Encode **reactions** by itself once, selecting its whole text. Both source
records point to that one native row because their standalone input is
identical. They are not independent repeats. No reference vector is regenerated.

Use the unchanged native SSE worker, checkpoint, base artifact, 768 dimensions,
512-token maximum, projection/pooling rule and batch size 32. The
[existing adapter](../title_selection_probe.py) now supports `prepare ...
--standalone`; its default contextual preparation is unchanged. Collection
validates native receipts and publishes only the requested view. Original
titles and meanings remain in provenance, rather than being rewritten as the
new encoder input. This diagnostic span is not an MP mask.

Score all conditions against the same contextual-title references, preserving
source-note exclusion and the mean of `exp(-5.5 * (1 - cosine))`. Keep the
existing six people-class controls and provisional judgments fixed.

## Results

These are mean-support scores, not cosine similarities or probabilities.

| Source entry | Full title in original context | Reactions in original context | Reactions alone | Saved useful classes outranked, original title → contextual reactions → alone |
|---|---:|---:|---:|---|
| L04535 | 0.067404 | 0.044577 | 0.012325 | 6/6 → 5/6 → 5/6 |
| L07783 | 0.064796 | 0.041539 | 0.012325 | 6/6 → 5/6 → 5/6 |

Raw mean cosine against the 16 People references decreases from 0.434016 and
0.421092 for contextual reactions to 0.200514 for reactions alone. The
standalone/contextual-reactions vector cosines are 0.818604 and 0.810524.

The exact selected token ID is **14081** in all three reactions-only views.
The context changes its position, but not its token identity. Tokenization into
different words does not explain the result. Prior scores replay exactly when
their saved vectors are reused; every query/reference and query/group score is
retained.

The remaining ordering compares a standalone wrong topic with contextual useful
topics. It does not establish that a consistently applied standalone-title
method fails or succeeds. Bare reactions also loses the audience qualification;
it is a mechanism control rather than a faithful replacement for either topic.
The subsequent [standalone people-class control](hierarchy-people-standalone-controls-v1.md)
is complete: three of six useful witnesses, representing two of five distinct
titles, now outrank reactions. Racing drivers, Astronauts and Australians still
score lower. This partial change does not establish a separating score.
This result does not qualify head-word extraction or context removal as an
admission policy; the conservative candidate is retained unchanged.

## Evidence and checks

Ignored evidence remains in
`target/food-halves-v1/hr38-reactions-standalone-v1/`, through the existing
external-storage symlink. The research worktree is retained for source bindings
and these artifacts.

- Plan SHA256, frozen before the new vector:
  `e20744502ac36cbea5b8c83543c8b278b75e359dcaddae51275883c8cef82928`.
  All 44 analysis source bindings remain unchanged. Original adapter identity
  is verified from commit `bdeed884` against the preceding frozen inputs, while
  the new request pins the current adapter. Historical receipts stay intact.
- One new context and one native vector; two provenance records share it.
  Native bytes, request/config/receipt identities, exact selected text and
  unchanged source records are validated independently.
- Independent scalar reconstruction checks 414 pair cosines and 42 group means,
  with maximum error `3.34e-16`; previous contextual scores replay exactly.
- A new production-path test first failed on the missing standalone option.
  It now checks exact context removal, UTF-8 spans, deduplication into one native
  row, preserved evidence and native worker collection. All **16 native/adapter
  tests and 65 numerical tests pass**, without skips, in their existing pinned
  Torch and NumPy/SciPy environments.
- No LLM calls, training, paid resources, new admission, prompt/hierarchy/UI
  changes or official HR construction.
