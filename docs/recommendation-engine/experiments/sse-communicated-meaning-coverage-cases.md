# TEv3.1 — Did Missing Coverage Cause TEv2's Suspicious Neighborhoods?

## Answer

TEv2's suspicious neighborhoods had two competing explanations:

1. The target vector did not preserve the intended meaning.
2. The vector preserved useful meaning, but the 32-note corpus did not contain
   enough related vectors to reveal it.

TEv3.1 tested the second explanation by appending raw-text-selected notes while
keeping the model, prompts, masks, and original TEv2 vectors fixed. It ran in
two stages so each coverage change remains independently inspectable.

The earlier TEv2 analysis assigned stable case numbers. This document keeps
that shorthand:

- **Failure #3:** control language matched automatic backups;
- **Failure #5:** an autonomy vector developed a coffee-heavy neighborhood;
- **Failure #6:** a retirement vector followed greenhouse and energy context.

These names identify cases; they are not conclusions.

| Target meaning | What happened after adding coverage | Conclusion |
|---|---|---|
| Failure #3 — systemic control and surveillance | A relevant surveillance vector became rank 1, and relevant additions reached ranks 3, 4, 6, 9–11, 14, and 15. Automatic backups remained rank 2, and several direct surveillance vectors still ranked poorly. | Missing coverage contributed to the failure, but did not fully explain it. |
| Failure #5 — personal autonomy | Relevant notes occupied the first eight ranks. | Missing coverage was a major cause of the misleading TEv2 ranking. |
| Failure #6 — non-consumption-based retirement | Relevant notes reached ranks 1, 4, 6, 8, 11, and 12 in its controlled coverage stage, while greenhouse and solar notes remained near the top. | Missing coverage was one cause, but not the whole cause. |

The supported diagnosis is now:

> All three target vectors retained some intended signal that sparse coverage
> had hidden. Coverage largely repaired Failure #5 and partially repaired
> Failures #3 and #6. Context influence, mask specificity, and inconsistent
> fine-grained geometry remain live explanations for the unrepaired results.

## What changed

TEv2 contained 32 notes and 73 vectors.

TEv3.1 stage 1 appended 12 notes and 33 vectors for Failures #5 and #6. Stage 2
appended six more notes and 25 vectors for Failure #3. All additions were:

- real notes from the frozen learning split;
- selected from raw text without consulting SSE vectors, scores, or ranks;
- written by distinct authors with no author overlap;
- processed with the same takeaway prompt, mask prompt, checkpoint, worker,
  and inference settings.

The final corpus contains 50 notes and 131 vectors. The original 73 TEv2
vectors are byte-identical in both stages. Stage 1 remains preserved as its own
immutable 44-note baseline. In stage 2, the Failure #3 target and its previous
leading neighbors are byte-identical to stage 1, so their cosine scores did not
change. Four vectors from stage 1's final note were recomputed under a different
batch shape and changed only at floating-point roundoff scale; none enters the
Failure #3 leading neighborhood.

## Failure #3 — Control and Automatic Backups

The target vector represented:

> Unspecified actors want to control everything.

Its entire mask was:

> they want to control everything

Before targeted coverage, its first three neighbors were automatic backups,
an open-source iMessage implementation, and a free-software stack. After six
notes and 25 vectors about surveillance, imposed control, financial autonomy,
and digital sovereignty were added, the leading neighborhood became:

| Rank | Cosine | Meaning | Assessment |
|---:|---:|---|---|
| 1 | `0.5067` | Government seeks to end anonymity and identify citizens everywhere | Related |
| 2 | `0.4175` | Molly supports automatic backups | Poor match |
| 3 | `0.4098` | Programmable money could impose government restrictions | Related |
| 4 | `0.4055` | Real-time surveillance keeps people in check | Related |
| 5 | `0.4005` | pypush is serverless, open-source, and cross-platform | Poor match |
| 6 | `0.3799` | Financial systems removing personal ownership and control | Related |
| 7 | `0.3763` | Moving an entire software stack to free and open source | Poor match |
| 8 | `0.3669` | Ledger Live tracks nearly every user interaction | Related |
| 9 | `0.3614` | Cloudflare metadata surveillance despite nominal decentralization | Related |
| 10 | `0.3602` | Consolidating all U.S. data into one AI system | Related |
| 11 | `0.3512` | Mandatory digital identity, compliance, and tracking | Related |
| 12 | `0.3494` | Cookie interfaces trick users into accepting tracking | Related |
| 13 | `0.3417` | Deceptive cookie controls contradict privacy claims | Related |
| 14 | `0.3389` | Avoiding centralized metadata exposure | Related |
| 15 | `0.3257` | Enabling Palantir and other surveillance software | Related |

The ranks and cosines are measured outputs. “Related” and “poor match” are
manual semantic judgments.

The direct measurements are:

1. The target vector's bytes did not change between stages.
2. A newly added vector reached rank 1 while the previous automatic-backup,
   pypush, and free-software scores remained unchanged at ranks 2, 5, and 7.
3. Added vectors selected to cover the target appeared throughout the ranking,
   from rank 1 through rank 73.

