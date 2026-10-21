# HRC02 — Harder HierarCaps evaluation

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

The results strengthen the case for HierarCaps as a broader–narrower signal. They do not establish a complete hierarchy-building method.

We tested **51 unchanged masks from 27 notes**, using the same released model, exact-mask inputs, and score as HRC01. No training, added context, model tuning, new hierarchy, or browser changes.

The cases were selected and independently reviewed before scores existed. Thirteen clearer category relationships, five activity descriptions, two coffee controls, and seven qualified examples were kept separate. The source corpus is mostly food and everyday life; this is not a representative accuracy estimate or broad technical-domain test.

## What happened

| Fixed group | Direction favored the proposed broader mask | Preferred the relevant broader mask over the alternative |
|---|---:|---:|
| Clearer categories | 13 / 13 | 14 / 14 |
| Activity descriptions | 5 / 5 | 4 / 5 |
| Coffee activities with shared wording | 2 / 2 | 2 / 2 |
| Qualified examples, for inspection only | 6 / 7 | 7 / 7 |

The category group has one extra comparison because freezing beets was compared against two different alternatives. Several cases share anchors or source notes; these are not independent trials of general accuracy.

Twelve category cases lacked a shared subject-word family. All favored the intended direction and relevant broader mask. These included bread → bagels, art → photography, dog → a Chihuahua's diet, and food preservation → freezing beets. The thirteenth, preserved century eggs, shares the preserved/preservation word family.

**Score legend:** For A → B, lower angles favor A as broader than B. Reversing the arrow tests the opposite direction. These are the paper-defined exterior angles, not probabilities. Cosine instead measures similarity, with higher values indicating more similarity. All cosines here use the same HierarCaps vectors—not SSE vectors.

V identifiers identify saved source masks, not the old SSE vector values. ⟦Brackets⟧ show exact mask text; fragment boundaries and complete source notes appear below.

## A useful distinction: preservation versus the same vegetable

The fixed narrower mask was:

