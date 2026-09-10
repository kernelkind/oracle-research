# Merge-rule exploration

Goal: find evidence-backed alternatives to HDBv3's single-edge merge rule for broad-to-narrow content discovery. Existing notes, masks, vectors, angular distances, source-note eligibility, and display simplification remain fixed. No generated titles or manual reassignment enter the comparison. This directory is separate from earlier experiments and user-authored notes.

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

**Initial inspection:** Read the first 32 changed cross-note groups, the full masks in M01/1292, /1316, /1337 and /1373, and the original notes needed to interpret the pie/bread/cream examples. Most early changes remain interpretable: coffee, dietary variety, egg-related material, crockpot cooking, and bread ingredients. No semantic titles were generated or used. Complete hierarchy inspection remains in progress; these observations are not an overall pass rate.

**Concrete changed decision:** V777/N083 selects `⟦easter matcha-cashew pie⟧ ⟦no refined sugar⟧`. Its strongest individual connection still points to V355/V356/N045, `⟦Half & half⟧ ⟦ruining my coffee⟧`, with cosine 0.635076. Neither vector changed. In HDBv3 it joins an 81-vector, 30-note group at1270. In M01 it instead pairs with V666/N072, `⟦Irish soda bread⟧ ⟦I tried out recently⟧ ⟦currants aren't in season yet⟧`, at1261. Their cosine is0.595311.

At that M01 decision, the half-and-half vector already belongs to group1259 (42 vectors/19 notes). The candidate score to that whole group is1.016842. The candidate score to V666 alone is0.933144; the current bread-heavy group1242 scores0.962995. Lower scores are merged first. Thus the changed placement comes from group-level evidence, not different embeddings or a hand-moved note. The pie/bread pair is plausible, but broader semantic value still requires inspection; neither mask is a complete baking recipe, and the original pie is explicitly no-bake.

**Preserved useful pairs:** V237/N028 and V663/N072 remain together alone at M01/1151 (baseline1224). V114/N016 and V674/N073 remain together alone at M01/1053 (baseline1076). The half-and-half mask now first pairs with the raw-cream coffee mask at M01/1110. These are specific preservation/improvement candidates, not proof that every changed branch is better.

**Next question:** The normalized rule still produces many one-child levels. The 2026 paper explicitly studies removing normalization. Test that single change next, preserving symmetric aggregation and all other controls. Check whether less chaining merely creates arbitrary small groups, rather than assuming a shorter hierarchy is better.

**Pending:** Complete source-grounded hierarchy inspection, generic merge-history TUI input that preserves inversions honestly, and final candidate comparison.

## Reproduce M01

From the repository root, use a Python environment with NumPy and run:

```sh
python3 sse_multivector/merge_rule_experiment.py \
  --baseline sse_multivector/real-note-fine-segmentation-v1/hdbv3-cross-note-edges-v1/response.json \
  --request sse_multivector/real-note-fine-segmentation-v1/hdbv3-cross-note-edges-v1/request.json \
  --vector-map sse_multivector/real-note-fine-segmentation-v1/vectors/vector-map.json \
  --notes sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json \
  --run-id M01-replay \
  --output /tmp/M01-replay.json
```

The runner refuses to overwrite an existing output. Compare `merges`, IDs and source checksums; run ID, source-code hash and elapsed time are provenance rather than membership output.
