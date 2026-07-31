# Four Bad SSE Matches

This document puts all the evidence for four bad matches in one place. Each
case includes:

- both full notes;
- every takeaway produced by the agent;
- the exact mask used for each takeaway;
- the two takeaways being compared;
- their cosine scores and ranks;
- what the evidence does and does not show.

The main cosine for each pair is shown at full precision. Other scores are
rounded to six decimal places. Invisible trailing spaces are omitted from the
notes; their wording and line breaks are unchanged.

SSE never saw the takeaway text. It encoded the full note, then pooled the
token states selected by the mask. Because it encoded the full note first,
text outside the mask could still affect the resulting vector.

- Inputs: [`communicated-meaning-full-proposal-v1.json`](../../../sse_multivector/communicated-meaning-full-proposal-v1.json)
- Results: [`communicated-meaning-full-v1`](../../../sse_multivector/baselines/communicated-meaning-full-v1/)

## 1. Affogato versus a picky-eating child

Cosine `0.548712659889978` · A → B rank 1 · B → A rank 1

**A — Affogato** · `e1b9153e2006fb77384475cbe034cdb6224ffd06d1bdee46ca8fd6dfd867d407`

```text
Wants a kick off during the day?  Affogato is easy to prepare and always available at your kitchen! #coolerstr @ #coffeestr https://image.nostr.build/ff4853ba4171c95546a55f17ac7e6712e8a4c34077f77c74c10fac32de518f45.jpg
```

Takeaways and masks:

**Compared takeaway:** Affogato is an easy-to-prepare daytime pick-me-up that
can be made at home.

Mask:

```text
Wants a kick off during the day?  Affogato is easy to prepare and always available at your kitchen!
```

**B — Daughter, car seat, and eating** · `a530656af6c5fe8c1ee2ce8bdd33e9f7312334a68e1cdff7483c381a251a7ac4`

```text
Another great sleepover with my daughter.
She finally weighs enough that I had to switch her car seat to forward facing.
So much easier to get her in & out if it now.
She’s such picky eater…
Gotta get her to start eating new foods somehow…
```

Takeaways and masks:

**Takeaway:** The author had another great sleepover with their daughter.

Mask:

```text
Another great sleepover with my daughter.
```

**Takeaway:** The author's daughter now weighs enough for a forward-facing car
seat, which makes getting her in and out easier.

Mask fragments:

```text
She finally weighs enough that I had to switch her car seat to forward facing.
```

```text
So much easier to get her in & out if it now.
```

**Compared takeaway:** The author's daughter is a picky eater, and the author
wants to get her to try new foods.

Mask fragments:

```text
She’s such picky eater…
```

```text
Gotta get her to start eating new foods somehow…
```

**Closest results**

The affogato vector's closest cross-note results were:

1. picky eating: `0.548713`;
2. flavored coffee becoming tiresome: `0.508565`;
3. roasting beans for a personal flavor profile: `0.490364`;
4. eating ice cream from a plate: `0.452030`.

The picky-eating vector's closest cross-note results were:

1. affogato: `0.548713`;
2. eating ice cream from a plate: `0.464914`;
3. flavored coffee becoming tiresome: `0.430594`;
4. roasting beans for a personal flavor profile: `0.428911`.

**What we know**

The affogato mask contains all prose in the note; it excludes only the hashtags
and image URL. The picky-eating mask excludes the sleepover and car-seat
passages. The two masks both concern food and eating. The affogato vector's
more precise coffee matches received lower scores.

**What it likely means**

SSE probably matched these because both concern food and eating. That is a
real connection, but it is too broad: the coffee notes should have ranked
higher. This does not look like context leakage. It shows that cosine alone
cannot distinguish a broad shared category from the same precise meaning.

## 2. A repeatedly loud fan versus a long-chirping wren

Cosine `0.4665483233395116` · A → B rank 2 · B → A rank 1

**A — BitAxe fan** · `84aba98daa2c1ce749395dc7c2249e5072c3c84d73573e37f61e15228fc0ae9d`

