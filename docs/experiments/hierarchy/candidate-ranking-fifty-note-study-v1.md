# Candidate ranking on the historical fifty-note hierarchy

For a shorter explanation of the selection process and cost calculation, see
[Candidate selection: savings and how the method works](candidate-selection-savings-and-method-v1.md).

**Historical research only.** The original ASv6.48 subjects and all derived
meanings, vectors, comparisons and hierarchy data are deprecated. The approved
baseline is ASv6.100. These results diagnose the requested saved construction;
they do not validate the current pipeline or approve a policy change.

The most promising result is a learned ranking using several SSE representations
of immutable meanings. Without canonical graph features, it reproduced every
saved construction step with 2,049 comparisons instead of 2,682. Its conditional
known API-equivalent total is $7.540058 instead of $9.1301216: **17.42% less**.
This is offline replay, not a new inference run or realized subscription savings.
Chronologically trained alternatives did not preserve the whole construction.
Keep the production shortlist unchanged until independent current-data validation.

## What was measured

The frozen source is `oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/`
`hierarchy-b96-c48-fifty-note-v1/menu-access-children-01/state.json`, SHA256
`fd3e5b8e3831a7952dc66de0686a1383c3fb1e9ff07dcbbc1fdb275740cc22f8`.
It has 181 processed local entries: 146 additions, 16 equivalences and 19 holds.
There are 177 native comparison steps and 2,682 valid saved comparisons. Its
user-reviewed finished menu has 76 nodes, six roots and at most six choices per
group. Every displayed edge narrows its distinct-note set; all fifty notes are
reachable. Saved positive judgments are not independently reviewed semantic gold.

The study calls the original production receipt readers, placement function,
settled-answer contradiction checks and complete implication verification.
No teacher/provider calls, prompt edits, graph writes or UI refresh occurred.
The comparison prompts remain Bootstrap-v96 / Compare-v48, Sol 6.1 medium.

Two checks are separate:

1. **Frozen snapshots:** rerank each original sixteen-candidate pool and check
   its resulting placement against the original before-graph and full original
   prior answer history. This is a cheap screen, not a reachable new build.
2. **Exact construction replay:** previous steps retain only answers the new
   selection actually requested or independently verified. Stop at the first
   changed graph or unobserved required answer. Later original inputs cannot be
   reused after a graph change.

A complete replay reproduces all meanings, supports, parent relationships and
holds. The original menu recipe therefore remains available on the unchanged
final graph. This establishes preservation of that saved result, including its
existing semantic qualifications; it does not establish general correctness.

## Why the original ranking misses useful candidates

The original ranking alternates heading-only SSE cosine and lexical TF-IDF.
SSE takes the maximum match across the selected heading and its original local
ancestor headings. Canonical headings are encoded alone. Lexical matching uses
headings and meanings. The mapped canonical parent remains first.

- **Breakfast:** Meals C013 is an eating-occasion topic; Meals C015 concerns meal
  food. Their heading vectors are identical. C015 ranks ninth in the original
  combined nomination, while Homegrown food gets a lexical boost from an
  incidental breakfast example. The learned full-feature scorer moves C015 to
  fifth among all eligible nodes. Both Meals nodes remain distinct candidates.
- **Yogurt making:** Food C008 and Dairy products C049 rank ninth and twelfth.
  Contextual SSE and graph-neighborhood scoring move them earlier; the learned
  full-feature ranks are second and fourth. Both are saved positive comparisons.
- **Hunger:** Mental states C010 ranks seventeenth and was never compared.
  Some alternative scores move it earlier. Its relationship remains unknown;
  neither a new rank nor a similar meaning makes it a verified parent.

These examples distinguish finding a likely useful comparison from deciding
containment. All learned scores remain nomination signals, never graph edges.
The query is the selected local entry's independently generated meaning, not an
undifferentiated embedding of its whole post and every topic in that post.

## Representations and controlled methods

The ordinary SSE worker encoded 181 unique heading/meaning pairs into 547 rows,
including four bare-heading replay controls. Every new control matches its
original subject vector to cosine at least 0.999999 and maximum normalized error
at most 0.00001. Checkpoint, model tree, pooling and dimension identity match.
Preparation hashes the original state, corpus, source code and worker settings;
the worker receipt must identify that exact preparation and request.

