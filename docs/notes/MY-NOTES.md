TO AGENTS: YOU MUST NOT EDIT OR DELETE. These are my personal notes, which is read only to AI's.

# Thesis
My current thesis is that a content hierarchy will be the best content discovery mechanism for users.
- That way the algorithm does not need to gauge whether the user is getting tired of a specific topic, it's up to the user to decide that and switch topics themselves.
- The user might not know what they want to see, but when presented with cascading options, they can "narrow-in" on their current interest.


# High-Level Implementation

From a high level, the current implementation is:
1) an AI is given a note and prompted with a takeaway prompt (TP) to generate takeaways which apply to a given note
2) an AI is given a takeaway and the original note and is prompted with a mask prompt (MP) to generate a mask for that takeaway in the note
3) an AI is given a mask and the original note and is prompted with a relevance prompt* to figure out how relevant the mask is to the whole of the note*
4) Each mask is used in SSE to generate a vector which represents the semantic meaning of the mask, where vectors that are close to each other have a similar semantic meaning.
5) Some mechanism is used to "segment" the vectors in the vector space dimensions to group them together
6) Some algorithm recursively groups the segments together to form a hierarchy
7) a UI presents the hierarchy as a series of multiple choice decisions. It does not need to present all levels/nodes of the hierarchy. Once it gets to the last decision, it presents the notes associated with the vectors in that node. Each vector has a relevance value, and the UI can sort by this so the notes which have the highest relevance to the mask the vector is generated from are at the top of the presentation.


# Scaleability

The current implementation is definitely not scaleable. But an embedding model can be trained to generate the masks for a note, skipping two AI pipelines. I'm not sure if the relevance weighting can be tacked on as well, but that would be ideal if it could be, that way only one embedding model would need to be trained.


# SSE

SSE was seen in practice to perform well for determining similarity of atomic facts. We are making the bet that it can also perform well for determining similarity of atomic note meanings. Because if it does, then we can use geometric locality of vectors to construct this hierarchy.

There are some things that must be true for SSE to work favorably for us:
1. Different wording for the same atomic subject should produce nearby vectors. (Semantic understanding)
2. Materially different subjects must remain distinguishable despite sharing works or surrounding text. (Context isolation)


## SSE Experiments
We generated synthetic tests.

### 1) Single 'fragment' factorial experiment
Generate a synthetic note with an atomic subject as a control. Then do the following permutations and compare:
1.1) Use the same mask, but compare it to a version with different surrounding context. (tests whether context can be isolated well)
1.2) Paraphrase the mask, but use the same context as the control (tests for semantic understanding, for the positive case)
1.3) Use a completely different mask, but use the same context (tests for semantic understanding, for the negative case)

#### Experimental Results


### 2) Multi fragrment mask experiment
Control: A synthetic note with the subject in one fragment
Test: The same synthetic note with the subject in multiple fragments


### 3) Real note transfer experiment
Repeat experiments 1 & 2 with real Nostr notes and hand picked masks 


#### Experimental Results
**Telemetry comparison: (R07 vs R08, cosine of 0.5114)**
**Hypothesis:** These masks are both semantically about telemetry/data tracking. The first is a statement about operating systems in general having telemetry, the second is about a specific app that has concrete telemetry mechanisms. We predict that these vectors will have a high cosine.

**R07**
> they want to control everything..
>
> ..if you think your #Nostr nsec key is safe on a proprietary OS (#Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger
> picture.. ..⟦all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices⟧.. ..i'm still
> on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS.. ..i've already switched to #Linux computer-
> wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

**R08**
> Ledger Live Tracks and Sends ALL User Information to Outsourced Data Harvesting Service
>
> “The tracking code is too structural to be just counting users and downloads, like regular apps do. {Ledger Live is doing analytics on
> everything from screen views, to button clicks, error events, installs, uninstalls, etc. It's basically tracking everything.} Anything you
> do on that app gets tracked.”
>
> https://www.nobsbitcoin.com/ledger-live-tracks-and-sends-out-all-user-information-by-default/

**Result:** validated. Although 0.51 is not extrordinarily high

---

**Control comparison (R09 vs R07, cosine 0.3961)**
hmm a bad comparison it seems

**R07**
> they want to control everything..
>
> ..if you think your #Nostr nsec key is safe on a proprietary OS (#Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger
> picture.. ..⟦all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices⟧.. ..i'm still
> on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS.. ..i've already switched to #Linux computer-
> wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

**R09**
> ⟦A lot of websites use dark patterns in relation to cookies management, with the majority of them trying to trick you into accepting all of
> them.⟧ It tells you everything you need to know about their sincerity when they say “we care about your privacy”
>
> #privacy #cookies #darkpatterns

---

**Solar-mining comparison (R10 vs R11, cosine 0.6558):**
**Description:** These masks are both very narrowly similar, they are about using solar panels with a bitcoin miner. The contexts are different though. The first note's context is a casual thought about wanting to optimize their solar-mining system for maximum duration of operation. The second note's context is about the logistics of solar mining.
**Hypothesis:** The cosine will be high for the vectors since the masks are extremely semantically similar despite having different contexts.
**Result:** validated

**R10**
> This week I just let the miner running to keep temperatures for a minimum and save the #statistics.
>
> I want to find the best way how to run the miner. So far it only starts when it is below a specific temperature (with a day/night mode)
>
> Meanwhile I do a bit of programming to ⟦start up the miner when I have #solar #energy left⟧. And to have statistics how much solar energy
> is used for the miner.
>
> Anyhow in the winter days almost everything is required to heat the house so it won’t be much anyhow.
>
> #orangery #greenhouse #grownostr #miner #bitcoin #nostr #btc

**R11**
> #proofofwork
>
> Got 14 460w ⟦solar panels⟧ series and ready to connect. Have to grab some wire out of my trailer on one of the jobs. This weekend project.
> might be able to charge a car or ⟦run a Bitcoin miner off this successfully⟧. I still have six extra panels back there and four that are
> working up top on the roof.
>
> https://m.primal.net/Mkft.jpg

---


**R10**
> This week I just let the miner running to keep temperatures for a minimum and save the #statistics.
>
> I want to find the best way how to run the miner. So far it only starts when it is below a specific temperature (with a day/night mode)
>
> Meanwhile I do a bit of programming to ⟦start up the miner when I have #solar #energy left⟧. And to have statistics how much solar energy
> is used for the miner.
>
> Anyhow in the winter days almost everything is required to heat the house so it won’t be much anyhow.
>
> #orangery #greenhouse #grownostr #miner #bitcoin #nostr #btc

R12
> ⟦Solar power will be the vast majority of power generation in the future⟧

R10↔R12 cosine: 0.7777

**Ablation study:**

R10
> start up the miner when I have #solar #energy left

R11
> solar panels
> run a Bitcoin miner off this successfully

R12
> Solar power will be the vast majority of power generation in the future

 Edge                    Full notes    Masks only     Change
━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━  ━━━━━━━━━━━━  ━━━━━━━━━
 R10↔R11 solar mining        0.6558        0.6981    +0.0423
──────────────────────  ────────────  ────────────  ─────────
 R10↔R12 solar only          0.7777        0.6977    −0.0800
──────────────────────  ────────────  ────────────  ─────────
 R11↔R12 solar only          0.4659        0.5965    +0.1306


