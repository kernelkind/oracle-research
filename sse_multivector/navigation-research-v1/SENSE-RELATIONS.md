# Task-trained relations and definition inputs

SRR01–SRR03 do not establish a usable parent-assignment rule. A model trained
specifically on semantic relationships preserves the obvious Bread → Sourdough
relation, but also produces clear false parents. Changing names into definitions
changes those errors rather than reliably removing them. No hierarchy, group,
mask, note membership, subject or browser was changed.

## Why test this model?

GDR03's generic topic classifier treated association as containment. The next
test therefore changes the learned task, not another topic prompt.

The released `ChangeIsKey/change-type-classifier` is a 355M-parameter
RoBERTa-large cross-encoder trained on pairs of WordNet sense definitions. Its
five labels are broader, narrower, sibling, opposite and unrelated meanings.
The last is called `homonym` in the checkpoint. It has no identity class.[^1]
The paper uses direct taxonomic relationships and random negative pairs;
its evaluation is not arbitrary note-category construction. The paper also
warns about wording-dependent lexical cues.[^2]

The pinned author evaluation code establishes output orientation: `hyponym`
means the **first** input is narrower, `hypernym` means the first is broader.
It excludes the test file's `metaphor` records. The published training source
currently creates a six-output head, whereas the released checkpoint and
evaluation code have five outputs. We use the verified five-output checkpoint,
not a claim to reproduce its training.[^3]

TaxoInstruct was also inspected first. Its released inference code exposes
parent selection and sibling generation, but the construction workflow uses
seed-taxonomy fine-tuning. The author's public Drive lists a 14.72GB `model.zip`;
its contents were not downloaded or verified. That additional dependency and
entity-name interface made it a less direct first diagnostic. It was not
declared unavailable or generally unsuitable.[^4]

## SRR01: fixed descriptions, different learned task

[Plan](./SRR01-PLAN.md), [all 908 scored pairs](./SRR01/scores.json),
[configuration and hashes](./SRR01/config.json).

Inputs were frozen before scoring:

- All 842 ordered subject-candidate pairs from GDR02, with only its known
  `This text is about ….` wrapper removed. Original words and punctuation remain.
- All 56 ordered pairs of GDR01's eight existing manual descriptions.
- The first two examples of each supported class from the pinned author's
  WordNet test file: ten implementation controls, not a Nostr benchmark.

Every input pair is passed directly to the tokenizer as a sequence pair, with
no instructions, aboutness template or external context. Scores below are
five-way softmax outputs, **not calibrated probabilities of correct placement**.

| First input | Second input | Model's relationship | Score | Interpretation |
| --- | --- | --- | ---: | --- |
| Sourdough bread. | Bread. | First is narrower | .99854 | Correct familiar refinement. |
| Brisket as food. | Beef as part of a meal. | First is narrower | .99713 | Plausible topical relation; the meal-specific seed still does not describe every Beef mask. |
| Coffee. | A good-morning greeting. | First is narrower | .98254 | Wrong: a drink is not a greeting. |
| Dogs. | A carnivore diet. | First is narrower | .96492 | Wrong for this corpus's human-diet meaning. |
| A carnivore diet. | Dogs. | First is broader | .81326 | Same wrong placement in reverse. |
| Nostr. | Music. | Unrelated | .97732 | Avoids the earlier false parent; not proof that these topics can never overlap in a note. |
| Homesteading. | Freedom. | Unrelated | .99538 | Avoids the earlier unsupported parent relation. |

