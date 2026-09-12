# SGC03 source evidence

Unchanged complete notes, masks, descriptions and native graph edges.
Brackets mark the source fragments; each complete fragment list is also saved.
Descriptions are frozen parser inputs, not new annotations.

## Row 88

N094

> ⟦Decafe coffee drinkers⟧ are the purist coffee enthusiasts of them all as they do it ⟦for⟧ the ⟦experience⟧ and ⟦flavour⟧. ⟦Unlike⟧ the ⟦caffeine addicted⟧ heathens. Change my mind.

**Frozen description:** Decaffeinated-coffee drinkers drink coffee for its experience and flavour rather than to satisfy a caffeine addiction.

**Exact fragments:** ["Decafe coffee drinkers", "for", "experience", "flavour", "Unlike", "caffeine addicted"]

**Native edges:**

- person.n.01 → Role → decaffeinated-coffee_drinker.n.01
- drink.v.01 → Agent → person.n.01
- drink.v.01 → Time → fourth_dimension.n.01
- drink.v.01 → Patient → coffee.n.01
- drink.v.01 → Beneficiary → entity.n.01
- experience.n.01 → Creator → entity.n.01
- entity.n.01 → Sub → experience.n.01
- entity.n.01 → Sub → spirit.n.02
- satisfy.v.01 → Agent → decaffeinated-coffee_drinker.n.01

## Row 91

N039

> Well the ⟦parade was rained out⟧ and umbrellas were ruined.
> 
> ⟦Next rounds of storms⟧ look like they ⟦will hit just in time for grilling out dinner⟧.
> 
> ⟦Third round⟧ is ⟦scheduled for when we are supposed to have fireworks⟧.

**Frozen description:** Rain and successive rounds of storms disrupt or threaten a parade, outdoor dinner grilling, and planned fireworks.

**Exact fragments:** ["parade was rained out", "Next rounds of storms", "will hit just in time for grilling out dinner", "Third round", "scheduled for when we are supposed to have fireworks"]

**Native edges:**

- entity.n.01 → Sub → rain.n.01
- entity.n.01 → Sub → round.n.04
- round.n.04 → Attribute → consecutive.s.02
- round.n.04 → PartOf → storm.n.01
- interrupt.v.01 → Causer → entity.n.01
- interrupt.v.01 → Time → fourth_dimension.n.01
- interrupt.v.01 → Theme → parade.n.01
- grilling.v.01 → Attribute → outdoor.n.01
- grilling.v.01 → MadeOf → dinner.n.01
- entity.n.01 → Sub → parade.n.01
- entity.n.01 → Sub → grilling.v.01

## Row 187

N026

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

**Frozen description:** The author washed many dishes used while preparing tomatoes for salsa, making yogurt, bagging chicken meat, and making chicken stock.

**Exact fragments:** ["prepared", "tomato’s to make salsa", "Made", "yogurt", "bagged the chicken meat", "made", "chicken stock", "cleaned", "many dishes", "i used doing all the above"]

Native output is malformed and remains excluded.

## Row 345

N065

> ⟦Coffee shop⟧ I liked now has a “No laptops or tablets” rule on weekends. This is what happens if you let hipsters get too successful. ⟦Felt like changing their router/ap passwords so they⟧ could ⟦experience⟧ the true ⟦freedom from internet⟧, but I simply went to another coffee shop and will remove this one from rotation. Personal growth on display.

**Frozen description:** The author wanted to change the coffee shop's router or wireless access point passwords so the people running the shop would experience being without internet access.

**Exact fragments:** ["Coffee shop", "Felt like changing their router/ap passwords so they", "experience", "freedom from internet"]

Native output is malformed and remains excluded.

## Row 350

N100

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

**Frozen description:** Beef and steak preparation.

**Exact fragments:** ["sirloin", "cut", "steaks"]

**Native edges:**

- event.v.01 → Participant → steak.n.01
- entity.n.01 → Sub → beef.n.01
- entity.n.01 → Sub → preparation.n.01
- preparation.n.01 → MadeOf → steak.n.01

## Row 375

N047

