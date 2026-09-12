# USM02 source results

Every section shows the unchanged original note with its original mask and the unchanged description encoded in USM01. Only dictionary candidate eligibility changes. Rows identify descriptions; word indices are zero-based within the saved tokenization. Several descriptions may belong to one note.

Columns compare saved lemma/POS, original-word lookup across all parts of speech, and original-word lookup retaining saved POS (USM02). Cosines score dictionary meanings; they are not membership probabilities or semantic approvals. Empty means no eligible lexical candidate. The exact top-five results remain in each run’s `scores.json`.

## N094 · Row 88 · V854

> ⟦Decafe coffee drinkers⟧ are the purist coffee enthusiasts of them all as they do it ⟦for⟧ the ⟦experience⟧ and ⟦flavour⟧. ⟦Unlike⟧ the ⟦caffeine addicted⟧ heathens. Change my mind.

Encoded description: Decaffeinated-coffee drinkers drink coffee for its experience and flavour rather than to satisfy a caffeine addiction.

| Word index · text · saved POS | Saved lemma/POS | Original word, all POS | Original word, saved POS |
| --- | --- | --- | --- |
| 0 · Decaffeinated · ADJ | Empty | `decaffeinate.v.01` · 0.687347 | Empty |
| 2 · coffee · NOUN | `coffee.n.01` · 0.812313 | `coffee.n.01` · 0.812313 | `coffee.n.01` · 0.812313 |
| 3 · drinkers · NOUN | `drinker.n.01` · 0.842322 | `drinker.n.01` · 0.842322 | `drinker.n.01` · 0.842322 |
| 4 · drink · VERB | `drink.v.01` · 0.780527 | `drink.v.01` · 0.780527 | `drink.v.01` · 0.780527 |
| 5 · coffee · NOUN | `coffee.n.01` · 0.848948 | `coffee.n.01` · 0.848948 | `coffee.n.01` · 0.848948 |
| 8 · experience · NOUN | `experience.n.03` · 0.766922 | `experience.n.03` · 0.766922 | `experience.n.03` · 0.766922 |
| 10 · flavour · NOUN | `relish.n.03` · 0.672415 | `season.v.01` · 0.823691 | `relish.n.03` · 0.672415 |
| 11 · rather · ADV | `rather.r.01` · 0.806459 | `rather.r.01` · 0.806459 | `rather.r.01` · 0.806459 |
| 14 · satisfy · VERB | `meet.v.04` · 0.822803 | `meet.v.04` · 0.822803 | `meet.v.04` · 0.822803 |
| 16 · caffeine · NOUN | `caffeine.n.01` · 0.841556 | `caffeine.n.01` · 0.841556 | `caffeine.n.01` · 0.841556 |
| 17 · addiction · NOUN | `addiction.n.02` · 0.558531 | `addiction.n.02` · 0.558531 | `addiction.n.02` · 0.558531 |

Decaffeination becomes empty again: the saved adjective restriction excludes the supported caffeine-removal verb. Coffee and drinking remain, but the narrower distinction is lost. Flavour returns to perceived taste instead of lending flavour; its condiment-specific dictionary definition is still not established for this coffee.

## N039 · Row 91 · V298

> Well the ⟦parade was rained out⟧ and umbrellas were ruined.
>
> ⟦Next rounds of storms⟧ look like they ⟦will hit just in time for grilling out dinner⟧.
>
> ⟦Third round⟧ is ⟦scheduled for when we are supposed to have fireworks⟧.

Encoded description: Rain and successive rounds of storms disrupt or threaten a parade, outdoor dinner grilling, and planned fireworks.

