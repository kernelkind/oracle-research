# HDBv2 coverage follow-up

## What happened

Adding related notes repaired the gianduja placement. It did not cleanly repair all three rejected placements. Adding the same number of other-subject notes left all three original segments unchanged.

| Original mask | With 24 related notes | With 24 other-subject notes |
|---|---|---|
| V766: ⟦gianguja jars⟧ ⟦store⟧ | Leaves greetings; joins three other gianduja posts. User approved the new segment. | Original greeting segment unchanged. |
| V439: ⟦Literature⟧ | Gains two book-related masks, but stays with the old audiobook-criticism masks. User rejected the new segment, identifying V439 as the outlier. | Original segment unchanged. |
| V841: ⟦today is a gift⟧ | Leaves Christmas. User found its new 61-mask segment mostly coherent, but rejected it because V991, ⟦Thanks guys⟧, stands out. | Original Christmas segment unchanged. |

The related-addition user review is complete: **20 valid, 2 invalid, 2 uncertain**, all 24 decisions confirmed. The other-subject review is still pending. Assistant assessments remain saved separately. No segment titles were generated.

The [full source notes with inline masks](target-evidence.md) show each original target and its closest different-note mask before and after the related addition. [Exact scores](target-comparison.json) retain the ten closest different-note vectors for every target in all three runs. The complete segments, not just nearest neighbors, are in the review tool below.

## What changed and what stayed fixed

The question was whether missing related examples contributed to the three bad HDBv2 placements.

- Original: the existing 100 notes and 945 vectors.
- Related addition (`arm-a`): those exact inputs plus 24 notes about gianduja/jarred foods, books, and appreciation of life.
- Other-subject addition (`arm-b`): those exact inputs plus 24 other notes, largely technical, with sports, pets, and music.

Only the additional notes and their derived vectors differ. The old vector bytes, IDs, subjects, masks, and user decisions were not changed. ASv6.23, MPv3.5, Astra low, Sentence-T5-base SSE, normalization, and HDBv2 settings stayed fixed. Each complete partition was rebuilt and independently replayed with the pinned candidate binary; both full parsed responses matched.

HDBv2 still uses the closest vector from a different note for core distance, angular distance, `min_samples=2`, `min_cluster_size=2`, and excess-of-mass selection. No settings were tuned after seeing these results. Exact-mask deduplication before encoding remains separate, unimplemented work; this experiment retained the old encoding path and candidate alias handling.

All 48 original texts were read before generation. All 409 generated subjects and masks were reviewed before encoding: three subject corrections and nine mask corrections were saved separately from the raw outputs. All 457 generation calls used distinct fresh threads; no retries or guard stops occurred. Nothing was regenerated after examining the segments.

## The three placements

**V766:** Its closest different-note mask changes from ⟦Gm nostr⟧, cosine **0.556752**, to ⟦limited edition⟧ ⟦Gianduja⟧ ⟦available⟧, **0.749020**. Its new segment, `Sd621a11e19`, contains six masks from four posts, all about gianduja availability. The remaining greeting masks stay together separately. The original gianduja-to-greeting cosine has not decreased; better neighbors were added and HDBv2 selected a different group.

**V439:** Its closest different-note mask changes from audiobook criticism, **0.609150**, to ⟦Audiobooks⟧ ⟦“read”⟧, **0.667523**. However, `S110c9d7b6f` still contains every member of the rejected original segment, plus that audiobook mask and ⟦non-fiction books⟧ ⟦so much filler⟧. The user rejected this expanded group: “mostly valid. v439 stands out too much”. The independent assistant reviewer had accepted the broader books connection; that assessment does not override the user's rejection.

