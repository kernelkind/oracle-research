# M07 complete-B: bounded source-grounded subtree audit

## Scope and method

This audit covers the 38 assigned, disjoint M07 raw reading roots below, not a semantic cut and not the whole hierarchy. The 24-canonical-vector reading cap is organizational, not a quality threshold. All 38 roots are displayed nodes under the current note projection. Their connecting parents are outside this report.

Evidence was read from the frozen `real-note-fine-segmentation-v1/vectors/vector-map.json` and complete `reviewed-input.json` originals, with structure from `M07.json`. Every selected original-ID mask, including every alias, was read. Each of the 1,236 fragment spans was checked as a UTF-8 **byte** slice of its original and decoded exactly equal to the stored fragment. The 96 complete source originals were read: N001–N100 except N006, N025, N042, and N044. “Complete” means the entire frozen original; visibly truncated source posts remain truncated evidence. Generated labels, generated subject strings, linked pages, and inferred image contents were not evidence.

The score definition in `surrounding-connections.md` was read for context: M07 uses positive linear angular affinities, original weighted degrees, and the PARIS merge ratio. These structural/numerical properties are not semantic scores. No candidate was run and no input, code, model output, or label was changed.

| Coverage | Count |
| --- | ---: |
| Disjoint reading roots | 38 |
| Canonical vector leaves | 455 |
| Original vector IDs, including aliases | 469 |
| Mask fragments checked against UTF-8 byte ranges | 1,236 |
| Complete source originals read | 96 |
| Internal transitions freshly inspected bottom-up | 417 |
| Displayed internal nodes / raw-only internal nodes | 415 / 2 |
| Exact recursive matches to M04 / M06 | 75 / 75 |
| Exact matches to either / both | 76 / 74 |
| Maximal exact-match subtrees inside this forest | 59 |
| Internal subtrees differing from both | 341 |

Exact comparison uses an alias-inclusive leaf signature and an **unordered pair of complete recursive child signatures** at every internal node. Equal top membership is not sufficient. M07, M04, and M06 alias groups were checked equal, and M07/M06 frozen source records were checked equal. None of the 38 reading roots exactly matches either earlier tree. Every transition here received fresh source-grounded inspection, including all 76 exact matches; no earlier semantic verdict or “approval” is imported. The registry nevertheless records every exact match, including nested ones, so that structural continuity is explicit. A match can be weak, as the observations below demonstrate.

## Reading the findings and registry

“Useful” or “weak” below is a bounded analyst interpretation of the selected masks in full-original context, not user approval or a claim of known-label recovery. A broad family, contrast, opposed position, or unfamiliar connection can be meaningful. Sparse masks cannot borrow unselected content merely because that content occurs in the same note. Whole-note context is used to prevent misreading, not to replace the selected mask.

The clearest local examples in this forest include displayed M07/1080 (three-note visual practice), M07/1455 (four-note Christmas), M07/1523 (four-note restaurant access), and M07/1564 (six-note food/time family containing the relevant stock, future lunch, and preserved-egg sources). These are concrete usable alternatives, not a complete gain/loss comparison against earlier runs. Broad parents do not erase displayed children. No conclusion that a note has become inaccessible is based on the reunion—or failure to reunite—of one exact set of vectors.

Each root section records its exact raw children, canonical/original/note counts, source-bound leaf registry, and **every internal transition**, in increasing creation-ID order. Together the leaf bindings and adjacency records preserve the full nested binary structure; they are not flattened memberships.

- `leaf=Nxxx:Vxxx,Vyyy` binds a canonical leaf to its original IDs, including aliases.
- `idD=(left,right)` is a displayed M07 internal node; `idR` is raw-only.
- `~M04/id,M06/id` means exact recursive structural identity, not equal membership and not semantic approval.
- All unprefixed node numbers are **M07** IDs. Earlier-run IDs are explicitly prefixed.
- The only raw-only internal nodes here are 970 and 1026, both inside root 1630; their first displayed ancestor is 1072. Their source membership remains present. Recursive hiding of a parent's displayed masks does not remove its full membership.

## Per-root observations and complete transition registry

### M07/1779

24 canonical / 26 original IDs / 18 notes; 23 internal transitions. Exact raw children: (1703, 1758). Root displayed; immediate raw parent: 1797 (outside this reading subtree).

963 pairs N048/V391 (“Photography”) with N080/V761 (art/painting tags); 1080 adds N064/V549, whose kitchen work led to forgotten photographs. This is a useful, displayed three-note visual-practice group, not a requirement that all photography-related masks reunite. 1091 has a legitimate movement relation (stretching/bowing and walking/biking). In contrast, 1206 pairs N011/V083's Japan trip with N024/V176's Rome proverb: the latter is not travel. 1415's dated snack and infant age, 1594's supermarket-chemical complaint and last-year salsa, and the upper joins are considerably looser chronology, activity, or food associations. They do not remove 1080.

```text
Leaves
13=N090:V810,V811,V812  25=N080:V742  26=N003:V026  117=N031:V254
154=N048:V391  203=N080:V760  353=N064:V549  398=N043:V345
414=N024:V176  415=N012:V089  430=N069:V615  439=N069:V621
554=N080:V761  600=N048:V388  606=N069:V617  633=N005:V038
666=N011:V083  744=N054:V436  815=N061:V508  859=N055:V444
893=N054:V441  900=N039:V309  905=N026:V217  911=N058:V491
Transitions
957D=(606,859) ~M04/1307,M06/1307  963D=(154,554)  1080D=(353,963)
1085D=(203,600)  1091D=(398,439)  1092D=(430,893)
1118D=(25,957)  1174D=(13,26) ~M06/1649  1206D=(414,666) ~M04/1650,M06/1645
1291D=(744,1118)  1359D=(633,1206)  1375D=(1085,1174)
1415D=(415,815)  1463D=(900,911)  1497D=(1092,1375)
1582D=(1080,1091)  1586D=(1359,1463)  1594D=(117,905)
1640D=(1291,1586)  1703D=(1497,1594)  1734D=(1415,1582)
1758D=(1640,1734)  1779D=(1703,1758)
```

### M07/1676

24 canonical / 24 original IDs / 18 notes; 23 internal transitions. Exact raw children: (1627, 1646). Root displayed; immediate raw parent: 1725 (outside this reading subtree).

The lower greeting, welcome, shared joy, gratitude, and conduct branches (934, 943, 956, 967, 974, 1003, 1048) support a broad positive-affect/social family. N051/V406 is “Stay humble,” not raw milk merely because milk occurs elsewhere in that note. 1053 has genuine Christmas context, though N054/V424's mask omits the source's negation about Santa. 1223 joins the cute infant with jealous “Miss unicorn”; the latter's species is not identified. 1464's stove-tinkering invitation and storm/fireworks report are a weak outdoor-activity join. The root combines greetings, wellbeing, pleasure, and occasions rather than one shared event.

