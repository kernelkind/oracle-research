# SGC01 complete source evidence

Each section retains the original note and original mask, the unchanged
description supplied to the parser, and its exact output. Numbered senses
are predictions, not accepted meanings. A syntax check is not a semantic judgment.

## Row 88 · N094 · V854

> ⟦Decafe coffee drinkers⟧ are the purist coffee enthusiasts of them all as they do it ⟦for⟧ the ⟦experience⟧ and ⟦flavour⟧. ⟦Unlike⟧ the ⟦caffeine addicted⟧ heathens. Change my mind.

Parser input: Decaffeinated-coffee drinkers drink coffee for its experience and flavour rather than to satisfy a caffeine addiction.

Exact native output:

```text
person.n.01 Role +1 decaffeinated-coffee_drinker.n.01 drink.v.01 Agent -2 Time +1 Patient +2 Beneficiary +5 time.n.08 EQU now coffee.n.01 entity.n.01 experience.n.01 Creator -1 entity.n.01 Sub -1 Sub +1 flavour.n.01 CONTINUATION <1 satisfy.v.01 Agent -8 
```

Syntax check: passed local sequence/reference checks

Predicted concepts:

| Node | Native sense | Dictionary meaning |
|---|---|---|
| 0 | `person.n.01` | a human being |
| 1 | `decaffeinated-coffee_drinker.n.01` | No such sense in cached WordNet 3.0 |
| 2 | `drink.v.01` | take in liquids |
| 3 | `time.n.08` | the fourth coordinate that is required (along with three spatial dimensions) to specify a physical event |
| 4 | `coffee.n.01` | a beverage consisting of an infusion of ground coffee beans |
| 5 | `entity.n.01` | that which is perceived or known or inferred to have its own distinct existence (living or nonliving) |
| 6 | `experience.n.01` | the accumulation of knowledge or skill that results from direct participation in events or activities |
| 7 | `entity.n.01` | that which is perceived or known or inferred to have its own distinct existence (living or nonliving) |
| 8 | `flavour.n.01` | the general atmosphere of a place or situation and the effect that it has on people |
| 9 | `satisfy.v.01` | meet the requirements or expectations of |

Predicted relationships (IDs refer only to this row):

```text
0 — Role → 1
2 — Agent → 0
2 — Time → 3
2 — Patient → 4
2 — Beneficiary → 7
6 — Creator → 5
7 — Sub → 6
7 — Sub → 8
9 — Agent → 1
```

## Row 91 · N039 · V298

> Well the ⟦parade was rained out⟧ and umbrellas were ruined.
> 
> ⟦Next rounds of storms⟧ look like they ⟦will hit just in time for grilling out dinner⟧.
> 
> ⟦Third round⟧ is ⟦scheduled for when we are supposed to have fireworks⟧.

Parser input: Rain and successive rounds of storms disrupt or threaten a parade, outdoor dinner grilling, and planned fireworks.

Exact native output:

```text
rain.n.01 entity.n.01 Sub -1 Sub +2 successive.a.01 AttributeOf +1 round.n.04 PartOf +1 storm.n.01 disrupt.v.01 Causer -4 Time +1 Theme +2 time.n.08 TPR now parade.n.01 outdoor.n.01 dinner.n.01 grilling.v.01 Attribute -2 MadeOf -1 entity.n.01 Sub -4 Sub -1
```

Syntax check: passed local sequence/reference checks

Predicted concepts:

| Node | Native sense | Dictionary meaning |
|---|---|---|
| 0 | `rain.n.01` | water falling in drops from vapor condensed in the atmosphere |
| 1 | `entity.n.01` | that which is perceived or known or inferred to have its own distinct existence (living or nonliving) |
| 2 | `successive.a.01` | in regular succession without gaps |
| 3 | `round.n.04` | (often plural) a series of professional calls (usually in a set order) |
| 4 | `storm.n.01` | a violent weather condition with winds 64-72 knots (11 on the Beaufort scale) and precipitation and thunder and lightning |
| 5 | `disrupt.v.01` | make a break in |
| 6 | `time.n.08` | the fourth coordinate that is required (along with three spatial dimensions) to specify a physical event |
| 7 | `parade.n.01` | a ceremonial procession including people marching |
| 8 | `outdoor.n.01` | No such sense in cached WordNet 3.0 |
| 9 | `dinner.n.01` | the main meal of the day served in the evening or at midday |
| 10 | `grilling.v.01` | No such sense in cached WordNet 3.0 |
| 11 | `entity.n.01` | that which is perceived or known or inferred to have its own distinct existence (living or nonliving) |

