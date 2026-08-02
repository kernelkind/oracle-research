# Every Multi-Note Bucket, With Its Evidence

## What this document shows

The experiment turned parts of 50 notes into 194 separate numerical
representations of meaning. It then grouped representations that pointed in
similar directions.

This document shows every bucket produced at P40, P50, or P60 by the grouping
procedure explained below that contains meaning from at least two original
notes. It does not decide whether any bucket is good or bad. It supplies the
complete evidence needed to make that judgment.

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

All numbered fragments listed under one `VXXX` jointly form that piece's
mask. Masks for different pieces from the same note may overlap because each
piece is calculated independently. Every stored fragment selects its first
occurrence in the note; `V063` explicitly calls this out because its fragment
`Molly` appears three times.

## How the pieces were grouped

The grouping procedure starts with all 194 meaning pieces in separate
buckets. It compares the direction of every pair of vectors using cosine
similarity: a higher score means the two represented meanings point in more
similar directions.

For every possible pair of buckets, the procedure looks at the least-similar
pair of meaning pieces that would be brought together. It joins the two
buckets whose least-similar pair has the highest score, provided that score
meets the chosen minimum. It repeats until no remaining join meets the
minimum. The code calls this rule complete linkage.

The same frozen vectors were grouped three times with increasingly strict
minimums:

| Setting | Every pair in one bucket must score at least |
|---|---:|
| P40 | `0.479168` |
| P50 | `0.505010` |
| P60 | `0.538475` |

The three names come from the data. For each of the 194 pieces, the experiment
found its most similar piece from a different note. It sorted those 194 scores.
P40 uses the 40th-percentile score as its minimum, P50 uses the 50th, and P60
uses the 60th. These three adjacent settings were chosen before anyone judged
the meanings, so the review would not depend on one conveniently selected
minimum.

P40, P50, and P60 are not probabilities, confidence scores, or accuracy
measurements. They are three stopping points in the same sequence of bucket
joins. Raising the minimum can only split an earlier bucket; a piece cannot
move into a different P40 case. No setting changes or deletes a meaning piece.

For example, F01 begins at P40 with `V001`, `V102`, `V103`, and `V104` in one
bucket. They remain together at P50. At P60, `V001` stands alone while
`V102`, `V103`, and `V104` remain together. All four pieces still exist.

## What the labels mean

- `VXXX` identifies one meaning piece produced by SSE. Its section shows the
  generated takeaway and selected source words, and links to the original
  note.
- `NXX` identifies one original note within this document. Its complete text
  appears once in the appendix. The hexadecimal text beside `NXX` is the
  beginning of that note's stable ID.
- `FXX` is only a label for one review case in this document. It lets us
  follow the same P40 bucket as the rule becomes stricter without repeating
  all of its evidence. It is not a model output, bucket ID, or description of
  the pieces' subject.

The **least-similar pair still kept together** is the pair with the lowest
cosine score inside a bucket. That score explains what the grouping procedure
did; it does not prove that the meanings belong together.

Use a complete source note only to resolve what its selected words refer to.
Do not import meaning from unselected parts of the note.

Judge every bucket with the same question:

> Could one precise subject description accurately cover every meaning piece
> in this bucket without becoming vague?

Base that decision on each takeaway and its selected source words.

## What is included

Across the three settings, the frozen result contains:

- 17 buckets containing pieces from different original notes at P40;
- 14 at P50;
- 11 at P60;
- 42 bucket appearances when each setting is counted separately;
- 18 different combinations of meaning pieces;
- 52 meaning pieces from 27 original notes.

Following each P40 bucket through the stricter settings produces the 17 cases
below without omitting any bucket. There are 18 combinations but 17 cases
because F02's five-piece P40/P50 bucket becomes a three-piece bucket at P60;
both combinations are shown together in F02. A bucket containing pieces from
only one original note after a split no longer contributes to the 17, 14, or
11 multi-note totals, although its pieces remain listed in the case history.

Only 52 of the 194 pieces, from 27 of the 50 notes, appear below. The others
never entered a multi-note bucket at these three settings.

The pilot also ran an alternative grouping procedure. It is excluded here
because changing the input order changed its buckets, and it was not the
procedure behind the groupings being reviewed in this document.

## Case index

Every cell states where all of that case's pieces are at that setting.

