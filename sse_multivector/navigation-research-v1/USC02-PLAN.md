# USC02: meaning presence without a second-word requirement

## Question and fixed inputs

USC01 found useful Cooking/Meat and Change/Flavoring refinements, but requiring
different word occurrences also excluded notes from Cooking/Act, even though
every cooking occurrence already supplies Act. A semantic conjunction should
ask whether both meanings are supported, not whether two different words exist.

Hold fixed all fifteen descriptions, original masks, 128 nonempty assignments,
WordNet order, and USC01's complete candidate keys separately for each lexical
condition. No new descriptions, senses, source edges, category names or learned
models. Literal and generalized inventories remain distinct. The source is
`USC01/construction`, committed in `54e42630287b4d71f4003021370adaf6812266e4`.

For every existing pair A/B, recompute its source rows as the intersection of
the two existing singleton row sets. Only then project rows to notes. A single
occurrence may supply both meanings. Never intersect note sets across separate
descriptions. Preserve original witnesses verbatim and record new assignments
from each endpoint to its supporting occurrence; do not invent reflexive edges.

Keep this fixed-key inventory separately from a generalized-only derived graph
that identifies pairs with a redundant ancestor/identical endpoint with their
narrower singleton. Redirect links, remove self-links, and deduplicate links.
Do not equate incomparable meanings merely because their current notes match.
Literal support is exact assigned-sense support, so lexical-ancestor quotienting
must not silently change that control. Recompute recurring/most-specific reports.

## Hypothesis, alternatives and distinguishing evidence

The informative hypothesis is that newly admitted source rows preserve coherent
nonredundant refinements rather than adding unsupported meanings or erasing the
useful distinctions observed in USC01. Competing explanations are that prior
word-count restrictions accidentally hid source/ancestry errors, or that some
combinations add no useful semantic restriction even without those errors.

Several outcomes are guaranteed by the definition and are implementation checks,
not evidence of useful navigation: no old row/note disappears; literal membership
stays fixed; generalized Cooking/Act equals Cooking; existing Cooking/Meat
witnesses survive. Fewer nodes or these checks passing does not establish success.

Audit every changed pair-to-note admission and its new row witnesses, including
patterns that were previously single-note. Distinguish new rows from new notes.
Inspect all newly recurring most-specific nonredundant candidates; the old set
of 202 is not the new audit boundary. Review the complete before/after local
paths through cooking/meat, change/flavoring, food/vegetables/tomatoes and
preservation, including retained source errors and missing memberships. These
are diagnostic areas, not a prescribed correct taxonomy. Broad or unexpected
combinations may be valid; judgments use original masks/notes and exact meanings.

Could this succeed without demonstrating the needed capability? Yes: repairing
only redundant endpoints is algebraic, and accepting two good retained examples
could ignore new bad admissions. The all-change and newly recurring audits are
required to distinguish that outcome. Missing memberships can remain because
of source descriptions or the dictionary, not the conjunction rule. Report those
separately rather than restoring a word-count rule to conceal them.

Would either outcome change the next decision? If nonredundant combinations
retain supported useful narrowing, keep conjunction as the simpler construction
rule and investigate the consequential remaining source/order or category-choice
limitation. If their new admissions undermine the useful distinctions, identify
the responsible source/order or combination semantics before adding complexity;
combinations with no demonstrated value should not displace singleton paths.
This fixed-key test cannot reject conjunctions that USC01 never proposed.

## Method fit and execution

RHOG separates label subsumption from the additional Object Identity constraint,
which prevents two pattern nodes from sharing one source node.[^1] Its formal
results assume the label order and do not validate semantic meanings. This test
does not claim to implement all RHOG operators or learn an ontology. It changes
the occurrence-level meaning of a pair, not the generic graph constructor's
actual-edge contract. No second lexical-generalization engine is needed.

Add small pure support/quotient operations with failing tests first. Run one local
CPU construction and an exact replay. Preserve the raw fixed-key result, separate
quotient, all source evidence and code/configuration hashes. No paid resource,
encoding or source correction. No review-tool packaging before wrap-up.

[^1]: Santiago Ontañón, [RHOG](https://arxiv.org/pdf/1604.06954), arXiv v2, section 1.3.1 and Figure 3. Without Object Identity, different pattern nodes may share a source node; this is a formal mapping distinction, not proof of topical fidelity.
