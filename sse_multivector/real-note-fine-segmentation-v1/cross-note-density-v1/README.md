# Cross-note density: results

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

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

The historical review and hierarchy commands below require the original local
artifacts and executables.

This opens only the 41 new or changed multi-note segments, with exact bracketed mask fragments. The 23 unchanged segments remain in the complete trial result and are not presented again. Your earlier answers are not copied into this new session.

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
R=sse_multivector/real-note-fine-segmentation-v1/cross-note-density-v1
./target/debug/fine-segmentation-review "$R/review.json" "$R/user-session.json" "$R/user-response.json"
```

Use the same command to resume. To inspect all 64 trial segments, the complete review artifact is `../hdbscan-cross-note/review/review.json`; use separate session and response paths.

## Explore the saved HDBv2 hierarchy

This read-only explorer shows the complete saved condensed tree, not only the 64 selected segments. It preserves all 130 groups and their nested memberships. No titles, new segmentation, or review decisions are added. Inspecting this structure does not select it as the final navigation hierarchy.

In this raw view, a direct parent mask is hidden if its source note appears anywhere in a child subtree, however deep. Collapsed children count too; expanding or visiting a group does not change this rule. Masks from notes absent from those child subtrees remain visible, and leaf masks are unchanged. An entirely hidden parent-mask list leaves no empty heading. This changes only the displayed rows: saved masks, memberships, and note counts remain intact. The separate `--selection` view does not apply this filter.

```sh
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-hdbscan-hierarchy.sh
```

It starts at group 1043, with its immediate children collapsed. Use **j/k** or ↓/↑ to select and **h/l** or ←/→ to collapse/expand. **U** shows the parent while keeping expanded descendants nested and preserving selection. In this raw view, going up places that parent's unopened children above its expanded children. Their displayed order then stays fixed while you open or collapse them; the saved child order is unchanged. **Enter** on a mask opens its full original note with inline brackets; **Esc** returns. **F** focuses a selected group, **?** opens help, and **Q** quits. Optional argument `916` starts at the root instead.

In the tree, notes, and help, **gg/G** go to the beginning/end, **Ctrl-F/B** scroll a page down/up, and **Ctrl-U/D** scroll half a page up/down. **j/k** scroll in notes and help. Existing arrow, Home/End, and PgUp/PgDn bindings remain available.

Note counts include descendants and count each source note once per group. Siblings may contain vectors from the same note, so their note counts are not additive. Identical masks from one note sharing a vector appear once with all their original IDs; merely overlapping masks remain separate.

The script runs the existing binary without rebuilding. After a fresh checkout, build it once in the development shell with `cargo build --bin hdbscan-hierarchy`. To check the saved inputs without opening a terminal UI:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
D=sse_multivector/real-note-fine-segmentation-v1
./target/debug/hdbscan-hierarchy "$D/hdbscan-cross-note/response.json" \
  "$D/vectors/vector-map.json" "$D/reviewed-input.json" --check
```

## HDBv3: exclude same-note connections

HDBv3 is a diagnostic variant of HDBv2, not an adopted replacement. It tests the first of the four hierarchy concerns: whether same-note connections are responsible for questionable parent placements. The other concerns remain deferred. The parallel music-corpus experiment is separate and its inputs, outputs, and instructions were not changed by this run.

**Result:** HDBv3 offers the coffee-making and hot-coffee notes together without the chicken-and-egg diary. The earlier HDBv2 tree did not offer that membership. Subsequent source tracing distinguishes that improvement from accepted SSE misses and from useful groups that exist before condensation but are not separately offered afterward. This is not a complete semantic validation or an adopted replacement.

### Control and change

The control is the saved HDBv2 result in `../hdbscan-cross-note/response.json`. HDBv3 uses exactly the same 100 notes, 945 original vector records, 916 unique vectors, masks, source-note assignments, density distances, and settings: `min_samples=2`, `min_cluster_size=2`, excess-of-mass selection.

