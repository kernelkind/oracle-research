# Experiment 3: lexical coincidence

Status: **draft; every proposition and every `B`, `P`, and `C` mask requires
human approval before encoding**.

## Assumption

> Lexical coincidences do not substitute for semantic relationships.

## Question

If two unrelated fine subjects happen to use the same ambiguous word, does the
fine-segmentation result change *because both subjects now share that word*?

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

Every one of the 24 vector positions has three versions:

- `B` uses the baseline noun;
- `P` replaces it with a different noun used only for that subject;
- `C` replaces it with the ambiguous noun shared by the trap's two subjects.

Within one position, the three complete masks differ only at that noun. Every
substituted noun is one tokenizer piece under the frozen Sentence-T5 tokenizer,
so `B`, `P`, and `C` average the same number of selected token
representations. This controls token position, token count, and the pooling
denominator. It does not assume that the three nouns have identical learned
representations.

A design-time check against the pinned tokenizer found 72 masks, 24 complete
`B/P/C` trios, equal selected-piece counts within every trio, and exactly one
changed token position in every `B`-to-`P` and `B`-to-`C` comparison. The
selected counts range from 21 to 34 pieces. The executable experiment must
repeat and preserve this check.

The rest of each mask states the complete proposition. Each complete synthetic
note is also its complete mask. The system receives only opaque position IDs
and vectors; the subject identities and version names are scoring data.

## Fixture

### `COACH-SPORTS`

Fixed proposition: the speaker's swim-team instructor corrected the speaker's
freestyle arm motion during practice.

`COACH-SPORTS-1`

- `B` ⟦The trainer—our pool squad's instructor—corrected my freestyle arm movement during practice.⟧
- `P` ⟦The mentor—our pool squad's instructor—corrected my freestyle arm movement during practice.⟧
- `C` ⟦The coach—our pool squad's instructor—corrected my freestyle arm movement during practice.⟧

`COACH-SPORTS-2`

- `B` ⟦At an aquatic rehearsal, the trainer—the person teaching my group—fixed how I moved my upper limbs in front crawl.⟧
- `P` ⟦At an aquatic rehearsal, the mentor—the person teaching my group—fixed how I moved my upper limbs in front crawl.⟧
- `C` ⟦At an aquatic rehearsal, the coach—the person teaching my group—fixed how I moved my upper limbs in front crawl.⟧

`COACH-SPORTS-3`

- `B` ⟦While I worked on the freestyle stroke, the trainer—the guide assigned to our swimmers—adjusted the action of my arms.⟧
- `P` ⟦While I worked on the freestyle stroke, the mentor—the guide assigned to our swimmers—adjusted the action of my arms.⟧
- `C` ⟦While I worked on the freestyle stroke, the coach—the guide assigned to our swimmers—adjusted the action of my arms.⟧

`COACH-SPORTS-4`

- `B` ⟦The trainer—who leads my team's water sessions—corrected the swing of my upper limbs while I performed freestyle.⟧
- `P` ⟦The mentor—who leads my team's water sessions—corrected the swing of my upper limbs while I performed freestyle.⟧
- `C` ⟦The coach—who leads my team's water sessions—corrected the swing of my upper limbs while I performed freestyle.⟧

### `COACH-VEHICLE`

Fixed proposition: an intercity passenger road vehicle carried the speaker's
party overnight between two cities.

`COACH-VEHICLE-1`

- `B` ⟦The bus—a long-distance road conveyance for passengers—carried us overnight from one city to another.⟧
- `P` ⟦The vehicle—a long-distance road conveyance for passengers—carried us overnight from one city to another.⟧
- `C` ⟦The coach—a long-distance road conveyance for passengers—carried us overnight from one city to another.⟧

`COACH-VEHICLE-2`

- `B` ⟦We spent the hours of darkness traveling between two urban centers aboard the bus—an intercity road service for people.⟧
- `P` ⟦We spent the hours of darkness traveling between two urban centers aboard the vehicle—an intercity road service for people.⟧
- `C` ⟦We spent the hours of darkness traveling between two urban centers aboard the coach—an intercity road service for people.⟧