```text
Has anyone replaced the fan on their BitAxe? If so, what did you use? I'd normally go with a Noctua but I hate that the NF-A4x20 is the stupid beige/brown colorway.

The stock fan is just getting too loud to deal with. I clean it and within a day or two, it's right back to being loud as hell.
```

Takeaways and masks:

**Takeaway:** The user is seeking recommendations from people who have
replaced a BitAxe fan.

Mask:

```text
Has anyone replaced the fan on their BitAxe? If so, what did you use?
```

**Takeaway:** They would normally choose a Noctua fan but dislike the
NF-A4x20's beige-and-brown color scheme.

Mask:

```text
I'd normally go with a Noctua but I hate that the NF-A4x20 is the stupid beige/brown colorway.
```

**Compared takeaway:** The stock fan becomes intolerably loud again within a
day or two of cleaning.

Mask:

```text
The stock fan is just getting too loud to deal with. I clean it and within a day or two, it's right back to being loud as hell.
```

**B — Saturday thoughts** · `2c054d399715c118387a16ab9d3960d3dcb27cd8c3ee33cea2ac3336138a1b6a`

```text
Annie's Saturday Morning Thoughts

Don't assume that everyone who agrees with you in public agrees with you in private. 😏

The wren on the fence has been chirping for a while. Must have good lungs.

Only the things you choose without pressure define you. The rest is a facade. 🤥

Flavored coffee is nice but can get old if you have it every day.

Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree and a crossvine in bloom. This is the recipe for a good Saturday. 🤗
```

Takeaways and masks:

**Takeaway:** Public agreement does not necessarily mean private agreement.

Mask:

```text
Don't assume that everyone who agrees with you in public agrees with you in private.
```

**Compared takeaway:** A wren has been chirping on the fence for a long time
and seems to have strong lungs.

Mask fragments:

```text
The wren on the fence has been chirping for a while.
```

```text
Must have good lungs.
```

**Takeaway:** Only choices made without pressure define a person; the rest is
a facade.

Mask fragments:

```text
Only the things you choose without pressure define you.
```

```text
The rest is a facade.
```

**Takeaway:** Flavored coffee is enjoyable but becomes tiresome when consumed
every day.

Mask:

```text
Flavored coffee is nice but can get old if you have it every day.
```

**Takeaway:** Sunshine, a cool breeze, wildlife, tree shade, and blooming
crossvine make for a good Saturday.

Mask fragments:

```text
Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree and a crossvine in bloom.
```

```text
This is the recipe for a good Saturday.
```

**Closest results**

The fan vector correctly ranked the Avalon/Bitaxe noise comparison first at
`0.672400`, followed by the wren at `0.466548`.

The wren vector ranked:

1. the repeatedly loud fan: `0.466548`;
2. the Avalon/Bitaxe noise comparison: `0.428812`;
3. Aeropress taste improvement: `0.273537`.

**What we know**

Outside the masks, the first note discusses BitAxe hardware and the second
contains several unrelated Saturday thoughts. The masks both describe a sound
that persists or returns over time: the fan becomes loud again within days,
while the wren has been chirping for a while.

**What it likely means**

SSE probably matched the shared pattern of a sound continuing or recurring
over time. That relation is real, but the takeaways are about different things.
This does not mainly look like context leakage. It shows that cosine can favor
a shared attribute or analogy over the actual subject.

## 3. “They want to control everything” versus automatic backups

Cosine `0.41754547551075744` · A → B rank 1 · B → A rank 1

**A — Proprietary systems and surveillance** · `7adcfe1ab26f770b6ff5968fda1d6ef7d5a0fe63a946af714d44178a3470712e`

```text
they want to control everything..
..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty
```

Takeaways and masks:

**Compared takeaway:** Unspecified actors want to control everything.

Mask:

```text
they want to control everything
```

**Takeaway:** The author believes Nostr nsec keys are unsafe on proprietary
operating systems because their telemetry and APIs can access everything on a
device.

Mask fragments:

```text
if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture
```

```text
all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices
```

