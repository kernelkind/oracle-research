# Every Multi-Note Segment, With Its Evidence

## What this document shows

The experiment turned parts of 50 notes into 194 separate numerical
representations of meaning. It then grouped representations that pointed in
similar directions. Each resulting group is a **segment**. A segment may
contain one vector or many vectors.

This document shows every segment produced from P40 through P90 by the
grouping procedure explained below that contains meaning from at least two
original notes. It does not decide whether any segment is good or bad. It
supplies the complete evidence needed to make that judgment.

**Frozen** below means saved before anyone judged the groupings and left
unchanged during the review.

## How one note became several meaning pieces

For each original note:

1. The frozen TPv3.81 prompt wrote separate **takeaways** describing the
   meanings communicated by the note.
2. For each takeaway, the frozen MPv3.3 prompt selected the exact words in the
   original note that support that meaning. Those selected words are the
   **mask**.
3. The SSE embedding model read the complete note for context, but used the
   selected words to calculate one numerical vector for that meaning.

The frozen experiment produced 194 such meaning pieces, numbered `V000`
through `V193`. The takeaway explains what a piece is intended to mean; its
words were not used to calculate the vector.

All `⟦highlighted fragments⟧` shown under one `VXXX` jointly form that piece's
mask. Masks for different pieces from the same note may overlap because each
piece is calculated independently. Every highlighted fragment below selects
its first occurrence in the note; `V063` explicitly calls this out because
its fragment `Molly` appears three times.

## How the pieces were grouped

The grouping procedure starts with 194 one-vector segments. It compares the
direction of every pair of vectors using cosine similarity: a higher score
means the two represented meanings point in more similar directions.

For every possible pair of segments, the procedure looks at the least-similar
pair of meaning pieces that would be brought together. It joins the two
segments whose least-similar pair has the highest score, provided that score
meets the chosen minimum. It repeats until no remaining join meets the
minimum. The code calls this rule complete linkage.

At the six settings covered here, the same frozen vectors were grouped with
increasingly strict minimums:

| Setting | Every pair in one segment must score at least |
|---|---:|
| P40 | `0.479168` |
| P50 | `0.505010` |
| P60 | `0.538475` |
| P70 | `0.569165` |
| P80 | `0.648779` |
| P90 | `0.687749` |

The six names come from the data. For each of the 194 pieces, the experiment
found its most similar piece from a different note. It sorted those 194 scores.
P40 uses the 40th-percentile score as its minimum, P50 uses the 50th, and P60
uses the 60th; P70 through P90 follow the same rule. P40 through P60 were the
three adjacent settings chosen before anyone judged the meanings. P70 through
P90 are the stricter levels from the same frozen diagnostic sweep, included
here so the higher-resolution segments are not omitted.

P40 through P90 are not probabilities, confidence scores, or accuracy
measurements. They are six stopping points in the same sequence of segment
joins. Raising the minimum can only split an earlier segment. No setting
changes or deletes a meaning piece.

## What the labels mean

- `VXXX` identifies one meaning piece produced by SSE. Its section shows the
  generated takeaway and the complete original note with its selected words
  highlighted.
- `NXX` identifies the original note shown under a vector. The same `NXX` may
  appear under several vectors or segments. The hexadecimal text beside it is
  the beginning of that note's stable ID.
- `SXXX` identifies one exact segment in this frozen review. Two appearances
  share an ID only when they contain exactly the same vectors. The 20 IDs are
  assigned deterministically by the first included setting where the segment
  appears, then by ascending vector membership.

This document assigns `SXXX` IDs only to the 20 segments that contain vectors
from at least two notes. The complete output also contains one-vector and
same-note segments, whose vectors all come from one original note, but they
are outside this multi-note review.

The **least-similar member pair** is the pair with the lowest cosine score
inside a segment. That score explains what the grouping procedure
did; it does not prove that the meanings belong together.

Use a complete source note only to resolve what its selected words refer to.
Do not import meaning from unselected parts of the note.

Judge every segment with the same question:

> Could one precise subject description accurately cover every meaning piece
> in this segment without becoming vague?

Base that decision on each takeaway and its selected source words.

## What is included

Across the six settings, the frozen result contains:

- 17 segments containing pieces from different original notes at P40;
- 14 at P50;
- 11 at P60;
- 10 at P70;
- 8 at P80;
- 3 at P90;
- 63 segment appearances when each setting is counted separately;
- 20 distinct multi-note segments;
- 52 meaning pieces from 27 original notes.

The same exact segment may exist at more than one setting, so the 63
appearances reduce to 20 distinct segments. Three new multi-note segments are
created by splits as the minimum rises: S018 at P60 from S002, S019 at P80
from S018, and S020 at P80 from S016.

A segment containing vectors from only one original note does not contribute
to the multi-note totals above. It remains a valid segment in the full
partition.

Only 52 of the 194 pieces, from 27 of the 50 notes, appear below. The others
never entered a multi-note segment at these six settings.

The pilot also ran an alternative grouping procedure. It is excluded here
because changing the input order changed its segments, and it was not the
procedure behind the groupings being reviewed in this document.

## Segment comparison across settings

**Yes** means that the exact vectors shown in that row form one segment at
that setting. A dash means that exact segment does not exist at that setting;
the segment evidence below explains any split.

**Source notes** lists the set of original notes represented in each segment.

