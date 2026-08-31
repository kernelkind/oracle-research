# Recommendation MVP Rating Analysis

## Purpose

This report analyzes the evaluator's Phase 3 adaptive-learning ratings and the
confirmed-valid prefix of the Phase 4 final evaluation.

It asks:

> What do the recorded ratings reveal about why the tested recommendation
> system failed, and what remains plausible?

This is a companion to the
[`recommendation-mvp-autopsy.md`](recommendation-mvp-autopsy.md). The autopsy owns
the verdict. This report preserves the deeper cross-phase analysis without
changing that verdict or selecting a replacement architecture.

## Evidence Policy

This report distinguishes:

1. **Artifact fact:** directly recorded in the frozen implementation or run
   artifacts.
2. **Evaluator report:** the evaluator's stated experience.
3. **Derived result:** a deterministic calculation from artifact facts.
4. **Exploratory result:** a post-run calculation useful for forming a later
   hypothesis, but not part of the frozen evaluation.
5. **Interpretation:** an explanation consistent with the evidence but not
   established as a cause.
6. **Unknown:** a question the experiment cannot answer.

Interpretations and exploratory results must not be presented as established
causes.

## Data Boundary

### Phase 3

The analysis includes all `356` unique adaptive-learning presentations after
seed selection.

The Phase 3 artifact contains no mechanical-rating pattern comparable to Phase
4's final uninterrupted sequence of `18` ratings of `1`. Its longest
same-rating run is five presentations. This does not prove that fatigue was
absent, but there is no artifact-visible reason to discard a Phase 3 suffix.

Phase 3 was adaptive. A rating changed later evidence and candidate selection,
so its trajectory is descriptive rather than an independent held-out quality
test.

### Phase 4

Quality calculations use only presentations `1` through `140`. The evaluator
independently confirmed that every judgment through `140` was genuine.

Later Phase 4 ratings are excluded from quality estimation because the
evaluator eventually began rating mechanically. They remain valid only as run
history and as the operational marker documented in the autopsy.

## Main Finding

The strongest supported account is narrower than “semantic embeddings failed”:

> The tested system expanded weak positive evidence into persistent semantic
> neighborhoods, produced almost-neutral personalizer scores, and lacked a
> feed-level representation of recent subject exposure.

The evaluator reported repeated subject families. This is consistent with
retrieval finding thematic relation, but the local system did not turn that
relation into a sustained high-value feed.

The data does not isolate how much of the failure came from the embedding,
positive-source discovery, the scoring objective, corpus age, or missing
sequence context.

## Observed Phase 3 Ratings Declined Over Adaptive Rounds

The beginning and end of adaptive learning moved in the wrong direction:

| Phase 3 interval | Unique notes | Mean | Ratings `1`–`2` | Ratings `5`–`7` |
|---|---:|---:|---:|---:|
| Rounds `1`–`3` | `92` | `4.08` | `8` (`8.7%`) | `38` (`41.3%`) |
| Rounds `8`–`10` | `113` | `3.05` | `60` (`53.1%`) | `31` (`27.4%`) |

Per personalizer, comparing its first three and last three batches:

| Personalizer | First-three mean | Last-three mean |
|---|---:|---:|
| Compact | `4.12` | `3.27` |
| RBF | `4.02` | `2.92` |

The decline fluctuated and included temporary rebounds, so it was not
monotonic. Fatigue, saturation, and changing candidate pools varied alongside
learning, so the ratings do not establish that learning caused the decline.
The observed trajectory provides no evidence of improvement.

Across all `356` unique Phase 3 notes:

| Rating | Count |
|---:|---:|
| `1` | `19` |
| `2` | `88` |
| `3` | `78` |
| `4` | `61` |
| `5` | `96` |
| `6` | `11` |
| `7` | `3` |

Only `14` notes, `3.9%`, received a `6` or `7`. Of the `110` positive
ratings, `96` were the weakest positive value, `5`.

### The two personalizers genuinely diverged

The number of shared top-20 assignments by round was:

```text
19, 5, 2, 0, 0, 0, 0, 0, 0, 2
```

The two personalizers therefore selected mostly different notes within the same
rounds while their observed ratings declined similarly. There were also `16`
cross-round selections of an already rated note ID; these reused its stored
rating rather than presenting it again. The result cannot be explained solely
by overlap between the personalizers' contemporaneous note selections, but it
does not identify which shared condition was responsible.

