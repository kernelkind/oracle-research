# TRUE08 — Does the meat/seafood category miss foods other than Steak?

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

Yes. With the unchanged 0.142 cutoff, TRUE also missed **Shrimp dishes**. It accepted Brisket, Roast chicken and Grilled salmon. Native generation answered No to every case.

## Experiment

**Question:** Is the existing Steak miss an isolated item, or does the same parent also miss other obvious food members?

**Control:** The exact existing relationship “Foods featuring meat or seafood” contains “Steak,” repeated from TRUE07.

**Variable:** The proposed child category. The parent remained **Foods featuring meat or seafood** for all eight forward checks. Other members cover beef, poultry, fish and shellfish; three nonmembers are food categories not requiring meat or seafood. Every reverse direction was also checked.

**Hypothesis:** This parent will accept several other clear meat/seafood members while rejecting clear nonmembers. If further members fail, the problem is not exclusive to Steak; if other members pass, the parent does not fail universally.

The exact titles and expected answers were checked in fresh context before scoring. All eight cases were retained. The extra child categories are manually selected diagnostic descriptions, not newly generated HDBSCAN nodes. No masks were invented for them.

## Exact input

For A = the proposed parent and B = the proposed child, TRUE received:

```text
premise: This text is about {B}. hypothesis: This text is about {A}.
```

For example, the Steak check was exactly:

```text
premise: This text is about Steak. hypothesis: This text is about Foods featuring meat or seafood.
```

The model saw only those title strings, not masks, notes, expectations, reasons or earlier results. Reverse checks swapped A and B.

TRUE weights, CPU float32 inference, input framing and cutoff are unchanged. **Native** means the model's complete generated 0/1 answer. **Cutoff** is our separate rule: the saved score must be strictly greater than 0.142 for Yes. The score is the full-vocabulary probability of first output token 209 (“1”), not cosine or a calibrated probability of category containment.

## All results

Fixed A: **Foods featuring meat or seafood**. Each row asks whether A contains B. Scores are unrounded.

| B | Expected | Native | Cutoff | Score |
| --- | --- | --- | --- | --- |
| Steak | Yes | No | No | 0.1235739534223383 |
| Brisket | Yes | No | Yes | 0.14994582539588022 |
| Roast chicken | Yes | No | Yes | 0.14743398056459042 |
| Grilled salmon | Yes | No | Yes | 0.19998089383597475 |
| Shrimp dishes | Yes | No | No | 0.0841750905038157 |
| Plain boiled rice | No | No | No | 0.0010497363802683805 |
| Fresh fruit | No | No | No | 0.00037086795318523326 |
| Vegan meals | No | No | No | 0.0004398610358106002 |

The cutoff recovered 3 of 5 valid forward relationships; native generation recovered none. Both rules correctly rejected all three forward nonmembers. These are eight selected relationships, not a population accuracy estimate.

For the reverse checks, B was fixed to **Foods featuring meat or seafood**. Each row asks whether category A contains that entire category. Every expected, native and cutoff answer was No.

| A | Expected | Native | Cutoff | Score |
| --- | --- | --- | --- | --- |
| Steak | No | No | No | 0.023683351790971564 |
| Brisket | No | No | No | 0.008630275223838267 |
| Roast chicken | No | No | No | 0.0113755909605274 |
| Grilled salmon | No | No | No | 0.022051603673766306 |
| Shrimp dishes | No | No | No | 0.01083904072552144 |
| Plain boiled rice | No | No | No | 0.0003723980718199731 |
| Fresh fruit | No | No | No | 0.0005451989732339825 |
| Vegan meals | No | No | No | 0.0006521152636253363 |

## Interpretation

1. **Not just Steak.** Shrimp dishes also misses the fixed cutoff. This is an ordinary-food case and does not depend on Bitcoin familiarity.
2. **Not wholesale failure either.** Brisket, Roast chicken and Grilled salmon pass the cutoff. Two are close to it; the native model rejects all five valid relationships.
3. **Useful separation remains.** The lowest-scoring valid member is Shrimp dishes at 0.0841750905038157. The highest-scoring forward nonmember is plain boiled rice at 0.0010497363802683805. Even the largest reverse score, 0.023683351790971564, is below every valid member.
4. **The cause remains open.** Keeping the parent fixed establishes which additional children are accepted or missed. It does not isolate parent wording, the combined category, the “This text is about” framing, or another model behavior as the cause.

Do not lower the cutoff to fit these cases. The preserved TRUE05 incorrect relationship “Foods featuring meat or seafood” contains “Meals featuring potatoes, other vegetables, and animal-based protein” scored 0.14128443363025314. A cutoff low enough to recover both missed foods here would accept that known incorrect relationship as well. No cutoff was changed.

