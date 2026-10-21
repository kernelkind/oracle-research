# Subject-conditioned removal: first six notes

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

All 14 masks were accepted: twelve subjects from six notes, with two additional M05 trials. The unchanged baseline had eleven accepted masks and three M05 scope errors on these same inputs. This candidate corrected that observed error without a new observed error in this small set.

The change replaces ambiguous minimization wording with removal judged against the fixed supplied subject. These results do not establish why the change worked, corpus-wide reliability, SSE quality, or segmentation quality.

The remaining development calls are recorded in [completed development](./development-results.md): 36/36 accepted. This page preserves the first 14 outputs. [Separate final validation](./final/results.md) also passed at 52/52; the original 35/36 development and 50/52 final requirements remained unchanged.

Generation usage for these 14 calls: 34,599 input tokens and 1,557 output tokens. Cached input (7,680) is included in input; reasoning (1,255) is included in output.

Full source notes follow. Each highlight shows the returned fragments at the first source-order-compatible placement. All placement alternatives (`./mechanical-checks.json`) and execution verification (`./verification.json`) are saved separately; this display does not claim SSE equivalence across placements.

## M01-t1

Subject: Bitcoin block at height 949680.

> ⟦bitcoin block⟧
> height ⟦949680⟧
> network fee 3 sats/vB
> price 78170.1 usd
> moscow time 1279 sats
>
> #bitcoin #block #day 6595

Accepted. Bitcoin block plus its number identifies the requested block height in this status note; no other status field is included.

## M02-t1

Subject: Bitcoin network transaction fee rate of 3 satoshis per virtual byte.

> ⟦bitcoin⟧ block
> height 949680
> ⟦network fee 3 sats/vB⟧
> price 78170.1 usd
> moscow time 1279 sats
>
> #bitcoin #block #day 6595

Accepted. Bitcoin identity and the full fee value/unit are retained; other status fields are excluded.

## M03-t1

Subject: Aurora Innovations’ self-driving trucks can now travel nonstop.

> Is a career in long-haul trucking soon to be a thing of the past? ⟦Aurora Innovations’ self-driving trucks can now travel nonstop⟧ on a 1,000-mile route between Fort Worth and Phoenix — exceeding what a human driver can legally accomplish. Read more from nostr:nprofile1qy2hwumn8ghj7un9d3shjtnyd968gmewwp6kyqpqnm0yhmfzsafedypm7ya8lkhskhhmerf05x5u3pw66fycy5z672gs37h0ra:
>
> https://flip.it/ZYkgKU
>
> #Tech #AuroraInnovations #Transportation #SelfDriving #Technology

Accepted. Retains the company, self-driving trucks and current nonstop-travel capability; excludes the route and comparison.

## M04-t1

Subject: Aurora Innovations’ self-driving trucks’ ability to travel nonstop on a 1,000-mile route between Fort Worth and Phoenix exceeds what a human driver can legally accomplish.

> Is a career in long-haul trucking soon to be a thing of the past? ⟦Aurora Innovations’ self-driving trucks⟧ can now ⟦travel nonstop⟧ on a ⟦1,000-mile route between Fort Worth and Phoenix⟧ — ⟦exceeding⟧ what a ⟦human driver can legally accomplish⟧. Read more from nostr:nprofile1qy2hwumn8ghj7un9d3shjtnyd968gmewwp6kyqpqnm0yhmfzsafedypm7ya8lkhskhhmerf05x5u3pw66fycy5z672gs37h0ra:
>
> https://flip.it/ZYkgKU
>
> #Tech #AuroraInnovations #Transportation #SelfDriving #Technology

Accepted. Retains the truck referent, nonstop travel, full route and legal human-driver comparison. Missing function words do not remove those relationships in the complete source context.

## M05-t1

Subject: A call for Salvadorans to make their presence known.

> ⟦Where are⟧ all
> My ⟦Salvadorans⟧ at?
> https://blossom.primal.net/2b5ac7389e0863fcc843a67abf667a024f4e8f79310cbe048a3e3141bfecedca.jpg

