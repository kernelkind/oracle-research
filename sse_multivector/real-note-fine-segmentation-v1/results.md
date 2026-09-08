# 100-note fine-segmentation results

The user reviewed the masks-only baseline and reported that the groupings all looked valid. This supports the pipeline's ability to form recognizable groups across real notes in this collection. The three HDBSCAN settings produce different groupings and leave different vectors ungrouped; this review does not select an overall winner.

[Open the review instructions](review-handoff/README.md). [See the full notes and inline masks behind three observations](evidence.md).

## User review

On 2026-09-08, after using the masks-only baseline reviewer, the user said:

> done. these all look like valid groupings to me

The review displayed 43 segments, each containing masks from at least two distinct notes. It excluded the 209 one-note segments and did not show generated labels or assistant judgments. This is a positive assessment of the displayed baseline groupings, not a review of the alternative configurations or every possible omitted grouping.

The tool saved 37 confirmed Valid decisions, no Invalid or Uncertain decisions, one Valid selection without confirmation, and five Pending segments. The statement above is recorded separately; no missing clicks were filled in and no saved decisions were changed. The assistant's earlier doubts about individual baseline groups should not be reported as user-confirmed failures.

What this supports: reviewed source masks, SSE vectors, and baseline HDBSCAN can together produce coherent cross-note fine segments in this concentrated 100-note collection. It does not establish that all useful groups were found, that automatic extraction needs no correction, or that the result generalizes to the full corpus.

## What was held fixed

100 food/drink notes from 95 authors were selected before inspecting vectors. Their mixed and incidental subjects were retained too. This is a deliberately concentrated development collection, not an unbiased corpus sample or a strictly unseen holdout.

ASv6.23 and MPv3.5 ran with Astra low, in fresh isolated calls. Every generated subject and mask was reviewed before encoding. Raw outputs and corrections remain separate. Of 946 generated subjects, 945 were accepted and encoded; one unresolved interpretation, N028-S002, remains explicitly excluded. Eleven subject wordings and seventeen masks were corrected. All 100 original notes remain represented.

The unchanged Sentence-T5-base SSE checkpoint generated 945 vectors of 768 dimensions. Each encoding used the complete original note and one reviewed mask. Every HDBSCAN run used exactly these same normalized vectors. No segment labels were generated.

## What changed between runs

| Run | min_samples | min_cluster_size | Selection | Segments | Containing multiple notes | Vectors grouped | Vectors ungrouped |
|---|---:|---:|---|---:|---:|---:|---:|
| Baseline | 2 | 2 | EOM | 252 | 43 | 783 | 162 |
| Leaf | 2 | 2 | Leaf | 260 | 44 | 778 | 167 |
| Density | 3 | 2 | EOM | 119 | 29 | 619 | 326 |

EOM can retain a broader group when its measured persistence matches or exceeds that of its descendants. Leaf selects the smallest retained groups instead. The density comparison changes only the neighborhood used to measure local density. In this implementation, min_samples includes the point itself. All runs use angular distance between unit vectors; exact duplicate vectors are collapsed for clustering and their IDs restored afterward. The 945 vectors contain 916 distinct rows.

At least one vector from 97 notes is grouped in baseline and leaf, versus 88 notes in density. All vectors from all 100 notes remain preserved, including those left ungrouped.

All three saved requests were executed twice with the same pinned binary. The complete parsed responses matched. The configuration plans were recorded before their respective runs; this was not a parameter grid.

## What the comparisons show

1. **Useful relationships can exist even when HDBSCAN leaves a vector ungrouped.** Baseline V342, whose mask is `Fetching coffee`, has cosine 0.9541 with V277, whose mask is `More coffee`. Yet V342 is ungrouped. The density setting puts both into S34b70d4196. Being ungrouped does not mean that the vector has no relevant neighbors.

2. **Smaller groups are not automatically better.** Leaf makes one avocado-related grouping more specific, but also divides seven matching coffeechain masks and leaves two of them ungrouped. The earlier assessment called the avocado parent invalid; after reconsidering its broader shared meal meaning, the final baseline assessment is Uncertain. Narrower children do not settle that granularity question.

3. **The density change has real gains and real losses.** It reunites the coffee masks, including V243, V281 and V342, and reduces some repeated divisions. It also leaves 190 previously grouped vectors ungrouped while admitting 26 previously ungrouped vectors. Fourteen baseline groups containing multiple notes disappear entirely, including the coffee-shop music group S6f2f479441. Some lost baseline groups were questionable; others were judged coherent. The smaller segment count alone is not an improvement.

4. **Most groups still come from one note.** Baseline has 209 such groups and 43 containing multiple notes. Coherent masks from one note are legitimate, but they do not demonstrate recurrence across independent notes. Overlapping masks also give HDBSCAN several correlated points; vector counts are not counts of independent evidence.

These observations concern the complete pipeline with manually reviewed inputs. They do not isolate an SSE failure, establish automatic extraction accuracy, or qualify HDBSCAN generally.

## Assessment and stopping point

All 252 baseline segments and all 82 changed segments from the alternatives received separate assistant assessments using complete notes and exact masks. Identical membership and evidence were reused, not rejudged. The first baseline pass was too strict about different claims or food types; its original decisions are preserved alongside the explicit adjudications. The final baseline assessment records 221 Valid, 30 Uncertain and 1 Invalid. Those are subjective judgments, not an accuracy score.

All 162 baseline ungrouped mask strings were inspected. Fourteen were selected by their text for a closer neighbor inspection. The density comparison also inspects the 190 newly ungrouped masks and the lost groups. This is not an exhaustive judgment of every possible pair or every omitted segment.

Stop configuration exploration here: the comparisons expose a coverage/granularity tradeoff, and none establishes that another nearby setting would resolve it. The baseline is the starting review set because it retains more material, not because it has been selected as the final algorithm. Leaf and density remain explicit alternatives. No hybrid partition has been constructed from their favorable pieces.

## Records

- [Frozen input accounting](all-inputs-reviewed-checkpoint.json), [reviewed subjects and masks](reviewed-input.json), and [vector manifest](vectors/manifest.json).
- [Baseline assessment](assistant-baseline-final.json), [leaf changes](assistant-leaf-changes.json), [leaf assessment calibration](assistant-baseline-additional-adjudications.json), and [density assessment](assistant-density-final.json).
- [Ungrouped-vector inspection](unassigned-neighbor-inspection.json), [density membership changes](density-membership-comparison.json), and [review/run mapping](review-handoff/manifest.json).
- [Final interactive verification](handoff-smoke/interactive-check.md) and [integration regression evidence](integration-tests.md).

Generation used 1,045 calls: 100 subject calls and 945 mask calls. Total recorded usage was 2,604,727 input tokens, including 1,526,784 cached tokens, and 133,208 output tokens, including 86,327 reasoning tokens. No calls needed retrying. SSE took 67.70 seconds on four local CPU cores and peaked at about 1.23 GiB of memory. No resource guard interruption or OOM occurred. No new paid service or rented compute was used.