> ⟦Cleaning out⟧ the ⟦ashes⟧ ⟦to now put in⟧ the ⟦bread pans⟧. It remains very hot for some time. Takes about 5-6 min for them to cook. https://video.nostr.build/1287907c5686c9eb72895eb5c52a9869aaff5ed6c46db7041ed4d8797635af04.mp4 https://image.nostr.build/ac895487f166b3e2a6bfb161d4bc0fca1a8720386968b3187981b6dcbf18d7ae.jpg https://image.nostr.build/9a73232d8b89163a07272467dab427cfe8549181b9a74da654d353b4b68ed6ce.jpg  nostr:note1tc57qmd25gu4ddgqwyuk3my7endvrxvwgdtqldvd066ml5f885tqps5a3c

**Frozen description:** Baking bread in pans after cleaning ashes out of the baking space.

**Exact fragments:** ["Cleaning out", "ashes", "to now put in", "bread pans"]

Native output is malformed and remains excluded.

## Row 378

N022

> This year’s ⟦beets⟧. Vac sealed and ready for the freezer. Not too bad for a 4x4 raised bed. ⟦5 meals⟧ of ⟦sides⟧ in a pinch. I am looking forward to having more garden space but this is good while we are still in a half acre lot in town. https://image.nostr.build/b4349cc1251dccf78990620ee851ad0ae449327da16ac31391e3e71fafdbe65c.jpg https://image.nostr.build/5c7e4ba19bb3c2e98cb57753679d33be2bbad3a07900afc86315c85f80bc46e4.jpg 

**Frozen description:** The author's beet harvest provides side dishes for five meals.

**Exact fragments:** ["beets", "5 meals", "sides"]

**Native edges:**

- person.n.01 → Role → writer.n.01
- harvest.n.02 → Creator → person.n.01
- harvest.n.02 → Attribute → beet.n.02
- provide.v.02 → Causer → harvest.n.02
- provide.v.02 → Time → fourth_dimension.n.01
- provide.v.02 → Theme → dish.n.01
- provide.v.02 → Duration → meal.n.01
- dish.n.01 → Theme → side.n.01
- meal.n.01 → Quantity → measure.n.02

## Row 405

N069

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

**Frozen description:** Being good for one's own peace rather than for other people's sake.

**Exact fragments:** ["Be good, not for others sake, but for your own peace"]

**Native edges:**

- entity.n.01 → Attribute → good.a.01
- good.a.01 → Theme → peace.n.01
- peace.n.01 → Creator → person.n.01
- entity.n.01 → EQU → good.a.01
- entity.n.01 → Theme → sake.n.01
- person.n.01 → NEQ → person.n.01
- sake.n.01 → Creator → person.n.01

## Row 468

N013

> Got the ⟦stock pots rolling⟧ today for a batch of ⟦chicken stock⟧. We save carcasses when we butcher and a couple of times a year do this. I’ll ⟦pressure can⟧ it and ⟦store in the pantry⟧. Should get around 25 quarts with this batch. 
> #grownostr
> #homesteading
> #foodsecurity
> #foodstr https://image.nostr.build/aead0ba70aa9ec698013666afe87bb76d74d9a19dbb7b93ceb0de953fa2e3386.jpg 

**Frozen description:** Pressure-canning homemade chicken stock for pantry storage is a form of food preservation.

**Exact fragments:** ["stock pots rolling", "chicken stock", "pressure can", "store in the pantry"]

**Native edges:**

- pressure-canning.v.01 → Theme → stock.n.01
- stock.n.01 → Attribute → homemade.a.01
- stock.n.01 → MadeOf → chicken.n.02
- stock.n.01 → Asset → storage.n.01
- storage.n.01 → Theme → pantry.n.01
- be.v.01 → Theme → homemade.a.01
- be.v.01 → Time → fourth_dimension.n.01
- be.v.01 → Co-Theme → form.n.01
- form.n.01 → Content → preservation.n.01
- preservation.n.01 → Theme → food.n.01

## Row 544

N096

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

**Frozen description:** A method for preparing spaghetti Bolognaise by sautéing vegetables, gently frying beef, adding tomatoes, water and basil, and simmering the sauce.

**Exact fragments:** ["Spaghetti Bolognaise", "sauté", "onion, celery and carrot", "Gently fry beef", "add", "tomatoes", "water", "basil", "Simmer"]

Native output is malformed and remains excluded.

## Row 572

N094

> ⟦Decafe coffee drinkers⟧ are the purist coffee enthusiasts of them all as they do it ⟦for the experience⟧ and flavour. Unlike the caffeine addicted heathens. Change my mind.

**Frozen description:** Decaffeinated-coffee drinkers drink coffee for the experience of drinking coffee.

