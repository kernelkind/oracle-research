# Definition-input control

SRR01 retained Bread → Sourdough but confused Coffee with a morning greeting
when supplied short names. Its existing manual descriptions removed that error
without establishing reliable relations generally. The checkpoint was trained
on definitions, not category names.

**Hypothesis:** changing the eight fixed GDR01 descriptions into explicit
definitions of the same meanings improves the directional distinctions. Keep
the model, ordered pairs, groups, masks and notes fixed. Score all 56 ordered
pairs, not just the failures. No threshold tuning or hierarchy construction.

Definitions are manually supplied diagnostic inputs, frozen before inference.
They are not an automatic labeling solution. They must preserve the original
scope (including coffee shops) and describe each meaning independently, without
mentioning another group's inclusion or exclusion as a test-specific instruction.

Inspect whether Sourdough remains narrower than Bread, Coffee stops being
narrower than greetings, and the human carnivore diet stops containing Dogs.
Also inspect every other directional prediction, including the bread/diet
error that appeared with SRR01's manual descriptions. The two greeting groups
are equivalent for this experiment; the classifier has no equality output and
cannot establish a useful narrowing between them.

If definitions help, the result supports investigating how to obtain faithful
definitions from complete mask groups. It does not establish a hierarchy or
justify using a single seed's meaning to describe its whole group. If they do
not, inspect the concrete errors rather than adapting the definitions to scores.
