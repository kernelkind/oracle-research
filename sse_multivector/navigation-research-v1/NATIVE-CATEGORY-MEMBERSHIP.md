# Native text-to-category membership

TCC01 finds useful recognition of shared subjects, but the model's default
membership decisions are unreliable. Reversing the same category list changes
which records it accepts. Supplying categories individually removes many such
errors but leaves confident false assignments. Importantly, the individual
scores still separate the supported and unsupported examples in this small
audit; that possibility should be tested elsewhere, not dismissed or declared
validated.

This is a membership diagnostic, not a generated hierarchy. GDC09, the
extraction prompts, masks, vectors and browser are unchanged.

## Why this model was tested

DSP01 established that valid descriptions of a common subject can have different
grammatical paths. Exact grammatical matching therefore cannot be required.
PPR01 showed useful semantic neighborhoods without a membership rule. The
missing capability is accepting different grounded descriptions of a category
while rejecting merely associated content.

GLiClass's native task is multi-label text classification, with natural-language
category names supplied alongside text. Its training includes short inputs,
variable label counts, classification and NLI. Its benchmarks measure topic and
sentiment classification, not arbitrary narrow grounded categories or
parent–child construction. This provides task-fit grounds for a small test,
not a claim of reliable transfer.[^1]

The exact public training data also show a limitation: a five-word camera title
receives unsupported attributes as positive labels. Some NLI rows store relation
markers where the public loader expects candidate strings. Passed unchanged,
those rows produce all-zero targets; the exact release preprocessing is not
established. Neither observation proves what caused the inference errors here.
The independent audit inspected untruncated dataset-server JSON, including its
matching revision header.[^2][^3]

The pinned model reads all supplied categories and the text in one encoder
pass. Category tokens and the first token of the joint input feed a learned MLP;
each output receives a sigmoid independently. These scores are not cosine
similarities or calibrated probabilities of semantic correctness. The category
list is part of the model input, so its influence must be tested.[^4]

## What stayed fixed

All 14 descriptions from DSP01 were used unchanged, with their full source
notes and masks retained in [inputs.json](./TCC01/inputs.json). Only each saved
`subject` string entered the model. Other parts of the original note cannot
explain the model's assignments, because it never saw them.

The categories were Food, Food preservation, Bread, Bread with rosemary,
Coffee, Coffee drinking experience, Coffee shops, and Morning greetings.
These are fixed manual diagnostic descriptions, not a discovered or uniquely
correct taxonomy. Broader and overlapping memberships are allowed.

Each description was scored with all eight categories, with the identical
list reversed, and with each category supplied alone. All 336 logits and
sigmoid scores are preserved in [scores.json](./TCC01/scores.json), including
every value below the native 0.5 threshold. No threshold was tuned.

The [pre-run plan](./TCC01-PLAN.md) distinguishes its focused judgments from
other initially unjudged assignments. The subsequent
[complete semantic audit](./TCC01/audit.json) covers all 14 records and all
scores, retaining five scope-dependent assignments as unjudged. It is an
assistant assessment, not a record of user approval.

## Recognition across different expressions

These values use the full category list. They demonstrate useful common-subject
recognition, not exclusivity: unrelated categories can also receive high scores.

| Supplied description | Category | Score |
| --- | --- | ---: |
| Rosemary in sourdough bread. | Bread with rosemary | 0.999666 |
| The author added fresh rosemary and cranberries to the Irish soda bread. | Bread with rosemary | 0.999640 |
| Food preservation. | Food preservation | 0.999652 |
| The author is preparing this year's garden-grown beets for preservation by freezing. | Food preservation | 0.999617 |
| Pressure-canning homemade chicken stock for pantry storage is a form of food preservation. | Food preservation | 0.999630 |

Both coffee-experience descriptions also receive Coffee and Coffee drinking
experience. The internet-dispute description receives Coffee shops and Coffee,
which is legitimate: Coffee may narrow into venue-related content. Thus a
different grammatical realization is not itself preventing recognition.

Across the predeclared checks, all 25 supported assignments exceed 0.5 in each
condition. But 4 of 11 unsupported assignments also exceed it jointly, 4 with
reversed categories, and 5 with categories supplied individually. These small,
deliberately selected counts are not corpus accuracy estimates.

## Category order changes an unsupported assignment

Row 658 · N076 · V700. The supplied description is:

> Tandoori-spiced chicken with yogurt.

Complete original with its mask:

