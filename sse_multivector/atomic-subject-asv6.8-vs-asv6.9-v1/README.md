# ASv6.8 vs ASv6.9: test paused before any output

The first ASv6.8 call failed during authentication. No subject output was generated, and ASv6.9 has not run. There is no comparison result yet.

The earlier attempt failed during authentication. All later batches were stopped. No account/model switch or retry was made.

## Planned comparison

Six original notes, three fresh calls per note with each prompt: 36 planned calls, all Sol low. ASv6.8 stays frozen; ASv6.9 is the exact user-approved draft.

- Sports and AI headlines test whether ASv6.9 removes the model's added commentary about unclear or unstated information.
- Cloud certification and Katie test interpretation wording. Their LLC and teeth readings are unresolved judgments, not established errors.
- Kremlin and Iran/Bitcoin check that source-expressed negative statements and reasonable implications remain represented.

Full notes and their selection reasons are in [selection.json](./selection.json). Exact prompts, settings and pre-run criteria are in [plan.json](./plan.json), [ASv6.8.md](./ASv6.8.md), [ASv6.9.md](./ASv6.9.md) and the six run configurations. No masks, SSE, prompt edits or user approvals are part of this comparison.

## What ran

A launcher error first prevented Python from starting; no Codex call occurred. Using Python's absolute path fixed that setup issue.

The first actual attempt was ASv6.8, trial 1, cloud-certification note. Codex exited with status 1 before producing a response. Token usage was not reported. The local service ran for 5.828 seconds, peaked at 16.6 MiB memory and used no swap; it was capped at 2 GiB with a 900-second limit.

The complete failed record remains in [results.jsonl](./asv6.8-trial-1/run/results.jsonl). [status.json](./status.json) records the pause. Original prompts, notes, review decisions and frozen artifacts remain unchanged.

## To resume

