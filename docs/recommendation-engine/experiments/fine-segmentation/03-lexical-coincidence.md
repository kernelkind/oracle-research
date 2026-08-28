# Experiment 3: lexical coincidence

Status: **draft; notes, masks, and expected relationships require human
approval before encoding**.

## Assumption under test

> Lexical coincidences do not substitute for semantic relationships.

The desired structure is semantic. A conspicuous shared word must not join two
different meanings, while paraphrases of one meaning must remain recoverable
even when they share less wording.

## Question

Can one frozen candidate recover the two meanings in each of three lexical
traps without joining them through an ambiguous word they share?

## Why this fixture exists

Each trap has equal support on both sides: three independently worded instances
of one meaning and three of the other. This avoids confounding lexical
robustness with singleton or unequal-density handling.

Some formulations use the conspicuous word, while others express the same
meaning differently. All notes use the same carrier sentence, so unmasked
context is not the intended variable.

Each trap is anchored by one ambiguous case-insensitive lexeme—`rust`, `Java`,
or `mouse`—that appears in at least one formulation on each side. Paraphrases
may omit that lexeme; they remain members of the same human-declared subject.

## Synthetic notes and masks

### Trap 1: programming-language Rust versus metal corrosion

#### Subject `RUST-CODE`: Rust borrowing errors

**RUST-CODE-1**

> This note concerns ⟦fixing a Rust borrow-checker error⟧.

**RUST-CODE-2**

> This note concerns ⟦resolving a rejected mutable borrow in Rust code⟧.

**RUST-CODE-3**

> This note concerns ⟦debugging a borrowing conflict reported by the Rust
> compiler⟧.

#### Subject `RUST-METAL`: rust corrosion on bicycle chains

**RUST-METAL-1**

> This note concerns ⟦removing rust corrosion from a bicycle chain⟧.

**RUST-METAL-2**

> This note concerns ⟦cleaning orange oxidation from steel bicycle links⟧.

**RUST-METAL-3**

> This note concerns ⟦removing iron corrosion from a bike chain⟧.

### Trap 2: Java software versus the island of Java

#### Subject `JAVA-CODE`: Java null-reference failures

**JAVA-CODE-1**

> This note concerns ⟦debugging a Java NullPointerException⟧.

**JAVA-CODE-2**

> This note concerns ⟦tracing a null-reference crash in a Java service⟧.

**JAVA-CODE-3**

> This note concerns ⟦fixing a Java program that dereferences null⟧.

#### Subject `JAVA-ISLAND`: travel across the island of Java

**JAVA-ISLAND-1**

> This note concerns ⟦hiking across the island of Java⟧.

**JAVA-ISLAND-2**

> This note concerns ⟦trekking through Java's volcanic highlands⟧.

**JAVA-ISLAND-3**

> This note concerns ⟦trekking across the Indonesian island of Java⟧.

### Trap 3: computer mouse versus animal mouse

#### Subject `MOUSE-DEVICE`: repairing a computer mouse

**MOUSE-DEVICE-1**

> This note concerns ⟦repairing a broken computer mouse⟧.

**MOUSE-DEVICE-2**

> This note concerns ⟦fixing a malfunctioning cursor-control device⟧.

**MOUSE-DEVICE-3**

> This note concerns ⟦replacing the click switch in a USB mouse⟧.

#### Subject `MOUSE-ANIMAL`: mice nesting in a home

**MOUSE-ANIMAL-1**

> This note concerns ⟦a house mouse nesting in the pantry⟧.

**MOUSE-ANIMAL-2**

> This note concerns ⟦a small rodent building a nest behind the cupboard⟧.

**MOUSE-ANIMAL-3**

> This note concerns ⟦a wild mouse nesting inside a kitchen⟧.

The six subject identities and three trap pairings are scoring data. The
candidate does not receive them.

## Frozen hypothesis

1. Each of the six three-vector subjects will be recovered as an exact
   three-vector segment.
2. No segment will join either side of the Rust trap.
3. No segment will join either side of the Java trap.
4. No segment will join either side of the mouse trap.

The first condition prevents a candidate from passing by refusing to group
anything. The remaining conditions prevent it from returning correct narrow
segments while also emitting lexical false merges as additional fine segments.

A subject is **recovered** when one segment contains exactly its three vectors
among this eighteen-vector fixture. This prevents an unrelated cross-trap
mixture from masquerading as recovery. Additional cross-trap segments are
recorded but do not affect this experiment's verdict; their correctness would
require separate fine-resolution judgments.

## Frozen system boundary

Use the shared 768-dimensional Sentence-T5-base SSE checkpoint identified in:

README.md

Preserve its raw outputs exactly. Any normalization, distance, or other
preprocessing belongs to the candidate's frozen configuration.

The candidate receives only opaque IDs and vectors. It may return overlapping
fine segments and leave vectors unassigned. Scoring consumes only its
predeclared fine-segment collection; coarser parents are excluded.

This is a visible development fixture, not held-out confirmation.

## Protocol

1. Obtain human approval of all eighteen notes, masks, subject identities, and
   trap pairings.
2. Freeze this document and the candidate's implementation, preprocessing,
   configuration, fine-output rule, and seed.
3. Generate all eighteen SSE vectors once and preserve their exact bytes.
4. Give the candidate only opaque IDs and vectors in one frozen shuffled order.
5. Preserve the complete returned fine-segment collection.
6. Reveal the fixture identities and score the frozen hypothesis.
7. Show every failure with the complete notes, masks, segment memberships, and
   cosine values.

## Pass rule

The experiment passes only if:

- all six subjects are recovered as exact three-vector segments;
- no pair crossing one of the three declared trap boundaries shares a returned
  fine segment.

Cross-trap memberships are diagnostics only. One failure on a declared trap
boundary is not averaged away.

## Required record

Preserve:

- recovery status for all six subjects;
- every declared trap-boundary membership;
- every other cross-trap membership as a non-scoring diagnostic;
- every returned segment, overlap, and omission;
- the exact shuffled input order;
- the cosine matrix and nearest-neighbor order computed from immutable raw SSE
  outputs;
- the smallest within-subject cosine for each subject;
- every cosine crossing a lexical-trap boundary;
- the raw SSE artifact and hashes;
- the complete candidate configuration and seed.

Cosine can suggest whether a misleading relationship was already prominent in
the raw vector geometry. It does not prove causation, describe every geometric
relationship available to a candidate, or determine the verdict.

## What a result means

A pass supports lexical robustness for these three controlled traps. It does
not establish arbitrary homonym handling, natural-language robustness,
context invariance, density behavior, stability, or hierarchy quality.

A failure applies to the complete vector-plus-candidate system. The diagnostics
may indicate a likely failure stage, but this experiment cannot conclusively
attribute the cause to SSE or the segmentation procedure.
