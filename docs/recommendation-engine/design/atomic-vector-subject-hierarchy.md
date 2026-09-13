# Atomic-Subject Content Hierarchy

## Status

This is the approved architectural direction for the content-discovery
experiment. It is not a validated system.

Subjects and discovered groups may have different breadths. They are not
required to form a uniformly fine layer before hierarchy work begins. The
frozen subject prompt explicitly permits broad, narrow, nested, and overlapping
subjects; a useful group is not automatically a terminal navigation subject.

The [100-note real-data experiment](../../../sse_multivector/real-note-fine-segmentation-v1/README.md)
uses frozen ASv6.23 subjects and MPv3.5 masks. The current hierarchy investigation
compares the saved [HDBv2/HDBv3 trees and optional note-navigation view](../../../sse_multivector/real-note-fine-segmentation-v1/cross-note-density-v1/README.md),
without generated titles. The comparison starts from HDBv3's complete merge
history rather than only its condensed groups. It omits one-note groups and
collapses parent-child transitions returning the same notes. Coherent groups
do not establish that all their parent placements are useful refinements.
Neither HDBv3 nor this simplification is selected as the final algorithm.

The earlier [controlled qualification and its results](../experiments/fine-segmentation/controlled-run-v1-results.md)
remain experimental evidence. Their frozen protocols and outcomes are not
changed by the later real-note investigation or by this breadth clarification.

## Goal

Build a public, corpus-derived hierarchy that lets a person repeatedly narrow
the subject they want to explore and then inspect notes associated with the
selected subject.

The hierarchy does not infer current intent from ratings or behavior. The
person supplies current intent by choosing among the hierarchy's visible
refinements.

## Separation of Concerns

The system has distinct transformations:

```text
public note
  -> subject-bearing source masks
  -> identical masks within that note deduplicated
  -> one SSE vector per remaining mask
  -> subject-group memberships
  -> broad-to-narrow subject hierarchy
  -> note results for an explicitly selected subject
```

Each stage has an explicit output boundary. A later label or hierarchy must not
conceal a failure in extraction, SSE geometry, or grouping. A test
that deliberately changes source text and re-encodes it before segmentation
qualifies the frozen SSE-plus-segmentation combination; it cannot assign the
result to either stage by itself. These are separate responsibilities, not a
requirement to use separate algorithms: a grouping method may also produce a
candidate hierarchy whose subject refinements require independent inspection.

## 1. Produce Grounded Subject Vectors

One note may express several subjects. It therefore may produce several source
masks and several SSE vectors instead of one whole-note vector.

For future runs, encode identical masks from the same original note only once,
retaining links to every subject record that produced that mask. Identity here
means the same source note and the same set of mask ranges, not similar wording
or overlapping meaning. The real-note adapter supports this with
`deduplicate_identical_masks: true` on each new input note. A vector's
`reviewed_subjects` retains every contributing subject record and its identity.
Absent that setting, historical per-subject encoding remains unchanged so frozen
experiment inputs, results, and reviews can still be replayed exactly.

Every vector instance must retain:

- a stable vector ID;
- its source `NoteId`;
- the exact selected source fragments;
- its SSE vector; and
- its prominence to the complete note.

The intended downstream unit is a source-grounded subject. The frozen
[ASv6.23 prompt](../../../sse_multivector/subject-prompt-goal-v1/asv6.23/ASv6.23.md)
states: "Subjects may overlap, nest, or describe the same material at broad and
narrow levels." The existing name "atomic subject" does not require every
subject to be maximally narrow. Complete uniqueness is not required: related
masks may produce related or partially redundant vectors.
The requirement is that materially different subjects remain distinguishable
enough for the later segmentation stage.

### Current implementation

The current real-note experiment uses:

```text
note
  -> ASv6.23 subjects
  -> MPv3.5 exact source masks
  -> reviewed subjects and masks
  -> SSE vectors
```

The generated subject is an intermediate instruction for mask selection; SSE
receives the complete note and selected token positions, not the subject
text. The selected contextual token representations are averaged and passed
through SSE's learned output transformation.

