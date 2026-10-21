# TRUE04 — Containment across all 61 generated group titles

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

TRUE recovered many useful parent–child relationships. It also accepted some wrong relationships in both directions, which would create false category equivalences if used directly to build the graph.

All **3,660 ordered questions** ran, without cosine filtering. The original 61 groups have **58 distinct title strings**; repeated Food, Coffee and Bitcoin groups remain separate. The exact v20/Astra-low titles, model, input wording and cutoff were unchanged. No hierarchy was constructed.

## What was tested

For the question **Does A contain B?**, TRUE received:

```text
premise: This text is about {B}. hypothesis: This text is about {A}.
```

It saw only those titles, not masks, notes, IDs or expected answers. The score is the full-vocabulary probability of first generating token `1`, **not cosine or a calibrated probability of containment**. The native answer is the model's complete generated Yes/No label. The separate frozen rule accepts **score > 0.142**.

Before inspecting scores, reviewers nominated 120 clear relationships and 42 ambiguous ones. Unlisted pairs were left unlabeled, not presumed No. After scoring, every accepted title pair was reviewed; a fresh reviewer also reconsidered the missed nominations without seeing scores. These semantic judgments are revisable, not a uniquely correct hierarchy. The [reference record](../TRUE04-REFERENCE-REVIEW.md) explains the process and scope choices.

## Accepted relationships

| Decision rule | Accepted directions | Reasonable | Incorrect | Ambiguous |
|---|---:|---:|---:|---:|
| Fixed score > 0.142 | 106 | 91 | 9 | 6 |
| Native generated Yes | 86 | 79 | 4 | 3 |

Because titles repeat, these are not independent semantic examples. Collapsing only identical ordered title strings for reporting gives **64 cutoff-accepted questions: 53 reasonable, 6 incorrect, 5 ambiguous**. The native answer accepts 49 distinct questions: 45 reasonable, 2 incorrect, 2 ambiguous.

The lower cutoff adds 20 directions over native Yes: **12 reasonable, 5 incorrect and 3 ambiguous**. That is a tradeoff, not a clean improvement or a reason to change the rule after this run.

Some useful accepted questions:

| A: proposed parent | B: proposed child | Native | Score |
|---|---|---|---:|
| Food | Food Ingredients | Yes | 0.895404 |
| Food Ingredients | Sea Salt as a Food Ingredient | Yes | 0.819593 |
| Coffee | Coffee Bean Preparation | Yes | 0.836168 |
| Coffee | Appreciating Coffee for Its Flavor | Yes | 0.967635 |
| Coffee | Coffee Chains | No | 0.435481 |
| Poultry-Based Food Preparation | Making Chicken Stock | Yes | 0.903487 |
| Bitcoin | Satoshi Bitcoin Units | Yes | 0.624657 |
| Nostr | Grow Nostr Campaign | Yes | 0.603691 |

All 64 accepted title questions, not just these examples, appear in [the complete review](REVIEW.md). Scores in this report are rounded to six decimals; exact values are preserved in `scores.jsonl`.

## The six distinct incorrect accepted questions

**1. Does Food contain Nostr?** Native **Yes**; score **0.546812**; cutoff **Yes**.

```text
premise: This text is about Nostr. hypothesis: This text is about Food.
```

Nostr is a communication-network topic, not a food subcategory. There is no food restriction in the title. This occurs twice because two original groups have the title Food.

**2. Does Nostr contain Food?** Native **Yes**; score **0.644765**; cutoff **Yes**.

```text
premise: This text is about Food. hypothesis: This text is about Nostr.
```

Food discussions can appear on Nostr, but that does not make Food a subcategory of Nostr. This also occurs twice. Together with question 1, it would incorrectly make Food and Nostr equivalent **even using native answers alone**. The two duplicate-input scores differ slightly in their last decimal places; both full values are saved.

**3. Does Nostr contain Consuming Excessive Amounts of Food or Drink?** Native **No**; score **0.160344**; cutoff **Yes**.

