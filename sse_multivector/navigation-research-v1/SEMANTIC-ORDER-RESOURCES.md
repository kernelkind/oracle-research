# Semantic generalization across grammatical forms

The next missing capability is a usable broader meaning for differently phrased
but related source concepts. SGC02 already constructs some meaningful paired
parents from actual source connections. However, its WordNet-only order cannot
place a valid cooking/brisket connection under the same activity/food parent as
preparation and preservation. Another merge score cannot supply that absent
meaning. [SGC02 evidence](./CONNECTED-PATTERN-CONSTRUCTION.md).

SUMO is a plausible resource for an additional generalization order, not a
verified replacement ontology. Its published mappings provide concrete
cross-form paths, and a directly related system constructs shared semantic
patterns from them. But the mappings contain material meaning mismatches.
Keeping their provenance is necessary; it does not make them correct.

## The concrete gap

The unchanged SGC02 inputs contain these native connections:

| Source | Native connection | What the current order misses |
| --- | --- | --- |
| N085, row 711 | cooking verb → brisket | Cooking cannot reach the activity noun used by other food-work patterns. |
| N100, row 904; N076, row 673; N089, row 866 | preparation noun → steak, food, or bread | Preparation and cooking lack a shared food-work parent in the permitted order. |
| N022, row 350 | beet → preservation noun | Shares Activity with preparation, but not with cooking. |
| N013, row 468 | preservation noun → food | The nourishing-substance Food sense and solid-Food sense meet only at Matter. |

These are selected graph witnesses, not a complete account of every note.
All originals, masks, descriptions and native outputs remain in
[SOURCE-EVIDENCE.md](./SGC01/construction/SOURCE-EVIDENCE.md). Four malformed
graphs remain excluded. The missing preparation/beet connection is a separate
source-graph problem; additional ancestors cannot create that connection.

## Derivational links are insufficient by themselves

WordNet's morphosemantic resources distinguish event nominalizations from
agents, results and instruments. A verb's related noun is therefore not
automatically another name for the same event. The 2021 analysis studies fourteen
relation types; its results concern derivation, not browsing hierarchy quality.
[^morph]

A local check of the already cached WordNet 3.0 dictionary finds both the
cooking event noun and the cook/person noun among derivational relatives of
`cook.v.01`. The event noun's hypernym path passes through change of state and
action to `act.n.02`; preparation and preservation reach `activity.n.01`, then
`act.n.02`. Even selecting the event nominalization would not make cooking a
subtype of `activity.n.01`. It also would not unify the two Food ancestors.

Consequently, indiscriminately adding derivations would introduce wrong
event/person equivalences, while an event-only rule would still leave the
particular Activity and Food gaps. This rejects that shortcut as a complete
repair, not morphosemantic links as a potentially useful component.

## A directly related construction precedent

Pease and Cheung's *Toward a Semantic Concordancer* augments dependency graphs
with SUMO types obtained through WordNet senses. Section 6 constructs a shared
abstraction from example sentences: kicking and pushing become Motion while
the event's connections to people and vehicles remain bound. Section 4 matches
patterns using broader classes; section 8 describes indexed corpus access.
This is actual shared-pattern construction, not only classification under
supplied labels. [^concordancer]

The fit is partial. Their inputs are parsed sentences, not SSE vectors or
informal source masks. Their evaluation concerns linguistic usage and
preposition errors, not useful category menus or complete note paths. The
reported roughly 66% result measures word-sense disambiguation, not construction
quality. The paper explicitly treats mapped equivalences as informal. Its
authored role-rewriting rules are not required for the bounded unordered-edge
construction already implemented here. [^concordancer]

The released `CommonCNFUtil.java` implements common-pattern construction and
common-ancestor lookup. This verifies an executable precedent, but its parser,
unification strategy and ontology processing are not adopted by this research.
[^implementation]

## Exact resource mappings

The inspected SUMO repository revision is
`abcb7cc1090c5b35cbfacd9e44e50e50c7434433`. Entries were matched using WordNet
3.0 part of speech and synset offsets, not unqualified word spelling.

