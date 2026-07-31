# SSE Communicated-Meaning Failure Cases

## How to read this document

For every failure below, this document shows:

1. both complete notes seen by SSE;
2. every takeaway generated for each note;
3. the exact source fragment or fragments masked for every takeaway;
4. which two masked takeaways were compared;
5. their cosine, cross-note ranks, and the evidence supporting the diagnosis.

The compared-pair cosines are preserved at full recorded precision.
Neighborhood scores are rounded to six decimal places. Invisible trailing
whitespace in the complete notes is omitted; the wording and line breaks are
otherwise preserved.

The generated takeaway text was never given to SSE. SSE contextualized every
token using the complete note, then pooled only the token states selected by
the mask. Therefore, an unselected sentence can influence a selected token's
vector through the model's attention.

All inputs come from
[`communicated-meaning-full-proposal-v1.json`](../../../sse_multivector/communicated-meaning-full-proposal-v1.json),
and all scores and ranks come from the deterministically verified full-run
analysis preserved in
[`communicated-meaning-full-v1`](../../../sse_multivector/baselines/communicated-meaning-full-v1/).

## 1. Affogato versus a picky-eating child

**Cosine:** `0.548712659889978`

Each vector ranked the other first among all takeaways from other notes.

### Note A · Affogato

Note ID: `e1b9153e2006fb77384475cbe034cdb6224ffd06d1bdee46ca8fd6dfd867d407`

#### Complete note

```text
Wants a kick off during the day?  Affogato is easy to prepare and always available at your kitchen! #coolerstr @ #coffeestr https://image.nostr.build/ff4853ba4171c95546a55f17ac7e6712e8a4c34077f77c74c10fac32de518f45.jpg
```

#### Generated takeaways and masks

**Compared takeaway:** Affogato is an easy-to-prepare daytime pick-me-up that
can be made at home.

Mask:

```text
Wants a kick off during the day?  Affogato is easy to prepare and always available at your kitchen!
```

### Note B · Daughter, car seat, and eating

Note ID: `a530656af6c5fe8c1ee2ce8bdd33e9f7312334a68e1cdff7483c381a251a7ac4`

#### Complete note

```text
Another great sleepover with my daughter.
She finally weighs enough that I had to switch her car seat to forward facing.
So much easier to get her in & out if it now.
She’s such picky eater…
Gotta get her to start eating new foods somehow…
```

#### Generated takeaways and masks

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

### Measured neighborhood

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

### Observed facts

The affogato mask contains nearly all meaningful text in its note. The other
note's unselected text concerns a sleepover and a car seat. There is no shared
unselected subject that obviously explains the high score.

The selected passages share the broad domain of food and eating. The affogato
passage's more precise coffee neighbors received lower scores.

### Working interpretation

SSE appears to have emphasized the real broad relationship above the more
precise coffee relationships available in the corpus.

**Working diagnosis:** broad-domain or granularity collapse, rather than an
obvious context-leakage case. A single cosine does not distinguish sharing a
broad parent such as food from expressing the same fine meaning.

## 2. A repeatedly loud fan versus a long-chirping wren

**Cosine:** `0.4665483233395116`

The fan ranked the wren second among cross-note takeaways. The wren ranked the
fan first.

### Note A · BitAxe fan

Note ID: `84aba98daa2c1ce749395dc7c2249e5072c3c84d73573e37f61e15228fc0ae9d`

#### Complete note

```text
Has anyone replaced the fan on their BitAxe? If so, what did you use? I'd normally go with a Noctua but I hate that the NF-A4x20 is the stupid beige/brown colorway.

The stock fan is just getting too loud to deal with. I clean it and within a day or two, it's right back to being loud as hell.
```

#### Generated takeaways and masks

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

### Note B · Saturday thoughts

Note ID: `2c054d399715c118387a16ab9d3960d3dcb27cd8c3ee33cea2ac3336138a1b6a`

#### Complete note

```text
Annie's Saturday Morning Thoughts

Don't assume that everyone who agrees with you in public agrees with you in private. 😏

The wren on the fence has been chirping for a while. Must have good lungs.

Only the things you choose without pressure define you. The rest is a facade. 🤥

Flavored coffee is nice but can get old if you have it every day.

Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree and a crossvine in bloom. This is the recipe for a good Saturday. 🤗
```

#### Generated takeaways and masks

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

### Measured neighborhood

The fan vector correctly ranked the Avalon/Bitaxe noise comparison first at
`0.672400`, followed by the wren at `0.466548`.

The wren vector ranked:

1. the repeatedly loud fan: `0.466548`;
2. the Avalon/Bitaxe noise comparison: `0.428812`;
3. Aeropress taste improvement: `0.273537`.

