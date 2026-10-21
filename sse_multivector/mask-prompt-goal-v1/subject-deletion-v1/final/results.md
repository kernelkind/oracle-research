# Final mask validation

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../../docs/experiments/README.md#reading-the-research-records).

The unchanged prompt passed semantic review on all 52 outputs: 40 fixed subjects from 20 reserved notes, plus two extra trials for six predesignated subjects. All six repeated subjects passed all three trials. The approved threshold was 50/52, with no repeated demonstrated error.

[Prompt](../mask-prompt.md) · [Validation plan](./plan.json) · [Development results](../development-results.md) · Execution verification (`./verification.json`)

All 52 calls succeeded on their first attempt. Independent checks verified the frozen prompt and source inputs, unchanged subjects, fresh threads/workdirs, tool-free execution, exact returned text and all compatible positions. No resource guard stopped a call.

These notes were reserved before mask-prompt development. Their prior subject-generation and review exposure is disclosed. No notes, subjects or attempted masks were replaced, and the prompt was not edited during final validation.

Generation usage: 128,544 input tokens and 4,285 output tokens. Cached input (45,696) is included in input; reasoning (3,210) is included in output.

No semantic mask errors or unresolved scope judgments remained in this set. Limits remain: this is a small selected corpus, not a population guarantee; masks need not form grammatical prose; an ambiguous abbreviation's mask does not establish its author's unique intent; and repeated text can leave source position ambiguous. Nothing here establishes SSE or segmentation quality.

Each heading identifies one actual call. The subject is unchanged. Every note is shown in full with its returned fragments highlighted at the first compatible position. Exact strings, all compatible positions and judgments are in the linked batch review. Positions use UTF-16 code-unit offsets; no unique-position or equivalent-SSE-vector claim is made for repeated strings.

## F01-S1-t1

Subject: 2025年11月13日03:10～03:20のJPリレー「こじら川」は、投稿11件、再投稿0件、お気に入り51件。

> ■ 流速計測
>   ⟦2025/11/13 03:10～03:20⟧
>
> [⟦JP リレー⟧]
> きりの川: 9 posts, 0 reposts, 1 favs
> やぶみ川: 11 posts, 0 reposts, 51 favs
> かすてら川: 2 posts, 0 reposts, 2 favs
> ⟦こじら川: 11 posts, 0 reposts, 51 favs⟧
> しの川: 2 posts, 0 reposts, 0 favs
>
> [GLOBAL リレー]
> きりの川(G): 15 posts, 1 reposts, 56 favs
> こじら大川: 15 posts, 1 reposts, 56 favs
> しの川(G): 1 posts, 0 reposts, 0 favs
>
> ■ 野洲田川定点観測所
>   https://nostr-hotter-site.vercel.app
>
>

Accepted. The shared timestamp, JP relay group, exact relay name and all three specified counts are retained; neighboring rows are excluded.

## F01-S1-t2

Subject: 2025年11月13日03:10～03:20のJPリレー「こじら川」は、投稿11件、再投稿0件、お気に入り51件。

> ■ 流速計測
>   ⟦2025/11/13 03:10～03:20⟧
>
> [⟦JP リレー⟧]
> きりの川: 9 posts, 0 reposts, 1 favs
> やぶみ川: 11 posts, 0 reposts, 51 favs
> かすてら川: 2 posts, 0 reposts, 2 favs
> ⟦こじら川: 11 posts, 0 reposts, 51 favs⟧
> しの川: 2 posts, 0 reposts, 0 favs
>
> [GLOBAL リレー]
> きりの川(G): 15 posts, 1 reposts, 56 favs
> こじら大川: 15 posts, 1 reposts, 56 favs
> しの川(G): 1 posts, 0 reposts, 0 favs
>
> ■ 野洲田川定点観測所
>   https://nostr-hotter-site.vercel.app
>
>

Accepted. The same timestamp, JP section, named row and all counts are retained as in the accepted first output.

## F01-S1-t3

Subject: 2025年11月13日03:10～03:20のJPリレー「こじら川」は、投稿11件、再投稿0件、お気に入り51件。

> ■ 流速計測
>   ⟦2025/11/13 03:10～03:20⟧
>
> [⟦JP リレー⟧]
> きりの川: 9 posts, 0 reposts, 1 favs
> やぶみ川: 11 posts, 0 reposts, 51 favs
> かすてら川: 2 posts, 0 reposts, 2 favs
> ⟦こじら川: 11 posts, 0 reposts, 51 favs⟧
> しの川: 2 posts, 0 reposts, 0 favs
>
> [GLOBAL リレー]
> きりの川(G): 15 posts, 1 reposts, 56 favs
> こじら大川: 15 posts, 1 reposts, 56 favs
> しの川(G): 1 posts, 0 reposts, 0 favs
>
> ■ 野洲田川定点観測所
>   https://nostr-hotter-site.vercel.app
>
>

Accepted. The same timestamp, JP section, named row and all counts are retained as in the accepted first output.

## F01-S2-t1

Subject: 2025年11月13日03:10～03:20のGLOBALリレー「こじら大川」は、投稿15件、再投稿1件、お気に入り56件。

> ■ 流速計測
>   ⟦2025/11/13 03:10～03:20⟧
>
> [JP リレー]
> きりの川: 9 posts, 0 reposts, 1 favs
> やぶみ川: 11 posts, 0 reposts, 51 favs
> かすてら川: 2 posts, 0 reposts, 2 favs
> こじら川: 11 posts, 0 reposts, 51 favs
> しの川: 2 posts, 0 reposts, 0 favs
>
> [⟦GLOBAL リレー⟧]
> きりの川(G): 15 posts, 1 reposts, 56 favs
> ⟦こじら大川: 15 posts, 1 reposts, 56 favs⟧
> しの川(G): 1 posts, 0 reposts, 0 favs
>
> ■ 野洲田川定点観測所
>   https://nostr-hotter-site.vercel.app
>
>