Both prompt packages are frozen for this experiment. This does not establish
production-wide extraction quality. The older takeaway/prominence orchestration
remains implemented, but is not the preparation path used for the saved HDBv2
experiment. A future trained extractor may replace subject and mask generation
if the transformation is demonstrated and enough supervision can be created.

## 2. Discover Subject Groups

The grouping algorithm receives the frozen SSE vectors and returns candidate
groups of related source masks. Groups may represent subjects at different
breadths. Neither the input prompt nor the grouping requirement fixes them to
one finest level.

The vector-space requirements are recorded in
[`../research/fine-segmentation-vector-space-requirements.md`](../research/fine-segmentation-vector-space-requirements.md).
They deliberately do not require the result to be:

- exhaustive;
- hard rather than weighted;
- non-overlapping; or
- one membership per vector.

Those are unresolved output-contract choices. A candidate method must expose
its actual memberships and unassigned vectors rather than silently changing
them to fit a preferred architecture.

The current grouping experiments establish memberships without generating
English labels. HDBv2 and HDBv3 also return nested hierarchies. Their
connectivity-based parent relations are candidate structure to inspect, not
automatically valid broader-subject relations.

## 3. Label Subject Groups from Grounded Evidence

Every member vector retains exact source fragments. A subject group can
therefore be described from the source evidence that formed it instead of
attempting to decode an opaque vector directly.

The approved labeling contract interprets these observed instances collectively.
Their grouping by contextual SSE similarity is evidence of related meaning,
not proof that every member fits any proposed title. Other instances can support
a more specific interpretation where one mask leaves meaning unspecified. A
generic mask does not require the title to encompass every possible meaning of
that mask in isolation. Explicitly incompatible meaning still constrains the
description; mere compatibility does not establish an otherwise unsupported
qualification.

This replaces the independent-per-instance proof standard used in earlier
title reviews. Existing raw outputs and recorded judgments remain experimental
evidence, not current verdicts under the revised contract. In particular, the
v3/v4/v6 weather, art and literature assessments require consistent
reconsideration; this decision does not automatically reverse them all.
Category subsumption retains its ordinary broad-to-narrow meaning. Interpreting
an observed mask within a group does not redefine the category named by that
mask, alter group membership, or validate downstream placement by itself.

The frozen v1 title prompt receives one numbered instance per vector:

```text
Instances:

1. “{fragment}”; “{fragment}”
2. “{fragment}”

What is the most precise and concise title for the semantic similarity among these instances?
```

Multiple fragments belonging to one vector remain one instance. The prompt is
stored in
[`../../../sse_multivector/fine-region-title-prompt-versions.json`](../../../sse_multivector/fine-region-title-prompt-versions.json).

The same registry also preserves **v2**, an approved candidate tested on the
same three HDBv2 nodes with one fresh isolated Sol low call per node.
It changes only “the semantic similarity among these instances” to
“the subject matter shared by these instances.” The input format is unchanged.
It aims to make titles name the shared subject rather than the text's
presentation, addressing the user-confirmed “Keywords” description error.
v1 remains the frozen baseline, and its
[three-node HDBv2 probe](../../../sse_multivector/hdbv2-node-description-probe-v1/README.md)
and raw results remain unchanged. The
[v1/v2 comparison](../../../sse_multivector/hdbv2-node-description-probe-v2/README.md)
records every input mask and exact output: v2 dropped “Keywords” from the art
title but added a user-confirmed unsupported “Home” restriction to the coffee title. The
consumption title still raises an unresolved scope question. One trial per
node does not isolate wording effects from sampling variation; v2 has not
been selected as the replacement.

The registry also preserves approved **v3**, which adds only: “The title's full
meaning, including any qualifying details, must be supported by every instance.”
A [fresh six-node v2/v3 comparison](../../../sse_multivector/hdbv2-node-description-probe-v3/README.md)
found more useful v3 descriptions, especially for art, while retaining specific
sea-salt and coffee-preparation meanings. Some dietary and kindness wording
remains interpretive. V2 also dropped its earlier Home restriction on repeat,
so not all improvements can be attributed to v3. These are provisional assistant
assessments, not new user verdicts or a representative accuracy estimate. V3 is
tested but not frozen; all earlier prompts and results remain unchanged.

