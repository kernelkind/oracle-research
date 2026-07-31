# Four SSE Failures

`⟦...⟧` marks the exact text selected by the mask. The rest of each note was
still visible to SSE as context. The agent-generated takeaway explains what
the mask was meant to represent; SSE did not receive that takeaway.

Scores are rounded to four decimal places.

## 1. Affogato matched picky eating

Cosine `0.5487` · each was the other's closest takeaway from another note

**A takeaway:** Affogato is an easy-to-prepare daytime pick-me-up that can be
made at home.

> ⟦Wants a kick off during the day?  Affogato is easy to prepare and always available at your kitchen!⟧ #coolerstr @ #coffeestr https://image.nostr.build/ff4853ba4171c95546a55f17ac7e6712e8a4c34077f77c74c10fac32de518f45.jpg

**B takeaway:** The author's daughter is a picky eater, and the author wants
to get her to try new foods.

> Another great sleepover with my daughter.
> She finally weighs enough that I had to switch her car seat to forward facing.
> So much easier to get her in & out if it now.
> ⟦She’s such picky eater…⟧
> ⟦Gotta get her to start eating new foods somehow…⟧

**What happened:** SSE matched the broad idea of food and eating.

**Why it is wrong:** The affogato takeaway is specifically about coffee. Two
actual coffee takeaways scored `0.5086` and `0.4904`, below picky eating.

**Likely problem:** The model favored a broad category over the precise
meaning. This does not look like context leakage.

## 2. A loud fan matched a chirping wren

Cosine `0.4665` · fan → wren rank 2 · wren → fan rank 1

**A takeaway:** The stock fan becomes intolerably loud again within a day or
two of cleaning.

> Has anyone replaced the fan on their BitAxe? If so, what did you use? I'd normally go with a Noctua but I hate that the NF-A4x20 is the stupid beige/brown colorway.
>
> ⟦The stock fan is just getting too loud to deal with. I clean it and within a day or two, it's right back to being loud as hell.⟧

**B takeaway:** A wren has been chirping on the fence for a long time and seems
to have strong lungs.

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

**What happened:** Both masks describe a sound that persists or returns over
time.

**Why it is wrong:** A recurring fan noise and a bird chirping are not the same
takeaway. The fan did correctly match another mining-device noise takeaway at
`0.6724`, but the wren still became its second match and ranked the fan first.

**Likely problem:** The model favored a shared attribute—persistent sound—over
what each takeaway was actually about.

## 3. “They want to control everything” matched automatic backups

Cosine `0.4175` · each was the other's closest takeaway from another note

**A takeaway:** Unspecified actors want to control everything.

> ⟦they want to control everything⟧..
> ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

**B takeaway:** Molly supports automatic backups.

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

**What happened:** The two masks say different things and share no meaningful
wording. Their full notes both discuss open-source, security-oriented software.

**Why it is wrong:** Wanting control and supporting backups are unrelated
takeaways.

**Likely problem:** Context from the rest of each note may have affected the
masked vectors. The first mask is also vague: its surrounding text suggests
what “they” and “everything” refer to without identifying the actors. This is
the clearest context-leakage candidate, but only a span-only run can confirm it.

## 4. Miner control matched automatic app locking

Cosine `0.4040` · miner → app rank 1 · app → miner rank 2

**A takeaway:** They want to find the best way to operate the miner, which
currently starts below a set temperature using day and night modes.

> This week I just let the miner running to keep temperatures for a minimum and save the #statistics.
> ⟦I want to find the best way how to run the miner. So far it only starts when it is below a specific temperature (with a day/night mode)⟧
>
> Meanwhile I do a bit of programming to start up the miner when I have #solar #energy  left. And to have statistics how much solar energy is used for the miner.
>
> Anyhow in the winter days almost everything is required to heat the house so it won’t be much anyhow.
>
> #orangery #greenhouse   #grownostr #miner #bitcoin #nostr #btc

**B takeaway:** Molly can automatically lock after a configured period of
inactivity.

> I'm thinking I'll regularly post about open source tech I find useful.
>
> Molly is a fork of Signal, made to be more secure.
>
> Some of it's features include:
> No proprietary blobs/code.
> Molly protects your messages with passphrase encryption.
> ⟦The app can lock down automatically after a set time of not being opened.⟧
> Molly, "Securely shreds sensitive data from RAM."
> You can create automatic backups
> It even supports setting an app proxy through Tor via Orbot.
>
> Available on their own Fdroid repo:
> https://molly.im/

**What happened:** Both masks describe a device automatically changing state
when a condition is met.

**Why it is wrong:** Temperature-based miner operation and inactivity-based
app locking are not the same takeaway.

**Likely problem:** The model favored a shared trigger/action pattern over the
actual content. Context from the Molly note may also matter, but it is not
needed to explain this match.

## Bottom line

These are not four copies of one bug:

- Case 1 matched a broad category.
- Case 2 matched a shared attribute.
- Case 3 may have matched surrounding-note context.
- Case 4 matched a shared functional pattern.

Only case 3 strongly suggests context leakage. The other cases show a broader
problem: cosine measures how similar two vectors are, but not *why* they are
similar or whether the similarity is precise enough for our use.

Raw inputs:
[`communicated-meaning-full-proposal-v1.json`](../../../sse_multivector/communicated-meaning-full-proposal-v1.json) ·
raw results:
[`communicated-meaning-full-v1`](../../../sse_multivector/baselines/communicated-meaning-full-v1/)
