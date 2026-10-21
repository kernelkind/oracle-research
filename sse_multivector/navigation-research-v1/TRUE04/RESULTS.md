# TRUE04 — Containment across all 61 generated group titles

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

TRUE recovered many useful parent–child relationships. It also accepted some wrong relationships in both directions, which would create false category equivalences if used directly to build the graph.

All **3,660 ordered questions** ran, without cosine filtering. The original 61 groups have **58 distinct title strings**; repeated Food, Coffee and Bitcoin groups remain separate. The exact v20/Astra-low titles, model, input wording and cutoff were unchanged. No hierarchy was constructed.

## What was tested

For the question **Does A contain B?**, TRUE received:

```text
premise: This text is about {B}. hypothesis: This text is about {A}.
```

It saw only those titles, not masks, notes, IDs or expected answers. The score is the full-vocabulary probability of first generating token `1`, **not cosine or a calibrated probability of containment**. The native answer is the model's complete generated Yes/No label. The separate frozen rule accepts **score > 0.142**.

Before inspecting scores, reviewers nominated 120 clear relationships and 42 ambiguous ones. Unlisted pairs were left unlabeled, not presumed No. After scoring, every accepted title pair was reviewed; a fresh reviewer also reconsidered the missed nominations without seeing scores. These semantic judgments are revisable, not a uniquely correct hierarchy. The [reference record](../TRUE04-REFERENCE-REVIEW.md) explains the process and scope choices.

## Accepted relationships

| Decision rule | Accepted directions | Reasonable | Incorrect | Ambiguous |
|---|---:|---:|---:|---:|
| Fixed score > 0.142 | 106 | 91 | 9 | 6 |
| Native generated Yes | 86 | 79 | 4 | 3 |

Because titles repeat, these are not independent semantic examples. Collapsing only identical ordered title strings for reporting gives **64 cutoff-accepted questions: 53 reasonable, 6 incorrect, 5 ambiguous**. The native answer accepts 49 distinct questions: 45 reasonable, 2 incorrect, 2 ambiguous.

The lower cutoff adds 20 directions over native Yes: **12 reasonable, 5 incorrect and 3 ambiguous**. That is a tradeoff, not a clean improvement or a reason to change the rule after this run.

Some useful accepted questions:

| A: proposed parent | B: proposed child | Native | Score |
|---|---|---|---:|
| Food | Food Ingredients | Yes | 0.895404 |
| Food Ingredients | Sea Salt as a Food Ingredient | Yes | 0.819593 |
| Coffee | Coffee Bean Preparation | Yes | 0.836168 |
| Coffee | Appreciating Coffee for Its Flavor | Yes | 0.967635 |
| Coffee | Coffee Chains | No | 0.435481 |
| Poultry-Based Food Preparation | Making Chicken Stock | Yes | 0.903487 |
| Bitcoin | Satoshi Bitcoin Units | Yes | 0.624657 |
| Nostr | Grow Nostr Campaign | Yes | 0.603691 |

All 64 accepted title questions, not just these examples, appear in [the complete review](REVIEW.md). Scores in this report are rounded to six decimals; exact values are preserved in `scores.jsonl`.

## The six distinct incorrect accepted questions

**1. Does Food contain Nostr?** Native **Yes**; score **0.546812**; cutoff **Yes**.

```text
premise: This text is about Nostr. hypothesis: This text is about Food.
```

Nostr is a communication-network topic, not a food subcategory. There is no food restriction in the title. This occurs twice because two original groups have the title Food.

**2. Does Nostr contain Food?** Native **Yes**; score **0.644765**; cutoff **Yes**.

```text
premise: This text is about Food. hypothesis: This text is about Nostr.
```

Food discussions can appear on Nostr, but that does not make Food a subcategory of Nostr. This also occurs twice. Together with question 1, it would incorrectly make Food and Nostr equivalent **even using native answers alone**. The two duplicate-input scores differ slightly in their last decimal places; both full values are saved.

**3. Does Nostr contain Consuming Excessive Amounts of Food or Drink?** Native **No**; score **0.160344**; cutoff **Yes**.

```text
premise: This text is about Consuming Excessive Amounts of Food or Drink. hypothesis: This text is about Nostr.
```

The eating-and-drinking category has no Nostr-specific meaning. The fixed cutoff introduces this acceptance; the native answer rejects it.

**4. Does Daytime Greetings contain How the Day Is Going?** Native **No**; score **0.336519**; cutoff **Yes**.

```text
premise: This text is about How the Day Is Going. hypothesis: This text is about Daytime Greetings.
```

A report about someone's day need not be a greeting. The subjects are related, but the broader day-status title does not fit wholly inside greetings. The independent reviewer agreed with this distinction.

**5. Does Coffee Consumption contain Coffee?** Native **No**; score **0.186424**; cutoff **Yes**.

```text
premise: This text is about Coffee. hypothesis: This text is about Coffee Consumption.
```

Coffee includes cultivation, preparation and trade, not just consumption. The correct direction, Coffee contains Coffee Consumption, scores **0.966989** and is accepted. The wrong reverse occurs twice because Coffee has two source groups. This reproduces the earlier TRUE03 error rather than supplying an independent new failure.

**6. Does Advice on Meat Consumption contain Meat Eating?** Native **No**; score **0.237189**; cutoff **Yes**.

