# TRUE08 — Every frozen holdout decision

Each row asks **A contains B?** B is the premise; A is the hypothesis. All inputs use the unchanged TRUE01 topic sentence wrapper.

Native answers are complete greedy labels with EOS required. Score is full-vocabulary probability of the first output token being `1`, not calibrated category confidence. The separately frozen cutoff verdict is **score > 0.142**; no cutoff was fitted here.

| ID | A | B | Expected | Native | Score | Cutoff |
|---|---|---|---|---|---|---|
| P01-a-contains-b | Foods featuring meat or seafood | Steak | Yes | No | 0.123574 | No |
| P01-b-contains-a | Steak | Foods featuring meat or seafood | No | No | 0.023683 | No |
| P02-a-contains-b | Foods featuring meat or seafood | Brisket | Yes | No | 0.149946 | Yes |
| P02-b-contains-a | Brisket | Foods featuring meat or seafood | No | No | 0.008630 | No |
| P03-a-contains-b | Foods featuring meat or seafood | Roast chicken | Yes | No | 0.147434 | Yes |
| P03-b-contains-a | Roast chicken | Foods featuring meat or seafood | No | No | 0.011376 | No |
| P04-a-contains-b | Foods featuring meat or seafood | Grilled salmon | Yes | No | 0.199981 | Yes |
| P04-b-contains-a | Grilled salmon | Foods featuring meat or seafood | No | No | 0.022052 | No |
| P05-a-contains-b | Foods featuring meat or seafood | Shrimp dishes | Yes | No | 0.084175 | No |
| P05-b-contains-a | Shrimp dishes | Foods featuring meat or seafood | No | No | 0.010839 | No |
| P06-a-contains-b | Foods featuring meat or seafood | Plain boiled rice | No | No | 0.001050 | No |
| P06-b-contains-a | Plain boiled rice | Foods featuring meat or seafood | No | No | 0.000372 | No |
| P07-a-contains-b | Foods featuring meat or seafood | Fresh fruit | No | No | 0.000371 | No |
| P07-b-contains-a | Fresh fruit | Foods featuring meat or seafood | No | No | 0.000545 | No |
| P08-a-contains-b | Foods featuring meat or seafood | Vegan meals | No | No | 0.000440 | No |
| P08-b-contains-a | Vegan meals | Foods featuring meat or seafood | No | No | 0.000652 | No |

## Native errors (5)

- P01-a-contains-b: expected Yes; got No; score 0.123574.
- P02-a-contains-b: expected Yes; got No; score 0.149946.
- P03-a-contains-b: expected Yes; got No; score 0.147434.
- P04-a-contains-b: expected Yes; got No; score 0.199981.
- P05-a-contains-b: expected Yes; got No; score 0.084175.

## Cutoff errors (2)

- P01-a-contains-b: expected Yes; got No; score 0.123574.
- P05-a-contains-b: expected Yes; got No; score 0.084175.
