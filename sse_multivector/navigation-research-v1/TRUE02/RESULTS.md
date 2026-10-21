# TRUE02 — The fixed cutoff transferred well, but not perfectly

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

**The unchanged 0.142 cutoff answered 147/150 directional questions correctly.** It accepted all 45 valid relationships and rejected 102 of 105 invalid ones. All three mistakes put a bread variety under **Bread baking**, even though the variety's full subject also includes eating, taste, nutrition, storage, and other topics beyond baking.

These are new manually constructed descriptions, not actual generated HDBSCAN labels. The complete input set and judgments were reviewed before scoring. No scores, labels, wording, weights, or cutoff were adjusted after seeing results.

## What was tested

Thirty descriptions: six in each of food, software, economics, politics, and interpersonal relationships. Every distinct within-domain pair was checked in both directions: 75 pairs, 150 decisions. There were no easy between-domain negatives. None of these ordered category pairs occurred in TRUE01.

For **A contains B?**, TRUE received exactly:

```text
premise: This text is about {B}. hypothesis: This text is about {A}.
```

The score is the probability of first output token `1`, not cosine or a calibrated category-containment probability. The native answer is TRUE's complete generated `0` or `1`. The separately frozen rule accepts when the score is **greater than 0.142**.

| Decision rule | Valid relationships accepted | Invalid relationships rejected | Correct directions | Pairs with both directions correct |
|---|---:|---:|---:|---:|
| Native answer | 34/45 | 103/105 | 137/150 | 62/75 |
| Fixed cutoff, unchanged from the proposal after TRUE01 | 45/45 | 102/105 | 147/150 | 72/75 |

The cutoff recovered eleven missed valid relationships while adding one false relationship. It did not simply answer Yes to related categories: it rejected all 35 reversed strict-inclusion directions and 67/70 directions where neither category contains the other. All ten directions of the five equivalences were accepted.

| Area | Native correct | Cutoff correct |
|---|---:|---:|
| Food | 28/30 | 27/30 |
| Software | 25/30 | 30/30 |
| Economics | 27/30 | 30/30 |
| Politics | 28/30 | 30/30 |
| Interpersonal relationships | 29/30 | 30/30 |

## Every cutoff mistake

The question is whether **A contains B**, not whether the descriptions are related.

| ID | A | B | Expected | Native | Score | Cutoff |
|---|---|---|---|---|---:|---|
| F6-contains-F2 | Bread baking | Sourdough bread | No | Yes | 0.538085 | Yes |
| F6-contains-F4 | Bread baking | Gluten-free bread | No | No | 0.178456 | Yes |
| F6-contains-F5 | Bread baking | Bread made without gluten | No | Yes | 0.509176 | Yes |

For the first error, the complete model input was:

```text
premise: This text is about Sourdough bread. hypothesis: This text is about Bread baking.
```

Sourdough bread belongs under **Bread**; its entire category does not belong under **Bread baking**. A note about storing or eating sourdough need not concern baking. The same distinction applies to gluten-free bread. Those counterexamples were recorded in the blind review before inference.

F4 and F5 are equivalent descriptions, so the three errors represent two bread varieties and one recurring error pattern, not three independent failure mechanisms. Their scores also differ substantially (0.178456 versus 0.509176), changing the native answer despite the equivalent meaning. This is observed wording sensitivity; no alternative wording was selected afterward to improve the result.

The output is consistent with confusing a product's topic with its production process. This experiment does not isolate whether that comes from TRUE's learned associations, our topic wrapper, or another mechanism.

## Why a different universal cutoff cannot make this set perfect

Consider these two actual decisions:

| A contains B? | Expected | Score |
|---|---|---:|
| Software testing contains Security testing of web applications | Yes | 0.157464 |
| Bread baking contains Sourdough bread | No | 0.538085 |

A cutoff low enough to accept the valid software relationship also accepts the invalid bread relationship. A cutoff high enough to reject that bread relationship rejects the valid software relationship. This establishes a limitation of a single cutoff on these observations, **not** that the model is useless: the frozen cutoff still made only three errors.

Within each area's six categories, every valid relationship scored above every invalid relationship:

| Area | Lowest valid score | Highest invalid score |
|---|---:|---:|
| Food | 0.740384 | 0.538085 |
| Software | 0.157464 | 0.037221 |
| Economics | 0.193878 | 0.013346 |
| Politics | 0.292186 | 0.087392 |
| Interpersonal relationships | 0.466535 | 0.036581 |

Across all areas, 28 of the 4,725 valid-versus-invalid score comparisons have the invalid relationship higher. All 28 cross areas and involve one of the three bread errors; there are no ties. Every such comparison (`score-inversions.json`).

This matches the predeclared outcome in which ordering is clean within the sampled areas but not globally. It does **not** demonstrate stable domain-specific cutoffs: there is only one six-category collection per area, and error type, wording, and domain are confounded. No per-domain cutoffs were fitted.

## Examples where overlap was handled correctly

