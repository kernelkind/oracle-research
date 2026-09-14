# TRUE02 — The fixed cutoff transferred well, but not perfectly

**The unchanged 0.142 cutoff answered 147/150 directional questions correctly.** It accepted all 45 valid relationships and rejected 102 of 105 invalid ones. All three mistakes put a bread variety under **Bread baking**, even though the variety's full subject also includes eating, taste, nutrition, storage, and other topics beyond baking.

These are new manually constructed descriptions, not actual generated HDBSCAN labels. The complete input set and judgments were reviewed before scoring. No scores, labels, wording, weights, or cutoff were adjusted after seeing results.

## What was tested

Thirty descriptions: six in each of food, software, economics, politics, and interpersonal relationships. Every distinct within-domain pair was checked in both directions: 75 pairs, 150 decisions. There were no easy between-domain negatives. None of these ordered category pairs occurred in TRUE01.

For **A contains B?**, TRUE received exactly:

```text
premise: This text is about {B}. hypothesis: This text is about {A}.
```

The score is the probability of first output token `1`, not cosine or a calibrated category-containment probability. The native answer is TRUE's complete generated `0` or `1`. The separately frozen rule accepts when the score is **greater than 0.142**.

| Decision rule | Valid relationships accepted | Invalid relationships rejected | Correct directions | Pairs with both directions correct |
|---|---:|---:|---:|---:|
| Native answer | 34/45 | 103/105 | 137/150 | 62/75 |
| Fixed cutoff, unchanged from the proposal after TRUE01 | 45/45 | 102/105 | 147/150 | 72/75 |

The cutoff recovered eleven missed valid relationships while adding one false relationship. It did not simply answer Yes to related categories: it rejected all 35 reversed strict-inclusion directions and 67/70 directions where neither category contains the other. All ten directions of the five equivalences were accepted.

| Area | Native correct | Cutoff correct |
|---|---:|---:|
| Food | 28/30 | 27/30 |
| Software | 25/30 | 30/30 |
| Economics | 27/30 | 30/30 |
| Politics | 28/30 | 30/30 |
| Interpersonal relationships | 29/30 | 30/30 |

## Every cutoff mistake

The question is whether **A contains B**, not whether the descriptions are related.

| ID | A | B | Expected | Native | Score | Cutoff |
|---|---|---|---|---|---:|---|
| F6-contains-F2 | Bread baking | Sourdough bread | No | Yes | 0.538085 | Yes |
| F6-contains-F4 | Bread baking | Gluten-free bread | No | No | 0.178456 | Yes |
| F6-contains-F5 | Bread baking | Bread made without gluten | No | Yes | 0.509176 | Yes |

For the first error, the complete model input was:

```text
premise: This text is about Sourdough bread. hypothesis: This text is about Bread baking.
```

Sourdough bread belongs under **Bread**; its entire category does not belong under **Bread baking**. A note about storing or eating sourdough need not concern baking. The same distinction applies to gluten-free bread. Those counterexamples were recorded in the blind review before inference.

F4 and F5 are equivalent descriptions, so the three errors represent two bread varieties and one recurring error pattern, not three independent failure mechanisms. Their scores also differ substantially (0.178456 versus 0.509176), changing the native answer despite the equivalent meaning. This is observed wording sensitivity; no alternative wording was selected afterward to improve the result.

The output is consistent with confusing a product's topic with its production process. This experiment does not isolate whether that comes from TRUE's learned associations, our topic wrapper, or another mechanism.

## Why a different universal cutoff cannot make this set perfect

Consider these two actual decisions:

| A contains B? | Expected | Score |
|---|---|---:|
| Software testing contains Security testing of web applications | Yes | 0.157464 |
| Bread baking contains Sourdough bread | No | 0.538085 |