Accepted. Where are plus Salvadorans retains the call in the complete source context without adding affinity. all and at are not necessary to identify this supplied subject; grammatical completeness is not required.

## M05-t2

Subject: A call for Salvadorans to make their presence known.

> ⟦Where⟧ are all
> My ⟦Salvadorans⟧ at?
> https://blossom.primal.net/2b5ac7389e0863fcc843a67abf667a024f4e8f79310cbe048a3e3141bfecedca.jpg

Accepted. Where and Salvadorans retain the call in the complete source context without adding affinity. The mask need not be grammatical prose. This acceptance is not a claim about a future SSE vector.

## M05-t3

Subject: A call for Salvadorans to make their presence known.

> ⟦Where⟧ are all
> My ⟦Salvadorans⟧ at?
> https://blossom.primal.net/2b5ac7389e0863fcc843a67abf667a024f4e8f79310cbe048a3e3141bfecedca.jpg

Accepted. Where and Salvadorans retain the call in the complete source context without adding affinity. The mask need not be grammatical prose. This acceptance is not a claim about a future SSE vector.

## M06-t1

Subject: The poster's expressed affinity with Salvadorans.

> Where are all
> ⟦My Salvadorans⟧ at?
> https://blossom.primal.net/2b5ac7389e0863fcc843a67abf667a024f4e8f79310cbe048a3e3141bfecedca.jpg

Accepted. My Salvadorans retains precisely the requested affinity and group.

## M07-t1

Subject: People’s interpretations of “Scaling laws for reward model overoptimization” reveal more about the people interpreting the work than about the work itself.

> https://openai.com/index/scaling-laws-for-reward-model-overoptimization
>
> "⟦Scaling laws for reward model overoptimization⟧" is a Rorschach test for tech opinions. ⟦what you see says more about you⟧.

Accepted. The work's title and the author's judgment about its readers' interpretations are retained. The unrelated URL is excluded.

## M08-t1

Subject: Scaling laws for reward model overoptimization.

> https://openai.com/index/scaling-laws-for-reward-model-overoptimization
>
> "⟦Scaling laws for reward model overoptimization⟧" is a Rorschach test for tech opinions. what you see says more about you.

Accepted. The literal title captures the supplied subject; the surrounding Rorschach comparison is excluded.

## M09-t1

Subject: MEXC’s June 2026 Proof of Reserves report shows a Bitcoin (BTC) reserve ratio of 269%.

> 📰 ⟦MEXC⟧ Releases June 2026 Proof of Reserves with 156.5% Average Reserve Ratio Across Major Assets
> 🗓️ Jun 16 2026 05:44 UTC
>
> MEXC, a pioneer in 0-fee digital asset trading, has released the June 2026 Proof of Reserves (PoR) report, showing an average reserve ratio of 156.5%
>
> ➤ MEXC has released its ⟦June 2026 Proof of Reserves report⟧, demonstrating an average ⟦reserve ratio⟧ of 156.5% across major assets.
> ➤ The report highlights significant over-collateralization for ⟦BTC (269%)⟧, ETH (118%), USDT (114%), and USDC (125%), confirming user assets are fully backed.
> ➤ MEXC utilizes Merkle Tree verification and partners with Hacken for independent audits, alongside implementing insurance and guardian funds to protect user assets.
>
> #mexc #proofofreserves #reserveratio #btc #eth #usdt #usdc #merkletree #hacken #audits
>
> 🔗 Read more at: https://rwatimes.io/articles/coinmarketcap-mexc-releases-june-2026-proof-of-reserves-with-156-5-average-reserve-ratio-across-major-assets-3561866285

Accepted. Retains MEXC, the report date/title, reserve ratio and BTC's 269%. Other assets and the 156.5% average are excluded. Repeated wording permits multiple source placements; these have the same scope judgment.

## M10-t1

Subject: MEXC implements insurance funds and guardian funds to protect user assets.