The inconsistency also appears within the new coverage. Directly relevant
takeaways about Flock camera surveillance, social-credit spending limits, and
Fourth Amendment protections ranked between 32 and 73. Meanwhile less-direct
takeaways from a surveillance-heavy Matrix note—public support rooms and
self-hosting—ranked 16 and 18.

**Interpretation:** The unchanged target retained useful
control-and-surveillance signal that sparse coverage had hidden. Sparse
coverage was therefore a real contributor to Failure #3. It was not sufficient
to explain the automatic-backup match or the uneven ordering among directly
relevant examples. The ranking is consistent with complete-note context
influencing individual masked vectors, but does not isolate that as the cause.
Other possible causes include the underspecified target mask and SSE's learned
geometry.

## Failure #5 — Personal Autonomy

The target vector represented this takeaway:

> Only choices made without pressure define a person; the rest is a facade.

In TEv2, there were almost no other autonomy examples. Coffee, software, and
other weak matches consequently appeared near the top:

| TEv2 rank | Cosine | Meaning |
|---:|---:|---|
| 1 | `0.4349` | Fear of books changing someone's thinking |
| 2 | `0.4347` | Personal coffee roasting |
| 3 | `0.3875` | Enjoying decaf coffee |
| 4 | `0.3851` | Software containing no proprietary code |
| 5 | `0.3277` | Tim Hortons coffee quality |

After adding autonomy coverage, the first eight results were all judged
relevant:

The meanings in this and the following table are shortened for readability.
The appendix preserves the exact generated text.

| TEv3.1 rank | Cosine | Meaning |
|---:|---:|---|
| 1 | `0.5430` | The wisdom in being yourself |
| 2 | `0.5403` | Moral character removes fear of temporary authority |
| 3 | `0.5225` | Being forced to hide one's potential |
| 4 | `0.4997` | Character over external approval |
| 5 | `0.4974` | Integrity and authenticity |
| 6 | `0.4878` | Following one's own path |
| 7 | `0.4801` | Conformity punishing independent thought |
| 8 | `0.4406` | Character over reputation |

The old coffee-roasting result retained the same `0.4347` score but fell from
rank 2 to rank 10.

**What this shows:** The unchanged target vector contained useful autonomy
signal. TEv2 made it look broken because the corpus offered almost nothing
appropriate to retrieve.

**What remains unresolved:** The coffee score stayed high. Surrounding coffee
text may still have influenced the target vector. TEv3.1 shows that coverage
was a major problem; it does not prove that context leakage is absent.

## Failure #6 — Non-Consumption-Based Retirement

The target vector represented this takeaway:

> The greenhouse project is the author's first step toward a
> non-consumption-based retirement.

TEv2 had no other retirement or non-consumption example. Its first five
results instead followed greenhouse, energy, software, and food context:

| TEv2 rank | Cosine | Meaning |
|---:|---:|---|
| 1 | `0.3690` | Future solar generation |
| 2 | `0.3626` | A miner maintaining greenhouse temperature |
| 3 | `0.3392` | Automatic software backups |
| 4 | `0.3161` | Preparing affogato at home |
| 5 | `0.3104` | A miner using surplus solar energy |

After adding coverage, relevant results appeared throughout the leading
neighborhood:

| TEv3.1 rank | Cosine | Meaning |
|---:|---:|---|
| 1 | `0.3957` | Leaving the conventional American grind |
| 4 | `0.3562` | Receiving a retirement-planning packet |
| 6 | `0.3216` | Declining an employer retirement account |
| 8 | `0.3128` | Simple living leaves less to lose |
| 11 | `0.3002` | Showing alternatives to the usual rat race |
| 12 | `0.2992` | Planning to retire in 2029 |
| 23 | `0.2046` | Choosing minimalism despite pricing incentives |
| 25 | `0.1994` | Being retired while friends still work |
| 33 | `0.1589` | Paid work slowing a food-growing project |

However, the original solar and greenhouse results remained at ranks 2 and 3
with unchanged scores. Automatic backups remained rank 5, and affogato
remained rank 7.

**What this shows:** The unchanged target vector recognized work exit,
retirement planning, and simple living once those meanings existed in the
corpus.

**What remains unresolved:** Coverage did not produce a clean retirement
neighborhood. The vector may legitimately contain several meanings, may have
absorbed irrelevant greenhouse context, or may represent the intended meaning
poorly. TEv3.1 cannot distinguish those explanations. It also added only one
self-provision note, which is insufficient to judge that part reliably.

## Overall conclusion

The direct observation is:

> Adding hand-selected relevant examples substantially changed all three
> targeted rankings without changing the targets or their existing cosine
> relationships.

The supported interpretation is:

- sparse coverage contributed to Failure #3, but poor leading and low-ranked
  direct matches remain;
- sparse coverage was a major cause of the autonomy result;
- sparse coverage contributed to, but does not fully explain, the retirement
  result;
- mask quality and context leakage must remain a separate experimental axis.

TEv3.1 does not establish population-level accuracy or that SSE works across
the complete Nostr corpus.

The remainder of this document preserves the complete evidence. It is not
needed to understand the result.

## Evidence appendix — How to read it

