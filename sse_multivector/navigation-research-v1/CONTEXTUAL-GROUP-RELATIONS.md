# Contextual group relations

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

GDR01 recovered the shared greeting meaning of GM and Good morning when both
were replaced by source-checked descriptions. It retained the one-way relation
from Sourdough bread to Bread and proposed no relation between the other tested
group meanings. This establishes a small, useful relation-scoring result **with
manually supplied meanings**, not automatic hierarchy construction.

No source group, mask, note, vector, label or browser file changed. The existing
ND02-NP01 candidate remains the strongest packaged browser; this diagnostic is
not substituted for it.

## What changed

The [pre-run plan](./GDR01-PLAN.md) fixes eight existing MDH02 groups and the local
DeBERTa binary entailment model used earlier. Together the groups contain 149
distinct canonical masks from 37 notes. All member masks and original notes were
read before supplying these descriptions:

| Group ID | Original seed phrase | Contextual description supplied for this diagnostic |
| --- | --- | --- |
| D82879f64c8d0 | bread | bread as food |
| D57d89affb1a1 | sourdough bread | sourdough bread |
| D133882956ce9 | carnivore | the human carnivore diet |
| D3cbafae1fbeb | dog | dogs as animals |
| D0748da9782f5 | GM | greeting people in the morning |
| D9f21a0591c5a | Good morning | wishing people a good morning |
| D185749d2e92b | Coffee | coffee and coffee shops |
| De23fc8b14651 | Music | music |

The descriptions identify the common topical dimension, not everything said by
each member. Coffee includes shops because its masks discuss music, a rave and
laptop rules in coffee shops, as well as the beverage. No descriptions assert
that one tested category is a kind of another. Descriptions are experimental
inputs, not outputs produced by the tested method.

For each ordered pair, the model receives two statements. For example:

> Premise: This text is about greeting people in the morning.
>
> Hypothesis: This text is about wishing people a good morning.

The score measures the model's support for the hypothesis given the premise.
It is not cosine similarity or a calibrated probability. If the implication
holds only one way, it can suggest narrowing; if both ways, it can suggest
equivalent category meanings. Neither result automatically adopts a graph edge.

All 56 directions were scored in four conditions: both original phrases, only
the proposed child's context, only the proposed parent's context, and context
on both sides. That produces 224 scores, not 224 independent semantic examples.

## Results

In this table, the direction is **proposed child → proposed parent**, the reverse
of a browser's broad-to-narrow path. Ordinary classifier decisions use 0.5 only
for reporting; it is not a selected production cutoff.

| Direction tested | Both phrases | Child clarified | Parent clarified | Both clarified |
| --- | ---: | ---: | ---: | ---: |
| Sourdough bread → Bread | 0.995728 | 0.995728 | 0.972497 | 0.972497 |
| Bread → Sourdough bread | 0.007004 | 0.003560 | 0.007004 | 0.003560 |
| GM → Good morning | 0.003505 | 0.985307 | 0.003049 | 0.988890 |
| Good morning → GM | 0.007281 | 0.002588 | 0.991249 | 0.974966 |
| Dog → Carnivore | 0.036610 | 0.084779 | 0.000402 | 0.003968 |
| Carnivore → Dog | 0.008795 | 0.009373 | 0.120181 | 0.047978 |
| Coffee → Music | 0.000043 | 0.000062 | 0.000040 | 0.000056 |
| Music → Coffee | 0.000058 | 0.000065 | 0.000207 | 0.000271 |

**Greeting equivalence improved.** Leaving GM unexplained on either side loses
that direction of the match. Clarifying GM on the relevant side recovers it.
These are independently worded but manually understood descriptions; the model
did not learn the abbreviation or infer its sense from the original note here.

For context, these two complete originals support the shared greeting meaning:

> N099: ⟦GM⟧ happy pizza day to those who observe

> N017: ⟦Good morning⟧, crushed a solid gym session this morning to kick off the weekend. Now time for a late breakfast! #coffeechain

These are examples, not the only inspected members. All six GM masks and all
four Good morning masks, including their complete notes, remain in the saved
group evidence (`./GDR01/groups.json`). The groups have different note sets;
equivalent meanings would call for collecting their notes together, not a
redundant parent–child step.

**Bread narrowing remained intact.** The model accepts Sourdough bread → Bread
and rejects its reverse. This repeats an already available relationship; it
does not demonstrate a newly discovered parent.

**The dog/diet mismatch was not a new classifier correction.** Even the
bare-word DeBERTa condition rejects Dog → Carnivore at 0.5. Supplying the diet
meaning reduces its score, but claiming a rescued decision would confuse this
model with the earlier WordNet lookup that proposed the animal relation.

**Coffee and Music remained separate.** Their shared coffee-shop mask can
support membership in both topics. It does not make either entire group a
narrower form of the other. The contextual condition also keeps Coffee → Good
morning low, at 0.010829. This does not erase the earlier model's different
failure on a raw morning-coffee mask.

All 224 outputs were inspected. With both sides clarified, the only three
positive directions are the intended bread implication and the two greeting
directions. The other 53 directions stay below 0.5; the highest is human
Carnivore diet → Dogs, at 0.047978. These are predominantly easy cross-subject
negatives. There are only four focal relationships, so this is not evidence
of broad relation accuracy, perfect membership, or complete browsing quality.

## What the research changed

