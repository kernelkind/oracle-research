# Corpus-Induced Semantic Region Discovery

## Status

Literature review complete. This is research, not an approved architecture or
experiment.

An earlier version of this review misunderstood *dynamic* to mean clustering a
person's rated notes or the results of a query. That is not the target.

## Accepted Problem

The public corpus is embedded first. A public process then derives semantic
structure from the complete embedded corpus:

- no subject taxonomy is supplied beforehand;
- subjects emerge from relationships among public notes;
- every eligible note participates in the versioned public structure;
- a note may belong to several regions or remain an explicit fine-grained
  outlier;
- descriptions are generated after regions are discovered;
- private ratings do not create the public subjects;
- private evidence may overlay the public structure and rank or select notes
  locally without redefining its regions.

The user-facing list may still be dynamic. A client can choose a useful
resolution, order regions against private evidence, and describe the displayed
choices without reclustering the corpus around that person.

Query-result clustering, rated-note clustering, and a fixed external ontology
do not satisfy this requirement.

## Central Finding

This is a recognized family of problems: corpus-wide clustering, hierarchical
clustering, and topic discovery over document representations. The literature
makes useful structure plausible after embeddings exist. It does not establish
that useful structure exists in this Nostr corpus or its current embedding
geometry.

It does **not** support the existence of one objectively correct subject map.
Every method still chooses a notion of region, scale, overlap, and outlier:

- spherical k-means chooses a number of partitions;
- density methods choose density and minimum-size rules;
- graph methods choose neighbors, edge weights, and resolution;
- probabilistic topic models choose priors and model form;
- hierarchical methods choose where the hierarchy is cut.

