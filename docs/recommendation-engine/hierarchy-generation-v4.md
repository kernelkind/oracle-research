# HiGen V4.2 — hierarchy from one HDBSCAN tree

New construction uses [HiGen V5.2](hierarchy-generation-v5.md). This document
describes frozen V4 settings, still-used experiment evidence and native resume
compatibility; it does not select V4 for new definitions.

Status: approved V4.2 setting; native construction is implemented. V4.2 changes
only `min_cluster_size` from two to four. All other V4.1 settings and stages
remain unchanged. HR23 completed using HR22’s exact 100-note inputs and saved
Bootstrap answers/vectors: 53 nodes, six roots and 93/100 notes. Native structural
validation and its review UI check passed; human semantic review is pending.
Official V4.1 runs HR21 (50 notes) and HR22 (100 notes) completed with native
structural validation and checked review UIs; human semantic review is pending.
Their parameters and commands are in
[the compact run index](hierarchy-review-commands.md).
The earlier V4 root-only experiment remains separate evidence below. Historical
V3 variants and V4 definitions retain their frozen policies on resume.

## Authorized parameter comparisons

V4.3 and V4.4 are experimental variants of the same V4.2 construction. Their
configuration is authorized for testing; neither is a new semantic approval or
replacement for the V4.2 baseline.

| Version | `min_samples` (including the entry itself) | `min_cluster_size` | Frozen policy |
| --- | ---: | ---: | --- |
| V4.1 | 3 | 2 | `hierarchy-generation-v4.1` |
| V4.2 | 3 | 4 | `hierarchy-generation-v4.2` |
| V4.3 | 4 | 2 | `hierarchy-generation-v4.3` |
| V4.4 | 4 | 4 | `hierarchy-generation-v4.4` |

The V4.3/V4.4 trials reuse HR23's exact ordered 100-note corpus, Bootstrap-v133
answers and original vectors. All other model, prompt, encoder, grouping,
section-cut and stopping settings remain the same. Existing requests, answers
and receipts remain immutable; exact grouped-consolidation answers are reused
when available. Only newly required section definitions need inference.

### Completed 100-note comparisons

| Run | Samples / minimum cluster size | Original groups | Displayed nodes | Notes represented | Maximum leaf depth |
| --- | --- | ---: | ---: | ---: | ---: |
| HR22 · V4.1 | 3 / 2 | 62 | 80 | 94 | 9 |
| HR23 · V4.2 | 3 / 4 | 42 | 53 | 93 | 6 |
| HR24 · V4.3 | 4 / 2 | 46 | 60 | 94 | 7 |
| HR25 · V4.4 | 4 / 4 | 39 | 52 | 90 | 6 |

All four retain at most six roots/children per section. These are native
structural results, not semantic approval. For the 92 notes shared by HR22 and
HR24, average shortest category selections to a note group fall from 4.4457 to
3.7391. For the 89 notes shared by HR23 and HR25, they change only from 3.1011
to 3.0899; HR25 has three fewer represented notes overall. These comparisons
exclude selecting or scanning individual notes within a group. Broad repeated
categories persist, so fewer groups or levels alone do not establish improved
browsing quality. Prompts, original meanings/vectors and all other parameters
remain fixed; newly required section definitions are single model draws.

Native HR24/HR25 accounting totals 49 new attempts, including 13 warmups, zero
failures/retries and complete usage. The incremental catalog subtotal is
$0.2652616 API-equivalent, not a cash subscription charge. Each run's exact
reuse and immutable receipts remain separate from new attempts; no matched
operational-cost savings are claimed. See the compact run index for definitions,
source checkpoints, retained evidence and complete per-run accounting.

## Approved V4.2 process

Use Bootstrap-v133's generated titles and fixed meanings for original local L1
entries. SSE encodes `title`, two newline characters, and `meaning`, pooling
only the title. Run HDBSCAN once with `min_samples = 3`, `min_cluster_size = 4`
and excess-of-mass selection. The size minimum counts original entries rather
than distinct notes. Preserve the selected groups, their ancestor connections
and the exact input/output evidence. Leave unassigned entries out of the
hierarchy; report lost entries and distinct notes rather than claiming complete
corpus coverage.

Use only those selected groups and the connections above them. Hide branches
with no selected-group descendants and skip ancestors with only one remaining
branch. Do not absorb unassigned entries when displaying a broader branch.

At the top, choose the first distance threshold that produces at most six
sections. Repeat within every displayed section containing multiple original
groups. If a section contains six or fewer groups, show those groups directly.
Merge equal-distance joins together; a cut can produce fewer than six sections.
These thresholds use angular mutual-reachability distance, not cosine cutoff.
If tied distances make a section impossible to split into two through six
children, retain the evidence and block construction rather than inventing a
partition or repeatedly retrying the runner.

Generate names and meanings from the bottom upward using
[Consolidated-grouped-v1](../../sse_multivector/shr_single_pair/Hierarchy-consolidated-grouped-v1.md).
First supply each original group's member titles and meanings. Then supply
each broader section's immediate children's generated titles and fixed meanings.
Every supplied meaning must be covered. No enclosing parent is supplied because
its definition is generated later from those children. Generated titles and
meanings are not encoded or reclustered.

Every displayed section becomes a canonical node. Preserve each node's
associated original local entries, deduplicating note IDs when counting notes.
Different sections can represent some of the same notes. Stop at the original
HDBSCAN groups and expose their notes directly, regardless of their note count;
there is no local L2 or further subdivision phase in V4.2.

All ready grouped-consolidation cases use the shared native runner. A broader
section can advance once its own children have valid answers without waiting
for unrelated groups. Preserve ordinary exact reuse, receipt validation,
provider retry limits, constructor outage backoff and atomic resume. Freeze and
validate the numerical sections, membership and canonical parent relationships
against the saved HDBSCAN result on advancement.

Select `generation_policy = hierarchy-generation-v4.2` in a schema-1 hierarchy
definition. Use the ordinary `prepare-hierarchy`, `advance-hierarchy` and
`run-hierarchy` commands. `hdbscan_binary` names the production executable.
Optional `bootstrap_hierarchy` reuses a matching frozen V3.2 or V4.1–V4.4
Bootstrap-v133 checkpoint and original vectors; without it, preparation creates
the ordinary Bootstrap batch followed by original SSE encoding. Teacher specs, source corpus
and local encoder controls retain their existing contracts.

Saved V4.1 and V4 root-only definitions retain `min_cluster_size = 2` under
their existing generation policies. Their requests, receipts, parameter
records and results are not relabeled as V4.2. A V4.2 run requires a new
definition and preparation; changing a frozen run's policy is invalid.

## V4.1 validation evidence

The V4.1 offline adapter reproduced the earlier 27-group walkthrough: six roots and
33 displayed nodes, ending at all 27 original groups. That reference used v129
meanings. V4.1 uses v133 inputs, so those historical memberships are a mechanical
regression control rather than the expected new hierarchy.

The saved Bootstrap-v133 first-round result also passes offline section
validation: 25 original groups, 31 displayed nodes, six roots and at most six
children per node. No teacher or encoder calls were made for this check;
section names had not been generated in that offline check. The constructor, numerical-cut,
assembly and saved-viewer regression suites pass 91 tests, including native
fresh preparation, independent readiness, exact reuse and atomic resume.

## Earlier V4 root-only experiment

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
