# TRUE04 — Every accepted title relationship and every missed nomination

Each question asks: **Does A contain B?** TRUE received only the exact titles, in this order:

```text
premise: This text is about {B}. hypothesis: This text is about {A}.
```

The 61 original groups include repeated Food, Coffee and Bitcoin titles. This document shows each distinct ordered title pair once. [DECISIONS.md](DECISIONS.md) preserves every original group ID and all 3,660 directions; [scores.jsonl](scores.jsonl) contains each exact input and full-precision score.

Scores below are rounded to six decimals. They are the full-vocabulary probability of first generating token `1`, not cosine or calibrated containment confidence. **Native** is the generated Yes/No answer. The separate frozen cutoff accepts scores **greater than 0.142**.

## Accepted relationships

The cutoff accepted 106 original directions, representing 64 distinct title pairs. Every one was reviewed. The categories below are semantic judgments, not model outputs. [Judgments and reasons](title-pair-judgments.json) preserve every accepted title pair's rationale and reviewer disagreements.

All entries in the following three tables were accepted by the cutoff, including those whose native answer was No.

### Incorrect — 6 distinct questions

| A: proposed parent | B: proposed child | Native | Score |
|---|---|---|---:|
| Advice on Meat Consumption | Meat Eating | No | 0.237189 |
| Coffee Consumption | Coffee | No | 0.186424 |
| Daytime Greetings | How the Day Is Going | No | 0.336519 |
| Food | Nostr | Yes | 0.546812 |
| Nostr | Consuming Excessive Amounts of Food or Drink | No | 0.160344 |
| Nostr | Food | Yes | 0.644764–0.644765 |

### Ambiguous — 5 distinct questions

| A: proposed parent | B: proposed child | Native | Score |
|---|---|---|---:|
| Cheese-based foods | Pizza Day | No | 0.443342 |
| Food | Pizza Day | Yes | 0.626429 |
| Food Ingredients | Tomatoes | Yes | 0.619981 |
| Meat Eating | Crockpot Meat Dishes | No | 0.234342 |
| Meat Eating | Steak | No | 0.246708 |

### Reasonable containment — 53 distinct questions

| A: proposed parent | B: proposed child | Native | Score |
|---|---|---|---:|
| Bitcoin | Bitcoin | Yes | 0.985914 |
| Bitcoin | Satoshi Bitcoin Units | Yes | 0.624657 |
| Coffee | Appreciating Coffee for Its Flavor | Yes | 0.967635 |
| Coffee | Coffee | Yes | 0.985560 |
| Coffee | Coffee Bean Preparation | Yes | 0.836168 |
| Coffee | Coffee Chains | No | 0.435481 |
| Coffee | Coffee Consumption | Yes | 0.966989 |
| Coffee Consumption | Appreciating Coffee for Its Flavor | Yes | 0.772754 |
| Communication | Daytime Greetings | No | 0.372657 |
| Food | Advice on Meat Consumption | Yes | 0.754813 |
| Food | Appreciating Coffee for Its Flavor | No | 0.212356 |
| Food | Attitudes toward meat consumption | Yes | 0.561918 |
| Food | Avocados in Meals | Yes | 0.852987 |
| Food | Breakfast meals | Yes | 0.808426 |
| Food | Brisket | Yes | 0.626476 |
| Food | Butter | Yes | 0.670211 |
| Food | Carrots as a Recipe Ingredient | Yes | 0.851763 |
| Food | Cheese-based foods | Yes | 0.823583 |
| Food | Children and Food | Yes | 0.905487 |
| Food | Chinese Cuisine | Yes | 0.875685 |
| Food | Coffee Bean Preparation | No | 0.331991 |
| Food | Consuming Excessive Amounts of Food or Drink | Yes | 0.887261 |
| Food | Cooking Times | Yes | 0.627007 |
| Food | Crockpot Meat Dishes | Yes | 0.880330 |
| Food | Food | Yes | 0.984152 |
| Food | Food Ingredients | Yes | 0.895404 |
| Food | Human Diet and Eating Behavior | Yes | 0.714402 |
| Food | Indian Food | Yes | 0.912983 |
| Food | Making Chicken Stock | Yes | 0.798028 |
| Food | Meals with Potatoes and Other Vegetables | Yes | 0.931811 |
| Food | Meat Eating | Yes | 0.765692 |
| Food | Poultry and eggs | No | 0.483415 |
| Food | Poultry-Based Food Preparation | Yes | 0.934421 |
| Food | Raw Milk | Yes | 0.525075 |
| Food | Recipes and Their Results | Yes | 0.875341 |
| Food | Red meat | Yes | 0.715540 |
| Food | Sea Salt as a Food Ingredient | Yes | 0.880510 |
| Food | Seasonings and Toppings for Savory Dishes | Yes | 0.858247 |
| Food | Steak | Yes | 0.775532 |
| Food | Tomatoes | Yes | 0.705269 |
| Food Ingredients | Avocados in Meals | Yes | 0.891059 |
| Food Ingredients | Butter | Yes | 0.700475 |
| Food Ingredients | Carrots as a Recipe Ingredient | Yes | 0.845873 |
| Food Ingredients | Meals with Potatoes and Other Vegetables | No | 0.352352 |
| Food Ingredients | Sea Salt as a Food Ingredient | Yes | 0.819593 |
| Food Ingredients | Seasonings and Toppings for Savory Dishes | Yes | 0.886872 |
| Human Diet and Eating Behavior | Consuming Excessive Amounts of Food or Drink | No | 0.165049 |
| Meat Eating | Advice on Meat Consumption | Yes | 0.934846 |
| Meat Eating | Attitudes toward meat consumption | Yes | 0.613692 |
| Nostr | Grow Nostr Campaign | Yes | 0.603691 |
| Poultry-Based Food Preparation | Making Chicken Stock | Yes | 0.903487 |
| Red meat | Brisket | No | 0.471738 |
| Red meat | Steak | Yes | 0.761681 |