Predicted relationships (IDs refer only to this row):

```text
1 — Sub → 0
1 — Sub → 3
3 — Attribute → 2
3 — PartOf → 4
5 — Causer → 1
5 — Time → 6
5 — Theme → 7
10 — Attribute → 8
10 — MadeOf → 9
11 — Sub → 7
11 — Sub → 10
```

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

Parser input: The author washed many dishes used while preparing tomatoes for salsa, making yogurt, bagging chicken meat, and making chicken stock.

Exact native output:

```text
person.n.01 Role +1 author.n.01 wash.v.02 Agent -2 Time +1 Source +2 Manner +5 time.n.08 TPR now dish.n.01 Quantity + use.v.01 Theme -1 Time +1 time.n.08 TPR now prepare.v.01 Agent -7 Theme +1 Goal +2 tomato.n.01 salsa.n.01 make.v.06 Agent -9 Product +2 
```

Syntax check: concept reference outside native sequence: {'source': 10, 'role': 'Product', 'target': 12}

## Row 345 · N065 · V561

> ⟦Coffee shop⟧ I liked now has a “No laptops or tablets” rule on weekends. This is what happens if you let hipsters get too successful. ⟦Felt like changing their router/ap passwords so they⟧ could ⟦experience⟧ the true ⟦freedom from internet⟧, but I simply went to another coffee shop and will remove this one from rotation. Personal growth on display.

Parser input: The author wanted to change the coffee shop's router or wireless access point passwords so the people running the shop would experience being without internet access.

Exact native output:

```text
person.n.01 Role +1 author.n.01 want.v.01 Pivot -2 Time +1 Theme +2 time.n.08 TPR now change.v.01 Agent -4 Theme +2 entity.n.01 person.n.01 run.v.07 Agent -1 Theme +1 shop.n.01 time.n.08 TSU now experience.v.01 Stimulus -4 Time -1 Stimulus +1 be.v.01 Them
```

Syntax check: incomplete relation or context at token 38: Them

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

Parser input: Beef and steak preparation.

Exact native output:

```text
event.v.01 Participant +3 beef.n.01 entity.n.01 Sub -1 Sub +2 steak.n.01 preparation.n.01 MadeOf -1
```

Syntax check: passed local sequence/reference checks

Predicted concepts:

| Node | Native sense | Dictionary meaning |
|---|---|---|
| 0 | `event.v.01` | No such sense in cached WordNet 3.0 |
| 1 | `beef.n.01` | cattle that are reared for their meat |
| 2 | `entity.n.01` | that which is perceived or known or inferred to have its own distinct existence (living or nonliving) |
| 3 | `steak.n.01` | a slice of meat cut from the fleshy part of an animal or large fish |
| 4 | `preparation.n.01` | the activity of putting or setting in order in advance of some act or purpose |

Predicted relationships (IDs refer only to this row):

```text
0 — Participant → 3
2 — Sub → 1
2 — Sub → 4
4 — MadeOf → 3
```

## Row 375 · N047 · V364

> ⟦Cleaning out⟧ the ⟦ashes⟧ ⟦to now put in⟧ the ⟦bread pans⟧. It remains very hot for some time. Takes about 5-6 min for them to cook. https://video.nostr.build/1287907c5686c9eb72895eb5c52a9869aaff5ed6c46db7041ed4d8797635af04.mp4 https://image.nostr.build/ac895487f166b3e2a6bfb161d4bc0fca1a8720386968b3187981b6dcbf18d7ae.jpg https://image.nostr.build/9a73232d8b89163a07272467dab427cfe8549181b9a74da654d353b4b68ed6ce.jpg  nostr:note1tc57qmd25gu4ddgqwyuk3my7endvrxvwgdtqldvd066ml5f885tqps5a3c

