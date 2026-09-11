# Original-coordinate hierarchy experiments

The strongest current candidate is **unit-sphere diffusion, GDC09**, not the earlier slower Euclidean diffusion. Following the coordinate-motion diagnostic produced genuine additional parent–child structure: coffee→tea, sleep→daily routines, cookware→kitchen equipment, and literature→knowledge/writing. This remains a partial candidate, not a validated complete navigation system. Some memberships are weak, many successive nodes add examples without a new descriptive level, and coverage gaps remain.

[Continuation findings](./CONTINUATION.md) record the causal investigation, controlled changes, completed trajectory, robustness checks, and remaining counterexamples. The original runs below remain unchanged. The earlier conclusion that motion tracing was merely a future recommendation was premature; that work is now performed.

These are exploratory adaptations, not a benchmark ranking or a finding that the underlying papers are wrong. No category labels, subject edits, or mask edits entered the numerical experiments. The subsequently requested inspection browsers below read the saved results without running extraction, embedding, or clustering again.

## View GDC09

### Categories and original notes

```sh
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-diffusion-categories.sh
```

This reuses the existing category browser. Each screen lists **only the immediate child categories** of the current level. Enter or `l` descends, including into a leaf. `N` separately opens the **current category's** complete original notes, including every descendant and deduplicating source notes; it does not open the highlighted child's notes. Escape returns to the same category and selection, then moves up a level. `j/k` move or scroll, `h/l` change notes, `?` opens analysis/help, and `q` exits. Deep paths show the immediate parent and current category so the header cannot consume the note area. Add `--check` to validate without opening a terminal.

The browser starts at the full 100-note root and has **219 categories** after collapsing **141 parent–child steps** with identical recursive note sets. The highest native group survives each collapse, with narrower descendants promoted in their saved order. One-note group choices stay hidden; their notes remain at displayed ancestors. No note or underlying vector membership is deleted.

The two collapse rules are deliberately different:

- **Parent–child:** identical returned note sets collapse, even if the masks differ, because clicking would not narrow the notes.
- **Separate branches:** identical notes are only candidates for merging. The grouped masks must also express the same subject. The five repeated note sets in this run were checked and kept separate: their masks express different or insufficiently equivalent meanings. No automatic merge based only on note identity or matching titles is performed.

The assistant assigned titles bottom-up from the grouped masks, reading complete notes to clarify context. **Every displayed category has a content-based name.** The root choices are Everyday life, Hospitality, and Storms, Bitcoin and apocalypse. These are inspection descriptions, not clustering inputs or certified categories. A mixed-content name states what a group contains; it does not establish a relationship between those subjects. Some labels repeat across levels whose note sets differ; no narrower meaning was invented to disguise that limitation. Qualifications are in the separate analysis screen, not in place of category names or inside the original-note box.

`GDC09/categories.json` is the browser input. `category-titles.json` contains the authored labels and caveats; `category-mask-review.json` records the separate-branch decisions. `category-projection.json` maps all 838 native internal groups to the displayed groups and binds the saved inputs and output with checksums. `../export_diffusion_categories.py` reproduces the export into new output paths. It does not recompute coordinates or clusters. All 100 original notes remain available.

