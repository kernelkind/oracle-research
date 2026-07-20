# CREC-72 complete-build runbook

This runbook documents the one reviewed path for the frozen GTE complete build.
The executable owns the commands, retries, receipts, and recovery logic. Do not
reconstruct the workflow manually.

## Boundary

`prepare` is free. It may inspect local artifacts and read Vast offer and
instance records, but it cannot reserve the budget or create an instance.

`run` crosses the paid boundary only when it receives the SHA-256 of the exact
plan approved by the user. The approval binds the executable, operation
contract, frozen package, offer, projected cost, and canonical ledger.

## Commands

Set the three local paths once:

```sh
ROOT=/home/dev/src/notedeck_worktrees/algos/damus_snapshot/runs/crec-72-gte-full-build
CONTRACT=/home/dev/src/notedeck_worktrees/algos/oracle-mvp/gte/vast-full-build-operation.json
OPERATOR="$ROOT/transport/control/vast_full_build.py"
```

Prepare and print the exact plan requiring approval:

```sh
python3 "$OPERATOR" --root "$ROOT" --config "$CONTRACT" prepare
```

After the user approves the printed plan SHA-256, advance the build through
one verified worker start:

```sh
python3 "$OPERATOR" --root "$ROOT" --config "$CONTRACT" \
  run --approve PLAN_SHA256
```

The first paid invocation prompts on the terminal for the private image's
read-only Docker PAT. The PAT is passed only to Vast's create request and is
not written to a receipt, environment file, or command argument.

`run` is resumable. If it is interrupted, invoke the same command again. Once
the approval receipt exists, omit `--approve`. It verifies existing receipts
and continues the first unfinished transition. It never duplicates a
reservation or instance. After a worker execution is durably committed, it
never starts a second one.

If `run` returns `preparing` or `remote_access_pending`, rerun it until it
returns `running` or a terminal cleanup state.

Observe the running job without changing local or provider state:

```sh
python3 "$OPERATOR" --root "$ROOT" --config "$CONTRACT" \
  status --watch
```

While it runs, watch:

- `remote.progress.completed_new_shards` for durable progress;
- `remote.progress.newest_new_shard_age_seconds`; about 30 minutes without a
  new shard means investigate, not restart;
- `cost.conservative_observed_total_micro_usd` and
  `manual_stop_recommended`; stop at the reviewed $42 boundary.

`status --watch` exits when the worker becomes terminal. Promptly invoke `run`
again to seal, retrieve, verify, destroy, obtain the finalized invoice, and
settle. If it returns `invoice_pending`, rerun it after
`next_eligible_observation_utc`.

To stop a running worker explicitly and enter the same verified cleanup path:

```sh
python3 "$OPERATOR" --root "$ROOT" --config "$CONTRACT" stop
```

`stop` requests a terminal worker record, then uses the same retrieval,
verification, destruction, invoice, and settlement path. If verified result
retrieval is impossible, it destroys the instance but returns
`ledger_reconciliation_required` and deliberately leaves settlement for
review.

## Recovery rule

Never delete or edit a receipt to make the operation continue. Rerun the
appropriate command. A mismatch between receipts, the provider, the remote
machine, or the canonical ledger is a hard stop requiring review.

There is no automatic relaunch, provider failover, watchdog, or cost-triggered
termination. `status` warns at the reviewed cost boundary; only `stop` ends a
running worker.
