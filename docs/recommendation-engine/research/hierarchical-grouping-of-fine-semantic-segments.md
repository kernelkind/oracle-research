# Hierarchical Grouping of Fine Semantic Segments

## Status

This document records the CREC-122 literature review after correcting the
object being organized.

It is research for a later stage, not a frozen algorithm decision or current
execution plan. Hierarchy comparison begins only after the fine-segmentation
work demonstrates useful fine subjects. The review identifies methods that can
then be compared without asking a language model to define the topology or
fitting one filled geometric volume to every parent.

## Question

Given validated and frozen fine semantic segments, how can we construct a useful
broad-to-narrow hierarchy in which every higher subject is exactly a union of
complete finer subjects?

The input is:

```text
FineSegmentId -> {AtomicSubjectVectorId}
```

This representation does not require the fine-segmentation stage to be
exhaustive or non-overlapping. One vector may occur in more than one fine
segment, and an unassigned vector is outside the hierarchy input. The exact
fine-segmentation membership contract must be frozen before this research is
turned into an experiment.

The required output is a nested partition:

```text
fine segments
  -> groups of fine segments
  -> groups of those groups
  -> ...
```

For every hierarchy node `h`:

```text
members(h) = union of the complete fine segments below h
```

A parent is not required to be one point, centroid, sphere, box, Gaussian, or
other filled region in the embedding space.

For example, a parent called `Programming languages` could be the exact union
of separate Rust, Python, and C fine segments. It does not claim that every
point in the empty space between those segments belongs to the parent.

## Corrected Image-Segmentation Analogy

The useful analogy is not that a semantic subject has the shape of an image
object. It is that hierarchical image segmentation organizes indivisible fine
regions through a graph:

| Image segmentation | Semantic hierarchy |
|---|---|
| pixel or local feature | atomic-subject vector |
| superpixel or fine image region | frozen fine semantic segment |
| physical region adjacency | inferred semantic-neighborhood relation |
| boundary strength | evidence that two fine segments should remain separate |
| region hierarchy | nested unions of semantic segments |

The mathematical image-segmentation literature already supports hierarchical
segmentation on arbitrary edge-weighted graphs. A two-dimensional pixel grid
is not required. Ultrametric-watershed theory establishes a correspondence
between edge-weighted graph hierarchies and nested segmentations.

What does **not** transfer automatically is adjacency. Two image regions either
share a physical boundary or they do not. Semantic space supplies no canonical
equivalent. Constructing the semantic relation graph is therefore a
load-bearing modeling decision.

