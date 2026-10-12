# Official hierarchy runs and experimental parameters

This Markdown file is the register of official hierarchy runs and their
experimental parameters. **HR05** is the completed 24-note rerun with a review UI.
**HR04** is the completed 12-note run; **HR03** is the completed 50-note baseline.
Each run's raw build, browsing menu and export share its ID.

**HR08** has finished with a partial result: 23 of 24 notes, after eligible
selection was exhausted. **HR09** completed with all 24 notes. **HR10** was
stopped by the user on October 12, 2026 at 20:16 UTC after its authorized resume.
It retains a partial graph with 48 of 50 notes, 136 of 164 guaranteed entries
settled and 4,088/10,000 attempts. Final catalogue, review UI and accounting
for this stop are being prepared. Their fixed V2 parameters are
recorded below; native preparation pinned exact source
commits, prompt hashes and input evidence before model requests.

**HR06** and **HR07** preserve the two earlier ASv6.48 builds the user reviewed.
They were registered later, so ID order is not generation order. The intervening
16-note builds are not official entries.

| Run | Notes | Subject prompt | Bootstrap / Compare |
| --- | --- | --- | --- |
| HR06 | 8 | ASv6.48 | v88 / v36 |
| HR07 | 50 | ASv6.48 | v96 / v48 |
| HR03 | 50 | ASv6.100 | v96 / v48 |
| HR04 | 12 | ASv6.100 | v109 / v179 |
| HR05 | 24 | ASv6.100 | v109 / v179 |
| HR08 | 24 | ASv6.100 | v109 / v179 |
| HR09 | 24 | ASv6.100 | v122 / v192 |
| HR10 | 50 | ASv6.100 | v122 / v192 |

## HR08–HR10 — approved V2 comparison

| Parameter | HR08 | HR09 | HR10 |
| --- | --- | --- | --- |
| Status | Exhausted selection; partial, 23/24 notes | Complete, 24/24 notes | User-stopped after resume; partial, 48/50 notes |
| Notes | HR05's same 24, same order | HR05's same 24, same order | HR03's exact original 50-note AS selection order |
| Run definition | [HR08](../../sse_multivector/hierarchy-runs/hr08/traversal.spec.json) | [HR09](../../sse_multivector/hierarchy-runs/hr09/traversal.spec.json) | [HR10](../../sse_multivector/hierarchy-runs/hr10/traversal.spec.json) |
| Prepared provenance | [HR08](../../../oracle-mvp-hierarchy-hr08-v2/target/hierarchy-hr08-v2-24-note-v1/prepared-provenance.json) | [HR09](../../../oracle-mvp-hierarchy-hr09-v2/target/hierarchy-hr09-v2-24-note-v1/prepared-provenance.json) | [HR10](../../../oracle-mvp-hierarchy-hr10-v2/target/hierarchy-hr10-v2-50-note-v1/prepared-provenance.json) |
| Continuation provenance | [HR08](../../../oracle-mvp-hierarchy-hr08-v2/target/hierarchy-hr08-v2-24-note-v1/continuation-provenance-v1.json) | [HR09](../../../oracle-mvp-hierarchy-hr09-v2/target/hierarchy-hr09-v2-24-note-v1/continuation-provenance-v1.json) | [HR10](../../../oracle-mvp-hierarchy-hr10-v2/target/hierarchy-hr10-v2-50-note-v1/continuation-provenance-v1.json) |
| Subject trees | Saved ASv6.100 from HR03 | Same | Same |
| Local subject entries / L1 roots | 832 / 150 | 832 / 150 | 1,510 / 326 |
| Bootstrap | v109 | v122 | v122 |
| Compare | v179 | v192 | v192 |
| Consolidation | v4, exact HR05 prompt | v18 | v18 |
| Prominence | PPv35-post-meaning-v1 | Same | Same |
| Persistent attempt ceiling | 3,000 | 3,000 | 10,000 |

All three use `hierarchy-generation-v2`, local schema 4 and an empty initial
graph. They reuse the exact ASv6.100 corpus SHA-256
`18370b4772fee22c8d11f49a505f20f781f163e0512a8f32473d487ebdc8849a`;
no subject extraction or vector generation is included.

V2 establishes an independent Bootstrap meaning and PPv35 prominence for every
original L1. For each note it guarantees every L1 scoring at least 50, or the
first highest-scoring L1 when none meets 50. Guaranteed processing and triggered
consolidation finish before additional L1 selection for uncovered notes.
Eligible deeper heading matches take priority over prominence-ordered refinement
of multi-note leaves. Original note order and local-node tie order are retained.
There is no prominence cutoff for deeper entries. Exact native answer reuse
retains its producer evidence and is reported separately from new attempts.

Model execution is `openai-codex` subscription / `gpt-6.1-sol` / medium reasoning
/ SSE, with prefix caching and automatic warming for eligible prompts. Bootstrap,
Compare and consolidation retain caching; PPv35's 829-token prefix is below the
runner's 1,024-token minimum and runs uncached. Bootstrap and prominence use
600-second timeouts; Compare and consolidation use 1,800 seconds. No explicit
output-token limit, seed or temperature override is set. Each hierarchy permits
three active searches with placements in selection order; the shared provider
queue admits at most 30 requests across experiments. Each run's separate
persistent ceiling includes warmups, retries and every resume.
Native provider-transient failures permit at most two attempts per case across
resumes. There are no manual retries or repairs of semantic/schema failures.

The three runs share a fresh native history at
`target/hierarchy-v2-official-history-v1/` in the canonical repository's ignored
artifact storage. Native request identity and producer receipts govern exact
reuse across these official runs; earlier diagnostic outputs are not added to
this history. Identical requests are not additional independent samples.

The original three isolated project worktrees remain frozen at generation commit
`1a7f68a3b27b8ab19f30256a6c613ce28768e0d9`. Both the shared stable launcher
and model worker use the isolated runner worktree
`experiment-runner-hr08-hr10-source-v1`, frozen at
`e19592f9a6b0b3a2b3ac0bc63220156d86a0f1a7`. Native preparation records
exact prompt/schema/code hashes and clean source status before dispatch.

Consolidation is best effort after an addition leaves at least six siblings,
including roots. Proposals undergo ordinary Compare traversal and placement
checks; Audit-v5 is not an extra construction step. Finished-view shaping keeps
the child of an equal-note-set single-child parent; for a multiple-child parent
it retains the parent and bypasses equal-note-set children on that branch.
The raw canonical graph and fixed meanings remain preserved.

Completion requires all guaranteed entries and triggered consolidation to
finish, exhaustion of eligible selection, access to every selected note, and
strictly narrowing browsing edges, with no unresolved original L1 scoring.
Refinement exhaustion may leave multi-note
leaves; singleton leaves are measured rather than required by V2. An exhausted
attempt allowance preserves partial work and reports unfinished construction.

Bootstrap-v122, Compare-v192 and Consolidation-v18 remain experimental.
These official runs evaluate them without declaring the prompts qualified or
changing their adoption status. Each output will receive its run ID, a review
view, a native usage report and API-equivalent cost accounting. Full generation
commits and clean uncommitted-source status were recorded before execution;
Final HR08/HR09 results, HR10's current user stop and its historical pre-resume
checkpoint are recorded below. HR10 retains an unfinished graph because the
user stopped construction. Its 10,000-attempt ceiling was not exhausted.

### Initial execution checkpoint

All original L1 Bootstrap answers are schema-valid: 150 for HR08, 150 for HR09
and 326 for HR10. HR08 and HR09 have non-null meanings for every root; HR10 has
two null meanings. HR10 includes 150 exact native reuses from HR09. The drivers
stopped before any prominence request or placement because V2 inherited Bootstrap's
cache flag for PPv35, whose fixed prefix has 829 estimated tokens, below the
shared runner's 1,024-token minimum. Saved meanings, receipts and counters are
preserved. A tested constructor fix now applies the native prefix eligibility
policy. Reviewed continuation from separate isolated source worktrees records
the original and replacement constructor paths and hashes, the effective PP
cache setting, and the archived zero-call preparation. All selected prompt
bytes, note inputs and persistent counters remain fixed. The three production
regressions and relevant constructor/graph/receipt/viewer suite pass 59 tests;
all three also pass on the combined landed result.

The cache fix is commit `90cfa66026a9167a314607a22f7a4b7ad1eceb56` on local
`main`. All three continuation source worktrees are frozen at
`542d5697ccee1b85b28f3ded0a9e093c36de0c1b`; the original worktrees and
meaning receipts remain unchanged. Native `source_upgrades` records all eight
constructor bindings, old/new source hashes, PP caching true to false, and the
archived unprepared batch. The original counters were 152/3,000, 151/3,000 and
178/10,000 at continuation; none was reset. Prominence preparation and scoring
have finished. The saved outcomes below supersede this initial checkpoint.

