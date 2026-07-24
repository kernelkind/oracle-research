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

The implementation and isolated run directory are prepared. Read-only
verification reproduced `3,833` candidates, the ordered `40`-note history, and
the exact frozen ceiling. No CREC-109 evaluator session exists yet.

Run artifacts:

`damus_snapshot/runs/crec-109-full-pool-escape-v1`
