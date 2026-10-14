# S05 synthetic root trial

Status: authorized experimental naming of one section, not a hierarchy-policy
activation or a replacement of HR22. The user chose the largest-membership
section as the first root and authorized this concrete S05 trial. Here S05
has both the most groups and the most distinct notes.

The [100-note numerical review](food-drink-hundred-epsilon-v1.md) fixes S05's
15 groups and 58 distinct notes. This trial uses those original groups' existing
HR22 synthetic titles and explicit meanings, unchanged. It does not use every
Bootstrap entry or existing wider section definitions. G22 includes domestic
dogs, including feral dogs; that fixed scope must also be covered.

## Native preparation

The `hierarchy_group_consolidation` adapter accepts a source reference:

```json
{"schema_version":1,"epsilon_review":"PATH/analysis.json","section":"S05"}
```

Preparation reconstructs the saved numerical review from native HDBSCAN
evidence and requires an exact match. It selects the original named group
nodes, validates their producer receipts, and protects the review, state,
native controls and selected producers with source hashes. It creates one case
with `nodes` containing only `{title, meaning}`. No `parent` is supplied.
Group IDs, note IDs and receipts remain review evidence outside model input.
Tampered membership or incomplete native group definitions prevent preparation.

The [spec](../../../sse_multivector/experiment_specs/food-drink-s05-root-v1.json)
uses unchanged Hierarchy-consolidated-grouped-v1 and GPT-6.1 Sol medium over
subscription SSE. This one-case trial omits automatic prefix warming to avoid
an extra inference request. Exact request reuse remains enabled. Saved HR22,
other sections and the hierarchy UI are unchanged.

Prepare and run from the retained task worktree:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp-food-drink-s05-root-v1
../experiment-runner/bin/experiment-runner prepare \
  target/food-drink-s05-root-v1/experiment \
  --spec sse_multivector/experiment_specs/food-drink-s05-root-v1.json \
  --history-root target
../experiment-runner/bin/experiment-runner run \
  target/food-drink-s05-root-v1/experiment
```

The result proposes a synthetic root whose supporting notes are the existing
58-note union; it does not apply a graph change. Mechanical output validity
does not certify semantic coverage or browsing usefulness.

## Completed result

The native S05 case completed with one fresh attempt, no reuse, no retry and
no prefix warmup. The proposed title is **Food and domestic animals**. Its
definition covers the food activities, social systems and resources along
with animals of domesticated kinds, including feral dogs. This preserves the
Dogs group's independent scope instead of giving it a food restriction.
The combined title's usefulness and the proposal's semantic specificity still
require review; this result is not human approval.

The receipt is in the retained task worktree at
`target/food-drink-s05-root-v1/experiment/run/results.jsonl`, with record SHA256
`fae843bfad016379bf9ed2d7be015cf47e3c14eec9a800d66d33652fa0a2f45b`.
Use native `show ... --case S05` for the complete unchanged title and meaning.
The ignored native plan retains all 15 original group producers and 58 note
IDs outside the model's input.

| Native usage | Tokens |
|---|---:|
| Input | 2,895 |
| Cached input | 0 |
| Cache writes | 0 |
| Output, including reasoning | 732 |
| Reasoning, included above | 516 |

Known API-equivalent total is **$0.01311**, with complete usage. This was
subscription inference, not a paid API charge. No saved hierarchy or UI was
changed, and this diagnostic is not a new official HR run.

The production-path test first failed because the adapter required copied
case inputs. It now selects exact native group definitions, freezes producer
receipts, completes ordinary runner execution and rejects altered section
membership. Review, HDBSCAN and prompt-assembly regressions also pass.

Verification: 41 focused checks passed. The broader 73-check constructor and
selection suite passed 72 checks, including all 62 constructor checks. Its
existing `test_generation_costs_keep_zero_normalized_failure_usage_unknown`
check failed. Repeating that check in the unchanged retained numerical-review
worktree also failed: the shared runner reported an unknown catalog total
where the old test expected a numeric subtotal. No runner/cost change was made
in this task; this unrelated regression remains unresolved.

The task worktree is retained for the native receipt, frozen source identity
and absolute review/producer references. Generated data remains ignored.