`COACH-VEHICLE-3`

- `B` ⟦During the night, the bus—motorized road transport for passengers making intercity journeys—took our party from one city to a different city.⟧
- `P` ⟦During the night, the vehicle—motorized road transport for passengers making intercity journeys—took our party from one city to a different city.⟧
- `C` ⟦During the night, the coach—motorized road transport for passengers making intercity journeys—took our party from one city to a different city.⟧

`COACH-VEHICLE-4`

- `B` ⟦Our trip connecting a pair of distant cities continued through the night until morning inside the bus—a large roadway carrier for passengers.⟧
- `P` ⟦Our trip connecting a pair of distant cities continued through the night until morning inside the vehicle—a large roadway carrier for passengers.⟧
- `C` ⟦Our trip connecting a pair of distant cities continued through the night until morning inside the coach—a large roadway carrier for passengers.⟧

### `PITCHER-BALLGAME`

Fixed proposition: a team's starting thrower struck out nine batters in a
ballgame.

`PITCHER-BALLGAME-1`

- `B` ⟦The player—the team's starting thrower in the ballgame—struck out nine batters.⟧
- `P` ⟦The athlete—the team's starting thrower in the ballgame—struck out nine batters.⟧
- `C` ⟦The pitcher—the team's starting thrower in the ballgame—struck out nine batters.⟧

`PITCHER-BALLGAME-2`

- `B` ⟦Nine hitters went down on strikes against the player—the mound performer who opened the ballgame for the club.⟧
- `P` ⟦Nine hitters went down on strikes against the athlete—the mound performer who opened the ballgame for the club.⟧
- `C` ⟦Nine hitters went down on strikes against the pitcher—the mound performer who opened the ballgame for the club.⟧

`PITCHER-BALLGAME-3`

- `B` ⟦The player—our side's first defensive launcher—recorded nine strikeouts in the diamond contest.⟧
- `P` ⟦The athlete—our side's first defensive launcher—recorded nine strikeouts in the diamond contest.⟧
- `C` ⟦The pitcher—our side's first defensive launcher—recorded nine strikeouts in the diamond contest.⟧

`PITCHER-BALLGAME-4`

- `B` ⟦Beginning the match as the person sending deliveries toward home plate, the player retired nine opponents through missed swings and called strikes.⟧
- `P` ⟦Beginning the match as the person sending deliveries toward home plate, the athlete retired nine opponents through missed swings and called strikes.⟧
- `C` ⟦Beginning the match as the person sending deliveries toward home plate, the pitcher retired nine opponents through missed swings and called strikes.⟧

### `PITCHER-CONTAINER`

Fixed proposition: a handled, spouted ceramic vessel held cold water.

`PITCHER-CONTAINER-1`

- `B` ⟦The vessel—a ceramic item with a handle and pouring spout—held cold water.⟧
- `P` ⟦The container—a ceramic item with a handle and pouring spout—held cold water.⟧
- `C` ⟦The pitcher—a ceramic item with a handle and pouring spout—held cold water.⟧

`PITCHER-CONTAINER-2`

- `B` ⟦Chilled water filled the vessel—an earthenware receptacle bearing a grip and a projecting lip.⟧
- `P` ⟦Chilled water filled the container—an earthenware receptacle bearing a grip and a projecting lip.⟧
- `C` ⟦Chilled water filled the pitcher—an earthenware receptacle bearing a grip and a projecting lip.⟧

`PITCHER-CONTAINER-3`

- `B` ⟦The vessel—a pottery piece shaped with a loop and projecting mouth for pouring—was full of refrigerated water.⟧
- `P` ⟦The container—a pottery piece shaped with a loop and projecting mouth for pouring—was full of refrigerated water.⟧
- `C` ⟦The pitcher—a pottery piece shaped with a loop and projecting mouth for pouring—was full of refrigerated water.⟧

`PITCHER-CONTAINER-4`

