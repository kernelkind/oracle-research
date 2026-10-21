# Grammatical structure and shared subjects

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

DSP01 finds usable local phrase structure, but exposes a limit of treating exact
grammatical matches as a replacement for semantic interpretation.
Different grammatical structures can support the same browsing subject.
Some native parses also contain attachment errors; these are separate issues.

No category, source mask, original vector, GDC09 hierarchy or browser changed.
This is a 14-record diagnostic, not a broad accuracy benchmark.

## Inputs and method

The [pre-run plan](DEPENDENCY-DESCRIPTIONS.md#dsp01-study-design) fixes 14 existing subject descriptions from
14 notes, selected from CAP04/PPR01 evidence. Stanza reads the exact descriptions,
not the full notes and not their masks. Full originals and masks are retained
in `./DSP01/inputs.json` for judging what those descriptions mean.

The released English EWT pipeline produces grammatical word trees. Its parser
uses a BiLSTM/biaffine architecture trained for dependency annotations, with
pretrained word embeddings. EWT's web genres make grammatical transfer worth
examining, but its native task is not ingredient recognition or category
containment. The pinned no-character-language-model configuration and its
training/evaluation qualifications are in the plan.[^1]

All words, offsets, lemmas, parts of speech, heads and relation labels are saved
in `./DSP01/parses.json`, together with all 1,121 within-sentence
word-pair paths. Every occurrence remains separate. No similarity threshold,
path-length cutoff or category acceptance rule was introduced.

The path record also preserves prepositions attached beside its words. These
are context for interpretation, not necessarily part of the smaller phrase.
For example, `of` connects “form” to “food preservation”; it is not an extra
qualification of the internal Food-preservation subject.[^2]

## Rosemary used in bread

| Record | Exact subject | Supporting source fragments |
|---|---|---|
| 669 / N037 / V290 | Rosemary in sourdough bread. | ⟦rosemary⟧ ⟦sourdough bread⟧ |
| 254 / N072 / V665 | The author added fresh rosemary and cranberries to the Irish soda bread. | ⟦Irish soda bread⟧ ⟦I added fresh rosemary and cranberries⟧ |

Both originals describe rosemary used in bread. These are not identical recipes,
but the common ingredient subject is legitimate.

The native parser connects bread directly to rosemary in both descriptions.
It keeps `in` for the first and `to` for the second, and tags sentence-initial
Rosemary as a proper noun. The second attachment does not correctly capture
“added … to the bread.” Treating the shared nominal-modifier edge as recovered
ingredient semantics would therefore credit a parsing error.

The [analytical controls](./DSP01/analytical-controls.json) change only that
attachment and the culinary noun tag, leaving native outputs untouched:

```text
669: rosemary — nominal modifier: in → bread
254: rosemary ← object — add — oblique: to → bread
```

The corrected structures still differ. Exact connected-pattern matching does
not supply the interpretation shared by the two. Dropping the intermediate
relation until only rosemary/bread remain would return to the co-occurrence
representation CAP04 showed was insufficient. This does not establish that
semantic normalization is impossible, or that every browsing category must
encode a complete logical relation.

## Coffee experience and an internet dispute

Record 572 / N094 / V852 says:

> Decaffeinated-coffee drinkers drink coffee for the experience of drinking coffee.

Its mask is ⟦Decafe coffee drinkers⟧ ⟦for the experience⟧. The native tree exposes
“experience → drinking → coffee,” along with two paths through earlier coffee
occurrences. Every path is retained rather than choosing the most favorable one.

Record 854 / N086 / V792 says:

> Whether the reader has experienced coffee with a taste profile uniquely their own, rather than merely having had coffee.

Its mask is ⟦You’ve had coffee. But have you had your coffee?⟧
⟦taste profile that’s uniquely yours⟧. The local tree connects the verb
experienced directly to its object coffee. The global attachment around “own”
is questionable, but that does not remove this local relation.

Both support coffee-drinking experience. Yet the noun-plus-drinking construction
and the verb-plus-object construction have different paths, even after simple
lemmatization. Exact structure identity would separate these valid witnesses.

Record 345 / N065 / V561 instead describes making coffee-shop operators experience
losing internet access. Its mask is ⟦Coffee shop⟧
⟦Felt like changing their router/ap passwords so they⟧ ⟦experience⟧
⟦freedom from internet⟧. The tree connects coffee through shop/router/change/want
to experience. This is useful evidence against interpreting the two words as a
coffee-drinking-experience phrase. It does not justify turning path length into
a general semantic score; the parse has other imperfect attachments too.

Thus grammar preserves a useful distinction, but preserving that distinction
does not automatically identify the common meaning of the two positive records.

## Simple phrase evidence and remaining omissions

The complete audit (`./DSP01/audit.json`) covers all 14 records, including:

- **Morning greetings:** rows 258 and 192 share the good/morning adjective
  relation despite hyphenation. Coffee-only row 551 does not. CAP04 already
  found these words; this is a retained capability, not a new discovery claim.
- **Sourdough bread:** rows 40 and 669 share the sourdough/bread compound.
  A broader bread destination remains valid for the rosemary note.
- **Food preservation:** rows 484 and 468 share food modifying preservation.
  But row 468 incorrectly makes stock, rather than the canning activity, the
  subject of “is a form of.” That tree must not establish that plain stock
  itself is a preservation process.
- **Beet freezing:** row 904 explicitly names preservation but not food.
  Even perfect grammatical analysis does not add the knowledge that these
  beets are food. The native lemma also leaves “freezing” unnormalized.
- **Other food material:** the carnivore-diet and Tandoori-chicken records
  lack the narrower preservation/rosemary patterns. They remain valid broader
  food-related material, not globally incorrect neighbors.

## Construction consequence

Do not build an exact-tree miner as though this resolved the shared-category
problem. Retain grammatical attachment as possible evidence, not a mandatory
new pipeline component. A more accurate parser could reduce the native errors,
but would not make every valid paraphrase syntactically identical.

This does not reject mining useful local phrases, require a particular
coffee-experience category, or prove that no useful hierarchy could use these
trees. No common-subtree mining algorithm or resulting hierarchy was evaluated.
The narrower finding is that the observed structures do not themselves normalize
these shared meanings; a complete construction proposal must account for that
limitation rather than silently assuming it away.

This is consistent with Woods' conceptual indexing: it combines structured
phrases with lexical/semantic subsumption, rather than deriving all generality
from syntax. It also uses relaxed passage retrieval for meaning not captured
by extracted phrases. Its reported retrieval benefit is not proof of every
parent–child relation in a note browser.[^3] Syntactic-tree pattern structures
provide a formal common-subtree operation, but their published drug-interaction
classification task does not certify our desired shared subjects.[^4]

The complete approach still needs to propose a recognizable category, accept
different source-grounded witnesses for it, and establish meaningful narrowing.
Neither an exact word intersection, a grammar intersection nor a high affinity
score has established all three. Requiring all witnesses to have one grammar
would add a restriction that the browsing goal does not require.

Before implementing another structural representation, investigate a mechanism
whose native output is text-to-category membership with flexible wording. That
is an alternative to requiring syntactic normalization, not proof of what
caused the previous learned-model errors. Existing phrases/descriptions can
supply candidate inputs, but their adequacy and semantic parent relations still
need separate evidence; matching finite note sets alone does not prove either.

The subsequent lead was GLiClass. It jointly encodes text and
candidate labels and learns classification scores. Its reported training includes
short titles, longer passages, generated positive/negative labels, classification
and NLI. This is closer to accepting different textual witnesses than dictionary
definition relations, although it is not a shared-category generator. The paper
also reports sensitivity to label/text ratios and mixed benchmark performance;
these require controls, not an assumption of reliable membership.[^5]

That training-data and native-code audit, followed by a controlled 14-record
experiment, is now recorded in [TCC01](./NATIVE-CATEGORY-MEMBERSHIP.md). Shared
subjects are recognized, but native acceptance changes with the other supplied
labels and their order. Single-category scoring remains a limited possibility
requiring different-record validation, not an adopted membership rule. Do not
treat the classifier's probabilities as calibrated semantic truth.

## Verification and reproduction

Three new production-path tests failed first for the absent module, then passed.
They cover path direction, repeated occurrences, separate sentences, prepositions,
input preservation and invalid trees. All 44 relevant regression tests pass.
The native cat/dog subject/object smoke
check passes. The 14 descriptions take about 0.51 seconds after loading; peak
process RSS is about 4.9 GiB. Public model/cache files occupy about 233 MiB.
No paid service, GPU or frontier generation was used.

The complete offline replay has byte-identical input records, native parses,
all paths and runner snapshot; model hashes also agree. Timing/RSS measurements
are not expected to be identical. These checks establish reproducibility, not
semantic success. All original GDC09 baseline artifacts remain unchanged.

```sh
env LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  /tmp/oracle-nli-probe-venv/bin/python sse_multivector/dependency_description_probe.py \
  --input sse_multivector/navigation-research-v1/CAP04/result.json \
  --rows 669 254 572 854 345 484 904 468 258 192 551 40 414 658 \
  --cache /tmp/oracle-stanza-probe-cache --offline \
  --output /tmp/dsp01-another-replay
```

Use a new output directory. Omit `--offline` only to fetch the pinned public
models/resources. The environment adds Stanza 1.11.0, emoji 2.15.0 and protobuf
7.36.1 without changing the earlier model packages. Native artifacts remain
separate from the explicitly marked manual grammatical controls.

## Sources

[^1]: Qi et al. (2020), [Stanza](https://aclanthology.org/2020.acl-demos.14.pdf), sections 2–4; [English EWT corpus](https://universaldependencies.org/treebanks/en_ewt/index.html); exact revisions and resource choices in the pre-run plan.
[^2]: [Universal Dependencies syntax](https://universaldependencies.org/u/overview/syntax.html), content/function-word and core-argument sections. A syntactic dependency is not itself a semantic ingredient or topical-containment relation.
[^3]: Woods (2000), [Conceptual Indexing](https://cdn.aaai.org/AAAI/2000/AAAI00-215.pdf), conceptual indexing, passage retrieval and evaluation sections.
[^4]: Leeuwenberg et al. (2015), [Exploring Pattern Structures of Syntactic Trees for Relation Extraction](https://publications.hse.ru/pubs/share/folder/x9m9ofrdni/163919667.pdf), sections 2–3; CSA01 retains its evaluation limitations.
[^5]: Stepanov et al. (2025), [GLiClass](https://arxiv.org/html/2508.07662v1), sections 2–3, including training streams, native label integration and Tables 2–5. DSP01 itself ran no GLiClass model; the later release/data audit and native run are documented separately in TCC01.

## DSP01 study design

### Question and consequence

CAP04 loses attachment when it matches words across gaps, and loses valid
rosemary/bread evidence when it requires adjacency. PPR01 shows that complete
descriptions carry some of the missing meaning, but affinity does not identify
the common subject. Can explicit grammatical connections distinguish these
cases while preserving common subjects across their existing wording?

Test the frozen descriptions, not rewritten notes or concatenated masks.
Use CAP04 rows 669, 254, 572, 854, 345, 484, 904, 468, 258, 192, 551,
40, 414, 658. Preserve their full originals and masks alongside all parses.
The first five cover cross-gap combination and different attachment. Preservation,
greetings, plain bread and other food records expose what grammar cannot supply.
These are diagnosed examples, not an unseen accuracy benchmark.

Hypothesis: a labeled grammatical path can distinguish the known coffee/experience
attachments, but exact path identity will not by itself recover the shared
rosemary/bread subject across a noun phrase and an adding-ingredients clause.
This determines whether exact syntactic common-pattern mining is worth building
as the next category-construction component. No parser is assumed to output
ingredient relations, topical containment or shared abstract categories.

Competing explanations: a difference may arise from an incorrect parse, a correct
syntactic distinction between equivalent meanings, or genuinely different
subjects. Inspect the complete parse and source for each. Where a parse is
incorrect, describe the smallest grammatical correction as an analytical
control, keeping native outputs untouched. A successful corrected parse is not
automatic extraction success. Do not attribute a mismatch to the parser if a
correct tree has the same limitation.

Would either outcome change the next decision? Yes: if native connected
structures retain shared subject evidence across the diagnostic constructions,
investigate common-structure candidate construction. If correct grammar keeps
valid combinations structurally different, do not build an exact-tree miner as
though it solved the missing capability; investigate semantic normalization or
a construction that can retain different witnesses for the same subject.
If neither conclusion follows, stop and record the unresolved discriminator.

### Native method and task fit

Woods combines phrase structure with a lexicon and semantic subsumption rules;
syntax alone is not its concept-comparison mechanism. Even that system needs a
separate relaxed passage matcher for some differently expressed meaning.[^dsp01-study-design-1]
Syntactic-tree pattern structures provide an intersection operation, but their
published experiment classifies already-tagged drug pairs using constituency
trees. This probe is not a reproduction of that classifier or evidence of its
navigation quality.[^dsp01-study-design-2]

Use Stanza 1.11.0's English EWT tokenizer, multiword expansion, lemmatizer,
POS tagger and dependency parser, with released `ewt_nocharlm` POS/lemma/parser
weights and `conll17` word embeddings. Its BiLSTM/biaffine parser learns annotated
grammatical heads and relation labels, not category meanings.[^dsp01-study-design-3] EWT includes
web reviews, blogs, email and answers; this supports investigating English
grammatical analysis of the saved descriptions. Fragmentary subjects and their
generated reporting style remain a transfer assumption, inspected directly.[^dsp01-study-design-4]

The 2020 paper's EWT LAS is 83.59; that is neither semantic accuracy nor a
benchmark of this later exact checkpoint. This small test does not select the
best parser. Omitting the extra character language models limits CPU/memory
cost; observed parsing errors would require a separate diagnostic, not rejection
of all dependency parsing.

Pinned model repository: `stanfordnlp/stanza-en`, revision
`3485d1dd01841c4cace1834d8078395a6f5e4520` (v1.11.0).
Use public downloads without account credentials. One CPU process, two threads,
one description at a time; no paid compute, frontier generation or GPU.

### Procedure

1. Save the complete selected source records without modifying any field.
2. Run the official pipeline on the exact subject strings. Save all tokens,
   lemmas, parts of speech, character offsets, heads and dependency labels.
3. Record every word-pair's unique path within each sentence. Retain all
   intervening words, edge direction and labels. Also retain `case` dependents
   on path words: UD places prepositions beside the path, so bare path extraction
   can otherwise conflate expressions using different prepositions.[^dsp01-study-design-5]
4. Compare all paths for the diagnostic word pairs, including repeated occurrences.
   Compare endpoint-only matches as the co-occurrence control. Do not turn path
   length, shared words or exact path identity into a semantic acceptance score.
5. Audit the original notes, masks, subjects and full parses together. Record
   whether each difference is grammatical error, ordinary syntactic variation,
   semantic distinction, or unresolved. No group, mask or hierarchy is repaired.

An ordinary English subject/object sentence is a native pipeline smoke check,
not a semantic benchmark. Unit tests must exercise the runner's path calculation,
including direction, multiple occurrences, prepositions and malformed trees.
Replay the small run offline and compare saved parses/paths exactly. Save model,
source and code hashes. No TUI is warranted by this component experiment.

### Sources

[^dsp01-study-design-1]: Woods (2000), [Conceptual Indexing](https://cdn.aaai.org/AAAI/2000/AAAI00-215.pdf), conceptual indexing, passage retrieval and evaluation sections.
[^dsp01-study-design-2]: Leeuwenberg et al. (2015), [Exploring Pattern Structures of Syntactic Trees for Relation Extraction](https://publications.hse.ru/pubs/share/folder/x9m9ofrdni/163919667.pdf), sections 2–3; prior CSA01 records the later evaluation and limitations.
[^dsp01-study-design-3]: Qi et al. (2020), [Stanza](https://aclanthology.org/2020.acl-demos.14.pdf), sections 2.1, 3 and 4/Table 2; [official dependency interface](https://stanfordnlp.github.io/stanza/depparse.html).
[^dsp01-study-design-4]: [UD English EWT](https://universaldependencies.org/treebanks/en_ewt/index.html), corpus description; [released models](https://huggingface.co/stanfordnlp/stanza-en/tree/3485d1dd01841c4cace1834d8078395a6f5e4520).
[^dsp01-study-design-5]: [Universal Dependencies syntax principles](https://universaldependencies.org/u/overview/syntax.html), content/function words, core arguments and coordination. These labels are syntactic, not ingredient or topical-subsumption labels.
