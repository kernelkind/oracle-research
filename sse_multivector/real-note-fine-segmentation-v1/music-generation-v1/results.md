# Music100 and combined200

Both runs are finished. User review is pending. No labels were generated.

| | Original food/drink 100 | Music 100 | Both collections, 200 |
|---|---:|---:|---:|
| Vectors supplied | 945 | 1,057 | 2,002 |
| Segments containing multiple notes | 64 | 53 | 124 |
| Vectors in those segments | 266 | 199 | 495 |
| Vectors left ungrouped | 679 | 858 | 1,507 |
| Notes with at least one grouped vector | 78 | 77 | 157 |

All segments in these runs contain at least two different notes. Having one grouped vector does not mean all subjects in that note were covered.

## What changed when the collections were combined?

The vectors did not change. Every original food vector and every new music vector was reused byte-for-byte. Only the collection supplied to HDBv2 changed; the candidate binary and settings stayed fixed. Each new run was executed twice and its complete outputs matched.

| Original segments | Food/drink | Music |
|---|---:|---:|
| Exactly the same members after combining | 44 of 64 | 35 of 53 |
| All members still together, including groups that gained members | 54 of 64 | 45 of 53 |
| Previously ungrouped vectors that became grouped | 37 | 32 |
| Previously grouped vectors that became ungrouped | 24 | 15 |

Thus adding the second collection did not simply add new segments: it also changed existing placements. These counts measure membership changes, not whether those changes were good.

The combined result contains 46 segments using only original-collection notes, 36 using only music-collection notes, and 42 using notes from both. A segment spanning both collections is not necessarily about both food and music: either collection can contain other subjects.

Complete member-by-member comparisons are preserved in [food-vs-combined/comparison.json](food-vs-combined/comparison.json) and [music-vs-combined/comparison.json](music-vs-combined/comparison.json). The latter also verifies unchanged music vector bytes and source-mask evidence despite different display IDs.

## Separate assistant assessment

Fresh independent review covered all 53 music segments and all 45 combined segments with memberships absent from either standalone run. The primary assistant also read every mask in those 98 segments and inspected original notes for disputed meanings. The 44 unchanged food segments retain their earlier review evidence; the 35 unchanged music segments use their music assessment.

Raw independent judgments are preserved separately:

- [Music100](assistant-assessment-music100.json): 46 valid, 5 invalid, 2 uncertain.
- [First 23 new combined segments](assistant-assessment-combined-new-a.json): 16 valid, 4 invalid, 3 uncertain.
- [Other 22 new combined segments](assistant-assessment-combined-new-b.json): 12 valid, 7 invalid, 3 uncertain.

These are assistant opinions, not user decisions or measured precision. Some objections depend on how broad a shared subject may be. In particular, I would leave the beauty/cuteness pair (`Sc4dfbf87cb`) and the expectations-of-people pair (`Sd392951671`) open for user judgment rather than treat the independent invalid verdicts as established failures. Photographing one's father and `#dadlife` (`Se76a1ad176`) have a plausible direct family connection despite the independent uncertain verdict.

Stronger concerns have concrete mismatches:

- `S7eda1523d1`: literal sunlight and watching the movie *Sunshine*. The movie mask omits the source words `the movie`; this is an upstream mask concern as well as a questionable grouping. This mismatch already existed in music100 (`S6a156609f5`).
- `Sdc132e09e5`: mental fog clearing and actual fog in outdoor photography. The original mental-fog masks omit the wording that establishes mental clarity.
- `Sd067c0c586`: an egg-related group includes a restaurant brunch recommendation whose complete source never mentions eggs.
- `S206f331bf1`: the original gianduja-product mask remains among GM greetings. Adding music notes did not repair that earlier rejected placement.

The first two do not isolate HDBSCAN as the cause: extraction and SSE's representation remain possible contributors. No masks were corrected after seeing these segments. The review tool presents all evidence without assistant verdicts so the user can assess the groupings independently.

## Preserved inputs and the one exception

The original food inputs include earlier manual corrections; music generation was left unchanged. This limits direct quality comparisons between the two collections. It does not invalidate standalone-versus-combined comparisons, which reuse the same vectors. Both collections were deliberately selected, not randomly sampled from Nostr.

All 100 music notes and all 1,080 generated subject/mask records remain preserved. Subject text and mask strings were not manually edited. Two non-verbatim masks were retried once each with the same frozen prompt/model; both attempts remain saved.

Identical byte ranges within a note were encoded once while preserving all originating subject associations. One valid mask, `N090-S008` / `Mexico.` / `🇲🇽`, cannot select a complete token because the tokenizer combines the adjacent `💜🇲🇽`. The user approved leaving only that mask unencoded. Its subject, mask and source note remain intact in [encoding-admission-v2/disposition.json](encoding-admission-v2/disposition.json) and the complete reviewed input. This leaves 1,057 encodings representing 1,079 subject associations.

The failed encoder attempt remains in `encoder-run/`. The successful attempt is in `encoder-run-v2/`: 66.48 seconds, peak 1,210,642,432 bytes of memory, no OOM, and maximum rolling two-second workload I/O pressure 0.0324%. No further model generation or new paid resources were used for encoding, clustering or comparison.

## Review

Start with music100. Then review the 45 new or changed combined segments. Exact duplicates are not shown twice. The three baseline groups lacking saved clicks are also omitted because the user's earlier chat explicitly assessed the displayed baseline as valid; that chat assessment is recorded separately, without filling missing clicks.

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
M=sse_multivector/real-note-fine-segmentation-v1/music-generation-v1
./target/debug/fine-segmentation-review \
  "$M/review-handoff/music/review.json" \
  "$M/review-handoff/music/user-session.json" \
  "$M/review-handoff/music/user-response.json"
```

For the combined collection:

```sh
./target/debug/fine-segmentation-review \
  "$M/review-handoff/combined/review.json" \
  "$M/review-handoff/combined/user-session.json" \
  "$M/review-handoff/combined/user-response.json"
```

Partial review is fine. Arrow keys change segments or scroll masks; Ctrl-C saves and exits. All masks are shown with brackets and spaces, without generated labels. [Handoff manifest](review-handoff/manifest.json) records every included or omitted segment and its review location. Complete raw results remain available in both run directories.
