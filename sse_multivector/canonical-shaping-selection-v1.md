# Selecting local entries to reduce overcrowding

The user approved selecting promising unused local entries when a canonical
group has too many children. A nomination still follows ordinary local versus
canonical graph traversal. Selection does not establish containment, placement,
equivalence or a preferred answer.

**Current investigation: reverse-engineer retrieval of an available parent.**
The user approved using Plant foods as a known candidate and investigating a
general rule for finding it. Title-pair similarity and original source branches
have been screened offline; the proposed priority is not activated. Missing
parent topics remain diagnostic references only. The earlier subgroup screens
use `--method subgroups --pair FIRST_ID SECOND_ID`. Original
local ancestry and SSE similarity remain retrieval evidence; ordinary traversal
still decides placement. No new scoring rule is approved by this investigation.

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
useful route lengths. The offline investigations below examine proper subsets
of these siblings. This single trial does not establish general selection
accuracy or rejection of SSE.

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

The tested cosine difference is insufficient for choosing a group parent. No
construction policy or live hierarchy changed, and no model calls were made in
this investigation. The local-ancestor screen below tests original branch
evidence, while retaining normal traversal as the sole relationship judge.
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

The later local-ancestor investigation tests retrieval using original branch
evidence with these saved meaning vectors. Normal comparison traversal remains
the sole placement authority.

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

The next investigation retrieved unused local ancestors for these five formed
groups. Those frozen results remain useful controls for the current pair-only
search; the user has moved the active investigation away from larger clusters.

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

## Pair-only investigation

The user approved focusing on pairs. `--pair FIRST_ID SECOND_ID` searches exactly
one supplied pair of distinct immediate siblings, bypassing both clustering
algorithms. Other siblings stay in the outside contrast. The same saved full
meanings, unused original local ancestors, descendant scores and native
eligibility remain fixed. No candidate is selected automatically, and the
previous CLI defaults remain available to reproduce existing evidence.

All 21 possible pairs of the seven C005 siblings were inspected separately.
Each report searches the same 1,386 unused local entries; 812 have proper local
descendants. This exposes 19 pairs absent from the preceding complete-link
ancestor screen. Both previously formed pairs reproduce their rankings and
exact source paths unchanged. No report invokes SciPy clustering, and all
protected hashes match. No inference, new encodings or graph/UI changes occur.

| Pair | Meaning cosine | First local ancestor nominee |
|---|---:|---|
| Bread preparation + Rosemary | 0.7623 | Puns |
| Food smoking + Grilling | 0.6224 | Outdoor grilling |
| Bread preparation + Pie preparation | 0.6005 | Half-and-half |
| Cookware + Cooking appliances | 0.5230 | Food preservation |

Pie preparation abbreviates C098's original heading without changing it. The
Food preservation nominee is entry 3 of note
`dc1d58a8e0d9036ad3e1f4e58e225733cdb9921fbca7c1a78c84aa4a7a2c7d4c`.
Its context is “The beets are vacuum-sealed and prepared for freezer storage.”
Its winning descendants are Preparation of food for freezer storage and Vacuum
sealing food. These provide resemblance to food-handling subjects, but no
source evidence that the parent topic encompasses both cookware and cooking
appliances. Its separation score is -0.0006, so an outside sibling matches
slightly more strongly than its weakest pair member.

Fourteen of the 21 first-ranked nominees use one descendant subject for both
members. Six first nominees have a weakest member cosine below 0.3; this is a
descriptive count, not a fitted threshold or semantic verdict. Three first
nominees have negative separation scores. Reviewing the returned topics still
does not identify a parent nominee we recommend for full traversal. This is
an agent selection assessment; no comparison outcomes or human gold were added.
Pair-only search simplifies the investigation but has not resolved parent
retrieval.

