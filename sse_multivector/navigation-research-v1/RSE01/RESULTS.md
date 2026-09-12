# RSE01 — Different strengths, no overall parent-selection improvement

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

[Plan](../RSE01-PLAN.md) · [Execution](EXECUTION.md) · [Every case](CASES.md) · [Analysis](analysis.json) · [Inputs](inputs.json) · [Raw embeddings and entailment relation](embeddings.json) · [All 32,400 scores](scores.json) · [Verification](verification.json).

Six new tests and 17 existing regression tests pass. The 180 inputs are byte-identical to HRC03's prepared inputs; token counts range from 4 to 16, below the author's 32-token limit. No truncation. The released model has 355,369,984 parameters and 1,024-dimensional vectors. The main run used about 2.99 GiB peak process memory and 13.35 seconds total, including 5.65 seconds of encoding. CPU only, two threads, one bounded model process at a time; no paid resources. Previous artifacts are unchanged.

Independent verification instantiated the pinned author's complete RSE class and reproduced all 180 embeddings and the entailment relation bit-for-bit. It independently recalculated all 32,400 pairs, 60 matched and 240 mixed-wording comparisons. Author float32 cosine differs from saved double-precision scores by at most 2.385e-7; no parent, direction or cosine choice changes. The verifier took 11.68 seconds and peaked at about 3.01 GiB. Its source hashes, compatibility details and enforced resource limits are in [verification.json](verification.json).
