# Private, Decentralized Recommendation Engine

## Current Status

Oracle MVP v1 is complete and frozen at the local `oracle-mvp-v1` tag.

The exact v1 Oracle-plus-personalizer system missed its approved quality
criterion on the historical corpus. This is not a direct failure of the broader
Oracle architecture. The post-run analysis found exploratory evidence that
vector proximity retained some relationship to the evaluator's judgments, but
the tested system did not convert that signal into a sufficiently valuable,
varied feed.

No complete replacement architecture has been approved. The current
prerequisite experiment asks whether public Nostr notes can support one
corpus-induced weighted note-topic relation. Hierarchy, labels, navigation, and
another personalizer remain out of scope until that relation is validated.

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

## V1 Experimental Mandate

Before choosing a production architecture, the v1 mandate was to run the strongest Oracle experiment that fit the `$500` lifetime paid-compute ceiling for the complete MVP. It used the complete eligible public Nostr corpus after calibration showed that it fit. Production constraints such as mobile runtime and network serving were deferred, but the lifetime ceiling was not.

The public Oracle supplied semantic candidates and reusable public vectors. A private personalizer learned from one person's judgments and produced the final order. Recommendation quality belonged to that combined system and was evaluated by whether the person was consciously glad they saw the resulting notes.

## Interpretation

A successful later experiment would establish that public Nostr data and private local judgments contain enough information for a worthwhile recommendation system under its tested conditions.

The v1 result is strong evidence against its exact tested configuration. It does not prove that every future representation, corpus, personalizer, or Oracle-like architecture must fail.

If a later experiment succeeds, its result should become the quality target. Production constraints should then be introduced one at a time: fit the public representation and private personalization onto supported devices, then distribute and update the public inputs through a decentralized protocol. Recommendation quality must be compared with that result at each stage so the cost of every constraint is known.

## Document Map

### Current design work

- [`design/adjacent-novelty.md`](design/adjacent-novelty.md)
- [`design/semantic-region-navigation.md`](design/semantic-region-navigation.md)
- [`design/corpus-induced-subject-map-hypothesis.md`](design/corpus-induced-subject-map-hypothesis.md)
- [`experiments/adjacent-novelty/crec-101-theme-vector-separation.md`](experiments/adjacent-novelty/crec-101-theme-vector-separation.md)
- [`experiments/adjacent-novelty/crec-102-cumulative-theme-exposure-replay.md`](experiments/adjacent-novelty/crec-102-cumulative-theme-exposure-replay.md)
- [`experiments/adjacent-novelty/crec-110-semantic-branch-recovery.md`](experiments/adjacent-novelty/crec-110-semantic-branch-recovery.md)

### Operational guidance

- [`disk-io-pressure-control.md`](disk-io-pressure-control.md)

### Frozen Oracle MVP v1

- [`experiments/oracle-mvp-v1/design/oracle-mvp.md`](experiments/oracle-mvp-v1/design/oracle-mvp.md)
- [`experiments/oracle-mvp-v1/design/local-personalizer.md`](experiments/oracle-mvp-v1/design/local-personalizer.md)
- [`experiments/oracle-mvp-v1/design/oracle-embedding-model-research.md`](experiments/oracle-mvp-v1/design/oracle-embedding-model-research.md)
- [`experiments/oracle-mvp-v1/results/recommendation-mvp-autopsy.md`](experiments/oracle-mvp-v1/results/recommendation-mvp-autopsy.md)
- [`experiments/oracle-mvp-v1/results/recommendation-mvp-rating-analysis.md`](experiments/oracle-mvp-v1/results/recommendation-mvp-rating-analysis.md)
- [`experiments/oracle-mvp-v1/artifact-locations.md`](experiments/oracle-mvp-v1/artifact-locations.md)

### Research

- [`research/direct-note-to-mask-extractor.md`](research/direct-note-to-mask-extractor.md)
- [`research/semantic-region-discovery-and-labeling.md`](research/semantic-region-discovery-and-labeling.md)
- [`research/leading-content-recommendation-systems.md`](research/leading-content-recommendation-systems.md)
- [`research/general-semantic-recommendation-systems.md`](research/general-semantic-recommendation-systems.md)
- [`research/existing-nostr-recommendation-systems.md`](research/existing-nostr-recommendation-systems.md)
- [`research/nostr-semantic-recommendation-prior-art.md`](research/nostr-semantic-recommendation-prior-art.md)
- [`research/nostr-relay-storage-research.md`](research/nostr-relay-storage-research.md)
