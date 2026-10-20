# SPC02: source audit of the 79 word-only edges

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

## Scope and interpretation

This is a post-construction, source-aware semantic audit, not a new experiment or a gold taxonomy. It uses the final deterministic artifact, `final/result.json`, and the unchanged SPC01 inputs (`../SPC01/construction/inputs.json`) and native parses (`../SPC01/native/parses.json`). No model was run, experimental input generated, or source artifact changed for this audit.

The audited universe is exactly: `words_lexical` edges whose parent is one of the 30 multiword SPC01 nodes with at least two distinct source notes, excluding original SPC01 direct edges and every edge also admitted by `structure_lexical`. There are 97 scoped new word edges, 18 shared with the structure condition, and 79 differences. The differences involve 18 parents, 72 unique children, 90 child occurrences, 70 distinct child source rows, and 41 notes. All child occurrences were examined against their saved descriptions, original mask fragments, and complete readable originals; parent evidence was also examined. The union of parent and child evidence is 127 rows from 49 notes. Repeated edges and overlapping masks are not independent semantic cases.

Of the 79 differences, 61 also exist in `words_literal`; only 18 require lexical matching. Thus most differences test whether the structural restriction rejects a source-supported topical placement, not whether WordNet discovers a new relation. The last 40 entries below all have literal alternatives.

Judgments concern **source-supported topical placement**, not exclusively noun-class subsumption. A shop's rules, ingredients in bread, or participation in a posting chain can be useful branches. Conversely, mere word overlap, incidental authorship language, and a source's unrelated topic do not establish a meaningful branch. “Supported” does not certify every qualifier or the emitted child's grammatical construction. Material inherited description/parse defects are recorded separately; a malformed child can still point at the correct parent topic. “Unresolved” preserves a real source or parent-scope ambiguity rather than forcing a canonical taxonomy.

These are direct-edge witness judgments, not an audit of all transitive memberships or complete root menus. In particular, an invalid witness does not imply the note lacks another valid witness, and a valid direct witness does not certify every membership reachable through the graph.

Placement judgments are 70 supported, two invalid and seven unresolved. These
are not 70 certified navigation steps: malformed child expressions, weak parent
scopes, equivalent meanings and bad selected explanations are qualified below.

## Consequential findings

- The structure condition rejects genuine activity-to-topic connections: bread baking (row 375/N047), brisket cooking (711/N085), cabbage/egg cooking (887/131/N001), mushroom-risotto cooking (20/N063), and beef frying (544/N096). In these saved parses, the food noun is the head and the cooking/baking/frying noun is its compound modifier; `Food preparation` has preparation as its head. The source meaning supports the placement despite this head mismatch. Row 20's cooking interpretation was already present in the saved description of the dish/chef-emoji source; it was not introduced by SPC02.
- The word condition also supplies a genuine food-preservation route for N022: row 904 describes the garden-grown beets being prepared for freezing, with original mask fragments `This year’s beets`, `ready for the freezer`, and `raised bed`. The child denotes the beets for preservation rather than a preservation-headed phrase. For topical browsing, that is not a reason to reject the branch. This is a relation/membership opportunity beyond exact shared-head matching.
- There are clear wrong semantic matches: chicken stock is matched to a takeout dish's **name** through stock-as-lineage (910/N010), and good/better food is matched to a **good view** through the separate word lunch (915/N054). N054 has another good-food witness, so the second is a bad witness/edge, not a newly demonstrated wrong full-note membership.
- Bad recorded lexical evidence is not equivalent to a bad destination. The frying-pan child is a plausible food-preparation-equipment branch, but its saved Food match uses the **Punch** brand as a beverage. Two sourdough children save bread-to-sugar through the money sense `boodle.n.01`, although their explicit culinary bread words supply literal mappings already admitted by `words_literal`. The two many-foods/mochi-bread children likewise have literal alternatives to the saved food-to-ham mapping. These alternative mappings were inspected, not inferred from a correct-looking label.
- Some blocked connections restore compatible forms rather than a new distinction: `good morning greeting` under `good morning`; a greeting to Nostr members under the Nostr-directed greeting node; and two identical `themed social media posting chain` labels with different native attachment. These can improve source coverage without constituting new semantic refinements.
- Existing defects remain existing defects. The saved child `coffee shop's weekend laptop` drops the tablet-ban construction; `... tablets to hipsters` detaches a causal attribution; finite associates, objects, and tastes are treated as nouns in three other candidates. These need not produce a wrong parent topic, but they are not certified as correct displayed categories by this audit. Hashtag-to-community/posting interpretations and generic author language also predate SPC02.