- `B` ⟦We kept low-temperature water inside the vessel—a fired-clay holder whose side grasp and projecting lip permit pouring.⟧
- `P` ⟦We kept low-temperature water inside the container—a fired-clay holder whose side grasp and projecting lip permit pouring.⟧
- `C` ⟦We kept low-temperature water inside the pitcher—a fired-clay holder whose side grasp and projecting lip permit pouring.⟧

### `BANK-FINANCIAL`

Fixed proposition: a regulated financial organization approved the speaker's
mortgage application after reviewing wages.

`BANK-FINANCIAL-1`

- `B` ⟦The lender—the regulated organization financing our home purchase—approved our mortgage application after reviewing our wages.⟧
- `P` ⟦The institution—the regulated organization financing our home purchase—approved our mortgage application after reviewing our wages.⟧
- `C` ⟦The bank—the regulated organization financing our home purchase—approved our mortgage application after reviewing our wages.⟧

`BANK-FINANCIAL-2`

- `B` ⟦After examining what we earned from work, the lender—the regulated financial business supplying money for a residence—approved our application for a housing loan.⟧
- `P` ⟦After examining what we earned from work, the institution—the regulated financial business supplying money for a residence—approved our application for a housing loan.⟧
- `C` ⟦After examining what we earned from work, the bank—the regulated financial business supplying money for a residence—approved our application for a housing loan.⟧

`BANK-FINANCIAL-3`

- `B` ⟦Following its review of our earnings, the lender—a supervised provider of residential credit—gave consent to our home-loan petition.⟧
- `P` ⟦Following its review of our earnings, the institution—a supervised provider of residential credit—gave consent to our home-loan petition.⟧
- `C` ⟦Following its review of our earnings, the bank—a supervised provider of residential credit—gave consent to our home-loan petition.⟧

`BANK-FINANCIAL-4`

- `B` ⟦The lender—the regulated company providing credit for our property acquisition—looked over our salaries and approved the proposed mortgage application.⟧
- `P` ⟦The institution—the regulated company providing credit for our property acquisition—looked over our salaries and approved the proposed mortgage application.⟧
- `C` ⟦The bank—the regulated company providing credit for our property acquisition—looked over our salaries and approved the proposed mortgage application.⟧

### `BANK-RIVER`

Fixed proposition: after heavy rain, soil at a river's edge was removed by
fast water.

`BANK-RIVER-1`

- `B` ⟦After heavy rain, the shore—the ground beside the river—lost soil to rushing water.⟧
- `P` ⟦After heavy rain, the edge—the ground beside the river—lost soil to rushing water.⟧
- `C` ⟦After heavy rain, the bank—the ground beside the river—lost soil to rushing water.⟧

`BANK-RIVER-2`

- `B` ⟦A swollen river washed earth from the shore—the sloping land along its channel—following a downpour.⟧
- `P` ⟦A swollen river washed earth from the edge—the sloping land along its channel—following a downpour.⟧
- `C` ⟦A swollen river washed earth from the bank—the sloping land along its channel—following a downpour.⟧

`BANK-RIVER-3`

- `B` ⟦The shore—the strip of terrain bordering the river—eroded when runoff from a downpour made the current race.⟧
- `P` ⟦The edge—the strip of terrain bordering the river—eroded when runoff from a downpour made the current race.⟧
- `C` ⟦The bank—the strip of terrain bordering the river—eroded when runoff from a downpour made the current race.⟧

`BANK-RIVER-4`

- `B` ⟦Torrential rain caused a rapid freshwater current to carry dirt away from the shore—the margin separating the moving river water from a field.⟧
- `P` ⟦Torrential rain caused a rapid freshwater current to carry dirt away from the edge—the margin separating the moving river water from a field.⟧
- `C` ⟦Torrential rain caused a rapid freshwater current to carry dirt away from the bank—the margin separating the moving river water from a field.⟧

## Thirteen collections

`BASELINE` uses `B` at all 24 positions. For each trap, four additional
collections change only that trap's eight positions:

| Collection | First subject | Second subject | What it controls |
|---|---:|---:|---|
| `COACH-PLACEBO` | `P` | `P` | two ordinary noun substitutions |
| `COACH-SPORTS-ONLY` | `C` | `B` | `coach` in the sports meaning only |
| `COACH-VEHICLE-ONLY` | `B` | `C` | `coach` in the vehicle meaning only |
| `COACH-BOTH` | `C` | `C` | shared `coach` identity across both meanings |
| `PITCHER-PLACEBO` | `P` | `P` | two ordinary noun substitutions |
| `PITCHER-BALLGAME-ONLY` | `C` | `B` | `pitcher` in the ballgame meaning only |
| `PITCHER-CONTAINER-ONLY` | `B` | `C` | `pitcher` in the container meaning only |
| `PITCHER-BOTH` | `C` | `C` | shared `pitcher` identity across both meanings |
| `BANK-PLACEBO` | `P` | `P` | two ordinary noun substitutions |
| `BANK-FINANCIAL-ONLY` | `C` | `B` | `bank` in the financial meaning only |
| `BANK-RIVER-ONLY` | `B` | `C` | `bank` in the river meaning only |
| `BANK-BOTH` | `C` | `C` | shared `bank` identity across both meanings |

All other positions remain `B`. Corresponding positions retain the same
opaque ID, input order, candidate configuration, and seed. The one-sided runs
show whether an ambiguous noun changes either subject before the noun is shared
across subjects. Only the `BOTH` run makes the designated substituted noun
identical across the two subjects.

## Lexical-baseline gate

Before encoding with SSE, try to solve the fixture directly from its words
using three deliberately lexical representations:

1. lowercase exact-token Jaccard similarity;
2. lowercase word unigram-and-bigram TF-IDF cosine similarity;
3. lowercase character 3-to-5-gram TF-IDF cosine similarity.

Normalize text to Unicode NFC, lowercase it, and collapse each whitespace run
to one space. For token methods, treat each maximal sequence of Unicode letters
or numbers as one token. Character n-grams operate directly on the normalized
text, including punctuation. Fit TF-IDF vocabulary and document frequencies
once on the union of every distinct `B`, `P`, and `C` mask. Use
`idf = log((1 + N) / (1 + df)) + 1`, raw term counts, and L2 normalization.

For each representation, sweep every distinct similarity occurring between
any pair of the 72 masks, plus the no-edge boundary above the largest
similarity. At one fixed threshold for all 13 collections, connect two
positions when their similarity meets or exceeds the threshold and return the
connected components. The fixture fails this gate if any representation and
threshold qualifies `BASELINE` and returns the same six exact four-position
components in all 12 variants.

The gate is intentionally favorable to the lexical baselines: their best
threshold is selected after seeing the fixture. It does not prove that no
possible lexical method could pass. It rejects a fixture already solved by
three obvious lexical shortcuts. A gate failure requires fixture redesign and
new human approval before any SSE run.

The exact draft fixture above passed a design-time preflight. Exact-token
Jaccard had no threshold that recovered `BASELINE`. Word and character TF-IDF
each recovered `BASELINE` at some thresholds, but neither preserved the six
exact four-position components across all 13 collections. The executable
experiment must rerun and preserve this gate; the preflight is not an
experimental result.

## Two output comparisons

Every raw candidate output is preserved. Score it in two separate ways.

### 1. Subject relationships

Record:

1. whether each of the six approved four-position subject segments exists;
2. every pair of positions from different approved subjects that appears
   together in any returned segment.

This detects lost recovery of an approved subject and new cross-subject
grouping. It deliberately ignores duplicate segments, singleton changes, and
extra segments contained entirely inside one approved subject.

### 2. Complete output

Canonicalize without discarding information:

1. sort the member IDs inside each returned segment;
2. sort the complete list of segments while retaining overlaps, singleton
   segments, and duplicate segments;
3. derive and sort IDs that occur in no returned segment.

Segment IDs and output order are ignored because they carry no meaning. An
empty segment, an unknown ID, or a repeated member inside one segment makes the
output invalid.

Relative to `BASELINE`, classify every valid arm as:

- **exactly stable** when its complete canonical output is equal;
- **shape-only change** when its complete output differs but the recorded
  subject relationships are equal;
- **semantic change** when its recorded subject relationships differ.