For each vector:

- **Takeaway** is the generated description of the meaning the mask was meant
  to isolate.
- **Mask** is the exact source text selected for that meaning.
- SSE received the complete note and the mask, but not the takeaway.
- **Rank** compares the vector with vectors from other notes in the controlled
  stage for that case. Failure #3 uses stage 2; Failures #5 and #6 use stage 1.
- **Cosine** measures directional similarity between the two vectors.

Scores below are rounded to four decimal places.

## Evidence Appendix — Failure #3

**Target note**

> they want to control everything..
> ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

**Target takeaway:** Unspecified actors want to control everything.

**Target mask:** `they want to control everything`

**Cross-note neighborhood after targeted coverage**

| Rank | Cosine | Exact generated takeaway |
|---:|---:|---|
| 1 | `0.5067` | The CCC warns that Germany’s left-green-liberal government seeks to effectively eliminate anonymity and make citizens identifiable everywhere. |
| 2 | `0.4175` | Molly supports automatic backups. |
| 3 | `0.4098` | Programmable money could expire or be subject to government-imposed spending restrictions. |
| 4 | `0.4055` | Ellison has said real-time surveillance is beneficial because it keeps people in check. |
| 5 | `0.4005` | pypush can now send and receive iMessages on any platform as a serverless, open-source project. |
| 6 | `0.3799` | The author claims emerging financial systems aim to eliminate true personal ownership and control of money, not merely restrict access to it. |
| 7 | `0.3763` | The user is close to making their entire software stack free and open source. |
| 8 | `0.3669` | Ledger Live tracks nearly every user interaction, including screen views, button clicks, errors, installs, and uninstalls, rather than only basic usage metrics. |
| 9 | `0.3614` | Matrix is decentralized in theory but centralized in practice, exposing users to Cloudflare metadata surveillance. |
| 10 | `0.3602` | Larry Ellison wants to consolidate all U.S. data into one large AI system. |
| 11 | `0.3512` | Mandatory digital identity could make every transaction dependent on compliance and enable comprehensive tracking. |
| 12 | `0.3494` | Many websites use cookie-management dark patterns to trick users into accepting all cookies. |
| 13 | `0.3417` | Using deceptive cookie controls undermines websites' claims that they care about user privacy. |
| 14 | `0.3389` | The author’s priority is avoiding centralized metadata exposure, not promoting a favorite protocol, and argues that using Cloudflare or exposing metadata to Proton Mail undermines privacy claims. |
| 15 | `0.3257` | The CCC says the government’s plans would enable the use of Palantir and other surveillance software. |

**Same-note context relationships**

- Cosine `0.5354`
  - Takeaway: The author considers free and open-source software the only way
    to retain sovereignty in a technology surveillance state.
  - Mask: `free and opensource is the only way to navigate this tech
    surveillance state with any level of sovereignty`
- Cosine `0.4268`
  - Takeaway: The author believes Nostr nsec keys are unsafe on proprietary
    operating systems because their telemetry and APIs can access everything
    on a device.
  - Masks: `if you think your #Nostr nsec key is safe on a proprietary OS (
    #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger
    picture` + `all those OS's are saturated with telemetry mechanisms and APIs
    that have access to everything on your devices`

These same-note vectors were not retrieval candidates. They only show which
parts of the complete note the target vector resembles.

### Matrix, self-hosting, and metadata surveillance

> Despite it being easier to self-host XMPP and less expensive on resources, Matrix is more popular. Why?
>
> The real reason Matrix is popular is because corporate and FOSS developers like the encrypted group chats for their internal use. (XMPP is NOT encrypted group chats). So then devs host a Matrix room to answer end-user questions, and having all these rooms encourages overall adoption.
>
> The part that's not usually mentioned, is that only the devs usually use self-hosted Matrix servers, and the vast majority of the public uses Matrix.org which is on Cloudflare with Gmail verification.
>
> In theory Matrix is decentralized, but in the real world, everyone gets Cloudflare metadata surveillance, and uses the same Element client.
>
> Here's my core message: Try to be Self-Sovereign with what you're doing. If you're hosting a website, 1 core VPS for email, whatever. Then host your own XMPP/Matrix. XMPP uses so little resources, it's near free.
>
> If a VPS is really not for you, even if you pay someone like me $100 to set it up: https://simplifiedprivacy.com/email-cloud-combo/index.html
>
> Then public SimpleX/Session servers are right for you. That's fine. This isn't about me trying to force you to use my favorite protocol. It's about you not using Cloudflare (and Protonmail seeing your metadata) and thinking you're "doing privacy".

- Rank 70 · cosine `0.0954`
  - Takeaway: Matrix is more popular than XMPP despite XMPP being easier and
    less resource-intensive to self-host.
  - Mask: `Despite it being easier to self-host XMPP and less expensive on
    resources, Matrix is more popular.`
- Rank 28 · cosine `0.2198`
  - Takeaway: Matrix adoption is driven by corporate and FOSS developers
    wanting encrypted group chats, which the author says XMPP lacks.
  - Mask: `The real reason Matrix is popular is because corporate and FOSS
    developers like the encrypted group chats for their internal use.  (XMPP
    is NOT encrypted group chats).`
