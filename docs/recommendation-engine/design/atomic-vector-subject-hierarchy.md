# Atomic-Subject Content Hierarchy

## Status

This is the approved architectural direction for the content-discovery
experiment. It is not a validated system.

The current implementation has several provisional components. The exact
prompt boundary, final fine-segmentation output contract and algorithm,
hierarchy algorithm, and labels must still be tested and frozen in dependency
order. HDBSCAN* with `min_samples = 2`, `min_cluster_size = 2`, and
excess-of-mass selection and SNN with `neighbor_count = 5`,
`minimum_shared_neighbor_count = 2`, and `minimum_core_neighbor_count = 3` are
the two predeclared controlled-qualification configurations. Once their full
technical identities and the shared inputs are frozen, they will run the
complete suite as separate candidate instances. Neither is the final
fine-segmentation choice.

The suite's exact semantic fixtures, scoring rules, and prerequisite graph were
approved on 2026-08-31. Its controlled run completed on 2026-09-01. Both
candidates exceeded the frozen Experiment 2 limit of 100 unique cross-subject
packets, so neither may proceed and the user's `revise candidate` or `stop`
dispositions remain pending. See the
[controlled-run results](../experiments/fine-segmentation/controlled-run-v1-results.md).
A separately versioned exploratory v2 follow-up reviews the nine distinct
sorted sets of approved synthetic subjects represented by HDBSCAN*'s 177
retained exact packets. Each judgment replays to every matching exact packet
and formal occurrence, covering all 177 packets and 191 occurrences. This
methodological correction leaves the frozen capacity-failure result, HDBSCAN*
candidate and evidence, original 177-packet v1 review session, SNN record, and
final user selection unchanged. The review records only group coherence;
fine-subject naming remains downstream.

## Goal

Build a public, corpus-derived hierarchy that lets a person repeatedly narrow
the subject they want to explore and then inspect notes associated with the
selected fine subject.

The hierarchy does not infer current intent from ratings or behavior. The
person supplies current intent by choosing among the hierarchy's visible
refinements.

## Separation of Concerns

The system has distinct transformations:

```text
public note
  -> subject-bearing source masks
  -> one SSE vector per mask
  -> fine-subject memberships
  -> broad-to-narrow subject hierarchy
  -> note results for an explicitly selected subject
```

Each stage has an explicit output boundary. A later label or hierarchy must not
conceal a failure in extraction, SSE geometry, or fine segmentation. A test
that deliberately changes source text and re-encodes it before segmentation
qualifies the frozen SSE-plus-segmentation combination; it cannot assign the
result to either stage by itself.

## 1. Produce Grounded Subject Vectors

One note may express several subjects. It therefore may produce several source
masks and several SSE vectors instead of one whole-note vector.

Every vector instance must retain:

- a stable vector ID;
- its source `NoteId`;
- the exact selected source fragments;
- its SSE vector; and
- its prominence to the complete note.

The intended downstream unit is an atomic subject. Complete uniqueness is not
required: related masks may produce related or partially redundant vectors.
The requirement is that materially different subjects remain distinguishable
enough for the later segmentation stage.

### Current implementation

The current corpus-preparation path is:

```text
note
  -> TPv3.82 takeaways
  -> MPv3.4 exact source masks
  -> PPv2 prominence
  -> SSE vectors
```

The generated takeaway is an intermediate instruction for mask selection; SSE
receives the complete note and selected token positions, not the takeaway
text. The selected contextual token representations are averaged and passed
through SSE's learned output transformation.

This pipeline exists, but prompt repair remains current work. It has not yet
shown that its masks reliably correspond to the atomic subjects required by
the downstream hierarchy. A future trained extractor may replace the TP and MP
calls if the transformation is first demonstrated and enough supervision can
be created.

## 2. Recover Fine Subjects

The fine-segmentation algorithm receives the frozen SSE vectors and returns
groups intended to represent recurring fine subjects.

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

The fine-segmentation stage establishes membership only. It does not generate
English labels or higher hierarchy nodes.

## 3. Label Fine Subjects from Grounded Evidence

Every member vector retains exact source fragments. A fine subject can
therefore be described from the source evidence that formed it instead of
attempting to decode an opaque vector directly.

The current fine-subject title prompt receives one numbered instance per
vector:

```text
Instances:

1. “{fragment}”; “{fragment}”
2. “{fragment}”

What is the most precise and concise title for the semantic similarity among these instances?
```

