# Relations between mask groups

LGR01 found two lexical parent proposals among the 22 frozen MDH02 groups.
One repeats Bread → Sourdough bread. The other uses the animal meaning of
Carnivore to propose Carnivore → Dog, although the existing Carnivore group
discusses the human diet. Neither supplies a new defensible browsing edge.
No group, mask, note membership, SSE vector or browser artifact was changed.

## Question and method

Can explicit broader-term and synonym relations supply useful group relationships
that literal word inclusion misses? The [pre-run plan](./LGR01-PLAN.md) fixes the
question and diagnostic expectations. This is a proposal-component experiment,
not a test of a finished hierarchy.

MDH02 has 22 groups representing 53 of the 100 source notes. Each group originated
from a complete source mask and contains masks matching that mask's word features.
For LGR01, each original seed phrase is looked up in WordNet 3.0. Its source word
order is retained: `sourdough bread`, not the alphabetically sorted feature list
`bread sourdough`. No generated category name or generated subject is an input.
Case and whitespace are normalized; words and hashtag markers are not removed.

Every available sense is retained. The algorithm examines all 462 ordered pairs:

- An explicit hypernym path supplies a possible broader–narrower relationship.
- A shared sense supplies possible equivalence, separately from parentage.
- A shared ancestor alone supplies neither relationship.
- Missing terms or links remain unresolved, not declarations of unrelatedness.

The model-free lookup sees seed phrases, **not the group's complete meaning**.
That limitation is intentional and exposed: every proposal must subsequently be
checked against all member masks and original notes. No proposal is automatically
adopted. WordNet distinguishes senses and relation types; these are not cosine
scores or similarity cutoffs.[^1]

## Every proposed parent

| Proposed parent | Proposed child | Lexical evidence | Inspection |
| --- | --- | --- | --- |
| D82879f64c8d0 · Bread | D57d89affb1a1 · Sourdough bread | `sour_bread.n.01 → bread.n.01` | Defensible, but already present in MDH02. |
| D133882956ce9 · Carnivore | D3cbafae1fbeb · Dog | `dog.n.01 → canine.n.02 → carnivore.n.01` | Wrong meaning for the existing parent group. |

### Bread and sourdough bread

The child contains ten canonical masks from N015 and N037. All discuss preparing
or describing sourdough bread. The parent contains 51 masks from eight notes,
including those two notes and other bread types, ingredients, recipes and baking.
Both groups' full masks and all original notes were inspected. The path is a
recognizable narrowing, but the lexical lookup adds no new reachable note here.

Two complete child notes, with representative masks:

> N015: How to spend some moments: Preparing ⟦sourdough bread⟧.
>
> https://z428.micro.blog/uploads/2024/abcd7a949e.jpg https://z428.micro.blog/uploads/2024/abcd7a949e.jpg

> N037: #foodstr
> Cranberry , rosemary , brown sugar and cinnamon ⟦sourdough bread⟧ , good lord it soo good https://image.nostr.build/cb6f56072bd4957a92c9f13a54444b0472c9ec071483b8dee2407469509d3ff0.jpg https://image.nostr.build/0b31d68d6792f6c7c54d5137a38880d68fdad1ccef9d760be02084141bb7a750.jpg https://image.nostr.build/ee8911a263955cf26e737a57d5abe0389a60623c89fcd97aa4855f43f584dfbd.jpg

### Carnivore and dog

All seven Carnivore masks come from N028, N041 and N074. They concern a human
diet or commentary about it. For example, V679 selects `stir controversy` and
`carnivore diet` from this complete N074 note:

> The #nostr diet is boring. It doesn’t generate clicks like the #plantbased diet. It doesn’t ⟦stir controversy⟧ like the #⟦carnivore diet⟧…
>
> Unless, of course, you’re 10 and your mom tells you to eat your veggies.
>
> Tired of the bitcoin carnivore narrative.
>
> Eat real food. Not too much. Mostly plants. #FoodRules (Michael Pollan)

The five Dog masks come from N048 and N100. Four discuss scraps or meat for a
dog; one is a bare dog hashtag. They do not refine the human diet discussed by
the existing parent. Calling that parent “all meat-eating animals” would change
its interpretation to accommodate the proposed child, not validate the original
relationship. A separately justified broader category remains possible.

