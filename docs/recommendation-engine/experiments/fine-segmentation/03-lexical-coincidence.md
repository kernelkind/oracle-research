# Experiment 3: paired lexical coincidence

Status: **draft; every subject identity, baseline/treatment pair, and mask
requires human approval before encoding**.

## Assumption under test

> Lexical coincidences do not substitute for semantic relationships.

## Question

Starting from a run that separates each trap's two meanings, does replacing
either or both meanings' unambiguous wording with the same ambiguous word
create false relationships or destroy valid ones?

## Controlled intervention

Use one 24-vector baseline in which every meaning has unambiguous wording.
Then run three variants for each trap:

1. replace the wording for its first meaning only;
2. replace the wording for its second meaning only;
3. replace the wording for both meanings.

All other positions remain in baseline form. This produces ten 24-vector runs:
one shared baseline and three isolated variants for each of three traps.

The ambiguous words are `draft`, `pupil`, and `trunk`. Each appears once in
every treatment mask on both sides of its trap: four times per meaning and
eight times per trap. It never appears in the corresponding baseline masks.

Every run contains exactly one version of every position; a position's
baseline and treatment vectors never appear together. The whole synthetic note
is masked, so unmasked context cannot affect this experiment.

## Paired synthetic notes and masks

`B` is the baseline mask. `T` is the corresponding treatment mask.

### Trap 1: `draft`

Subject `DRAFT-DOCUMENT`: correcting citation errors in a grant-proposal
version

| ID | Mask |
|---|---|
| DOC-1 B | ⟦I corrected citation errors in the preliminary version of the grant proposal before submission.⟧ |
| DOC-1 T | ⟦I corrected citation errors in the draft of the grant proposal before submission.⟧ |
| DOC-2 B | ⟦Before submitting the grant proposal, I fixed incorrect citations in its preliminary version.⟧ |
| DOC-2 T | ⟦Before submitting the grant proposal, I fixed incorrect citations in its draft.⟧ |
| DOC-3 B | ⟦I reviewed the grant proposal's preliminary version and repaired mistakes in its citations.⟧ |
| DOC-3 T | ⟦I reviewed the grant proposal's draft and repaired mistakes in its citations.⟧ |
| DOC-4 B | ⟦The preliminary version of my grant proposal had citation errors that I corrected before sending it.⟧ |
| DOC-4 T | ⟦The draft of my grant proposal had citation errors that I corrected before sending it.⟧ |

Subject `DRAFT-AIR`: blocking cold airflow beneath a kitchen door

| ID | Mask |
|---|---|
| AIR-1 B | ⟦I installed a door sweep to block the airflow under the kitchen door.⟧ |
| AIR-1 T | ⟦I installed a door sweep to block the draft under the kitchen door.⟧ |
| AIR-2 B | ⟦A new sweep beneath the kitchen door stopped the airflow that had been entering the room.⟧ |
| AIR-2 T | ⟦A new sweep beneath the kitchen door stopped the draft that had been entering the room.⟧ |
| AIR-3 B | ⟦I sealed the bottom of the kitchen door so the cold airflow no longer entered.⟧ |
| AIR-3 T | ⟦I sealed the bottom of the kitchen door so the cold draft no longer entered.⟧ |
| AIR-4 B | ⟦To stop the airflow from the gap under the kitchen door, I fitted a door sweep.⟧ |
| AIR-4 T | ⟦To stop the draft from the gap under the kitchen door, I fitted a door sweep.⟧ |

### Trap 2: `pupil`

Subject `PUPIL-STUDENT`: teaching multiplication to a primary-school student

