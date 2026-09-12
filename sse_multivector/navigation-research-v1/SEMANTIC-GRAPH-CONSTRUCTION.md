# Contextual semantic graphs and category construction

SGC01 produces a useful food-preparation grouping and explicit paths into
bread and steak preparation. It does not establish a better complete hierarchy.
The shared preparation group already had the same three notes before lexical
generalization; several other cooking and preservation sources remain separate.
The run also exposes wrong contextual senses, missing participants and early
endings in the released parser.

These are not grounds for demanding perfect logical representations. A wrong
relationship elsewhere in a graph does not invalidate a useful topical path.
Conversely, a correct set of returned notes cannot validate an incorrect source
interpretation. Both distinctions matter here. No browser or baseline changed.

## Question and method

[SPC02](./STRUCTURAL-GENERALIZATION.md) found that matching phrase structure and
any available dictionary sense can recover useful broader topics, but also
switch word meanings along a path. It misses legitimate relationships expressed
with different grammatical arrangements. SGC01 tests contextual concepts and
their linked participants as a possible construction input.

Fifteen unchanged descriptions from thirteen notes were selected before
inference. They cover the existing cooking/preparation/preservation cases,
washed dishes versus food dishes, purpose-sake, and two kinds of experience.
Each retains its original mask and complete note. This is a targeted diagnostic,
not an unseen accuracy sample. The model receives the saved description—not
the full note, an SSE vector, or the highlighted source fragments directly.
That representation change is part of the tested pipeline, not an assumption
that the inputs are interchangeable.

The released ByT5 parser converts text into Sequence Box Notation: numbered
WordNet concepts, participant relationships and contextual operators. The
formalism explicitly distinguishes concepts, role links, constants and context
connections.[^1] A local reader checks sequence syntax and references; it does
not certify the full logical structure or semantic correctness.

The constructor enumerates single concepts and linked concept pairs. In the
literal condition, the predicted concept and relationship labels stay exact.
In the generalized condition, a concept may be replaced by its cached WordNet
ancestor. The relationship and the specific pair of source participants remain
unchanged. Broader-to-narrower links either add a relationship constraint or
specialize a concept. Note membership comes from actual source occurrences,
not an independently scored classifier.

This is a bounded construction inspired by order-labelled graph refinement,
not a replication of RHOG or a complete ontology learner. RHOG gives formal
generalization operations over structured graphs; those properties do not
establish that predicted concepts or the resulting choices serve browsing.[^2]
No nominal-to-verbal equivalences, guessed roles or food-specific bridges were
added. Unknown concepts remain literal. Equal-note-set patterns remain distinct
meanings in the saved data; the inventory groups them only for inspection.

The [frozen plan](./SGC01-PLAN.md) records the hypothesis, competing explanations
and decision consequences. A plan sentence excluding wrong graphs from evidence
must be interpreted locally: an unsupported relationship cannot validate that
relationship, but a correct subgraph can remain useful.

## Model fit and provenance

The checkpoint is `XiaoZhang98/byT5-DRS`, revision
`d8ec0dea6b9ac786927a864bfe87bca0951b2ce7`. Its public card documents native
text-to-DRS usage but not the exact training split. Its saved configuration is
ByT5-base, with 581,653,248 parameters. The model is task-specific contextual
text interpretation, unlike the previously tested dictionary-definition
relation classifier. Nevertheless, transfer to these descriptive phrases is
an empirical question.[^3]

The PMB5 paper trains large models on gold/silver English annotations followed
by gold-only fine-tuning. Its ByT5 results fall from 93.1 Smatch on compositional
substitutions to 84.8 on extensions; long texts yield 5.5 with 65.4% malformed
outputs. These are warnings about task difficulty, **not performance claims for
this base checkpoint**.[^4] A different contextual DRS parser also reports sense
and role errors together in its manual audit. Internally compatible predictions
need not be correct interpretations of the source.[^5]

## Actual run

One CPU model, two compute threads, FP32, one input at a time, greedy decoding.
No input was truncated. The fifteen inputs contain 28–167 byte-model tokens;
a separate native-format control, “I am a student,” is excluded from construction.
The run took 140.40 seconds including loading/download work. Its own `/proc`
high-water mark was 4,262,720 KiB, approximately 4.07 GiB. No paid resource was used.

| Stage | Observed result |
|---|---:|
| Selected descriptions / distinct notes | 15 / 13 |
| Passed local sequence/reference checks | 11 descriptions / 9 notes |
| Excluded malformed descriptions | 4 |
| Literal patterns / construction links | 137 / 155 |
| Generalized patterns / construction links | 1,955 / 6,656 |
| Recurring distinct-note sets, literal / generalized | 7 / 32 |

