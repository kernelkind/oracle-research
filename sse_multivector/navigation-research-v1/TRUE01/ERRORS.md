# TRUE01 — All unexpected answers

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

Each row asks **does A contain B?** All rows below were expected to receive **Yes**, but TRUE generated **No**. There were no unexpected Yes answers or unfinished outputs in either format. These are the frozen expectations, not labels changed after scoring.

The model received only the two category descriptions—not notes, masks, examples, or expected answers. Its score here is the probability of first output token `1`; the decision comes from its complete generated `0` or `1`, including termination. The score is neither cosine nor calibrated category confidence.

## Categories in sentences — all eight misses

The exact serialization is `premise: This text is about {B}. hypothesis: This text is about {A}.` The full A and B strings appear below. There are six missed broader–narrower inclusions and two missed equivalence directions.

| ID | A | B | Score | Analysis |
|---|---|---|---:|---|
| F02-w1-forward | Fermented foods | Yogurt made with live cultures | 0.391975 | Yogurt made using live cultures belongs among fermented foods. TRUE accepts the other wording, which explicitly says “fermented.” |
| F06-w1-forward | Vegetarian meals | Lentil stew made entirely from plant ingredients | 0.434810 | An entirely plant-based lentil stew fits vegetarian meals. This is a missed inclusion, not merely a weaker preference between parents. |
| F06-w2-forward | Meals without meat or fish | A lentil stew made entirely from plant ingredients | 0.458879 | An entirely plant-based lentil stew fits meals without meat or fish. The same category pair is accepted in the bare-text format. |
| S03-w2-forward | Software whose source code users may inspect, modify, and redistribute | Software distributed under the GPL | 0.144155 | GPL-distributed software supports the stated source-code permissions. The shorter “Open-source software” / full-GPL-name wording is accepted. This observation does not isolate acronym knowledge from wording length or the expanded definition. |
| E02-w1-forward | Monetary policy | A central bank raising interest rates | 0.445237 | A central bank’s interest-rate increase is a monetary-policy action. This pair is accepted with bare text; the expanded second wording is accepted with the sentence wrapper. Input wording matters. |
| P01-w1-forward | Freedom of expression | The right to criticize the government | 0.376392 | The right to criticize government is a specific freedom of expression. The second wording, about voicing opinions and speaking against government policies, is accepted. |
| S05-equivalent-2-1 | Preventing a program from using memory after it has been freed | Preventing access to freed memory | 0.412917 | The frozen review treated these as equivalent descriptions of preventing use after free. The expanded wording supplies the implicit program context. This expectation is more interpretation-dependent than the plant-only stew inclusion; it has not been relabeled after seeing the score. |
| E02-equivalent-2-1 | Government decisions about taxation and spending | Fiscal policy | 0.168097 | Taxation and spending decisions are the standard intended meaning of fiscal policy in this fixture. TRUE accepts the reverse direction in the sentence format, but not this direction. This is a missed definition match under the frozen category interpretation. |

## Bare category text — all thirteen misses

The exact serialization is `premise: {B} hypothesis: {A}`. This secondary format is reported independently. It did not receive different expected answers.

| ID | A | B | Score |
|---|---|---|---:|
| F02-w1-forward | Fermented foods | Yogurt made with live cultures | 0.268394 |
| F06-w1-forward | Vegetarian meals | Lentil stew made entirely from plant ingredients | 0.458776 |
| S03-w2-forward | Software whose source code users may inspect, modify, and redistribute | Software distributed under the GPL | 0.048672 |
| S05-w1-forward | Memory safety | Preventing access to freed memory | 0.467457 |
| S05-w2-forward | Safe use of computer memory | Preventing a program from using memory after it has been freed | 0.203902 |
| E02-w2-forward | Central-bank management of money and borrowing conditions | An increase in policy interest rates by the central bank | 0.469192 |
| E06-w1-forward | Market competition | Businesses competing by lowering prices | 0.446741 |
| E06-w2-forward | Rivalry between sellers | Sellers undercutting each other's prices | 0.498149 |
| P01-w1-forward | Freedom of expression | The right to criticize the government | 0.445877 |
| P03-w1-forward | Decentralization of government | Giving local councils more decision-making power instead of the national government | 0.129578 |
| R02-w2-forward | Respect for other people's personal limits | Letting a friend keep a sensitive topic private | 0.388025 |
| E02-equivalent-1-2 | Fiscal policy | Government decisions about taxation and spending | 0.296772 |
| E02-equivalent-2-1 | Government decisions about taxation and spending | Fiscal policy | 0.103767 |

The bare-text-only misses also concern genuine inclusions under the frozen reading: preventing use after free concerns memory safety; central-bank policy-rate increases concern monetary management; undercutting prices concerns competition; giving local councils national authority concerns decentralization; permitting privacy respects personal boundaries. Their presence does not prove those concepts are absent from the model: adding the fixed sentence wrapper changes several decisions.

Across both formats, the wrapper changes eleven answers: eight become expected Yes answers and three become unexpected No answers. It is helpful overall on these descriptions, but not uniformly helpful.

## What the missed answers do—and do not—show

In the sentence format, every positive still scores above every negative: the lowest positive is **0.144155**, and the highest negative is **0.140235**. Therefore these eight native No answers do not demonstrate that the continuous score cannot support our decision. The gap is just **0.003920**, and choosing a cutoff from these same examples would not validate it on other categories. No cutoff was selected or applied.

The bare format has overlapping positive and negative scores; its lowest positive is **0.048672**, below its highest negative at **0.138809**. No single cutoff perfectly separates that observed set.

Every answer, including successes (`03bd9e45:sse_multivector/navigation-research-v1/TRUE01/DECISIONS.md`) · [Summary and interpretation](RESULTS.md) · Exact model inputs and raw recorded answers (`scores.jsonl`).

**Selected data:** Compact pair-score results, inputs and parameters for `TRUE01` are selected for release as `numerical/pair-scores-44261922841cf8b2` in the [publication catalog](../../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.
