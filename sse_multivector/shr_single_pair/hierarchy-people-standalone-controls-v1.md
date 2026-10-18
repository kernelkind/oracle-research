# People-class titles without context v1 — experimental findings

Removing context from the six useful people-class titles improves their ordering
against the saved standalone **reactions** control: three witnesses now score
higher, versus one before. Those three witnesses are only **two distinct
titles**, Celebrities and Spectators. Racing drivers, Astronauts and Australians
remain below reactions. Context removal has not established a separating score
or admission improvement.

This completes the bounded control proposed by the
[standalone reactions diagnostic](hierarchy-reactions-standalone-probe-v1.md).
No new semantic judgments, boundaries, admissions or hierarchy changes occur.

## Fixed experiment

Retain the same six previously reviewed useful witnesses, all seven C00006
reference groups and their 69 saved contextual-title vectors. The primary
fused-002 group remains 15 People entries and one Individuals entry.

Encode each original title by itself, pooling the entire text. The six source
records have five distinct titles because both Celebrities entries share the
same standalone input. The native worker encodes those five texts once in one
batch; collection maps the Celebrities vector to both original source records.
No contextual query or reference vector is regenerated. Reuse the previously
encoded lowercase **reactions** text without changing its vector.

Use the same source-note exclusion and mean of
`exp(-5.5 * (1 - cosine))` over references. Keep references contextual in both
conditions to isolate the useful query representation. These experimental
standalone titles are not MP masks, and no SP subject-vector artifact is
relabeled. Original titles, explicit meanings and note identities stay intact
in the evidence.

The existing [adapter](../title_selection_probe.py) supports
`prepare ... --whole-title --standalone`, deriving each input directly from
its source record. It retains the frozen worker/checkpoint/base-model identity,
768 dimensions, 512-token maximum, pooling/projection and batch size 32.
Its previous explicit-substring and contextual options retain their behavior.

## Actual scores

These are People-group mean-support scores, not cosines or probabilities.
The unchanged standalone reactions score is **0.012325**.

| Entry | Exact standalone text | Saved contextual-title score | Standalone score | Standalone above reactions? |
|---|---|---:|---:|---|
| L03026 | Celebrities | 0.010988 | 0.014403 | Yes |
| L03937 | Spectators | 0.051219 | 0.046687 | Yes |
| L05684 | Racing drivers | 0.009688 | 0.009910 | No |
| L07104 | Celebrities | 0.009467 | 0.014403 | Yes |
| L03337 | Astronauts | 0.010740 | 0.010081 | No |
| L07560 | Australians | 0.006748 | 0.011229 | No |

The comparison rises from 1/6 to 3/6 witnesses above reactions, or from 1/5 to
2/5 distinct titles. These are overlapping, previously selected diagnostic
controls, not independent accuracy samples. Both Celebrities rows now have an
identical score by construction; they do not count as independent confirmations.
Context removal helps some controls and slightly weakens others.

The negative is still the shortened text reactions, rather than the full
Audience reactions title. References remain contextual. This is not a complete
uniform standalone-title evaluation or evidence that discarding disambiguating
context is generally safe. Lower absolute scores do not themselves establish
correct rejection, and no threshold is fitted.

The user rejected the subsequent proposal to manually select defining words
such as people, impressions or responses. That proposal is closed without
preparation or encoding. The measured results above remain evidence, but this
word-selection detour supplies no automatic admission rule. Work returns to the
[cross-corpus conservative admission assessment](hierarchy-note-bend-admission-v1.md#current-practical-assessment-across-corpora),
without requiring perfect separation of the People cases. The existing
conservative admission candidate remains unchanged.

## Evidence and verification

Ignored artifacts remain at
`target/food-halves-v1/hr38-people-standalone-controls-v1/` through the existing
external-storage symlink. Retain the research worktree for frozen source and
artifact references.

- Plan frozen before the new vectors, SHA256:
  `9d3ff2d1751e31b0016fd24d8c94ce700b3e6d8a5bc7f9f04d1fb2ad08b1c9a2`.
  All 50 analysis source bindings remain unchanged. Historical adapter bytes
  are checked against commit `8a341482`; native historical receipts are intact.
- Native request has five unique contexts/rows and six provenance records.
  Independent checks reconstruct normalized vectors from raw bytes, check each
  exact source title and UTF-8 span, and verify both Celebrities bindings.
- All 828 query/reference cosines and 84 group means are checked with scalar
  arithmetic, with maximum error `2.78e-16`. The reactions reference score
  replays within `3.5e-18` using the identical saved vector. All seven group
  scores and raw pair cosines are retained, not only the reported People score.
- The new whole-title production-path test first failed on the missing input
  support. The implemented native preparation/collection path then passes:
  **17 native/adapter tests and 65 numerical tests**, with no skips, in the
  existing pinned Torch and NumPy/SciPy environments.
- No LLM calls, training, paid resources, policy activation, prompts, hierarchy
  changes, UI refresh or official HR construction.