### Scoring checkpoint

| Measurement | HR08 | HR09 | HR10 |
| --- | ---: | ---: | ---: |
| Non-null original L1 meanings | 150 / 150 | 150 / 150 | 324 / 326 |
| Valid original L1 prominence scores | 149 / 150 | 150 / 150 | 324 / 324 attempted |
| Guaranteed entries established from valid scores | 75 | 90 | 164 |
| Unresolved original L1 entries | 1 | 0 | 2 |

HR08's prominence answer for **GrowNostr**, local entry `10` of note
`25f5a4c…`, contains invalid JSON (`fifty` as an unquoted value). HR10's
Bootstrap answers for local entry `4` of note `862486d8…` and local entry `7`
of note `e0508834…`, both coffee-chain subjects, contain null meanings; no
prominence requests are made for those entries. The saved answers remain
unchanged and are not manually retried. A note with unresolved original L1
scoring is not eligible for V2 selection. These unresolved entries prevent
construction from being reported complete even if the remaining selection
finishes. Saved results below retain the native status and coverage measurements.

## Token usage and API cost

These totals cover hierarchy construction: Bootstrap, prominence where used,
Compare and consolidation, including warmups, retries, unused charged producers
and the original generation
behind exact answer reuses, counted once. Separate subject extraction and vector
encoding are excluded. HR06 includes its three-note base and the seven original
producer calls behind reused answers.

HR10's usage and cost values below describe its preserved pre-resume checkpoint
at 2,635 attempts. Native accounting for the user stop at 4,088 attempts is being
prepared; these historical subtotals do not cover the resumed work.

| Run | Uncached input | Cached input | Output | Reasoning within output | Known total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| HR06 | 388,609 | 0 | 23,141 | 2,816 | 411,750 |
| HR07 | 2,335,245 | 4,790,016 | 398,063 | 56,493 | 7,523,324 |
| HR03 | 1,576,819 | 3,422,720 | 279,473 | 47,330 | 5,279,012 |
| HR04 | 63,494 | 324,096 | 58,375 | 14,516 | 445,965 |
| HR05 | 155,217 | 898,560 | 172,399 | 43,644 | 1,226,176 |
| HR08 | 963,210 | 4,528,896 | 1,046,126 | 260,212 | 6,538,232 |
| HR09 | 1,096,320 | 4,925,056 | 1,149,130 | 314,234 | 7,170,506 |
| HR10, pre-resume checkpoint | 1,482,908 | 6,448,384 | 1,421,127 | 374,549 | 9,352,419 |

Known total tokens = uncached input + cached input + output. Reasoning is already
included in output and must not be added again. All listed reports record zero
cache-write tokens. Failed calls with missing usage are excluded from these
known subtotals; their consumption is unknown.

| Run | Known API-equivalent generation cost | Calls missing usage/cost |
| --- | ---: | ---: |
| HR06 | $1.008628 | 0 |
| HR07 | $9.1301216 | 7 |
| HR03 | $6.290640 | 12 |
| HR04 | $0.7431476 | 1 |
| HR05 | $2.124280 | 3 |
| HR08 | $12.8405696 | 28 |
| HR09 | $14.1764456 | 10 |
| HR10, pre-resume checkpoint | $17.8219244 | 27 |

Costs use the saved per-call API catalogue estimates, not subscription charges
or current-price recalculation. HR06's complete saved generation estimate
includes $0.907694 newly dispatched during the three-to-eight-note lineage plus
original generation behind reused answers. The other listed cost totals remain
incomplete because failed attempts lack usage and cost estimates. HR08 includes
one exact prominence-answer reuse from HR09. Its newly dispatched subtotal is
$12.8365336; the generation subtotal above includes that original producer.
Do not sum per-run generation costs across HR08–HR10: shared producer calls
would be counted more than once. HR09 has no reuses; HR10's pre-resume checkpoint
has 709, with a newly
dispatched cost subtotal of $13.3828492. The combined native report counts each
original producer once. At HR10's historical pre-resume checkpoint, the
[combined report](../../target/hierarchy-catalogue/usage/HR08-HR10-combined-v1.json)
and [inventory](../../target/hierarchy-catalogue/usage/HR08-HR10-combined-source-v1.json)
cover 1,275 experiments and 7,884 fresh attempts: **20,755,595 known tokens**
and **$40.3958284 known API-equivalent cost**, with 65 failed attempts missing
usage and cost. All reused producers occur in this combined inventory; no
additional source calls are added. Fresh accounting for the resumed HR10 user
stop is being prepared; these files preserve the earlier checkpoint.

HR03's [original full report](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/usage-v2.json)
also includes ASv6.100 extraction: another 549,380 known tokens and $1.005864,
with two additional failed calls missing usage. Its combined extraction and
construction inventory has 5,828,392 known tokens and a $7.296504 known cost subtotal. The
[construction-only native report](../../target/hierarchy-catalogue/usage/HR03-hierarchy.json)
used above excludes only that AS experiment; its
[354-experiment inventory](../../target/hierarchy-catalogue/usage/HR03-hierarchy-source.json)
retains all hierarchy producers and comparisons. HR04–HR07 usage reports are
linked in their run records below.

## HR09 — ASv6.100 24-note V2, new prompts

Completed October 12, 2026 with native construction and execution status
`complete`, after eligible selection and dispatched work finished. It uses
Bootstrap-v122, Compare-v192, Consolidation-v18 and PPv35-post-meaning-v1.

| Measurement | Saved result |
| --- | --- |
| Notes represented and individually accessible | 24 of 24 |
| Guaranteed original L1 entries settled | 90 of 90 |
| Local selections | 94: 77 additions, one equivalent, 16 held |
| Consolidation | 29 parents placed, 27 proposals held |
| Raw graph | 106 nodes, 123 edges, three roots |
| Shaped browsing menu | 103 nodes, 120 strictly narrowing edges, three roots |
| Maximum child choices | Seven; one warning above the soft target of six |
| Multi-note leaves / unresolved original scoring | Zero / zero |
| Native attempts | 2,646 of 3,000: 419 warmups and 2,227 ordinary attempts; counter delta zero |
| Exact answer reuses | Zero |
| Model cases | 2,218 valid; zero malformed, failed or unrun |
| Failed / recovered / retry attempts | 10 / 10 / 10 |
| Known API-equivalent generation cost | $14.1764456; 10 recovered failed calls have unknown usage and cost |

The [immutable state](../../../oracle-mvp-hierarchy-hr09-v2/target/hierarchy-hr09-v2-24-note-v1/HR09/state.json)
has SHA-256 `059840fdf8a43794392990ea40c685eb54019ecbd49657c465ff8101068af44e`.
The [final code provenance](../../../oracle-mvp-hierarchy-hr09-v2/target/hierarchy-hr09-v2-24-note-v1/HR09/code-provenance.json)
records initial Oracle `1a7f68a3b27b8ab19f30256a6c613ce28768e0d9`, continuation
`542d5697ccee1b85b28f3ded0a9e093c36de0c1b` and runner
`e19592f9a6b0b3a2b3ac0bc63220156d86a0f1a7`, all clean. It labels the correction
of an initial plan digest incorrectly described as a manifest digest; original
files, prompts, model outputs and receipts are preserved.

The [native structural audit](../../../oracle-mvp-hierarchy-hr09-v2/target/hierarchy-hr09-v2-24-note-v1/HR09/audit.json)
passes all structural constraints. Its `done: false` and ungraded semantic
assessment do not override native construction completion. The
[usage report](../../../oracle-mvp-hierarchy-hr09-v2/target/hierarchy-hr09-v2-24-note-v1/usage.json)
has `complete: true`, `usage_complete: false`; its
[inventory](../../../oracle-mvp-hierarchy-hr09-v2/target/hierarchy-hr09-v2-24-note-v1/usage-source.json)
includes every charged experiment.

