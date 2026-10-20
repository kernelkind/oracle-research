# Hierarchy Construction from SSE Vectors

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../experiments/README.md#reading-the-research-records).

## Scope and conclusion

This review keeps SSE, the source notes, and their existing masked-subject vectors fixed. It examines alternative ways to organize those vectors into a browsable hierarchy of notes. It does not select a replacement encoder, generate category labels, or declare a hierarchy algorithm validated. Sources and repository evidence were checked on 2026-09-10.

The strongest immediate candidates are **hierarchical Infomap**, **nested stochastic block models**, and **recursive spectral partitioning**. They test different explanations for the current problems: insufficient use of collective connections, an inadequate whole-hierarchy objective, and early bottom-up commitments. Infomap and nested block models also permit revising assignments rather than preserving every initial merge.

This is a ranking of experiments worth doing, not a demonstrated ranking of semantic quality. None of the reviewed sources establishes that its method produces consistently accurate, increasingly specific categories for mixed short notes represented by SSE. The literature supports continuing geometric investigation; it does not establish either its sufficiency or its impossibility.

## The output that matters

The goal is a hierarchy in which choosing a child gives a more specific description of the notes returned, while remaining consistent with the descriptions above it. A smaller set of vectors is not automatically a narrower subject. A coherent child is not automatically correctly placed beneath its parent.[^1]

A note can contain several subjects. A category need not describe everything in the note; the note must actually support the meaning offered by that category and its path. Another subject in the same note does not make every category containing that note a valid parent of its other subjects.

The current design permits broad, narrow, nested, and overlapping subjects. There is no requirement to discover a uniformly fine layer first. Nor must every geometric group become a visible category. Category naming, membership construction, and choosing which existing groups to display remain separate responsibilities, even if one algorithm contributes to several of them.[^1]

Two kinds of containment must be distinguished:

- **Set containment:** every note returned under a child is also included in its parent.
- **Meaning:** the child's subject is a more specific version of the parent's subject, and the notes support that interpretation.

Mapping a vector tree back to note IDs can guarantee the first. It cannot guarantee the second.

## What the existing results actually establish

The current comparison contains 100 notes, 916 distinct vectors, and 945 original mask records. HDBv2, HDBv3, and the later merge-rule experiments are different saved results, not interchangeable names for one algorithm.[^2][^3]

| Observation | Supported conclusion | Conclusion not established |
| --- | --- | --- |
| Removing same-note connections in HDBv3 changed the coffee/egg placement while preserving the vector inputs. | Connection eligibility can materially affect ancestors. | Every same-note connection is harmful, or the new tree is correct everywhere. |
| The chicken-stock vectors split into two pairs, but both pairs still return both original notes. | Exact vector membership changed. | Relevant notes became undiscoverable. |
| The six-mask chocolate/tea group exists in the raw history but is not separately offered by condensation. | Displayed groups can omit useful memberships that already exist. | The vector relationships or merge history lack that group. |
| The allotment rejection was retracted after inspecting the complete note. | The displayed mask omitted the concrete gardening evidence. | HDBSCAN made that grouping incorrectly. |
| The greeting/jar, literature/audiobook, and gift/Christmas memberships remained rejected after full-note inspection. | Those memberships are unwanted. | Their causes have been isolated to SSE or to HDBSCAN. |
| M06's smallest group containing the five accepted coffee-preparation notes contains 19 notes. This also holds when allowing any mask from each note. | Pruning M06 cannot reveal a smaller group containing those five notes. | This exact five-note category is the only acceptable hierarchy, or the merge rule alone caused its absence. |

The first five observations are documented in the saved HDB review; the coffee comparison is recorded separately.[^2][^4]

M01–M09 already explored nearest-partner means and sums, all-pairs means and medians, equal source-note-pair weighting, PARIS normalization, and a worst-supported-nearest-partner rule. They produce complementary useful groups and regressions. Shorter trees and complete numerical replays do not constitute semantic approval.[^3]

In particular, M07 already uses connections to the rest of the graph. It would be incorrect to describe every prior experiment as using only one isolated cosine. The genuinely different questions now concern collective partitioning, reassignment, and the objective used to choose a whole hierarchy—not simply whether another normalization exists.

## What keeping SSE fixed allows

Each vector remains attached to its original note and exact mask. An algorithm may use the existing coordinates, their distances, or a graph constructed from those relationships. No additional language-model inference is required for the shortlisted grouping algorithms.

