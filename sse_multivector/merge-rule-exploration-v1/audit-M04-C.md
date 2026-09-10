# M04 semantic audit C

These are provisional analyst judgments, not user approvals. No labels, memberships, inputs, or display rules were changed.

## Coverage

Read every mask and internal merge below the 22 raw points listed below: 339 canonical vectors, 347 original vector IDs, 1,043 fragments, 317 internal merges, and 67 source notes. All 1,043 fragments were also checked against their original UTF-8 byte ranges. Full original notes were consulted for the specific interpretations discussed here; this does not claim that every source note was reread in full.

These disjoint subtrees are inspection batches, not a proposed cut. The remaining connecting parents are inspected separately. A one-vector inspection batch such as point913 is not a displayed one-note group.

Sources: `M04.json`; `../real-note-fine-segmentation-v1/vectors/vector-map.json`; `../real-note-fine-segmentation-v1/reviewed-input.json`. Comparisons use M01–M03 and the frozen HDBv3 raw tree. Subject strings in the vector map were not used as semantic evidence.

## 1. Food preservation is available without inheriting most notes

**Evidence.** These exact masks give three distinct source notes:

- V099 / N013: ⟦stock pots rolling⟧ ⟦chicken stock⟧ ⟦save carcasses when we butcher⟧ ⟦I’ll pressure can it⟧ ⟦store in the pantry⟧
- V148 / N022: ⟦beets⟧ ⟦Vac sealed⟧ ⟦ready for the freezer⟧
- V939 / N100: ⟦vacuum sealer⟧

N013's complete note describes twice-yearly stock preparation, pressure canning, and pantry storage. N022 describes vacuum-sealed beets, freezing, and garden space. N100 describes cutting beef, saving scraps for animals, and buying and using a vacuum sealer. The full notes confirm rather than invent this connection.

The comparison searched displayed groups for at least one relevant mask from each note, not for every duplicate vector. Allowed masks were N013 V096/V097/V099–V102; N022 V148/V149/V153; and N100 V932–V939/V942/V943. Thus alternative representations, including generic preservation tags, were allowed.

| Run | Smallest displayed note set found | Notes | Canonical vectors |
| --- | --- | ---: | ---: |
| HDBv3 | 1352 | 85 | 378 |
| M01 | 1477 | 3 | 9 |
| M02 | 1693 | 4 | 9 |
| M03 | 1384 | 10 | 21 |
| M04 | 1566 | 3 | 12 |

**Analysis.** M01 and M04 both supply useful three-note discovery absent from the baseline under this check. This is not a new M04 improvement over M01. M04's smaller raw three-note group1514 is collapsed by the unchanged note-set display rule; displayed1566 additionally carries N100's poultry-feeding masks and N013's pressure-canning mask. The note set stays the same, but the displayed group's complete mask scope is broader than preservation alone. M01's three-note mask set is cleaner for this particular interpretation.

M04/1660 then joins1566 to1583, whose masks include packing food, eating kimchi from a tub, and eating ice cream from a plate. Those are broader food-handling connections, not additional preservation examples. Their presence at an ancestor does not remove the smaller useful descendants.

## 2. An unexpected small group deserves inspection, not automatic rejection

**Evidence.** M04/1495 contains exactly:

- V500 / N059: ⟦emotion-based resistance to new foods⟧
- V501 / N059: ⟦Maybe seeing the world with a restricted color palate tones down⟧ ⟦emotion-based resistance to new foods⟧
- V552 / N064: ⟦Today meat dumplings⟧ ⟦out of sentiment⟧
- V182 / N024: ⟦people⟧ ⟦don’t like ice cream⟧ ⟦else⟧ ⟦hiding⟧

N059 proposes an explanation for resistance to new foods. N064 explicitly says the dumplings are sentimental. N024 jokes that people who dislike ice cream might be hiding something; it does not present a clinical psychological finding.

**Analysis.** This is a defensible broad connection between food preferences and emotional or personal associations, despite different claims and tone. It is not one shared psychological mechanism. Checking N059 V500/V501, N064 V552, and N024 V181–V183 finds the first available displayed groups at HDBv3/1517 (95 notes), M01/1708 (96), M02/1825 (58), M03/1536 (29), and M04/1495 (3). These counts locate a real change in available note sets; whether the shared meaning warrants a useful destination remains a human semantic judgment.

The parent1570 adds broader diet/food masks from1460. It does not change the four masks inside1495.

## 3. Good cooking descendants coexist with weak early pairs

**Evidence.** Several small descendants have explicit support:

- M04/999: V103 / N014 ⟦I have⟧ ⟦crockpot of beef stew⟧ and V826 / N092 ⟦I got up early and put the roast and veggies in the crockpot⟧.
- M04/1004: V206 / N026 ⟦i⟧ ⟦rotisserie chickens⟧ ⟦bagged⟧ ⟦meat⟧ ⟦made⟧ ⟦chicken stock from the bones⟧ and V094 / N013 ⟦stock pots rolling⟧ ⟦chicken stock⟧ ⟦We save carcasses when we butcher⟧.
- M04/1070: V197 / N026 ⟦Today i⟧ ⟦Acquired, roasted and prepared 12 pounds or more of tomato’s to make salsa⟧ and V891 / N096 ⟦Spaghetti Bolognaise⟧ ⟦tin chopped tomatoes⟧ ⟦tin tomato purée⟧ ⟦Once beef is all the same colour add⟧ ⟦1 tin of water⟧.
- M04/938 and its same-note expansions: brisket in a smoker from N019 and N085.

Other early pairs are less convincing at that level of specificity:

- M04/1305: V921 / N100 ⟦sirloin strip sub primal⟧ ⟦cut 15 steaks⟧ and V540 / N063 ⟦Mushroom Risotto with Shrimp⟧ ⟦Lemon⟧.
- M04/1482: V884 / N096 ⟦Spaghetti Bolognaise⟧ ⟦add⟧ ⟦1 tin of water⟧ and V911 / N098 ⟦I⟧ ⟦eating⟧ ⟦whole tub⟧ ⟦kimchi⟧.
- M04/1300: V247 / N030 ⟦tomato turn red⟧ ⟦Because⟧ ⟦saw⟧ ⟦salad dressing⟧ and V698 / N075 ⟦Steak and cheese⟧ ⟦raw onions white or red⟧ ⟦dont matter⟧. V248 is an alias of the same vector with different fragment boundaries: ⟦tomato⟧ ⟦turn red⟧ ⟦Because⟧ ⟦saw⟧ ⟦salad⟧ ⟦dressing⟧.

**Analysis.** Food, quantities, or colour provide possible broad commonalities, but these pairs do not share the specific operation or ingredient supported by the stronger examples. This does not establish a lexical cause, nor a new regression relative to every other run. All-pairs average still merges individual vectors first when they have the best eligible score; it cannot require group-wide corroboration when the groups are singletons. Later ancestors preserve the useful crockpot, stock, tomato-preparation, and brisket descendants. Rejecting those entire ancestors would discard real structure along with questionable attachments.

## Other inspected branches

The entries describe actual contents; they are not generated hierarchy titles.

| Raw point | Observation and provisional judgment |
| --- | --- |
| 1617 | Pancake recipe, Full English Breakfast, plain bagels, and an easy pasta recipe. Broad food/meal preparation is plausible; no shared specific recipe is claimed. |
| 1737 | Omelette toppings, risotto herbs, pasta seasoning, dietary-fat claims, fibre/protein/omega3, bagels, and salt preservation. Ingredient/food-composition commonality is broader than seasoning alone. Claims about bodily effects remain the notes' claims. |
| 1673 | Christmas-lunch budgeting, a rural Paraguayan shared meal, and an Argentinian meat purchase. Regional meals and costs connect the notes; no common country is inferred. |
| 1460 | Meal planning, packing, infant interest in food, processed-food criticism, diet variety, and food-storage terms. Broad food practices are plausible, with narrower dietary descendants preserved. |
| 1575 | Vegan and carnivore statements, meat preference, and diet commentary. Opposing positions remain relevant to shared subject discovery. |
| 1612 | Recipe feedback, enjoyment of meals, cooking success, and a minimal cooktop versus a simple-looking Chinese dish. The last pair1285 is weakly linked by presentation/simplicity, not the same cooking method. |
| 1694 | Pizza, restaurant availability, ordering/takeout, dining out, and meals. A narrower pizza-day descendant remains; restaurant-closure masks need a broader parent than ordering a meal. |
| 1271 | Beets grown in a 4x4 raised bed join four hens/four eggs. A quantity attraction is possible, but egg-only descendant992 survives. |
| 1266 | Avocado in an omelette, with beef, and in an egg/bread meal. Clear shared ingredient with different dishes. |
| 1467 | Egg cooking/laying/preservation/coffee/dinner masks, plus olive oil, cheese omelette, and pie masks in a separate descendant. Do not call the entire ancestor an egg-only group. |
| 1516 | Vegan/gluten-free/no-bake pie, pancakes, reluctance to cook eggs, chocolate snacking, and an infant's interest in food. Small pair1123 is weakly connected by food timing/reluctance; larger dietary/preparation scope is broad. |
| 1571 | Meat cutting, fat/scraps, pet feeding, gamey flavour, purchase quantities, then tomato/water/kimchi material. Useful meat/pet-food descendants survive; the water/kimchi pair is discussed above. |
| 1459 | Strong shrimp sushi/risotto descendant1204; Tandori chicken and the steak/lemon pair broaden it. No shrimp-only claim is valid for the complete parent. |
| 1477 | Many explicit onion/garlic/carrot/tomato and cooking-process relationships across risotto, Bolognaise, and meals. Tomato-joke/raw-onion pair1300 is much weaker. Ingredient-sharing need not imply identical recipes. |
| 1598 | Salsa tomatoes, Bolognaise tomatoes, homegrown breakfast tomatoes, tomato tortillas; later Tandori chicken and cherries/squirrel-attacked tomatoes. The strong tomato-use descendants are more specific than the final parent. |
| 1623 | Cheesesteak, beef dishes/cutting, butter/tallow, and beet side portions. Coherent beef and fat descendants; beet portions are not beef. |
| 913 | One cookware mask; its later attachment must be judged with its parent, not as a standalone displayed group. |
| 1509 | Rocket-stove vegetables and a lamb/potato/broccoli dinner. Shared cooking/meal ingredients are real although the stove and dinner experience differ. |
| 1480 | Crockpot meals, carcass stock, cooking/grilling, kitchen work and equipment. Compound masks are present, but several concrete cooking descendants survive. |
| 1537 | Brisket smoking, bread pans/heat/ashes, cast-iron cookware, frying and toasted bread, a charcoal-based stove. A broad cooking-heat/equipment connection is plausible, without inferring an unseen oven from N047's video. |

## Limits

No complete semantic pass rate is inferred. The source input contains both very narrow masks and large compound masks. Some weak pairs may be embedding limitations, source-mask ambiguity, consequences of greedy irreversible merging, or combinations of these. Changing only the merge rule isolates which resulting groups change; it does not independently identify every cause of a poor vector connection.

The food-preservation and food-emotion checks search explicit alternative mask lists. They are reproducible, bounded checks of available meaningful note access, not an oracle covering every possible interpretation. No overall winner is selected from these examples.
