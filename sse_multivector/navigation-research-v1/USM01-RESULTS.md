# Contextual source meanings: USM01

Unrestricted matching is not justified as the default source-concept assignment.
It supplies some useful meanings, but often replaces a supported general meaning
with an unsupported subtype or a different related subject. Original-word lookup
already explains the main recoveries from erroneous lemmas. It also has failures:
removing part-of-speech restrictions lets bread become breading and beef become
complaining. No replacement hierarchy was constructed or adopted.

## What was held fixed

The same fifteen descriptions from thirteen notes produced 134 contextual word
vectors. Each word was encoded once with the complete description, using the
released LMMS-SP-USM BERT representation. Original notes and masks were evidence
for interpretation, not extra encoder context. Three candidate restrictions used
the same vectors and scores: saved lemma/POS, original-word morphology across
parts of speech, and the unrestricted sense inventory.

The [pre-run plan](./USM01-PLAN.md) states the hypothesis and competing
explanations. [Complete source results](./USM01/SOURCE-RESULTS.md) show every
original note with its original mask, every encoded description, all 134
highest-match comparisons, definitions and analysis. [Raw results](./USM01/run/scores.json)
retain the top five sensekeys, exact cosines and candidate counts. These are
word meanings, not automatically accepted note categories.

## Recoveries do not require unrestricted matching

| Source word | Saved lemma/POS | Original-word lookup | Unrestricted |
| --- | --- | --- | --- |
| N026 tomatoes · 187/8 | No candidate | Tomato fruit · 0.844034 | Plum tomato · 0.846576 |
| N022 beet · 378/3 | Protective boot casing · 0.488708 | Beet vegetable · 0.629193 | Beet leaves · 0.757154 |
| N096 tomatoes · 544/15 | No candidate | Tomato fruit · 0.820750 | Plum tomato · 0.831517 |
| N096 simmering · 544/22 | No candidate | Low-temperature boiling · 0.790283 | Same meaning and score |

The source masks explicitly mention tomatoes, beets and simmering. They do not
establish plum tomatoes or beet leaves. Thus unrestricted assignment cannot be
credited with these recoveries merely because it improves on missing candidates
or boot casing. The stronger original-word control already recovers their subject.
Root versus crop-plant beet senses need not have one prescribed correct answer;
the unsupported leaves selection is a separate matter.

## Genuine additional capability, with consequential regressions

Two useful unrestricted changes stand out:

- N096, 544/7: sautéing has no candidate under either lexical condition, while
  unrestricted matching gives frying—cooking in fat/oil in a pan. The original
  mask and recipe explicitly support that broader cooking operation.
- N094, 88/17: general addiction becomes caffeine addiction. Both the description
  and original contrast support it. This does not assert addiction of decaf drinkers.

Other changes retain the general topic but invent detail. Three chicken
occurrences become specifically young chickens; fireworks become aerial rockets;
yeast becomes compressed moist yeast. They are related, not source-established
refinements. Several changes would support plainly wrong narrower destinations:

| Source meaning | Original-word highest match | Unrestricted highest match |
| --- | --- | --- |
| N026 chicken stock · 187/22 | Broth · 0.718665 | Beef broth · 0.727057 |
| N065 router · 345/9 | Packet-forwarding router · 0.599844 | Telephone-line modem · 0.680306 |
| N013 pressure-canning · 468/2 | Canning operation · 0.645152 | Canning factory · 0.692435 |
| N096 basil · 544/19 | Culinary basil leaves · 0.629954 | Basil thyme, a different plant · 0.738908 |
| N096 sauce · 544/24 | Sauce · 0.799509 | Soy-based Chinese sauce · 0.825067 |

These are not merely low scores for unrelated content. The unsupported meaning
ranks above the valid broader meaning in this representation. A single score
cutoff cannot admit the latter while excluding the former within that ordering.
This does not rule out another selection mechanism or show all models fail.

Not every change is bad: the spaghetti token's unrestricted match is spaghetti
sauce, which the original recipe also discusses. It is not the same token
meaning, but can be a valid note subject. Baking versus oven-baking is another
change without a demonstrated substantive topic failure. The audit keeps these
separate from unsupported identities rather than assigning a blanket error count.

## Lexical restrictions are not a complete solution

Original-word matching changes nineteen highest synsets relative to saved
lemma/POS. Some changes are sensible noun/verb/adjective variants: planned,
used, drinking and cooking. Eight previously empty candidate sets become
nonempty, but nonemptiness is not semantic accuracy.

Other changes expose the cost of discarding POS:

- N100, 350/0: beef becomes complaining. Its original note concerns cutting
  sirloin into steaks. The saved noun sense denotes cattle rather than meat;
  it is related, but not an exact description of the selected food.
- N089, 866/0: bread becomes covering something with breadcrumbs. The original
  mask concerns bread ingredients and mixing, not breading another item.

Several errors remain under every condition. Preparing beets in 904/3 means
preparing a written or spoken delivery. Preparation in 350/3 and 866/1 is a
substance prepared by formula rather than an activity. Bagging chicken meat is
misread as hunting or coarse sack fabric. Side dishes and wireless access point
are not faithfully recovered by their separate word targets. Cooking equipment
called a smoker still becomes a tobacco user; its top five unrestricted matches
remain tobacco-related.

There are also useful retained meanings: coffee and experienced events, storm
cycles and grilling, bread/pans/ashes, broth and pantry, culinary craft, salt and
mixing, garden cultivation and preservation. Compared descriptively with earlier
DRS outputs, broth avoids financial stock, storm cycles avoid professional visits,
and experienced events avoid accumulated knowledge. This is not a controlled
attribution to one changed parser feature: the source representation itself changed.

Every judgment separates the sense's fit to the generated description from
support in the original mask. For example, the word author does not establish a
professional paid writer. N076's original chef hashtag reasonably supports a
culinary topic; it does not prove professional employment or every literal detail
in its expanded description. A representation can fit an input expansion without
validating that expansion.

## Decision and remaining construction question

Do not adopt unrestricted top-one meanings. Preserve lexical evidence and
separate faulty lemmatization from faulty contextual ranking. The next small
distinguishing control can reuse these frozen vectors: original-word morphology
with the saved POS retained. It tests whether keeping that evidence avoids the
bread/beef regressions while retaining the useful lemma corrections. It is not a
new model, new description prompt, or assumed complete fix.

After that decision, investigate the actual construction consequences of an
algorithmically chosen representation. Do not hand-select correct meanings and
call the resulting hierarchy an automatic success. Nor require perfect senses
for all 134 words: useful cooking/brisket discovery does not require recovering
every smoker sense. What remains unproven is whether retained source meanings
and a valid broader relation produce useful complete note destinations without
false admissions. The earlier beet ancestry gap, ontology mapping errors,
category selection and redundant note sets remain independent concerns.

## Verification and preserved state

- 134 targets, fifteen descriptions, thirteen notes; all offsets recover exact
  description text. All previously malformed DRS descriptions are processed,
  without crediting output existence as semantic recovery.
- Empty candidate sets: saved 10, original-word 2, unrestricted 0. The earlier
  lookup audit found nine saved-lemma/POS empties because `wn.synsets` also applies
  morphology; the native exact-sensekey condition does not. Freezing accounts
  for the extra empty set. No requested WordNet sensekey is missing from the
  downloaded inventory.
- Nineteen highest synsets change saved→original-word; twenty-nine change
  original-word→unrestricted; forty-one change anywhere. These are mechanical
  counts, not an accuracy estimate or forty-one failures. Repeated descriptions
  and tokens from one note are not independent note evidence.
- The new runner test suite first failed on importing the missing module; all
  seven tests passed after implementation. They exercise production pooling, tokenization, candidate selection,
  ranking, input validation and bounded inventory loading. Independent source
  review found no blocking fidelity defect. This does not replace semantic review.
  All 61 existing semantic-graph/ontology regression tests also pass.
- Independent replay from saved vectors matches all 402 condition comparisons
  and all 1,579 saved cosine values exactly, with maximum difference 0.0.
  Candidate metadata, sensekeys, synsets, definitions and artifact hashes match.
  This verifies matching reproducibility without rerunning the neural encoder.
- Encoding including model loading: 2.873 s. Inventory loading and matching:
  40.466 s. Peak process RSS: 5,517,548 KiB, approximately 5.3 GiB. One CPU process,
  two Torch threads; no paid compute. These phase times exclude separate hash
  verification and output writing.
- Published checkpoint, ZIP and layer hashes verified; 206,949 sensekeys,
  1,024 dimensions. CPU/eager attention, NumPy 2.3.4 float64 weighting/scores,
  shared file-order tie breaking, 24 selected layers and unused 25th weight are
  explicit adaptations, not a byte-identical published benchmark claim.
- [Execution record](./USM01/execution.json), [configuration](./USM01/run/config.json),
  [tokenization](./USM01/run/tokenization.json), saved target vectors and runner
  source preserve the experiment. Original GDC09, SGC01–03, masks and browser
  remain unchanged. No UI packaging.