The only request change is `candidate: hdbscan_cross_note` → `candidate: hdbscan_cross_note_edges`. Before building a new minimum spanning tree, HDBv3 excludes every connection whose two vectors come only from the same note. It then rebuilds the complete hierarchy and selected groups. It does not merely cut edges from the saved tree. If identical vectors have aliases from different notes, those aliases can still supply a genuine cross-note connection.

The isolated new binary first reproduced the **complete HDBv2 result exactly**. HDBv3 then ran twice with identical complete responses. Canonicalization, all core distances, the complete mutual-reachability distance matrix, and configuration were exactly unchanged. The old result, vector map, notes, and request remained byte-identical. See proof.json (`../hdbv3-cross-note-edges-v1/proof.json`).

In the following examples, V IDs and N IDs retain their original meanings. Group IDs belong to a particular run: HDBv2 group 1004 and HDBv3 group 1004 are not presumed to contain the same vectors. comparison.json (`../hdbv3-cross-note-edges-v1/comparison.json`) matches **every old group by vector membership**, and includes each tree's nested children, direct masks, complete vector and note sets, and the lowest-distance saved connections crossing each old group's boundary.

### 1. Eggs moved out of the coffee branch

These unchanged masks explain the original connection:

- V342 · N043: ⟦Fetching coffee⟧
- V504 · N060: ⟦Made⟧ ⟦coffee with raw cream⟧ ⟦today⟧
- V506 · N060: ⟦Made my coffee⟧ ⟦raw cream⟧ ⟦raw egg yolk today⟧
- V738 · N080: ⟦clutch of eggs⟧ ⟦receding⟧

In HDBv2, the saved connection path was V342 → V504 → V506 → V738. The middle connection joined two masks from N060. Its full source note is:

> Made my coffee with raw cream and a raw egg yolk today #coffeechain

The egg group, HDBv2/1004, sat beside the coffee-heavy group, HDBv2/1003, beneath HDBv2/999. That common parent contained 56 unique vectors from 24 notes.

HDBv3 excludes V504–V506. The 12 old egg-group vectors remain together in HDBv3/1090, with one additional egg mask from an already represented note:

> V163 · N023: ⟦My⟧ ⟦eggs⟧ ⟦1 always breaks, classic⟧

That group now sits outside the coffee branch. HDBv3/1045 is coffee-heavy and contains V342 and V504, but not N080. HDBv3/1090 contains V506, V738 and the other egg masks. Their smallest common parent is now HDBv3/1021: 323 vectors from 84 notes, rather than the former 56-vector, 24-note parent.

The strongest remaining route between the coffee and egg examples passes through cross-note breakfast masks, including V124/N017, ⟦Now time for a late breakfast⟧, and V736/N080, ⟦My guests had scrambled eggs for breakfast⟧. The largest connection distance on the route rises from **0.776557 to 0.894378**, so those examples join later, in a much broader group. These are HDBSCAN connection distances, not cosine scores; smaller distances connect earlier.

**What this supports:** excluding same-note connections removes this particular placement while preserving the egg material. N060 still legitimately appears through its coffee masks and its coffee-with-egg masks. This does not establish that every new ancestor is semantically correct, or isolate the effect of excluding V504–V506 from excluding the other same-note connections.

### 2. Greetings still connect to coffee

HDBv2 connected these masks in order:

- V503 · N060: ⟦Made⟧ ⟦coffee⟧ ⟦today⟧
- V494 · N058: ⟦coffee⟧ ⟦hot⟧ ⟦this AM⟧
- V495 · N058: ⟦Glad⟧ ⟦coffee⟧ ⟦hot⟧ ⟦AM⟧
- V120 · N017: ⟦Good morning⟧

HDBv3 removes V494–V495, the same-note connection. But it finds a cross-note alternative:

> V494 · N058: ⟦coffee⟧ ⟦hot⟧ ⟦this AM⟧
>
> V647 · N071: ⟦Good morning frens⟧

