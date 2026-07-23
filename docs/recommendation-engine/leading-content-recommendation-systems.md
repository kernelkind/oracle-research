# Leading Content Recommendation Systems

Research cutoff: 2026-07-10.

## Executive Summary

There is no defensible public leaderboard for content recommenders. The systems
operate on different catalogs, interfaces, feedback loops, and business goals;
none exposes a common online evaluation set; and recommendations change the data
on which they are later evaluated. This report therefore uses "best" to mean the
best-documented frontier systems: large deployed recommenders with strong
technical disclosure, controlled online evidence, or an unusually auditable
implementation.

Across the selected systems, recurring techniques include the following; no
system publicly demonstrates every layer:

1. several independent candidate generators with different coverage properties;
2. a staged funnel that spends more computation as the candidate set shrinks;
3. user state at long-term, session, and request timescales;
4. collaborative, graph, ID, text, audio, image, and context representations;
5. separate predictions for multiple positive and negative outcomes;
6. rewards aligned to satisfaction or long-term value rather than raw clicks;
7. explicit correction for exposure, position, sampling, and train/serve bias;
8. deliberate exploration, diversity, freshness, and creator-distribution logic;
9. eligibility, safety, and quality controls outside the relevance model; and
10. randomized online evaluation plus operational controls for freshness,
    calibration, latency, and representation versioning.

The most important conclusion is that candidate discovery and objective design
set the quality ceiling. A powerful final ranker cannot recover relevant content
that retrieval omitted, and an accurate model of the wrong reward makes the
wrong feed more efficiently.

## Method and Evidence Labels

The systems were selected for scale, product success, architectural distinctness,
and availability of primary sources. Commerce recommenders were excluded unless
the disclosed technique directly powered a content surface. Systems with no
current primary technical disclosure were not reverse-engineered from marketing
advice or third-party speculation.

Claims use these evidence levels:

- **Production**: a primary source explicitly says the system is deployed or
  serving traffic.
- **Online experiment**: a controlled production test is reported, but permanent
  or universal rollout is not assumed.
- **Historical production**: a deployed architecture is useful evidence but is
  not assumed to remain current.
- **Research**: a company paper or prototype does not establish deployment on a
  named surface.
- **Inference**: a causal explanation synthesized from disclosed behavior rather
  than directly established by an experiment.

Reported lifts are not comparable across companies. Metric definitions, traffic
populations, experiment duration, and baselines differ.

## Systems Selected

| System | Why it belongs in the comparison | Distinctive strength | Main evidence limit |
| --- | --- | --- | --- |
| YouTube Home, Watch Next, and Shorts | Mature video recommendation with the latest disclosed production long-term slate optimization and historical production studies | Incremental long-term satisfaction plus historical exposure-correction and content-retrieval evidence | The full 2026 stack is not public; the 2016/2019 components are historical precedents |
| TikTok For You and separately disclosed ByteDance systems | Large short-video product with current product-level recommendation disclosures | Dense sequential feedback and deliberate novelty; related ByteDance systems disclose learned retrieval and minute-level sparse updates | TikTok's exact models and online results are undisclosed; ByteDance and BytePlus results are not TikTok evidence |
| Netflix Home | Strongest public work on whole-page recommendation and long-horizon subscription value | Generative page construction, shared preference models, and long-term reward engineering | Current corpus retrieval remains only partly disclosed |
| Spotify Home, radio, search, and podcast discovery | Strong public evidence for discovery, multi-content calibration, and delayed value | Reusable user representations, contextual bandits, and long-horizon policies | Different surfaces use different stacks |
| Pinterest Home Feed, Related Pins, and Search | Most complete current disclosure of a visual recommendation funnel | Graph and multimodal retrieval, plural interests, lifelong sequences, and list diversity | Several production models coexist; exact traffic allocation is private |
| Meta Instagram Explore and Facebook Reels | Extremely large multi-surface fleet with current retrieval and satisfaction work | Learned early-funnel intelligence, multimodal understanding, and survey alignment | There is no single "Meta algorithm"; surface attribution is often withheld |
| X For You | Most auditable current social-feed implementation | Open two-tower retrieval plus a sequential multi-action ranker | No current quality or retention lift is published |
| LinkedIn Feed | Current end-to-end disclosure with strong online results in a trust-sensitive domain | LLM retrieval, sequential ranking, professional graph features, and ecosystem objectives | Connected and out-of-network retrieval remain separate |

## 1. YouTube

### Latest disclosed production shape: long-term slate ranking

