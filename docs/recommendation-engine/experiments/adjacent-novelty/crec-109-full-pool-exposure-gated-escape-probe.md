# CREC-109: Full-Pool Exposure-Gated Escape Probe

## Question

Can the frozen candidate pool escape an exhausted semantic region while
remaining connected to demonstrated preferences?

This tests one selection transition. It does not update personalization,
retrieve new neighborhoods, test corpus freshness, or evaluate a complete
recommendation loop.

## Frozen Inputs

- The frozen Compact-positive order of `3,833` candidates.
- The exact `40` CREC-108 presentations, in their original order, as the
  starting exposure history.
- All events shown before or during CREC-108 are excluded.
- CREC-108's completed session, report, and reconstructed input identities are
  bound into the new session.

## Selection

For candidate `c`, each prior shown note `i` contributes:

`max(0, cosine(c, i) - 0.42087467246166055) × 2^(-age/20)`

The exposure ceiling is `0.32686638460886658`. It was selected from the 40
CREC-108 repetition answers by:

1. enumerating midpoints between adjacent distinct observed exposure scores;
2. predicting `repetition=yes` when exposure is at or above a midpoint;
3. maximizing balanced accuracy; and
4. choosing the higher midpoint on an exact tie.

This calibration classified the source answers as `TP=20`, `FN=1`, `TN=12`,
and `FP=7`. These are in-sample calibration facts, not validation results.

At each step:

1. scan every remaining candidate;
2. reject exposure at or above the ceiling;
3. select the first survivor in frozen Compact support order; and
4. add every shown note to exposure history, regardless of its answers.

Ratings and repetition answers cannot change the profile, support order,
candidate pool, or later selections. There is no fallback when no candidate
survives.

## Evaluation

- At most `20` valid 1–7 ratings.
- One mandatory rest after `10` valid ratings.
- The same broad-subject repetition question follows every valid rating.
- One wrong-language replacement is reserved; a second wrong-language
  presentation terminates with a separate diagnostic outcome.
- No event may be presented twice.

Interpret each rated note as:

- rating `5–7` and repetition `no`: successful escape;
- rating `1–4` and repetition `no`: thematic escape with low personal value;
- repetition `yes` despite passing the gate: exposure proxy or ceiling
  failure.

If no candidate is below the ceiling, the result is that the frozen pool
cannot sustain this escape transition. The ceiling must not be relaxed.

## Status

Completed and deterministically verified.

Run artifacts:

`damus_snapshot/runs/crec-109-full-pool-escape-v1`

## Results

### Verified facts

- Termination: valid-rating quota reached.
- Presentations: `20`, all with valid ratings and distinct event IDs.
- Wrong-language presentations: `0`.
- The mandatory rest after rating `10` was completed.
- Rating `2`: `4` notes; rating `3`: `5`; rating `4`: `4`; rating
  `5`: `7`. None were rated `1`, `6`, or `7`.
- Mean rating: `3.70`; median rating: `4`.
- Broad-subject repetition: `13 no`, `7 yes`.
- Successful escape (`5–7` and `no`): `6/20`.
- Thematic escape with low personal value (`1–4` and `no`): `7/20`.
- Exposure-proxy or ceiling failure (`yes`): `7/20`. One was rated `5`.

All selected exposures were strictly below the frozen ceiling. The selector
completed without fallback, candidate exhaustion, profile updates, or Oracle
inference.

The eligible supply was thin:

- Before the first selection, `98` of `3,570` remaining candidates survived.
- After the fourth presentation, only `20` survived.
- Thereafter, the survivor count ranged from `9` to `20`.
- Selected frozen-support ranks ranged from `306` to `2,155`, with median
  `1,083`.
- Frozen support fell from `0.0005054492` on the first selection to
  `0.0000092420` on the last.

Within this selected, below-ceiling sample, exposure only weakly ordered the
live repetition answers: its descriptive yes/no AUC was `0.593` (`54/91`
ordered yes/no pairs). This is selection-truncated and is not a global
validation score. One repetition-`yes` note had exposure `0.111`, while four of
the six successful escapes had higher exposure. Lowering the scalar ceiling
enough to reject that note would therefore also reject most observed
successes.

### Content observations

A separate content review grouped the selected notes into two dominant broad
families:

- `7` Nostr or Damus notes;
- `7` health, self-improvement, or generic motivation notes.

All seven repetition-`yes` answers occurred within those two families. The
gate escaped part of the earlier concentration, but much of the resulting feed
remained concentrated or formed a new concentration.

Topic alone did not determine value. A concrete fitness story and a Nostr
engineering note were both rated `5/no` despite other notes from their broad
families feeling repetitive. Genericity, angle, and substance therefore
affected the judgment in ways a hard subject cap would miss.

### Interpretation

The narrow existence hypothesis received positive evidence: the frozen pool
contained six notes that were both mildly valuable and not experienced as
another overexposed broad subject.

The mechanism was not reliable enough to constitute a good feed:

- `14/20` notes missed the joint success condition;
- `7/20` still felt repetitive despite passing the vector gate;
- no note was rated clearly or exceptionally valuable (`6–7`);
- preserving the hard ceiling required reaching far down the frozen support
  order.

This is partial evidence that vector exposure can help escape a semantic
region. It is also evidence that one scalar whole-note exposure gate is too
coarse to prevent thematic jail while preserving valuable angles within broad
subjects. Merely lowering the ceiling is not supported by the observed score
ordering.

No aggregate pass/fail threshold was frozen before the run, so this experiment
must not be retrospectively labeled a global pass or failure. Comparisons with
CREC-108 are descriptive only because the selection conditions differed.
