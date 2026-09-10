# Excluded connections in the merge rule

## Question

M07 treats same-note connections as absent observed graph weight, but its independent-endpoint expectation still assigns weight to those pairs. The [nine-state score diagnostic](audit-M07-score-factors.md) shows that this changes available partner rankings. Does excluding these pairs from the expectation, while keeping the original strength factors, improve the resulting note-discovery hierarchy?

This is a controlled comparison with M07, not a claim that exclusions caused all its weaknesses. Same-note pairs remain unavailable. No embeddings, masks, notes, angular distances, affinity conversion, original strengths, or display rules change.

## Research

Barber's bipartite modularity explicitly excludes forbidden pairs from the null model. Otherwise, placing two vertices from the same part together incurs an automatic negative contribution. Its degree-preserving closed form depends on two parts with equal total degree; it cannot be copied unchanged to our 100 unequal source-note parts. BRIM's real-network results also depend on initialization and allowed module count. This supports respecting eligibility, not a claim that modularity optimization would produce our desired full hierarchy.[^1]

Aicher, Jacobs and Clauset distinguish an observed missing edge, an observed zero weight, and an unobserved interaction. The last contributes no likelihood term. Their NFL example separates schedule-driven groups from score-driven groups; cross-validation compares edge and weight prediction. Our source-note exclusions similarly arise from the experimental design, not observed semantic dissimilarity. Their block model introduces distribution, group-count and mixing choices that we need not add to test this one mechanism.[^2]

Saracco et al. restrict their binary ensemble to eligible bipartite pairs, then fit parameters to reproduce expected degrees. Their results capture some trade-network structure but leave higher-order deviations unexplained. Restricting an existing degree product and fitting a new degree-preserving expectation are therefore distinct operations. The binary likelihood is not a distribution for our continuous affinities.[^3]

These methods and results were read directly. M07 already inspected the PARIS authors' implementation and its additive updates in [the preceding research record](surrounding-connections.md). No cited paper establishes the exact variant below as a validated semantic-hierarchy method.

## M08 definition before running

Use the original canonical-vector graph. Let `E[i,j]` be one for an existing eligible pair, zero otherwise, including the diagonal. Keep `w[i,j] = 1 - angle[i,j]/π` on eligible pairs and zero otherwise. Let `s[i] = sum_j w[i,j]` and `W = sum_i s[i]`.

Condition independent endpoint draws on eligibility:

```text
Z = sum_i sum_j E[i,j] s[i] s[j]
q[i,j] = E[i,j] s[i] s[j] / Z
p[i,j] = w[i,j] / W

D08(A,B) = q(A,B) / p(A,B)
         = (W/Z) × sum_eligible_cross_pairs s[i] s[j]
                    / sum_cross_pairs w[i,j].
```

Both distributions sum to one over ordered pairs. Each cross-group sum counts the A-by-B block once. A pair of groups without eligible connections remains inadmissible; `0/0` is not a merge score. Merge the global minimum with the existing ID tie order. Keep both original pair matrices fixed and add their cross-group sums on union.

This changes the support of the expected distribution only. It does **not** preserve its endpoint marginals: a source note's strength mass affects the probability of an eligible partner. It also does not remove the effect of source-note size on original strengths. A fitted-strength model would change those factors and potentially the first merge as well; that would be a different experiment.

For every eligible singleton pair, `D08/D07 = W²/Z`, a common constant. Thus singleton ordering is mathematically unchanged, while groups sharing source notes can change relative order. Global normalization changes score units, not the hierarchy. Updated scores are observed-cross-weight averages of the two previous scores, so global-greedy merge heights are nondecreasing. These are algebraic properties, not semantic predictions.

## Verification and interpretation

Before implementation, test the masked expected numerator, ordered normalization, original-strength preservation, singleton ordering, non-preservation of marginal strengths, same-note exclusions, disconnected inputs, exact ties and complete histories against independent exhaustive calculations. Use synthetic arithmetic checks, not semantic fixtures designed to force preferred corpus groups. All previous tests and saved histories must remain unchanged.

Run the full frozen input once as M08, retaining M07. Verify the production nested viewer, then inspect the complete hierarchy bottom-up using all original masks and context. Compare established relations with the same generous alternate masks, and inspect new groups beyond those relations. Separating variants of one note or reuniting them is not by itself a discovery loss or gain. A more focused branch, a weak addition, or a missing relevant extension requires source evidence.

