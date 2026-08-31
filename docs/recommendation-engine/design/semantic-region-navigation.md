# User-Directed Subject Navigation

## Status

This document defines the intended user-facing behavior of the content
hierarchy. The backend that constructs the hierarchy remains experimental.

## Purpose

The system should not guess which subject the person wants right now.

A person may not be able to name the desired subject from an empty prompt, but
can choose among several concrete alternatives. Repeating that choice at
successively narrower levels lets the person state current intent without the
system attempting to infer it from private behavior.

For example:

```text
Technology
  -> Programming
     -> Rust
        -> Borrow-checker diagnostics
```

Each selection has meaning only within the complete path. A child is not an
independent label; it must predict a narrower subset of what the parent
offered.

## Interaction Contract

1. Show a small set of useful subject choices at the current node.
2. The person selects one choice.
3. Show that subject's meaningful refinements.
4. Repeat until the interface reaches a useful terminal subject.
5. Show the notes associated with that subject.

The interface may omit structural hierarchy levels that add no useful choice.
It must not show:

- a parent-to-child transition with the same note result;
- sibling choices with identical note results; or
- a label whose visible meaning does not predict the notes beneath it.

The exact maximum number of visible choices is not frozen.

## Note Membership

The hierarchy organizes subject-vector memberships. A note may contribute
several vectors and therefore appear in several final subject results.

Within one selected result:

- repeated occurrences of the same note are deduplicated;
- prominence scores may order notes by how strongly the complete note is about
  the matched subject; and
- the same note's membership in another subject is not removed.

## Separation from Recommendation

These actions have different meanings:

- Rating a note records how glad the person was to see that note at that time.
- Selecting a subject states what the person wants to explore now.
- Showing a note records exposure.

Oracle MVP v1 used positive note ratings to expand whole-note semantic
neighborhoods. That is existing frozen-v1 behavior, not the control mechanism
for this hierarchy.

The hierarchy may later coexist with a local recommender, but private ratings
must not define the public subject structure or silently select the person's
current path.

## Public and Private Boundary

Public computation may derive a versioned hierarchy and note memberships from
public Nostr notes.

Private local state may retain:

- the person's current navigation path;
- notes already shown locally;
- local ordering or filtering preferences; and
- private recommendation state belonging to a separate recommender.

The public hierarchy must not require that private state.

## Backend Dependency

The backend direction is documented in
[`atomic-vector-subject-hierarchy.md`](atomic-vector-subject-hierarchy.md).
The method-independent fine-segmentation boundary is documented in
[`../research/fine-segmentation-vector-space-requirements.md`](../research/fine-segmentation-vector-space-requirements.md).

Navigation work begins only after the earlier stages demonstrate useful fine
subjects and a usable hierarchy. The interface must evaluate the complete
root-to-note experience; attractive labels alone are not sufficient.

## Open Decisions

- the visible branching limit;
- how structural levels are condensed for navigation;
- how the root choices are presented;
- when a subject becomes a terminal note result;
- how note ordering uses prominence;
- how versions and corpus updates affect saved paths; and
- the complete navigation evaluation.
