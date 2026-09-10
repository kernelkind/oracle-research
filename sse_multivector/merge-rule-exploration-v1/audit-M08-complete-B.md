# M08 complete-B: bounded source-grounded subtree audit

## Scope and evidence

This report covers the 32 assigned disjoint maximal inspection roots, not a semantic cut and not the whole M08 hierarchy. All 32 roots are displayed under the current note-set projection. Their connecting parents, the other inspection forest, and the separately assigned known relations are outside this report's coverage.

Structure and aliases were read from `M08.json`; exact masks and original-ID mappings from `../real-note-fine-segmentation-v1/vectors/vector-map.json`; complete source texts from that directory's `reviewed-input.json`. Every original-ID fragment in this forest was read individually, including every alias. All 1,157 stored fragments were verified by slicing their complete originals at the recorded UTF-8 **byte** ranges and decoding to exact equality. Aliases were not assumed to have identical fragments: for example, the canonical leaf carrying N042/V333,V334 has two-fragment and four-fragment versions, both independently checked.

Complete-original context was available for all 87 covered notes. This reused the prior complete frozen-original readings for 84 notes from the M07-B audit. Six of those originals were freshly revisited where context mattered (N011, N023, N053, N093, N098, N100), and the three newly encountered originals N006, N042, and N044 were read in full. This is not a claim that all 87 originals were needlessly reread this turn. The complete originals remain the entire frozen post text, including any visible truncation. Linked articles, linked images, generated titles, and generated subject strings were not evidence.

M08/M07 frozen source records and M08/M07/M06/M04 alias groups were checked equal. No inputs, embeddings, code, labels, or other files were changed, and no candidate was run. Structural size, score, and amount of projection hiding are not semantic-quality scores.

| Coverage | Count |
| --- | ---: |
| Disjoint inspection roots | 32 |
| Canonical leaves | 436 |
| Original vector IDs, including aliases | 451 |
| Exact UTF-8 fragments checked | 1,157 |
| Complete originals available/read as described above | 87 |
| Internal transitions inspected bottom-up | 404 |
| Displayed / raw-only internal nodes | 216 / 188 |
| Exact recursive matches to M04 / M06 / M07 | 128 / 126 / 106 |
| Internal subtrees exactly matching at least one earlier run | 163 |
| Maximal such exact-match subtrees within this forest | 81 |
| Internal subtrees differing recursively from all three | 241 |
| Of those 241: same original-vector membership somewhere earlier, different children | 51 |
| Of those 241: original-vector membership absent from all three earlier trees | 190 |

The comparison signature is an alias-inclusive leaf followed by an **unordered pair of full recursive child signatures** at every internal node. Equality of top vector membership, note membership, size, or displayed appearance is not sufficient. All 32 inspection roots differ recursively from all three earlier runs. Two roots illustrate the distinction particularly clearly: M08/1085 has M04/984's vector membership; M08/1582 has M04/1587 and M06/1561's vector membership. Neither is an exact recursive match.

The registry identifies every inherited exact structure, including nested matches. All 404 transitions, including those 163 matches, were inspected against their selected masks in complete-original context. Prior full-source knowledge was reused; an earlier semantic verdict was not silently imported as approval. “New membership” above means only relative to M04, M06, and M07, not all previous experiments or all possible meaningful relations.

## Interpretation and registry conventions

Several useful displayed children are concrete: M08/1571 relates three avocado-containing meals; M08/1377 connects four notes about animal killing/use despite opposed attitudes; M08/1445 retains the food-emotion pair; M08/1582 connects three notes through tea; M08/1732 contains four actual Christmas notes plus N092's gift metaphor as a fifth note. These are source-grounded local observations, not an overall ranking or a complete gain/loss comparison.

Broad families, contrasting opinions, and unexpected connections may be valid. Weak placement is distinguished from lost note discovery. A sparse mask cannot borrow unselected meaning simply because another part of its original concerns the desired topic. Conversely, one inconvenient variant's location does not establish a loss where another relevant mask still offers a useful route.

Each section gives exact children, counts, an alias-complete leaf binding registry, and **all** nested transitions in increasing creation-ID order. The adjacency records preserve the complete recursive structure, not merely flattened membership. In prose, transition numbers refer to raw M08 IDs unless explicitly described as displayed; the registry provides the exact display status and replacement ancestor.

- `leaf=Nxxx:Vxxx,Vyyy` binds a canonical leaf to every original alias ID and its source note.
- `idD=(left,right)` is a displayed M08 internal node.
- `idR=(left,right) >ancestorD` is raw-only and gives its first displayed ancestor.
- `~M04/id,M06/id,M07/id` records exact recursive identity in the indicated earlier runs, not approval.
- All unprefixed IDs are M08 IDs. Each section's root is displayed.
- Raw nodes can disappear from the note projection when their note set equals their immediate parent's. Their complete membership is not removed. Recursively hiding masks already shown below a parent likewise does not alter its full membership.

## Per-root observations and complete transition registry

### M08/1085

22 canonical / 22 original IDs / 13 notes; 21 transitions (16 displayed). Exact raw children: (644, 1045). Displayed root; immediate raw parent: 1131, outside this inspection subtree.

Every selected mask actually mentions coffee or coffeechain, including breakfast coffee, fetching coffee as motion, iced coffee, requests, and coffee-shop-related tags. The lower exact lexical children and later combinations therefore remain a useful broad coffee group across 13 notes. Raw 932/979/982/1021/1045 are fully recorded below; their suppression changes the displayed path, not the source membership. This root has exactly M04/984's original-vector membership but different recursive children, so the earlier subtree is not inherited as an exact match. No improvement is claimed merely from gathering additional coffee variants of notes already present.

```text
Leaves
10=N086:V790  58=N036:V281  127=N071:V653  145=N079:V726
166=N086:V797  167=N048:V381  169=N079:V727  176=N024:V187
233=N079:V724  330=N071:V656  365=N038:V297  413=N095:V865
512=N043:V342  550=N035:V276  617=N017:V126  621=N029:V243
632=N029:V244  644=N043:V343  669=N095:V859  673=N005:V043
818=N036:V280  897=N035:V277
Transitions
931D=(233,550) ~M04/917,M06/917,M07/930  932R=(818,931) >954D ~M04/919,M06/919,M07/931  937D=(167,632) ~M04/920,M06/920,M07/936
943D=(176,673) ~M04/922,M06/922,M07/940  945D=(413,617) ~M04/921,M06/921,M07/942  949D=(330,945) ~M04/924,M06/924,M07/945
950D=(365,949) ~M04/926,M06/926,M07/946  953D=(166,950) ~M04/927,M06/927,M07/949  954D=(897,932) ~M04/928,M06/928
957D=(10,669) ~M04/932,M06/932,M07/952  958D=(937,943) ~M04/934,M06/934,M07/953  967D=(512,954) ~M04/935,M06/935
971D=(958,967)  973D=(621,953) ~M04/944,M06/944,M07/965  979R=(957,971) >1003D
982R=(58,979) >1003D  1003D=(169,982)  1015D=(127,1003)
1021R=(973,1015) >1085D  1045R=(145,1021) >1085D  1085D=(644,1045)
```

### M08/1536

10 canonical / 11 original IDs / 5 notes; 9 transitions (5 displayed). Exact raw children: (1261, 1393). Displayed root; immediate raw parent: 1692, outside this inspection subtree.

