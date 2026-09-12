# Broader concepts in category construction

SGC03 produced useful additional candidate paths from the unchanged source
graphs. Food preservation now includes both chicken stock and beets. A broader
food/process pattern can include those notes, food preparation and brisket
cooking. No food-specific merge or source repair created these connections.

However, the same general procedure also produces unsupported meanings. Some
come from previously wrong source senses; others come from the added resource
or from interpreting its mappings as ordinary broader-class relationships.
This is evidence for candidate construction, not a dependable semantic order
or an improved complete browsing hierarchy.

## Experiment

The [pre-run plan](./SGC03-PLAN.md) changes only the available broader concepts.
All fifteen selected descriptions, masks and complete notes remain unchanged.
Eleven native graphs from nine notes are usable; four malformed graphs remain
excluded. No new inference, model, parser repair, source correction, category
label generation or UI change occurred.

Each source graph contains named concepts and actual connections between them.
The constructor enumerates single concepts and connected concept pairs, then
generalizes their endpoints. It ignores the edge's role and direction but
retains both in its evidence. A paired category therefore means that its two
concepts are connected in the source graph; it does not automatically mean
one is acting upon the other.

| Condition | Ancestors available | Generated patterns | Recurring note sets | Most-specific patterns for those sets |
| --- | --- | ---: | ---: | ---: |
| WordNet | Frozen WordNet senses and ancestors | 1,464 | 32 | 38 |
| Nouns | The same order plus eligible noun mappings and SUMO ancestors | 5,557 | 49 | 82 |
| Nouns and verbs | The same noun intervention plus eligible verb mappings | 7,276 | 79 | 157 |

These counts are structural observations, not quality scores. Different
patterns can return the same notes. Every original WordNet pattern and all its
members and native witnesses remain unchanged in both interventions.

The general source list is SigmaKEE's 45 configured SUMO constituents, not a
hand-selected food ontology. Files and noun/verb mapping annotations are pinned,
hashed and retained separately. The [resource research](./SEMANTIC-ORDER-RESOURCES.md)
explains why this resource was worth testing and its known limitations. The
31.9 MB downloaded resources required no paid service or neural inference.

## A new food destination

`G45565692d14a728c639b`, the SUMO Food singleton, contains these eight notes:

| Note | Relevant source meaning in the frozen input |
| --- | --- |
| N013 | Making and pressure-canning chicken stock |
| N022 | Beets as meal sides; preserving beets by freezing |
| N039 | Storms threatening outdoor dinner grilling |
| N076 | A chef's food preparation |
| N085 | Cooking brisket on a smoker |
| N089 | Preparing bread with salt and yeast |
| N094 | Drinking decaffeinated coffee for its experience |
| N100 | Cutting sirloin into steaks |

The ninth accepted note, N069, contributes a mask about being good for one's
own peace. Its *complete post* also mentions diet, but that is outside this
experiment's selected mask. The source record makes this distinction visible.
The other four selected notes are excluded because of malformed parser output,
not judged irrelevant.

This Food node joins the two previously separate WordNet Food destinations.
Its eight-note set already existed under the much less informative WordNet
Matter concept. That does not make Food a numerical coverage gain. The useful
change is a more informative, source-supported meaning and additional paths
beneath it—not a larger set or a renamed Matter node.

