# Review the segments

Each screen presents all masks in one segment together. Only segments containing at least two distinct notes are shown. Each `V...` identifies one vector's mask; its fragments appear as `⟦first fragment⟧ ⟦second fragment⟧`, separated by spaces. There is no surrounding note text, note carousel, generated subject title, or assistant verdict.

Start here:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
E=sse_multivector/real-note-fine-segmentation-v1
./target/debug/fine-segmentation-review \
  "$E/review-handoff/baseline/review.json" \
  "$E/review-handoff/baseline/user-session.json" \
  "$E/review-handoff/baseline/user-response.json"
```

This uses the already-built executable; Cargo and direnv are not required. Run the same command to resume. The baseline shows 43 segments. The other 209 contain masks from just one note and are hidden from navigation, not removed from the stored experiment. Existing decisions and comments remain saved, including any for hidden segments. You do not need to review every segment.

- Left / Right: previous / next segment.
- Up / Down or Ctrl-D / Ctrl-U: scroll the segment's masks.
- V / I / U, then Enter: record Valid / Invalid / Uncertain.
- C: optional comment. S: skip. Ctrl-C: save and exit.

Your decision applies to every mask in the segment, including any below the visible area. Several vectors can come from the same note, but each displayed segment contains at least two distinct notes. `S...` identifies an exact set of vectors. IDs retain their meaning across runs.

## Compare the alternatives

These are different partitions of the same frozen vectors, not extra groups to combine with the baseline. Neither alternative is declared the winner.

| Review set | HDBSCAN change from baseline | New or changed multi-note segments to inspect | Identical segments already in baseline (unfiltered) |
|---|---|---:|---:|
| `baseline` | None: min_samples 2, min_cluster_size 2, EOM | 43 | — |
| `leaf` | Select the smallest retained groups instead of EOM groups | 3 | 245 |
| `density` | min_samples 3 instead of 2; keep EOM | 23 | 52 |

For either alternative, replace **all three** occurrences of `baseline` in the command with `leaf` or `density`. Each uses a separate user session. Identical groups are omitted from the alternative review inputs; they remain in that run's full result and are mapped in `manifest.json`. The tool additionally hides one-note groups. No different groups have been combined because they appear similar.

All masks left ungrouped are also preserved, with complete original notes and inline highlights:

- [Baseline ungrouped masks](../hdbscan-baseline/review/unassigned.txt)
- [Leaf ungrouped masks](../hdbscan-leaf/review/unassigned.txt)
- [Density ungrouped masks](../hdbscan-density/review/unassigned.txt)

The full, unfiltered segment lists are `../hdbscan-baseline/review/review.json`, `../hdbscan-leaf/review/review.json`, and `../hdbscan-density/review/review.json`, relative to this directory. My assessments are separate files in the experiment directory; they are not loaded by this tool.