1046/1393 collect the gamey-meat dislike question, carnivore controversy, and meat-eater fog/clarity claims; 1261 supplies the contrasted vegan and “just eat meat” positions. These are substantive animal-food/diet-attitude relations even though the positions conflict. The N033 source is visibly truncated and the physiological and dietary assertions remain authors' claims. Repeated variants in raw 1176/1181/1314 do not supply additional independent sources. The five-note parent is a coherent broad disagreement/preference family, not evidence of a single dietary recommendation.

```text
Leaves
90=N033:V265  195=N074:V679  235=N087:V799  397=N041:V332
400=N041:V317  441=N090:V814,V815  590=N087:V798  712=N041:V316
762=N033:V264  853=N074:V678
Transitions
1042R=(90,195) >1046D ~M07/1006  1046D=(853,1042)  1176R=(235,441) >1261D ~M04/1010,M06/1012,M07/1104
1181R=(397,762) >1304D ~M04/1039,M06/1042,M07/1106  1261D=(590,1176) ~M04/1049,M06/1051  1304D=(400,1181) ~M04/1089,M06/1090
1314R=(712,1046) >1393D  1393D=(1304,1314)  1536D=(1261,1393)
```

### M08/1563

24 canonical / 26 original IDs / 7 notes; 23 transitions (10 displayed). Exact raw children: (1501, 1523). Displayed root; immediate raw parent: 1726, outside this inspection subtree.

964–1071 connect speaking, sharing knowledge, education, and an invitation for additions; 1027–1118 connect philosophy, acknowledging limited knowledge, openness, and purpose. Those are plausible broad learning/outlook relations. Some joins are weaker: 1058 and 1159 pair a mind being “off” with advice about incomplete knowledge and purpose, while 1330/1346 join sparse “dream,” “ISLAND LIFE,” and “Freedom” masks. The audiobook/literature variants at 976–1078 have a concrete reading relation; 1340/1523 broaden to writing and music. The root links intellectual and leisure material, but the selected words do not establish one philosophy, diagnosis, or travel experience.

```text
Leaves
5=N080:V744  7=N014:V105,V106  25=N080:V742  200=N080:V745
219=N069:V628  270=N069:V634  275=N048:V383  286=N080:V743
467=N043:V339,V340  579=N069:V627  588=N069:V635  606=N069:V617
611=N054:V439  709=N054:V434  734=N069:V637  738=N054:V438
740=N069:V619  744=N054:V436  745=N080:V746  751=N055:V465
808=N069:V629  859=N055:V444  893=N054:V441  904=N069:V636
Transitions
964R=(606,859) >1071D ~M04/1307,M06/1307,M07/957  976R=(286,611) >1078D ~M04/1210,M06/1208,M07/968  997R=(25,976) >1078D ~M04/1293,M06/1289
1009R=(751,964) >1071D ~M04/1582,M06/1575  1025R=(5,997) >1078D ~M04/1389,M06/1388  1027R=(738,904) >1118D ~M04/1503,M06/1495,M07/996
1035R=(200,1025) >1078D ~M04/1409,M06/1411  1052R=(588,1027) >1118D ~M04/1535,M06/1530  1058R=(7,270) >1192D ~M07/1019
1071D=(734,1009)  1078D=(745,1035) ~M04/1489,M06/1480  1111R=(808,1052) >1118D
1118D=(579,1111)  1159R=(219,1058) >1192D  1164D=(1071,1118)
1192D=(740,1159)  1330R=(275,893) >1346D ~M04/1759,M06/1763  1340R=(467,1078) >1523D ~M04/1698,M06/1661
1346D=(709,1330) ~M04/1764,M06/1767  1421D=(1164,1192)  1501D=(1346,1421)
1523D=(744,1340)  1563D=(1501,1523)
```

### M08/1569

21 canonical / 22 original IDs / 6 notes; 20 transitions (9 displayed). Exact raw children: (1377, 1485). Displayed root; immediate raw parent: 1692, outside this inspection subtree.

1030/1064 connect butchered chicken carcasses to the opposed animal-graves quote; 1055/1104 add actual animal by-product/dog-food material. 1224/1264 then bring in the generous pig-slaughter account, and the subsequent N055 variants culminate at displayed 1377, a four-note animal-killing/use group. The contrast is valid; the grave metaphor is not literal burial. 920/1083/1139/1286/1383 relate dog tags, a chihuahua's raw diet, and dog/chicken feed; 1485 adds only a cat tag, appropriately a broader animal extension rather than specific meat-feeding evidence. Root 1569 keeps six notes accessible in an animal/food family. N100's myoglobin is for dogs; water and sunflower seeds are for chickens.

```text
Leaves
6=N048:V376  53=N048:V372  72=N055:V455  89=N055:V453
198=N100:V945  208=N055:V458  218=N013:V093  243=N026:V212
263=N055:V462  306=N055:V456  346=N100:V928  364=N048:V374
418=N048:V380  435=N055:V457  436=N054:V440  478=N055:V454
535=N048:V373,V375  655=N055:V459  778=N026:V213  806=N048:V382
856=N100:V927
Transitions
920D=(436,806) ~M04/930,M06/930,M07/920  1030R=(218,535) >1064D ~M04/1071,M06/1073,M07/999  1055D=(6,346) ~M07/1015
1064D=(364,1030)  1083D=(243,920) ~M04/1229,M06/1226,M07/1032  1104D=(1055,1064)
1139R=(856,1083) >1485D ~M07/1075  1224R=(53,263) >1264D ~M07/1129  1264D=(208,1224)
1286R=(778,1139) >1485D  1289R=(1104,1264) >1377D  1308R=(478,1289) >1377D
1315R=(435,1308) >1377D  1324R=(306,1315) >1377D  1333R=(72,1324) >1377D
1337R=(89,1333) >1377D  1377D=(655,1337)  1383R=(198,1286) >1485D
1485D=(418,1383)  1569D=(1377,1485)
```

### M08/1582

4 canonical / 5 original IDs / 3 notes; 3 transitions (2 displayed). Exact raw children: (370, 1260). Displayed root; immediate raw parent: 1723, outside this inspection subtree.

1196 pairs N042's hot-tea request with N080's morning tea/wee, and 1260 adds N080's other morning-need variant. 1582 extends this genuine two-note tea child with N072/V670's explicit comparison to different ways of making sweet tea. N072's whole post concerns soda bread, but this selected tea analogy is still a relevant beverage/preparation-family connection; it need not describe actually drinking tea. All five original IDs, including the differently fragmented V333/V334 alias pair, were checked individually. This root shares exact membership with M04/1587 and M06/1561 but not their complete recursive structure.

```text
Leaves
222=N042:V333,V334  370=N072:V670  608=N080:V731  898=N080:V730
Transitions
1196R=(222,608) >1260D ~M07/1112  1260D=(898,1196)  1582D=(370,1260)
```

### M08/1630

5 canonical / 7 original IDs / 4 notes; 4 transitions (3 displayed). Exact raw children: (1489, 1497). Displayed root; immediate raw parent: 1741, outside this inspection subtree.

