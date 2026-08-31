# General Semantic Recommendation Systems

Research date: 2026-07-11

## Purpose

Record published evidence about semantic recommendation systems. This is
background for the separate recommendation problem; it does not prescribe the
current user-directed subject hierarchy or an active MVP experiment.

## Conclusion

The retained research findings are:

- Public item representations can support inexpensive per-user learning.
- Recommendation-trained representations often outperform generic semantic
  embeddings on their own objectives.
- Multiple interest representations avoid collapsing unrelated tastes.
- Private local ranking remains technically plausible, but the reviewed
  systems do not establish its quality for Nostr notes.

These findings concern recommendation systems. They do not define the atomic
subjects, fine segmentation, or hierarchy used by the current content-discovery
direction.

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

