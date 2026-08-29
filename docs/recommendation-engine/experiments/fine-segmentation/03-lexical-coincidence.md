# Experiment 3: lexical coincidence

Status: **draft; every subject identity and every baseline, placebo, and
collision mask requires human approval before encoding**.

## Assumption

> Lexical coincidences do not substitute for semantic relationships.

## Test

The fixture contains three ambiguous words: `coach`, `pitcher`, and `bank`.
Each word has two unrelated meanings. Each meaning has four independently
worded instances, for 24 vector positions in total.

Every position has three versions:

- **Baseline (`B`)** uses an unambiguous alias.
- **Placebo (`P`)** replaces that alias with a different unambiguous alias.
- **Collision (`C`)** replaces it with the ambiguous word shared by both
  meanings.

Within each trap, baseline repeats one unambiguous alias four times for the
first meaning and a different alias four times for the second. Placebo does the
same with two new unambiguous aliases. Collision preserves that within-subject
repetition but uses the same ambiguous word for both meanings. Shared identity
across the two meanings is therefore the collision's only structural change.
Each alias occurs only at the substituted position; the fixed wording contains
none of that subject's aliases.

Every complete note is also its complete mask. In every position, `B`, `P`,
and `C` differ at exactly one tokenizer position. Every substituted alias is
one piece under the frozen Sentence-T5 tokenizer, so the number of selected
token representations averaged by SSE stays fixed.

## Fixture

The system receives only opaque IDs and vectors. The subject names and the
`B`/`P`/`C` labels are scoring data.

### `COACH-SPORTS`: a swim-team coach correcting freestyle technique

`COACH-SPORTS-1` · 21 pieces in every version

- `B` ⟦The trainer—the swimming squad's stroke specialist—corrected my freestyle technique during practice.⟧
- `P` ⟦The mentor—the swimming squad's stroke specialist—corrected my freestyle technique during practice.⟧
- `C` ⟦The coach—the swimming squad's stroke specialist—corrected my freestyle technique during practice.⟧

`COACH-SPORTS-2` · 29 pieces in every version

- `B` ⟦During pool practice, the trainer—the person teaching our swimmers—showed me how to improve front-crawl form.⟧
- `P` ⟦During pool practice, the mentor—the person teaching our swimmers—showed me how to improve front-crawl form.⟧
- `C` ⟦During pool practice, the coach—the person teaching our swimmers—showed me how to improve front-crawl form.⟧

`COACH-SPORTS-3` · 28 pieces in every version

- `B` ⟦The trainer—the leader responsible for aquatic training—adjusted my arm motion while I rehearsed freestyle.⟧
- `P` ⟦The mentor—the leader responsible for aquatic training—adjusted my arm motion while I rehearsed freestyle.⟧
- `C` ⟦The coach—the leader responsible for aquatic training—adjusted my arm motion while I rehearsed freestyle.⟧

`COACH-SPORTS-4` · 22 pieces in every version

- `B` ⟦I improved my crawl stroke after the trainer—the person guiding the swim squad—fixed my body position.⟧
- `P` ⟦I improved my crawl stroke after the mentor—the person guiding the swim squad—fixed my body position.⟧
- `C` ⟦I improved my crawl stroke after the coach—the person guiding the swim squad—fixed my body position.⟧

### `COACH-VEHICLE`: an intercity passenger coach making an overnight trip

`COACH-VEHICLE-1` · 21 pieces in every version

- `B` ⟦The bus—a long-distance passenger conveyance—took us overnight between two cities.⟧
- `P` ⟦The vehicle—a long-distance passenger conveyance—took us overnight between two cities.⟧
- `C` ⟦The coach—a long-distance passenger conveyance—took us overnight between two cities.⟧

`COACH-VEHICLE-2` · 19 pieces in every version

- `B` ⟦We crossed the region after dark in the bus—a road service built for intercity travelers.⟧
- `P` ⟦We crossed the region after dark in the vehicle—a road service built for intercity travelers.⟧
- `C` ⟦We crossed the region after dark in the coach—a road service built for intercity travelers.⟧

`COACH-VEHICLE-3` · 21 pieces in every version

- `B` ⟦The bus—a motorized means of public travel between distant urban centers—left the terminal near midnight.⟧
- `P` ⟦The vehicle—a motorized means of public travel between distant urban centers—left the terminal near midnight.⟧
- `C` ⟦The coach—a motorized means of public travel between distant urban centers—left the terminal near midnight.⟧