**V841:** Its closest different-note mask changes from printing Christmas cards, **0.564604**, to ⟦I’m grateful⟧ ⟦present⟧, **0.631959**. The Christmas masks remain together without V841. The user rejected its new segment, `S07e6d2ac71`, but explained: “it's mostly coherent. v991 stands out a bit too much though”. V991 selects only ⟦Thanks guys⟧ from a pecan-product note. This differs from my earlier criticism that the entire life/spirituality group was too diffuse: the user's stated problem is that particular outlier. It is not a claim that V841 still belongs with Christmas, nor approval of a hypothetical group with V991 removed. All 61 masks remain unchanged.

## Changes elsewhere

| Measurement | Original HDBv2 | Related addition | Other-subject addition |
|---|---:|---:|---:|
| Notes | 100 | 124 | 124 |
| Vectors | 945 | 1,141 | 1,158 |
| Multi-note segments | 64 | 73 | 78 |
| One-note segments | 0 | 0 | 0 |
| Grouped vectors | 266 | 364 | 339 |
| Ungrouped vectors | 679 | 777 | 819 |
| Original notes with at least one grouped vector | 78 | 79 | 79 |
| Original vectors gaining a segment | — | 27 | 19 |
| Original vectors becoming ungrouped | — | 8 | 1 |
| Exactly unchanged original segments | — | 49 | 59 |
| New or changed segments to review | — | 24 | 19 |

These counts measure placement, not semantic correctness or recall. Related additions do not dominate the other addition on every measure.

Of the 61 previously accepted original segments, 49 remain exactly unchanged with related additions and 56 with other-subject additions. Twelve and five accepted segments respectively change. The related run leaves eight previously grouped vectors ungrouped, including ⟦How are you today?⟧, Saturday well-wishes, waking-brain wording, two communication masks, and three autumn/frost masks. The other run leaves only the ⟦fall⟧ ⟦definitely here⟧ vector newly ungrouped. This is a cost to inspect, not something hidden by reporting only recoveries.

Every original segment's destination and every original vector's transition are recorded in `arm-a-comparison/comparison.json` and `arm-b-comparison/comparison.json`. Separate assistant assessments cover all 24 and 19 new/changed segments. They are provisional semantic judgments, not user decisions or automatic changes to the data.

## Review

Only new or changed segments are shown. Every displayed segment contains masks from at least two distinct notes. All its masks appear together; scroll for long segments. Unchanged segments remain in the complete results and are not requested again. The two review sessions are independent. The related-addition session is complete; the other-subject session has not been reviewed.

### Your related-addition review

All 24 saved judgments match the confirmed session decisions and the original review artifact: 20 valid, 2 invalid, 2 uncertain.

- `Sd621a11e19`, the gianduja segment: valid.
- `S07e6d2ac71`, containing V841: invalid, with the V991 outlier comment above.
- `S110c9d7b6f`, containing V439: invalid, with V439 identified as the outlier.
- `S67274cded4` and `S8a0cf4f31b`: uncertain, with no comments. The first combines initial-writing masks and ending an overlong note; the second combines gianduja shipping/order timing and choosing fruit for a challenge. Those descriptions are not inferred reasons for the user's uncertainty.
- `Sc2be76b29b`: valid, with “we really need to dedup. it is making it hard to understand...”. Its ten displayed masks include one exact same-note/range duplicate pair, V105/V106, and several distinct overlapping masks. The comment records review friction; it does not choose a broader deduplication rule or authorize removing current evidence.

The user also accepted the philosophy/psychology group that the assistant had marked uncertain, and the grownostr/agroforestr group whose initial assistant interpretation was corrected before this review. Raw assistant judgments and user decisions remain separate and unchanged. No masks were removed, no algorithm rerun, and no prompt or deduplication change was made in response to this review.

Review set: `RNeb4ad12783e3`. Evidence SHA-256:

| File | SHA-256 |
|---|---|
| `arm-a-comparison/review.json` | `8736814a4097fcca50dc2ad8088b3310d562773842e107af0f720c4a46b79ca1` |
| `arm-a-user-response.json` | `81e81837c5b667ed1a071aeaa7dfd2c52a005437875d26cc5cbf7d62ebe54ef1` |
| `arm-a-user-session.json` | `b855b63478a2e5102dd24dc25e577503fa43db6280a7f4e2594606f91f3389f0` |

