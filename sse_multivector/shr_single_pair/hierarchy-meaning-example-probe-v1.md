# Meaning example probe v1 — experimental diagnostic

Status: controlled HR38 diagnostic completed; no production change.
This is a local frozen-SSE diagnostic, not a new hierarchy/admission policy,
meaning rewrite or prompt experiment. The selected group and outsiders stay fixed.

Compare three views of each original meaning in a saved reference group:

1. Pool the entire meaning in its original `title + "\n\n" + meaning` context.
2. Pool only the prefix preceding the exact `, including but not limited to `
   suffix, leaving that suffix in the encoder context.
3. Pool that identical prefix in a context with the suffix removed.

Meanings without that explicit optional suffix are unchanged controls. Other
forms of inclusion are not shortened. Original meanings, IDs, note identities,
accepted memberships and historical vectors are preserved. This narrow text
operation is a diagnostic intervention, not a generally valid meaning-cleaning
rule. It does not remove purposes, states, restrictive clauses or alternatives.

[meaning_example_probe.py](../meaning_example_probe.py) reads the saved group
and source plan directly, deduplicates exact context/span requests, pins source
hashes, and prepares the existing native
[worker.py](../worker.py). It adds no inference implementation or provider path.
The worker retains the source model descriptor, checkpoint, base artifact,
contextual pooling, dimensions, device and batching. Collection validates the
native receipt, raw vector hash, source identities and row bindings, then saves
three normalized arrays with the original group-member order. Changed sources
or incompatible existing results fail rather than silently overwriting evidence.

The adapter's `prepare` command takes a completed study, a new output directory,
and saved root/group IDs. Run its generated config through the existing native
SSE worker in the pinned CPU environment; `collect` validates and saves paired
views. No teacher calls or provider execution path is added. Experiments remain
in an isolated task worktree with generated evidence ignored.

Use original full-meaning replay to validate numerical compatibility before
interpreting differences. Hold groups, outsider meanings, semantic review labels
and the admission algorithm fixed when inspecting scores and consistently
recomputed boundaries. This is a post-result mechanism test using already
reviewed HR38 cases, not another held-out accuracy estimate. No LLMs, training,
paid resources, hierarchy changes or prompt changes are involved.

## Controlled HR38 result

Use C00006's saved fused-002 group: 15 People entries and one Individuals entry,
all from distinct notes. Thirteen meanings contain the exact explicit optional
suffix; three are unchanged controls. The adapter requests 19 distinct contexts
and 32 distinct context/span views. Original full-meaning vectors replay within
`1.39e-17` normalized absolute error and `4.44e-16` cosine error. The worker,
checkpoint, base artifacts, packages, 768 dimensions, 512-token maximum and
batch size 32 match the earlier study. Native receipts confirm identical
selected prefix token IDs in both contexts for all 16 records; tokenization
differences do not explain their context comparison.

Keep all seven existing reference groups, their 69 original meanings/memberships
and all 2,127 outsider meaning vectors fixed. Replace only the affected 13
reference vectors in each experimental condition. Consistently recompute
reference support and the **same** admission rule for each condition. No fusion
network is rebuilt, and no new semantic label or parameter is selected.

### Where the representation changes

| Reference view | Median within-group cosine | Group median support | Final group threshold |
|---|---:|---:|---:|
| Full original meaning | 0.2839 | 0.03335 | 0.01153 |
| Definition prefix pooled; examples remain in context | 0.9480 | 0.74144 | 0.39550 |
| Same prefix pooled; examples removed from context | 0.9505 | 0.78535 | 0.59953 |

Pooling the explicit optional example words causes most of this loss of
within-group agreement. The prefix has much greater agreement while the entire
original context is still present. Removing the suffix from context increases
median agreement only another 0.0025. For the 13 changed meanings, the median
cosine between the two prefix vectors is 0.9834 (range 0.9629–0.9905). Context
still has an effect; the result does not establish that context is irrelevant
or that every example in every topic should be removed.

