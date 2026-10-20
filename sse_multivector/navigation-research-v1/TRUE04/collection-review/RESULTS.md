# TRUE04 — Review the collection, not 3,660 separate questions

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../../docs/experiments/README.md#reading-the-research-records).

The 61 category titles were reviewed as a collection. Clearly unrelated combinations were excluded by their meanings, without using TRUE's answers to decide what deserved review. Both directions were then examined for plausible or uncertain pairs.

**Result:** the cutoff misses **17 of the 64 non-Nostr relationships judged reasonable** in this review. Native answers miss **24 of those 64**. There are also **63 uncertain non-Nostr directions**, which are not counted as correct or incorrect.

No additional clear missed relationships emerged beyond those already nominated in the earlier reference. This review supplies a more systematic check of the remaining category combinations; it does not turn the old positive nominations into an exhaustive negative answer key.

## What was reviewed

The 61 source groups have 58 distinct title strings. Repeated Food, Coffee and Bitcoin titles were interpreted once, while preserving every original model result. Identical titles do not prove that their source groups contain the same notes or masks.

- 167 unordered category pairs warranted closer consideration, including related pairs that ultimately do not contain one another.
- Those pairs give 334 directions: 67 reasonable containments, 65 uncertain directions, 200 rejected directions, and two directions left unestablished because Plebchain's meaning is unresolved.
- 1,431 other unordered pairs were excluded at the collection level as having no plausible title-level containment. They were not turned into thousands of independently verified No judgments.
- The remaining 55 unordered pairs involve the unresolved name Plebchain and stay unestablished. Two other Plebchain pairs were retained explicitly: the proposed Nostr/Communication parents are uncertain, and the reverse directions remain unestablished.
- All 1,653 pairs of different title strings are accounted for: 167 + 1,431 + 55.

The review considered cross-topic exceptions rather than making impermeable subject groups. Music in Coffee Shops was considered against Art as well as Coffee. Advice on Meat Consumption was considered against Communication as well as eating-related categories. Coffee Bean Preparation versus Nostr needed no individual model-driven inspection.

A fresh reviewer saw only the 61 titles and repository instructions. A second fresh reviewer saw nine scope-sensitive title pairs. Neither saw model predictions, scores, prior judgments, or source notes. The coordinating reviewer had already seen earlier results; this is therefore **not** claimed to be a fully blinded new benchmark. The original screens and final scope decisions are preserved in `screen.json`.

## Results with Nostr-related categories set aside

Nostr, Grow Nostr Campaign and Plebchain are set aside here, as requested. Their saved results remain intact. Neither model wording nor cutoff changed.

| Our semantic judgment | Distinct directions | Cutoff Yes | Cutoff No | Native Yes | Native No |
|---|---:|---:|---:|---:|---:|
| Reasonable containment | 64 | 47 | 17 | 40 | 24 |
| No containment, after closer review | 195 | 3 | 192 | 0 | 195 |
| Uncertain | 63 | 7 | 56 | 3 | 60 |

The cutoff recovers 47/64 (73.4%) of the reasonable relationships; native answers recover 40/64 (62.5%). These are **recovery rates within the semantic review**, not overall accuracy. All 63 uncertain directions remain visible in the table.

The other 2,648 non-Nostr directions were excluded by collection-level reasoning. Both model rules happen to reject them. That agreement was checked afterward; it was not the basis for excluding them, and it is not an independent correctness guarantee.

## All 17 reasonable relationships rejected by both rules

Each row asks **Does A contain B?** Both native and cutoff answer **No**.

TRUE received exactly:

```text
premise: This text is about {B}. hypothesis: This text is about {A}.
```

The score is the full-vocabulary probability of first generating token `1`. It is not cosine or a calibrated containment probability. The frozen rule accepts only scores strictly greater than 0.142.

| A: broader category | B: narrower category | Score |
|---|---|---:|
| Recipes and Their Results | Carrots as a Recipe Ingredient | 0.040590 |
| Food | Drinking tea | 0.059107 |
| Food | Coffee | 0.010624 |
| Food | Coffee Consumption | 0.002454 |
| Food | Wine | 0.000792 |
| Food | Coffee Chains | 0.002888 |
| Poultry and eggs | Making Chicken Stock | 0.131106 |
| Poultry and eggs | Poultry-Based Food Preparation | 0.039920 |
| Communication | Weekend Well-Wishes | 0.074170 |
| Communication | Advice on Meat Consumption | 0.003286 |
| Human Diet and Eating Behavior | Meat Eating | 0.116333 |
| Human Diet and Eating Behavior | Children and Food | 0.024595 |
| Human Diet and Eating Behavior | Drinking tea | 0.002954 |
| Human Diet and Eating Behavior | Coffee Consumption | 0.003920 |
| Human Diet and Eating Behavior | Advice on Meat Consumption | 0.044848 |
| Human Diet and Eating Behavior | Appreciating Coffee for Its Flavor | 0.000533 |
| Human Diet and Eating Behavior | Attitudes toward meat consumption | 0.051121 |