Open the checked review UI, with all 24 original note bodies:

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr09-v2/target/hr09-review-ui-v1/launch.sh
```

The [UI provenance](../../../oracle-mvp-hierarchy-hr09-v2/target/hr09-review-ui-v1/provenance.json)
records exact native exports, the exporter commit and the existing HR05 viewer
binary hash. No display placements were added; the original binary build commit
remains unknown.

## HR10 — ASv6.100 50-note V2, new prompts, user-stopped

The user stopped HR10 on October 12, 2026 at 20:16 UTC. The
[user-stop record](../../../oracle-mvp-hierarchy-hr10-v2/target/hierarchy-hr10-v2-50-note-v1/user-stop-20261012-v1.json)
records driver exit 130, the cancelled notification watcher and no queued
completion message. The graph remains `constructing` in `guaranteed_l1`:
136/164 guaranteed entries settled, 140 raw nodes and 48/50 notes represented.
The persistent counter remains 4,088/10,000. Execution status is `user_stopped`;
this stop is not a new provider blockage or completed construction. The native
`run-summary.json` was not rewritten by interruption and describes only the
historical pre-resume provider blockage. Final catalogue binding, review UI,
native audit and accounting for this stop are being prepared.

The user had authorized resume earlier on October 12, 2026. The native driver
resumed the original `trial` from frozen continuation commit
`542d5697ccee1b85b28f3ded0a9e093c36de0c1b` and runner
`e19592f9a6b0b3a2b3ac0bc63220156d86a0f1a7`. Code, prompts and note selection
remain fixed. The existing graph and answers are preserved; new work advances
the same 10,000-attempt counter. It prepared a new
native warmup child; the warmup and previously unrun comparison succeeded at
2,637 attempts before construction advanced to the user stop. The
[resume provenance](../../../oracle-mvp-hierarchy-hr10-v2/target/hierarchy-hr10-v2-50-note-v1/resume-20261012-v1-provenance.json)
and [native resume log](../../../oracle-mvp-hierarchy-hr10-v2/target/hierarchy-hr10-v2-50-note-v1/resume-20261012-v1.log)
retain this continuation. The prior checkpoint, cost reports and review UI
below remain unchanged and describe the historical pre-resume outcome.

### Historical pre-resume provider-blocked checkpoint

Stopped October 12, 2026 with native graph status `constructing` and execution
status `blocked`. The final comparison cache warmup, batch `00443`, failed twice
with provider `server_error`, after approximately 61 seconds each, below its
1,800-second timeout. The driver exited with status 1. No manual retry or
attempt-counter reset occurred. This is an unfinished official run.
Native resume can prepare a new warmup child while preserving the exhausted
child's two failed attempts, the current graph and the same attempt counter.
At that checkpoint there were 7,365 attempts remaining. Its saved snapshot
remains preserved under the same run ID; all measurements and artifacts below
describe the historical pre-resume checkpoint.

| Measurement | Saved result |
| --- | --- |
| Notes represented and individually accessible | 48 of 50 |
| Selection phase | `guaranteed_l1` |
| Guaranteed original L1 entries settled | 92 of 164; two additional selections remain unsettled |
| Settled local entries | 92: 78 additions, four equivalents, 10 held |
| Consolidation | 24 parents placed, 37 proposals held |
| Raw graph and current browsing menu | 102 nodes, 123 strictly narrowing edges, five roots |
| Maximum child choices | 11; four nodes exceed the soft target of six |
| Multi-note leaves | One two-note leaf, C083 |
| Unresolved original scoring | Two null Coffeechain meanings; both notes excluded from eligible selection |
| Native attempts | 2,635 of 10,000; counter delta zero |
| Native experiments / exact answer reuses | 444 / 709 |
| Model cases | 2,941 valid, one terminal comparison failure, one unrun comparison blocked by warmup |
| Failed / recovered / retry attempts | 27 / 23 / 25 |
| Known API-equivalent fresh / generation cost | $13.3828492 / $17.8219244; 27 failed calls have unknown usage and cost |

An earlier consolidation comparison, `batch-00132/C057`, failed twice with
streaming socket closures after 45.28 and 38.21 seconds; its proposal remains
held. The final warmup failure stopped further construction. The two unresolved
original meanings independently prevent completion under V2; saved answers
remain unchanged. Every current displayed edge narrows note sets, but the
native structural audit fails missing-note coverage.

The [immutable stopped state](../../../oracle-mvp-hierarchy-hr10-v2/target/hierarchy-hr10-v2-50-note-v1/HR10/state.json)
has SHA-256 `3ee17399c36543a3f8531c5538cbd4fd19d046ef1ea7db6032804926eeacb1d7`.
The [checkpoint code provenance](../../../oracle-mvp-hierarchy-hr10-v2/target/hierarchy-hr10-v2-50-note-v1/HR10/code-provenance.json)
preserves initial Oracle `1a7f68a3b27b8ab19f30256a6c613ce28768e0d9`, continuation
`542d5697ccee1b85b28f3ded0a9e093c36de0c1b` and runner
`e19592f9a6b0b3a2b3ac0bc63220156d86a0f1a7`, all clean. It labels completion
and cache metadata corrections while retaining the original provenance.

The [native audit](../../../oracle-mvp-hierarchy-hr10-v2/target/hierarchy-hr10-v2-50-note-v1/HR10/native-audit.json),
[usage report](../../../oracle-mvp-hierarchy-hr10-v2/target/hierarchy-hr10-v2-50-note-v1/HR10/native-usage-summary.json)
and [inventory](../../../oracle-mvp-hierarchy-hr10-v2/target/hierarchy-hr10-v2-50-note-v1/HR10/usage-source.json)
retain this historical pre-resume outcome. Both usage completion flags are false. Generation
usage includes the exact original producer calls behind reused answers; subject
extraction remains excluded.

Open the checked historical pre-resume review UI:

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr10-v2/target/hr10-review-ui-v1/launch.sh
```

It includes all 50 original note bodies. The two missing notes appear only on
the display root, labelled unresolved, without canonical placements. The
[UI provenance](../../../oracle-mvp-hierarchy-hr10-v2/target/hr10-review-ui-v1/provenance.json)
preserves exact native exports, records the frozen exporter and existing HR05
binary hashes, and confirms the viewer check. The binary's original build
commit remains unknown. This UI describes the stopped checkpoint and does not
imply that construction completed or show the resumed user-stopped graph.

## HR08 — ASv6.100 24-note V2, previous prompts

Finished October 12, 2026 with native construction and execution status
`exhausted`. Eligible selection ended at 2,603 of 3,000 attempts; the allowance
was not exhausted. Its prompts are Bootstrap-v109, Compare-v179,
Consolidation-v4 and PPv35-post-meaning-v1, as approved above.

| Measurement | Saved result |
| --- | --- |
| Notes represented and individually accessible | 23 of 24 |
| Guaranteed original L1 entries settled | 75 of 75 |
| Local selections | 84: 68 additions, four equivalents, 12 held |
| Deeper heading matches | Three selections: two held, one equivalent |
| Consolidation | 19 parents placed, 25 proposals held, five null proposals |
| Raw graph | 87 nodes, 110 edges, four roots |
| Shaped browsing menu | 84 nodes, 106 strictly narrowing edges, four roots |
| Maximum child choices | 10; six is a soft branching target |
| Leaves with multiple notes | One two-note leaf, C012, after eligible refinement ended |
| Unresolved original scoring | One malformed prominence answer, GrowNostr, note `25f5a4c…` |
| Native attempts | 2,603: 408 warmups and 2,195 ordinary attempts; counter delta zero |
| Exact answer reuses | One prominence answer originally generated in HR09 |
| Model cases | 2,170 valid, one malformed, three terminal provider failures; zero unrun |
| Failed / recovered / retry attempts | 28 / 22 / 25 |
| Known API-equivalent generation cost | $12.8405696; 28 failed calls have unknown usage and cost |

The malformed GrowNostr prominence answer made its note ineligible for V2
selection. The native structural audit fails missing-note coverage; all 106
displayed edges strictly narrow note sets. It does not grade meanings or
relationships. Two heading-match comparison cases and one leaf-refinement case
exhausted native provider retries and remain held. Saved outputs are unchanged.

The [immutable state](../../../oracle-mvp-hierarchy-hr08-v2/target/hierarchy-hr08-v2-24-note-v1/HR08/state.json)
has SHA-256 `156c83cd1db31075eef485d8447394ec85903fe135eec1aa8f5c5929ce1035f9`.
The [final code provenance](../../../oracle-mvp-hierarchy-hr08-v2/target/hierarchy-hr08-v2-24-note-v1/HR08/code-provenance.json)
records original Oracle commit `1a7f68a3b27b8ab19f30256a6c613ce28768e0d9`,
reviewed continuation `542d5697ccee1b85b28f3ded0a9e093c36de0c1b`, and runner
`e19592f9a6b0b3a2b3ac0bc63220156d86a0f1a7`, with clean source status.
It preserves the original provenance and labels the metadata correction:
singleton leaves are measured, rather than required for V2 completion.

The [native structural audit](../../../oracle-mvp-hierarchy-hr08-v2/target/hierarchy-hr08-v2-24-note-v1/audit-v1.json),
[usage report](../../../oracle-mvp-hierarchy-hr08-v2/target/hierarchy-hr08-v2-24-note-v1/usage-v1.json)
and [complete charged-experiment inventory](../../../oracle-mvp-hierarchy-hr08-v2/target/hierarchy-hr08-v2-24-note-v1/usage-source-v1.json)
retain the evidence. The usage report's `complete` and `usage_complete` are false:
one malformed case and three terminal failures remain, and failed-call
consumption is unknown.

