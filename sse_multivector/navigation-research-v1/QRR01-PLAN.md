# QRR01 — Qwen3-Reranker parent ranking and rejection on the frozen HRC03 fixture

Recorded before any model scoring. Execution requires separate user approval of
this plan.

Question: does `Qwen/Qwen3-Reranker-8B`, used with its released query/document
relevance interface, rank the intended broader category above a plausible
alternative on the exact frozen HRC03 fixture, and do its absolute scores
separate valid parent pairs from invalid ones?

This is a model-transfer diagnostic for the open node-relationship stage. It is
not model adoption, not construction of a hierarchy, and not a claim about the
real HR02 node titles and masks.

## Material

- Exact frozen HRC03 fixture: `../hrc03-fixture.json`, SHA256
  `d3efece72ebf6f03e4c0b5fe9b1c588fbece361b00599b34389c242a699c2c35`.
  30 families, two wordings each, 60 matched parent comparisons, five domains.
  Its original judgments and later qualifications are preserved and unchanged.
  No new generated text, masks, notes, labels, or hierarchy changes. The only
  new material is the rejection-probe recombination declared below, built
  entirely from frozen fixture strings by a deterministic rule.
- Model: `Qwen/Qwen3-Reranker-8B`, local cache snapshot
  `77d193c791ed757ca307ee72715aa132723da912`, offline only. Weight SHA256s:
  `22cdfea4a13b7b3e866573800eeeb638fc38962940adf631d06dc03befed047a`,
  `d2163b74137e35b4614bd2aa5bf27bcb07de4ca61c6962495feb968385eb0df8`,
  `a5038caa78c817e8acce6806104869675938a33fd4e60ed038e9931d390d6989`,
  `247f85538c5996d4c296291b0e4004f618c9b17ca8cdc25d1fc726567eb15803`,
  `8ba41b93c2e4ec8339ad16b000bc977fde196aeac054956cbfc8c0186ee6d4cf`;
  index `8a22e7ffd6001796256c0be7c73594835b6f907eec442fde691301ebf35087d9`;
  config `e87a4f50c475c7276fc642eabfc986a7c8da1c8a30a4ee34b4979048b330f2be`;
  tokenizer `aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4`.
- Author inference reference: `Qwen3-Embedding` example
  `qwen3_reranker_transformers.py`, SHA256
  `c8a5b364b0d218670cc2bad8241e095e67a519e3c0f084f28cd1ff2e7486fa6c`
  (the copy under `/tmp/qwen3-embedding-src/examples`; not a git checkout).
  The scoring formula and prompt assembly are copied from it and checked
  against it, not re-derived.

## Fixed scoring rule

- Prompt assembly exactly as the author example: fixed system/user wrapper
  strings and `<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {doc}`
  body, last-token logits, `no`/`yes` token ids.
- Fixed instruction, not tuned: "Judge whether the Document's topic is a
  narrower instance of the Query's topic."
- `Query` = candidate parent phrase (a fixture `broader` or `alternative`
  string). `Document` = child phrase (the fixture `narrower` string). This
  direction is chosen once here; a direction flip would be a separate
  experiment, not a repair of this one.
- Score = `exp(log_softmax([logit_no, logit_yes])[1])`, i.e. the author's
  `compute_logits`. The sigmoid-looking score is not a calibrated membership
  probability and is not compared across differently phrased queries as if it
  were one.
- `max_length` 4096, author truncation behavior; inputs beyond it are recorded
  as issues rather than silently shortened. Exact tie between the two candidate
  scores counts as an incorrect comparison.
- Declared deviations from the author snippet: CPU execution with
  `torch.bfloat16` instead of CUDA float16 with flash-attention-2, batch size
  one. No other deviation; every difference is recorded in the execution
  record.

## Ranking comparison

Score all 60 matched comparisons: each family's two wordings, each wording's
intended `broader` and its `alternative` — 120 pair scores. A comparison is
correct when score(intended broader) > score(alternative).

Report: correct comparisons out of 60 against the recorded HRC03/RSE01
baselines (HierarCaps 49/60, cosine on HierarCaps vectors 50/60, RSE 49/60,
cosine on RSE vectors 50/60); families where both wordings agree with the
expected choice; families whose two wordings disagree in outcome; every
mismatch with its exact texts and scores. These baselines are comparisons on
this fixture, not accuracy claims.

## Rejection probe

The trap recorded in `CATEGORY-SUBSUMPTION-MODELS-RESEARCH.md` is that a
ranking score can choose the better of two bad parents without being able to
reject that neither fits. Two bounded checks, both from frozen strings:

1. **Cutoff existence.** The ranking run already yields 60 invalid-pair scores
   (every `alternative`). Ask only whether any single threshold on this
   material separates all 60 valid-pair scores (intended `broader`) from all
   invalid-pair scores. Report the overlap count and the extreme violating
   pairs. No threshold is fitted or adopted; overlapping ranges are themselves
   the "no cutoff can fix this" evidence, as in RER01.
2. **Both-wrong pairs.** For each family, wording 1 only, score two candidate
   parents that are neither the intended `broader` nor the family's own
   `alternative`: donor rule, family index `i` donates its `broader` string
   from families `(i+10) mod 30` and `(i+20) mod 30`, advancing the offset by
   +1 until the donor family has a different domain and its `broader` string
   differs from the child's `broader`. 30 families × 2 = 60 additional pair
   scores. Report how often the larger of the two wrong scores still meets or
   exceeds the median valid-pair score, and every case where it does. The
   model's preference between two wrong parents is recorded, never treated as
   a placement.

Total bounded workload: 180 pair scores. The donor pairing is computed and
saved before scoring and never adjusted after seeing any score.

## Verification and reproducibility

- Test-first unit checks: the rendered prompt string for one frozen fixture
  case (exact expected text), the score formula against a manual
  `sigmoid(logit_yes - logit_no)` calculation, the tie rule, and the donor
  pairing rule against its definition.
- Independent check that prompt assembly and `compute_logits` match the hashed
  author reference.
- Replay five pre-registered pairs (fixed in the saved inputs before the main
  run) in a separate process and compare scores for exact equality; record any
  difference instead of rerunning until it disappears.
- Save `inputs.json`, `scores.json`, `analysis.json`, `verification.json` and
  `EXECUTION.md` under `QRR01/`, with fixture, model, weight, source and input
  hashes, runtime and peak memory. The run refuses to overwrite `QRR01/`.

## Resource scope

Local CPU only; this host has no GPU. One fresh pinned environment (recorded
requirements and installed versions; the earlier probe venv in `/tmp` is gone),
`HF_HUB_OFFLINE=1` `TRANSFORMERS_OFFLINE=1`, model loaded from the local cache
only. `systemd-run --user --scope` with a memory bound of 48 GiB, no swap and a
CPU quota; batch size one. No paid API, no remote compute, no training, no
network access. Estimated a few CPU hours for 180 forward passes; recorded, not
optimized.

## What this run cannot establish

Ranking two candidates is not absolute rejection; the rejection probe only
tests whether separation exists on this material. The fixture's constructed
title-like descriptions are a proxy for node titles, not the real 129 HR02
titles and masks, and no result transfers to them without a separate check. No
production placement rule, cost or throughput figure follows from 180 local
scores. Every case is inspected; aggregate counts never replace the recorded
counterexamples.