The last three rows are structural counts, not semantic quality scores.
All patterns, including one-note patterns and unhelpful ones, remain saved.
No minimum-count menu, title generator or navigation simplifier was applied.

Four descriptions fail local checks:

| Row / note | Source topic | Observed problem |
|---|---|---|
| 187 / N026 | Washing dishes after food preparation | Ends after `make … Product +2`, pointing beyond the sequence. |
| 345 / N065 | Making cafe operators experience loss of internet | Ends mid-relation at `Them`. |
| 375 / N047 | Baking bread after clearing ashes | A cleaning-agent reference points before the first concept. |
| 544 / N096 | Preparing spaghetti sauce | Ends after frying's patient reference, without its target. |

All outputs emitted EOS before the 2,048-new-token allowance was reached.
Installed Transformers 4.57.1 applies that override, giving a total limit of
2,049 including the decoder prefix. There is no forced-EOS setting. Therefore
the endings around 256 tokens are not an unnoticed 256-token inference cap.
Why the checkpoint chooses those endings remains unproven; training-time
truncation is only a possible explanation. Increasing the limit again is not
a justified next experiment. Some outputs that pass syntax checks also omit
source content, such as the fireworks or caffeine contrast.

## Useful paths that actually exist

The following are analytical readings of saved patterns, not generated or
adopted UI titles. Complete machine paths through the shared preparation
pattern, including dictionary intermediates and every source witness, are in
[shared-preparation-paths.json](./SGC01/shared-preparation-paths.json).
[inspected-paths.json](./SGC01/inspected-paths.json) preserves five additional
paths through the food/material patterns.

The generalized pattern `Ge4a69898bcb685754923` contains
`preparation.n.01 — MadeOf → food.n.02`. Its three sources are:

| Note / row | Original mask fragments | Native paired concepts |
|---|---|---|
| N100 / 350 | `sirloin`, `cut`, `steaks` | preparation — MadeOf → steak |
| N089 / 866 | `Bread`, `salt`, `yeast`, `mixing` | preparation — MadeOf → bread |
| N076 / 673 | `chef` | preparation — MadeOf → food |

Bread reaches `food.n.02` through baked goods. Steak reaches it through cut
of meat and meat. Thus a Food pattern reaches the shared preparation pattern,
which reaches the more specific bread and steak patterns. At the note level,
Food contains N022, N076, N085, N089 and N100; the preparation pattern narrows
that to N076, N089 and N100; the bread and steak endpoints each retain their
own source note. Those transitions are real, although the last choices are
far too sparsely supported to establish a useful production menu.

`MadeOf` is not a faithful account of preparing food: the action is not made
out of bread or steak. Still, these notes genuinely concern food preparation.
The grouping is not rejected merely because the relationship name is wrong.
The chef source is weaker evidence for a specific action: its broad culinary
description was inherited from the subject generator, while its mask is just
`chef`. The complete note supplies food context, but the parser did not infer
the broader description itself.

There are two important qualifications to this gain. First, literal
`preparation.n.01` already contains those same three notes. Generalization
adds a material-qualified shared pattern and paths, not additional notes in
that preparation group. Second, SPC02 already recovered the bread/steak
relationship. This is evidence that a different construction can express it,
not a new recovery over the preceding baseline.

A separate, clean material grouping arises at `cut.n.06`: steak/N100 and
brisket/N085 are both meat cuts. The latter retains the correct local
`cook.v.01 — Theme → brisket.n.01` relationship. Its erroneous smoker/person
relationship elsewhere does not erase that success.

## What still separates related material

Three saved patterns illustrate the unresolved construction issue:

| Pattern | Notes | Limitation of the current construction |
|---|---|---|
| cook — Theme → food | N085 | Does not join the noun-based preparation — MadeOf → food pattern. |
| food — Goal → preservation | N022 | Does not join the preservation-headed pattern below. |
| preservation — Theme → food | N013 | Uses both a different relationship arrangement and a different Food sense. |

Exact role matching intentionally does not invent their equivalence. This
separates constructor limitations from missing source evidence: N022's graph
does preserve a beet/preservation connection even though its separate freezing
concept is wrong and disconnected. N013's graph preserves food preservation
despite interpreting stock as company equity. More complete graphs alone do
not guarantee that differently represented topical meanings will meet.

WordNet also has two relevant Food senses: one for nourishment substances and
one for solid foods. Neither is an ancestor of the other in the cached
hypernym relation. A single correct bread sense happens to reach both through
different paths; steak reaches the solid-food sense. The fact that both would
often be called “Food” in a browser does not make their graph identities equal.
The complete dictionary paths are saved, rather than silently joined.

