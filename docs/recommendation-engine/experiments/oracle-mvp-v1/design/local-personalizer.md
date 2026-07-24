# Instance-Based Local Personalizer

> **Status:** Frozen v1 personalizer design. It is not an approved next-phase
> architecture.

## Purpose

This document records the current direction for the private personalization stage of the recommendation MVP.

The public Oracle operates only on public Nostr data. It exposes two operations over the same frozen kind `1` representation:

```text
similar_notes(note_id, candidate_depth, representation_version)
    -> candidate event IDs, source-specific ranks and scores, and versions

vectors_for_notes(note_ids[], representation_version)
    -> candidate/document vector and representation version for each included event ID
```

The Oracle never receives private judgments, positive or negative labels, a user profile, local scores, or the final ranking. `search_text` is excluded from the MVP. The five initial positive notes are selected manually.

## Decision

Test two instance-based personalizers:

1. **Adaptive compact-support kernel regression.** Nearby rated examples vote on a candidate. Distant examples contribute exactly nothing. The support adapts to the candidate's local similarity neighborhood, and weak evidence shrinks toward neutral.
2. **Zero-mean RBF kernel ridge regression.** A regularized nonlinear function is fitted jointly through the rated examples. It can form disconnected positive and negative regions and returns toward neutral far from evidence.

Both methods keep every rated whole note as an independent example:

- A positive note is weak evidence for nearby content.
- A negative note is weak local counterevidence.
- Repeated nearby agreement strengthens support.
- Nearby positive and negative evidence creates uncertainty.
- Distant and unjudged notes are neutral.

The profile is not collapsed into named interests, a fixed taxonomy, or one user vector. Separate interests emerge from disconnected regions of evidence.

The two algorithm families and their scorers below are approved. Their finite parameter grids, first-round presets, forward-only learning rules, retained diagnostics, shared candidate-construction rules, and direct final-evaluation rule are also frozen below.

### Shared local distance

For every local comparison between normalized candidate/document vectors, calculate squared chord distance directly from the stored FP32 coordinates while accumulating in `f64`:

```text
d2(x, z) = sum_j((f64(x_j) - f64(z_j))^2)
d(x, z) = sqrt(d2(x, z))
```

For normalized vectors this is the same chord geometry as `2 - 2 * dot(x, z)`, but direct differences remain correct at and near zero when the stored FP32 rows are not mathematically unit length. Do not derive local distance through a rounded dot product, introduce an epsilon, or treat a near match as exact. `d2(x, z) = 0` means the finite stored coordinates are numerically equal; `+0` and `-0` are equivalent. This distance definition applies to both personalizers, the `H` and `S` scale derivation, and `B16`. It does not change the Oracle's directional query-to-candidate retrieval score.

### Approved compact-support scorer

For a normalized candidate vector `x` and normalized rated-note vectors `x_i`, attach each note's signed target `y_i = (rating_i - 4) / 3` and use the shared local chord distance `d_i(x) = d(x, x_i)`.

For fixed parameters `(k, H, lambda)`, let the candidate-specific bandwidth be:

```text
h(x) = min(H, distance to the (k + 1)th closest rated note)
```

If fewer than `k + 1` rated notes exist, the second term is infinite and `h(x) = H`. This lets the support shrink in a dense profile region while the hard cap `H` prevents distant examples from being forced to vote. With tricube weights:

```text
w_i(x) = 1                             when d2(x, x_i) = 0
         (1 - (d_i(x) / h(x))^3)^3    when 0 < d_i(x) < h(x)
         0                              otherwise
```

the local score is:

```text
score(x) = sum(w_i(x) * y_i) / (lambda + sum(w_i(x)))
```

`lambda` is positive neutral prior weight. It pulls weakly supported predictions toward `0`. If no rated note has positive kernel weight, the score is exactly `0`. Nearby positive and negative targets can cancel, repeated nearby agreement strengthens the result, and distant evidence contributes exactly nothing.

The first weight case completely defines zero bandwidth: when `h(x) = 0`, every numerically equal stored vector receives weight `1` and every other vector receives weight `0`; the normal score, including `lambda`, is unchanged. Keep distinct rated events as independent observations even when their vectors match. Do not choose an arbitrary tied subset, collapse their judgments, substitute the next positive distance, or impose an epsilon bandwidth.

Use the following finite grid:

```text
k      in {1, 2, 4, 8, 16, 32, infinity}
H      in {H16, H64, H256}
lambda in {0.5, 1, 2}
```

The finite `k` values geometrically span one through 32 possible local voters. `k = infinity` disables density-based bandwidth shrinkage and gives `h(x) = H`, allowing the learning data to reject that assumption. When the available evidence makes multiple `k` values behave identically, retain their predictions but collapse the duplicate calculation.

`lambda` is measured in maximum-strength kernel weight. Its three values therefore act like one-half, one, or two neutral examples. This is enough to compare weak, moderate, and strong shrinkage without creating a large selection search.

The three `H` values are representation-specific distances, not generic cosine thresholds. After the complete normalized candidate/document matrix is frozen, deterministically select `512` public anchors by hashing `(representation_version, event_id)`. For each anchor `a`, exclude itself and use an exact same-role matrix scan to calculate its tricube effective mass:

```text
M_a(H) = sum over j != a of (1 - (d(a, j) / H)^3)^3
         for d(a, j) < H
```

For each target mass `m` in `{16, 64, 256}`, find the smallest radius `h_a(m)` whose effective mass reaches `m`. Define `Hm` as the median `h_a(m)` across the anchors and retain its full-precision chord distance with the `representation_version`. The three factor-four mass levels are a bounded MVP locality grid, not claimed literature optima. This one public diagnostic adds no Oracle operation, index, vector transform, or private input. Any paid execution must have a `$2` hard cap charged to the Oracle MVP's lifetime budget.

The first learning round uses `(k = 1, H = H64, lambda = 1)`. With five deliberately separated seeds, this lets the nearest seed provide bounded support without making unrelated seeds agree: even one exact maximum-strength positive has score `0.5`. Before any recommendation rating is shown, perform only a structural availability check against the five-seed candidate union. If `H64` cannot fill the already-frozen first-round quota and reserve with nonzero support, use `H256`. If `H256` also cannot fill it, stop as an Oracle-personalizer geometry mismatch; do not invent a new radius after seeing judgments.

The Oracle vector space never changes during learning. Before a learning batch's ratings are revealed, every allowed parameter tuple scores the same frozen choices selected by the currently active tuple, using only the five seeds and earlier completed batches. Persist those predictions before presenting the batch.

After each complete adaptive batch is rated, the compact personalizer performs two state transitions in order:

1. Add each selected note's unchanged Oracle vector and signed target to that algorithm's private evidence set.
2. Re-select `(k, H, lambda)` for the next batch from the predictions that were frozen before each completed batch was rated.

For tuple `theta` and completed batch `t`, calculate the mean squared error between that batch's retained pre-rating predictions and its signed targets. Select the tuple with the lowest mean error across all completed batches. Break an exact tie conservatively by preferring smaller `H`, then smaller `k`, then larger `lambda`. After the tenth batch, apply the same rule once more and freeze the result. Final ratings may never select or alter parameters.

This forward-only procedure prevents a later batch from leaking information backward. A batch's ratings influence which notes exist in later batches, so training on later batches to reconstruct an earlier held-out batch would not be a valid prediction test. Inactive tuples are evaluated as scorers on the choices actually encountered; they do not generate counterfactual batches or add evaluator work.

### Retained learning diagnostics

For every learning round and every allowed tuple, retain the evidence-state identity, active tuple, frozen candidate IDs and attribution, pre-rating prediction for each valid choice, revealed signed target, per-batch mean squared error, cumulative mean squared error, and tuple selected for the next round.

After round ten, plot:

- prediction error by round for the active tuple and the best tuple known at that point;
- cumulative prediction error for every tuple; and
- the selected `k`, `H`, and `lambda` across rounds.

Preserve the raw data behind every plot. These diagnostics can show that parameter choice and predictive error stabilized within the fixed `200`-rating learning budget, or that they were still changing when it ended. They cannot prove a global optimum or prove how much another batch would help. They are descriptive and may not change the ten-round stopping rule or the final verdict.

### Approved zero-mean RBF kernel-ridge scorer

For normalized same-role candidate/document vectors and the same signed targets `y_i = (rating_i - 4) / 3`, use the shared squared chord distance and calculate:

```text
K_S(x, z) = exp(-d2(x, z) / (2 * S^2))

K_ij = K_S(x_i, x_j)
alpha = solve(K + rho * I, y)

raw_score(x) = K_S(x, X) * alpha
score(x) = clamp(raw_score(x), -1, 1)
```

