# GDC09 navigation research

The original GDC09 tree, masks, vectors, labels, and browser remain unchanged.
The objective is a repeatable construction method, not a hand-repaired 100-note tree.

## Current evaluation decisions — September 15, 2026

**Coffee → Music at Coffee Shops is approved for evaluation.** The user explicitly
approved this category relationship, superseding the earlier No in
[TRUE06/U02](./TRUE06/user-review.json). The parent is `S9c440e7f47`; the child is
`S8ea08f1aff`, with these masks:

- N004 · V035: ⟦Rave at a coffee shop⟧
- N038 · V295: ⟦playing⟧ ⟦coffee shop⟧ ⟦music⟧

The [saved TRUE output](./TRUE10/graph/scores.json) for
`premise: This text is about Music at Coffee Shops. hypothesis: This text is about Coffee.`
is native No, with score `0.009861395630151667`. The fixed `> 0.142` rule also
rejects it. Under the updated user judgment, both rules miss this relationship.
Repeated rows for equivalent Coffee titles are the same model input, not
independent failures. No new inference was performed.

This approval concerns this pair only. The reverse direction was not adjudicated;
the earlier Food consumption → Having drunk coffee rejection remains unchanged.
That evaluation approval did not change a hierarchy edge, category title, mask,
or score. How to recover this missing relationship automatically remains open.

Separately, the user approved all six notes in the
[TRUE12 membership review](./TRUE12/membership-review.json): N004, N005, N017,
N024, N038, and N065. These are note-level membership decisions, not approvals of
every individual mask or of other category relationships. The saved review
session had state SHA-256
`2aabc553e6cd68d9fb63f610fd79e63a76bffb4a08ca48e1eab5c77fe6583667`.

The [TRUE06 report](./TRUE06/RESULTS.md) and
[TRUE12 report](./TRUE12/RESULTS.md) remain frozen experiment evidence. Their
original judgments and pending-review language predate these decisions; they
are not the current evaluation verdicts for the items above.

## Complete category inventory — TRUE13

A failed title is not a rejected group. TRUE10 incorrectly excluded
`Sf5a4b23523` because its generated title, “Coffee shop chains,” was rejected.
The underlying seven-mask group had not been rejected. TRUE13 restores it as
`#coffeechain`, the user's category name, with explicit title-override provenance.
Its masks and original generated-title record are preserved.

The inventory is now checked against the original source packets:

- HDBv2 selected 64 groups. Three earlier user grouping rejections remain unchanged.
- All 61 remaining groups must be represented, regardless of title-review status.
- Two previously reviewed equivalent pairs are consolidated without losing masks.
- This leaves 59 categories, with no title-based exclusions.

[TRUE13](./TRUE13/categories.json) shows every category, including disconnected
ones under the root. It preserves the 3,306 existing relationship scores and
checks only the 116 directions involving the restored category. Native TRUE
answers determine links; no Coffee link is inserted manually. Cycles would stop
publication, not trigger silent deletion or consolidation.

The 116 new checks produced one accepted relationship: Coffee → `#coffeechain`
(native Yes; score 0.7825745). The other 115 were native No. The graph has no
cycles. All 48 original accepted relationships remain unchanged.

The full view also preserves the saved TRUE12 Coffee/Tea membership additions.
It contains 79 distinct notes; notes and highlights remain visible recursively.
The other 21 original notes have neither retained HDBSCAN membership nor an
accepted Coffee/Tea membership in these results. This is not a new exclusion.
The known missing Coffee → Music at Coffee Shops link remains uncorrected;
the Music category itself is present, not hidden.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./sse_multivector/run-true13-hierarchy.sh
```

Enter descends; N shows the current category's notes and all descendants.
D shows only directly assigned notes, including direct notes also present in
children. O shows notes that appear in none of the current category's children
or deeper descendants. All three views show full original notes with the saved
combined inline masks for the current category. Empty results stay empty;
Escape returns to the category menu and preserves its selection.
Category IDs identify the original groups. `--check` validates the saved view
without opening the UI.

[The plan](./TRUE13/plan.json) records inventory and preservation hashes;
[the completion record](./TRUE13/completion.json) records graph and output hashes.
The current handoff checks the full source inventory before generating inputs,
accounting only for explicit consolidations. Missing titles/groups cause an
error instead of filtering. TRUE10–12 remain frozen comparison evidence.

Next, inspect the restored categories and their actual placement. This separates
the corrected omission from remaining title, membership, and relationship errors.

For Coffee, N shows 22 notes, D shows 18 directly assigned notes, and O shows
13 notes absent from all descendants. O excludes a whole note when it appears
below the category, even if its masks differ. This action works for every
category in the existing UI; it does not change memberships or saved masks.

## Earlier focused Coffee and Tea review — TRUE12

The [expanded view](./TRUE12/hierarchy/categories.json) packages the saved
TRUE12 membership additions: Coffee has 22 notes and Tea as a beverage has four.
It shows only these two branches, with all three original Coffee children and
their contents unchanged. It does not add the approved Music at Coffee Shops
edge or create subcategories for the newly included notes.

Membership is additive: every original note remains, and every saved mask score
strictly above 0.142 contributes its source note and exact highlights. The
browser overlays the union of those masks and the existing category/descendant
masks. Source notes, titles, model scores, category links and the original
TRUE11 browser are unchanged. This is a candidate to inspect, not an assertion
that its navigation is adequate.

Open the expanded view:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./sse_multivector/run-true12-hierarchy.sh
```