**Takeaway:** The author plans to leave iOS, likely for GrapheneOS, and already
minimizes phone use.

Mask fragments:

```text
i'm still on iOS phone-wise, but my days are numbered with that
```

```text
likely moving to #GrapheneOS (although i already try to use my phone as little as possible)
```

**Takeaway:** The author has already switched to Linux on computers.

Mask:

```text
i've already switched to #Linux computer-wise
```

**Takeaway:** The author considers free and open-source software the only way
to retain sovereignty in a technology surveillance state.

Mask:

```text
free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty
```

**B — Molly secure-messaging features** · `aa269973db710939d2cdc6f8582c94b2f0e5f472f3e07b8f9e684140bd341376`

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

Takeaways and masks:

**Takeaway:** The user plans to regularly share useful open-source technology.

Mask:

```text
I'm thinking I'll regularly post about open source tech I find useful.
```

**Takeaway:** Molly is a Signal fork designed for greater security.

Mask:

```text
Molly is a fork of Signal, made to be more secure.
```

**Takeaway:** Molly contains no proprietary code or binary blobs.

Mask:

```text
No proprietary blobs/code.
```

**Takeaway:** Molly encrypts messages using a passphrase.

Mask:

```text
Molly protects your messages with passphrase encryption.
```

**Takeaway:** Molly can automatically lock after a configured period of
inactivity.

Mask:

```text
The app can lock down automatically after a set time of not being opened.
```

**Takeaway:** Molly securely removes sensitive data from RAM.

Mask:

```text
Molly, "Securely shreds sensitive data from RAM."
```

**Compared takeaway:** Molly supports automatic backups.

Mask:

```text
You can create automatic backups
```

**Takeaway:** Molly can route its connection through Tor using Orbot as an app
proxy.

Mask:

```text
It even supports setting an app proxy through Tor via Orbot.
```

**Takeaway:** Molly is available through its own F-Droid repository.

Mask:

```text
Available on their own Fdroid repo:
https://molly.im/
```

**Closest results**

The “control everything” vector's closest cross-note results were:

1. automatic backups: `0.417545`;
2. open-source pypush: `0.400475`;
3. an almost entirely FOSS software stack: `0.376306`;
4. Ledger interaction tracking: `0.366851`;
5. cookie dark patterns: `0.349440`.

The automatic-backup vector ranked:

1. “control everything”: `0.417545`;
2. a non-consumption-based retirement: `0.339194`;
3. Ledger interaction tracking: `0.314357`;
4. programming a miner around surplus solar power: `0.266802`.

**What we know**

One mask says unspecified people want control. The other says Molly can make
automatic backups. They share no meaningful wording and say different things.
Their full notes both concern open-source, security-oriented software. The
first also discusses privacy and surveillance.

The surrounding OS and surveillance text suggests what “they” and “everything”
refer to, but never identifies the actors.

**What it likely means**

This is the clearest case where the rest of the note may have affected the
masked vector. The fragment “they want to control everything” also depends on
the surrounding text to explain who “they” are and what they control. We still
need a span-only run to prove whether that surrounding context caused the
match.

## 4. Timed miner control versus automatic app locking

Cosine `0.404047938171206` · A → B rank 1 · B → A rank 2

**A — Miner control** · `7e2e4e93cf8f88476ffe5fe2d4f6c89e6af1efed33de7e18802d6cbcee0f7a13`

```text
This week I just let the miner running to keep temperatures for a minimum and save the #statistics.
I want to find the best way how to run the miner. So far it only starts when it is below a specific temperature (with a day/night mode)

Meanwhile I do a bit of programming to start up the miner when I have #solar #energy  left. And to have statistics how much solar energy is used for the miner.

Anyhow in the winter days almost everything is required to heat the house so it won’t be much anyhow.

#orangery #greenhouse   #grownostr #miner #bitcoin #nostr #btc
```

Takeaways and masks:

**Takeaway:** The user left the miner running this week to maintain a minimum
temperature and record statistics.

Mask:

```text
This week I just let the miner running to keep temperatures for a minimum and save the #statistics.
```

**Compared takeaway:** They want to find the best way to operate the miner,
which currently starts below a set temperature using day and night modes.

Mask:

```text
I want to find the best way how to run the miner. So far it only starts when it is below a specific temperature (with a day/night mode)
```

**Takeaway:** They are programming the miner to start when surplus solar
energy is available and to track how much solar energy it consumes.

Mask:

```text
Meanwhile I do a bit of programming to start up the miner when I have #solar #energy  left. And to have statistics how much solar energy is used for the miner.
```

**Takeaway:** Winter household heating consumes nearly all available energy,
leaving little surplus for mining.

Mask:

```text
Anyhow in the winter days almost everything is required to heat the house so it won’t be much anyhow.
```

**B — Molly secure-messaging features** · `aa269973db710939d2cdc6f8582c94b2f0e5f472f3e07b8f9e684140bd341376`

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

Takeaways and masks:

**Takeaway:** The user plans to regularly share useful open-source technology.

Mask:

```text
I'm thinking I'll regularly post about open source tech I find useful.
```

**Takeaway:** Molly is a Signal fork designed for greater security.

Mask:

```text
Molly is a fork of Signal, made to be more secure.
```

**Takeaway:** Molly contains no proprietary code or binary blobs.

Mask:

```text
No proprietary blobs/code.
```

**Takeaway:** Molly encrypts messages using a passphrase.

Mask:

```text
Molly protects your messages with passphrase encryption.
```

**Compared takeaway:** Molly can automatically lock after a configured period
of inactivity.

Mask:

```text
The app can lock down automatically after a set time of not being opened.
```

**Takeaway:** Molly securely removes sensitive data from RAM.

Mask:

```text
Molly, "Securely shreds sensitive data from RAM."
```

**Takeaway:** Molly supports automatic backups.

Mask:

```text
You can create automatic backups
```

**Takeaway:** Molly can route its connection through Tor using Orbot as an app
proxy.

Mask:

```text
It even supports setting an app proxy through Tor via Orbot.
```

**Takeaway:** Molly is available through its own F-Droid repository.

Mask:

```text
Available on their own Fdroid repo:
https://molly.im/
```

**Closest results**

The miner-control vector's closest cross-note results were:

1. automatic app locking: `0.404048`;
2. preparing fourteen solar panels as a weekend project: `0.370182`;
3. future solar generation: `0.327629`;
4. recurring BitAxe fan noise: `0.325734`;
5. using solar panels to charge a car or run a miner: `0.318257`.

The automatic-lock vector ranked:

1. Ledger interaction tracking: `0.448268`;
2. miner temperature/day-night control: `0.404048`;
3. leaving a miner running to maintain temperature: `0.383133`;
4. finishing a book in one night if work allowed: `0.359352`;
5. recurring BitAxe fan noise after days: `0.307509`.

**What we know**

Both masks describe automatic behavior triggered by a condition. The miner
starts below a temperature threshold and varies by day/night mode. The app
locks after a period of inactivity.

Outside these masks, the two notes discuss different subjects. The app-lock
vector's nearest result was Ledger tracking. That could reflect app/privacy
context from the Molly note, but this result alone does not prove it.

**What it likely means**

SSE probably matched both as automatic device behavior triggered by time or a
condition. That is a real structural similarity, but not the same takeaway.
The rest of the Molly note may also influence its vector, but we do not need
context leakage to explain this match.

## What these examples show

These do not look like four instances of one bug:

1. Affogato versus picky eating matched on the broad idea of food.
2. Fan noise versus a chirping wren matched on recurring sound.
3. “Control everything” versus backups may reflect surrounding-note context.
4. Miner control versus app locking matched on conditional automation.

Only the third case gives a clear reason to suspect that text outside the mask
affected the vector, and even that is not proven yet. Removing full-note
context might fix it without fixing the other three.

The broader problem is that cosine says how strongly two vectors resemble each
other. It does not say which feature made them similar, or whether that
similarity is precise enough for our use.
