# Corpus-Induced Semantic Region Discovery

## Status

Literature evidence record. This document reports what published methods
demonstrate, cross-study synthesis, and remaining evidence gaps. It does not
contain project requirements, recommend an architecture, select a method, or
approve an experiment.

Project inferences and the current technical proposal are kept separately in
[Corpus-Induced Subject Map Hypothesis](../design/corpus-induced-subject-map-hypothesis.md).

## Limits of the Evidence

This is a recognized family of problems: corpus-wide clustering, hierarchical
clustering, and topic discovery over document representations. The literature
contains methods that construct semantic structure after documents are
represented. It does not establish that any reviewed method will produce useful
subjects for Nostr notes, nor which text representation should be used.

Every reviewed method chooses a notion of region, scale, overlap, and outlier:

- spherical k-means chooses a number of partitions;
- density methods choose density and minimum-size rules;
- graph methods choose neighbors, edge weights, and resolution;
- probabilistic topic models choose priors and model form;
- hierarchical methods choose where the hierarchy is cut.

[Kleinberg's clustering result](https://papers.nips.cc/paper_files/paper/2002/hash/43e4e6a6f341e00671e123714de019a8-Abstract.html)
shows that a distance-based clustering function cannot simultaneously satisfy
its scale-invariance, richness, and consistency axioms. Methods that infer a
topic count move the choice into assumptions; they do not reveal a unique
solution under those axioms. This theorem does not prove that no objectively
correct human subject map exists.

## Evidence That Corpus-Induced Regions Are Plausible

[Top2Vec](https://arxiv.org/abs/2008.09470) embeds documents, reduces the
geometry, finds dense regions, and derives topic words from those regions. It
does not require a predefined topic count and can reduce the discovered topics
into a hierarchy.

[BERTopic](https://arxiv.org/abs/2203.05794) follows a related
embedding-to-density-cluster pipeline and derives descriptions with
class-based TF-IDF. Both demonstrate automatically derived topic clusters and
descriptions after documents are represented. They do not establish that those
clusters match human-recognized subjects.

Direct clustering has competitive published results.
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

Spherical k-means partitions normalized vectors by cosine geometry.
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
navigation interface. Its demonstrated properties include:

- operates on embedding relationships;
- produces reusable multiple granularities;
- has a million-scale hierarchy benchmark;
- separately has human evaluation of fine-grained flat query clusters;
- does not require predefined subjects or a fixed region count.

It still makes consequential choices. Its published benchmarks used a 25-NN
ScaNN graph, a 200-threshold schedule, and a selected hierarchy cut. More
generally:

- the neighbor graph defines which relationships exist;
- thresholds define the hierarchy;
- membership is hard and nested;
- hubs and outliers can still be assigned misleadingly;
- no result establishes Nostr subject fidelity.

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

The reviewed evidence does not establish its behavior on a million-scale
short-note corpus.

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

The reviewed studies establish scalability and graph-partition properties, not
that graph communities correspond to useful Nostr subjects.

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
introduce a bag-of-words or token representation instead of operating only on a
single frozen document embedding. Short informal notes are sparse, and topic
priors still determine the resulting structure.

[FASTopic](https://proceedings.neurips.cc/paper_files/paper/2024/hash/998f8d8ff2697da2eae5f87143668754-Abstract-Conference.html)
combines frozen document embeddings, learned topic prototypes, and soft
document-to-topic weights. It requires a chosen topic count, materializes
document-topic relations, was evaluated at much smaller scale, and lacks human
navigation evidence.

### Sparse topic atoms over document embeddings

[SAE-TM](https://arxiv.org/abs/2511.16309) derives the sparse-autoencoder
objective as maximum a posteriori inference in a continuous topic model. It
trains a sparse autoencoder over document embeddings, interprets learned
features as reusable topic atoms, and merges those atoms into different
numbers of topics without retraining the autoencoder. A document may activate
several atoms.

Its text experiments used News-20K, IMDB, Yelp, DailyMail, and a filtered
Twitter corpus containing 1,183,728 tweets. The Twitter experiment excluded
tweets without at least seven non-stopword lemmas among the 5,000-word
vocabulary, so its reported result does not cover the shortest and sparsest
social posts. The paper used Granite-R2 document embeddings and evaluated
topic coherence, diversity, and document-topic relevance primarily with
automatic and LLM judgments.

SAE-TM reported higher topic-coherence scores than the tested baselines and
second-place topic diversity. Its Phi-4 relevance evaluation reported 66.5%
accuracy when distinguishing one active from one inactive topic, but only
38.3% of active topics were judged relevant to their documents, compared with
29.0% for the strongest baseline. It did not provide a corpus hierarchy,
human-validated exhaustive membership for mixed short posts, or a navigation
study.

[BatchTopK sparse autoencoders](https://arxiv.org/abs/2412.06410) relax fixed
per-sample TopK activation to a batch-level sparsity budget. The method permits
different samples to activate different numbers of features while controlling
average sparsity. Its published evaluation concerns reconstruction of language
model activations, not document topic recovery.

## One Note, Several Subjects

A whole-note embedding is one point. If that point is between two regions,
multiple weights can mean either:

1. the note genuinely contains both subjects; or
2. the model is uncertain which single subject fits.

Soft membership over one pooled representation does not by itself identify
which interpretation is correct. GMM, von Mises-Fisher, fuzzy, and HDBSCAN
membership scores describe proximity or uncertainty around that pooled
representation; additional evidence is needed to interpret several memberships
as compositional meaning.

[Semantic Component Analysis](https://aclanthology.org/2025.findings-emnlp.964/)
is the most direct reviewed attempt to recover several semantic components
from whole-document embeddings. Each iteration clusters residual embeddings
and subtracts each sample's projection onto its assigned centroid component.
It was tested on up to 1.463 million tweets and produced multiple components
with competitive automatic metrics.

Its reported evidence has these limits:

- it had no navigation user study;
- component count varied substantially with configuration;
- generic components could be over-assigned;
- activation scores were not calibrated as a share of meaning;
- it assumes semantic meanings can be separated as vector directions.

Token- or span-level approaches such as
[contextual token clustering](https://arxiv.org/abs/2010.12626) and
[Contextual-Top2Vec](https://aclanthology.org/2024.findings-emnlp.790/) can
associate different text spans with different regions, preserving source-text
provenance for each assignment. They require token- or span-level
representations and note-level aggregation. The reviewed work did not report
compute or storage measurements at Nostr scale.

No reviewed evidence establishes whether a whole-note representation preserves
enough separable information for faithful multi-subject membership on Nostr
notes. No reviewed evidence establishes that a span-level representation is
necessary for them either.

## Hierarchy Evidence

[Stability analysis](https://arxiv.org/abs/1404.4606) can identify brittle
resolutions by comparing results across seeds or corpus perturbations.
[Clustering-stability research](https://arxiv.org/abs/1007.1075) also warns
that stability alone can favor the wrong structure. Stability does not
establish semantic correctness.

[BoxTM](https://aclanthology.org/2024.tacl-1.77/) represents topics and words
as boxes whose volume models semantic scope. It uses a symmetric overlap
measure for relatedness and an asymmetric containment measure for broad-to-
narrow relations, then recursively constructs upper-level topics from lower-
level topics. Its document encoder consumes TF-IDF representations, and the
paper does not establish scale or human navigation quality for millions of
short social notes.

[Hierarchical Overlapping Clustering](https://proceedings.mlr.press/v267/pan25a.html)
constructs an overlapping hierarchy in which an item may have multiple
parents. The paper reports processing a graph with 1.13 million nodes and 2.99
million edges in under 12 minutes on an 8 GB machine. Its semantic hierarchy
quality was evaluated on synthetic data; the real datasets supplied scale
evidence rather than human semantic validation.

These papers establish two distinct hierarchy mechanisms: asymmetric semantic
containment and scalable overlapping graph structure. They do not establish
that either mechanism yields correct parent-child subjects for Nostr.

## Evidence About Labels

A plausible label does not establish region coherence, note-to-region
membership, or hierarchy quality. Those are separate empirical claims.

[Human topic-label research](https://aclanthology.org/Q17-1001/) found the
tested automatic labels weaker than human labels and evaluated labels against
the documents they described. Reviewed labeling methods use representative
members, distinctive words or phrases, and contrasts with nearby topics as
inputs. The literature does not establish that a fluent generated label is
faithful to all members of its region.

## Human Validation

Automatic coherence, clustering loss, likelihood, and stability are
insufficient by themselves to establish whether regions are useful subjects.

[Reading Tea Leaves](https://proceedings.neurips.cc/paper_files/paper/2009/hash/f92586a25bb3145facd64ab20fd554ff-Abstract.html)
found that likelihood can prefer topics people find less interpretable.
[Hoyle et al.](https://proceedings.neurips.cc/paper/2021/hash/0f83556a305d789b1d71815e8ea4f4b0-Abstract.html)
found that automatic coherence measures can select winners that human
judgments do not support.

The reviewed evidence evaluates different claims with different instruments:
topic coherence, document-topic relevance, hierarchy quality, label quality,
stability, or downstream task performance. No reviewed metric jointly
establishes region coherence, complete mixed-note membership, correct
hierarchy, faithful labels, and useful navigation. The project evaluation
proposal is therefore recorded separately from this evidence review.

## Comparison

| Family | Input | Membership and hierarchy | Evidence boundary in reviewed work |
| --- | --- | --- | --- |
| Spherical/bisecting k-means | Normalized point vectors | One hard assignment per level; recursive splits can form a tree | Method properties; no Nostr evaluation |
| SCC | Nearest-neighbor graph over point vectors | Hard nested hierarchy | 1.3M-point ImageNet hierarchy benchmark; separate human review of flat proprietary query clusters |
| HDBSCAN | Usually reduced point vectors | Density hierarchy, noise state, and soft membership scores | Human study on 10K news articles; SCC study did not scale it to 1.3M points |
| Leiden | Weighted graph | Flat hard communities per resolution | Scalable graph partitioning; no reviewed Nostr subject evaluation |
| LDA/HDP/nHDP | Token counts | Mixed word-level topics; nHDP supplies a shared hierarchy | nHDP reported 2.7M Wikipedia documents; bag-of-words representation |
| FASTopic | Document embeddings and learned topic prototypes | Soft flat topic weights | Chosen topic count; no reviewed human navigation study |
| SAE-TM | Document embeddings | Sparse atom activations; atoms can be merged after training | 1.18M filtered tweets; automatic and Phi-4 evaluation; no hierarchy study |
| BatchTopK SAE | Model activations | Variable active-feature count; no topic hierarchy | Reconstruction evaluation on language-model activations |
| SCA | Whole-document embeddings | Several residual semantic components; flat | Up to 1.463M tweets; automatic evaluation |
| Contextual token/span methods | Contextual token or span embeddings | Span-level topic assignments; Contextual-Top2Vec merges topics hierarchically | Evaluated on corpora up to 50K documents; primarily automatic evaluation |
| BoxTM | TF-IDF documents and learned word/topic boxes | Soft topic mixtures and asymmetric topic hierarchy | Intrinsic, extrinsic, and limited human evaluation; no million-note study |
| Hierarchical overlapping clustering | Graph | Overlapping hierarchy with multiple parents | 1.13M-node scale result; semantic quality evaluated synthetically |

## Questions the Literature Does Not Decide

The reviewed evidence does not decide:

- which text representation preserves the subjects that people perceive in
  short, informal Nostr notes;
- whether one whole-note embedding can support faithful multi-subject
  membership;
- whether sparse topic atoms, contextual spans, probabilistic topics, or
  another construction yields faithful subjects for short notes;
- how many useful granularities exist in the corpus;
- whether broad-to-narrow relationships require a tree or overlapping graph;
- which residual or outlier policy preserves rare notes without inventing
  subjects;
- whether generated labels predict the contents of their regions;
- whether any resulting map improves user-directed discovery.

Those are project decisions and empirical questions. The current project
hypothesis is documented separately; it is not a conclusion of this review.