Consequently, a greeting group still sits beside coffee material: HDBv3/1046 and HDBv3/1045 are children of HDBv3/1037. The new greeting group contains all six old greeting-group vectors plus V496/N058, ⟦brrr⟧ ⟦Glad⟧ ⟦coffee⟧ ⟦hot⟧ ⟦AM⟧. This sibling relationship is not itself a demonstrated placement failure. Both old and new greeting groups return the same six notes, all of whose complete posts contain greetings; N058 starts with “GM Nostr! Happy Sunday!”

The separate “GM” and “Good morning” groups meet only near the root, even in the complete merge history. For example, V805/N089, ⟦Gm nostr⟧, has cosine 0.5568 with V766/N081, ⟦gianguja jars⟧ ⟦store⟧, but only 0.1912 with V824/N092, ⟦Good morning nostr⟧. No narrower shared greeting group was discarded by condensation. The user accepts this abbreviated-versus-spelled-out greeting miss as a limitation of the current SSE representation; it is not a reason to modify the hierarchy algorithm. This does not revoke the separate user rejection of V766's individual membership.

### 3. Changed groups need note-level interpretation

| HDBv2 group | HDBv3 result |
|---|---|
| 1043: brisket/smoker and crockpot material | Exactly preserved as 1114, including the same two child memberships as 1115 and 1116. |
| 1011: music at coffee shops | Exactly preserved as 1050. |
| 1031: four chicken-stock masks from two notes | Split into two two-mask groups, 1108 and 1110. Their smallest common parent now contains 44 vectors from 21 notes. |
| 980: chocolate/tea quantities and concern about their effects | All six masks remain together in 1022, but it adds V098/N013: ⟦today⟧ ⟦batch⟧ ⟦chicken stock⟧ ⟦Should get around 25 quarts⟧. This is a changed grouping, not a verified preservation of the same meaning. |

The chicken-stock example changes how mask variants are grouped. HDBv2 connected V092/N013, ⟦stock pots rolling today⟧ ⟦batch of chicken stock⟧, to V094/N013, ⟦stock pots rolling⟧ ⟦chicken stock⟧ ⟦We save carcasses when we butcher⟧, through two masks from N026:

- V196: ⟦Today i⟧ ⟦Acquired⟧ ⟦prepared⟧ ⟦tomato’s⟧ ⟦Made⟧ ⟦yogurt⟧ ⟦bagged⟧ ⟦chicken meat⟧ ⟦made⟧ ⟦chicken stock⟧ ⟦cleaned⟧ ⟦dishes⟧
- V206: ⟦i⟧ ⟦rotisserie chickens⟧ ⟦bagged⟧ ⟦meat⟧ ⟦made⟧ ⟦chicken stock from the bones⟧

Removing V196–V206 also removes a connection between two masks that genuinely share chicken-stock meaning. The strongest remaining path between V092 and V094 has a largest connection distance of **0.804264**, up from **0.761153**. Their pairs now meet only within a much larger group. However, **each new pair independently returns both N013 and N026**. This is not a demonstrated loss of note discovery; preserving those four particular mask variants in one node was not the objective.

The chocolate-and-tea example is different. HDBv3's complete merge history contains exactly the six old masks at raw node **1204**, forming at connection distance 0.860736. Raw node **1254** adds the stock-production mask V098 at 0.877109. Condensation keeps the seven-mask branch as group **1022**. When the single stock mask departs, only one branch remains above the minimum size of two vectors, so it keeps the same identity instead of producing a six-mask child. The saved data contains the narrower group, but the condensed-tree viewer does not offer it separately. Raw merge IDs and condensed group IDs are different namespaces, even within one run.

### Whole-tree changes and limits

| | HDBv2 | HDBv3 |
|---|---:|---:|
| Same-note-only connections in the minimum spanning tree | 435 | 0 |
| Total connections in that tree | 915 | 915 |
| Groups in the complete condensed hierarchy | 130 | 201 |
| Longest path, in edges | 42 | 71 |
| Parent–child edges returning identical note sets | 15 | 41 |
| Selected groups | 64 | 96 |
| Original vector records in selected groups | 266 | 379 |

