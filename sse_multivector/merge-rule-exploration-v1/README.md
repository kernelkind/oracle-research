# Merge-rule exploration

Goal: find evidence-backed alternatives to HDBv3's single-edge merge rule for broad-to-narrow content discovery. Existing notes, masks, vectors, angular distances, source-note eligibility, and display simplification remain fixed. The merge experiments use no generated titles or manual reassignment. This directory is separate from earlier experiments and user-authored notes.

The separate [M06 titled note view](inspection.md#m06-with-provisional-titles-and-original-notes) now adds provisional reading aids to the unchanged five-note projection. It uses all 150 displayed groups and all 100 original notes, not a manually rearranged hierarchy. Broad Food or Coffee can be sufficient; the manual preparation subgroup is not a required target. Repeated broad labels expose the current lack of informative narrowing at some levels. These inspection titles do not change or validate the merge rule.

**Start with [the inspection package](inspection.md): verified TUI commands, exact masks and the main improvements and regressions.** M06 and M07 are the primary comparisons, M01 preserves useful contrasting groups, and M03 has an optional animal-processing/slaughter example. No final algorithm is selected. The sections below retain the chronological research and experiment record; their “next question” paragraphs explain why the following experiment was run.

The separate [Infomap comparison](../infomap-experiment-v1/README.md) reuses M07's exact graph, then tests three nearest-neighbor subgraphs while preserving its weights and frozen SSE inputs. All four outputs are available in a native-module viewer. None produced nested modules; local membership results are mixed. This does not replace or revise any M01–M09 result.

## Research that determines the first experiment

Gowda et al. (2026), *Chamfer-Linkage for Hierarchical Agglomerative Clustering*, directly studies per-point nearest-neighbor linkage. Our proposed symmetric mean is their normalized symmetric variant divided by two, before adapting excluded edges. Section 3 supplies exact point-to-group update equations. All variants can lack increasing merge costs. The headline method instead uses unnormalized directional sums and chooses the cheaper direction. Appendix A.3 evaluates the best label agreement across several cut orders; those results do not establish semantic navigation quality. [Paper](https://arxiv.org/html/2602.10444v1)

Cena and Gagolewski (2020), *Genie+OWA*, §5, also separates point-level, group-level, and directional aggregation. Its strongest configurations use different aggregators plus a cluster-size correction. They do not validate symmetric averaging alone. [Paper](https://doi.org/10.1016/j.ins.2020.02.025)

These findings justify a controlled first experiment, not a predetermined sequence of algorithms. After examining its changes, choose the next question and targeted literature review.

## M01 — Symmetric nearest-neighbor means

**Question:** Does considering each eligible endpoint change the single-edge attachments in useful ways, without destroying coherent smaller groups?

**Change:** For each point in A, use its nearest permitted point in B. Average these distances; repeat in the other direction; average the two means. When a point has no permitted partner, omit it from that directional mean and record the omission. The exclusion of edges is unchanged. Requiring every endpoint to have a partner would create an additional constraint that can prevent a complete tree even with a connected permitted graph.

**Controls:** HDBv3 and the complete frozen 916-point / 945-original-ID / 100-note artifact. Compare memberships by original IDs, not coincidentally equal merge IDs.

**Implementation checks:** Exact global pair selection compared against exhaustive recomputation on small numeric inputs. Explicit tests for excluded edges, disconnected input, and a score inversion using actual unit-vector angular geometry. The experiment stores raw merge costs and does not present them as HDBSCAN density lifetimes.

**Result:** M01 completed in 1.31 seconds. All 916 canonical vectors, 945 original IDs, and 100 notes remain. There are 18 parent-score inversions and 390 merges where at least one endpoint has no permitted partner in the opposite group. Those endpoints were omitted as declared, not assigned artificial distances.

| Structural measurement | HDBv3 | M01 |
| --- | ---: | ---: |
| Raw maximum depth | 565 | 161 |
| Groups after unchanged note-set simplification | 246 | 428 |
| Maximum simplified depth | 54 | 33 |
| Simplified groups with one child | 86 | 116 |

These counts describe structure, not semantic quality. M01 preserves exactly 246 of the baseline's 915 raw membership sets; changed merge order alone is not counted as a changed group.

**Initial inspection:** Read the first 32 changed cross-note groups, the full masks in M01/1292, /1316, /1337 and /1373, and the original notes needed to interpret the pie/bread/cream examples. Most early changes remain interpretable: coffee, dietary variety, egg-related material, crockpot cooking, and bread ingredients. No semantic titles were generated or used. These initial observations are not an overall pass rate; complete reading coverage is now documented below.

**Concrete changed decision:** V777/N083 selects `⟦easter matcha-cashew pie⟧ ⟦no refined sugar⟧`. Its strongest individual connection still points to V355/V356/N045, `⟦Half & half⟧ ⟦ruining my coffee⟧`, with cosine 0.635076. Neither vector changed. In HDBv3 it joins an 81-vector, 30-note group at1270. In M01 it instead pairs with V666/N072, `⟦Irish soda bread⟧ ⟦I tried out recently⟧ ⟦currants aren't in season yet⟧`, at1261. Their cosine is0.595311.

At that M01 decision, the half-and-half vector already belongs to group1259 (42 vectors/19 notes). The candidate score to that whole group is1.016842. The candidate score to V666 alone is0.933144; the current bread-heavy group1242 scores0.962995. Lower scores are merged first. Thus the changed placement comes from group-level evidence, not different embeddings or a hand-moved note. The pie/bread pair is plausible, but broader semantic value still requires inspection; neither mask is a complete baking recipe, and the original pie is explicitly no-bake.

**Preserved useful pairs:** V237/N028 and V663/N072 remain together alone at M01/1151 (baseline1224). V114/N016 and V674/N073 remain together alone at M01/1053 (baseline1076). The half-and-half mask now first pairs with the raw-cream coffee mask at M01/1110. These are specific preservation/improvement candidates, not proof that every changed branch is better.

**Next question:** The normalized rule still produces many one-child levels. The 2026 paper explicitly studies removing normalization. Test that single change next, preserving symmetric aggregation and all other controls. Check whether less chaining merely creates arbitrary small groups, rather than assuming a shorter hierarchy is better.

**Completed inspection:** The [complete M01 audit](audit-M01-complete.md) covers all 915 internal nodes: 444 exact recursive M04 matches and 471 newly inspected transitions. It includes all 100 original notes and checks the relevant alternate masks behind the strongest gain/loss claims. Useful Christmas, photography and animal-flesh extensions coexist with weak pairs and very broad upper parents. This is complete reading coverage, not semantic approval. M01 is included as a focused contrast in the inspection package.

## M02 — Symmetric nearest-neighbor sums

**Question:** Does removing normalization reduce chains while preserving useful group membership? This changes only directional means to directional sums; it does not change distances, exclusions, or the symmetric combination.

**Result:** 1.41 seconds; all inputs preserved. Raw maximum depth falls to 16, and the unchanged note projection has 513 groups, maximum depth 10, and 7 one-child groups. There are no observed parent-score inversions and 383 merges with omitted unsupported endpoints. Replaying M01 after the implementation change reproduces every saved merge and source checksum exactly.

**Concrete regression candidate:** M02/1294 contains V355/V356 and V357, the two half-and-half coffee complaint masks from N045, together with V777/N083, the matcha-cashew pie mask. No narrower descendant separates the coffee complaint from the pie. M01 instead offers the raw-cream coffee pair at1110 and pie/bread pair at1261. The M02 ancestor1703 further joins these masks to caffeine, iced coffee, and ice-cream material; its ancestor1769 also inherits a baby's name and affection through a coffee-shop song mask. This is evidence to inspect, not a declaration that every unusual shared subject is invalid.

**Why this changed:** At the exact partition immediately before M02/1118, V355 is alone; the raw-cream coffee vector V504 already belongs to group1056 with V503 (coffee) and V653 (breakfast coffee). Compare two available choices for V355:

| Other group | M01 rule at this fixed partition | M02 rule at this fixed partition |
| --- | ---: | ---: |
| V777 alone | 0.882689 | 0.882689 |
| Group1056, three coffee vectors | 0.862207 | 1.756219 |

Lower scores merge first. Removing normalization reverses these choices: the receiving group's accumulated reverse cost outweighs the coffee connection. This establishes a score-level mechanism at one fixed state, not a claim that rerunning M01 would follow this same earlier history. V777 itself still has its closest individual connection to V355; that embedding limitation remains unchanged.

**Next question:** Does requiring both directions cause this delay? Keep the sums but use the smaller directional sum, following the main Chamfer rule rather than its symmetric variant. This is M03. For a singleton entering an existing group, this removes the receiving group's reverse cost, but also restores single-linkage-like attachment. Check the resulting chains and mid-level memberships, not merely whether the motivating pair changes. Retain exact global score selection: our finite-only omission policy does not inherit the paper's monotonic directional-update shortcut.

**Completed inspection:** The [complete M02 audit](audit-M02-complete.md) covers all915 transitions:408 exact recursive prior matches and507 freshly inspected transitions, all945 masks,2490 fragments and100 complete originals. Useful descendants and a qualified activity group survive, but compact Christmas, photography, tea, preservation and restaurant extensions are weaker than several other runs. This is complete reading coverage, not an overall pass or rejection. The observations below were the earlier bounded inspection.

**Independent inspection beyond coffee:** All 26 canonical leaves under M02/1791 and five comparison masks were inspected, with seven full original notes. M02/1362 preserves the exact six-vector audiobook/literature group found at M01/1527 and HDBv3/1674.

**Correction to an apparent improvement:** M02/1508 combines seven purpose/open-mindedness/philosophy masks; those exact seven first coexist at M01/1793 (856 vectors). But M01/1666 already contains six of them, with exactly the same two notes, N054 and N069. The additional V628 comes from N069, which is already represented by five other masks. Thus M02 reunites a vector but does not establish a new note-discovery improvement over M01. M04/1677 later reproduces the same seven-vector group. This is why complete vector-set preservation is not the objective. The audiobook and purpose examples also rely on bare hashtags from N054 rather than rich substantive cross-note coverage.

The same inspection found questionable intermediate combinations, without treating them as automatic failures: M02/1567 combines `Movies`, `Music`, and `biking instead of the car`. General activities is a possible broader interpretation. M02/1553 joins a Sorrento food walk to travel/jet-lag masks from Charlotte; travel is a legitimate commonality. M01 is not consistently better: M01/1489 joins three-stop Sorrento food-walk masks to three discounted rotisserie chickens. Source masks and full notes, rather than inferred labels, determine these judgments.

## M03 — Smaller directional nearest-neighbor sum

**Question:** Does removing the receiving group's reverse cost preserve useful attachments without restoring single-edge chains? M03 changes only M02's final combination: use the smaller directional sum rather than half their sum. Exact global updates remain in place; no monotonic nearest-neighbor shortcut is assumed.

**Result:** 1.56 seconds; all 916 vectors and 100 notes retained. Raw maximum depth109; unchanged note projection496 groups, maximum depth45, and304 one-child groups. There are no observed parent-score inversions and405 merges with unsupported endpoints. Replaying M02 after adding this rule reproduces every merge and source checksum exactly.

**Concrete result:** The coffee complaint V355 now enters an existing six-note coffee group at1127. V777's pie mask subsequently enters that group at1231, which then contains12 vectors from7 notes. This is smaller than HDBv3's30-note first attachment but does not establish a suitable shared subject. In particular, the M01 raw-cream/half-and-half pair no longer exists alone.

**Preservation checks:** The coffee-shop music pair remains at1042, the chocolate/tea consumption pair at1066, and the recipe pair at1190. These are raw membership checks; equal-note transitions can be collapsed in the display without losing note access. V627 and V635 first coexist at M03/1816, with229 vectors from56 notes. That does not establish lost purpose/philosophy note access: the complete V629 alternative supplies a five-note option at1670, and open-mindedness alternatives provide four-note1593. The complete audit corrects the earlier exact-vector interpretation.

**Analysis:** The removed reverse cost does change attachments as predicted, but M03 has many successive one-child levels after exactly the same simplification. Neither symmetry nor tree depth alone identifies a winner. This result led to the all-pairs comparison in M04.

**Completed inspection:** The [complete M03 audit](audit-M03-complete.md) covers all915 transitions:278 exact recursive prior matches and637 freshly inspected transitions, all945 masks,2490 fragments and100 complete originals. Christmas1603 and photography1527 remain useful. Animal-processing/slaughter1778 offers a focused six-note parent with three-note1614 retained underneath, and is included as an optional inspection stop. Tea separates to the root, while food/emotion and concrete preservation need broader parents. No overall winner follows.

## Reproducing the additional runs

Use the M01 command below with the same four input paths. For M02, add `--rule symmetric_sum`, set `--run-id M02-replay`, and use a new output path. For M03, use `--rule min_sum`, `--run-id M03-replay`, and a new output path. Output files are never overwritten. Compare complete `merges`, aliases, canonical IDs, and input checksums; elapsed time, run ID and current source-code hash may differ.

## M04 — All eligible cross-group pairs

**Question, before running:** Do nearest-partner rules actually give better memberships than considering every eligible connection between the two groups? The preceding experiments changed normalization and directional combination; they have not yet isolated the value of nearest-partner support against this standard comparator on the frozen 100-note input.

Use average linkage, adapted only to the same fixed excluded edges: sum all permitted cross-group distances and divide by their count. This is not a mean of the two child scores and is not the earlier repository experiment over preselected fine segments with `1 - cosine` distances. Existing code was inspected; it cannot be reused unchanged without altering this experiment's frozen inputs and eligibility policy.

Average linkage is the established all-pairs rule. Its exact definition and finite-input requirement are documented by [SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.linkage.html). The whole-hierarchy analysis of Cohen-Addad et al., §6.1, concerns a distance-weighted objective, not semantic navigation; its guarantee is not claimed for our omitted-edge denominator. [Paper](https://arxiv.org/html/1704.02147v1)

The tradeoff to inspect is specific: considering every pair may prevent a few close representatives from joining poorly related groups, but may also penalize legitimate broad groups whose different subsubjects need not all resemble one another. A standard comparator is more informative now than choosing an intermediate normalization exponent from the observed examples.

**Result:** 1.38 seconds. All 916 vectors and 100 notes retained; raw maximum depth53, no observed parent-score inversions,379 merges with unsupported endpoints. The unchanged note projection has485 groups, maximum depth23, and114 one-child groups. The saved file passes the production TUI loader.

**Initial inspection:** The raw-cream/half-and-half pair remains alone at1097; coffee-shop music at1026; chocolate/tea consumption at1046; recipes at1133. The purpose/open-mindedness branch is available at1677 with the same two notes as M01/1666 and M02/1508. The pie mask first pairs at1275 and later enters the20-vector group1381, which includes bread-related masks and a spaghetti-preparation mask. All masks in the named small groups and1381 were read. These observations justify further comparison, not an overall semantic verdict.

Reproduce with `--rule average`, a fresh run ID and a new output path. In the viewer, use `M04.json` with the same map and notes. Eligible-edge degrees differ between source rows, so this comparison also changes their effective weighting; it is not a pure inner-minimum-to-mean substitution.

**Completed inspection:** [Audit A](audit-M04-A.md), [audit B](audit-M04-B.md), [audit C](audit-M04-C.md), and the [connecting parents](audit-M04-upper.md) cover all 916 canonical vectors, 945 original IDs, 2,490 exact fragments and 915 merges. This is exhaustive M04 reading coverage, not a semantic pass rate. All fragments were checked against original byte ranges. The [targeted M01 regression search](audit-M01-regressions.md) separately checks alternate masks before claiming lost note discovery; it does not claim full M01 semantic coverage.

There are real tradeoffs. M04 brings animal-slaughter notes N013/N048/N055 together at 1506 and food/emotion notes N024/N059/N064 at 1495. M01 instead retains a Christmas extension involving N062 at 1655 and a photography/painting connection involving N064 at 1637; M04's relevant alternatives first meet at 100-note ancestors. M01 and M04 both preserve food-storage and garden connections missing from compact baseline branches. These judgments are provisional and source-grounded, not label agreement scores.

The unchanged viewer still exposes a 99-note child below M04's 100-note root. Fewer raw levels therefore did not solve all navigation problems. Useful smaller descendants coexist with weak pairs and broad upper transitions. M02/M03 remain saved contrasts, not selected winners.

**Verification:** All 11 numeric tests pass. Replaying all four rules with the current runner exactly reproduces each saved 915-merge history, aliases, canonical IDs and input checksums. M04 passes the production merge-history viewer with 485 groups and all 100 notes.

## M05 — Median of eligible cross-group distances

**Question:** Does replacing the all-pairs mean with the ordinary median yield useful groups that neither magnitude-sensitive averaging nor per-point nearest partners preserve? This is a distribution-aggregation comparison, not a claim that the existing losses are caused by outliers. Use the middle value when the count is odd, and the average of the two middle values when it is even. Excluded edges remain absent, not artificial infinite observations. Do not choose a percentile from the semantic results.

**Research:** Gagolewski et al. (2023), §3.2 Definition2, applies ordered weighted averages to all cross-group pairs, explicitly including medians, quantiles and trimmed means. It is not an MST-only framework. Its later theorems concern particular weight generators; they do not automatically cover every quantile convention. The paper supplies theoretical linkage results, not semantic-navigation evidence. [Paper](https://arxiv.org/pdf/2303.05683)

The implementation must use the actual cross-pair median, not SciPy's differently defined centroid-based `method="median"`. The latter would change the question and geometry. [SciPy definition](https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.linkage.html)

**Fixed-state check before implementing:** At M04's exact partition before V518 joins1659, the mean distances to the regional-meal group1659 and Christmas group1669 are1.233848 and1.243088; medians are1.220974 and1.257601. Median therefore does **not** favor the Christmas alternative at this state. For V549, before its attachment to work group1402, the only eligible distance to1402 is1.105920; the mean to the art group1490 is1.265650 and its median1.322550. Median again does not reverse the local choice. These are fixed-state calculations, not a complete M05 replay. They rule out claiming in advance that median directly repairs these two decisions.

**Reason to test:** The statistic is genuinely distinct and cheap to compare across the full frozen tree. It reduces magnitude sensitivity to extreme pairs but can still penalize legitimate heterogeneous groups, ignore a minority of vectors, and inherit erroneous singleton pairings. Inspect new groups and preserved/lost note relationships rather than treating either known example as the entire test. No labels or manual assignments enter the run.

**Implementation plan:** Recompute each changed pair's exact median from the frozen eligible distances; retain exact global heap selection and the existing support reporting. Do not average child medians, alter merge heights, or import a nearest-neighbor shortcut. Check against independent exhaustive selection before running the corpus. Optimize only if measured local runtime warrants it.

**Result:** The exact implementation completed in5.75 seconds, preserving all916 canonical vectors,945 original IDs and100 notes. Raw maximum depth is47; no parent-score inversions occurred;370 merges have unsupported endpoints under the unchanged exclusion policy. The production viewer retains500 groups, maximum depth23 and124 one-child groups. These are structural measurements, not semantic scores. Thirteen numeric tests pass, including independently sorted cross-pair medians and exhaustive global selection. All five saved runs reproduce exactly after this addition.

**Semantic findings:** The [seven-relation audit](audit-M05-relations.md) confirms preservation of M04's slaughter, food/emotion and food-storage discoveries, but not M01's Christmas or photography extensions. The [new-group audit](audit-M05-new-groups.md) finds a useful restaurant-food-availability group1467 across N010/N050/N057 that the other runs do not expose compactly through the declared relevant alternative masks. It also finds a weak bread-failure/ice-cream-serving pair1686; other bread masks still preserve useful bread-note access, so this is not total lost discovery.

**Mechanism and qualification:** Before1437, V399/N050 can join1403={V075,V077 from N010; V485 from N057}. The three distances are1.064952239,1.065452461,1.284297580. Median1.065452461 favors this third-note addition over the available N057 variant V484 at1.074607679; mean1.138234093 does not. This is a real local choice reversal, not a full causal replay. Crucially, the median majority consists of two masks from **one** note, not two independent notes. Its useful result does not prove source-note consensus.

**Correction to the earlier comparison:** The food/emotion alternative list originally admitted N024 V181–V183. Its96-note M01 bound was valid for that list, but V173 also contains the ice-cream joke. Including it gives M01/1377 at36 notes. M04/M05 still provide the three-note relation much more compactly;96 must not be presented as an exhaustive bound. The relation audit records the complete alternative checks.

**Completed inspection:** [A](audit-M05-complete-A.md), [B](audit-M05-complete-B.md), and the [connecting parents](audit-M05-upper.md) cover all916 canonical vectors,945 original IDs,2490 exact fragments and915 merges. There are521 exact recursive M04 matches and394 newly inspected transitions. This is complete reading coverage, not a semantic pass rate or an overall winner.

**Additional regression:** M04/1587 exposes a three-note tea relationship across N042/N072/N080. M05 preserves the hot/morning-tea pair at1208, but every relevant tea-mask alternative involving N072 first meets it at the displayed root. N072's sweet-tea analogy remains with bread instead. The upper audit gives the exact alternatives and source context; this is a qualified loss of that extension, not of all tea discovery.

## M06 — Equal weighting of source-note pairs

**Question:** Does averaging separately within each unordered source-note pair, then averaging those pair means equally, improve the hierarchy compared with M04's vector-pair mean? The [pre-run research and definition](source-note-weighting.md) explain why source multiplicity is worth testing without declaring it inherently wrong. No input, distance, excluded edge, or display rule changed.

**Result:** 8.62 seconds; all916 canonical vectors,945 original IDs and100 notes retained. Raw maximum depth54; two genuine score inversions at1176 and1615;371 merges with unsupported endpoints. The unchanged viewer retains488 groups, maximum depth22 and129 one-child groups. These counts are not semantic scores.

**Complete inspection:** [A](audit-M06-complete-A.md), [B](audit-M06-complete-B.md), and the [connecting parents](audit-M06-upper.md) exhaust all915 merges and2490 exact fragments. There are599 exact recursive M04 matches and316 changed transitions. [Nine relation checks](audit-M06-relations.md) and a [new-small-group search](audit-M06-new-groups.md) separately admit relevant alternate masks before claiming better or worse note access.

**Findings:** M06 recovers compact Christmas and five-note animal-flesh groups also available in M01, and the tea group available in M04 but missing from compact M05 branches. Food/emotion remains useful. New promising intermediate options include physical activity1736, getting-going/caffeine1442, seasoning1397, tomatoes1285 and cooking/eating equipment1746. M05's restaurant-availability extension is not recovered; photography remains separated. Slaughter and concrete preservation still have relevant access, but with broader or weaker additions. A 99-note near-root child remains; in this food-focused corpus, its size alone is not proof of semantic incoherence.

**Mechanism, not a universal repair:** At1397, three source-pair means have4,2 and1 eligible edges. M04 gives them those weights and scores1.103133528; M06 weights the means equally and scores1.035868624. Both children are exact M04 subtrees. Conversely, the useful equipment group1746 has a higher M06 score than the M04 formula on the same children, and new singleton pairs retain identical scores. Earlier merge availability matters; a favorable final group does not prove that its own score decreased or that all multiplicity effects are solved.

**Verification:** All19 tests pass, including a real command-line test of valid aliases, conflicting map/request provenance and multi-source-alias rejection. That added test exposed an integer-JSON-distance loader error; explicitly reading numeric distances as float64 fixed it. All six complete saved histories replay unchanged after the fix. The M06 artifact retains the hash of the source that generated it; replay checks compare histories and frozen input hashes rather than falsely requiring the later source hash to match.

**Live viewer check:** Open1704, open V518's complete original with its inline mask, return, expand1453, and move upward to1781. The opened child stays nested and the unopened1761 sibling appears above it. Exiting restores the terminal. This confirms display behavior, not semantic approval.

## M07 — PARIS with fixed linear affinities

**Question:** Can a connection judged relative to the groups' connections to the rest of the corpus improve nested memberships? The [paper/source review and predeclared definition](surrounding-connections.md) specify PARIS on `1 − frozen angle / π`, preserving every eligible edge. Original degree mass stays fixed through unions. This is not new embedding geometry and not a pure change from mean to median: excluded edges have no graph weight, unlike omission from M04's denominator.

**Result:** 1.38 seconds; all 916 canonical vectors, 945 original IDs and 100 notes retained. Raw maximum depth 26, no score inversions, and two merges with unsupported endpoints. The unchanged viewer retains 904 groups, maximum depth 20, and 277 one-child groups. Neither shorter raw depth nor monotonic scores demonstrates semantic improvement.

**Complete inspection:** [A](audit-M07-complete-A.md), [B](audit-M07-complete-B.md), and the [connecting parents](audit-M07-upper.md) cover all 915 transitions and 2,490 original mask fragments. There are 162 exact recursive matches to M04 or M06 and 753 changed transitions. All masks, including aliases with different fragments, were read; full originals were used throughout. The [13 relation checks](audit-M07-relations.md) retain the previously declared generous alternate masks.

**Findings:** M07 restores photography 1080, preserves Christmas 1455, tea 1426 and physical activity 1276, and restores restaurant access at 1523 with a relevant coffee-shop restriction added. It does not dominate M06: the complete tomato and seasoning extensions are less focused, as is the three-note food/emotion extension. Useful partial groups survive. Concrete preservation still includes the weak vacuum-sealer/grab-bar link. The upper tree has intelligible food/drink broadening alongside mixed numeric, technical and generic fragments; no coherent complete top-level partition is established.

**Mechanism:** The [fixed-pair score diagnostic](audit-M07-score-factors.md) separates original-degree effects from the fraction of possible cross pairs that are eligible. Across nine saved decisions, both factors favor useful and weak groups. Removing only the explicit eligibility-fraction factor reverses eight inspected competing-pair comparisons; these are fixed-state calculations, not reruns or proof of whole-tree causation. Source-note size also affects original degree. This warrants a source-grounded investigation of the null model's treatment of eligibility, not an automatic claim that degree correction caused every improvement or regression.

**Verification:** All 25 tests pass. Six new tests were first verified to fail before implementation; they cover external-degree influence, preserved internal degree mass, independent exhaustive full histories, exact ties, eligibility guards and the constant-edge source-size effect. Independent numerical review found no defect. All seven saved 915-merge histories, aliases, canonical IDs and input hashes replay exactly with the current runner.

**Live viewer:** At 1626, expand 1312 and open V777's full original with its inline mask. Return and move upward to 1718: unopened 1133 and 1611 appear above the still-nested 1626/1312 chain. Exit restores the terminal. Reproduce using `--rule paris_linear`, a fresh run ID and a new output path; preserve the recorded affinity definition and original degree mass.

## M08 — Expected connections conditioned on eligibility

**Question:** Does excluding forbidden same-note pairs from M07's expected connections improve discovery? The [predeclared research and definition](excluded-expected-connections.md) distinguish absent evidence from zero similarity and conditioning from refitting expected strengths. Original affinities, original strengths, angular distances, edge eligibility, inputs and display remain fixed.

**Result:** 1.42 seconds, with all 916 canonical vectors, 945 original IDs and 100 notes retained. Raw maximum depth is 31, no score inversions, and 370 merges have unsupported endpoints. The unchanged viewer retains 502 groups, maximum depth 20 and 117 one-child groups. These are structural measurements, not semantic grades.

**Complete inspection:** [A](audit-M08-complete-A.md), [B](audit-M08-complete-B.md), and the [connecting parents](audit-M08-upper.md) cover all 915 transitions and 2,490 original fragments. There are 331 exact recursive M04/M06/M07 matches and 584 changed transitions. The [13 relation checks](audit-M08-relations.md) preserve all previously admitted alternate masks, including the separate future-lunch and concrete-preservation variants.

**Findings:** Tea1582 and restaurant1737 retain useful access; tomatoes1743 provides a more focused but qualified full extension than M07. Christmas1732 remains available with an additional generic gift/gratitude note. Photography separates again; food over time and concrete preservation need broader parents. The same vacuum-sealer/grab-bar pair survives. Some upper beverage and culinary unions remain intelligible, but the full root partition is not established as coherent. M08 is a mixed comparison, not a replacement winner.

**Mechanism:** The first 12 merges are identical to M07. At928, removing an excluded same-note expected contribution makes the Bitcoin-workshop alternative win instead of a greeting addition. That exact change reunites another mask of an already-present note; it does not add a discovered note. All eligible singleton rankings are unchanged up to one common rescaling, and conditional expected endpoint strengths need not match observed strengths.

**Verification:** Six new tests failed before implementation; all31 merge-rule tests now pass. Independent exhaustive checks cover the definition, eligibility, ties, normalization and complete small histories. All eight saved full histories replay exactly. The live production TUI opens1582, shows V670's complete original inline, expands1260 and moves up to1723 with unopened1534 above the still-nested children. No display code changed. Reproduce with `--rule paris_conditional`, a fresh run ID and a new output path.

## M09 — Largest finite nearest-partner distance

**Question:** Does replacing M01's average with the largest nearest-partner distance prevent poorly matched endpoints from disappearing in the average? The [research and predeclared definition](internal-variation-and-coverage.md) distinguish this adapted Hausdorff linkage from complete linkage, maximum directional means and minimax prototypes. Unsupported endpoints are still omitted and counted; this is not a complete-coverage guarantee.

**Result:** 1.79 seconds, preserving all 916 canonical vectors, 945 original IDs and 100 notes. Raw maximum depth is 29, with 28 genuine parent-score inversions and 345 merges with unsupported endpoints. The unchanged viewer retains 536 groups, maximum depth 19 and 62 one-child groups. These are structural measurements, not semantic grades.

**Complete inspection:** [A](audit-M09-complete-A.md), [B](audit-M09-complete-B.md), and the [connecting parents](audit-M09-upper.md) cover all 915 transitions and 2,490 exact fragments: 517 exact recursive matches to previously audited trees and 398 changed transitions. The [13 relation checks](audit-M09-relations.md) retain the same admitted alternate masks. Focused food/emotion1343 and slaughter1596 survive. Useful tomato-preparation1323 and Christmas1512 children remain, but their complete previously examined note extensions need broader ancestors. The complete tea, photography, restaurant and activity relations require all-note ancestors. M09 is not an overall improvement.

**Mechanism:** Two [fixed-child comparisons](M09-fixed-child-comparisons.md) reproduce the precise available masks and scores. Before1227, one coffee-tag endpoint raises the maximum for a larger coffee group above the pie/bread alternative, despite the coffee group's lower mean. Before1583, the maximum favors a regional-flavor branch over the available tea group, while the mean favors tea. These local choices show the cost of worst-endpoint sensitivity; they do not prove that rerunning M01 would follow the same history or repair every affected relation. The first six child-pair choices match M01, but their scores need not.

**Verification:** Six new tests failed before implementation; all 37 merge-rule tests pass. Independent numerical review checked 96 exhaustive small histories and the omission/reversal behavior. All nine saved full histories replay exactly. The live production TUI opens1482, expands1248, shows V531's full original with its inline mask, then moves upward to1507 with unopened1266 above the still-nested children. Reproduce with `--rule hausdorff_finite`, a fresh run ID and an unused output path. No display code changed.

## Comparison table

| Run | Group score | Raw maximum depth | Display maximum depth | Display groups | Display one-child groups |
| --- | --- | ---: | ---: | ---: | ---: |
| HDBv3 | Closest permitted edge | 565 | 54 | 246 | 86 |
| M01 | Average of both nearest-partner means | 161 | 33 | 428 | 116 |
| M02 | Half the sum of both nearest-partner sums | 16 | 10 | 513 | 7 |
| M03 | Smaller nearest-partner sum | 109 | 45 | 496 | 304 |
| M04 | Average of every permitted cross-group distance | 53 | 23 | 485 | 114 |
| M05 | Median of every permitted cross-group distance | 47 | 23 | 500 | 124 |
| M06 | Equal mean of unordered source-note-pair means | 54 | 22 | 488 | 129 |
| M07 | Original degree masses relative to cross-group graph weight (PARIS) | 26 | 20 | 904 | 277 |
| M08 | Eligible original degree products relative to cross-group graph weight | 31 | 20 | 502 | 117 |
| M09 | Largest finite nearest-partner distance across both directions | 29 | 19 | 536 | 62 |

These are structural measurements only. Before claiming a lost discovery path, check whether another vector from the same note already provides that access. Before claiming improvement from reuniting vectors, check whether any new relevant note becomes reachable. Exact memberships remain useful for locating changes, not as a substitute for the semantic and note-level objective.

M07 tests surrounding-connection evidence and changes singleton-pair scores, unlike M01–M06. M08 tests the treatment of excluded connections; M09 tests the worst supported endpoint instead of the mean. Neither removes the observed tradeoffs. The [within-child-structure review](within-child-structure.md) identifies useful CHAMELEON precedents, but also initialization, edge-count and implementation-version choices that prevent treating it as an unchanged drop-in rule. No M10 or final winner is selected. All nine complete-tree audits and the [inspection package](inspection.md) are available. No additional runs were needed to deliver the supported candidate comparison.

## Further literature considered

Maximizing the two directional means is the established modified Hausdorff distance MH1, not a new invention. James et al., Definition2.2 and Proposition3.1, also show that it can ignore changes in one direction while the other dominates. Their clustering uses distances between pre-existing time-series change-point sets, not this dynamic merge problem. This supports considering the measure but does not justify implementing it before inspecting the all-pairs comparator. [Paper](https://arxiv.org/pdf/1911.00995)

## Review-tool verification

The new `--merge-history` input uses the existing note-set projection and nested renderer, but accepts genuine decreasing merge scores without pretending they are HDBSCAN distances. Tests cover source masks, aliases, structural validation, score inversions, conflicting modes, and old HDB distance validation. All 65 hierarchy integration tests and both launcher tests passed. In a real terminal, M01 rendered, expanded, opened a full original note with its inline mask, moved upward while preserving expansion, and exited cleanly. Baseline counts match the frozen binary exactly.

From the repository root:

```sh
target/merge-rule-review-build/debug/hdbscan-hierarchy \
  sse_multivector/merge-rule-exploration-v1/M01.json \
  sse_multivector/real-note-fine-segmentation-v1/vectors/vector-map.json \
  sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json \
  --merge-history
```

Substitute `M02.json`, `M03.json`, `M04.json`, `M05.json`, `M06.json`, `M07.json`, `M08.json`, or `M09.json` to inspect another saved run. All nine pass the production loader. Add `--start-at 1467` for M05's restaurant example, `--start-at 1704` for M06's Christmas example, `--start-at 1523` for M07's restaurant example, `--start-at 1582` for M08's tea example, or `--start-at 1482` for M09's recipe/ingredient example. M05 was also verified in a live terminal: expand child1403, open V399's full original with its inline mask, return, move upward to1651 while retaining the expanded nesting, and exit. To build this binary from a fresh checkout, without changing the existing pinned launcher:

```sh
CARGO_TARGET_DIR=target/merge-rule-review-build CARGO_BUILD_JOBS=2 \
  nix develop -c cargo build --bin hdbscan-hierarchy
```

## Reproduce M01

From the repository root, this pinned Nix command supplies Python and NumPy without changing the repository's development environment. Python3.13.14/NumPy2.5.0 reproduces all nine saved histories exactly; the original runs used Python3.13.12/NumPy2.3.4. Numeric worker counts remain one. Choose an unused output path:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
nix shell --expr '(let pkgs = (builtins.getFlake "github:NixOS/nixpkgs/35d3407a3816f3b341d8cf1d60abaf2b7b8166ac").legacyPackages.x86_64-linux; in pkgs.python313.withPackages (p: [p.numpy]))' \
  --command python3 sse_multivector/merge_rule_experiment.py \
  --baseline sse_multivector/real-note-fine-segmentation-v1/hdbv3-cross-note-edges-v1/response.json \
  --request sse_multivector/real-note-fine-segmentation-v1/hdbv3-cross-note-edges-v1/request.json \
  --vector-map sse_multivector/real-note-fine-segmentation-v1/vectors/vector-map.json \
  --notes sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json \
  --run-id M01-replay \
  --output /tmp/M01-replay.json
```

The runner refuses to overwrite an existing output. Compare `merges`, IDs and source checksums; run ID, source-code hash and elapsed time are provenance rather than membership output.

For M06, use `--rule note_pair_mean`, a fresh run ID and an unused output path with the same four input files. It requires one source note per canonical vector, which the complete frozen artifact satisfies.

For M07, use `--rule paris_linear`. The other rule names appear in their experiment sections. With the same Nix prefix, replace the command after `--command` by `python3 -m unittest discover -s sse_multivector -p 'test_merge_rule*.py'` to run all37 numeric/CLI tests. The final verification ran all nine production CLI replays into temporary outputs and compared every merge, input hash, alias, canonical ID, exclusion count and summary; all matched. Saved results were not overwritten.
