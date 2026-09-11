# TEv4.1 — Did clearer masks produce better semantic vectors?

## Status

Executed historical diagnostic using communicated takeaways as vector units.
It explains one transition toward atomic-subject masks, but it does not define
or validate the current intended representation.

## Result

TEv4.1 did not support the hypothesis.

TEv4.1 tested whether making a mask self-contained would make SSE represent its
takeaway more cleanly. The evidence shows that adding a referent to a mask can
move its vector toward the referent's subject matter. It does not establish that
self-contained masks are always worse, nor does it establish the current
atomic-subject design.

The main argument below is deliberately sequential. Each claim presents its
evidence before its analysis. Complete generation records for the three
inspected source notes follow afterward; the immutable archive preserves the
full 50-note run.

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
In every note below, `⟦…⟧` marks text selected by the mask; the surrounding
text is visible context that was not selected for pooling.

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

## Logical argument

### Claim 1 — `RET-NEW` adds solar-greenhouse text to `RET-OLD`

#### Evidence

Both retirement target vectors came from this exact note:

> Flexicables installed for our geothermal solar powered greenhouse. The
> greenhouse they have in Aliance Nebraska grows pineapple and dates and
> citrus.
> This will be the first steps to my non consumption based retirement.
> https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

**`RET-OLD` — TEv3.1 target mask:**

> Flexicables installed for our geothermal solar powered greenhouse. The
> greenhouse they have in Aliance Nebraska grows pineapple and dates and
> citrus.
> ⟦This will be the first steps to my non consumption based retirement.⟧
> https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

**`RET-NEW` — TEv4.1 target mask:**

> Flexicables installed for ⟦our geothermal solar powered greenhouse⟧. The
> greenhouse they have in Aliance Nebraska grows pineapple and dates and
> citrus.
> ⟦This will be the first steps to my non consumption based retirement.⟧
> https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

The note, SSE checkpoint, and inference configuration were fixed. `RET-OLD` and
`RET-NEW` have cosine `0.8002`, so adding the referent changed the vector.

#### Analysis

This evidence establishes the intervention: `RET-NEW` directly pooled the words
`our geothermal solar powered greenhouse`, while `RET-OLD` did not. It does not
yet establish whether that change was helpful or harmful.

### Claim 2 — `RET-NEW` became more similar to one fixed solar vector

#### Evidence

The controlled candidate was this one-sentence note:

> ⟦Solar power will be the vast majority of power generation in the future⟧

Both runs selected that complete sentence. Its vector was byte-identical across
runs. Its cosine to the target was:

| Target | Cosine to the fixed solar candidate |
|---|---:|
| `RET-OLD` | `0.3690` |
| `RET-NEW` | `0.6565` |

#### Analysis

Because the candidate did not change, the target-mask change caused the
increase. This proves only that `RET-NEW` became more similar to this one
solar vector. It does not, by itself, show that retirement meaning became
weaker or that the new vector was worse.

### Claim 3 — `RET-NEW` became less similar to one fixed retirement vector

#### Evidence

The controlled retirement candidate came from this note:

> When I joined my current company, I was provided a retirement packet to fill
> out.
>
> In it, I wrote that I planned on retiring in 2029, and then declined opening a
> retirement account with them.
>
> #JustBitcoinerThings

The fixed candidate vector selected:

> ⟦When I joined my current company, I was provided a retirement packet⟧ to fill
> out.
>
> In it, I wrote that I planned on retiring in 2029, and then declined opening a
> retirement account with them.
>
> #JustBitcoinerThings

The TEv3.1 candidate vector was held fixed while only the target changed:

| Fixed candidate meaning | `RET-OLD` | `RET-NEW` |
|---|---:|---:|
| Receiving a retirement packet | `0.3562099685` | `0.2455033805` |

#### Analysis

This explicitly retirement-related candidate was less similar to `RET-NEW`
than to `RET-OLD`. That is direct retirement evidence, unlike the weaker “break
free from the typical American grind” comparison. It is still only one
candidate and does not establish movement away from every retirement meaning.

Claims 2 and 3 together establish the direction of this one target's movement:
adding the greenhouse referent made it more similar to the fixed solar vector
and less similar to the fixed retirement vector above.

This does not prove that the new vector misrepresented the complete compound
claim. A solar greenhouse genuinely is part of that claim. It shows that making
the mask self-contained traded away similarity to the fixed retirement
representation used in this comparison.

### Claim 4 — `CTRL-NEW` showed the same kind of tradeoff

#### Evidence

Both control targets came from this note:

> they want to control everything..
> ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows,
> #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all
> those OS's are saturated with telemetry mechanisms and APIs that have access
> to everything on your devices.. ..i'm still on iOS phone-wise, but my days are
> numbered with that.. ..likely moving to #GrapheneOS (although i already try to
> use my phone as little as possible).. ..i've already switched to #Linux
> computer-wise.. ..free and opensource is the only way to navigate this tech
> surveillance state with any level of sovereignty

**`CTRL-OLD` — TEv3.1 target mask:**

