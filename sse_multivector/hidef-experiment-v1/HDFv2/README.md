# HDFv2 — graph connections with HiDeF unchanged

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

The source-note restriction did **not** produce a consistent improvement. It recovered the Satoshi connection that motivated the test, but did not isolate it from unrelated meanings. Some useful original groups became harder to recover. Keeping the same number of strongest edges produced different successes and losses, not a clear replacement.

All nine runs are preserved. HDFv1 remains the default. No labels, masks, vectors, or memberships were manually changed. These are analyst findings pending user inspection, not approval of a hierarchy algorithm. CREC-124.

## What changed

All runs use the same 100 notes and 916 vectors, and the same 242 HiDeF resolutions. Each policy was run independently with seeds 123, 124, and 125.

| Policy | Connections retained | Vectors with no connection | Notes represented in a multi-note group |
| --- | ---: | ---: | ---: |
| `original` — unchanged I03 | 7,175 | 0 | 100 |
| `mutual_best_per_note` — both vectors must choose one another as their best neighbor from the other's note | 2,008 | 78 | 100 |
| `strongest_edges_matched` — the 2,008 highest-weight original connections | 2,008 | 352 | 94 |

Those counts are identical across seeds. Every vector and note remains saved, including disconnected vectors. The last column counts notes outside the artificial root, in groups containing at least two distinct notes. It does not say that every meaning in those notes is preserved.

The six notes without a multi-note group in the strongest-edge control are N003, N044, N062, N065, N081, and N088. The original graph has one connected component. The restriction produces 82 components (78 are single vectors); the control produces 372 (352 are single vectors).

The second policy permits at most one connection from a vector to each other source note. It does not refill removed connections with more distant neighbors. The third policy matches edge count only; it does not match degrees, connected components, or Leiden's changed null model.

[PLAN.md](./PLAN.md) was frozen before the new hierarchy runs. Its SHA256 is `10f59179daa12fde53a34e60c1b0f82b741517f7c022f87f0b6e2607a9251c60`. It records the hypotheses, fixed settings, known examples, and additional review sample chosen without seeing HDFv2 results.

## The original failure was not repaired

In HDFv1, group **1046** mixed Satoshi, an infant named Sophia, Sorrento's food tour, and restaurant locations. Removing repeated connections from the food-tour note did connect the two Satoshi masks, but their smallest shared group still contained unrelated meanings.

In `mutual_best_per_note`, seed 123, **1117** contains exactly:

- V189 · N024: ⟦satoshi⟧
- V516 · N061: ⟦Sophia⟧ ⟦#nostrbaby⟧
- V290 · N037: ⟦rosemary⟧ ⟦sourdough bread⟧
- V433 · N054: ⟦Satoshis⟧
- V022 · N002: ⟦Sorrento's Savory Stroll⟧ ⟦🍋⟧
- V877 · N096: ⟦Spaghetti Bolognaise⟧ ⟦bunch fresh basil⟧ ⟦chopped⟧ ⟦leaves⟧

The source notes confirm that Sophia is a five-month-old baby, rosemary and basil are recipe ingredients, and the Sorrento text advertises a tour. The two Satoshi masks now meet, but there is no narrower saved group containing both without unrelated masks.

This is not just the primary seed: the smallest shared Satoshi group is **1123** in seed 124, with Sorrento, a zapathon, and exercise advice; it is **1065** in seed 125, with Sorrento, Sophia, herbs, and a zapathon. None is a clean Satoshi group.

Correction from the HDFv3 source audit: the strongest-edge control does produce a clean persistent Satoshi/Satoshis pair in seed 123, group **1119**, with seven supporting resolutions. The earlier summary omitted this positive. The control also disconnects many other vectors and loses six notes from multi-note groups; the clean pair does not erase those coverage losses.

## Useful original groups did not all survive the change

IDs in this table are run-local. Original means HDFv1 seed 123; both new columns mean HDFv2 seed 123. Descriptions here explain the inspection and are not stored titles.

| Original evidence | Source-note restriction | Same-count strongest-edge control |
| --- | --- | --- |
| **951:** 15 coffee notes | **963** retains 13 of those notes coherently. The smallest group covering all 15 is **925**, with 23 notes including a gin/cherry-beer post that says nothing about coffee. | **930** contains all 15 plus two other coffee-related notes. This is a useful local group, not proof of its ancestors. |
| **976:** seven egg notes | **1031** is still a recognizable egg group. It replaces the duck-egg breakfast-burrito note with a different note about preparing eggs. That change is not inherently a failure. | **937** includes all seven but adds beet-growing, pie, stock, and risotto masks. Its smaller children still mix some of those meanings. |
| **965 → 1037:** cooking/eating equipment narrows to five notes using cooking equipment | **1157**, the nearest five-note counterpart, loses the bread-pan note and adds lamb with steamed broccoli. The smallest saved group covering the original five notes has 83 notes. The useful original path is not recovered. | **973** preserves the five cooking-equipment notes. Its child **1006** drops the bread-pan note; **1019** returns the same four notes as 1006. The local group survives, but this is not demonstrated semantic narrowing. |
| **1027:** wine and gin across four notes | **1140** mixes wine masks with steak-and-cheese sandwiches containing white onions. The gin note is elsewhere. | **967** also mixes wine with white/red onions, while the gin vector is disconnected. |
| **1023:** ten exercise masks from three notes | Four of those vectors are disconnected. **1205** contains the same three notes through different masks about morning activity; identical note membership does not establish preservation of the original subject. | Nine of the ten exercise vectors are disconnected. A match based only on source-note overlap instead finds sleep/tiredness masks. |

