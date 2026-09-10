# HDFv1

HiDeF on the unchanged I03 graph: 100 notes, 916 canonical vectors, 945 original vector IDs. No new subjects, masks, embeddings, or labels were generated. CREC-124.

## Inspect

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-hidef-hierarchy.sh
```

The default is seed 123. Pass `124` or `125` to inspect the independent repeat runs. Numeric group IDs identify groups only within that run.

Use `j/k` to move, `h/l` to collapse/expand, `F` to focus, and `U` to go up. Select a mask and press Enter for the complete original note. `a` reveals parent masks normally hidden because their notes already occur in a child. `?` opens help.

Children remain nested. A shared child retains the same group ID and membership along every parent path. Groups containing only one distinct note are absent from the display but preserved in the data. An edge marked `same notes` changes the vector set without changing the returned notes. This is the unsimplified experimental structure, not a finished navigation product.

Useful starting points for primary-run inspection:

```bash
# Coffee: inspect the children, then U to inspect its broader parent.
sse_multivector/run-hidef-hierarchy.sh 123 --start-at 951

# Egg groups; this shared group opens all ancestor routes rather than choosing one.
sse_multivector/run-hidef-hierarchy.sh 123 --start-at 976

# A problematic local group, not just a questionable broad parent.
sse_multivector/run-hidef-hierarchy.sh 123 --start-at 1046
```

These comments describe inspection targets; no titles are stored in the hierarchy.

## What was tested

[PLAN.md](./PLAN.md) was written before the first real-data run. At each of 242 resolutions, weighted Leiden independently partitioned the same saved graph. Actual pinned HiDeF persistence then combined recurring communities. Every raw partition and the membership before and after that combination are saved.

Distinct resulting sets were connected by exact vector containment. No parent gained a vector to make a child fit. Multiple parents were retained; redundant direct edges were removed. The resulting edges and unchanged memberships were independently checked against the released Weaver API at exact containment.

The primary seed is 123. Seeds 124 and 125 repeat the complete experiment independently, with every other setting unchanged. They were not pooled and were not used to tune settings. The preselected single-resolution reference is gamma 1.0148, sample index 167, yielding 12 flat groups in each run. This distinguishes a single Leiden partition from the multiresolution result without selecting a reference by its apparent semantic quality.

## Results

| Measure | Seed 123 | Seed 124 | Seed 125 |
| --- | ---: | ---: | ---: |
| Raw partitions | 242 | 242 | 242 |
| Raw groups across all partitions | 6,808 | 6,753 | 6,764 |
| Persistent families | 266 | 263 | 274 |
| Distinct groups, including root | 263 | 261 | 270 |
| Displayed groups, including root | 240 | 236 | 244 |
| Immediate children of root | 65 | 64 | 70 |
| Parent-child edges excluding edges from root | 332 | 352 | 329 |
| Those edges returning fewer notes | 327 | 341 | 320 |
| Those edges returning the same notes | 5 | 11 | 9 |
| Groups with multiple parents | 87 | 99 | 89 |
| Longest path, edges from root | 6 | 6 | 6 |
| Local runtime, seconds | 7.000 | 6.931 | 6.958 |
| Peak process memory, KiB | 237,320 | 237,564 | 236,452 |

Returning fewer notes does **not** establish a more specific subject. These are structural counts, not semantic pass rates. The primary displayed hierarchy has 276 edges excluding root edges; 271 return fewer notes. Across the full saved DAG, unfolding all routes produces 473 group appearances, with no group appearing along more than seven root paths.

### Repeatability

Of the primary run's 262 non-root vector sets, 143 recur exactly with seed 124 and 134 with seed 125. There are 112 exact vector sets common to all three runs. Of the primary run's 249 distinct non-root note sets, 161 recur exactly with seed 124 and 157 with seed 125; 138 recur in all three.

The mean best-match vector-set Jaccard is 0.8608 against seed 124 and 0.8602 against seed 125. For distinct note sets it is 0.8986 and 0.8995. These nearest matches can reuse the same counterpart; they are not semantic judgments, one-to-one alignments, or evidence that whole paths are stable. There are also more matching opportunities in a multiresolution result than in the 12-group single-resolution reference.

Several inspected examples recur. The egg group 976 matches seed-124 group 972 and seed-125 group 975 exactly. The alcoholic-drinks group 1027 matches 1032 and 1033 exactly. The problematic group 1046 also matches seed-124 group 1053 and seed-125 group 1049 exactly: repeatability preserves bad groups too. The physical-activity group 1023 does not recur exactly; its nearest matches add two vectors and one note in each other run.

## Independent semantic inspection

The inspection used exact masks and complete original notes, not the generated subject strings. It covered every mask in the ten largest non-root groups, the medium-group inventory, and complete memberships of selected coffee, eggs, cooking-equipment, dietary, exercise, alcohol, and problematic branches. This is an analyst inspection, not user approval or an exhaustive scored evaluation of every path.

All IDs below refer to `HDFv1-seed123`. Descriptions are explanations of the inspection, not proposed stored category labels.

### Useful local groups exist

- **951, 15 notes:** coffee drinking, preparation, preferences, and coffee-shop experiences. For example V410/N052 is `⟦grind coffee beans⟧`, V504/N060 is `⟦Made⟧ ⟦coffee with raw cream⟧ ⟦today⟧`, and V294/N038 is `⟦Baby Got Back⟧ ⟦playing⟧ ⟦coffee shop⟧`. Some masks are only tags or dependent fragments; this is not a claim that extraction quality is perfect.
- **976, seven notes:** eggs, including omelettes, preserved eggs, laying hens, egg meals, and egg yolk in coffee. V733/N080 is `⟦Our chickens⟧ ⟦laying an egg a day⟧`; V505/N060 is `⟦Made⟧ ⟦coffee with⟧ ⟦raw egg yolk today⟧`. Those are different notes and different uses of eggs, not necessarily a bad combination.
- **1037, five notes:** equipment used to cook food. It includes V006/N001 `⟦my rocket stove⟧ ⟦just⟧ ⟦charcoal grill⟧ ⟦j-tube added⟧`, V134/N019 `⟦brisket⟧ ⟦homemade barrel  smoker⟧`, and the cast-iron cookware masks from N056.
- **1023, three notes:** physical activity: a gym session, stretching, walking/biking, and exercise advice.
- **1027, four notes:** alcoholic drinks in meals, recipes, and gifts. This includes both wine and gin; describing it as wine alone would be incorrect.

These local successes do not certify their ancestors or require one uniquely correct subdivision.

### Smaller groups are not automatically clearer subjects

The coffee path **951 → 981 → 1059** returns **15 → 11 → six notes**. The last group still includes plain coffee masks, grinding coffee beans, roasting beans, and music playing at a coffee shop. There is clear shared coffee meaning, but this inspection did not identify a corresponding progression of increasingly specific categories. Shrinking membership is not sufficient evidence for semantic narrowing.

The egg path **976 → 1002 → 1019** returns **seven → six → six notes**. The last edge removes only two vectors:

- V819/N091: `⟦Century eggs⟧ ⟦called alkalized or preserved eggs⟧`
- V506/N060: `⟦Made my coffee⟧ ⟦raw cream⟧ ⟦raw egg yolk today⟧`

Other vectors retain both source notes, so that transition cannot narrow note discovery. The viewer marks it `same notes`. The preceding seven-to-six-note transition drops the breakfast-burrito note while retaining several other egg uses; no clear narrower subject was established for it either.

### Some groups already mix unrelated meanings before ancestry is constructed

**1046** contains these masks, among its aliases:

- V189/N024: `⟦satoshi⟧`
- V516/N061: `⟦Sophia⟧ ⟦#nostrbaby⟧`
- V011/N002: `⟦Sorrento's Savory Stroll⟧`
- V848/N093: `⟦Khyber Pass⟧ ⟦St Marks Place⟧ ⟦jersey⟧ ⟦now⟧`
- V400/N050: `⟦our town⟧ ⟦St Michel de L'Attalaye⟧ ⟦haiti⟧`

