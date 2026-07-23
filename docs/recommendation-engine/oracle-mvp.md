# Recommendation Oracle MVP

## Goal

Test one question:

> Can the strongest affordable public semantic Oracle and a private local personalizer together produce a general kind `1` feed that this person is consciously glad to see?

The MVP is an existence test. Semantic similarity alone is not a recommendation, so the test includes both candidate discovery and local personalization. It does not attempt to prove population-wide quality, optimize a production client, or identify the final decentralized deployment architecture.

The final result is based only on each frozen personalizer's own `200` untouched recommendations rated on the frozen `1`–`7` gladness scale. A personalizer passes when:

- The mean rating is at least `5`.
- No more than `20` ratings are `1` or `2`.

The MVP passes if either personalizer passes and fails if neither passes. There is no winner selection, external-feed comparison, control feed, confidence interval, or ambiguous quality verdict.

## Separation of Responsibilities

The Oracle analyzes only public Nostr data. It owns the public corpus, public representations, and deterministic semantic retrieval. It never receives private ratings, positive or negative labels, the complete profile, local scores, or the final feed order.

The local personalizer owns all private state. It decides which positive notes to use for candidate discovery, interprets positive and negative evidence, ranks candidates, prevents repetition, and constructs the feed.

For the offline MVP, both components may read local files on the same machine. The logical boundary remains the same:

```text
PUBLIC ORACLE
  public kind 1 corpus
  candidate/document vectors
  similar-notes retrieval
  vector lookup
           │
           │ public IDs, retrieval scores, and vectors
           ▼
PRIVATE PERSONALIZER
  ratings and profile
  candidate-to-profile comparisons
  local ranking and feed construction
```

The MVP has no network service, authentication, relay protocol, or NIP. Those are later deployment questions.

## Corpus

The canonical MVP corpus contains `3,530,470` notes from the April 2025 Damus snapshot. A note is included only when it has already passed the approved pipeline:

- Valid root kind `1` event.
- Not a reply or quote note.
- English-eligible.
- At most `512` tokens under the frozen corpus gate.
- Exact-content deduplication, retaining the event with the lexicographically lowest ID.

The corpus includes raw note content and URLs. The MVP never fetches or analyzes URL targets, linked notes, images, video, audio, or webpages. It does not use follows, reactions, popularity, author reputation, or collaborative behavior.

Fifteen canonical events have no text after trimming and therefore cannot be encoded. Their IDs are explicitly recorded as exclusions in the semantic-order artifact. The complete representation consequently contains `3,530,455` notes. No other model-specific filter may silently redefine the corpus.

The represented event IDs, row order, exclusions, and checksums are fixed before the complete embedding build.

## Public Representation

