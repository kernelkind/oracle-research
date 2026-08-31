# TPv3.81 + MP3.2 six-note probe

TPv3.81 was run once per note. MP3.2 was then run once per generated takeaway. Every call used a newly spawned agent with clean context.

Each numbered item shows the fixed TPv3.81 takeaway followed by the complete source note. Text inside `⟦…⟧` is the exact source text selected by MP3.2.

The analysis keeps three concerns separate:

- TPv3.81 decides what the post communicates.
- MP3.2 aligns one fixed takeaway to exact source text.
- Removing opaque identifiers before SSE is a later encoder-input normalization step, not a mask-selection decision.

## Result

- 23 of 31 takeaway-mask pairs have no clear problem.
- 7 pairs expose an MP3.2 alignment problem.
- 1 pair exposes a TPv3.81 interpretation problem; its MP3.2 alignment is faithful to that incorrect takeaway.

MP3.2 fixed two previously observed mask failures:

- It excluded the unrelated sour-flavor claim from the bitterness mask.
- It excluded `Flexicables installed for` from the non-consumption-based-retirement mask.

Its recurring failure is now narrower: it often selects a sentence containing `this`, `the stock fan`, `the beans`, or an omitted subject without also selecting the earlier fragment that identifies the referent.

## 1. BitAxe fan

### 1.1

**Takeaway:** The author asks BitAxe owners whether they have replaced the device’s fan and, if so, which replacement fan they used.

**Analysis:** No issue found. Both the device and the replacement question are selected.

**Complete note with mask:**

> ⟦Has anyone replaced the fan on their BitAxe?⟧ ⟦If so, what did you use?⟧ I'd normally go with a Noctua but I hate that the NF-A4x20 is the stupid beige/brown colorway.
>
> The stock fan is just getting too loud to deal with. I clean it and within a day or two, it's right back to being loud as hell.

### 1.2

**Takeaway:** The author would ordinarily choose a Noctua fan but strongly dislikes the beige-and-brown color scheme of the Noctua NF-A4x20.

**Analysis:** **MP3.2 problem.** The selected sentence preserves the preference, manufacturer, model, and objection, but it never identifies the selected product as a fan. The earlier `fan` is required to preserve the complete takeaway.

**Complete note with mask:**

> Has anyone replaced the fan on their BitAxe? If so, what did you use? ⟦I'd normally go with a Noctua but I hate that the NF-A4x20 is the stupid beige/brown colorway.⟧
>
> The stock fan is just getting too loud to deal with. I clean it and within a day or two, it's right back to being loud as hell.

### 1.3

**Takeaway:** The BitAxe’s stock fan has become intolerably loud for the author.

**Analysis:** **MP3.2 problem.** `The stock fan` is selected, but the earlier BitAxe anchor is not. The mask therefore loses which device owns the fan.

**Complete note with mask:**

> Has anyone replaced the fan on their BitAxe? If so, what did you use? I'd normally go with a Noctua but I hate that the NF-A4x20 is the stupid beige/brown colorway.
>
> ⟦The stock fan is just getting too loud to deal with.⟧ I clean it and within a day or two, it's right back to being loud as hell.

### 1.4

**Takeaway:** Cleaning the BitAxe’s stock fan reduces its noise only briefly, because it becomes extremely loud again within one or two days.

**Analysis:** **MP3.2 problem.** The mask preserves the cleaning, timing, and renewed noise, but it does not identify the stock fan as belonging to the BitAxe.

**Complete note with mask:**

> Has anyone replaced the fan on their BitAxe? If so, what did you use? I'd normally go with a Noctua but I hate that the NF-A4x20 is the stupid beige/brown colorway.
>
> ⟦The stock fan⟧ is just getting too loud to deal with. ⟦I clean it and within a day or two, it's right back to being loud as hell.⟧

## 2. Books and gardening

### 2.1

**Takeaway:** The author hopes the members of their Nostr community are having a good day.

**Analysis:** No issue found. `nostrichez` supplies the Nostr-community audience.

**Complete note with mask:**