YouTube's latest public production description is not the 2016 watch-time DNN. The
2024 [Learned Ranking Function paper](https://arxiv.org/abs/2408.06512)
describes a production pipeline with candidate generation, multitask behavior
prediction, learned slate ranking, and a final re-ranking stage.

The Learned Ranking Function, or LRF, contributes several important techniques:

- It models a recommendation panel as a cascade. At each position a viewer can
  click, skip, or abandon the panel, so value depends on both the item and the
  position-dependent continuation state.
- It estimates the value the viewer would receive after abandoning the panel.
  The learned ranking score combines click and abandonment probabilities with
  each video's predicted future-reward lift over that baseline, so the slate is
  credited for incremental platform-wide value rather than value the viewer
  would have obtained elsewhere anyway.
- Separate small networks estimate abandonment reward, click-conditioned lift,
  and click probability. This preserves interpretable subproblems while learning
  their slate-level combination.
- Training is on-policy Monte Carlo learning from a recent FIFO trajectory
  buffer. Small traffic slices run experimental policies, and occasional random
  promotion to the first position supplies identifiable exploration data.
- Dynamic linear scalarization updates weights using offline evaluation on
  randomized exploration candidates to target stable secondary-objective
  tradeoffs while optimizing the primary objective.

The initial LRF improved YouTube's long-term satisfaction metric by 0.21% over
the production heuristic. Adding the cascade click model added 0.66%. Removing
the incremental-lift formulation improved local Watch reward but regressed the
platform-wide metric by 0.46%, unusually direct evidence that local engagement
is not the same objective as incremental value. The system launched on Watch and
then Home and Shorts.

### Retrieval and coverage

The 2019 historical-production Neural Deep Retrieval system used a two-tower
model over the current video, watch history, context, and video content
features. Dot products made tens-of-millions-scale retrieval practical. Its
critical improvement was not merely using embeddings: it corrected in-batch
logits with streaming frequency estimates because ordinary batches oversample
popular videos. This reduces sampling bias that would otherwise conflate
observed item frequency with relevance and adapts as the corpus changes.
Frequency-corrected NDR improved online engagement 0.37%, versus 0.20% for
uncorrected NDR. See
[Sampling-Bias-Corrected Neural Modeling for Large Corpus Item Recommendations](https://research.google/pubs/sampling-bias-corrected-neural-modeling-for-large-corpus-item-recommendations/).

Content-aware item towers matter for fresh and tail videos because semantic
features exist before co-watch statistics do. An earlier research demo
[content-based related-video system](https://research.google/pubs/content-based-related-video-recommendations/)
learned visual embeddings from collaborative co-watch targets, using behavior
to define useful semantic similarity while retaining a cold-start path.

The landmark 2016
[Deep Neural Networks for YouTube Recommendations](https://research.google/pubs/deep-neural-networks-for-youtube-recommendations/)
remains useful historical production evidence:

- next-watch retrieval was extreme multiclass classification followed by
  approximate maximum-inner-product search;
- training included watches discovered outside recommendations, importing
  exogenous discoveries instead of learning only from the recommender's own
  exposures;
- per-user example caps stopped heavy users from dominating;
- histories were rolled back to predict a future watch, avoiding leakage caused
  by random holdouts;
- example age modeled freshness; and
- the final ranker used watch-time-weighted logistic regression rather than CTR,
  reducing clickbait incentives.

These are precedents, not a claim that the 2016 model remains YouTube's complete
current architecture.

### Multiple objectives and feedback bias

In a 2019 historical-production Watch Next study, the system predicted click,
watch duration, likes, dismissals, and ratings. Multi-gate Mixture-of-Experts
allowed related tasks to share capacity while letting conflicting tasks select
different experts. The eight-expert MMoE at 6.1M multiplications reported
+0.45% engagement and +3.07% satisfaction relative to the 3.7M shared-bottom
reference. The equal-compute 6.1M shared-bottom reported +0.10% and +1.89%, so
the quoted MMoE lifts are not direct deltas against the equal-cost model. See
[Recommending What Video to Watch Next: A Multitask Ranking System](https://research.google/pubs/recommending-what-video-to-watch-next-a-multitask-ranking-system/).

A shallow position tower learned position crossed with device during training;
at serving, the position feature was treated as missing rather than the tower
being removed. This was designed to separate item utility from exposure
propensity and reported +0.24% engagement. Adding position as an ordinary
feature reported -0.07%.

YouTube also reported historical production deployment of policy-gradient
retrieval with:

- a learned approximation of historical behavior policies;
- capped importance weights for off-policy correction;
- top-K correction so the policy retains probability mass across several good
  slate candidates; and
- Boltzmann exploration within a high-probability ANN-retrieved subset rather
  than uniform epsilon-greedy exploration over the entire corpus.

Against the standard off-policy baseline, top-K correction reported +0.85%
ViewTime and a -0.16% change in videos viewed. See
[Top-K Off-Policy Correction for a REINFORCE Recommender System](https://research.google/pubs/top-k-off-policy-correction-for-a-reinforce-recommender-system/).

### Satisfaction, diversity, and safety

YouTube's 2021 product explanation lists clicks, watch time, survey responses,
sharing, likes, and dislikes as distinct signals. "Valued watchtime" is derived
from sparse one-to-five-star surveys, and only time on videos rated four or five
stars counts toward it. A model imputes responses for other views, and held-out
survey responses continuously test that model. Signal weights vary by viewer
rather than following one universal formula. See
[On YouTube's recommendation system](https://blog.youtube/inside-youtube/on-youtubes-recommendation-system/).

This is a strong success mechanism: sparse intentional judgments supervise a
model that scales beyond the surveyed impressions, while abundant behavior
still supplies personalized state.

Diversity and responsibility remain separate controls. Historical YouTube
production work used a determinantal point process to combine item quality with
pairwise dissimilarity at the set level. Current LRF documentation still places
diversity in re-ranking, but does not establish that the old DPP remains live.
The same 2021 explanation says human and expert judgments train
authoritativeness and borderline-content classifiers; those signals can
override engagement for news and information.

### Why YouTube succeeds

**Inference:** YouTube's disclosed advantage is alignment through the entire funnel:
content-aware, bias-corrected retrieval supplies broad candidates; multitask
models preserve different meanings of behavior; explicit exploration makes
counterfactual learning possible; survey-imputed satisfaction improves the
reward; and cascade/lift ranking optimizes incremental long-term value of the
slate rather than a locally attractive click.

## 2. TikTok and ByteDance

### What TikTok actually discloses

TikTok's current Help Center describes an outer pipeline:

eligible corpus -> personalized interest prediction -> ranked feed -> diversity
and safety controls.

See [How TikTok recommends content](https://support.tiktok.com/en/using-tiktok/exploring-videos/how-tiktok-recommends-content)
and the current
[For You eligibility standards](https://www.tiktok.com/community-guidelines/en/fyf-standards/).

Documented For You inputs include:

- full watches, time spent, skips, likes, shares, comments, follows, and searches;
- sounds, hashtags, view count, publication country, and other video data;
- language, location, device, time zone, and time context; and
- behavior of people with similar interests.

For most users, TikTok says interaction signals, including time spent, are
generally weighted more heavily than content and user-information factors. The
stronger completion-versus-country comparison appears only in TikTok's June
2020 explanation. New users can select interests; otherwise TikTok starts with
broadly suitable popular content conditioned on location and language. Initial
interactions begin reshaping the feed, but TikTok does not publish an adaptation
rate.

TikTok also documents deliberate out-of-interest recommendations, avoidance of
already-seen and repetitive material, promotion of recent and local content,
explicit "Not Interested" controls, topic/keyword controls, and interruption of
repeated sensitive themes. Relevant sources include
[Making your feed For You](https://www.tiktok.com/safety/en/making-your-feed-for-you)
and its
[recommendation diversity update](https://newsroom.tiktok.com/an-update-on-our-work-to-safeguard-and-diversify-recommendations?lang=en).

**Inference:** the full-screen one-item interface produces a dense sequence of
completion, dwell, replay, and skip events. Coupled with intentional
out-of-interest insertions, this could make sequence feedback easier to
attribute than in a multi-item viewport; TikTok publishes no comparative
adaptation-rate experiment.

### Safety is corpus eligibility, not merely a score

TikTok removes policy violations, excludes content that is permitted but not
suitable for broad recommendation, applies age-specific Content Levels, reviews
rapidly rising posts again, and limits repeated exposure to individually
eligible but cumulatively risky topics. Separating eligibility from predicted
interest prevents an engagement model from trading safety against a larger
relevance score.

### ByteDance Deep Retrieval

TikTok does not publish its model architecture. The strongest related primary
evidence is ByteDance's 2021
[Deep Retrieval](https://arxiv.org/abs/2007.07203) deployment on an unnamed
short-video platform. It must not be attributed to TikTok.

Deep Retrieval learns the retrieval structure and user objective together
instead of learning Euclidean embeddings and attaching a separately optimized
ANN index:

- each video maps to one or more paths through a learned layered discrete
  structure;
- multiple paths represent different aspects of one video;
- a path-size regularizer prevents collapse into a few popular buckets;
- EM-style updates alternate neural learning with item-path assignment;
- streaming score decay responds to changing interest;
- beam search retrieves sublinearly; and
- a jointly trained reranker separates items sharing a path.

Against FFM embeddings plus HNSW, the unnamed production test reported +3.0%
finish rate, +0.87% app view time, and +0.036% second-day retention. The authors
also reported more exposure for less-popular creators. The likely contribution
is alignment between the retrieval partition and the actual completion
objective, plus multi-path coverage that does not force one item into one
semantic neighborhood.

### Monolith and real-time adaptation

The 2022 [Monolith paper](https://arxiv.org/abs/2209.07663) establishes
historical deployment in BytePlus Recommend, not TikTok. The
[ByteDance repository](https://github.com/bytedance/monolith) was archived on
2025-10-13 and is read-only.

Monolith's important techniques are:

- collisionless Cuckoo-hash tables so sparse users and items do not share an
  embedding accidentally;
- frequency admission filters so almost-never-seen IDs consume no vector;
- per-table expiry for stale users and short-lived videos;
- event/feature stream joins that tolerate delayed and out-of-order outcomes;
- continuous online training after a batch bootstrap;
- touched-key tracking that sends only changed sparse embeddings to serving;
- minute-level sparse updates and day-level dense-weight updates; and
- failure-tolerant snapshots that trade a small amount of sparse state for much
  lower recovery cost.

This establishes that the disclosed BytePlus or unnamed production
infrastructure synchronized touched sparse embeddings at minute level while
dense weights updated daily. Its update-frequency evidence comes from a Criteo
simulation and an unnamed production ads model; it does not establish TikTok
deployment or minute-scale end-to-end concept-drift tracking on TikTok.

### Why TikTok succeeds, within the evidence boundary

**Inference:** A plausible contribution of TikTok's disclosed product design is
high-information feedback from short interactions, first-session adaptation,
controlled novelty, and eligibility and repetition controls around relevance.
TikTok's June 2020 explanation said follower count and prior viral hits were not
direct ranking factors; current documentation does not restate that exact claim,
and it did not imply follower count has no indirect exposure effect. Claims
about TikTok's exact loss, embedding model, candidate generators, exploration
rate, or online lift remain unsupported.

## 3. Netflix

### Current frontier: GenPage

Netflix's June 2026
[GenPage](https://arxiv.org/abs/2606.31031) system treats the whole structured
homepage as the prediction target. A decoder-only transformer receives user and
request context as a prompt and autoregressively emits rows and titles in layout
order.

Its main techniques are:

- a domain tokenizer for title ID, row ID, action type, time bucket, and duration
  bucket, making long histories far cheaper than natural-language tokens;
- page-level examples containing context, the shown page, and feedback such as
  plays, thumbs, and abandonment;
- next-token pretraining on production pages followed by Weighted Binary
  Classification, where reward sign supplies the label and reward magnitude the
  example weight;
- a long-term reward system in which binge completion, shallow plays,
  abandonment, novelty, and later behavior can have different value;
- autoregressive row and title selection, so later choices depend on the page
  already constructed;
- token masks for eligibility, deduplication, pinned rows, and row-title
  consistency;
- multi-cadence incremental training, daily vocabulary updates, historical
  replay, and semantic fallback embeddings for new titles; and
- hybrid decoding: generate the first few entities in each row
  autoregressively, then score the remaining row candidates together.

Five Weighted Binary Classification variants beat a mature multi-stage baseline
in a 14-day online experiment. The best improved Netflix's core engagement
metric by 0.24% with p < 0.001 and reduced end-to-end serving latency by 20%.
The deployed experiment still decoded over production candidate sets, so this
does not establish that GenPage replaced corpus-scale retrieval.
The test also produced unintended shifts in impressed-title categories; Netflix
says those shifts remain under investigation.

Netflix also tested page-level reinforcement learning. It improved learned
offline reward and diversity, but the evaluation used a related reward model and
Netflix does not claim the RL variant is deployed. That boundary matters.

GenPage's deployed-test contribution is a page-native representation and
autoregressive serving path. Its Weighted Binary Classification objective still
decomposes reward by entity; only the unshipped reinforcement-learning variant
jointly optimizes page reward and explicitly models interactions such as
diversity and differing stopping power.

### Shared preference foundation model

Netflix's 2025
[Foundation Model for Personalized Recommendation](https://netflixtechblog.com/foundation-model-for-personalized-recommendation-1a0bd8e02d39)
centralizes preference learning from comprehensive interaction histories and
content data.

Important design choices include:

- tokenizing meaningful interaction sequences while preserving action, duration,
  and timing;
- next-token and multi-token future prediction rather than hand-building a
  separate user representation for every surface;
- content and ID representations, with stronger content fallback for new titles;
- compressed older history, sparse attention, sliding windows, and KV caching;
- reusable member/title embeddings and fine-tunable weights; and
- orthogonal low-rank alignment to stabilize embedding dimensions across
  retraining runs.

Netflix documents three production integration modes:

1. Daily profile and title embeddings in a versioned Embedding Store: cheapest
   and easiest, but potentially stale.
2. The foundation decoder as a downstream-model subgraph: fresher and more
   expressive, but larger and slower.
3. Product-specific fine-tuning: strongest task alignment, but more models and
   operational cost.

The embedding pipeline pretrains broadly, fine-tunes on current data, expands
for new titles, and is moving toward near-real-time session updates. See
[Integrating Netflix's Foundation Model into Personalization applications](https://netflixtechblog.medium.com/integrating-netflixs-foundation-model-into-personalization-applications-cf176b5860eb).

### Long-term reward engineering

Netflix's
[long-term member satisfaction work](https://netflixtechblog.com/recommending-for-long-term-member-satisfaction-at-netflix-ac15cada49ef)
starts from retention but does not optimize retention directly because it is
sparse, delayed, noisy, and difficult to attribute. Instead it validates proxy
rewards from play depth, completion, thumbs, novelty, and later behavior.

Concrete state transitions are treated differently: fast season completion can
be positive; completion followed by thumbs-down is negative; a ten-minute movie
play is ambiguous; and sustained consumption in a newly sampled genre can carry
discovery value. A delayed-feedback model estimates mature labels for recent
examples. Offline AUC is diagnostic, while online retention and satisfaction
experiments decide whether the proxy is actually useful.

### Evidence that personalization adds value

A 2025/2026 Netflix study,
[The Value of Personalized Recommendations](https://arxiv.org/abs/2511.07280),
uses a structural choice model validated with randomized recommendation
perturbations. Its counterfactual estimates say replacing the current system
with matrix factorization would reduce engagement about 4%, and replacing it
with popularity ranking about 12%, while both alternatives concentrate
consumption more heavily. Most estimated value comes from targeting
mid-popularity titles rather than mechanically increasing exposure. These are
modeled counterfactuals, not a randomized shutdown of the complete system.

### Why Netflix succeeds

Netflix aligns each level with the member's decision: full-history preference
learning represents latent taste; session intent changes the current request;
long-term rewards proxy member satisfaction; and page-native generation
conditions later choices on the already-generated layout. Explicit joint
optimization of diversity and stopping power is limited to the unshipped
reinforcement-learning result. Hard masks preserve catalog, policy, and product
correctness instead of asking the learned score to absorb every constraint.

## 4. Spotify

### Generalized user representations

Spotify's 2025 production
[Generalized User Representations](https://research.atspotify.com/2025/9/generalized-user-representations-for-large-scale-recommendations)
train one denoising autoencoder over complementary preference signals and attach
small transfer heads for Home retrieval, ranking, and search.

The representation combines:

- acoustic track embeddings;
- collaborative playlist and co-listening embeddings;
- behavior over roughly week, month, and six-month horizons;
- onboarding choices; and
- demographic and request context.

Denoising prevents the encoder from copying a sparse input. Onboarding artists,
genres, languages, and context initialize cold users; the representation
gradually shifts toward behavior-driven signals as observations accumulate.
Batch vectors cover the population, while active-user updates reach the online
feature store within minutes.

Representation versioning is a correctness feature: every snapshot carries a
version, downstream consumers retrain against it, and the previous snapshot
remains live until all consumers can switch together. This prevents a user
vector from being compared with items or models in a different embedding space.

Reported online results include +2.9% discoveries and +13% item-to-stream
conversion for Home candidate generation. Removing onboarding reduced cold-start
nDCG@50 by 13.8%; removing audio/collaborative inputs reduced favorite-artist
nDCG by 37.1%. These ablations show complementary value from onboarding, the
combined audio-plus-collaborative encoders, and static user attributes; they do
not isolate audio from collaborative signals or individual time horizons.

### Long-horizon podcast discovery

Spotify's production
[long-term audio recommendation system](https://arxiv.org/abs/2302.03561)
separates the probability of an initial stream from the probability that a show
becomes a durable relationship.

- Candidate generation reduces tens of thousands of shows to about 100.
- State separates slow user taste, immediate context, and sparse per-show
  relationship features.
- A short-term model predicts the initial listen.
- A stickiness model predicts active days or relationship strength over a
  60-day horizon.
- The policy ranks approximately by immediate-listen probability multiplied by
  incremental personalized stickiness.
- Holdbacks estimate whether discovery would have occurred organically.

Item-level reward decomposition avoids assigning all later application behavior
to one recommendation and dramatically lowers sample requirements compared with
a black-box long-horizon value model. In a banner test the long-term policy
sacrificed some first streams but increased 60-day show minutes 81% and active
days 32%. A nine-week shelf test improved week-eight discovery consumption 6.2%
and lasting discoveries 5.4%.

The decomposition assumes no indirect substitution or spillover between
recommended items and assumes future value is mediated by the next
item-relationship state. Spotify validates the discovery application online,
but reports only offline correlational evidence for resurfacing familiar shows.

### Contextual calibration and exploration

Spotify Home is historically a candidate-generation then ranking system, with
cards grouped into shelves. Its March 2025 deployed
[contextual calibration bandit](https://research.atspotify.com/2025/9/calibrated-recommendations-with-contextual-bandits-on-spotify-homepage)
chooses the distribution of music, podcasts, and other content types for the
current request.

Context includes time, day, device, user embeddings, and content embeddings.
Epsilon-greedy exploration supplies feedback. The chosen type distribution
guides sequential slate construction, with a KL-divergence penalty balancing
item relevance against deviation from the desired mix. Against a static
90-day-preference baseline, the online experiment reported +36.6% podcast
impression-to-stream efficiency, +3.93% overall impression-to-stream efficiency,
+1.28% consumption, and +1.54% Home activity.

The deployed reward is short-term Home-page streaming for a chosen content-type
distribution; long-term and multi-objective rewards are explicitly future work.

This succeeds because calibration is contextual rather than a fixed reflection
of historical shares. A listener's podcast preference on a weekday commute need
not consume the same fraction of an evening music session.

Spotify's November 2025
[Semantic-ID LLM work](https://research.atspotify.com/2025/11/teaching-large-language-models-to-speak-spotify-how-semantic-ids-enable)
productionized catalog-native infrastructure using residual lookup-free
quantization, an expanded LLM vocabulary, Redis URI/ID resolution, and vLLM
serving. Its reported 1.96x episode-recommendation result and search parity are
benchmark results, not online A/B lifts; broader generative recommendation
applications are described as forthcoming.

### Multi-stakeholder and sequence objectives

Spotify's research-only
[Mostra](https://research.atspotify.com/2022/4/mostra-balancing-multiple-objectives-for-music-recommendation)
uses a Set Transformer and beam search to trade listener satisfaction against
discovery, emerging-artist exposure, and explicit platform objectives. A
counterfactual decode step only promotes an objective-tagged track when its
relevance lies within epsilon of the best item, and submodular scoring covers
different objectives across the sequence. The decoder's weights can change
without re-encoding the catalog.

Spotify has also tested sequence optimization that models both position value
and adjacent-track acoustic compatibility. Randomized logging and
inverse-propensity estimators supported offline evaluation; an online test
reported +2.52% completed tracks per session and -2.73% skips. The source
reports an online experiment, not confirmed permanent deployment. See
[Exploiting Sequential Music Preferences](https://research.atspotify.com/2023/10/exploiting-sequential-music-preferences-via-optimisation-based-sequencing).

The shipped "Exclude From Your Taste Profile" control is equally important:
functional or household listening can be removed from the personalization
profile without deleting it from history surfaces. That prevents a concrete
contextual action from mutating long-term preference state. See
[Exclude From Your Taste Profile](https://engineering.atspotify.com/2023/10/exclude-from-your-taste-profile).

### Why Spotify succeeds

Spotify preserves several meanings of taste: semantic and collaborative,
familiar and exploratory, short- and long-horizon, current context and durable
preference. It has online-tested ordered listening-sequence optimization, treats
durable discovery as a separate reward, and exposes controls for feedback that
should not train the profile.

## 5. Pinterest

Pinterest publishes the most complete current funnel in this set:

retrieval -> pre-ranking -> ranking -> multi-objective re-ranking.

### Generative retrieval

The 2025/2026 production
[PinRec](https://arxiv.org/abs/2504.10507) transformer is one candidate
generator across Home Feed, Related Pins, and Search.

- It pretrains on lifelong cross-surface activity, then fine-tunes
  surface-specific variants on impression logs.
- Inputs combine Pin/query embeddings, surface, absolute time, and relative
  time.
- It generates dense embeddings resolved through ANN rather than discrete IDs.
  This avoids invalid-ID generation and supports unseen entities.
- Sampled-softmax frequency correction handles non-uniform in-batch sampling.
- Impressed-but-unengaged candidates become hard negatives.
- Outcome-conditioned generation emits separate embeddings for saves, clicks,
  and other outcomes; per-outcome budgets provide an explicit Pareto control.
- Multi-step generation feeds a selected output back into the next step, so
  later candidates depend on the developing synthetic sequence.
- Daily long-history state is joined with post-cutoff real-time activity.

PinRec improved Home grid clicks 4.01%, Related Pins time spent 0.38%, and
Search fulfillment 2.24% in reported online tests. It remains one candidate
source whose results pass through the rest of the funnel.

### Graph, multimodal, and plural-interest retrieval

Pinterest's historical graph systems remain instructive. Pixie performs
real-time random walks over the Pin-board bipartite graph and caps popular-node
influence. [PinSage](https://medium.com/pinterest-engineering/pinsage-a-new-graph-convolutional-neural-network-for-web-scale-recommender-systems-88795a107f48)
learned graph-convolution embeddings from importance-sampled neighborhoods,
content features, and hard negatives.

[PinnerSage](https://medium.com/pinterest-engineering/pinnersage-multi-modal-user-embedding-framework-for-recommendations-at-pinterest-bfd116b49475)
made a crucial correction to single-vector personalization:

- cluster a person's clicks and saves in PinSage space;
- represent every cluster with a medoid, embedding, and importance score;
- select several clusters online and retrieve ANN neighbors for each; and
- combine daily long-term inference with same-day online clusters.

Keeping item embeddings fixed prevents unrelated user interests from pulling
otherwise dissimilar Pins together. Multiple user vectors preserve unrelated
interests instead of averaging them into a meaningless center.

Current learned retrieval adds two-tower models, real-time transformer state,
multi-interest differentiable clustering, explicit interest-conditioned
retrieval, and multimodal Pin representations. The 2026
[PinCLIP](https://arxiv.org/abs/2603.03544) work aligns image and text at
Pinterest scale for retrieval and ranking.

### Stage-correct pre-ranking

Pinterest's 2025
[modern pre-ranking layer](https://medium.com/pinterest-engineering/modernizing-home-feed-pre-ranking-stage-e636c9cdc36b)
replaced independent lightweight rankers attached to each retriever.

A request network computes user state once; item networks score sharded
candidates using cached non-real-time item features and early user-item feature
crossing. Training combines final impressions with early-funnel candidates that
were retrieved but not impressed. These are harder, more
serving-representative negatives. BCE on engagement is combined with KL
distillation from the calibrated full ranker, aligning the cheap model with the
decision it approximates.

### Lifelong and real-time sequence ranking

The production 2025
[TransAct V2](https://arxiv.org/abs/2506.02267) system stores up to 16,000
lifelong actions with timestamp, action type, surface, and quantized Pin
representations. For each candidate it selects recent actions plus
candidate-relevant neighbors from lifelong, real-time, and impression history;
only a compact selected sequence enters the transformer.

The model:

- early-fuses candidate content into the action sequence;
- predicts click, repin, hide, and other outcomes with multitask heads;
- adds a next-action auxiliary loss; and
- uses impressed-but-unengaged negatives, which outperform in-batch negatives
  for reducing hides.

Request-level deduplication, int8 state, and custom Triton kernels make long
history affordable. Reported online results include +6.35% repins, -12.80%
hides, +0.45% impression diversity, and +1.41% time spent.

Pinterest's separate production
[PinFM](https://arxiv.org/abs/2507.12704) work scales a causal sequence model to
20B+ parameters over up to two years of activity; most of those parameters are
CPU-served embedding tables. It uses next-event and
multi-token future objectives, age-dependent candidate-ID dropout for cold
start, shared sequence computation across about 1,000 candidates, KV caching,
and int4 post-training quantization of the embedding tables. Reported Home
results include +1.20% sitewide saves and +5.70% fresh-Pin saves. Public sources
do not establish that PinFM and TransAct V2 are mutually exclusive replacements.

### Multi-objective feed construction

Pinterest's 2026
[multi-objective Home Feed account](https://medium.com/pinterest-engineering/evolution-of-multi-objective-optimization-at-pinterest-home-feed-06657e33cd10)
contains one of the clearest long-term diversity experiments: removing
feed-level diversity increased saves on day one, turned negative by week two,
and reduced session time.

The production re-ranker has evolved from DPP-based relevance/similarity
selection toward Sliding Spectrum Decomposition:

- build a local sliding similarity matrix;
- spectrally identify overexposed latent directions;
- softly penalize repeated spectra rather than hard-filtering every similar
  item; and
- use visual features upgraded to PinCLIP, text, GraphSAGE, and Semantic-ID
  signals; taxonomy belonged primarily to the earlier DPP stack.

Soft spacing applies distance-decayed penalties to clusters of elevated-risk
content. A significant portion of diversification moved to a PyTorch model
server, and soft spacing became configuration-driven; additional backend
heuristics remain, with further migration ongoing. User-specific diversity and
RL value models are listed as future work and must not be described as current.

Pinterest also trained a 92K-parameter visual-quality model from ratings of
5,000 Pins and used it across Home, Related Pins, and Search. See
[Improving Quality of Recommended Content through Pinner Surveys](https://medium.com/pinterest-engineering/improving-quality-of-recommended-content-through-pinner-surveys-eebca8a52652).

### Why Pinterest succeeds

Pinterest treats discovery as a coverage problem before it is a ranking problem.
Graph walks, multimodal ANN, learned retrieval, and explicit interest sources
reach different inventory. Plural user embeddings preserve unrelated tastes.
Real-time and lifelong sequences supply different state. Each funnel stage is
trained with stage-relevant evidence: pre-ranking uses early-funnel negatives
from its own decision boundary, while ranking uses impression outcomes. Final
set-level optimization prevents visually repetitive relevance from degrading
long-term value.

## 6. Meta: Instagram Explore and Facebook Reels

### One company, many recommenders

There is no single Meta recommender. Instagram operated more than 1,000
production models across many surfaces and funnel layers by 2025. See
[Journey to 1000 models](https://engineering.fb.com/2025/05/21/production-engineering/journey-to-1000-models-scaling-instagrams-recommendation-system/).
Instagram Explore's detailed public architecture is a 2023 production snapshot,
while SilverTorch and Facebook Reels survey alignment are current 2026
disclosures.

### Instagram Explore's staged funnel

The 2023
[Explore architecture](https://engineering.fb.com/2023/08/09/ml-applications/scaling-instagram-explore-recommendations-system/)
uses retrieval, first-stage ranking, second-stage ranking, and final re-ranking.

- Retrieval mixes heuristic and learned, real-time and pregenerated sources with
  tunable weights. Sources include trending/local content, two-tower user-item
  retrieval, and item-to-item ANN seeded from selected likes, saves, and shares.
- Low-quality history seeds are removed before retrieval so an accidental
  interaction does not flood the feed.
- The two-tower retriever supports arbitrary user, media, and author features
  and several engagement tasks. Cached offline item vectors and a fresh online
  user tower give efficient ANN search.
- The first-stage two-tower ranker is distilled from the heavy model: its target
  is whether the heavy ranker would place the item in its top K.
- The heavy MTML model uses user-item cross features and predicts clicks, likes,
  negative actions, and other outcomes for about the best 100 candidates.
- The value formula combines positive and negative probabilities; final
  re-ranking applies integrity and author-diversity rules.
- Hourly continual fine-tuning, cacheable embeddings, off-peak generation, and
  distillation allocate expensive computation to the shrinking funnel.

The architecture succeeds by aligning cheap early stages to later decisions
while retaining heterogeneous candidate coverage. The price of independent
towers is that the retrieval score cannot use direct user-item cross features;
those wait for later stages.

### Current model-based retrieval infrastructure

Meta's May 2026
[SilverTorch](https://engineering.fb.com/2026/05/26/ml-applications/silvertorch-index-as-model-new-retrieval-paradigm-recommendation-systems/)
turns the retrieval index, eligibility filter, ANN search, neural re-ranker, and
multi-action scorer into modules in one PyTorch graph.

Keeping item state and cross features in GPU memory permits:

- one forward pass instead of a mesh of serialized microservice calls;
- according to Meta, one to two orders of magnitude more candidates through
  additional learned early scoring;
- richer user-item interaction models before final ranking;
- joint optimization of selected handwritten and learned modules;
- full snapshots plus targeted tensor updates between snapshots, as described
  by Meta's engineering account; and
- consistent deployment as one model artifact.

On an 80M-item replay, SilverTorch delivered 23.7x the requests per second of
an optimized multi-service baseline. Its reported cost efficiency was 20.9x
versus an all-CPU baseline and 13.35x versus an optimized two-stage GPU baseline
with reranking. A separate no-recall-loss result applies to the disclosed fused
Int8 ANN configuration at 64 probes and top-2048. These are system/replay
results, not user-level A/B evidence. Meta says SilverTorch supports feed and
video recommendations across a family of apps without naming every surface.

### Sequential generative models

Meta's 2024
[HSTU Generative Recommenders](https://arxiv.org/abs/2402.17152) reformulate
retrieval and ranking as sequential transduction over heterogeneous streaming
events. HSTU is designed for high-cardinality, nonstationary recommendation
data; M-FALCON amortizes inference across candidates. A 1.5T-parameter
deployment reported a 12.4% lift on unnamed top-line metrics across multiple
unnamed surfaces of a large platform with billions of users. This establishes
Meta-scale deployment, not use by a specific Instagram or Facebook surface.

### Direct satisfaction through Facebook Reels surveys

The current
[User True Interest Survey system](https://engineering.fb.com/2026/01/14/ml-applications/adapting-the-facebook-reels-recsys-ai-model-based-on-user-feedback/)
corrects a concrete failure of engagement-only ranking.

Random viewing sessions receive a one-to-five interest-match question.
Responses are weighted for sampling and nonresponse bias and binarized to reduce
variance. A lightweight perception layer consumes the base MTML event
predictions plus user, content, and interest features and predicts stated
interest match.

That score is used twice:

1. late ranking adds it to the final value formula; and
2. early retrieval reconstructs true-interest profiles and distills the
   late-stage signal into large retrieval models.

This lets sparse intentional labels supervise abundant behavioral predictions
through the entire funnel. In an A/B test with more than 10 million users, Meta
reported +5.4% high survey ratings, -6.84% low ratings, +5.2% total engagement,
and -0.34% integrity violations. The approach also increased delivery of niche,
high-quality content relative to generic popularity.

### Multimodal understanding and operations

Meta's unconnected-content stack uses visual, audio, OCR, language, topic,
hashtag, graph, and similarity representations. See
[AI recommendations of unconnected content](https://ai.meta.com/blog/ai-unconnected-content-recommendations-facebook-instagram/).
In Meta's 2023 Explore disclosure, poor-quality history seeds were filtered
before ranking and integrity signals were applied during final re-ranking.

Fleet operations contribute directly to quality. Instagram's model registry
tracks each model's surface, funnel role, baseline, holdout, and criticality.
Calibration and normalized entropy are monitored per output; replay and capacity
tests guard launches. This exposed prediction failures that ordinary service
uptime did not detect and enabled more than ten model launches per week.

### Why Meta succeeds

Across separate disclosed systems—not one named current end-to-end Instagram or
Facebook stack—Meta combines broad heterogeneous retrieval, distillation into
cheap early models, multimodal content understanding, online freshness,
sequential user state, many positive and negative targets, survey-derived
satisfaction, and separate integrity/diversity controls. System/model co-design
raises the number and complexity of candidates that can be evaluated under the
same latency budget.

## 7. X For You

### Current 2026 pipeline

X's May 2026 [open algorithm repository](https://github.com/xai-org/x-algorithm)
describes the current core as Thunder, Phoenix, and Home Mixer. It supersedes the
2023 Twitter RealGraph/GraphJet/SimClusters architecture; the two should not be
silently combined.

Home Mixer hydrates recent actions, follows, preferences, topics, impression
Bloom filters, mutual-follow state, and served history. Independent sources and
hydrators run in parallel.

Candidate retrieval has two primary paths:

- **Thunder** consumes create/delete events, holds recent per-author posts in
  memory, and returns followed-account inventory with sub-millisecond lookup.
- **Phoenix retrieval** uses a transformer user tower over user state and
  engagement history, a candidate tower over posts, normalized embeddings, and
  dot-product/ANN search over out-of-network inventory.

The Phoenix ranker is a Grok-derived transformer. A candidate can attend to the
shared user/history context and itself but not to other candidates. This
candidate-isolation mask makes scores independent of batch composition and
lets all candidates share one user/history context in a forward pass while
keeping each candidate score independent and cacheable.

Phoenix separately predicts:

- favorite, reply, repost, quote, click, profile click;
- video view, photo expansion, share, dwell, follow-author; and
- not-interested, block, mute, and report.

A weighted sum rewards positive predictions and penalizes negative ones.
Checked-in weights are not evidence of exact live production weights.

The complete pipeline retains explicit product logic even though X says learned
relevance no longer uses hand-engineered features:

- duplicate, age, self-post, access, block, mute, keyword, seen, and
  already-served filters;
- author-diversity attenuation;
- out-of-network calibration;
- conversation deduplication; and
- VFFilter removal of deleted, spam, violence, and gore content.

Grox separately supplies content-understanding, spam, category, and policy
signals.

Thunder provides event-time freshness, while Phoenix production is described as
continuously trained. The public checkpoint is a smaller frozen artifact and
production scaling optimizations are withheld.

### Evidence boundary

The open implementation provides unusually strong architectural evidence but no
current online A/B lift, retention change, relevance metric, or production
quality benchmark. Out-of-network retrieval broadens discovery, but X does not
publish an explicit bandit, uncertainty bonus, or exploration rate. X belongs
in this comparison for auditability and modern system design, not because public
data proves that it outperforms the other systems.

### Why the design is strong

The system combines real-time social inventory with learned global discovery,
uses the same transformer architecture for the retrieval user tower and ranker,
both conditioned on engagement history, lets candidates share one history
context, models negative outcomes directly, and keeps product policy composable
outside the learned ranker.

## 8. LinkedIn Feed

### Current retrieval

LinkedIn's current out-of-network retriever is a shared fine-tuned Llama-3 dual
encoder. See
[Large Scale Retrieval for the LinkedIn Feed Using Causal Language Models](https://arxiv.org/abs/2510.14223)
and the 2026
[engineering overview](https://www.linkedin.com/blog/engineering/feed/engineering-the-next-generation-of-linkedins-feed).

Post prompts contain text, format, author, job/company/industry context,
popularity, and article metadata. Member prompts contain profile, skills,
work/education history, and chronologically ordered professional interactions.
Positive-only history worked better in the long member representation, while
shown-but-unengaged posts served as per-member hard negatives during training.
This separates durable identity from contrastive near misses.

Other important techniques:

- InfoNCE combines global in-batch easy negatives with impressed hard negatives.
- A combined ablation—truncating post text to 60 tokens and adding quantized
  popularity-percentage tokens—raised Recall@10 from 0.1580 to 0.1839. The full
  lift cannot be attributed solely to percentile tokens or to recency or
  affinity fields.
- Matryoshka training provides nested embedding sizes for storage/latency
  tradeoffs without retraining separate models.
- New post/profile embeddings arrive in about a minute; interaction updates
  arrive in about 30 minutes.
- Trust, language, block, and seen filters execute inside GPU retrieval.

Holding downstream ranking fixed, the online retrieval test reported +0.2%
daily unique professional interactors and +0.8% revenue. Low-connectivity users
benefited more. Connected-network inventory still uses separate sources; the
LLM retriever does not replace the professional graph.

### Current sequential ranker

The May 2026
[Feed Sequential Recommender](https://arxiv.org/abs/2602.12354) replaces the
previous DCNv2 ranker and serves most Feed traffic.

Feed-SR retains roughly 1,000 impressed posts across up to a year, interleaving
compact post and multi-hot action embeddings. A causal transformer predicts
actions at every position. At serving, hundreds of candidates are appended and
scored in one pass.

Its candidate-isolation/shared-context mask lets candidates attend to history
and themselves, not one another. That avoids recomputing the 1,000-item history
for each candidate and produced an 80x transformer-forward speedup. A custom
Flash-Attention kernel skips invalid mask tiles.

Feed-SR is not feature-purist:

- sequence learning removed about 80% of old hand-engineered features;
- device/request context, item popularity, and long-window viewer-author
  affinity remain useful;
- those structured features enter through late fusion to avoid quadratic
  sequence cost; and
- a daily Qwen3-derived profile embedding helps sparse histories.

LinkedIn reports that an earlier text-only LLM ranker never beat the incumbent
online; Feed-SR separately beat that incumbent. The reported Feed-SR test
improved time spent 2.10% and likes/comments/reshares 3.52%. The authors report
nonsignificant new-member deltas rather than a demonstrated cold-start gain.

### Multi-objective ecosystem value: 2024 production snapshot

LinkedIn's 2024 Feed disclosure described an objective including:

- viewer passive value such as normalized dwell;
- viewer contribution such as comments and reshares;
- downstream value to the viewer's network; and
- upstream feedback value to the creator.

See [Leveraging Dwell Time to Improve Member Experiences](https://www.linkedin.com/blog/engineering/feed/leveraging-dwell-time-to-improve-member-experiences-on-the-linkedin-feed).

A fixed dwell threshold would favor intrinsically long formats. LinkedIn labels
"long dwell" relative to daily percentiles within content type, creator type,
and distribution path. Recomputing these cohorts daily follows ecosystem drift
and compares quality within a format instead of turning format duration into
relevance.

The 2026 Feed-SR paper confirms long-dwell and contribution heads, but does not
confirm that downstream-value, creator-value, or the exact 2024 dwell
normalization remain in the current objective.

Historical creator-side optimization modeled diminishing returns: a first
useful response to an underserved creator carried more ecosystem value than
another response to an already saturated creator, subject to viewer-quality
constraints. The 2018 test shifted about 8% of feedback from the top 0.1% of
creators to the bottom 98% and increased returning creators 5%. It is a useful
precedent, not a claim about the current formula. See
[LinkedIn Feed with Creator-Side Optimization](https://www.linkedin.com/blog/engineering/member-customer-experience/linkedin-feed-with-creator-side-optimization).

### Debiasing and production correctness

Current Feed-SR work exposes several less glamorous but high-value corrections:

- randomize within-session order during training so prior session labels cannot
  leak information unavailable at serving;
- downsample easy negatives for training but evaluate on the full distribution,
  because negative downsampling inflates AUC;
- replay the same sessions offline and compare exact online scores to find
  feature-transformation and train/serve bugs.

A separate 2019 LinkedIn practice used a randomized first-pass traffic slice so
downstream labels covered more than the incumbent retriever's favorite
candidates and evaluated early retrieval by recall against downstream top K
rather than first-stage precision. This is a historical debiasing precedent,
not evidence about the current Feed-SR stack.

### Why LinkedIn succeeds

LinkedIn preserves the professional graph while adding semantic out-of-network
retrieval; uses sequence models without discarding exact numeric and
relationship features; and co-designs model kernels and feature transport so
the stronger model can meet real-time cost. LinkedIn's 2024 production
disclosure separately described objectives spanning viewer, network, and
creator value.

## Cross-System Synthesis

### Techniques with the strongest transferable evidence

| Technique | Contribution | Strongest examples |
| --- | --- | --- |
| Multiple candidate sources | Raises recall and prevents one representation from defining the eligible universe | Instagram source mixing, Pinterest's 20+ generators, X in-/out-of-network split |
| Stage-specific supervision | Teaches each funnel layer the decision it actually approximates | Pinterest early-funnel negatives and distillation; Instagram top-K distillation |
| Sampling and exposure correction | Stops popularity, position, or incumbent policy from masquerading as preference | YouTube frequency and position correction; LinkedIn randomized first pass (2019 disclosure) |
| Content plus collaborative identity | Preserves behaviorally useful similarity while handling new and tail items | YouTube NDR, Pinterest PinCLIP/PinSage, Spotify acoustic plus co-listening |
| Multiple user timescales | Separates durable taste from current intent and accidental context | Netflix session context, Spotify horizon features, Pinterest lifelong plus real-time actions |
| Plural interests | Prevents unrelated tastes from averaging into one poor vector | PinnerSage and Pinterest multi-interest retrieval |
| Sequential models | Learns order, recency, transitions, and changing intent directly | LinkedIn Feed-SR, Pinterest TransAct V2, X Phoenix, Meta HSTU |
| Multi-action prediction | Preserves distinct semantics of clicks, completion, contribution, hides, and reports | YouTube MMoE, Meta MTML, X Phoenix, LinkedIn Feed-SR |
| Satisfaction labels | Corrects engagement proxies with sparse intentional judgments | YouTube valued watchtime, Facebook Reels UTIS, Pinterest quality surveys |
| Long-term rewards | Avoids optimizing attractive but disposable consumption | YouTube LRF, Netflix reward system, Spotify podcast stickiness |
| List/page optimization | Captures dependencies and composition that independent item scores miss | Netflix GenPage, YouTube cascade LRF, Pinterest spectrum diversity, Spotify slate calibration |
| Controlled exploration | Produces information without sending arbitrary low-quality items | YouTube randomized top promotion and Boltzmann/top-K policies; Spotify contextual bandit |
| Explicit negative controls | Lets users correct state and prevents positive-only feedback loops | TikTok Not Interested, X block/mute/report heads, Spotify taste exclusion |
| Eligibility and integrity controls | Applies hard eligibility before relevance and permits integrity signals to override engagement where needed | TikTok eligibility; YouTube authoritativeness/borderline overrides; Meta/X filtering |
| Fresh online state | Responds to session intent, new content, and concept drift | Historical BytePlus Monolith, Instagram's disclosed hourly fine-tuning, LinkedIn minute-level embeddings |
| Representation versioning | Prevents silent comparison across incompatible embedding spaces | Spotify snapshot IDs, Netflix alignment transforms, Pinterest model/index synchronization |
| System/model co-design | Converts latency and memory headroom into recommendation quality | SilverTorch, Feed-SR shared context, TransAct kernels, GenPage hybrid decoding |
| Randomized online evaluation | Resolves offline metric ambiguity and measures long-term/guardrail effects | YouTube, Netflix, Spotify, Pinterest, Meta, and LinkedIn; TikTok and current X lack comparable public outcome evidence |

### The common architecture

The disclosures collectively support this recurring logical flow—even when a
generative model collapses physical stages—but no selected system publicly
documents every step of its current stack:

1. **Eligibility:** determine what is legally, safely, geographically, and
   product-wise showable.
2. **Candidate union:** combine social, graph, semantic, collaborative, popular,
   fresh, local, editorial, and exploratory sources.
3. **Cheap alignment:** pre-rank many candidates using cacheable embeddings or a
   distilled early model.
4. **Rich prediction:** use cross features and sequential state to predict
   several user and ecosystem outcomes.
5. **Value model:** translate those probabilities into satisfaction or
   long-term incremental value.
6. **Set construction:** apply diversity, fatigue, author distribution,
   content-type calibration, and page/sequence interactions.
7. **Feedback and learning:** where exploration or off-policy correction is
   used, log propensities and experiment assignments; update state and validate
   launches with randomized tests where available.

Netflix GenPage collapses several ranking and page-construction stages;
Pinterest PinRec remains a candidate generator feeding existing ranking and
blending. Meta's HSTU deployments on unnamed surfaces and Pinterest's disclosed
generative retrieval work change where some boundaries live, not the need for
eligibility, coverage, objectives, and counterfactual evaluation.

### What matters more than model family

1. **Reward quality.** YouTube, Netflix, Spotify, Pinterest, and Meta all publish
   cases where a short-term metric points in the wrong direction.
2. **Candidate recall.** Re-ranking only rearranges the retrieved set.
3. **Feedback semantics.** A completion, replay, save, hide, report, and survey
   answer are not interchangeable labels.
4. **State separation.** Long-term identity, current session intent, request
   context, and instructions to change future recommendations should not be one
   undifferentiated vector.
5. **Bias correction.** Logged feedback describes the previous policy's
   exposures as much as it describes user preference.
6. **Whole-list effects.** Individually relevant items can form a repetitive,
   unbalanced, or harmful feed.
7. **Freshness and correctness.** Stale or version-mismatched embeddings erase
   theoretical model gains.
8. **Online evidence.** Better AUC, Recall@K, or learned reward does not prove
   better long-term user value.

## Failure Modes to Avoid

- **Engagement as the sole reward:** produces clickbait, regretful watch time,
  overly familiar music, or low-quality visual content.
- **One pooled embedding for multi-intent retrieval:** can average unrelated
  interests into a poor query vector.
- **A single retriever without explicit coverage validation:** can create blind
  spots that no ranker can repair.
- **Popularity without sampling correction:** turns exposure frequency into a
  learned preference prior and suppresses tail content.
- **Treating every non-click as dislike:** confuses lack of attention, bad
  position, and genuine negative preference.
- **Using logged position as an ordinary serving feature:** can reproduce
  exposure bias instead of estimating item utility; YouTube's 2019 study
  reported a -0.07% engagement change for that variant.
- **Pointwise ranking without set controls:** creates author, topic, format, and
  visual repetition.
- **Uniform random exploration over the corpus:** wastes impressions and can be
  unsafe; exploration should operate inside an eligible, plausibly relevant
  subset.
- **Offline-only selection:** misses long-term reversals such as the day-one
  save gain from removing Pinterest's diversity component reversing by week two.
- **Embedding updates without coordinated consumers:** silently compares vectors
  in incompatible spaces.
- **Assuming a company paper names a product:** ByteDance research is not proof
  of TikTok internals, and Meta platform research is not proof of a specific
  Instagram surface.
- **Copying published weights or lifts:** objective scales and experiment
  baselines are system-specific.

## Implications for a Private, Decentralized Notedeck Recommender

The centralized systems depend heavily on pooled private behavior, but many of
their strongest ideas survive the privacy boundary.

This section describes possible capabilities of a later production system, not
the approved Oracle MVP. The MVP deliberately tests one public semantic
candidate source over root text kind `1` notes, two local personalizers, and one
untouched final evaluation. It does not add graph, popularity, freshness,
multimedia, collaborative, quality, safety, exploration, or fixed-interest
components. Those parts require evidence and separate approval after the MVP
decision.

### Public computation

Public Nostr events can support:

- multimodal/text content embeddings;
- author, reply, repost, reaction, topic, and co-occurrence graphs;
- graph and semantic item-to-item retrieval;
- public popularity and freshness estimates with explicit bias correction;
- multiple independently reproducible candidate indexes; and
- public quality or safety signals whose trust provider remains user-selectable.

These artifacts should be content- or graph-derived and independently
replaceable. No one service should define the eligible corpus.

### Private on-device state

The device can retain:

- several long-term interest vectors or clusters rather than one profile;
- short-term session actions and current context;
- explicit "worth seeing" judgments;
- separate instructions such as less from this author/topic or do not train on
  this context;
- local seen/impressed state;
- local predictions for positive and negative outcomes; and
- the final value formula and slate re-ranking.

This mirrors the strongest systems while keeping private behavior, inferred
preferences, recommendation feedback, and final ranking local.

### Candidate discovery

A later production recommender could union several sources before ranking:

1. followed-author and social-neighborhood content;
2. reply/repost/reaction graph walks;
3. semantic neighbors of distinct interest clusters;
4. collaborative neighborhoods derived only from public events;
5. fresh and local-to-topic content;
6. underexposed but high-quality content;
7. explicit topic or author requests; and
8. a small eligible exploration pool.

That later system could evaluate each source by marginal recall: how many eventually valuable
items disappear when that source is removed? Aggregate precision is not enough.

### Objective and feedback design

The existing "worth seeing" judgment should be the primary satisfaction target,
not passive dwell. A separate control that changes future recommendations must
mutate local preference state without being treated as a judgment of the current
note. Absence of feedback must remain unknown rather than negative.

Useful auxiliary outcomes include open-thread, expand-media, profile-open,
reply, repost, zap, save, hide, mute, and report, but the value model should be
trained or calibrated against intentional worth judgments. This follows the
YouTube, UTIS, and Pinterest survey pattern without exporting the survey data.

### Exploration and evaluation

Safe local exploration requires:

- eligibility before exploration;
- randomization among plausible candidates, not the full corpus;
- logged selection probability;
- explicit source and model version;
- enough persistence to observe delayed judgments; and
- user-level controls to disable or reset learned state.

A later production evaluation could report:

- per-interest and per-user candidate Recall@K;
- recall of unknown-author and low-popularity items;
- calibrated worth probability;
- diversity across author, topic, format, and interest cluster;
- discovery rate and lasting value after first exposure;
- negative-feedback and regret rate;
- catalog and creator exposure concentration;
- freshness, latency, and resource cost; and
- ablations for every candidate source, state timescale, and objective term.

If the MVP succeeds, production constraints can be introduced one at a time
and measured against that combined retrieval-and-personalization result, as
required by
[private-decentralized-recommendation-engine.md](./private-decentralized-recommendation-engine.md).

## Research Bottom Line for Later Product Work

The following are lessons for possible post-MVP product design, not approved
parts of the current experiment.

Across the best-documented systems, recurring design principles are:

- maximize candidate coverage with several representations;
- model the user's plural, time-varying state;
- predict behaviors separately;
- learn value from intentional satisfaction and delayed outcomes;
- correct logged-data bias;
- construct the feed as a set or sequence;
- keep eligibility and user controls explicit;
- update fresh state without breaking representation consistency; and
- treat randomized online tests as the strongest evidence of causal product
  improvement, while retaining offline, safety, and operational evidence for
  claims those tests cannot resolve.

For Notedeck, the central design opportunity is to move public representation
and discovery into replaceable public artifacts while retaining multi-interest
state, intentional feedback, exploration, value estimation, and final slate
construction on-device. The current MVP tests the narrower prerequisite: can
one strong public semantic representation and private local personalization
meet the direct personal-value bar? It does not compare against a pooled-private
system or measure a quality loss relative to one.
