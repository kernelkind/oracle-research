# TRUE03 — Actual generated titles: useful containment, with three discrepancies

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

**At the unchanged 0.142 cutoff, 41 of 44 directional answers matched the expectations recorded before scoring.** The test used 22 pairs from 25 original HDBv2 groups, with their exact v20/Astra-low titles.

| Decision rule | Expected Yes accepted | Expected No rejected | Correct directions |
|---|---:|---:|---:|
| Native generated answer | 14/17 | 27/27 | 41/44 |
| Fixed score > 0.142 | 15/17 | 26/27 | 41/44 |

For the cutoff rule, 13/15 strict broader-to-narrower relationships were accepted, 14/15 reverse directions were rejected, all 12 directions between noncontaining categories were rejected, and both identical-title equivalence directions were accepted. Both directions were correct for 19/22 pairs. These counts describe this selected pilot, not deployment accuracy.

## Three discrepancies at the fixed cutoff

Each question asks whether category A contains category B. TRUE receives B as premise and A as hypothesis. The score below is the full-vocabulary probability of the first output token being `1`, not cosine or calibrated category confidence. “Native” means the complete generated label; “cutoff” is our separate rule.

**1. Does Coffee Consumption contain Coffee?**

A: Coffee Consumption (`Sa241c43eb5`). B: Coffee (`S9c440e7f47`).

Exact model input:

```text
premise: This text is about Coffee. hypothesis: This text is about Coffee Consumption.
```

Expected: **No**. Native: **No**. Score: **0.186424**. Cutoff: **Yes**.

The expected answer is No: the Coffee category also includes subjects such as cultivation, not just drinking coffee. TRUE's native generated answer was No, but our fixed cutoff turned its score into Yes. The correct forward direction, Coffee contains Coffee Consumption, scored 0.966989 and was accepted.

**2. Does Poultry and eggs contain Poultry-Based Food Preparation?**

A: Poultry and eggs (`S5ea79ac96e`). B: Poultry-Based Food Preparation (`Se66af3a9b7`).

Exact model input:

```text
premise: This text is about Poultry-Based Food Preparation. hypothesis: This text is about Poultry and eggs.
```

Expected: **Yes**. Native: **No**. Score: **0.039920**. Cutoff: **No**.

The expected answer is Yes: Poultry and eggs is being used as a broad category that includes poultry topics, including preparing poultry-based food. Both the native answer and the cutoff answer were No.

**3. Does Poultry and eggs contain Making Chicken Stock?**

A: Poultry and eggs (`S5ea79ac96e`). B: Making Chicken Stock (`Sa1a95316f6`).

Exact model input:

```text
premise: This text is about Making Chicken Stock. hypothesis: This text is about Poultry and eggs.
```

Expected: **Yes**. Native: **No**. Score: **0.131106**. Cutoff: **No**.

The expected answer is Yes: making stock from chicken is a poultry subject. Both the native answer and the cutoff answer were No. Its score was close to, but below, the unchanged cutoff.

## What worked

- Coffee contained Coffee Bean Preparation, Coffee Consumption and Appreciating Coffee for Its Flavor. Preparation and consumption were correctly treated as distinct, related categories; so were preparation and flavor appreciation.
- Food contained Food Ingredients, and both contained Sea Salt as a Food Ingredient. Chinese Cuisine and Indian Food were both placed under Food without being treated as containing each other.
- Poultry-Based Food Preparation contained Making Chicken Stock, even though the broader Poultry and eggs links were missed.
- Bitcoin contained Satoshi Bitcoin Units (0.624658); Nostr contained Grow Nostr Campaign (0.603691). Their reverse directions were rejected.
- The two original groups titled Coffee were recognized as equivalent descriptions. This does not test differently worded equivalence or prove identical note membership.

The native-only additional error was **Red meat contains Brisket**: native No, score 0.471738, cutoff Yes. The cutoff therefore recovered one valid relationship while introducing the reverse-coffee error. There is no net correct-count advantage between the two rules in this pilot, and no rule was changed afterward.

## What the discrepancies suggest

The two missed relationships share the same proposed parent, Poultry and eggs. One plausible explanation is that our topic sentence makes TRUE read “and eggs” as requiring an additional subject, whereas a category title can collect poultry topics and egg topics. That would be a mismatch between the category question and how it is expressed as an entailment question. **This is a hypothesis, not an isolated cause**; learned associations or other wording effects remain possible. We did not rewrite the title, change the model input or run a follow-up variant.

A different universal cutoff cannot perfectly separate this observed set: the invalid Coffee Consumption contains Coffee score, 0.186424, is higher than both missed valid poultry scores. This does not mean the model is unusable, or that perfect separation is required.

The coffee error also creates an inconsistent set of predictions: the cutoff accepts Coffee Consumption contains Coffee and Coffee contains Coffee Bean Preparation, but rejects Coffee Consumption contains Coffee Bean Preparation. It also accepts Coffee and Coffee Consumption in both directions. These are consequences of the same error, not additional independent failures; reciprocal Yes answers cannot automatically be treated as proven equivalence.

## Conclusion and next decision

This is encouraging evidence that TRUE can use actual generated titles to recover useful containment relations, including distinguishing related categories from containment. It does not establish that the full collection will form a valid hierarchy.

The broader [TRUE04 test](../TRUE04/RESULTS.md) is now complete: all 61 original groups and 3,660 ordered questions, with titles, wording and cutoff unchanged. Of 106 cutoff-accepted directions, semantic review judged 91 reasonable, 9 incorrect and 6 ambiguous; these include repeated title strings. It recovered 90 of 120 relationships nominated before score inspection, with disputes preserved separately. The reciprocal-coffee error and missed poultry relationships reproduced unchanged. TRUE04 also found false Food/Nostr equivalence even in native answers. No title repair, cutoff change or hierarchy adoption followed.

The pre-score expectations remain unchanged. P16 (Meat Eating / Red meat) and P24 (Art / Music in Coffee Shops) were excluded before inference because the titles permitted materially different scopes. See the [blind review](../TRUE03-BLIND-REVIEW.md). Their exclusion limits what this pilot establishes about ambiguous titles.

## Evidence

- [Every scored direction](DECISIONS.md), exact model inputs (`inputs.json`), raw outputs (`scores.jsonl`), numerical summary (`analysis.json`).
- [Frozen plan](../TRUE03-PLAN.md), [input pairs and scope explanations](fixture.json), unchanged source titles (`titles.json`).
- [Execution and tests](EXECUTION.md), independent verification (`verification.json`).

No title, mask, group membership or expectation was changed after scoring. No hierarchy, review UI, model retraining, new cutoff or paid resource was introduced.

**Selected data:** Compact pair-score results, inputs and parameters for `TRUE03` are selected for release as `numerical/pair-scores-cc65be11ce8ebfa5` in the [publication catalog](../../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.
