# Mapping repair and source meaning

The literature and released resources do not justify replacing SGC03's mappings
with a supposedly verified table, or adding a general mapping classifier now.
The available correction release changes the ontology as well as its mappings;
the learned methods examined recover supplied ontology relationships rather than
independently certify their meanings.

The source audit also changes the research priority. Some earlier objections
were about formal object types, not bad note discovery. Other errors genuinely
create unsupported destinations, but often begin with the parser choosing the
wrong dictionary sense. Those mechanisms must remain separate.

This is a research and dependency audit, not SGC04 or a new hierarchy condition.
The original notes, masks, descriptions, source graphs, SGC03 results, GDC09
baseline and browser remain unchanged. No classifier was trained or run.

## The question being investigated

[SGC03](./ONTOLOGY-CONSTRUCTION.md) added useful candidate Food → food/process →
preparation/preservation/cooking paths. It also produced questionable additional
meanings. The consequential question was whether an existing general treatment
could reduce those wrong meanings while retaining the useful paths.

Three explanations can coexist:

- The source graph selects the wrong meaning of a word.
- The selected meaning is mapped to an inappropriate ontology concept, or its
  mapping is interpreted incorrectly.
- A formally questionable derivation nevertheless leads to a reasonable topic
  for the note. Rejecting it solely for its formal type would overstate the
  discovery problem.

Mapping repair alone cannot distinguish or solve all three. Nor does a smaller
candidate inventory demonstrate better browsing.

## What the literature supplies

### Typed interpretation

Álvez, Lucio and Rigau distinguish mappings to ordinary classes, individual
attributes and classes of attributes. An object can belong to a class and have
an attribute; these are not interchangeable subclass statements. Their first
translation introduces a separate attribute variable when needed. The paper
constructs ontology-reasoning questions, not note categories, and explicitly
balances stronger assertions against usable coverage.[^typed]

This explains why SGC03's declared-class test is insufficient. It does not show
that all attribute-related topics should be removed. A chef can be relevant to
occupations without the person literally being an occupation.

### Existing semantic corrections

The 2023 correction study inspected 200 basic-level WordNet concepts, changed
50 mappings, then propagated corrections only through descendants sharing the
original mapping. That affected 3,883 mappings. Additional authored rules target
organism/group confusions. The work combines expert interpretation with
automatic propagation; it is not a learned semantic validator. Its reported
precision concerns validation of meronymy questions, not independently measured
mapping accuracy or navigation quality. The best reported intervention changes
both mappings and ontology knowledge.[^correction]

Its release is worth inspecting before building another component. The actual
compatibility check is below; the label “corrected” is not treated as a guarantee.

### Repair without throwing away all useful consequences

Li and Lambrix weaken a rejected subclass assertion by specializing its source,
generalizing its target, or both. A completion step can restore additional
correct consequences. However, a domain expert who judges candidate axioms is
an explicit input. Their experiments use ontology networks, not informal text
or autonomous category generation.[^weakening]

This offers a useful operation, not the missing correctness judgment. Even
candidate availability is uneven in SGC03: ShipContainer has Container above
it, whereas Food's only immediate named superclass is SelfConnectedObject.
Moving upward cannot preserve a useful generic-food meaning in that latter
case. These are observations about the pinned resource, not accepted repairs.

### Learned alternatives and their actual supervision

| Method | Inputs and computation | Evaluation and limitation for this decision |
| --- | --- | --- |
| BERTSubs | Fine-tunes BERT-base on an ontology's declared positive subclass pairs and sampled negatives. Inputs contain class labels, optionally neighboring paths or breadth context. Cross-ontology training uses each ontology's internal relationships. | On HeLiS–FoodOn, the path-context condition reports MRR 0.629 and top-one accuracy 0.481, ranking against roughly 41 negatives per query. The target relationships derive from curated equivalences and target parents. This supports supervised relationship prediction, not independent validation of erroneous WordNet–SUMO mappings.[^bertsubs] |
| OntoLAMA | Turns ontology expressions into premise/hypothesis sentences and probes or fine-tunes RoBERTa using entailed positives and assumed-disjoint negatives. | Under its prompts, zero-shot ontology results trail ordinary NLI; task-specific examples help. The labels still depend on supplied ontology semantics. This is a useful task-fit warning, not evidence that another generic entailment pass would repair SGC03.[^ontolama] |
| InME/CoME with self-matching | Builds word–annotation occurrence matrices, compresses them with an autoencoder, and trains a random forest on supplied relationships plus positive identity pairs. No general-language pretraining is needed for those matrices. | InME reports MRR 0.253 on GO and 0.282 on FoodOn, ranking across available classes. This is not directly comparable with BERTSubs's smaller candidate sets. It learns from existing relationships and annotations; it does not provide an independent semantic truth test.[^selfmatching] |