> ⟦they want to control everything⟧..
> ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows,
> #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all
> those OS's are saturated with telemetry mechanisms and APIs that have access
> to everything on your devices.. ..i'm still on iOS phone-wise, but my days are
> numbered with that.. ..likely moving to #GrapheneOS (although i already try to
> use my phone as little as possible).. ..i've already switched to #Linux
> computer-wise.. ..free and opensource is the only way to navigate this tech
> surveillance state with any level of sovereignty

**`CTRL-NEW` — TEv4.1 target mask:**

> ⟦they want to control everything⟧..
> ..if you think your #Nostr nsec key is safe on ⟦a proprietary OS ( #Windows,
> #macOS, #iOS, #Android, etc.)⟧ then you are missing the bigger picture..
> ..⟦all those OS's are saturated with telemetry mechanisms and APIs that have
> access to everything on your devices⟧.. ..i'm still on iOS phone-wise, but my
> days are numbered with that.. ..likely moving to #GrapheneOS (although i
> already try to use my phone as little as possible).. ..i've already switched
> to #Linux computer-wise.. ..free and opensource is the only way to navigate
> ⟦this tech surveillance state⟧ with any level of sovereignty

Three candidate vectors were held fixed:

1. Direct government control:

   > NEW - ⟦The CCC warns that the German left-green-liberal government wants to
   > "effectively end anonymity" and make all citizens "identifiable at all
   > times and in all places,"⟧ including by opening doors to Palantir and other
   > surveillance software.
   >
   > https://www.ccc.de/en/updates/2024/biometrischer-uberwachungsexzess-der-bundesregierung
   >
   > https://hell.twtr.plus/media/cf6857f1982ee096057b3c09692a162778dd08f6e86e47e845309425238d567a.file

2. Generic free software:

   > ⟦Getting close to 100% of my software stack being free and open source.⟧

3. A cross-platform open-source application:

   > It's ready! ⟦#pypush can now send and receive #iMessage, on any platform,
   > completely server-less and open-source!⟧ 🎉
   >
   > https://github.com/JJTech0130/pypush

Their cosines changed as follows:

| Fixed candidate meaning | `CTRL-OLD` | `CTRL-NEW` |
|---|---:|---:|
| Government ending anonymity | `0.5067` | `0.3327` |
| Free and open-source software stack | `0.3763` | `0.4650` |
| Cross-platform open-source iMessage application | `0.4005` | `0.6599` |

#### Analysis

`CTRL-NEW` was less similar than `CTRL-OLD` to the direct government-control
candidate and more similar than `CTRL-OLD` to the two software candidates.
Because all three candidates were held fixed, the target change caused those
differences.

This is a second concrete example of referent or explanatory source text
changing which part of a compound meaning dominates the resulting geometry. It
does not prove that every self-contained mask behaves this way.

### Claim 5 — TEv4.1 also changed the number of vectors produced per note

#### Evidence

TEv3.1 represented this source passage once:

> ⟦Only the things you choose without pressure define you.⟧ ⟦The rest is a
> facade.⟧

TEv4.1 represented it twice:

> ⟦Only the things you choose without pressure define you.⟧ The rest is a
> facade.

and:

> ⟦Only the things you choose without pressure define you. The rest is a
> facade.⟧

The second TEv4.1 vector is byte-identical to the TEv3.1 vector. The two TEv4.1
vectors have cosine `0.9225` with each other.

Across all 50 notes:

| Measurement | TEv3.1 | TEv4.1 |
|---|---:|---:|
| Vectors | 131 | 194 |
| Mean vectors per note | 2.62 | 3.88 |
| Same-note pairs with overlapping selected tokens | 6 | 192 |
| All same-note pairs | 193 | 410 |

Forty notes gained takeaways; no note lost takeaways.

#### Analysis

TEv4.1 was not merely the old decomposition with clearer masks. It also emitted
more meanings and reused source spans much more often. Some overlap can be
legitimate, but the example above gives nearly the same source meaning two
opportunities to enter retrieval results.

Therefore, aggregate TEv3.1-versus-TEv4.1 changes cannot be attributed only to
mask clarification. Controlled target/candidate comparisons are required.

### Claim 6 — Some generated takeaways were not supported by selectable text

#### Evidence

One generated takeaway was:

> The post also links to a Hacker News discussion of the article.

Its complete source and selected mask were:

> Why a spritz of water before grinding coffee yields better results
>
> ⟦Comments⟧ ( https://news.ycombinator.com/item?id=38554310 )
>
> https://arstechnica.com/science/2023/12/study-why-a-spritz-of-water-before-grinding-coffee-yields-less-waste-tastier-espresso/

MPv3.3 was forbidden from selecting URLs. The word `Comments` alone does not
identify Hacker News or the linked article.

#### Analysis

This mask is mechanically valid—the selected substring exists—but it does not
contain the takeaway's meaning. Exact-substring validation cannot detect that
semantic failure.

This is separate from SSE geometry. It shows that TPv3.81 can generate meaning
from a URL that MPv3.3 is then unable to ground under its selection rules.

### What the claims jointly establish

The controlled evidence establishes that:

1. Adding referent text can change a vector.
2. In the greenhouse case, the target became more similar to one fixed solar
   vector and less similar to one fixed retirement vector.
3. In the surveillance case, the target became less similar to one fixed
   government-control vector and more similar to two fixed software vectors.
4. TEv4.1 changed decomposition granularity as well as mask context.
5. Some generated takeaways could not be supported by the permitted source
   fragments.

The evidence does **not** establish that:

- self-contained masks are always worse;
- SSE cannot represent independently searchable meanings;
- atomic vectors are already proven to be the right solution;
- TPv3.81 or MPv3.3 individually caused every observed change;
- these 50 diagnostic notes estimate corpus-wide performance.

The hypothesis this result suggested at the time was:

> One vector should represent one independently searchable meaning, while one
> note may produce several such vectors.

For the greenhouse note, that could mean separate vectors for `geothermal solar
powered greenhouse` and `non consumption based retirement`, rather than adding
the greenhouse phrase merely to make the retirement sentence self-contained.
That was not a TEv4.1 result and is not the current definition of an atomic
subject.

## Detailed evidence A — Surveillance

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

   **Mask over the complete original note:**

   > ⟦they want to control everything⟧..
   > ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

2. **Takeaway:** The author believes Nostr nsec keys are unsafe on proprietary operating systems because their telemetry and APIs can access everything on a device.

   **Mask over the complete original note:**

   > they want to control everything..
   > ..⟦if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture⟧.. ..⟦all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices⟧.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

3. **Takeaway:** The author plans to leave iOS, likely for GrapheneOS, and already minimizes phone use.

   **Mask over the complete original note:**

   > they want to control everything..
   > ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..⟦i'm still on iOS phone-wise, but my days are numbered with that⟧.. ..⟦likely moving to #GrapheneOS (although i already try to use my phone as little as possible)⟧.. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

4. **Takeaway:** The author has already switched to Linux on computers.

   **Mask over the complete original note:**

   > they want to control everything..
   > ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..⟦i've already switched to #Linux computer-wise⟧.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

5. **Takeaway:** The author considers free and open-source software the only way to retain sovereignty in a technology surveillance state.

   **Mask over the complete original note:**

   > they want to control everything..
   > ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..⟦free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty⟧

### Everything TEv4.1 generated from this note

1. **Takeaway:** The author believes that the forces behind pervasive proprietary-technology surveillance seek total control.

   **Mask over the complete original note:**

   > ⟦they want to control everything⟧..
   > ..if you think your #Nostr nsec key is safe on ⟦a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.)⟧ then you are missing the bigger picture.. ..⟦all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices⟧.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate ⟦this tech surveillance state⟧ with any level of sovereignty

2. **Takeaway:** The author warns that treating a Nostr nsec private key as secure on an operating system they regard as proprietary—such as Windows, macOS, iOS, or Android—ignores broader surveillance and device-access risks.

   **Mask over the complete original note:**

   > they want to control everything..
   > ..⟦if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture⟧.. ..⟦all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices⟧.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

3. **Takeaway:** The author claims that Windows, macOS, iOS, Android, and similar operating systems are saturated with telemetry mechanisms and APIs capable of accessing everything on a user's device.

   **Mask over the complete original note:**

   > they want to control everything..
   > ..if you think your #Nostr nsec key is safe on a proprietary OS ( ⟦#Windows, #macOS, #iOS, #Android, etc.⟧) then you are missing the bigger picture.. ..⟦all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices⟧.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

4. **Takeaway:** The author still uses iOS on their phone but expects to stop soon.

   **Mask over the complete original note:**

   > they want to control everything..
   > ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..⟦i'm still on iOS phone-wise, but my days are numbered with that⟧.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

5. **Takeaway:** The author will likely replace iOS with GrapheneOS, despite already trying to use their phone as little as possible.

   **Mask over the complete original note:**

   > they want to control everything..
   > ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..⟦i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible)⟧.. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

6. **Takeaway:** The author has already switched their computer operating system to Linux.

   **Mask over the complete original note:**

   > they want to control everything..
   > ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..⟦i've already switched to #Linux computer-wise⟧.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

7. **Takeaway:** The author believes free and open-source software is the only way to retain any degree of technological sovereignty within what they view as a technology-surveillance state.

   **Mask over the complete original note:**

   > they want to control everything..
   > ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..⟦free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty⟧

### Target masks — `CTRL-OLD` and `CTRL-NEW`

TEv3.1 represented the control claim using only:

> they want to control everything

TEv4.1 tried to resolve who `they` meant by also selecting the proprietary-OS,
telemetry, and technology-surveillance-state fragments. `CTRL-OLD` and
`CTRL-NEW` have cosine `0.5209`, so this changed the vector.

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

The relevant candidate vector selected the same source text in both runs.

**Shared mask over the complete original note:**

