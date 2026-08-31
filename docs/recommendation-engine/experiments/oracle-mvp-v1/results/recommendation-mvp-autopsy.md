# Recommendation MVP Autopsy

## Evidence Policy

This report separates five kinds of statement:

1. **Artifact fact:** directly recorded in the frozen implementation or run
   artifacts.
2. **Evaluator report:** the evaluator's recollection of what they experienced.
3. **Derived result:** a deterministic calculation from artifact facts and the
   evaluator-confirmed validity boundary.
4. **Interpretation:** an explanation consistent with the evidence but not
   established by this experiment.
5. **Unknown:** a question the experiment cannot answer.

Only artifact facts, evaluator reports, and derived results support the MVP
verdict. Interpretations must not be treated as established causes.

## Deeper Rating Analysis

The
[`recommendation-mvp-rating-analysis.md`](recommendation-mvp-rating-analysis.md)
preserves the full cross-phase analysis of Phase 3 and the confirmed-valid
Phase 4 prefix.

Its strongest additional finding is that the observed adaptive-learning
trajectory did not improve: both personalizers ended with almost-neutral
predictions, while weak positive sources could still expand into large,
persistent neighborhoods. The ratings also distinguish thematic repetition
from repeated note IDs or authors and show a plausible mismatch between
contextual “glad I saw this now” feedback and permanent preference evidence.

These findings deepen the failure analysis. They do not change the frozen
verdict, establish one primary cause, or select a replacement architecture.

## Result

**Derived result:** The exact Oracle-plus-personalizer system tested on the
frozen historical corpus failed its frozen MVP criterion.

RBF became unable to pass at global presentation `120`. Compact became unable
to pass at presentation `130`. The evaluator confirmed that all judgments
through presentation `140` were genuine. The result was therefore fixed before
the evaluator later began rating mechanically.

The result establishes only:

> This exact system, using this corpus, profile-building process, two frozen
> personalizers, candidate construction, and feed construction, did not produce
> an actually good general feed for this evaluator.

It does not identify the primary cause of failure and does not establish that
semantic retrieval, every possible local personalizer, or private and
decentralized recommendation is infeasible.

## Experiment Definition

The following are artifact facts.

The frozen experiment used:

- The `3,530,455`-note GTE-Qwen2-7B-Instruct Oracle representation derived from
  the April 2025 Damus snapshot.
- Lazy `similar_notes` retrieval from positive profile notes.
- Same-version candidate/document vectors supplied to the local personalizers.
- Five manually selected positive seeds.
- Ten adaptive-learning rounds giving each personalizer `200` ratings.
- Two independently learned local personalizers:
  - adaptive Compact kernel regression;
  - zero-mean RBF kernel ridge regression.
- A final frozen order of `200` recommendations per personalizer.

Four recommendations appeared in both final orders. The `400` personalizer
claims therefore became `396` unique presentations. One rating for an overlap
was routed to both personalizers.

A personalizer passed only if:

- its mean over `200` valid final ratings was at least `5`; and
- no more than `20` ratings were `1` or `2`.

The MVP passed if either personalizer passed.

## Validity Boundary

**Evaluator report:** Every judgment through presentation `140` was genuine.
The evaluator read each note and chose the rating that matched their reaction.
Annoyance from already having seen too much similar material was part of that
genuine reaction.

**Evaluator report:** Later in the run, the evaluator became exhausted and
eventually began assigning ratings mechanically. The evaluator did not identify
an exact first mechanically rated presentation.

**Artifact fact:** The final `18` stored judgments were all `1`.

**Conclusion about use of the data:** The report uses the first `140`
presentations for the verdict because the evaluator independently confirmed
that boundary. It does not select a different cutoff from the observed rating
curve. Ratings after `140` remain preserved as run history but are not used for
an unbiased estimate of exact quality or to compare Compact with RBF.

### Operational marker for absolute fatigue

The final uninterrupted sequence of `18` ratings of `1` is used as the
artifact-visible marker for absolute fatigue. This does not claim that fatigue
began at that point. It marks when mechanical rating became unambiguous in the
stored decisions.

The count requested from immediately after the five-seed profile was populated
is:

| Interval | Unique presentations |
|---|---:|
| Phase 3 adaptive learning after seed selection | `356` |
| Phase 4 before the uninterrupted `1` sequence | `339` |
| Total before the sequence | `695` |

