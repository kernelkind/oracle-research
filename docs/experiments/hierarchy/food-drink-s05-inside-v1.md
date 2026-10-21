# Original S05 entries plus original unassigned entries

Status: completed authorized numerical experiment. The user requested a rerun
using only original local entries inside S05, excluding other selected groups,
including unassigned entries, and excluding the synthetic node. This uses
**original S05** from the [100-note review](food-drink-hundred-epsilon-v1.md),
not the later S05 label in the [replacement rerun](food-drink-s05-recluster-v1.md).
It changes no production HiGen policy, prompt or saved hierarchy.

## Input and controls

The 113 original S05 entries plus all 361 originally unassigned entries give
**474 original vector inputs across 97 distinct notes**. The other 254 grouped
entries, belonging to 47 original groups, are excluded. No synthetic entry is
included. Unassigned status is taken from the original 728-entry HR22 result;
the previous replacement rerun's 323 unassigned entries are not this source.

Original ASv6.100 / Bootstrap-v133 titles and meanings and their native vectors
are reused exactly. There are no new encodings, teacher calls or paid charges.
The HDBSCAN configuration remains angular distance, `min_samples=3`,
`min_cluster_size=2`, excess-of-mass selection. HDBSCAN is rerun on the filtered
vectors; the old selected groups are not merely hidden in an existing tree.
The same approximately middle-80% curve-bend rule chooses epsilon from the
newly computed selected-group tree.

The numerical review CLI now supports `--section S05 --include-unassigned`.
It verifies the native source state and original clustering, selects original
IDs in saved order, and records the included/excluded counts and hashes.
`--name` gives the SVG and table a unique filename. Default saved-tree and
whole-source modes retain their behavior. This capability is experimental
research support, not automatic canonical hierarchy construction.

## Result

| Measure | Result |
|---|---:|
| Original S05 inputs | 113 |
| Included original unassigned inputs | 361 |
| Total inputs | 474 |
| Distinct input notes | 97 |
| Assigned inputs | 176 |
| Remaining unassigned inputs | 298 |
| Selected HDBSCAN groups | 26 |
| Epsilon sections | 12 |
| Represented distinct notes | 77 |
| Chosen epsilon | 0.882608358725754 |

All 113 original S05 inputs remain grouped. All 15 original S05 groups retain
their exact membership. Another **63 originally unassigned inputs** become
grouped, forming the 11 other groups. No synthetic title or meaning is used.

The largest section, **new S01**, contains exactly the same 113 entries and
58-note union as original S05. Its 15 groups still share one section. The
chosen epsilon lies between split distances `0.9491119306298481` and
`0.8161047868216599`; the latter is original S05's outer join. Thus this cutoff
keeps S05 together rather than dividing its internal branches.
The curve has 25 distinct distance levels; three from each end are excluded
for fitting, leaving 19. The final cut still includes all 26 groups.

| Largest sections | Distinct notes |
|---|---:|
| S01: original food/domestic-dog section | 58 |
| S02: coffee, cacao/chocolate, caffeine and related topics | 10 |
| S03: emotions and assessments of the day | 9 |
| S04: health, wellbeing and personal progress | 7 |
| S06: time, stress, pace and boredom | 6 |

Note sets overlap. Newly formed groups and their numerical placement are not
semantic gold; for example Sunflower seeds / Seed oils / Sunlight warrants
review. No new synthetic section meanings were generated or applied.

## Reproduction and retained evidence

The ignored output contains `sources.json`, the actual new HDBSCAN request and
result, complete `analysis.json`, and uniquely named
`food-drink-s05-originals-and-ungrouped.svg`, `.png` and `.md`.
The original artifacts retain their frozen code/source bindings.
Original state SHA256 remains
`9c8e6610cdcb5e6ecfa4dd1675f83da949570d317cadc3422beded6786799555`.
This diagnostic is not a new official HR run and refreshes no hierarchy UI.