The complete notes concern a general red-flags post with hashtags, a five-month-old baby, a food tour, a restaurant's location, and plans for a pizza restaurant. The infant and Satoshi masks do not establish a shared food/place subject with the others. The problem exists in the discovered group itself; attaching it under a different parent would not remove those members.

Several largely food-related broad groups also contain these unrelated tag/name meanings, and V387/N048 `⟦Linux⟧`. Their presence is evidence of contamination, not proof that every member of those broad groups is unrelated. This experiment does not isolate whether the responsible error originated in extraction, SSE geometry, graph construction, Leiden discovery, or persistence aggregation.

**1021**, containing two notes, is another questionable grouping: bathroom safety-grab-bar installation in N092 is combined with changing a coffee shop's router passwords in N065. Both involve changing a facility, but this inspection found no useful narrower shared subject. That remains an analyst judgment for review, not a theorem based on their different vocabulary.

### Exact containment is not the only outstanding limitation

The primary result records 845 ordered group pairs whose note sets permit containment but whose vector sets do not. These include equal-note-set pairs and are not 845 demonstrated missing parent relationships. Different masks from the same note can express different subjects. Every blocking vector is saved for inspection; none was replaced or dropped to force an edge.

This result produced many exact-containment edges already. Thus a lack of any possible nesting is not the main explanation for the observed coffee/egg paths: membership can nest while the descriptions fail to narrow. Bad independent groups and redundant semantic levels are also present. Changing containment alone would not establish meaningful parenthood.

