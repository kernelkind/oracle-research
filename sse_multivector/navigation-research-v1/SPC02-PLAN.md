# SPC02: structure-preserving lexical generalization

## Question and role in construction

SPC01 constructs source expressions and observed grammatical refinements, but
Food preparation omits bread and steak preparation. Food preservation omits
beet freezing. The missing capability is broader phrase meaning with justified
source support, not another word lookup or a smaller menu.

Test whether lexical generalization that preserves the grammatical arrangement
of a phrase supplies useful additional paths and memberships. The complete
SPC01 inventory, all 945 descriptions and their original masks remain fixed.
No descriptions, senses, phrases, thresholds or source memberships are repaired
by hand. No browser or baseline is replaced.

## Mechanism and literature fit

Woods (1997), sections 3.2.1–3.2.2, describes structural subsumption: each
broader relation/value restriction must match an at-least-as-specific narrower
restriction. It explicitly leaves the syntax-to-concept mapping unspecified.
Its conceptual relations are not equivalent to Universal Dependencies labels.
Matching our saved grammatical heads and dependencies is therefore a new
approximation, not a reproduction of Woods.

Luu, Kim and Ng (2014), section 2.2.1, supplies the contrasting SIWN idea:
every general-term word matches some synonymous or more-specific word in the
specific term. It does not preserve heads or corresponding roles. Section 3.1
reports expert judgments of sampled term relations, not propagated source-note
memberships. The control below is inspired by this idea, not its complete system.

These mechanisms are worth testing because the actual missing food-preparation
expressions share a head and modifier arrangement. No claim is made that the
same rule supplies every useful topical relation or resolves different syntax.
Woods et al. (2000) also found that the benefit of lexical knowledge depended
on its integration into retrieval; adding facts alone was not sufficient.

## Frozen comparison

Use all 2,129 SPC01 phrases as candidate parents and children. Use the same
cached WordNet 3.0 and saved parses in every condition. Run four combinations:

- Word matching, literal lemmas only.
- Structure matching, literal lemmas only.
- Word matching, literal lemmas plus WordNet noun synonym/hypernym relations.
- Structure matching, the identical lexical relation table.

Both matchers require distinct corresponding words, preserve part of speech,
and cover every parent word; a child may contain additional words. Word
matching ignores order and dependencies. Structure matching additionally
requires head-to-head correspondence and matching dependency connections.
Other parts of speech match literally. This isolates structural matching from
adding dictionary relationships. It is not a test of contextual disambiguation.

Retain all compatible dictionary-sense witnesses rather than selecting the
sense that makes a desired example pass. These are ambiguous proposals, not
approved semantic edges. Equal phrases are not self-edges. Record reciprocal
relations, graph reachability and transitive memberships without silently
cutting cycles or interpreting them as valid equivalence.

For every direct proposal, preserve the word mapping and dictionary paths.
For inherited notes, preserve the actual source phrase/row and distinguish
direct support from graph-only reachability. A final note can be relevant while
the particular mask used to place it is wrong; audit both.

## Hypothesis, competing explanations and controls

Hypothesis: retaining heads and connections removes source-invalid phrase
relations admitted by the same lexical evidence without structure, while
adding some justified multiword paths and recovering their missing notes
relative to SPC01. Neither fewer edges nor Bread-to-Food alone demonstrates it.

Competing explanations include wrong dictionary senses, malformed source
descriptions, grammatical parsing errors, invalid generalization of a compound
position, and valid meanings expressed through different grammatical forms.
Literal-only controls separate lexical changes from matching structure across
different source occurrences. Exact word mappings, native trees, dictionary
paths, masks and full originals separate these explanations where possible.

Audit the complete changed relation/occurrence surface for all 30 multiword
SPC01 destinations already supported by at least two distinct notes. Include
one-word parents when inspecting their complete new paths; do not evaluate
only note additions or only familiar successful examples. Keep unresolved
semantic scopes distinct from invalid relations. If the surface is too large
for a complete audit in one turn, preserve it and continue; do not replace it
with a hand-picked success sample or claim global accuracy.

Specific controls are Food preparation with N089/N100, Food preservation with
N022, Sea salt with N046, and food/live-bird Chicken evidence including N092.
The last control can expose a wrong source witness even when another mask from
that note genuinely belongs to Food. Coffee shops need not be a kind of coffee;
lacking that lexical link is not automatically a failure of this component.

Would either outcome change the next decision? Useful source-backed paths
across the full inspected surface justify retaining this bounded component and
investigating its demonstrated unresolved dependency. If wrong senses or
compound meanings dominate, reject automatic propagation from this rule;
do not hide errors through a support cutoff. If lexical generalization supplies
little beyond known word links, do not keep expanding this grammar solely
because it is inexpensive. Reassess the construction method instead.

## Execution and verification

Use test-first local code and the cached lexicon; no frontier generation, model
download, GPU or paid compute. Preserve source artifacts, output configurations,
code/input hashes and reproducible output. Compare all conditions mechanically
before semantic interpretation. Implementation tests establish behavior, not
semantic validity. Evaluate complete affected paths and new/unchanged note
memberships separately. Report source-valid, source-invalid and unresolved
results without claiming one uniquely correct hierarchy.

## Sources

1. Woods (1997), [Conceptual Indexing: A Better Way to Organize Knowledge](https://citeseerx.ist.psu.edu/document?doi=8bf7117e692d42c389f6fd293addf270c4690788&repid=rep1&type=pdf), sections 3.2.1–3.2.2, pp. 28–30. Relevant primary text inspected through indexed excerpts; direct PDF retrieval failed. No claim of inspecting the whole report.
2. Luu, Kim and Ng (2014), [Taxonomy Construction Using Syntactic Contextual Evidence](https://aclanthology.org/D14-1088.pdf), sections 2.2.1–2.3 and 3.1–3.2. SIWN's sampled relation precision does not establish phrase-occurrence correctness in this corpus.
3. Woods et al. (2000), [Linguistic Knowledge can Improve Information Retrieval](https://aclanthology.org/A00-1036.pdf), sections 2–5. Retrieval performance evaluates the combined system, not every category member or parent relation.
