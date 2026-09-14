# TRUE03 — Containment between actual generated category titles

## Question

Does the TRUE configuration that worked on manually written descriptions also make useful containment decisions between our actual HDBv2 titles?

Use the unchanged v20/Astra-low outputs in `../hdbv2-node-titles-v20-astra-low/titles.json`, SHA256 `424ffe683fe5fdb3de152cfc6fa09496dfef9fdef422e7a22618b28cc1e20716`. The title review is complete; titles, masks and memberships are not changed for this test. No hierarchy or UI is being constructed.

## Before scoring

The final [input set](true03-fixture.json) contains 22 pairs involving 25 original groups: 15 expected strict containments, six related-but-noncontaining pairs and one identical-title equivalence control. Both directions give 44 questions: 17 expected Yes and 27 expected No.

Pairs were selected by their title meanings, without looking at TRUE03 scores or using a cosine filter. They cover coffee, food ingredients, cuisines, meat dishes, poultry, greetings, personal qualities, Bitcoin and Nostr. This is a targeted pilot, predominantly food because that is the source collection, not a random or comprehensive sample.

An independent reviewer judged the proposed title pairs without seeing the main agent's expectations or any TRUE03 scores. Two scope-ambiguous pairs were removed before inference; the [blind-review record](TRUE03-BLIND-REVIEW.md) preserves both the initial judgments and why those pairs were set aside. No alternative titles were substituted. Final fixture SHA256: `46867f4041dfd002b22414e802953d702c2b7064b7410c7a2a355c0f3873328e`.

For each retained pair, the JSON records explicit expectations and a short scope explanation. These are practical, revisable semantic judgments, not a claim that one canonical hierarchy exists. Model disagreement does not prove that an expectation is correct.

## Unchanged model question

For **A contains B?**, TRUE receives exactly:

```text
premise: This text is about {B}. hypothesis: This text is about {A}.
```

Only exact title strings enter this input. No masks, full notes, expected answers, explanations or pair IDs are sent to TRUE.

Use the same released checkpoint/revision, tokenizer, CPU float32 weights, four threads, batch four, greedy generation and full-vocabulary first-token probability as TRUE02. Keep native generated answers and scores separately. The fixed decision rule remains **score > 0.142**, without retuning. The score is not cosine or a calibrated containment probability.

## Decisions this test should inform

Report valid relationships accepted and invalid relationships rejected separately, including reverse directions, noncontainment and the identical-title control. Show every error with both titles, the exact model input, score and expectation rationale. Do not use many unrelated pairs to inflate an overall count.

If mistakes are limited and do not reveal a major practical obstacle, broader testing across the 61 groups is justified. If clear relationships fail systematically, inspect that behavior before expanding. Check inconsistencies among tested chains without silently repairing them. A single possible error or debatable wording is not an automatic stop criterion.

Do not change title wording or the cutoff in response to scores. If an expectation becomes disputed, retain it and report the dispute separately. This test does not establish title-to-mask fidelity, missing-parent generation, a complete hierarchy, or general population accuracy.

## Execution and preservation

One offline inference process, with 60 GiB memory limit, no swap and four CPUs. Require at least 70 GiB available host memory before launch; do not stop other processes. No rental, API billing, training or model download.

The old environment's Python 3.11.15 executable is missing. Use the already-installed Python 3.11.14 with its existing Python 3.11 packages, recording this runtime difference. The model libraries remain torch 2.8.0+cpu, transformers 4.57.1, NumPy 2.3.4, huggingface_hub 0.36.2 and safetensors 0.6.2. Model/scoring settings are unchanged; do not claim the entire runtime is byte-identical to TRUE02.

Freeze inputs and provenance before loading the model. Save results under a new `TRUE03/` directory and refuse overwrites. Preserve exact inputs, native outputs, raw logits, scores, hashes, source snapshots and resource measurements. Independently replay the saved scores without a second model load. All previous experiment artifacts remain intact.
