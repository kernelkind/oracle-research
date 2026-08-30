# Experiment 3: lexical coincidence

Status: **draft; every proposition and every `B` and `C` mask requires
human approval before encoding**.

## Assumption

> Lexical coincidences do not substitute for semantic relationships.

## Question

When two unrelated fine subjects use the same ambiguous word at once, do their
recovered subject relationships change after each one-sided substitution has
remained stable?

## Role and dependencies

The default spending gate is suite-level. Human approval, the frozen SSE and
candidate boundaries, construction-level candidate eligibility, blinding,
exact-input output validity, and exact-input repeatability are governed by
[README.md](README.md); none is an Experiment 3 lexical result.

Within this experiment:

1. `BASELINE` supplies one independent local recovery gate per trap;
2. the first-subject-only and second-subject-only collections are the local
   controls for using the ambiguous noun on either side alone; and
3. `BOTH` alone owns the lexical-collision verdict.

If the default spending graph stops upstream, Experiment 3 is skipped. An
explicitly authorized diagnostic run may still produce its own scoped results,
but those results cannot reopen the stopped edge. Within any run, exact-input
integrity and the local prerequisites below determine which lexical results are
available. If one trap's `BASELINE` relationships or a one-sided control do not
qualify, record that local prerequisite failure and give only that trap no
lexical verdict. Another trap remains scoreable when its own relationships and
inputs qualify.

The experiment uses three ambiguous words:

| Trap | First subject | Second subject |
|---|---|---|
| `COACH` | a swim-team instructor correcting freestyle arm motion | an intercity passenger vehicle carrying travelers overnight |
| `PITCHER` | a ballgame's starting player striking out nine batters | a handled ceramic vessel holding cold water |
| `BANK` | a financial institution approving a mortgage after reviewing wages | a river edge losing soil after heavy rain |

Each subject has four paraphrases of one fixed proposition. The event,
participants, relationships, and qualifications stay the same within the four
paraphrases. This prevents ordinary content differences inside a subject from
being mistaken for lexical sensitivity.

## Intervention

Every one of the 24 vector positions has two versions:

- `B` uses the baseline noun;
- `C` replaces it with the ambiguous noun shared by the trap's two subjects.

Within one position, the two complete masks differ only at that noun. Both
nouns are one tokenizer piece under the frozen Sentence-T5 tokenizer, so `B`
and `C` average the same number of selected token representations. This
controls token position, token count, and the pooling denominator. It does not
assume that the two nouns have identical learned representations.

A design-time check against the pinned tokenizer found 48 masks, 24 complete
`B/C` pairs, equal selected-piece counts within every pair, and exactly one
changed token position in every `B`-to-`C` comparison. The selected counts
range from 21 to 34 pieces. The executable experiment must repeat and preserve
this check.

The rest of each mask states the complete proposition. Each complete synthetic
note is also its complete mask. The system receives only opaque position IDs
and vectors; the subject identities and version names are scoring data.

## Fixture

### `COACH-SPORTS`

Fixed proposition: the speaker's swim-team instructor corrected the speaker's
freestyle arm motion during practice.

`COACH-SPORTS-1`

- `B` ⟦The trainer—our pool squad's instructor—corrected my freestyle arm movement during practice.⟧
- `C` ⟦The coach—our pool squad's instructor—corrected my freestyle arm movement during practice.⟧

`COACH-SPORTS-2`

- `B` ⟦At an aquatic rehearsal, the trainer—the person teaching my group—fixed how I moved my upper limbs in front crawl.⟧
- `C` ⟦At an aquatic rehearsal, the coach—the person teaching my group—fixed how I moved my upper limbs in front crawl.⟧

`COACH-SPORTS-3`

- `B` ⟦While I worked on the freestyle stroke, the trainer—the guide assigned to our swimmers—adjusted the action of my arms.⟧
- `C` ⟦While I worked on the freestyle stroke, the coach—the guide assigned to our swimmers—adjusted the action of my arms.⟧

`COACH-SPORTS-4`

- `B` ⟦The trainer—who leads my team's water sessions—corrected the swing of my upper limbs while I performed freestyle.⟧
- `C` ⟦The coach—who leads my team's water sessions—corrected the swing of my upper limbs while I performed freestyle.⟧

### `COACH-VEHICLE`

Fixed proposition: an intercity passenger road vehicle carried the speaker's
party overnight between two cities.

`COACH-VEHICLE-1`

- `B` ⟦The bus—a long-distance road conveyance for passengers—carried us overnight from one city to another.⟧
- `C` ⟦The coach—a long-distance road conveyance for passengers—carried us overnight from one city to another.⟧

`COACH-VEHICLE-2`

