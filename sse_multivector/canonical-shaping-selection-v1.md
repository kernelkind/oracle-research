# Selecting local entries to reduce overcrowding

The user approved selecting promising unused local entries when a canonical
group has too many children. A nomination still follows ordinary local versus
canonical graph traversal. Selection does not establish containment, placement,
equivalence or a preferred answer.

The [bounded selector](canonical_shaping_selection.py) ranks entries by their
second-highest cosine against eligible immediate siblings' subject vectors.
An exact match to one sibling therefore cannot alone dominate the ranking.
Each local entry retains its own source identity and native eligibility, even
when several entries have identical headings. Candidate headings share vector
computation; this does not merge entries or their meanings. Fewer than two
eligible siblings gives no grouping score. Similarity does not determine which
topic is broader.

Preparation excludes already processed entries, uses the native same-note and
mapped-parent eligibility rules, and preserves source hashes for the original
state, finished-menu candidate, corpus, implementation and SSE receipt sources.
It rejects changed canonical meanings/supports and menu links without original
graph reachability. It makes no teacher calls or new encodings. The bounded
implementation permits 4,096 local entries and 512 siblings; it scans saved
vectors and is not a corpus-scale retrieval index.

## First trial: Food preparation

The current ASv6.100 / Bootstrap-v96 / Compare-v48 fifty-note menu has seven
children beneath Food preparation C005. Preparation ranks all 1,386 unused
local entries and selects **Cooking**, local entry 4 from N011:
`51209f1582fd9e8e5f440278ba79e399f65c8b020fc0d43f07f1e67005a8bf70`.
Its context says: “How to cook” establishes cooking as a subject. The original
post asks how to cook ham-and-cheese mochi bread from Japanese convenience
stores. Its strongest eligible sibling cosines are Cooking appliances C014
0.8488, Grilling C012 0.7791 and Cookware C008 0.7612. The ranking score is 0.7791.

The ignored frozen nomination is
`target/canonical-shaping-selection-v1/food-preparation-v1.json` in the retained
task worktree `oracle-mvp-canonical-shaping-selection-v1`. The
[trial source](shr_single_pair/hierarchy-shaping-food-preparation-v1.json)
selects this original local root and the original producer/comparison specs.
It assigns no canonical destination. The trial must enable graph search;
the older sixteen-node shortlist is not a substitute.

**Status: live traversal completed; the proposed menu does not improve shape.**
The independently generated Bootstrap-v96 meaning was frozen before normal
Compare-v48 graph traversal. No destination or positive answer was prescribed.
The original ninety-nine-node graph was copied into a separate trial; its
existing headings, meanings and supporting entries remain unchanged.

Traversal added Cooking as C125 below Food preparation C005 and above all seven
of C005's retained menu children. All ninety-seven eligible canonical nodes were
settled: ninety-two direct comparisons and five relationships inferred through
the native traversal's transitivity rules. The two same-note exclusions were
preserved. The older shortlist policy was used only to prepare an unexecuted
seed before the native graph-search fork; no shortlist comparison was run.

The [measured menu definition](shr_single_pair/hierarchy-shaping-food-preparation-menu-v1.json)
preserves every original menu heading, meaning, support and branch outside this
one insertion. The native shape and audit commands report:

| Measure | Original menu | Cooking inserted |
|---|---:|---:|
| Food preparation choices | 7 | 1 |
| Cooking choices | absent | 7 |
| Nodes / edges | 70 / 74 | 71 / 75 |
| Equal-note-set edges | 0 | 1 |
| Structural violations | 3 | 4 |
| Reachable and individually isolated notes | 50 | 50 |
| Mean shortest selections to an individual note | 2.68 | 2.86 |
| Maximum shortest selections | 4 | 5 |

Nine individual notes require one additional selection. C005 and C125 each
represent eleven distinct notes in the proposed menu, so their edge does not
narrow the note set. The original C005 menu represented ten notes; adding the
incoming Cooking support brings N011 into this branch. The seven-root and
thirteen-child Food violations remain. Thus the nomination produced valid
model-judged containment but merely relocated overcrowding and added depth.
This menu is not adopted, and the other agent's saved hierarchy is untouched.
No UI was updated.

