# Decisions from category scores

The next candidate should be one shared score cutoff, learned once from the
existing development judgments and then frozen for a different-note,
different-category test. A probability-calibration subsystem is not presently
justified. The literature offers useful alternatives, but their extra inputs
and transfer assumptions must not be mistaken for solved membership.

This decision follows a new calculation on the saved TCC03 scores, not a new
model run: a shared cutoff can retain **18 of 19 supported assignments while
admitting 2 of 15 unsupported assignments**. The native 0.5 rule retains the
same 19 supported assignments but admits 12 unsupported ones. The former is
not a validated operating point; it shows that useful imperfect decisions are
possible in the observed data. Perfect separation is not required.

## Capability and inputs

The required output is a set of notes for a proposed category, with traceable
support in their masks. Categories may overlap. A note can belong to several
categories, and no fixed category prevalence or number of memberships is known.
New categories must not silently require a person to calibrate each one.

The current input to GLiClass is one saved subject description and one category
string. The classifier does not see the full note or mask. TCC03 scores all
existing descriptions of each note independently and assigns the note their
maximum score. The native classifier, weights, rendering and score semantics
are documented in [TCC01](./NATIVE-CATEGORY-MEMBERSHIP.md). The change from masks
to descriptions remains a representation assumption, not an interchangeable
input format.

This is a membership component for a possible construction method: propose
categories from repeated grounded descriptions, recover their relevant notes,
and separately establish useful semantic refinements between categories.
Neither a good membership cutoff nor accidental inclusion of one predicted
note set inside another establishes a meaningful parent–child relationship.

## Existing scores: what a shared cutoff can do

The calculation uses every expanded note maximum and every frozen full-note
judgment in [TCC03](./TCC03/audit.json). There are 40 note/category pairs from
20 notes: 19 supported, 15 unsupported and six scope-unresolved pairs. These
are correlated diagnostic observations, not independent population samples.

For the rule `score >= cutoff`, enumerate every change in the admitted set,
including admitting everything and nothing. There are 39 evaluated cutoffs,
38 distinct admitted sets and 33 distinct judged confusion-count combinations.
Score ties explain why
some counts cannot occur. A result is dominated if another cutoff retains at
least as many supported assignments and admits no more unsupported ones, with
at least one strict improvement.

The four nondominated judged tradeoffs are:

| Relevant assignments retained | Relevant assignments missed | Irrelevant assignments admitted | Irrelevant assignments rejected |
| ---: | ---: | ---: | ---: |
| 14 | 5 | 0 | 15 |
| 15 | 4 | 1 | 14 |
| 18 | 1 | 2 | 13 |
| 19 | 0 | 6 | 9 |

The native 0.5 result is **19 retained, zero missed, 12 incorrectly admitted,
three correctly rejected**. It is dominated even without allowing a missed
positive. Thus different score levels across Coffee and Morning greetings
do not by themselves justify a complex label-specific decision mechanism.

The 18-retained, two-incorrect result occurs throughout:

```text
0.9968927054312497 < cutoff <= 0.9970136067594879
```

Coffee contributes ten correct admissions, one miss and no incorrect admissions.
Morning greetings contributes eight correct admissions, no misses and two
incorrect admissions. Three unresolved pairs are admitted: Coffee/N005 and
Morning greetings/N018 and N052. They are not converted into correct decisions.

At the no-incorrect-admission end, Coffee loses N004, N038, N043, N045 and
N052. At the all-supported-retained end, Morning greetings incorrectly includes
N031, N035, N036, N038, N043 and N080. The complete states, exact scores,
attaining rows and unresolved admissions are in
[the retrospective calculation](./category-decision-tradeoffs.json).

### The actual tradeoff is not abstract

The one missed Coffee note at the 18-retained operating interval is N004:

> Weird #coffeechain today
> Rave at a coffee shop lol https://video.nostr.build/252e03e0d852e21d29e875ca7e1f381ad5559b8eee53b4a683babcb688b946ed.mp4

Its highest Coffee score is **0.9856252260105455**, from row0, “An unusual
coffee-themed social-media post,” supported by ⟦Weird⟧ ⟦#coffeechain⟧.
Its unambiguous cafe witness is row784, “Amusement at a rave taking place at a
coffee shop,” mask ⟦Rave at a coffee shop lol⟧, score **0.928681**.
Both fall below that operating interval. This is a real retrieval cost under
the frozen Coffee scope, not a reason to redefine the category after scoring.

One incorrectly admitted greeting is N043, row479, score
**0.9989441931227349**. Its description is “Incorporating movement into a morning
through coffee-fetching, stretching, and bowing.” The complete note and mask:

> Beyond ⟦9am⟧. Hazy sunlight on dusty desk. First tasks done, first minutes written, first things postponed. ⟦Fetching coffee⟧ as a ritual of motion, as well as doing some clumsy ⟦stretching⟧ and ⟦bowing⟧ to fight the physical and mental rust, to counter the effects of being stuck in the same position for too long.

The other is N080, row552, score **0.9987150164748367**. Its description is
“A beautiful morning with a stunning sunrise over a frosty garden.” The full
note with that mask is:

> Wednesday, 20th November 2024 - Cherries
>
> Wow what a ⟦beautiful morning⟧. ⟦Stunning sunrise over a frosty garden⟧. That got me out of bed - plus the need for tea and a wee. Yes and in that order.
>
> Our chickens are laying an egg a day. Having four hens that is a lot of eggs. My guests had scrambled eggs for breakfast and I soft boiled nine eggs for my lunch over the next few days. The clutch of eggs is receding. Michael Mosley said that a boiled egg is a good alternative to a packet of crisps!!!! Can't quite see the similarity but I have plenty of crisp substitutes in the fridge.
>
> The new audio book I had was like listening to a load of fluff. Total meaningless drivel. I gave up and have started a new murder mystery which is much more entertaining. I needed it while I was printing the last of our Christmas cards.
>
> Tim came home from Brussels with a gift of a bottle of gin, a bottle of Kreik and a bar of dark chocolate. Week 3 Day 3 I have chosen fruit for Kalie Graves challenge. My bottle of Kreik is cherry flavoured.
> -
> -
> -
> #kgaweekday #katesconnectedpostcardproject #apaintingaday #katerundell #artblog #dailyart #instaart #instaartist #watercolour #artoninstagram #artofinstagram #painting #watercolourpainting #blogger #dailyblogger #winsorandnewton #instadaily #danielsmithwatercolors https://nostrcheck.me/media/18d26089c0617d1b68bd08dfef065cf5eb5316a97eee1c0014d079ed3a6bc815/654867f61c247a385f166f7ba177be4382829feb6c77bfb73131fd7dfa849ce5.webp

These two notes describe mornings rather than greet their audience. Their
association with greetings is understandable, but it is not support for the
supplied category. Conversely, combining every morning activity under a
different broad category might be legitimate; that does not make these
Morning greetings assignments correct.

## Literature and task fit

### Shared score cutoff

Al-Otaibi, Flach and Kull distinguish a global score cutoff from per-label
cutoffs, fixed-count ranking and prevalence-matching rules. Their SCut method
chooses a cutoff against a loss on labeled validation data; the global version
shares it across labels. PCut instead uses training prevalence, and RCut fixes
the number of labels returned. Their work concerns supervised multi-label
classification, not transfer to newly generated categories.[^1]

The global SCut mechanism matches the immediate decision problem without
assuming exclusive labels, a fixed membership count or probability calibration.
Research judgments supply development supervision once; the same numeric rule
can then be applied to a new category without new annotations. Whether its
accuracy transfers is exactly the next empirical question, not a literature
guarantee. This is the simplest presently justified candidate.

### Probability calibration

Guo et al. fit temperature scaling using a labeled validation set. Their
multiclass transformation rescales logits and leaves the predicted argmax
unchanged while changing confidence. It was evaluated on image and document
classification models, not independent GLiClass category scores or maxima over
multiple subject descriptions.[^2]

For our independent binary scores, the analogous positive-temperature transform
is `sigmoid(logit / T)`. At cutoff 0.5, it preserves every decision because it
preserves the sign of the logit. Likewise, a single increasing transformation
with a new common cutoff cannot change the attainable shared-cutoff tradeoffs.
These are mathematical consequences, not measured claims about a calibration
implementation. There is no reason to run temperature scaling merely to make
the numbers look less extreme.

### Supervised multi-label calibration

Feng, Pratapa and Mortensen's CASENT predicts entity types with T5 and transforms
sequence scores using a logistic calibration model. It includes empty-input
type bias and frequency-based parameter sharing, fitted on labeled development
data. The main task has a predefined inventory of 10,331 overlapping types.
Crucially, Table 3's zero-shot cross-domain results use no calibration; those
datasets use single-label decisions. The improved recalibration results use
each target dataset's development labels.[^3]

CASENT is evidence that calibrated multi-label scoring is feasible. It is not
evidence that a threshold transfers annotation-free to arbitrary new categories.
Its conditional sequence likelihoods also differ from the native sigmoid
scores currently tested. Importing its bias features or frequency sharing would
add assumptions and supervision that the simpler cutoff does not need.

### Per-category active threshold selection

Chausson et al. score tweets against independent natural-language claims with
BART-MNLI. A human repeatedly judges a document near the estimated threshold;
probabilistic bisection updates the estimate. Their case study averaged
21.3 ± 8.4 annotations per claim. This is explicitly few-shot rather than
zero-shot and needs threshold tuning for each new claim. The uniform initial
distribution concerns threshold location, not balanced claim prevalence.[^4]