Accepted. The shared timestamp, GLOBAL relay group, exact relay name and all three specified counts are retained; neighboring rows are excluded.

## F02-S1-t1

Subject: Ecosystem growth is one of the four KPI areas governing MegaETH's token incentive mechanism.

> ⟦MegaETH⟧, a prominent player in the decentralized finance space, is set to address structural challenges related to low liquidity and high Fully Diluted Valuations (FDV) through an innovative ⟦"KPI incentive" mechanism⟧. According to Namik Muduroglu, co-founder of MegaETH, this new system will decouple ⟦token⟧ unlocks from rigid timelines, instead tying them directly to the actual progress and achievements of the protocol.
>
> A significant portion of the MEGA token supply, exceeding 50%, will be reserved for holders who opt for strategic lock-ups. These tokens will only be distributed upon the successful attainment of pre-defined key performance indicators (KPIs). The KPIs are categorized into ⟦four⟧ key ⟦areas: ecosystem growth⟧, MegaETH decentralization, performance enhancements, and advancements in the broader Ethereum ecosystem's decentralization.
>
> Upon achieving these metrics, rewards will be allocated to participants based on the duration of their locked positions. Any tokens not unlocked through the KPI mechanism will be retained by the foundation for treasury purposes, supporting ongoing development and expansion initiatives.
>
> #crypto #blockchain #news

Accepted. MegaETH, KPI incentive mechanism, token, four areas and ecosystem growth are retained without the three other areas or token-unlock conditions.

The returned strings have 3 compatible placements; see all positions (`./batch-a/review.json`).

## F02-S1-t2

Subject: Ecosystem growth is one of the four KPI areas governing MegaETH's token incentive mechanism.

> ⟦MegaETH⟧, a prominent player in the decentralized finance space, is set to address structural challenges related to low liquidity and high Fully Diluted Valuations (FDV) through an innovative ⟦"KPI incentive" mechanism⟧. According to Namik Muduroglu, co-founder of MegaETH, this new system will decouple ⟦token⟧ unlocks from rigid timelines, instead tying them directly to the actual progress and achievements of the protocol.
>
> A significant portion of the MEGA token supply, exceeding 50%, will be reserved for holders who opt for strategic lock-ups. These tokens will only be distributed upon the successful attainment of pre-defined key performance indicators (KPIs). The KPIs are categorized into ⟦four⟧ key ⟦areas: ecosystem growth⟧, MegaETH decentralization, performance enhancements, and advancements in the broader Ethereum ecosystem's decentralization.
>
> Upon achieving these metrics, rewards will be allocated to participants based on the duration of their locked positions. Any tokens not unlocked through the KPI mechanism will be retained by the foundation for treasury purposes, supporting ongoing development and expansion initiatives.
>
> #crypto #blockchain #news

Accepted. MegaETH, token KPI mechanism, four areas and ecosystem growth remain. The joined four-key-areas phrase in trial3 still describes the same KPI grouping; no other area or reward condition is added.

The returned strings have 3 compatible placements; see all positions (`./repeats/review.json`).

## F02-S1-t3

Subject: Ecosystem growth is one of the four KPI areas governing MegaETH's token incentive mechanism.

> ⟦MegaETH⟧, a prominent player in the decentralized finance space, is set to address structural challenges related to low liquidity and high Fully Diluted Valuations (FDV) through an innovative ⟦"KPI incentive" mechanism⟧. According to Namik Muduroglu, co-founder of MegaETH, this new system will decouple ⟦token⟧ unlocks from rigid timelines, instead tying them directly to the actual progress and achievements of the protocol.
>
> A significant portion of the MEGA token supply, exceeding 50%, will be reserved for holders who opt for strategic lock-ups. These tokens will only be distributed upon the successful attainment of pre-defined key performance indicators (KPIs). The KPIs are categorized into ⟦four key areas: ecosystem growth⟧, MegaETH decentralization, performance enhancements, and advancements in the broader Ethereum ecosystem's decentralization.
>
> Upon achieving these metrics, rewards will be allocated to participants based on the duration of their locked positions. Any tokens not unlocked through the KPI mechanism will be retained by the foundation for treasury purposes, supporting ongoing development and expansion initiatives.
>
> #crypto #blockchain #news

Accepted. MegaETH, token KPI mechanism, four areas and ecosystem growth remain. The joined four-key-areas phrase in trial3 still describes the same KPI grouping; no other area or reward condition is added.

The returned strings have 3 compatible placements; see all positions (`./repeats/review.json`).

## F02-S2-t1

Subject: MegaETH's proposed KPI incentive mechanism is presented as innovative.

> ⟦MegaETH⟧, a prominent player in the decentralized finance space, ⟦is set to⟧ address structural challenges related to low liquidity and high Fully Diluted Valuations (FDV) through an ⟦innovative "KPI incentive" mechanism⟧. According to Namik Muduroglu, co-founder of MegaETH, this new system will decouple token unlocks from rigid timelines, instead tying them directly to the actual progress and achievements of the protocol.
>
> A significant portion of the MEGA token supply, exceeding 50%, will be reserved for holders who opt for strategic lock-ups. These tokens will only be distributed upon the successful attainment of pre-defined key performance indicators (KPIs). The KPIs are categorized into four key areas: ecosystem growth, MegaETH decentralization, performance enhancements, and advancements in the broader Ethereum ecosystem's decentralization.
>
> Upon achieving these metrics, rewards will be allocated to participants based on the duration of their locked positions. Any tokens not unlocked through the KPI mechanism will be retained by the foundation for treasury purposes, supporting ongoing development and expansion initiatives.
>
> #crypto #blockchain #news

