# V22 versus v23: interpreting names and tags

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

V23 did not fix the Coffeechain title: **all three responses were “Coffee shop chains.”** The two control groups remained appropriate. There is no demonstrated reason to adopt the added instruction.

Both versions ran three times on each group: **18 fresh Astra-low calls**. V23 adds only the approved instruction about interpreting names and tags. Exact masks, ordering, model, effort and wrapper stayed fixed. Earlier outputs were not substituted for fresh baseline calls.

## Every result

The group headings and analysis below were not supplied to generation. Each line shows one complete mask.

### Sf5a4b23523 — Coffeechain

- V797: ⟦Sipping⟧ ⟦#coffeechain⟧
- V187: ⟦coffeechain⟧
- V656: ⟦#coffeechain⟧
- V297: ⟦#coffeechain⟧
- V865: ⟦#coffeechain⟧
- V126: ⟦#coffeechain⟧
- V043: ⟦coffeechain⟧

| Trial | V22 | V23 |
|---|---|---|
| 1 | Coffee chains | Coffee shop chains |
| 2 | Coffee shop chains | Coffee shop chains |
| 3 | Coffee-shop chains | Coffee shop chains |

Titles explicitly naming shop chains impose an unsupported commercial interpretation. Coffee chains remains ambiguous rather than a demonstrated correction; that wording was already surfaced in the previous test.

### Sd5f4538ab9 — Food

- V901: ⟦omlette⟧ ⟦topped⟧ ⟦parm⟧
- V539: ⟦Mushroom Risotto with Shrimp⟧ ⟦Pepper⟧
- V881: ⟦Spaghetti Bolognaise⟧ ⟦Salt and pepper to taste⟧
- V902: ⟦omlette⟧ ⟦topped⟧ ⟦jalepenos⟧ ⟦parm⟧
- V532: ⟦Mushroom Risotto with Shrimp⟧ ⟦Parsley⟧

| Trial | V22 | V23 |
|---|---|---|
| 1 | Dishes with toppings or seasonings | Seasonings and toppings for savory dishes |
| 2 | Savory dishes with seasonings or toppings | Savory dishes with seasonings or toppings |
| 3 | Savory dishes with seasonings or toppings | Savory dishes with toppings or seasonings |

All titles preserve the shared food relationship: savory dishes with toppings/seasonings or those additions used for savory dishes. The change of emphasis is reasonable; none describes the input as phrases or keywords.

### S24afa84c49 — Coffee preparation

- V410: ⟦grind coffee beans⟧
- V411: ⟦Rise⟧ ⟦grind coffee beans⟧
- V793: ⟦coffee⟧ ⟦Roasting your own beans⟧

| Trial | V22 | V23 |
|---|---|---|
| 1 | Coffee Bean Preparation | Coffee Bean Preparation |
| 2 | Preparing Coffee Beans | Preparing coffee beans for brewing |
| 3 | Preparing coffee beans for brewing | Preparing coffee beans |

All titles cover grinding and roasting as coffee-bean preparation. The ordinary implied purpose for brewing is acceptable, consistent with the previous review. Capitalization is immaterial.

## What this tells us

The proposed rule did not change the rejected commercial interpretation in this sample. The controls showed no material regression, but preserving already-good outputs does not demonstrate a benefit from the addition. Do not promote v23 on these results.

This does not tell us whether the model disregarded the instruction or considered the commercial interpretation established knowledge. Both remain possible. It also does not show that names cannot be interpreted from masks, or that all prompt changes would fail.

The only ambiguous title is the same “Coffee chains” wording already presented in the previous review, this time from a baseline call. It is preserved as ambiguous, not turned into an invented user decision. There are no new control uncertainties to burden the user with in another review batch.

## Integrity and limits

- All 18 calls succeeded on their first attempt, in distinct threads and empty working directories. Event logs contain only assistant-message items, no tools. Both prompt files stayed unchanged.
- The unchanged production preparer validated the source UTF-8 ranges and retained each mask's fragments together. All seven existing preparer tests passed.
- First call ran alone, then at most three ran concurrently. No retries or selected best-of outputs.
- All 386 snapshotted prior files were unchanged after generation. Subsequent current-status documentation updates, if any, are explicitly listed in verification; raw evidence and user decisions remain preserved.
- This is a small reused diagnostic, not a general accuracy estimate. Coffeechain and coffee preparation share one underlying note through different masks.
- Generation used **41,631 input tokens** (5,760 cached) and **1,117 output tokens** (924 reasoning): **42,748 input plus output**. Subcounts are included, not additional. Main-agent work and the independent audit are excluded.
- Existing authorized Codex subscription only; no API billing, purchase, rental, account switch, saved-title replacement, prompt freeze, TRUE run or hierarchy change. Tracking card: CREC-127. No Plane tool was available.

Exact v22 inputs (`./inputs-v22.json`), exact v23 inputs (`./inputs-v23.json`), every output and per-call usage (`./comparison.json`), [run plan](./run-plan.json), verification (`./verification.json`).

The [official evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices#what-are-evals) informed the scoped comparison and respect for human judgments, not the semantic verdicts.

**Publication status:** `collection:tracked-hdbv2-node-description-probe-v23` is selected as `title-studies/hdbv2-node-description-probe-v23` in the [publication catalog](../../../docs/experiments/publications.csv), with [dataset manifest](../../../docs/experiments/downloads.md#dataset-manifest). The local export preserves saved answers and recorded assessments; input AS lineage remains unverified. Nothing has been uploaded.
