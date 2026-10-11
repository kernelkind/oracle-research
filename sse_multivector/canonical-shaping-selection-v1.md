# Selecting local entries to reduce overcrowding

The latest user-authorized test uses
[Hierarchy-consolidation-v10](shr_single_pair/Hierarchy-consolidation-v10.md).
It restores one instruction from v8: “Define the selected topic, not every
concept it mentions.” All other v9 prompt bytes remain unchanged. The latest
eight fresh GPT-6.1 Sol medium requests test Food preparation, Food, Cooking
appliances and Eating in two independent draws each. Six non-null proposals
receive bounded agent accepts; Eating returns reasonable nulls twice. Each
non-null proposal narrows its prospective note sets, although Food still leaves
twelve choices. No proposal is applied. The earlier four-request roots and
Mental states screen also remains preserved. These visible development cases
do not establish broader accuracy, the restored instruction's causal effect,
or a resolution of the disputed Bread/Cuisine cases.
The preceding matched v8/v9 panel has sixteen fresh valid GPT-6.1 Sol medium requests,
two draws for each of four complete sibling groups. Each prompt has four
qualified agent accepts on the clear controls and four uncertain disputed
judgments. All prospective local shape checks pass; no proposal is applied.
V9 uses 13.4% fewer input tokens and has 17.1% lower observed API-equivalent
cost in this panel. This does not establish broader accuracy or hierarchy
quality. One v9 output unnecessarily defines Bread inside its proposed meaning;
the simplification omitted the general rule against defining every mentioned
concept. V10 restores that rule without claiming a measured improvement.
Historical Bootstrap and consolidation versions remain fixed; Bootstrap has
not adopted the new wording. Bread/Food dishes and Cuisine boundaries remain
unsettled, and previous reviews remain preserved. No semantic improvement or
change in a verified failure rate is established.
See [the shared wording contract](#synthetic-parent-draft-and-shared-definition-wording),
[the completed containment screen](#expanded-consolidation-v3-containment-screen),
the [completed v4 proposal panel](#consolidation-v4-proposal-panel),
[the v5 revision record](#consolidation-v5-draft),
[the completed v5 proposal panel](#consolidation-v5-proposal-panel),
[the v6 example draft](#consolidation-v6-synthetic-example-draft), and
[the completed v6 panel](#consolidation-v6-focused-proposal-panel), and
[the completed consolidation audit](#consolidation-audit-v1), and
[the v7 revision and panel](#consolidation-v7-required-condition-revision-and-panel), and
[the v8 draft and evaluation correction](#consolidation-v8-draft-and-evaluation-correction), and
[the v9 definition-writing simplification](#consolidation-v9-definition-writing-simplification), and
[the matched v8/v9 panel](#consolidation-v8v9-matched-panel), and
[the v10 targeted restoration](#consolidation-v10-topic-definition-rule-restoration), and
[the v10 clear-control screen](#consolidation-v10-clear-control-screen), and
[the broader v10 screen](#consolidation-v10-broader-screen).
It remains isolated and has not changed the active construction policy.

The user approved selecting promising unused local entries when a canonical
group has too many children. A nomination still follows ordinary local versus
canonical graph traversal. Selection does not establish containment, placement,
equivalence or a preferred answer.

**Current investigation: select a useful parent for any subset of an
overcrowded sibling group.** The user clarified that the input is the whole
group, including roots; choosing a particular pair first is optional. Pair
examples are evidence for this broader selection problem. The latest offline
whole-group screen rejects estimating containment membership from a cosine
cutoff; its note-set check cannot fix incorrect predicted membership. The later
model nomination screen also fails the saved Cooking/Drinking contrasts in two
independent draws. Neither screen is adopted as a shaping rule.

The user explicitly clarified that improving these particular menus is a means
of discovering the rules, rather than the end goal. Plant foods retrieval,
Cooking/Drinking placements, held Food nominees and the Coffee shortcut
provide contrasting examples. Competing nominees are now inspected against
the actual retained browsing choices and saved placement outcomes. Title-pair
similarity and original source branches have been screened offline; proposed
priorities remain unactivated. New shaping rules below are proposals, not
approved changes to construction or its guards. Missing parent topics remain
diagnostic references only. The earlier subgroup screens
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
has seven. Under the then-approved six-choice limit, the complete hierarchy
remained unfinished. That limit is now a best-effort goal, so these counts alone
no longer establish that the hierarchy is unfinished. The saved result remains
a qualified shaping improvement under its original bound, not a reduction in
every route length or proof of semantic accuracy/global optimality.

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

The post-integration rerun exposed an existing order-sensitive assertion in
`test_uncertain_root_holds_child_before_unvisited_mapped_parent`: both roots
were requested, but their logged request order was reversed. The existing test
failed with `PYTHONHASHSEED=0` and passed with `PYTHONHASHSEED=1`. It now checks
the same exact two-root multiset, matching the neighboring mapped-parent test;
its hold reason, unchanged graph and unvisited-descendant checks remain intact.
No production traversal behavior was changed.

## Food sibling examples: deriving shaping rules

This continuation inspects the same frozen fifty-note source, saved native
answers and existing subject vectors. It makes zero new provider calls or
encodings and leaves the attempt allowance at 189 used / 31 remaining. No
comparison prompt, constructor guard or selector behavior changes.

### A missing nominee can be an excluded held entry

Two original entries appeared absent when looking only at unused entries:
**Meals** and **Processed food**. Both actually exist, and both had already been
attempted and held. The implementation excludes every processed entry from
nomination, including held entries; neither became canonical. The preliminary
absence assessment was corrected after inspecting their recorded status.

Meals is original root **5** in note
`dc1d58a8e0d9036ad3e1f4e58e225733cdb9921fbca7c1a78c84aa4a7a2c7d4c`.
Its context says: `“5 meals of sides in a pinch” identifies a meal-related use
for the beets.` The independently generated fixed meaning is:

> Meals are eating occasions and the food intended to be eaten as part of
> them, including but not limited to side dishes accompanying the main food.
> Meal components may be prepared or stored for later use, including when
> food is needed at short notice.

The saved comparison at `menu-growth-v1/step-076/experiment` establishes:

| Compared canonical node | Saved relation to local Meals |
|---|---|
| Food C001 | `canonical_contains_local` |
| Dinners C059 | `local_contains_canonical` |
| Food for a lunch box C058 | `local_contains_canonical` |
| Food dishes C020 | `uncertain` |

The uncertainty caused the entire Meals entry to be held. Its reason cites
Food dishes' descendants Bread and Salsa lacking a meal-use restriction. This
investigation preserves that answer and hold. The positives concern their
original frozen comparison inputs; they do not certify placement against the
current graph, whose descendant evidence has grown. Breakfast C018 was not
queried in that sixteen-node phase, so Breakfast + Dinners remains a proposed
control rather than a fully labeled positive pair.

The Dinners + Food for a lunch box pair is especially useful: both are retained
Food menu children, and both original comparisons to Meals are saved positives.
Using the weaker heading-pair SSE score with native eligibility:

| Candidate pool | Eligible entries / distinct headings | Meals heading rank |
|---|---:|---:|
| Unused original entries | 1,320 / 601 | Excluded as previously processed |
| Unused entries plus held entries, diagnostic only | 1,334 / 604 | **2** |

Meals scores 0.7929 against Dinners and 0.7092 against Food for a lunch box;
the weaker score is 0.7092. Lunch makers ranks first, demonstrating that
similarity alone still does not identify the containment direction or guarantee
a suitable parent. For Breakfast + Dinners, Meals ranks seventh among headings
and tenth among original entries in the expanded diagnostic pool.

Processed food is original entry **1.1** in note
`54dcdd65cdde0aa60951b640dd95fbff6d0e7497fcb87762c4ecd7939b502165`.
It was held at `coverage-children-v1/step-066/experiment`, also because the
Food dishes comparison was uncertain. For Cheese doodles C022 + Processed
food being harmful to the author C081, its source note also makes it ineligible
to compare with C081 under the existing same-note rule. Including held entries
in retrieval does not remove that second blocker. No exception is introduced.

**Selection implication:** distinguish an original parent topic that is absent,
one excluded by comparison eligibility, and one previously attempted but held.
Keep the latter's identity and blocking reason visible to the investigation;
do not silently treat it as nonexistent or automatically repeat its model calls.
This is a proposal for shaping-selection evidence, not approval to relax holds.
The ignored `food-pair-availability-v1.json` artifact records six bounded pool
contrasts with source hashes; it is a ranking diagnostic, not comparison input.

### Evaluate the affected groups together

The prior native audits distinguish useful regrouping from relocated
overcrowding. With K = 6, count the choices beyond six in each sibling group,
including roots, and sum them across the menu:

| Saved menu | Choices beyond six, summed across groups | Equal-note-set edges | Total shortest individual selections |
|---|---:|---:|---:|
| Frozen baseline | 9 | 0 | 134 |
| Cooking insertion | 9 | 1 | 143 |
| Drinking insertion | **8** | 0 | 140 |

Cooking moves all seven children into another seven-choice group, introduces
a non-narrowing step and increases depth. Drinking fixes the root group at
the cost of one additional selection for six notes. Neither counting a smaller
original group alone nor minimizing depth alone describes the approved goal.

For illustration only, start with Food's 13 children and replace m direct
choices with a new parent containing those m children. Without additional
rewiring, Food then has 13−m+1 choices and the new parent has m:

| Children grouped | New choice counts: Food / new parent | Choices beyond six in these groups: before → after |
|---|---:|---:|
| 2 | 12 / 2 | 7 → 6 |
| 8 | 6 / 8 | 7 → 2 |
| 13 | 1 / 13 | 7 → 7 |

These are arithmetic examples, not generated edges or semantic judgments.
A new parent may still have too many children while making useful progress;
requiring every intermediate grouping to be finished immediately would exclude
the eight-child example. Conversely, merely moving the entire list does not
reduce the remaining overcrowding. Actual placement may affect other branches,
so use the completed menu audit rather than just this local formula.

### Draft process suggested by the examples

1. Start with the whole overcrowded browsing group. Use available original
   local entries to nominate a broader topic for any useful subset of children;
   retain prior construction status and normal comparison eligibility.
2. Send the selected local entry through ordinary graph traversal. A similarity
   score or original local ancestry never supplies the canonical relationship.
   Keep blocked candidates separate from candidates that were never found.
3. Evaluate all affected groups together. Prefer a reduction in choices beyond
   K, preserve strictly smaller note sets at each downward step, and measure
   added selections. The new parent may contain more than two children.
4. Once choice limits are satisfied, favor fewer selections using already valid
   relationships. The approved shortcut rule remains relevant: direct choices
   may remain when there is room, rather than forcing every route through a
   new intermediate parent.

This is a draft to review, not a complete optimization objective. The ordering
of competing improvements and the acceptable depth cost remain open. The
existing semantic, immutable-meaning, note-coverage and uncertainty requirements
remain in force; no change to those requirements is inferred from this study.

## Overlapping sibling notes: checks for the draft shaping rules

This continuation uses the same ASv6.100 / B96 / C48 fifty-note source. It
makes zero provider calls and zero encodings; the allowance remains 189 used
of 220. The examples develop selection rules, not a repair or adoption of
this particular menu. No semantic judgments, canonical meanings, constructor
guards, prompts or production selection behavior change.

### Fewer choices can add an unnecessary selection

Coffee C006 already has six immediate choices. Second coffee C101 is both a
direct choice and a child of Additional coffee C102. The saved containments
therefore permit either route:

```text
Coffee C006
├── Second coffee C101                    [one note]
└── Additional coffee C102                [two notes]
    └── Second coffee C101                [the same canonical node]
```

The native `shape-canonical-trial` command produced a separate menu from
`shr_single_pair/hierarchy-shaping-coffee-shortcut-v1.json`, removing only
the direct C006 → C101 edge. It preserved the original 70 nodes, their
headings, meanings and supporting entries, every represented note set, and
all other menu edges. Every selected edge has a native saved containment
witness; the audit completed and reports the remaining violations below.

| Measure | Frozen baseline | Remove direct Second coffee choice |
|---|---:|---:|
| Coffee's immediate choices | 6 | 5 |
| Choices beyond six across all groups | 9 | 9 |
| Selections to isolate the Second coffee note | 2 | 3 |
| Total shortest selections across 50 individual notes | 134 | 135 |
| Retained nodes / edges | 70 / 74 | 70 / 73 |
| Non-narrowing edges | 0 | 0 |
| Reachable and individually isolatable notes | 50 | 50 |

Only note `862486d8ab23753c39aa9484b1beb52b51e59369f91eb037f2898c5ed9b1f75e`
has a longer shortest route: C006 → C101 becomes C006 → C102 → C101.
All other individual shortest lengths remain unchanged. The seven-root,
thirteen-choice Food and seven-choice Food preparation problems remain.
Neither menu satisfies the final requirements.

**Draft selection implication:** target overcrowded groups. Do not select
another grouping merely to reduce an already acceptable choice count when
the change only adds selections. The result supports keeping valid direct
shortcuts while they fit within K; it does not measure the reading cost of
five versus six options or prove that every shortcut is useful.

Evidence is retained in ignored
`target/canonical-shaping-selection-v1/coffee-shortcut-menu-v1/{state,audit}.json`.
The first command against the current project adapter stopped before creating
output because its comparison policy differed from the frozen trial. Using
the same shared runner with `--project-root` selecting the original source
project preserved that frozen contract and completed the shape. No policy
hash, frozen source or model receipt was altered.

### Count distinct notes, not the sum of child counts

The baseline menu contains these overlapping sibling pairs:

| Sibling pair | Left / right notes | Shared notes | Distinct union |
|---|---:|---:|---:|
| Cookware C008 / Cooking appliances C014 | 2 / 4 | 2 | 4 |
| Dinners C059 / Avocados C062 | 4 / 1 | 1 | 4 |
| Cuisine C016 / Food dishes C020 | 6 / 7 | 2 | 11 |

For Cookware and Cooking appliances, all two observed Cookware notes also
appear under Cooking appliances. Their fixed meanings still distinguish
vessels holding food during heat-based cooking from devices designed to cook
food. Their note-set overlap supplies no new canonical containment. The
previous diagnostic found no available unused Cooking equipment local topic;
none is invented or added here.

Avocados' single support note is also Dinners' own support note. The fixed
Avocados meaning concerns edible avocado fruits; Dinners concerns evening or
main meals, their composition and related preferences. The one shared note
does not turn those meanings into equivalent topics or establish a parent
relationship. Selection must retain both the topics and the normal semantic
comparison rather than deriving an edge from note-set inclusion.

For Cuisine and Food dishes, the combined observed coverage is eleven notes,
not thirteen. A group can reduce two visible choices to one even when their
notes overlap. Counting covered notes by addition would exaggerate the group
size; penalizing every overlap would exclude potentially useful groups.
No new parent or semantic answer is asserted for any of these three pairs.

### A nominated parent's own support matters

For a proposed parent, count the distinct union of its original supporting
notes and all retained descendants. Its note set is not necessarily just the
union of the two siblings used to nominate it. The earlier native Drinking
trial demonstrates this: Coffee contributes six notes, Slush drinks one, and
the original Drinking support adds a different eighth note.

As arithmetic diagnostics only, if a new parent groups just Cookware and
Cooking appliances and adds no other distinct note, it represents four
notes. Its edge to Cooking appliances would then be four → four. Likewise,
a parent grouping just Dinners and Avocados without another note would yield
four → four above Dinners. Both fail strict narrowing with those child
headings retained. If the parent's own support or another valid child adds
a different note, that conclusion can change. Its placement and all affected
note sets must be checked after normal traversal; pair overlap alone is not
a reason to exclude the nominee beforehand.

**Draft rule addition:** evaluate the actual resulting branch, counting
original support and recursive notes once. Require strict narrowing on every
retained edge, assess choice limits across affected groups, and record the
added selections. Do not substitute disjoint sibling notes, summed child
counts or fewer choices alone for these checks. These additions remain draft
selection guidance; this investigation introduces no automatic policy.

The reusable menu definition is tracked; generated evidence is ignored.
Protected corpus, raw-state and baseline-menu SHA-256 values match the earlier
record. Source comparison confirms that only the named shortcut is removed,
all 70 original node payloads are unchanged except parent lists, and all
represented note sets are identical. The native audit retains all 50 notes
and reports 73 strictly narrowing edges, zero equal-note-set edges and the
same three baseline structural violations. Individual and topic routes remain
structural measurements, not semantic certification or a complete model of
which note groups a user will request.

## Competing nominations for the same sibling pair

This is an offline continuation of the shaping-rule investigation. It reuses
the same frozen ASv6.100 / B96 / C48 source, production `rank_candidates`,
native eligibility and receipt-bound subject vectors. It makes no provider
calls, encodings, prompt changes or construction-policy changes. The shared
allowance remains 189 used / 31 remaining. These are candidate comparisons,
not a head-to-head model trial of every nominee.

### Similarity order and demonstrated shaping benefit differ

For retained roots Coffee C006 + Slush drinks C039, the weaker of the two
heading cosines gives this order among eligible unused distinct headings:

| Heading rank | Original local nominee | Weaker cosine | Existing evidence |
|---|---|---:|---|
| 1 | Coffee | 0.4669 | Context describes the author's lack of need for coffee; no saved placement for this specific unused entry. |
| 2 | Coffee chains | 0.4456 | Context names a coffee-chain hashtag; no saved placement for this entry. |
| 3 | Ice cream | 0.4421 | Context names ice cream in a list; no saved placement for this entry. |
| 4 | Drinking | 0.4375 | Completed native traversal and audit reduce root choices from seven to six, with six notes taking one extra selection. |

The first three are associated topics whose source evidence does not itself
establish that they contain the selected pair. They remain untested, not
model-rejected negatives. Drinking's measured benefit is already documented
above. Choosing only the highest cosine would fail to nominate that demonstrated
useful entry. Keeping four headings happens to include it in this example;
this does not establish four as a sufficient general shortlist size.

For Food children Dinners C059 + Food for a lunch box C058, the unused pool
starts with Lunch makers (0.7464), Meal planning (0.6630), Food (0.6459),
Lunchly (0.6168), then Author's clean, simple, healthy dinner today (0.6154).
The first nominee is original local entry 5.6 in note
`38862a72602118a848694796950dd35f2bb48770c085735f6a9d1abdb0f7fe8c`.
Its ancestor is **People**, and its context describes people making lunches.
Meal planning is an original root about the author's intention to plan meals.
Those original roles explain why close wording can nominate an associated
person or activity; they are retrieval evidence, not canonical rejections.

Meals is excluded from that unused pool because it was held. In the diagnostic
pool that also shows held entries, it ranks second at 0.7092. Native `show`
confirms both original saved pair answers are `local_contains_canonical`.
Its separate Food dishes uncertainty still blocks placement, and those answers
do not certify the current larger descendant contexts. Its four Dinners notes,
one lunch-box note and distinct original beet-post support would make six
distinct notes if only that pair were grouped. That arithmetic permits strict
child narrowing, but it neither resolves the hold nor establishes an actual
menu improvement. No alternative nominee is declared a successful parent.

For Cookware C008 + Cooking appliances C014, Cooking ranks first at 0.7612,
ahead of Crockpots (0.7018) and Charcoal grills (0.6050). Cooking's saved
complete placement is positive to the pair, yet its measured menu moves all
seven choices into another seven-choice group and introduces an equal-note-set
edge. Thus even a high-ranking, model-accepted broader topic can fail the
shaping goal. The other nominees remain untested; the earlier manual source
inspection did not find the proposed intermediate Cooking equipment topic.

### Use the displayed group as the shaping target

Only **Avocados C062** is retained in the browsing menu among the six topics
used in the earlier Plant foods retrieval panel. Tomatoes C064, Cranberries
C069, Potatoes C087, Cabbage C088 and Green beans C089 remain in the raw graph
but are omitted from that menu. The panel remains a useful retrieval control;
its excellent ranks do not establish removal of two currently visible Food
choices. Similar-looking raw topics elsewhere in the graph do not automatically
identify the group whose option count needs reducing.

The combined examples suggest the following draft selection process:

1. Inspect all immediate choices actually displayed in the overcrowded group,
   including roots. Find a useful parent for any subset of them; a fixed pair
   is an optional investigation, not a prerequisite. Keep raw-only retrieval
   controls separate.
2. Retrieve several eligible original entries. The existing second-strongest
   sibling cosine and the pair-heading screen supply experimental resemblance
   cues, without establishing broader scope.
   Use original branches as additional retrieval evidence, retaining a wider
   fallback. Keep original entry identities and prior held/tried status visible.
   No fixed shortlist size, threshold or automatic semantic filter is validated.
3. Send the selected original entry through ordinary traversal. Its eventual
   children may extend beyond the initially anticipated subset. Neither rank nor source
   ancestry supplies the relationship or a predicted number of children.
4. Assess the completed menu using actual valid placements: distinct-note
   narrowing, choices beyond K across affected groups, preserved coverage and
   added selections. An accepted broader topic alone is not shaping success.

No automatic ordering among untested competitors is adopted. The evidence
supports considering more than the first similarity result and distinguishing
untried, held, accepted-but-unhelpful and demonstrated useful nominations.
It does not establish comparative model accuracy for the untried entries.
Inspection covers three fixed pairs and their first few candidates, not all
possible sibling pairs or a corpus-scale retrieval benchmark. A larger system
should retrieve bounded candidates from existing vectors and source indexes;
this investigation does not propose exhaustive pair enumeration or repeated
full-corpus scans for every placement.

## Whole-group branch and estimated-shape screen

The user approved testing original-branch retrieval and an estimated grouping
benefit against the saved Drinking success and Cooking failure. This offline
screen uses all seven retained roots, all seven Food preparation C005 children,
and all thirteen Food C001 children. It considers all 1,386 unused original
entries, retaining their distinct identities and native same-note/mapped-parent
eligibility. It enumerates no sibling pairs and makes zero teacher calls or
encodings. The allowance remains 189 used / 31 remaining. No ranking code or
automatic constructor policy was added: the estimate fails the known screen.

### Concrete estimates tested

Two source representations were inspected separately through the existing
production `_scores` and `_local_ancestor_scores` functions:

- The candidate's standalone heading versus each canonical sibling's heading.
- The best proper original descendant heading versus each sibling heading,
  keeping every match within the candidate's own note and source branch.

For sensitivity inspection, count eligible siblings with cosine at least a
cutoff. The known two cases use 0.3, 0.4, 0.5, 0.6 and 0.7; the full candidate
pools use 0.3, 0.4 and 0.5. These values are diagnostic choices, not a calibrated
threshold, confidence measure or containment rule. Fewer than two matches
does not propose a grouping. Source branches and standalone headings remain
separate routes; the heading route shows the fallback needed when a source
branch supplies poor matches.

For N visible siblings and m estimated matches, the estimated reduction in
choices beyond six is:

`max(0, N−6) − max(0, N−m+1−6) − max(0, m−6)`.

This assumes those m direct choices are replaced by one new parent with m
children. It is an arithmetic estimate, not a generated menu. Candidate own
support and the represented child notes are deduplicated. Discard an estimate
if its parent note set equals a proposed child's set, or, in a non-root group,
equals the existing parent's set after adding the candidate's support. Rank
the remaining positive estimates by that reduction, then the second-strongest
eligible similarity and stable original-entry identity. No value enters a
comparison prompt or overrides ordinary traversal.

### The estimate misses the decisive relationship

| Known nominee / representation | Cutoff | Estimated children | Estimated reduction beyond six | Saved outcome |
|---|---:|---:|---:|---|
| Drinking / heading | 0.3 or 0.4 | 2 | 1 | Actual root reduction is 1. |
| Drinking / heading | 0.5, 0.6 or 0.7 | 0 | No nomination | Misses the useful nominee. |
| Drinking / proper descendants | All five cutoffs | 0 | No nomination | Misses the useful nominee. |
| Cooking / heading | 0.3 or 0.4 | 6 | 1 | Actual overcrowding reduction is 0; one equal-note-set edge appears. |
| Cooking / heading | 0.5 / 0.6 / 0.7 | 5 / 4 / 3 | 1 | Same bad estimate despite changing the cutoff. |
| Cooking / proper descendants | 0.3 | 5 | 1 | Still predicts useful grouping. |
| Cooking / proper descendants | 0.4, 0.5, 0.6 or 0.7 | 0 | No nomination | Exclusion is not evidence that useful alternatives improve. |

Drinking's heading scores 0.4430 against Coffee and 0.4375 against Slush
drinks. Its proper descendant **Author not drinking wine** scores only 0.2969
and 0.2994 against those same headings. That source-specific example does not
recover the broader topic's two accepted relationships. Requiring several
distinct original descendant witnesses would also exclude this successful
candidate: it has only this one proper descendant.

Cooking's heading scores only **0.1337 against Rosemary**, although its saved
traversal contains Rosemary C070 as well as all six other displayed children.
At 0.3 or 0.4 the estimate therefore predicts six children, with nine distinct
notes before adding the candidate's own note. Its proposed parent has ten
notes, whereas Food preparation would have eleven after that support is added.
Every predicted edge passes the note-set narrowing check. Actual placement
also groups Rosemary's distinct note, bringing the new parent to eleven;
Food preparation → Cooking is then eleven → eleven. The decisive failure
comes from missing one predicted relationship, not arithmetic or duplicate
counting. A correct narrowing check cannot repair an incorrect membership set.

### Whole-group rankings remain weak

At cutoffs 0.3 and 0.4, Drinking is **eleventh among distinct headings** and
thirteenth among entries in the root-group heading ranking, rather than fourth
in the earlier preselected Coffee + Slush drinks pair. The whole-group search
also considers resemblance to other root combinations. Its first five headings
at both cutoffs are Plant foods, Plant-based diet, Chocolate consumption,
Outdoor grilling and Michael Pollan's Food Rules recommendation to eat mostly
plant foods. None was traversed in this screen; their predicted benefit is not
a positive semantic or shaping label.

Cooking remains first in its whole-group heading ranking at all three tested
full-pool cutoffs, even after the estimated note-set check. Source-descendant
ranking instead promotes Charcoal grills, the author's rocket stove, J-tubes,
People and Food. At 0.3, Cooking falls to heading rank 168; at 0.4 and 0.5 it
does not propose a group. These replacements are also untested, not demonstrated
improvements.

Food's thirteen-choice group shows the structural score's additional weakness.
Grouping six, seven or eight choices all gives the largest estimated reduction,
five. At 0.4 the heading route consequently promotes Food appeal, Foodies,
Food quantities, Healthy dinners and Meat eaters; the descendant route promotes
Healthy dinners, Meal planning, Beginning activities, Shrimp tempura sushi and
the author's particular dinner. The arithmetic rewards an estimated count in
that range even though similarity has not established the containment direction.
No rejection or false-positive label is assigned to these untried entries.

**Finding:** do not activate this cosine-count estimate as a way to choose
which nomination improves shape. Original branches remain retrieval evidence,
and the exact note-set/choice checks remain useful after actual placement.
The proposed pre-placement membership estimate fails the known Cooking case
and loses the known Drinking case on the branch route. This is evidence against
this concrete estimate, not proof that every use of SSE or original branches
is inadequate, nor a comparison-prompt failure.

The remaining task is selecting an original local parent likely to contain
any useful subset of the whole oversized sibling group. The source heading,
context and original ancestors may supply information about broader scope that
cosine alone does not express. The user subsequently authorized the bounded
semantic nomination investigation below. Ordinary traversal and actual
end-hierarchy checks remain decisive.

Verification reused the production vector normalization, source-branch
aggregation and native eligibility paths. Original corpus, raw-state and
baseline-menu hashes match the earlier protected record; actual Drinking and
Cooking outcomes remain the native saved audits. All calculations above are
separate estimates, not model answers or new canonical edges. There are no new
source functions, experiment cases, model receipts, hierarchy changes or UI
refreshes to integrate.

## Whole-group model nomination: failed saved-outcome screen

The user approved a small test in which SSE retrieves available original local
entries and a model nominates a useful parent while considering the entire
overcrowded sibling group. This authorizes the experiment, not a production
selection rule or changes to the comparison/bootstrap prompts.

Experimental [Hierarchy-parent-nomination-v1](shr_single_pair/Hierarchy-parent-nomination-v1.md)
was tested on the frozen B96/C48 fifty-note graph's seven roots and Food
preparation's seven children. For each group, the existing second-highest
eligible sibling subject-cosine ranking supplied twenty distinct exact
headings. The first eligible original entry for each heading was retained;
context variants were not tested exhaustively. No candidate was injected using
its historical outcome. Drinking was heading rank eleven, original-entry rank
thirteen; Cooking was first in its group.

The new `canonical_shaping_nomination` input adapter in
[experiment_inputs.py](experiment_inputs.py) gathers the saved group and
original entries through native preparation. The model receives:

- Every sibling's original heading, immutable meaning, immediate canonical
  parents and deduplicated recursive note membership.
- The group's canonical parent and its recursive canonical ancestors, with
  their parent IDs preserving the relationships.
- Each offered local entry's heading, context, original local ancestors,
  source-note ID and eligible sibling IDs, plus its full original post.

Original posts are supplied once per distinct note, rather than repeated for
each entry. Short note labels are bound to original IDs in review evidence.
SSE scores, saved model answers, expected relations and historical outcome
labels do not enter the prompt. Hashes bind the original corpus, raw graph,
shaped menu, SSE receipts and ranking report. Preparation rejects changed
sources, processed entries, incomplete local ancestor branches and changed
canonical evidence. Output validation refuses invented IDs, duplicates,
ineligible children or a proposal covering fewer than two or the whole group.
It validates mechanics, not containment. This adapter never applies placement.

Two independent native draws used GPT-6.1 Sol medium. The second was prepared
with `--from ... --repeat`; it dispatched again with the same rendered input,
instructions, schema and settings, without reusing the first answers.

| Whole group | First draw | Fresh repeat | Saved ordinary-traversal contrast |
|---|---|---|---|
| Seven roots | No nominee | No nominee | Drinking was accepted above Coffee and Slush drinks; the retained menu's root choices decreased from seven to six. |
| Food preparation's seven children | Cooking above Cookware, Bread preparation, Food smoking, Grilling and Cooking appliances | Same nominee and same five children | B96 Cooking contained all seven children, produced an equal-note-set edge beneath Food preparation and increased depth without reducing excess choices. |

The root answers explicitly rejected Drinking because it is an activity rather
than a beverage category. That differs from the saved Compare-v48 results.
The Cooking answers excluded Rosemary and the raw, no-bake pie, predicting
that the five-child grouping would improve shape. The saved bootstrap meaning
instead admits culinary techniques including mixing and shaping without
requiring heating. Its actual traversal contained both excluded siblings and
the saved shape audit showed the unnecessary extra level.

**Finding:** this concrete nomination screen misses the demonstrated useful
nominee and favours the demonstrated unhelpful nominee, in both draws. It is
not adopted. Model-based selection cannot be treated as a shortcut if it uses
a different containment contract or establishes a different local meaning
from the one ordinary traversal will compare. The prompt was not supplied the
candidates' saved bootstrap meanings; this is a plausible contributor to the
Cooking mismatch, not an isolated causal result. Activity-versus-product
interpretation is another observed mismatch in the reasons.

The saved traversal outcomes are evaluation controls, not new human semantic
gold. No broader-parent topics were invented, no new full traversal was run,
and no hierarchy, comparison/bootstrap prompt or review UI was changed. This
test establishes no operational-policy savings, quality preservation or
reliability estimate. Its rendered group data were 12,233 and 15,950 characters;
using bounded candidate lists limits per-request work, but production scaling
and shortlist coverage remain unproven.

Native evidence is retained under `target/canonical-shaping-selection-v1/` in
the task worktree:

- `whole-roots-v2.json` and `whole-food-preparation-v2.json`: frozen SSE rankings.
- `parent-nomination-v1` and `parent-nomination-repeat-v1`: prepared inputs,
  native outputs and immutable receipts.
- `parent-nomination-usage-v1.json`: shared-runner accounting from
  [the maintained usage selection](shr_single_pair/hierarchy-parent-nomination-usage-v1.json).

There were **four fresh attempts, four valid outputs, zero exact reuses,
retries, failures, warmups or new SSE encodings**. Total observed input was
18,604 tokens and output was 755 tokens, including 394 reasoning tokens; cache
read and write counts were zero. Saved total API-equivalent catalog cost was
**$0.044758**; subscription cash charge was zero. The persistent task counter
advanced from 189/220 to **193/220**, leaving 27 attempts. The earlier Cooking
and Drinking traversals were reused as evidence and were not billed or counted
again.

The production-CLI input test first failed on the missing adapter, then passed
after preparation/validation support was added. The two new adapter tests and
two related exact-reuse and subject-pair checks pass; all twenty-seven
shaping-selection tests pass. Broad suites were also run:
the experiment suite had nineteen failures and six skips among 140 tests,
and the shaping/canonical suite had two failures among 61 tests. Selected
unchanged-main checks reproduced obsolete configurable-concurrency and
retry-order expectations. The transitive graph-preservation fixture both
passed and failed on unchanged main and the task branch. Its single-attempt
counterexample does not specify a case ID and therefore depends on dispatch
order. Those broad suites are not reported as passing; their runner migration
and order-sensitive tests were left outside this experiment's scope.

The subsequent user decision permits proposing a synthetic parent when the
original local entries do not supply a useful consolidation topic. The user
requested the first prompt draft, sharing applicable bootstrap wording, and
coordination with the bootstrap agent. This replaces the earlier proposed
nomination diagnostic as the immediate next work. No new selection policy has
been activated.

## Synthetic parent draft and shared definition wording

**Hierarchy-consolidation-v3 is user-approved and has completed its initial
proposal and comparison screen. It has not been adopted into construction.**
The user initially authorized its preparation in the shaping task worktree only,
then approved the prompt and the initial test described below.
The previously authorized bootstrap-agent consultation is closed; the user
instructed this task to stop messaging that agent. No bootstrap revision,
construction change, review UI refresh or main integration is part of this task.

The [complete v3 draft](shr_single_pair/Hierarchy-consolidation-v3.md) receives
only the siblings' immediate parent and the siblings, each with an ID, title
and fixed explicit meaning. For a root group the parent is null. The user
explicitly removed recursive ancestors from this input; ancestor checks and
parent-ID relationship fields are also removed. It proposes one new topic
with a title, explicit meaning and at least two intended child IDs, or JSON
null. It searches for any useful subset across the whole sibling group. A
proposal containing every sibling only adds a level and is excluded. The
proposal must still undergo ordinary comparison to establish actual placement;
this task does not implement that path for synthetic inputs.

The user approved keeping shared instructions in versioned files and assembling
full prompt files before preparation. V1 shared only 119 words. After the user
asked whether that was sufficient, the approved expansion produces nine shared
clauses totaling 385 words, all copied verbatim from approved
[Bootstrap-v104](shr_single_pair/Hierarchy-bootstrap-v104.md):

- [Identity and defining features](shr_single_pair/prompt_parts/explicit-meaning-rules-v2/01-identity.md).
- [Required roles and intended use](shr_single_pair/prompt_parts/explicit-meaning-rules-v2/02-roles.md).
- [Preserving alternatives and parts](shr_single_pair/prompt_parts/explicit-meaning-rules-v2/03-alternatives.md).
- [Required actions versus optional methods](shr_single_pair/prompt_parts/explicit-meaning-rules-v2/04-activities.md).
- [Choosing coherent boundaries](shr_single_pair/prompt_parts/explicit-meaning-rules-v2/05-boundaries.md).
- [Writing the standalone definition](shr_single_pair/prompt_parts/explicit-meaning-rules-v2/06-definition.md).
- [Optional variations and illustrative examples](shr_single_pair/prompt_parts/explicit-meaning-rules-v2/07-variations.md).
- [Required absences and frequency qualifiers](shr_single_pair/prompt_parts/explicit-meaning-rules-v2/08-qualifiers.md).
- [Consistent restrictions and an unresolved meaning](shr_single_pair/prompt_parts/explicit-meaning-rules-v2/09-consistency.md).

Post-specific evidence instructions, original local-branch interpretation,
and examples remain bootstrap-specific. The old shared consistency clause
also imported Bootstrap's instruction to return a null meaning; v8 below
removes that task-specific behavior from the shared writing text.
The shared clauses govern the proposed parent's meaning; supplied canonical
meanings stay fixed. The consolidation output instructions specify JSON null
when a coherent meaning cannot be established, rather than an object with a
null meaning. Repeated definition rules outside the shared section were removed.
Input and grouping rules retain v1's behavior. The shared runner's native
`revise` produced v2 and its exact
[revision record](shr_single_pair/Hierarchy-consolidation-v2.md.revision.json).
The native `revise` command subsequently produced v3's parent-only input and
[revision record](shr_single_pair/Hierarchy-consolidation-v3.md.revision.json).
Its shared definition clauses remain byte-for-byte identical to v2.

The pinned assembly manifests for the approved references are
[Bootstrap-v104 with expanded shared clauses](shr_single_pair/Hierarchy-bootstrap-v104.shared-v2.assembly.json)
and [Consolidation-v3](shr_single_pair/Hierarchy-consolidation-v3.assembly.json).
Both reference the exact same nine shared files in the same order. The
experimental [Consolidation-v4 manifest](shr_single_pair/Hierarchy-consolidation-v4.assembly.json),
[Consolidation-v5 manifest](shr_single_pair/Hierarchy-consolidation-v5.assembly.json),
[Consolidation-v6 manifest](shr_single_pair/Hierarchy-consolidation-v6.assembly.json)
and [Consolidation-v7 manifest](shr_single_pair/Hierarchy-consolidation-v7.assembly.json)
also preserve those exact shared files and separators, changing only their
task-specific wrappers. The [Consolidation-v8 manifest](shr_single_pair/Hierarchy-consolidation-v8.assembly.json)
retains the first eight files and uses a new
[neutral consistency fragment](shr_single_pair/prompt_parts/explicit-meaning-rules-v3/09-consistency.md):
the exact first two sentences of the old ninth clause, without Bootstrap's
null-meaning behavior. The [Consolidation-v9 manifest](shr_single_pair/Hierarchy-consolidation-v9.assembly.json)
instead pins one [simplified definition-writing fragment](shr_single_pair/prompt_parts/explicit-meaning-rules-v4.md).
This is new draft wording, not a byte-exact Bootstrap extraction. Only v9
adopts it; Bootstrap-v104 and all existing consumers keep their pinned versions.
The [Consolidation-v10 manifest](shr_single_pair/Hierarchy-consolidation-v10.assembly.json)
pins [fragment v5](shr_single_pair/prompt_parts/explicit-meaning-rules-v5.md),
which adds only “Define the selected topic, not every concept it mentions.”
to v4. Only v10 adopts v5, retaining the exact v9 wrappers and separators.
Historical Bootstrap and consolidation recipes remain
fixed. V3 remains the last human-approved full consolidation
wording; authorization to draft or test later versions is not semantic qualification. The bootstrap
recipe preserves its original clause positions and intervening bytes;
the consolidation recipe places them together in its definition section. The
original bootstrap recipe, shared v1 file and consolidation v1 remain fixed.
The additional bootstrap recipe is an extraction change, not a Bootstrap
meaning-generation revision or activation; its complete output remains v104.
Each records the prompt version, every source part's path and SHA-256, their
order, and the full output's path and SHA-256. Paths are relative to the
manifest. Literal parts such as `{"text": "\n\n"}` declare separators without
creating empty source files; the assembled output hash pins that exact text.
[prompt_assembly.py](prompt_assembly.py) concatenates exact file and literal
bytes; it does not interpret template variables or add implicit separators.
Each wrapper owns
its surrounding whitespace, including a mid-paragraph space or a final blank
separator when necessary for exact reconstruction. Git's default whitespace
check reports intentional wrapper endings; the assembled prompts and
remaining source pass the check. Missing or changed parts, a wrong assembled hash,
and a differing existing output are errors. Existing matching outputs are
checked without rewriting them.

Use the assembled Markdown file with the shared runner's existing `prepare`
command. The runner still freezes full text; it does not resolve includes or
read shared parts during execution. Assembly is a source-authoring operation,
not an alternative experiment preparation or execution path.

From the task worktree:

```bash
python3 sse_multivector/prompt_assembly.py check \
  sse_multivector/shr_single_pair/Hierarchy-bootstrap-v104.shared-v2.assembly.json
python3 sse_multivector/prompt_assembly.py build \
  sse_multivector/shr_single_pair/Hierarchy-consolidation-v10.assembly.json
```

After a shared instruction changes, create a new shared-file version and new
versions of every prompt adopting it, with newly pinned manifests and reviewed
full assembled text. Old prompt versions, manifests and prepared experiments
remain fixed. Advancing only one consumer is explicit: its manifest selects
the new shared version while other consumers retain the old one.

The bootstrap reconstruction's SHA-256 is
`d97d0cfe078546e9525ac15252b81eee20630fba6e4786b1000c5cf942d49ba0`,
identical to the pre-existing v104 file. The nine shared-file hashes are pinned
in both approved-reference assembly manifests. V1's 119-word definition excerpt is the
unchanged sixth shared clause; the v1 output still hashes to
`6a93d4d2a06c20b3a46ffd9758144cd280f7f0017153eb18a43cae72b2947965`.
The initial CLI test failed because assembly support was absent. The expansion
check first failed on the missing v2 manifest; the literal-separator check first
failed on its unsupported part shape. The parent-only check first failed on
the missing v3 manifest. Eleven assembly checks and nine existing
revision checks now pass, including refusal of source drift or output overwrite,
exact v104 reconstruction through both recipes, identical shared clauses in
both consumers, and native generic `prepare` freezing each consolidation
version without inference. These checks establish assembly behavior, not semantic
quality or API acceptance of a consolidation output schema. No schema or
production activation is introduced in this draft.

The user-requested boundary annotations are kept in an ignored review copy:
`target/canonical-shaping-selection-v1/Hierarchy-consolidation-v3-annotated.md`
in the task worktree. Visible BEGIN/END markers surround the complete shared
section. Removing them restores v3 exactly; they are not model instructions.

The initial v3 draft uses explicit sections, delimited input and no requested
reasoning trace or examples, consistent with
[official reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices).
That guidance does not validate the consolidation semantics.

## Initial consolidation-v3 test

The user approved four GPT-6.1 Sol medium proposal calls: the saved Food
preparation group and seven roots, with two independent draws for each.
The shared runner prepared the second draw with `--from` and `--repeat`;
input text, model and reasoning settings match, and all four outputs have fresh
native receipts. No source post, local nominee list, SSE ranking or expected
answer enters the consolidation input.

The reusable `canonical_consolidation` adapter gathers the whole sibling group
from pinned raw/menu sources, preserves original canonical titles, meanings and
support, and supplies only `parent` and `siblings`. It validates JSON null or
exactly `title`, `meaning` and distinct supplied `children` IDs selecting a
proper subset of at least two. Preparation does not infer or change a graph.
[The source](shr_single_pair/hierarchy-consolidation-v3-source-v1.json) and
[first-draw specification](shr_single_pair/hierarchy-consolidation-v3-first-v1.spec.json)
freeze both seven-choice groups.

| Group | First draw | Independent repeat |
|---|---|---|
| Food preparation C005 | Cooking equipment above Cookware C008 and Cooking appliances C014 | JSON null |
| Roots | Beverages above Coffee C006 and Slush drinks C039 | Beverages above the same two nodes, with a different fixed definition |

The `canonical_consolidation_pairs` adapter then preserves each of the three
non-null returned definitions verbatim and prepares comparisons against every
offered sibling, plus the supplied parent when present. It verifies the saved
proposal's native receipt and source hashes, supplies the original raw graph's
full recursive canonical ancestor/descendant meanings, and requires exact
meaning-copy outputs. It does not invent a source post for a synthetic topic.
The unchanged **Compare-v75** fixed-meaning prompt is used for this bounded
validation; this is not a claim that it replaces the fifty-note graph's original
Compare-v48 construction or qualifies newer experimental Compare versions.
[The comparison source](shr_single_pair/hierarchy-consolidation-v3-comparison-source-v1.json)
and [specification](shr_single_pair/hierarchy-consolidation-v3-comparison-v1.spec.json)
record that choice.

All twenty-two comparison requests are valid. Both Beverages definitions contain
Coffee and Slush drinks and return neither against the other five roots.
Cooking equipment contains the two proposed children, returns neither against
the other five siblings, and is contained by Food preparation. Required
canonical consequences were included in each request. These are model judgments
under fixed meanings, not new human gold or complete graph traversal.

The native `show` report now includes `consolidation_shapes`, an offline check
of deduplicated supporting-note sets plus recursive descendants. It changes no
hierarchy and labels every result `applied: false`:

- **Beverages passes the local structural check.** It represents seven notes;
  Coffee represents six and Slush drinks one. Both proposed downward edges
  narrow the note set. Replacing those two roots with their parent would reduce
  root choices from seven to six; the new parent would offer two choices.
- **Cooking equipment fails the local structural check.** Cookware represents
  two notes, both already included in Cooking appliances' four-note set. The
  proposed parent's union is four notes too. Its edge to Cooking appliances
  would not narrow the note set, despite reducing Food preparation's immediate
  choices from seven to six. Do not apply this grouping under the approved
  strict-narrowing requirement.

A semantically valid grouping need not improve browsing. The immediate useful
process change is to screen note-set narrowing before paying for comparisons.
The consolidation model was not given note memberships, so this structural
failure does not by itself identify a wording defect. The null repeat also does
not establish whether no alternative useful grouping exists.

Native evidence remains ignored under `target/canonical-shaping-selection-v1/`:
`consolidation-v3-first-v1`, `consolidation-v3-repeat-v1`, and
`consolidation-v3-compare-v75-v1`, with `*-report-v1.json` viewing snapshots.
The shared runner's [usage selection](shr_single_pair/hierarchy-consolidation-v3-usage-v1.json)
produces `consolidation-v3-usage-v1.json`: **26 fresh attempts**, zero reuses,
warmups, retries, failures or missing usage; 64,007 input tokens, zero cache
reads/writes, and 8,994 output tokens including 2,063 reasoning tokens.
Complete API-equivalent catalog cost is **$0.217954**, not subscription billing.
The initial test advanced the existing counter from 193/220 to **219/220**;
one attempt remained at that checkpoint. It did not increase the allowance.

Production-path checks first failed on the two missing adapters and missing
shape report, then passed. Together with nomination, assembly and revision regression checks,
twenty-six relevant tests pass. Full saved hierarchy traversal and an actual
synthetic-node insertion remain unrun; this screen does not establish globally
optimal shaping, route-depth savings or whole-hierarchy quality. The user
subsequently prioritized broader consolidation prompt development; full
traversal and insertion remain deferred. No graph, prompt version, UI or other agent's
worktree was changed, and no agent message was sent.

## Expanded consolidation-v3 prompt test

The user approved expanding the prompt tests beyond the initial two groups,
including groups with four or five siblings. The same completed ASv6.100
fifty-note menu contains seven additional groups of at least four siblings.
The [expanded source](shr_single_pair/hierarchy-consolidation-v3-expanded-source-v1.json)
freezes all seven complete groups, their immediate parents and the unchanged
raw/menu hashes. The [specification](shr_single_pair/hierarchy-consolidation-v3-expanded-v1.spec.json)
uses unchanged approved Hierarchy-consolidation-v3 and GPT-6.1 Sol medium/SSE.
There is no note-membership input, new prompt version, construction-policy
activation or hierarchy insertion.

Two independent native draws were completed for each group. The repeat was
prepared with `--from` and `--repeat`; exact prompt text, complete case inputs,
source hashes and model settings match. All fourteen cases have fresh valid
receipts, rather than reused answers.

| Parent and supplied choices | First draw | Independent repeat | Prospective local note-set result |
|---|---|---|---|
| Food C001: 13 | Meals above Breakfast C018, Food dishes C020 and Dinners C059 | Daily meals above Breakfast C018 and Dinners C059 | Both narrow; original choices fall to 11 or 12, still above six |
| Mental states C003: 6 | Motivational states above Perceived needs C047 and Desires C076 | Same title and children, separately generated meaning | Both narrow; 6 to 5 choices |
| Coffee C006: 6 | Further coffee above Second coffee C101 and Additional coffee C102 | Same title and children, separately generated meaning | Both fail narrowing: the proposed union and Additional coffee each contain the same two notes |
| Cuisine C016: 6 | Prepared dishes above Pizza C054, Cheesesteaks C066 and Risotto C073 | Same title and children, separately generated meaning | Both narrow; 6 to 4 choices |
| Food dishes C020: 6 | Dough and batter foods above Pancakes C031 and Bread C068 | Dough- and batter-based foods above the same children | Both narrow; 6 to 5 choices |
| Eating C123: 5 | JSON null | JSON null | No proposed edges |
| Cooking appliances C014: 4 | Cookware above Stockpots C015 and Cast-iron cookware C105 | Cooking vessels above the same children | Both narrow; 4 to 3 choices |

Six of seven groups choose the same children in both draws; this includes
Eating's repeated null. Different generated meanings remain distinct proposals
and do not share comparison answers merely because their children match.
Food's differing subsets are not a reversal or contradiction: Meals and Daily
meals choose different scopes. Four groups meet the local structural check
twice. Food's two proposals make partial progress without satisfying K = 6
yet; `local_group_constraints_met: false` must not be read as a semantic
failure or absence of useful improvement in that case. The Coffee proposal
would violate the approved strictly smaller-note-set requirement and should
not be inserted with these children. The model has no note memberships, so
that failure does not itself establish a prompt-wording defect.

The wider proposal screen supplies promising definition and grouping controls,
not semantic certification. That fourteen-call stage made no Compare calls;
the subsequent containment screen below checks the entire selected meanings,
containment beneath the fixed parent and omission of other siblings that fit
the proposed meaning.
One targeted question is whether Cuisine's Prepared dishes meanings also cover
Turning pantry staples into chewy bagels C099: the first definition explicitly
covers preparation variations, whereas both draws omit that activity. An
activity/product distinction alone does not settle this. Cooking vessels and
Cookware should also be checked against the existing canonical Cookware topic
during any later placement; a similar title alone is not a duplicate-node
failure in this parent-and-siblings-only prompt. Repeated null for Eating does
not establish that no useful proposal exists. None of these observations is
new human gold or a request to change Bootstrap/Compare.

Native evidence is ignored under `target/canonical-shaping-selection-v1/`:
`consolidation-v3-expanded-first-v1` and
`consolidation-v3-expanded-repeat-v1`. The complete viewing snapshots are
`consolidation-v3-expanded-first-report-v2.json` and
`consolidation-v3-expanded-repeat-report-v1.json`; the earlier partial
first-report-v1 remains preserved. Together with the initial two-group screen,
these sources define nine repeatable prompt-development cases with two draws
each. These are visible development inputs, not an untouched final test set.

The shared runner's [usage selection](shr_single_pair/hierarchy-consolidation-v3-expanded-usage-v1.json)
produces `consolidation-v3-expanded-usage-v1.json`: **14 fresh attempts**, zero
reuses, warmups, retries, failures or missing usage; **19,140 input tokens**, zero
cache reads/writes, and **3,867 output tokens including 3,091 reasoning tokens**.
Complete API-equivalent catalog cost is **$0.076950**, not a subscription bill.
The user's `proceed` authorized the stated fourteen-call panel: one remaining
attempt was used under the earlier 220 cap, and the other thirteen extended
that persistent counter to **233/233** at that checkpoint. The later forty-call
renewal and its completed use are recorded below.

Twenty-four relevant production-adapter, assembly and revision checks pass.
Native preparation and receipt validation preserve the original source files
and complete input/settings identity. This work remains isolated in the shaping
task worktree, as requested. No graph, prompt text, UI or other agent's worktree
changed, and no agent message was sent. The user subsequently approved
proceeding with focused containment review of these saved definitions before
changing the prompt; the prepared native screen is described below. Full
synthetic-node placement is not the current development priority.

## Expanded consolidation-v3 containment screen

The user's subsequent `proceed` approved the prepared forty GPT-6.1 Sol medium
comparisons. All forty completed with valid fresh receipts, zero reused answers,
failures, retries or warmups. The persistent allowance advanced from 233/233
to **273/273**; no further calls remain authorized.

The [comparison source](shr_single_pair/hierarchy-consolidation-v3-expanded-comparison-source-v1.json)
selects the five usable first-draw definitions, preserving the producer
experiment envelope hash and each valid native receipt. Coffee is excluded
because its proposed note sets cannot strictly narrow; Eating supplied no
definition. Both Food's useful partial reduction and the four other promising
groups are included. The [specification](shr_single_pair/hierarchy-consolidation-v3-expanded-comparison-v1.spec.json)
retains the earlier screen's Compare-v75 prompt, response schema, GPT-6.1 Sol
medium/SSE settings and complete canonical ancestor/descendant input. It does
not activate or qualify Compare-v75 as the current hierarchy-generation prompt.

The shared runner executed
`target/canonical-shaping-selection-v1/consolidation-v3-expanded-compare-v75-v1`:

| Saved proposal | Offered siblings plus immediate parent |
|---|---:|
| Meals, from Food | 14 |
| Motivational states, from Mental states | 7 |
| Prepared dishes, from Cuisine | 7 |
| Dough and batter foods, from Food dishes | 7 |
| Cookware, from Cooking appliances | 5 |
| Total | 40 |

These are twelve intended-child checks, five supplied-parent checks and
twenty-three checks for other siblings. All forty exact requests received new
answers under the saved request identities. Preparation itself made no model
calls. Each synthetic local input contains only its saved title and meaning;
no fabricated original post or original local branch is added. Source hashes
and the complete original graph meanings are verified.

Before inference, two concerns are recorded with the native `review` command
as source-bound **agent uncertain** assessments of the saved proposals:

- **Cuisine:** Prepared dishes explicitly covers ingredient and preparation
  variations, but omits Turning pantry staples into chewy bagels C099. Check
  whether that activity's whole fixed meaning fits. An activity/product
  distinction alone does not establish exclusion.
- **Food dishes:** the supplied parent C020 defines prepared foods served or
  eaten as a meal or part of a meal; the proposed dough/batter-food definition
  does not state that condition. The supplied Bread and Pancakes meanings also
  omit it. Check containment without silently adding a meal restriction;
  a conflict could originate in the existing branch rather than consolidation.

Those pre-inference concerns remain preserved alongside the later results.
Native `review` records now also bind five post-screen **agent** assessments to
the exact proposal inputs and outputs. Original outputs and receipts remain
immutable. None of these assessments establishes new human gold.

| Saved proposal | Selected children | Supplied parent | Other offered siblings | Assessment under this screen |
|---|---|---|---|---|
| Meals | Breakfast and Dinners accepted; Food dishes' direct meaning covered, final relation uncertain | Food accepts containment | Eating contains Meals; remaining ten neither | Existing Food dishes descendants block compatible placement; this does not establish a consolidation wording failure |
| Motivational states | Both accepted | Mental states accepts containment | All four neither | Complete successful bounded screen |
| Prepared dishes | All three accepted | Cuisine returns neither | Bagel-making contained; Japanese food and Sorrento's cuisine neither | Parent-fit failure and missing covered sibling |
| Dough and batter foods | Both accepted | Food dishes returns uncertain, with direct containment rejected | All four neither | Direct parent-fit failure plus an existing branch conflict |
| Cookware | Both accepted | Cooking appliances accepts containment | Both neither | Complete successful bounded screen |

The twelve selected-child directional answers all state full coverage. Eleven
final relations are `local_contains_canonical`; Meals versus Food dishes is
`uncertain` because its canonical descendants introduce conflicting scopes.
Three of five supplied-parent checks accept containment, one returns `neither`,
and one returns `uncertain`. Among twenty-three omitted-sibling checks, twenty-one
return `neither`, one contains the proposal, and one is contained by it. The
aggregate final relations are twelve `local_contains_canonical`, four
`canonical_contains_local`, twenty-two `neither` and two `uncertain`.

Four exact cases preserve the original comparison findings and review
hypotheses. Their meal-role and Cuisine-association interpretations remain
disputed under the later user-approved evaluation correction; comparison
answers are model observations, not independently established semantic gold:

- **`proposal-3-C016`, Prepared dishes versus Cuisine:** the generated meaning
  admits a finished improvised dish without a culinary style/tradition
  association. Cuisine's fixed meaning describes a style or tradition and its
  associated dishes. The answer explicitly says: “An improvised dish
  unassociated with a culinary style or tradition is covered by prepared dishes
  but not by cuisine.” This records a direct model parent-fit rejection rather
  than a blocked implication; whether the counterexample is valid remains open.
- **`proposal-3-C099`, Prepared dishes versus bagel-making:** the output says:
  “Full coverage holds: making chewy bagels from pantry staples is a specific
  preparation variation of a prepared culinary item.” The generated definition
  explicitly covers preparation variations but leaves C099 out of `children`.
  This corroborates the saved include-all concern under the unchanged comparison
  prompt. Restricting the list to products while writing a definition that covers
  their preparation is not a coherent solution.
- **`proposal-4-C020`, Dough and batter foods versus Food dishes:** the answer
  says: “A cooked dough food eaten solely as a non-meal snack is excluded by the
  canonical node.” The proposal does not require the parent's meal role. Its
  final `uncertain` separately identifies that the existing Bread/Pancakes
  meanings also lack that role. Adding a meal condition to the proposal would
  narrow those fixed children under the original required-role interpretation.
  Whether the meal wording characterizes a kind or requires that role throughout
  the topic remains unresolved.
- **`proposal-1-C020`, Meals versus Food dishes:** the direct answer says:
  “Full coverage holds for the selected canonical meaning.” Its final
  `uncertain` concerns Bread and Salsa descendants without a meal restriction.
  Consolidation receives only the immediate parent and offered sibling meanings,
  so that hidden graph conflict does not by itself justify changing its wording
  or adding ancestor/descendant inputs. Ordinary placement remains necessary.

Eating C123's `canonical_contains_local` answer for Meals is a possible further
parent relationship, not a missing child. Canonical Cookware elsewhere remains
a later equivalence/placement check. Neither accepted screen establishes whole
hierarchy quality, reliable repeats, globally optimal shaping or fewer browsing
decisions after actual insertion. Only the first-draw definitions were compared;
the separately generated repeat definitions remain unvalidated.

**Revision focus implemented in the subsequent experimental v4 draft:** organize
the task-specific instructions so the final standalone meaning determines the
complete child list, then check that same meaning against the supplied parent's
entire scope. A recognizable shared category is insufficient if its final scope
escapes that parent. If preserving whole child meanings makes the constraints
incompatible, choose a different grouping or return null. V4 replaces the relevant
selection/output wording and retains the hash-pinned shared Bootstrap clauses
unchanged. Official
[reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices)
supports direct instructions and clear delimiters without requesting reasoning
traces. It does not establish this semantic fix; the revised wording would need
fresh qualification on these controls, with complete comparison of changed
definitions rather than reuse based on matching child IDs.

Native evidence remains ignored under `target/canonical-shaping-selection-v1/`:
`consolidation-v3-expanded-compare-v75-v1`, its source-bound receipts, and
`consolidation-v3-expanded-compare-report-v1.json`. This stage reports **98,643
input tokens**, zero cache reads/writes, and **16,278 output tokens including
3,215 reasoning tokens**. Complete API-equivalent catalog cost is **$0.360066**.
The [combined usage selection](shr_single_pair/hierarchy-consolidation-v3-expanded-validation-usage-v1.json)
reproduces `consolidation-v3-expanded-validation-usage-v1.json` through native
`summarize-experiments`: the fourteen proposal draws plus forty comparisons total
**54 fresh attempts**, **117,783 input**, **20,145 output including 6,306 reasoning**,
and **$0.437016**. Usage is complete with zero reuses, warmups, failures, retries
or missing token/cost estimates. These are API-equivalent catalog amounts, not
subscription invoices; reasoning is already counted in output.

Expected roles remain outside model input. A compatible selected edge requires
`local_contains_canonical`; the supplied parent requires
`canonical_contains_local`. An omitted sibling returned as
`local_contains_canonical` or `equivalent` needs review against consolidation's
include-all requirement. An uncertain branch judgment alone does not establish
a consolidation wording failure. Twenty-four production-adapter, shared assembly
and revision checks pass; assembly reconstruction preserves approved v3 bytes.
No graph, prompt text, UI or other agent's
worktree changed, and no agent message was sent. The results and maintained
findings remain isolated in this task worktree as requested.

## Consolidation-v4 draft

The user explicitly authorized drafting
[Hierarchy-consolidation-v4](shr_single_pair/Hierarchy-consolidation-v4.md)
after the forty-comparison screen. The shared runner's native `revise` uses
last approved v3 as its baseline and preserves an exact
[revision receipt](shr_single_pair/Hierarchy-consolidation-v4.md.revision.json).
The new [assembly manifest](shr_single_pair/Hierarchy-consolidation-v4.assembly.json)
pins the final prompt and the two new task-specific wrappers. All nine shared
Bootstrap-v104 clauses, their order and their separator bytes are unchanged.
The final v4 SHA-256 is
`144e23d89c65910f0851d4163ac7dff1baee248ebf5dab5c8779c843f9aae7c6`.

V4 moves the complete child-list and parent-fit requirements into a check of
the final standalone meaning. It checks every offered sibling, including the
activities and uses explicitly covered by that sibling's meaning, and includes
all siblings whose entire meanings fit. The supplied parent's fixed meaning
must cover the proposed meaning in full; existing placement cannot add a
restriction missing from a sibling. If fitting beneath that parent would narrow
a selected sibling, the grouping is invalid and another topic or null is needed.
This targets the saved bagel omission and Cuisine/meal-role problems without
adding case-specific examples or changing the shared definition-writing rules.

Input remains immediate `parent` or null plus the complete `siblings` group.
Output remains null or exactly `title`, `meaning` and distinct `children` IDs,
with at least two children and fewer than the complete group. The proposal
still requires ordinary comparison before placement. There are no ancestor or
descendant inputs, note-membership inputs, shaping-policy changes or fabricated
restrictions. Existing graph conflicts remain outside this prompt's evidence.

The new production assembly check first failed because the v4 manifest was
missing, then passed with the versioned assembly and native revision receipt.
Twenty-five production-adapter, assembly and revision checks pass, including
shared-byte equality to v3, preserved v3/v104 hashes, and native preparation
freezing the complete v4 prompt without inference. These checks establish
mechanical integrity, not model judgment quality. Drafting made no new model
calls; the persistent counter was **273/273** at that checkpoint. The proposal
panel below subsequently tests the unchanged experimental v4 draft. It has not
changed the active constructor or any hierarchy.

The proposal qualification below reuses the nine original complete groups with
passing, null and structural-negative controls. New generated meanings still
need their own fixed-meaning comparisons; matching child IDs do not justify
reusing a different definition's answers. The draft and its reusable sources
remain isolated in this task worktree as requested.

## Consolidation-v4 proposal panel

The user approved proceeding with the saved-group test. The announced panel
was eighteen GPT-6.1 Sol medium attempts: two independent draws on each of the
same nine groups. The persistent allowance advanced from 273/273 to
**291/291** and all eighteen attempts produced valid native receipts. There
were no failures, retries, warmups, reused answers or missing usage. No further
calls remain authorized by this panel.

Preparation used native `--from` against the two v3 first-draw experiments,
changing only the prompt to v4. The complete case inputs, review evidence and
model/settings objects match those baselines. Native `--repeat` prepared the
two fresh-repeat experiments with identical v4 text, complete inputs and
settings. Earlier proposal answers and labels remain outside model input.
All four runs used the shared runner and its managed queue; no source changed
while they were active.

| Supplied group | V4 first draw | V4 fresh repeat | Prospective local note-set check |
|---|---|---|---|
| Food preparation: 7 | Bakery food preparation above Bread preparation C010 and raw pie-making C098 | Food processing above those two and Food smoking C011 | Both narrow and leave six or five choices |
| Roots: 7 | Beverages above Coffee C006 and Slush drinks C039 | Same children, separately generated meaning | Both narrow; seven to six choices |
| Food: 13 | Meals above Breakfast C018 and Dinners C059 | Daily meals above the same children | Both narrow but leave twelve choices, still above six |
| Mental states: 6 | Motivational states above Perceived needs C047 and Desires C076 | Same children, separately generated meaning | Both narrow; six to five choices |
| Coffee: 6 | Follow-on coffee above Second coffee C101 and Additional coffee C102 | Further coffee above the same children | Both fail: the proposed union equals C102's two-note set |
| Cuisine: 6 | Italian-origin dishes above Pizza C054 and Risotto C073 | Prepared dishes above Pizza C054, Cheesesteaks C066 and Risotto C073 | Both narrow; six to five or four choices |
| Food dishes: 6 | Dough and batter foods above Pancakes C031 and Bread C068 | Meat and meat-alternative dishes above Burgers C036 and Chicken dishes C114 | Both narrow; six to five choices |
| Eating: 5 | JSON null | JSON null | No proposed edges |
| Cooking appliances: 4 | Heat-generating cooking appliances above the author's rocket stove C083 and Induction hobs C107 | Same children, separately generated meaning | Both narrow; four to three choices |

Six of nine groups select the same children across the two draws, including
Eating's repeated null. Different valid topics can choose different subsets;
this agreement is not a semantic accuracy or reliability estimate. Of sixteen
non-null proposals, fourteen pass prospective strict note-set narrowing;
twelve also reduce their local choice count to six or fewer. Food's two partial
reductions and Coffee's two failures remain distinct. These are unchanged native
offline shape checks, not actual placements or semantic approvals.

**V4 continued generating the disputed scope groupings.** Initial native
agent reviews rejected two proposals under the recorded scope interpretation.
Both now have appended uncertain reassessments; these are boundary concerns
rather than established semantic failures:

- **Food dishes, first draw:** the proposed meaning says “prepared foods made
  by cooking dough or batter, eaten as a meal or part of a meal.” Its selected
  Bread meaning remains “Bread is a food made by baking or otherwise cooking
  flour-based dough, with varieties including but not limited to sourdough
  bread.” Neither that meaning nor the Pancakes meaning explicitly states the
  meal role. The v3 model screen treats non-meal foods as counterexamples.
  Under that interpretation, the proposal excludes part of its selected
  children's meanings; the neutral audits later accept the analogous grouping.
  The boundary remains open, and no original canonical meaning was changed.
- **Cuisine, fresh repeat:** the output defines Prepared dishes as “foods made
  by cooking or assembling ingredients into distinct preparations for eating.”
  Cuisine describes a style or tradition and its associated dishes. The initial
  assessment applies the old unassociated-improvised-dish counterexample to
  parent fit; the scope of associated dishes remains disputed. The first draw
  instead proposes Italian-origin dishes with an
  explicit culinary-tradition connection, a promising alternative requiring
  independent comparison. The repeat no longer explicitly includes preparation
  variations, so the old bagel-making containment label cannot be transferred
  to it.

Other recorded agent concerns remain unresolved:

- The second Food dishes proposal also requires a meal role; fixed Burgers
  specifies a patty served in a bun, so its whole coverage needs checking.
- Food processing may be equivalent to its Food preparation parent rather than
  narrower. It also omits Grilling, whose complete meaning includes plans as
  well as cooking; test both questions rather than assume coverage.
- Meals and Daily meals now omit Food dishes. Their changed scopes and the
  earlier graph conflict prevent copying the v3 judgment or claiming that this
  omission is corrected.
- Coffee remains structurally ineligible for insertion regardless of semantic
  comparisons. The model still receives no note memberships, so this does not
  establish a consolidation wording failure.

Native `review` initially rejected the two scope concerns and the two Coffee
insertions. The scope rejects now have uncertain reassessments, preserving
the initial reviews; Coffee's note-set violations remain separate. No new fixed-meaning Compare calls have been
made for v4. The promising new groupings, repeated positive-looking controls
and repeated null do not establish improved end-hierarchy quality. No hierarchy,
UI, shared Bootstrap clause or v4 prompt text changed, and no agent message
was sent.

The ignored native experiments are `consolidation-v4-first-v1`,
`consolidation-v4-repeat-v1`, `consolidation-v4-expanded-first-v1` and
`consolidation-v4-expanded-repeat-v1`, all under
`target/canonical-shaping-selection-v1/`. Their `*-report-v1.json` snapshots
and native receipts preserve exact outputs. The
[usage selection](shr_single_pair/hierarchy-consolidation-v4-usage-v1.json)
reproduces `consolidation-v4-usage-v1.json` using `summarize-experiments`:
**27,124 input tokens**, zero cache reads/writes, **6,056 output tokens including
4,877 reasoning tokens**, and complete **$0.114808 API-equivalent catalog cost**.
This is not subscription billing; reasoning is already counted in output.

The proposed nine-check Compare diagnostic was not prepared or run. After the
user clarified that this task is consolidation, the next authorized action
became the v5 prompt revision below. Ordinary comparison still validates actual
placement later; this task has not changed the Compare prompt or its workflow.
Twenty-five production-adapter, assembly and revision checks passed at the v4
checkpoint. V4 remains experimental.

## Consolidation-v5 draft

The user authorized proceeding with
[Hierarchy-consolidation-v5](shr_single_pair/Hierarchy-consolidation-v5.md)
to investigate the recorded scope concerns directly in consolidation. V5 checks
every supplied sibling against the supplied parent's entire fixed meaning
before choosing a grouping. Only siblings whose whole meanings fit are
available. Existing placement cannot supply a restriction missing from a fixed
meaning; fewer than two compatible siblings requires JSON null. When the
siblings are roots, there is no supplied-parent constraint.

This changes the order of the task rather than adding another preservation
rule at the end. Under the initial required-role interpretation, a meal-restricted
parent cannot justify selecting broader Bread or Pancakes meanings and adding
a meal restriction to the new parent.
The final check still requires the proposed meaning to fit wholly beneath the
supplied parent and be narrower rather than equivalent. Whole-child coverage,
the complete child list, a useful proper subset and null behavior remain in
place. The panel below tests this mechanism hypothesis; the revision itself
does not establish that either boundary concern is resolved.

The shared runner's native `revise` again uses last approved v3 as its baseline.
The [revision receipt](shr_single_pair/Hierarchy-consolidation-v5.md.revision.json)
and [assembly manifest](shr_single_pair/Hierarchy-consolidation-v5.assembly.json)
pin the complete v5 text to SHA-256
`e1a284fc33bbbd121ed34229f4a1cadd7e4a2d8fa1641286a82ba0a43cb502d9`.
Only the task-specific wrappers change; all nine shared Bootstrap-v104 clauses,
their order and separator bytes remain identical to v3 and v4. Historical
prompts, Bootstrap and saved experiment identities are unchanged.

Input remains the immediate `parent` or null and the complete `siblings`
group. Output remains null or exactly `title`, `meaning` and distinct
`children` IDs. No ancestor inputs, note memberships, hierarchy/UI changes,
Compare edits or messages to other agents were added.

The new production assembly test first failed because the v5 manifest was
missing, then passed with the versioned source and revision receipt. Native
preparation also freezes the full assembled v5 text without inference.
Twenty-six production-adapter, assembly and revision checks passed. These checks
establish mechanical integrity, not semantic quality. There were no model
calls in the revision; the persistent counter was **291/291** at that checkpoint.
The subsequent panel tests unchanged v5 under the new bounded allowance.

## Consolidation-v5 proposal panel

The user authorized the same nine complete groups with two independent draws:
at most eighteen GPT-6.1 Sol medium subscription attempts. The persistent
counter advanced to **309/309**. All eighteen attempts completed with valid
native receipts, distinct upstream response references and reported
`gpt-6.1-sol`. There were no failures, retries, warmups, exact reuses, missing
usage or remaining requests. No allowance remains from this panel.

Native `prepare --from` used the v4 first-draw experiments as baselines and
changed only the consolidation prompt. Complete inputs, source evidence and
runner settings match v4. Native `--repeat` requested fresh independent draws
with identical complete v5 prompts and settings. Four experiments ran through
the shared runner's managed queue; no bound source changed during execution.
Historical outputs and judgments remained outside model input.

| Supplied group | V5 first draw | V5 fresh repeat | Prospective note-set check |
|---|---|---|---|
| Food preparation: 7 | Food processing: Bread preparation C010, Food smoking C011, raw pie-making C098 | Bakery food preparation: C010 and C098 | Both narrow; seven to five or six choices |
| Roots: 7 | Beverages: Coffee C006 and Slush drinks C039 | Same children, new definition | Both narrow; seven to six |
| Food: 13 | Meals: Breakfast C018 and Dinners C059 | Meals: those two and Food dishes C020 | Both narrow; thirteen to twelve or eleven, still above six |
| Mental states: 6 | Subjective cognitive functioning: Brain fog and mental clarity C050, sleepiness C092 | Cognitive functioning states: same children | Both narrow; six to five |
| Coffee: 6 | Coffee identified relative to other coffee: Second coffee C101, Additional coffee C102 | Further coffee: same children | Both fail: the new union equals C102's two-note set |
| Cuisine: 6 | Bread-based dishes: Pizza C054 and Cheesesteaks C066 | Cooked dishes: those two and Risotto C073 | Both narrow; six to five or four |
| Food dishes: 6 | Bread-based dishes: Burgers C036 and Bread C068 | Bread-based foods: same children | Both narrow; six to five |
| Eating: 5 | JSON null | JSON null | No proposed edges |
| Cooking appliances: 4 | Stoves: rocket stove C083 and Induction hobs C107 | Heat-generating cooking appliances: same children | Both narrow; four to three |

Six groups retain the same child lists across draws, including Eating's null.
Different definitions and valid broader topics can yield different lists, so
this is not an accuracy estimate. Native prospective shape checks give the
same aggregate as v4: fourteen of sixteen non-null proposals have strict
note-set narrowing, and twelve also leave at most six choices in both affected
groups. Food's partial reductions and Coffee's structural failures remain
distinct; none of these checks establishes semantic correctness or placement.

**The disputed scope groupings occur in both v5 draws.** Initial source-bound
agent reviews recorded four rejects under the required-condition interpretation;
all four now have uncertain reassessments:

- **Food dishes:** both definitions select Bread C068 but require serving or
  eating as a meal or part of a meal. The fixed Bread definition requires
  cooking flour-based dough and has no meal condition. The new parents exclude
  some of their selected child's meaning under that interpretation. The
  alternative food-kind reading remains unsettled. Existing placement cannot
  supply the missing condition.
- **Cuisine:** Bread-based dishes requires a bread or baked-dough base holding
  other ingredients; Cooked dishes requires a cooked component. Neither final
  meaning requires association with a style or culinary tradition. Both retain
  the earlier improvised-food counterexample under the initial interpretation.
  This is an assessment of the exact new definitions, not a copied Compare
  label; the model's neutral audits later disagree with the same boundary.

The original six native rejections comprised these four scope findings and the
two structural Coffee failures. The scope findings are now uncertain; Coffee's
strict note-set violations remain rejected. Five bounded agent accepts cover both Beverages
definitions, both cognitive-state definitions and Bakery food preparation.
They are promising input-only assessments, not independently validated
placements or new human gold. Seven uncertain assessments retain these limits:

- Food processing may be equivalent to Food preparation; complete Grilling
  coverage, including plans, remains unresolved.
- The first Meals definition covers food for an occasion as a whole; the
  repeat explicitly includes components. That wording can explain different
  child lists. Whole fit and prior inherited graph conflicts remain open.
- The new Stoves and Heat-generating cooking appliances definitions need
  independent checking for identity, full scope and proper narrowing.
- Eating's repeated null does not prove that no useful grouping exists.

All eighteen assessments were appended through native `review` with role
`agent`. Outputs and receipts are immutable; the `*-report-v1.json` snapshots
were saved before these reviews, and current native `show` retains the bound
reviews. No new Compare requests, Compare prompt edits, v5 text changes,
graph insertions, UI updates or agent messages occurred.

The ignored experiments are `consolidation-v5-first-v1`,
`consolidation-v5-repeat-v1`, `consolidation-v5-expanded-first-v1` and
`consolidation-v5-expanded-repeat-v1` beneath
`target/canonical-shaping-selection-v1/`. The committed
[usage selection](shr_single_pair/hierarchy-consolidation-v5-usage-v1.json)
reproduces native `consolidation-v5-usage-v1.json`. It reports **26,348 input
tokens**, **1,280 cached input tokens**, zero cache writes, and **7,297 output
tokens including 6,103 reasoning tokens**. Complete API-equivalent catalog
cost is **$0.125794**. One ordinary request reports cached input; no explicit
cache setting or warmup was added, and this is not a caching experiment.
Reasoning is already counted in output; catalog amounts are not subscription
invoices.

V5 is not established as an improvement over v4. Moving the same condition
earlier did not resolve the disagreement over its interpretation. The user subsequently
authorized the synthetic example draft below and then its eight-request
targeted panel. That completed v6 panel tests Cuisine and Food dishes alongside
Beverages and Mental states, with two independent draws per group. Unsupported
parent restrictions remain separate from the later note-set check.

Twenty-six production-adapter, assembly and revision checks pass after syncing
current local main. The v5 assembly hash and shared Bootstrap clauses remain
unchanged; the prompt remains experimental.

## Consolidation-v6 synthetic example draft

The user approved adding an example and explicitly required it to be synthetic
and unrelated to the tests.
[Hierarchy-consolidation-v6](shr_single_pair/Hierarchy-consolidation-v6.md)
adds exactly one input/output example to unchanged v5 wording. It uses Blue
shapes as the supplied parent, with Squares of any color, Blue triangles,
Blue rectangles and Blue circles as siblings. The output proposes Blue
polygons above the two wholly covered siblings, triangles and rectangles.

The example teaches the scope constraints through a useful non-null grouping:
Squares cannot acquire a blue-only restriction from existing placement;
Blue circles fit the supplied parent but not the proposed polygon category;
and a proposed polygon meaning allowing any color would extend beyond the
supplied parent. All definitions, IDs and the answer were authored for this
example, without copying a corpus entry, saved judgment or regression label.
None of its topic names occurs in the nine frozen regression inputs. Its two
JSON blocks parse, and removing the example reconstructs v5 exactly.

The [assembly manifest](shr_single_pair/Hierarchy-consolidation-v6.assembly.json)
reuses v5's unchanged before-wrapper and all nine shared Bootstrap-v104
clauses and separators. Only the after-wrapper is new. The shared runner's
native `revise` uses last human-approved v3 as the baseline and records the
[revision provenance](shr_single_pair/Hierarchy-consolidation-v6.md.revision.json).
The complete v6 SHA-256 is
`591c92c0677b027fa6b2e3576c58bf2201511f03e5aee6d85fdca7e1890abe42`.
Historical prompts, definitions, test inputs and saved receipts are unchanged.

The production assembly test first failed on the missing v6 manifest, then
passed. Twenty-seven production-adapter, assembly and revision checks pass,
including native preparation freezing the complete v6 text without inference.
The input/output contract is unchanged. At the draft checkpoint there were no
new model calls and the counter was **309/309**. V6 remains experimental after
the completed panel below. This task remains isolated in its worktree, with
no hierarchy or UI changes.

## Consolidation-v6 focused proposal panel

The user authorized the proposed eight-attempt panel: roots, Mental states,
Cuisine and Food dishes, each with two independent draws. All eight GPT-6.1 Sol
medium subscription attempts completed with valid native receipts and distinct
upstream response references. The persistent counter reached **317/317**.
There were no failures, retries, warmups, exact reuses or missing usage; no
requests remain under this panel's allowance.

Native `prepare --from` retained the exact complete v5 inputs, evidence and
runner settings and changed only the consolidation prompt. Native `--repeat`
dispatched fresh requests with identical complete v6 prompts and settings.
The sole v5-to-v6 text change is the unrelated synthetic example; the nine
shared Bootstrap-v104 clauses and all supplied fixed meanings are unchanged.
Historical answers and judgments remain outside model input.

| Complete supplied group | First draw | Fresh repeat | Bounded agent assessment |
|---|---|---|---|
| Roots: 7 | Beverages: Coffee C006, Slush drinks C039 | Beverages: same children, changed definition | Both accept |
| Mental states: 6 | States of mental alertness: Brain fog and mental clarity C050, sleepiness C092 | Motivational states: Perceived needs C047, Desires C076 | Both accept; different useful subsets are permissible |
| Cuisine: 6 | Italian-origin dishes: Pizza C054, Risotto C073 | Cooked dishes: those two and Cheesesteaks C066 | Both uncertain |
| Food dishes: 6 | Bread-based dishes: Burgers C036, Bread C068 | Meat and meat-alternative dishes: Burgers C036, Chicken dishes C114 | Both uncertain |

The two scope concerns therefore still appear under the initial interpretation:

- **Food dishes, first draw:** Bread-based dishes requires foods “served or
  eaten as a meal or part of a meal.” Selected Bread's fixed meaning only
  requires food made by cooking flour-based dough, with no meal condition.
  Under the required-role reading, it excludes part of the child's meaning. Neither
  existing placement nor the proposed parent's definition can add the missing
  condition to immutable Bread.
- **Cuisine, repeat:** Cooked dishes requires a finished food made by cooking
  at least one ingredient. It does not require the association with a style or
  culinary tradition in Cuisine's fixed meaning. An improvised cooked dish
  lacking that association still fits the proposed category under that reading;
  the breadth of Cuisine's associated-dishes scope remains disputed.

The first Cuisine proposal is promising because it explicitly requires a
connection to Italy's culinary traditions. Risotto's fixed meaning identifies
it as Italian, but Pizza's definition does not state origin; whole Pizza
coverage remains unresolved rather than receiving an old comparison label.
The second Food dishes proposal retains the meal-role requirement. Burgers'
fixed meaning states a cooked patty served in a bun without an explicit meal
role, so this analogous question also remains unresolved. Neither assessment
is new human gold or an independently validated placement.

All eight native prospective shape checks pass: each proposal would strictly
narrow the affected note sets and leave both affected groups at or below six
choices. Roots would shrink from seven to six; the other groups from six to
five, except Cooked dishes would leave four. These structural successes do not
settle semantic judgments. Every report records `applied: false`; no hierarchy
was generated or changed.

Native `review` initially appended four accepts, two rejects and two uncertain
assessments. The rejects now have uncertain reassessments, yielding four
accepts and four uncertain current assessments. Saved answers and receipts
are unchanged. Neither the initial count nor the corrected count is an
accuracy estimate or a validated improvement over v5. The synthetic example
has not demonstrably resolved the disputed interpretations.

The ignored experiments are `consolidation-v6-focused-roots-first-v1`,
`consolidation-v6-focused-roots-repeat-v1`, `consolidation-v6-focused-first-v1`
and `consolidation-v6-focused-repeat-v1` under
`target/canonical-shaping-selection-v1/`. Their `*-report-v1.json` snapshots
preserve exact pre-review outputs, and native `show` retains the bound reviews.
The committed [usage selection](shr_single_pair/hierarchy-consolidation-v6-usage-v1.json)
reproduces native `consolidation-v6-usage-v1.json`: **14,438 input tokens**,
zero cache reads/writes, **2,714 output tokens including 2,211 reasoning tokens**,
and complete **$0.056016 API-equivalent catalog cost**. Reasoning is already
included in output; this is not subscription billing or a caching experiment.

Twenty-seven production-adapter, assembly and revision checks pass after
syncing current local main. All eight receipt identities and matched controls
were checked offline. Prompt text remains unchanged from the v6 draft; no
Compare calls, graph insertions, UI changes or agent messages occurred. The
consolidation task remains isolated as requested.

## Consolidation-audit-v1

The user approved four diagnostic requests before another wording edit: audit
the two initially rejected v6 proposals twice each using unchanged meanings. Experimental
[Hierarchy-consolidation-audit-v1](shr_single_pair/Hierarchy-consolidation-audit-v1.md)
receives the complete original `parent` and `siblings`, plus the exact saved
`proposal`. It returns `covers_children`, `fits_parent`, `valid` and a brief
`reason`; it cannot rewrite meanings, generate a replacement or establish
placement. No agent verdict, expected answer or identified failure enters
model input. The Compare prompt and all Bootstrap shared clauses are unchanged.

The native `canonical_consolidation_review` adapter reuses the existing saved
proposal loader rather than manually assembling cases. Hash-bound producer
references, frozen inputs, native receipt validation and protected source
hashes are retained; whole-group review creates one case per proposal, while
the existing `canonical_consolidation_pairs` path still creates edge checks.
The new production-path test first failed on the unknown adapter, then passed
after this bounded extension. A second test rejects null proposals and changed
producer references before inference. Review evidence and labels stay outside
the rendered input. This adds no production shaping or validation stage.

All four GPT-6.1 Sol medium requests complete successfully through main's
shared runner, with four distinct fresh native receipts. Native `--repeat`
keeps the full prompts, inputs and settings identical and dispatches new
requests. There are no retries, reuses, warmups or missing usage. The counter
advances from **317/317 to 321/321** under the four-request diagnostic allowance.

| Saved proposal | First audit | Fresh repeat | What the brief explanations check |
|---|---|---|---|
| Bread-based dishes under Food dishes, selecting Burgers and Bread | All three booleans true | All three booleans true | Bread is explicitly included; Burgers has a bun or roll |
| Cooked dishes under Cuisine, selecting Pizza, Cheesesteaks and Risotto | All three booleans true | All three booleans true | These foods have cooked ingredients; Cuisine covers culinary dishes |

Neither Bread explanation addresses the proposal's added meal-role condition.
Neither Cuisine explanation requires the tradition association in the supplied
parent definition. These are disagreements with the recorded bounded agent
assessments, not independently established human errors or direct access to
the model's internal process. The hypothesis that generation alone fails while
focused auditing reliably agrees with the agent's rejection criteria is not
supported by this screen. Required-condition interpretation remains unresolved.

The native first-draw and repeat artifacts are `consolidation-audit-v1-first-v1`
and `consolidation-audit-v1-repeat-v1` under
`target/canonical-shaping-selection-v1/`, with exact `*-report-v1.json` snapshots.
The [usage selection](shr_single_pair/hierarchy-consolidation-audit-v1-usage.json)
reproduces native `consolidation-audit-v1-usage-v1.json`: **3,802 input tokens**,
zero cache reads/writes, **688 output tokens including 306 reasoning tokens**,
and complete **$0.014484 API-equivalent cost**. Reasoning is included in output;
catalog cost is not a subscription invoice.

Twenty-nine relevant consolidation, assembly and revision checks pass. The
broader suite runs 169 tests with 19 failures and six skips: old configurable
concurrency and sequential backoff expectations conflict with the current
shared queue, and the parent-guide preparation test lacks `tiktoken`. Three
representative failures reproduce with the committed baseline test definitions;
this task has not repaired or claimed a passing full runner suite. The new
adapter's preparation, receipt binding and native execution checks pass.

The v7 hypothesis below is that a containing meaning's required conditions must
already hold throughout the contained meaning. Naming a child as an included
kind cannot exempt it from those conditions. This is a tested wording hypothesis,
not a new graph guard or semantic gold.
It follows the official [reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices)
in using explicit success criteria, direct instructions and a brief decision
explanation without requesting a reasoning trace. That guidance does not
establish this particular semantic rule or resolve the disputed boundaries.

## Consolidation-v7 required-condition revision and panel

The approved follow-up drafts and tests
[Hierarchy-consolidation-v7](shr_single_pair/Hierarchy-consolidation-v7.md).
The four audits above do not support the hypothesis that focused auditing
reliably recognizes violations missed during generation. V7 therefore targets
the interpretation of required conditions, changing only `Check the proposal`:
every condition in the proposed meaning must already follow from each child's
entire meaning, and every condition in the supplied parent must follow from
the entire proposed meaning. Conditions may follow from topic identity without
matching words. Customary uses, associations, included names and existing
placement cannot supply missing conditions or waive required ones.

The input/output contract, sibling-eligibility stage, synthetic example and
all nine shared Bootstrap-v104 clauses remain unchanged. The
[assembly manifest](shr_single_pair/Hierarchy-consolidation-v7.assembly.json)
reuses v6's exact parts except the versioned after-wrapper. Native `revise`
uses last human-approved v3 as the baseline, with its
[revision receipt](shr_single_pair/Hierarchy-consolidation-v7.md.revision.json).
The full v7 SHA-256 is
`43e98314b418f517c211e8b1d307aeb319ba8c6d29c603fc3c96a0835553dcf5`.
The assembly test first failed on the missing v7 manifest, then passed with
the complete version and provenance. Historical prompt bytes remain fixed.

Eight fresh GPT-6.1 Sol medium requests test the same four complete v6 groups
twice. Native preparation retains inputs, evidence and runner settings;
`--repeat` dispatches independent requests with identical full v7 prompts.
All eight validate with distinct upstream receipts; there are no retries,
reuses, warmups or missing usage. The persistent counter reaches **329/329**,
including the four audits and eight follow-up requests authorized in this
iteration. Source and prompt text stay frozen during execution.

| Complete supplied group | First draw | Fresh repeat | Bound agent review |
|---|---|---|---|
| Roots: 7 | Beverages: Coffee C006, Slush drinks C039 | Same children, changed definition | Two accepts |
| Mental states: 6 | Subjective cognitive states: Brain fog and mental clarity C050, sleepiness C092 | Motivational states: Perceived needs C047, Desires C076 | Two accepts; alternative useful subsets |
| Cuisine: 6 | Cooked dishes: Pizza C054, Cheesesteaks C066, Risotto C073 | Bread-based dishes: Pizza and Cheesesteaks | Two uncertain parent-fit assessments |
| Food dishes: 6 | Bread-based foods: Burgers C036, Bread C068 | Bread-based dishes: same children | Two uncertain whole-child assessments |

Both Food dishes outputs impose a meal role on unrestricted Bread. The first
also explicitly illustrates its category with “bread itself”; the revised
instruction against exempting named children from conditions has not removed
this output. Neither Cuisine definition states the tradition association
required under the recorded agent interpretation of its supplied parent.
The four initial rejections applied the same criteria as the prior panels.
All now have appended uncertain reassessments. Native reviews preserve the
disagreement and history without promoting the expectations to human gold.

All eight prospective shape checks pass with strict note-set narrowing and
at most six choices in both affected groups. Roots would shrink seven to six;
other groups six to five, except the first Cooked dishes grouping leaves four.
Every proposal remains unapplied. Structural success does not resolve these
semantic disagreements or establish hierarchy quality.

V7 and v6 each currently have four bounded agent accepts and four uncertain
assessments. Their initial rejection counts used an unsettled interpretation
and do not establish failure rates. Two draws per group cannot establish a
reliability change, and different useful topics may select different subsets.
No improvement is demonstrated. Whether Food dishes' meal condition requires
a role throughout its contents or characterizes the food kind remains open.
The v8 draft below simplifies the instructions while retaining this dispute;
the hierarchy containment assumption and fixed original meanings remain unchanged.

The ignored native experiments are `consolidation-v7-focused-roots-first-v2`,
`consolidation-v7-focused-roots-repeat-v2`, `consolidation-v7-focused-first-v2`
and `consolidation-v7-focused-repeat-v2` under
`target/canonical-shaping-selection-v1/`. Version-one directories were prepared
but never run; preparation was repeated after syncing changed main code,
preserving all inputs and settings without spending extra attempts. Exact
`*-report-v1.json` snapshots preserve pre-review outputs; native `show` retains
the source-bound assessments. The committed
[usage selection](shr_single_pair/hierarchy-consolidation-v7-usage-v1.json)
reproduces native `consolidation-v7-usage-v1.json`: **15,422 input tokens**,
zero cache reads/writes, **3,540 output tokens including 3,078 reasoning tokens**,
and complete **$0.066244 API-equivalent cost**. The audit's separate subtotal
is $0.014484; neither is subscription billing.

Thirty relevant consolidation, assembly and revision checks pass after the
main sync. The broader-suite limitations recorded above remain unresolved;
this is not a claim that the full runner suite passes. Prompt definitions,
receipt identities, matched controls and usage source paths were checked.
No Compare requests, graph changes, UI updates or agent messages occurred.
The task remains isolated as requested; v7 is tested and experimental, not
human-approved or activated.

## Consolidation-v8 draft and evaluation correction

The user approved fixing the four findings from the prompt audit and requested
a draft. [Hierarchy-consolidation-v8](shr_single_pair/Hierarchy-consolidation-v8.md)
implements that request; it has not been trialed or approved as a complete
prompt. Its input remains the immediate parent or null and the complete sibling
group, with fixed titles and meanings. Its output remains JSON null or exactly
`title`, `meaning` and `children`. Ordinary comparison still owns placement.

The redundant sibling-versus-existing-parent precheck is removed. A single
proposal-check section states whole-child coverage, whole and strictly narrower
parent fit, and the complete child list with at least two members and fewer
than the full group. Under the existing containment assumption, these checks
also establish selected-child fit beneath the existing parent. Repeated
constraints elsewhere in the wrappers are removed without choosing a preferred
Bread or Cuisine interpretation.

The first eight shared definition files remain hash-identical. The new neutral
consistency fragment is a byte-exact prefix of the old ninth file and appears
once in both the preserved Bootstrap-v104 text and v8. Only the Bootstrap-specific
instruction to return a null meaning is omitted. Consolidation's whole-response
JSON-null policy now appears solely in its output section, including unresolved
material ambiguity. Historical shared files, Bootstrap prompts and reconstruction
recipes are unchanged; no new Bootstrap consumer or agent consultation is added.

The synthetic example retains Blue shapes, the same four siblings and the same
Blue polygons output. Squares' definition no longer says it may have any color.
The explanation now teaches that the absent blue restriction cannot be supplied
by existing placement. No corpus entry or regression answer is copied into the
example, and no extra example is added.

The fourth correction concerns evaluation, not an instruction to force a
particular grouping. The user agreed that the meal-role and Cuisine-association
interpretations remain unsettled. Native `review` appended role-agent uncertain
reassessments to fourteen previous rejects:

| Prior panel | Corrected cases | Number |
|---|---|---:|
| v3 expanded first | Cuisine and Food dishes | 2 |
| v4 expanded first / repeat | Food dishes first; Cuisine repeat | 2 |
| v5 expanded first / repeat | Cuisine and Food dishes in both | 4 |
| v6 focused first / repeat | Food dishes first; Cuisine repeat | 2 |
| v7 focused first / repeat | Cuisine and Food dishes in both | 4 |

The original verdicts remain in native review history. Earlier Compare outputs
and counterexamples are retained as model observations, not semantic gold.
Coffee's strict note-set violations and separate child-list completeness
concerns are not reclassified by this boundary correction. V6 and v7 now each
have four qualified agent accepts and four uncertain current assessments;
neither panel supplies a verified semantic failure rate. No new human verdict
on an individual proposal is inferred. Offline checks confirm v6/v7 answers,
parsed outputs, receipts, input hashes, raw metadata and usage are unchanged.

The new [assembly manifest](shr_single_pair/Hierarchy-consolidation-v8.assembly.json)
pins the new wrappers, neutral consistency fragment and all unchanged shared
parts. The shared runner's native `revise` uses last approved v3 as its baseline;
the [revision receipt](shr_single_pair/Hierarchy-consolidation-v8.md.revision.json)
records full v8 SHA-256
`5bb245a302a18f3e34bee56636509bfa221b1930a8f88e57ed2b8bee8fde7b42`.
V8 is 917 whitespace-delimited words versus v7's 1,195; this is a text-length
comparison, not a token, API-cost or quality measurement. The ignored preview,
edits and native full-context diff remain under
`target/canonical-shaping-selection-v1/consolidation-v8-*`.

The new production assembly check first failed on the missing v8 manifest.
Thirty-one relevant consolidation, assembly and revision checks pass after
syncing current main, including native preparation freezing complete v8 text
without inference and preserving historical v3/v7/v104 hashes. Existing broader
runner-suite limitations remain documented above. No model, warmup or Compare
requests were made; the attempt counter remains **329/329**. No hierarchy or
UI changed, and no messages were sent to another agent. The task remains in its
isolated worktree as requested. Next review the draft and qualify clear controls
separately from the disputed semantic diagnostics before claiming improvement.

## Consolidation-v9 definition-writing simplification

After identifying the repeated identity, boundary and role instructions in v8,
the user authorized fixing them. [Hierarchy-consolidation-v9](shr_single_pair/Hierarchy-consolidation-v9.md)
combines those instructions into one new 198-word definition-writing fragment.
It retains coherent interpretation, identity and alternatives, required versus
optional features, explicit roles and purposes, activity boundaries, consistent
restrictions, non-exhaustive illustrations and required absences. Task-specific
JSON-null behavior stays in the consolidation wrapper. This is a wording
hypothesis, not a demonstrated semantic improvement or a Bootstrap revision.

The input and useful-parent sections retain their wording. The proposal checks,
synthetic example and output section are byte-identical to v8. No preferred Bread
or Cuisine verdict is added. Supplied canonical meanings and historical reviews
remain fixed; the unsettled boundaries recorded above remain open.

The [assembly manifest](shr_single_pair/Hierarchy-consolidation-v9.assembly.json)
pins the new fragment and wrappers. Native `revise` again uses last approved
full consolidation v3 as baseline; the
[revision receipt](shr_single_pair/Hierarchy-consolidation-v9.md.revision.json)
records SHA-256
`751c9d83c43fa69ca1f57042a95cc5574eed8a556e57b1547c4bb38b9baf6beb`.
Full text is 728 whitespace-delimited words versus v8's 917; this is not a token,
API-cost or quality measurement. The ignored preview, edits and native diff are
under `target/canonical-shaping-selection-v1/consolidation-v9-*`.

The approach follows the official guidance to
[keep instructions simple and direct](https://developers.openai.com/api/docs/guides/reasoning-best-practices)
and [remove repetitions one group at a time, then rerun the same evaluations](https://developers.openai.com/api/docs/guides/latest-model).
The synthetic example is retained to teach the missing-restriction distinction.
These recommendations motivate the draft; they do not certify its performance.

The production assembly check first failed on the missing v9 manifest, then
passed. Thirty-two relevant consolidation, assembly and revision checks pass,
including native preparation freezing complete v9 text without inference.
Historical v8 and Bootstrap-v104 hashes remain unchanged. Broader runner-suite
limitations remain recorded above. No provider calls, graph or UI changes, or
agent messages occurred; the attempt counter remained 329/329 at this draft
checkpoint. The following section records the subsequently authorized matched
trial. The task remains isolated as requested.

## Consolidation-v8/v9 matched panel

The user authorized sixteen additional GPT-6.1 Sol medium subscription attempts
for four complete groups, both prompts and two independent draws per prompt.
The persistent counter advanced from 329/329 to **345/345**. All sixteen requests
are valid, with distinct upstream response references and reported GPT-6.1 Sol.
There are no failures, retries, reuses, warmups or missing usage. Native queue
recovery delayed admission; it cleared without changing account limits or
bypassing backoff. No allowance remains from this panel.

The shared runner's `prepare --from` freezes the same v7 source cases for v8
and v9. Complete inputs, original evidence, schema and worker settings match.
The ordinary request format is retained; only prompt wording differs between
versions. Repeats are prepared from each completed first draw with `--repeat`.
Offline equality checks confirm their prompts, cases and settings are unchanged.
Neither saved answers nor reviews enter a later model input. The prompts and
source code stay fixed during execution.

| Complete supplied group | V8 first / repeat | V9 first / repeat | Current bounded agent assessment |
|---|---|---|---|
| Roots: 7 | Beverages: Coffee + Slush drinks, both draws | Same children, both draws | Four accepts |
| Mental states: 6 | Alertness: Brain fog and mental clarity + sleepiness; then Motivational states: Perceived needs + Desires | Same respective children | Four accepts; two useful alternative subsets |
| Cuisine: 6 | Prepared dishes: Pizza + Cheesesteaks + Risotto, both draws | Same children, both draws | Four uncertain parent-fit judgments |
| Food dishes: 6 | Dough and batter dishes: Pancakes + Bread, both draws | Dough and batter foods: Pancakes + Bread; then Bread-based foods: Burgers + Bread | Four uncertain whole-child judgments |

Native role-agent reviews preserve four qualified accepts and four uncertain
judgments for each prompt. This is not human gold or an accuracy estimate.
The clear controls preserve coverage and parent fit in both draws. The disputed
cases still turn on Cuisine's associated-dishes scope and Food dishes' meal
condition as a food-kind or particular-instance role. The panel does not settle
either convention. Changed valid subsets are not themselves errors.

All sixteen prospective local grouping checks pass: roots shrink seven choices
to six, Mental states and Food dishes shrink six to five, and Cuisine shrinks
six to four. Each proposed parent has two or three children and strictly larger
distinct-note sets than its individual children; it is narrower than an existing
parent's note set. These are source-bound local checks, not full traversal or
semantic validation. All proposals remain unapplied; no hierarchy or UI changed.

One writing issue deserves a targeted follow-up. V9's repeated Food dishes answer
adds a separate sentence defining Bread after defining Bread-based foods. V8's
shared rule says “Define the selected topic, not every concept it mentions.”
V9 omitted that general instruction and retains a narrower instruction against
separate technical definitions only for activities. The omission is established
by the prompt diff; one output cannot establish its causal effect or a regression
rate. The extra sentence is unnecessary here, not evidence that the disputed
grouping is wrong. The user subsequently authorized restoring the general rule
in the v10 draft below. Bootstrap remains unchanged.

The committed [usage selection](shr_single_pair/hierarchy-consolidation-v8-v9-matched-usage-v1.json)
reproduces native `consolidation-v8-v9-matched-usage-v1.json` under
`target/canonical-shaping-selection-v1/`:

| Native usage and saved catalog pricing | V8: 8 attempts | V9: 8 attempts |
|---|---:|---:|
| Input tokens | 12,798 | 11,086 |
| Cached input / cache-write tokens | 0 / 0 | 0 / 0 |
| Output tokens, reasoning included | 2,598 | 2,056 |
| Reasoning tokens, a subset of output | 2,120 | 1,630 |
| API-equivalent total cost | $0.051576 | $0.042732 |

The observed API-equivalent reduction is **17.15%**, calculated as
`(0.051576 - 0.042732) / 0.051576`. Inputs drop 13.38%; every corresponding
request is 214 input tokens shorter. Outputs drop 20.86% in these particular
draws. Output variability means the observed cost reduction is not a guaranteed
saving or an isolated measurement of the input change. The full panel costs
$0.094308 at saved catalog prices; subscription billing is not inferred.
Native accounting totals include reasoning once, retain zero cache observations,
and have no missing-cost or missing-usage qualifications.

Ignored experiments are `consolidation-v{8,9}-matched-roots-{first,repeat}-v1`
and `consolidation-v{8,9}-matched-{first,repeat}-v1`. Native `*-report-v1.json`
snapshots preserve the outputs before reviews; `show` retains the attributed
assessments. Offline checks confirm answers, parsed outputs, receipts, raw
metadata, usage and input hashes remain unchanged after review. Thirty-two
relevant consolidation, assembly and revision checks pass after syncing local
main. Broader suite limitations remain recorded above. No Compare calls,
Bootstrap edits, graph changes, UI updates or agent messages occurred.
V9 is tested and experimental, not human-approved as a full prompt or activated.
The task remains isolated as requested. The targeted restoration is now drafted
below; broader clear controls remain the recommended next evaluation rather
than treating repeated disputed judgments as progress or failures.

## Consolidation-v10 topic-definition rule restoration

The user authorized the targeted edit following the matched panel.
[Hierarchy-consolidation-v10](shr_single_pair/Hierarchy-consolidation-v10.md)
adds exactly “Define the selected topic, not every concept it mentions.” after
the standalone-definition instruction. Removing that insertion reproduces v9
byte for byte. The sentence is retained verbatim from v8; no test-specific
topic, preferred grouping or additional example is introduced.

The [assembly manifest](shr_single_pair/Hierarchy-consolidation-v10.assembly.json)
pins the new 207-word shared fragment and unchanged v9 wrappers. Historical
fragments, prompts and Bootstrap-v104 reconstruction hashes remain fixed.
Native `revise` uses the last approved full consolidation v3 as baseline. Its
[revision receipt](shr_single_pair/Hierarchy-consolidation-v10.md.revision.json)
records the full output SHA-256
`53cc0c8d4aa71db22408da13b60958a141d07cadc3df46cd43e1458e0f5cc452`.
The full prompt has 737 whitespace-delimited words. This count is not a token
or API-cost measurement; the previous panel's observed savings apply to v9.

The production assembly check first failed because the v10 manifest was absent,
then passed after authoring. Thirty-three relevant consolidation, assembly and
revision checks pass, including native preparation freezing complete v10 text
without inference. The exact v9 delta and the historical v9/v104 hashes are
checked. Broader runner-suite limitations remain recorded above. The ignored
preview, native edits and full-context diff are under
`target/canonical-shaping-selection-v1/consolidation-v10-*`.

At this draft checkpoint, no provider, warmup or Compare calls were made and
the attempt counter remained **345/345**. No graph, UI, Bootstrap or active
policy changed, and no messages were sent to another agent. V10 was an isolated
draft without a model trial or activation. The following section records its
subsequently authorized clear-control screen. Bread/Food dishes and Cuisine
scope judgments remain unresolved; repeated disputed judgments cannot establish
accuracy.

## Consolidation-v10 clear-control screen

The user authorized proceeding with the clear-control test. The screen is
bounded to four additional GPT-6.1 Sol medium subscription attempts, advancing
the persistent counter from 345 used to **349/349**. All four are fresh and
valid, with distinct upstream response references and HTTP 200 metadata naming
GPT-6.1 Sol. There are no failures, retries, warmups, reuses or missing usage.
At most two requests from this screen run concurrently, within the shared native
queue; no service limit is changed.

Native `prepare --from` inherits the matched v9 inputs and settings. `--only`
selects Mental states without changing its complete sibling group. The first
draws preserve the v9 rendered prompts except for the one restored sentence.
Native `prepare --from FIRST --repeat` requests independent second draws;
offline checks confirm their complete prompts, inputs and settings match the
first draws exactly. Ordinary SSE transport and the saved response schema stay
fixed. Old answers and reviews remain outside model input. Bread/Food dishes
and Cuisine are excluded because their expected containment judgments are still
unsettled; this is not a full rerun of the earlier panel.

| Complete supplied group | First draw | Independent repeat | Bounded agent assessment |
|---|---|---|---|
| Roots: 7 | Beverages: Coffee C006 + Slush drinks C039 | Same title and children | Two accepts |
| Mental states: 6 | Motivational states: Perceived needs C047 + Desires C076 | Same title and children | Two accepts |

All four standalone meanings define the selected topic without separately
defining an illustrative member or component. The Beverages meanings admit
partially frozen drinks. The Motivational states meanings preserve wanting and
perceived necessity and fit within cognitive or emotional Mental states.
This is a bounded agent assessment, not human gold or an accuracy estimate.
Passing these controls does not prove that the restored sentence caused the
observed behavior or fixed the separate Bread-definition issue.

All four native prospective grouping checks pass. Roots would shrink seven
choices to six; Mental states would shrink six to five. Each proposal groups
two children and has a larger distinct-note set than each child; the proposed
Mental states subgroup is smaller than its existing parent. Every report
retains `applied: false`. These are local shape checks, not full traversal or a
newly generated hierarchy, and no existing branch or immutable meaning changes.

The committed [usage selection](shr_single_pair/hierarchy-consolidation-v10-clear-usage-v1.json)
reproduces native `consolidation-v10-clear-usage-v1.json` under
`target/canonical-shaping-selection-v1/`. It records 5,480 input tokens, zero
cached-input/write tokens, and 1,184 output tokens including 981 reasoning
tokens. Complete API-equivalent catalog cost is **$0.022800**; reasoning is
counted once. This is not subscription billing or a matched savings estimate.
The previous v8/v9 savings measurement remains separate.

Ignored experiments are `consolidation-v10-clear-{roots,mental}-{first,repeat}-v1`.
Native `*-report-v1.json` snapshots preserve outputs before the four attributed
role-agent reviews. Post-review snapshots retain exact answers, parsed outputs,
receipts, raw metadata, usage and input hashes. The prompt and source remain
fixed throughout the screen. Thirty-three relevant consolidation, assembly and
revision checks pass after syncing current main. Broader runner-suite limitations
remain recorded above. No Compare calls, Bootstrap edits, graph changes,
UI refresh or agent messages occur. The work remains isolated as requested.
V10 is tested and experimental, not approved as a full prompt or activated.
The subsequently authorized broader screen below adds the other saved groups
and the historical null diagnostic. Disputed scope judgments remain a separate
review problem, and this four-attempt allowance is exhausted.

## Consolidation-v10 broader screen

The user authorized broadening the controls, including expected-null cases.
The screen is bounded to eight additional GPT-6.1 Sol medium subscription
attempts: two independent draws on four complete original ASv6.100 sibling
groups. The persistent counter advances from 349 used to **357/357**. All eight
have fresh valid native receipts and distinct HTTP 200 upstream references
reporting GPT-6.1 Sol. There are no reuses, warmups, retries, failures or missing
usage. The native shared queue admits at most four requests from this screen
concurrently; no service limit is changed.

Native `prepare --from` inherits the v5 first-draw inputs and settings, changes
only the prompt to unchanged v10, and uses `--only` to preserve each selected
group in full. Food preparation has seven siblings, Food thirteen, Cooking
appliances four and Eating five. All original source hashes, complete inputs,
input digests and review evidence match; the v10 prompt hash is the only new
source-map entry. The initial blanket source-map equality assertion was too
strict because it also compared that new prompt entry. The corrected comparison
confirms that no original source changes. Native `--repeat` requests independent
second draws with byte-identical complete prompts, cases and settings. The
ordinary SSE request format and saved response schema remain fixed; historical
answers and assessments do not enter model input.

Eating is a provisional null diagnostic, not a certified negative. Its earlier
repeated nulls do not establish that no valid useful parent exists. Any new
non-null proposal would be assessed on its meaning rather than rejected for
differing from those old answers. Bread/Food dishes and Cuisine remain outside
this screen because their expected scope judgments are unsettled.

| Complete supplied group | First draw | Independent repeat | Bounded assessment |
|---|---|---|---|
| Food preparation C005: 7 | Bakery and dessert preparation: Bread preparation C010 + raw no-bake pie preparation C098 | Bakery food preparation: same children | Two qualified accepts |
| Food C001: 13 | Daily meals: Breakfast C018 + Dinners C059 | Meals of the day: same children | Two qualified accepts; partial choice reduction |
| Cooking appliances C014: 4 | Cooking vessels: Stockpots C015 + Cast-iron cookware C105 | Same title and children | Two qualified accepts |
| Eating C123: 5 | JSON null | JSON null | Two qualified null accepts; no exhaustive impossibility claim |

The bakery definitions retain individual preparation stages and explicitly allow
no-bake methods. Classification of the named raw matcha-cashew pie as a bakery
food or dessert is an ordinary topic-identity interpretation, not independently
validated human gold. The meal definitions require a day/waking-period timing
or main-meal role, retain planned dinners and the supplied associated information,
and exclude sibling topics that do not wholly require that role. They do not
reuse the earlier broader generic Meals definition. Cooking vessels preserves
container identity; it adds no heat-generation or power requirement that would
exclude the chosen vessels. Its immediate supplied parent defines devices
designed to cook food. This assessment does not validate an existing ancestor
branch or settle equivalence with another canonical node.

Eating's null is reasonable because the food-kind and dietary-information
siblings extend beyond the supplied consuming activity, while only the named
enjoyment of eating clearly supplies a matching activity or experience. No
evident two-child subgroup is established by this review. This is an attributed
agent assessment, not human gold or proof that all possible proposals fail.
All six non-null meanings define the proposed topic without separately defining
its illustrative members. No clear new wording failure is established in this
screen; passing it does not prove that the restored instruction fixed the
separate Bread-definition issue.

All six non-null proposals have strictly narrowing prospective note sets.
Food preparation would shrink seven choices to six and Cooking appliances four
to three. Food would shrink thirteen to twelve. Its native
`local_group_constraints_met: false` reflects the remaining count above six,
not an equal-note-set edge or a semantic failure. Six is now a best-effort goal,
and this result makes useful partial progress. All reports retain
`applied: false`; no hierarchy, edge, immutable meaning or note support changes.

The committed [usage selection](shr_single_pair/hierarchy-consolidation-v10-broader-usage-v1.json)
reproduces native `consolidation-v10-broader-usage-v1.json` under
`target/canonical-shaping-selection-v1/`. Complete usage is 11,742 input tokens,
zero cached-input/write tokens, and 2,643 output tokens including 2,252 reasoning
tokens. Complete API-equivalent catalog cost is **$0.049914**. Reasoning is
counted once; no subscription charge or matched policy/prompt saving is inferred.

Ignored experiments are `consolidation-v10-broader-{first,repeat}-v1` and
`consolidation-v10-broader-preparation-{first,repeat}-v1`. Native
`*-report-v1.json` snapshots precede the eight role-agent reviews; post-review
snapshots preserve exact outputs, parsed answers, receipts, raw metadata, usage,
input hashes and prompts. Thirty-three relevant consolidation, assembly and
revision checks pass after syncing current main; broader runner-suite limitations
remain recorded above. No Compare calls, Bootstrap edits, graph changes,
UI refresh or agent messages occur. V10 remains tested and experimental in the
isolated worktree, without activation or full-prompt human approval.
The eight-attempt allowance is exhausted. Next assess these proposals through
ordinary placement in a separate saved-graph trial and measure the resulting
browsing choices, rather than make another wording change without a demonstrated
failure. That placement/integration trial has not begun.
