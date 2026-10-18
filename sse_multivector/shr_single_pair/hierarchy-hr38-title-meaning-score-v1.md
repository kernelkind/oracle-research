# HR38 title versus meaning scores v1 — experimental findings

Saved contextual-title vectors improve ordering on the fixed People controls,
but do not separate useful people topics from the reviewed wrong activities.
A useful people topic scores above a wrong case in **24 of 66** comparisons,
versus **14 of 66** with full-meaning vectors. The same Audience reactions
entry scores above all six useful people topics in **both** views.

No new encoding, grouping, boundary, admission policy, semantic label, prompt or
hierarchy was produced. The original conservative candidate is unchanged.
This is a post-result diagnosis on provisional agent-reviewed controls, not a
held-out accuracy estimate or new human gold.

## Fixed comparison

Use the same 22 controls as the
[optional-example probe](hierarchy-meaning-example-probe-v1.md): seven useful
witnesses, 11 reviewed wrong cases and four unresolved cases. Six useful
witnesses describe classes of human beings. Patient advocacy is the seventh;
its accepted witness concerns humane treatment, so it is reported separately
from the six people-class comparisons.

Keep C00006's fused-002 group: 15 People entries and one Individuals entry, all
from distinct source notes. Keep the other six reference groups available for
inspection. Every original title and meaning, source-note exclusion and vector
binding stays unchanged. Compare exactly two saved views:

- **Meaning:** pool the entire explicit meaning in its original
  `title + "\n\n" + meaning` context.
- **Contextual title:** pool the title in that same context. This is not the
  standalone subject vector and does not use an MP mask.

Use the existing score in both views: calculate `exp(-5.5 * (1-cosine))` for
each query/reference pair, then average over the fixed group's references,
excluding the query's entire source note. The kernel and averaging do not
change. Full pair cosines, raw mean cosines, every query/group score and nearest
references are retained for inspection; the primary ordering uses that same
existing mean-support score.

For a useful control, retain its previously reviewed witness. For a wrong case
with several already-reviewed headings, use the highest score among those
headings in each view. Save all heading-level values. Unresolved cases remain
unresolved. No threshold, score weight or new label is fitted from these cases.

The numerical work is bounded: 26 query entries by 69 saved reference entries;
the primary People comparison uses 16 references. There is no outsider graph,
new model, training or all-corpus pairwise calculation.

## Actual scores

Scores below are group mean-support values, not raw cosine similarities.
The two Celebrities rows come from different source notes and meanings.

| Useful people-class witness | Meaning score | Contextual-title score |
|---|---:|---:|
| L03026 · Celebrities | 0.014094 | 0.010988 |
| L03937 · Spectators | 0.020622 | 0.051219 |
| L05684 · Racing drivers | 0.007281 | 0.009688 |
| L07104 · Celebrities | 0.008274 | 0.009467 |
| L03337 · Astronauts | 0.004233 | 0.010740 |
| L07560 · Australians | 0.005236 | 0.006748 |

| Reviewed wrong case | Meaning score | Contextual-title score |
|---|---:|---:|
| Undesired behavior / Spread of behavior | 0.025882 | 0.051153 |
| L04535 · Audience reactions | 0.027289 | 0.067404 |
| Inquiries | 0.014026 | 0.004968 |
| Threats | 0.016556 | 0.005957 |
| Perception | 0.012100 | 0.039123 |
| App login options | 0.014554 | 0.005271 |
| L07783 · Audience reactions | 0.014030 | 0.064796 |
| Games | 0.012093 | 0.012809 |
| Inner spiritual change | 0.014078 | 0.019909 |
| Cognitive biases / Experiences | 0.024220 | 0.025498 |
| Desire to avoid unwanted outcomes | 0.013675 | 0.012920 |

Title scores help distinguish Inquiries, Threats and App login options from
many actual people classes. They still favor audience responses, behavior and
perception. Merely replacing the meaning score with the title score has not
established a usable admission rule.

Across the same six useful by 11 wrong case pairings, useful ranks higher in
14/66 comparisons for meanings and 24/66 for contextual titles; there are no
exact ties. These comparisons share cases and include two Celebrities notes.
They are not 66 independent samples or percentages of correct admissions.
Patient advocacy scores 0.016027 and 0.024886 respectively against this People
group; those values do not judge its separate humane-treatment witness. All
four unresolved controls and their full scores remain saved separately.

## What combining the two scores cannot fix

The strongest counterexample uses **one identical heading in both views**:
L04535, Audience reactions. Its meaning describes audience members communicating
impressions, feelings or evaluations in response to content. The reference
meanings denote human beings. Under the frozen review it is the responses,
rather than the people themselves, that make this a wrong People placement.
That expectation remains a provisional semantic judgment.

This heading's meaning score and title score both exceed every one of the six
useful people-class scores. Consequently, a nonnegative weighted average of
these two group scores will still put it above all six useful entries. The
same limitation applies to other combinations that never decrease when either
input increases. Changing a weight or cutoff cannot reverse this particular
ordering. No such combined score was fitted or introduced here.

Across the whole control panel, a single wrong heading is at least as high in
both affected-group scores in 36/66 pairings. The audit verifies the same wrong
heading, rather than combining one heading's meaning maximum with another's
title maximum. It preserves the initial case-maximum calculation separately.

This is a limit of these **two aggregate group scores**, not proof that all
information in SSE or all reference-based methods fails. Scores against other
reference groups can differ: the Audience reactions witness does not dominate
any of the six useful cases in all 14 coordinates (seven groups times two
views). No rule for exploiting those differences has been validated here.

The next focused diagnostic is to compare pooling the main noun **reactions**
with pooling the entire title **Audience reactions**, keeping its full context
identical. That tests whether the actor word is driving a response-topic match
to People before introducing another boundary or score weight. It would require
new frozen SSE views and has not been run or implemented by this comparison.

## Evidence and verification

Ignored evidence is retained at
`target/food-halves-v1/hr38-title-meaning-score-v1/` in the research task worktree,
through the existing external-storage symlink. Retain the worktree for frozen
source and artifact paths.

- Frozen plan SHA256:
  `4f46ede36dc657637a019fbe5cde42a3a5af9581861d62cbc3b94a5a5eabb468`.
  It pins 29 inputs and the unchanged controls before title-score outcomes.
- `meaning-scores.npz` and `title-scores.npz` retain all 26 by 69 raw pair cosines
  and 26 by seven group mean-support scores. `case-scores.json` retains the
  headings, meanings, scores and closest reference evidence for all 22 cases.
- Both ordering-pair files retain every one of the 66 comparisons.
  `dominance-diagnostic.json` records same-heading two-score and all-14-score
  comparisons without fitting weights or changing labels.
- All 29 inputs remain unchanged. All 95 required title rows match the native
  original HR38 outputs within `8.66e-14` cosine error. All 182 corresponding
  original meaning/group scores replay exactly. Independent scalar
  reconstruction of all 364 group means differs by at most `1.81e-16` and all
  3,588 raw pair cosines by at most `4.45e-16`. The 40 relevant scoring,
  source-note-exclusion and query-isolation regression tests pass.
- No new encodings, LLM calls, training, paid resources, hierarchy changes,
  production admission changes or UI updates.
