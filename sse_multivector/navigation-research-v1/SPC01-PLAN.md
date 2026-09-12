# SPC01 — source-derived category paths

## Question

Can grammatical phrase construction turn the existing descriptions into useful
complete category choices and source-backed narrowing paths? This tests actual
construction, not whether two paraphrases have identical dependency trees.

CAP04 enumerated two-word patterns; CPC02 kept twelve predetermined strings.
DSP01 inspected fourteen parses without constructing a category inventory or
paths. Their limitations remain controls, not proof that a phrase-based
construction cannot contribute anything useful.

## Frozen inputs and construction

Use all 945 descriptions in CAP04/result.json, with their original source notes,
masks and aliases unchanged. Parse them using DSP01's pinned, cached Stanza
English EWT pipeline. It was trained for grammatical annotation, not semantic
categories. Reuse its production parsing function and retain native parses.
No new model, frontier generation, source correction or semantic classifier.

For each noun/proper-noun head, generate at most three nested expressions:

1. The head and its `flat`/`fixed` dependents.
2. Add its nominal modifiers: `compound`, `amod` and `nummod`, retaining their
   internal modifiers and coordination.
3. Add nominal `nmod` dependents, preserving their case markers and nominal
   content. Do not follow a main verb or relative clause to invent a phrase.

Retain case markers inside an added modifier, not the external preposition of
the head itself. Omit ordinary determiners from expressions. Preserve selected
source word IDs, exact source fragments and all native labels. These are
grammatical projections proposed as category descriptions, not certified noun
phrases or semantic truths. Keep discontinuous projections visible for audit.

Identify expressions by their case-folded lemma sequence and internal labeled
dependency structure, including the head position. Original surface forms
remain available. Equal expressions share a candidate; distinct parses remain
distinct. Every source occurrence remains recoverable, but count support by
distinct original note IDs, not repeated descriptions.

Propose a broader-to-narrower edge only when two expressions are nested stages
of the **same head in the same description**. Record that occurrence as the
edge's evidence. Merge these observed edges across descriptions. Do not infer
edges from note-set containment, reverse edges by frequency, attach disconnected
roots through similarity, or propagate predicted memberships upward.

For each candidate, membership is the union of notes where its grammatical
expression was produced. Audit parent/child membership differences explicitly:
sharing a phrase string elsewhere need not reproduce the same observed path.
Do not silently repair such differences.

Keep every candidate internally. Report the complete menu restricted to at
least two distinct notes, contracting paths only across excluded candidates;
also report which choices would remain at five notes. These are display/support
views of the same result, not fitted semantic cutoffs. Preserve equal-note
choices as flagged records rather than claiming their meanings equivalent.
Do not package a TUI yet.

## Hypotheses, controls and competing explanations

The hypothesis is that retaining grammatical expressions and their observed
extensions produces meaningful complete distinctions beyond CAP04/CPC02,
without admitting unrelated notes through a learned classifier. It can fail
because the expressions are mostly verbose single-note descriptions, generic
reporting language, repeated choices or misleading generalizations.

Inspect complete menus and every multi-note proposed edge, including all
supporting source records and actual originals for consequential judgments.
Record correct paths, incorrect paths, genuinely uncertain scopes, missed
known material and equal-note transitions separately. Do not declare the whole
method failed from one error or successful from one familiar phrase.

Use these existing records as diagnostic controls, not a canonical taxonomy:

- N037/356 contains an ingredient-qualified sourdough-bread description: can a
  complete expression and its simpler forms actually be constructed?
- N010/278 and N092/243 distinguish a chicken dish from a chicken tractor;
  the shared prefix `a chicken` is not the complete distinction.
- N047/375, N047/838 and N072/501 expose the contexts hidden by `bread in`.
- N013/468 has a known incorrect native grammatical attachment: do not credit
  it as evidence that plain chicken stock is a preservation activity.
- Rosemary/bread 669/254 and coffee-experience 572/854 remain different-grammar
  controls. Missing their common refinements bounds coverage; it need not
  invalidate other useful construction. Row345's internet dispute must not
  be credited as coffee-drinking experience.
- Sea salt and Sourdough bread are known successes. Merely reproducing them
  does not establish new construction progress.

Competing explanations include better phrase boundaries, merely stricter
matching that loses relevant notes, false precision from parser errors, and
generated-description meaning absent from the original mask. Preserve the
distinction between a valid destination note and a faulty supporting witness.

Would either outcome change the next decision? Yes. Useful new paths and
understandable menus would justify retaining this as a construction foundation
and investigating its remaining disconnected meanings. Mostly unusable choices
would reject phrase construction alone for that role. It would not justify
another parser, stopword list or threshold without evidence of the responsible
mechanism. An implementation failure requires correction before semantic
conclusions. A correct one-note phrase is not evidence of useful multi-note
browsing, and its absence from the menu is not a grammatical failure.

## Complete-method fit and limits

The proposed foundation would derive descriptions, their source occurrences and
some narrowing paths together, keeping each placement traceable to text. Broader
lexical abstractions and paraphrase recovery would remain separate additions,
not assumed results. Woods' conceptual indexing combines such structure with
lexical relations and relaxed retrieval; grammar alone does not reproduce it.

Head-preserving structure is only one kind of topical refinement. Chicken stock
has head stock, and coffee shops has head shops: a Chicken or Coffee parent needs
additional justification. Equivalence, word senses and useful top-level
selection remain open. This test does not require a complete dictionary taxonomy,
perfect recall, or one prescribed arrangement of these notes.

See [construction-method research](./CONSTRUCTION-MECHANISMS.md) for the source
and task-fit review. No literature result certifies the generated paths.

## Verification and resources

Create minimal production-path tests first and observe their expected failure.
Cover nested stages, exact fragments, external versus internal prepositions,
preserved identities, source-note deduplication, edge provenance, disconnected
roots and invalid input. Reproduce output deterministically from saved parses.
Compare the fourteen overlapping native parses with DSP01 rather than silently
changing those controls. Preserve code/input/model hashes and all baseline files.
CPU only, one model process, two threads; no paid resources or downloads.
