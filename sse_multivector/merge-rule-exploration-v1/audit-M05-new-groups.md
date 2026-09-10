# M05: bounded audit of changed small-to-mid groups

These are provisional semantic judgments, not approved memberships or generated hierarchy titles. No labels, inputs, vectors, exclusions, or display rules were changed.

## Result and scope

The strongest new example in this inspection is M05/1467: an off-menu dish, unavailable local pizza, and restaurant closures. Relevant alternative masks still require 98–99-note displayed groups in M04/M01/HDBv3. A fixed-state calculation also identifies a real median-versus-mean/minima choice reversal behind its third-note extension.

M05/1285 provides a smaller, more acquisition-focused steak group. Conversely, M05/1686 introduces a weak bread-failure/ice-cream-serving pair. The latter is a local placement regression, not loss of the useful bread-note relationship: other masks preserve that relationship.

Most other apparent improvements disappear as *new note discovery* after checking alternative masks. Children's food, family, tomatoes, sleep, plant-focused food choices, and commercial-food examples already have compact counterparts. Neither exact-set novelty nor the size of an exact-vector common ancestor measures their semantic improvement.

This audit focuses on 16 changed raw groups: 1138, 1285, 1313, 1421, 1431, 1467, 1518, 1616, 1643, 1684, 1688, 1693, 1722, 1732, 1750, 1770. Their disjoint subtrees contain 111 canonical vectors, 114 original IDs, 318 fragments, 95 internal merges, and 37 notes. Every focal fragment array and every focal merge's children were read bottom-up; all 318 fragments matched their original UTF-8 byte ranges. Those 37 original notes were read in full. Additional comparator masks, same-note projection extensions, and specifically named ancestors were inspected as needed. This is not full-tree coverage, a representative sample, or a semantic pass rate. Structural screening used shortened fragments only to locate candidates; those screening results are not counted as semantic coverage.

Sources are the frozen M01/M04/M05 artifacts, `../real-note-fine-segmentation-v1/vectors/vector-map.json`, `reviewed-input.json`, and `hdbv3-cross-note-edges-v1/response.json`. Generated subject fields in the map were not used as evidence. Membership comparisons expand aliases to original IDs. Displayed-group checks apply the existing rule: retain the root, and otherwise retain a cross-note merge only when its note set differs from its immediate raw parent's. A group's number below is its raw merge ID, not a generated identifier.

## 1. M05/1467: a useful new third-note extension

The complete group contains six exact masks:

- V075/N010: ⟦Chinese take out⟧ ⟦lady behind the register⟧ ⟦eating⟧ ⟦beautiful dish⟧ ⟦isn't on the menu⟧.
- V077/N010: ⟦Chinese take out place⟧ ⟦behind the register⟧ ⟦eating⟧ ⟦beautiful dish⟧ ⟦isn't on the menu⟧.
- V071/N010: ⟦Chinese take out place⟧ ⟦lady behind the register⟧ ⟦eating⟧ ⟦dish⟧ ⟦looks simple⟧.
- V399/N050: ⟦we currently have no ways to get pizza⟧ ⟦St Michel de L'Attalaye⟧ ⟦haiti⟧.
- V484/N057: ⟦Largest Barbecue Chain⟧ ⟦U.S.⟧ ⟦Shuttering Locations⟧.
- V485/N057: ⟦Largest Barbecue Chain in U.S. Quietly Shuttering Locations⟧.

The originals describe different restrictions: a dish not offered on a menu, absence of a local pizza option, and restaurant closures. These are a defensible broad connection about access to restaurant food, not the same cause, cuisine, or place. V071 alone does not express unavailability; its own pair is correspondingly weaker. The original N010 confirms the missing-menu context, but that context must not be silently inserted into V071's mask.

Bottom-up, 1378 pairs V077 with V485. This pair is not new: M04/1372 and M01/1410 already have it. M05/1403 adds V075; 1437 adds V399, creating the useful three-note combination. Separately, 1464 pairs V071 with V484. The final 1467 joins these two children. The weaker second child does not erase the clearer four-mask, three-note child1437. The unchanged display collapses 1437 into1467 because both have the same note set.

The alternate-mask search admitted N010 V065/V075/V077, N050 V399/V401–V405, and N057 V484/V485. It therefore includes the longer off-menu account and the other pizza-goal representations; it does not demand these exact six vectors.

