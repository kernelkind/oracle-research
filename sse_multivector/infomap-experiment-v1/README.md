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

The [plan](PLAN.md) records settings fixed before inspection. I01 changes only the hierarchy algorithm from M07. I02–I04 then change only which graph connections remain. No prompts, masks, embeddings, or edge weights were revised. Neighbors are vectors, not distinct notes; several vectors from another note can occupy the list.

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