| ID | Mask |
|---|---|
| STUDENT-1 B | ⟦The teacher showed the primary-school student how to solve a multiplication problem.⟧ |
| STUDENT-1 T | ⟦The teacher showed the primary-school pupil how to solve a multiplication problem.⟧ |
| STUDENT-2 B | ⟦The teacher guided the primary-school student through each step of multiplying two numbers.⟧ |
| STUDENT-2 T | ⟦The teacher guided the primary-school pupil through each step of multiplying two numbers.⟧ |
| STUDENT-3 B | ⟦During the math lesson, the primary-school student learned multiplication with the teacher's help.⟧ |
| STUDENT-3 T | ⟦During the math lesson, the primary-school pupil learned multiplication with the teacher's help.⟧ |
| STUDENT-4 B | ⟦The tutor taught the primary-school student a method for solving multiplication problems.⟧ |
| STUDENT-4 T | ⟦The tutor taught the primary-school pupil a method for solving multiplication problems.⟧ |

Subject `PUPIL-EYE`: an eye opening constricting in bright light

| ID | Mask |
|---|---|
| EYE-1 B | ⟦The iris opening narrowed under bright light.⟧ |
| EYE-1 T | ⟦The pupil narrowed under bright light.⟧ |
| EYE-2 B | ⟦A bright examination lamp caused the iris opening to contract.⟧ |
| EYE-2 T | ⟦A bright examination lamp caused the pupil to contract.⟧ |
| EYE-3 B | ⟦The iris opening became smaller when light shone into the eye.⟧ |
| EYE-3 T | ⟦The pupil became smaller when light shone into the eye.⟧ |
| EYE-4 B | ⟦The eye exam recorded the iris opening constricting in response to bright light.⟧ |
| EYE-4 T | ⟦The eye exam recorded the pupil constricting in response to bright light.⟧ |

### Trap 3: `trunk`

Subject `TRUNK-ELEPHANT`: an elephant spraying itself with water

| ID | Mask |
|---|---|
| ELEPHANT-1 B | ⟦An elephant sprayed water over its back with its proboscis.⟧ |
| ELEPHANT-1 T | ⟦An elephant sprayed water over its back with its trunk.⟧ |
| ELEPHANT-2 B | ⟦At the sanctuary, an elephant used its proboscis to shower its body with water.⟧ |
| ELEPHANT-2 T | ⟦At the sanctuary, an elephant used its trunk to shower its body with water.⟧ |
| ELEPHANT-3 B | ⟦An elephant sprayed its body with water from its proboscis.⟧ |
| ELEPHANT-3 T | ⟦An elephant sprayed its body with water from its trunk.⟧ |
| ELEPHANT-4 B | ⟦At the watering pool, an elephant splashed water onto its skin with its proboscis.⟧ |
| ELEPHANT-4 T | ⟦At the watering pool, an elephant splashed water onto its skin with its trunk.⟧ |

Subject `TRUNK-CAR`: loading groceries into a car's rear cargo compartment

| ID | Mask |
|---|---|
| CAR-1 B | ⟦I loaded grocery bags into my sedan's cargo compartment.⟧ |
| CAR-1 T | ⟦I loaded grocery bags into my sedan's trunk.⟧ |
| CAR-2 B | ⟦I arranged the groceries inside my sedan's cargo compartment.⟧ |
| CAR-2 T | ⟦I arranged the groceries inside my sedan's trunk.⟧ |
| CAR-3 B | ⟦I placed the supermarket bags in my sedan's cargo compartment.⟧ |
| CAR-3 T | ⟦I placed the supermarket bags in my sedan's trunk.⟧ |
| CAR-4 B | ⟦I stowed the grocery bags securely in my sedan's cargo compartment.⟧ |
| CAR-4 T | ⟦I stowed the grocery bags securely in my sedan's trunk.⟧ |

The six subject identities and three trap pairings are scoring data. The
system receives only opaque IDs and vectors. The IDs printed above exist only
for human review and must be remapped before any candidate run.

## Scoring

For any two positions, record **together** when at least one returned fine
segment contains both vectors. Otherwise record **apart**.

Each trap contains:

- 12 within-subject pairs: six from each four-vector subject;
- 16 pairs crossing the two meanings of the ambiguous word.

### Baseline prerequisite

