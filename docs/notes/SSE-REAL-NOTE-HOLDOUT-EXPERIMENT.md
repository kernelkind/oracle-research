# Real-note holdout mask experiment

## Question

Do manually selected atomic-subject masks preserve the expected local semantic relationship in previously unused real Nostr notes?

## Setup

The experiment used 12 real notes in four comparisons. Each comparison contained:

- A and B: masks expected to represent the same narrow subject.
- C: a related mask expected to represent a different subject.

The notes, masks, and expected result were approved before any of their SSE vectors were generated. None of the 12 note IDs appeared in the frozen 1,000-note sample or the prior SSE experiment records checked during selection.

Only these 12 vectors were encoded. A comparison passed when:

`cosine(A, B) > cosine(A, C)` and `cosine(A, B) > cosine(B, C)`

All vectors used the frozen Sentence-T5-base SSE checkpoint with SHA-256 `ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d`.

## 1) Camera bird feeders

### Description

A and B concern bird feeders with cameras. C concerns wild eagles returning to England.

### Hypothesis

The A–B cosine will be higher than both control cosines.

### A

> The Smart Bird Feeders Everyone’s Talking About (and Actually Buying) (2026)
>
> These ⟦bird feeders come with cameras and connected apps⟧ to let you see and learn about the birds in your neighborhood.
>
> https://www.wired.com/story/best-smart-bird-feeders/

### B

> My wife got a ⟦camera bird feeder⟧, and I have to say, I do not mind getting these notifications.
>
> https://mograph.social/system/media_attachments/files/116/127/500/431/041/174/original/b26c7f899642eeaf.png

### C

> ⟦Golden eagles are returning to English skies for the first time in centuries.⟧ Sometimes things that seemed gone for good find their way back. If you're in a season that feels like everything has disappeared — your energy, your hope, your sense of who you are — you don't have to rush the return. Even the eagles needed time, and the right winds. The sky is still there. ♡

### Result

| Pair | Cosine |
|---|---:|
| A–B | `0.568817` |
| A–C | `-0.058361` |
| B–C | `0.171170` |

The hypothesis passed. A–B exceeded both controls by at least `0.397646`.

## 2) Moving from Windows to Linux

### Description

A and B concern adopting Linux instead of Windows. C concerns running Windows applications on Linux while retaining the Windows software.

This was deliberately a hard comparison. Before encoding, we agreed that a pass would be strong evidence, but a failure would not be definitive because the frozen model might not know this technical distinction well enough.

### Hypothesis

The A–B cosine will be higher than both control cosines.

### A

> ⟦Windows 12 could be the tipping point that finally pushes you to Linux⟧ - here's why
> https://www.zdnet.com/article/windows-12-rumors-linux-migration/

### B

> Hey nostr:nprofile1qyvhwumn8ghj7un9d3shjtnyd9mxjmn99emxjer9duhsqgyt29lcuuq8ql0afk8fwn6k6xphzxtc6u3sxp3sxz3kqjge86n5ty8j9k4f since you seem up on this stuff I'm interested in potentially ⟦getting a home Linux mini-PC⟧... do they make those pre-installed with Linux or does it make more sense to just get one off the shelf and ⟦scoop out the Windows slop⟧ myself?

### C

> ⟦How to run Windows apps on Linux with Wine⟧ - it's easy
> https://www.zdnet.com/article/how-to-run-windows-apps-on-linux-with-wine/

### Result

| Pair | Cosine |
|---|---:|
| A–B | `0.665970` |
| A–C | `0.580301` |
| B–C | `0.701669` |

The hypothesis failed. A was closer to B than to C, but B was closer to C than to A by `0.035699`.

This comparison does not support SSE distinguishing Linux adoption from Windows-software compatibility. It does not identify whether the cause was mask behavior, limited model knowledge, or another property of the frozen encoder.

## 3) Explicit air-fryer masks

### Description

A and B explicitly mask `air fryer`. C masks `Olive Oil Dispenser`, while unmasked text later in C mentions an air-fryer toaster oven.