| Word index · text · saved POS | Saved lemma/POS | Original word, all POS | Original word, saved POS |
| --- | --- | --- | --- |
| 0 · Rain · NOUN | `rain.n.01` · 0.741923 | `rain.n.01` · 0.741923 | `rain.n.01` · 0.741923 |
| 2 · successive · ADJ | `consecutive.s.02` · 0.814787 | `consecutive.s.02` · 0.814787 | `consecutive.s.02` · 0.814787 |
| 3 · rounds · NOUN | `cycle.n.01` · 0.764815 | `cycle.n.01` · 0.764815 | `cycle.n.01` · 0.764815 |
| 5 · storms · NOUN | `storm.n.01` · 0.801861 | `storm.n.01` · 0.801861 | `storm.n.01` · 0.801861 |
| 6 · disrupt · VERB | `disrupt.v.02` · 0.787293 | `disrupt.v.02` · 0.787293 | `disrupt.v.02` · 0.787293 |
| 8 · threaten · VERB | `endanger.v.01` · 0.801221 | `endanger.v.01` · 0.801221 | `endanger.v.01` · 0.801221 |
| 10 · parade · NOUN | `parade.n.01` · 0.842718 | `parade.n.01` · 0.842718 | `parade.n.01` · 0.842718 |
| 12 · outdoor · ADJ | `outdoor.a.01` · 0.808653 | `outdoor.a.01` · 0.808653 | `outdoor.a.01` · 0.808653 |
| 13 · dinner · NOUN | `dinner.n.02` · 0.797881 | `dinner.n.02` · 0.797881 | `dinner.n.02` · 0.797881 |
| 14 · grilling · NOUN | `broil.n.01` · 0.809189 | `broil.n.01` · 0.809189 | `broil.n.01` · 0.809189 |
| 17 · planned · VERB | `plan.v.02` · 0.726970 | `planned.a.01` · 0.781195 | `plan.v.02` · 0.726970 |
| 18 · fireworks · NOUN | `firework.n.01` · 0.774918 | `firework.n.01` · 0.774918 | `firework.n.01` · 0.774918 |

Planning and the planned adjective both fit the scheduled fireworks. The grammatical change is not a demonstrated subject failure. The unchanged grilling noun supplies a cooking ancestor.

## N026 · Row 187 · V207

> Today i have:
> —Acquired, roasted and ⟦prepared⟧ 12 pounds or more of ⟦tomato’s to make salsa⟧.
> —⟦Made⟧ a big jar of ⟦yogurt⟧
> —acquired 3 rotisserie chickens that were marked down
> —⟦bagged the chicken meat⟧
> —⟦made⟧ over a half gallon of ⟦chicken stock⟧ from the bones,
> —⟦cleaned⟧ so ⟦many dishes⟧ from all the dishes ⟦i used doing all the above⟧.
> —also received a big bag of raw meat to break down into smaller bags, as i begin to switch my chihuahua to raw diet
>
> I could post a few jars of salsa on nostr to see if I could sell a few jars.
> (Pictured is a jar from last year that i just opened :)
> #grownostr

Encoded description: The author washed many dishes used while preparing tomatoes for salsa, making yogurt, bagging chicken meat, and making chicken stock.

| Word index · text · saved POS | Saved lemma/POS | Original word, all POS | Original word, saved POS |
| --- | --- | --- | --- |
| 1 · author · NOUN | `writer.n.01` · 0.748541 | `writer.n.01` · 0.748541 | `writer.n.01` · 0.748541 |
| 2 · washed · VERB | `wash.v.02` · 0.785453 | `wash.v.02` · 0.785453 | `wash.v.02` · 0.785453 |
| 3 · many · ADJ | `many.a.01` · 0.784616 | `many.a.01` · 0.784616 | `many.a.01` · 0.784616 |
| 4 · dishes · NOUN | `dish.n.01` · 0.806576 | `dish.n.01` · 0.806576 | `dish.n.01` · 0.806576 |
| 5 · used · VERB | `use.v.01` · 0.711312 | `used.a.01` · 0.779331 | `use.v.01` · 0.711312 |
| 7 · preparing · VERB | `cook.v.02` · 0.807640 | `cook.v.02` · 0.807640 | `cook.v.02` · 0.807640 |
| 8 · tomatoes · NOUN | Empty | `tomato.n.01` · 0.844034 | `tomato.n.01` · 0.844034 |
| 10 · salsa · NOUN | `salsa.n.01` · 0.869873 | `salsa.n.01` · 0.869873 | `salsa.n.01` · 0.869873 |
| 12 · making · VERB | `make.v.15` · 0.737125 | `make.v.15` · 0.737125 | `make.v.15` · 0.737125 |
| 13 · yogurt · NOUN | `yogurt.n.01` · 0.878936 | `yogurt.n.01` · 0.878936 | `yogurt.n.01` · 0.878936 |
| 15 · bagging · VERB | `bag.v.01` · 0.747693 | `sacking.n.01` · 0.818775 | `bag.v.01` · 0.747693 |
| 16 · chicken · NOUN | `chicken.n.01` · 0.802893 | `chicken.n.01` · 0.802893 | `chicken.n.01` · 0.802893 |
| 17 · meat · NOUN | `meat.n.01` · 0.788382 | `meat.n.01` · 0.788382 | `meat.n.01` · 0.788382 |
| 20 · making · VERB | `make.v.15` · 0.745332 | `make.v.15` · 0.745332 | `make.v.15` · 0.745332 |
| 21 · chicken · NOUN | `chicken.n.01` · 0.799659 | `chicken.n.01` · 0.799659 | `chicken.n.01` · 0.799659 |
| 22 · stock · NOUN | `broth.n.01` · 0.718665 | `broth.n.01` · 0.718665 | `broth.n.01` · 0.718665 |

