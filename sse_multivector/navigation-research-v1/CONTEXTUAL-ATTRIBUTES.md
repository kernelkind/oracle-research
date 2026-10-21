# Contextual attributes for category construction

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

CSA01 checks whether contextual word senses could replace CAP02's literal word
features. Correct senses can add useful abstractions, but they do not supply
the complete meaning of a masked phrase or all legitimate topical relationships.
No word-sense model was run, and no new hierarchy is adopted.

The practical decision is to retain word senses as a possible supplementary
source of attributes, not select a sense-only construction pipeline. Research
on structured phrase generalization is more directly aligned with the remaining
representation question. It is a lead, not an implemented or validated solution.

## What the models actually learn

| Method | Native input and training | Meaning of its output | Fit here |
| --- | --- | --- | --- |
| Gloss-informed bi-encoder, BEM | A target word in its sentence; separate candidate dictionary definitions. Two BERT-base encoders trained jointly on 226,036 SemCor annotations with a word-sense classification loss. | Highest-scoring candidate sense for that word. | Directly relevant to word ambiguity, not a classifier for whole mask meanings or parent categories. |
| ConSeC | A marked word, its context, candidate definitions and definitions assigned to nearby words. DeBERTa-large trained to select the correct candidate definition. | A contextual sense choice, conditioned on earlier choices. | Uses the right kind of source context, but still selects from a supplied sense inventory. |
| SPLADE | Query and passage text; vocabulary-sized weights learned for retrieval with sparsity regularization. | Features useful for ranking relevant passages. | A vocabulary coordinate is not guaranteed to mean that literal subject. It cannot be adopted as a faithful category attribute without separate evidence. |

BEM reports 79.0 F1 on its combined English WSD evaluation, including the
development set; its less-frequent-sense score is 52.6. These are word-sense
results, not note-membership accuracy.[^1] ConSeC's released SemCor checkpoint
reports 82.0 on ALL. Its interactive code accepts a token position and candidate
definitions, constructs a `ConsecSample`, and returns scores for definition
positions. It does not return a phrase graph or category relationships.[^2][^3]

This is a better input match than SRR's classifier for pairs of dictionary
definitions: original source sentences are native WSD inputs. However, an
informal Nostr post is still a transfer from the evaluated data, and candidate
inventory coverage remains a separate limitation. Neither checkpoint has been
downloaded or evaluated here. Their released code also uses older dependencies
and noncommercial licenses; no deployment decision follows from this review.

SPLADE was considered because expanded terms might provide missing broad
subjects. But controlled retraining shows useful retrieval with stopword-only,
random and artificial output vocabularies.[^4] A newer dissection finds that
apparently unrelated expansion tokens can contribute to ranking, particularly
in-domain.[^5] These findings do not invalidate SPLADE retrieval. They defeat
the shortcut of treating a high-weight token as an established semantic property
of the source. No SPLADE model or cutoff was tested.

## Source audit

