# TRUE07 — Does ordinary title wording change containment decisions?

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

TRUE sometimes misses a valid relationship because of wording. This was clear for Bitcoin and satoshis. Steak remained a miss across all three wordings; the coffee relationships and related noncontainments stayed correct.

## What changed

For each relationship, the category meanings stayed fixed while a title was reworded. The current v21 titles are wording 0. Alternatives were written manually for this diagnostic, reviewed before scoring, and are not replacements for the saved generated titles.

Four parent–child relationships used three wordings of one title, keeping the other fixed. Two related noncontainments used all nine combinations of three wordings per title. Both directions were tested: 60 directed checks of six semantic relationships, not 60 independent examples.

This is a selected diagnostic, including known problems and successful controls. It does not estimate the error rate across the collection.

**Hypothesis:** Ordinary rewording that preserves the category meaning will preserve the correct containment decision. The scores themselves need not remain equal.

## What the model saw

For “Does A contain B?”, the complete model input was:

```text
premise: This text is about {B}. hypothesis: This text is about {A}.
```

A and B were replaced with the exact titles below. The reverse check swapped them. The model received no masks, full notes, expected answers or reviewer reasoning.

The model, weights, input format and inference settings were unchanged from TRUE06. “Native” is the model's complete generated 0/1 answer. “Cutoff” is our separate rule: score strictly greater than 0.142 means Yes. The score is the model's first-token probability for 1, not cosine or a calibrated probability of category containment.

## Findings

| Relationship | With the fixed cutoff | Native answer |
| --- | --- | --- |
| Bitcoin contains its smallest units | Correct for 2/3 wordings; one miss | Correct for 1/3 |
| Meat/seafood foods contains Steak | Missed for all 3 wordings | Same |
| Coffee contains coffee-bean preparation | Correct for all 3 wordings | Same |
| Coffee contains flavour appreciation | Correct for all 3 wordings | Same |
| Bean preparation versus flavour appreciation | Correctly rejected in both directions for all 9 combinations | Same |
| Meat/seafood foods versus butter in meals | Correctly rejected in both directions for all 9 combinations | Same |

All 12 reversed parent–child checks were also correctly rejected. No unresolved output occurred.

The errors were missed valid links, not invented parent links, in this sample. At the level of the four positive relationships: one was wording-sensitive, one consistently missed, and two consistently correct.

## Every wording and result

Scores below are unrounded. In the first four sections, the expected forward answer is Yes and the reverse answer is No. Every reverse native and cutoff answer was No.

### R01 — Bitcoin / Satoshis: Bitcoin’s Smallest Units

Satoshis are a narrower Bitcoin unit topic. Bitcoin is not restricted to its smallest units.

Fixed A: **Bitcoin**.

| B wording | A contains B: native | A contains B: cutoff | Score | B contains A: score |
| --- | --- | --- | --- | --- |
| Satoshis: Bitcoin’s Smallest Units | No | No | 0.1065474025314582 | 0.0006432771048666953 |
| Satoshis, the smallest units of Bitcoin | No | Yes | 0.1454850506842777 | 0.00043506894874106134 |
| Bitcoin’s smallest units, called satoshis | Yes | Yes | 0.5136041009346426 | 0.0004102643783335969 |

**Analysis:** The same smallest-unit meaning changed from rejection to acceptance. The third wording is accepted even by native generation, so this is not solely a borderline cutoff crossing. This experiment changes wording as a whole; it does not isolate word order, punctuation or a particular token as the cause.

### R02 — Foods featuring meat or seafood / Steak

Steak is meat-based food. Foods featuring meat or seafood need not be steak.

Fixed B: **Steak**.

| A wording | A contains B: native | A contains B: cutoff | Score | B contains A: score |
| --- | --- | --- | --- | --- |
| Foods featuring meat or seafood | No | No | 0.1235739534223383 | 0.023683376600192332 |
| Foods that feature meat or seafood | No | No | 0.13677494138326873 | 0.018167287031532357 |
| Foods featuring seafood or meat | No | No | 0.0975555661022446 | 0.022500243244448177 |

