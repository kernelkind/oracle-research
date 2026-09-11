# Following the diffusion evidence

GDC09 is the strongest candidate from this investigation. Keeping moving vectors at unit length produced useful intermediate memberships missing from the earlier Euclidean run. The completed result still contains weak joins and redundant levels; it is not a finished navigation hierarchy.

All fits use the same 916 canonical vectors, 945 preserved mask aliases, 100 notes, and 768 original dimensions. No subjects, masks, source notes, or semantic labels were changed. No new model calls or TUI were used. GDC02 remains the unchanged Euclidean baseline. Configuration, exact masks, full notes, native tree, and final coordinates are retained for every run.

## What the motion trace established

N045 complains that half-and-half is ruining the author's coffee. Its V356 mask is `⟦Half & half⟧` and `⟦ruining my coffee⟧`. The old run did not join it to the 18-note coffee group until a parent containing 81 notes. N058's V494 mask is `⟦coffee⟧ ⟦hot⟧ ⟦this AM⟧`; its corresponding parent contained 89 notes. Both already had nearby coffee vectors in the original geometry. Their complete notes and original comparisons are in the main README and `original-neighbors.json`.

GDC02S is an observational replay: every native node and final coordinate matches GDC02 bitwise. It saves47 coordinate snapshots. `motion.json` reconstructs observed updates and distinguishes averaging weight from signed contribution to motion. Reference sets are retrospective accounting sets, not categories supplied to fitting.

Three mechanisms were measured separately:

1. **Density correction changes which neighbors exert influence.** Initially, V356 is almost equally distant from a fetching-coffee vector and a coffee-with-raw-cream vector:0.805955 versus0.806747. The less densely surrounded destination receives5.26 times the averaging weight. This follows from the actual row-normalized formula: destination weight is proportional to Gaussian affinity divided by destination degree. It is not a claim that the closest single neighbor determines the outcome.
2. **Vectors shrink as well as change direction.** The median norm drops from1 to0.4323 at step32 and0.3438 at40. For V494 and a coffee-preparation vector, step32 affinity is0.672347; normalizing those same directions before measuring the kernel gives0.082252. Shrinking radii make fixed-width Euclidean neighborhoods effectively broader, without requiring equivalent angular convergence.
3. **Numerical merging records very late proximity.** At step32, V356 and the successful coffee vector are already0.019404 apart, with Gaussian affinity0.997054 and nearly identical averaging distributions. The merge threshold is only0.0001. This justified testing the readout separately, not assuming it caused the semantic problem.

## Controlled changes and their consequences

| Run | Single change from its stated control | What was learned |
| --- | --- | --- |
| GDC04 vs GDC02 | Density normalization1→0 | N045 joins a19-note coffee group. N058 loses a useful morning intermediate; some meal/sleep distinctions worsen. Reweighting matters, but removing it is not a general fix. |
| GDC05 vs GDC02 | Merge tolerance0.0001→0.0358139 | Records unions earlier, without changing coordinate motion. Coffee membership remains the same18-note core; missing intermediates are not generally repaired. |
| GDC06 vs GDC02 | Normalize every updated vector to unit length | Restores N045 and adds genuine diet, sleep/routine, kitchen, and garden intermediates. It is still moving at its2,000-step bound. |
| GDC07 vs GDC06 | Density normalization1→0 | Preserves local coffee; adds useful shrimp, bread, steak groupings; loses some planning, egg, and sleep-to-morning distinctions. Different useful arrangements, not one universal winner. |
| GDC08 vs GDC06 | Initial epsilon×1.25 | Exact diet-quality, sleep/tiredness, daily-routine, and Bitcoin-facet memberships survive. Other subdivisions change. Partial robustness, not a parameter-invariant taxonomy. |
| GDC09 vs GDC06 | Iteration bound2,000→8,000 | Completes at3,480 steps. The first2,000 history entries, all prefix nodes, and coordinates at2,000 match GDC06 exactly. Additional useful knowledge/writing parents appear; late weak joins remain. |

GDC09 increases epsilon under the existing degree-change rule at steps3,221 and3,479. The run stops once every vector belongs to the same recorded group. This computational completion is not a claim that the root or every intermediate node is a meaningful category.

