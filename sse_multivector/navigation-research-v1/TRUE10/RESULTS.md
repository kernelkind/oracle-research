# TRUE10 — Building the graph with TRUE

TRUE creates useful parent–child connections, but the unchanged 0.142 rule does **not** produce a usable hierarchy as-is. Two incorrect reverse connections create cycles and give narrower categories their supposed parents’ entire contents. Other valid destinations still miss relevant categories and notes.

No titles, masks or non-equivalence connections were repaired. No new UI was built.

## What we built

We checked all 3,540 ordered directions between the 60 retained categories. There were 3,308 distinct input strings: 212 reused verified earlier scores, and 3,096 were newly scored. The previously rejected coffee-chain category remained excluded.

Two pairs genuinely describe the same categories: Coffee and Bitcoin. After explicitly consolidating those pairs and preserving their original IDs and memberships, the graph has **58 categories, 88 accepted connections, and all 232 source masks from 77 notes**.

For a proposed parent A and child B, TRUE received only:

```text
premise: This text is about {B}. hypothesis: This text is about {A}.
```

It did not receive notes or masks. A score strictly greater than 0.142 created A → B. “Native” below is TRUE’s separately generated 0/1 answer; the score is not cosine or a calibrated probability of containment.

## Useful connections exist

These are actual accepted connections, not hand-built replacements:

```text
Coffee
├─ Coffee Bean Preparation
├─ Having drunk coffee
└─ Appreciating Coffee for Its Flavour

Food → Food Preparation and Dining → Cooking Times
Food → Tomatoes → Breakfast foods made with tomatoes
```

Coffee’s own masks cover five notes; following its children makes nine notes available. Its three child connections score 0.8362, 0.8710 and 0.9684, respectively.

The two Food paths are useful local relationships inside a graph that still contains the problems below. They are not a claim that the complete Food organization is correct.

## Two false reverse connections prevent a hierarchy

Every row asks whether A contains B.

| A | B | Score | Native | Fixed cutoff | Analysis |
| --- | --- | ---: | --- | --- | --- |
| Food | Food consumption | 0.981883 | Yes | Yes | Valid broader-to-narrower direction. |
| Food consumption | Food | 0.223126 | No | Yes | Incorrect reverse: Food also covers preparation and ingredients. |
| Prepared foods | Dishes with Toppings or Seasonings | 0.585767 | Yes | Yes | Valid broader-to-narrower direction. |
| Dishes with Toppings or Seasonings | Prepared foods | 0.303842 | No | Yes | Incorrect reverse: prepared food need not have toppings or seasonings. |

These pairs are not equivalences. We therefore did not consolidate them or choose an edge to delete.

The consequences are concrete:

- Food consumption inherits all of Food’s descendants. Both consequently contain 58 notes.
- Dishes with Toppings or Seasonings inherits all of Prepared foods’ descendants. Both consequently contain 35 notes.
- Food and Food consumption both have a parent, so neither qualifies as a starting category under the rule “start at categories with no parent.” Following only such starts reaches 28 of 58 categories and 41 of 77 notes. **No data was deleted:** the other categories and notes remain in the saved graph. This is a consequence of the cyclic organization, not a measured bug in an existing UI.

Equal inherited note sets here are a consequence of the cycles—not evidence that the categories mean the same thing. Removing redundant connections was withheld because the graph is still cyclic.

## Missing connections have different consequences

**Foods featuring meat or seafood → Steak:** score 0.123574, rejected. There is also no indirect route. Neither of Steak’s two source notes is available under Foods featuring meat or seafood. This is an actual missing destination, not merely a missing shortcut.

**Food Preparation and Dining → Carrots as a food ingredient:** score 0.025222, rejected, with no indirect route. One of the two carrot notes is already available through other categories; the other is missing there.

**Bitcoin → Satoshis: Bitcoin’s Smallest Units:** rejected with no indirect route, but both Satoshis notes already have other masks in Bitcoin. The category route is missing; these particular notes are not. This remains separate from the ordinary-food findings and the previously noted knowledge-transfer limitations.

A route can also be present for the wrong reason. There are 26 rejected direct relationships reachable through accepted connections; several routes pass through the incorrect reverse connections above. We did not count every such route as a successful recovery.

## Semantic review is not ground truth

A fresh-context reviewer examined plausible relationships across the collection without seeing TRUE scores. Its 354 directional judgments included 62 Yes, 251 No and 41 uncertain. The fixed cutoff agreed with 49 of its 62 Yes judgments and 241 of its 251 No judgments. Native answers agreed with 36 and 248, respectively. The cutoff accepted 17 of the 41 uncertain directions; native answers accepted 11.

These are assistant judgments about repeated categories, not independent test examples or a general accuracy estimate. Uncertainty includes product-versus-activity scope and whether Food includes beverages. The four uncertain duplicate-category directions were subsequently resolved by explicit mask review, not by automatic cycle contraction. Nineteen accepted directions absent from the initial review received a separate post-score review. Unlisted directions were not silently classified as No.

## Next step suggested—not performed

Compare the graph built from native answers with this fixed-cutoff graph, **using the saved outputs and no additional inference**. Native answers reject both false reverse connections above, but also miss more independently judged valid connections. The useful question is how that tradeoff affects complete paths and available notes—not which rule has the larger headline accuracy. No replacement rule has been selected.

## Records

- [Complete connections, category IDs and source masks](./GRAPH.md)
- [Original notes, masks and recursive note memberships](./derived/notes.json)
- [Every ordered decision and its source](./graph/scores.json)
- [Raw graph](./graph/graph.json) and [graph after the two reviewed consolidations](./derived/graph.json)
- [Initial independent review](./semantic-review.json), [all direct/path/note comparisons](./derived/semantic-comparison.json), and [additional review](./additional-semantic-review.json)
- [Analysis and counts](./analysis.json), [frozen run plan](./plan.json), and [final integrity verification](./final-verification.json)

The local, offline CPU model run took 71.4 minutes including loading and peaked at 44.2 GiB RSS. It used one process, four threads, a 60 GiB memory cap and no swap allowance. No new paid resource or API call was used. Earlier experiment measurements are preserved.
