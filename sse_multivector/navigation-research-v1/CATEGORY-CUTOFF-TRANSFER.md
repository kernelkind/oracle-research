# Transfer of a category cutoff

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

The cutoff fitted on Coffee and Morning greetings did not transfer usefully to
Bread, Chicken and Salt. It missed **10 of 13 supported assignments**. The
unchanged native cutoff missed none and admitted **one of 21 unsupported
assignments**. Both conditions use exactly the same scores.

Within each of the three categories, every judged relevant note scored above
every judged irrelevant note. The result rejects this transferred global cutoff,
not the usefulness of the rankings or the broader construction architecture.
It does not establish that a single cutoff could never offer a useful imperfect
tradeoff. No threshold was retuned or adopted.

## What was tested

[TCC04's frozen plan](./TCC04-PLAN.md) compares native 0.5 with
**0.9969531560953688**, chosen on TCC03 and committed before TCC04 selection.
TCC04 contains 12 different notes, all their 145 saved subject descriptions
(143 canonical masks), and three existing construction-category strings.
There are **435 separately scored single-category inputs**, not joint-label
classification. A note's category score is the maximum across all its saved
descriptions. The model sees a description and category, not the original note.

These are classifier scores, **not cosine similarities or verified membership
probabilities**. Each score is the sigmoid of the native classifier logit.
The cutoffs differ only in which of those unchanged scores they admit.

Source-based judgments were frozen before scoring and independently reviewed:
13 supported, 21 unsupported and two unresolved note/category assignments.
These are correlated assignments from 12 deliberately selected notes, not a
population accuracy estimate. Neither the notes nor the categories are
research-naive, although none of these notes was in TCC01–TCC03 and none of these
category strings was used to fit the cutoff.

## Results

| Category | Native: retained / missed / incorrect additions | Frozen: retained / missed / incorrect additions |
| --- | ---: | ---: |
| Bread | 5 / 0 / 0 | 2 / 3 / 0 |
| Chicken | 4 / 0 / 1 | 1 / 3 / 0 |
| Salt | 4 / 0 / 0 | 0 / 4 / 0 |
| Total | 13 / 0 / 1 | 3 / 10 / 0 |

The frozen rule keeps only Bread/N023, Bread/N047 and Chicken/N026.
It triggers the predeclared retrieval safeguard for **every category**:
more than half of each category's supported notes are lost. Salt is empty.
Its total error is ten rather than one, so the primary hypothesis also fails.

Unresolved boundaries remain outside those counts. Chicken/N023, whose dinner
has eggs without a stated species, is included only at 0.5. Bread/N020, whose
dinner includes pizza, is omitted at both cutoffs. Neither decision is counted
as correct or incorrect.

## The one incorrect addition at 0.5

**Chicken · N047 · row849 · score 0.7955949469212105**

Saved description: “The baking space remains very hot for some time.”

Complete original with the attaining mask:

> Cleaning out the ashes to now ⟦put in the bread pans⟧. It ⟦remains very hot for some time⟧. Takes about 5-6 min for them to cook. https://video.nostr.build/1287907c5686c9eb72895eb5c52a9869aaff5ed6c46db7041ed4d8797635af04.mp4 https://image.nostr.build/ac895487f166b3e2a6bfb161d4bc0fca1a8720386968b3187981b6dcbf18d7ae.jpg https://image.nostr.build/9a73232d8b89163a07272467dab427cfe8549181b9a74da654d353b4b68ed6ce.jpg  nostr:note1tc57qmd25gu4ddgqwyuk3my7endvrxvwgdtqldvd066ml5f885tqps5a3c

The selected words support heat retained while baking bread. Neither the mask
nor the full readable note discusses chicken. The category error is not repaired
by removing this generic description alone. Another unchanged description,
row838, explicitly says “Bread in the pans takes about 5–6 minutes to cook.” and still scores Chicken
**0.5810889931427398**, above 0.5.

The complete original with row838's mask:

> Cleaning out the ashes to now put in the ⟦bread pans⟧. It remains very hot for some time. ⟦Takes about 5-6 min⟧ for them to ⟦cook⟧. https://video.nostr.build/1287907c5686c9eb72895eb5c52a9869aaff5ed6c46db7041ed4d8797635af04.mp4 https://image.nostr.build/ac895487f166b3e2a6bfb161d4bc0fca1a8720386968b3187981b6dcbf18d7ae.jpg https://image.nostr.build/9a73232d8b89163a07272467dab427cfe8549181b9a74da654d353b4b68ed6ce.jpg  nostr:note1tc57qmd25gu4ddgqwyuk3my7endvrxvwgdtqldvd066ml5f885tqps5a3c

That second result rules out the narrow explanation that only the missing word
“bread” in row849 caused the note admission. It does not isolate why the model
associates these cooking descriptions with Chicken. One occasional error is not
itself grounds for discarding the model; the failed transfer concerns the
tradeoff made by the stricter rule.

## Every missed supported assignment

All ten missed assignments have genuinely supporting attaining masks. No
post-score mask repair or favorable witness substitution is used below.
When one note has two missed categories, each has its own score, description
and complete-note mask overlay.

### N011

**Bread · row42 · score 0.9964726685701406**

Saved description: “Ham-and-cheese mochi bread from a Japanese convenience store.”

> https://www.alojapan.com/1198654/how-to-cook-this-mochi-bread-from-combini-need-recipe/ How to cook this “⟦mochi bread⟧” from ⟦combini⟧? Need recipe. #food #JapaneseFood So, I was in Japan this summer and among many-many new tasty things I found this: (picture from internet; google the word 生もちっ ⟦ハムチーズ⟧ ) https://preview.redd.it/3xrbmo1mmpie1.jpg?width=750&format=pjpg&auto=webp&s=5f062e504119cf9e7803a399320d908153ed824b >! https://www.youtube.com/watch?v=vp9lT2-ue0c!< Pretty common food for combini (Lawson if I remember co…
>
> https://media.channels.im/media_attachments/files/113/991/553/366/222/878/original/51c9a85d3eeb84dc.jpg

The intact source explicitly discusses mochi bread and requests a recipe. Its truncation is recorded; no missing words or linked material are needed for Bread. This is a missed supported assignment, not absent extraction evidence.

### N046

**Bread · row649 · score 0.7907212008873039**

Saved description: “Bagels with a chewy texture.”

> Turn pantry staples into ⟦chewy bagels⟧ 🥯 
>
> Toppings : sesame, sea salt flakes and plain 
>
> #foodstr   
> https://m.primal.net/OHSR.jpg
> https://m.primal.net/OHSS.jpg

**Salt · row779 · score 0.7614537723989248**

Saved description: “Bagels topped with sea salt flakes.”

> Turn pantry staples into chewy ⟦bagels⟧ 🥯 
>
> Toppings : sesame, ⟦sea salt flakes⟧ and plain 
>
> #foodstr   
> https://m.primal.net/OHSR.jpg
> https://m.primal.net/OHSS.jpg

Bagels are a bread type. The second mask separately identifies sea salt as a topping. Both meanings are explicit or ordinary category refinements, despite their scores being much lower than several valid examples elsewhere.

### N075

**Bread · row558 · score 0.9855959977881305**

Saved description: “Extra-toasted bread for a steak-and-cheese sandwich.”

> ⟦Steak⟧ and ⟦cheese⟧ extra cheese light pepperoni ⟦bread extra toasted⟧ and raw onions white or red it dont matter 

The mask explicitly identifies extra-toasted bread. Its score is below the transferred cutoff even though it is the highest Bread score for this note.

### N010

**Chicken · row278 · score 0.9956183020274599**

Saved description: “Ordering a chicken dish with a name beginning with “General” at a Chinese takeout restaurant.”

> You ever walk into a ⟦Chinese take out place⟧ and ⟦order general⟧ whatever ⟦chicken⟧...then when you come to pick up your food...the lady behind the register is eating some beautiful dish that looks simple and clean with veggies and soup but isn't on the menu.....

The selected passage explicitly describes ordering chicken. No generic food association or inference from an unmentioned ingredient is needed.

### N020

**Chicken · row867 · score 0.9941485473089521**

Saved description: “Pizza with barbecue chicken.”

> Leftover ⟦BBQ chicken pizza⟧ from yesterday and shrimp tempura sushi for dinner
> #foodstr https://image.nostr.build/f091997302fbf0fe6dfdb2d2f4aee3acee67c14a78db24ad64c5b5a80990e2d6.jpg

Barbecue chicken is explicit in the pizza description. The separate Pizza/Bread boundary remains unresolved; it does not weaken the Chicken evidence.

### N091

**Chicken · row538 · score 0.9920119524500289**

Saved description: “Century eggs are made from duck, chicken, or quail eggs.”

> ⟦Century eggs⟧, also called alkalized or preserved eggs, are a Chinese culinary delicacy ⟦made⟧ by preserving ⟦duck, chicken, or quail eggs⟧ in a mixture of clay, ash, salt, quicklime, and rice hulls for several weeks to several months.
>  https://t.co/H3rYBZBKd3 https://video.twimg.com/ext_tw_video/1771890392331653120/pu/vid/avc1/720x1280/ECtlOiuN11A8UeTv.mp4?tag=12

**Salt · row35 · score 0.9492049546845808**

Saved description: “Century eggs are made by preserving eggs in a mixture of clay, ash, salt, quicklime, and rice hulls.”

> ⟦Century eggs⟧, also called alkalized or preserved eggs, are a Chinese culinary delicacy made by ⟦preserving⟧ duck, chicken, or quail ⟦eggs in a mixture of clay, ash, salt, quicklime, and rice hulls⟧ for several weeks to several months.
>  https://t.co/H3rYBZBKd3 https://video.twimg.com/ext_tw_video/1771890392331653120/pu/vid/avc1/720x1280/ECtlOiuN11A8UeTv.mp4?tag=12

Chicken eggs and the salt-containing preservation mixture are explicit, separately supported meanings. The note need not be exclusively about chicken or salt to belong in those categories.

### N063

**Salt · row822 · score 0.9850477320799099**

Saved description: “Sea salt as an ingredient in mushroom risotto with shrimp.”

> ⟦Mushroom Risotto with Shrimp⟧👨‍🍳
>
> 📝 Shrimp, Arborio Rice, Pecorino, Cremini Mushroom, Yellow Onion, Garlic, Parsley, Thyme, EVOO, Butter, Dry White Wine, Vegetable Broth, ⟦Sea Salt⟧, Pepper, Lemon.
>
> #foodstr #nostr https://image.nostr.build/c05d0c4857aa8b1c788bb74d90569f18d4e934e7c9896b2a9b0ea0a11519a624.jpg https://image.nostr.build/60be2aa485e15fddde8fbc8be8bd6d67728c4832b4e9365276a90d59efdbb3ce.jpg 

Sea salt is explicitly an ingredient. The lower-scoring broad ingredient-list description does not erase this specific supporting description.

### N096

**Salt · row508 · score 0.9941940917765758**

Saved description: “Salt and pepper to taste in spaghetti Bolognaise.”

> My #neverfail ⟦Spaghetti Bolognaise⟧ recipe that feeds 5. 
> 1x med onion 
> 1x celery stick
> 1x med carrot 
> 1-2 cloves garlic 
> bunch fresh basil 
> 500g ground beef
> 1x 400g tin chopped tomatoes
> 1x 400g tin tomato purée 
> ⟦Salt and pepper to taste⟧
> 2 Tbls olive oil 
> 500g dried spaghetti 
>
> In a large pan on medium heat, sauté the finely chopped onion, celery and carrot in the olive oil. After a few minutes add the crushed garlic. Once onions are clear, push to side and add ground beef. Gently fry beef without browning. Once beef is all the same colour add both tins of tomatoes plus 1 tin of water. Add chopped fresh basil leaves. Mix all ingredients thoroughly. Simmer on low heat for 45min-1hr. 
> Cook spaghetti according to packet. 
> #food #recipe #easy #spaghetti #bolognaise #tomato #dinner
>
> https://m.primal.net/ODru.mov

Salt and pepper are explicitly listed and selected. The generic all-ingredients description is not the only available input; row508 provides the precise seasoning meaning.

## What the ordering establishes

| Category | Lowest supported note score | Highest unsupported note score | Incorrect within-category orderings |
| --- | ---: | ---: | ---: |
| Bread | 0.790721201 | 0.328862733 | 0 of 30 |
| Chicken | 0.992011952 | 0.795594947 | 0 of 28 |
| Salt | 0.761453772 | 0.324475379 | 0 of 32 |

There are zero inversions in 90 judged positive–negative comparisons within
categories. This is retrospective evidence of separability for these inputs,
not an automatic method for locating each boundary. It neither defines one
correct taxonomy nor requires every future category to be perfectly separable.

Across categories, the unsupported Chicken/N047 score, **0.795594947**, exceeds
the supported Bread/N046 (**0.790721201**) and Salt/N046 (**0.761453772**) scores.
Thus these particular decisions cannot all be made perfectly by one shared
cutoff. An imperfect shared rule might still be useful; the measured native
result is an example on this challenge. Earlier TCC03 errors prevent treating
its 0.5 cutoff as universally sufficient.

The observed distinction is between category-specific useful rankings and
a transferred numeric decision. Changing notes and categories together does
not causally identify whether label identity, content, source-description
counts or another distribution difference shifted the scores. A per-category
constant correction would preserve rankings; that alone does not establish
how to estimate the correction without new category judgments.

## All note decisions

“row” identifies a saved CAP04 description and its mask, not a hierarchy node
or a newly generated SSE vector. Every maximum has one attaining row.
All scores below are rounded for display; the audit (`./TCC04/audit.json`)
preserves exact values and supporting-witness scores.

| Category | Note | Source judgment | Maximum score | Attaining description | Native 0.5 | Frozen cutoff |
| --- | --- | --- | ---: | --- | --- | --- |
| bread | N006 | unsupported | 0.022673283 | row331 | omit | omit |
| bread | N010 | unsupported | 0.328862733 | row483 | omit | omit |
| bread | N011 | supported | 0.996472669 | row42 | include | omit |
| bread | N020 | unresolved | 0.054987024 | row334 | omit | omit |
| bread | N023 | supported | 0.999213747 | row659 | include | include |
| bread | N026 | unsupported | 0.117698938 | row899 | omit | omit |
| bread | N046 | supported | 0.790721201 | row649 | include | omit |
| bread | N047 | supported | 0.998776724 | row375 | include | include |
| bread | N063 | unsupported | 0.016813749 | row457 | omit | omit |
| bread | N075 | supported | 0.985595998 | row558 | include | omit |
| bread | N091 | unsupported | 0.233377766 | row538 | omit | omit |
| bread | N096 | unsupported | 0.083852648 | row742 | omit | omit |
| chicken | N006 | unsupported | 0.023708746 | row331 | omit | omit |
| chicken | N010 | supported | 0.995618302 | row278 | include | omit |
| chicken | N011 | unsupported | 0.448929144 | row346 | omit | omit |
| chicken | N020 | supported | 0.994148547 | row867 | include | omit |
| chicken | N023 | unresolved | 0.992671337 | row392 | include | omit |
| chicken | N026 | supported | 0.998620014 | row531 | include | include |
| chicken | N046 | unsupported | 0.144815026 | row649 | omit | omit |
| chicken | N047 | unsupported | 0.795594947 | row849 | include | omit |
| chicken | N063 | unsupported | 0.013864743 | row553 | omit | omit |
| chicken | N075 | unsupported | 0.080139543 | row177 | omit | omit |
| chicken | N091 | supported | 0.992011952 | row538 | include | omit |
| chicken | N096 | unsupported | 0.205716621 | row698 | omit | omit |
| salt | N006 | unsupported | 0.088777196 | row811 | omit | omit |
| salt | N010 | unsupported | 0.203126742 | row870 | omit | omit |
| salt | N011 | unsupported | 0.111205194 | row603 | omit | omit |
| salt | N020 | unsupported | 0.079876638 | row334 | omit | omit |
| salt | N023 | unsupported | 0.202248015 | row813 | omit | omit |
| salt | N026 | unsupported | 0.261871074 | row27 | omit | omit |
| salt | N046 | supported | 0.761453772 | row779 | include | omit |
| salt | N047 | unsupported | 0.324475379 | row849 | omit | omit |
| salt | N063 | supported | 0.985047732 | row822 | include | omit |
| salt | N075 | unsupported | 0.314267135 | row177 | omit | omit |
| salt | N091 | supported | 0.949204955 | row35 | include | omit |
| salt | N096 | supported | 0.994194092 | row508 | include | omit |

## Combined development tradeoffs

Before adding category-specific calibration, a separate retrospective check
enumerated all shared-cutoff outcomes on the combined TCC03 and TCC04 maxima.
This calculation uses already exposed judgments. It does not change the frozen
TCC04 test or turn these outcomes into validation. The complete calculation is
in combined development tradeoffs (`./TCC04/combined-development-tradeoffs.json`).

There are 76 note/category assignments from 32 distinct notes: 32 supported,
36 unsupported and eight unresolved. These are the 76 measured pairs, not all
160 combinations of 32 notes and five categories. The nondominated judged
outcomes are:

| Supported retained | Supported missed | Incorrectly admitted |
| ---: | ---: | ---: |
| 32 | 0 | 11 |
| 31 | 1 | 10 |
| 30 | 2 | 6 |
| 25 | 7 | 5 |
| 23 | 9 | 4 |
| 21 | 11 | 2 |
| 17 | 15 | 1 |
| 15 | 17 | 0 |

The minimum equal-cost development error is eight: 30 retained, two missed and
six incorrectly admitted. Both misses concern N046, under Bread and Salt.
All six incorrect admissions are Morning greetings: N031, N035, N036, N038,
N043 and N080. Every category retains more than half its supported notes at
this tradeoff; there is no empty supported destination. Nevertheless, greetings
contains eight supported, six unsupported and three unresolved notes, so the
pooled result hides a substantial local problem. All six unresolved admissions
at this tradeoff are Coffee/N005 and N034, Morning greetings/N018, N045 and N052,
and Chicken/N023. Its full original scores and masks remain in
TCC03 inputs (`./TCC03/inputs.json`) and TCC03 audit (`./TCC03/audit.json`).

This is enough to keep a simple shared rule as a **research component**, not
enough to adopt it. It would be a methodological mistake to infer that a more
complex category-specific mechanism is necessary merely because the earlier
two-category fitted cutoff failed. Perfect membership is not a prerequisite
for testing whether construction has more fundamental remaining problems.

## Consequences for construction

Do not deploy the transferred cutoff, tune it on these results, or change the
extractor to explain these misses. Existing descriptions already contain the
necessary evidence. Retain the scorer as a possible membership-ranking
component; it has not become a dependable universal membership decision.

The resulting construction question is now tested in
[CPC01–CPC02](./CATEGORY-PATH-COMPATIBILITY.md), keeping a source-derived family,
both relation rules, prior counterexamples and unresolved scopes fixed.
Both classifier cutoffs remove three meaningful paths. The failure mechanisms
are distinguished by exact note evidence: incorrect child additions versus
incorrect parent omissions. No silent upward union or cutoff retuning hides
those contradictions.

CPC02's word-form control recovers the two genuine development-condition gains
without incorrect additions and retains the paths. It does not fix incomplete
categories, duplicates or broader semantic omissions. That result redirects
work toward construction and semantic relation evidence, not another
probability-calibration benchmark. A score gap or well-fitted mixture alone
still does not establish a semantic boundary.

This does not construct categories or establish parent–child meaning. Those
dependencies remain necessary: source-grounded category proposals, recoverable
membership, and genuine narrowing of the represented meaning and note set.
Corrected membership alone will not validate subset-based parents.

CPC01 froze its concrete strings from CAP04's ordered source occurrences,
rather than rewriting CAP02's unordered feature sets. For example, sorted
`salt sea` features are not automatically equivalent model inputs to the
observed phrase `sea salt`. That provenance distinction remains necessary;
neither experiment certifies every candidate string as a complete category.

## Calibration alternatives reconsidered

Zhao et al. estimate contextual label bias using content-free input in GPT
classification. Their correction normalizes generative label-token probabilities
against a closed answer set. Their empty string, N/A and literal [MASK] probes
are not validated neutral references for GLiClass's independent binary outputs.
In particular, [MASK] has pretrained special-token semantics in its tokenizer.
The study motivates asking whether a reference response helps; it does not
establish that subtracting it yields correct membership here.[^1]

CASENT uses empty-input type likelihood as an additional learned calibration
feature for overlapping entity types. It fits that feature's contribution,
the original likelihood and intercept with development supervision, sharing
parameters by type frequency. The bias-feature ablation reduces macro-F1 from
51.3 to 49.4 on its UFET test. This supports the feature in its native setting,
not fixed unit subtraction or annotation-free transfer to new GLiClass labels.
An absent-text response may encode legitimate lack of evidence rather than
a removable nuisance offset.[^2]

These methods remain alternatives, not selected implementations. No empty-input
guard was bypassed, no reference scores were generated and no extra classifier
component was added. The combined shared-cutoff calculation makes a bounded
construction diagnostic more consequential than introducing that mismatch now.

## Evidence and reproduction

- [Frozen plan](./TCC04-PLAN.md), judgments (`./TCC04/judgments.json`) and
  prescore hashes (`./TCC04/prescore-manifest.json`).
- All 145 unchanged input records (`./TCC04/inputs.json`): complete originals,
  subject descriptions, fragments, source-note IDs and GDC09 alias references.
- Every request and score (`./TCC04/run/scores.json`): exact rendered input,
  token IDs, logits and native sigmoid scores.
- Audit (`./TCC04/audit.json`): every note maximum, both decisions, every error,
  prespecified supporting witnesses and independent audit.
- Runtime configuration (`./TCC04/run/config.json`) and
  [the exact executed runner](./TCC04/run/native_category_probe.py).
- Prior [decision-method research](./CATEGORY-DECISION-METHODS.md) explains
  the fixed cutoff, alternatives and their actual supervision requirements.

All prescore hashes still match. Every input is an unchanged CAP04 record in
original order, and all 145 source aliases and byte-span fragments match GDC09.
The replay at `/tmp/tcc04-offline-replay-20260912` reproduces all 435 scores,
rendered inputs, token IDs and source snapshots byte-for-byte. Model/source
hashes and configuration match except timing and peak memory measurements.
The four existing runner tests pass; no production code changed.

Both runs used one local CPU process with two Torch threads and cached public
weights, without paid resources or downloads. Inference took 15.505 and 15.403
seconds; peak RSS was 5,147,264 and 5,148,832 KiB, approximately 4.91 GiB.
No inference remains running. GDC09, prior experiments and the browser are
unchanged. The hierarchy goal remains open; no review-tool packaging occurred.

## Sources

[^1]: Tony Z. Zhao et al. [Calibrate Before Use: Improving Few-Shot Performance of Language Models](https://proceedings.mlr.press/v139/zhao21c/zhao21c.pdf). ICML 2021, §5 and §5.2; actual score normalization, reference inputs and reference sensitivity. GLiClass's input/token semantics were separately checked in its pinned native implementation and existing model audit.
[^2]: Yanlin Feng, Adithya Pratapa and David Mortensen. [Calibrated Seq2seq Models for Efficient and Generalizable Ultra-fine Entity Typing](https://aclanthology.org/2023.findings-emnlp.1040.pdf). Findings of EMNLP 2023, §3.4, §5.2 and Table4; calibration features, supervision, transfer qualifications and ablation.
