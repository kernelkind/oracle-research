# Original-word lookup with grammatical evidence

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

USM02 retains the useful tomato, beet and simmer recoveries without letting bread
become breadcrumb coating or beef become complaining. It also excludes useful
decaffeination, canning and homemade meanings. Use this fixed condition for the
next construction comparison, not as an accepted final source representation.

## Controlled change

All 134 USM01 vectors and the 206,949-entry sense inventory were reused. Each
word's candidates came from its original spelling and WordNet morphology, limited
to its saved part of speech. No new encoding, lemma/POS correction, semantic
filter or empty-result fallback was used. The fifteen descriptions represent
thirteen notes, not fifteen independent notes.

The [pre-run plan](USM02-RESULTS.md#usm02-study-design) specifies the alternatives and decision.
[All original notes, inline masks and 134 comparisons](./USM02/SOURCE-RESULTS.md)
are preserved separately. Raw results (`./USM02/run/scores.json`) contain exact
candidate sets and the five highest eligible scores.

## Results and costs

Five highest synsets change relative to saved lemma/POS: tomatoes twice, beet,
simmering and freezing. All five have source-supported physical meanings.
Fifteen change relative to unrestricted-POS word lookup; nineteen occurrences
change against at least one control. These counts describe interventions, not
accuracy rates. Six targets are empty.

Keeping POS fixes the bread-versus-breading distinction. It avoids beef meaning
complaining, although the surviving noun denotes cattle rather than meat.
Bagging still means hunting, and side still means half an animal carcass rather
than the beet meal portions in its source. A lower score for the retained meaning
does not itself indicate lower semantic accuracy.

Four supported original-word outputs become empty: decaffeination twice in one
note, canning, and homemade. The saved grammatical analyses permit no corresponding
lexical entry. Thus the hypothesis is only partly supported: grammatical evidence
prevents some wrong meanings while also blocking useful cross-form matches.
Bolognaise and sautéing remain empty under both lexical alternatives.

Some changed grammatical forms are equivalent topics. Planning versus planned,
using versus used, and drinking noun versus verb need not be categorized as
semantic errors. They can nonetheless produce different dictionary ancestors.
Likewise, cause-to-freeze is a valid description of the intended process, but the
source says ready for the freezer, not that freezing has already completed.

## Construction consequences

An independent all-output WordNet closure check identifies useful potential
destinations, without removing any bad assignment:

| Dictionary meaning | Notes supported by automatic assignments |
| --- | --- |
| Tomato fruit | N026, N096 |
| Vegetable | N022, N026, N096 |
| Cooking | N039, N047, N085, N096 |
| Preparation activity | N076 only |
| Preservation | N013, N022 |
| Meat cuts | N022, N085, N100 |

Cooking has four coherent witnesses: storm-threatened grilling, bread baking,
recipe frying and brisket cooking. This does not require correctly interpreting
every word, such as smoker. Tomato and vegetable meanings can improve narrowing;
these recoveries do not newly bring those notes into broad Food destinations.

The meat-cut group exposes a concrete error: N022 enters through side → half
carcass → meat cut, although its source describes beet side dishes. The steak
and brisket members are valid. Valid neighboring members cannot excuse the
incorrect admission.

The older bread/steak preparation activity group is not preserved by these
assignments: preparation now means a formulated substance in those descriptions.
Only the expanded chef description supplies preparation activity. Its original
chef hashtag supports less literal detail than the expansion.

Simmering reaches boiling/change rather than cooking/preparation. Freezing reaches
physical change rather than preservation. Correct source meanings do not by
themselves supply every useful broader relation. The historical beets/preparation
gap also retains its independent ancestry and source-edge limitations; this run
does not repair the old graphs.

These are construction dependencies, not an improved hierarchy. The completed
[USC01 comparison](./USC01-RESULTS.md) uses the complete automatic assignment to
compare singleton paths with same-description pair refinements. It finds a useful
Cooking/Meat distinction and an occurrence-count artifact, moving the decision
to combination semantics rather than isolated word-accuracy polishing.

## Verification

The run reproduced all 402 original USM01 comparisons and all 1,579 saved scores,
with maximum numerical difference 0.0. An independent source audit checked all
134 identities, ordering and offsets against the fifteen frozen descriptions,
and verified that NLTK actually loaded the hashed WordNet archive.

That audit exposed two missing runner assertions, not corrupt current data.
After a failing regression test, source-identity and loaded-dictionary checks
were added. They pass on the saved inputs. The original executed runner remains
snapshotted with the run; no encoder or numerical rerun was needed for these
provenance checks. Twelve LMMS tests, including a later memory-report correction,
and 61 existing semantic-construction tests pass. The plan hash remains unchanged.

Inventory loading and scoring took 38.746 seconds. Recorded `ru_maxrss` was
5,557,388 KiB; the USC01 check showed this can include inherited pre-exec memory,
so it is not an isolated measurement of this scoring run. Historical values
remain intact; current runners use the process's own `VmHWM`. One CPU process,
BLAS limited to one thread, no model encoding or paid resources.
Run configuration (`./USM02/run/config.json`) preserves hashes and executed source.
Verification (`./USM02/verification.json`) also records a guard limitation:
non-target token edits are not rejected by the source validator. The actual
saved tokenization was independently checked unchanged; this run uses cached
target vectors rather than re-encoding that metadata.
USM01, SGC01–03, GDC09 and the browser remain unchanged.

## USM02 study design

Status: pre-run design. This follows USM01; it does not revise USM01's
preregistered comparison or rerun its encoder.

### Question

USM01 original-word lookup recovered meanings excluded by bad lemmas, but also
removed grammatical restrictions. Bread then became covering something with
breadcrumbs, and beef became complaining. Which effects remain when only the
word lookup changes and the saved part of speech is retained?

The hypothesis is that retaining POS removes those grammatical-category
regressions while preserving the tomato/beet/simmer corrections. An alternative
is that saved POS itself excludes useful meanings, as with the noun analysis
of canning or the verb analysis of homemade. Contextual ranking errors can
remain regardless of either restriction. This is not a hypothesis that any
condition yields perfect senses or an automatically valid hierarchy.

### Fixed and changed inputs

Use every one of USM01's 134 contextual vectors, fifteen unchanged descriptions
and thirteen original notes. Reuse the exact LMMS sense inventory, normalization
and scores. No new model encoding, manual lemma/POS corrections, rewritten
descriptions, source masks, sense additions or semantic filtering.

New condition: run WordNet morphology on the actual token text only within its
saved POS; PROPN uses NOUN as in USM01. Admit only exact lexical sensekeys for
those morphological analyses. Keep empty results empty. Do not add an all-POS
fallback or choose the condition separately for each reviewed example.

Compare it with both USM01 lexical conditions. Reproduce all three USM01 result
sets from saved vectors before interpreting the new condition. Preserve top
five keys, definitions, scores and candidate sets. A supported broader sense,
a related meaning and an unsupported narrow meaning must remain distinct.

### Interpretation criteria

Inspect all changed highest matches and all newly empty results against their
description and original mask separately. A grammatical change is not inherently
a subject error; food versus complaining or bread versus breading is substantive.
Record useful corrections lost by POS as well as regressions avoided. Count
occurrences and distinct source notes separately, not as independent trials.

Would either outcome change the next decision? Yes: retained corrections with
fewer unsupported shifts favor keeping lexical/POS evidence for subsequent
construction investigation; exclusion of useful meanings demonstrates a cost
and may prevent adoption of a strict POS rule. Persistent errors identify limits
not fixed by this intervention. Do not fit example-specific exceptions or claim
that this establishes another cause without a distinguishing observation.

Regardless of outcome, stop treating source-word accuracy as the whole goal.
Trace which observed differences could change existing note destinations and
which still cannot bridge their ancestry or membership limitations. Any later
construction must choose inputs algorithmically, not from hand-approved senses.
Do not redo construction solely to illustrate an unchanged dependency.

### Execution

One local CPU scoring process; OPENBLAS_NUM_THREADS=1. Verify the frozen
vectors, input/config hashes, WordNet 3.0 hash and sense-inventory identity.
Bound allocations and score all targets in one matrix multiplication, avoiding
repeated float64 inventory promotion. Add minimal failing tests for new behavior,
then the smallest implementation. Preserve USM01 and the GDC09 browser unchanged.
No paid resource, model download or review-tool packaging.

Method and implementation background remain in
[the source-occurrence research](SOURCE-OCCURRENCE-GROUNDING.md) and
[USM01 results](USM01-RESULTS.md). This test isolates an observed mechanism
within that method rather than selecting a new technique from a model catalogue.