The unit update has direct precedent in blurring directional mean shift: average neighboring directions and normalize before repeating. The authors' implementation replaces all source positions at each step. Our density correction, quarter-step relaxation, cumulative unions, and bandwidth rule remain explicit adaptations, not a published semantic-hierarchy guarantee. [Zhang and Chen, Appendix A.3](https://jmlr.org/papers/v22/20-1194.html), [pinned author implementation](https://github.com/zhangyk8/DirMS/blob/9a9fd6754a3eec0bf7eba7260a268fb3dbf67112/DirMS_fun.py#L209-L228).

## Useful paths in the completed GDC09

The following descriptions are human analysis of saved evidence, not generated node titles or fitting inputs. Arrows point upward. Intermediate nodes are sometimes omitted from these short summaries; `path-evidence.json` preserves each complete chain and the full evidence needed to reconstruct every node.

**Coffee → coffee/tea → food/drink.** Node1487 contains41 vectors from19 notes, including N045. Later1580 adds N072's sweet-tea material, and1598 adds N042/N080 tea, reaching22 notes. Node1609 combines that branch with a65-note food branch, giving82 distinct notes. Food/drink is a defensible broadening;82 is not itself an error. Some intervening nodes add additional masks from already represented coffee notes, not new note-discovery choices. N072 also contributes a recipe-variation mask, so the boundary is not perfectly clean.

**Sleep → tiredness/caffeine → daily routines.** Node1533 contains sleep-related masks from N041 and N069. Node1557 adds N034's tiredness/caffeine,1562 adds N043's physical/mental effects of remaining at a desk,1571 joins morning routines, and1574 reaches12 notes. Much later1680 contains18 notes covering a broader range of daily experiences. It must not be presented as18 sleep notes.

**Cookware → kitchen equipment.** Node1492 contains N056's cookware material. Node1636 adds N044's knife/fork,1659 adds N001's rocket stove, and1671 adds N027's induction hob and N100's vacuum sealer. The five-note parent has a recognizable equipment relationship. In GDC02, the smallest node containing N056,N027,N100 already had91 notes; GDC08 also preserves a four-note equipment parent. These comparisons check every note union, not just one chosen mask.

**Literature/audiobooks → knowledge/education → writing.** Node1661 contains N054 and N080. Node1693 adds N055 and N069;1700 adds N043, giving five notes. These parents arise after step2,000, so the earlier unfinished result could not show them. GDC08 independently contains the same five-note set. GDC02 needs an81-note parent to contain those five source notes.

**Gardening/homesteading.** Node1629 groups N022's garden beets, N031's allotments, and N100's homesteading. Their smallest common note parent had55 notes in GDC02. GDC08 preserves the same three-note set. N031's vague `allotment efforts` mask remains an earlier acknowledged extraction weakness; the complete note supplies the gardening context. This must not be counted as proof the mask alone is sufficiently descriptive.

These are real additions beyond the originally examined coffee branch. They do not establish one uniquely correct hierarchy or corpus-wide accuracy. The audit read all100 full source-note texts, selected complete paths, all exact fragments of new post2,000 groups with fewer than50 notes, and the inspected broader food branches. It did not independently certify every possible node.

## Remaining concerns, with representation separated from grouping

**N058's hot-morning-coffee meaning still follows morning context.** In the unit trajectory its affinity to V503 coffee preparation falls from0.010020 initially to0.000296 at step32. The same mask initially has nearly tied coffee and greeting alternatives. Keeping lengths fixed does not force the intended coffee interpretation, and density normalization changes which interpretation wins. Its first common note parent with the N045/N060 coffee pair has98 notes in GDC09. The evidence supports a remaining coverage gap, not the claim that sphere normalization solved all contextual competition.

**Chocolate is not reliably connected.** N081 says:

> Added a few #gianguja jars to the store. Just out of the melanger! https://yabisi.farm/index.php/product/macambo-gianduja/
>
> #foodstr #grownostr #craftchocolate

Its five masks end in a group with greetings and Gentoo, eventually reaching other chocolate notes only through a99-note parent. However, the original geometry is already problematic: `⟦gianguja jars⟧ ⟦store⟧` has cosine0.556752 to `⟦Gm nostr⟧`, while its best vector from N016's chocolate-eating note scores0.158867. The mask containing `⟦gianguja⟧ ⟦craftchocolate⟧` has stronger food connections, including N016 at0.489519, but coffee, cake, and greetings compete. This is not a clean algorithm-only failure; spelling/domain knowledge, mask content, and frozen geometry may all contribute. No extraction was changed to rescue it.