TaxoLLaMA's public release is a LoRA adapter for Llama-2-7B. Its normal
hypernym-scoring path includes the child's definition but not the parent's.
The code supports an optional target-definition mode, but the published default
does not establish performance with both group meanings. That limitation matters
for the Carnivore ambiguity. No TaxoLLaMA weights were loaded or run.[^1]

HyperDef explicitly compares both terms and both definitions. It also identifies
a pitfall: inferring an entire dictionary definition is not equivalent to
recognizing a broader concept. Its maximum over all available senses would
likewise admit irrelevant senses for our fixed groups. These findings support
the input comparison, not treating an unchanged entailment model as HyperDef or
as an already qualified taxonomy builder.[^2]

GDR01 therefore reuses the installed local model and compares **topical
statements**, not one original note's claims against another note's claims.
The neural weights and settings stay fixed, isolating the supplied language.

## Next component and a concrete warning

The next construction problem is obtaining faithful group meanings without
hand-writing them. Existing subject-generation outputs may supply candidate
meanings, avoiding a new generator. For example, the GM seed V914 already has
the frozen subject `A good-morning greeting.`; the Carnivore seed V332 has
`A carnivore diet.` These were not GDR01 inputs.

But one seed's subject cannot automatically describe every mask in its group.
Inspection of the unchanged MDH02 Rise group D807b030c4cd6 reveals:

> N052: ⟦Rise⟧ and grind coffee beans

V409's generated subject is `Getting up.` Other masks from that note also select
the grinding words. The same group contains this complete different note:

> N062: https://www.moreechampion.com.au/images/transform/v1/crop/frm/233370197/11fc5f7b-4786-4e6c-8038-65d475e49320.png/r61_53_958_524_w1200_h630_fmax.jpg
>
> ⟦Aussies' Christmas lunch costs rise⟧: budget-friendly tips | Moree Champion
>
> https://www.moreechampion.com.au/story/8811317/aussies-christmas-lunch-costs-rise-budget-friendly-tips/

V519's generated subject is `Rising costs of Christmas lunch for Australians.`
The shared word does not make Getting up a faithful description of that mask.
This is a grouping problem, not a reason to invent a broader label that hides it.
The source subjects already distinguish the two meanings. The completed
[GDR02 follow-up](./EXISTING-SUBJECT-RELATIONS.md) exposes this mixture and recovers
greeting equivalence using those existing outputs, but also finds incorrect
relations and coverage decisions. [GDR03](./SUBJECT-INPUT-RENDERING.md) isolates
input formatting: some matches improve, while associated-topic errors remain or
increase. A seed subject is still not automatically a description of the whole
group. No automatic grouping or parent method is established by these tests.

## Reproduction and integrity

[Frozen inputs](./GDR01/fixture.json), every score (`./GDR01/scores.json`),
classifier disagreements (`./GDR01/summary.json`), configuration (`./GDR01/config.json`).
The eight saved groups are exactly equal to their LGR01 inputs, including all
source notes and masks. Nothing was removed to improve the result.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 \
LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib \
/tmp/oracle-nli-probe-venv/bin/python \
  sse_multivector/navigation-research-v1/GDR01/group_description_relations.py \
  --groups sse_multivector/navigation-research-v1/LGR01/groups.json \
  --fixture sse_multivector/navigation-research-v1/GDR01/fixture.json \
  --cache /tmp/oracle-nli-model-cache --output /tmp/gdr01-reproduction
```

The output path must not exist. A saved-source replay produced byte-identical
scores, summaries and group evidence. Configuration records pinned model and
package versions, input/source hashes and raw logits. Execution used two CPU
threads and batch four; inference took 7.145 seconds. No paid inference, training
or model download occurred. The raw process high-water RSS is recorded, not
interpreted as an isolated model-memory measurement.

Four new production-path tests initially failed because the runner was absent;
they now pass together with 73 existing regression tests. These 77 tests verify
implementation behavior, not semantic correctness. The semantic inspection and
the complete saved-source replay are separate checks.

One preliminary launch was interrupted after a patch failed to apply the planned
shorter bread descriptions. It had begun scoring but emitted and saved no
scores, and created no result directory. The input correction and its SHA-256
`ae8c5784fe91b0413bf8c7e61af3578c6d37f6e46adaa3bdd13a0059215ebf14`
were verified before the completed run. No result-informed input revision or
discarded completed result is hidden by the reported comparison.

## Sources

[^1]: Moskvoretskii et al. (2024), [TaxoLLaMA](https://aclanthology.org/2024.acl-long.127/); [pinned author prompt code](https://github.com/VityaVitalich/TaxoLLaMA/blob/7881f9fd26c4ab935d98ffce0fac91eb1fac621c/pipeline_src/dataset/prompt_schemas.py), [scoring code](https://github.com/VityaVitalich/TaxoLLaMA/blob/7881f9fd26c4ab935d98ffce0fac91eb1fac621c/TExEval-2_testdata_1.2/est_ppl.py), [adapter configuration](https://huggingface.co/VityaVitalich/TaxoLLaMA/blob/16eee40bf4205c1de762711fff1b907590cf5fd4/adapter_config.json).
[^2]: Yin and Roth (2018), [Term Definitions Help Hypernymy Detection](https://aclanthology.org/S18-2025.pdf), sections 3–4. Read for both-sided definitions, training, ablations and error mechanisms; not reproduced here.

**Selected data:** Compact pair-score results, inputs and parameters for `GDR01` are selected for release as `numerical/pair-scores-3e12777c9a08d409` in the [publication catalog](../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.
