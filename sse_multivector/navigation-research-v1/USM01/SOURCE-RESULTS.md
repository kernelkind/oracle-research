# USM01 source results

Every original note and frozen mask appears below. The description is the text actually encoded; only its lexical word occurrences were scored. These are not SSE masks or generated navigation labels. Trailing line whitespace is omitted in this Markdown display; exact source text remains in [inputs.json](./run/inputs.json).

`Row/index` identifies a word in one description. Saved = saved lemma and part of speech. Surface = original-word morphology across parts of speech. Unrestricted = entire sense inventory. Numbers are cosine similarities, not confidence probabilities. A dash means no eligible candidate. Each cell shows the highest match; [scores.json](./run/scores.json) preserves all five matches, exact scores and candidate counts.

## Row 88 · N094 · V854

> ⟦Decafe coffee drinkers⟧ are the purist coffee enthusiasts of them all as they do it ⟦for⟧ the ⟦experience⟧ and ⟦flavour⟧. ⟦Unlike⟧ the ⟦caffeine addicted⟧ heathens. Change my mind.

Encoded description: Decaffeinated-coffee drinkers drink coffee for its experience and flavour rather than to satisfy a caffeine addiction.

Analysis: Coffee, drinking and experience are retained. Original-word lookup supplies decaffeination. Unrestricted caffeine addiction is supported by the contrast, not asserted of decaf drinkers. Flavor remains imperfect: perceived taste is not the act of adding seasoning.

| Word index · text | Saved | Surface | Unrestricted |
| --- | --- | --- | --- |
| 0 · Decaffeinated | — | `decaffeinate.v.01` · 0.687347 | `decaffeinate.v.01` · 0.687347 |
| 2 · coffee | `coffee.n.01` · 0.812313 | `coffee.n.01` · 0.812313 | `coffee.n.01` · 0.812313 |
| 3 · drinkers | `drinker.n.01` · 0.842322 | `drinker.n.01` · 0.842322 | `drinker.n.01` · 0.842322 |
| 4 · drink | `drink.v.01` · 0.780527 | `drink.v.01` · 0.780527 | `drink.v.01` · 0.780527 |
| 5 · coffee | `coffee.n.01` · 0.848948 | `coffee.n.01` · 0.848948 | `coffee.n.01` · 0.848948 |
| 8 · experience | `experience.n.03` · 0.766922 | `experience.n.03` · 0.766922 | `experience.n.03` · 0.766922 |
| 10 · flavour | `relish.n.03` · 0.672415 | `season.v.01` · 0.823691 | `season.v.01` · 0.823691 |
| 11 · rather | `rather.r.01` · 0.806459 | `rather.r.01` · 0.806459 | `rather.r.01` · 0.806459 |
| 14 · satisfy | `meet.v.04` · 0.822803 | `meet.v.04` · 0.822803 | `meet.v.04` · 0.822803 |
| 16 · caffeine | `caffeine.n.01` · 0.841556 | `caffeine.n.01` · 0.841556 | `caffeine.n.01` · 0.841556 |
| 17 · addiction | `addiction.n.02` · 0.558531 | `addiction.n.02` · 0.558531 | `caffein_addiction.n.01` · 0.767034 |

Dictionary meanings of these highest matches:

- `decaffeinate.v.01`: remove caffeine from (coffee)
- `coffee.n.01`: a beverage consisting of an infusion of ground coffee beans
- `drinker.n.01`: a person who drinks liquids
- `drink.v.01`: take in liquids
- `experience.n.03`: an event as apprehended
- `relish.n.03`: the taste experience when a savoury condiment is taken into the mouth
- `season.v.01`: lend flavor to
- `rather.r.01`: on the contrary
- `meet.v.04`: fill or meet a want or need
- `caffeine.n.01`: a bitter alkaloid found in coffee and tea that is responsible for their stimulating effects
- `addiction.n.02`: an abnormally strong craving
- `caffein_addiction.n.01`: an addiction to caffein

## Row 91 · N039 · V298

> Well the ⟦parade was rained out⟧ and umbrellas were ruined.
>
> ⟦Next rounds of storms⟧ look like they ⟦will hit just in time for grilling out dinner⟧.
>
> ⟦Third round⟧ is ⟦scheduled for when we are supposed to have fireworks⟧.

Encoded description: Rain and successive rounds of storms disrupt or threaten a parade, outdoor dinner grilling, and planned fireworks.

Analysis: Storm rounds now map to a recurring cycle rather than professional visits. Grilling is represented as radiant-heat cooking. The unrestricted aerial-firework subtype is not established by the source; planned action versus planned adjective is not a substantive failure.