> NEW - ⟦The CCC warns that the German left-green-liberal government wants to
> "effectively end anonymity" and make all citizens "identifiable at all times
> and in all places,"⟧ including by opening doors to Palantir and other
> surveillance software.
>
> https://www.ccc.de/en/updates/2024/biometrischer-uberwachungsexzess-der-bundesregierung
>
> https://hell.twtr.plus/media/cf6857f1982ee096057b3c09692a162778dd08f6e86e47e845309425238d567a.file

Its generated takeaway changed wording, but its source mask and vector were
byte-identical:

- TEv3.1: `The CCC warns that Germany’s left-green-liberal government seeks to
  effectively eliminate anonymity and make citizens identifiable everywhere.`
- TEv4.1: `The Chaos Computer Club warns that Germany’s left-green-liberal
  governing coalition wants to effectively eliminate anonymity by making every
  citizen identifiable at all times and in all places.`

The candidate's cosine was `0.5067` with `CTRL-OLD` and `0.3327` with
`CTRL-NEW`. Because the candidate vector did not change, replacing `CTRL-OLD`
with `CTRL-NEW` caused the decrease.

### Controlled neighbor 2 — generic free software moved closer

**Complete candidate note**

> Getting close to 100% of my software stack being free and open source.

Both runs selected the entire note. The vector was byte-identical.

- TEv3.1 takeaway: `The user is close to making their entire software stack
  free and open source.`
- TEv4.1 takeaway: `The author is nearing the point where their entire software
  stack consists of free and open-source software.`

**Shared mask over the complete original note:**

> ⟦Getting close to 100% of my software stack being free and open source.⟧

The candidate's cosine was `0.3763` with `CTRL-OLD` and `0.4650` with
`CTRL-NEW`. Because the candidate did not change, replacing `CTRL-OLD` with
`CTRL-NEW` caused the increase.

### New rank-1 neighbor — cross-platform iMessage

**Complete candidate note**

> It's ready! #pypush can now send and receive #iMessage, on any platform,
> completely server-less and open-source! 🎉
>
> https://github.com/JJTech0130/pypush

TEv3.1 generated one vector:

- **Takeaway:** pypush can now send and receive iMessages on any platform as a
  serverless, open-source project.

  **Mask over the complete original note:**

  > It's ready! ⟦#pypush can now send and receive #iMessage, on any platform,
  > completely server-less and open-source!⟧ 🎉
  >
  > https://github.com/JJTech0130/pypush

TEv4.1 generated four vectors:

1. **Takeaway:** The author announces that the pypush project is ready.

   **Mask over the complete original note:**

   > ⟦It's ready! #pypush⟧ can now send and receive #iMessage, on any platform,
   > completely server-less and open-source! 🎉
   >
   > https://github.com/JJTech0130/pypush

2. **Takeaway:** Pypush can now send and receive messages through Apple’s
   iMessage service on any platform.

   **Mask over the complete original note:**

   > It's ready! ⟦#pypush can now send and receive #iMessage, on any platform⟧,
   > completely server-less and open-source! 🎉
   >
   > https://github.com/JJTech0130/pypush

3. **Takeaway:** Pypush is entirely serverless and open-source.

   **Mask over the complete original note:**

   > It's ready! ⟦#pypush⟧ can now send and receive #iMessage, on any platform,
   > ⟦completely server-less and open-source⟧! 🎉
   >
   > https://github.com/JJTech0130/pypush

4. **Takeaway:** The author provides a link to the pypush project’s GitHub
   repository.

   **Mask over the complete original note:**

   > It's ready! #⟦pypush⟧ can now send and receive #iMessage, on any platform,
   > completely server-less and open-source! 🎉
   >
   > https://github.com/JJTech0130/pypush

The TEv4.1 platform-only vector became `CTRL-NEW`'s rank-1 cross-note
neighbor at `0.6889`. Comparing every old/new combination shows where the
increase came from:

| Control target | iMessage candidate | Cosine |
|---|---|---:|
| `CTRL-OLD` | TEv3.1 combined vector | `0.4005` |
| `CTRL-OLD` | TEv4.1 platform-only vector | `0.2810` |
| `CTRL-NEW` | TEv3.1 combined vector | `0.6599` |
| `CTRL-NEW` | TEv4.1 platform-only vector | `0.6889` |

Even with the TEv3.1 iMessage vector held fixed, replacing `CTRL-OLD` with
`CTRL-NEW` raised the cosine from `0.4005` to `0.6599`. The source text added to
`CTRL-NEW` caused most of the increase.

### Automatic-backup observation — not a controlled comparison

`CTRL-OLD`'s second-nearest cross-note result was this takeaway:

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

**TEv3.1 mask over the complete original note:**

> I'm thinking I'll regularly post about open source tech I find useful.
>
> Molly is a fork of Signal, made to be more secure.
>
> Some of it's features include:
> No proprietary blobs/code.
> Molly protects your messages with passphrase encryption.
> The app can lock down automatically after a set time of not being opened.
> Molly, "Securely shreds sensitive data from RAM."
> ⟦You can create automatic backups⟧
> It even supports setting an app proxy through Tor via Orbot.
>
> Available on their own Fdroid repo:
> https://molly.im/

