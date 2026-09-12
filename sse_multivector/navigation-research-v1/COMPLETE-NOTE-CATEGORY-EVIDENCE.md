# Complete note evidence for category membership

TCC03 restores the judged Coffee note ordering by allowing every existing
description of each note to contribute. Morning greetings remains separated.
This is a useful result: an incorrectly ordered individual witness need not
prevent finding its note through another, genuinely supporting witness.

The native 0.5 cutoff nevertheless gets worse. After expansion it puts every
one of the 20 notes under Morning greetings. Useful score ordering and a useful
membership decision are different requirements. No cutoff or hierarchy is adopted.

## What was tested

The same 20 TCC02 notes supply 181 saved descriptions covering 177 canonical
masks. Each description is independently scored against Coffee and Morning
greetings, one category per request. The model, category strings, rendering,
native implementation and weights remain fixed. No original text, mask or
subject was rewritten; the classifier still sees only a subject description.

The control gives each note the highest score among its TCC02 descriptions.
The changed condition gives it the highest score among all its descriptions.
Both conditions use the same TCC03 score matrix. This accepts a note if any
description exceeds a fixed threshold, intended as a proxy for a genuinely
supporting mask. It does not establish that support, calculate its probability,
or combine evidence inside the model.

The [plan](./TCC03-PLAN.md) and [full-note judgments](./TCC03/judgments.json)
were frozen before additional inference. The main and independent reviewers
read all 20 originals and 181 descriptions/masks. These are previously examined
notes, not a new holdout. Coffeechain-only and caffeine-only cases remain
unjudged for Coffee. Afternoon greetings, “Rise and grind,” and “Dear America”
remain greeting-scope boundaries. These full-note judgments are separate from
TCC02's unchanged individual-witness judgments.

## Result

| Category and evidence | Lowest supported note | Highest unsupported note | Inverted supported–unsupported pairs |
| --- | ---: | ---: | ---: |
| Coffee, control | 0.839482 | 0.859700 | 1 of 66 |
| Coffee, all descriptions | 0.985625 | 0.859700 | 0 of 66 |
| Morning greetings, control | 0.999392 | 0.996623 | 0 of 72 |
| Morning greetings, all descriptions | 0.999392 | 0.998944 | 0 of 72 |

The same notes and predeclared full-note judgments are used in both conditions.
The pair counts are not independent trials or a corpus-wide accuracy estimate.
Perfect ordering here does not establish a transferable cutoff.

## The recovered cafe note

N004's complete original:

> Weird #coffeechain today
> Rave at a coffee shop lol https://video.nostr.build/252e03e0d852e21d29e875ca7e1f381ad5559b8eee53b4a683babcb688b946ed.mp4

Its TCC02 description, row151, was:

> A rave taking place at a coffee shop.

The mask was ⟦Rave at a coffee shop⟧ and the Coffee score was **0.839482**.
That was below N099's plain greeting, **0.859700**.

Another existing N004 description, row784, is:

> Amusement at a rave taking place at a coffee shop.

Complete original with that mask:

> Weird #coffeechain today
> ⟦Rave at a coffee shop lol⟧ https://video.nostr.build/252e03e0d852e21d29e875ca7e1f381ad5559b8eee53b4a683babcb688b946ed.mp4

Its Coffee score is **0.928681**, above every judged unsupported note.
Both descriptions were generated before this experiment. The model did not
repair row151 or combine the two; allowing another grounded description gave
the note another route into Coffee.

The actual maximum is still higher: **0.985625**, from row0, “An unusual
coffee-themed social-media post,” supported by ⟦Weird⟧ ⟦#coffeechain⟧.
That hashtag-derived winner is weaker evidence of recognizing the cafe passage.
The independently sufficient row784 is why the recovery can be credited
without relying on the hashtag. This is an explanatory source check, not a
manual change to the algorithm or a retroactively selected decision threshold.

For comparison, the highest judged-negative note, N099, remains:

> ⟦GM⟧ happy pizza day to those who observe

The attaining description is “A good-morning greeting,” row361, score
**0.859700**. N099's other existing descriptions concern Pizza Day and do not
raise its maximum. Its readable source supplies no Coffee subject.

## Other recovery and source checks

N036 changes from “Iced coffee,” **0.936674**, to the existing broader
description “Coffee,” **0.999088**, with mask ⟦coffee⟧ inside “Iced coffee.”
Its other detailed serving descriptions also score above **0.9856**. This is
another case where a more general existing witness can recover the note;
it does not establish that the more specific witness was semantically wrong.

Two additional maxima require qualifications:

- N038's winner is Coffeechain-derived, **0.997014**, but its original
  music-in-a-coffee-shop description already scores **0.971751**, above the
  highest judged-negative note.
