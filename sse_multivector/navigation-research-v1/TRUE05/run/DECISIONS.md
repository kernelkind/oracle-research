# TRUE05 — Every frozen holdout decision

Each row asks **A contains B?** B is the premise; A is the hypothesis. All inputs use the unchanged TRUE01 topic sentence wrapper.

Native answers are complete greedy labels with EOS required. Score is full-vocabulary probability of the first output token being `1`, not calibrated category confidence. The separately frozen cutoff verdict is **score > 0.142**; no cutoff was fitted here.

| ID | A | B | Expected | Native | Score | Cutoff |
|---|---|---|---|---|---|---|
| U001-a-contains-b | Feedback on how food recipes turn out | Meat-based meals in a crockpot | No | No | 0.002216 | No |
| U001-b-contains-a | Meat-based meals in a crockpot | Feedback on how food recipes turn out | No | No | 0.000310 | No |
| U023-a-contains-b | Foods featuring meat or seafood | Raw Milk | No | No | 0.001817 | No |
| U023-b-contains-a | Raw Milk | Foods featuring meat or seafood | No | No | 0.000520 | No |
| U024-a-contains-b | Foods featuring meat or seafood | Meals featuring potatoes, other vegetables, and animal-based protein | No | No | 0.141284 | No |
| U024-b-contains-a | Meals featuring potatoes, other vegetables, and animal-based protein | Foods featuring meat or seafood | No | No | 0.002000 | No |
| U026-a-contains-b | Foods featuring meat or seafood | Steak | Yes | No | 0.123574 | No |
| U026-b-contains-a | Steak | Foods featuring meat or seafood | No | No | 0.023683 | No |
| U028-a-contains-b | Foods featuring meat or seafood | Butter as part of a meal | No | No | 0.001490 | No |
| U028-b-contains-a | Butter as part of a meal | Foods featuring meat or seafood | No | No | 0.000830 | No |
| U040-a-contains-b | Visual Art | Music at Coffee Shops | No | No | 0.000611 | No |
| U040-b-contains-a | Music at Coffee Shops | Visual Art | No | No | 0.000399 | No |

## Native errors (1)

- U026-a-contains-b: expected Yes; got No; score 0.123574.

## Cutoff errors (1)

- U026-a-contains-b: expected Yes; got No; score 0.123574.
