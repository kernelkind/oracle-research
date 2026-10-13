# Hierarchy generation V3

Status: approved canonical generation mechanism, replacing V2. Constructor
implementation and hierarchy-quality qualification remain pending; the current
constructor still implements V2. Pair-consolidation wording remains an unreviewed
draft. This document does not authorize model calls. The user's personal outline,
`docs/notes/MY-NOTES_10-12.md`, remains read-only. The preceding mechanisms are
V2 and V1; earlier variants need no formal naming.

## Construction outline

Bootstrap establishes an explicit meaning for every original local L1 entry.
Pairing and consolidation then repeatedly form temporary synthetic grouping
nodes. Only the final groups become nodes in one canonical level. Intermediate
synthetic nodes do not become canonical nodes or browsing steps.

To construct children of a canonical node, start again from the original local
L1 entries associated with that node, reusing their meanings and vectors. Do not
expose the temporary binary grouping tree as the next canonical level.

Six is the maximum number of nodes per sibling family, not an exact required
count. Stop expansion when a node has two or fewer distinct notes (rule 3.2).
Other unresolved details are listed below.

## Step 1.1: establish the original local L1 meanings

Run Bootstrap independently for every original local L1 entry and preserve its
answer and producer evidence. If an answer has a null meaning, record that
entry as unresolved and continue the other Bootstrap requests. Wait to
construct the roots until every original local L1 has an established meaning.
Do not silently omit an unresolved entry or encode a null meaning.

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
When the node count is odd, carry the one unpaired node forward unchanged,
including its subject, explicit meaning, SSE vector and associated original
local L1 entries.

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

For root construction, supply no parent. For deeper canonical levels, supply
the current canonical parent's subject and fixed explicit meaning. Use that
same canonical parent throughout the temporary consolidation steps constructing
its children. Do not supply recursive ancestors or use a temporary synthetic
node as the enclosing canonical parent.

The proposed synthetic meaning must cover both supplied meanings and fit wholly
within the supplied canonical parent's fixed meaning when one is present.
There is no selection of a subset from a larger supplied sibling group.

The pair prompt must always generate a synthetic parent whose explicit meaning
covers both supplied meanings. Return only its subject and explicit meaning;
`null` is not an allowed semantic result. This rule is approved. Transport or
invalid-output failures remain separate, unresolved operational cases.

Use this same consolidation rule for every selected pair. Do not add a
separate equivalence judgment, comparison call or equivalent-pair branch.
The proposed special case of recognizing equivalence and copying one supplied
meaning was withdrawn; it is not part of this design.

The user deferred full prompt review.
[Hierarchy-pair-consolidation-v4](../../sse_multivector/shr_single_pair/Hierarchy-pair-consolidation-v4.md)
records the approved mandatory-output and optional-parent rules. Its overall
wording remains an unreviewed, untested draft. V3 added the optional parent;
V4 defines that input directly without relying on the term "canonical node"
inside the prompt. It uses the exact shared definition-writing rules-v6 from
Bootstrap-v129 and Consolidation-v21 through a pinned assembly; those prompts
and shared rules are unchanged. No prompt is activated by this draft.

Exact answer reuse must match the complete request, including the optional
canonical parent. A root-consolidation answer cannot be reused for a request
with a supplied canonical parent merely because its two input nodes match.

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
synthetic nodes' subjects and explicit meanings, plus the current canonical
parent when constructing a deeper level. Root construction has no parent.

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

If construction starts with more than six nodes and each consolidation
successfully returns one parent for its pair, the final node count is four,
five or six. The last consolidation starts with seven to twelve nodes: seven
or eight become four; nine or ten become five; eleven or twelve become six.
For seven nodes, three pairs produce three synthetic parents and the unpaired
node carries forward, giving four nodes total. This range is acceptable.

If the starting set already has six or fewer nodes, no consolidation is needed;
the final count can be below four.

## Step 1.9: make the final nodes canonical

Only the final nodes become canonical roots. Each retains all original local
L1 entries associated with it through the consolidations. Intermediate
synthetic nodes do not enter the canonical hierarchy. The same construction
is repeated separately for each canonical parent's next level, using that
parent's associated original local L1 entries.

## Steps 2.1–2.4: construct canonical L2

For each canonical root, take the exact original local L1 entries associated
with it through consolidation. Reuse those entries' Bootstrap meanings and
original SSE vectors. Do not use the intermediate synthetic nodes, original
local L2 nodes, or every L1 from the notes represented by that root.

Within this separate family, find the highest-scoring unique cosine pairs and
consolidate each pair. Generate SSE vectors for the resulting synthetic nodes
and repeat pairing and consolidation until six or fewer nodes remain. Only
those final nodes become the root's canonical L2 children. Each retains the
original local L1 entries associated with it. Process each root separately,
subject to the stopping rule below.

## Steps 3.1–3.2: repeat for deeper canonical levels

Repeat the same construction beneath each canonical L2 node to construct L3,
and continue recursively. At each canonical node, start from its associated
original local L1 entries and reuse their original meanings and SSE vectors.
The local input remains L1 even as canonical depth increases.

Stop expanding a canonical node once it contains two or fewer distinct notes,
counting each note once even when multiple associated local L1 entries come
from it. A node already containing one note is finished and is not expanded.

## Details still to settle

- Handling similarity ties and failed/invalid consolidation calls.
- Exact consolidation wording/output and meaning validation.
- Cases where further grouping does not provide useful refinement despite
  a node containing more than two distinct notes.

These open details are not implementation decisions.
