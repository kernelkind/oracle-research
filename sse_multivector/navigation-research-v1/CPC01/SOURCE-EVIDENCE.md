# CPC01 source evidence

These are exact saved descriptions and complete original notes. `row` identifies a CAP04 description record; `V` identifies its saved mask and `N` its note. Brackets mark the original UTF-8 mask ranges. The classifier received only the description and one category—not the full note shown here for evaluation. Scores are native sigmoid outputs, not calibrated probabilities of semantic truth.

## N080 · V732 · row 36

Category: chicken. Score: 0.999222010.

Description: The author's household has four hens.

> Wednesday, 20th November 2024 - Cherries
> 
> Wow what a beautiful morning. Stunning sunrise over a frosty garden. That got me out of bed - plus the need for tea and a wee. Yes and in that order.
> 
> ⟦Our⟧ chickens are laying an egg a day. Having ⟦four hens⟧ that is a lot of eggs. My guests had scrambled eggs for breakfast and I soft boiled nine eggs for my lunch over the next few days. The clutch of eggs is receding. Michael Mosley said that a boiled egg is a good alternative to a packet of crisps!!!! Can't quite see the similarity but I have plenty of crisp substitutes in the fridge.
> 
> The new audio book I had was like listening to a load of fluff. Total meaningless drivel. I gave up and have started a new murder mystery which is much more entertaining. I needed it while I was printing the last of our Christmas cards.
> 
> Tim came home from Brussels with a gift of a bottle of gin, a bottle of Kreik and a bar of dark chocolate. Week 3 Day 3 I have chosen fruit for Kalie Graves challenge. My bottle of Kreik is cherry flavoured.
> - 
> -
> -
> #kgaweekday #katesconnectedpostcardproject #apaintingaday #katerundell #artblog #dailyart #instaart #instaartist #watercolour #artoninstagram #artofinstagram #painting #watercolourpainting #blogger #dailyblogger #winsorandnewton #instadaily #danielsmithwatercolors https://nostrcheck.me/media/18d26089c0617d1b68bd08dfef065cf5eb5316a97eee1c0014d079ed3a6bc815/654867f61c247a385f166f7ba177be4382829feb6c77bfb73131fd7dfa849ce5.webp

Analysis: Valid Chicken membership. This is the maximum, but other saved descriptions already contain “chickens”; CPC02 tests whether normalization recovers the note without needing this hens-to-chicken inference.

## N100 · V929 · row 686

Category: chicken. Score: 0.998803593.

Description: The author plans to put out cold water and sunflower seeds for the chickens tomorrow.

> Alright today's been pretty solid. 
> 
> Picked up a sirloin strip sub primal for $10 a lb cut 15 steaks about 1.5-2" thickness. 
> 
> Trimmed about 3lb of fat for making tallow and about a quarter pound of some connective tissue and scrap meat for the dog. 
> 
> 
> Saved the excess myoglobin to add in the dogs food and ⟦will put⟧ some some ⟦cold water and sunflower seeds for the chickens tomorrow⟧. 
> 
> I finally got to use the new vacuum sealer and this one is much better than the food savers I've used in the past. I got this on a deal from Amazon for 30% off and love it after using it. If you need one check out the Nesco VS-12
> 
> #beef #foodstr #foodpreservation #cooking #steak #cooking #grownostr #prepping #plebchain #homesteading 
> 
>  https://image.nostr.build/270bbbc11299301ee5b4678883c5d48ab2f95eb13b1417093186ba855f4d90e5.jpg

Analysis: A clean independent witness for Chicken/N100. It remains above the development cutoff even without the erroneous description in row 728.

## N100 · V930 · row 728

Category: chicken stock. Score: 0.975001172.

Description: The author plans to put some saved beef myoglobin in cold water with sunflower seeds for the chickens tomorrow.

> Alright today's been pretty solid. 
> 
> Picked up a ⟦sirloin⟧ strip sub primal for $10 a lb cut 15 steaks about 1.5-2" thickness. 
> 
> Trimmed about 3lb of fat for making tallow and about a quarter pound of some connective tissue and scrap meat for the dog. 
> 
> 
> ⟦Saved⟧ the excess ⟦myoglobin⟧ to add in the dogs food and ⟦will put some⟧ some ⟦cold water and sunflower seeds for the chickens tomorrow⟧. 
> 
> I finally got to use the new vacuum sealer and this one is much better than the food savers I've used in the past. I got this on a deal from Amazon for 30% off and love it after using it. If you need one check out the Nesco VS-12
> 
> #beef #foodstr #foodpreservation #cooking #steak #cooking #grownostr #prepping #plebchain #homesteading 
> 
>  https://image.nostr.build/270bbbc11299301ee5b4678883c5d48ab2f95eb13b1417093186ba855f4d90e5.jpg

Analysis: Incorrect Chicken-stock membership. This saved description incorrectly attaches myoglobin to the chickens. Even the distorted description does not establish stock. Other unchanged descriptions cross 0.5 too, so the native error cannot be attributed solely to this one input. N100 correctly belongs to Chicken; this particular stock error does not break the parent edge.

## N029 · V239 · row 465

Category: chicken stock. Score: 0.966487678.

Description: The Rogue Batch.

> #⟦TheRogueBatch⟧ #nostr                                                                        #Bitcoin #coffeechain #grownostr 2nd #coffee
> 
> https://nostrcheck.me/media/5824c03d29d372b3277cc0b6cb32d4541102a7af0865bda38fbcedec4d454efa/bfd00fd4781a4b157c3aa5e6f2110bf9c45d775f5247d447b4fa866d39e13be2.webp

Analysis: The name supplies neither Chicken stock nor Sourdough bread. This note is the sole development Chicken→Chicken-stock containment blocker. Its Sourdough score is also an error. No image content is inferred.

