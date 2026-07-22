# Phase 3 capacity bound (CREC-89)

## Decision

The complete ten-round adaptive-learning run is clearly safe on disk and appears feasible in elapsed time. It is **not yet safe to begin human ratings on this host**, because the first-round preflight does not bound late-round memory.

The smallest missing measurement is one disposable, no-human, all-positive ten-round run through the production runner. It should measure simultaneous controller and worker memory, per-round elapsed time, and cache growth. It must use a separate run directory, keep the rental artifacts read-only, and make no recommendation-quality claim. Synthetic all-7 ratings maximize positive evidence per rated note, but they do not guarantee disjoint personalizer choices or neighborhoods. The result is a direct bound only for the counts it actually reaches; any gap from the exact maxima below must remain explicit.

No cache redesign or other optimization is justified before that measurement.

## Scope and evidence

This bound covers the ten learning rounds implemented by `AdaptiveLearningCoordinator`. It does not include the later frozen comparison or final evaluation.

The measured input is the CREC-88 v4 report:

- Path: `../damus_snapshot/runs/crec-88-phase3-first-round-v4/report.json`
- SHA-256: `7244299011b179f70a8cab8aee20c80e216f1d8769715596ed37f927464f9995`
- Representation: 3,530,455 rows × 3,584 FP32 dimensions
- Spend: $0
- Quality claim: none

The report is warm-biased because complete representation verification read every vector shard immediately before the measured scan. Its times are coefficients, not certified upper bounds.

## Exact protocol bounds

Phase 3 starts both personalizers from the same five positive seeds, runs ten rounds, and accepts 20 learning notes per personalizer per round ([adaptive_learning.rs](src/adaptive_learning.rs), [candidate_order.rs](src/candidate_order.rs)). Ratings 5–7 can become later `similar_notes` sources; ratings 1–4 cannot.

At the start of round `r`, one personalizer can therefore have at most:

```text
5 + 20(r - 1)
```

positive sources. The deduplicated union across both personalizers can have at most:

```text
5 + 40(r - 1)
```

The round-by-round maxima are:

| Round | Per personalizer | Union | New uncached union sources |
| ---: | ---: | ---: | ---: |
| 1 | 5 | 5 | 5 |
| 2 | 25 | 45 | 40 |
| 3 | 45 | 85 | 40 |
| 4 | 65 | 125 | 40 |
| 5 | 85 | 165 | 40 |
| 6 | 105 | 205 | 40 |
| 7 | 125 | 245 | 40 |
| 8 | 145 | 285 | 40 |
| 9 | 165 | 325 | 40 |
| 10 | 185 | 365 | 40 |

Consequently, a successful worst-case learning run has these limits:

| Item | Maximum |
| --- | ---: |
| Unique encoded source queries | 365 |
| Physical full-matrix passes | 10 |
| Logical Oracle calls, including the optional first-round Compact fallback | 31 |
| Source responses delivered across logical calls | 3,755 |
| Unique `similar_notes` response files | 365 |
| Candidate records in unique source responses | 373,760 |
| Candidate vectors plus five seed vectors | 373,765 |
| Vector-response files | 20 |
| Total durable Oracle cache files | 416 |

The 20 vector-response files are one seed batch, one shared first-round candidate batch, and at most two candidate batches in each later round. `CandidateVectorCache` asks only for missing vectors ([candidate_order.rs](src/candidate_order.rs)).

Completed round records retain both complete candidate-order audits, not just the selected 41-note orders ([shared_learning_round.rs](src/shared_learning_round.rs)). Their worst-case retained source-candidate attribution count is:

```text
2 × 1,024 × (5 + 25 + ... + 185) = 1,945,600
```

The optional first-round Compact fallback can add 5,120, for a maximum of 1,950,720.

## Disk

The v4 candidate-vector response used 228,269,750 bytes for 4,980 vectors, or about 45,837 JSON bytes per vector. Applying that measured rate to the exact count bounds gives:

| Artifact | Projected size |
| --- | ---: |
| Vector-response cache | 15.96 GiB |
| Unique responses plus duplicated logical-call tapes | 0.65 GiB |
| Session JSON | about 0.2 GiB |
| Complete disposable workspace | about 20.6 GiB |

The host currently has about 1.49 TiB available. Disk capacity is not a blocker, even with a large safety factor.

## Elapsed work

The v4 five-query wave measured:

| Work | Five-query measurement | Linear 365-query projection |
| --- | ---: | ---: |
| Query encoding | 42.92 s | 52.2 min |
| Matrix scan | 62.56 s | 76.1 min |
| Result merge | 0.26 s | 0.3 min |

