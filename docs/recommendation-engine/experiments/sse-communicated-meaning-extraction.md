# TEv4.1 — Did clearer masks produce better semantic vectors?

## Result

No—not reliably.

TEv4.1 tested whether making a mask self-contained would make SSE represent the
intended takeaway more cleanly. In the surveillance and retirement cases below,
the added fragments made previously unresolved references understandable to a
person. But that source text also changed the vectors' meaning.

The three concrete failures are documented below with their complete source
notes, generated takeaways, masks, measured neighbors, and interpretation.

## What the experiment changed

The pipeline is:

1. TPv3.81 reads one complete note and generates takeaways.
2. A fresh MPv3.3 call receives one takeaway and the complete note. It selects
   exact source fragments as the mask.
3. SSE encodes the complete note, takes the contextual token representations
   selected by the mask, and pools them into one vector.

The takeaway text itself is not passed to SSE. It only guides mask selection.
Within the same fixed SSE configuration, identical source text and identical
masks produce identical vectors even if the takeaways are worded differently.

TEv3.1 and TEv4.1 used the same ordered 50 notes, SSE checkpoint,
Sentence-T5 base model, worker, 768 dimensions, and inference batch size.
TEv3.1 used the previous takeaways and masks. TEv4.1 regenerated all of them
with TPv3.81 and MPv3.3.

A higher cosine means two vectors point in more nearly the same direction.
Rank is the vector's position among vectors from other notes.

TEv3.1 has 131 vectors and TEv4.1 has 194. Therefore, a rank change by itself
is not a controlled comparison: the number and identity of competing vectors
also changed. The cases below use raw cosines and byte-identical candidate
vectors wherever possible.

## Failure #3 — Clarifying surveillance shifted the vector toward software

### Complete source note

> they want to control everything..
> ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows,
> #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all
> those OS's are saturated with telemetry mechanisms and APIs that have access
> to everything on your devices.. ..i'm still on iOS phone-wise, but my days are
> numbered with that.. ..likely moving to #GrapheneOS (although i already try to
> use my phone as little as possible).. ..i've already switched to #Linux
> computer-wise.. ..free and opensource is the only way to navigate this tech
> surveillance state with any level of sovereignty

### Everything TEv3.1 generated from this note

1. **Takeaway:** Unspecified actors want to control everything.

   **Mask:** `they want to control everything`
2. **Takeaway:** The author believes Nostr nsec keys are unsafe on proprietary
   operating systems because their telemetry and APIs can access everything on
   a device.

   **Mask:** `if you think your #Nostr nsec key is safe on a proprietary OS (
   #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger
   picture` + `all those OS's are saturated with telemetry mechanisms and APIs
   that have access to everything on your devices`
3. **Takeaway:** The author plans to leave iOS, likely for GrapheneOS, and
   already minimizes phone use.

   **Mask:** `i'm still on iOS phone-wise, but my days are numbered with that` +
   `likely moving to #GrapheneOS (although i already try to use my phone as
   little as possible)`
4. **Takeaway:** The author has already switched to Linux on computers.

   **Mask:** `i've already switched to #Linux computer-wise`
5. **Takeaway:** The author considers free and open-source software the only way
   to retain sovereignty in a technology surveillance state.

   **Mask:** `free and opensource is the only way to navigate this tech
   surveillance state with any level of sovereignty`

### Everything TEv4.1 generated from this note

1. **Takeaway:** The author believes that the forces behind pervasive
   proprietary-technology surveillance seek total control.

   **Mask:** `they want to control everything` + `a proprietary OS ( #Windows,
   #macOS, #iOS, #Android, etc.)` + `all those OS's are saturated with telemetry
   mechanisms and APIs that have access to everything on your devices` + `this
   tech surveillance state`
2. **Takeaway:** The author warns that treating a Nostr nsec private key as
   secure on an operating system they regard as proprietary—such as Windows,
   macOS, iOS, or Android—ignores broader surveillance and device-access risks.

   **Mask:** `if you think your #Nostr nsec key is safe on a proprietary OS (
   #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger
   picture` + `all those OS's are saturated with telemetry mechanisms and APIs
   that have access to everything on your devices`
