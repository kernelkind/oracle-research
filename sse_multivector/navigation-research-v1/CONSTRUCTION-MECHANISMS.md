# Constructing categories and their relationships

SPC01 tested construction from complete source phrases rather than another
score cutoff or independent pair classifier. It demonstrated some useful
local paths, but incomplete memberships and missing broader connections remain.
See the [results](./SOURCE-PHRASE-PATHS.md). The review below records why that
experiment was selected; it does not establish grammar as a complete semantic
hierarchy. Its pre-run commitments remain in the [plan](SOURCE-PHRASE-PATHS.md#spc01-study-design).

## What the existing evidence changes

[CPC01–CPC02](./CATEGORY-PATH-COMPATIBILITY.md) separates three problems that a
single hierarchy picture can conceal. Some proposed category descriptions are
incomplete, some note assignments are wrong, and some meaningful parent–child
relationships disappear when ancestry requires exact containment of independently
predicted note sets. Fixing one does not establish the others.

At CPC01's development cutoff, Chicken stock incorrectly admits N029, the
coffee-related “Rogue Batch” post. Because Chicken does not admit N029, the
previous Chicken → Chicken stock path disappears. Admitting N029 to Chicken
would restore consistency while spreading the error. Salt → Sea salt has a
different mechanism: the bagel note has genuine sea-salt evidence, but the
broader Salt score falls below the cutoff. The same missing-edge symptom does
not justify the same repair.

CPC02 recovers the classifier's only two development gains through ordinary
word-form matching, without its incorrect additions. That strengthens the
simple membership reference. It does not finish category construction: the
candidate strings still include “bread in” and “a chicken,” and many broader
meanings remain absent.

[DSP01](./DEPENDENCY-DESCRIPTIONS.md) found useful local structure and genuine
limitations. The rosemary/bread paraphrases have different grammatical paths;
one native attachment is also wrong. It did not construct a candidate inventory,
category paths or a menu. Thus an experiment that merely compares those parses
again would be redundant, but an actual phrase-based construction is untested.

## Relevant construction mechanisms

### Castanet: lexical paths fitted to a collection

Castanet extracts frequent one- and two-word noun phrases and uses WordNet
hypernym paths to construct facet hierarchies. Unambiguous terms establish a
core; ambiguous terms are attached through the path with strongest representation
in that core. Unknown terms are omitted, and one sense is chosen per term for
the entire collection. Compression and removal of high-level nodes produce the
displayed structures.[^1]

Its recipe study involved 34 information architects; 85% expressed willingness
to use the output. However, assignment was literal, participants were not asked
to judge item assignment, and some top-level adjustments were manual. This is
directly relevant construction and usability evidence, not validation of every
root-to-note path.[^1]

The later journal-title study reports 11/15 participants willing to use Castanet.
More importantly for transfer, its open-problems section explicitly identifies
per-occurrence sense disambiguation, unknown compounds, synonyms and multiple
uses of a word as unfinished work.[^2]

**Fit judgment:** lexical ancestors could supply meanings absent from literal
corpus phrases. Native collection-wide sense selection is poorly matched to
mixed notes, where Chicken as food and Chicken as a live animal can both occur.
This does not reject a lexical component. Another Bread → Food lookup would
merely repeat CSA01; a meaningful test must exercise construction and contextual
assignments, not rediscover a known dictionary entry.

### Woods: structured phrases combined with lexical meaning

Conceptual indexing combines morphology, lexical senses and structured phrases.
It places concepts using semantic subsumption rather than document co-occurrence:
the example of car washing beneath automobile cleaning requires both phrase
structure and lexical relationships. Its retrieval process also relaxes phrase
matching when meaning is expressed through different wording or structure.[^3]

**Fit judgment:** this is a plausible complete-method precedent, but not a
released semantic guarantee. Its retrieval evidence does not certify all
category relations. It explains why a grammatical phrase constructor can be a
useful component without requiring every valid witness to share one parse.
Lexical generalization and flexible evidence recovery would still need their
own support. Head preservation alone would put Coffee shops under Shops, not
automatically under Coffee; topical refinement is broader than strict “is-a.”

### SnakeT: shared phrases construct parent folders

SnakeT extracts ordered phrases with gaps from about 200 query-result snippets.
An anchor-text index enriches snippets; a DMOZ-based resource ranks phrases.
Folders share primary labels and secondary phrases found in 80% of their
snippets. Shared folder phrases create parents. The method then prunes nearly
identical child coverage and similar labels, stopping at three levels.[^4]

The 77-query evaluation reports top-level label precision of .91 at three and
.79 at ten. Its relevance judgment can credit an ambiguous parent when most
children are relevant, which is weaker than auditing whether the parent predicts
its notes. DMOZ ranks phrases rather than supplying the folder hierarchy.[^4]

**Fit judgment:** this genuinely constructs descriptions and hierarchy together;
it is not just a labeler for a fixed clustering. But repeating its 80% coverage
rule would not independently establish semantic generality. Its substantial
external resources also contribute to phrase quality. Stripping those away and
reusing CAP04's raw pairs would not be a faithful replication.

### TaxoGen: jointly refine terms, topics and document support

TaxoGen recursively clusters phrase embeddings, identifies terms too general
for the proposed children, and retains those terms at the parent. It estimates
topic-related documents and retrains local SkipGram embeddings before deeper
splits. Parenthood is not inferred solely from containment of independently
classified document sets.[^5]

The experiments use about 1.89 million paper titles and 94,476 abstracts,
with five children per split. Human relation accuracy is .775 and .520,
respectively. Judges see each topic's five representative terms, not all source
documents. The authors themselves identify an overly specific top-level label
and repeated parent/child topics in ablations.[^5]

**Fit judgment:** this is substantive topic-construction evidence, not a solution
to be dismissed because it is imperfect. However, replacing locally trained
term embeddings with our existing sentence vectors would be a new variant.
One hundred notes do not reproduce its training regime. Before that variant,
we can test the still-unmeasured source-phrase construction capability directly.
Do not describe shared statistical support as proof of semantic parenthood.

### Syntactic contextual taxonomy construction

Luu et al. combine noun-phrase extraction, WordNet-assisted string inclusion,
lexico-syntactic web patterns and distributional inclusion of syntactic contexts.
Their method gathers web evidence for candidate relations, then weights and
prunes a taxonomy graph. The grammatical parser is only one component; it does
not itself supply all semantic relations.[^6]

**Fit judgment:** this supports treating grammatical structure as evidence rather
than as an ontology. Copying its string-inclusion step alone would omit the
other evidence channels. Its hypernym objective is also narrower than all
reasonable topical browsing refinements. No experiment here adopts its web
queries, fitted scores, or taxonomy-pruning rules.

## What not to infer from these papers

A graph can have nested sets, a grammar can have nested phrases, and a learned
model can have nested latent topics without establishing the same semantic
claim. Conversely, lack of a universal guarantee does not make an empirical
construction experiment pointless. The relevant question is whether the
produced choices and paths demonstrably help browsing this testbed, with errors
and omissions visible.

The research therefore does not impose one correct taxonomy or require all
useful parent relationships to be dictionary hypernyms. Source-supported phrase
extension is one candidate relation, lexical abstraction another, and
path-conditioned combinations another. They require different evidence.
Joining them indiscriminately would obscure what each edge means.

## Why SPC01 was selected

SPC01 was designed to derive nominal expressions automatically from the existing
descriptions, preserve their source occurrences, and connect observed extensions
of the same grammatical head. It generated actual candidate paths and
complete menus, including awkward output, rather than manually select attractive
examples. The parser is the same pinned one used in DSP01; its native task is
grammatical annotation, not category membership.[^7]

For example, the existing N037 description “Sourdough bread with cranberry,
rosemary, brown sugar, and cinnamon” provides an opportunity to construct an
ingredient-qualified expression and simpler bread expressions. That is an input
opportunity, not a promised output or required taxonomy. The chicken-dish and
chicken-tractor descriptions likewise expose whether complete phrases improve
on their shared incomplete prefix.

This approach generates a narrow expression and its source support together.
It does not ask a separate classifier to guess every category membership and
then interpret guessed set inclusion as meaning. This may avoid CPC01's specific
classification errors, but literal grammatical identity can miss paraphrases,
merge unresolved senses, and produce unhelpful reporting-language choices.
Those tradeoffs must be measured in the produced paths.

The measured output now contains useful refinements alongside reporting-language
choices and omissions. Its 234 recurring candidates have only 30 links. This
supports a partial construction role, not adoption as a sufficient foundation.
The next unresolved capability is contextual generalization of complete
expressions with justified memberships. Forcing disconnected roots together or
merely recovering the familiar Bread → Sourdough bread edge would not establish
a better browsing method.

The existing baseline and browser remain unchanged. This research informed an
experiment, not an adopted architecture. Detailed hypotheses, competing
explanations, source controls and decision consequences are frozen in the plan.

## Follow-up after SPC01: inference and retrieval must be distinguished

Woods et al.'s separate retrieval study combines lexical relations,
morphological analysis and structured-phrase inference with a graded passage
matching algorithm. It can relate “becomes black” to color change by combining
the relevant lexical relationships; the mechanism is not limited to identical
grammatical heads.[^8]

On 84 answerable UNIX-documentation queries, top-ten answer success rose from
42.9% without the knowledge sources to 50.0% with lexical knowledge and 60.7%
with morphological analysis added. But adding the same subsumption facts to a
commercial search engine degraded results—even when the facts were chosen to
help find relevant documents. The evaluation asks whether an answer appears
in ten results, not whether every category member is correct.[^8]

**Implication for the next experiment:** broader lexical facts may be useful,
but merely adding them to the index or propagating every lexical match is not
a demonstrated solution. A proposed compositional rule must show the relevant
connection in its actual source expression, while any relaxed match remains
separately identified. The paper's hand-built lexicon, semantic axioms and
matching penalties cannot be treated as interchangeable with WordNet or SSE.
The Food-preparation and beet-preservation controls test different parts of
that transfer; no new implementation is selected from this paper alone.

## SPC02 follow-up

The [structural generalization experiment](./STRUCTURAL-GENERALIZATION.md)
implements a bounded comparison informed by these sources. Its
[plan](STRUCTURAL-GENERALIZATION.md#spc02-study-design) records the additional Woods 1997 structural rule and
Luu SIWN method/evaluation qualifications. Universal Dependencies connections
are explicitly an approximation to conceptual relations, not a reproduction.

The complete recurring-multiword audit finds useful new food-preparation paths,
an incorrect dish sense, and valid topical paths lost through grammatical
restrictions. The larger dictionary graph additionally switches meanings at
intermediate expressions. The next method must address contextual meanings and
their bindings; the literature does not justify treating either present matcher
as a complete hierarchy constructor. No method or browser is adopted from
these papers alone.

## Sources

[^1]: Stoica, Hearst and Richardson (2007), [Automating Creation of Hierarchical Faceted Metadata Structures](https://aclanthology.org/N07-1031.pdf), method and evaluation sections.
[^2]: Hearst and Stoica (2009), [NLP Support for Faceted Navigation in Scholarly Collections](https://aclanthology.org/W09-3608.pdf), sections 2.2–2.3.
[^3]: Woods (2000), [Conceptual Indexing: Practical Large-Scale AI for Efficient Information Access](https://cdn.aaai.org/AAAI/2000/AAAI00-215.pdf), conceptual indexing, subsumption and retrieval sections.
[^4]: Ferragina and Gulli (2005), [A Personalized Search Engine Based on Web-Snippet Hierarchical Clustering](https://archives.iw3c2.org/www2005/proceedings/docs/p801.pdf), sections 3 and 5.
[^5]: Zhang et al. (2018), [TaxoGen: Unsupervised Topic Taxonomy Construction by Adaptive Term Embedding and Clustering](https://arxiv.org/html/1812.09551v1), sections 3–5, including Table 2.
[^6]: Luu, Kim and Ng (2014), [Taxonomy Construction Using Syntactic Contextual Evidence](https://aclanthology.org/D14-1088.pdf), sections 2.1–2.3; used for method decomposition, not a claimed replication or transfer accuracy.
[^7]: Qi et al. (2020), [Stanza](https://aclanthology.org/2020.acl-demos.14.pdf); [Universal Dependencies syntax](https://universaldependencies.org/u/overview/syntax.html). DSP01-PLAN.md records the cached model and resource revisions and their training qualifications.
[^8]: Woods et al. (2000), [Linguistic Knowledge can Improve Information Retrieval](https://aclanthology.org/A00-1036.pdf), sections 2–5. Full method and quantitative discussion inspected; the uncontrolled anecdotal evaluations in section 6 are not used as validation.
