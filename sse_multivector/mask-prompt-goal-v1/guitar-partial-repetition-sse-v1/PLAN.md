# GPRv1 — repetition at broad and detailed subject levels

Prospective plan, before inference. Follow-up to BPRv1, not a prompt test.
One unchanged real guitar note; broad target **Guitars** and detailed target
**Guitar retuning when putting on or taking off a capo**. These are previously
fixed diagnostic subjects, not newly generated ASv6.48 headings. This note is
different from the bread note but was used in prior masking tests.

## Question and competing explanations

Does selecting more guitar mentions help represent the broad subject while
weakening the detailed one? It could help both, hurt both, have negligible or
mixed effects, or behave differently by mention context. Bread may not transfer.
Even if target similarity rises, separation from a different meaning may fall.
No result establishes that an entire hierarchy succeeds or fails.

## Fixed intervention

Reuse the saved accepted MPv3.32 masks for T03/T04. The later detailed MPv3.34
output omits `every time`, an unresolved issue; do not combine that omission
with this repetition test. No regeneration or change to any saved output.

For both levels, the core guitar mention is the one in the retuning sentence.
The broad core selects that word alone. The detailed core retains all three
saved fragments within that sentence: `retune`, `guitar every time you put a capo
on and take it`, and `off`. Retain the condition throughout.

At each level compare core, core plus the final hashtag's guitar, core plus the
other four prose guitar mentions, and core plus all five additional mentions.
The last variants exactly reproduce each saved full mask. The same extra spans
are added at both levels; no new ownership, electric, setup or fret wording.

Also encode each of the six guitar mentions alone. The retuning mention is
already the broad core, so add only five more masks. This checks sensitivity to
the initial occurrence rather than selecting a convenient one after results.
These 13 masks are controlled interventions, not approved replacements.

## Comparisons

Fifteen full-text, synthetic comparison anchors are fixed in study.py: three
surface forms for guitars generally, three matched violin controls, three
capo-triggered retuning paraphrases, three string-replacement-triggered retuning
paraphrases, and three capo-use-without-retuning contrasts. They are diagnostics,
not real corpus notes, gold parents, or independent statistical replicates.

Report all scores, means, matched rankings and margins. For the broad subject,
inspect resemblance to guitars generally and distinction from violins. Relative
movement toward/away from retuning indicates emphasis, not correctness alone.
For the detailed subject, inspect target resemblance plus separation from
other-trigger and without-retuning contrasts. If those distinctions are absent
in the core, do not attribute the failure to repetition. Interpret negation
failures separately from abstraction. Inspect every wording, not just means.

Compare broad all-mentions against all six single-mention results. If only the
chosen core improves but another single mention is already better, report that
limitation. Do not claim all-mentions is an optimal broad mask from its mean.

## Execution and decision

One 28-vector CPU FP32 run with the unchanged production SSE worker, checkpoint,
tokenizer artifacts and batch size. Reuse BPRv1's exact local dependency versions
and measured saved-vector parity; verify identities and runtime equality without
rerunning those seven controls. Offline, no paid services, generation, baseline
prompt reruns, model downloads, clustering or UI changes. The historical
container reference in the worker schema is not evidence of Docker execution.

If the effect differs by subject level, propose a scope-sensitive repetition
policy rather than blanket inclusion/exclusion. If both levels benefit or
results are mixed, retain that evidence against the initial explanation. If
neither benefits, reconsider why exhaustive repetition is required at all.
In every outcome preserve the prompt and record uncertainty; recommend the next
decision without starting another test or prompt revision automatically.
