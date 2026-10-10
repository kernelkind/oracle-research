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

## Using siblings' explicit meanings

The user requested repeating the screen with SSE encodings of the siblings'
explicit meanings. The opt-in `--sibling-meanings DIRECTORY` uses the saved
auxiliary `meaning` representation: encode the immutable meaning alone and pool
its entire text. These are auxiliary SSE encodings, not MP masks. Each vector is
bound to its canonical ID and exact heading/meaning, so identically titled nodes
can retain distinct representations. Preparation verifies the native state,
whole-meaning byte spans, request/receipt hashes, checkpoint, model and dimensions.

Only the siblings' representation changes. Both their pairwise clustering and
their cosine against unused local title vectors now use the explicit meaning.
The 1,386 local entries, subject vectors, eligibility, score, group sizes and
ordering stay unchanged. Their explicit meanings have not been generated.
There is no automatic nomination or graph modification.

The existing ASv6.100 auxiliary vectors cover every node of this exact native
state. All three preparations therefore needed **zero encodings and zero model
calls**. Reports under `target/canonical-shaping-selection-v1` bind to the
updated implementation and existing auxiliary sources separately from earlier
title-only reports:

| Target | Title groups | Meaning groups | Identical member sets | Meaning report |
|---|---:|---:|---:|---|
| Food preparation C005 | 18 | 17 | 7 | `subgroups-meanings-C005-v1.json` |
| Food C001 | 52 | 58 | 7 | `subgroups-meanings-C001-v1.json` |
| Roots | 25 | 25 | 15 | `subgroups-meanings-roots-v1.json` |

The full meanings produce substantially different neighbors:

- Food preparation's nearest pair changes from **Cookware + Cooking appliances**
  (title cosine 0.8707) to **Bread preparation + Rosemary** (meaning cosine
  0.7623). The cookware/appliance meaning cosine is 0.5230, and that pair is no
  longer proposed as a two-member group. Both Bread preparation and Rosemary's
  meanings explicitly mention sourdough bread; that shared detail is a plausible
  explanation for their attraction, not a proven causal isolation.
- **Food smoking + Grilling** remains a pair, with meaning cosine 0.6224.
  Its first unused candidate changes from **BBQ chicken pizza** to **Outdoor
  grilling**. This nomination still establishes no broader-parent direction.
- The existing **Cookware + Grilling + Cooking appliances** group remains, but
  its first unused candidate changes from **Cooking** to **Desks**, with weakest
  member cosine only 0.0705. Its positive separation of 0.0405 illustrates why
  separation alone is insufficient evidence of useful affinity.
- The nearest root pair changes from **Coffee + Slush drinks** to **Food +
  Gardening** (meaning cosine 0.7222). Food's meaning includes sourcing and
  cultivation; Gardening's includes food production and produce storage.
  Those overlapping aspects supply similarity without establishing containment.

Thus the experiment establishes sensitivity to the full supplied meaning, but
does **not** establish better parent selection or better hierarchy quality.
It also uses an asymmetric representation: local titles against canonical
meanings. No comparison outcome or shaping success is inferred from these
rankings. The previous title-only default remains unchanged.

Eighteen selector/receipt tests and sixty-two combined selector, traversal,
construction, regression and auxiliary-vector tests pass. The new behavior test
first failed because sibling-vector replacement was unsupported. Native
preparation completed for all three targets and protected source hashes match.

Repeat this controlled screen, with saved vectors and no inference:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 sse_multivector/canonical_shaping_selection.py \
  --reference-project ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1 \
  --state ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/regrouping-roots-v1/state.json \
  --menu ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/menu-v2/state.json \
  --parent C005 \
  --method subgroups \
  --sibling-meanings ../oracle-mvp-hierarchy-candidate-rankings-v1/target/candidate-ranking-as100-v1/meaning-vectors \
  --output target/canonical-shaping-selection-v1/subgroups-meanings-C005-repeat.json
