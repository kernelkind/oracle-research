# Continue manual section replacement to six roots

Status: completed six-root experiment, stopped at the requested observation
point; not an activated HiGen version.
The user requested continuing the same process until six roots exist, then
observing that result before settling complete-coverage or sixth-root rules.

## HiGen V5 — approved recursive design and native implementation

The user named this recursive design **HiGen V5**. The following decisions do
not change the completed six-root evidence or activate its implementation.
This completed manual experiment did not construct recursive children. The
subsequent native implementation is described in
[HiGen V5.3](../hierarchy-generation-v5.md). New definitions now default to
V5.3, which retains initially unassigned entries for later root rounds, ranks
sections by notes not already covered by existing siblings at each level, and
adds global untracked entries sharing HDBSCAN groups with completed siblings'
original members. The
historical V5 decisions and this completed manual evidence remain unchanged.

The subsequent V5 implementation used angular HDBSCAN with
`min_cluster_size = 2`, `min_samples = 3` and excess-of-mass selection, retaining
Bootstrap-v133 titles and explicit meanings. These are V5's recorded settings;
they do not relabel historical V4 parameter experiments. Investigating a real
below-line bend is deferred; it does not change the approved positive-bend rule.

For each final parent, use its complete accumulated set of assigned HDBSCAN
groups, including additions from every amendment. Do not use only the groups
from the parent's first version. Apply the same “custom magic” to the HDBSCAN
nodes and connections associated with that complete set: find the bend using
the middle 80% of merge-distance levels, choose epsilon between that distance
and the next smaller distance, split into sections, and repeat the existing
selection, grouped consolidation, replacement and amendment process to generate
the parent's children. Repeat recursively within each resulting child.

At every level, use the current node's own HDBSCAN tree when constructing its
next level. Build that tree fresh from its accumulated original entries,
including additions from amendments. Do not splice earlier trees together or
remap those entries to groups in the original whole-corpus run. The six-group
leaf stopping rule below still applies: a node already assigned six or fewer
groups exposes those groups as leaves, without constructing another section
level. In particular, Root 6 uses its six creation groups as leaves; its entries
spanning seven original groups does not change that decision.

Choose the largest eligible section by its number of distinct supporting notes.
Count each note ID once per section, including the original note associations
represented by any synthetic nodes in that section. Input-node and group counts
do not determine which section is largest.

Each synthetic input remains associated with its existing canonical node. It
acts as that canonical node's representative in later HDBSCAN runs. Entries
grouped with that representative belong to its associated canonical node and
amend that node, rather than becoming part of the new canonical node currently
being constructed. This does not authorize merging existing canonical nodes.
This association was already followed by all four saved amendments: Slot2v1
to v2, Slot2v2 to v3, Slot4v1 to v2 and Slot1v1 to v2.

Generate each group's title and explicit meaning from its member definitions
first. Canonical-node consolidation always receives the groups' generated
titles and meanings; never send original local L1 titles and meanings directly
to canonical-node consolidation. Preserve the group-definition stage and its
evidence even when exact saved group definitions are reused.

If a selected section contains exactly one group, reuse that group's generated
title and explicit meaning directly as the canonical node. Generate the group
definition first if it is missing; do not make an extra canonical consolidation
call with one group.

For canonical consolidation beneath an existing node, supply that enclosing
node's title and fixed explicit meaning as `parent`. The proposed child must
cover the supplied group meanings in full and fit wholly within that parent.
Omit `parent` when generating top-level roots. Historical requests, answers
and exact-reuse identities remain unchanged.

Each sibling lineup has at most six nodes. After selecting `k` children, if
the remaining sections number at most `6 - k`, turn each remaining section
directly into a child rather than continuing to select them one at a time.
For example, after the first child, five or fewer remaining sections can all
become children immediately.

When a parent has six or fewer assigned HDBSCAN groups, use those groups as its
leaf nodes, each with its generated title and explicit meaning. Expose their
notes directly; do not expand them into individual local L1 nodes.

If six children have been generated and groups remain outside those children,
discard the remaining groups as child-node candidates and retain their notes
directly on the parent, deduplicating note IDs. For example, while generating
children beneath L2S1, those notes remain attached to L2S1 and appear when
viewing L2S1's notes. The child limit must not remove those note associations.

### Approved cut fallbacks

For nodes with more than six groups, try the middle-80% bend rule first. If
there are fewer than three retained distance levels or no positive bend, use
the previous V4 six-section cut: split at successive merge distances, stopping
before the next split would produce more than six sections. Equal-distance
joins split together, so this cut can yield fewer than six sections.

