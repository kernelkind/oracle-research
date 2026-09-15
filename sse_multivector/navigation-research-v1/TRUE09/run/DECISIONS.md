# TRUE09 — Every frozen holdout decision

Each row asks **A contains B?** B is the premise; A is the hypothesis. All inputs use the unchanged TRUE01 topic sentence wrapper.

Native answers are complete greedy labels with EOS required. Score is full-vocabulary probability of the first output token being `1`, not calibrated category confidence. The separately frozen cutoff verdict is **score > 0.142**; no cutoff was fitted here.

| ID | A | B | Expected | Native | Score | Cutoff |
|---|---|---|---|---|---|---|
| P01-M-a-contains-b | Meat | Steak | Yes | Yes | 0.626187 | Yes |
| P01-M-b-contains-a | Steak | Meat | No | No | 0.026186 | No |
| P01-MF-a-contains-b | Foods featuring meat | Steak | Yes | No | 0.398649 | Yes |
| P01-MF-b-contains-a | Steak | Foods featuring meat | No | No | 0.018786 | No |
| P01-U-a-contains-b | Meat or seafood | Steak | Yes | No | 0.212263 | Yes |
| P01-U-b-contains-a | Steak | Meat or seafood | No | No | 0.034485 | No |
| P01-UF-a-contains-b | Foods featuring meat or seafood | Steak | Yes | No | 0.123574 | No |
| P01-UF-b-contains-a | Steak | Foods featuring meat or seafood | No | No | 0.023683 | No |
| P02-M-a-contains-b | Meat | Brisket | Yes | Yes | 0.569453 | Yes |
| P02-M-b-contains-a | Brisket | Meat | No | No | 0.021851 | No |
| P02-MF-a-contains-b | Foods featuring meat | Brisket | Yes | No | 0.428051 | Yes |
| P02-MF-b-contains-a | Brisket | Foods featuring meat | No | No | 0.011443 | No |
| P02-U-a-contains-b | Meat or seafood | Brisket | Yes | No | 0.159273 | Yes |
| P02-U-b-contains-a | Brisket | Meat or seafood | No | No | 0.019451 | No |
| P02-UF-a-contains-b | Foods featuring meat or seafood | Brisket | Yes | No | 0.149946 | Yes |
| P02-UF-b-contains-a | Brisket | Foods featuring meat or seafood | No | No | 0.008630 | No |
| P03-M-a-contains-b | Meat | Roast chicken | Yes | Yes | 0.516898 | Yes |
| P03-M-b-contains-a | Roast chicken | Meat | No | No | 0.006901 | No |
| P03-MF-a-contains-b | Foods featuring meat | Roast chicken | Yes | No | 0.413524 | Yes |
| P03-MF-b-contains-a | Roast chicken | Foods featuring meat | No | No | 0.009950 | No |
| P03-U-a-contains-b | Meat or seafood | Roast chicken | Yes | No | 0.433770 | Yes |
| P03-U-b-contains-a | Roast chicken | Meat or seafood | No | No | 0.010586 | No |
| P03-UF-a-contains-b | Foods featuring meat or seafood | Roast chicken | Yes | No | 0.147434 | Yes |
| P03-UF-b-contains-a | Roast chicken | Foods featuring meat or seafood | No | No | 0.011376 | No |
| P04-S-a-contains-b | Seafood | Grilled salmon | Yes | Yes | 0.566964 | Yes |
| P04-S-b-contains-a | Grilled salmon | Seafood | No | No | 0.017782 | No |
| P04-SF-a-contains-b | Foods featuring seafood | Grilled salmon | Yes | No | 0.430938 | Yes |
| P04-SF-b-contains-a | Grilled salmon | Foods featuring seafood | No | No | 0.016891 | No |
| P04-U-a-contains-b | Meat or seafood | Grilled salmon | Yes | No | 0.484351 | Yes |
| P04-U-b-contains-a | Grilled salmon | Meat or seafood | No | No | 0.027432 | No |
| P04-UF-a-contains-b | Foods featuring meat or seafood | Grilled salmon | Yes | No | 0.199981 | Yes |
| P04-UF-b-contains-a | Grilled salmon | Foods featuring meat or seafood | No | No | 0.022052 | No |
| P05-S-a-contains-b | Seafood | Shrimp dishes | Yes | Yes | 0.541128 | Yes |
| P05-S-b-contains-a | Shrimp dishes | Seafood | No | No | 0.009366 | No |
| P05-SF-a-contains-b | Foods featuring seafood | Shrimp dishes | Yes | Yes | 0.589476 | Yes |
| P05-SF-b-contains-a | Shrimp dishes | Foods featuring seafood | No | No | 0.013103 | No |
| P05-U-a-contains-b | Meat or seafood | Shrimp dishes | Yes | No | 0.096785 | No |
| P05-U-b-contains-a | Shrimp dishes | Meat or seafood | No | No | 0.009070 | No |
| P05-UF-a-contains-b | Foods featuring meat or seafood | Shrimp dishes | Yes | No | 0.084175 | No |
| P05-UF-b-contains-a | Shrimp dishes | Foods featuring meat or seafood | No | No | 0.010839 | No |
| P06-M-a-contains-b | Meat | Plain boiled rice | No | No | 0.000661 | No |
| P06-M-b-contains-a | Plain boiled rice | Meat | No | No | 0.000556 | No |
| P06-MF-a-contains-b | Foods featuring meat | Plain boiled rice | No | No | 0.000979 | No |
| P06-MF-b-contains-a | Plain boiled rice | Foods featuring meat | No | No | 0.000548 | No |
| P06-S-a-contains-b | Seafood | Plain boiled rice | No | No | 0.000960 | No |
| P06-S-b-contains-a | Plain boiled rice | Seafood | No | No | 0.000338 | No |
| P06-SF-a-contains-b | Foods featuring seafood | Plain boiled rice | No | No | 0.001484 | No |
| P06-SF-b-contains-a | Plain boiled rice | Foods featuring seafood | No | No | 0.000394 | No |
| P06-U-a-contains-b | Meat or seafood | Plain boiled rice | No | No | 0.000941 | No |
| P06-U-b-contains-a | Plain boiled rice | Meat or seafood | No | No | 0.000266 | No |
| P06-UF-a-contains-b | Foods featuring meat or seafood | Plain boiled rice | No | No | 0.001050 | No |
| P06-UF-b-contains-a | Plain boiled rice | Foods featuring meat or seafood | No | No | 0.000372 | No |
| P07-M-a-contains-b | Meat | Fresh fruit | No | No | 0.000490 | No |
| P07-M-b-contains-a | Fresh fruit | Meat | No | No | 0.000672 | No |
| P07-MF-a-contains-b | Foods featuring meat | Fresh fruit | No | No | 0.000380 | No |
| P07-MF-b-contains-a | Fresh fruit | Foods featuring meat | No | No | 0.000664 | No |
| P07-S-a-contains-b | Seafood | Fresh fruit | No | No | 0.000436 | No |
| P07-S-b-contains-a | Fresh fruit | Seafood | No | No | 0.000829 | No |
| P07-SF-a-contains-b | Foods featuring seafood | Fresh fruit | No | No | 0.000633 | No |
| P07-SF-b-contains-a | Fresh fruit | Foods featuring seafood | No | No | 0.000724 | No |
| P07-U-a-contains-b | Meat or seafood | Fresh fruit | No | No | 0.000482 | No |
| P07-U-b-contains-a | Fresh fruit | Meat or seafood | No | No | 0.000508 | No |
| P07-UF-a-contains-b | Foods featuring meat or seafood | Fresh fruit | No | No | 0.000371 | No |
| P07-UF-b-contains-a | Fresh fruit | Foods featuring meat or seafood | No | No | 0.000545 | No |
| P08-M-a-contains-b | Meat | Vegan meals | No | No | 0.000819 | No |
| P08-M-b-contains-a | Vegan meals | Meat | No | No | 0.001035 | No |
| P08-MF-a-contains-b | Foods featuring meat | Vegan meals | No | No | 0.000515 | No |
| P08-MF-b-contains-a | Vegan meals | Foods featuring meat | No | No | 0.000755 | No |
| P08-S-a-contains-b | Seafood | Vegan meals | No | No | 0.000404 | No |
| P08-S-b-contains-a | Vegan meals | Seafood | No | No | 0.000347 | No |
| P08-SF-a-contains-b | Foods featuring seafood | Vegan meals | No | No | 0.000357 | No |
| P08-SF-b-contains-a | Vegan meals | Foods featuring seafood | No | No | 0.000421 | No |
| P08-U-a-contains-b | Meat or seafood | Vegan meals | No | No | 0.000489 | No |
| P08-U-b-contains-a | Vegan meals | Meat or seafood | No | No | 0.000661 | No |
| P08-UF-a-contains-b | Foods featuring meat or seafood | Vegan meals | No | No | 0.000440 | No |
| P08-UF-b-contains-a | Vegan meals | Foods featuring meat or seafood | No | No | 0.000652 | No |