For each pair, the study uses:

- the existing standalone heading **subject vector**;
- a standalone explicit-meaning encoding;
- the heading span encoded in `heading + newline + meaning`;
- the meaning span encoded in that same text.

The latter three are auxiliary SSE representations. They are not MP masks,
mask vectors, new SP entries or changed node definitions. The worker performs
two new text encodings per unique pair and pools three spans. Canonical meanings
are immutable, so these representations can be reused without encoding growing
branches on every comparison.

The initial screen covers sixteen ranking methods at limits 8, 12 and 16:
heading/meaning/contextual cosine, fixed mixtures, lexical definition matching,
same-heading coverage, graph-neighborhood scores, multi-view late interaction,
density correction and a learned relationship-likelihood score.

Graph-neighborhood scoring gives a candidate the maximum score among itself and
its recursive descendants. It can nominate a broad parent through a nearby
specific topic, but can also give many broad nodes the same high score.

Multi-view late interaction takes each query view's best cosine against the
candidate's views and averages those best matches. This follows the independent
encoding/cheap interaction idea in [ColBERT](https://arxiv.org/abs/2004.12832),
but is not ColBERT or its trained token-level representation.

The density correction is `2 * contextual_cosine - mean_neighbor_cosine`, using
up to ten other current canonical vectors. It is a one-space adaptation of
[CSLS](https://arxiv.org/abs/1710.04087), not a replication of its cross-language
procedure. In this experiment it suppresses useful broad topics: at Yogurt
making, Food moves from original rank nine to density-corrected rank twenty-two.

The learned score is ridge logistic regression, penalty 10. Its target is any
saved containment/equivalence versus `neither`; uncertain answers are excluded.
Features include semantic and lexical similarities, optional canonical graph
counts/neighborhood scores, and separate query/candidate, difference and product
features from a fixed 16-dimensional projection of contextual meaning vectors.
These separate query/candidate features allow more than symmetric closeness.
[Order embeddings](https://arxiv.org/abs/1511.06361) motivate distinguishing
hierarchical relationships from symmetric similarity; this study does not train
an order embedding or derive containment from vector coordinates.

Forty notes form development data and ten are held out by deterministic note-ID
hash. Development predictions exclude their own note fold; test predictions use
the forty-note model. The initial winner is selected on development only.
The later blends/ablations are exploratory responses to observed failures, not a
new untouched test set. This small food-heavy corpus is not a deployment benchmark.

## Results

All methods below retain original eligibility, mapped-parent priority, fixed
meanings and implication verification. Reranking stays inside the original
sixteen-candidate pool, so it cannot prove recovery of unqueried relationships.

| Method | Snapshot comparisons | Matching snapshots / 177 | Exact replay: entries matched / 181 |
|---|---:|---:|---:|
| Original sixteen | 2,682 | 177 | 181 |
| Original first twelve | 2,047 | 169 | 75 |
| Contextual descendant maximum, eight | 1,392 | 173 | 82 |
| Full learned score, twelve | 2,046 | 177 | 180 |
| Learned score without canonical graph features, twelve | 2,049 | 177 | 181 |
| Original twelve union learned eight | 2,231 | 177 | 181 |
| Learned scalar similarities/counts only, twelve | 2,046 | 177 | 180 |
| Learned score without meaning-vector features, twelve | 2,046 | 176 | 179 |
| Learned similarities only, twelve | 2,047 | 176 | 155 |

The winning ablation removes canonical ancestor/descendant/support counts and
descendant-max similarities. It retains original local ancestor-heading matching,
meaning/contextual SSE, lexical features and projected meaning interactions.
Graph information remains available to the unchanged teacher and graph guards.

### Why positive recall is insufficient

The full learned score appears perfect in frozen snapshots but fails the last
exact-replay step. At entry 137, it omits Eating practices versus Gamey meat,
whose saved answer is `neither`. At entry 180, Meat eating links Eating practices
above Gamey meat. The original graph holds this contradiction; replay without
the earlier negative admits it. The three fixed-meaning claims cannot all hold.

The original rank of that critical negative is ten, while the full learned rank
is twenty-six among all eligible nodes. Thus prediction of positive relationships
can discard a valuable future guard. The original-twelve/learned-eight blend
retains both this negative and lower-ranked positives. The no-graph learned
ablation also preserves the complete history outcome. These are measured results,
not a general guarantee that either strategy always retains important negatives.

### Chronological transfer did not pass

A model trained only on the first fifty entries, then frozen, loses Food
preparation at Half-and-half (entry 121). Its blended version first loses
Processed food at leftover chicken pizza (entry 153). A semantic-only frozen
version diverges at entry 93. Adding a small graph stream does not fix the pizza
case. These differ from the corpus-wide, note-held-out screen.

Two further replays refit before each entry using only previously requested
answers, retaining all original comparisons for the first fifty entries.
Both the full-feature and semantic-only original-twelve/learned-eight variants
first diverge at Bread (entry 75), omitting Processed food. No later original
inputs are used for either replay. Updating the model alone does not establish
safe transfer. A current-data validation must explicitly cover newly introduced
broad topics, equivalence placements and future contradiction witnesses.

## API-equivalent cost, not just call count

The complete no-graph learned replay retains 2,033 initial and 16 verification
comparisons, a **23.60% case reduction**. Native receipt accounting includes its
three retained comparison failures; their usage is unknown. All original meaning
generation and warmup overhead is retained in the projection.

| Cost component | Original known subtotal | Retained comparison projection |
|---|---:|---:|
| Comparison requests, all priced token types | $7.5723448 | $5.9822812 |
| Original meaning + warmup overhead | $1.5577768 | $1.5577768 |
| Total known API-equivalent subtotal | $9.1301216 | $7.5400580 |

The **17.42% total reduction** uses saved uncached input, cached input, output
and cache-write prices. Reported cache writes are zero. Reasoning is included
in output and is not charged twice. Retained comparison token reductions are
20.52% uncached input, 23.16% cached input and 21.46% output. Seven original
failures lack usage, so complete totals remain unknown. Original cache behavior
may differ after dispatching fewer requests; these are conditional saved-token
projections, not measured new-run costs. Reusing historical answers neither
refunds their original cost nor proves this reduction on an unseen hierarchy.

## Scale and recommended next step

The reusable code is [vector preparation](../../../sse_multivector/canonical_ranking_vectors.py) and the
[offline study](../../../sse_multivector/candidate_ranking_study.py). Source and request hashes are checked
before original native receipts can be reused. The worker is the existing SSE
implementation; the experiment runner and production ranking are unchanged.

The expensive teacher work is replaced only by nomination scores: one model
embedding per reusable representation, then small vector operations. Three
additional float32 vectors per canonical node require about 9.2 KB before indexes. The
current all-candidate and descendant scans are bounded diagnostic code, not a
large-corpus index. A deployment would use indexed semantic nominations and
bounded graph expansion; exhaustive descendant rescoring at every query is not
the proposed scalable implementation. Training and encoding costs also need
measurement before claiming end-to-end latency savings.

 Do not deploy the historical weights.
Measure candidate recovery, settled-negative preservation, full guarded replay
and all-in cost together. Do not lower the production cap or replace teacher
judgments based on this historical result alone.

Ignored artifacts are retained in the research worktree under
`target/candidate-ranking-study-v1/`: `meaning-vectors`, `ranking-screen-v3.json`,
`prefix-and-cost-v2.json`, `prefix-and-cost-v3.json`, `ablation-v1.json`,
`causal-semantic-v1.json` and `online-v1.json`. Earlier failed import logs remain
as evidence. The worktree is retained because the worker's frozen inputs and
receipt refer to its exact source/configuration paths. No inference was spent.

Final verification is `final-verification-v3.json`, with both original sixteen
and the no-graph learned method replaying all 181 entries. During verification,
another task edited the reference project's subject-vector reader. The native
source check correctly refused that changed file. An ignored, hash-exact copy
of the original committed reader was mounted over its original path in a private
read-only filesystem view for verification; the other task's working file was
untouched. Original receipts, frozen states and hashes were not rewritten.
The archived reader SHA256 is
`9a8efa8a0db07a9dd92d577bb65b41c18fef28cc88a43e984a78cfcf7b73b552`.
Unit/worker checks pass: 24 tests with no skips in the existing encoder environment.