> ⟦Hope the day is going well my nostrichez⟧, I’ve scratched 5 things off my list so far. Gonna spend the rest of the day puttering in the garden.
>
> I’ve been listening to a book on Napoleon all day, but I wanna switch it up. Any good book recommendations?
>
> Btw nostr:npub1example I finished Germs, Guns & steel, that was a great recommend https://example.com/image.jpg

### 2.2

**Takeaway:** The author has completed five items on their list so far today.

**Analysis:** No issue found.

**Complete note with mask:**

> Hope the day is going well my nostrichez, ⟦I’ve scratched 5 things off my list so far.⟧ Gonna spend the rest of the day puttering in the garden.
>
> I’ve been listening to a book on Napoleon all day, but I wanna switch it up. Any good book recommendations?
>
> Btw nostr:npub1example I finished Germs, Guns & steel, that was a great recommend https://example.com/image.jpg

### 2.3

**Takeaway:** The author plans to spend the rest of the day casually working in the garden.

**Analysis:** No issue found.

**Complete note with mask:**

> Hope the day is going well my nostrichez, I’ve scratched 5 things off my list so far. ⟦Gonna spend the rest of the day puttering in the garden.⟧
>
> I’ve been listening to a book on Napoleon all day, but I wanna switch it up. Any good book recommendations?
>
> Btw nostr:npub1example I finished Germs, Guns & steel, that was a great recommend https://example.com/image.jpg

### 2.4

**Takeaway:** After listening to an audiobook about Napoleon throughout the day, the author wants to switch to something different.

**Analysis:** No issue found. The selected sentence preserves the activity, subject, duration, and desire to switch.

**Complete note with mask:**

> Hope the day is going well my nostrichez, I’ve scratched 5 things off my list so far. Gonna spend the rest of the day puttering in the garden.
>
> ⟦I’ve been listening to a book on Napoleon all day, but I wanna switch it up.⟧ Any good book recommendations?
>
> Btw nostr:npub1example I finished Germs, Guns & steel, that was a great recommend https://example.com/image.jpg

### 2.5

**Takeaway:** The author asks their audience for good book recommendations.

**Analysis:** No issue found.

**Complete note with mask:**

> Hope the day is going well my nostrichez, I’ve scratched 5 things off my list so far. Gonna spend the rest of the day puttering in the garden.
>
> I’ve been listening to a book on Napoleon all day, but I wanna switch it up. ⟦Any good book recommendations?⟧
>
> Btw nostr:npub1example I finished Germs, Guns & steel, that was a great recommend https://example.com/image.jpg

### 2.6

**Takeaway:** The author tells a particular Nostr user that they finished Guns, Germs, and Steel and considered the user's recommendation excellent.

**Analysis:** No mask problem. The identifier is the source evidence that a particular user was addressed, so MP3.2 correctly selects it. Whether that opaque token should be removed or replaced before SSE is a separate encoder-input decision.

**Complete note with mask:**

> Hope the day is going well my nostrichez, I’ve scratched 5 things off my list so far. Gonna spend the rest of the day puttering in the garden.
>
> I’ve been listening to a book on Napoleon all day, but I wanna switch it up. Any good book recommendations?
>
> Btw ⟦nostr:npub1example⟧ ⟦I finished Germs, Guns & steel⟧, that was a ⟦great recommend⟧ https://example.com/image.jpg

## 3. Technology surveillance

### 3.1

**Takeaway:** The forces behind what the author describes as a technology surveillance state seek total control.

**Analysis:** No issue found. The two fragments resolve `they` descriptively without inventing a more exact identity.

**Complete note with mask:**

> ⟦they want to control everything⟧..
> ..if you think your #Nostr nsec key is safe on a proprietary OS (#Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate ⟦this tech surveillance state⟧ with any level of sovereignty

### 3.2

**Takeaway:** Believing that a Nostr nsec private key is safe on a proprietary operating system overlooks the broader surveillance threat.

**Analysis:** No issue found. The second fragment supplies the concrete threat behind `the bigger picture`.

**Complete note with mask:**

> they want to control everything..
> ..⟦if you think your #Nostr nsec key is safe on a proprietary OS (#Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture⟧.. ..⟦all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices⟧.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

### 3.3

