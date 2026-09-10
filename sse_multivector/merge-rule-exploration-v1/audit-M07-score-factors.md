# M07: fixed-pair PARIS score factors

The added evidence is **original total connection strength** and **the fraction of possible cross pairs that are eligible**, not another estimate of the mean pair angle. Lower degree products favor both useful and weak/mixed groups in these examples. Source-note exclusions also change several observed pair rankings materially, even though every selected final pair below has complete eligible cross support.

This is a bounded numerical diagnostic of the saved M07 history. It is not a new candidate, a causal explanation of the whole tree, or a semantic score.

## Exact decomposition

For disjoint canonical-vector groups A and B, let:

- a and b be their canonical vector counts.
- k be the number of finite eligible cross pairs, counting one A-by-B block.
- rho = k/(a × b).
- mean_angle be the ordinary mean of those k frozen angles: exactly M04's score **on these fixed children**, not a score from M04's different history.
- mean_affinity = 1 − mean_angle/π, because the declared affinity conversion is linear.
- mean_degree_A and mean_degree_B be the average **original** vector degrees in each group.
- W be the sum of all original vector degrees, counting every undirected graph edge twice.

For k > 0, production PARIS satisfies:

```text
D(A,B)
  = s(A) s(B) / [W w(A,B)]
  = (a mean_degree_A)(b mean_degree_B)
      / [W k mean_affinity]
  = [mean_degree_A mean_degree_B / W]
      / [mean_affinity × rho].
```

Write G = mean_degree_A × mean_degree_B / W. Thus D = G / (mean_affinity × rho). The explicit a × b size factor cancels. The rule does not directly reward small groups; memberships affect average original degrees, eligible affinity and eligibility fraction.

For rho = 1 and fixed G, the score is merely a monotone transform of M04's ordinary mean angle. New ranking information comes from variation in G and rho. There is no shared-neighbor-identity comparison or independent-note agreement test in this formula. Original degree mass includes edges that later become internal; it is not recomputed from the current external graph.

The production source confirms these parts: `_paris_weights` omits diagonal/excluded edges and converts eligible angles; initialization computes original degrees and PARIS singleton heap scores; union updates add original mass and cross weights. The inspected source SHA-256 equals M07's saved `source_code_sha256`:

```text
d5a8f523b3ea9a34fe82094724efa41f358be2feccd26f0cd7e2812feeef9f08
```

## Frozen input and verification

Used the existing production baseline loader, not recomputed embeddings or angles. The graph has 916 canonical vectors, 412,379 eligible undirected edges, 6,691 excluded undirected same-note pairs and W = **445440.1723263121**. Every canonical vector has one source note. Its finite neighbors are exactly all canonical vectors from other source notes; this equality was checked across the full matrix.

Replayed only the **saved** merge IDs and children to reconstruct the nine states immediately before the requested merges. No greedy history was regenerated. For each state, enumerated every currently eligible candidate pair, verified that the saved winner is the global PARIS minimum, and identified existing alternatives. This inspected 781,527 candidate pairs across the nine snapshots.

Each reported fixed-pair score was independently reconstructed from the original cross block and original degrees, then checked against production `pair_score` for both PARIS and M04-average definitions. Selected scores also match the saved M07 values within 1e-12. The linear mean-affinity identity and exact source-note exclusion mask were verified. Numeric work was local, single-thread NumPy; no `agglomerate` call or candidate output was made.

Read complete masks and children for the nine requested roots and all alternatives discussed here: 91 canonical vectors / 94 original IDs / 238 byte-validated fragments / 65 internal transitions, with their 43 source originals read across this diagnostic and the preceding relation inspection. The requested roots alone contain 45 canonical vectors / 47 original IDs / 121 fragments / 36 transitions. Linked contents were not interpreted.

## The nine actual final merges

Angles are radians. Degree means are per canonical vector, not per original alias ID. Every selected pair has rho = 1 because its child note sets are disjoint. All original aliases remain represented in the membership ledger below.