Reports are under `target/canonical-shaping-selection-v1/pairs-C005-v1`, named
by the two canonical IDs. The prior selector is preserved at `014a28f0` and
ignored `selector-014a28f0.py`. Twenty-seven selector/receipt tests and
seventy-two combined tests pass. The minimal test first failed because fixed
pair selection was unsupported; it now verifies a pair omitted by nearest
neighbors, eligibility, outside contrast, stable ordering, original ancestry
evidence and rejection of invalid pair IDs or conflicting clustering settings.

The option handles one selected pair per invocation; it does not enumerate all
pairs automatically. This bounded seven-sibling study exhausts its 21 pairs;
it is not an activated exhaustive-pair policy for large sibling groups.

Repeat one pair with a NumPy-enabled environment:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 sse_multivector/canonical_shaping_selection.py \
  --reference-project ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1 \
  --state ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/regrouping-roots-v1/state.json \
  --menu ../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/menu-v2/state.json \
  --parent C005 \
  --method subgroups \
  --pair C008 C014 \
  --candidate-scope local-ancestors \
  --sibling-meanings ../oracle-mvp-hierarchy-candidate-rankings-v1/target/candidate-ranking-as100-v1/meaning-vectors \
  --output target/canonical-shaping-selection-v1/pair-C008-C014-repeat.json