### Admission remains unresolved

Freeze 22 previously reviewed HR38 controls before new encoding: seven useful
witnesses, 11 wrong root placements and four unresolved cases. Six useful
witnesses are actual classes of people; the seventh is patient advocacy with an
accepted humane-treatment witness. The labels remain provisional prior agent
judgments. They do not enter scoring or boundary calculation, and this
purposive panel is a mechanism diagnostic, not a held-out precision estimate.

| Reference view, same boundary algorithm recalculated | Useful witnesses admitted | Wrong cases admitted | Unresolved cases proposed | All outsider notes proposed |
|---|---:|---:|---:|---:|
| Full original meaning | 3/7 | 11/11 | 4/4 | 203 |
| Prefix pooled in original context | 0/7 | 0/11 | 1/4 | 27 |
| Prefix pooled in shortened context | 0/7 | 0/11 | 1/4 | 17 |

Four of the seven useful witnesses were already omitted by the baseline; the
alternatives additionally lose its three surviving useful witnesses. Existing
memberships are never removed. The 27 and 17 surviving outsider-note proposals
have not received a new semantic audit, so no improved precision is claimed.

Holding every original threshold fixed instead isolates the changed query-to-
reference score: either prefix condition admits two of seven useful witnesses
and nine of 11 wrong cases. The broad removal of wrong proposals in the table
therefore depends mainly on the much higher recalculated boundary.

The outsider score has a separate problem. On the affected group, each of six
human-class witnesses is compared with each of the 11 reviewed wrong cases.
The useful entry scores higher in **14/66** such comparisons originally, and
**6/66** in either prefix condition. These are overlapping diagnostic pair
comparisons, not independent accuracy samples or thresholds fitted from labels.
Wrong activities can still score above real people topics such as racing
drivers, astronauts and Australians. Better agreement among near-equivalent
People definitions does not establish useful separation for narrower topics.

This test establishes a concrete pooling effect and preserves the original
conservative candidate. It does **not** qualify either prefix condition as an
admission improvement. Before changing the boundary again, the most useful next
check is whether the already-saved contextual-title vectors rank these actual
people topics ahead of the same wrong activities. The subsequent
[saved-title comparison](hierarchy-hr38-title-meaning-score-v1.md) is now complete:
ordering improves from 14/66 to 24/66, while the same Audience reactions entry
still exceeds all six useful people topics in both views. No score combination,
boundary or admission policy is introduced.

## Evidence and verification

Local evidence directory: `target/food-halves-v1/hr38-meaning-examples-v1/`.

- Inputs SHA256:
  `83678a08ac49776bdb99528ace124e44832a91f838039fa389963f65521ba75e`.
- Analysis plan SHA256, frozen before new vectors:
  `7b83f9c7d31c08920d851f588f88c103614a2eca35515027738c5e667287391a`.
- `inputs.json` retains full original meanings, exact removed suffixes, UTF-8
  spans and all three view bindings. Native request/config/receipt and raw
  vectors are preserved. No original meaning was edited.
- `results.json`, `control-results.json`, all query/group NPZ files and the three
  reference models retain complete outcomes and consistently recalculated
  member boundaries. `ordering-diagnostic.json` saves every control score and
  `context-effect.json` saves each paired prefix-vector comparison.
- All 42 preparation source bindings and 15 analysis bindings remain unchanged.
  Full original admissions replay exactly. Independent scalar verification
  checks 183 member scores, selected outsider group means and all 21 group
  thresholds. Maximum score difference is `2.45e-15`; boundary error is zero.
- Failing-first preparation/collection tests exercise actual worker requests,
  UTF-8 spans, unchanged controls, real native receipt collection and changed-
  source rejection. All **102** relevant tests pass, including the native
  projection/pooling integration tests in the pinned Torch environment. Earlier
  dependency-only skips in the numerical environment are resolved by that run.
- No LLM calls, training, paid resources, membership changes, hierarchy changes,
  prompt changes or production admission changes occurred.