- `B` ⟦We spent the hours of darkness traveling between two urban centers aboard the bus—an intercity road service for people.⟧
- `C` ⟦We spent the hours of darkness traveling between two urban centers aboard the coach—an intercity road service for people.⟧

`COACH-VEHICLE-3`

- `B` ⟦During the night, the bus—motorized road transport for passengers making intercity journeys—took our party from one city to a different city.⟧
- `C` ⟦During the night, the coach—motorized road transport for passengers making intercity journeys—took our party from one city to a different city.⟧

`COACH-VEHICLE-4`

- `B` ⟦Our trip connecting a pair of distant cities continued through the night until morning inside the bus—a large roadway carrier for passengers.⟧
- `C` ⟦Our trip connecting a pair of distant cities continued through the night until morning inside the coach—a large roadway carrier for passengers.⟧

### `PITCHER-BALLGAME`

Fixed proposition: a team's starting thrower struck out nine batters in a
ballgame.

`PITCHER-BALLGAME-1`

- `B` ⟦The player—the team's starting thrower in the ballgame—struck out nine batters.⟧
- `C` ⟦The pitcher—the team's starting thrower in the ballgame—struck out nine batters.⟧

`PITCHER-BALLGAME-2`

- `B` ⟦Nine hitters went down on strikes against the player—the mound performer who opened the ballgame for the club.⟧
- `C` ⟦Nine hitters went down on strikes against the pitcher—the mound performer who opened the ballgame for the club.⟧

`PITCHER-BALLGAME-3`

- `B` ⟦The player—our side's first defensive launcher—recorded nine strikeouts in the diamond contest.⟧
- `C` ⟦The pitcher—our side's first defensive launcher—recorded nine strikeouts in the diamond contest.⟧

`PITCHER-BALLGAME-4`

- `B` ⟦Beginning the match as the person sending deliveries toward home plate, the player retired nine opponents through missed swings and called strikes.⟧
- `C` ⟦Beginning the match as the person sending deliveries toward home plate, the pitcher retired nine opponents through missed swings and called strikes.⟧

### `PITCHER-CONTAINER`

Fixed proposition: a handled, spouted ceramic vessel held cold water.

`PITCHER-CONTAINER-1`

- `B` ⟦The vessel—a ceramic item with a handle and pouring spout—held cold water.⟧
- `C` ⟦The pitcher—a ceramic item with a handle and pouring spout—held cold water.⟧

`PITCHER-CONTAINER-2`

- `B` ⟦Chilled water filled the vessel—an earthenware receptacle bearing a grip and a projecting lip.⟧
- `C` ⟦Chilled water filled the pitcher—an earthenware receptacle bearing a grip and a projecting lip.⟧

`PITCHER-CONTAINER-3`

- `B` ⟦The vessel—a pottery piece shaped with a loop and projecting mouth for pouring—was full of refrigerated water.⟧
- `C` ⟦The pitcher—a pottery piece shaped with a loop and projecting mouth for pouring—was full of refrigerated water.⟧

`PITCHER-CONTAINER-4`

- `B` ⟦We kept low-temperature water inside the vessel—a fired-clay holder whose side grasp and projecting lip permit pouring.⟧
- `C` ⟦We kept low-temperature water inside the pitcher—a fired-clay holder whose side grasp and projecting lip permit pouring.⟧

### `BANK-FINANCIAL`

Fixed proposition: a regulated financial organization approved the speaker's
mortgage application after reviewing wages.

`BANK-FINANCIAL-1`

- `B` ⟦The lender—the regulated organization financing our home purchase—approved our mortgage application after reviewing our wages.⟧
- `C` ⟦The bank—the regulated organization financing our home purchase—approved our mortgage application after reviewing our wages.⟧

`BANK-FINANCIAL-2`

- `B` ⟦After examining what we earned from work, the lender—the regulated financial business supplying money for a residence—approved our application for a housing loan.⟧
- `C` ⟦After examining what we earned from work, the bank—the regulated financial business supplying money for a residence—approved our application for a housing loan.⟧

`BANK-FINANCIAL-3`

- `B` ⟦Following its review of our earnings, the lender—a supervised provider of residential credit—gave consent to our home-loan petition.⟧
- `C` ⟦Following its review of our earnings, the bank—a supervised provider of residential credit—gave consent to our home-loan petition.⟧

`BANK-FINANCIAL-4`

- `B` ⟦The lender—the regulated company providing credit for our property acquisition—looked over our salaries and approved the proposed mortgage application.⟧
- `C` ⟦The bank—the regulated company providing credit for our property acquisition—looked over our salaries and approved the proposed mortgage application.⟧

