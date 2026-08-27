# SSE Experiments
We generated synthetic tests.

## 1) [SSE-SINGLE-FRAGMENT-MASK-EXPERIMENTS.md](./SSE-SINGLE-FRAGMENT-MASK-EXPERIMENTS.md)
We must have sufficient evidence that single-fragment masks satisfy the following requirements:
1. Changing the wording or boundaries of the mask fragment must not materially change the vector when the intended atomic subject remains the same.
2. Changing only text outside the mask should affect the vector less than changing the atomic subject.
3. When changing the fragment changes the human-defined atomic subject, the resulting vector should also become distinguishable from the original vector.


## 2) [SSE-MULTI-FRAGMENT-MASK-EXPERIMENTS.md](./SSE-MULTI-FRAGMENT-MASK-EXPERIMENTS.md)
We must have sufficient evidence that multi fragment masks satisfy the following requirements:
1) Changing the wording, number, boundaries, or redundancy of mask fragments must not materially change the vector when the intended atomic subject remains the same.
2) Changing only text outside the mask should affect the vector less than changing the atomic subject.
3) When changing a fragment changes the human-defined atomic subject, the resulting vector should also become distinguishable from the original vector.

## 3) Real note transfer experiment
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

## 4) [Real-note holdout mask experiment](./SSE-REAL-NOTE-HOLDOUT-EXPERIMENT.md)

Four predeclared comparisons over 12 previously unused real Nostr notes. Three passed; the hard Windows/Linux comparison failed.