**Derived result:** The first rating in the uninterrupted `18`-rating sequence
was the evaluator's `696th` unique presentation after seed selection. The
sequence covered post-seed presentations `696` through `713`.

**Artifact fact:** Within Phase 4 itself, the sequence began at presentation
`340` and continued through the pause after presentation `357`.

The separate seed-selection process had presented `72` notes before the
five-seed profile was complete. Those notes are excluded from the requested
post-seed count. Including them, the first rating in the uninterrupted sequence
was the evaluator's `768th` presentation across seed selection, adaptive
learning, and final evaluation.

## Recorded Run Facts

### Stopped state

The run stopped cleanly after `357` of `396` unique presentations:

- `357` durable ratings;
- no `wrong_language` outcomes;
- no repeated note IDs;
- no pending presentation;
- `39` presentations remaining.

The runner did not produce its normal terminal report because neither
personalizer reached `200` valid ratings.

### Irreversible failure

| Personalizer | Global presentation | Its ratings at that point | Ratings of `1`–`2` |
|---|---:|---:|---:|
| RBF | `120` | `56` | `21` |
| Compact | `130` | `70` | `21` |

**Derived result:** Once the count of ratings `1`–`2` reached `21`, that
personalizer could no longer satisfy the maximum of `20`. Future ratings could
not reduce the count. This makes the failure deterministic rather than a
statistical early-stopping inference.

At the recorded break after presentation `140`:

| Personalizer | Ratings received | Mean | Ratings of `1`–`2` |
|---|---:|---:|---:|
| Compact | `77` | `3.34` | `24` |
| RBF | `66` | `3.42` | `24` |

Both had already become unable to pass.

### First 130 presentations

The first `130` unique presentations had a combined mean of `3.42`:

| Rating | Count |
|---:|---:|
| `1` | `5` |
| `2` | `38` |
| `3` | `24` |
| `4` | `25` |
| `5` | `37` |
| `6` | `1` |
| `7` | `0` |

**Artifact fact:** `38` notes received ratings of `5`–`7`, while `43` received
ratings of `1`–`2`. Of the positive ratings, `37` were `5`, one was `6`, and
none was `7`.

**Limited conclusion:** The end-to-end pipeline surfaced some notes the
evaluator was glad to see. These counts do not isolate whether the Oracle
candidate pool or the personalizer was responsible.

### Personalizer scores

Within the first `130` presentations, Pearson correlation between deployed
score and rating was:

- Compact: approximately `+0.13`;
- RBF: approximately `-0.01`.

Their early means were also similar:

- Compact: `3.41`;
- RBF: `3.42`.

**Limited conclusion:** Within the recommendations that were selected and
shown, neither deployed score had a strong linear relationship with the
contextual rating. This calculation does not measure unselected candidates and
does not identify why the relationship was weak.

At the end of adaptive learning, the selected parameters were:

- Compact: `k = 1`, `H16`, `lambda = 2`;
- RBF: `S16`, `rho = 4`.

These were each personalizer's smallest approved semantic scale and strongest
approved neutral shrinkage. That selection is an artifact fact. Any explanation
of what it says about the representation or preferences is an interpretation.

### Vector spacing and source attribution

For the first `130` presented vectors:

- median pairwise cosine similarity was `0.419`;
- the `95th` percentile was `0.638`;
- `10` of `8,385` pairs were at or above `0.75`;
- no pair was at or above `0.80`.

One positive source was attributed to `22` of RBF's first `62` rated
candidates, approximately `35%`. Compact's largest source was attributed to
`9` of its first `70`, approximately `13%`.

These numbers describe vector spacing and source attribution. They do not by
themselves measure subject diversity or prove what caused the evaluator's
experience.

### Time inputs

The corpus snapshot was from April 2025. The evaluation occurred in July 2026,
approximately fifteen months later.

The corpus could not contain material published after its snapshot. The
approved Compact and RBF scores used vectors and ratings; they did not use note
timestamps, the evaluation date, or the state of an external discussion. The
approved final order did not change during presentation.

These are system facts. Whether a current corpus or time-aware scoring would
have changed the verdict was not tested.

## Evaluator-Reported Observations

These are first-person observations, not conclusions derived from the
artifacts.

### Repeated subjects

The evaluator reported that the feed repeatedly concentrated on:

- generic praise of Nostr;
- Bitcoin;
- Monero;
- LLMs;
- alcohol recovery.

The evaluator has some interest in each of these subjects but did not want
hundreds of notes about almost nothing else. The evaluator reported that this
repetition was the main reason the run became exhausting.

The repetition was thematic, not a claim that exact notes were repeated.

### Temporally obsolete content

The evaluator reported that much of the content felt too old to remain
interesting. Examples included:

- LLM discussions whose state of the art had moved well beyond the note;
- NIP proposal discussions that had already concluded;
- announcements whose referenced real-world occurrence had already passed.

The evaluator did not claim that all old content was unwanted. The reported
problem was content whose practical value had changed because technology had
advanced, a discussion had concluded, or a referenced occurrence had passed.

### Other value judgments

Across the evaluation work, the evaluator also reported encountering notes that
were uninteresting or expressed ideas they considered poor. These observations
show that topical relation alone did not guarantee a positive judgment. They do
not establish which representation or algorithmic component failed.

## Failure Localization

The full measurements are preserved in the
[`recommendation-mvp-rating-analysis.md`](recommendation-mvp-rating-analysis.md).
The following separates the observed state transitions from their
interpretation.

### Derived pipeline facts

1. **Seed retrieval:** The five seed queries returned `5,105` distinct events
   from `5,120` result slots, with almost no event-ID overlap between seed
   pairs. A retrieval-stage surface-form audit nevertheless classified `72.6%`
   of the initial union as mentioning Nostr or Bitcoin/Monero.
2. **Adaptive discovery:** Every note rated `5`–`7` became a discovery source
   with the same `1,024`-candidate retrieval limit. About `87%` of the final
   discovery sources were rated only `5`.
3. **Final candidate pools:** Compact and RBF together reached `42,473` unique
   events. The same retrieval-stage audit classified `82.1%` as mentioning
   Nostr or Bitcoin/Monero.
4. **Local selection:** Compact and RBF shared only four event IDs in their
   primary `200`-note orders. Compact's order was `80.0%` Nostr and `16.5%`
   LLM/AI by the audit; RBF's was `44.5%` Nostr and `35.0%`
   Bitcoin/Monero.
5. **Individual amplification:** One original rating-`5` seed solely supplied
   `66` of RBF's `200` primary recommendations. One rating-`5` note added in
   Compact's final adaptive round supplied `26` of Compact's `200`.
6. **Feed construction:** Phase 4 removed repeated event IDs and shuffled the
   two frozen orders. It had no input representing recently shown subjects and
   could not change after later ratings. Every consecutive `20`-note block in
   the valid prefix was at least half Nostr-related under the separate
   valid-prefix audit.
7. **Freshness:** Every valid-prefix note was between approximately `500` and
   `1,092` days old. Creation time had almost no rank correlation with rating
   inside that already historical range.

The keyword categories above are surface-form measurements. They do not
identify every subject or substitute for human semantic judgment.

### Localization boundary

Concentration was observable in the initial retrieval union, changed
differently under the two personalizers, and remained present throughout the
frozen feed. The historical corpus separately bounded currentness. This traces
where the observed conditions entered or persisted; it does not establish
independent causal failures at every stage. One upstream limitation could have
produced downstream symptoms.

The final shuffle distributed already selected groups through the session.
`B16` filtered close vectors, but close-vector diversity did not prevent the
reported thematic repetition.

The causal hypotheses and unresolved questions remain separated below. In
particular, most unshown candidates were never rated. The analysis therefore
does not justify rebuilding the Oracle representation or establish that
changing only the local ranker would be sufficient.

## Directly Supported Conclusions

The following conclusions require no causal assumption beyond the recorded
facts and evaluator-confirmed validity boundary.

1. Neither Compact nor RBF could satisfy the frozen MVP rule.
2. The exact end-to-end system failed on the frozen April 2025 corpus.
3. Exact note-ID no-repeat did not prevent the evaluator from experiencing
   repeated subjects.
4. Low close-pair counts under the stored-vector geometry did not prevent the
   evaluator from experiencing repeated subjects.
5. The deployed scores showed little linear association with the shown
   contextual ratings in the valid early prefix.
6. The historical corpus could not offer newer material that was absent from
   the snapshot.
7. Continuing after presentation `130` could not change the pass/fail result.