The result does not establish that word matching should replace structure, or that structure is unnecessary. It establishes that the saved dependency constraint both blocks real binding/sense mistakes and excludes source-supported topical paths. A correct destination, correct lexical explanation, well-formed child, and safe propagation are separate questions. This subset alone cannot supply comparative precision for either complete graph.

## Complete edge inventory

Numbers are the zero-based order of the difference in the final `words_lexical` edge list. The artifact has no separate edge-ID field; the exact parent-ID → child-ID pair is its identity. Labels below are the saved labels, not repaired experimental inputs. Rows identify the frozen SPC01 inputs; all occurrences of a child are covered even where several edges reuse that child.

### Carnivore diet — P1132

| # | Exact edge and saved child label | Judgment and source |
| --- | --- | --- |
| 0 | P1132 → P1741 — carnivore diet food | Supported as a carnivore-diet discussion, **not** as a claim that the pancakes comply with the diet. Row 267/N028 explicitly says `Sorry, not Carnivore :)`; projecting the phrase loses the surrounding negation. |
| 1 | P1132 → P1828 — narrative associates bitcoin with carnivore diet | Supported topical association discussion. Row 304/N074 selects `bitcoin carnivore narrative`; the full note criticizes it. Inherited parse defect: finite associates becomes noun associate, with bitcoin as head. This does not make the carnivore destination irrelevant. |

### Chicken stock — P1144

| # | Exact edge and saved child label | Judgment and source |
| --- | --- | --- |
| 2 | P1144 → P0086 — batch of chicken stock | Supported quantity/batch branch. Row 360/N013 explicitly selects stock pots and `batch of chicken stock`. |
| 3 | P1144 → P0367 — gallon of chicken stock | Supported stock-quantity topic. Row 712/N026 says `over a half gallon of chicken stock from the bones`; the inherited projection must not be read as an assertion of a whole gallon. |
| 4 | P1144 → P1501 — precise name of Chinese takeout chicken dish as General | **Invalid.** Row 910/N010 is the name `general whatever chicken`, not stock. The mapping uses `name.n.03 → family.n.04 → lineage.n.01`, selecting a different sense of stock. The complete readable note supplies no chicken-stock witness. |
| 5 | P1144 → P1933 — today's batch of chicken stock | Supported batch/time-qualified stock topic. Row 240/N013 explicitly selects today, batch, chicken stock, and the expected 25 quarts. |

### Coffee shop — P1157

All eleven edges use N065's readable account of a previously liked coffee shop's weekend laptop/tablet ban, the author's contemplated router-password retaliation, and the decision to visit another shop. Rules, equipment, and selection are legitimate shop-related topics; they need not themselves be shops. N065 is already a source note of the parent.