- Rank 16 · cosine `0.3206`
  - Takeaway: Developers’ public Matrix support rooms encourage end users to
    adopt Matrix.
  - Mask: `devs host a Matrix room to answer end-user questions, and having all
    these rooms encourages overall adoption`
- Rank 52 · cosine `0.1288`
  - Takeaway: Most developers self-host Matrix, while most public users rely on
    Matrix.org, Cloudflare, Gmail verification, and the Element client.
  - Masks: `only the devs usually use self-hosted Matrix servers` + `the vast
    majority of the public uses Matrix.org which is on Cloudflare with Gmail
    verification` + `uses the same Element client`
- Rank 9 · cosine `0.3614`
  - Takeaway: Matrix is decentralized in theory but centralized in practice,
    exposing users to Cloudflare metadata surveillance.
  - Mask: `In theory Matrix is decentralized, but in the real world, everyone
    gets Cloudflare metadata surveillance`
- Rank 18 · cosine `0.3083`
  - Takeaway: The author urges users to be self-sovereign by hosting their own
    XMPP or Matrix server alongside services they already run; XMPP is
    especially inexpensive to host.
  - Masks: `Try to be Self-Sovereign with what you're doing.` + `If you're
    hosting a website, 1 core VPS for email, whatever.  Then host your own
    XMPP/Matrix.` + `XMPP uses so little resources, it's near free.`
- Rank 31 · cosine `0.2081`
  - Takeaway: Users who cannot or will not run a VPS should use public SimpleX
    or Session servers instead.
  - Masks: `If a VPS is really not for you, even if you pay someone like me
    $100 to set it up:` + `Then public SimpleX/Session servers are right for
    you.`
- Rank 14 · cosine `0.3389`
  - Takeaway: The author’s priority is avoiding centralized metadata exposure,
    not promoting a favorite protocol, and argues that using Cloudflare or
    exposing metadata to Proton Mail undermines privacy claims.
  - Masks: `This isn't about me trying to force you to use my favorite
    protocol.` + `It's about you not using Cloudflare (and Protonmail seeing
    your metadata) and thinking you're "doing privacy".`

### Government plans to end anonymity

> NEW - The CCC warns that the German left-green-liberal government wants to "effectively end anonymity" and make all citizens "identifiable at all times and in all places," including by opening doors to Palantir and other surveillance software.
>
> https://www.ccc.de/en/updates/2024/biometrischer-uberwachungsexzess-der-bundesregierung
>
> https://hell.twtr.plus/media/cf6857f1982ee096057b3c09692a162778dd08f6e86e47e845309425238d567a.file

- Rank 1 · cosine `0.5067`
  - Takeaway: The CCC warns that Germany’s left-green-liberal government seeks
    to effectively eliminate anonymity and make citizens identifiable
    everywhere.
  - Mask: `The CCC warns that the German left-green-liberal government wants
    to "effectively end anonymity" and make all citizens "identifiable at all
    times and in all places,"`
- Rank 15 · cosine `0.3257`
  - Takeaway: The CCC says the government’s plans would enable the use of
    Palantir and other surveillance software.
  - Masks: `The CCC warns that` + `government wants to` + `opening doors to
    Palantir and other surveillance software`

### Financial control

> The Next Phase: Total Financial Control
>
> They’re not just restricting access to money. They’re building a system where you’ll never truly own it again.
>
> Here’s what’s coming next:
>
> Programmable Money – Your funds will expire or be restricted based on government policies.
>
> Social Credit Systems – Your spending could be limited if your behavior doesn’t align with the system.
>
> Forced Digital ID – No transactions without full compliance and tracking.
>
> This is no longer a theory. It’s happening right now in different parts of the world.
>
> Bitcoin is the last escape before total financial surveillance.
>
> No expiration dates on your wealth. No restrictions on where and how you spend. No authority deciding if you "deserve" access to your own money.
>
> They’re not coming for your money. They’re coming for your financial independence.
>
> Will you wait until it’s too late?

- Rank 6 · cosine `0.3799`
  - Takeaway: The author claims emerging financial systems aim to eliminate
    true personal ownership and control of money, not merely restrict access
    to it.
  - Mask: `They’re not just restricting access to money. They’re building a
    system where you’ll never truly own it again.`
- Rank 3 · cosine `0.4098`
  - Takeaway: Programmable money could expire or be subject to
    government-imposed spending restrictions.
  - Mask: `Programmable Money – Your funds will expire or be restricted based
    on government policies.`
- Rank 60 · cosine `0.1118`
  - Takeaway: Social credit systems could limit spending based on whether a
    person’s behavior conforms to system expectations.
  - Mask: `Social Credit Systems – Your spending could be limited if your
    behavior doesn’t align with the system.`
- Rank 11 · cosine `0.3512`
  - Takeaway: Mandatory digital identity could make every transaction
    dependent on compliance and enable comprehensive tracking.
  - Mask: `Forced Digital ID – No transactions without full compliance and
    tracking.`
