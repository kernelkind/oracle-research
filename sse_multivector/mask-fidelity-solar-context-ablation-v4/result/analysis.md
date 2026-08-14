# Solar-mining context ablation

## Question

What happens to the solar-mining comparison when all unselected source
context is removed from R10 and R11?

## Controlled change

The frozen v5 nine-note batch was rerun with the same encoder, checkpoint,
container, and row order. Only the encoder inputs for R10 and R11 changed.

R10 became its source-exact selected fragment:

```text
start up the miner when I have #solar #energy  left
```

The two spaces before `left` are present in the source.

R11 became its two source-exact selected fragments in source order:

```text
solar panels
run a Bitcoin miner off this successfully
```

The inserted newline is an unselected separator. All original unselected
source text was removed.

R12 was already entirely selected and remained unchanged:

> ⟦Solar power will be the vast majority of power generation in the future⟧

## Measurements

| Edge | Complete-note context | Mask-only input | Change |
|---|---:|---:|---:|
| R10 solar mining ↔ R11 solar mining | `0.655805` | `0.698130` | `+0.042324` |
| R10 solar mining ↔ R12 solar only | `0.777669` | `0.697712` | `-0.079957` |
| R11 solar mining ↔ R12 solar only | `0.465934` | `0.596508` | `+0.130573` |

Under mask-only input, R10↔R11 was greater than:

- R10↔R12 by `+0.000418`;
- R11↔R12 by `+0.101622`.

The frozen strict-greater-than rule therefore records a pass. The first margin
is so small that this should be understood as an effective tie, not a robust
separation.

## Isolation check

The seven unchanged output-vector rows are byte-for-byte identical to the v5
baseline. Only R10 and R11 differ.

- Complete-context R10 ↔ mask-only R10: `0.922493`
- Complete-context R11 ↔ mask-only R11: `0.895997`

The experiment binds the baseline experiment and raw-vector hashes in
`experiment.json`.

## What this establishes

Removing unselected source context materially changed all three
relationships. It made the intended R10↔R11 pair more similar and eliminated
its previous clear loss to R10↔R12. However, it did not produce a meaningful
separation between those two edges; they remained almost equal.

The observed changes are consistent with the complete R10 note supplying
additional solar-related context and the complete R11 note supplying unrelated
job, vehicle, and project details. This experiment does not isolate which
specific context tokens caused each change.

Therefore, the original solar result cannot be treated as clean evidence that
SSE failed to represent solar-powered mining. But mask-only encoding has not
yet shown that SSE can robustly distinguish solar-powered mining from solar
power more generally.

This result does not address automatic mask extraction or segmentation.