Use the same command with `--baseline` for the original Coffee (nine notes) and
Tea (two notes) branches. Enter descends; N displays all notes at the current
category, including descendants; D displays direct notes only; h returns to the
parent from the category menu. `--check` validates either view without opening
the terminal UI.

[The packaging manifest](./TRUE12/hierarchy/manifest.json) records the input and
output hashes. Packaging uses no inference and refuses to replace an existing
output directory. This focused view remains available for comparison; use TRUE13
above to inspect all categories without this branch filter.

## Earlier construction research

[USC01 — source meanings and pairs](./USC01-RESULTS.md).
All fifteen unchanged descriptions and all 128 nonempty USM02 word assignments
produce singleton and same-description pair hierarchies. Cooking → Cooking with
meat supplies a supported new local destination; transformation with seasoning
is another plausible distinction. These are not complete-navigation results.

The full 202-pair semantic audit also exposes artificial narrowing: Cooking plus
Act excludes two cooking notes merely because they lack a second eligible word,
although Cooking already entails Act under the fixed dictionary. Forty-two
most-specific pairs have identical or ancestor-overlapping endpoints; nineteen
lose notes relative to the narrower singleton. Existing wrong senses, lexical
ancestry gaps, and description omissions cause separate errors. The next
justified control is same-description conjunction that can reuse an occurrence,
not another sense-matching sweep. It has not run or been adopted.

All original notes, inline masks, word scores, source witnesses, two complete
audit partitions and reconstruction evidence are preserved. Seventy-six tests
pass, and all result/graph/lexicon/input files replay byte-for-byte. The browser
and original GDC09 remain unchanged; no review UI is packaged before wrap-up.

Preceding construction experiment: [SGC03 — broader concepts](./ONTOLOGY-CONSTRUCTION.md).
Adding pinned SUMO noun and verb mappings to the unchanged eleven source graphs
creates locally useful Food → food/process → preservation/preparation/cooking
paths. The shared activity parent includes brisket cooking, which WordNet-only
construction missed there. A new Food/preservation pattern joins stock and beets.
This is actual candidate construction, not merely static ancestor lookup.

It is not a dependable semantic order or a complete browsing improvement.
Generalization also introduces shipping containers from generic containers
and learning processes from coffee experience. Some occupation/attribute
derivations are formally problematic without being bad topical destinations:
a chef note can reasonably concern occupations. Existing wrong source senses remain;
correct local food results also rely on a globally imperfect animal/human Food
mapping. Class-only mapping admission is insufficient. The connection controls
show different behavior from co-occurrence, not demonstrated better membership.

All three conditions replay, all original WordNet patterns and witnesses remain
unchanged, and complete masks, native graphs, paths, controls and all candidate
patterns are preserved. The 157 final recurring representatives are not approved
categories. Repeated note sets, source omissions and menu selection remain open.
The completed [mapping and source-meaning audit](./MAPPING-VALIDATION.md)
finds no justified drop-in mapping repair. The authors' correction release
changes ontology definitions as well as noun mappings and supplies no matching
final verb table. Learned methods examined predict supplied ontology
relationships; they do not establish independent correction of these errors.
Five fixed-witness dependency checks identify affected destinations without
rebuilding or adopting a mapping blacklist.

The [source-occurrence audit](./SOURCE-OCCURRENCE-GROUNDING.md) now separates
candidate availability from contextual sense selection. Existing token offsets
are usable, but the saved parser turns beet into boot and supplies nonexistent
lemmas for tomatoes and simmering. Removing those restrictions is a different
question from repairing a generated DRS graph. The edge-control audit finds no
demonstrated semantic advantage requiring that graph; it does not prove that
relationships never matter. The beets/preparation omission also has two
independent barriers: a missing direct edge and missing lexical ancestry.

