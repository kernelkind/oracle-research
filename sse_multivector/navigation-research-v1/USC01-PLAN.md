# USC01: source meanings and same-description refinements

## Missing capability

USM02 recovers some useful material and operation meanings, with errors retained.
It does not show whether adding a second meaning creates useful narrower note
destinations. SGC's source-edge requirement has not demonstrated enough value to
require a new DRS parser. Test the simpler alternative on the complete automatic
output, not on hand-approved senses.

## Hypothesis and competing explanations

With source assignments and lexical generalization fixed, requiring two distinct
source concepts from the same description will produce some coherent, genuinely
narrower destinations that the singleton construction cannot offer. Alternatives:
the pairs mostly restate existing singleton destinations, join unrelated details,
or propagate source/lexical errors. More patterns and set containment alone cannot
distinguish these outcomes.

The input is every nonempty highest match from USM02: fifteen frozen descriptions
from thirteen notes. Empty words remain absent; their descriptions are retained.
Do not revise masks, descriptions, senses, POS, or select a condition per example.
Use the same WordNet 3.0 hypernym and instance-hypernym rules for every assigned
sense, generating the complete needed lexicon rather than reusing an incomplete
cache. No SUMO mappings or additional learned model in this comparison.

Baseline: construct all observed single concepts and their lexical ancestors.
Intervention: additionally construct unordered pairs witnessed by two different
word occurrences with different assigned senses in one description. Generalize
either endpoint with the same lexical order. A pair means both concepts occur
in that description; it does not assert an action-object or causal relationship.
Do not join words from separate descriptions, even if they share a note.

The constructor's broader-to-narrower operations drop an endpoint or replace an
endpoint with an ancestor. Preserve every original witness, all patterns and
links. Project source rows to distinct notes afterward. Equal note sets are not
evidence of synonymous meanings. This is candidate construction, not menu
selection or browser adoption.

## Evidence and decisions

Verify that every baseline singleton and its witnesses remain identical.
Inspect all new recurring most-specific pairs against the original masks/notes,
not only the appealing examples. Record their complete note membership and
source witnesses, including false admissions and losses relative to older
constructions. Inspect complete paths involving the observed cooking/material,
tomato/vegetable and preservation/preparation areas; these are diagnostic areas,
not a prescribed correct hierarchy. Unexpected coherent refinements count.

Would either outcome change the next decision? Useful distinct refinements
justify keeping pair construction for a broader construction/selection test.
If pairs add only duplicates or unsupported intersections, remove that component
and investigate the remaining source/generalization or selection limitation.
Do not compensate with hand-picked labels, corrected senses or a parameter sweep.
Existing wrong senses, the noun/verb ancestry gap, and the targeted small sample
limit conclusions about complete navigation and the remaining corpus.

## Method fit

Castanet constructs collection-specific lexical hierarchies and explicitly
distinguishes faceted co-presence from event-role interpretation.[^1] Woods uses
structured source expressions and lexical subsumption to build an index, but
its phrase alignment is stronger than the unordered pairs tested here.[^2]
RHOG supplies formal refinement operators given labels and an order; its formal
properties do not validate our source concepts or browsing choices.[^3] This
comparison is a bounded simplification informed by these methods, not a claimed
replication or a new guarantee of semantic validity.

## Execution

Reuse the existing constructor and WordNet normalization path. Add only the
source-occurrence adapter, with failing tests before implementation. One local
CPU process, no encoding or paid resource. Preserve USM01–02, SGC01–03 and GDC09.
No review-tool packaging before the goal's wrap-up condition.

[^1]: Stoica, Hearst and Richardson (2007), [Automating Creation of Hierarchical Faceted Metadata Structures](https://aclanthology.org/N07-1031.pdf), sections 2 and 4. Its evaluation does not certify all item assignments.
[^2]: Woods (2000), [Conceptual Indexing](https://cdn.aaai.org/AAAI/2000/AAAI00-215.pdf), conceptual indexing and subsumption sections.
[^3]: Ontañón (2016), [RHOG](https://arxiv.org/pdf/1604.06954), sections 1.3 and 2. Lexical-label specialization and graph operations assume a supplied order.
