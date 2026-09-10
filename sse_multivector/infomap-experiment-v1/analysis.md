# What the Infomap comparison tells us

The main result is structural: **none of these four configurations produced the broad-to-narrow hierarchy we wanted.** The sparse graphs did produce useful relationships alongside questionable memberships. This is evidence about these graphs and this frozen corpus, not a rejection of Infomap in general.

## The hierarchy is genuinely flat

I01 has one group containing all 916 vectors. I02, I03, and I04 have 43, 28, and 16 groups respectively. Each group sits directly below the full-corpus root and has no child groups.

This was verified independently against the native tree, native JSON, saved paths, and actual pinned C++ settings. Hierarchical mode was enabled, with no prescribed depth or number of groups. No levels were discarded by our export or viewer. The library's own search returned these results; it does not establish that a deeper solution is impossible.

Changing only graph connections was enough to change the outcome from one group to many groups. This supports investigating graph construction as a substantive part of the method. It does not establish that fewer connections are always better, or that the smallest codelength across different graphs identifies the best semantic result.

## Useful relationships are present

I02/925 brings together grinding coffee, adding cream, wanting another coffee, iced coffee, and coffee-shop material. The following are examples, not the group's entire membership; the TUI contains all 32 canonical vectors from 16 notes.

**V410 · N052 — complete original with mask**

> Rise and ⟦grind coffee beans⟧

**V355/V356 · N045 — complete original with mask**

> Dear America,
>
> ⟦Half & half⟧ ≠ cream.
>
> Stop ⟦ruining my coffee⟧ with it.

**V504 · N060 — complete original with mask**

> ⟦Made⟧ my ⟦coffee with raw cream⟧ and a raw egg yolk ⟦today⟧ #coffeechain

These share a genuine subject despite describing different actions or opinions. I03/917 and I04/917 collect a broader set of coffee-related material, but also contain other drink/food-related masks. They should not be assumed to be perfectly clean coffee categories.

Other grounded relationships appear in I03/923 and I04/922: pig slaughter, saved chicken carcasses, raw meat for dogs, and opposition to eating killed animals. Opposing views are not a reason to split them automatically. I03/932 and I04/923 also connect cooking and equipment such as rocket stoves, smokers, bread pans, cookware, and crockpots. These are positive observations within the groups, not blanket approval of every member.

## A questionable group gathers repeated numbers

I03/931 contains 12 canonical vectors from six notes. Its complete mask membership is:

- V016 · N002: ⟦Sorrento's Savory Stroll⟧ ⟦3 delightful stops⟧
- V017 · N002: ⟦Sorrento's⟧ ⟦Stroll⟧ ⟦Indulge⟧ ⟦3⟧ ⟦stops⟧ ⟦local flavors⟧
- V018 · N002: ⟦Sorrento's⟧ ⟦Stroll⟧ ⟦3⟧ ⟦stops⟧ ⟦promise⟧ ⟦unforgettable gastronomic adventure⟧
- V202 · N026: ⟦Today i⟧ ⟦acquired 3 rotisserie chickens⟧ ⟦marked down⟧
- V203 · N026: ⟦acquired 3 rotisserie chickens⟧ ⟦marked down⟧
- V204 · N026: ⟦i⟧ ⟦3 rotisserie chickens⟧ ⟦bagged⟧ ⟦meat⟧
- V327/V328 · N041: ⟦Usually I'm up like three times⟧
- V305 · N039: ⟦storms⟧ ⟦Third round⟧ ⟦scheduled for⟧ ⟦fireworks⟧
- V307 · N039: ⟦storms⟧ ⟦Third round⟧ ⟦when⟧ ⟦supposed to have fireworks⟧
- V309 · N039: ⟦storms⟧ ⟦Third round⟧ ⟦scheduled for when⟧ ⟦supposed to have fireworks⟧
- V787 · N085: ⟦Brisket⟧ ⟦on⟧ ⟦smoker⟧ ⟦about 3 hours⟧
- V435 · N054: ⟦Apocalypse⟧

Two complete originals illustrate why I question the group:

**V016 · N002**

> Embark on ⟦Sorrento's Savory Stroll⟧ 🍴! Discover the heart of Sorrento's cuisine in an easy 1.09 km journey. Indulge in ⟦3 delightful stops⟧ that promise an unforgettable gastronomic adventure. Perfect for foodies craving local flavors! 🍋🇮🇹 #Sorrento #EasyWalk #GastronomyTrail
>
> https://tinyurl.com/24s8vjcm
> https://comware-city-walk.s3.ap-southeast-2.amazonaws.com/generated_tours/easy/sorrento_s_savory_stroll__a_gastronomic_journey.png

**V327/V328 · N041**

> I think I got grasp on that fog/clarity meat eaters often mention.
> I fell asleep with the kids, very tired and kind of cold. Woke up at five and my brain was started.
> I don't feel I need a coffee to start living today. Fog is lifted and all.
> It might be just a good sleep, but I've had a very good sleep last days. ⟦Usually I'm up like three times⟧, now I just sleep like a bear.
> #fasting #keto #carnivore

