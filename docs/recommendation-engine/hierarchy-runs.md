# Official hierarchy runs and experimental parameters

Open the [hierarchy catalogue](../../target/hierarchy-catalogue/index.html) for
official hierarchy runs and their recorded experimental parameters. **HR03** is
the human-designated ASv6.100 50-note Bootstrap-v96 / Compare-v48 build. Its raw
build and derived menu/export belong to this one run ID.

Register a run only when the human explicitly designates it as official.
Completing a diagnostic, approving its execution or generating a browsing output
does not make it official. Checkpoints and derived outputs remain attached to
their run; they do not receive separate run IDs. The previous `H0001`–`H0701`
diagnostic inventory is withdrawn, and those IDs must not be reused.

The [catalogue source](../../sse_multivector/hierarchy-catalogue-source-v1.json)
contains the explicit `official_runs` list. Each entry records `version_id`,
`name`, `root`, `artifact_path` and `sha256`, with optional `related_outputs` for
the run's other saved outputs. The
[version registry](../../sse_multivector/hierarchy-versions.json) binds the ID to
its preserved output and parameter evidence. The existing-run cutoff remains
October 8, 2026 at midnight America/New_York (`2026-10-08T04:00:00Z`). Older bound
inputs remain provenance.

The catalogue shows frozen input, prompt, model, construction and execution
settings, source hashes and native receipts together. Compare runs there;
missing settings and historical Git commits stay explicitly unknown. Generator
source is accepted only when its bytes match a saved hash. An exact Git blob
identifies file contents, not the run's overall commit. Before a new run, record
the full commits of Oracle and the shared runner, plus any uncommitted source
changes, alongside their frozen code hashes.

Regenerate the catalogue after updating the explicit official-run list, from a
task worktree:

```bash
/home/dev/src/notedeck_worktrees/algos/experiment-runner/bin/experiment-runner \
  --project-root "$PWD" catalogue-hierarchies \
  --source sse_multivector/hierarchy-catalogue-source-v1.json \
  --registry sse_multivector/hierarchy-versions.json \
  --output /home/dev/src/notedeck_worktrees/algos/oracle-mvp/target/hierarchy-catalogue
```

This offline command makes no model calls and preserves original experiments.
Use `--saved-only` to regenerate from retained records. Generated pages, parameter
evidence and output snapshots stay ignored under `target/`; preserve them with
the original runs. The registry alone is not a backup. Experiment preparation,
execution and resumption still use task worktrees and the shared launcher.
