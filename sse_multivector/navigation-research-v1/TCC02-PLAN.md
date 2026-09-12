# TCC02 — individual-category discrimination on other records

TCC01 found label-context effects and false default decisions, but its
single-category scores put every supported witness above every unsupported
witness for that category in its small audit. The unresolved question is whether
that separation survives other source records. This directly determines whether
calibration is worth investigating; it does not yet choose a membership rule.

## Fixed experiment

Use the same pinned GLiClass checkpoint, native source, runtime, saved-subject
representation, and category wording. Supply only one category per request:
`coffee` or `morning greetings`. No examples, rewritten descriptions, competing
labels, model switch or tuned thresholds. Keep the native 0.5 decisions as
descriptive data, not the main criterion.

Select 25 existing records from 20 notes outside TCC01's 14 source notes.
`TCC02/inputs.json` preserves every complete original, description and mask;
`TCC02/judgments.json` freezes the pre-score semantic judgments. Selection used
source meaning, never new model scores. Coverage includes venues, preparation,
iced coffee, a complaint, wanting another coffee, greeting variants, morning
activity without greeting, breakfast, tea and fatigue. These are a deliberate
challenge set, not a random sample or a corpus accuracy estimate. Two greeting
descriptions are identical; they are not independent semantic successes.

Same-note controls separate coffee from greetings in N095, N058 and N071, and
greetings from jet-lagged breakfast in N005. The model sees only each saved
description. Other meanings in the original cannot supply evidence for that
record's assignment. Full-note consequences must nevertheless be audited
separately: a wrong witness may return a note that belongs through another mask.

Leave caffeine-only row 928 unjudged for Coffee because its broader scope is
not settled. Leave afternoon-greeting row 667 unjudged for Morning greetings;
a broader greeting category could be valid, and that time-of-day boundary is
not the question here. Neither is to become a convenient decisive failure.

## Hypothesis and competing explanations

**Hypothesis:** For each fixed category, the lowest supported score remains
higher than the highest unsupported score among these other records. Inspect
all scores and all resulting inversions, not only selected improvements.

Competing explanations: TCC01 happened to contain easily separable descriptions;
broader category recognition is consistent but the native cutoff is poorly
suited; or wording/context associations cause valid and invalid witnesses to
interleave. A representation or semantic-judgment error could also invalidate
an apparent inversion. Inspect the complete original, actual mask and saved
description before attributing an inversion to classification.

This is a prerequisite check for one monotonic score cutoff per category, not
a claim that perfect classification is a product requirement. An inversion
precludes perfect separation for that tested category; its size and actual
note-discovery consequence still matter. A few errors do not invalidate all
classification or the complete architecture.

Would either outcome change the next decision? Yes. Separation would justify
testing a calibration procedure with disjoint fitting and validation data,
without fitting to this challenge set and calling it validation. Interleaving
would show that threshold adjustment alone cannot provide exact grounded
membership here; inspect the failures and their coverage consequences before
choosing any repair. Do not automatically swap models or turn a narrower
scoped question into a hierarchy-success claim.

The complete construction still needs automatically proposed categories and
meaningful parent–child relations. This experiment tests membership evidence
that those steps would consume; it does not construct a taxonomy by hand or
adopt category-set containment as semantic parenthood.

## Execution and preservation

Reuse the existing native runner with a tested option selecting only the
single-category condition. Preserve its old default behavior and TCC01's
original source snapshot. CPU only, two Torch threads, one model process,
50 primary scores. No downloads of new weights or paid resources.

Preserve the plan and judgments before inference, all inputs and scores,
rendered tokens, native loading checks, code/model hashes, resource use,
regressions and an offline replay. GDC09, prior results, extraction prompts,
and the browser remain unchanged. No TUI packaging.

## Sources

Task-fit and implementation evidence remain the primary sources already audited
in [TCC01](./NATIVE-CATEGORY-MEMBERSHIP.md), particularly the
[GLiClass paper](https://arxiv.org/html/2508.07662v1) and its
[pinned native source](https://github.com/Knowledgator/GLiClass/tree/5d96d8a5d099a10f00d90a2493e5f93a3ddbd2ae).
No new technique or training objective is introduced in this follow-up.
