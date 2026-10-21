# TRUE06 — Finding parent–child relationships

The fixed cutoff found **8 of 9** relationships we judged valid before inference, and correctly rejected **all 15** negative directions. Native model answers found **6 of 9**, with the same 15 correct rejections.

This is a small test using existing category titles, mostly food and coffee. It is **not a holdout or a whole-hierarchy evaluation**.

## What was tested

A → B means: **category A contains category B as a narrower topic**. Each of 12 pairs was checked in both directions. Nine directions were expected Yes; fifteen were expected No. The titles were not rewritten. The masks supported our judgments but were not sent to TRUE.

The model saw:

```text
premise: This text is about {B}. hypothesis: This text is about {A}.
```

Native Yes/No comes from TRUE’s complete generated `1`/`0` answer. The separate cutoff rule accepts an answer only when its saved score is **greater than 0.142**. This score is the first-output-token probability of `1` over the full vocabulary—not cosine similarity or calibrated containment confidence. Decisions use full precision; the tables display six decimals.

## Results

| Check | Native answer | Fixed cutoff |
|---|---:|---:|
| Valid parent–child relationships found | 6 / 9 | 8 / 9 |
| Reversed relationships correctly rejected | 9 / 9 | 9 / 9 |
| Related noncontainments correctly rejected | 6 / 6 | 6 / 6 |
| Pairs correct in both directions | 9 / 12 | 11 / 12 |
| All directed decisions correct | 21 / 24 | 23 / 24 |

Every direction is listed below. “Expected” is our pre-run judgment, not an answer supplied to the model.

| Pair | Proposed parent A | Proposed child B | Expected | Native | Cutoff | Score |
|---|---|---|---|---|---|---:|
| P01 | Food | Brisket | Yes | Yes | Yes | 0.626476 |
| P01 | Brisket | Food | No | No | No | 0.012057 |
| P02 | Food | Raw Milk | Yes | Yes | Yes | 0.525075 |
| P02 | Raw Milk | Food | No | No | No | 0.001752 |
| P03 | Food Preparation and Dining | Making Chicken Stock | Yes | No | Yes | 0.163581 |
| P03 | Making Chicken Stock | Food Preparation and Dining | No | No | No | 0.002538 |
| P04 | Foods featuring meat or seafood | Meat-based meals in a crockpot | Yes | No | Yes | 0.277598 |
| P04 | Meat-based meals in a crockpot | Foods featuring meat or seafood | No | No | No | 0.004974 |
| P05 | Coffee | Coffee Bean Preparation | Yes | Yes | Yes | 0.836168 |
| P05 | Coffee Bean Preparation | Coffee | No | No | No | 0.017445 |
| P06 | Coffee | Appreciating Coffee for Its Flavour | Yes | Yes | Yes | 0.968358 |
| P06 | Appreciating Coffee for Its Flavour | Coffee | No | No | No | 0.008152 |
| P07 | Bitcoin | Satoshis: Bitcoin’s Smallest Units | Yes | No | No | 0.106547 |
| P07 | Satoshis: Bitcoin’s Smallest Units | Bitcoin | No | No | No | 0.000643 |
| P08 | Coffee Bean Preparation | Appreciating Coffee for Its Flavour | No | No | No | 0.001406 |
| P08 | Appreciating Coffee for Its Flavour | Coffee Bean Preparation | No | No | No | 0.000385 |
| P09 | Visual Art | Music at Coffee Shops | No | No | No | 0.000611 |
| P09 | Music at Coffee Shops | Visual Art | No | No | No | 0.000399 |
| P10 | Foods featuring meat or seafood | Butter as part of a meal | No | No | No | 0.001490 |
| P10 | Butter as part of a meal | Foods featuring meat or seafood | No | No | No | 0.000830 |
| P11 | Coffee | Having drunk coffee | Yes | Yes | Yes | 0.870951 |
| P11 | Having drunk coffee | Coffee | No | No | No | 0.037948 |
| P12 | Food consumption | Meat eating | Yes | Yes | Yes | 0.740588 |
| P12 | Meat eating | Food consumption | No | No | No | 0.012094 |

