# Private, Decentralized Recommendation Engine

## Goal

Build an actually good recommendation engine that provides personalized, high-signal discovery without exposing private user behavior or placing discovery under the control of an indispensable provider.

A recommendation succeeds when that particular person is consciously glad they saw it. Aggregate popularity, engagement, or consumption time cannot substitute for personal value.

## Hard Constraints

- Shared computation may analyze only public Nostr data. Private behavior, recommendation feedback, inferred preferences, and final ranking remain on-device.
- Personalized candidate discovery must reach niche and unfamiliar content rather than merely reorder a generic or popularity-selected pool. Suppressing content already seen by a person is a client responsibility, not an Oracle-quality requirement.
- No external provider may be the sole gatekeeper of eligible content or a required dependency for recommendation.
- The eventual personalized discovery and ranking system must be practical on supported mobile and desktop hardware.

## Quality Bar

The engine must discover content from unknown authors across a person's distinct and potentially unrelated tastes. It must learn from explicit local judgments of whether a recommendation was worth seeing. Lack of feedback remains neutral.

## Quality Oracle

Before choosing a production architecture, run the strongest Oracle experiment that fits the `$500` lifetime paid-compute ceiling for the complete MVP. Use the complete eligible public Nostr corpus when calibration shows that it fits. Production constraints such as mobile runtime and network serving are deferred, but the lifetime ceiling is not.

The public Oracle supplies semantic candidates and reusable public vectors. A private personalizer learns from one person's judgments and produces the final order. Recommendation quality belongs to that combined system and is evaluated by whether the person is consciously glad they saw the resulting notes.

## Interpretation

Success would establish that public Nostr data and private local judgments contain enough information for a worthwhile recommendation system under the tested conditions.

A failed result from the strongest affordable complete-corpus configuration would be strong evidence against that tested approach. It would not prove that every future representation, corpus, or personalizer must fail.

If the MVP succeeds, its result becomes the quality target. Production constraints should then be introduced one at a time: fit the public representation and private personalization onto supported devices, then distribute and update the public inputs through a decentralized protocol. Recommendation quality must be compared with the MVP result at each stage so the cost of every constraint is known.
