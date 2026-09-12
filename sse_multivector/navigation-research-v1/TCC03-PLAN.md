# TCC03 — complete available evidence per note

## Missing capability

TCC02 demonstrates some incorrect ordering of individual subject descriptions.
It does not establish incorrect ordering after every available description
can contribute to the note. A note has several masks; the intended architecture
permits any genuinely supporting mask to place it in a category. Before changing
the model or tuning cutoffs, test this actual representation-to-note step.

## Fixed inputs and intervention

Use every saved CAP04 subject/mask record from the same 20 TCC02 notes:
181 descriptions, 177 canonical masks, 3–34 descriptions per note. Preserve
all originals, subjects, fragments, IDs and ambiguities. Place the original
25 records first, then the additional records in original row order. No new
subjects, masks, manual repairs, category labels or model settings.

Each description is scored independently with `coffee` alone and `morning
greetings` alone, using the same pinned native GLiClass runner. The model sees
only the subject description; it never sees the entire note or other records.
The two analysis conditions use these same scores:

- Control: a note receives the highest score among its TCC02 records.
- Expanded evidence: a note receives the highest score among all its records.

The maximum is a deterministic implementation of accepting a note when any
description passes a threshold. It is not a probability that the note belongs.
Keep each attaining row and its original mask. Duplicate descriptions and
aliases are preserved, not counted as independent evidence.

All TCC02 source judgments are preserved. The separate full-note judgments in
`TCC03/judgments.json` are made before additional inference and independently
reviewed, but these notes and some scores have already been examined. This is
not an unseen holdout or a corpus accuracy estimate. Coffeechain-only N005/N092
and caffeine-only N034 remain unjudged for Coffee. For greetings, leave N018
(afternoon), N052 (Rise and grind) and N045 (Dear America) unresolved. N045's
salutation is outside its saved masks; it must not become a convenient decisive
failure. No category boundary is inferred from a score.

## Hypothesis, competing explanations and decisions

Hypothesis: the additional descriptions contain grounded supporting evidence
that restores Coffee's note-level ordering without destroying the greeting
ordering. For each category and condition, compare every judged supported note
with every judged unsupported note. Preserve all inversions, not just a favorable
example. Inspect every maximum and any additional supporting description that
changes a consequential ordering against its source.

Competing explanations: TCC02 omitted a stronger valid witness; the model's
association errors remain after full evidence; or more descriptions amplify
false associations until unrelated notes outrank valid ones. Restored ranking
through an unsupported or overinterpreted maximum is not grounded recovery.
Existing extraction errors and category-scope disputes must be distinguished
from pooling and classification errors.

At a fixed threshold, expanding a maximum cannot remove an admitted note. Since
TCC02 already accepts all judged positives at 0.5, this cannot repair its
existing default-threshold errors. The question is ranking and the possibility
of subsequent calibration, not a promised improvement at 0.5. Check common
record scores against TCC02 to detect numerical/runtime changes; use the same
TCC03 scores for both analysis conditions.

Would either outcome change the next decision? Yes. Grounded recovery would
show that selected-witness inversions need not block note retrieval, supporting
a separate calibration investigation on disjoint notes. Remaining inversions
would show that full available evidence and this pooling rule still do not
allow exact separation here. Lost greeting separation would expose an aggregation
problem missing from TCC02. In every case inspect practical coverage and incorrect
additions; do not require perfect accuracy to call a score potentially useful.

This study does not generate categories or semantic parent relations. If evidence
supports a usable imperfect membership component, the next construction decision
must address those dependencies rather than indefinitely optimizing two labels.

## Execution and preservation

Run one CPU process, two Torch threads, 362 primary scores, offline from the
existing checkpoint cache. No paid resources or new model download. Preserve
inputs, judgments, complete scores, maxima and all inversions, native provenance,
an exact offline replay and regression results. Do not alter GDC09 or package
a browser. This is a consequential follow-up to TCC02, not a new model choice;
the training/task-fit evidence remains in the TCC01 primary-source audit.