1320/1497 join N092's worry about older bnb guests falling to N053's “We ... overrun ... halp” variants; 1489 joins N048's “Come in!” to N098's “I'm ... in ... corner.” A very broad people/place/concern reading is possible, but these sparse masks supply little direct commonality, and 1630's root join is correspondingly weak. The N053 original involves tomatoes and squirrels, not an established indoor invasion or guest-safety problem; the image was not inspected. N098's kimchi is absent from V909. Actual tomato masks from N053 occur at 1743 and an actual kimchi mask from N098 at 1757, so these weak placements alone do not establish food-discovery losses.

```text
Leaves
157=N092:V831  188=N053:V418,V419  409=N098:V909  470=N053:V416,V417
690=N048:V369
Transitions
1320R=(157,188) >1497D  1489D=(409,690)  1497D=(470,1320)
1630D=(1489,1497)
```

### M08/1645

14 canonical / 14 original IDs / 10 notes; 13 transitions (10 displayed). Exact raw children: (969, 1622). Displayed root; immediate raw parent: 1761, outside this inspection subtree.

926–969 form an exact seven-note grownostr-tag subtree. 1217/1398 connect an allotment effort, desired garden space, and growing one's own food; 1283/1321 supply concrete raised-bed beets on a town lot. 1202's initially sparse half-acre-lot/homesteading pair becomes more directly grounded as those gardening variants arrive. 1622/1645 combine specific home-growing material with the broader tag family, a useful ten-note discovery route. The tags alone do not establish that every tagged note describes the same growing practice, or independently corroborate the authors' food-quality opinions.

```text
Leaves
56=N005:V042  108=N100:V944  164=N031:V255  206=N024:V192
209=N048:V386  224=N022:V154  236=N029:V241  335=N031:V257
549=N022:V157  582=N061:V517  595=N071:V657  677=N022:V156
896=N092:V844  914=N022:V155
Transitions
926D=(206,209) ~M04/949,M06/949,M07/926  927D=(236,896) ~M04/929,M06/929,M07/927  933D=(56,927) ~M04/936,M06/936,M07/932
936D=(595,933) ~M04/940,M06/940,M07/935  938D=(582,926) ~M04/969,M06/969,M07/937  969D=(936,938) ~M04/1001,M06/1001,M07/962
1202R=(108,914) >1321D ~M07/1117  1217R=(224,335) >1398D ~M04/1268,M06/1268,M07/1123  1283R=(677,1202) >1321D
1321D=(549,1283)  1398D=(164,1217)  1622D=(1321,1398)
1645D=(969,1622)
```

### M08/1651

8 canonical / 9 original IDs / 6 notes; 7 transitions (5 displayed). Exact raw children: (129, 1549). Displayed root; immediate raw parent: 1754, outside this inspection subtree.

922/924/1082 provide explicit Nostr/zap material. 1197's “Nature” mask is a weak extension of those platform terms, even though it comes from the same N048 note as legitimate Nostr masks already in that branch. 1403's nostriches term and 1549/1651's actual salsa-sale proposal and first recipe posted on Nostr produce a meaningful broader Nostr/content-sharing family. N048/V389 must not borrow its unselected nostr tag as the meaning of “Nature.” The root still offers real platform-related access through V390/V394; the weak extra variant is not a new note-access failure.

```text
Leaves
129=N028:V230  158=N048:V389  308=N005:V041  357=N048:V394
362=N029:V240  390=N024:V184  459=N048:V390  625=N026:V214,V216
Transitions
922D=(362,390) ~M04/939,M06/939,M07/922  924R=(459,922) >1197D ~M04/959,M06/959,M07/924  1082R=(357,924) >1197D ~M04/1551,M06/1549
1197D=(158,1082) ~M04/1663  1403D=(308,1197)  1549D=(625,1403)
1651D=(129,1549)
```

### M08/1658

10 canonical / 10 original IDs / 4 notes; 9 transitions (3 displayed). Exact raw children: (642, 1571). Displayed root; immediate raw parent: 1729, outside this inspection subtree.

1036/1126 pair avocado in dinner, an omelette, and a beef meal. The subsequent N023 dinner variants and N082 beef variant add details about the same actual ingredient, ending at displayed 1571 with three notes. Their “clean,” “simple,” and “healthy” language is an author's description, not a validated property transferred to the other dishes. 1658 adds N083/V779's vegan matcha-cashew pie: a defensible broad food/plant-based contrast, but no shared avocado ingredient. The four-note root is broader than the particularly clear avocado child.

```text
Leaves
29=N097:V899  334=N023:V161  336=N023:V158  472=N023:V171
578=N082:V771  635=N023:V165  636=N082:V767  642=N083:V779
805=N023:V166  823=N023:V167
Transitions
1036D=(29,334) ~M07/1000  1126R=(578,1036) >1571D ~M07/1063  1405R=(823,1126) >1571D
1437R=(635,1405) >1571D  1443R=(805,1437) >1571D  1515R=(336,1443) >1571D
1566R=(636,1515) >1571D  1571D=(472,1566)  1658D=(642,1571)
```

### M08/1675

21 canonical / 21 original IDs / 9 notes; 20 transitions (9 displayed). Exact raw children: (833, 1639). Displayed root; immediate raw parent: 1715, outside this inspection subtree.

1028–1413 combine dietary variety, better food, avoidance of processed food, and moderation/mostly-plants advice; disagreement or different emphasis is not a failure. 1439/1480 form a concrete meal-planning/lunch-quantity child, and 1385–1555 connect food enjoyment with the social value of sharing meals. 1492/1607 broaden these practical and social eating branches. 1595's fasting tag plus infant interest in food is less specific: the original describes parents delaying the infant's food, not an infant fasting practice. 1639/1675 add further infant-interest material to a broad food-choice/intake family without endorsing feeding or medical advice.

```text
Leaves
2=N055:V448  43=N069:V597  69=N069:V598  84=N070:V644
98=N070:V643  102=N074:V686  136=N070:V640  237=N009:V064
291=N070:V642  331=N070:V645  350=N054:V428  424=N055:V449
479=N061:V509  584=N021:V143  598=N074:V685  682=N055:V447
698=N041:V330  795=N069:V596  800=N074:V688  822=N021:V144
833=N061:V510
Transitions
1028R=(69,136) >1105D ~M04/967,M06/967,M07/997  1029R=(43,102) >1132D ~M07/998  1048R=(598,1029) >1132D
1077R=(291,1028) >1105D ~M04/989,M06/991  1096R=(84,1077) >1105D  1105D=(98,1096)
1132D=(795,1048)  1183R=(331,1132) >1413D  1255R=(1105,1183) >1413D
1385R=(350,682) >1555D ~M07/1252  1413D=(800,1255)  1439R=(237,584) >1480D ~M04/1058,M06/1060
1480D=(822,1439) ~M04/1085,M06/1086  1490R=(2,1385) >1555D  1492D=(1413,1480)
1555D=(424,1490)  1595D=(479,698)  1607D=(1492,1555)
1639R=(1595,1607) >1675D  1675D=(833,1639)
```

### M08/1687

4 canonical / 4 original IDs / 3 notes; 3 transitions (3 displayed). Exact raw children: (1532, 1567). Displayed root; immediate raw parent: 1774, outside this inspection subtree.

1532 relates N052's “Rise ... grind” to N043's actual morning coffee-fetching, stretching, and bowing: a plausible morning-activity connection in full-source context. 1567 instead pairs N052/V409's bare “Rise” with N072's happiness at finding a high-altitude baking site. The whole N052 post is about coffee, so this is a weak word/height association rather than an instruction about bread rising. The three-note parent combines that weak placement with the stronger coffee/morning pair; it is not uniformly a baking group.