**TEv4.1 mask over the complete original note:**

> I'm thinking I'll regularly post about open source tech I find useful.
>
> ⟦Molly⟧ is a fork of Signal, made to be more secure.
>
> Some of it's features include:
> No proprietary blobs/code.
> Molly protects your messages with passphrase encryption.
> The app can lock down automatically after a set time of not being opened.
> Molly, "Securely shreds sensitive data from RAM."
> You ⟦can create automatic backups⟧
> It even supports setting an app proxy through Tor via Orbot.
>
> Available on their own Fdroid repo:
> https://molly.im/

It was rank 2 at `0.4175` under `CTRL-OLD` and rank 43 at `0.1723` under
`CTRL-NEW`. This looks better, but both the target and candidate masks changed,
so this pair cannot show which change caused the improvement.

### Analysis

If `CTRL-NEW` is intended to preserve an independently searchable `powerful
actors seeking control` meaning, these controls did not improve: cosine to the
fixed government-control vector fell, while cosines to the fixed free-software
and cross-platform-application vectors rose. This does not establish the
intrinsic quality of the complete compound surveillance representation.

The automatic-backup result is not part of that controlled conclusion because
both its candidate mask and the target mask changed.

## Detailed evidence B — Retirement and greenhouse

### Complete source note

> Flexicables installed for our geothermal solar powered greenhouse. The
> greenhouse they have in Aliance Nebraska grows pineapple and dates and
> citrus.
> This will be the first steps to my non consumption based retirement.
> https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

### Everything TEv3.1 generated from this note

1. **Takeaway:** Flexicables have been installed for the author's geothermal, solar-powered greenhouse.

   **Mask over the complete original note:**

   > ⟦Flexicables installed for our geothermal solar powered greenhouse.⟧ The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.
   > This will be the first steps to my non consumption based retirement. https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

2. **Takeaway:** A greenhouse in Aliance, Nebraska grows pineapples, dates, and citrus.

   **Mask over the complete original note:**

   > Flexicables installed for our geothermal solar powered greenhouse. ⟦The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.⟧
   > This will be the first steps to my non consumption based retirement. https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

3. **Takeaway:** The greenhouse project is the author's first step toward a non-consumption-based retirement.

   **Mask over the complete original note:**

   > Flexicables installed for our geothermal solar powered greenhouse. The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.
   > ⟦This will be the first steps to my non consumption based retirement.⟧ https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

### Everything TEv4.1 generated from this note

1. **Takeaway:** Flexible cables have been installed as part of a greenhouse project shared by the author and others.

   **Mask over the complete original note:**

   > ⟦Flexicables installed for our ⟧geothermal solar powered ⟦greenhouse.⟧ The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.
   > This will be the first steps to my non consumption based retirement. https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

2. **Takeaway:** The shared greenhouse is designed to use geothermal and solar energy.

   **Mask over the complete original note:**

   > Flexicables installed for ⟦our geothermal solar powered greenhouse⟧. The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.
   > This will be the first steps to my non consumption based retirement. https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

3. **Takeaway:** An existing greenhouse in Alliance, Nebraska, grows pineapples, dates, and citrus fruit.

   **Mask over the complete original note:**

   > Flexicables installed for our geothermal solar powered greenhouse. ⟦The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.⟧
   > This will be the first steps to my non consumption based retirement. https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

4. **Takeaway:** The author views the greenhouse project as an initial step toward a retirement that is not consumption-based.

   **Mask over the complete original note:**

   > Flexicables installed for ⟦our geothermal solar powered greenhouse⟧. The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.
   > ⟦This will be the first steps to my non consumption based retirement.⟧ https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

### Target masks — `RET-OLD` and `RET-NEW`

`RET-OLD` contained `This` without its referent. `RET-NEW` added `our geothermal
solar powered greenhouse` so a person could understand what the retirement
sentence referred to.

`RET-OLD` and `RET-NEW` have cosine `0.8002`: they remain related, but they are
not identical. This comparison alone does not establish the direction of the
change.

### Controlled neighbor — future solar generation

**Complete candidate note**

> Solar power will be the vast majority of power generation in the future

Both runs selected the complete sentence, so the candidate vector was
byte-identical.

- TEv3.1 takeaway: `Solar power will provide the vast majority of future power
  generation.`
- TEv4.1 takeaway: `In the future, solar energy will account for the vast
  majority of power generation.`

**Shared mask over the complete original note:**

> ⟦Solar power will be the vast majority of power generation in the future⟧

The candidate's cosine was `0.3690` with `RET-OLD` and `0.6565` with `RET-NEW`.
Because the candidate did not change, the source text added to `RET-NEW` caused
the increase.

### Controlled candidate — explicit retirement

**Complete candidate note**

> When I joined my current company, I was provided a retirement packet to fill
> out.
>
> In it, I wrote that I planned on retiring in 2029, and then declined opening a
> retirement account with them.
>
> #JustBitcoinerThings

The fixed TEv3.1 candidate selected:

> ⟦When I joined my current company, I was provided a retirement packet⟧ to fill
> out.
>
> In it, I wrote that I planned on retiring in 2029, and then declined opening a
> retirement account with them.
>
> #JustBitcoinerThings

Holding that exact TEv3.1 candidate vector fixed, its cosine was
`0.3562099685` with `RET-OLD` and `0.2455033805` with `RET-NEW`.

This candidate is explicitly about retirement. It replaces the weaker
American-grind proxy in the logical argument.

### Excluded proxy — leaving the conventional American grind

This comparison is preserved for audit, but it is not evidence that retirement
meaning weakened. Leaving the conventional American grind does not necessarily
mean retiring.

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

  **Mask over the complete original note:**

  > Hey there, folks! So, I've got this idea to ⟦start sharing daily updates on
  > Nostr⟧, kind of like a journal, ⟦about my journey to break free from the
  > typical American grind⟧. The plan? Well, by 04/20/2025, my wife and I are
  > hoping to hop on a plane to Argentina with just the essentials we can carry
  > onboard.
  >
  > After some thinking, we've come to the conclusion that life might just be
  > sweeter elsewhere. We're pretty keen on this whole flag theory concept and
  > are excited about stacking passports.
  >
  > I figure sharing online will not only keep us on track but maybe also show
  > others that there's more to life than the usual rat race. Let's see where
  > this adventure takes us!

Holding that TEv3.1 candidate fixed, its cosine was `0.3957` with `RET-OLD` and
`0.2486` with `RET-NEW`.

TEv4.1 regenerated the candidate as:

- **Takeaway:** The author intends to publish daily, journal-style updates on
  Nostr documenting an effort to escape the conventional American work-centered
  grind.

  **Mask over the complete original note:**

  > Hey there, folks! So, ⟦I've got this idea to start sharing daily updates on
  > Nostr, kind of like a journal, about my journey to break free from the
  > typical American grind.⟧ The plan? Well, by 04/20/2025, my wife and I are
  > hoping to hop on a plane to Argentina with just the essentials we can carry
  > onboard.
  >
  > After some thinking, we've come to the conclusion that life might just be
  > sweeter elsewhere. We're pretty keen on this whole flag theory concept and
  > are excited about stacking passports.
  >
  > I figure sharing online will not only keep us on track but maybe also show
  > others that there's more to life than the usual rat race. Let's see where
  > this adventure takes us!

That regenerated candidate ranked 32 at `0.2282` against `RET-NEW`.

### `RET-OLD`'s leading cross-note neighbors

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

`RET-OLD` was imperfect, but its leading neighborhood contained several
financial-independence, retirement, and alternative-lifestyle meanings.

### `RET-NEW`'s leading cross-note neighbors

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

The rank-29 packet result uses TEv4.1's separately regenerated candidate, whose
mask differs from the fixed TEv3.1 packet vector used in the controlled
`0.3562099685` versus `0.2455033805` comparison. The values answer different
questions and should not be compared as though the candidate were unchanged.

### Analysis

The new mask correctly resolved what `This` meant for a human, and SSE pooled
the newly selected `geothermal solar powered greenhouse` tokens as part of the
target meaning. Its cosine to one fixed solar vector rose, while its cosine to
one fixed retirement-packet vector fell.

The explicitly selected energy phrase provides a direct mechanism for the
change. SSE also contextualizes selected tokens against the complete note, so
this experiment does not isolate or rule out additional whole-note context
effects. This run emitted no separate retirement-only vector for this note.
Whether a more atomic extraction would preserve both meanings better remains an
untested hypothesis.

## Detailed evidence C — Overlapping vectors

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

   **Mask over the complete original note:**

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

2. **Takeaway:** A wren has been chirping on the fence for a long time and seems to have strong lungs.

   **Mask over the complete original note:**

   > Annie's Saturday Morning Thoughts
   >
   > Don't assume that everyone who agrees with you in public agrees with you in private. 😏
   >
   > ⟦The wren on the fence has been chirping for a while.⟧ ⟦Must have good lungs.⟧
   >
   > Only the things you choose without pressure define you. The rest is a facade. 🤥
   >
   > Flavored coffee is nice but can get old if you have it every day.
   >
   > Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree and a crossvine in bloom. This is the recipe for a good Saturday. 🤗

3. **Takeaway:** Only choices made without pressure define a person; the rest is a facade.

   **Mask over the complete original note:**

   > Annie's Saturday Morning Thoughts
   >
   > Don't assume that everyone who agrees with you in public agrees with you in private. 😏
   >
   > The wren on the fence has been chirping for a while. Must have good lungs.
   >
   > ⟦Only the things you choose without pressure define you.⟧ ⟦The rest is a facade.⟧ 🤥
   >
   > Flavored coffee is nice but can get old if you have it every day.
   >
   > Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree and a crossvine in bloom. This is the recipe for a good Saturday. 🤗

