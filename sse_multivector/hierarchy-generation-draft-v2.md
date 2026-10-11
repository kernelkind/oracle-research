# Hierarchy generation — draft v2

**Status: next-generation draft; not implemented or tested.** The user approved
guaranteed L1 selection by prominence, additional L1s for uncovered notes, and
prominence-ordered refinement of multi-note leaves. Choosing which equal-note-set
steps to remove remains open. The current constructor still follows the
[standalone traversal design](hierarchy-traversal-draft.md).

## Purpose

Build the hierarchy around topics that represent a substantial share of each
note. Ensure every guaranteed L1 is considered, even if every note becomes
represented before all guaranteed L1s have been processed.

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

## Select guaranteed L1s separately for each note

- If at least one L1 has prominence **greater than or equal to 50**, select
  **all** of that note's L1s meeting the threshold for the guaranteed pass.
  Leave its other L1s unused for now.
- If **none** reaches 50, select **only the highest-scoring L1** of that note.

Proposed tie handling: when several L1s share the highest score in the fallback
case, select the first in the note's saved local-node order. This keeps the
fallback to exactly one L1 without an additional model call.

Determine eligibility after all of that note's L1s have valid scores. A failed
meaning or prominence result is unresolved evidence, not a score of zero and
not permission to invoke the fallback using incomplete scores.

Preserve the existing rotation across notes and saved local-node order, taking
one guaranteed L1 per note per pass.

## Guaranteed processing

**Every guaranteed L1 must be processed before construction can stop.**

The first guaranteed L1 seeds an empty canonical hierarchy with its established
meaning. Every subsequent guaranteed L1 follows ordinary local-versus-canonical
traversal and the existing placement checks.

Selection guarantees an opportunity for placement, not admission to the
canonical hierarchy. A guaranteed L1 can become a new canonical node, supply
equivalent support to an existing node, or be held when comparison or validation
prevents placement. Preserve those outcomes and their evidence.

Do not stop merely because browsing conditions pass while guaranteed
L1s remain unprocessed. Starting a search is not enough: its placement or hold
must be recorded, and any triggered consolidation must finish.

## Add remaining L1s only for uncovered notes

After the guaranteed pass and its triggered consolidation finish, check which
notes have at least one original local entry represented in a canonical node.
An equivalent placement counts as representation; a held entry does not.

For a note still absent, select its remaining unused L1s until one is admitted.
Use its already saved prominence scores, taking the highest unused first. Stop
selecting additional L1s for that note once it is represented. Rotate across
uncovered notes when several still need admission.

If every L1 of a note is processed without admission, record that coverage is
unresolved. Do not fabricate support or claim that note is represented.

## Refine multi-note canonical leaves

A canonical leaf has no canonical children. Its note set consists of its
supporting note IDs, deduplicated. Select unused deeper local nodes to refine
leaves containing more than one distinct note.

1. Choose the unfinished leaf containing the most distinct notes. Use saved
   canonical-node order to break ties.
2. For each note in that leaf, identify the original local branch supporting
   it. Initially, consider only the L2 children of that branch's local root,
   rather than every L2 across the note's other local roots.
3. Establish each eligible child's explicit meaning and run PPv35 using that
   meaning and its complete original post, as for L1. Prominence sets priority;
   there is **no 50-point cutoff** at these deeper levels.
4. Rotate across the leaf's notes in saved note order. Take the highest-scoring
   unused eligible child for each note on its turn. Break prominence ties using
   saved local-node order.
5. Every selected child follows ordinary traversal of the canonical hierarchy.
   Selecting from a leaf's supporting branch does not force placement beneath
   that leaf. Reassess leaf membership after placements and consolidation.

For a leaf containing notes A, B and C, selection proceeds as:

```text
A's highest unused L2 -> B's highest unused L2 -> C's highest unused L2
A's next unused L2    -> B's next unused L2    -> C's next unused L2
```

When the relevant L2 is exhausted and refinement is still needed, repeat at L3
and subsequent levels within those original local branches. Continue rotating
across notes and selecting the highest-prominence unused node at that level.
Do not repeat a local node already processed through another leaf.

Stop expanding a leaf when it represents one note or its relevant original
local branches have no unused descendants left. Record a multi-note group that
remains after exhaustion. A note represented only at an internal canonical node
does not require additional comparisons solely to create a singleton node for it.

## Selection completion and shaping

Selection has no remaining work when every guaranteed L1 has been processed,
every note is represented, and no multi-note leaf has eligible unused descendants.
Uncovered notes remain an unresolved outcome rather than successful coverage.

The finished browsing hierarchy must strictly narrow the distinct-note set at
every downward edge. Count own supporting notes plus recursive canonical
descendants, deduplicating note IDs. Remove equal-note-set steps while preserving
note access, fixed meanings and valid containment. Equal observed note sets do
not establish semantic equivalence.

Which nodes to retain and how to perform this removal automatically remain
open. The selection rules alone do not resolve equal-note-set edges or establish
that a finished hierarchy has passed this requirement.

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
those outside the guaranteed pass. Deeper scoring covers eligible entries in
the relevant local branches of multi-note leaves, not every deeper entry of
every note. The added scoring work grows with the entries assessed and their
source-post lengths, not every local/canonical pair. Reuse exact saved meanings,
prominence answers and comparisons where available.

No cost reduction or hierarchy-quality improvement has been measured for this
draft. Compare actual finished hierarchies and total API-equivalent cost,
including meaning generation, PPv35, traversal and consolidation, before making
either claim.
