# HiGen V4 — root experiment draft

Status: approved root-test design; Consolidated-grouped-v1 is a wording draft
awaiting user review. No V4 constructor is implemented or activated, and no
model calls have been made for this draft. V3, V3.1 and V3.2 remain available.
The V3.3 proposal is not part of this experiment.

## Inputs and grouping

Use the selected 50-note ASv6.100 corpus and Bootstrap-v133. Reuse exact saved
Bootstrap-v133 answers and encodings where available; preserve original local
L1 subjects and identities as evidence. Each construction item uses its
Bootstrap-generated title and explicit meaning.

SSE encodes the title, two newline characters, and explicit meaning. Pool only
the title; the meaning is unselected encoder context. Apply the same layout to
generated group titles and meanings in subsequent rounds.

Run HDBSCAN with `min_samples = 3`, `min_cluster_size = 2`, and the saved test's
default excess-of-mass group selection. This replaces greedy cosine pairing;
there is no cosine cutoff or V3.3 normal-consolidation phase.

For every group, supply every member's title and fixed meaning to
[Hierarchy-consolidated-grouped-v1](../../sse_multivector/shr_single_pair/Hierarchy-consolidated-grouped-v1.md).
Generate one synthetic title and meaning covering all supplied meanings. Do
not select a subset. Root requests supply no parent. Each generated item keeps
the union of its members' associated original local L1 entries.

Discard unassigned items from further construction in that round, preserving
their source associations and evidence. If six or fewer generated items remain,
use them as the roots. Otherwise, encode them and repeat HDBSCAN and group
consolidation with unchanged settings. Intermediate synthetic items do not
become canonical nodes. This first experiment generates roots only.

## Required measurements

For every round, record input-item count, group count and sizes, unassigned-item
count, distinct notes before and after grouping, and exact note IDs lost in that
round. Count each note once across all surviving groups, even when several
members or groups represent it. Preserve original-entry associations through
every generated item. Report final roots with their complete titles, meanings
and distinct-note sets; zero groups would mean zero retained notes, not a
successful browsing hierarchy.

The previously displayed 27 groups, 135 grouped entries and 46/50 represented
notes used HR14's Bootstrap-v129 meanings and original subject headings.
Bootstrap-v133 changes the encoded titles and meanings, so recompute the first
round rather than treating that old membership as the new test's starting
result. Keep the earlier result as a separate reference.

## Prompt relationship

Consolidated-grouped-v1 minimally adapts Pair-consolidation-v11 from exactly two
nodes to a group of two or more. It generalizes all coverage and restriction
checks to every member. The example, output fields, title requirements and
shared definition-writing rules are unchanged. Its pinned assembly references
the same shared rules-v6 used by Bootstrap-v133 and names Bootstrap-v133 as its
companion. Historical prompts and assemblies remain unchanged.