Cosine uses all vector dimensions. For normalized vectors, the complete cosine matrix is their Gram matrix: it determines their relative Euclidean geometry up to an orthogonal transformation. Computing cosine therefore does not, by itself, reduce the entire corpus to one dimension. A single pair score is limited evidence; the complete pattern of pair scores contains much more structure.

The important choices are which relationships to retain and what organization to infer from them. Replacing cosine with Euclidean distance on normalized vectors preserves pairwise ordering, although nonlinear transformations can still change sums, weights, and algorithm outputs. That alone does not add semantic evidence.

A similarity graph has one vertex per existing vector. An edge records a retained relationship between two vectors, optionally with a nonnegative similarity weight. An MST retains a cycle-free set of connections sufficient for its connectivity hierarchy. A general graph can retain additional connections and alternative routes between groups. A hierarchy algorithm can use these collectively without requiring a subject to occupy one sphere, box, or filled geometric region.

This does not make the graph neutral. Neighbor selection, edge weights, same-note eligibility, and the number of related masks per source note all affect the evidence presented to the algorithm.

## Candidate comparison

| Candidate | What it uses | How it chooses the hierarchy | Principal reason to investigate | Principal limitation |
| --- | --- | --- | --- | --- |
| Hierarchical Infomap | A vector-similarity graph | Nested groups that compress movement along its edges | Uses many connections and can reconsider memberships | Retained movement is not semantic parenthood |
| Nested stochastic block model | A graph and an explicit statistical model for its edges | Nested groups that explain connections economically | Compares whole structures and permits reassignment | Similar connection patterns can describe roles rather than subjects |
| Recursive spectral partitioning | A similarity graph | Repeatedly splits a group using its collective connection pattern | Tests broad-first organization without fixed initial segments | Ordinary recursion cannot undo an earlier split |
| B++&C | Existing vectors under supported similarity/distance formulas | Optimized top-down cuts, then local average linkage | Relevant large-embedding evidence; no encoder training | No verified released implementation located; objective is not semantic accuracy |
| HypHC | Fixed pairwise similarities | Learns auxiliary hyperbolic coordinates, then decodes a tree | Searches a whole-tree objective with released code | Additional optimization; limited directly relevant evaluation |

The following sections separate published mechanisms from their proposed use with SSE.

## 1. Hierarchical Infomap

**Published mechanism.** Imagine movement from one graph vertex to another, with stronger edges making a move more likely. Infomap seeks nested groups that make these movements economical to describe. A useful group contains repeated internal movement; a useful parent captures additional regularity among its children. Extra levels must improve the description. The hierarchy need not have a prescribed depth or binary branching.[^6]

Its optimization is not just a permanent merge sequence. It can move individual vertices between groups, subdivide groups and move the subdivisions, and search for additional coarser or finer levels. These operations still use heuristic optimization; they do not guarantee the globally best solution.[^7]

**Proposed SSE use.** Construct an explicit similarity graph over the existing vectors. Run the multilevel method, retain its memberships, and resolve each group to distinct source notes for inspection. Do not first freeze HDBSCAN groups as indivisible inputs: that would prevent this test from correcting their memberships.

**Why this is the first candidate.** It directly tests whether several reinforcing connections can support a parent that an irreversible merge history misses. Its capacity to move members is materially different from pruning a tree or changing one pairwise merge statistic. It also avoids prescribing geometric shapes for parent regions.

**Evidence and limitation.** The original study recovered recognizable scientific fields and broader disciplines from journal citations. But in its disease network, useful lower groups did not generally produce natural higher classifications; only the cancer parent matched one. This is unusually relevant counterevidence against assuming good children imply good parents.[^6]

Those networks contain observed relationships, not SSE similarities. For notes, the proposed movement is a mathematical device—not measured reader behavior, and not a model of the user's current interests.

**Computing and availability.** The maintained author implementation provides C++ and Python interfaces, repeated trials, and saved hierarchical outputs. It requires graph computation, not pretrained model weights or frontier calls. Sparse-graph memory and repeated-search runtime should be measured on the frozen pilot before scaling.[^8]

## 2. Nested stochastic block models

**Published mechanism.** Assign graph vertices to groups and model how often edges occur within and between them. Then group that pattern of group-to-group connections at another level, repeating to form a hierarchy. Model selection balances how well the graph is explained against the cost of describing the model. Degree correction separately accounts for variation in how many connections individual vertices have.[^9]