Tomatoes remains correctly recovered. Used changes grammatical form without a demonstrated meaning loss. Bagging returns from sack fabric to hunting; both miss putting chicken meat into bags.

## N065 · Row 345 · V561

> ⟦Coffee shop⟧ I liked now has a “No laptops or tablets” rule on weekends. This is what happens if you let hipsters get too successful. ⟦Felt like changing their router/ap passwords so they⟧ could ⟦experience⟧ the true ⟦freedom from internet⟧, but I simply went to another coffee shop and will remove this one from rotation. Personal growth on display.

Encoded description: The author wanted to change the coffee shop's router or wireless access point passwords so the people running the shop would experience being without internet access.

| Word index · text · saved POS | Saved lemma/POS | Original word, all POS | Original word, saved POS |
| --- | --- | --- | --- |
| 1 · author · NOUN | `writer.n.01` · 0.710751 | `writer.n.01` · 0.710751 | `writer.n.01` · 0.710751 |
| 2 · wanted · VERB | `desire.v.01` · 0.737119 | `desire.v.01` · 0.737119 | `desire.v.01` · 0.737119 |
| 4 · change · VERB | `change.v.01` · 0.798390 | `change.v.01` · 0.798390 | `change.v.01` · 0.798390 |
| 6 · coffee · NOUN | `coffee.n.01` · 0.747635 | `coffee.n.01` · 0.747635 | `coffee.n.01` · 0.747635 |
| 7 · shop · NOUN | `shop.n.01` · 0.754329 | `shop.n.01` · 0.754329 | `shop.n.01` · 0.754329 |
| 9 · router · NOUN | `router.n.02` · 0.599844 | `router.n.02` · 0.599844 | `router.n.02` · 0.599844 |
| 11 · wireless · ADJ | `wireless.a.01` · 0.833250 | `wireless.a.01` · 0.833250 | `wireless.a.01` · 0.833250 |
| 12 · access · NOUN | `entree.n.02` · 0.730801 | `entree.n.02` · 0.730801 | `entree.n.02` · 0.730801 |
| 13 · point · NOUN | `point.n.25` · 0.653627 | `point.n.25` · 0.653627 | `point.n.25` · 0.653627 |
| 14 · passwords · NOUN | `password.n.01` · 0.794532 | `password.n.01` · 0.794532 | `password.n.01` · 0.794532 |
| 17 · people · NOUN | `people.n.01` · 0.772024 | `people.n.01` · 0.772024 | `people.n.01` · 0.772024 |
| 18 · running · VERB | `run.v.13` · 0.719842 | `run.v.13` · 0.719842 | `run.v.13` · 0.719842 |
| 20 · shop · NOUN | `shop.n.01` · 0.782505 | `shop.n.01` · 0.782505 | `shop.n.01` · 0.782505 |
| 22 · experience · VERB | `know.v.05` · 0.742357 | `know.v.05` · 0.742357 | `know.v.05` · 0.742357 |
| 25 · internet · NOUN | `internet.n.01` · 0.775375 | `internet.n.01` · 0.775375 | `internet.n.01` · 0.775375 |
| 26 · access · NOUN | `access.n.02` · 0.741091 | `access.n.02` · 0.741091 | `access.n.02` · 0.741091 |

No highest match changes. Wireless access point remains split into inappropriate single-word meanings. The source qualifications in USM01 still apply; correct router and shop meanings do not certify every derived category.

## N100 · Row 350 · V940

> Alright today's been pretty solid.
>
> Picked up a ⟦sirloin⟧ strip sub primal for $10 a lb ⟦cut⟧ 15 ⟦steaks⟧ about 1.5-2" thickness.
>
> Trimmed about 3lb of fat for making tallow and about a quarter pound of some connective tissue and scrap meat for the dog.
>
>
> Saved the excess myoglobin to add in the dogs food and will put some some cold water and sunflower seeds for the chickens tomorrow.
>
> I finally got to use the new vacuum sealer and this one is much better than the food savers I've used in the past. I got this on a deal from Amazon for 30% off and love it after using it. If you need one check out the Nesco VS-12
>
> #beef #foodstr #foodpreservation #cooking #steak #cooking #grownostr #prepping #plebchain #homesteading
>
>  https://image.nostr.build/270bbbc11299301ee5b4678883c5d48ab2f95eb13b1417093186ba855f4d90e5.jpg

