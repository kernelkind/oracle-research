# SSE Fine-Region Partition Pilot

## Status

Executed against the frozen TEv4.1 vectors. The result artifact is
`sse_multivector/fine-region-partition-result-v1/`.

This was a hard, exhaustive partition pilot over the communicated-meaning
vectors produced by TEv4.1. That membership contract belongs only to this
frozen experiment. It is not a requirement for the current fine-segmentation
stage, whose exhaustive, overlapping, hard, or weighted output contract remains
open.

## Question

Can the 194 communicated-meaning vectors from TEv4.1 form nontrivial, coherent
fine regions without preselecting how many regions exist?

This pilot tests only:

```text
TEv4.1 communicated-meaning vectors -> hard fine-subject regions
```

It does not generate region labels or build the hierarchy.

## Frozen input

Use the immutable TEv4.1 archive:

```text
sse_multivector/baselines/communicated-meaning-tev4-1/baseline.tar.zst
```

The pilot consumes its 50 real notes, 194 TPv3.81 takeaways, MPv3.3 source
masks, and 194 normalized 768-dimensional SSE vectors. The archive remains
unchanged.

## Region contract

- Every vector belongs to exactly one region.
- A one-vector region is valid.
- Regions contain vectors, not notes.
- Several vectors from one note may enter different regions.
- No noise or residual bucket exists.
- Generated language must not affect membership.

## Resolution sweep

There is no neutral, parameter-free partition. The pilot therefore does not
pretend to infer one uniquely correct resolution.

For each vector, find its nearest vector from another note. Use the 10th
through 90th percentiles of those 194 cross-note nearest-neighbor cosines as
nine pairwise resolution levels. This spans sparse through strong recurring
relationships without allowing a same-note neighbor to set any vector's
nearest-neighbor value. Notes with more vectors still contribute more values
to the percentile distribution.

The complete-linkage cut at pairwise cosine `s` guarantees that every pair in
a region has cosine at least `s`.

For the corresponding DP-vMF run, use `s` as its native member-to-centroid
cosine threshold. Unlike complete linkage, this does not impose `s` as a
member-to-member bound. The artifact therefore records the actual minimum
member-pair cosine for every DP-vMF region.

An earlier draft used `sqrt((1 + s) / 2)` to halve the permitted angle and
match complete linkage's worst-case region diameter. That was rejected before
interpreting any semantic result: DP-vMF creates a region from one vector, so
the second vector is compared with that first vector, not with their future
midpoint. The half-angle threshold made the scalable method unable to seed any
cross-note region in this dataset. Using `s` exercises the standard DP-vMF
creation and assignment rule on the same observed cosine scale; it does not
claim the two methods have identical region geometry.

The full sweep is diagnostic. The 40th, 50th, and 60th-percentile levels are
the predeclared audit window; using adjacent levels prevents one convenient
cut from determining the conclusion.

## Methods

### Exact reference

Build the complete-linkage hierarchy from all 18,721 exact cosine values and
cut it at every frozen resolution.

### Scalable candidate

Run DP-vMF-means with the same numeric `s` as its native centroid threshold.
This is not matched region geometry. Use a fixed identity order
plus 31 deterministic shuffled orders. Retain every partition and its
coassignment matrix so order dependence remains visible.

No graph clustering, dimensionality reduction, generated labels, or fixed-K
control participates in the result.

## Recorded evidence

For every resolution, record:

- threshold and angle;
- region count and size distribution;
- one-vector regions;
- regions spanning more than one source note;
- minimum and median within-region cosine;
- each member's nearest same-region and nearest other-region vector;
- silhouette as a geometry diagnostic;
- DP-vMF region-count range and pairwise coassignment stability;
- agreement between the exact reference and DP-vMF stable cores.

For the three audit levels, render every cross-note region using only:

- stable vector and note IDs;
- the complete takeaway;
- exact selected source fragments;
- pairwise cosine evidence.

No generated region title may appear in the audit evidence.

## Interpretation

The pilot supports continued work only if a contiguous part of the audit
window contains recurring cross-note regions whose raw member evidence has one
narrow recognizable meaning, while unrelated meanings remain separate.

Automated geometry and stability can expose failures but cannot establish that
meaning. The semantic conclusion must cite concrete member evidence. A
one-vector region is not a failure; it means this 50-note input contains no
demonstrated recurrence for that vector.

