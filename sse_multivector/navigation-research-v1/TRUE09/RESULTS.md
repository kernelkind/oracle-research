# TRUE09 — Separating the combined category from “Foods featuring”

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

TRUE recognizes the five foods under **Meat** or **Seafood**. Combining those parent categories lowers every positive score. Adding **Foods featuring** also lowers most scores, but not uniformly. The original Steak miss therefore is not simply a failure to recognize steak as meat.

## Experiment

**Question:** Do the combined “meat or seafood” category and the “Foods featuring” qualification each contribute to the low scores observed in TRUE08?

**Control:** The same eight child titles and the original parent **Foods featuring meat or seafood**, repeated from TRUE08.

**Variable:** The parent description. For each positive child, compare its single food category, that category with “Foods featuring,” the combined category, and the full original title. Compare these changes separately within each child.

**Hypothesis:** If combination is involved, replacing the single category with the combined category will lower scores or lose correct answers, both with and without “Foods featuring.” If the qualification is involved, adding it will do so for the single or combined category. Either change could behave differently for different children; negative checks detect incorrect acceptance.

For Steak, Brisket and Roast chicken, the four parents are:

- Meat
- Foods featuring meat
- Meat or seafood
- Foods featuring meat or seafood

For Grilled salmon and Shrimp dishes, replace the first two with **Seafood** and **Foods featuring seafood**. Plain boiled rice, Fresh fruit and Vegan meals are checked against all six parents. Every reverse direction is also checked.

The 38 pairs and their 76 expected answers were frozen before inference. There are 20 expected Yes answers and 56 expected No answers. The same children recur across conditions, so these are not 76 independent examples.

A fresh-context semantic review checked the design before scoring. “Steak” uses the ordinary meat sense supported by the existing node's sirloin mask. “Foods featuring meat” includes meat itself; it does not require a composed dish. We did not test seafood under bare “Meat,” whose scope is debatable. These interpretations were recorded before results.

The parents differ in scope; these are not equivalent paraphrases. A correct containment answer is nevertheless Yes for every declared positive input. The test compares observable model behavior, not an identified internal mechanism.

## What TRUE received

For each A and B below, the exact input is:

```text
premise: This text is about {B}. hypothesis: This text is about {A}.
```

For example:

```text
premise: This text is about Steak. hypothesis: This text is about Meat.
premise: This text is about Steak. hypothesis: This text is about Foods featuring meat.
premise: This text is about Steak. hypothesis: This text is about Meat or seafood.
premise: This text is about Steak. hypothesis: This text is about Foods featuring meat or seafood.
```

Those are four separate calls/inputs, not one combined premise. TRUE saw no masks, notes, expected answers or analysis. Reverse checks swapped A and B. Every exact input is preserved in `./inputs.json`.

**Native** is the model's complete generated 0/1 answer. **Cutoff** is our separate rule: score strictly greater than 0.142 means Yes. The score is the full-vocabulary probability of first output token 209 (“1”), not cosine or a calibrated probability of category containment. The checkpoint, framing, cutoff and inference settings remained unchanged.

## All expected-Yes results

Every row asks whether category A contains category B. Scores are unrounded.

| A: proposed parent | B: proposed child | Score | Native | Cutoff |
| --- | --- | --- | --- | --- |
| Meat | Steak | 0.626186793494629 | Yes | Yes |
| Foods featuring meat | Steak | 0.398648846642382 | No | Yes |
| Meat or seafood | Steak | 0.2122631114669181 | No | Yes |
| Foods featuring meat or seafood | Steak | 0.12357401794475145 | No | No |
| Meat | Brisket | 0.5694532690952429 | Yes | Yes |
| Foods featuring meat | Brisket | 0.4280509579935581 | No | Yes |
| Meat or seafood | Brisket | 0.15927334337990232 | No | Yes |
| Foods featuring meat or seafood | Brisket | 0.14994582539588022 | No | Yes |
| Meat | Roast chicken | 0.5168975138402766 | Yes | Yes |
| Foods featuring meat | Roast chicken | 0.41352397847741473 | No | Yes |
| Meat or seafood | Roast chicken | 0.43376967502926 | No | Yes |
| Foods featuring meat or seafood | Roast chicken | 0.14743377083712622 | No | Yes |
| Seafood | Grilled salmon | 0.5669641586912968 | Yes | Yes |
| Foods featuring seafood | Grilled salmon | 0.4309375722004163 | No | Yes |
| Meat or seafood | Grilled salmon | 0.48435140393976395 | No | Yes |
| Foods featuring meat or seafood | Grilled salmon | 0.19998089383597475 | No | Yes |
| Seafood | Shrimp dishes | 0.5411279589919403 | Yes | Yes |
| Foods featuring seafood | Shrimp dishes | 0.5894762333708646 | Yes | Yes |
| Meat or seafood | Shrimp dishes | 0.09678453800811439 | No | No |
| Foods featuring meat or seafood | Shrimp dishes | 0.08417514555952067 | No | No |

