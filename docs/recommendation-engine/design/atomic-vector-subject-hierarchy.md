# Atomic-Subject Content Hierarchy

## Status

This is the approved architectural direction for the content-discovery
experiment. It is not a validated system.

The current implementation has several provisional components. The exact
prompt boundary, fine-segmentation output contract, fine-segmentation
algorithm, hierarchy algorithm, and labels must still be tested and frozen in
dependency order.

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

Each stage must be evaluated on its own output. A later label or hierarchy must
not conceal a failure in extraction, SSE geometry, or fine segmentation.

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

- Can one frozen candidate recover repeated subjects?
- Can it resolve nearby but meaningfully distinct subjects?
- Does it follow semantic relationships rather than lexical coincidence?
- Does unselected context avoid determining membership?
- How does it behave under unequal support, duplicates, unrelated additions,
  and input reordering?

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

1. Fix and freeze the temporary TP, MP, and prominence boundary.
2. Freeze one fine-segmentation candidate and run the
   [`../experiments/fine-segmentation/README.md`](../experiments/fine-segmentation/README.md).
3. If the synthetic evidence supports proceeding, test the same candidate on
   hand-selected real notes from one niche subject area.
4. Only after useful fine subjects are demonstrated, compare and freeze a
   hierarchy method.
5. Construct labels and the hierarchy, then evaluate the navigation TUI.

## Open Decisions

- the final direct subject-mask extractor;
- the fine-segmentation membership contract;
- the selected fine-segmentation algorithm and configuration;
- the hierarchy algorithm and configuration;
- tree versus overlapping parent paths;
- hierarchy condensation and visible branching;
- fine and higher subject-label generation;
- corpus scale and update policy; and
- final navigation evaluation.