```text
Leaves
47=N064:V542  113=N055:V445  126=N092:V825  196=N043:V347
287=N099:V915  420=N054:V424  451=N064:V544  471=N069:V606
476=N069:V632  517=N003:V032  522=N058:V496  542=N100:V918
545=N094:V852  597=N001:V008  667=N048:V370  704=N095:V862
725=N039:V307  772=N092:V842  842=N069:V616  845=N071:V655
861=N055:V446  862=N051:V406  873=N069:V614  891=N061:V515
Transitions
934D=(113,873) ~M04/971,M06/971  943D=(667,934) ~M04/982,M06/982  956D=(842,861)
967D=(471,862) ~M04/1156,M06/1155  974D=(126,542) ~M04/1024,M06/1026  1003D=(47,974) ~M04/1189,M06/1191
1048D=(476,772)  1053D=(420,451)  1077D=(943,1003)
1132D=(196,967)  1150D=(517,956)  1223D=(845,891) ~M04/1581,M06/1571
1246D=(522,1077)  1349D=(704,1048)  1410D=(1053,1349)
1459D=(1132,1246)  1464D=(597,725)  1482D=(545,1150)
1566D=(1459,1482)  1616D=(1223,1566)  1627D=(287,1410)
1646D=(1464,1616)  1676D=(1627,1646)
```

### M07/1086

23 canonical / 23 original IDs / 15 notes; 22 internal transitions. Exact raw children: (271, 1060). Root displayed; immediate raw parent: 1158 (outside this reading subtree).

All 23 original masks concern coffee, coffee-taking/preparation, or explicit coffee-related tags across 15 notes. The exact small coffee/tag children grow through hot/iced coffee, breakfast coffee, requests, and fetching coffee; 1086 adds N052/V411's bean grinding. Tag-only children carry less detail but still expose a real coffee relation. No note-access improvement is claimed merely because duplicate coffee representations are arranged differently.

```text
Leaves
10=N086:V790  58=N036:V281  127=N071:V653  166=N086:V797
167=N048:V381  169=N079:V727  176=N024:V187  233=N079:V724
271=N052:V411  330=N071:V656  365=N038:V297  413=N095:V865
512=N043:V342  526=N060:V503  550=N035:V276  617=N017:V126
621=N029:V243  632=N029:V244  644=N043:V343  669=N095:V859
673=N005:V043  818=N036:V280  897=N035:V277
Transitions
930D=(233,550) ~M04/917,M06/917  931D=(818,930) ~M04/919,M06/919  936D=(167,632) ~M04/920,M06/920
940D=(176,673) ~M04/922,M06/922  942D=(413,617) ~M04/921,M06/921  945D=(330,942) ~M04/924,M06/924
946D=(365,945) ~M04/926,M06/926  949D=(166,946) ~M04/927,M06/927  952D=(10,669) ~M04/932,M06/932
953D=(936,940) ~M04/934,M06/934  958D=(931,952)  961D=(512,897)
965D=(621,949) ~M04/944,M06/944  966D=(953,958)  972D=(58,961)
982D=(169,972)  983D=(127,966)  1012D=(965,982)
1016D=(644,983)  1045D=(526,1016)  1060D=(1012,1045)
1086D=(271,1060)
```

### M07/1730

22 canonical / 24 original IDs / 18 notes; 21 internal transitions. Exact raw children: (1609, 1689). Root displayed; immediate raw parent: 1772 (outside this reading subtree).

999 links N013/V093's butchered carcasses with N048/V373,V375's moral objection to bodies as animal graves. 1106, 1164, 1194, and 1318 extend through gamey meat, carnivore material, raw dog food, and N055/V453's pig slaughter: an interpretable, displayed six-note animal-food group despite opposed attitudes. 1116–1542 form another animal-food/meat-meal branch; 1411/1489 connect vegan food and non-carnivore alternatives without treating these as identical beliefs. 1005/1285 relate hens, beets, and chicks as household food production, while 1545 adds squirrels attacking tomatoes. The 18-note parent is broader animal/diet/food-production material, not uniform endorsement of meat.

```text
Leaves
32=N080:V732  89=N055:V453  101=N022:V150  218=N013:V093
243=N026:V212  302=N075:V690,V691  333=N100:V940  383=N053:V414
397=N041:V332  435=N055:V457  436=N054:V440  535=N048:V373,V375
571=N063:V526  590=N087:V798  642=N083:V779  717=N092:V836
749=N066:V576  762=N033:V264  778=N026:V213  806=N048:V382
854=N028:V231  856=N100:V927
Transitions
920D=(436,806) ~M04/930,M06/930  999D=(218,535) ~M04/1071,M06/1073  1005D=(32,101)
1032D=(243,920) ~M04/1229,M06/1226  1075D=(856,1032)  1106D=(397,762) ~M04/1039,M06/1042
1116D=(302,333) ~M04/1072,M06/1075  1164D=(999,1106)  1194D=(778,1164)
1285D=(717,1005)  1318D=(89,1194)  1411D=(590,642)
1439D=(571,1116)  1450D=(435,1075)  1489D=(854,1411)
1542D=(749,1439)  1545D=(383,1318)  1609D=(1285,1450)
1618D=(1542,1545)  1689D=(1489,1618)  1730D=(1609,1689)
```

### M07/1669

22 canonical / 23 original IDs / 20 notes; 21 internal transitions. Exact raw children: (1575, 1578). Root displayed; immediate raw parent: 1720 (outside this reading subtree).

997–1251 build dietary variety, real food, planning, and food quantities; infant interest and fasting broaden intake at 1345/1467. 1175/1185/1307 contain real cooking and dumpling relations, and shared meals/social food settings support 1252/1413/1517. There are weaker transitions: 1254 joins N024/V180's plastic/never-expiring-food red flag with N100/V934's use of food savers; the latter is equipment context, not a health claim. The root is a broad food-choice, preparation, and eating family, with differing opinions intact.

```text
Leaves
69=N069:V598  97=N084:V783,V784  109=N039:V303  115=N021:V141
118=N008:V057  136=N070:V640  155=N032:V261  237=N009:V064
311=N024:V180  350=N054:V428  434=N064:V551  479=N061:V509
536=N077:V711  584=N021:V143  598=N074:V685  645=N076:V709
682=N055:V447  698=N041:V330  720=N031:V253  803=N100:V934
833=N061:V510  908=N010:V069
Transitions
997D=(69,136) ~M04/967,M06/967  1058D=(598,997)  1103D=(155,720)
1175D=(536,645) ~M04/1000,M06/1000  1185D=(109,118) ~M04/996,M06/996  1212D=(237,1058)
1251D=(584,1212)  1252D=(350,682)  1254D=(311,803)
1271D=(1175,1185)  1307D=(434,1271)  1344D=(115,1252)
1345D=(479,1251)  1363D=(1103,1254)  1413D=(97,908)
1467D=(698,1345)  1487D=(833,1413)  1517D=(1344,1487)
1575D=(1307,1517)  1578D=(1363,1467)  1669D=(1575,1578)
```

### M07/1786