- N035's winner interprets “cool places” as cold temperatures, **0.999208**.
  The source does not resolve that interpretation. Its unambiguous “Coffee”
  record scores **0.999088**, and the original place-related description
  already scores **0.998646**. Membership does not depend on endorsing the
  temperature reading.

The remaining changed supported Coffee maxima—rows879, 672, 285 and 697—are
grounded coffee descriptions. All eight supported greeting maxima remain
unchanged and come from genuine greeting masks. Every one of the 40 expanded
note/category maxima was independently inspected; the source evidence is in
[inputs.json](./TCC03/inputs.json), not inferred from the winning score.

## Where expansion hurts

Taking a maximum over more descriptions cannot lower a note's score. It can
find better evidence, but it also gives unrelated descriptions more chances
to receive a high score. The native cutoff shows both effects:

| Category | Judged unsupported notes admitted: control → all | All notes admitted: control → all |
| --- | ---: | ---: |
| Coffee | 2 → 3 | 16 → 17 |
| Morning greetings | 7 → 9 | 18 → 20 |

Coffee newly admits N064 through row480, **0.643087**:

> The author is spending time working in the kitchen, as usual.

Complete original with that mask:

> GM! 💜🫂 How are you today?
> It's now after Christmas, things are slowly getting back to normal and I'm starting to slow down. In the ⟦kitchen⟧ ⟦as always⟧ a lot of ⟦work⟧ but I like it 😂😂
> From all this I even forgot to take photos 🙈Today meat dumplings, so out of sentiment....
> #food #foodstr #plebchain https://image.nostr.build/3fb21ce7646872c6b17a873a3849f902dca94e24079fdcb5d99db096a3056653.jpg https://image.nostr.build/d63ddf6c600431c95faa2ce795c99d7653afa1c300d2f0a1a5cb922a1b2ed60d.jpg

Morning greetings newly admits N004 through its coffee-themed-post description,
**0.947067**, and N034 through row647, **0.817115**:

> The author feels sleepy.

Complete original with the existing row647 mask:

> I've had a stupid amount of caffeine today and ⟦I⟧ still feel so tired. 4 more hours of work. ⟦😴⟧

Neither the cafe note nor the sleepy note greets anyone. At 0.5, Morning
greetings therefore admits all 20 notes, despite correctly ordering its eight
judged greeting notes above the nine judged nongreeting notes. The three
scope-unresolved notes remain outside those correctness counts.

The strongest nongreeting maximum rises to **0.998944**: N043, row479,
“Incorporating movement into a morning through coffee-fetching, stretching,
and bowing.” Its source says what the author does in the morning; it does
not greet the audience. The complete original with that mask:

> Beyond ⟦9am⟧. Hazy sunlight on dusty desk. First tasks done, first minutes written, first things postponed. ⟦Fetching coffee⟧ as a ritual of motion, as well as doing some clumsy ⟦stretching⟧ and ⟦bowing⟧ to fight the physical and mental rust, to counter the effects of being stuck in the same position for too long.

The weakest genuine greeting still scores **0.999392**. Do not translate
this observed separation into a selected threshold or a general reliability
claim. Notes in this set have 3–34 descriptions; it does not estimate how
additional descriptions affect arbitrary notes or categories.

## Complete maximum-score record

Rows are existing subject/mask record IDs, not hierarchy nodes. The judgment
is for the full note. Each table includes every note, including unresolved
category-scope cases. Full precision, all attaining rows and all inversions
are in [audit.json](./TCC03/audit.json).

### Coffee

| Note | Judgment | Control: row, score | All descriptions: row, score |
| --- | --- | --- | --- |
| N004 | supported | 151 · 0.839482 | 0 · 0.985625 |
| N005 | unjudged | 133 · 0.731378 | 701 · 0.997014 |
| N018 | supported | 763 · 0.999216 | 879 · 0.999230 |
| N031 | unsupported | 10 · 0.341430 | 10 · 0.341430 |
| N034 | unjudged | 928 · 0.985611 | 928 · 0.985611 |
| N035 | supported | 17 · 0.998646 | 584 · 0.999208 |
| N036 | supported | 62 · 0.936674 | 847 · 0.999088 |
| N038 | supported | 825 · 0.971751 | 382 · 0.997014 |
| N043 | supported | 537 · 0.998431 | 672 · 0.998773 |
| N045 | supported | 119 · 0.998466 | 119 · 0.998466 |
| N052 | supported | 194 · 0.996714 | 285 · 0.998333 |
| N058 | supported | 274 · 0.999337 | 274 · 0.999337 |
| N064 | unsupported | 913 · 0.361204 | 480 · 0.643087 |
| N071 | supported | 136 · 0.999193 | 136 · 0.999193 |
| N073 | unsupported | 564 · 0.148770 | 4 · 0.153456 |
| N080 | unsupported | 635 · 0.150453 | 474 · 0.495831 |
| N089 | unsupported | 539 · 0.762822 | 539 · 0.762822 |
| N092 | unjudged | 71 · 0.946979 | 71 · 0.946979 |
| N095 | supported | 273 · 0.998932 | 697 · 0.999114 |
| N099 | unsupported | 361 · 0.859700 | 361 · 0.859700 |

