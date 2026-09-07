# ASv6.23 final validation

ASv6.23 passes the unchanged development and final-test requirements. Freeze the exact prompt, Astra-low setting, output schema and input normalization that produced these results. This freezes an experiment package; production defaults, masks and downstream processing are unchanged.

## Result

| Check | Required | Observed |
| --- | ---: | ---: |
| Fully accepted first outputs | At least 54 / 60 | 57 / 60 |
| Accepted subjects across all calls | At least 95% | 809 / 819 (98.78%) |
| Fully accepted outputs including repeats | At least 76 / 84 | 80 / 84 |
| Same specific issue in 2 / 3 repeats or 3 distinct final notes | None | None |
| Clear negation/comparison reversal or wrong-speaker allegation | None | None found |

“Fully accepted” means no recorded error, unresolved judgment or missing distinct meaning in that output. The ten unresolved subjects count against acceptance. No definite item error or missing distinct meaning remains in the final main review. First outputs alone had 572 / 581 accepted subjects.

The test used 60 notes from the 500-note source: 20 short, 20 medium and 20 long. Twelve notes were each generated twice more. All 84 calls used fresh isolated contexts. The only reserved note previously exposed during development was replaced by the next eligible note under the original rule; the other 59 notes were unchanged. [Selection and repair](./selection.json).

## What remains uncertain

These are review questions, not established extractor failures:

| Note/output | Subjects | Question |
| --- | --- | --- |
| H20-t1 |2,4 |Does “giving the gold to Spain, just like the old days” support a gold-medal reading as well as gold transfers? |
| H32-t1 |3–7 |Does an incoherent sequence containing “tippers” and “halter” communicate the multiple dictionary meanings returned? |
| H52-t1 |17,19 |Does stating Moscow's actions directly lose the author's “suggests” qualification? |
| H34-t3 |13 |Is “Toronto within the discussion…” a geographic subject or commentary about a tag? |

All sources, exact subjects and the reasoning for these judgments are in [remaining questions](./remaining-questions.md). Independent reviewers accepted some readings that the main reviewer still found uncertain; those disagreements are preserved, not averaged away. One independent reviewer also requested a subject naming “Bitcoin Benji”; the final review treats that line as a node identifier/credit, not a required separate subject, while retaining the full-node service relationship.

## What this establishes

The tested package meets our pilot stopping rule. It is strong enough to stop subject-prompt revisions for now.

It does not establish universal accuracy, an exact canonical subject list, or that the auxiliary context field causes the model to reason in a particular order. Output counts vary because overlapping, broad and narrow subjects are intentionally allowed. The final test is one attempt on one corpus sample; its languages and note types are limited. [Observed source coverage](./source-coverage-audit.json).

The preceding development check also passed: 27 / 28 first lists accepted, followed by no recurring failure across the eight fixed difficult notes. [Development results](../repeat/results.md). Development's snow reading and three insurance references remain unresolved in the record; final success does not retroactively change those judgments.

## Execution and records

All 84 calls succeeded on their first attempt with Astra low. All 819 final subjects were reviewed against complete original notes, with context fields hidden during semantic review. Every subject has a recorded decision; raw outputs were not changed. Main review was not entirely blinded to independent judgments, as the saved timing notes explain.

All 84 thread IDs and working directories were unique and separate from the prior 600 calls. No model tools were used, and no experiment units remain active. Sampled available memory stayed above 104.85 GiB; sampled memory/IO pressure stayed zero. 36 calls logged the known nonfatal shell-snapshot startup diagnostic. [Technical verification](./technical-verification.json).

Reported final-call usage: 222,147 input tokens (111,360 cached) and 35,449 output tokens (9,263 reasoning tokens). These are reported categories, not extra sums to add together. The goal total is 684 generation calls.

[Complete first outputs](./full-first-outputs.md) · [Complete repeated outputs](./full-repeat-outputs.md) · [Decisions and disagreements](./review.json) · [Mechanical gate verification](./verification.json) · [Frozen package](../../asv6.23/frozen.json)