| Run | Smallest displayed group found | Distinct notes | Canonical vectors |
| --- | ---: | ---: | ---: |
| HDBv3 | 1640 | 99 | 715 |
| M01 | 1737 | 99 | 703 |
| M04 | 1801 | 98 | 601 |
| M05 | 1467 | 3 | 6 |

These are bounded, relation-specific searches, not a declaration that every possible interpretation of these notes was tested. They do establish that this result is more than reunion of duplicate masks from notes already available together through the selected relationship.

### A concrete median choice, with its limitation

Immediately before M05/1437, group1403 is exactly V075/V077/V485. V399 is still a singleton, as are V484 and V071. Its three eligible distances into1403 are:

| Pair | Angular distance |
| --- | ---: |
| V399–V075 | 1.064952239 |
| V399–V077 | 1.065452461 |
| V399–V485 | 1.284297580 |

At this *same saved partition*, the candidate scores are:

| Candidate to join1403 | All-pairs mean | All-pairs median | Symmetric nearest-partner means |
| --- | ---: | ---: | ---: |
| V399, adding N050 | 1.138234093 | **1.065452461** | 1.101593166 |
| V484, another N057 mask | **1.074607679** | 1.074607679 | **1.070367309** |
| V071, another N010 mask | 1.083845801 | 1.083845801 | 1.083845801 |

Lower scores win. The mean's best partner for1403 at this state is V484; the median's is V399. Symmetric nearest-partner means also prefer V484 to V399, although that rule has a still cheaper larger-group candidate. This is a local reversal between available choices, not a claim that a complete M01/M04 replay would share this earlier history. In fact, M04 sends V075 into an existing dining-out group at1401, so its off-menu/closure branch never obtains these exact three masks together at this stage.

The median has reduced the effect of the relatively distant pizza/closure pair. But its majority consists of **two masks from N010**, not two independent notes. This successful example therefore does not establish note-level consensus or show that the discarded magnitude was noise. The frozen mask multiplicities and omitted same-note edges still matter.

## 2. M05/1285: a smaller acquisition-focused option, not an invalidated parent

1171 pairs V578/N066, ⟦haul cost⟧ ⟦Argentina⟧ ⟦1.1kg⟧ ⟦Tbone⟧, with V919/N100, ⟦Picked up⟧ ⟦sirloin strip sub primal⟧ ⟦$10 a lb⟧ ⟦cut 15 steaks about 1.5-2" thickness⟧. 1223 adds V920's purchase/price mask. 1285 adds V924, ⟦Trimmed about 3lb of fat for making tallow⟧ ⟦beef⟧. The originals confirm a steak haul and a bulk steak purchase followed by processing; no matching price or country is inferred.

Allowing every N066 cost/haul mask V572–V578 and N100's explicit purchase masks V919/V920 yields HDBv3/1297 at62 notes, M01/1222 at3, M04/1287 at3, and M05/1285 at2. M01/1222 and M04/1287 include N096 V872's quantified Bolognaise ingredient list. That is not unrelated to meat quantities. M05 offers a narrower two-note acquisition/processing option; the broader recipe-containing alternatives are not thereby failures. V924 also broadens M05 beyond purchasing alone.

## 3. M05/1688: new ice-cream access accompanied by a local regression

1356 joins V282/N036 ⟦ice⟧ to the aliased V181/V183/N024 ⟦Red flags⟧ ⟦people who don’t like ice cream⟧. N036's original is iced coffee served in ice, not ice cream. The mask is genuinely underspecified.

1686 makes the new pair:

- V586/N068: ⟦a plate rather than a bowl⟧ ⟦My husband asked⟧ ⟦is that to make easier to lick the ice cream?⟧.
- V660/N072: ⟦soda bread I usually made doesn't work at the high altitude I live at now⟧.

The originals concern serving/eating ice cream and failure of a bread recipe after an altitude change. General food practices is possible, but neither a shared preparation constraint nor a shared serving issue is established. At this local level this is weaker than V660's M04 attachment1306, which adds it to V664 plus N089's salt/yeast-separation bread masks. M05/1688 then joins the two pairs. Its exact scope is four canonical vectors, five original IDs, and four notes—not an ice-cream-only group.