Encoded description: Beef and steak preparation.

| Word index · text · saved POS | Saved lemma/POS | Original word, all POS | Original word, saved POS |
| --- | --- | --- | --- |
| 0 · Beef · NOUN | `beef.n.01` · 0.545082 | `gripe.v.01` · 0.569100 | `beef.n.01` · 0.545082 |
| 2 · steak · NOUN | `steak.n.01` · 0.824985 | `steak.n.01` · 0.824985 | `steak.n.01` · 0.824985 |
| 3 · preparation · NOUN | `formulation.n.01` · 0.732952 | `formulation.n.01` · 0.732952 | `formulation.n.01` · 0.732952 |

Beef no longer means complaining, but the noun denotes cattle rather than meat. Steak independently supplies a valid meat-cut witness. Preparation still denotes a formulated substance, not an activity.

## N047 · Row 375 · V364

> ⟦Cleaning out⟧ the ⟦ashes⟧ ⟦to now put in⟧ the ⟦bread pans⟧. It remains very hot for some time. Takes about 5-6 min for them to cook. https://video.nostr.build/1287907c5686c9eb72895eb5c52a9869aaff5ed6c46db7041ed4d8797635af04.mp4 https://image.nostr.build/ac895487f166b3e2a6bfb161d4bc0fca1a8720386968b3187981b6dcbf18d7ae.jpg https://image.nostr.build/9a73232d8b89163a07272467dab427cfe8549181b9a74da654d353b4b68ed6ce.jpg  nostr:note1tc57qmd25gu4ddgqwyuk3my7endvrxvwgdtqldvd066ml5f885tqps5a3c

Encoded description: Baking bread in pans after cleaning ashes out of the baking space.

| Word index · text · saved POS | Saved lemma/POS | Original word, all POS | Original word, saved POS |
| --- | --- | --- | --- |
| 0 · Baking · NOUN | `baking.n.01` · 0.604723 | `bake.v.01` · 0.691766 | `baking.n.01` · 0.604723 |
| 1 · bread · NOUN | `bread.n.01` · 0.828937 | `bread.n.01` · 0.828937 | `bread.n.01` · 0.828937 |
| 3 · pans · NOUN | `pan.n.01` · 0.815840 | `pan.n.01` · 0.815840 | `pan.n.01` · 0.815840 |
| 5 · cleaning · VERB | `clean.v.01` · 0.786481 | `clean.v.01` · 0.786481 | `clean.v.01` · 0.786481 |
| 6 · ashes · NOUN | `ash.n.01` · 0.760834 | `ash.n.01` · 0.760834 | `ash.n.01` · 0.760834 |
| 10 · baking · NOUN | `baking.n.02` · 0.680590 | `baking.n.02` · 0.680590 | `baking.n.02` · 0.680590 |
| 11 · space · NOUN | `space.n.03` · 0.768148 | `space.n.03` · 0.768148 | `space.n.03` · 0.768148 |

Both baking readings are plausible topics for the hot space, ashes and bread pans. The source does not explicitly name an oven. Retained baking meanings supply a cooking ancestor.

## N022 · Row 378 · V152

> This year’s ⟦beets⟧. Vac sealed and ready for the freezer. Not too bad for a 4x4 raised bed. ⟦5 meals⟧ of ⟦sides⟧ in a pinch. I am looking forward to having more garden space but this is good while we are still in a half acre lot in town. https://image.nostr.build/b4349cc1251dccf78990620ee851ad0ae449327da16ac31391e3e71fafdbe65c.jpg https://image.nostr.build/5c7e4ba19bb3c2e98cb57753679d33be2bbad3a07900afc86315c85f80bc46e4.jpg

Encoded description: The author's beet harvest provides side dishes for five meals.