| Segment | Exact vectors | Source notes | P40 | P50 | P60 | P70 | P80 | P90 |
|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| S001 | `V001 V102 V103 V104` | `N01 N02` | Yes | Yes | — | — | — | — |
| S002 | `V003 V004 V023 V099 V101` | `N01 N03 N04` | Yes | Yes | — | — | — | — |
| S003 | `V005 V116` | `N05 N06` | Yes | Yes | Yes | Yes | Yes | — |
| S004 | `V007 V008 V009 V105 V106 V107` | `N07 N08` | Yes | Yes | Yes | Yes | Yes | — |
| S005 | `V010 V028` | `N07 N09` | Yes | Yes | Yes | Yes | Yes | Yes |
| S006 | `V013 V152` | `N10 N11` | Yes | — | — | — | — | — |
| S007 | `V029 V030 V031 V050` | `N12 N13` | Yes | Yes | Yes | Yes | Yes | — |
| S008 | `V035 V051 V060` | `N12 N13 N14` | Yes | Yes | Yes | Yes | Yes | Yes |
| S009 | `V062 V186` | `N15 N16` | Yes | Yes | Yes | Yes | — | — |
| S010 | `V063 V170` | `N15 N17` | Yes | — | — | — | — | — |
| S011 | `V076 V095 V096 V097` | `N18 N19` | Yes | Yes | Yes | Yes | — | — |
| S012 | `V078 V092` | `N20 N21` | Yes | — | — | — | — | — |
| S013 | `V094 V119` | `N21 N22` | Yes | Yes | Yes | — | — | — |
| S014 | `V100 V114` | `N04 N23` | Yes | Yes | — | — | — | — |
| S015 | `V109 V123` | `N23 N24` | Yes | Yes | Yes | Yes | Yes | — |
| S016 | `V118 V127 V133 V136` | `N22 N24 N25` | Yes | Yes | Yes | Yes | — | — |
| S017 | `V174 V175 V192 V193` | `N26 N27` | Yes | Yes | — | — | — | — |
| S018 | `V023 V099 V101` | `N03 N04` | — | — | Yes | Yes | — | — |
| S019 | `V023 V099` | `N03 N04` | — | — | — | — | Yes | — |
| S020 | `V118 V127` | `N22 N24` | — | — | — | — | Yes | Yes |

## Segment evidence

Each segment below is self-contained. For every member vector, `⟦…⟧`
marks the exact source words selected by its mask. All unmarked text is
still shown because SSE received the complete note as context, but that
text was not selected by this vector's mask.

### S001

- **Vectors:** `V001 V102 V103 V104`
- **Exists at:** P40 and P50
- **Least-similar member pair:** `V001 ↔ V103` · cosine `0.537917`
- **Other included settings:** At P60, these vectors form the one-vector segment `[V001]` and the same-note segment `[V102 V103 V104]`, whose vectors all come from N02.

#### V001 · source N01 · `7e2e4e93cf8f…`

**Takeaway:** The author wants to determine the best way to operate the Bitcoin miner.

**Complete source note with this vector's mask:**

> This week I just let the miner running to keep temperatures for a minimum and save the #statistics.
> ⟦I want to find the best way how to run the miner.⟧ So far it only starts when it is below a specific temperature (with a day/night mode)
>
> Meanwhile I do a bit of programming to start up the miner when I have #solar #energy  left. And to have statistics how much solar energy is used for the miner.
>
> Anyhow in the winter days almost everything is required to heat the house so it won’t be much anyhow.
>
> #orangery #greenhouse   #grownostr #miner ⟦#bitcoin⟧ #nostr #btc

#### V102 · source N02 · `e09b8c19f52a…`

**Takeaway:** The author has just ordered a BitAxe, a device for mining Bitcoin.

**Complete source note with this vector's mask:**

> ⟦Just ordered a BitAxe.⟧ Super excited to finally start ⟦mining⟧ at home and contributing to the network.

#### V103 · source N02 · `e09b8c19f52a…`

**Takeaway:** The author is very excited to begin mining Bitcoin at home, something they have been looking forward to doing.

**Complete source note with this vector's mask:**

> ⟦Just ordered a BitAxe.⟧ ⟦Super excited to finally start mining at home⟧ and contributing to the network.

#### V104 · source N02 · `e09b8c19f52a…`

**Takeaway:** The author expects their home Bitcoin mining to contribute computing power to the Bitcoin network.

**Complete source note with this vector's mask:**

> Just ordered a ⟦BitAxe⟧. Super excited to finally ⟦start mining at home and contributing to the network⟧.

### S002

- **Vectors:** `V003 V004 V023 V099 V101`
- **Exists at:** P40 and P50
- **Least-similar member pair:** `V004 ↔ V099` · cosine `0.517907`
- **Other included settings:** At P60, these vectors form the same-note segment `[V003 V004]`, whose vectors both come from N01, and S018, whose membership is `[V023 V099 V101]`.

#### V003 · source N01 · `7e2e4e93cf8f…`

**Takeaway:** The author is programming the Bitcoin miner to start when surplus solar energy is available and to record how much solar energy the miner uses.

**Complete source note with this vector's mask:**

> This week I just let the miner running to keep temperatures for a minimum and save the #statistics.
> I want to find the best way how to run the miner. So far it only starts when it is below a specific temperature (with a day/night mode)
>
> Meanwhile ⟦I do a bit of programming to start up the miner when I have #solar #energy  left. And to have statistics how much solar energy is used for the miner.⟧
>
> Anyhow in the winter days almost everything is required to heat the house so it won’t be much anyhow.
>
> #orangery #greenhouse   #grownostr #miner ⟦#bitcoin⟧ #nostr #btc

#### V004 · source N01 · `7e2e4e93cf8f…`

**Takeaway:** During winter, heating the author’s house requires nearly all the available energy, so little surplus solar energy will remain for the Bitcoin miner.

**Complete source note with this vector's mask:**

