# Hierarchy versions and experimental parameters

Open the [hierarchy catalogue](../../target/hierarchy-catalogue/index.html) for
all saved versions and their recorded experimental parameters. Search by version
ID, original experiment name, prompt, model, seed or other saved setting. Select
two versions to inspect their parameters side by side.

The catalogue collects saved canonical trials, clustering hierarchies, graph
exports and browsing outputs from the repository's retained Git worktrees.
Each entry includes an immutable output copy, its SHA-256, original locations,
recorded configuration, source bindings and parameter evidence. Missing or
changed frozen sources are displayed. Unrecorded historical defaults stay
unknown; current defaults are never substituted. Archived geometric signature
defaults are included only when the source matches its recorded hash.

Each entry also has a **Generator code** section. Code and prompt files identified by
saved hashes are preserved under the catalogue's `code/` directory. The command
checks live and retained worktree files, then local Git history, accepting only
bytes matching the recorded SHA-256. A recovered Git blob establishes the exact
file contents; it does not establish the run's overall commit. Saved commit
identifiers are shown when recorded. Missing source files and unrecorded commits
remain unknown. This inventory cannot recover code that a run never identified.

Before a new run, record its source commit and any uncommitted source changes
alongside the runner's frozen code hashes. Preserve that source before executing
the experiment; the checkout's later HEAD is not evidence of the run's code.

IDs use `H0001`, `H0002`, and so on. The maintained
[version registry](../../sse_multivector/hierarchy-versions.json) permanently
associates each ID with a saved output and its adjacent parameter evidence.
Copies at the same relative path share an ID when output and evidence match.
Independent saved paths remain separate, even if their output bytes match.
Changed output or adjacent evidence gets a new ID. Existing versions and their
snapshots are retained. Recorded source hashes link related versions; browsing
exports and checkpoints can therefore be referred to individually.

The catalogue includes historical/deprecated subject-derived experiments. A
recorded ASv6.100 source does not establish that a hierarchy is approved or
semantically correct. Unknown subject versions are labelled explicitly. Empty
preparations, pair-only diagnostics, smoke fixtures and synthetic storage
benchmarks are excluded.

Refresh after saving a hierarchy, from its task worktree:

```bash
/home/dev/src/notedeck_worktrees/algos/experiment-runner/bin/experiment-runner \
  --project-root "$PWD" catalogue-hierarchies \
  --source sse_multivector/hierarchy-catalogue-source-v1.json \
  --registry sse_multivector/hierarchy-versions.json \
  --output /home/dev/src/notedeck_worktrees/algos/oracle-mvp/target/hierarchy-catalogue
```

This command makes no model calls and never changes original experiments.
Use that shared output directory across tasks so earlier versions remain
available. Refresh sequentially and merge local `main` before assigning IDs.
Commit and land registry changes with the task. The generated catalogue,
parameter projections and output snapshots stay ignored under `target/`;
preserve that directory together with the original retained experiments.
The registry alone is not a backup of experiment data. A missing retained
record stops regeneration instead of silently losing a version's evidence.
Use `--saved-only` to rebuild the page and source archives from the retained
inventory without discovering new hierarchy outputs.

The workspace copy linked above lives under the canonical repository's
`target/hierarchy-catalogue/`. Refreshing the catalogue is an offline inventory
operation; preparing, running and resuming experiments still happens only in
task worktrees through the shared launcher.