Open the review UI:

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr08-v2/target/hr08-review-ui-v1/launch.sh
```

It includes all 24 original note bodies. The missing note appears only on the
display root, labelled as absent from the canonical hierarchy; this adds no
canonical placement. Exact native exports are preserved alongside the review
data. The [UI provenance](../../../oracle-mvp-hierarchy-hr08-v2/target/hr08-review-ui-v1/provenance.json)
records the exporter commit, file hashes and passing viewer check. The existing
HR05 viewer binary was copied exactly; its original build commit is unknown.

## HR05 — ASv6.100 24-note hierarchy

Approved as a rerun of HR04 with 24 notes and completed October 11, 2026. The
[run definition](../../sse_multivector/hierarchy-runs/hr05/traversal.spec.json)
records complete note IDs in their original selection order. The prompts, model
settings and hierarchy source match HR04; the selected note count changed from
12 to 24, with a fresh 500-attempt allowance.

### Result

| Measurement | Saved result |
| --- | --- |
| Construction / execution status | complete / complete |
| Notes represented and individually accessible | 24 of 24 |
| Raw graph and browsing menu | 30 nodes, 26 edges, 5 roots |
| Maximum child choices | 5 |
| Structural audit | Passed; all 26 edges strictly narrow note sets, all 18 leaves contain one note, no violations |
| Selected local entries | 26, all L1 roots; 24 placed and two searches retained without placement after stopping |
| Local placements | 23 additions and one equivalent |
| Consolidation proposals | 15: seven placed, eight held |
| Held local entries | 0 |
| Native attempts | 459 of 500: 119 warmups and 340 ordinary attempts |
| Valid model answers | 339; three provider failures recovered by retry, no terminal failures |
| Unrun prepared cases | 5 speculative comparisons, paused when construction stopped |
| Exact answer reuses | 0 |
| Known API-equivalent cost subtotal | $2.12428; complete total unknown because three recovered failed attempts have no usage |

The run stopped during L1. It did not need deeper refinement or removal of
equal-note-set steps, so it does not establish their behavior with live model
judgments. The structural audit does not grade meanings or relationships; its
`done` field deliberately remains false. Saved teacher judgments and all eight
held proposals remain unchanged. The native usage report has `complete: false`
because five speculative cases remain unrun; construction and execution are
complete. The attempt ledger and counter reconcile exactly. The saved cost is
an API catalogue estimate, not a subscription charge.

### Review UI

Open the existing terminal hierarchy viewer:

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr05-twenty-four-note-v1/target/hr05-review-ui-v1/launch.sh
```

Use `j`/`k` to select, `Enter` to open, `n` for all notes, `d` for direct notes,
`o` for notes outside children, `?` for meanings and details, and `q` to exit.
The UI preserves all 30 hierarchy nodes, shared parents, fixed meanings and the
24 full original note bodies. It adds one display root labelled **HR05**, with
no filtering or display collapse. The launcher's production `--check` passed.
The exporter used the generation commits below; the exact existing viewer
binary is retained, with its build commit and build dirty state marked unknown.

### Inputs and construction

| Parameter | Selected value |
| --- | --- |
| Notes | First 24 notes in HR03's frozen 50-note selection, in the same order |
| Subject prompt | ASv6.100; reuse HR03's saved subject trees |
| Local subject entries | 832, including 150 local roots |
| Bootstrap prompt | [Hierarchy-bootstrap-v109](../../sse_multivector/shr_single_pair/Hierarchy-bootstrap-v109.md) |
| Compare prompt | [Hierarchy-compare-v179](../../sse_multivector/shr_single_pair/Hierarchy-compare-v179.md), symmetric A/B fixed meanings |
| Consolidation prompt | [Hierarchy-consolidation-v4](../../sse_multivector/hierarchy-runs/hr05/Hierarchy-consolidation-v4.md), unchanged from the three-note trial |
| Constructor | `traversal-v24`, including landed refinement change `c5cc28d31455403292dd012e862aa871d06e0241` |
| Local schema version | 4 |
| Initial graph | Empty |
| Selection | L1 roots first, then deeper levels; rotate one local entry per note per pass in saved order |
| Refinement after coverage | Deeper entries only from notes represented in leaves containing multiple notes |
| Active local searches | At most 3; placements in selection order |
| Consolidation trigger | An addition leaves 6 or more siblings, including roots; best effort |
| Redundant browsing steps | Bypass equal-note-set parents, retaining deeper headings and preserving the raw graph |
| Completion | All notes individually accessible, one note per browsing leaf, strictly smaller note sets on downward edges |

The selected notes reuse the exact HR03 ASv6.100 corpus. Construction starts
from an empty graph with native meanings and comparisons, retaining any exact
answer reuse with its producer receipts.

### Model execution and attempt allowance

| Parameter | Selected value |
| --- | --- |
| Provider | `openai-codex`, subscription |
| Model | `gpt-6.1-sol` |
| Reasoning effort | medium |
| Transport | SSE |
| Prompt cache | Enabled, with automatic warming |
| Shared provider queue | Maximum 30 requests across experiments |
| Bootstrap timeout | 600 seconds |
| Compare/consolidation timeout | 1,800 seconds |
| Output-token limit | No explicit limit |
| Seed / temperature | Unspecified; no overrides |
| Persistent attempt ceiling | 500 total, including warmups, retries and every resume |

The exact Bootstrap, Compare and consolidation settings are saved alongside the
run definition. The same persistent allowance is used throughout. Reaching its
ceiling preserves partial work and reports unfinished construction.

### Git provenance and retained artifacts

| Generation provenance | Recorded value |
| --- | --- |
| Oracle generation commit | `251cf0edef01397e8403a53e6b00438b1a398a7c` |
| Shared-runner generation commit | `e19592f9a6b0b3a2b3ac0bc63220156d86a0f1a7` |
| Uncommitted source changes at generation | None in either isolated worktree |

The [frozen preparation record](../../../oracle-mvp-hierarchy-hr05-twenty-four-note-v1/target/hierarchy-hr05-twenty-four-note-v1/prepared-provenance.json)
contains all selected IDs, settings, source bindings and initial native plans.
The hierarchy source, prompts and runner fingerprints match HR04. The subject
corpus SHA-256 remains
`18370b4772fee22c8d11f49a505f20f781f163e0512a8f32473d487ebdc8849a`.
Later documentation and prompt-development commits do not change these
generation commits. The retained task worktree and shared runner remain frozen
for source bindings, native receipts and review UI paths. The final graph, menu,
audit, usage and attempt ledger are preserved under
`target/hierarchy-hr05-twenty-four-note-v1/HR05/`.

| Saved artifact | File |
| --- | --- |
| Raw hierarchy | [HR05 raw state](../../target/hierarchy-catalogue/outputs/HR05.json) |
| Browsing menu | [HR05 menu](../../target/hierarchy-catalogue/outputs/HR05-related-1.json) |
| Review UI export | [HR05 viewer hierarchy](../../target/hierarchy-catalogue/outputs/HR05-related-2.json) |
| Complete parameters and evidence | [HR05 record](../../target/hierarchy-catalogue/records/HR05.json) |
| Structural audit | [Saved audit](../../../oracle-mvp-hierarchy-hr05-twenty-four-note-v1/target/hierarchy-hr05-twenty-four-note-v1/HR05/audit.json) |
| Native usage and allowance reconciliation | [Saved usage](../../../oracle-mvp-hierarchy-hr05-twenty-four-note-v1/target/hierarchy-hr05-twenty-four-note-v1/HR05/usage.json) |
| Attempt allowance | [Persistent counter](../../../oracle-mvp-hierarchy-hr05-twenty-four-note-v1/target/hierarchy-hr05-twenty-four-note-v1/attempt-budget.json) |
| Final source and output provenance | [Saved provenance](../../../oracle-mvp-hierarchy-hr05-twenty-four-note-v1/target/hierarchy-hr05-twenty-four-note-v1/HR05/code-provenance.json) |
| Exact generator source snapshots | [43-file source archive](../../../oracle-mvp-hierarchy-hr05-twenty-four-note-v1/target/hierarchy-hr05-twenty-four-note-v1/code-snapshot/manifest.json) |
| Review UI launcher | [Open HR05](../../../oracle-mvp-hierarchy-hr05-twenty-four-note-v1/target/hr05-review-ui-v1/launch.sh) |
| Review UI provenance | [Export, notes and binary hashes](../../../oracle-mvp-hierarchy-hr05-twenty-four-note-v1/target/hr05-review-ui-v1/provenance.json) |

### SHA-256 bindings