> This week I just let the miner running to keep temperatures for a minimum and save the #statistics.
> I want to find the best way how to run the miner. So far it only starts when it is below a specific temperature (with a day/night mode)
>
> Meanwhile I do a bit of programming to ⟦start up the miner when I have #solar #energy  left⟧. And to have statistics how much solar energy is used for the miner.
>
> Anyhow ⟦in the winter days almost everything is required to heat the house so it won’t be much⟧ anyhow.
>
> #orangery #greenhouse   #grownostr ⟦#miner #bitcoin⟧ #nostr #btc

#### V023 · source N03 · `974dd5c02c7a…`

**Takeaway:** In the future, solar energy will account for the vast majority of power generation.

**Complete source note with this vector's mask:**

> ⟦Solar power will be the vast majority of power generation in the future⟧

#### V099 · source N04 · `a59ca772c163…`

**Takeaway:** The shared greenhouse is designed to use geothermal and solar energy.

**Complete source note with this vector's mask:**

> Flexicables installed for ⟦our geothermal solar powered greenhouse⟧. The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.
> This will be the first steps to my non consumption based retirement. https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

#### V101 · source N04 · `a59ca772c163…`

**Takeaway:** The author views the greenhouse project as an initial step toward a retirement that is not consumption-based.

**Complete source note with this vector's mask:**

> Flexicables installed for ⟦our geothermal solar powered greenhouse⟧. The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.
> ⟦This will be the first steps to my non consumption based retirement.⟧ https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

### S003

- **Vectors:** `V005 V116`
- **Exists at:** P40, P50, P60, P70, and P80
- **Least-similar member pair:** `V005 ↔ V116` · cosine `0.656710`
- **Other included settings:** At P90, these vectors form two one-vector segments: `[V005]` and `[V116]`.

#### V005 · source N05 · `f81f01d4d50f…`

**Takeaway:** A linked science article discusses research showing that lightly spraying coffee beans with water before grinding can reduce waste and produce tastier espresso.

**Complete source note with this vector's mask:**