| # | Exact edge and saved child label | Judgment and source |
| --- | --- | --- |
| 6 | P1157 → P0694 — policies such as coffee shop's weekend ban on laptops and tablets | Supported policy/example branch; row 569/N065 selects the shop, ban, and hipster-success explanation. |
| 7 | P1157 → P1445 — objectionable restrictions such as coffee shop's weekend ban on laptops and tablets | Supported restriction/complaint branch; row 554/N065 has the same explicitly shop-related ban. |
| 8 | P1157 → P1930 — their regular selection of coffee shops | Supported choice/rotation branch; row 445/N065 selects the shop/ban and `will remove this one from rotation`. |
| 9 | P1157 → P1984 — coffee shop's restriction on customers' laptops and tablets | Supported restriction branch; row 181/N065 selects the shop, ban, and imagined router-password response. |
| 10 | P1157 → P1985 — coffee shop's router | Supported equipment-related branch; row 345/N065 explicitly selects the shop and the contemplated change to `their router/ap passwords`. It is not a report that the author actually changed them. |
| 11 | P1157 → P1986 — coffee shop's rule | Supported rule branch; row 160/N065 selects `Coffee shop`, `No laptops or tablets`, and `on weekends`. |
| 12 | P1157 → P2063 — unwelcome coffee shop rule | Supported disliked-rule branch; row 359/N065 retains the rule, contemplated retaliation, departure, and ironic personal-growth comment. |
| 13 | P1157 → P2080 — coffee shop's weekend ban on laptops and tablets to hipsters | Supported **parent destination**, but not a certified child as rendered. Row 693/N065 attributes the ban **to hipsters becoming too successful**. The saved parse attaches `to hipsters` to laptops and the projection drops the rest of that attribution; it does not establish a ban directed at hipsters. |
| 14 | P1157 → P2081 — coffee shop's weekend ban on laptops and tablets | Supported ban branch. All three rows 399, 554, 569/N065 retain the shop's laptop/tablet ban; their additional emphases differ. |
| 15 | P1157 → P2082 — coffee shop's weekend laptop | Supported **parent destination; unsupported child construction**. Row 130/N065 describes the laptop **and tablet ban**, not a particular weekend laptop owned by the shop. The saved noun projection loses the coordinated ban construction. This is not a new irrelevant Coffee-shop note. |
| 16 | P1157 → P2123 — previously liked coffee shop's weekend ban on laptops and tablets | Supported as the previously liked **shop's** ban, row 428/N065 (`Coffee shop I liked`, rule, removal from rotation). The saved parse attaches liked to ban; the source does not say the author previously liked the ban. |

### Food preparation — P1259

Parent evidence includes row 899/N026's preparation/dishwashing account and row 673/N076's culinary-craft/chef description. It is not frozen as only a strict class of preparation events. The cooking rows below are supported activity refinements; equipment is marked explicitly as an aspect branch.

| # | Exact edge and saved child label | Judgment and source |
| --- | --- | --- |
| 17 | P1259 → P0414 — heart of Sorrento's local cuisine | **Unresolved topical scope; invalid lexical justification.** Row 583/N002 promotes discovering local cuisine on a culinary walk. Food preparation might encompass culinary styles, but the source primarily concerns a tasting tour, not preparing food. Food is matched to heart as edible organ (`heart.n.08`), while preparation is matched to cuisine; that does not resolve the scope question. |
| 18 | P1259 → P1089 — Baking bread in pans | Supported baking/preparation branch; row 375/N047 selects cleaning ashes to put in bread pans. The full original describes the still-hot baking space and short cook. Food/preparation matches bread/baking, but bread is the saved head. |
| 19 | P1259 → P1090 — Baking bread | Supported same baking source, row 375/N047; less specific than the pans child. Same head mismatch. |
| 20 | P1259 → P1171 — Cooking brisket on smoker | Supported preparation/method branch; row 711/N085 selects `Brisket on the smoker`. Native head is brisket rather than cooking. |
| 21 | P1259 → P1172 — Cooking brisket | Supported same cooking source, row 711/N085. Same head mismatch. |
| 22 | P1259 → P1173 — Cooking cabbage on author's rocket stove | Supported preparation/equipment branch; row 887/N001 selects `my rocket stove`, `cook`, `cabbage`. Native head is cabbage. |
| 23 | P1259 → P1174 — Cooking cabbage | Supported same explicit cooking source, row 887/N001. Same head mismatch. |
| 24 | P1259 → P1175 — Cooking eggs on author's rocket stove | Supported preparation/equipment branch; row 131/N001 selects `my rocket stove`, `cook`, `eggs`. Native head is eggs. |
| 25 | P1259 → P1176 — Cooking eggs | Supported same explicit cooking source, row 131/N001. Same head mismatch. |
| 26 | P1259 → P1177 — Cooking mushroom | Supported ingredient/preparation topic in row 20/N063's saved cooking-mushroom-risotto description. Original mask is `Mushroom Risotto`, `Shrimp👨‍🍳`; cooking is an inherited contextual interpretation, not a new SPC02 assertion that a particular cooking step occurred. Native head is mushroom. |
| 27 | P1259 → P1275 — frying beef | Supported explicit preparation branch; row 544/N096 selects the recipe's `Gently fry beef` within its method. Native head is beef. |
| 28 | P1259 → P1276 — frying pan in Staub x Buster Punch collection | Supported as a **food-preparation-equipment** aspect, not a claim that a pan is a preparation event. Row 37/N056 selects the collection and frying pan/handle description. The saved lexical explanation is wrong: Food matches the brand **Punch** as `punch.n.02` beverage, not the pan's function. Correct topical placement does not validate that match. |
| 29 | P1259 → P1757 — Cooking mushroom risotto with shrimp | Supported dish/preparation branch, row 20/N063, with the same inherited cooking interpretation noted at #26. Native head is risotto; preparation matches cooking and food matches mushroom. |
| 30 | P1259 → P1758 — Cooking mushroom risotto | Supported same source and interpretation, row 20/N063. Same native head mismatch. |

