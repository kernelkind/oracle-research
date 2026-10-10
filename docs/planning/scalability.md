# Hierarchy-build scalability

Updated October 10, 2026. This records scalability decisions and evidence.
Implementation and spending require their own task authorization. Release
requirements, corpus scope, compute locations and budget remain in
[release decisions](release-decisions.md).

## User decisions and scope

- October 5: node sorting is deferred as nice-to-have work. It does not block
  hierarchy validation, teacher selection, fine-tuning or release resource
  estimates. Preserve existing sorting evidence; no replacement method is
  selected.
- September 29 clarification: HDBSCAN use is undecided. Its scale assessment
  (21) is required for 20 and 28 only if HDBSCAN is used. Time and cost checks
  for the chosen workflow remain required. The investigation below remains
  evidence for that open choice, not selection of HDBSCAN or a replacement.
- Task 22 measures stages used in the chosen workflow. Separate node-title
  generation and its input-growth costs are required only if that stage is used;
  the corresponding large-input work in 28 is conditional too. The title-cost
  evidence below describes the HDBSCAN route, not a mandatory stage of every
  workflow. No production workflow is selected by this clarification.
- Task 20 separates teacher-based release estimates from optional distilled-model
  estimates. Shared construction measurements can inform both where applicable;
  pilot generation rates are not teacher generation rates and do not block the
  release estimate. Model-track checks 10 and 11 do not gate the release snapshot.
- Authorized a read-only review of the pipeline's scaling risks, then a
  read-only investigation of scaling HDBSCAN while preserving its grouping
  rules. Those investigations are complete; launch-scale feasibility is not.
- The user described the low-memory approach below as reasonable after
  discussing what it retains and recomputes. This is acceptance of its
  plausibility, not selection of an implementation or approval to run a test.
- Subsequently authorized defining the bounded performance test below. Its
  procedure and proposed $10 ceiling have not been approved for execution.
- This workstream remains planning and investigation. No replacement algorithm,
  changed grouping rules, implementation work, GPU rental or spending has been
  approved here.
- This is a concurrent scalability investigation, not a refactor of the working
  pipeline. Any subsequently authorized prototype must be isolated: do not
  modify existing pipeline code, redirect its commands, overwrite its artifacts
  or alter the environment used by concurrent work. Read saved inputs/results
  without changing them and keep experimental code, builds and outputs separate.
  The user agreed to a separate Git worktree with separate build outputs and
  results, then authorized its setup only. The worktree is now created as
  recorded below. Prototype implementation and benchmark execution remain
  unapproved.
- Do not modify the diagram without direct user permission. This written record
  does not authorize a diagram update or change task readiness on it.
- Keep decisions and findings here as the discussion develops. Present findings
  in small, concise increments in chat; do not repeat the full audit at once.

## Investigation worktree

Created September 20, 2026; setup only, with no build, prototype or experiment.

| Item | Location or identity |
| --- | --- |
| Worktree | `/home/dev/src/notedeck_worktrees/algos/oracle-mvp-scalability` |
| Branch | `experiment/scalability-v1` |
| Starting commit | `1315f309078e43152ed2f48c300cc0e1cf75e6ea` |
| Dedicated build directory | `target/` inside that worktree |
| Dedicated result directory | `scalability-results/` inside that worktree |

The current scalability note is carried into the new worktree. Unrelated
uncommitted changes in the original worktree are not copied or altered. Future
builds must explicitly use the dedicated build directory; existing launchers
must be checked for absolute paths before reuse. No dependencies were installed
or shared build configuration changed during setup.

A worktree isolates working files, not host CPU/memory or the repository's
lifetime spending limit. Resource limits must be settled before experiments;
a worktree's ledger snapshot is not a separate budget or proof of current
available funds. No paid action is authorized by this setup.

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
| Subject/mask generation | The required release uses teachers; 2–5k notes is a target, not a minimum. Estimate generation time and cost from teacher measurements for the prospective corpus. Node sorting is deferred and adds no required outputs or resource checks. Keep optional pilot/distilled-model generation measurements separate. The old 30-billion-token estimate describes an earlier teacher workload, not a forecast for either current track. |
| SSE | Two saved 100-note CPU runs took about 67 seconds each. The encoder processes a note once, then pools its selected token representations for each mask. Large-batch GPU throughput remains unmeasured. |
| Node titles | Current inputs include all distinct mask instances in each group. Neither launch-scale node counts nor group-input sizes are established; scaling 61 groups to 610,000 is not a forecast. |
| Node relationships | The launch relationship method is open. Earlier Jev/manual-placement evidence remains preserved. NSP-Astra-Masks-v1 is tested experimentally with HR02-NMP09 groups and merges fixed. HR02-NSP-MASKS02 expands the first test to 48 structurally valid comparisons: 36 new Astra-low subscription calls plus 12 exact-request reuses, no retries. Initial agent review accepted 29 new answers, rejected two and left five uncertain; this is not measured accuracy. The user subsequently resolved the three linked meat comparisons, rejecting two answers and accepting one, and confirmed the missed Positive emotions parent of Enjoyment of food. Fire/Ash, Pizza, Ice/ice cream and the earlier Preservation comparison remain unresolved; the agent withdrew its likely-miss assessment of Ice/ice cream. No graph changes followed. The earlier user-confirmed rejection remains recorded separately. Existing tree links and the bounded cross-branch shortlist yield 566 unique pairs over 148 groups; this is a saved-input count, not full-pass authorization or a scale estimate. Combined merging/placement is deferred. Candidate coverage, graph-conflict handling, throughput and production-scale input costs remain unvalidated. |
| Missing memberships | This is separate from linking nodes. The coffee/tea test checked 945 masks against six nodes. A scalable recovery procedure has not been selected here. |

