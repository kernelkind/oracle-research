# Autonomous SP iteration

The user authorized autonomous SP iteration on 2026-10-02, with at most
1,000 attempts on `gpt-6.1-sol` at `low` or `medium` reasoning. This is an upper
bound, not a target. Use the subscription `openai-codex` route, without paid
fallback. MP and production adoption remain outside this campaign.

Start from ASv6.58 (candidate, tested with failures). Frozen SP ASv6.48 remains
unchanged. Preserve the existing SP output schema and all instruction/example
coverage. Each candidate needs a version ID and native revision receipt.

## Evidence and evaluation

The six reusable diagnostic cases form three positive/control pairs: purpose
from a list heading versus unrelated co-mention, first use versus newness, and
repair/colour relationships versus distinct objects. Their rubrics are agent
judgments, not user labels. Original regression cases N063, N074, N096 and N100
use native preparation from the saved complete source posts. Both sets are
development evidence, not untouched generalization evidence.

Grade each returned hierarchy for supported meanings, heading-alone parent
relationships, specific source-subject retention and valid placement beneath
every applicable returned parent. Include all occurrences of repeated parents.
Do not infer semantic correctness from output size or text difference. Keep
agent reviews separate from actual user decisions. A rejected answer needs a
concrete source omission or child/parent counterexample.

Whether *derived general headings* also require every valid placement remains
unresolved; track that separately. Do not force controversial memberships
such as vegetable broth under vegetables.

## Execution

All preparation, inference and review use `sse_multivector/experiment.py`.
Saved experiments and receipts live under the ignored
`sse_multivector/experiments/sp-autonomous-v1/`; request history and the native
persistent attempt budget live under ignored `target/sp-autonomous-v1/`.
The attempt budget is never reset or refunded. Only native `run` launches
calls, and each run must name this same budget. Failed/interrupted calls count.
Subscription incremental cash cost is zero; quota consumption is unmeasured.
The monetary ledger was read before launch; no paid commitment is introduced.

Screen revisions on small cases before repeating long outputs. SP remains one
model call per post: no production grading stage or repeated corpus-wide pass
is added. Input work scales with the post and fixed prompt; output work also
includes the existing repeated-branch requirement.

## Results

Baseline preparation and evaluation in progress. No candidate is adopted.
