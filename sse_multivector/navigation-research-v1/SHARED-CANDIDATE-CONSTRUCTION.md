# Shared candidate construction

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

CAP02 generates several useful broader/narrower relationships that MDH02 could
not propose. It also generates grammatical structure and joins different word
meanings. The unfiltered result is not a browsable hierarchy and is not adopted.

## What changed

The control, MDH02, permits a candidate only if some complete mask supplies its
entire feature set. CAP02 additionally starts from each recurring feature and
collects the features common to every mask containing it. Identical proposals
are combined. Existing candidates and their memberships remain exact copies.

For example, every mask containing `stock` also contains `chicken`, so the new
proposal is `chicken stock`. Masks containing `chicken` have only `chicken` in
common. The unchanged relation rule links the larger feature set beneath the
smaller one only when its note set is also strictly smaller. This creates an
overlapping candidate structure, not a partition of notes.

The algorithm reads only source-mask features. It does not use the names below,
generated subjects, SSE coordinates, old ancestry, a classifier, or manual
semantic decisions. Names such as “Bread with rosemary” are interpretations for
this analysis, not additional algorithm inputs or generated browser labels.

## Results

| Measure | MDH02 | CAP02 |
| --- | ---: | ---: |
| Candidates | 22 | 336 |
| Immediate parent–child links | 3 | 43 |
| Roots | 20 | 304 |

All 22 old candidates and their memberships are unchanged. There are 314 new
candidates and 40 new links. Every proposed link strictly reduces the note set,
but this mathematical property does not establish meaningful narrowing. All
43 links are immediate: this result contains no multi-link path. It therefore
does not demonstrate a complete broad-to-fine organization.

All 100 notes match something, often a grammatical word. That is not useful
semantic coverage. Most candidates have no parent, and not all root-only
candidates were semantically evaluated.

## Useful new relationships

Each row below was checked against every supporting mask and complete note at
both ends. These are defensible topical arrangements, not a prescribed taxonomy
or claims of exhaustive membership.

| Interpreted path | Parent notes | Child notes | Source evidence |
| --- | ---: | --- | --- |
| Coffee → Coffee shops | 19 | N004, N038, N065 | A rave in a cafe; music playing in a cafe; a cafe's laptop/tablet ban |
| Bread → Bread with rosemary | 8 | N037, N072 | Rosemary in sourdough and in soda bread |
| Food → Processed food | 15 | N032, N069 | Both explicitly discuss processed food |
| Chicken → Chicken stock | 5 | N013, N026 | Both prepare chicken stock |
| Salt → Sea salt | 5 | N046, N063 | Sea salt on bagels and in risotto |

Bread with rosemary was not prescribed in the experiment. It connects different
bread types through an explicit shared ingredient. The existing Bread →
Sourdough bread sibling remains, allowing N037 in both children. Neither sibling
must be disjoint or uniquely correct. This is a useful instance of emergent
narrowing, not merely a count of recurring words.

Coffee shops is topical narrowing, not the assertion that a shop is a type of
beverage. This distinction matters when considering learned taxonomic models.
Likewise, Bread includes preparation equipment and Food includes food-storage
equipment; those objects are not themselves edible. A description of browsing
content is not interchangeable with an object-class label.

## Two concrete problems

**Dinner → “dinner hit.”** The child selects N007 and N039 from seven dinner
notes. Its masks include:

- N007 / V052: ⟦dinner⟧ ⟦Lamb with steamed seasoned broccoli and baby potatoes really hit the spot⟧
- N039 / V304: ⟦Next⟧ ⟦storms look like they will hit⟧ ⟦grilling out dinner⟧

N007 describes enjoying a meal. N039 describes storms disrupting outdoor plans.
The repeated word `hit` does not supply the same narrower dinner meaning. A
smaller note set alone has created a formally valid but unsupported refinement.
These notes remain appropriately related through dinner; that is not the error.

**Coffee → “coffee experience.”** The child selects N065 and N094 from nineteen
coffee notes. Its masks include:

- N065 / V561: ⟦Coffee shop⟧ ⟦Felt like changing their router/ap passwords so they⟧ ⟦experience⟧ ⟦freedom from internet⟧
- N094 / V852: ⟦Decafe coffee drinkers⟧ ⟦for the experience⟧

N094 concerns the experience of drinking coffee. In N065 the contemplated
experience is cafe staff losing internet access. Interpreting this child as
coffee's drinking experience is unsupported. Calling it merely coffee-related
experiences would require a separate demonstration that this is a meaningful
narrowing, rather than nearly every personal coffee post fitting it.

These examples show word-meaning and attachment information missing from the
feature sets. They do not prove that the source masks lack that information,
that SSE failed, or that the two notes could never share another valid category.

## Unresolved judgments and selection