| Input, source or output | SHA-256 |
| --- | --- |
| Run definition and note order | `6e2848ec7c291df8abc89ef0fe87175b38dc72233e8aa96bf35ec418d341dec3` |
| Bootstrap-v109 prompt | `caa77221193ce816c6112ea20ea81fcf4bf4739994fa06102e4b41f132128cd1` |
| Compare-v179 prompt | `49d936bd6d5e251bcc1317f34a87fd71c25eb1e63f972e5ec8824b81f73eb9ed` |
| Consolidation-v4 prompt | `144e23d89c65910f0851d4163ac7dff1baee248ebf5dab5c8779c843f9aae7c6` |
| Bootstrap response schema | `5806c8c66ce8a8a9b13fb9f5ff6445eb79bb918cf15925a17fd9354a1877809c` |
| Compare response schema | `9bdea40731448a9ef7b73372743cc258c5f6dc9419377c1d6c563d9dd12bc522` |
| Shared-runner fingerprint | `67a3688360b285fa4de34c08f2009df12708246143163e7a35d7ea04301cc0b8` |
| Request-code fingerprint | `15429b548cf904622a33bdad86c20d523da097c1956cc736ebbb2a513ded9018` |
| Source archive manifest | `a7b75f63a20ae0efc0c2ab0a3410f2d65e5d1784adf1c51720cb4d4914f58e5c` |
| Raw hierarchy | `2c660067560b80055fafd33a97d9fa49ef5861b5daae829f8f9edc9b52abd8e3` |
| Browsing menu | `ec666a427c0855c78c2cbc41abd7c0eab03b7c74025d210471cbef1993524168` |
| Review UI hierarchy export | `3d654734d4f07cb5ece1a3a520e902012c5a0562a83e001b7a908ea0efe2acdd` |
| Review UI full notes | `11bb71d9852f6a1f3f7e3bfae2c54630900588c725df5825e5fa9af10e498fe9` |

## HR04 — ASv6.100 12-note hierarchy

Approved and completed October 11, 2026. The run uses the current
standalone constructor, including restricted refinement, single-note leaves and
deeper-heading retention. The
[run definition](../../sse_multivector/hierarchy-runs/hr04/traversal.spec.json)
records the complete note IDs in their selection order.

### Result

| Measurement | Saved result |
| --- | --- |
| Construction / execution status | complete / complete |
| Notes represented and individually accessible | 12 of 12 |
| Raw graph and browsing menu | 14 nodes, 9 edges, 5 roots |
| Maximum child choices | 6 |
| Structural audit | Passed; all 9 edges strictly narrow note sets, every leaf contains one note, no violations |
| Selected local entries | 14, all L1 roots; two searches retained without placement after stopping |
| Consolidation proposals | 3: two placed, one held because required containment was not established |
| Held local entries | 0 |
| Native attempts | 153 of 500: 45 warmups and 108 ordinary attempts |
| Valid model answers | 107; one provider failure recovered by retry, no terminal failures |
| Exact answer reuses | 0 |
| Known API-equivalent cost subtotal | $0.7431476; complete total unknown because the recovered failed attempt has no usage |

The run stopped during L1. It did not need deeper refinement or removal of
equal-note-set steps, so it does not establish their behavior with live model
judgments. The structural audit does not grade meanings or relationships; its
`done` field deliberately remains false. Saved teacher judgments and the held
proposal remain unchanged.

### Inputs and construction

| Parameter | Selected value |
| --- | --- |
| Notes | First 12 notes in HR03's frozen 50-note selection, in the same order |
| Subject prompt | ASv6.100; reuse HR03's saved subject trees |
| Local subject entries | 416, including 72 local roots |
| Bootstrap prompt | [Hierarchy-bootstrap-v109](../../sse_multivector/shr_single_pair/Hierarchy-bootstrap-v109.md) |
| Compare prompt | [Hierarchy-compare-v179](../../sse_multivector/shr_single_pair/Hierarchy-compare-v179.md), symmetric A/B fixed meanings |
| Consolidation prompt | [Hierarchy-consolidation-v4](../../sse_multivector/hierarchy-runs/hr04/Hierarchy-consolidation-v4.md), unchanged from the three-note trial |
| Constructor | `traversal-v24`, including landed refinement change `c5cc28d31455403292dd012e862aa871d06e0241` |
| Local schema version | 4 |
| Initial graph | Empty |
| Selection | L1 roots first, then deeper levels; rotate one local entry per note per pass in saved order |
| Refinement after coverage | Deeper entries only from notes represented in leaves containing multiple notes |
| Active local searches | At most 3; placements in selection order |
| Consolidation trigger | An addition leaves 6 or more siblings, including roots; best effort |
| Redundant browsing steps | Bypass equal-note-set parents, retaining deeper headings and preserving the raw graph |
| Completion | All notes individually accessible, one note per browsing leaf, strictly smaller note sets on downward edges |

The selected notes cover rocket-stove cooking, lamb dinner, shrimp risotto,
cranberry sourdough, cast-iron cookware, chicken stock, preserved beets,
matcha-cashew pie, meal planning, beef stew, sourdough preparation and smoked
brisket. Their saved AS outputs are reused; meanings and comparisons use the
native runner and retain any exact answer reuse with its original receipt.

### Model execution and attempt allowance

| Parameter | Selected value |
| --- | --- |
| Provider | `openai-codex`, subscription |
| Model | `gpt-6.1-sol` |
| Reasoning effort | medium |
| Transport | SSE |
| Prompt cache | Enabled, with automatic warming |
| Shared provider queue | Maximum 30 requests across experiments |
| Bootstrap timeout | 600 seconds |
| Compare/consolidation timeout | 1,800 seconds |
| Output-token limit | No explicit limit |
| Seed / temperature | Unspecified; no overrides |
| Persistent attempt ceiling | 500 total, including warmups, retries and every resume |

The exact Bootstrap, Compare and consolidation settings are saved alongside the
run definition. The same persistent allowance is used throughout. Reaching its
ceiling preserves partial work and reports unfinished construction.

### Git provenance and retained artifacts

| Generation provenance | Recorded value |
| --- | --- |
| Oracle generation commit | `17ea0b74959106090de110d2971e6797eff73c11` |
| Shared-runner generation commit | `e19592f9a6b0b3a2b3ac0bc63220156d86a0f1a7` |
| Uncommitted source changes at generation | None in either isolated worktree |

The [frozen preparation record](../../../oracle-mvp-hierarchy-hr04-twelve-note-v1/target/hierarchy-hr04-twelve-note-v1/prepared-provenance.json)
contains the commits, selected note IDs, complete settings, frozen constructor
hashes and initial native plan bindings. Later documentation commits do not
change these generation commits. Resume from the retained task worktree with
the same attempt-budget path; its frozen source remains unchanged.

The run worktree is `oracle-mvp-hierarchy-hr04-twelve-note-v1`; artifacts remain
under `target/hierarchy-hr04-twelve-note-v1/`. Its saved AS corpus SHA-256 is
`18370b4772fee22c8d11f49a505f20f781f163e0512a8f32473d487ebdc8849a`, identical to
HR03's bound subject corpus. The prepared definition separately binds the exact
12-note selection. Preserve the raw graph, menu, execution summary, attempt
ledger, native receipts and source provenance there. The final graph and menu
are copied into `final/` and bound by immutable output hashes in the official
register. Retain both the Oracle and runner worktrees for native frozen paths.

| Saved artifact | File |
| --- | --- |
| Raw hierarchy | [HR04 raw state](../../target/hierarchy-catalogue/outputs/HR04.json) |
| Browsing menu | [HR04 menu](../../target/hierarchy-catalogue/outputs/HR04-related-1.json) |
| Complete parameters and evidence | [HR04 record](../../target/hierarchy-catalogue/records/HR04.json) |
| Structural audit | [Saved audit](../../../oracle-mvp-hierarchy-hr04-twelve-note-v1/target/hierarchy-hr04-twelve-note-v1/final/audit.json) |
| Native usage and allowance reconciliation | [Saved usage](../../../oracle-mvp-hierarchy-hr04-twelve-note-v1/target/hierarchy-hr04-twelve-note-v1/final/usage.json) |
| Final source and output provenance | [Saved provenance](../../../oracle-mvp-hierarchy-hr04-twelve-note-v1/target/hierarchy-hr04-twelve-note-v1/final/code-provenance.json) |
| Exact generator source snapshots | [43-file source archive](../../../oracle-mvp-hierarchy-hr04-twelve-note-v1/target/hierarchy-hr04-twelve-note-v1/code-snapshot/manifest.json) |

### SHA-256 bindings

