# Original-coordinate hierarchy experiments

The strongest result is **partial improvement from slower diffusion**, not a working complete hierarchy. All three methods produce some coherent groups. None of the inspected outputs consistently turns their nested memberships into increasingly specific, accurate categories of notes.

These are exploratory adaptations, not a benchmark ranking or a finding that the underlying papers are wrong. No generated category labels, new TUI, subject edits, mask edits, or new model calls were used.

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
| GDC02 | GDC01 with each coordinate update reduced to one quarter | Adds genuine prepared-meal and sleep intermediates. Long chains still mostly add more examples of the same broad subject. Strongest partial candidate. |
| GDC03 | GDC01 with three applications of each current diffusion operator | Converges faster and provides fewer useful intermediate choices in the inspected paths. No observed rescue from this published mechanism. |

## Strongest diffusion examples

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

These comparisons rule out the simple explanation that no strong original coffee relationship exists. They do **not** establish why the final memberships separate: the complete neighborhoods, coordinate motion, and cumulative merging remain possible contributors. See `original-neighbors.json` for the exact inputs and six nearest distinct-note neighbors per target.

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

**Diffusion:** [original diffusion condensation](https://arxiv.org/html/1907.04463v3), [later theoretical and experimental treatment](https://arxiv.org/html/2203.14860). Coordinates move by a recomputed, density-normalized Gaussian operator; all original rows remain, and near-coincidence unions accumulate. The algorithm never increased epsilon in these saved runs. The tau=3 experiment follows the later paper's mechanism of applying the current operator repeatedly before rebuilding it. The slower update is motivated by [generalised blurring mean shift](https://iacl.ece.jhu.edu/proceedings/cvpr2008/papers/095.pdf); adapting its convex update to this density-normalized process is explicit, not an assertion that its convergence examples prove semantic quality here.

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

## Next informative step

The strongest follow-up is a bounded **diffusion-motion diagnostic**, not another blind parameter sweep: follow N045/N058 and their already-related original neighbors through saved coordinate updates, separating which neighbors pull them, when those relationships change, and when cumulative merging commits their placement. Compare this with a successful path. That can distinguish lost geometry during motion from a problematic conversion of an otherwise useful geometric state. The current results justify that investigation; they do not yet justify replacing the production hierarchy or blaming SSE alone.
