# Internal variation and endpoint coverage

## What M08 leaves open

Conditioning expected connections changed meaningful and weak groups together. M08 does not dominate M07 or M06. Merely fitting another normalization is not the only informative next step. The next research question was whether a proposed union should be judged against variation already inside its children, rather than only their cross-group average.

The frozen source-note exclusions matter mathematically. They are not measured infinite distances, observed zeros, or a random sample of missing observations. An adaptation must say exactly how it uses them.

## Energy and generalized Ward

Székely and Rizzo's between-within criterion subtracts each group's internal average distance from twice its cross-group average, with a size factor. Their complete-distance method distinguishes distributions, not just centers. Dermatology and gene-expression results outperform ordinary Ward at the reported reference cuts, but performance varies with the chosen cut and simulation geometry. Their missing-age treatment reconstructs rescaled distances from available features; it does not omit arbitrary pairs. Methods pp153–156 and results pp165–166/169 were read directly from the scanned paper.[^1]

Lyons establishes negative type for angular distance on spheres, and strong negative type when there is at most one antipodal pair. Thus complete, unsquared angular distances are not automatically an invalid input to an energy criterion. This theorem does not apply unchanged after source-dependent pair omissions. The theorem and its proof were read directly.[^2]

**Definition check, not a corpus failure:** put four distinct vectors on the unit circle at the following angles, all in one open hemisphere:

| Group | Source P | Source Q |
| --- | ---: | ---: |
| A | 0 | 1 |
| B | 1.1 | 0.1 |

The complete cross distances are1.1,0.1,0.1,0.9. Same-source exclusion removes1.1 and0.9. Each within-group off-diagonal distance is1.

The paper's complete expression is `2 × cross mean − within-A mean − within-B mean`, with ordered within-group means including the zero diagonal. Its size factor is1 here. Exact arithmetic gives:

- Complete distances: `2 × 0.55 − 0.5 − 0.5 = 0.1`.
- Drop the two excluded terms but keep original denominators: `2 × 0.05 − 0.5 − 0.5 = −0.9`.
- Renormalize every mean over eligible non-self pairs: `2 × 0.1 − 1 − 1 = −1.8`.

Both proposed omissions lose the original nonnegativity result. These fixed groups are a definition counterexample, not a claim that a greedy corpus run forms them. They do not prove that every possible exclusion-aware energy method is invalid. Restoring same-note distances or choosing an imputation model would change additional controls, so neither is silently added.

## Minimax linkage

Bien and Tibshirani measure a proposed union by the smallest covering radius around one of its actual members. Their complete-distance method has monotonicity and duplicate-invariance properties; word-cooccurrence and face examples illustrate prototypes. Simulated results depend on whether the true number of groups or the best retrospective cut is used. A representative point is not automatically a broader subject. Methods §§2–4 and examples/results §§5–7 were read directly.[^3]

Omitting a prototype's same-note distances would remove its guarantee of covering the whole union. Treating those missing distances as infinite instead could make every potential prototype inadmissible when every source is represented more than once. This is a different missing-evidence problem, not a ready replacement for M08.

## Next controlled candidate: M09

The research also identifies an established alternative that does not require internal-distance subtraction or one shared prototype: Hausdorff linkage. Basalto et al. use the largest nearest-partner distance in either direction. Their synthetic and stock examples compare actual tree structures and acknowledge reversals. Some synthetic conclusions use a visually chosen cut and input tie order, so these are not general semantic-navigation guarantees. Methods §IV and results §V were read directly.[^4]

**Question:** Does M01's averaging allow a merge despite one poorly matched supported endpoint? Test the literal maximum of the same endpoint distances instead. This follows the evidence about mixed unions; it does not assert that every current failure has that cause.

For every vector in A, find its nearest eligible vector in B. Do the same from B to A. As in M01, omit endpoints with no eligible partner and record their counts. Take the maximum of all remaining distances from both directions. A group pair with no eligible cross edge remains inadmissible. Select the global minimum with the existing ID tie order.

Call this **finite-support Hausdorff**, rule `hausdorff_finite`. It is an explicitly adapted linkage, not a claim that the incomplete relation satisfies the Hausdorff metric axioms. It is not the maximum of directional means, not the largest distance among all cross pairs, and not minimax prototype radius.

This isolates endpoint aggregation while keeping M01's partners and omission policy. With a singleton, it equals the maximum eligible distance to the other group. With two multi-vector groups it can use different partners for different endpoints. It can therefore penalize an unmatched meaning without requiring every meaning to resemble every other one. It can also reject useful broad or unusual material; literal maximum sensitivity is a risk, not a presumed advantage. Omitted endpoints have no coverage guarantee.

Before running the corpus, add failing production-path tests for the exact finite row/column minima, unsupported endpoints, singleton behavior, global ties, actual angular reversals, monotone transformations and complete histories versus exhaustive recomputation. Preserve all earlier tests and replay all saved artifacts. No score flattening, distance change, new threshold, source reassignment or title generation.

Inspect the complete M09 hierarchy bottom-up, preserving the same alternate-mask relation checks. Examine new groups beyond those checks, and trace actual fixed-child endpoint scores where a change appears useful or harmful. Shorter trees, reunified variants and the number of surviving groups are not semantic verdicts. The allowance check before this candidate returned45%;30% remains the wrap-up signal.

## Sources

[^1]: Gábor J. Székely and Maria L. Rizzo (2005), *Hierarchical Clustering via Joint Between-Within Distances: Extending Ward's Minimum Variance Method*. [Primary paper](https://home.ipipan.waw.pl/j.mielniczuk/Szekely-Rizzo_2005.pdf).
[^2]: Russell Lyons (2020), *Strong Negative Type in Spheres*, Theorem1.1 and §2. [Primary paper](https://arxiv.org/pdf/1905.02863).
[^3]: Jacob Bien and Robert Tibshirani (2011), *Hierarchical Clustering With Prototypes via Minimax Linkage*. [Author's paper](https://faculty.marshall.usc.edu/jacob-bien/papers/jasa2011minimax.pdf).
[^4]: N. Basalto, R. Bellotti, F. De Carlo, P. Facchi, E. Pantaleo and S. Pascazio (2008), *Hausdorff Clustering*, Physical Review E78,046112. [Author's paper](https://home.ba.infn.it/~facchi/papers/75%20hausdorff2.pdf).