> ⟦Why a spritz of water before grinding coffee yields better results⟧
>
> Comments ( https://news.ycombinator.com/item?id=38554310 )
>
> https://arstechnica.com/science/2023/12/study-why-a-spritz-of-water-before-grinding-coffee-yields-less-waste-tastier-espresso/

#### V116 · source N06 · `f15fe96ab816…`

**Takeaway:** The author is typing the social-media post while drinking coffee they consider delicious.

**Complete source note with this vector's mask:**

> I was about to say good morning but I’m not, instead ⟦I’m typing this while drinking my delicious coffee.⟧

### S004

- **Vectors:** `V007 V008 V009 V105 V106 V107`
- **Exists at:** P40, P50, P60, P70, and P80
- **Least-similar member pair:** `V008 ↔ V107` · cosine `0.682637`
- **Other included settings:** At P90, these vectors form the same-note segment `[V007 V008 V009]` from N07 and the same-note segment `[V105 V106 V107]` from N08.

#### V007 · source N07 · `056e64662570…`

**Takeaway:** The author suggests that merely drinking ordinary coffee differs from experiencing coffee made personally one’s own by roasting the beans oneself.

**Complete source note with this vector's mask:**

> ⟦You’ve had coffee. But have you had your coffee?”⟧
> https://blossom.primal.net/1379b90996b8ecb2f4fdef6756fd61c4ab964fa19f9e1505950e10a4d97640dd.jpg
> ⟦Roasting your own beans means discovering a taste profile that’s uniquely yours.⟧ It’s a personal journey that no bag of pre-roasted coffee can replicate.
>
> Sipping  @ #coffeechain
>
> #HotTake ☕

#### V008 · source N07 · `056e64662570…`

**Takeaway:** Roasting one’s own coffee beans enables a person to discover a flavor profile unique to their tastes.

**Complete source note with this vector's mask:**

> You’ve had coffee. But have you had your coffee?”
> https://blossom.primal.net/1379b90996b8ecb2f4fdef6756fd61c4ab964fa19f9e1505950e10a4d97640dd.jpg
> ⟦Roasting your own beans means discovering a taste profile that’s uniquely yours.⟧ It’s a personal journey that no bag of pre-roasted coffee can replicate.
>
> Sipping  @ #coffeechain
>
> #HotTake ☕

#### V009 · source N07 · `056e64662570…`

**Takeaway:** The author views self-roasting and discovering a personal coffee profile as an individual journey that pre-roasted coffee cannot reproduce.

**Complete source note with this vector's mask:**

> You’ve had coffee. But have you had your coffee?”
> https://blossom.primal.net/1379b90996b8ecb2f4fdef6756fd61c4ab964fa19f9e1505950e10a4d97640dd.jpg
> ⟦Roasting your own beans means discovering a taste profile that’s uniquely yours. It’s a personal journey that no bag of pre-roasted coffee can replicate.⟧
>
> Sipping  @ #coffeechain
>
> #HotTake ☕

#### V105 · source N08 · `2dc50a304a2f…`

**Takeaway:** The author believes decaffeinated-coffee drinkers are the most genuine coffee enthusiasts because they drink coffee for its flavor and overall experience rather than for caffeine.

**Complete source note with this vector's mask:**

> ⟦Decafe coffee drinkers are the purist coffee enthusiasts of them all as they do it for the experience and flavour.⟧ Unlike the caffeine addicted heathens. Change my mind.

#### V106 · source N08 · `2dc50a304a2f…`

**Takeaway:** The author disparagingly contrasts decaffeinated-coffee enthusiasts with caffeine-addicted coffee drinkers, whom the author portrays as less pure in their appreciation of coffee.

**Complete source note with this vector's mask:**

> ⟦Decafe coffee drinkers are the purist coffee enthusiasts of them all as they do it for the experience and flavour.⟧ ⟦Unlike the caffeine addicted heathens.⟧ Change my mind.

#### V107 · source N08 · `2dc50a304a2f…`

**Takeaway:** The author challenges others to change this opinion about decaffeinated-coffee drinkers.

**Complete source note with this vector's mask:**

> ⟦Decafe coffee drinkers are the purist coffee enthusiasts of them all as they do it for the experience and flavour. Unlike the caffeine addicted heathens.⟧ ⟦Change my mind.⟧

### S005

- **Vectors:** `V010 V028`
- **Exists at:** P40, P50, P60, P70, P80, and P90
- **Least-similar member pair:** `V010 ↔ V028` · cosine `0.759397`

#### V010 · source N07 · `056e64662570…`

**Takeaway:** The author says they are sipping coffee and frames the post as a provocative opinion in a coffee-focused social-media discussion.

**Complete source note with this vector's mask:**

> You’ve had coffee. But have you had your coffee?”
> https://blossom.primal.net/1379b90996b8ecb2f4fdef6756fd61c4ab964fa19f9e1505950e10a4d97640dd.jpg
> Roasting your own beans means discovering a taste profile that’s uniquely yours. It’s a personal journey that no bag of pre-roasted coffee can replicate.
>
> ⟦Sipping⟧  @ ⟦#coffeechain⟧
>
> ⟦#HotTake⟧ ☕

#### V028 · source N09 · `f4c5aa5f1802…`

**Takeaway:** The author presented the post as part of a social-media coffee chain.

**Complete source note with this vector's mask:**

> Made my coffee with raw cream and a raw egg yolk today ⟦#coffeechain⟧

### S006

- **Vectors:** `V013 V152`
- **Exists at:** P40
- **Least-similar member pair:** `V013 ↔ V152` · cosine `0.501598`
- **Other included settings:** At P50 through P90, these vectors form two one-vector segments: `[V013]` and `[V152]`.

#### V013 · source N10 · `74694da41f36…`

**Takeaway:** The author needs to retrieve wire from a personal trailer located at one of the author’s job sites.

**Complete source note with this vector's mask:**

> #proofofwork
>
> Got 14 460w solar panels series and ready to connect. ⟦Have to grab some wire out of my trailer on one of the jobs.⟧ This weekend project. might be able to charge a car or run a Bitcoin miner off this successfully. I still have six extra panels back there and four that are working up top on the roof.
>
> https://m.primal.net/Mkft.jpg

#### V152 · source N11 · `e79637da76e4…`

**Takeaway:** The author needs to replace a fuel-tank grommet on a post-hole digger they share or own with others.

**Complete source note with this vector's mask:**

> ⟦We need to replace a grommet on the fuel tank of our post hole digger.⟧
> Searching Amazon and eBay the part I need to buy is $11 OR you can get a 70 piece spares kit for $7.
> Why is it like this? This is why minimalism is an active choice.

### S007

- **Vectors:** `V029 V030 V031 V050`
- **Exists at:** P40, P50, P60, P70, and P80
- **Least-similar member pair:** `V030 ↔ V050` · cosine `0.664877`
- **Other included settings:** At P90, these vectors form the same-note segment `[V029 V030 V031]` from N12 and the one-vector segment `[V050]`.

#### V029 · source N12 · `7adcfe1ab26f…`

**Takeaway:** The author believes that the forces behind pervasive proprietary-technology surveillance seek total control.

**Complete source note with this vector's mask:**

> ⟦they want to control everything⟧..
> ..if you think your #Nostr nsec key is safe on ⟦a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.)⟧ then you are missing the bigger picture.. ..⟦all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices⟧.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate ⟦this tech surveillance state⟧ with any level of sovereignty

#### V030 · source N12 · `7adcfe1ab26f…`

**Takeaway:** The author warns that treating a Nostr nsec private key as secure on an operating system they regard as proprietary—such as Windows, macOS, iOS, or Android—ignores broader surveillance and device-access risks.

**Complete source note with this vector's mask:**

> they want to control everything..
> ..⟦if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture⟧.. ..⟦all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices⟧.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

#### V031 · source N12 · `7adcfe1ab26f…`

**Takeaway:** The author claims that Windows, macOS, iOS, Android, and similar operating systems are saturated with telemetry mechanisms and APIs capable of accessing everything on a user's device.

**Complete source note with this vector's mask:**

> they want to control everything..
> ..if you think your #Nostr nsec key is safe on a proprietary OS ( ⟦#Windows, #macOS, #iOS, #Android, etc.⟧) then you are missing the bigger picture.. ..⟦all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices⟧.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

#### V050 · source N13 · `735104aa3dfc…`

**Takeaway:** Pypush can now send and receive messages through Apple’s iMessage service on any platform.

**Complete source note with this vector's mask:**

> It's ready! ⟦#pypush can now send and receive #iMessage, on any platform⟧, completely server-less and open-source! 🎉
>
> https://github.com/JJTech0130/pypush

### S008

- **Vectors:** `V035 V051 V060`
- **Exists at:** P40, P50, P60, P70, P80, and P90
- **Least-similar member pair:** `V035 ↔ V060` · cosine `0.717748`

#### V035 · source N12 · `7adcfe1ab26f…`

**Takeaway:** The author believes free and open-source software is the only way to retain any degree of technological sovereignty within what they view as a technology-surveillance state.

**Complete source note with this vector's mask:**

> they want to control everything..
> ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..⟦free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty⟧

#### V051 · source N13 · `735104aa3dfc…`

**Takeaway:** Pypush is entirely serverless and open-source.

**Complete source note with this vector's mask:**

> It's ready! ⟦#pypush⟧ can now send and receive #iMessage, on any platform, ⟦completely server-less and open-source⟧! 🎉
>
> https://github.com/JJTech0130/pypush

#### V060 · source N14 · `bbe63b10f768…`

**Takeaway:** The author is nearing the point where their entire software stack consists of free and open-source software.

**Complete source note with this vector's mask:**

> ⟦Getting close to 100% of my software stack being free and open source.⟧

### S009

- **Vectors:** `V062 V186`
- **Exists at:** P40, P50, P60, and P70
- **Least-similar member pair:** `V062 ↔ V186` · cosine `0.569165`
- **Other included settings:** At P80 and P90, these vectors form two one-vector segments: `[V062]` and `[V186]`.

#### V062 · source N15 · `aa269973db71…`

**Takeaway:** Molly is a fork of the Signal messaging app designed to offer additional security.

**Complete source note with this vector's mask:**

> I'm thinking I'll regularly post about open source tech I find useful.
>
> ⟦Molly is a fork of Signal, made to be more secure.⟧
>
> Some of it's features include:
> No proprietary blobs/code.
> Molly protects your messages with passphrase encryption.
> The app can lock down automatically after a set time of not being opened.
> Molly, "Securely shreds sensitive data from RAM."
> You can create automatic backups
> It even supports setting an app proxy through Tor via Orbot.
>
> Available on their own Fdroid repo:
> https://molly.im/

#### V186 · source N16 · `d94ef8a432ec…`

**Takeaway:** Larry Ellison has said that real-time surveillance is beneficial because it keeps people’s behavior in check.

**Complete source note with this vector's mask:**

> ⟦Larry Ellison⟧ wants to put all US data in one big AI system - From the billionaire who ⟦said real-time surveillance is good for keeping us in check⟧
> https://www.theregister.com/2025/02/12/larry_ellison_wants_all_data/

### S010

- **Vectors:** `V063 V170`
- **Exists at:** P40
- **Least-similar member pair:** `V063 ↔ V170` · cosine `0.498993`
- **Other included settings:** At P50 through P90, these vectors form two one-vector segments: `[V063]` and `[V170]`.

#### V063 · source N15 · `aa269973db71…`

**Takeaway:** Molly contains no proprietary code or binary blobs.

**Complete source note with this vector's mask:**

> I'm thinking I'll regularly post about open source tech I find useful.
>
> ⟦Molly⟧ is a fork of Signal, made to be more secure.
>
> Some of it's features include:
> ⟦No proprietary blobs/code.⟧
> Molly protects your messages with passphrase encryption.
> The app can lock down automatically after a set time of not being opened.
> Molly, "Securely shreds sensitive data from RAM."
> You can create automatic backups
> It even supports setting an app proxy through Tor via Orbot.
>
> Available on their own Fdroid repo:
> https://molly.im/

#### V170 · source N17 · `53b0f8fe4650…`

**Takeaway:** The author says the message is not an attempt to force anyone to use the author's preferred communication protocol.

**Complete source note with this vector's mask:**

> Despite it being easier to self-host XMPP and less expensive on resources, Matrix is more popular.  Why?
>
> The real reason Matrix is popular is because corporate and FOSS developers like the encrypted group chats for their internal use.  (XMPP is NOT encrypted group chats).  So then devs host a Matrix room to answer end-user questions, and having all these rooms encourages overall adoption.
>
> The part that's not usually mentioned, is that only the devs usually use self-hosted Matrix servers, and the vast majority of the public uses Matrix.org which is on Cloudflare with Gmail verification.
>
> In theory Matrix is decentralized, but in the real world, everyone gets Cloudflare metadata surveillance, and uses the same Element client.
>
> ⟦Here's my core message:⟧
> Try to be Self-Sovereign with what you're doing.
> If you're hosting a website, 1 core VPS for email, whatever.  Then host your own XMPP/Matrix.  XMPP uses so little resources, it's near free.
>
> If a VPS is really not for you, even if you pay someone like me $100 to set it up:
> https://simplifiedprivacy.com/email-cloud-combo/index.html
>
> Then public SimpleX/Session servers are right for you.  That's fine.  ⟦This isn't about me trying to force you to use my favorite protocol.⟧  It's about you not using Cloudflare (and Protonmail seeing your metadata) and thinking you're "doing privacy".

### S011

- **Vectors:** `V076 V095 V096 V097`
- **Exists at:** P40, P50, P60, and P70
- **Least-similar member pair:** `V076 ↔ V096` · cosine `0.610311`
- **Other included settings:** At P80 and P90, these vectors form the one-vector segment `[V076]` and the same-note segment `[V095 V096 V097]`, whose vectors all come from N19.

#### V076 · source N18 · `84aba98daa2c…`

**Takeaway:** Cleaning the stock BitAxe fan quiets it for only a day or two before it becomes extremely loud again.

**Complete source note with this vector's mask:**

> Has anyone replaced ⟦the fan on their BitAxe⟧? If so, what did you use? I'd normally go with a Noctua but I hate that the NF-A4x20 is the stupid beige/brown colorway.
>
> ⟦The stock fan⟧ is just getting too loud to deal with. ⟦I clean it and within a day or two, it's right back to being loud as hell.⟧

#### V095 · source N19 · `dcd6544eba8e…`

**Takeaway:** The author’s Avalon Nano 3 cryptocurrency miner has become noticeably louder after nearly a year of use despite being kept clean.

**Complete source note with this vector's mask:**

> ⟦After nearly a year of mining with the #AvalonNano3, it’s noticeably getting louder over time-even though I keep it clean.⟧ The difference is clear! In comparison, I’ve had the 4 #Bitaxe for about the same period, and its noise level has remained consistent. My prediction is that Avalons gonna die much more faster than Bitaxe ⏳

#### V096 · source N19 · `dcd6544eba8e…`

**Takeaway:** The author’s four Bitaxe cryptocurrency miners have maintained consistent noise levels over roughly the same period in which the Avalon Nano 3 became louder.

**Complete source note with this vector's mask:**

> ⟦After nearly a year of mining with the #AvalonNano3, it’s noticeably getting louder over time⟧-even though I keep it clean. The difference is clear! ⟦In comparison, I’ve had the 4 #Bitaxe for about the same period, and its noise level has remained consistent.⟧ My prediction is that Avalons gonna die much more faster than Bitaxe ⏳

#### V097 · source N19 · `dcd6544eba8e…`

**Takeaway:** Based on this contrast, the author predicts that the Avalon Nano 3 will fail much sooner than the Bitaxe miners.

**Complete source note with this vector's mask:**

> ⟦After nearly a year of mining with the #AvalonNano3, it’s noticeably getting louder over time-even though I keep it clean.⟧ The difference is clear! ⟦In comparison, I’ve had the 4 #Bitaxe for about the same period, and its noise level has remained consistent.⟧ ⟦My prediction is that Avalons gonna die much more faster than Bitaxe⟧ ⏳

### S012

- **Vectors:** `V078 V092`
- **Exists at:** P40
- **Least-similar member pair:** `V078 ↔ V092` · cosine `0.482704`
- **Other included settings:** At P50 through P90, these vectors form two one-vector segments: `[V078]` and `[V092]`.

#### V078 · source N20 · `4166411750a2…`

**Takeaway:** The author directs the book-choice question to Nostr users, including its book-focused and “plebchain” communities.

**Complete source note with this vector's mask:**

> ⟦Trying to decide what book I should read next 🤔 What one would you read?⟧
>
> The Mandibles
> The Mobile Wave
> The Fourth revolution
> Fiat Food
> The Principles of Economics
> Broken Money
> Bitcoin is Venice
>
> ⟦#asknostr #bookstr #plebchain⟧

#### V092 · source N21 · `38c864c05535…`

**Takeaway:** Based on what they have read so far, the author considers Elizondo’s book “Imminent” authentic, well written, and gripping.

**Complete source note with this vector's mask:**

> ⟦Elizondo’s Imminent is an authentic, well-written page turner so far as I’ve read.⟧ If I didn’t have to work tomorrow I’d finish the whole dang thing tonight. Lots of puzzle pieces shifting into place in the back of my mind 🛸
>
> #uap
> #plebchain

### S013

- **Vectors:** `V094 V119`
- **Exists at:** P40, P50, and P60
- **Least-similar member pair:** `V094 ↔ V119` · cosine `0.538615`
- **Other included settings:** At P70 through P90, these vectors form two one-vector segments: `[V094]` and `[V119]`.

#### V094 · source N21 · `38c864c05535…`

**Takeaway:** Reading “Imminent” is prompting the author to mentally connect and reorganize many ideas related to unidentified anomalous phenomena.

**Complete source note with this vector's mask:**

> ⟦Elizondo’s Imminent⟧ is an authentic, well-written page turner ⟦so far as I’ve read⟧. If I didn’t have to work tomorrow I’d finish the whole dang thing tonight. ⟦Lots of puzzle pieces shifting into place in the back of my mind⟧ 🛸
>
> ⟦#uap⟧
> #plebchain

#### V119 · source N22 · `075b407e91d5…`

**Takeaway:** The author says it took them a lifetime to understand why remaining true to oneself is profound advice.

**Complete source note with this vector's mask:**

> ⟦"Just be yourself"⟧ is the best of all the bad ⟦advice⟧ you ever got. Wisdom hidden in plain sight. ⟦It took me a lifetime to understand why this is deep.⟧

### S014

- **Vectors:** `V100 V114`
- **Exists at:** P40 and P50
- **Least-similar member pair:** `V100 ↔ V114` · cosine `0.507426`
- **Other included settings:** At P60 through P90, these vectors form two one-vector segments: `[V100]` and `[V114]`.

#### V100 · source N04 · `a59ca772c163…`

**Takeaway:** An existing greenhouse in Alliance, Nebraska, grows pineapples, dates, and citrus fruit.

**Complete source note with this vector's mask:**

> Flexicables installed for our geothermal solar powered greenhouse. ⟦The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.⟧
> This will be the first steps to my non consumption based retirement. https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

#### V114 · source N23 · `2c054d399715…`

**Takeaway:** The author says that sunshine, a cool breeze, doves, wrens, robins, squirrels, shade from an oak tree, and a blooming crossvine together make for a good Saturday.

**Complete source note with this vector's mask:**

> Annie's Saturday Morning Thoughts
>
> Don't assume that everyone who agrees with you in public agrees with you in private. 😏
>
> The wren on the fence has been chirping for a while. Must have good lungs.
>
> Only the things you choose without pressure define you. The rest is a facade. 🤥
>
> Flavored coffee is nice but can get old if you have it every day.
>
> ⟦Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree and a crossvine in bloom. This is the recipe for a good Saturday.⟧ 🤗

### S015

- **Vectors:** `V109 V123`
- **Exists at:** P40, P50, P60, P70, and P80
- **Least-similar member pair:** `V109 ↔ V123` · cosine `0.656426`
- **Other included settings:** At P90, these vectors form two one-vector segments: `[V109]` and `[V123]`.

#### V109 · source N23 · `2c054d399715…`

**Takeaway:** A person should not assume that everyone who publicly expresses agreement with them privately holds the same view.

**Complete source note with this vector's mask:**

> Annie's Saturday Morning Thoughts
>
> ⟦Don't assume that everyone who agrees with you in public agrees with you in private.⟧ 😏
>
> The wren on the fence has been chirping for a while. Must have good lungs.
>
> Only the things you choose without pressure define you. The rest is a facade. 🤥
>
> Flavored coffee is nice but can get old if you have it every day.
>
> Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree and a crossvine in bloom. This is the recipe for a good Saturday. 🤗

#### V123 · source N24 · `4a3184dbd492…`

**Takeaway:** In societies that value conformity and obedience, people who dare to think independently are often excluded and mocked.

**Complete source note with this vector's mask:**

> ⟦In a society that values conformity and obedience, the individual who dares to think for themselves is often ostracized and ridiculed.⟧ These nonconformists, these outcasts, are the true pioneers of society, the ones who push us to question our assumptions and expand our horizons.
> They are the ones who are not afraid to be different, to be themselves.
> If you find yourself feeling like an outsider, like you don't fit in with the crowd, that's a good thing. It means that you have the potential to make a real difference in the world. Don't be afraid to be yourself, to follow your own path. The world needs your unique perspective. https://image.nostr.build/8a30d246bf5f8ece1abf2a5a6798252c868e7c58a0def48102453d52675533b9.jpg

### S016

- **Vectors:** `V118 V127 V133 V136`
- **Exists at:** P40, P50, P60, and P70
- **Least-similar member pair:** `V118 ↔ V133` · cosine `0.577648`
- **Other included settings:** At P80, these vectors form S020 (`[V118 V127]`) and the one-vector segments `[V133]` and `[V136]`. At P90, S020 remains unchanged.

#### V118 · source N22 · `075b407e91d5…`

**Takeaway:** The seemingly obvious advice to remain true to oneself contains profound wisdom that is easy to overlook.

**Complete source note with this vector's mask:**

> ⟦"Just be yourself"⟧ is the best of all the bad advice you ever got. ⟦Wisdom hidden in plain sight.⟧ It took me a lifetime to understand why ⟦this is deep.⟧

#### V127 · source N24 · `4a3184dbd492…`

**Takeaway:** People who feel like outsiders should not fear being themselves or following their own paths, because the world needs their unique perspectives.

**Complete source note with this vector's mask:**

> In a society that values conformity and obedience, the individual who dares to think for themselves is often ostracized and ridiculed. These nonconformists, these outcasts, are the true pioneers of society, the ones who push us to question our assumptions and expand our horizons.
> They are the ones who are not afraid to be different, to be themselves.
> ⟦If you find yourself feeling like an outsider⟧, like you don't fit in with the crowd, that's a good thing. It means that you have the potential to make a real difference in the world. ⟦Don't be afraid to be yourself, to follow your own path. The world needs your unique perspective.⟧ https://image.nostr.build/8a30d246bf5f8ece1abf2a5a6798252c868e7c58a0def48102453d52675533b9.jpg

#### V133 · source N25 · `adb5912a5214…`

**Takeaway:** Integrity, authenticity, and an inner moral compass can guide a person through challenges and confrontations while helping them remain firm in their convictions and true to themselves.

**Complete source note with this vector's mask:**

> In a world where titles and positions often dictate power dynamics, it's easy to feel overshadowed or intimidated by those in authority. But here's a simple truth: if your daily actions and intentions stem from an ethical and moral foundation, you need not worry or be bothered by anyone else, regardless of their temporary title or status. ⟦Your integrity, authenticity, and inner compass will guide you through any challenge or confrontation, ensuring that you remain steadfast in your convictions and true to yourself.⟧ So, trust in the strength of your character and the righteousness of your deeds, and let go of the need for external validation or approval. When you walk with integrity, you walk with unwavering confidence and peace of mind, unshaken by the winds of authority or influence. Stay true to yourself, and the rest will fall into place.

#### V136 · source N25 · `adb5912a5214…`

**Takeaway:** By remaining true to oneself, a person can trust that other aspects of life will fall into place.

**Complete source note with this vector's mask:**

> In a world where titles and positions often dictate power dynamics, it's easy to feel overshadowed or intimidated by those in authority. But here's a simple truth: if your daily actions and intentions stem from an ethical and moral foundation, you need not worry or be bothered by anyone else, regardless of their temporary title or status. Your integrity, authenticity, and inner compass will guide you through any challenge or confrontation, ensuring that you remain steadfast in your convictions and true to yourself. So, trust in the strength of your character and the righteousness of your deeds, and let go of the need for external validation or approval. When you walk with integrity, you walk with unwavering confidence and peace of mind, unshaken by the winds of authority or influence. ⟦Stay true to yourself, and the rest will fall into place.⟧

### S017

- **Vectors:** `V174 V175 V192 V193`
- **Exists at:** P40 and P50
- **Least-similar member pair:** `V175 ↔ V193` · cosine `0.518401`
- **Other included settings:** At P60 through P90, these vectors form the same-note segment `[V174 V175]` from N26 and the same-note segment `[V192 V193]` from N27.

#### V174 · source N26 · `c36ed58c0f53…`

**Takeaway:** The author claims that governments or comparable financial authorities are moving beyond restricting access to money toward total financial control, under which individuals will no longer genuinely own their funds.

**Complete source note with this vector's mask:**

> ⟦The Next Phase: Total Financial Control⟧
>
> ⟦They’re not just restricting access to money. They’re building a system where you’ll never truly own it again.⟧
>
> Here’s what’s coming next:
>
> Programmable Money – ⟦Your funds will⟧ expire or ⟦be restricted based on government policies.⟧
>
> Social Credit Systems – Your spending could be limited if your behavior doesn’t align with the system.
>
> Forced Digital ID – No transactions without full compliance and tracking.
>
>
> This is no longer a theory. It’s happening right now in different parts of the world.
>
> Bitcoin is the last escape before total financial surveillance.
>
> No expiration dates on your wealth.
>
> No restrictions on where and how you spend.
>
> No authority deciding if you "deserve" access to your own money.
>
>
> They’re not coming for your money. They’re coming for your financial independence.
>
> Will you wait until it’s too late?
>

#### V175 · source N26 · `c36ed58c0f53…`

**Takeaway:** The author predicts that programmable money will allow governments to make funds expire or restrict their use according to government policy.

**Complete source note with this vector's mask:**

> The Next Phase: Total Financial Control
>
> They’re not just restricting access to money. They’re building a system where you’ll never truly own it again.
>
> ⟦Here’s what’s coming next:⟧
>
> ⟦Programmable Money – Your funds will expire or be restricted based on government policies.⟧
>
> Social Credit Systems – Your spending could be limited if your behavior doesn’t align with the system.
>
> Forced Digital ID – No transactions without full compliance and tracking.
>
>
> This is no longer a theory. It’s happening right now in different parts of the world.
>
> Bitcoin is the last escape before total financial surveillance.
>
> No expiration dates on your wealth.
>
> No restrictions on where and how you spend.
>
> No authority deciding if you "deserve" access to your own money.
>
>
> They’re not coming for your money. They’re coming for your financial independence.
>
> Will you wait until it’s too late?
>

#### V192 · source N27 · `f55043b51692…`

**Takeaway:** Society faces a consequential choice between money that enables government surveillance and a people-centered form of money that is free, open, and private.

**Complete source note with this vector's mask:**

> ⟦We're at a crossroads: government surveillance money or free, open, private people's money.⟧ Choose wisely.

#### V193 · source N27 · `f55043b51692…`

**Takeaway:** The author urges people to choose carefully and frames free, open, private money for the people as preferable to surveillance-oriented government money.

**Complete source note with this vector's mask:**

> ⟦We're at a crossroads: government surveillance money or free, open, private people's money. Choose wisely.⟧

### S018

- **Vectors:** `V023 V099 V101`
- **Exists at:** P60 and P70
- **Least-similar member pair:** `V099 ↔ V101` · cosine `0.611745`
- **Other included settings:** At P40 and P50, these vectors are part of S002. At P80, they form S019 (`[V023 V099]`) and the one-vector segment `[V101]`; at P90, S019 also splits into one-vector segments.

#### V023 · source N03 · `974dd5c02c7a…`

**Takeaway:** In the future, solar energy will account for the vast majority of power generation.

**Complete source note with this vector's mask:**

> ⟦Solar power will be the vast majority of power generation in the future⟧

#### V099 · source N04 · `a59ca772c163…`

**Takeaway:** The shared greenhouse is designed to use geothermal and solar energy.

**Complete source note with this vector's mask:**

> Flexicables installed for ⟦our geothermal solar powered greenhouse⟧. The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.
> This will be the first steps to my non consumption based retirement. https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

#### V101 · source N04 · `a59ca772c163…`

**Takeaway:** The author views the greenhouse project as an initial step toward a retirement that is not consumption-based.

**Complete source note with this vector's mask:**

> Flexicables installed for ⟦our geothermal solar powered greenhouse⟧. The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.
> ⟦This will be the first steps to my non consumption based retirement.⟧ https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

### S019

- **Vectors:** `V023 V099`
- **Exists at:** P80
- **Least-similar member pair:** `V023 ↔ V099` · cosine `0.674224`
- **Other included settings:** At P40 and P50, these vectors are part of S002; at P60 and P70, they are part of S018. At P90, they form two one-vector segments: `[V023]` and `[V099]`.

#### V023 · source N03 · `974dd5c02c7a…`

**Takeaway:** In the future, solar energy will account for the vast majority of power generation.

**Complete source note with this vector's mask:**

> ⟦Solar power will be the vast majority of power generation in the future⟧

#### V099 · source N04 · `a59ca772c163…`

**Takeaway:** The shared greenhouse is designed to use geothermal and solar energy.

**Complete source note with this vector's mask:**

> Flexicables installed for ⟦our geothermal solar powered greenhouse⟧. The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.
> This will be the first steps to my non consumption based retirement. https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

### S020

- **Vectors:** `V118 V127`
- **Exists at:** P80 and P90
- **Least-similar member pair:** `V118 ↔ V127` · cosine `0.716208`
- **Other included settings:** At P40 through P70, these vectors are part of S016.

#### V118 · source N22 · `075b407e91d5…`

**Takeaway:** The seemingly obvious advice to remain true to oneself contains profound wisdom that is easy to overlook.

**Complete source note with this vector's mask:**

> ⟦"Just be yourself"⟧ is the best of all the bad advice you ever got. ⟦Wisdom hidden in plain sight.⟧ It took me a lifetime to understand why ⟦this is deep.⟧

#### V127 · source N24 · `4a3184dbd492…`

**Takeaway:** People who feel like outsiders should not fear being themselves or following their own paths, because the world needs their unique perspectives.

**Complete source note with this vector's mask:**

> In a society that values conformity and obedience, the individual who dares to think for themselves is often ostracized and ridiculed. These nonconformists, these outcasts, are the true pioneers of society, the ones who push us to question our assumptions and expand our horizons.
> They are the ones who are not afraid to be different, to be themselves.
> ⟦If you find yourself feeling like an outsider⟧, like you don't fit in with the crowd, that's a good thing. It means that you have the potential to make a real difference in the world. ⟦Don't be afraid to be yourself, to follow your own path. The world needs your unique perspective.⟧ https://image.nostr.build/8a30d246bf5f8ece1abf2a5a6798252c868e7c58a0def48102453d52675533b9.jpg

## Provenance

All segment contents, takeaways, masks, source notes, and cosine values come
from this saved JSON output:

```text
sse_multivector/fine-region-partition-result-v1/analysis.json
```

The saved note, takeaway, and mask inputs and the saved grouping output remain
unchanged.
