# Hierarchy generation V2 — FUTURE WORK

**Status: approved V2 design, implemented as `hierarchy-generation-v2`; initial
provider trials HR08–HR10 have started, with no completed hierarchy-quality
qualification.** V2
replaces the previous selection implementation through the existing shared-runner
commands. The FUTURE WORK label denotes pending qualification with real model
judgments, not an alternative opt-in constructor.

The user approved guaranteed L1 selection by prominence, additional L1s for
uncovered notes, prominence-ordered refinement of multi-note leaves, additional
eligibility for deeper entries matching canonical headings, and giving those
entries priority over multi-note-leaf work. Finished-view shaping retains the
specific child of an equal-set single-child parent. For a parent with multiple
children it retains the parent and bypasses equal-set children on that browsing
branch. The canonical graph, meanings, evidence and relationships remain intact.

## Purpose

Build the hierarchy around topics that represent a substantial share of each
note. Ensure every guaranteed L1 is considered, even if every note becomes
represented before all guaranteed L1s have been processed.

L1 means a root in a note's original local hierarchy. L2 is its immediate-child
level, and subsequent local levels continue downward. These levels do not refer
to the resulting canonical hierarchy.

## Establish meaning and prominence

For every L1 of every selected note:

1. Establish its explicit meaning independently using the Bootstrap prompt and
   its original evidence.
2. Run [PPv35-post-meaning-v1](prominence-prompt-goal-v1/ppv35-post-meaning-v1/PPv35-post-meaning-v1.md)
   with `node_title` set to the local heading, `node_description` set to that
   explicit meaning, and `post` set to the complete original post.
3. Save the meaning and prominence together with their exact input and producer
   evidence. Reuse that same meaning during traversal; do not regenerate it to
   fit a canonical comparison.

Prominence is an integer from 0 through 100 estimating the percentage of the
complete post's meaning concerning the supplied topic. It is not confidence in
a relationship. Overlapping L1 topics can each score highly; their separate
scores need not sum to 100.

## Select guaranteed L1s separately for each note

- If at least one L1 has prominence **greater than or equal to 50**, select
  **all** of that note's L1s meeting the threshold for the guaranteed pass.
  Leave its other L1s unused for now.
- If **none** reaches 50, select **only the highest-scoring L1** of that note.

Tie handling: when several L1s share the highest score in the fallback
case, select the first in the note's saved local-node order. This keeps the
fallback to exactly one L1 without an additional model call.

Determine eligibility after all of that note's L1s have valid scores. A failed
meaning or prominence result is unresolved evidence, not a score of zero and
not permission to invoke the fallback using incomplete scores.

Preserve the existing rotation across notes and saved local-node order, taking
one guaranteed L1 per note per pass.

## Guaranteed processing

**Every guaranteed L1 must be processed before construction can stop.**

The first guaranteed L1 seeds an empty canonical hierarchy with its established
meaning. Every subsequent guaranteed L1 follows ordinary local-versus-canonical
traversal and the existing placement checks.

Selection guarantees an opportunity for placement, not admission to the
canonical hierarchy. A guaranteed L1 can become a new canonical node, supply
equivalent support to an existing node, or be held when comparison or validation
prevents placement. Preserve those outcomes and their evidence.

Do not stop merely because browsing conditions pass while guaranteed
L1s remain unprocessed. Starting a search is not enough: its placement or hold
must be recorded, and any triggered consolidation must finish.

## Add remaining L1s only for uncovered notes

After the guaranteed pass and its triggered consolidation finish, check which
notes have at least one original local entry represented in a canonical node.
An equivalent placement counts as representation; a held entry does not.

For a note still absent, select its remaining unused L1s until one is admitted.
Use its already saved prominence scores, taking the highest unused first. Stop
selecting additional L1s for that note once it is represented. Rotate across
uncovered notes when several still need admission.

If every L1 of a note is processed without admission, record that coverage is
unresolved. Do not fabricate support or claim that note is represented.

## Refine multi-note canonical leaves