Accepted. MegaETH, proposed/future intent and the innovative characterization of the KPI incentive mechanism are retained without the structural challenges.

## F03-S1-t1

Subject: Bread buns.

> My ⟦bunz⟧ https://www.diningandcooking.com/2534519/my-bunz/ #Bread #homemade #HomemadeBread
>
> https://media.vive.im/media_attachments/files/116/150/124/527/601/230/original/2128cfcd1a823342.jpg

Accepted. Bunz expresses bread buns in this complete source, whose bread hashtags disambiguate the ordinary word. The returned string is not a URL and includes no affinity. It also occurs inside the URL slug; that alternate occurrence selects the same word, not My or another meaning. This is recorded positional ambiguity, not a demonstrated scope-changing alternative or proof of which occurrence the model intended.

The returned strings have 2 compatible placements; see all positions (`./batch-a/review.json`). One alternative lies inside a URL, but the returned fragment is not itself a URL and no different scope is demonstrated.

## F03-S1-t2

Subject: Bread buns.

> My ⟦bunz⟧ https://www.diningandcooking.com/2534519/my-bunz/ #Bread #homemade #HomemadeBread
>
> https://media.vive.im/media_attachments/files/116/150/124/527/601/230/original/2128cfcd1a823342.jpg

Accepted. Bunz retains the bread-bun subject without affinity or homemade meaning, as in the first output. Both the ordinary-text and URL-slug matches remain recorded; neither selects additional words or proves an intended URL selection.

The returned strings have 2 compatible placements; see all positions (`./repeats/review.json`). One alternative lies inside a URL, but the returned fragment is not itself a URL and no different scope is demonstrated.

## F03-S1-t3

Subject: Bread buns.

> My ⟦bunz⟧ https://www.diningandcooking.com/2534519/my-bunz/ #Bread #homemade #HomemadeBread
>
> https://media.vive.im/media_attachments/files/116/150/124/527/601/230/original/2128cfcd1a823342.jpg

Accepted. Bunz retains the bread-bun subject without affinity or homemade meaning, as in the first output. Both the ordinary-text and URL-slug matches remain recorded; neither selects additional words or proves an intended URL selection.

The returned strings have 2 compatible placements; see all positions (`./repeats/review.json`). One alternative lies inside a URL, but the returned fragment is not itself a URL and no different scope is demonstrated.

## F03-S2-t1

Subject: The post author's homemade bread buns.

> ⟦My bunz⟧ https://www.diningandcooking.com/2534519/my-bunz/ #Bread #⟦homemade⟧ #HomemadeBread
>
> https://media.vive.im/media_attachments/files/116/150/124/527/601/230/original/2128cfcd1a823342.jpg

Accepted. My bunz plus homemade retains the author's homemade bread buns. It excludes the URL and does not require reproducing hashtag syntax.

## F04-S1-t1

Subject: Independent Reserve is a New Zealand option offering 45,224 bitcoin satoshis for $100.

> Best Value:
>
> LightningPay:
> 64,638 sats = ⟦$100⟧
>
> Other ⟦NZ options⟧:
> 63,655 sats - Easy Crypto
> 54,394 sats - Swyftx
> ⟦45,224 sats⟧ - ⟦Independent Reserve⟧
>

Accepted. The shared $100 comparison, New Zealand options, exact amount/unit and Independent Reserve are retained without another provider's offer.

## F04-S1-t2

Subject: Independent Reserve is a New Zealand option offering 45,224 bitcoin satoshis for $100.

> Best Value:
>
> LightningPay:
> 64,638 sats = ⟦$100⟧
>
> Other ⟦NZ⟧ options:
> 63,655 sats - Easy Crypto
> 54,394 sats - Swyftx
> ⟦45,224 sats⟧ - ⟦Independent Reserve⟧
>

Accepted. The shared price, NZ identity, exact amount/unit and provider remain. The option is identified by the offer in context, whether or not the word options is retained.

## F04-S1-t3

Subject: Independent Reserve is a New Zealand option offering 45,224 bitcoin satoshis for $100.

> Best Value:
>
> LightningPay:
> 64,638 sats = ⟦$100⟧
>
> Other ⟦NZ options⟧:
> 63,655 sats - Easy Crypto
> 54,394 sats - Swyftx
> ⟦45,224 sats⟧ - ⟦Independent Reserve⟧
>

Accepted. The shared price, NZ identity, exact amount/unit and provider remain. The option is identified by the offer in context, whether or not the word options is retained.

## F04-S2-t1

Subject: LightningPay offers 64,638 bitcoin satoshis for $100.

> Best Value:
>
> ⟦LightningPay⟧:
> ⟦64,638 sats = $100⟧
>
> Other NZ options:
> 63,655 sats - Easy Crypto
> 54,394 sats - Swyftx
> 45,224 sats - Independent Reserve
>

Accepted. The named provider and complete amount/value exchange are retained without the Best Value endorsement or competing offers.

## F05-S1-t1

Subject: Dissent becomes dangerous once an authoritarian regime consolidates power.

