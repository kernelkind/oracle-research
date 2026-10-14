# HiGen V4 — root experiment draft

Status: approved root-test design and approved Consolidated-grouped-v1 wording.
The native constructor supports the root-only experiment explicitly; full V4
hierarchy construction is not implemented or activated. V3, V3.1 and V3.2 remain available.
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

## First 50-note root result

The approved root-only test completed on 2026-10-14 using Bootstrap-v133 and
Consolidated-grouped-v1, GPT-6.1 Sol medium, and unchanged HDBSCAN settings.
It reused HR20's complete Bootstrap answers and original vectors: 326 original
L1 entries, four null meanings retained as evidence, 322 construction inputs,
and all 50 notes represented before clustering. The encoder for generated
groups used the same checkpoint, base-model artifact, 512-token limit,
title-only pooling and Python 3.13.12 / torch 2.13.0+cpu / transformers 4.57.1 /
tokenizers 0.22.2 / numpy 2.5.2 environment. No Bootstrap calls were repeated.

| Round | Input nodes | Groups | Unassigned nodes | Notes before | Notes after | Notes lost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 322 | 25 | 183 | 50 | 46 | 4 |
| 2 | 25 | 2 | 3 | 46 | 46 | 0 |

Round 1 groups contain 139 original entries. Round 2 groups contain 18 and four
generated items. The final two roots are:

| Root | Generated title | Distinct notes | Associated original entries |
| --- | --- | ---: | ---: |
| C00001 | Society and the environment | 45 | 97 |
| C00002 | Human experience | 17 | 25 |

Sixteen notes appear under both roots; their union is 46. The four notes lost
in round 1 concern preparing sourdough bread, enjoying a raw-milk slush,
snacking on chocolate instead of cooking eggs, and a butler's recommendation
to eat burgers with a knife and fork. Exact IDs and complete source posts
remain in the frozen corpus and round summary.

The generated Parents and children, Nostr ecosystem, and Requests for input
items were unassigned in round 2 and discarded. Their notes survive through
other topics, so zero additional missing notes does not mean zero topic loss.

Agent assessment: initial grouping is promising, but the final roots are broad
and overlapping browsing choices. Society and the environment resulted from
consolidating 18 of the 25 generated topics. Note retention alone does not
establish useful root distinctions or semantic coverage. Inspect that complete
group and its proposed meaning before extending V4 below the roots. This is
an assessment, not a new human approval, prompt failure attribution or automatic
parameter change.

Native accounting: 27 fresh consolidation answers, two prefix warmups, 29
actual attempts, zero failures/retries, and complete reported usage. New-call
API-equivalent cost is $0.142840: 19,519 uncached input, 30,720 cached input,
10,073 output including 7,588 reasoning tokens, and zero reported cache writes.
This excludes the reused historical Bootstrap/encoder work and is not a cash
subscription charge or matched policy-savings claim.

Reusable definition:
`sse_multivector/hierarchy-runs/higen-v4-roots-v1/hierarchy.spec.json`.
Native evidence is retained in the isolated
`oracle-mvp-hierarchy-generation-v4-draft-v1` worktree under
`target/higen-v4-roots-v1/`: `trial/state.json`, `trial/run-summary.json`,
`trial/hdbscan-0000{0,1}/{request,result}.json`, all native teacher receipts,
new encoder receipts, and `usage.json`. The root experiment completed without
constructing children or refreshing a review UI. Offline validation passed 76
constructor/assembly checks, three V4 checks on combined main, retained-binary
reproduction of the earlier 27-group result, and complete native state/receipt
validation of this finished test. Retain the worktree for these frozen absolute
source and artifact paths.

## Native root-only test

Use `prepare-hierarchy`, `advance-hierarchy` and `run-hierarchy` through the
shared stable launcher, selecting `generation_policy` =
`hierarchy-generation-v4-roots` explicitly. The schema-1 definition adds
`bootstrap_hierarchy`, naming a saved V3.2 state with matching Bootstrap-v133
answers and original vectors, and `hdbscan_binary`, naming the retained
production `fine-segmentation-candidate` executable. Their hashes are frozen;
all other corpus, teacher and encoder controls retain the existing constructor
contract. Native preparation validates and reuses the saved Bootstrap producer
and encoder receipts without dispatching Bootstrap again.

Every group becomes one ordinary native `hierarchy_group_consolidation` case.
The shared runner owns scheduling, caching, usage and provider retries. The
constructor retains its runner-outage backoff, receipt checks and atomic
resumption. Root summaries expose `hdbscan_rounds` and
`notes_not_in_hierarchy`. Final nodes are roots even when they represent more
than two notes: this experiment never constructs their children. Discarded
members remain in the saved round evidence with their original associations.