3. **Takeaway:** The author claims that Windows, macOS, iOS, Android, and
   similar operating systems are saturated with telemetry mechanisms and APIs
   capable of accessing everything on a user's device.

   **Mask:** `#Windows, #macOS, #iOS, #Android, etc.` + `all those OS's are
   saturated with telemetry mechanisms and APIs that have access to everything
   on your devices`
4. **Takeaway:** The author still uses iOS on their phone but expects to stop
   soon.

   **Mask:** `i'm still on iOS phone-wise, but my days are numbered with that`
5. **Takeaway:** The author will likely replace iOS with GrapheneOS, despite
   already trying to use their phone as little as possible.

   **Mask:** `i'm still on iOS phone-wise, but my days are numbered with that..
   ..likely moving to #GrapheneOS (although i already try to use my phone as
   little as possible)`
6. **Takeaway:** The author has already switched their computer operating
   system to Linux.

   **Mask:** `i've already switched to #Linux computer-wise`
7. **Takeaway:** The author believes free and open-source software is the only
   way to retain any degree of technological sovereignty within what they view
   as a technology-surveillance state.

   **Mask:** `free and opensource is the only way to navigate this tech
   surveillance state with any level of sovereignty`

### The vector being tested

TEv3.1 represented the control claim using only:

> they want to control everything

TEv4.1 tried to resolve who `they` meant by also selecting the proprietary-OS,
telemetry, and technology-surveillance-state fragments. The old and new target
vectors have cosine `0.5209`, so this changed the vector substantially.

### Controlled neighbor 1 — direct government control moved away

**Complete candidate note**

> NEW - The CCC warns that the German left-green-liberal government wants to
> "effectively end anonymity" and make all citizens "identifiable at all times
> and in all places," including by opening doors to Palantir and other
> surveillance software.
>
> https://www.ccc.de/en/updates/2024/biometrischer-uberwachungsexzess-der-bundesregierung
>
> https://hell.twtr.plus/media/cf6857f1982ee096057b3c09692a162778dd08f6e86e47e845309425238d567a.file

The relevant candidate vector selected the same source text in both runs:

> The CCC warns that the German left-green-liberal government wants to
> "effectively end anonymity" and make all citizens "identifiable at all times
> and in all places,"

Its generated takeaway changed wording, but its source mask and vector were
byte-identical:

- TEv3.1: `The CCC warns that Germany’s left-green-liberal government seeks to
  effectively eliminate anonymity and make citizens identifiable everywhere.`
- TEv4.1: `The Chaos Computer Club warns that Germany’s left-green-liberal
  governing coalition wants to effectively eliminate anonymity by making every
  citizen identifiable at all times and in all places.`

Cosine to the control target fell from `0.5067` to `0.3327`. Because the
candidate vector did not change, the changed target caused the decrease.

### Controlled neighbor 2 — generic free software moved closer

**Complete candidate note**

> Getting close to 100% of my software stack being free and open source.

Both runs selected the entire note. The vector was byte-identical.

- TEv3.1 takeaway: `The user is close to making their entire software stack
  free and open source.`
- TEv4.1 takeaway: `The author is nearing the point where their entire software
  stack consists of free and open-source software.`
- Mask in both runs: `Getting close to 100% of my software stack being free and
  open source.`

Cosine to the control target rose from `0.3763` to `0.4650`. Because the
candidate did not change, the added software and operating-system text in the
new target caused the increase.

### New rank-1 neighbor — cross-platform iMessage

**Complete candidate note**

> It's ready! #pypush can now send and receive #iMessage, on any platform,
> completely server-less and open-source! 🎉
>
> https://github.com/JJTech0130/pypush

TEv3.1 generated one vector:

- **Takeaway:** pypush can now send and receive iMessages on any platform as a
  serverless, open-source project.