## Relevant results already available

After TRUE08, I checked earlier scores before recommending a new basic-food test. TRUE04 already provides these exact title-only relationships, under the same model, framing and inference configuration:

| Proposed parent | Child | Score | Native | Cutoff |
| --- | --- | --- | --- | --- |
| Food | Steak | 0.7755322806573992 | Yes | Yes |
| Red meat | Steak | 0.7616807831363871 | Yes | Yes |
| Food | Brisket | 0.6264764137890964 | Yes | Yes |
| Red meat | Brisket | 0.47173792530090025 | No | Yes |

TRUE already recognizes some simpler relationships for the same foods. We do not need to rerun those checks. These are reused historical results, not additional TRUE08 trials, and the parent meanings differ. They argue against a blanket inability to recognize these food categories but do not prove why the combined parent is difficult. Exact input strings and provenance are in `./existing-comparisons.json`; old node memberships are not being treated as current categories.

**Approved follow-up completed:** [TRUE09](../TRUE09/RESULTS.md) separately compared the combined “meat or seafood” category and the “foods featuring” qualification, holding the food children and inference settings fixed. Expectations were checked before scoring the different-scope parents. This was a diagnostic; production titles and the cutoff remain unchanged. All TRUE08 measurements above are preserved.

## Existing masks

The fixed parent and repeated Steak node are bound to existing v21 category IDs. The other child titles are manually selected diagnostic inputs. Canonical masks for those two existing nodes are preserved below for context; they were not given to TRUE. Fragments of each mask stay together; ↵ marks an original line break.

### Foods featuring meat or seafood · S485994b768

- V573: ⟦Guess how much⟧ ⟦cost us⟧ ⟦Argentina⟧ ⟦600 grams of chorizo⟧ ⟦600 grams of rib eye⟧ ⟦1.1kg of Tbone⟧
- V872: ⟦Spaghetti Bolognaise⟧ ⟦feeds 5⟧ ⟦1x med onion  ↵ 1x celery stick ↵ 1x med carrot  ↵ 1-2 cloves garlic  ↵ bunch fresh basil  ↵ 500g ground beef ↵ 1x 400g tin chopped tomatoes ↵ 1x 400g tin tomato purée  ↵ Salt and pepper to taste ↵ 2 Tbls olive oil  ↵ 500g dried spaghetti⟧ ⟦1 tin of water⟧
- V574: ⟦haul⟧ ⟦Argentina⟧ ⟦600 grams⟧ ⟦chorizo⟧ ⟦600 grams⟧ ⟦rib eye⟧ ⟦1.1kg⟧ ⟦Tbone⟧
- V525: ⟦Mushroom Risotto⟧ ⟦Shrimp, Arborio Rice, Pecorino, Cremini Mushroom, Yellow Onion, Garlic, Parsley, Thyme, EVOO, Butter, Dry White Wine, Vegetable Broth, Sea Salt, Pepper, Lemon⟧

### Steak · S62d57141b0

- V690: ⟦Steak⟧ ⟦cheese⟧ ⟦bread⟧
- V940: ⟦sirloin⟧ ⟦cut⟧ ⟦steaks⟧
- V692: ⟦Steak⟧ ⟦extra cheese⟧ ⟦bread⟧

## Record

- [Pre-inference plan](./plan.json), semantic review (`./semantic-review.json`), titles (`./titles.json`), exact inputs (`./inputs.json`), and freeze manifest (`./frozen.json`).
- Every raw score (`./run/scores.jsonl`), logits (`./run/first-token-logits.npy`), configuration (`./run/config.json`), derived analysis (`./analysis.json`), and resource record (`./resources.json`).
- Independent verification (`./verification.json`) reproduced all 16 scores and decisions and checked frozen inputs, prior artifacts and unchanged model settings. The Steak forward result exactly reproduces TRUE07. Its reverse score differs only by about 0.000000025, with no decision change.
- Offline local run: 63.6 seconds including checkpoint verification/loading; 43.37 GiB peak process RSS. One model process, 60GiB scope memory limit, no scope swap. All 42 relevant regressions passed before and after.
- Shared production code and all frozen TRUE07 inputs/raw outputs remain unchanged. The legacy fixture schema tag is TRUE03; runtime identity is TRUE08. Raw shared DECISIONS.md says “holdout,” but this is a selected diagnostic.
- No hierarchy, title change, extra model comparison or UI was generated. Existing Plane card is CREC-127; the Plane tool was unavailable, so no external card update is claimed.

**Selected data:** Compact pair-score results, inputs and parameters for `TRUE08/run` are selected for release as `numerical/pair-scores-e42f023da4b36520` in the [publication catalog](../../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.
