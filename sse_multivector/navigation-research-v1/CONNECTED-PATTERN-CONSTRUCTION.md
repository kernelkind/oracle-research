# Connected patterns and category paths

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

SGC02 finds useful shared meanings after removing the requirement that source
relationships have identical labels and directions. It does not establish a
better browsing hierarchy. Two new food-activity groups have genuine source
support, but their surrounding paths still omit relevant notes. The distinction
matters: generating a meaningful parent is progress; obtaining smaller note
sets is not evidence that its children narrow correctly.

## Controlled change

SGC01 produced semantic graphs from fifteen frozen descriptions belonging to
thirteen notes. Eleven graphs from nine notes passed local sequence/reference
checks. SGC02 reuses exactly those eleven graphs and the same WordNet dictionary.
The four malformed outputs remain excluded and all fifteen inputs remain saved.
No descriptions, masks, word senses, participants, or browser memberships were
corrected. No model was run.

The control requires an exact directed relationship, such as
`preparation — MadeOf → food`. The changed construction requires an existing
edge between the two concepts, regardless of its label or direction. It retains
every native edge as evidence. It does not join arbitrary concepts from one
description or follow a chain of intervening concepts. Replacing endpoints
with dictionary ancestors is unchanged. Single-concept categories and their
memberships are unchanged.