| M07 merge | Actual children A + B | a × b | Mean degrees A / B | M04 mean angle | Mean affinity | k / (a × b) | PARIS score |
| --- | --- | --- | --- | ---: | ---: | --- | ---: |
| 1455 | 659 + 1076 | 1 × 3 | 492.694 / 472.614 | 1.208573 | 0.615299 | 3/3 | 0.849587116 |
| 1080 | 353 + 963 | 1 × 2 | 479.114 / 444.245 | 1.129708 | 0.640403 | 2/2 | 0.746137036 |
| 1523 | 1253 + 1324 | 2 × 2 | 478.730 / 495.547 | 1.206615 | 0.615923 | 4/4 | 0.864688576 |
| 1426 | 370 + 1112 | 1 × 2 | 483.689 / 489.839 | 1.157219 | 0.631646 | 2/2 | 0.842085669 |
| 1276 | 1028 + 1160 | 2 × 2 | 450.887 / 467.092 | 1.298511 | 0.586671 | 4/4 | 0.805909436 |
| 1469 | 1208 + 1295 | 2 × 5 | 485.380 / 463.561 | 1.280133 | 0.592521 | 10/10 | 0.852501474 |
| 1525 | 1141 + 1256 | 3 × 2 | 452.698 / 456.302 | 1.456880 | 0.536261 | 6/6 | 0.864758725 |
| 1659 | 1493 + 1549 | 4 × 4 | 484.921 / 496.694 | 1.271121 | 0.595390 | 16/16 | 0.908174667 |
| 1626 | 1312 + 1502 | 3 × 4 | 503.152 / 501.198 | 1.157277 | 0.631627 | 12/12 | 0.896309861 |

Complete original-ID memberships of those actual final children:

| M07 merge | A masks | B masks |
| --- | --- | --- |
| 1455 | V518 | V426 V545 V748 |
| 1080 | V549 | V391 V761 |
| 1523 | V404 V568 | V077 V485 |
| 1426 | V670 | V333 V334 V731 |
| 1276 | V346 V622 | V121 V177 |
| 1469 | V016 V203 | V305 V327 V328 V489 V592 V787 |
| 1525 | V329 V383 V594 | V191 V753 |
| 1659 | V049 V387 V540 V921 | V023 V152 V769 V878 |
| 1626 | V291 V671 V777 | V159 V238 V245 V354 |

The semantic readings remain those in [the relation report](audit-M07-relations.md) and [the complete-A audit](audit-M07-complete-A.md). Christmas1455, photography1080, restaurants1523, tea1426 and activity1276 have defensible concrete relations. The requested weak/mixed examples differ:

- 1469's sides combine a three-stop food tour/three marked-down chickens with bedtime hours, waking counts, three-hour brisket smoking, a third storm round and 35-degree weather. The numbers do not establish one process.
- 1525 joins the bedtime/sleep/dream child with the DCA-tag/chocolate-gift pair. Neither full source supplies the latter investing/gift/chocolate connection.
- 1659 includes bare Linux paired with lamb dinner, a steak-cutting/risotto-lemon pair, a reasonable ground-beef/beef/beet-side child, and anger about Mr Beast/Lunchly. Surrounding food in N048's full note does not give the selected Linux tag a food meaning.
- 1626 is more qualified: sugar-bearing bread versus a pie without refined sugar can be a valid opposed ingredient relationship, and its whole seven-note group permits broad food/drink/preparation preferences. Its second-coffee/two-pieces-of-bread and cacao-pancake/half-and-half-not-cream children do not establish one common ingredient. The numerical diagnostic does not upgrade this mixed relation to a strong one or forbid broad compounds.

## Original degree changes the ordering even without cross exclusions

For each actual state, the next table selects the **smallest M04 mean angle among candidates with rho = 1**. These alternatives were present at that M07 state; this is not a claim about what the saved M04 run would choose. All nine alternatives have lower mean angle than the chosen pair but higher PARIS score.

G is the degree factor defined above. The last two columns compare the selected pair with the alternative; a score ratio below 1 means PARIS favors the actual selected pair.