```

The user subsequently directed a manual parent search before further ranking
experiments. The Puns and Food preservation witnesses remain evidence that a
descendant match alone can promote an unrelated or narrower parent. First
establish that the desired parent meaning is available in the original entries;
otherwise its absence from the ranking cannot diagnose retrieval failure.

## Manual parent availability diagnostic

This uses the same frozen fifty-note ASv6.100 / Bootstrap-v96 / Compare-v48
snapshot, not another agent's newer construction. The selected pair is the two
retained C005 children **Cookware C008** and **Cooking appliances C014**. Their
fixed meanings are:

- C008: “Cookware is vessels designed to hold food while it is cooked using
  heat, including but not limited to cocottes and frying pans, for preparing
  meals such as a Full English Breakfast.”
- C014: “Cooking appliances are devices designed to cook food, including but
  not limited to induction hobs. The topic covers these appliances and their
  functions, design, installation and integrated components, which may include
  extractor fans.”

The manually proposed intermediate topic is **Cooking equipment**: physical
tools, vessels and appliances designed for cooking food, including descriptions
of those items' functions, design, installation and components. This is an
agent-proposed diagnostic meaning, not user-reviewed semantic gold or a new
local/canonical entry. It could group the equipment pair without requiring all
the food-preparation activities to be children. Ordinary traversal would still
be required for a real available candidate.

The source has 1,510 local entries from fifty notes. Its 124 processed entries
leave 1,386 unused entries, with 626 distinct headings and 1,206 distinct
heading/context pairs. All 626 unused headings were screened manually; plausible
alternatives then received detailed inspection of their source post, context
and local branch. This is not a claim that every unused context was separately
reviewed, nor a formal proof of semantic absence. It goes beyond searching only
for the exact phrase Cooking equipment.

| Original unused local entry | Evidence and availability assessment |
|---|---|
| Cooking, entry 4, note `51209f1582fd9e8e5f440278ba79e399f65c8b020fc0d43f07f1e67005a8bf70` | Context: “How to cook” establishes cooking as a subject. The post requests a mochi-bread recipe. This is the already tested broader activity topic; its saved traversal groups all seven children and relocates overcrowding. It is available, but does not supply the intermediate equipment meaning. |
| Product design, entry 4, note `33fd524783fedacfcfd6746dfcddd885ebb9577607bc8c40bb5a46ba2ad0384f` | Context: “The post describes the hob's sleek minimalist design.” This describes design rather than the general class of equipment. |
| Cooking functions, entry 5, same note | Context: “The hob incorporates several advanced cooking functions.” This describes capabilities rather than the equipment class. |
| Dishes, entry 5, note `f7ed481e9a564c95bf788dbcf34e0c098b32e7e5dffe2c841f769fb8cbc4f5e0` | Context: “Cleaned so many dishes from all the dishes i used doing all the above.” The post describes vessels used during salsa, yogurt, chicken and stock preparation. This does not establish a general class including induction hobs. |
| Food smokers, entry 2, note `c68026e7c9e1f97913aa4044eea86d60c22ce1d8469b315ebb8a124149235525` | Context: “The post names a smoker used for brisket.” This is one equipment type, rather than a parent of both whole generic classes. |
| Crockpots, entry 1, note `821011b60ccabb942d2540b722ea5d88f15484c407bfb77c9b6318c851eedb9f` | Context: “The author names a crockpot holding beef stew.” This is another equipment type. |
| Food preservation, entry 3, note `dc1d58a8e0d9036ad3e1f4e58e225733cdb9921fbca7c1a78c84aa4a7a2c7d4c` | Context: “The beets are vacuum-sealed and prepared for freezer storage.” This is the pair ranker's leading nominee, but it describes a process/purpose rather than the general equipment class. |

Other inspected possibilities included charcoal grills, J-tubes, rocket mass
heaters, extractor fans, worktops, knives, forks, recipes, brands, homesteading
and food security. Equipment types/components are narrower; the knife/fork
post establishes eating utensils; the remaining topics describe instructions,
makers or broader themes. None supplies the proposed intermediate equipment
meaning. These are manual availability assessments, not saved model rejections
or a prohibition on thematic containment.

**Finding:** no matching unused local topic was found for this diagnostic
parent. An available Cooking entry was already retrieved and tested, so the
finding is not that all possible parents are absent. The particular intermediate
topic appears missing from this candidate pool. A selector cannot retrieve an
entry that is not there; this pair alone cannot validate an improved ranker.
No synthetic topic, comparison, encoding, graph change or UI update was made.

### Available original-parent control

A separate manual positive control does have an original unused entry:

- Local **Plant foods**, entry **7.1**, note
  `fbd3796768e2bb12f215dd5d15a4e7377f6c9ce7849c01e6de166cafffd29a25`,
  under local Food. Context: “'Mostly plants' recommends plant foods; 'veggies'
  names vegetables.” The post recommends real food, moderate amounts and mostly
  plants, citing Michael Pollan's Food Rules. A proposed independent reading is
  plant-derived foods for human consumption; it has not been generated or frozen.
- Canonical **Avocados C062**: “Avocados as food: the edible fruits of the
  avocado tree, whose fleshy pulp is eaten.”
- Canonical **Cranberries C069**: “Cranberries are tart berries considered as
  food, encompassing edible forms and culinary uses, including but not limited
  to their use as an ingredient in sourdough bread with rosemary, brown sugar
  and cinnamon.”

Both canonical nodes have C001 Food as their original immediate parent. Their
supports come from different notes than the proposed local parent, so this
control does not depend on overriding same-note exclusion. The manual judgment
is that Plant foods can encompass both fixed meanings. This is a proposed
retrieval control, not user-approved gold or a model-verified placement.
**Cranberries C069 is omitted from the shaped menu**, so retrieving this pair's
parent would not by itself prove fewer menu choices or preserved hierarchy
quality. It separates an available original parent from the equipment topic
that appears missing, before any further retrieval experiment is designed.

The manual checks assert the corpus counts, original entry identity/non-use,
the pair's raw sibling relationship and menu membership. Frozen source SHA-256:

| Source relative to `target/hierarchy-as100-b96-c48-fifty-note-v1` | SHA-256 |
|---|---|
| `subjects/subjects.json` | `18370b4772fee22c8d11f49a505f20f781f163e0512a8f32473d487ebdc8849a` |
| `regrouping-roots-v1/state.json` | `853343330cac7db7c2cc9c5a2a333b590c05ca79c8563df0b7261850789a3aae` |
| `menu-v2/state.json` | `4fd0a99ed797b57f94a79d8c1c90ba5d81df72de071bec73d1372a0922e1dc8c` |

## Reverse-engineering available parent retrieval

The user requested inspection of the Plant foods control, then a general rule
for retrieving it. No teacher calls, new encodings, graph changes or selector
behavior changes were made. This is a candidate-selection investigation;
ordinary local-versus-canonical traversal still decides relationships.

### Why the previous score fails this pair

Inspecting all 23 original Food C001 children rather than the 13 retained menu
children keeps Cranberries C069 in the diagnostic. Native eligibility leaves
1,313 unused original entries for Avocados C062 + Cranberries C069. The title
versus full-meaning separation score puts Plant foods 962nd. Its components
are a weakest pair cosine of 0.4081 minus an outside cosine of 0.7271 against
Growing one's own food C094. Rain ranks first despite a weakest pair cosine of
only 0.0837: its outside maximum is even smaller, 0.0710.

The original-descendant version places Plant foods 616th of 769 eligible local
parents. It subtracts the 0.7740 Vegetables-to-Cabbage match from a weakest pair
match of 0.3638. Strong resemblance to Cabbage need not be a defect: Plant foods
can also be a useful parent of Cabbage. Pair inspection does not require the
prospective parent to exclude every other sibling.

Dropping this subtraction alone improves Plant foods to entry rank 167 using
its title and 247 using descendants. Full canonical meanings still promote
long culinary descriptions ahead of this short class heading. These are
retrieval failures, not comparison-prompt failures or semantic rejections.

### Word-independent rule under investigation

For a chosen sibling pair, score each eligible unused local heading by the
**weaker of its two SSE cosines against the siblings' original headings**.
Candidate and sibling headings are each encoded alone, using the existing
receipt-bound subject vectors. Do not subtract similarity to other siblings.
The weaker match rewards resemblance to both supplied subjects. It supplies
no evidence about containment direction.

For Avocados + Cranberries, Plant foods scores 0.4534 against Avocados and
0.4123 against Cranberries, giving 0.4123. It is the first eligible original
entry and the first distinct heading. No Plant foods-specific word, weight or
threshold enters the rule. The existing production `rank_candidates` function,
when supplied just these two canonical rows and the corresponding eligibility,
already implements this weaker-heading score; no new scoring component was
needed for the offline checks. The CLI's existing defaults remain unchanged.

Original branch structure improves the retrieval pool further:

1. Take the overcrowded canonical parent's heading, such as Food.
2. Find matching headings in the original local hierarchies, using
   case-insensitive exact wording for this screen.
3. Prioritize eligible unused entries anywhere beneath those original local
   headings, then order them by the weaker sibling-heading cosine.
4. Preserve a wider search outside those branches. Heading equality does not
   establish meaning equality, and a useful parent may originate elsewhere.

Food's original branches contain 186 unused entries with 105 distinct headings,
compared with 1,386 entries and 626 headings in the full unused pool. The
source-local relationship gives a retrieval cue; it does not become a canonical
edge or establish a relationship to either selected sibling. Canonical fixed
meanings, the local evidence and native eligibility remain unchanged.

### Broader screen and qualifications

Three panels reuse the same fifty-note source:

- **Plant foods:** all 15 pairs among Avocados C062, Tomatoes C064, Cranberries
  C069, Potatoes C087, Cabbage C088 and Green beans C089. Each fixed meaning
  establishes a plant-food role. The parent expectation is a manual assessment.
- **Vegetables:** Cabbage + Green beans, Potatoes + Cabbage, and Potatoes + Green
  beans. The unused Food → Plant foods → Vegetables entry supplies an original
  food-role candidate. These expectations are also manual assessments.
- **Cooking:** 36 pairs among nine original C005 children with explicitly saved
  positive Cooking C125 comparisons: C008, C010, C011, C012, C014, C070, C071,
  C072 and C098. These are model-judged positives, not human gold. No unverified
  Butter relationship is included. The previous Cooking insertion still failed
  the menu-shaping test; retrieving it is not automatically a useful regrouping.

The ranks below count distinct eligible headings. Computation shares a vector
for identical text; original entries, contexts and source IDs remain separate.
For example, Plant foods' full-pool worst heading rank is 8, while its worst
original-entry rank is 23 because other headings have repeated source entries.
An eight-heading retrieval is therefore not an eight-comparison cost claim.

| Panel | Pairs | Full unused pool: heading minimum, median / worst rank | Matching original branches: median / worst rank |
|---|---:|---:|---:|
| Plant foods | 15 | 4 / 8 | 2 / 3 |
| Vegetables | 3 | 1 / 3 | 1 / 1 |
| Cooking | 36 | 22.5 / 148 | Candidate absent from this pool |

Plant foods is first for Avocados + Cranberries in both pools. All 15 plant-food
pairs put it in the first three headings when using the original Food branches.
Vegetables is first on all three vegetable pairs in that pool. Restricting
the priority to **immediate** original children would instead exclude
Vegetables; using recursive original descendants matters.

Food preparation has no unused descendants beneath matching original headings
in this snapshot. The Cooking candidate is an independent original root, so a
hard source-branch filter would lose it entirely. Even unrestricted heading
minimum fails some Cooking pairs: Cooking ranks 134th for Grilling + Rosemary.
Heading average raises it to second, but performs worse on the Plant foods
panel; averaging full-meaning matches raises it only to sixteenth. Taking the
best title/meaning similarity for each sibling does not solve these panels
either. No single tested score is presented as a universal parent retriever.

**Proposed use:** prioritize original matching branches with heading-pair
minimum, while retaining a wider fallback. This retrieves the available plant
parents without forcing an exclusive two-child group. It is exploratory,
food-domain evidence from three parent headings, not independent validation,
an adopted scheduling policy or proof of end-hierarchy quality/API savings.
The stronger 18-case source-branch result concerns two parent headings and
does not generalize the unresolved Cooking cases away.

The screen reuses original 768-dimensional vectors and the saved full-meaning
vectors only for contrasts. Each selected pair needs two heading similarities
per candidate heading. A larger implementation should use existing vector
retrieval and indexed source-branch lookup; repeated corpus scans or automatic
enumeration of every sibling pair are not implied by this bounded study.
Large Food branches, retrieval recall and total construction cost remain open.

Ignored reports in the retained task worktree are
`target/canonical-shaping-selection-v1/parent-pair-retrieval-screen-v1.json`
(54 qualified controls, seven score contrasts, exact-entry ranks and source
hashes) and `parent-pair-source-branches-v1.json` in the same directory
(the source-branch contrast using the native two-sibling ranker). Source hashes
and SSE identities were verified before and after inspection. Existing saved
requests and results remain immutable. No new relation labels enter a prompt.

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

## Retained-root trial: Coffee + Slush drinks

The next user-authorized trial tested an actual retained browsing pair on the
same frozen ASv6.100/B96/C48 fifty-note baseline. Coffee C006 and Slush drinks
C039 were two of its seven menu roots. An unused original **Drinking** root
was nominated, then sent through ordinary independent meaning generation and
local-versus-canonical graph traversal. No destination or positive relation
was supplied to the model.

### Selection and original evidence

The selected local entry is number `8` in note
`26749e4bb8c7c7c2d53e303033b7f2641952894edd51bab1e9deafbf46be81b2`:

- Heading: **Drinking**.
- Context: `“I don’t drink……wine” explicitly concerns drinking, with wine
  singled out by the pause.`
- Original post: `I have to say I was rather impressed with dinner tonight.
  Lamb with steamed seasoned broccoli and baby potatoes really hit the spot.
  Though wine was available with the lamb I don’t drink……wine. 😈
  https://image.nostr.build/3a6a6b04d2263cfc5286255200859abab75efe502ae43fd664a25b93428e168c.png`

