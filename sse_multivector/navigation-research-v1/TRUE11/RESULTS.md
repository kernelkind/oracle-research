# TRUE11 — Native answers versus the fixed cutoff

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

**Native answers remove both cycles, but also remove useful parent–child relationships.** This produces an acyclic graph, not a demonstrated solution to category placement.

No new inference was needed. Both graphs use exactly the same 58 categories, 232 masks, 77 notes and 3,306 saved directional outputs. The two previously reviewed Coffee and Bitcoin equivalences remain unchanged. No other categories were consolidated, relabeled or moved by hand.

## What changed

For proposed parent A and child B, TRUE originally received:

```text
premise: This text is about {B}. hypothesis: This text is about {A}.
```

It saw category titles, not notes or masks. TRUE10 accepts a connection when the saved score exceeds 0.142. TRUE11 instead accepts it when TRUE's saved generated answer is Yes. Native answers are not reconstructed using a 0.5 cutoff.

| Measurement | Fixed cutoff — TRUE10 | Native answers — TRUE11 |
| --- | ---: | ---: |
| Accepted connections | 88 | 48 |
| Cycles | 2 | 0 |
| Connections after removing redundant shortcuts | Withheld because of cycles | 36 |
| Categories / original notes retained | 58 / 77 | 58 / 77 |

All 40 changed decisions are cutoff Yes / native No. Across direct and indirect routes, 64 parent–descendant relationships disappear; none are added. Twelve native connections are redundant shortcuts: removing them preserves every remaining route and allows categories to retain multiple parents.

## What improves

Native answers reject these two incorrect reverse connections:

- **Food consumption → Food:** Food includes more than consumption, including ingredients and preparation. The cutoff accepted this at 0.223126.
- **Dishes with Toppings or Seasonings → Prepared foods:** prepared food need not have toppings or seasonings. The cutoff accepted this at 0.303842.

The correct directions remain. Food consumption therefore stops inheriting everything under Food; Dishes with Toppings or Seasonings stops inheriting everything under Prepared foods.

All 58 categories and 77 notes can now be reached by starting at categories with no parent. The cyclic cutoff graph reached only 28 categories and 41 notes under that starting rule. This is a structural consequence, not a semantic accuracy score; neither graph deleted any notes.

## What gets worse

These useful relationships disappear without an alternative route:

| Parent | Missing child | Saved score | Child's notes available under parent: cutoff → native |
| --- | --- | ---: | ---: |
| Food Preparation and Dining | Cooking Times | 0.251294 | 2 → 0 |
| Food Preparation and Dining | Making Chicken Stock | 0.163581 | 2 → 0 |
| Foods featuring meat or seafood | Meat-based meals in a crockpot | 0.277598 | 2 → 0 |
| Foods featuring meat or seafood | Brisket | 0.149946 | 2 → 0 |
| Tomatoes | Breakfast foods made with tomatoes | 0.318855 | 2 → 0 |

For example, Cooking Times includes these actual masks:

- V894: ⟦Spaghetti Bolognaise⟧ ⟦Simmer⟧ ⟦low heat⟧ ⟦45min-1hr⟧
- V368: ⟦bread pans⟧ ⟦Takes about 5-6 min⟧ ⟦cook⟧

These concern food preparation. Native answers leave Cooking Times and Making Chicken Stock directly under Food, but outside Food Preparation and Dining. A user entering food preparation would miss those notes, even though they still exist elsewhere.

The complete [changed-decision record](./CHANGED-DECISIONS.md) gives every changed direction, exact scores, both categories' masks, routes and note availability. These are not just missing shortcuts: the table above checks that the notes are unavailable through other children too.

## What remains unchanged or uncertain

Coffee keeps the same three children: Coffee Bean Preparation, Having drunk coffee, and Appreciating Coffee for Its Flavour. Its own five notes expand to nine through those children in both graphs.

Both rules still miss **Foods featuring meat or seafood → Steak**. Neither of Steak's two notes is available under that parent. Changing the decision rule does not repair that ordinary-subject failure.

Not all removed relationships are clearly good or bad. Food versus beverages, and food products versus activities involving those products, still have scope ambiguities. The user's acceptance of Foods with sea salt under Dishes with Toppings or Seasonings was qualified, not an unequivocal boundary rule. Likewise, criticism of meat eating can still concern meat eating; rejecting it is not automatically an improvement.

The saved earlier assistant judgments remain inspection evidence, not ground truth. Repeated alias judgments and uncertain answers are identified explicitly. No overall accuracy percentage is inferred from them, and no claim is made that every remaining native connection is correct.

## Conclusion and current next step

Native answers provide cleaner structure while losing meaningful refinements. Neither rule is established as the replacement. Counts of connections or inherited notes alone cannot choose between them.

The user chose to inspect the native hierarchy before considering further model work. The existing category browser now displays the saved reduced graph, with all category IDs and titles unchanged. Shared categories remain accessible under each parent. No frontier-model prompt or experiment has been started.

## Inspect the hierarchy

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./sse_multivector/run-true-hierarchy.sh
```

- `j` / `k` selects a category; `Enter` descends.
- `N` shows the current category's original notes, including descendants, with all relevant masks overlaid together.
- In notes, `h` / `l` changes notes; `j` / `k` scrolls.
- `Backspace` returns through the category path actually visited; `Q` exits.

The neutral All notes root opens the 26 starting categories. The browser retains all 58 categories, all 36 reduced connections, and all 77 notes. It does not absorb single-child categories, choose one parent for shared categories, or repair semantic placements. Source masks from unrelated branches are excluded even when they belong to the same note.

The viewer uses schema version 2 of the existing category format to allow multiple parents while still rejecting cycles. Its input (`./categories.json`) is derived by [the exporter](../../true_graph_categories.py) from the frozen graph, memberships, original notes and note-ID mapping. Version 1 inputs retain their tree-only validation.

Viewer verification (`./viewer-verification.json`): 85 Rust integration tests, 96 TRUE Python tests and the launcher test passed. The actual terminal view was inspected, including category descent, all nine Coffee notes, combined masks and returning through the visited path. All saved graph memberships were independently checked.

## Records and verification

- [Native hierarchy: all categories, connections and masks](./GRAPH.md)
- [All 40 changed decisions with both categories' masks](./CHANGED-DECISIONS.md)
- Original notes, masks and native recursive memberships (`./native-notes.json`)
- Every changed category route (`./route-changes.json`) and note membership changes for all categories (`./note-changes.json`)
- Earlier judgments compared against both graphs (`./semantic-comparison.json`)
- Measurements (`./comparison.json`), [frozen plan](./plan.json), completion hashes (`./completion.json`), and independent verification (`./verification.json`)

The original graph comparison passed 92 TRUE production-path tests. Independent verification confirmed every saved score row, source mask, title, original membership, equivalence and baseline hash; the reduced native graph preserves all native routes. TRUE was not loaded or rerun, and no new paid compute was provisioned. The plan records a retrospective comparison, not a blinded new evaluation.