Inference can revise group assignments and the number of groups or levels. Current graph-tool documentation also supports merge-split refinement and sampling alternative partitions. For continuous edge strengths, it provides explicit weight distributions; similarity values should not silently be treated as integer edge counts.[^10]

**Proposed SSE use.** Use the same declared graph as the other graph candidates. Compare the fitted hierarchy through its actual masks and note memberships. Do not declare degree correction automatically right: a high-degree vector might be a generic subject, a repeated formulation, or a useful bridge, and those explanations have different meanings for discovery.

**Why it is worth comparing.** This tests a substantially different whole-graph explanation. It can also expose competing plausible assignments instead of presenting one tree as certain. Variation among sampled or independently fitted structures would diagnose ambiguity in this model, not prove that the semantic interpretation is ambiguous.

**Critical limitation.** A general block model permits groups with similar connection roles, including structures that are not internally cohesive. A statistically economical group is not necessarily a common topic. Degree correction does not remove that mismatch.[^9]

**Document evidence.** A related hierarchical SBM topic model was tested on real corpora including 10,000 tweets and illustrated nested biology/physics groups in 63 Wikipedia articles. However, its inputs were word–document occurrence graphs. Its statistical advantages over LDA do not establish semantic superiority on an embedding graph, or successful note navigation.[^11]

**Computing and availability.** graph-tool provides a maintained compiled implementation. Its documented nested-model initialization/optimization wrapper has an approximately `O(E log² V)` complexity bound, where `E` is edge count and `V` is vertex count; additional refinement and sampling cost extra. This is corpus-specific statistical fitting, not language-model training.[^12]

## 3. Recursive spectral partitioning

**Published mechanism.** Start with the graph for all input vectors. Test whether there is evidence for more than one group. If there is, compute a split from the collective connection matrix and repeat separately inside each resulting group. Spectral methods obtain this split from eigenvectors—numerical directions summarizing the matrix's connection pattern. Stop where the chosen evidence test no longer supports another split.[^13]

**Proposed SSE use.** Keep the same vector graph, use a published split method and stopping rule, and preserve every generated group. This does not depend on first discovering fine segments. It tests whether establishing broader separations before local subdivisions gives more useful ancestors.

**Reason for lower priority.** A wrong early split is permanent in ordinary recursion. The reviewed formulation is binary, and its stopping test answers a graph-structure question rather than whether further subjects would be meaningful.[^13]

The literature proves recovery under particular hierarchical random-graph models. That is useful evidence about the algorithm, but an embedding-neighbor graph has geometric dependencies and is not known to satisfy those models. The empirical examples include gene co-occurrence and researcher citation networks, not the required note-browsing task.[^13][^14]

**Computing and availability.** This is numerical matrix/graph computation, with no pretrained weights or encoder training. The authors provide an R implementation. Its defaults include a non-backtracking stopping rule and a minimum-size stopping condition; they are not automatically suitable for this pilot.[^15]

**Input compatibility.** The stopping rule must match the graph: the reviewed non-backtracking test assumes unweighted adjacency, whereas edge cross-validation can handle weighted networks under a low-rank assumption. A shared weighted graph cannot simply be passed through the default configuration. Use a compatible declared test, or treat conversion to unweighted adjacency as an explicit separate comparison.[^13]

## Other plausible options

### B++&C and HypHC: optimize a tree objective

B++&C recursively searches for cuts that minimize crossing similarity or maximize crossing distance, then uses average linkage below a size threshold. Its kernel formulation can avoid explicitly storing all pairwise relationships. Published tests include millions of word vectors and SST-2 sentence embeddings; these are useful compatibility and scale results. Sentence evaluation concerns sentiment labels, not increasingly specific topical categories.[^16]

No verified released B++&C implementation was located in the inspected paper or author pages. It therefore ranks below immediately reproducible candidates for the pilot. Its split-size preference and supported kernel formulas also need scrutiny before transplanting the current excluded-edge policy.

HypHC instead optimizes auxiliary hyperbolic coordinates and decodes them into a binary hierarchy. SSE stays frozen: the extra coordinates are a representation of the proposed tree, not a replacement language encoder. Released PyTorch code makes it reproducible. The paper uses sampled triples, 50 training epochs, and a P100 GPU; its principal benchmark is a similarity-based tree cost, not human judgment of note categories.[^17][^18]

For either method, improving its objective is not sufficient evidence of a better browsing hierarchy. The B++&C study itself reports high raw objective scores for random trees and introduces a normalization to measure improvement over that baseline. Its large-scale evidence should not be summarized as millions of semantically validated categories.[^16]