[V148](#v148) ⟦beets Vac sealed ready for the freezer⟧

We compared these proposed broader masks:

| Proposed broader mask | Angle — lower favors broader | Cosine — higher means more similar |
|---|---:|---:|
| [V942](#v942) ⟦foodpreservation⟧ | 84.28° | 0.2876 |
| [V147](#v147) ⟦This year’s beets raised bed⟧ | 107.13° | 0.5228 |

Cosine favors the other beet passage. The directional score instead favors food preservation. That is useful for the intended parent relationship: growing beets and preserving beets concern the same vegetable but are different activities.

The source of V148 says the beets are vacuum-sealed and ready for the freezer; it does not claim they are already frozen. The intended broad topic is preservation, not a claim about an already completed freezing event.

## It did not simply treat the shorter text as broader

These broader activity descriptions contain more model tokens than their narrower examples:

| Proposed broader mask | Narrower mask | Token counts, broader / narrower | Forward angle | Reversed angle |
|---|---|---:|---:|---:|
| [V547](#v547) ⟦In the kitchen as always a lot of work⟧ | [V108](#v108) ⟦Preparing sourdough bread⟧ | 11 / 5 | 116.28° | 125.85° |
| [V547](#v547) ⟦In the kitchen as always a lot of work⟧ | [V201](#v201) ⟦Today i Made big jar yogurt⟧ | 11 / 8 | 113.48° | 135.55° |
| [V465](#v465) ⟦Education is the way forward⟧ | [V451](#v451) ⟦Bitcoin workshop⟧ | 7 / 4 | 116.82° | 136.52° |

All three favor the intended direction. Two share the kitchen-work mask. Two additional, qualified cases also favored a longer proposed broader text; their scores remain in the tables below.

This contradicts a rule that always calls shorter text broader. It does not prove that length, wording, or specificity cues never influence the model. The equal-token category pairs, Indian food/dal fry and art/photography, also favored the intended direction.

## One concrete wrong ordering

The fixed narrower mask was:

[V201](#v201) ⟦Today i Made big jar yogurt⟧

| Proposed broader mask | Angle — lower favors broader | Cosine — higher means more similar |
|---|---:|---:|
| [V547](#v547) ⟦In the kitchen as always a lot of work⟧ | 113.48° | 0.6191 |
| [V129](#v129) ⟦Off couple of days running errands⟧ | 111.00° | 0.6104 |

Making yogurt fits kitchen work more naturally than running errands, but the directional score prefers errands by 2.48°. Ordinary cosine gets this particular comparison right.

The kitchen-work pair still beats its own reversed direction. That demonstrates why getting pair direction right does not guarantee choosing an appropriate parent among alternatives.

The neighboring sourdough/kitchen-work comparison favored kitchen work over errands by only 0.89°. These are weaker observed separations than most category examples, not calibrated uncertainty or evidence of instability.

## Directional score versus cosine

Of the 28 fixed comparisons, the directional score agreed with the proposed relevant-parent ordering on 27; cosine agreed on 24. Those totals include the qualified examples, so they are descriptive agreement counts, not accuracy estimates.

The methods disagreed on five comparisons:

| Fixed narrower mask | Proposed relevant broader mask | Alternative | Directional score favored | Cosine favored |
|---|---|---|---|---|
| [V148](#v148) ⟦beets Vac sealed ready for the freezer⟧ | [V942](#v942) ⟦foodpreservation⟧ | [V147](#v147) ⟦This year’s beets raised bed⟧ | Proposed broader mask | Alternative |
| [V147](#v147) ⟦This year’s beets raised bed⟧ | [V255](#v255) ⟦food Growing your own skill⟧ | [V148](#v148) ⟦beets Vac sealed ready for the freezer⟧ | Proposed broader mask | Alternative |
| [V413](#v413) ⟦squirrels attacking tomatoes⟧ | [V389](#v389) ⟦Nature⟧ | [V380](#v380) ⟦cat⟧ | Proposed broader mask | Alternative |
| [V201](#v201) ⟦Today i Made big jar yogurt⟧ | [V547](#v547) ⟦In the kitchen as always a lot of work⟧ | [V129](#v129) ⟦Off couple of days running errands⟧ | Alternative | Proposed broader mask |
| [V793](#v793) ⟦coffee Roasting your own beans⟧ | [V381](#v381) ⟦Coffee⟧ | [V410](#v410) ⟦grind coffee beans⟧ | Proposed broader mask | Alternative |

Four disagreements favor the directional score; the yogurt comparison favors cosine. Thus the directional score adds useful information on these examples, but is not uniformly better.

This is not a comparison against SSE, nor a comparison of two different embedding models.

## A good ranking is not a universal acceptance rule

For coffee roasting, Coffee scores better as a broader subject than grinding coffee beans:

| Proposed broader mask | Narrower mask | Angle |
|---|---|---:|
| [V381](#v381) ⟦Coffee⟧ | [V793](#v793) ⟦coffee Roasting your own beans⟧ | 87.58° |
| [V410](#v410) ⟦grind coffee beans⟧ | [V793](#v793) ⟦coffee Roasting your own beans⟧ | 93.36° |

That ordering is useful. But the unsupported grinding → roasting relationship scores 93.36°, lower than the supported Coffee → grinding relationship at 94.97°. A single rule accepting every angle below one cutoff cannot retain that supported pair while rejecting the unsupported one.

This is a limitation of using the raw angle as a global yes/no rule. It does not invalidate the useful relative rankings or show that an algorithm using more than a cutoff cannot construct a hierarchy. No cutoff was fitted here.

## All fixed cases

A and B labels below refer to the exact displayed masks. Forward means proposed broader A → narrower B. Every alternative comparison holds B fixed.

The cases retain their original IDs after pre-score review. A08 was moved into the activity group, and A09 into the qualified group, before inference; neither move was motivated by a score.

### Clearer category relationships

| Case | Proposed broader A | Narrower B | A → B | B → A | Tokens A / B |
|---|---|---|---:|---:|---:|
| A01 | [V286](#v286) ⟦bread⟧ | [V359](#v359) ⟦chewy bagels⟧ | 88.26° | 152.66° | 3 / 4 |
| A02 | [V286](#v286) ⟦bread⟧ | [V719](#v719) ⟦Lacha Paratha⟧ | 99.51° | 153.05° | 3 / 6 |
| A03 | [V078](#v078) ⟦JapaneseFood⟧ | [V140](#v140) ⟦shrimp tempura sushi⟧ | 82.76° | 155.61° | 4 / 6 |
| A04 | [V722](#v722) ⟦india food⟧ | [V720](#v720) ⟦dal fry⟧ | 106.90° | 143.86° | 4 / 4 |
| A05 | [V722](#v722) ⟦india food⟧ | [V719](#v719) ⟦Lacha Paratha⟧ | 93.20° | 143.94° | 4 / 6 |
| A06 | [V942](#v942) ⟦foodpreservation⟧ | [V148](#v148) ⟦beets Vac sealed ready for the freezer⟧ | 84.28° | 164.10° | 4 / 9 |
| A07 | [V942](#v942) ⟦foodpreservation⟧ | [V096](#v096) ⟦today chicken stock I’ll pressure can⟧ | 97.75° | 153.71° | 4 / 11 |
| A10 | [V377](#v377) ⟦art⟧ | [V758](#v758) ⟦watercolourpainting⟧ | 89.16° | 162.13° | 3 / 5 |
| A11 | [V377](#v377) ⟦art⟧ | [V391](#v391) ⟦Photography⟧ | 107.46° | 147.71° | 3 / 3 |
| A12 | [V382](#v382) ⟦dog⟧ | [V212](#v212) ⟦begin switch my chihuahua raw diet⟧ | 89.02° | 162.98° | 3 / 8 |
| A13 | [V439](#v439) ⟦Literature⟧ | [V745](#v745) ⟦audio book drivel I gave up started new murder mystery⟧ | 94.55° | 156.79° | 3 / 13 |
| A14 | [V389](#v389) ⟦Nature⟧ | [V413](#v413) ⟦squirrels attacking tomatoes⟧ | 89.86° | 170.31° | 3 / 5 |
| A15 | [V942](#v942) ⟦foodpreservation⟧ | [V819](#v819) ⟦Century eggs called alkalized or preserved eggs⟧ | 89.00° | 157.98° | 4 / 10 |

| Case | Alternative proposed parent for the same B | Its angle | A's angle | Alternative cosine | A's cosine |
|---|---|---:|---:|---:|---:|
| A01 | [V579](#v579) ⟦cheesecake⟧ | 109.33° | 88.26° | 0.7524 | 0.8074 |
| A02 | [V579](#v579) ⟦cheesecake⟧ | 112.44° | 99.51° | 0.7294 | 0.7644 |
| A03 | [V722](#v722) ⟦india food⟧ | 98.94° | 82.76° | 0.5987 | 0.6828 |
| A04 | [V078](#v078) ⟦JapaneseFood⟧ | 113.72° | 106.90° | 0.7302 | 0.7758 |
| A05 | [V078](#v078) ⟦JapaneseFood⟧ | 105.63° | 93.20° | 0.7491 | 0.8218 |
| A06 | [V147](#v147) ⟦This year’s beets raised bed⟧ | 107.13° | 84.28° | 0.5228 | 0.2876 |
| A06 | [V096](#v096) ⟦today chicken stock I’ll pressure can⟧ | 105.35° | 84.28° | 0.2362 | 0.2876 |
| A07 | [V148](#v148) ⟦beets Vac sealed ready for the freezer⟧ | 143.55° | 97.75° | 0.2362 | 0.7164 |
| A10 | [V391](#v391) ⟦Photography⟧ | 111.61° | 89.16° | 0.8261 | 0.8618 |
| A11 | [V758](#v758) ⟦watercolourpainting⟧ | 149.38° | 107.46° | 0.8261 | 0.9525 |
| A12 | [V380](#v380) ⟦cat⟧ | 98.03° | 89.02° | 0.6197 | 0.6585 |
| A13 | [V437](#v437) ⟦Movies⟧ | 105.09° | 94.55° | 0.7100 | 0.7416 |
| A14 | [V380](#v380) ⟦cat⟧ | 92.74° | 89.86° | 0.5824 | 0.5808 |
| A15 | [V096](#v096) ⟦today chicken stock I’ll pressure can⟧ | 116.42° | 89.00° | 0.5302 | 0.6271 |

### Activity and fragmented-phrase tests

| Case | Proposed broader A | Narrower B | A → B | B → A | Tokens A / B |
|---|---|---|---:|---:|---:|
| A08 | [V255](#v255) ⟦food Growing your own skill⟧ | [V147](#v147) ⟦This year’s beets raised bed⟧ | 90.28° | 150.64° | 7 / 10 |
| B01 | [V547](#v547) ⟦In the kitchen as always a lot of work⟧ | [V108](#v108) ⟦Preparing sourdough bread⟧ | 116.28° | 125.85° | 11 / 5 |
| B02 | [V547](#v547) ⟦In the kitchen as always a lot of work⟧ | [V201](#v201) ⟦Today i Made big jar yogurt⟧ | 113.48° | 135.55° | 11 / 8 |
| B03 | [V711](#v711) ⟦right way to cook things⟧ | [V895](#v895) ⟦Cook spaghetti according to packet.⟧ | 100.60° | 138.67° | 7 / 8 |
| B04 | [V465](#v465) ⟦Education is the way forward⟧ | [V451](#v451) ⟦Bitcoin workshop⟧ | 116.82° | 136.52° | 7 / 4 |

| Case | Alternative proposed parent for the same B | Its angle | A's angle | Alternative cosine | A's cosine |
|---|---|---:|---:|---:|---:|
| A08 | [V148](#v148) ⟦beets Vac sealed ready for the freezer⟧ | 119.82° | 90.28° | 0.5228 | 0.4862 |
| B01 | [V129](#v129) ⟦Off couple of days running errands⟧ | 117.18° | 116.28° | 0.6927 | 0.7451 |
| B02 | [V129](#v129) ⟦Off couple of days running errands⟧ | 111.00° | 113.48° | 0.6104 | 0.6191 |
| B03 | [V359](#v359) ⟦chewy bagels⟧ | 119.72° | 100.60° | 0.5852 | 0.7353 |
| B04 | [V402](#v402) ⟦goals pizza restaurant St Michel de L'Attalaye accept Bitcoin haiti⟧ | 147.68° | 116.82° | 0.4986 | 0.7977 |

### Shared-word coffee controls

| Case | Proposed broader A | Narrower B | A → B | B → A | Tokens A / B |
|---|---|---|---:|---:|---:|
| D01 | [V381](#v381) ⟦Coffee⟧ | [V410](#v410) ⟦grind coffee beans⟧ | 94.97° | 138.60° | 3 / 5 |
| D02 | [V381](#v381) ⟦Coffee⟧ | [V793](#v793) ⟦coffee Roasting your own beans⟧ | 87.58° | 149.16° | 3 / 7 |

| Case | Alternative proposed parent for the same B | Its angle | A's angle | Alternative cosine | A's cosine |
|---|---|---:|---:|---:|---:|
| D01 | [V793](#v793) ⟦coffee Roasting your own beans⟧ | 129.51° | 94.97° | 0.8456 | 0.8705 |
| D02 | [V410](#v410) ⟦grind coffee beans⟧ | 93.36° | 87.58° | 0.8456 | 0.7671 |

### Qualified examples — no mandatory verdict

These interpretations were marked uncertain before scoring. In particular, good sleep and consistent bedtime need not have a mandatory broad-to-narrow order. Its reversed result is shown, not counted as a newly discovered clear failure.

| Case | Proposed broader A | Narrower B | A → B | B → A | Tokens A / B |
|---|---|---|---:|---:|---:|
| A09 | [V377](#v377) ⟦art⟧ | [V757](#v757) ⟦painting⟧ | 85.85° | 155.87° | 3 / 3 |
| C01 | [V465](#v465) ⟦Education is the way forward⟧ | [V466](#v466) ⟦Bitcoin Education way forward⟧ | 98.47° | 136.28° | 7 / 6 |
| C02 | [V606](#v606) ⟦Be positive⟧ | [V607](#v607) ⟦assume the best in people⟧ | 106.29° | 132.03° | 4 / 7 |
| C03 | [V633](#v633) ⟦Be kind⟧ | [V626](#v626) ⟦not speak bad about a person⟧ | 117.28° | 126.96° | 4 / 8 |
| C04 | [V598](#v598) ⟦Provide your body with a diverse diet⟧ | [V599](#v599) ⟦get in fiber and protein, omega 3⟧ | 111.38° | 123.74° | 9 / 10 |
| C05 | [V595](#v595) ⟦Get enough good sleep.⟧ | [V594](#v594) ⟦consitent bed time⟧ | 122.32° | 119.42° | 7 / 7 |
| C06 | [V638](#v638) ⟦Humans are very adapted to most environments.⟧ | [V640](#v640) ⟦Humans can eat many kinds of foods⟧ | 115.21° | 132.91° | 10 / 9 |

| Case | Alternative proposed parent for the same B | Its angle | A's angle | Alternative cosine | A's cosine |
|---|---|---:|---:|---:|---:|
| A09 | [V391](#v391) ⟦Photography⟧ | 117.08° | 85.85° | 0.8971 | 0.9327 |
| C01 | [V402](#v402) ⟦goals pizza restaurant St Michel de L'Attalaye accept Bitcoin haiti⟧ | 144.10° | 98.47° | 0.5035 | 0.8543 |
| C02 | [V626](#v626) ⟦not speak bad about a person⟧ | 117.45° | 106.29° | 0.8764 | 0.9096 |
| C03 | [V607](#v607) ⟦assume the best in people⟧ | 129.43° | 117.28° | 0.8764 | 0.9105 |
| C04 | [V597](#v597) ⟦Do not eat processed food⟧ | 117.75° | 111.38° | 0.7971 | 0.8403 |
| C05 | [V592](#v592) ⟦stop eating 3 hours before bed time⟧ | 132.09° | 122.32° | 0.8037 | 0.8502 |
| C06 | [V595](#v595) ⟦Get enough good sleep.⟧ | 121.70° | 115.21° | 0.7519 | 0.7957 |

## What remains uncertain

- Input scope and sense: “food Growing your own skill” requires interpreting broken fragment wording; bare “painting” is ambiguous without the rest of its note. Both were separated before scoring.
- The squirrel note says the squirrels have **given up** attacking tomatoes. Its mask drops the reversal. Its topical Nature result is not evidence about understanding negation.
- The qualified diet, sleep, kindness, and adaptation examples do not have a uniquely necessary parent direction. Favorable scores do not remove that qualification.
- Reused anchors, related food families, and several examples from one advice note limit independent coverage. There is no broad technical-domain evidence here.
- No paraphrase-invariance, corpus-wide parent ranking, membership threshold, hierarchy construction, transitivity, or navigation quality was tested.
- Directional angle order and distance-from-origin order are the same geometric evidence. They were not counted as separate confirmations.

The supported conclusion is that this released model carries useful broader–narrower topical information beyond literal shared words and a simple length rule on these masks. The results justify taking it seriously as a component; they do not yet specify how to construct or accept a whole hierarchy.

## Original notes with individual masks

Each entry shows the complete source note, with only that mask highlighted. The model received exactly the listed input, formed by joining the mask fragments with spaces. The complete note and generated subject descriptions were not model inputs.

### V286

N037. Exact model input: `bread`

> #foodstr
> Cranberry , rosemary , brown sugar and cinnamon sourdough ⟦bread⟧ , good lord it soo good https://image.nostr.build/cb6f56072bd4957a92c9f13a54444b0472c9ec071483b8dee2407469509d3ff0.jpg https://image.nostr.build/0b31d68d6792f6c7c54d5137a38880d68fdad1ccef9d760be02084141bb7a750.jpg https://image.nostr.build/ee8911a263955cf26e737a57d5abe0389a60623c89fcd97aa4855f43f584dfbd.jpg

### V359

N046. Exact model input: `chewy bagels`

> Turn pantry staples into ⟦chewy bagels⟧ 🥯
>
> Toppings : sesame, sea salt flakes and plain
>
> #foodstr
> https://m.primal.net/OHSR.jpg
> https://m.primal.net/OHSS.jpg

### V579

N067. Exact model input: `cheesecake`

> And my #Blueberry ⟦cheesecake⟧!  #foodstr #nostr https://image.nostr.build/ffde1f0a6109f806b66beae798e610fa7d4055a8ca4b21565160ecf84de16753.jpg

### V719

N078. Exact model input: `Lacha Paratha`

> Tonight's dinner - ⟦Lacha Paratha⟧ with dal fry
>
> #india #foodstr #foodchain
>
>
> https://image.nostr.build/33c2565fd8f964f4d60ed1d8e286972a538e3686ff9f00f18dfe51f64496d91d.jpg

### V078

N011. Exact model input: `JapaneseFood`

> https://www.alojapan.com/1198654/how-to-cook-this-mochi-bread-from-combini-need-recipe/ How to cook this “mochi bread” from combini? Need recipe. #food #⟦JapaneseFood⟧ So, I was in Japan this summer and among many-many new tasty things I found this: (picture from internet; google the word 生もちっ ハムチーズ ) https://preview.redd.it/3xrbmo1mmpie1.jpg?width=750&format=pjpg&auto=webp&s=5f062e504119cf9e7803a399320d908153ed824b >! https://www.youtube.com/watch?v=vp9lT2-ue0c!< Pretty common food for combini (Lawson if I remember co…
>
> https://media.channels.im/media_attachments/files/113/991/553/366/222/878/original/51c9a85d3eeb84dc.jpg

### V140

N020. Exact model input: `shrimp tempura sushi`

> Leftover BBQ chicken pizza from yesterday and ⟦shrimp tempura sushi⟧ for dinner
> #foodstr https://image.nostr.build/f091997302fbf0fe6dfdb2d2f4aee3acee67c14a78db24ad64c5b5a80990e2d6.jpg

### V722

N078. Exact model input: `india food`

> Tonight's dinner - Lacha Paratha with dal fry
>
> #⟦india⟧ #⟦food⟧str #foodchain
>
>
> https://image.nostr.build/33c2565fd8f964f4d60ed1d8e286972a538e3686ff9f00f18dfe51f64496d91d.jpg

### V720

N078. Exact model input: `dal fry`

> Tonight's dinner - Lacha Paratha with ⟦dal fry⟧
>
> #india #foodstr #foodchain
>
>
> https://image.nostr.build/33c2565fd8f964f4d60ed1d8e286972a538e3686ff9f00f18dfe51f64496d91d.jpg

### V942

N100. Exact model input: `foodpreservation`

> Alright today's been pretty solid.
>
> Picked up a sirloin strip sub primal for $10 a lb cut 15 steaks about 1.5-2" thickness.
>
> Trimmed about 3lb of fat for making tallow and about a quarter pound of some connective tissue and scrap meat for the dog.
>
>
> Saved the excess myoglobin to add in the dogs food and will put some some cold water and sunflower seeds for the chickens tomorrow.
>
> I finally got to use the new vacuum sealer and this one is much better than the food savers I've used in the past. I got this on a deal from Amazon for 30% off and love it after using it. If you need one check out the Nesco VS-12
>
> #beef #foodstr #⟦foodpreservation⟧ #cooking #steak #cooking #grownostr #prepping #plebchain #homesteading
>
>  https://image.nostr.build/270bbbc11299301ee5b4678883c5d48ab2f95eb13b1417093186ba855f4d90e5.jpg

### V148

N022. Exact model input: `beets Vac sealed ready for the freezer`

> This year’s ⟦beets⟧. ⟦Vac sealed⟧ and ⟦ready for the freezer⟧. Not too bad for a 4x4 raised bed. 5 meals of sides in a pinch. I am looking forward to having more garden space but this is good while we are still in a half acre lot in town. https://image.nostr.build/b4349cc1251dccf78990620ee851ad0ae449327da16ac31391e3e71fafdbe65c.jpg https://image.nostr.build/5c7e4ba19bb3c2e98cb57753679d33be2bbad3a07900afc86315c85f80bc46e4.jpg

### V147

N022. Exact model input: `This year’s beets raised bed`

> ⟦This year’s beets⟧. Vac sealed and ready for the freezer. Not too bad for a 4x4 ⟦raised bed⟧. 5 meals of sides in a pinch. I am looking forward to having more garden space but this is good while we are still in a half acre lot in town. https://image.nostr.build/b4349cc1251dccf78990620ee851ad0ae449327da16ac31391e3e71fafdbe65c.jpg https://image.nostr.build/5c7e4ba19bb3c2e98cb57753679d33be2bbad3a07900afc86315c85f80bc46e4.jpg

### V096

N013. Exact model input: `today chicken stock I’ll pressure can`

> Got the stock pots rolling ⟦today⟧ for a batch of ⟦chicken stock⟧. We save carcasses when we butcher and a couple of times a year do this. ⟦I’ll pressure can⟧ it and store in the pantry. Should get around 25 quarts with this batch.
> #grownostr
> #homesteading
> #foodsecurity
> #foodstr https://image.nostr.build/aead0ba70aa9ec698013666afe87bb76d74d9a19dbb7b93ceb0de953fa2e3386.jpg

### V255

N031. Exact model input: `food Growing your own skill`

> Supermarket ⟦food⟧ is packed with harmful pesticides and chemicals. ⟦Growing your own⟧ is a lost ⟦skill⟧.
>
> I love nostr:npub1rcf8y4dfygz6jjwsdml06wmrg4sfn7cwh25p68w5myj83npjxcgslj6e2p ‘s allotment efforts—fried homegrown tomatoes for brekkie are the best!  🍅
> https://m.primal.net/KRKC.jpg

### V377

N048. Exact model input: `art`

> #Come in! We will be happy: https://linuxtosha.ru/
> “How can we hope that peace and prosperity will reign on earth if our bodies are living graves in which killed animals are buried?” Lev Nikolaevich Tolstoy
> https://m.primal.net/IADr.png
> #⟦art⟧ #alby #bitcoin #cat #Coffee #dog #dream #Gentoo #grownostr #Linux #memes #Nature #nostr #Photography #pleb #plebchain #zap #zapathon

### V757

N080. Exact model input: `painting`

> Wednesday, 20th November 2024 - Cherries
>
> Wow what a beautiful morning. Stunning sunrise over a frosty garden. That got me out of bed - plus the need for tea and a wee. Yes and in that order.
>
> Our chickens are laying an egg a day. Having four hens that is a lot of eggs. My guests had scrambled eggs for breakfast and I soft boiled nine eggs for my lunch over the next few days. The clutch of eggs is receding. Michael Mosley said that a boiled egg is a good alternative to a packet of crisps!!!! Can't quite see the similarity but I have plenty of crisp substitutes in the fridge.
>
> The new audio book I had was like listening to a load of fluff. Total meaningless drivel. I gave up and have started a new murder mystery which is much more entertaining. I needed it while I was printing the last of our Christmas cards.
>
> Tim came home from Brussels with a gift of a bottle of gin, a bottle of Kreik and a bar of dark chocolate. Week 3 Day 3 I have chosen fruit for Kalie Graves challenge. My bottle of Kreik is cherry flavoured.
> -
> -
> -
> #kgaweekday #katesconnectedpostcardproject #apaintingaday #katerundell #artblog #dailyart #instaart #instaartist #watercolour #artoninstagram #artofinstagram #⟦painting⟧ #watercolourpainting #blogger #dailyblogger #winsorandnewton #instadaily #danielsmithwatercolors https://nostrcheck.me/media/18d26089c0617d1b68bd08dfef065cf5eb5316a97eee1c0014d079ed3a6bc815/654867f61c247a385f166f7ba177be4382829feb6c77bfb73131fd7dfa849ce5.webp

### V391

N048. Exact model input: `Photography`

> #Come in! We will be happy: https://linuxtosha.ru/
> “How can we hope that peace and prosperity will reign on earth if our bodies are living graves in which killed animals are buried?” Lev Nikolaevich Tolstoy
> https://m.primal.net/IADr.png
> #art #alby #bitcoin #cat #Coffee #dog #dream #Gentoo #grownostr #Linux #memes #Nature #nostr #⟦Photography⟧ #pleb #plebchain #zap #zapathon

### V758

N080. Exact model input: `watercolourpainting`

> Wednesday, 20th November 2024 - Cherries
>
> Wow what a beautiful morning. Stunning sunrise over a frosty garden. That got me out of bed - plus the need for tea and a wee. Yes and in that order.
>
> Our chickens are laying an egg a day. Having four hens that is a lot of eggs. My guests had scrambled eggs for breakfast and I soft boiled nine eggs for my lunch over the next few days. The clutch of eggs is receding. Michael Mosley said that a boiled egg is a good alternative to a packet of crisps!!!! Can't quite see the similarity but I have plenty of crisp substitutes in the fridge.
>
> The new audio book I had was like listening to a load of fluff. Total meaningless drivel. I gave up and have started a new murder mystery which is much more entertaining. I needed it while I was printing the last of our Christmas cards.
>
> Tim came home from Brussels with a gift of a bottle of gin, a bottle of Kreik and a bar of dark chocolate. Week 3 Day 3 I have chosen fruit for Kalie Graves challenge. My bottle of Kreik is cherry flavoured.
> -
> -
> -
> #kgaweekday #katesconnectedpostcardproject #apaintingaday #katerundell #artblog #dailyart #instaart #instaartist #watercolour #artoninstagram #artofinstagram #painting #⟦watercolourpainting⟧ #blogger #dailyblogger #winsorandnewton #instadaily #danielsmithwatercolors https://nostrcheck.me/media/18d26089c0617d1b68bd08dfef065cf5eb5316a97eee1c0014d079ed3a6bc815/654867f61c247a385f166f7ba177be4382829feb6c77bfb73131fd7dfa849ce5.webp

### V382

N048. Exact model input: `dog`

> #Come in! We will be happy: https://linuxtosha.ru/
> “How can we hope that peace and prosperity will reign on earth if our bodies are living graves in which killed animals are buried?” Lev Nikolaevich Tolstoy
> https://m.primal.net/IADr.png
> #art #alby #bitcoin #cat #Coffee #⟦dog⟧ #dream #Gentoo #grownostr #Linux #memes #Nature #nostr #Photography #pleb #plebchain #zap #zapathon

### V212

N026. Exact model input: `begin switch my chihuahua raw diet`

> Today i have:
> —Acquired, roasted and prepared 12 pounds or more of tomato’s to make salsa.
> —Made a big jar of yogurt
> —acquired 3 rotisserie chickens that were marked down
> —bagged the chicken meat
> —made over a half gallon of chicken stock from the bones,
> —cleaned so many dishes from all the dishes i used doing all the above.
> —also received a big bag of raw meat to break down into smaller bags, as i ⟦begin⟧ to ⟦switch my chihuahua⟧ to ⟦raw diet⟧
>
> I could post a few jars of salsa on nostr to see if I could sell a few jars.
> (Pictured is a jar from last year that i just opened :)
> #grownostr

### V380

N048. Exact model input: `cat`

> #Come in! We will be happy: https://linuxtosha.ru/
> “How can we hope that peace and prosperity will reign on earth if our bodies are living graves in which killed animals are buried?” Lev Nikolaevich Tolstoy
> https://m.primal.net/IADr.png
> #art #alby #bitcoin #⟦cat⟧ #Coffee #dog #dream #Gentoo #grownostr #Linux #memes #Nature #nostr #Photography #pleb #plebchain #zap #zapathon

### V439

N054. Exact model input: `Literature`

>
>                         🌊 SURF 'N TURF 🏝️
>                   -THE BITCOIN ISLAND LIFE-
> https://image.nostr.build/d9f3de673feef75afe8905f3484ad56a8108ebda0f8889ec07df46ef78bbfd90.jpg
>      Sitting,waiting, wishing......Santa didn't show!
> https://image.nostr.build/e47dc55b8c67ade6cf163f80a1e41bef7e4af914de4d8c765ee044fd549e934d.jpg
> So, went and had lunch instead, always good food and a good view here at the bay.
> https://image.nostr.build/46ebd9afe798f652924017bf2fc23f76c2c72bc9c5610b6a1a30b41b3de179cf.jpg
> Pura Vida 🏝️
> https://image.nostr.build/d6b881c3cc8a887780de6a05487266b649538b22aee01274daf847dfee55502f.jpg
> https://image.nostr.build/e8ed1661f18346f342ce0d6ab14095de2ceccf3c7323745cc63876a5a401f8aa.jpg
>                  Credits Goes to the respective
>                     Author ✍️/ Photographer📸
>                                     🐇 🕳️
> #Bitcoin #Satoshis #Freedom #Apocalypse          #Music   #Movies #Philosophy  #⟦Literature⟧
>                                  #dogstr #islands

### V745

N080. Exact model input: `audio book drivel I gave up started new murder mystery`

> Wednesday, 20th November 2024 - Cherries
>
> Wow what a beautiful morning. Stunning sunrise over a frosty garden. That got me out of bed - plus the need for tea and a wee. Yes and in that order.
>
> Our chickens are laying an egg a day. Having four hens that is a lot of eggs. My guests had scrambled eggs for breakfast and I soft boiled nine eggs for my lunch over the next few days. The clutch of eggs is receding. Michael Mosley said that a boiled egg is a good alternative to a packet of crisps!!!! Can't quite see the similarity but I have plenty of crisp substitutes in the fridge.
>
> The new ⟦audio book⟧ I had was like listening to a load of fluff. Total meaningless ⟦drivel⟧. ⟦I gave up⟧ and have ⟦started⟧ a ⟦new murder mystery⟧ which is much more entertaining. I needed it while I was printing the last of our Christmas cards.
>
> Tim came home from Brussels with a gift of a bottle of gin, a bottle of Kreik and a bar of dark chocolate. Week 3 Day 3 I have chosen fruit for Kalie Graves challenge. My bottle of Kreik is cherry flavoured.
> -
> -
> -
> #kgaweekday #katesconnectedpostcardproject #apaintingaday #katerundell #artblog #dailyart #instaart #instaartist #watercolour #artoninstagram #artofinstagram #painting #watercolourpainting #blogger #dailyblogger #winsorandnewton #instadaily #danielsmithwatercolors https://nostrcheck.me/media/18d26089c0617d1b68bd08dfef065cf5eb5316a97eee1c0014d079ed3a6bc815/654867f61c247a385f166f7ba177be4382829feb6c77bfb73131fd7dfa849ce5.webp

### V437

N054. Exact model input: `Movies`

>
>                         🌊 SURF 'N TURF 🏝️
>                   -THE BITCOIN ISLAND LIFE-
> https://image.nostr.build/d9f3de673feef75afe8905f3484ad56a8108ebda0f8889ec07df46ef78bbfd90.jpg
>      Sitting,waiting, wishing......Santa didn't show!
> https://image.nostr.build/e47dc55b8c67ade6cf163f80a1e41bef7e4af914de4d8c765ee044fd549e934d.jpg
> So, went and had lunch instead, always good food and a good view here at the bay.
> https://image.nostr.build/46ebd9afe798f652924017bf2fc23f76c2c72bc9c5610b6a1a30b41b3de179cf.jpg
> Pura Vida 🏝️
> https://image.nostr.build/d6b881c3cc8a887780de6a05487266b649538b22aee01274daf847dfee55502f.jpg
> https://image.nostr.build/e8ed1661f18346f342ce0d6ab14095de2ceccf3c7323745cc63876a5a401f8aa.jpg
>                  Credits Goes to the respective
>                     Author ✍️/ Photographer📸
>                                     🐇 🕳️
> #Bitcoin #Satoshis #Freedom #Apocalypse          #Music   #⟦Movies⟧ #Philosophy  #Literature
>                                  #dogstr #islands

### V389

N048. Exact model input: `Nature`

> #Come in! We will be happy: https://linuxtosha.ru/
> “How can we hope that peace and prosperity will reign on earth if our bodies are living graves in which killed animals are buried?” Lev Nikolaevich Tolstoy
> https://m.primal.net/IADr.png
> #art #alby #bitcoin #cat #Coffee #dog #dream #Gentoo #grownostr #Linux #memes #⟦Nature⟧ #nostr #Photography #pleb #plebchain #zap #zapathon

### V413

N053. Exact model input: `squirrels attacking tomatoes`

> Even the ⟦squirrels⟧ have given up ⟦attacking⟧ the ⟦tomatoes⟧. We have been overrun. Send halp. #foodstr https://image.nostr.build/2338cae17437e1bbbc1e87d30746987a77ccae9d551433e63c6c1d008dc6f176.jpg

### V819

N091. Exact model input: `Century eggs called alkalized or preserved eggs`

> ⟦Century eggs⟧, also ⟦called alkalized or preserved eggs⟧, are a Chinese culinary delicacy made by preserving duck, chicken, or quail eggs in a mixture of clay, ash, salt, quicklime, and rice hulls for several weeks to several months.
>  https://t.co/H3rYBZBKd3 https://video.twimg.com/ext_tw_video/1771890392331653120/pu/vid/avc1/720x1280/ECtlOiuN11A8UeTv.mp4?tag=12

### V547

N064. Exact model input: `In the kitchen as always a lot of work`

> GM! 💜🫂 How are you today?
> It's now after Christmas, things are slowly getting back to normal and I'm starting to slow down. ⟦In the kitchen as always a lot of work⟧ but I like it 😂😂
> From all this I even forgot to take photos 🙈Today meat dumplings, so out of sentiment....
> #food #foodstr #plebchain https://image.nostr.build/3fb21ce7646872c6b17a873a3849f902dca94e24079fdcb5d99db096a3056653.jpg https://image.nostr.build/d63ddf6c600431c95faa2ce795c99d7653afa1c300d2f0a1a5cb922a1b2ed60d.jpg

### V108

N015. Exact model input: `Preparing sourdough bread`

> How to spend some moments: ⟦Preparing sourdough bread⟧.
>
>  https://z428.micro.blog/uploads/2024/abcd7a949e.jpg https://z428.micro.blog/uploads/2024/abcd7a949e.jpg

### V129

N018. Exact model input: `Off couple of days running errands`

> Good...er...Afternoon Nostr!
>
> ⟦Off⟧ for a ⟦couple of days⟧ ⟦running⟧ some ⟦errands⟧...but even on those days I enjoyed a morning coffee!
>
> Will be back in the coffeechain tomorrow!
>

### V201

N026. Exact model input: `Today i Made big jar yogurt`

> ⟦Today i⟧ have:
> —Acquired, roasted and prepared 12 pounds or more of tomato’s to make salsa.
> —⟦Made⟧ a ⟦big jar⟧ of ⟦yogurt⟧
> —acquired 3 rotisserie chickens that were marked down
> —bagged the chicken meat
> —made over a half gallon of chicken stock from the bones,
> —cleaned so many dishes from all the dishes i used doing all the above.
> —also received a big bag of raw meat to break down into smaller bags, as i begin to switch my chihuahua to raw diet
>
> I could post a few jars of salsa on nostr to see if I could sell a few jars.
> (Pictured is a jar from last year that i just opened :)
> #grownostr

### V711

N077. Exact model input: `right way to cook things`

> Arguing about the ⟦right way to cook things⟧ is the wholesome controversial content I like to see on nostr

### V895

N096. Exact model input: `Cook spaghetti according to packet.`

> My #neverfail Spaghetti Bolognaise recipe that feeds 5.
> 1x med onion
> 1x celery stick
> 1x med carrot
> 1-2 cloves garlic
> bunch fresh basil
> 500g ground beef
> 1x 400g tin chopped tomatoes
> 1x 400g tin tomato purée
> Salt and pepper to taste
> 2 Tbls olive oil
> 500g dried spaghetti
>
> In a large pan on medium heat, sauté the finely chopped onion, celery and carrot in the olive oil. After a few minutes add the crushed garlic. Once onions are clear, push to side and add ground beef. Gently fry beef without browning. Once beef is all the same colour add both tins of tomatoes plus 1 tin of water. Add chopped fresh basil leaves. Mix all ingredients thoroughly. Simmer on low heat for 45min-1hr.
> ⟦Cook spaghetti according to packet.⟧
> #food #recipe #easy #spaghetti #bolognaise #tomato #dinner
>
> https://m.primal.net/ODru.mov

### V465

N055. Exact model input: `Education is the way forward`

> Knowledge must be shared, so must joy, and if there's something sacred that breaks all barriers, it's sharing a meal. After the #Bitcoin workshop conducted by nostr:nprofile1qqsqkp32f9m2xp2snj8xtqac4plm0ah3rjjy9dc3fgdz35gk30gswrqpzemhxue69uhhyetvv9ujuurjd9kkzmpwdejhgqgjwaehxw309ac82unsd3jhqct89ejhxqgnwaehxw309aex2mrp09skymr99ehhyecaxwfrt https://image.nostr.build/4ab2ef1dd6512a4ba68fa38d1fb96ea043a5cabb1e0fcd17fbca8d06d1c408ea.jpg c, the humble people of Amambay( a rural área of Paraguay )The real plebs, The guarani-speaking peasants, slaughtered a pig. As a rule, the poorest are often the most generous. ⟦Education is the way forward⟧ 🇵🇾🧡 https://image.nostr.build/d41cbe864aa9bf691a5435cb3c9364520cd7900e5c5e6a2f6599187f3c3c74e1.jpg

### V451

N055. Exact model input: `Bitcoin workshop`

> Knowledge must be shared, so must joy, and if there's something sacred that breaks all barriers, it's sharing a meal. After the #⟦Bitcoin workshop⟧ conducted by nostr:nprofile1qqsqkp32f9m2xp2snj8xtqac4plm0ah3rjjy9dc3fgdz35gk30gswrqpzemhxue69uhhyetvv9ujuurjd9kkzmpwdejhgqgjwaehxw309ac82unsd3jhqct89ejhxqgnwaehxw309aex2mrp09skymr99ehhyecaxwfrt https://image.nostr.build/4ab2ef1dd6512a4ba68fa38d1fb96ea043a5cabb1e0fcd17fbca8d06d1c408ea.jpg c, the humble people of Amambay( a rural área of Paraguay )The real plebs, The guarani-speaking peasants, slaughtered a pig. As a rule, the poorest are often the most generous. Education is the way forward 🇵🇾🧡 https://image.nostr.build/d41cbe864aa9bf691a5435cb3c9364520cd7900e5c5e6a2f6599187f3c3c74e1.jpg

### V402

N050. Exact model input: `goals pizza restaurant St Michel de L'Attalaye accept Bitcoin haiti`

> Happy Bitcoin pizza day! While we currently have no ways to get pizza, one of our ⟦goals⟧ by next year is to have ONE ⟦pizza restaurant⟧ in our town of ⟦St Michel de L'Attalaye⟧ and they WILL ⟦accept Bitcoin⟧! #⟦haiti⟧
>
> https://m.primal.net/IKDD.jpg
>

### V466

N055. Exact model input: `Bitcoin Education way forward`

> Knowledge must be shared, so must joy, and if there's something sacred that breaks all barriers, it's sharing a meal. After the #⟦Bitcoin⟧ workshop conducted by nostr:nprofile1qqsqkp32f9m2xp2snj8xtqac4plm0ah3rjjy9dc3fgdz35gk30gswrqpzemhxue69uhhyetvv9ujuurjd9kkzmpwdejhgqgjwaehxw309ac82unsd3jhqct89ejhxqgnwaehxw309aex2mrp09skymr99ehhyecaxwfrt https://image.nostr.build/4ab2ef1dd6512a4ba68fa38d1fb96ea043a5cabb1e0fcd17fbca8d06d1c408ea.jpg c, the humble people of Amambay( a rural área of Paraguay )The real plebs, The guarani-speaking peasants, slaughtered a pig. As a rule, the poorest are often the most generous. ⟦Education⟧ is the ⟦way forward⟧ 🇵🇾🧡 https://image.nostr.build/d41cbe864aa9bf691a5435cb3c9364520cd7900e5c5e6a2f6599187f3c3c74e1.jpg

### V606

N069. Exact model input: `Be positive`

> 1. Do not use your phone after 8pm.
> 2. Fast 18 hours a day, stop eating 3 hours before bed time.
> 3. Be consitent with your bed time. Get enough good sleep.
> 4. Do not eat processed food. Provide your body with a diverse diet, make sure to get in fiber and protein, omega 3.
> 5. Find a way to slow things down, change your life if you have unhealthy stress.
> 6. Get out of the house, especially in the morning.
> 7. Focus on community / family.
> 8. ⟦Be positive⟧, assume the best in people. Be consequent if you been proven otherwise.
> 9. Be good, not for others sake, but for your own peace. Even if that means you will face reprecussion.
> 10. If you are priveleged, be greatful for what you have. Stop admiring the life of others. You are already happy, find your happiness inside of you.
> 11.  Learn when to speak…accept that not everything needs to be said, even if this means things do not go your way.
> 12. Work out in zone 2 as much as you can. Think of walking instead of biking, or biking instead of the car.
> 13. Try to read, especially before bed time.
> 14. Do not speak bad about a person.
> 15. Find purpose and pursue that purpose, without making your purpose the process of finding purpose.
> 16. Do not grant someone more priveleges based on status, or similar, but based on kindness and goodness.
> 17. Be kind!
> 18. Accept that you never know everything, be open to different views.
> 19. …
>
> What would you add?

### V607

N069. Exact model input: `assume the best in people`

> 1. Do not use your phone after 8pm.
> 2. Fast 18 hours a day, stop eating 3 hours before bed time.
> 3. Be consitent with your bed time. Get enough good sleep.
> 4. Do not eat processed food. Provide your body with a diverse diet, make sure to get in fiber and protein, omega 3.
> 5. Find a way to slow things down, change your life if you have unhealthy stress.
> 6. Get out of the house, especially in the morning.
> 7. Focus on community / family.
> 8. Be positive, ⟦assume the best in people⟧. Be consequent if you been proven otherwise.
> 9. Be good, not for others sake, but for your own peace. Even if that means you will face reprecussion.
> 10. If you are priveleged, be greatful for what you have. Stop admiring the life of others. You are already happy, find your happiness inside of you.
> 11.  Learn when to speak…accept that not everything needs to be said, even if this means things do not go your way.
> 12. Work out in zone 2 as much as you can. Think of walking instead of biking, or biking instead of the car.
> 13. Try to read, especially before bed time.
> 14. Do not speak bad about a person.
> 15. Find purpose and pursue that purpose, without making your purpose the process of finding purpose.
> 16. Do not grant someone more priveleges based on status, or similar, but based on kindness and goodness.
> 17. Be kind!
> 18. Accept that you never know everything, be open to different views.
> 19. …
>
> What would you add?

### V626

N069. Exact model input: `not speak bad about a person`

> 1. Do not use your phone after 8pm.
> 2. Fast 18 hours a day, stop eating 3 hours before bed time.
> 3. Be consitent with your bed time. Get enough good sleep.
> 4. Do not eat processed food. Provide your body with a diverse diet, make sure to get in fiber and protein, omega 3.
> 5. Find a way to slow things down, change your life if you have unhealthy stress.
> 6. Get out of the house, especially in the morning.
> 7. Focus on community / family.
> 8. Be positive, assume the best in people. Be consequent if you been proven otherwise.
> 9. Be good, not for others sake, but for your own peace. Even if that means you will face reprecussion.
> 10. If you are priveleged, be greatful for what you have. Stop admiring the life of others. You are already happy, find your happiness inside of you.
> 11.  Learn when to speak…accept that not everything needs to be said, even if this means things do not go your way.
> 12. Work out in zone 2 as much as you can. Think of walking instead of biking, or biking instead of the car.
> 13. Try to read, especially before bed time.
> 14. Do ⟦not speak bad about a person⟧.
> 15. Find purpose and pursue that purpose, without making your purpose the process of finding purpose.
> 16. Do not grant someone more priveleges based on status, or similar, but based on kindness and goodness.
> 17. Be kind!
> 18. Accept that you never know everything, be open to different views.
> 19. …
>
> What would you add?

### V633

N069. Exact model input: `Be kind`

> 1. Do not use your phone after 8pm.
> 2. Fast 18 hours a day, stop eating 3 hours before bed time.
> 3. Be consitent with your bed time. Get enough good sleep.
> 4. Do not eat processed food. Provide your body with a diverse diet, make sure to get in fiber and protein, omega 3.
> 5. Find a way to slow things down, change your life if you have unhealthy stress.
> 6. Get out of the house, especially in the morning.
> 7. Focus on community / family.
> 8. Be positive, assume the best in people. Be consequent if you been proven otherwise.
> 9. Be good, not for others sake, but for your own peace. Even if that means you will face reprecussion.
> 10. If you are priveleged, be greatful for what you have. Stop admiring the life of others. You are already happy, find your happiness inside of you.
> 11.  Learn when to speak…accept that not everything needs to be said, even if this means things do not go your way.
> 12. Work out in zone 2 as much as you can. Think of walking instead of biking, or biking instead of the car.
> 13. Try to read, especially before bed time.
> 14. Do not speak bad about a person.
> 15. Find purpose and pursue that purpose, without making your purpose the process of finding purpose.
> 16. Do not grant someone more priveleges based on status, or similar, but based on kindness and goodness.
> 17. ⟦Be kind⟧!
> 18. Accept that you never know everything, be open to different views.
> 19. …
>
> What would you add?

### V598

N069. Exact model input: `Provide your body with a diverse diet`

> 1. Do not use your phone after 8pm.
> 2. Fast 18 hours a day, stop eating 3 hours before bed time.
> 3. Be consitent with your bed time. Get enough good sleep.
> 4. Do not eat processed food. ⟦Provide your body with a diverse diet⟧, make sure to get in fiber and protein, omega 3.
> 5. Find a way to slow things down, change your life if you have unhealthy stress.
> 6. Get out of the house, especially in the morning.
> 7. Focus on community / family.
> 8. Be positive, assume the best in people. Be consequent if you been proven otherwise.
> 9. Be good, not for others sake, but for your own peace. Even if that means you will face reprecussion.
> 10. If you are priveleged, be greatful for what you have. Stop admiring the life of others. You are already happy, find your happiness inside of you.
> 11.  Learn when to speak…accept that not everything needs to be said, even if this means things do not go your way.
> 12. Work out in zone 2 as much as you can. Think of walking instead of biking, or biking instead of the car.
> 13. Try to read, especially before bed time.
> 14. Do not speak bad about a person.
> 15. Find purpose and pursue that purpose, without making your purpose the process of finding purpose.
> 16. Do not grant someone more priveleges based on status, or similar, but based on kindness and goodness.
> 17. Be kind!
> 18. Accept that you never know everything, be open to different views.
> 19. …
>
> What would you add?

### V599

N069. Exact model input: `get in fiber and protein, omega 3`

> 1. Do not use your phone after 8pm.
> 2. Fast 18 hours a day, stop eating 3 hours before bed time.
> 3. Be consitent with your bed time. Get enough good sleep.
> 4. Do not eat processed food. Provide your body with a diverse diet, make sure to ⟦get in fiber and protein, omega 3⟧.
> 5. Find a way to slow things down, change your life if you have unhealthy stress.
> 6. Get out of the house, especially in the morning.
> 7. Focus on community / family.
> 8. Be positive, assume the best in people. Be consequent if you been proven otherwise.
> 9. Be good, not for others sake, but for your own peace. Even if that means you will face reprecussion.
> 10. If you are priveleged, be greatful for what you have. Stop admiring the life of others. You are already happy, find your happiness inside of you.
> 11.  Learn when to speak…accept that not everything needs to be said, even if this means things do not go your way.
> 12. Work out in zone 2 as much as you can. Think of walking instead of biking, or biking instead of the car.
> 13. Try to read, especially before bed time.
> 14. Do not speak bad about a person.
> 15. Find purpose and pursue that purpose, without making your purpose the process of finding purpose.
> 16. Do not grant someone more priveleges based on status, or similar, but based on kindness and goodness.
> 17. Be kind!
> 18. Accept that you never know everything, be open to different views.
> 19. …
>
> What would you add?

### V597

N069. Exact model input: `Do not eat processed food`

> 1. Do not use your phone after 8pm.
> 2. Fast 18 hours a day, stop eating 3 hours before bed time.
> 3. Be consitent with your bed time. Get enough good sleep.
> 4. ⟦Do not eat processed food⟧. Provide your body with a diverse diet, make sure to get in fiber and protein, omega 3.
> 5. Find a way to slow things down, change your life if you have unhealthy stress.
> 6. Get out of the house, especially in the morning.
> 7. Focus on community / family.
> 8. Be positive, assume the best in people. Be consequent if you been proven otherwise.
> 9. Be good, not for others sake, but for your own peace. Even if that means you will face reprecussion.
> 10. If you are priveleged, be greatful for what you have. Stop admiring the life of others. You are already happy, find your happiness inside of you.
> 11.  Learn when to speak…accept that not everything needs to be said, even if this means things do not go your way.
> 12. Work out in zone 2 as much as you can. Think of walking instead of biking, or biking instead of the car.
> 13. Try to read, especially before bed time.
> 14. Do not speak bad about a person.
> 15. Find purpose and pursue that purpose, without making your purpose the process of finding purpose.
> 16. Do not grant someone more priveleges based on status, or similar, but based on kindness and goodness.
> 17. Be kind!
> 18. Accept that you never know everything, be open to different views.
> 19. …
>
> What would you add?

### V595

N069. Exact model input: `Get enough good sleep.`

> 1. Do not use your phone after 8pm.
> 2. Fast 18 hours a day, stop eating 3 hours before bed time.
> 3. Be consitent with your bed time. ⟦Get enough good sleep.⟧
> 4. Do not eat processed food. Provide your body with a diverse diet, make sure to get in fiber and protein, omega 3.
> 5. Find a way to slow things down, change your life if you have unhealthy stress.
> 6. Get out of the house, especially in the morning.
> 7. Focus on community / family.
> 8. Be positive, assume the best in people. Be consequent if you been proven otherwise.
> 9. Be good, not for others sake, but for your own peace. Even if that means you will face reprecussion.
> 10. If you are priveleged, be greatful for what you have. Stop admiring the life of others. You are already happy, find your happiness inside of you.
> 11.  Learn when to speak…accept that not everything needs to be said, even if this means things do not go your way.
> 12. Work out in zone 2 as much as you can. Think of walking instead of biking, or biking instead of the car.
> 13. Try to read, especially before bed time.
> 14. Do not speak bad about a person.
> 15. Find purpose and pursue that purpose, without making your purpose the process of finding purpose.
> 16. Do not grant someone more priveleges based on status, or similar, but based on kindness and goodness.
> 17. Be kind!
> 18. Accept that you never know everything, be open to different views.
> 19. …
>
> What would you add?

### V594

N069. Exact model input: `consitent bed time`

> 1. Do not use your phone after 8pm.
> 2. Fast 18 hours a day, stop eating 3 hours before bed time.
> 3. Be ⟦consitent⟧ with your ⟦bed time⟧. Get enough good sleep.
> 4. Do not eat processed food. Provide your body with a diverse diet, make sure to get in fiber and protein, omega 3.
> 5. Find a way to slow things down, change your life if you have unhealthy stress.
> 6. Get out of the house, especially in the morning.
> 7. Focus on community / family.
> 8. Be positive, assume the best in people. Be consequent if you been proven otherwise.
> 9. Be good, not for others sake, but for your own peace. Even if that means you will face reprecussion.
> 10. If you are priveleged, be greatful for what you have. Stop admiring the life of others. You are already happy, find your happiness inside of you.
> 11.  Learn when to speak…accept that not everything needs to be said, even if this means things do not go your way.
> 12. Work out in zone 2 as much as you can. Think of walking instead of biking, or biking instead of the car.
> 13. Try to read, especially before bed time.
> 14. Do not speak bad about a person.
> 15. Find purpose and pursue that purpose, without making your purpose the process of finding purpose.
> 16. Do not grant someone more priveleges based on status, or similar, but based on kindness and goodness.
> 17. Be kind!
> 18. Accept that you never know everything, be open to different views.
> 19. …
>
> What would you add?

### V592

N069. Exact model input: `stop eating 3 hours before bed time`

> 1. Do not use your phone after 8pm.
> 2. Fast 18 hours a day, ⟦stop eating 3 hours before bed time⟧.
> 3. Be consitent with your bed time. Get enough good sleep.
> 4. Do not eat processed food. Provide your body with a diverse diet, make sure to get in fiber and protein, omega 3.
> 5. Find a way to slow things down, change your life if you have unhealthy stress.
> 6. Get out of the house, especially in the morning.
> 7. Focus on community / family.
> 8. Be positive, assume the best in people. Be consequent if you been proven otherwise.
> 9. Be good, not for others sake, but for your own peace. Even if that means you will face reprecussion.
> 10. If you are priveleged, be greatful for what you have. Stop admiring the life of others. You are already happy, find your happiness inside of you.
> 11.  Learn when to speak…accept that not everything needs to be said, even if this means things do not go your way.
> 12. Work out in zone 2 as much as you can. Think of walking instead of biking, or biking instead of the car.
> 13. Try to read, especially before bed time.
> 14. Do not speak bad about a person.
> 15. Find purpose and pursue that purpose, without making your purpose the process of finding purpose.
> 16. Do not grant someone more priveleges based on status, or similar, but based on kindness and goodness.
> 17. Be kind!
> 18. Accept that you never know everything, be open to different views.
> 19. …
>
> What would you add?

### V638

N070. Exact model input: `Humans are very adapted to most environments.`

> ⟦Humans are very adapted to most environments.⟧ We can survive in many different conditions. We can eat many many kinds of foods. But there are better conditions and better foods.
>
> While to survive we can eat anything, it doesn't mean we should eat crap when better food is available.

### V640

N070. Exact model input: `Humans can eat many kinds of foods`

> ⟦Humans⟧ are very adapted to most environments. We can survive in many different conditions. We ⟦can eat⟧ many ⟦many kinds of foods⟧. But there are better conditions and better foods.
>
> While to survive we can eat anything, it doesn't mean we should eat crap when better food is available.

### V381

N048. Exact model input: `Coffee`

> #Come in! We will be happy: https://linuxtosha.ru/
> “How can we hope that peace and prosperity will reign on earth if our bodies are living graves in which killed animals are buried?” Lev Nikolaevich Tolstoy
> https://m.primal.net/IADr.png
> #art #alby #bitcoin #cat #⟦Coffee⟧ #dog #dream #Gentoo #grownostr #Linux #memes #Nature #nostr #Photography #pleb #plebchain #zap #zapathon

### V410

N052. Exact model input: `grind coffee beans`

> Rise and ⟦grind coffee beans⟧

### V793

N086. Exact model input: `coffee Roasting your own beans`

> You’ve had coffee. But have you had your ⟦coffee⟧?”
> https://blossom.primal.net/1379b90996b8ecb2f4fdef6756fd61c4ab964fa19f9e1505950e10a4d97640dd.jpg
> ⟦Roasting your own beans⟧ means discovering a taste profile that’s uniquely yours. It’s a personal journey that no bag of pre-roasted coffee can replicate.
>
> Sipping  @ #coffeechain
>
> #HotTake ☕

## Artifacts and verification

[Plan](RESULTS.md#hrc02-study-design) · [Frozen judgments and comparisons](fixture.json) · Complete case analysis (`analysis.json`) · All 2,601 scores (`scores.json`) · Vectors (`embeddings.json`) · Exact inputs (`inputs.json`) · Configuration and hashes (`config.json`) · Verification (`verification.json`).

The checkpoint, source artifacts, tokenizer, scoring implementation, two CPU threads, float32 precision, and batches of four match HRC01. Nine unchanged runner tests pass. All original masks and ranges verify; all 2,601 scores replay exactly.

An independent invocation using the full author-style CLIPModel reproduced all 52 vectors exactly, including the empty-string origin. All 2,550 defined angles matched the author's literal Torch formula within 0.000001334 radians; 51 self-pairs have undefined angles. No truncation; token counts match.

Encoding took 0.45 seconds; cached model loading took 0.37 seconds. The experiment and verification each ran inside the 6 GiB/no-swap/two-CPU-equivalent scope. Verification's current-process memory high-water mark was 721,012 KiB. The unchanged runner's ru_maxrss field is retained as raw legacy telemetry and is not treated as workload-isolated peak memory. No paid resources.

A separate clean-context reader reviewed every fixed case and comparison after scoring and independently confirmed the counts, yogurt ordering problem, and limitations. All previous experiments and the browser remain unchanged.

**Selected data:** Compact pair-score results, inputs and parameters for `HRC02` are selected for release as `numerical/pair-scores-cf76f60afaaf64ac` in the [publication catalog](../../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.

## HRC02 study design

Test the same released HierarCaps CLIP-L checkpoint and paper-defined angle as HRC01. No training, rewritten model inputs, generated subjects, full-note context, new hierarchy, or parameter search. Reuse the unchanged runner and preserve HRC01.

### Questions

1. Does broader-to-narrower ordering survive without repeating the broader subject's words? Examples include bread → bagels and art → photography.
2. Does a real broader subject score better than a related but different subject for the same mask? Examples include food preservation versus growing beets as possible parents of freezing beets, and coffee versus grinding as possible parents of roasting coffee.
3. Does the score favor the intended broader subject when it is described using more words? Examples include general kitchen work versus preparing sourdough.

The selected source corpus is already familiar and mostly food/lifestyle. This is a more discriminating follow-up, not a representative accuracy estimate, unseen-corpus holdout, or technical-domain qualification.

### Freeze before scoring

The [fixture](../hrc02-fixture.json) contains 51 exact saved masks and 27 direction comparisons, with 28 fixed-child comparisons against other proposed parents. Two independent clean-context readers proposed candidates from text only. The main agent inspected the masks and selected cases. A third clean-context reader reviewed them before inference.

That review moved an ambiguous painting mask and a fragmented food-growing mask out of the clearer category group. It also identified the preserved/preservation word-family cue and a mask that omits the source's reversal about squirrels giving up attacks. The saved masks remain unchanged. All selection caveats and reasons are in the fixture.

Report groups separately:

- Thirteen clearer category relationships. Twelve lack a shared subject-word family; the century-eggs case has preserved/preservation overlap.
- Five broader-activity or fragmented-phrase tests, including longer broader wording.
- Seven qualified examples for inspecting ambiguity, advice, diet, and sleep; no mandatory correct direction.
- Two dependent shared-word coffee controls with closely related alternatives.

These are not 27 independent semantic families: several comparisons reuse bread, art, preservation, or advice from the same note. A child may have more than one valid broader subject. Do not prescribe an entire hierarchy or force a unique closest parent.

### Analysis

Preserve all 2,601 ordered pair scores and all 51 embeddings, plus the empty-string origin. Use the same scoring formula and exact-input constraints as [HRC01](../HRC01/RESULTS.md#hrc01-study-design). Model tokenization is allowed; semantic text rewriting and silent truncation are not.

For every fixed direction, show forward and reverse angles, token counts, and the result of the simple assumption that the shorter text is broader. Equal lengths leave that baseline undecided. Direction and distance-from-origin ordering are the same evidence, not separate confirmations.

For every fixed-child comparison, compare both exterior angle and ordinary cosine on the same two proposed parents. This tests whether the directional score adds useful ordering beyond relatedness on these cases. The shorter-parent baseline is reported here too, with ties undecided. Do not interpret its correlation with successes as proof that model behavior is caused by length.

Inspect every scored case, not only aggregate counts. Keep qualified examples separate, and preserve any disagreement with the fixed judgments instead of relabeling failures to improve a score. Do not fit an acceptance cutoff, claim universal error rates, or treat missing candidate parents as model failures.

The exact notes and individual masks must be available with the scores. Validation will replay calculations, verify source and checkpoint hashes, check the unchanged runner tests, and independently reproduce the embeddings. A separate reader will review interpretation after scoring.

### Resources and boundary

Use the already cached checkpoint, CPU only, two threads, batches of four, and the same 6 GiB RAM/no-swap/two-CPU-equivalent systemd limit. No paid resources. The old runner's ru_maxrss field is retained as raw historical telemetry, not asserted as an isolated workload peak. No original artifacts, model parameters, hierarchy memberships, browser, or other agents' files change.