The Oracle-only linear projection is about 2.14 hours. This is not a time guarantee: the measured matrix was warm, and later query batches can contain 40 notes instead of five.

Local scoring also cannot be estimated as ten times round one. With no neighborhood overlap, the two personalizers can perform at most about 904.7 billion vector-component distance operations across all ten candidate-order builds. Compact performs as many as 972,800 small evidence-distance sorts containing 126.2 million total elements; `n log2(n)` gives roughly 964 million comparison units, but the exact count depends on the sort implementation ([local_personalizer.rs](src/local_personalizer.rs)). RBF fitting and frozen-batch prediction add about 2.87 billion vector-component operations. About 127.0 million exponentials accompany the RBF work, mostly the active candidate distances already included in the 904.7 billion count.

The B16 walk is another wide range. If the first 41 scored notes are sufficiently distinct, the complete run makes only 16,400 diversity comparisons. A worst successful traversal can make 77.8 million. Because each current comparison validates both vectors and then computes their distance, that worst case visits about 836.8 billion vector components ([candidate_order.rs](src/candidate_order.rs)). CREC-88 did not record how far the walk advanced.

Session persistence also rewrites the entire pretty-printed session before and after every presentation and calls `sync_all` each time ([adaptive_learning_runner.rs](src/adaptive_learning_runner.rs)). V4 used 2,811,452 bytes for 4,985 referenced vectors, about 564 bytes per vector ID. At 40 disjoint numeric presentations per round, applying that measured rate to the staged vector counts projects about 80 GiB of cumulative session rewrites. A successful run may also consume the global reserve of 21 wrong-language presentations; placing all of them at the largest session raises the projection to about 88 GiB. That is write traffic, not final disk usage.

These counts make a several-hour run plausible, but CREC-88 did not isolate late-round local-scoring throughput. The proposed ten-round capacity run measures it directly instead of adding speculative optimization.

## Memory

CREC-88 measured:

| Process | Peak RSS |
| --- | ---: |
| Controller | 47.77 GiB |
| Query worker | 35.16 GiB |
| Sum of independent high-water marks | 82.93 GiB |

Most controller RSS is the file-backed representation: about 47.14 GiB of vectors plus about 0.22 GiB of indexes. Those pages are reclaimable, and the two high-water marks were not recorded at the same instant. Their sum is therefore conservative, but it is not a simultaneous-memory measurement.

Late-round state adds two retained raw copies of as many as 373,760 candidate vectors:

- `CandidateVectorCache`: at most 4.99 GiB.
- `SessionOracle.loaded_vectors`: at most another 4.99 GiB.

A single later vector response can add at most 20 × 1,024 new vectors, because each personalizer receives at most 20 new evidence notes per round. During response publication, the code temporarily holds three raw copies of that new batch and its JSON byte buffer ([adaptive_learning_runner.rs](src/adaptive_learning_runner.rs)). Immediately before the second round-ten batch, the vector path alone can therefore reach about 11.13 GiB, compared with about 0.41 GiB in CREC-88.

Adding only that measured-and-derived growth to the two v4 process high-water marks gives about 93.65 GiB. The host currently reports 95.57 GiB available, while 15.06 GiB of 15.06 GiB swap is already used. This leaves no credible margin for two unmeasured terms:

- the worker growing from a five-query batch to a 40-query batch;
- the 1,950,720 retained candidate-order audit attributions and their surrounding records.

This does not prove the run will fail: file-backed matrix pages can be reclaimed. It proves that the first-round result is insufficient to call the unchanged run safe.

## Required next evidence

Run the unchanged production workflow for ten rounds with a disposable evaluator that:

1. marks every candidate language-eligible;
2. assigns every learning note rating 7, maximizing later positive sources;
3. records the reached source, candidate, vector, audit, and presentation counts beside the exact maxima in this report;
4. records simultaneous controller and worker memory, including anonymous versus file-backed memory;
5. records per-round Oracle, local-scoring, persistence, cache-size, and elapsed growth;
6. runs under a hard memory ceiling so a failed bound cannot destabilize the host;
7. writes only to a new disposable run directory and opens the rental representation read-only.

This is capacity data only. Its synthetic ratings cannot be reused for recommendation evaluation and make no quality claim. Marking every note language-eligible deliberately omits the reserve path: wrong-language outcomes do not increase the source, vector, or matrix-pass maxima, and their successful-run persistence cost is bounded analytically above. If the stress run does not reach a material source/vector/audit maximum, it does not erase that remaining risk; its measured per-unit coefficients must be projected over the explicit gap or followed by a narrower probe.