Parser input: Baking bread in pans after cleaning ashes out of the baking space.

Exact native output:

```text
entity.n.01 bake.v.02 Agent -1 Theme +1 Destination +2 Manner +3 bread.n.01 pan.n.01 clean.v.01 Agent -5 Theme +1 Source +3 ash.n.01 bake.v.02 Theme +1 space.n.04
```

Syntax check: concept reference outside native sequence: {'source': 4, 'role': 'Agent', 'target': -1}

## Row 378 · N022 · V152

> This year’s ⟦beets⟧. Vac sealed and ready for the freezer. Not too bad for a 4x4 raised bed. ⟦5 meals⟧ of ⟦sides⟧ in a pinch. I am looking forward to having more garden space but this is good while we are still in a half acre lot in town. https://image.nostr.build/b4349cc1251dccf78990620ee851ad0ae449327da16ac31391e3e71fafdbe65c.jpg https://image.nostr.build/5c7e4ba19bb3c2e98cb57753679d33be2bbad3a07900afc86315c85f80bc46e4.jpg 

Parser input: The author's beet harvest provides side dishes for five meals.

Exact native output:

```text
person.n.01 Role +1 author.n.01 beet.n.02 harvest.n.02 Creator -3 Attribute -1 provide.v.02 Causer -1 Time +1 Theme +3 Duration +5 time.n.08 EQU now side.n.01 dish.n.01 Theme -1 quantity.n.01 EQU 5 meal.n.01 Quantity -1
```

Syntax check: passed local sequence/reference checks

Predicted concepts:

| Node | Native sense | Dictionary meaning |
|---|---|---|
| 0 | `person.n.01` | a human being |
| 1 | `author.n.01` | writes (books or stories or articles or the like) professionally (for pay) |
| 2 | `beet.n.02` | round red root vegetable |
| 3 | `harvest.n.02` | the consequence of an effort or activity |
| 4 | `provide.v.02` | give what is desired or needed, especially support, food or sustenance |
| 5 | `time.n.08` | the fourth coordinate that is required (along with three spatial dimensions) to specify a physical event |
| 6 | `side.n.01` | a place within a region identified relative to a center or reference location |
| 7 | `dish.n.01` | a piece of dishware normally used as a container for holding or serving food |
| 8 | `quantity.n.01` | how much there is or how many there are of something that you can quantify |
| 9 | `meal.n.01` | the food served and eaten at one time |

Predicted relationships (IDs refer only to this row):

```text
0 — Role → 1
3 — Creator → 0
3 — Attribute → 2
4 — Causer → 3
4 — Time → 5
4 — Theme → 7
4 — Duration → 9
7 — Theme → 6
9 — Quantity → 8
```

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

Parser input: Being good for one's own peace rather than for other people's sake.

Exact native output:

```text
entity.n.01 good.a.01 AttributeOf -1 Theme +2 person.n.01 peace.n.01 Creator -1 NEGATION <1 entity.n.01 EQU -3 Theme +3 person.n.01 NEQ +1 person.n.01 sake.n.01 Creator -2
```

Syntax check: passed local sequence/reference checks

Predicted concepts:

| Node | Native sense | Dictionary meaning |
|---|---|---|
| 0 | `entity.n.01` | that which is perceived or known or inferred to have its own distinct existence (living or nonliving) |
| 1 | `good.a.01` | having desirable or positive qualities especially those suitable for a thing specified |
| 2 | `person.n.01` | a human being |
| 3 | `peace.n.01` | the state prevailing during the absence of war |
| 4 | `entity.n.01` | that which is perceived or known or inferred to have its own distinct existence (living or nonliving) |
| 5 | `person.n.01` | a human being |
| 6 | `person.n.01` | a human being |
| 7 | `sake.n.01` | a reason for wanting something done |

Predicted relationships (IDs refer only to this row):

```text
0 — Attribute → 1
1 — Theme → 3
3 — Creator → 2
4 — EQU → 1
4 — Theme → 7
5 — NEQ → 6
7 — Creator → 5
```