A canonical leaf has no canonical children. Its note set consists of its
supporting note IDs, deduplicated. Select unused deeper local nodes to refine
leaves containing more than one distinct note.

1. Choose the unfinished leaf containing the most distinct notes. Use saved
   canonical-node order to break ties.
2. For each note in that leaf, identify the original local entries supporting
   the canonical node. Start with those entries' immediate original children,
   regardless of their original level numbers. Do not restart at the note's
   L1 roots or select siblings outside the supporting branches.
3. Establish each eligible child's explicit meaning and run PPv35 using that
   meaning and its complete original post, as for L1. Prominence sets priority;
   there is **no 50-point cutoff** at these deeper levels.
4. Rotate across the leaf's notes in saved note order. Take the highest-scoring
   unused eligible child for each note on its turn. Break prominence ties using
   saved local-node order.
5. Every selected child follows ordinary traversal of the canonical hierarchy.
   Selecting from a leaf's supporting branch does not force placement beneath
   that leaf. Reassess leaf membership after placements and consolidation.

For a leaf containing notes A, B and C, selection proceeds as:

```text
A's highest unused child -> B's highest unused child -> C's highest unused child
A's next unused child    -> B's next unused child    -> C's next unused child
```

When those immediate children are exhausted and further selection is still
needed, continue to deeper original descendants within the same supporting
branches, processing nearer descendants before more distant ones. Retain each
entry's original numbering; the supporting entries and their children can be
at different original levels in different notes. Continue rotating across
notes and selecting the highest-prominence unused node at the next depth in
its supporting branch. Do not repeat a local node already processed through
another leaf.

**Branch selection approved October 11, 2026:** the user replied
"sure" to starting from the immediate children of each local entry supporting
the canonical node. If both Bread entries below are admitted as support for
canonical Bread, the next candidates are Sourdough bread in both posts:

```text
Sourdough-preparation post
Bread [1]                         <- supporting entry
└── Sourdough bread [1.1]          <- immediate child, original L2

Cranberry-bread post
Food [1]
└── Bread [1.1]                    <- supporting entry
    └── Sourdough bread [1.1.1]    <- immediate child, original L3
```

The cranberry post's Cranberries, Rosemary, Brown sugar and Cinnamon entries
are siblings of its supporting Bread entry beneath Food; they are outside this
Bread branch. Selection still invokes ordinary traversal rather than forcing
canonical placement beneath Bread. This example assumes the Bread admissions;
it does not record new comparison results.

Stop expanding a leaf when it represents one note or its relevant original
local branches have no unused descendants left. Record a multi-note group that
remains after exhaustion. A note represented only at an internal canonical node
does not require additional comparisons solely to create a singleton node for it.

## Additional deeper-entry eligibility — provisional V2 rule

**Approved provisionally October 11, 2026; implemented, not model-qualified.** After
the guaranteed L1 pass, additional L1 work for uncovered notes, and their
triggered consolidation finish, an unused local child is also eligible when:

- Its original immediate local parent has been admitted to the canonical
  hierarchy. Equivalent admission counts; a held parent does not.
- Its heading matches an existing canonical heading whose node does not yet
  represent that child's note. Count own supporting notes plus recursive
  descendants, deduplicating note IDs.

The user's reply to adding this rule was: "ok, i suppose that sounds reasonable".

This first rule uses the same heading wording as a selection hint. It applies
even when the canonical node representing the original parent is a one-note
leaf. The heading match establishes eligibility only, not equivalent meaning or
containment. Establish the child's fixed meaning and PPv35 prominence with its
original evidence; retain prominence priority, round robin across notes, and no
50-point cutoff for deeper entries. Every selected entry follows ordinary
traversal of the whole canonical hierarchy and existing placement checks.
Do not force placement at the matching heading or process the same local entry
twice.

The HR05 Bread case motivates this rule:

| Original post | Local entry | HR05 outcome |
| --- | --- | --- |
| Sourdough preparation | L1 Bread `1` | Admitted as Bread C015, representing this note only |
| Cranberry sourdough | Food `1` -> Bread `1.1` | Food admitted as C004, a one-note leaf; Bread unselected |
| Bread-and-avocado dinner | Food `1` -> Bread `1.2` | Food admitted as C021, a one-note leaf; Bread unselected |

