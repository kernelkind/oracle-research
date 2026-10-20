# Phrase structure and broader meanings

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

SPC02 recovers three justified Food preparation memberships, but does not
establish a usable hierarchy. Preserving grammatical structure rejects some
wrong connections and also misses legitimate cooking and preservation topics.
It does not resolve word meaning: dishes being washed still become food.
Combining ambiguous dictionary links produces cycles containing 271 expressions.

The useful result is specific: broader phrase construction can work for some
actual sources without a separate note classifier. The negative result is also
specific: grammatical correspondence plus any compatible dictionary sense is
not enough to justify source memberships or longer paths. Neither condition is
adopted, and the GDC09 browser is unchanged.

## What was held fixed

All 945 saved descriptions, their masks and originals, and all 2,129 SPC01
expressions were reused unchanged. The cached WordNet 3.0 provides possible
noun synonyms and hypernyms; no contextual sense selector was run. Other
parts of speech match only their existing lemmas. Both matchers require a
distinct corresponding child word for every parent word.

The four conditions vary two things independently: whether dictionary
relations are available, and whether matching must preserve the grammatical
head and dependency connections. Extra child words are allowed. Word matching
ignores order and dependencies; structure matching preserves connections,
not necessarily surface word order. All compatible senses for a selected
word correspondence are recorded; the implementation does not choose a
contextually correct sense.

The [pre-run plan](./SPC02-PLAN.md) records the literature fit, hypothesis,
competing explanations and decision consequences. This is an approximation
inspired by structured subsumption, not a reproduction of Woods's conceptual
representations or Luu et al.'s complete taxonomy-construction system.

## Complete mechanical comparison

| Matching rule | All proposed links | Additional direct links into the 30 established multiword destinations | Groups of mutually reachable expressions |
|---|---:|---:|---:|
| Words, literal lemmas | 4,254 | 74 | 16 |
| Structure, literal lemmas | 1,725 | 13 | 1 |
| Words, with dictionary relations | 24,872 | 97 | 42 |
| Structure, with dictionary relations | 16,063 | 18 | 26 |

Additional links are counted against SPC01's 1,268 observed direct links.
They are not automatically new destinations, useful distinctions or new notes.
Both structure conditions are exact subsets of their corresponding word
conditions. All original SPC01 links remain in the structural literal result.

Cycles are retained as evidence, not cut into an apparently valid tree. Some
small cycles reflect equivalent expressions; the largest dictionary-induced
cycle mixes 271 expressions and is not legitimate semantic equivalence.

The semantic audit covers all 18 new structural links into the 30 destinations
and all 79 further word-only links there. It does not claim semantic precision
over every one of the 24,872 proposed links. Whole-graph reachability and
source-specific counterexamples expose additional construction problems.

## Food preparation: a real recovery

P1259 Food preparation originally contained only N026 and N076. The structural
dictionary rule adds N089, N100 and N039 through these complete expressions:

| Source expression | Broader expression | Original evidence |
|---|---|---|
| P1120 Bread preparation | P1259 Food preparation | N089 / row 866: `Bread`, `salt`, `yeast`, `mixing` |
| P1974 Beef and steak preparation | P1259 Food preparation | N100 / row 350: `sirloin`, `cut`, `steaks` |
| P1852 Outdoor dinner grilling | P1259 Food preparation | N039 / row 91 includes `will hit just in time for grilling out dinner` |

The first two preserve preparation while generalizing the material. The third
generalizes both dinner to food and grilling to preparation. Its original post
discusses storms threatening dinner grilling; it need not provide cooking
instructions to concern that topic. This is an additional source-grounded
path, not just reproduction of the already-known Bread-to-Food word relation.