There is an important resource qualification: SUMO Food is defined as suitable
for humans, while WordNet `food.n.01` covers nourishment for animals generally.
The released equivalence mapping is not universally valid. All eight selected
food contexts are locally compatible with human food, but that does not make
the general mapping sound. A new note about animal feed could expose the scope
error. [Pinned definitions and mapping](./SEMANTIC-ORDER-RESOURCES.md#known-mapping-and-ontology-limits).

## A new shared activity parent

`G0953c4544ac6b557bbcc` requires a Food concept connected to an
IntentionalProcess concept. The latter means a process with a specific purpose
for its agent. It is **not** a generated label saying that every note is about
food preparation.

| Condition | Notes in that pattern |
| --- | --- |
| WordNet | This SUMO pattern does not exist. The earlier Activity–solid Food pattern contains N022, N076, N089 and N100. |
| Nouns | N013, N022, N076, N089, N100 |
| Nouns and verbs | N013, N022, N076, **N085**, N089, N100 |

The noun intervention brings chicken-stock preservation into a shared Food
parent. Adding verbs then brings in brisket cooking through the existing
`cook.v.01 → brisket.n.01` connection. The original source error that interprets
the smoker as a person remains elsewhere in that same graph; it is not needed
for this valid cooking connection.

N085, complete note and unchanged mask:

> #foodstr starting out with a bang this morning. ⟦Brisket on the smoker⟧ for about 3 hours now. https://image.nostr.build/bb53e68600aed853077353e5865e7c7700dfcbd40903b1e0d7852e461d7d70c9.jpg

The frozen parser description is “Cooking brisket on a smoker.” The relevant
native edge is `cook.v.01 —Theme→ brisket.n.01`.
The verb maps forward to Cooking, which is a Making process, then an
IntentionalProcess. Brisket's meat ancestry supplies the food endpoint.
The source, edge and pertinent local broader meanings align here.

N013, complete note and unchanged mask:

> Got the ⟦stock pots rolling⟧ today for a batch of ⟦chicken stock⟧. We save carcasses when we butcher and a couple of times a year do this. I’ll ⟦pressure can⟧ it and ⟦store in the pantry⟧. Should get around 25 quarts with this batch.
> #grownostr
> #homesteading
> #foodsecurity
> #foodstr https://image.nostr.build/aead0ba70aa9ec698013666afe87bb76d74d9a19dbb7b93ceb0de953fa2e3386.jpg

Its frozen description explicitly identifies food preservation. The native
`preservation.n.01 —Theme→ food.n.01` edge supplies the new shared parent.
Preservation maps to Maintaining, then IntentionalProcess. The local food
membership is reasonable; the general animal-to-human Food mapping qualification
above still applies. The separate native financial-stock sense is unnecessary
to this admission and remains an error, not a repaired interpretation.

N022 also has an appropriate preservation/beet witness from row 904. Its
additional row 378 admissions through *harvest as an outcome* and row 904
admission through *time as an occasion* have questionable process mappings.
Those alternate routes do not invalidate the genuine preservation witness,
but a correct final note set must not hide them.

## What actually narrows below that parent

These are waypoints on actual generated paths. The complete intermediate nodes,
exact IDs, memberships and every note removed at each edge are retained in
[audit.json](./SGC03/audit.json). Nothing was manually reparented.

| Waypoint | Pattern ID | Notes |
| --- | --- | --- |
| Food | G45565692d14a728c639b | N013 N022 N039 N076 N085 N089 N094 N100 |
| Food connected to an intentional process | G0953c4544ac6b557bbcc | N013 N022 N076 N085 N089 N100 |
| Food connected to preservation | G63a768150ba5cfe1fe77 | N013 N022 |
| Food connected to preparation | G58b7c19d4e4ae0af7655 | N076 N089 N100 |
| Food connected to cooking | See the complete cooking path | N085 |

The preservation branch meaningfully narrows the broad activity parent to
preserving chicken stock and beets. The preparation branch narrows to the
three unchanged preparation witnesses and can narrow again to bread or steak.
Cooking now has an actual route from the broader food/activity parent.

This does not establish a complete or well-condensed hierarchy:

- The preparation branch still misses the preparing-beets description. Its
  native graph lacks the required preparation/beet connection. Adding broader
  concepts cannot invent that missing evidence.
- N039 remains absent from food/process patterns despite its grilling meaning.
  The native `grilling.v.01` is an unknown placeholder without a dictionary
  ancestor. This is not evidence that storms and grilling are unrelated.
- Purposeful coffee drinking is absent from IntentionalProcess–Food. Its
  drinking sense reaches Ingesting/Process, not the intentional-process class.
  The broader Process–Food pattern includes N094. Neither branch is a canonical
  desired taxonomy; names must respect the actual meanings and omissions.
- The raw paths contain repeated note sets. For example, Food–Maintaining,
  Food–Protection and Food–Preservation all return N013 and N022. The brisket
  path has several one-note steps. These are available refinements, not a usable
  menu or proof of discovery value at each click.

## What the connection control establishes

For Food–IntentionalProcess in the noun-and-verb condition, intersecting the
two singleton **source-row** sets returns all ten accepted food rows. Requiring
an actual connecting edge retains seven rows and excludes rows 88/572 (coffee)
and row 91 (storms/grilling).

This proves that the connection constraint does something different from
co-occurrence in this sample. It does **not** prove better membership. Coffee's
separate experience node acquires IntentionalProcess through a wrong learning
mapping; grilling's own action sense remains unknown. The omitted notes also
have plausible food-activity meanings. Their exclusion cannot be credited as
a clean precision improvement.

The narrower Food–Preparation and Food–Preservation patterns equal their
same-order singleton-row intersections exactly. Those results show no extra
discrimination from preserving the native connection in this sample. They
remain interpretable connected patterns, but a simpler construction control
has not been ruled out.

## Additional meanings and derivation problems

All final 157 most-specific patterns and the 17 noun-condition representatives
that disappear or change status were inspected against the fixed source graphs.
The [complete inventory](./SGC03/INVENTORY.md) enumerates them without approved
titles; [source evidence](./SGC03/SOURCE-EVIDENCE.md) gives every original note,
inline mask, description and native connection. No validity percentage is
claimed: generic patterns and uncertain category utility are not binary errors.

The audit separates incorrect destinations from formally questionable
derivations. The latter need not make a topic irrelevant to its source note:

| Mechanism | Concrete source route | What the evidence supports |
| --- | --- | --- |
| Existing wrong source sense, then an additional narrowing error | N022 side dishes → dishware → generic container → ShipContainer | Neither dishware nor a ship container describes the side-food meaning. The shipping restriction comes from the mapping resource. |
| Mapping changes the kind of thing | N094 coffee experience → accumulated knowledge → Learning/EducationalProcess | Knowledge held is not the process of acquiring or teaching knowledge. The source does not discuss learning. |
| A property or role is treated as the thing that has it | N076 chef → skilled worker → SkilledOccupation → SocialRole | This is not ordinary subclass meaning, but a chef note can legitimately concern occupations. The same destination's N085 member comes from cooking equipment wrongly interpreted as a person. A type defect alone is not a discovery-failure judgment. |

N022 row 378, complete note and unchanged mask:

> This year’s ⟦beets⟧. Vac sealed and ready for the freezer. Not too bad for a 4x4 raised bed. ⟦5 meals⟧ of ⟦sides⟧ in a pinch. I am looking forward to having more garden space but this is good while we are still in a half acre lot in town. https://image.nostr.build/b4349cc1251dccf78990620ee851ad0ae449327da16ac31391e3e71fafdbe65c.jpg https://image.nostr.build/5c7e4ba19bb3c2e98cb57753679d33be2bbad3a07900afc86315c85f80bc46e4.jpg

Its description says the beet harvest provides side dishes for five meals.
The parser selects a container sense of dish. WordNet's generic container
then maps to ShipContainer, defined as designed for container ships. This is
a one-note collateral candidate, preserved even though the recurring inventory
does not show it.

N094 row 572, complete note and unchanged mask:

> ⟦Decafe coffee drinkers⟧ are the purist coffee enthusiasts of them all as they do it ⟦for the experience⟧ and flavour. Unlike the caffeine addicted heathens. Change my mind.

Its description says the coffee is consumed for the experience of drinking it.
The native accumulated-knowledge sense of experience maps to Learning; a second
ancestor route maps education-as-knowledge to EducationalProcess. Neither route
grounds learning in this note. The raw drinking/coffee edge remains meaningful
and supplies a different, locally plausible food/process pattern.

The same class-only admission problem also affects mappings to classes of
attributes: interrupting, involving and satisfying acquire
SubjectiveAssessmentAttribute. Some broad patterns therefore appear everywhere
because actions have been mapped as if they were subjective qualities.
Preparation/preservation acquire PsychologicalAttribute through an existing
WordNet psychological-feature ancestor. That is a cross-resource derivation,
**not** a SUMO assertion that IntentionalProcess is a psychological attribute.

Other inspected qualifications include beef/cattle mapping to female dairy Cow,
harvest-as-outcome and time-as-occasion mapping to IntentionalProcess, and
beet-root mapping to the reproductive-structure FruitOrVegetable class.
These remain in the evidence; no food-specific blacklist repaired the result.

The SUMO class check was insufficient. An annotation can point to a declared
class without asserting that the source is a subtype of that class. The
literature's translation distinguishes ordinary membership from having an
attribute; using a flat ancestor edge loses that distinction. The original
plan already ruled out known individual attributes but did not resolve these
class-of-attribute cases. This run makes the consequence concrete. [^mapping]

## Category choices remain unresolved

Of the 157 final representatives, many describe generic objects, people,
attributes, physical entities, processes, or mixtures of these. Some are
legitimate general truths; others inherit the errors above. Counting them as
new categories says nothing about whether a person would learn what selecting
them reveals.

The most-specific-per-note-set rule also demotes ten original WordNet patterns
after verbs are added, without changing their actual membership. For example,
a broad food pattern can become less specific than a new food/activity pattern
that happens to cover the same sampled notes. This is sample-relative evidence,
not proof that the broader concept has no future browsing value.

The counts therefore do not establish useful menu distinctions, coverage on the
other corpus notes, or robustness to new notes. The original 100-note browser
and its baseline artifacts are unchanged. No UI packaging is justified yet.

## Decision

The experiment reduces one consequential uncertainty: an external concept
resource can enable actual, more informative parent paths unavailable to this
WordNet-only construction, without changing the source graphs. This is stronger
than a static lookup demonstration and weaker than a dependable construction
method. The best paths are locally plausible candidates with explicit mapping
qualifications, not certificates of semantic containment.

The subsequent [mapping and source-meaning audit](./MAPPING-VALIDATION.md)
examines typed interpretation, expert correction and propagation, weakening and
completion, learned subsumption methods, and the actual released correction
archive. It does not justify adding a mapping verifier or swapping the resource.
The archive changes definitions and ancestry as well as mappings; the learned
methods do not establish independent correction of these errors. Some formal
type objections also overstate the topical-discovery problem.

The source audit identifies unsupported meanings, and five fixed-witness checks
locate their mapping dependencies while preserving the existing food/process
memberships. These are not rebuilt
conditions or evidence that a blacklist repairs construction. The source audit
distinguishes wrong available senses, unknown identifiers and absent meanings.
Contextual source grounding is the next research question, not an adopted
replacement: the existing parser consumes generated descriptions rather than
the original note and mask. Sense selection cannot alone create missing
connections or correct later ontology generalizations.

This does not impose an error-free ontology or require every enumerated
candidate to become a valid category. Approximate candidate generation may be
adequate. The consequential issue is whether a general treatment can preserve
the useful paths while reducing the demonstrated wrong meanings at destinations
we might actually expose. Merely reducing the number of candidates would not
answer that question.

No particular verifier, corrective rule, model, or new experiment is adopted
here. A mechanism that only deletes questionable mappings without preserving
useful broader paths would not by itself meet the construction goal. Source
sense recovery and category selection remain independent unresolved dependencies.

## Preservation and verification

The saved constructor replays all three conditions exactly. All original
WordNet patterns, source rows, native witnesses and four exclusions remain
unchanged. Both additions have acyclic pattern graphs and preserve note/row
containment along every edge. This verifies implementation consistency, not
semantic correctness.

The relevant production regression suite passes 61 tests, including the new
resource/order, comparison and experiment tests. Initial missing-module tests
failed as expected before implementation; the noun-to-verb comparison correction
also had a failing production-path test before its fix.

An independent check also matched all 178 known sense offsets against the frozen
WordNet archive directly and checked all 17,726 saved mapping/path steps.
The full parsed 7,118-class SUMO graph is acyclic. All 51 cached resource/config/
tree records match their saved hashes; ontology files also match upstream Git
blob hashes. Neither acyclicity nor provenance validates a semantic mapping.

The parser recognized 17 malformed noun rows and 314 multi-annotation rows in
the full mapping resource. One additional malformed row, offset `08747887`,
ends in `&&%LandArea@` and was recorded as unmapped rather than malformed.
It is absent from every selected input/ancestor, so it changes no construction
result. This is an audit-statistics omission, not evidence of a silently admitted
bad mapping. The saved source snapshot preserves the implementation actually run.

The first launch needed the existing NLTK data directory added to its environment.
The next launch stopped because the comparison initially required noun-created
SUMO memberships to remain unchanged when verbs were added. Tests now distinguish
immutable WordNet evidence from the SUMO expansion being measured. Neither failed
launch produced a saved candidate artifact; neither changed the intervention.

Full raw results, source snapshots, resource notices, all condition comparisons,
same-order singleton controls, added/removed representatives and all one-note
patterns are preserved under [SGC03](./SGC03/INVENTORY.md). Large JSON artifacts
are losslessly compressed for storage; the verifier reads either form.

```sh
python3 sse_multivector/navigation-research-v1/SGC03/verify.py
```

This replays the saved production paths without a neural model, ontology service
or fresh download. It regenerates the complete inventory and source-evidence
record from the frozen inputs. The resource cache can be recreated with the
saved runner's `fetch` command and pinned revisions.

[^mapping]: Javier Álvez, Paqui Lucio and German Rigau, [Black-box Testing of First-Order Logic Ontologies Using WordNet](https://arxiv.org/pdf/1705.10217v3), section 4.2, especially the distinct translations for ordinary classes and attributes. Their objective is ontology reasoning tests, not note navigation. The experiment's exact mappings, class declarations and definitions are in `SGC03/construction/mappings.json` and `ontology.json.gz`, with pinned source file/line provenance.