The [native usage source](shr_single_pair/hierarchy-shaping-food-preparation-usage-v1.json)
accounts for one meaning request, ninety-two comparison requests and four cache
warmups: **ninety-seven actual attempts**, with no reuse, failure, retry or
missing usage. GPT-6.1 Sol medium ran at runtime concurrency four. Saved usage
is 152,309 uncached input tokens, 69,248 cached input tokens, zero reported cache
write tokens and 12,396 output tokens. The 1,500 reasoning tokens are already
included in output. Complete catalogue/API-equivalent cost is **$0.4355028**;
subscription incremental cash cost is zero, not an API invoice. The native
summary reconciles all ninety-seven attempts with the persistent trial counter.
There is no matched baseline cost experiment and no selection-savings claim.

Retained ignored evidence under `target/canonical-shaping-selection-v1` in the
task worktree includes the frozen nomination `food-preparation-v1.json`, native
trial `cooking-traversal-v1`, proposed menu and audit `cooking-menu-v1`, and
receipt-validated accounting `usage-v1.json`. The worktree remains necessary
because saved source and receipt paths bind to it.

The second-highest cosine criterion detects resemblance to multiple siblings,
but does not distinguish grouping two to six siblings from grouping all seven.
For this target, a useful new intermediate parent must reduce the old choices,
keep its own choices within six, and preserve strict note-set narrowing and
useful route lengths. **Suggested next investigation, not implemented:** rank
unused locals for grouping a proper subset of the overcrowded siblings. This
single trial does not establish general selection accuracy or rejection of SSE.

Verification at this checkpoint: eighty-four selector, graph-search,
construction, selection-regression, vector, native audit/shape and native usage
tests passed. The live native audit and usage commands also completed, with the
counter reconciled and generated evidence ignored.

## Offline subgroup investigation

Following the user's approval to investigate clustering, `--method subgroups`
adds an experimental read-only screen. The previous second-best method remains
the default. The new screen selects no local automatically and makes no teacher
requests or new encodings. Both stages reuse the original ASv6.100 source-bound
subject vectors, not mask or explicit-meaning vectors.

For each sibling, take its nearest siblings in SSE subject cosine to propose
groups of two through six nodes. Exclude the full sibling set, deduplicate
identical groups and permit overlapping groups. This produces at most five
groups per sibling, rather than enumerating every subset. Order groups by size,
then their mean pairwise cosine, so small coherent groups are examined first.
One two-child group would reduce seven immediate choices to six if a new parent
actually contained exactly those children. Thirteen choices require multiple
groups under the six-child limit; no single allowed group can solve them.

For each group, rank unused eligible locals by:

`weakest cosine to any group member − strongest cosine to any outside sibling`

Every group member must be eligible for that particular local entry. Outside
siblings remain in the contrast even when they are ineligible; excluding them
could make a broadly matching heading appear selective. Equal local headings
share vector calculation but keep separate source identities. The report retains
the member affinity and strongest outside match alongside the difference:
a positive difference alone can still describe weak matches to everything.
There is no fitted threshold, learned semantic direction or inferred containment.

The native frozen preparation produced these ignored reports against the
original complete graph and menu, each considering 1,386 unused entries:

| Target | Siblings | Proposed proper subgroups | Artifact |
|---|---:|---:|---|
| Food preparation C005 | 7 | 18 | `subgroups-C005-v1.json` |
| Food C001 | 13 | 52 | `subgroups-C001-v1.json` |
| Roots | 7 | 25 | `subgroups-roots-v1.json` |

All artifacts are under the retained task worktree's
`target/canonical-shaping-selection-v1`. Sources, vectors and implementation
are hashed; no input, original graph, meaning or menu is changed. The bounded
research limits remain 4,096 locals and 512 siblings. Preparation uses dense
cosines over unique local headings and the selected sibling group, followed by
group scoring. This is not a corpus-scale retrieval implementation.

### Findings

The closest Food preparation pair is **Cookware C008 + Cooking appliances C014**
(cosine 0.8707). Its first local candidate is **Crockpots**, N014 entry 1,
`821011b60ccabb942d2540b722ea5d88f15484c407bfb77c9b6318c851eedb9f`.
Its weakest member cosine is 0.7018 and strongest outside cosine is 0.5649,
giving 0.1369. The context names a crockpot holding beef stew; its local branch
descends to that crockpot and the author's possession of it. This is strong
equipment resemblance, but supplies no evidence that Crockpots is broader than
Cookware and Cooking appliances. Treating it as a group parent would be an
unsupported direction judgment, not a selection success.