### Commands

Related addition — 24 segments:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
R=sse_multivector/real-note-fine-segmentation-v1/coverage-expansion-v1
./target/debug/fine-segmentation-review "$R/arm-a-comparison/review.json" "$R/arm-a-user-session.json" "$R/arm-a-user-response.json"
```

Other-subject addition — 19 segments:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
R=sse_multivector/real-note-fine-segmentation-v1/coverage-expansion-v1
./target/debug/fine-segmentation-review "$R/arm-b-comparison/review.json" "$R/arm-b-user-session.json" "$R/arm-b-user-response.json"
```

Use the same command to resume. V001–V945 mean the same original vectors in both runs. Higher V numbers are local to each run; do not equate them across the two additions. Segment IDs identify exact member sets. Full note IDs, source texts, spans, and persistent vector IDs remain in the review files.

## What this supports

The selected related addition changed the three target neighborhoods in ways that the equally sized other-subject addition did not. Gianduja supplies a concrete example where missing related notes contributed to an incorrect placement and additional evidence repaired it without changing the original representation or HDBv2.

This is not evidence that sparsity explains every failure, that more notes necessarily improve every segment, or that HDBv2 is a final algorithm. The literature relationship remains rejected. The life-related group is mostly coherent according to the user but still contains a named outlier. The other-subject run's new groups have assistant assessments, not user judgments. Representation, corpus coverage, and segmentation remain separate sources of uncertainty.

## Limits and saved evidence

- The additions are deliberately selected, not randomized population samples. All three gianduja additions share the original author and product. This does not demonstrate recovery across independent authors or different wording styles.
- Note counts are equal and complete-text lengths are closely matched, but the additions produce different vector counts: 196 versus 213. Their effects cannot be attributed solely to an abstract quantity called topic coverage.
- The other-subject addition is not greeting-free: its Mastodon staffing announcement says “Welcome to the team.” This was recorded before encoding in `input-review-checkpoint.json`; the earlier selection description overstates that exclusion. Neither addition is semantically restricted to its intended area.
- The author-index search found five eligible gianduja posts in the 3.53-million-note source. Three were selected. The separate broad scan timed out; no complete full-pool text search is claimed.
- All old inputs, vector bytes, partitions, and raw user decisions remain unchanged. Of 103 snapshotted files, 102 are byte-identical; concurrent hierarchy work added explorer instructions to `cross-note-density-v1/README.md`. That unrelated edit was preserved and is identified in `preserved-after.json` rather than silently excluded from the audit.
- SSE finished in 19.61 seconds, peaking at 1.32 GiB RAM under a four-CPU, 8-GiB/no-swap limit. Its workload I/O-pressure reading briefly reached 32.47% during startup and then settled to zero. Monitoring was diagnostic: it did not pause the encoder. One final sample failed because the completed container's cgroup had been removed. No further work ran alongside encoding; no OOM was observed. Both HDBv2 runs used a 4-GiB/no-swap, two-CPU scope and ran sequentially.
- Fourteen adapter/helper tests plus 29 relevant existing regression/integration tests pass. Both actual review files were opened successfully in the existing TUI; navigation and scrolling were checked using separate smoke sessions, without recording user judgments.

`final-selection.json` and `notes.json` preserve selection and complete texts. `subjects/` and `masks/` preserve prompts, raw outputs, and fresh-thread receipts. Review corrections and `input-review-checkpoint.json` precede `encoder-input/` and `encoder-run/`. `new-vectors/` stores the 409 new vectors; `arm-*-vectors/`, `arm-*-hdbv2/`, and `arm-*-comparison/` preserve both complete runs and comparisons. `assistant-arm-*-assessment.json` stores independent judgments; `assistant-reconciliation.json` records subsequent interpretation corrections without rewriting those judgments.