If that cut also cannot produce two through six sections because a tied split
jumps directly from one section to more than six, use the six largest groups
as leaves and retain the remaining groups' notes directly on the parent.
Largest still means distinct supporting notes. Preserve the existing canonical
associations and the six-child limit when applying these fallbacks.

The shared numerical module now implements V5's cut and both fallbacks in
`hierarchy_hdbscan.select_sections`. It returns every section or group so the
constructor can select by distinct-note count and preserve leftover notes.
The numerical review tool still uses the original bend-only rule, and frozen
V4 construction still blocks on an impossible tied split. The recursive V5
constructor uses the shared runner and preserves native request reuse,
amendment histories, fresh original-entry child pools and direct leftover notes.
This implementation does not turn the manual screen into semantic approval or
an actual V5 experiment.

The fresh-tree rule also resolves amendments: use all accumulated original
entries when constructing the next nonterminal level. Synthetic inputs only
represent already-created siblings while constructing their current lineup;
they do not replace original entries in the pool for their own children.

## Starting evidence and round construction

Start from the [completed S10 replacement](food-drink-s10-synthetic-grouped-v1.md):
217 inputs, two retained synthetic roots, 39 HDBSCAN groups and 32 sections.
S07 contains the second synthetic root and four mental-state entries; it amends
root 2. S04 is the proposed third root, subject to the intervening rerun.

The user tentatively approved this round rule after Slot2v2 grouped with People
and related entries. Freeze one clustering and choose its largest section
without an existing synthetic root as the next new root. Also amend existing
roots that grouped with new entries in that clustering. Count distinct
supporting notes, expand synthetic nodes to original support, and use saved
section order for ties. Existing-root amendments do not occupy another slot.

The new-root and amendment definitions use disjoint sections of that same saved
pool, so their ready model batches can run concurrently. Validate all results,
apply the selected disjoint replacements together, encode only missing vectors,
then recluster. Stop after a completed round retains six synthetic roots. This
is a provisional experiment rule, not an assertion of complete coverage of
eligible notes or local entries.

Keep originally grouped inputs, even if a later run leaves them unassigned.
Exclude the 361 originally unassigned entries throughout. Preserve all original
associations, fixed definitions, native receipts and reused SSE vectors. An
unassigned synthetic root remains a root and a clustering input.

Use unchanged Hierarchy-consolidated-grouped-v1 and GPT-6.1 Sol medium through
the shared runner. For multiple groups, reuse exact native group definitions,
generate only missing group definitions, then consolidate those definitions.
For a one-group section, its group consolidation is already the root definition;
do not send an unnecessary one-definition consolidation. An exact existing
native group result can directly supply this replacement with its original
receipt and validated current membership, without a model call.

The replacement CLI's `roots` command exports retained roots separately from
current clustering assignments, with original support, distinct-note coverage,
and root-slot amendment history. Its SVG and full-definition Markdown do not
omit a root merely because HDBSCAN currently leaves it unassigned. These are
experimental views, not a refresh of the hierarchy UI or an official HR run.

The offline `sse_multivector.hdbscan_root_round prepare DIRECTORY --source FILE`
validates native section results sharing one exact frozen review and rejects
overlapping membership before creating the new pool. Its source contains
`schema_version: 1`, `replacement_review`, and a `proposals` array of native
`experiment`/`case` references. A proposal's optional `section` identifies an
exact saved original group reused directly in the current review. Each change
retains its producer receipt, removed inputs, original support and amendment
history. Model execution stays in the shared runner.

The initial continuation uses the isolated worktree
`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-food-drink-six-roots-v1`.
Its frozen model bindings remain unchanged. Round-support source work and later
runs use `oracle-mvp-food-drink-six-roots-rounds-v1` under the same directory.
Retain both worktrees' ignored `target/food-drink-six-roots-v1` evidence and their
referenced sources. Native usage summaries distinguish fresh calls from exact
saved definitions; API-equivalent cost is not an incremental subscription bill.

## Completed six-root snapshot

All four growth rounds completed. Slot2v2 was established first from the four
mental-state additions. The first growth round created Nostr and amended slot 2
with the ten People/Humans entries; the second created Coffee; the third created
Biology and daily life and amended Coffee; the fourth created Cognition and
expression and amended the first root. No deeper canonical level was generated.