```text
premise: This text is about Meat Eating. hypothesis: This text is about Advice on Meat Consumption.
```

Meat Eating also covers habits, experiences and descriptions that are not advice. The correct direction, Meat Eating contains Advice on Meat Consumption, scores **0.934846** and is accepted. Again the cutoff accepts both directions where only one is appropriate.

These are **six distinct questions and nine original directions**, not nine independent failure mechanisms. The run does not isolate whether individual errors come from title interpretation, the topic-sentence wording, learned knowledge or other model behavior.

## Relationships the model missed

| Pre-score nominations | Directions | Recovered by cutoff | Recovered by native Yes |
|---|---:|---:|---:|
| All clear nominations | 120 | 90 | 79 |
| Food as parent | 74 | 62 | 56 |
| Other parents | 46 | 28 | 23 |

At the distinct-title level, the cutoff recovers **52 of 75** nominated questions; native Yes recovers **45 of 75**. These are recovery counts for an explicitly nominated reference, **not total recall or overall accuracy**.

The 30 missed directions represent 23 distinct questions. Fresh review upheld 20 of those nominations and left three unresolved. Examples upheld by both reviews:

| A: proposed parent | B: proposed child | Native | Score |
|---|---|---|---:|
| Human Diet and Eating Behavior | Meat Eating | No | 0.116333 |
| Poultry and eggs | Making Chicken Stock | No | 0.131106 |
| Poultry and eggs | Poultry-Based Food Preparation | No | 0.039920 |
| Communication | Weekend Well-Wishes | No | 0.074170 |
| Food | Coffee | No | 0.010624 |

Food was interpreted broadly to include beverages; that scope is an explicit human choice. The three unresolved nominations are Communication contains Advice on Meat Consumption, Nostr contains Plebchain, and Communication contains Plebchain. The first depends on the scope of Communication; the fresh reviewer could not confirm the meaning of Plebchain. They remain visible disputes, not three proven errors. [The complete review](REVIEW.md) shows all 23 missed questions and their reasons.

## Implications for the hierarchy

**There is real containment signal.** Useful chains such as Food → Food Ingredients → Sea Salt as a Food Ingredient and Coffee → Coffee Consumption → Appreciating Coffee for Its Flavor are present. This is stronger evidence than the selected TRUE03 pilot alone, though the corpus remains food-heavy.

**Reciprocal Yes is not reliable evidence of equivalence.** Native answers falsely equate Food and Nostr. The cutoff additionally falsely equates Coffee with Coffee Consumption and Meat Eating with Advice on Meat Consumption. No equivalence consolidation was performed.

**Pair decisions can be inconsistent as a collection.** For example, Food contains Nostr and Nostr contains Grow Nostr Campaign are accepted, but Food contains Grow Nostr Campaign is rejected at **0.064004**. Taking transitive closure would propagate the first wrong link. The saved diagnostics contain 58 such original-ID triples for native answers and 70 for the cutoff. These reuse links and duplicate titles; they are consequences of existing errors or omissions, not that many independent failures.

**A different cutoff cannot perfectly order this observed set.** Wrong native-positive Food/Nostr scores exceed many reasonable rejected relationships. This does not establish that TRUE is unusable or that occasional errors are unacceptable. It establishes a concrete tradeoff that a hierarchy using these decisions would inherit; perfect separation was not a requirement of this experiment.

The result supports TRUE as a source of many useful proposed relationships, but not treating every positive or reciprocal pair as automatically trustworthy. It does not yet measure the resulting browsing experience. No title, mask, group membership, model wording or cutoff was changed; no hierarchy was generated or repaired.

## Verification and preserved evidence

All 44 earlier TRUE03 inputs and decisions reproduced unchanged: 41/44 still match that pilot's original expectations. That repeat checks implementation continuity, not new generalization.

An independent audit verified every input, score and saved decision, replayed all first-token probabilities from the saved logits, and independently reproduced the complete semantic-analysis arithmetic. It did not re-adjudicate semantic judgments. The one offline CPU run took **76 minutes**, with about **44.24 GiB peak process memory** and no run-scope swap. No additional inference was used for verification.

- [Every accepted relationship and missed nomination](REVIEW.md), [all 3,660 decisions](DECISIONS.md).
- Exact inputs (`inputs.json`), native outputs and full-precision scores (`scores.jsonl`), semantic analysis (`semantic-analysis.json`), accepted-pair judgments (`title-pair-judgments.json`).
- [Frozen plan](../TRUE04-PLAN.md), pre-score reference (`../true04-reference.json`), [reference-review history](../TRUE04-REFERENCE-REVIEW.md), fresh review of misses (`missed-reference-review.json`).
- [Execution, tests and resource details](EXECUTION.md), independent verification (`verification.json`), completion hashes (`completion.json`).

The 449 MiB raw-logit file remains locally preserved as `first-token-logits.npy`, excluded from Git by an exact path rule. Its hash is in the completion record. Inputs, outputs, reviews and summaries remain with the original run; selected final results are identified below. Shared source lives in `sse_multivector/`, with the original run layout preserved in Git history.

**Selected data:** Compact pair-score results, inputs and parameters for `TRUE04` are selected for release as `numerical/pair-scores-7dd83c45e206d5c8` in the [publication catalog](../../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.
