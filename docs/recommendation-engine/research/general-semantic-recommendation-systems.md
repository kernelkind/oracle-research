# General Semantic Recommendation Systems

Research date: 2026-07-11

## Purpose

Identify the strongest disclosed semantic recommendation systems, compare their
successful mechanisms with the proposed Nostr meaning-map oracle, and determine
which improvements remain compatible with its privacy boundary and the `$500`
lifetime paid-compute ceiling for the complete MVP.

The completed v1 Nostr design is documented in
[oracle-mvp.md](../experiments/oracle-mvp-v1/design/oracle-mvp.md).

> **Frozen-v1 boundary (2026-07-16):** The PPLX/GTE-Large bake-off,
> 25-million-note assumptions, compact-vector sizing, and one-million-note
> experiments later in this research were historical proposals, not v1
> requirements. The evidence review and sequential GTE-then-conditional-Grit
> decision used by v1 are recorded in
> [oracle-embedding-model-research.md](../experiments/oracle-mvp-v1/design/oracle-embedding-model-research.md).
> That decision,
> [oracle-mvp.md](../experiments/oracle-mvp-v1/design/oracle-mvp.md), and
> [local-personalizer.md](../experiments/oracle-mvp-v1/design/local-personalizer.md)
> record what v1 used wherever this older survey conflicts.

## Conclusion

The retained architectural findings are:

- Compute public item representations once.
- Retrieve candidates lazily only for positive source notes that are queried.
- Return the exact same-version public candidate/document vectors needed for
  private local comparison.
- Keep private judgments, candidate fusion, and final ranking local.

The strongest systems do not reveal a better low-cost retrieval topology. Their
main advantage is that their representations are trained for recommendation on
domain-specific behavioral evidence rather than used as generic semantic
embeddings.

The completed v1 MVP did not run the model, dimension, or architecture
bake-offs proposed below. It calibrated one GTE-Qwen2-7B-Instruct
complete-corpus build, then compared two inexpensive local personalizers before
one untouched final evaluation. Nostr-adapted encoders and additional public
candidate sources remain possible later experiments, not parts of v1.

## Evidence Boundary

Most production disclosures optimize or report clicks, watch time, reactions,
or downstream-ranker recall. These establish that a technique improved the
company's existing objective, not that people were consciously glad they saw
each recommendation.

Scholar Inbox provides the strongest public evidence based on explicit ratings
and a user study. Even it operates in the relatively homogeneous domain of
research papers and does not establish quality for short, noisy social posts.

No system reviewed proves the complete Notedeck goal: broad long-tail discovery,
private local preference state, plural interests, local final ranking, and
quality measured as personal worth.

## Strongest Direct Analogues

### Scholar Inbox