The [pre-run plan](CONNECTED-PATTERN-CONSTRUCTION.md#sgc02-study-design) asks whether precise role identity prevents
useful broader categories. Type and direction changed together, so their
individual effects are not isolated. This is a known-example construction
experiment, not unseen-note accuracy or a comparison of complete systems.

## Food activities: a real connection, incomplete membership

The changed construction produces `activity.n.01 — food.n.02` with four notes:

| Note | Frozen description supplied to the parser | Native connection used |
| --- | --- | --- |
| N100 | Beef and steak preparation. | preparation — MadeOf → steak |
| N076 | Food preparation and the culinary craft of chefs. | preparation — MadeOf → food |
| N089 | Bread preparation involving salt, yeast, and mixing. | preparation — MadeOf → bread |
| N022 | The author is preparing this year's garden-grown beets for preservation by freezing. | beet — Goal → preservation |

The dictionary connects preparation and preservation to activity, and steak,
bread and beet to the same solid-food sense. The exact control had no category
with this four-note set—not merely no category with the same relationship label.
Its preparation/food category held the first three; the beet/preservation
relationship remained separate.

The native labels are not precise event descriptions: preparation is not
literally made of steak. Nevertheless, these connected concepts accurately
support topical categories about working with food. Treating their imperfect
role names as grounds to discard that shared subject would be too strict.

The original notes and masks are below. These are frozen masks, not new evidence
selections. The descriptions above may express more than the selected words;
N076, whose mask is only `chef`, is an especially clear instance of that existing
representation change.

**N100 · V940**

> Alright today's been pretty solid.
>
> Picked up a ⟦sirloin⟧ strip sub primal for $10 a lb ⟦cut⟧ 15 ⟦steaks⟧ about 1.5-2" thickness.
>
> Trimmed about 3lb of fat for making tallow and about a quarter pound of some connective tissue and scrap meat for the dog.
>
> Saved the excess myoglobin to add in the dogs food and will put some some cold water and sunflower seeds for the chickens tomorrow.
>
> I finally got to use the new vacuum sealer and this one is much better than the food savers I've used in the past. I got this on a deal from Amazon for 30% off and love it after using it. If you need one check out the Nesco VS-12
>
> #beef #foodstr #foodpreservation #cooking #steak #cooking #grownostr #prepping #plebchain #homesteading
>
> https://image.nostr.build/270bbbc11299301ee5b4678883c5d48ab2f95eb13b1417093186ba855f4d90e5.jpg

**N076 · V709**

> Tandori spice chik with somo sexi yogo. On pure fire with best handmade wild rose wine,  #purelife #food #⟦chef⟧ #foodstr no compromise
>
> https://image.nostr.build/d9fce20da7cd056362daca85445508eafc7620bf706788474b1dc28e4875971e.jpg https://image.nostr.build/a648216b769b08347153de65a019f5968d249882cefa912b8c64519d36ca95cf.jpg
> https://image.nostr.build/07e9f6b72f1983601c5f5733b7b889fd6fbe0e8a25e40f131edf1ad299cacd20.jpg

**N089 · V806**

> Gm nostr
>
> ⟦Bread⟧ superstition requires ⟦salt⟧ to be added at a distance from ⟦yeast⟧ before ⟦mixing⟧ 🤔
>
> https://image.nostr.build/cc4282a3aa0bc2b42942e1f9e1e6a5cbd9db22ec6d82cee2ef6a7ff665cbe63e.jpg

**N022 · V149**

> ⟦This year’s beets⟧. Vac sealed and ⟦ready for the freezer⟧. Not too bad for a 4x4 ⟦raised bed⟧. 5 meals of sides in a pinch. I am looking forward to having more garden space but this is good while we are still in a half acre lot in town. https://image.nostr.build/b4349cc1251dccf78990620ee851ad0ae449327da16ac31391e3e71fafdbe65c.jpg https://image.nostr.build/5c7e4ba19bb3c2e98cb57753679d33be2bbad3a07900afc86315c85f80bc46e4.jpg

### What the saved paths establish

The following readings describe selected saved patterns for this analysis.
They are not generated labels or a newly adopted menu. Every intervening
dictionary step is preserved in `./SGC02/audit.json`.

```text
Food: N022 N076 N085 N089 N100
  Food activities: N022 N076 N089 N100
    Food preparation: N076 N089 N100
      Bread preparation: N089
      Steak preparation: N100
    Food preservation: N022
      Beet preservation: N022
  Cooking food: N085
    Cooking brisket: N085
```

The new activity/food pattern supports both preparation and preservation
refinements. This was unavailable as one paired parent in SGC01. Existing Food
and Activity singleton roots already provided routes to the component notes,
so this is an additional meaningful intermediate description, not the discovery
of previously inaccessible source notes.

Two omissions prevent treating this as validated navigation:

1. Food → Food activities drops only N085, even though cooking brisket is a food
   activity. The graph has a correct local `cook → Theme → brisket` connection.
   Its verb sense cannot reach the noun activity through the permitted dictionary
   links. Neither insufficient sample density nor wrong role identity explains
   that specific exclusion.
2. Food activities → Food preparation drops N022, although the frozen
   description explicitly says the beets are being prepared. Its preparation
   verb is linked to `garden-grown`, while beet is linked to preservation.
   Role relaxation does not repair that missing participant connection, and the
   verb cannot become the preparation noun through the current hypernym rules.

Thus the parent/child descriptions have sensible conceptual relationships, but
the smaller returned sets do not demonstrate correct semantic discrimination.
There is no requirement that preparation and preservation be disjoint choices.

**N085 · V786**, omitted from Food activities:

> #foodstr starting out with a bang this morning. ⟦Brisket on the smoker⟧ for about 3 hours now. https://image.nostr.build/bb53e68600aed853077353e5865e7c7700dfcbd40903b1e0d7852e461d7d70c9.jpg

Frozen description: Cooking brisket on a smoker.

The parser separately misreads `smoker` as a tobacco-smoking person. That is
not why its valid cooking/brisket connection fails the activity category.

## A second Food category splits essentially the same subject

`activity.n.01 — food.n.01` joins N013's stock preservation with N089's bread
preparation. That two-note set is also absent from every SGC01 pattern. Both
source connections support activities involving food, despite their different
native roles. N089 is the same note and mask shown above.

**N013 · V100**

> Got the ⟦stock pots rolling⟧ today for a batch of ⟦chicken stock⟧. We save carcasses when we butcher and a couple of times a year do this. I’ll ⟦pressure can⟧ it and ⟦store in the pantry⟧. Should get around 25 quarts with this batch.
> #grownostr
> #homesteading
> #foodsecurity
> #foodstr https://image.nostr.build/aead0ba70aa9ec698013666afe87bb76d74d9a19dbb7b93ceb0de953fa2e3386.jpg

Frozen description: Pressure-canning homemade chicken stock for pantry storage
is a form of food preservation.

Here the dictionary treats `food.n.01` as nourishing substance and `food.n.02`
as solid food. Their common ancestor is Matter, not a shared Food concept.
Bread reaches both senses; steak, beet and the native generic solid-food node
reach only the latter. The result is two overlapping food-activity destinations,
with no supplied food-level parent collecting the five notes.

The connected Activity–Matter pattern does collect those five, but the existing
Activity singleton already had exactly those notes. Calling that pattern
“Food activities” would add meaning absent from its key. Similarly,
Preservation–Matter joins N013 and N022, but those notes already shared the
Preservation singleton. These are not additional demonstrated retrieval gains.

The two new food-activity supports also equal intersections of the corresponding
existing singleton row sets. This experiment does not establish that native-edge
evidence outperforms simple co-occurrence. No co-occurrence condition was run;
the earlier malformed coffee-shop input is not a passed negative control here.

## Complete recurring-pattern audit

Both generalized inventories contain 32 recurring note sets, but they are not
the same 32: ten sets appear and ten disappear. The literal condition changes
none. All memberships, witnesses and gains/losses are saved, including unhelpful
patterns. “Recurring” means at least two distinct source notes, not repeated
masks from one note.

The generalized inventory has 38 most-specific representatives for these sets:
25 connected patterns and 13 singletons. Most-specific means no narrower saved
pattern retains the identical notes; it does not mean best, correct or suitable
for display. All 25 connected representatives were checked against their full
source witnesses and the [original notes/masks](./SGC01/construction/SOURCE-EVIDENCE.md).

| Pattern ID | Endpoint concepts | Source-based judgment |
| --- | --- | --- |
| Gf6998481878a00e0ecfe | activity / food 2 | New meaningful shared food activities; omissions discussed above. |
| G605f65f29fe969dd1cd1 | activity / food 1 | New meaningful food activities, split from the previous pattern by dictionary senses. |
| G36f94f976d4ef51e4450 | food 2 / preparation | Useful existing three-note preparation meaning; not a new support gain. |
| Gc4c0feb628df443405c0 | matter / preservation | Genuine preservation connections; same notes as existing Preservation. |
| G1c139ee234be661e61e0 | activity / matter | Genuine local food-work connections, but generic meaning and existing Activity note set. |
| G8b58dcb63d271a373521 | abstraction / food 1 | Combines five-meal quantity, preservation and preparation. Food is shared; abstraction adds no demonstrated useful choice. |
| G9638337349e2b95ee52f | abstraction / person | Inner-peace advice and chefs' craft; no shared specific topic established by this abstraction. |
| G413c326f790b4f1e18ea | abstraction / organism | Adds chicken through the erroneous financial-stock sense to the preceding kind of mixture. |
| Gc8478e150ce03d6573f2 | activity / whole object | Pantry storage and chefs' craft attached to a person. Not a shared practical activity category established by these endpoints. |
| G1c70ec7ab2c217b6f113 | artifact / entity | Beets' side dishes are wrongly parsed as tableware; pantry is an artifact. Not evidence of a shared kitchen-equipment topic. |
| G00344b447466d656594c | entity / part | A wrongly lexicalized “form of preservation” and salt as part of a coordination. No common narrow source topic established. |
| Gae3544ad260314f64c58 | entity / vertebrate | Cattle and chicken enter through wrong meat/stock interpretations. The original notes both concern food, but that does not validate an animal-based derivation. |
| Gdf830373f92326698ea4 | entity / state | Coffee flavour is misread as atmosphere; personal peace as absence of war. Not a supported shared state-of-mind category. |
| G5a12b744247c24ac3ba4 | act / change verb | Storm disruption of a parade and preparing beets for preservation. Generic actions/changes do not establish a meaningful common choice. |
| G4e35a9cef6a7f6faf4f6 | change verb / time coordinate | Time arguments of those events; not a substantive temporal topic shared by the masks. |
| G54c7148590e95599b1f7 | entity / phenomenon | Rain/storms and harvest-as-outcome. No narrower common topic established. |
| Gd8853a814e091b3edc8d | person / person | Mixes author/chef roles, people inequality and the wrongly human smoker. Not a supported interpersonal subject. |
| Gedea7e98d8d1c25543a1 | entity / unknown event verb | Parser-created event placeholder attached to preparation material/coordination; no independent useful meaning. |
| G6e83b3fd84cd82b32d79 | abstraction / entity | Many unrelated source edges, including lexical errors; no informative shared topic beyond generic existence/abstraction. |
| G43470e24b65f69ef9065 | abstraction / physical entity | Food work, pantry, people's motives, quantity and storms; generic overlap, not a validated shared category. |
| Ge80778fe9ece65a1aed1 | act / physical entity | Food work plus misread rounds of storms and chef/person attachment; insufficient common subject. |
| G9b6da913175847401b67 | entity / entity | Almost all native noun relationships; no meaningful distinction for navigation established. |
| Gab7376eee4c58d7168be | entity / organism | Authors, chef, wrongly human smoker, yeast, beef misread as cattle, and chicken attached to financial stock; generic overlap. |
| G47e84f5712ce292d9e71 | entity / physical entity | Broad mixture of materials, people and weather; no demonstrated useful common category. |
| Gbfba077518d2e299b629 | entity / psychological feature | Native events/acts plus misread experience/rounds and representation scaffolding; no supported shared psychological topic. |

The one literal connected representative (`Gb9accb2cbff16daf30ff`, entity /
preparation) combines coordination placeholders in N076 and N100. Its support
already existed under the exact role and adds no useful category meaning.

All 13 generalized singleton representatives remain byte-identical. Food in its
two senses, meat cuts and meals have recognizable source support. Matter,
physical entity, people, organisms, attributes and the unknown event placeholder
are either extremely generic or affected by the already documented source
errors. Time-coordinate, part and essential-substance interpretations do not
establish corresponding substantive topics. This is not a new precision score
for singleton categories or a claim that broad categories are inherently wrong.

The ten disappearing note sets likewise have no demonstrated lost useful
category in this audit. Their most-specific exact representatives are generic
Theme, Creator, Attribute, Role and coordination combinations. One contains
food-preparation witnesses mixed with financial-stock/chicken through MadeOf;
others depend on writer/smoker or beef/animal errors. Their complete witnesses
are in `lost_representatives` in audit.json. The exact inventory remains saved;
these are changes in the candidate representation, not deleted source evidence.

## Decision and remaining construction problem

The experiment supports relaxing exact source-role identity when proposing
broader topical connections. It weakens the case for acquiring a more precise
event-role model before any further construction work. It does not show that
role information is always dispensable, that edge evidence beats co-occurrence,
or that the resulting categories recover all appropriate notes.

The next consequential issue is the generalization order itself. Correct
local cooking/food evidence exists, yet the allowed noun/verb links do not
connect it to food activities. Two ordinary food senses share only Matter.
Repairing category names, pruning levels, or tuning a frequency cutoff cannot
supply those absent semantic paths. Nor should a food-specific manually added
edge be presented as a general solution.

Before another construction run, inspect resources that relate the same
meaning across grammatical forms and supply useful broader concepts. Preserve
the distinction between equivalence, broader meaning and mere association.
Require an actual source-grounded path improvement from the proposed relation
set, and inspect new admissions as well as recoveries. The native parser's
wrong senses and four excluded graphs remain separate limitations. No new
model, ontology mapping or navigation hierarchy is adopted by SGC02.

## Reproduction and evidence

- [Frozen plan](CONNECTED-PATTERN-CONSTRUCTION.md#sgc02-study-design), configuration (`./SGC02/construction/config.json`),
  complete results (`./SGC02/construction/result.json`),
  exact-counterpart comparison (`./SGC02/construction/comparison.json`), and
  [recurring inventory](./SGC02/construction/INVENTORY.md).
- Audit data (`./SGC02/audit.json`) contains every representative's native
  witnesses, gained/lost sets, exact-control comparisons, and all steps along
  the five inspected paths. Verification script (`03bd9e45:sse_multivector/navigation-research-v1/SGC02/verify.py`) checks the
  frozen hashes, replays the saved production code and recreates that artifact.
- [Complete original evidence](./SGC01/construction/SOURCE-EVIDENCE.md) retains
  all fifteen originals, inline masks, unchanged descriptions, native parser
  outputs and local-check failures. The examples above preserve their text
  while normalizing whitespace for reading.
- All 89 relevant tests pass, including the 14 new connection/comparison tests.
  The new tests first failed before implementation. Existing tests were not
  changed. Exact construction remains byte-identical; connection construction
  replays deterministically. DAG and support containment checks establish
  structural consistency, not semantic correctness.

From the repository root:

The second command requires a previously nonexistent output directory.
Configuration elapsed time is observational; result, comparison, input,
inventory and source snapshots replay byte-for-byte. No model download,
inference or paid resource was required for this comparison.

## Research sources

SGC02 is informed by the [SGC01 source/representation analysis](./SEMANTIC-GRAPH-CONSTRUCTION.md)
and [predicate-frame investigation](./PREDICATE-FRAME-RESOURCES.md). Its bounded
constraint relaxation is consistent with ordered graph refinement, but is not
a replication of a complete graph-search system or evidence for its browsing
quality: Santiago Ontañón (2016), [RHOG: A Refinement-Operator Library for
Directed Labeled Graphs](https://arxiv.org/pdf/1604.06954), sections 2–2.4.
The distinction between contextual graph evidence and whole-expression
co-occurrence is motivated by the preserved [CAP03](./SUBJECT-DESCRIPTION-CONSTRUCTION.md)
and [DSP01](./DEPENDENCY-DESCRIPTIONS.md) cases, not tested by a new negative
control in this run.

## SGC02 study design

### Question

Does requiring an exact relationship type and direction unnecessarily prevent
useful broader note categories? SGC01 retains genuine preparation/food and
beet/preservation connections, but its patterns cannot share them when the
native labels or directions differ. Fine-grained event logic is not a browsing
requirement. Conversely, arbitrary words from the same description do not
necessarily express a shared subject.

### Fixed evidence and intervention

Use SGC01's eleven accepted native graphs, the same source records, and the
same WordNet ancestor dictionary. Preserve all fifteen input records and the
four exclusions in the evidence. This is a targeted comparison on nine included
notes from thirteen selected notes, not a complete-corpus coverage study.
Do not rerun a model, correct an input or sense, infer a missing participant,
add frames, tune a threshold, or change the browser.

Control: SGC01's exact, directed single-role patterns.

Changed condition: patterns contain two concepts joined by an existing source
edge, without requiring that edge's type or direction. Keep the native edge,
node identities, direction and contexts in each witness. Replace a concept
only with its existing dictionary ancestor. Never form a pair merely because
its concepts occur in one description, or connect through an arbitrary path.

This jointly relaxes relationship type and direction. A gain does not isolate
which of those two restrictions was responsible. The tested decision is whether
precise role normalization is necessary before this construction can progress.
Single-concept patterns and their memberships must remain unchanged.

### Hypothesis and competing explanations

Hypothesis: forgetting the exact role requirement while preserving actual
connected participants produces at least one useful, source-supported broader
pattern joining relevant notes that no corresponding exact-role pattern joined.
Its category must support recognizable narrowing in a saved path; counts or
renamed patterns alone are insufficient. No exact taxonomy is prescribed.

One pre-run opportunity is the shared activity/food abstraction of preparation
and preservation. It would be a broader food-related activity meaning, not an
assertion that every activity is the same preparation process. The source
dictionary, not a hand-added activity relationship, determines whether the
path exists. An unexpected coherent result can also support the hypothesis.

Competing explanations for apparent gains include generic or incidental
concepts, source interpretation errors, a misleading paraphrase of the relaxed
pattern, and notes already discoverable through an equally useful existing
pattern. Missing gains can arise from wrong senses, absent participants,
dictionary gaps or insufficient sampling rather than essential role precision.
Inspect every witness of a claimed gain and check relevant omissions within
the available inputs. Do not call a source error caused by role relaxation when
the same error existed in the control.

The coffee-drinking source's erroneous `Result → coffee` can still support a
coffee-drinking topic without asserting coffee production. In contrast,
CAP03's “more complete disconnection” at a coffee shop must not become “more
coffee” through whole-description co-occurrence. These earlier observations
motivate keeping connections; the latter malformed SGC01 input remains excluded
and is not advertised as a passed experimental control.

### Decision consequences

Would either outcome change the next decision?

- Useful new connected patterns weaken the case for acquiring a precise-role
  model first. Retain only the supported capability claim; category selection,
  other lexical gaps and broader transfer remain open.
- New pairs that cannot sustain recognizable meanings or useful paths do not
  justify adoption. Identify whether role information was actually needed or
  whether other fixed inputs explain the problem before choosing a remedy.
- Only generic combinations or changes already matched by a simpler control
  provide no consequential construction improvement. Do not expand this run
  merely because it creates more or fewer patterns.

### Evaluation and preservation

Save both conditions in full, including one-note patterns, original witnesses,
construction links and unhelpful output. Compare patterns sharing the same
unordered endpoint concepts, retaining every exact-role counterpart rather
than choose one convenient control. Inventory every recurring connected-pattern
note set and its most-specific patterns. Audit all such representatives and
all witnesses of claimed gains. Preserve complete paths and the full original
notes with inline masks for any presented evidence.

Verify tests first against production code, unchanged exact output, unchanged
singletons, no invented pairs, note deduplication, support containment,
acyclicity and deterministic replay. Structural checks are not semantic scores.
Use only local deterministic construction; no inference or paid resource.

### Research basis

The [SGC01 report](SEMANTIC-GRAPH-CONSTRUCTION.md) and
[predicate-frame investigation](PREDICATE-FRAME-RESOURCES.md) distinguish
useful local topical connections from exact event semantics. Order-labelled
graph refinement supports generalized labels and deleting constraints, but
does not establish semantic usefulness for text browsing: [Ontañón 2016,
sections 2–2.4](https://arxiv.org/pdf/1604.06954). This experiment is a bounded
relaxation, not a claim to reproduce that library or its complete search.
The [CAP03](SUBJECT-DESCRIPTION-CONSTRUCTION.md) and
[DSP01](DEPENDENCY-DESCRIPTIONS.md) records supply the connection/co-occurrence
distinction and its limitations.
