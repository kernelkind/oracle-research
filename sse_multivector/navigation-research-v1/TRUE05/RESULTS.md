# TRUE05 — Do the current titles clarify the old ambiguous relationships?

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

Six of seven selected pairs now have clear category meanings for this comparison. **TRUE still missed the one valid containment tested: Foods featuring meat or seafood → Steak.** It rejected all twelve directions.

The first finding concerns title clarity; the second concerns TRUE's answers. Neither is a constructed hierarchy or a general accuracy estimate. These are seven reused cases, not a holdout. Some old cards already had user decisions; this is not a claim that all six clear cases were previously undecidable to the user.

After the run, the user gave **U052 a qualified Yes**: “yes i think, though it is arguable both ways.” This is recorded separately from the pre-run judgments below. U052 was not sent to TRUE and is not added to the original test counts.

## Results

Each question asks **Does A contain B?** The reverse was also tested for each clear pair; all six reverse answers were No and agreed with the frozen judgments.

| ID | Current A | Current B | Pre-run judgment | Native | Cutoff | Score |
|---|---|---|---|---|---|---|
| U001 | Feedback on how food recipes turn out | Meat-based meals in a crockpot | No | No | No | 0.002216 |
| U023 | Foods featuring meat or seafood | Raw Milk | No | No | No | 0.001817 |
| U024 | Foods featuring meat or seafood | Meals featuring potatoes, other vegetables, and animal-based protein | No | No | No | 0.141284 |
| U026 | Foods featuring meat or seafood | Steak | Yes | No | No | 0.123574 |
| U028 | Foods featuring meat or seafood | Butter as part of a meal | No | No | No | 0.001490 |
| U040 | Visual Art | Music at Coffee Shops | No | No | No | 0.000611 |
| U052 | Dishes with Toppings or Seasonings | Foods with sea salt | Uncertain | Not run | Not run | — |

The score is TRUE's full-vocabulary probability of first generating token `1`, not cosine or calibrated containment confidence. The native answer is its complete generated label (`0` or `1`); our separate cutoff rule accepts scores strictly greater than **0.142**.

Although 11/12 decisions match the frozen judgments, that is eleven correct rejections and **zero of one valid containment recovered**. It should not be presented as broad 91.7% success.

## The concrete remaining model problem

TRUE saw exactly:

```text
premise: This text is about Steak. hypothesis: This text is about Foods featuring meat or seafood.
```

It generated `0` (No). Its score was **0.123574**, below 0.142. Steak is meat-based food, and the masks below explicitly show sirloin/steak; the reverse does not hold because the parent also includes other meat and seafood foods.

Simply lowering the cutoff cannot make both relevant judgments correct here. The broader category **Meals featuring potatoes, other vegetables, and animal-based protein** scored **0.141284** against the same proposed parent. That category includes eggs, explicitly present in V001, so it is not wholly inside meat/seafood. Any threshold low enough to accept Steak would also accept that noncontainment. This is one local score-ordering failure, not a claim that TRUE is useless generally.

## Every pair, with its exact masks

These masks support our review; they were **not** supplied to TRUE. TRUE received only the exact category titles in the fixed sentence template. Same-note exact duplicates were already removed in the source title artifact; the masks below are unchanged.

### U001

Previous titles: **Recipes and Their Results** → **Crockpot Meat Dishes**.

Previous uncertainty: Crockpot meat dishes can be the results of recipes. But the category can also cover the dishes themselves without presenting or evaluating a recipe.

Previous user decision: **no**. This remains an answer about the old wording; it is not overwritten by the current assessment.

**A — Feedback on how food recipes turn out** (S07d0857008)

- V237: ⟦pancakes⟧ ⟦recipe⟧ ⟦Let us know how it tastes!⟧
- V663: ⟦Irish soda bread recipe I tried out recently⟧ ⟦very pleased⟧ ⟦turned out great⟧

**B — Meat-based meals in a crockpot** (S0c034c4006)

- V103: ⟦I have⟧ ⟦crockpot of beef stew⟧
- V826: ⟦I got up early and put the roast and veggies in the crockpot⟧

**Assessment:** Crockpot meat meals do not necessarily communicate feedback on recipe outcomes; recipe feedback need not concern meat or crockpots.

A contains B: expected No; native No; cutoff No; score 0.002216.

B contains A: expected No; native No; cutoff No; score 0.000310.

### U023

Previous titles: **Food Ingredients** → **Raw Milk**.

