# Review the segments

Each screen presents one actual segment. Tab cycles through its vectors, showing each complete original note with that vector's mask inline. Judge the highlighted meanings as a group. No subject titles or assistant verdicts are shown.

Start here:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
E=sse_multivector/real-note-fine-segmentation-v1
./target/debug/fine-segmentation-review \
  "$E/review-handoff/baseline/review.json" \
  "$E/review-handoff/baseline/user-session.json" \
  "$E/review-handoff/baseline/user-response.json"
```

This uses the already-built executable; Cargo and direnv are not required. Run the same command to resume. The first 43 segments contain masks from multiple notes; the remaining 209 contain masks from one note. All are retained, and you do not need to review them all.

- Tab / Shift-Tab: next / previous mask in this segment.
- Left / Right: previous / next segment.
- Up / Down or Ctrl-D / Ctrl-U: scroll the original note.
- V / I / U, then Enter: record Valid / Invalid / Uncertain.
- C: optional comment. S: skip. Ctrl-C: save and exit.

Your decision applies to the complete segment, not only the currently displayed mask. Several vectors can come from the same note. `V...` identifies a vector and its mask; `S...` identifies an exact set of vectors. These IDs retain their meaning across runs.

## Compare the alternatives

These are different partitions of the same frozen vectors, not extra groups to combine with the baseline. Neither alternative is declared the winner.

| Review set | HDBSCAN change from baseline | New or changed segments to inspect | Identical segments already in baseline |
|---|---|---:|---:|
| `baseline` | None: min_samples 2, min_cluster_size 2, EOM | 252 | — |
| `leaf` | Select the smallest retained groups instead of EOM groups | 15 | 245 |
| `density` | min_samples 3 instead of 2; keep EOM | 67 | 52 |

For either alternative, replace **all three** occurrences of `baseline` in the command with `leaf` or `density`. Each has its own empty user session. Identical groups are omitted from the alternative review screens only; they remain in that run's full result and are mapped in `manifest.json`. No different groups have been combined because they appear similar.

All masks left ungrouped are also preserved, with complete original notes and inline highlights:

- [Baseline ungrouped masks](../hdbscan-baseline/review/unassigned.txt)
- [Leaf ungrouped masks](../hdbscan-leaf/review/unassigned.txt)
- [Density ungrouped masks](../hdbscan-density/review/unassigned.txt)

The full, unfiltered segment lists are `../hdbscan-baseline/review/review.json`, `../hdbscan-leaf/review/review.json`, and `../hdbscan-density/review/review.json`, relative to this directory. My assessments are separate files in the experiment directory; they are not loaded by this tool.