Coffee → “coffee personal” connects N065's ironic personal-growth remark with
N086's personal journey of roasting. Personal development through coffee choices
is conceivable; the current evidence does not establish whether that category
is a useful, predictable distinction. It remains unresolved, not an automatic
failure. Similar qualifications apply to morning greetings under a broad
Mornings topic and pizza-day observance under Pizza.

The complete edge audit records seven supported topical links (five new), two
mixed-word-meaning links, seven scope-unresolved links, and twenty-seven links
without an established descriptive parent. These are transparent working
judgments, not a calibrated success rate. They do not certify all 336 candidates.

Many parents are `a`, `to`, `of`, or an apostrophe suffix. Some children below
them contain useful material: `down slow to` genuinely joins slowing down
after Christmas and advice to slow one's life. The useless parent does not
make that child useless. No stopword filter or hand-selected hierarchy was run.
Removing grammatical parents would still leave the dinner and coffee errors.

## Membership remains separate

`chicken` and `chickens` are separate features. N080's actual mask V733 is
⟦Our chickens⟧ ⟦laying an egg a day⟧. It is outside the singular `chicken`
destination, even though a broader chicken-related destination would plausibly
include it. This is an explicit wording mismatch, not missing model knowledge.

Literal Food still cannot place Bread beneath it when bread masks do not say
`food`. The new four-note Recipe candidate is also a root, not automatically a
child of Food. More shared-feature proposals do not supply unstated abstractions.

N048 contributes a coffee-only hashtag mask, while its complete readable note
quotes Tolstoy on eating animals and has a long tag list. Broad Coffee already
included it in MDH02. This is a source-evidence/content-discovery concern, not a
new CAP02 regression; an explicit masked word need not promise useful reading
content about that word. No source mask was changed in this experiment.

## What the experiment changes next

There is now evidence that source-derived shared features can construct some
useful category relations without old-tree ancestry or a relation classifier.
The missing-candidate restriction was worth removing for this diagnostic.
There is not evidence that unrestricted word sets are an adequate representation
for complete navigation. CAP02 should not be polished or packaged as a browser.

The next missing capability is identifying a shared meaning in context, rather
than only a shared spelling. Investigate source-grounded phrase/relationship
attributes before another relation-model run. A proposed alternative must retain
valid dispersed evidence such as rosemary added to bread, distinguish the two
uses of `hit`, and keep meaning-bearing actions as well as noun phrases. Merely
dropping function words or requiring adjacent words would not answer that
question. No parser, extraction rule, or learned model is selected yet.

Separately, normalization and recovery must address singular/plural and implicit
broader meanings. Do not claim a spelling fix would supply Food → Bread or solve
candidate interpretation. The complete proposed construction still depends on
adequate shared attributes, selective memberships, valid inclusion relations,
and navigation selection; these dependencies are not discharged by five links.

The subsequent [CSA01 audit](./CONTEXTUAL-ATTRIBUTES.md) checks contextual
word senses before a model run. It confirms useful lexical ancestors but also
inventory and composition limits. Word senses are retained as a possible
component, not selected as the sole replacement for source descriptions.
The original CAP02 data and judgments above remain unchanged.

## Literature check

