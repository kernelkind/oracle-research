# RSE01 — Different strengths, no overall parent-selection improvement

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

RSE selected the intended parent in 49/60 comparisons, the same total as HierarCaps. It improved software and some wording-sensitive cases, but introduced other clear mistakes. Its directional score did not outperform ordinary cosine on its own vectors. This run does not establish RSE as a better standalone category-placement mechanism.

## What changed

Only the model and its native scoring calculation changed. We reused all 180 exact category-description inputs from HRC03: 30 cases across five areas, with two wordings each. No prompts, original notes, masks, definitions, or expected answers were supplied to RSE. Nothing was trained or tuned.

RSE encodes each description independently. Its final first-token representation goes through the released linear layer and tanh. For a proposed relationship, it adds the released entailment vector to the child's raw vector, then calculates cosine with the parent's vector. Higher favors that relationship. Ordinary cosine, without the entailment vector, is the baseline. Neither score is an acceptance probability.

The [author's inference](https://github.com/BinWang28/RSE/blob/2fc202227bf95bd12ce3b41acbbfefb1a45c983f/rse_src/inference.py) defines this operation. The plan and code preserve addition before normalization, entailment index 0, and the trained projection.

## Result 1 — Some areas improve, others regress

Counts below mean “selected the intended parent from the two supplied candidates.” They are not general accuracy estimates. Each pair of wordings belongs to one case, not two independent cases. Existing qualifications about the alternatives remain unchanged.

| Area | RSE entailment | RSE cosine | HierarCaps angle |
| --- | ---: | ---: | ---: |
| Software | 9/12 | 10/12 | 6/12 |
| Economics | 9/12 | 9/12 | 12/12 |
| Political ideas | 12/12 | 12/12 | 11/12 |
| Relationships | 11/12 | 10/12 | 10/12 |
| Food | 8/12 | 9/12 | 10/12 |
| Total | 49/60 | 50/60 | 49/60 |

RSE changed nine of HierarCaps' alternative selections to the intended parent, but changed nine intended selections to the alternative. This is evidence of different behavior, not an overall improvement. Some transitions concern already-qualified alternatives; the concrete examples below provide stronger evidence than treating every count as an absolute judgment.

## Result 2 — A previous wording problem is resolved

**E02. Child:** A central bank raising interest rates

Keep the alternative **Fiscal policy** fixed. Change only the intended parent's wording:

| Intended parent | RSE score | Fixed alternative's RSE score | HierarCaps choice |
| --- | ---: | ---: | --- |
| Monetary policy | 0.428858 | 0.340600 | Intended |
| Central-bank management of money and borrowing conditions | 0.577087 | 0.340600 | Alternative |

RSE selects the monetary-policy category in both versions. It also selects the intended parent across all eight combinations of child, parent and alternative wording for this case. HierarCaps did so in five of eight.

This is a genuine local improvement: changing the parent from a short name to a supported description no longer reverses this placement. RSE's ordinary cosine also selects the intended parent in all eight combinations, so this improvement cannot be credited specifically to the entailment relation. It does not establish general wording robustness.

## Result 3 — Another previous wording problem remains

**S03. Child:** Programs released under the GNU General Public License

Keep the alternative **Closed-source software** fixed:

| Intended parent | RSE score | Fixed alternative's RSE score | RSE choice |
| --- | ---: | ---: | --- |
| Open-source software | 0.726371 | 0.578604 | Intended |
| Software whose source code users may inspect, modify, and redistribute | 0.563498 | 0.578604 | Alternative |

Both intended descriptions cover GPL software. RSE still changes its choice when only that description changes. Although the two matched-wording trials both select the intended parent, checking the wordings independently exposes this failure. HierarCaps had the same parent-only flip.

Across all 30 cases, RSE selected the intended parent in every wording combination for 13 cases, versus eight for HierarCaps. Its own ordinary cosine did so for 14 cases. This is improved stability relative to HierarCaps, but not evidence that the directional addition provides that improvement.

## Result 4 — There is a clear new food mismatch

**F06, wording 2. Child:** A lentil stew made entirely from plant ingredients

| Proposed parent | RSE entailment | RSE cosine |
| --- | ---: | ---: |
| Meals without meat or fish | 0.459323 | 0.528851 |
| Dishes containing meat | 0.636504 | 0.476989 |

The child explicitly excludes meat. RSE's directional score nevertheless favors dishes containing meat. In this wording, ordinary cosine favors the meat-free parent. The learned relation changes that preference in the wrong direction.

RSE's directional score favors the meat-containing alternative in all eight wording combinations for this case. The other matched version uses **Lentil stew made entirely from plant ingredients**, **Vegetarian meals**, and **Meat dishes**; scores are 0.555008 for vegetarian meals and 0.625868 for meat dishes. HierarCaps selected the intended parent in both matched versions and seven of eight wording combinations.

This is stronger evidence than merely calling two related food categories confusing: the competing parent's meaning directly conflicts with the supplied child description.

## Result 5 — The directional calculation does not improve the overall choices

Holding the RSE vectors fixed, adding the entailment relation changes seven matched choices: three move to the intended parent, four move to the alternative. The total falls from 50/60 with cosine to 49/60 with the relation.

One persistent software example is **S01, wording 1**:

**Child:** Blocking cross-site tracking

| Proposed parent | RSE entailment | RSE cosine |
| --- | ---: | ---: |
| Web browser privacy | 0.381531 | 0.438012 |
| Web browser appearance | 0.421560 | 0.425764 |

Cosine favors privacy, but the directional score favors appearance. HierarCaps also preferred appearance here. These results do not show that the input has no useful semantic representation; they show that this directional calculation is not reliably converting that representation into the intended parent preference.

The separate forward-versus-reverse check favors child-to-parent entailment in 44/60 comparisons. A pair can prefer the intended parent over an alternative while still preferring the reverse direction between child and parent. These are different questions; neither is proof of a complete hierarchy.

## All unexpected matched selections

Full child and parent text, both model scores, and every wording combination appear in [CASES.md](CASES.md). These rows are observations with interpretations, not redefined expected labels.

| Case | Alternative selected | Interpretation |
| --- | --- | --- |
| S01 wording 1 | Browser appearance over privacy for blocking tracking | Clear mismatch; shown above. |
| S05 wording 2 | Memory speed/efficiency over safe memory use for preventing use after free | Safety is directly expressed; performance is not. |
| S06 wording 1 | Application software over operating systems for Linux distributions | A distribution can contain applications, but that does not make it an application-software subtype. |
| E03 wording 1 | Domestic sales taxation over international trade for import tariffs | The qualifier “domestic sales” is a poor match for import tariffs. Small score difference: 0.004795. |
| E05 wording 2 | Working-hour agreements over pay/benefits for asking for a pay rise | Salary is supplied; working hours are not. |
| E06 wording 1 | Price collusion over market competition for competing through lower prices | Competing does not supply coordination or collusion. Small difference: 0.003178. |
| R02 wording 2 | Giving personal guidance over respecting limits for letting a friend keep a topic private | The action is allowing privacy, not giving advice. |
| F04 wording 2 | Food decoration over baking for preparing an oven-baked cake | Baking is directly supported; decoration is possible during preparation but not stated. Less decisive than F06. |
| F05 wording 1 | Cutting techniques over cooking methods for pan-frying vegetables | Frying is supplied; cutting is not. |
| F06 both wordings | Meat-containing dishes over meat-free meals for an entirely plant-based stew | Clear mismatch across every wording combination; shown above. |

## What we can conclude

RSE can represent useful relationships across nonvisual subjects. It remedies some HierarCaps problems, including the monetary-policy wording test. But the frozen entailment score is not a demonstrated improvement in overall parent selection, and it still fails clear category comparisons. The evidence does not justify adopting it as the placement rule.

This test does not identify whether remaining problems principally reflect noun-phrase inputs versus training sentences, the learned relation's form, or insufficient category knowledge. Those are possible explanations, not findings. It also does not test generated HDBSCAN descriptions or complete navigation paths. No further experiment was silently substituted for this one.

## Reproduction and preserved evidence

[Plan](RESULTS.md#rse01-study-design) · [Execution](RESULTS.md#rse01-runtime-and-verification) · [Every case](CASES.md) · Analysis (`analysis.json`) · Inputs (`inputs.json`) · Raw embeddings and entailment relation (`embeddings.json`) · All 32,400 scores (`scores.json`) · Verification (`verification.json`).

Six new tests and 17 existing regression tests pass. The 180 inputs are byte-identical to HRC03's prepared inputs; token counts range from 4 to 16, below the author's 32-token limit. No truncation. The released model has 355,369,984 parameters and 1,024-dimensional vectors. The main run used about 2.99 GiB peak process memory and 13.35 seconds total, including 5.65 seconds of encoding. CPU only, two threads, one bounded model process at a time; no paid resources. Previous artifacts are unchanged.

Independent verification instantiated the pinned author's complete RSE class and reproduced all 180 embeddings and the entailment relation bit-for-bit. It independently recalculated all 32,400 pairs, 60 matched and 240 mixed-wording comparisons. Author float32 cosine differs from saved double-precision scores by at most 2.385e-7; no parent, direction or cosine choice changes. The verifier took 11.68 seconds and peaked at about 3.01 GiB. Its source hashes, compatibility details and enforced resource limits are in `verification.json`.

## RSE01 study design

Authorized September 12, 2026. This plan is recorded before model scoring.

Question: does the released RSE entailment score distinguish plausible broader categories from the fixed alternatives more reliably than HierarCaps did on HRC03?

Use the exact frozen HRC03 fixture: 30 cases, two wordings each, five domains, 180 description occurrences. Preserve its original judgments and later qualifications. Fixture SHA256: `d3efece72ebf6f03e4c0b5fe9b1c588fbece361b00599b34389c242a699c2c35`. No new generated text, masks, notes, labels, or hierarchy changes.

Model: `binwang/RSE-RoBERTa-large-10-relations`, revision `b1da9ad30f7c5f943ea35d3c2685df0862ad3cb5`. Weights SHA256: `76ae8a51d65f60b70b526954ad047bc72398d80681ba5b80a8c8dcfa39b87e39`. Author code revision: `2fc202227bf95bd12ce3b41acbbfefb1a45c983f`.

Encode plain descriptions independently. Use the final first-token representation, trained linear layer and tanh. Score `cosine(z(child) + relation[0], z(parent))`; add before normalization. Relation 0 is entailment. Keep plain same-model cosine as a baseline. Do not use the SentEval helper that maximizes the two directions. No training, relation selection, fitted cutoff, or prompt changes.

Check token counts before inference. Use the author's 32-token limit with truncation forbidden; if an input exceeds it, stop and record the issue rather than silently shorten it.

Compare all 60 matched parent choices and the 30 families' stability across all eight combinations of wording. Report direction separately; preferring forward over reverse does not itself establish parent membership. Compare RSE's native score against its own cosine and saved HRC03 results; record both improvements and regressions. No absolute acceptance threshold or universal accuracy claim follows from this constructed fixture.

Verify scoring and projection with test-first checks. Save complete inputs, raw vectors, the learned relation, all ordered pair scores, derived comparisons, model/input/source hashes, runtime and memory. Independently check the implementation against author code and reproduce saved calculations. Present concrete text and both scores for questionable placements; preserve ambiguous cases without silently changing their expected labels.

Resource scope: local CPU only, batch 4, two CPU threads, 6 GiB process/cgroup memory bound, no swap, one model process at a time. One public 1.42 GB weight download; no paid resources. Prior runs remain unchanged. This is a model-transfer diagnostic, not model adoption or construction of a hierarchy.

## RSE01 runtime and verification

Run on local CPU, September 12, 2026. No training or paid resources.

### Source and input identity

- Checkpoint: `binwang/RSE-RoBERTa-large-10-relations` at `b1da9ad30f7c5f943ea35d3c2685df0862ad3cb5`.
- Weight file SHA256: `76ae8a51d65f60b70b526954ad047bc72398d80681ba5b80a8c8dcfa39b87e39`.
- Author source revision: `2fc202227bf95bd12ce3b41acbbfefb1a45c983f`.
- Fixture SHA256: `d3efece72ebf6f03e4c0b5fe9b1c588fbece361b00599b34389c242a699c2c35`.
- Input-record SHA256: `886ea3f362d95c02077f2c7b7c7cd45370e29d86b7120f4de29c9d4a7d3ed277`, identical to HRC03.

Package versions and every downloaded-file hash are in `config.json`. The 1.42 GB weight download used one worker, a 2 GiB/no-swap scope, and no authentication token. No GPU or paid provider was used.

### Main invocation

The run recorded 355,369,984 parameters, 1,024 dimensions, 5.64810058567673 seconds encoding, 13.347875773906708 seconds total, and 3,133,396 KiB peak RSS.

### Compatibility and numerical details

The runner reproduces author inference with the standard `RobertaModel` plus the checkpoint's trained linear/tanh projection. All encoder tensors load strictly; exactly the three expected head tensors remain. The old persisted position-ID buffer is validated against the architecture's fixed sequence before omitting it from the modern nonpersistent state. No trained tensor is discarded or replaced by a random initialization.

The model runs in float32, with eager attention and evaluation/inference mode. Raw embeddings are saved before any normalization. Saved pair scores use Python double-precision arithmetic on those float32 values; the author's example uses float32 tensor cosine. Independent verification records the numerical difference rather than claiming bit-identical scores across arithmetic implementations.

No relation or threshold selection is performed. Relation 0 is the released entailment relation, and scoring uses child-to-parent direction. The symmetric SentEval maximum-of-both-directions helper is deliberately not used.

### Independent author-implementation verification

`verify.py` loads pinned, hash-checked author `model.py` and `model_utils.py`. The unused `from turtle import forward` import is removed only in memory to avoid the irrelevant GUI dependency; inference code is otherwise unchanged. It instantiates `RoBERTaForRSE`, loads the full checkpoint strictly, and invokes `sentemb_forward` through the author class. The legacy fixed position buffer receives the same explicit value check as in the primary runner.

All 180 embeddings and the relation are bit-identical. Independent double-precision score replay differs by at most 3.997e-15. Float32 author cosine differs by at most 2.385e-7; every matched and mixed-wording decision retains the same sign. Original artifact hashes are unchanged. The verifier's model process ran only after the primary process exited.

The verifier fetches and hash-checks the small pinned author source files on each run; model weights remain offline. It prints its report without overwriting the saved verification. Full details are in `verification.json`.