19 canonical / 19 original IDs / 17 notes; 18 internal transitions. Exact raw children: (1714, 1731). Root displayed; immediate raw parent: 1794 (outside this reading subtree).

1300 is a substantive two-note food-emotion relation: N059/V500's speculative emotion-based resistance and N064/V552's sentimental dumplings. 1006–1374 support food dislikes, carnivore controversy, and cooking preferences; 1189/1478 support taste/enjoyment. 1129's anti-killing passage and generous pig-slaughter account are legitimately opposed animal-food perspectives, but 1510 adds N080/V746's murder-mystery audiobook through a much weaker killing/death association. 1093/1388 and 1325/1543 mix adaptation, advice, purpose, disputes, and interests without establishing one psychological mechanism. The broad parent preserves the stronger food-attitude children.

```text
Leaves
53=N048:V372  67=N001:V010  90=N033:V265  93=N069:V613
107=N003:V027  180=N086:V794  195=N074:V679  245=N002:V019
263=N055:V462  400=N041:V317  543=N065:V559  562=N059:V500
603=N077:V714  661=N070:V639  702=N059:V501  745=N080:V746
785=N064:V552  808=N069:V629  849=N094:V851
Transitions
1006D=(90,195)  1093D=(93,661)  1124D=(107,543)
1129D=(53,263)  1189D=(180,849)  1222D=(400,1006)
1300D=(562,785) ~M04/1155,M06/1154  1325D=(808,1124)  1374D=(603,1222)
1388D=(702,1093)  1476D=(1300,1374)  1478D=(245,1189)
1510D=(745,1129)  1543D=(67,1325)  1648D=(1476,1510)
1714D=(1543,1648)  1731D=(1388,1478)  1786D=(1714,1731)
```

### M07/1630

19 canonical / 19 original IDs / 12 notes; 18 internal transitions. Exact raw children: (1360, 1473). Root displayed; immediate raw parent: 1751 (outside this reading subtree).

916–925, 929/947/950, and 1072/1240 provide real Bitcoin/community/workshop connections, including the proposed Bitcoin-accepting pizza restaurant. Raw 970 and 1026 add masks from notes already represented; their displayed ancestor is 1072, and their complete membership is not discarded. 1232's Lunchly-market argument and complaint about the Bitcoin-carnivore narrative share a broad cultural/consumer controversy, not one food position. The root's other child, 1360, links N080/V750's Brussels gifts with N056/V470's London design-brand context: a weak place/lifestyle bridge, not Bitcoin evidence. The useful 1473 branch remains independently displayed.

```text
Leaves
57=N080:V750  197=N024:V186  234=N054:V432  248=N095:V866
289=N074:V683  316=N054:V422  380=N055:V451  381=N012:V090
384=N003:V024  442=N048:V392  609=N055:V464  613=N048:V393
685=N056:V470  741=N050:V405  753=N024:V185  789=N048:V379
794=N055:V450  804=N074:V684  888=N029:V242
Transitions
916D=(753,789) ~M04/918,M06/918  917D=(234,916) ~M04/923,M06/923  918D=(381,888) ~M04/916,M06/916
919D=(917,918) ~M04/925,M06/925  925D=(380,919) ~M04/957,M06/957  929D=(197,442)
947D=(248,613)  950D=(316,794)  970R=(289,925)
980D=(929,950)  1026R=(609,970)  1072D=(980,1026)
1232D=(384,804) ~M04/1562  1240D=(741,1072)  1360D=(57,685)
1399D=(947,1232)  1473D=(1240,1399)  1630D=(1360,1473)
```

### M07/1747

18 canonical / 19 original IDs / 15 notes; 17 internal transitions. Exact raw children: (1603, 1700). Root displayed; immediate raw parent: 1761 (outside this reading subtree).

1065 pairs the complete risotto and spaghetti ingredient masks; 1108 joins cranberry/rosemary bread variants, and 1183 joins shrimp meals. Recipe quantities, meat portions, vegetables, and seasonings make several broader joins intelligible without requiring identical recipes. 1225's linoleic-acid and nutrient advice is a nutrient family, not validation of either claim. 1245 connects a century-egg preparation mixture to bagel salt/sesame toppings only broadly as food ingredients; it does not show the same preservation process. 1266/1401's tomato joke, recipe, and preparation/cleanup share tomatoes but different purposes. Upper ingredient/meal joins are correspondingly broad.

```text
Leaves
22=N030:V247,V248  31=N091:V822  174=N063:V523  175=N066:V573
240=N072:V665  252=N096:V872  297=N096:V892  339=N037:V288
449=N007:V050  458=N088:V801  618=N076:V704  662=N069:V599
668=N063:V525  731=N096:V877  834=N020:V139  855=N100:V922
870=N026:V208  880=N046:V360
Transitions
1065D=(252,668)  1108D=(240,339)  1147D=(175,855)
1183D=(174,834) ~M04/1119,M06/1118  1225D=(458,662) ~M04/1337,M06/1336  1245D=(31,880)
1261D=(1065,1147)  1266D=(22,297)  1338D=(449,731)
1380D=(618,1183)  1401D=(870,1266)  1504D=(1108,1338)
1518D=(1225,1245)  1541D=(1261,1518)  1603D=(1380,1401)
1700D=(1504,1541)  1747D=(1603,1700)
```

### M07/1767

18 canonical / 18 original IDs / 17 notes; 17 internal transitions. Exact raw children: (1685, 1710). Root displayed; immediate raw parent: 1807 (outside this reading subtree).

1037 relates periodic chicken-stock preparation to weeks-long century-egg preservation. 1341 adds the ancestral-meat claim; 1350 joins actual future boiled-egg lunch material to two compound food-choice/concern masks. Their parent 1564 is a displayed six-note alternative containing relevant N013/V095, N080/V737, and N091/V823; it is not a pure preservation group. 1062/1201/1652 link quantities and concern about chocolate, tea, seed oils, and kimchi, without endorsing health assertions. 1120/1205/1178/1538 support meat by-products, portions, and ingredients. Food disputes at 1237/1419 broaden the root further but do not erase the narrower temporal relation.

```text
Leaves
11=N074:V681  81=N016:V115  163=N098:V913  205=N100:V926
216=N080:V737  372=N088:V804  464=N066:V574  491=N096:V888
529=N065:V558  531=N016:V119  534=N091:V823  538=N073:V674
564=N075:V695  568=N024:V173  602=N013:V095  679=N003:V025
684=N026:V205  688=N090:V817
Transitions
1037D=(534,602) ~M04/1029,M06/1031  1062D=(81,538)  1120D=(205,684)
1178D=(491,564) ~M04/1099,M06/1099  1201D=(372,1062)  1205D=(464,1120)
1237D=(529,679)  1283D=(531,568) ~M04/1163,M06/1163  1341D=(688,1037) ~M04/1411,M06/1414
1350D=(216,1283) ~M04/1360,M06/1358  1419D=(11,1237)  1538D=(1178,1205)
1564D=(1341,1350)  1652D=(163,1201)  1685D=(1419,1564)
1710D=(1538,1652)  1767D=(1685,1710)
```