Food is interpreted as the broad browsing subject that includes drinks, culinary activities and food businesses. Communication includes explicitly named communicative activities such as advice and well-wishes. These are stated semantic scope choices, not meanings established by TRUE.

Every original direction represented by a listed finding, its exact input, full-precision score and source group IDs are preserved in `comparison.json`. Repeated titles can have minute score differences; all values remain in the JSON even when the rounded display coincides.

## Seven more reasonable relationships rejected only by native answers

These are independent semantic judgments of valid relationships, not an assumption that the cutoff is correct.

| A: broader category | B: narrower category | Native | Cutoff | Score |
|---|---|---|---|---:|
| Food | Coffee Bean Preparation | No | Yes | 0.331991 |
| Food | Poultry and eggs | No | Yes | 0.483415 |
| Food | Appreciating Coffee for Its Flavor | No | Yes | 0.212356 |
| Red meat | Brisket | No | Yes | 0.471738 |
| Coffee | Coffee Chains | No | Yes | 0.435481 |
| Communication | Daytime Greetings | No | Yes | 0.372657 |
| Human Diet and Eating Behavior | Consuming Excessive Amounts of Food or Drink | No | Yes | 0.165049 |

## What remains uncertain

Examples include Art → Music in Coffee Shops, Positive Living → Patience, and Mental Activity States → Psychological Distress. Those are reasonable under broader readings of the parent names, but the titles also permit narrower readings.

Seasonings and Toppings for Savory Dishes → Sea Salt as a Food Ingredient has a different issue: the parent explicitly says savory, while the child does not restrict its food uses that way. The review preserved that uncertainty rather than overlooking the qualification.

This follow-up also keeps Food Ingredients → Butter and Food Ingredients → Meals with Potatoes and Other Vegetables uncertain, where the earlier accepted-link review had called them reasonable. Ingredient-organized topics and ingredient objects do not have identical scope. This is a change in our assessment, not a change in the model.

The earlier clear-reference nominations Positive Living → Kindness Beyond Social Status and Food Ingredients → Making Chicken Stock likewise remain scope-sensitive here. Plebchain relationships remain unestablished. These differences explain why this review's counts must not be substituted silently into the earlier report.

The prior-reference cross-check also restored Communication → Art to the uncertain candidates: artistic expression may fall under a broad Communication category. Positive Living → Weekend Well-Wishes was rejected as goodwill communication rather than inherently a lifestyle subject; Bitcoin ↔ Plebchain remains unestablished rather than guessed.

All 63 non-Nostr uncertain directions, their predictions and exact scores are listed in comparison.json. The user subsequently requested all uncertainties for decision; the review below includes those 63 and the two previously set-aside Nostr/Plebchain questions.

## Decide the uncertain relationships

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-true04-uncertainties.sh
```

The 65 cards show A's exact category title above a box containing all its masks, followed by B's title and mask box. Each mask retains its vector ID and brackets around each fragment. My explanation of the uncertainty remains separate. U001–U063 are the non-Nostr questions; U064–U065 are the two previously set-aside questions. Identical title pairs appear once; where a title represents several original groups, its box includes all their masks, deduplicating only repeated vector IDs. Every original source score remains in the optional details.

The masks come from the saved title-generation record (`../titles.json`); they are display evidence, not new input to TRUE. TRUE received only the category titles. Adding the masks does not change the questions or invalidate existing answers, comments, or the saved review position.

Answer **Does category A contain category B?** A is the proposed parent and B the proposed child. A records Yes; R records No; S skips; C edits an optional comment, saved with Enter. These answers do not approve or reject my uncertainty statement.

Left/right visits all cards, including reviewed ones. A, B, and my comment remain visible together. Tab selects which box to scroll; up/down or j/k scrolls. `?` opens details, including the unchanged model input and predictions. Predictions are not displayed as an answer key on the decision screen.

Ctrl-C exits; the same command resumes the saved current card. To reopen a particular card, append `--start-at U001` (or another card ID). You do not have to finish the batch.

User answers and comments are saved separately in `target/true04-uncertainty-review/decisions.json`, bound to the exact review packet (`uncertainty-review.json`). No decisions are prefilled, and no hierarchy changes or new model calls are performed. The original read-only `run-true04-review.sh` remains available and unchanged.

## Conclusion

The user's collection-first approach substantially reduces the review burden while checking rejected relationships independently of the model. The principal rejection problems were already present in the earlier nominated set; the remaining review did not uncover a new clear class of missed relationships.

TRUE still provides useful containment decisions, but both rules miss some reasonable broader/narrower relationships. The lower cutoff recovers seven additional reasonable non-Nostr relationships and accepts three clearly wrong ones. Native agreement is never used as the answer key.

The semantic audit did not change the original experiment outputs, earlier reviews, titles, masks, cutoff, model configuration, or UI. The subsequent decision review adds a separate saved-review mode without changing those results. Neither step is a new model experiment, a full accuracy estimate, or a constructed hierarchy.

**Selected data:** Compact pair-score results, inputs and parameters for `TRUE04` are selected for release as `numerical/pair-scores-7dd83c45e206d5c8` in the [publication catalog](../../../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.