## The Personalizers Did Not Beat Neutral Prediction on Shown Notes

Both personalizers were trained on the signed target:

```text
y = (rating - 4) / 3
```

On their own selected Phase 3 notes, honest forward predictions did not improve
mean squared error over predicting neutral, `y = 0`, for every note:

| Personalizer | Learned Phase 3 MSE | Always-neutral MSE | Prediction/rating correlation |
|---|---:|---:|---:|
| Compact | `0.23280` | `0.22944` | `+0.274` |
| RBF | `0.22750` | `0.22667` | `+0.111` |

This is a selected top-range comparison, not a measurement over every unshown
candidate. It nevertheless shows no predictive-error improvement during
learning.

The final selected parameters were:

- Compact: `k = 1`, `H16`, `lambda = 2`;
- RBF: `S16`, `rho = 4`.

These are the smallest approved semantic scales and strongest approved neutral
shrinkage. Compact's `k = 1` also means its final score used only the nearest
rated example rather than agreement among several examples.

### The final scores were effectively neutral

Among each personalizer's frozen `200` primary recommendations:

| Personalizer | Median score | Maximum score | Implied median rating | Implied maximum rating |
|---|---:|---:|---:|---:|
| Compact | `0.001099` | `0.009260` | `4.003` | `4.028` |
| RBF | `0.000044` | `0.001578` | `4.0001` | `4.0047` |

The implementation excluded scores at or below zero, then filled the
`200`-item primary quota from every score strictly above zero. It therefore
converted almost-neutral estimates into `200` required primary
recommendations per personalizer. The frozen artifacts retained another `21`
accepted candidates per personalizer as reserve.

On the valid Phase 4 prefix, the frozen scores again failed to improve squared
error over always predicting neutral:

| Personalizer | Frozen-score MSE | Always-neutral MSE | Score/rating correlation |
|---|---:|---:|---:|
| Compact | `0.221223` | `0.220779` | `+0.154` |
| RBF | `0.228980` | `0.228956` | `-0.012` |

The scores were used ordinally rather than claimed as calibrated probabilities,
so small magnitude alone does not prove ranking failure. The frozen scores
showed no useful linear predictive relationship in the valid shown prefix.
Their ranking quality over unshown candidates remains unknown.

## Weak Positive Evidence Was Amplified

For each personalizer, each of its own examples rated `5`, `6`, or `7` became a
persistent discovery source. Every source was queried with the same
`1,024`-candidate `similar_notes` limit even though its scorer target was
graded:

```text
5 → +1/3
6 → +2/3
7 → +1
```

At final freeze, the positive sources were:

| Personalizer | All positive sources | Rated `5` | Rated `6` | Rated `7` |
|---|---:|---:|---:|---:|
| Compact | `65` | `57` | `7` | `1` |
| RBF | `72` | `62` | `8` | `2` |

About `87%` of discovery sources were therefore only “slightly glad” evidence.
The scorer downweighted a `5`, but discovery breadth did not.

The candidate unions grew from `5,105` events in the initial shared
seed-driven round. By round 10 of adaptive learning, they reached:

- `27,049` events for Compact;
- `29,243` events for RBF.

After the last ratings were added, the frozen Phase 4 pools contained:

- `27,814` events for Compact;
- `29,809` events for RBF.

More sources and larger pools did not produce improving shown quality.

### Initial retrieval was distinct by note ID but narrow by subject

The five seed queries returned `5,105` distinct events from `5,120` total
result slots. Eight of the ten seed-pair intersections contained no shared
event IDs; the other two contained only six and nine. The initial seed
neighborhoods were therefore not collapsing onto the same notes.

A consistent, case-insensitive surface-form audit across every retrieval stage
found that `3,705` of those `5,105` events, `72.6%`, mentioned Nostr or
Bitcoin/Monero. This is a keyword result, not a semantic classification, but it
shows that distinct retrieval neighborhoods did not imply broad subject
coverage.

By the final freeze:

- `50` of Compact's `65` positive sources, `76.9%`, mentioned Nostr;
- `56` of RBF's `72` positive sources, `77.8%`, mentioned Nostr;
- the union of both final candidate pools contained `42,473` unique events;
- `34,851` of those events, `82.1%`, mentioned Nostr or Bitcoin/Monero.

