# Surrounding connections in merge decisions

## Question

M01 through M06 assign the same ordinary distance to any eligible singleton pair. Their later group scores differ, so they can create different early pairings by changing which partners remain available. M06's useful lunch pair1568 and weak cooktop/corner pair1601 demonstrate this distinction: neither pair's own score changed.

Would judging a connection relative to the groups' connections to the rest of the corpus produce more useful nested memberships? This asks about an additional kind of geometric evidence, not another average/median setting. It does not presume that the current vectors contain enough evidence to repair every weak pair.

## Literature and source inspection

Bonald et al.'s PARIS takes a nonnegative weighted graph and minimizes `s(A) × s(B) / (W × w(A,B))`: `s` sums original vertex degrees, `W` is total degree and `w` sums cross-group edge weights. Degree mass includes connections outside the proposed pair. Additive updates give a reducible full hierarchy; a nearest-neighbor chain can accelerate exact selection. The authors evaluate hierarchical synthetic graphs, real link networks and whole-tree Dasgupta cost. Qualitative Wikipedia examples report selected high-degree pages, not exhaustive semantic judgments. This is promising evidence for a contextual merge criterion, not proof of note-discovery quality.[^1]

The authors' implementation preserves accumulated degree mass through merges and sums connection weights. Recomputing a group's degree from only its remaining external edges would implement a different rule. Its graph-copying and NetworkX nearest-neighbor chain are unnecessary for this small dense input; the existing exact global heap can implement the same score and preserve our deterministic tie policy.[^2]

## M07 definition before running

Use PARIS with a declared linear conversion of the **existing frozen angular distances**, not new embeddings or recomputed distances:

- Each existing eligible edge has weight `1 − angle / π`.
- Existing excluded edges and self-edges remain absent.
- Each vector's degree is the sum of its edge weights. Each group's degree mass is the sum of its vectors' original degrees, including connections that have become internal.
- Score a candidate pair by the formula above. Merge the globally smallest current score, preserving all children and existing tie order.
- Keep note projection, aliases, note text, masks, vector memberships and unsupported-endpoint reporting unchanged. Do not also apply M06's source-note-pair weights.

The affinity conversion is our experimental choice, not prescribed by the paper. It uses no fitted bandwidth, neighbor count or cutoff. It retains every currently eligible edge: the saved angles range from0.113397707 to1.889571792, so all412,379 eligible weights are positive, from0.398530618 to0.963904389. An eligible angle at or beyond π must be rejected for this rule rather than silently deleting an edge or adding an arbitrary epsilon.

This is not a pure degree-normalization substitution into M04. PARIS also treats absent connections as absent graph evidence, while M04 omits them from its mean's denominator. Both use the same allowed edges, but aggregate their absence differently. Its contextual information is total connection strength, not the identity or agreement of shared neighbors.

## Pre-run checks and risks

The initial singleton scores genuinely change. Only17 of the50 strongest angular pairs remain among the50 strongest PARIS pairs. The first PARIS choice is V185/N024 with V379/N048, both selecting `bitcoin`, at angle0.122235655 and score0.483236051. The original smallest angle is V090/N012 with V242/N029, both selecting `Bitcoin`, at0.113397707; its PARIS score is0.503115951. These are initial scores, not a completed hierarchy or a semantic improvement claim.

The frozen artifact has1–49 canonical vectors per source note. A constant-weight control exposes a potential bias: with the same exclusions, a vector from a note containing `m` vectors has degree `916 − m`. Its PARIS singleton score therefore depends on source-note size even when all eligible edge weights are identical. Degrees would range867–915. In the actual graph, weighted degrees range428.188952–536.088321. Neither range establishes semantic harm, but source-note multiplicity is not corrected automatically by this rule.

Every retained edge has substantial positive weight under the linear conversion. Large numbers of weak connections can therefore affect the degree totals. Conversely, lowering the scores of less generally connected material may help separate specific subjects from broadly connected food material. These are competing hypotheses, not reasons to tune the conversion after viewing results.

## Verification and inspection

Before implementation, add tests for the actual score, outside-pair influence, preserved internal degree mass, excluded edges, deterministic global selection, the constant-edge source-size effect, and invalid affinity inputs. Compare every merge against independent exhaustive calculations on small angular inputs. All previous tests and six saved histories must remain unchanged.

Run one full M07 on the frozen artifact. Preserve raw scores and verify the production nested viewer. Inspect changed memberships bottom-up, including the established useful relations and new groups outside them. Admit relevant alternate masks before claiming note-discovery gains or losses. Do not call shorter trees, monotonic scores, or lower graph cost semantic success.

## Sources

[^1]: Thomas Bonald, Bertrand Charpentier, Alexis Galland and Alexandre Hollocou, *Hierarchical Graph Clustering using Node Pair Sampling* (arXiv v2,22 June2018), §§3–7. [Paper](https://arxiv.org/html/1806.01664v2). The HTML page's2026 rendering date is not the paper's publication date.
[^2]: Authors' PARIS implementation, especially degree initialization and additive updates. [Source](https://raw.githubusercontent.com/tbonald/paris/master/paris.py).