**Analysis:** All three ordinary descriptions of the parent missed Steak. This is a stable miss across these variants, not a decision flip. The result does not establish why it misses Steak, or that every possible rewording would fail.

### R03 — Coffee / Coffee Bean Preparation

Bean preparation is a coffee topic; coffee is not restricted to bean preparation.

Fixed A: **Coffee**.

| B wording | A contains B: native | A contains B: cutoff | Score | B contains A: score |
| --- | --- | --- | --- | --- |
| Coffee Bean Preparation | Yes | Yes | 0.8361679975206591 | 0.01744520833172085 |
| Preparing coffee beans | Yes | Yes | 0.8347880883889183 | 0.01089222841272651 |
| Preparation of coffee beans | Yes | Yes | 0.7935029270115171 | 0.016366678492359916 |

**Analysis:** All three wordings preserved the useful parent–child decision and its direction. Wording sensitivity was not universal.

### R04 — Coffee / Appreciating Coffee for Its Flavour

Flavour appreciation is a coffee topic; coffee is not restricted to appreciation of its flavour.

Fixed A: **Coffee**.

| B wording | A contains B: native | A contains B: cutoff | Score | B contains A: score |
| --- | --- | --- | --- | --- |
| Appreciating Coffee for Its Flavour | Yes | Yes | 0.9683582251741967 | 0.00815197528310537 |
| Appreciation of coffee’s flavour | Yes | Yes | 0.9436991019115715 | 0.014280380015266868 |
| Appreciating coffee’s flavour | Yes | Yes | 0.9396955321351337 | 0.007296412863370326 |

**Analysis:** All three wordings preserved the useful parent–child decision and its direction. Wording sensitivity was not universal.

### R05 — Coffee Bean Preparation / Appreciating Coffee for Its Flavour

Preparation can influence flavour but need not express appreciation. Flavour can be appreciated without preparing beans. Neither complete topic contains the other.

Both expected answers are No. Every native and cutoff answer was No.

- A0: Coffee Bean Preparation
- A1: Preparing coffee beans
- A2: Preparation of coffee beans
- B0: Appreciating Coffee for Its Flavour
- B1: Appreciation of coffee’s flavour
- B2: Appreciating coffee’s flavour

| A wording | B wording | A contains B: score | B contains A: score |
| --- | --- | --- | --- |
| A0 | B0 | 0.0014061961666864574 | 0.00038546131976702934 |
| A0 | B1 | 0.00137111900921156 | 0.0006844287995340958 |
| A0 | B2 | 0.0014394862725215945 | 0.0005626475237582609 |
| A1 | B0 | 0.002282600923250214 | 0.0013667526711815838 |
| A1 | B1 | 0.0008220435368695805 | 0.0006732818979587872 |
| A1 | B2 | 0.0010746005268995097 | 0.0007763408926770786 |
| A2 | B0 | 0.0012761888233175714 | 0.0009972442725673341 |
| A2 | B1 | 0.0007014446416725719 | 0.00055521576404 |
| A2 | B2 | 0.0008145030151393344 | 0.0005181440215914232 |

Holding either title fixed and varying the other caused no decision flip.

### R06 — Foods featuring meat or seafood / Butter as part of a meal

Butter in a meal does not require meat or seafood, and meat/seafood foods do not require butter. A shared shrimp-risotto mask is overlap, not containment.

Both expected answers are No. Every native and cutoff answer was No.

- A0: Foods featuring meat or seafood
- A1: Foods that feature meat or seafood
- A2: Foods featuring seafood or meat
- B0: Butter as part of a meal
- B1: Butter included in a meal
- B2: Butter in meals

