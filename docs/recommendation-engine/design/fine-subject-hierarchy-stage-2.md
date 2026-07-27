# Stage 2 Fine-Subject Hierarchy Proposal

## Status

Draft for review. This is a concrete candidate for the Stage 2 experiment. It
is not an approved architecture and has not been tested.

## Purpose

Stage 2 asks:

> Can corpus-learned fine subjects be organized into a useful broad-to-narrow
> hierarchy with a small number of choices at every level?

The intended interface begins with broad subjects. Selecting one reveals
narrower subjects. This continues until the selected subject contains few
enough notes to inspect directly.

## Fixed Separation of Concerns

Stage 1 owns fine-subject discovery:

```text
NoteId -> {FineSubjectId -> weight}
```

Stage 2 owns only hierarchy construction:

```text
FineSubjectId -> hierarchy path
```

Stage 2 must not:

- discover replacement fine subjects;
- change Stage 1's note-to-fine-subject weights;
- classify every corpus note with an LLM;
- infer new private preferences;
- hide a Stage 1 failure by inventing hierarchy structure.

If Stage 1 misses a meaning, that remains a Stage 1 limitation.

## Inputs

For every accepted fine subject:

- its stable `FineSubjectId`;
- its decoder vector from Stage 1;
- its strongest activating notes;
- nearby notes that do not activate it;
- `w(note, fine_subject)`;
- its total membership mass:

```text
mass(fine_subject) = sum(w(note, fine_subject))
```

The number of accepted fine subjects is unknown. The current 3,072-feature
experiment configuration is not an estimate of the correct number of subjects
for Nostr.

## Output

A precomputed tree containing:

- a short label and definition for every displayed node;
- between two and eight children for every nonterminal node;
- exactly one child route for every fine subject at each level;
- the descendant fine-subject IDs under every node;
- the note membership derived from the frozen Stage 1 relation;
- explicit build failures where a valid split could not be produced.

One fine subject follows one hierarchy path. A note may still appear under
multiple branches because Stage 1 may assign that note to several fine
subjects.

## Proposed Proof-Oriented Construction

### 1. Describe one fine subject

Create an evidence card from:

- eight of the strongest activating notes, with at most one per author;
- four semantically nearby notes with zero activation for that fine subject.

One scoped LLM call receives only that evidence card. It returns:

```text
label
one-sentence inclusion definition
```

It may instead return `ABSTAIN` when the activating notes do not express one
coherent subject. An abstaining subject cannot enter Stage 2.

The original note IDs and texts remain attached to the generated description
for later inspection. The generated description is not treated as proof that
the fine subject is coherent.

### 2. Propose children for one hierarchy node

A hierarchy node contains:

```text
parent definition
set of FineSubjectIds
```

Select at most 64 fine subjects from the node by farthest-first traversal over
their normalized decoder vectors. This panel is intended to expose different
parts of the node; it does not assign hierarchy membership.

One LLM call receives:

- the parent definition;
- the selected fine-subject labels and definitions.

It returns between two and eight proposed children. Every child contains:

```text
label
one-sentence inclusion definition
supporting FineSubjectIds from the panel
```

`Other`, `Miscellaneous`, and equivalent residual categories are forbidden.

### 3. Route every fine subject in that node

Process the node's fine-subject cards in batches of at most 16. Each routing
call receives:

- the parent definition;
- the proposed child definitions;
- the fine-subject cards in that batch.

For every fine subject, it returns exactly one child ID or `NONE`.

The routing question is:

> Which one child is the narrowest valid broader subject for this fine
> subject?

The router does not see corpus notes other than the representative evidence
already contained in those fine-subject cards.

### 4. Apply mechanical checks

Reject the proposed split if:

- any fine subject receives `NONE`;
- any child receives no fine subjects;
- any child contains the node's complete fine-subject set;
- two children contain identical fine-subject sets;
- fewer than two or more than eight children are returned.

These checks are deterministic. They do not establish that the semantic
assignments are correct.

### 5. Repair only the failed node

If a split is rejected:

1. Select at most 32 unresolved fine subjects.
2. Add representative fine subjects from the proposed children while keeping
   the complete repair panel at or below 64 cards.
3. Give the failed child definitions and repair panel to the generator.
4. Require a replacement set of two to eight children.
5. Route every fine subject in the node again from scratch.

After three unsuccessful repair rounds, record the node as `UNBUILDABLE`.
Do not publish a partial split or create a residual child.

### 6. Recurse or stop

For each accepted child:

- derive its set of fine subjects;
- derive its eligible notes from Stage 1 weights;
- recurse when its note count exceeds the frozen terminal-note quota;
- otherwise store it as a terminal node.

There is no fixed hierarchy depth.

If a node contains only one fine subject but still exceeds the terminal-note
quota, record `FINE_SUBJECT_TOO_BROAD`. Stage 2 cannot recover detail that
Stage 1 did not produce.

## Deriving Note Membership

Stage 2 never sends ordinary corpus notes through a new classifier.

For hierarchy node `h`, let `F(h)` be its distinct descendant fine subjects:

```text
W(note, h) = sum(w(note, f) for f in F(h))
```

The same frozen Stage 1 relation therefore supports:

```text
NoteId -> {HierarchySubjectId -> weight}
HierarchySubjectId -> {NoteId -> weight}
```

## Exact LLM Scope

The proposed proof-oriented procedure gives the LLM only:

- twelve notes while describing one fine subject;
- at most 64 compact fine-subject descriptions while proposing one split;
- at most 16 compact fine-subject cards while routing against no more than
  eight children.

It never receives:

- the complete note corpus;
- all fine subjects in one prompt;
- the complete hierarchy in one prompt.

## Computational Shape

Let:

- `S` be the number of accepted fine subjects;
- `D` be their average hierarchy depth.

The proof-oriented proposal requires approximately:

```text
fine-subject description work: 12 * S note appearances
fine-subject routing work:      S * D routing decisions
```

This is linear in the number of fine subjects, not the number of corpus notes.
It is suitable only if the resulting LLM cost is acceptable for the
experiment.

No assumption is made that `S = 3,072`. Before a complete run, token usage and
cost must be measured on a bounded sample and projected using the observed
card sizes, routing depth, and repair rate.

## Possible Scaling Path

This is not part of the proof-oriented experiment.

If direct LLM routing becomes too expensive:

1. Ask the LLM to propose children and route only a small diverse seed set.
2. Build one prototype vector for each child from those routed fine-subject
   vectors.
3. Route the remaining fine subjects through vector comparison.
4. Send only low-margin and far-from-every-prototype cases to the LLM.
5. Recalculate the prototypes after those decisions.

This would keep the same Stage 1/Stage 2 boundary. It must not be added before
the direct procedure establishes that the semantic operation works.

## Unresolved Decisions

- The actual number of accepted fine subjects.
- The LLM used for fine-subject descriptions.
- The LLM used for child generation and routing.
- Exact prompt schemas.
- The terminal-note quota.
- Whether eight positive and four contrasting notes are sufficient evidence.
- Whether a fine subject must have exactly one path or eventually needs
  explicit cross-links.
- The formal evaluation procedure and pass criteria.
- The measured token usage and monetary cost.
- Whether the proposed repair limit is sufficient.

## What Success Would Establish

Success would establish that accepted fine subjects can be converted into a
bounded, understandable navigation hierarchy without processing every corpus
note with an LLM.

It would not establish that:

- Stage 1 discovered every subject in the corpus;
- the correct number of fine subjects is known;
- the hierarchy scales economically to a much larger subject dictionary;
- the resulting navigation experience is useful;
- this is the final production architecture.
