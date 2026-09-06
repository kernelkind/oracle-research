# ASv6.8 vs ASv6.9

All 36 comparison calls completed. ASv6.9 helped on the sports example, but it did not eliminate the problem: one Katie output still adds an ambiguity comment. One Iran output also calculates a new time interval. ASv6.8 remains frozen; ASv6.9 has not been accepted as its replacement.

[Complete original notes and every generated subject](./main/results.md)

## Comparison

Six fixed notes, three fresh calls per note with each prompt, all Sol low. These are selected development examples, not a corpus-wide accuracy test. Broad, nested and duplicate subjects remain allowed.

| Observation | ASv6.8 | ASv6.9 |
| --- | --- | --- |
| Sports: adds that a connection is unclear | 1/3 | 0/3 |
| Katie: adds commentary about unclear or incomplete meaning | 1/3 | 1/3 |
| AI: repeats the exact prior “the post does not state” causation remark | 0/3 | 0/3 |
| Iran: calculates a two-week gap | 0/3 | 1/3 |
| Kremlin: retains the source's “nothing to add” statement | 3/3 | 3/3 |
| Iran: retains the argument, normal-conditions contrast and future-adoption question | 3/3 | 3/3 |

The exact old AI remark did not recur with ASv6.8, so this comparison cannot establish that ASv6.9 fixed it. Qualifying a supported interpretation as uncertain is allowed; uncertainty words alone are not failures. The LLC and smile/teeth readings remain interpretation questions, not established errors.

The two remaining ASv6.9 problems are concrete:

- **Katie, trial 3, subject 6:** “Direct contact with the unspecified group is conditionally connected to not wanting a ticket to be used, though the precise relationship is ambiguous”. The ending adds the model's commentary instead of qualifying the proposed interpretation itself.
- **Iran, trial 2, subject 8:** “Iran launched Hormuz Safe two weeks after Tether froze $344 million in USDT linked to the Central Bank of Iran.” The source says “Three weeks ago” and “Last week”; the generated subject subtracts them, contrary to the unchanged restriction on new calculations.

The source statements and complete outputs are together in [results.md](./main/results.md); the separate judgments are in [assistant-analysis.json](./main/assistant-analysis.json). Neither compared prompt changed during that run. The subsequent [ASv6.10 test](../atomic-subject-asv6.10-test-v1/README.md) reuses the saved ASv6.9 outputs; it does not alter this comparison's inputs or results.

## Inputs and execution

Full notes and selection reasons are in [selection.json](./selection.json). The [original plan](./plan.json), [ASv6.8](./ASv6.8.md) and [ASv6.9](./ASv6.9.md) remain unchanged. The [completed-run plan](./main/plan.json) preserves the experiment settings in separate output locations.

The earlier attempt failed during authentication and produced no subject output. Its [complete error record](./asv6.8-trial-1/run/results.jsonl) is preserved. It is not a semantic failure or one of the 36 completed calls. An earlier launcher-path error occurred before Codex ran.

Main uses the existing dedicated home at `/home/dev/.local/state/oracle-mvp/codex-home`. No credentials were copied or printed. Both prompts ran on that account, with the same pinned CLI 0.153.0, Sol-low settings, input normalization, JSON schema and isolated runner.

All 36 main calls succeeded on their first attempt. Verification found 36 distinct threads and working directories, one turn per call, no tools, exact rendered-prompt and output hashes, unchanged subject exports, and all 59 protected files unchanged. See [verification.json](./main/verification.json). No masks, SSE vectors, production code changes or user approvals were generated.

Reported usage:

- ASv6.8: 39,105 input tokens, 8,199 output tokens.
- ASv6.9: 39,573 input tokens, 8,509 output tokens.

Output totals include reported reasoning tokens. The failed attempt reported no usage. Runs were sequential through the existing subscription; no paid API or rental was used. [runtime.json](./main/runtime.json) records the local launcher services' measurements, not whole-host memory use.

Current execution status: [status.json](./status.json).