The full originals and original inline masks are available at
[row 866](./SPC01/SOURCE-EVIDENCE.md#row-866--n089),
[row 350](./SPC01/SOURCE-EVIDENCE.md#row-350--n100), and
[row 91](./SPC01/SOURCE-EVIDENCE.md#row-91--n039).
Food preparation now has five notes through direct matching, and following
its proposed descendants adds no further notes.

This does not validate every higher ancestor of Food preparation. A useful
local construction and an invalid larger hierarchy can coexist.

## A correct destination can hide a wrong source interpretation

P1395 Many dishes comes from N026 / row 187:

> The author washed many dishes used while preparing tomatoes for salsa, making yogurt, bagging chicken meat, and making chicken stock.

P1396 Many foods is admitted as its parent using the dictionary's prepared-food
sense of dish. But the original says the dishes were **used and cleaned**:

> —cleaned so many dishes from all the dishes i used doing all the above.

The complete note also lists several foods. Thus N026 can genuinely belong in
a food-variety destination while the proposed dish-to-food derivation is wrong.
The full note and mask are preserved at
[row 187](./SPC01/SOURCE-EVIDENCE.md#row-187--n026).

Head and modifier correspondence cannot settle this: both expressions have
the same structure. The failure is selecting the wrong contextual meaning,
not a reversed dependency or missing dictionary fact. The original description
already supplies the washing context; the phrase-level representation does
not use it to select the dish sense.

Across the five lexical additions to these recurring multiword destinations,
three are the justified food-preparation links, one is this wrong dish
interpretation, and one—Good coffee under the existing Good/better food
category—remains scope-sensitive. The thirteen literal structural additions
mostly reuse existing notes or source distinctions. The
[complete structural audit](./SPC02/STRUCTURE-MATCH-AUDIT.md) qualifies all 18.

## Structure also rejects valid topical paths

The word matcher admits Cooking brisket, Baking bread and Frying beef under
Food preparation. The structure matcher rejects them because their saved
parses make the food noun the head and the activity a nominal modifier.
The original notes plainly discuss preparing food. This is not evidence that
the broader topic is wrong; it shows that grammatical shape is an incomplete
proxy for the relationship we need.

N022's beet-preservation note remains absent from Food preservation in the
structural condition. Its expression is beet-headed, with preservation linked
through “for.” The word condition recovers the topical relationship. That
does not turn the beet-headed expression into the same conceptual structure as
Food preservation; the semantic relation is expressed differently.

Sea salt likewise remains incomplete under structural matching. The N046
bagel parse has sea and salt attached separately to flakes or toppings.
The needed semantic subexpression is not supplied by the existing tree.

Conversely, structure blocks genuine problems in the word condition. The
[complete 79-edge contrast](./SPC02/WORD-MATCH-AUDIT.md) distinguishes valid
topical losses, invalid placements, invalid selected lexical explanations and
unresolved scopes. A bad selected explanation is not proof that no valid
correspondence or topical relationship exists.

## Longer paths switch word meanings

The structural dictionary graph contains this actual path:

`Food → Sake → Interest → Things → Content → Greeting`

The first edge uses sake as a drink. The second uses sake as a purpose or
interest. Those are different meanings of the same spelling, not a valid
intermediate category connecting food and interest. Further links switch
meanings again. The saved word correspondences and dictionary paths make
the failure inspectable; it is not inferred merely from an unattractive label.

The bare Sake candidate is P0796; its only source is N069 / row 405. Its entire mask is:

> ⟦Be good, not for others sake, but for your own peace⟧

Its supplied description concerns being good for one's peace rather than
other people's sake. There is no rice-wine meaning in this occurrence. N069
also contains independent diet advice, so again the final note can belong to
Food for a different reason. The complete original remains in
the unchanged input records (`./SPC01/construction/inputs.json`), row 405.

All 271 expressions in the largest cycle can reach each other. Food directly
matches sources from 91 notes under some available dictionary meanings;
following graph paths reaches all 100. Direct matching is therefore not a
complete repair, even if transitive sense switching were prohibited. One must
also establish which interpretation fits each source occurrence.

Reaching all 100 notes is not by itself evidence that those notes are unrelated
to Food. The demonstrated defect is the incompatible sense path and its wrong
source witnesses, even where another part of a returned note genuinely concerns food.

These are separate requirements: retaining a compatible meaning along a path
and grounding that meaning in its source. This experiment does not demonstrate
a method satisfying either automatically. It also does not invalidate every
dictionary relation: the bread, steak and grilling examples use fitting senses.

## Decision and next question

Do not adopt either graph or propagate memberships through its ambiguous
nodes. Do not repair the result by cutting cycles, raising support thresholds,
or preferring the visibly attractive examples. Those actions would conceal
unresolved semantic evidence.

Retain structural correspondence as possible evidence, not an acceptance gate
for every topical relation. Some rejected relationships are valid precisely
because their meaning is expressed with a different structure. Retain the
three food-preparation recoveries as component evidence, not a complete-method
success or an estimate of broad-corpus reliability.

The consequential research target identified here was **source-context interpretation in
the representation being composed**. A candidate approach needs evidence for
distinguishing meanings such as washed dishes versus prepared dishes and
purpose-sake versus drink-sake, while also handling the activity/material
relationship across different phrasing. These are observed failure mechanisms,
not a requirement for perfect classification or one dictionary sense per category.
Selecting a model merely because it recognizes dictionary word relations
would repeat LGR01/SRR01's mistake. Its actual inputs and training must match
contextual interpretation, and its output must plausibly participate in
construction. A further word-matching or parser tweak alone is not justified.

That is a missing capability and method-selection requirement, not a decision
to download a particular model or adopt a word-sense-only taxonomy. The
construction still needs to support legitimate topical relationships beyond
strict object-type subsumption.

[SGC01](./SEMANTIC-GRAPH-CONSTRUCTION.md) now tests a contextual semantic-graph
representation with a bounded generic constructor. It preserves some useful
local food-preparation and meat-cut paths, but also predicts wrong senses and
bindings and emits malformed outputs. The useful paths are not rejected solely
for unrelated logical errors; they also do not establish an improved complete
hierarchy. A subsequent static check separates parser-recoverable paths from
relations absent in the fixed dictionary and exact-role scheme. This supersedes
the pending method-selection step, not SPC02's observations or frozen records.

## Reproduction and verification

- [Frozen plan and primary-source qualifications](./SPC02-PLAN.md).
- All final relations, word mappings, source occurrences and memberships (`./SPC02/final/result.json`).
- Exact dictionary definitions and paths (`./SPC02/final/lexicon.json`).
- Verification record (`./SPC02/verification.json`).
- [Complete structural audit](./SPC02/STRUCTURE-MATCH-AUDIT.md) and [word-only contrast](./SPC02/WORD-MATCH-AUDIT.md).

Seventy-two production-path tests pass, including eighteen new tests. The
new module was tested before implementation. Two further regressions exposed
a witness tie-order problem and hash-dependent serialization of reciprocal
pairs; both were fixed without weakening the tests. Initial runs remain
preserved. Their actual edges, mappings and note memberships are identical
to the final run; only reciprocal-pair serialization order changed.

The final result, lexicon and source-code snapshot replay byte-for-byte with
a different Python hash seed. Configurations match except elapsed time and
the operating-system resource counter. The final construction took 6.24
seconds locally using saved inputs. No new model, frontier generation, GPU
or paid resource was used. The recorded `ru_maxrss` is not an attributable
memory measurement here: a fresh Python process reports about 5 GiB despite
its own `/proc` high-water mark being about 11 MiB. Do not interpret that
inherited counter as this experiment's measured RAM requirement.

All frozen GDC09 files, SPC01 inputs and native parses match the pre-run
commit. No new browser was packaged. The unrelated HiT files remain untouched.

From the repository root, replay into a new directory:

```sh
PYTHONHASHSEED=0 python3 sse_multivector/structural_phrase_generalization.py \
  --input sse_multivector/navigation-research-v1/SPC01/construction/result.json \
  --lexicon sse_multivector/navigation-research-v1/SPC02/final/lexicon.json \
  --output /tmp/spc02-replay-new
```

No model packages are required for replay from the saved lexicon. Existing
output directories are deliberately refused.