A [six-additional-node v3 test](../../../sse_multivector/hdbv2-node-description-probe-v3-additional-v1/README.md)
kept the prompt unchanged. Outputs included appropriate shared descriptions
such as Weekend Well-Wishes, Literature and Family. The assistant flagged
Fall’s Arrival because two masks describe frost and sunrise without establishing
the season. This remains a review judgment, not a user-confirmed error or a
grouping verdict. The same-corpus test does not establish general reliability;
v3 remains unfrozen.

The [v4 contrastive-example test and title review](../../../sse_multivector/hdbv2-node-description-probe-v4/README.md)
prepend one unrelated jewelry-polishing example to the otherwise unchanged v3
prompt. Fresh v3/v4 calls on six existing nodes both retain the fall restriction
in the weather case; this example did not demonstrate a fix. Other selected
controls remain broadly defensible under assistant assessment. The dedicated
`sse-mask-review review-titles` mode presents an exact v4 title, every member
mask, and the assistant's assessment, with v3 comparison available on demand.
The current launcher surfaces only uncertain assistant judgments: one sea-salt
title. Its saved UI decision is Approved; the user later clarified in chat that
the description should include the food context shared by every mask. That is
a title omission, not merely a naming preference. The original explanation
appears in a separate **My comment** section,
alongside the masks and brief assessment; C edits the user's own comment.
Supplementary assistant comments do not change the original review inputs or
reset saved decisions. Confident assistant
judgments and all original results remain saved separately, never copied into
user decisions. The original six-card review session is preserved; the focused
review has a separate session. The frozen selector remains v1; v4 is not a
selected replacement.

Preserved candidate **v5** adds one contrast to v4's existing unrelated example: Jewelry
is too broad because both instances describe polishing. The prior explanation
rejecting an unsupported gold restriction remains. The aim is to retain shared
subject-defining context as well as avoid unsupported qualifications. This
revision was prepared but not tested or frozen. The user instead requested an
example-free task definition before adding examples; earlier prompts, results,
and recorded decisions are unchanged.