The [plan](CONTEXTUAL-ATTRIBUTES.md#csa01-study-design) preceded the new lookup. All twelve queries and 227
returned senses/ancestors are saved in the lexical record (`./CSA01-lexicon.json`).
The ten exact masks and complete original notes are in
the source record (`./CSA01-sources.json`). Source texts were inspected, not
reconstructed from labels. The interpretations below are diagnostic judgments,
not model outputs or manual repairs to the corpus.

### Dinner and the two uses of hit

N007/V052:

> ⟦dinner⟧ ⟦Lamb with steamed seasoned broccoli and baby potatoes really hit the spot⟧

N039/V304:

> ⟦Next⟧ ⟦storms look like they will hit⟧ ⟦grilling out dinner⟧

The weather sense `hit.v.05` is available. The whole expression `hit_the_spot`
has no entry. Individual `hit` has numerous other senses, including reaching
a goal, but none explicitly supplies the idiom's satisfied-appetite meaning.
A broad goal-reaching interpretation might still be usable; the audit does
not declare that a model must fail on this note.

The concrete limitation is that selecting a sense of the isolated word does
not itself normalize the idiom to meal satisfaction. Both source uses are
verbs, so distinguishing noun from verb cannot resolve this pair. A WSD run
could test its choice among available senses, but not demonstrate recovery of
a missing phrase meaning merely by choosing a different sense from the storm.

### The two uses of experience

N065/V561:

> ⟦Coffee shop⟧ ⟦Felt like changing their router/ap passwords so they⟧ ⟦experience⟧ ⟦freedom from internet⟧

N094/V852:

> ⟦Decafe coffee drinkers⟧ ⟦for the experience⟧

N065 contemplates cafe staff experiencing loss of internet. N094 discusses
the experience of drinking decaf. WordNet has separate verb and noun candidates.
Simply retaining part of speech would separate these exact feature keys.
Therefore, a model separating this pair would not establish that it resolved
the attachment of the experience to internet deprivation versus coffee drinking.

Correct word senses also do not encode those participants and relationships
as output. That information remains in the source phrase. This does not make
either note unrelated to coffee, and it does not prohibit another defensible
shared category; it limits what the proposed attributes can establish.

### Chickens, chicken meat and chicken stock

N080/V733:

> ⟦Our chickens⟧ ⟦laying an egg a day⟧

N013/V097:

> ⟦chicken stock⟧ ⟦I’ll pressure can⟧ ⟦store in the pantry⟧

N026/V205:

> ⟦rotisserie chickens⟧ ⟦made over a half gallon of chicken stock from the bones⟧

Lookup normalizes the plural: `chicken` and `chickens` share the same noun
candidate inventory. That addresses spelling variation before learned sense
selection. But the meat and living-bird senses are different. Their only shared
hypernym ancestors in this lookup are `physical_entity.n.01` and `entity.n.01`.
The complete phrase `chicken_stock` maps to a broth sense beneath soup, not
beneath either chicken sense.

This is a valid distinction in an object taxonomy. It does not supply a
Chicken-related browsing topic spanning birds, meat and stock. Such a topic
is possible, not mandatory: a hierarchy could reasonably place those notes
under different useful destinations. The result therefore limits a sense-only
representation's range; it is not a failed comparison against a prescribed
correct tree. Keeping both broader topical associations and precise senses
would require an explicit construction rule, not silently treating them as
the same relation.

### Bread, rosemary and food

N015/V107:

> ⟦sourdough bread⟧

N037/V290:

> ⟦rosemary⟧ ⟦sourdough bread⟧

N072/V665:

> ⟦Irish soda bread⟧ ⟦I added fresh rosemary and cranberries⟧

The dictionary supplies paths from sourdough bread through bread to food.
The culinary rosemary sense also reaches food through herb, flavoring and
ingredient concepts. These are usable sources of unstated broad attributes;
CAP02's literal features could not obtain them. `soda_bread` has no complete
entry, although the word `bread` does.

Neither ancestor chain establishes that the rosemary is an ingredient of the
particular bread. N037 expresses the combination within a noun phrase. N072
expresses it across sentences using `it` in the complete source. CAP02's
co-occurrence happened to preserve this valid combination. Replacing it with
adjacent phrases or isolated sense IDs would not establish an equally capable
representation. The distinction to investigate is a common relationship despite
different wording and syntax—not merely whether the two words can be recognized.

### Known inventory control

LGR01 already found no greeting sense for `gm`. Choosing among its available
dictionary senses cannot manufacture the missing one. That evidence is retained
from [LGR01](./GROUP-RELATIONS.md), not counted as a new CSA01 discovery. A
fallback for unknown words or meanings remains necessary if WSD is used.

## Construction consequences

The audit separates four mechanisms that a single apparent improvement could
otherwise conflate:

- Normalization can unite singular/plural spellings.
- Part of speech can separate the two observed experience uses.
- Sense selection can distinguish meanings represented in an inventory.
- Phrase interpretation must retain how the words relate, including meaning
  distributed across fragments and sentences.

Replacing word features with sense IDs and hypernyms addresses only part of
the problem. Adding source words back would preserve more topical possibilities,
but would also preserve the original ambiguity; that is not a demonstrated fix.
Conversely, a correct dictionary distinction is not automatically a desirable
separation of browsing topics. The testbed does not define one required taxonomy.

No model run is warranted merely to verify that `experience` has two parts of
speech or that bread has a food ancestor. Those questions are now answered by
source inspection and the fixed lexical data. WSD remains a plausible later
component when the construction has a defined use for its outputs. This is a
decision not to select the sense-only route, not a claim that WSD is ineffective.

## Structured phrase research

Woods' conceptual indexing is a closer complete-construction precedent: it
combines source positions, morphology, lexical relations and structured phrase
subsumption. Its comparison of automobile cleaning with car washing aligns
the corresponding components instead of intersecting bare word sets. But it
also explicitly needs a relaxed passage-matching mechanism when meaning is
distributed beyond extracted phrases. Its retrieval results do not certify
all parent–child memberships in a note browser.[^6]

Pattern structures generalize FCA from binary attributes to structured
descriptions. Leeuwenberg et al. compare sets of rooted syntax trees using
maximal common subtrees and project them to branches to reduce computation.
This offers a concrete way to preserve relationships in the common description.
However, their actual experiment classifies preidentified drug pairs in medical
sentences; it does not build an open-ended browsing hierarchy. The best reported
F1 in Table 2 is 0.39894, and the authors show losses from simplifying away
important context. Its formalism is a lead, not evidence that a syntax parser
will solve our task.[^7]

A dissertation combining FCA and WordNet assesses reductions in lattice size
and explicitly leaves the quality of removed concepts unconfirmed. It does not
justify adopting a synonym/hypernym replacement or frequency threshold merely
because it produces a smaller structure.[^8]

The subsequent [CAP03 construction control](./SUBJECT-DESCRIPTION-CONSTRUCTION.md)
first checks the already-generated per-mask subject descriptions. It recovers
some abstractions, but finds both lost attachments and explicit combinations
excluded by the candidate seed rule. That omission alone does not justify adding
another context extractor: the common meaning is already expressed. The following structured-description question remains open,
but is no longer grounds for selecting a parser as the immediate next action.

A discriminating investigation is whether a bounded, source-grounded
structured description can preserve useful shared phrases and relationships
across our different source constructions. Before selecting a parser, define
the output and check its expressiveness on the saved masks: distinguish a shared
relationship from two words co-occurring, retain valid dispersed evidence,
and permit broad topics without declaring every relation to be object `is-a`.
Only then test automatic extraction against that defined use. No parser,
pattern-mining implementation, or new extraction prompt is selected here.

That investigation must still connect to the complete construction: recovering
broader attributes, constructing candidates, assigning masks, and selecting
useful note-level choices. It must not become an open-ended project to parse
every logical detail of every post. Fine-grained claim polarity and a unique
taxonomy are not added requirements.

## Reproduction and verification

The audit uses the existing production WordNet lookup, not a new implementation.
Run from the repository root using the existing local environment and pinned
archive; output is JSON to standard output:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
/tmp/oracle-nli-probe-venv/bin/python -c '
import sys, json
from pathlib import Path
sys.path.insert(0, "sse_multivector")
from mask_group_lexical_relations import load_wordnet
queries = {"hit", "hit_the_spot", "experience", "chicken", "chickens",
           "chicken_stock", "stock", "bread", "sourdough_bread", "soda_bread",
           "rosemary", "food"}
print(json.dumps(load_wordnet(queries, Path("/tmp/navigation-wordnet-data")),
                 ensure_ascii=False, indent=2))'
```

`./CSA01-result.json` records source/module hashes and the
selected ancestor paths. `./CSA01-sources.json` preserves
complete original text, exact mask fragments and byte spans for ten masks from
ten notes. Every saved source range is checked against GDC09; the lookup and
paths are replayed against the existing production functions. These checks
verify the audit data, not automatic semantic performance.

No source mask, vector, category membership, hierarchy or browser default changed.
No learned model, paid compute or remote inference was used. The two pre-existing
The overall hierarchy goal is incomplete.

## Sources

[^1]: Blevins and Zettlemoyer (2020), [Moving Down the Long Tail of Word Sense Disambiguation with Gloss Informed Bi-encoders](https://aclanthology.org/2020.acl-main.95.pdf), sections 3–5 and Tables 1–2; [released code and training instructions](https://github.com/facebookresearch/wsd-biencoders).
[^2]: Barba, Procopio and Navigli (2021), [ConSeC: Word Sense Disambiguation as Continuous Sense Comprehension](https://aclanthology.org/2021.emnlp-main.112.pdf), sections 3–4.
[^3]: SapienzaNLP, [ConSeC release and native interactive inputs](https://github.com/SapienzaNLP/consec); [prediction implementation](https://github.com/SapienzaNLP/consec/blob/main/src/scripts/model/predict.py), inspected 2026-09-11.
[^4]: Mackenzie, Zhuang and Zuccon (2023), [Exploring the Representation Power of SPLADE Models](https://arxiv.org/html/2306.16680), controlled-vocabulary experiments and Table 2.
[^5]: Polyakov, Scells and Eickhoff (2026), [Understanding Wacky Weights: A Dissection of SPLADE’s Learned Term Importance](https://arxiv.org/html/2605.19628v1), sections 4–5.1. Their proposed explanation of dataset-specific overfitting remains a hypothesis; this record relies on the observed ranking contributions, not that causal conclusion.
[^6]: Woods (2000), [Conceptual Indexing: Practical Large-Scale AI for Efficient Information Access](https://cdn.aaai.org/AAAI/2000/AAAI00-215.pdf), conceptual indexing, passage retrieval and evaluation sections.
[^7]: Leeuwenberg, Buzmakov, Toussaint and Napoli, [Exploring Pattern Structures of Syntactic Trees for Relation Extraction](https://publications.hse.ru/pubs/share/folder/x9m9ofrdni/163919667.pdf), sections 2–6, especially the actual classification task, branch projection, context-loss example and Table 2.
[^8]: [Ontology Learning Using Formal Concept Analysis and WordNet](https://arxiv.org/pdf/2311.14699), dissertation posted to arXiv in 2023, sections 4.5, 5.2–5.4 and conclusions. Only the relevant method/evaluation sections were inspected; it is not treated as validation of semantic navigation quality.

## CSA01 study design

### Question

Would replacing CAP02's word features with correctly chosen contextual word
senses and their dictionary ancestors supply the missing construction capability?
This is an audit of that representation before selecting or running a model.
It is not an evaluation of automatic word-sense disambiguation.

The proposed full route is: interpret mask-supported words in their original
contexts; attach their sense IDs and broader dictionary concepts to each mask;
construct recurring shared attributes and inclusion relations; then select
useful note-navigation choices. Per-occurrence interpretation and dictionary
lookup are not intrinsically unscalable. Whether this route retains phrase
meaning and supplies useful topical parents remains unproven.

### Evidence and controls

Keep GDC09 and CAP02 unchanged. Use the existing pinned WordNet 3.0 archive and
the production lookup in `mask_group_lexical_relations.py`. Save every queried
sense and ancestor, not only a preferred answer. Inspect complete source notes
and their exact masks. Human interpretation identifies plausible senses for
this diagnostic only; it must not become repaired corpus annotations.

Inspect these already documented mechanisms, selected before new lookup:

1. N007/V052 and N039/V304: the two uses of `hit`. Query both the word and
   `hit the spot`; check whether the required distinction exists in the inventory.
2. N065/V561 and N094/V852: `experience` in the cafe-retaliation and decaf
   masks. Check whether part of speech alone already separates the uses.
3. N013/V097, N026/V205 and N080/V733: chicken stock and egg-laying chickens.
   Check normalization separately from the meat/bird distinction and inspect
   whether dictionary ancestry actually supports a shared topical destination.
4. N015's sourdough-bread mask, N037/V290 and N072/V665: inspect the paths
   from bread types and culinary rosemary to food. Distinguish broader lexical
   concepts from the relationship that rosemary is added to bread.
5. Retain the established LGR01 missing greeting sense for GM as an inventory
   control. Do not rerun that lookup as though it were a new discovery.

### Hypothesis and competing explanations

The hypothesis is that contextual senses plus their ancestors can supply
meaningful new abstractions while resolving CAP02's observed word ambiguity.
Competing explanations are that grammatical tagging already explains an apparent
gain; the needed sense is absent; or correct word senses still omit the relation
required to describe a group. A dictionary animal/meat split might also remove
a legitimate cross-sense topic rather than improve discovery.

For each example, record what literal features preserve, what sense IDs could
add, and what neither represents. An ancestor path establishes a dictionary
relation only, not correct membership of every original mask in a browsing
category. A missing path is not a judgment that two notes are unrelated.

### Decision consequences

Would either outcome change the next decision? Yes. If the inventory supplies
the needed distinctions and abstractions without losing the established topical
links, a small native-context WSD test becomes justified. If it cannot, do not
spend a model run testing a representation that already lacks the needed output.
Instead identify whether senses should be optional attributes, whether a
compositional representation is necessary, or whether this route should stop.

This audit cannot establish extraction accuracy, end-to-end category quality,
coverage over all notes, or a preferred taxonomy. Do not package a browser from
it. The decision concerns the role and adequacy of the proposed representation,
not whether a particular checkpoint is competent.
