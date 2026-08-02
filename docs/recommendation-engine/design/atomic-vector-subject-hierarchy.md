# Atomic-Vector Subject Hierarchy

## Status

This is the current architecture hypothesis for the next content-discovery
direction. It is not yet validated.

The immediate work is to verify its assumptions in order. Technology choices,
scale, hierarchy shape, and evaluation details remain open until the
corresponding assumption is understood.

This direction supersedes the earlier whole-note topic-map and hierarchy
proposals as the planned path forward. Their artifacts remain historical
evidence; this document does not reinterpret their results.

## Goal

Build a public, corpus-derived subject hierarchy that lets a person repeatedly
narrow what they want to explore and then inspect notes from the selected
fine subject.

The hierarchy must emerge from the public note corpus. It must not begin with a
predefined ontology or infer what the person currently wants.

## Separation of Concerns

The architecture has four separate transformations:

```text
note
  -> atomic semantic vectors
  -> hard fine-subject regions
  -> recursively grouped subject hierarchy
  -> notes presented by the UI
```

Failure at one transformation must remain visible. A later transformation must
not manufacture structure to conceal an earlier failure.

## 1. Represent Each Note with Multiple Atomic Vectors

One note may discuss several independent ideas. The representation therefore
produces several semantic vectors rather than pooling the complete note into
one vector.

Each vector instance retains:

- the source `NoteId`;
- the exact source-token region that supports it;
- its semantic vector;
- an importance-to-note value only if the representation naturally and
  reliably provides one.

The intended meaning of one vector is one sufficiently atomic idea expressed
by the note.

For example:

```text
I love writing Rust code while sipping a martini on the beach.
```

could produce separate vectors grounded in:

```text
writing Rust code
sipping a martini
on the beach
```

The current 32-case counterfactual pilot found no valid observed blending
failure and supports continuing to the next assumption. This is small-pilot
evidence, not a claim that the decomposition is universally correct. The
preserved interpretation is in
[`scientific-interpretation.md`](../../../sse_multivector/context-counterfactual-result-v1/scientific-interpretation.md).

## 2. Hard-Partition Atomic Vectors into Fine Subjects

All atomic vector instances from the corpus are partitioned into fine semantic
regions:

```text
AtomicVectorId -> FineSubjectId
```

This is a hard partition:

- every atomic vector belongs to exactly one fine-subject region;
- fine-subject regions do not overlap;
- notes are not being partitioned.

A note can still belong to several fine subjects because it can contribute
several atomic vectors:

```text
NoteId -> {FineSubjectId}
```

The representation supplies the separate ideas. The partition aligns
equivalent ideas expressed across different notes.

## 3. Give Every Fine Region a Grounded English Label

Every vector retains the exact token region that produced it. A fine region can
therefore be described using the English evidence attached to its member
vectors rather than by attempting to decode an opaque vector directly.

For one fine region, a scoped language-model operation receives grounded source
evidence from that region. The complete frozen input format is:

```text
Instances:

1. “{fragment}”; “{fragment}”
2. “{fragment}”

What is the most precise and concise title for the semantic similarity among these instances?
```

Each vector is one numbered instance. Every exact source fragment is enclosed
in curly double quotes. Multiple fragments from one vector remain in source
order and are joined with `; `. Instances are joined with one newline. The
blank lines shown above are part of the prompt.

The exact text is also preserved in
[`fine-region-title-prompt-versions.json`](../../../sse_multivector/fine-region-title-prompt-versions.json).

For example, a region grounded in spans such as:

```text
writing Rust code
fixing borrow-checker errors
Cargo workspace configuration
rust-analyzer completion
```

might receive the label:

```text
Rust development and tooling
```

The title does not define, validate, reject, or change the region. It only maps
a region already established from corpus vectors into human language.

The conceptual evidence is the set of source spans attached to the region's
member vectors. How large regions are batched or sampled without producing a
misleading label is unresolved.

## 4. Build the Hierarchy Bottom-Up

The fine-subject regions become the leaves of the hierarchy.

A separate partitioning process groups related leaf subjects. For each proposed
group, a scoped language-model operation receives the children's grounded
English representations and must either:

- name the narrowest recognizable subject for which every child is a valid
  refinement; or
- reject the group as incoherent.

For example:

```text
Rust development
Python development
C++ development
```

could become children of:

```text
Programming languages
```

The accepted parent retains its child regions and their underlying evidence.
Its generated label never replaces that evidence.

The same operation repeats over the newly created parent regions until the
complete broad-to-narrow hierarchy exists.

Under the current hypothesis, every subject node belongs to exactly one parent
group at the next level. The result is therefore a tree. No DAG or overlapping
parent structure is currently required.

The number of roots, maximum children per node, and stopping rules are not yet
decided.

## 5. Resolve Leaf Vectors Back to Notes

The hierarchy organizes atomic vectors, not notes.

When the UI reaches a leaf:

1. read the vector instances assigned to that leaf;
2. resolve their source `NoteId` values;
3. deduplicate repeated `NoteId` values within that leaf;
4. present the resulting notes.

The membership rule is binary:

```text
if at least one vector from a note belongs to the leaf,
the note belongs to that leaf
```

Because one note can produce several vectors, the same note may legitimately
appear in several different leaves.

An importance-to-note value could later improve ordering within a leaf. It is
not required to establish membership or validate the architecture.

## Load-Bearing Assumptions

### A. Atomic decomposition

The multi-vector representation must:

- preserve the material ideas expressed by a note;
- separate those ideas into sufficiently atomic vectors;
- avoid routinely blending unrelated ideas into one vector;
- retain reliable source-token grounding.

### B. Fine-region recovery

The corpus geometry must permit a useful hard partition in which:

- equivalent atomic ideas expressed with different wording share a region;
- unrelated ideas remain separate;
- rare ideas are not silently discarded or forced into an incorrect region.

The first 194-vector pilot found several coherent recurring regions but also
persistent false merges and obvious splits. It did not validate one global
hard partition. DP-vMF also failed as the authoritative scalable method due to
broad, order-sensitive merging. The result is preserved in
[`sse-fine-region-partition-pilot.md`](../experiments/sse-fine-region-partition-pilot.md).

### C. Fine-region labeling

Grounded source evidence must be sufficient to produce a concise label that
accurately predicts the region's members. Region membership remains the
partitioner's responsibility; the labeler must not conceal a partitioning
failure by changing membership or inventing a broader region.

### D. Hierarchy construction

Repeated partitioning must produce groups with precise common parents. Every
selection must meaningfully narrow the content beneath its parent instead of
creating vague concatenations of neighboring subjects.

### E. Leaf presentation

Resolving any matching vector back to its note must produce a useful set of
notes for the selected fine subject. Importance weighting and final ordering
can be evaluated separately.

## Verification Order

Verify the assumptions in dependency order:

1. `note -> atomic semantic vectors`;
2. `atomic vectors -> coherent hard fine-subject regions`;
3. `fine region -> faithful grounded label`;
4. `fine subjects -> useful recursive hierarchy`;
5. `leaf vectors -> useful note set`.

Step 1 has small-pilot support. Step 2 remains unresolved. The next test must
determine whether sparse subject coverage caused the observed false merges and
splits before any label or hierarchy work begins.

Do not build a later stage merely to make an unverified earlier stage appear
successful.

## Not Currently Required

- personalization or recommendation;
- private user behavior;
- a predefined subject ontology;
- one whole-note embedding as the subject map;
- overlapping fine-subject regions;
- a DAG;
- importance-to-note weights;
- a fixed topic count;
- a fixed hierarchy depth;
- a fixed branching factor;
- final note-ranking policy.
