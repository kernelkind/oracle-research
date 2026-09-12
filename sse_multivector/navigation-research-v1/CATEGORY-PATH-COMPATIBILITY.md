# Category membership and browsing paths

CPC01 connects the previously tested category classifier to the existing
construction rules. It recovers some relevant notes, but both fixed score
cutoffs remove all three clearly meaningful parent–child paths in the tested
family. This is evidence against the unchanged combination—not against the
existence of those semantic relationships, or against every learned matcher.

No GDC09 category, mask, vector, hierarchy or browser changed. The experiment
does not generate a new taxonomy or claim that this family is representative.

## What changed

The [pre-run plan](./CPC01-PLAN.md) fixes 12 source-derived candidate strings:
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
[frozen judgments](./CPC01-JUDGMENTS.json) cover six complete categories across
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

The [complete audit](./CPC01/audit.json) lists every error, retained assignment,
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

The [control plan](./CPC02-PLAN.md) was written after CPC01 and frozen before
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
and 712. Thus there are [17 added occurrences](./CPC02/added-occurrences.json)
across 16 distinct source rows, not just the 14 added candidate/row memberships
in the table. Nothing is removed. All changed masks and complete originals
were independently inspected.
The [audit](./CPC02/audit.json) retains each changed description and all six
category judgments. [result.json](./CPC02/result.json) retains every raw and
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
[run/config.json](./CPC01/run/config.json).

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

The [analysis result](./CPC01/analysis/result.json) preserves all twelve candidate
memberships and relation outputs, including candidates without a certified
meaning. [Raw scores](./CPC01/run/scores.json), [unchanged inputs](./CPC01/prepared/inputs.json),
[candidate occurrences](./CPC01/prepared/candidates.json) and the
[pre-score manifest](./CPC01/prescore-manifest.json) remain available separately.

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
does not. The [pre-control manifest](./CPC02-precontrol-manifest.json) freezes
the plan, judgments, source inputs, candidates, runner and stemmer source.
[CPC02/config.json](./CPC02/config.json) records the copied code/package hashes.

## Sources

[^1]: Sanderson and Croft (1999), [Deriving concept hierarchies from text](https://ciir.cs.umass.edu/pubfiles/ir-156.pdf), sections 2–4.
[^2]: Shang et al. (2017), [Automated Phrase Mining from Massive Text Corpora](https://arxiv.org/html/1702.04457), sections 2–4.
[^3]: Woods (2000), [Conceptual Indexing](https://cdn.aaai.org/AAAI/2000/AAAI00-215.pdf), conceptual indexing, subsumption and retrieval sections.
[^4]: NLTK 3.9.2, [English Snowball stemmer](https://www.nltk.org/api/nltk.stem.snowball.html#nltk.stem.snowball.EnglishStemmer), rule-based suffix processing and fixed implementation.
