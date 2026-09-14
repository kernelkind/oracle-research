# TRUE03 — Every frozen holdout decision

Each row asks **A contains B?** B is the premise; A is the hypothesis. All inputs use the unchanged TRUE01 topic sentence wrapper.

Native answers are complete greedy labels with EOS required. Score is full-vocabulary probability of the first output token being `1`, not calibrated category confidence. The separately frozen cutoff verdict is **score > 0.142**; no cutoff was fitted here.

| ID | A | B | Expected | Native | Score | Cutoff |
|---|---|---|---|---|---|---|
| P01-a-contains-b | Coffee | Coffee Bean Preparation | Yes | Yes | 0.836168 | Yes |
| P01-b-contains-a | Coffee Bean Preparation | Coffee | No | No | 0.017445 | No |
| P02-a-contains-b | Coffee | Coffee Consumption | Yes | Yes | 0.966989 | Yes |
| P02-b-contains-a | Coffee Consumption | Coffee | No | No | 0.186424 | Yes |
| P03-a-contains-b | Coffee | Appreciating Coffee for Its Flavor | Yes | Yes | 0.967635 | Yes |
| P03-b-contains-a | Appreciating Coffee for Its Flavor | Coffee | No | No | 0.007997 | No |
| P04-a-contains-b | Coffee Bean Preparation | Coffee Consumption | No | No | 0.001472 | No |
| P04-b-contains-a | Coffee Consumption | Coffee Bean Preparation | No | No | 0.001495 | No |
| P05-a-contains-b | Coffee Bean Preparation | Appreciating Coffee for Its Flavor | No | No | 0.001656 | No |
| P05-b-contains-a | Appreciating Coffee for Its Flavor | Coffee Bean Preparation | No | No | 0.000458 | No |
| P06-a-contains-b | Coffee | Coffee | Yes | Yes | 0.985560 | Yes |
| P06-b-contains-a | Coffee | Coffee | Yes | Yes | 0.985560 | Yes |
| P07-a-contains-b | Food | Food Ingredients | Yes | Yes | 0.895404 | Yes |
| P07-b-contains-a | Food Ingredients | Food | No | No | 0.027527 | No |
| P08-a-contains-b | Food Ingredients | Sea Salt as a Food Ingredient | Yes | Yes | 0.819593 | Yes |
| P08-b-contains-a | Sea Salt as a Food Ingredient | Food Ingredients | No | No | 0.010283 | No |
| P09-a-contains-b | Food | Sea Salt as a Food Ingredient | Yes | Yes | 0.880510 | Yes |
| P09-b-contains-a | Sea Salt as a Food Ingredient | Food | No | No | 0.001864 | No |
| P10-a-contains-b | Food Ingredients | Carrots as a Recipe Ingredient | Yes | Yes | 0.845873 | Yes |
| P10-b-contains-a | Carrots as a Recipe Ingredient | Food Ingredients | No | No | 0.024904 | No |
| P11-a-contains-b | Food | Chinese Cuisine | Yes | Yes | 0.875685 | Yes |
| P11-b-contains-a | Chinese Cuisine | Food | No | No | 0.003839 | No |
| P12-a-contains-b | Food | Indian Food | Yes | Yes | 0.912983 | Yes |
| P12-b-contains-a | Indian Food | Food | No | No | 0.005744 | No |
| P13-a-contains-b | Chinese Cuisine | Indian Food | No | No | 0.000802 | No |
| P13-b-contains-a | Indian Food | Chinese Cuisine | No | No | 0.000924 | No |
| P14-a-contains-b | Red meat | Brisket | Yes | No | 0.471738 | Yes |
| P14-b-contains-a | Brisket | Red meat | No | No | 0.025378 | No |
| P15-a-contains-b | Brisket | Crockpot Meat Dishes | No | No | 0.002874 | No |
| P15-b-contains-a | Crockpot Meat Dishes | Brisket | No | No | 0.018208 | No |
| P17-a-contains-b | Poultry and eggs | Poultry-Based Food Preparation | Yes | No | 0.039920 | No |
| P17-b-contains-a | Poultry-Based Food Preparation | Poultry and eggs | No | No | 0.028125 | No |
| P18-a-contains-b | Poultry-Based Food Preparation | Making Chicken Stock | Yes | Yes | 0.903487 | Yes |
| P18-b-contains-a | Making Chicken Stock | Poultry-Based Food Preparation | No | No | 0.006919 | No |
| P19-a-contains-b | Poultry and eggs | Making Chicken Stock | Yes | No | 0.131106 | No |
| P19-b-contains-a | Making Chicken Stock | Poultry and eggs | No | No | 0.002547 | No |
| P20-a-contains-b | Daytime Greetings | Weekend Well-Wishes | No | No | 0.000950 | No |
| P20-b-contains-a | Weekend Well-Wishes | Daytime Greetings | No | No | 0.001175 | No |
| P21-a-contains-b | Patience | Kindness Beyond Social Status | No | No | 0.004140 | No |
| P21-b-contains-a | Kindness Beyond Social Status | Patience | No | No | 0.003831 | No |
| P22-a-contains-b | Bitcoin | Satoshi Bitcoin Units | Yes | Yes | 0.624658 | Yes |
| P22-b-contains-a | Satoshi Bitcoin Units | Bitcoin | No | No | 0.060995 | No |
| P23-a-contains-b | Nostr | Grow Nostr Campaign | Yes | Yes | 0.603691 | Yes |
| P23-b-contains-a | Grow Nostr Campaign | Nostr | No | No | 0.009594 | No |

## Native errors (3)

- P14-a-contains-b: expected Yes; got No; score 0.471738.
- P17-a-contains-b: expected Yes; got No; score 0.039920.
- P19-a-contains-b: expected Yes; got No; score 0.131106.

## Cutoff errors (3)

- P02-b-contains-a: expected No; got Yes; score 0.186424.
- P17-a-contains-b: expected Yes; got No; score 0.039920.
- P19-a-contains-b: expected Yes; got No; score 0.131106.
