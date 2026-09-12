# Shared-feature candidate construction

## Question

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

## Construction

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

## Hypothesis and competing explanations

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

## Fit and limits of the literature

Cimiano, Hotho and Staab derive formal concepts from shared attributes and order
them by inclusion. They use parsed, lemmatized dependency features over terms;
our objects are masked meanings and our attributes are literal words/symbols.
Only the algebra transfers directly. Semantic fidelity of these attributes is
the experiment, not a result borrowed from their evaluation.[^1]

Their full lattice has exponential worst-case size. Restricting seeds bounds
this candidate family but is incomplete; it does not reproduce the published
full hierarchy method or prove scalability of all later steps.[^2]

## Preservation

Save proposals, relations, source IDs, original evidence, code hashes and the
semantic findings under CAP02. Do not change GDC09, any prompt, any SSE vector,
or the browser. Do not package a TUI before the goal's wrap-up signal.

## Sources

[^1]: Cimiano, Hotho and Staab (2005), [Formal Concept Analysis](https://www.cs.cmu.edu/afs/cs/project/jair/pub/volume24/cimiano05a-html/node3.html) and [Overall Process](https://www.cs.cmu.edu/afs/cs/project/jair/pub/volume24/cimiano05a-html/node2.html).
[^2]: Cimiano, Hotho and Staab (2005), [Discussion](https://www.cs.cmu.edu/afs/cs/project/jair/pub/volume24/cimiano05a-html/node10.html).
