# Hard Fine-Region Partitioning Research

## Question

Given one normalized SSE vector for each grounded idea instance, which methods
could place every vector into exactly one fine semantic region without fixing
the number of regions in advance?

This is only the vector-to-region transformation. Region labels and the later
hierarchy are separate problems and cannot be used to repair a bad partition.

## Required behavior

- Every vector has exactly one region.
- A rare idea may remain in a one-vector region.
- No vector may disappear into a noise or residual bucket.
- The method must use the directional geometry of normalized semantic vectors.
- The first pilot must expose bad membership directly through takeaways and
  source masks.
- A successful method must have a plausible path from 194 pilot vectors to the
  full corpus.

## Findings from the literature

### There is no parameter-free answer

Not specifying a region count does not eliminate a resolution decision. It
moves that decision into a distance threshold, density scale, graph
construction, or hierarchy cut. Kleinberg proved that no clustering function
can satisfy three basic and individually reasonable clustering properties at
once; a method must choose a notion of cluster structure.

Source: [Kleinberg, *An Impossibility Theorem for Clustering*](https://papers.nips.cc/paper/2340-an-impossibility-theorem-for-clustering)

### Cosine and angular distance describe the same pair ordering here

For unit vectors `x` and `y`:

```text
||x - y||^2 = 2(1 - x·y)
```

Cosine similarity, chord distance, and angular distance therefore order pairs
identically. Directional centroid methods should use cosine directly. Metric
clustering may use the equivalent angular distance.

### Complete linkage gives the cleanest small-pilot contract

Complete-linkage agglomerative clustering repeatedly merges the two regions
whose most-dissimilar cross-pair is closest. Cutting its hierarchy at cosine
`s` guarantees:

```text
every pair in every resulting region has cosine >= s
```

That is the strictest useful interpretation of a fine region for this pilot.
It also prevents a chain of individually close vectors from joining two
distant endpoints.

The drawback is scale: exact hierarchical clustering requires quadratic
pairwise state and is not the production method for millions of vectors. It is
appropriate as an exact reference for 194 vectors, which have only 18,721
unordered pairs.

Sources: [Müllner, *Modern hierarchical, agglomerative clustering algorithms*](https://arxiv.org/abs/1109.2378), [SciPy linkage definition](https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.linkage.html)

### DP-vMF-means is the strongest direct scaling candidate

DP-vMF-means is a hard-clustering algorithm derived from a Dirichlet-process
mixture of von Mises–Fisher distributions. For each unit vector, it either:

1. assigns the vector to the closest directional centroid when the cosine is
   above a chosen angular boundary; or
2. opens a new region for that vector.

After assignment, each centroid becomes the normalized sum of its members.
The algorithm therefore respects the sphere, allows one-vector regions, and
does not require a fixed region count. Its unavoidable parameter is the
maximum angle from a member to its centroid. The original work explicitly
notes applicability to high-dimensional semantic vectors.

Its weaknesses are also relevant: results can depend on input order and local
optima, and its regions are directional caps around centroids. A cap may be a
poor model if real semantic regions are long or curved.

Sources: [Straub et al., *Small-Variance Nonparametric Clustering on the Hypersphere*](https://openaccess.thecvf.com/content_cvpr_2015/html/Straub_Small-Variance_Nonparametric_Clustering_2015_CVPR_paper.html), [Banerjee et al., *Clustering on the Unit Hypersphere using von Mises-Fisher Distributions*](https://www.jmlr.org/papers/v6/banerjee05a.html)

### Why the other methods are not first

- Spherical k-means has the right geometry but requires a fixed region count
  and forces rare ideas into an existing region.
- HDBSCAN finds persistent dense regions but intentionally returns noise.
  Corpus frequency would decide whether a rare valid idea exists.
- A nearest-neighbor graph plus Leiden is the strongest alternative if regions
  are not centroid-shaped. It adds a neighbor count, graph symmetrization rule,
  edge weighting, and community resolution before that complexity is known to
  be necessary. Leiden is preferable to Louvain because it guarantees
  connected communities.
- FINCH avoids a conventional threshold but always links every point through
  its first neighbor. That removes the valid one-vector-region outcome and is
  especially risky when high-dimensional hubs or a single bad nearest neighbor
  exist.

Sources: [Campello et al., *Hierarchical Density Estimates for Data Clustering, Visualization, and Outlier Detection*](https://doi.org/10.1145/2733381), [Traag et al., *From Louvain to Leiden*](https://doi.org/10.1038/s41598-019-41695-z), [Sarfraz et al., *FINCH*](https://openaccess.thecvf.com/content_CVPR_2019/html/Sarfraz_Efficient_Parameter-Free_Clustering_Using_First_Neighbor_Relations_CVPR_2019_paper.html), [Radovanović et al., *Hubs in Space*](https://www.jmlr.org/papers/volume11/radovanovic10a/radovanovic10a.pdf)

## What automated measurements can and cannot establish

Internal measurements can expose geometric defects:

- a member closer to another region than its own;
- a region with a weak most-dissimilar pair;
- a hub appearing in many nearest-neighbor lists;
- DP-vMF assignments changing across input orders;
- a resolution at which almost everything is one region or one-vector regions.

They cannot establish that a region has one recognizable human meaning.
Silhouette measures compactness and separation under the chosen geometry, not
semantic truth. Stability can reject a fragile partition, but the most stable
partition is not necessarily the useful one.

Sources: [Rousseeuw, *Silhouettes*](https://doi.org/10.1016/0377-0427(87)90125-7), [von Luxburg, *Clustering Stability: An Overview*](https://doi.org/10.1561/2200000008), [Chang et al., *Reading Tea Leaves*](https://papers.nips.cc/paper/2009/hash/f92586a25bb3145facd64ab20fd554ff-Abstract.html)

The semantic check must therefore inspect the unlabeled member evidence. A
generated region name comes only after membership succeeds.

## Research conclusion

The smallest defensible pilot needs both:

1. exact complete linkage as the conservative reference; and
2. DP-vMF-means as the scalable candidate.

If compact regions work, no graph layer is needed. If exact coherent groups
exist but DP-vMF cannot reproduce them, the next research question is whether
their shape requires a local graph method. If exact complete linkage itself
cannot find a useful resolution, changing the scalable algorithm cannot rescue
the current vector geometry.