### Morning greetings

| Note | Judgment | Control: row, score | All descriptions: row, score |
| --- | --- | --- | --- |
| N004 | unsupported | 151 · 0.388218 | 0 · 0.947067 |
| N005 | supported | 133 · 0.999456 | 133 · 0.999456 |
| N018 | unjudged | 763 · 0.998573 | 763 · 0.998573 |
| N031 | unsupported | 10 · 0.993018 | 45 · 0.994303 |
| N034 | unsupported | 928 · 0.145654 | 647 · 0.817115 |
| N035 | unsupported | 17 · 0.994438 | 577 · 0.996893 |
| N036 | unsupported | 62 · 0.976533 | 847 · 0.996893 |
| N038 | unsupported | 825 · 0.982568 | 923 · 0.992934 |
| N043 | unsupported | 537 · 0.996128 | 479 · 0.998944 |
| N045 | unjudged | 119 · 0.932986 | 921 · 0.952063 |
| N052 | unjudged | 194 · 0.935329 | 744 · 0.998258 |
| N058 | supported | 651 · 0.999467 | 651 · 0.999467 |
| N064 | supported | 913 · 0.999392 | 913 · 0.999392 |
| N071 | supported | 619 · 0.999482 | 619 · 0.999482 |
| N073 | unsupported | 564 · 0.752490 | 564 · 0.752490 |
| N080 | unsupported | 635 · 0.996623 | 552 · 0.998715 |
| N089 | supported | 539 · 0.999467 | 539 · 0.999467 |
| N092 | supported | 71 · 0.999521 | 71 · 0.999521 |
| N095 | supported | 255 · 0.999533 | 255 · 0.999533 |
| N099 | supported | 361 · 0.999469 | 361 · 0.999469 |

## Construction decision

The selected-witness failure overstated the obstacle to note retrieval.
Complete available descriptions provide sufficient grounded evidence to restore
the tested Coffee ordering while preserving greeting ordering. Retain this
as evidence for a potentially useful membership component, not an adopted
membership rule. The native cutoff is decisively unsuitable for this use.

The consequential remaining question is how to obtain defensible membership
decisions from these category-dependent scores without choosing cutoffs from
the same examples used to claim success. Research calibration methods against
their actual supervision and input assumptions before testing one. Preserve
the distinction between a rule applicable to new categories and hand-fitting
these two diagnostic labels. No model-size increase or new wording variant is
justified by this result alone.

Automatic category proposals and meaningful parent–child construction remain
separate dependencies. The current result does not justify treating predicted
note-set inclusion as semantic parenthood, and it does not validate GDC09's
existing ancestry. Once membership evidence is sufficient for a construction
test, return to those dependencies rather than optimizing these two labels
indefinitely. The ultimate outcome remains algorithmically generated browsing
paths, not a classifier benchmark or manually supplied category list.

## Reproduction and preservation

All 362 scores and rendered token inputs are preserved in
[run/scores.json](./TCC03/run/scores.json). The offline replay is byte-identical,
including the runner snapshot, with matching model/source hashes, packages
and native checks. Full originals and masks retain their source records exactly.

Compared with TCC02, only row10 has small score differences, at most
**0.000000563**, with unchanged rendered tokens. Its batch padding changes
when additional records are present. That is a plausible numerical explanation,
not a tested cause; both analysis conditions use the same TCC03 scores to
avoid depending on it. No relevant ordering or decision changes.

The previous 72 regression tests remain passing. This run makes no additional
production code change. One CPU process, two Torch threads, **12.11 seconds**
inference and about **4.9 GiB** peak RSS; no paid resource or frontier call.
GDC09, all earlier results and the browser remain unchanged. No review-tool
packaging before wrap-up.

Use the TCC02 reproduction command with input
`sse_multivector/navigation-research-v1/TCC03/inputs.json` and a new output
directory. Model revision, native source and all runtime settings are identical;
[run/config.json](./TCC03/run/config.json) records them. To reproduce the audit,
group the saved scores by category and note, take the maximum over the frozen
control rows or all rows, retain every attaining row, and compare all supported
notes with all unsupported notes from the frozen judgment file. No threshold
fitting is part of this calculation.