```text
premise: This text is about Consuming Excessive Amounts of Food or Drink. hypothesis: This text is about Nostr.
```

The eating-and-drinking category has no Nostr-specific meaning. The fixed cutoff introduces this acceptance; the native answer rejects it.

**4. Does Daytime Greetings contain How the Day Is Going?** Native **No**; score **0.336519**; cutoff **Yes**.

```text
premise: This text is about How the Day Is Going. hypothesis: This text is about Daytime Greetings.
```

A report about someone's day need not be a greeting. The subjects are related, but the broader day-status title does not fit wholly inside greetings. The independent reviewer agreed with this distinction.

**5. Does Coffee Consumption contain Coffee?** Native **No**; score **0.186424**; cutoff **Yes**.

```text
premise: This text is about Coffee. hypothesis: This text is about Coffee Consumption.
```

Coffee includes cultivation, preparation and trade, not just consumption. The correct direction, Coffee contains Coffee Consumption, scores **0.966989** and is accepted. The wrong reverse occurs twice because Coffee has two source groups. This reproduces the earlier TRUE03 error rather than supplying an independent new failure.

**6. Does Advice on Meat Consumption contain Meat Eating?** Native **No**; score **0.237189**; cutoff **Yes**.

```text
premise: This text is about Meat Eating. hypothesis: This text is about Advice on Meat Consumption.
```

Meat Eating also covers habits, experiences and descriptions that are not advice. The correct direction, Meat Eating contains Advice on Meat Consumption, scores **0.934846** and is accepted. Again the cutoff accepts both directions where only one is appropriate.

These are **six distinct questions and nine original directions**, not nine independent failure mechanisms. The run does not isolate whether individual errors come from title interpretation, the topic-sentence wording, learned knowledge or other model behavior.

## Relationships the model missed

| Pre-score nominations | Directions | Recovered by cutoff | Recovered by native Yes |
|---|---:|---:|---:|
| All clear nominations | 120 | 90 | 79 |
| Food as parent | 74 | 62 | 56 |
| Other parents | 46 | 28 | 23 |

At the distinct-title level, the cutoff recovers **52 of 75** nominated questions; native Yes recovers **45 of 75**. These are recovery counts for an explicitly nominated reference, **not total recall or overall accuracy**.

The 30 missed directions represent 23 distinct questions. Fresh review upheld 20 of those nominations and left three unresolved. Examples upheld by both reviews:

| A: proposed parent | B: proposed child | Native | Score |
|---|---|---|---:|
| Human Diet and Eating Behavior | Meat Eating | No | 0.116333 |
| Poultry and eggs | Making Chicken Stock | No | 0.131106 |
| Poultry and eggs | Poultry-Based Food Preparation | No | 0.039920 |
| Communication | Weekend Well-Wishes | No | 0.074170 |
| Food | Coffee | No | 0.010624 |

Food was interpreted broadly to include beverages; that scope is an explicit human choice. The three unresolved nominations are Communication contains Advice on Meat Consumption, Nostr contains Plebchain, and Communication contains Plebchain. The first depends on the scope of Communication; the fresh reviewer could not confirm the meaning of Plebchain. They remain visible disputes, not three proven errors. [The complete review](REVIEW.md) shows all 23 missed questions and their reasons.

## Implications for the hierarchy

**There is real containment signal.** Useful chains such as Food → Food Ingredients → Sea Salt as a Food Ingredient and Coffee → Coffee Consumption → Appreciating Coffee for Its Flavor are present. This is stronger evidence than the selected TRUE03 pilot alone, though the corpus remains food-heavy.

**Reciprocal Yes is not reliable evidence of equivalence.** Native answers falsely equate Food and Nostr. The cutoff additionally falsely equates Coffee with Coffee Consumption and Meat Eating with Advice on Meat Consumption. No equivalence consolidation was performed.

