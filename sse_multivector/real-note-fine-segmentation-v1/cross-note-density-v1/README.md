# Cross-note density: results

The complete rerun produced more multi-note segments, but it did not resolve the six exact omitted pairs you approved. It also introduced some questionable groupings. This is not yet a replacement for the baseline.

All previous results and review decisions are unchanged. Checksums match for all 65 preserved files.

## What changed

All 945 vectors stayed fixed. Previously, a vector's closest neighbor could come from the same note. For this trial's density calculation, that neighbor had to come from another note. HDBSCAN then rebuilt the entire hierarchy and selected segments again, with the remaining settings unchanged.

| | Baseline | Cross-note trial |
|---|---:|---:|
| Segments containing multiple notes | 43 | 64 |
| Vectors in those segments | 150 | 266 |
| Segments containing only one note | 209 | 0 |
| Vectors left ungrouped | 162 | 679 |

The rise in ungrouped vectors is largely the disappearance of one-note groups. It is not a loss of that many previously demonstrated cross-note relationships: 128 vectors gained a multi-note segment, while 12 lost one.

Of the 43 baseline multi-note segments, 23 are exactly unchanged. Eleven retain all their members together in an enlarged segment. Nine lose some members to the ungrouped set. The trial contains 41 new or changed segments for review.

## The known omitted pairs

None of the six exact user-approved pairs is together in a selected trial segment. All six remain recorded in `comparison.json`; no pair was forced into a group.

There is a useful qualification. V709, `⟦chef⟧`, now shares S49eb0ac749 with V551, `⟦kitchen⟧ ⟦Today meat dumplings⟧`. V551 comes from the same note as the approved partner V553, `⟦kitchen⟧ ⟦work⟧ ⟦dumplings⟧`. V553 itself remains ungrouped. The new result therefore finds a related connection without recovering that exact reviewed pair.

Of the five user-rejected pairs, one is now grouped: V742 and V439 in S3d2aa08f70. The other four remain apart. Separately, two of the 28 assistant-only accepted pairs are now together; those are not user approvals or evidence that their complete new segments are valid.

## My inspection

I read every mask in all 41 changed segments: 30 looked valid, 8 remained uncertain, and 3 looked invalid. These are my judgments, not an accuracy score or your review decisions. No labels were generated or supplied to the reviewer.

Three concrete concerns:

- S14b6e36e21 puts `⟦gianguja jars⟧ ⟦store⟧` among five greeting masks such as `⟦GM⟧`.
- S68ce4fd21f puts `⟦today is a gift⟧` among Christmas and Santa masks. The metaphor does not establish a Christmas connection.
- S72d277b43a puts `⟦Spaghetti Bolognaise⟧ ⟦Mix all ingredients thoroughly.⟧ ⟦Simmer⟧` among fifteen bread masks.

The change removes the opportunity for same-note neighbors alone to establish a short core distance. It does not make the remaining cross-note neighbors semantically correct, and it does not remove repeated same-note contributions from cluster stability. The full rerun demonstrates both gains and costs; it does not justify changing more settings automatically.

## Review

This opens only the 41 new or changed multi-note segments, with exact bracketed mask fragments. The 23 unchanged segments remain in the complete trial result and are not presented again. Your earlier answers are not copied into this new session.

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
R=sse_multivector/real-note-fine-segmentation-v1/cross-note-density-v1
./target/debug/fine-segmentation-review "$R/review.json" "$R/user-session.json" "$R/user-response.json"
```

Use the same command to resume. To inspect all 64 trial segments, the complete review artifact is `../hdbscan-cross-note/review/review.json`; use separate session and response paths.

## Duplicate masks

During review, V814 and V815 were confirmed to contain the same mask ranges from the same original note. Two different subject records produced those identical masks. Their vectors are identical too: HDBSCAN already counted them once, but restoring both original IDs caused both to appear in the reviewer. Six of the 41 displayed segments contain this kind of exact duplicate. Removing those repeated rows would not change any segment's distinct-note count.

The user approved deduplicating such inputs before vector generation in future runs. [The pending encoding change](../README.md#current-checkpoint) preserves subject associations and does not merge merely overlapping masks. No current input, vector, partition, review artifact, or user decision was changed by this decision.

## Records

- `protocol.md`: the change and comparison declared before running.
- `comparison.json`: every baseline segment's destination, exact memberships, all eleven user-reviewed pairs, and short vector IDs.
- `assistant-assessment.json`: my separate judgment of every changed segment.
- `preserved-before.json` and `preserved-after.json`: preservation evidence.
- `../hdbscan-cross-note/`: the request, full result, identical replay, and complete review evidence.
- `baseline-recheck/`: the original baseline request rerun using the new binary. Its complete algorithm result equals the saved baseline exactly; only the implementation-source hashes changed.
- `verification.md`: tests, numerical checks, terminal smoke test, and resources.

Recheck preservation without changing anything:

```sh
python3 sse_multivector/real-note-fine-segmentation-v1/compare_cross_note.py verify-preserved
```
