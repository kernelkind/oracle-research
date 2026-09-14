# TRUE04 — Containment across all generated HDBv2 titles

## Question

Does the unchanged TRUE03 setup make useful containment decisions across the complete set of 61 original HDBv2 group titles, rather than just the selected pilot pairs?

The user approved this expansion. Keep the exact v20/Astra-low titles, model, input wording, score calculation and **score > 0.142** rule. Do not generate titles, change memberships, construct a hierarchy, retune a cutoff or filter pairs by cosine.

## Inputs

Source: `../hdbv2-node-titles-v20-astra-low/titles.json`, SHA256 `424ffe683fe5fdb3de152cfc6fa09496dfef9fdef422e7a22618b28cc1e20716`.

Score all **3,660 ordered pairs** of distinct group IDs. The 61 groups have 58 distinct title strings; repeated Food, Coffee and Bitcoin titles remain separate source groups. Repeated strings are not independent evidence of semantic generalization.

For **A contains B?**, TRUE sees only:

```text
premise: This text is about {B}. hypothesis: This text is about {A}.
```

No masks, notes, expected answers, IDs or reviewer explanations enter the model. Its native answer and the cutoff decision are recorded separately. The score is the full-vocabulary probability of the first output token being `1`, not cosine or a calibrated probability of containment.

## Semantic review

Before inspecting scores, two clean-context reviewers consider all possible parents for disjoint halves of the child-title list. They nominate clear containments and scope-ambiguous relationships, with short reasons. The coordinating reviewer checks these nominations and freezes the resulting reference before inspecting predictions. Unlisted pairs are **not** silently labeled No.

This is a revisable semantic reference, not a prescribed unique hierarchy. Ordinary category meanings guide the judgments; merely related subjects need not contain one another. Do not reject reasonable emergent relationships because they were unexpected, or elevate niche counterexamples into decisive failures.

After inference:

1. Inspect every accepted relationship for valid containment, a clear wrong link, or genuine ambiguity.
2. Inspect missed relationships from the pre-score reference. Preserve disagreements with that reference explicitly.
3. Recheck the 44 TRUE03 directions as a repeat of known evidence, not independent validation.
4. Inspect reciprocal decisions and inconsistent chains. Do not consolidate reciprocal errors into equivalent categories or silently repair the output.

Report accepted-link quality and recovery of the clear reference separately. Do not present a high overall accuracy dominated by thousands of unrelated negative pairs. Show exact titles, model inputs, scores and semantic reasons for concrete problems. This test cannot establish title-to-mask fidelity, missing-parent generation or general performance outside this collection.

## Execution

One offline CPU process using the pinned `google/t5_xxl_true_nli_mixture` revision `aa6cfe1dd4257853bfdd772992045f41bfc14988`, float32, four threads and batch four. Keep the TRUE03 inference function unchanged. Extend reporting to accept unlabeled rows rather than fabricate an answer key.

Use the existing Python 3.11.14 runtime and cached packages/model; no paid calls, rentals, training or downloads. Require 70 GiB available memory before launch. Run under a 60 GiB memory limit, zero permitted swap and four-CPU quota. Do not stop unrelated processes. Save a new `TRUE04/` output, refusing overwrite; preserve all prior experiments.

Freeze source titles, all inputs, runner/scorer code and hashes before loading. Preserve native outputs, full first-token logits, scores, runtime/resource records and analysis. Independently verify inputs and replay scores from saved logits without a second model load. Full inference is expected to take substantially longer than the 44-question pilot.