An offline check of HR05's admitted original parents and unused L2 entries
found three candidates with an existing canonical heading that does not yet
represent their note: these two Bread entries and Dinner `1.3` from the
pizza-and-sushi post. Evidence remains in the saved
[HR05 state](../../oracle-mvp-hierarchy-hr05-twenty-four-note-v1/target/hierarchy-hr05-twenty-four-note-v1/HR05/state.json)
and [original subject entries](../../oracle-mvp-hierarchy-hr05-twenty-four-note-v1/target/hierarchy-hr05-twenty-four-note-v1/subjects.json).
No new meanings, prominence scores or comparisons were generated. Their
relationships and any resulting browsing improvement remain untested.

### Approved order within the deeper-node phase

The user accepted this ordering on October 11, 2026: "ok sounds fine".
**Approved for V2; covered by offline native-workflow tests, not a provider trial.**

1. After L1 work, note coverage and their consolidation finish, give eligible
   local children matching existing canonical headings priority. Use PPv35
   priority within each note and round robin across notes, as above.
2. When no such eligible entries remain, select deeper entries for the
   unfinished multi-note leaf containing the most notes. Retain its existing
   prominence priority, note rotation and saved-order tie handling.
3. After each placement and its triggered consolidation, reassess eligibility
   before selecting further entries. A newly admitted canonical heading may
   make other unused local children eligible; give those entries priority
   before continuing multi-note-leaf work. Process each original local entry
   at most once.

In the HR05 Bread case, process the cranberry-bread and dinner-bread entries
before expanding multi-note leaves. If ordinary traversal establishes suitable
relationships, Bread can collect their support; any subsequent deeper selection
uses the resulting note groups. This is a conditional illustration, not a
predicted or observed comparison result.

This rule does not establish discovery of shared topics whose headings differ
or which have no existing canonical node. The broader width/depth objective remains deferred; no global menu optimum is claimed.

## Selection completion and shaping

Selection has no remaining work when every guaranteed L1 has been processed,
every note is represented, no multi-note leaf has eligible unused descendants,
and no unused local child qualifies under the additional heading-match rule.
Any selected entry still needs a recorded placement or hold and completed
triggered consolidation before selection can finish.
Uncovered notes remain an unresolved outcome rather than successful coverage.

The finished browsing hierarchy must strictly narrow the distinct-note set at
every downward edge. Count own supporting notes plus recursive canonical
descendants, deduplicating note IDs. Remove equal-note-set steps while preserving
note access, fixed meanings and valid containment. Equal observed note sets do
not establish semantic equivalence.

**Approved single-child rule:** when a parent has exactly one canonical child
and both represent the same distinct-note set, retain the more specific child
and omit the parent from the finished browsing hierarchy. A root's child becomes
a browsing root. Below another retained ancestor, bypass the omitted parent
using the existing transitive containment relationship.

For example, if `Food {A, B}` has only `Vegetables {A, B}` beneath it, retain
Vegetables. Do not merge their meanings, transfer Food's evidence into
Vegetables, or delete Food from the original construction graph. This rule
changes which canonical nodes appear in the finished browsing hierarchy.

**Approved multiple-child rule (October 11, 2026):** retain the parent created
by consolidation. In the finished browsing view, bypass any child representing
exactly the same notes as that parent and show that child's children directly
beneath the parent. Apply this only on the affected branch; keep useful
placements of the child beneath other parents. Each exposed child has a
transitive containment witness in the original canonical graph.

The user's approval was "agree" to: "I propose keeping the parent created by
consolidation. If a child represents exactly the same notes as that parent,
remove the child's navigation step and show its children directly beneath the
parent. This changes the browsing view only. The canonical nodes, meanings,
evidence and relationships remain intact."