> ⟦Tandori spice chik⟧ ⟦with⟧ somo sexi ⟦yogo⟧. On pure fire with best handmade wild rose wine,  #purelife #food #chef #foodstr no compromise
>
> https://image.nostr.build/d9fce20da7cd056362daca85445508eafc7620bf706788474b1dc28e4875971e.jpg https://image.nostr.build/a648216b769b08347153de65a019f5968d249882cefa912b8c64519d36ca95cf.jpg
> https://image.nostr.build/07e9f6b72f1983601c5f5733b7b889fd6fbe0e8a25e40f131edf1ad299cacd20.jpg

| Input change | Bread score | Native decision |
| --- | ---: | --- |
| Original order of the eight categories | 0.112018 | Reject |
| Reverse those same eight categories | 0.639839 | Accept |

Only the category order changes. Bread is unsupported by this description and
mask in either condition. The stock-preservation record similarly changes
0.078575 → 0.580911 for Bread, and the beet-preservation record changes
0.356889 → 0.807237. Across the full matrix, order reversal changes 9 of 112
native threshold decisions. This demonstrates an order effect, not its precise
internal cause.

A separate set-change control is even larger: for row 669, `Rosemary in
sourdough bread.`, Coffee scores 0.021723 when supplied alone and 0.966067 with
all eight categories. Unlike reversal, that intervention changes both the
number and content of other labels; it does not isolate a particular added label.

## Removing other labels does not fix every false assignment

Row 258 · N017 · V120. Supplied description:

> The author wishes readers a good morning.

Complete original with its mask:

> ⟦Good morning⟧, crushed a solid gym session this morning to kick off the weekend. Now time for a late breakfast! #coffeechain

Coffee supplied alone scores **0.941256**. Breakfast and Coffeechain are in the
original but not the model input or mask. They cannot rescue that assignment
for this record.

Row 551 · N060 · V503. Supplied description:

> The post author made coffee today.

Complete original with its mask:

> ⟦Made⟧ my ⟦coffee⟧ with raw cream and a raw egg yolk ⟦today⟧ #coffeechain

Morning greetings supplied alone scores **0.997870**. Neither the supplied
description nor selected text greets anyone or specifies morning. This shows
that eliminating label interactions alone does not make the native threshold
a dependable membership rule. Coffee drinking experience for this same record
remains an open scope judgment; it is not counted as another clear failure.

## What the score order does and does not establish

In the joint condition, Coffee scores the greeting above the coffee-shop record:

| Record | Coffee score |
| --- | ---: |
| 258 · greeting, unsupported | 0.999138 |
| 345 · coffee-shop dispute, supported | 0.992595 |

Row 345's complete original and mask:

> ⟦Coffee shop⟧ I liked now has a “No laptops or tablets” rule on weekends. This is what happens if you let hipsters get too successful. ⟦Felt like changing their router/ap passwords so they⟧ could ⟦experience⟧ the true ⟦freedom from internet⟧, but I simply went to another coffee shop and will remove this one from rotation. Personal growth on display.

Its supplied description is:

> The author wanted to change the coffee shop's router or wireless access point passwords so the people running the shop would experience being without internet access.

No one cutoff for joint Coffee can reject that greeting while retaining this
valid venue-related record. Reversed Coffee has the same inversion.

The single-category condition is different. For each category below, every
supported record scores above every unsupported record in the complete audit.
Five explicitly unjudged boundaries are excluded. The extra judgments were
made after seeing scores, so this is descriptive evidence, not a predeclared
test success or calibration result.

| Category supplied alone | Lowest supported score | Highest unsupported score |
| --- | ---: | ---: |
| Food | 0.992513 | 0.260118 |
| Food preservation | 0.999381 | 0.939220 |
| Bread | 0.974850 | 0.328542 |
| Bread with rosemary | 0.996396 | 0.630193 |
| Coffee | 0.963154 | 0.941256 |
| Coffee drinking experience | 0.998990 | 0.856304 |
| Coffee shops | 0.998520 | 0.820462 |
| Morning greetings | 0.999467 | 0.997870 |

No cutoff is selected from these values. In particular, the greeting separation
is narrow in sigmoid space, and none of these bounds has been tested on other
records. The result would be misrepresented both by calling the native
classifier reliable and by claiming that no calibration could possibly help.

## Construction consequence and next uncertainty

Do not define category contents from joint GLiClass scores at 0.5. The same
description can enter Bread merely because choices were reordered, and Coffee
contains a demonstrated wrong ordering. No hierarchy should inherit those
assignments.