### `BANK-RIVER`

Fixed proposition: after heavy rain, soil at a river's edge was removed by
fast water.

`BANK-RIVER-1`

- `B` ⟦After heavy rain, the shore—the ground beside the river—lost soil to rushing water.⟧
- `C` ⟦After heavy rain, the bank—the ground beside the river—lost soil to rushing water.⟧

`BANK-RIVER-2`

- `B` ⟦A swollen river washed earth from the shore—the sloping land along its channel—following a downpour.⟧
- `C` ⟦A swollen river washed earth from the bank—the sloping land along its channel—following a downpour.⟧

`BANK-RIVER-3`

- `B` ⟦The shore—the strip of terrain bordering the river—eroded when runoff from a downpour made the current race.⟧
- `C` ⟦The bank—the strip of terrain bordering the river—eroded when runoff from a downpour made the current race.⟧

`BANK-RIVER-4`

- `B` ⟦Torrential rain caused a rapid freshwater current to carry dirt away from the shore—the margin separating the moving river water from a field.⟧
- `C` ⟦Torrential rain caused a rapid freshwater current to carry dirt away from the bank—the margin separating the moving river water from a field.⟧

## Ten collections

`BASELINE` uses `B` at all 24 positions. For each trap, three additional
collections change only that trap's eight positions:

| Collection | First subject | Second subject | What it controls |
|---|---:|---:|---|
| `COACH-SPORTS-ONLY` | `C` | `B` | `coach` in the sports meaning only |
| `COACH-VEHICLE-ONLY` | `B` | `C` | `coach` in the vehicle meaning only |
| `COACH-BOTH` | `C` | `C` | shared `coach` identity across both meanings |
| `PITCHER-BALLGAME-ONLY` | `C` | `B` | `pitcher` in the ballgame meaning only |
| `PITCHER-CONTAINER-ONLY` | `B` | `C` | `pitcher` in the container meaning only |
| `PITCHER-BOTH` | `C` | `C` | shared `pitcher` identity across both meanings |
| `BANK-FINANCIAL-ONLY` | `C` | `B` | `bank` in the financial meaning only |
| `BANK-RIVER-ONLY` | `B` | `C` | `bank` in the river meaning only |
| `BANK-BOTH` | `C` | `C` | shared `bank` identity across both meanings |

All other positions remain `B`. Corresponding positions retain the same
opaque ID, input order, candidate configuration, and seed. The one-sided runs
show whether an ambiguous noun changes either subject before the noun is shared
across subjects. Only the `BOTH` run makes the designated substituted noun
identical across the two subjects.

## Two output comparisons

Every raw candidate output is preserved. Apply the shared output-validity,
canonicalization, repeatability, and blinding contract in [README.md](README.md)
before revealing fixture identities or doing either semantic comparison below.
In particular, duplicate member sets make an output invalid; they are never
silently removed or treated as a semantic or shape change.

Only valid, repeatable outputs are scored in the two separate ways below.

### 1. Subject relationships

Record:

1. whether each of the six approved four-position subject segments exists;
2. every pair of positions from different approved subjects that appears
   together in any returned segment.

This detects lost recovery of an approved subject and new cross-subject
grouping. For a valid output, it deliberately ignores singleton changes and
extra segments contained entirely inside one approved subject.

For one trap, its **local subject relationships** contain only:

1. whether each of that trap's two approved four-position subject segments
   exists; and
2. every cross-subject pair containing at least one of that trap's eight
   positions.

Changes involving only another trap remain complete-output diagnostics; they
do not gate or decide this trap.

### 2. Complete output

Use the shared canonical JSON as the complete output. It retains every valid
overlap and singleton. Also derive and sort the input IDs that occur in no
returned segment for the diagnostic record.

Relative to `BASELINE`, classify every valid arm as:

- **exactly stable** when its complete canonical output is equal;
- **shape-only change** when its complete output differs but the recorded
  subject relationships are equal;
- **semantic change** when its recorded subject relationships differ.

Shape-only changes are reported as stability diagnostics. They do not decide
whether shared spelling replaced a semantic relationship.

## Baseline qualification

After its two runs pass the shared validity and repeatability checks, score
baseline recovery independently for each trap. Each adjacent pair below is one
trap's two required segments:

```text
{COACH-SPORTS-1 ... COACH-SPORTS-4}
{COACH-VEHICLE-1 ... COACH-VEHICLE-4}
{PITCHER-BALLGAME-1 ... PITCHER-BALLGAME-4}
{PITCHER-CONTAINER-1 ... PITCHER-CONTAINER-4}
{BANK-FINANCIAL-1 ... BANK-FINANCIAL-4}
{BANK-RIVER-1 ... BANK-RIVER-4}
```

