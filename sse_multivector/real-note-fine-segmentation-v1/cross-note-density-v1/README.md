# Cross-note density: results

Your current judgments are **38 Valid, 3 Invalid**, including the later retraction of the garden/allotment rejection. The original saved review contains 37 Valid and 4 Invalid decisions and remains unchanged. Contextual re-examination is complete: you reaffirmed the V766, V439, and V841 grouping rejections after inspecting their full notes. The complete rerun produced more multi-note segments, but it did not resolve the six exact omitted pairs you approved. This review does not select it as a replacement for the baseline.

All previous result and saved-review files are unchanged; chat revisions are recorded below. Checksums match for all 65 preserved files.

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

All 41 new or changed multi-note segments have confirmed saved decisions. None was skipped or left pending. The original response accepted 37 and rejected these four; subsequent chat decisions follow the table:

| Segment | Your comment |
|---|---|
| S14b6e36e21 | “v766 does not belong” |
| S3d2aa08f70 | “v439 is very different from the others” |
| S68ce4fd21f | “v841 does not seem related. others do” |
| Saadde5a7ec | No comment |

The first three comments identify a specific unwanted member. For the fourth rejection, you later clarified in chat that “allotment efforts” is too generic. After seeing its supplied subject and full source note, you concluded: “this is a masking failure.” You then explicitly retracted the Invalid grouping decision: “hdbscan did a good job here, it was masking which did not.” Saadde5a7ec is therefore Valid in the current assessment. The saved original decision and empty comment above remain unchanged.

V257 was generated for subject N031-S007, “The author loves someone’s allotment gardening efforts.” Its mask is `⟦I love⟧ ⟦allotment efforts⟧`. The note supplies concrete gardening context through “Growing your own” and “homegrown tomatoes,” but that text is outside the mask. The diagnosis is that the mask does not adequately express the supplied subject, not that the source note lacks that meaning. SSE received the complete note; the user accepts the grouping once that meaning is visible. The earlier assistant judgment missed the masking issue.

You also agreed to retain S14b6e36e21's Invalid judgment after full-note inspection. V766's subject is “Gianduja as a food product offered in jars.” Its mask, `⟦gianguja jars⟧ ⟦store⟧`, comes from a product announcement with no greeting elsewhere in the note. The other five masks explicitly express greetings. Unlike the allotment example, context does not clarify V766 into the shared meaning. This confirms an inappropriate grouping without isolating an SSE or HDBSCAN cause.

You reaffirmed S3d2aa08f70's rejection after inspecting V439's full note and the three audiobook masks: “agree w reject.” V439's supplied subject is “Literature.” Its mask faithfully selects `⟦Literature⟧` from a closing hashtag; the rest of the note does not supply a narrower audiobook meaning. The other masks describe an unsatisfying audiobook. The assistant noted their broad literary relationship but did not identify a missing-context masking failure. Your grouping rejection remains in force; the cause is not isolated.

You reaffirmed S68ce4fd21f's rejection after inspecting V841's full note and the eight other masks. V841's subject is “Today is a gift to appreciate.” Its mask, `⟦today is a gift⟧`, preserves that meaning. The note describes an ordinary Saturday: preparing lunch, considering bathroom grab bars, and checking chicks. It supplies no Christmas meaning that would explain placement among the Santa and Christmas masks. You agreed that the grouping remains invalid; this is not the allotment masking issue. All three contextual re-examinations are complete, but no SSE-versus-HDBSCAN cause has been isolated.

No mask, vector, member, or saved review file has been changed. The appropriate allotment mask correction remains open; these decisions do not authorize a prompt change, rerun, or algorithm change.

The original saved review had two direct disagreements with my earlier judgments: you accepted S72d277b43a (bread masks plus the spaghetti preparation mask), which I marked Invalid; you initially rejected Saadde5a7ec, which I marked Valid. Your later retraction resolves the latter grouping disagreement while identifying a masking problem. Your decisions and my original assessment remain separate. In particular, the spaghetti member is not a user-confirmed failure.

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

## Explore the saved HDBv2 hierarchy

