# Cross-note density: results

You completed the 41-segment review: **37 Valid, 4 Invalid**, with every decision confirmed. The complete rerun produced more multi-note segments, but it did not resolve the six exact omitted pairs you approved. This review does not select it as a replacement for the baseline.

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

## Your review

All 41 new or changed multi-note segments have confirmed decisions. None was skipped or left pending. You accepted 37 and rejected these four:

| Segment | Your comment |
|---|---|
| S14b6e36e21 | “v766 does not belong” |
| S3d2aa08f70 | “v439 is very different from the others” |
| S68ce4fd21f | “v841 does not seem related. others do” |
| Saadde5a7ec | No comment |

The first three comments identify a specific unwanted member. For the fourth rejection, you later clarified in chat that “allotment efforts” is too generic. After seeing its supplied subject and full source note, you concluded: “this is a masking failure.” The saved empty comment above remains unchanged.

V257 was generated for subject N031-S007, “The author loves someone’s allotment gardening efforts.” Its mask is `⟦I love⟧ ⟦allotment efforts⟧`. The note supplies concrete gardening context through “Growing your own” and “homegrown tomatoes,” but that text is outside the mask. The diagnosis is that the mask does not adequately express the supplied subject, not that the source note lacks that meaning. SSE received the complete note, so this rejection does not by itself establish a segmentation failure. The earlier assistant judgment missed this masking issue.

No mask, vector, member, or review decision has been changed. The appropriate mask correction remains open; this diagnosis does not authorize a prompt change, rerun, or algorithm change.

Two decisions directly differ from my earlier judgments: you accepted S72d277b43a (bread masks plus the spaghetti preparation mask), which I marked Invalid; you rejected Saadde5a7ec, which I marked Valid. Your decisions and my original assessment remain separate. In particular, the spaghetti member is not a user-confirmed failure.

The saved response and session both bind to review set `RN30ea35e75a20` and review-artifact SHA-256 `77bda6b0747cc0aec0dc4305b6f1ef6f2302ac3055173d6965a7f4736506dbea`. Response SHA-256: `cc21a5e9b5963b59e1c5035c84a8362534d02c89efbc61c5e9084b659546e9ee`. Session SHA-256: `92f2aca83650c974a7dd7fa3b8ff858aa1dba36abb718bb7a44fd5bc70e802d0`. These local user files were inspected, not modified or added to Git.

## My assessment before your review

I read every mask in all 41 changed segments: 30 looked valid, 8 remained uncertain, and 3 looked invalid. These are my judgments, not an accuracy score or your review decisions. No labels were generated or supplied to the reviewer.

I had marked these three segments Invalid:

- S14b6e36e21 puts `⟦gianguja jars⟧ ⟦store⟧` among five greeting masks such as `⟦GM⟧`.
- S68ce4fd21f puts `⟦today is a gift⟧` among Christmas and Santa masks. The metaphor does not establish a Christmas connection.
- S72d277b43a puts `⟦Spaghetti Bolognaise⟧ ⟦Mix all ingredients thoroughly.⟧ ⟦Simmer⟧` among fifteen bread masks.

Your review agreed on the first two rejections but accepted the third. The original assistant-assessment file is preserved rather than rewritten to match your answers.

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