- **Mask:** `#pypush can now send and receive #iMessage, on any platform,
  completely server-less and open-source!`

TEv4.1 generated four vectors:

1. **Takeaway:** The author announces that the pypush project is ready.
   **Mask:** `It's ready! #pypush`
2. **Takeaway:** Pypush can now send and receive messages through Apple’s
   iMessage service on any platform.
   **Mask:** `#pypush can now send and receive #iMessage, on any platform`
3. **Takeaway:** Pypush is entirely serverless and open-source.
   **Mask:** `#pypush` + `completely server-less and open-source`
4. **Takeaway:** The author provides a link to the pypush project’s GitHub
   repository.
   **Mask:** `pypush`

The TEv4.1 platform-only vector became the new target's rank-1 cross-note
neighbor at `0.6889`. Comparing every old/new combination shows where the
increase came from:

| Control target | iMessage candidate | Cosine |
|---|---|---:|
| TEv3.1 | TEv3.1 combined vector | `0.4005` |
| TEv3.1 | TEv4.1 platform-only vector | `0.2810` |
| TEv4.1 | TEv3.1 combined vector | `0.6599` |
| TEv4.1 | TEv4.1 platform-only vector | `0.6889` |

Even with the old iMessage vector held fixed, changing only the target raised
the cosine from `0.4005` to `0.6599`. The target's added operating-system and
platform context caused most of the increase.

### Automatic-backup observation — not a controlled comparison

The old control target's second-nearest cross-note result was this takeaway:

> Molly supports automatic backups.

It came from this complete note:

> I'm thinking I'll regularly post about open source tech I find useful.
>
> Molly is a fork of Signal, made to be more secure.
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

- TEv3.1 mask: `You can create automatic backups`
- TEv4.1 mask: `Molly` + `can create automatic backups`

It moved from rank 2 at `0.4175` to rank 43 at `0.1723`. This looks better, but
both the target and candidate masks changed, so this pair cannot show which
change caused the improvement.

### What failed

The clearer target did not become a cleaner representation of systemic control
and surveillance. Direct government-control content moved away. Generic
free-software and cross-platform application content moved closer. The original
automatic-backup mismatch fell to rank 43, but the failure changed form rather
than disappearing.

## Failure #6 — Clarifying retirement shifted the vector toward solar energy

### Complete source note

> Flexicables installed for our geothermal solar powered greenhouse. The
> greenhouse they have in Aliance Nebraska grows pineapple and dates and
> citrus.
> This will be the first steps to my non consumption based retirement.
> https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

### Everything TEv3.1 generated from this note

1. **Takeaway:** Flexicables have been installed for the author's geothermal,
   solar-powered greenhouse.

   **Mask:** `Flexicables installed for our geothermal solar powered
   greenhouse.`
2. **Takeaway:** A greenhouse in Aliance, Nebraska grows pineapples, dates, and
   citrus.

   **Mask:** `The greenhouse they have in Aliance Nebraska grows pineapple and
   dates and citrus.`
3. **Takeaway:** The greenhouse project is the author's first step toward a
   non-consumption-based retirement.

   **Mask:** `This will be the first steps to my non consumption based
   retirement.`

### Everything TEv4.1 generated from this note

1. **Takeaway:** Flexible cables have been installed as part of a greenhouse
   project shared by the author and others.

   **Mask:** `Flexicables installed for our ` + `greenhouse.`
2. **Takeaway:** The shared greenhouse is designed to use geothermal and solar
   energy.

   **Mask:** `our geothermal solar powered greenhouse`
3. **Takeaway:** An existing greenhouse in Alliance, Nebraska, grows
   pineapples, dates, and citrus fruit.

   **Mask:** `The greenhouse they have in Aliance Nebraska grows pineapple and
   dates and citrus.`
4. **Takeaway:** The author views the greenhouse project as an initial step
   toward a retirement that is not consumption-based.

   **Mask:** `our geothermal solar powered greenhouse` + `This will be the first
   steps to my non consumption based retirement.`

