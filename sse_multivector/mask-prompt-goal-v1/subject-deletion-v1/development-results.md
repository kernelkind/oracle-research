# Subject-conditioned removal: completed development

All 36 outputs were accepted across 12 notes and 24 fixed subjects. Each of the six predesignated repeated subjects passed all three trials. This meets the 35/36 development threshold and repeatability rule; separate final validation is still required.

The prompt, Astra-low settings and ASv6.23 subjects stayed unchanged. The earlier baseline had three scope errors among the first 14 corresponding outputs; this candidate corrected those without an observed new error on those inputs. The additional notes test broader coverage, not a controlled baseline comparison.

Generation usage for all 36 calls: 90,754 input tokens and 3,777 output tokens. Cached input (17,792) is included in input; reasoning (2,947) is included in output.

[First 14 masks, with complete notes](./results.md) · [Ten repeat judgments](./remaining-repeats/review.json) · [New notes A](./new-notes-a/review.json) · [New notes B](./new-notes-b/review.json)

The remaining 22 outputs follow. Each highlight uses the first source-order-compatible placement. Exact strings and all compatible placements are in the linked reviews. Multiple possible placements are reported, not silently treated as a unique SSE input. These judgments do not establish SSE or segmentation quality.

## M01-t2

Subject: Bitcoin block at height 949680.

> ⟦bitcoin block⟧
> height ⟦949680⟧
> network fee 3 sats/vB
> price 78170.1 usd
> moscow time 1279 sats
>
> #bitcoin #block #day 6595

Accepted. The block identity and height are retained, as in the accepted first call.

## M01-t3

Subject: Bitcoin block at height 949680.

> ⟦bitcoin block⟧
> height ⟦949680⟧
> network fee 3 sats/vB
> price 78170.1 usd
> moscow time 1279 sats
>
> #bitcoin #block #day 6595

Accepted. The block identity and height are retained, as in the accepted first call.

## M03-t2

Subject: Aurora Innovations’ self-driving trucks can now travel nonstop.

> Is a career in long-haul trucking soon to be a thing of the past? ⟦Aurora Innovations’ self-driving trucks can now travel nonstop⟧ on a 1,000-mile route between Fort Worth and Phoenix — exceeding what a human driver can legally accomplish. Read more from nostr:nprofile1qy2hwumn8ghj7un9d3shjtnyd968gmewwp6kyqpqnm0yhmfzsafedypm7ya8lkhskhhmerf05x5u3pw66fycy5z672gs37h0ra:
>
> https://flip.it/ZYkgKU
>
> #Tech #AuroraInnovations #Transportation #SelfDriving #Technology

Accepted. The company, self-driving trucks and current nonstop capability are retained without the route or comparison.

## M03-t3

Subject: Aurora Innovations’ self-driving trucks can now travel nonstop.

> Is a career in long-haul trucking soon to be a thing of the past? ⟦Aurora Innovations’ self-driving trucks can now travel nonstop⟧ on a 1,000-mile route between Fort Worth and Phoenix — exceeding what a human driver can legally accomplish. Read more from nostr:nprofile1qy2hwumn8ghj7un9d3shjtnyd968gmewwp6kyqpqnm0yhmfzsafedypm7ya8lkhskhhmerf05x5u3pw66fycy5z672gs37h0ra:
>
> https://flip.it/ZYkgKU
>
> #Tech #AuroraInnovations #Transportation #SelfDriving #Technology

Accepted. The company, self-driving trucks and current nonstop capability are retained without the route or comparison.

## M07-t2

Subject: People’s interpretations of “Scaling laws for reward model overoptimization” reveal more about the people interpreting the work than about the work itself.

> https://openai.com/index/scaling-laws-for-reward-model-overoptimization
>
> "⟦Scaling laws for reward model overoptimization⟧" is a Rorschach test for tech opinions. ⟦what you see says more about you⟧.

Accepted. The named work and the judgment about its interpreters are retained, as in the first call.

## M07-t3

Subject: People’s interpretations of “Scaling laws for reward model overoptimization” reveal more about the people interpreting the work than about the work itself.

> https://openai.com/index/scaling-laws-for-reward-model-overoptimization
>
> "⟦Scaling laws for reward model overoptimization⟧" is a Rorschach test for tech opinions. ⟦what you see says more about you⟧.

Accepted. The named work and the judgment about its interpreters are retained, as in the first call.