```text
Leaves
61=N072:V661  445=N052:V412  461=N043:V351  716=N052:V409
Transitions
1532D=(445,461) ~M04/1439,M06/1437  1567D=(61,716) ~M04/1588  1687D=(1532,1567)
```

### M08/1691

5 canonical / 5 original IDs / 4 notes; 4 transitions (3 displayed). Exact raw children: (892, 1623). Displayed root; immediate raw parent: 1740, outside this inspection subtree.

1465's cacao added to pancakes and “Half & half ≠ cream” have a broad ingredient-choice/substitution relation, but the mask does not establish that either dairy product was used in the pancakes. 1447 joins a no-refined-sugar pie with soda-bread recipe variation and its sweet-tea analogy, another broad recipe/ingredient variation. 1623/1691 add the coffee complaint about half-and-half, making food/drink preferences and ingredients a reasonable qualified parent interpretation. “No refined sugar” and dairy equivalence are not properties of all children, and ingredient co-occurrence beyond the masks is not supplied.

```text
Leaves
192=N083:V777  257=N028:V238  280=N045:V354  742=N072:V671
892=N045:V357
Transitions
1447D=(192,742) ~M04/1275,M06/1273  1465D=(257,280) ~M04/1224,M06/1221,M07/1321  1623R=(1447,1465) >1691D ~M06/1400
1691D=(892,1623)
```

### M08/1696

18 canonical / 18 original IDs / 5 notes; 17 transitions (7 displayed). Exact raw children: (1602, 1605). Displayed root; immediate raw parent: 1716, outside this inspection subtree.

983–1284 are a concrete sourdough/preparation family; 1342/1513 and 1446–1602 relate bread mixing, salt/yeast practice, soda-bread variants, and high-altitude recipe success or difficulty. Many raw nodes merely add another selected variant from an already represented note, but every transition was inspected. 1590 is the broader transition: spaghetti mixing/simmering joins a bread branch. Both are food preparation, yet the spaghetti mask supplies no baking or yeast evidence. The five-note root is a defensible preparation family, broader than its stronger bread-specific children and not one recipe.

```text
Leaves
36=N015:V107  94=N015:V109  112=N089:V808  139=N037:V287
146=N072:V664  161=N037:V292  217=N072:V669  256=N072:V660
354=N089:V807  567=N089:V809  628=N037:V291  634=N096:V893
641=N037:V290  652=N015:V108  687=N072:V658  694=N072:V662
760=N037:V286  837=N089:V806
Transitions
983R=(36,139) >1284D ~M04/931,M06/931,M07/973  1067R=(652,983) >1284D ~M04/950,M06/950  1110R=(94,1067) >1284D ~M04/958,M06/958
1242R=(641,1110) >1284D ~M04/980,M06/980  1265R=(161,1242) >1284D ~M04/997,M06/997  1284D=(628,1265) ~M04/1007,M06/1010
1342D=(760,837) ~M04/1063,M06/1066,M07/1221  1446R=(112,146) >1602D ~M04/1137,M06/1137,M07/1301  1448R=(567,1446) >1602D
1452R=(354,1448) >1602D  1481R=(256,1452) >1602D  1513D=(687,1342) ~M07/1364
1526D=(217,1284)  1590D=(634,1526)  1602D=(694,1481)
1605R=(1513,1590) >1696D  1696D=(1602,1605)
```

### M08/1698

16 canonical / 16 original IDs / 4 notes; 15 transitions (5 displayed). Exact raw children: (1533, 1601). Displayed root; immediate raw parent: 1758, outside this inspection subtree.

1143–1414 gather actual meat purchases, prices, weights, cutting, and fat/tallow preparation across N066/N100. 1207–1290 connect stock from chicken bones, dog scraps, and breaking down a raw-meat bag: legitimate by-product/portioning practices, including different human and pet uses. 1153/1285/1601 relate gamey/bloody taste to the selected steak-trimming/myoglobin material; that is broader meat-character/use context, not proof that the prepared beef was gamey. 1533/1698 form a substantive four-note meat-handling/intake family. Repetition within notes does not increase independent source support.

```text
Leaves
24=N026:V210  175=N066:V573  205=N100:V926  348=N026:V211
367=N100:V924  464=N066:V574  494=N100:V919  511=N066:V578
684=N026:V205  689=N100:V923  721=N033:V268  724=N026:V209
748=N033:V266  764=N033:V267  855=N100:V922  901=N100:V920
Transitions
1143R=(494,511) >1414D ~M07/1079  1153R=(689,764) >1601D ~M07/1087  1179R=(901,1143) >1414D
1207R=(205,684) >1290D ~M07/1120  1212R=(348,1207) >1290D  1240R=(24,1212) >1290D
1244R=(855,1179) >1414D  1271R=(175,1244) >1414D  1285R=(721,1153) >1601D
1290D=(724,1240)  1323R=(464,1271) >1414D  1414D=(367,1323)
1533D=(1290,1414)  1601D=(748,1285)  1698D=(1533,1601)
```

### M08/1709

3 canonical / 3 original IDs / 3 notes; 2 transitions (2 displayed). Exact raw children: (193, 1542). Displayed root; immediate raw parent: 1809, outside this inspection subtree.

1542 joins plain bagels to an easy, reliable spaghetti recipe, and 1709 adds N033/V269's “Normal meat.” All are actual food references, but “plain,” “easy,” and “normal” describe different things: topping choice, preparation difficulty, and a meat contrast. This is at most a weak everyday/simple-food family, not a shared recipe or demonstrated equivalent preference. N033's unselected discussion of gamey meat cannot be treated as an explicit preparation method in this mask.

```text
Leaves
77=N046:V363  193=N033:V269  763=N096:V869
Transitions
1542D=(77,763) ~M04/1319,M06/1315  1709D=(193,1542)
```

### M08/1719

5 canonical / 6 original IDs / 3 notes; 4 transitions (2 displayed). Exact raw children: (160, 1707). Displayed root; immediate raw parent: 1804, outside this inspection subtree.

1281/1401 join the joking suspicion of people who dislike ice cream with N036/V282's bare “ice”: a weak lexical extension, not a shared food attitude. 1707/1719 add N059's explicit resistance-to-new-foods speculation, producing a legitimate broader food-preference/resistance connection between N024 and N059, albeit with the weak ice-only third note. The speculation about color vision and the joke's implications are not validated. Raw 1707 is represented by displayed 1719, so its complete source membership remains available.

```text
Leaves
8=N024:V182  106=N036:V282  160=N059:V497  186=N059:V498
544=N024:V181,V183
Transitions
1281R=(106,544) >1401D ~M04/1346,M06/1346,M07/1171  1401D=(8,1281)  1707R=(186,1401) >1719D
1719D=(160,1707)
```

### M08/1722

9 canonical / 9 original IDs / 4 notes; 8 transitions (4 displayed). Exact raw children: (1619, 1702). Displayed root; immediate raw parent: 1778, outside this inspection subtree.

1456–1511 connect a burger knife-and-fork recommendation with cookware's metal handles at a broad utensil/equipment level, not the same implement or handling advice. 1619 adds the child's plate-versus-bowl ice-cream argument. Separately, 1600/1690/1702 connect that argument and easier licking to N080/V741's boiled-egg/crisps substitution: different proposed alternatives for eating, not nutritional equivalence or one vessel choice. The four-note root supports broad eating methods/preferences with weaker utensil-to-cookware and food-to-container bridges. Only N044's visible headline was evidence, not the linked article.