**Takeaway:** Windows, macOS, iOS, Android, and other proprietary operating systems are saturated with telemetry mechanisms and APIs capable of accessing everything on a user's device.

**Analysis:** No issue found.

**Complete note with mask:**

> they want to control everything..
> ..if you think your #Nostr nsec key is safe on a ⟦proprietary OS (#Windows, #macOS, #iOS, #Android, etc.)⟧ then you are missing the bigger picture.. ..⟦all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices⟧.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

### 3.4

**Takeaway:** The author still uses an iPhone but expects to stop using iOS soon.

**Analysis:** No issue found.

**Complete note with mask:**

> they want to control everything..
> ..if you think your #Nostr nsec key is safe on a proprietary OS (#Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..⟦i'm still on iOS phone-wise, but my days are numbered with that⟧.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

### 3.5

**Takeaway:** The author will probably replace iOS with GrapheneOS.

**Analysis:** No issue found. The first fragment supplies the current operating system and intent to leave; the second supplies the likely replacement.

**Complete note with mask:**

> they want to control everything..
> ..if you think your #Nostr nsec key is safe on a proprietary OS (#Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..⟦i'm still on iOS phone-wise, but my days are numbered with that⟧.. ..⟦likely moving to #GrapheneOS⟧ (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

### 3.6

**Takeaway:** The author already tries to use their phone as little as possible.

**Analysis:** No issue found.

**Complete note with mask:**

> they want to control everything..
> ..if you think your #Nostr nsec key is safe on a proprietary OS (#Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (⟦although i already try to use my phone as little as possible⟧).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

### 3.7

**Takeaway:** The author has already switched to Linux on their computers.

**Analysis:** No issue found.

**Complete note with mask:**

> they want to control everything..
> ..if you think your #Nostr nsec key is safe on a proprietary OS (#Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..⟦i've already switched to #Linux computer-wise⟧.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

### 3.8

**Takeaway:** The author believes free and open-source software is the only way to retain any technological sovereignty while living under pervasive digital surveillance.

**Analysis:** No issue found.

**Complete note with mask:**

> they want to control everything..
> ..if you think your #Nostr nsec key is safe on a proprietary OS (#Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..⟦free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty⟧

## 4. Greenhouse

### 4.1

**Takeaway:** Flexible cables have been installed for the author’s geothermal- and solar-powered greenhouse.

**Analysis:** **TPv3.81 problem.** `Flexicables` may be a name or product. TPv3.81 invents the generic interpretation `Flexible cables`. MP3.2 faithfully selects the source sentence; the mask is not the failure.

**Complete note with mask:**

> ⟦Flexicables installed for our geothermal solar powered greenhouse.⟧ The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.
> This will be the first steps to my non consumption based retirement. https://example.com

### 4.2

**Takeaway:** An existing greenhouse in Alliance, Nebraska, grows pineapples, dates, and citrus fruit.

**Analysis:** No issue found.

**Complete note with mask:**

> Flexicables installed for our geothermal solar powered greenhouse. ⟦The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.⟧
> This will be the first steps to my non consumption based retirement. https://example.com

### 4.3

**Takeaway:** The author sees developing their geothermal- and solar-powered greenhouse as an initial step toward a retirement lifestyle that is not based on consumption.

**Analysis:** No issue found. The mask selects the greenhouse itself and the retirement meaning without importing the separate `Flexicables installed for` detail.

**Complete note with mask:**

> Flexicables installed for ⟦our geothermal solar powered greenhouse⟧. The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.
> ⟦This will be the first steps to my non consumption based retirement.⟧ https://example.com

## 5. Coffee

### 5.1

**Takeaway:** The author bought a 300-gram bag of Tim Hortons medium-roast whole-bean coffee for $9 because of its price and quantity.

**Analysis:** No issue found.

**Complete note with mask:**

> ⟦Bought this bag of Tim Hortons medium roast whole bean coffee because it was 300g for $9.⟧
>
> And I asked myself, “Would this be better if I ground the beans myself and put it through an Aeropress?”
>
> Well, kind of. Somehow, the Aeropress brings out some sour notes. And it transformed something that was once terrible into something tolerable.
>
> But this is still Tim Hortons coffee and it still sacks you over the head with bitterness. Still better than Starbucks, but only barely. And if your choice is between Maxwell House and whole bean Tim Hortons, well, grab this bag.
>
> However, this is still not premium coffee—not by a long shot.