The first TEv4.1 takeaway also incorrectly rewrote the name `Flexicables` as
generic flexible cables. That is a separate extraction error.

### The vector being tested

The old retirement mask contained `This` without its referent. TEv4.1 added
`our geothermal solar powered greenhouse` so a person could understand what
the retirement sentence referred to.

The old and new target vectors have cosine `0.8002`: they remain related, but
the added greenhouse fragment moved the new vector strongly toward greenhouse
and energy content.

### Controlled neighbor — future solar generation

**Complete candidate note**

> Solar power will be the vast majority of power generation in the future

Both runs selected the complete sentence, so the candidate vector was
byte-identical.

- TEv3.1 takeaway: `Solar power will provide the vast majority of future power
  generation.`
- TEv4.1 takeaway: `In the future, solar energy will account for the vast
  majority of power generation.`
- Mask in both runs: `Solar power will be the vast majority of power generation
  in the future`

Cosine to the retirement target rose from `0.3690` to `0.6565`. Because the
candidate did not change, adding the greenhouse fragment to the retirement
target caused the increase.

### Retirement-related neighbor — leaving the conventional grind

**Complete candidate note**

> Hey there, folks! So, I've got this idea to start sharing daily updates on
> Nostr, kind of like a journal, about my journey to break free from the typical
> American grind. The plan? Well, by 04/20/2025, my wife and I are hoping to hop
> on a plane to Argentina with just the essentials we can carry onboard.
>
> After some thinking, we've come to the conclusion that life might just be
> sweeter elsewhere. We're pretty keen on this whole flag theory concept and
> are excited about stacking passports.
>
> I figure sharing online will not only keep us on track but maybe also show
> others that there's more to life than the usual rat race. Let's see where this
> adventure takes us!

The TEv3.1 candidate was:

- **Takeaway:** The user plans to post daily Nostr updates documenting an
  effort to leave the conventional American grind.
- **Mask:** `start sharing daily updates on Nostr` + `about my journey to break
  free from the typical American grind`

Holding that TEv3.1 candidate fixed, its cosine to the retirement target fell
from `0.3957` to `0.2486` when only the target changed.

TEv4.1 regenerated the candidate as:

- **Takeaway:** The author intends to publish daily, journal-style updates on
  Nostr documenting an effort to escape the conventional American work-centered
  grind.
- **Mask:** `I've got this idea to start sharing daily updates on Nostr, kind
  of like a journal, about my journey to break free from the typical American
  grind.`

That regenerated candidate ranked 32 at `0.2282` against the new target.

### The old target's leading cross-note neighbors

| Rank | Neighbor meaning | Cosine |
|---:|---|---:|
| 1 | Eliminating personal ownership and control of money | `0.5202` |
| 2 | Financial independence as the ultimate target | `0.4011` |
| 3 | Leaving the conventional American grind | `0.3957` |
| 4 | Bitcoin as an escape from financial surveillance | `0.3692` |
| 5 | Future solar energy generation | `0.3690` |
| 6 | A miner maintaining greenhouse temperature | `0.3626` |
| 7 | A retirement-planning packet | `0.3562` |
| 8 | Automatic backups | `0.3392` |
| 9 | Declining an employer retirement account | `0.3216` |
| 10 | Affogato | `0.3161` |
| 11 | Simple living | `0.3128` |
| 12 | A miner using surplus solar energy | `0.3104` |

The old mask was imperfect, but its leading neighborhood contained several
financial-independence, retirement, and alternative-lifestyle meanings.

### The new target's leading cross-note neighbors