Neither selected canonical root shares this note. Apply native eligibility
before ranking original entries. The weaker of the two heading-to-heading
cosines puts Drinking fourth among both eligible original entries and distinct
headings: Coffee **0.4430**, Slush drinks **0.4375**, weaker match **0.4375**.
The eligible pool contains 1,261 entries and 561 headings. The first four
headings are Coffee, Coffee chains, Ice cream and Drinking. Selecting the
plausible broader entry from that shortlist was an agent assessment; this is
not an implemented automatic decision about which nominee to try.

This extends the available-parent investigation beyond the Plant foods
retrieval control. Root choices have no canonical parent heading whose original
local branches could supply the priority pool, so this trial uses the wider
heading-pair search. No new SSE encodings were made.

### Native placement and menu result

Bootstrap-v96 established:

> Drinking is the activity of consuming beverages by mouth, including but not
> limited to wine. The topic covers that activity and people's stated choices
> or abstention concerning beverage consumption.

Compare-v48 returned `local_contains_canonical` for both C006 and C039.
The ordinary traversal completed four comparison phases, queried 86 eligible
canonical nodes and inferred nine descendant relationships from existing
containment. It added **Drinking C125** as a root with no hold. These are native
model judgments, not new human gold.

The separate menu replaces the Coffee and Slush drinks root choices with
Drinking, which has those two children. All 70 previous menu headings, immutable
meanings, supporting entries and represented note sets are preserved. All
other existing menu edges are retained. Drinking's original supporting note
also remains attached to Drinking; no support is transferred to another node.