| Input, source or output | SHA-256 |
| --- | --- |
| Run definition and note order | `a83792329bcd13ca6598ad32c0144bba6c915baa634254cc392659642c1848ad` |
| Bootstrap-v109 prompt | `caa77221193ce816c6112ea20ea81fcf4bf4739994fa06102e4b41f132128cd1` |
| Compare-v179 prompt | `49d936bd6d5e251bcc1317f34a87fd71c25eb1e63f972e5ec8824b81f73eb9ed` |
| Consolidation-v4 prompt | `144e23d89c65910f0851d4163ac7dff1baee248ebf5dab5c8779c843f9aae7c6` |
| Bootstrap response schema | `5806c8c66ce8a8a9b13fb9f5ff6445eb79bb918cf15925a17fd9354a1877809c` |
| Compare response schema | `9bdea40731448a9ef7b73372743cc258c5f6dc9419377c1d6c563d9dd12bc522` |
| Shared-runner fingerprint | `67a3688360b285fa4de34c08f2009df12708246143163e7a35d7ea04301cc0b8` |
| Request-code fingerprint | `15429b548cf904622a33bdad86c20d523da097c1956cc736ebbb2a513ded9018` |
| Source archive manifest | `182ed08a12b76ac6dcb5e8ebcbfc113e938b14a8851aec0fb86f76cdc9790099` |
| Raw hierarchy | `f482553bd90d76b9b4eeac77ec0662419dd3387465d1dbc67d046c034cce19b7` |
| Browsing menu | `86bd1e43fe30aafbbfdb1c1f0b87f9bebe7b6cd81f6f608c5524d6a2cc95599a` |

## HR03 — ASv6.100 50-note hierarchy

Generated October 10, 2026, using Bootstrap-v96 and Compare-v48. The latest
saved execution start is `2026-10-10T19:29:26.716124Z`.

### Inputs and construction

| Parameter | Recorded value |
| --- | --- |
| Notes | 50 |
| Note selection | [Frozen 50-note subject-generation specification](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/sse_multivector/shr_single_pair/hierarchy-as100-fifty-note-subjects-v1.spec.json) |
| Initial construction | [20 local roots from 20 notes](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/sse_multivector/shr_single_pair/hierarchy-as100-fifty-note-prefix-v1.json), before extending to the selected 50 notes |
| Subject prompt | [ASv6.100, frozen run template](../../target/hierarchy-catalogue/code/0e3fdfb713128233ba65070c0092914a38b0059a2eb5e873c0d828add1c5d52f.txt) |
| Subject entries | 1,510 |
| Bootstrap prompt | [Hierarchy-bootstrap-v96, frozen run copy](../../target/hierarchy-catalogue/code/599e811307cfd3feac290ec91b0c763f1900cc244fccc4756d8255027a050845.md) |
| Compare prompt | [Hierarchy-compare-v48, frozen run copy](../../target/hierarchy-catalogue/code/b225da8653af04dfbe41fc8ff9e4f9d8bf780df527e27ee3e2d088c0e7eb23af.md) |
| Comparison policy | guarded16 |
| Comparison limit | 16 |
| Local candidate limit | 32 |
| Maximum entries | 200 |
| Maximum choices setting | 6 |
| Independent meanings | true |
| Local schema version | 4 |

### Model execution

These are the saved settings, including the historical concurrency of 32.

| Parameter | Recorded value |
| --- | --- |
| Provider | `openai-codex` |
| Model | `gpt-6.1-sol` |
| Reasoning effort | medium |
| Transport | SSE |
| Prepared concurrency | 32 |
| Execution concurrency | 32 |
| Prompt cache | enabled in the frozen Bootstrap/Compare specifications |
| Warm cache | true |
| Subject-generation timeout | 1,800 seconds |
| Bootstrap/Compare timeout | 600 seconds |
| Output-token limit | No explicit limit; `null` in saved manifests |
| Seed | Unknown; not recorded |
| Temperature | Unknown; not recorded |

### Subject vectors

| Parameter | Recorded value |
| --- | --- |
| Model | `sentence-transformers/sentence-t5-base` |
| Device | CPU |
| Note batch size | 8 |
| Unique subject texts | 693 |
| Dimensions | 768 |
| Maximum length | 512 |
| Pooling | `selected-contextual-token-mean-linear-relu-linear-v1` |
| Python | `3.13.12` |
| PyTorch | `2.13.0+cpu` |
| Transformers | `4.57.1` |
| Tokenizers | `0.22.2` |

### Browsing menu

The run uses the saved
[shape-v2 recipe](../../sse_multivector/shr_single_pair/hierarchy-as100-fifty-note-shape-v2.json)
to select roots and child links from the raw hierarchy. The maximum-choices
setting was 6; the resulting menu has 7 roots, with 13 choices under Food.
The saved recipe and assessment retain those actual choices.

### Generator code and Git commits

| Code provenance | Recorded value |
| --- | --- |
| Oracle generation commit | Unknown; not recorded |
| Shared-runner generation commit | Unknown; not recorded |
| Uncommitted source changes at generation | Unknown; not recorded |
| Preserved Oracle source commit | `7f0a54b9e2fc9dcd47e62b7da0ac901056087904` |
| Preserved shared-runner source commit | `e27660d98798facf959d4661000b885e2dcd298f` |

The preserved Oracle commit was made after generation. Its source matches all
53 recorded project Python files. The preserved runner commit matches eight
recorded Python files and the saved seven-file runner fingerprint. These checks
identify matching source; they do not recover the execution-time Git HEAD or
uncommitted changes. Exact source-file snapshots and their hashes are listed in
the [complete HR03 record](../../target/hierarchy-catalogue/records/HR03.json).

### Outputs and complete evidence

| Output | Saved file |
| --- | --- |
| Raw hierarchy (`regrouping-roots-v1`) | [HR03 raw state](../../target/hierarchy-catalogue/outputs/HR03.json) |
| Browsing menu (`menu-v2`) | [HR03 menu](../../target/hierarchy-catalogue/outputs/HR03-related-1.json) |
| Browser export (`review-ui-v1`) | [HR03 browser export](../../target/hierarchy-catalogue/outputs/HR03-related-2.json) |

The [complete HR03 record](../../target/hierarchy-catalogue/records/HR03.json)
contains the frozen construction settings, response schemas, source bindings,
menu recipe and references to saved parameter evidence. The original native
[plan and code hashes](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/regrouping-roots-v1/step-123/experiment/experiment.json)
and [execution settings](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/regrouping-roots-v1/step-123/experiment/execution-settings.jsonl)
remain available. Unrecorded historical settings stay unknown.

### SHA-256 bindings

| Input, source or output | SHA-256 |
| --- | --- |
| Source corpus | `581e465d9a4c3ac5e6e2067a2edb9e9711acb3fd68982909394c9c704151dbf3` |
| 50-note selection specification | `452add80668e785462e01c8a8840e2547108e47212d2d33d344d549639a5ac99` |
| Initial 20-root construction definition | `3e3922c1c9dc9c5356fbff871d7ed0695f8c7caaa9eed0521483a54adb03d54b` |
| Subjects | `18370b4772fee22c8d11f49a505f20f781f163e0512a8f32473d487ebdc8849a` |
| ASv6.100 template | `0e3fdfb713128233ba65070c0092914a38b0059a2eb5e873c0d828add1c5d52f` |
| Bootstrap-v96 prompt | `599e811307cfd3feac290ec91b0c763f1900cc244fccc4756d8255027a050845` |
| Compare-v48 prompt | `b225da8653af04dfbe41fc8ff9e4f9d8bf780df527e27ee3e2d088c0e7eb23af` |
| Subject-vector checkpoint | `ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d` |
| Subject-vector model tree | `bba50abbbb7de6165ee3828c4e4abb0c88a6386bd4754374469246cde5017e5d` |
| Subject-vector container image | `a6c9674dca720e1f094b7feeb1397b6e6b0a97e10f13e0a6555deebf4b70ddaa` |
| Subject-vector worker source | `eccf48810ca4f43724f7e197d71c25e456d62ed510ba13f8cf40e90127a580fc` |
| Subject-vector receipt | `c35d1d37279c164a4e628be9c12e769667b8b3a8166be7ee686a2726881b80a1` |
| Subject-vector data | `d2012833be298658fe6686c8e9ea3233279d806a5d4061be7071059da0f7d429` |
| Menu recipe | `bd576d8e2617940bb7dfb9bb37ce5692654bcc8e2dee4c7d53cbdd256a5dacfe` |
| Shared-runner fingerprint | `5fa694dce385a2579286bae5a637625bfe14818ca6511de8cbec014724c44888` |
| Raw hierarchy | `853343330cac7db7c2cc9c5a2a333b590c05ca79c8563df0b7261850789a3aae` |
| Browsing menu | `4fd0a99ed797b57f94a79d8c1c90ba5d81df72de071bec73d1372a0922e1dc8c` |
| Browser export | `763ddd9c614581529653dcd1dcd342a3145ccd9beb9f194655448ee5f4f69060` |