**Pair decisions can be inconsistent as a collection.** For example, Food contains Nostr and Nostr contains Grow Nostr Campaign are accepted, but Food contains Grow Nostr Campaign is rejected at **0.064004**. Taking transitive closure would propagate the first wrong link. The saved diagnostics contain 58 such original-ID triples for native answers and 70 for the cutoff. These reuse links and duplicate titles; they are consequences of existing errors or omissions, not that many independent failures.

**A different cutoff cannot perfectly order this observed set.** Wrong native-positive Food/Nostr scores exceed many reasonable rejected relationships. This does not establish that TRUE is unusable or that occasional errors are unacceptable. It establishes a concrete tradeoff that a hierarchy using these decisions would inherit; perfect separation was not a requirement of this experiment.

The result supports TRUE as a source of many useful proposed relationships, but not treating every positive or reciprocal pair as automatically trustworthy. It does not yet measure the resulting browsing experience. No title, mask, group membership, model wording or cutoff was changed; no hierarchy was generated or repaired.

## Verification and preserved evidence

All 44 earlier TRUE03 inputs and decisions reproduced unchanged: 41/44 still match that pilot's original expectations. That repeat checks implementation continuity, not new generalization.

An independent audit verified every input, score and saved decision, replayed all first-token probabilities from the saved logits, and independently reproduced the complete semantic-analysis arithmetic. It did not re-adjudicate semantic judgments. The one offline CPU run took **76 minutes**, with about **44.24 GiB peak process memory** and no run-scope swap. No additional inference was used for verification.

