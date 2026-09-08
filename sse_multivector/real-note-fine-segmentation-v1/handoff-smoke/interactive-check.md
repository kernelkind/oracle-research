# Final review-interface check

Verified on 2026-09-08 UTC using the real `target/debug/fine-segmentation-review` executable in a 110-column, 34-row terminal. No source-code changes were needed for this final check.

All three final inputs opened successfully:

- `review-handoff/baseline/review.json`: 252 segments.
- `review-handoff/leaf/review.json`: 15 changed segments.
- `review-handoff/density/review.json`: 67 changed segments.

The first baseline screen showed S0a3823e53e and V088's complete original note with `Cheese Doodle` highlighted. Tab changed to V579's complete cheesecake note with its different mask. Segment navigation reached S18bc272886; Ctrl-D revealed V440's final `dogstr` highlight, and Up scrolled back. Instructions, IDs, comments and decisions remained outside the original-note box.

A comment was saved on S18bc272886, then the segment was skipped and the program exited with Ctrl-C. Relaunch restored the next segment. Returning to S18bc272886 showed the exact comment and skipped state. Tab switched to V382, and the saved session retained that mask position. The baseline smoke response has no judgments.

In the leaf smoke session only, S051b48ba1c received an Uncertain selection, then Enter confirmation, with the comment `Technical persistence test only; ignore this verdict.` Relaunch restored the next segment; returning showed the stored verdict and exact comment. This is a persistence test, not a semantic judgment. The density smoke session was opened and exited without a decision.

These test states exist only under `handoff-smoke/`. They are never copied into `review-handoff/`, where the user's session and response files are initially absent. Saved scroll offsets are not promised; segment, mask position, decisions and comments are preserved.

To reproduce the launch, replace `baseline` with `leaf` or `density` as needed:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
E=sse_multivector/real-note-fine-segmentation-v1
./target/debug/fine-segmentation-review \
  "$E/review-handoff/baseline/review.json" \
  "$E/handoff-smoke/baseline-session.json" \
  "$E/handoff-smoke/baseline-response.json"
```

Do not use the smoke-session paths for the user's review. The actual user command is in `review-handoff/README.md`.
