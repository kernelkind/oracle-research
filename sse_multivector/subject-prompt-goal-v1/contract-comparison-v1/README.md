# ASv6.13 versus ASv6.19

Neither prompt passes the development test. ASv6.19 improved some outputs but introduced an unstated calculation and left several recurring problems unresolved.

| Same 28 notes, one output per prompt | ASv6.13 | ASv6.19 | Required |
| --- | ---: | ---: | ---: |
| Notes with no error or unresolved judgment | 20/28 | 22/28 | At least 26/28 |
| Accepted subjects | 256/274 (93.43%) | 187/198 (94.44%) | At least 95% |

“Clean” below means every generated subject was accepted and whole-note coverage was accepted. Broad, overlapping and duplicate subjects are allowed. Fewer subjects is not itself an improvement.

This is one paired run, not evidence that ASv6.19 is reliably better. Its repeated-note checks and unseen final validation have not been completed. ASv6.8 remains frozen.

## What was tested

The [proposal](../asv6.19/proposal.json) asked whether a simpler output-focused contract improves extraction overall. ASv6.19 moved the standalone-item requirement earlier and simplified source-gap, numerical and attribution instructions. ASv6.13 was the earlier broadly tested reference.

Both prompts received the same complete 28 development notes through the unchanged isolated Sol-low runner. Their order alternated across notes. All 56 calls succeeded, and every output was reviewed against its complete source.

The comparison tests that instruction group together. It cannot show which individual sentence caused a difference.

## Where the results differed

D-numbers identify notes in the frozen development input, not new categories.

| Note | ASv6.13 | ASv6.19 |
| --- | --- | --- |
| D04 — Satoshi preceded us | Expanded “everywhere we are going” into the group going everywhere. | Clean. |
| D08 — short Snow was still fly | Omitted short stature; literal flight remained unresolved. | Clean: short stature, style and emotional tone were represented. |
| D24 — insurance report | Clean. | “The Council” left the source of an interpretation unresolved. This was not an explicit wrong-source claim. |
| D26 — spaceflight crew | One item referred to “the announcement” without saying what was announced. | Clean. |
| D27 — investigating a cartoon ban | One comparison omitted both compared explanations and the cartoon's name. | Clean. |
| D28 — Tether and Hormuz Safe | Clean. | Added a newly calculated time interval. |

ASv6.19 gained four clean notes and lost two in this paired run. Both versions were clean on the same other 18 notes and unclean on the same four notes below.

## Problems shared by both versions

- D10, the Riley Walz report: ASv6.13 left four individual items without the hiring/event context. ASv6.19 preserved that context but generated the report's sector/confidence annotation as a subject.
- D12, the mixed-language Bitcoin post: complete coverage remains unverified because the reviewer has not established the full meaning of “HosKasi Laguma Karo.” ASv6.19's translation is also unresolved. These are not demonstrated extractor failures.
- D23, the fee report: both prompts produced priority/purging information without its Bitcoin-fee or mempool context inside the individual items.
- D25, the clipped CEO quotation: both prompts generated commentary about the unfinished source. ASv6.13 also left later items referring to “the quoted account” or “those fundamentals”; ASv6.19 supplied CEO context in those items.

## The new arithmetic error

The source says:

> Three weeks ago, Tether froze $344 million in USDT linked to Iran's Central Bank.
>
> Last week, Iran launched Hormuz Safe, a state-backed platform for maritime insurance settlements using Bitcoin and other cryptocurrencies.

ASv6.19 generated:

> Iran launched Hormuz Safe two weeks after Tether froze $344 million in USDT linked to Iran’s Central Bank.

The two-week interval was calculated from the two source expressions. The post did not state it. This is an extraction error under the already-fixed requirement against newly calculated facts, irrespective of whether that subtraction seems reasonable.

ASv6.13 kept “three weeks before the post,” “one week before the post,” and the stated event order. The complete original note and every generated subject remain in each run's output file.

## Review consistency

The [second review audit](../semantic-review-audit-v2.json) separately corrects five earlier decisions. It does not edit their original review files or generated text.

- The known short/style/emotional meanings in two older D08 outputs were covered, even though extra literal-flight subjects remained unresolved. Another older D08 output demonstrably omitted short stature.
- Two ASv6.17 subjects about possible investor/cloud-provider actions were reasonably supported by the Riley Walz post. They were too strictly rejected merely for expressing a possibility instead of repeating a question. The metadata comparison's adjusted ASv6.17 total is 185/227 accepted subjects, previously 183/227; its 8/27 clean outputs and overall conclusion are unchanged.
- The advertising note's service offer and immediate hiring invitation cover its commercial call to action. Separate visit/contact items are permissible but not a mandatory additional subject here. The same interpretation was used for both current prompts and the earlier metadata comparison.

A bounded language lookup found relevant component meanings in [Zorc's Somali-English dictionary](https://zorc.net/RDZorc/SOMALI/SOMALI-ENGLISH=DICTIONARY.pdf), but did not establish the compressed phrase's full meaning in D12. That uncertainty is retained rather than converted into a pass or failure.

## Next action

Repeat the two unchanged prompts twice on 12 notes: the eight fixed difficult notes plus every note whose clean result differed here. That is 48 fresh calls. The [confirmation proposal](../contract-confirmation-v1/proposal.json) records the exact selection and interpretation before generation.

This asks whether the observed gains and regressions repeat. It does not add another prompt version, discard the first results, or replace full-development and final-validation requirements. Neither prompt is eligible for final validation from this run.

## Evidence and execution

- [ASv6.13 full source notes and generated subjects](./asv6.13/output.json)
- [ASv6.19 full source notes and generated subjects](./asv6.19/output.json)
- [Subject-by-subject and whole-note reviews](./review.json)
- [Provenance verification](./verification.json) and [read-only verifier](./verify.py)
- [Sequential execution and host-pressure observations](./runtime.json)

Verification found 56 unique threads and working directories, one turn and no tool events per call, no reuse across 339 earlier calls checked, exact prompts and inputs, unedited raw outputs, and a review for every generated subject. This verifies execution and preservation, not the semantic truth of the judgments.

Across the 56 calls: 121,416 input tokens and 17,707 output tokens. The output total includes 9,677 reasoning tokens; the input total includes 17,280 cached tokens. No new paid API or rental was used.

Minimum observed available memory was 105.21 GiB; the maximum observed memory and I/O PSI averages were both zero. All generation units finished. No final-validation input, criterion, frozen prompt, model, mask, embedding or downstream artifact was changed.
