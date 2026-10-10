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