### Food preservation — P1260

| # | Exact edge and saved child label | Judgment and source |
| --- | --- | --- |
| 31 | P1260 → P0355 — form of food preservation | Supported but the child label is generic/non-distinguishing. Row 468/N013's complete saved description specifies pressure-canning stock for pantry storage; that meaningful detail is absent from this projected label. |
| 32 | P1260 → P1663 — Vacuum sealing as food preservation method | Supported preservation-method branch; row 48/N100 selects `vacuum sealer`, within the original's food-processing/preservation context. The generic method description predates SPC02. |
| 33 | P1260 → P1779 — food preservation method | Supported generic method topic from row 48/N100, but omitting vacuum sealing loses the distinguishing method. |
| 34 | P1260 → P2069 — year's grown beets for preservation | Supported preserved-food/preparation branch; row 904/N022 explicitly connects the grown beets to readiness for freezing. Food matches the edible beet sense; preservation is literal. Rejecting it solely because the child head is beets would lose a relevant topical route. |

### Better food — P1295

The saved key normalizes both good and better to good: this parent includes row 385/N054's good food as well as rows 348/602/N070's better-food choices. It is not treated as only a strict comparative, or only a taste/nutrition assertion.

| # | Exact edge and saved child label | Judgment and source |
| --- | --- | --- |
| 35 | P1295 → P1290 — good alternative to packet of crisps | Supported under that good/better-food-choice scope. Row 815/N080 explicitly selects `Michael Mosley said`, `boiled egg`, `good alternative`, `packet`, `crisps`. It is a reported favorable food substitution, not proof that crisps are good food, or that the author endorses the advice. The saved food→crisps mapping alone misses the recommended egg/comparator binding. |
| 36 | P1295 → P1755 — consistently good view at narrator's lunch location at bay | **Invalid witness/edge.** Row 915/N054 selects `lunch`, `always`, `good view`, `bay`; good modifies view, not lunch/food. The original's separate `good food` is retained by parent row 385, not this child mask. Do not credit this edge through the unrelated parent witness or count N054 as a newly wrong note. |
| 37 | P1295 → P1942 — Very good fortune concerning food specifically in relation to Khyber Pass | **Unresolved.** Row 692/N093 selects `v. lucky`, `food`, `Khyber Pass`. This may express a favorable food/restaurant opportunity, but it does not clearly assert food quality. Good modifies fortune, not food; the broad-versus-quality-only boundary is not fixed by the short original. |
| 38 | P1295 → P1943 — Very good fortune concerning food | **Unresolved**, same source ambiguity in row 708/N093, whose mask is `v. lucky`, `food`. A positive circumstance concerning food is not automatically praise of the food itself. |

### Good morning — P1296

Parent evidence is the greeting use, including GM expansions, not pleasant morning weather. Community/addressee detail can be a branch; merely spelling out greeting can be equivalent.