| Question | Expected | Score | Cutoff |
|---|---|---:|---|
| Bread contains Gluten-free food | No | 0.008023 | No |
| Gluten-free food contains Bread | No | 0.001926 | No |
| Testing web applications contains Software security testing | No | 0.016933 | No |
| Software security testing contains Testing web applications | No | 0.004838 | No |
| Friendship contains Workplace relationships | No | 0.001379 | No |
| Workplace relationships contains Friendship | No | 0.000820 | No |

These categories can share instances without containing each other. Their low scores provide direct evidence that the model is not merely reporting semantic similarity in this sample.

## Conclusion

TRUE plus our unchanged topic wording remains a promising candidate for description-based subsumption. The cutoff's success on genuinely new pairs is stronger evidence than its perfect fit to TRUE01, and the reverse/overlap results directly address the required distinction.

It is not a solved membership oracle. The universal score boundary is imperfect, equivalent wording can change scores, and this test does not establish performance on generated node descriptions or all topics. Nor does it validate complete hierarchy construction, equivalence consolidation, missing-parent generation, or navigation.

The 150 directions reuse just 30 descriptions in five tightly constructed collections, including explicit intersections and simple paraphrases. The 98% figure is descriptive of this test, not an estimated deployment accuracy. All expectations remain unchanged; disputes can be revisited openly without rewriting the saved answer key.

## Current research status — 2026-09-14

After the pause for node-description work, the user approved resuming TRUE tests on actual generated titles. The [TRUE03 pilot](../TRUE03/RESULTS.md) and completed [TRUE04 full-title test](../TRUE04/RESULTS.md) use unchanged v20/Astra-low titles and TRUE02's model, input wording and 0.142 cutoff. TRUE04 scored all 3,660 directions across 61 original groups. Semantic review judged 91 of 106 cutoff-accepted directions reasonable, 9 incorrect and 6 ambiguous; it also recorded missed relationships and false reciprocal containments. These results do not adopt TRUE as the final hierarchy system. The TRUE02 measurements and original judgments above remain unchanged.

## Complete evidence