> https://ipfs.girino.org/ipfs/QmdkMQcLFhJEwkpZs9p139MYfbXTk46qa5xaohM2zVqBiw?filename=file.jpg
>
> Freedom is easier to lose than to reclaim.
>
> ⟦Once a regime consolidates power⟧, it controls the military, the police, the courts, the media, and the economy.
>
> ⟦Dissent becomes dangerous⟧. Organization becomes nearly impossible. The state knows who you are, where you work, and who your family is. Speaking out can mean losing your job, your home, or your life. This asymmetry is why ⟦authoritarian⟧ takeovers are measured in years, but recoveries take decades.
>
> Iran's revolution in 1979 happened quickly. Forty-five years later, people are still fighting to get back what was lost.
>
> Venezuela's slide into dictatorship was gradual, with each crisis used to justify more control. Now millions have fled, and those remaining face a state apparatus designed to crush resistance before it starts.
>
> The lesson isn't that freedom can't be reclaimed. It's that waiting until after consolidation makes the cost unbearable.
>
> Source: https://www.facebook.com/photo/?fbid=1351671356992121

Accepted. The consolidation condition, dangerous dissent and authoritarian characterization remain. Descriptions of institutional control, punishments and country examples are excluded.

## F05-S1-t2

Subject: Dissent becomes dangerous once an authoritarian regime consolidates power.

> https://ipfs.girino.org/ipfs/QmdkMQcLFhJEwkpZs9p139MYfbXTk46qa5xaohM2zVqBiw?filename=file.jpg
>
> Freedom is easier to lose than to reclaim.
>
> ⟦Once a regime consolidates power⟧, it controls the military, the police, the courts, the media, and the economy.
>
> ⟦Dissent becomes dangerous⟧. Organization becomes nearly impossible. The state knows who you are, where you work, and who your family is. Speaking out can mean losing your job, your home, or your life. This asymmetry is why ⟦authoritarian⟧ takeovers are measured in years, but recoveries take decades.
>
> Iran's revolution in 1979 happened quickly. Forty-five years later, people are still fighting to get back what was lost.
>
> Venezuela's slide into dictatorship was gradual, with each crisis used to justify more control. Now millions have fled, and those remaining face a state apparatus designed to crush resistance before it starts.
>
> The lesson isn't that freedom can't be reclaimed. It's that waiting until after consolidation makes the cost unbearable.
>
> Source: https://www.facebook.com/photo/?fbid=1351671356992121

Accepted. The consolidation condition, dangerous dissent and authoritarian characterization remain. Splitting Once from the regime clause does not change this meaning.

## F05-S1-t3

Subject: Dissent becomes dangerous once an authoritarian regime consolidates power.

> https://ipfs.girino.org/ipfs/QmdkMQcLFhJEwkpZs9p139MYfbXTk46qa5xaohM2zVqBiw?filename=file.jpg
>
> Freedom is easier to lose than to reclaim.
>
> ⟦Once⟧ a ⟦regime consolidates power⟧, it controls the military, the police, the courts, the media, and the economy.
>
> ⟦Dissent becomes dangerous⟧. Organization becomes nearly impossible. The state knows who you are, where you work, and who your family is. Speaking out can mean losing your job, your home, or your life. This asymmetry is why ⟦authoritarian⟧ takeovers are measured in years, but recoveries take decades.
>
> Iran's revolution in 1979 happened quickly. Forty-five years later, people are still fighting to get back what was lost.
>
> Venezuela's slide into dictatorship was gradual, with each crisis used to justify more control. Now millions have fled, and those remaining face a state apparatus designed to crush resistance before it starts.
>
> The lesson isn't that freedom can't be reclaimed. It's that waiting until after consolidation makes the cost unbearable.
>
> Source: https://www.facebook.com/photo/?fbid=1351671356992121

Accepted. The consolidation condition, dangerous dissent and authoritarian characterization remain. Splitting Once from the regime clause does not change this meaning.

## F05-S2-t1

Subject: Freedom is easier to lose than to reclaim.

> https://ipfs.girino.org/ipfs/QmdkMQcLFhJEwkpZs9p139MYfbXTk46qa5xaohM2zVqBiw?filename=file.jpg
>
> ⟦Freedom⟧ is ⟦easier to lose than to reclaim⟧.
>
> Once a regime consolidates power, it controls the military, the police, the courts, the media, and the economy.
>
> Dissent becomes dangerous. Organization becomes nearly impossible. The state knows who you are, where you work, and who your family is. Speaking out can mean losing your job, your home, or your life. This asymmetry is why authoritarian takeovers are measured in years, but recoveries take decades.
>
> Iran's revolution in 1979 happened quickly. Forty-five years later, people are still fighting to get back what was lost.
>
> Venezuela's slide into dictatorship was gradual, with each crisis used to justify more control. Now millions have fled, and those remaining face a state apparatus designed to crush resistance before it starts.
>
> The lesson isn't that freedom can't be reclaimed. It's that waiting until after consolidation makes the cost unbearable.
>
> Source: https://www.facebook.com/photo/?fbid=1351671356992121

Accepted. The exact comparative freedom claim remains without the later explanation or cases.

## F06-S1-t1

Subject: Former Jan. 6 defendant Ryan Samsel is suing the federal government over alleged abuses in custody.

> Jan. 6 Defendant Sues Federal Government Over Alleged Abuses In Custody
>
> From ZeroHedge
>
> Authored by Matthew Vadum via The Epoch Times, A ⟦former Jan. 6 defendant⟧ who ⟦alleges⟧ he was repeatedly ⟦abused in custody⟧ is ⟦suing the federal government⟧ for almost $18 million. ⟦Ryan Samsel⟧ of Bristol, Pennsylvania, was convicted in September 2024 of civil disorder-related offenses […]
>
> Dec 3rd 2025 3:45pm EST
>
> Source Link: https://www.zerohedge.com/political/jan-6-defendant-sues-federal-government-over-alleged-abuses-custody
>
> Share, promote & comment with Nostr: https://dissentwatch.com/boost/?boost_post_id=1070739

