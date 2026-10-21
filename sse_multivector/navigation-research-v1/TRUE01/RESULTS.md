# TRUE01 — Promising scores; native answers miss valid relationships

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

TRUE is worth investigating further for category containment. Its native answers accepted no invalid relationship in this small test, but missed several valid ones. More importantly, with the sentence input format, its scores placed every valid relationship above every invalid one. That is useful evidence—not a validated deployment rule.

## What we tested

Ten constructed category families across food, software, economics, political ideas, and interpersonal relationships. Each family had two existing wordings. We tested 20 broader–narrower inclusions, their 20 reversals, 40 related alternatives in both directions, and ten directions of five reviewed equivalent descriptions. Expected answers were frozen before inference.

The question was **does A contain B?**, not “which proposed parent scores higher?” TRUE received B as premise and A as hypothesis. Two fixed formats were tested separately:

- Primary: `premise: This text is about {B}. hypothesis: This text is about {A}.`
- Secondary: `premise: {B} hypothesis: {A}`

Only the descriptions were supplied. No original notes, masks, expected answers, demonstrations, or agent context entered the model. There were 90 decisions per format, but only ten constructed families—not 90 independent examples.

## Native answers

These counts use TRUE’s complete greedy generated `0` or `1` answer, not a tuned numerical cutoff.

| Test | Descriptions in sentences | Bare descriptions |
|---|---:|---:|
| Valid broader–narrower inclusions accepted | 14/20 | 9/20 |
| Valid equivalence directions accepted | 8/10 | 8/10 |
| Invalid directions/alternatives rejected | 60/60 | 60/60 |
| Unresolved output | 0/90 | 0/90 |

The primary format gets 82/90 answers right, but that total conceals eight missed valid relationships. For example, it says No to **Vegetarian meals containing Lentil stew made entirely from plant ingredients**. It also misses the expanded GPL/source-code-permissions relationship and one wording of central-bank rate increases under monetary policy. [All unexpected answers, with complete descriptions and analysis](ERRORS.md).

The sentence wrapper changes eleven answers relative to bare text: eight improve and three worsen. In the primary format, only five of ten families have their forward inclusion accepted in both original wordings. Wording sensitivity remains real.

## The important score result

We also saved the probability of TRUE’s first output token being `1`. This is not cosine, a complete-label probability, or calibrated category confidence.

With descriptions in sentences:

- Lowest score for a valid relationship: **0.144155**. A = “Software whose source code users may inspect, modify, and redistribute”; B = “Software distributed under the GPL.”
- Highest score for an invalid relationship: **0.140235**. A = “Memory performance”; B = “Preventing access to freed memory.”

**Every valid relationship scores above every invalid relationship in this fixed sample.** The narrowest gap is only **0.003920**. A cutoff could separate these observed examples, but selecting it here would fit this same sample. We did not select or apply one, and have not shown that the separation transfers to unseen descriptions.

Bare descriptions do not have that separation: their lowest valid score is 0.048672 and highest invalid score is 0.138809. Seven positive–negative score orderings are reversed. This is a concrete difference between the input formats, not proof that the wrapper solves general category containment.

## What this leaves us with

The native No answers do not justify discarding TRUE’s score. Conversely, zero false containments among these 60 negatives does not establish a reliable graph-construction rule. These are clear constructed categories previously used with other models, not an unseen sample of actual generated HDBSCAN descriptions. The NLI-to-topic-membership adaptation, category ambiguity, equivalence, and larger-graph consistency remain separate limitations.

A justified next test would choose a decision rule using one set of category pairs, freeze it, and test it on a separate unseen set. No neural-model training is needed for that. It was **not** performed in TRUE01. No hierarchy was built or changed.

This is not an apples-to-apples accuracy comparison with HRC03/RSE01: those studies primarily tested forced parent preference, while this one tests individual containment decisions on a smaller selected subset.

