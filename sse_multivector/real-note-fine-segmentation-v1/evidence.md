**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

V identifies a vector and its mask. S identifies a segment. ⟦…⟧ marks the exact selected text. Every note below is complete, including URLs; only those mask markers and blockquote prefixes have been inserted. Repeated notes are shown again when their masks differ.

## 1. A close coffee neighbor remains ungrouped in baseline

Baseline leaves V342 ungrouped even though its saved cosine similarity to V277 is 0.9541. Density groups both in S34b70d4196.

V342

> Beyond 9am. Hazy sunlight on dusty desk. First tasks done, first minutes written, first things postponed. ⟦Fetching coffee⟧ as a ritual of motion, as well as doing some clumsy stretching and bowing to fight the physical and mental rust, to counter the effects of being stuck in the same position for too long. 
> 

V277

> ⟦More coffee⟧ in cool places https://image.nostr.build/f09d0a87aad1f999f48a1c3ff1ce4ea08db05749888f258359c12719943797ad.jpg

Measured facts: the saved neighbor inspection (`unassigned-neighbor-inspection.json`) records cosine 0.9541135626375935 for V342–V277, across two different notes. In baseline (`hdbscan-baseline/review/review.json`), V277 belongs to Sbb8511308a and V342 appears in unassigned instances (`hdbscan-baseline/review/unassigned.json`). In density (`hdbscan-density/review/review.json`), both belong to S34b70d4196.

“Fetching coffee” and “More coffee” share selected coffee content despite differing in action and quantity. This is a concrete baseline grouping omission next to a highly similar saved vector, recovered by the density result. The cosine is descriptive evidence, not a clustering threshold or a guarantee that every member of S34b70d4196 is valid. It does not establish why either configuration made its assignments.

## 2. Leaf divides seven coffeechain masks into 2 + 3 and leaves two ungrouped

Baseline's Sf5a4b23523 contains seven masks from seven notes. Leaf retains two smaller groups and leaves V297 and V797 ungrouped, although all seven still explicitly select the same coffeechain reference.

V043

> Gm nostriches, mid jet lag after landing into Charlotte NC yesterday. Hoping the breakfast will get me going. #grownostr #⟦coffeechain⟧ https://image.nostr.build/fc2f76e3c0dc8676f3fcefa27a1bb3a50331ed157d9519630b066085b45ef7b9.jpg 

V126

> Good morning, crushed a solid gym session this morning to kick off the weekend. Now time for a late breakfast! ⟦#coffeechain⟧

V187

> Red flags: Workout plans shorter than 1,000 days (because Rome wasn’t built in 6 weeks), food that never expires (are we eating plastic?), and people who don’t like ice cream (what else are they hiding?).
> 
> 
> #nostr #bitcoin #plebchain #⟦coffeechain⟧ #dadlife #satoshi #DCA #daily #grownostr #hardmoney 
> https://m.primal.net/LSVD.jpg

V297

> Awwww yeah. Baby Got Back playing in the coffee shop. 😂 #musicstr ⟦#coffeechain⟧

V656

> Good morning frens. 
> #Duck egg and #basil #breakfast burrito on a tomato tortilla and of course some good #coffee to go with. 
> 
> Miss unicorn jealously watching hehe 😜 
> ⟦#coffeechain⟧ #grownostr https://image.nostr.build/804c5dc348d07b0322c87bedbe2284de6900fdd16796c876e0640791a24287d3.jpg 

V797

> You’ve had coffee. But have you had your coffee?”
> https://blossom.primal.net/1379b90996b8ecb2f4fdef6756fd61c4ab964fa19f9e1505950e10a4d97640dd.jpg
> Roasting your own beans means discovering a taste profile that’s uniquely yours. It’s a personal journey that no bag of pre-roasted coffee can replicate.
> 
> ⟦Sipping⟧  @ ⟦#coffeechain⟧ 
> 
> #HotTake ☕

V865

> Just had a coffee, but I need another one... Good morning world, I wish you all a wonderful and blessed Sunday. 
> 
> ⟦#coffeechain⟧ #plebchain 

Measured memberships from the baseline (`hdbscan-baseline/review/review.json`) and leaf (`hdbscan-leaf/review/review.json`) reviews, also checked against leaf unassigned instances (`hdbscan-leaf/review/unassigned.json`):

| Result | Segment or status | Instances |
| --- | --- | --- |
| Baseline | Sf5a4b23523 | V043, V126, V187, V297, V656, V797, V865 |
| Leaf | S051b48ba1c | V043, V187 |
| Leaf | S317bb50727 | V126, V656, V865 |
| Leaf | Ungrouped | V297, V797 |

The leaf assessment (`assistant-leaf-changes.json`) accepts both child segments individually but finds the split needless. The two-member segment selects “coffeechain” without the hash sign; the three-member segment selects “#coffeechain”. This observed partition is not a demonstrated semantic distinction or an explanation of the algorithm's cause. V297 selects exactly the same hashtag as the three-member segment. V797 adds “Sipping” while retaining that hashtag. Their unmasked music, travel, breakfast or roasting details do not remove this shared selected meaning. The result reduces one seven-note recurrence to two- and three-note groups and excludes two relevant instances.

## 3. Density loses a valid coffee-shop music group entirely

Baseline's S6f2f479441 groups three masks from two notes. Density leaves all three ungrouped.

V035

> Weird #coffeechain today
> ⟦Rave at a coffee shop⟧ lol https://video.nostr.build/252e03e0d852e21d29e875ca7e1f381ad5559b8eee53b4a683babcb688b946ed.mp4 

V036

> Weird #coffeechain today
> ⟦Rave at a coffee shop lol⟧ https://video.nostr.build/252e03e0d852e21d29e875ca7e1f381ad5559b8eee53b4a683babcb688b946ed.mp4 

V295

> Awwww yeah. Baby Got Back ⟦playing⟧ in the ⟦coffee shop⟧. 😂 #⟦music⟧str #coffeechain

Measured facts: baseline (`hdbscan-baseline/review/review.json`) places V035, V036 and V295 together in S6f2f479441. The final baseline assessment (`assistant-baseline-final.json`) marks that segment valid. V035 and V036 are variants from one original note; V295 comes from a second note. The segment is absent from the density review (`hdbscan-density/review/review.json`), and all three instances appear in density's unassigned list (`hdbscan-density/review/unassigned.json`), not in replacement segments.

The selected rave at a coffee shop and music playing in a coffee shop share a concrete activity and kind of venue. They need not describe the same music or event. This judgment does not require opening the video URL or importing the unselected song title. Density therefore loses valid two-note grouping coverage here. That is a grouping-result regression; losing the group alone does not show an SSE representation failure or identify the cause.