Source: [Najman, *On the Equivalence Between Hierarchical Segmentations and
Ultrametric Watersheds*](https://arxiv.org/abs/1002.1887).

## Central Finding

The strongest methods do not reduce two fine segments to one direct cosine.
They compare how each fine segment relates to a wider semantic neighborhood.

This matters because siblings in a useful hierarchy need not be one another's
closest points. For example:

```text
Rust
  -> compiler tooling, type systems, package management, programming

Python
  -> interpreters, package management, programming, tooling
```

Rust and Python can have similar patterns of relationships even when their
direct centroid cosine is not the strongest available pair. Conversely, one
accidentally close vector pair should not determine a merge when the rest of
the segments' relationships disagree.

This is the main distinction from the previously tested average-linkage and
SCC constructions. Those methods still made direct similarity do nearly all
the work.

## Proposed Semantic Relation Graph

The most defensible initial graph construction is:

1. Build a sparse mutual-`k`-nearest-neighbor graph over the original atomic
   meaning vectors.
2. If fine-segment memberships are non-overlapping, contract each fine
   segment's vector nodes into one segment node. If memberships overlap, this
   contraction is not defined: the hierarchy experiment must first specify how
   one vector contributes evidence to several segment nodes without duplicating
   or discarding it.
3. Preserve segment mass, the multiplicity and weight of cross-segment edges,
   and internal edges as self-flow when the hierarchy method supports it.

For segments `a` and `b`, one possible contracted edge weight is:

```text
w(a, b) = sum of retained atom-level neighbor-edge weights
          crossing from a to b
```

This retains evidence from every atomic vector. Replacing each fine segment
with one average vector would discard local contacts, segment size, internal
cohesion, and potentially multimodal geometry.

Mutual nearest-neighbor edges are preferable to an ordinary directed `k`-NN
graph as a first attempt because they reduce asymmetric links and some
high-dimensional hub behavior. Shared-nearest-neighbor similarity is a later
graph-construction candidate if direct neighbor edges remain unstable; it
compares the overlap between two points' neighborhoods and was developed for
high-dimensional data with differing densities.

Source: [Ertöz, Steinbach, and Kumar, *Finding Clusters of Different Sizes,
Shapes, and Densities in Noisy, High Dimensional
Data*](https://epubs.siam.org/doi/10.1137/1.9781611972733.5).

The first hierarchy comparison should not add other edge types:

- Same-note co-occurrence means two ideas were communicated together. It does
  not prove that either is a broader subject of the other.
- Vector-to-note prominence describes importance to a note. It is useful for
  ordering notes inside a subject, not for defining subject topology.
- Generated labels describe already-formed groups. They must not determine
  membership during this comparison.

Those signals can be tested independently later if semantic-neighborhood
relations prove insufficient.

## Leading Candidate: Nested Degree-Corrected Stochastic Block Model

A stochastic block model groups graph nodes according to the pattern of edges
between groups. In the nested model:

1. fine-segment nodes are assigned to blocks;
2. inter-block edge counts form a smaller graph;
3. that graph is assigned to broader blocks;
4. the process repeats to form a hierarchy.

Every parent is therefore exactly a union of its child blocks.

The model chooses structure by minimizing the complete description length:

```text
description length = cost of describing the hierarchy
                   + cost of describing the graph given that hierarchy
```

An extra group or level survives only when the graph becomes sufficiently
more predictable to pay for the added hierarchy complexity. This supplies
evidence-based choices for group count, branching, and depth rather than one
global cosine cutoff. The model supports nonbinary structure and is not
limited to dense spherical clusters.

Degree correction is important because fine segments can differ substantially
in size and graph degree. Without it, high-degree semantic hubs can be grouped
for the wrong reason.

Sources:

- [Peixoto, *Hierarchical Block Structures and High-Resolution Model Selection
  in Large Networks*](https://journals.aps.org/prx/abstract/10.1103/PhysRevX.4.011047)
- [Peixoto, *Nonparametric Bayesian Inference of the Microcanonical Stochastic
  Block Model*](https://journals.aps.org/pre/abstract/10.1103/PhysRevE.95.012317)
- [Peixoto, *Nonparametric Weighted Stochastic Block
  Models*](https://journals.aps.org/pre/abstract/10.1103/PhysRevE.97.012306)

### Why it fits

- It preserves frozen leaves.
- Higher nodes are exact unions, not enclosing geometric shapes.
- It can use complete relation patterns rather than direct pairwise proximity.
- Its model-selection objective penalizes unsupported levels.
- Its published inference methods are intended for large sparse graphs.

### Main risk

An unrestricted block model can discover graph roles or disassortative
patterns. Two segments could be grouped because they interact with the graph
similarly even if a person would not recognize one broader subject containing
both. Statistical graph structure is not automatically semantic taxonomy.

This is the strongest primary candidate, but that risk prevents selecting it
without a semantic comparison.

## Independent Candidate: Hierarchical Infomap

Hierarchical Infomap models a random walk over the segment graph. A group is
useful when movement tends to remain inside it, allowing the walk to be
described economically with a shared local codebook. It recursively adds
levels only when they shorten the complete description.

The result has:

- exact nested unions;
- nonbinary branching;
- different depths in different branches;
- no required fixed group count.

Source: [Rosvall and Bergstrom, *Multilevel Compression of Random Walks on
Networks Reveals Hierarchical Organization in Large Integrated
Systems*](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0018209).

### Why it fits

Infomap more directly prefers cohesive semantic neighborhoods than an
unrestricted block model. It is therefore an important independent comparison
when the intended subject hierarchy is primarily assortative.

### Main risk

It discovers flow-retaining modules, not semantic abstraction itself. It can
overpartition long or diffuse structures when one-step flow cannot see far
enough through the graph. Graph hubs, neighbor count, and edge weights can
materially change the result.

Source: [Schaub, Lambiotte, and Barahona, *Encoding Dynamics for Multiscale
Community Detection: Markov Time Sweeping for the Map
Equation*](https://journals.aps.org/pre/abstract/10.1103/PhysRevE.86.026112).

## Diagnostic Candidate: Agglomerative Information Bottleneck

Agglomerative Information Bottleneck represents each fine segment by a
conditional distribution over a chosen context. For this experiment, the
context can be the segment's semantic neighbors in the contracted graph.

It starts with one cluster per fine segment and repeatedly merges the pair
whose union loses the least information about those context distributions.
Two segments can therefore merge because they predict similar semantic
surroundings rather than because they have the highest direct cosine.

Source: [Slonim and Tishby, *Agglomerative Information
Bottleneck*](https://papers.nips.cc/paper_files/paper/1999/hash/be3e9d3f7d70537357c67bb3f4086846-Abstract.html).

### Why it fits

- It provides the clearest direct test of the relationship-pattern hypothesis.
- Every merge is an exact union.
- The individual merge decision is comparatively easy to inspect.

### Main risks

- The straightforward method produces a forced binary dendrogram.
- The original method does not supply a principled semantic stopping rule.
- The choice of context distribution defines what information is preserved.
- A straightforward implementation maintains a quadratic set of merge
  candidates.

It is therefore the strongest transparent diagnostic, not the leading final
architecture.

## Other Methods Reviewed

### Ultrametric watershed and Binary Partition Trees

These are the closest formal image-segmentation analogues. They contract
regions while recording merge or boundary levels, and every threshold yields
a valid nested partition.

Their limitation is decisive: they organize a hierarchy once a meaningful
boundary strength exists, but they do not tell us what a semantic boundary
should be. Using direct cosine as that boundary would reproduce the weakness
already observed. Minimum-spanning-tree variants can also chain large groups
through one accidental weak edge.

Sources:

- [Najman, *On the Equivalence Between Hierarchical Segmentations and
  Ultrametric Watersheds*](https://arxiv.org/abs/1002.1887)
- [Salembier and Garrido, *Binary Partition Tree as an Efficient
  Representation for Image Processing, Segmentation, and Information
  Retrieval*](https://imatge.upc.edu/web/sites/default/files/pub/aSalembier00.pdf)

### CHAMELEON

CHAMELEON uses a `k`-NN graph and merges clusters according to their relative
interconnectivity and relative closeness compared with each cluster's internal
structure. This is stronger than centroid linkage and can follow irregular
shapes.

It is a possible deterministic graph-merging baseline. However, many current
fine segments contain very few vectors, making estimates of internal
connectivity and closeness unstable. It also remains fundamentally a
proximity/interconnectivity method rather than a full relationship-pattern
model.

Source: [Karypis, Han, and Kumar, *CHAMELEON: A Hierarchical Clustering
Algorithm Using Dynamic Modeling*](https://conservancy.umn.edu/bitstreams/14e94fa2-92fb-458b-b6fb-527bb4ba07ca/download).

### Density cluster trees and HDBSCAN

Density cluster trees organize connected components of progressively lower
density level sets. HDBSCAN uses mutual-reachability distance, builds this
hierarchy, and extracts persistent clusters.

This is useful when one broader group should be one connected density region.
That is not required here. `Programming languages` may be a union of separated
Rust, Python, and C regions with no dense path filling the space between them.
Density connectivity would add a requirement that the desired architecture
does not need.

Source: [Chaudhuri et al., *Consistent Procedures for Cluster Tree Estimation
and Pruning*](https://cseweb.ucsd.edu/~dasgupta/papers/cluster-ieee.pdf).

### Markov Stability

Markov Stability finds graph partitions at different diffusion times and can
expose robust scales. The partitions at different times are optimized
independently and are not guaranteed to nest. Enforcing a hierarchy afterward
would add another reconciliation step, so this is better treated as a scale
diagnostic than a final construction method.

Source: [Delvenne, Yaliraki, and Barahona, *Stability of Graph Communities
Across Time Scales*](https://www.pnas.org/doi/10.1073/pnas.0903215107).

### Diffusion condensation

Diffusion condensation repeatedly diffuses and contracts data to expose
coarser structure. It is a genuine multiscale method, but it moves and averages
the representation while constructing the hierarchy. That makes the meaning
of a parent harder to ground in the fixed fine segments and adds machinery not
required for the first comparison.

Source: [Brugnone et al., *Coarse Graining of Data via Inhomogeneous Diffusion
Condensation*](https://pmc.ncbi.nlm.nih.gov/articles/PMC7398322/).

### Bayesian hierarchical clustering and rose trees

Bayesian rose trees can produce nonbinary trees and compare alternate tree
structures through marginal likelihood. With a Gaussian component likelihood,
however, each parent is again evaluated as if its descendants came from one
geometric distribution. That quietly reintroduces the solid-parent-shape
assumption. The approach is relevant only if a new likelihood over semantic
relationship evidence is designed first.

Source: [Blundell, Teh, and Heller, *Bayesian Rose
Trees*](https://www.gatsby.ucl.ac.uk/~ucgtcbl/papers/BluTehHel2010a.pdf).

### Independent flat clustering at several resolutions

Running a flat clustering method several times at different resolutions does
not guarantee that the partitions are nested. A segment can change branches
between levels. The hierarchy must be part of the model or enforced through a
monotone merge process.

Source: [Guimarães et al., *Hierarchical Image Segmentation Through Discrete
Optimization*](https://arxiv.org/abs/1206.2807).

## Comparison

| Method | Grouping evidence | Strict nested output | Chooses levels | Principal concern |
|---|---|---:|---:|---|
| Nested degree-corrected SBM | complete graph connection patterns | yes | yes, through model selection | graph roles may not be subjects |
| Hierarchical Infomap | random-walk persistence | yes | yes, through code length | diffuse subjects may be split |
| Agglomerative Information Bottleneck | similarity of neighbor distributions | yes, binary | no principled semantic stop | context definition controls result |
| Ultrametric watershed | supplied boundary strengths | yes | only through supplied scales | semantic boundary remains unsolved |
| CHAMELEON | relative connectivity and closeness | yes | needs a target or stopping choice | unstable for very small leaves |
| HDBSCAN or density cluster tree | density-connected components | yes | persistence-based extraction | imposes unnecessary connectedness |
| Markov Stability | diffusion retention at each scale | no | finds scales | partitions may cross |

## Recommended Controlled Comparison

No paper establishes that semantic-neighborhood graph structure corresponds
to a human broad-to-narrow subject hierarchy. That remains the experiment.

The smallest comparison that isolates it is:

1. Freeze one atom-level mutual-`k`-NN graph and the demonstrated fine-segment
   memberships.
2. Run a nested degree-corrected SBM as the primary statistical candidate.
3. Run hierarchical Infomap as the assortative flow-based comparison.
4. Run Agglomerative Information Bottleneck over the same neighbor evidence as
   the transparent diagnostic.
5. Inspect inferred groups bottom-up using their raw supporting masks. Do not
   generate titles before deciding whether the membership itself is coherent.
6. After the initial comparison, rerun the promising method under nearby graph
   neighbor counts, edge perturbations, and algorithm seeds to measure
   stability.

Earlier small artifacts tested mechanics only. A hierarchy comparison should
use the first fine-segment artifact admitted by the synthetic and real-niche
FSA work; no larger artifact is authorized merely by this review.

The review criteria are:

- every child in a proposed group is a valid narrower refinement of one
  recognizable broader subject;
- an unsupported collection may remain under a structural root rather than
  receive a fabricated semantic parent;
- higher nodes add a real distinction instead of reproducing the same child
  or note set;
- useful groups persist under small graph and inference perturbations;
- different branches may have different depths and branching factors.

The navigation constraint of showing only a small number of choices is a later
tree-condensation problem. It should not determine the scientific topology
during this comparison.

## Findings Versus Hypotheses

The literature establishes:

- arbitrary edge-weighted graphs can represent nested segmentations;
- nested block models and hierarchical Infomap produce hard nested graph
  partitions without fixing one hierarchy depth;
- Agglomerative Information Bottleneck can merge objects according to the
  information contained in their context distributions;
- independently optimized partitions at several scales need not form a
  hierarchy.

The literature does **not** establish:

- that mutual semantic nearest-neighbor edges are the correct analogue of
  image-region adjacency;
- that connection-pattern blocks correspond to recognizable subjects;
- that one graph construction works across sparse and dense areas of this
  corpus;
- that any candidate will produce labels or navigation choices that accurately
  predict the notes below them.

The resulting working hypothesis is:

> The complete semantic-neighborhood relationships among frozen fine segments
> contain enough structure for a graph hierarchy method to recover useful
> broader subjects as exact unions of those segments.

That hypothesis is more precise than assuming direct cosine linkage should
construct the hierarchy, and it can be tested without changing the earlier
representation or fine-segment stages.
