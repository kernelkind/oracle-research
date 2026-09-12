# SGC01: contextual semantic graphs and category construction

## Question

Can a contextual semantic parser supply source-faithful meanings and bindings
that a generic graph-generalization operation turns into useful category paths?
SPC02 lost the food-preparation relation across different grammatical forms
and accepted the wrong sense of washed dishes. A parser score alone would not
answer the construction question.

## Method and fit

Use the released `XiaoZhang98/byT5-DRS` checkpoint, revision
`d8ec0dea6b9ac786927a864bfe87bca0951b2ce7`, on unchanged saved descriptions.
Its native interface is text to a serialized semantic representation; unlike
SRR's definition-pair classifier, contextual sentence interpretation is the
intended task. PMB representations contain WordNet concepts and role-linked
participants. This addresses an observed representation gap rather than
assuming another embedding or similarity threshold will repair construction.

The checkpoint identifies ByT5-base; its sparse card does not establish the
exact training split or identify it with the larger models reported in PMB5.
Do not attribute paper scores to this release. Published PMB evaluations expose
both sense/role errors and severe length sensitivity. Our short descriptions
are a closer input match than full informal notes, but nominal descriptions,
unusual vocabulary and faithful transfer from their masks remain assumptions.
Keep originals and masks alongside every output. No input rewrites or model
fine-tuning are part of this experiment.

Construction will use the predicted concepts, not every possible sense of each
spelling. Enumerate single-concept and single-role patterns, retaining the two
specific participants joined by each role. Broaden concepts only through the
cached WordNet 3.0 hypernym/instance-hypernym relations; retain unknown concepts
literally. Keep roles exact in this first diagnostic. Do not merge nominal and
verbal predicates through guessed equivalence, infer missing roles, or invent
food-specific bridges. Record all resulting patterns and their source witnesses.

This is a bounded use of order-labelled graph generalization, not a reproduction
of RHOG's entire algorithm. A broader pattern contains a narrower one when it
drops a role constraint or replaces a concept with its recorded ancestor while
preserving the relationship. Source-note membership follows the actual pattern
witness; it is not supplied by an independent classifier. Multiword topics can
therefore arise without occurring as literal phrases. Full multi-role graphs,
category selection, natural labels and a production browser remain unproven.

## Fixed inputs

Select these 15 rows from the unchanged SPC01 inputs before inference:

- 91: storms and dinner grilling;
- 187: dishes washed after food preparation;
- 350: beef and steak preparation;
- 375: baking bread;
- 378: beet side dishes;
- 405: other people's sake;
- 468: pressure-canning chicken stock for preservation;
- 544: spaghetti preparation, including frying beef;
- 572: experiencing coffee;
- 673: food preparation and chefs;
- 711: cooking brisket;
- 866: bread preparation;
- 904: preparing beets for freezing;
- 345: experiencing loss of internet access at a coffee shop;
- 88: coffee experience and flavour rather than caffeine dependence.

These are mechanism probes selected from observed failures, valid recoveries
and source contrasts, not an unseen accuracy sample. Aliases from the same note
do not count as independent notes. The model card's `I am a student.` is a
separate native-format control and must not enter category construction.

## Hypothesis, alternatives and decisions

Hypothesis: contextual concepts and participant bindings preserve at least some
shared activity/material meaning across the saved grammatical variants, allowing
source-supported multiword generalizations without the wrong dish/sake senses.
No exact taxonomy or title is required, and success is not merely generating
Food or another isolated ancestor word.

Competing explanations are parser errors, missing or inappropriate dictionary
relations, incompatible semantic-role choices, overly restricted patterns, and
incorrect supplied descriptions/masks. Inspect native output before attributing
an absent path to the constructor. Inspect every source witness of a claimed
improvement before attributing a new path to semantic understanding.

Would either outcome change the next decision?

- Faithful graphs plus useful grounded paths justify expanding this construction
  test beyond the selected examples, not adopting a complete hierarchy.
- Faithful graphs without useful paths identify a remaining constructor or
  lexical-coverage question; another parser run would not answer it.
- Wrong graphs prevent this checkpoint's outputs from validating construction.
  A syntactically valid output or a correct final note set is insufficient.
- Truncated or malformed outputs first require an implementation/format diagnosis;
  do not silently repair them or score them as semantic counterexamples.

Compare literal graph patterns with patterns generalized by the fixed dictionary.
Keep single-concept recovery separate from relationship-preserving recovery.
Inspect all source-level errors, recurring role patterns at their most specific
available generalizations, and complete candidate paths used for any conclusion.
Record alternative coherent readings rather than enforce one preferred hierarchy.

## Execution and preservation

Use local CPU inference, one loaded model, two compute threads, one input at a
time. The public weights are approximately 2.33 GB; no paid resource is needed.
Check available memory before loading. Save raw output and token counts per input,
including whether generation reached EOS. Do not truncate inputs. Use a fixed
2,048-new-token output allowance to avoid treating the checkpoint's saved
256-token generation default as a semantic limitation.

Write new artifacts under `SGC01/`; preserve GDC09, SPC01, SPC02 and unrelated
work. Implement minimal production-path tests first. Validate serialization,
relative references, inverse roles and pattern provenance without changing any
approved tests. Reproduce deterministic construction from saved native outputs.
No UI packaging during this investigation.

## Primary sources

- [Bos 2023, sequence notation, sections 2–3](https://aclanthology.org/2023.iwcs-1.20.pdf).
- [PMB role definitions](https://pmb.let.rug.nl/roles.php).
- [Zhang et al., PMB5, sections 3–4](https://arxiv.org/html/2404.08354v2).
- [Shen and Evang 2022, contextual DRS parsing and error analysis](https://aclanthology.org/2022.starsem-1.19.pdf).
- [Released checkpoint and native usage](https://huggingface.co/XiaoZhang98/byT5-DRS/tree/d8ec0dea6b9ac786927a864bfe87bca0951b2ce7).
- [Ontañón 2016, order-labelled graph subsumption and upward refinement](https://arxiv.org/pdf/1604.06954).