```text
Leaves
92=N080:V741  293=N068:V587  399=N068:V586  401=N056:V479
437=N044:V353  560=N068:V583  765=N068:V584  766=N056:V478
909=N056:V477
Transitions
1456R=(401,437) >1511D ~M04/1510,M06/1506,M07/1315  1483R=(909,1456) >1511D ~M04/1522,M06/1521  1511D=(766,1483) ~M04/1556,M06/1554
1600R=(92,765) >1702D  1619D=(560,1511)  1690R=(399,1600) >1702D
1702D=(293,1690)  1722D=(1619,1702)
```

### M08/1733

15 canonical / 17 original IDs / 10 notes; 14 transitions (9 displayed). Exact raw children: (1636, 1640). Displayed root; immediate raw parent: 1783, outside this inspection subtree.

1293/1418 connect chef/right-way-to-cook material; 1471/1491 add actual kitchen work and dumplings, and 1611/1640 extend through cooktop functions and cooking-show enthusiasm. 1301–1524 connect real dinners, leftovers, and grilling plans disrupted by storms. 1568/1573's dinner date and the takeout worker's dish are broader social/venue meal contexts, not the same outing. 1636/1733 combine practical cooking, food interest, and dinners into an intelligible ten-note family while retaining more specific children.

```text
Leaves
96=N084:V785  97=N084:V783,V784  109=N039:V303  118=N008:V057
133=N027:V227  137=N039:V304  199=N049:V396,V397  317=N020:V137
322=N077:V712  434=N064:V551  536=N077:V711  547=N039:V302
645=N076:V709  718=N064:V553  908=N010:V069
Transitions
1293R=(536,645) >1418D ~M04/1000,M06/1000,M07/1175  1301R=(109,118) >1430D ~M04/996,M06/996,M07/1185  1367R=(137,1301) >1430D
1418D=(322,1293)  1430D=(547,1367)  1471R=(434,1418) >1491D
1491D=(718,1471)  1524D=(317,1430)  1568R=(97,908) >1573D ~M07/1413
1573D=(96,1568)  1611D=(133,1491)  1636D=(1524,1573)
1640D=(199,1611)  1733D=(1636,1640)
```

### M08/1743

18 canonical / 19 original IDs / 8 notes; 17 transitions (9 displayed). Exact raw children: (1609, 1638). Displayed root; immediate raw parent: 1776, outside this inspection subtree.

1092–1238 contain direct tomato preparation/recipe relations; 1370/1494 add tomato-tortilla breakfast and homegrown tomatoes. The separate 1509 breakfast pair is also substantively tomato-related. 1587 introduces N076/V699's tandori chicken, a broader meal extension with no selected tomato ingredient. 1508/1633/1638 connect mostly-plants advice with squirrels and tomatoes; that is a broad plant/food/animal interaction, not evidence that the diet advice concerns squirrels. The N053 original says the squirrels have given up attacking, whereas V413 omits that qualification; its variants were not treated as contradictory independent accounts. Root 1743 remains broader than the strong tomato children.

```text
Leaves
9=N031:V259  64=N071:V648,V651  159=N096:V880  165=N076:V699
194=N026:V197  214=N053:V415  221=N096:V879  383=N053:V414
416=N071:V652  419=N096:V891  485=N074:V687  489=N026:V199
515=N023:V164  577=N031:V258  663=N053:V413  736=N026:V200
870=N026:V208  902=N026:V198
Transitions
1092D=(419,736) ~M07/1039  1108R=(515,1092) >1238D ~M07/1056  1150R=(221,489) >1206D ~M07/1084
1160R=(194,1150) >1206D  1187R=(902,1160) >1206D  1206D=(159,1187)
1210R=(870,1108) >1238D  1238D=(1206,1210)  1370D=(64,1238)
1494D=(577,1370)  1508R=(485,663) >1638D  1509D=(9,416) ~M04/1073,M06/1076
1587R=(165,1494) >1609D  1609D=(1509,1587)  1633R=(214,1508) >1638D
1638D=(383,1633)  1743D=(1609,1638)
```

### M08/1745

9 canonical / 9 original IDs / 6 notes; 8 transitions (5 displayed). Exact raw children: (1436, 1596). Displayed root; immediate raw parent: 1801, outside this inspection subtree.

1011/1053 join explicit sea-salt ingredients in bagels and risotto. 1451 extends to the actual salt-containing century-egg preservation mixture; 1596 adds recipe water. These are broad ingredients/process connections, not a common preservation method, nor a claim that the bagels are brined. 1344–1436 connect nutrient advice to seed-oil/linoleic-acid claims at a broad nutrition level. 1745 joins those branches as food composition/preparation. No claim about linoleic-acid half-life, risk, or dietary benefit is endorsed by this association.

```text
Leaves
31=N091:V822  202=N096:V884  458=N088:V801  662=N069:V599
750=N046:V362  771=N088:V803  790=N088:V802  793=N063:V538
880=N046:V360
Transitions
1011R=(750,793) >1053D ~M04/998,M06/998,M07/989  1053D=(880,1011) ~M04/1027,M06/1029  1344R=(458,662) >1436D ~M04/1337,M06/1336,M07/1225
1416R=(771,1344) >1436D ~M04/1447,M06/1445  1436D=(790,1416)  1451D=(31,1053) ~M04/1406
1596D=(202,1451)  1745D=(1436,1596)
```

### M08/1751

13 canonical / 13 original IDs / 7 notes; 12 transitions (7 displayed). Exact raw children: (1710, 1725). Displayed root; immediate raw parent: 1772, outside this inspection subtree.

1445 preserves the direct emotion-based food-resistance/sentimental-dumplings pair. 1673/1710 add cooking arguments as a broader food-attitude child. 1155 concerns negative judgments about food/dietary authority; 1225–1305's loss of home-growing skill versus a plant-based/nostr diet generating clicks is a weaker contrast of food practice and rhetoric, not one shared claim. 1654/1689/1725 add childhood-vegetable controversy and the fuller color-vision speculation. The root is a defensible broad food-attitude/opinion family, with the concrete emotional pair kept distinct from unsupported psychological or health conclusions.

```text
Leaves
110=N031:V256  407=N077:V715  474=N090:V813  483=N074:V676
539=N074:V675  553=N074:V677  562=N059:V500  575=N070:V646
593=N059:V502  603=N077:V714  702=N059:V501  719=N074:V682
785=N064:V552
Transitions
1155D=(474,575) ~M07/1089  1225R=(110,483) >1305D ~M04/1230,M06/1227,M07/1130  1275R=(553,1225) >1305D ~M04/1304,M06/1304
1305D=(539,1275) ~M04/1331,M06/1327  1433R=(1155,1305) >1654D  1445D=(562,785) ~M04/1155,M06/1154,M07/1300
1654D=(719,1433)  1673R=(407,1445) >1710D  1689R=(702,1654) >1725D
1710D=(603,1673)  1725D=(593,1689)  1751D=(1710,1725)
```

### M08/1756

23 canonical / 23 original IDs / 11 notes; 22 transitions (14 displayed). Exact raw children: (587, 1708). Displayed root; immediate raw parent: 1785, outside this inspection subtree.