### Observed facts

The complete notes otherwise concern unrelated domains. Their selected
passages, however, both describe a sound-producing thing continuing over time:
the fan becomes loud again within days, while the wren has been chirping for a
while and appears to have strong lungs.

### Working interpretation

SSE appears to have captured an acoustic-and-duration analogy. That analogy is
real on one semantic axis but wrong as a fine communicated-meaning neighbor.

**Working diagnosis:** relational or attribute similarity at the wrong level,
rather than primarily context leakage. Cosine exposes closeness but cannot say
whether the closeness comes from subject identity, a shared attribute, or an
analogy.

## 3. “They want to control everything” versus automatic backups

**Cosine:** `0.41754547551075744`

Each vector ranked the other first among all takeaways from other notes.

### Note A · Proprietary systems and surveillance

Note ID: `7adcfe1ab26f770b6ff5968fda1d6ef7d5a0fe63a946af714d44178a3470712e`

#### Complete note

```text
they want to control everything..
..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty
```

#### Generated takeaways and masks

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

### Note B · Molly secure-messaging features

Note ID: `aa269973db710939d2cdc6f8582c94b2f0e5f472f3e07b8f9e684140bd341376`

#### Complete note

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

#### Generated takeaways and masks

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

### Measured neighborhood

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

### Observed facts

The selected fragments share no substantive wording and communicate apparently
different things. Their complete notes do share substantial unselected
context: both discuss open-source, security-oriented software. The first note
additionally discusses privacy and surveillance.

The “control everything” fragment is also not self-contained. Its pronoun and
object acquire meaning only from the proprietary-OS and surveillance text
around it.

### Working interpretation

The score is consistent with SSE carrying the broader source-note domain into
the selected vector strongly enough that an unrelated Molly feature becomes
its nearest neighbor. A span-only ablation is required to establish whether
that surrounding context caused the score.

**Working diagnosis:** the strongest context-leakage candidate among these
four failures, compounded by an underspecified selected fragment. Context
leakage remains unproven.

## 4. Timed miner control versus automatic app locking

**Cosine:** `0.404047938171206`

The miner-control vector ranked the app-lock vector first among cross-note
takeaways. The app-lock vector ranked miner control second, behind Ledger
interaction tracking at `0.448268`.

### Note A · Miner control

Note ID: `7e2e4e93cf8f88476ffe5fe2d4f6c89e6af1efed33de7e18802d6cbcee0f7a13`

#### Complete note

```text
This week I just let the miner running to keep temperatures for a minimum and save the #statistics.
I want to find the best way how to run the miner. So far it only starts when it is below a specific temperature (with a day/night mode)

Meanwhile I do a bit of programming to start up the miner when I have #solar #energy  left. And to have statistics how much solar energy is used for the miner.

Anyhow in the winter days almost everything is required to heat the house so it won’t be much anyhow.

#orangery #greenhouse   #grownostr #miner #bitcoin #nostr #btc
```

#### Generated takeaways and masks

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

### Note B · Molly secure-messaging features

Note ID: `aa269973db710939d2cdc6f8582c94b2f0e5f472f3e07b8f9e684140bd341376`

#### Complete note

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

#### Generated takeaways and masks

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

### Measured neighborhood

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

### Observed facts

The selected fragments themselves share an abstract relation: a device
automatically changes state when a time or condition threshold is met. The
miner starts below a temperature threshold and varies by day/night mode; the
app locks after a period of inactivity.

The full notes otherwise concern different domains. The app-lock vector's
nearest result was Ledger tracking, which is consistent with—but does not
prove—retained app/privacy context.

### Working interpretation

The functional similarity between the selected passages is sufficient to
explain much of their closeness without relying on context leakage.

**Working diagnosis:** primarily relational or functional-structure similarity
at the wrong semantic level, with possible secondary context influence. A
scalar cosine does not distinguish “these implement analogous conditional
behavior” from “these communicate the same subject.”

## Combined conclusion

The four pairs are not all best explained by the same mechanism:

1. **Broad-domain collapse:** affogato versus picky eating.
2. **Attribute or analogy collapse:** persistent fan noise versus persistent
   bird sound.
3. **Leading context-leakage candidate:** control rhetoric versus automatic
   backups.
4. **Functional-relation collapse:** conditional miner control versus
   conditional app locking.

The third pair is the one most consistent with surrounding-context influence,
but the current run cannot prove that cause. Removing complete-note context
may reduce that failure, but it would not necessarily fix the other three.
Those expose a more general limitation: one cosine value cannot identify which
semantic axis or level of specificity produced the similarity.
