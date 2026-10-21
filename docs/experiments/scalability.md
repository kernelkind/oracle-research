# Hierarchy-build scalability

The project aims to generate hierarchies for corpora exceeding one million
notes on consumer hardware. That scale has not been demonstrated. This record
preserves implementation analysis and measured small-run results; the
[generation guide](../generate-hierarchy.md) describes the current pipeline.

**Evidence:** Unlinked data references below identify local originals outside
this checkout. See [publication availability](README.md#reading-the-research-records).

## HDBSCAN implementation limits

The HDBv2 implementation studied here builds full cosine, angular-distance and
mutual-reachability matrices. Their storage grows with the square of the number
of distinct vectors. The exact spanning-tree calculation also performs
quadratic work. This was deliberately implemented for a small pilot; it does
not establish that HDBSCAN itself requires these matrices.

For illustration, one float64 matrix for ten million distinct vectors occupies
800 TB, whereas the 768-dimensional float32 vectors themselves occupy about
31 GB. These are decimal storage calculations, not measured peak memory. The
HDBv2 implementation holds additional data and copies. Roughly ten vectors per note
occurred in older selected samples; that is not a forecast for the distilled
model or a commitment to ten million distinct vectors.

Sources: [cosine matrix](../../src/fine_region_partition.rs),
[HDBSCAN implementation](../../src/fine_region_hdbscan.rs), and
[saved 100/200-note vector counts](../../sse_multivector/real-note-fine-segmentation-v1/music-generation-v1/results.md).

## Low-memory approach discussed, not implemented

1. For each vector, find its nearest neighbor from another source note. Keep
   the resulting distance rather than the full row of pairwise distances.
2. While building the spanning tree, retain each unconnected vector's cheapest
   connection to the connected set. Adding a vector requires comparing it with
   the remaining vectors and updating those saved connections.
3. Discard individual distances after use. Feed the completed tree into the
   existing condensation and group-selection calculation.

The connection cost is the maximum of the pair's angular distance and the two
vectors' cross-note nearest-neighbor distances. Keeping only each vector's
nearest neighbor once is **not** enough to perform the whole algorithm.
Removing full matrices saves memory but can require recomputing distances; it
does not by itself reduce the number of comparisons or prove affordable runtime.

This is an established computational approach, not a new clustering method:
the reference HDBSCAN implementation's
[`mst_linkage_core_vector`](https://github.com/scikit-learn-contrib/hdbscan/blob/7b2f0e0dcff6ef99b0c976d1471cbeec99da49a9/hdbscan/_hdbscan_linkage.pyx)
accepts vectors and supplied core distances and stores per-vector connection
state rather than a full matrix. No compatibility or performance test against
our pipeline has been run in this investigation.

### Compatibility requirements

Our HDBv2 density calculation requires the nearest neighbor to come from another
note; it does **not** prohibit same-note connections elsewhere in the spanning
tree. Exact-vector aliases can represent multiple source notes. Angular
distances, cluster-size counting, selection rules and handling of ties also
matter. See the [cross-note adapter](../../src/fine_region_candidate.rs).

Standard library settings must not be assumed equivalent. In particular,
switching to another distance can preserve neighbor ordering while changing
the stability values used to select groups. Approximate neighbor searches or
restricting connections to a limited neighbor list can also change results.

The investigation inspected the reference HDBSCAN implementation,
[fast_hdbscan](https://github.com/TutteInstitute/fast_hdbscan) and
[RAPIDS cuML](https://github.com/rapidsai/cuml/blob/main/python/cuml/cuml/cluster/hdbscan/hdbscan.pyx).
Memory-bounded and GPU-accelerated components exist, but no off-the-shelf path
has been verified to preserve our complete calculation. Low-dimensional
benchmarks are not evidence for our 768-dimensional SSE workload.

## Earlier pipeline measurements

Two saved 100-note SSE CPU runs took about **67 seconds each**. The encoder
processes a note once, then pools selected token representations for each mask.
This does not establish large-batch GPU throughput. The original resource
receipts are `sse_multivector/real-note-fine-segmentation-v1/encoder-run/resource-summary.json`
and `sse_multivector/real-note-fine-segmentation-v1/music-generation-v1/encoder-run-v2/resource-summary.json`.
See the [SSE worker](../../sse_multivector/worker.py).

The older title-generation route supplied every distinct mask instance in a
group to the model. Its total input grows with both mask membership and repeated
inclusion across groups; group count alone is insufficient for a cost estimate.
See [title-input preparation](../../sse_multivector/prepare_category_title_inputs.py).
The [historical token estimate](scaling/token-usage-1m-notes.md)
uses an earlier teacher workload and is not a forecast for HiGen V5.3.

The HR02-NSP-MASKS03 relationship experiment compared a fixed shortlist of
**566 pairs** over **148 groups**, not all pairs. It reused 48 saved answers and
made 520 new attempts, including two successful HTTP-503 retries. Its export
retained 148 nodes and 100 posts, with 101 reduced links and 76 roots. There
were no cycles; 39 uncertain pairs and three rejected-but-reachable directions
remained unresolved. A deterministic rebuild and browser checks passed, without
establishing semantic quality, candidate coverage or production scalability.
See the [NSP diagnostic](../../sse_multivector/node-merge-prompt-jev-v1/README.md#parentchild-prompt--nsp-astra-masks-v1).

## Eight-candidate comparison replay

The baseline is Bootstrap-v68 / Compare-v36, GPT-6.1 Sol medium, from
`oracle-mvp-shr-pair-correctness-v1/target/hierarchy-selective-sprint-v1/eight-v68-selection-02`.
The replay keeps its seventeen selected original entries, independently fixed
meanings and placement order. The experiment reduced the comparison-policy `limit`
from sixteen to eight; text/SSE ranking, same-note/mapped-parent rules and complete
eligible implication verification remain enabled. No constructor, prompt or
runner code changed.

| Whole-generation measure | Sixteen candidates | Eight candidates |
|---|---:|---:|
| Meaning requests | 17 | 17 |
| Comparison requests | 113 | 91 |
| Uncached input tokens | 254,575 | 211,641 |
| Cache-read tokens | 1,664 | 1,664 |
| Cache-write tokens | 0 | 0 |
| Output tokens, including reasoning | 7,806 | 6,462 |
| API-equivalent catalogue cost | $0.5873764 | $0.4880684 |

Total API-equivalent cost falls **16.9%**; comparison requests fall **19.5%**.
Costs include original generation of reused answers, not just replay execution.
All saved usage is present. Reasoning is already included in output. The replay
itself makes **zero provider attempts** and uses 108 exact saved answers.

All seventeen before/after graph snapshots match exactly. The complete raw graph
(fifteen canonical nodes), fixed meanings, supporting entries and shaped menu
(twelve nodes) are identical. Native policy evaluation reports preserved quality,
no changed placement decisions and zero structural violations. No omitted implied
relationship requires an extra verification phase in this run; the guard remains
enabled. This demonstrates preservation of this saved hierarchy, including its
existing semantic qualifications, not independent semantic accuracy or reliability
on future corpora. The baseline is the v68 build, not the earlier
fourteen-node Bootstrap-v14 / Compare-v19 menu reviewed in this scaling fork.

The original replay evidence was recorded under:
`oracle-mvp-canonical-selective-construction-v2/target/canonical-shortlist-eight-replay-v1/`.
Native evaluation (`../../../oracle-mvp-canonical-selective-construction-v2/target/canonical-shortlist-eight-replay-v1/evaluation-native.json`),
placement checks (`../../../oracle-mvp-canonical-selective-construction-v2/target/canonical-shortlist-eight-replay-v1/placement-checks.json`),
native usage (`../../../oracle-mvp-canonical-selective-construction-v2/target/canonical-shortlist-eight-replay-v1/usage-native.json`)
and `completed-replay.json` preserve the exact trial paths and receipts.
These original native artifacts are not reconstructed by compact results.

## Fresh ASv6.100 fifty-note construction

The [fifty-note failure record](../../sse_multivector/shr_single_pair/hierarchy-as100-fifty-note-findings-v1.md)
documents a completed fresh ASv6.100 build using Bootstrap-v96 and Compare-v48.
All fifty notes are individually reachable and every displayed edge narrows the
note set. The saved menu nevertheless exceeds K=6: seven roots, thirteen Food
children and seven Food-preparation children. Unchanged meanings also produced
incompatible comparison interpretations; guards and receipt-bound agent review
held those placements. These outcomes do not establish semantic accuracy or
production-scale feasibility.

The report retains the evaluated prompts, two menu recipes and canonical runtime.
Construction, selective entry discovery, guarded comparison selection,
continuation, shaping, structural audit and native accounting use the shared
runner. These checks do not resolve the saved semantic conflicts or the
six-choice limitation.
See the [native workflow](../../sse_multivector/model-runner.md#hierarchy-construction-and-saved-results).
The report retains source versions and the original evidence bindings. The
[reproduction guide](reproduce.md) describes the supported current reader paths.
