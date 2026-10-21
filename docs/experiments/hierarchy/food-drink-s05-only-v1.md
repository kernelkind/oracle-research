# Original S05 local nodes only

Status: completed authorized numerical experiment. The user requested repeating
the [S05-local-entry rerun](food-drink-s05-inside-v1.md) with unassigned entries
excluded. This uses original S05 from the [100-note review](food-drink-hundred-epsilon-v1.md).
No synthetic node is included. No production policy or source code was changed.

## Controls

The input is exactly **113 original local L1 entries across 58 distinct notes**.
All 361 originally unassigned entries and all 254 entries from the other 47
selected groups are excluded. Native ASv6.100 / Bootstrap-v133 titles, meanings,
original vector identities and worker receipts are reused unchanged.

The existing numerical CLI reruns HDBSCAN with angular distance,
`min_samples=3`, `min_cluster_size=2`, excess-of-mass selection. The same
middle-approximately-80% curve-bend rule selects epsilon on the new tree.
There are no new teacher calls, encodings or paid charges. This diagnostic is
not a new official HR run and updates no hierarchy UI.

## Result

| Measure | S05 plus original unassigned inputs | S05 only |
|---|---:|---:|
| Clustering inputs | 474 | 113 |
| Distinct input notes | 97 | 58 |
| Assigned inputs | 176 | 112 |
| Selected groups | 26 | 15 |
| Epsilon sections | 12 | 12 |
| Represented distinct notes | 77 | 57 |
| Epsilon | 0.882608358725754 | 0.579583723151021 |

The largest new section is **S02**, containing new G02, G05 and G10: Food,
food preferences/enjoyment and food preservation/security. It represents
**38 distinct notes**. Other sections expose Foodstr (two groups, 10 notes),
cooking/equipment (11 notes), meat (4), eating/nutrition (3), diets (3), recipes
(3), lunches (4), bread/baking (5), smoking (2), restaurants (3) and dogs (3).
Note memberships overlap.

The rule now cuts inside the original S05 branch. It selects the interval
between `0.6195031634670014` and `0.5396642828350408`; their midpoint is the
epsilon above. There are 14 distance levels, with two from each end omitted
for fitting, leaving 10. Every newly selected group remains in the final cut.

One original entry becomes unassigned in the new HDBSCAN result:

- Local ID: `L00344`; original local number `11`.
- Title: **Eating animals**.
- Meaning: human ingestion of killed animals' flesh or other body parts as
  food, whether killed by the eater or someone else.
- Note ID: `be8d07d42b8f14d60ccfe50b63c93c5c607c589129d79d9f6b560948150542bc`.

That note has no other input in this subset, so represented coverage is 57 of
58 notes. This is a clustering-membership change, not an epsilon-cut omission.
No repair, assignment override or semantic fault attribution was made.

## Evidence and verification

The unchanged existing implementation is from `ef2896a3`. Native state/vector
receipts, HDBSCAN request/result identity, exact 113-entry scope, original-only
IDs and all 15 groups' unique coverage by 12 sections were verified. Source
state SHA256 remains
`9c8e6610cdcb5e6ecfa4dd1675f83da949570d317cadc3422beded6786799555`.
The PNG was visually inspected. No new test or code change was needed for
this use of the existing CLI.