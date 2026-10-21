# Infomap results

**The sparse graphs produced some useful groups, but none of the four runs produced nested subject levels.** This comparison is complete and ready for inspection; Infomap is not selected as the hierarchy algorithm.

| Run | Graph connections | Groups below the root | Further levels |
| --- | --- | ---: | ---: |
| I01 | Existing M07 graph: 412,379 connections | 1, containing everything | 0 |
| I02 | 5 nearest eligible vectors; 3,675 connections | 43 | 0 |
| I03 | 10 nearest eligible vectors; 7,175 connections | 28 | 0 |
| I04 | 20 nearest eligible vectors; 13,988 connections | 16 | 0 |

All four retain the same 100 notes, 916 canonical vectors, and 945 original mask records. Every displayed group contains at least two distinct notes in these actual results. The loader does not impose that filter or hide native levels. All four graphs are connected; no vector is isolated.

## Open the results

From any directory:

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-infomap-hierarchy.sh I02
```

Replace `I02` with `I01`, `I03`, or `I04`. This launches the saved result, not inference. The Infomap code and saved results are now on `main` alongside the existing HDBSCAN, merge-rule, and M06 viewers. Their launchers remain unchanged. The separate Infomap worktree is retained; absolute paths inside the frozen JSON files record where the experiment originally ran and are not runtime dependencies.

`j/k` selects; `h/l` collapses/expands; `Enter` opens the complete original note with its mask inline. `U` shows the parent; unopened siblings appear above the expanded group. `F` focuses a group. `gg/G` goes to the beginning/end; `?` opens help; `q` exits. Parent masks whose source note appears recursively below start hidden; `a` reveals them. No review decisions or source edits are made.

Some useful starting points, with interpretation in [the analysis](analysis.md):

```bash
# Many coffee masks together; a useful relationship, not a generated title.
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-infomap-hierarchy.sh I02 --start-at 925

# Three tour stops, three chickens, three awakenings, and other material.
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-infomap-hierarchy.sh I03 --start-at 931

# Greetings together with gianguja, Gentoo, a gin gift, and a 'goblin'.
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-infomap-hierarchy.sh I04 --start-at 929

# Bitcoin-heavy material with an unexplained storm mask.
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-infomap-hierarchy.sh I04 --start-at 931
```

Group IDs apply only within their run. `I03/931` and `I04/931` contain different vectors. N and V IDs retain their original corpus meanings across all runs. The UI shows exact fragments separated by spaces, and combines display-identical aliases while retaining every original ID.

## What was tested

The [plan](README.md#infomap-study-design) records settings fixed before inspection. I01 changes only the hierarchy algorithm from M07. I02–I04 then change only which graph connections remain. No prompts, masks, embeddings, or edge weights were revised. Neighbors are vectors, not distinct notes; several vectors from another note can occupy the list.

Native hierarchical Infomap was enabled. Independent verification checked the actual C++ settings and all native paths: this is not a two-level-only flag, a truncated export, or a viewer flattening. The method is heuristic. A flat result does not prove that no deeper partition exists; a one-group initial partition can also end the library's hierarchy search early. See [the pinned implementation](https://github.com/mapequation/infomap/blob/v2.15.1/src/core/InfomapBase.cpp#L2026-L2051).

These four outputs are separate partitions, **not successive hierarchy levels**. Increasing the neighbor count reassigns vectors; it does not necessarily combine whole groups from the previous run.

## Reproduce and verify

The lightweight experiment command uses the pinned Nix development shell, NumPy 2.3.4 and Infomap 2.15.1. It fixes seed 123 and ten internal trials and refuses an existing output directory. It requires `nix` and `uv`. No model calls or paid resources are needed.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
sse_multivector/run-infomap-experiment.sh I02 /tmp/infomap-I02-replay
```

Each run directory contains:

- `configuration.json`: input/code hashes, graph definition, package versions, and algorithm settings.
- `graph.net`: exact weighted graph given to Infomap, including all vector IDs.
- `native.tree` and `native.json`: unmodified Infomap exports.
- `hierarchy.json`: original aliases, native paths, complete module memberships, and measurements consumed by the viewer.

The root ID is 916. Other group IDs are assigned to all distinct native module-path prefixes in numeric lexicographic order, starting at 917. The `modules` array records the mapping; no merge scores or binary joins are invented. Native paths include a final vector position; `module_path` excludes only that position.

