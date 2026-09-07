# Initial mask results

Five of six masks accepted. M05 includes one additional meaning. This is the first three-note batch, not completed validation; no repeated calls or prompt edits have been made.

All six calls used Astra low with fresh context. The complete source note and one unchanged ASv6.23 subject were supplied each time. The auxiliary context field was not supplied. Nothing below was hand-corrected.

## M01

Subject: Bitcoin block at height 949680.

> ⟦bitcoin block
> height 949680⟧
> network fee 3 sats/vB
> price 78170.1 usd
> moscow time 1279 sats
>
> #bitcoin #block #day 6595

Accept. The mask identifies Bitcoin, the block and its exact height, without taking the other status fields.

## M02

Subject: Bitcoin network transaction fee rate of 3 satoshis per virtual byte.

> ⟦bitcoin⟧ block
> height 949680
> ⟦network fee 3 sats/vB⟧
> price 78170.1 usd
> moscow time 1279 sats
>
> #bitcoin #block #day 6595

Accept. The two fragments supply Bitcoin context and the fee value/unit. Source order fixes the first fragment to the opening word, not the later hashtag.

## M03

Subject: Aurora Innovations’ self-driving trucks can now travel nonstop.

> Is a career in long-haul trucking soon to be a thing of the past? ⟦Aurora Innovations’ self-driving trucks can now travel nonstop⟧ on a 1,000-mile route between Fort Worth and Phoenix — exceeding what a human driver can legally accomplish. Read more from nostr:nprofile1qy2hwumn8ghj7un9d3shjtnyd968gmewwp6kyqpqnm0yhmfzsafedypm7ya8lkhskhhmerf05x5u3pw66fycy5z672gs37h0ra:
>
> https://flip.it/ZYkgKU
>
> #Tech #AuroraInnovations #Transportation #SelfDriving #Technology

Accept. It keeps the company, self-driving trucks and nonstop capability; the route and human-driver comparison remain outside this narrower mask.

## M04

Subject: Aurora Innovations’ self-driving trucks’ ability to travel nonstop on a 1,000-mile route between Fort Worth and Phoenix exceeds what a human driver can legally accomplish.

> Is a career in long-haul trucking soon to be a thing of the past? ⟦Aurora Innovations’ self-driving trucks can now travel nonstop on a 1,000-mile route between Fort Worth and Phoenix — exceeding what a human driver can legally accomplish.⟧ Read more from nostr:nprofile1qy2hwumn8ghj7un9d3shjtnyd968gmewwp6kyqpqnm0yhmfzsafedypm7ya8lkhskhhmerf05x5u3pw66fycy5z672gs37h0ra:
>
> https://flip.it/ZYkgKU
>
> #Tech #AuroraInnovations #Transportation #SelfDriving #Technology

Accept. The selected sentence covers the complete route-and-capability comparison requested by this fuller subject.

## M05

Subject: A call for Salvadorans to make their presence known.

> ⟦Where are all
> My Salvadorans at?⟧
> https://blossom.primal.net/2b5ac7389e0863fcc843a67abf667a024f4e8f79310cbe048a3e3141bfecedca.jpg

Scope error. The call is present, but “My” also expresses the author's affinity with Salvadorans. That additional meaning is not part of this fixed subject; it is the meaning requested separately by M06. This is a small masking error, not an unsupported subject or an identifier problem.

## M06

Subject: The poster's expressed affinity with Salvadorans.

> Where are all
> ⟦My Salvadorans⟧ at?
> https://blossom.primal.net/2b5ac7389e0863fcc843a67abf667a024f4e8f79310cbe048a3e3141bfecedca.jpg

Accept. “My Salvadorans” supplies the affinity cue and its audience without asserting the author's nationality.

## What follows

Keep the prompt unchanged and add three notes that exercise different masking difficulties. Reserve the separate final inputs first, as the approved plan requires. Track the M05 scope error in later trials; do not rerun it to replace this result.

Generation used 14,861 input tokens and 136 output tokens; 1,920 input tokens were cached. These are the six mask calls only, not review or orchestration usage. All six calls had distinct threads and working directories, with tools and web search disabled. Memory and I/O pressure stayed at zero in the recorded samples.

[Raw review](./review.json) · [Mechanical and isolation checks](./verification.json) · [Execution record](./execution/results.json)