There is a simultaneous positive change: allowing N024 V181–V183 and N068 V582–V587 finds the two notes together at displayed M05/1688 (4 notes), versus M04/1734 (65), M01/1708 (96), and HDBv3/1517 (95). The two notes do share ice cream, even though one jokes about dislike and the other discusses how to eat it. The added bread-failure mask and bare ice mask weaken this particular destination; the smaller note set alone is not a clean win.

Two checks prevent overstating the regression:

1. N072/N089 still have the four-mask bread-constraint group M05/1153, using V664 and V807–V809. The relevant relationship is not lost just because V660 moved. M01/1166 supplies that same four-mask alternative; M04/1340 includes V660/V662 as well.
2. N068 still has a serving/utensil route with N044's V353 ⟦king's butler⟧ ⟦say⟧ ⟦should eat burgers with⟧ ⟦knife and fork⟧ through V583 at M05/1733. That group also includes cookware material, as the M01/M04 alternatives do. Moving V586 does not eliminate N068's access through this relationship.

This weak pair is not evidence that the median directly preferred ice cream over a still-small bread group. At M04's saved state before1306, V660's mean and median to the available bread group are0.982277131 and0.988094727: both favor it. By M05/1686 the bread masks are already in a97-canonical-vector group. V660/V586 are singletons with the same1.244466598 score under all three aggregations. Earlier merge history changed the choices still available; the final singleton score itself does not explain that history.

## 4. Apparent discoveries that already have compact counterparts

The following descriptions come from all masks in each focal subtree and the named comparator groups. Counts refer to displayed groups, with relevant alternatives allowed; they are not exact-set common-ancestor counts.

| Focal M05 group | Bottom-up finding and comparison |
| --- | --- |
| 1138 | The original sick-after-chocolate/worry-after-tea pair at1046 gains chocolate and tea variants through1051,1061,1084,1138. All six masks explicitly concern large consumption within a short time. HDBv3/1204 already has the exact six; M01/1086 and M04/1084 have five and the same two notes. M05 restores V113, not a missing note relationship. |
| 1313 → displayed1355 | 1020 pairs buying tomatoes with preparing salsa; 1067 pairs tomato salsa preparation with Bolognaise tomatoes. Later children add fried homegrown tomatoes and tomato tortilla. Displayed1355 adds V259/V260/V652, ending with five notes. M01/1257 and M04/1338 already expose those five notes through tomato-bearing masks. Adding N026's V198 quantity mask is not a new fifth-note discovery. No claim that the dishes share a recipe is needed. |
| 1421 | 1211/1314 link growing food with ⟦Eat⟧ ⟦Mostly plants⟧; 1232/1304/1333 link ⟦lost skill⟧ to plant-based-diet/clicks/boring masks; 1421 reunites the two same-note branches. Food production and plant-focused consumption provide a broad bridge. The second child is less specific because social-media attention is not cultivation. M01/1348 and M04/1314 already connect N031/N074 using the more direct growing/plants masks. |
| 1431 → displayed1453 | V234's child-requested pancakes pair with V582's son eating ice cream at1276; V233 and N003's mother-buying-lunch masks join. Displayed1453 additionally includes V032's child happiness. These are legitimately children's food despite different foods and buying versus cooking. HDBv3/1499, M01/1520, and M04/1538 already offer the same three notes through these actions, with4,5,4 canonical vectors respectively. The exact V029-inclusive set's enormous M04 ancestor was misleading. |
| 1616 | 1035/1080/1227 link tiredness despite caffeine with not needing coffee after sleep; 1038/1111/1141/1189/1329 link tiredness and sleep advice. The other child1340 includes fasting duration, working while tired, nighttime waking, and eating before bed. 1616 unites them without adding a fourth note. M01/1300 and M04/1499 already offer the three notes through sleep/tiredness masks. M05's fasting addition broadens the scope; the notes do not prove that fasting caused any reported sleep change. |
| 1643 → displayed1719 | 1498 pairs V080 ⟦mochi bread⟧ ⟦combini⟧ ⟦ハムチーズ⟧ with V765 ⟦gianguja⟧ ⟦craftchocolate⟧; V764's melanger and V763's store stock follow. Displayed1719 adds V087's Lawson mask. Both concern commercially available food, but the originals ask for a recipe versus announce stock, not one shared recipe/process. M01/1703 and M04/1651 already pair alternative masks V087/V764 from these same two notes. M05's additional food detail is not new note discovery. |
| 1684 | 1107 pairs V513 ⟦Sophia⟧ ⟦baby⟧ ⟦family⟧ with V605 ⟦Focus on⟧ ⟦family⟧; 1383 adds V188 ⟦#dadlife⟧; 1521 adds community/family; 1684 adds compound advice V588 ⟦Get enough⟧ ⟦sleep⟧ ⟦family⟧ ⟦Be positive⟧ ⟦Be kind⟧. Family is explicit, but the cross-note contribution from N024 remains a hashtag. HDBv3/1602, M01/1498, and M04/1513 already contain the other four masks and the same three notes. |
| 1693 | One child combines Japanese mochi-bread/recipe masks with Tandori chicken/yogo and kimchi; the other combines local Roti breakfast with ⟦india⟧/⟦india⟧ ⟦food⟧. Broad food/cuisine exploration is possible; no shared country or preparation method is established, and V701 ⟦sexi yogo⟧ remains weak on its own. M04/1685 already has16 of the17 masks and the same five notes. M05 reunites N040's no-service-charge mask V314; it does not discover a new fifth note. |
| 1722 → displayed1783 | 1530 pairs V404's pizza-access goal with V568's leaving a coffee shop after its device ban. Other avoidance masks join. This is a plausible broader connection about having usable local venues, not two instances of a restaurant being absent. The display also inherits the retaliatory-password thoughts and Bitcoin pizza goal through1749/1756/1783. M04/1611 already gives the two notes through five direct availability/avoidance masks. M01/1801 offers another two-note route via V403/V570/V571. The larger exact-set ancestors in those runs do not show lost discovery. |