### M07/1822

16 canonical / 16 original IDs / 16 notes; 15 internal transitions. Exact raw children: (1707, 1783). Root displayed; immediate raw parent: 1826 (outside this reading subtree).

951/986/1339/1479/1550 form a meaningful family/child-feeding branch from infant and family material, vegetables, pancakes, and buying lunch. 1078/1445 relate beets, hen eggs, and chick welfare as household production/care. 1335's pressure-canning-today and chicken-water/seeds-tomorrow masks support broad scheduled food/feed preparation, not identical canning. 1070/1462 connect garlic and meal vegetables; 1641 has real venue-choice context but includes the coffee-shop password-retaliation fantasy. 1707/1783/1822 broaden to household feeding and food choices. N065's original says the person actually left and removed the shop from their rotation, not that they carried out the imagined hack.

```text
Leaves
87=N050:V401  91=N063:V531  119=N013:V096  134=N080:V735
140=N061:V513  173=N028:V233  307=N065:V569  406=N074:V680
423=N003:V030  473=N024:V188  487=N092:V838  507=N069:V605
558=N097:V896  658=N100:V929  706=N096:V876  787=N022:V151
Transitions
951D=(140,507) ~M04/1105,M06/1104  986D=(473,951) ~M04/1378,M06/1378  1070D=(91,706)
1078D=(134,787)  1335D=(119,658) ~M04/1435,M06/1432  1339D=(406,986)
1445D=(487,1078)  1462D=(558,1070)  1479D=(173,1339)
1550D=(423,1479)  1641D=(87,307)  1692D=(1335,1445)
1707D=(1462,1641)  1783D=(1550,1692)  1822D=(1707,1783)
```

### M07/1744

16 canonical / 16 original IDs / 13 notes; 15 internal transitions. Exact raw children: (1662, 1702). Root displayed; immediate raw parent: 1773 (outside this reading subtree).

1013 directly relates opposing caffeine/sleep/energy experiences, while 979/1035 support slower pace and sedentary-time concerns. 1134 is weaker: waiting in Santa context versus delaying an infant's food is shared waiting, not the same practice; 1385 broadens to restraint. 1330/1396/1475 make a plausible food-effort/time branch from reluctant egg preparation, feeding, lunch packing, and kitchen work that displaced photographs. N064/V550's placement here does not disprove the useful photography alternative at 1080 using V549. 1602's imagined router retaliation is only weakly connected to the wellbeing branch. The root remains heterogeneous care, effort, waiting, and reaction material.

```text
Leaves
18=N054:V423  71=N064:V550  204=N003:V031  254=N069:V600
282=N069:V588  283=N016:V111  328=N065:V561  347=N061:V511
500=N041:V324  518=N021:V145  530=N061:V512  647=N023:V170
719=N074:V682  792=N043:V350  827=N069:V618  899=N034:V272
Transitions
979D=(254,792)  1013D=(500,899) ~M04/1034,M06/1035  1035D=(647,979)
1102D=(204,282) ~M04/1491,M06/1482  1134D=(18,347) ~M04/1368,M06/1364  1250D=(1013,1035)
1330D=(283,530)  1385D=(827,1134)  1396D=(518,1330)
1466D=(719,1102)  1475D=(71,1396)  1602D=(328,1250)
1662D=(1466,1475)  1702D=(1385,1602)  1744D=(1662,1702)
```

### M07/1764

15 canonical / 15 original IDs / 13 notes; 14 internal transitions. Exact raw children: (1675, 1719). Root displayed; immediate raw parent: 1788 (outside this reading subtree).

1170 and 1221/1364 support sourdough and bread-ingredient/practice relations. 1386 adds spaghetti stirring/simmering as broader food preparation, not baking; 1398/1494 mix breakfast and baked foods. 1403/1521/1655 connect cooking equipment, brisket smoking, bread pans, and pancakes at a broad preparation level. 1560 is a conspicuously weak join: N052/V412's “Rise and grind” belongs to coffee in the complete original, while N072/V662 concerns success with high-altitude bread. The source does not turn the coffee phrase into a bread-rising instruction. Stronger bread children remain visible below that placement.

```text
Leaves
34=N056:V468  116=N047:V365  179=N071:V650  445=N052:V412
452=N085:V789  454=N067:V581  622=N046:V359  634=N096:V893
641=N037:V290  652=N015:V108  687=N072:V658  694=N072:V662
695=N028:V236  760=N037:V286  837=N089:V806
Transitions
1170D=(641,652)  1221D=(760,837) ~M04/1063,M06/1066  1364D=(687,1221)
1386D=(634,1170)  1398D=(179,454) ~M04/1193,M06/1195  1403D=(34,452)
1494D=(622,1398)  1521D=(116,1403)  1560D=(445,694)
1589D=(1364,1494)  1655D=(695,1521)  1675D=(1386,1560)
1719D=(1589,1655)  1764D=(1675,1719)
```

### M07/1529

15 canonical / 15 original IDs / 11 notes; 14 internal transitions. Exact raw children: (1257, 1400). Root displayed; immediate raw parent: 1620 (outside this reading subtree).

933/944/948/1001/1049/1317 support greetings, morning/afternoon time, and awakening; 1121 is a concrete late-breakfast/hot-morning-coffee pair. 959's “Beyond 9am” and consistent bedtimes are only a broad time/routine link, made more relevant to waking by 1081. 995/1234 connect first tasks, reading before bed, and morning tea/wee as daily activities, not a shared drink or exact schedule. The root is a broad day-routine family; the tea mask's placement alone establishes no tea-discovery loss.

```text
Leaves
66=N092:V824  70=N069:V593  147=N043:V337  156=N041:V319
241=N095:V861  244=N017:V120  260=N058:V495  369=N069:V625
524=N058:V494  592=N071:V647  639=N018:V127  716=N052:V409
754=N043:V335  828=N017:V124  898=N080:V730
Transitions
933D=(66,244)  944D=(241,933)  948D=(592,944)
959D=(70,754)  995D=(147,369)  1001D=(639,948)
1049D=(260,1001)  1081D=(156,959)  1121D=(524,828) ~M04/1106,M06/1105
1234D=(898,995)  1257D=(1081,1121)  1317D=(716,1049)
1400D=(1234,1317)  1529D=(1257,1400)
```

### M07/1661

14 canonical / 14 original IDs / 13 notes; 13 internal transitions. Exact raw children: (1511, 1614). Root displayed; immediate raw parent: 1713 (outside this reading subtree).

1107/1244/1382 connect dietary advice and judgments about processing or food quality. 1114/1331/1506 connect simple/clean meals, an easy recipe, and opinions about cooking. 1154's explicit food-preservation tag and never-expiring-food red flag support a broad preservation/expiry relation despite different attitudes; later joins introduce survival and lunch-packing effort. 1229 is weaker: a supermarket-pesticide complaint joins N078/V723's “foodchain” tag. The tag does not establish a retail-chain meaning merely because another note mentions a supermarket. The root's broad food-quality/preparation family is defensible, with this limited leaf evidence kept distinct.