Single-category scoring is a remaining, bounded possibility, not an adopted
fix. Before either calibrating it or discarding it, test whether supported and
unsupported records outside this diagnostic remain separable for a fixed
category. Freeze the model, descriptions and category wording; inspect all
high-scoring additions and low-scoring supported witnesses with full source
context. Interleaving would show why calibration cannot solve that category's
errors; separation would justify a genuinely held-out calibration experiment.
Do not tune a cutoff and report these same fourteen records as validation.

This is consequential because content-based membership is still missing from
the proposed construction. It is not a substitute for generating categories
or establishing meaningful parent–child relationships. Even perfect assignments
to these eight manually supplied labels would not establish either requirement.

## Reproduction and resource use

Three production-path tests failed for the absent module before implementation.
All 71 selected regression tests now pass. Exact native tokenization, special
tokens, checkpoint keys/shapes and direct-score/native-pipeline agreement were
checked. The model-card travel example accepts Travel and Dreams and rejects
the other three labels; no published numerical ground truth was assumed.

The isolated runtime uses Transformers 4.48.2 and the pre-paper native source
revision. All source/model/package hashes and rendered input tokens are in
[config.json](./TCC01/config.json). The longest input is 55 tokens, with no
truncation. The measured checkpoint has **186,545,922** float32 parameters;
the pre-run plan's metadata-derived count was one lower. Exact weight loading
succeeded with no missing, unexpected or mismatched keys.

One CPU process, two Torch threads, batches of four: 5.51 seconds inference,
about 4.9 GiB peak RSS, 723 MiB public checkpoint cache. No paid service, GPU,
frontier generation, new masks or rewritten subjects were used. The offline
replay reproduced inputs, all 336 scores, rendered tokens and runner snapshot
byte-for-byte; source/model hashes and package versions also match.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib \
/tmp/oracle-gliclass-probe-venv/bin/python sse_multivector/native_category_probe.py \
  --input sse_multivector/navigation-research-v1/DSP01/inputs.json \
  --labels food 'food preservation' bread 'bread with rosemary' coffee \
    'coffee drinking experience' 'coffee shops' 'morning greetings' \
  --source /tmp/navigation-gliclass-v3-source-20260912 \
  --cache /tmp/oracle-gliclass-probe-cache --offline \
  --output /tmp/tcc01-another-replay
```

Use a new output directory. The source checkout must be clean at revision
`5d96d8a5d099a10f00d90a2493e5f93a3ddbd2ae`; the model revision is
`77a70e6cd52e602ed18184ef37d18bdd3741e3d5`. The public dependency source can be
re-fetched by that revision; hashes preserve the exact files used. Earlier
GDC09 and experimental artifacts are unchanged. Existing untracked HiT files
are not part of this experiment and remain untouched.

## Sources

[^1]: Stepanov et al., [GLiClass: Generalist Lightweight Model for Sequence Classification Tasks](https://arxiv.org/html/2508.07662v1), 2025, §§2–3. Task, training streams, evaluation and architecture; no hierarchy construction benchmark.
[^2]: Knowledgator, [v3 logic dataset](https://huggingface.co/datasets/knowledgator/gliclass-v3-logic-dataset), revision `ee8e07d42c1f95a4421ae78498eec23aec74f1d7`; exact dataset-server rows 1, 21 and 72. Rows were read without truncation, not inferred from abbreviated previews.
[^3]: Knowledgator, [pre-paper training loader](https://github.com/Knowledgator/GLiClass/blob/5d96d8a5d099a10f00d90a2493e5f93a3ddbd2ae/gliclass/data_processing.py) and [entry point](https://github.com/Knowledgator/GLiClass/blob/5d96d8a5d099a10f00d90a2493e5f93a3ddbd2ae/train.py). Conditional loader behavior is not proof of the private release preprocessing.
[^4]: Knowledgator, [pinned native model](https://github.com/Knowledgator/GLiClass/blob/5d96d8a5d099a10f00d90a2493e5f93a3ddbd2ae/gliclass/model.py), [pipeline](https://github.com/Knowledgator/GLiClass/blob/5d96d8a5d099a10f00d90a2493e5f93a3ddbd2ae/gliclass/pipeline.py), and [base-v3 checkpoint configuration](https://huggingface.co/knowledgator/gliclass-base-v3.0/tree/77a70e6cd52e602ed18184ef37d18bdd3741e3d5).
