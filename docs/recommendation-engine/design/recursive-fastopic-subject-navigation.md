# Recursive FASTopic Subject Navigation

## Status

This is a candidate design for the next subject-navigation experiment. It is
not a final architecture or an experiment result.

## Goal

Build a static hierarchy of subjects from real Nostr notes.

The interface begins with a small set of broad subjects. After the person
chooses one, it shows a small set of narrower subjects. This repeats until the
interface shows notes from the final, precise subject.

The subjects must come from the corpus. They are not written in advance.

## Inputs and Output

Input:

- 51,200 real Nostr notes, each identified by its `NoteId`;
- the text of each note;
- one vector per note;
- lexical word counts required by FASTopic.

Output:

- a fully precomputed subject tree;
- a short description for every displayed subject;
- the notes assigned to every subject;
- FASTopic's note-to-subject weights.

No embedding model, FASTopic model, or labeling model runs while the person
navigates the tree.

## Construction

### 1. Prepare the Note Text

Each note is converted into one canonical text value:

- replace opaque URLs, NIP-19 values, and invoices with typed markers;
- retain the surrounding text, hashtags, technical identifiers, code, and
  emoji;
- do not fetch or interpret linked content.

The same canonical text is used to create the note vector and FASTopic's word
counts.

### 2. Create One Vector per Note

Two embedding models are candidates:

- [Qwen3-Embedding-8B](https://huggingface.co/Qwen/Qwen3-Embedding-8B);
- [KaLM-Embedding-V2.5](https://huggingface.co/KaLM-Embedding/KaLM-embedding-multilingual-mini-instruct-v2.5).

For every note, the embedding model receives the same instruction:

```text
Instruct: Identify the subjects discussed in the given social-media post at both broad and specific levels.
Query:<canonical note text>
```

It returns one numerical vector for the complete note. It does not return
subject names or a list of subjects. The instruction makes subject matter at
multiple levels the similarity relation represented by the vector.

The result from each candidate model is a matrix with one vector row for every
`NoteId`.

### 3. Select One Embedding Model

The hierarchy requires one vector matrix. Qwen and KaLM would produce different
matrices, so one model must be selected before the hierarchy is built.

The model-selection procedure has not been designed. There is currently no
approved partial-tree comparison or winner-selection rule. Do not build the
hierarchy until this decision is made.

### 4. Split One Subject

Every tree node contains a set of note IDs. The root node contains all 51,200
note IDs.

To split one node:

1. Choose a child count between two and eight.
2. Give FASTopic the node's note vectors and word counts.
3. Fit FASTopic once using the node's frozen random seed.
4. FASTopic returns:
   - the requested number of unnamed subjects;
   - one weight for every note-subject pair;
   - characteristic words for each subject.
5. Route each note to the subject for which it has the largest weight.

The complete note-to-subject weight vector is retained for inspection, even
though the tree uses one route per note.

### 5. Continue or Stop

After a node is split:

- create no more than eight children;
- use fewer children when the node cannot support eight;
- split a child again when it contains more than the terminal-note limit;
- stop a branch when it is small enough;
- also stop when FASTopic cannot produce at least two supported narrower
  children.

Different branches may therefore have different depths.

Every recursive fit reuses the note vectors created in step 2. Notes are never
re-encoded while the tree is being built.

If an attempted split produces fewer than two supported children, discard that
split and keep the original node as a terminal subject.

### 6. Describe the Discovered Subjects

FASTopic's subjects are initially unnamed.

After a sibling group has been created, a labeling model receives:

- the parent description, except at the root;
- each child's characteristic words;
- representative notes from each child;
- contrasting notes from the sibling children.

It returns a short label and definition for each child. It may instead report
that a child cannot be described reliably.

The labeling model does not create subjects, assign notes, move notes, or
change the hierarchy.

### 7. Store and Navigate the Tree

The static artifact stores, for every node:

- its parent and children;
- its label and definition;
- its routed note IDs;
- the note weights from the FASTopic fit that created it;
- whether it is terminal.

The interface shows the root subjects, then the children of the selected
subject. It supports moving back or rejecting the available choices.

At a terminal subject:

- only notes routed through that complete path are eligible;
- notes are ordered by their weight for that terminal subject;
- weights from different levels are not multiplied together.

## Decisions Already Made

- Subjects are learned from the note corpus, not defined beforehand.
- Every note is encoded with the same frozen subject-oriented instruction.
- The complete tree is built before the person navigates it.
- Every node has at most eight children.
- The tree has no fixed depth.
- A branch keeps splitting until it is small enough or cannot produce two
  supported narrower children.
- One frozen FASTopic run builds each node; multiple seeds cannot be used to
  curate a preferred result.
- One note follows one route while the tree is constructed, but all of its
  sibling weights are retained.
- A labeling model describes discovered subjects but cannot change them.

## Not Yet Decided

- The maximum number of notes in a terminal subject.
- How the child count from two through eight is selected at each node.
- The minimum number of notes required for a supported child.
- What happens to notes routed into an undersized child when other children
  are supported.
- How one embedding model is selected.
- The exact selection of representative and contrasting notes for labeling.
- What happens when the labeling model cannot describe a child reliably.

These are unresolved design choices. An implementation must not silently
invent them.

## Why FASTopic Is the Candidate

[FASTopic](https://proceedings.neurips.cc/paper_files/paper/2024/file/998f8d8ff2697da2eae5f87143668754-Paper-Conference.pdf)
accepts both semantic note vectors and lexical word counts. One fit produces
the three outputs needed here:

- learned subject vectors;
- note-to-subject weights;
- characteristic words for description.

FASTopic itself produces one flat set of subjects. It does not produce this
tree. The experimental hypothesis is:

> Re-running FASTopic inside each routed subset will produce genuinely
> narrower subjects instead of merely smaller arbitrary partitions.

Its built-in hierarchy display does not test that hypothesis. It merges
subjects from one flat fit by similarity rather than learning new subjects
inside each parent.

## Known Risks

- Early hard-routing errors cannot be recovered deeper in the tree.
- A whole-note vector may blend several subjects.
- Rare subjects may not form a supported child.
- FASTopic may respond to shared wording instead of shared meaning.
- A persuasive label can hide a poor subject grouping.
- A different random seed may produce a different tree.
- Recursive FASTopic has not yet been validated for this Nostr navigation
  experiment.
