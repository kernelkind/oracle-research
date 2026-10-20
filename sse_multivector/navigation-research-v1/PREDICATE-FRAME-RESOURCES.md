# Shared activity meanings across grammatical forms

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

NounAtlas and VerbAtlas supply real noun/verb connections missing from SGC01's
WordNet ancestry. They do not repair the saved source interpretations or provide
a finished category hierarchy. Checking the released mappings against the actual
graphs rules out a redundant next experiment: adding those mappings alone would
not recover a new shared preparation/material pattern.

## The missing capability

[SGC01](./SEMANTIC-GRAPH-CONSTRUCTION.md) represents preparing steak and mixing
bread ingredients with the noun `preparation.n.01`. Preparing beets uses the
verb `fix.v.12`, WordNet's canonical identifier for the relevant `prepare.v.01`.
The fixed hypernym relation does not connect those noun and verb representations.
This is not evidence that the underlying activities should be separate browsing
destinations. It is a limitation of that representation and relation inventory.

The required capability is broader than resolving a spelling: a shared activity
meaning must retain its connection to the actual material or participant in the
source. Knowing that two predicates concern preparation does not establish what
each source is preparing. Nor must all cooking and preservation activities be
placed under one particular preparation taxonomy. A material category could
instead narrow to several activity branches.

## What the resources contain

VerbAtlas groups WordNet verb senses into manually constructed scenario classes,
called frames, with shared argument-role inventories. A frame groups related
meanings rather than declaring them identical. Its prototypical roles include
optional arguments; typical argument preferences are not statements that those
arguments occur in a particular source. The original evaluation measures
semantic-role labeling, not note-category construction.[^1]

NounAtlas extends those frames to event-related nouns. It combines derivational
links with expert assignments; a definition-pair classifier proposes candidates
for otherwise unlinked nouns, followed by expert selection. This classifier's
input is dictionary definitions, not arbitrary note descriptions. It is not a
justified substitute for contextual interpretation here.[^2]

The separate nominal role-labeling experiment generates nominalized SemCor
sentences, transfers verbal argument spans, and trains on the resulting data.
Its joint nominal/verbal baseline scores 72.4 overall F1 and 76.4 role F1 on 500
expert-corrected generated examples. These results establish neither transfer
accuracy on informal notes nor useful hierarchy construction.[^2]

## Verified lookup results

`./SGC01/frame-resource-check.json` preserves 43
queries: 39 mapped senses and four absent ones. Each result retains the exact
WordNet-offset → BabelNet-ID → frame-ID rows, the relevant argument-role rows,
source URLs, repository revision and file hashes. These are static lookups,
not outputs from a new contextual model. The inspected resource revision is
`8e0e7d41683eff548b53ffb3e02b71391fe95a45`.[^3]

| Source sense | Shared class | What the lookup does establish |
|---|---|---|
| `cook.v.01/.02/.03`; `cooking.n.01` | COOK | Several cooking senses and the cooking noun share a frame. |
| `fix.v.12`; `preparation.n.01` | PREPARE | The general preparing verb and preparation noun share a frame. |
| `preserve.v.04`; `freeze.v.04`; `preservation.n.01/.03` | PRESERVE | The resource groups causative freezing with preservation. |
| `freeze.v.01` | STOP | The wrong native sense does not become preservation. |
| `freeze.n.01`, also the canonical sense of `freezing.n.01` | CHANGE-APPEARANCE/STATE | Grammatical variants do not invariably receive the same frame. |

PRESERVE membership is a resource classification, not proof that any particular
freezing event has preservation as its purpose. Similarly, generic preparation
is not interchangeable with the heat-specific cooking sense of preparation.
The original sense and source witness must remain available.

The released schemas for the three relevant classes differ:

- COOK includes Agent, Patient, Instrument, Source and Beneficiary.
- PREPARE includes Product and Material, alongside Agent and other roles.
- PRESERVE includes Agent, Patient and Theme.

Those are allowable roles, not observed bindings. A predicate-specific
PropBank-to-Atlas mapping is available, but no corresponding PMB-to-Atlas
conversion was established. Shared English role names do not justify silently
rewriting `MadeOf`, `Patient` or `Theme`.[^3][^4]

