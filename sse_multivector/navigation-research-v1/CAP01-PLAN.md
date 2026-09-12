# Candidate coverage before relation prediction

## Question

Does MDH02's requirement that every candidate equal a complete source mask
exclude recurring subject evidence already available inside longer masks?

This is a source-code and data audit, not a replacement hierarchy or a test of
SSE. The frozen GDC09 evidence, MDH02 feature extraction, two-distinct-note
support requirement, and saved MDH02 candidates remain unchanged. No new
subjects, masks, labels, embeddings, model scores, or navigation are generated.

## Hypothesis and competing explanations

The whole-mask seed rule prevents some recurring source-supported meanings from
ever reaching later relation tests. Alternatives are that missing candidates
lack recurring lexical evidence, or that their absence appropriately excludes
ambiguous words and incomplete meanings. These explanations can coexist.

Inventory every individual word or symbol shared by at least two source notes,
not just a hand-selected subject. For each, retain all canonical mask rows,
source note IDs, whether a complete mask supplies that feature alone, and whether
the feature is already a candidate in saved MDH02. Recompute MDH02 with the
unchanged production function and require exact agreement with the saved list.
Record input and source hashes. Inspect full source masks and notes for semantic
interpretation; word counts alone cannot certify subjects.

The already noticed occurrence of `food` inside several longer masks motivates
the audit; it is not a blind discovery or a prespecified correct taxonomy. No
particular parent-child relation is prescribed.

## What the outcomes would change

If useful recurring evidence is excluded solely for lacking a standalone mask,
test a bounded shared-feature candidate generator before spending more on
classifying the same fixed candidates. If excluded features mostly join unrelated
uses, the next question is representation or sense discrimination, not merely
more candidate enumeration. Either result leaves unstated broader concepts,
paraphrases, and semantic parent-child validity unresolved.

Passing this audit would not show that frequent words are correct categories.
It would isolate a candidate-availability limitation of MDH02. The original
geometry-based GDC09 hierarchy did not use this seed rule and cannot be blamed
for it. A capability-only result need not identify the causes of SRR failures.

## Literature fit

Cimiano, Hotho and Staab's FCA construction derives abstract concepts from shared
attributes; a concept need not reproduce any single object's full description.
Their inputs are parsed term-dependency attributes, not our mask word sets.
Thus the paper motivates checking the complete-mask restriction, not treating
our lexical features as validated semantic attributes.[^1]

Full concept lattices can grow exponentially. This audit does not propose
enumerating one in a product. Any subsequent construction experiment must bound
candidate discovery and still establish useful semantic meaning.[^2]

HiT scores supplied entity names. Its WordNet and ontology transfer evidence does
not supply absent category candidates or establish how our full masks map to
them. HIT01 remains an unrun alternative, not a rejected model or the automatic
next step.[^3]

## Sources

[^1]: Cimiano, Hotho and Staab (2005), [Formal Concept Analysis](https://www.cs.cmu.edu/afs/cs/project/jair/pub/volume24/cimiano05a-html/node3.html) and [Overall Process](https://www.cs.cmu.edu/afs/cs/project/jair/pub/volume24/cimiano05a-html/node2.html).
[^2]: Cimiano, Hotho and Staab (2005), [Discussion](https://www.cs.cmu.edu/afs/cs/project/jair/pub/volume24/cimiano05a-html/node10.html).
[^3]: He et al. (2024), [Language Models as Hierarchy Encoders](https://arxiv.org/html/2401.11374v3), sections 3–4 and appendix A.