For this pair, **Cooking N011 entry 4** falls from first under the original
second-best method to sixty-second under the separation score (−0.0179).
However, Cooking ranks first for **Cookware + Grilling + Cooking appliances**
(0.1128). Its already saved B96/C48 comparisons contain all seven original menu
children, including those outside this proposed subgroup. These original nodes
are exactly the prior live trial's before-state. This is direct saved evidence
that a proper vector cluster and positive separation do not establish selective
containment. No new sample was taken or historical answer changed.

Other leading nominees show the same missing direction:

| Proposed sibling group | Leading unused local | Separation | Weakest member cosine |
|---|---|---:|---:|
| Food smoking + Grilling | BBQ chicken pizza, N020 entry 1.1.1 | 0.0963 | 0.4713 |
| Food preparation + Food dishes | Ingredient additions, N028 entry 11 | 0.0982 | 0.6599 |
| Coffee + Slush drinks | Caffeine, N034 entry 1 | 0.2127 | 0.4170 |

These are nominations, not new negative gold or completed model comparisons.
An agent review finds no established parent meaning for these groups. Other
groups produce clearly weak affinities: the Bread preparation + Rosemary pair
offers Raised garden beds with weakest cosine 0.2262, and some larger groups
rank unrelated subjects because their outside similarities are even lower.

The available-heading inventory also matters. None of these fifty notes has an
exact AS heading Cooking equipment, Kitchen equipment, Equipment, Cooking
methods, Beverages or Drinks. Meals occurs once and is already processed.
This does not exclude differently worded possible parents, but shows why an
intuitively convenient group name cannot simply be nominated from this pool.
Selection cannot manufacture a local entry absent from the supplied hierarchies.

**Conclusion:** clustering is useful for proposing which children to group;
the tested cosine difference is insufficient for choosing their parent. No
construction policy or live hierarchy changed, and no model calls were made in
this investigation. Suggested next investigation, requiring approval: combine
cluster retrieval with evidence of broader scope from original local ancestor
relationships, while retaining normal traversal as the sole relationship judge.
Exact unused ancestors of the current children's own supports were absent in
the initial audit, so this would need to search analogous local branches rather
than assume an exact witness exists. If no supported parent is available, retain
the crowding limitation instead of inventing containment.

The original selector source is recoverable at commit `c9f0a6f5`; an ignored
`selector-c9f0a6f5.py` snapshot preserves its hash from the first nomination.
The newer subgroup artifacts bind to the updated implementation separately.
The minimal new behavior test first failed because subgroup ranking was absent;
twelve selector tests and fifty-six combined selection/traversal/vector tests
now pass. All three real preparations completed, and their protected hashes
were checked alongside the preserved original selector snapshot.

Run the Food preparation screen with the NumPy-enabled environment:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 sse_multivector/canonical_shaping_selection.py \
  --reference-project ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1 \
  --state ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/regrouping-roots-v1/state.json \
  --menu ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/menu-v2/state.json \
  --parent C005 \
  --method subgroups \
  --output target/canonical-shaping-selection-v1/subgroups-C005-repeat.json
```

When a new intermediate parent groups m existing siblings, replacing their
direct choices with that parent can reduce the original group by m−1 choices.
Measure the actual completed placement and menu, including any new overcrowded
group and added depth. A placement elsewhere or equivalence is not automatically
a shaping improvement. Both existing and new note routes must remain reachable,
and every retained downward step must narrow the distinct-note set.

Repeat nomination into a fresh output file:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 sse_multivector/canonical_shaping_selection.py \
  --reference-project ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1 \
  --state ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/regrouping-roots-v1/state.json \
  --menu ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/menu-v2/state.json \
  --parent C005 \
  --output target/canonical-shaping-selection-v1/food-preparation-repeat.json
```

Use the project's NumPy-enabled Python environment if the system Python lacks
NumPy. Generated nominations are ignored artifacts, not semantic gold.