- [Every accepted relationship and missed nomination](REVIEW.md), all 3,660 decisions (`03bd9e45:sse_multivector/navigation-research-v1/TRUE04/DECISIONS.md`).
- Exact inputs (`inputs.json`), native outputs and full-precision scores (`scores.jsonl`), semantic analysis (`semantic-analysis.json`), accepted-pair judgments (`title-pair-judgments.json`).
- [Frozen plan](RESULTS.md#true04-study-design), pre-score reference (`../true04-reference.json`), [reference-review history](../TRUE04-REFERENCE-REVIEW.md), fresh review of misses (`missed-reference-review.json`).
- [Execution, tests and resource details](RESULTS.md#true04-runtime-and-verification), independent verification (`verification.json`), completion hashes (`completion.json`).

The 449 MiB raw-logit file remains locally preserved as `first-token-logits.npy`, excluded from Git by an exact path rule. Its hash is in the completion record. Inputs, outputs, reviews and summaries remain with the original run; selected final results are identified below. Shared source lives in `sse_multivector/`, with the original run layout preserved in Git history.

**Selected data:** Compact pair-score results, inputs and parameters for `TRUE04` are selected for release as `numerical/pair-scores-7dd83c45e206d5c8` in the [publication catalog](../../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.

## TRUE04 study design

### Question

Does the unchanged TRUE03 setup make useful containment decisions across the complete set of 61 original HDBv2 group titles, rather than just the selected pilot pairs?

The user approved this expansion. Keep the exact v20/Astra-low titles, model, input wording, score calculation and **score > 0.142** rule. Do not generate titles, change memberships, construct a hierarchy, retune a cutoff or filter pairs by cosine.

### Inputs

Source: `../hdbv2-node-titles-v20-astra-low/titles.json`, SHA256 `424ffe683fe5fdb3de152cfc6fa09496dfef9fdef422e7a22618b28cc1e20716`.

Score all **3,660 ordered pairs** of distinct group IDs. The 61 groups have 58 distinct title strings; repeated Food, Coffee and Bitcoin titles remain separate source groups. Repeated strings are not independent evidence of semantic generalization.

For **A contains B?**, TRUE sees only:

No masks, notes, expected answers, IDs or reviewer explanations enter the model. Its native answer and the cutoff decision are recorded separately. The score is the full-vocabulary probability of the first output token being `1`, not cosine or a calibrated probability of containment.

### Semantic review

Before inspecting scores, two clean-context reviewers consider all possible parents for disjoint halves of the child-title list. They nominate clear containments and scope-ambiguous relationships, with short reasons. The coordinating reviewer checks these nominations and freezes the resulting reference before inspecting predictions. Unlisted pairs are **not** silently labeled No.

This is a revisable semantic reference, not a prescribed unique hierarchy. Ordinary category meanings guide the judgments; merely related subjects need not contain one another. Do not reject reasonable emergent relationships because they were unexpected, or elevate niche counterexamples into decisive failures.

After inference:

1. Inspect every accepted relationship for valid containment, a clear wrong link, or genuine ambiguity.
2. Inspect missed relationships from the pre-score reference. Preserve disagreements with that reference explicitly.
3. Recheck the 44 TRUE03 directions as a repeat of known evidence, not independent validation.
4. Inspect reciprocal decisions and inconsistent chains. Do not consolidate reciprocal errors into equivalent categories or silently repair the output.

Report accepted-link quality and recovery of the clear reference separately. Do not present a high overall accuracy dominated by thousands of unrelated negative pairs. Show exact titles, model inputs, scores and semantic reasons for concrete problems. This test cannot establish title-to-mask fidelity, missing-parent generation or general performance outside this collection.

### Execution

One offline CPU process using the pinned `google/t5_xxl_true_nli_mixture` revision `aa6cfe1dd4257853bfdd772992045f41bfc14988`, float32, four threads and batch four. Keep the TRUE03 inference function unchanged. Extend reporting to accept unlabeled rows rather than fabricate an answer key.

Use the existing Python 3.11.14 runtime and cached packages/model; no paid calls, rentals, training or downloads. Require 70 GiB available memory before launch. Run under a 60 GiB memory limit, zero permitted swap and four-CPU quota. Do not stop unrelated processes. Save a new `TRUE04/` output, refusing overwrite; preserve all prior experiments.

Freeze source titles, all inputs, runner/scorer code and hashes before loading. Preserve native outputs, full first-token logits, scores, runtime/resource records and analysis. Independently verify inputs and replay scores from saved logits without a second model load. Full inference is expected to take substantially longer than the 44-question pilot.

## TRUE04 runtime and verification

The approved [TRUE04 plan](RESULTS.md#true04-study-design) completed one offline CPU run over all 3,660 ordered pairs of distinct source group IDs. This record documents execution and provenance, not a new semantic assessment.

### Frozen inputs and decisions

The source was `sse_multivector/hdbv2-node-titles-v20-astra-low/titles.json`, preserved byte-for-byte as `titles.json`, SHA256 `424ffe683fe5fdb3de152cfc6fa09496dfef9fdef422e7a22618b28cc1e20716`. Its 61 groups have 58 distinct title strings: repeated Food, Coffee and Bitcoin titles remain separate groups. There are 1,830 unordered group pairs and 3,309 unique model-input strings. No titles or memberships were changed.

Each row asks **A contains B?**: does belonging to B warrant belonging to A? B is the premise and A the hypothesis, with the exact input:

Only the exact title strings enter this text. IDs remain row metadata; masks, source notes, expected answers and review explanations are absent. `inputs.json` has SHA256 `e4e118d4ac430ea74dade05f6c3135a8ecce574490f47af9b2463df7609ac17c`.

`started.json` records the input and four source-file hashes. The runner froze those files before checkpoint hashing/loading and refused an existing output directory. The frozen copies are `true_all_titles_probe.py`, `true_holdout_probe.py`, `true_category_probe.py` and `hierarcaps_mask_probe.py`. Verification found the inference function, scorer and threshold behavior unchanged from TRUE03.

The model was cached `google/t5_xxl_true_nli_mixture`, revision `aa6cfe1dd4257853bfdd772992045f41bfc14988`, with 11,307,321,344 float32 parameters. `model-files.json` records checkpoint/tokenizer hashes; the runner checked all five weight-shard hashes before loading. `config.json` records no missing, unexpected or mismatched keys, or loading errors.

Two decisions were retained separately:

- Native: complete greedy output `0` or `1`, with EOS required and no cutoff. Tokenization is `0` → `[3, 632]`, `1` → `[209]`; the initial token `3` alone is not a complete No answer.
- Cutoff: `entailment_score > 0.142`, strictly greater than. The score is the full-vocabulary first-output-token probability of token `209`, not the binary-renormalized label-prefix score or a calibrated probability of containment.

Generation used no sampling, one beam, at most three new tokens and seed 0. No input truncation was allowed; the largest input was 43 tokens against a 512-token limit.

### Runtime and resources

The existing Python 3.11.14 runtime used torch `2.8.0+cpu`, transformers `4.57.1`, huggingface_hub `0.36.2`, numpy `2.3.4` and safetensors `0.6.2`. Inference used CPU float32, four threads, one inter-op thread and batches of four (915 batches). No external paid API, model/package download, training or rental was used for this execution.

`resources.json` records launch at `2026-09-14 20:27:58 UTC`, 107 GiB available host memory at preflight, and no concurrent large model process. The launch required at least 70 GiB available, then applied a 60 GiB memory limit, zero permitted scope swap and a four-CPU quota. All recorded active-scope samples reported `MemorySwapCurrent=0`. About 12 GiB of host swap was already in use before launch; that is not swap used by this run.

`completion.json` records 3,660 completed rows, 4,542.877 seconds for the inference interval and 4,568.646 seconds total (76 minutes 8.646 seconds), including a 25.769-second startup/load interval from `config.json`. These are runner timers, not launch-to-last-observation wall time; the inference interval also includes result-artifact construction. Peak process RSS was 46,387,100 KiB (44.24 GiB). The smaller sampled scope `MemoryPeak` values in `resources.json` are a separate accounting observation, not a replacement for process RSS. The resource record reports successful process exit and an inactive scope, observed at `21:47:27 UTC`.

### Saved evidence and verification

The original inputs, frozen source, scores/native token sequences, decisions, configuration, resource records and review/analysis JSON were retained with the run. Generated artifacts are outside this Git checkout; selected final results are identified below. `first-token-logits.npy` remains local and explicitly Git-ignored: 470,354,048 bytes (about 449 MiB), shape `(3660, 32128)`, float32. Its SHA256 is `f5b4eddd88edb02ccbd970e58cdb02283053190111b6d82877264678f4b7f7c4`, recorded in `completion.json` and `verification.json`. A Git checkout alone does not include these raw logits or the cached model weights.

The independent integrity review passed without discrepancies. It reconstructed all inputs and input tokens, checked artifact/source hashes and every machine-produced decision/report row, and replayed all 117,588,480 saved finite logits using full-vocabulary softmax in float64. Numeric differences from stored diagnostics were within `2e-15`; every cutoff decision matched the strict rule. It also checked semantic-analysis arithmetic, not the correctness of semantic judgments. No model, torch or transformers was imported for verification, and no inference was repeated.

Verification limits remain explicit:

- First-token logits establish the first greedy token and displayed score. Later-token logits were not saved; complete labels/EOS were checked against saved generated sequences and tokenizer decoding, not independent later-token inference.
- The review checked nonweight model files and the recorded manifest but did not reread or rehash weight shards. Their hashes were checked by the original runner.
- All 44 reused TRUE03 inputs/tokenizations and native/cutoff decisions matched. Only 19 logits rows were bit-identical; the maximum score difference was `6.700754752175797e-7`. This is not a claim of bit-for-bit inference reproducibility or independent new validation.
- Scope exit/resource observations are recorded separately from numerical replay. Arithmetic/integrity checks do not establish semantic correctness or general population accuracy.

```text
python3 -m unittest test_true_all_titles_probe test_true_generated_title_probe test_true_holdout_probe test_true_category_probe
python3.11 -m unittest test_true_category_probe test_rse_category_probe test_hierarcaps_category_probe test_hierarcaps_mask_probe
```