The approved offline HR02-NSP-MASKS02 construction now consumes the 48 saved
answers without requiring all-pairs inference or creating answers for untested
pairs. Its separate browser view retains all 148 nodes and 100 posts, with 20
links; six model-uncertain pairs remain unresolved and 518 candidate pairs are
untested. Strict-containment cycles stop export without automatic merging;
other path contradictions are reported without repairs. The saved sample had
neither kind of contradiction. This does not validate semantic quality,
candidate coverage or launch-scale throughput. The user separately approved
HR02-NSP-MASKS03 to finish the 518 remaining candidate pairs with unchanged
prompt, Astra low and concurrency four, reusing the 48 saved answers. This
completes the existing 566-pair list, not all pairs over the 148 groups; no
production-scale claim follows. HD07 and existing groups/merges/titles stay fixed.
The pass completed with 566 valid answers, 48 reuses and 520 new attempts
(including two successful HTTP-503 retries). Its separate browser export has
148 nodes, 100 posts, 101 reduced links and 76 roots, without cycles. The 39
uncertain pairs and three rejected-but-reachable directions remain unresolved.
Browser validation and deterministic rebuild passed; browsing quality and
production scalability remain unvalidated.

Evidence: [historical token estimate](../../sse_multivector/TOKEN-USAGE-ESTIMATE-1M-NOTES.md),
[SSE worker](../../sse_multivector/worker.py),
[original SSE receipt](../../sse_multivector/real-note-fine-segmentation-v1/encoder-run/resource-summary.json),
[music SSE receipt](../../sse_multivector/real-note-fine-segmentation-v1/music-generation-v1/encoder-run-v2/resource-summary.json),
[title-input preparation](../../sse_multivector/prepare_category_title_inputs.py),
[TRUE CPU timing](../../sse_multivector/navigation-research-v1/TRUE04/completion.json),
and [coffee/tea membership workload](../../sse_multivector/navigation-research-v1/TRUE14/plan.json).

## Bounded performance test — draft, execution not approved

Question: can memory-bounded execution of our unchanged HDBSCAN calculation
preserve the groups and run quickly enough to justify a larger feasibility
trial? A small pilot cannot by itself certify the final launch build.

### 1. Check preservation locally before renting a GPU

Reuse the frozen vectors and complete results from the original food/drink
collection, music collection, and their combined collection. They contain 945,
1,057 and 2,002 supplied vectors respectively, before exact-vector aliasing.
Do not regenerate subjects, masks or SSE vectors for this comparison.

Require identical group memberships and ungrouped-mask sets, ignoring arbitrary
cluster IDs. Check the cross-note nearest distances, angular connection costs
and density hierarchy, not just the final number of groups. Existing tests for
cross-note cores, aliases and equal-distance cases provide additional checks.
Numerical differences must be explained; do not require identical internal
tree edges when tied alternatives represent the same hierarchy. Unexplained
membership differences stop advancement to larger runs.

This requires an isolated prototype, which has not been implemented or selected
here. Exercise that prototype's actual grouping path, not a substitute
calculation created only for the test. Compare against the existing saved
baseline without modifying the working pipeline. Local preparation and
execution still require approval; no paid resources are needed for this step.

Sources: [food/drink result](../../sse_multivector/real-note-fine-segmentation-v1/hdbscan-cross-note/response.json),
[music result](../../sse_multivector/real-note-fine-segmentation-v1/music-generation-v1/HDBv2-music100/response.json),
and [combined result](../../sse_multivector/real-note-fine-segmentation-v1/music-generation-v1/HDBv2-combined200/response.json).

### 2. Measure complete runtime and memory at increasing sizes

Before a paid run, identify the larger input artifacts, vector counts, hardware,
implementation, precision and resource limits. The verified small collections
above are not a representative million-note workload. A larger suitable SSE
pool has not been identified in this investigation; its provenance and any
generation work need to be settled separately. Do not inflate the sample by
duplicating vectors and present the result as a representative scale test.