| Rank | Neighbor meaning | Cosine |
|---:|---|---:|
| 1 | Future solar energy generation | `0.6565` |
| 2 | Winter heating leaves little surplus solar energy for mining | `0.5942` |
| 3 | Programming a miner to use surplus solar energy | `0.5801` |
| 4 | A miner maintaining greenhouse temperature and recording statistics | `0.5015` |
| 5 | A miner starting below a greenhouse temperature threshold | `0.4197` |
| 6 | A solar project framed as proof of work | `0.3801` |
| 7 | A solar array may charge a car or run a miner | `0.3793` |
| 8 | Connecting a solar array | `0.3707` |
| 9 | Fourteen solar panels ready for connection | `0.3594` |
| 10 | Excitement about home Bitcoin mining | `0.3555` |
| 11 | Home mining contributing network computing power | `0.3507` |
| 12 | Authorities targeting financial independence | `0.3222` |
| 13 | Retiring in 2029 while declining an employer retirement account | `0.3153` |

Direct retirement results begin at rank 13. Other relevant placements include:

- declining an employer retirement account: rank 17, `0.2910`;
- retiring in 2029: rank 27, `0.2415`;
- a retirement-planning packet: rank 29, `0.2361`;
- alternatives to the rat race: rank 31, `0.2332`;
- escaping the conventional work-centered grind: rank 32, `0.2282`;
- simple living: rank 40, `0.2130`;
- minimalism: rank 77, `0.1197`;
- being largely retired: rank 102, `0.0759`.

### What failed

The new mask correctly resolved what `This` meant for a human. But SSE pooled
the newly selected `geothermal solar powered greenhouse` tokens as part of the
target meaning. The result became much better at retrieving solar, greenhouse,
and mining content and much worse at isolating retirement and non-consumption.

This is not hidden whole-note context leakage: the energy meaning was explicitly
added to the selected mask. TEv4.1 has no separate retirement-only takeaway for
this note, so it cannot represent the resolved retirement claim without also
selecting the greenhouse subject matter.

## Failure #5 — One meaning became multiple overlapping vectors

### Complete source note

> Annie's Saturday Morning Thoughts
>
> Don't assume that everyone who agrees with you in public agrees with you in
> private. 😏
>
> The wren on the fence has been chirping for a while. Must have good lungs.
>
> Only the things you choose without pressure define you. The rest is a facade.
> 🤥
>
> Flavored coffee is nice but can get old if you have it every day.
>
> Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree
> and a crossvine in bloom. This is the recipe for a good Saturday. 🤗

### Everything TEv3.1 generated from this note

1. **Takeaway:** Public agreement does not necessarily mean private agreement.

   **Mask:** `Don't assume that everyone who agrees with you in public agrees
   with you in private.`
2. **Takeaway:** A wren has been chirping on the fence for a long time and seems
   to have strong lungs.

   **Mask:** `The wren on the fence has been chirping for a while.` + `Must have
   good lungs.`
3. **Takeaway:** Only choices made without pressure define a person; the rest
   is a facade.

   **Mask:** `Only the things you choose without pressure define you.` + `The
   rest is a facade.`
4. **Takeaway:** Flavored coffee is enjoyable but becomes tiresome when
   consumed every day.

   **Mask:** `Flavored coffee is nice but can get old if you have it every day.`
5. **Takeaway:** Sunshine, a cool breeze, wildlife, tree shade, and blooming
   crossvine make for a good Saturday.

   **Mask:** `Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from
   an oak tree and a crossvine in bloom.` + `This is the recipe for a good
   Saturday.`

### Everything TEv4.1 generated from this note

1. **Takeaway:** The post is framed as Annie’s reflections from a Saturday
   morning.

   **Mask:** `Annie's Saturday Morning Thoughts`
2. **Takeaway:** A person should not assume that everyone who publicly expresses
   agreement with them privately holds the same view.

   **Mask:** `Don't assume that everyone who agrees with you in public agrees
   with you in private.`
3. **Takeaway:** A wren on a fence has been chirping for some time, which the
   author takes as evidence that the bird has strong lungs.

   **Mask:** `The wren on the fence has been chirping for a while. Must have good
   lungs.`
4. **Takeaway:** The author believes that only choices made freely and without
   pressure reveal a person’s true character.

   **Mask:** `Only the things you choose without pressure define you.`