The RBF amplitude is fixed at `1`. There is no intercept, target centering, kernel centering, learned mean, or average-rating baseline. This makes unsupported content return toward the neutral score `0`; the five deliberately positive seeds cannot create a positive global baseline for unrelated content. Rating `4` remains an observed target `0`, while an unjudged note is absent rather than manufactured neutral evidence.

Use `K + rho * I`, not `K + n * rho * I`. `rho` is fixed per-rating uncertainty. Adding evidence in one disconnected interest must not weaken an unrelated interest merely because the complete profile grew, while repeated nearby evidence must be able to overcome the fixed regularization.

Keep distinct rated events as separate observations even if their vectors are identical. Their agreement strengthens the local prediction and their disagreement cancels. A repeated event ID is instead a presentation-ledger error. Positive `rho` keeps the system solvable when vectors repeat.

Use this finite grid:

```text
S   in {S16, S64, S256}
rho in {0.25, 1, 4}
```

For one isolated exact example, these `rho` values retain `0.8`, `0.5`, or `0.2` of its target. This spans weak, moderate, and strong shrinkage with only nine tuples.

The `S` values are RBF-specific public distances. Do not reuse the numeric compact-kernel `H` values: tricube influence is zero at `H`, while RBF influence at a distance equal to its scale remains `exp(-1/2)`. Reuse the compact scorer's same `512` deterministic public anchors and exact same-role distance scan, but calculate:

```text
G_a(S) = sum over j != a of exp(-d2(a, j) / (2 * S^2))
```

For each target mass `m` in `{16, 64, 256}`, find the smallest scale `s_a(m)` whose effective RBF mass reaches `m`. Define `Sm` as the median `s_a(m)` across the anchors and retain its full-precision value with the `representation_version`. Derive both the compact and RBF grids in the same bounded diagnostic; together they remain under its single `$2` lifetime-budget cap.

The first RBF learning round uses `(S = S64, rho = 1)`. Before every RBF batch is rated, fit all nine tuples using only the five seeds and earlier completed batches, and persist each tuple's raw and clamped predictions for the same choices selected by the active tuple. After the batch is rated, add its evidence and choose the tuple with the lowest cumulative pre-rating mean squared error calculated from the clamped predictions. An exact tie prefers smaller `S`, then larger `rho`. Re-select after round ten and freeze the result; final ratings never tune it.

Fit and score in `f64`. Build one symmetric kernel matrix with an exact diagonal of `1` and solve the positive-definite system with Cholesky; never form a matrix inverse. A failure with finite inputs and an approved positive `rho` invalidates the run rather than silently adding jitter or changing the model. At no more than `205` evidence notes, the exact solve is negligible.

Use only the clamped posterior-mean score for candidate ordering and forward error. Retain the raw score for audit, but do not use it to break clipped-score ties. Do not add GP variance, an uncertainty or exploration bonus, Oracle retrieval scores, or another learned parameter; those would define a different personalizer.

Measure and retain hubness statistics from the final frozen Oracle vectors, but apply no filtering, downweighting, vector transformation, pause condition, or automatic correction. The statistics are descriptive evidence for interpreting the result and considering later work. They never alter the frozen MVP experiment or its verdict.

## Why Whole-Note Examples

A judgment on one mixed note does not reveal which part caused it. For example:

> I love writing Rust code while sipping a martini on the beach.

One positive judgment does not establish separate preferences for Rust, martinis, and beaches. The complete note remains one weak, ambiguous example. Later overlapping judgments can strengthen or oppose parts of its neighborhood without manufacturing a reason for the original judgment.

## Oracle-Personalizer Interface

Every positive profile note independently calls `similar_notes`. The union of those responses forms the candidate pool, and each response remains attributable to its source note. Negative profile notes do not generate candidates.

For notes rated during adaptive learning, `5`–`7` become positive candidate sources in later rounds, and `1`–`3` provide negative evidence without calling `similar_notes`. A `4` is retained with its unchanged vector and target value `0`. It does not generate candidates, but it acts as local neutral evidence: when it is near a candidate, it pulls that candidate's prediction toward neutral; when it is distant, it has no material effect. Evidence strength remains graded through `(rating - 4) / 3`: positive weights are `1/3`, `2/3`, and `1`, while negative weights are `-1/3`, `-2/3`, and `-1`.