## Native errors (14)

- P01-MF-a-contains-b: expected Yes; got No; score 0.398649.
- P01-U-a-contains-b: expected Yes; got No; score 0.212263.
- P01-UF-a-contains-b: expected Yes; got No; score 0.123574.
- P02-MF-a-contains-b: expected Yes; got No; score 0.428051.
- P02-U-a-contains-b: expected Yes; got No; score 0.159273.
- P02-UF-a-contains-b: expected Yes; got No; score 0.149946.
- P03-MF-a-contains-b: expected Yes; got No; score 0.413524.
- P03-U-a-contains-b: expected Yes; got No; score 0.433770.
- P03-UF-a-contains-b: expected Yes; got No; score 0.147434.
- P04-SF-a-contains-b: expected Yes; got No; score 0.430938.
- P04-U-a-contains-b: expected Yes; got No; score 0.484351.
- P04-UF-a-contains-b: expected Yes; got No; score 0.199981.
- P05-U-a-contains-b: expected Yes; got No; score 0.096785.
- P05-UF-a-contains-b: expected Yes; got No; score 0.084175.

## Cutoff errors (3)

- P01-UF-a-contains-b: expected Yes; got No; score 0.123574.
- P05-U-a-contains-b: expected Yes; got No; score 0.096785.
- P05-UF-a-contains-b: expected Yes; got No; score 0.084175.
