# Candidate coverage

CAP01 identifies a restrictive candidate rule in MDH02. It does not identify a
failure of SSE, explain the relation classifiers' errors, or improve GDC09 yet.
The subsequent [CAP02 test](./SHARED-CANDIDATE-CONSTRUCTION.md) examines
shared-feature proposals before classifying the same restricted list again.

## The restriction

`descriptions_from_masks` in `mask_description_hierarchy.py` uses each complete
mask's word-and-symbol set as a candidate seed. It keeps that candidate only
when matching masks occur in at least two different notes. A shared subset is
not considered unless another complete mask already supplies that subset.

Consequently, better relation scores cannot place an absent candidate. This is
a limitation of the MDH02 branch of the research, not of GDC09's diffusion tree.

## Evidence

The audit recomputed all 22 saved MDH02 candidates exactly, then inventoried
every individual feature appearing in masks from at least two notes. There are
333 such features; 18 are existing one-feature candidates and 315 are absent.
MDH02's four other candidates have multiple features. These are lexical counts,
not a count of valid or missing categories.

| Shared feature | Canonical masks | Different notes | Complete masks containing only this feature | MDH02 candidate |
| --- | ---: | ---: | ---: | --- |
| food | 45 | 15 | 0 | Absent |
| meat | 26 | 6 | 0 | Absent |
| chicken | 24 | 5 | 0 | Absent |
| recipe | 14 | 4 | 0 | Absent |
| processed | 5 | 2 | 0 | Absent |
| stock | 14 | 2 | 0 | Absent |

These examples were interpreted after inspecting every matching mask and full
original across their 27 source notes. They are an explanatory subset of the
inventory, not an exhaustive semantic evaluation of its 315 excluded features.
`food` was noticed before the audit; this is not a blind holdout.

Complete inventory and input/source hashes: [CAP01-inventory.json](./CAP01-inventory.json).
All masks and originals for the six rows above: [CAP01-sources.json](./CAP01-sources.json).
Question and competing explanations recorded before running: [CAP01-PLAN.md](./CAP01-PLAN.md).

## What the original notes establish

N032 explicitly says processed food is bad for the author. Its masks include
`processed food` and `bad for me`. N069 explicitly advises not eating processed
food; its masks include `Do not eat processed food` and a longer dietary passage.
The words shared by all five relevant masks are exactly `processed` and `food`.
The complete-mask rule proposes neither that shared phrase nor `food` itself.
Both notes have a recognizable processed-food subject, regardless of whether
their dietary claims are true. No agreement with those claims is required.

N013 describes making chicken stock, pressure-canning it, and storing it. N026
also describes making chicken stock from bones among several food-preparation
activities. All fourteen masks containing `stock` also contain `chicken`; their
common word set is exactly those two words. The other `chicken` masks concern
takeout chicken, chicken pizza, and preserved chicken eggs. This supplies
evidence for investigating a broader chicken-related destination and a narrower
chicken-stock destination, not a requirement that these be the final categories.

The four `recipe` notes concern finding a mochi-bread recipe, posting a pancake
recipe, adapting soda bread to high altitude, and a spaghetti recipe. The six
`meat` notes cover preparation, flavor, dietary arguments, dumplings, and meat
for dogs. These uses provide concrete subject evidence beyond shared spelling.

`food` covers cooking, lunch packing, diet, infant feeding, restaurants, animal
food, and food-preservation equipment. It supports a broad food-related topic,
not the assertion that every mentioned entity is itself a food. In particular,
N100's `food savers` masks concern equipment, while its `dogs food` mask concerns
animal feeding. A class-membership test and a topical browsing test must not
silently exchange these meanings.

## What this does not establish

Many excluded features are grammatical words: `of`, `to`, `a`, `the`, and `i`
are the five with greatest distinct-note support. More candidates alone are not
progress toward meaningful navigation. Literal features still mix word senses,
ignore relationships and miss paraphrases. Keeping symbols avoids the earlier
specific emoji-erasure bug; it does not validate arbitrary partial-mask meaning.

Literal `food` misses bread and recipe masks that never say `food`. It therefore
cannot yet recover all notes appropriate to a food destination or automatically
place Bread beneath it. Conversely, the recipe matches are an aspect of food,
not recipes as edible objects. This audit does not settle those relations.

The useful result is narrower: recurring source-supported abstractions were
excluded by candidate generation before any semantic relation mechanism ran.
The presence of grammatical and ambiguous features is real competing evidence
against adopting unrestricted lexical enumeration as the solution.

## Literature and the decision tested by CAP02

Formal Concept Analysis constructs abstractions from shared attributes without
requiring their description to equal any single input object's description.
Cimiano et al. use parsed term-dependency attributes, not mask tokens; their
paper also warns that accidental corpus similarities need not be semantic
relations. It supports investigating the restriction, not certifying our
representation.[^1] Full lattices can grow exponentially, so enumerating every
possible concept is not the proposed product design.[^2]

The next controlled construction test should keep source masks, feature
extraction, note support, and the descriptor-extension relation fixed while
changing candidate discovery. Use a bounded pool of recurring shared features
and combinations, preserving every candidate and semantic objection. Test
whether it supplies useful previously absent destinations and narrower
children, not merely whether the candidate count increases. Category quality,
membership omissions, and navigation selection remain separately unresolved.

HiT remains a plausible alternative for recognizing named taxonomic relations.
It does not itself propose missing names, and its supplied-name ontology task
does not establish topical membership for our masks. The earlier HIT01 plan is
not executed merely because models and tests were prepared.[^3]

## Reproduction

Run from the repository root; the command prints the saved inventory to stdout:

```sh
python3 sse_multivector/mask_candidate_coverage.py \
  --evidence sse_multivector/geometric-hierarchy-v1/GDC09/evidence.json \
  --baseline sse_multivector/navigation-research-v1/MDH02/descriptions.json
```

No baseline, mask, subject, embedding, label, or browser changed. No model
inference, model download, or paid compute was used. The new tests initially
failed because the audit module did not exist; all 22 relevant tests now pass.
Implementation checks support these counts, not the semantic interpretation.

## Sources

[^1]: Cimiano, Hotho and Staab (2005), [Formal Concept Analysis](https://www.cs.cmu.edu/afs/cs/project/jair/pub/volume24/cimiano05a-html/node3.html) and [Overall Process](https://www.cs.cmu.edu/afs/cs/project/jair/pub/volume24/cimiano05a-html/node2.html).
[^2]: Cimiano, Hotho and Staab (2005), [Discussion](https://www.cs.cmu.edu/afs/cs/project/jair/pub/volume24/cimiano05a-html/node10.html).
[^3]: He et al. (2024), [Language Models as Hierarchy Encoders](https://arxiv.org/html/2401.11374v3), sections 3–4 and appendix A.
