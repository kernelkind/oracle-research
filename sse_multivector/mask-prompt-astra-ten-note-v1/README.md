# Astra masks for every subject in ten additional notes

All 60 mask calls returned. My initial review found **55 masks with no issue**, **one mask-scope question**, and **four supplied subjects that need separate judgment**. I found no clear mask-selection failure. The user has now approved all five masks in the review sample, resolving the mask-scope question. This is not approval of all 60 masks or evidence of perfect accuracy.

[Every supplied subject, full original note and inline mask](./masks.md)

## Review outcome and remaining questions

The resolved mask-scope question was **N06-S06**.

Subject: “The story is categorized as relating to the United States.”

Returned mask: `["#UnitedStates"]`

My question was whether the country tag also needed text identifying the story. ASv6.8 itself only says “the story”; I had not declared a missing-reference failure. The user corrected an accidental rejection to approval. The other four reviewed masks (N01-S03, N05-S05, N06-S01 and N07-S03) were already approved. Only N06-S06's decision was changed, using the existing review tool; all other decisions and comments stayed unchanged.

The tag occurs twice; the TUI displays its first occurrence, while the complete report shows both. Approval resolves mask scope, not whether either occurrence would produce the same SSE vector.

The four separate subject questions are:

| Subject | Concern introduced before masking |
| --- | --- |
| N05-S13 | The tag `technologyservicesllc` becomes a claim about technology services provided through a limited liability company. It could instead be an organization name. |
| N06-S05 | The subject adds “although the connection to sports is unclear.” The post uses sports tags but does not make that comment. |
| N07-S05 | The subject proposes Katie's smile or teeth as the thing needing repair. The fragmented post mentions a smile, but not teeth; the connection remains uncertain. |
| N09-S03 | The subject adds “the post does not state that the fight caused the fear.” That describes absent information rather than another message in the headline. |

The first and third are uncertain interpretations, not established subject failures. The second and fourth are extractor commentary. These were flagged before mask inference and remain separate from mask quality. No subject or mask has been rewritten.

My initial concern about **N07-S02** was not upheld as a failure: a greeting to Katie followed by praise for information makes Katie-as-source a reasonable interpretation. The original pre-mask note remains preserved.

## Small review sample

Five screens: the mask-scope question plus four masks I judged to have no issue. The four were chosen by sorting their precomputed prompt hashes and taking distinct notes, not by choosing particular mask outputs. These are a check on my judgments, not a requirement to review all 60.

The two screens from the same note are adjacent.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./target/release/sse-mask-review review-masks \
  sse_multivector/mask-prompt-astra-ten-note-v1/review-sample.json \
  target/mask-prompt-astra-ten-note-v1-review-session.json
```

This uses the existing binary, without a Cargo build. The review began with no decisions prefilled; the saved session now contains five approvals. The subject-generation questions above are not inserted into this mask-only review.

## What ran

The input was the frozen 500-note corpus file:

`target/crec-119-500-note-v2/input/notes.json`

Its SHA-256 is `af1f82719003ed73aea0f569c0a936733a95f6c366d4d95e1436c7cebae9b5d1`.

After excluding notes in saved subject/claim-development inputs and previous mask-comparison selections, 417 rows remained. We took the next ten in the existing order. No topic, length, difficulty or quality filter was applied. These are additional notes for this prompt work, not a claim that no earlier Oracle experiment ever used them.

Frozen **ASv6.8**, using **Sol low**, ran once per note and produced 60 subjects. Every subject then received exactly one fresh **Astra-low** mask call with the unchanged original mask prompt. We did not choose only two subjects per note, edit subjects, or discard overlapping/broad subjects.

The existing subject runner removes long encoded Nostr identifiers before subject generation. Mask calls received the complete original notes. All other prompt and input behavior stayed unchanged.

| Note | Frozen input position | Subjects / mask calls |
| --- | ---: | ---: |
| N01 | 2 | 3 |
| N02 | 4 | 3 |
| N03 | 5 | 6 |
| N04 | 7 | 5 |
| N05 | 8 | 13 |
| N06 | 9 | 6 |
| N07 | 10 | 13 |
| N08 | 11 | 2 |
| N09 | 13 | 4 |
| N10 | 14 | 5 |

## Checks and limits

- All 60 masks are arrays of exact source fragments in source order.
- Three outputs permit more than one source placement: N04-S01, N04-S02 and N06-S06. All alternatives are preserved. No SSE encoding or occurrence approval happened.
- All 70 calls, including subject generation, used distinct fresh threads and working directories, with no overlap against 711 earlier records checked.
- The same pinned CLI 0.153.0 and unchanged runner were used. Tools, web search, inherited rules and user configuration were disabled. Recorded prompts contained no earlier answers, review notes or expected masks.
- No retries, repairs, reruns, automatic checker or model-default changes.
- Calls were sequential under a 2 GiB local cap, zero swap allowance and 900-second per-batch timeout. Reported service peaks ranged from 16.3 to 17.3 MiB; all four batches used zero swap.
- Existing subscription only: no paid API or rented compute was added.

These checks cover recorded local inputs, processes and returned events. They cannot inspect undisclosed service-level instructions. Prefix caching is not conversation-history reuse.

| Stage | Calls | Reported input tokens | Reported output tokens |
| --- | ---: | ---: | ---: |
| ASv6.8 / Sol low | 10 | 20,999 | 3,350 |
| Masks / Astra low | 60 | 149,959 | 3,188 |

Cached input is included in input totals; reasoning tokens are included in output totals. Per-call usage and times are in [verification.json](./verification.json).

## What follows from this

The result supports Astra low with the current mask prompt as a working generator for reviewed experimental data. It does not establish a corpus-wide error rate, settle the four subject questions, or override failures in earlier experiments. One call per subject also does not measure repeatability on these new inputs.

The distinction between actual corpus inputs, task-specific judgments and human review follows [OpenAI's evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices). That guidance informed the test design; the semantic judgments above come from inspecting our data.

## Saved evidence

- [selection.json](./selection.json): selected notes, source positions and exclusion provenance.
- [plan.json](./plan.json): scope and controls fixed before inference.
- [fixed-subjects.json](./fixed-subjects.json): all 60 unedited subjects, fixed before masks.
- [review-basis-before-masks.json](./review-basis-before-masks.json): review criteria and initial subject concerns, never sent to the models.
- [assistant-review.json](./assistant-review.json): initial assistant mask/subject judgments for every item, preserved unchanged; the user review outcome is recorded above.
- [mechanical-checks.json](./mechanical-checks.json): fragments and all source-order-valid placements.
- [review-preparation.json](./review-preparation.json): sample selection and explicit source-occurrence display convention.
- [verification.json](./verification.json): hashes, isolation and execution checks.
- `subjects-1/`, `subjects-2/`, `masks-1/` and `masks-2/`: exact configurations, manifests, outputs and raw call records.

No user notes document, existing prompt, production code, SSE artifact or segmentation result was changed. The only decision correction was the explicitly authorized N06-S06 rejection-to-approval change. CREC-125 remains In Review with four subject-generation questions open; neither the model nor mask prompt was frozen.