Accepted. The former Jan.6 defendant role, allegation status, custody abuse, federal-government lawsuit and Ryan Samsel identity are retained. The amount, location and conviction are excluded.

## F06-S1-t2

Subject: Former Jan. 6 defendant Ryan Samsel is suing the federal government over alleged abuses in custody.

> Jan. 6 Defendant Sues Federal Government Over Alleged Abuses In Custody
>
> From ZeroHedge
>
> Authored by Matthew Vadum via The Epoch Times, A ⟦former Jan. 6 defendant⟧ who ⟦alleges⟧ he was repeatedly ⟦abused in custody⟧ is ⟦suing the federal government⟧ for almost $18 million. ⟦Ryan Samsel⟧ of Bristol, Pennsylvania, was convicted in September 2024 of civil disorder-related offenses […]
>
> Dec 3rd 2025 3:45pm EST
>
> Source Link: https://www.zerohedge.com/political/jan-6-defendant-sues-federal-government-over-alleged-abuses-custody
>
> Share, promote & comment with Nostr: https://dissentwatch.com/boost/?boost_post_id=1070739

Accepted. The defendant's identity/role, allegation status, custody abuse and federal-government lawsuit remain. Splitting suing from federal government changes no subject meaning.

## F06-S1-t3

Subject: Former Jan. 6 defendant Ryan Samsel is suing the federal government over alleged abuses in custody.

> Jan. 6 Defendant Sues Federal Government Over Alleged Abuses In Custody
>
> From ZeroHedge
>
> Authored by Matthew Vadum via The Epoch Times, A ⟦former Jan. 6 defendant⟧ who ⟦alleges⟧ he was repeatedly ⟦abused in custody⟧ is ⟦suing⟧ the ⟦federal government⟧ for almost $18 million. ⟦Ryan Samsel⟧ of Bristol, Pennsylvania, was convicted in September 2024 of civil disorder-related offenses […]
>
> Dec 3rd 2025 3:45pm EST
>
> Source Link: https://www.zerohedge.com/political/jan-6-defendant-sues-federal-government-over-alleged-abuses-custody
>
> Share, promote & comment with Nostr: https://dissentwatch.com/boost/?boost_post_id=1070739

Accepted. The defendant's identity/role, allegation status, custody abuse and federal-government lawsuit remain. Splitting suing from federal government changes no subject meaning.

## F06-S2-t1

Subject: Ryan Samsel alleges that he was repeatedly abused in custody.

> Jan. 6 Defendant Sues Federal Government Over Alleged Abuses In Custody
>
> From ZeroHedge
>
> Authored by Matthew Vadum via The Epoch Times, A former Jan. 6 defendant who ⟦alleges⟧ he was ⟦repeatedly abused in custody⟧ is suing the federal government for almost $18 million. ⟦Ryan Samsel⟧ of Bristol, Pennsylvania, was convicted in September 2024 of civil disorder-related offenses […]
>
> Dec 3rd 2025 3:45pm EST
>
> Source Link: https://www.zerohedge.com/political/jan-6-defendant-sues-federal-government-over-alleged-abuses-custody
>
> Share, promote & comment with Nostr: https://dissentwatch.com/boost/?boost_post_id=1070739

Accepted. The named speaker of the allegation, repeated abuse and custody context are retained without the lawsuit or conviction. The source allegation is not turned into an established fact.

## F07-S1-t1

Subject: A ground invasion of Iran would be like the biggest pile of dog feces anyone could ever possibly step in.

> a ⟦ground invasion of iran would be⟧ the ⟦biggest pile of dog shit⟧ you ⟦could ever⟧ possibly ⟦step in⟧

Accepted. The invasion, hypothetical metaphor, superlative and possibility of stepping into it remain; omitted function words do not change the condemnation's meaning.

## F07-S2-t1

Subject: A ground invasion of Iran.

> a ⟦ground invasion of iran⟧ would be the biggest pile of dog shit you could ever possibly step in

Accepted. The ground invasion of Iran is retained without the condemning metaphor, matching this plain subject.

## F08-S1-t1

Subject: Ontario's high cost of living.

> Here's how much Ontario salaries are expected to increase this year
> Salary is always top of mind for employees in ⟦Ontario's high-cost-of-living⟧ environment, but let's face it, not everyone receives the raise they feel they deserve. A new report from consulting firm Normandin Beaudry shows the projected trend of planning salary increases for Ontario companies in 2026. And afte...
> #salary #economy #employment #Ontario #Toronto
> https://www.blogto.com/city/2026/01/ontario-salaries-increasing-2026/
>
> https://files.hongkongers.net/media_attachments/files/115/934/917/224/548/909/original/db862fa20192c695.jpg

Accepted. Ontario and high cost of living are selected without the salary expectations or report attribution.

## F08-S2-t1

Subject: Toronto.

> Here's how much Ontario salaries are expected to increase this year
> Salary is always top of mind for employees in Ontario's high-cost-of-living environment, but let's face it, not everyone receives the raise they feel they deserve. A new report from consulting firm Normandin Beaudry shows the projected trend of planning salary increases for Ontario companies in 2026. And afte...
> #salary #economy #employment #Ontario #⟦Toronto⟧
> https://www.blogto.com/city/2026/01/ontario-salaries-increasing-2026/
>
> https://files.hongkongers.net/media_attachments/files/115/934/917/224/548/909/original/db862fa20192c695.jpg

Accepted. The Toronto word is selected from its hashtag. No geographic relationship or URL meaning is added.

## F09-S1-t1

Subject: Sharing, promoting, and commenting on the post about Americans’ country preferences using Nostr.

