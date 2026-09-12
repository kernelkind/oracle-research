# Dependency structure diagnostic

## Question and consequence

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

## Native method and task fit

Woods combines phrase structure with a lexicon and semantic subsumption rules;
syntax alone is not its concept-comparison mechanism. Even that system needs a
separate relaxed passage matcher for some differently expressed meaning.[^1]
Syntactic-tree pattern structures provide an intersection operation, but their
published experiment classifies already-tagged drug pairs using constituency
trees. This probe is not a reproduction of that classifier or evidence of its
navigation quality.[^2]

Use Stanza 1.11.0's English EWT tokenizer, multiword expansion, lemmatizer,
POS tagger and dependency parser, with released `ewt_nocharlm` POS/lemma/parser
weights and `conll17` word embeddings. Its BiLSTM/biaffine parser learns annotated
grammatical heads and relation labels, not category meanings.[^3] EWT includes
web reviews, blogs, email and answers; this supports investigating English
grammatical analysis of the saved descriptions. Fragmentary subjects and their
generated reporting style remain a transfer assumption, inspected directly.[^4]

The 2020 paper's EWT LAS is 83.59; that is neither semantic accuracy nor a
benchmark of this later exact checkpoint. This small test does not select the
best parser. Omitting the extra character language models limits CPU/memory
cost; observed parsing errors would require a separate diagnostic, not rejection
of all dependency parsing.

Pinned model repository: `stanfordnlp/stanza-en`, revision
`3485d1dd01841c4cace1834d8078395a6f5e4520` (v1.11.0).
Use public downloads without account credentials. One CPU process, two threads,
one description at a time; no paid compute, frontier generation or GPU.

## Procedure

1. Save the complete selected source records without modifying any field.
2. Run the official pipeline on the exact subject strings. Save all tokens,
   lemmas, parts of speech, character offsets, heads and dependency labels.
3. Record every word-pair's unique path within each sentence. Retain all
   intervening words, edge direction and labels. Also retain `case` dependents
   on path words: UD places prepositions beside the path, so bare path extraction
   can otherwise conflate expressions using different prepositions.[^5]
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

## Sources

[^1]: Woods (2000), [Conceptual Indexing](https://cdn.aaai.org/AAAI/2000/AAAI00-215.pdf), conceptual indexing, passage retrieval and evaluation sections.
[^2]: Leeuwenberg et al. (2015), [Exploring Pattern Structures of Syntactic Trees for Relation Extraction](https://publications.hse.ru/pubs/share/folder/x9m9ofrdni/163919667.pdf), sections 2–3; prior CSA01 records the later evaluation and limitations.
[^3]: Qi et al. (2020), [Stanza](https://aclanthology.org/2020.acl-demos.14.pdf), sections 2.1, 3 and 4/Table 2; [official dependency interface](https://stanfordnlp.github.io/stanza/depparse.html).
[^4]: [UD English EWT](https://universaldependencies.org/treebanks/en_ewt/index.html), corpus description; [released models](https://huggingface.co/stanfordnlp/stanza-en/tree/3485d1dd01841c4cace1834d8078395a6f5e4520).
[^5]: [Universal Dependencies syntax principles](https://universaldependencies.org/u/overview/syntax.html), content/function words, core arguments and coordination. These labels are syntactic, not ingredient or topical-subsumption labels.