**The storm note lacks a useful shared weather parent.** N039 says:

> Well the parade was rained out and umbrellas were ruined.
>
> Next rounds of storms look like they will hit just in time for grilling out dinner.
>
> Third round is scheduled for when we are supposed to have fireworks.

Its nine-mask storm/parade/fireworks group1686 joins `⟦alby⟧`, `⟦#DCA⟧`, and `⟦Apocalypse⟧` at1751, then nearly immediately reaches the corpus root. Those other complete notes do not supply actual storm accounts. Searching every note union finds N039 together with N058's cold morning and N080's frosty sunrise only at a98-note parent.

Again, the input matters. The exact mask `⟦Next rounds of storms⟧` scores only0.157403 against its best N058 vector and0.134908 against its best N080 vector; a brain-fog mask is its closest other-note neighbor at0.271418. Another mask containing storms and grilling dinner is much closer to meal preparation,0.715740. The missing weather category is a content-discovery limitation of this frozen pipeline, not isolated evidence that a different merge rule would recover it. `remaining-original-neighborhoods.json` retains every checked target, requested note comparison, and nearest distinct-note masks.

**Many levels still do not describe a new interest.** A larger set of food notes is not automatically a broader semantic category. Repeated note sets and successive additions of examples remain prominent. Removing such levels would be a separate readout decision; no pruning or generated titles were used to conceal them here.

## Does cumulative merging hide later separation?