> Which ⟦Countries Americans Like⟧ Most (And Least)
>
> From ZeroHedge
>
> Public opinion offers a window into how Americans perceive the world beyond their borders. Using Gallup survey data from February 2026, this ranking, via Visual Capitalist’s Dorothy Neufeld, shows how Americans view 21 major countries, from longtime allies to geopolitical competitors. The results provide a snapshot of global perceptions at a […]
>
> Jun 17th 2026 2:45am EDT
>
> Source Link: https://www.zerohedge.com/geopolitical/which-countries-americans-most-and-least
>
> ⟦Share, promote & comment with Nostr⟧: https://dissentwatch.com/boost/?boost_post_id=1148911

Accepted. The countries/Americans/preference reference identifies the post being shared, promoted and commented on with Nostr. Survey details and publisher attribution are outside this subject.

## F09-S2-t1

Subject: A ranking of Americans’ views of 21 major countries using Gallup survey data from February 2026.

> Which Countries Americans Like Most (And Least)
>
> From ZeroHedge
>
> Public opinion offers a window into how Americans perceive the world beyond their borders. ⟦Using Gallup survey data from February 2026⟧, this ⟦ranking⟧, via Visual Capitalist’s Dorothy Neufeld, shows how ⟦Americans view 21 major countries⟧, from longtime allies to geopolitical competitors. The results provide a snapshot of global perceptions at a […]
>
> Jun 17th 2026 2:45am EDT
>
> Source Link: https://www.zerohedge.com/geopolitical/which-countries-americans-most-and-least
>
> Share, promote & comment with Nostr: https://dissentwatch.com/boost/?boost_post_id=1148911

Accepted. The survey organization, February2026 data, ranking, Americans and21 major countries are retained without unrelated footer instructions.

## F10-S1-t1

Subject: Germany bears responsibility that it cannot easily avoid.

> The Duran (Interview Polylang)
>
> Money flow running low, ⟦Germany on the hook⟧
>
> Published on Jan 2, 2026
>
> The Duran: Episode 2427
>
> +++
>
> Sources & Links
>
>
> Please visit a channel for donations and further information
>
>
> **OUR OFFICIAL CHANNELS**
>
> THE DURAN:
> https://youtube.com/channel/UCdeMVChrumySxV9N1w0Au-w
>
> ALEX:
> https://youtube.com/alexchristoforou
>
> **VIDEO PLATFORMS**
>
> RUMBLE THE DURAN: https://rumble.com/c/theduran
>
> ODYSEE:
>
> THE DURAN: https://odysee.com/@theduran
>
> ALEXANDER: https://odysee.com/@AlexanderMercouris:a
>
> ALEX: https://odysee.com/@alexchristoforou:7
>
> BITCHUTE:
>
> THE DURAN:
> https://bitchute.com/theduran
>
> ALEXANDER:
> https://bitchute.com/alexandermercouris
>
> ALEX:
> https://bitchute.com/channel/izwNAdmMGIC7
>
> +++
>
> https://www.youtube.com/watch?v=gCj6CatE-u4
>

Accepted. Germany on the hook carries the subject through ordinary idiomatic meaning. Low money flow and other video metadata are not added.

## F10-S2-t1

Subject: Readers are asked to visit a channel to make donations.

> The Duran (Interview Polylang)
>
> Money flow running low, Germany on the hook
>
> Published on Jan 2, 2026
>
> The Duran: Episode 2427
>
> +++
>
> Sources & Links
>
>
> Please ⟦visit a channel for donations⟧ and further information
>
>
> **OUR OFFICIAL CHANNELS**
>
> THE DURAN:
> https://youtube.com/channel/UCdeMVChrumySxV9N1w0Au-w
>
> ALEX:
> https://youtube.com/alexchristoforou
>
> **VIDEO PLATFORMS**
>
> RUMBLE THE DURAN: https://rumble.com/c/theduran
>
> ODYSEE:
>
> THE DURAN: https://odysee.com/@theduran
>
> ALEXANDER: https://odysee.com/@AlexanderMercouris:a
>
> ALEX: https://odysee.com/@alexchristoforou:7
>
> BITCHUTE:
>
> THE DURAN:
> https://bitchute.com/theduran
>
> ALEXANDER:
> https://bitchute.com/alexandermercouris
>
> ALEX:
> https://bitchute.com/channel/izwNAdmMGIC7
>
> +++
>
> https://www.youtube.com/watch?v=gCj6CatE-u4
>

Accepted. The imperative visit, channel and donation purpose remain; further information is an additional purpose and excluded.

## F11-S1-t1

Subject: LeBron James potentially forcing a mid-season trade if Luka Dončić and the Los Angeles Lakers struggle throughout James’s 23rd NBA season.

> ⟦LeBron James may force mid-season trade if Luka, Lakers struggle throughout 23rd NBA campaign⟧ https://www.rawchili.com/nba/335643/ #Basketball #NBA
>
> https://media.channels.im/media_attachments/files/115/357/156/922/018/586/original/7ae81a6ab339ac82.webp

Accepted. The complete headline preserves LeBron's possible action, mid-season timing, conditional Luka/Lakers struggle and23rd NBA campaign. Links are excluded; the source's ordinary short names identify the fixed subject's expanded names.

## F11-S2-t1

Subject: NBA basketball.

> LeBron James may force mid-season trade if Luka, Lakers struggle throughout 23rd ⟦NBA⟧ campaign https://www.rawchili.com/nba/335643/ #Basketball #NBA
>
> https://media.channels.im/media_attachments/files/115/357/156/922/018/586/original/7ae81a6ab339ac82.webp

