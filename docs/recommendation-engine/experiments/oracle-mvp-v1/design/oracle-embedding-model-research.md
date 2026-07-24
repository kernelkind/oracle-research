# Oracle Embedding Model Research

> **Status:** Frozen record of the v1 embedding-model decision.

## Decision

The Oracle needs to answer this relation:

> Given a note, retrieve other notes related to the interests it expresses.

The first complete-corpus build will use
[GTE-Qwen2-7B-Instruct](https://huggingface.co/Alibaba-NLP/gte-Qwen2-7B-instruct),
provided a capped calibration shows that the complete build and evaluation fit
inside the remaining MVP budget.

The execution order is:

1. Run a small GTE calibration to measure cost and catch a catastrophically
   broken configuration.
2. If the budget gate passes, build GTE candidate representations for the
   complete eligible corpus.
3. Evaluate the complete retrieval-and-local-personalization system.
4. Stop if it succeeds.
5. Consider a complete [GritLM-7B](https://huggingface.co/GritLM/GritLM-7B)
   build only if GTE fails, Grit could plausibly explain that failure, the
   remaining lifetime budget permits it, and a separate decision approves it.

A small-corpus comparison must not be described as choosing the quality
winner. A valid direct quality comparison between GTE and Grit would require
complete-corpus artifacts for both. That expense is unnecessary unless the
first serious attempt fails.

## Why GTE Is the First Bet

No public model has been proven on the exact Nostr task. The decision therefore
uses the closest available evidence rather than pretending certainty.

GTE has the closest overall match to the intended system:

- Its query-side instruction tuning and unprompted document encoding fit the
  hybrid-lazy architecture. Corpus notes are encoded once as candidates; a
  selected source note can be encoded lazily as a query.
- A 2025 controlled study of training-free cold-start recommendation found
  text-embedding models stronger and more scalable than direct LLM reranking,
  with GTE-Qwen2-7B the strongest tested embedding model on average. This is
  unusually close to the Oracle's use of public text without behavioral
  training data.
- GTE also outperforms Grit on the MTEB MIND-small news-recommendation task.
  That task is imperfect, but it is more relevant than a generic retrieval
  leaderboard.

The evidence has important limits. The cold-start study ranks only a small
candidate set, uses random distractors, and appears to apply a query prefix to
candidate items. MIND contains Microsoft News data, and GTE's training data
includes Microsoft News title/body pairs, so domain overlap may help its score.
These results justify the first bet; they do not prove the Nostr result.

Sources:

- [GTE-Qwen2-7B-Instruct model card](https://huggingface.co/Alibaba-NLP/gte-Qwen2-7B-instruct)
- [Are Large Language Models Really Effective for Training-Free Cold-Start Recommendation?](https://arxiv.org/abs/2512.13001)
- [MIND: A Large-scale Dataset for News Recommendation](https://aclanthology.org/2020.acl-main.331/)

## Why Grit Is the Fallback

GritLM-7B has the strongest competing evidence for large candidate sets and
complex intent. The BLaIR recommendation benchmark reports strong Grit results
on Amazon-C4 and Reddit-Movies and finds that generic MTEB rank has little
correlation with recommendation performance. This is a reason to retain Grit
as a serious alternative, and a reason not to select a model from a generic
leaderboard alone.

Grit is not the first build because its closest recommendation evidence is
mixed: BLaIR exposes failures on some nuanced preference descriptions, while
GTE has the stronger direct liked-item and news evidence. If GTE fails, Grit's
different training and instruction behavior make it the most meaningful model
choice to revisit.

Sources:

- [Generative Representational Instruction Tuning](https://arxiv.org/abs/2402.09906)
- [Bridging Language and Items for Retrieval and Recommendation](https://arxiv.org/abs/2403.03952)

## Other Models Considered

- **TwHIN-BERT-large** has the most relevant social-post training. It learned
  from seven billion tweets and socially similar tweet pairs mined from public
  engagement structure. However, the released checkpoint does not include the
  contrastive projection head used by the social objective, and raw
  checkpoint-cosine retrieval is not validated. It is at most an optional
  zero- or near-zero-cost sanity probe, not a complete-corpus candidate.
- **pplx-embed-v1-4B** is an efficiency fallback. Its strongest adjacent
  result groups search queries that led to the same URL. That tests shared
  search intent more directly than broad interest-related note discovery.
- **QZhou-Embedding** is misaligned. Its training treats different aspects of
  one topic as hard negatives, while the Oracle explicitly wants related
  interests rather than only paraphrases.
- **Nemotron-3-Embed-8B** and **Harrier-27B** are strong generic retrieval
  models, but neither has enough recommendation-specific evidence to displace
  GTE or Grit. Harrier also makes the one complete-corpus pass materially more
  expensive.
- Recommendation-specialized systems such as NoteLLM and UniNote are
  architecturally relevant, but usable trained weights and data are not
  available for this experiment.

Source for the social model:

- [TwHIN-BERT](https://arxiv.org/abs/2209.07562)

## What a Small Run Can Establish

A small run can establish:

- that the exact model revision and query/document formatting execute;
- that vectors, scores, and rankings are numerically valid;
- that `vectors_for_notes` returns byte-identical stored candidate/document
  rows in batches and rejects missing or incompatible representation versions;
- that the chosen instruction is not catastrophically misaligned;
- measured throughput, memory use, artifact size, query cost, and projected
  complete-corpus cost.

It cannot establish which model gives better complete-corpus recommendations.
A small corpus contains fewer true related notes and fewer difficult false
matches. Expanding to the complete corpus changes both sides of the ranking
problem, so relative model quality can reverse.

The small run is therefore a cost calibration and catastrophic sanity check,
not a bake-off. External evidence chooses the first model; the complete MVP
evaluation determines whether that model is good enough.

## Still Unresolved

Before renting hardware, the actionable calibration task must freeze:

- the exact GTE revision and query instruction;
- pooling, normalization, storage precision, and retrieval implementation;
- the representation manifest, serialization, and missing-event and
  version-mismatch behavior shared by `similar_notes` and
  `vectors_for_notes`;
- the representative production batches and automatic stop conditions;
- GPU choice and maximum calibration spend;
- the conservative complete-build projection and failure reserve.

None of these unresolved implementation choices reopen the approved model
execution order.
