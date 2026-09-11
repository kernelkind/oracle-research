# HDFv2 — change graph connections, keep HiDeF fixed

Approved on 2026-09-10, before the HDFv2 hierarchy runs. CREC-124.

## Question

Does preventing several vectors from one note from accumulating connections to the same other vector improve the discovered groups and their parent–child relationships? Compare this with removing the same number of connections by weight alone.

This does not change extraction, masks, SSE, edge weights, HiDeF settings, or the display rules. It does not repair memberships or generate category labels. A better local group is not by itself a successful navigation hierarchy.

## Fixed inputs

- I03 graph: 100 notes, 916 canonical vectors, 945 original vector IDs, 7,175 undirected cross-note edges.
- Original graph SHA256: `b1722b18826e6389b2b608b0ae9a2ea3d40e46803e8e2e6cd3e28f47e259cf64`.
- Original primary hierarchy: `../HDFv1/seed123/hierarchy.json`, SHA256 `1cfe57e6835691ade70e5adf3e4c46c2babce0f0ef4f469e40f8b0db9dd2282d`.
- Existing HDFv1 data and input artifacts remain untouched. Each new configuration records the input hashes, original and actual graph hashes, code hashes, retained original edge indices, and removed original edge indices.

## Three graph policies

1. `original`: retain I03 unchanged; independently repeat it to verify the implementation still reproduces HDFv1.
2. `mutual_best_per_note`: for each vector and each other source note, choose its highest-weight existing neighbor from that note. Retain an existing edge only if both endpoints choose one another. Equal weights choose the lower canonical neighbor index. Do not add replacement edges.
3. `strongest_edges_matched`: retain the same number of original edges as policy 2, selecting the highest weights globally. Equal weights choose the lower ordered endpoint pair. This controls for edge count, not degree distribution, connected components, or the resulting modularity null model.

Every policy retains all vertices, including isolates, and preserves each surviving weight and original edge order. Run Leiden on the whole graph; do not partition connected components independently because that would change its objective.

## Runs

Run all three policies with seeds 123, 124, and 125, independently. IDs are `HDFv2-POLICY-seedSEED`, saved under `HDFv2/POLICY/seedSEED/`. Seed 123 is primary; the other seeds measure sensitivity and are not pooled or used to tune settings.

Use the existing pinned HiDeF implementation and dependencies. Keep minres 0.001, maxres 25, density 0.1, resolution neighbors 10, Jaccard 0.75, persistence 5, consensus percent 75, two Leiden iterations, one sample per resolution, and one worker. Retain singleton candidates and all intermediate partitions. Build the same exact-vector-containment DAG and independently check it with Weaver. No threshold or resolution changes after seeing results.

Execute sequentially with numerical threads limited to one. Use a process memory limit and inspect memory/runtime before continuing. No paid inference. A resource failure must be reported, not silently handled by dropping groups or changing the algorithm.

## Inspection selected before new runs

Use source masks and complete original notes, not generated subject titles. Inspect the known bad primary group 1046 and useful groups 951, 976, 1027, 1023, plus the candidate useful path 965 → 1037. Check where removed members actually go, rather than treating disappearance as success.

Additional selection uses HDFv1 primary groups, excluding the root, one-note groups, and the seven anchor groups above. Within each note-count stratum, take the four lowest SHA256 hashes of the UTF-8 string `HDFv1-source-balance-review-v1|HDFv1-seed123|GROUP_ID`:

- 2–4 notes: 1071, 1030, 1151, 1055.
- 5–14 notes: 1069, 994, 977, 995.
- 15 or more notes: 923, 938, 931, 939.

For these groups, select at most one incoming non-root edge and one outgoing edge to a group with at least two notes, taking the lowest hash of `HDFv1-source-balance-review-v1|HDFv1-seed123|edge|PARENT|CHILD`. Selected edges: 965 → 1071; 1005 → 1030; 929 → 1151; 997 → 1055; 994 → 1060; 923 → 1134; 938 → 975; 931 → 950; 919 → 939; 939 → 983.

Locate counterparts using the top two vector-set Jaccard matches and the top note-set Jaccard match, with lower group ID breaking ties, then deduplicate. These are inspection aids, not semantic scores or prescribed correct groups. Where no corresponding edge survives, inspect the actual shared parents rather than inventing a link. Unexpected coherent groupings are valid.

## Required checks and handoff

- Verify input preservation, retained edge identity/weights, source identities, every output hash, partition coverage, isolate handling, strict containment, and original-policy replay against HDFv1.
- Report isolates and connected components, note coverage outside the artificial root, group-size distribution, parent–child note reductions, and same-note transitions. These counts do not certify semantic quality.
- Inspect known failures, useful groups, the frozen additional sample, and complete paths. Main and an independent reviewer must examine masks; record disagreement and uncertainty without silently changing memberships.
- Preserve all nine runs. Extend the existing viewer with explicit policy selection; leave its HDFv1 default unchanged. Keep children nested and hide only the existing one-note display cases.
- Package evidence, limitations, run-local group IDs, and commands for user inspection. Do not declare a final algorithm or adopt a new default from this experiment.