`COACH-VEHICLE-4` · 20 pieces in every version

- `B` ⟦Our bus—a large roadway conveyance for people taking extended journeys—arrived at dawn.⟧
- `P` ⟦Our vehicle—a large roadway conveyance for people taking extended journeys—arrived at dawn.⟧
- `C` ⟦Our coach—a large roadway conveyance for people taking extended journeys—arrived at dawn.⟧

### `PITCHER-BASEBALL`: a baseball pitcher performing in a game

`PITCHER-BASEBALL-1` · 19 pieces in every version

- `B` ⟦The player—the baseball team's opening thrower—struck out nine batters.⟧
- `P` ⟦The athlete—the baseball team's opening thrower—struck out nine batters.⟧
- `C` ⟦The pitcher—the baseball team's opening thrower—struck out nine batters.⟧

`PITCHER-BASEBALL-2` · 27 pieces in every version

- `B` ⟦In the first inning, the player—the person delivering balls from the mound—retired all three hitters.⟧
- `P` ⟦In the first inning, the athlete—the person delivering balls from the mound—retired all three hitters.⟧
- `C` ⟦In the first inning, the pitcher—the person delivering balls from the mound—retired all three hitters.⟧

`PITCHER-BASEBALL-3` · 20 pieces in every version

- `B` ⟦The player—the diamond-sport participant assigned to begin on defense—allowed only two hits.⟧
- `P` ⟦The athlete—the diamond-sport participant assigned to begin on defense—allowed only two hits.⟧
- `C` ⟦The pitcher—the diamond-sport participant assigned to begin on defense—allowed only two hits.⟧

`PITCHER-BASEBALL-4` · 25 pieces in every version

- `B` ⟦After seven frames, the player—the person launching each pitch toward home plate—had recorded ten strikeouts.⟧
- `P` ⟦After seven frames, the athlete—the person launching each pitch toward home plate—had recorded ten strikeouts.⟧
- `C` ⟦After seven frames, the pitcher—the person launching each pitch toward home plate—had recorded ten strikeouts.⟧

### `PITCHER-CONTAINER`: a handled pitcher holding or serving a drink

`PITCHER-CONTAINER-1` · 22 pieces in every version

- `B` ⟦The vessel—a ceramic piece with a handle and pouring spout—held cold water.⟧
- `P` ⟦The container—a ceramic piece with a handle and pouring spout—held cold water.⟧
- `C` ⟦The pitcher—a ceramic piece with a handle and pouring spout—held cold water.⟧

`PITCHER-CONTAINER-2` · 30 pieces in every version

- `B` ⟦She poured lemonade from the vessel—a wide-mouthed receptacle with a grip and pouring lip.⟧
- `P` ⟦She poured lemonade from the container—a wide-mouthed receptacle with a grip and pouring lip.⟧
- `C` ⟦She poured lemonade from the pitcher—a wide-mouthed receptacle with a grip and pouring lip.⟧

`PITCHER-CONTAINER-3` · 28 pieces in every version

- `B` ⟦The vessel—tableware shaped with a handle and spout for serving beverages—was filled with iced tea.⟧
- `P` ⟦The container—tableware shaped with a handle and spout for serving beverages—was filled with iced tea.⟧
- `C` ⟦The pitcher—tableware shaped with a handle and spout for serving beverages—was filled with iced tea.⟧

`PITCHER-CONTAINER-4` · 27 pieces in every version

- `B` ⟦We set the vessel—a ceramic holder whose handle and lip make it suitable for pouring liquids—on the table.⟧
- `P` ⟦We set the container—a ceramic holder whose handle and lip make it suitable for pouring liquids—on the table.⟧
- `C` ⟦We set the pitcher—a ceramic holder whose handle and lip make it suitable for pouring liquids—on the table.⟧

### `BANK-FINANCIAL`: approving a mortgage after reviewing the borrower

`BANK-FINANCIAL-1` · 17 pieces in every version

- `B` ⟦The lender—the regulated organization financing our home purchase—approved the mortgage application.⟧
- `P` ⟦The institution—the regulated organization financing our home purchase—approved the mortgage application.⟧
- `C` ⟦The bank—the regulated organization financing our home purchase—approved the mortgage application.⟧