## Source interpretation audit

Every selected description was compared with its complete original note and
inline mask. The full evidence, exact output, concept definitions and decoded
relationships are in [SOURCE-EVIDENCE.md](./SGC01/construction/SOURCE-EVIDENCE.md).
The four malformed cases above were not silently repaired. The eleven others
have these useful components and limitations:

| Row / note | Useful source meaning retained | Material limitation |
|---|---|---|
| 88 / N094 | Drinking coffee | Flavour becomes atmosphere; experience becomes acquired knowledge. The caffeine contrast disappears. |
| 91 / N039 | Storms disrupting a parade; dinner grilling | Rounds become professional calls; grilling is an unknown sense. Fireworks disappear. |
| 350 / N100 | Steak preparation | Beef becomes cattle; the material relationship is misnamed. |
| 378 / N022 | Beets and meals | Side dishes become spatial side plus tableware. |
| 405 / N069 | Goodness for one's sake/peace | Sake is correctly purpose, not wine; peace becomes absence of war and purpose/ownership becomes Creator. |
| 468 / N013 | Food preservation | Stock becomes corporate equity; storage's Theme is pantry, not the stored stock. |
| 572 / N094 | Drinking coffee | A second drinking event produces coffee as its Result. This is the same note as row 88, not independent recurrence. |
| 673 / N076 | Culinary craft and chef | The food-preparation expansion came from the saved description, not the one-word chef mask. |
| 711 / N085 | Cooking brisket | The smoker becomes a tobacco-smoking person and cooking's Beneficiary. |
| 866 / N089 | Bread preparation | Only salt is attached to the involvement relation; yeast/mixing coordination remains separate. |
| 904 / N022 | Beets for preservation | Preparation targets the garden-grown adjective. Freeze means becoming motionless and has no beet participant. |

This is not a binary error rate for eleven entire graphs. Formal errors vary
in their relevance to browsing. What matters is whether the specific meaning
used to form a destination is supported. For example, side-dish/tableware is
an actual wrong material interpretation, even if other beets in the same note
would correctly place it under Food.

## Recurring-pattern audit scope

The generalized inventory has 39 most-specific patterns across its 32 recurring
note sets: 22 single concepts and 17 linked pairs. All are inspected; the full
inventory remains available. This is not an audit of all 1,955 potential choices.

| Recurring pair family | Count | Source-based interpretation |
|---|---:|---|
| preparation / MadeOf / food | 1 | Useful grouping with the qualification above. |
| Sub / coordination | 5 | Includes a preparation member of a coordination, not a newly shared activity. |
| Creator | 3 | Inherits the coffee-experience and own-peace relationship errors. |
| Theme | 2 | Mixes side/tableware and pantry-storage interpretations; the broader pattern also has a genuine preservation witness. |
| person / Role / person | 1 | Combines author and chef roles with the wrongly interpreted smoker. |
| entity / PartOf / entity | 1 | Combines storm rounds with the incorrect beet/time attachment. |
| event / Participant / entity | 1 | Generic event introduction, including unknown `event.v.01`. |
| abstraction / MadeOf / physical entity | 1 | Adds financial stock made of a chicken to preparation patterns. |
| physical entity / Attribute / entity | 1 | Combines harvest/beet and person/craft bindings; no useful shared narrowing established. |
| change / Time / fourth dimension | 1 | Temporal notation rather than a shared substantive subject. |

These cover all seventeen. Correct witnesses do not validate incorrect ones
in the same pattern. In particular, the stock source is culinary, but its
financial interpretation is not a sound explanation to propagate.

The single concepts include useful food, meat-cut, meal and preservation
groupings. They also include people introduced as authors and temporal
notation. Turning every DRS condition into a selectable subject would expose
irrelevant choices such as the fourth dimension from ordinary tense handling.
Frequency or acyclicity does not decide which of these are useful subjects.

No reported construction cycle exists: both graphs are acyclic, and every
child's notes are a subset of its parent's. This avoids SPC02's demonstrated
meaning-switch cycle because numbered senses persist through paths. It does
not prove the initial sense choices or category choices correct.

## Decision

Do not adopt this checkpoint or package its unfiltered graph as a browser.
Do not discard the useful preparation and meat-cut groupings. Do not make exact
logical-role correctness a new product requirement, or attribute every absent
connection to one general parser failure.

The run reduces uncertainty about this specific native parser and constructor:
useful local material-qualified paths can be constructed, but its automatic
input does not establish improved complete coverage or meaningful category
selection. Better end-of-sequence allowance is not the next intervention.
Another parser is not justified solely because this one made mistakes.