For reproducibility, the relation-specific alternative lists behind the principal corrections were:

- Consumption: N016 V113–V115; N073 V672–V674.
- Tomatoes: N023 V164; N026 V197–V200/V208; N031 V258–V260; N071 V648/V651/V652; N096 V871/V879/V880/V885/V891/V892. All named successful groups contain explicit tomato masks; the larger allowed list does not require every recipe mask to be present.
- Growing/plants: N031 V255/V256; N074 V676/V677/V687/V688.
- Children's food: N003 V025/V028–V033; N028 V233/V234; N068 V582–V587.
- Sleep: N034 V271/V272/V274/V275; N041 V318/V321/V324–V329; N069 V593–V595.
- Family: N024 V188; N061 V507–V516; N069 V588/V603/V605. The actual successful groups use V513, not only the more permissive infant alternatives.
- Commercial foods: N011 V078–V082/V085–V087; N081 V762–V766.
- Five-note food/cuisine group: N011 V078–V082/V085–V087; N040 V311–V315; N076 V699–V703/V710; N078 V717–V722; N098 V907–V913.
- Pizza/coffee-shop access: N050 V399/V401–V405; N065 V554–V559/V563–V571.

## 5. Other changed intermediates: smaller does not settle usefulness

### M05/1518

1353 pairs V129/N018 ⟦Off⟧ ⟦couple of days⟧ ⟦running⟧ ⟦errands⟧ with V348/N043 ⟦stuck in the same position for too long⟧. M04/1343 already has this pair. N043's original describes desk work, coffee as motion, and stretching, so a contrast between activities is defensible; the mask itself does not name desk work. 1459 adds V273/N034 ⟦4 more hours of work⟧. The other child1399 pairs a weekend-starting gym session with being off for errands while enjoying morning coffee. 1518 connects these children. Daily activity/work and time off is a broad commonality, not one workout or one work problem. This inspection does not establish a useful new note relationship over both comparators, and the pre-existing weak pair should not be attributed to median alone.

### M05/1732 → displayed1771

1555 pairs V033's contrast between a resentful online critic and a mother buying a child's lunch with V559's complaint about successful hipsters imposing a coffee-shop device ban. 1564/1567/1639 add variants. A broad connection between judgments about consumers and businesses is possible without agreeing with either insult. M01/1680 and M04/1628 have exactly the same five-mask, two-note descendant as M05/1639.