- Rank 65 · cosine `0.1014`
  - Takeaway: The author says these developments are already occurring in
    different parts of the world rather than remaining theoretical.
  - Mask: `This is no longer a theory. It’s happening right now in different
    parts of the world.`
- Rank 20 · cosine `0.2989`
  - Takeaway: Bitcoin is presented as the final escape from financial
    surveillance because it does not expire, restrict spending, or let an
    authority decide who may access their wealth.
  - Masks: `Bitcoin is the last escape before total financial surveillance.` +
    `No expiration dates on your wealth.` + `No restrictions on where and how
    you spend.` + `No authority deciding if you "deserve" access to your own
    money.`
- Rank 53 · cosine `0.1233`
  - Takeaway: The author warns that the ultimate target is financial
    independence and urges people to act before it is too late.
  - Masks: `They’re coming for your financial independence.` + `Will you wait
    until it’s too late?`

### AI and real-time surveillance

> Larry Ellison wants to put all US data in one big AI system - From the billionaire who said real-time surveillance is good for keeping us in check
> https://www.theregister.com/2025/02/12/larry_ellison_wants_all_data/

- Rank 10 · cosine `0.3602`
  - Takeaway: Larry Ellison wants to consolidate all U.S. data into one large
    AI system.
  - Mask: `Larry Ellison wants to put all US data in one big AI system`
- Rank 4 · cosine `0.4055`
  - Takeaway: Ellison has said real-time surveillance is beneficial because it
    keeps people in check.
  - Mask: `said real-time surveillance is good for keeping us in check`

### Warrantless license-plate surveillance

> Are Automatic License Plate Scanners Constitutional?
>
> An advocacy groups is https://www.404media.co/lawsuit-argues-warrantless-use-of-flock-surveillance-cameras-is-unconstitutional/ a Fourth Amendment challenge against automatic license plate readers. “The City of Norfolk, Virginia, has installed a network of cameras that make it functionally impossible for people to drive anywhere without having their movements tracked, photographed, and stored in an AI-assisted database that enables the warrantless surveillance of their every move. This civil rights lawsuit seeks to end this dragnet surveillance program,” the https://ij.org/wp-content/uploads/2024/10/2024.10.21-1-Complaint.pdf . “In Norfolk, no one can escape the government’s 172 unblinking eyes,” it continues, referring to the 172 Flock cameras currently operational in Norfolk. The Fourth Amendment protects against unreasonable searches and seizures and has been ruled in many cases to protect against warrantless government surveillance, and the lawsuit specifically says Norfolk’s installation violates that.”...
>
> https://www.schneier.com/blog/archives/2024/10/are-automatic-license-plate-scanners-constitutional.html

- Rank 73 · cosine `0.0836`
  - Takeaway: A civil-rights advocacy group is challenging Norfolk’s
    warrantless use of automatic license plate readers under the Fourth
    Amendment.
  - Masks: `An advocacy groups` + `a Fourth Amendment challenge against
    automatic license plate readers` + `The City of Norfolk, Virginia,` +
    `warrantless surveillance`
- Rank 32 · cosine `0.2004`
  - Takeaway: Norfolk’s 172 Flock cameras allegedly make it nearly impossible
    to drive in the city without being tracked, photographed, and recorded in
    an AI-assisted database.
  - Masks: `The City of Norfolk, Virginia, has installed a network of cameras
    that make it functionally impossible for people to drive anywhere without
    having their movements tracked, photographed, and stored in an AI-assisted
    database` + `172 Flock cameras currently operational in Norfolk`
- Rank 63 · cosine `0.1034`
  - Takeaway: The lawsuit seeks to end Norfolk’s camera network as an
    unconstitutional dragnet surveillance program.
  - Masks: `This civil rights lawsuit seeks to end this dragnet surveillance
    program` + `the lawsuit specifically says Norfolk’s installation violates
    that`
- Rank 44 · cosine `0.1589`
  - Takeaway: The complaint argues that the camera network violates Fourth
    Amendment protections against unreasonable searches and warrantless
    government surveillance.
  - Mask: `The Fourth Amendment protects against unreasonable searches and
    seizures and has been ruled in many cases to protect against warrantless
    government surveillance, and the lawsuit specifically says Norfolk’s
    installation violates that.`

### Surveillance money or private money

> We're at a crossroads: government surveillance money or free, open, private people's money. Choose wisely.

- Rank 17 · cosine `0.3160`
  - Takeaway: Society faces a consequential choice between
    government-controlled surveillance money and free, open, private money for
    the people.
  - Mask: `We're at a crossroads: government surveillance money or free, open,
    private people's money.`
- Rank 36 · cosine `0.1865`
  - Takeaway: People should choose carefully between these alternatives.
  - Mask: `Choose wisely.`

## Evidence Appendix — Failure #5

**Target note**

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
> Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree and a crossvine in bloom. This is the recipe for a good Saturday. 🤗

**Target takeaway:** Only choices made without pressure define a person; the
rest is a facade.

**Target masks:** `Only the things you choose without pressure define you.` +
`The rest is a facade.`

### “Just be yourself”

> "Just be yourself" is the best of all the bad advice you ever got. Wisdom hidden in plain sight. It took me a lifetime to understand why this is deep.