For one trap to qualify, both of its required segments must exist and every
other returned segment containing one of that trap's positions and at least two
positions total must be a subset of that position's approved subject. Extra
same-subject subsegments and singleton segments are allowed. A segment
involving only other traps does not affect this trap's baseline gate.

An invalid `BASELINE` raw output is an **output-contract failure**. Two valid
baseline outputs that disagree are a **repeatability failure**. If the valid,
repeatable `BASELINE` does not qualify for one trap, record a **local recovery
prerequisite failure** for that trap. It receives no lexical verdict. Other
traps use their own baseline relationships.

## Trap verdict

For one trap, apply these checks in order:

1. Its first-subject-only and second-subject-only collections must each produce
   a valid, repeatable output. An invalid control output is an
   **output-contract failure** for that exact input; disagreeing valid
   repetitions are a **repeatability failure** for that exact input. Either
   case withholds the trap verdict.
2. Each one-sided control must preserve that trap's local baseline subject
   relationships. A valid, repeatable control that does not is a
   **one-sided-control prerequisite failure**, not evidence about simultaneous
   shared spelling, and withholds the trap verdict.
3. Once both controls qualify, an invalid `BOTH` output is an ordinary
   **output-contract failure** for that exact input. It receives no lexical
   verdict. Disagreeing valid `BOTH` repetitions are likewise a repeatability
   failure with no lexical verdict.
4. If the controls qualify and `BOTH` is valid and repeatable, record **pass**
   when its local subject relationships equal the trap's baseline
   relationships. Record **lexical-collision failure** only when those local
   relationships differ.

Overall support requires all three traps to pass; do not average them. Report
all shape-only changes and the full segments added or removed. A shape-only
change is diagnostic and never changes a trap verdict.

A lexical-collision failure is strong evidence that the simultaneous shared
noun matters in this fixture after neither one-sided use changed the subject
relationships. It is not universal mechanistic proof: two individually
subthreshold vector shifts could combine across a candidate's decision
boundary.

## Protocol

1. Human-approve and freeze the six propositions, all 48 masks, the 10
   collection assignments, both output comparisons, and the verdict rules.
2. Freeze the complete candidate identity and document its construction-level
   permutation invariance before inspecting any vectors or candidate output.
3. Use `03-lexical-coincidence` as the shared blinding namespace. Derive and
   commit the opaque-ID mapping and order, then freeze the SSE boundary and all
   10 exact collection inputs.
4. Encode each distinct `B` and `C` mask once. Record dimensions and
   hashes, then preserve and reuse the exact vectors in every applicable
   collection.
5. Run each input twice in fresh candidate processes with identical
   vectors, opaque IDs, order, selector, configuration, and seed.
6. Preserve all 20 raw outputs while identities remain hidden. Validate each
   raw output before canonicalization, identity reveal, or semantic scoring.
7. Compare the shared canonical bytes for each valid identical-input pair. A
   mismatch is a repeatability failure, not a lexical result.
8. After the required outputs are immutable, reveal and verify the fixture
   mapping, qualify each trap's local `BASELINE` relationships, qualify that
   trap's controls, and only then score its valid, repeatable `BOTH` output.

The fixture is controlled development evidence because its labels are visible
while candidate algorithms may still be developed. If its result changes the
candidate, independent support requires a newly frozen holdout fixture.

## Required record

Preserve:

- every approved proposition and `B` and `C` mask;
- tokenizer IDs, selected positions, and piece counts for every mask;
- raw SSE vectors and hashes;
- the candidate implementation, preprocessing, configuration, seed, private
  opaque-ID mapping, order, and fine-output selector;
- all 20 raw outputs and validity results, plus canonical JSON bytes and hashes
  for every valid raw output;
- all 10 repeatability comparisons;
- all three local baseline qualifications, all six one-sided-control
  qualifications, and all three trap verdicts;
- every output-contract, repeatability, and prerequisite failure;
- every subject-relationship and complete-output difference;
- raw-vector cosine matrices and matched `B`/`C` cosine changes.

## Meaning of a result

A pass supports one narrow claim: in these three explicit, proposition-level
traps, sharing one ambiguous noun across two unrelated meanings did not change
the recovered subject relationships after both one-sided ambiguous-noun
conditions preserved them. It does not prove that the candidate used no
lexical information internally.

A prerequisite failure means a valid, repeatable baseline or control did not
reach the state needed to test lexical robustness. An output-contract or
repeatability failure supplies no semantic verdict. A lexical-collision failure
means the controls qualified and the valid, repeatable simultaneous shared-noun
output alone changed the subject relationships.