## Every missed relationship

Recipe line breaks are shown as spaces below; exact source whitespace is preserved in `source-evidence.json`.

### P03 — Food Preparation and Dining → Making Chicken Stock

Expected: **Yes**. Native: **No**. Cutoff: **Yes**. Exact score: `0.16358104743150909`.

Exact model input:

```text
premise: This text is about Making Chicken Stock. hypothesis: This text is about Food Preparation and Dining.
```

**A: Food Preparation and Dining** (`S49eb0ac749`)

- V059: ⟦cooked⟧ ⟦proper food tonight⟧ ⟦went down well⟧
- V303: ⟦grilling out dinner⟧
- V057: ⟦cooked⟧ ⟦proper food tonight⟧
- V551: ⟦kitchen⟧ ⟦Today meat dumplings⟧
- V711: ⟦right way to cook things⟧
- V709: ⟦chef⟧
- V047: ⟦I was rather impressed⟧ ⟦dinner tonight⟧
- V447: ⟦sacred⟧ ⟦sharing a meal⟧

**B: Making Chicken Stock** (`Sa1a95316f6`)

- V196: ⟦Today i⟧ ⟦Acquired⟧ ⟦prepared⟧ ⟦tomato’s⟧ ⟦Made⟧ ⟦yogurt⟧ ⟦bagged⟧ ⟦chicken meat⟧ ⟦made⟧ ⟦chicken stock⟧ ⟦cleaned⟧ ⟦dishes⟧
- V092: ⟦stock pots rolling today⟧ ⟦batch of chicken stock⟧
- V206: ⟦i⟧ ⟦rotisserie chickens⟧ ⟦bagged⟧ ⟦meat⟧ ⟦made⟧ ⟦chicken stock from the bones⟧
- V094: ⟦stock pots rolling⟧ ⟦chicken stock⟧ ⟦We save carcasses when we butcher⟧

**Why we expected containment:** Making chicken stock is food preparation, supported by cooking, stock pots and chicken bones. Food Preparation and Dining is an umbrella for preparation and dining, not a requirement that every child perform both. Stock making does not encompass all preparation or dining.

**What happened:** The native answer missed this relationship. The unchanged cutoff recovered it.

### P04 — Foods featuring meat or seafood → Meat-based meals in a crockpot

Expected: **Yes**. Native: **No**. Cutoff: **Yes**. Exact score: `0.2775984649264226`.

Exact model input:

```text
premise: This text is about Meat-based meals in a crockpot. hypothesis: This text is about Foods featuring meat or seafood.
```

**A: Foods featuring meat or seafood** (`S485994b768`)

- V573: ⟦Guess how much⟧ ⟦cost us⟧ ⟦Argentina⟧ ⟦600 grams of chorizo⟧ ⟦600 grams of rib eye⟧ ⟦1.1kg of Tbone⟧
- V872: ⟦Spaghetti Bolognaise⟧ ⟦feeds 5⟧ ⟦1x med onion 1x celery stick 1x med carrot 1-2 cloves garlic bunch fresh basil 500g ground beef 1x 400g tin chopped tomatoes 1x 400g tin tomato purée Salt and pepper to taste 2 Tbls olive oil 500g dried spaghetti⟧ ⟦1 tin of water⟧
- V574: ⟦haul⟧ ⟦Argentina⟧ ⟦600 grams⟧ ⟦chorizo⟧ ⟦600 grams⟧ ⟦rib eye⟧ ⟦1.1kg⟧ ⟦Tbone⟧
- V525: ⟦Mushroom Risotto⟧ ⟦Shrimp, Arborio Rice, Pecorino, Cremini Mushroom, Yellow Onion, Garlic, Parsley, Thyme, EVOO, Butter, Dry White Wine, Vegetable Broth, Sea Salt, Pepper, Lemon⟧

**B: Meat-based meals in a crockpot** (`S0c034c4006`)

- V103: ⟦I have⟧ ⟦crockpot of beef stew⟧
- V826: ⟦I got up early and put the roast and veggies in the crockpot⟧

