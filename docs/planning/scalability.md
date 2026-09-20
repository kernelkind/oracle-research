# Hierarchy-build scalability

Updated September 20, 2026. This records the scalability discussion, not an
approved implementation or benchmark plan. Release requirements, corpus scope,
compute locations and budget remain in [release decisions](release-decisions.md).

## User decisions and scope

- Authorized a read-only review of the pipeline's scaling risks, then a
  read-only investigation of scaling HDBSCAN while preserving its grouping
  rules. Those investigations are complete; launch-scale feasibility is not.
- The user described the low-memory approach below as reasonable after
  discussing what it retains and recomputes. This is acceptance of its
  plausibility, not selection of an implementation or approval to run a test.
- This workstream remains planning and investigation. No replacement algorithm,
  changed grouping rules, implementation work, GPU rental or spending has been
  approved here.
- Do not modify the diagram without direct user permission. This written record
  does not authorize a diagram update or change task readiness on it.
- Keep decisions and findings here as the discussion develops. Present findings
  in small, concise increments in chat; do not repeat the full audit at once.

## HDBSCAN: confirmed limitation in the current code

The current implementation builds full cosine, angular-distance and
mutual-reachability matrices. Their storage grows with the square of the number
of distinct vectors. The exact spanning-tree calculation also performs
quadratic work. This was deliberately implemented for a small pilot; it does
not establish that HDBSCAN itself requires these matrices.

For illustration, one float64 matrix for ten million distinct vectors occupies
800 TB, whereas the 768-dimensional float32 vectors themselves occupy about
31 GB. These are decimal storage calculations, not measured peak memory. The
current code holds additional data and copies. Roughly ten vectors per note
occurred in older selected samples; that is not a forecast for the new extractor
or a commitment to ten million distinct vectors.

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

### What must not change silently

Our HDBv2 density calculation requires the nearest neighbor to come from another
note; it does **not** prohibit same-note connections elsewhere in the spanning
tree. Exact-vector aliases can represent multiple source notes. Angular
distances, cluster-size counting, selection rules and handling of ties also
matter. See the [current cross-note adapter](../../src/fine_region_candidate.rs).

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

## Other concerns retained from the pipeline audit

| Stage | Evidence and remaining question |
| --- | --- |
| Mask/prominence generation | The intended fine-tuned extractor receives a complete note and emits its masks and prominence. Its speed and cost are unmeasured. The old 30-billion-token estimate describes the annotation process, not this production path. |
| SSE | Two saved 100-note CPU runs took about 67 seconds each. The encoder processes a note once, then pools its selected token representations for each mask. Large-batch GPU throughput remains unmeasured. |
| Category titles | Current inputs include all distinct mask instances in each group. Neither launch-scale category counts nor group-input sizes are established; scaling 61 groups to 610,000 is not a forecast. |
| TRUE category links | Intended launch work uses cosine-filtered candidate pairs, not exhaustive TRUE comparisons. Both retained-pair counts and GPU throughput remain unknown; filtering must preserve useful links. |
| Missing memberships | This is separate from linking categories. The coffee/tea test checked 945 masks against six categories. A scalable recovery procedure has not been selected here. |

Evidence: [historical token estimate](../../sse_multivector/TOKEN-USAGE-ESTIMATE-1M-NOTES.md),
[SSE worker](../../sse_multivector/worker.py),
[original SSE receipt](../../sse_multivector/real-note-fine-segmentation-v1/encoder-run/resource-summary.json),
[music SSE receipt](../../sse_multivector/real-note-fine-segmentation-v1/music-generation-v1/encoder-run-v2/resource-summary.json),
[title-input preparation](../../sse_multivector/prepare_category_title_inputs.py),
[TRUE CPU timing](../../sse_multivector/navigation-research-v1/TRUE04/completion.json),
and [coffee/tea membership workload](../../sse_multivector/navigation-research-v1/TRUE14/plan.json).

## Suggested next step — not approved

Define a bounded performance test of the unchanged HDBSCAN calculations,
including compatibility checks against saved results, representative vector
counts, runtime and peak-memory measurements, and a maximum GPU charge.
Implementation, hardware, test procedure and spending need explicit approval.

The decision it should inform is whether the exact calculation can fit the
launch deadline and remaining budget, or whether further investigation is
needed. Removing the memory obstacle does not answer that question; a small
matching result alone would not answer it either. No approximation, corpus-size
reduction or change to grouping rules is pre-approved if performance falls short.
