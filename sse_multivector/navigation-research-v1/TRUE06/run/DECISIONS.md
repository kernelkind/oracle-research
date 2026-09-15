# TRUE06 — Every frozen holdout decision

Each row asks **A contains B?** B is the premise; A is the hypothesis. All inputs use the unchanged TRUE01 topic sentence wrapper.

Native answers are complete greedy labels with EOS required. Score is full-vocabulary probability of the first output token being `1`, not calibrated category confidence. The separately frozen cutoff verdict is **score > 0.142**; no cutoff was fitted here.

| ID | A | B | Expected | Native | Score | Cutoff |
|---|---|---|---|---|---|---|
| P01-a-contains-b | Food | Brisket | Yes | Yes | 0.626476 | Yes |
| P01-b-contains-a | Brisket | Food | No | No | 0.012057 | No |
| P02-a-contains-b | Food | Raw Milk | Yes | Yes | 0.525075 | Yes |
| P02-b-contains-a | Raw Milk | Food | No | No | 0.001752 | No |
| P03-a-contains-b | Food Preparation and Dining | Making Chicken Stock | Yes | No | 0.163581 | Yes |
| P03-b-contains-a | Making Chicken Stock | Food Preparation and Dining | No | No | 0.002538 | No |
| P04-a-contains-b | Foods featuring meat or seafood | Meat-based meals in a crockpot | Yes | No | 0.277598 | Yes |
| P04-b-contains-a | Meat-based meals in a crockpot | Foods featuring meat or seafood | No | No | 0.004974 | No |
| P05-a-contains-b | Coffee | Coffee Bean Preparation | Yes | Yes | 0.836168 | Yes |
| P05-b-contains-a | Coffee Bean Preparation | Coffee | No | No | 0.017445 | No |
| P06-a-contains-b | Coffee | Appreciating Coffee for Its Flavour | Yes | Yes | 0.968358 | Yes |
| P06-b-contains-a | Appreciating Coffee for Its Flavour | Coffee | No | No | 0.008152 | No |
| P07-a-contains-b | Bitcoin | Satoshis: Bitcoin’s Smallest Units | Yes | No | 0.106547 | No |
| P07-b-contains-a | Satoshis: Bitcoin’s Smallest Units | Bitcoin | No | No | 0.000643 | No |
| P08-a-contains-b | Coffee Bean Preparation | Appreciating Coffee for Its Flavour | No | No | 0.001406 | No |
| P08-b-contains-a | Appreciating Coffee for Its Flavour | Coffee Bean Preparation | No | No | 0.000385 | No |
| P09-a-contains-b | Visual Art | Music at Coffee Shops | No | No | 0.000611 | No |
| P09-b-contains-a | Music at Coffee Shops | Visual Art | No | No | 0.000399 | No |
| P10-a-contains-b | Foods featuring meat or seafood | Butter as part of a meal | No | No | 0.001490 | No |
| P10-b-contains-a | Butter as part of a meal | Foods featuring meat or seafood | No | No | 0.000830 | No |
| P11-a-contains-b | Coffee | Having drunk coffee | Yes | Yes | 0.870951 | Yes |
| P11-b-contains-a | Having drunk coffee | Coffee | No | No | 0.037948 | No |
| P12-a-contains-b | Food consumption | Meat eating | Yes | Yes | 0.740588 | Yes |
| P12-b-contains-a | Meat eating | Food consumption | No | No | 0.012094 | No |

## Native errors (3)

- P03-a-contains-b: expected Yes; got No; score 0.163581.
- P04-a-contains-b: expected Yes; got No; score 0.277598.
- P07-a-contains-b: expected Yes; got No; score 0.106547.

## Cutoff errors (1)

- P07-a-contains-b: expected Yes; got No; score 0.106547.