If the binary has not been built:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
CARGO_TARGET_DIR=target/infomap-review-build CARGO_BUILD_JOBS=2 CARGO_PROFILE_DEV_DEBUG=0 nix develop --command cargo build --bin sse-subject-navigation
```

### Original nested-mask view

The earlier raw viewer remains available for inspecting the exact saved mask hierarchy:

```sh
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-diffusion-hierarchy.sh
```

It starts at group **1487**, the 19-note coffee group. `j/k` select, `l` or Enter expands, `u` shows the parent, and `f` focuses the selected group. Enter on a mask opens the complete original note with that mask highlighted. `a` shows or hides repeated parent masks; `?` explains the controls; `q` exits.

Pass a group number to start elsewhere: `1671` for kitchen equipment, `1533` for sleep, `1700` for knowledge/writing, or `1753` for the full root. These descriptions are inspection aids, not generated titles. Add `--check` to validate without opening a terminal UI.

The viewer retains all **360 multi-note groups**, their original IDs, child order, and exact memberships. Equal-note levels remain visible. As in the previous viewer, one-note group choices are hidden, with their masks kept at the nearest displayed ancestor. A parent mask starts hidden if its source note already occurs recursively in a child; the `a` toggle reveals it. Children remain nested, and moving upward puts unopened sections above opened sections.

`GDC09/viewer.json` is a checked format export, not a new clustering result. All 916 vectors, 945 original mask IDs, and 100 notes remain. The native tree and prior results are unchanged. The existing viewer calls this an exact-containment hierarchy; the displayed run is **GDC09**, not a HiDeF run. Export source: `../export_diffusion_hierarchy.py`.

## What stayed fixed

All runs use the same 916 distinct saved SSE vectors in their original 768 dimensions, representing 945 masks from 100 real notes. Exact coordinate aliases are preserved in the evidence. The old HDBv3 artifact supplies only that alias mapping—not its graph or source-note edge restrictions. Inputs are verified against their frozen manifest before fitting. No PCA, UMAP, fine-segment preprocessing, or semantic labels enter a fit.

Each result contains full notes, exact mask fragments, alias IDs, and byte ranges in `evidence.json`. Note membership is the union of the source notes of enclosed vectors: a note need appear through only one of its vectors. Counts below are distinct notes, not independent confirmations from overlapping masks.

## Runs and what they taught us

| Run | Method and controlled change | Finding |
| --- | --- | --- |
| GHA01 | HAUS released recursive core, shifted cosine affinity | Some useful coffee, food, and Bitcoin groups; higher branches often combine material without a demonstrated useful common description. |
| GHA02 | GHA01 with local Gaussian affinity, epsilon 0.12762124070971148 | Stops at the root. Local affinities and the released perturbation gate interact badly; this is not evidence of absent local structure. |
| GHA03 | GHA02 with epsilon 0.49514064923464207 | Recursion returns, but higher-level coherence is not reliably restored. Its binary root bypasses the perturbation gate, as in released code. |
| GFM01 | Paper-derived adaptive Fast Multilevel Clustering | Native fuzzy memberships contain useful structure that the separate hard-tree conversion can destroy. Some native groups are mixed too. |
| GFM02 | GFM01 with adaptive aggregation disabled | Preserves one cleaner hard coffee group, but does not repair the native vacuum-sealing/bathroom mixture; other paths deteriorate. |
| GDC01 | Density-normalized diffusion condensation, epsilon 0.12762124070971148 | Useful local groups, but many jump directly into broad collections. |
| GDC01S | Identical GDC01 dynamics, saving iterations 0–16 | Hierarchy and final coordinates match GDC01 bitwise. A 100-fold merge-tolerance range shifts the broad food jump rather than removing it. |
| GDC02 | GDC01 with each coordinate update reduced to one quarter | Adds genuine prepared-meal and sleep intermediates. Long chains still mostly add more examples of the same broad subject. Earlier baseline, superseded as strongest candidate. |
| GDC03 | GDC01 with three applications of each current diffusion operator | Converges faster and provides fewer useful intermediate choices in the inspected paths. No observed rescue from this published mechanism. |
| GDC02S | Unchanged GDC02, sparse coordinate snapshots | Bitwise replay; identifies density reweighting, radial contraction, and late numerical merging. |
| GDC04 | GDC02 with density normalization disabled | Restores one coffee connection but loses other useful distinctions. Not a global improvement. |
| GDC05 | GDC02 with earlier numerical merge recording | Does not generally repair missing intermediate structure. Motion stays identical. |
| GDC06 | GDC02 with unit normalization after each update | Genuine additional intermediate groups; reaches its 2,000-step bound unfinished. |
| GDC07 | GDC06 without density normalization | Useful alternative shrimp, bread, steak groups, with other distinctions lost. Completes at 1,825 steps. |
| GDC08 | GDC06 with initial epsilon multiplied by 1.25 | Several exact diet/sleep/routine groups survive; other subdivisions change. Unfinished at 2,000 steps. |
| GDC09 | GDC06 unchanged, bound extended to 8,000 | Completes at 3,480 steps; first 2,000 steps match exactly. Adds useful knowledge/writing parents; late weak joins persist. Strongest current candidate. |

## Earlier Euclidean diffusion examples

Node IDs identify saved computational groups, not titles. Arrows here move upward, from narrower memberships toward the root.

**Prepared meals, GDC02: `1250 → 1269 → 1284 → 1304 → 1311`.** Node 1250 contains six notes about shrimp-and-mushroom risotto, spaghetti Bolognaise, beef stew, chicken stock, meat dumplings, and a crockpot roast with vegetables. It then enters broader food groups containing 22, 32, 38, and 51 notes. The first broadening has a defensible meaning: prepared meals become a broader range of food interests. Most subsequent additions do not demonstrate a new descriptive level; they add more food examples. GDC01 instead jumped from a four-note cooked-food group to a 50-note food group.

**Sleep, GDC02: `1409 → 1415 → 1418 → 1424 → 1430`.** The first three groups contain two notes, N041 and N069, with masks about good sleep, consistent bedtime, reading before bed, and stopping eating before bed. Node 1424 then adds N018's days off, errands, and morning coffee. This can legitimately broaden to everyday habits—it is not a failure because the parent no longer means only sleep. The following parent includes 92 notes. GDC01 did not retain the narrower two-note sleep group before those additions.

**Coffee coverage remains incomplete.** GDC02/1334 contains 18 notes about coffee and caffeine. N045's cream-in-coffee complaint and N058's hot morning coffee do not join that branch until common parents containing 81 and 89 notes respectively. This is an observed coverage gap for that interest, not a claim that there is one uniquely correct taxonomy.

The original geometry does contain relevant relationships:

> N045: Dear America,
>
> ⟦Half & half⟧ ≠ cream.
>
> Stop ⟦ruining my coffee⟧ with it.

V356 has cosine **0.675218** to V342, whose mask is `⟦Fetching coffee⟧`, inside 1334. It is V356's nearest vector from a different note. V355 is an exact alias, not a second independent vector.

> N058: GM Nostr!
>
> Happy Sunday!
>
> Woke up to 35 degress today---brrr. It'll warm up, but fall is definitely here.
>
> Glad the ⟦coffee⟧ is ⟦hot⟧ ⟦this AM⟧!
>
> #coffeechain

V494 has cosine **0.706267** to V503, whose mask is `⟦Made⟧ ⟦coffee⟧ ⟦today⟧`, also inside 1334. It is V494's nearest vector from a different note. Nearby greeting vectors are almost as close, so the original neighborhood is not exclusively coffee.

These original comparisons rule out the simple explanation that no strong original coffee relationship exists. The continuation then traced the motion and tested the mechanisms rather than attributing the outcome from these two similarities alone. See `original-neighbors.json` for the original evidence and [CONTINUATION.md](./CONTINUATION.md) for the completed investigation.

## What FMC clarified

FMC's native result is a sequence of weighted, overlapping memberships. The hard hierarchy here is an explicitly separate conversion that assigns an entire child to its largest outgoing transition.

In GFM01, native level 6, column 0 gives all 24 coffee/ice-related vectors weight at least **0.4688**, while every other vector has weight at most **0.1859**. The hard projection nevertheless attaches a 22-vector food child on an almost tied transition, **0.07799 versus 0.07724**. This is a conversion problem, not evidence that the native model failed to distinguish those vectors. Those food vectors contribute only about **3.50%** of that native parent's mass.

However, GFM01/1445 combines vacuum sealing, vacuum-sealed beets, bathroom grab bars, and a vague “overrun” mask. The relevant rows also select the same native aggregate; their weights overlap. Disabling adaptive aggregation in GFM02 does not separate the vacuum and bathroom groups. Consequently, inspecting native fuzzy evidence rescues one earlier apparent failure, not the whole hierarchy.

Native matrices are retained in `native-fuzzy.json` and `native-fuzzy-arrays.npz`. Positive but tiny fuzzy membership is not evidence of semantic containment. A hard tree must not be presented as the native FMC result.

## Important limits on interpretation

- A parent may have a broader meaning than its child. “Food” is a valid category; no prescribed cooking subcategories are required.
- Splitting overlapping coffee masks from N086/N094 across branches does not lose either note from coffee browsing: both notes already occur in GDC02/1334.
- The dog emoji in N079 belongs to a real coffee-request note. It is not an unrelated-note inclusion merely because that particular mask is weak.
- Separate greetings already showed an SSE geometry limitation in earlier work. Their distant common parent is not new evidence against these hierarchy methods.
- A broad group containing 50 notes is not inherently bad. Missing useful intermediate distinctions and repeated note sets are separate observations.
- GDC02 has 65 ancestors containing all 100 notes. Collapsing repeated note sets can remove those transitions, but cannot create absent intermediate memberships.
- This is a small, food-heavy corpus and an exploratory semantic audit, not a measured corpus-wide accuracy score. Not every parameter, kernel, source-balancing rule, or possible readout was tested.

## Literature and implementation boundaries

**HAUS:** [NeurIPS 2024 paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/b31c332c4cebcec31b788400b47c94b3-Paper-Conference.pdf), [author code](https://github.com/deepplants/recursive-deep-spectral-clustering), commit `37ee4d32a6698cc9d241ff0d77c97dbd9bdac608`. This adaptation follows the released recursive core, not a silent mixture of code and appendix pseudocode. It omits image preprocessing, overclustering, and CRF; uses dense symmetric eigensolving; and records all stopping reasons. Released code inherits affinities, uses a mean-cut stopping test, and bypasses the perturbation gate for an initially binary split. Those differences from the paper matter on this input. GHA02's median same-note share of affinity is 88.70%; GHA03's is 5.70%. Changing affinity scale therefore changes the experiment substantially, not just a display threshold.

**FMC:** [author-hosted Fast Multilevel Clustering](https://www.wisdom.weizmann.ac.il/~achi/LOP158.pdf). This is an independent dense implementation, not covariance-based FMSC or a sparse linear-time reproduction. Conventions and unspecified parameters are explicit in `geometric_fmc.py`. A source discrepancy remains: the indexed author-hosted section 3.2 gives the implemented unweighted coarse sparsity average; an indexed [CiteSeer copy](https://citeseerx.ist.psu.edu/document?doi=8951aa6713594bee2e0c654e5f62b4b1097931db&repid=rep1&type=pdf) includes accumulated volume. Actual PDF bytes/rendered equations could not be retrieved. This is unresolved source/extraction provenance, not a confirmed transcription defect. No formula was silently changed.

**Diffusion:** [original diffusion condensation](https://arxiv.org/html/1907.04463v3), [later theoretical and experimental treatment](https://arxiv.org/html/2203.14860). Coordinates move by a recomputed, density-normalized Gaussian operator; all original rows remain, and near-coincidence unions accumulate. The original GDC01–03 runs never increased epsilon; GDC07 and GDC09 later did. The tau=3 experiment follows the later paper's mechanism of applying the current operator repeatedly before rebuilding it. The slower update is motivated by [generalised blurring mean shift](https://iacl.ece.jhu.edu/proceedings/cvpr2008/papers/095.pdf); adapting its convex update to this density-normalized process is explicit, not an assertion that its convergence examples prove semantic quality here. Unit-sphere precedent and adaptation limits are documented in the continuation.

## Reproduce and inspect

Run from `oracle-mvp/sse_multivector` with Python 3.13, NumPy 2.4.6, SciPy 1.18.0, and scikit-learn 1.9.0. Set `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, and `MKL_NUM_THREADS=1`. The investigation used `/tmp/crec100-plscan-venv/bin/python` with the Nix library path recorded in the private research log; use an equivalent installed environment when that temporary path is unavailable.