A trap qualifies for the lexical test only when its baseline run puts:

- all 12 within-subject pairs together; and
- all 16 cross-meaning pairs apart.

If not, record a **baseline prerequisite failure**. That trap cannot show what
the ambiguous word changed.

This prerequisite prevents meaningless passes: returning no relationships
fails the within-subject check, while returning one giant relationship fails
the cross-meaning check.

### Variant verdict

A qualified trap passes only when all three of its variant runs preserve all
28 scored pairwise relationships from baseline:

- a within-subject pair changing from together to apart means valid recovery
  was lost after a controlled substitution;
- a cross-meaning pair changing from apart to together means a controlled
  substitution created a false relationship.

Record the complete four-state pattern for every pair: baseline, first-side
only, second-side only, and both sides.

- A change in a one-sided run means one substitution was sufficient.
- A change only in the both-sides run is the strongest evidence of interaction
  between the two uses of the ambiguous word.
- A relation between unchanged vectors that changes in a one-sided run exposes
  a collection-dependent effect of the substituted vectors.

These patterns identify where the system changed. They do not prove that exact
token matching, rather than nonlinear embedding or segmentation behavior, was
the internal mechanism.

Do not average the three traps. Report each independently. Segments joining
different traps are diagnostics only; this experiment has no approved truth
for those relationships.

This scoring does not require exact segment shapes and permits overlapping
segments or unassigned vectors.

## Frozen system boundary

Use the shared 768-dimensional Sentence-T5-base SSE checkpoint identified in
[the experiment README](README.md). Preserve its raw outputs exactly.

Freeze the fine-segmentation implementation, preprocessing, configuration,
fine-output rule, and random seed before any run. Any normalization or
distance calculation belongs to that frozen configuration.

This is a visible development fixture, not held-out confirmation.

## Protocol

1. Obtain human approval of all six subject identities, all 24
   baseline/treatment mask pairs, and the three trap assignments.
2. Freeze this document, SSE, and the complete fine-segmentation candidate.
3. Assign the same 24 opaque IDs and shuffled positions to corresponding
   baseline and treatment vectors.
4. Generate the 24 baseline and 24 treatment SSE vectors once and preserve
   their exact bytes and tokenizer-piece counts.
5. Run the all-baseline collection in a clean process.
6. For each trap, run its first-side-only, second-side-only, and both-sides
   variants in separate clean processes. Keep every other position at
   baseline.
7. Use the same positions, configuration, and seed in all ten runs.
8. Preserve all ten complete outputs before inspecting or scoring any of them.
9. Score the baseline prerequisite and three variant transitions for every
   trap.

## Required record

Preserve:

- all paired inputs and scoring identities;
- all ten complete returned fine-segment collections;
- every scored pair's four-state pattern for its trap;
- every changed pair;
- every overlap and unassigned vector;
- the exact input positions;
- tokenizer-piece counts for every baseline/treatment pair;
- cosine similarity for every matched baseline/treatment vector pair;
- complete cosine matrices and nearest-neighbor orders for all ten runs;
- raw SSE artifacts and hashes;
- the complete fine-segmentation configuration and seed.

Cosine diagnostics may show how the controlled wording change affected the raw
geometry. They do not determine the experiment's verdict or assign a failure
specifically to SSE or fine segmentation.

## What a result means

A pass supports lexical robustness for these three balanced, common-word traps
in an isolated synthetic collection.

A baseline prerequisite failure is ordinary recovery failure, not evidence of
a lexical-coincidence failure. A variant failure after a qualified baseline
shows that the controlled lexical substitution changed the behavior of the
complete SSE-plus-fine-segmentation system. The four-state pattern distinguishes
one-sided substitution sensitivity from a both-sides-only interaction, but
does not by itself prove the system's internal failure mechanism.

This experiment does not establish robustness for arbitrary ambiguous words,
natural social-media text, a large mixed corpus, unmasked context, unequal
density, stability, or hierarchy construction.