This is the closest direct precedent for overlapping natural-language targets
and limited annotation. But requiring per-category human judgments would be a
different deployed construction mechanism. It can serve as a research reference
for what label-specific adjustment could achieve, not a silently assumed final
solution. A concentrated threshold posterior is also not an independently
validated error guarantee.

### Unlabeled background thresholds

Bongiovanni et al. score a taxonomy label against roughly 1,000 random Wikipedia
articles presumed irrelevant, fit a background distribution and take its 95th
percentile. That label-specific threshold controls upward score propagation
in an existing taxonomy. Their three evaluations assign a single branch per
document; they do not independently establish overlapping membership accuracy
for an arbitrary new category.[^5]

The idea directly addresses differing category score levels, but its background
assumption matters. Random documents need not be irrelevant to a broad category.
Wikipedia articles also do not reproduce maxima over 3–34 generated descriptions
of short social posts. A high percentile measures unusualness relative to that
background, not semantic correctness. Using the mixed target corpus instead
would risk retaining a fixed tail of genuinely common categories. This is a
plausible later alternative only with a justified background construction.

### Contextual and batch calibration

Zhou et al. study label-token bias in prompted PaLM 2 and CLIP classification.
Batch Calibration subtracts the mean score vector over a batch before selecting
the highest-scoring label. The paper also compares content-free calibration,
random-token domain calibration and Gaussian-mixture prototypical calibration.
Its formal prediction problem is an argmax over a supplied label set.[^6]

That is not the current independent multi-label membership problem. Subtracting
the mean score for a category here would mix model bias with how frequently
that subject actually occurs. It might be adapted and tested, but the paper's
results do not justify treating the resulting boundary as membership truth.
Neither a histogram valley nor a largest score gap alone supplies that truth.

## Mask support remains a separate check

A correct note admission is not automatically a correctly selected mask. N038
illustrates the difference. Its full original is:

> Awwww yeah. Baby Got Back playing in the coffee shop. 😂 #musicstr #coffeechain

The highest Coffee score, **0.9970136067594879**, comes from row382, “Coffee and
a coffee-themed social-media posting chain,” mask ⟦#coffeechain⟧. The explicit
venue description, row825, “Music playing in a coffee shop,” scores **0.971751**,
with fragments ⟦playing⟧ ⟦coffee shop⟧ ⟦music⟧. A cutoff in the 18-retained
interval admits the note but not that venue witness.

That does not make the note admission incorrect. It prevents interpreting it
as demonstrated recognition of the cafe passage. The next test must separately
report note membership, the actually admitted masks and genuinely supporting
evidence. A human inspection must not silently replace the mask selected by the
rule. Complete masks/originals remain in [TCC03 inputs](./TCC03/inputs.json).

The decision must be evaluated at the same aggregation level as its proposed
use. Taking a maximum over additional descriptions can only increase the score,
including for irrelevant notes. A description-level reference distribution or
TCC01's selected individual witnesses cannot be substituted for complete-note
maxima without testing that change.

## Next controlled test

Freeze a global development rule before new scores are revealed:

1. Use the 34 judged TCC03 note/category pairs, excluding the six unresolved
   pairs from the selection objective.
2. Give each incorrect admission and missed supported assignment equal cost.
   Minimize their sum over all shared-cutoff intervals. This is a diagnostic
   convention, not a settled product tradeoff or claim about deployment prevalence.
3. Choose the midpoint of the best interval; if separate intervals tie, use
   the one with the highest midpoint. The present optimum is the interval above,
   yielding **0.9969531560953688**.
4. Freeze that number, the model, single-category input format and maximum over
   all existing descriptions. Compare against the unchanged native 0.5 rule.

This freezes an experimental candidate, not a deployed rule. The retrospective
18/19 and 2/15 counts are its development fit and must not be reported as test
performance. A global increasing recalibration with a cutoff would still be
another shared cutoff; extra machinery does not fix its observed ordering.

The falsifiable hypothesis is that the frozen cutoff reduces the total number
of incorrect note/category decisions relative to 0.5 on a different-note,
different-category challenge set. Report errors and retained relevant notes
for every category, not only the pooled result. Report mask support separately.
Emptying a destination or rejecting most of its relevant notes does not count
as successful transfer merely because the total error falls. The next plan
must preserve that retrieval safeguard alongside its error comparison.

Before inference, select a small set of different original notes and category
strings from existing construction candidates, read their complete source
evidence, and freeze supported, unsupported and unresolved judgments. Include
related nonmembers as well as positives; unrelated easy negatives alone would
not exercise the observed morning/greeting confusion. Use all existing
descriptions of each selected note, not a favorable chosen witness. Do not
claim the notes are generally unseen if other research already inspected them.