| Word index · text · saved POS | Saved lemma/POS | Original word, all POS | Original word, saved POS |
| --- | --- | --- | --- |
| 1 · author · NOUN | `writer.n.01` · 0.734731 | `writer.n.01` · 0.734731 | `writer.n.01` · 0.734731 |
| 3 · beet · NOUN | `boot.n.04` · 0.488708 | `beet.n.02` · 0.629193 | `beet.n.02` · 0.629193 |
| 4 · harvest · NOUN | `crop.n.01` · 0.778358 | `crop.n.01` · 0.778358 | `crop.n.01` · 0.778358 |
| 5 · provides · VERB | `supply.v.01` · 0.777270 | `supply.v.01` · 0.777270 | `supply.v.01` · 0.777270 |
| 6 · side · NOUN | `side.n.09` · 0.656441 | `side.a.01` · 0.745557 | `side.n.09` · 0.656441 |
| 7 · dishes · NOUN | `dish.n.01` · 0.769702 | `dish.n.01` · 0.769702 | `dish.n.01` · 0.769702 |
| 10 · meals · NOUN | `meal.n.01` · 0.834910 | `meal.n.01` · 0.834910 | `meal.n.01` · 0.834910 |

Beet remains correctly recovered as the edible root rather than boot casing. Side returns to half an animal carcass instead of the intended beet food portions. This wrong sense admits the note to meat cuts. Crop-plant versus edible-root readings need not have one prescribed correct answer.

## N069 · Row 405 · V610

> 1. Do not use your phone after 8pm.
> 2. Fast 18 hours a day, stop eating 3 hours before bed time.
> 3. Be consitent with your bed time. Get enough good sleep.
> 4. Do not eat processed food. Provide your body with a diverse diet, make sure to get in fiber and protein, omega 3.
> 5. Find a way to slow things down, change your life if you have unhealthy stress.
> 6. Get out of the house, especially in the morning.
> 7. Focus on community / family.
> 8. Be positive, assume the best in people. Be consequent if you been proven otherwise.
> 9. ⟦Be good, not for others sake, but for your own peace⟧. Even if that means you will face reprecussion.
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

Encoded description: Being good for one's own peace rather than for other people's sake.

| Word index · text · saved POS | Saved lemma/POS | Original word, all POS | Original word, saved POS |
| --- | --- | --- | --- |
| 1 · good · ADJ | `beneficial.s.01` · 0.804187 | `beneficial.s.01` · 0.804187 | `beneficial.s.01` · 0.804187 |
| 5 · own · ADJ | `own.s.01` · 0.807172 | `own.s.01` · 0.807172 | `own.s.01` · 0.807172 |
| 6 · peace · NOUN | `peace.n.02` · 0.788001 | `peace.n.02` · 0.788001 | `peace.n.02` · 0.788001 |
| 7 · rather · ADV | `rather.r.01` · 0.812393 | `rather.r.01` · 0.812393 | `rather.r.01` · 0.812393 |
| 10 · other · ADJ | `other.a.01` · 0.725506 | `other.a.01` · 0.725506 | `other.a.01` · 0.725506 |
| 11 · people · NOUN | `people.n.01` · 0.758457 | `people.n.01` · 0.758457 | `people.n.01` · 0.758457 |
| 13 · sake · NOUN | `sake.n.01` · 0.797903 | `sake.n.01` · 0.797903 | `sake.n.01` · 0.797903 |

No highest match changes. The original USM01 source qualifications remain; this intervention does not adjudicate new morning, wellbeing or peace meanings.

## N013 · Row 468 · V100

> Got the ⟦stock pots rolling⟧ today for a batch of ⟦chicken stock⟧. We save carcasses when we butcher and a couple of times a year do this. I’ll ⟦pressure can⟧ it and ⟦store in the pantry⟧. Should get around 25 quarts with this batch.
> #grownostr
> #homesteading
> #foodsecurity
> #foodstr https://image.nostr.build/aead0ba70aa9ec698013666afe87bb76d74d9a19dbb7b93ceb0de953fa2e3386.jpg

Encoded description: Pressure-canning homemade chicken stock for pantry storage is a form of food preservation.

