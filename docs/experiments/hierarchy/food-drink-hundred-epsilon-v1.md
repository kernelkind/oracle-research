# Food & Drink 100-note epsilon review

Status: completed experimental numerical review. The unchanged
[10%-trimmed bend rule](hr21-epsilon-selection-v1.md) was applied to all 100
Food & Drink notes. No production HiGen policy, prompt or canonical graph was
changed. This reuses HR22's saved data rather than starting a new HR hierarchy
run or generating synthetic section names.

## Source and controls

All 100 distinct IDs in
`sse_multivector/real-note-fine-segmentation-v1/corpus-selection-v1/notes.json`
match HR22's selected notes. Every original post text also matches. HR22 uses
a different saved order, which is retained; all notes are included.

Frozen state:
`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr22-v41/target/hierarchy-hr22-v41-hundred-note-v1/HR22/state.json`.
State SHA256:
`9c8e6610cdcb5e6ecfa4dd1675f83da949570d317cadc3422beded6786799555`.

The source uses ASv6.100 local hierarchies and Bootstrap-v133 titles/meanings.
Native state, original producer/encoder receipts and HDBSCAN request/result
identities were validated by the existing offline review CLI. Original SSE
title vectors retain their explicit-meaning context. HDBSCAN settings are
unchanged: angular distance, `min_samples=3`, `min_cluster_size=2`,
excess-of-mass selection. The selected groups remain atomic in the epsilon cut.

No new model calls, encodings, HDBSCAN executions or paid charges were needed.
The saved clustering already covers this exact corpus and configuration.

## Result

| Measure | Result |
|---|---:|
| Input notes | 100 |
| Original L1 entries | 733 |
| Existing null Bootstrap meanings | 5 |
| Reused encoded entries | 728 |
| Entries in selected groups | 367 |
| Unassigned encoded entries | 361 |
| Fixed HDBSCAN groups | 62 |
| Notes represented | 94 |
| Automatic epsilon | 0.8265007473450509 |
| Colored sections | 42 |

The selected split distance is `0.8368967078684418`; the next smaller full-curve
distance is `0.8161047868216599`. Their midpoint is the epsilon above. Every
selected group appears exactly once; the cut removes no groups or notes.
The six missing notes have no entries assigned to a selected HDBSCAN group.

Four sections combine multiple groups; the other 38 are singletons:

| Section | Groups | Contents | Distinct notes |
|---|---|---|---:|
| S05 | G02, G03, G04, G05, G15, G22, G23, G24, G25, G30, G31, G36, G50, G51, G52 | Meat, food/meals/preparation, Foodstr/Foodchain, preservation, dogs, smoking, eating, bread/baking, preferences, cooking/equipment, diets, restaurants, lunch and recipes | 58 |
| S09 | G20, G27 | Breakfast and waking/mornings | 10 |
| S12 | G07, G37, G47 | Coffee, coffee shops/chains and Coffeechain hashtags | 19 |
| S19 | G08, G17, G21, G33 | Appreciation/kindness, enjoyment/happiness, greetings and hopes | 26 |

Note sets overlap. These are numerical sections, not validated semantic parents.
In particular, G22's Dogs entries occur inside S05 and merit inspection before
using this grouping for construction. No semantic fault is assigned here.

## Artifacts and verification

- `food-drink-100-epsilon.svg` and `.png`: uniquely named full colored tree.
- `food-drink-100-groups.md`: complete compact group and section tables.
- `analysis.json`: frozen source hashes, projection, full curve, fitted points,
  interval and exact memberships.
- `../result-summary.json`: explicit bounded result and reuse accounting.

All 62 memberships and labels, exact section coverage and the selected section
count were checked. The PNG was visually inspected. Cutoff arrows remain
outside the branches. No code or prompt behavior changed, and no hierarchy
review UI was refreshed. The original source bindings identify those review artifacts.

Review G22's exact meanings within S05 before treating the food-colored section
as evidence of useful semantic containment.
