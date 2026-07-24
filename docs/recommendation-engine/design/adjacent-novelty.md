# Adjacent-Novelty Design Direction

## Status

This is an approved working direction, not a complete architecture or an
approved experiment. Exact thresholds and algorithms remain undecided. Oracle
MVP v1 remains frozen.

## Why

V1 repeatedly presented the same broad themes. Its discovery transition was:

> Every positive rating from 5 through 7 opens another 1,024-note semantic
> neighborhood.

Most discovery sources were only weak positives rated 5. This let already
concentrated regions repeatedly replenish themselves. The next design must
escape exhausted regions without treating arbitrary dissimilarity as useful
discovery.

Corpus freshness is a separate problem. It does not explain or solve the
reinforcement loop.

## Approved Direction

Adjacent novelty is a feedback-gated walk through semantic space:

1. Keep stable preference evidence separate from temporary recent exposure.
2. Every shown note updates recent exposure, regardless of its rating.
3. Require every candidate to retain meaningful positive personal support
   after considering positive, neutral, and negative evidence.
4. Prefer supported candidates outside recently exhausted regions.
5. Occasionally present a more distant, but still supported, candidate as a
   bounded probe.
6. Only a probe rated 5 through 7 may call `similar_notes` and open its adjacent
   region. A rating from 1 through 4 stops expansion.
7. Newly retrieved neighbors receive no guaranteed feed positions. Each must
   qualify independently.
8. If no probe qualifies, return no probe rather than force unrelated content.

## Probe Qualification

A candidate qualifies as an underexposed adjacent probe only when all of these
conditions hold:

### Adjacent

The candidate is an unseen result from `similar_notes` for a note rated 5
through 7. It is reachable from positive evidence, not sampled randomly from
the corpus.

### Supported

The personalizer predicts meaningful positive value after considering all
retained evidence. Merely having a score above zero is insufficient. The
support floor should correspond to approximately a rating of 5, but its exact
calculation and threshold have not been chosen.

### Underexposed

Accumulated similarity to all recently shown notes is below an exposure
budget. Every shown note contributes, regardless of its rating, so many
moderately related presentations can exhaust a region. This must measure a
broader region than exact or near-duplicate suppression.

### Controlled

The candidate has not already opened a neighborhood, and a bounded probe
position is available.

After these gates, selection should prefer stronger support and lower recent
exposure. It should not select the most distant candidate, collapse the gates
into one relevance-versus-novelty score, or give probes unrestricted feed
positions.

## Probe State Transition

After a probe is shown:

- Always add it to the shown ledger and temporary exposure state.
- Rating 5 through 7: retain graded positive evidence and allow one
  `similar_notes` expansion.
- Rating 4: retain neutral evidence and do not expand.
- Rating 1 through 3: retain graded negative evidence and do not expand.
- Never expand the same shown note twice.

## Unknowns

- The exposure similarity function, its semantic scale or scales, and its
  budget.
- The support calculation and minimum support floor.
- The number and placement of bounded probe positions.
- Whether and how temporary exposure decays or rebounds.
- Whether the Oracle vectors preserve the broad themes people experience as
  repetitive.
- How to avoid interpreting a low rating caused by temporary saturation as a
  permanent dislike.
- How disconnected interests can be discovered when they are unreachable from
  current positive evidence.

Freshness, public quality signals, and stale source data remain separate
problems.

## Research Basis

The direction combines established ideas without claiming that the complete
design has already been validated:

- [Maximal Marginal Relevance](https://aclanthology.org/X98-1025/) constrains
  novelty by relevance rather than rewarding arbitrary distance.
- [Diversified news recommendation](https://proceedings.neurips.cc/paper/2011/hash/33ebd5b07dc7e407752fe773eed20635-Abstract.html)
  models diminishing value from repeated coverage.
- [Safe exploration](https://proceedings.mlr.press/v37/sui15.html) motivates a
  minimum predicted-value boundary before exploration.
- [FRec](https://arxiv.org/abs/2405.11764) treats repeated exposure as
  cumulative rather than only suppressing exact duplicates.
- [Rebounding Bandits](https://arxiv.org/abs/2011.06741) separates stable
  preference from temporary satiation.

These works support the components. They do not establish that the Oracle
embedding, the unchosen thresholds, or this combined loop will work for Nostr.
