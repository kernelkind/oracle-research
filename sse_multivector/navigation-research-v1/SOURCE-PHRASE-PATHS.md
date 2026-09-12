# Source phrases and category paths

SPC01 can construct some meaningful category refinements together with their
supporting notes. It does not produce a usable hierarchy on its own. Many
choices are disconnected, some distinctions are merely reporting language,
and several smaller destinations omit notes that clearly fit their meaning.

This answers the construction question left open by DSP01's fourteen-parse
inspection. It does not establish a complete category-membership mechanism,
make grammatical inclusion equivalent to semantic refinement, or justify a
replacement browser.

## Experiment

The [plan](./SPC01-PLAN.md) was written before execution. The input is all 945
unchanged saved descriptions, masks and originals from CAP04, covering 100
notes. The same cached Stanza 1.11.0 English EWT parser used in DSP01 annotates
the descriptions. It does not parse the original notes or generate new subjects.

For each noun head, the constructor proposes the head, the head with its nominal
modifiers, and that expression with further nominal attachments. It connects
observed extensions of the same head in the same description. Equal lemma and
grammatical structures share a candidate; that candidate receives the notes
where the expression was produced. Source occurrences remain available.

For example, an actual description produces:

> Bread → Sourdough bread → Sourdough bread with cranberry rosemary brown sugar and cinnamon

No independent category classifier decides those memberships, no note-set
containment creates the edge, and no similarity rule connects the remaining
roots. This isolates one construction mechanism. It does not reproduce the
full lexical and semantic machinery of conceptual indexing.

The related-method review is in
[Constructing categories and their relationships](./CONSTRUCTION-MECHANISMS.md).
Its principal qualification remains important: Woods combines structured
phrases with lexical relationships and flexible matching; neither Woods nor
Castanet establishes grammar alone as a solution to semantic browsing.[^1][^2]

## Complete output

There are 2,129 proposed expressions and 1,268 observed links. Of these,
1,895 expressions occur in only one note. They remain in the raw result but
do not count as demonstrated recurring choices.

| Display support | Choices | Disconnected roots | Links | Links with equal note sets |
|---|---:|---:|---:|---:|
| At least two notes | 234 | 204 | 30 | 8 |
| At least five notes | 45 | 41 | 4 | 1 |

These are two views of the same run, not fitted semantic cutoffs. Every original
note appears somewhere in the two-note view; that does not establish that it is
reachable through an appropriate topic. “Author” alone contains 37 notes.

The [complete root menus](./SPC01/construction/INVENTORY.md) include useful
choices such as Coffee, Bread, Chicken and Food alongside Amount, Author, Part,
Things and Year. Coffee has 21 notes, but its only recurring child is “author's
coffee,” with two. Food has 29 notes, with Better food, Many foods and Processed
food beneath it. Bread and Meat remain separate roots rather than refinements
under Food. The allowed same-head relation cannot create those lexical links.

These observations do not make every isolated subject invalid. They show why
this output is not yet a coherent broad-to-narrow browsing menu. A support
filter removes some choices but supplies neither missing relationships nor
missing memberships.

There is exactly one root-to-terminal path with three categories in the
two-note view: Greeting → Good morning greeting → Good morning greeting to
Nostr community, with 7 → 7 → 2 notes. Its first step repeats the same notes;
its second omits other Nostr-directed greetings. All other paths have one or
two categories. Thus useful individual links have not combined into a
demonstrably useful sequence of successive refinements. At five-note support,
the longest paths contain only two categories.

## Some refinements are genuinely useful

Diet → Carnivore diet has five → three notes. Its sources include criticism,
recipe qualification and diet context; the category need not mean adherence
to the diet. Tea → Hot tea has four → two notes with explicit temperature
evidence. Community → Nostr community has ten → four notes addressing or
referring to that community. These are defensible topical refinements, not
necessarily strict dictionary “is-a” relationships.

Other conceptual distinctions are real but return the same notes: Milk → Raw
milk, Shop → Coffee shop and Stock → Chicken stock. That is a navigation
redundancy, not evidence that raw milk is unrelated to milk.

Sourdough bread and Processed food reproduce already-known source meanings.
Their recovery should not be counted as new evidence of semantic capability.
The added evidence is that a fixed, corpus-wide procedure can construct some
of these paths and their source occurrences together, while exposing its
unattractive output as well.

