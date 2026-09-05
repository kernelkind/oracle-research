# Astra low: blocked before mask generation

The first request was rejected because the frozen Codex CLI is too old for Astra:

> The 'gpt-6-astra' model requires a newer version of Codex. Please upgrade to the latest app or CLI and try again.

This is **not a mask-quality result**. There are no generated masks to compare.

## What ran

- Requested: the same 12 fixed subjects and notes, three trials, unchanged prompt.
- Attempted: M01 in trial 1, using Astra low and the baseline CLI, version 0.150.1.
- Result: HTTP 400 before any mask was generated. The batch stopped immediately.
- Completed masks: 0. The other 35 calls were not attempted.
- No retries, prompt edits, new examples, account changes, or alternative model calls.

The service returned no token usage; that is unknown, not a measured zero. The batch lasted 4.151 seconds, peaked at 16.8 MiB of memory, and used zero swap. Existing subscription only; no paid API or rented compute.

## What would need to change

Codex CLI **0.153.0 is already installed**. Its Astra access has not been tested.

Using it only for Astra would change both the model and the CLI relative to the frozen Sol runs. To keep the model as the only changed configuration variable, the proposed adjustment is to run **both Sol low and Astra low through the newer CLI**: 36 calls per model, 72 total.

That exceeds the approved 36-call plan and changes the frozen runtime, so execution is paused for the user's decision. Nothing has been upgraded or switched.

## Preserved evidence

- `plan.json`: the original approved plan, unchanged.
- `selection.json`: the unchanged fixed subjects and complete original notes.
- `trial-1/config.json` and `trial-1/run/`: the exact request configuration, manifest, minimal instructions, and failed raw record.
- `trial-2/config.json` and `trial-3/config.json`: prepared but never run.
- `execution-status.json`: the service error, actual counts, installed CLI versions, and pending choice.
- `verification.json`: unchanged-input checks, isolation, file hashes, and resource limits.

The original Sol and medium-effort data, frozen prompts, user reviews, registries, production code, and user notes documents are unchanged.
