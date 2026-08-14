# Real-note mask-fidelity transfer

## Question

Do manually selected atomic-subject masks from real Nostr notes produce the
expected cosine relationships?

The nine notes came directly from the frozen Nostr sample. The masks were
selected manually from the source text. TPv3.81, MPv3.3, and their generated
takeaways were not used.

Three subject families were tested against related controls. Every comparison
asked whether the intended pair had a strictly higher cosine than one intended
mask paired with a control.

## Result

**The strict experiment failed. Six of eight predeclared comparisons passed.**

| Family | Comparisons passed | Intended-pair cosine | Result |
|---|---:|---:|---|
| Mining-hardware noise | 2/2 | `0.453278` | Pass |
| Pervasive software telemetry | 1/2 | `0.385255` | Fail |
| Running a miner with solar energy | 3/4 | `0.655805` | Fail |

The two failed comparisons are shown below with the complete note text and
masks. Line and trailing whitespace are normalized for readability.

## Failure 1: telemetry versus cookie dark patterns

### Intended note R07

> they want to control everything..
>
> ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..⟦all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices⟧.. ..i'm still on iOS phone-wise, but my days are numbered with that.. ..likely moving to #GrapheneOS (although i already try to use my phone as little as possible).. ..i've already switched to #Linux computer-wise.. ..free and opensource is the only way to navigate this tech surveillance state with any level of sovereignty

### Intended peer R08

> ⟦Ledger Live Tracks and Sends ALL User Information to Outsourced Data Harvesting Service⟧
>
> "The tracking code is too structural to be just counting users and downloads, like regular apps do. Ledger Live is doing analytics on everything from screen views, to button clicks, error events, installs, uninstalls, etc. It's basically tracking everything. Anything you do on that app gets tracked."
>
> https://www.nobsbitcoin.com/ledger-live-tracks-and-sends-out-all-user-information-by-default/

### Control R09

> ⟦A lot of websites use dark patterns in relation to cookies management, with the majority of them trying to trick you into accepting all of them.⟧ It tells you everything you need to know about their sincerity when they say “we care about your privacy”
>
> #privacy #cookies #darkpatterns

Observed cosines:

- R07 ↔ intended telemetry peer R08: `0.385255`
- R07 ↔ cookie-dark-pattern control R09: `0.396109`
- Margin: `-0.010853`

The control was only `0.010853` higher, but the frozen rule counts the ordering
as a failure. From R08's side, the intended pair did beat the same control by
`+0.120634`.

This establishes an unstable ordering for this three-note comparison. It does
not isolate whether the cause is phrasing, the selected masks, insufficient
examples, or SSE's geometry.

## Failure 2: solar mining versus solar power

### Intended note R10

> This week I just let the miner running to keep temperatures for a minimum and save the #statistics.
>
> I want to find the best way how to run the miner. So far it only starts when it is below a specific temperature (with a day/night mode)
>
> Meanwhile I do a bit of programming to ⟦start up the miner when I have #solar #energy  left⟧. And to have statistics how much solar energy is used for the miner.
>
> Anyhow in the winter days almost everything is required to heat the house so it won’t be much anyhow.
>
> #orangery #greenhouse #grownostr #miner #bitcoin #nostr #btc

### Intended peer R11

> #proofofwork
>
> Got 14 460w ⟦solar panels⟧ series and ready to connect. Have to grab some wire out of my trailer on one of the jobs. This weekend project. might be able to charge a car or ⟦run a Bitcoin miner off this successfully⟧. I still have six extra panels back there and four that are working up top on the roof.
>
> https://m.primal.net/Mkft.jpg

The two selected fragments in R11 jointly identify the subject; the first
supplies the concrete referent of `this`.

### Solar-only control R12

> ⟦Solar power will be the vast majority of power generation in the future⟧

### Mining-only control R06

> Just ordered a BitAxe. ⟦Super excited to finally start mining at home and contributing to the network.⟧

Observed cosines:

| Anchor | Intended solar-mining peer | Solar-only control | Mining-only control |
|---|---:|---:|---:|
| R10 | `0.655805` | `0.777669` | `0.429723` |
| R11 | `0.655805` | `0.465934` | `0.549905` |

R10 was more similar to the generic solar statement than to R11, producing a
`-0.121864` margin. The other three component-control comparisons passed.

This establishes that the two solar-mining masks did not form a uniformly
tighter pair than both components in this tiny fixture. It does not establish
that they could not form a recurring region when additional solar-mining
examples exist.

## Passing family: mining-hardware noise

The intended masks were:

> ⟦The stock fan is just getting too loud to deal with.⟧

and:

> ⟦After nearly a year of mining with the #AvalonNano3, it’s noticeably getting louder over time-even though I keep it clean.⟧

Their cosine was `0.453278`. Against the home-mining control, the two margins
were `+0.315720` and `+0.099155`.

## What this establishes

Manual real-note masks sometimes produced the expected local relationship,
but not reliably across this nine-note pilot. Therefore, the synthetic results
do not yet transfer cleanly enough to settle mask fidelity for real Nostr
notes.

The complete source-bound fixtures and unrounded comparisons are in
`experiment.json` and `analysis.json`; the full 9-by-9 cosine matrix is in
`cosine-matrix.csv`.