| Case | P40 | P50 | P60 |
|---|---|---|---|
| [F01](#f01) | `V001 V102 V103 V104` together | `V001 V102 V103 V104` together | `V001` alone; `V102 V103 V104` together, all from N02 |
| [F02](#f02) | `V003 V004 V023 V099 V101` together | `V003 V004 V023 V099 V101` together | `V023 V099 V101` together; `V003 V004` together, both from N01 |
| [F03](#f03) | `V005 V116` together | `V005 V116` together | `V005 V116` together |
| [F04](#f04) | `V007 V008 V009 V105 V106 V107` together | `V007 V008 V009 V105 V106 V107` together | `V007 V008 V009 V105 V106 V107` together |
| [F05](#f05) | `V010 V028` together | `V010 V028` together | `V010 V028` together |
| [F06](#f06) | `V013 V152` together | `V013` alone; `V152` alone | `V013` alone; `V152` alone |
| [F07](#f07) | `V029 V030 V031 V050` together | `V029 V030 V031 V050` together | `V029 V030 V031 V050` together |
| [F08](#f08) | `V035 V051 V060` together | `V035 V051 V060` together | `V035 V051 V060` together |
| [F09](#f09) | `V062 V186` together | `V062 V186` together | `V062 V186` together |
| [F10](#f10) | `V063 V170` together | `V063` alone; `V170` alone | `V063` alone; `V170` alone |
| [F11](#f11) | `V076 V095 V096 V097` together | `V076 V095 V096 V097` together | `V076 V095 V096 V097` together |
| [F12](#f12) | `V078 V092` together | `V078` alone; `V092` alone | `V078` alone; `V092` alone |
| [F13](#f13) | `V094 V119` together | `V094 V119` together | `V094 V119` together |
| [F14](#f14) | `V100 V114` together | `V100 V114` together | `V100` alone; `V114` alone |
| [F15](#f15) | `V109 V123` together | `V109 V123` together | `V109 V123` together |
| [F16](#f16) | `V118 V127 V133 V136` together | `V118 V127 V133 V136` together | `V118 V127 V133 V136` together |
| [F17](#f17) | `V174 V175 V192 V193` together | `V174 V175 V192 V193` together | `V174 V175` together, both from N26; `V192 V193` together, both from N27 |

## F01

**What happened as the rule became stricter**

- P40: `V001 V102 V103 V104` were together in one bucket.
- P50: `V001 V102 V103 V104` remained together.
- P60: `V001` stood alone. `V102 V103 V104` remained together, but all three
  came from N02.
- Least-similar pair still kept together at P40 and P50:
  `V001 ↔ V103` · cosine `0.537917`.

### `V001` · [source N01](#n01--7e2e4e93cf8f)

**Takeaway:** The author wants to determine the best way to operate the
Bitcoin miner.

**Mask:**

1. `I want to find the best way how to run the miner.`
2. `#bitcoin`

### `V102` · [source N02](#n02--e09b8c19f52a)

**Takeaway:** The author has just ordered a BitAxe, a device for mining
Bitcoin.

**Mask:**

1. `Just ordered a BitAxe.`
2. `mining`

### `V103` · [source N02](#n02--e09b8c19f52a)

**Takeaway:** The author is very excited to begin mining Bitcoin at home,
something they have been looking forward to doing.

**Mask:**

1. `Just ordered a BitAxe.`
2. `Super excited to finally start mining at home`

### `V104` · [source N02](#n02--e09b8c19f52a)

**Takeaway:** The author expects their home Bitcoin mining to contribute
computing power to the Bitcoin network.

**Mask:**

1. `BitAxe`
2. `start mining at home and contributing to the network`

## F02

**What happened as the rule became stricter**

- P40: `V003 V004 V023 V099 V101` were together in one bucket.
- P50: `V003 V004 V023 V099 V101` remained together.
- P60: `V023 V099 V101` remained together. `V003 V004` formed a separate
  bucket, but both came from N01.
- Least-similar pair still kept together at P40 and P50:
  `V004 ↔ V099` · cosine `0.517907`.
- Least-similar pair still kept together in the P60 bucket containing pieces
  from different notes: `V099 ↔ V101` · cosine `0.611745`.

### `V003` · [source N01](#n01--7e2e4e93cf8f)

**Takeaway:** The author is programming the Bitcoin miner to start when
surplus solar energy is available and to record how much solar energy the
miner uses.

**Mask:**

1. `I do a bit of programming to start up the miner when I have #solar #energy  left. And to have statistics how much solar energy is used for the miner.`
2. `#bitcoin`

### `V004` · [source N01](#n01--7e2e4e93cf8f)

**Takeaway:** During winter, heating the author’s house requires nearly all
the available energy, so little surplus solar energy will remain for the
Bitcoin miner.

**Mask:**

1. `start up the miner when I have #solar #energy  left`
2. `in the winter days almost everything is required to heat the house so it won’t be much`
3. `#miner #bitcoin`

### `V023` · [source N03](#n03--974dd5c02c7a)

**Takeaway:** In the future, solar energy will account for the vast majority
of power generation.

**Mask:**

1. `Solar power will be the vast majority of power generation in the future`

### `V099` · [source N04](#n04--a59ca772c163)

**Takeaway:** The shared greenhouse is designed to use geothermal and solar
energy.

**Mask:**

1. `our geothermal solar powered greenhouse`

### `V101` · [source N04](#n04--a59ca772c163)

**Takeaway:** The author views the greenhouse project as an initial step
toward a retirement that is not consumption-based.

**Mask:**

1. `our geothermal solar powered greenhouse`
2. `This will be the first steps to my non consumption based retirement.`

## F03

**What happened as the rule became stricter**

- P40: `V005 V116` were together in one bucket.
- P50: `V005 V116` remained together.
- P60: `V005 V116` remained together.
- Least-similar pair still kept together: `V005 ↔ V116` · cosine `0.656710`.

### `V005` · [source N05](#n05--f81f01d4d50f)

**Takeaway:** A linked science article discusses research showing that
lightly spraying coffee beans with water before grinding can reduce waste and
produce tastier espresso.

**Mask:**

1. `Why a spritz of water before grinding coffee yields better results`

### `V116` · [source N06](#n06--f15fe96ab816)

**Takeaway:** The author is typing the social-media post while drinking coffee
they consider delicious.

**Mask:**

1. `I’m typing this while drinking my delicious coffee.`

## F04

**What happened as the rule became stricter**

- P40: `V007 V008 V009 V105 V106 V107` were together in one bucket.
- P50: `V007 V008 V009 V105 V106 V107` remained together.
- P60: `V007 V008 V009 V105 V106 V107` remained together.
- Least-similar pair still kept together: `V008 ↔ V107` · cosine `0.682637`.

### `V007` · [source N07](#n07--056e64662570)

**Takeaway:** The author suggests that merely drinking ordinary coffee
differs from experiencing coffee made personally one’s own by roasting the
beans oneself.

**Mask:**

1. `You’ve had coffee. But have you had your coffee?”`
2. `Roasting your own beans means discovering a taste profile that’s uniquely yours.`

### `V008` · [source N07](#n07--056e64662570)

**Takeaway:** Roasting one’s own coffee beans enables a person to discover a
flavor profile unique to their tastes.

**Mask:**

1. `Roasting your own beans means discovering a taste profile that’s uniquely yours.`

### `V009` · [source N07](#n07--056e64662570)

**Takeaway:** The author views self-roasting and discovering a personal coffee
profile as an individual journey that pre-roasted coffee cannot reproduce.

**Mask:**

1. `Roasting your own beans means discovering a taste profile that’s uniquely yours. It’s a personal journey that no bag of pre-roasted coffee can replicate.`

### `V105` · [source N08](#n08--2dc50a304a2f)

**Takeaway:** The author believes decaffeinated-coffee drinkers are the most
genuine coffee enthusiasts because they drink coffee for its flavor and
overall experience rather than for caffeine.

**Mask:**

1. `Decafe coffee drinkers are the purist coffee enthusiasts of them all as they do it for the experience and flavour.`

### `V106` · [source N08](#n08--2dc50a304a2f)

**Takeaway:** The author disparagingly contrasts decaffeinated-coffee
enthusiasts with caffeine-addicted coffee drinkers, whom the author portrays
as less pure in their appreciation of coffee.

**Mask:**

1. `Decafe coffee drinkers are the purist coffee enthusiasts of them all as they do it for the experience and flavour.`
2. `Unlike the caffeine addicted heathens.`

### `V107` · [source N08](#n08--2dc50a304a2f)

**Takeaway:** The author challenges others to change this opinion about
decaffeinated-coffee drinkers.

**Mask:**

1. `Decafe coffee drinkers are the purist coffee enthusiasts of them all as they do it for the experience and flavour. Unlike the caffeine addicted heathens.`
2. `Change my mind.`

## F05

**What happened as the rule became stricter**

- P40: `V010 V028` were together in one bucket.
- P50: `V010 V028` remained together.
- P60: `V010 V028` remained together.
- Least-similar pair still kept together: `V010 ↔ V028` · cosine `0.759397`.

### `V010` · [source N07](#n07--056e64662570)

**Takeaway:** The author says they are sipping coffee and frames the post as a
provocative opinion in a coffee-focused social-media discussion.

**Mask:**

1. `Sipping`
2. `#coffeechain`
3. `#HotTake`

### `V028` · [source N09](#n09--f4c5aa5f1802)

**Takeaway:** The author presented the post as part of a social-media coffee
chain.

**Mask:**

1. `#coffeechain`

## F06

**What happened as the rule became stricter**

- P40: `V013 V152` were together in one bucket.
- P50: `V013` stood alone and `V152` stood alone.
- P60: `V013` stood alone and `V152` stood alone.
- Least-similar pair still kept together at P40:
  `V013 ↔ V152` · cosine `0.501598`.

### `V013` · [source N10](#n10--74694da41f36)

**Takeaway:** The author needs to retrieve wire from a personal trailer
located at one of the author’s job sites.

**Mask:**

1. `Have to grab some wire out of my trailer on one of the jobs.`

### `V152` · [source N11](#n11--e79637da76e4)

**Takeaway:** The author needs to replace a fuel-tank grommet on a post-hole
digger they share or own with others.

**Mask:**

1. `We need to replace a grommet on the fuel tank of our post hole digger.`

## F07

**What happened as the rule became stricter**

- P40: `V029 V030 V031 V050` were together in one bucket.
- P50: `V029 V030 V031 V050` remained together.
- P60: `V029 V030 V031 V050` remained together.
- Least-similar pair still kept together: `V030 ↔ V050` · cosine `0.664877`.

### `V029` · [source N12](#n12--7adcfe1ab26f)

**Takeaway:** The author believes that the forces behind pervasive
proprietary-technology surveillance seek total control.

**Mask:**

1. `they want to control everything`
2. `a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.)`
3. `all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices`
4. `this tech surveillance state`

### `V030` · [source N12](#n12--7adcfe1ab26f)

**Takeaway:** The author warns that treating a Nostr nsec private key as
secure on an operating system they regard as proprietary—such as Windows,
macOS, iOS, or Android—ignores broader surveillance and device-access risks.

**Mask:**

1. `if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture`
2. `all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices`

### `V031` · [source N12](#n12--7adcfe1ab26f)

**Takeaway:** The author claims that Windows, macOS, iOS, Android, and similar
operating systems are saturated with telemetry mechanisms and APIs capable of
accessing everything on a user's device.

**Mask:**

1. `#Windows, #macOS, #iOS, #Android, etc.`
2. `all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices`

### `V050` · [source N13](#n13--735104aa3dfc)

**Takeaway:** Pypush can now send and receive messages through Apple’s
iMessage service on any platform.

**Mask:**

1. `#pypush can now send and receive #iMessage, on any platform`

## F08

**What happened as the rule became stricter**

- P40: `V035 V051 V060` were together in one bucket.
- P50: `V035 V051 V060` remained together.
- P60: `V035 V051 V060` remained together.
- Least-similar pair still kept together: `V035 ↔ V060` · cosine `0.717748`.

### `V035` · [source N12](#n12--7adcfe1ab26f)

**Takeaway:** The author believes free and open-source software is the only
way to retain any degree of technological sovereignty within what they view
as a technology-surveillance state.

**Mask:**

1. `free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty`

### `V051` · [source N13](#n13--735104aa3dfc)

**Takeaway:** Pypush is entirely serverless and open-source.

**Mask:**

1. `#pypush`
2. `completely server-less and open-source`

### `V060` · [source N14](#n14--bbe63b10f768)

**Takeaway:** The author is nearing the point where their entire software
stack consists of free and open-source software.

**Mask:**

1. `Getting close to 100% of my software stack being free and open source.`

## F09

**What happened as the rule became stricter**

- P40: `V062 V186` were together in one bucket.
- P50: `V062 V186` remained together.
- P60: `V062 V186` remained together.
- Least-similar pair still kept together: `V062 ↔ V186` · cosine `0.569165`.

### `V062` · [source N15](#n15--aa269973db71)

**Takeaway:** Molly is a fork of the Signal messaging app designed to offer
additional security.

**Mask:**

1. `Molly is a fork of Signal, made to be more secure.`

### `V186` · [source N16](#n16--d94ef8a432ec)

**Takeaway:** Larry Ellison has said that real-time surveillance is beneficial
because it keeps people’s behavior in check.

**Mask:**

1. `Larry Ellison`
2. `said real-time surveillance is good for keeping us in check`

## F10

**What happened as the rule became stricter**

- P40: `V063 V170` were together in one bucket.
- P50: `V063` stood alone and `V170` stood alone.
- P60: `V063` stood alone and `V170` stood alone.
- Least-similar pair still kept together at P40:
  `V063 ↔ V170` · cosine `0.498993`.

### `V063` · [source N15](#n15--aa269973db71)

**Takeaway:** Molly contains no proprietary code or binary blobs.

**Mask:**

1. `Molly` — first occurrence of three
2. `No proprietary blobs/code.`

### `V170` · [source N17](#n17--53b0f8fe4650)

**Takeaway:** The author says the message is not an attempt to force anyone to
use the author's preferred communication protocol.

**Mask:**

1. `Here's my core message:`
2. `This isn't about me trying to force you to use my favorite protocol.`

## F11

**What happened as the rule became stricter**

- P40: `V076 V095 V096 V097` were together in one bucket.
- P50: `V076 V095 V096 V097` remained together.
- P60: `V076 V095 V096 V097` remained together.
- Least-similar pair still kept together: `V076 ↔ V096` · cosine `0.610311`.

### `V076` · [source N18](#n18--84aba98daa2c)

**Takeaway:** Cleaning the stock BitAxe fan quiets it for only a day or two
before it becomes extremely loud again.

**Mask:**

1. `the fan on their BitAxe`
2. `The stock fan`
3. `I clean it and within a day or two, it's right back to being loud as hell.`

### `V095` · [source N19](#n19--dcd6544eba8e)

**Takeaway:** The author’s Avalon Nano 3 cryptocurrency miner has become
noticeably louder after nearly a year of use despite being kept clean.

**Mask:**

1. `After nearly a year of mining with the #AvalonNano3, it’s noticeably getting louder over time-even though I keep it clean.`

### `V096` · [source N19](#n19--dcd6544eba8e)

**Takeaway:** The author’s four Bitaxe cryptocurrency miners have maintained
consistent noise levels over roughly the same period in which the Avalon Nano
3 became louder.

**Mask:**

1. `After nearly a year of mining with the #AvalonNano3, it’s noticeably getting louder over time`
2. `In comparison, I’ve had the 4 #Bitaxe for about the same period, and its noise level has remained consistent.`

### `V097` · [source N19](#n19--dcd6544eba8e)

**Takeaway:** Based on this contrast, the author predicts that the Avalon Nano
3 will fail much sooner than the Bitaxe miners.

**Mask:**

1. `After nearly a year of mining with the #AvalonNano3, it’s noticeably getting louder over time-even though I keep it clean.`
2. `In comparison, I’ve had the 4 #Bitaxe for about the same period, and its noise level has remained consistent.`
3. `My prediction is that Avalons gonna die much more faster than Bitaxe`

## F12

**What happened as the rule became stricter**

- P40: `V078 V092` were together in one bucket.
- P50: `V078` stood alone and `V092` stood alone.
- P60: `V078` stood alone and `V092` stood alone.
- Least-similar pair still kept together at P40:
  `V078 ↔ V092` · cosine `0.482704`.

### `V078` · [source N20](#n20--4166411750a2)

**Takeaway:** The author directs the book-choice question to Nostr users,
including its book-focused and “plebchain” communities.

**Mask:**

1. `Trying to decide what book I should read next 🤔 What one would you read?`
2. `#asknostr #bookstr #plebchain`

### `V092` · [source N21](#n21--38c864c05535)

**Takeaway:** Based on what they have read so far, the author considers
Elizondo’s book “Imminent” authentic, well written, and gripping.

**Mask:**

1. `Elizondo’s Imminent is an authentic, well-written page turner so far as I’ve read.`

## F13

**What happened as the rule became stricter**

- P40: `V094 V119` were together in one bucket.
- P50: `V094 V119` remained together.
- P60: `V094 V119` remained together.
- Least-similar pair still kept together: `V094 ↔ V119` · cosine `0.538615`.

### `V094` · [source N21](#n21--38c864c05535)

**Takeaway:** Reading “Imminent” is prompting the author to mentally connect
and reorganize many ideas related to unidentified anomalous phenomena.

**Mask:**

1. `Elizondo’s Imminent`
2. `so far as I’ve read`
3. `Lots of puzzle pieces shifting into place in the back of my mind`
4. `#uap`

### `V119` · [source N22](#n22--075b407e91d5)

**Takeaway:** The author says it took them a lifetime to understand why
remaining true to oneself is profound advice.

**Mask:**

1. `"Just be yourself"`
2. `advice`
3. `It took me a lifetime to understand why this is deep.`

## F14

**What happened as the rule became stricter**

- P40: `V100 V114` were together in one bucket.
- P50: `V100 V114` remained together.
- P60: `V100` stood alone and `V114` stood alone.
- Least-similar pair still kept together at P40 and P50:
  `V100 ↔ V114` · cosine `0.507426`.

### `V100` · [source N04](#n04--a59ca772c163)

**Takeaway:** An existing greenhouse in Alliance, Nebraska, grows pineapples,
dates, and citrus fruit.

**Mask:**

1. `The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.`

### `V114` · [source N23](#n23--2c054d399715)

**Takeaway:** The author says that sunshine, a cool breeze, doves, wrens,
robins, squirrels, shade from an oak tree, and a blooming crossvine together
make for a good Saturday.

**Mask:**

1. `Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree and a crossvine in bloom. This is the recipe for a good Saturday.`

## F15

**What happened as the rule became stricter**

- P40: `V109 V123` were together in one bucket.
- P50: `V109 V123` remained together.
- P60: `V109 V123` remained together.
- Least-similar pair still kept together: `V109 ↔ V123` · cosine `0.656426`.

### `V109` · [source N23](#n23--2c054d399715)

**Takeaway:** A person should not assume that everyone who publicly expresses
agreement with them privately holds the same view.

**Mask:**

1. `Don't assume that everyone who agrees with you in public agrees with you in private.`

### `V123` · [source N24](#n24--4a3184dbd492)

**Takeaway:** In societies that value conformity and obedience, people who
dare to think independently are often excluded and mocked.

**Mask:**

1. `In a society that values conformity and obedience, the individual who dares to think for themselves is often ostracized and ridiculed.`

## F16

**What happened as the rule became stricter**

- P40: `V118 V127 V133 V136` were together in one bucket.
- P50: `V118 V127 V133 V136` remained together.
- P60: `V118 V127 V133 V136` remained together.
- Least-similar pair still kept together: `V118 ↔ V133` · cosine `0.577648`.

### `V118` · [source N22](#n22--075b407e91d5)

**Takeaway:** The seemingly obvious advice to remain true to oneself contains
profound wisdom that is easy to overlook.

**Mask:**

1. `"Just be yourself"`
2. `Wisdom hidden in plain sight.`
3. `this is deep.`

### `V127` · [source N24](#n24--4a3184dbd492)

**Takeaway:** People who feel like outsiders should not fear being themselves
or following their own paths, because the world needs their unique
perspectives.

**Mask:**

1. `If you find yourself feeling like an outsider`
2. `Don't be afraid to be yourself, to follow your own path. The world needs your unique perspective.`

### `V133` · [source N25](#n25--adb5912a5214)

**Takeaway:** Integrity, authenticity, and an inner moral compass can guide a
person through challenges and confrontations while helping them remain firm
in their convictions and true to themselves.

**Mask:**

1. `Your integrity, authenticity, and inner compass will guide you through any challenge or confrontation, ensuring that you remain steadfast in your convictions and true to yourself.`

### `V136` · [source N25](#n25--adb5912a5214)

**Takeaway:** By remaining true to oneself, a person can trust that other
aspects of life will fall into place.

**Mask:**

1. `Stay true to yourself, and the rest will fall into place.`

## F17

**What happened as the rule became stricter**

- P40: `V174 V175 V192 V193` were together in one bucket.
- P50: `V174 V175 V192 V193` remained together.
- P60: `V174 V175` formed one bucket, but both came from N26. `V192 V193`
  formed another bucket, but both came from N27.
- Least-similar pair still kept together at P40 and P50:
  `V175 ↔ V193` · cosine `0.518401`.

### `V174` · [source N26](#n26--c36ed58c0f53)

**Takeaway:** The author claims that governments or comparable financial
authorities are moving beyond restricting access to money toward total
financial control, under which individuals will no longer genuinely own their
funds.

**Mask:**

1. `The Next Phase: Total Financial Control`
2. `They’re not just restricting access to money. They’re building a system where you’ll never truly own it again.`
3. `Your funds will`
4. `be restricted based on government policies.`

### `V175` · [source N26](#n26--c36ed58c0f53)

**Takeaway:** The author predicts that programmable money will allow
governments to make funds expire or restrict their use according to government
policy.

**Mask:**

1. `Here’s what’s coming next:`
2. `Programmable Money – Your funds will expire or be restricted based on government policies.`

### `V192` · [source N27](#n27--f55043b51692)

**Takeaway:** Society faces a consequential choice between money that enables
government surveillance and a people-centered form of money that is free,
open, and private.

**Mask:**

1. `We're at a crossroads: government surveillance money or free, open, private people's money.`

### `V193` · [source N27](#n27--f55043b51692)

**Takeaway:** The author urges people to choose carefully and frames free,
open, private money for the people as preferable to surveillance-oriented
government money.

**Mask:**

1. `We're at a crossroads: government surveillance money or free, open, private people's money. Choose wisely.`

## Source-note appendix

The substantive text below is copied from the frozen artifact. Trailing spaces
and excess blank lines are normalized. Each source is shown once so the mask
fragments above can be evaluated in complete context without repeating long
notes inside every case.

### N01 · `7e2e4e93cf8f…`

Used by F01 and F02.

```text
This week I just let the miner running to keep temperatures for a minimum and save the #statistics.
I want to find the best way how to run the miner. So far it only starts when it is below a specific temperature (with a day/night mode)

Meanwhile I do a bit of programming to start up the miner when I have #solar #energy  left. And to have statistics how much solar energy is used for the miner.

Anyhow in the winter days almost everything is required to heat the house so it won’t be much anyhow.

#orangery #greenhouse   #grownostr #miner #bitcoin #nostr #btc
```

### N02 · `e09b8c19f52a…`

Used by F01.

```text
Just ordered a BitAxe. Super excited to finally start mining at home and contributing to the network.
```

### N03 · `974dd5c02c7a…`

Used by F02.

```text
Solar power will be the vast majority of power generation in the future
```

### N04 · `a59ca772c163…`

Used by F02 and F14.

```text
Flexicables installed for our geothermal solar powered greenhouse. The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.
This will be the first steps to my non consumption based retirement. https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg
```

### N05 · `f81f01d4d50f…`

Used by F03.

```text
Why a spritz of water before grinding coffee yields better results

Comments ( https://news.ycombinator.com/item?id=38554310 )

https://arstechnica.com/science/2023/12/study-why-a-spritz-of-water-before-grinding-coffee-yields-less-waste-tastier-espresso/
```

### N06 · `f15fe96ab816…`

Used by F03.

```text
I was about to say good morning but I’m not, instead I’m typing this while drinking my delicious coffee.
```

### N07 · `056e64662570…`

Used by F04 and F05.

```text
You’ve had coffee. But have you had your coffee?”
https://blossom.primal.net/1379b90996b8ecb2f4fdef6756fd61c4ab964fa19f9e1505950e10a4d97640dd.jpg
Roasting your own beans means discovering a taste profile that’s uniquely yours. It’s a personal journey that no bag of pre-roasted coffee can replicate.

Sipping  @ #coffeechain

#HotTake ☕
```

### N08 · `2dc50a304a2f…`

Used by F04.

```text
Decafe coffee drinkers are the purist coffee enthusiasts of them all as they do it for the experience and flavour. Unlike the caffeine addicted heathens. Change my mind.
```

### N09 · `f4c5aa5f1802…`

Used by F05.

```text
Made my coffee with raw cream and a raw egg yolk today #coffeechain
```

### N10 · `74694da41f36…`

Used by F06.

```text
#proofofwork

Got 14 460w solar panels series and ready to connect. Have to grab some wire out of my trailer on one of the jobs. This weekend project. might be able to charge a car or run a Bitcoin miner off this successfully. I still have six extra panels back there and four that are working up top on the roof.

https://m.primal.net/Mkft.jpg
```

### N11 · `e79637da76e4…`

Used by F06.

```text
We need to replace a grommet on the fuel tank of our post hole digger.
Searching Amazon and eBay the part I need to buy is $11 OR you can get a 70 piece spares kit for $7.
Why is it like this? This is why minimalism is an active choice.
```

### N12 · `7adcfe1ab26f…`

Used by F07 and F08.

```text
they want to control everything..
..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty
```

### N13 · `735104aa3dfc…`

Used by F07 and F08.

```text
It's ready! #pypush can now send and receive #iMessage, on any platform, completely server-less and open-source! 🎉

https://github.com/JJTech0130/pypush
```

### N14 · `bbe63b10f768…`

Used by F08.

```text
Getting close to 100% of my software stack being free and open source.
```

### N15 · `aa269973db71…`

Used by F09 and F10.

```text
I'm thinking I'll regularly post about open source tech I find useful.

Molly is a fork of Signal, made to be more secure.

Some of it's features include:
No proprietary blobs/code.
Molly protects your messages with passphrase encryption.
The app can lock down automatically after a set time of not being opened.
Molly, "Securely shreds sensitive data from RAM."
You can create automatic backups
It even supports setting an app proxy through Tor via Orbot.

Available on their own Fdroid repo:
https://molly.im/
```

### N16 · `d94ef8a432ec…`

Used by F09.

```text
Larry Ellison wants to put all US data in one big AI system - From the billionaire who said real-time surveillance is good for keeping us in check
https://www.theregister.com/2025/02/12/larry_ellison_wants_all_data/
```

### N17 · `53b0f8fe4650…`

Used by F10.

```text
Despite it being easier to self-host XMPP and less expensive on resources, Matrix is more popular.  Why?

The real reason Matrix is popular is because corporate and FOSS developers like the encrypted group chats for their internal use.  (XMPP is NOT encrypted group chats).  So then devs host a Matrix room to answer end-user questions, and having all these rooms encourages overall adoption.

The part that's not usually mentioned, is that only the devs usually use self-hosted Matrix servers, and the vast majority of the public uses Matrix.org which is on Cloudflare with Gmail verification.

In theory Matrix is decentralized, but in the real world, everyone gets Cloudflare metadata surveillance, and uses the same Element client.

Here's my core message:
Try to be Self-Sovereign with what you're doing.
If you're hosting a website, 1 core VPS for email, whatever.  Then host your own XMPP/Matrix.  XMPP uses so little resources, it's near free.

If a VPS is really not for you, even if you pay someone like me $100 to set it up:
https://simplifiedprivacy.com/email-cloud-combo/index.html

Then public SimpleX/Session servers are right for you.  That's fine.  This isn't about me trying to force you to use my favorite protocol.  It's about you not using Cloudflare (and Protonmail seeing your metadata) and thinking you're "doing privacy".
```

### N18 · `84aba98daa2c…`

Used by F11.

```text
Has anyone replaced the fan on their BitAxe? If so, what did you use? I'd normally go with a Noctua but I hate that the NF-A4x20 is the stupid beige/brown colorway.

The stock fan is just getting too loud to deal with. I clean it and within a day or two, it's right back to being loud as hell.
```

### N19 · `dcd6544eba8e…`

Used by F11.

```text
After nearly a year of mining with the #AvalonNano3, it’s noticeably getting louder over time-even though I keep it clean. The difference is clear! In comparison, I’ve had the 4 #Bitaxe for about the same period, and its noise level has remained consistent. My prediction is that Avalons gonna die much more faster than Bitaxe ⏳
```

### N20 · `4166411750a2…`

Used by F12.

```text
Trying to decide what book I should read next 🤔 What one would you read?

The Mandibles
The Mobile Wave
The Fourth revolution
Fiat Food
The Principles of Economics
Broken Money
Bitcoin is Venice

#asknostr #bookstr #plebchain
```

### N21 · `38c864c05535…`

Used by F12 and F13.

```text
Elizondo’s Imminent is an authentic, well-written page turner so far as I’ve read. If I didn’t have to work tomorrow I’d finish the whole dang thing tonight. Lots of puzzle pieces shifting into place in the back of my mind 🛸

#uap
#plebchain
```

### N22 · `075b407e91d5…`

Used by F13 and F16.

```text
"Just be yourself" is the best of all the bad advice you ever got. Wisdom hidden in plain sight. It took me a lifetime to understand why this is deep.
```

### N23 · `2c054d399715…`

Used by F14 and F15.

```text
Annie's Saturday Morning Thoughts

Don't assume that everyone who agrees with you in public agrees with you in private. 😏

The wren on the fence has been chirping for a while. Must have good lungs.

Only the things you choose without pressure define you. The rest is a facade. 🤥

Flavored coffee is nice but can get old if you have it every day.

Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree and a crossvine in bloom. This is the recipe for a good Saturday. 🤗
```

### N24 · `4a3184dbd492…`

Used by F15 and F16.

```text
In a society that values conformity and obedience, the individual who dares to think for themselves is often ostracized and ridiculed. These nonconformists, these outcasts, are the true pioneers of society, the ones who push us to question our assumptions and expand our horizons.
They are the ones who are not afraid to be different, to be themselves.
If you find yourself feeling like an outsider, like you don't fit in with the crowd, that's a good thing. It means that you have the potential to make a real difference in the world. Don't be afraid to be yourself, to follow your own path. The world needs your unique perspective. https://image.nostr.build/8a30d246bf5f8ece1abf2a5a6798252c868e7c58a0def48102453d52675533b9.jpg
```

### N25 · `adb5912a5214…`

Used by F16.

```text
In a world where titles and positions often dictate power dynamics, it's easy to feel overshadowed or intimidated by those in authority. But here's a simple truth: if your daily actions and intentions stem from an ethical and moral foundation, you need not worry or be bothered by anyone else, regardless of their temporary title or status. Your integrity, authenticity, and inner compass will guide you through any challenge or confrontation, ensuring that you remain steadfast in your convictions and true to yourself. So, trust in the strength of your character and the righteousness of your deeds, and let go of the need for external validation or approval. When you walk with integrity, you walk with unwavering confidence and peace of mind, unshaken by the winds of authority or influence. Stay true to yourself, and the rest will fall into place.
```

### N26 · `c36ed58c0f53…`

Used by F17.

```text
The Next Phase: Total Financial Control

They’re not just restricting access to money. They’re building a system where you’ll never truly own it again.

Here’s what’s coming next:

Programmable Money – Your funds will expire or be restricted based on government policies.

Social Credit Systems – Your spending could be limited if your behavior doesn’t align with the system.

Forced Digital ID – No transactions without full compliance and tracking.

This is no longer a theory. It’s happening right now in different parts of the world.

Bitcoin is the last escape before total financial surveillance.

No expiration dates on your wealth.

No restrictions on where and how you spend.

No authority deciding if you "deserve" access to your own money.

They’re not coming for your money. They’re coming for your financial independence.

Will you wait until it’s too late?
```

### N27 · `f55043b51692…`

Used by F17.

```text
We're at a crossroads: government surveillance money or free, open, private people's money. Choose wisely.
```

## Provenance

All bucket contents, takeaways, masks, source notes, and cosine values come
from this saved JSON output:

```text
sse_multivector/fine-region-partition-result-v1/analysis.json
```

The saved note, takeaway, and mask inputs and the saved grouping output remain
unchanged.