```text
Leaves
30=N023:V168  76=N031:V252  84=N070:V644  227=N078:V723
246=N021:V146  291=N070:V642  407=N077:V715  465=N010:V072
466=N100:V942  537=N024:V178  737=N032:V263  763=N096:V869
795=N069:V596  800=N074:V688
Transitions
1107D=(795,800)  1114D=(30,465)  1154D=(466,537) ~M04/1239,M06/1240
1229D=(76,227)  1244D=(291,737)  1268D=(84,1154)
1331D=(763,1114)  1373D=(246,1268)  1382D=(1107,1244)
1506D=(407,1331)  1511D=(1229,1382)  1614D=(1373,1506)
1661D=(1511,1614)
```

### M07/1778

13 canonical / 13 original IDs / 13 notes; 12 internal transitions. Exact raw children: (1686, 1722). Root displayed; immediate raw parent: 1791 (outside this reading subtree).

1299 compares real egg-containing meals, and 1320/1512 broaden to pancakes and a full English breakfast. 1484 has actual pie and soda-bread ingredient/method context, but no shared baking method: the pie is no-bake. 1567 adds reluctance to cook eggs and chocolate-related illness as a looser food-preference/experience link. 1197/1531 relate meal ingredients; 1540/1687 relate specific cuisine/recipe and breakfast material without asserting the same cuisine. All leaves have real food context, but the 13-note parent is broader than any single recipe or process.

```text
Leaves
249=N096:V886  250=N076:V703  273=N083:V776  337=N011:V082
345=N075:V689  393=N056:V469  492=N040:V313  504=N097:V900
548=N016:V116  627=N028:V235  759=N072:V666  805=N023:V166
839=N080:V740
Transitions
1197D=(249,345)  1299D=(805,839) ~M04/1172,M06/1169  1320D=(393,627) ~M04/1259,M06/1255
1484D=(273,759)  1512D=(1299,1320)  1531D=(504,1197)
1540D=(250,337)  1567D=(548,1484)  1686D=(1512,1567)
1687D=(492,1540)  1722D=(1531,1687)  1778D=(1686,1722)
```

### M07/1808

13 canonical / 14 original IDs / 13 notes; 12 internal transitions. Exact raw children: (1681, 1693). Root displayed; immediate raw parent: 1825 (outside this reading subtree).

1253 pairs the absent-local-pizza/restaurant goal with a coffee-shop device ban and subsequent avoidance; 1324 pairs an off-menu dish with barbecue-location closures. Their displayed parent 1523 provides a concrete four-note restaurant-access alternative: N010/V077, N050/V404, N057/V485, N065/V568. No exact-vector reunion is needed. 1290 is weaker: Sorrento's three food stops and three cheap rotisserie chickens share a number and obtaining food, not a three-stop chicken tour; 1628 adds interrupted outdoor plans. Other children connect recipe ingredients and meals. The broad 1808 parent does not remove 1523's usefulness.

```text
Leaves
35=N057:V485  38=N011:V080  86=N039:V298  121=N065:V568
123=N055:V463  210=N096:V874  225=N097:V904  446=N002:V018
506=N026:V202  528=N063:V522  743=N083:V773,V774  841=N010:V077
860=N050:V404
Transitions
1253D=(121,860) ~M04/1528,M06/1525  1290D=(446,506)  1296D=(210,528)
1324D=(35,841) ~M04/1372,M06/1369  1454D=(123,225)  1472D=(38,1296)
1523D=(1253,1324)  1551D=(743,1454)  1628D=(86,1290)
1681D=(1523,1628)  1693D=(1472,1551)  1808D=(1681,1693)
```

### M07/1729

13 canonical / 14 original IDs / 12 notes; 12 internal transitions. Exact raw children: (1577, 1612). Root displayed; immediate raw parent: 1774 (outside this reading subtree).

1029/1153/1270 and 1083/1149/1537 connect explicit localities, brands, travel/return, and named foods at a broad geographic/food-context level. 1297 pairs a mochi-bread request with gianguja/melanger material: different foods/preparation contexts, not the same recipe. 1372 pairs N054/V437's “Movies” with N069/V619's advice to leave some things unsaid; 1444 then adds N048/V395's “zapathon.” Those masks provide little concrete commonality. The root combines these weak fragments with more intelligible place/food material; a geographic reading cannot supply absent meaning to the unrelated masks.

```text
Leaves
1=N056:V471  48=N048:V395  74=N081:V764  191=N011:V087
268=N080:V749  320=N055:V452  327=N054:V437  503=N027:V220
505=N093:V848,V849  740=N069:V619  779=N050:V400  840=N078:V719
864=N054:V431
Transitions
1029D=(320,864)  1083D=(268,503)  1149D=(1,1083)
1153D=(840,1029)  1270D=(779,1153)  1297D=(74,191) ~M04/1651,M06/1646
1372D=(327,740)  1444D=(48,1372)  1537D=(505,1149)
1577D=(1444,1537)  1612D=(1270,1297)  1729D=(1577,1612)
```

### M07/1739

12 canonical / 12 original IDs / 12 notes; 11 internal transitions. Exact raw children: (1636, 1695). Root displayed; immediate raw parent: 1782 (outside this reading subtree).

1113/1323/1425 connect tomatoes, tomato preparation, and meals. 1204, 1301, and 1526 form a genuine bread/preparation branch including sourdough, soda bread, altitude difficulties, and salt/yeast practice. 1536 combines vegan raw pie with non-carnivore pancakes; 1563 connects egg meals and reluctance to cook eggs, and 1636 broadens food choices. 1695/1739 are broad meal/preparation joins rather than one recipe or shared claim about health. The more specific tomato and bread children remain legible.

```text
Leaves
9=N031:V259  94=N015:V109  105=N083:V781  112=N089:V808
146=N072:V664  159=N096:V880  161=N037:V292  194=N026:V197
228=N016:V112  253=N028:V232  416=N071:V652  823=N023:V167
Transitions
1113D=(159,194)  1204D=(94,161)  1301D=(112,146) ~M04/1137,M06/1137
1323D=(416,1113)  1425D=(9,1323)  1526D=(1204,1301)
1536D=(105,253)  1563D=(228,823)  1636D=(1536,1563)
1695D=(1425,1526)  1739D=(1636,1695)
```

### M07/1699

12 canonical / 12 original IDs / 11 notes; 11 internal transitions. Exact raw children: (1498, 1576). Root displayed; immediate raw parent: 1827 (outside this reading subtree).

989 is a direct sea-salt ingredient pair; 1079 relates steak purchases/portions. 1126/1198/1357 connect food/drink quantities and amounts prepared or consumed, while 1576 adds the whole kimchi tub. These are broad amount relations, not a uniform storage process. 1176 is especially weak: N002/V014's 1.09 km stroll and N100/V920's steak price have different measured dimensions. 1336's recipe water with salt-containing dishes is only an ingredient/preparation extension, not a shared brine. The root combines useful food-amount children with a numerical-looking outlier; numerical resemblance is not a semantic score.

