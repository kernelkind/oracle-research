# Structure-matched proposals

This is the complete set of 18 additional direct edges into the 30 multiword
SPC01 categories originally supported by at least two notes. Additional means
absent from SPC01's direct-edge list, not necessarily a new note or a new
semantic discovery. Thirteen also appear without WordNet; five need lexical
generalization. No proposal is adopted automatically.

P identifiers name frozen SPC01 expressions. Row identifiers name unchanged
CAP04 subject/mask records. All originals and inline masks for the rows below
are in [SPC01's source evidence](../SPC01/SOURCE-EVIDENCE.md); the raw input
record also retains the exact description and fragments. Source phrases are
constructed from those descriptions, not new masks cut from the original post.

## Complete edge audit

| Parent | Child | Source rows / notes | Assessment |
|---|---|---|---|
| P1144 Chicken stock | P2039 Pressure-canned chicken stock in pantry | 41 / N013 | Supported chicken-stock topic. Adds a direct link, not a new note. |
| P1144 Chicken stock | P2040 Pressure-canned chicken stock | 41 / N013 | Supported; same note and source as the preceding expression. |
| P1144 Chicken stock | P2096 Pressure canning homemade chicken stock for pantry storage | 468 / N013 | Supported topic in the original. The stored parse makes stock the head of the activity phrase; this is not evidence that the parse correctly represents the activity. |
| P1144 Chicken stock | P2097 Pressure canning homemade chicken stock | 468 / N013 | Same qualification as P2096; no new note. |
| P1157 Coffee shop | P1765 Different coffee shop | 130 / N065 | Supported venue topic. The source describes switching shops. No new note. |
| P1259 Food preparation | P1120 Bread preparation | 866 / N089 | Supported new note. The original discusses salt, yeast and mixing bread. Bread's food sense fits this occurrence. |
| P1259 Food preparation | P1852 Outdoor dinner grilling | 91 / N039 | Supported new note. The original discusses storms threatening dinner grilling. It need not teach cooking to concern food preparation. Both dinner→food and grilling→preparation retain the activity/material connection. |
| P1259 Food preparation | P1974 Beef and steak preparation | 350 / N100 | Supported new note. The original describes cutting sirloin into steaks. The mapping uses beef→food and retains preparation; the coordinated steak restriction remains in the child. |
| P1295 Better food | P1293 Good coffee | 433 / N071 | Scope-sensitive. Quality of coffee can fit a broad food-and-drink-quality topic, but the existing parent mixes good food and comparative better food. This is not certified as either a valid final title or a clear lexical failure. |
| P1295 Better food | P1753 Consistently good food at narrator's lunch location at bay | 367 / N054 | Supported under the same good/better-food scope already present in SPC01. Existing lemma identity loses comparative degree; this run does not introduce that issue. No new note. |
| P1295 Better food | P1754 Consistently good food | 367 / N054 | Same source and qualification as P1753. |
| P1396 Many foods | P1395 Many dishes | 187 / N026 | Invalid source interpretation: these dishes are tableware being washed, not prepared food. N026 independently discusses several foods, so the final note can fit while this lexical witness is wrong. |
| P1396 Many foods | P2013 Many new tasty foods during summer stay in Japan | 73 / N011 | Supported variety-of-foods meaning. No new note. |
| P1396 Many foods | P2014 Many new tasty foods | 73 / N011 | Same supported source; no new note. |
| P1442 Nostr community | P2021 Nostr social-media community | 324 / N005 | Supported by addressing nostriches. No new note. |
| P1597 Social media | P1749 Coffee social media | 347, 648 / N071, N029 | Consistent with the existing coffeechain interpretation. Recovers these two notes at Social media; does not establish that an affiliation hashtag is a useful standalone navigation choice. |
| P1706 Author's coffee | P2036 Post author's coffee | 119 / N045 | Supported ownership expression but not a useful demonstrated new distinction. No new note. |
| P2111 Themed social-media posting chain | P2114 Coffee-themed social-media posting chain | 347, 648 / N071, N029 | Consistent with the same existing hashtag interpretation; two new notes here, but duplicates the Social-media recovery rather than adding another independent success. |

Sixteen edges are source-supported with the qualifications above, one has an
invalid source interpretation, and one remains scope-sensitive. This is not
16 useful new navigation steps: repeated expressions, existing notes and weak
reporting-language choices remain. The five lexical additions alone are three
supported food-preparation paths, one invalid dish interpretation and one
scope-sensitive coffee-quality relation.

## The dish error is hidden by a correct-looking note

The supplied subject at row 187 is:

> The author washed many dishes used while preparing tomatoes for salsa, making yogurt, bagging chicken meat, and making chicken stock.

The source mask contains both preparation and washing fragments:

> ⟦prepared⟧ … ⟦tomato’s to make salsa⟧ … ⟦Made⟧ … ⟦yogurt⟧ … ⟦bagged the chicken meat⟧ … ⟦made⟧ … ⟦chicken stock⟧ … ⟦cleaned⟧ … ⟦many dishes⟧ … ⟦i used doing all the above⟧

This line lists fragments; it is not the complete note. The complete original
with that mask is [row 187](../SPC01/SOURCE-EVIDENCE.md#row-187--n026).

The generated phrase P1395 is **many dishes**, and the actual dictionary path is:

`dish.n.02 → nutriment.n.01 → food.n.01`

That is the prepared-food sense of dish. The original says the dishes were
used and then cleaned. Matching the identical modifier/head arrangement of
many dishes and many foods does not resolve which dish meaning applies.

The note also lists salsa, yogurt and chicken. Therefore admitting N026 to a
food-variety category is not sufficient evidence that this particular derivation
was valid. The two assessments must remain separate.

## What structure still misses

Food preservation still omits N022, despite its explicit beet-freezing meaning.
The available expression is beet-headed with preservation attached through
“for”; it does not share Food preservation's head arrangement. Sea salt still
omits N046 because sea and salt separately modify flakes or toppings in its
stored structures.

Several further food-preparation sources are also rejected: Baking bread,
Cooking brisket, Cooking cabbage, Cooking eggs, Cooking mushroom risotto, and
Frying beef. Their saved expressions often have the food noun as head and
the activity as a nominal compound modifier. Their originals do discuss food
preparation. Removing them is not an improvement merely because it makes
the relation list smaller. The [word-match audit](./WORD-MATCH-AUDIT.md)
enumerates the complete contrasting surface.
