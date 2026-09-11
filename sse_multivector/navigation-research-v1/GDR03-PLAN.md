# Input rendering control

GDR02's coverage check rejects even `The author has just had a coffee.` for
Coffee (0.0976) and `Rosemary in sourdough bread.` for Sourdough bread (0.3299).
Its premise renderer puts complete sentences inside `This text is about ...`.
That is not the model author's demonstrated classification input: the example
uses the original sentence as premise and a topic statement as hypothesis.[^1]

**Hypothesis:** removing this extra premise wrapper improves subject coverage,
without merely making unrelated pairs positive. This is a rendering diagnostic,
not a new model, prompt-generation project, threshold search or hierarchy.

Keep all 1,197 generated-subject pairs from GDR02: 355 coverage pairs and 842
cross-group candidate pairs. Keep their text, candidates, groups, model weights,
batch size, seed and CPU settings fixed. Use GDR02's scores as the baseline.
Run two controls for every pair:

1. Keep both wrappers, but avoid adding a second final period when the source
   already supplies sentence-ending punctuation.
2. Give the member/child's existing subject directly as the premise, keeping
   the same hypothesis as control 1.

Control 1 separates punctuation from the premise-wrapper change. Existing
subject text is never rewritten. Preserve all baseline scores and every changed
input/score. Analyze coverage and group relations separately. The direct-premise
condition is closer to topic classification, not proof of universal category
containment; a sentence and a category definition are not interchangeable.

Inspect known correct and incorrect examples and every new positive group
direction. More positive scores are not inherently progress. If input formatting
does not explain the errors, stop treating another cosmetic template change as
a promising construction method. A source description can still be too narrow
for its group, and classification can still mistake association for narrowing.

[^1]: Moritz Laurer, [model card, How to use the models](https://huggingface.co/MoritzLaurer/deberta-v3-base-zeroshot-v2.0#how-to-use-the-models), accessed September 11, 2026. The author's example supplies the text unchanged and applies `This text is about {}` only to the candidate class. This motivates a controlled test; it does not prove our alternative succeeds.