The two final candidate pools shared `15,150` events, a Jaccard overlap of
`35.7%`. Their broad public reach therefore overlapped substantially, while
their selected primary orders did not: only four event IDs appeared in both
top-`200` orders.

The same audit found different concentration after local selection:

| Frozen primary order | Nostr | Bitcoin/Monero | LLM/AI |
|---|---:|---:|---:|
| Compact | `80.0%` | `3.0%` | `16.5%` |
| RBF | `44.5%` | `35.0%` | `0.5%` |

These categories can overlap. They identify surface concentration, not every
subject or the semantic reason a note was selected.

### Concrete source failures

In RBF's frozen primary order, one of the five original shared seeds, rated
`5`, was the sole recorded source attribution for `66` of `200`
recommendations. It was the sole attribution for `23` of RBF's first `66`
valid Phase 4 recommendations:

- mean rating: `2.57`;
- ratings `1`–`2`: `16`;
- ratings `5`–`7`: `3`.

That one neighborhood contributed two-thirds of RBF's low ratings in the valid
prefix.

Compact was less concentrated. Its largest frozen-primary source was a note
rated `5` in the final adaptive round. It supplied `26` of Compact's `200`
primary recommendations and was the strongest attribution for nine
valid-prefix candidates. Eight were rated `1`–`2`, with a mean of `2.22`.
Because that source entered in the last adaptive round, another adaptive round
never tested its descendants before the order was frozen.

Across Phase 3 primary sources that supplied at least five selected
descendants:

- `12` of `13` Compact sources had downstream mean rating below `4`;
- `13` of `16` RBF sources had downstream mean rating below `4`.

These attributions establish retrieval proximity, not which evidence caused a
score. They nevertheless show that value assigned to a mildly positive source
usually did not transfer smoothly to its selected semantic descendants.

## Repetition Was a Feed-Level Problem

### Phase 3 had geometric repetition across the complete sequence

`B16` prevented close pairs inside each current personalizer order. It was not
historical across adaptive-learning rounds.

Among all `63,190` Phase 3 vector pairs:

- `545` exceeded the cosine-equivalent `B16` boundary of approximately
  `0.7754`;
- `267` were at or above cosine `0.80`.

There was therefore genuine geometric repetition across the complete Phase 3
sequence in addition to the broader thematic repetition the evaluator
reported. This all-pairs count does not isolate how much crossed adaptive
rounds.

### Phase 4 repetition was broader than close-vector duplication

Among the first `140` Phase 4 vectors:

- only `11` of `9,730` pairs reached cosine `0.75`;
- none reached cosine `0.80`.

During frozen-order construction, `B16` recorded only `54` Compact and `32`
RBF rejections as too close to an already accepted candidate. It prevented
close-vector repetition inside each new order; it did not represent subjects
or recent exposure.

The valid prefix came from `114` authors. The most frequent author supplied six
notes, and the five most frequent authors supplied `22` of `140`.

The evaluator's repeated-subject experience therefore cannot be reduced to
exact notes, close vector duplicates, or a few overrepresented authors.

A case-insensitive surface-form keyword audit found:

- `93` notes mentioning Nostr, from `78` authors;
- `28` notes mentioning Bitcoin or Monero, from `27` authors.

The Bitcoin-or-Monero notes averaged `2.79`; `18` were rated `1`–`2`. Twenty
three of the `28` traced to the same positive RBF seed as their strongest or
only source attribution.

This identifies one source-linked Bitcoin-or-Monero-heavy retrieval group
occupying approximately `16%` of the complete valid prefix despite broad
author diversity.

Across consecutive `20`-note blocks of the valid prefix, the Nostr surface-form
audit counted:

```text
15, 12, 13, 10, 16, 13, 14
```

Every block was therefore at least half Nostr-related. The deterministic final
shuffle spread the concentration through the session; ratings during Phase 4
could not change the remaining order.

## Contextual Value Was Stored as Persistent Preference

The following state transition is an artifact fact:

1. The evaluator answered how glad they were to see a note at that moment.
2. The rating became permanent signed evidence.
3. Ratings `5`–`7` also remained persistent discovery sources.
4. Later scores did not receive recent-subject exposure as an input.