The pattern, keeping each child's four conditions together:

- Combining categories lowered scores in all ten matched comparisons: five without the qualification, five with it.
- Adding “Foods featuring” lowered single-category scores for four children, but raised Shrimp dishes from 0.5411 to 0.5895. It lowered combined-category scores for all five.
- Under the fixed cutoff, both single-category conditions accepted all five children. **Meat or seafood** missed Shrimp dishes. **Foods featuring meat or seafood** missed Steak and Shrimp dishes.
- Native generation accepted all five under the bare single categories, only Shrimp dishes under their qualified versions, and none under either combined category.

The cutoff therefore has three misses among these 20 expected-Yes directions. Native generation has 14. This describes the chosen five foods under four parents, not general model accuracy.

## All forward nonmembers

Every expected answer is No. All 18 are No under both rules.

| A: proposed parent | B: proposed child | Score | Native | Cutoff |
| --- | --- | --- | --- | --- |
| Meat | Plain boiled rice | 0.0006612430952227451 | No | No |
| Foods featuring meat | Plain boiled rice | 0.0009787928894135658 | No | No |
| Seafood | Plain boiled rice | 0.0009602464842878858 | No | No |
| Foods featuring seafood | Plain boiled rice | 0.0014837656454464259 | No | No |
| Meat or seafood | Plain boiled rice | 0.0009405452427960981 | No | No |
| Foods featuring meat or seafood | Plain boiled rice | 0.0010497363802683805 | No | No |
| Meat | Fresh fruit | 0.0004898211406196034 | No | No |
| Foods featuring meat | Fresh fruit | 0.000379937247625777 | No | No |
| Seafood | Fresh fruit | 0.00043596101661185697 | No | No |
| Foods featuring seafood | Fresh fruit | 0.0006329934796586066 | No | No |
| Meat or seafood | Fresh fruit | 0.00048191827549537815 | No | No |
| Foods featuring meat or seafood | Fresh fruit | 0.00037086795318523326 | No | No |
| Meat | Vegan meals | 0.0008188149204104753 | No | No |
| Foods featuring meat | Vegan meals | 0.0005154234653435839 | No | No |
| Seafood | Vegan meals | 0.0004043443667835491 | No | No |
| Foods featuring seafood | Vegan meals | 0.00035699989586838765 | No | No |
| Meat or seafood | Vegan meals | 0.0004891210800930712 | No | No |
| Foods featuring meat or seafood | Vegan meals | 0.0004398610358106002 | No | No |

## All reverse checks

Every expected answer is No. These checks ask whether one child category contains the entire proposed parent category. All 38 are No under both rules.

| A: proposed parent | B: proposed child | Score | Native | Cutoff |
| --- | --- | --- | --- | --- |
| Steak | Meat | 0.026185997524650322 | No | No |
| Steak | Foods featuring meat | 0.01878623694684477 | No | No |
| Steak | Meat or seafood | 0.03448539025492332 | No | No |
| Steak | Foods featuring meat or seafood | 0.02368336006125749 | No | No |
| Brisket | Meat | 0.021850916455498273 | No | No |
| Brisket | Foods featuring meat | 0.011442536409638542 | No | No |
| Brisket | Meat or seafood | 0.01945116266016894 | No | No |
| Brisket | Foods featuring meat or seafood | 0.008630275223838267 | No | No |
| Roast chicken | Meat | 0.006900564940773055 | No | No |
| Roast chicken | Foods featuring meat | 0.009950338456090807 | No | No |
| Roast chicken | Meat or seafood | 0.01058632317725995 | No | No |
| Roast chicken | Foods featuring meat or seafood | 0.011375600344850413 | No | No |
| Grilled salmon | Seafood | 0.017782456091006524 | No | No |
| Grilled salmon | Foods featuring seafood | 0.01689102672051469 | No | No |
| Grilled salmon | Meat or seafood | 0.027431826611013854 | No | No |
| Grilled salmon | Foods featuring meat or seafood | 0.022051603673766306 | No | No |
| Shrimp dishes | Seafood | 0.009366058418104325 | No | No |
| Shrimp dishes | Foods featuring seafood | 0.013103001571320815 | No | No |
| Shrimp dishes | Meat or seafood | 0.009070272061478538 | No | No |
| Shrimp dishes | Foods featuring meat or seafood | 0.010839035613378161 | No | No |
| Plain boiled rice | Meat | 0.0005560577560261664 | No | No |
| Plain boiled rice | Foods featuring meat | 0.0005481835670943718 | No | No |
| Plain boiled rice | Seafood | 0.0003378614326506663 | No | No |
| Plain boiled rice | Foods featuring seafood | 0.0003935115449830842 | No | No |
| Plain boiled rice | Meat or seafood | 0.0002658222859128172 | No | No |
| Plain boiled rice | Foods featuring meat or seafood | 0.0003723980718199731 | No | No |
| Fresh fruit | Meat | 0.0006715980077673081 | No | No |
| Fresh fruit | Foods featuring meat | 0.0006639713238478774 | No | No |
| Fresh fruit | Seafood | 0.0008289264475425135 | No | No |
| Fresh fruit | Foods featuring seafood | 0.0007241200125032327 | No | No |
| Fresh fruit | Meat or seafood | 0.0005076340864628323 | No | No |
| Fresh fruit | Foods featuring meat or seafood | 0.0005451989732339825 | No | No |
| Vegan meals | Meat | 0.001034770557639067 | No | No |
| Vegan meals | Foods featuring meat | 0.0007553698906779702 | No | No |
| Vegan meals | Seafood | 0.00034708263058335395 | No | No |
| Vegan meals | Foods featuring seafood | 0.000420611496830767 | No | No |
| Vegan meals | Meat or seafood | 0.0006614514799556568 | No | No |
| Vegan meals | Foods featuring meat or seafood | 0.0006521152636253363 | No | No |