A newer continuous-hierarchy method, HypCSE, also combines graph learning and hyperbolic optimization. Its reported benchmarks do not establish the missing note-level semantic evidence. Additional trainable components are not presently justified by a clearer fit to the task.[^19]

### Overlapping link communities

Link-community clustering groups graph edges rather than vertices. A vector inherits the groups of its incident edges, allowing it to participate in overlapping groups while the edge groups have a hierarchy. The original paper includes meaningful overlapping structures in a word-association network. However, its construction still uses single-linkage merging, and similarity edges are not known to each express one distinct subject.[^20]

Overlap among **notes** already follows from their multiple vectors; it does not require this method. Overlap for a **single vector** is an additional option, not a consequence that must be imposed. Investigate it only if the evidence identifies valid competing placements that cannot be served by other vectors from the same notes.

The original partition-density objective also requires caution: later work shows that directly optimizing it tends to favor tiny triangular communities. That criticism concerns the objective and its direct optimization, not a proof that every hierarchy produced by the original procedure is invalid.[^21]

### CHAMELEON and further merge rules

CHAMELEON compares connections between candidate groups with connectivity inside those groups. That is a legitimate unresolved source of evidence. But the original method requires a sparse graph and initial subgroups; it is not simply a formula that can be inserted unchanged into the existing singleton-based dense comparison.[^5]

The repository's review also found materially different implementations and size effects when adapting their edge counts to the current graph. This justifies careful specification, not rejecting the family. It is lower priority because it adds graph and initialization choices while retaining irreversible merging.[^5]

### Other methods from the earlier shortlist

**Hierarchical Felzenszwalb–Huttenlocher segmentation** constructs nested regions by comparing boundary differences with internal variation and region size. The reviewed hierarchical variant computes new observation-scale weights on an MST. Its image results support a legitimate segmentation mechanism, not the earlier suggestion that it was already the best semantic-hierarchy architecture. It remains worth investigating if boundary evidence is the targeted hypothesis, but does not supply the collective reassignment tested by the leading candidates.[^23]

**Agglomerative Information Bottleneck** merges groups while minimizing loss of information about a supplied relevance variable. With SSE, a distribution over semantic neighbors could play that role, but defining it would be an additional modeling choice. This is another meaningful use of surrounding relationships, not independent language understanding, and ordinary agglomeration still makes permanent merges.[^24]

**Markov Stability** compares partitions by how movement remains within groups over different time scales. It is useful for identifying persistent groupings. Independently optimizing partitions at different scales does not itself enforce that every smaller group is contained in one larger group; assembling a strictly nested result therefore needs explicit treatment. It remains a multiscale comparison option rather than an immediate complete hierarchy solution.[^25]

## Graph construction is a separate hypothesis

The current dense eligible graph and a sparse semantic-neighbor graph are different inputs. Missing edges in the former mean the pair was forbidden by source-note policy; missing edges in the latter may mean it was not sufficiently local. Those meanings must not be conflated.

A practical comparison can begin with a declared nearest-neighbor construction, and later contrast it with a local-density-adjusted graph. CkNN is one documented option: connect two points when their distance is below a scale factor times the geometric mean of their local neighbor distances. Its theory concerns sampled manifolds and asymptotic geometric consistency, not semantic category correctness. The current source-note restrictions do not automatically inherit those guarantees.[^22]

Graph choices should be tested with the hierarchy method fixed; algorithm choices should be tested on the same graph. If a graph is disconnected, preserve and report that fact instead of quietly inventing edges to obtain one semantic root. A corpus root can collect unrelated components without claiming a common subject.

A few important controls follow from the existing evidence:

- Preserve source-note identities, exact masks, vector aliases, and existing duplicates policy.
- Specify whether edge weights represent similarity, distance, or a statistical covariate. These are not interchangeable inputs.
- Do not automatically treat many overlapping masks from one note as many independent notes supporting a connection.
- Inspect graph changes as well as hierarchy changes. A new useful group could result from changed edges, not the hierarchy method.
- Avoid simultaneous re-embedding, dimension reduction, graph replacement, and hierarchy replacement when attributing an improvement.

These are proposed experimental controls, not a frozen graph configuration.

## Interpreting a future comparison

The primary question is whether actual memberships support accurate narrowing descriptions. A generated title cannot establish that; inspection must retain source masks and full notes. Statistical fit, compression, separation, and stability are useful diagnostics, but not substitutes for this judgment.