Example read-only inspection, including complete original notes with inline masks:

```sh
python geometric_experiment.py inspect geometric-hierarchy-v1/GDC02 1250 --full-notes
```

Example independent replay (the runner refuses an existing output directory):

```sh
python geometric_experiment.py run \
  --data real-note-fine-segmentation-v1 --method diffusion \
  --config '{"epsilon":0.12762124070971148,"relaxation":0.25}' \
  --run-id GDC02-replay --output /tmp/GDC02-replay
```

Every configuration preserves source hashes, canonical order, actual parameters, original code hashes, runtime, and peak process memory. Every original runner and method-source version has a matching archived copy, indexed by `provenance.json`. The earliest runner was recovered from its original transcript patch and verified against its recorded SHA-256, not reconstructed from memory. A final HAUS audit found and fixed a latent normalized-embedding fallback discrepancy; a new test first reproduced it. Replaying all three HAUS configurations after the fix preserves every saved node's members, children, parent, and note set. Original kernels/results remain archived unchanged.

The 86 MiB `GDC01S/coordinate-snapshots.npz` observation cache remains saved locally but is excluded from Git; its checksum, exact generating configuration, final coordinates, and complete derived tolerance comparison are tracked. It can be regenerated without changing the experiment. No prior experiment artifacts were overwritten or deleted.

## Current handoff

Inspect GDC09 as the strongest complete saved trajectory and GDC07 as the alternative without density correction. No production hierarchy was replaced. Native structure, note-level repetition, source-mask weaknesses, and semantic acceptance remain separate questions. The continuation includes concrete paths and counterexamples so the next decision can concern those actual results, not another unperformed motion diagnostic.
