# PPv10 coffee-node study

Approved node-note order evidence for hierarchy node **Coffee (S9c440e7f47)** of
the generated 100-note hierarchy: all of the node's own direct masks in the
current hierarchy (TRUE14 `mask_instances` minus child-inherited masks) — 36
masks across 13 notes. 32 are new calls here; 4 byte-identical masks already
scored in `../ppv10-ranking-v1/` (V276=95, V280=95, V244=88, V381=2) are reused
as saved scores and are not re-called.

Prompt: **PPv10** (`../ppv10-draft-v1/PPv10.md`, SHA-256
`d40835fb0b104865727c0b0a2bde4074afb642991d9bddc424d5379ef4b038ea`) — unchanged,
user-approved, tested experimentally, not production-frozen. Model `gpt-6-astra`,
reasoning `low`, provider `openai-codex`, one call per case. `plan.json` records
selection, per-case expectations and five predeclared order checks (3 clear,
2 tentative) before inference. No subject descriptions or labels enter the
model input. Child nodes and their inherited masks are out of scope; how one
note's several masks combine into one node-note position stays undecided
(task 27).

## Status: prepared, inference blocked by the credential sandbox

Preparation succeeded offline (`{"prepared": 32, "model_calls": 0,
"all_saved_fragments_and_occurrences_verified": true}`). Every execution attempt
fails before any HTTP request, with no usage and no charge: the selected-account
credential sandbox cannot bind `models.json` into its new root —

```
bwrap: Can't bind mount /bindfile… on /newroot/home/dev/.pi/agent/models.json:
Unable to mount source on destination: No such file or directory
```

This is environmental, not input- or config-related: the same error occurs for
the no-op smoke `agent-account exec pi -- pi --version`. It matches the
"nested credential-sandbox mount failure" recorded in `budget-ledger.json` for
the 2026-09-22 title-probe attempts, which later completed through the
OpenRouter route instead.
Failed-attempt receipts are preserved in
`run/results.jsonl`; the credential service is not modified here.

## Commands

Prepare once (done; refuses to overwrite evidence):

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
PYTHONPATH=sse_multivector/prominence-prompt-goal-v1/ppv10-ranking-v1 \
python3 -c 'import study; study.ROOT = study.ROOT.parent / "ppv10-coffee-node-v1"; study.prepare()'
```

The old saved-batch CLI is retired. Preserve these inputs and receipts as evidence;
import them with an explicit template/input mapping rather than rerunning the baseline.
The preparation/collection scripts below describe this saved study, not a second
supported workflow for new prompt experiments.

Collect once (validates pinned inputs and actual receipts):

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
PYTHONPATH=sse_multivector/prominence-prompt-goal-v1/ppv10-ranking-v1 \
python3 -c 'import study; study.ROOT = study.ROOT.parent / "ppv10-coffee-node-v1"; study.collect()'
```
