# SSE Similarity Analysis

`⟦...⟧` marks the exact text selected by the mask. The rest of each note was
still visible to SSE as context. The agent-generated takeaway explains what
the mask was meant to represent; SSE did not receive that takeaway.

This analysis uses the criterion required by the proposed segmentation system:
a match is useful when the selected spans share a real subject that a later
labeling step could name. The two takeaways do not need to be interchangeable
or come from the same application domain. A pairwise cosine also does not prove
that the complete corpus would place both vectors in the same segment.

Scores are rounded to four decimal places.

## 1. Affogato matched picky eating — valid signal

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

**Assessment:** This is not a failure. Affogato is food, and the other passage
is about getting someone to try new foods. Their shared subject is broad but
real. Two more specific coffee matches scored `0.5086` and `0.4904`; the later
segmentation step, using the complete corpus, must determine whether these
signals belong in the same final region.

## 2. A loud fan matched a chirping wren — success

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

**Assessment:** This is useful cross-domain signal. A later labeling step could
name their common subject “persistent sounds.” “Annoying sounds” would be too
strong because the wren passage does not express annoyance. The fan also
matched another mining-device noise takeaway more strongly at `0.6724`.

## 3. “They want to control everything” matched automatic backups — failure

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

**Assessment:** The selected spans have no defensible common subject. Their
full notes share software and security context, which may have affected the
vectors. Only a span-only run can confirm that explanation.

**Separate mask problem:** “They” and “everything” cannot be interpreted from
the selected span alone. The surrounding note suggests their meaning without
identifying the actors.

## 4. Miner control matched automatic app locking — success

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

**Assessment:** This is useful cross-domain signal. “Condition-triggered
automatic device behavior” is a defensible common subject. The fact that one
device is a miner and the other is an app does not make the relationship
wrong.

## 5. An autonomy vector developed a coffee-heavy neighborhood — failure

Cosine `0.4347` · autonomy → coffee rank 2 · coffee → autonomy rank 7

**A takeaway:** Only choices made without pressure define a person; the rest
is a facade.

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

**B takeaway:** Roasting your own coffee beans creates a uniquely personal
flavor profile that pre-roasted coffee cannot replicate.

> You’ve had coffee. But have you had your coffee?”
> https://blossom.primal.net/1379b90996b8ecb2f4fdef6756fd61c4ab964fa19f9e1505950e10a4d97640dd.jpg
> ⟦Roasting your own beans means discovering a taste profile that’s uniquely yours. It’s a personal journey that no bag of pre-roasted coffee can replicate.⟧
>
> Sipping  @ #coffeechain
>
> #HotTake ☕

**What happened:** The autonomy mask contains nothing about coffee, but three
of its five closest takeaways from other notes were about coffee:

1. fear of books changing someone's thinking: `0.4349`;
2. roasting coffee for a personal flavor profile: `0.4347`;
3. decaf drinkers valuing flavor and experience: `0.3875`;
4. Molly containing no proprietary code: `0.3851`;
5. Tim Hortons coffee not being premium: `0.3277`.

**Assessment:** The first result—fear of books changing someone's thinking—is
a valid neighbor. The coffee-roasting result also has a possible cross-domain
connection through personal authenticity or self-directed choice, so that pair
alone does not prove failure.

The corpus has few close autonomy examples, but it is not empty. Other
plausible candidates include deceptive cookie controls (`0.2842`), FOSS
sovereignty (`0.2368`), and unspecified actors seeking control (`0.1945`).
Sparsity and corpus composition may worsen the ranking. Even so, the
combination of three coffee results and an unmasked coffee sentence in the
source note is suspicious. The Tim Hortons result has no defensible autonomy
connection.

**Likely problem:** The unmasked coffee sentence may have affected the autonomy
vector. This is the clearest context-leakage example in the run, although a
span-only comparison or suitable baseline is still required to distinguish
that explanation from corpus composition or the model's underlying geometry.

## 6. A retirement takeaway followed greenhouse and energy context — inconclusive

Cosine `0.3690` · retirement → solar rank 1 · solar → retirement rank 5

**A takeaway:** The greenhouse project is the author's first step toward a
non-consumption-based retirement.

> Flexicables installed for our geothermal solar powered greenhouse. The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.
> ⟦This will be the first steps to my non consumption based retirement.⟧ https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

**B takeaway:** Solar power will provide the vast majority of future power
generation.

> ⟦Solar power will be the vast majority of power generation in the future⟧

**What happened:** The retirement vector's five closest takeaways from other
notes were:

1. future solar power generation: `0.3690`;
2. running a miner to maintain temperature and record statistics: `0.3626`;
3. Molly supporting automatic backups: `0.3392`;
4. preparing affogato at home: `0.3161`;
5. programming a miner around surplus solar energy: `0.3104`.

**Assessment:** The 73-takeaway corpus contains no other retirement or
non-consumption example. The generated takeaway also explicitly includes the
greenhouse project, making some solar and greenhouse similarity legitimate.
The result is consistent with context outweighing the retirement meaning, but
it cannot establish that failure.

**Separate mask problem:** The selected span still communicates
non-consumption-based retirement, but “This” is unresolved. A labeling step
given only that span cannot recover that the complete takeaway refers to the
greenhouse project.

## Conclusion

- Valid broad signal: case 1.
- Successes: cases 2 and 4.
- Failures: cases 3 and 5.
- Inconclusive: case 6.

The previous analysis incorrectly treated “different takeaways with a real
common subject” as failure. That is precisely the signal the proposed segment
and labeling stages need. A genuine failure is a high similarity for which the
selected spans have no defensible common subject, especially when the match
instead follows unselected source-note context.

Cases 1, 3, and 6 also contain unresolved references in their masks. Case 1
still supports the subject of picky eating. In cases 3 and 6, a labeling step
given only the span could recover a partial subject, but not the actors or
referent needed for the complete generated takeaway.

Raw inputs:
[`communicated-meaning-full-proposal-v1.json`](../../../sse_multivector/communicated-meaning-full-proposal-v1.json) ·
raw results:
[`communicated-meaning-full-v1`](../../../sse_multivector/baselines/communicated-meaning-full-v1/)