## Row 468 · N013 · V100

> Got the ⟦stock pots rolling⟧ today for a batch of ⟦chicken stock⟧. We save carcasses when we butcher and a couple of times a year do this. I’ll ⟦pressure can⟧ it and ⟦store in the pantry⟧. Should get around 25 quarts with this batch. 
> #grownostr
> #homesteading
> #foodsecurity
> #foodstr https://image.nostr.build/aead0ba70aa9ec698013666afe87bb76d74d9a19dbb7b93ceb0de953fa2e3386.jpg 

Parser input: Pressure-canning homemade chicken stock for pantry storage is a form of food preservation.

Exact native output:

```text
pressure-canning.v.01 Theme +3 homemade.a.01 AttributeOf +2 chicken.n.02 stock.n.01 MadeOf -1 Asset +2 pantry.n.01 storage.n.01 Theme -1 be.v.01 Theme -5 Time +1 Co-Theme +2 time.n.08 EQU now form.n.01 Content +2 food.n.01 preservation.n.01 Theme -1
```

Syntax check: passed local sequence/reference checks

Predicted concepts:

| Node | Native sense | Dictionary meaning |
|---|---|---|
| 0 | `pressure-canning.v.01` | No such sense in cached WordNet 3.0 |
| 1 | `homemade.a.01` | made or produced in the home or by yourself |
| 2 | `chicken.n.02` | a domestic fowl bred for flesh or eggs; believed to have been developed from the red jungle fowl |
| 3 | `stock.n.01` | the capital raised by a corporation through the issue of shares entitling holders to an ownership interest (equity) |
| 4 | `pantry.n.01` | a small storeroom for storing foods or wines |
| 5 | `storage.n.01` | the act of storing something |
| 6 | `be.v.01` | have the quality of being; (copula, used with an adjective or a predicate noun) |
| 7 | `time.n.08` | the fourth coordinate that is required (along with three spatial dimensions) to specify a physical event |
| 8 | `form.n.01` | the phonological or orthographic sound or appearance of a word that can be used to describe or identify something |
| 9 | `food.n.01` | any substance that can be metabolized by an animal to give energy and build tissue |
| 10 | `preservation.n.01` | the activity of protecting something from loss or danger |

Predicted relationships (IDs refer only to this row):

```text
0 — Theme → 3
3 — Attribute → 1
3 — MadeOf → 2
3 — Asset → 5
5 — Theme → 4
6 — Theme → 1
6 — Time → 7
6 — Co-Theme → 8
8 — Content → 10
10 — Theme → 9
```

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

Parser input: A method for preparing spaghetti Bolognaise by sautéing vegetables, gently frying beef, adding tomatoes, water and basil, and simmering the sauce.

Exact native output:

```text
event.v.01 Participant +1 method.n.01 Beneficiary +2 entity.n.01 prepare.v.01 Agent -1 Product +2 Manner +3 spaghetti.n.01 bolognaise.n.01 MadeOf -1 sauté.v.01 Agent -5 Patient +1 Manner +3 vegetable.n.01 gently.r.01 fry.v.02 Agent -7 Manner -1 Patient +1
```

Syntax check: concept reference outside native sequence: {'source': 9, 'role': 'Patient', 'target': 10}

## Row 572 · N094 · V852

> ⟦Decafe coffee drinkers⟧ are the purist coffee enthusiasts of them all as they do it ⟦for the experience⟧ and flavour. Unlike the caffeine addicted heathens. Change my mind.

Parser input: Decaffeinated-coffee drinkers drink coffee for the experience of drinking coffee.

Exact native output:

```text
person.n.01 Role +1 decaffeinated-coffee_drinker.n.01 drink.v.01 Agent -2 Time +1 Patient +2 Goal +3 time.n.08 EQU now coffee.n.01 experience.n.01 Theme +2 entity.n.01 drink.v.01 Patient -1 Result +1 coffee.n.01
```

Syntax check: passed local sequence/reference checks

Predicted concepts:

| Node | Native sense | Dictionary meaning |
|---|---|---|
| 0 | `person.n.01` | a human being |
| 1 | `decaffeinated-coffee_drinker.n.01` | No such sense in cached WordNet 3.0 |
| 2 | `drink.v.01` | take in liquids |
| 3 | `time.n.08` | the fourth coordinate that is required (along with three spatial dimensions) to specify a physical event |
| 4 | `coffee.n.01` | a beverage consisting of an infusion of ground coffee beans |
| 5 | `experience.n.01` | the accumulation of knowledge or skill that results from direct participation in events or activities |
| 6 | `entity.n.01` | that which is perceived or known or inferred to have its own distinct existence (living or nonliving) |
| 7 | `drink.v.01` | take in liquids |
| 8 | `coffee.n.01` | a beverage consisting of an infusion of ground coffee beans |

Predicted relationships (IDs refer only to this row):

```text
0 — Role → 1
2 — Agent → 0
2 — Time → 3
2 — Patient → 4
2 — Goal → 5
5 — Theme → 7
7 — Patient → 6
7 — Result → 8
```

## Row 673 · N076 · V709

> Tandori spice chik with somo sexi yogo. On pure fire with best handmade wild rose wine,  #purelife #food #⟦chef⟧ #foodstr no compromise 
> 
> https://image.nostr.build/d9fce20da7cd056362daca85445508eafc7620bf706788474b1dc28e4875971e.jpg https://image.nostr.build/a648216b769b08347153de65a019f5968d249882cefa912b8c64519d36ca95cf.jpg
> https://image.nostr.build/07e9f6b72f1983601c5f5733b7b889fd6fbe0e8a25e40f131edf1ad299cacd20.jpg

Parser input: Food preparation and the culinary craft of chefs.

Exact native output:

```text
event.v.01 Participant +3 food.n.02 preparation.n.01 MadeOf -1 entity.n.01 Sub -1 Sub +2 culinary.a.01 AttributeOf +1 craft.n.01 AttributeOf +1 person.n.01 Role +1 chef.n.01
```

Syntax check: passed local sequence/reference checks

Predicted concepts:

| Node | Native sense | Dictionary meaning |
|---|---|---|
| 0 | `event.v.01` | No such sense in cached WordNet 3.0 |
| 1 | `food.n.02` | any solid substance (as opposed to liquid) that is used as a source of nourishment |
| 2 | `preparation.n.01` | the activity of putting or setting in order in advance of some act or purpose |
| 3 | `entity.n.01` | that which is perceived or known or inferred to have its own distinct existence (living or nonliving) |
| 4 | `culinary.a.01` | of or relating to or used in cooking |
| 5 | `craft.n.01` | the skilled practice of a practical occupation |
| 6 | `person.n.01` | a human being |
| 7 | `chef.n.01` | a professional cook |

Predicted relationships (IDs refer only to this row):

```text
0 — Participant → 3
2 — MadeOf → 1
3 — Sub → 2
3 — Sub → 5
5 — Attribute → 4
6 — Attribute → 5
6 — Role → 7
```

## Row 711 · N085 · V786

> #foodstr starting out with a bang this morning. ⟦Brisket on the smoker⟧ for about 3 hours now. https://image.nostr.build/bb53e68600aed853077353e5865e7c7700dfcbd40903b1e0d7852e461d7d70c9.jpg 

Parser input: Cooking brisket on a smoker.

Exact native output:

```text
event.v.01 Participant +1 cook.v.01 Theme +1 Beneficiary +2 brisket.n.01 person.n.01 Role +1 smoker.n.01
```

Syntax check: passed local sequence/reference checks

Predicted concepts:

| Node | Native sense | Dictionary meaning |
|---|---|---|
| 0 | `event.v.01` | No such sense in cached WordNet 3.0 |
| 1 | `cook.v.01` | prepare a hot meal |
| 2 | `brisket.n.01` | a cut of meat from the breast or lower chest especially of beef |
| 3 | `person.n.01` | a human being |
| 4 | `smoker.n.01` | a person who smokes tobacco |

Predicted relationships (IDs refer only to this row):

```text
0 — Participant → 1
1 — Theme → 2
1 — Beneficiary → 3
3 — Role → 4
```

## Row 866 · N089 · V806

