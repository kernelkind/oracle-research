# Hierarchy Approach 2 — draft v1

Status: future design under discussion. This document records the agreed details
below; it does not replace the current hierarchy implementation or authorize
experiments. The user's personal outline, `docs/notes/MY-NOTES_10-12.md`, remains
read-only. No code or prompt changes have been made for this design.

## Construction outline

Bootstrap establishes an explicit meaning for every original local L1 entry.
Pairing and consolidation then repeatedly form temporary synthetic grouping
nodes. Only the final groups become nodes in one canonical level. Intermediate
synthetic nodes do not become canonical nodes or browsing steps.

To construct children of a canonical node, start again from the original local
L1 entries associated with that node, reusing their meanings and vectors. Do not
expose the temporary binary grouping tree as the next canonical level.

Six is the maximum number of nodes per sibling family, not an exact required
count. The outline stops expansion when a node has two distinct notes (rule
3.2). Detailed boundary cases remain open.

## Step 1.2: SSE encoding of original local L1 entries

Use exactly this text layout:

```text
[[{local L1 subject}]]

{explicit meaning from Bootstrap}
```

The brackets mark the tokens selected for SSE pooling; they are notation rather
than literal text to encode. Pool only the subject. The explicit meaning is
unselected context available to the encoder.

## Step 1.3: cosine pairing within one family

Compute cosine similarity for every unordered pair of distinct vectors in the
current family's construction pool. Use all vectors in that pool, without a
candidate shortlist. Rank those pairs from highest similarity to lowest and
select non-overlapping pairs in that order: once a vector has been selected,
skip subsequent pairs containing it. Continue selecting pairs until no pair of
unused vectors remains. With ten nodes this selects five pairs, not four.

Families are separate. Do not pair entries belonging to different canonical
parents merely because their intended children are at the same depth. Root
construction has one pool containing the original local L1 entries from the
whole selected corpus. Subsequent construction uses a separate pool for each
parent, containing its associated original local L1 entries. Later temporary
consolidation rounds stay within that same family.

In the user's notation, L is distance from the root, with roots at L1. The S
numbers identify the nodes in the example; parent relationships identify their
families:

```text
L1S1
├── L2S1
└── L2S2

L1S2
└── L2S3

L1S3
├── L2S4
├── L2S5
└── L2S6
```

L2S1 and L2S2 are compared together. Separately, every pair among L2S4, L2S5
and L2S6 is compared. L2S3 has no partner in its family. The six L2 nodes are
never one pairing pool. This illustration establishes family boundaries; it
does not attempt to demonstrate the distinct-note stopping rule 3.2.

## Step 1.4: consolidation of a selected pair

Follow the current consolidation prompt's overall structure, adapted to exactly
two supplied nodes, each with its subject and explicit meaning. Generate a
synthetic parent for that pair rather than selecting two or more nodes from a
larger supplied group.

There is no supplied parent or ancestor input at any consolidation round. Do
not include the current prompt's parent-relative restrictions or its instruction
to select two or more siblings. Family separation is handled by construction
as specified above, not by providing a parent to the consolidation prompt.

Hierarchy-pair-consolidation-v1 was presented in chat, but the user deferred
review. Its wording and output contract remain unapproved.

## Step 1.5: SSE encoding of temporary synthetic nodes

Use the same layout and pooling boundary as for original local L1 entries:

```text
[[{synthetic subject}]]

{synthetic explicit meaning}
```

Pool only the synthetic subject. The synthetic explicit meaning is unselected
encoder context. As above, the brackets indicate the selected tokens and are
not literal text to encode.

## Steps 1.6–1.7: pair and consolidate the synthetic nodes

Use cosine similarity across all the synthetic nodes' SSE vectors within the
same sibling family to select the highest-scoring unique pairs, following the
non-overlapping selection in step 1.3. Consolidation generates a synthetic
parent for each selected pair, following step 1.4. Its inputs are the two
synthetic nodes' subjects and explicit meanings, without a supplied parent.

## Step 1.8: repeat until at most six nodes remain

Repeat steps 1.5–1.7 until there are six or fewer nodes in the sibling family.
Select all the highest-scoring unique pairs as described in step 1.3; do not
limit pairing to force exactly six nodes.

With ten nodes, generate ten SSE vectors and calculate cosine similarity for
all 45 distinct pairs. Select five non-overlapping pairs. If each consolidation
returns a synthetic parent, five consolidation calls produce five synthetic
nodes. Five is within the maximum, so no further consolidation is needed for
that family. These final nodes become canonical; intermediate synthetic nodes
remain outside the canonical hierarchy.

## Details still to settle

- Handling odd leftovers, similarity ties, equivalence and failed/null
  consolidation results.
- Exact consolidation wording/output, meaning validation and final canonical
  promotion.
- Complete distinct-note stopping behavior and cases where further grouping
  does not provide useful refinement.

These open details are not implementation decisions.