Previous uncertainty: Raw milk can be an ingredient or a drink on its own. I am unsure whether the parent includes foods that can be ingredients, or only their use as ingredients.

Previous user decision: **yes**. Comment: “hmmm A means things that CONTAINS food ingredients. B IS A food ingredient... not sure how to reconcile” This remains an answer about the old wording; it is not overwritten by the current assessment.

**A — Foods featuring meat or seafood** (S485994b768)

- V573: ⟦Guess how much⟧ ⟦cost us⟧ ⟦Argentina⟧ ⟦600 grams of chorizo⟧ ⟦600 grams of rib eye⟧ ⟦1.1kg of Tbone⟧
- V872: ⟦Spaghetti Bolognaise⟧ ⟦feeds 5⟧ ⟦1x med onion <br>1x celery stick<br>1x med carrot <br>1-2 cloves garlic <br>bunch fresh basil <br>500g ground beef<br>1x 400g tin chopped tomatoes<br>1x 400g tin tomato purée <br>Salt and pepper to taste<br>2 Tbls olive oil <br>500g dried spaghetti⟧ ⟦1 tin of water⟧
- V574: ⟦haul⟧ ⟦Argentina⟧ ⟦600 grams⟧ ⟦chorizo⟧ ⟦600 grams⟧ ⟦rib eye⟧ ⟦1.1kg⟧ ⟦Tbone⟧
- V525: ⟦Mushroom Risotto⟧ ⟦Shrimp, Arborio Rice, Pecorino, Cremini Mushroom, Yellow Onion, Garlic, Parsley, Thyme, EVOO, Butter, Dry White Wine, Vegetable Broth, Sea Salt, Pepper, Lemon⟧

**B — Raw Milk** (S349051e569)

- V044: ⟦raw milk slush⟧
- V408: ⟦Stay humble⟧ ⟦stack⟧ ⟦raw milk⟧
- V407: ⟦stack⟧ ⟦raw milk⟧
- V046: ⟦ngl⟧ ⟦raw milk slush⟧ ⟦soooo good⟧
- V045: ⟦raw milk slush⟧ ⟦soooo good⟧

**Assessment:** Raw milk is dairy, not meat or seafood. Foods featuring meat or seafood need not contain raw milk. This changes the old ambiguous Food Ingredients wording rather than overturning the user's old-title decision.

A contains B: expected No; native No; cutoff No; score 0.001817.

B contains A: expected No; native No; cutoff No; score 0.000520.

### U024

Previous titles: **Food Ingredients** → **Meals with Potatoes and Other Vegetables**.

Previous uncertainty: The meals are described by their ingredients, but a complete meal is not itself an ingredient. The answer depends on whether the parent covers ingredient-related meal topics.

**A — Foods featuring meat or seafood** (S485994b768)

- V573: ⟦Guess how much⟧ ⟦cost us⟧ ⟦Argentina⟧ ⟦600 grams of chorizo⟧ ⟦600 grams of rib eye⟧ ⟦1.1kg of Tbone⟧
- V872: ⟦Spaghetti Bolognaise⟧ ⟦feeds 5⟧ ⟦1x med onion <br>1x celery stick<br>1x med carrot <br>1-2 cloves garlic <br>bunch fresh basil <br>500g ground beef<br>1x 400g tin chopped tomatoes<br>1x 400g tin tomato purée <br>Salt and pepper to taste<br>2 Tbls olive oil <br>500g dried spaghetti⟧ ⟦1 tin of water⟧
- V574: ⟦haul⟧ ⟦Argentina⟧ ⟦600 grams⟧ ⟦chorizo⟧ ⟦600 grams⟧ ⟦rib eye⟧ ⟦1.1kg⟧ ⟦Tbone⟧
- V525: ⟦Mushroom Risotto⟧ ⟦Shrimp, Arborio Rice, Pecorino, Cremini Mushroom, Yellow Onion, Garlic, Parsley, Thyme, EVOO, Butter, Dry White Wine, Vegetable Broth, Sea Salt, Pepper, Lemon⟧

**B — Meals featuring potatoes, other vegetables, and animal-based protein** (S4a36e8ac6b)

- V048: ⟦dinner⟧ ⟦Lamb with steamed seasoned broccoli and baby potatoes⟧
- V052: ⟦dinner⟧ ⟦Lamb with steamed seasoned broccoli and baby potatoes really hit the spot⟧
- V001: ⟦Fired up⟧ ⟦rocket stove to cook potatoes, cabbage, green beans, and eggs⟧

