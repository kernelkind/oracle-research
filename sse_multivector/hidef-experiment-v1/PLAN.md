# HDFv1: independently discovered groups and exact containment

Frozen before running the real-note experiment, 2026-09-10. Tracking: CREC-124.

## Question

Can groups discovered independently at different scales produce meaningful broad-to-narrow paths over the existing notes, without making every larger group inherit an earlier merge?

This tests a construction process, not a label prompt. A saved parent must contain every vector of its child already. No membership is added to create that relationship. We will inspect the masks and source notes, not generated titles.

## Fixed input

- The existing 100 notes and 916 canonical vectors (945 original vector aliases).
- The I03 graph: 7,175 undirected weighted edges, with the exact saved weights and zero-based vector identities.
- Graph SHA-256: `b1722b18826e6389b2b608b0ae9a2ea3d40e46803e8e2e6cd3e28f47e259cf64`.
- Source artifact hashes and canonical-vector order must match I03. No new extraction, masks, embeddings, similarity calculation, or graph construction.
- Existing Infomap and HDBSCAN results remain unchanged.

## First-run settings

Use the released HiDeF finder at commit `3d016a375ac52feda0e0b2a3ace917c834f3a3a9`, with its community-comparison and consensus functions. Record installed dependencies and code hashes with each run.

| Setting | Value |
| --- | --- |
| Community algorithm | Weighted Leiden, RB configuration objective |
| Resolution range | 0.001 to 25 |
| Resolution sampling | HiDeF geometric subdivision; density 0.1; neighbors 10 |
| Edge sampling | 1.0: preserve every I03 edge |
| Leiden iterations | 2 |
| Primary seed | 123, plus deterministic sample index for each Leiden call |
| Candidate-size minimum | 1 vector; preserve all raw groups |
| Community similarity | Jaccard strictly greater than 0.75 |
| HiDeF consensus | k=5, f=1, p=75 |
| Parent containment | Exact vector-set containment; distinct sets only |
| Worker and numerical-library threads | 1 |

These are audited upstream CLI starting settings, not parameters chosen to fit these notes. Three intentional implementation differences must remain explicit:

1. Pass edge weights and seeds explicitly; the released `run_alg` omits them.
2. Preserve groups smaller than four vectors. The upstream filter of four is not a distinct-note requirement and would silently remove existing data.
3. Construct an exact-subset DAG directly from the preserved consensus groups. Do not use Weaver's approximate-containment membership expansion or couple its threshold to persistence similarity.

The upstream consensus retains a vector only when it occurs in **more than 75%** of the community instances in its family. It can therefore produce a group different from every raw candidate. Save the raw groups, their families, and the resulting consensus sets separately. Upstream persistence counts community instances, which is not necessarily the number of distinct resolutions; report both. A lineage calculation must agree with the actual upstream consensus output.

## Execution and preservation

First verify the production code with small tests: exact weighted graph loading; complete raw partitions; upstream consensus agreement; strict containment without membership expansion; overlapping parents; exact note counts; and the existing viewer regressions.

Run the primary sweep once. Record timing and peak memory, preserving raw partitions, candidates, persistent groups, exact-containment edges, note-set diagnostics, configuration, and source hashes. Refuse to overwrite a result directory.

Save the primary result under `HDFv1/seed123`, identified as `HDFv1-seed123`; likewise use separate `seed124` and `seed125` directories and identities. A numeric group ID refers only to its own run. Resolution generation has a 4,096-sample safety limit; reaching it aborts rather than silently shortening a valid sweep.

Then run two independent sensitivity sweeps with seeds 124 and 125 and otherwise identical settings. Do not combine their samples into the primary persistence calculation. Compare membership and ancestry repeatability; do not pick settings or present only the most attractive seed. If an implementation check fails, preserve the failed artifact and distinguish a corrected rerun from a valid scientific result.

All computation is local CPU work. No model calls or paid resources are part of this experiment.

## Hierarchy and viewer

Deduplicate equal vector sets. Connect each group to its immediate strict supersets, retaining multiple parents when present. Add a non-semantic root containing all 916 vectors. A child may appear along multiple paths but keeps the same identity and membership.

The viewer preserves nesting, shows exact masks with N/V identifiers, and makes complete original notes available. It omits groups containing fewer than two distinct notes only from display; their saved memberships remain available. Counts use set unions, never sums of overlapping child counts. Existing recursive note-based parent-mask hiding stays a display rule.

Report parent-child edges returning identical note sets as such, not as useful narrowing. Preserve and report pairs with note containment but no vector containment; do not automatically attach them, because different masks of one note can express different subjects.

## Independent inspection

Inspect independently discovered groups before judging their assembled paths. Cover broad groups, intermediate groups, leaves, and problematic boundaries across the complete collection. A short analyst description may explain a judgment but cannot change membership or become a generated title.

For each inspected path, record the actual masks supporting the judgment:

- Does the broader description fit the member meanings?
- Does the child express a legitimate refinement of that description?
- Does entering the child meaningfully narrow the returned notes?

An acceptable broad coffee group does not need prescribed subdivisions. One coherent branch does not establish correctness elsewhere. Persistence or reproducibility alone does not establish semantic coherence.

## How the result will inform us

- Useful groups and useful paths: evidence for this construction on the fixed corpus, not a production guarantee.
- Useful independent groups but few usable containment paths: evidence that the assembly criterion is limiting this result.
- Broad groups already mix unrelated meanings: the problem occurs before hierarchy assembly in this graph/discovery procedure.
- Additional levels return the same notes: more vector structure has not added note-discovery value.

Package all three runs for the existing TUI and provide a concise account of the strongest and weakest evidence. Algorithm selection remains open.

## Sources

- [HiDeF paper](https://link.springer.com/article/10.1186/s13059-020-02228-4).
- [Pinned HiDeF finder](https://github.com/fanzheng10/HiDeF/blob/3d016a375ac52feda0e0b2a3ace917c834f3a3a9/hidef/hidef_finder.py).
- [Pinned Weaver implementation](https://github.com/fanzheng10/HiDeF/blob/3d016a375ac52feda0e0b2a3ace917c834f3a3a9/hidef/weaver.py).