916–1287 build substantial Bitcoin/workshop/pleb material, including the complaint about the Bitcoin-carnivore narrative. 1453/1470/1606/1684 extend through the explicit planned Bitcoin-accepting pizza restaurant and Bitcoin-day tag. These are genuine platform/economy/community connections. In contrast, 1399 pairs N024/V191's “#DCA” with N080/V753's gift of dark chocolate; the latter mask says nothing about Bitcoin. 1708 imports this weak child, and 1756 adds N065's imagined coffee-shop router retaliation without explicit Bitcoin evidence. The root's sparse/weak additions do not remove the useful 1684 branch, and the imagined action was not performed in the original.

```text
Leaves
197=N024:V186  234=N054:V432  248=N095:V866  289=N074:V683
316=N054:V422  380=N055:V451  381=N012:V090  429=N012:V091
442=N048:V392  468=N050:V402  540=N080:V753  570=N050:V403
587=N065:V562  609=N055:V464  613=N048:V393  671=N024:V191
741=N050:V405  753=N024:V185  789=N048:V379  794=N055:V450
804=N074:V684  843=N055:V466  888=N029:V242
Transitions
916D=(753,789) ~M04/918,M06/918,M07/916  917D=(234,916) ~M04/923,M06/923,M07/917  918D=(381,888) ~M04/916,M06/916,M07/918
919D=(917,918) ~M04/925,M06/925,M07/919  925R=(380,919) >948D ~M04/957,M06/957,M07/925  928R=(794,925) >948D ~M04/968,M06/968
930R=(197,442) >939D ~M07/929  939D=(613,930)  942R=(609,928) >948D
948D=(316,942)  956D=(248,939)  993R=(289,948) >1005D
1005D=(843,993)  1100R=(956,1005) >1287D  1287D=(804,1100)
1399D=(540,671) ~M07/1256  1453R=(741,1287) >1684D  1470R=(468,1453) >1684D
1606D=(429,570) ~M04/1703,M07/1451  1684D=(1470,1606)  1708D=(1399,1684)
1756D=(587,1708)
```

### M08/1757

16 canonical / 16 original IDs / 5 notes; 15 transitions (4 displayed). Exact raw children: (1581, 1625). Displayed root; immediate raw parent: 1828, outside this inspection subtree.

1363–1581 connect named local breakfast and explicit India/food masks at a broad cuisine/food-access level. 1339's JapaneseFood tag and “sexi yogo” start more sparsely; 1365–1614 add actual mochi-bread request/travel/combini context and tandori chicken/yogurt, making a defensible varied-food/recipe family rather than one cuisine. 1625 adds explicit kimchi consumption. The five-note root contains real culinary evidence, but locality or untranslated Japanese text was not expanded into facts absent from the originals. N040's no-VAT/no-service-charge variants concern its breakfast venue, not every food here.

```text
Leaves
68=N011:V085  171=N040:V312  190=N011:V086  220=N076:V701
274=N040:V314  321=N078:V722  337=N011:V082  417=N040:V315
492=N040:V313  576=N011:V078  630=N076:V700  660=N078:V721
697=N011:V081  711=N098:V910  776=N011:V079  788=N040:V311
Transitions
1339R=(220,576) >1614D ~M07/1216  1363R=(321,788) >1581D ~M04/1361,M06/1359,M07/1241  1365R=(776,1339) >1614D
1376R=(417,1363) >1581D ~M04/1369,M06/1366  1404R=(190,1365) >1614D  1406R=(660,1376) >1581D ~M04/1465,M06/1462
1425R=(697,1404) >1614D  1520R=(492,1406) >1581D  1529R=(337,630) >1614D
1553R=(171,1520) >1581D  1554R=(68,1425) >1614D  1581D=(274,1553)
1614D=(1529,1554)  1625D=(711,1614)  1757D=(1581,1625)
```

### M08/1769

20 canonical / 20 original IDs / 10 notes; 19 transitions (12 displayed). Exact raw children: (382, 1734). Displayed root; immediate raw parent: 1791, outside this inspection subtree.

944–1205 form a real Sunday/Saturday/weekend-activity family; 1372/1428/1541 add actual weekend coffee-shop restrictions and avoidance. 1128/1369 connect days off, a dated painting challenge, and lunch prepared for coming days as a broad time/planning branch, not all food preservation. 1266/1426/1435 are looser routine/return links involving coffeechain, daily painting, and changing coffee shops. 1329 repeats the weak Japan-trip/Rome-proverb pairing: Rome is not actual travel in N024. 1510/1575 add genuine Charlotte arrival/jet lag, but cannot retroactively convert the proverb into a journey. The ten-note parent is broad time, routines, and travel with specific weak bridges; no whole-tree loss claim follows from N080/V737's placement here.

```text
Leaves
73=N095:V863  75=N018:V128  151=N065:V555  153=N065:V566
216=N080:V737  261=N080:V754  267=N058:V487  379=N017:V123
382=N065:V564  414=N024:V176  428=N065:V567  469=N095:V864
541=N005:V039  566=N092:V840  633=N005:V038  666=N011:V083
704=N095:V862  768=N018:V132  774=N065:V554  915=N080:V759
Transitions
944R=(73,267) >962D ~M04/945,M06/945,M07/941  951R=(469,944) >962D ~M04/955,M06/955  962D=(704,951) ~M04/960,M06/960
1093D=(379,566)  1128R=(75,261) >1369D ~M04/1431,M06/1429,M07/1064  1205D=(962,1093)
1266D=(768,915) ~M04/1505,M06/1497,M07/1159  1329D=(414,666) ~M04/1650,M06/1645,M07/1206  1369D=(216,1128)
1372R=(151,1205) >1428D  1426R=(153,1266) >1435D ~M07/1281  1428D=(774,1372)
1435D=(428,1426)  1510R=(633,1329) >1575D ~M07/1359  1541D=(1428,1435)
1575D=(541,1510)  1650D=(1369,1575)  1734R=(1541,1650) >1769D
1769D=(382,1734)
```

### M08/1777

6 canonical / 6 original IDs / 5 notes; 5 transitions (4 displayed). Exact raw children: (1384, 1667). Displayed root; immediate raw parent: 1812, outside this inspection subtree.

1098/1384 are concrete cooking-duration connections: bread-pan cooking, spaghetti simmering, and brisket smoking. 1660/1667 relate successful food preparation with hoped-for chemotherapy outcomes to storm-disrupted dinner/parade/fireworks plans, a much broader plans-and-setbacks connection. 1777 joins the two branches through cooking and timing, but not all masks describe the same cooking process or kind of delay. The chemotherapy hope remains a personal statement; no treatment result is inferred.

```text
Leaves
86=N039:V298  278=N039:V308  599=N008:V062  714=N096:V894
727=N085:V787  809=N047:V368
Transitions
1098D=(714,809) ~M04/1041,M06/1044,M07/1044  1384D=(727,1098) ~M04/1299,M06/1298  1660R=(278,599) >1667D ~M04/1599,M06/1596,M07/1527
1667D=(86,1660) ~M04/1608,M06/1606  1777D=(1384,1667)
```

### M08/1779

16 canonical / 16 original IDs / 6 notes; 15 transitions (6 displayed). Exact raw children: (1309, 1749). Displayed root; immediate raw parent: 1815, outside this inspection subtree.