- Rank 1 · cosine `0.5430`
  - Takeaway: “Just be yourself” may sound like bad or clichéd advice, but it
    contains profound wisdom.
  - Masks: `"Just be yourself" is the best of all the bad advice you ever got.`
    + `Wisdom hidden in plain sight.`
- Rank 34 · cosine `0.1880`
  - Takeaway: The author says it took a lifetime to understand the advice’s
    depth.
  - Mask: `It took me a lifetime to understand why this is deep.`

### Character over reputation

> Be more concerned with your character than your reputation, because your character is what you really are, while your reputation is merely what others think you are. —Coach John Wooden (This advice is more important now than ever before: character > reputation) https://image.nostr.build/b90b882906eb9a9baf44a23278c50cdb9e343c53482039be2ad670117f9e4b81.jpg

- Rank 8 · cosine `0.4406`
  - Takeaway: Prioritize character over reputation because character reflects
    who you truly are, while reputation is only others’ perception—and this
    distinction is especially important today.
  - Masks: `Be more concerned with your character than your reputation` +
    `your character is what you really are, while your reputation is merely
    what others think you are` +
    `This advice is more important now than ever before`

### Critical thinking and conformity

> #criticalthinking is the scarcest asset in the bankrupt age of conformity. https://m.primal.net/PkPI.jpg

- Rank 19 · cosine `0.3251`
  - Takeaway: Critical thinking is exceptionally scarce in an intellectually
    bankrupt era of conformity.
  - Mask: `#criticalthinking is the scarcest asset in the bankrupt age of
    conformity`

### Nonconformity and self-direction

> In a society that values conformity and obedience, the individual who dares to think for themselves is often ostracized and ridiculed. These nonconformists, these outcasts, are the true pioneers of society, the ones who push us to question our assumptions and expand our horizons. They are the ones who are not afraid to be different, to be themselves. If you find yourself feeling like an outsider, like you don't fit in with the crowd, that's a good thing. It means that you have the potential to make a real difference in the world. Don't be afraid to be yourself, to follow your own path. The world needs your unique perspective. https://image.nostr.build/8a30d246bf5f8ece1abf2a5a6798252c868e7c58a0def48102453d52675533b9.jpg

- Rank 7 · cosine `0.4801`
  - Takeaway: Societies that prize conformity and obedience often ostracize
    people who think independently.
  - Mask: `In a society that values conformity and obedience, the individual
    who dares to think for themselves is often ostracized`
- Rank 12 · cosine `0.4143`
  - Takeaway: Nonconformists are pioneers who challenge assumptions and
    broaden society’s horizons by embracing their differences.
  - Masks: `These nonconformists, these outcasts, are the true pioneers of
    society` + `push us to question our assumptions and expand our horizons` +
    `not afraid to be different, to be themselves`
- Rank 16 · cosine `0.3511`
  - Takeaway: Feeling like an outsider can signal the potential to make a
    meaningful difference.
  - Mask: `If you find yourself feeling like an outsider, like you don't fit in
    with the crowd, that's a good thing. It means that you have the potential
    to make a real difference in the world.`
- Rank 6 · cosine `0.4878`
  - Takeaway: People should be authentic and follow their own path because the
    world needs unique perspectives.
  - Masks: `Don't be afraid to be yourself, to follow your own path.` +
    `The world needs your unique perspective.`

### Hiding one's potential

> The worst feeling is knowing you have so much potential but being forced to hide it and settle for less. When you finally find the courage to be yourself, it’s like a burst of unlimited energy and motivation. That’s when you start moving toward greatness.

- Rank 3 · cosine `0.5225`
  - Takeaway: Being forced to hide your potential and settle for less is
    deeply painful.
  - Masks: `The worst feeling` + `you have so much potential but being forced
    to hide it and settle for less`
- Rank 11 · cosine `0.4153`
  - Takeaway: Finding the courage to be yourself unleashes powerful energy and
    motivation.
  - Masks: `find the courage to be yourself` +
    `a burst of unlimited energy and motivation`
- Rank 15 · cosine `0.3610`
  - Takeaway: Embracing your authentic self helps you move toward greatness.
  - Masks: `When you finally find the courage to be yourself` +
    `That’s when you start moving toward greatness.`

### Integrity and external authority

> In a world where titles and positions often dictate power dynamics, it's easy to feel overshadowed or intimidated by those in authority. But here's a simple truth: if your daily actions and intentions stem from an ethical and moral foundation, you need not worry or be bothered by anyone else, regardless of their temporary title or status. Your integrity, authenticity, and inner compass will guide you through any challenge or confrontation, ensuring that you remain steadfast in your convictions and true to yourself. So, trust in the strength of your character and the righteousness of your deeds, and let go of the need for external validation or approval. When you walk with integrity, you walk with unwavering confidence and peace of mind, unshaken by the winds of authority or influence. Stay true to yourself, and the rest will fall into place.

- Rank 32 · cosine `0.2007`
  - Takeaway: Titles and positions can create power imbalances that make
    people feel intimidated or overshadowed.
  - Masks: `titles and positions often dictate power dynamics` +
    `feel overshadowed or intimidated by those in authority`