The personalizer calls `vectors_for_notes` for the unique profile notes and candidates whose vectors it has not cached. It compares candidates with positive and negative profile notes locally using those same-role candidate/document vectors. It never needs the complete corpus matrix.

The directional query-to-candidate score returned by `similar_notes` remains source-specific retrieval evidence. It is not treated as a symmetric kernel. Candidate-to-profile kernels use only candidate/document vectors from one `representation_version`. Missing vectors and version mismatches are rejected; vectors from different versions are never mixed. Absence from one bounded `similar_notes` response means unknown similarity, not zero similarity.

The exact Phase 2 Oracle artifact and `representation_version` used for personalizer learning are also frozen for final evaluation.

## Candidate and Batch Construction

Each unique positive profile note calls `similar_notes` once at the fixed depth `1024`. Cache that immutable response by representation version, source event ID, and depth. A later round reuses the response; it does not repeat or deepen the query. Negative and neutral notes never generate candidates. At the start of a learning wave, the runner makes all newly available uncached calls together so the local Oracle can serve them with one exact blocked matrix pass. This is internal scheduling only: every source retains its independent query encoding, ranks, scores, and response.

For each personalizer and round:

1. Form the deduplicated union of that personalizer's positive-source responses, retaining every source attribution.
2. Exclude event IDs disallowed by the presentation rules and fetch any uncached, same-version candidate vectors.
3. Recalculate every remaining candidate's local score from that personalizer's current evidence and active parameters.
4. Keep only candidates with finite scores strictly greater than neutral `0`.
5. Sort by local score descending, breaking an exact tie with a deterministic hash of `(representation_version, event_id)`. Oracle ranks and directional scores do not affect this ordering.
6. Walk that order once, accepting a candidate only when its chord distance from every candidate already accepted into this new list is at least `B16`.
7. Stop after accepting the phase quota plus `21` reserve events, and freeze that bounded order before revealing any rating. This means `41` accepted events per algorithm in a learning round and `221` per algorithm in final evaluation. The required choices come from the front of that order and the unchanged `21`-event suffix supplies replacements for `wrong_language`. Promotion advances through the suffix without querying, rescoring, or reordering.

`B16` is a representation-specific near-duplicate boundary. During the same exact public scan used for `H` and `S`, find each of the `512` deterministic anchors' chord distance to its actual sixteenth-nearest other corpus note. `B16` is the median of those distances, retained at full precision with the representation version. It is separate from `H16` and `S16`, whose weighted-mass meanings are not valid hard-distance boundaries. All three sets of values remain within the diagnostic's single `$2` lifetime-budget cap.

The `B16` check applies only within the newly frozen bounded order. Once the quota plus `21` reserves have been accepted, candidate processing stops; no unused remainder of the candidate pool is diversity-filtered. This prevents paraphrases and one extremely dense semantic neighborhood from wasting a batch without constructing an order that can never be presented. It does not impose topics, source quotas, or equal representation across interests. Semantic proximity to an event shown in an earlier batch does not by itself exclude a candidate; the global event-ID no-repeat rule still applies.

If the fixed candidate pool cannot provide the required positive-scoring, separated choices, the run records a candidate-pool failure. It must not silently deepen retrieval, relax `B16`, or pad the batch with neutral predictions after ratings have begun.

### Shared quota resolution

Each personalizer freezes its bounded accepted order of `41` events during a learning round or `221` events during final evaluation, then initially claims the first `20` or `200`, respectively. Merge the claimed event IDs for presentation, but retain which algorithms claimed each event. An event claimed by both is displayed and rated once, and that one rating counts toward both algorithms' quotas.

When a claimed event receives `wrong_language`, it counts toward neither the affected algorithms' evidence nor their valid-choice quotas. Each affected algorithm advances to the next event in its own already-frozen suffix. Merge and deduplicate those promotions in another blinded presentation wave. Repeat until every algorithm has exactly its required number of valid ratings.

The reserve is `21` per algorithm because adaptive learning and final evaluation can each present at most `400` unique valid notes. Even in the worst case where every language failure is concentrated in one algorithm's order, `21 / 421` remains below the `5%` phase ceiling, while `22 / 422` exceeds it. A phase that would need a twenty-second replacement cannot produce a valid result, so constructing a longer suffix cannot help.

Promotion may inspect event identity, prior presentation state, and whether an event was invalid, but never a revealed rating value. It cannot issue another Oracle query, rescore candidates, reorder the frozen suffix, or update the profile. If the suffix is exhausted before an algorithm fills its quota, the run fails.

