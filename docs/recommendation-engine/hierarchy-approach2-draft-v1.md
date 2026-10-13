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

The original outline targets six groups per family and stops expansion when a
node has two distinct notes (rule 3.2). Detailed boundary cases remain open.

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
skip subsequent pairs containing it.

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

## Details still to settle

- Vector text and selected tokens for temporary synthetic nodes (step 1.5).
- Handling odd leftovers, similarity ties, equivalence and failed/null
  consolidation results.
- How a round reaches the target group count without reducing past it.
- Consolidation inputs, meaning validation and final canonical promotion.
- Complete distinct-note stopping behavior and cases where further grouping
  does not provide useful refinement.

These open details are not implementation decisions.