Every decision (`03bd9e45:sse_multivector/navigation-research-v1/TRUE01/DECISIONS.md`) · [All unexpected answers](ERRORS.md) · [Frozen plan](RESULTS.md#true01-study-design) · [Execution and verification](RESULTS.md#true01-runtime-and-verification) · Raw scores and complete inputs (`scores.jsonl`).

**Selected data:** Compact pair-score results, inputs and parameters for `TRUE01` are selected for release as `numerical/pair-scores-44261922841cf8b2` in the [publication catalog](../../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.

## TRUE01 study design

Frozen before any TRUE inference on September 12, 2026. No training, paid compute, hierarchy changes, or model/threshold selection from results.

### Question

Given category A and category B, does A contain B? Here containment means that membership in B warrants membership in A, not that A and B merely overlap or discuss related things. Equivalent descriptions should pass in both directions. Strict containment should pass in only one direction.

We are testing whether a released sentence-entailment model can implement this decision. That transfer is a hypothesis, not a property guaranteed by NLI training. No hierarchy will be constructed in this test. Missing parent categories remain out of scope.

### Model and inputs

Use `google/t5_xxl_true_nli_mixture`, revision `aa6cfe1dd4257853bfdd772992045f41bfc14988`, offline float32 on CPU. The model card specifies binary output `1` for entailment and `0` for no entailment, with this input serialization:

```text
premise: PREMISE_TEXT hypothesis: HYPOTHESIS_TEXT
```

For **A contains B**, B is the premise and A is the hypothesis. Use two fixed formats, reported separately:

1. Primary, topical membership: `premise: This text is about {B}. hypothesis: This text is about {A}.`
2. Secondary, direct category text: `premise: {B} hypothesis: {A}`

The first format is our task adaptation, not a prompt supplied by the model authors. It addresses categories of notes rather than asserting that an activity is a physical object. The second checks whether the wrapper materially changes the result. Neither is tuned after inspection; do not silently select the better format as a prespecified winner.

Source: [pinned model card](https://huggingface.co/google/t5_xxl_true_nli_mixture/blob/aa6cfe1dd4257853bfdd772992045f41bfc14988/README.md). Its training mixture is SNLI, MNLI, FEVER, SciTail, PAWS, and VitaminC. Do not substitute the TRUE paper's ANLI training mixture for this particular release.

### Frozen examples and expectations

Reuse exact text from `hrc03-fixture.json`, SHA256 `d3efece72ebf6f03e4c0b5fe9b1c588fbece361b00599b34389c242a699c2c35`.

Choose F02/F06 (food), S03/S05 (software), E02/E06 (economics), P01/P03 (politics), and R02/R03 (interpersonal relationships). A separately spawned, clean-context audit reviewed this selection without seeing any TRUE output.

For each of the two existing wordings in each family, independently test:

| A | B | A contains B? |
|---|---|---|
| Broader category | Narrower category | Yes |
| Narrower category | Broader category | No |
| Related alternative | Narrower category | No |
| Narrower category | Related alternative | No |

Also test both directions of these five reviewed equivalences:

| First description | Second description |
|---|---|
| Fermented foods | Foods produced through fermentation |
| Preventing access to freed memory | Preventing a program from using memory after it has been freed |
| Fiscal policy | Government decisions about taxation and spending |
| Decentralization of government | Decentralizing government authority |
| Financial support | Helping someone with money or expenses |

This gives 90 directed decisions per input format: 30 Yes, 60 No. There are ten constructed families, not 90 independent semantic examples. The descriptions were already used with earlier models; this is not an unseen holdout or a representative sample of generated HDBSCAN titles.

Keep existing uncertain cases outside the clean scored subset: S04 can include backup management in file organization; S06 wording 2 does not uniquely identify application software; F03 admits broad harvest-workflow interpretations. P03 stays included with its qualification: local councils may be elected, but transferring authority does not itself require electoral representation.

Do not assume every pair of existing paraphrases is equivalent. Several change scope. Only the five listed equivalences receive mutual-containment expectations. Original cases and prior annotations remain unchanged.

### Measurements and interpretation

Use the complete native greedy generated answer: exactly `1` means Yes, exactly `0` means No, and other or unterminated output is unresolved. Require EOS after the label. Do not tune or apply a score cutoff.

Tokenizer preflight before inference established that `0` is **two tokens**, `[3,632]`, whereas `1` is `[209]`. The initial single-token-label plan was corrected before any model judgment was observed. A whitespace prefix is not a complete No answer. Three generated tokens accommodate either canonical label and EOS. The native generation call also returns its raw first-token logits, avoiding a duplicate encoder pass.

Save the complete generated token IDs and text, full first-token vocabulary logits, and their argmax. Verify that native generation starts with that argmax. Display the full-vocabulary probability of first token `209` as the entailment score. It is not cosine, complete-label probability, or calibrated category-containment confidence. Separately retain the `209`-versus-`3` normalized score and combined prefix probability mass as **prefix-only diagnostics**, never as complete binary-label probabilities. Use max-subtracted softmax to avoid overflow.

Report false containments, missed containments, reversed-direction errors, equivalence results, and differences between the two original wordings. Include complete category texts and raw results for every error, not just selected successes. Report domains separately and preserve semantic qualifications. There is no declared universal passing accuracy or post-hoc optimized score threshold.

If clean obvious false containments remain, inspect them before proposing a deployment rule. If the initial decisions look useful, this supports a separate broader test with actual generated categories, not declaring the hierarchy solved. The pilot does not establish graph consistency, missing-parent generation, or scalability of all-pairs inference.

### Execution safeguards

One local inference process; four CPU threads; batch size four; 60 GiB memory maximum; no swap permitted. No GPU, quantization, fine-tuning, remote model code, or uploaded inputs. One download worker in a separate 2 GiB/no-swap scope. Recheck host resources before inference.

Before inference, raised the initially proposed CPU allowance from two to four threads: the 28-logical-CPU host had a load average near 1.4, while the selected model is approximately 11B parameters. This limits runtime without adding model processes or changing precision, inputs, scores, or RAM allowance. No TRUE judgment had been observed at this point.

Preflight: host had about 100 GiB available RAM and 120 GB free disk. Pinned weights occupy about 45.5 GB; download preserves existing caches. Torch is CPU 2.8.0 and Transformers 4.57.1. Load only pinned public files with `weights_only=True`, verify all five published weight hashes, and reject incomplete parameter loading or input truncation.

New test module first failed with `ModuleNotFoundError` because the production runner did not yet exist. The report and complete-generation tests also first failed because their production functions did not exist. After implementation and independent audit, all twelve new tests and 23 unchanged regression tests passed. Inputs, expected judgments, provenance, scores, and resource measurements are written under a new `TRUE01` directory. The runner refuses to overwrite any existing run.

## TRUE01 runtime and verification

Run locally on September 12, 2026. No training, paid resources, GPU, quantization, or remote model code. Earlier experiment files were not changed.

### Model and input identity

- Model: `google/t5_xxl_true_nli_mixture`, revision `aa6cfe1dd4257853bfdd772992045f41bfc14988`.
- Loaded parameters: **11,307,321,344**, all float32, evaluation/inference mode.
- All five checkpoint weight hashes matched the published pinned manifest. Every missing/unexpected/mismatched/error list was empty.
- Original HRC03 fixture SHA256: `d3efece72ebf6f03e4c0b5fe9b1c588fbece361b00599b34389c242a699c2c35`.
- Exact prepared inputs and runner hash: `started.json`.
- Model file hashes: `model-files.json`. Packages and loading diagnostics: `config.json`.

Input lengths were at most 39 tokens for the sentence format and 29 for bare descriptions. Nothing was truncated. Each pair’s actual model text and token IDs are preserved in `scores.jsonl`.

### Binary generation detail

The pinned tokenizer encodes `0` as `[3,632]` and `1` as `[209]`. A tokenizer-only preflight caught this before model inference. The original single-token-label assumption was corrected before any prediction was observed.

Classification therefore uses complete native greedy generation, with EOS required: `0` means No and `1` means Yes. Three new tokens allow either canonical answer plus EOS. Other or unterminated output would be unresolved; none occurred.

The same generation call returns raw first-token logits. Their argmax agrees with the first generated token for all 180 inputs. The displayed score is full-vocabulary probability of token `209`. A separate normalized comparison of prefixes `209` and `3` is saved only as a diagnostic; whitespace token `3` is not itself treated as a complete No answer.

### Resource use

The approximately 45.5 GB public checkpoint download used one weight-file worker, a 2 GiB/no-swap scope, and no authentication token. A separate brief, bounded tokenizer-only fetch checked the output encoding while weights downloaded. The weight download took about 32 minutes. No existing cache was deleted.

Inference used one CPU process, four threads, batch size four, a **60 GiB memory limit**, and **no swap**. The 28-logical-CPU host had about 100 GiB available RAM before launch. Four threads were selected before inference, replacing the initial two-thread proposal to avoid unnecessary delay on a lightly loaded host.

- Total runner time including hashing/loading: **428.02 seconds**.
- Generation and result packaging: **385.35 seconds**.
- First batch: **171.1 seconds**, including demand-loading weight pages. Subsequent batches generally took about 4–6 seconds.
- Peak process RSS: **43.62 GiB**. Observed scope memory stayed below its 60 GiB limit, with zero scope swap.

### Test-first checks and independent replay

A clean-context independent agent reviewed the frozen expectations before outputs existed, audited the runner, and later reviewed every primary-format disagreement. No subagent performed model inference or altered data.

The separate read-only verifier (`03bd9e45:sse_multivector/navigation-research-v1/TRUE01/verify.py`) imports no production scoring code and loads no neural model. It reconstructs every pair’s direction and serialization from the frozen fixture, retokenizes the actual input strings, decodes complete saved outputs, checks EOS and raw-logit argmax, recomputes scores with NumPy, and independently recounts decisions. All 180 match. Maximum probability replay difference: **5.55e-16**. Artifact hashes and the runner’s recorded hash match. Verification results (`verification.json`).

This verifies the saved calculation and protocol; it is not an independent second model run or proof that our expected semantic labels are universally correct.