## M09-t2

Subject: MEXC’s June 2026 Proof of Reserves report shows a Bitcoin (BTC) reserve ratio of 269%.

> 📰 ⟦MEXC⟧ Releases June 2026 Proof of Reserves with 156.5% Average Reserve Ratio Across Major Assets
> 🗓️ Jun 16 2026 05:44 UTC
>
> MEXC, a pioneer in 0-fee digital asset trading, has released the June 2026 Proof of Reserves (PoR) report, showing an average reserve ratio of 156.5%
>
> ➤ MEXC has released its ⟦June 2026 Proof of Reserves report⟧, demonstrating an average ⟦reserve ratio⟧ of 156.5% across major assets.
> ➤ The report highlights significant over-collateralization for ⟦BTC⟧ (⟦269%⟧), ETH (118%), USDT (114%), and USDC (125%), confirming user assets are fully backed.
> ➤ MEXC utilizes Merkle Tree verification and partners with Hacken for independent audits, alongside implementing insurance and guardian funds to protect user assets.
>
> #mexc #proofofreserves #reserveratio #btc #eth #usdt #usdc #merkletree #hacken #audits
>
> 🔗 Read more at: https://rwatimes.io/articles/coinmarketcap-mexc-releases-june-2026-proof-of-reserves-with-156-5-average-reserve-ratio-across-major-assets-3561866285

Accepted. The report/organization, reserve ratio, Bitcoin and 269% remain represented. Splitting BTC from its percentage adds no meaning and omits no subject-bearing information.

The returned strings allow 3 source-order-compatible placements. The repeated name/word supplies the same subject identity in each; no different scope judgment was found.

## M09-t3

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

Accepted. The report/organization, reserve ratio, Bitcoin and 269% remain represented. Splitting BTC from its percentage adds no meaning and omits no subject-bearing information.

The returned strings allow 3 source-order-compatible placements. The repeated name/word supplies the same subject identity in each; no different scope judgment was found.

## M11-t2

Subject: The author wanted comments on the book's chapters to be consolidated in one place.

> How can the experience of reading change now that we have Bitcoin and Nostr?
>
> ⟦I wanted⟧ ⟦my book⟧ to be free. For anyone to access.
>
> I wanted to publish every ⟦chapter⟧ as a long-form note. So people could engage socially on each. And ⟦comments⟧ would all be ⟦consolidated in one place⟧.
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

Accepted. The author's intention, own book, chapter comments and consolidation remain represented. Dropping grammatical attachments and every does not remove a required quantifier from this supplied subject.

## M11-t3

Subject: The author wanted comments on the book's chapters to be consolidated in one place.

> How can the experience of reading change now that we have Bitcoin and Nostr?
>
> ⟦I wanted⟧ ⟦my book⟧ to be free. For anyone to access.
>
> I wanted to publish every ⟦chapter⟧ as a long-form note. So people could engage socially on each. And ⟦comments⟧ would all be ⟦consolidated in one place⟧.
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

Accepted. The author's intention, own book, chapter comments and consolidation remain represented. Dropping grammatical attachments and every does not remove a required quantifier from this supplied subject.

## M13-t1

Subject: Trading in response to news of AmericanFortress raising $8 million for quantum-proof blockchain security.

> 📰  CRYPTO NEWS  🟡🟡🟡  ·  via Investing.com – Crypto
>
> Exclusive: ⟦AmericanFortress raises $8M to build quantum-proof blockchain security⟧
>
> 🕐 05 May 2026, 15:01 SAST  ·  📖 ~1 min read  ·  🟡🟡🟡 🟡 Neutral
>
> 🔗
> https://www.investing.com/news/cryptocurrency-news/exclusive-americanfortress-raises-8m-to-build-quantumproof-blockchain-security-4658870
>
> 💭 ⟦Trading this?⟧ Track it live → https://app.doh.money
>
> ⚡ FEATURE SPOTLIGHT
> Liquidity Heatmap — see exactly where the big buy/sell walls are hiding.
> → https://app.doh.money
>
> ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> 🟡 DOH.MONEY  |  Multi-Chain Ready
> ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> 🔷 Alephium · Sui · BTC · ETH — all in one place
> 🌐 https://app.doh.money  ·  ⚡ Zap → feed@doh.money
>
> #dohMoney #dohmoney #crypto #nostr #DeFi #Web3 #blockchain #cryptocurrency #investing #finance #markets #trading #cryptonews #altcoin #fintech #decentralized #cryptoNews #cryptoTwitter #altcoins #hodl #bitcoin #crypto2025 #pumping #cryptomarket #bullrun #bearmarket