[USM01](./USM01-PLAN.md) selects a bounded direct-occurrence comparison using
one released LMMS sense representation: saved-lemma filtering, original-word
morphological lookup, and unrestricted matching. The original-word control
tests whether bypassing faulty lemmas explains any apparent improvement.
The [completed comparison](./USM01-RESULTS.md) processes all fifteen descriptions
and 134 lexical targets, including the four descriptions the DRS parser could
not process. Original-word lookup explains the main lemma-error recoveries;
unrestricted matching additionally finds a useful frying meaning for sautéing
but introduces unsupported specifics such as beef broth for chicken stock.
Dropping POS also lets bread become breading and beef become complaining.
Neither condition resolves every source meaning; preparing beets still maps to
preparing a speech. All originals, masks, scores and judgments are preserved.
The completed [USM02 control](./USM02-RESULTS.md) reuses those frozen vectors
and retains saved POS during original-word lookup. It preserves useful tomato,
beet and simmer recoveries and avoids bread/beef grammatical misreadings, but
blocks useful decaffeination, canning and homemade meanings. All 402 previous
comparisons and 1,579 scores reproduce exactly. This fixed condition supplies
USC01 above; it is not accepted as a final representation. Current source
identity checks and a corrected process-memory measurement are documented;
historical run files remain unchanged.

Preceding construction experiment: [SGC02 — connected patterns](./CONNECTED-PATTERN-CONSTRUCTION.md).
With SGC01's eleven accepted graphs and dictionary fixed, relaxing exact
relationship labels/directions produces two genuinely shared food-activity
patterns. One joins beet preservation with the three food-preparation notes;
the other joins stock preservation with bread preparation. Both note sets are
new, but neither establishes better complete navigation. Food activities still
misses brisket cooking; its Preparation child misses the preparing-beets note.
Two ordinary food senses remain split into overlapping destinations.

All 25 recurring connected representatives and their source witnesses are
audited. Generic pattern growth is not credited as semantic progress. The
generalized inventories each have 32 recurring note sets, with ten gained and
ten lost—not identical sets. Existing singletons remain unchanged. All 89
relevant tests pass; exact and relaxed construction replay, and originals,
inline masks, all witnesses and five complete inspection paths are preserved.
No browser is adopted. The comparison weakens the case for requiring precise
event roles before proceeding, but leaves lexical generalization, source errors,
category selection and complete-note coverage unresolved.