This read-only explorer shows the complete saved condensed tree, not only the 64 selected segments. It preserves all 130 groups and their nested memberships, including masks that belong to a parent outside its child groups. No titles, filtering, new segmentation, or review decisions are added. Inspecting this structure does not select it as the final navigation hierarchy.

```sh
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-hdbscan-hierarchy.sh
```

It starts at group 1043, with its immediate children collapsed. Use **j/k** or ↓/↑ to select and **h/l** or ←/→ to collapse/expand. **U** shows the parent while keeping expanded descendants nested. **Enter** on a mask opens its full original note with inline brackets; **Esc** returns. **F** focuses a selected group, **?** opens help, and **Q** quits. Optional argument `916` starts at the root instead.

In the tree, notes, and help, **gg/G** go to the beginning/end, **Ctrl-F/B** scroll a page down/up, and **Ctrl-U/D** scroll half a page up/down. **j/k** scroll in notes and help. Existing arrow, Home/End, and PgUp/PgDn bindings remain available.

Note counts include descendants and count each source note once per group. Siblings may contain vectors from the same note, so their note counts are not additive. Identical masks from one note sharing a vector appear once with all their original IDs; merely overlapping masks remain separate.

The script runs the existing binary without rebuilding. After a fresh checkout, build it once in the development shell with `cargo build --bin hdbscan-hierarchy`. To check the saved inputs without opening a terminal UI:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
D=sse_multivector/real-note-fine-segmentation-v1
./target/debug/hdbscan-hierarchy "$D/hdbscan-cross-note/response.json" \
  "$D/vectors/vector-map.json" "$D/reviewed-input.json" --check
```

## Manual selection of hierarchy levels

The approved follow-up asks whether choosing which **existing groups** to show can produce useful navigation. It does not authorize new groups, moved members, generated titles, or adoption of HDBSCAN. The raw explorer and its inputs remain unchanged.

I inspected all 130 groups and their masks. The separate assistant proposal is [hierarchy-selection-v1.json](hierarchy-selection-v1.json). It records a decision for every group, the retained ancestor relationships, exact point inventories, source checksums, and unresolved concerns. These are not user approvals.

| | Raw tree | This proposal |
|---|---:|---:|
| Exposed groups, including root | 130 | 55 |
| Longest path, in edges | 42 | 4 |
| Choices immediately below root | 2 | 34 |

Every other retained parent has at most nine children. No retained parent has only one child, no child returns exactly its parent's note set, and no siblings return identical note sets. These structural checks do **not** establish that the choices are semantically good.

One useful local selection is:

```text
990
└─ 1030
   ├─ 1038
   └─ 1043
      ├─ 1044
      └─ 1045
```

This excerpt omits 990's other children, which remain in the proposal. Group 1044 contains the brisket/smoker masks; 1045 contains the crockpot stew/roast masks. Group 1038 mostly concerns food quality and intake. Skipping intermediate groups shortens the route while preserving these distinctions. V843's compound crockpot/chicks/homesteading mask remains directly in 1043; it was not removed to make the example cleaner.

The whole-tree result is less satisfactory. Of 916 unique vectors, **600 have no retained group below the root**. They remain in the root inventory, not deleted. The other 316 vectors represent 81 notes. Nineteen notes have no retained non-root destination; thirty have no retained terminal-group destination. Parent-only masks elsewhere also remain, so this is not yet a solution where all notes are reached only at leaves.

Skipping levels exposes many small groups without supplying better shared parents. For example, group 958's tea masks and group 972's wine masks first meet at existing group 955, which contains 495 vectors from 92 notes—not just beverages. We cannot create a smaller common parent for them merely by skipping levels.

The three user-rejected groups remain unchanged internally but are not proposed as choices. The accepted allotment group and accepted bread/spaghetti group retain their prior decisions. New assistant concerns remain explicitly separate, including standalone sleep and the dog-emoji mask within 1003.

**Conclusion:** selecting levels reveals useful local structure, but this proposal does not yet provide a good complete discovery hierarchy. It is one inspected selection, not proof that every possible selection fails. There was no rerun, retuning, label generation, new UI mode, or membership change. The JSON is an audit artifact; the existing explorer still shows the raw tree.

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
