# TRUE07 — Every frozen holdout decision

Each row asks **A contains B?** B is the premise; A is the hypothesis. All inputs use the unchanged TRUE01 topic sentence wrapper.

Native answers are complete greedy labels with EOS required. Score is full-vocabulary probability of the first output token being `1`, not calibrated category confidence. The separately frozen cutoff verdict is **score > 0.142**; no cutoff was fitted here.

| ID | A | B | Expected | Native | Score | Cutoff |
|---|---|---|---|---|---|---|
| R01-w0-w0-a-contains-b | Bitcoin | Satoshis: Bitcoin’s Smallest Units | Yes | No | 0.106547 | No |
| R01-w0-w0-b-contains-a | Satoshis: Bitcoin’s Smallest Units | Bitcoin | No | No | 0.000643 | No |
| R01-w0-w1-a-contains-b | Bitcoin | Satoshis, the smallest units of Bitcoin | Yes | No | 0.145485 | Yes |
| R01-w0-w1-b-contains-a | Satoshis, the smallest units of Bitcoin | Bitcoin | No | No | 0.000435 | No |
| R01-w0-w2-a-contains-b | Bitcoin | Bitcoin’s smallest units, called satoshis | Yes | Yes | 0.513604 | Yes |
| R01-w0-w2-b-contains-a | Bitcoin’s smallest units, called satoshis | Bitcoin | No | No | 0.000410 | No |
| R02-w0-w0-a-contains-b | Foods featuring meat or seafood | Steak | Yes | No | 0.123574 | No |
| R02-w0-w0-b-contains-a | Steak | Foods featuring meat or seafood | No | No | 0.023683 | No |
| R02-w1-w0-a-contains-b | Foods that feature meat or seafood | Steak | Yes | No | 0.136775 | No |
| R02-w1-w0-b-contains-a | Steak | Foods that feature meat or seafood | No | No | 0.018167 | No |
| R02-w2-w0-a-contains-b | Foods featuring seafood or meat | Steak | Yes | No | 0.097556 | No |
| R02-w2-w0-b-contains-a | Steak | Foods featuring seafood or meat | No | No | 0.022500 | No |
| R03-w0-w0-a-contains-b | Coffee | Coffee Bean Preparation | Yes | Yes | 0.836168 | Yes |
| R03-w0-w0-b-contains-a | Coffee Bean Preparation | Coffee | No | No | 0.017445 | No |
| R03-w0-w1-a-contains-b | Coffee | Preparing coffee beans | Yes | Yes | 0.834788 | Yes |
| R03-w0-w1-b-contains-a | Preparing coffee beans | Coffee | No | No | 0.010892 | No |
| R03-w0-w2-a-contains-b | Coffee | Preparation of coffee beans | Yes | Yes | 0.793503 | Yes |
| R03-w0-w2-b-contains-a | Preparation of coffee beans | Coffee | No | No | 0.016367 | No |
| R04-w0-w0-a-contains-b | Coffee | Appreciating Coffee for Its Flavour | Yes | Yes | 0.968358 | Yes |
| R04-w0-w0-b-contains-a | Appreciating Coffee for Its Flavour | Coffee | No | No | 0.008152 | No |
| R04-w0-w1-a-contains-b | Coffee | Appreciation of coffee’s flavour | Yes | Yes | 0.943699 | Yes |
| R04-w0-w1-b-contains-a | Appreciation of coffee’s flavour | Coffee | No | No | 0.014280 | No |
| R04-w0-w2-a-contains-b | Coffee | Appreciating coffee’s flavour | Yes | Yes | 0.939696 | Yes |
| R04-w0-w2-b-contains-a | Appreciating coffee’s flavour | Coffee | No | No | 0.007296 | No |
| R05-w0-w0-a-contains-b | Coffee Bean Preparation | Appreciating Coffee for Its Flavour | No | No | 0.001406 | No |
| R05-w0-w0-b-contains-a | Appreciating Coffee for Its Flavour | Coffee Bean Preparation | No | No | 0.000385 | No |
| R05-w0-w1-a-contains-b | Coffee Bean Preparation | Appreciation of coffee’s flavour | No | No | 0.001371 | No |
| R05-w0-w1-b-contains-a | Appreciation of coffee’s flavour | Coffee Bean Preparation | No | No | 0.000684 | No |
| R05-w0-w2-a-contains-b | Coffee Bean Preparation | Appreciating coffee’s flavour | No | No | 0.001439 | No |
| R05-w0-w2-b-contains-a | Appreciating coffee’s flavour | Coffee Bean Preparation | No | No | 0.000563 | No |
| R05-w1-w0-a-contains-b | Preparing coffee beans | Appreciating Coffee for Its Flavour | No | No | 0.002283 | No |
| R05-w1-w0-b-contains-a | Appreciating Coffee for Its Flavour | Preparing coffee beans | No | No | 0.001367 | No |
| R05-w1-w1-a-contains-b | Preparing coffee beans | Appreciation of coffee’s flavour | No | No | 0.000822 | No |
| R05-w1-w1-b-contains-a | Appreciation of coffee’s flavour | Preparing coffee beans | No | No | 0.000673 | No |
| R05-w1-w2-a-contains-b | Preparing coffee beans | Appreciating coffee’s flavour | No | No | 0.001075 | No |
| R05-w1-w2-b-contains-a | Appreciating coffee’s flavour | Preparing coffee beans | No | No | 0.000776 | No |
| R05-w2-w0-a-contains-b | Preparation of coffee beans | Appreciating Coffee for Its Flavour | No | No | 0.001276 | No |
| R05-w2-w0-b-contains-a | Appreciating Coffee for Its Flavour | Preparation of coffee beans | No | No | 0.000997 | No |
| R05-w2-w1-a-contains-b | Preparation of coffee beans | Appreciation of coffee’s flavour | No | No | 0.000701 | No |
| R05-w2-w1-b-contains-a | Appreciation of coffee’s flavour | Preparation of coffee beans | No | No | 0.000555 | No |
| R05-w2-w2-a-contains-b | Preparation of coffee beans | Appreciating coffee’s flavour | No | No | 0.000815 | No |
| R05-w2-w2-b-contains-a | Appreciating coffee’s flavour | Preparation of coffee beans | No | No | 0.000518 | No |
| R06-w0-w0-a-contains-b | Foods featuring meat or seafood | Butter as part of a meal | No | No | 0.001490 | No |
| R06-w0-w0-b-contains-a | Butter as part of a meal | Foods featuring meat or seafood | No | No | 0.000830 | No |
| R06-w0-w1-a-contains-b | Foods featuring meat or seafood | Butter included in a meal | No | No | 0.001992 | No |
| R06-w0-w1-b-contains-a | Butter included in a meal | Foods featuring meat or seafood | No | No | 0.001545 | No |
| R06-w0-w2-a-contains-b | Foods featuring meat or seafood | Butter in meals | No | No | 0.001918 | No |
| R06-w0-w2-b-contains-a | Butter in meals | Foods featuring meat or seafood | No | No | 0.001191 | No |
| R06-w1-w0-a-contains-b | Foods that feature meat or seafood | Butter as part of a meal | No | No | 0.000783 | No |
| R06-w1-w0-b-contains-a | Butter as part of a meal | Foods that feature meat or seafood | No | No | 0.000738 | No |
| R06-w1-w1-a-contains-b | Foods that feature meat or seafood | Butter included in a meal | No | No | 0.001174 | No |
| R06-w1-w1-b-contains-a | Butter included in a meal | Foods that feature meat or seafood | No | No | 0.001278 | No |
| R06-w1-w2-a-contains-b | Foods that feature meat or seafood | Butter in meals | No | No | 0.001217 | No |
| R06-w1-w2-b-contains-a | Butter in meals | Foods that feature meat or seafood | No | No | 0.000858 | No |
| R06-w2-w0-a-contains-b | Foods featuring seafood or meat | Butter as part of a meal | No | No | 0.001951 | No |
| R06-w2-w0-b-contains-a | Butter as part of a meal | Foods featuring seafood or meat | No | No | 0.001110 | No |
| R06-w2-w1-a-contains-b | Foods featuring seafood or meat | Butter included in a meal | No | No | 0.002806 | No |
| R06-w2-w1-b-contains-a | Butter included in a meal | Foods featuring seafood or meat | No | No | 0.001800 | No |
| R06-w2-w2-a-contains-b | Foods featuring seafood or meat | Butter in meals | No | No | 0.002455 | No |
| R06-w2-w2-b-contains-a | Butter in meals | Foods featuring seafood or meat | No | No | 0.001251 | No |

## Native errors (5)

- R01-w0-w0-a-contains-b: expected Yes; got No; score 0.106547.
- R01-w0-w1-a-contains-b: expected Yes; got No; score 0.145485.
- R02-w0-w0-a-contains-b: expected Yes; got No; score 0.123574.
- R02-w1-w0-a-contains-b: expected Yes; got No; score 0.136775.
- R02-w2-w0-a-contains-b: expected Yes; got No; score 0.097556.

## Cutoff errors (4)

- R01-w0-w0-a-contains-b: expected Yes; got No; score 0.106547.
- R02-w0-w0-a-contains-b: expected Yes; got No; score 0.123574.
- R02-w1-w0-a-contains-b: expected Yes; got No; score 0.136775.
- R02-w2-w0-a-contains-b: expected Yes; got No; score 0.097556.