Accepted. NBA identifies the supplied basketball subject in this basketball post, without the trade claim. The abbreviation itself carries the sport identity; an additional Basketball token is not a required exact match.

The returned strings have 2 compatible placements; see all positions (`./batch-d/review.json`).

## F12-S1-t1

Subject: England.

> https://www.europesays.com/uk/771883/ Free career classes helping fight ageism #ageism #Britain #career #Charity #classes #⟦England⟧ #GreatBritain #local #london #News #Richmond #UK #UnitedKingdom #Work
>
> https://media.pubeurope.com/media_attachments/files/116/089/896/014/010/340/original/cb68aee34be1a736.jpg

Accepted. England is directly selected from the hashtag, without adding a relationship to the career classes.

## F12-S2-t1

Subject: Richmond.

> https://www.europesays.com/uk/771883/ Free career classes helping fight ageism #ageism #Britain #career #Charity #classes #England #GreatBritain #local #london #News #⟦Richmond⟧ #UK #UnitedKingdom #Work
>
> https://media.pubeurope.com/media_attachments/files/116/089/896/014/010/340/original/cb68aee34be1a736.jpg

Accepted. Richmond is directly selected from the hashtag, without inventing a more specific place or relationship.

## F13-S1-t1

Subject: Opera will follow Google Chrome in eliminating all workarounds that allow uBlock Origin to continue operating despite browser restrictions.

> Google ⟦Chrome⟧ is ⟦killing all uBlock Origin bypasses⟧, Microsoft Edge, ⟦Opera⟧ to ⟦follow⟧
> https://www.neowin.net/news/google-chrome-is-killing-all-ublock-origin-bypasses-microsoft-edge-opera-to-follow/

Accepted. Chrome identifies Google Chrome in the source; killing all uBlock Origin bypasses identifies the action Opera will follow. Opera and follow retain that relation without adding Microsoft Edge.

The returned strings have 2 compatible placements; see all positions (`./batch-d/review.json`). One alternative lies inside a URL, but the returned fragment is not itself a URL and no different scope is demonstrated.

## F13-S2-t1

Subject: Google Chrome is eliminating all workarounds that allow uBlock Origin to continue operating despite browser restrictions.

> Google ⟦Chrome⟧ is ⟦killing all uBlock Origin bypasses⟧, Microsoft Edge, Opera to follow
> https://www.neowin.net/news/google-chrome-is-killing-all-ublock-origin-bypasses-microsoft-edge-opera-to-follow/

Accepted. Chrome identifies the source's Google Chrome, and the complete action retains all uBlock Origin bypasses. The other browsers are excluded. Requiring the full branded name despite an unambiguous short name would be an exact-word rule.

## F14-S1-t1

Subject: Nostr is cool.

> nostr:nprofile1qqsfnz2sqsflkatdssmeztxr90s8xrd7r07xkhfwaa6eu9zkcguljpgpvemhxue69uhkv6tvw3jhytnwdaehgu3wwa5kuef0dec82c33ws6hwcecdqenwatgddsh2wt5wdmnsvnndfuxuer3xq6xgvmw8pcrvve5w468qerxweengardx4ux6apjwdckw6ekv34k20mzwfhkzerrv9ehg0t5wf6k2qgcwaehxw309akxjemgw3hxjmn8wfjkccte9e3k7mg86k9re + nostr:nprofile1qqsp8wgtgxvx8v438ea4prqxn2t7gnrqamayfsxuqc4zvnk63xgp08qpzemhxue69uhhyetvv9ujuerfw36x7tnsw43z7qgkwaehxw309aex2mrp0yh8qunfd4skctnwv46qpyqm5d or nostr:nprofile1qqsq36k72r04rkj2gt6acpz7xkehrypwqmt2spfpt0kr6ukudp7vkpqppemhxue69uhkummn9ekx7mp0qyg8wumn8ghj7mn0wd68ytnddakj7he2e0e
>
> Build whatever you want.
> ⟦Nostr⟧ is ⟦cool⟧.
> You know this. You're here.
>
>

Accepted. Nostr and cool retain the evaluation without the surrounding encouragement or encoded user identifiers.

## F14-S2-t1

Subject: Encouragement to build anything one wants.

> nostr:nprofile1qqsfnz2sqsflkatdssmeztxr90s8xrd7r07xkhfwaa6eu9zkcguljpgpvemhxue69uhkv6tvw3jhytnwdaehgu3wwa5kuef0dec82c33ws6hwcecdqenwatgddsh2wt5wdmnsvnndfuxuer3xq6xgvmw8pcrvve5w468qerxweengardx4ux6apjwdckw6ekv34k20mzwfhkzerrv9ehg0t5wf6k2qgcwaehxw309akxjemgw3hxjmn8wfjkccte9e3k7mg86k9re + nostr:nprofile1qqsp8wgtgxvx8v438ea4prqxn2t7gnrqamayfsxuqc4zvnk63xgp08qpzemhxue69uhhyetvv9ujuerfw36x7tnsw43z7qgkwaehxw309aex2mrp0yh8qunfd4skctnwv46qpyqm5d or nostr:nprofile1qqsq36k72r04rkj2gt6acpz7xkehrypwqmt2spfpt0kr6ukudp7vkpqppemhxue69uhkummn9ekx7mp0qyg8wumn8ghj7mn0wd68ytnddakj7he2e0e
>
> ⟦Build whatever you want.⟧
> Nostr is cool.
> You know this. You're here.
>
>

Accepted. The complete encouragement is retained without the Nostr evaluation or encoded identifiers.

## F15-S1-t1

Subject: GraphQL.

