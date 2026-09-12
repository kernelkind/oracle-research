# USM02: original-word lookup with part of speech retained

Status: pre-run design. This follows USM01; it does not revise USM01's
preregistered comparison or rerun its encoder.

## Question

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

## Fixed and changed inputs

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

## Interpretation and next decision

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

## Execution

One local CPU scoring process; OPENBLAS_NUM_THREADS=1. Verify the frozen
vectors, input/config hashes, WordNet 3.0 hash and sense-inventory identity.
Bound allocations and score all targets in one matrix multiplication, avoiding
repeated float64 inventory promotion. Add minimal failing tests for new behavior,
then the smallest implementation. Preserve USM01 and the GDC09 browser unchanged.
No paid resource, model download or review-tool packaging.

Method and implementation background remain in
[the source-occurrence research](./SOURCE-OCCURRENCE-GROUNDING.md) and
[USM01 results](./USM01-RESULTS.md). This test isolates an observed mechanism
within that method rather than selecting a new technique from a model catalogue.
