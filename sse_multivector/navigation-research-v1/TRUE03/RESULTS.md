# TRUE03 — Actual generated titles: useful containment, with three discrepancies

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

**At the unchanged 0.142 cutoff, 41 of 44 directional answers matched the expectations recorded before scoring.** The test used 22 pairs from 25 original HDBv2 groups, with their exact v20/Astra-low titles.

| Decision rule | Expected Yes accepted | Expected No rejected | Correct directions |
|---|---:|---:|---:|
| Native generated answer | 14/17 | 27/27 | 41/44 |
| Fixed score > 0.142 | 15/17 | 26/27 | 41/44 |

For the cutoff rule, 13/15 strict broader-to-narrower relationships were accepted, 14/15 reverse directions were rejected, all 12 directions between noncontaining categories were rejected, and both identical-title equivalence directions were accepted. Both directions were correct for 19/22 pairs. These counts describe this selected pilot, not deployment accuracy.

## Three discrepancies at the fixed cutoff

Each question asks whether category A contains category B. TRUE receives B as premise and A as hypothesis. The score below is the full-vocabulary probability of the first output token being `1`, not cosine or calibrated category confidence. “Native” means the complete generated label; “cutoff” is our separate rule.

**1. Does Coffee Consumption contain Coffee?**

A: Coffee Consumption (`Sa241c43eb5`). B: Coffee (`S9c440e7f47`).

Exact model input:

```text
premise: This text is about Coffee. hypothesis: This text is about Coffee Consumption.
```

Expected: **No**. Native: **No**. Score: **0.186424**. Cutoff: **Yes**.

The expected answer is No: the Coffee category also includes subjects such as cultivation, not just drinking coffee. TRUE's native generated answer was No, but our fixed cutoff turned its score into Yes. The correct forward direction, Coffee contains Coffee Consumption, scored 0.966989 and was accepted.

**2. Does Poultry and eggs contain Poultry-Based Food Preparation?**

A: Poultry and eggs (`S5ea79ac96e`). B: Poultry-Based Food Preparation (`Se66af3a9b7`).

Exact model input:

```text
premise: This text is about Poultry-Based Food Preparation. hypothesis: This text is about Poultry and eggs.
```

Expected: **Yes**. Native: **No**. Score: **0.039920**. Cutoff: **No**.

The expected answer is Yes: Poultry and eggs is being used as a broad category that includes poultry topics, including preparing poultry-based food. Both the native answer and the cutoff answer were No.

**3. Does Poultry and eggs contain Making Chicken Stock?**

A: Poultry and eggs (`S5ea79ac96e`). B: Making Chicken Stock (`Sa1a95316f6`).

Exact model input:

```text
premise: This text is about Making Chicken Stock. hypothesis: This text is about Poultry and eggs.
```

Expected: **Yes**. Native: **No**. Score: **0.131106**. Cutoff: **No**.

The expected answer is Yes: making stock from chicken is a poultry subject. Both the native answer and the cutoff answer were No. Its score was close to, but below, the unchanged cutoff.

## What worked

- Coffee contained Coffee Bean Preparation, Coffee Consumption and Appreciating Coffee for Its Flavor. Preparation and consumption were correctly treated as distinct, related categories; so were preparation and flavor appreciation.
- Food contained Food Ingredients, and both contained Sea Salt as a Food Ingredient. Chinese Cuisine and Indian Food were both placed under Food without being treated as containing each other.
- Poultry-Based Food Preparation contained Making Chicken Stock, even though the broader Poultry and eggs links were missed.
- Bitcoin contained Satoshi Bitcoin Units (0.624658); Nostr contained Grow Nostr Campaign (0.603691). Their reverse directions were rejected.
- The two original groups titled Coffee were recognized as equivalent descriptions. This does not test differently worded equivalence or prove identical note membership.

The native-only additional error was **Red meat contains Brisket**: native No, score 0.471738, cutoff Yes. The cutoff therefore recovered one valid relationship while introducing the reverse-coffee error. There is no net correct-count advantage between the two rules in this pilot, and no rule was changed afterward.

## What the discrepancies suggest

The two missed relationships share the same proposed parent, Poultry and eggs. One plausible explanation is that our topic sentence makes TRUE read “and eggs” as requiring an additional subject, whereas a category title can collect poultry topics and egg topics. That would be a mismatch between the category question and how it is expressed as an entailment question. **This is a hypothesis, not an isolated cause**; learned associations or other wording effects remain possible. We did not rewrite the title, change the model input or run a follow-up variant.

A different universal cutoff cannot perfectly separate this observed set: the invalid Coffee Consumption contains Coffee score, 0.186424, is higher than both missed valid poultry scores. This does not mean the model is unusable, or that perfect separation is required.