4. **Takeaway:** Flavored coffee is enjoyable but becomes tiresome when consumed every day.

   **Mask over the complete original note:**

   > Annie's Saturday Morning Thoughts
   >
   > Don't assume that everyone who agrees with you in public agrees with you in private. 😏
   >
   > The wren on the fence has been chirping for a while. Must have good lungs.
   >
   > Only the things you choose without pressure define you. The rest is a facade. 🤥
   >
   > ⟦Flavored coffee is nice but can get old if you have it every day.⟧
   >
   > Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree and a crossvine in bloom. This is the recipe for a good Saturday. 🤗

5. **Takeaway:** Sunshine, a cool breeze, wildlife, tree shade, and blooming crossvine make for a good Saturday.

   **Mask over the complete original note:**

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
   > ⟦Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree and a crossvine in bloom.⟧ ⟦This is the recipe for a good Saturday.⟧ 🤗

### Everything TEv4.1 generated from this note

1. **Takeaway:** The post is framed as Annie’s reflections from a Saturday morning.

   **Mask over the complete original note:**

   > ⟦Annie's Saturday Morning Thoughts⟧
   >
   > Don't assume that everyone who agrees with you in public agrees with you in private. 😏
   >
   > The wren on the fence has been chirping for a while. Must have good lungs.
   >
   > Only the things you choose without pressure define you. The rest is a facade. 🤥
   >
   > Flavored coffee is nice but can get old if you have it every day.
   >
   > Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree and a crossvine in bloom. This is the recipe for a good Saturday. 🤗

2. **Takeaway:** A person should not assume that everyone who publicly expresses agreement with them privately holds the same view.

   **Mask over the complete original note:**

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

3. **Takeaway:** A wren on a fence has been chirping for some time, which the author takes as evidence that the bird has strong lungs.

   **Mask over the complete original note:**

   > Annie's Saturday Morning Thoughts
   >
   > Don't assume that everyone who agrees with you in public agrees with you in private. 😏
   >
   > ⟦The wren on the fence has been chirping for a while. Must have good lungs.⟧
   >
   > Only the things you choose without pressure define you. The rest is a facade. 🤥
   >
   > Flavored coffee is nice but can get old if you have it every day.
   >
   > Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree and a crossvine in bloom. This is the recipe for a good Saturday. 🤗

4. **Takeaway:** The author believes that only choices made freely and without pressure reveal a person’s true character.

   **Mask over the complete original note:**

   > Annie's Saturday Morning Thoughts
   >
   > Don't assume that everyone who agrees with you in public agrees with you in private. 😏
   >
   > The wren on the fence has been chirping for a while. Must have good lungs.
   >
   > ⟦Only the things you choose without pressure define you.⟧ The rest is a facade. 🤥
   >
   > Flavored coffee is nice but can get old if you have it every day.
   >
   > Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree and a crossvine in bloom. This is the recipe for a good Saturday. 🤗

5. **Takeaway:** The author believes that choices made under pressure create a false outward image rather than authentically defining the person.

   **Mask over the complete original note:**

   > Annie's Saturday Morning Thoughts
   >
   > Don't assume that everyone who agrees with you in public agrees with you in private. 😏
   >
   > The wren on the fence has been chirping for a while. Must have good lungs.
   >
   > ⟦Only the things you choose without pressure define you. The rest is a facade.⟧ 🤥
   >
   > Flavored coffee is nice but can get old if you have it every day.
   >
   > Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree and a crossvine in bloom. This is the recipe for a good Saturday. 🤗

6. **Takeaway:** Flavored coffee can be enjoyable, but drinking it every day can make it tiresome.

   **Mask over the complete original note:**

   > Annie's Saturday Morning Thoughts
   >
   > Don't assume that everyone who agrees with you in public agrees with you in private. 😏
   >
   > The wren on the fence has been chirping for a while. Must have good lungs.
   >
   > Only the things you choose without pressure define you. The rest is a facade. 🤥
   >
   > ⟦Flavored coffee is nice but can get old if you have it every day.⟧
   >
   > Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree and a crossvine in bloom. This is the recipe for a good Saturday. 🤗

7. **Takeaway:** The author says that sunshine, a cool breeze, doves, wrens, robins, squirrels, shade from an oak tree, and a blooming crossvine together make for a good Saturday.

   **Mask over the complete original note:**

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

**Shared mask over the complete original note:**

> You’ve had coffee. But have you had your coffee?”
> https://blossom.primal.net/1379b90996b8ecb2f4fdef6756fd61c4ab964fa19f9e1505950e10a4d97640dd.jpg
> ⟦Roasting your own beans means discovering a taste profile that’s uniquely
> yours. It’s a personal journey that no bag of pre-roasted coffee can
> replicate.⟧
>
> Sipping @ #coffeechain
>
> #HotTake ☕

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

### Analysis

The new pipeline did not merely clarify masks. It changed how many meanings it
claimed each note communicated and frequently reused the same source tokens.
The autonomy example is now represented twice, and those two vectors have
different cross-note neighborhoods. The pipeline emits and uses both;
it does not choose the better one.

## Detailed evidence D — Unsupported or distorted extractions