During adaptive learning only, an algorithm may claim an event already rated for the other algorithm. Freeze the selecting algorithm's pre-rating predictions first, then route the stored rating without displaying the event again. The rating is added only after the complete round, like every other learning rating. Final evaluation instead excludes the complete presentation ledger and uses only fresh events.

## Benchmark Workflow

### 1. Seed both personalizers

Manually choose exactly five distinct positive note IDs that the evaluator values and that are not all semantically close. Verify that every ID belongs to the frozen Oracle corpus.

Rate each selected seed once with the approved `1`–`7` gladness question and convert it to signed evidence with `(rating - 4) / 3`. A seed must produce positive evidence. Both algorithms receive the same five weighted seeds but maintain independent profile states afterward.

### 2. Run independent adaptive learning paths

Run ten rounds. In each round:

1. Each algorithm independently generates and freezes its first `41` accepted candidates from its current profile, consisting of `20` choices and `21` reserves, and claims its first `20` choices.
2. Resolve both algorithms' valid-rating quotas using the shared presentation and frozen-suffix rules above, hiding algorithm provenance and freezing each presentation wave before it is shown.
3. Rate every unique eligible note once on the approved `1`–`7` gladness scale.
4. Route that rating only to the algorithms that selected the note. If both selected it, both receive the same rating.
5. After the complete merged round is judged, each algorithm converts its own ratings to signed evidence with `(rating - 4) / 3` and updates only its own profile.

An algorithm never learns from a note it did not select. If it later selects a note already rated for the other algorithm, reuse the stored rating for that algorithm without presenting the note again.

After ten rounds, each algorithm has received ratings for `200` of its own adaptive choices. The evaluator rates at most `400` unique eligible learning notes; overlap reduces that number.

### 3. Directly evaluate both frozen personalizers

After the tenth learning round, freeze both algorithms, their independently learned profiles, and their selected parameters. Each generates and freezes its first `221` accepted fresh final candidates, consisting of `200` choices and `21` reserves, and claims its first `200`. Final choices exclude every event presented during seeding or adaptive learning.

Resolve both algorithms' valid-rating quotas using the shared presentation and frozen-suffix rules above. Merge and deduplicate their claims, hide provenance, and rate each unique eligible note once in its frozen shuffled wave. A note claimed by both contributes its one rating to both result sets. Final ratings never update either profile, select an algorithm, or alter a later recommendation.

Calculate each algorithm's result over its own `200` valid choices. That algorithm passes when its mean rating is at least `5` and no more than `20` ratings are `1` or `2`. The MVP passes if either frozen algorithm passes. It fails only when neither passes. Report both outcomes directly; there is no winner-selection phase, confidence interval, or ambiguous quality verdict.

The evaluator rates at most `400` unique eligible final notes. Overlap reduces that number. This is the same worst-case rating count as the rejected design's separate `200`-rating comparison plus a `200`-rating winner-only final, but it tests both complete frozen systems without consuming their strongest recommendations first.

## Presentation Rules

Seed, learning, and final judgments show exactly the raw kind `1` content available to the Oracle. URLs and Nostr identifiers remain visible, but the runner does not open, dereference, preview, render, or follow them. There is no unavailable-context or unjudgeable status. If raw event content cannot be displayed, the run pauses on that note.

A clearly primarily non-English note receives `wrong_language`, no rating, and no profile weight. The runner advances only through the order and suffix frozen before that batch's judgments; it does not issue a replacement query or rerank in response. Mixed-language, code-heavy, and ambiguous notes remain eligible.

Across adaptive learning, `wrong_language` may comprise at most `5%` of all presented notes. The merged final phase has the same `5%` ceiling over unique presentations. Exceeding either ceiling pauses the experiment as a corpus-filter failure and prevents a valid final verdict.

## No-Repeat Rule

Maintain one presentation ledger keyed by event ID across the complete experiment. It starts with the five seeds. Add an event when it is first presented, including an event marked `wrong_language`. Before presenting anything, check the ledger; an event already recorded is never displayed again.

Deduplication changes presentation only. It does not erase algorithm attribution, and a stored rating may be routed to an algorithm that later selects an already judged learning note after its prediction is frozen. Final choices must be fresh and therefore exclude the complete ledger before their orders are frozen. An unused suffix entry is not excluded merely because it appeared in a prior frozen order; it enters the ledger only if presented.