The first complete-corpus attempt uses [GTE-Qwen2-7B-Instruct](https://huggingface.co/Alibaba-NLP/gte-Qwen2-7B-instruct) at immutable revision `a8d08b36ada9cacfe34c4d6f80957772a025daf2`. External recommendation-specific evidence currently gives it the strongest justification for the first serious attempt; generic embedding leaderboards do not reliably predict recommendation retrieval quality. The supporting model review is recorded in [oracle-embedding-model-research.md](./oracle-embedding-model-research.md).

Every represented note receives one stored candidate/document vector. `similar_notes` lazily encodes only the requested source note in the model's query role and compares it with the stored candidate/document matrix. Query and candidate encodings may differ.

Candidate/document input is the unchanged raw note content with no instruction or chat template. Query input is exactly:

```text
Instruct: Given a note, retrieve other notes related to the interests it expresses
Query: {raw note content}
```

Both roles use the tokenizer pinned to the same model revision, official last-token pooling, and L2 normalization. Model inference, pooling, normalization, and the complete `3,584`-dimensional stored output all use FP32. The encoder must not truncate, split, summarize, preprocess, reduce, quantize, enable TF32, or lower the inference or storage precision of the note or vector.

The runtime is the direct PyTorch and Transformers model path with pinned software and container identities. It does not use Sentence Transformers, ONNX, vLLM, TEI, an inference server, FlashAttention, or another exported or reduced-precision execution path. Those components do not improve the representation being tested and would create additional behavior to validate.

FP32 is authoritative because the experiment tests whether the strongest affordable system can work, not whether its computation or vectors can be compressed. The calibration projects this exact FP32 system first. If that conservative projection fits within the lifetime budget, no reduced-precision comparison runs. Lower inference or storage precision may be considered only if the FP32 system would prevent the complete experiment from fitting the budget, and only through a separate explicit decision before complete-corpus work.

## Oracle Interface

The Oracle exposes exactly two logical operations:

```text
similar_notes(note_id, depth, representation_version)
    -> candidate event IDs, ranks, directional retrieval scores,
       corpus version, and representation version

vectors_for_notes(note_ids[], representation_version)
    -> stored candidate/document vector and representation version
       for each included event ID
```

`similar_notes` loads one included note's canonical text, computes its FP32 query-role vector, searches every candidate/document shard, deterministically merges the shard-local results into one exact ranking, and excludes the source event. A missing or excluded event returns `not_found`. Each request remains logically independent; the Oracle never combines query vectors, scores, or sources and never estimates personal value. The local implementation may co-schedule multiple already-requested calls in one physical matrix pass while preserving a separate exact response for each call.

`vectors_for_notes` performs a batched event-ID-to-row lookup. It returns the requested stored FP32 rows unchanged; it does not re-embed the notes or scan the complete corpus. This lets the personalizer fetch and cache only the profile and candidate vectors it needs.

The paid calibration produced shard `157`; it did not exercise the Oracle operations. The free CREC-72 preflight subsequently exercised both operations through the exact frozen controller, model, and calibrated shard on a disposable local copy. It proved stored-vector lookup, real query-role encoding, exact scan, source exclusion, and ranked output without changing the source artifact. That partial-shard smoke validates behavior only; it is not a complete-matrix latency or recommendation-quality result.

A `similar_notes` score is directional query-to-candidate retrieval evidence. Local personalized comparisons use same-role candidate/document vectors returned by `vectors_for_notes`. They must not treat an asymmetric retrieval score as a symmetric kernel, and absence from a bounded `similar_notes` response is unknown rather than zero similarity.

Text-query retrieval is not part of the MVP. The five initial positive notes are chosen manually. Preserving the exact model and artifact may make text queries possible later without rebuilding the candidate matrix, but that possibility adds no current operation or requirement.

## Artifact Contract

The corpus's existing ordered event-ID artifact defines vector row order. Vector data is stored as immutable FP32 shards over fixed, non-overlapping row ranges. A completed calibration shard is therefore already a verified part of the complete artifact rather than a disposable sample or a second format.

A compact event-ID-to-row lookup supports batched `vectors_for_notes` requests without scanning the ordered IDs or duplicating note content. The artifact contains no neighbor graph, ANN index, or copy of the corpus text.

One manifest records the corpus and ordered-ID hashes, model revision, exact query instruction and roles, pinned runtime identities, dimension, FP32 format, shard row ranges, and shard checksums. The hash of that manifest is the `representation_version`. Only completed, checksum-verified shards appear in a published manifest.

## Representation Compatibility

One `representation_version` binds:

- Model revision.
- Tokenizer and preprocessing.
- Query instruction and query role.
- Candidate/document role.
- Pooling, dimension, and normalization.
- Numeric and serialization formats.
- Corpus artifact and row mapping.

Every response identifies this version. Missing or mismatched vector requests are rejected. The personalizer must never mix versions.

The same complete Oracle artifact and `representation_version` used during personalizer learning must also be used for the direct final evaluation of both frozen personalizers. A model, corpus, preprocessing, or representation change creates a different experiment.

## Lazy Retrieval

The MVP does not precompute a neighbor graph. It stores one candidate/document vector per corpus note and computes a query only when `similar_notes` is called.

Given the same corpus, representations, and score calculation, exact lazy search returns the same result as computing that source's graph row in advance. It avoids paying to compute rows that the private profile never requests.

The MVP uses exact dense search. Its small query volume does not justify an approximate index or its recall risk. Matrix shards can be searched independently and their local top results merged, so the build remains resumable without materializing note-to-note relationships.

The full-corpus scanner opens the verified FP32 matrix through a persistent memory mapping rather than opening, allocating, decoding, and revalidating one vector for every row of every query. Stored rows are checksum- and format-verified when the completed artifact is opened; the search path reads them directly in contiguous blocks.

At the start of each adaptive-learning wave, collect every newly available, uncached positive-source request from both personalizers. Encode each source independently in the approved query role, then scan every candidate block once and compare that block with all of the wave's query vectors using the frozen FP32 blocked-matrix calculation. Maintain a separate bounded top-`1024` heap for each logical request, then deterministically sort and merge that request's winners. Cache each response by `(representation_version, source_event_id, depth)` so it is never searched twice.

Batching changes only execution scheduling. It does not average queries, share scores, alter candidate depth, introduce an approximate index, or create a third Oracle operation. With the five initial seeds followed by ten adaptive rounds, recommendation retrieval requires at most one complete matrix pass in each of eleven query waves instead of one complete pass for every positive source. The block size, FP32 score calculation, top-`k` behavior, and tie ordering are frozen before the experiment so repeated requests remain deterministic.

## Candidate Discovery and Local Evidence

The local profile retains every rated whole note as independent evidence:

- Positive notes are weak evidence for nearby content.
- Negative notes are weak local counterevidence.
- Distant examples contribute nothing.
- Repeated nearby agreement strengthens support.
- Nearby positive and negative evidence creates conflict or uncertainty.
- Unjudged notes remain neutral.

Every positive profile note independently calls `similar_notes`. The union of those results is the candidate pool. Negative profile notes do not generate candidates.

For adaptively rated notes, ratings `5`–`7` become positive candidate sources in later rounds, `4` remains neutral, and ratings `1`–`3` provide negative evidence without calling `similar_notes`. The signed weight `(rating - 4) / 3` preserves strength: `7` contributes three times the positive weight of `5`, and `1` contributes three times the negative magnitude of `3`.

The personalizer then calls `vectors_for_notes` for the unique profile notes and candidates it has not already cached. It calculates every candidate-to-profile comparison locally. This preserves disconnected interests without named topics, extracted preferences, a single global user vector, or a language-model personalizer.

The underlying family is instance-based relevance feedback. Prior work supports retaining individual positive and negative examples and using local similarity-weighted evidence:

- [A Personal News Agent that Talks, Learns and Explains](https://www.ics.uci.edu/~pazzani/Publications/agents99-news.pdf)
- [Using Topic Models in Content-Based News Recommender Systems](https://aclanthology.org/W13-5622.pdf)
- [Instance-Based Relevance Feedback for Image Retrieval](https://papers.nips.cc/paper_files/paper/2004/file/5acdc9ca5d99ae66afdfe1eea0e3b26b-Paper.pdf)
- [Incorporating Relevance Feedback for Information-Seeking Retrieval using Few-Shot Document Re-Ranking](https://aclanthology.org/2022.emnlp-main.614.pdf)

This evidence justifies the experiment. It does not establish that the selected Nostr embedding geometry preserves what predicts this person's value.

## Personalizer Learning

Two approved personalizers learn independently and are then evaluated directly:

1. Adaptive compact-support kernel regression.
2. Zero-mean RBF kernel ridge regression.

Both operate on the same versioned candidate/document vectors. The first directly aggregates nearby independent evidence; the second jointly fits a regularized nonlinear preference landscape. Their exact equations, hyperparameter rules, support rules, candidate depth, hub handling, non-redundant batch construction, tie-breaks, and reserve accounting are frozen before any benchmark rating is collected.

The approved learning flow is:

1. Manually select the same five distinct positive corpus notes for both algorithms. Rate each seed once on the approved `1`–`7` scale, require positive evidence, and convert it with `(rating - 4) / 3`.
2. Give each algorithm an independent profile initialized with the same five weighted seeds.
3. For each of ten rounds, each algorithm independently freezes `20` valid recommendation choices plus its required reserve from its current profile.
4. Merge and deduplicate the two lists for presentation, hide algorithm provenance, and present the unique notes in one frozen shuffled order.
5. Rate each eligible note once on the approved `1`–`7` scale. Route that rating only to the algorithm or algorithms that selected it.
6. After the complete merged round is rated, update each algorithm using only its own `20` choices and the frozen signed-evidence rule `(rating - 4) / 3`.
7. Repeat until each algorithm has received `200` adaptive learning ratings.

Learning therefore requires at most `400` unique valid ratings. Overlap reduces the number of notes the evaluator must see without merging the algorithms' profile states.

After learning:

1. Freeze both algorithms and their independently learned profiles.
2. Freeze each algorithm's selected parameters and update rule.
3. Hand both frozen systems and the complete presentation ledger directly to final evaluation.

There is no comparison phase, winner selection, winner-only final, or second learning phase.

## Presentation and No-Repeat Rules

The runner maintains one experiment-wide presentation ledger keyed by event ID.

- It begins with the five seed IDs.
- An ID is recorded immediately when first displayed, including a note marked `wrong_language`.
- No recorded ID is ever displayed again during learning or final evaluation.
- If both algorithms select the same note, it is displayed once and the same rating is routed to both.
- If an algorithm later selects a note already rated for the other algorithm during learning, the stored rating may be reused internally without displaying it again.
- Final choices must be fresh and exclude the complete ledger before their orders are frozen.
- An unused reserve item is not recorded merely because it was in a reserve; only presentation adds it to the ledger.

Candidate processing never constructs a complete diversity-filtered order for the whole pool. Each algorithm freezes only its required quota plus the finite reserve allowed by the phase's `5%` wrong-language ceiling, then stops. Anything beyond that bounded primary-plus-reserve order cannot be presented in a valid run and is not processed.

This is an experiment no-repeat rule, not synchronized product seen state.

The evaluator sees the raw kind `1` content, including URLs and Nostr identifiers, but does not open, follow, preview, or render them. Every successfully displayed eligible raw note must be rated. There is no unavailable-context or unjudgeable status. If the raw event itself cannot be displayed, the run pauses on that event instead of silently replacing it.

A note that is clearly primarily non-English receives `wrong_language`:

- It receives no rating or profile weight.
- It does not consume a valid-rating position.
- Its ID remains in the no-repeat ledger.
- The runner advances only through the already frozen reserve; it does not re-query or rerank in response.

Mixed-language, code-heavy, and ambiguous notes remain eligible and must be rated. Every `wrong_language` presentation is reported. Each phase's finite reserve is the largest number of replacements that could occur without exceeding `5%`, using that phase's maximum unique valid presentations; a longer reserve could not rescue a valid result. More than `5%` `wrong_language` outcomes during adaptive learning pauses the experiment as a corpus-filter failure, and more than `5%` over all notes presented in the final phase prevents a valid quality verdict.

## Direct Final Evaluation

The final phase receives directly from adaptive learning:

- Both frozen algorithms and update rules.
- Both independently learned frozen profiles.
- The complete presentation ledger.
- The exact complete Oracle artifact and `representation_version` used during learning.

Each personalizer independently generates and freezes a bounded fresh order of `221` accepted events: `200` recommendations and `21` wrong-language reserves. Every event ID must be distinct and outside the complete seed and learning presentation ledger, including prior `wrong_language` notes.

Merge and deduplicate both personalizers' initial claims, conceal provenance, and present the unique events in one frozen shuffled order. An event claimed by both is shown and rated once, and that rating counts in each personalizer's own result set. Advance through only the affected personalizer's frozen reserve after `wrong_language` until both have exactly `200` valid ratings.

For every note, the evaluator answers:

> Considering the attention it required, how glad are you that you saw this note?

The anchored scale is:

- `1`: Actively wish it had not been shown.
- `2`: Clearly not worth seeing.
- `3`: Little personal value.
- `4`: Indifferent.
- `5`: Mildly glad to have seen it.
- `6`: Clearly glad; personally valuable.
- `7`: Exceptionally valuable.

No final rating updates either profile, changes either algorithm, selects between the personalizers, alters either frozen order, or affects later recommendations.

Report each personalizer's mean, full rating distribution, count and percentage rated `1`–`2`, wrong-language rate, artifact provenance, and pass/fail result. A personalizer passes when its mean is at least `5` and no more than `20` of its ratings are `1` or `2`. The MVP passes if either personalizer passes and fails if neither passes. Learning results are reported separately as development evidence.

## Capped GTE Calibration

The MVP has a hard `$500` lifetime paid-compute ceiling. Every rental and paid operation draws from the same ledger. The objective is to give the hypothesis one strongest affordable complete-corpus attempt without risking the ceiling.

The calibration and admitted complete build use one full [RTX PRO 6000 Blackwell Workstation Edition](https://www.nvidia.com/en-us/products/workstations/professional-desktop-gpus/rtx-pro-6000/) GPU in on-demand mode. Its `96 GB` of ECC VRAM provides headroom for strict FP32 inference and can hold the roughly `47.26 GiB` complete vector artifact alongside the FP32 model when useful. Current Vast.ai value, true FP32 throughput, and memory capacity make it the strongest single-GPU fit; no paid hardware comparison runs.

The exact Vast.ai offer is selected immediately before rental rather than recorded in advance. It must provide the full GPU, a `600 W` power limit, verified status, at least `99.5%` reliability with `99.9%` preferred, at least `128 GB` host RAM, at least `200 GB` local NVMe storage with `1 GB/s` measured bandwidth, NVIDIA driver `580.95.05` or newer, sufficient available duration, and acceptable storage and transfer prices. If no offer meets the frozen requirements, no substitute GPU is rented. A different GPU class requires a separate decision; a material host change requires calibration revalidation.

The production image derives from the official PyTorch `2.12.1-cuda13.0-cudnn9-runtime` image for Linux AMD64 at immutable digest `docker.io/pytorch/pytorch@sha256:72f863fa1fe13d5d87a72d00db2c85fb2d43409ee08dd26bc469de4c8a28b427`. It provides Python `3.12`, PyTorch `2.12.1`, and CUDA `13.0.2`. The derived image pins `transformers==4.41.2`, matching the model configuration, plus a complete hash-locked dependency set. Its final image digest is frozen after the local build and dry run.

Model execution uses `attn_implementation="eager"`, `torch.float32`, `model.eval()`, `torch.inference_mode()`, and `use_cache=False`. PyTorch's global, CUDA-matmul, and cuDNN FP32 precision controls are set to `ieee`; deterministic algorithms are enabled and verified by repeated fixed-input inference. FlashAttention, autocasting, quantization, compilation, inference servers, and mutable runtime installation are absent.

Before any rental, the current actionable calibration-design task must freeze:

- Exact PyTorch, Transformers, CUDA, dependency, and container identities, plus the FP32 numeric format and serialization for the approved GTE encoding contract.
- The manifest-derived `representation_version`, immutable FP32 shard layout, event-ID-to-row lookup, and missing-event and mismatch rejection rules.
- Both `similar_notes` and batched `vectors_for_notes` calibration paths.
- The token-length ranges and number of real production batches measured for each range in one capped calibration run.
- The exact qualifying RTX PRO 6000 WS offer, the `$25` lifetime calibration cap, automatic termination, and failure allowance.
- Measurements and the conservative admission calculation for exactly one complete GTE build.

Before paid model execution, the exact GTE tokenizer audits all `3,530,455` represented notes locally. This records the complete input-length distribution, defines the calibration's length ranges, and rejects a configuration that would truncate or fail to encode any represented note.

Before any rental, the pinned production container and production code are dry-run locally as far as the hardware permits. This includes the complete tokenizer audit; real CPU model loading and a tiny query/document encoding smoke test; pooling, normalization, and FP32 serialization; shard creation, checksums, interruption and resume; `similar_notes`; `vectors_for_notes`; representation-version rejection; and both budget gates. The rental must not be used to debug hardware-independent behavior. Only CUDA and driver compatibility, GPU numerics, VRAM, throughput, power, paid-host I/O, and cost remain rental-only measurements.

Local execution remains the default throughout the MVP. Model and container downloads and hashing, corpus analysis, shard planning, indexes and manifests, tests, artifact verification, exact scanning, vector lookup, personalization, and evaluation run on this machine whenever practical. Lazy query encoding is attempted locally before any paid evaluation-time execution is admitted. The rental is used only for the corpus-wide GTE forward pass and work that must validate or measure the exact GPU host. It is terminated as soon as the required GPU work and artifact transfer are verified; no operation moves to the rental merely for convenience.

The rental launches directly from the private production Docker image by immutable digest; no Vast template is used. The read-only registry credential is supplied only for that launch. The compressed corpus and checksum-pinned control bundle are transferred from this machine. The exact public model revision is downloaded on the rental, verified file-by-file against the transported payload identity, and restored to the frozen cache metadata required by the production verifier before any model execution.

The paid calibration has a `$25` lifetime cap across all calibration attempts, including failures. Reaching the cap terminates calibration automatically. It processes several real production batches from every defined length range through the exact build path. It does not precommit to an arbitrary total such as `100,000` notes, repeat projection rounds, or require a convergence procedure. Every generated vector is written into an immutable, checksum-verified shard that remains part of the complete artifact.

For each length range, the projection applies its measured end-to-end production cost to the audit's exact count of corpus notes in that range, then sums the ranges and complete pipeline overhead. The budget gate adds actual spend, artifact storage and transfer, any evaluation-time lazy inference shown to be impractical locally, one cold restart, and one lost shard. The measured machine, model configuration, batching, and artifact format must match the proposed build; a material machine change requires revalidation. If any required range cannot run or the provider-enforced calibration cap is reached, no complete build is admitted.

The capped calibration may establish only that:

- The production encoding, serialization, exact retrieval, and batched vector lookup work.
- Looked-up vectors are byte-identical to their stored candidate/document rows.
- Roles and representation versions are correct and incompatible requests are rejected.
- Vectors and scores are numerically valid and the configuration is not catastrophically broken.
- Measured throughput, memory, artifact size, lazy-query cost, and total rental cost support a conservative complete-corpus projection.

It does not compare recommendation quality on a partial corpus or choose between models. A partial corpus has fewer potentially useful notes and fewer hard false matches, so its recommendation result cannot settle complete-corpus quality.

Only when the completed calibration and conservative remaining-work projection fit within the lifetime budget may one complete GTE build be separately approved:

```text
actual spend
+ conservative remaining corpus build
+ artifact storage and transfer
+ any evaluation-time lazy inference shown to be impractical locally
+ one cold restart
+ one lost shard
<= $500
```

The per-range measurements include loading, tokenization, padding, model execution, normalization, serialization, checksums, and checkpoint overhead. Production shards are immutable and resumable so a stopped rental does not require recomputing completed rows.

[GritLM-7B](https://huggingface.co/GritLM/GritLM-7B) is only a conditional fallback. It may be considered after the complete GTE system fails the final evaluation, model choice plausibly explains that failure, sufficient lifetime budget remains, and a separate decision explicitly approves the expense. It is not calibrated or built in parallel.

## What the Result Means

A pass shows that this public semantic representation and private local-personalization approach can produce a compelling finite feed for this evaluator, corpus, and frozen configuration. It justifies continuing toward a private decentralized product.

A fail shows that the strongest approved attempt did not meet the MVP goal. The retained retrieval, learning, and final-rating evidence may help distinguish candidate-recall, embedding-geometry, or local-ranking problems, but no diagnostic changes the predeclared result.

Neither outcome establishes quality for every person or proves that future models, corpora, or personalization methods cannot do better.

## Deliberately Deferred

- A network service, authentication, relay requests, or a NIP.
- Query unlinkability and transport privacy.
- Text-query retrieval or generated private topic queries.
- Replies, quote notes, conversational context, multimedia understanding, or URL dereferencing.
- Follows, reactions, public behavior maps, collaborative filtering, or public quality priors.
- A complete neighbor graph, ANN index, product quantization, or reranker.
- Population-wide evaluation, cold-start optimization, and production device constraints.
- Live ingestion and index updates.
- Any representation or retrieval path for notes excluded by the MVP corpus gates.

These become relevant only after the complete Oracle, independent local-personalizer learning, and direct untouched evaluation of both frozen systems have answered the MVP existence question.
