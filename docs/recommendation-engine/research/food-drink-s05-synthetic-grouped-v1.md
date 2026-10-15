# Synthetic S05 without original unassigned nodes

Status: completed authorized numerical experiment. The user requested returning
to the [synthetic-node rerun](food-drink-s05-recluster-v1.md) while excluding
ungrouped nodes. As stated before execution, this excludes the 361 entries
unassigned in the **original HR22 review**. It does not instead retain the
38 entries that became assigned in the later synthetic-node rerun.

## Exact comparison

The input is **255 vectors**: the existing Food and domestic animals synthetic
node plus 254 original entries from the original groups outside S05. The
original S05's 113 entries remain replaced by the same one node, with their
58-note associations unchanged. The 361 originally unassigned entries are
excluded. Eligible input support covers 94 distinct notes.

All 255 normalized inputs, including opaque IDs and vector values, exactly
match the corresponding inputs in the earlier 616-input synthetic-node run.
The synthetic title, meaning and its original SSE vector are reused unchanged.
No new teacher calls, encodings or paid charges occur. HDBSCAN still uses
angular distance, `min_samples=3`, `min_cluster_size=2`, excess-of-mass selection;
the same approximately middle-80% curve-bend rule chooses epsilon.

## Result

| Measure | Synthetic node with original unassigned inputs | Without them |
|---|---:|---:|
| Inputs | 616 | 255 |
| Distinct input notes | 100 | 94 |
| Assigned inputs | 293 | 249 |
| Selected groups | 51 | 44 |
| Epsilon sections | 40 | 33 |
| Represented distinct notes | 96 | 80 |
| Synthetic node assigned | G31, inside S08 | Unassigned |
| Epsilon | 0.8912946305292836 | 0.9425191168536686 |

**The synthetic node becomes unassigned.** It was supplied to HDBSCAN as the
same one vector; it is absent from selected groups before epsilon selection.
Five retained original inputs also become unassigned: L00089, L00118, L00503,
L00507 and L00552. The final selected groups represent 80 of 94 eligible notes.
No special assignment or graph repair was applied. This is evidence about
clustering sensitivity, not a semantic rejection of the synthetic definition.

| Largest new sections | Groups | Distinct notes |
|---|---|---:|
| S10: appreciation, positive feelings, greetings, hopes and aspirations | G04, G12, G16, G22, G42 | 27 |
| S20: Nostr and GrowNostr | G19, G20 | 24 |
| S03: coffee, coffee businesses and Coffeechain hashtags | G03, G25, G32 | 19 |
| S09: breakfast, mornings and sleep | G15, G18, G38 | 13 |
| S08: chicken-related topics and eggs | G10, G27 | 10 |

There are 43 distance levels; five from each end are excluded while fitting,
leaving 33. The selected interval is between `0.9591060511300664` and
`0.9259321825772708`. Their midpoint is the epsilon above. Every selected
group is covered once by the section cut; unassigned inputs are not displayed
as invented groups. The synthetic node is consequently absent from the SVG.

## Native reuse and verification

The reusable project replacement CLI supports preparation from an existing
replacement with `--from-replacement` and optional `--exclude-unassigned`.
It validates frozen sources and worker receipts, reuses the completed encoding,
and freezes the filtered input IDs, excluded IDs and exact source plan hash.
Synthetic support is expanded when determining eligible and represented note
sets. The source preparation and raw receipts remain unchanged.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp-food-drink-s05-synthetic-grouped-v1
python3 -m sse_multivector.hdbscan_section_replacement prepare \
  target/food-drink-s05-synthetic-grouped-v1 \
  --from-replacement ../oracle-mvp-food-drink-s05-recluster-v1/target/food-drink-s05-recluster-v1 \
  --exclude-unassigned
python3 -m sse_multivector.hdbscan_section_replacement collect \
  target/food-drink-s05-synthetic-grouped-v1 \
  --name food-drink-s05-synthetic-no-ungrouped
```

A production CLI test first failed because cached replacement reuse/filtering
was unavailable. It now checks exact grouped-only selection, synthetic-vector
reuse without an encoder call, original support, unchanged source paths and
actual native collection. Sixteen replacement, selection, epsilon, native
source and HDBSCAN tests passed. The real trial's 255 normalized inputs were
compared exactly to their earlier counterparts; the PNG was visually inspected.

The ignored output holds the source-bound replacement plan, actual new request/
result, full analysis, and uniquely named `food-drink-s05-synthetic-no-ungrouped.svg`,
`.png` and `.md`. Retain the task worktree for those artifacts and its frozen
code paths. No official HR run, production policy, prompt or hierarchy UI was
changed. The original synthetic vector is referenced directly from its existing
worker receipt rather than copied or recomputed.

## Approved next replacement

Use the original HR22 grouping to decide which original entries remain eligible
throughout replacement. Keep originally grouped entries as separate inputs when
a later run leaves them unassigned; exclude originally unassigned entries.
Synthetic nodes retain their original entries' associations and remain eligible
even when temporarily unassigned. Inclusion does not force group assignment.

The next selected section is S10: 39 current entries in five groups, representing
27 distinct notes. Consolidate each group separately, then consolidate those five
generated definitions into one synthetic section with no parent. Four groups
have exact saved native definitions; G04's seven-entry membership differs and
requires a new definition. Reuse the four exact results, making two new teacher
calls rather than sending all 39 entries directly to one consolidation.

Replace S10's 39 inputs with its one synthetic node. Keep the six currently
unassigned inputs, including Food and domestic animals: they derive from
originally grouped entries. The next pool therefore contains 217 inputs
(`255 - 39 + 1`), with the original 361 unassigned entries still excluded.
The existing synthetic definition, original associations, HDBSCAN settings and
epsilon rule stay unchanged. This is the approved experiment plan, not a claim
that the S10 calls or replacement have already completed.