## What this establishes

The weighted multiresolution construction works mechanically on the frozen corpus, uses little local compute at this size, and produces inspectable nested and overlapping groups without expanding parent memberships. Some local groups are recognizable.

It has **not** established a coherent overall navigation hierarchy. Persistence does not by itself ensure coherent groups or meaningful refinements; exact set containment does not supply those guarantees either. These are findings about this graph, representation, and fixed procedure—not a rejection of every multiscale method or of SSE in general.

No parameter was changed after semantic inspection. No group was hand-repaired. No labels were used to make the output appear coherent. All three runs remain available for user review.

## Saved evidence

Each `HDFv1/seed123`, `seed124`, and `seed125` directory contains:

| File | Content |
| --- | --- |
| `configuration.json` | Frozen parameters, ordered resolution schedule, graph/source/code hashes, exact dependencies |
| `graph.net` | Byte-identical copy of the original I03 weighted graph |
| `raw-partitions.json` | Every native partition and weighted objective; the preselected single-resolution reference |
| `candidates.json` | Every raw group and the community-similarity graph |
| `persistent-groups.json` | Actual HiDeF consensus, source candidate families, instance and distinct-resolution counts |
| `strict-dag.json` | Deduplicated complete sets, all immediate containment edges, independent Weaver check |
| `note-projection.json` | Same-note transitions, one-note groups, note-only containment and exact blocking vectors |
| `hierarchy.json` | Viewer input with original canonical IDs, aliases, complete vector/note memberships |
| `timings.json` | Runtime per stage and peak process memory |
| `manifest.json` | SHA-256 of every other file in the run directory |

Historical absolute paths in I03's copied source metadata remain provenance. The runner and launcher load the matching files from this checkout and verify hashes; they do not require the old worktree.

## Reproduce and verify

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp

# A new output directory is mandatory; existing results are never overwritten.
sse_multivector/run-hidef-experiment.sh 123 /tmp/hidef-seed123-replay --plan
sse_multivector/run-hidef-experiment.sh 123 /tmp/hidef-seed123-replay

# Validate a saved run without opening the terminal UI.
sse_multivector/run-hidef-hierarchy.sh 123 --check

# Rebuild the viewer if needed. Do not run concurrent Cargo invocations.
CARGO_TARGET_DIR=target/infomap-review-build CARGO_BUILD_JOBS=2 CARGO_PROFILE_DEV_DEBUG=0 \
  nix develop --command cargo build --bin hdbscan-hierarchy

nix develop --command nix shell --inputs-from . nixpkgs#python311 --command \
  uv run --no-project --python python3.11 \
  --with-requirements sse_multivector/hidef-requirements.lock \
  python -m unittest discover -s sse_multivector -p test_hidef_experiment.py
```

Eleven Python production-path tests and 113 Rust hierarchy integration tests passed, along with five launcher tests and checks of all three real artifacts. The minimal unsupported-CLI and missing-launcher tests failed before implementation. Tests exercise exact weights, graph IDs, consensus, serialization, repeatability, no-overwrite behavior, source integrity, shared-child navigation, nested masks, and the existing hierarchy modes. Both an independent viewer audit and the main agent checked the live terminal.

An independent read-only artifact audit verified every partition, consensus family, containment edge, note union, and manifest. It also recomputed the weighted RB objective for all 726 saved partitions directly from the graph and memberships; every score agreed within 4.4e-11.

The released HiDeF commit is `3d016a375ac52feda0e0b2a3ace917c834f3a3a9`, reporting version **1.1.5**. Runtime testing caught an incompatible newer SciPy wildcard import and a NumPy integer serialization issue before any real-data run. Final pinned versions and source hashes are in each configuration and `../hidef-requirements.lock`. The upstream `louvain` import emits a deprecation warning despite using Leiden; the required setuptools version is pinned. No upstream algorithm was patched. HiDeF's LICENSE is BSD-3-Clause; the graph libraries have their own licenses, including GPL licenses for igraph/Leidenalg.