## HR07 — ASv6.48 50-note hierarchy

Generated and reviewed October 10, 2026, before HR03. The user reviewed the saved
menu and said "wow, this hierarchy is great." This is the earlier ASv6.48 build,
with different subject outputs from HR03 despite identical Bootstrap-v96 and
Compare-v48 prompt bytes. **ASv6.48-derived data is deprecated; this entry is
historical comparison evidence.**

### Inputs and construction

| Parameter | Recorded value |
| --- | --- |
| Notes | 50; previous 16 original root pointers, then the first 34 unseen note IDs in saved corpus order |
| Exact selection | [50-note root definition](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/sse_multivector/shr_single_pair/hierarchy-fifty-note-b96-c48-roots-v1.json) |
| Subject prompt | ASv6.48; reuse saved `sh200-generation-v1` outputs |
| Subject entries / local roots | 1,346 / 315 |
| Bootstrap | [Hierarchy-bootstrap-v96](../../target/hierarchy-catalogue/code/599e811307cfd3feac290ec91b0c763f1900cc244fccc4756d8255027a050845.md) |
| Compare | [Hierarchy-compare-v48](../../target/hierarchy-catalogue/code/b225da8653af04dfbe41fc8ff9e4f9d8bf780df527e27ee3e2d088c0e7eb23af.md) |
| Initial graph | Empty; earlier 16-note graph not inherited |
| Meanings / local schema | Independent fixed meanings / version 4 |
| Root producers / placements | 50 root meanings generated together, then sequential placement with exact reuse |
| Comparison selection | `guarded16`, limit 16, with complete omitted-implication verification |
| Local candidate limit | 32 |
| Selective entry bound | 160 for the selective stage; later authorized growth brought total processed entries to 181 |
| Choice limit | 6 roots or children in the finished menu |
| Construction definitions | [Selection settings](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/sse_multivector/shr_single_pair/hierarchy-fifty-note-b96-c48-selection-v1.json); per-phase settings and caps retained in the complete record |
| Menu recipe | [Shape-v2](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/sse_multivector/shr_single_pair/hierarchy-fifty-note-b96-c48-shape-v2.json); preserve fixed meanings and witnessed ancestry |

### Model execution and attempt allowance

| Parameter | Recorded value |
| --- | --- |
| Provider / model / effort | `openai-codex` subscription / `gpt-6.1-sol` / medium |
| Transport | SSE |
| Prepared concurrency | 32 |
| Actual execution concurrency | 32 for 180 Bootstrap and 186 Compare batches; 8 for 13 Bootstrap batches |
| Prompt cache | Enabled; automatic static-prefix warming |
| Cache prefix | Template; `o200k_base` tokenizer; minimum 1,024 tokens |
| Bootstrap / Compare timeout | 600 seconds |
| Output-token limit | No explicit limit |
| Seed / temperature | Unknown; not recorded |
| Shared attempt allowance | 20,000 for the existing sprint, including warmups, failures, retries and continuations; not reset for this run |
| Historical shared-counter endpoints | 3,594 before; 6,679 after; later work is outside this run's usage |

### Result and review

| Measurement | Saved result |
| --- | --- |
| Raw graph | 146 nodes, 158 edges, 20 roots, maximum 24 children |
| Original entries processed | 181: 146 additions, 16 equivalences, 19 holds; 14 holds concern relationship contradictions |
| Reviewed menu | 76 nodes, 87 strictly narrowing edges, 6 roots, maximum 6 children |
| Individual note access | 50 of 50; 15 notes need 2 topic choices, 30 need 3, 5 need 4; mean 2.8 |
| Structural audit | Passed; no violations; semantic grading remains separate |
| Provider attempts | 3,085: 204 warmups and 2,881 ordinary attempts |
| Model answers / reuse | 3,075 valid case occurrences, including 201 exact reuses; no terminal failures or unrun cases |
| Recovered failures | 7, each missing usage/cost |
| Known API-equivalent cost subtotal | $9.1301216; full cost unknown; not a subscription charge |
| Unused valid prefetched receipts | 35; charged producer work remains included in usage |

The positive user review accepts the displayed menu, not every raw relationship.
Food exposes 24 of its 34 raw-graph notes; the other 10 remain reachable elsewhere.
The original judgments and holds are preserved. The audit's `done` remains false
because it does not grade semantic completion. The old native cost-statistics
section reports zero warmups; exact receipt-line verification establishes the
204/2,881 breakdown above without rewriting that original report.

### Git provenance and saved outputs

| Provenance | Recorded value |
| --- | --- |
| Oracle / shared-runner generation commits | Unknown; not recorded |
| Uncommitted source changes at generation | Unknown; not recorded |
| Source-preparation commit | `839d62d8ad935dc2ef6554c2e37ac9029abe3df6`; preparation/support, not a recorded execution HEAD |
| Bootstrap prompt source commit | `f098d3afc6e0d274dfae95276c466562e54bbcbe`; prompt definition only |
| Compare prompt source commit | `15ddf7df062da98105f71849af25f3d31c63eed5`; prompt definition only |

Generator files are preserved only when their bytes match native saved hashes.
The [complete HR07 record](../../target/hierarchy-catalogue/records/HR07.json)
contains the exact source snapshots, all construction-stage caps, model settings,
native receipts and input bindings. Some source paths now contain newer code;
their recovered historical snapshots retain the recorded bytes. The separate
[catalogue provenance](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-b96-c48-fifty-note-v1/menu-access-children-01/code-provenance.json)
was added after generation and does not replace original receipts or outputs.

| Saved artifact | File |
| --- | --- |
| Raw hierarchy | [HR07 raw state](../../target/hierarchy-catalogue/outputs/HR07.json) |
| User-reviewed menu | [HR07 menu](../../target/hierarchy-catalogue/outputs/HR07-related-1.json) |
| Original review UI export | [HR07 viewer hierarchy](../../target/hierarchy-catalogue/outputs/HR07-related-2.json) |
| Native usage | [Original usage](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-b96-c48-fifty-note-v1/fifty-note-final-usage-v1.json) |
| Structural audit | [Original audit](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-b96-c48-fifty-note-v1/finished-menu-v2/audit.json) |
| Review and qualifications | [Original findings](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/sse_multivector/shr_single_pair/hierarchy-fifty-note-b96-c48-findings.md) |

## HR06 — ASv6.48 8-note hierarchy

Generated and reviewed October 9, 2026. The user reviewed the saved menu and said
"LGTM. Now do 16 notes". HR06 records that accepted eight-note output and its
three-note base. The later 16-note extension has no separate official ID.
**ASv6.48-derived data is deprecated; this entry is historical comparison evidence.**

### Inputs and construction

| Parameter | Recorded value |
| --- | --- |
| Notes | 8; retain the original 3 notes, then add the 5 roots in the saved growth definition |
| Exact selection | [Eight-note growth definition](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/sse_multivector/shr_single_pair/hierarchy-eight-note-v88-growth-v1.json) |
| Subject prompt / entries | Reuse saved ASv6.48 outputs / 323 entries |
| Bootstrap | [Hierarchy-bootstrap-v88](../../target/hierarchy-catalogue/code/aa65ea9139e599fcdda89dc23741c3cd2f856cf42e59d51e6f68957e5526d0e0.md) |
| Compare | [Hierarchy-compare-v36](../../target/hierarchy-catalogue/code/10ba4da63ff9afd11eb996d58cf719381c9e61f6cb2df31e928778fadc081ee9.md) |
| Initial graph | 9 entries from the empty-start three-note build; add 5 original roots and 4 selected entries |
| Meanings / local schema | Independent fixed meanings / version 4 |
| Comparison selection | `guarded16`, limit 16; complete omitted-implication and settled-relationship checks |
| Same-note comparisons | Excluded except mapped-parent implication checks |
| Local candidate / selective entry limit | 32 / 32 |
| Choice limit | 6 roots or children in the finished menu |
| Selective settings | [Original selection](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/sse_multivector/shr_single_pair/hierarchy-three-note-v88-selection-v1.json) |
| Menu recipe | [Eight-note shape](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/sse_multivector/shr_single_pair/hierarchy-eight-note-v88-shape-v1.json) |

### Model execution and attempt allowance

