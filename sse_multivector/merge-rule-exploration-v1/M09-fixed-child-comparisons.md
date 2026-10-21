# M09: two fixed-child comparisons

Changing a merge rule changes which groups exist later. These calculations therefore compare **exactly the same available groups immediately before an actual M09 merge**. They do not claim to reproduce the whole M01 history, nor that these are the globally best pairs under M01 at that moment.

Scores below are angular-distance aggregates: **smaller ranks earlier**. They are not cosine similarities. The inputs, aliases, exclusions and group memberships are fixed.

## 1. Dairy-in-coffee meets baked-food ingredients before the larger coffee group

Immediately before M09 merge1227, group1088 contains the dairy-in-coffee pair. Both group1204 and group1217 exist. The two rules rank these alternatives differently:

| Fixed alternative for1088 | Directional-mean score | Worst nearest-partner score |
| --- | ---: | ---: |
| Coffee group1204,34 canonical vectors /16 notes | 0.853524 | 1.018150 |
| Pie/bread pair1217,2 vectors /2 notes | 0.909646 | 0.936604 |

M09 chooses1217. The maximum for1088↔1204 comes from V243/N029 ⟦#coffeechain⟧ finding its nearest permitted partner at V504/N060, distance1.018150. For1088↔1217 the maximum is V504↔V666/N072, distance0.936604. Thus the larger coffee group's numerous good matches cannot reduce its worst supported endpoint score. This is a concrete ranking reversal caused by aggregation, not changed geometry.

The pie/bread union can support a broader food/ingredient relationship. The evidence does not establish a correct mandatory parent title. It shows a cost of insisting on the worst nearest partner: the established larger coffee group loses this local comparison even though its average is better. Group1088 later reaches coffee through a branch already containing bread/raw milk.

### Exact group1088 masks

- V356 · N045: ⟦Half & half⟧ ⟦ruining my coffee⟧
- V355 · N045: ⟦Half & half⟧ ⟦ruining my coffee⟧
- V504 · N060: ⟦Made⟧ ⟦coffee with raw cream⟧ ⟦today⟧

### Exact group1217 masks

- V777 · N083: ⟦easter matcha-cashew pie⟧ ⟦no refined sugar⟧
- V666 · N072: ⟦Irish soda bread⟧ ⟦I tried out recently⟧ ⟦currants aren't in season yet⟧

## 2. Sweet-tea variation meets regional food before the other tea masks

Immediately before merge1583, V670/N072 remains a singleton. Group1192 contains hot/morning tea from N042/N080. Group1497 contains local flavors from N002 and the longer tea/bread analogy from N072.

| Fixed alternative for V670 | Directional-mean score | Worst nearest-partner score |
| --- | ---: | ---: |
| Tea group1192 | 1.135019 | 1.209232 |
| Regional-food/analogy group1497 | 1.177957 | 1.177957 |

M09 chooses1497. Against1192 the three eligible distances are V334/V333:1.105206; V730:1.180055; V731:1.209232. The maximum retains V731's full morning/tea/wee combination as the decisive endpoint. Against1497 the N072↔N072 edge is forbidden, so only N002/V019 contributes, at1.177957; V671 has no eligible partner and is recorded as unsupported. Reuniting the two N072 variants is not a new-note gain.

This illustrates both the worst-endpoint tradeoff and the frozen omission boundary. The regional-flavor connection is plausible, but it does not collect all three tea notes. The full alternative-mask audit locates M09's first complete three-note tea counterpart at raw1793; its first displayed counterpart is root1830. Both contain all100 notes. M04/M06/M07/M08 had focused three-note options; M01 did not. These two fixed scores cannot explain all those historical differences.

V670 · N072: ⟦every Southerner has a different way of making sweet tea⟧

### Exact group1192 masks

- V731 · N080: ⟦morning⟧ ⟦tea⟧ ⟦wee⟧ ⟦in that order⟧
- V334 · N042: ⟦I⟧ ⟦want⟧ ⟦hot tea⟧ ⟦too⟧
- V333 · N042: ⟦I want⟧ ⟦hot tea too⟧
- V730 · N080: ⟦got me out of bed⟧ ⟦plus the need for tea and a wee⟧

### Exact group1497 masks

- V019 · N002: ⟦Sorrento's⟧ ⟦Indulge⟧ ⟦local flavors⟧
- V671 · N072: ⟦Soda bread⟧ ⟦recipes vary⟧ ⟦I hear⟧ ⟦much like⟧ ⟦Southerner⟧ ⟦different way of making sweet tea⟧

## First divergence from M01 is not a semantic verdict

The first six child-pair choices are identical, although their scores can differ: at919, M01 scores0.131133 and M09 scores0.133274. At922, M01 adds V656/N071's coffeechain mask to the V865/N095–V126/N017 pair: mean0.218733, maximum0.237401. M09 instead pairs V187/N024 and V043/N005, both coffeechain, at0.221141. Both are related tag-supported choices. This proves the recurrence changes the ordering early; it does not prove that either choice is semantically better, or directly explain all later regressions.

## Complete larger coffee-group masks

All35 original IDs in the34 canonical leaves of1204 are listed, including the V283/V284 alias. These are the actual alternative's members, not a selected sample.