> Gm nostr
> 
> ⟦Bread⟧ superstition requires ⟦salt⟧ to be added at a distance from ⟦yeast⟧ before ⟦mixing⟧ 🤔 
> 
> https://image.nostr.build/cc4282a3aa0bc2b42942e1f9e1e6a5cbd9db22ec6d82cee2ef6a7ff665cbe63e.jpg

Parser input: Bread preparation involving salt, yeast, and mixing.

Exact native output:

```text
event.v.01 Participant +3 bread.n.01 preparation.n.01 MadeOf -1 involve.v.01 Agent -1 Theme +1 salt.n.01 yeast.n.02 entity.n.01 Sub -2 Sub -1 Sub +1 mixing.n.01
```

Syntax check: passed local sequence/reference checks

Predicted concepts:

| Node | Native sense | Dictionary meaning |
|---|---|---|
| 0 | `event.v.01` | No such sense in cached WordNet 3.0 |
| 1 | `bread.n.01` | food made from dough of flour or meal and usually raised with yeast or baking powder and then baked |
| 2 | `preparation.n.01` | the activity of putting or setting in order in advance of some act or purpose |
| 3 | `involve.v.01` | connect closely and often incriminatingly |
| 4 | `salt.n.01` | a compound formed by replacing hydrogen in an acid by a metal (or a radical that acts like a metal) |
| 5 | `yeast.n.02` | any of various single-celled fungi that reproduce asexually by budding or division |
| 6 | `entity.n.01` | that which is perceived or known or inferred to have its own distinct existence (living or nonliving) |
| 7 | `mixing.n.01` | the act of mixing together |

Predicted relationships (IDs refer only to this row):

```text
0 — Participant → 3
2 — MadeOf → 1
3 — Agent → 2
3 — Theme → 4
6 — Sub → 4
6 — Sub → 5
6 — Sub → 7
```

## Row 904 · N022 · V149

> ⟦This year’s beets⟧. Vac sealed and ⟦ready for the freezer⟧. Not too bad for a 4x4 ⟦raised bed⟧. 5 meals of sides in a pinch. I am looking forward to having more garden space but this is good while we are still in a half acre lot in town. https://image.nostr.build/b4349cc1251dccf78990620ee851ad0ae449327da16ac31391e3e71fafdbe65c.jpg https://image.nostr.build/5c7e4ba19bb3c2e98cb57753679d33be2bbad3a07900afc86315c85f80bc46e4.jpg 

Parser input: The author is preparing this year's garden-grown beets for preservation by freezing.

Exact native output:

```text
person.n.01 Role +1 author.n.01 time.n.08 EQU now prepare.v.01 Agent -3 Time -1 Patient +3 Manner +5 time.n.08 TPR now time.n.01 garden-grown.a.01 AttributeOf +1 beet.n.02 PartOf -2 Goal +1 preservation.n.01 freeze.v.01
```

Syntax check: passed local sequence/reference checks

Predicted concepts:

| Node | Native sense | Dictionary meaning |
|---|---|---|
| 0 | `person.n.01` | a human being |
| 1 | `author.n.01` | writes (books or stories or articles or the like) professionally (for pay) |
| 2 | `time.n.08` | the fourth coordinate that is required (along with three spatial dimensions) to specify a physical event |
| 3 | `prepare.v.01` | make ready or suitable or equip in advance for a particular purpose or for some use, event, etc |
| 4 | `time.n.08` | the fourth coordinate that is required (along with three spatial dimensions) to specify a physical event |
| 5 | `time.n.01` | an instance or single occasion for some event |
| 6 | `garden-grown.a.01` | No such sense in cached WordNet 3.0 |
| 7 | `beet.n.02` | round red root vegetable |
| 8 | `preservation.n.01` | the activity of protecting something from loss or danger |
| 9 | `freeze.v.01` | stop moving or become immobilized |

Predicted relationships (IDs refer only to this row):

```text
0 — Role → 1
3 — Agent → 0
3 — Time → 2
3 — Patient → 6
3 — Manner → 8
7 — Attribute → 6
7 — PartOf → 5
7 — Goal → 8
```
