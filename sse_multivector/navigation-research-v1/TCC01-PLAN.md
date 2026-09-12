# TCC01 — native text-to-category membership

## Question and construction role

Can a classifier trained on text/category assignments recognize a common
subject across different grammatical expressions, while excluding merely
associated meanings? DSP01 showed why identical grammatical paths cannot be
required; PPR01 showed that embedding proximity is not itself membership.

A plausible construction would propose category expressions from the corpus,
check their membership against grounded records, and then establish meaningful
broader/narrower relations separately. This experiment tests only that middle
capability. Its eight manually specified diagnostic categories are not an
automatically discovered taxonomy, nor the only acceptable arrangement.
Success would justify a broader membership audit, not construction of a browser.

## Task fit and limits

GLiClass is natively trained to assign multiple natural-language categories to
text. Its paper describes classification/NLI training followed by short-text
and variable-label-density post-training. That is closer to saved subject
descriptions than dictionary-definition relation classification. Its reported
benchmarks do not establish grounded membership for arbitrary narrow topics.[^1]

The released data also contain unsupported positive attributes: the title
`Nice Camera - Very Fragile` has positives including `Compact size` and
`Lightweight`. This is a concrete reason to test association errors, not assume
the training supervision enforces our evidence boundary. It does not establish
how much this example influenced the weights. Dataset/release provenance needs
to be distinguished from proof of the exact training run.[^2]

The native uni-encoder reads category names and text jointly. The pinned
checkpoint uses a first-token representation of that joint input, special
category-token representations, and an MLP scorer. Multi-label outputs are
sigmoids, not mutually exclusive softmax choices. Other supplied categories can
change the result. Current package code has changed; use the last pre-paper
source revision and its supported Transformers version instead.[^3][^4]

## Fixed inputs and controls

Use all 14 unchanged records in `DSP01/inputs.json`. Model input is each saved
`subject` string. Preserve its complete original note, fragments and IDs for
semantic inspection, but do not feed them to the classifier. No rewriting,
mask regeneration, examples, instruction prompt, or old-tree labels.

Fixed categories, in this order:

1. food
2. food preservation
3. bread
4. bread with rosemary
5. coffee
6. coffee drinking experience
7. coffee shops
8. morning greetings

Score each record with the full list, the reversed list, and each category
individually. These are controls for label interaction and order, not a sweep
for whichever configuration looks best. Retain every raw logit and sigmoid,
including those below the native 0.5 threshold. Do not tune that threshold.

Predeclared focused judgments (row IDs refer to the preserved records):

| Category | Supported | Unsupported for the supplied description |
| --- | --- | --- |
| bread with rosemary | 669, 254 | 40, 658 |
| bread | 669, 254, 40 | 658 |
| coffee drinking experience | 572, 854 | 345 |
| coffee shops | 345 | 572, 854 |
| coffee | 572, 854, 345, 551 | 258, 192 |
| morning greetings | 258, 192 | 551 |
| food preservation | 484, 468, 904 | 414, 658 |
| food | 669, 254, 40, 484, 468, 904, 414, 658 | — |

These judgments are about the specific supplied description and its supporting
mask, not every subject elsewhere in the full note. For example, the carnivore
note also mentions coffee, but its selected record says only `A carnivore diet.`
Unlisted assignments are not automatically errors. Broad Food, venue-related
Coffee, and overlapping memberships are legitimate; no exact claim equivalence
or direction-of-action discrimination is required.

## Hypothesis, competing explanations, decisions

**Hypothesis:** Native multi-label classification accepts the different grounded
witnesses in each family and rejects the listed associated/partial alternatives,
without those assignments depending on category order or competing labels.

Competing explanations are that the scores primarily follow associated topics,
that the supplied category set suppresses valid overlapping labels, or that an
input/runtime mismatch makes the test invalid. Full/reversed/single conditions
distinguish some label effects; native formatting and loading checks address
implementation fidelity. The saved inputs permit auditing category wording and
upstream meaning before blaming classification.

Inspect the complete matrix, not only selected improvements. Report native
threshold decisions and, separately, whether an unsupported witness outranks a
supported one for the same category. Such an inversion cannot be repaired by a
single score cutoff for that category/condition. It is not proof of the cause.

Would either outcome change the next decision? Yes. Consistent grounded
assignments would justify testing more records and corpus-proposed expressions
before attempting membership-backed construction. Repeated association errors
would rule out adopting this frozen configuration as that membership rule;
do not automatically try a larger checkpoint or change descriptions. If only
label-set interactions fail, investigate that mechanism before a broader run.
If judgments are ambiguous, do not count them as demonstrated model failures.

## Execution and preservation

- Model: `knowledgator/gliclass-base-v3.0`, revision
  `77a70e6cd52e602ed18184ef37d18bdd3741e3d5` (186,545,921 parameters).
- Source: Knowledgator/GLiClass `5d96d8a5d099a10f00d90a2493e5f93a3ddbd2ae`.
- Supported native runtime: Transformers 4.48.2; isolated environment, CPU only,
  two Torch threads, one model process, batches of at most four.
- Run the model-card travel example as an implementation smoke check, preserving
  its complete scores. It supplies no published numeric expectation.
- Check exact weight loading, special-token IDs, rendered inputs, token counts,
  no truncation, and direct-logit agreement with the native pipeline's sigmoid.
- Preserve sources, hashes, complete inputs, all scores, tests, elapsed time,
  peak memory and an offline replay. No paid infrastructure or frontier calls.
- GDC09, earlier results, personal notes, and the review tool remain untouched.

## Sources

[^1]: Stepanov et al., [GLiClass](https://arxiv.org/html/2508.07662v1), 2025,
  §§2–3. Training, native task and limits of the reported evaluation.
[^2]: Knowledgator, [v3 logic dataset](https://huggingface.co/datasets/knowledgator/gliclass-v3-logic-dataset),
  revision `ee8e07d42c1f95a4421ae78498eec23aec74f1d7`, exact row 21.
[^3]: Knowledgator, [native pipeline](https://github.com/Knowledgator/GLiClass/blob/5d96d8a5d099a10f00d90a2493e5f93a3ddbd2ae/gliclass/pipeline.py),
  [model](https://github.com/Knowledgator/GLiClass/blob/5d96d8a5d099a10f00d90a2493e5f93a3ddbd2ae/gliclass/model.py).
[^4]: Knowledgator, [base-v3 checkpoint](https://huggingface.co/knowledgator/gliclass-base-v3.0/tree/77a70e6cd52e602ed18184ef37d18bdd3741e3d5),
  configuration and native usage example.
