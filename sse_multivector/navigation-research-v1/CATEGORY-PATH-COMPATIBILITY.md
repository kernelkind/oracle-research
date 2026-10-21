# Category membership and browsing paths

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

CPC01 connects the previously tested category classifier to the existing
construction rules. It recovers some relevant notes, but both fixed score
cutoffs remove all three clearly meaningful parent–child paths in the tested
family. This is evidence against the unchanged combination—not against the
existence of those semantic relationships, or against every learned matcher.

No GDC09 category, mask, vector, hierarchy or browser changed. The experiment
does not generate a new taxonomy or claim that this family is representative.

## What changed

The [pre-run plan](CATEGORY-PATH-COMPATIBILITY.md#cpc01-study-design) fixes 12 source-derived candidate strings:
Bread, Chicken and Salt, plus every CAP04 adjacent phrase containing one of
those words. All 945 saved descriptions from all 100 notes remain unchanged.
The strings include useful subjects, incomplete phrases and possible duplicates;
none is silently repaired or removed after scoring.

GLiClass receives one saved description and one category string per request.
It does not see the original note or the other descriptions. Each note's score
for a category is the highest of its description scores. There are 11,340
requests and 1,200 note/category maxima; every tied attaining description is
preserved. These are native classifier outputs, not calibrated probabilities
that a category assignment is correct.

Three membership conditions feed the same two existing relation rules:

| Condition | When a note belongs |
| --- | --- |
| Literal | A saved description contains the word or adjacent phrase |
| Native | Its maximum score is at least 0.5 |
| Development | Its maximum score is at least 0.9481359422711596 |

The development cutoff comes from the prior combined TCC03/TCC04 tradeoff.
It is not selected from CPC01 and is not a clean validation setting. Neither
cutoff is retuned here.

The `note_subset` rule requires every child note to belong to its parent, with
at least one additional parent note. `descriptor_extension` also requires the
parent's words to be a proper subset of the child's words. Both remove
transitive edges. These are implemented construction rules, not definitions of
semantic correctness. Equal note sets remove an edge but do not remove either
candidate. There is no upward propagation of child memberships.

## Membership results

Before the run, both reviewers read the complete source notes. The
frozen judgments (`./CPC01-JUDGMENTS.json`) cover six complete categories across
all 100 notes. They contain 31 supported, 557 unsupported and 12 unresolved
note/category pairs. Unresolved cases include unspecified egg species and
the scope of Bread for some composite dishes; they are not counted as errors
or silently resolved from model scores. These are researcher judgments, not
user approvals.

| Condition | Supported pairs admitted | Supported pairs missed | Unsupported pairs admitted | Unresolved pairs admitted |
| --- | ---: | ---: | ---: | ---: |
| Literal | 26 | 5 | 0 | 0 |
| Native | 31 | 0 | 162 | 3 |
| Development | 27 | 4 | 8 | 2 |

The complete audit (`./CPC01/audit.json`) lists every error, retained assignment,
unresolved admission, ordering inversion and resulting edge. Counts alone
overstate grounded recognition: the native Bread assignment for N071 comes
only from the description “Growing Nostr,” not from its actual tortilla
descriptions. The note is relevant, but the accepted witness is not.

At the development cutoff, the only new supported memberships are Chicken/N080
and Chicken/N100. Both have faithful supporting descriptions. N100's maximum
comes from a description with an incorrect myoglobin attachment, but a separate
clean water-and-seeds description independently clears the cutoff. The valid
Chicken assignment therefore does not depend on that extraction error.

Native scoring also recognizes the bagel and paratha notes as Bread through
valid witnesses. It admits many unrelated notes alongside them. Those genuine
semantic gains should not be erased from the account merely because the
operating rule performs poorly overall.

## What happens to the three clear paths

These are meaningful examples in the existing family, not a prescribed complete
taxonomy. All three paths exist under literal membership. All three disappear
under both scored conditions.

At the development cutoff, the exact blockers are:

| Path | What prevents containment | Interpretation |
| --- | --- | --- |
| Bread → Sourdough bread | The child adds N024, N029, N045, N069, N081 and N100, which are not in Bread | Incorrect child memberships disconnect the path |
| Chicken → Chicken stock | The child adds N029, which is not in Chicken | One incorrect child membership disconnects the path |
| Salt → Sea salt | Sea salt correctly retains N046, but Salt misses it | One incorrect parent omission disconnects the path |

N100 is also incorrectly admitted to Chicken stock. It does **not** break
Chicken → Chicken stock: the note correctly belongs to Chicken. Separating
the membership error from the actual edge blocker matters.

For Salt/Sea salt, the same faithful description, “Bagels topped with sea salt
flakes,” scores 0.761452690 for Salt and 0.999215152 for Sea salt. The original
mask selects `bagels` and `sea salt flakes`. This is not evidence that sea salt
lacks a relationship to salt. It is evidence that independent thresholding
followed by exact containment can lose a valid relation. This particular
regression was already predicted before CPC01; the new evidence includes the
child score and the completed construction.

N029 illustrates the other direction. Its description “The Rogue Batch,”
grounded only in that hashtag/name, scores 0.966487678 for Chicken stock and
0.971722524 for Sourdough bread. The readable post establishes neither topic.
The classifier's acceptance makes a category membership wrong; the containment
rule then turns that local error into loss of a broader browsing path.

The [source evidence](./CPC01/SOURCE-EVIDENCE.md) presents these descriptions,
scores and masks overlaid on the complete originals. It also includes every
development Sourdough false admission, the N100 attachment distinction, both
Chicken recoveries, and the genuine and unsupported Bread witnesses.

## The complete resulting choices

No awkward root, duplicate or surviving incomplete phrase is hidden.

Literal membership gives three roots—Bread, Chicken and Salt—and nine immediate
edges under either rule:

```text
Bread
├─ bread in
└─ sourdough bread
Chicken
├─ a chicken
├─ chicken stock
├─ make chicken
├─ making chicken
└─ of chicken
Salt
├─ salt and
└─ sea salt
```

Only three of these are already established useful refinements. `bread in`
and `salt and` lack their complements. The four Chicken children containing
stock/make/making/of have the same two-note set; grammatical differences are
not four established semantic distinctions.

At native 0.5, `descriptor_extension` retains only Chicken → a chicken. Every
other candidate is a root: eleven roots total. The less restrictive `note_subset`
rule instead retains these immediate edges:

```text
of chicken → chicken → a chicken
make chicken → making chicken
sourdough bread → bread
```

Its eight roots are `of chicken`, `make chicken`, `sourdough bread`, `chicken stock`,
`sea salt`, `salt and`, `bread in` and `salt`. The Sourdough → Bread edge reverses
the meaningful relationship. Different erroneous note sets can satisfy numerical
containment without supporting the corresponding semantic direction.

At the development cutoff, `descriptor_extension` retains only:

```text
Chicken → a chicken
Bread → bread in
Salt → salt and
```

`note_subset` adds `of chicken → a chicken`. Both have nine roots: Chicken, Bread,
Salt, Chicken stock, Sea salt, Sourdough bread, `of chicken`, `make chicken` and
`making chicken`. The last two have identical seven-note sets but remain separate
roots. Their notes include unspecified cooking and chicken housing, so equality
does not itself establish a clean preparation category.

Dropping six edges is not a successful removal of six low-value choices.
The candidates remain, useful paths disappear, and more choices move to the
root. A smaller edge count is not the navigation objective.

## What this does and does not establish

The unchanged classifier-plus-containment combination is not an improved
construction method for this family. It leaves malformed candidates and
duplicates unresolved and magnifies membership mistakes into path failures.
This does not establish that a classifier is incapable of useful discrimination.

Chicken and all three complete fine categories have no judged
supported-versus-unsupported note-order inversions in this run. Bread has 34
such inversions and Salt has one: N029's unsupported Salt score exceeds N046's
supported score. A monotone cutoff cannot fix these wrong orderings. Conversely,
it would be false to claim that all six categories have wrong orderings.

All six supported fine-category memberships already occur literally. Their
good ordering is promising discrimination, not demonstrated new fine-category
recall or an independently validated category-specific cutoff. No calibration
sweep follows from this result.

The two development recoveries also have descriptions containing `chickens`.
The distinguishing control, CPC02 below, tests whether ordinary word-form
matching recovers the same gains without the classifier's incorrect additions.

The construction-level question remains how to combine evidence for a
meaningful refinement with imperfect note memberships. A valid semantic
relationship can exist when independently predicted memberships violate
containment, as Salt and Sea salt demonstrate here.
Automatically propagating children upward would restore containment while
also spreading false child assignments; it is not an established repair.

## CPC02 — are the observed gains already available without the classifier?

The [control plan](CATEGORY-PATH-COMPATIBILITY.md#cpc02-study-design) was written after CPC01 and frozen before
CPC02 ran. Keep all 12 candidates, 945 descriptions, 100 notes, judgments and
both relation rules. Change only membership matching: apply the cached NLTK
3.9.2 English Snowball stemmer to each candidate token and description token,
then require the resulting sequence to occur contiguously. Original labels,
relation features and source positions remain intact. No category-specific
exceptions, new candidate selection, score cutoff or learned inference enter
this control. Stemming normalizes word forms; it does not establish senses or
semantic equivalence.[^4]

| Condition | Supported admitted | Supported missed | Unsupported admitted | Clear existing paths retained |
| --- | ---: | ---: | ---: | ---: |
| CPC01 literal | 26 | 5 | 0 | 3 |
| CPC01 development | 27 | 4 | 8 | 0 |
| CPC02 word forms | 28 | 3 | 0 | 3 |

CPC02 admits none of the 12 unresolved pairs. The only new note memberships
are Chicken/N080 and Chicken/N100, precisely the development classifier's two
supported additions. No literal membership is lost. Every other candidate's
note set remains unchanged; both complete relation outputs and all equal-note
classes remain exactly the literal baseline's. This is not a new improved
taxonomy: the same incomplete choices and duplicate children remain.

Newly matched description rows are:

| Candidate | Newly matched description rows | New notes |
| --- | --- | --- |
| Chicken | 27, 59, 209, 531, 686, 728, 873 | N080, N100 |
| make chicken | 187, 349, 875, 935 | None |
| making chicken | 439, 548, 629 | None |

The Chicken matches use `chickens`; the preparation matches equate `make` and
`making`. The latter only add evidence inside the same existing two notes.
Chicken also gains plural occurrences inside already-matched rows 230, 439
and 712. Thus there are 17 added occurrences (`./CPC02/added-occurrences.json`)
across 16 distinct source rows, not just the 14 added candidate/row memberships
in the table. Nothing is removed. All changed masks and complete originals
were independently inspected.
The audit (`./CPC02/audit.json`) retains each changed description and all six
category judgments. `./CPC02/result.json` retains every raw and
normalized token match, exact positions, membership difference and edge.

N080 is recovered through row 59, “The author's chickens collectively lay one
egg a day,” whose mask is `Our chickens` plus `laying an egg a day`. N100 is
recovered through the clean row 686 water-and-seeds description, among others.
The word `collectively` in row 59 may misstate the original egg-count scope;
Chicken membership needs only its explicit chicken evidence, not that quantity
interpretation. This is not a claim that every matched description is flawless.
The classifier also recognized hens in N080, but that additional inference was
not needed to reach the note: another description explicitly says chickens.
The bad N100 attachment remains frozen, yet is unnecessary for the recovered
membership. The control does not credit that bad input as its success.

This answers the component-necessity question for these gains: retain word-form
matching as a stronger reference before claiming future semantic recovery.
Do not retain the classifier merely because it beats exact spelling here.
This does not reject its genuine native bagel/paratha recognition or establish
that normalization can replace semantic matching generally. N046, N071 and
N078 remain absent from Bread: bagels, tortillas and paratha are not inflections
of `bread`.

The next investigation must return to construction: selecting complete,
meaningfully different categories and establishing their broader/narrower
relationships without making independently predicted note sets the sole
evidence. Do not turn this result into a normalizer comparison, a new threshold
sweep or an assumption that shared spelling establishes every parent. Any
proposed semantic-relation mechanism must be checked against the prior lexical,
grammar and learned-relation failures before another implementation.

## Literature and fit

Sanderson and Croft use term/document inclusion to propose browsing hierarchies,
including topical aspects. Their evidence supports treating document inclusion
as a proposal mechanism, not equating every numerical subset with a valid
semantic refinement. Their relaxed conditional-frequency rule and query-focused
collections differ from this exact-containment experiment.[^1]

AutoPhrase separates recurring sequences from interpretable phrase quality.
That distinction directly matters for `bread in` and `salt and`; changing
membership does not complete either meaning. Its distant supervision,
statistical features and much larger training corpora do not establish that
it will solve this small collection of generated descriptions.[^2]

Woods distinguishes morphology, structured phrases and semantic subsumption
in conceptual indexing. This supports testing the observed plural mismatch
separately from broader knowledge or parent relationships. Its retrieval
results are not a validation of every path in this note-discovery task.[^3]

## Verification and reproduction

Eight new production-path tests first failed because the runner did not exist,
then passed. All 42 relevant regression tests pass. Preparation validates source
tokens, exact casefolded occurrences and saved adjacent-pattern provenance.
Analysis validates the complete native score matrix, maxima/ties, fixed cutoffs,
equal/empty/single-note cases and reuse of both existing relation rules.

Independent recomputation verifies all 11,340 scores in the matrix, 1,200 maxima
and ties, memberships, roots and immediate/transitive edges. The frozen inputs
and pre-score judgments remain unchanged. Deterministic preparation and analysis
replay byte-for-byte, including source snapshots and configurations.

All 435 overlapping TCC04 requests retain identical records, rendered inputs
and token IDs. Of their scores, 313 are exactly equal; the largest difference is
0.000001082672. There are zero decision changes at either CPC01 cutoff or the
older TCC04 cutoff. Different batch composition is a plausible numerical
explanation, not an isolated cause. This is not claimed as an exact neural
inference replay.

The cached 186,545,922-parameter GLiClass checkpoint runs on one CPU process with
two Torch threads and batch size four. Inference takes 398.88 seconds; peak RSS
is 5,197,376 KiB. No paid service, GPU, new download or parallel model process
was used. Model/source revisions, native smoke check and package hashes are in
`./CPC01/run/config.json`.

From the repository root, deterministic replay uses fresh output directories:

```sh
python3 sse_multivector/category_path_compatibility.py prepare \
  --patterns sse_multivector/navigation-research-v1/CAP04/result.json \
  --anchors bread chicken salt --output /tmp/cpc01-replay/prepared

python3 sse_multivector/category_path_compatibility.py analyze \
  --prepared sse_multivector/navigation-research-v1/CPC01/prepared \
  --scores sse_multivector/navigation-research-v1/CPC01/run/scores.json \
  --cutoffs 0.5 0.9481359422711596 --output /tmp/cpc01-replay/analysis
```

The analysis result (`./CPC01/analysis/result.json`) preserves all twelve candidate
memberships and relation outputs, including candidates without a certified
meaning. Raw scores (`./CPC01/run/scores.json`), unchanged inputs (`./CPC01/prepared/inputs.json`),
candidate occurrences (`./CPC01/prepared/candidates.json`) and the
pre-score manifest (`./CPC01/prescore-manifest.json`) remain available separately.

CPC02's five new production-path tests also failed first for its absent module,
then passed. The combined 47-test regression suite passes. The complete
deterministic control replay is byte-identical, including configurations,
source snapshots and NLTK package/source records. The control uses only the
cached word-form implementation; no model or network request is made.

```sh
/tmp/oracle-nli-probe-venv/bin/python sse_multivector/category_morphology_control.py \
  --patterns sse_multivector/navigation-research-v1/CAP04/result.json \
  --prepared sse_multivector/navigation-research-v1/CPC01/prepared \
  --output /tmp/cpc02-replay
```

Use a fresh output directory. The environment has NLTK 3.9.2; system Python
does not. The pre-control manifest (`./CPC02-precontrol-manifest.json`) freezes
the plan, judgments, source inputs, candidates, runner and stemmer source.
`./CPC02/config.json` records the copied code/package hashes.

## Sources

[^1]: Sanderson and Croft (1999), [Deriving concept hierarchies from text](https://ciir.cs.umass.edu/pubfiles/ir-156.pdf), sections 2–4.
[^2]: Shang et al. (2017), [Automated Phrase Mining from Massive Text Corpora](https://arxiv.org/html/1702.04457), sections 2–4.
[^3]: Woods (2000), [Conceptual Indexing](https://cdn.aaai.org/AAAI/2000/AAAI00-215.pdf), conceptual indexing, subsumption and retrieval sections.
[^4]: NLTK 3.9.2, [English Snowball stemmer](https://www.nltk.org/api/nltk.stem.snowball.html#nltk.stem.snowball.EnglishStemmer), rule-based suffix processing and fixed implementation.

## CPC01 study design

### Question

Can the useful but imperfect membership mechanism from TCC03/TCC04 improve
access through existing source-derived category candidates when it is connected
to the existing relation rules? This is a construction-compatibility experiment,
not another search for a score cutoff and not a complete hierarchy solution.

The original GDC09 hierarchy, masks, descriptions and all previous experiments
remain unchanged. No browser is packaged during this investigation.

### Frozen candidate family

Use the three existing TCC04 source words `bread`, `chicken` and `salt`, plus
**every** CAP04 adjacent two-word pattern containing any of those words:

| Source word | All adjacent patterns |
| --- | --- |
| bread | bread in; sourdough bread |
| chicken | a chicken; chicken stock; make chicken; making chicken; of chicken |
| salt | salt and; sea salt |

These are 12 candidate strings, not 12 approved subjects. CAP04's saved token
positions establish their order. Verify that every recorded occurrence's
casefolded source span exactly equals the space-joined string. Preserve the
source rows and positions; do not fix grammar, choose more favorable wording,
or turn CAP02's unordered feature sets into invented phrases.

This is an intentionally bounded family around the preceding three membership
categories, not a representative estimate of all possible categories. It
contains recognizable refinements, incomplete phrases, and possible duplicates.
It excludes valid possibilities such as rosemary used in bread, which is not a
recurrent adjacent phrase. No membership score can recover an absent candidate.

### Inputs and conditions

Copy all 945 CAP04 input records, unchanged, covering all 100 GDC09 notes.
The native pinned GLiClass runner scores each saved subject description against
each of the 12 strings **separately**: 11,340 requests. The model sees neither
the whole original note nor other descriptions. Originals, masks and alias
identifiers remain in the evidence for evaluation.

For each note/category, retain the maximum over all its saved descriptions,
including every tied attaining row. Compare three conditions:

1. **Literal:** the source word or adjacent phrase occurs in a saved description.
2. **Native:** the complete-note maximum is at least 0.5.
3. **Development:** that maximum is at least 0.9481359422711596, the retrospective
   shared operating point in the frozen TCC03+TCC04 tradeoff record.

Both score cutoffs are fixed before this run. Do not choose a new cutoff,
category-specific cutoff, or accepted-note quota after seeing the results.
The native condition is important: unlike the higher operating point, it
retained the previously tested Bagel/Salt assignment. Both conditions reuse
development evidence and are not clean holdout estimates. The full 100-note
memberships and the new compound-category scores have not been measured by
this experiment before.

For every condition reuse `mask_description_hierarchy.description_relations`
unchanged. It returns both existing rules:

- `note_subset`: child notes are a proper subset of parent notes.
- `descriptor_extension`: the same note condition, plus the parent's token
  set is a proper subset of the child's token set.

Both rules remove transitive edges. Neither establishes semantic parenthood.
Preserve all candidates, roots, edges, empty and one-note destinations, and
equal-note-set groups in the output. Do not silently reapply recurrence after
scoring, discard awkward candidates, merge equivalent-looking labels, or add
child notes to parents. Equal note sets remove an edge under these rules; they
do **not** remove the category or its duplicate siblings.

### Hypothesis and predictions before scores

Hypothesis: replacing literal membership with one of these fixed semantic
conditions produces at least one additional source-supported reachable
destination or valid relation in this bounded family. Record every regression
and incorrect addition alongside that improvement. A component improvement
does not make the complete output a useful browser.

Positive opportunities include Bread notes expressed as bagels, tortillas or
paratha, and Chicken notes expressed as chickens or chicks. The three complete
child phrases already have literal support for their two known relevant notes;
do not portray retaining those notes as new recovery.

Three existing relations have a clear source-supported interpretation:
Bread → sourdough bread; Chicken → chicken stock; Salt → sea salt. They are
examples, not an exhaustive prescribed taxonomy. Accept other coherent
relations if their actual evidence supports the complete path.

One regression is already predicted for the development condition. Salt's
saved score for N046 is 0.761453772, below the fixed cutoff. N046 explicitly
lists sea-salt bagel toppings. If `sea salt` accepts that note, strict note
containment blocks Salt → sea salt. If it does not, the child loses relevant
content too. No new child score can preserve that route with N046 in this
condition. Its reappearance is not a novel finding.

The source audit also already establishes that `bread in`, `of chicken` and
`salt and` are incomplete expressions, not independently defined narrower
topics. Their scores cannot prove that a category generator understood them.
`a chicken` occurs inside descriptions of a chicken dish or chicken tractor,
not evidence for a whole-bird-only category. `make chicken` and `making chicken`
may describe a recognizable preparation activity; their source occurrences
continue with `stock`. Preserve possible useful interpretations rather than
predeclaring every non-noun phrase invalid.

### Competing explanations and discriminating observations

- **Useful membership transfers into useful access:** previously absent notes
  enter appropriate destinations through genuine source witnesses, and those
  destinations retain valid narrower choices. This warrants work on candidate
  selection and semantic relation evidence with membership as a component.
- **Literal grammatical distinctions were incidental:** complete note sets
  become equal or near-equal. Report the actual remaining roots and siblings;
  edge disappearance alone is not removal of low-value navigation choices.
- **Strict containment magnifies membership errors:** a supported child loses
  its appropriate parent because of one missing parent note or erroneous child
  addition. Identify that exact note and winning description/mask. Do not call
  the broken edge evidence that the subjects lack a broader/narrower relation.
- **Finite co-occurrence mimics semantic refinement:** a new strict subset link
  is not a recognizable narrowing when its complete masks and notes are read.
  This limits the relation rule, even if individual memberships are acceptable.
- **The category input is not a defined meaning:** an incomplete source fragment
  yields a score or note set. Keep this separate from failure to recognize a
  complete category. Do not repair the phrase after scoring.
- **The available evidence is defective:** the winning saved description adds
  meaning or the mask omits it. Distinguish original-note validity, description
  validity, and attaining-mask support rather than blaming the relation rule.

Would either outcome change the next decision? Yes. Source-supported access
improvements with retained paths justify testing a repeatable candidate-selection
step. If new memberships mainly cause broken paths, extra roots or unsupported
distinctions, revise the way semantic relation evidence and note membership are
combined; do not automatically fit another cutoff. Neither outcome establishes
all category generation, equivalent-category handling or parenthood solved.

### Evaluation and evidence

The main and independent reviewer have read all 100 original notes before this
run. The independent reviewer also inspected all 945 saved subject/mask records.
`CPC01-JUDGMENTS.json` freezes supported and unresolved note IDs for the six
complete topical categories. Other notes are unsupported by the readable text,
not proof that a food contains none of a particular ingredient. Unresolved
bread-family and unspecified-egg boundaries stay outside binary error counts.

After scoring inspect all admitted notes for the six complete categories, all
attaining source witnesses for additions/misses, every edge under both rules,
and the entire root menu. Audit the other six strings as possible meanings or
incomplete inputs; do not manufacture binary truth labels for undefined scopes.
Keep all raw scores, maxima, source texts, inline masks, decisions and source
hashes. Report selection, membership and relation failures separately.

### Literature and task fit

Sanderson and Croft construct browsing menus from terms and document inclusion,
allowing topical aspects as well as type relations. Their conditional-frequency
rule was relaxed to 0.8 through informal analysis; query-focused retrieved
collections helped limit ambiguity. That motivates testing extensional evidence,
not adopting their threshold or treating inclusion as semantic proof.[^cpc01-study-design-1]

AutoPhrase explicitly separates candidate sequences from phrase quality. It
requires interpretable semantic units rather than assuming recurrence suffices.
Its distant training, statistical features and POS-guided segmentation were
evaluated on much larger corpora than these saved descriptions. It supports
keeping category validity separate here; it does not justify deploying a new
phrase model without checking its fit.[^cpc01-study-design-2]

GLiClass's exact native inputs, training streams, model loading and transfer
limits are recorded in TCC01–TCC04. No new model-transfer claim is introduced.
Here the new assumption is compositional: that imperfect independent category
memberships remain useful when supplied to the existing relation rules.

### Resources and verification

Use only the already cached native checkpoint, CPU, one process and two Torch
threads. Prior peak RSS was about 4.91 GiB; no parallel model processes, GPU,
paid service or new download. Expect minutes rather than a long sweep.

Implement minimal production-path tests first for source-preserving preparation,
complete score-matrix validation, maxima, fixed thresholds, equality/empty cases
and unchanged relation construction. Independently audit the assembled artifact.
Replay the deterministic preparation/analysis and verify reused TCC04 scores
against their unchanged description/category requests. Keep all frozen prior
artifacts and the unrelated pending HiT files untouched.

[^cpc01-study-design-1]: Sanderson and Croft (1999), [Deriving concept hierarchies from text](https://ciir.cs.umass.edu/pubfiles/ir-156.pdf), sections 2–4.
[^cpc01-study-design-2]: Shang et al. (2017), [Automated Phrase Mining from Massive Text Corpora](https://arxiv.org/html/1702.04457), sections 2–4.

## CPC02 study design

CPC01's development condition recovers Chicken/N080 and Chicken/N100 from the
literal baseline. Both notes already have saved descriptions explicitly saying
`chickens`. This leaves a competing explanation: ordinary inflection handling,
not learned semantic generalization, is sufficient for the observed gains.

Before retaining the classifier as necessary for this construction family,
test that explanation directly. Keep CPC01's 12 candidate strings, IDs, source
records and both relation rules unchanged. Use NLTK 3.9.2's cached
`EnglishStemmer` to normalize each CAP04 token and each candidate token solely
for matching. A candidate matches when its normalized token sequence occurs
contiguously in a description. Note membership is still any matching description.
Preserve the actual source positions; do not claim normalized matches were
literal occurrences or rename the categories using stemmed words.

Hypothesis: this fixed normalization recovers both observed Chicken notes,
without adding unsupported notes to the six complete categories or losing
their literal supported memberships, and preserves the three clear existing
refinements. Evaluate all 100 notes and all 12 candidates, not only those two
positive examples. Keep CPC01's frozen source judgments, unresolved boundaries,
duplicates and incomplete-category limitations. No learned score or cutoff is
used in this control. There is no classifier retraining, download or new model.

Competing explanations:

- If the same gains follow from generic normalization and other memberships
  remain appropriate, the observed gains do not establish a need for the learned
  matcher in this family. Use the simpler control as the reference for future
  semantic-recovery claims rather than crediting elementary inflection again.
- If normalization fails to recover them or introduces other unsupported
  memberships, inspect those exact source matches. The classifier may provide
  a useful distinction here, but this does not establish broad transfer.
- Either method can leave missing broader knowledge: `bagels`, `tomato tortilla`
  and `Lacha Paratha` need not normalize to `bread`. Do not interpret their
  continued absence as failure of an inflection control or as solved membership.

Would either outcome change the next decision? Yes: it determines whether the
only demonstrated gains require the expensive component, or whether subsequent
work should start from a simpler reference. It does not decide category quality
or semantic parenthood, which remain separate unresolved construction needs.

This is a post-CPC01, pre-control hypothesis, not a predeclared CPC01 condition.
No hand-written suffix rule, exception for these notes, or canonical taxonomy.

The [native NLTK documentation](https://www.nltk.org/api/nltk.stem.snowball.html)
describes English Snowball stemming and its rule-based suffix processing.
This is word-form normalization, not a learned sentence classifier or a
guarantee of word-sense identity. Woods' [Conceptual Indexing](https://cdn.aaai.org/AAAI/2000/AAAI00-215.pdf)
keeps morphology, semantic generality and phrase relationships distinct; this
control deliberately tests only the first, without adopting that full system.

Write minimal failing production-path tests, then run the fixed control once.
Save source matches, changed memberships, both complete relation outputs,
package/source hashes, and an exact offline replay. Preserve CPC01 and GDC09.