[Scholar Inbox](https://arxiv.org/html/2504.08385v2) is the closest validated
example of a fixed semantic corpus combined with inexpensive personalized
learning.

Its design:

- Encodes papers using public content embeddings.
- Trains one logistic-regression classifier per user from explicit upvotes and
  downvotes.
- Adds 5,000 randomly sampled unjudged papers as regularizing negatives.
- Uses active learning to request labels near and above the classifier's
  decision boundary.
- Scores newly published papers with the resulting classifier.

Its evaluation used approximately 800,000 explicit ratings from more than
14,000 users and a 1,233-participant user study. The system selected GTE-Large
embeddings after comparing GTE, SPECTER2, and TF-IDF. Reducing the dense
embeddings to 256 dimensions with PCA caused little degradation above that
threshold.

Transferable lessons:

- Personalized ranking over public embeddings does not require a large local
  model.
- Active labeling can learn useful distinctions from relatively few explicit
  judgments.
- Compact vectors can retain enough information for both semantic retrieval
  and local classification.

Parts that must not be copied directly:

- An unjudged item is not a negative under the Notedeck requirements.
- One classifier can entangle unrelated interests.
- A negative worth judgment must not automatically become a broad instruction
  to suppress semantically similar content.

### Xiaohongshu NoteLLM

[NoteLLM](https://arxiv.org/html/2403.01744v1) is the closest production example
of semantic item-to-item retrieval over short user-generated posts.

Its design:

- Starts from a 7B Llama 2 model.
- Compresses each note into one retrieval embedding.
- Constructs related-note pairs from one week of private co-click behavior.
- Uses contrastive learning to bring related notes together.
- Simultaneously learns to generate hashtags and categories so the embedding
  captures condensed concepts.

The disclosed training experiment used 458,221 notes, 312,564 training pairs,
and eight 80 GB A100 GPUs. Against a 257,937-note test pool, NoteLLM reported
84.02% Recall@100 versus 70.72% for its production SentenceBERT baseline. A
week-long production experiment reported a 16.2% click-through-rate increase
and improved exposure for new notes.

The important result is not that the oracle needs a 7B model. It is that
recommendation-aligned contrastive training substantially outperformed a
generic semantic encoder. Most of the gain came from behavioral pair training;
the hashtag/category auxiliary task added a smaller further improvement.

Its private co-click logs and compute footprint cannot be copied. Public Nostr
relations could eventually provide weaker supervision without crossing the
privacy boundary, but they lack impression and non-click evidence and are
exposed to popularity, spam, and selection bias.

### LinkedIn Feed Retrieval

[LinkedIn's disclosed retrieval system](https://ar5iv.labs.arxiv.org/html/2510.14223v1)
fine-tunes a shared Llama 3 dual encoder over member and post text.

Its relevant results:

- The experiment used five million member-item pairs and a 3B model.
- An unfine-tuned Llama representation achieved 0.2434 Recall@10 against the
  downstream ranker; InfoNCE fine-tuning achieved 0.4238.
- Adding two hard negatives per member improved Recall@10 by another 3.6%.
- Matryoshka training reduced 3,072-dimensional embeddings to 512 dimensions
  with almost no recall loss.
- Positive-only interaction history outperformed mixing positive history with
  non-engaged impressions.

This is strong evidence for recommendation-aware fine-tuning, curated labels,
hard-negative evaluation, and compact embeddings. It is not a feasible Nostr
architecture: the disclosed experiment trained on eight H100s, continuously
generated private member embeddings, and used large GPU fleets for embedding
and retrieval.

The remote member tower is also incompatible with the Notedeck boundary. The
device must retain the equivalent private state and final model.

### Pinterest PinnerSage

[PinnerSage](https://medium.com/pinterest-engineering/pinnersage-multi-modal-user-embedding-framework-for-recommendations-at-pinterest-bfd116b49475)
provides the strongest production precedent for preserving plural interests.

It:

- Clusters a person's actions into as many coherent interests as the data
  supports.
- Represents each cluster with an actual interacted item, its medoid, rather
  than averaging unrelated items into one vector.
- Samples a small number of medoids for nearest-neighbor retrieval.
- Separates long-term batch state from same-day state.

The current oracle already follows the essential lesson more conservatively:
each positive source event remains an independent query and results are fused
locally. Local clustering and medoid selection should be considered only when
query volume becomes expensive; querying every selected source remains the
quality reference.

### Semantic Scholar

The [Semantic Scholar Recommendations API](https://api.semanticscholar.org/api-docs/recommendations)
accepts positive and negative paper IDs and returns up to 500 recommended
papers. It establishes that example-item recommendation can be exposed as a
simple public retrieval service.

Its public documentation does not disclose enough about the current ranking
model or recommendation-quality evaluation to guide the oracle beyond the
better-documented Scholar Inbox findings.

## Privacy-Oriented Analogues

### Brave News

[Brave News](https://brave.com/brave-news/) distributes an identical compressed
public catalog to every client and ranks it from follows and browsing history
entirely on-device. It validates the information topology of shared public
content plus private local personalization.

It does not solve the Nostr candidate-discovery problem. Its catalog contains a
bounded set of recent articles from hundreds of sources, whereas a Nostr client
cannot download and rank the complete public corpus on a phone. No rigorous
recommendation-quality evaluation is public.

### Uni-FedRec

[Uni-FedRec](https://aclanthology.org/2021.findings-emnlp.124/) learns multiple
interest representations locally, uploads them for server-side candidate
retrieval, and ranks candidates locally.

This is architecturally close, but its uploaded interest representations are
private-derived personalized requests. Perturbing or decomposing those vectors
does not satisfy the current hard boundary. Querying independent public source
event IDs leaks access patterns but does not directly upload a synthesized user
profile.

## Generative Recommendation

[OneRec](https://arxiv.org/abs/2502.18965) and newer generative recommenders
replace explicit retrieval and ranking stages with transformers that decode
semantic item identifiers from long behavioral histories. They combine
semantic tokenization, large sequential models, preference optimization, and
continuous centralized training.

These systems may improve recommendation objectives at industrial scale, but
they are a poor fit for this oracle:

- Their primary signal is pooled private behavior.
- Training and serving require industrial GPU infrastructure.
- Semantic identifiers add a learned catalog-tokenization problem.
- Generative decoding does not eliminate corpus eligibility or personalization
  control; it hides both inside the model.
- Their reported engagement gains do not establish conscious personal value.

They should not be added to the MVP.

## Historical Comparison With the Earlier Oracle

The following table records the design that existed when this survey was
written. It is retained as research history and must not be used as the current
execution plan.

| Concern | Strong systems | Earlier oracle design | Historical assessment |
| --- | --- | --- | --- |
| Public item representation | Precomputed dense or semantic-ID representations | Native-INT8 dense vectors | Correct |
| Candidate computation | ANN or GPU nearest-neighbor retrieval at request time | Exact lazy cosine scan | Correct for low-volume oracle quality |
| Representation objective | Domain and behavior aligned | Generic semantic retrieval | Largest quality risk |
| Plural interests | Multiple embeddings or interest clusters | Independent source-event queries | Strong |
| Local personalization | Small classifiers through large sequential rankers | Similarity evidence and local fusion, not yet concrete | Needs an experimental local scorer |
| Compact vectors | PCA, Matryoshka, quantization | Full 1,024-dimensional INT8 vectors | Unnecessarily fixed |
| Hard distinctions | Impression hard negatives or explicit ratings | Human worth judgments in the bake-off | Evaluation exists; training use remains unresolved |
| Final ranking | Usually centralized | Local | Required advantage |
| Complete neighbor graph | Generally unnecessary | Explicitly omitted | Correct |
| ANN | Required at industrial QPS | Deferred | Correct |

## Historical Candidate Improvements

The following proposals were considered before the GTE-first decision. They
are not approved MVP work.

### 1. Matryoshka Dimension Bake-Off

The selected
[pplx-embed-v1-0.6B model](https://huggingface.co/perplexity-ai/pplx-embed-v1-0.6b)
natively emits INT8 embeddings and advertises Matryoshka support. Its
[training report](https://ar5iv.labs.arxiv.org/html/2602.11151) includes
128-, 256-, 512-, and 1,024-dimensional objectives for the 0.6B model family.

The bake-off should compare exact retrieval using every supported prefix:

| Dimensions | Raw vectors for 25M events |
| ---: | ---: |
| 1,024 | 25.6 GB |
| 512 | 12.8 GB |
| 256 | 6.4 GB |
| 128 | 3.2 GB |

This does not materially reduce the encoder's forward-pass cost. It can reduce
artifact transfer, resident memory, memory bandwidth per exact query, local
payload size, and ongoing service cost.

Full 1,024-dimensional exact search remains the recall reference. A second
serving experiment may scan a compact prefix over the complete corpus and
rerank a deep shortlist using the full vectors. The cascade is retained only if
it preserves worthwhile candidates relative to the exact reference.

### 2. Public Candidate Vectors for Local Learning

The public response should be able to include each candidate's compact vector
alongside its event ID and source-candidate score. A 1,000-candidate response
adds approximately 256 KB at 256 dimensions.

The local bake-off can then compare:

- Existing independent-source similarity and support.
- A strongly regularized linear scorer per active interest.
- A positive-only prototype when explicit negative evidence is insufficient.

No local LLM is required. Unjudged events remain neutral. An exact negative
worth judgment continues to exclude that event; broader model updates must
respect the separate instruction for changing future recommendations.

### 3. Independent Encoder Control

The 0.6B and 4B Perplexity encoders share a backbone family and training method.
Their agreement is not independent evidence that semantic retrieval has reached
its practical limit.

The earlier one-million-event bake-off proposal would have included one
independently trained encoder. GTE-Large was a defensible control because it
produced Scholar Inbox's strongest
explicit-rating results. It is not assumed to be the production choice. It
receives a full-corpus build only if it contributes material unique worthwhile
recall.

### 4. Active Human Labeling

Scholar Inbox demonstrates that active labeling near a model's uncertain region
can improve a small personalized model efficiently. The oracle can use this to
reduce labeling effort, but evaluation must retain a separately sampled holdout
so an actively selected pool does not masquerade as unbiased recommendation
quality.

### 5. Separately Gated Nostr Adaptation

If strong generic encoders omit worthwhile candidates, the next experiment is a
Nostr-adapted public encoder, not a larger local LLM.

A cost-bounded first attempt may train a small projection or adapter over the
0.6B representation using only public evidence such as event relationships and
kind `1` tags. It must:

- Use missing interaction as unknown, not negative.
- Prevent prolific users, authors, and popular events from dominating pair
  construction.
- Mask probable false negatives during contrastive training.
- Preserve content-based representations for zero-engagement events.
- Measure low-engagement and unknown-author recall separately.
- Win on unique worthwhile discovery before the full corpus is embedded.

Training and model selection occur before the only 25-million-event embedding
pass. A hard bake-off cap and measured end-to-end throughput are required; the
budget cannot be guaranteed from parameter count alone.

This experiment remains compatible with the public/private information
boundary, but not with the current meaning-only scope. It must be approved as a
separate hypothesis.

## Approaches Not Justified for the MVP

- A centralized user tower or uploaded private interest vector.
- A complete precomputed event-neighbor graph.
- ANN before exact search establishes the quality reference and measured QPS
  requires it.
- Generative semantic identifiers or end-to-end transformer recommendation.
- Mandatory pairwise reranking before dense candidate recall is known.
- Treating random or unobserved events as negative preference evidence.
- Pooling all interests into one vector or one undifferentiated user model.
- Selecting an encoder from general retrieval leaderboards alone.

## Resulting MVP Direction

The approved cost-constrained design is:

1. Calibrate GTE-Qwen2-7B-Instruct for compatibility and complete-build cost.
2. If the lifetime budget gate passes, build one versioned candidate/document
   representation over all `3,530,455` representable notes.
3. Expose `similar_notes` for positive-source candidate discovery and
   `vectors_for_notes` for same-version local comparison.
4. Train and freeze both approved local personalizers using private adaptive
   judgments.
5. Evaluate each frozen personalizer on its own `200` untouched
   recommendations using the direct approved pass/fail rule. Either may pass;
   the MVP does not select a winner first.

GritLM, a Nostr-adapted encoder, additional candidate sources, compact
representations, and serving optimizations require later evidence and separate
approval.