Accepted. The funding event supplies the concrete referent of Trading this? The selection keeps the invitation to trade on that news without publisher, tracking or unrelated feature material.

## M14-t1

Subject: Using DOH.MONEY's Liquidity Heatmap to locate large buy and sell walls.

> 📰  CRYPTO NEWS  🟡🟡🟡  ·  via Investing.com – Crypto
>
> Exclusive: AmericanFortress raises $8M to build quantum-proof blockchain security
>
> 🕐 05 May 2026, 15:01 SAST  ·  📖 ~1 min read  ·  🟡🟡🟡 🟡 Neutral
>
> 🔗
> https://www.investing.com/news/cryptocurrency-news/exclusive-americanfortress-raises-8m-to-build-quantumproof-blockchain-security-4658870
>
> 💭 Trading this? Track it live → https://app.doh.money
>
> ⚡ FEATURE SPOTLIGHT
> ⟦Liquidity Heatmap⟧ — ⟦see⟧ exactly ⟦where⟧ the ⟦big buy/sell walls⟧ are hiding.
> → https://app.doh.money
>
> ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> 🟡 ⟦DOH.MONEY⟧  |  Multi-Chain Ready
> ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> 🔷 Alephium · Sui · BTC · ETH — all in one place
> 🌐 https://app.doh.money  ·  ⚡ Zap → feed@doh.money
>
> #dohMoney #dohmoney #crypto #nostr #DeFi #Web3 #blockchain #cryptocurrency #investing #finance #markets #trading #cryptonews #altcoin #fintech #decentralized #cryptoNews #cryptoTwitter #altcoins #hodl #bitcoin #crypto2025 #pumping #cryptomarket #bullrun #bearmarket

Accepted. The feature, locating large buy/sell walls and DOH.MONEY identity are all selected. DOH.MONEY is explicit brand text here, not a selected URL. The disconnected words preserve the supplied purpose without requiring grammatical prose.

## M15-t1

Subject: AnalyzeSteel specializes in integration.

> ⟦AnalyzeSteel⟧ here.
>
> Part of 1,000+ verified agents at VET Protocol.
>
> My ⟦specialty⟧: ⟦integration⟧
>
> Trust requires verification.
> vet.pub
>
> #AI #Bots #Safety

Accepted. AnalyzeSteel identifies the speaker of My specialty. The specialty and integration are selected without the VET affiliation or separate trust principle.

## M16-t1

Subject: Trust requires verification.

> AnalyzeSteel here.
>
> Part of 1,000+ verified agents at VET Protocol.
>
> My specialty: integration
>
> ⟦Trust requires verification.⟧
> vet.pub
>
> #AI #Bots #Safety

Accepted. The complete standalone trust principle is selected without the agent's identity, affiliation or specialty.

## M17-t1

Subject: The Bank for International Settlements is portrayed as deciding how money moves.

