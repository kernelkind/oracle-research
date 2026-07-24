# Existing Nostr Recommendation Systems

Research current as of 2026-07-10.

## Conclusion

The Nostr recommendation field is substantially less developed than recommendation systems on large centralized platforms. Divine is the only deployed Nostr product found that clearly provides learned, per-user, out-of-network content recommendations. Its architecture is centralized and depends on identity-linked behavioral feedback.

The remaining systems provide useful but incomplete pieces:

- Primal provides mature public indexing, engagement ranking, trust filtering, and graph-based discovery.
- Nalgorithm provides semantic ranking against an explicit preference profile.
- AlgoRelay provides a transparent per-user heuristic feed.
- Nostria provides private local behavioral adaptation.
- Nostr.band, Vertex, and Brainstorm provide trust, spam filtering, or account discovery rather than content recommendation.
- NIP-90 DVMs provide a way to request feeds from interchangeable services, but the available algorithms are mostly popularity and graph filters.

No system found combines broad out-of-network retrieval, semantic content understanding, private local preference learning, local final ranking, and decentralized access to public inputs.

## Evidence Limitations

No public Nostr-specific recommendation benchmark, evaluation corpus, satisfaction study, or credible online experiment comparing these systems was found. In particular, no system publishes results for recommendation satisfaction, precision, recall, NDCG, serendipity, long-tail discovery, or retention adjusted for user welfare.

Consequently, “best” here does not mean proven recommendation quality. Systems are compared by:

1. Whether recommendations are genuinely personalized.
2. Whether they discover content outside the follow graph.
3. The sophistication of candidate retrieval and ranking.
4. Whether the system is deployed and maintained.
5. Whether its implementation can be inspected.
6. Whether private behavior and final ranking remain local.

## Comparison

| System | Personal signal | Candidate discovery | Ranking | Deployment | Privacy boundary |
| --- | --- | --- | --- | --- | --- |
| Divine | Views, reactions, comments, reposts | Out-of-network video corpus | Central Gorse-backed personalized ranking | Deployed | Signed viewing behavior leaves the device; request identifies the user |
| Primal | Public follows, mutes, and graph context | Broad indexed public corpus | Trust-filtered engagement and feed-specific heuristics | Deployed | Ranking and user context are handled by a server |
| Nalgorithm | Explicit preference prompt and public likes | Posts from followed accounts only | LLM relevance score | Experimental | Private with a local LLM; preferences leave the device with a cloud LLM |
| AlgoRelay | Public interactions with authors and user-selected weights | Preferred authors plus a viral pool | Weighted heuristic score | Public implementation | Server receives the user's identity and produces the final feed |
| Nostria | Local views, reading, interactions, and time | Popular starter pack, follows, and previously encountered authors | Local author-affinity selection; posts remain chronological | Deployed client implementation | Behavioral metrics remain local |

## Divine

### What Is Deployed

Divine's For You video feed calls a Funnelcake REST endpoint for a specific public key:

```text
GET /api/users/{pubkey}/recommendations
```

The client receives an ordered list of videos rather than fetching a generic pool and ranking it locally. The feed is available only while Funnelcake is reachable.

The production endpoint responded during this research. Established public keys received distinct ordered results, while unrelated unused keys received the same cold-start-like result. This is consistent with active per-user personalization, but it is not a controlled quality evaluation.

Sources:

- [For You feature description](https://github.com/divinevideo/divine-mobile/issues/1827)
- [For You client provider](https://github.com/divinevideo/divine-mobile/blob/main/mobile/lib/providers/for_you_provider.dart)
- [Production API description](https://relay.divine.video/openapi.json)

### Known Inputs

Divine states that the deployed recommender uses the following relative feedback strengths:

1. Reposts: strongest.
2. Comments: strong.
3. Reactions: medium.
4. Views: light.

Cold-start users receive a mixture of popular and trending videos. The system is explicitly intended to surface videos outside the user's existing network.

### Gorse and the Unknown Production Configuration

Funnelcake is described as Gorse-backed. Gorse supports a conventional multi-stage recommendation pipeline:

- Latest and non-personalized candidate sources.
- User-to-user nearest-neighbor retrieval.
- Item-to-item nearest-neighbor retrieval.
- Matrix-factorization collaborative filtering.
- External candidate sources.
- Factorization-machine or LLM-based final rankers.
- Removal of previously read items and configurable fallback behavior.

Sources:

- [Gorse retrieval and ranking pipeline](https://gorse.io/docs/concepts/pipeline)
- [Gorse rankers](https://gorse.io/docs/concepts/ranking)
- [Gorse evaluation](https://gorse.io/docs/concepts/evaluation)

The Funnelcake implementation and production Gorse configuration were not found publicly. It is therefore unknown which Gorse candidate generators and rankers Divine actually enables. The public evidence establishes a Gorse-backed service, its feedback types, and personalized output; it does not establish that Divine uses matrix factorization, semantic embeddings, factorization machines, or an LLM.

### Privacy Boundary

Divine publishes signed kind `22236` video-view events to Nostr relays. These events contain:

- The viewed video.
- One or more watched intervals.
- The traffic source, including whether the video came from For You.
- Loop information.
- The viewer's public identity through the event signature.

The source states that these events power analytics and recommendation systems. Although kind `22236` is ephemeral for relay-handling purposes, a recipient can retain and aggregate the event. The recommendation request also identifies the user by public key.

Source: [Divine view-event publisher](https://github.com/divinevideo/divine-mobile/blob/main/mobile/lib/services/view_event_publisher.dart).

This violates the intended boundary for a private recommender: private consumption behavior leaves the device, an external service constructs the preference model, and final ranking occurs externally.

### Quality and Maturity

The feature is deployed, paginated, and integrated into the product. However, no recommendation-quality results are public. A 2026 issue documented repeated, stale, and already-watched videos resurfacing. Later work added cursor pagination, session seeds, and result jitter, but these changes do not constitute evidence of recommendation relevance.

Source: [Repeated and stale recommendations](https://github.com/divinevideo/divine-mobile/issues/3049).

Divine has also designed swipe-based “more” and “less” tuning. The client-side implementation has been feature-flagged, while end-to-end Gorse ingestion was described as deferred. The proposed feedback is a plaintext public kind `4242` event rather than private local state. It should not be treated as a completed production capability.

Source: [Swipe feed-tuning design](https://github.com/divinevideo/divine-mobile/blob/main/docs/superpowers/specs/2026-06-25-swipe-feed-tuning-design.md).

### Assessment

Divine is the strongest deployed Nostr recommender found. It demonstrates that identity-linked behavioral learning can produce individualized, out-of-network Nostr recommendations. It does not demonstrate that the same quality is possible under a private local-personalization boundary, and it publishes no evidence that its recommendations are consistently good.

## Primal

### Public Discovery Architecture

Primal operates a large ingestion, cache, enrichment, search, and discovery service over public Nostr events. Its open server implements multiple feed families, including:

- Global trending.
- Most zapped.
- Wide-network notes.
- Strange but popular.
- Engaging discussions.
- Content bookmarked by follows.
- Important notes the user might have missed.
- DVM-provided feeds.

Sources:

- [Primal server](https://github.com/PrimalHQ/primal-server)
- [Feed and discovery implementation](https://github.com/PrimalHQ/primal-server/blob/main/src/app_ext.jl)
- [Application endpoints](https://github.com/PrimalHQ/primal-server/blob/main/src/app.jl)

### Ranking

Primal maintains event scores from public engagement. Current source assigns example base increments of:

- Reaction: `1`.
- Repost: `7`.
- Zap: `5`.
- Reply: `10`.

An action contributes to the public score only when its initiator passes Primal's TrustRank-derived human check. Twenty-four-hour scores are separately maintained and expired. This reduces the influence of obvious spam and low-trust accounts before engagement is used for discovery.

Sources:

- [Event scoring](https://github.com/PrimalHQ/primal-server/blob/main/src/cache_storage_ext.jl)
- [TrustRank integration](https://github.com/PrimalHQ/primal-server/blob/main/src/trust_rank.jl)

### Personalization Limit

Primal uses user context for follows, mutes, network-scoped feeds, missed-content retrieval, and filtering. Its discovery feeds nevertheless remain primarily functions of public graph relationships, recency, engagement, and a selected feed recipe.

No production content-embedding or learned semantic taste model was found in the recommendation path. Embeddings present elsewhere in the server are not evidence of semantic feed personalization.

### Assessment

Primal is the strongest mature public text-discovery stack found. It is valuable as evidence that a broad public Nostr corpus can be indexed, cleaned, scored, and queried efficiently. It does not solve plural personal taste: two people with different interests but similar follow-graph context can still receive substantially the same highly scored material.

The server is open and self-hostable, which reduces provider lock-in, but a hosted instance still observes user-specific requests and produces the final ranking.

## Nalgorithm

### Method

Nalgorithm fetches original posts, quote posts, and boosts from followed accounts. It asks an OpenAI-compatible LLM to assign each post a relevance score from `0` to `10` using:

- A natural-language preference profile written by the user.
- A learned preference prompt derived incrementally from the user's public kind `7` reactions.
- The text of the candidate post and resolved quoted or boosted content.

Scores and learned prompts are cached in browser local storage or local CLI files.

Source: [Nalgorithm](https://github.com/jooray/nalgorithm).

### Privacy

With local Ollama, the preference profile, learned profile, candidates, and ranking remain local. With OpenRouter, Venice, Ollama Cloud, or another remote compatible provider, the provider receives the preference information and candidate batch. The candidate posts are public, but the explicit preference profile need not be.

### Discovery Limit

Nalgorithm only retrieves posts from followed accounts. Semantic ranking can identify the most relevant material within that pool, but cannot recover an excellent post by an unknown author that never entered the pool.

### Maturity

The project is a small experiment with no published evaluation, production population, or out-of-network retrieval system. Its importance is conceptual: it is the clearest Nostr implementation found that judges post meaning rather than relying entirely on authorship and engagement proxies.

### Assessment

Nalgorithm is the strongest semantic-ranking experiment found, but it is a reranker rather than a complete discovery system. It is also the clearest precedent for using an explicit human-readable preference model with a local inference option.

## AlgoRelay

### Method

AlgoRelay exposes a personalized Nostr-compatible feed keyed by user public key. It constructs candidates from:

- Notes by authors with whom the user has interacted most.
- A separate globally viral pool.

For a note `event`, its score is the weighted sum of:

- Global comment count.
- Global reaction count.
- Global zap count.
- An exponential recency factor.
- The user's interaction count with the author.

Users can configure the weights. Feed variants mix author-affinity and viral candidates and damp repeated authors.

Source: [AlgoRelay algorithm](https://github.com/barrydeen/algo-relay/blob/master/algorithm.go).

### Limit

The only learned personal relationship is between the user and an author. A positive interaction with one post raises other posts by that author regardless of topic, format, or reason for the original interaction. There is no semantic representation of content or evidence of plural-interest modeling.

The service also receives the user's identity and performs final ranking externally.

### Assessment

AlgoRelay is the clearest open Nostr-native per-user feed implementation found and a useful transparent heuristic baseline. It is not competitive with a modern content-level recommender.

## Nostria

### Local Behavioral State

Nostria maintains local per-account, per-author metrics including:

- Viewed posts.
- Profile visits.
- Likes.
- Reads.
- Replies.
- Reposts.
- Quotes.
- Zaps.
- Messages.
- Mentions.
- Time spent.
- Aggregate engagement points and scores.

Sources:

- [Local metrics](https://github.com/nostria-app/nostria/blob/main/src/app/services/metrics.ts)
- [Author-affinity algorithms](https://github.com/nostria-app/nostria/blob/main/src/app/services/algorithms.ts)

The state is partitioned by the local account and used to identify authors with whom the person has meaningful recent engagement.

### For You Candidate Construction

Nostria's For You feed combines:

1. A hardcoded or fetched popular starter pack.
2. Up to twenty recently followed accounts.
3. A small number of locally top-engaged authors.

It then fetches events from the combined author set. The resulting posts are deduplicated and principally sorted by `created_at`; the local engagement model selects authors rather than scoring individual posts for relevance.

Source: [Nostria feed service](https://github.com/nostria-app/nostria/blob/main/src/app/services/feed.service.ts).

### Assessment

Nostria is the strongest precedent found for keeping behavioral adaptation local. It does not perform content-level recommendation. Unknown-author discovery is supplied by a generic popular starter pack, while personalization mainly retrieves additional posts from already encountered authors.

## Nostr.band

Nostr.band provides public discovery infrastructure rather than a personal recommender.

Its TrustRank constructs a directed graph from public Nostr identities and relationships, starts from trusted seeds, and iteratively propagates rank in a PageRank-like process. Search and relay results can exclude identities with no trust by default.

Its spam system groups recent text using word and n-gram similarity and suppresses clusters that exceed its similarity and rate thresholds.

Sources:

- [Nostr.band TrustRank](https://trust.nostr.band/)
- [Nostr.band spam filtering](https://spam.nostr.band/)
- [Nostr.band frontend](https://github.com/nostrband/nostr-band-app)

No public source for the main backend or evidence of a per-user content-taste model was found. TrustRank and spam filtering can improve candidate hygiene, but they do not determine whether a trustworthy post is personally valuable.

## Vertex

Vertex crawls the public follow graph and computes global and personalized Monte Carlo PageRank. Its API and DVM can recommend public keys while excluding accounts already followed by the source user.

Sources:

- [Vertex documentation](https://vertexlab.io/docs/)
- [Recommend Follows endpoint](https://vertexlab.io/docs/endpoints/recommend-follows/)
- [Vertex repositories](https://github.com/vertex-lab)

Vertex is a deployed account-discovery and graph-ranking service, not a post recommender. A request identifies the source public key, and the output is a list of accounts rather than personally relevant content.

## Brainstorm and GrapeRank

Brainstorm is an alpha personalized Web-of-Trust relay. GrapeRank develops related personalized graph-ranking methods from follows, mutes, reports, and other public assertions.

Sources:

- [Brainstorm](https://github.com/Pretty-Good-Freedom-Tech/brainstorm)
- [GrapeRank](https://github.com/Pretty-Good-Freedom-Tech/graperank-nodejs)

The available work concerns trust, reputation, and people discovery. Content recommendations are incomplete or described as future work. These systems may constrain or diversify candidate sources, but do not currently supply content-level personal relevance.

## NIP-90 Data Vending Machines

NIP-90 defines request, result, and payment events for external computation. A user may ask multiple providers to perform the same type of job, including content discovery. It is a transport and service-discovery mechanism, not a recommendation algorithm.

Sources:

- [NIP-90](https://nips.nostr.com/90)
- [DVM kind registry](https://github.com/nostr-protocol/data-vending-machines)
- [NostrDVM framework](https://github.com/believethehype/nostrdvm)

The current NIP is marked `draft unrecommended optional` and warns that it became too broad; use-case-specific microstandards are now preferred.

The open kind `5300` feed implementations inspected include:

- Recently popular notes.
- Popular notes from followed accounts.
- Popular notes excluding followed accounts.
- Top-zapped notes.
- Popular notes matching a topic.
- One recent note per followed account.
- Nostr.band trending notes.

The primary ranking method is counting recent reactions, reposts, zaps, and replies, sometimes after restricting authors or matching a search term. Personalized jobs generally include a `user` public-key parameter. DVMs therefore provide provider choice, but the known implementations neither keep the request private nor introduce a sophisticated recommendation model.

Amethyst and Primal expose DVM feed discovery or consumption, but their support for DVMs should not be mistaken for an independent recommendation algorithm.

## Open Ranking Protocol

The Open Ranking protocol is a recent draft for provider-swappable ranking over HTTP. It defines account-ranking and account-recommendation operations.

Source: [Open Ranking protocol](https://github.com/Open-Ranking/protocol).

No production provider or post-level recommendation endpoint was found. It is relevant protocol work, but not an existing content recommender.

## NostrArchives

NostrArchives provides public indexing, trending results, leaderboards, and engagement-derived ordering with Web-of-Trust-gated ingestion.

Source: [NostrArchives API](https://github.com/barrydeen/nostrarchives-api).

Its available behavior is global analytics and trending rather than learned personal recommendation.

## Other Approaches Investigated

### Custom Feeds and Filters

Coracle, Nostur, Primal feed recipes, DVM selectors, relay filters, topics, hashtags, lists, and starter packs offer valuable user control. They retrieve content matching explicit structural rules, but do not infer post-level personal value. They are custom retrieval systems rather than learned recommenders.

### Follow Discovery

Two-hop follow discovery and graph-ranked account suggestions can help a person construct a useful social graph. They do not solve discovery across several unrelated interests, and they require the user to subscribe to an author before seeing whether a particular post is worthwhile.

### EigenVibe

EigenVibe describes a local preference-space experiment using reactions and author alignment. No inspectable production implementation, public evaluation, or evidence of current deployment was found, so it cannot be ranked alongside the systems above.

### Older Proofs of Concept

Older projects such as Squint explored algorithmic Nostr feeds but were not found to have current deployment, recent development, or quality evidence. They do not alter the current architectural picture.

### False Positives

Several search results were unrelated despite matching the terminology:

- Nosto is a centralized ecommerce-personalization company, not Nostr.
- News aggregators that use Nostr for login or publishing are not recommenders over the Nostr corpus.
- Generic peer-to-peer embedding proposals without Nostr interoperability are not existing Nostr systems.

## Cross-System Findings

### Most Nostr “Algorithms” Are Public Popularity Functions

The dominant pattern is:

1. Restrict the corpus by time, follows, topic, trust, or relay.
2. Count reactions, reposts, replies, or zaps.
3. Apply recency decay.
4. Return the highest-scoring events.

This can produce a useful trending feed, but it cannot represent different tastes among people exposed to the same public graph.

### Author Affinity Is Common; Content Taste Is Rare

AlgoRelay and Nostria learn which authors receive attention. Primal uses follows and network context extensively. These approaches generalize a judgment about one post to its author because they lack a representation of why the post was valuable.

Nalgorithm is the only inspected project that directly compares post meaning with a preference description. It does not solve global retrieval.

### Large AI Models Are Not Currently the Norm

Most deployed Nostr discovery systems use counts, graph algorithms, filters, and conventional recommender infrastructure. Nalgorithm explicitly uses an LLM. Gorse supports LLM reranking and embedding-based features, but there is no public evidence that Divine enables them.

The principal missing capability is not access to a very large language model. It is a complete retrieval-and-ranking pipeline that can search a broad corpus using a private, plural, correctable personal model.

### Provider Choice Does Not Create Decentralized Recommendation

DVMs and open/self-hostable servers reduce dependence on one operator. If every provider still receives a user identity or preference query and returns the final personalized order, personalization remains externally observable. Multiple interchangeable centralized rankers do not satisfy a local-personalization boundary.

### Open Source Does Not Establish Quality

Gorse, Primal, AlgoRelay, Nostria, Nalgorithm, and NostrDVM expose useful implementation details. None publishes evidence that users are consciously glad they saw its recommendations. Engagement prediction and recommendation satisfaction remain different objectives.

## Implications for the Recommendation Oracle

The existing systems establish that Nostr already has useful popularity, graph,
filter, and hosted-personalization components. They do not establish the current
MVP question: whether public semantic note relationships plus private local
judgments can produce a feed one person is consciously glad to see.

The MVP therefore does not compare four broad architectures. It makes one
strong, affordable complete-corpus semantic attempt, exposes reusable public
evidence through `similar_notes` and `vectors_for_notes`, and compares two
local personalizers before one untouched final evaluation. Collaborative,
graph, engagement, recency, freshness, and exploration sources remain possible
follow-up work only if the semantic MVP result justifies it.

The unoccupied design space remains a system in which public infrastructure
computes replaceable information about public Nostr content while private
behavior constructs the user's taste model and final ranking locally. None of
the surveyed systems currently demonstrates that combination with conscious
personal-value evaluation.