The coffee error also creates an inconsistent set of predictions: the cutoff accepts Coffee Consumption contains Coffee and Coffee contains Coffee Bean Preparation, but rejects Coffee Consumption contains Coffee Bean Preparation. It also accepts Coffee and Coffee Consumption in both directions. These are consequences of the same error, not additional independent failures; reciprocal Yes answers cannot automatically be treated as proven equivalence.

## Conclusion and next decision

This is encouraging evidence that TRUE can use actual generated titles to recover useful containment relations, including distinguishing related categories from containment. It does not establish that the full collection will form a valid hierarchy.

The broader [TRUE04 test](../TRUE04/RESULTS.md) is now complete: all 61 original groups and 3,660 ordered questions, with titles, wording and cutoff unchanged. Of 106 cutoff-accepted directions, semantic review judged 91 reasonable, 9 incorrect and 6 ambiguous; these include repeated title strings. It recovered 90 of 120 relationships nominated before score inspection, with disputes preserved separately. The reciprocal-coffee error and missed poultry relationships reproduced unchanged. TRUE04 also found false Food/Nostr equivalence even in native answers. No title repair, cutoff change or hierarchy adoption followed.

The pre-score expectations remain unchanged. P16 (Meat Eating / Red meat) and P24 (Art / Music in Coffee Shops) were excluded before inference because the titles permitted materially different scopes. See the [blind review](../TRUE03-BLIND-REVIEW.md). Their exclusion limits what this pilot establishes about ambiguous titles.

## Evidence