The paper explicitly enforces cumulative unions because proximity at one time does not guarantee continued proximity. Our code therefore must not imply that permanent tree membership is a proven geometric permanence property. [Huguet et al., Section5.2](https://arxiv.org/html/2203.14860#S5.SS2).

The saved-snapshot check found one temporary disconnection in GDC02S/1331: its six vectors split into two connected sets at steps49–54. Maximum spread was0.0002264, versus the0.0001 recording threshold—still tiny relative to the kernel width. No disconnected previously recorded group was observed in the26 saved GDC09 snapshots through step3,000. The maximum recorded-group spread over all checked snapshots/runs was0.0006056. These sparse observations do not prove every-step permanence, but they do not support treating later separation as the cause of the unit run's remaining semantic weaknesses.

`continuation-analysis.json` also verifies the GDC06 prefix and tracks the original coffee targets. In GDC09, V356 moves into the existing coffee group while it is still locally distinct: at step64, the baseline coffee rows receive0.8151 of its averaging weight. In the Euclidean baseline at the same step, coffee, food, and morning coordinates have already become nearly indistinguishable. The change is more than simply adding iteration numbers to the same hierarchy; the intermediate memberships differ.

## FMC native memberships: a separate limitation

Further inspection of the saved fuzzy matrices found that independently selecting each vector's largest membership at every level does not produce nested partitions. In GFM01, level5→6,78 child groups include22 whose vectors select different next parents. Even the best single-parent assignment for every whole child must disagree with141 of916 next-level winners. In GFM02, level7→8, the corresponding unavoidable minimum is218 of916.

This is a conversion conflict, not a numerical implementation bug or proof that the fuzzy memberships lack meaning. For GFM02 row568, its old preferred branch passes its entire0.082658 contribution to the next coffee node. Contributions from other branches increase that destination's total membership to0.094252, but a different parent reaches0.098297 and becomes the winner. The old contribution did not disappear. No new hard projector was invented here; native arrays and the earlier conversion stay frozen.

## Does longer persistence identify better levels?

The final diagnostic makes no changes to the tree. It measures how long a group remains unchanged before gaining another note. Adjacent nodes containing exactly the same notes count as one interval for this measurement, even when additional masks arrive. The root has no measured end. All durations below use GDC09's clock; they are not comparable confidence scores across different update schedules.

| Saved group | Distinct notes | Iterations before the note set changes | Evidence-based interpretation |
| --- | ---: | ---: | --- |
| 1401 | 4 | 2 | Diet quality: processed food, diverse diets, and choosing better food. |
| 1419 | 2 | 1 | Meal planning and packing a lunch box. A defensible connection, despite its short duration. |
| 1487 and its equal-note parents | 19 | 129 | Coffee. Node 1487 alone lasts only 8 iterations; subsequent masks initially add no new notes. |
| 1598 | 22 | 53 | Coffee and tea. |
| 1671 | 5 | 780 | Kitchen equipment. |
| 1693 | 4 | 818 | Knowledge and education, including literature. |
| 1665 | 7 | 2,287 | Greetings, Gentoo, and gianguja/chocolate masks. Long duration does not repair this questionable combination. |
| 1751 | 4 | 1 | Storms alongside alby, DCA, and Apocalypse. A weak late join. |

The masks behind the two most direct counterexamples are concrete. The short-lived 1419 contains `⟦I gotta start meal planning⟧` and lunch-box fragments such as `⟦Packing⟧ ⟦lunch box⟧ ⟦food⟧`. The long-lived 1665 contains `⟦GM⟧`, `⟦Gentoo⟧`, and `⟦gianguja⟧ ⟦craftchocolate⟧`, among their overlapping variants. Its full-note and original-neighborhood limitations are discussed above. There is no demonstrated semantic-quality ordering in which merely lasting longer makes the second group preferable.

Checking the 20 longest-lived multi-note sets also found both recognizable relationships, such as anxiety/stress and visual art, and questionable mixtures, such as Sorrento tourism with satoshi references. These were inspected after ranking, unlike the preselected examples in the table; they are additional observations, not an independent validation set.

The literature supports examining time between merges, but does not turn it into semantic confidence. CUTS uses unchanged-segment duration for image segmentation; Multiscale PHATE instead selects scales from global motion. Neither establishes an automatic nested selector for these note vectors. Our equal-note-set measurement is additionally distinct from both methods' original observation identities. [CUTS, Methods](https://papers.miccai.org/miccai-2024/paper/1569_paper.pdf), [Multiscale PHATE, Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC10015653/).

Conclusion: raw node duration can misrepresent stability at the note level, and note-set duration alone is insufficient to judge meaning. No persistence threshold, pruning, or new ranking was adopted. `note-set-duration.json` retains every measured interval for GDC02, GDC07, GDC08, and GDC09; `code/check-note-set-duration.py` reproduces the calculation from their unchanged trees.

## Reproducibility and handoff

- `GDC09` is the complete strongest directional candidate. `GDC07` is the useful alternative without density correction. `GDC08` is a bounded bandwidth robustness comparison, not a converged result.
- `GDC02S/motion.json`, `GDC09/continuation-analysis.json`, and `GDC09/remaining-original-neighborhoods.json` preserve the numerical diagnoses. The diagnostic source scripts are in `code/`.
- `note-set-duration.json` records the final level-selection diagnostic. It does not alter or filter any result.
- `path-evidence.json` stores complete chains for the discussed interests, exact masks, and full original notes. Existing `geometric_experiment.py inspect RUN NODE --full-notes` remains a read-only inspection interface. After the investigation, the user requested UI viewing: `../run-diffusion-hierarchy.sh` now loads the unchanged GDC09 memberships into the existing nested-mask viewer. See the main README for its display rules and controls; no new TUI or semantic labels were generated.
- Source archives and `provenance.json` preserve code and artifact hashes. Observation NPZ caches stay local and Git-ignored; configuration and checksums make them reproducible. No baseline output was overwritten.
- The production regression suite passed73 tests. After the optional unit-sphere feature was added, default Euclidean fitting reproduces GDC02's first558 steps of nodes and GDC05's final coordinates. Separately, the unchanged GDC02S observational replay matches the complete archived GDC02 tree and final coordinates.

Conclusion: the original-vector geometry can support more useful nested note relationships than the first runs exposed. Unit-sphere motion is the best demonstrated improvement here. Complete semantic navigation, reliable coverage across interests, and automatic selection of useful levels remain unproven. Those limitations are not interchangeable, and another isolated cosine or one attractive flat group cannot settle them.

## Justified next experiment, not performed here

Replicate the Euclidean-versus-unit-sphere comparison on a separately selected dense corpus from a different broad semantic area. Freeze its masks and vectors before fitting, retain the bandwidth-selection rule and other settings, and compare complete paths without prescribing the categories that should emerge. This directly asks whether the directional improvement generalizes beyond the repeatedly inspected food-heavy corpus. It is a separate proposed experiment, not authorization to change this corpus or start another extraction run.

GDC09 and GDC07 are packaged as the strongest inspected candidate and a useful alternative, not certified winners. More tuning on this same corpus, or hiding its weak levels using a lifetime cutoff, would not answer that generalization question. The investigation can therefore conclude without consuming the remaining allowance merely to reach the 70% wrap-up signal.