| # | Exact edge and saved child label | Judgment and source |
| --- | --- | --- |
| 39 | P1296 → P1792 — good morning greeting to friends | Supported addressee branch; row 619/N071 selects `Good morning frens`. |
| 40 | P1296 → P1793 — good morning greeting to members of Nostr community | Supported addressee branch; row 133/N005 selects `Gm nostriches`. |
| 41 | P1296 → P1794 — good morning greeting to Nostr community | Supported addressee branch; rows 539/N089 and 651/N058 explicitly address the Nostr community in their morning greetings. |
| 42 | P1296 → P1795 — good morning greeting to Siamstr community | Supported addressee branch; row 192/N040 retains GM and the Siamstr context. The community rendering is inherited. |
| 43 | P1296 → P1796 — good morning greeting | Supported, mostly equivalent/non-distinguishing to the parent's greeting sense. All seven rows are greeting witnesses: 133/N005, 192/N040, 361/N099, 539/N089, 619/N071, 651/N058, 913/N064. Their smaller source set does not establish a narrower meaning. |

### Hot tea — P1330; many foods — P1396

| # | Exact edge and saved child label | Judgment and source |
| --- | --- | --- |
| 44 | P1330 → P0368 — gallon of hot tea | Supported quantity-qualified tea topic. All three rows 4, 327, 564/N073 retain drinking over a gallon of hot tea in less than 24 hours; they differ in realization/consumption/health-question emphasis. |
| 45 | P1396 → P1708 — author's discovery of many foods | Supported variety/discovery branch; row 346/N011 selects the Japan stay and `many`, `new tasty things`, `I found`. |
| 46 | P1396 → P1709 — author's discovery of ham and cheese mochi bread among many new tasty foods during summer stay in Japan | Supported: row 73/N011 explicitly places this discovery among many new tasty foods. The saved lexical mapping pairs food with ham rather than the noun governed by many; a literal many/foods alternative exists in `words_literal`. The source supports the whole relation, not that isolated mapping. |
| 47 | P1396 → P1820 — many different kinds of food | Supported, substantially a paraphrase/qualification of the variety parent; row 145/N070 explicitly says humans can eat many kinds of foods. |
| 48 | P1396 → P2086 — ham and cheese mochi bread among many new tasty foods during summer stay in Japan | Supported in the explicit variety context, row 73/N011. Same saved food→ham caveat and valid literal alternative as #46; do not infer many foods from a lone food item outside that context. |

### Nostr community — P1442

The parent already includes Nostr-addressed greetings and community/affiliation interpretations. The N048 hashtag rows below inherit that scope; neither the edge nor this audit verifies membership of named people or makes every Bitcoin community a Nostr community.

| # | Exact edge and saved child label | Judgment and source |
| --- | --- | --- |
| 49 | P1442 → P0557 — members of Nostr community | Supported member-related branch; row 133/N005 addresses `nostriches`. It need not denote a kind of community. |
| 50 | P1442 → P1461 — Ordinary members of Bitcoin and Nostr communities | Supported within inherited community/affiliation scope, row 460/N048 (`#bitcoin`, `#nostr`, `#pleb`). The source does **not independently establish ordinary members**; that qualifier/population interpretation is a preexisting description issue. |
| 51 | P1442 → P1494 — Plebchain community on Nostr | Supported within inherited affiliation scope, row 640/N048 (`#nostr`, `#plebchain`). It concerns that community without proving identities or formal memberships. |
| 52 | P1442 → P1793 — good morning greeting to members of Nostr community | Supported community-addressed greeting branch, row 133/N005 (`Gm nostriches`). |
| 53 | P1442 → P1794 — good morning greeting to Nostr community | Supported community-addressed greeting branch; both rows 539/N089 and 651/N058. |
| 54 | P1442 → P1975 — Bitcoin and Nostr communities | Supported joint topic under the inherited affiliation interpretation, row 460/N048. The coordination retains Nostr; this is not a universal subset claim about all Bitcoin communities. |

### Post author — P1499

This parent is already weak reporting language, drawn from different post authors in N045 and N060. It does not identify a shared person. Its weakness must not be hidden by a high rate of grammatical author/post word overlap.

