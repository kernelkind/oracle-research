# Broader concepts in category construction

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

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

The [pre-run plan](ONTOLOGY-CONSTRUCTION.md#sgc03-study-design) changes only the available broader concepts.
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
`./SGC03/audit.json`. Nothing was manually reparented.

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

- The preparation branch still misses the preparing-beets description for two
  independent reasons. Its `fix.v.12` sense does not reach `preparation.n.01`
  in the frozen order, and the graph lacks a direct fix/beet edge. Removing
  the edge restriction alone—or supplying only that edge—would not recover
  this membership. [Source and order audit](./SOURCE-OCCURRENCE-GROUNDING.md).
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

This replays the saved production paths without a neural model, ontology service
or fresh download. It regenerates the complete inventory and source-evidence
record from the frozen inputs. The resource cache can be recreated with the
saved runner's `fetch` command and pinned revisions.

[^mapping]: Javier Álvez, Paqui Lucio and German Rigau, [Black-box Testing of First-Order Logic Ontologies Using WordNet](https://arxiv.org/pdf/1705.10217v3), section 4.2, especially the distinct translations for ordinary classes and attributes. Their objective is ontology reasoning tests, not note navigation. The experiment's exact mappings, class declarations and definitions are in `SGC03/construction/mappings.json` and `ontology.json.gz`, with pinned source file/line provenance.

## SGC03 study design

Status: construction complete; [findings and qualifications](ONTOLOGY-CONSTRUCTION.md).
The design below records the intervention and controls chosen before the run.
No new inference or browser change was involved.

### Capability and hypothesis

Can a general, released concept resource add meaningful parent–child paths
missing from SGC02, rather than merely produce larger or more numerous groups?
The source graphs already contain a correct cooking/brisket connection, but
their WordNet-only generalization order cannot connect it to the food-work
patterns expressed with nouns. Separate Food senses also lack a shared Food
parent. These are available-evidence limitations, not hypothesized density
problems. [Source evidence](CONNECTED-PATTERN-CONSTRUCTION.md).

The hypothesis is that adding separately identified SUMO ancestors supplies
at least one new, source-supported broader category with meaningful narrowing
and improved coverage of the relevant available notes. A known mapping lookup,
an extra generic parent, or a renamed existing note set is insufficient.
Unexpected coherent paths can support the hypothesis; no exact hierarchy or
preferred number of categories is prescribed.

This tests construction with a fallible resource, not the proposition that
the augmented WordNet-to-SUMO order guarantees semantic containment. The
inspected Food mapping already disproves that universal claim: nourishment
for any animal does not imply human food. This mapping error does not by itself
establish that SUMO's internal subclass order is unsound.
The resulting local memberships and their derivations must be judged separately.
[Research and resource qualifications](SEMANTIC-ORDER-RESOURCES.md).

### Fixed inputs and conditions

Keep SGC02's eleven accepted graphs from nine notes, the exact descriptions,
masks, note identities, native senses, actual edges, connection policy and
existing WordNet ancestors. Preserve all fifteen selected inputs and four
malformed exclusions. Do not repair source graphs, generate descriptions,
infer participants, choose a food-specific relation, or change a browser.

Use one pinned resource revision, with three construction conditions:

1. **WordNet:** replay the complete SGC02 construction.
2. **Additional noun ancestors:** add eligible WordNet-noun mappings and their
   SUMO subclass ancestors, keeping the original senses distinct.
3. **Additional noun and verb ancestors:** add eligible verb mappings as well,
   with everything else identical to condition 2.

Conditions 2–3 distinguish new noun-level category connections from the added
cross-part-of-speech reachability. Their effects are not inferred from the final
counts alone. No threshold sweep, replacement parser or new model is involved.

The original WordNet patterns and memberships must remain unchanged in every
condition. New intermediary ancestors can change generating links and which
patterns have most-specific status; retain and compare those changes explicitly.
The original Food and Activity patterns are not silently repaired or renamed.

### Resource admission before construction

Use SUMO revision `abcb7cc1090c5b35cbfacd9e44e50e50c7434433` and the already
frozen WordNet 3.0 offsets. Preserve original mapping annotations and source
locations. Keep `SUMO:` concept identities separate from WordNet identities;
add no SUMO-to-WordNet reverse mapping and no equivalence collapse.

The initially eligible mappings are positive equivalence/subsumption mappings
to declared classes, used only as candidate forward ancestors. Class ancestry
comes from explicit top-level ground subclass statements. Instance, complement,
attribute-instance and relation-valued mappings must not be recast as subclass
edges. Adjective and adverb mappings remain outside this noun/verb intervention;
their original WordNet evidence is retained. Do not infer participants or new
facts from logical axioms.

Before construction, verify the released mapping syntax, treatment of multiple
annotations, class declarations, closure and resource notices. Record unsupported
or unresolvable mappings rather than guess their semantics. Resource parsing
must distinguish ground facts from quoted text and conditional axioms. Any
cycle must be reported rather than silently collapsed. If these checks require
changing the treatment, amend this plan before running and preserve the reason.

Save the exact generalization paths used by each candidate. Do not whitelist
food mappings because they give preferred results, or blacklist a known bad
mapping to repair this sample. The scope is deliberately approximate: forward
use prevents identity collapse, but does not correct an invalid broadening.
Known scope mismatches remain flagged independently of local source support.

#### Resource preflight decisions

Use the 45 constituents in SigmaKEE's published SUMO domain configuration,
pinned at `9dba684eac829fd1e5d6740b8d28c5e208dc8204`, with their contents from
the SUMO revision above. This is a general deployed domain list, not a selection
of food files or every experimental file in the repository. Save the configuration,
each exact resource hash, and its upstream revision and applicable notices.
[Declared list](https://github.com/ontologyportal/sigmakee/blob/9dba684eac829fd1e5d6740b8d28c5e208dc8204/docker/sigmakee2023/kbs/config.xml).

Parse the complete terminal annotation list. Multiple annotations have a
conjunctive interpretation: retain each eligible class mapping, separately
excluding property/individual mappings. They are not alternative interpretations.
Malformed suffixes or spacing are recorded without repairing or salvaging part
of the annotation list. Conflicting duplicate offsets are excluded; identical
duplicates retain their provenance. This follows the distinction in section 4.2
of [Álvez, Lucio and Rigau, arXiv v3](https://arxiv.org/pdf/1705.10217v3);
it does not establish that the mapping assertions are correct.

Only exact top-level ground `subclass` statements supply class edges.
`instance` facts help identify class roles but do not become subclass edges.
Quoted text, comments, nested conditional statements and partition assertions
are not mined for extra edges. Reject malformed resource syntax and reachable
cycles rather than silently repairing or dropping them. Preserve complete raw
resources in a separate cache and the used facts/definitions/mapping rows with
their source positions in the experiment record. No resource or source-graph
repair is part of the intervention.

### Controls and semantic reading

Inspect every new or changed recurring representative and its native witnesses,
including new meanings whose note set already existed. Also inspect removed
representatives and every new recurring note set. For every claimed improvement,
retain a complete actual parent–child path, source masks inline in full notes,
all memberships, and the
notes excluded at each step. Interpret the class definitions and graph pattern,
not just the displayed word Food, Activity or Preparation.

Compare each claimed connected-category gain with:

- Every existing WordNet-only category with the same note set or an equally
  useful source-supported route.
- Its single-concept categories under the same augmented order. A Food–Process
  category returning exactly Food's notes does not establish a useful extra
  navigation step merely because its pattern is longer.
- The intersection of its endpoint singleton **source-row** sets under that
  same order. An equal intersection means native connections have not shown
  additional discrimination in this sample. An unequal intersection requires
  inspecting the excluded source occurrences; inequality alone is not success.

Complete paths must show a meaningful narrowing, not merely a smaller note set.
Sibling categories may overlap. A broad Food destination can be useful without
matching an imagined finer taxonomy. Inspect incorrect additions and new
misleading paths alongside recoveries; do not present only the motivating food
witnesses. Four excluded parser outputs remain missing evidence, not negatives.

Separate three judgments for a new admission: whether the original source
supports the category, whether the native source graph supplies the claimed
connection, and whether the mapping chain is semantically justified. A correct
note at the end does not vindicate a wrong source sense or mapping. No global
validity or unseen-note accuracy is inferred from this small selected sample.

### Competing explanations and decisions

Apparent gains may come from a useful broader concept, a generic union, a
redundant parent, an invalid mapping, or a source error whose final note happens
to fit. Missing gains may come from absent source connections, inappropriate
ancestors, or an inadequate construction/selection rule. Conditions 2–3 and
the same-order singleton controls distinguish some of these explanations;
source and mapping inspection must distinguish the rest.

Would either outcome change the next decision?

- Meaningful additional paths with justified source witnesses and mappings
  support testing the construction on different, more varied source graphs.
  Category selection and computational growth would remain separate work.
- Locally plausible recovery depending on a known invalid mapping is evidence
  for an approximate candidate only. It does not justify adopting that mapping
  as semantic containment or scaling it without a general treatment of the
  mismatch. Do not claim the original missing category was repaired.
- Only generic or duplicate paths provide no demonstrated navigation gain.
  Do not expand ontology machinery merely because the expected union appears.
- If appropriate ancestors exist but no useful path is constructed, investigate
  the construction or selection restriction. If the available ancestor meanings
  are inappropriate, reconsider the resource rather than tune a frequency cutoff.

### Preservation and verification

Create production-path tests before implementation; verify their expected
initial failures. Test typed mappings, exact offsets, no invented source edges,
no reverse sense collapse, parsing boundaries, closure, unchanged WordNet
supports, deterministic construction and full witness provenance. Structural
consistency does not certify semantics.

Save every condition, resource revision/hash/notice, source snapshot, native
witness, candidate inventory and semantic audit, including one-note output and
unhelpful candidates. Keep frozen SGC01/SGC02/GDC09 bytes untouched. Use local
deterministic processing and public resource reads only; no paid service or
inference is part of this plan. Review-tool packaging remains reserved for goal
wrap-up and requires a demonstrated improvement.