The competing explanations and consequences are:

- **A broadly reusable operating point exists:** fewer incorrect admissions
  with an acceptable, explicitly displayed retrieval cost would justify a
  construction-facing trial. Do not keep optimizing Coffee and greetings.
- **Category score levels do not transfer:** the fixed rule misses a category's
  relevant notes even though their scores remain usefully ordered above its
  nonmembers. This would justify considering label-relative decisions, not
  immediately changing the semantic encoder.
- **Ordering itself fails:** unsupported notes outrank supported notes under
  the same complete-note aggregation within a category. No category-specific
  scalar cutoff can repair those pairs. An individual-witness inversion alone
  does not establish this note-level failure.
- **Input evidence or scope is faulty:** the subjects/masks do not support the
  intended decisions, or the category boundary remains unresolved. Separate
  that issue from classifier errors rather than recoding the case to improve
  results.

Would either outcome change the next decision? Yes: useful transfer supports
using this inexpensive component in category construction; failure directs
inspection toward score levels, ordering or grounding before adding anything.
Changing notes and categories together tests the needed combined transfer but
does not isolate which change caused a failure. Any subsequent causal claim
would need a distinguishing control.

This test will not establish the category-proposal method, meaningful parent
relations, broad deployment accuracy or a uniquely correct taxonomy. Its value
is resolving whether a simple shared membership decision is already usable
enough to test those construction dependencies. No new inference was performed
for this literature review and retrospective calculation; the next challenge
inputs and judgments have not yet been selected or frozen.

## Reproduction and preservation

Source hashes and all enumerated states are saved in
[category-decision-tradeoffs.json](./category-decision-tradeoffs.json).
Reproduce them by reading `TCC03/audit.json`, using each category's
`all.maxima`, checking its judgments against `TCC03/judgments.json`, then applying
`score >= cutoff` at every distinct score plus 0 and 1. Keep unresolved admissions
separate. Retain nondominated counts using supported admissions and incorrect
admissions as the two objectives. No source record, score or judgment is edited.

The main calculation and an independent read-only audit agree on all four
tradeoffs and their concrete errors. The literature audit was also independently
challenged for supervision and task fit. GDC09, the browser, earlier model
artifacts and the pending HiT files remain unchanged. No review-tool packaging
occurs before wrap-up.

## Sources

[^1]: Reem Al-Otaibi, Peter Flach and Meelis Kull. [Multi-label Classification: A Comparative Study on Threshold Selection Methods](https://dmip.webs.upv.es/LMCE2014/Papers/lmce2014_submission_11.pdf). 2014, §§3–4. Method definitions and supervision requirements; no new-category transfer result is assumed.
[^2]: Chuan Guo, Geoff Pleiss, Yu Sun and Kilian Q. Weinberger. [On Calibration of Modern Neural Networks](https://proceedings.mlr.press/v70/guo17a/guo17a.pdf). ICML 2017, §4.2. Positive-temperature rescaling, validation fitting and unchanged class predictions.
[^3]: Yanlin Feng, Adithya Pratapa and David Mortensen. [Calibrated Seq2seq Models for Efficient and Generalizable Ultra-fine Entity Typing](https://aclanthology.org/2023.findings-emnlp.1040.pdf). Findings of EMNLP 2023, §§3.1–3.4, 5.2 and Table 3. Native overlapping-label task, calibration inputs and the distinction between zero-shot and target-development recalibration results.
[^4]: Sandrine Chausson, Marion Fourcade, David J. Harding, Björn Ross and Grégory Renard. [The Insight-Inference Loop: Efficient Text Classification via Natural Language Inference and Threshold-Tuning](https://journals.sagepub.com/doi/10.1177/00491241251326819). Sociological Methods & Research, online 2025; journal page identifies the 2026 issue. Sections “Obtaining Entailment Scores” and “Finding Thresholds by Annotating a Small Sample of Data.”
[^5]: Lorenzo Bongiovanni, Luca Bruno, Fabrizio Dominici and Giuseppe Rizzo. [Zero-Shot Taxonomy Mapping for Document Classification](https://www.starlight-h2020.eu/sites/default/files/2024-07/Zero-Shot%20Taxonomy%20Mapping%20for%20Document%20Classification.pdf). SAC 2023, §§3, 5.1–5.2. Background-score thresholds and their role in an already supplied taxonomy.
[^6]: Han Zhou et al. [Batch Calibration: Rethinking Calibration for In-Context Learning and Prompt Engineering](https://arxiv.org/html/2309.17249v3). ICLR 2024; arXiv revision December 2024, §§3–4. Actual input/output setting and score transformations; not evidence of independent multi-label threshold transfer.