These statements do not prove why the system failed.

## Interpretations Consistent With the Evidence

The following are hypotheses for later investigation. The experiment did not
compare them, manipulate them independently, or estimate their causal effects.

### Sequence-insensitive scoring may have contributed to subject saturation

The personalizers scored candidates independently of recently presented
subjects, and the final order was frozen before presentation. It is plausible
that a note's static relevance remained positive even after similar material
had become tiresome.

This could explain why evidence of some interest behaved like evidence for an
unbounded quantity of that subject. The experiment did not test a
sequence-aware alternative, so it cannot establish that adding one would be
sufficient.

### Positive-source discovery may have concentrated exploration

Only positive notes called `similar_notes`. Negative and neutral notes affected
local scores but did not generate candidates. It is plausible that:

- the five seeds constrained initially reached regions;
- later positive ratings expanded regions already reached;
- adaptively selected learning examples covered less of the evaluator's
  preferences than `200` independent examples would have.

The source-attribution concentration for RBF is consistent with this
possibility. It does not prove that this mechanism caused the repeated subjects,
especially because Compact had lower source concentration and similar ratings.

### Temporal mismatch may have reduced achievable quality

A fifteen-month-old snapshot necessarily omitted current material. Static
semantic relatedness also does not by itself establish that a technical
discussion remains current or unresolved.

It is plausible that a current corpus and time-aware eligibility or scoring
would improve results for fast-changing subjects. The experiment did not
measure the size of that improvement and cannot establish that it would rescue
the system.

### Whole-note semantic distance may omit distinctions needed for value

The weak score-to-rating relationships are consistent with personal value not
being sufficiently smooth in the stored whole-note geometry. They are also
consistent with subject saturation, temporal obsolescence, incomplete profile
coverage, candidate-pool limitations, or interactions among them.

The experiment cannot select among these explanations.

## Unknowns

The experiment does not answer:

- Whether the unranked Oracle candidate pools contained enough highly valuable
  notes.
- Whether a different local ranker could identify valuable candidates already
  present.
- Whether one whole-note vector preserved the distinctions needed to predict
  value.
- Whether the adaptive profile covered enough of the evaluator's interests.
- How much of the outcome came from subject saturation.
- How much came from temporally obsolete content.
- How the same approach would perform on a current, continuously refreshed
  corpus.
- Whether time-aware eligibility or scoring would materially improve results.
- Whether sequence-aware feed construction would materially improve results.
- Whether public quality or other supplementary signals would materially
  improve results.
- Whether another private and decentralized architecture can produce an
  actually good feed.

No single failure location should be asserted from this run.

## Evaluation-Protocol Finding

**Artifact fact:** RBF could no longer pass after presentation `120`, Compact
could no longer pass after `130`, and the runner continued until the evaluator
paused after `357`.

**Derived result:** The `227` judgments after presentation `130` had no ability
to change the frozen verdict.

**Evaluator report:** Repeated subjects were the main source of exhaustion.

**Interpretation:** Continuing after the result was fixed increased the amount
of evaluator work. The experiment did not quantify how much that additional
work, rather than the repetitive feed itself, contributed to exhaustion.

Any future evaluation with a monotonic rule should define a deterministic stop
when every remaining system has become unable to pass. This is a protocol
recommendation, not an explanation of the recommendation failure.

## Decisions

- Do not resume the remaining `39` presentations.
- Preserve the stopped session and every frozen input unchanged.
- Record a conclusive failure of this exact configuration on this historical
  corpus.
- Do not use the mechanically rated tail as an unbiased per-note quality
  estimate.
- Do not lower or reinterpret the frozen pass threshold after observing the
  result.
- Preserve the complete Oracle artifact for any later analysis.

No new architecture is selected by this autopsy.

## Evidence

The stopped final-evaluation artifacts are under:

```text
damus_snapshot/runs/crec-99-phase4-final-v1/
```

The durable decision record is:

```text
damus_snapshot/runs/crec-99-phase4-final-v1/work/phase4-session.json
```

The frozen orders, scores, attributions, and candidate vectors are:

```text
damus_snapshot/runs/crec-99-phase4-final-v1/work/frozen-orders.json
```

The confirmed-valid prefix ends at presentation `140`. Figures from later
presentations are descriptive only and are not necessary for the verdict.