Multiple fragments belonging to one vector remain one instance. The prompt is
stored in
[`../../../sse_multivector/fine-region-title-prompt-versions.json`](../../../sse_multivector/fine-region-title-prompt-versions.json).

A title describes an already formed fine subject. It must not change
membership or broaden an incoherent group until it sounds plausible. Prompt
quality remains open work after fine segmentation is validated.

## 4. Build the Hierarchy from Fine Subjects

Fine-subject nodes are the inputs to a separate hierarchy-construction stage.
That stage recursively groups narrower subjects into broader subjects.

Every visible child must be a meaningful refinement of its parent and of the
complete path above it. Independent labels that happen to be nearby are not a
hierarchy.

The current literature review is
[`../research/hierarchical-grouping-of-fine-semantic-segments.md`](../research/hierarchical-grouping-of-fine-semantic-segments.md).
It identifies candidates and risks; it does not freeze an algorithm. The
number of roots, depth, branching, parent-membership policy, and condensation
for navigation remain open.

Hierarchy labels must be generated from the grounded evidence beneath each
node. They describe membership; they do not define it.

## 5. Resolve a Selected Fine Subject to Notes

When navigation reaches a selected fine subject:

1. collect the vector memberships for that subject;
2. resolve each vector to its source `NoteId`;
3. deduplicate repeated `NoteId` values inside that result; and
4. order the notes using the vector-to-note prominence values.

One note may appear in several fine subjects because it may contribute several
subject vectors. That is expected.

Prominence affects note ordering inside a subject result. It does not create
fine-subject membership or hierarchy edges.

## Load-Bearing Questions

### Subject extraction and SSE

- Do the selected masks represent the atomic subjects needed by the system?
- Do differently worded instances of the same subject remain nearby?
- Do materially different subjects remain distinguishable despite shared words
  and unselected context?

### Fine segmentation

- Can each frozen candidate recover repeated subjects?
- Can each resolve nearby but meaningfully distinct subjects?
- Does each follow semantic relationships rather than lexical coincidence?
- Does unselected context avoid determining either candidate's memberships?
- How does each behave under unequal support, duplicates, unrelated additions,
  and input reordering?
- What differences in their complete evidence matter to the user's final
  choice?

### Hierarchy and navigation

- Can useful broad subjects be built from demonstrated fine subjects?
- Does every visible choice narrow the complete path predictably?
- Do labels accurately predict the notes that selection reveals?
- Can the UI expose a small, usable set of choices without changing the
  scientific hierarchy?

## Current Evidence

The controlled SSE evidence is indexed in
[`../../notes/SSE-EXPERIMENTS.md`](../../notes/SSE-EXPERIMENTS.md). It supports some
single- and multi-fragment subject relationships, but it also records failures,
including relationship reversal and mixed real-note transfer. It does not
validate corpus-wide fine segmentation.

Earlier complete-linkage and SCC pilots demonstrated mechanics and exposed bad
groupings. They did not validate a global hard partition and are not the
current fine-segmentation specification.

## Verification Order

1. Technically freeze the shared SSE inputs, bind the approved fixtures and
   scoring rules by hash, and freeze the orders and both complete candidate
   identities, then run the complete
   [`../experiments/fine-segmentation/README.md`](../experiments/fine-segmentation/README.md)
   separately for HDBSCAN* and SNN. Experiments 3 and 4 are integration evidence
   for each SSE-plus-candidate combination; the remaining experiment-specific
   claims retain the ownership defined by the suite. Semantic failures do not
   halt later local tests; integrity failures block only affected inputs and
   dependent conclusions.
2. Present both complete records side by side. The assistant may recommend an
   outcome; the user alone selects and final-freezes a candidate, requests a
   revision, or stops the approach.
3. If the user selects a candidate, test that exact identity on hand-selected
   real notes from one niche subject area.
4. Only after useful fine subjects are demonstrated, compare and freeze a
   hierarchy method.
5. Construct labels and the hierarchy, then evaluate the navigation TUI.

The temporary TP, MP, and prominence boundary remains separate upstream work.
It must be resolved before arbitrary notes can enter the complete architecture,
but it does not gate this suite because the synthetic atomic-subject masks are
hand-authored and frozen.

## Open Decisions

- the final direct subject-mask extractor;
- the final fine-segmentation membership contract;
- the final fine-segmentation algorithm and configuration after controlled
  qualification;
- the hierarchy algorithm and configuration;
- tree versus overlapping parent paths;
- hierarchy condensation and visible branching;
- fine and higher subject-label generation;
- corpus scale and update policy; and
- final navigation evaluation.