**Assessment:** Animal-based protein includes eggs, explicitly present in V001. B is therefore not wholly within meat or seafood. A's meat/seafood foods need not include potatoes and other vegetables.

A contains B: expected No; native No; cutoff No; score 0.141284.

B contains A: expected No; native No; cutoff No; score 0.002000.

### U026

Previous titles: **Food Ingredients** → **Steak**.

Previous uncertainty: Steak can be an ingredient in a dish or a finished food. It is unclear whether the parent covers steak generally or only its ingredient uses.

**A — Foods featuring meat or seafood** (S485994b768)

- V573: ⟦Guess how much⟧ ⟦cost us⟧ ⟦Argentina⟧ ⟦600 grams of chorizo⟧ ⟦600 grams of rib eye⟧ ⟦1.1kg of Tbone⟧
- V872: ⟦Spaghetti Bolognaise⟧ ⟦feeds 5⟧ ⟦1x med onion <br>1x celery stick<br>1x med carrot <br>1-2 cloves garlic <br>bunch fresh basil <br>500g ground beef<br>1x 400g tin chopped tomatoes<br>1x 400g tin tomato purée <br>Salt and pepper to taste<br>2 Tbls olive oil <br>500g dried spaghetti⟧ ⟦1 tin of water⟧
- V574: ⟦haul⟧ ⟦Argentina⟧ ⟦600 grams⟧ ⟦chorizo⟧ ⟦600 grams⟧ ⟦rib eye⟧ ⟦1.1kg⟧ ⟦Tbone⟧
- V525: ⟦Mushroom Risotto⟧ ⟦Shrimp, Arborio Rice, Pecorino, Cremini Mushroom, Yellow Onion, Garlic, Parsley, Thyme, EVOO, Butter, Dry White Wine, Vegetable Broth, Sea Salt, Pepper, Lemon⟧

**B — Steak** (S62d57141b0)

- V690: ⟦Steak⟧ ⟦cheese⟧ ⟦bread⟧
- V940: ⟦sirloin⟧ ⟦cut⟧ ⟦steaks⟧
- V692: ⟦Steak⟧ ⟦extra cheese⟧ ⟦bread⟧

**Assessment:** Steak is meat-based food; the supplied sirloin/steak masks support that ordinary meaning. Meat/seafood foods also include chorizo, ground beef and shrimp, so the reverse is false.

A contains B: expected Yes; native No; cutoff No; score 0.123574.

B contains A: expected No; native No; cutoff No; score 0.023683.

### U028

Previous titles: **Food Ingredients** → **Butter**.

Previous uncertainty: Butter is a familiar ingredient, but can also be discussed as a food or product. I am unsure whether that distinction matters for the intended scope of Food Ingredients.

**A — Foods featuring meat or seafood** (S485994b768)

- V573: ⟦Guess how much⟧ ⟦cost us⟧ ⟦Argentina⟧ ⟦600 grams of chorizo⟧ ⟦600 grams of rib eye⟧ ⟦1.1kg of Tbone⟧
- V872: ⟦Spaghetti Bolognaise⟧ ⟦feeds 5⟧ ⟦1x med onion <br>1x celery stick<br>1x med carrot <br>1-2 cloves garlic <br>bunch fresh basil <br>500g ground beef<br>1x 400g tin chopped tomatoes<br>1x 400g tin tomato purée <br>Salt and pepper to taste<br>2 Tbls olive oil <br>500g dried spaghetti⟧ ⟦1 tin of water⟧
- V574: ⟦haul⟧ ⟦Argentina⟧ ⟦600 grams⟧ ⟦chorizo⟧ ⟦600 grams⟧ ⟦rib eye⟧ ⟦1.1kg⟧ ⟦Tbone⟧
- V525: ⟦Mushroom Risotto⟧ ⟦Shrimp, Arborio Rice, Pecorino, Cremini Mushroom, Yellow Onion, Garlic, Parsley, Thyme, EVOO, Butter, Dry White Wine, Vegetable Broth, Sea Salt, Pepper, Lemon⟧

**B — Butter as part of a meal** (S7e8dc24c0e)

- V160: ⟦My dinner today⟧ ⟦Butter⟧
- V535: ⟦Mushroom Risotto with Shrimp⟧ ⟦Butter⟧

**Assessment:** Butter as part of a meal does not require meat or seafood, and meat/seafood foods do not require butter. The shared shrimp-risotto example establishes overlap, not containment.

A contains B: expected No; native No; cutoff No; score 0.001490.

B contains A: expected No; native No; cutoff No; score 0.000830.

### U040