| Slot | Version | Final title | Distinct notes | Original entries |
|---|---:|---|---:|---:|
| 1 | 2 | Food and Domestic Life | 58 | 117 |
| 2 | 3 | Humans and human life | 34 | 53 |
| 3 | 1 | Nostr ecosystem | 24 | 26 |
| 4 | 2 | Biological products and beverages | 29 | 38 |
| 5 | 1 | Biology and daily life | 21 | 28 |
| 6 | 1 | Cognition and expression | 20 | 26 |

Note counts overlap. The six roots together represent **89 of 94 eligible
notes**, with **288 of 367 originally grouped entries** associated with a root.
The remaining **79 original entries**, including five eligible notes absent
from all roots, remain in the input pool. All 367 original associations are
preserved exactly across roots plus remaining entries; the original 361
unassigned entries stay excluded. The source corpus contains 100 notes; the
original grouped-only inclusion rule makes 94 eligible for this experiment.
Reaching six roots therefore did not complete either note or entry coverage.

| Checkpoint | Input vectors | Selected groups | Sections | Epsilon | Notes under retained roots |
|---|---:|---:|---:|---:|---:|
| S10 starting point | 217 | 39 | 32 | 0.942519 | 71 |
| Slot2v2 amendment | 213 | 38 | 31 | 0.942519 | 73 |
| Round 1: three roots | 178 | 35 | 29 | 0.942519 | 76 |
| Round 2: four roots | 153 | 32 | 20 | 1.093721 | 82 |
| Round 3: five roots | 114 | 24 | 15 | 1.144814 | 86 |
| Round 4: six roots | 85 | 18 | 5 | 1.288263 | 89 |

The six retained roots and latest clustering are separate views. In the final
clustering G09 contains roots 1, 2 and 5, and S01 contains fourteen selected
groups. Roots 3, 4 and 6 are currently unassigned by HDBSCAN but remain accepted
roots and clustering inputs. This is not a semantic equivalence or containment
judgment. The selected epsilon increased as the pool changed; no isolated
experiment establishes which change caused the broader sections.

The names and scopes also broadened during construction. For example, Coffee
beverages became Biological products and beverages after joining tea,
tomatoes/tallow and drinking-related entries. Biology and daily life came from
chicken/egg and breakfast/morning/sleep groups. Preserve these actual outcomes
for review rather than silently substituting different groups or definitions.

## Actual cost and verification

The native `usage-final.json` summary covers the Slot2v2 amendment and four new
growth rounds: **10 fresh attempts, 10 valid results, zero failures, retries,
warmups or missing usages**. All use unchanged grouped-v1/Sol 6.1 medium.
There are 18,223 input tokens, zero cache reads/writes, and 6,094 output tokens
including 4,249 reasoning tokens. Fresh API-equivalent catalog cost is
**$0.097386**; incremental subscription cash charge is zero.

Seventeen distinct native original group definitions are reused as inputs.
These are source references, not seventeen reused dispatch cases; the runner's
case-reuse count is zero. Their historical costs, original Bootstrap work and
earlier S05/S10 calls are outside the fresh subtotal. Eight synthetic vectors
are newly encoded across five SSE jobs; retained input vectors are reused.
This is not a matched end-hierarchy quality or operational-savings comparison.

Round support was developed with a failing production-path test and landed at
12efc6a7. Its integration checks verify shared source identity, disjoint
membership, original eligibility, exact native result reuse and combined root
history; overlapping sections fail before a destination is created. A later
single-section continuation regression first failed on inherited round IDs,
then passed with metadata fix e3623abc. Seventeen focused/native checks passed
in the task/integration worktrees and on combined local main. Historical
experiment bindings remain unchanged; the metadata fix was integrated
separately.

The final ignored evidence directory is
`target/food-drink-six-roots-v1/round-04/recluster` in
`oracle-mvp-food-drink-six-roots-rounds-v1`. Files
`food-drink-six-roots-final.svg`, `.png`, `.md` and `.json` show the six retained
roots, complete fixed meanings, support and versions. The separate
`food-drink-six-roots-final-clustering.svg`, `.png` and `.md` show the latest
HDBSCAN tree and remaining input groups. Both SVGs were rendered and visually
inspected. Native plans, worker receipts, HDBSCAN results and source hashes are
preserved alongside them; the usage summary is one directory tree above at
`target/food-drink-six-roots-v1/usage-final.json`.

Keep both experiment worktrees and their referenced sources for immutable
receipts, vectors and absolute bindings. No official HR ID was assigned and
the hierarchy UI was not refreshed. The temporary metadata-fix worktree was
removed after its tested changes landed on main. Model calls stopped at the
requested observation point. Subsequent recursive-design decisions are recorded
above; implementing and testing that extension remains future work.
