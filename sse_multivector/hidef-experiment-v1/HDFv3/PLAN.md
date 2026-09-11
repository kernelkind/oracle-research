# HDFv3 — extend the original graph's resolution range

Approved 2026-09-10. Frozen before HDFv3 corpus runs. CREC-124.

## Question

Did ending the HiDeF search at resolution 25 prevent useful categories and parent–child relationships from being discovered?

Extend the original graph's range through 190. Its weighted RB objective has a calculated all-singleton endpoint of 189.04515286794103. This supplies a finite stopping point, not a claim that singleton leaves are useful or that intermediate optima will all be found. More groups or smaller groups alone are not success.

The motivating calculation concerned the separate HDFv2 restricted graph: its observed six-member Satoshi/Sophia/Sorrento/herb group only favors separating the two Satoshi masks above approximately 60. That graph is not being rerun here. The original graph is the first test because it retains useful connections and all 100 notes; the calculation does not guarantee the original graph will recover that pair.

## Fixed inputs and procedure

- Original I03 graph: 100 notes, 916 canonical vectors, 945 original vector IDs, 7,175 undirected cross-note connections. SHA256 `b1722b18826e6389b2b608b0ae9a2ea3d40e46803e8e2e6cd3e28f47e259cf64`.
- Reuse `../HDFv2/original/seed123`, `seed124`, and `seed125`, including every old raw partition and candidate. Preserve resolution, seed, membership, score, sample index, candidate IDs, and recorded timing. Do not optimize old resolutions again.
- Preserve all note text, subjects, masks, vector values, aliases, graph weights and edges, pinned dependencies, weighted Leiden objective, two optimization iterations, and one sample per resolution.
- Preserve minimum resolution 0.001, density 0.1, resolution neighbors 10, Jaccard 0.75, persistence 5, consensus percent 75, singleton retention, exact vector containment, and note projection/display rules.
- Generate additional resolutions using the existing sampling rule on the interval [25, 190], omit its already-present lower endpoint, and append them after the old samples. Reconstruct the resolution-neighbor graph using all old plus new resolutions, allowing cross-boundary connections.
- New seed = original base seed + global sample index. Old seeds are reused verbatim. A fresh full-range schedule is not equivalent and must not replace the old schedule.
- Recompute persistence and containment from the combined candidate pool. Old persistent groups may change when new evidence joins their families; track that explicitly rather than forcing their preservation.

Each run records source artifact/manifest hashes, old/new resolution counts and values, derived endpoint, code and dependency provenance. IDs are `HDFv3-seed123`, `HDFv3-seed124`, and `HDFv3-seed125`, saved in their respective new directories. HDFv1 and HDFv2 are never overwritten; the viewer default remains HDFv1.

## Checks and inspection

First validate exact preservation of the graph, source identities, old raw partition and candidate prefixes. Validate all partitions cover every vector, recompute objective scores, verify manifests, consensus provenance and strict containment, and check that the final resolution produces singleton groups. Keep raw and persistent results distinct.

Use masks and complete original notes, not generated titles or changed memberships. Follow the baseline examples: original groups 1046 (mixed Satoshi association), 951 (coffee), 976 (eggs), 1027 (wine/gin), 1023 (exercise), 965 → 1037 (equipment), 977 (tomatoes), 994 → 1060 (number association), and 919 → 939 → 983 (food/storage). These descriptions are inspection shorthand, not prescribed labels or a uniquely correct taxonomy. Match exact vector memberships and inspect top vector-set/note-set correspondences where a group changes. Note-set overlap alone is not evidence that the same subject was preserved.

Separately trace canonical vectors 187 and 691 (display V189/N024 and V433/N054) through raw candidates, persistent groups, and actual ancestors. Do not call disappearance of an unwanted group a repaired placement.

For new primary-seed multi-note groups, select two memberships per note-count stratum (2–4, 5–14, 15 or more) with the smallest SHA256 of `HDFv3-resolution-extension-review-v1|` followed by comma-separated sorted canonical vector indices. Missing strata remain empty. This additional sample is selected mechanically before semantic inspection. Inspect incoming/outgoing relationships and full notes as necessary; report ambiguities and regressions alongside positives.

Success means new coherent choices and useful narrowing while preserving valid access. A correct isolated pair is a local result, not proof of a complete hierarchy. If good raw groups are missing, lost during persistence, or placed under incoherent parents, distinguish those failures.

## Resources and handoff

Run primary seed 123 first; inspect resources before running the two fixed sensitivity seeds sequentially. Use one numerical thread and a 6 GiB per-process address-space limit. No paid inference, new embeddings, rentals, or automatic parameter tuning. A resource failure must be reported, not handled by silently dropping candidates.

Package separate artifacts and the existing nested-mask TUI, retaining full-note access and the two-distinct-note display minimum. Record analyst judgments separately from user approval. Leave broader algorithm selection open.