Previous titles: **Art** → **Music in Coffee Shops**.

Previous uncertainty: Music is an art form, so this fits a category covering the arts broadly. It does not fit if Art is intended to mean visual art.

**A — Visual Art** (S8a6ab7afaf)

- V391: ⟦Photography⟧
- V757: ⟦painting⟧
- V761: ⟦#artoninstagram⟧ ⟦#painting⟧
- V758: ⟦watercolourpainting⟧
- V377: ⟦art⟧

**B — Music at Coffee Shops** (S8ea08f1aff)

- V035: ⟦Rave at a coffee shop⟧
- V295: ⟦playing⟧ ⟦coffee shop⟧ ⟦music⟧

**Assessment:** Visual Art makes the accepted intended sense explicit. Music and raves at coffee shops do not belong to visual art; visual art does not require music or coffee shops.

A contains B: expected No; native No; cutoff No; score 0.000611.

B contains A: expected No; native No; cutoff No; score 0.000399.

### U052

Previous titles: **Seasonings and Toppings for Savory Dishes** → **Sea Salt as a Food Ingredient**.

Previous uncertainty: The parent explicitly limits itself to savory dishes. Sea salt as a food ingredient also permits uses outside savory seasoning or toppings.

**A — Dishes with Toppings or Seasonings** (Sd5f4538ab9)

- V901: ⟦omlette⟧ ⟦topped⟧ ⟦parm⟧
- V539: ⟦Mushroom Risotto with Shrimp⟧ ⟦Pepper⟧
- V881: ⟦Spaghetti Bolognaise⟧ ⟦Salt and pepper to taste⟧
- V902: ⟦omlette⟧ ⟦topped⟧ ⟦jalepenos⟧ ⟦parm⟧
- V532: ⟦Mushroom Risotto with Shrimp⟧ ⟦Parsley⟧

**B — Foods with sea salt** (Sfd8645f195)

- V362: ⟦bagels⟧ ⟦sea salt flakes⟧
- V538: ⟦Mushroom Risotto with Shrimp⟧ ⟦Sea Salt⟧
- V360: ⟦bagels⟧ ⟦sesame⟧ ⟦sea salt flakes⟧ ⟦plain⟧

**Assessment:** The actual bagel and risotto masks fit dishes seasoned with salt. But Foods with sea salt also permits ingredients such as salted butter; its full title scope is not unambiguously narrower than dishes. Reverse containment is clearly false, but the whole pair is left for user review, outside this binary model test.

**Not submitted to TRUE.** The user subsequently answered: “yes i think, though it is arguable both ways.” Record A containing B as a qualified Yes, preserving the caveat. This does not retroactively make the pre-run judgment unambiguous, add a model result, decide the reverse direction, or establish a general rule about foods and dishes.

## What changed, and what did not

The title strings are the existing generated v21 titles, not newly written for this test. In particular, the old Food Ingredients group is now Foods featuring meat or seafood; this clarifies the actual group but changes the question compared with the old broad wording. Old user answers and TRUE04 scores remain intact. `./comparison.json` retains both versions of every tested direction without assigning the current answers to the old titles.

Six current pairs were judged clear before inference. A fresh independent reviewer saw only current titles and masks, not prior decisions or model scores, and agreed on all twelve tested directions. The main reviewer had seen historical work, so this is not claimed as a wholly blinded new benchmark. U052 remained uncertain after reconciliation and was excluded before inference.

The [plan](./plan.json), frozen judgments and masks (`./semantic-review.json`), exact model inputs (`./run/inputs.json`), raw outputs (`./run/scores.jsonl`), configuration (`./run/config.json`), resource record (`./resources.json`), and verification (`./verification.json`) preserve the experiment. The unchanged renderer's inherited holdout wording in run/DECISIONS.md must not be interpreted as a holdout design here.

Offline cached TRUE ran once, CPU float32, four threads, batch size four, with the same weights, generation settings, input template and 0.142 cutoff as TRUE04. Model work took about 78 seconds including checkpoint verification/loading and 17 seconds for the inference/report interval. Peak process RSS was about 43.7GiB. No downloads, training, paid API calls or rentals occurred. The scope was memory-limited and exited successfully.

No title prompt was changed or frozen, no title was manually corrected, and no hierarchy was constructed. The category-label evidence is encouraging in these selected cases; dependable containment decisions remain unestablished.

**Selected data:** Compact pair-score results, inputs and parameters for `TRUE05/run` are selected for release as `numerical/pair-scores-57a416d20d022ca3` in the [publication catalog](../../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.
