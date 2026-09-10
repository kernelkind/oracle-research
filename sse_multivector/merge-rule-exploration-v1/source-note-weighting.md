# Source-note weighting

## Question

M05 revealed that two overlapping masks from N010 can constitute the median majority when a third note joins a group. Their shared source is known. They are not two independent notes, although they are two different vectors. Would giving each source-note pair equal weight produce more useful hierarchy memberships?

This is a weighting question, not evidence that the restaurant group is invalid. It is also not a new requirement that every note must count equally. Multiple masks can represent genuinely different meanings as well as redundant ones.

## Relevant research

Zhang and Zhou's BAMIC clusters whole bags with k-medoids and Hausdorff-type distances. Its ordinary-instance comparators can split bags; **evaluation** then weights each instance by inverse bag size so each source bag has total weight one. That is not their merge rule. The Musk and synthetic results compare agreement with known bag labels, not overlapping note discovery. This supplies precedent for distinguishing objects from their instances, but importing whole-bag clustering would violate our vector-level architecture.[^1]

Cheplygina, Tax and Loog compare point-set, distribution and graph dissimilarities as features for supervised bag classification. Their §5.3 explicitly distinguishes informative bag size from sampling variation: sums can help when size predicts a class; averaging can be preferable otherwise. Their results favor different measures on different datasets. Thus removing multiplicity is an application hypothesis, not a universal correction. Their existing MIL/PRTools implementation performs a different downstream task; the dissimilarity definitions inform this experiment, not a classifier substitution.[^2]

Jégou and Zisserman's democratic aggregation addresses unequal contributions of local image descriptors. It solves positive weighting equations using a modified Sinkhorn procedure. In their image-search experiments, aggregation improves the triangulation representation, while gains with Fisher vectors are smaller and not universal. Similar repeated descriptors can still dominate, and their implementation adds power normalization. These findings make redundancy a credible mechanism to inspect, but do not establish a semantic linkage rule. Re-embedding, whitening or aggregating each note into one vector would change this experiment's frozen geometry and is not adopted.[^3]

## M06 definition, before running

Relative to M04, change only the averaging weights:

1. Collect the permitted vector-to-vector distances between the two candidate groups.
2. Group these distances by their **unordered source-note pair**. If both notes occur in both groups, pool both orientations under the same pair.
3. Average the distances within each source-note pair.
4. Average those pair means equally. The smallest current score merges next.

For example, if two N010 masks connect to N050 and one N057 mask connects to N050, M04 gives N010–N050 two of three pair votes. M06 gives the N010–N050 mean and the N057–N050 mean one vote each.

This is not WPGMA: child groups do not receive equal recursive weights. It is not a minimum match per note. Every permitted distance still contributes within its source-note pair. It is not equal weight per note either: a note participating in more distinct note pairs participates in more terms. No masks are removed or forced to stay with their source note.

The frozen input has exactly one source note per canonical vector, including its aliases. Require that condition explicitly for this experiment; do not invent an attribution policy for a future multi-source canonical vector. Source labels are read from the existing frozen provenance. The distance matrix and exclusions remain authoritative and unchanged.

Recompute changed group scores exactly, retaining global smallest-score selection, deterministic ties and genuine score decreases. Do not assume an average-linkage recurrence or monotonic merge heights. First test the definition, overlapping source-note sets, equal weighting of unequal pair counts, and the complete history against an independent exhaustive implementation. Existing tests and all previous saved histories must remain unchanged.

## Fixed-state evidence

These calculations use actual saved groups and fixed distances, before any M06 run. Lower scores merge earlier. They compare available choices at an existing state, not a predicted full history.

| Existing state | Other vector | Permitted distances | Source-note pairs | M04 mean | Equal mean of note-pair means |
| --- | --- | ---: | ---: | ---: | ---: |
| M05/1403 | V399 · absent pizza venue | 3 | 2 | 1.138234 | 1.174750 |
| M05/1403 | V484 · barbecue-chain closures | 2 | 1 | 1.074608 | 1.074608 |
| M04/1659 · regional meals | V518 · Christmas lunch | 4 | 2 | 1.233848 | 1.233848 |
| M04/1669 · Christmas | V518 | 10 | 4 | 1.243088 | 1.249759 |
| M04/1402 · tasks | V549 · missed photographs | 1 | 1 | 1.105920 | 1.105920 |
| M04/1490 · art | V549 | 5 | 2 | 1.265650 | 1.253537 |

This change does **not** repair the known Christmas or photography choice at those fixed states. It would also oppose M05's useful restaurant extension at its motivating state. The reason to run it is to test source multiplicity across the complete hierarchy, not to fit these examples or assume that this weighting will win.

## Interpretation boundaries

Equal source-pair weight may reduce the influence of repeated masks, but can increase the influence of a weak singleton connection from another note. Replicating an entire note's identical set of masks at a fixed comparison need not change its pair mean; selectively repeating only one of its different meanings can still change that mean. The actual tree can change earlier than either comparison. Neither statistical independence nor complete duplicate invariance is claimed.

Inspect newly created and lost note relationships, plus complete nested structure, before judging usefulness. Preserve M01/M04/M05 tradeoffs and check alternate masks. The existing broad-root and sparse-fragment problems may survive unchanged.

## Sources

[^1]: Min-Ling Zhang and Zhi-Hua Zhou, *Multi-Instance Clustering with Applications to Multi-Instance Prediction* (2009), §§3.1–3.2, especially Eq.7 and the evaluation weights before Eqs.8–9. [Author PDF](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/apin09.pdf).
[^2]: Veronika Cheplygina, David M. J. Tax and Marco Loog, *Multiple Instance Learning with Bag Dissimilarities*, arXiv v3 (2014), §§3.1, 5.1–5.4. [Paper](https://arxiv.org/pdf/1309.5643).
[^3]: Hervé Jégou and Andrew Zisserman, *Triangulation Embedding and Democratic Aggregation for Image Search* (CVPR 2014), §§4–5, Table1 and supplemental algorithm. [Author PDF with supplement](https://www.robots.ox.ac.uk/~vgg/publications/2014/Jegou14/jegou14.pdf).