The selected numbers are conspicuous, but a tour's three stops and waking three times do not identify the same activity or subject. Reading all six originals did not reveal a stronger connection. I do not regard this as a reliable content-discovery group. This does **not** prove that the algorithm matched only numbers or isolate whether the embeddings, graph construction, or partition objective caused it.

I04 distributes several of these masks more plausibly: smoking duration goes to I04/923 alongside cooking; waking three times goes to I04/928 alongside sleep. A related I03/944 group combines five meals, March 5th, a five-month-old baby, a four-year half-life, and cooking times. I04 also separates several of those into more relevant groups. That is improvement in these placements, not proof that every I04 group is better.

M07 already contained related numerical combinations, including M07/1469. This is not a newly introduced Infomap problem.

## A greeting-heavy group still contains unrelated material

I04/929 has 12 canonical vectors from ten notes. Its complete membership is:

- V385 · N048: ⟦Gentoo⟧
- V764 · N081: ⟦gianguja⟧ ⟦melanger⟧
- V037 · N005: ⟦Gm nostriches⟧
- V310 · N040: ⟦GM⟧ ⟦siamstr⟧
- V762 · N081: ⟦Added⟧ ⟦few⟧ ⟦gianguja jars⟧ ⟦store⟧
- V914 · N099: ⟦GM⟧
- V751 · N080: ⟦Tim came home⟧ ⟦with a gift of a bottle of gin⟧
- V906 · N098: ⟦I'm⟧ ⟦goblin⟧
- V805 · N089: ⟦Gm nostr⟧
- V766 · N081: ⟦gianguja jars⟧ ⟦store⟧
- V486 · N058: ⟦GM Nostr⟧
- V541 · N064: ⟦GM⟧ ⟦💜⟧ ⟦🫂⟧

**V037 · N005 — complete original with mask**

> ⟦Gm nostriches⟧, mid jet lag after landing into Charlotte NC yesterday. Hoping the breakfast will get me going. #grownostr #coffeechain https://image.nostr.build/fc2f76e3c0dc8676f3fcefa27a1bb3a50331ed157d9519630b066085b45ef7b9.jpg

**V766 · N081 — complete original with mask**

> Added a few #⟦gianguja jars⟧ to the ⟦store⟧. Just out of the melanger! https://yabisi.farm/index.php/product/macambo-gianduja/
>
> #foodstr #grownostr #craftchocolate

**V906 · N098 — complete original with mask**

> Don't mind me. ⟦I'm⟧ just that ⟦goblin⟧ in the corner eating a whole tub of kimchi.

The greetings belong together. The complete gianguja and kimchi notes do not contain greetings, so this is not merely a misleading short-mask display hiding a correct note-level relationship. The group lacks an evident subject that would make this particular selection predictable. M07/1409 already combined greetings with Gentoo, goblin, and gianguja; Infomap did not eliminate that problem.

## One storm mask joins Bitcoin-heavy material

I04/931 contains 25 canonical vectors from ten notes. Much of it explicitly mentions Bitcoin, workshops, payments, or related tags. But V301/N039 selects only ⟦Next rounds of storms⟧.

**V402 · N050 — complete original with mask**

> Happy Bitcoin pizza day! While we currently have no ways to get pizza, one of our ⟦goals⟧ by next year is to have ONE ⟦pizza restaurant⟧ in our town of ⟦St Michel de L'Attalaye⟧ and they WILL ⟦accept Bitcoin⟧! #⟦haiti⟧
>
> https://m.primal.net/IKDD.jpg

**V301 · N039 — complete original with mask**

> Well the parade was rained out and umbrellas were ruined.
>
> ⟦Next rounds of storms⟧ look like they will hit just in time for grilling out dinner.
>
> Third round is scheduled for when we are supposed to have fireworks.

The storm note has no Bitcoin connection in its full text. A Bitcoin description would therefore mislead for this member. No description was generated or installed; this is an interpretation of the actual membership for review, not a title-generation evaluation.

## Limits and stopping point

Inspection covered all 43 I02 groups and their 945 original mask records; an independent semantic inspection covered all 28 I03 groups, all 16 I04 groups, all mask records in both runs, and all 100 complete original texts. Relevant originals were also read by the primary reviewer. These are assistant judgments, not user approvals or a numerical accuracy estimate. The examples above are the clearest evidence, not a claim that every unmentioned group passed.

The fixed notes and masks include bare hashtags, highly overlapping masks, and notes contributing very different numbers of vectors. Those conditions may influence the graph. They were not changed here, and this experiment does not isolate their effects. Every vector is assigned a module; a questionable vector was not allowed to become HDBSCAN-style noise. That methodological difference is also not separately tested.

We have finished the agreed comparison. The result does not supply the required hierarchy. It does show that local graph construction changes which relationships Infomap finds, with some useful and some questionable outcomes. Further graph designs, additional corpora, another algorithm, or altered representations would be new experiments requiring discussion.