5. **Takeaway:** The author believes that choices made under pressure create a
   false outward image rather than authentically defining the person.

   **Mask:** `Only the things you choose without pressure define you. The rest
   is a facade.`
6. **Takeaway:** Flavored coffee can be enjoyable, but drinking it every day can
   make it tiresome.

   **Mask:** `Flavored coffee is nice but can get old if you have it every day.`
7. **Takeaway:** The author says that sunshine, a cool breeze, doves, wrens,
   robins, squirrels, shade from an oak tree, and a blooming crossvine together
   make for a good Saturday.

   **Mask:** `Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from
   an oak tree and a crossvine in bloom. This is the recipe for a good Saturday.`

### The duplicate autonomy representation

TEv3.1 produced one autonomy vector from both sentences:

> Only the things you choose without pressure define you. The rest is a facade.

TEv4.1 produced two vectors:

1. one from only `Only the things you choose without pressure define you.`;
2. one from `Only the things you choose without pressure define you. The rest
   is a facade.`

The second TEv4.1 mask selects exactly the same tokens as the TEv3.1 autonomy
mask. Their vectors are byte-identical. The two TEv4.1 autonomy vectors have
same-note cosine `0.9225`, so the pipeline now represents nearly the same source
meaning twice.

### The coffee neighbor retained by the unchanged vector

**Complete candidate note**

> You’ve had coffee. But have you had your coffee?”
> https://blossom.primal.net/1379b90996b8ecb2f4fdef6756fd61c4ab964fa19f9e1505950e10a4d97640dd.jpg
> Roasting your own beans means discovering a taste profile that’s uniquely
> yours. It’s a personal journey that no bag of pre-roasted coffee can
> replicate.
>
> Sipping @ #coffeechain
>
> #HotTake ☕

The relevant coffee vector was byte-identical between runs:

- TEv3.1 takeaway: `Roasting your own coffee beans creates a uniquely personal
  flavor profile that pre-roasted coffee cannot replicate.`
- TEv4.1 takeaway: `The author views self-roasting and discovering a personal
  coffee profile as an individual journey that pre-roasted coffee cannot
  reproduce.`
- Mask in both runs: `Roasting your own beans means discovering a taste profile
  that’s uniquely yours. It’s a personal journey that no bag of pre-roasted
  coffee can replicate.`

For the unchanged full autonomy vector, the coffee cosine remains exactly
`0.4347354678`, and coffee remains rank 10. TEv3.1's added autonomy coverage
still places eight appropriate autonomy or authenticity vectors ahead of it.

The new first-clause-only autonomy vector has a different neighborhood. Coffee
takeaways occupy ranks 4 and 8–10:

| Rank | Neighbor meaning | Cosine |
|---:|---|---:|
| 1 | Wisdom in remaining true to oneself | `0.5431` |
| 2 | Moral conduct versus temporary authority | `0.5237` |
| 3 | Outsiders following their own paths | `0.5191` |
| 4 | Challenging others to change a decaf-coffee opinion | `0.5017` |
| 5 | Character over external validation | `0.4824` |
| 6 | Forced concealment of potential | `0.4717` |
| 7 | Integrity and authenticity | `0.4705` |
| 8 | Decaf enthusiasts versus caffeine drinkers | `0.4664` |
| 9 | A personal coffee-roasting journey | `0.4643` |
| 10 | Decaf drinkers as genuine coffee enthusiasts | `0.4636` |

### The complete-run overlap change

| Measurement | TEv3.1 | TEv4.1 |
|---|---:|---:|
| Vectors | 131 | 194 |
| Mean vectors per note | 2.62 | 3.88 |
| Same-note pairs with overlapping selected tokens | 6 | 192 |
| All same-note pairs | 193 | 410 |

Forty of the 50 notes gained takeaways; none lost takeaways. Overlap is not
automatically wrong because one source passage can support multiple meanings.
But this run often represented almost the same passage more than once, as the
two autonomy vectors demonstrate. That adds computation and gives one source
meaning multiple opportunities to occupy retrieval results.

