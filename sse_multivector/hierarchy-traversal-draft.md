# Three-note automatic traversal trial — historical baseline

This record preserves the saved Bootstrap-v109 / Compare-v179 trial and its
limitations. It used the former `traversal-v24` selection policy, predating V2
and [hierarchy generation V3](../docs/recommendation-engine/hierarchy-generation-v3.md).
Its frozen source worktree and native receipts remain required for reproduction. The current
constructor replaces those policies; these measurements do not qualify V3.

## Three-note automatic trial with Bootstrap-v109 and Compare-v179

The user selected these exact prompts for the first real automatic trial on
2026-10-11. The saved ASv6.100 corpus is an unchanged copy of
`oracle-mvp-shr-pair-correctness-v1/target/bootstrap-asv6.100-regression-refresh-v1/collected/subjects.json`.
Selected original notes, in order: rocket-stove cooking (`99e6a514…`), lamb dinner
(`26749e4b…`) and shrimp risotto (`a7475c94…`). Full IDs and frozen bindings are in
`oracle-mvp-canonical-traversal-three-note-v1/target/canonical-traversal-three-note-v1/traversal.spec.json`
and `trial/state.json`. Execution used the shared stable launcher, GPT-6.1 Sol
medium subscription requests and a persistent 100-attempt safety limit. The
Consolidation-v4 text was copied unchanged from the shaping task; no prompt was
edited or broadly activated.

The automatic command finished with three independent canonical roots: Cooking,
Dinner and Food. Each represents one distinct note, so individual access passes
and the zero-edge graph has no note-set violations. Compare-v179 returned
neither for all three root pairs; its reasons distinguish the required cooking
activity, evening-meal restriction and Food's human-consumer restriction. These
are saved model judgments, not new human gold. Five local entries were selected;
three were placed and two concurrent searches were preserved without placement.
The run stopped during L1. It exercised neither descendant placement nor
consolidation, and therefore does not qualify those behaviors or hierarchy
quality generally.

Native accounting reconciles 15 fresh attempts, including warmups and one
recovered failure, plus two exact answer reuses. There were zero terminal
failures or held placements. Two unrun comparison cases remain paused following
the stopping decision. Known fresh API-equivalent catalog cost is $0.067084;
the complete total is unknown because the failed attempt lacks usage. Receipts,
`run-summary.json`, `audit.json`, `usage.json` and resume state remain in the
ignored task artifacts. The task worktree must remain for those frozen paths.

**Frozen trial limitation:** strict note-set narrowing was a stopping check;
the L1-first round-robin selector had no rule targeting equal-note-set edges.
The six-sibling consolidation trigger addressed option count, and could not be
assumed to remove such edges. This trial has no edges and does not exercise that
limitation. The user subsequently approved the redundant-step removal and
restricted refinement selection in the former constructor. Those changes were implemented and
covered by offline production-path checks; this saved trial is unchanged and
does not validate them with live model judgments.