| A wording | B wording | A contains B: score | B contains A: score |
| --- | --- | --- | --- |
| A0 | B0 | 0.0014903492699236348 | 0.0008298165994148826 |
| A0 | B1 | 0.0019924125297277797 | 0.0015452813569825055 |
| A0 | B2 | 0.0019182378099136016 | 0.0011906984981290782 |
| A1 | B0 | 0.0007829974906687453 | 0.000737548238574088 |
| A1 | B1 | 0.0011735361016582328 | 0.0012783793704665852 |
| A1 | B2 | 0.001216613518686508 | 0.0008581078986652583 |
| A2 | B0 | 0.001951483441575649 | 0.0011100762524677763 |
| A2 | B1 | 0.0028055501801930644 | 0.0017996170131727408 |
| A2 | B2 | 0.002455371683245613 | 0.0012509612018056942 |

Holding either title fixed and varying the other caused no decision flip.

## What this establishes—and what it does not

The Bitcoin result provides controlled evidence that ordinary title wording can change a correct containment decision into an error under this fixed TRUE configuration. It is not a title-meaning change introduced by the generator. The other relationships show that score changes need not cause wrong decisions.

There is also useful semantic signal: every expected Yes scored above every expected No in this particular sample (minimum Yes 0.0975555661022446; maximum No 0.023683376600192332). That is worth retaining, not treating TRUE as universally incapable.

It does **not** justify lowering the cutoff to fit this sample. In the preserved TRUE05 results, the invalid parent “Foods featuring meat or seafood” → “Meals featuring potatoes, other vegetables, and animal-based protein” scored 0.14128443363025314—above the missed Steak variants. A lower cutoff that recovers all these misses would admit that known wrong link. The child can include eggs without meat or seafood.

The diagnostic does not establish how often wording causes errors across real categories, how to repair it, or whether TRUE is unusable. It does not validate a complete hierarchy. No variant was selected as a production replacement.

**Agreed investigation priority:** focus on ordinary food relationships, especially the missed containment of Steak by “Foods featuring meat or seafood.” Give the Bitcoin result less weight when judging general performance: limited Bitcoin familiarity could contribute, but its training coverage and the cause of this failure are unestablished. All measured results remain unchanged. The approved fixed-parent follow-up is now complete as [TRUE08](../TRUE08/RESULTS.md): it checks other food members and clear nonmembers. No alternative-model comparison has been run.

## Source masks

These are all 24 canonical v21 masks for the eight categories. They were available to semantic review, not to TRUE. Quoted parts of one mask belong together; masks were not combined across instances. ↵ denotes an original line break. Exact full notes, byte ranges and original note IDs are preserved in `./source-evidence.json`. The older source packets also contain V691 and V190, exact same-note/same-range duplicates of V690 and V189; these were already deduplicated in v21, before this experiment. Nothing was removed based on TRUE07 scores.

### Bitcoin · S50475065d8

- V432: ⟦BITCOIN⟧
- V185: ⟦bitcoin⟧
- V379: ⟦bitcoin⟧

### Satoshis: Bitcoin’s Smallest Units · S983e3758e5

- V189: ⟦satoshi⟧
- V433: ⟦Satoshis⟧

### Foods featuring meat or seafood · S485994b768

- V573: ⟦Guess how much⟧ ⟦cost us⟧ ⟦Argentina⟧ ⟦600 grams of chorizo⟧ ⟦600 grams of rib eye⟧ ⟦1.1kg of Tbone⟧
- V872: ⟦Spaghetti Bolognaise⟧ ⟦feeds 5⟧ ⟦1x med onion  ↵ 1x celery stick ↵ 1x med carrot  ↵ 1-2 cloves garlic  ↵ bunch fresh basil  ↵ 500g ground beef ↵ 1x 400g tin chopped tomatoes ↵ 1x 400g tin tomato purée  ↵ Salt and pepper to taste ↵ 2 Tbls olive oil  ↵ 500g dried spaghetti⟧ ⟦1 tin of water⟧
- V574: ⟦haul⟧ ⟦Argentina⟧ ⟦600 grams⟧ ⟦chorizo⟧ ⟦600 grams⟧ ⟦rib eye⟧ ⟦1.1kg⟧ ⟦Tbone⟧
- V525: ⟦Mushroom Risotto⟧ ⟦Shrimp, Arborio Rice, Pecorino, Cremini Mushroom, Yellow Onion, Garlic, Parsley, Thyme, EVOO, Butter, Dry White Wine, Vegetable Broth, Sea Salt, Pepper, Lemon⟧