The [CAP02 plan](SHARED-CANDIDATE-CONSTRUCTION.md#cap02-study-design) records the bounded FCA mechanism, its fit,
competing explanations, and decision-changing outcomes. It deliberately does
not borrow semantic correctness from work using parsed dependency attributes.

Sanderson and Croft construct topical menus using term co-occurrence, allowing
both type and aspect relationships. However, they use query-focused retrieved
documents to reduce ambiguity, not a demonstrated general sense resolver. Their
small user study judges term-pair interest and relationship types, not complete
note membership. This is relevant precedent, but neither its frequency-based
relation nor its informal 0.8 threshold answers CAP02's observed ambiguities.
We should not adopt those settings merely because the overall application looks
similar.[^1]

## Evidence and reproduction

- [Plan](SHARED-CANDIDATE-CONSTRUCTION.md#cap02-study-design): recorded before implementation and results.
- Candidates and relations (`./CAP02-result.json`): all proposals, support rows,
  source notes, unchanged baseline IDs, provenance and code hashes.
- Complete edge audit (`./CAP02-edge-audit.json`): every one of the 43 links.
- Source evidence (`./CAP02-sources.json`): all child masks and originals, plus
  complete memberships of fourteen potentially substantive parents; 350
  canonical masks in 79 notes. Other root-only candidates and complete
  grammatical-parent memberships are not certified.

Run from the repository root:

```sh
python3 sse_multivector/shared_mask_descriptions.py \
  --evidence sse_multivector/geometric-hierarchy-v1/GDC09/evidence.json \
  --baseline sse_multivector/navigation-research-v1/MDH02/descriptions.json
```

Two production runs give byte-identical output. Five new tests first failed on
the absent implementation; all 27 relevant tests now pass. Tests check baseline
preservation, exact closure support, deduplication, distinct-note recurrence,
the bounded family's known incompleteness, and the real-corpus CLI. These checks
validate implementation, not the semantic judgments above. All frozen GDC09
files and browser defaults remain unchanged. No model inference or paid compute
was used. Overall hierarchy research remains open.

## Sources

[^1]: Sanderson and Croft (1999), [Deriving concept hierarchies from text](https://ciir.cs.umass.edu/pubfiles/ir-156.pdf), sections 2.1–2.4 and 4.

## CAP02 study design

### Question

Does admitting recurring shared features produce useful broader/narrower
destinations that MDH02 could not propose, with the existing relation rule?
The desired output is a source-grounded candidate structure, not a larger list
of words and not an adopted browser hierarchy.

CAP01 established that whole-mask seeds exclude recognizable shared subjects.
It did not establish that the resulting new destinations form useful paths.
This experiment changes candidate discovery only. Freeze the 916 GDC09 masks,
word-and-symbol extraction, two-distinct-note support, literal membership, and
the strict descriptor-extension plus strict note-subset relation. Preserve the
22 baseline candidates and every original membership exactly.

### Construction

For each feature occurring in at least two notes, collect all masks containing
it. Intersect their feature sets. Propose this shared set as a description of
those masks; retain every feature that led to the proposal as provenance. Merge
identical proposals, then add the unchanged MDH02 candidates. No stopwords,
manual subjects, dictionary expansion, semantic model or score cutoff is added.

This is the attribute-concept closure from Formal Concept Analysis, restricted
to individual-feature seeds, not a full lattice. It adds at most one candidate
per recurrent feature. It can miss a meaningful combination whose individual
features all occur more broadly; that limitation is deliberately explicit.
Candidate discovery uses postings rather than comparing all source-note pairs.
The existing experimental relation implementation remains unchanged and is not
a production scalability benchmark.

### Hypothesis and competing explanations

The added candidates supply recognizable broader meanings and narrower choices
with smaller note sets. Competing explanations: (a) extra text merely adds
grammatical constraints; (b) recurring features merge distinct word senses;
(c) corpus co-occurrence creates a spurious apparent refinement; (d) the bounded
seed family still misses useful combinations; (e) literal matching still omits
relevant notes that use different words. More than one can be true.

Inspect the complete edge inventory, not only the already noticed food examples.
For substantive candidate paths, inspect every supporting mask and original
note, the sibling differences, and what was excluded. Record grammatical and
ambiguous paths rather than filtering them away after seeing results. Any
limited semantic audit must state its coverage; counts never certify the rest.
Use the prior candidate list as the control and verify unchanged memberships.

Could success merely reflect shared spelling? Yes: formal inclusion is
guaranteed by the rule, so it cannot be the semantic result. A meaningful path
needs a recognizable description supported by the masks, a genuinely narrower
child meaning, and an actual smaller set of notes. It need not be the unique
or preferred taxonomy. No result here certifies exhaustive membership.

Would either outcome change the next decision? If useful paths appear alongside
noise, candidate availability is improved but selection/representation becomes
the immediate unresolved dependency. If the output supplies only word overlaps,
do not tune cutoffs: reconsider the attributes or candidate family. If useful
destinations omit differently worded notes, quantify that separate recovery gap
before adding more nodes or testing category-relation classifiers.

### Fit and limits of the literature

Cimiano, Hotho and Staab derive formal concepts from shared attributes and order
them by inclusion. They use parsed, lemmatized dependency features over terms;
our objects are masked meanings and our attributes are literal words/symbols.
Only the algebra transfers directly. Semantic fidelity of these attributes is
the experiment, not a result borrowed from their evaluation.[^cap02-study-design-1]

Their full lattice has exponential worst-case size. Restricting seeds bounds
this candidate family but is incomplete; it does not reproduce the published
full hierarchy method or prove scalability of all later steps.[^cap02-study-design-2]

### Preservation

Save proposals, relations, source IDs, original evidence, code hashes and the
semantic findings under CAP02. Do not change GDC09, any prompt, any SSE vector,
or the browser. Do not package a TUI before the goal's wrap-up signal.

### Sources

[^cap02-study-design-1]: Cimiano, Hotho and Staab (2005), [Formal Concept Analysis](https://www.cs.cmu.edu/afs/cs/project/jair/pub/volume24/cimiano05a-html/node3.html) and [Overall Process](https://www.cs.cmu.edu/afs/cs/project/jair/pub/volume24/cimiano05a-html/node2.html).
[^cap02-study-design-2]: Cimiano, Hotho and Staab (2005), [Discussion](https://www.cs.cmu.edu/afs/cs/project/jair/pub/volume24/cimiano05a-html/node10.html).