These judgments are grounded in the unchanged groups, not those words alone.
The human-diet group concerns a recipe, meat eaters and criticism of carnivore
diet discourse, not biological carnivores. The greeting masks greet readers;
the Coffee group concerns coffee and coffee shops. Full masks, generated subjects
and original notes remain in [GDR02's groups](./GDR02/groups.json); their prior
complete audits are in [GDR01](./CONTEXTUAL-GROUP-RELATIONS.md) and
[GDR02](./EXISTING-SUBJECT-RELATIONS.md).

With the existing manual descriptions, Coffee/greeting receives unrelated
predictions, while the human diet/Dogs pair receives sibling predictions rather
than containment. That is not an unqualified success: `bread as food` becomes
narrower than `the human carnivore diet` with score .59878. We therefore tested
the definition-input mismatch separately.

All 74 directional subject predictions and all non-unrelated manual predictions
were inspected as text pairs. This is not an exhaustive semantic accuracy claim
for all 842 pairs or a new audit certifying the complete groups. For example,
an Art/Music relation cannot certify a group that mixes art with “state-of-the-art.”
Community/protocol and event/food scope questions also remain distinct from
clear false placements. No highest-scoring wording variant was adopted.

The native controls agree with six of ten supplied labels. Two reverse the
supplied substance/part direction. The other two predict a broader relation
where the data says sibling: “an action” versus vampire actions is one such
case. The definition text itself can support that broader reading. This tiny,
source-ordered set verifies orientation and operation; it is not an estimate
of benchmark accuracy, nor are all four disagreements unquestionable semantic
errors. Both antonym and both unrelated examples agree with their labels.

## SRR02: same model and groups, explicit definitions

[Plan](./SRR02-PLAN.md), [frozen definitions](./SRR02/definitions.json),
[all 56 comparisons including baseline scores](./SRR02/scores.json).

This changes only the eight manual descriptions, preserving their intended
scope and all ordered pairs. Definitions are diagnostic human inputs, not an
automatic description generator. In particular, Coffee still includes shops;
it was not silently narrowed to drinks to make the test easier.

Every definition supplied to the model:

| Existing meaning | Definition |
| --- | --- |
| Bread as food | Food made by cooking a dough of flour and liquid, usually by baking. |
| Sourdough bread | Bread made from dough fermented with a culture of wild yeast and bacteria. |
| Human carnivore diet | A way of eating in which a person eats animal foods and avoids plant foods. |
| Dogs as animals | Domesticated canine animals commonly kept as pets or used for work. |
| Morning greeting | An expression of welcome or goodwill addressed to someone during the morning. |
| Wishing a good morning | A greeting that expresses a wish for someone to have a pleasant morning. |
| Coffee and coffee shops | A drink prepared from roasted coffee beans, and establishments where that drink is prepared and served. |
| Music | Sounds arranged through rhythm, melody or harmony for expression or enjoyment. |

The classifier makes 13 directional predictions. Two correctly encode
Bread/Sourdough, two order the equivalent greeting meanings, and nine create
the following six false parent links. Both directions are listed separately
when the model predicts both; an empty reverse entry is not evidence of correctness.

| Predicted parent → child | Child-input narrower score | Parent-input broader score |
| --- | ---: | ---: |
| Bread → wishing a good morning | — | .73687 |
| Bread → Coffee and coffee shops | .92468 | .70937 |
| Human carnivore diet → Sourdough | — | .68708 |
| Human carnivore diet → Dogs | .96318 | — |
| Music → morning greeting | .87302 | .99632 |
| Music → wishing a good morning | .99197 | .99676 |

The earlier bread/diet prediction changes from narrower to sibling. That fixes
one directional error, but is not evidence of overall improvement. The two
greeting meanings cannot be assessed as strict parents because the model lacks
an equality output. No score cutoff or inverse-agreement filter is adopted:
several wrong links are strong and mutually consistent across both directions.

This result makes the limitation more concrete. The model can recognize familiar
refinements, but even explicit definitions do not make it reliably retain the
restrictions that distinguish a subject from an associated one. The exact causal
mechanism is not isolated: ignored qualifications, lexical cues and domain
mismatch remain hypotheses. These runs do not justify declaring all local
models incapable, or word-sense taxonomy equivalent to note browsing.

## SRR03: retain both the names and their definitions

The definition-only condition removed the familiar names, so one information
control remained. SRR03 mechanically concatenates each unchanged GDR01 description,
`: `, and its unchanged SRR02 definition. It adds no new explanation or selected
exception. HyperDef's joint term-and-definition representation motivates this
control; concatenation into this different classifier does not reproduce that
model.[^7] [Plan](./SRR03-PLAN.md), [exact inputs](./SRR03/definitions.json),
[all 56 scored pairs](./SRR03/scores.json).

This does not rescue the classifier. It produces 25 directional predictions,
including the following:

| Predicted narrower meaning | Predicted broader meaning | Narrower score |
| --- | --- | ---: |
| Sourdough bread | Bread as food | .99891 |
| Coffee and coffee shops | Bread as food | .99824 |
| Dogs as animals | Bread as food | .96277 |
| Morning greeting | Bread as food | .98035 |
| Coffee and coffee shops | Music | .98384 |
| Wishing a good morning | Music | .99384 |

The first is valid; the rest are not. All 25 directional inputs were inspected,
not just these examples. The exact input for the Coffee/Bread error is:

> coffee and coffee shops: A drink prepared from roasted coffee beans, and establishments where that drink is prepared and served.

> bread as food: Food made by cooking a dough of flour and liquid, usually by baking.

Thus neither absent familiar names nor absent definitions alone explains the
remaining errors. Combined inputs could themselves be out of distribution;
this is evidence against adopting this tested application, not against every
possible adaptation of this model. No wording was subsequently optimized to
these scores.

## Consequence for the hierarchy goal

Do not turn these predictions into edges, rewrite definitions to fit these
scores, or claim that the hierarchy improved. Reliable membership, group-wide
description fidelity, useful sibling choices and complete browsing paths remain
open. The strongest existing optional browser remains ND02-NP01.

The next research lead is a **shared learned hierarchy representation**, rather
than another independently scored pair classifier. HiT retrains a text encoder
with a loss bringing children near parents and another ordering their distances
from a common origin. Its paper includes transfer to other ontologies and hard
negative siblings, not just random unrelated words.[^5] This is a specific
hypothesis about training and representation, not a declaration that hyperbolic
geometry supplies semantics. Its actual score still requires a fitted weight
and threshold; transitivity and semantic correctness are not guaranteed merely
by using that score. Before any test, inspect the released model, input rendering,
training split and published calibration. Preserve the current fixed meanings
and compare with its unmodified base encoder if a test is justified. No HiT
weights were downloaded or inference run in this checkpoint.

An alternative was considered: construct path-specific intersections of note
memberships instead of claiming global subject subsumption. Faceted navigation
has an established conjunctive interpretation.[^6] But an exploratory count
over these 22 unchanged groups finds only 23 pair intersections with two or
more notes; only Coffee/Coffeechain has at least five (seven). Most intersections
involve community tags. That does not create the missing broad concepts or
establish useful distinctions, so it is not promoted as a solved hierarchy or
a reason to start another UI implementation. Earlier literal word-intersection
tests and this note-set observation are different operations.

## Reproduction and resources

All three runs use the same pinned checkpoint revision
`5c833b8a1f6e1f6fc3e27c533ce16e21949c931e`, CPU, two threads, batch size four,
FP32 and deterministic evaluation, without truncation. SRR01 inference took
43.73 seconds, SRR02 5.05 seconds and SRR03 6.29 seconds; peak process RSS was
about 4.80 GiB.
The public weights occupy 1.42GB. No paid model, GPU or external compute was used.
Every class logit, score, input string and source reference is saved. The
native source file is preserved for deterministic example selection.

From the repository root, choose new output directories:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
export TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1
export LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib
/tmp/oracle-nli-probe-venv/bin/python \
  sse_multivector/navigation-research-v1/SRR01/sense_relation_probe.py \
  --source sse_multivector/navigation-research-v1/SRR01/source.json \
  --manual sse_multivector/navigation-research-v1/SRR01/manual.json \
  --native sse_multivector/navigation-research-v1/SRR01/native.jsonl \
  --cache /tmp/oracle-sense-model-cache --output /tmp/srr01-replay-new
/tmp/oracle-nli-probe-venv/bin/python \
  sse_multivector/navigation-research-v1/SRR02/sense_definition_control.py \
  --source sse_multivector/navigation-research-v1/SRR02/source.json \
  --definitions sse_multivector/navigation-research-v1/SRR02/definitions.json \
  --cache /tmp/oracle-sense-model-cache --output /tmp/srr02-replay-new
/tmp/oracle-nli-probe-venv/bin/python \
  sse_multivector/navigation-research-v1/SRR03/sense_definition_control.py \
  --source sse_multivector/navigation-research-v1/SRR03/source.json \
  --definitions sse_multivector/navigation-research-v1/SRR03/definitions.json \
  --cache /tmp/oracle-sense-model-cache --output /tmp/srr03-replay-new
```

Five new tests were written before their implementation and first failed on
missing functions/modules. All 91 relevant tests pass. The native-data guard
caught its extra `metaphor` label before any inference; selection now follows
the published five-class evaluation's exclusion, with a regression test. No
approved test was weakened. Independent audit delegation was unavailable because
the agent thread limit was reached; this record does not claim agent consensus.

Saved-source replays into `/tmp/navigation-srr01-reproduce`,
`/tmp/navigation-srr02-reproduce` and `/tmp/navigation-srr03-reproduce` reproduce
all 1,020 scored pairs, summaries, input copies and source snapshots byte-for-byte.
Source hashes, original-pair references and all SRR03 concatenations were checked.
Runtime timing fields are observational and are not expected to be identical.

[^1]: [ChangeIsKey model card and pinned files](https://huggingface.co/ChangeIsKey/change-type-classifier/tree/5c833b8a1f6e1f6fc3e27c533ce16e21949c931e), accessed September 11, 2026.
[^2]: Cassotti, De Pascale and Tahmasebi (2024), [Using Synchronic Definitions and Semantic Relations to Classify Semantic Change Types](https://aclanthology.org/2024.acl-long.249.pdf), §§4–7, footnote 8 and §9. Read for training inputs, class semantics, identity limitation and wording caveats; the reported native benchmark is not reproduced here.
[^3]: [Author evaluation code](https://github.com/ChangeIsKey/change-type-classification/blob/71ceac95188eb41eaed4ba831c1c2a212c004a76/src/evaluate_wn.py), [training code](https://github.com/ChangeIsKey/change-type-classification/blob/71ceac95188eb41eaed4ba831c1c2a212c004a76/src/roberta_trainer.py), [native test data](https://github.com/ChangeIsKey/change-type-classification/blob/71ceac95188eb41eaed4ba831c1c2a212c004a76/data/test.jsonl).
[^4]: Shen et al. (2025), [TaxoInstruct paper](https://aclanthology.org/2025.findings-acl.167.pdf), §§3–4, [pinned author repository](https://github.com/yanzhen4/TaxoInstruct/tree/e3c6dbb46cbf21a2e48864b2af471385fe1c1010), [author model/data listing](https://drive.google.com/drive/folders/1uzvK0jppBEni9B7Hy5OhZLQ9McbQym32). README, inference, training and HiExpan scripts inspected; archive contents not inspected.
[^5]: He et al. (2024), [Language Models as Hierarchy Encoders](https://arxiv.org/html/2401.11374v3), §§2–4, especially equation 6 and transfer/hard-negative evaluation; [released MPNet model](https://huggingface.co/Hierarchy-Transformers/HiT-MPNet-WordNetNoun). Research lead only, not an SRR result.
[^6]: Hearst (2008), [UIs for Faceted Navigation: Recent Advances and Remaining Open Problems](https://people.ischool.berkeley.edu/~hearst/papers/hcir08.pdf), §§2, 7–8. Read for conjunction across facets and the unresolved large-subject-space problem, not as an algorithm that generates our categories.
[^7]: Yin and Roth (2018), [Term Definitions Help Hypernymy Detection](https://aclanthology.org/S18-2025.pdf), §3. Its separate term/definition comparisons motivate an information control, not simple concatenation as a proven substitute.