`BANK-FINANCIAL-2` · 25 pieces in every version

- `B` ⟦After checking our wages, the lender—the business supplying borrowed money for a residence—granted the requested funds.⟧
- `P` ⟦After checking our wages, the institution—the business supplying borrowed money for a residence—granted the requested funds.⟧
- `C` ⟦After checking our wages, the bank—the business supplying borrowed money for a residence—granted the requested funds.⟧

`BANK-FINANCIAL-3` · 22 pieces in every version

- `B` ⟦Our request for credit to buy a house was accepted by the lender—the corporate source of the capital.⟧
- `P` ⟦Our request for credit to buy a house was accepted by the institution—the corporate source of the capital.⟧
- `C` ⟦Our request for credit to buy a house was accepted by the bank—the corporate source of the capital.⟧

`BANK-FINANCIAL-4` · 21 pieces in every version

- `B` ⟦The lender—the financial organization funding the property acquisition—authorized our housing loan after reviewing repayment history.⟧
- `P` ⟦The institution—the financial organization funding the property acquisition—authorized our housing loan after reviewing repayment history.⟧
- `C` ⟦The bank—the financial organization funding the property acquisition—authorized our housing loan after reviewing repayment history.⟧

### `BANK-RIVER`: river-edge soil eroding after a storm

`BANK-RIVER-1` · 24 pieces in every version

- `B` ⟦After the storm, the shore—the strip of ground next to the river—lost soil to rushing water.⟧
- `P` ⟦After the storm, the edge—the strip of ground next to the river—lost soil to rushing water.⟧
- `C` ⟦After the storm, the bank—the strip of ground next to the river—lost soil to rushing water.⟧

`BANK-RIVER-2` · 19 pieces in every version

- `B` ⟦Floodwater washed earth from the shore—the sloped terrain adjoining the stream.⟧
- `P` ⟦Floodwater washed earth from the edge—the sloped terrain adjoining the stream.⟧
- `C` ⟦Floodwater washed earth from the bank—the sloped terrain adjoining the stream.⟧

`BANK-RIVER-3` · 24 pieces in every version

- `B` ⟦As the channel rose, erosion cut into the shore—the soil separating a watercourse from a field.⟧
- `P` ⟦As the channel rose, erosion cut into the edge—the soil separating a watercourse from a field.⟧
- `C` ⟦As the channel rose, erosion cut into the bank—the soil separating a watercourse from a field.⟧

`BANK-RIVER-4` · 27 pieces in every version

- `B` ⟦Heavy rain caused the shore—the land following the course of flowing freshwater—to crumble into the swollen current.⟧
- `P` ⟦Heavy rain caused the edge—the land following the course of flowing freshwater—to crumble into the swollen current.⟧
- `C` ⟦Heavy rain caused the bank—the land following the course of flowing freshwater—to crumble into the swollen current.⟧

## Seven collections

Run the candidate on these seven 24-vector collections:

| Collection | Versions used |
|---|---|
| `BASELINE` | `B` at all 24 positions |
| `COACH-PLACEBO` | `P` for the eight `COACH` positions; `B` elsewhere |
| `COACH-COLLISION` | `C` for the eight `COACH` positions; `B` elsewhere |
| `PITCHER-PLACEBO` | `P` for the eight `PITCHER` positions; `B` elsewhere |
| `PITCHER-COLLISION` | `C` for the eight `PITCHER` positions; `B` elsewhere |
| `BANK-PLACEBO` | `P` for the eight `BANK` positions; `B` elsewhere |
| `BANK-COLLISION` | `C` for the eight `BANK` positions; `B` elsewhere |

Corresponding positions keep the same opaque ID, input order, configuration,
and seed in every collection. Only the eight stated vectors change.

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

For each representation, sweep every distinct pairwise-similarity threshold
plus the no-edge boundary above the largest similarity. At one fixed threshold
for all seven collections, connect two positions when their similarity meets
or exceeds the threshold and return the connected components. The fixture
fails this gate if any representation and threshold qualifies `BASELINE` and
returns the same complete components in all six variants.

This is intentionally favorable to the lexical baselines: their best threshold
is selected after seeing the fixture. The gate does not prove that no possible
lexical method could pass. It rejects a fixture that is already solvable by
three obvious lexical shortcuts.

