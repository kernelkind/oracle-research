# Subject input rendering

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

GDR03 establishes that GDR02's input formatting affected some errors, but fixing
it does not make this classifier a reliable hierarchy constructor. Removing the
extra premise wrapper improves several correct matches and introduces incorrect
Coffee → morning-greeting relationships. No input format or score threshold is
adopted for automatic parent assignment.

## Controlled change

Keep all 1,197 generated-subject pairs from GDR02, the same local DeBERTa weights,
and every original group/member. There are 355 coverage pairs and 842 directional
candidate pairs. The two new conditions produce 2,394 scores; GDR02 supplies the
unchanged baseline. [The plan](SUBJECT-INPUT-RENDERING.md#gdr03-study-design) was written before scoring.

For the generated subject `Grinding coffee beans.` and candidate `Coffee.`:

| Condition | Premise | Hypothesis |
|---|---|---|
| GDR02 baseline | This text is about Grinding coffee beans.. | This text is about Coffee.. |
| Punctuation control | This text is about Grinding coffee beans. | This text is about Coffee. |
| Direct premise | Grinding coffee beans. | This text is about Coffee. |

Punctuation control changes only the added sentence-ending punctuation.
Direct premise then removes only the premise wrapper. Source subject words are
never rewritten. The author's documented classifier example supplies its input
sentence directly and wraps only the candidate class.[^1] This supports testing
the change, not assuming it will work.

## Improvements and persistent misses

Scores below use baseline → punctuation control → direct premise. Each supplied
subject comes from the unchanged extraction artifacts; it is not a new paraphrase.

| Existing subject → candidate | Baseline | Punctuation | Direct |
|---|---:|---:|---:|
| Grinding coffee beans. → Coffee. | .1759 | .6214 | .9487 |
| Rosemary in sourdough bread. → Sourdough bread. | .3299 | .4950 | .9384 |
| The author is tired of the narrative associating bitcoin with the carnivore diet. → A carnivore diet. | .4579 | .3535 | .8320 |
| The author has just had a coffee. → Coffee. | .0976 | .0688 | .0623 |
| Wishing the Nostr community a good morning. → The author wishes readers a good morning. | .0588 | .1373 | .1045 |

The first three are genuine topical improvements. The coffee-consumption match
still fails, while the greeting target remains an overly specific author's claim
rather than a clean group description. There is no evidence that formatting alone
solves either subject coverage or description scope.

The useful Art/state-of-the-art and getting-up/price-rise distinctions remain
negative in both controls. For example, rising Christmas-lunch costs score
.000075 → .000109 → .000097 against Getting up.

## Regressions and associated-topic errors

Some correct coverage is lost. The subject `The author presents today's dinner
of bread, butter, avocado, and eggs as clean eating.` goes from .7003 to .2809
against Bread; `Good coffee accompanying a duck egg and basil breakfast burrito
on a tomato tortilla.` goes from .7074 to .4564 against Coffee. Their masks
explicitly identify bread (V165) and coffee (V652). These are not evidence that
the notes should disappear from those destinations.

The direct-premise condition adds six previously absent positive group directions:

| Proposed child → parent | Baseline | Direct | Source-grounded judgment |
|---|---:|---:|---|
| Carnivore diet → Dogs | .1678 | .8457 | Human-diet masks in N028/N041/N074 do not identify dogs. |
| Coffee → GM | .0117 | .8727 | Coffee masks alone do not express greetings. |
| Coffee → GM Nostr | .0207 | .5827 | Neither greeting nor Nostr audience follows from Coffee. |
| Coffee → Good morning | .0955 | .9559 | Associated routine, not a broader category containing Coffee. |
| Grow Nostr → Music | .0149–.4662 | .9395–.9476 | The two positive descriptions concern growing Nostr, not music. |
| Getting up → Good morning | .0609 | .6989 | Getting up is not itself a greeting; the frozen Rise group also contains rising prices. |

These were checked against the complete source groups in
`./GDR02/groups.json`. They cannot be credited as emergent
valid hierarchy relations merely because they are plausible associations.

The earlier Nostr → Music mistake also rises from .6805 to .9827. The incorrect
Beef → Carnivore diet relation rises from .6942 to .9745. A high cutoff that
retained Brisket → Beef (.9457) would not remove either of those wrong relations.
This is a concrete ordering problem, not just a calibration question.

Punctuation-only creates two new positive group directions: GM Nostr → Nostr
is a plausible community refinement, while Grow Nostr → Music is wrong. Thus
even cleaning the extra periods is not uniformly beneficial. Other positive
pairs concern alternatives of relationships already inspected in GDR02.

## Complete counts, not an accuracy claim

| Condition | Positive coverage pairs / 355 | Positive candidate pairs / 842 | Positive group directions |
|---|---:|---:|---:|
| Baseline | 212 | 18 | 13 |
| Punctuation | 222 | 21 | 14 |
| Direct premise | 225 | 28 | 18 |

Direct premise changes 20 coverage decisions from negative to positive and seven
from positive to negative. Those are decisions, not 20 successes and seven errors:
some parent descriptions have questionable scope. Every changed coverage input
was inspected; all raw scores and provenance remain available. No exhaustive
accuracy or all-negative ground truth is claimed.

## Research decision

Do not keep tuning this classifier's topic template to manufacture a hierarchy.
The useful question now is whether a method trained for **parent versus sibling
relations** can avoid the association errors. Generated subjects remain useful
context; a single seed's statement still cannot certify the whole group.

TaxoInstruct is a concrete literature lead: it jointly trains parent and sibling
generation on a disease taxonomy, then adapts to the target taxonomy. Its
construction benchmark starts with seeded levels and reports improved parent
ranking, including an ablation without parent training. That objective is closer
to the unresolved distinction than generic topic classification.[^2] But it uses
entity names and a seed taxonomy, not masked-note groups; it is not a drop-in
solution. The follow-up [SRR01–SRR03 research](./SENSE-RELATIONS.md) inspected
TaxoInstruct's released workflow and tested a smaller WordNet definition-relation
classifier instead. That model also produces false parents, including after
explicit definition inputs. TaxoInstruct itself has not been downloaded or run.

The end goal remains a repeatable complete note hierarchy. These diagnostics
do not establish a new browser candidate, automatic group naming, membership
recovery, or meaningful complete paths. The original hierarchy remains untouched.

## Reproduction

All changed inputs and scores (`./GDR03/scores.json`),
decision counts (`./GDR03/summary.json`), model and source hashes (`./GDR03/config.json`).
Every row identifies its original GDR02 pair and retains its baseline score.
All source strings and masks can be recovered from GDR02's preserved artifacts.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 \
LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib \
/tmp/oracle-nli-probe-venv/bin/python \
  sse_multivector/nli_subject_rendering.py \
  --source sse_multivector/navigation-research-v1/GDR02 \
  --cache /tmp/oracle-nli-model-cache --output /tmp/gdr03-replay-new
```

The run used two CPU threads, batch size four, 85.35 seconds of inference and
approximately 4.80 GiB peak process RSS. There was no paid compute or new model
download. The runner rejects an existing output directory. Four new tests first
failed because the implementation was absent; all 86 relevant tests now pass.
A saved-source replay into `/tmp/navigation-gdr03-reproduce` reproduces all
2,394 scores and summaries byte-for-byte. The shared scoring refactor also
reproduces GDR01's original 224 scores exactly; no baseline result was replaced.

[^1]: Moritz Laurer, [DeBERTa zero-shot model card](https://huggingface.co/MoritzLaurer/deberta-v3-base-zeroshot-v2.0#how-to-use-the-models), accessed September 11, 2026.
[^2]: Shen et al. (2025), [A Unified Taxonomy-Guided Instruction Tuning Framework for Entity Set Expansion and Taxonomy Expansion](https://aclanthology.org/2025.findings-acl.167.pdf), sections 3.1–3.4 and 4.3, [author repository](https://github.com/yanzhen4/TaxoInstruct). This is a research lead, not our experimental result.

**Selected data:** The [publication catalog](../../docs/experiments/publications.csv) lists compact pair-score results, inputs and parameters selected for release for these saved runs:

- `GDR02` — `numerical/pair-scores-73a3d2de97c2627c`.
- `GDR03` — `numerical/pair-scores-2d84a7975adb7d2d`.

These compact exports use a different format. Other cited artifacts remain separate originals.

## GDR03 study design

GDR02's coverage check rejects even `The author has just had a coffee.` for
Coffee (0.0976) and `Rosemary in sourdough bread.` for Sourdough bread (0.3299).
Its premise renderer puts complete sentences inside `This text is about ...`.
That is not the model author's demonstrated classification input: the example
uses the original sentence as premise and a topic statement as hypothesis.[^gdr03-study-design-1]

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

[^gdr03-study-design-1]: Moritz Laurer, [model card, How to use the models](https://huggingface.co/MoritzLaurer/deberta-v3-base-zeroshot-v2.0#how-to-use-the-models), accessed September 11, 2026. The author's example supplies the text unchanged and applies `This text is about {}` only to the candidate class. This motivates a controlled test; it does not prove our alternative succeeds.