The dictionary's animal relation is not itself erroneous. Its transfer to these
fixed groups is unsupported. Complete notes and every mask for both groups are
retained in [groups.json](./LGR01/groups.json); the original N100 and N048 were
also inspected, not inferred from the short words.

## Missed and unresolved relationships

**Greetings:** the six GM masks address people or Nostr audiences; the four Good
morning masks are greetings too. All ten original notes were inspected. WordNet
returns only the unit of mass for `gm`, while `good_morning` has a greeting
sense. `gm_nostr` is absent. The lookup cannot establish their shared greeting
meaning. Choosing among the returned GM senses cannot fix a missing greeting
sense; a closed-inventory word-sense model alone would not fix it either.

**Brisket and beef:** all seven Brisket masks describe smoking brisket, across
N019 and N085. All 21 Beef masks concern beef food, preparation or scraps,
across four other notes. WordNet places brisket below a cut of meat, and beef
below meat; it does not place brisket below beef. These source notes do not name
the animal behind their brisket. Beef → Brisket remains a plausible contextual
browsing hypothesis, not a universal lexical fact established by this run. An
absent link is not scored as an algorithmic false negative against invented gold.

**Coffee and music:** no parent relation is proposed. The complete music masks
are a Music hashtag and a statement about music playing in a coffee shop. Shared
setting does not make either subject a narrower form of the other. This is a
useful negative control, but sparse output alone is not high precision.

Seven entire group phrases have no dictionary match: Bitcoin, Coffeechain,
Happy pizza day, GM Nostr, Grownostr, Nostr and Plebchain. Another important case,
GM, matches a dictionary entry with the wrong sense for these notes. Ten of the
fifteen matched groups have more than one sense available. A dictionary hit is
therefore not evidence that its meaning was understood.

There are no equivalence proposals. The experiment did not produce any new
audited parent edge. It does not establish that a learned relation model,
context-sensitive matching, or broader proposal vocabulary would fail.

## What the literature contributes

Woods' conceptual indexing combines lexical knowledge with phrase structure,
source locations and subsumption. Its relevance is the explicit separation of
generality from ordinary association—not a claim that this lookup reproduces
its system. LGR01 omits its morphological, compositional and knowledge-based
interpretation machinery.[^2]

RelBERT is a released RoBERTa-based **relation embedding** model: an ordered word
pair is inserted into a template and encoded. It learns to bring pairs expressing
similar relations together. Its lexical-classification experiments additionally
train a classifier; a pair embedding alone is not a broader/equivalent verdict.
The available base checkpoint uses noise-contrastive training on SemEval-2012
relational examples. It offers a learned signal beyond dictionary lookup, but
does not directly establish the meaning of a whole mask group.[^3]

Pitarch et al. fine-tune BERT/RoBERTa for lexical-relation classification and graded
entailment. Their study supports simple input templates after task-specific
training, not prompting an unchanged base model as if it were already trained.
Synonymy and domain dependence remain problems, and their error analysis includes
misleading benchmark labels. Their published weighted F1 is not evidence of
correct note-category parentage. The inspected repository supplies training and
evaluation code; a ready group-level classifier was not found there.[^4]

TaxoLLaMA explicitly conditions broader-term generation and directional scoring
on a term **and its definition**. It is Llama-2-7B fine-tuned on WordNet noun/verb
edges using QLoRA. Its use of definitions directly addresses an input gap exposed
here. However, converting a group of masks into a faithful definition is another
assumption; its published taxonomy errors also include overly broad parents.
Neither its weights nor RelBERT's weights were run in this experiment.[^5]

ConSeC selects a target word's definition using its surrounding text and senses
assigned to nearby words. It motivates contextual interpretation, but its fixed
sense inventory cannot by itself supply the missing GM greeting or an absent
human-diet sense. It was inspected as a possible response to LGR01's failure,
not installed or tested.[^6]

## Consequence for the next experiment