All four saved graphs were replayed through Infomap's file-input path with the same settings. Native memberships and paths reproduced exactly, and codelengths matched to ten decimal places. The replay did not modify saved outputs. All source hashes still match M07. The dense run took about 1.6 seconds end to end; sparse runs each took about 0.6 seconds. Each process peaked below 160 MiB RSS. These figures exclude dependency setup, compilation, and semantic inspection.

To rebuild the isolated viewer:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
CARGO_TARGET_DIR=target/infomap-review-build CARGO_BUILD_JOBS=2 CARGO_PROFILE_DEV_DEBUG=0 \
  nix develop --command cargo build --bin hdbscan-hierarchy
```

Verification commands:

```bash
nix develop --command env INFOMAP_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  uv run --no-project --with numpy==2.3.4 --with infomap==2.15.1 \
  python -m unittest discover -s sse_multivector -p 'test_infomap*.py'
python3 -m unittest discover -s tests -p test_infomap_launcher.py
sse_multivector/run-infomap-hierarchy.sh I02 --check
```

The relevant Rust tests cover native multiway/nested groups, direct vectors, aliases, exact mask spans, source checksums, N/V IDs, CLI option conflicts, and real saved artifacts. Existing HDBSCAN and comparison-view regressions also pass. Test fixtures with genuinely nested modules verify nesting even though this experiment's outputs are flat. The terminal inspection covers originals, scrolling, help, aliases, parent navigation, and clean exit.

## Infomap study design

Approved 2026-09-10. Stop after the four saved configurations, nested TUI inspection, and evidence-backed analysis. A poor result is a valid stopping outcome. No new prompts, masks, vectors, generated titles, manual group repairs, or final algorithm selection.

### Fixed inputs

100 real notes, 916 canonical SSE vectors, 945 original mask records. Reuse the four source files recorded by M07, checking their SHA-256 hashes before every run. Preserve their ordered canonical IDs and every alias.

M07's graph connects all eligible cross-note pairs with weight `1 - angle / pi`. The saved HDBv3 distances equal original angular distances on those eligible pairs. Same-note pairs remain absent. Do not use M07's merge scores as graph edges.

### Runs fixed before inspecting output

| Run | Connections |
| --- | --- |
| I01 | Exact dense M07 graph |
| I02 | Each vector chooses its 5 nearest eligible vectors |
| I03 | Each vector chooses its 10 nearest eligible vectors |
| I04 | Each vector chooses its 20 nearest eligible vectors |

For I02–I04, keep an undirected connection if either endpoint chooses it. Break exact distance ties by canonical node ID. Retain the exact M07 weight on every retained edge. These are nearest vectors, not nearest distinct notes; multiple vectors from another note can occupy the list. No new edge or connection between disconnected components is introduced.

Infomap 2.15.1; undirected flow; native hierarchical mode; seed 123; ten internal trials, keeping Infomap's shortest-description result. Other algorithm settings stay at that release's defaults. NumPy 2.3.4; one OpenMP/BLAS thread; run configurations sequentially. No paid compute or model inference. Save the input graph, configuration, source/code checksums, native tree/JSON, complete memberships, trial scores, elapsed time, and peak memory. Refuse to overwrite an output directory.

Five, ten, and twenty are exploratory neighborhood settings, not established semantic thresholds. Compare all three without choosing a favorable setting after seeing one example. Internal trials reduce search randomness but do not constitute a semantic reliability estimate. Codelengths from different graphs are not directly comparable quality scores.

### Inspection

Preserve the native module nesting, including one-note modules and equal-note parent/child transitions, so the experiment does not hide what Infomap produced. Do not fabricate binary merges or distances to fit the viewer. Show exact masks, N/V IDs, full original notes, and an option to reveal parent masks normally hidden because their note already appears recursively below.

Read the complete module memberships and inspect originals for questionable cases. Record supported broad-to-narrow organization, questionable placements, useful groups lost or mixed, and uneven coverage. Treat labels as interpretations, never evidence. The accepted manual coffee example is one valid arrangement, not a uniquely correct target. Distinguish problems in masks/vectors from grouping errors when the evidence allows; otherwise leave the cause unresolved.

Compare I01 with existing M07 to change only the hierarchy algorithm. Compare I02–I04 with I01 to change only the retained connections. Keeping SSE frozen does not establish that every vector is correct. A negative dense-graph result alone does not invalidate Infomap with other graphs.