1088–1309 connect tasks done with kitchen work, including the two masks explicitly saying work caused photographs to be forgotten. This is a meaningful task/effort relation even though the photo component has another possible discovery use. 1229's generic waiting/wishing and delayed infant feeding are a weaker waiting relation. 1482–1659 join hunger, reluctance to fix eggs, chocolate, and infant food interest/delay; 1717/1749 broaden to food intentions and next-dinner ideas. The six-note parent is a qualified food-work/waiting/planning family. Having both N064/V549,V550 here does not by itself establish loss of photography discovery; generous alternatives across the whole tree are outside this report.

```text
Leaves
18=N054:V423  62=N016:V117  71=N064:V550  130=N016:V110
184=N043:V338  228=N016:V112  283=N016:V111  347=N061:V511
353=N064:V549  408=N064:V548  462=N064:V546  499=N064:V547
530=N061:V512  548=N016:V116  784=N023:V172  869=N016:V118
Transitions
1088R=(184,499) >1309D ~M07/1038  1090R=(462,1088) >1309D  1182R=(71,1090) >1309D
1229D=(18,347) ~M04/1368,M06/1364,M07/1134  1249R=(353,1182) >1309D  1309D=(408,1249)
1482R=(283,530) >1659D ~M07/1330  1486R=(130,1482) >1659D  1496R=(228,1486) >1659D
1580R=(62,1496) >1659D  1594R=(869,1580) >1659D  1659D=(548,1594)
1717D=(1229,1659)  1749D=(784,1717)  1779D=(1309,1749)
```

### M08/1788

18 canonical / 18 original IDs / 8 notes; 17 transitions (9 displayed). Exact raw children: (1681, 1704). Displayed root; immediate raw parent: 1807, outside this inspection subtree.

1017–1174 relate meal toppings/ingredients in risotto and omelette; 1061/1277 add direct pepper and cheese-seasoning context. 1070–1472 connect explicit Paraguay/island/Haiti localities and named paratha at a broader place/food level. 1547–1681 relate a shared rural meal to an Argentina meat purchase, again a broad food-and-place connection rather than the same location or social event. 1459/1704/1788 combine these branches into varied meals, seasoning, and locality material. N055/V467's people/Paraguay/heart mask alone is not a meal, though the separately selected V463 explicitly is.

```text
Leaves
104=N097:V901  123=N055:V463  225=N097:V904  284=N066:V575
320=N055:V452  387=N063:V528  404=N063:V539  486=N096:V881
551=N097:V902  558=N097:V896  610=N097:V903  722=N066:V572
747=N063:V532  749=N066:V576  779=N050:V400  840=N078:V719
852=N055:V467  864=N054:V431
Transitions
1017R=(104,747) >1174D ~M04/1003,M06/1003,M07/993  1041R=(551,1017) >1174D ~M04/1045,M06/1048  1061R=(404,486) >1277D ~M04/1022,M06/1022,M07/1023
1070R=(320,864) >1076D ~M07/1029  1076D=(852,1070)  1136R=(610,1041) >1174D
1138R=(558,1136) >1174D  1174D=(225,1138)  1277D=(387,1061) ~M04/1276,M06/1274
1280D=(840,1076)  1459D=(1174,1277)  1472D=(779,1280)
1547R=(123,722) >1681D ~M04/1408,M06/1410  1666R=(284,1547) >1681D ~M04/1484,M06/1476  1681D=(749,1666)
1704D=(1459,1472)  1788D=(1681,1704)
```

### M08/1789

13 canonical / 13 original IDs / 11 notes; 12 transitions (10 displayed). Exact raw children: (1627, 1718). Displayed root; immediate raw parent: 1823, outside this inspection subtree.

921–1063 are direct GM/Nostr greeting children. 1170's bare N048/V385 “Gentoo” supplies weak greeting evidence, and 1327's “Gm nostriches” with N098/V906 “I'm ... goblin” is at most a playful identity/address connection. 1537 combines those sparse additions with the real greetings. 1442–1627 contain actual mochi-bread/combini and gianguja/melanger/store material, a broad food/preparation connection rather than one recipe. 1718 adds cooking beans on a rocket stove to the greeting branch; 1789's final food/greeting join is correspondingly loose. The goblin-only mask must not silently inherit the original's unselected kimchi.

```text
Leaves
19=N048:V385  38=N011:V080  74=N081:V764  124=N005:V037
183=N040:V310  191=N011:V087  344=N099:V914  352=N001:V004
501=N098:V906  514=N089:V805  619=N081:V763  624=N058:V486
884=N064:V541
Transitions
921D=(344,884) ~M04/933,M06/933,M07/921  929D=(183,921) ~M04/961,M06/961,M07/928  1010D=(624,929) ~M04/1205,M06/1204,M07/988
1063D=(514,1010) ~M04/1234,M06/1232,M07/1024  1170D=(19,1063) ~M04/1579,M06/1570,M07/1099  1327D=(124,501) ~M04/1696,M06/1694,M07/1203
1442R=(74,191) >1627D ~M04/1651,M06/1646,M07/1297  1479R=(38,1442) >1627D  1537D=(1170,1327) ~M04/1751,M06/1753
1627D=(619,1479)  1718D=(352,1537)  1789D=(1627,1718)
```

### M08/1792

13 canonical / 13 original IDs / 5 notes; 12 transitions (5 displayed). Exact raw children: (1394, 1473). Displayed root; immediate raw parent: 1820, outside this inspection subtree.

1056/1394 are a direct raw-milk pair, with N051's humility/stacking wording left in context. 1044/1074 and 1057–1473 form a genuine wine-with-food, wine-quality, and cooking-wine family; the refusal to drink wine is a valid contrasting position, not contradiction that invalidates grouping. 1792 broadens to raw milk and wine as consumed liquids associated with food or preference. This is a reasonable five-note beverage family, not a claim that wine and raw milk have equivalent preparation, health effects, or endorsement.

```text
Leaves
63=N007:V056  65=N007:V053  290=N076:V706  304=N076:V707
314=N006:V044  338=N076:V708  618=N076:V704  653=N063:V536
715=N051:V408  739=N051:V407  868=N076:V705  879=N007:V054
890=N007:V055
Transitions
1044R=(338,879) >1074D ~M04/972,M06/972,M07/1007  1056R=(314,739) >1394D ~M04/948,M06/948,M07/1017  1057R=(65,868) >1101D ~M04/1065,M06/1067,M07/1018
1073R=(890,1044) >1074D  1074D=(63,1073)  1101D=(290,1057) ~M04/1098,M06/1097
1119R=(653,1101) >1473D ~M04/1127,M06/1135  1167R=(304,1119) >1473D ~M04/1195,M06/1197  1357R=(618,1167) >1473D ~M04/1255,M06/1252
1394D=(715,1056) ~M04/1059,M06/1062  1473D=(1074,1357)  1792D=(1394,1473)
```

### M08/1795

23 canonical / 25 original IDs / 10 notes; 22 transitions (11 displayed). Exact raw children: (1637, 1746). Displayed root; immediate raw parent: 1814, outside this inspection subtree.