A [static dictionary check](./SGC01/lexical-boundary-check.json) makes the next decision more specific. It uses
source-appropriate senses and their recorded relationships, without running
another model or altering any graph:

| Source comparison | Available under unchanged rules | Still unavailable |
|---|---|---|
| Bread baking / brisket cooking | The excluded bread output already has bake/Theme/bread. Its activity and the valid cook/Theme/brisket pattern can meet at create-from-raw-material/Theme/food. | Recovering this pair would not address nominal preparation or preservation. |
| Grilling / frying | Source-supported grill and fry senses share `cook.v.03`. | Native roles differ, and dinner versus beef have different Food ancestors. |
| Steak cutting / bread mixing / cooking | Cutting and mixing support generic preparation; the existing grouping is useful. | No noun/verb hypernym link joins preparation to cooking. Selecting the heat-specific cooking-noun sense simply to create that path would change the source meaning. |
| Pressure-canning / freezing | Food-canning verbs can reach preserve; the correct freeze sense concerns causing food to freeze. | The freeze sense does not reach food preservation or cooking. Broth and beet first meet at matter, not either Food sense. |

This check does **not** establish that correction is useless. It identifies
one recoverable shared pattern and several independent missing relationships.
A full fifteen-input annotation control now would largely repeat an available
constructor result while leaving those central gaps predetermined. Do not
run it merely to obtain cleaner graphs.

A subsequent [NounAtlas/VerbAtlas resource check](./PREDICATE-FRAME-RESOURCES.md)
finds genuine shared noun/verb activity classes, but not the missing source
bindings. Adding those mappings to the unchanged graphs would give a broad
four-note PREPARE union without a new shared preparation/material pattern.
The lookup question is answered; repeating it as an experiment is unnecessary.
Contextual argument evidence, category selection and complete navigation remain
unproven dependencies. No replacement model or frame hierarchy is adopted.

## Reproduction and preservation

[verification.json](./SGC01/verification.json) records the exact input checks,
baseline hashes, structural checks, output lengths and semantic replay hashes.
The native run and initial construction snapshots remain unchanged. A later
one-line validation fix rejects a supplied null dictionary entry rather than
treating it as a missing entry. Its new regression test failed first; the fix
changes none of the saved semantic outputs. The current-source replay is
byte-identical for inputs, decoded graphs, dictionary, results and both reports.
The source report deliberately preserves original and native-output whitespace.
Both generated reports also retain their original final blank line for exact
replay; the resulting whitespace warnings do not indicate altered inputs.

Seventy-five relevant production-path tests pass, including twenty-two new
tests. Source witnesses retain exact node identities, roles, contexts and
dictionary ancestors. All eight checked GDC09/SPC01/SPC02 files match the
pre-run commit. These checks establish reproducibility and implementation
invariants, not semantic validity. Unrelated HiT work remains untouched.

From `oracle-mvp`, using the existing Python environment with NumPy:

```sh
python sse_multivector/semantic_graph_construction.py \
  --native sse_multivector/navigation-research-v1/SGC01/native \
  --lexicon sse_multivector/navigation-research-v1/SGC01/construction/lexicon.json \
  --evidence sse_multivector/geometric-hierarchy-v1/GDC09/evidence.json \
  --output /tmp/sgc01-replay-new
```

An existing output directory is refused. This replays construction without
loading the model or downloading WordNet. The model revision, generation
parameters and runtime versions remain in the native configuration.

## Sources

[^1]: Johan Bos (2023), [The Sequence Notation: Catching Complex Meanings in Simple Graphs](https://aclanthology.org/2023.iwcs-1.20.pdf), sections 2–3 and Appendix B; [PMB thematic roles](https://pmb.let.rug.nl/roles.php).
[^2]: Santiago Ontañón (2016), [RHOG: A Refinement-Operator Library for Directed Labeled Graphs](https://arxiv.org/pdf/1604.06954), graph subsumption and section 2.4. Formal refinement results, not an evaluation of note navigation.
[^3]: [XiaoZhang98/byT5-DRS native card and pinned files](https://huggingface.co/XiaoZhang98/byT5-DRS/tree/d8ec0dea6b9ac786927a864bfe87bca0951b2ce7). The sparse card leaves exact training provenance unresolved.
[^4]: Zhang, Wang, van Noord and Bos (2024), [Gaining More Insight into Neural Semantic Parsing with Challenging Benchmarks](https://arxiv.org/html/2404.08354v2), sections 3–4, especially model sizes, training settings and Table 8.
[^5]: Shen and Evang (2022), [DRS parsing study](https://aclanthology.org/2022.starsem-1.19.pdf), section 6. Its error analysis concerns another parser, not this checkpoint.