All 945 original vector records and all 100 notes remain in the complete hierarchy. Selected-group counts describe the separate excess-of-mass selection, not deletion from the raw hierarchy. Fifty-four old hierarchy groups retain exactly the same vector membership somewhere in HDBv3; 38 old selected groups remain selected with exactly the same membership.

The greater depth and repeated note sets are measured costs. More selected groups do not establish higher semantic quality. This run has not received a complete human review of all 201 groups. The unchanged user-rejected greeting/jar group, HDBv2/935 → HDBv3/957, also demonstrates that the change does not resolve every previously identified problem. The bread/spaghetti group remains user-accepted evidence, not a failure target. The subsequently approved note-navigation comparison below addresses only which existing merge-tree memberships to offer.

**Conclusion:** same-note connections can materially affect parent placement. The coffee example improves; the chicken-stock split does not establish lost note discovery; the shared greeting miss is accepted; and the narrower chocolate-and-tea group exists before condensation. Keep HDBv3 as diagnostic evidence. These findings motivate inspecting a different simplification of its saved merge tree, not changing SSE or the merge rule.

### Reproduce the diagnostic

The new candidate is explicit; the old candidates and original launcher retain their defaults. The build used `target/hdbv3-build`, leaving the shared `target/debug` binaries unchanged. No frontier-model calls, new masks, vector generation, or title generation were used. All 108 Rust tests in the relevant suites and three experiment-runner tests passed. The existing raw hierarchy loader also validated all 201 new groups, 916 unique vectors, 945 original IDs and 100 notes. A separate check walked every vector upward through its ancestors and reproduced the recorded memberships and note counts for all 130 old and 201 new groups.

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 sse_multivector/run_cross_note_edges_experiment.py \
  sse_multivector/real-note-fine-segmentation-v1/hdbscan-cross-note \
  sse_multivector/real-note-fine-segmentation-v1/vectors/vector-map.json \
  sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json \
  target/hdbv3-build/debug/fine-segmentation-candidate \
  17fbdd57f29ae8b6930ab5895c5ac3b3cc6fd80c2f73a8945d141b83c1fb6981 \
  target/hdbv3-fresh-replay