| Word index · text · saved POS | Saved lemma/POS | Original word, all POS | Original word, saved POS |
| --- | --- | --- | --- |
| 0 · Pressure · NOUN | `press.n.09` · 0.647262 | `press.n.09` · 0.647262 | `press.n.09` · 0.647262 |
| 2 · canning · NOUN | Empty | `can.v.01` · 0.645152 | Empty |
| 3 · homemade · VERB | Empty | `homemade.a.01` · 0.848421 | Empty |
| 4 · chicken · NOUN | `chicken.n.01` · 0.816733 | `chicken.n.01` · 0.816733 | `chicken.n.01` · 0.816733 |
| 5 · stock · NOUN | `broth.n.01` · 0.725257 | `broth.n.01` · 0.725257 | `broth.n.01` · 0.725257 |
| 7 · pantry · NOUN | `pantry.n.01` · 0.845062 | `pantry.n.01` · 0.845062 | `pantry.n.01` · 0.845062 |
| 8 · storage · NOUN | `storage.n.03` · 0.815215 | `storage.n.03` · 0.815215 | `storage.n.03` · 0.815215 |
| 11 · form · NOUN | `kind.n.01` · 0.754599 | `kind.n.01` · 0.754599 | `kind.n.01` · 0.754599 |
| 13 · food · NOUN | `food.n.01` · 0.789954 | `food.n.01` · 0.789954 | `food.n.01` · 0.789954 |
| 14 · preservation · NOUN | `preservation.n.01` · 0.700743 | `preservation.n.01` · 0.700743 | `preservation.n.01` · 0.700743 |

Canning becomes empty under the saved noun analysis; homemade becomes empty under the saved verb analysis. The original pressure-canning and personal stock-making support their broader meanings. The mask does not establish a particular building. Other words still support chicken stock and preservation; no fallback or hand correction is applied.

## N096 · Row 544 · V885

> My #neverfail ⟦Spaghetti Bolognaise⟧ recipe that feeds 5.
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
> In a large pan on medium heat, ⟦sauté⟧ the finely chopped ⟦onion, celery and carrot⟧ in the olive oil. After a few minutes add the crushed garlic. Once onions are clear, push to side and add ground beef. ⟦Gently fry beef⟧ without browning. Once beef is all the same colour ⟦add⟧ both tins of ⟦tomatoes⟧ plus 1 tin of ⟦water⟧. Add chopped fresh ⟦basil⟧ leaves. Mix all ingredients thoroughly. ⟦Simmer⟧ on low heat for 45min-1hr.
> Cook spaghetti according to packet.
> #food #recipe #easy #spaghetti #bolognaise #tomato #dinner
>
> https://m.primal.net/ODru.mov

Encoded description: A method for preparing spaghetti Bolognaise by sautéing vegetables, gently frying beef, adding tomatoes, water and basil, and simmering the sauce.

| Word index · text · saved POS | Saved lemma/POS | Original word, all POS | Original word, saved POS |
| --- | --- | --- | --- |
| 1 · method · NOUN | `method.n.01` · 0.796874 | `method.n.01` · 0.796874 | `method.n.01` · 0.796874 |
| 3 · preparing · VERB | `cook.v.02` · 0.791895 | `cook.v.02` · 0.791895 | `cook.v.02` · 0.791895 |
| 4 · spaghetti · NOUN | `spaghetti.n.01` · 0.706384 | `spaghetti.n.01` · 0.706384 | `spaghetti.n.01` · 0.706384 |
| 5 · Bolognaise · PROPN | Empty | Empty | Empty |
| 7 · sautéing · NOUN | Empty | Empty | Empty |
| 8 · vegetables · NOUN | `vegetable.n.01` · 0.773412 | `vegetable.n.01` · 0.773412 | `vegetable.n.01` · 0.773412 |
| 10 · gently · ADV | `gently.r.01` · 0.785732 | `gently.r.01` · 0.785732 | `gently.r.01` · 0.785732 |
| 11 · frying · NOUN | `frying.n.01` · 0.856687 | `frying.n.01` · 0.856687 | `frying.n.01` · 0.856687 |
| 12 · beef · NOUN | `beef.n.02` · 0.804644 | `beef.n.02` · 0.804644 | `beef.n.02` · 0.804644 |
| 14 · adding · VERB | `add.v.01` · 0.720059 | `add.v.01` · 0.720059 | `add.v.01` · 0.720059 |
| 15 · tomatoes · NOUN | Empty | `tomato.n.01` · 0.820750 | `tomato.n.01` · 0.820750 |
| 17 · water · NOUN | `water.n.01` · 0.752058 | `water.n.01` · 0.752058 | `water.n.01` · 0.752058 |
| 19 · basil · NOUN | `basil.n.03` · 0.629954 | `basil.n.03` · 0.629954 | `basil.n.03` · 0.629954 |
| 22 · simmering · VERB | Empty | `simmer.v.01` · 0.790283 | `simmer.v.01` · 0.790283 |
| 24 · sauce · NOUN | `sauce.n.01` · 0.799509 | `sauce.n.01` · 0.799509 | `sauce.n.01` · 0.799509 |