Other relevant scores: sourdough bread = 0.971722524.

## N046 · V362 · row 779

Category: salt. Score: 0.761452690.

Description: Bagels topped with sea salt flakes.

> Turn pantry staples into chewy ⟦bagels⟧ 🥯 
> 
> Toppings : sesame, ⟦sea salt flakes⟧ and plain 
> 
> #foodstr   
> https://m.primal.net/OHSR.jpg
> https://m.primal.net/OHSS.jpg

Analysis: The same faithful input is scored below the development cutoff for Salt and above it for Sea salt. This parent omission alone breaks Salt→Sea salt. It was predicted before the run from prior Salt evidence.

Other relevant scores: sea salt = 0.999215152.

## N024 · V178 · row 563

Category: sourdough bread. Score: 0.954252015.

Description: Food that never expires as a red flag.

> ⟦Red flags⟧: Workout plans shorter than 1,000 days (because Rome wasn’t built in 6 weeks), ⟦food that never expires⟧ (are we eating plastic?), and people who don’t like ice cream (what else are they hiding?).
> 
> 
> #nostr #bitcoin #plebchain #coffeechain #dadlife #satoshi #DCA #daily #grownostr #hardmoney 
> https://m.primal.net/LSVD.jpg

Analysis: The warning about food expiration does not identify sourdough. A faithful description receives an incorrect category membership.

## N045 · V354 · row 294

Category: sourdough bread. Score: 0.958850272.

Description: Half-and-half is not cream.

> Dear America,
> 
> ⟦Half & half ≠ cream⟧.
> 
> Stop ruining my coffee with it.

Analysis: The cream/half-and-half distinction does not establish sourdough. This is not a description-extraction distortion.

## N069 · V597 · row 47

Category: sourdough bread. Score: 0.980815529.

Description: Not eating processed food.

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

Analysis: Avoiding processed food is not evidence that the note discusses sourdough bread. The model never saw the whole note.

## N081 · V763 · row 646

Category: sourdough bread. Score: 0.955024926.

Description: The gianduja added to the store is freshly out of the melanger.

> ⟦Added⟧ a few #⟦gianguja⟧ jars ⟦to the store⟧. ⟦Just out of the melanger⟧! https://yabisi.farm/index.php/product/macambo-gianduja/
> 
> #foodstr #grownostr #craftchocolate

Analysis: The post concerns gianduja production/sales, not sourdough bread. An association with freshness or food production is insufficient to establish this narrower membership.

## N100 · V918 · row 568

Category: sourdough bread. Score: 0.958040034.

Description: The author describes the day as pretty solid.

> Alright ⟦today's been pretty solid⟧. 
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
> #beef #foodstr #foodpreservation #cooking #steak #cooking #grownostr #prepping #plebchain #homesteading 
> 
>  https://image.nostr.build/270bbbc11299301ee5b4678883c5d48ab2f95eb13b1417093186ba855f4d90e5.jpg

Analysis: A positive assessment of the day does not establish sourdough. Unlike row 728, this description is faithful and contains no chicken claim.

## N071 · V657 · row 622

Category: bread. Score: 0.769809577.

Description: Growing Nostr.

> Good morning frens. 
> #Duck egg and #basil #breakfast burrito on a tomato tortilla and of course some good #coffee to go with. 
> 
> Miss unicorn jealously watching hehe 😜 
> #coffeechain ⟦#grownostr⟧ https://image.nostr.build/804c5dc348d07b0322c87bedbe2284de6900fdd16796c876e0640791a24287d3.jpg 

Analysis: The note really contains a tortilla, but this is its only description scoring at least 0.5 for Bread. The admitted witness says Growing Nostr. This is a correct note-level destination reached through unsupported evidence—not demonstrated recognition of the tortilla as bread.

## N071 · V651 · row 69

Category: bread. Score: 0.023659140.

Description: A tomato tortilla for a duck egg and basil breakfast burrito.

> Good morning frens. 
> #⟦Duck egg⟧ and #⟦basil⟧ #⟦breakfast burrito⟧ on a ⟦tomato tortilla⟧ and of course some good #coffee to go with. 
> 
> Miss unicorn jealously watching hehe 😜 
> #coffeechain #grownostr https://image.nostr.build/804c5dc348d07b0322c87bedbe2284de6900fdd16796c876e0640791a24287d3.jpg 

Analysis: The actual tortilla witness has a low Bread score. The other tortilla descriptions also remain below 0.5. This explains why counting only note-level true positives overstates grounded recovery.

## N046 · V359 · row 649

Category: bread. Score: 0.790721201.

Description: Bagels with a chewy texture.

> Turn pantry staples into ⟦chewy bagels⟧ 🥯 
> 
> Toppings : sesame, sea salt flakes and plain 
> 
> #foodstr   
> https://m.primal.net/OHSR.jpg
> https://m.primal.net/OHSS.jpg

Analysis: Genuine recognition of bagels as Bread at native 0.5, but below the development cutoff. It is outranked by several unsupported notes; merely lowering a monotone cutoff cannot preserve this recovery while excluding all higher-scoring false positives.

## N078 · V719 · row 869

Category: bread. Score: 0.527606153.

Description: Lacha Paratha.

> Tonight's dinner - ⟦Lacha Paratha⟧ with dal fry
> 
> #india #foodstr #foodchain
> 
> 
> https://image.nostr.build/33c2565fd8f964f4d60ed1d8e286972a538e3686ff9f00f18dfe51f64496d91d.jpg

Analysis: Genuine recognition of paratha as Bread at native 0.5, but below the development cutoff. The note does not establish Chicken stock or Sourdough bread despite their higher scores.
