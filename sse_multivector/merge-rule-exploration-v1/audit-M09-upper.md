# M09: connecting parents

M09 retains many useful local relationships, but replacing averages with the worst nearest-partner distance does not produce a clearly better discovery hierarchy. Focused food/emotion and slaughter groups survive. Several other complete note relations need much broader ancestors than in earlier runs. The independent [relation audit](audit-M09-relations.md) checks those statements through unchanged alternate masks.

## Scope and controls

The 65 disjoint reading boundaries cover all 916 canonical vectors, 945 original IDs and 2,490 fragments. [Audit A](audit-M09-complete-A.md) covers 419 internal transitions and [audit B](audit-M09-complete-B.md) another 419. Four boundaries have exact recursive matches to previously audited trees, covering 13 transitions: M09/1266 = M06/1269; 1248 = M06/1265; 1141 = M08/1231; 1506 = M06/1517. This report covers the remaining 64 connecting parents. These are reading divisions, not selected segments.

All boundary masks were read in source form, including both different-fragment alias pairs V247/V248 and V333/V334. Every one of the 2,490 fragments was independently checked against its original UTF-8 ranges. Complete originals were reopened for the ambiguous examples; A/B separately read the full source notes in their assigned subtrees. No linked content or generated title supplies missing evidence.

The implementation passed 37 tests, including six new tests first observed failing because the rule did not exist. An independent implementation review additionally checked 96 small exhaustive histories, 564 merges, 184 unsupported-endpoint merges and five parent reversals. All nine saved corpus histories replay exactly, including every merge, score, unsupported count, input hash and alias group. M09 took 1.79 seconds locally and retained 28 genuine parent-score reversals. Its 345 merges with unsupported endpoints have the declared omission policy, not a full Hausdorff coverage guarantee.

## Coffee, bread and ingredients

Coffee preparation 1002 and drinking/tags 1021 meet at raw1066, displayed1118 after iced/cool-place coffee joins. Hot coffee joins at1204, caffeine at1416, and coffee-shop music at1488. These are useful broader connections; the dog-only mask and nonspecific caffeine note remain qualifications.

The dairy-in-coffee pair1088 instead joins pie/bread ingredients at1227, then bread1244 at1340. The bread branch eventually joins the larger coffee branch at1570. A general food/drink connection is possible; this is not proof that the parent must be named coffee. But the [fixed-child comparison](M09-fixed-child-comparisons.md) shows exactly how the maximum changes this choice: one coffee-tag endpoint makes the larger coffee branch rank worse than the two baked-food masks, although its average nearest-partner score ranks better.

Cooking methods, recipes, ingredients and meal experiences form substantial subtrees through1562,1592,1648 and1717. Their variety is not automatically a failure. They also inherit weak attachments, and progressively collecting food-related material is not by itself evidence of useful narrowing at every level.

## Timing, context and incomplete relations

The three-note tea relation separates: N042/N080 tea masks remain together at1192, while N072/V670 joins a local-flavor/recipe-variation branch at1583. Both alternatives are explicit meanings of their source masks. At the same available children, the average favors the tea group and the maximum favors the regional-food group. The comparison identifies a local ranking effect, not proof that a complete mean-linkage replay would recover the relation; M01 itself did not recover a focused three-note tea parent.

Node1761 combines gym/kitchen/future-lunch timing with homestead/preservation and longer-timescale food statements. Its smaller size than the M08 counterpart does not make the entire union coherent. The focused egg-preservation/carcass-saving pair remains a meaningful descendant; separate statements about millions of years of meat eating and a claimed linoleic-acid half-life are different kinds of temporal evidence.

Node1774 joins sleep and mental-state material with weather/day observations. V322/V323 select ⟦Fog is lifted⟧, but the complete N041 note explicitly concerns mental clarity, sleep and not needing coffee. Literal weather is not established. Other N041 masks retain sleep/caffeine access. The available evidence does not isolate how much of this attachment comes from the mask, embedding or merge rule.

## Weak pairs are not repaired merely by using a maximum

M09/1422 still pairs N100/V939 ⟦vacuum sealer⟧ with N092/V829 ⟦I think⟧ ⟦safety grab bars⟧ ⟦bathroom⟧ ⟦cabin⟧ ⟦installing⟧. At two singletons the mean and maximum are identical: each has only one eligible distance. Later maxima can change parents, but cannot add missing semantic discrimination to that fixed pair. N092's separate crockpot passage is not evidence inside the grab-bar mask.

Other small associations differ. The previous Linux/lamb pair does not survive: lamb joins food material, while Linux later occurs in the mixed1820 branch. That is a changed local placement, not a new Linux-related discovery or proof that the whole branch is useful.

