# Hierarchy generation — draft v2

**Status: next-generation draft; not implemented or tested.** The user approved
the L1 prominence threshold, guaranteed selection and highest-score fallback.
The current constructor still follows the
[standalone traversal design](hierarchy-traversal-draft.md).

## Purpose

Build the hierarchy around topics that represent a substantial share of each
note. Ensure every selected L1 is considered, even if individual note access
becomes possible before all selected L1s have been processed.

L1 means a root in a note's original local hierarchy. L2 is its immediate-child
level, and subsequent local levels continue downward. These levels do not refer
to the resulting canonical hierarchy.

## Establish meaning and prominence

For every L1 of every selected note:

1. Establish its explicit meaning independently using the Bootstrap prompt and
   its original evidence.
2. Run [PPv35-post-meaning-v1](prominence-prompt-goal-v1/ppv35-post-meaning-v1/PPv35-post-meaning-v1.md)
   with `node_title` set to the local heading, `node_description` set to that
   explicit meaning, and `post` set to the complete original post.
3. Save the meaning and prominence together with their exact input and producer
   evidence. Reuse that same meaning during traversal; do not regenerate it to
   fit a canonical comparison.

Prominence is an integer from 0 through 100 estimating the percentage of the
complete post's meaning concerning the supplied topic. It is not confidence in
a relationship. Overlapping L1 topics can each score highly; their separate
scores need not sum to 100.

## Select L1s separately for each note

- If at least one L1 has prominence **greater than or equal to 50**, select
  **all** of that note's L1s meeting the threshold. Exclude its other L1s.
- If **none** reaches 50, select **only the highest-scoring L1** of that note.

Proposed tie handling: when several L1s share the highest score in the fallback
case, select the first in the note's saved local-node order. This keeps the
fallback to exactly one L1 without an additional model call.

Determine eligibility after all of that note's L1s have valid scores. A failed
meaning or prominence result is unresolved evidence, not a score of zero and
not permission to invoke the fallback using incomplete scores.

Preserve the existing rotation across notes and saved local-node order, taking
one selected L1 per note per pass. Do not select an excluded L1 later merely
because stopping conditions remain unmet.

## Guaranteed processing

**Every selected L1 must be processed before construction can stop.**

The first selected L1 seeds an empty canonical hierarchy with its established
meaning. Every subsequent selected L1 follows ordinary local-versus-canonical
traversal and the existing placement checks.

Selection guarantees an opportunity for placement, not admission to the
canonical hierarchy. A selected L1 can become a new canonical node, supply
equivalent support to an existing node, or be held when comparison or validation
prevents placement. Preserve those outcomes and their evidence.

Do not stop merely because the existing browsing conditions pass while selected
L1s remain unprocessed. Starting a search is not enough: its placement or hold
must be recorded, and any triggered consolidation must finish.

## Later levels and stopping

This revision applies the prominence threshold to **L1 only**. It does not add a
prominence filter to L2 or deeper levels or change their existing selection
order. Once all selected L1s and their triggered consolidation have finished:

- Stop if every note is individually reachable and every downward canonical
  edge strictly reduces the distinct-note set.
- Otherwise, continue with L2 and deeper levels under the existing traversal
  design, checking the browsing conditions after placements and consolidation.

A held L1 does not waive individual note access. If construction exhausts its
eligible local entries while the browsing conditions remain unmet, report that
outcome rather than claiming a finished hierarchy.

## Existing construction rules

Retain immutable canonical meanings, local-versus-canonical comparisons,
top-to-bottom traversal, branch stopping on `neither`, holds on `uncertain`,
transitive containment, exact answer reuse, and placement checks. Up to three
local searches can overlap; placements remain ordered. The experiment runner
controls request concurrency.

Retain best-effort consolidation after a canonical addition leaves six or more
siblings, including roots. Synthetic proposals still require ordinary traversal
and validation. Six remains a trigger, not a hard maximum.

## Work and validation

Meaning generation and prominence scoring cover every original L1, including
those subsequently excluded. The added work grows with the number of L1s and
their source-post lengths, not every local/canonical pair. Traversal then
processes the selected L1s, reusing exact saved answers where available.

No cost reduction or hierarchy-quality improvement has been measured for this
draft. Compare actual finished hierarchies and total API-equivalent cost,
including meaning generation, PPv35, traversal and consolidation, before making
either claim.