For the cooking-equipment example, the smallest group covering the original five notes contains **83, 100, and 86 notes** in the three restricted runs. This is evidence of a repeatable loss of that compact combination, not a requirement that every valid alternative reproduce its exact vector set.

The [additional frozen sample](./inspection.md) records all twelve extra groups and ten relationships. It also contains positive evidence: the strongest-edge control discovers a coherent six-note tomato group and a promising actual path from broad food/preparation to pressure-canning and vacuum-sealed food. These successes do not offset its coverage losses automatically, and the tomato group's next level returns the same six notes.

## Structure and runtime

| Measure | Original, seeds 123 / 124 / 125 | Source-note restriction | Strongest-edge control |
| --- | --- | --- | --- |
| Displayed groups, including root | 240 / 236 / 244 | 306 / 295 / 310 | 234 / 238 / 238 |
| Displayed parent–child edges below root | 276 / 296 / 272 | 372 / 345 / 411 | 287 / 285 / 283 |
| Those edges returning the same notes | 5 / 11 / 9 | 2 / 1 / 3 | 14 / 15 / 15 |
| Runtime, seconds | 7.05 / 7.01 / 7.09 | 18.12 / 17.89 / 18.10 | 66.40 / 66.26 / 67.83 |
| Peak process memory, MiB | 234.1 / 233.1 / 233.4 | 448.7 / 448.8 / 449.4 | 1203.9 / 1203.0 / 1203.7 |

More displayed groups and fewer same-note edges do not demonstrate better categories. The control is slower because disconnected vectors still participate as singleton candidates throughout the unchanged persistence calculation. Nothing was dropped to speed it up. Runs were sequential, used one numerical thread, and stayed below the 6 GiB address-space limit. No paid inference was used.

## Inspect in the existing TUI

```bash
# Restricted graph: the Satoshi/Sophia/recipe mixture above.
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-hidef-hierarchy.sh --graph-policy mutual_best_per_note --start-at 1117

# Restricted graph: the surviving 13-note coffee group.
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-hidef-hierarchy.sh --graph-policy mutual_best_per_note --start-at 963

# Same-count strongest-edge control: its 17-note coffee group.
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-hidef-hierarchy.sh --graph-policy strongest_edges_matched --start-at 930

# Preserved original result.
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-hidef-hierarchy.sh --start-at 951
```

To inspect a repeat, place `124` or `125` before `--graph-policy`; IDs differ between runs. Omit `--start-at` to start at the root. Use `j/k`, `h/l`, `U` for parents, and `F` to focus. Enter on a mask opens its complete original note. `a` reveals parent masks hidden because their notes already occur recursively below them. Children remain nested, shared groups retain their actual memberships, and one-note groups remain hidden only in the display.

Starting at a group with several ancestor routes opens their shared ancestry, rather than choosing one parent path for you.

## What this establishes

This particular mutual-choice restriction is not justified as the next default. Repeated contributions from one note can affect graph construction, but removing those contributions this way is not a sufficient repair. It also removes support for useful groups.

The equal-edge-count control is important: merely having fewer edges does not explain a general improvement, and clean surviving groups can conceal lost coverage. These results do not rule out graph-based hierarchy construction or every form of source balancing. They do rule out claiming that the proposed restriction has solved the observed hierarchy problem.

This comparison kept the HiDeF settings frozen to isolate the graph change. It is not a separately optimized configuration search for each graph.

## Verification and saved data

`./comparison.json` records graph fragmentation, note coverage, group sizes, all preselected group correspondences, and repeat-seed intersections. It was produced by a read-only checker:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 sse_multivector/compare_hidef_graph_policies.py
```

All nine runs passed manifest/source checks, retained-edge reconstruction, partition coverage, consensus membership checks, and exact reduced containment checks. All three original-policy runs exactly reproduce HDFv1's raw memberships, candidates, persistence, and DAG. A separate read-only audit independently verified the graphs, all 2,178 partitions, original replay, and preservation of all 30 committed HDFv1 files.

The implementation was tested with expected failures before changes. Verification passed 20 HiDeF/policy tests, seven comparison tests, seven launcher tests, and 55 existing Rust hierarchy/CLI/TUI tests. Every saved run loads through the real viewer; live expansion, scrolling, mask display, and exit were checked. No Rust implementation or existing approved tests were changed.

Each `POLICY/seedSEED/` directory contains configuration, actual graph, raw partitions, candidate memberships, persistent groups, strict DAG, note projection, viewer hierarchy, timings, and a manifest. No stage was discarded. To repeat a run, choose a new output directory:

```bash
sse_multivector/run-hidef-experiment.sh 123 /tmp/hdfv2-new-repeat --graph-policy mutual_best_per_note
```

The launcher refuses an existing output directory. Add `--plan` to inspect configuration without running discovery. The new directory keeps a repeat separate; its configuration records the policy, seed, and code/dependency hashes.

**Selected release data:** The [publication catalog](../../../docs/experiments/publications.csv) identifies the compact final-result export derived from the saved source:

- `numerical/comparison-bbb238e60ef6c956` — original `comparison.json`, bound by its recorded source SHA-256.

The export uses the publication format; the original files referenced above remain outside this checkout. Downloads are still being prepared.