The evaluation should distinguish three outcomes:

1. A useful membership exists in the generated hierarchy and is visible.
2. It exists but display selection or note-set simplification hides it.
3. It never exists in the generated hierarchy, so rearranging the display cannot recover it.

At each inspected group, trace the relevant vectors back to distinct notes. Before claiming a lost discovery path, check alternate masks from those notes. Before claiming that reuniting vectors improves discovery, check whether it adds any relevant note or meaning that was previously unavailable.

The accepted coffee arrangement provides one concrete positive example, not the only allowable answer. Other coherent organizations should be admitted. Likewise, a category need not exclude disagreement, or require every note to express the same claim. The test is the subject relationship offered by the path.[^4]

Broad notes may remain available at a broader visible category without being forced into an unsupported specific one. A computational tree whose leaves are vectors does not require displaying those leaves as maximally narrow semantic categories. Equal note sets, one-note choices, and presentation depth should remain separately inspectable rather than silently changing memberships.

## Recommendation

Prioritize **hierarchical Infomap**, with **nested stochastic block models** as the most distinct challenger and **recursive spectral partitioning** as a useful broad-first control. Retain HDBv3 and the strongest existing M01/M06/M07 memberships as comparisons, not as accepted ground truth. B++&C and HypHC remain credible later objective-based alternatives.

The proposed first comparison should use the existing corpus and unchanged SSE vectors. Establish the graph contract before running it, keep the output memberships unaltered, and inspect both useful local groups and their parents. Do not begin by repairing labels or aggressively pruning the hierarchy: that would obscure which organization the algorithm actually produced.

The central research question is now concrete: **can an algorithm using the wider pattern of SSE relationships—and, for the first two candidates, revisable assignments—produce more accurate parent placement than the saved irreversible merge histories?** A positive result would support this approach. A negative result would narrow the explanation only after graph construction, note projection, and known extraction/representation errors are accounted for.

No candidate has been run or selected by this review.

## Sources