### What failed

The new pipeline did not merely clarify masks. It changed how many meanings it
claimed each note communicated and frequently reused the same source tokens.
The autonomy example is now represented twice, and those two vectors have
materially different cross-note neighborhoods. The pipeline emits and uses both;
it does not choose the better one.

## Other extraction failures

These are independent prompt or mask failures observed in the same run:

| Generated takeaway | Selected mask | Problem |
|---|---|---|
| `The post links to id Software’s Doom source-code repository and a separate Doom-related social-media post as references for the licensing update.` | `Doom 1 and 2 are now officially licensed under the #GPL, no longer dual-licensed with the DSL :)` | The licensing sentence does not contain either link's meaning. |
| `The post also links to a Hacker News discussion of the article.` | `Comments` | `Comments` does not identify Hacker News or the article. |
| `The author provides a link to the pypush project’s GitHub repository.` | `pypush` | The project name does not establish that the omitted link is a GitHub repository. |
| `Flexible cables have been installed as part of a greenhouse project shared by the author and others.` | `Flexicables installed for our ` + `greenhouse.` | `Flexicables` was rewritten as generic flexible cables. |

The first three expose a mismatch between the prompts:

1. TPv3.81 can preserve meaning contributed by a URL.
2. MPv3.3 forbids selecting URLs.
3. The mask generator substitutes nearby source words that do not contain the
   omitted link's meaning.

Mechanical validation proves that each selected fragment occurs in the source
and appears in source order. It cannot prove that the fragments preserve the
takeaway's meaning.

## Aggregate measurements

The cross-note cosine distribution barely changed:

| Measurement | TEv3.1 | TEv4.1 |
|---|---:|---:|
| Median | `0.0520` | `0.0490` |
| Mean | `0.0728` | `0.0701` |
| p95 | `0.3214` | `0.3169` |

These measurements do not show a global geometry improvement.

## Conclusion

TEv4.1 tested:

> Resolving ambiguous masks by adding all source context needed to reconstruct
> the takeaway will improve the SSE geometry.

The evidence does not support that hypothesis.

- The surveillance target moved away from direct government control and toward
  generic software and platforms.
- The retirement target moved strongly toward solar, greenhouse, and mining
  content.
- The new prompts produced many more overlapping vectors, including multiple
  vectors for nearly the same source meaning.
- Additional unsupported and distorted extractions remained.

This does not reject communicated-meaning vectors or SSE generally. It rejects
the simpler assumption that a source mask that is more self-contained for a
person will necessarily produce a better-isolated SSE vector.

Both prompts changed together, so TEv4.1 cannot attribute the result to
TPv3.81 or MPv3.3 alone. Generation was one run, and these 50 notes are a
diagnostic set rather than a representative sample. The experiment does not
establish population-level accuracy.

## Exact controls and preserved evidence

The ordered 50-note set has SHA-256:

`c7064a8eff5826273fc514ab47ee7b7cd1f91c1f994e3de6d2887d23c8843c85`

TEv4.1 used:

- TPv3.81;
- MPv3.3;
- `gpt-5.6-sol` at `max` reasoning;
- one fresh ephemeral Codex process for every takeaway and mask call;
- the same SSE checkpoint, Sentence-T5 base model, worker, 768-dimensional
  output, and inference batch size as TEv3.1.

No generated result received a subjective correction pass. One mask response
contained a non-exact substring. Mechanical validation rejected it, and a
fresh retry succeeded. The rejected attempt remains in the audit log.

The [immutable TEv4.1 archive and inspection
instructions](/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/baselines/communicated-meaning-tev4-1/README.md)
preserve:

- the exact 50-note input and generation configurations;
- every accepted fresh-context response;
- all raw call logs, including the mechanically rejected attempt;
- the source-bound proposal and SSE worker request;
- the raw vectors and worker receipt;
- the complete pairwise cosine analysis and manifests.