## Shared Personalizer Requirements

- Use positive notes for candidate discovery and negative notes only as local counterevidence.
- Keep every rated note as an independent example.
- Preserve local support, conflict, uncertainty, and disconnected interests.
- Record generic-hub behavior, and prevent near-duplicates or one extremely dense semantic region from filling a batch.
- Do not treat a local score as a calibrated probability unless calibration is separately demonstrated.
- Keep all candidate-to-profile comparisons, profile updates, and final ranking local.

## Evidence

The exact Nostr pipeline has not been proven, but the underlying method is established:

- [A Personal News Agent that Talks, Learns and Explains](https://www.ics.uci.edu/~pazzani/Publications/agents99-news.pdf) stored individually rated news stories and predicted new ratings from a similarity-weighted average of nearby examples.
- [Using Topic Models in Content-Based News Recommender Systems](https://aclanthology.org/W13-5622.pdf) evaluated `10,401` real ratings and found nearest-neighbor regression consistently strong and generally better than the tested linear and Naive Bayes alternatives.
- [Instance-Based Relevance Feedback for Image Retrieval](https://papers.nips.cc/paper_files/paper/2004/file/5acdc9ca5d99ae66afdfe1eea0e3b26b-Paper.pdf) retained relevant and non-relevant examples separately and treated negatives as local counterevidence.
- [Incorporating Relevance Feedback for Information-Seeking Retrieval using Few-Shot Document Re-Ranking](https://aclanthology.org/2022.emnlp-main.614.pdf) found value in retaining per-document dense similarities instead of averaging feedback documents into one prototype.
- [GPR4DUR](https://papers.neurips.cc/paper_files/paper/2024/file/5e28c085a8cd881a4c7e5cf13391aac5-Paper-Conference.pdf) used a zero-mean RBF Gaussian process over fixed item embeddings to represent disconnected interests.
- [ProKeR](https://openaccess.thecvf.com/content/CVPR2025/html/Bendou_ProKeR_A_Kernel_Perspective_on_Few-Shot_Adaptation_of_Large_Vision-Language_CVPR_2025_paper.html) found globally regularized RBF kernel regression stronger than cache-based local adaptation across its tested few-shot tasks.
- [Gaussian Processes for Machine Learning, Chapter 2](https://gaussianprocess.org/gpml/chapters/RW2.pdf) derives the same zero-mean `K + rho I` posterior mean and uses a Cholesky solve rather than an explicit inverse.
- [Bandwidth Selection for Gaussian Kernel Ridge Regression via Jacobian Control](https://arxiv.org/abs/2205.11956) shows that an RBF scale must balance returning too quickly to zero against excessive smoothing and ill-conditioning; it does not supply a universal numeric scale.
- [Ivanov-Regularised Least-Squares Estimators over Large RKHSs](https://jmlr.org/papers/v20/17-672.html) supports clipping a bounded-target kernel regressor to its target range; it does not establish this MVP's recommendation quality.
- [k-NN Regression Adapts to Local Intrinsic Dimension](https://proceedings.neurips.cc/paper_files/paper/2011/hash/05f971b5ec196b8c65b75d2ef8267331-Abstract.html) supports adapting neighbor scale to the local mass around a query; it does not determine this MVP's exact finite grid.
- [Statistical Theory: The Prequential Approach](https://academic.oup.com/jrsssa/article/147/2/278/7106293) motivates evaluating a sequential predictor using only predictions made before each outcome is observed.
- [On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation](https://jmlr.org/papers/v11/cawley10a.html) shows that optimizing a noisy finite-sample selection criterion can itself overfit, supporting a small grid and a separate untouched final evaluation.

These results justify comparing the two approved families. They do not establish that either will produce an actually good personalized Nostr feed.

## Primary Hypothesis

> Can agreement and conflict among whole-note semantic neighborhoods predict which notes this person will value, and does one of the two approved local methods turn that evidence into a consistently valuable feed?

## Deliberately Excluded

- No `search_text` or topic queries.
- No semantic decomposition, extracted interests, generated preference queries, or fixed taxonomy.
- No single global user vector or frontier language-model personalizer.
- No public behavior model or general quality prior in the MVP personalizer.
- No URL dereferencing, linked-note following, or media rendering.
- No use of final ratings to fit, update, or select the personalizer.
- No algorithm or update-rule changes after benchmark ratings begin.