1732 adds V831/N092: ⟦We get⟧ ⟦bnb guests⟧ ⟦older⟧ ⟦i always worry about someone falling⟧. The original explains proposed bathroom grab bars. Grouping clientele-related experiences is possible at a broader level, but fall prevention is not the same claim as criticizing a clientele or an owner. The display further adds V028's market/busy-mother mask and V830's older-guests mask at1771. This is a questionable extension of a preserved smaller group, not evidence that its coherent two-note descendant disappeared. M04/M01 attach V831 elsewhere, but their alternatives were not established as an overall better semantic solution here.

### M05/1750

1658 pairs V083/N011 ⟦I⟧ ⟦in Japan this summer⟧ with V176/N024 ⟦Rome wasn’t built in 6 weeks⟧. N024's original uses the latter to argue for long workout plans; it is not an account of travel to Rome. 1725/1750 then add Charlotte arrival and jet lag. The Japan/Charlotte travel connection is real, but the initial Rome addition is weak. Importantly, M01/1702 and M04/1650 already make the exact same misleading pair. Their displayed travel groups1761/1735 include the same three notes. M05 adds a Charlotte jet-lag mask where those groups contain a Japanese-food-discovery mask; this is not a newly created median failure or cleanly repaired travel group.

### M05/1770

1761 pairs N048's bare ⟦dream⟧ with N054's ⟦ISLAND LIFE⟧; 1764 adds N054's bare ⟦Freedom⟧; 1770 adds V619/N069 ⟦accept that not everything needs to be said, even if this means things do not go your way⟧. Aspirations and one's attitude to life is a possible very broad bridge. The full originals do not turn the hashtags into substantive discussion of self-restraint, however. A compact size is insufficient to count this as useful discovery. M04 places V619 with a much broader advice branch, including the shorter V618 mask; that does not establish that all those notes must be moved or that M05 has lost their other advice relationships.

## Coverage registry

These are inspection batches, not a proposed hierarchy cut. All fragment arrays belonging to the listed original IDs were read. Each listed internal merge's children were inspected.

| Raw group | Original IDs | Internal merge IDs |
| --- | --- | --- |
| 1138 | V113–V115, V672–V674 | 1046,1051,1061,1084,1138 |
| 1285 | V578,V919,V920,V924 | 1171,1223,1285 |
| 1313 | V164,V197–V200,V208,V258,V648,V651,V879,V880,V891 | 1020,1067,1076,1094,1098,1106,1167,1201,1244,1313 |
| 1421 | V255,V256,V675–V677,V687,V688 | 1211,1232,1304,1314,1333,1421 |
| 1431 | V029–V031,V233,V234,V582 | 1276,1299,1335,1370,1431 |
| 1467 | V071,V075,V077,V399,V484,V485 | 1378,1403,1437,1464,1467 |
| 1518 | V123,V129,V131,V273,V348 | 1353,1399,1459,1518 |
| 1616 | V271,V272,V274,V275,V318,V321,V324–V329,V590–V593,V595 | 1035,1038,1080,1111,1141,1178,1181,1189,1214,1227,1250,1329,1340,1432,1616 |
| 1643 | V080,V763–V765 | 1498,1544,1643 |
| 1684 | V188,V513,V588,V603,V605 | 1107,1383,1521,1684 |
| 1688 | V181,V183,V282,V586,V660 | 1356,1686,1688 |
| 1693 | V078,V079,V081,V082,V085,V086,V311–V315,V700,V701,V703,V721,V722,V910 | 1247,1324,1368,1374,1382,1385,1405,1415,1468,1477,1519,1541,1556,1602,1615,1693 |
| 1722 | V404,V556,V566–V569 | 1530,1582,1620,1622,1722 |
| 1732 | V027,V033,V557–V559,V831 | 1555,1564,1567,1639,1732 |
| 1750 | V038,V039,V083,V176 | 1658,1725,1750 |
| 1770 | V383,V434,V441,V619 | 1761,1764,1770 |

The 37 full originals were N003,N005,N010,N011,N016,N017,N018,N023,N024,N026,N028,N031,N034,N036,N040,N041,N043,N048,N050,N054,N057,N061,N065,N066,N068,N069,N071,N072,N073,N074,N076,N078,N081,N092,N096,N098,N100. Same-note display extensions explicitly checked were1355,1453,1719,1749,1756,1783,1771; they are additional to the95 focal merges, not additional independent success cases.

No inference/model run, code change, Cargo operation, commit, card mutation, or write outside this report was performed. The findings support a distinct useful median tradeoff and a concrete local regression; they do not select an overall winner.