**Why we expected containment:** The crockpot category specifies meat-based meals, and its masks describe beef stew and a roast. These fall within foods featuring meat or seafood; that broader category does not require crockpot cooking.

**What happened:** The native answer missed this relationship. The unchanged cutoff recovered it.

### P07 — Bitcoin → Satoshis: Bitcoin’s Smallest Units

Expected: **Yes**. Native: **No**. Cutoff: **No**. Exact score: `0.1065474025314582`.

Exact model input:

```text
premise: This text is about Satoshis: Bitcoin’s Smallest Units. hypothesis: This text is about Bitcoin.
```

**A: Bitcoin** (`S50475065d8`)

- V432: ⟦BITCOIN⟧
- V185: ⟦bitcoin⟧
- V379: ⟦bitcoin⟧

**B: Satoshis: Bitcoin’s Smallest Units** (`S983e3758e5`)

- V189: ⟦satoshi⟧
- V433: ⟦Satoshis⟧

**Why we expected containment:** The fixed child title explicitly identifies satoshis as Bitcoin units. This is a narrower Bitcoin topic, not a claim that a unit is itself an entire cryptocurrency. Bitcoin is not restricted to its smallest units.

**What happened:** Both the native answer and the unchanged cutoff missed this relationship. This single result does not establish whether the cause is domain knowledge, the topic-statement wording, or another limitation of the model.

## What this changes

TRUE is not merely returning No: it found eight usable narrower-topic relationships while keeping every tested reverse and noncontaining direction separate. That supports considering a partial graph using the current rule. It does not mean every pair among the 61 categories will be handled this well.

There is no reason here to revise the title prompt or tune the cutoff. Lowering the cutoff enough to accept the missed Bitcoin relationship would also accept the previously rejected TRUE05 relationship **Foods featuring meat or seafood → Meals featuring potatoes, other vegetables, and animal-based protein**, which scored `0.14128443363025314`. The earlier result remains relevant; this smaller sample does not erase it.

## The two excluded questions

You answered **No** to both **Food consumption → Having drunk coffee** and **Coffee → Music at Coffee Shops**. Those answers arrived after selection but before inference. Both pairs remained outside this run, as stated when presented. They are recorded in `user-review.json`, not counted as model successes or failures. Reverse directions were not decided by you.

## Reproducibility and limits

- All titles are the existing v21 outputs; no new LLM generation, mask edits, training, wrapper wording changes, or threshold tuning occurred.
- Judgments were settled before scores. An independently spawned reviewer checked titles and masks without historical model results. The main agent already knew earlier experiments, so this was not fully blind.
- Six directed inputs repeat TRUE04 exactly: both directions of P01, P02, and P05. Four repeat TRUE05 exactly: both directions of P09 and P10. These are repetitions, not ten new independent examples. This overlap was checked after freezing the selection and did not change it.
- Canonical v21 masks are used. V060 and V190 were omitted only as same-note exact duplicates of V059 and V189. Source text, note IDs, byte spans, and masks are preserved in `source-evidence.json`.
- The unchanged model was `google/t5_xxl_true_nli_mixture`, revision `aa6cfe1dd4257853bfdd772992045f41bfc14988`, local CPU float32, four threads, batch size four. Both generation and token scores are preserved.
- The run took 64.43 seconds including checkpoint verification/loading; peak process RSS was 43.42 GiB. The scope had a 60 GiB memory ceiling and zero swap allowance. No download, paid API call, or rental was used.
- `fixture.json` uses the old TRUE03 schema discriminator to reuse the unchanged validator; the experiment is TRUE06. The shared raw `run/DECISIONS.md` incorrectly calls this a holdout by template. This report supplies the correct description.

Independent verification reproduced all input directions, native decisions, cutoff decisions, and summaries. Raw-logit replay matched all saved score fields; independent softmax differed by at most `2.22e-16`. All 75 canonical masks match their source byte spans. The 42 relevant regression tests passed before and after inference. See `verification.json`.

Files: `plan.json` and `semantic-review.json` preserve pre-run choices; `run/inputs.json` and `run/scores.jsonl` preserve every exact model input and result; `analysis.json` records conclusions; `resources.json` records execution limits.