| Selected merge | Full-support alternative A + B | Alternative M04 mean angle | Alternative G | Alternative PARIS | Selected G / alternative G | Selected score / alternative score |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1455 | 253 + 273 | 0.864995 | 0.620858 | 0.856752849 | 0.841981 | 0.991636 |
| 1080 | 641 + 652 | 0.666119 | 0.612783 | 0.777675276 | 0.779767 | 0.959445 |
| 1523 | 105 + 253 | 0.889515 | 0.622094 | 0.867806190 | 0.856110 | 0.996407 |
| 1426 | 253 + 273 | 0.864995 | 0.620858 | 0.856752849 | 0.856718 | 0.982881 |
| 1276 | 319 + 604 | 0.754730 | 0.616187 | 0.811026594 | 0.767305 | 0.993691 |
| 1469 | 253 + 273 | 0.864995 | 0.620858 | 0.856752849 | 0.813593 | 0.995038 |
| 1525 | 105 + 253 | 0.889515 | 0.622094 | 0.867806190 | 0.745443 | 0.996488 |
| 1659 | 1386 + 1567 | 1.090414 | 0.602853 | 0.923331501 | 0.896932 | 0.983585 |
| 1626 | 130 + 1536 | 0.991032 | 0.616736 | 0.900943993 | 0.917951 | 0.994856 |

These are real fixed masks, not hypothetical directions. Examples: 641 + 652 is N037/V290 rosemary sourdough with N015/V108 preparing sourdough; 319 + 604 is N014/V104 crockpot beef stew with N092/V826 roast/vegetables in a crockpot; 253 + 273 is non-carnivore pancakes V232 with no-bake pie V776; 105 + 253 uses the pie's vegan/raw V781 instead. The complete larger alternatives are 130 + 1536 (V110 with V232/V781) and1386 + 1567 (V108/V290/V893 with V116/V666/V776). Their content is read, but a lower angle or an intuitive local connection does not by itself rank their full eventual trees.

For photography1080, the degree-factor ratio is 0.779767, overcoming the local-affinity penalty of 1.230425 and producing score ratio 0.959445. The group is less strongly connected to the frozen corpus overall, not more similar on its mean cross angle.

The same arithmetic favors weak1525 over the lower-angle V781/V232 pair: degree-factor ratio 0.745443 × local-affinity penalty 1.336772 = score ratio 0.996488. Its final mean angle is 1.456880 versus 0.889515 for that alternative. Thus lower surrounding degree can favor both a useful visual-practice connection and a weak DCA/chocolate/sleep union. It is not itself evidence of semantic specificity.

## Source-note exclusions materially affect competing pair scores

A winner having rho = 1 does **not** mean exclusions were irrelevant to its choice. Existing competitors can share source notes. M04 omits those pairs from its mean denominator; PARIS has no edge weight there, producing the explicit 1/rho factor.

For each state, select the lowest-angle available alternative that shares at least one endpoint group with the actual merge. All reported alternatives have a lower M04 mean angle. The column D × rho removes **only** that candidate's explicit eligibility-fraction factor, holding its measured original degrees, W and eligible mean affinity fixed. It does not impute excluded angles or describe a valid rerun with edges restored.

| Selected merge | Incident alternative A + B | Alternative k / all pairs | Alternative M04 angle | Actual alternative D | D × rho, factor only | Would this factor-only value beat selected D? |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 1455 | 1076 + 1217 | 12/15 | 1.101737 | 0.939876576 | 0.751901261 | Yes |
| 1080 | 283 + 353 | 1/1 | 1.074704 | 0.838340320 | 0.838340320 | No |
| 1523 | 1324 + 1443 | 2/4 | 1.074986 | 1.681537898 | 0.840768949 | Yes |
| 1426 | 370 + 1312 | 2/3 | 1.060342 | 1.237066551 | 0.824711034 | Yes |
| 1276 | 1057 + 1160 | 4/6 | 1.148214 | 1.131244460 | 0.754162973 | Yes |
| 1469 | 1208 + 1290 | 2/4 | 1.051556 | 1.601385955 | 0.800692978 | Yes |
| 1525 | 1141 + 1257 | 13/15 | 1.246598 | 0.915888519 | 0.793770050 | Yes |
| 1659 | 1549 + 1654 | 26/28 | 1.176360 | 0.976909965 | 0.907130682 | Yes |
| 1626 | 1312 + 1526 | 10/12 | 1.016089 | 1.035714273 | 0.863095227 | Yes |

The explicit fraction changes the selected-versus-alternative ranking in **eight of these nine fixed comparisons**. For example:

- At Christmas1455, the actual pair is V518 with the V426/V545/V748 Christmas child. The alternative joins that child to1217, V306/V425/V543/V747/V841: fireworks, Santa, after-Christmas, Christmas cards and today's-gift material. Three same-note cross pairs are absent, so rho = 12/15. Its factor-only value0.751901 is below the chosen0.849587, but division by0.8 raises its actual score to0.939877. This is partly reunion of already represented notes, not a new-note discovery that was simply lost.
- At activity1276, alternative1057 + 1160 would reunite the gym/workout children through V122/V174/V175/V620 versus V121/V177. N017 and N024 occur on both sides: four of six cross pairs remain. D × rho = 0.754163, below selected0.805909; actual D = 1.131244. The useful walking/stretching extension wins over that available reunion, but the algebra does not establish that every later activity decision would survive a different exclusion policy.
- At weak1525, alternative1141 + 1257 combines V329/V383/V594 with V124/V319/V335/V494/V593—sleep/bedtime plus breakfast, waking, morning time and coffee. Two of fifteen pairs are same-note, rho = 13/15. The factor-only0.793770 is below the weak winner0.864759; actual0.915889 is above it.
- At1659 the effect is small but ranking-relevant: 1549 + 1654 has rho = 26/28. Its factor-only0.907131 is just below selected0.908175, while its actual0.976910 is above. The alternative contains concrete beef, cookware and crockpot masks, but the existing mixed1549 child remains mixed under either parent.

Photography's incident alternative283 + 353 is fully eligible: N016/V111's reluctance to fix eggs with N064/V549's kitchen work/forgotten photos. Its lower mean angle still loses through the original-degree term, with no direct rho penalty.

As a separate check, the globally minimum M04-mean pair at **every** inspected M07 state has partial eligibility: rho = 1/2 for the first eight states through1626, and10/12 at1659. These include duplicated-note bread groups, wine masks and pizza-day masks. Their presence explains why it would be wrong to compare PARIS only with complete-support alternatives, or to call delayed reunion of duplicate variants a lost note-access relation.

## Source-note multiplicity also enters original degree

There is a second, distinct exclusion effect. If source note p has m_p canonical vectors, a vector i from p has exactly c_i = 916 − m_p eligible original neighbors. Therefore:

```text
degree_i = c_i × (mean affinity over i's eligible original neighbors).

mean_degree_A
  = mean_capacity_A × pooled_original_affinity_A,

where mean_capacity_A = mean(c_i for i in A)
and pooled_original_affinity_A = sum(degree_i) / sum(c_i).
```

The second identity is exact; the pooled affinity weights each vector by its eligible-neighbor count. Hence G further decomposes into a capacity product and a pooled-original-affinity product, divided by W. Alias count is not used: the capacities here count canonical vectors.

Capacities range867–915; original weighted degrees range428.188952–536.088321. The chosen groups' lower degree factors are not merely a source-count statistic: for photography, the capacity-product ratio against its full-support alternative is0.965083, while its pooled-original-affinity-product ratio is0.807979. Both multiply to the degree-factor ratio0.779767.

Still, small count effects can matter when competing scores are close. In three of the full-support comparisons above, dividing the selected/alternative score ratio by its measured capacity-product ratio crosses 1:

| Selected merge | Actual selected/alternative score ratio | Capacity-product ratio | Ratio with only capacity-product ratio removed |
| --- | ---: | ---: | ---: |
| 1276 | 0.993691 | 0.976879 | 1.017209 |
| 1469 | 0.995038 | 0.982209 | 1.013061 |
| 1525 | 0.996488 | 0.959596 | 1.038446 |

This establishes a ranking-relevant **algebraic contribution** of the source-size exposure factor in those particular fixed comparisons. It does not show what a graph with restored same-note edges, differently sized notes, or a normalized-degree algorithm would do: those changes would also alter degrees, affinities, competitors and earlier merges. No such algorithm or run is proposed here.

## What this supports—and does not

PARIS uses two additions to pair averaging: total original connection strength and absent-edge fraction. The observed useful and weak/mixed merges both exploit them. Direct source-note overlap penalties favor some new-note unions over overlapping-note reunions; source-note multiplicity also affects original degree. Both can change actual fixed-pair ordering.

Those exact identities and rankings are stronger than a correlation, but narrower than an intervention on the full clustering process. They do not prove the semantic gains were caused solely by degree normalization, that source exclusions explain all weaknesses, or that any factor should be tuned. Original source text remains the basis for semantic judgments.

Only this report was written. No code, inputs, candidate artifacts, titles, tests, commits, cards or other reports were changed.