**Exact fragments:** ["Decafe coffee drinkers", "for the experience"]

**Native edges:**

- person.n.01 → Role → decaffeinated-coffee_drinker.n.01
- drink.v.01 → Agent → person.n.01
- drink.v.01 → Time → fourth_dimension.n.01
- drink.v.01 → Patient → coffee.n.01
- drink.v.01 → Goal → experience.n.01
- experience.n.01 → Theme → drink.v.01
- drink.v.01 → Patient → entity.n.01
- drink.v.01 → Result → coffee.n.01

## Row 673

N076

> Tandori spice chik with somo sexi yogo. On pure fire with best handmade wild rose wine,  #purelife #food #⟦chef⟧ #foodstr no compromise 
> 
> https://image.nostr.build/d9fce20da7cd056362daca85445508eafc7620bf706788474b1dc28e4875971e.jpg https://image.nostr.build/a648216b769b08347153de65a019f5968d249882cefa912b8c64519d36ca95cf.jpg
> https://image.nostr.build/07e9f6b72f1983601c5f5733b7b889fd6fbe0e8a25e40f131edf1ad299cacd20.jpg

**Frozen description:** Food preparation and the culinary craft of chefs.

**Exact fragments:** ["chef"]

**Native edges:**

- event.v.01 → Participant → entity.n.01
- preparation.n.01 → MadeOf → food.n.02
- entity.n.01 → Sub → preparation.n.01
- entity.n.01 → Sub → trade.n.02
- trade.n.02 → Attribute → culinary.a.01
- person.n.01 → Attribute → trade.n.02
- person.n.01 → Role → chef.n.01

## Row 711

N085

> #foodstr starting out with a bang this morning. ⟦Brisket on the smoker⟧ for about 3 hours now. https://image.nostr.build/bb53e68600aed853077353e5865e7c7700dfcbd40903b1e0d7852e461d7d70c9.jpg 

**Frozen description:** Cooking brisket on a smoker.

**Exact fragments:** ["Brisket on the smoker"]

**Native edges:**

- event.v.01 → Participant → cook.v.01
- cook.v.01 → Theme → brisket.n.01
- cook.v.01 → Beneficiary → person.n.01
- person.n.01 → Role → smoker.n.01

## Row 866

N089

> Gm nostr
> 
> ⟦Bread⟧ superstition requires ⟦salt⟧ to be added at a distance from ⟦yeast⟧ before ⟦mixing⟧ 🤔 
> 
> https://image.nostr.build/cc4282a3aa0bc2b42942e1f9e1e6a5cbd9db22ec6d82cee2ef6a7ff665cbe63e.jpg

**Frozen description:** Bread preparation involving salt, yeast, and mixing.

**Exact fragments:** ["Bread", "salt", "yeast", "mixing"]

**Native edges:**

- event.v.01 → Participant → involve.v.01
- preparation.n.01 → MadeOf → bread.n.01
- involve.v.01 → Agent → preparation.n.01
- involve.v.01 → Theme → salt.n.01
- entity.n.01 → Sub → salt.n.01
- entity.n.01 → Sub → yeast.n.02
- entity.n.01 → Sub → mix.n.03

## Row 904

N022

> ⟦This year’s beets⟧. Vac sealed and ⟦ready for the freezer⟧. Not too bad for a 4x4 ⟦raised bed⟧. 5 meals of sides in a pinch. I am looking forward to having more garden space but this is good while we are still in a half acre lot in town. https://image.nostr.build/b4349cc1251dccf78990620ee851ad0ae449327da16ac31391e3e71fafdbe65c.jpg https://image.nostr.build/5c7e4ba19bb3c2e98cb57753679d33be2bbad3a07900afc86315c85f80bc46e4.jpg 

**Frozen description:** The author is preparing this year's garden-grown beets for preservation by freezing.

**Exact fragments:** ["This year’s beets", "ready for the freezer", "raised bed"]

**Native edges:**

- person.n.01 → Role → writer.n.01
- fix.v.12 → Agent → person.n.01
- fix.v.12 → Time → fourth_dimension.n.01
- fix.v.12 → Patient → garden-grown.a.01
- fix.v.12 → Manner → preservation.n.01
- beet.n.02 → Attribute → garden-grown.a.01
- beet.n.02 → PartOf → time.n.01
- beet.n.02 → Goal → preservation.n.01