955–1408 build family/parenting material, and 1538/1557 directly relate children's food wishes. 1617–1746 connect those to feeding children and the vegetable controversy, though 1512's older bnb guests are a weaker people/care extension, not explicit family. 1218–1364 concern consumer/venue arguments and resentment rhetoric; 1292/1559 connect derogatory dietary-authority language to the Lunchly-market argument without validating the insults. 1637/1795 combine family feeding with food-market controversy. Different stances and tones can belong to this broad family; the many N003 variants are not independent corroborating sources.

```text
Leaves
11=N074:V681  13=N090:V810,V811,V812  26=N003:V026  42=N068:V582
107=N003:V027  140=N061:V513  173=N028:V233  204=N003:V031
292=N069:V603  384=N003:V024  406=N074:V680  423=N003:V030
431=N028:V234  473=N024:V188  507=N069:V605  517=N003:V032
529=N065:V558  543=N065:V559  665=N065:V557  679=N003:V025
813=N003:V028  832=N092:V830  882=N003:V033
Transitions
955D=(140,507) ~M04/1105,M06/1104,M07/951  1007R=(473,955) >1034D ~M04/1378,M06/1378,M07/986  1034D=(292,1007) ~M04/1513,M06/1508
1218R=(107,543) >1364D ~M07/1124  1235R=(529,1218) >1364D  1236R=(665,1235) >1364D
1292R=(13,26) >1559D ~M06/1649,M07/1174  1361R=(679,1236) >1364D  1364D=(882,1361)
1408D=(204,1034)  1512R=(832,1408) >1561D  1538R=(42,431) >1557D ~M04/1278,M06/1276,M07/1387
1557D=(173,1538) ~M04/1301,M06/1300  1559D=(384,1292)  1561D=(517,1512)
1617R=(406,1561) >1721D  1637D=(1364,1559)  1676R=(11,1617) >1721D
1703R=(423,1676) >1721D  1721D=(813,1703)  1746D=(1557,1721)
1795D=(1637,1746)
```

### M08/1796

15 canonical / 16 original IDs / 6 notes; 14 transitions (6 displayed). Exact raw children: (1752, 1773). Displayed root; immediate raw parent: 1817, outside this inspection subtree.

1148–1603 link actual Swiss/French/London brand context and a return from Brussels with gifts: broadly places, goods, and travel, not identical locations or brands. 1478 pairs cherry-flavoured Kreik with the Khyber Pass/St Marks Place mask, a weak drink/place join; later variants make N093's food-location context explicit but do not establish that the drink came from that venue. 1677–1752 relate the local pizza-restaurant goal to actually choosing another coffee shop, with the imagined router retaliation kept distinct from the action. 1773/1796 form a broad food/venue/place/lifestyle parent containing those weak bridges.

```text
Leaves
1=N056:V471  57=N080:V750  87=N050:V401  268=N080:V749
342=N065:V571  443=N065:V570  456=N080:V755  503=N027:V220
505=N093:V848,V849  656=N093:V847  664=N093:V846  685=N056:V470
707=N080:V752  761=N056:V472  836=N065:V565
Transitions
1148D=(268,503) ~M07/1083  1253R=(1,1148) >1603D ~M07/1149  1354R=(761,1253) >1603D
1455R=(685,1354) >1603D  1478R=(456,656) >1565D ~M07/1328  1493R=(707,1478) >1565D
1539R=(505,1493) >1565D  1565D=(664,1539)  1603D=(57,1455)
1677R=(87,443) >1752D  1724R=(342,1677) >1752D  1752D=(836,1724)
1773D=(1565,1603)  1796D=(1752,1773)
```

### M08/1800

19 canonical / 19 original IDs / 8 notes; 18 transitions (7 displayed). Exact raw children: (1732, 1764). Displayed root; immediate raw parent: 1816, outside this inspection subtree.

941 joins explicit post-Christmas and Christmas-card masks; 972–1121 add Santa's absence/lunch and further Christmas variants, producing a displayed three-note Christmas child. 1223/1382/1521 broaden through N092's “today is a gift” metaphor and N080's gin gift: legitimate gift-related associations, but neither is explicitly Christmas gifting. 1628–1732 add N062's actual Christmas-lunch headline, costs, and budget tips, yielding a displayed five-note group containing all four concrete Christmas notes plus N092. 1099–1297 form a real pizza-day child; 1764 adds an Easter pie as a broader food-occasion relation. Root 1800 combines holidays/observances/food and gift language without asserting one shared date or occasion.

```text
Leaves
141=N054:V425  287=N099:V915  389=N099:V917  396=N054:V426
420=N054:V424  438=N080:V751  451=N064:V544  455=N064:V545
460=N062:V519  546=N050:V398  561=N062:V520  657=N092:V841
659=N062:V518  686=N064:V543  723=N083:V782  726=N099:V916
772=N092:V842  777=N080:V747  798=N080:V748
Transitions
941D=(686,777) ~M04/981,M06/981,M07/939  972R=(141,941) >1121D ~M07/964  989R=(455,972) >1121D
1022R=(451,989) >1121D  1062R=(420,1022) >1121D  1069R=(396,1062) >1121D
1099R=(546,726) >1297D ~M04/976,M06/976,M07/1046  1121D=(798,1069)  1149R=(287,1099) >1297D ~M04/1032,M06/1033
1223R=(657,1121) >1521D  1297D=(389,1149) ~M04/1135,M06/1134  1382R=(772,1223) >1521D
1521D=(438,1382)  1628R=(659,1521) >1732D  1674R=(460,1628) >1732D
1732D=(561,1674)  1764D=(723,1297)  1800D=(1732,1764)
```

## Limits and outstanding questions

There are no uninspected transitions or unread/unchecked alias fragments inside these 32 roots. Complete-original context covers every included source as specified above. The report does not cover their connecting parents, the other assigned forest, or all alternative relevant masks across M08. It therefore does not claim a full-tree semantic verdict or a completed comparison of all known relations.

Directly witnessed weak joins include the sparse “overrun”/guest-safety and corner/welcome pairings at 1630, “Rise” beside the high-altitude baking-site mask at 1567, the Rome proverb beside Japan travel at 1329, the dark-chocolate gift beside “#DCA” at 1399, and cherry-flavoured Kreik beside a venue/location mask at 1478. Some retain earlier exact structure, demonstrating why a recursive match is not itself a positive semantic assessment.

There are also clear alternate-mask safeguards against premature loss claims: N053's actual tomato masks remain under 1743 while its vague “overrun” masks occur elsewhere; N098's actual kimchi mask remains under 1757 while its goblin/corner fragments occur elsewhere; N048's explicit Nostr masks remain within 1651 despite the weak “Nature” extension. The placement of N064's two work/photo masks under 1309 and N080's future-lunch mask under 1769 was recorded without declaring their respective broader relations lost. That requires the separately assigned whole-tree alternate-mask comparison.

The input limitations remain substantive: sparse tags/words, compound and discontiguous masks, aliases with differing fragmentation, visibly truncated posts, and embedded jokes or speculative claims. The N053 image was not used to decide what “overrun” depicts. Untranslated Japanese text was preserved without adding an interpretation. Dietary/physiological assertions were not endorsed, animal-grave language was not read literally, and imagined coffee-shop retaliation was not reported as performed.

M08's gathering of same-note variants causes many raw transitions to be projected away in this forest. The counts document that structural fact; they are not evidence of semantic improvement or harm. Useful narrow children coexist with broad families and weak joins. This bounded analyst audit does not require all variants or all same-subject notes to reunite, select a preferred merge rule, or stand in for the user's judgment.
