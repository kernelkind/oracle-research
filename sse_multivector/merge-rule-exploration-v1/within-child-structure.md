# Within-child structure after M09

M09's two fixed-child comparisons show that taking the worst endpoint can reject an otherwise useful connection. This does not imply that another percentile is the answer. The next research question was whether a proposed connection should instead be judged against the structure already inside its children.

## What CHAMELEON contributes

Original CHAMELEON compares cross-group edge weight with a balanced minimum cut inside each child. Its closeness term compares the mean cross-edge weight with the means on those internal cuts. The product-based scheme used in its experiments selects the next merge through their product, with an adjustable exponent. It also describes a threshold-based scheme. Internal cut edges are explicitly different from all internal edges or the child's historical final merge.[^1]

The original starts with a nearest-neighbor graph and graph-partitioned seed groups. Section4.4 says small groups cannot reliably supply its internal statistics. Its five synthetic 2D experiments inspect selected levels recovering the expected clusters, not the semantic quality of every ancestor. Methods §§4.2–4.4 and results §§5.1–5.2 were read directly.[^1]

**Implication for this experiment:** a singleton has no internal bisection. Importing the original requires a seed phase or an additional convention. Changing the graph to nearest-neighbor adjacency also changes which missing connections mean “not neighbors”; our missing connections currently mean “same source note.” These are substantive additional choices, not an interchangeable merge formula.

## Ch2 has materially different definitions in circulation

Chameleon2++ v1 describes a Ch2 rule using internal edge counts and weight means rather than repeated balanced cuts. The cross mean is divided by a pooled internal mean; a cross/internal edge-count factor and ratio of internal means also enter. Its stated edge-free-child formula leaves a zero denominator when both children have no internal edges. The full2019 Ch2 paper was inaccessible, so these details are attributed to the successor's explicit equations, not presumed to reproduce the2019 experiments.[^2]

Two pinned implementations resolve this differently:

| Source | If both children are singletons | Other material details |
| --- | --- | --- |
| Original authors' Clueminer, `c08ad031` | Score is `1000 × mean cross weight`. | Adds ones to two ratios and a size-dependent power of1000. |
| Successor authors' Python, `b8132453` | Score is `1000²` at the supplied configuration's exponent2, independent of the permitted edge's weight. | Uses the unshifted count/mean ratios for nonempty children. |

The complete Java scoring/update methods and the Python scoring helpers were read directly. The singleton tie problem therefore applies to the Python version, **not the entire Ch2 family**. The Java code preserves singleton affinity ordering, but its added constants make uniform rescaling of affinities consequential.[^3][^4]

The revised Chameleon2++ paper changes graph construction and partitioning, retaining Ch2-style merging. It reports the best external clustering metric across merging stages and12 neighbor-count configurations. Against Ch2, its six-dataset table has two improvements, one tie and three reductions. This is useful pipeline evidence, not validation of one merge rule on our frozen graph. Methods §§2.1–2.3 and results §§3.1–3.2/Table3 were read directly.[^5]

## A control exposes why edge counts need care here

Our graph has every cross-note pair, rather than a sparse semantic neighborhood. For children of sizes `a` and `b`, let `a_p` and `b_p` count their vectors from source note `p`:

```text
internal eligible pairs in A = (a² − sum(a_p²)) / 2
eligible pairs between A and B = a×b − sum(a_p×b_p)
```

These counts are determined by size and source-note composition; no semantic distance appears in them.

For the v1 nonsingleton formula, make every eligible affinity equal and give every vector a distinct source note. The closeness and internal-mean ratios become1. Only the cross-count divided by the smaller internal count remains:

| Child sizes | Cross pairs | Smaller internal count | Score, larger preferred |
| --- | ---: | ---: | ---: |
| 2 and2 | 4 | 1 | 4 |
| 100 and2 | 200 | 1 | 200 |

This is an analytic control, reproduced locally, not a corpus run or an observed semantic failure. It shows that the count factor would introduce strong size preference without any additional similarity evidence. A dense adaptation might still be useful, but cannot be justified as measuring semantic neighborhood connectivity.

A separate Java-formula control uses two children of size2, with equal positive weights throughout. Uniform weights0.5,1 and2 give scores33.740480,22.493653 and16.870240. The geometry's ordering has not changed; the added constants change the score scale. Our existing linear affinities are approximately0.40–0.96, so copying constants from an inverse-distance pipeline is not scale-neutral.

## Decision

Do not label a new run “CHAMELEON” and quietly choose between these definitions. No M10 was implemented from this review.

Within-child evidence is a legitimate unresolved direction, different from PARIS's original-degree normalization. However, original CHAMELEON needs initialization/bisection choices, while a Ch2 adaptation needs an explicit formula, singleton convention and justification for its count and scale factors. A narrower experiment using only the relative-closeness term would also be a new declared adaptation, not the published algorithm.

The immediate useful work is to complete the remaining saved-tree audits and assemble the strongest existing comparisons. This preserves what the controlled runs established without treating additional normalization choices as an automatic next improvement. The research remains a concrete lead for later work; it is not evidence that internal structure cannot help.

## Sources

[^1]: George Karypis, Eui-Hong Han and Vipin Kumar (1999), *CHAMELEON: A Hierarchical Clustering Algorithm Using Dynamic Modeling*, technical report99–007. [Author-uploaded full text](https://www.researchgate.net/publication/2955136_Chameleon_hierarchical_clustering_using_dynamic_modeling).
[^2]: Priyanshu Singh and Kapil Ahuja (2025), *Chameleon2++: An Efficient Chameleon2 Clustering with Approximate Nearest Neighbors*, v1, §2.1.4, Eqs.1–5. [Full text](https://arxiv.org/html/2501.02612v1).
[^3]: Clueminer authors, `Ch2.java`, revision `c08ad031b4362f20b7a0dd64ad788dbef089e45c`, scoring and cluster update methods. [Pinned source](https://raw.githubusercontent.com/deric/clueminer/c08ad031b4362f20b7a0dd64ad788dbef089e45c/modules/chameleon/src/main/java/org/clueminer/chameleon/similarity/Ch2.java).
[^4]: Chameleon2++ authors, `Ch2.py`, revision `b8132453b2f221d3a6e10a58616ff9be840c6565`, `OptimizedChameleonMerger` scoring helpers. [Pinned source](https://raw.githubusercontent.com/modsslabiiti/Chameleon2_plus_plus/b8132453b2f221d3a6e10a58616ff9be840c6565/Ch2.py).
[^5]: Priyanshu Singh and Kapil Ahuja (2025), *Chameleon2++: An Efficient and Scalable Variant Of Chameleon Clustering*, v2. [Full text](https://arxiv.org/html/2501.02612v2).