[^1]: Repository design, [Atomic-Subject Content Hierarchy](../design/atomic-vector-subject-hierarchy.md), especially Status, Goal, Separation of Concerns, and hierarchy membership requirements. Snapshot inspected 2026-09-10.
[^2]: Repository experiment, [Cross-note density and HDBv3 results](../../../sse_multivector/real-note-fine-segmentation-v1/cross-note-density-v1/README.md), especially contextual re-examination, HDBv3, and optional note-navigation comparison. Snapshot inspected 2026-09-10.
[^3]: Repository experiment, [Merge-rule exploration M01–M09](../../../sse_multivector/merge-rule-exploration-v1/README.md), individual results and comparison table. Snapshot inspected 2026-09-10.
[^4]: Repository comparison, [Merge rules: results to inspect](../../../sse_multivector/merge-rule-exploration-v1/inspection.md), Manual coffee example and Coffee preparation compared with M06; underlying comparison artifact (`../../../sse_multivector/manual-coffee-hierarchy-v1/m06-comparison.json`). Snapshot inspected 2026-09-10.
[^5]: Repository source audit, [Within-child structure after M09](../../../sse_multivector/merge-rule-exploration-v1/within-child-structure.md), including primary-paper links and pinned implementation comparisons. Snapshot inspected 2026-09-10.
[^6]: Martin Rosvall and Carl T. Bergstrom (2011), [Multilevel Compression of Random Walks on Networks Reveals Hierarchical Organization in Large Integrated Systems](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0018209), PLOS ONE 6(4), e18209. Hierarchical map equation and real-network results; [full manuscript](https://arxiv.org/html/1010.0431).
[^7]: Daniel Edler, Ludvig Bohlin and Martin Rosvall (2017), [Mapping Higher-Order Network Flows in Memory and Multilayer Networks with Infomap](https://arxiv.org/html/1706.04792), §§4.3–4.5 and Algorithms 5–6.
[^8]: Infomap authors, [official implementation](https://github.com/mapequation/infomap), README installation and usage documentation. Checked 2026-09-10.
[^9]: Tiago P. Peixoto (2014), [Hierarchical Block Structures and High-Resolution Model Selection in Large Networks](https://arxiv.org/html/1310.4377), Physical Review X 4, 011047; model, inference, and non-assortative structures.
[^10]: graph-tool authors, [Inferring modular network structure](https://graph-tool.skewed.de/static/docs/stable/demos/inference/inference.html), hierarchical partitions, merge-split refinement, posterior sampling, and edge weights/covariates. Checked 2026-09-10.
[^11]: Martin Gerlach, Tiago P. Peixoto and Eduardo G. Altmann (2018), [A Network Approach to Topic Models](https://arxiv.org/html/1708.01677), Science Advances 4, eaaq1360; real-corpus comparisons and Wikipedia example.
[^12]: graph-tool authors, [`minimize_nested_blockmodel_dl`](https://graph-tool.skewed.de/static/docs/stable/autosummary/graph_tool.inference.minimize_nested_blockmodel_dl.html), API and complexity notes. Checked 2026-09-10.
[^13]: Tianxi Li, Lihua Lei, Sharmodeep Bhattacharyya, Koen Van den Berge, Purnamrita Sarkar, Peter J. Bickel and Elizaveta Levina, [Hierarchical Community Detection by Recursive Partitioning](https://arxiv.org/html/1810.01509), manuscript first posted 2018; §§2.2–2.3, §5, and Appendix F.
[^14]: Lihua Lei, Xiaodong Li and Xingmei Lou, [Consistency of Spectral Clustering on Hierarchical Stochastic Block Models](https://arxiv.org/abs/2004.14531), manuscript first posted 2020. Recovery guarantees concern specified hierarchical graph models.
[^15]: Tianxi Li, [HCD author-maintained R package](https://tianxili.r-universe.dev/HCD) and [manual](https://tianxili.r-universe.dev/HCD/doc/manual.html), source and package defaults. Checked 2026-09-10.
[^16]: Stanislav Naumov, Grigory Yaroslavtsev and Dmitrii Avdiukhin (2021), [Objective-Based Hierarchical Clustering of Deep Embedding Vectors](https://ojs.aaai.org/index.php/AAAI/article/download/17094/16901), AAAI; [extended manuscript](https://arxiv.org/pdf/2012.08466), including computational methods, objective normalization, and sentence-embedding evaluation. Implementation search also checked the [Avdiukhin](https://dyukha.github.io/publications.html) and [Yaroslavtsev](https://grigory.us/) publication pages; absence of a located release is not proof none exists.
[^17]: Ines Chami, Albert Gu, Vaggos Chatziafratis and Christopher Ré (2020), [From Trees to Continuous Embeddings and Back: Hyperbolic Hierarchical Clustering](https://papers.neurips.cc/paper_files/paper/2020/file/ac10ec1ace51b2d973cd87973a98d3ab-Paper.pdf), NeurIPS; §§3–6.
[^18]: HypHC authors, [official implementation](https://github.com/HazyResearch/HypHC). Checked 2026-09-10.
[^19]: Guangjie Zeng and colleagues, [Hyperbolic Continuous Structural Entropy for Hierarchical Clustering](https://arxiv.org/abs/2512.00524), manuscript first posted 2025 and listed as accepted by AAAI 2026; [full manuscript](https://arxiv.org/html/2512.00524v1), experiments and Appendix E.
[^20]: Yong-Yeol Ahn, James P. Bagrow and Sune Lehmann (2010), [Link Communities Reveal Multiscale Complexity in Networks](https://bagrow.com/pdf/nature09182.pdf), Nature 466, 761–764; method and word-association example.
[^21]: Juyong Lee and colleagues (2017), [Inverse Resolution Limit of Partition Density and Detecting Overlapping Communities by Link-Surprise](https://pmc.ncbi.nlm.nih.gov/articles/PMC5622083/), analysis and numerical experiments on partition-density optimization.
[^22]: Tyrus Berry and Timothy Sauer, [Consistent Manifold Representation for Topological Data Analysis](https://arxiv.org/html/1606.02353), manuscript first posted 2016; CkNN construction and assumptions behind geometric consistency.
[^23]: Silvio Jamil F. Guimarães, Jean Cousty, Yukiko Kenmochi and Laurent Najman (2012), [An Efficient Hierarchical Graph Based Image Segmentation](https://arxiv.org/html/1206.2807), §2 and image experiments.
[^24]: Noam Slonim and Naftali Tishby (1999), [Agglomerative Information Bottleneck](https://papers.nips.cc/paper_files/paper/1999/hash/be3e9d3f7d70537357c67bb3f4086846-Abstract.html), NeurIPS.
[^25]: Jean-Charles Delvenne, Sophia N. Yaliraki and Mauricio Barahona, [Stability of Graph Communities Across Time Scales](https://arxiv.org/html/0812.1811), manuscript first posted 2008; published in PNAS (2010).