```text
Leaves
40=N016:V113  202=N096:V884  226=N013:V098  298=N098:V911
310=N073:V672  448=N002:V014  494=N100:V919  511=N066:V578
750=N046:V362  793=N063:V538  901=N100:V920  902=N026:V198
Transitions
989D=(750,793) ~M04/998,M06/998  1079D=(494,511)  1109D=(902,1079)
1126D=(40,310)  1176D=(448,901)  1198D=(226,1126)
1336D=(202,989)  1357D=(1109,1198)  1498D=(1176,1336)
1576D=(298,1357)  1699D=(1498,1576)
```

### M07/1709

11 canonical / 11 original IDs / 10 notes; 10 internal transitions. Exact raw children: (1496, 1654). Root displayed; immediate raw parent: 1766 (outside this reading subtree).

1157 directly pairs briskets in smokers. 1286/1326 relate beef preparation and crockpots, 1258/1378 relate steak/beef meals and cutting steaks, and 1362/1554 introduce actual cookware. 1496's bread pans and ashes broaden equipment/heat preparation without claiming that all items are the same vessel or process. 1654/1709 remain interpretable beef/cooking/equipment joins across ten notes. This is a broad useful family, not a claim that the bread-pan mask itself mentions beef.

```text
Leaves
182=N056:V474  319=N014:V104  349=N075:V692  421=N019:V134
426=N100:V941  555=N082:V768  601=N085:V788  604=N092:V826
775=N096:V889  876=N047:V366  913=N056:V475
Transitions
1157D=(421,601)  1258D=(349,426)  1286D=(319,775)
1326D=(604,1286)  1362D=(182,1157)  1378D=(555,1258)
1496D=(876,1362)  1554D=(913,1326)  1654D=(1378,1554)
1709D=(1496,1654)
```

### M07/1673

10 canonical / 10 original IDs / 10 notes; 9 internal transitions. Exact raw children: (1483, 1565). Root displayed; immediate raw parent: 1761 (outside this reading subtree).

1139/1303 connect fruit choices and then the two cranberry/rosemary bread sources, yielding a real bread-ingredient alternative despite the extra cherry mask. 1255 links household food-preparation tasks, but N100/V930 includes myoglobin for the dog and cold water/seeds for chickens; it must not be paraphrased as giving myoglobin to chickens. 1376/1395/1483 contain genuine meal, vegetable, and preparation context. 1421/1565/1673 broaden through risotto and chicken/yogurt/wine to varied meals and food enjoyment. This is not one cuisine, but neither is differing cuisine itself a failure.

```text
Leaves
88=N076:V710  177=N037:V293  178=N026:V207  239=N007:V052
374=N010:V076  377=N080:V756  427=N096:V887  432=N063:V529
480=N072:V667  700=N100:V930
Transitions
1139D=(377,480)  1255D=(178,700)  1303D=(177,1139)
1376D=(239,427)  1395D=(374,1255)  1421D=(432,1303)
1483D=(1376,1395)  1565D=(88,1421)  1673D=(1483,1565)
```

### M07/1757

10 canonical / 11 original IDs / 10 notes; 9 internal transitions. Exact raw children: (1634, 1678). Root displayed; immediate raw parent: 1811 (outside this reading subtree).

1020/1076/1455 form a particularly clear displayed four-note Christmas group: N054/V426's absent Santa/lunch, N064/V545's post-Christmas slowdown, N080/V748's Christmas cards and audiobook, and N062/V518's Christmas-lunch headline. N080's cards are sufficient; its Brussels gifts need not be assumed to be Christmas gifts. 1308/1634 add a Sunday greeting and weekend coffee-shop rule as broader calendar/routine material. 1387 legitimately relates children's food preferences. 1171's N036/V282 “ice” plus N024/V181,V183's ice-cream-dislike red flag is much weaker lexical overlap; the source context does not make them the same preference. 1678/1757 preserve the useful Christmas child while broadening substantially.

```text
Leaves
42=N068:V582  106=N036:V282  396=N054:V426  431=N028:V234
455=N064:V545  469=N095:V864  544=N024:V181,V183  659=N062:V518
774=N065:V554  798=N080:V748
Transitions
1020D=(396,455)  1076D=(798,1020)  1171D=(106,544) ~M04/1346,M06/1346
1308D=(469,774)  1387D=(42,431) ~M04/1278,M06/1276  1455D=(659,1076)
1634D=(1308,1455)  1678D=(1171,1387)  1757D=(1634,1678)
```

### M07/1732

9 canonical / 10 original IDs / 9 notes; 8 internal transitions. Exact raw children: (1527, 1691). Root displayed; immediate raw parent: 1795 (outside this reading subtree).

1215/1377/1546 connect cooking enthusiasm, kitchen work, cooktop functions, and stove tinkering. 1027's “hope” and pursuing purpose are a broad mental-orientation link; 1507's request for next-dinner ideas adds plans without establishing a grand life purpose. 1527 joins disrupted storm/grilling plans with a successful meal and hope about chemotherapy at most as food plans amid difficulties. The upper joins therefore mix interests, hopes, and cooking at varying strength. N048/V384 supplies only “hope”; the complete moral quote cannot be silently substituted for that sparse mask.

```text
Leaves
133=N027:V227  199=N049:V396,V397  266=N048:V384  278=N039:V308
408=N064:V548  552=N001:V007  579=N069:V627  599=N008:V062
784=N023:V172
Transitions
1027D=(266,579)  1215D=(199,408) ~M04/1184,M06/1184  1377D=(133,552)
1507D=(784,1027)  1527D=(278,599) ~M04/1599,M06/1596  1546D=(1215,1377)
1691D=(1507,1546)  1732D=(1527,1691)
```

### M07/1717

9 canonical / 9 original IDs / 8 notes; 8 internal transitions. Exact raw children: (1284, 1670). Root displayed; immediate raw parent: 1809 (outside this reading subtree).

1018 and 1051 contain actual wine with meals or cooking; 1284's gin is a legitimate broader alcohol extension. 1101 joins cranberry/currant bread choices and 1465 extends to salt/yeast bread practice. 1310 is weaker: white-or-red onions join dry white wine and homemade wine, with color/food-flavour overlap rather than the same ingredient. 1670/1717 connect preparation/flavour and drinks broadly; the bread children do not become alcohol evidence simply by sharing a parent.

```text
Leaves
65=N007:V053  168=N075:V698  290=N076:V706  351=N072:V668
354=N089:V807  438=N080:V751  646=N037:V289  653=N063:V536
868=N076:V705
Transitions
1018D=(65,868) ~M04/1065,M06/1067  1051D=(290,653)  1101D=(351,646) ~M04/1012,M06/1014
1284D=(438,1018)  1310D=(168,1051)  1465D=(354,1101)
1670D=(1310,1465)  1717D=(1284,1670)
```

### M07/1580