- Every scored direction (`03bd9e45:sse_multivector/navigation-research-v1/TRUE03/DECISIONS.md`), exact model inputs (`inputs.json`), raw outputs (`scores.jsonl`), numerical summary (`analysis.json`).
- [Frozen plan](RESULTS.md#true03-study-design), [input pairs and scope explanations](fixture.json), unchanged source titles (`titles.json`).
- [Execution and tests](RESULTS.md#true03-runtime-and-verification), independent verification (`verification.json`).

No title, mask, group membership or expectation was changed after scoring. No hierarchy, review UI, model retraining, new cutoff or paid resource was introduced.

**Selected data:** Compact pair-score results, inputs and parameters for `TRUE03` are selected for release as `numerical/pair-scores-cc65be11ce8ebfa5` in the [publication catalog](../../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.

## TRUE03 study design

### Question

Does the TRUE configuration that worked on manually written descriptions also make useful containment decisions between our actual HDBv2 titles?

Use the unchanged v20/Astra-low outputs in `../hdbv2-node-titles-v20-astra-low/titles.json`, SHA256 `424ffe683fe5fdb3de152cfc6fa09496dfef9fdef422e7a22618b28cc1e20716`. The title review is complete; titles, masks and memberships are not changed for this test. No hierarchy or UI is being constructed.

### Before scoring

The final [input set](../true03-fixture.json) contains 22 pairs involving 25 original groups: 15 expected strict containments, six related-but-noncontaining pairs and one identical-title equivalence control. Both directions give 44 questions: 17 expected Yes and 27 expected No.

Pairs were selected by their title meanings, without looking at TRUE03 scores or using a cosine filter. They cover coffee, food ingredients, cuisines, meat dishes, poultry, greetings, personal qualities, Bitcoin and Nostr. This is a targeted pilot, predominantly food because that is the source collection, not a random or comprehensive sample.

An independent reviewer judged the proposed title pairs without seeing the main agent's expectations or any TRUE03 scores. Two scope-ambiguous pairs were removed before inference; the [blind-review record](../TRUE03-BLIND-REVIEW.md) preserves both the initial judgments and why those pairs were set aside. No alternative titles were substituted. Final fixture SHA256: `46867f4041dfd002b22414e802953d702c2b7064b7410c7a2a355c0f3873328e`.

For each retained pair, the JSON records explicit expectations and a short scope explanation. These are practical, revisable semantic judgments, not a claim that one canonical hierarchy exists. Model disagreement does not prove that an expectation is correct.

### Unchanged model question

For **A contains B?**, TRUE receives exactly:

```text
premise: This text is about {B}. hypothesis: This text is about {A}.
```

Only exact title strings enter this input. No masks, full notes, expected answers, explanations or pair IDs are sent to TRUE.

Use the same released checkpoint/revision, tokenizer, CPU float32 weights, four threads, batch four, greedy generation and full-vocabulary first-token probability as TRUE02. Keep native generated answers and scores separately. The fixed decision rule remains **score > 0.142**, without retuning. The score is not cosine or a calibrated containment probability.

### Decisions this test should inform

Report valid relationships accepted and invalid relationships rejected separately, including reverse directions, noncontainment and the identical-title control. Show every error with both titles, the exact model input, score and expectation rationale. Do not use many unrelated pairs to inflate an overall count.

If mistakes are limited and do not reveal a major practical obstacle, broader testing across the 61 groups is justified. If clear relationships fail systematically, inspect that behavior before expanding. Check inconsistencies among tested chains without silently repairing them. A single possible error or debatable wording is not an automatic stop criterion.

Do not change title wording or the cutoff in response to scores. If an expectation becomes disputed, retain it and report the dispute separately. This test does not establish title-to-mask fidelity, missing-parent generation, a complete hierarchy, or general population accuracy.

### Execution constraints

One offline inference process, with 60 GiB memory limit, no swap and four CPUs. Require at least 70 GiB available host memory before launch; do not stop other processes. No rental, API billing, training or model download.

The old environment's Python 3.11.15 executable is missing. Use the already-installed Python 3.11.14 with its existing Python 3.11 packages, recording this runtime difference. The model libraries remain torch 2.8.0+cpu, transformers 4.57.1, NumPy 2.3.4, huggingface_hub 0.36.2 and safetensors 0.6.2. Model/scoring settings are unchanged; do not claim the entire runtime is byte-identical to TRUE02.

Freeze inputs and provenance before loading the model. Save results under a new `TRUE03/` directory and refuse overwrites. Preserve exact inputs, native outputs, raw logits, scores, hashes, source snapshots and resource measurements. Independently replay the saved scores without a second model load. All previous experiment artifacts remain intact.

## TRUE03 runtime and verification

Run locally on September 14, 2026. No training, paid compute, API call, model download or GPU. Previous raw experiment artifacts are preserved.

### Identity and environment

- Model: `google/t5_xxl_true_nli_mixture`, revision `aa6cfe1dd4257853bfdd772992045f41bfc14988`, 11,307,321,344 parameters.
- Same TRUE02 CPU float32 inference, four threads, batch four, seed zero, deterministic algorithms and complete native greedy generation. All checkpoint loading-error lists are empty.
- Same topic input, label tokenization and strictly-greater-than-0.142 score rule. Native labels and cutoff decisions remain separate.
- Same installed torch 2.8.0+cpu, transformers 4.57.1, NumPy 2.3.4, huggingface_hub 0.36.2 and safetensors 0.6.2.
- The old environment's Python 3.11.15 executable was missing. An already-installed Python 3.11.14 interpreter used the existing Python 3.11 package directory through an explicit existing NixOS loader. No environment, shared interpreter, package or library was overwritten. This runtime difference is saved in `started.json`; the complete environment is not claimed byte-identical to TRUE02.
- All five released weight hashes and the model-file manifest match TRUE02. No model configuration or threshold was fitted to these outputs.

The 22 pairs were fixed after an independent blind semantic review and before inference. Two ambiguous pairs were excluded at that stage. The runner saved the exact fixture, full title artifact, 44 prepared inputs and source snapshots before checkpoint hashing/loading.

### Resources

Before launch, approximately 107 GiB of host memory was available. The command refused to start below 70 GiB. One model process ran in `oracle-true03.scope`, with 60 GiB RAM maximum, zero scope swap and four-CPU quota. These limits and zero swap were observed while it was active; no other process was stopped.

- Total runner time including hashing/loading: **128.25 seconds**.
- Inference and packaging: **84.09 seconds**.
- Peak process RSS: **45,492,116 KiB**, approximately **43.4 GiB**.
- Exit status: **0**. The scope was inactive after completion; no model process remained.
- Artifact size before this explanatory documentation: approximately **5.7 MiB**.

Global host swap already contained unrelated data before the run. The zero-swap observation concerns this inference scope, not the whole machine.

### Implementation and tests

A small new runner resolves actual titles from their original group IDs and validates the frozen source/fixture hashes. It prepares both directions with explicit pre-scoring expectations but sends only the serialized topic sentences to the model. It refuses duplicate/self/unknown pairs, non-Boolean expectations, missing rationale, changed source bytes and existing output directories.

The existing TRUE02 inference block was extracted into a shared function so the new runner does not maintain a duplicate model implementation. An executable-AST comparison against the frozen TRUE02 source confirms only the experiment name, output path and batch-size references were parameterized. The default TRUE02 entrypoint remains supported.

### Independent verification

A separate read-only agent reconstructed every input from the frozen title file and pair list without importing the production preparation code. It checked all source hashes, exact title strings, directions, expectations, exclusions and model-only inputs.

It then replayed the saved 44 × 32,128 first-token logits using NumPy, independently verified tokenization/native decoding/EOS, all recorded score diagnostics, cutoff decisions, aggregate counts, score orderings and completion hashes. Maximum numerical discrepancy was **8.88e-16**; maximum input length was **30 tokens**, without truncation. No second neural-model load or weight rehash was used; verification peak RSS was approximately 140 MiB.

Verification record (`verification.json`), raw runtime measurements and output hashes (`completion.json`).
