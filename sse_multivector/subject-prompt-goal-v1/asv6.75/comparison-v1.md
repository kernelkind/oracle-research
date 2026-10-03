# ASv6.75 fixed comparison with ASv6.74

Status: approved, frozen before generation. The user approved testing the exact
ASv6.75 draft on 2026-10-02 after reviewing its delta and offline audit. This
authorizes this comparison; no candidate is adopted. Production SP remains
ASv6.48 and MP is outside scope.

## Frozen source and trials

Use the committed ASv6.75 source and ordinary POST template without changes:
source SHA-256 `4a673d7d6c87dc568bcf6043e46bb05c01ca873eacc9c87c4797f12231dc8c70`;
template SHA-256 `ad2d0130f4bf0c1fb4afbeae32209a6ca82a0994b6da539832e34887045e5ccb`.
ASv6.74 source remains
`3c94791e498fa002d05dcdea144770d0b313fffcb01421ca0b251e7f9e247560`.
All instruction bytes and C2–C7 remain unchanged between the two versions.

Prepare only through native `experiment.py prepare --from`, with ASv6.75's
template, prompt ID and `--repeat`. Preserve the exact complete inputs,
evidence, schema and saved baseline output for every selected case. Do not
rerun baselines, select trials by their quality or stop early for quality.

| Cases | Candidate trials | Saved ASv6.74 baseline |
| --- | --- | --- |
| S001–S008, D001–D008 | Three independent trials each: 48 new answers | `as74-scope-min-medium-r1` through `r3`, paired by trial. |
| N063, N074, N096, N100 | Five independent trials each: 20 new answers | `as74-original-medium-r1` through `r5`, paired by trial. |
| I011, I012 | Three independent trials each: six new answers | Select these two cases from `as74-interactions-medium-r1` through `r3`. |

The repair cases inspect regressions after replacing their closely related C1.
The minimized cases inspect scope and source/placement separately. Original
posts inspect transfer within the used regression set. All are development
evidence; this is not unseen-topic validation.

## Criteria fixed before generation

Reuse the committed criteria for
[scope minimization](../autonomous-sp-v1/scope-minimization-v1.md#pre-generation-criteria),
[original posts](../autonomous-sp-v1/README.md#fixed-repeated-comparison-asv658-versus-asv673)
and [repair interactions](../autonomous-sp-v1/interaction-audit-v1.md#pre-generation-criteria).
Judge equivalent wording by meaning, without imposing a tree shape or phrase.

- **Scope:** inspect heading strings alone. Generic salt/oil cannot inherit
  food purpose; tissue or scraps merely for the dog cannot inherit feeding.
  Explicit qualified interpretations are allowed when supported. Inspect other
  displayed restrictions, including counts, medium size, first use and newness.
- **Source:** preserve specific participants, amounts, modifiers, negation,
  references and expressed relationships. Keep source material groups and
  complete actions; separate pieces or context cannot replace their combination.
  The dog trim amount is for the combined tissue/scraps, not each separately.
- **Placement:** inspect every compatible numbered parent occurrence for each
  complete source group/action. Descendants count. Correct scope elsewhere does
  not repair a bare child, and a correct copy elsewhere cannot fill an omitted
  branch. Explicit dog-feeding materials concern every returned Dog food parent,
  including copies otherwise containing only the separate myoglobin topic.
- **Exposure:** report whether food/seasoning/feeding parents were actually
  returned, separately from observed valid/invalid edges. No parent means zero
  observations, not a successful relationship check.

Reject with a concrete confirmed witness. Where no confirmed failure is found
but a material question remains, mark uncertain; bounded acceptance is not
full-SP gold. Keep N063's complete-dish/ingredient-group question, uncertain
ingredient memberships, N100's chicken/myoglobin ambiguity and derived
broader-heading closure outside confirmed rejection counts. Preserve the open
C2 help/appreciation question. These are agent assessments, not user labels.

Record one current output-bound native agent review per completed answer.
Report all trials, including failures/uncertainties, exact numbered witnesses
and changes to baseline findings. Do not collapse scope, source and placement
into a claim that qualification alone fixes the prompt.

## Execution, budget and scale

All eleven experiments use subscription `openai-codex`, exact `gpt-6.1-sol`,
medium, WebSocket, 1,800-second timeout, no output-token cap or paid fallback.
Scope-minimization concurrency stays four per experiment. Original-post and
repair concurrency is one per experiment, overriding the predecessors' four
and twelve solely to bound scheduling. At most twenty requests can be in
flight across the independent native runners; each owns its scheduling.

Plan 74 new answers. The persistent campaign attempt budget starts at 356 of
1,000 and is never reset or refunded. Every run names
`target/sp-autonomous-v1/attempt-budget.json` and the existing history root is
`target/sp-autonomous-v1/history`. Native provider-only retries permit at most
two total attempts per case. Bound each sixteen-case run to 32 attempts, each
four-case run to eight and each two-case run to four, including retries.
All-first-attempt success reaches 430; the full allowed 148 attempts reaches
504, still beneath the campaign ceiling. Retain malformed/local/unknown
failures without ineligible retry or quality-driven reruns.

SP still uses one model pass per post. This finite comparison introduces no
production component; ASv6.75 adds 2,129 fixed UTF-8 input bytes per post.
Hierarchy repetition remains part of the existing contract. Use native reports
for usage, without manual token/cost aggregation. Subscription incremental cash
is zero; quota and provider billing are unmeasured and catalog estimates are
not bills. No paid commitment is added.

The ignored native directories are `as75-scope-min-medium-r1` through `r3`,
`as75-original-medium-r1` through `r5`, and `as75-repair-medium-r1` through `r3`,
under `sse_multivector/experiments/sp-autonomous-v1/`. Before launch, run the
offline example/attempt-budget/revision tests and verify exact frozen source,
rendering, inputs/evidence/settings and paired baselines. After completion,
verify native receipts, fresh attempts, absence of reuse and every review's
current input/output binding. Commit this plan before inference; keep rendered
inputs, model outputs and per-run reports ignored.