```

Suggested next investigation, requiring approval: keep these meaning-based
groups fixed and test local-parent retrieval using original local branch
evidence of broader scope. This directly addresses the missing direction while
preserving normal comparison traversal as the sole placement authority.

## Complete-link clustering of sibling meanings

Following the user's approval, `--clustering complete` tests a standard
hierarchical clustering algorithm on the same full-meaning vectors. It uses
SciPy's `linkage` with complete linkage and pairwise cosine distance
`1 - cosine`. Each sibling begins alone. The distance between two groups is
the greatest distance between any member of one and any member of the other;
the algorithm merges the closest groups and updates those distances. Thus a
merge considers every cross-group pair, rather than one starting sibling.
See the [SciPy linkage definition](https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.linkage.html).

All siblings take part in the complete clustering. Retain its proper groups of
two through six members for the existing unused-local search; the full sibling
set and larger groups are excluded. Groups are nested or disjoint. There is no
similarity threshold or prescribed number of final clusters. Canonical IDs are
sorted before clustering to make repeated runs in the same runtime deterministic;
the report records the SciPy and NumPy versions. A similarity tie can resolve
differently in a different library version.

This changes only group formation. The native inputs, full-meaning encodings,
1,386 unused entries, local subject vectors, eligibility and parent-candidate
score remain fixed. All groups shared with the earlier screen reproduce their
ranked candidates exactly: five groups for C005, seven for C001 and three for
roots. No comparison call, hierarchy edge, immutable meaning, menu or UI changes.

| Target | Earlier meaning groups | Complete-link groups | Artifact |
|---|---:|---:|---|
| Food preparation C005 | 17 | 5 | `subgroups-complete-meanings-C005-v1.json` |
| Food C001 | 58 | 9 | `subgroups-complete-meanings-C001-v1.json` |
| Roots | 25 | 5 | `subgroups-complete-meanings-roots-v1.json` |

The reports are under the retained worktree's
`target/canonical-shaping-selection-v1`. All three preparations used **zero new
encodings and zero model calls**. This is a reduction in candidate groups, not
measured inference/API-cost savings or established hierarchy-quality improvement.

Food preparation's seven siblings ultimately split into these two proper groups
before their final all-seven merge. The pie heading is abbreviated below; the
saved report retains its full original wording.

```text
Cluster: Cookware, Food smoking, Grilling, Cooking appliances
  Nested group: Cookware, Food smoking, Grilling
    Nested pair: Cookware, Food smoking

Cluster: Bread preparation, Rosemary, Pie preparation
  Nested pair: Bread preparation, Rosemary
```

| Group | Least member-pair cosine | First unused local candidate |
|---|---:|---|
| Bread preparation + Rosemary | 0.7623 | Soup |
| Cookware + Food smoking | 0.6580 | Chicken meat |
| Cookware + Food smoking + Grilling | 0.6155 | Outdoor grilling |
| Bread preparation + Rosemary + Pie preparation | 0.5626 | Dry white wine as an ingredient in mushroom risotto with shrimp |
| Cookware + Food smoking + Grilling + Cooking appliances | 0.4781 | Stove ignition |

The algorithm replaces overlapping alternatives with nested groups, but has not
established better parent retrieval. Bread preparation and Rosemary still cluster first;
their exact meanings share the sourdough example. Narrow ingredient and activity
entries still rank as possible parents of broader groups. These are agent-reviewed
selection concerns, not newly established comparison outcomes. The root clustering
also contains weaker groups, such as Coffee + Raves (0.3835) and a later
Food + Gardening + Mental states + Jokes group whose weakest pair is 0.0639.
Building a complete clustering eventually joins weak matches; retaining a formed
group does not automatically make it worth a model traversal.

The implementation uses SciPy's quadratic-time, quadratic-memory complete-link
algorithm over the selected sibling set. Existing bounded research limits remain
4,096 locals and 512 siblings. This does not introduce a corpus-wide all-pairs
clustering step. Parent retrieval remains the same bounded dense cosine screen.

Verification: the minimal seed-versus-whole-group test first failed because the
new clustering option was absent. Twenty-one selector/receipt tests and sixty-six
combined selector, traversal, construction, regression and auxiliary-vector tests
pass. All three actual native preparations completed and their protected hashes
match. The tested isolated runtime is Python 3.13.12, NumPy 2.5.2 and SciPy 1.18.1;
SciPy is needed only for the opt-in complete-link screen. The previous source
version is preserved at `bea0d94e` and ignored `selector-bea0d94e.py`, separately
from new source-bound reports.

Repeat with a NumPy/SciPy environment:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 sse_multivector/canonical_shaping_selection.py \
  --reference-project ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1 \
  --state ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/regrouping-roots-v1/state.json \
  --menu ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/menu-v2/state.json \
  --parent C005 \
  --method subgroups \
  --clustering complete \
  --sibling-meanings ../oracle-mvp-hierarchy-candidate-rankings-v1/target/candidate-ranking-as100-v1/meaning-vectors \
  --output target/canonical-shaping-selection-v1/subgroups-complete-meanings-C005-repeat.json
```

Suggested next investigation, requiring approval: use the two main C005 groups
to retrieve unused local ancestors above similar subjects. This targets broader
entries with original branch evidence instead of sending the current narrow
nominees through expensive traversal. Normal local-versus-canonical comparison
remains the sole placement authority.

## Searching original local ancestors

The user approved that investigation. The opt-in `--candidate-scope
local-ancestors` keeps all five complete-link C005 groups fixed and changes
only parent-candidate retrieval. The saved fifty-note corpus has 1,510 original
entries, 1,386 unprocessed entries, and 812 unprocessed entries with proper
descendants. Both processed and unused descendants can supply retrieval evidence;
only unused ancestors can be nominated.

For each unused candidate and each canonical sibling, take the highest cosine
between that sibling's full-meaning vector and any proper descendant's original
subject vector in the candidate's own local branch. Apply the existing group
score to these values: weakest match to a group member minus strongest match
to an outside sibling. Candidate eligibility stays native and unchanged.
Candidates without proper descendants are excluded from this opt-in search.