## Effect on the unchanged SGC01 graphs

The one identified additional activity union is:

```text
PREPARE                         N022 N076 N089 N100
├─ preparation.n.01             N076 N089 N100
└─ fix.v.12                     N022
```

This is a prospective lookup-induced structure, **not a newly executed
construction run or an adopted menu**. The nominal sources already formed the
three-note preparation group. The additional note is the beet-freezing post:

> ⟦This year’s beets⟧. Vac sealed and ⟦ready for the freezer⟧. Not too bad
> for a 4x4 ⟦raised bed⟧. 5 meals of sides in a pinch.

This excerpt locates the relevant source; the unchanged complete note and native
output are preserved under row 904 in
[SOURCE-EVIDENCE.md](./SGC01/construction/SOURCE-EVIDENCE.md).

The native preparation verb points to `garden-grown.a.01` as its Patient—not
to the beets. The other sources use `MadeOf` to connect preparation to steak,
food or bread. Adding PREPARE therefore does not provide a new common bound
pattern. Its immediate branches would mainly distinguish grammatical
representations. A correct broad four-note union is not, by itself, a useful
new browsing distinction.

The other mappings cannot supply the missing construction evidence either.
COOK has only the valid brisket source, row 711. The baking and frying outputs
were malformed; native `grilling.v.01` is unknown. PRESERVE reproduces the
existing preservation-noun membership, N013 and N022. The native freezing
sense remains STOP and has no beet participant. These are direct consequences
of the saved graphs, not a measured accuracy claim for NounAtlas.

## Decision and remaining work

Do not run another model or constructor just to demonstrate the verified
lookup. Do not add a hand-chosen COOK → PREPARE edge or repair roles to obtain
a preferred hierarchy. Those actions would not answer the outstanding question.

A construction-facing test would become informative if a native contextual
method supplies shared activity frames **and actual argument evidence** from
the unchanged descriptions. Its output must feed category construction, with
the resulting complete paths inspected. A successful frame tagger alone would
not establish useful categories. Availability and training fit must first be
verified, particularly for nominal predicates; the released dictionary tables
are not such a contextual method.

This is not a requirement for perfect event logic. Correct local evidence can
remain useful despite other graph errors. The next investigation must establish
whether the additional structure helps discover notes, rather than turn into
an open-ended project to annotate every relation. Category selection and
complete-note coverage remain independent unresolved dependencies.

Both resource release pages state CC BY-NC-SA 4.0. The bundled WordNet and
BabelNet mappings also have notices. This is not evidence of unrestricted
commercial reuse; no production adoption or paid service is authorized by this
research.[^5]

## Contextual implementation availability

The directly related release chain does not establish a ready-to-run joint
nominal/verbal model:

- At the pinned NounAtlas revision, the README describes its joint model's
  InVeRo availability as forthcoming. It provides training data and a
  `roberta-base` joint-training configuration with `vocabulary.va.na.json`,
  not an identified downloadable joint checkpoint.[^6]
- MultiSRL's text interface loads Stanza output through
  `SrlDataset.load_sentences`. At revision
  `7c0376970ecaec8da80aa6d8cf6b8a8b21c0279e`, it selects predicate positions
  only when the part of speech is VERB. Prediction consumes those positions.
  A NOUN-tagged “preparation” is therefore excluded by that interface,
  regardless of whether its training code can consume nominal annotations.[^7]
- InVeRo-XL documents span-based CPU/CUDA packages and a text-to-frame/argument
  API, but the download link leads to an account-gated resource manager. No
  public checkpoint identity establishing NounAtlas joint training was verified.
  Its 2021 evaluation uses preidentified predicates and reports no separate
  nominal result; it cannot stand in for the later joint experiment.[^4][^8]

This is a scoped availability finding, not proof that no suitable model exists.
No model or package was downloaded, no hosted inference was invoked, and no
training was started. Changing a verb-only frontend would not by itself supply
the missing nominal training or participant meanings. Do not substitute that
configuration and then call its expected nominal omission a failed transfer
experiment. Before expanding this route, reassess which relational distinctions
the constructor actually needs for browsing; exact event-role recovery is not
an end in itself.

## Construction question before another model