If the fixture fails this gate, redesign and reapprove it before any SSE run.

The exact draft fixture above has passed a design-time preflight. Exact-token
Jaccard had no threshold that recovered the six baseline subjects. Word and
character TF-IDF each recovered the baseline at some thresholds, but no
threshold preserved those groups across all six variants. The executable
experiment must rerun and preserve the gate rather than treating this
preflight as its result.

## Complete-output comparison

Canonicalize each candidate output without discarding information:

1. sort the member IDs inside each returned segment;
2. sort the complete list of segments, retaining overlaps, singleton segments,
   and duplicate segments;
3. derive and sort the IDs that occur in no returned segment.

Segment IDs and output order are ignored because they carry no meaning. An
empty segment, an unknown ID, or a repeated member inside one segment makes the
output invalid.

### Baseline qualification

`BASELINE` qualifies only when its complete output contains these six exact
four-position segments:

```text
{COACH-SPORTS-1 ... COACH-SPORTS-4}
{COACH-VEHICLE-1 ... COACH-VEHICLE-4}
{PITCHER-BASEBALL-1 ... PITCHER-BASEBALL-4}
{PITCHER-CONTAINER-1 ... PITCHER-CONTAINER-4}
{BANK-FINANCIAL-1 ... BANK-FINANCIAL-4}
{BANK-RIVER-1 ... BANK-RIVER-4}
```

Every other returned segment containing two or more positions must be a subset
of exactly one declared subject. Extra same-subject subsegments and singleton
segments are allowed. The six exact segments necessarily assign every
position.

If `BASELINE` does not qualify, the experiment stops with **baseline recovery
failure**. A system that did not first recover the intended subjects cannot
show whether the substitutions preserved them.

### Trap verdict

For each trap, compare the complete canonical outputs:

- If its placebo output is invalid or differs from `BASELINE`, record
  **inconclusive**. An ordinary matched alias substitution already changed the
  result.
- If its placebo output equals `BASELINE` and its collision output also equals
  `BASELINE`, record **pass**.
- If its placebo output equals `BASELINE` but its collision output is invalid
  or differs, record **lexical-collision failure**.

Overall support requires all three traps to pass. Do not average them.

For diagnosis, list the multiset of segment member sets added or removed. For
each position, also compare the multiset of returned member sets containing
it. This remains well-defined when segments overlap or repeat. Distinguish a
new cross-meaning segment from lost or changed same-subject recovery, but both
are lexical-collision failures because the shared alias was the collision's
only structural change. Pairwise together/apart relations and cosine changes
are diagnostics only; they do not replace the complete-output verdict.

## Protocol

1. Obtain human approval of all six subject identities and all 72 masks.
2. Run and preserve the complete lexical-baseline gate.
3. Freeze this document, the shared SSE contract from [README.md](README.md),
   and the complete fine-segmentation candidate.
4. Encode each distinct `B`, `P`, and `C` mask once. Preserve the exact input,
   tokenizer positions, raw vector bytes, and hashes.
5. Assign one frozen shuffled order of 24 opaque position IDs.
6. Run the seven collections in separate clean processes with the same
   configuration and seed.
7. Preserve all seven raw outputs before restoring fixture identities or
   calculating a verdict.
8. Qualify `BASELINE`, then apply the three trap verdicts.

## Required record

Preserve:

- every approved subject identity and mask;
- tokenizer IDs, selected positions, and piece counts for every mask;
- raw SSE vectors and hashes;
- the lexical representations, similarity matrices, threshold sweep, and
  outputs;
- the candidate implementation, preprocessing, configuration, seed, input
  order, and fine-output selector;
- all seven raw and canonical candidate outputs;
- the baseline qualification and three trap verdicts;
- all complete-output and assignment differences;
- the raw-vector cosine matrices and matched `B`/`P`/`C` cosine changes.

## Meaning of a result

A pass supports one narrow claim: in these three common-word traps, replacing
unambiguous aliases with one shared ambiguous word did not change recovered
fine segments, even though matched unambiguous substitutions also did not
change them.

An inconclusive result means ordinary alias replacement was not controlled. A
lexical-collision failure means the shared ambiguous word changed the complete
output after that control held. A baseline recovery failure means this fixture
never reached the state needed to test lexical robustness.