9 canonical / 10 original IDs / 8 notes; 8 internal transitions. Exact raw children: (1329, 1449). Root displayed; immediate raw parent: 1751 (outside this reading subtree).

1025 connects brain activity on waking with mental/physical effects of remaining still; 1142/1449 broaden mental states to the food-vision/emotion speculation. 996/1220 connect philosophy, openness to different views, and education; 1329 adds abandoning an unsatisfying audiobook. 1019's mind being “off” and accepting incomplete knowledge is a weak general mind/knowledge relation, not a shared diagnosis. The root is broad cognition, outlook, and response material. Neither the clustering nor this audit validates N059's speculation about color vision and food resistance.

```text
Leaves
7=N014:V105,V106  78=N043:V349  200=N080:V745  231=N041:V320
270=N069:V634  593=N059:V502  738=N054:V438  843=N055:V466
904=N069:V636
Transitions
996D=(738,904) ~M04/1503,M06/1495  1019D=(7,270)  1025D=(78,231)
1142D=(1019,1025)  1220D=(843,996)  1329D=(200,1220)
1449D=(593,1142)  1580D=(1329,1449)
```

### M07/1674

8 canonical / 8 original IDs / 7 notes; 7 internal transitions. Exact raw children: (1448, 1557). Root displayed; immediate raw parent: 1762 (outside this reading subtree).

969's peace-related masks, 1088's better human conditions, and 1127's health wish form a broad wellbeing branch. 1059 links kindness and finding arguments about cooking wholesome; 1557 adds hoped-for treatment/meal outcomes. 1448 introduces sharing a meal as barrier-breaking social value. 1674 therefore has a plausible broad wellbeing/kindness/food-sociality reading while joining different kinds of wishes, conduct, and experience. It does not assert equivalent medical outcomes or identical moral positions.

```text
Leaves
323=N023:V169  388=N069:V610  402=N008:V061  424=N055:V449
509=N069:V633  572=N048:V371  733=N070:V641  863=N077:V713
Transitions
969D=(388,572) ~M04/1219,M06/1217  1059D=(509,863)  1088D=(733,969)
1127D=(323,1088)  1448D=(424,1127)  1557D=(402,1059)
1674D=(1448,1557)
```

### M07/1635

7 canonical / 7 original IDs / 7 notes; 6 internal transitions. Exact raw children: (1427, 1452). Root displayed; immediate raw parent: 1756 (outside this reading subtree).

1069 directly joins saved chicken carcasses/bone stock with stock made from rotisserie-chicken bones; 1242 adds steak trimmings, tallow, and dog scraps as another by-product-use practice. 1090 pairs pig slaughter with the opposed animal-graves quote, and 1452 combines animal killing/use across five notes. This is another relevant mask alternative to the animal-food branches, not evidence that all such masks must reunite. 1427/1635 broaden through chicks and raised-bed beets to household food production; those two masks do not themselves describe slaughter.

```text
Leaves
144=N100:V931  208=N055:V458  299=N092:V839  364=N048:V374
422=N026:V206  523=N013:V094  651=N022:V147
Transitions
1069D=(422,523) ~M04/1004,M06/1004  1090D=(208,364)  1242D=(144,1069)
1427D=(299,651)  1452D=(1090,1242)  1635D=(1427,1452)
```

### M07/1745

7 canonical / 7 original IDs / 7 notes; 6 internal transitions. Exact raw children: (1592, 1688). Root displayed; immediate raw parent: 1804 (outside this reading subtree).

1361/1592 relate named dishes and Sorrento cuisine; 1443 has real takeout-venue and restaurant-closure context. 1574/1688 relate local breakfast/combini food access and then venues more broadly, with no requirement that the dishes share one cuisine. The root is an intelligible seven-note prepared-food/cuisine/access family. The exact masks differ from restaurant-access 1523, so this supplies a broader legitimate alternative rather than invalidating or replacing the more focused child elsewhere.

```text
Leaves
170=N063:V521  171=N040:V312  190=N011:V086  276=N057:V484
556=N002:V013  848=N010:V071  885=N096:V883
Transitions
1361D=(170,885)  1443D=(276,848)  1574D=(171,190)
1592D=(556,1361)  1688D=(1443,1574)  1745D=(1592,1688)
```

### M07/1352

7 canonical / 7 original IDs / 7 notes; 6 internal transitions. Exact raw children: (1115, 1219). Root displayed; immediate raw parent: 1414 (outside this reading subtree).

1021/1047 directly concern wanting or having more coffee. 1115 pairs coffee-shop music and a coffee-shop rave, while 1128 pairs coffee in interesting places with iced coffee served in ice. 1219/1352 combine seven actual coffee-experience masks into a useful broad group. No non-coffee mask needs to be rescued by another passage in its source.

```text
Leaves
145=N079:V726  259=N095:V860  557=N035:V279  612=N086:V791
755=N004:V036  758=N036:V285  894=N038:V294
Transitions
1021D=(145,612)  1047D=(259,1021)  1115D=(755,894)
1128D=(557,758)  1219D=(1047,1128)  1352D=(1115,1219)
```

### M07/1579

7 canonical / 7 original IDs / 7 notes; 6 internal transitions. Exact raw children: (1436, 1492). Root displayed; immediate raw parent: 1704 (outside this reading subtree).

987 is a real seasonal-weather/frosty-morning pair; 1094 and 1492 broaden to high-altitude residence and gardening on a town lot. 1067, however, pairs N098/V909's being “in [a] corner” with N069/V626's advice not to speak badly about someone; the actual kimchi elsewhere in N098 is absent from this mask. 1436's stretching/bowing does not repair that limited relation. 1579 joins this weak body/location/conduct child to environmental/garden context. The stronger weather child remains, but the whole parent has little specific commonality.

```text
Leaves
135=N058:V493  324=N072:V659  409=N098:V909  527=N080:V728
591=N043:V344  629=N069:V626  677=N022:V156
Transitions
987D=(135,527) ~M04/1158,M06/1158  1067D=(409,629)  1094D=(324,987)
1436D=(591,1067)  1492D=(677,1094)  1579D=(1436,1492)
```

### M07/1716

6 canonical / 6 original IDs / 6 notes; 5 internal transitions. Exact raw children: (1468, 1613). Root displayed; immediate raw parent: 1823 (outside this reading subtree).

1241 and 1305 relate local/named food and recipe material at a broad cuisine level; the mochi and tandori masks are not one recipe. 1468 connects explicit Sorrento/Italian context with spaghetti Bolognaise, and 1613/1716 unite the six food/cuisine notes more broadly. These are legitimate broad food-discovery relations without requiring exact dish identity. The source's Japanese characters are preserved; no additional interpretation of untranslated text is needed.

```text
Leaves
321=N078:V722  630=N076:V700  697=N011:V081  769=N096:V868
783=N002:V021  788=N040:V311
Transitions
1241D=(321,788) ~M04/1361,M06/1359  1305D=(630,697) ~M04/1245,M06/1244  1468D=(769,783)
1613D=(1241,1305)  1716D=(1468,1613)
```

