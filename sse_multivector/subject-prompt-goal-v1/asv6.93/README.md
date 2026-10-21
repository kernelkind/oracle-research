# ASv6.93 finite collection clarification

Status: tested experimental draft; retains failures and is unadopted.
The [completed matched screen](../isolation-v1/finite-collection-v1.md) has
24 accepts/9 rejects from 33 valid first attempts, including 6 accepts/6 rejects
on the original posts. Finite collection clarification does not yield a reliable
fix. Historical pre-inference descriptions below record authoring conditions.
[ASv6.93](ASv6.93.md) derives from the exact
[ASv6.92 source](../asv6.92/ASv6.92.md) and POST template. It clarifies that a
heading's own entry represents an equal-meaning source subject, while every
more-specific compatible source subject belongs among its descendants at every
numbered occurrence. The pre-numbering instruction and every subsequent edge,
source and copy audit remain exact.

One added C1 explanation sentence demonstrates the same finite interpretation:
the complete shared cutting action is represented by its own terminal entry and
still appears beneath every compatible group and partial-action occurrence.
All seven example posts and JSON outputs remain byte-identical to ASv6.92;
the other six explanations remain unchanged.

This makes R22's already implied finite collection explicit. C1 retains its
primary R22 assignment and demonstrates canonical leaves alongside proper group
and partial-action descendants. All 34 primary clause assignments and five
tracked implications remain covered. No new primary rule, output field, schema,
inference pass or optional heading requirement is introduced. Equality depends
on the subject wording's meaning; source context cannot supply missing
restrictions, and a placement elsewhere cannot fill a distinct compatible
subject's missing copy.

ASv6.92's confirmed N096 and N100 proper-copy failures remain the existing
production-path failing cases. The literal self-collection ambiguity is not
asserted as their cause, and this draft has no demonstrated behavioral gain.
The planned ASv6.94 counterpart inherits this exact finite clarification and
C1 sentence and changes only collection traversal direction. The root agent
owns screen freezing, inference, budget accounting, tests, aggregate
documentation and the final local commit. Authoring makes no teacher requests.

Native `experiment.py revise` applies the two exact replacements to the pinned
ASv6.92 source and template bases. The versioned
source edits (`03bd9e45:sse_multivector/subject-prompt-goal-v1/asv6.93/prompt-edits.json`) and template edits (`03bd9e45:sse_multivector/subject-prompt-goal-v1/asv6.93/edits.json`) preserve those
base hashes; automatic receipts record the revised
source (`03bd9e45:sse_multivector/subject-prompt-goal-v1/asv6.93/ASv6.93.md.revision.json`) and
template (`03bd9e45:sse_multivector/experiment_specs/asv6.93-hr01-post-template.txt.revision.json`).
The POST template (`03bd9e45:sse_multivector/experiment_specs/asv6.93-hr01-post-template.txt`) remains
exactly the prompt followed by `\n<post>\n{POST}\n</post>`.

The [matched screen](../isolation-v1/finite-collection-v1.md) freezes 33 new
answers for this draft and 33 for ASv6.94, inheriting identical completed
ASv6.92 inputs/evidence and runner settings. All 121 relevant offline checks
pass, including production example validation, proper per-occurrence copies,
irreflexive example ancestry and unchanged coverage/template. These checks are
authored consistency evidence; model behavior remains untested at this freeze.