A fresh N008 reread also corrected an earlier M08 prose error: the note mentions chemotherapy but identifies neither a mother nor the recipient. The historical masks and results were unchanged; the unsupported prose attribution was corrected explicitly.

## Upper structure and actual viewer

The unchanged note-set projection yields 536 displayed groups, maximum depth19 and62 one-child groups. These are descriptive counts, not success metrics. Root1830 exposes groups1771,1792,1801,1810,1816,1823 and1829. The first contains broad food/provision/routine material; the others contain regional food, seasonal/day material, advice/technical material and several mixed residual branches. No coherent complete top-level partition is established.

The production viewer was opened at displayed1482. Expanding1248 preserved its nesting and showed the exact masks. Opening V531 showed the complete N063 original with its risotto/garlic mask inline. Returning and expanding upward to1507 placed unopened1266 above the already open1482/1248 branch. Quitting exited successfully. Raw1434 is correctly unavailable as a start group because the existing projection collapses it; use1482.

```bash
target/merge-rule-review-build/debug/hdbscan-hierarchy \
  sse_multivector/merge-rule-exploration-v1/M09.json \
  sse_multivector/real-note-fine-segmentation-v1/vectors/vector-map.json \
  sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json \
  --merge-history --start-at 1482
```

## Complete connecting-parent registry

Child IDs are raw immediate children, retaining the actual nesting. “Collapsed” means equal note sets under the frozen projection, not a semantic rejection. Observations below describe membership evidence; they are not generated navigation labels.