### M07/1264

5 canonical / 6 original IDs / 5 notes; 4 internal transitions. Exact raw children: (21, 1224). Root displayed; immediate raw parent: 1304 (outside this reading subtree).

1022/1151/1224 form a real four-note coffee-place/music/iced-coffee child. 1264 then adds N079/V725, whose entire selected mask is the dog emoji “🐶”. The complete N079 note does ask about coffee, but that does not turn this particular mask into coffee evidence. This is a weak leaf placement; importantly, N079 has legitimate coffee alternatives (V724,V727 at 1086 and V726 at 1352) in this same audited forest. It is therefore not a demonstrated loss of access to N079 through coffee.

```text
Leaves
14=N035:V278  21=N079:V725  99=N036:V283,V284  142=N004:V035
796=N038:V295
Transitions
1022D=(142,796) ~M04/1026,M06/1028  1151D=(14,99)  1224D=(1022,1151)
1264D=(21,1224)
```

### M07/1663

5 canonical / 5 original IDs / 5 notes; 4 internal transitions. Exact raw children: (1196, 1500). Root displayed; immediate raw parent: 1742 (outside this reading subtree).

1044 legitimately relates cooking durations for bread pans and spaghetti simmering. 1500 adds N058/V488's 35-degree morning as only broad temperature context, not cooking temperature. 1196 joins a five-month-old infant with N088/V800's claimed four-year linoleic-acid half-life; sharing duration units does not establish a food/biological process in common. 1663 combines these children into a weak time/temperature family. The original medical claim is reported as a claim, not validated.

```text
Leaves
463=N061:V507  520=N058:V488  649=N088:V800  714=N096:V894
809=N047:V368
Transitions
1044D=(714,809) ~M04/1041,M06/1044  1196D=(463,649)  1500D=(520,1044)
1663D=(1196,1500)
```

### M07/1643

4 canonical / 5 original IDs / 4 notes; 3 internal transitions. Exact raw children: (1190, 1528). Root displayed; immediate raw parent: 1746 (outside this reading subtree).

1190 joins “Cheese Doodle” with cheesecake; both are foods, but the shared cheese word does not make the snack and dessert the same dish. 1528's craft-chocolate/gianguja and matcha-cashew pie are a defensible broader confection/dessert relation. 1643 combines snack and sweet-food material across four notes, with much stronger food evidence than a bare numerical or unrelated-word join. The pie's gluten-free mask does not transfer that property to the other foods.

```text
Leaves
212=N012:V088  223=N067:V579,V580  285=N081:V765  816=N083:V778
Transitions
1190D=(212,223) ~M04/1075,M06/1078  1528D=(285,816)  1643D=(1190,1528)
```

### M07/1520

4 canonical / 4 original IDs / 4 notes; 3 internal transitions. Exact raw children: (607, 1272). Root displayed; immediate raw parent: 1776 (outside this reading subtree).

993 relates parsley in shrimp risotto to Parmesan on an omelette as meal ingredient/topping context, not the same topping. 1272 adds N055/V467's people/rural Paraguay/heart mask, which omits that original's shared meal; that placement has weak direct food evidence. 1520 adds actual paratha/dal meal material and is broader food/social-locality context. Other N055 masks explicitly contain sharing food in roots 1669/1674/1808, so this sparse placement alone cannot establish lost meal discovery.

```text
Leaves
104=N097:V901  607=N078:V718  747=N063:V532  852=N055:V467
Transitions
993D=(104,747) ~M04/1003,M06/1003  1272D=(852,993)  1520D=(607,1272)
```

### M07/1639

4 canonical / 4 original IDs / 4 notes; 3 internal transitions. Exact raw children: (1095, 1556). Root displayed; immediate raw parent: 1803 (outside this reading subtree).

1095 pairs two actual named kitchen devices: an induction cooktop and a recommended vacuum sealer. 1556 pairs a rocket stove used to cook green beans with cast-iron cookware and its handles. 1639 is a coherent broad cooking/storage equipment group with different functions, not one cooking method. This is a genuinely broader connection; it need not be rejected for crossing stove, vessel, and preservation equipment.

```text
Leaves
352=N001:V004  395=N027:V221  453=N056:V481  826=N100:V938
Transitions
1095D=(395,826)  1556D=(352,453)  1639D=(1095,1556)
```

### M07/1228

3 canonical / 3 original IDs / 3 notes; 2 internal transitions. Exact raw children: (382, 975). Root displayed; immediate raw parent: 1683 (outside this reading subtree).

975 relates a 9am/postponed-task mask to an after-8pm phone limit only as time/routine management. 1228 adds the coffee-shop weekend device ban and imagined router retaliation, making digital restrictions/disconnection a clearer link to N069/V589, but not to every word of N043/V341. The root is a qualified routine/device-restriction group. N065's imagined password change is not represented as an action actually carried out.

```text
Leaves
382=N065:V564  412=N069:V589  498=N043:V341
Transitions
975D=(412,498) ~M04/1321,M06/1318  1228D=(382,975)
```

### M07/1277

2 canonical / 3 original IDs / 2 notes; 1 internal transitions. Exact raw children: (111, 895). Root displayed; immediate raw parent: 1393 (outside this reading subtree).

N045/V355,V356 complain that half-and-half is ruining coffee; N094/V856 contrasts decaf purism with caffeine addiction. Both concern what determines an acceptable coffee experience, despite differing targets and tone. This displayed two-note group is a reasonable coffee-preference connection, not evidence that the authors share the same position.

```text
Leaves
111=N045:V355,V356  895=N094:V856
Transitions
1277D=(111,895)
```

## Boundaries and unresolved questions

This is complete transition coverage of the assigned forest, with no unread mask, unchecked fragment, or unread original inside that scope. It does **not** cover other reading roots or the connecting ancestors, and does not claim a complete semantic audit of M07. Exact recursive match counts describe structure, not how many relations are good.

Several weak placements are directly witnessed: Rome-as-travel at 1206, coffee “Rise and grind” beside high-altitude bread at 1560, a stroll length beside steak price at 1176, the dog-only mask at 1264, and age/half-life durations at 1196. Those are distinct from established losses of note discovery. For example, N079's actual coffee masks remain in 1086 and 1352, and N064's actual photo mask remains in 1080. Where no generous alternate-mask search across the entire M07 tree was performed, no loss is asserted.

The input itself sets limits: tag-only or one-word masks, discontiguous spans, compound masks covering several activities, source truncation, and source claims or jokes that must remain claims or jokes. Untranslated source text was preserved without inferring extra meaning. Statements about dietary risk, physiology, morality, or actions imagined but not performed were not endorsed or converted into facts by their placement. The audit cannot determine the embedding's causal rationale from a merge alone.

Within this bounded reading, M07 supports several useful narrow groups and broad families while also producing weak joins. This report supplies exact source and transition evidence; it does not establish that M07 is globally better, select a new rule, require every same-subject note to reunite, or substitute an analyst's interpretation for the user's judgment.