## Smaller destinations can be incomplete rather than narrower

### Preparation → Food preparation

Preparation contains N026, N076, N089 and N100. Food preparation contains only
N026 and N076. However, the two excluded notes have these unchanged descriptions
and original masks:

**N089, row 866 — “Bread preparation involving salt, yeast, and mixing.”**

> Gm nostr
>
> ⟦Bread⟧ superstition requires ⟦salt⟧ to be added at a distance from ⟦yeast⟧ before ⟦mixing⟧ 🤔
>
> https://image.nostr.build/cc4282a3aa0bc2b42942e1f9e1e6a5cbd9db22ec6d82cee2ef6a7ff665cbe63e.jpg

**N100, row 350 — “Beef and steak preparation.”**

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

Both fit Food preparation. The constructor does produce Bread preparation and
Beef and steak preparation, but it has no rule relating their modifiers to Food.
The four-to-two transition therefore does not demonstrate a meaningful
food/non-food distinction in this collection. A broader category can be valid
even when the implementation assigns it incompletely.

### Preservation → Food preservation

Preservation contains N013, N022 and N100. Food preservation contains N013 and
N100. The excluded note is:

**N022, row 904 — “The author is preparing this year's garden-grown beets for preservation by freezing.”**

> ⟦This year’s beets⟧. Vac sealed and ⟦ready for the freezer⟧. Not too bad for a 4x4 ⟦raised bed⟧. 5 meals of sides in a pinch. I am looking forward to having more garden space but this is good while we are still in a half acre lot in town. https://image.nostr.build/b4349cc1251dccf78990620ee851ad0ae449327da16ac31391e3e71fafdbe65c.jpg https://image.nostr.build/5c7e4ba19bb3c2e98cb57753679d33be2bbad3a07900afc86315c85f80bc46e4.jpg

The subject names preservation, but Food is not a literal modifier of it. A
beet→Food lookup alone would not establish Food preservation: the preserved
thing must remain connected to the preservation activity. This is an observed
construction limitation, not a newly discovered absence of the meaning from
the input; the earlier grammatical studies already exposed that distinction.

Similar omissions affect Social media and greetings directed at the Nostr
community. Their full records are in the [edge audit](./SPC01/EDGE-AUDIT.md).

## Phrase boundaries still matter

The familiar Sea salt category loses its multi-note status. N063's risotto
ingredient description produces Sea salt, but N046's bagel description does not:

**N046, row 779 — “Bagels topped with sea salt flakes.”**

> Turn pantry staples into chewy ⟦bagels⟧ 🥯
>
> Toppings : sesame, ⟦sea salt flakes⟧ and plain
>
> #foodstr
> https://m.primal.net/OHSR.jpg
> https://m.primal.net/OHSS.jpg

The native parse makes both sea and salt modify flakes. The constructor produces
Flakes → Sea salt flakes, plus the separate Sea and Salt heads, but not the
intermediate Sea salt phrase. Row 909's alternate bagel description has the same
problem under Toppings. Sea salt therefore remains a one-note candidate.

This trace identifies the actual limitation: the saved grammatical structure
does not expose every useful semantic subexpression. Simply increasing minimum
support cannot recover the missing occurrence. Conversely, enumerating every
word subset would reintroduce the earlier unrelated-word combinations.

The complete Chicken dish and Chicken tractor expressions are generated where
CAP04 had the incomplete common prefix “a chicken.” That is an improvement in
local expression boundaries, but each has only one note. It is not evidence of
a useful recurring branch. The rosemary-bread and coffee-experience paraphrase
controls still lack their shared refinements.

## Not every head extension is a semantic refinement

Author → Post author, Coffee → Author's coffee and Dinner → Author's dinner
mostly follow the reporting language of generated descriptions. Their smaller
note sets omit other equally personal coffee and dinner posts.

The separate Plans → Author plans link is more concrete: the parser marks
“plans” as a noun and “author” as its compound in clauses such as “The author
plans to store the pressure-canned chicken stock in the pantry.” That does not
support the nominal category as rendered.

Cream → Ice cream remains scope-sensitive rather than a certified failure:
there is a plausible cream-based-food relationship, but a compound's head is
not necessarily the intended standalone parent meaning. Better food and Many
foods likewise retain plausible shared meanings despite weak titles. The audit
does not reject unexpected commonalities merely because they are not preferred
category names.