The [v6 example-free comparison](../../../sse_multivector/hdbv2-node-description-probe-v4/README.md#v6--example-free-comparison)
tested explicit shared-meaning preservation against fresh v3 calls on the same
six groups. V6 retained food context and coffee preparation and returned Frosty
fall mornings for the weather group. Fresh v3 also retained food context. Under
the prior standard, four v6 outputs received assistant acceptance, one rejection,
and one uncertain, lean-reject art-scope judgment; these are not user decisions. The
existing TUI surfaces only that uncertain judgment with every mask and a
separate explanation. Twelve clean-context Sol low calls and all raw outputs
are preserved. This selected comparison does not establish reliability or a
winning prompt; v6 remains unfrozen and v1 remains the frozen selector.

Candidate **v7** implements the revised collective-context contract in the same
registry. It supplies the grouping provenance, permits a more specific
interpretation supported by the group, and requires consistency with each
instance's explicit meaning. It retains shared relationships, generalization
and meaning-before-brevity instructions without examples. The candidate is
prepared for prompt review, not tested or frozen. Exact instance serialization,
v1–v6 prompts, generated data, review decisions, and model/runner settings are
unchanged. The extent to which the prompt reliably makes this distinction
remains unproven.

Candidate **v8** preserves the reviewed revision of v7: it shortens the
grouping explanation and clarifies using group evidence without contradicting
explicit meaning. Its numbered, per-vector input format is unchanged.

Candidate **v9** is a separate flat-input alternative. It receives one collection
of individually quoted exact fragments, one per line, without numbered instances
or note/mask boundaries. Its prompt interprets that collection collectively
rather than first reconstructing each instance. The registry specifies both the
prompt and this different input format. Existing instance order, source order
within each mask, and duplicate occurrences are retained; source note/vector/mask
associations remain saved internally but are not presented to the title model.

V8 remains untested. Before testing v9, the user removed its instruction to
generalize differing details; the earlier proposal remains in Git history.
The [six-group v9 trial](../../../sse_multivector/hdbv2-node-description-probe-v4/README.md#v9--flat-fragment-trial)
preserves all exact inputs and outputs. Main review accepts the collective
weather and audiobook descriptions, rejects an unsupported Home qualifier and
a food-list title, and leaves Instagram scope and Sunday emphasis uncertain.
These are assistant assessments, not user decisions. The existing review tool
surfaces those two uncertainties with flat fragments and separate comments.

Candidate **v10** saves the subsequently approved trimmed grouped-mask prompt.
It names the subject expressed collectively, interprets quoted text within each
instance together, uses group context without contradicting explicit meaning,
and preserves shared context and relationships. It removes the provenance
explanation and puts concision in the opening instruction rather than requiring
the final wording not to broaden an intermediate interpretation.

The [six-group v10 trial](../../../sse_multivector/hdbv2-node-description-probe-v4/README.md#v10--grouped-subject-title-trial)
used six fresh isolated Sol low calls on the same 25 masks. Main and independent
reviewers accept all six under the collective-context contract. The coffee title
no longer adds Home, and the food title describes food associated with sea salt
instead of listing items. Art redundancy and awkward audiobook wording remain
stylistic imperfections. These are assistant judgments, not user decisions; the
complete sampler is available in the existing review tool without requiring a
new user review for that first sample.

The [additional six-group v10 trial](../../../sse_multivector/hdbv2-node-description-probe-v4/README.md#v10--additional-sample-1)
kept the prompt unchanged and used previously unused complete groups: 35 masks
from 15 notes. Main review accepts four titles and leaves two scope questions
uncertain: whether a rave event justifies Rave Music and whether wine/food
associations justify Food Pairings. Neither is a proven contradiction. An
independent reviewer accepts the rave title, shares the wine uncertainty, and
questions synthesis in the time-related advice title, which main review treats
as a wording weakness. These disagreements are preserved, not assigned as user
decisions. The focused review shows only main review's two uncertainties with
all masks and separate reasoning. No exact masks were reused from prior title
probes, but the notes come from the same food-centered corpus. The user subsequently
rejected the wine title because food association does not necessarily establish
pairing; the rave-title scope remains undecided.

Candidate **v11** removes only V10's explicit instruction to clarify one instance
using group evidence. The [six-group paired trial](../../../sse_multivector/hdbv2-node-description-probe-v4/README.md#v11--remove-cross-instance-clarification)
preserves 27 masks and twelve fresh isolated Sol-low calls. Both prompts return
Visual Art and Photography and repeat the rejected Wine and Food Pairings.
Fresh V10 also avoids the previous rave-specific wording. Main and independent
reviewers accept the coffee-preparation and weekend-wishes meanings, but leave
V11's Events and Flavor Variations additions uncertain. The focused TUI preserves
those scope questions with masks, paired outputs and separate reasoning. The
deletion has no demonstrated advantage in this small development sample; no
new general rule, winning prompt or automatic user decision is established.

V1 remains the frozen selector. V8–v11 are not selected replacements;
the runner, grouping, original masks and earlier review artifacts are unchanged.
One v9 response per group, without fresh v8 controls, cannot isolate flattening
from prompt wording or sampling variation. V10 also has one response per group,
and v9 was not rerun alongside it. These selected development results do not
establish general reliability or isolate the effect of restoring mask bundles
from the changed wording. V11's paired controls hold inputs and execution settings
fixed, but one output per variant/group still does not establish a reliable causal
effect of deleting the sentence.

A title describes an already formed group. It must not change
membership or broaden an incoherent group until it sounds plausible. Prompt
quality remains open work; the current hierarchy comparison is deliberately unnamed.

## 4. Organize Groups into a Broad-to-Narrow Hierarchy

The hierarchy must organize subjects of different breadths into meaningful
narrowing paths. Discovered groups are not presumed to be indivisible leaves.
Whether the grouping method's own hierarchy supplies useful paths, or a
separate construction method is needed, remains under investigation.

Every visible child must be a meaningful refinement of its parent and of the
complete path above it. Independent labels that happen to be nearby are not a
hierarchy.

The current literature review is
[`../research/hierarchical-grouping-of-fine-semantic-segments.md`](../research/hierarchical-grouping-of-fine-semantic-segments.md).
It identifies candidates and risks; it does not freeze an algorithm. The
number of roots, depth, branching, parent-membership policy, and condensation
for navigation remain open.

The current note-navigation comparison preserves complete memberships from the
saved merge tree. One-note groups are not offered as choices, but their masks
remain at the nearest retained ancestor. When a child returns exactly the same
notes as its parent, the parent is retained and the child's remaining descendants
are promoted without reassigning semantic memberships. This preserves narrower
note sets that HDBSCAN condensation may not expose as separate nodes. It does
not validate those sets semantically or impose a branching limit.

An optional [five-note view of saved M06](../../../sse_multivector/merge-rule-exploration-v1/inspection.md#optional-five-note-view-of-m06)
tests stopping navigation earlier. `--min-notes 5` hides smaller group choices,
keeping their masks at the nearest displayed ancestor. The saved merges and
every retained group's complete membership stay unchanged; the default remains
two notes. Five is a provisional display minimum, not a merge constraint or a
selected production requirement.

Hierarchy labels must be generated from the grounded evidence beneath each
node. They describe membership; they do not define it.

## 5. Resolve a Selected Subject to Notes

When navigation reaches a selected terminal subject:

1. collect the vector memberships for that subject;
2. resolve each vector to its source `NoteId`;
3. deduplicate repeated `NoteId` values inside that result; and
4. order the notes using the vector-to-note prominence values.

One note may appear in several subjects because it may contribute several
subject vectors. That is expected.

Prominence affects note ordering inside a subject result. It does not create
subject membership or hierarchy edges.

## Load-Bearing Questions

### Subject extraction and SSE

- Do the selected masks represent the atomic subjects needed by the system?
- Do differently worded instances of the same subject remain nearby?
- Do materially different subjects remain distinguishable despite shared words
  and unselected context?

### Subject grouping

- Can each frozen candidate recover repeated subjects?
- Can each resolve nearby but meaningfully distinct subjects?
- Does each follow semantic relationships rather than lexical coincidence?
- Does unselected context avoid determining a candidate's memberships?
- How does each behave under unequal support, duplicates, unrelated additions,
  and input reordering?
- What differences in their complete evidence matter to the user's final
  choice?

### Hierarchy and navigation

- Can discovered groups at different breadths support meaningful narrowing
  paths?
- Does every visible choice narrow the complete path predictably?
- Do labels accurately predict the notes that selection reveals?
- Can the UI expose a small, usable set of choices without changing the
  scientific hierarchy?

## Current Evidence

The controlled SSE evidence is indexed in
[`../../notes/SSE-EXPERIMENTS.md`](../../notes/SSE-EXPERIMENTS.md). It supports some
single- and multi-fragment subject relationships, but it also records failures,
including relationship reversal and mixed real-note transfer. It does not
validate corpus-wide subject grouping.

Earlier complete-linkage and SCC pilots demonstrated mechanics and exposed bad
groupings. They did not validate a global hard partition and are not the
current grouping specification. The later real-note experiment and HDBv2
hierarchy inspection are linked above; they preserve earlier results rather
than retroactively changing their protocols or declaring a final algorithm.

## Evidence Boundaries

Each experiment must identify and freeze its actual inputs and configuration.
Review source masks before using the resulting groups as semantic evidence.
Keep group-coherence judgments separate from judgments about parent placement,
labels, and complete navigation paths.

A candidate hierarchy may be inspected while grouping remains experimental;
inspection is not final algorithm selection. Useful groups need not first be
declared maximally fine. Preserve complete memberships, parent-only masks, and
ungrouped material when assessing what the hierarchy does and does not offer.
The user selects the final algorithm and navigation direction; the assistant's
research or proposed selection is not approval.

## Open Decisions

- the final direct subject-mask extractor;
- the final subject-group membership contract;
- the final grouping algorithm and configuration after controlled
  qualification;
- the hierarchy algorithm and configuration;
- tree versus overlapping parent paths;
- hierarchy condensation and visible branching;
- subject-label generation at each breadth;
- corpus scale and update policy; and
- final navigation evaluation.
