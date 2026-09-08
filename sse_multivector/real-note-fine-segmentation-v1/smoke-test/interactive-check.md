# Saved-example interactive check

This is a technical check using existing reviewed masks, not a semantic evaluation of the new collection. No new subject or mask calls were made.

The real CLI was launched in a 110-column, 34-row terminal:

```sh
./target/debug/fine-segmentation-review \
  sse_multivector/real-note-fine-segmentation-v1/smoke-test/review/review.json \
  sse_multivector/real-note-fine-segmentation-v1/smoke-test/manual-session.json \
  sse_multivector/real-note-fine-segmentation-v1/smoke-test/manual-response.json
```

Verified on 2026-09-08 UTC:

- The first segment displayed its complete source note with `Bitcoin Block Art` highlighted inline. Instructions and decisions stayed outside the note box.
- Tab changed to the other vector's complete MegaETH source note, showing its five separate fragments, including the explicitly resolved later occurrence of `token`.
- Ctrl-D scrolled the long original note and exposed its final lines; it did not change the vector or mask.
- C, a comment, and Enter saved `Integration smoke only; not a semantic judgment.` without assigning a verdict.
- S preserved the comment, marked the segment skipped, and moved to the next segment. Japanese text and mixed-width characters remained visible with inline masks.
- Ctrl-C saved and exited successfully.
- Launching the same command restored segment 2 of 4. Left returned to the first segment with its skipped state and exact comment intact. Ctrl-C again exited successfully.
- The saved response contains no judgments. These smoke decisions are separate from the eventual user review.

The running binary predated additional save/resume edge-case fixes and their regression run. Final integration admission also requires those tests and a stable-binary baseline replay; see the experiment checkpoint log.