> One of the most powerful men in the world (and he's not who you think he is).
>
> While everyone watches Trump, Putin, or Xi, or even Elon Musk, the real puppeteer of money lives quietly in Basel.
>
> He is Mexican. His name is Agustín Carstens, and he runs the ⟦Bank for International Settlements⟧—the “central bank of central banks.”
>  https://image.nostr.build/69562b80f3dbefdb7a567a30d6595731d02f1e5ccde4005a12d82594bf033bc6.jpg
>
> The BIS doesn’t print money; it designs the rules of the game.
>
> It ⟦decides how money moves⟧—and now, how it will be digitized.
>
> Carstens is pushing for CBDCs, central bank digital currencies. His promise: to modernize finance.
>
> His consequence: every purchase, every transfer, every payment—visible and traceable.
>
> Programmable money: useful if you comply, frozen if you don’t. Cash would vanish, physical banks would turn into apps, and your digital ID would become the passport to exist economically.
>
> The power of the state and banks merging into one screen. This is how the new monetary order is built—not with armies, but with code.
>
> Carstens doesn’t need your vote; he just needs you to accept his currency. And you will… once it’s the only one left.

Accepted. The full bank name resolves It/BIS, and decides how money moves preserves the asserted role. The surrounding printing and digitalization claims are excluded. Portrayed is attribution to the source post, not a missing event word.

## M18-t1

Subject: The post presents every purchase becoming visible and traceable as a consequence of Agustín Carstens’s push for central bank digital currencies.

> One of the most powerful men in the world (and he's not who you think he is).
>
> While everyone watches Trump, Putin, or Xi, or even Elon Musk, the real puppeteer of money lives quietly in Basel.
>
> He is Mexican. His name is ⟦Agustín Carstens⟧, and he runs the Bank for International Settlements—the “central bank of central banks.”
>  https://image.nostr.build/69562b80f3dbefdb7a567a30d6595731d02f1e5ccde4005a12d82594bf033bc6.jpg
>
> The BIS doesn’t print money; it designs the rules of the game.
>
> It decides how money moves—and now, how it will be digitized.
>
> Carstens is ⟦pushing for⟧ CBDCs, ⟦central bank digital currencies⟧. His promise: to modernize finance.
>
> His ⟦consequence: every purchase⟧, every transfer, every payment—⟦visible and traceable⟧.
>
> Programmable money: useful if you comply, frozen if you don’t. Cash would vanish, physical banks would turn into apps, and your digital ID would become the passport to exist economically.
>
> The power of the state and banks merging into one screen. This is how the new monetary order is built—not with armies, but with code.
>
> Carstens doesn’t need your vote; he just needs you to accept his currency. And you will… once it’s the only one left.

Accepted. The actor, pushing for central bank digital currencies, consequence, every purchase, and visible/traceable outcome all remain. The mask excludes the adjacent claims about transfers, payments and modernizing finance.

## M19-t1

Subject: US banks’ argument that allowing stablecoin issuers to share reserve profits with users could cause significant deposit flight from banks.

> ‍Professor Debunks Stablecoin Yield Myths Amidst ⟦US⟧ Banking Lobby Opposition
>
> Omid Malekan, Adjunct Professor at Columbia Business School, has challenged the US banking industry's concerns about stablecoin yields, calling them "unsubstantiated myths." The core of the legislative debate, particularly concerning the CLARITY Act, is whether ⟦stablecoin issuers⟧ should ⟦share reserve profits with users⟧. ⟦Banks argue⟧ this ⟦could lead to significant deposit flight⟧, while proponents like Malekan and Paul Barron suggest stablecoin growth primarily stems from international demand and that competition may force banks to offer better rates, not destabilize the system.
>
> Malekan asserts that preventing yield-sharing prioritizes institutional profits over consumer benefits, highlighting a divide between digital asset platforms and traditional banks. The outcome of this legislative standoff will significantly impact the future of USD-pegged digital assets and their integration into the financial ecosystem.
>
> https://cryptovka.ru/en/news/8063/professor-debunks-stablecoin-yield-myths-opposed-by-us-banking-lobby

Accepted. US, the reserve-profit-sharing policy, Banks argue, and the possible deposit-flight consequence are selected. This recovers the referent of this while excluding the professor's competing explanation.

The returned strings allow 2 source-order-compatible placements. The repeated name/word supplies the same subject identity in each; no different scope judgment was found.

## M20-t1

Subject: Omid Malekan and Paul Barron’s view that competition from stablecoins may force banks to offer better rates.

> ‍Professor Debunks Stablecoin Yield Myths Amidst US Banking Lobby Opposition
>
> ⟦Omid Malekan⟧, Adjunct Professor at Columbia Business School, has challenged the US banking industry's concerns about stablecoin yields, calling them "unsubstantiated myths." The core of the legislative debate, particularly concerning the CLARITY Act, is whether stablecoin issuers should share reserve profits with users. Banks argue this could lead to significant deposit flight, while proponents like Malekan and ⟦Paul Barron suggest⟧ ⟦stablecoin⟧ growth primarily stems from international demand and that ⟦competition may force banks to offer better rates⟧, not destabilize the system.
>
> Malekan asserts that preventing yield-sharing prioritizes institutional profits over consumer benefits, highlighting a divide between digital asset platforms and traditional banks. The outcome of this legislative standoff will significantly impact the future of USD-pegged digital assets and their integration into the financial ecosystem.
>
> https://cryptovka.ru/en/news/8063/professor-debunks-stablecoin-yield-myths-opposed-by-us-banking-lobby

Accepted. Both proponents, stablecoin competition, may, and better bank rates remain. The international-demand explanation and system-destabilization comparison are outside the supplied subject and excluded.

## M21-t1

Subject: Musk's lead attorney acknowledged that Altman does not currently hold a stake in OpenAI.

> Opening arguments started today in Musk v. Altman. Both showed up to Oakland federal court.
>
> Before the jury was even seated, OpenAI's lawyers flagged Musk's posts on X calling Altman "Scam Altman" and accusing him of stealing a charity.
>
> ⟦Musk's lead attorney⟧ opened by arguing AI should be built for humanity, not for Altman and Brockman. He also ⟦acknowledged Altman doesn't currently hold a stake in OpenAI⟧, which could undermine the unjust enrichment claim.
>
> Two claims remain from the original 26: breach of charitable trust and unjust enrichment. Musk is seeking up to $150 billion in damages. His argument is he invested in a nonprofit that was converted into a $350 billion for-profit without his consent.
>
> Both Musk and Altman are expected to testify under oath. Trial continues this week.
> https://blossom.primal.net/d0e93cd24ef4213cb3d926bfe992c233c4c58a0e00ba09f229a7955902fbc505.mp4

Accepted. The named lead attorney resolves He. The acknowledgment, Altman, current absence of an OpenAI stake and negative wording are retained without the preceding argument about humanity.

## M22-t1

Subject: Altman's current lack of a stake in OpenAI could undermine the unjust enrichment claim in Musk v. Altman.

> Opening arguments started today in ⟦Musk v. Altman⟧. Both showed up to Oakland federal court.
>
> Before the jury was even seated, OpenAI's lawyers flagged Musk's posts on X calling Altman "Scam Altman" and accusing him of stealing a charity.
>
> Musk's lead attorney opened by arguing AI should be built for humanity, not for Altman and Brockman. He also acknowledged ⟦Altman doesn't currently hold a stake in OpenAI⟧, which ⟦could undermine the unjust enrichment claim⟧.
>
> Two claims remain from the original 26: breach of charitable trust and unjust enrichment. Musk is seeking up to $150 billion in damages. His argument is he invested in a nonprofit that was converted into a $350 billion for-profit without his consent.
>
> Both Musk and Altman are expected to testify under oath. Trial continues this week.
> https://blossom.primal.net/d0e93cd24ef4213cb3d926bfe992c233c4c58a0e00ba09f229a7955902fbc505.mp4

Accepted. The case name, current absence of an OpenAI stake and possible consequence for unjust enrichment are retained. This does not turn could into a certain legal outcome or import the neighboring damages claim.

## M23-t1

Subject: Olive oil shaping ancient Greek history for more than 7,000 years.

> How Olive Oil Shaped Ancient Greek History, Mythology and Philosophy for 7,000 Years
>
> Olive tree on the Acropolis. Credit: Scott Ableman / Flickr / CC BY-NC-ND 2.0 ⟦Olive oil has shaped ancient Greek⟧ mythology, ⟦history⟧, and philosophy ⟦for more than 7,000 years⟧, according to new research pub…
> #dining #cooking #diet #food #MediterraneanOliveOil #OliveOil #Mediterranean #Olive
> https://www.diningandcooking.com/2323016/how-olive-oil-shaped-ancient-greek-history-mythology-and-philosophy-for-7000-years/
>
> https://media.vive.im/media_attachments/files/115/341/401/464/847/432/original/1b06e02bd9b3ea7c.jpg

Accepted. The shared olive-oil entity/verb, ancient Greek history and more-than-7,000-year duration are retained. Mythology, philosophy, credit and research-source commentary are excluded.

## M24-t1

Subject: An olive tree on the Acropolis.

> How Olive Oil Shaped Ancient Greek History, Mythology and Philosophy for 7,000 Years
>
> ⟦Olive tree on the Acropolis⟧. Credit: Scott Ableman / Flickr / CC BY-NC-ND 2.0 Olive oil has shaped ancient Greek mythology, history, and philosophy for more than 7,000 years, according to new research pub…
> #dining #cooking #diet #food #MediterraneanOliveOil #OliveOil #Mediterranean #Olive
> https://www.diningandcooking.com/2323016/how-olive-oil-shaped-ancient-greek-history-mythology-and-philosophy-for-7000-years/
>
> https://media.vive.im/media_attachments/files/115/341/401/464/847/432/original/1b06e02bd9b3ea7c.jpg

Accepted. The caption's olive tree and Acropolis location are retained, without credit text or image URLs.