### 5.2

**Takeaway:** The author tested whether grinding the Tim Hortons beans personally and brewing them with an AeroPress would improve the coffee, and found that it improved it somewhat.

**Analysis:** **MP3.2 problem.** The question and `Well, kind of` preserve the test and result, but `the beans` and `this` remain unidentified. The earlier Tim Hortons-coffee anchor is missing.

**Complete note with mask:**

> Bought this bag of Tim Hortons medium roast whole bean coffee because it was 300g for $9.
>
> ⟦And I asked myself, “Would this be better if I ground the beans myself and put it through an Aeropress?”⟧
>
> ⟦Well, kind of.⟧ Somehow, the Aeropress brings out some sour notes. And it transformed something that was once terrible into something tolerable.
>
> But this is still Tim Hortons coffee and it still sacks you over the head with bitterness. Still better than Starbucks, but only barely. And if your choice is between Maxwell House and whole bean Tim Hortons, well, grab this bag.
>
> However, this is still not premium coffee—not by a long shot.

### 5.3

**Takeaway:** Brewing the self-ground Tim Hortons coffee with an AeroPress brought out sour notes and made coffee the author considered terrible become tolerable.

**Analysis:** No issue found. The fragments preserve the product, preparation, sour flavor, and before-and-after judgment.

**Complete note with mask:**

> Bought this bag of ⟦Tim Hortons medium roast whole bean coffee⟧ because it was 300g for $9.
>
> And I asked myself, “Would this be better if I ⟦ground the beans myself and put it through an Aeropress⟧?”
>
> Well, kind of. Somehow, ⟦the Aeropress brings out some sour notes. And it transformed something that was once terrible into something tolerable.⟧
>
> But this is still Tim Hortons coffee and it still sacks you over the head with bitterness. Still better than Starbucks, but only barely. And if your choice is between Maxwell House and whole bean Tim Hortons, well, grab this bag.
>
> However, this is still not premium coffee—not by a long shot.

### 5.4

**Takeaway:** Even after being freshly ground and brewed with an AeroPress, the Tim Hortons coffee remained overwhelmingly bitter.

**Analysis:** No issue found. Unlike MPv3, MP3.2 selects the preparation itself rather than importing the unrelated sour-flavor claim.

**Complete note with mask:**

> Bought this bag of Tim Hortons medium roast whole bean coffee because it was 300g for $9.
>
> And I asked myself, “Would this be better if I ⟦ground the beans myself and put it through an Aeropress⟧?”
>
> Well, kind of. Somehow, the Aeropress brings out some sour notes. And it transformed something that was once terrible into something tolerable.
>
> But ⟦this is still Tim Hortons coffee and it still sacks you over the head with bitterness⟧. Still better than Starbucks, but only barely. And if your choice is between Maxwell House and whole bean Tim Hortons, well, grab this bag.
>
> However, this is still not premium coffee—not by a long shot.

### 5.5

**Takeaway:** The author considers the Tim Hortons whole-bean coffee only slightly better than Starbucks coffee.

**Analysis:** **MP3.2 problem.** `Still better` has no selected subject. The earlier Tim Hortons-coffee anchor is required to identify what is only slightly better than Starbucks.

**Complete note with mask:**

> Bought this bag of Tim Hortons medium roast whole bean coffee because it was 300g for $9.
>
> And I asked myself, “Would this be better if I ground the beans myself and put it through an Aeropress?”
>
> Well, kind of. Somehow, the Aeropress brings out some sour notes. And it transformed something that was once terrible into something tolerable.
>
> But this is still Tim Hortons coffee and it still sacks you over the head with bitterness. ⟦Still better than Starbucks, but only barely.⟧ And if your choice is between Maxwell House and whole bean Tim Hortons, well, grab this bag.
>
> However, this is still not premium coffee—not by a long shot.

### 5.6

