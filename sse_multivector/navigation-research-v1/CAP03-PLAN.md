# Existing subject text as construction input

## Question

Can the already-generated description of each mask improve category construction
without adding a parser, another generation step, or a category-relation model?
CAP02 used literal mask words as attributes. CSA01 established that word senses
alone would not supply all the missing phrase meanings. Before adding a new
component, test the semantic descriptions already present in the frozen evidence.

This is a representation control, not permission to replace source evidence with
generated prose. Category judgments still require the masks and complete notes.
GDR02 used a seed subject as a description of an entire group. Here each subject
describes only its own mask; shared descriptions are constructed mechanically.

## Fixed and changed inputs

Use all GDC09 evidence, with no hand-selected subjects or manual corrections.
Each distinct saved subject for a canonical mask becomes a separate input record.
Keep its canonical row, note, aliases, exact subject, fragments and full original.
Do not concatenate alternative subjects into a new compound description.

Run the same CAP02 construction twice on these identical records:

- Control: features extracted from the original mask fragments.
- Changed input: features extracted from the corresponding saved subject string.

Keep word/symbol extraction, recurrence in at least two distinct notes, complete
input seeds, single-feature closures, descriptor extension, strict note narrowing,
and transitive reduction unchanged. Repeated aliases do not provide extra notes.
Verify that mapping control memberships back to canonical rows reproduces CAP02
exactly. No stemming, stopword list, score cutoff, learned classifier or manual
category is added. Record every subject alternative rather than choosing a best one.

## Hypothesis and competing explanations

The subject representation removes some misleading shared-word descriptions and
creates source-supported parent/child paths or restores relevant memberships that
the mask-word control misses. The existing dinner/storm, coffee-experience, bread
and greeting examples are diagnostics, not an exhaustive or uniquely correct taxonomy.

Competing explanations: apparent gains come from unsupported generated meaning;
generic summary wording creates spurious commonalities; useful distinctions are
still lost when prose is reduced to unordered words; paraphrases create new lexical
omissions; the bounded candidate family misses useful combinations in either input.

Inspect all proposed links and every source mask/full note supporting links judged
potentially substantive. Record excluded relevant examples where evidence exists.
Classify grammatical constraints separately, without using that classification to
silently modify the output. Preserve ambiguous cases instead of forcing pass/fail.
Formal containment and additional depth are not semantic evidence by themselves.

Could success occur without the needed capability? Yes: a generated term might
describe the note but not its mask, or repeated reporting language might create an
apparently narrower group. Audit source grounding and scope before counting gains.
Could failure be unrelated to the representation? Yes: closure limits and literal
matching remain. Confirm the unchanged control and inspect which stage loses a
meaning instead of declaring the subject model or whole architecture invalid.

Would either outcome change the next decision? If this removes meaningful errors
or supplies defensible new paths, reuse existing descriptions for further structure
tests rather than assume another context extractor is required. If a meaning is
present in the subject but lost by word features, test structured features next.
If it is absent or unsupported in the saved subject, attribute that limitation to
the representation input and do not ask a parser to repair it. More than one
outcome may occur. Do not adopt a browser on the strength of a few examples.

## Literature fit

LLooM separates short textual summaries, clustered examples, synthesized concepts,
and membership scoring. Its synthesis may identify a subset of a cluster rather
than invent a description covering every item. This supports keeping per-example
descriptions separate from group descriptions. Its explicit full-data scoring
remains a different, costly operation; it does not validate our inclusion rule.
The paper also notes that its implementation does not verify summary fidelity.
This experiment reuses existing descriptions and deterministic construction; it
does not reproduce LLooM or establish its model performance here.[^1]

## Preservation and decision record

Save exact inputs, both outputs, differences, code/input hashes, complete link
inventory and semantic assessment under CAP03. Keep GDC09, previous experiments,
prompts, masks, SSE vectors and the browser unchanged. No new model calls, model
downloads or paid compute are required. No TUI packaging before goal wrap-up.

[^1]: Lam et al. (2024), [Concept Induction: Analyzing Unstructured Text with
High-Level Concepts Using LLooM](https://arxiv.org/html/2404.12259v1), sections
3.1.1–3.1.4. These method and limitation sections were read; this experiment does
not borrow a quantitative performance claim from the paper.