| # | Exact edge and saved child label | Judgment and source |
| --- | --- | --- |
| 55 | P1499 → P1273 — fruit theme in author's post | **Unresolved: weak parent scope.** Row 394/N080 selects `Cherries`, `chosen fruit` and genuinely reports the author's theme choice. An author-activity interpretation is possible, but generic post-author framing does not establish this as a useful refinement. The post-author/author-post binding difference is insufficient evidence for the relation, not proof that no topical relation exists. |
| 56 | P1499 → P1718 — author's post | **Unresolved: weak parent scope**, same row 394/N080. The author describes a real theme choice, but the projected author's-post label loses that distinction. This does not certify an invalid author-topic destination; the generic parent's intended scope is insufficiently established. |
| 57 | P1499 → P1861 — post's author | Supported as a role paraphrase, not useful narrowing; row 921/N045 retains the first-person coffee complaint directed at America. The generic reporting-language limitation remains. |
| 58 | P1499 → P2036 — post author's coffee | **Unresolved scope.** Row 119/N045 explicitly retains `ruining my coffee`, so the ownership is real. Whether the author's coffee is a useful branch of a generic multi-author Post-author node is not established; a changed head alone is not proof of an invalid topic. |
| 59 | P1499 → P2037 — post's author objects to half and half | **Unresolved as a Post-author refinement; inherited parse defect.** Row 120/N045 genuinely describes the author's objection using `Half & half`, `ruining my coffee`. The native parser turns finite objects into noun object and binds post/author as its modifiers, which does not certify a nominal author-objects category. The underlying complaint is real; do not call N045 a newly irrelevant parent note or conflate the parse defect with a proven wrong author-topic destination. |

### Raw milk — P1519; social media — P1597

Social-media posting/community scope below is already established by the parent descriptions. The existing hashtag-based coffeechain/foodchain interpretations are not newly generated evidence, nor automatically literal beverage/food-content claims.

| # | Exact edge and saved child label | Judgment and source |
| --- | --- | --- |
| 60 | P1519 → P1871 — raw milk slush | Supported preparation/product branch. Both rows 811 and 840/N006 explicitly retain `raw milk slush`, `soooo good`. |
| 61 | P1597 → P0643 — part of themed social media posting chain | Supported participation branch; row 175/N086 retains the source's `Sipping @` coffeechain participation. |
| 62 | P1597 → P1904 — social media posting | Supported posting activity; row 797/N018 selects `back`, `coffeechain`, `tomorrow`. |
| 63 | P1597 → P2021 — Nostr social media community | Supported community branch under the inherited Nostr reading; row 324/N005 selects nostriches. |
| 64 | P1597 → P2110 — themed social media posting chain | Supported posting-chain topic; row 797/N018 explicitly says the author will be back in the coffeechain tomorrow. |
| 65 | P1597 → P2111 — themed social media posting chain | Supported under the existing posting interpretation. All six source rows retain their chain evidence: 175/N086, 241/N078, 382/N038, 430/N095, 644/N017, 701/N005. |
| 66 | P1597 → P2114 — coffee themed social media posting chain | Supported coffeechain topic; rows 347/N071 and 648/N029 retain `#coffeechain`. These are genuine compatible sources omitted by this structure condition, not newly generated beverage claims. |
| 67 | P1597 → P2122 — unusual coffee themed social media post | Supported specific posting topic; row 0/N004 selects `Weird`, `#coffeechain`. The full original describes a rave at a coffee shop; that extra venue evidence is not needed to invent a beverage witness. |

### Sourdough bread — P1601

All five children concern N037's explicitly ingredient-qualified sourdough bread. Ingredient/praise aspects can be useful topical branches even though their heads are not bread.

