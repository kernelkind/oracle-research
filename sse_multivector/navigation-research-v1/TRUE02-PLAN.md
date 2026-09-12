# TRUE02 — Does containment remain distinguishable from overlap?

## Question

TRUE01's topic-sentence scores placed all valid relationships above all invalid relationships in ten constructed families. The gap was only 0.003920. Does this useful separation survive a different set with many closely related, overlapping categories?

This tests a proposed component, not an adopted hierarchy. No model training, HDBSCAN changes, category-generation changes, or graph construction are included.

## Frozen comparison

Keep TRUE01's released checkpoint, exact topic wrapper, tokenizer, float32 CPU inference, greedy generation, and score calculation unchanged. The only semantic input change is the category set. Bare titles are not retested.

For **A contains B?**, the model receives:

```text
premise: This text is about {B}. hypothesis: This text is about {A}.
```

The model sees neither our expected answers nor our scope explanations. Our wrapper is an adaptation for topical containment, not an instruction prescribed by the TRUE paper.

Keep native Yes/No answers and the full score. Separately accept when the score is **strictly greater than 0.142**, the provisional cutoff proposed from TRUE01 before any TRUE02 score is observed. Do not change this cutoff after scoring. The score is the full-vocabulary probability of first output token `1`; it is not cosine or a calibrated probability of category containment.

## New examples and judgments

[Exact fixture](true02-fixture.json): six categories in each of food, software, economics, politics, and interpersonal relationships. Test every distinct pair within each domain in both directions: **75 unordered pairs, 150 directional decisions**. Do not add easy unrelated cross-domain pairs to increase apparent accuracy.

The descriptions are manually constructed realistic categories, **not actual generated HDBSCAN labels**. This isolates the relationship scorer from label-generation quality. The domains recur from TRUE01; the category pairs are new. This is unseen-example transfer within familiar broad domains, not proof of transfer to all new domains or of an end-to-end hierarchy.

Expected-positive directions are explicitly listed; all remaining directions are expected No. Reciprocal positives represent equivalence. Scope explanations provide noncontainment counterexamples. A separate reviewer audits all unordered pairs without access to TRUE02 scores. Resolve or explicitly set aside genuinely ambiguous judgments before freezing the fixture, never by inspecting predictions.

This evaluation concerns topical containment. For example, bread baking is a narrower topic under bread, even though a process is not a physical loaf. If a disputed pair cannot sustain a clear topical judgment, it must not be presented as a definitive model error.

## Analysis fixed before scoring

1. Report correct/incorrect native decisions and decisions at 0.142, globally and per domain. Also report whether both directions of each pair are correct.
2. Report strict containment, equivalence, reverse containment, and noncontainment separately. Inspect all errors with both complete descriptions and scores.
3. Check whether any expected-negative score reaches or exceeds an expected-positive score, globally and within each domain. Preserve all such orderings. No new cutoff is fitted.
4. If separation holds, this strengthens evidence for a threshold-based component on these inputs. If ordering is clean within domains but not across them, a shared threshold is questionable. If valid and invalid relationships interleave within a domain, no cutoff can perfectly separate those observations. That is not by itself proof that the model is unusable or that every observed error is unacceptable.
5. Treat counts as descriptive: the 150 directions share only 30 descriptions and five collections. They are not 150 independent samples. Revisit semantic ambiguity transparently, preserving the original judgments and reporting any disputed case separately rather than silently correcting the answer key.

## Execution and preservation

Run locally from the cached pinned checkpoint, one inference process, four CPU threads, batch four, maximum 60 GiB RAM, zero swap for the run. Check available memory and competing processes before launch. No paid compute or downloads are planned.

Save the frozen fixture hash before inference, exact serialized inputs, native generated tokens, raw logits, scores, configuration, model hashes, code hashes, and resource measurements under `TRUE02/`. Refuse overwrites. Preserve TRUE01 and all earlier results. Independently replay the saved calculations without another model run. No review UI is part of this experiment.
