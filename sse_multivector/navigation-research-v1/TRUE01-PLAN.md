# TRUE01 — Does TRUE recognize category containment?

Frozen before any TRUE inference on September 12, 2026. No training, paid compute, hierarchy changes, or model/threshold selection from results.

## Question

Given category A and category B, does A contain B? Here containment means that membership in B warrants membership in A, not that A and B merely overlap or discuss related things. Equivalent descriptions should pass in both directions. Strict containment should pass in only one direction.

We are testing whether a released sentence-entailment model can implement this decision. That transfer is a hypothesis, not a property guaranteed by NLI training. No hierarchy will be constructed in this test. Missing parent categories remain out of scope.

## Model and inputs

Use `google/t5_xxl_true_nli_mixture`, revision `aa6cfe1dd4257853bfdd772992045f41bfc14988`, offline float32 on CPU. The model card specifies binary output `1` for entailment and `0` for no entailment, with this input serialization:

```text
premise: PREMISE_TEXT hypothesis: HYPOTHESIS_TEXT
```

For **A contains B**, B is the premise and A is the hypothesis. Use two fixed formats, reported separately:

1. Primary, topical membership: `premise: This text is about {B}. hypothesis: This text is about {A}.`
2. Secondary, direct category text: `premise: {B} hypothesis: {A}`

The first format is our task adaptation, not a prompt supplied by the model authors. It addresses categories of notes rather than asserting that an activity is a physical object. The second checks whether the wrapper materially changes the result. Neither is tuned after inspection; do not silently select the better format as a prespecified winner.

Source: [pinned model card](https://huggingface.co/google/t5_xxl_true_nli_mixture/blob/aa6cfe1dd4257853bfdd772992045f41bfc14988/README.md). Its training mixture is SNLI, MNLI, FEVER, SciTail, PAWS, and VitaminC. Do not substitute the TRUE paper's ANLI training mixture for this particular release.

## Frozen examples and expectations

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

## Measurements and interpretation

Use the complete native greedy generated answer: exactly `1` means Yes, exactly `0` means No, and other or unterminated output is unresolved. Require EOS after the label. Do not tune or apply a score cutoff.

Tokenizer preflight before inference established that `0` is **two tokens**, `[3,632]`, whereas `1` is `[209]`. The initial single-token-label plan was corrected before any model judgment was observed. A whitespace prefix is not a complete No answer. Three generated tokens accommodate either canonical label and EOS. The native generation call also returns its raw first-token logits, avoiding a duplicate encoder pass.

Save the complete generated token IDs and text, full first-token vocabulary logits, and their argmax. Verify that native generation starts with that argmax. Display the full-vocabulary probability of first token `209` as the entailment score. It is not cosine, complete-label probability, or calibrated category-containment confidence. Separately retain the `209`-versus-`3` normalized score and combined prefix probability mass as **prefix-only diagnostics**, never as complete binary-label probabilities. Use max-subtracted softmax to avoid overflow.

Report false containments, missed containments, reversed-direction errors, equivalence results, and differences between the two original wordings. Include complete category texts and raw results for every error, not just selected successes. Report domains separately and preserve semantic qualifications. There is no declared universal passing accuracy or post-hoc optimized score threshold.

If clean obvious false containments remain, inspect them before proposing a deployment rule. If the initial decisions look useful, this supports a separate broader test with actual generated categories, not declaring the hierarchy solved. The pilot does not establish graph consistency, missing-parent generation, or scalability of all-pairs inference.

## Execution safeguards

One local inference process; four CPU threads; batch size four; 60 GiB memory maximum; no swap permitted. No GPU, quantization, fine-tuning, remote model code, or uploaded inputs. One download worker in a separate 2 GiB/no-swap scope. Recheck host resources before inference.

Before inference, raised the initially proposed CPU allowance from two to four threads: the 28-logical-CPU host had a load average near 1.4, while the selected model is approximately 11B parameters. This limits runtime without adding model processes or changing precision, inputs, scores, or RAM allowance. No TRUE judgment had been observed at this point.

Preflight: host had about 100 GiB available RAM and 120 GB free disk. Pinned weights occupy about 45.5 GB; download preserves existing caches. Torch is CPU 2.8.0 and Transformers 4.57.1. Load only pinned public files with `weights_only=True`, verify all five published weight hashes, and reject incomplete parameter loading or input truncation.

New test module first failed with `ModuleNotFoundError` because the production runner did not yet exist. The report and complete-generation tests also first failed because their production functions did not exist. After implementation and independent audit, all twelve new tests and 23 unchanged regression tests passed. Inputs, expected judgments, provenance, scores, and resource measurements are written under a new `TRUE01` directory. The runner refuses to overwrite any existing run.