The report preserves the exact winning original path, including headings,
contexts, note ID and local entry numbers, for each member and the strongest
outside match. Exact-score ties use stable original entry identity. Every path
must stay in the same note and contain all original intermediate entries.
Similarity supplies only a selection cue; the source's original ancestor
relationship does not establish containment of a different canonical meaning.

**Result: this screen did not identify a parent nominee we recommend sending
through full traversal.** That is an agent selection assessment, not a set of
teacher rejections or semantic gold. No model calls or new encodings were made,
no local meanings were generated, and the graph, menu and UI remain unchanged.

The exact-title controls explain one limitation of the available source:

- Cookware, Bread preparation, Food smoking, Grilling and Cooking appliances
  each occur once as an original local root. Their local branches offer no
  original ancestors to nominate.
- Rosemary's only exact occurrence is beneath Food, which was already processed.
- The exact pie-preparation heading occurs on four branches. Three retain unused
  ancestors such as Food, Pies, Matcha and Cashews. Those witnesses concern the
  pie entry and do not establish a common parent for the full cluster.

Fuzzy descendant resemblance finds ancestors, but often follows one specific
story rather than identifying a broader shared topic:

| Cluster | First unused ancestor nominee | Weakest descendant cosine | Separation |
|---|---|---:|---:|
| Bread preparation + Rosemary | Puns | 0.4399 | 0.0983 |
| Cookware + Food smoking | Cooking potatoes, cabbage, green beans and eggs on the author's rocket stove | 0.5845 | 0.0725 |
| Bread preparation + Rosemary + Pie preparation | A tomato seeing salad dressing | 0.3669 | 0.1270 |
| Cookware + Food smoking + Grilling | Outdoor grilling | 0.5019 | 0.1232 |
| Cookware + Food smoking + Grilling + Cooking appliances | Rocket mass heaters | 0.4041 | 0.1909 |

For **Puns**, both member matches follow the same descendant about a tomato joke
that plays on salad dressing and getting dressed. The parent title itself has
cosines only 0.0970 to Bread preparation and 0.0510 to Rosemary. The higher
descendant matches therefore do not provide evidence that the parent topic
fits either full canonical meaning.

For **Rocket mass heaters**, all four matches follow the same descendant about
other people's enjoyment of experimenting with rocket stoves and rocket mass
heaters. The weakest parent-title cosine is 0.2299, versus 0.4041 through that
descendant. Further down the ranking, Charcoal grills has four different matching
descendant headings, but they are variants of the same note's cooking of potatoes,
cabbage, green beans and eggs. Counting distinct headings alone would not resolve
the scope problem.

Every top-ten nominee for the first four groups uses one descendant subject for
all member matches. For the four-member equipment/method group, six of the top
ten do so; the other four use the related rocket-stove cooking headings just
described. This is evidence of a retrieval mechanism's weakness, not proof that
all 812 unused parents are unsuitable or that no useful parent exists.

The frozen final report is
`target/canonical-shaping-selection-v1/subgroups-complete-ancestor-C005-v2.json`
in the retained task worktree. It also records exact local matches and their
processed/unprocessed ancestors. Its cluster memberships and coherence scores
exactly reproduce the preceding complete-link report. All protected hashes match.
The initial discovery is preserved separately as `subgroups-complete-ancestor-C005-v1.json`
and its exact `selector-ancestor-v1.py` source snapshot. Previous complete-link
source is recoverable at `2100de55` and ignored `selector-2100de55.py`.

Preparation computes original-entry versus sibling cosines once and propagates
each entry's scores to its unused proper ancestors. It avoids an all-pairs local
comparison matrix. Additional aggregation work depends on the number of original
ancestor links times the sibling count; retained paths are emitted only for the
bounded top candidate lists. The existing 4,096-entry / 512-sibling research bounds
still apply. This is an offline selection study, not an activated construction
policy or a corpus-scale retrieval index.

Verification: the minimal production-path test first failed because original
local ancestor retrieval was unsupported. Twenty-four selector/receipt tests and
sixty-nine combined selection, vector, construction and graph-search tests pass.
Tests cover a useful broad ancestor, exclusion of leaves, unchanged source paths,
processed descendant evidence, cross-note isolation, outside-sibling contrast,
original-context validation, incomplete paths and deterministic tie handling.

Repeat with the same NumPy/SciPy environment, without inference:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 sse_multivector/canonical_shaping_selection.py \
  --reference-project ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1 \
  --state ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/regrouping-roots-v1/state.json \
  --menu ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/menu-v2/state.json \
  --parent C005 \
  --method subgroups \
  --clustering complete \
  --candidate-scope local-ancestors \
  --sibling-meanings ../oracle-mvp-hierarchy-candidate-rankings-v1/target/candidate-ranking-as100-v1/meaning-vectors \
  --output target/canonical-shaping-selection-v1/subgroups-complete-ancestor-C005-repeat.json
```

Suggested next investigation, requiring approval: evaluate parent-title affinity
alongside descendant evidence, on these fixed inputs. The Puns witness shows
concretely why dropping the parent's own topic can promote an unrelated ancestor.
This would reuse existing vectors without generating meanings for hundreds of
unused entries; it still would not establish containment or guarantee a suitable
parent is available.

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
