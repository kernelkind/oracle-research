# ASv6.8 versus ASv6.10: 20-note holdout

ASv6.10 improved the targeted calculation and commentary examples. It is not established as a complete fix: a definition-like item, unclear slang and repeated chart-link subjects still need judgment. ASv6.8 remains the frozen default.

[Complete notes, all 305 subjects, and per-note analysis](./results.md)

## What happened

The next 20 unused development notes were selected from the frozen 500-note order before generation. Both unchanged prompts ran once on every note: **40 fresh isolated Sol-low calls**, sequentially. All completed on their first attempt. No output edits, masks, SSE, repair calls or default changes.

“Unused” means absent from the saved subject/claim-development inputs and mask-comparison selections listed in [selection.json](./selection.json). It does not mean that no earlier corpus-wide pipeline ever encoded the notes. The audit covered 38 input/selection files; 93 of the 500 corpus notes were excluded, leaving 407 eligible. Selection was mechanical, not based on content.

## What the comparison shows

| Note | ASv6.8 | ASv6.10 |
| --- | --- | --- |
| N12 — additional satoshis | Adds “equivalent to 0.005 bitcoin.” | Keeps 500,000 satoshis; no conversion. |
| N01 — GPU compatibility | Adds that the post does not specify AMD Anti-Lag’s relationship to the other tools. | Names AMD Anti-Lag without that explanation. |
| N02 — previous action | Adds that the action’s exact meaning is uncertain. | “The previous action was up.” |
| N05 — Bitcoin poem | Discusses uncertainty about what “appears” means. | Gives direct literal and metaphorical subjects. |
| N17 — Venezuela | Discusses whether the post describes a plan or urges one. | Gives possible intent and an exhortation directly. |
| N19 — dashboard | Appends an explanation that interpreting “pipes” is uncertain. | Qualifies the actual maintenance subject with “appears.” |
| N18 — exchange listing | Describes the active instruments. | Also adds 12 subjects describing individual chart-link destinations. |

N12 also loses ASv6.8’s proposed interpretation of “Hos Kasi Laguma Karo.” I cannot validate that phrase, so this is **unresolved coverage**, not a demonstrated success or failure. The six notes N01/N02/N05/N12/N17/N19 show the intended wording change, but that is not a measured accuracy rate.

The straightforward text examples retain their main communicated meanings. That does not establish complete coverage across all 20 notes: the slang and non-English phrase remain unresolved. More outputs are not inherently worse: ASv6.8 returned 140 subjects and ASv6.10 returned 165; duplicates and broad/nested subjects are allowed.

## Review focus

1. **N03, ASv6.10 subject 2:** is defining “execution” a subject of the post, or commentary about interpreting it?
2. **N08, both versions:** which Snow/snow interpretations does the short text support? The image was not examined.
3. **N18, ASv6.10 subject 3:** is the chart-page item a represented subject or link bookkeeping? One decision can inform inspection of the repeated pattern; it is not automatically copied to all items.
4. **N12:** the conversion difference is concrete; the non-English phrase needs someone able to judge it.

The [review focus](./review-focus.json) preserves the complete source notes and exact subject strings. All user decisions remain empty. [Assistant analysis](./assistant-analysis.json) also records the less clear provenance questions in N07, N14 and N20 rather than treating every URL-related subject as invalid.

### Existing review tool: wording approval pending

The actual generation runs load in the existing subject-review tool. Its current screen/help still asks for one narrow subject, rejects broad/incidental subjects, and has a distinctness check. Those rules conflict with this experiment’s accepted broad/overlapping-subject policy. No UI code has been changed; permission was requested to update only the review wording. Do not use its old narrowness/distinctness instructions to judge this experiment.

The tool reviews complete generated runs, not a filtered list of isolated subjects. Both original runs remain intact; no fabricated or rebound generation records were made to filter them. A smoke check opened ASv6.8, navigated to the next note and paused with **zero decisions**. The temporary session is under `target/atomic-subject-asv6.8-vs-asv6.10-holdout-v1/`.

Once review wording is resolved, the existing inputs are `asv6.8/run` and `asv6.10/run`; the four review-focus notes above identify where human judgment is useful. The user need not finish every note.

## Verification and limits

[Verification](./verification.json) checked 40 distinct threads and working directories, no reuse of the 54 prior comparison calls, one turn per call, no tool activity, exact rendered prompts, raw-output hashes, unchanged exported subject strings and all 93 prior protected files. The seven new frozen input/config/plan files also stayed unchanged. A subsequent documentation-only follow-up link in the prior test README is recorded separately; it does not alter any prior result.

[Runtime](./runtime.json): 4m23.457s for ASv6.8 and 4m28.746s for ASv6.10. Host memory and I/O pressure stayed quiet at sampled checks; available memory remained above 109 GiB. Launcher memory reports of 17M and 16.8M exclude the separate Codex scopes. Existing subscription only; no paid API/rental or credential changes.

| Version | Input tokens | Cached input | Output tokens | Included reasoning tokens |
| --- | ---: | ---: | ---: | ---: |
| ASv6.8 | 41,968 | 1,792 | 7,108 | 4,532 |
| ASv6.10 | 45,136 | 7,680 | 7,149 | 4,564 |

This is one paired generation per note, in two sequential blocks, from an existing frozen corpus—not a repeatability estimate, a random sample of all Nostr, or evidence that every prompt change caused its observed difference. No new default has been approved.