- V494 · N058: ⟦coffee⟧ ⟦hot⟧ ⟦this AM⟧
- V503 · N060: ⟦Made⟧ ⟦coffee⟧ ⟦today⟧
- V343 · N043: ⟦Fetching coffee as a ritual of motion⟧
- V411 · N052: ⟦Rise⟧ ⟦grind coffee beans⟧
- V410 · N052: ⟦grind coffee beans⟧
- V793 · N086: ⟦coffee⟧ ⟦Roasting your own beans⟧
- V243 · N029: ⟦#coffeechain⟧
- V797 · N086: ⟦Sipping⟧ ⟦#coffeechain⟧
- V297 · N038: ⟦#coffeechain⟧
- V656 · N071: ⟦#coffeechain⟧
- V865 · N095: ⟦#coffeechain⟧
- V126 · N017: ⟦#coffeechain⟧
- V281 · N036: ⟦Iced coffee⟧
- V381 · N048: ⟦Coffee⟧
- V244 · N029: ⟦coffee⟧
- V187 · N024: ⟦coffeechain⟧
- V043 · N005: ⟦coffeechain⟧
- V790 · N086: ⟦You’ve had coffee.⟧
- V859 · N095: ⟦Just had⟧ ⟦coffee⟧
- V342 · N043: ⟦Fetching coffee⟧
- V277 · N035: ⟦More coffee⟧
- V280 · N036: ⟦coffee⟧
- V724 · N079: ⟦coffee⟧
- V276 · N035: ⟦coffee⟧
- V653 · N071: ⟦breakfast⟧ ⟦of course⟧ ⟦coffee⟧ ⟦to go with⟧
- V727 · N079: ⟦Is there coffee for me⟧ ⟦🐶⟧
- V860 · N095: ⟦Just had⟧ ⟦coffee⟧ ⟦I need another⟧
- V726 · N079: ⟦Is there coffee for me?⟧
- V791 · N086: ⟦have you had your coffee⟧
- V725 · N079: ⟦🐶⟧
- V283 · N036: ⟦Iced coffee⟧ ⟦in ice⟧
- V284 · N036: ⟦Iced coffee⟧ ⟦in ice⟧
- V278 · N035: ⟦More coffee in cool places⟧
- V279 · N035: ⟦More coffee⟧ ⟦cool places⟧
- V285 · N036: ⟦Iced coffee⟧ ⟦served in ice⟧

## Complete originals for the decisive evidence

The longer coffee-group list above is available with every original in the TUI; this section includes the complete source notes for the decisive masks and both smaller comparisons. Trailing spaces are omitted from these Markdown quotations; the saved source text is unchanged. URLs are original text only; their destinations were not used.

### N002

> Embark on Sorrento's Savory Stroll 🍴! Discover the heart of Sorrento's cuisine in an easy 1.09 km journey. Indulge in 3 delightful stops that promise an unforgettable gastronomic adventure. Perfect for foodies craving local flavors! 🍋🇮🇹 #Sorrento #EasyWalk #GastronomyTrail
>
> https://tinyurl.com/24s8vjcm
> https://comware-city-walk.s3.ap-southeast-2.amazonaws.com/generated_tours/easy/sorrento_s_savory_stroll__a_gastronomic_journey.png

### N029

> #TheRogueBatch #nostr                                                                        #Bitcoin #coffeechain #grownostr 2nd #coffee
>
> https://nostrcheck.me/media/5824c03d29d372b3277cc0b6cb32d4541102a7af0865bda38fbcedec4d454efa/bfd00fd4781a4b157c3aa5e6f2110bf9c45d775f5247d447b4fa866d39e13be2.webp

### N042

> I want some hot tea too.

### N045

> Dear America,
>
> Half & half ≠ cream.
>
> Stop ruining my coffee with it.

### N060

> Made my coffee with raw cream and a raw egg yolk today #coffeechain

### N072

> An Irish soda bread recipe I tried out recently, I was so happy to find a high altitude baking site! The soda bread I usually made doesn't work at the high altitude I live at now, so I was very pleased to see this recipe turned out great! 😁
> I added fresh rosemary and cranberries to it as currants aren't in season yet.
>  Soda bread usually has currants but recipes vary, I hear it's much like how every Southerner has a different way of making sweet tea, they're many ways of doing it
>
> If anyone was curious the sites called
> highaltitudebakes.com
>
> #grownostr🌱 #baking #bread #irishbaking #sodabread
> https://image.nostr.build/d4d3b7e0574fcdb67b0dafcf441c4399a60294ce56031b41b6df2da64951eb30.jpg#m=image%2Fjpeg&dim=768x1020&blurhash=_JFh%23aK%2Bb%7BaLt8WVkYxgO%40axsSobbbofr%7DyYS%25s%3BWCoyWED%2BS%25%25MnhadR%25jEohIqa%24sonhRjjZShV%40xZozRORjo0XTi%7BRlobfln%24ofbcsnRiWAt7n%25bHfjtRe.R%2CtRogRi&x=822d9b4311ea7b98777bca01fdf7376a8ac657161d817b7f9a611936f7d0bae9

### N080

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
> #kgaweekday #katesconnectedpostcardproject #apaintingaday #katerundell #artblog #dailyart #instaart #instaartist #watercolour #artoninstagram #artofinstagram #painting #watercolourpainting #blogger #dailyblogger #winsorandnewton #instadaily #danielsmithwatercolors https://nostrcheck.me/media/18d26089c0617d1b68bd08dfef065cf5eb5316a97eee1c0014d079ed3a6bc815/654867f61c247a385f166f7ba177be4382829feb6c77bfb73131fd7dfa849ce5.webp

### N083

> Made this easter matcha-cashew pie 🥕 Carrots made with real carrots and coconut butter
> No-baking, no refined sugar, gluten free and vegan 🌱 Addictive potential...
>
> https://i.nostr.build/oMKXw.png
> https://i.nostr.build/AadqE.png
> https://i.nostr.build/nW3R7.png
>
> #vegan #glutenfree #raw #rawvegan #foodstr #matcha #food