## Result

The pilot found real recurring semantic structure, but it did not find a
defensible global hard-partition regime.

The complete-link audit classified every cross-note region from raw takeaways
and exact source masks:

| Resolution | Narrow coherent | Broad or ambiguous | Incoherent |
|---|---:|---:|---:|
| P40 | 8 of 17 | 1 of 17 | 8 of 17 |
| P50 | 8 of 14 | 1 of 14 | 5 of 14 |
| P60 | 6 of 11 | 1 of 11 | 4 of 11 |

Coherent recurring regions included:

- free and open-source software;
- cryptocurrency-miner fan noise and reliability;
- authenticity and remaining true to oneself;
- social conformity suppressing independent thought;
- participation in the same coffee-chain discussion;
- government control of money at P40 and P50.

Persistent false merges included:

- coffee-grinding research with merely drinking coffee;
- proprietary-operating-system surveillance with cross-platform iMessage
  support;
- a secure Signal fork with an argument favoring surveillance;
- reorganizing ideas about unidentified anomalous phenomena with taking a
  lifetime to understand advice about being oneself.

Tightening the exact cut improved precision by fragmentation. P90 contained
three cross-note regions, all coherent, but only 7 of 194 vectors entered a
region spanning more than one source note. All vectors remained assigned, yet
plainly related vectors were split into separate regions and 98 of the 141
regions contained one vector. That is evidence for sparse high-confidence
semantic cores, not for an exhaustive fine-subject map.

DP-vMF did not qualify as the final scalable partitioner. At P40, P50, and P60
its mean pair precision against the exact complete-link reference was 42.8%,
48.3%, and 53.6%. Its centroid-cap geometry admitted many regions whose member
pairs violated the corresponding complete-link cut. Across 32 input orders,
the median identity-versus-shuffle coassignment Jaccard was 0.409, 0.474, and
0.529. No complete-link cross-note region was reproduced exactly in every
order. DP-vMF may still generate candidate groups, but it cannot define final
membership by itself.

The machine-readable report and the complete raw-membership audit are in:

```text
sse_multivector/fine-region-partition-result-v1/
```

Every exact complete-link cross-note merge in the P40–P60 audit window is also
presented without a correctness verdict, together with all takeaways, masks,
and complete source notes, in
[`sse-fine-region-complete-merge-review.md`](sse-fine-region-complete-merge-review.md).

The report binds the frozen input manifests, config, partition source, pilot
source, every order-specific DP-vMF partition, and every exact source-fragment
occurrence.

## Follow-up title-prompt probe

After the partition audit, a separate probe tested only the mapping from a
fixed segment to a human-facing title. It did not change or validate segment
membership.

Each segment member was presented as one numbered instance. Multiple source
fragments belonging to one vector were separated with semicolons. Fresh,
isolated `gpt-5.6-sol` calls at low reasoning effort received this exact frozen
prompt:

> What is the most precise and concise title for the semantic similarity among
> these instances?

The five P80 segments produced:

| Segment | Title |
|---|---|
| S003 | `Coffee Preparation and Consumption` |
| S004 | `Coffee Connoisseurship as Personal Identity` |
| S007 | `Proprietary Platform Control and Access` |
| S015 | `Public Conformity and Private Dissent` |
| S019 | `Solar Power Generation` |

The three P90 segments produced:

| Segment | Title |
|---|---|
| S005 | `Coffee Chain` |
| S008 | `Commitment to Free and Open-Source Software for Technological Sovereignty` |
| S020 | `Authenticity and Individuality` |

These outputs record how the frozen prompt titled already-fixed segments. They
do not establish that the partition was correct or select the current labeling
method.

## Scientific conclusion

This pilot supports:

> The frozen TEv4.1 vectors contain useful recurring semantic cores.

It does not yet support:

> One global cosine resolution plus DP-vMF can turn all idea vectors into a
> reliable hard fine-subject partition.

This is not evidence that labels or hierarchy construction should begin. The
pilot leaves the fine-segmentation algorithm, membership contract, and labeling
and hierarchy methods open. Its observed false merges and splits remain useful
evidence about this frozen hard-partition candidate, not a prescription for the
current atomic-subject pipeline.