None of these reviewed experiments establishes general zero-shot repair of the
specific errors found here. This is not a claim that learned repair is impossible.
Training one now would introduce a supervision question before establishing why
the proposed supervision resolves our actual failure mechanism.

The previous [SRR01–SRR03](./SENSE-RELATIONS.md) results also remain relevant:
explicit human-written definitions did not rescue the tested relationship
classifier. Using dictionary definitions is a different input condition, but
that fact alone is insufficient reason to repeat the model.

## The released corrections are not a drop-in replacement

The [author portal](https://adimen.ehu.eus/web/adimenSUMO) links
`CorrectionMethodsUsingMember.zip` to the 2023 paper. The archive contains a
WordNet 3.0 noun mapping and an AdimenSUMO 2.7 ontology snapshot. It does not
contain a corresponding final verb mapping.

The noun file has 82,115 offset records. All 152 noun entries from SGC03's
174 mapped entries match by offset. After normalizing relation notation,
33 noun mappings differ and 119 match. The remaining 22 SGC03 entries are verbs.
These differences compare two snapshots; they are not all attributable to the
authors' 2023 correction procedure.

| Sense | SGC03 mapping | Released mapping | Why this matters |
| --- | --- | --- | --- |
| container.n.01 | ShipContainer= | Container= | Removes the unjustified shipping restriction, but does not correct the original side-food → dishware source error. |
| food.n.01 | Food= | PreparedFood+ | The target's meaning and ancestry differ between ontology snapshots. |
| food.n.02 | Food= | SolidFood= | SolidFood is absent from the pinned current ontology. |
| beet.n.02 | FruitOrVegetable+ | PreparedFood+ | Not interchangeable without inspecting which PreparedFood definition is used. |
| chef.n.01 | Chef= | SkilledOccupation+ | The release explicitly types this target as a class of attributes, not an ordinary object class. |
| experience.n.01 | Learning+ | unchanged | The knowledge/learning distinction is not repaired by this row. |
| education.n.02 | EducationalProcess= | unchanged | Likewise leaves the knowledge/teaching-process distinction. |
| harvest.n.02; time.n.01 | IntentionalProcess+; IntentionalProcess= | unchanged | No repair of these outcome/occasion routes. |
| beef.n.01; cattle.n.01 | Cow+; Cow= | unchanged | The old and current Cow definitions differ; unchanged text does not mean unchanged semantics. |

Here `=` denotes equivalence and `+` subsumption. The useful preparation,
preservation, bread and brisket mappings are unchanged. The release also changes
several senses denoting individual hoofed mammals to GroupOfAnimals; their
dictionary definitions do not justify treating every such change as safer.

Three concrete compatibility differences prevent a clean mapping-only swap:

1. Current MILO records the removal of SolidFood and LiquidFood on 2023-05-11.
   Agent is another released class target missing from the pinned class inventory.
2. In the archive, PreparedFood is under SelfConnectedObject and covers
   intentionally prepared material ingestible by animals. In current SUMO it is
   under Food and Mixture, with human-oriented wording. Importing the old mapping
   into current SUMO would reinterpret it. Importing the complete old ontology
   would also change the available parent paths.
3. The archive's Cow describes a generic domesticated hoofed mammal. Current
   Cow describes female cattle. The unchanged cattle mapping cannot be used to
   claim the authors retained the same female-only error.

The archive is a distinct resource candidate, not an isolated treatment for
the present mapping failures. No substitution was performed.

## Which defects affect actual destinations?

The complete originals and inline masks remain in
[SGC03's source evidence](./SGC03/SOURCE-EVIDENCE.md). The following judgments
distinguish topic relevance from the particular witness that admitted the note.

| Existing destination | Concrete source evidence | Judgment |
| --- | --- | --- |
| SocialRole/person, `G50c9e382a3b151da1f8d` | N076 selects `chef` in a cooking note. N085 selects `Brisket on the smoker`, but its graph supplies a person/smoker connection. | Chef/occupations is plausible. N085's equipment → person interpretation is the consequential error; an occupation blacklist would target the wrong distinction. |
| Food/IntentionalProcess, `G0953c4544ac6b557bbcc` | N022 has questionable time/harvest routes **and** a separate beet/preservation witness. | The questionable routes do not invalidate its independently supported food-preservation membership. |
| ContentBearingProcess/Process, `G6d262e2a81fd2bce2749` | N089 enters through involvement → relevance → Communication. N094 enters through experience → Learning/EducationalProcess. | The selected meanings concern bread preparation and coffee experience, not communicating content or learning. Merely being public posts is not sufficient topical evidence. |
| IntentionalProcess/SocialInteraction, `G81d9b4fc37dceb893e96` | N089 has the involvement/relevance route. N022's harvest supplies meals and reaches Giving; its graph contains no receiving person. | The interpersonal interpretation needs evidence that these selected meanings do not supply. |
| SubjectiveAssessmentAttribute/entity, `G9e4514a82e666fb2e025` | N069 concerns goodness and peace; N094 expresses a coffee preference; N039 concerns weather disruption. N089's full post mentions superstition, but its selected mask is Bread/salt/yeast/mixing. | Not uniformly invalid. N039's objective disruption does not establish subjective assessment. N089's full-note relevance must not be mistaken for proof that this mask/derivation captures the belief. |

The source attribution is important. N089's `involve.v.01` already denotes
close, often incriminating involvement rather than ingredient inclusion. Its
hypernym `refer.v.02` denotes relevance, which then maps to Communication.
There is both a source-sense error and a mapping issue; changing one does not
establish that the other is fixed.

N022 instead uses `provide.v.02`, whose food/sustenance meaning is plausible
for a harvest supplying meals. Its Giving/SocialInteraction ancestry adds a
stronger interpersonal reading. Both the direct provide mapping and the
`give.v.03` ancestor offer Giving routes, so removing only the direct mapping
would leave another route. This is not a clean one-edge substitution.

These are candidate meanings, not approved titles or a canonical taxonomy.
SKOS's distinction between hierarchical and associative relations is pertinent:
broader topic relations need not be object subclass relations, while arbitrary
associations must not simply be followed transitively.[^skos] That distinction
does not itself construct our hierarchy.

## Mapping-dependency check

The existing 157 final representatives and all their saved source witnesses were
held fixed. Each listed omission was applied **only in memory** to the mapping
input of the existing `augment` function. A witness remained supported when its
original source senses still reached the required pattern concepts, considering
either orientation for an undirected connected pair. Notes were retained if any
saved witness survived.

No patterns were constructed or reselected. No omission was adopted. These
retrospective checks locate dependencies; they do not test a proposed semantic
repair or estimate how many bad categories exist.

| Mappings omitted for the check | Existing representatives whose note support changes | Those left with fewer than two notes |
| --- | ---: | ---: |
| refer.v.02 | 29 | 16 |
| experience.n.01 and education.n.02 | 9 | 3 |
| time.n.01 and harvest.n.02 | 1 | 1 |
| skilled_worker.n.01 and user.n.01 | 15 | 1 |
| interrupt.v.01 | 11 | 4 |

All five checks preserve these existing memberships:

- Food/IntentionalProcess: N013 N022 N076 N085 N089 N100.
- Food/Process: N013 N022 N076 N085 N089 N094 N100.
- Food/InternalChange: N085 N094.

For example, omitting refer.v.02 changes the SocialInteraction pair from
N022/N089 to N022 alone. Omitting worker/user changes the SocialRole/person
pair from N076/N085 to N076 alone: the chef note retains an independent
person/trade witness. Removing an erroneous derivation need not remove a useful
note, and removing a representative need not remove an erroneous meaning from
the rest of the construction. Rebuilding and semantically inspecting a future
condition would still be necessary.

## Dictionary coverage is a separate limitation

A read-only lookup in the frozen WordNet 3.0 archive distinguishes available
meanings from inventory gaps:

| Source expression | Observed issue | Dictionary observation |
| --- | --- | --- |
| chicken stock | Native stock.n.01 means financial capital. | The stock lemma has the food sense broth.n.01. |
| side dishes | Native dish.n.01 means dishware. | dish.n.02 denotes prepared food. |
| original N022 fragment `sides` | The description expands this to side dishes. | The side lemma's twelve noun senses do not include a side dish; side_dish.n.01 exists under a different lemma. A direct-original input changes the candidate-generation problem. |
| beef in a steak-preparation note | Native beef.n.01 denotes cattle. | beef.n.02 denotes meat. |
| bread preparation involving ingredients | Native involve.v.01 has the wrong involvement meaning. | involve.v.05 covers containing something as a part. |
| coffee experience | Native experience.n.01 denotes accumulated knowledge. | Other experience senses cover observation/participation and apprehended events. Their suitability still needs contextual judgment. |
| grilling | Native grilling.v.01 is unresolved by exact sense lookup. | Morphological lemma lookup finds grill.v.01, cooking over a grill. This does not authorize blindly transferring sense numbers for every inflection. |
| smoker used to cook brisket | Native smoker.n.01 denotes a tobacco-smoking person. | The three smoker-lemma senses concern a person, a men's party and a smoking railway car. None denotes cooking equipment. |

The current lookup accepts exact WordNet identifiers and retains unknowns as
literal-only concepts. That behavior is unchanged. Inventory availability does
not show that a model will select the appropriate sense; inventory absence
means forced choice among those senses cannot express the intended meaning.

## What a source-grounding method would have to do

The financial-stock error occurs even though the existing generated description
already explicitly says pressure-canning homemade chicken stock for food
preservation. It is therefore not enough to propose adding missing full-note
context. The next comparison must separate contextual interpretation from
free-form sense-identifier generation and from candidate availability.

One directly relevant mechanism is **candidate-conditioned sense selection**.
ESCHER takes a sentence with a marked word or multiword occurrence and all
candidate dictionary definitions. BART-large is fine-tuned on SemCor's 226,036
WordNet-annotated occurrences to predict the start/end of the correct definition;
inference chooses only a complete candidate definition. This prevents an
invented sense identifier by construction, not a wrong choice among real senses.
The paper reports an 8.5-F1 improvement over a same-backbone sense-vocabulary
classifier. That comparison concerns its benchmark, not our ByT5 parser or
notes. Its unfamiliar-definition tests still supply the right definition at
inference; they do not test an absent intended sense.[^escher]

This is relevant supervision for choosing a meaning in context, unlike a model
trained only to classify pairs of ontology definitions. It is not a replacement
for category construction, source-graph connections, or unseen-sense handling.

A separate **unknown-sense detector** asks whether any dictionary sense fits.
Lautenschlager et al. compare marked word-usage embeddings with dictionary
examples or glosses, using XL-LEXEME, an XLM-R model trained on word-in-context
comparisons. They tune a nearest-sense similarity threshold using annotated
data and simulated missing senses. Their real English follow-up found only
45 genuinely unrecorded usages among 322 flagged usages (13.98%, versus 9.5%
in the random sample). This combines modern and historical English. It provides
a direct warning that simulated-missing-sense performance does not establish
a reliable automatic rejection mechanism. It flags gaps; it does not create
their missing dictionary concepts or parent relations.[^unknown]

Neither operation is yet selected. The source-code audit reveals a prerequisite
for using a sense selector: native graph concepts have numbered senses but no
source-token offsets. Some concepts are introduced by the description or
parser. A model requiring a marked occurrence cannot simply be attached to
every node. Supplying manual alignments could isolate sense selection in a
diagnostic, but would not establish automatic source grounding.

The inspected ESCHER implementation requires tokenized target instances with
lemma and part of speech, builds candidates from those fields and returns
dictionary offsets. It skips an empty inventory but still chooses from a
nonempty inventory whose meanings are all inappropriate. The inspected release
uses legacy dependencies and a noncommercial repository license; checkpoint
execution and artifact-specific reuse terms remain unverified.[^escher-code]

The subsequent [source-occurrence audit](./SOURCE-OCCURRENCE-GROUNDING.md)
finds existing token offsets but also erroneous candidate restrictions. It
selects a direct-occurrence comparison, not an alignment layer for DRS.
For a bounded test that instead repairs the existing graph's sense selection,
keep the existing descriptions, graph connections and generalization
resource fixed, include currently correct concepts as regression controls, and
record unavailable or unaligned cases rather than supplying hand-picked
replacement meanings. Any resulting change must then be traced through actual
construction. A better sense list alone is not the goal.

Preserving the whole DRS parser is not a requirement. SGC03 has not shown that
its connected-pair restriction improves semantic membership over the simpler
same-source co-occurrence control. An extra sense model plus an alignment layer
must not become the default architecture just because they could repair this
parser. The construction value of retained structure and the cost of the
alternative representation must be reassessed before adding those parts.

## Decision and next research question

Do not install a new mapping verifier, wholesale-swap the correction archive,
or remove all occupation/attribute mappings. The research supplies reasons to
avoid those specific actions, not a verdict against ontology-backed construction.

The next investigation should examine **contextual grounding of source concepts**,
with these distinctions explicit:

1. Selecting among existing dictionary meanings.
2. Recognizing when the dictionary lacks the intended meaning, rather than
   forcing a wrong known sense.
3. Separately assessing subsequent generalization: a correct source sense can
   still acquire an unsupported broader meaning, as with food provision and
   interpersonal Giving.

Before selecting or running a method, inspect its actual input, supervision and
treatment of absent senses. A model evaluated only on choosing among guaranteed
present senses would not establish the second capability. Another generic
definition-pair classifier is not justified by this audit.

The current input path is concrete: a generated description is passed to the
ByT5 parser; its predicted numbered senses are then looked up exactly in
WordNet. The parser receives neither the original note nor its mask. A future
comparison must distinguish those inputs. Using surrounding note text to
interpret a masked expression is not permission to add topics outside the
mask. The superstition in N089 and diet in N069 illustrate that boundary.

Source grounding is not a requirement to perfect every parser node. N085's
valid cooking path does not need its wrong smoker/person node. Nor could sense
selection alone resolve N022's two separate barriers: no direct fix/beet edge
and no path from its existing `fix.v.12` sense to `preparation.n.01` in the
frozen order. The correct drinking sense also does not reach IntentionalProcess.
Research must establish which source errors actually prevent useful
construction, not just reduce an error
count in an intermediate representation.

The practical success criterion remains construction: preserve the useful food,
preservation and occupation destinations while avoiding unsupported meanings
and recovering genuinely missing source topics. A source-only diagnostic can
inform that decision, but cannot establish an improved hierarchy. No source
repair, new model, experiment configuration or navigation candidate is adopted
here. Category selection and complete-corpus coverage remain unresolved.

## Reproduction records

SGC03's input files and source snapshots remain the authoritative baseline.
The current and frozen `semantic_ontology_order.py` both have SHA-256
`98b3bb822fa892bc15bbee3aca7025607f232b7dde461ad7451347d499cea076`.
The dependency check was independently rerun and reproduced all five counts.
It uses `augment`, the existing representatives and their complete witnesses;
it must not be described as rerunning construction.

Run from the repository root. This command reads the frozen inputs, calls the
unchanged production generalization function and writes nothing:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=sse_multivector python3 - <<'PY'
import gzip
import json
from pathlib import Path
from semantic_ontology_order import augment

base = Path('sse_multivector/navigation-research-v1/SGC03')
ontology = json.loads(gzip.decompress(
    (base / 'construction/ontology.json.gz').read_bytes()))
mappings = json.loads((base / 'construction/mappings.json').read_bytes())
lexicon = json.loads(
    (base.parent / 'SGC01/construction/lexicon.json').read_bytes())['senses']
representatives = json.loads((base / 'audit.json').read_bytes())[
    'conditions'][2]['representatives']

def survives(pattern, witness, senses):
    key, source = pattern['key'], witness['source_senses']
    if len(key) == 1:
        return key[0] in senses[source[0]]['ancestors']
    return any(
        key[0] in senses[a]['ancestors']
        and key[1] in senses[b]['ancestors']
        for a, b in (source, source[::-1]))

checks = [
    ['refer.v.02'],
    ['experience.n.01', 'education.n.02'],
    ['time.n.01', 'harvest.n.02'],
    ['skilled_worker.n.01', 'user.n.01'],
    ['interrupt.v.01'],
]
for omitted in checks:
    senses = augment(lexicon, {
        name: value for name, value in mappings.items()
        if name not in omitted
    }, ontology, ['n', 'v'])['senses']
    changed = []
    for pattern in representatives:
        remaining = sorted({w['note'] for w in pattern['witnesses']
                            if survives(pattern, w, senses)})
        if remaining != pattern['notes']:
            changed.append(remaining)
    print(', '.join(omitted), len(changed),
          sum(len(notes) < 2 for notes in changed))
PY
```

Output columns after the mapping names are changed note support, then fewer
than two remaining notes:

```text
refer.v.02 29 16
experience.n.01, education.n.02 9 3
time.n.01, harvest.n.02 1 1
skilled_worker.n.01, user.n.01 15 1
interrupt.v.01 11 4
```

The correction archive is available at
`https://adimen.ehu.eus/web/files/AdimenSUMO/CorrectionMethodsUsingMember.zip`.
Its observed size is 50,948,780 bytes. Member paths below omit the outer
`CorrectionMethodsUsingMember/` directory:

| Archive member | SHA-256 |
| --- | --- |
| Mappings/nounMapping2AdimenSUMO.pl | dca36704d9e791cf3beb17ef6f748c8db9e235cd06d9ea5cc9c9dbc43ab8ec8f |
| Ontology/merge.kif | a34e72ef6d14939ffd329e8ec02656f23f3979891ca70fb15becb406def10f82 |
| Ontology/milo.kif | 27bd0cfba631295adf5dc1f1603e9344aad1197898e6e6cec7c234ddde76223a |

An independent HTTP-range read fetched 4,522,404 bytes, verified all three
member hashes, and matched every changed row in the table below against the
release. ZIP-member integrity was checked during decompression. No ontology
code or bundled executable was run, and the archive was not adopted.

The archive gives no verified Git revision. Its ontology members identify
AdimenSUMO 2.7 and have January 2019 ZIP timestamps; the noun mapping has a
December 2020 timestamp. These timestamps are not publication or semantic
version guarantees. The portal's CC BY 3.0 statement coexists with embedded
IEEE/GNU notices in ontology headers; this audit does not declare every
constituent uniformly licensed.

Dictionary lookups used the existing NLTK 3.9.2 environment and WordNet 3.0
archive, SHA-256
`cbda5ea6eef7f36a97a43d4a75f85e07fccbb4f23657d27b4ccbc93e2646ab59`.
This was not a model-accuracy test or a held-out evaluation.

### All changed noun mappings

These are the complete 33 normalized differences, not only the examples used
above. `Type` preserves the release's literal field: uppercase `Attribute`
means a class of attributes and is distinct from lowercase individual
`attribute`. Line numbers refer to `Mappings/nounMapping2AdimenSUMO.pl`.
The release's `not(subsumption)` is normalized to `[`. The unchanged
`natural_phenomenon.n.01 → IntentionalProcess[` is therefore not a difference.

| Sense | SGC03 | Release | Type | Line |
| --- | --- | --- | --- | ---: |
| beet.n.02 | FruitOrVegetable+ | PreparedFood+ | class | 81662 |
| bovid.n.01 | HoofedMammal+ | GroupOfAnimals+ | class | 77858 |
| bovine.n.01 | Cattle+ | GroupOfAnimals+ | class | 77859 |
| capital.n.01 | MeanOfProduction+ | RelationalAttribute+ | Attribute | 64140 |
| chef.n.01 | Chef= | SkilledOccupation+ | Attribute | 49205 |
| collection.n.01 | Collection= | Group= | class | 78359 |
| consumer.n.01 | Consumer= | Human+ | class | 47176 |
| container.n.01 | ShipContainer= | Container= | class | 77590 |
| dinner.n.01 | Dinner+ | RelationalAttribute+ | Attribute | 37061 |
| even-toed_ungulate.n.01 | HoofedMammal+ | GroupOfAnimals+ | class | 77852 |
| food.n.01 | Food= | PreparedFood+ | class | 81084 |
| food.n.02 | Food= | SolidFood= | class | 75793 |
| meal.n.01 | Meal= | Collection+ | class | 37050 |
| measure.n.02 | ConstantQuantity+ | ConstantQuantity= | class | 75725 |
| nutriment.n.01 | Food+ | Substance+ | class | 78648 |
| peace.n.01 | PeaceState= | SubjectiveAssessmentAttribute+ | Attribute | 67323 |
| physical_entity.n.01 | Physical= | Physical+ | class | 74444 |
| physical_phenomenon.n.01 | IntentionalProcess[ | NaturalProcess+ | class | 78464 |
| produce.n.01 | GroceryProduce= | PreparedFood+ | class | 81093 |
| rain.n.01 | Raining+ | Precipitation+ | class | 58017 |
| relation.n.01 | BinaryRelation= | Relation= | Relation | 75718 |
| root_vegetable.n.01 | RootVegetable= | PreparedFood+ | class | 81124 |
| ruminant.n.01 | HoofedMammal+ | GroupOfAnimals+ | class | 78205 |
| starches.n.01 | Food+ | PreparedFood+ | class | 81209 |
| state.n.02 | Proposition+ | Attribute= | Attribute | 77014 |
| stock.n.01 | Stock= | FinancialInstrument+ | class | 64031 |
| storm.n.01 | BeaufortNumberEleven= | RelationalAttribute+ | Attribute | 57808 |
| structure.n.01 | Artifact+ | Artifact= | class | 75741 |
| substance.n.01 | Object= | Substance= | class | 75722 |
| substance.n.07 | Object= | Object+ | class | 75794 |
| vegetable.n.01 | Vegetable= | FruitOrVegetable+ | class | 78202 |
| worker.n.01 | Employee+ | SocialRole+ | Attribute | 47245 |
| writer.n.01 | Writer= | SkilledOccupation+ | Attribute | 54187 |

## Sources

[^typed]: Álvez, Lucio and Rigau, [Black-box Testing of First-Order Logic Ontologies Using WordNet](https://arxiv.org/pdf/1705.10217v3), §§4.1–4.2. The inspected interpretation is designed for ontology competency questions, not topical navigation.
[^correction]: Álvez, Gonzalez-Dios and Rigau, [Towards Effective Correction Methods Using WordNet Meronymy Relations](https://aclanthology.org/2023.gwc-1.4.pdf), §§4–6; [author release page](https://adimen.ehu.eus/web/adimenSUMO).
[^weakening]: Li and Lambrix, [Repairing Networks of EL-bottom Ontologies using Weakening and Completing](https://arxiv.org/html/2407.18848v1), §§2.2–2.3 and 3–6.
[^bertsubs]: Chen et al., [Contextual Semantic Embeddings for Ontology Subsumption Prediction](https://www.cs.ox.ac.uk/files/14088/BERTSubs_preprint_2022.pdf), §§3–4, especially cross-ontology training and Table 5.
[^ontolama]: He et al., [Language Model Analysis for Ontology Subsumption Inference](https://aclanthology.org/2023.findings-acl.213.pdf), §§3–5. Its cloze-style prompts and fine-tuning are different from instruction-following model calls.
[^selfmatching]: Shiraishi and Kaneiwa, [A Self-matching Training Method with Annotation Embedding Models for Ontology Subsumption Prediction](https://arxiv.org/pdf/2402.16278), §§5–6 and Table 5.
[^skos]: W3C, [SKOS Primer](https://www.w3.org/TR/skos-primer/), §§2.3, 3.3 and 5.2. This is a representation distinction, not a category-construction algorithm or a newly adopted dependency.
[^escher]: Barba, Pasini and Navigli, [ESC: Redesigning WSD with Extractive Sense Comprehension](https://aclanthology.org/2021.naacl-main.371.pdf), §§3–4.2. Candidate spans constrain output validity; the experiment does not demonstrate our source-to-graph alignment or unknown-sense rejection.
[^unknown]: Lautenschlager et al., [Detection of Non-recorded Word Senses in English and Swedish](https://arxiv.org/pdf/2403.02285), §§2.3–4 and 6.2, Table 6 and Appendix I. Real flagged-sample precision must be distinguished from calibration with artificially withheld senses.
[^escher-code]: SapienzaNLP/esc, revision `2576c15947f6418239f77075d9f414b2c539bad3`: [candidate/input construction](https://github.com/SapienzaNLP/esc/blob/2576c15947f6418239f77075d9f414b2c539bad3/esc/esc_dataset.py#L224), [prediction](https://github.com/SapienzaNLP/esc/blob/2576c15947f6418239f77075d9f414b2c539bad3/esc/predict.py#L41), [XML reader](https://github.com/SapienzaNLP/esc/blob/2576c15947f6418239f77075d9f414b2c539bad3/esc/utils/wsd.py#L68), [requirements](https://github.com/SapienzaNLP/esc/blob/2576c15947f6418239f77075d9f414b2c539bad3/requirements.txt), [CC BY-NC-SA 4.0 notice](https://github.com/SapienzaNLP/esc/blob/2576c15947f6418239f77075d9f414b2c539bad3/license.txt). Source inspection only; no author executable or checkpoint was run.