| Parameter | Recorded value |
| --- | --- |
| Provider / model / effort | `openai-codex` subscription / `gpt-6.1-sol` / medium |
| Transport | SSE |
| Prepared / actual concurrency | 32 / 32 |
| Bootstrap / Compare timeout | 600 seconds |
| Output-token limit | No explicit limit |
| Seed / temperature | Unknown; not recorded |
| Prompt cache | No explicit setting in saved plans; zero warmups and reported cache reads/writes |
| Shared attempt allowance | 20,000 for the existing sprint; inherited shared counter, not an independent allowance |
| Saved shared-counter endpoint | 1,735 used; 18,265 remaining; includes unrelated earlier sprint work |
| Base phase attempt caps | 30 per roots/selective phase; 40 for the two dinner-child additions |
| Eight-note extension caps | 150 for the five new roots; 50 for each of four selected additions |

### Result and review

| Measurement | Saved result |
| --- | --- |
| Raw graph | 17 nodes, 16 edges, 4 roots |
| Original entries processed | 18: 17 additions, one equivalence, zero holds |
| User-reviewed menu | 13 nodes, 9 strictly narrowing edges, 6 roots, maximum 5 children |
| Individual note access | 8 of 8; 3 notes need 1 topic choice, 5 need 2 |
| Structural audit | Passed; no violations; no omitted-node verification phase was needed |
| Full three-to-eight-note lineage | 153 new attempts and 7 exact reuses; 160 valid case occurrences |
| Eight-note extension alone | 118 new attempts and 2 exact reuses |
| Failures / retries / unrun cases | 0 / 0 / 0 |
| Newly dispatched API-equivalent cost | $0.907694 for the full lineage; $0.690570 for the extension |
| Generation cost including original reused producers | $1.008628; complete saved API estimate, not a subscription charge |

The original Cooking heat-boundary concern remains, along with Food and ingredient
scope-review candidates. The menu omits intermediates and an unresolved Food to
Cooking ingredients link while retaining their original raw judgments. Meals
and Food-storage shared views were not recovered. The user review accepts this
menu; the structural audit does not grade meanings, and its `done` remains false.

### Git provenance and saved outputs

| Provenance | Recorded value |
| --- | --- |
| Oracle / shared-runner generation commits | Unknown; not recorded |
| Uncommitted source changes at generation | Unknown; not recorded |
| Matching three-note source commit | `20c87769661c9910979a87c4598187e17ea3a500`; all 53 recorded Oracle Python files match |
| Matching eight-note source commit | `8a08529c22c96856e7e4343874101e7e608d63c0`; all 53 recorded Oracle Python files match |
| Matching runner source commit | `c3742c8e488a2154bbde7748813d9ce68c649cda`; all 8 recorded runner Python files match |

These matching commits identify preserved file contents, not the execution-time
Git HEAD or dirty state. The [complete HR06 record](../../target/hierarchy-catalogue/records/HR06.json)
contains exact generator snapshots, native plans, phase caps and receipts. The
separate [catalogue provenance](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-v88-eight-note-v1/selection-04/code-provenance.json)
was added after generation; original artifacts remain unchanged.

| Saved artifact | File |
| --- | --- |
| Raw hierarchy | [HR06 raw state](../../target/hierarchy-catalogue/outputs/HR06.json) |
| User-reviewed menu | [HR06 menu](../../target/hierarchy-catalogue/outputs/HR06-related-1.json) |
| Original review UI export | [HR06 viewer hierarchy](../../target/hierarchy-catalogue/outputs/HR06-related-2.json) |
| Native usage | [Original usage](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-v88-eight-note-v1/usage.json) |
| Structural audit | [Original audit](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-v88-eight-note-v1/menu/audit.json) |
| Human review and qualifications | [Original record](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/sse_multivector/shr_single_pair/README.md#bootstrap-v88-eight-note-construction-user-reviewed-menu) |

### Shared historical inputs for HR06 and HR07

Both runs reused subject outputs and standalone subject vectors from the same
saved 200-note corpus; neither reran subject extraction or vector encoding.

| Input parameter | Recorded value |
| --- | --- |
| Original subject producer | ASv6.48, `openai-codex`, `gpt-6.1-sol`, medium |
| Original AS transport / concurrency / timeout | Websocket / 16 / 1,800 seconds |
| Subject-vector model / device | `sentence-transformers/sentence-t5-base` / CPU |
| Vector scope | Saved 200-note probe; 4,370 unique headings |
| Note batch size / dimensions / maximum length | 8 / 768 / 512 |
| Encoding / pooling | Standalone full subject wording / `selected-contextual-token-mean-linear-relu-linear-v1` |
| Python / PyTorch / Transformers / Tokenizers | 3.13.12 / 2.13.0+cpu / 4.57.1 / 0.22.2 |
| Vector receipt and runtime bindings | [Original worker receipt](../../../oracle-mvp-scalable-hierarchy-v12/target/sh200-generation-v1/subject-vectors/worker-result/worker-receipt.json) |

| Shared input or runtime binding | SHA-256 |
| --- | --- |
| Saved subjects | `1f87b7c853beef38d2701f6cef6a3fc4957a93c547f34f7f80caa6919e6d0a07` |
| Original ASv6.48 template | `5329a4dbbd9787803bfc6dcd8020a720caaa156f36548a9cdff85ee29288d4ff` |
| Subject-vector checkpoint | `ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d` |
| Subject-vector model tree | `bba50abbbb7de6165ee3828c4e4abb0c88a6386bd4754374469246cde5017e5d` |
| Vector container image | `a6c9674dca720e1f094b7feeb1397b6e6b0a97e10f13e0a6555deebf4b70ddaa` |
| Vector worker | `4e1446e3f48f2989a4b441994b81cf05d409d4b196e7d55155f9202e2b6b4f53` |
| Saved vector data | `66f59bcfc065eae45c80db02b7104b5a697abf7dea04ffdab44904317196b402` |
| Hierarchy runner fingerprint | `3e246132e01f45d06c61cc55e048b4ad3d390feee826e2550068956a2bc7bcf9` |

| Run output | SHA-256 |
| --- | --- |
| HR06 raw hierarchy | `a8a508e4282169dbc9ffc8615bfb647115f6c4671408e60edd3006a13f18a547` |
| HR06 reviewed menu | `c71e24ac3fe4c088a9ea9a3da809dc989a8e592e13a7a90ae1ca3f5febc2ee54` |
| HR06 original UI export | `8d9707570f93d2d959e3e3eb1e6bce83fbfc24f38da5b314e7bbb9b4b0e1db92` |
| HR07 raw hierarchy | `fd3e5b8e3831a7952dc66de0686a1383c3fb1e9ff07dcbbc1fdb275740cc22f8` |
| HR07 reviewed menu | `3d90dde150b2028e4f86b8a288ef2c8caa4f267e0a40e8e24e47dd400932a731` |
| HR07 original UI export | `6cec4a3ef21287260aed1ad0625045528ae17355291c21f2b72a5fc14c8678cd` |

## Registering future runs

Register a run only when the human explicitly designates it as official.
Completing a diagnostic, approving its execution or generating a browsing output
does not make it official. Checkpoints and derived outputs remain attached to
their run; they do not receive separate run IDs. The previous `H0001`–`H0701`
diagnostic inventory is withdrawn, and those IDs must not be reused.

The [catalogue source](../../sse_multivector/hierarchy-catalogue-source-v1.json)
contains the explicit `official_runs` list. Each entry records `version_id`,
`name`, `root`, `artifact_path` and `sha256`, with optional `related_outputs` for
the run's other saved outputs. The
[version registry](../../sse_multivector/hierarchy-versions.json) binds the ID to
its preserved output and parameter evidence. The existing-run cutoff remains
October 8, 2026 at midnight America/New_York (`2026-10-08T04:00:00Z`). Older bound
inputs remain provenance.

Keep this Markdown register and the explicit source list synchronized when
registering an official run. Before a new run, record the full commits of Oracle
and the shared runner, plus any uncommitted source changes, alongside their
frozen code hashes. Generator source is accepted only when its bytes match a
saved hash. An exact Git blob identifies file contents, not the run's overall
commit.

Regenerate the catalogue after updating the explicit official-run list, from a
task worktree:

```bash
/home/dev/src/notedeck_worktrees/algos/experiment-runner/bin/experiment-runner \
  --project-root "$PWD" catalogue-hierarchies \
  --source sse_multivector/hierarchy-catalogue-source-v1.json \
  --registry sse_multivector/hierarchy-versions.json \
  --output /home/dev/src/notedeck_worktrees/algos/oracle-mvp/target/hierarchy-catalogue
```

This offline command makes no model calls and preserves original experiments.
Use `--saved-only` to regenerate from retained records. Generated pages, parameter
evidence and output snapshots stay ignored under `target/`; preserve them with
the original runs. The registry alone is not a backup. Experiment preparation,
execution and resumption still use task worktrees and the shared launcher.
The [HTML viewer](../../target/hierarchy-catalogue/index.html) also supports
side-by-side comparison of official runs.