Tomatoes and simmering remain recovered. Bolognaise and sautéing stay empty. Frying independently supplies cooking; simmer’s ordinary hypernyms do not themselves reach cooking or preparation.

## N094 · Row 572 · V852

> ⟦Decafe coffee drinkers⟧ are the purist coffee enthusiasts of them all as they do it ⟦for the experience⟧ and flavour. Unlike the caffeine addicted heathens. Change my mind.

Encoded description: Decaffeinated-coffee drinkers drink coffee for the experience of drinking coffee.

| Word index · text · saved POS | Saved lemma/POS | Original word, all POS | Original word, saved POS |
| --- | --- | --- | --- |
| 0 · Decaffeinated · ADJ | Empty | `decaffeinate.v.01` · 0.690938 | Empty |
| 2 · coffee · NOUN | `coffee.n.01` · 0.813838 | `coffee.n.01` · 0.813838 | `coffee.n.01` · 0.813838 |
| 3 · drinkers · NOUN | `drinker.n.01` · 0.857162 | `drinker.n.01` · 0.857162 | `drinker.n.01` · 0.857162 |
| 4 · drink · VERB | `drink.v.01` · 0.795055 | `drink.v.01` · 0.795055 | `drink.v.01` · 0.795055 |
| 5 · coffee · NOUN | `coffee.n.01` · 0.842690 | `coffee.n.01` · 0.842690 | `coffee.n.01` · 0.842690 |
| 8 · experience · NOUN | `experience.n.03` · 0.764595 | `experience.n.03` · 0.764595 | `experience.n.03` · 0.764595 |
| 10 · drinking · VERB | `drink.v.01` · 0.744936 | `drinking.n.01` · 0.792518 | `drink.v.01` · 0.744936 |
| 11 · coffee · NOUN | `coffee.n.01` · 0.834140 | `coffee.n.01` · 0.834140 | `coffee.n.01` · 0.834140 |

This second empty decaffeination occurrence belongs to the same note as row 88. Drinking changes between consuming-liquids noun and take-in-liquids verb; the topic is preserved but dictionary ancestry differs.

## N076 · Row 673 · V709

> Tandori spice chik with somo sexi yogo. On pure fire with best handmade wild rose wine,  #purelife #food #⟦chef⟧ #foodstr no compromise
>
> https://image.nostr.build/d9fce20da7cd056362daca85445508eafc7620bf706788474b1dc28e4875971e.jpg https://image.nostr.build/a648216b769b08347153de65a019f5968d249882cefa912b8c64519d36ca95cf.jpg
> https://image.nostr.build/07e9f6b72f1983601c5f5733b7b889fd6fbe0e8a25e40f131edf1ad299cacd20.jpg

Encoded description: Food preparation and the culinary craft of chefs.

| Word index · text · saved POS | Saved lemma/POS | Original word, all POS | Original word, saved POS |
| --- | --- | --- | --- |
| 0 · Food · NOUN | `food.n.01` · 0.728607 | `food.n.01` · 0.728607 | `food.n.01` · 0.728607 |
| 1 · preparation · NOUN | `preparation.n.01` · 0.736607 | `preparation.n.01` · 0.736607 | `preparation.n.01` · 0.736607 |
| 4 · culinary · ADJ | `culinary.a.01` · 0.856037 | `culinary.a.01` · 0.856037 | `culinary.a.01` · 0.856037 |
| 5 · craft · NOUN | `trade.n.02` · 0.763323 | `trade.n.02` · 0.763323 | `trade.n.02` · 0.763323 |
| 7 · chefs · NOUN | `chef.n.01` · 0.847984 | `chef.n.01` · 0.847984 | `chef.n.01` · 0.847984 |

No highest match changes. The original chef hashtag supports a culinary topic, not necessarily every professional-role detail in the expanded description. This description supplies the automatic inventory’s only preparation noun.

## N085 · Row 711 · V786

> #foodstr starting out with a bang this morning. ⟦Brisket on the smoker⟧ for about 3 hours now. https://image.nostr.build/bb53e68600aed853077353e5865e7c7700dfcbd40903b1e0d7852e461d7d70c9.jpg

Encoded description: Cooking brisket on a smoker.