The [semantic-order investigation](./SEMANTIC-ORDER-RESOURCES.md) found a
direct construction precedent and concrete SUMO paths across the missing
noun/verb and Food distinctions. It also finds scope mismatches: the resource
is not a verified semantic order. [SGC03's pre-run design](./SGC03-PLAN.md)
separates approximate construction from mapping validity using noun-only and
noun-plus-verb conditions and same-order singleton controls. The completed
comparison and collateral-admission audit are linked above.

Preceding construction experiment: [SGC01 — contextual semantic graphs](./SEMANTIC-GRAPH-CONSTRUCTION.md).
Fifteen unchanged descriptions from thirteen notes were given to a native
text-to-DRS parser. Eleven outputs pass local sequence/reference checks; four
are malformed despite ending themselves below the allowed output length.
Generic graph generalization produces useful food-preparation and meat-cut
paths, but no improved complete browsing arrangement. The preparation group
retains the same three notes as its literal counterpart. Wrong dish, stock and
smoker senses coexist with useful local patterns; neither whole-graph rejection
nor accepting a correct final note set would be a sufficient semantic audit.

All originals, inline masks, native outputs, numbered senses, source witnesses
and construction paths are preserved. Seventy-five relevant tests pass, and
construction replays byte-for-byte. Both constructed graphs are acyclic; this
does not certify their meanings or category choices. No browser is adopted.

A static source/dictionary check finds one baking/brisket grouping recoverable
through better input, but several cross-form preparation/preservation links
remain unavailable under the fixed hypernym and exact-role rules. Do not run
a full annotation control merely to repeat that known limitation.
[NounAtlas/VerbAtlas lookup research](./PREDICATE-FRAME-RESOURCES.md) verifies
shared noun/verb activity classes. But adding them alone to the saved graphs
would not repair the missing beet participant or create a new shared
preparation/material pattern. That lookup question is now answered; a further
test needs contextual argument evidence and must exercise actual construction,
not just produce cleaner frame names. Category selection and complete-note
coverage remain open. No replacement model, frame hierarchy or browser is adopted.
The directly related release chain also leaves joint nominal/verbal inference
unverified: NounAtlas's joint release is described as forthcoming, and the
inspected MultiSRL text interface selects verbs only. No substitute model is run.
Precise event-role recovery must not become a requirement without showing its
value for the browsing construction.
The resulting controlled comparison is complete in SGC02 above. It retains
actual source edges rather than combining arbitrary words from a description.
That construction constraint has not been shown superior to co-occurrence in
this small run; the earlier coffee-shop counterexample was malformed and
remains excluded.

Preceding construction experiment: [SPC02 — phrase structure and broader meanings](./STRUCTURAL-GENERALIZATION.md).
Using all frozen SPC01 expressions, structural lexical matching recovers three
Food-preparation notes through bread preparation, steak preparation and outdoor
grilling. It also interprets washed dishes as food, and rejects valid cooking
and preservation topics whose grammatical arrangements differ. All 18 new links
into existing recurring multiword destinations and the 79 further word-only
links are audited; fewer links are not equated with better semantics.

Ambiguous dictionary paths also create a 271-expression cycle. Food → Sake
uses a drink sense; Sake → Interest switches to a purpose/interest sense. Food
then reaches all 100 notes through the graph. A relevant destination note can
hide a wrong source witness, so memberships and derivations are evaluated
separately. Neither graph is adopted. This motivated the contextual
representation experiment SGC01 above, including relationships across different
phrasing—not another word-matching or grammar tweak.
Seventy-two tests pass; final artifacts replay byte-for-byte across hash seeds.
The original inputs and browser remain unchanged.

Preceding construction experiment: [SPC01 — source phrases and category paths](./SOURCE-PHRASE-PATHS.md).
The unchanged 945 descriptions generate 2,129 expressions and 1,268 observed
head-extension links. Requiring two distinct notes leaves 234 choices, 204 roots
and 30 links; eight links return identical note sets. The complete source audit
finds useful Diet → Carnivore diet and Tea → Hot tea refinements, but also
reporting-language choices and incomplete destinations. Food preparation omits
bread and steak preparation; Food preservation omits the beet-freezing note.
Sea salt flakes does not contribute to the recurring Sea salt category because
that semantic subexpression is absent from the saved grammatical structure.

This establishes partial phrase-based construction, not a sufficient hierarchy.
No browser, parser revision, threshold or semantic repair is adopted. All source
occurrences, menus, native parses and the 30-link audit are preserved; 49 tests
pass and construction replays exactly. This motivated contextual generalization
of complete expressions into broader paths with justified memberships. SPC02
above tests one grammatical/lexical approximation and exposes its unresolved
context and binding requirements. [Method-fit research](./CONSTRUCTION-MECHANISMS.md)
records the construction precedents and qualifications; no independent cutoff
or stopword tweak is adopted.

Preceding construction diagnostic: [CPC01–CPC02 — memberships and paths](./CATEGORY-PATH-COMPATIBILITY.md).
CPC01 scores all 945 saved descriptions from 100 notes against 12 frozen
source-derived category candidates. Both fixed classifier cutoffs remove all
three clearly meaningful existing refinements. At the development cutoff,
wrong child admissions break Bread → Sourdough bread and Chicken → Chicken stock;
a missed parent admission breaks Salt → Sea salt. Malformed and duplicate
candidates remain. Better memberships alone do not establish better construction.

CPC02's fixed word-form control recovers the classifier's only two development
gains, Chicken/N080 and N100, without its incorrect additions. Across the six
judged complete categories it retains 28/31 supported assignments, adds none of
557 unsupported assignments, and preserves all three paths. The three missing
Bread notes require more than inflection matching. This is a stronger simple
reference, not a solved taxonomy: incomplete choices and duplicate children
remain. No cutoff, classifier or new browser is adopted. All evidence, source
overlays and deterministic replays are preserved; 47 tests pass.

SPC01 above tests complete source-phrase proposals and observed extensions,
using these failures as controls. Independently predicted note containment
cannot be the sole evidence for meaning; automatically propagating child errors
upward is not a demonstrated repair. No additional normalizer or threshold
sweep is justified by CPC01–CPC02.

Preceding transfer diagnostic: [TCC04 — the frozen cutoff](./CATEGORY-CUTOFF-TRANSFER.md).
On 12 different notes with all 145 saved descriptions, the TCC03 cutoff misses
10/13 supported Bread, Chicken and Salt assignments; native 0.5 misses none and
incorrectly adds one bread-baking note to Chicken. All missed assignments have
genuine supporting masks. All 90 judged within-category positive–negative
comparisons are correctly ordered. The fixed cutoff fails transfer; useful
rankings remain. No cutoff or hierarchy is adopted. All 435 scores, originals,
inline masks, judgments, hashes and an exact offline replay are preserved.

A separate retrospective check of combined TCC03+TCC04 scores finds a shared
tradeoff retaining 30/32 supported assignments with six incorrect additions,
all Morning greetings. Both misses concern the bagel note, under Bread and Salt.
This is development feasibility, not validation or an adopted rule. It motivated
the now-completed CPC01 family/path test above before adding calibration.
Category generation, meaningful relations and overall browsing remain open.

Preceding decision-method research: [literature and shared-cutoff tradeoffs](./CATEGORY-DECISION-METHODS.md).
The TCC03-only development cutoff was 0.9969531560953688; its full derivation,
alternatives and source-supervision audit are preserved unchanged as frozen
TCC04 inputs. TCC04 above supersedes that report's pending-transfer prescription,
not its measured development counts. Neither result justifies probability
calibration solely to make scores look less extreme.

Preceding note-membership diagnostic: [TCC03 — complete available evidence](./COMPLETE-NOTE-CATEGORY-EVIDENCE.md).
Scoring all 181 existing descriptions from the same 20 TCC02 notes restores
the judged Coffee note ordering and preserves Morning greetings ordering.
The cafe recovery has a genuine venue witness; it does not depend on its
hashtag-derived maximum. But maximum pooling worsens the native 0.5 decisions:
Morning greetings admits all 20 notes. No cutoff or hierarchy is adopted.
The shared-cutoff transfer test is now complete in TCC04 above; fitting only
these two labels was development, not general success.
Category generation and meaningful parent relations remain unresolved.
Full scores, all note maxima, source
judgments, originals/masks and exact offline replay are preserved. No browser
or baseline change; pending HiT files remain untouched.

Preceding discrimination diagnostic: [TCC02 — individual categories](./INDIVIDUAL-CATEGORY-DISCRIMINATION.md).
With the model and category wording fixed, 25 descriptions from 20 notes
outside TCC01 produce five Coffee witness inversions; greeting witness scores
remain separated. Frozen pre-score judgments retain ambiguous scopes. Witness
errors do not all add irrelevant notes, and unscored descriptions can recover
missed notes. TCC03 above tests that architectural distinction instead of
incorrectly extrapolating selected-witness errors to complete note retrieval.
All 50 scores and an exact replay are saved. All 72 regression tests pass;
the runner's old defaults reproduce TCC01 scores and tokens exactly.

Preceding membership diagnostic: [TCC01 — native classification](./NATIVE-CATEGORY-MEMBERSHIP.md).
All 25 predeclared supported assignments are recognized across the 14 frozen
records, but the native 0.5 rule also accepts unsupported meanings. Reversing
the same eight category choices turns chicken-with-yogurt into Bread membership;
adding other labels turns rosemary bread into Coffee. Single-category scoring
removes many interaction errors but still accepts greeting/coffee associations.
Its supported/unsupported scores remain separated in this small complete audit,
which motivated the different-record TCC02 check above. No cutoff, membership
rule or hierarchy is adopted. All 336 scores and complete originals/masks are
preserved; 71 tests pass and the complete offline replay is exact. Category generation and meaningful
parent relations remain separate unresolved requirements. No browser change.

Preceding representation diagnostic: [DSP01 — grammatical connections](./DEPENDENCY-DESCRIPTIONS.md).
On 14 frozen subject/mask records, dependency parsing retains useful local
phrases and separates coffee experience from the coffee-shop internet dispute.
But valid common subjects also have different grammatical paths; correcting
the rosemary/bread attachment does not make those paths identical. Native
parsing errors are recorded separately. Do not build an exact-tree miner as
a sufficient category rule. All parses, 1,121 paths, full originals/masks and
analytical controls are preserved, with an exact offline replay. No hierarchy
or browser changed. TCC01 above audits and tests native text-to-category
classification that can accept different grammatical witnesses. It does not
provide a category-generation solution.

Preceding representation diagnostic: [PPR01 — complete subject descriptions](./PHRASE-DESCRIPTION-NEIGHBORHOODS.md).
On the same 945 records, the base Sentence-BERT recovers the nine other known
morning-greeting notes within ten neighbors and the rosemary/bread note at position
two under Euclidean distance. Both models distinguish coffee-taste experience
from operators experiencing internet loss. Phrase-BERT improves preservation
matches but regresses elsewhere; neither supplies a membership or containment
rule. The audit separates correct notes from incorrect winning masks. All 90
inspected records and 50 full notes, both vector sets and scores are preserved;
41 tests pass and offline replays are exact. No hierarchy or browser changed.
Retain base affinity as possible proposal evidence, not a grouping rule. Next,
investigate explicit compositional relationships as evidence for shared and
broader meanings. DSP01 above tests grammatical structure without adopting it
as a construction rule.

Preceding construction diagnostic: [CAP04 — order and adjacency](./ORDERED-PHRASE-CANDIDATES.md).
The same 945 subject records yield useful repeated phrases, including ten morning
greetings omitted by CAP03. Word order removes the specific More-coffee collision;
adjacency also loses the valid rosemary/bread combination. Repeated reporting
language remains, and equivalent greeting expressions select different note sets.
Neither pattern family is a sufficient semantic representation. All patterns and
154 inspected source records are saved; 38 tests pass, with an exact replay.
No hierarchy, baseline or browser changed. PPR01 above tests complete grounded
subject expressions. Cross-gap attachment, wording equivalence and containment
remain separate questions; do not extend pair enumeration or tune frequency as
a semantic solution.

Preceding construction control: [CAP03 — existing subject descriptions](./SUBJECT-DESCRIPTION-CONSTRUCTION.md).
The mask control reproduces CAP02 exactly. Using saved per-mask subjects adds
useful Food abstractions and local preservation/harmful-food refinements, but
also produces 556 candidates and 359 links dominated by reporting/function words.
The meaningful relationship in `more complete disconnection` is lost when its
words are grouped with `more coffee`. Explicit good-morning, processed-food and
sea-salt combinations are present in the input but missed by the single-feature
seed family. This separates candidate availability from missing interpretation.
No browser is adopted. CAP04 above tests retaining shared multiword descriptions
and bounds what order/adjacency can establish. Attachment, equivalent meanings
and broader membership remain open; no new extractor has been selected.
All inputs, both outputs, source snapshots and the complete link audit are saved.

Preceding representation audit: [CSA01 — contextual attributes](./CONTEXTUAL-ATTRIBUTES.md).
Contextual word senses can add lexical abstractions such as Bread → Food, but
do not alone encode phrase relationships or every legitimate topical parent.
The two `experience` uses already differ in part of speech; separating them
would not establish deeper interpretation. Chicken meat and live chickens have
only physical entity/entity as shared hypernym ancestors. This limits a
sense-only route, not the validity of either separate or combined browsing topics.
Ten source masks and all queried dictionary entries are preserved. No WSD or
SPLADE model was run. CAP03 checks the existing descriptions before selecting
another component; word senses remain a possible component.

Preceding construction test: [CAP02 — shared candidates](./SHARED-CANDIDATE-CONSTRUCTION.md).
Keeping source features and the relation rule fixed, shared-feature closures
add five source-supported topical links, including Bread → Bread with rosemary
and Coffee → Coffee shops. The full output has 336 candidates, 43 links and 304
roots; grammatical structure, mixed word meanings and membership omissions
remain. All old candidates are unchanged. This is not an adopted browser.
Next, investigate source-grounded phrase/relationship attributes that distinguish
shared meanings from shared spelling, without discarding valid dispersed masks.
CSA01 above narrows the role of word-sense models in that investigation.
CAP03 above refines the immediate question. No parser, extraction rule or model
has been selected.

Preceding construction audit: [CAP01 — candidate coverage](./CANDIDATE-COVERAGE.md).
MDH02's complete-mask seed rule excludes `food` despite 45 matching masks from
15 notes, and also excludes recurring recipe, processed-food and chicken-stock
evidence. All 22 saved candidates reproduce exactly. The 315 excluded recurrent
features are not 315 valid subjects: grammatical words and ambiguous uses remain.
CAP02 tests bounded shared-feature proposals with source evidence and the
relation rule fixed. No original category, mask, vector, membership or browser changed.
HiT remains an unrun alternative rather than the automatic next experiment.

Latest task-trained relation evidence: [SRR01–SRR03](./SENSE-RELATIONS.md).
A WordNet definition-relation classifier preserves Bread → Sourdough but also
produces false Coffee/greeting and human-diet/Dog parents. Explicit definitions
change the errors rather than reliably removing them, adding Music → greetings
and Bread → Coffee. Retaining both names and definitions also fails. Neither a
new hierarchy nor another description rewrite is adopted. These input variants
do not isolate why the classifier failed. HiT's shared learned representation
was a subsequent lead, but it does not itself supply absent category candidates;
the construction-level reassessment above takes priority.

Earlier contextual-relation evidence: [GDR02](./EXISTING-SUBJECT-RELATIONS.md) and
[GDR03](./SUBJECT-INPUT-RENDERING.md). Existing generated subjects recover greeting
equivalence without GDR01's manual descriptions, but one seed's subject often
does not describe its whole group. A controlled input-format change fixes some
coverage misses and introduces incorrect associated-topic relations, including
Coffee → morning greetings. No automatic classifier, group description or new
hierarchy is adopted. All inputs and scores are preserved. The task-trained
follow-up is recorded above. Earlier [GDR01](./CONTEXTUAL-GROUP-RELATIONS.md) remains the manual-input
control.

Prior group-relation evidence: [lexical broader and equivalent relations](./GROUP-RELATIONS.md).
LGR01 checks all 462 ordered pairs of the 22 frozen MDH02 groups. It proposes
the existing Bread → Sourdough bread link and an animal-sense Carnivore → Dog
link that does not fit the human-diet parent group. It finds no equivalences;
GM resolves to the unit of mass, not the greeting. No new defensible parent
link or browser change results. Full evidence and an offline replay are saved.

Earlier learned-membership evidence: [entailment and relevance models](./MODEL-MEMBERSHIP.md).
NLI01/NLI02 show some useful broader-subject recognition but also abbreviation,
negation and greeting-association errors. RER01/RER02 do not fix membership:
for Coffee, the reranker puts `Good morning` above explicit coffee masks.
All inputs and scores are preserved. No classifier, membership rule or new
hierarchy is adopted by these component tests.

Latest parent-construction evidence: [mask descriptions and hierarchy relations](./MASK-DESCRIPTION-HIERARCHY.md).
MDH02 removes the old-tree dependency and finds three immediate relations, but
literal matching confuses word senses and leaves twenty roots. It is not a new
browser candidate. The record also corrects an `I` candidate caused by stripping
a sleep emoji from its source mask.

Latest membership evidence: [explicit masks and missing notes](./LITERAL-MEMBERSHIP.md).
NMR03 finds four notes outside broad Coffee and two outside Bitcoin through
literal subject evidence. It is an audited diagnostic, not an adopted assignment
rule or a new hierarchy. Source snapshots and all proposed masks are preserved.

Latest browser comparison: [mask distinctions and middle-level scoring](./MASK-DISTINCTIONS.md).
ND02-NP01 removes three repeated textual choices from NP01 while preserving all
retained evidence. It is a small inspectable improvement, not a solved hierarchy.

## NMR01 — original-vector membership

**Question:** Can fixed examples from an existing group recover omitted subject
vectors without admitting unrelated meanings?

The six groups are native GDC09 nodes 1614, 1533, 1551, 1325, 1671, and 1598.
Their masks respectively suggest exercise, sleep, cooking times, coffee-shop
music, kitchen equipment, and coffee/tea. These descriptions select diagnostic
destinations; they are not input features or certified labels. In particular,
1598 already contains a dog emoji, an ice-only mask, and a soda-bread mask.
These are preserved, not silently cleaned before the test.

**Hypothesis:** Original-coordinate support from independent notes can recover
the known exercise omission V620 and additional defensible memberships. Any
unrelated admission is counterevidence to the assignment rule's selectivity.
All proposed masks, not just newly reached notes, require semantic inspection.

For each vector, find its highest cosine to an example from each source note.
Exclude examples from its own note. Average those note scores so repeated masks
from one note do not receive repeated votes. For each existing note, take its
best mask's score against the other notes. The smallest of these scores is the
group's provisional acceptance threshold. An outside vector must clear it and
have at least two other source notes available. Examples remain frozen; new
admissions cannot recruit further members.

This threshold is a hypothesis, **not** a calibrated probability or a statistical
guarantee. Two-note groups are especially weak calibration cases: an existing
mask is scored against one other note, whereas an outside mask is scored against
two. The experiment records this asymmetry rather than claiming independent
validation. Additional held-out-note work is needed before adopting the rule.

The runner records all outside scores, per-note witnesses, every proposed
addition, and full original notes/masks for all proposals and the top twelve
outside vectors. Existing non-members are unlabeled, not presumed negatives.

The design borrows separation of discovery and later assignment from
[Dynamic Hybrid Tree Cut](https://academic.oup.com/bioinformatics/article/24/5/719/200751),
and the use of multiple examples from
[HDBSCAN soft clustering](https://hdbscan.readthedocs.io/en/latest/soft_clustering_explanation.html).
The note-balanced score and threshold above are experimental adaptations, not
those papers' published algorithms. No moved diffusion coordinates, titles, or
text embeddings generated from labels enter the calculation.

Run from the repository root with the existing NumPy environment:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib \
/tmp/crec100-plscan-venv/bin/python sse_multivector/category_membership.py \
  --data sse_multivector/real-note-fine-segmentation-v1 \
  --hierarchy sse_multivector/geometric-hierarchy-v1/GDC09/hierarchy.json \
  --groups 1614 1533 1551 1325 1671 1598 \
  --output sse_multivector/navigation-research-v1/NMR01
```

The output directory must not exist. A reproduction should choose a new output
directory. Configuration records hash the frozen inputs and source code.

## NMR02 — local agreement instead of a group-wide threshold

NMR01's exercise threshold was 0.5498 and rejected V620 at 0.3898. Its kitchen
threshold was 0.2951 and proposed 88 masks, including dinner ingredients and
the word `chef`. Group-wide average affinity and an internal threshold did not
give a reliable boundary. Coffee/tea also proposed plain sourdough-bread masks.
An audit of all proposed additions is retained separately.

**New hypothesis:** Requiring the two nearest examples from different notes to
both belong to the frozen group will retain local subject support while rejecting
the broad spillover seen in NMR01. The nearest examples are found across the
complete original corpus, excluding every vector from the query's own note.
Membership of a note does not transfer to its other masks: the actual nearest
vector must belong to the group. No new member recruits another during the pass.

This changes assignment only. The groups, masks, vectors, and six destinations
stay frozen. Two is the smallest number requiring independent source-note support;
it is not a tuned cosine cutoff. Unknown examples do not supply group support,
but are not presumed semantically negative. The procedure can still miss a valid
point whose neighbors are themselves missing from the group, or accept a weak
point whose nearest available examples are both misleading. Those outcomes must
be inspected rather than assumed away. In particular, no nearest-neighbor rule
alone establishes an absolute semantic confidence.

Run the command above with `--method local` and output directory `NMR02`.
The original mean scores remain available as diagnostics, but no longer decide
admission. This is not a reproduction of a published classifier; it tests the
specific local-support mechanism revealed by NMR01.

The rejection problem also motivated a follow-up reading of
[Tax's nearest-neighbor data description, Appendix B](https://rduin.nl/papers/thesis_01_tax.pdf).
It compares a query's distance to its nearest example with that example's own
nearest-training-example distance. This gives a local reference scale instead
of a group-wide radius. However, the saved exercise numbers already show why
the default acceptance boundary would be too restrictive here: V620 has cosine
0.4452 to V122, whereas V122 has cosine 0.5498 to its closest other-note anchor.
V620 is farther away. This does not invalidate the published method; it rejects
the assumption that adding its default local-density gate automatically solves
our omissions. No new fitted run or tuned ratio threshold was adopted.

## NP01 — bounded descendant promotion

**Question:** Can navigation skip low-value intermediates without losing access
to notes, changing retained category masks, or creating unwieldy menus?

This experiment uses the unchanged GDC09 categories, not NMR01/NMR02 membership
proposals. For each parent, it considers replacing an internal child with that
child's own children. A count-based gain trades one less step against more
choices: `child_notes * (1 + child_count) - parent_notes * (child_count - 1)`.
It performs the highest positive-gain replacement, breaking ties by saved order,
and repeats. The resulting menu is bounded to eight choices. Existing larger
menus may remain but cannot grow. Eight is a prototype setting, not an empirically
validated cognitive limit. `NP00` removes this bound as a mechanism control.

**Hypothesis:** Promotion shortens the repetitive routes while leaving useful
destinations available and keeping menus readable. Every original leaf must
remain; every retained category must have exactly its original complete notes
and mask ranges. Notes no longer covered by promoted children remain directly
accessible at the retained parent.

Preserving leaves does not prove that removed intermediate destinations were
expendable. The review must check the removed groups and newly adjacent
parent/child pairs, including Coffee, Exercise, Sleep, and Kitchen equipment.
The rule cannot validate category meaning, repair membership, or distinguish
two Coffeechain children with effectively the same meaning. Shorter paths alone
will not establish success.

This is a simple experimental cost proxy inspired by
[BioNav](https://www.cs.ucr.edu/~vagelis/publications/BioNav%20TKDE2009.pdf),
not its published optimizer. BioNav assumes an already-valid semantic hierarchy.
Overlapping memberships here also prevent interpreting raw note counts as
calibrated browsing probabilities.

```sh
python3 sse_multivector/select_note_categories.py \
  sse_multivector/geometric-hierarchy-v1/GDC09/categories.json \
  --output sse_multivector/navigation-research-v1/NP01 --run-id NP01
```

The unbounded control uses `--max-choices 0`, `--run-id NP00`, and its own output
directory. Neither run changes the original browser's default artifact.

## ND02 — repeated masked words

The follow-up [research record](./MASK-DISTINCTIONS.md) contains the rejected
common-word-intersection hypothesis, the stricter tested rule, every removal,
preservation controls, provenance, and inspection commands. It also records a
separate category-utility diagnostic that changes no category or membership.
The follow-up NMR03 tests missing explicit subject evidence elsewhere in the
corpus, not another arbitrary pruning threshold.

## NMR03 — literal subject membership

[The record](./LITERAL-MEMBERSHIP.md) separates seed-union growth from omissions
in existing broad destinations, inspects all additions, and preserves uncertain
scope and literal-matching misses. No browsing membership changed. MDH01/MDH02
now test descriptions independent of the old groups; shared wording yields a
few useful relationships but does not supply semantic parent construction.
