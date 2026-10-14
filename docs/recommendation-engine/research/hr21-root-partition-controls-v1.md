# HR21 root partition controls — exploratory findings v1

Status: offline investigation, not an approved or activated HiGen policy. No
Bootstrap, consolidation, vector, group membership, canonical hierarchy, or UI
was changed. No model calls were made.

The user identified four consecutive blocks in HR21's group-connection SVG and
confirmed the following interpretation. This is a preference for the root
partition, not independently validated semantic gold for section names.

| Root option | Fixed groups |
|---|---|
| Branch ending at G09 | G01, G02, G05, G09, G13, G22, G23, G24, G25 |
| Block ending at G19 | G03, G07, G12, G16, G19 |
| Branch ending at G17 | G04, G06, G08, G10, G11, G17 |
| Block ending at G18 | G14, G15, G18, G20, G21 |

All 25 fixed groups are covered once. The first and third options are complete
branches in the saved tree. The second and fourth combine side branches whose
common ancestor also contains groups assigned to other options. Consecutive
SVG rows alone are not evidence of semantic coherence.

## Findings

Two size controls, plus collecting small side branches along their original
ancestor paths, reproduce the target exactly:

- Treat a child branch containing fewer than **four fixed groups** as a small
  side branch.
- Stop descending when a branch contains **ten fixed groups or fewer**.

Here, size means number of fixed HDBSCAN groups, not original vectors, local
entries, or distinct notes. Original groups remain indivisible.

This is a custom section-selection rule. It uses the saved connections but can
combine several side branches into a new section. A different global epsilon
cut, or choosing existing whole branches by persistence, cannot by itself
produce the target.

## Collection rule

Start at the projected tree's root with an empty collection:

1. If the current branch is at or below the stopping size, retain it whole and
   emit any collected side branches as a separate section.
2. Otherwise, collect children below the small-branch threshold.
3. If one larger child remains, continue down it with that collection.
4. If several larger children remain, emit the collection and process each
   larger child independently, starting a new collection for each.
5. If no larger child remains, emit the collection. No groups are discarded.

The final order uses the earliest G ID in each section, not SVG adjacency as a
selection criterion. Each collection follows ancestor relationships.

Applied to HR21:

- The five outer side branches collect into G14, G15, G18, G20, G21.
- Their remaining 20-group branch divides into branches of 14 and six groups.
  The six-group branch is retained whole.
- Following the 14-group branch collects G19, then G12, then the three-group
  Coffee/Ice/Coffee-shops branch: G03, G07, G16.
- The remaining nine-group food/cooking branch is retained whole.

The result is exactly the four requested blocks, with sizes **9, 5, 6, 5**.

## Sensitivity and controls

An exhaustive 325-setting size sweep tested every integer threshold from one
to 25 and every stopping size from that threshold to 25. Exact matches occur
at all nine combinations of:

- Small-branch threshold: **4, 5, or 6**.
- Stopping size: **9, 10, or 11**.

The method does not read target labels while generating a partition. Target
membership is used afterward to measure agreement and select settings. This
is still fitting to one user-reviewed example, not held-out validation.

| Control | Result |
|---|---|
| Stop at ten, retain every small side branch separately | Ten root options |
| Collect branches below three, stop at ten | Five options; the proposed second block splits into G03/G07/G16 and G12/G19 |
| Collect branches below four, stop at ten | Exact four-block target |
| Any partition using only whole saved branches, at most six options | Target impossible; the six-option epsilon partition is the closest |

The whole-branch bound was calculated by dynamic programming over every
partition of the projected tree into at most six whole branches. There is
exactly one possible partition at each count from one to six: the outer
singleton branches consume the available choices before the 20-group branch
can be expanded. Choosing by persistence or another score cannot overcome
this structural restriction.

## Persistence and stability checks

Branch persistence here is the density interval from its recorded birth to
its surviving split. Values illustrate why longest persistence alone does
not identify the requested branches:

| Existing branch | Fixed groups | Persistence, delta lambda |
|---|---:|---:|
| Current broad root section | 20 | 0.002584 |
| Larger food/coffee/Nostr branch | 13 | 0.071515 |
| Requested food/cooking branch | 9 | 0.058119 |
| Requested branch ending at G17 | 6 | 0.010450 |

The screen replaced the size stopping criterion with thresholds on each of:
absolute persistence, persistence divided by birth density, persistence
weighted by fixed-group count, production EOM stability, and production EOM
stability divided by vector count at birth. Small-side-branch thresholds from
one to 25 were retained. Every score threshold interval was tested, totaling
**3,000 settings** across the five scores. None reproduced the target exactly.

The closest results produced five sections, splitting only the proposed second
block into G03/G07/G16 and G12/G19. Those best results consisted entirely of
collected side branches; they do not establish a beneficial contribution from
persistence or stability. This finding concerns the tested rule family, not
every possible use of these quantities.

Recorded production EOM scores were independently recomputed from condensed
tree edges and matched the saved selected-cluster scores. The ordinary section
plan was reproduced through the production `hierarchy_hdbscan.section_plan`
path and matched the saved roots and epsilon boundaries.

## Size scaling checks on larger saved trees

Fixed thresholds of four and ten do not scale consistently. For example,
HR22 yields nine root sections. As an exploratory alternative, set the small
branch threshold to **ceil(15% of fixed groups)** and the stopping size to
**floor(40% of fixed groups)**. HR21 then uses four and ten.

| Saved tree | Fixed groups | Absolute 4/10: root sizes | Proportional 15%/40%: root sizes |
|---|---:|---|---|
| HR21 | 25 | 9, 5, 6, 5 | 9, 5, 6, 5 |
| HR22 | 62 | 4, 12, 10, 9, 4, 5, 7, 5, 6 | 20, 22, 9, 11 |
| HR23 | 42 | 9, 10, 4, 7, 5, 7 | 9, 16, 10, 7 |
| HR24 | 46 | 13, 10, 4, 9, 7, 3 | 13, 17, 7, 9 |
| HR25 | 39 | 9, 10, 12, 8 | 9, 15, 7, 8 |

Every fixed group remains represented exactly once. Four root options on
these larger trees is a structural observation, not evidence that their
sections are understandable or semantically useful. These cases have no
new user-reviewed target partitions. The stopping size controls descent;
collected side branches can exceed it, as the absolute-setting results show.
Neither variant guarantees at most six options on arbitrary trees.

This study selects roots only. Naming collected sections, building their
deeper browsing structure, and deciding how to enforce width limits remain
separate design work. Existing HiGen behavior remains unchanged.

## Evidence

Ignored calculations, frozen input paths and hashes, all size/score settings,
branch measurements, ablations, and larger-tree checks:

`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hr21-persistence-partitions-v1/target/hr21-root-partition-study-v1/analysis.json`

HR21 source state:

`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr21-v41/target/hierarchy-hr21-v41-fifty-note-v1/HR21/state.json`

SHA256:
`89e7c00b1cb4c3807f594f9c6f6bdd3f04cabd4fc8f56082951a0afc463f8f81`.

Research source checkout starts at local main commit `47d6a5d0`. All five saved
experiment source checkouts and their receipts remain unchanged. The research
worktree is retained for its ignored calculations; this study has no new
inference receipts or official hierarchy run ID.