These are independent prompt or mask failures observed in the same run:

1. **Takeaway:** The post links to id Software’s Doom source-code repository
   and a separate Doom-related social-media post as references for the
   licensing update.

   **Mask over the complete original note:**

   > ⟦Doom 1 and 2 are now officially licensed under the #GPL, no longer
   > dual-licensed with the DSL :)⟧
   >
   > https://github.com/id-Software/DOOM/
   >
   > https://nitter.woodland.cafe/doom_txt/status/1747398603209883882
   >
   > #FOSS #OpenSource #Games #Gaming #GameNews

   **Problem:** The selected licensing sentence does not contain either link's
   meaning.

2. **Takeaway:** The post also links to a Hacker News discussion of the
   article.

   **Mask over the complete original note:**

   > Why a spritz of water before grinding coffee yields better results
   >
   > ⟦Comments⟧ ( https://news.ycombinator.com/item?id=38554310 )
   >
   > https://arstechnica.com/science/2023/12/study-why-a-spritz-of-water-before-grinding-coffee-yields-less-waste-tastier-espresso/

   **Problem:** `Comments` does not identify Hacker News or the article.

3. **Takeaway:** The author provides a link to the pypush project’s GitHub
   repository.

   **Mask over the complete original note:**

   > It's ready! #⟦pypush⟧ can now send and receive #iMessage, on any platform,
   > completely server-less and open-source! 🎉
   >
   > https://github.com/JJTech0130/pypush

   **Problem:** The project name does not establish that the omitted link is a
   GitHub repository.

4. **Takeaway:** Flexible cables have been installed as part of a greenhouse
   project shared by the author and others.

   **Mask over the complete original note:**

   > ⟦Flexicables installed for our ⟧geothermal solar powered ⟦greenhouse.⟧ The
   > greenhouse they have in Aliance Nebraska grows pineapple and dates and
   > citrus.
   > This will be the first steps to my non consumption based retirement.
   > https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

   **Problem:** `Flexicables` was rewritten as generic flexible cables.

The first three expose a mismatch between the prompts:

1. TPv3.81 can preserve meaning contributed by a URL.
2. MPv3.3 forbids selecting URLs.
3. The mask generator substitutes nearby source words that do not contain the
   omitted link's meaning.

Mechanical validation proves that each selected fragment occurs in the source
and appears in source order. It cannot prove that the fragments preserve the
takeaway's meaning.

## Aggregate measurements

The cross-note cosine distributions were:

| Measurement | TEv3.1 | TEv4.1 |
|---|---:|---:|
| Median | `0.0520` | `0.0490` |
| Mean | `0.0728` | `0.0701` |
| p95 | `0.3214` | `0.3169` |

These summaries barely changed, but they are not quality metrics. They cannot
establish or refute a semantic improvement.

## Final interpretation

TEv4.1 asked whether resolving ambiguous masks by adding enough exact source
text to reconstruct a takeaway would improve SSE's representation.

The controlled evidence showed two direction changes:

- `RET-NEW` was more similar than `RET-OLD` to one fixed solar vector and less
  similar than `RET-OLD` to one fixed retirement vector.
- `CTRL-NEW` was more similar than `CTRL-OLD` to two fixed software vectors and
  less similar than `CTRL-OLD` to one fixed government-control vector.

Separately, TEv4.1 generated more overlapping vectors and some
takeaways that its mask rules could not support.

Therefore, TEv4.1 does not provide evidence that making masks self-contained
improves independently searchable meanings. It also does not prove the opposite
for all notes: these are two controlled examples inside a 50-note diagnostic
set, not a population estimate.

The experiment does not reject SSE or multi-vector representations. It exposes
a narrower problem: exact source text needed to explain a reference can carry
additional subject matter that changes the vector's retrieval behavior.

The later atomic-subject direction was not established by TEv4.1. Both prompts
changed together, so this run also cannot attribute every effect specifically
to TPv3.81 or MPv3.3.

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

The [`../../../sse_multivector/baselines/communicated-meaning-tev4-1/README.md`](../../../sse_multivector/baselines/communicated-meaning-tev4-1/README.md)
preserves:

- the exact 50-note input and generation configurations;
- every accepted fresh-context response;
- all raw call logs, including the mechanically rejected attempt;
- the source-bound proposal and SSE worker request;
- the raw vectors and worker receipt;
- the complete pairwise cosine analysis and manifests.

The cross-run retirement control uses normalized vectors directly:

- `RET-OLD`: TEv3.1 ordinal 64;
- `RET-NEW`: TEv4.1 ordinal 101;
- fixed TEv3.1 retirement-packet candidate: ordinal 96;
- `RET-OLD` cosine: `0.3562099685`;
- `RET-NEW` cosine: `0.2455033805`.

Each cosine is the dot product of the fixed candidate row from TEv3.1's
`normalized-vectors.f32le` and the corresponding `RET-OLD` or `RET-NEW`
normalized target row. The solar control uses the same calculation with a
byte-identical candidate vector and yields `0.3690140084` and `0.6565306208`.