**Takeaway:** If choosing between Maxwell House coffee and Tim Hortons whole-bean coffee, the author recommends the Tim Hortons coffee.

**Analysis:** **MP3.2 problem.** Selecting `grab this bag` fixes MPv3's bare `grab`, but `this bag` still lacks its earlier exact antecedent. The initial `this bag of Tim Hortons medium roast whole bean coffee` is needed to make the recommendation target explicit.

**Complete note with mask:**

> Bought this bag of Tim Hortons medium roast whole bean coffee because it was 300g for $9.
>
> And I asked myself, “Would this be better if I ground the beans myself and put it through an Aeropress?”
>
> Well, kind of. Somehow, the Aeropress brings out some sour notes. And it transformed something that was once terrible into something tolerable.
>
> But this is still Tim Hortons coffee and it still sacks you over the head with bitterness. Still better than Starbucks, but only barely. And ⟦if your choice is between Maxwell House and whole bean Tim Hortons, well, grab this bag.⟧
>
> However, this is still not premium coffee—not by a long shot.

### 5.7

**Takeaway:** The author considers the Tim Hortons whole-bean coffee nowhere near premium quality.

**Analysis:** **MP3.2 problem.** `this` is unresolved inside the selected fragment. The earlier Tim Hortons-coffee anchor is missing.

**Complete note with mask:**

> Bought this bag of Tim Hortons medium roast whole bean coffee because it was 300g for $9.
>
> And I asked myself, “Would this be better if I ground the beans myself and put it through an Aeropress?”
>
> Well, kind of. Somehow, the Aeropress brings out some sour notes. And it transformed something that was once terrible into something tolerable.
>
> But this is still Tim Hortons coffee and it still sacks you over the head with bitterness. Still better than Starbucks, but only barely. And if your choice is between Maxwell House and whole bean Tim Hortons, well, grab this bag.
>
> ⟦However, this is still not premium coffee—not by a long shot.⟧

## 6. Poem

### 6.1

**Takeaway:** Chewing tobacco, whether in a pouch or a tin, has become quite rare, and encountering it revived the speaker’s memory of the person being addressed laughing, as if the speaker saw that person again.

**Analysis:** No issue found. The selected title and stanza preserve each part of the compound takeaway.

**Complete note with mask:**

> ⟦Pouch or tin⟧
>
> ⟦Chewing tobacco
> -though quite rare today
> Memories of you laughing
> I saw you again⟧
>
> Maxwell house coffee
> -small amount
> Encased in plastic
> Alone
> Atop grocery shelf
> No longer in a tin
> I brought it home
> So I could remember
> You
> Each day.
>
> -Uncle E.
>
> #poetry

### 6.2

**Takeaway:** The speaker found a small package of Maxwell House coffee encased in plastic and sitting alone atop a grocery-store shelf, rather than in the tin packaging the speaker remembered.

**Analysis:** No mask problem. The selected stanza contains all of the exact source evidence supporting the fixed takeaway. Any concern about whether `found` or `remembered` over-interprets that evidence belongs to TPv3.81, not MP3.2.

**Complete note with mask:**

> Pouch or tin
>
> Chewing tobacco
> -though quite rare today
> Memories of you laughing
> I saw you again
>
> ⟦Maxwell house coffee
> -small amount
> Encased in plastic
> Alone
> Atop grocery shelf
> No longer in a tin⟧
> I brought it home
> So I could remember
> You
> Each day.
>
> -Uncle E.
>
> #poetry

### 6.3

**Takeaway:** The speaker brought the small plastic package of Maxwell House coffee home because its association with the person being addressed would help the speaker remember that person every day.

**Analysis:** No issue found. The first fragment identifies the object; the second preserves the action, purpose, addressee, and repeated timing.

**Complete note with mask:**

> Pouch or tin
>
> Chewing tobacco
> -though quite rare today
> Memories of you laughing
> I saw you again
>
> ⟦Maxwell house coffee
> -small amount
> Encased in plastic⟧
> Alone
> Atop grocery shelf
> No longer in a tin
> ⟦I brought it home
> So I could remember
> You
> Each day.⟧
>
> -Uncle E.
>
> #poetry