The source audit identified a less demanding possibility. SGC01's preparation
sources already connect preparation to food through `MadeOf`; its beet source
connects beets to preservation through `Goal` in the other direction. Preparation
and preservation have an existing activity ancestor. Keeping those observed
connections while forgetting their exact type and direction was tested in
[SGC02](./CONNECTED-PATTERN-CONSTRUCTION.md), without a new frame inventory.
It produces source-supported food-activity patterns, but does not establish a
better complete browsing hierarchy.

This relaxation must remain separate from dropping all connections. The
[CAP03 evidence](./SUBJECT-DESCRIPTION-CONSTRUCTION.md) distinguishes “More
coffee” from a coffee-shop source where “more” qualifies disconnection from the
internet. Whole-description word co-occurrence would lose that distinction.
Wrong senses, missing participants and omitted sources likewise remain separate
limitations; erasing relation labels cannot repair them.

SGC02 kept every source, predicted sense and actual connected pair fixed. Its
source/path audit weakens the case for requiring precise role normalization
first. Remaining omissions concern the generalization order and source bindings:
the correct cooking/brisket edge still cannot reach the activity noun, and two
ordinary food senses meet only at Matter. Category pruning or better role names
cannot supply those links. Further resource investigation must address actual
construction paths, retaining mapping types and auditing source-supported
admissions; no particular food taxonomy or replacement model is prescribed.
The [semantic-order resource investigation](./SEMANTIC-ORDER-RESOURCES.md)
addresses that narrower dependency. Its published construction precedent and
known mapping mismatches motivate a controlled comparison, not another
nominal-role model search or adoption of a sound ontology by assumption.

## Sources

[^1]: Di Fabio, Conia and Navigli (2019), [VerbAtlas: a Novel Large-Scale Verbal Semantic Resource and Its Application to Semantic Role Labeling](https://aclanthology.org/D19-1058.pdf), sections 3–5. Frames, roles and role-labeling evaluation have different semantics from navigation ancestry.
[^2]: Navigli et al. (2024), [NounAtlas: Filling the Gap in Nominal Semantic Role Labeling](https://aclanthology.org/2024.acl-long.857.pdf), sections 3–4, especially definition-based mapping, nominalization, role propagation and the 500-sentence evaluation.
[^3]: [Pinned NounAtlas/VerbAtlas resources](https://github.com/SapienzaNLP/nounatlas/tree/8e0e7d41683eff548b53ffb3e02b71391fe95a45/resources). Exact selected rows and file hashes are preserved in the accompanying JSON; no resource frame names are adopted as UI labels.
[^4]: [VerbAtlas API documentation](https://verbatlas.org/api-documentation), contextual role output and inventory mapping interfaces. Documentation of an interface does not prove that a particular deployed model was trained on nominal examples.
[^5]: [NounAtlas release](https://frameatlas.org/download) and [VerbAtlas release](https://verbatlas.org/download), displayed license notices.
[^6]: [Pinned NounAtlas README](https://github.com/SapienzaNLP/nounatlas/blob/8e0e7d41683eff548b53ffb3e02b71391fe95a45/README.md) and [joint-training configuration](https://github.com/SapienzaNLP/nounatlas/blob/8e0e7d41683eff548b53ffb3e02b71391fe95a45/resources/roberta_custom_config/train/ontosemcorgemini_2_nn.yaml).
[^7]: MultiSRL pinned [text inference](https://github.com/SapienzaNLP/multi-srl/blob/7c0376970ecaec8da80aa6d8cf6b8a8b21c0279e/scripts/inference/predict.py), [predicate-position selection](https://github.com/SapienzaNLP/multi-srl/blob/7c0376970ecaec8da80aa6d8cf6b8a8b21c0279e/srl/data/srl_dataset.py), and [model prediction](https://github.com/SapienzaNLP/multi-srl/blob/7c0376970ecaec8da80aa6d8cf6b8a8b21c0279e/srl/model/srl_parser.py). This is source inspection, not a model-accuracy measurement.
[^8]: Conia et al. (2021), [InVeRo-XL](https://aclanthology.org/2021.emnlp-demo.36.pdf), section 2.3 and Table 1; [resource gateway](https://nlp.uniroma1.it/resources/).