When bypassing a leaf, preserve access to its notes at the retained parent.
These display-only `note_ids` are derived from the original graph's represented
notes; they are not new canonical supporting entries. The requested viewer
export exposes them as notes, while retaining separate original-support labels.
The finished view preserves each retained node's original represented note set.

Consolidation is not rejected merely because it creates equal-note-set edges.
Ordinary traversal, semantic placement checks, immutable meanings and valid
nominated-child relationships still apply. Construct the finished view from the
raw graph after placement and consolidation, retaining the raw graph unchanged.

Selection exhaustion can finish with an unrefined multi-note leaf; its notes
remain individually accessible. It cannot claim completion with missing note
coverage or unresolved L1 scoring. Provider errors, interrupted retries and
budget exhaustion remain native execution limits, not permission to invent
support. Broader depth optimization remains deferred.

## V2 — FUTURE WORK: consolidation investigation

**Offline structural findings, not an approved shaping rule or semantic
validation.** The controls assume fixed meanings and valid containment; no model
calls were made. They exercise the existing `_placement`, `_apply`,
`finish_nodes` and `_note_sets` functions at source commit `65e5aa30`.
Inputs, outputs and source hashes are retained in the ignored
[structural controls](../../oracle-mvp-hierarchy-v2-shaping-investigation/target/v2-shaping-investigation/structural-controls.json).

### Moving the check alone does not fix the problem

The refined control starts with six roots: Vegetables, Fruits and four unrelated
topics representing notes C through F. Vegetables represents A and B and has
Potatoes A and Broccoli B beneath it. Fruits represents B. Consolidation proposes
Food above Vegetables and Fruits, covering two of the six offered roots.

The existing placement checks permit the assumed containment relationships.
At that measured source, the consolidation-specific check rejects the raw Food-to-Vegetables edge
because both represent A and B. The original graph remains unchanged. Removing
only that rejection would not secure a useful finished grouping: the existing
shaper removes Food, returning to six roots.

An explicit candidate finished graph instead bypasses Vegetables on Food's
branch and retains Food above Potatoes, Broccoli and Fruits. All its edges have
original transitive containment witnesses. Every retained heading, meaning and
original support entry is unchanged; all retained note sets and global note
coverage are preserved.

| Structural control | Root choices | Largest choice group | Every edge narrows | Selections to a singleton for A / B |
| --- | ---: | ---: | --- | --- |
| Before the proposal | 6 | 6 | Yes | 2 / 1 |
| Raw Food proposal | 5 | 5 | No | 3 / 2 |
| Existing shaper applied to the raw proposal | 6 | 6 | Yes | 2 / 1 |
| Candidate retaining Food and bypassing Vegetables | 5 | 5 | Yes | 2 / 2 |

The candidate reduces root choices but increases B's shortest singleton route
by one selection. This is a tradeoff, not proof of a better hierarchy. Shortest
singleton routes do not measure every way a user may reach a note or choose a
topic. No API-cost or overall-quality improvement is established by this control.

### Refinement and other branches matter

Before Potatoes and Broccoli exist, Vegetables is a multi-note leaf with its own
support for A and B. Bypassing it and retaining synthetic Food above Fruits
loses A: synthetic Food has no original support of its own. Thus coverage alone
at the start of refinement is insufficient to justify this transformation.
It must be checked against the actually available descendants and evidence.

A separate control gives Vegetables another parent whose note set is A, B and
C. Vegetables usefully narrows that branch to A and B. The candidate bypasses
only Food-to-Vegetables, retains Vegetables beneath the other parent, and exposes
Potatoes and Broccoli beneath Food. All retained note sets and containment
witnesses survive. This shows why a child should not be erased globally just
because its edge under one parent is redundant.

### Approved resolution and limits

The approved multiple-child rule above preserves the proposed parent in the
raw graph and bypasses repeated steps only in the finished view. It removes the
old raw equal-note-set rejection. Display-only note access handles an unrefined
bypassed leaf without transferring its original supporting entries to the
synthetic node. Useful placements on other branches remain.

The structural findings remain evidence of the choice/depth tradeoff. They do
not prove overall browsing quality or API savings. No further global browsing
objective, synthetic proposal resampling or additional semantic inference is
introduced by this shaping rule.