If M08 changes the desired and undesired groups together, do not interpret that as a universal correction. The experiment asks whether this explicit treatment of exclusions is useful under the frozen representation; no passing semantic result is guaranteed.

## Initial result and mechanical checks

M08 completed in 1.42 seconds with all 916 canonical vectors, 945 original IDs and 100 notes. Raw maximum depth is 31, with no score inversions and 370 merges containing an unsupported endpoint. The unchanged production viewer loads 502 groups, maximum displayed depth 20 and 117 one-child groups. These measurements do not establish semantic quality.

All six new tests failed before implementation because the rule did not yet exist; all 31 merge-rule tests now pass. Independent implementation review also compared 140 sparse-angular merges against exhaustive calculations and checked complete-graph score rescaling. All eight saved full 915-merge histories, aliases, canonical IDs and frozen input provenance replay exactly after the addition. M07 remains preserved at commit `d0349d5d`; its saved source hash correctly refers to the earlier source version.

The first 12 merges choose identical children in M07 and M08. At merge 928, both runs therefore still have the same available groups. M07 chooses V310's `⟦GM⟧ ⟦siamstr⟧` with the V914/V541 greeting child. M08 instead joins V450's `⟦Bitcoin workshop conducted⟧` to an existing six-note Bitcoin group that already contains V451's `⟦Bitcoin workshop⟧` from the same N055 note. The fixed alternatives score as follows:

| Available pair before 928 | M07 score | M08 score |
| --- | ---: | ---: |
| V310 + greeting child 921 | 0.582647528 | 0.592364811 |
| V450 + Bitcoin child 925 | 0.684544301 | 0.581507604 |

The same-note V450/V451 pair is excluded in both observed graphs. Removing its expected contribution reverses this partner ranking under M08. The greeting alternative has disjoint note sets, so its change is only the common normalization factor. This is an exact first-divergence explanation, not proof of improved discovery: adding V450 does not introduce another note to the Bitcoin group. The unchanged originals and all masks for these children were read; no linked content was used.

Complete inspection is recorded in [A](audit-M08-complete-A.md), [B](audit-M08-complete-B.md), and the [connecting parents](audit-M08-upper.md). Of 915 transitions, 331 have exact recursive matches in previously audited M04/M06/M07; 584 are changed. The 64 disjoint new reading subtrees contain 873 canonical vectors and 809 transitions; 23 inherited subtrees/singletons contain 43 canonical vectors and 20 transitions. Their 86 connecting parents complete the tree. This division is only a reading aid and does not modify the hierarchy or certify its semantics.

The [same 13 relation checks](audit-M08-relations.md) find mixed results. Tea and restaurant access survive; the full tomato extension becomes more focused than M07, though some additions remain weak. Photography separates again, food-over-time access requires broader ancestors, and concrete preservation broadens while retaining the same vacuum-sealer/grab-bar weakness. Christmas remains available with additional generic gift material. The source evidence supports these specific tradeoffs, not a universal correction or an overall winner.

The remaining distinction is important: M08 corrects expected support but does not fit expected strengths. That is a possible further null-model question, not an automatic next experiment. Other research may be more informative if it examines a different source of grouping evidence. The allowance check after this audit returned 46% remaining; final candidate packaging is still pending.

## Sources

[^1]: Michael J. Barber (2007), *Modularity and community detection in bipartite networks*, §II, Eqs. 5–15, and §§III–IV. [Paper](https://arxiv.org/html/0707.1616). Its later HTML rendering date is not the publication date.
[^2]: Christopher Aicher, Abigail Z. Jacobs and Aaron Clauset (2015), *Learning Latent Block Structure in Weighted Networks*, §§2.1–2.2 and 4.1–4.2. [Paper](https://arxiv.org/html/1404.0431v2).
[^3]: Fabio Saracco, Riccardo Di Clemente, Andrea Gabrielli and Tiziano Squartini (2015), *Randomizing bipartite networks: the case of the World Trade Web*, Methods Eqs. 15–19 and Results on assortativity and motifs. [Paper](https://arxiv.org/html/1503.05098v2).