- Every decision, exact descriptions, scores, and native errors (`03bd9e45:sse_multivector/navigation-research-v1/TRUE02/DECISIONS.md`).
- [All errors with explanations](ERRORS.md).
- Raw inputs (`inputs.json`), raw outputs and token IDs (`scores.jsonl`), raw analysis (`analysis.json`).
- [Frozen plan](RESULTS.md#true02-study-design), [pre-score independent review](../TRUE02-BLIND-REVIEW.md).
- [Execution and reproducibility](RESULTS.md#true02-runtime-and-verification), independent verification (`verification.json`).

TRUE01 and this run's frozen source snapshots remain unchanged. No hierarchy or cutoff adjustment was made in TRUE02. TRUE03 and TRUE04 have separate artifacts. The current runner shares the same inference implementation through a tested extraction; TRUE04 adds reporting for unlabeled rows without changing inference or inventing expected answers.

**Selected data:** Compact pair-score results, inputs and parameters for `TRUE02` are selected for release as `numerical/pair-scores-e0df9005e4fdba93` in the [publication catalog](../../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.

## TRUE02 study design

### Question

TRUE01's topic-sentence scores placed all valid relationships above all invalid relationships in ten constructed families. The gap was only 0.003920. Does this useful separation survive a different set with many closely related, overlapping categories?

This tests a proposed component, not an adopted hierarchy. No model training, HDBSCAN changes, category-generation changes, or graph construction are included.

### Frozen comparison

Keep TRUE01's released checkpoint, exact topic wrapper, tokenizer, float32 CPU inference, greedy generation, and score calculation unchanged. The only semantic input change is the category set. Bare titles are not retested.

For **A contains B?**, the model receives:

The model sees neither our expected answers nor our scope explanations. Our wrapper is an adaptation for topical containment, not an instruction prescribed by the TRUE paper.

Keep native Yes/No answers and the full score. Separately accept when the score is **strictly greater than 0.142**, the provisional cutoff proposed from TRUE01 before any TRUE02 score is observed. Do not change this cutoff after scoring. The score is the full-vocabulary probability of first output token `1`; it is not cosine or a calibrated probability of category containment.

### New examples and judgments

[Exact fixture](../true02-fixture.json): six categories in each of food, software, economics, politics, and interpersonal relationships. Test every distinct pair within each domain in both directions: **75 unordered pairs, 150 directional decisions**. Do not add easy unrelated cross-domain pairs to increase apparent accuracy.

The descriptions are manually constructed realistic categories, **not actual generated HDBSCAN labels**. This isolates the relationship scorer from label-generation quality. The domains recur from TRUE01; the category pairs are new. This is unseen-example transfer within familiar broad domains, not proof of transfer to all new domains or of an end-to-end hierarchy.

Expected-positive directions are explicitly listed; all remaining directions are expected No. Reciprocal positives represent equivalence. Scope explanations provide noncontainment counterexamples. A separate reviewer audits all unordered pairs without access to TRUE02 scores. Resolve or explicitly set aside genuinely ambiguous judgments before freezing the fixture, never by inspecting predictions.

This evaluation concerns topical containment. For example, bread baking is a narrower topic under bread, even though a process is not a physical loaf. If a disputed pair cannot sustain a clear topical judgment, it must not be presented as a definitive model error.

### Analysis fixed before scoring

1. Report correct/incorrect native decisions and decisions at 0.142, globally and per domain. Also report whether both directions of each pair are correct.
2. Report strict containment, equivalence, reverse containment, and noncontainment separately. Inspect all errors with both complete descriptions and scores.
3. Check whether any expected-negative score reaches or exceeds an expected-positive score, globally and within each domain. Preserve all such orderings. No new cutoff is fitted.
4. If separation holds, this strengthens evidence for a threshold-based component on these inputs. If ordering is clean within domains but not across them, a shared threshold is questionable. If valid and invalid relationships interleave within a domain, no cutoff can perfectly separate those observations. That is not by itself proof that the model is unusable or that every observed error is unacceptable.
5. Treat counts as descriptive: the 150 directions share only 30 descriptions and five collections. They are not 150 independent samples. Revisit semantic ambiguity transparently, preserving the original judgments and reporting any disputed case separately rather than silently correcting the answer key.

### Execution constraints

Run locally from the cached pinned checkpoint, one inference process, four CPU threads, batch four, maximum 60 GiB RAM, zero swap for the run. Check available memory and competing processes before launch. No paid compute or downloads are planned.

Save the frozen fixture hash before inference, exact serialized inputs, native generated tokens, raw logits, scores, configuration, model hashes, code hashes, and resource measurements under `TRUE02/`. Refuse overwrites. Preserve TRUE01 and all earlier results. Independently replay the saved calculations without another model run. No review UI is part of this experiment.

## TRUE02 runtime and verification

Run locally on September 12, 2026. No training, paid resources, downloads, GPU, quantization, or remote model code. TRUE01 and all earlier artifacts remain byte-for-byte unchanged.

### Frozen identity

- Model: `google/t5_xxl_true_nli_mixture`, revision `aa6cfe1dd4257853bfdd772992045f41bfc14988`.
- 11,307,321,344 parameters; CPU float32; evaluation/inference mode.
- Four threads, batch four, seed zero, deterministic algorithms, unchanged native greedy decoding with at most three new tokens.
- Exact tokenizer: `0` maps to `[3,632]`; `1` maps to `[209]`. Complete generated text with EOS determines native Yes/No. Whitespace token `3` alone is not a No answer.
- Score: full-vocabulary probability of first token `209`. Frozen cutoff: strictly greater than `0.142`.
- Fixture SHA256: `a514757d32adc0c31f859d0d8a912870cec4c7296ee07d231d9edc7608098e21`.
- Inputs SHA256: `cad6f8c463afc25108ebf42f93093773b3c3026601e62d5168bb0b441f171948`.
- Unchanged TRUE01 scorer SHA256: `334f5d7fc2e0ce390be049d828499dd130553ca981544df5a4656953fc525228`.

The 150 prepared inputs, exact fixture bytes, source snapshots, and source hashes were saved before checkpoint hashing or inference. The command required the fixture hash above and refused an existing output directory. The separate fixture review was completed before launch. No pair from TRUE01 was repeated. All five pinned weight hashes match; all checkpoint loading-error lists are empty. Model-file hashes and inference configuration match TRUE01. Maximum input length was 32 tokens; no truncation occurred.

Package versions: torch 2.8.0+cpu, transformers 4.57.1, huggingface_hub 0.36.2, numpy 2.3.4, safetensors 0.6.2.

### Resources

The host had approximately 100 GiB available RAM before launch. One model process ran inside a systemd scope capped at **60 GiB RAM**, **zero swap**, and **four CPUs**. Other processes were not stopped or changed.

- Total runner time, including checkpoint hashing/loading: **266.81 seconds**.
- Generation and packaging: **219.80 seconds**.
- Peak process RSS: **45,542,088 KiB**, about **43.43 GiB**.
- Observed scope swap: **zero**. The configured no-swap limit remained in force.
- Exit status: **0**. The inference scope is inactive; no model process remains.

Raw completion measurements and output hashes (`completion.json`). The approximately 19 MiB result directory retains all 150 full-vocabulary first-token logit arrays.

### Tests and independent checks

The separate verifier (`03bd9e45:sse_multivector/navigation-research-v1/TRUE02/verify.py`) imports no production scoring code and loads no neural model. It independently reconstructs all 150 expected directions and input strings, checks saved source/model/artifact hashes against TRUE01, retokenizes the inputs, decodes native answers, recomputes full-vocabulary probabilities using NumPy, checks the frozen cutoff, and recounts per-domain/per-kind errors, complete-pair correctness, and score inversions.

All checks pass; maximum score-replay difference is **4.44e-16**. The verifier ran in its own 2 GiB, no-swap, two-CPU scope. Complete verification result (`verification.json`).

A separate reviewer also checked all semantic expectations before scoring and, after scoring, inspected every error and the input/scoring snapshots. It found no required answer-key correction or implementation/scoring mismatch. This verifies the executed protocol, not universal semantic truth or a second independent model run.