## Existing construction rules

Retain immutable canonical meanings, local-versus-canonical comparisons,
top-to-bottom traversal, branch stopping on `neither`, holds on `uncertain`,
transitive containment, exact answer reuse, and placement checks. Up to three
local searches can overlap; placements remain ordered. The experiment runner
controls request concurrency.

Retain best-effort consolidation after a canonical addition leaves six or more
siblings, including roots. Synthetic proposals still require ordinary traversal
and validation. Six remains a trigger, not a hard maximum.

## Work and validation

Meaning generation and prominence scoring cover every original L1, including
those outside the guaranteed pass. Deeper scoring covers eligible entries in
the relevant local branches of multi-note leaves and children qualifying under
the additional heading-match rule, not every deeper entry of every note.
Heading matching uses already available local and canonical headings; it does
not require model judgments for every local/canonical pair. The added scoring
work grows with the entries assessed and their
source-post lengths, not every local/canonical pair. Reuse exact saved meanings,
prominence answers and comparisons where available.

No cost reduction or hierarchy-quality improvement has been measured for V2. Compare actual finished hierarchies and total API-equivalent cost,
including meaning generation, PPv35, traversal and consolidation, before making
either claim.

## Automated preparation and execution

Use the shared stable launcher from an isolated task worktree:

```bash
../experiment-runner/bin/experiment-runner prepare-canonical-traversal \
  target/HR06 --spec traversal.spec.json
../experiment-runner/bin/experiment-runner run-canonical-traversal \
  target/HR06 --attempt-budget allowance.json
```

The traversal spec still names the corpus, selected note IDs, local input schema,
and Bootstrap, Compare and consolidation specs. Preparation pins PPv35's exact
text and derives its runner settings from Bootstrap. All original L1 meanings
are prepared together; the corresponding prominence batch consumes their saved
meanings. Deeper batches contain only currently eligible entries. Each meaning
and score records its native producer case and receipt; all comparisons reuse
the independently established meaning.

`selection_phase` records L1 scoring, guaranteed L1, uncovered-note L1, heading
matches, multi-note leaf refinement or finished selection. Placements preserve
selection order with at most three local searches in flight. Exact answers,
provider retries, prefix warming and the persistent attempt allowance use the
ordinary shared runner. No new provider call is implied by preparing or testing
this implementation. Frozen older trials remain bound to their original source
worktrees; the current constructor has no legacy selection mode.

## Offline implementation verification

Failing-first production checks demonstrated the previous parent-removal rule,
missing prominence selection, unnecessary waiting for other active searches,
and a missing selected-score review check. Native CLI tests now cover guaranteed
roots, threshold/fallback/ties, uncovered-note selection, heading eligibility,
supporting-branch refinement, duplicate-entry prevention, both Compare formats,
producer reviews, accepted equal-set consolidation, note preservation and viewer
export. They use the local fake model transport, not provider judgments.

The broader 275-test run reported 22 failures across 20 existing general-runner
tests and six unavailable artifact/UI checks. All 20 failing methods were rerun
at unchanged baseline `6443dcfc`, producing the same 22 failures and no V2-only
failure method. These include removed external-concurrency expectations,
provider/proxy scheduling assumptions and an unavailable `tiktoken` dependency.
The stable runner was clean at `e19592f9a6b0b3a2b3ac0bc63220156d86a0f1a7`.
Those unrelated failures are reported, not suppressed or fixed by this task.

Frozen older constructor trials and the prior offline structural controls are
unchanged. The original implementation and offline validation used no provider
requests, prompt text edits, hierarchy UI refresh or paid resources. The user
subsequently authorized the three official [HR08–HR10 provider trials](../docs/recommendation-engine/hierarchy-runs.md).
Their initial L1 meanings are saved; prominence preparation exposed an
inherited cache flag on PPv35's ineligible short prefix. Continuation awaits
a tested constructor fix. Finished structure and total API-equivalent cost
remain unqualified.