| Measure | Frozen baseline | Drinking menu |
|---|---:|---:|
| Root choices | 7 | **6** |
| Nodes / edges | 70 / 74 | 71 / 76 |
| Reachable and individually isolatable notes | 50 | 50 |
| Strictly narrowing edges | 74 | 76 |
| Equal-note-set edges | 0 | 0 |
| Structural violations | 3 | **2** |
| Mean shortest individual selections | 2.68 | 2.80 |
| Maximum shortest individual selections | 4 | 4 |

This fixes the root-choice violation without creating another structural
violation. It adds one selection for six notes; the other 44 shortest routes
are unchanged. Food C001 still has 13 children and Food preparation C005 still
has seven. The complete hierarchy is therefore not finished. The result is a
qualified shaping improvement under the approved six-choice limit, not a
reduction in every route length or proof of semantic accuracy/global optimality.

### Accounting, preparation and retained evidence

The trial made **92 fresh subscription attempts**: one meaning, 86 comparisons
and five cache warmups. There were no failures, retries or exact reuses. Native
usage is complete: 98,574 uncached input tokens, 100,224 cached input tokens,
zero reported cache-write tokens and 9,328 output tokens, including 809
reasoning tokens. API-equivalent saved-catalog cost is **$0.3004504**;
subscription cash charge is zero. This is the cost of one parent insertion,
not an operational-policy savings estimate against a matched full rebuild.
The shared 220-attempt allowance is reconciled at **189 used / 31 remaining**,
including the earlier 97-attempt Cooking trial.