| Word index · text | Saved | Surface | Unrestricted |
| --- | --- | --- | --- |
| 0 · Rain | `rain.n.01` · 0.741923 | `rain.n.01` · 0.741923 | `rain.n.01` · 0.741923 |
| 2 · successive | `consecutive.s.02` · 0.814787 | `consecutive.s.02` · 0.814787 | `consecutive.s.02` · 0.814787 |
| 3 · rounds | `cycle.n.01` · 0.764815 | `cycle.n.01` · 0.764815 | `cycle.n.01` · 0.764815 |
| 5 · storms | `storm.n.01` · 0.801861 | `storm.n.01` · 0.801861 | `storm.n.01` · 0.801861 |
| 6 · disrupt | `disrupt.v.02` · 0.787293 | `disrupt.v.02` · 0.787293 | `disrupt.v.02` · 0.787293 |
| 8 · threaten | `endanger.v.01` · 0.801221 | `endanger.v.01` · 0.801221 | `endanger.v.01` · 0.801221 |
| 10 · parade | `parade.n.01` · 0.842718 | `parade.n.01` · 0.842718 | `parade.n.01` · 0.842718 |
| 12 · outdoor | `outdoor.a.01` · 0.808653 | `outdoor.a.01` · 0.808653 | `outdoor.a.01` · 0.808653 |
| 13 · dinner | `dinner.n.02` · 0.797881 | `dinner.n.02` · 0.797881 | `dinner.n.02` · 0.797881 |
| 14 · grilling | `broil.n.01` · 0.809189 | `broil.n.01` · 0.809189 | `broil.n.01` · 0.809189 |
| 17 · planned | `plan.v.02` · 0.726970 | `planned.a.01` · 0.781195 | `planned.a.01` · 0.781195 |
| 18 · fireworks | `firework.n.01` · 0.774918 | `firework.n.01` · 0.774918 | `skyrocket.n.02` · 0.803075 |

Dictionary meanings of these highest matches:

- `rain.n.01`: water falling in drops from vapor condensed in the atmosphere
- `consecutive.s.02`: in regular succession without gaps
- `cycle.n.01`: an interval during which a recurring sequence of events occurs
- `storm.n.01`: a violent weather condition with winds 64-72 knots (11 on the Beaufort scale) and precipitation and thunder and lightning
- `disrupt.v.02`: throw into disorder
- `endanger.v.01`: pose a threat to; present a danger to
- `parade.n.01`: a ceremonial procession including people marching
- `outdoor.a.01`: located, suited for, or taking place in the open air
- `dinner.n.02`: a party of people assembled to have dinner together
- `broil.n.01`: cooking by direct exposure to radiant heat (as over a fire or under a grill)
- `plan.v.02`: make plans for something
- `planned.a.01`: designed or carried out according to a plan
- `firework.n.01`: (usually plural) a device with an explosive that burns at a low rate and with colored flames; can be used to illuminate areas or send signals etc.
- `skyrocket.n.02`: sends a firework display high into the sky

## Row 187 · N026 · V207

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

Analysis: Original-word lookup restores tomatoes; lexical restrictions keep chicken and broth. Unrestricted matching adds unsupported tomato variety, chicken age, serving vessels and specifically beef broth despite explicit chicken stock. Both restricted conditions miss bagging meat; washing one's body also misidentifies dishwashing. The description is supported by the mask, but its author wording does not establish professional writing.

| Word index · text | Saved | Surface | Unrestricted |
| --- | --- | --- | --- |
| 1 · author | `writer.n.01` · 0.748541 | `writer.n.01` · 0.748541 | `writer.n.01` · 0.748541 |
| 2 · washed | `wash.v.02` · 0.785453 | `wash.v.02` · 0.785453 | `wash.v.02` · 0.785453 |
| 3 · many | `many.a.01` · 0.784616 | `many.a.01` · 0.784616 | `many.a.01` · 0.784616 |
| 4 · dishes | `dish.n.01` · 0.806576 | `dish.n.01` · 0.806576 | `serving_dish.n.01` · 0.826983 |
| 5 · used | `use.v.01` · 0.711312 | `used.a.01` · 0.779331 | `used.a.01` · 0.779331 |
| 7 · preparing | `cook.v.02` · 0.807640 | `cook.v.02` · 0.807640 | `cook.v.02` · 0.807640 |
| 8 · tomatoes | — | `tomato.n.01` · 0.844034 | `plum_tomato.n.02` · 0.846576 |
| 10 · salsa | `salsa.n.01` · 0.869873 | `salsa.n.01` · 0.869873 | `salsa.n.01` · 0.869873 |
| 12 · making | `make.v.15` · 0.737125 | `make.v.15` · 0.737125 | `make.v.15` · 0.737125 |
| 13 · yogurt | `yogurt.n.01` · 0.878936 | `yogurt.n.01` · 0.878936 | `yogurt.n.01` · 0.878936 |
| 15 · bagging | `bag.v.01` · 0.747693 | `sacking.n.01` · 0.818775 | `sacking.n.01` · 0.818775 |
| 16 · chicken | `chicken.n.01` · 0.802893 | `chicken.n.01` · 0.802893 | `spring_chicken.n.02` · 0.820658 |
| 17 · meat | `meat.n.01` · 0.788382 | `meat.n.01` · 0.788382 | `meat.n.01` · 0.788382 |
| 20 · making | `make.v.15` · 0.745332 | `make.v.15` · 0.745332 | `make.v.15` · 0.745332 |
| 21 · chicken | `chicken.n.01` · 0.799659 | `chicken.n.01` · 0.799659 | `spring_chicken.n.02` · 0.817043 |
| 22 · stock | `broth.n.01` · 0.718665 | `broth.n.01` · 0.718665 | `beef_broth.n.01` · 0.727057 |

Dictionary meanings of these highest matches:

- `writer.n.01`: writes (books or stories or articles or the like) professionally (for pay)
- `wash.v.02`: cleanse (one's body) with soap and water
- `many.a.01`: a quantifier that can be used with count nouns and is often preceded by `as' or `too' or `so' or `that'; amounting to a large but indefinite number
- `dish.n.01`: a piece of dishware normally used as a container for holding or serving food
- `serving_dish.n.01`: a dish used for serving food
- `use.v.01`: put into service; make work or employ for a particular purpose or for its inherent or natural purpose
- `used.a.01`: employed in accomplishing something; - H.H.Arnold & I.C.Eaker
- `cook.v.02`: prepare for eating by applying heat
- `tomato.n.01`: mildly acid red or yellow pulpy fruit eaten as a vegetable
- `plum_tomato.n.02`: a kind of cherry tomato that is frequently used in cooking rather than eaten raw
- `salsa.n.01`: spicy sauce of tomatoes and onions and chili peppers to accompany Mexican foods
- `make.v.15`: make by shaping or bringing together constituents
- `yogurt.n.01`: a custard-like food made from curdled milk
- `bag.v.01`: capture or kill, as in hunting
- `sacking.n.01`: coarse fabric used for bags or sacks
- `chicken.n.01`: the flesh of a chicken used for food
- `spring_chicken.n.02`: a young chicken having tender meat
- `meat.n.01`: the flesh of animals (including fishes and birds and snails) used as food
- `broth.n.01`: liquid in which meat and vegetables are simmered; used as a basis for e.g. soups or sauces
- `beef_broth.n.01`: a stock made with beef

## Row 345 · N065 · V561

> ⟦Coffee shop⟧ I liked now has a “No laptops or tablets” rule on weekends. This is what happens if you let hipsters get too successful. ⟦Felt like changing their router/ap passwords so they⟧ could ⟦experience⟧ the true ⟦freedom from internet⟧, but I simply went to another coffee shop and will remove this one from rotation. Personal growth on display.

Encoded description: The author wanted to change the coffee shop's router or wireless access point passwords so the people running the shop would experience being without internet access.

Analysis: Restricted router identifies the specified network device; unrestricted modem and highly experienced insiders add meanings absent from the source. Separate access and point tokens do not recover wireless access point. Professional authorship is unsupported; operational state is not precisely people managing the shop.

| Word index · text | Saved | Surface | Unrestricted |
| --- | --- | --- | --- |
| 1 · author | `writer.n.01` · 0.710751 | `writer.n.01` · 0.710751 | `writer.n.01` · 0.710751 |
| 2 · wanted | `desire.v.01` · 0.737119 | `desire.v.01` · 0.737119 | `desire.v.01` · 0.737119 |
| 4 · change | `change.v.01` · 0.798390 | `change.v.01` · 0.798390 | `change.v.01` · 0.798390 |
| 6 · coffee | `coffee.n.01` · 0.747635 | `coffee.n.01` · 0.747635 | `coffee.n.01` · 0.747635 |
| 7 · shop | `shop.n.01` · 0.754329 | `shop.n.01` · 0.754329 | `shop.n.01` · 0.754329 |
| 9 · router | `router.n.02` · 0.599844 | `router.n.02` · 0.599844 | `modem.n.01` · 0.680306 |
| 11 · wireless | `wireless.a.01` · 0.833250 | `wireless.a.01` · 0.833250 | `wireless.a.01` · 0.833250 |
| 12 · access | `entree.n.02` · 0.730801 | `entree.n.02` · 0.730801 | `entree.n.02` · 0.730801 |
| 13 · point | `point.n.25` · 0.653627 | `point.n.25` · 0.653627 | `point.n.25` · 0.653627 |
| 14 · passwords | `password.n.01` · 0.794532 | `password.n.01` · 0.794532 | `password.n.01` · 0.794532 |
| 17 · people | `people.n.01` · 0.772024 | `people.n.01` · 0.772024 | `smart_money.n.03` · 0.780404 |
| 18 · running | `run.v.13` · 0.719842 | `run.v.13` · 0.719842 | `run.v.13` · 0.719842 |
| 20 · shop | `shop.n.01` · 0.782505 | `shop.n.01` · 0.782505 | `shop.n.01` · 0.782505 |
| 22 · experience | `know.v.05` · 0.742357 | `know.v.05` · 0.742357 | `know.v.05` · 0.742357 |
| 25 · internet | `internet.n.01` · 0.775375 | `internet.n.01` · 0.775375 | `internet.n.01` · 0.775375 |
| 26 · access | `access.n.02` · 0.741091 | `access.n.02` · 0.741091 | `access.n.02` · 0.741091 |

Dictionary meanings of these highest matches:

- `writer.n.01`: writes (books or stories or articles or the like) professionally (for pay)
- `desire.v.01`: feel or have a desire for; want strongly
- `change.v.01`: cause to change; make different; cause a transformation
- `coffee.n.01`: a beverage consisting of an infusion of ground coffee beans
- `shop.n.01`: a mercantile establishment for the retail sale of goods or services
- `router.n.02`: (computer science) a device that forwards data packets between computer networks
- `modem.n.01`: (from a combination of MOdulate and DEModulate) electronic equipment consisting of a device used to connect computers by a telephone line
- `wireless.a.01`: having no wires
- `entree.n.02`: the right to enter
- `point.n.25`: a wall socket
- `password.n.01`: a secret word or phrase known only to a restricted group
- `people.n.01`: (plural) any group of human beings (men or women or children) collectively
- `smart_money.n.03`: people who are highly experienced or who have inside information
- `run.v.13`: be operating, running or functioning
- `know.v.05`: have firsthand knowledge of states, situations, emotions, or sensations
- `internet.n.01`: a computer network consisting of a worldwide network of computer networks that use the TCP/IP network protocols to facilitate data transmission and exchange
- `access.n.02`: the right to obtain or make use of or take advantage of something (as services or membership)

## Row 350 · N100 · V940

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

Analysis: The source is cutting sirloin into steaks. None of cattle, complaining or beef stroganoff is a faithful replacement for that meat subject, though cattle is related and stroganoff returns to the broad food family. Preparation as a formulated substance misses the activity in all conditions. Shortness alone has not been isolated as the cause.

| Word index · text | Saved | Surface | Unrestricted |
| --- | --- | --- | --- |
| 0 · Beef | `beef.n.01` · 0.545082 | `gripe.v.01` · 0.569100 | `beef_stroganoff.n.01` · 0.681332 |
| 2 · steak | `steak.n.01` · 0.824985 | `steak.n.01` · 0.824985 | `steak.n.01` · 0.824985 |
| 3 · preparation | `formulation.n.01` · 0.732952 | `formulation.n.01` · 0.732952 | `formulation.n.01` · 0.732952 |

Dictionary meanings of these highest matches:

- `beef.n.01`: cattle that are reared for their meat
- `gripe.v.01`: complain
- `beef_stroganoff.n.01`: sauteed strips of beef and mushrooms in sour cream sauce served with noodles
- `steak.n.01`: a slice of meat cut from the fleshy part of an animal or large fish
- `formulation.n.01`: a substance prepared according to a formula

## Row 375 · N047 · V364

> ⟦Cleaning out⟧ the ⟦ashes⟧ ⟦to now put in⟧ the ⟦bread pans⟧. It remains very hot for some time. Takes about 5-6 min for them to cook. https://video.nostr.build/1287907c5686c9eb72895eb5c52a9869aaff5ed6c46db7041ed4d8797635af04.mp4 https://image.nostr.build/ac895487f166b3e2a6bfb161d4bc0fca1a8720386968b3187981b6dcbf18d7ae.jpg https://image.nostr.build/9a73232d8b89163a07272467dab427cfe8549181b9a74da654d353b4b68ed6ce.jpg  nostr:note1tc57qmd25gu4ddgqwyuk3my7endvrxvwgdtqldvd066ml5f885tqps5a3c

Encoded description: Baking bread in pans after cleaning ashes out of the baking space.

Analysis: Bread, pans, cleaning, ashes and baking are preserved locally. Baking versus oven-baking is not a clear substantive failure; the original describes hot space, ashes and pans without explicitly naming an oven. A cookie sheet is not supported by the bread-pan source and does not mean the act of baking.

| Word index · text | Saved | Surface | Unrestricted |
| --- | --- | --- | --- |
| 0 · Baking | `baking.n.01` · 0.604723 | `bake.v.01` · 0.691766 | `ovenbake.v.01` · 0.702443 |
| 1 · bread | `bread.n.01` · 0.828937 | `bread.n.01` · 0.828937 | `bread.n.01` · 0.828937 |
| 3 · pans | `pan.n.01` · 0.815840 | `pan.n.01` · 0.815840 | `pan.n.01` · 0.815840 |
| 5 · cleaning | `clean.v.01` · 0.786481 | `clean.v.01` · 0.786481 | `clean.v.01` · 0.786481 |
| 6 · ashes | `ash.n.01` · 0.760834 | `ash.n.01` · 0.760834 | `ash.n.01` · 0.760834 |
| 10 · baking | `baking.n.02` · 0.680590 | `baking.n.02` · 0.680590 | `cookie_sheet.n.01` · 0.687902 |
| 11 · space | `space.n.03` · 0.768148 | `space.n.03` · 0.768148 | `space.n.03` · 0.768148 |

Dictionary meanings of these highest matches:

- `baking.n.01`: making bread or cake or pastry etc.
- `bake.v.01`: cook and make edible by putting in a hot oven
- `ovenbake.v.01`: bake in an oven
- `bread.n.01`: food made from dough of flour or meal and usually raised with yeast or baking powder and then baked
- `pan.n.01`: cooking utensil consisting of a wide metal vessel
- `clean.v.01`: make clean by removing dirt, filth, or unwanted substances from
- `ash.n.01`: the residue that remains when something is burned
- `baking.n.02`: cooking by dry heat in an oven
- `cookie_sheet.n.01`: a cooking utensil consisting of a flat rectangular metal sheet used for baking cookies or biscuits
- `space.n.03`: an area reserved for some particular purpose

## Row 378 · N022 · V152

> This year’s ⟦beets⟧. Vac sealed and ready for the freezer. Not too bad for a 4x4 raised bed. ⟦5 meals⟧ of ⟦sides⟧ in a pinch. I am looking forward to having more garden space but this is good while we are still in a half acre lot in town. https://image.nostr.build/b4349cc1251dccf78990620ee851ad0ae449327da16ac31391e3e71fafdbe65c.jpg https://image.nostr.build/5c7e4ba19bb3c2e98cb57753679d33be2bbad3a07900afc86315c85f80bc46e4.jpg

Encoded description: The author's beet harvest provides side dishes for five meals.

Analysis: Original-word lookup fixes beet from protective boot casing to the vegetable. Unrestricted beet leaves are not established. Side dishes are food portions, not half-carcasses, a spatial side, dishware or serving vessels. The phrase is split into word targets; the original mask itself does communicate sides for meals.

| Word index · text | Saved | Surface | Unrestricted |
| --- | --- | --- | --- |
| 1 · author | `writer.n.01` · 0.734731 | `writer.n.01` · 0.734731 | `writer.n.01` · 0.734731 |
| 3 · beet | `boot.n.04` · 0.488708 | `beet.n.02` · 0.629193 | `beet_green.n.01` · 0.757154 |
| 4 · harvest | `crop.n.01` · 0.778358 | `crop.n.01` · 0.778358 | `crop.n.01` · 0.778358 |
| 5 · provides | `supply.v.01` · 0.777270 | `supply.v.01` · 0.777270 | `supply.v.01` · 0.777270 |
| 6 · side | `side.n.09` · 0.656441 | `side.a.01` · 0.745557 | `side.a.01` · 0.745557 |
| 7 · dishes | `dish.n.01` · 0.769702 | `dish.n.01` · 0.769702 | `serving_dish.n.01` · 0.791865 |
| 10 · meals | `meal.n.01` · 0.834910 | `meal.n.01` · 0.834910 | `meal.n.01` · 0.834910 |

Dictionary meanings of these highest matches:

- `writer.n.01`: writes (books or stories or articles or the like) professionally (for pay)
- `boot.n.04`: protective casing for something that resembles a leg
- `beet.n.02`: round red root vegetable
- `beet_green.n.01`: young leaves of the beetroot
- `crop.n.01`: the yield from plants in a single growing season
- `supply.v.01`: give something useful or necessary to
- `side.n.09`: a lengthwise dressed half of an animal's carcass used for food
- `side.a.01`: located on a side
- `dish.n.01`: a piece of dishware normally used as a container for holding or serving food
- `serving_dish.n.01`: a dish used for serving food
- `meal.n.01`: the food served and eaten at one time

## Row 405 · N069 · V610

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

Analysis: Goodness for one's own peace remains the source meaning. Well-being and freedom from disputes are plausible nearby readings, not decisive fidelity successes. Unrestricted national/ethnic peoples adds an unsupported collective identity; the original simply refers to others.

| Word index · text | Saved | Surface | Unrestricted |
| --- | --- | --- | --- |
| 1 · good | `beneficial.s.01` · 0.804187 | `beneficial.s.01` · 0.804187 | `beneficial.s.01` · 0.804187 |
| 5 · own | `own.s.01` · 0.807172 | `own.s.01` · 0.807172 | `own.s.01` · 0.807172 |
| 6 · peace | `peace.n.02` · 0.788001 | `peace.n.02` · 0.788001 | `peace.n.02` · 0.788001 |
| 7 · rather | `rather.r.01` · 0.812393 | `rather.r.01` · 0.812393 | `rather.r.01` · 0.812393 |
| 10 · other | `other.a.01` · 0.725506 | `other.a.01` · 0.725506 | `other.a.01` · 0.725506 |
| 11 · people | `people.n.01` · 0.758457 | `people.n.01` · 0.758457 | `peoples.n.01` · 0.759818 |
| 13 · sake | `sake.n.01` · 0.797903 | `sake.n.01` · 0.797903 | `sake.n.01` · 0.797903 |

Dictionary meanings of these highest matches:

- `beneficial.s.01`: promoting or enhancing well-being
- `own.s.01`: belonging to or on behalf of a specified person (especially yourself); preceded by a possessive
- `peace.n.02`: harmonious relations; freedom from disputes
- `rather.r.01`: on the contrary
- `other.a.01`: not the same one or ones already mentioned or implied; - the White Queen
- `people.n.01`: (plural) any group of human beings (men or women or children) collectively
- `peoples.n.01`: the human beings of a particular nation or community or ethnic group
- `sake.n.01`: a reason for wanting something done

## Row 468 · N013 · V100

> Got the ⟦stock pots rolling⟧ today for a batch of ⟦chicken stock⟧. We save carcasses when we butcher and a couple of times a year do this. I’ll ⟦pressure can⟧ it and ⟦store in the pantry⟧. Should get around 25 quarts with this batch.
> #grownostr
> #homesteading
> #foodsecurity
> #foodstr https://image.nostr.build/aead0ba70aa9ec698013666afe87bb76d74d9a19dbb7b93ceb0de953fa2e3386.jpg

Encoded description: Pressure-canning homemade chicken stock for pantry storage is a form of food preservation.

Analysis: Original-word lookup supplies canning and homemade. Broth, pantry, food and preservation are useful retained meanings. A cannery, commercial storage enterprise, refrigerated storage or specially young chickens are not established. Preservation by pressure-canning remains clear without a perfect sense for every word.

| Word index · text | Saved | Surface | Unrestricted |
| --- | --- | --- | --- |
| 0 · Pressure | `press.n.09` · 0.647262 | `press.n.09` · 0.647262 | `press.n.09` · 0.647262 |
| 2 · canning | — | `can.v.01` · 0.645152 | `cannery.n.01` · 0.692435 |
| 3 · homemade | — | `homemade.a.01` · 0.848421 | `homemade.a.01` · 0.848421 |
| 4 · chicken | `chicken.n.01` · 0.816733 | `chicken.n.01` · 0.816733 | `spring_chicken.n.02` · 0.837499 |
| 5 · stock | `broth.n.01` · 0.725257 | `broth.n.01` · 0.725257 | `broth.n.01` · 0.725257 |
| 7 · pantry | `pantry.n.01` · 0.845062 | `pantry.n.01` · 0.845062 | `pantry.n.01` · 0.845062 |
| 8 · storage | `storage.n.03` · 0.815215 | `storage.n.03` · 0.815215 | `cold_storage.n.02` · 0.855036 |
| 11 · form | `kind.n.01` · 0.754599 | `kind.n.01` · 0.754599 | `kind.n.01` · 0.754599 |
| 13 · food | `food.n.01` · 0.789954 | `food.n.01` · 0.789954 | `food.n.01` · 0.789954 |
| 14 · preservation | `preservation.n.01` · 0.700743 | `preservation.n.01` · 0.700743 | `preservation.n.01` · 0.700743 |

Dictionary meanings of these highest matches:

- `press.n.09`: the act of pressing; the exertion of pressure
- `can.v.01`: preserve in a can or tin
- `cannery.n.01`: a factory where food is canned
- `homemade.a.01`: made or produced in the home or by yourself
- `chicken.n.01`: the flesh of a chicken used for food
- `spring_chicken.n.02`: a young chicken having tender meat
- `broth.n.01`: liquid in which meat and vegetables are simmered; used as a basis for e.g. soups or sauces
- `pantry.n.01`: a small storeroom for storing foods or wines
- `storage.n.03`: the commercial enterprise of storing goods and materials
- `cold_storage.n.02`: refrigerated storage for preservation
- `kind.n.01`: a category of things distinguished by some common characteristic or quality
- `food.n.01`: any substance that can be metabolized by an animal to give energy and build tissue
- `preservation.n.01`: the activity of protecting something from loss or danger

## Row 544 · N096 · V885

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

Analysis: Original-word lookup supplies tomatoes and simmering. Unrestricted frying is a useful broader match for sautéing; sauce is also a subject supported by the recipe, although it is not identical to the spaghetti token. Bologna sausage, plum tomatoes, basil thyme, soy sauce and nutrient fortification introduce unsupported identities or purposes. The two targets still empty under surface lookup must not be automatically counted as recovered merely because unrestricted matching returns something.

| Word index · text | Saved | Surface | Unrestricted |
| --- | --- | --- | --- |
| 1 · method | `method.n.01` · 0.796874 | `method.n.01` · 0.796874 | `method.n.01` · 0.796874 |
| 3 · preparing | `cook.v.02` · 0.791895 | `cook.v.02` · 0.791895 | `cook.v.02` · 0.791895 |
| 4 · spaghetti | `spaghetti.n.01` · 0.706384 | `spaghetti.n.01` · 0.706384 | `spaghetti_sauce.n.01` · 0.746320 |
| 5 · Bolognaise | — | — | `bologna.n.02` · 0.668720 |
| 7 · sautéing | — | — | `frying.n.01` · 0.796873 |
| 8 · vegetables | `vegetable.n.01` · 0.773412 | `vegetable.n.01` · 0.773412 | `vegetable.n.01` · 0.773412 |
| 10 · gently | `gently.r.01` · 0.785732 | `gently.r.01` · 0.785732 | `gently.r.01` · 0.785732 |
| 11 · frying | `frying.n.01` · 0.856687 | `frying.n.01` · 0.856687 | `frying.n.01` · 0.856687 |
| 12 · beef | `beef.n.02` · 0.804644 | `beef.n.02` · 0.804644 | `beef.n.02` · 0.804644 |
| 14 · adding | `add.v.01` · 0.720059 | `add.v.01` · 0.720059 | `fortify.v.04` · 0.726623 |
| 15 · tomatoes | — | `tomato.n.01` · 0.820750 | `plum_tomato.n.02` · 0.831517 |
| 17 · water | `water.n.01` · 0.752058 | `water.n.01` · 0.752058 | `water.n.01` · 0.752058 |
| 19 · basil | `basil.n.03` · 0.629954 | `basil.n.03` · 0.629954 | `basil_thyme.n.01` · 0.738908 |
| 22 · simmering | — | `simmer.v.01` · 0.790283 | `simmer.v.01` · 0.790283 |
| 24 · sauce | `sauce.n.01` · 0.799509 | `sauce.n.01` · 0.799509 | `chinese_brown_sauce.n.01` · 0.825067 |

Dictionary meanings of these highest matches:

- `method.n.01`: a way of doing something, especially a systematic way; implies an orderly logical arrangement (usually in steps)
- `cook.v.02`: prepare for eating by applying heat
- `spaghetti.n.01`: spaghetti served with a tomato sauce
- `spaghetti_sauce.n.01`: any of numerous sauces for spaghetti or other kinds of pasta
- `bologna.n.02`: large smooth-textured smoked sausage of beef and veal and pork
- `frying.n.01`: cooking in fat or oil in a pan or griddle
- `vegetable.n.01`: edible seeds or roots or stems or leaves or bulbs or tubers or nonsweet fruits of any of numerous herbaceous plant
- `gently.r.01`: in a gradual manner
- `beef.n.02`: meat from an adult domestic bovine
- `add.v.01`: make an addition (to); join or combine or unite with others; increase the quality, quantity, size or scope of
- `fortify.v.04`: add nutrients to
- `tomato.n.01`: mildly acid red or yellow pulpy fruit eaten as a vegetable
- `plum_tomato.n.02`: a kind of cherry tomato that is frequently used in cooking rather than eaten raw
- `water.n.01`: binary compound that occurs at room temperature as a clear colorless odorless tasteless liquid; freezes into ice below 0 degrees centigrade and boils above 100 degrees centigrade; widely used as a solvent
- `basil.n.03`: leaves of the common basil; used fresh or dried
- `basil_thyme.n.01`: fragrant European mint having clusters of small violet-and-white flowers; naturalized especially in eastern North America
- `simmer.v.01`: boil slowly at low temperature
- `sauce.n.01`: flavorful relish or dressing or topping served as an accompaniment to food
- `chinese_brown_sauce.n.01`: a sauce based on soy sauce

## Row 572 · N094 · V852

> ⟦Decafe coffee drinkers⟧ are the purist coffee enthusiasts of them all as they do it ⟦for the experience⟧ and flavour. Unlike the caffeine addicted heathens. Change my mind.

Encoded description: Decaffeinated-coffee drinkers drink coffee for the experience of drinking coffee.

Analysis: Coffee, liquid consumption and experienced events are retained. Original-word lookup supplies decaffeination. Drinking as a noun versus a verb does not create a substantive topic failure. This is a second description of N094, not an independent second note.

| Word index · text | Saved | Surface | Unrestricted |
| --- | --- | --- | --- |
| 0 · Decaffeinated | — | `decaffeinate.v.01` · 0.690938 | `decaffeinate.v.01` · 0.690938 |
| 2 · coffee | `coffee.n.01` · 0.813838 | `coffee.n.01` · 0.813838 | `coffee.n.01` · 0.813838 |
| 3 · drinkers | `drinker.n.01` · 0.857162 | `drinker.n.01` · 0.857162 | `drinker.n.01` · 0.857162 |
| 4 · drink | `drink.v.01` · 0.795055 | `drink.v.01` · 0.795055 | `drink.v.01` · 0.795055 |
| 5 · coffee | `coffee.n.01` · 0.842690 | `coffee.n.01` · 0.842690 | `coffee.n.01` · 0.842690 |
| 8 · experience | `experience.n.03` · 0.764595 | `experience.n.03` · 0.764595 | `experience.n.03` · 0.764595 |
| 10 · drinking | `drink.v.01` · 0.744936 | `drinking.n.01` · 0.792518 | `drinking.n.01` · 0.792518 |
| 11 · coffee | `coffee.n.01` · 0.834140 | `coffee.n.01` · 0.834140 | `coffee.n.01` · 0.834140 |

Dictionary meanings of these highest matches:

- `decaffeinate.v.01`: remove caffeine from (coffee)
- `coffee.n.01`: a beverage consisting of an infusion of ground coffee beans
- `drinker.n.01`: a person who drinks liquids
- `drink.v.01`: take in liquids
- `experience.n.03`: an event as apprehended
- `drinking.n.01`: the act of consuming liquids

## Row 673 · N076 · V709

> Tandori spice chik with somo sexi yogo. On pure fire with best handmade wild rose wine,  #purelife #food #⟦chef⟧ #foodstr no compromise
>
> https://image.nostr.build/d9fce20da7cd056362daca85445508eafc7620bf706788474b1dc28e4875971e.jpg https://image.nostr.build/a648216b769b08347153de65a019f5968d249882cefa912b8c64519d36ca95cf.jpg
> https://image.nostr.build/07e9f6b72f1983601c5f5733b7b889fd6fbe0e8a25e40f131edf1ad299cacd20.jpg

Encoded description: Food preparation and the culinary craft of chefs.

Analysis: Food, preparation, culinary work and chef meanings fit the supplied description. The original mask is only chef inside a hashtag: it supports a culinary topic, not proof of the author's professional employment or a separately described craft practice. Description fit and original-mask support are distinct judgments.

| Word index · text | Saved | Surface | Unrestricted |
| --- | --- | --- | --- |
| 0 · Food | `food.n.01` · 0.728607 | `food.n.01` · 0.728607 | `food.n.01` · 0.728607 |
| 1 · preparation | `preparation.n.01` · 0.736607 | `preparation.n.01` · 0.736607 | `preparation.n.01` · 0.736607 |
| 4 · culinary | `culinary.a.01` · 0.856037 | `culinary.a.01` · 0.856037 | `culinary.a.01` · 0.856037 |
| 5 · craft | `trade.n.02` · 0.763323 | `trade.n.02` · 0.763323 | `trade.n.02` · 0.763323 |
| 7 · chefs | `chef.n.01` · 0.847984 | `chef.n.01` · 0.847984 | `chef.n.01` · 0.847984 |

Dictionary meanings of these highest matches:

- `food.n.01`: any substance that can be metabolized by an animal to give energy and build tissue
- `preparation.n.01`: the activity of putting or setting in order in advance of some act or purpose
- `culinary.a.01`: of or relating to or used in cooking
- `trade.n.02`: the skilled practice of a practical occupation
- `chef.n.01`: a professional cook

## Row 711 · N085 · V786

> #foodstr starting out with a bang this morning. ⟦Brisket on the smoker⟧ for about 3 hours now. https://image.nostr.build/bb53e68600aed853077353e5865e7c7700dfcbd40903b1e0d7852e461d7d70c9.jpg

Encoded description: Cooking brisket on a smoker.

Analysis: Cooking and brisket are useful meanings. The smoker is cooking equipment, not a tobacco user or cigarette user. All three conditions miss this; the inventory limitation must not be disguised by selecting a more specific person sense. Cooking and brisket remain source-supported meanings; whether construction can use them without admitting the wrong person concept remains untested.

| Word index · text | Saved | Surface | Unrestricted |
| --- | --- | --- | --- |
| 0 · Cooking | `cooking.n.01` · 0.704449 | `cook.v.01` · 0.710078 | `cook.v.01` · 0.710078 |
| 1 · brisket | `brisket.n.01` · 0.828788 | `brisket.n.01` · 0.828788 | `brisket.n.01` · 0.828788 |
| 4 · smoker | `smoker.n.01` · 0.649078 | `smoker.n.01` · 0.649078 | `cigarette_smoker.n.01` · 0.749863 |

Dictionary meanings of these highest matches:

- `cooking.n.01`: the act of preparing something (as food) by the application of heat
- `cook.v.01`: prepare a hot meal
- `brisket.n.01`: a cut of meat from the breast or lower chest especially of beef
- `smoker.n.01`: a person who smokes tobacco
- `cigarette_smoker.n.01`: a smoker of cigarettes

## Row 866 · N089 · V806

> Gm nostr
>
> ⟦Bread⟧ superstition requires ⟦salt⟧ to be added at a distance from ⟦yeast⟧ before ⟦mixing⟧ 🤔
>
> https://image.nostr.build/cc4282a3aa0bc2b42942e1f9e1e6a5cbd9db22ec6d82cee2ef6a7ff665cbe63e.jpg

Encoded description: Bread preparation involving salt, yeast, and mixing.

Analysis: The source concerns bread ingredients and mixing. Surface lookup switches bread to covering something in crumbs; unrestricted restores the bread family but invents buns and a compressed yeast cake. Preparation as a formulated substance is not the activity. Salt and mixing remain useful. These are not tests of preserving exact causal relationships.

| Word index · text | Saved | Surface | Unrestricted |
| --- | --- | --- | --- |
| 0 · Bread | `bread.n.01` · 0.635696 | `bread.v.01` · 0.651334 | `bun.n.01` · 0.660457 |
| 1 · preparation | `formulation.n.01` · 0.815809 | `formulation.n.01` · 0.815809 | `formulation.n.01` · 0.815809 |
| 2 · involving | `necessitate.v.01` · 0.761333 | `necessitate.v.01` · 0.761333 | `necessitate.v.01` · 0.761333 |
| 3 · salt | `salt.n.02` · 0.849297 | `salt.n.02` · 0.849297 | `salt.n.02` · 0.849297 |
| 5 · yeast | `yeast.n.02` · 0.577178 | `yeast.n.02` · 0.577178 | `yeast_cake.n.01` · 0.743455 |
| 8 · mixing | `mix.n.03` · 0.732699 | `mix.n.03` · 0.732699 | `mix.n.03` · 0.732699 |

Dictionary meanings of these highest matches:

- `bread.n.01`: food made from dough of flour or meal and usually raised with yeast or baking powder and then baked
- `bread.v.01`: cover with bread crumbs
- `bun.n.01`: small rounded bread either plain or sweet
- `formulation.n.01`: a substance prepared according to a formula
- `necessitate.v.01`: require as useful, just, or proper
- `salt.n.02`: white crystalline form of especially sodium chloride used to season and preserve food
- `yeast.n.02`: any of various single-celled fungi that reproduce asexually by budding or division
- `yeast_cake.n.01`: small cake of compressed moist yeast
- `mix.n.03`: the act of mixing together

## Row 904 · N022 · V149

> ⟦This year’s beets⟧. Vac sealed and ⟦ready for the freezer⟧. Not too bad for a 4x4 ⟦raised bed⟧. 5 meals of sides in a pinch. I am looking forward to having more garden space but this is good while we are still in a half acre lot in town. https://image.nostr.build/b4349cc1251dccf78990620ee851ad0ae449327da16ac31391e3e71fafdbe65c.jpg https://image.nostr.build/5c7e4ba19bb3c2e98cb57753679d33be2bbad3a07900afc86315c85f80bc46e4.jpg

Encoded description: The author is preparing this year's garden-grown beets for preservation by freezing.

Analysis: Garden, cultivated beets and preservation are useful source subjects; a root-versus-plant dictionary distinction need not have one mandated answer. Unrestricted beet leaves are not established. Preparing written/spoken delivery is wrong under every condition. The original supports readiness for freezer preservation, not necessarily that freezing has already happened; the physical freezing topic is supported.

| Word index · text | Saved | Surface | Unrestricted |
| --- | --- | --- | --- |
| 1 · author | `writer.n.01` · 0.750907 | `writer.n.01` · 0.750907 | `writer.n.01` · 0.750907 |
| 3 · preparing | `prepare.v.03` · 0.773033 | `prepare.v.03` · 0.773033 | `prepare.v.03` · 0.773033 |
| 5 · year | `year.n.02` · 0.648993 | `year.n.02` · 0.648993 | `year.n.02` · 0.648993 |
| 7 · garden | `garden.n.01` · 0.818545 | `garden.n.01` · 0.818545 | `garden.n.01` · 0.818545 |
| 9 · grown | `grow.v.07` · 0.767674 | `grow.v.07` · 0.767674 | `grow.v.07` · 0.767674 |
| 10 · beets | `beet.n.01` · 0.631819 | `beet.n.01` · 0.631819 | `beet_green.n.01` · 0.749063 |
| 12 · preservation | `preservation.n.01` · 0.772101 | `preservation.n.01` · 0.772101 | `preservation.n.01` · 0.772101 |
| 14 · freezing | — | `freeze.n.01` · 0.786979 | `freeze.n.01` · 0.787131 |

Dictionary meanings of these highest matches:

- `writer.n.01`: writes (books or stories or articles or the like) professionally (for pay)
- `prepare.v.03`: to prepare verbally, either for written or spoken delivery
- `year.n.02`: a period of time occupying a regular part of a calendar year that is used for some particular activity
- `garden.n.01`: a plot of ground where plants are cultivated
- `grow.v.07`: cultivate by growing, often involving improvements by means of agricultural techniques
- `beet.n.01`: biennial Eurasian plant usually having a swollen edible root; widely cultivated as a food crop
- `beet_green.n.01`: young leaves of the beetroot
- `preservation.n.01`: the activity of protecting something from loss or danger
- `freeze.n.01`: the withdrawal of heat to change something from a liquid to a solid