> [ papiche/UPassport ] ⟦GraphQL⟧ WoT v2
> https://github.com/papiche/UPassport/commit/6e5718f1183e2aeab07d1b0b4cb9d72d3e60303b

Accepted. GraphQL is selected directly without the version or ambiguous WoT abbreviation.

## F15-S2-t1

Subject: Version 2 of a GraphQL Web of Things.

> [ papiche/UPassport ] ⟦GraphQL WoT v2⟧
> https://github.com/papiche/UPassport/commit/6e5718f1183e2aeab07d1b0b4cb9d72d3e60303b

Accepted. GraphQL, WoT and v2 jointly retain the fixed supplied interpretation and version. The mask does not invent an expanded phrase or establish which WoT expansion the author uniquely intended; that limitation was recorded before masking.

## F16-S1-t1

Subject: The Bitcoin block at height 954796 has a block weight of 3993709.

> #⟦Bitcoin Block⟧ Art by Blockstr!
> ⟦Height: 954796⟧
> ⟦Weight: 3993709⟧
> https://thebitcoinblockclock.com/blockstr/000000000000000000023bcfa83c793411f7948a494ab61261ca86a8f9d8cc4f.png

Accepted. Bitcoin block identity, height and weight are retained without art attribution or URL content.

## F16-S2-t1

Subject: Art representing a Bitcoin block.

> #⟦Bitcoin Block Art⟧ by Blockstr!
> Height: 954796
> Weight: 3993709
> https://thebitcoinblockclock.com/blockstr/000000000000000000023bcfa83c793411f7948a494ab61261ca86a8f9d8cc4f.png

Accepted. Bitcoin Block Art retains the representation subject without the specific block's fields or creator credit.

## F17-S1-t1

Subject: An unsupervised sentiment neuron.

> too early to judge "⟦Unsupervised sentiment neuron⟧".
>
> https://openai.com/index/unsupervised-sentiment-neuron

Accepted. The named unsupervised sentiment neuron is retained without the timing judgment.

## F17-S2-t1

Subject: It is too early to judge the unsupervised sentiment neuron.

> ⟦too early⟧ to ⟦judge⟧ "⟦Unsupervised sentiment neuron⟧".
>
> https://openai.com/index/unsupervised-sentiment-neuron

Accepted. Too early, judge and the named subject retain the timing judgment without a URL. Removed function words do not change the meaning in the complete source.

## F18-S1-t1

Subject: Satellite-based text messaging.

> Google Pixel ⟦Satellite Texting⟧ Expands to a New Market
> https://www.androidheadlines.com/2025/11/google-pixel-satellite-texting-expands-to-a-new-market.html

Accepted. Satellite Texting directly supplies the general messaging subject without brand or market expansion.

## F18-S2-t1

Subject: Expansion of Google Pixel satellite texting into a new market.

> ⟦Google Pixel Satellite Texting Expands⟧ to a ⟦New Market⟧
> https://www.androidheadlines.com/2025/11/google-pixel-satellite-texting-expands-to-a-new-market.html

Accepted. The full named feature, expansion and new market are retained. The omitted grammatical preposition/article add no separate meaning.

## F19-S1-t1

Subject: A plea to Capcom not to kill Leon Kennedy in Resident Evil Requiem.

> Dear ⟦Capcom⟧, ⟦please don't kill Leon Kennedy in Resident Evil Requiem⟧
> https://www.xda-developers.com/dear-capcom-please-dont-kill-leon-kennedy-in-resident-evil-requiem/

Accepted. Capcom, the plea and negative injunction, character and game are retained; the plea is not turned into an endorsement of killing.

## F19-S2-t1

Subject: Leon Kennedy’s survival or death in Resident Evil Requiem.

> Dear Capcom, please don't ⟦kill Leon Kennedy⟧ in ⟦Resident Evil Requiem⟧
> https://www.xda-developers.com/dear-capcom-please-dont-kill-leon-kennedy-in-resident-evil-requiem/

Accepted. Kill Leon Kennedy plus the game identifies the character's life/death stakes, matching this subject about fate rather than the separate plea. In the complete source this is not an assertion that he dies or an instruction to kill him; the request-specific wording is outside the fixed subject.

## F20-S1-t1

Subject: Bijou expresses fear in the context of Resident Evil Requiem.

> 【10日10:00 - #ホロライブ】
>
> 『【⟦RESIDENT EVIL REQUIEM⟧】LEON COME BACK I'M ⟦SCARED⟧【Spoilers Ahead】』
>
> ライバー: #⟦Bijou⟧
> https://www.youtube.com/watch?v=d_aSgNfznsI
>
> https://media.misskeyusercontent.com/io/ea0a97cc-9dd0-4741-a0b3-81c9eee93700.jpg?sensitive=true

Accepted. The game, fear expression and named streamer preserve the attribution in the full title/streamer context, without the separate request for Leon's return.

## F20-S2-t1

Subject: Bijou calls for Leon from Resident Evil Requiem to come back.

> 【10日10:00 - #ホロライブ】
>
> 『【⟦RESIDENT EVIL REQUIEM⟧】⟦LEON COME BACK⟧ I'M SCARED【Spoilers Ahead】』
>
> ライバー: #⟦Bijou⟧
> https://www.youtube.com/watch?v=d_aSgNfznsI
>
> https://media.misskeyusercontent.com/io/ea0a97cc-9dd0-4741-a0b3-81c9eee93700.jpg?sensitive=true

Accepted. The game, Leon's requested return and named streamer preserve the call and attribution, without the separate fear expression.

See conversion gaps (`03bd9e45:docs/experiments/publication-gaps.csv`) for `collection:tracked-mask-prompt-goal-v1`.