| Word index · text · saved POS | Saved lemma/POS | Original word, all POS | Original word, saved POS |
| --- | --- | --- | --- |
| 0 · Cooking · NOUN | `cooking.n.01` · 0.704449 | `cook.v.01` · 0.710078 | `cooking.n.01` · 0.704449 |
| 1 · brisket · NOUN | `brisket.n.01` · 0.828788 | `brisket.n.01` · 0.828788 | `brisket.n.01` · 0.828788 |
| 4 · smoker · NOUN | `smoker.n.01` · 0.649078 | `smoker.n.01` · 0.649078 | `smoker.n.01` · 0.649078 |

Both cooking meanings fit brisket on a smoker. The food-heating noun joins other cooking notes even though smoker remains incorrectly interpreted as a tobacco user.

## N089 · Row 866 · V806

> Gm nostr
>
> ⟦Bread⟧ superstition requires ⟦salt⟧ to be added at a distance from ⟦yeast⟧ before ⟦mixing⟧ 🤔
>
> https://image.nostr.build/cc4282a3aa0bc2b42942e1f9e1e6a5cbd9db22ec6d82cee2ef6a7ff665cbe63e.jpg

Encoded description: Bread preparation involving salt, yeast, and mixing.

| Word index · text · saved POS | Saved lemma/POS | Original word, all POS | Original word, saved POS |
| --- | --- | --- | --- |
| 0 · Bread · NOUN | `bread.n.01` · 0.635696 | `bread.v.01` · 0.651334 | `bread.n.01` · 0.635696 |
| 1 · preparation · NOUN | `formulation.n.01` · 0.815809 | `formulation.n.01` · 0.815809 | `formulation.n.01` · 0.815809 |
| 2 · involving · VERB | `necessitate.v.01` · 0.761333 | `necessitate.v.01` · 0.761333 | `necessitate.v.01` · 0.761333 |
| 3 · salt · NOUN | `salt.n.02` · 0.849297 | `salt.n.02` · 0.849297 | `salt.n.02` · 0.849297 |
| 5 · yeast · NOUN | `yeast.n.02` · 0.577178 | `yeast.n.02` · 0.577178 | `yeast.n.02` · 0.577178 |
| 8 · mixing · NOUN | `mix.n.03` · 0.732699 | `mix.n.03` · 0.732699 | `mix.n.03` · 0.732699 |

Bread correctly returns to bread food rather than breadcrumb coating. Preparation still denotes a formulated substance; recovering bread does not preserve the old bread/steak preparation activity grouping.

## N022 · Row 904 · V149

> ⟦This year’s beets⟧. Vac sealed and ⟦ready for the freezer⟧. Not too bad for a 4x4 ⟦raised bed⟧. 5 meals of sides in a pinch. I am looking forward to having more garden space but this is good while we are still in a half acre lot in town. https://image.nostr.build/b4349cc1251dccf78990620ee851ad0ae449327da16ac31391e3e71fafdbe65c.jpg https://image.nostr.build/5c7e4ba19bb3c2e98cb57753679d33be2bbad3a07900afc86315c85f80bc46e4.jpg

Encoded description: The author is preparing this year's garden-grown beets for preservation by freezing.

| Word index · text · saved POS | Saved lemma/POS | Original word, all POS | Original word, saved POS |
| --- | --- | --- | --- |
| 1 · author · NOUN | `writer.n.01` · 0.750907 | `writer.n.01` · 0.750907 | `writer.n.01` · 0.750907 |
| 3 · preparing · VERB | `prepare.v.03` · 0.773033 | `prepare.v.03` · 0.773033 | `prepare.v.03` · 0.773033 |
| 5 · year · NOUN | `year.n.02` · 0.648993 | `year.n.02` · 0.648993 | `year.n.02` · 0.648993 |
| 7 · garden · NOUN | `garden.n.01` · 0.818545 | `garden.n.01` · 0.818545 | `garden.n.01` · 0.818545 |
| 9 · grown · VERB | `grow.v.07` · 0.767674 | `grow.v.07` · 0.767674 | `grow.v.07` · 0.767674 |
| 10 · beets · NOUN | `beet.n.01` · 0.631819 | `beet.n.01` · 0.631819 | `beet.n.01` · 0.631819 |
| 12 · preservation · NOUN | `preservation.n.01` · 0.772101 | `preservation.n.01` · 0.772101 | `preservation.n.01` · 0.772101 |
| 14 · freezing · VERB | Empty | `freeze.n.01` · 0.786979 | `freeze.v.04` · 0.777550 |

The cause-to-freeze verb and the all-POS physical-freezing noun both fit the intended preservation process. The original says ready for the freezer, not that freezing has finished. The new verb supplies no preservation ancestor; preparing still has the wrong speech-preparation sense.