- Rank 2 · cosine `0.5403`
  - Takeaway: Acting from a sound ethical and moral foundation removes the
    need to fear people with temporary authority or status.
  - Mask: `if your daily actions and intentions stem from an ethical and moral
    foundation, you need not worry or be bothered by anyone else, regardless
    of their temporary title or status`
- Rank 5 · cosine `0.4974`
  - Takeaway: Integrity, authenticity, and an inner moral compass help you
    face challenges while remaining firm in your convictions and true to
    yourself.
  - Mask: `Your integrity, authenticity, and inner compass will guide you
    through any challenge or confrontation, ensuring that you remain steadfast
    in your convictions and true to yourself.`
- Rank 4 · cosine `0.4997`
  - Takeaway: Trusting your character instead of seeking external approval
    brings confidence and peace of mind that authority and influence cannot
    shake.
  - Masks: `trust in the strength of your character and the righteousness of
    your deeds, and let go of the need for external validation or approval` +
    `When you walk with integrity, you walk with unwavering confidence and
    peace of mind, unshaken by the winds of authority or influence`

**Autonomy measurements**

- The 13 vectors classified here as autonomy or self-direction had median
  target cosine `0.4801`.
- Twelve of the 13 outranked the Tim Hortons quality vector.
- Their 66 cross-note pairings had median cosine `0.4342`, compared with
  `0.0487` across all TEv3.1 cross-note pairs.

## Evidence Appendix — Failure #6

**Target note**

> Flexicables installed for our geothermal solar powered greenhouse. The greenhouse they have in Aliance Nebraska grows pineapple and dates and citrus.
> This will be the first steps to my non consumption based retirement. https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

**Target takeaway:** The greenhouse project is the author's first step toward
a non-consumption-based retirement.

**Target mask:** `This will be the first steps to my non consumption based
retirement.`

### Leaving the American grind

> Hey there, folks! So, I've got this idea to start sharing daily updates on Nostr, kind of like a journal, about my journey to break free from the typical American grind. The plan? Well, by 04/20/2025, my wife and I are hoping to hop on a plane to Argentina with just the essentials we can carry onboard. After some thinking, we've come to the conclusion that life might just be sweeter elsewhere. We're pretty keen on this whole flag theory concept and are excited about stacking passports. I figure sharing online will not only keep us on track but maybe also show others that there's more to life than the usual rat race. Let's see where this adventure takes us!

- Rank 1 · cosine `0.3957`
  - Takeaway: The user plans to post daily Nostr updates documenting an effort
    to leave the conventional American grind.
  - Masks: `start sharing daily updates on Nostr` +
    `about my journey to break free from the typical American grind`
- Rank 34 · cosine `0.1553`
  - Takeaway: The user and their wife hope to fly to Argentina by April 20,
    2025, bringing only essential carry-on belongings.
  - Mask: `by 04/20/2025, my wife and I are hoping to hop on a plane to
    Argentina with just the essentials we can carry onboard`
- Rank 16 · cosine `0.2595`
  - Takeaway: They believe life may be better outside the United States.
  - Mask: `life might just be sweeter elsewhere`
- Rank 73 · cosine `0.0022`
  - Takeaway: They are interested in flag theory and acquiring multiple
    passports.
  - Masks: `keen on this whole flag theory concept` +
    `excited about stacking passports`
- Rank 11 · cosine `0.3002`
  - Takeaway: Sharing the journey publicly is intended to keep them
    accountable and show others alternatives to the usual rat race.
  - Mask: `sharing online will not only keep us on track but maybe also show
    others that there's more to life than the usual rat race`

### Effectively retired while friends still work

> In 2017, 18 and 19: all I did was try to convince all my nomadic artist friends to adopt #Bitcoin as a form of payment None of them grasped what I was saying five years later, they are all still grinding getting no where, and I’m pretty much retired

- Rank 62 · cosine `0.0473`
  - Takeaway: From 2017 through 2019, the author urged nomadic artist friends to
    accept Bitcoin as payment.
  - Masks: `In 2017, 18 and 19` + `try to convince all my nomadic artist
    friends to adopt #Bitcoin as a form of payment`
- Rank 95 · cosine `-0.0677`
  - Takeaway: The friends did not understand the author’s advice and, five
    years later, are still working hard without making progress.
  - Masks: `None of them grasped what I was saying` +
    `five years later, they are all still grinding getting no where`
- Rank 25 · cosine `0.1994`
  - Takeaway: The author says they are now effectively retired, in contrast
    with those friends.
  - Masks: `they are all still grinding getting no where` +
    `I’m pretty much retired`

### Retirement planning

> When I joined my current company, I was provided a retirement packet to fill out. In it, I wrote that I planned on retiring in 2029, and then declined opening a retirement account with them. #JustBitcoinerThings

- Rank 4 · cosine `0.3562`
  - Takeaway: Upon joining the company, the user received a
    retirement-planning packet.
  - Mask: `When I joined my current company, I was provided a retirement
    packet`
- Rank 12 · cosine `0.2992`
  - Takeaway: The user said they planned to retire in 2029.
  - Mask: `I planned on retiring in 2029`