| WordNet sense | Offset | Released SUMO mapping |
| --- | --- | --- |
| `cook.v.01` | `01665638` | `Cooking+` |
| `cooking.n.01` | `00243918` | `Cooking=` |
| `preparation.n.01` | `01143040` | `IntentionalProcess+` |
| `preservation.n.01` | `00819024` | `Maintaining+` |
| `food.n.01` | `00021265` | `Food=` |
| `food.n.02` | `07555863` | `Food=` |
| `beet.n.02` | `07719839` | `FruitOrVegetable+` |
| `bread.n.01` | `07679356` | `BreadOrBiscuit+` |
| `brisket.n.01` | `07657547` | `Meat+` |

The noun and verb mapping headers distinguish equivalence (`=`), subsumption
(`+`), instantiation (`@`) and their complement forms (`:`, `[`, `]`). Sharing a
broader destination does not establish synonymy. Instance membership must not
silently become subclassing, and complement mappings are not positive
ancestors. [^noun-mapping] [^verb-mapping]

The released ground subclass statements include:

```text
Cooking → Making → IntentionalProcess
Maintaining → IntentionalProcess
Meat → Food
BreadOrBiscuit → PreparedFood → Food
```

These facts occur in the core, mid-level and food ontologies. A generic order
augmentation could therefore propose a separate
`SUMO:IntentionalProcess — connection — SUMO:Food` pattern from existing native
edges. It would not make cooking become the WordNet activity sense, nor merge
the two original WordNet Food senses. [^core] [^milo] [^food]

That distinction is important: the experiment must inspect this new parent's
actual meaning, not rename it to a previously desired category and claim the
old category was repaired.

## Known mapping and ontology limits

The inspected definitions expose concrete qualifications:

- SUMO Cooking includes food preparation without heating, despite the `=` link
  from the heat-based WordNet cooking noun.
- SUMO Food is human food; WordNet `food.n.01` includes nourishment for animals
  generally. Its mapping is not universally valid even as a one-way broadening.
- SUMO Meat includes eggs. Its scope is not ordinary-language meat alone.
- FruitOrVegetable is expressly not a Food subclass, because it includes
  inedible examples. It is defined through plant reproductive structures,
  while the mapped beet sense describes a root vegetable.
  [^core] [^noun-mapping]

Retaining the existing WordNet ancestors gives beet a separate route through
its solid-Food ancestor to SUMO Food. That may preserve a locally valid food
assignment; it does not vindicate the other FruitOrVegetable route. An audit
must distinguish a correct destination from an incorrect explanation for it.

Neither preserving mapping types nor changing equivalence into a forward edge
fixes a source sense broader than its mapped target. A local human-food result
could be useful while the general mapping remains invalid for animal feed.
The experiment must not infer universal semantic containment from this corpus.

An independent 2019 audit found incorrect mappings involved in 58 of 169
sampled reasoning problems; fourteen entailed results still used incorrect
mappings. These are historical problem-level findings, not a current mapping
error rate. The audit also identifies noun/adjective/process type confusions.
It supports checking derivations rather than trusting a successful result or
ontology provenance alone. [^audit]

## Consequential comparison

A bounded construction comparison is worth designing. It would keep the eleven
accepted source graphs, all original evidence and the SGC02 connection policy
fixed, changing only the supplied ancestor order. No new model, edited source
edge, food-specific rule or hand-chosen final taxonomy is needed.

The minimally informative comparison has three readings:

1. The original WordNet-only construction.
2. Construction with additional, separately identified ontology ancestors and
   a saved mapping path for each admission.
3. The single-concept categories and intersections of their source-row sets
   under that same additional order. These are explanatory controls, not
   assumed alternative category semantics.

The output must answer more than whether the already inspected mapping paths
exist. Does an actual new shared parent retain source-supported cooking,
preparation and preservation notes, have genuinely narrower children, and
avoid unsupported new members? Is it more informative than its Food or
IntentionalProcess singleton, or merely the same result with more words?
Does any observed advantage require native connections rather than coincidental
co-occurrence in this sample?

Inspect complete generated note sets and actual native witnesses, including
unexpected coherent categories and every regression. Do not prescribe one
correct hierarchy or count every broad pattern as a failure. But do not credit
generic cardinality growth, duplicate destinations or source errors hidden by
a plausible category name. The source parser's existing errors and exclusions
remain visible limitations, not repaired inputs.

The current evidence already establishes static reachability; rerunning only
those lookups would not reduce an uncertainty. Construction could still fail
because the ancestors are inappropriate, because source graphs are wrong, or
because useful candidates are swamped by non-distinct choices. Those outcomes
imply different next actions and must be distinguished in the pre-run plan.

