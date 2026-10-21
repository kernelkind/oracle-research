# HRC01 — HierarCaps on our masks

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

The small test is encouraging, but it does not establish a hierarchy-building solution.

All six planned direction checks and all four planned cross-topic comparisons favored the expected relationship. These are selected, mostly easy examples—not a measured general accuracy rate. The bread checks reuse one trio, and every planned positive contains the broader subject's words inside the narrower mask.

We used the released HierarCaps CLIP-L text encoder: 123,650,304 parameters, 768 numbers per vector. No training. Only exact existing mask text entered the model; the original notes below were retained for interpretation, not encoded.

## How to read the scores

For two masks A and B, the angle measures how well the vector for B extends outward from A, relative to the model's empty-string origin. **Lower favors A as broader than B.** The reversed score asks the opposite question. An angle is not a probability, and this experiment did not set an acceptance cutoff.

This is the [paper's exterior-angle measure](https://arxiv.org/html/2407.08521v2), checked against the [authors' code](https://github.com/TAU-VAILab/hierarcaps/blob/c8ddc41cdb0fcdf39f711875c9c72c14bbbbb0dc/code/train.py#L143). Their HyperLex benchmark adds an image-style text template. We deliberately did not: the question here is whether the model works with our original masks.

V identifiers refer to the existing masks. Their HierarCaps vectors are new; they are not the saved SSE vectors. N identifiers refer to original source notes. ⟦Brackets⟧ mark mask text.

## Directions selected before seeing scores

Each row compares the same two vectors in opposite directions.

| Expected broader mask A | Expected narrower mask B | A → B | B → A |
|---|---|---:|---:|
| [V286](#v286) ⟦bread⟧ | [V287](#v287) ⟦sourdough bread⟧ | 77.10° | 138.17° |
| [V287](#v287) ⟦sourdough bread⟧ | [V292](#v292) ⟦cinnamon sourdough bread⟧ | 78.72° | 141.51° |
| [V286](#v286) ⟦bread⟧ | [V292](#v292) ⟦cinnamon sourdough bread⟧ | 75.48° | 155.14° |
| [V381](#v381) ⟦Coffee⟧ | [V281](#v281) ⟦Iced coffee⟧ | 87.06° | 137.09° |
| [V379](#v379) ⟦bitcoin⟧ | [V451](#v451) ⟦Bitcoin workshop⟧ | 86.91° | 144.00° |
| [V436](#v436) ⟦Music⟧ | [V295](#v295) ⟦playing coffee shop music⟧ | 89.96° | 143.58° |

The expected direction wins in every row. This supports simple broad-to-narrow ordering on these masks. It does not establish that the model learned the distinction independently of word overlap or phrase length.

For cinnamon sourdough bread, both bread and sourdough bread are valid broader subjects. Bread scores slightly better than sourdough bread. The score therefore does not, by itself, choose the closest useful parent.

## Other subjects selected before seeing scores

Here the narrower mask stays fixed. Only the proposed broader mask changes.

| Narrower mask | Relevant broader mask and angle | Cross-topic alternative and angle |
|---|---|---|
| [V281](#v281) ⟦Iced coffee⟧ | [V381](#v381) ⟦Coffee⟧ — 87.06° | [V436](#v436) ⟦Music⟧ — 113.49° |
| [V295](#v295) ⟦playing coffee shop music⟧ | [V436](#v436) ⟦Music⟧ — 89.96° | [V379](#v379) ⟦bitcoin⟧ — 115.79° |
| [V451](#v451) ⟦Bitcoin workshop⟧ | [V379](#v379) ⟦bitcoin⟧ — 86.91° | [V387](#v387) ⟦Linux⟧ — 112.20° |
| [V292](#v292) ⟦cinnamon sourdough bread⟧ | [V286](#v286) ⟦bread⟧ — 75.48° | [V381](#v381) ⟦Coffee⟧ — 105.40° |

All four comparisons favor the relevant subject. This is additional evidence beyond simply assigning greater depth to longer phrases, but the alternatives are easy, cross-topic contrasts.

## The other comparisons

These inputs were selected before the run, without requiring a particular hierarchy or binary verdict. Their scores were inspected afterward.

| Mask A | Mask B | A → B | B → A | Interpretation |
|---|---|---:|---:|---|
| [V387](#v387) ⟦Linux⟧ | [V385](#v385) ⟦Gentoo⟧ | 94.05° | 145.88° | Exploratory non-overlapping words; Gentoo's sense is implicit in the mask. |
| [V444](#v444) ⟦Knowledge must be shared⟧ | [V464](#v464) ⟦Knowledge shared Bitcoin workshop⟧ | 101.01° | 144.14° | Plausible knowledge-sharing refinement, not strict logical entailment. |
| [V451](#v451) ⟦Bitcoin workshop⟧ | [V464](#v464) ⟦Knowledge shared Bitcoin workshop⟧ | 82.90° | 121.90° | The workshop mask with knowledge-sharing added. |
| [V282](#v282) ⟦ice⟧ | [V281](#v281) ⟦Iced coffee⟧ | 97.97° | 139.40° | An ingredient/use relationship; not declared invalid. |
| [V381](#v381) ⟦Coffee⟧ | [V295](#v295) ⟦playing coffee shop music⟧ | 102.98° | 134.01° | Shared coffee-shop context; no forced single parent. |
| [V295](#v295) ⟦playing coffee shop music⟧ | [V560](#v560) ⟦Coffee shop Felt like changing their router/ap passwords⟧ | 94.19° | 143.54° | Shared setting, but music is not broader than router-password-changing intent. |
| [V627](#v627) ⟦Find purpose and pursue that purpose⟧ | [V629](#v629) ⟦Find purpose and pursue that purpose, without making your purpose the process of finding purpose.⟧ | 89.06° | 118.42° | Added qualification may retain the same browsing subject. |
| [V618](#v618) ⟦accept that not everything needs to be said⟧ | [V619](#v619) ⟦accept that not everything needs to be said, even if this means things do not go your way⟧ | 82.35° | 126.96° | Added qualification may retain the same browsing subject. |
| [V617](#v617) ⟦Learn when to speak⟧ | [V618](#v618) ⟦accept that not everything needs to be said⟧ | 113.64° | 128.11° | Related advice; no mandatory direction was required. |

Linux is Gentoo's best-scoring proposed broader mask among these 20 inputs. That is encouraging evidence without literal word overlap, though it is still one exploratory example and the token count increases.

The coffee-shop activity comparison is a concrete caution. The masks say:

- [V295](#v295) ⟦playing coffee shop music⟧
- [V560](#v560) ⟦Coffee shop Felt like changing their router/ap passwords⟧

The first concerns music playing in a coffee shop; the second concerns wanting to change a shop's router passwords. They share a setting. That supports relatedness or a common broader category, not placing password-changing intent under music. Nevertheless, their 94.19° score is close to the 94.05° Linux → Gentoo score. This is a concern for direct score-based ancestry, not evidence that all coffee-related grouping is wrong.

A weaker abstract comparison is also worth preserving. For ⟦Bitcoin workshop⟧, these proposed broader masks score:

| Proposed broader mask | Angle |
|---|---:|
| [V379](#v379) ⟦bitcoin⟧ | 86.91° |
| [V286](#v286) ⟦bread⟧ | 112.64° |
| [V436](#v436) ⟦Music⟧ | 113.23° |
| [V444](#v444) ⟦Knowledge must be shared⟧ | 114.13° |

Knowledge-sharing is plausibly relevant to a workshop, yet it ranks below bread and music. The exact knowledge mask is an injunction, not simply the category “knowledge-sharing,” so this is a qualified warning about harder topical relationships, not a failed predeclared check. Bitcoin itself still ranks first.

## What this establishes

The tested configuration contains useful direction information for the selected simple relationships. It also recognizes a plausible Linux/Gentoo relationship despite different words.

It does not yet establish reliable behavior for abstract relationships, independence from phrase length, a cutoff for rejecting unsupported ancestry, which broader descriptions to generate, or which levels are useful to browse. Added qualifications need not become new levels. Directional angle ordering and distance-from-origin ordering are mathematically the same pairwise evidence, not two independent confirmations.

No hierarchy was built or changed. The useful next question is whether the favorable ordering survives examples without shared wording and whether closely related but non-parent subjects can be distinguished. This run does not answer that adequately.

## Original notes with each mask

Each entry below shows the complete original note with only that mask highlighted. Multiple fragments become one input by joining their exact text with a single space. Generated subject descriptions were not used.

### V286

N037. Exact model input: `bread`

> #foodstr
> Cranberry , rosemary , brown sugar and cinnamon sourdough ⟦bread⟧ , good lord it soo good https://image.nostr.build/cb6f56072bd4957a92c9f13a54444b0472c9ec071483b8dee2407469509d3ff0.jpg https://image.nostr.build/0b31d68d6792f6c7c54d5137a38880d68fdad1ccef9d760be02084141bb7a750.jpg https://image.nostr.build/ee8911a263955cf26e737a57d5abe0389a60623c89fcd97aa4855f43f584dfbd.jpg

### V287

N037. Exact model input: `sourdough bread`

> #foodstr
> Cranberry , rosemary , brown sugar and cinnamon ⟦sourdough bread⟧ , good lord it soo good https://image.nostr.build/cb6f56072bd4957a92c9f13a54444b0472c9ec071483b8dee2407469509d3ff0.jpg https://image.nostr.build/0b31d68d6792f6c7c54d5137a38880d68fdad1ccef9d760be02084141bb7a750.jpg https://image.nostr.build/ee8911a263955cf26e737a57d5abe0389a60623c89fcd97aa4855f43f584dfbd.jpg

### V292

N037. Exact model input: `cinnamon sourdough bread`

> #foodstr
> Cranberry , rosemary , brown sugar and ⟦cinnamon sourdough bread⟧ , good lord it soo good https://image.nostr.build/cb6f56072bd4957a92c9f13a54444b0472c9ec071483b8dee2407469509d3ff0.jpg https://image.nostr.build/0b31d68d6792f6c7c54d5137a38880d68fdad1ccef9d760be02084141bb7a750.jpg https://image.nostr.build/ee8911a263955cf26e737a57d5abe0389a60623c89fcd97aa4855f43f584dfbd.jpg

### V381

N048. Exact model input: `Coffee`

> #Come in! We will be happy: https://linuxtosha.ru/
> “How can we hope that peace and prosperity will reign on earth if our bodies are living graves in which killed animals are buried?” Lev Nikolaevich Tolstoy
> https://m.primal.net/IADr.png
> #art #alby #bitcoin #cat #⟦Coffee⟧ #dog #dream #Gentoo #grownostr #Linux #memes #Nature #nostr #Photography #pleb #plebchain #zap #zapathon

### V281

N036. Exact model input: `Iced coffee`

> ⟦Iced coffee⟧, served in ice
>
> 📹 wolf.0313
>
>  https://t.co/58sduGh4ME https://video.twimg.com/amplify_video/1807714912455872512/vid/avc1/720x1280/TRtP3N_40gd9jFGv.mp4?tag=14

### V282

N036. Exact model input: `ice`

> Iced coffee, served in ⟦ice⟧
>
> 📹 wolf.0313
>
>  https://t.co/58sduGh4ME https://video.twimg.com/amplify_video/1807714912455872512/vid/avc1/720x1280/TRtP3N_40gd9jFGv.mp4?tag=14

### V436

N054. Exact model input: `Music`

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
> #Bitcoin #Satoshis #Freedom #Apocalypse          #⟦Music⟧   #Movies #Philosophy  #Literature
>                                  #dogstr #islands

### V295

N038. Exact model input: `playing coffee shop music`

> Awwww yeah. Baby Got Back ⟦playing⟧ in the ⟦coffee shop⟧. 😂 #⟦music⟧str #coffeechain

### V379

N048. Exact model input: `bitcoin`

> #Come in! We will be happy: https://linuxtosha.ru/
> “How can we hope that peace and prosperity will reign on earth if our bodies are living graves in which killed animals are buried?” Lev Nikolaevich Tolstoy
> https://m.primal.net/IADr.png
> #art #alby #⟦bitcoin⟧ #cat #Coffee #dog #dream #Gentoo #grownostr #Linux #memes #Nature #nostr #Photography #pleb #plebchain #zap #zapathon

### V451

N055. Exact model input: `Bitcoin workshop`

> Knowledge must be shared, so must joy, and if there's something sacred that breaks all barriers, it's sharing a meal. After the #⟦Bitcoin workshop⟧ conducted by nostr:nprofile1qqsqkp32f9m2xp2snj8xtqac4plm0ah3rjjy9dc3fgdz35gk30gswrqpzemhxue69uhhyetvv9ujuurjd9kkzmpwdejhgqgjwaehxw309ac82unsd3jhqct89ejhxqgnwaehxw309aex2mrp09skymr99ehhyecaxwfrt https://image.nostr.build/4ab2ef1dd6512a4ba68fa38d1fb96ea043a5cabb1e0fcd17fbca8d06d1c408ea.jpg c, the humble people of Amambay( a rural área of Paraguay )The real plebs, The guarani-speaking peasants, slaughtered a pig. As a rule, the poorest are often the most generous. Education is the way forward 🇵🇾🧡 https://image.nostr.build/d41cbe864aa9bf691a5435cb3c9364520cd7900e5c5e6a2f6599187f3c3c74e1.jpg

### V444

N055. Exact model input: `Knowledge must be shared`

> ⟦Knowledge must be shared⟧, so must joy, and if there's something sacred that breaks all barriers, it's sharing a meal. After the #Bitcoin workshop conducted by nostr:nprofile1qqsqkp32f9m2xp2snj8xtqac4plm0ah3rjjy9dc3fgdz35gk30gswrqpzemhxue69uhhyetvv9ujuurjd9kkzmpwdejhgqgjwaehxw309ac82unsd3jhqct89ejhxqgnwaehxw309aex2mrp09skymr99ehhyecaxwfrt https://image.nostr.build/4ab2ef1dd6512a4ba68fa38d1fb96ea043a5cabb1e0fcd17fbca8d06d1c408ea.jpg c, the humble people of Amambay( a rural área of Paraguay )The real plebs, The guarani-speaking peasants, slaughtered a pig. As a rule, the poorest are often the most generous. Education is the way forward 🇵🇾🧡 https://image.nostr.build/d41cbe864aa9bf691a5435cb3c9364520cd7900e5c5e6a2f6599187f3c3c74e1.jpg

### V464

N055. Exact model input: `Knowledge shared Bitcoin workshop`

> ⟦Knowledge⟧ must be ⟦shared⟧, so must joy, and if there's something sacred that breaks all barriers, it's sharing a meal. After the #⟦Bitcoin workshop⟧ conducted by nostr:nprofile1qqsqkp32f9m2xp2snj8xtqac4plm0ah3rjjy9dc3fgdz35gk30gswrqpzemhxue69uhhyetvv9ujuurjd9kkzmpwdejhgqgjwaehxw309ac82unsd3jhqct89ejhxqgnwaehxw309aex2mrp09skymr99ehhyecaxwfrt https://image.nostr.build/4ab2ef1dd6512a4ba68fa38d1fb96ea043a5cabb1e0fcd17fbca8d06d1c408ea.jpg c, the humble people of Amambay( a rural área of Paraguay )The real plebs, The guarani-speaking peasants, slaughtered a pig. As a rule, the poorest are often the most generous. Education is the way forward 🇵🇾🧡 https://image.nostr.build/d41cbe864aa9bf691a5435cb3c9364520cd7900e5c5e6a2f6599187f3c3c74e1.jpg

### V385

N048. Exact model input: `Gentoo`

> #Come in! We will be happy: https://linuxtosha.ru/
> “How can we hope that peace and prosperity will reign on earth if our bodies are living graves in which killed animals are buried?” Lev Nikolaevich Tolstoy
> https://m.primal.net/IADr.png
> #art #alby #bitcoin #cat #Coffee #dog #dream #⟦Gentoo⟧ #grownostr #Linux #memes #Nature #nostr #Photography #pleb #plebchain #zap #zapathon

### V387

N048. Exact model input: `Linux`

> #Come in! We will be happy: https://linuxtosha.ru/
> “How can we hope that peace and prosperity will reign on earth if our bodies are living graves in which killed animals are buried?” Lev Nikolaevich Tolstoy
> https://m.primal.net/IADr.png
> #art #alby #bitcoin #cat #Coffee #dog #dream #Gentoo #grownostr #⟦Linux⟧ #memes #Nature #nostr #Photography #pleb #plebchain #zap #zapathon

### V627

N069. Exact model input: `Find purpose and pursue that purpose`

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
> 15. ⟦Find purpose and pursue that purpose⟧, without making your purpose the process of finding purpose.
> 16. Do not grant someone more priveleges based on status, or similar, but based on kindness and goodness.
> 17. Be kind!
> 18. Accept that you never know everything, be open to different views.
> 19. …
>
> What would you add?

### V629

N069. Exact model input: `Find purpose and pursue that purpose, without making your purpose the process of finding purpose.`

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
> 15. ⟦Find purpose and pursue that purpose, without making your purpose the process of finding purpose.⟧
> 16. Do not grant someone more priveleges based on status, or similar, but based on kindness and goodness.
> 17. Be kind!
> 18. Accept that you never know everything, be open to different views.
> 19. …
>
> What would you add?

### V617

N069. Exact model input: `Learn when to speak`

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
> 11.  ⟦Learn when to speak⟧…accept that not everything needs to be said, even if this means things do not go your way.
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

### V618

N069. Exact model input: `accept that not everything needs to be said`

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
> 11.  Learn when to speak…⟦accept that not everything needs to be said⟧, even if this means things do not go your way.
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

### V619

N069. Exact model input: `accept that not everything needs to be said, even if this means things do not go your way`

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
> 11.  Learn when to speak…⟦accept that not everything needs to be said, even if this means things do not go your way⟧.
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

### V560

N065. Exact model input: `Coffee shop Felt like changing their router/ap passwords`

> ⟦Coffee shop⟧ I liked now has a “No laptops or tablets” rule on weekends. This is what happens if you let hipsters get too successful. ⟦Felt like changing their router/ap passwords⟧ so they could experience the true freedom from internet, but I simply went to another coffee shop and will remove this one from rotation. Personal growth on display.

## Reproduction and checks

- [Frozen selections and interpretation limits](fixture.json), original notes and exact model inputs (`inputs.json`), all 400 scores (`scores.json`), all vectors (`embeddings.json`), planned comparisons (`checks.json`), checkpoint and runtime hashes (`config.json`), [executed runner](../../hierarcaps_mask_probe.py).
- Nine targeted tests passed after first failing because the runner did not exist. They exercise exact-mask inputs, original-artifact matching, UTF-8 ranges, source order, duplicate/unknown IDs, angle mathematics, undefined angles, and checkpoint completeness.
- All 400 stored scores replay exactly from the saved vectors. All 20 inputs match the original masks and source ranges.
- An independent verification loaded the full author-style CLIPModel from the same cached checkpoint. Its text features exactly matched all 21 saved vectors, including the empty-string origin. The author's literal Torch angle calculation matched all 380 defined pair scores within 0.000000463 radians; the remaining 20 self-pairs have undefined direction.
- All text parameters loaded from the checkpoint: zero missing or mismatched keys. Ignored parameters belong only to the unused image tower and image–text scaling.
- Model input lengths were 3–21 tokens including special tokens, below the 77-token limit. No truncation.
- CPU inference for 20 masks plus the origin took 0.19 seconds after loading. Initial download/loading took 79.94 seconds; the public checkpoint download was 1.71 GB because it also contains image weights. Only the text tower was used for the experiment.
- The experiment and verification each ran within a 6 GiB RAM, no-swap, two-CPU-equivalent systemd scope. The legacy `peak_rss_kib` field is raw `ru_maxrss`, which can inherit a pre-exec high-water value here; it is not a reliable workload-isolated peak. Verification's current-process `VmHWM` was 697,476 KiB. No paid compute.
- An independent reader inspected all 20 masks and all 400 scores. Its interpretation agreed with the limited positive finding and the caveats above.

**Selected data:** Compact pair-score results, inputs and parameters for `HRC01` are selected for release as `numerical/pair-scores-0b911a2c344e9f10` in the [publication catalog](../../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.

## HRC01 study design

Test the released HierarCaps text encoder as a possible source of broader–narrower relationships. Do not train anything, construct a hierarchy, change masks, or modify the browser.

### What changes

The source masks stay fixed. This run encodes their exact text with HierarCaps rather than SSE. It is a standalone capability check, not a controlled claim that HierarCaps improves upon SSE: no corresponding SSE score comparison is being run.

Use `malper/hierarcaps-clip-l` at revision `e3aa199d94c438f98628c9697a0b64ef5760b03c`. This is the larger released HierarCaps text encoder, approximately 123 million parameters. Choosing it does not imply it outperforms the base variant. Its image-caption training may transfer poorly to technical and abstract masks; those appear in the selected inputs.

The user authorized an already-trained model only. Inference is local CPU, two threads, batches of four, within a systemd scope capped at 6 GiB RAM with no swap and two CPU equivalents. No paid resources or new model training.

### Inputs and hypothesis

Twenty original masks were selected before any model scores by an independently spawned, clean-context reader. The main agent reviewed the selections before inference. Exact IDs, comparisons, limitations, checkpoint, and original-artifact hash are frozen in [hrc01-fixture.json](../hrc01-fixture.json).

**Hypothesis:** The released geometry distinguishes supported broad-to-narrow directions and separates those relationships from obvious cross-topic alternatives on these exact masks.

The fixed directions are bread → sourdough bread → cinnamon sourdough bread; coffee → iced coffee; Bitcoin → Bitcoin workshop; and music → playing music in a coffee shop. The three bread comparisons reuse one nested trio, not three independent examples. Four additional comparisons ask whether a suitable broader mask scores better than a clearly cross-topic alternative for the same specific mask.

Remaining inputs cover ingredients, technical names, knowledge-sharing, advice, and two different activities in a coffee-shop setting. These are inspected without requiring a unique parent. In particular, ice → iced coffee and timing speech → leaving things unsaid are not hard negative examples. Additional detail does not automatically require another navigation level.

The original masks come from `real-note-fine-segmentation-v1/vectors/vector-map.json`. Source notes come from `geometric-hierarchy-v1/GDC09/evidence.json`; each chosen record must match the original vector identity, source-note identity, fragments, and UTF-8 byte ranges. Model input is only the fragments joined with a space, in source order. No generated descriptions, full notes, semantic templates, dictionary lookups, or rewritten text enter the model. Full notes are saved separately for interpretation.

### Calculation and limits

Encode each mask and the empty string, normalizing each output vector to length one. The empty string supplies the author's geometric origin, not a semantic instruction. For proposed broader mask A and narrower mask B, calculate the angle between `A − origin` and `B − A`. Smaller angles support the proposed direction more strongly; they are not probabilities and have no calibrated acceptance threshold here.

This is the paper-defined exterior-angle measure, verified against the [paper, sections 3–4 and 6.1](https://arxiv.org/html/2407.08521v2) and [author code at c8ddc41](https://github.com/TAU-VAILab/hierarcaps/blob/c8ddc41cdb0fcdf39f711875c9c72c14bbbbb0dc/code/train.py#L143). The published HyperLex test adds an image-style prompt; this run deliberately does not because our required input is exact mask text. It is not a reproduction of that benchmark or of the image-retrieval demo.

Save both directions, ordinary cosine, and distance from the origin. Directional angle ordering and distance ordering are mathematically dependent; they must not be counted as independent evidence. Comparisons against other subjects are necessary to inspect whether the direction is semantically useful. Equal embeddings have no defined directional angle.

Preserve all 400 ordered pair scores, embeddings, original source notes, exact masks, loading diagnostics, input/checkpoint hashes, package versions, and the executed runner. Never truncate an input silently or accept randomly initialized text parameters. Do not fit a threshold after seeing results.

This small, selected pilot can expose concrete capability or counterexamples. It cannot establish corpus-wide accuracy, generate missing broader categories, or validate parent–child construction. A failure is specific to this checkpoint, mask-only input, and score—not every broader–narrower embedding model.