## What this establishes

1. **Both changes matter in this diagnostic.** The combination depresses scores consistently. The qualification usually does too, with one clear exception. Neither alone explains every result.
2. **Basic food knowledge is present.** TRUE accepts all five simple meat/seafood relationships natively. Its misses appear when these foods are placed under some more elaborate parent descriptions.
3. **The negative checks remain clean, but are mostly easy.** All true directions scored above all negatives in this sample. That does not demonstrate reliable separation of overlapping food categories.
4. **No production repair follows automatically.** Removing words would change the approved parent meaning. The test does not validate splitting arbitrary category titles or combining component answers. It also does not establish that all compound categories fail.

Do not fit a lower cutoff here. An earlier incorrect relationship, **Foods featuring meat or seafood** containing **Meals featuring potatoes, other vegetables, and animal-based protein**, scored 0.14128443363025314 in TRUE05—above both original-parent misses here. Animal-based protein need not be meat or seafood. Recovering these misses by lowering the cutoff would also admit that known error.

**Completed follow-up:** [TRUE10](../TRUE10/RESULTS.md) built the provisional graph with the current titles and unchanged TRUE rule. It preserves raw decisions and source memberships. Two reviewed duplicate-category pairs were consolidated; two non-equivalence cycles remain, alongside useful local connections and missing destinations. It did not produce a completed acyclic hierarchy. This replaced the proposed frontier-judge comparison; no new judge or prompt-development effort was run. All TRUE09 measurements above are preserved.

## Record

The original parent and Steak are existing v21 nodes; the other descriptions are controlled diagnostic inputs, not newly generated HDBSCAN groups. [TRUE08's original masks](../TRUE08/RESULTS.md#existing-masks) provide their source context. No masks were changed or supplied to this model.

- [Plan](./plan.json), semantic review (`./semantic-review.json`), titles (`./titles.json`), [fixture](./fixture.json), freeze manifest (`./frozen.json`).
- Every raw score (`./run/scores.jsonl`), raw logits (`./run/first-token-logits.npy`), configuration (`./run/config.json`), derived analysis (`./analysis.json`).
- Independent verification (`./verification.json`) checked all 76 raw scores, complete native outputs and cutoff decisions, the frozen files, and 51 preserved inputs/artifacts.
- All 16 repeated original-parent inputs and answers reproduce TRUE08. Ten logits rows are identical; six have small numerical differences. Maximum score difference is 0.00000020972746420100385, with no decision changes.
- Local offline inference took 112.7 seconds including verification/loading, with 43.29 GiB peak process RSS. One model process, 60 GiB scope memory cap, no scope swap; resources (`./resources.json`). No new paid resource or API call.
- All 42 relevant regression tests passed before and after. Shared production code, model settings, frozen earlier results, category titles and cutoff remain unchanged.
- The legacy fixture schema tag is TRUE03 and the raw shared decisions heading says “holdout.” Runtime identity is TRUE09; this is a selected diagnostic, not a holdout.
- No hierarchy or UI was generated. Existing tracking card is CREC-127; no Plane tool was available, so no external card update is claimed.

**Selected data:** Compact pair-score results, inputs and parameters for `TRUE09/run` are selected for release as `numerical/pair-scores-5e07db0afb5b7b6e` in the [publication catalog](../../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.
