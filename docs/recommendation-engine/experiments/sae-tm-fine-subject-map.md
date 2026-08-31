# Isolated Fine-Subject Map Experiment

## Status

Proposed experiment. It is not an approved product architecture and has no
result yet.

## Question

> Do learned semantic directions repeatedly represent recognizable subjects,
> and do mixed notes activate several appropriate directions?

This is the prerequisite for building a corpus-induced subject hierarchy. If
this relation does not work, labels, hierarchy, and navigation cannot repair
it.

## Hypothesis

A Nostr note embedding can be represented as a sparse, nonnegative combination
of semantic directions learned from the Nostr corpus:

```text
note_vector ~= activation_1 * direction_1
             + activation_2 * direction_2
             + ...
```

Each learned direction is initially an unnamed **fine-subject candidate**.
Each positive activation is evidence that the note belongs to that candidate.

This produces one sparse relation with two views:

```text
NoteId    -> {SubjectCandidateId -> weight}
SubjectCandidateId -> {NoteId -> weight}
```

The second view is derived from the first. It is not learned separately.

## Method

### 1. Freeze the inputs

Use a frozen set of real Nostr notes and one frozen whole-note semantic
representation. Split learning and held-out notes before fitting the model.
The split must prevent the same author or a high-confidence textual copy from
crossing the boundary.

The existing 51,200-note Granite-R2 representation is a credible input because
[SAE-TM](https://arxiv.org/abs/2511.16309) also evaluated Granite-R2. Reusing it
is permitted only after confirming that its exact preprocessing and provenance
fit this experiment; this experiment must not be distorted merely to reuse an
artifact.

### 2. Learn sparse semantic directions

Fit the official corpus-specific **L1 SAE-TM** method on only the learning-note
vectors.

The sparse autoencoder learns:

- one decoder vector for every semantic direction;
- a small set of positive activations for every note;
- a reconstruction residual for meaning not explained by those directions.

The directions are learned from recurring structure in the Nostr corpus. They
are not predefined subjects and are not created from private ratings.

### 3. Materialize the relation

For every positive activation `a(note, candidate)`, retain:

- the raw activation;
- the normalized within-note weight;
- the candidate's decoder vector;
- the note's reconstruction error.

The normalized weight is:

```text
w(note, candidate) =
    a(note, candidate) / sum(a(note, every active candidate))
```

The raw activation and normalized weight must both remain available. Neither
is a calibrated probability, a percentage of the note's text, or proof of how
important that subject is to a reader.

Dead directions are not subjects. Rare, universal, duplicated, stylistic,
incoherent, and otherwise suspicious directions must be reported rather than
silently hidden.

## Human Verification

The model's directions are unnamed. They are inspected through original notes,
not through persuasive generated labels.

The frozen evaluation must test both parts of the question:

1. **Repeated meaning**
   - Select subject candidates without curating attractive examples.
   - Show several held-out notes with strong activation for each candidate.
   - Determine whether the same recognizable subject is genuinely present
     across those notes.

2. **Mixed-note decomposition**
   - Select held-out notes with several strong activations without inspecting
     their content first.
   - For each activation, show independent representative notes for that
     candidate.
   - Determine whether the activated candidates correspond to distinct
     subjects actually present in the mixed note, rather than one blended
     subject or irrelevant properties.

The case-selection rules, sample sizes, questions, and pass criteria must be
frozen before any formal cases are inspected.

## What Success Means

Success requires evidence that:

- a useful share of learned directions correspond to coherent, recognizable
  subjects across multiple notes;
- held-out notes activate appropriate directions;
- mixed notes can activate multiple appropriate directions;
- the relation is not dominated by language, formatting, author identity,
  sentiment, or generic writing style.

Success would justify the next separate experiment: organizing accepted
fine-subject vectors into a broad-to-narrow hierarchy.

It would not establish that the hierarchy, labels, navigation interface, or
recommendations are good.

## What Failure Means

The hypothesis fails if the learned directions are mostly incoherent,
non-subject properties, overly generic, or blended, or if their activations do
not reliably describe held-out notes.

A specific failure on mixed notes would motivate one challenger:
contextual-span subject discovery, where grounded portions of a note are
represented and clustered separately. It should not be added before the
whole-note sparse decomposition has been tested.

## Excluded

This experiment does not include:

- FASTopic;
- recursive clustering;
- predefined subjects;
- subject labels;
- subject merging or hierarchy construction;
- a navigation interface;
- an LLM pass over every note;
- private ratings or personalization;
- recommendation evaluation.

The previous BatchTopK pilot did not test the official corpus-specific L1
SAE-TM method and is not evidence for or against this hypothesis.