This was an easy control. A failure would show a fundamental context-isolation problem. A pass provides only weak evidence by itself.

### Hypothesis

The A–B cosine will be higher than both control cosines.

### A

> ⟦air fryer⟧ kebab sandwiches have been proven a success

### B

> Cooking Meatloaf In The ⟦Air Fryer⟧ Will Give You The Best Texture Yet https://www.diningandcooking.com/2534044/cooking-meatloaf-in-the-air-fryer-will-give-you-the-best-texture-yet/ #AirFryer #ClassicMeatloaf #Cooking #DavidMiller #MeatloafRecipe #PerWitchel #TastingTable #VioletWitchel
>
> https://media.vive.im/media_attachments/files/116/148/355/361/148/257/original/e28f5e646d3fa45a.jpeg

### C

> This ⟦Olive Oil Dispenser⟧ Is the ‘Rare Perfect Product’
>
> One of the pantry ingredients I reach for most is olive oil. I use it to roast chicken or make crisp French fries in my air fryer toaster oven, crank out batches of popcorn in my stovetop popcorn maker, and fry slices of sweet peppers in my stainless steel skillet…
> #dining #cooking #diet #food #MediterraneanOliveOil #OliveOil #Mediterranean #Olive
> https://www.diningandcooking.com/2323894/this-olive-oil-dispenser-is-the-rare-perfect-product/
>
> https://media.vive.im/media_attachments/files/115/344/843/075/050/924/original/81e3277f5dc4da86.jpg

### Result

| Pair | Cosine |
|---|---:|
| A–B | `0.882650` |
| A–C | `0.196801` |
| B–C | `0.103369` |

The hypothesis passed. A–B exceeded both controls by at least `0.685849`.

## 4) Off-grid mesh networking

### Description

A and B concern off-grid mesh networking. B also contains unmasked solar language. C masks a solar-power headline without mesh networking.

### Hypothesis

The A–B cosine will be higher than both control cosines.

### A

> I love what this guy @ DataSlayer is doing with Reticulum—an open-source protocol that could allow anyone to ⟦build networks without relying on traditional internet infrastructure⟧.
>
> “In this video, I start with a simple setup inside my house and begin pushing the limits—testing communication across rooms, neighborhoods, and beyond ⟦using WiFi HaLow and mesh networking⟧. The goal is simple: see if it’s possible to send real messages across distance without depending on ISPs, centralized servers, or the internet as we know it.”
>
> https://youtu.be/6ibr7gm8uVA?si=ph7K75ZnjRr7BTAH
>
> #reticulum #meshnetworking #technology #communication

### B

> Solar powered ⟦mesh networks⟧ are the new atomic reactors, powering communities away from corporate surveillance. #MeshTheResistance
>
> ⟦Decentralized off-grid computing⟧ is key to protecting privacy and fostering autonomy. Imagine a world where no single corporation controls your data.
>
> MeshTheResistance OffGridPower SolarNetworks

### C

> ⟦US Builders Are Still Pushing The Solar Power Envelope⟧
>
> US Builders Are Still Pushing The Solar Power Envelope
>
> Sector: Real Infrastructure | Confidence: 98%
> Source: https://www.reddit.com/r/energy/comments/1rm69aa/us_builders_are_still_pushing_the_solar_power/
>
> #FIRE #Circle #infrastructure

### Result

| Pair | Cosine |
|---|---:|
| A–B | `0.791757` |
| A–C | `0.094671` |
| B–C | `0.256172` |

The hypothesis passed. A–B exceeded both controls by at least `0.535586`.

## Findings

Three of the four comparisons passed their predeclared ordering test.

The passing comparisons show that SSE can expose the expected narrow semantic relationship in some previously unused real notes, including notes with different wording, multiple mask fragments, and potentially distracting text outside the mask.

The failed Windows/Linux comparison shows that this behavior is not yet reliable for nearby subjects. Its result cannot distinguish a general SSE limitation from insufficient technical knowledge in the frozen model.

This experiment therefore supports continuing to test SSE mask fidelity, but does not establish that the necessary semantic structure is reliable across real Nostr content.