The evaluator reported that some subjects were initially welcome and later
became annoying through repeated presentation.

**Interpretation:** A later low rating may have meant “enough of this for now”
rather than “I have a stable dislike of this semantic region.” Persisting both
meanings as the same negative evidence can create contradictory labels around a
subject the evaluator still generally values.

This is consistent with both learned systems moving toward their smallest
scales and strongest neutral shrinkage. The experiment did not manipulate
stable preference and temporary saturation independently, so it cannot prove
that this caused the parameter choices or the failure.

## Corpus Age and Public Content Signals

### Every evaluated note was historical

Across the `356` Phase 3 notes and valid `140` Phase 4 notes:

- creation dates ranged from February 2, 2023 through April 23, 2025;
- at evaluation time, even the newest note was `455` days old;
- median age was `746` days in Phase 3 and `695` days in Phase 4.

Creation time had almost no rank correlation with rating inside this already
stale corpus:

- Phase 3: `+0.065`;
- Phase 4: `-0.009`.

This is consistent with the evaluator's distinction between old evergreen
content and content whose value had expired. These ratings provide no evidence
for a blanket age cutoff.

### Note length was associated with value

Character length had a consistent Spearman rank correlation with rating:

- Phase 3: approximately `+0.400`;
- Phase 4: approximately `+0.407`.

In the valid Phase 4 prefix:

| Note length | Count | Mean rating |
|---|---:|---:|
| At most `100` characters | `14` | `2.86` |
| `101`–`300` characters | `66` | `2.95` |
| `301`–`700` characters | `36` | `3.67` |
| More than `700` characters | `24` | `4.42` |

The association also appeared within the audited Nostr and cryptocurrency
keyword subsets. This does not rule out other topic or composition confounding.

**Interpretation:** For this evaluator, length may proxy for substance, detail,
or idea completeness. The relationship is observational and does not establish
that making a note longer causes value. It could justify validating note length
as a cheap public feature before introducing a more complex quality model.

## Evidence That the Oracle Geometry May Still Contain Useful Signal

The end-to-end system failed, and the frozen Phase 3-trained scores did not
generalize. That does not establish that the Oracle vectors contain no
preference-relevant information.

Within the valid Phase 4 prefix:

- mean high-rating-to-high-rating cosine was `0.441`;
- mean high-rating-to-low-rating cosine was `0.397`.

After inspecting `k = 1, 3, 5, 10, 20`, an exploratory ten-neighbor predictor
using only earlier Phase 4 ratings:

- correlated approximately `+0.48` with later ratings;
- had mean absolute error `0.939`;
- compared with `1.165` for a running-mean baseline.

This was post-run model selection and analysis over already selected Phase 4
notes, so its reported result is optimistic. It was not part of the frozen
experiment, did not evaluate unshown candidates, and is not evidence that this
particular predictor would create a good feed.

It is evidence against the stronger conclusion that the stored geometry has no
local relationship to the evaluator's judgments. One plausible explanation is
that current-context feedback transferred better within the Phase 4 candidate
distribution than the accumulated Phase 3 profile did. That explanation
remains unproven.

## Directly Supported Conclusions

1. Adaptive accumulation did not produce an improving quality trajectory.
2. The two personalizers selected mostly different notes but failed similarly.
3. Neither personalizer improved squared prediction error over an
   always-neutral predictor in Phase 3 or the valid Phase 4 prefix.
4. The final candidate scores were almost neutral, but the positive-score rule
   and primary quota still required `200` recommendations from each
   personalizer.
5. Mild rating-`5` evidence supplied approximately `87%` of all positive
   discovery sources.
6. Some individual rating-`5` source neighborhoods produced many low-rated
   descendants.
7. Exact-note exclusion, close-vector separation, and author diversity did not
   prevent repeated subjects.
8. All evaluated content was historical, but timestamp alone did not separate
   valuable from obsolete content.
9. Longer notes were associated with higher ratings for this evaluator.
10. The experiment does not establish that the Oracle geometry contains no
    preference-relevant signal.
11. The initial and final candidate sets were large and mostly distinct by
    event ID while remaining concentrated in a few surface subject families.
12. Compact and RBF amplified different narrow regions, yet both failed
    similarly.

## Interpretations Worth Preserving

The evidence is consistent with all of the following:

- The system treated “I value this subject” as permission to keep serving it
  without a diminishing return.
- Contextual saturation was stored as permanent preference evidence.
- Equal-depth expansion of weak positives overwhelmed the benefit of graded
  scorer weights.
- Cumulative-MSE selection chose the strongest tested neutral shrinkage, and
  the resulting final predictions were nearly neutral rather than identifying
  a sufficiently large set of high-value feed items.
- Current feed value depends on both a person's stable preferences and what the
  feed has recently shown.
- Public substance and content-dependent freshness may be necessary alongside
  semantic relatedness.

None is established as the sole or primary cause.

## Unknowns

The recorded ratings cannot determine:

- whether unshown candidate pools contained enough excellent notes;
- whether a different ranker could identify those notes;
- whether a current corpus would materially change the result;
- how stable preference and temporary saturation should be represented;
- how broad a semantic region should be before repeated exposure is penalized;
- whether the whole-note vector omitted decisive distinctions;
- whether public quality signals would rescue the approach;
- whether an online personalizer would sustain quality beyond the observed
  prefix;
- which combination of discovery, scoring, and feed construction would satisfy
  the MVP goal.

## Implications for Any Later Experiment

These are analysis implications, not approved architecture decisions:

- A scorer that predicts only neutral values should be allowed to abstain
  instead of being converted into a long required feed.
- A later design should keep stable preference evidence distinct from recent
  feed exposure.
- Discovery-source strength and feed exposure should not be conflated: a note
  can justify exploration without justifying unlimited presentation.
- Semantic-region repetition requires measurement beyond exact IDs, authors,
  and a close-pair threshold.
- Freshness must be content-sensitive rather than a blanket age rule.
- Existing Oracle artifacts and ratings should be reused for local offline
  analysis before paying to rebuild the public representation.
- A later evaluation should stop when every system has become mathematically
  unable to pass.

## Evidence and Method

Primary artifacts:

```text
damus_snapshot/runs/crec-96-phase3-learning-v1/work/phase3-session.json
damus_snapshot/runs/crec-96-phase3-learning-v1/work/seed-selection-handoff.json
damus_snapshot/runs/crec-99-phase4-final-v1/work/phase4-session.json
damus_snapshot/runs/crec-99-phase4-final-v1/work/frozen-orders.json
```

The analysis:

- joined frozen personalizer assignments to durable ratings by event ID;
- reconstructed production Compact and RBF scoring from the frozen vectors and
  approved formulas;
- loaded the exact frozen vectors by ordered representation row;
- reconstructed positive-source attribution from immutable cached
  `similar_notes` responses;
- used a disposable copy of the Phase 4 NostrDB corpus for note timestamps,
  content length, pubkeys, and keyword counts;
- left the frozen experiment and rental artifacts unchanged.

Both surface audits used raw note content without stripping URLs or Nostr
identifiers.

For the retrieval-stage audit, content was matched case-insensitively with word
boundaries:

- **Nostr:** `nostr`, `damus`, `nostrdb`, or `nip` followed by a number, with
  an optional hyphen or space;
- **Bitcoin/Monero:** `bitcoin`, `btc`, `monero`, or `xmr`;
- **LLM/AI:** `llm` or `llms`, `gpt`, `chatgpt`, `claude`, `llama`,
  `artificial intelligence`, `generative ai`, or `ai`.

The combined Nostr-or-Bitcoin/Monero count is the set union of the first two
matches. These rules count visible terms only; they can miss semantically
related notes and include notes that mention a term without being about it.

The earlier valid-prefix audit used Python
`re.search(pattern, content, re.IGNORECASE)` and counted each matching note
once. Its exact patterns were:

```text
Nostr/Damus:      nostr|damus
Bitcoin/Monero:  bitcoin|monero|\bbtc\b|\bxmr\b
LLM/AI:           \bllms?\b|large language|chatgpt|\bgpt(?:-|\s)?\d|#ai\b|deepseek|ollama|deberta|\bcursor\b|ai models?
Alcohol/recovery: alcohol|alcoholic|\bsober\b|sobriety|\brecovery\b|addiction|\bdrinking\b
```

The valid-prefix Nostr/Damus pattern intentionally includes surface forms such
as `nostriches` and Nostr URLs or identifiers. It produced the documented
`93`-note total and the seven consecutive-block counts.
