# Native text-to-category membership

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

TCC01 finds useful recognition of shared subjects, but the model's default
membership decisions are unreliable. Reversing the same category list changes
which records it accepts. Supplying categories individually removes many such
errors but leaves confident false assignments. Importantly, the individual
scores still separate the supported and unsupported examples in this small
audit; that possibility should be tested elsewhere, not dismissed or declared
validated. The subsequent [TCC02](./INDIVIDUAL-CATEGORY-DISCRIMINATION.md)
finds Coffee witness inversions on other notes, while
[TCC03](./COMPLETE-NOTE-CATEGORY-EVIDENCE.md) shows that complete available
descriptions nevertheless restore the judged note ordering. Those records
supersede the next-test prescription below, not the original measurements.

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
notes and masks retained in `./TCC01/inputs.json`. Only each saved
`subject` string entered the model. Other parts of the original note cannot
explain the model's assignments, because it never saw them.

The categories were Food, Food preservation, Bread, Bread with rosemary,
Coffee, Coffee drinking experience, Coffee shops, and Morning greetings.
These are fixed manual diagnostic descriptions, not a discovered or uniquely
correct taxonomy. Broader and overlapping memberships are allowed.

Each description was scored with all eight categories, with the identical
list reversed, and with each category supplied alone. All 336 logits and
sigmoid scores are preserved in `./TCC01/scores.json`, including
every value below the native 0.5 threshold. No threshold was tuned.

The [pre-run plan](NATIVE-CATEGORY-MEMBERSHIP.md#tcc01-study-design) distinguishes its focused judgments from
other initially unjudged assignments. The subsequent
complete semantic audit (`./TCC01/audit.json`) covers all 14 records and all
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

Single-category scoring was retained as a bounded possibility, not an adopted
fix. TCC02 subsequently tested supported/unsupported records outside these
fourteen notes while keeping model and categories fixed. Coffee witness scores
interleave, so one cutoff cannot perfectly separate those descriptions. TCC03
then restores judged note ordering by admitting every available description as
evidence. Neither experiment validates a cutoff. The next decision concerns
defensible score-to-membership calibration, not tuning on these records and
calling them independent validation. Perfect accuracy is not a product
requirement, and failed exact separation does not make every imperfect score
useless.

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
`./TCC01/config.json`. The longest input is 55 tokens, with no
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
GDC09 and experimental artifacts are unchanged.
are not part of this experiment and remain untouched.

## Sources

[^1]: Stepanov et al., [GLiClass: Generalist Lightweight Model for Sequence Classification Tasks](https://arxiv.org/html/2508.07662v1), 2025, §§2–3. Task, training streams, evaluation and architecture; no hierarchy construction benchmark.
[^2]: Knowledgator, [v3 logic dataset](https://huggingface.co/datasets/knowledgator/gliclass-v3-logic-dataset), revision `ee8e07d42c1f95a4421ae78498eec23aec74f1d7`; exact dataset-server rows 1, 21 and 72. Rows were read without truncation, not inferred from abbreviated previews.
[^3]: Knowledgator, [pre-paper training loader](https://github.com/Knowledgator/GLiClass/blob/5d96d8a5d099a10f00d90a2493e5f93a3ddbd2ae/gliclass/data_processing.py) and [entry point](https://github.com/Knowledgator/GLiClass/blob/5d96d8a5d099a10f00d90a2493e5f93a3ddbd2ae/train.py). Conditional loader behavior is not proof of the private release preprocessing.
[^4]: Knowledgator, [pinned native model](https://github.com/Knowledgator/GLiClass/blob/5d96d8a5d099a10f00d90a2493e5f93a3ddbd2ae/gliclass/model.py), [pipeline](https://github.com/Knowledgator/GLiClass/blob/5d96d8a5d099a10f00d90a2493e5f93a3ddbd2ae/gliclass/pipeline.py), and [base-v3 checkpoint configuration](https://huggingface.co/knowledgator/gliclass-base-v3.0/tree/77a70e6cd52e602ed18184ef37d18bdd3741e3d5).

## TCC01 study design

### Question and construction role

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

### Task fit and limits

GLiClass is natively trained to assign multiple natural-language categories to
text. Its paper describes classification/NLI training followed by short-text
and variable-label-density post-training. That is closer to saved subject
descriptions than dictionary-definition relation classification. Its reported
benchmarks do not establish grounded membership for arbitrary narrow topics.[^tcc01-study-design-1]

The released data also contain unsupported positive attributes: the title
`Nice Camera - Very Fragile` has positives including `Compact size` and
`Lightweight`. This is a concrete reason to test association errors, not assume
the training supervision enforces our evidence boundary. It does not establish
how much this example influenced the weights. Dataset/release provenance needs
to be distinguished from proof of the exact training run.[^tcc01-study-design-2]

The native uni-encoder reads category names and text jointly. The pinned
checkpoint uses a first-token representation of that joint input, special
category-token representations, and an MLP scorer. Multi-label outputs are
sigmoids, not mutually exclusive softmax choices. Other supplied categories can
change the result. Current package code has changed; use the last pre-paper
source revision and its supported Transformers version instead.[^tcc01-study-design-3][^tcc01-study-design-4]

### Fixed inputs and controls

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

### Hypothesis, competing explanations, decisions

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

### Execution constraints

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

### Sources

[^tcc01-study-design-1]: Stepanov et al., [GLiClass](https://arxiv.org/html/2508.07662v1), 2025,
  §§2–3. Training, native task and limits of the reported evaluation.
[^tcc01-study-design-2]: Knowledgator, [v3 logic dataset](https://huggingface.co/datasets/knowledgator/gliclass-v3-logic-dataset),
  revision `ee8e07d42c1f95a4421ae78498eec23aec74f1d7`, exact row 21.
[^tcc01-study-design-3]: Knowledgator, [native pipeline](https://github.com/Knowledgator/GLiClass/blob/5d96d8a5d099a10f00d90a2493e5f93a3ddbd2ae/gliclass/pipeline.py),
  [model](https://github.com/Knowledgator/GLiClass/blob/5d96d8a5d099a10f00d90a2493e5f93a3ddbd2ae/gliclass/model.py).
[^tcc01-study-design-4]: Knowledgator, [base-v3 checkpoint](https://huggingface.co/knowledgator/gliclass-base-v3.0/tree/77a70e6cd52e602ed18184ef37d18bdd3741e3d5),
  configuration and native usage example.