Measure end-to-end grouping time, host and GPU peak memory, and the separate
time spent loading/canonicalizing vectors, finding cross-note neighbors,
building connections, and selecting groups. Include transfers and setup in
the rental cost. GPU distance throughput alone is not an HDBSCAN benchmark.
Repeat a completed size to check timing variability before using its rate.

Use observed growth to decide whether the next size fits the approved limits.
Do not extrapolate linearly across quadratic work. Synthetic inputs, if later
approved, can test resource limits but cannot establish actual SSE grouping
quality or data-dependent runtime. Report the largest real workload completed
and distinguish measurements from projections.

### 3. Bound the pilot and report what it establishes

Propose a **$10 total maximum** for the initial paid feasibility test, including
setup, storage, transfers and failed attempts. This is an exploratory ceiling
(1% of the lifetime cap), not a price quote, an allocation, or evidence that the
test will fit. No amount has been reserved in the ledger. A suitable rental
quote, explicit approval and the existing budget admission check are
prerequisites to spending. A provider-enforced termination limit is not required.

Stop before a larger case would exceed the cost or memory limit, on unexplained
grouping changes, or if continued work cannot stay within the approved budget.
No automatic larger rental, approximation, corpus reduction, metric change or
new input-generation run follows a failed or inconclusive result.

The report should establish one of: the unchanged calculation warrants a
larger trial; the tested path exceeds the resource limits; or the evidence is
still insufficient. It must not declare million-note feasibility from small
matching cases or synthetic stress tests. Whether the full build fits the
deadline and budget remains a later decision using all pipeline stages.

## Eight-candidate comparison replay: saved for later handoff

On October 9 the user authorized replaying the eight-candidate comparison policy
against a saved eight-note build, with no new model calls. After the result, the
user said verbatim: **"OK we'll save this to give to the gen agent later"**.
The result is retained for a later handoff; the generation agent has not been
messaged and its active policy has not been changed by this task.

The baseline is Bootstrap-v68 / Compare-v36, GPT-6.1 Sol medium, from
`oracle-mvp-shr-pair-correctness-v1/target/hierarchy-selective-sprint-v1/eight-v68-selection-02`.
The replay keeps its seventeen selected original entries, independently fixed
meanings and placement order. The existing comparison-policy `limit` changes
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
on future corpora. The baseline is the generation agent's v68 build, not the earlier
fourteen-node Bootstrap-v14 / Compare-v19 menu reviewed in this scaling fork.

Evidence stays under the retained selective-construction worktree:
`oracle-mvp-canonical-selective-construction-v2/target/canonical-shortlist-eight-replay-v1/`.
[Native evaluation](../../../oracle-mvp-canonical-selective-construction-v2/target/canonical-shortlist-eight-replay-v1/evaluation-native.json),
[placement checks](../../../oracle-mvp-canonical-selective-construction-v2/target/canonical-shortlist-eight-replay-v1/placement-checks.json),
[native usage](../../../oracle-mvp-canonical-selective-construction-v2/target/canonical-shortlist-eight-replay-v1/usage-native.json)
and `completed-replay.json` preserve the exact trial paths and receipts.
The selective-construction worktree must remain while these artifacts, the review
UI and their frozen absolute references are needed.

For the later handoff: use a fresh comparison-policy definition with
`schema_version: 1`, `limit: 8` and the existing saved `subject_probe`. Keep current
approved prompts and complete guards; do not roll back to v68 solely to use this
policy. Prepare a fresh trial rather than editing a frozen sixteen-candidate
policy. This replay used the native constructor and shared experiment-runner CLI,
with request history pinned to the baseline's original receipt references and an
exhausted persistent budget to forbid new dispatch. If a proposed placement changes
later comparison inputs, stop replay when no exact saved answer exists. Any new
inference or active-policy adoption requires the relevant authorization; this
saved result grants no additional calls, spending or permission to contact agents.

## Fresh ASv6.100 fifty-note construction

The [fifty-note failure record](../../sse_multivector/shr_single_pair/hierarchy-as100-fifty-note-findings-v1.md)
documents a completed fresh ASv6.100 build using Bootstrap-v96 and Compare-v48.
All fifty notes are individually reachable and every displayed edge narrows the
note set. The saved menu nevertheless exceeds K=6: seven roots, thirteen Food
children and seven Food-preparation children. Unchanged meanings also produced
incompatible comparison interpretations; guards and receipt-bound agent review
held those placements. These outcomes do not establish semantic accuracy or
production-scale feasibility.

The report, exact evaluated prompts and two menu recipes are in main. The native
constructor, receipts and target artifacts remain in the retained
`oracle-mvp-hierarchy-bootstrap-v88-three-note-v1` worktree; the report gives the
source commit and complete inspection command. This bounded documentation
integration changes no generation policy, prompt or saved graph.
