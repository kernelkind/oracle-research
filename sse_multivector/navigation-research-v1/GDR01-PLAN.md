# Context in group relations

GDR01 tests one missing input: the meaning of each existing group, rather than
only the word that originally selected its masks. All MDH02 memberships, source
masks, notes, vectors and browser files remain fixed.

## Hypothesis

For the same local entailment model, expressing the source-checked subject of
both groups will recover the shared greeting meaning of GM and Good morning,
avoid placing Dogs under the human Carnivore diet, retain the direction from
Sourdough bread to Bread, and avoid a parent relationship between Coffee and
Music. A failure is informative; no threshold will be tuned to rescue it.

This is a diagnostic of relation scoring with supplied meanings, **not** an
automatic description-generation or hierarchy-construction experiment.
Descriptions are manually supplied experimental inputs, checked against every
member mask and original note before inference. They are not proposed UI titles,
new masks, exhaustive summaries, or independently learned group meanings.

## Controlled comparison

Use eight unchanged LGR01/MDH02 groups: Bread, Sourdough bread, Carnivore, Dog,
GM, Good morning, Coffee and Music. Score all 56 ordered pairs in four conditions:

1. Both sides use their complete original seed phrase.
2. Only the proposed child's phrase is replaced by its contextual description.
3. Only the proposed parent's phrase is replaced by its contextual description.
4. Both sides use their contextual descriptions.

Already clear descriptions may remain unchanged; do not add details merely to
make an input longer. The checked-in fixture is frozen before inference.

Each side has the identical wrapper `This text is about {description}.` The
premise describes the proposed child; the hypothesis describes the proposed
parent. This asks about topical implication, not whether a child's original
note proves every factual detail of a parent's original note or dictionary
definition. Reversing the inputs is scored independently.

Use the already installed `MoritzLaurer/deberta-v3-base-zeroshot-v2.0`, pinned
to `8e7e5af5983a0ddb1a5b45a38b129ab69e2258e8`, unchanged weights and inference
settings: local CPU, two threads, batch four, FP32, deterministic evaluation.
No new model download, training or paid inference is needed. The four conditions
contain 224 pairs, not 224 independent semantic examples.

## Interpretation fixed before the run

- Sourdough bread implies Bread; Bread does not imply Sourdough bread.
- GM and Good morning express the same greeting subject in these groups.
  Equivalence is not a reason to create a redundant parent–child step.
- Dog and the human Carnivore diet do not imply one another as group subjects.
- Coffee and Music do not imply one another. A music mask in a coffee shop
  supports overlapping membership, not whole-group ancestry.
- The remaining cross-group directions are negative controls for these specific
  meanings. Disagreement must be reviewed against source evidence, not scored
  automatically as semantic ground truth.

Inspect all scores and both directions. Report the ordinary binary classifier
decision at 0.5 only as its diagnostic output, not a validated browsing cutoff.
Show relevant errors alongside easy successes; do not summarize the sparse
positive set using overall accuracy alone. No relation is adopted by this run.

If contextual inputs help, the next unresolved component is obtaining faithful
group meanings automatically and checking their membership coverage. If they
do not, changing the representation alone has not established a working relation
mechanism. Neither outcome validates a complete navigation path.

## Research basis

TaxoLLaMA's published scoring code normally supplies the child's definition but
only the parent's name. This leaves the parent's sense unspecified. Its release
is a LoRA adapter for Llama-2-7B, not a standalone small classifier; it is not
being run here.[^1]

HyperDef uses the terms and definitions on **both** sides. Its analysis also
warns that whole-definition entailment is not equivalent to hypernymy: the
definitions can contain different factual details. Its all-definition maximum
would still admit a relation in an irrelevant sense. These findings motivate
the controlled input comparison, not a claim to reproduce HyperDef.[^2]

The chosen DeBERTa model is a trained binary entailment classifier. Its earlier
mask-to-description failures remain part of the evidence. This run changes the
relation inputs while keeping its weights fixed; it is not another model search.

[^1]: Moskvoretskii et al. (2024), [TaxoLLaMA](https://aclanthology.org/2024.acl-long.127/); [author prompt code](https://github.com/VityaVitalich/TaxoLLaMA/blob/7881f9fd26c4ab935d98ffce0fac91eb1fac621c/pipeline_src/dataset/prompt_schemas.py), [scoring code](https://github.com/VityaVitalich/TaxoLLaMA/blob/7881f9fd26c4ab935d98ffce0fac91eb1fac621c/TExEval-2_testdata_1.2/est_ppl.py), [adapter configuration](https://huggingface.co/VityaVitalich/TaxoLLaMA/blob/16eee40bf4205c1de762711fff1b907590cf5fd4/adapter_config.json).
[^2]: Yin and Roth (2018), [Term Definitions Help Hypernymy Detection](https://aclanthology.org/S18-2025.pdf), sections 3–4; [author repository](https://github.com/yinwenpeng/HyperDef/tree/ccd475d32a22800963b93fce854e43f626d10b31).