- Rank 6 · cosine `0.3216`
  - Takeaway: The user declined the company retirement account and framed that
    choice as typical Bitcoiner behavior.
  - Masks: `declined opening a retirement account with them` +
    `#JustBitcoinerThings`

### Simple living

> In a time long before Bitcoin boating accidents "Because the government will retaliate, Thoreau says he prefers living simply because he therefore has less to lose." https://en.m.wikipedia.org/wiki/Civil_Disobedience_(Thoreau)

- Rank 8 · cosine `0.3128`
  - Takeaway: Long before Bitcoin-era “boating accident” jokes, Thoreau argued
    that simple living leaves the government less leverage for retaliation.
  - Masks: `long before Bitcoin boating accidents` + `Because the government
    will retaliate, Thoreau says he prefers living simply because he therefore
    has less to lose.`

### Minimalism

> We need to replace a grommet on the fuel tank of our post hole digger. Searching Amazon and eBay the part I need to buy is $11 OR you can get a 70 piece spares kit for $7. Why is it like this? This is why minimalism is an active choice.

- Rank 39 · cosine `0.1453`
  - Takeaway: A replacement fuel-tank grommet for the post-hole digger costs
    $11 by itself, while a 70-piece spare-parts kit costs only $7.
  - Masks: `a grommet on the fuel tank of our post hole digger` +
    `the part I need to buy is $11 OR you can get a 70 piece spares kit for $7`
- Rank 23 · cosine `0.2046`
  - Takeaway: Counterintuitive pricing encourages buying more than needed, so
    practicing minimalism requires an active choice.
  - Masks: `the part I need to buy is $11 OR you can get a 70 piece spares kit
    for $7.` + `This is why minimalism is an active choice.`

### Gardening and self-provision

> Garlic, onions and potatoes coming up. Still have to get the carrots, beets and squash into the open beds. This project would be a lot quicker if I didn’t have to resume the 9 to 5 tomorrow. Or sorry make that seven till five. If things work out the way they did last year I should end up with about 250 pounds of potatoes, 120 pounds of tomatoes, 30 pounds of peppers, 50 pounds of beets, 35 pounds of carrots, and 75 pounds of squash. Then whatever the onions and garlic do. https://image.nostr.build/0e60c08218d2808f3227d96970ec4db153f1dae364fa0e9fc7519d31687fab52.jpg https://image.nostr.build/57b4014c55433ac5ab228f40e36e5b24c50ac4c28a6423dcf1b35909b3e9505f.jpg https://image.nostr.build/5db7a38a467f021cc40ddb947dbf55998189e2d544058af95bf7ec337d889525.jpg https://image.nostr.build/3c1d13edd912a7f91daa9979c40bfabd4181680428620cddbd6ad7946bff10f6.jpg

- Rank 70 · cosine `0.0155`
  - Takeaway: Garlic, onions, and potatoes are coming up.
  - Mask: `Garlic, onions and potatoes coming up.`
- Rank 72 · cosine `0.0034`
  - Takeaway: Carrots, beets, and squash still need to be planted in the open
    beds.
  - Mask: `Still have to get the carrots, beets and squash into the open beds.`
- Rank 33 · cosine `0.1589`
  - Takeaway: Returning to a 7-to-5 job tomorrow will slow the gardening
    project.
  - Masks: `This project would be a lot quicker if I didn’t have to resume the
    9 to 5 tomorrow.` + `seven till five`
- Rank 74 · cosine `0.0015`
  - Takeaway: If yields match last year, the garden should produce about 250
    pounds of potatoes, 120 pounds of tomatoes, 30 pounds of peppers, 50
    pounds of beets, 35 pounds of carrots, and 75 pounds of squash, plus an
    uncertain amount of onions and garlic.
  - Masks: `If things work out the way they did last year I should end up with
    about 250 pounds of potatoes, 120 pounds of tomatoes, 30 pounds of peppers,
    50 pounds of beets, 35 pounds of carrots, and 75 pounds of squash.` +
    `Then whatever the onions and garlic do.`

## Evidence appendix — Provenance

- Every added note came from the frozen learning split.
- Every added note had a distinct author, and no added author appeared in
  an earlier stage.
- Selection used raw note text only; it did not consult SSE vectors, scores,
  or ranks.
- All 58 generated takeaways were encoded, including meanings unrelated to
  the three targets.
- The first 73 raw vectors matched TEv2 byte-for-byte across 224,256 bytes.
- All 73 original receipt rows also matched TEv2 exactly.
- Stage 1 and stage 2 are preserved separately. The Failure #3 target and its
  earlier leading neighbors are byte-identical across them.

Summary:
[`./sse-communicated-meaning-coverage.md`](./sse-communicated-meaning-coverage.md) ·
complete artifacts:
[`../../../sse_multivector/baselines/communicated-meaning-coverage-v1/README.md`](../../../sse_multivector/baselines/communicated-meaning-coverage-v1/README.md)
and
[`../../../sse_multivector/baselines/communicated-meaning-coverage-v2/README.md`](../../../sse_multivector/baselines/communicated-meaning-coverage-v2/README.md)