## Decision

Retain the observed useful phrase constructions as evidence and a possible
component. Do not adopt this procedure alone as the hierarchy foundation or
spend another run merely changing the parser, support threshold or stopword list.
Those changes would not supply the absent semantic relationships.

The consequential remaining question is whether **contextual generalization of
complete expressions can construct broader paths and carry justified source
membership together**. Bread preparation → Food preparation is an actual
opportunity in this output; it requires more than generating the word Food.
Beet preservation is a harder control because the food/activity connection
spans a different grammatical structure.

The distinction from CPC01 is important. Independently classifying every note
against broad and narrow labels, then inferring ancestry from the resulting sets,
lost valid paths. A justified semantic relation could instead carry its actual
source witnesses into the broader destination. But propagation must be justified:
a false child-to-parent relation would spread errors, not repair them.

The subsequent [SPC02 experiment](./STRUCTURAL-GENERALIZATION.md) examined the
relevant primary methods and compared lexical phrase matching with and without
grammatical structure. It recovers three justified Food-preparation notes but
also confuses washed dishes with food and loses valid differently structured
cooking/preservation topics. Longer ambiguous dictionary paths switch senses
and form cycles. Neither graph is adopted as a sufficient construction method.

Those findings retain a limited role for source-backed phrase construction
while making source-context interpretation and cross-structure meaning the
next research requirements. They do not justify another parser, support-filter
or word-lookup tweak, or invalidate every possible semantic hierarchy.

## Evidence and verification

- [Frozen plan](./SPC01-PLAN.md).
- [Complete menus](./SPC01/construction/INVENTORY.md), including both support views.
- [All 30 multi-note edges and controls](./SPC01/EDGE-AUDIT.md).
- [Full source notes with original inline masks](./SPC01/SOURCE-EVIDENCE.md):
  488 description rows from 81 notes, covering every endpoint occurrence plus
  diagnostic controls. Export coverage is not a claim of exhaustive semantic
  annotation. All 945 original input records remain in the raw artifact.
- [Raw construction](./SPC01/construction/result.json),
  [all inputs](./SPC01/construction/inputs.json),
  [native parses](./SPC01/native/parses.json), and
  [verification record](./SPC01/verification.json).

All six construction files reproduce byte-for-byte from saved parses. All
fourteen overlapping DSP01 native parse records are identical. Source, code
and cached model hashes match; the three frozen GDC09 artifact hashes match
the pre-experiment commit. There was no second full 945-description model
inference, so the replay claim is explicitly about construction from saved
parses, not repeated model determinism.

Forty-nine production-path tests pass, including ten construction tests and
regressions for prior membership/construction tools. The initial seven tests
failed because the new implementation was absent, then passed; three additional
tests cover disconnected roots and contraction across excluded intermediates.
No approved tests were weakened or altered. These checks establish implementation
behavior, not semantic success.

Native parsing used one local CPU process with two threads: 23.24 seconds of
inference and peak RSS 5,250,828 KiB (about 5.01 GiB). No download, paid compute,
GPU or frontier generation was used. The frozen masks, vectors and browser were
not changed. The unrelated pending HiT files were not touched.

From the repository root, reproduce construction into a fresh directory:

```sh
python3 sse_multivector/source_phrase_construction.py \
  --input sse_multivector/navigation-research-v1/CAP04/result.json \
  --parses sse_multivector/navigation-research-v1/SPC01/native/parses.json \
  --output /tmp/spc01-replay
```

The existing output directory is intentionally never overwritten.

## Sources

[^1]: Woods (2000), [Conceptual Indexing: Practical Large-Scale AI for Efficient Information Access](https://cdn.aaai.org/AAAI/2000/AAAI00-215.pdf), conceptual indexing, subsumption and retrieval sections. Used as a complete-method precedent, not a claim that this experiment reproduces it.
[^2]: Stoica, Hearst and Richardson (2007), [Automating Creation of Hierarchical Faceted Metadata Structures](https://aclanthology.org/N07-1031.pdf), method and evaluation; Hearst and Stoica (2009), [NLP Support for Faceted Navigation in Scholarly Collections](https://aclanthology.org/W09-3608.pdf), open problems concerning senses, compounds and assignments.
