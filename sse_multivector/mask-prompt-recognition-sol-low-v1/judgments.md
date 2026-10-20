# Mask recognition — full results

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

Each ID below is one fixed mask. Every call received the complete note with that mask highlighted and the same supplied subject. It did not receive the expected judgment, another mask, or earlier answers.

Sol low judged each mask three times in fresh contexts. `missing_meaning` lists required meaning absent from the mask; `additional_meaning` lists meaning outside the supplied subject. An empty array means the model reported no issue of that kind.

The expected judgments were recorded before the calls. My analysis below is separate from your saved decisions. Source files and review provenance are in `./expected-judgments.json`.

## M05-1: Meditation — life is included

Subject: Meditation is the very understanding of life.

You approved this highlighted mask in the v3 review.

> "⟦Meditation⟧ is not a withdrawal from ⟦life⟧ but ⟦the very understanding of⟧ it."
>
> — Jiddu Krishnamurti, The First and Last Freedom (1954)
>
> https://post.noblegrowth.co/uploads/2026/05/27/2810eb2e17e3cf218105ffe60f8dab10df.mp4

Trials 1, 2, 3:

```json
{"missing_meaning":[],"additional_meaning":[]}
```

Analysis: All three calls reported no issue, agreeing with the saved decision. The mask includes both the subject, meditation, and the concrete referent, life. Its fragments do not form grammatical prose, but that was explicitly allowed.

## M05-2: Meditation — life is missing

Subject: Meditation is the very understanding of life.

You rejected this highlighted mask in the v4 review. The missing-life explanation below is my reading of that decision, not a comment attributed to you.

> "⟦Meditation⟧ is not a withdrawal from life but ⟦the very understanding of it⟧."
>
> — Jiddu Krishnamurti, The First and Last Freedom (1954)
>
> https://post.noblegrowth.co/uploads/2026/05/27/2810eb2e17e3cf218105ffe60f8dab10df.mp4

Trials 1, 2, 3:

```json
{"missing_meaning":[],"additional_meaning":[]}
```

Analysis: All three calls missed the problem. The subject explicitly concerns understanding life, but the mask contains only “it” where life should be identified. The complete post resolves the reference; that does not put the word life inside the mask. The approved criteria explicitly required the source words identifying the referent. The model gave the same no-issue judgment to M05-1 and M05-2, so this check did not distinguish those two masks. The outputs do not tell us why.

## M07-1: Insurance — supplied subject only

Subject: Hormuz Safe uses Bitcoin and other cryptocurrencies for maritime-insurance settlements.

This is an existing generated mask checked by me, not a new approval from you.

> Three weeks ago, Tether froze $344 million in USDT linked to Iran's Central Bank. The largest sovereign stablecoin seizure on record.
>
> Last week, Iran launched ⟦Hormuz Safe⟧, a state-backed platform for ⟦maritime insurance settlements using Bitcoin and other cryptocurrencies⟧.
>
> The timing is not coincidental. When stablecoins can be frozen with a single compliance request, they stop being reliable for anyone operating outside the system. Bitcoin has no central issuer, no blacklist function, and no way for a third party to remotely seize or freeze the funds.
>
> This is why restricted actors are shifting toward it for settlement. Not because it is better money in normal conditions, but because it remains usable when every other rail can be cut.
>
> The question is how many more will reach the same conclusion as enforcement tightens.
> https://blossom.primal.net/7ecc22b10e39179a2354abe724f5cc51e4c8d4a6f88e5a0a7f3b9b00b2a9fa63.png

Trials 1, 2, 3:

```json
{"missing_meaning":[],"additional_meaning":[]}
```

Analysis: All three calls reported no issue, agreeing with the pre-run assistant judgment. The fragments name Hormuz Safe and its cryptocurrency-insurance use. They exclude the separate state-backing description.

## M07-2: Insurance — state backing added

Subject: Hormuz Safe uses Bitcoin and other cryptocurrencies for maritime-insurance settlements.

You rejected this highlighted mask in the v3 review; the same issue was retained in v4.

> Three weeks ago, Tether froze $344 million in USDT linked to Iran's Central Bank. The largest sovereign stablecoin seizure on record.
>
> Last week, Iran launched ⟦Hormuz Safe⟧, ⟦a state-backed platform for maritime insurance settlements using Bitcoin and other cryptocurrencies⟧.
>
> The timing is not coincidental. When stablecoins can be frozen with a single compliance request, they stop being reliable for anyone operating outside the system. Bitcoin has no central issuer, no blacklist function, and no way for a third party to remotely seize or freeze the funds.
>
> This is why restricted actors are shifting toward it for settlement. Not because it is better money in normal conditions, but because it remains usable when every other rail can be cut.
>
> The question is how many more will reach the same conclusion as enforcement tightens.
> https://blossom.primal.net/7ecc22b10e39179a2354abe724f5cc51e4c8d4a6f88e5a0a7f3b9b00b2a9fa63.png

