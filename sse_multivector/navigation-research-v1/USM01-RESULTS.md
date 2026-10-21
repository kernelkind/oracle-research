# Contextual source meanings: USM01

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

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

The [pre-run plan](USM01-RESULTS.md#usm01-study-design) states the hypothesis and competing
explanations. [Complete source results](./USM01/SOURCE-RESULTS.md) show every
original note with its original mask, every encoded description, all 134
highest-match comparisons, definitions and analysis. Raw results (`./USM01/run/scores.json`)
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
  40.466 s. The recorded `ru_maxrss` is 5,517,548 KiB, but a later USC01 control
  showed that this launcher can pass its pre-exec high-water mark to that metric.
  Do not interpret it as this encoder's isolated peak memory. The historical
  measurement is preserved; current runners use `/proc/self/status` `VmHWM`.
  One CPU process, two Torch threads; no paid compute. These phase times exclude
  separate hash verification and output writing.
- Published checkpoint, ZIP and layer hashes verified; 206,949 sensekeys,
  1,024 dimensions. CPU/eager attention, NumPy 2.3.4 float64 weighting/scores,
  shared file-order tie breaking, 24 selected layers and unused 25th weight are
  explicit adaptations, not a byte-identical published benchmark claim.
- Execution record (`./USM01/execution.json`), configuration (`./USM01/run/config.json`),
  tokenization (`./USM01/run/tokenization.json`), saved target vectors and runner
  source preserve the experiment. Original GDC09, SGC01–03, masks and browser
  remain unchanged. No UI packaging.

## USM01 study design

Status: selected, not yet run. [Research and prerequisite audit](SOURCE-OCCURRENCE-GROUNDING.md).

### Question and construction role

Does unrestricted contextual matching add useful source meanings beyond a
generic lookup using the original word, while retaining correct interpretations?
The current dictionary lookup cannot recover beet when its input is boot.
This is a known input restriction; it is not yet evidence that unrestricted
matching will choose beet rather than another related or unrelated meaning.

The plausible construction path is source occurrences → contextual concepts →
shared, broader patterns → meaningful note destinations. This comparison tests
the first transition only. It does not add an alignment layer to the DRS parser.
If source-valid meanings improve, their actual construction consequences must
be traced before adopting the representation. Fine-grained roles, an exact
taxonomy and perfect word-sense accuracy are not prerequisites imposed here.

### Fixed inputs

Use all fifteen unchanged SGC01 descriptions from thirteen notes, including
the four that produced malformed DRS graphs. Their original notes, masks and
aliases remain audit evidence, not new encoder context. Freeze the existing
SPC01 token text/offsets and predicted lemma/POS; do not repair beet, tomatoes,
simmering or other annotations by hand.

Use all 134 NOUN/PROPN/VERB/ADJ/ADV occurrences identified in the lookup audit,
not just known failures. Encode each complete description with all its tokens;
the target is the current token's contextual representation. Assert the token
offsets against its exact description before inference. No extra subjects,
multiword targets, definitions or paraphrases are generated for this run.

These are word occurrences within generated descriptions, not SSE vectors or
new original-note masks. A success would not validate every generated
description or establish complete multiword extraction.

### One representation, three conditions

Use the released LMMS-SP-USM BERT-large-cased **sensekey** vectors and pinned
BERT/weight artifacts listed in the research record. Do not switch to the
separate synset vectors or SP-WSD profile.

Encode every occurrence once, normalize its vector, then score the same
released sense inventory in three conditions:

1. **Saved lemma:** restrict matches to the saved lemma and part of speech,
   following the released `match_senses` interpretation. An empty set remains
   empty; no most-frequent-sense fallback or manual correction.
2. **Surface word:** use WordNet's existing morphology on the original token,
   across noun, verb, adjective and adverb. Admit sensekeys for those lexical
   forms only, not every synonym in their synsets. This uses NLTK 3.9.2's
   `_morphy` followed by exact-name `lemmas` lookup, without special-case repairs.
3. **Unrestricted:** use all entries, without lemma/POS restrictions.

The surface-word condition is necessary: its candidate lookup already repairs
the known beet/tomatoes/simmering exclusions. Beating the saved-lemma condition
alone would not justify removing lexical restrictions generally. PROPN uses
NOUN in the saved-lemma condition, matching the audit's WordNet convention.

Retain the highest match and the top five distinct sensekeys for each
condition, including their canonical synset IDs and definitions. Synonymous
keys may map to the same synset: report that explicitly, not as independent
support. Additional lexical alternatives are diagnostic, not five accepted
subjects. No cutoff is fitted and no missing-sense rejection is assumed.

Use the author's evaluation convention: the last 24 hidden states in reverse
order with the first 24 published weights, mean WordPiece pooling per supplied
token, then normalization. Record that the 25th weight is unused, as in the
evaluation source; the embedding-build scripts use 25 states. Keep this choice
fixed across all conditions. This CPU/safetensors application is not a claim
to reproduce the published benchmark exactly.

### Hypothesis, alternatives and decisions

The hypothesis is that unrestricted matching supplies source-valid highest
matches unavailable or misranked under surface-word lookup, without enough
regressions to defeat its value for construction.

Competing explanations include:

- The useful change is simply bypassing erroneous lemmas. If surface-word
  lookup explains the gains, there is no demonstrated reason to drop lexical
  evidence and search the entire inventory.
- The intended meaning is available, but the contextual representation cannot
  rank it above merely associated meanings.
- Restricted matching is useful lexical evidence on ordinary cases even though
  its errors exclude correct meanings elsewhere.
- Neither condition can identify a sense absent from the inventory. Smoker's
  missing cooking-equipment sense must not become a false success by choosing
  a nearby person or a more specific, unsupported device.
- Target tokenization, the description itself or the inference implementation
  can fail independently of the representation.

Inspect the actual description and its original mask/note for every changed
highest match, all existing known failures and the unchanged controls. Record
separately whether the matched sense fits the encoder description and whether
that description/occurrence is supported by the original mask. Separate
an appropriate source meaning from a supported broader topic, a merely
associated concept and a genuinely unsupported interpretation. Preserve
reasonable ambiguity rather than force a unique dictionary answer.

Would either outcome change the next decision? Yes. Useful source-valid gains
beyond surface-word lookup, with manageable regressions, justify tracing
unrestricted matching through actual construction. If surface-word lookup
explains the gains, prefer that simpler restriction for the next investigation.
Strong gains only in the top five justify candidate proposal,
not automatic top-one assignment. Widespread unrelated matches instead argue
against unrestricted assignment; another cutoff cannot remove higher-ranked
wrong meanings while admitting lower-ranked correct ones. If implementation
fidelity is uncertain, resolve that before making a semantic conclusion.

The four newly processable descriptions are not credited as semantic coverage
merely because their outputs exist. Their interpretations require the same
audit. The beets/preparation ancestry gap and later SUMO errors remain separate
limitations even if individual words are interpreted correctly.

### Execution constraints

Before inference, verify public asset hashes, native token/layer pooling and
safe local loading. Create minimal failing tests for any new runner behavior,
then implement the smallest production path and run relevant regressions.
Use local CPU, two Torch threads and one inference process. Do not rent compute,
call a paid API, execute unpinned downloaded code or load remote pickle objects.
Check available memory and cap loading allocations; never run this concurrently
with another model load. Verify no truncation and preserve empty candidates.

Save exact source identities, input hashes, model/resource hashes, code
snapshots, tokenization, target vectors, scores, actual runtime/memory, and
source-grounded judgments. Preserve the baseline and all previous results.
No UI packaging is part of this diagnostic. The next construction decision
must follow its evidence; this plan does not declare a replacement hierarchy.