> 📰 ⟦MEXC⟧ Releases June 2026 Proof of Reserves with 156.5% Average Reserve Ratio Across Major Assets
> 🗓️ Jun 16 2026 05:44 UTC
>
> MEXC, a pioneer in 0-fee digital asset trading, has released the June 2026 Proof of Reserves (PoR) report, showing an average reserve ratio of 156.5%
>
> ➤ MEXC has released its June 2026 Proof of Reserves report, demonstrating an average reserve ratio of 156.5% across major assets.
> ➤ The report highlights significant over-collateralization for BTC (269%), ETH (118%), USDT (114%), and USDC (125%), confirming user assets are fully backed.
> ➤ MEXC utilizes Merkle Tree verification and partners with Hacken for independent audits, alongside ⟦implementing insurance and guardian funds to protect user assets⟧.
>
> #mexc #proofofreserves #reserveratio #btc #eth #usdt #usdc #merkletree #hacken #audits
>
> 🔗 Read more at: https://rwatimes.io/articles/coinmarketcap-mexc-releases-june-2026-proof-of-reserves-with-156-5-average-reserve-ratio-across-major-assets-3561866285

Accepted. Retains the organization, both funds and their protective purpose. Repeated MEXC mentions permit multiple placements; each identifies the same organization.

## M11-t1

Subject: The author wanted comments on the book's chapters to be consolidated in one place.

> How can the experience of reading change now that we have Bitcoin and Nostr?
>
> ⟦I wanted my book⟧ to be free. For anyone to access.
>
> I wanted to publish ⟦every chapter⟧ as a long-form note. So people could engage socially on each. And ⟦comments⟧ would all be ⟦consolidated in one place⟧.
>
> I wanted it to feel like the e-reader experience people are used to from other legacy apps.
>
> So nostr:nprofile1qqsqamukr9l4c6lrskdks9lx54ekdpv9d3qku2dzjfdatg2m9ftu3vgpz9mhxue69uhkummnw3ezuamfdejj7qguwaehxw309aex2mrp0yhxy6t5vdhkjmnsv9exktnrdakj7fgmet8 made me a library app for my book! To display the long-form notes like a book. With a "break the fourth wall" at the end of each chapter button that brings them into Primal for the full Nostr onboarding experience.
>
> This was my vision for the future of reading. And the book itself teaches Nostr. A fully immersive experience for the reader.
>
> I'm so happy to be able to share it with you.
>
> Check it out at www.theattentionprotocol.com
>
>
>
>
>

Accepted. Retains the author's intention, their book, its chapters, comments and consolidation. Excludes free access and the app's other features.

## M12-t1

Subject: The library app has a button at the end of each chapter that takes readers into Primal for the full Nostr onboarding experience.

> How can the experience of reading change now that we have Bitcoin and Nostr?
>
> I wanted my book to be free. For anyone to access.
>
> I wanted to publish every chapter as a long-form note. So people could engage socially on each. And comments would all be consolidated in one place.
>
> I wanted it to feel like the e-reader experience people are used to from other legacy apps.
>
> So nostr:nprofile1qqsqamukr9l4c6lrskdks9lx54ekdpv9d3qku2dzjfdatg2m9ftu3vgpz9mhxue69uhkummnw3ezuamfdejj7qguwaehxw309aex2mrp0yhxy6t5vdhkjmnsv9exktnrdakj7fgmet8 made me a ⟦library app⟧ for my book! To display the long-form notes like a book. With a "break the fourth wall" ⟦at the end of each chapter⟧ ⟦button that brings them into Primal for the full Nostr onboarding experience⟧.
>
> This was my vision for the future of reading. And the book itself teaches Nostr. A fully immersive experience for the reader.
>
> I'm so happy to be able to share it with you.
>
> Check it out at www.theattentionprotocol.com
>
>
>
>
>

Accepted. Retains the library app, chapter-end button, Primal and the full Nostr onboarding experience. The complete post supplies the ordinary reader reference; this does not introduce a new missing-reference standard.

See conversion gaps (`03bd9e45:docs/experiments/publication-gaps.csv`) for `collection:tracked-mask-prompt-goal-v1`.
