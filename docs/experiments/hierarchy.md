# Official hierarchy experiments

These are the 37 runs recorded in the comparison workbook, HR03–HR39.
The status and output counts below are the recorded results, not a new evaluation.
Completion does not imply full coverage or semantic approval.

Read the [run descriptions and findings](hierarchy/runs.md)
for interpretation. [Exact settings and source versions](hierarchy.csv),
[corpora](corpora.csv) and the [full parameter ledger](hierarchy/parameters.csv)
connect each run to its evidence and ordered note selection.

| Run | Input notes | Output notes | HiGen | Recorded status |
| --- | ---: | ---: | --- | --- |
| HR03 | 50 | 50 | Staged / guarded16 | Complete |
| HR04 | 12 | 12 | traversal-v24 | Complete |
| HR05 | 24 | 24 | traversal-v24 | Complete |
| HR06 | 8 | 8 | Staged / guarded16 | Deprecated |
| HR07 | 50 | 50 | Staged / guarded16 | Deprecated |
| HR08 | 24 | 23 | V2 | Partial |
| HR09 | 24 | 24 | V2 | Complete |
| HR10 | 50 | 48 | V2 | Stopped |
| HR11 | 6 | 6 | V3 | Complete |
| HR12 | 12 | 12 | V3 | Complete |
| HR13 | 24 | 24 | V3 | Complete |
| HR14 | 50 | 50 | V3 | Complete |
| HR15 | 24 | 24 | V3 | Complete |
| HR16 | 50 | 50 | V3 | Complete |
| HR17 | 24 | 19 | V3.1 | Complete |
| HR19 | 50 | 35 | V3.1 | Complete |
| HR18 | 24 | 19 | V3.2 | Complete |
| HR20 | 50 | 30 | V3.2 | Complete |
| HR21 | 50 | 46 | V4.1 | Complete |
| HR22 | 100 | 94 | V4.1 | Complete |
| HR23 | 100 | 93 | V4.2 | Complete |
| HR24 | 100 | 94 | V4.3 | Complete |
| HR25 | 100 | 90 | V4.4 | Complete |
| HR26 | 200 | 198 | V4.1 | Complete |
| HR27 | 50 | 46 | V5 | Complete |
| HR28 | 100 | 94 | V5 | Complete |
| HR29 | 200 | 198 | V5 | Complete |
| HR30 | 1000 | 976 | V5 | Complete; review UI checked |
| HR31 | 100 | 100 | V5.1 | Complete; review UI checked |
| HR32 | 200 | 176 | V5.1 | Complete; UI shows 176 under roots; 24 unclaimed hidden |
| HR33 | 200 | 189 | V5.2 | Complete; review UI checked; 189 under roots; 11 unclaimed hidden |
| HR34 | 200 | 199 | V5.3 | Complete; 199 beneath roots; membership scope issue flagged |
| HR35 | 1000 | 718 | V5.3 | Complete; partial root coverage (718/1000) |
| HR36 | 1000 | 683 | V5.3 | Complete; partial root coverage (683/1000) |
| HR37 | 1000 | 622 | V5.3 | Complete; partial root coverage |
| HR38 | 2000 | 1328 | V5.3 | Complete; partial root coverage |
| HR39 | 5000 | 2693 | V5.3 | Complete |

## Methods and investigations

The [current HiGen V5.3 reference](../design/hierarchy-generation.md) describes
new construction. Earlier [V3 methods](hierarchy/higen-v3.md) and
[V4 methods](hierarchy/higen-v4.md) explain their recorded trials.
[Performance measurements](hierarchy/performance.md), [scaling evidence](scalability.md)
and the [HR09 investigation](hierarchy/hr09-investigation.md) cover important
runtime and semantic limits.

The numerical investigations leading to recursive construction are grouped by
question:

- Cut selection: [HR21 partition controls](hierarchy/hr21-root-partition-controls-v1.md)
  and [trimmed-bend epsilon](hierarchy/hr21-epsilon-selection-v1.md).
- Corpus controls: [100 Food/Drink notes](hierarchy/food-drink-hundred-epsilon-v1.md),
  [50 Music notes](hierarchy/music-fifty-epsilon-v1.md) and
  [25 Food plus 25 Music notes](hierarchy/food-music-fifty-epsilon-v1.md).
- Input selection: [S05 with originally unassigned entries](hierarchy/food-drink-s05-inside-v1.md)
  and [S05 alone](hierarchy/food-drink-s05-only-v1.md).
- Synthetic replacement: [first root](hierarchy/food-drink-s05-root-v1.md),
  [reclustering](hierarchy/food-drink-s05-recluster-v1.md),
  [excluding original noise](hierarchy/food-drink-s05-synthetic-grouped-v1.md),
  [second replacement](hierarchy/food-drink-s10-synthetic-grouped-v1.md) and
  [six-root result](hierarchy/food-drink-six-roots-v1.md).

These records preserve actual controls, findings and failures. A numerical group
or visually appealing cut is not itself a validated semantic category.
