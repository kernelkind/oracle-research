# Nostr Semantic Recommendation Prior Art

Research date: 2026-07-11

## Conclusion

Semantic retrieval over Nostr events has been implemented several times. The core mechanics are established: embed notes, retrieve semantic neighbors from text or another vector, and update an interest vector from feedback.

No project found publicly demonstrates a broad, high-quality Nostr recommendation system meeting our requirements. The unsolved problem is recommendation quality at realistic Nostr scale, not vector-search plumbing.

## Existing Implementations

### Nostr Recommendation Algorithm

[NRA](https://github.com/garyokeeffe/NRA) is the closest direct predecessor found.

It:

- Fetches 3,000 Nostr notes.
- Embeds them and stores them in ChromaDB.
- Initializes one interest vector from the mean embedding of 20 notes authored by the user.
- Retrieves nearby notes.
- Moves the interest vector toward a note after positive feedback and away after negative feedback.

This demonstrates almost exactly the basic semantic-recommendation primitive. It remains a small experiment with no realistic corpus, deployment, or recommendation-quality evaluation.

Sources: [main pipeline](https://github.com/garyokeeffe/NRA/blob/main/main.py), [initial interest vector](https://github.com/garyokeeffe/NRA/blob/main/helpers/misc_helpers.py), [vector retrieval](https://github.com/garyokeeffe/NRA/blob/main/api_wrappers/chromadb_wrapper.py).

### Seekstr

[Seekstr](https://github.com/9qeklajc/seekstr) implements semantic search over Nostr events:

- Incoming events are embedded using `nomic-embed-text`.
- Embeddings and event metadata are stored in LanceDB.
- A free-text `/search` request is embedded and returns nearby Nostr event IDs.

It is a concrete implementation of text-to-Nostr-event semantic retrieval. No public broad corpus, deployed endpoint, usage evidence, or quality evaluation was found.

Sources: [search service](https://github.com/9qeklajc/seekstr/blob/main/lancedb-search/src/bin/main.rs), [embedding and retrieval path](https://github.com/9qeklajc/seekstr/blob/main/lancedb-search/src/embedding_service.rs).

### Socrates

[Socrates](https://github.com/coracle-social/socrates) is a kind-5300 DVM demonstration that embeds Nostr events with `all-MiniLM-L6-v2`, stores them in ChromaDB, and retrieves documents for a free-text request.

Its default configuration fetches only ten kind-1 events from one relay. It demonstrates the DVM integration and retrieval mechanics, not a usable corpus or recommendation system.

Sources: [pipeline description](https://github.com/coracle-social/socrates), [default configuration](https://github.com/coracle-social/socrates/blob/master/config.yaml).

### Nostr Paper Platform

[Nostr Paper Platform](https://github.com/outlaw-dame/nostr-paper-platform) contains an actual semantic NIP-50 implementation:

- `all-MiniLM-L6-v2` produces 384-dimensional embeddings.
- Event embeddings are stored with pgvector.
- Search requests are embedded at query time.
- Lexical and semantic rankings are combined using reciprocal rank fusion.

The repository describes the platform as a transition scaffold. No public deployment, corpus size, or retrieval-quality evaluation was found.

Sources: [search path](https://github.com/outlaw-dame/nostr-paper-platform/blob/main/services/search-api/src/main.ts), [embedder](https://github.com/outlaw-dame/nostr-paper-platform/blob/main/packages/semantic-embedder/src/index.ts).

### Fediway and CommonFeed

[Fediway Feeds](https://github.com/fediway/feeds) is the closest architectural predecessor. It is a cross-protocol provider that indexes public ActivityPub, AT Protocol, and Nostr content. Its live discovery document advertises a recommendation endpoint that accepts a caller-supplied interest vector.

[CommonFeed](https://github.com/fediway/commonfeed) specifies that:

- Engagement is processed by the consumer.
- The consumer constructs the interest vector locally.
- Requests contain no user identifier or history.
- The provider must not retain the interest vector after the request.

This independently establishes the architecture of private interest aggregation followed by public vector retrieval.

It does not establish that our goal has been solved:

- It is cross-protocol rather than a Nostr-specific corpus.
- Its current method collapses interest into one vector.
- Its current method does not support negative signals.
- Posts are embedded only after their first observed engagement, excluding zero-engagement content from retrieval.
- No public corpus size or recommendation-quality evaluation was found.
- The advertised `protocol` filter is parsed, but the current request path passes only language and recency into the Qdrant query. The live endpoint therefore cannot be assumed to return Nostr-only results.

Sources: [provider](https://github.com/fediway/feeds), [local aggregation and privacy method](https://github.com/fediway/commonfeed/blob/main/guidelines/embeddings/ema0.1.md), [engagement-gated embedding](https://github.com/fediway/feeds/blob/main/workers/orbit/src/main.rs), [filter definition](https://github.com/fediway/feeds/blob/main/crates/algorithms/src/posts/recommended.rs), [request path](https://github.com/fediway/feeds/blob/main/apps/server/src/routes/posts.rs), [live discovery document](https://feeds.fediway.com/.well-known/commonfeed).

## Evidence of Recommendation Quality

No credible public evidence was found that people consider the recommendations from these systems good. Public interest in an architecture or product does not establish that its output is valuable.

For our goal, recommendation quality means that a person considers each result worth seeing. Repository stars, screen time, engagement, praise for the user interface, and successful API requests do not establish this.

### Systems Without User-Quality Evidence

- NRA is an author-operated experiment with no release, user study, benchmark, or independent account of recommendation quality. Its public [Nostr announcement](https://nostr.com/nevent1qqsy7dp4frv8vnjfgtd9vpgmmrm5swp6gjc26x0k3jfpxfzcpezl8rgzypldr8nw3ukm0l5st3s67m7x8ctj75e26v0ylketszu8q05a7f4dvslv66y) received no substantive external evaluation.
- Seekstr is a semantic-search backend, not a personalized recommendation product. No public deployment, users, or relevance evaluation was found.
- Socrates is explicitly a pipeline demonstration over a trivial default corpus, not a consumer product.
- Nostr Paper Platform is semantic-search infrastructure, not a personalized feed. No public deployment or retrieval evaluation was found.

These systems establish implementation feasibility only.

### Fediway Beta

Fediway is the only system found with meaningful public user exposure. Its Mastodon instance currently reports 12 monthly active users through its [public instance API](https://fediway.com/api/v2/instance).

For a user with an interest vector, its current home feed allocates approximately:

- 60% to the user's network.
- 30% to personalized recommendations from CommonFeed providers.
- 10% to trending content.

A user without an interest vector receives no personalized allocation. Source: [Fediway home-feed implementation](https://github.com/fediway/fediway/blob/main/apps/server/src/feeds/timelines/home.rs).

Public beta feedback provides weak and ambiguous signals:

- One user said their [screen time was increasing](https://fediway.com/api/v1/statuses/116410556976744664).
- Several users praised the interface and animations.
- One user reported an [empty timeline after signing in](https://fediway.com/api/v1/statuses/116407308112882864).
- Another reported [receiving the same post when reloading](https://fediway.com/api/v1/statuses/116404400860198757).

None of the public feedback says that the personalized recommendations were relevant, surprising, consistently useful, or worth seeing. Increased screen time does not demonstrate personal value and is not our objective. Early interface and feed failures also do not establish that the underlying retrieval is poor; they make the available feedback inconclusive.

Fediway's public recommendation tests verify request validation and failure handling, not relevance or user satisfaction. Source: [recommendation endpoint tests](https://github.com/fediway/feeds/blob/main/apps/server/tests/recommended.rs).

Private beta feedback or internal engagement data may exist, but no recommendation-quality results have been published. The beta is a Mastodon product consuming a provider that includes Nostr content; no evidence was found of a Nostr client serving these recommendations to Nostr users. There is therefore no Nostr-user quality evidence.

### Quality Conclusion

The prior art demonstrates that semantic Nostr retrieval can be built. It does not demonstrate that semantic retrieval produces recommendations people are glad to receive.

## Protocol Support

[NIP-50](https://nips.nostr.com/50) already permits human-readable search strings and leaves matching and ranking to the relay implementation.

[Kind 5300](https://github.com/nostr-protocol/data-vending-machines/blob/master/kinds/5300.md) already permits free-text content-discovery requests and leaves the algorithm arbitrary.

Either interface can carry semantic discovery. Neither provides or validates the recommendation engine.

## What Is Already Established

- Embedding Nostr notes.
- Free-text-to-note semantic retrieval.
- Note-vector-to-note retrieval.
- Updating an interest vector from explicit feedback.
- Locally aggregating behavior before querying a public vector provider.
- Returning Nostr event IDs through existing protocol shapes.

## What Has Not Been Demonstrated

- Broad and fresh root-kind-1 corpus coverage.
- Inclusion of low- and zero-engagement notes.
- Embedding models evaluated specifically for Nostr retrieval.
- Multiple independent interests and current intent.
- Negative feedback without unjustified generalization.
- Local seen-state filtering and final ranking.
- Quality measured by whether a person considers each recommendation worth seeing.

## Relevance to Current Work

Existing projects establish that Nostr notes can be embedded and retrieved by
semantic proximity. They do not establish that the resulting vector geometry
supports atomic-subject extraction, useful fine segmentation, or a
broad-to-narrow content hierarchy.

This prior-art record therefore supports only the mechanical feasibility of
semantic Nostr infrastructure. It does not select the current extraction,
segmentation, hierarchy, or recommendation design.