| Parent | Children | Notes | Display | Observation |
| --- | --- | ---: | --- | --- |
| 1066 | 1002 + 1021 | 14 | collapsed | Coffee preparation joins coffee drinking/tags. |
| 1118 | 1066 + 1117 | 14 | shown | Adds iced/cool-place coffee; the dog-only mask remains weak evidence. |
| 1204 | 1047 + 1118 | 16 | shown | Adds hot/made-today coffee. |
| 1328 | 1187 + 1283 | 14 | shown | Diet/meal provision joins cooking and meal examples. |
| 1416 | 1141 + 1204 | 18 | shown | Adds caffeine/decaf material; N034 does not specify coffee. |
| 1457 | 1402 + 1432 | 9 | shown | Bread/ingredient variations join raw-milk and bread masks. |
| 1475 | 1328 + 1474 | 21 | shown | Adds food enjoyment and attitudes to meal/preparation material. |
| 1480 | 1356 + 1438 | 11 | shown | Smoker/crockpot/pan material joins pasta and other preparation. |
| 1482 | 1248 + 1434 | 8 | shown | Joins ingredient/recipe children; includes the tomato joke. |
| 1488 | 1347 + 1416 | 19 | shown | Adds coffee-shop music/rave material. |
| 1498 | 1436 + 1437 | 10 | shown | Egg dishes join avocado/pie/pancake variations; broader than eggs. |
| 1507 | 1266 + 1482 | 9 | shown | Adds potato/lamb/rocket-stove meals. |
| 1562 | 1480 + 1507 | 17 | shown | Joins cooking methods and dish/ingredient examples. |
| 1564 | 1323 + 1500 | 11 | shown | Tomato preparation joins food quantities; not a tomato-only parent. |
| 1568 | 1308 + 1475 | 24 | shown | Adds cooktop/takeout/food-work compounds to food appreciation. |
| 1570 | 1457 + 1488 | 27 | shown | Coffee/caffeine/venues join bread/raw-milk material. |
| 1592 | 1562 + 1568 | 38 | shown | Joins cooking/dish and meal/appreciation branches. |
| 1624 | 1570 + 1623 | 30 | shown | Adds breakfast/coffee/bread-count material. |
| 1631 | 1552 + 1594 | 11 | shown | Shrimp/tandoori/regional dishes join steak/cheese dishes. |
| 1639 | 1533 + 1585 | 15 | shown | Meal provision/outings join eating choices and convenience. |
| 1640 | 1592 + 1639 | 47 | shown | Adds meal provision and eating behavior to preparation/dishes. |
| 1645 | 1545 + 1601 | 13 | shown | Animal-diet opinions join meat cutting/handling; generic pet tags remain. |
| 1646 | 1598 + 1624 | 32 | shown | Adds coffee-flavor/gamey-meat/taste material. |
| 1647 | 1498 + 1622 | 14 | shown | Egg dishes join hens/chicken/stock/Chinese-food material. |
| 1648 | 1640 + 1647 | 51 | shown | Adds egg/poultry branches to the broad meal/preparation branch. |
| 1689 | 1646 + 1657 | 37 | shown | Adds morning tea/coffee/greetings; altitude-site delight is a weaker fit. |
| 1702 | 1564 + 1619 | 12 | shown | Food quantities/tomatoes join Paraguay/Argentina meat practices. |
| 1713 | 1660 + 1702 | 15 | shown | Adds paratha/lamb/tandoori/tallow masks. |
| 1716 | 1631 + 1645 | 21 | shown | Joins meat/cheese dishes and animal-diet/handling branches. |
| 1717 | 1648 + 1716 | 60 | shown | Joins broad meal/preparation and meat/diet branches. |
| 1724 | 1667 + 1677 | 12 | shown | Food growing/diet opinions join restaurant/takeout/local-food material. |
| 1728 | 1713 + 1717 | 63 | shown | Adds tomato/quantity/regional-meat branches to broader food branches. |
| 1739 | 1689 + 1693 | 46 | shown | Adds snacks and food-celebration material to coffee/breakfast. |
| 1740 | 1728 + 1739 | 91 | shown | Joins broad food branches; also inherits their weak small attachments. |
| 1741 | 1506 + 1669 | 7 | shown | Mental-state/stretching material joins sleep/tiredness/duration. |
| 1751 | 1744 + 1746 | 18 | shown | Preservation/family-food attitudes join utensils/equipment/cooking. |
| 1761 | 1735 + 1756 | 15 | shown | Food/daily timing and kitchen work join homestead/preservation; mixed. |
| 1763 | 1751 + 1762 | 27 | shown | Adds seasoning/nutrition/jars to equipment/provision material. |
| 1764 | 1740 + 1763 | 94 | shown | Joins broader food branches; not proof of a focused seasoning route. |
| 1765 | 1700 + 1732 | 9 | shown | Survival/conditions joins food-quality/resistance; squirrel ambiguity remains. |
| 1766 | 1724 + 1765 | 19 | shown | Joins growing/availability and quality/conditions material. |
| 1770 | 1761 + 1766 | 30 | shown | Adds time/routine/homestead material; concrete preservation is diffuse. |
| 1771 | 1764 + 1770 | 97 | shown | Joins broad food/provision/routine branches. |
| 1773 | 1722 + 1749 | 16 | shown | Venue/weekend conditions join geographically qualified food; weak additions remain. |
| 1774 | 1727 + 1741 | 13 | shown | Sleep/mental clarity joins weather/day material; metaphorical fog is not weather. |
| 1786 | 1759 + 1768 | 15 | shown | Nostr tags/GM join family/community and online attitudes; mixed. |
| 1792 | 1773 + 1789 | 27 | shown | Regional food/venues join geography/waiting/duration and slaughter; mixed. |
| 1793 | 1771 + 1792 | 100 | collapsed | All 100 notes already present; omitted only by unchanged note-set projection. |
| 1796 | 1747 + 1760 | 9 | shown | Equipment/router/grab-bar material joins branded appliances/Nostr masks. |
| 1798 | 1673 + 1782 | 15 | shown | Bitcoin/Nostr joins brands/places/products; no clear common subject established. |
| 1800 | 1774 + 1799 | 17 | shown | Weather/day/sleep joins Christmas/gifts/hospitality; not a greeting-only parent. |
| 1801 | 1786 + 1800 | 26 | shown | Community/online material joins daily/seasonal material; broad mixed union. |
| 1802 | 1793 + 1801 | 100 | collapsed | All-note union; does not supply a focused four-note Christmas group. |
| 1803 | 1781 + 1795 | 13 | shown | Movement/exercise/keto joins assorted places/writing/addition masks; weak. |
| 1804 | 1798 + 1803 | 26 | shown | Joins technology/place and movement/assorted-action branches; mixed. |
| 1806 | 1780 + 1784 | 9 | shown | Purpose/knowledge/reading joins conduct/joy/advice; useful parts, loose whole. |
| 1809 | 1796 + 1806 | 16 | shown | Equipment/router material joins advice/reading; weak commonality. |
| 1810 | 1804 + 1809 | 32 | shown | Joins broad mixed technical/place/advice/action branches. |
| 1811 | 1802 + 1810 | 100 | collapsed | All-note union; useful local descendants do not validate this whole. |
| 1816 | 1807 + 1813 | 14 | shown | Social judgments join wine/place/age fragments; mixed. |
| 1817 | 1811 + 1816 | 100 | collapsed | All-note union; equal-note projection is not semantic approval. |
| 1823 | 1820 + 1822 | 16 | shown | Stress/work/technical tags join cookware/weather/vision fragments; mixed. |
| 1824 | 1817 + 1823 | 100 | collapsed | All-note union; equal-note projection is not semantic approval. |
| 1830 | 1824 + 1829 | 100 | shown | Non-semantic collection root; seven displayed branches, not seven approved subjects. |
