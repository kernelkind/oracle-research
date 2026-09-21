# PPv3 — mask-based prominence

Status: draft, not model-tested, frozen or selected for production. This is a
standalone replacement-input proposal, not a modification to frozen PPv2 in
`../../prominence-prompt-versions.json`. No model calls accompany this draft.

## Purpose and input

Rank notes within a hierarchy node by how directly the complete note is about
the node's meaning. A mask's prominence within its source note is the proposed
ranking signal; how multiple masks contribute to ordering at a broader node
remains unresolved.

The prompt receives the complete original post with one nonempty, mechanically
valid mask marked inline. Every selected fragment is enclosed in `⟦` and `⟧`;
all marked fragments belong to that one mask. It receives no generated subject
description or other masks. Empty masks have no selected meaning to score;
invalid outputs must not be converted into empty masks or zero scores. This
draft does not implement input rendering or pipeline integration.

PPv3 keeps PPv2's 0–100 integer output and score bands as a provisional starting
point. It removes the requirement that a central focus be "extensive," so a
short note is not implicitly barred from a high score. The scale is not a
probability, a percentage of selected words, or a validated calibration.

## Reasoning and open checks

- The mask fixes what is being assessed; unmarked discussion can establish its
  prominence. Exact-level restrictions on mask selection must not exclude
  narrower examples from the evidence of focus.
- ASv6.48 subjects remain a reference for assessing extraction, not input to
  this prominence prompt. Mask development continues separately. A future test
  must identify the exact saved masks and prompt versions it uses.
- Saved MPv3.26 coffee-shop masks distinguish the venue from its laptop/tablet
  ban. Saved MPv3.27 baby masks show that two selected hashtag fragments can
  identify the subject of nearly the entire post.
- Saved MPv3.26 masks for "Getting up and grinding coffee beans" and "Wordplay
  on 'rise and grind' and grinding coffee beans" select the same complete note.
  A mask-only scorer cannot recover which original heading was intended. This
  draft does not claim to resolve that ambiguity or show that it harms ranking.
- Independent per-mask judgments may still disagree across overlapping masks.
  No monotonicity rule or parent-score aggregation is established here.
- No model performance is established by the manual inspection or this draft.

Relevant saved evidence:

- `../../mask-prompt-goal-v1/mpv3.26-coffee-ban-hierarchy-v1/assessment.json`
- `../../mask-prompt-goal-v1/mpv3.27-infant-hierarchy-v1/assessment.json`
- `../../mask-prompt-goal-v1/mpv3.26-complete-hierarchies-v1/assessment.json`

## Prompting guidance

The [official OpenAI reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively)
supports straightforward instructions, clear input delimiters, an initial
example-free prompt and no requested chain-of-thought output. It does not
validate this task definition, the numerical anchors or mask-based scoring.

Next suggested step, pending approval: test this draft on a small fixed set of
saved masks, including broad/narrow selections and central/incidental subjects,
without regenerating subjects or masks. Inspect resulting orderings and the
meaning actually scored, not merely whether the response is valid JSON.