A cutoff low enough to accept the valid software relationship also accepts the invalid bread relationship. A cutoff high enough to reject that bread relationship rejects the valid software relationship. This establishes a limitation of a single cutoff on these observations, **not** that the model is useless: the frozen cutoff still made only three errors.

Within each area's six categories, every valid relationship scored above every invalid relationship:

| Area | Lowest valid score | Highest invalid score |
|---|---:|---:|
| Food | 0.740384 | 0.538085 |
| Software | 0.157464 | 0.037221 |
| Economics | 0.193878 | 0.013346 |
| Politics | 0.292186 | 0.087392 |
| Interpersonal relationships | 0.466535 | 0.036581 |

Across all areas, 28 of the 4,725 valid-versus-invalid score comparisons have the invalid relationship higher. All 28 cross areas and involve one of the three bread errors; there are no ties. [Every such comparison](score-inversions.json).

This matches the predeclared outcome in which ordering is clean within the sampled areas but not globally. It does **not** demonstrate stable domain-specific cutoffs: there is only one six-category collection per area, and error type, wording, and domain are confounded. No per-domain cutoffs were fitted.

## Examples where overlap was handled correctly

| Question | Expected | Score | Cutoff |
|---|---|---:|---|
| Bread contains Gluten-free food | No | 0.008023 | No |
| Gluten-free food contains Bread | No | 0.001926 | No |
| Testing web applications contains Software security testing | No | 0.016933 | No |
| Software security testing contains Testing web applications | No | 0.004838 | No |
| Friendship contains Workplace relationships | No | 0.001379 | No |
| Workplace relationships contains Friendship | No | 0.000820 | No |

These categories can share instances without containing each other. Their low scores provide direct evidence that the model is not merely reporting semantic similarity in this sample.

## Conclusion

TRUE plus our unchanged topic wording remains a promising candidate for description-based subsumption. The cutoff's success on genuinely new pairs is stronger evidence than its perfect fit to TRUE01, and the reverse/overlap results directly address the required distinction.

It is not a solved membership oracle. The universal score boundary is imperfect, equivalent wording can change scores, and this test does not establish performance on generated node descriptions or all topics. Nor does it validate complete hierarchy construction, equivalence consolidation, missing-parent generation, or navigation.

The 150 directions reuse just 30 descriptions in five tightly constructed collections, including explicit intersections and simple paraphrases. The 98% figure is descriptive of this test, not an estimated deployment accuracy. All expectations remain unchanged; disputes can be revisited openly without rewriting the saved answer key.

## Current research status — 2026-09-14

After the pause for node-description work, the user approved resuming TRUE tests on actual generated titles. The [TRUE03 pilot](../TRUE03/RESULTS.md) and completed [TRUE04 full-title test](../TRUE04/RESULTS.md) use unchanged v20/Astra-low titles and TRUE02's model, input wording and 0.142 cutoff. TRUE04 scored all 3,660 directions across 61 original groups. Semantic review judged 91 of 106 cutoff-accepted directions reasonable, 9 incorrect and 6 ambiguous; it also recorded missed relationships and false reciprocal containments. These results do not adopt TRUE as the final hierarchy system. The TRUE02 measurements and original judgments above remain unchanged.

## Complete evidence

- [Every decision, exact descriptions, scores, and native errors](DECISIONS.md).
- [All errors with explanations](ERRORS.md).
- [Raw inputs](inputs.json), [raw outputs and token IDs](scores.jsonl), [raw analysis](analysis.json).
- [Frozen plan](../TRUE02-PLAN.md), [pre-score independent review](../TRUE02-BLIND-REVIEW.md).
- [Execution and reproducibility](EXECUTION.md), [independent verification](verification.json).

TRUE01 and this run's frozen source snapshots remain unchanged. No hierarchy or cutoff adjustment was made in TRUE02. TRUE03 and TRUE04 have separate artifacts. The current runner shares the same inference implementation through a tested extraction; TRUE04 adds reporting for unlabeled rows without changing inference or inventing expected answers.