Trial 1:

```json
{"missing_meaning":[],"additional_meaning":["The mask adds that Hormuz Safe is state-backed, which is not part of the supplied subject."]}
```

Trial 2:

```json
{"missing_meaning":[],"additional_meaning":["The mask additionally states that Hormuz Safe is a state-backed platform, which is outside the supplied subject."]}
```

Trial 3:

```json
{"missing_meaning":[],"additional_meaning":["The mask additionally states that Hormuz Safe is state-backed, which is not part of the supplied subject."]}
```

Analysis: All three calls identified the actual added meaning: state backing. The supplied subject names the platform and its use of cryptocurrencies for maritime-insurance settlements; it does not include who backs the platform. These are detections of the recorded problem, not rejections for an invented reason. Together with M07-1, this is one subject for which the recognizer consistently distinguished the acceptable and overinclusive masks.

## M09-1: Bitcoin — value under restrictions

Subject: Bitcoin’s value to restricted actors lies in its continued usability under financial restrictions rather than its ordinary monetary superiority.

You approved this highlighted mask in the v4 review.

> Three weeks ago, Tether froze $344 million in USDT linked to Iran's Central Bank. The largest sovereign stablecoin seizure on record.
>
> Last week, Iran launched Hormuz Safe, a state-backed platform for maritime insurance settlements using ⟦Bitcoin⟧ and other cryptocurrencies.
>
> The timing is not coincidental. When stablecoins can be frozen with a single compliance request, they stop being reliable for anyone operating outside the system. Bitcoin has no central issuer, no blacklist function, and no way for a third party to remotely seize or freeze the funds.
>
> This is why ⟦restricted actors⟧ are shifting toward it for settlement. ⟦Not because it is better money in normal conditions, but because it remains usable when every other rail can be cut⟧.
>
> The question is how many more will reach the same conclusion as enforcement tightens.
> https://blossom.primal.net/7ecc22b10e39179a2354abe724f5cc51e4c8d4a6f88e5a0a7f3b9b00b2a9fa63.png

Trials 1, 2, 3:

```json
{"missing_meaning":[],"additional_meaning":[]}
```

Analysis: All three calls reported no issue, agreeing with the saved decision. The mask identifies Bitcoin and restricted actors, then includes the contrast between ordinary monetary superiority and remaining usable when payment routes can be cut. It leaves the separate statement about actors actually shifting to Bitcoin outside the mask.

## M09-2: Bitcoin — actual settlement activity added

Subject: Bitcoin’s value to restricted actors lies in its continued usability under financial restrictions rather than its ordinary monetary superiority.

You rejected this mask in medium trial 3 and confirmed that rejection in chat.

> Three weeks ago, Tether froze $344 million in USDT linked to Iran's Central Bank. The largest sovereign stablecoin seizure on record.
>
> Last week, Iran launched Hormuz Safe, a state-backed platform for maritime insurance settlements using ⟦Bitcoin⟧ and other cryptocurrencies.
>
> The timing is not coincidental. When stablecoins can be frozen with a single compliance request, they stop being reliable for anyone operating outside the system. Bitcoin has no central issuer, no blacklist function, and no way for a third party to remotely seize or freeze the funds.
>
> This is why ⟦restricted actors are shifting toward it for settlement⟧. ⟦Not because it is better money in normal conditions, but because it remains usable when every other rail can be cut⟧.
>
> The question is how many more will reach the same conclusion as enforcement tightens.
> https://blossom.primal.net/7ecc22b10e39179a2354abe724f5cc51e4c8d4a6f88e5a0a7f3b9b00b2a9fa63.png

Trial 1:

```json
{"missing_meaning":[],"additional_meaning":[]}
```

Trial 2:

```json
{"missing_meaning":[],"additional_meaning":["The mask additionally states that restricted actors are shifting toward Bitcoin specifically for settlement, which is not part of the supplied subject."]}
```

Trial 3:

```json
{"missing_meaning":[],"additional_meaning":["Restricted actors are actively shifting toward Bitcoin specifically for settlement, an adoption claim beyond the subject’s statement about Bitcoin’s value to them."]}
```

Analysis: Trial 1 missed the extra meaning. Trials 2 and 3 correctly identified the statement that actors are actually shifting to Bitcoin for settlement. That statement is related to why Bitcoin is useful under restrictions, but it adds an adoption claim outside the fixed subject, matching the saved rejection. With the same input, recognition was inconsistent: two detections and one miss.

## What this establishes

The checker detected state backing in all three trials and the added settlement activity in two. It never detected the missing life reference. It raised no false alarms on the three acceptable masks across their nine calls.

That is evidence of selective, incomplete recognition—not a reliable checker. The test does not explain why generation fails or establish results beyond these six reused masks. No generated mask was repaired, no prompt default changed, and no new user approval was recorded.

See [conversion gaps](../../docs/experiments/publication-gaps.csv) for `collection:tracked-mask-prompt-recognition-sol-low-v1`.