```

The output directory must not exist; the runner refuses to overwrite results. Rebuilding the binary can change its checksum: record and explicitly supply the new checksum rather than silently changing the saved run. The saved request (`../hdbv3-cross-note-edges-v1/request.json`), response (`../hdbv3-cross-note-edges-v1/response.json`), comparison (`../hdbv3-cross-note-edges-v1/comparison.json`) and proof (`../hdbv3-cross-note-edges-v1/proof.json`) remain separate from HDBv2 and the music experiment. The original viewer command still opens HDBv2; it was not redirected to this variant.

## Optional HDBv3 note-navigation comparison

This view uses the saved `single_linkage_tree`, not the `condensed_tree` and not the earlier handmade selection. It performs no inference or clustering and writes no result or review files.

By default it applies two rules:

1. Do not offer groups containing fewer than two distinct source notes.
2. Collapse a child when its complete note set equals its parent's. Keep the parent and promote the remaining descendants, preserving each retained group's complete original vector membership.

The hierarchy binary also accepts `--min-notes N` with `--note-navigation` or
`--merge-history`, raising the first rule's minimum while leaving the second
unchanged. The [optional five-note M06 comparison](../../merge-rule-exploration-v1/inspection.md#optional-five-note-view-of-m06)
tests that viewing change. The launcher below still uses the default two-note
minimum; counts in this section describe that unchanged default.

The original local view retains all 916 unique vectors, 945 original IDs, 100 notes, exact masks and aliases. Masks from removed groups belong directly to their nearest retained ancestor. The root remains the full-corpus container. As in the existing raw viewer, a parent mask is hidden if its note appears recursively in any child; this only affects display, not membership.

For the saved HDBv3 data, 915 merge nodes become 246 offered groups. Maximum depth is 54, compared with 71 in the 201-group condensed tree. There are no one-note group choices or parent-child transitions returning identical note sets. The largest child list happens to contain ten groups; ten is not an imposed limit.

The two rules do not deduplicate siblings. One pair remains: children 1013 and 1150 under 1304 both return N007/N076, with different masks. Removing that duplication is not part of this comparison.

```sh
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-hdbscan-hierarchy.sh --note-navigation
```

The comparison starts at merge node **1254**: three notes, with stock mask V098 and a collapsed child **1204** containing the six chocolate-and-tea masks from two notes. Expand 1204 with `l`, focus it with `F`, or open its original notes with Enter. `U` retains nesting while moving upward, placing unopened child groups above opened ones. Vim keys, scrolling and full-note inline masks are unchanged. Help explains that these are **merge-tree IDs, not the condensed-tree IDs used by the old view**.

Other inspected starts are **1090** for coffee (includes N058/N060, excludes N080), and **1023** or **1063** for the two chicken-stock pairs (each returns N013/N026). Pass the start after `--note-navigation`; **1830** opens the root. No subject titles or semantic approval decisions are generated. This restores the demonstrated narrowing step but is not a final hierarchy or a complete semantic review.

The original command without the new flag still opens HDBv2, and `--selection` still opens the earlier manual proposal. The comparison uses the separately built `target/hierarchy-note-view-build/debug/hdbscan-hierarchy`; it does not overwrite the binaries pinned by earlier experiments. On a fresh checkout, build it in the development shell with `CARGO_TARGET_DIR=target/hierarchy-note-view-build cargo build --bin hdbscan-hierarchy`.

## Earlier manual selection of hierarchy levels

This earlier proposal asked whether choosing which **existing groups** to show could produce useful navigation. The user rejected it as incoherent; it is retained for comparison, not adopted. It did not create new groups, move members, or generate titles. The raw tree's saved data remains unchanged; inspecting the separate selection view in the same explorer requires the original local artifacts.

I inspected all 130 groups and their masks. The separate assistant proposal is `hierarchy-selection-v1.json`. It records a decision for every group, the retained ancestor relationships, exact point inventories, source checksums, and unresolved concerns. These are not user approvals.

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

**Conclusion:** selecting levels reveals useful local structure, but this proposal does not yet provide a good complete discovery hierarchy. It is one inspected selection, not proof that every possible selection fails. There was no rerun, retuning, label generation, or membership change.

To inspect the saved selection in the TUI:

```sh
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-hdbscan-hierarchy.sh --selection
```

This starts at root 916. Add a retained group ID, such as `--selection 1030`, to start there instead. The heading says **HDBv2 selection · proposal · read-only**. Children appear before masks outside those children; all masks remain available below them. **j/k** select, **l/h** expand/collapse, **U** goes to the displayed parent without flattening the children, **Enter** on a mask opens the full source note, and **Q** quits. No judgments are saved.

Without `--selection`, the same command still opens the original raw tree at 1043. The selection file is checked against all three source checksums and against the raw ancestry, complete memberships and counts before display. Unknown or skipped starting groups are rejected. The viewer never runs segmentation or changes the proposal.

## Duplicate masks

During review, V814 and V815 were confirmed to contain the same mask ranges from the same original note. Two different subject records produced those identical masks. Their vectors are identical too: HDBSCAN already counted them once, but restoring both original IDs caused both to appear in the reviewer. Six of the 41 displayed segments contain this kind of exact duplicate. Removing those repeated rows would not change any segment's distinct-note count.

The user approved deduplicating such inputs before vector generation in future runs. [The encoding change](../README.md#music-and-coverage-results) preserves subject associations and does not merge merely overlapping masks. No current input, vector, partition, review artifact, or user decision was changed by this decision.

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