[Kleinberg's clustering result](https://papers.nips.cc/paper_files/paper/2002/hash/43e4e6a6f341e00671e123714de019a8-Abstract.html)
shows that a distance-based clustering function cannot simultaneously satisfy
its scale-invariance, richness, and consistency axioms. Methods that infer a
topic count move the choice into assumptions; they do not reveal a unique
truth.

The defensible requirement is therefore:

> Derive a reproducible, versioned, corpus-wide structure that yields
> human-validated semantic regions at useful granularities.

Region names are outputs, not inputs. A region earns the name *subject* only
when its membership and description survive human validation.

## Evidence That Corpus-Induced Regions Are Plausible

[Top2Vec](https://arxiv.org/abs/2008.09470) embeds documents, reduces the
geometry, finds dense regions, and derives topic words from those regions. It
does not require a predefined topic count and can reduce the discovered topics
into a hierarchy.

[BERTopic](https://arxiv.org/abs/2203.05794) follows a related
embedding-to-density-cluster pipeline and derives descriptions with
class-based TF-IDF. Both are strong precedents for subjects emerging after
documents are represented.

Direct clustering is not merely a toy baseline.
[Zhang et al.](https://aclanthology.org/2022.naacl-main.285/) found that
clustering high-quality sentence embeddings with a suitable term-selection
method matched or beat the tested neural topic models on automatic coherence
and diversity while being simpler.

The most relevant human study used BERT embeddings, UMAP, and HDBSCAN on
10,000 news articles.
[Eklund and Forsman](https://aclanthology.org/2022.emnlp-industry.65/) found 52
of 63 clusters coherent. Those clusters contained 57% of the articles after the
study's soft-assignment postprocessing forced HDBSCAN's noise points into
clusters; 2,367 articles were manually inspected. The largest cluster was
incoherent, some regions grouped writing style rather than subject, and
evaluators disagreed about useful granularity. The authors also disclosed that
their embeddings accidentally used BERT's first hidden layer and suspected
padding artifacts in the largest cluster. This is limited evidence for the
basic idea and a strong warning against assuming that an automatic flat
partition is already a subject map.

The conclusion is narrow:

> Whole-document embeddings can contain discoverable subject structure, but
> useful subjects, assignments, and granularity do not follow automatically
> from clustering.

## Construction Families

### Spherical or bisecting k-means

The Oracle vectors are L2-normalized. Spherical k-means is therefore a natural
simple baseline because it partitions by cosine geometry.
[Banerjee et al.](https://www.jmlr.org/papers/v6/banerjee05a.html) derive
spherical k-means as a special case of mixtures of von Mises-Fisher
distributions for directional data.

Advantages:

- simple and predictable;
- scalable with streaming or minibatch implementations;
- every note receives an assignment;
- recursive bisection can provide several granularities.

Limitations:

- the number of regions or split rule is chosen;
- assignments form spherical Voronoi cells around centroids;
- every outlier is forced into a region;
- one note follows one hard path;
- uneven and rare subjects can be absorbed by larger regions.

This is the right sanity baseline, not the presumed final design.

### Scalable corpus-wide hierarchy

[The Sub-Cluster Component Algorithm](https://arxiv.org/abs/2010.11821) builds
a hierarchy by thresholding the nearest-neighbor relation between current
subclusters and taking connected components at each round. Its sparse
implementation derives those relations from a neighbor graph. It does not
require one fixed topic count.

Its scale evidence comes from two materially different settings:

- the 1.3-million-point, 2,048-dimensional benchmark used ImageNet embeddings
  and ground-truth dendrogram purity;
- the 30-billion-query application used proprietary lexical and behavioral
  features, with human review of about 1,200 extracted fine-grained flat
  clusters.

It did not human-validate a hierarchy over million-scale text embeddings or a
navigation interface. It remains a strong scale precedent for a first
corpus-wide hierarchy test because it:

- operates on embedding relationships;
- produces reusable multiple granularities;
- has direct million-scale and human-evaluation precedent;
- does not require predefined subjects or a fixed region count.

It still makes consequential choices. Its published benchmarks used a 25-NN
ScaNN graph, a 200-threshold schedule, and a selected hierarchy cut. More
generally:

- the neighbor graph defines which relationships exist;
- thresholds define the hierarchy;
- membership is hard and nested;
- hubs and outliers can still be assigned misleadingly;
- no result establishes Nostr subject fidelity.

It is a scalable candidate to test, not an established winner or architecture
decision.

### Density hierarchy

HDBSCAN supplies variable-density clusters, a hierarchy, and an explicit noise
state. Top2Vec and BERTopic demonstrate why that shape is attractive.

It replaces a chosen topic count with other choices:

- minimum cluster size;
- neighborhood density;
- dimension-reduction behavior;
- extraction of a flat set from the hierarchy.

High-dimensional density estimation is difficult, so these systems commonly
reduce dimensions before clustering. That transformation can change local
density and boundaries. The SCC study could not scale HDBSCAN to its
1.3-million-point benchmark.

HDBSCAN remains a credible comparator if explicit fine-grained outliers prove
important. It is not automatically the best first method for the current
3,584-dimensional corpus.

### Neighbor graph and community detection

A cosine-neighbor graph followed by
[Leiden](https://arxiv.org/abs/1810.08473) is scalable and yields connected
communities. Several resolutions can be materialized.

The graph is not a neutral compression of the original matrix:

- neighbor count and approximate-search recall decide which edges exist;
- edge symmetrization and weighting change community structure;
- the resolution parameter changes the partition;
- ordinary Leiden returns hard, non-overlapping communities;
- Leiden with modularity can merge small real communities because of
  modularity's [resolution limit](https://arxiv.org/abs/physics/0607100);
  Leiden with the Constant Potts Model replaces that global limit with an
  explicit resolution parameter.

Graph methods are plausible, but they add choices without yet offering a clear
advantage over a hierarchy designed directly for embedding clustering. Leiden
should not be adopted merely because it scales.

### Probabilistic and additive topics

[LDA](https://www.jmlr.org/papers/v3/blei03a.html) represents each document as
a mixture of word-level topics. The
[hierarchical Dirichlet process](https://proceedings.mlr.press/v15/wang11a.html)
defines a potentially unbounded topic count, although practical variational
inference uses a finite truncation. The
[nested HDP](https://arxiv.org/abs/1210.6738) lets words in one document
traverse different paths in a shared hierarchy. The
[final nHDP paper](https://www.cs.columbia.edu/~blei/papers/PaisleyWangBleiJordan2015.pdf)
reports a published experiment on 2.7 million Wikipedia documents.

These methods provide a principled account of multi-topic documents. They also
introduce a new bag-of-words or token representation instead of simply
organizing the existing Oracle vectors. Short informal notes are sparse, and
topic priors still determine the resulting structure.

[FASTopic](https://proceedings.neurips.cc/paper_files/paper/2024/hash/998f8d8ff2697da2eae5f87143668754-Abstract-Conference.html)
combines frozen document embeddings, learned topic prototypes, and soft
document-to-topic weights. It is attractive in form, but requires a chosen
topic count, materializes document-topic relations, was evaluated at much
smaller scale, and lacks human navigation evidence.

These are important compositional comparators, not the simplest first
full-corpus construction.

## One Note, Several Subjects

This requirement is not solved by ordinary soft clustering.

A whole-note embedding is one point. If that point is between two regions,
multiple weights can mean either:

1. the note genuinely contains both subjects; or
2. the model is uncertain which single subject fits.

GMM, von Mises-Fisher, fuzzy, and HDBSCAN membership scores generally cannot
distinguish those cases. The scores describe proximity or uncertainty around
one pooled representation, not proof of compositional meaning.

[Semantic Component Analysis](https://aclanthology.org/2025.findings-emnlp.964/)
is the most direct reviewed attempt to recover several semantic components
from whole-document embeddings. Each iteration clusters residual embeddings
and subtracts each sample's projection onto its assigned centroid component.
It was tested on up to 1.463 million tweets and produced multiple components
with competitive automatic metrics.

Its evidence is promising but insufficient:

- it had no navigation user study;
- component count varied substantially with configuration;
- generic components could be over-assigned;
- activation scores were not calibrated as a share of meaning;
- it assumes semantic meanings can be separated as vector directions.

Token- or span-level approaches such as
[contextual token clustering](https://arxiv.org/abs/2010.12626) and
[Contextual-Top2Vec](https://aclanthology.org/2024.findings-emnlp.790/) can
associate different text spans with different regions. That makes a mixed
note's assignments more auditable, but requires another public representation
and considerably more computation.

The current whole-note matrix may be sufficient for broad navigation. It has
not been shown sufficient for faithful multi-subject membership. That is a
prerequisite to test rather than a reason to redesign the Oracle now.

## Complete Coverage Without False Certainty

"Map every note" must not mean "force every note into a confident fine-grained
subject."

Every eligible note should remain addressable and browsable in the versioned
structure. At a given resolution it can have:

- one or more supported memberships;
- a coarse membership but no reliable fine membership;
- a boundary or residual state;
- an explicit outlier state.

An outlier is a mapping state, not a subject. It may still retain a reliable
coarse placement and must remain discoverable. This preserves complete corpus
access without manufacturing a fine subject for garbage, bridges, one-off
ideas, or genuinely rare content.

Rare content creates an unavoidable tradeoff:

- hard partitioning forces it into some region; chosen splits determine
  whether it forms a rare region or is absorbed;
- density methods may classify it as noise;
- aggressive component discovery may invent weak generic subjects.

Long-tail access therefore has to be evaluated directly. It cannot be inferred
from total assignment coverage.

## Granularity and Hierarchy

The public structure should support several useful granularities rather than
claim one true level.

A coarse region such as *software* and a narrower region such as *Rust
compiler tooling* can both be valid navigation choices. The important claims
are:

- children are coherent refinements of their parent;
- siblings are meaningfully distinct;
- at least one level is useful for choosing where to explore;
- rare areas are not erased at every level.

[Stability analysis](https://arxiv.org/abs/1404.4606) can identify brittle
resolutions by comparing results across seeds or corpus perturbations.
[Clustering-stability research](https://arxiv.org/abs/1007.1075) also warns
that stability alone can favor the wrong structure. It is a rejection screen,
not semantic proof.

## Labels Come After Regions

A plausible label does not validate a region. Region construction,
note-to-region membership, hierarchy, and label quality are four separate
claims.

Post-hoc descriptions should be grounded in:

- representative member notes;
- terms or phrases distinctive relative to parent and sibling regions;
- an explicit short inclusion description;
- examples near the center and boundary.

An LLM may draft a label from those public inputs. The label remains a
proposal. [Human topic-label research](https://aclanthology.org/Q17-1001/)
found automatic labels weaker than human labels and validated labels against
the documents they described.

A label drafted from one fixed member sample should predict other members that
were hidden from the drafting step and reject nearby nonmembers. Fluency is not
evidence of faithfulness.

## Human Validation

Automatic coherence, clustering loss, likelihood, and stability cannot decide
whether the regions are useful subjects.

[Reading Tea Leaves](https://proceedings.neurips.cc/paper_files/paper/2009/hash/f92586a25bb3145facd64ab20fd554ff-Abstract.html)
found that likelihood can prefer topics people find less interpretable.
[Hoyle et al.](https://proceedings.neurips.cc/paper/2021/hash/0f83556a305d789b1d71815e8ea4f4b0-Abstract.html)
found that automatic coherence measures can select winners that human
judgments do not support.

A Nostr validation must keep these questions separate:

1. **Region coherence:** do randomly sampled members that were not chosen as
   exemplars belong together?
2. **Assignment fidelity:** does a representative, boundary, or mixed note
   actually belong to every claimed region?
3. **Distinctness:** can nearby nonmembers and sibling regions be rejected?
4. **Hierarchy:** do children refine rather than merely rename parents?
5. **Granularity:** is the level useful for choosing what to explore?
6. **Long-tail behavior:** are sparse meanings preserved or honestly marked as
   residuals?
7. **Label fidelity:** does a description drafted from one visible member
   sample predict other members hidden from that drafting step?
8. **Stability:** do reruns and modest corpus changes preserve understandable
   structure?
9. **Navigation:** does selecting a region lead to the kind of notes expected?

Notes hidden from label drafting test label fidelity. A separately resampled
construction can test assignment and stability. These are audit devices, not
permanent omissions; the final public artifact still covers the complete
corpus.

## Scale Against the Existing Oracle

The frozen Oracle representation contains:

- 3,530,455 notes;
- 3,584 dimensions;
- L2-normalized FP32 vectors;
- about 47.1 GiB of raw vector data.

GTE-Qwen2 was selected and tested here for semantic retrieval, not unsupervised
topic clusterability. Good nearest neighbors do not prove that the full
geometry separates into coherent subjects. This is the central
artifact-specific unknown.

A sparse directed neighbor graph is small relative to the matrix: storing a
32-bit note index and FP32 similarity for 32 neighbors per note is about
0.84 GiB before symmetrization, index state, and library overhead. Exact
all-pairs construction is infeasible. Approximate index construction, search
cost, and achieved neighbor recall over this 3,584-dimensional matrix must be
calibrated; final edge storage is not the difficult part.

[FAISS](https://arxiv.org/abs/1702.08734) demonstrates that much larger
similarity-search and kNN-graph workloads are feasible on GPUs. That establishes
general feasibility, not this build's runtime, neighbor recall, or semantic
quality.

Dimension reduction may make clustering practical.
[Recent prompt-embedding analysis](https://aclanthology.org/2025.findings-acl.1330/)
found substantial redundant dimensions with the same 3,584-dimensional
gte-Qwen2 model. Its strong clustering result used a clustering-task
instruction, whereas the Oracle's public notes are unprompted document
encodings. Reduction quality for this matrix remains unproven and must be
measured.

Versioned immutable rebuilds are the conservative correctness baseline, not an
approved update design. Incremental assignment, rebuild frequency, and stable
region identities across changing corpora remain unresolved.

## Comparison

| Family | What it gives | Main unresolved risk |
| --- | --- | --- |
| Spherical/bisecting k-means | Cheapest full assignment and multilevel baseline | Chosen splits, forced outliers, hard one-path membership |
| SCC hierarchy | Scalable corpus-induced hierarchy without fixed topic count | Graph and threshold choices; hard membership |
| HDBSCAN | Density hierarchy and explicit outliers | Dimension reduction, density parameters, scale and long-tail loss |
| Leiden on a neighbor graph | Scalable communities at several resolutions | Graph construction and resolution redefine the result |
| LDA/HDP/nHDP | Compositional corpus-wide topics | New token model, priors, short-note sparsity |
| FASTopic | Soft topics over frozen embeddings | Fixed topic count and unproven scale/human utility |
| SCA | Multiple components from existing whole-note vectors | Unproven human fidelity and linear-decomposition assumption |
| Token/span methods | Auditable multiple meanings | New expensive public representation |

## Recommendation

Do not predefine subjects, generate them from private ratings, or build a
navigation interface yet.

The first architecture-neutral question is:

> Does the complete Nostr embedding corpus contain stable, coherent, and
> distinguishable regions at meaningful granularities?

The smallest credible next experiment would compare:

1. **SCC hierarchy** as a published million-scale hierarchy candidate; and
2. **bisecting spherical k-means** as the simple scalable baseline.

Both would use the same frozen public vectors and be evaluated across several
resolutions. Human review of representative members, boundary notes, rare
notes, mixed notes, and nearby nonmembers would test only region coherence,
distinctness, and assignment fidelity. Internal metrics would only reject
obviously brittle outputs.

If a construction passes that prerequisite, a separate labeling test would
draft descriptions from a fixed visible sample and judge whether they predict
other members hidden from label drafting while rejecting nearby nonmembers.
Only then would a navigation test ask whether the described choices behave as
the person expects.

SCA should be tested separately on the mixed-note cases if the hierarchy works
but one-path membership proves inadequate. A token/span representation is
warranted only if whole-note methods cannot recover meanings humans clearly
see.

This sequence eliminates unnecessary parts:

- first prove useful corpus-wide regions exist in the artifact already paid
  for;
- then test whether one vector per note is sufficient for overlap;
- then validate labels;
- only then design user ordering or navigation.

No new architecture or experiment is approved by this review.