The resource is intrinsically compatible with cached local lookup and finite
ancestor expansion. That is a plausibility argument for scalability, not a
benchmark or a claim that enumerating every possible larger graph is practical.
Full logical theorem proving and inferred participants are outside this test.

No SUMO mapping, new hierarchy, or browser is adopted here. The
[SGC03 pre-run design](ONTOLOGY-CONSTRUCTION.md#sgc03-study-design) separates noun-only and noun-plus-verb
augmentation, requires same-order singleton controls, and distinguishes local
membership from mapping validity. It explicitly does not test an already
contradicted claim of universally sound containment. A positive pilot with
justified paths would support testing transfer and category selection, not
declaring the whole navigation goal solved. The [completed SGC03 comparison](./ONTOLOGY-CONSTRUCTION.md)
now records useful local paths, class-of-attribute admission errors, other
mapping scope mismatches, and unchanged source limitations. Class declarations
and provenance did not establish semantic containment. Validation/adaptation
of the cross-resource mappings remains unresolved.

## Reuse and sources

The inspected files have different notices: the core ontology carries IEEE
attribution terms; the mid-level ontology, Food file and mapping annotations
declare GPL, and original WordNet content retains its own notice. They are not
uniformly permissive. SGC03 retains full pinned resources in a separate local
cache and saves parsed facts, used mapping rows, resource hashes and exact
header notices with the experiment. These retained excerpts and records preserve
the applicable notices; they do not relicense the upstream resource. [^core] [^milo] [^food]
[^noun-mapping] [^verb-mapping]

[^morph]: Verginica Mititelu, Svetlozara Leseva and Ivelina Stoyanova (2021), [Semantic Analysis of Verb-Noun Derivation in Princeton WordNet](https://aclanthology.org/2021.gwc-1.13.pdf), sections 2–4. Local lookup used the already frozen WordNet 3.0 cache and NLTK 3.9.2; this is not a new neural-model result.
[^concordancer]: Adam Pease and Andrew Cheung (2018), [Toward a Semantic Concordancer](https://aclanthology.org/2018.gwc-1.12.pdf), sections 3, 4, 6 and 8.
[^implementation]: Ontology Portal, [CommonCNFUtil.java](https://github.com/ontologyportal/sigmanlp/blob/89424d06a7ca5fde7f8d6ee8ea5ff9eead085c92/src/main/java/com/articulate/nlp/semRewrite/CommonCNFUtil.java), `findCommonAncestor`, `findCommonCNF`, `unify` and `mostSpecificUnifier`.
[^noun-mapping]: Ontology Portal, [WordNetMappings30-noun.txt](https://github.com/ontologyportal/sumo/blob/abcb7cc1090c5b35cbfacd9e44e50e50c7434433/WordNetMappings/WordNetMappings30-noun.txt), header and the numbered synsets listed above.
[^verb-mapping]: Ontology Portal, [WordNetMappings30-verb.txt](https://github.com/ontologyportal/sumo/blob/abcb7cc1090c5b35cbfacd9e44e50e50c7434433/WordNetMappings/WordNetMappings30-verb.txt), header and offset `01665638`.
[^core]: Ontology Portal, [Merge.kif](https://github.com/ontologyportal/sumo/blob/abcb7cc1090c5b35cbfacd9e44e50e50c7434433/Merge.kif), header; Maintaining, Making, Cooking, Food, Meat and FruitOrVegetable definitions and subclass statements.
[^milo]: Ontology Portal, [Mid-level-ontology.kif](https://github.com/ontologyportal/sumo/blob/abcb7cc1090c5b35cbfacd9e44e50e50c7434433/Mid-level-ontology.kif), header and PreparedFood definition/subclasses.
[^food]: Ontology Portal, [Food.kif](https://github.com/ontologyportal/sumo/blob/abcb7cc1090c5b35cbfacd9e44e50e50c7434433/Food.kif), header and BreadOrBiscuit definition/subclass.
[^audit]: Javier Álvez, Itziar Gonzalez-Dios and German Rigau (2019), [Commonsense Reasoning Using WordNet and SUMO: a Detailed Analysis](https://arxiv.org/pdf/1909.02314), sections 3–4 and Table 2. The evaluated historical core and benchmark are not the pinned current resource above.