| # | Exact edge and saved child label | Judgment and source |
| --- | --- | --- |
| 68 | P1601 → P0188 — Cinnamon in sourdough bread | Supported ingredient branch; row 170/N037 retains cinnamon and sourdough bread. |
| 69 | P1601 → P0233 — Cranberry in sourdough bread | Supported ingredient branch; row 674/N037 retains cranberry and sourdough bread. |
| 70 | P1601 → P0784 — Rosemary in sourdough bread | Supported ingredient branch; row 669/N037 retains rosemary and sourdough bread. |
| 71 | P1601 → P1125 — Brown sugar in sourdough bread | Supported ingredient branch; row 656/N037 retains `brown sugar`, `sourdough bread`. **Invalid saved lexical explanation:** bread matches sugar through the money sense `boodle.n.01`. A valid literal bread→bread mapping is already stored in `words_literal`; the bad selected explanation is not necessary for admission. |
| 72 | P1601 → P2127 — cranberry rosemary brown sugar and cinnamon sourdough bread tastes | Supported **bread-taste parent destination; inherited malformed candidate**. Row 186/N037 explicitly praises the ingredient-qualified bread (`soo good`). Finite tastes is projected as noun taste, so this is not certification of the emitted nominal construction. The same invalid bread→sugar money explanation as #71 is saved, and the same kind of valid literal alternative exists. Neither issue makes the source irrelevant to Sourdough bread. |

### Remaining parent scopes

| # | Exact edge and saved child label | Judgment and source |
| --- | --- | --- |
| 73 | P1707 author's dinner → P0501 — lamb at author's dinner | Supported meal-content branch; row 70/N007 selects `wine was available with the lamb`. The complete original explicitly introduces dinner; that dinner-context rendering already exists in the parent/child description, rather than being generated by SPC02. |
| 74 | P1749 coffee social media → P2114 — coffee themed social media posting chain | Supported under the parent's existing coffee-themed-posting sense; rows 347/N071 and 648/N029 are explicit coffeechain witnesses. Largely a more complete expression, not established narrowing. **Equal original source note sets:** both nodes contain exactly N029/N071. |
| 75 | P1749 coffee social media → P2122 — unusual coffee themed social media post | Supported specific posting topic; row 0/N004 (`Weird`, `#coffeechain`), under that same inherited parent sense. The parent's awkward title is not silently repaired in the artifact. |
| 76 | P1794 good morning greeting to Nostr community → P1793 — good morning greeting to members of Nostr community | Supported compatible addressee form, largely paraphrase rather than a distinct semantic refinement; row 133/N005 (`Gm nostriches`). It offers the parent a source missing from its original N058/N089 evidence. |
| 77 | P2111 themed social media posting chain → P0643 — part of themed social media posting chain | Supported participation/part-related topic; row 175/N086 explicitly supplies the coffeechain participation. A participation topic need not be a kind of chain. |
| 78 | P2111 themed social media posting chain → P2110 — themed social media posting chain | Supported equivalent expression, row 797/N018 (`back`, `coffeechain`, `tomorrow`). The labels agree, but native media attachment differs (to posting versus chain), so the structural rule rejects a compatible source form. |

Only #74 has equal **original source** note sets among these 79 pairs. Different source sets do not prove different category meanings; equal source sets do not by themselves make a meaningful refinement redundant in general. Neither statement concerns the larger sets after transitive propagation.

## Provenance

The final source-node/edge inventory and all four condition edge lists, including their saved mappings, were compared with the initially audited run; they are identical. This audit cites the final artifact rather than the earlier membership-serialization ordering. SHA-256 at audit time:

| File | SHA-256 |
| --- | --- |
| `SPC02-PLAN.md` | `6904514580eeaa8005170b3c19f8c4e30e43021a69f022cf6dd799eb06ad80ca` |
| `SPC02/final/result.json` | `482701b1bb2ff2297f85af2b587379be2fb14cabe7caee78c5d4f226829de971` |
| `SPC02/final/lexicon.json` | `de24b9a73c2181a57dfbaa05c9f48c4bdcd123828cdbefce8254f2eabe3b1d4a` |
| `SPC01/construction/inputs.json` | `7328c07e4ff270c908ed556e495556a6dfb2a2dc9ff6e1e20b38c243e5625c0a` |
| `SPC01/native/parses.json` | `b1f5e6ee04aaf34405228f3816397a36c2ce33d3e0b08c8d84274d40233a5370` |