Do not tune WordNet lookup, choose its first sense, or adopt these lexical
proposals as browsing edges. The useful next comparison is **bare phrase versus
source-grounded meaning with a directional relation method**, holding the groups
fixed. Include the greeting equivalence, human-diet/animal distinction, ordinary
bread refinement and merely associated coffee/music examples. Judge all masks,
not only a conveniently matching member or a model-generated description.

TaxoLLaMA's definition-conditioned method is the closest inspected fit for that
comparison; its model availability, safe local execution and the fidelity of the
conditioning text need verification before a run. RelBERT is an alternative
lexical signal, not a reason to substitute another generic relevance benchmark.
No new learned-model run, definition-generation prompt or classifier is approved
as a production component by this record.

## Reproduction and verification

Runner: [mask_group_lexical_relations.py](../mask_group_lexical_relations.py).
[Every pair](./LGR01/relations.json), [complete group evidence](./LGR01/groups.json),
[selected dictionary entries and ancestors](./LGR01/lexicon.json),
[configuration](./LGR01/config.json).

Original lookup used NLTK 3.9.2 and the WordNet 3.0 archive at NLTK-data commit
`96f9b3252457a2b97e52aec64c3dfceeb5c312d5`, SHA-256
`cbda5ea6eef7f36a97a43d4a75f85e07fccbb4f23657d27b4ccbc93e2646ab59`.[^7]
No paid compute, remote inference, model training or neural model loading occurred.
The archived lexical records allow replay without NLTK or a download:

```sh
python3 sse_multivector/navigation-research-v1/LGR01/mask_group_lexical_relations.py \
  --groups sse_multivector/navigation-research-v1/MDH02/descriptions.json \
  --evidence sse_multivector/geometric-hierarchy-v1/GDC09/evidence.json \
  --lexicon sse_multivector/navigation-research-v1/LGR01/lexicon.json \
  --output /tmp/lgr01-reproduction --run-id LGR01
```

An independent offline replay produced byte-identical relations, groups and
lexical records. All 462 ordered pairs and every unchanged group member were
checked against the source inputs. Five new production-path tests and 68 existing
regression tests pass. Tests establish implementation behavior, not semantic
correctness; the two proposals were inspected separately above. The goal and
the existing ND02-NP01 browser candidate remain unchanged.

## Sources

[^1]: Princeton University, [WordNet structure and relations](https://wordnet.princeton.edu/). NLTK, [WordNet interface](https://www.nltk.org/howto/wordnet.html).
[^2]: William A. Woods (2000), [Conceptual Indexing: Practical Large-Scale AI for Efficient Information Access](https://cdn.aaai.org/AAAI/2000/AAAI00-215.pdf), conceptual indexing and subsumption sections.
[^3]: Ushio et al. (2021), [Distilling Relation Embeddings from Pretrained Language Models](https://aclanthology.org/2021.emnlp-main.712/), methods and training; [author implementation](https://github.com/asahi417/relbert); [base checkpoint training configuration](https://huggingface.co/relbert/relbert-roberta-base/blob/1091843cb232d52ddde18634471f5fe3125eaff8/finetuning_config.json).
[^4]: Pitarch et al. (2023), [No clues, good clues: Out of context Lexical Relation Classification](https://aclanthology.org/2023.acl-long.308/), sections 4–7; [author code](https://github.com/sid-unizar/LRC).
[^5]: Moskvoretskii et al. (2024), [TaxoLLaMA: WordNet-based Model for Solving Multiple Lexical Semantic Tasks](https://aclanthology.org/2024.acl-long.127/), sections 3–5; [author code](https://github.com/VityaVitalich/TaxoLLaMA).
[^6]: Barba et al. (2021), [ConSeC: Word Sense Disambiguation as Continuous Sense Comprehension](https://aclanthology.org/2021.emnlp-main.112/), task and method sections; [author code](https://github.com/SapienzaNLP/consec).
[^7]: NLTK-data, [pinned WordNet archive](https://raw.githubusercontent.com/nltk/nltk_data/96f9b3252457a2b97e52aec64c3dfceeb5c312d5/packages/corpora/wordnet.zip). WordNet 3.0 is an older fixed vocabulary, not a current slang inventory.