## Missed relationships nominated before score inspection

The [frozen reference](../true04-reference.json) nominated 120 clear original directions, representing 75 distinct title pairs. The cutoff missed 30 directions, representing the 23 questions below. **Native and cutoff both answered No to every row.** These nominations are not a complete or infallible answer key.

A fresh reviewer, shown titles without scores, upheld 20 distinct nominations and found three unresolved. The original nominations remain unchanged; the disagreement is recorded rather than counted silently as proven model error.

### Nominations upheld on fresh review

| A: proposed parent | B: proposed child | Score | Review reason |
|---|---|---:|---|
| Recipes and Their Results | Carrots as a Recipe Ingredient | 0.040590 | Using carrots in recipes is a narrower recipe topic, including their role in the resulting dish. |
| Human Diet and Eating Behavior | Meat Eating | 0.116333 | Eating meat is a specific dietary practice within human diet and eating behavior. |
| Human Diet and Eating Behavior | Children and Food | 0.024595 | The ordinary scope is children's diets, feeding, preferences, and eating habits, a population-specific part of A. |
| Food | Drinking tea | 0.059107 | A broad food-discovery category reasonably includes beverages and their consumption, including tea. |
| Human Diet and Eating Behavior | Drinking tea | 0.002954 | Tea drinking is a specific beverage-consumption behavior within ordinary dietary scope. |
| Communication | Weekend Well-Wishes | 0.074170 | Weekend well-wishes are a specific form of interpersonal greeting and goodwill expression. |
| Food | Coffee | 0.010624 | Coffee is a conventional beverage topic within broad food and culinary discovery. |
| Communication | Nostr | 0.013745 | Nostr is a decentralized social communication protocol and ecosystem, fitting communication technology as a topical subcategory. |
| Food Ingredients | Making Chicken Stock | 0.044961 | Chicken stock is a cooking ingredient, and preparing it is directly within a practical category about ingredients. |
| Poultry and eggs | Making Chicken Stock | 0.131106 | Making chicken stock is a specific poultry-related food preparation topic. |
| Food | Coffee Consumption | 0.002454 | Consuming coffee fits the ordinary beverage-consumption scope of broad food discovery. |
| Human Diet and Eating Behavior | Coffee Consumption | 0.003920 | Coffee consumption is a specific human dietary habit. |
| Human Diet and Eating Behavior | Advice on Meat Consumption | 0.044848 | Advice about consuming meat is directly about a specific dietary choice and practice. |
| Human Diet and Eating Behavior | Appreciating Coffee for Its Flavor | 0.000533 | Flavor enjoyment and beverage preferences are ordinary aspects of human eating and drinking behavior. |
| Human Diet and Eating Behavior | Attitudes toward meat consumption | 0.051121 | Attitudes toward eating meat are a narrower topic about dietary choices and eating behavior. |
| Positive Living | Kindness Beyond Social Status | 0.030899 | Treating people kindly regardless of status is a concrete prosocial practice within ordinary positive-living content. |
| Poultry and eggs | Poultry-Based Food Preparation | 0.039920 | Preparing poultry-based food is a direct subtopic of poultry as a food category. |
| Food | Wine | 0.000792 | Wine is a conventional drink and culinary topic within broad food discovery. |
| Food | Coffee Chains | 0.002888 | Coffee chains are beverage-serving establishments, a natural food-service subtopic of broad food discovery. |
| Communication | Grow Nostr Campaign | 0.018566 | A campaign to grow Nostr concerns adoption of a social communication network, fitting the communication-technology topic. |

### Nominations needing a scope or meaning decision

| A: proposed parent | B: proposed child | Score | Review reason |
|---|---|---:|---|
| Communication | Advice on Meat Consumption | 0.003286 | If A groups communicative forms such as advice, this fits. If A groups topics about communication, B is dietary guidance rather than a communication subtopic; the titles do not establish which scope applies. |
| Nostr | Plebchain | 0.000447 | Plebchain is not familiar enough to me to establish its referent from this title alone. A Nostr-specific community or initiative could fit, but that relationship is not established by the supplied titles. |
| Communication | Plebchain | 0.015489 | Plebchain is not familiar enough to me to establish whether it denotes a communication platform, community, or something else. Containment cannot be resolved from the title alone. |

Food was interpreted broadly to include beverages, as is reasonable for content discovery; that scope is an explicit review choice, not a demonstrated universal meaning of the bare title. Plebchain was not confirmed by the fresh reviewer. Communication's scope is uncertain when used as a parent of advice merely because advice is a communicative act.

The [fresh review](missed-reference-review.json) and [pre-score rationales with all 30 scored directions](semantic-analysis.json) preserve both sides. Unlisted rejected questions were not automatically judged correct.

## What this record does not establish

These are category-title comparisons. The model did not see the masks, source notes or prior grouping decisions, and this test does not re-evaluate whether a title describes its source group. No graph was repaired or adopted, and no missing parent was generated. [Main findings](RESULTS.md) explain what the observed decisions support.