Shape-only changes are reported as stability diagnostics. They do not decide
whether shared spelling replaced a semantic relationship.

## Baseline qualification

`BASELINE` qualifies only when it contains these six exact segments:

```text
{COACH-SPORTS-1 ... COACH-SPORTS-4}
{COACH-VEHICLE-1 ... COACH-VEHICLE-4}
{PITCHER-BALLGAME-1 ... PITCHER-BALLGAME-4}
{PITCHER-CONTAINER-1 ... PITCHER-CONTAINER-4}
{BANK-FINANCIAL-1 ... BANK-FINANCIAL-4}
{BANK-RIVER-1 ... BANK-RIVER-4}
```

Every other returned segment containing two or more positions must be a subset
of one approved subject. Extra same-subject subsegments and singleton segments
are allowed.

If `BASELINE` does not qualify, stop with **baseline recovery failure**. A
system that did not recover the intended subjects cannot show whether the noun
substitutions preserved them.

## Trap verdict

For one trap:

1. Its `PLACEBO`, first-subject-only, and second-subject-only runs must be valid
   and preserve the baseline subject relationships. Otherwise the trap is
   **inconclusive** because ordinary substitution or one isolated use of the
   ambiguous noun already changed the semantic result.
2. If those three controls hold and `BOTH` is valid with the same subject
   relationships, record **pass**.
3. If those three controls hold and `BOTH` is invalid or changes the subject
   relationships, record **both-side-only lexical failure**.

Overall support requires all three traps to pass; do not average them. Report
all shape-only changes and the full segments added or removed.

A both-side-only failure is strong evidence that the simultaneous shared noun
matters in this fixture. It is not universal mechanistic proof: two
individually subthreshold vector shifts could combine across a candidate's
decision boundary.

## Protocol

1. Human-approve and freeze the six propositions, all 72 masks, the 13 arm
   assignments, both output comparisons, and the verdict rules.
2. Freeze the shared SSE contract from [README.md](README.md), the complete
   fine-segmentation candidate, preprocessing, fine-output selector,
   configuration, seed, and one shuffled opaque-ID order. Freeze these before
   rerunning the label-informed lexical gate or inspecting any vectors or
   candidate output.
3. Run and preserve the complete lexical-baseline gate. If it fails, discard
   the fixture without tuning the frozen candidate against the failure.
4. Encode each distinct `B`, `P`, and `C` mask once. Preserve and reuse the
   exact vectors in every applicable collection.
5. Run every collection twice in separate clean processes with the identical
   frozen vectors, opaque-ID order, selector, configuration, and seed.
6. Preserve all 26 raw outputs while identities remain hidden.
7. Canonical outputs from the two identical runs of each collection must
   match. Any mismatch stops the whole experiment as **nondeterministic**; it
   is not a lexical result.
8. Restore fixture identities, qualify `BASELINE`, and apply the three trap
   verdicts.

The fixture is controlled development evidence because its labels are visible
while candidate algorithms may still be developed. If its result changes the
candidate, independent support requires a newly frozen holdout fixture.

## Required record

Preserve:

- every approved proposition and `B`, `P`, and `C` mask;
- tokenizer IDs, selected positions, and piece counts for every mask;
- raw SSE vectors and hashes;
- the lexical representations, similarity matrices, threshold sweep, and
  outputs;
- the candidate implementation, preprocessing, configuration, seed, opaque-ID
   order, and fine-output selector;
- all 26 raw outputs and their complete canonical forms;
- both deterministic-replay comparisons;
- baseline qualification and all three trap verdicts;
- every subject-relationship and complete-output difference;
- raw-vector cosine matrices and matched `B`/`P`/`C` cosine changes.

## Meaning of a result

A pass supports one narrow claim: in these three explicit, proposition-level
traps, sharing one ambiguous noun across two unrelated meanings did not change
the recovered subject relationships after the paired placebo and both
one-sided ambiguous-noun conditions preserved them.

An inconclusive result means those controls did not hold. A both-side-only
lexical failure means only the simultaneous shared-noun condition changed the
semantic result. A baseline recovery failure means the fixture never reached
the state needed to test lexical robustness.