The frozen baseline's original project code validates its saved shortlist
policy. The shared runner prepares growth with that project, then the native
`fork-canonical-trial --graph-search` switches the separate trial to traversal.
New compatible specs retain the exact B96/C48 prompts, schemas and all other
settings, omitting only the obsolete configurable concurrency field. The
shared runner supplies its internal fair queue. Failed preliminary preparation
sent no provider requests; its original source definition is retained as v1.
The successful source definition is `hierarchy-shaping-drinking-v2.json`.

Maintained sources are under `sse_multivector/shr_single_pair/`:
`hierarchy-shaping-drinking-v2.json`, `hierarchy-shaping-b96-bootstrap-v1.spec.json`,
`hierarchy-shaping-c48-compare-v1.spec.json`,
`hierarchy-shaping-drinking-menu-v1.json` and
`hierarchy-shaping-drinking-usage-v1.json`. The usage source includes both
trials so the persistent shared attempt counter reconciles without resetting.
Ignored native evidence is under `target/canonical-shaping-selection-v1/`:
`drinking-prepared-v2`, `drinking-traversal-v1`, `drinking-menu-v1` and
`drinking-usage-v1.json`. Receipts and baseline source bytes remain unchanged.

The reusable selection, native graph construction and menu-shaping suites
passed 39 tests at this checkpoint. No prompt, production selection policy,
other agent's hierarchy or review UI was changed.
