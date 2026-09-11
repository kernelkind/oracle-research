# Existing subjects as group-meaning candidates

GDR01's manual descriptions recovered greeting equivalence. GDR02 removes that
manual step: every candidate comes from the frozen data. No new subject or mask
generation, description editing, model training, membership change or browser
change is performed.

## Hypothesis

The subjects already attached to the original seed masks contain enough context
to recover the greeting relationship and retain bread narrowing. Checking these
candidates against the group's other members should also expose the previously
observed Art and Rise sense mixtures. The model must not be credited with a
working construction process merely because these examples succeed.

## Fixed inputs

Use all 22 unchanged MDH02 groups saved in LGR01 and their original GDC09
evidence. Every original seed mask supplies two kinds of candidate:

- Its exact fragments joined with spaces.
- Every frozen generated subject attached to that canonical mask, verbatim.

Keep all distinct alternatives and their provenance. Merge only exactly equal
candidate strings within one group and one kind. Do not pick the first, shortest,
most confident or most conveniently interpreted generated subject. A candidate
is not assumed to describe the group correctly.

Use the same GDR01 model, pinned revision, settings and wrapper:
`This text is about {description}.` Existing subject strings can be sentences
and include final punctuation; they are not rewritten into noun phrases. Save
the exact resulting model inputs so formatting and scope remain inspectable.

## Two separate measurements

**Coverage:** compare every existing member's generated subject with each
candidate for its own group. The member subject is always the premise; only
the candidate changes between raw phrase and generated subject. Preserve all
aliases. Report both mask-level coverage and distinct notes with at least one
supported mask; duplicate masks must not turn one note into several votes.
Also expose unsupported aliases. Do not silently use either all-mask coverage
or one-mask-per-note coverage as an acceptance rule.

**Relations:** score every ordered pair of candidates from different groups,
separately for raw phrases and generated subjects. Retain every score, not just
the best combination. Report disagreement between alternatives rather than
accepting the most favorable pair. An implication in both directions suggests
equivalence, not redundant nesting.

Use the classifier's ordinary 0.5 decision only to organize inspection. No
threshold sweep, candidate selection, pruning, group reassignment or relation
adoption follows automatically. Inspect every positive group-pair proposal
against its complete source masks and notes, with its candidate-coverage results.

## What would be learned

Improved relation scores with adequate source coverage would support using the
existing subject outputs as an input to construction. Coverage failures may
instead reveal an unsuitable seed description, a mixed source group, a source
subject error, or a classifier error; distinguish these through the actual
masks and original notes. Generated subjects are evidence inputs, not truth.

The complete hierarchy remains the goal. This experiment tests whether the
manual semantic input can be removed before building from these relations.
It must not certify an eight-group toy hierarchy or demand that an algorithm
reproduce one hand-written taxonomy.

## Research basis

HyperDef makes term sense explicit through descriptions, but its maximum over
all definition combinations can validate an irrelevant sense for a particular
group. GDR02 retains alternatives and examines their coverage instead. It does
not reproduce HyperDef or claim that NLI is a proven hierarchy constructor.[^1]

[^1]: Yin and Roth (2018), [Term Definitions Help Hypernymy Detection](https://aclanthology.org/S18-2025.pdf), section 3.3 and analysis in section 4. The model and earlier diagnostic limitations are recorded in [GDR01](./CONTEXTUAL-GROUP-RELATIONS.md).