### Steak · S62d57141b0

- V690: ⟦Steak⟧ ⟦cheese⟧ ⟦bread⟧
- V940: ⟦sirloin⟧ ⟦cut⟧ ⟦steaks⟧
- V692: ⟦Steak⟧ ⟦extra cheese⟧ ⟦bread⟧

### Coffee · S9c440e7f47

- V381: ⟦Coffee⟧
- V244: ⟦coffee⟧

### Coffee Bean Preparation · S24afa84c49

- V410: ⟦grind coffee beans⟧
- V411: ⟦Rise⟧ ⟦grind coffee beans⟧
- V793: ⟦coffee⟧ ⟦Roasting your own beans⟧

### Appreciating Coffee for Its Flavour · Sbbd7d8dae4

- V858: ⟦Decafe coffee drinkers⟧ ⟦purist coffee enthusiasts⟧ ⟦for⟧ ⟦experience and flavour⟧ ⟦Unlike⟧ ⟦caffeine addicted⟧ ⟦Change my mind⟧
- V794: ⟦coffee⟧ ⟦Roasting⟧ ⟦own beans⟧ ⟦discovering⟧ ⟦taste profile⟧ ⟦uniquely yours⟧
- V795: ⟦coffee⟧ ⟦Roasting your own beans⟧ ⟦discovering a taste profile that’s uniquely yours⟧ ⟦personal journey⟧
- V796: ⟦Roasting your own beans⟧ ⟦discovering a taste profile that’s uniquely yours⟧ ⟦personal journey that no bag of pre-roasted coffee can replicate⟧
- V857: ⟦Decafe coffee drinkers⟧ ⟦purist coffee enthusiasts⟧ ⟦for the experience and flavour⟧

### Butter as part of a meal · S7e8dc24c0e

- V160: ⟦My dinner today⟧ ⟦Butter⟧
- V535: ⟦Mushroom Risotto with Shrimp⟧ ⟦Butter⟧

## Reproduction and preservation

- Pre-inference [plan](./plan.json), semantic review (`./semantic-review.json`), variants (`./variants.json`), exact 60 inputs (`./inputs.json`) and hash manifest (`./frozen.json`).
- Complete raw scores (`./run/scores.jsonl`), raw logits (`./run/first-token-logits.npy`), inference configuration (`./run/config.json`), analysis (`./analysis.json`) and resource record (`./resources.json`).
- Independent verification (`./verification.json`) reproduced every score and decision, checked all frozen/source hashes, and found no discrepancies. Exact repeated inputs retained their old decisions; maximum score difference from TRUE05/06 was 0.0000000482. All 42 relevant regression tests passed before and after inference.
- The local run used the cached pinned TRUE weights, CPU float32 and four threads. It took 105.1 seconds including model verification/loading, with 43.53 GiB peak process RSS. No external model API, rental, training or download.
- Existing v21 titles, source masks, TRUE05, TRUE06 and shared inference code were not changed. The shared fixture's TRUE03 tag is only schema compatibility; the runtime experiment is TRUE07. The generic raw DECISIONS.md uses the word “holdout”; this experiment is not a holdout.
- No UI, category graph or later model comparison was built in this task.

**Selected data:** Compact pair-score results, inputs and parameters for `TRUE07/run` are selected for release as `numerical/pair-scores-d1116bc357976e0f` in the [publication catalog](../../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.
