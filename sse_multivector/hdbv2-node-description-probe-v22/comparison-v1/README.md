# V21 versus v22: explicit social-media context

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

Adding the known source setting did not produce a clear Coffeechain correction in this small test. V22 returned **Coffee shop chains twice** and **Coffee chains once**. The last title is ambiguous, not an established fix. Both controls retained their subjects.

V22 contains only one change from v21: the opening sentence “Each instance contains text from a social-media post.” All other prompt wording and all masks are unchanged. Both versions ran three times on every group: **18 fresh Astra-low calls**. Earlier responses were not substituted for new baseline calls.

## Every result

Report headings below were not supplied as hints to generation. Each line is one complete mask; its parts stay together as one numbered instance.

### Sf5a4b23523 — Coffeechain

- V797: ⟦Sipping⟧ ⟦#coffeechain⟧
- V187: ⟦coffeechain⟧
- V656: ⟦#coffeechain⟧
- V297: ⟦#coffeechain⟧
- V865: ⟦#coffeechain⟧
- V126: ⟦#coffeechain⟧
- V043: ⟦coffeechain⟧

| Trial | V21 | V22 |
|---|---|---|
| 1 | Coffee shop chains | Coffee shop chains |
| 2 | Coffee shop chains | Coffee shop chains |
| 3 | Coffeehouse chains | Coffee chains |

The masks are coffeechain/#coffeechain, with Sipping in one. A shop or commercial chain is not established. Titles explicitly naming shop/coffeehouse chains repeat the prior rejected interpretation. The v22 trial-3 response Coffee chains lacks an explicit shop qualifier: its meaning is ambiguous and should not be counted as either a demonstrated correction or the identical explicit error.

### Sd5f4538ab9 — Food control

- V901: ⟦omlette⟧ ⟦topped⟧ ⟦parm⟧
- V539: ⟦Mushroom Risotto with Shrimp⟧ ⟦Pepper⟧
- V881: ⟦Spaghetti Bolognaise⟧ ⟦Salt and pepper to taste⟧
- V902: ⟦omlette⟧ ⟦topped⟧ ⟦jalepenos⟧ ⟦parm⟧
- V532: ⟦Mushroom Risotto with Shrimp⟧ ⟦Parsley⟧

| Trial | V21 | V22 |
|---|---|---|
| 1 | Savory dishes with seasonings or toppings | Food dishes with toppings or seasonings |
| 2 | Savory dishes and their toppings or seasonings | Savory dishes with seasonings or toppings |
| 3 | Savory dishes with toppings or seasonings | Savory dishes with seasonings or toppings |

Each mask combines a named food dish with toppings, ingredients used as additions, or seasonings. All six outputs name this shared food meaning. Word order, capitalization and food versus savory do not create a material difference. No phrases/keywords label reappeared.

### S24afa84c49 — Coffee-preparation control

- V410: ⟦grind coffee beans⟧
- V411: ⟦Rise⟧ ⟦grind coffee beans⟧
- V793: ⟦coffee⟧ ⟦Roasting your own beans⟧

| Trial | V21 | V22 |
|---|---|---|
| 1 | Coffee Bean Preparation | Preparing Coffee Beans |
| 2 | Coffee Bean Preparation | Preparing coffee beans |
| 3 | Preparing Coffee Beans for Brewing | Preparing coffee beans |

The masks concern grinding or roasting coffee beans. All six outputs cover bean preparation. The baseline phrase for brewing states an ordinary implied purpose; it is not rejected just because that word is absent. No output requires every instance to include both grinding and roasting.

## Conclusion

The source-context addition alone was insufficient to demonstrate the intended correction. That does not make supplying the known source setting unnecessary: this tests a remedy, not whether the model should have been given the true context. The approved factual addition is preserved.

The model could have intended different readings of Coffee chains. We cannot recover its intended sense from the two-word title. That output is left for user judgment; no decision is prefilled. There is no demonstrated control regression, and no new prompt is invented from these outcomes.

## Focused review

The existing review tool contains only the ambiguous trial-3 title, all seven exact masks and a separate assistant comment. B shows the fresh v21 response from the same trial. The session is new and separate from previous reviews.

## Integrity and limits

- Both prompts remained fixed. All 18 calls succeeded on attempt 1 with distinct threads and empty workspaces. No retries, output selection, tools, web, source notes, prior titles or reviewer hints entered generation.
- Same pinned CLI, wrapper, model/effort and authorized main subscription. The first call ran alone; subsequent calls ran with a maximum concurrency of 3, interleaving versions and rotating group order.
- The existing preparer validates original UTF-8 spans and preserves mask order. No selected group needed exact same-note deduplication; repeated strings from different notes remain.
- Independent read-only integrity audit passed. All 131 snapshotted files, including both prompts and the user’s earlier review session, remain unchanged. Seven existing input-preparation tests passed. No production code changed.
- This is a small reused diagnostic, not general accuracy. Coffeechain and preparation include different masks from one shared source note. All assistant judgments remain separate from user decisions.
- Generation usage: **41,334 input tokens** (11,904 cached), **1,183 output tokens** (990 reasoning), **42,517 input plus output tokens**. Cached and reasoning counts are subsets; main-agent work and the independent audit are excluded.
- No API billing, purchases, rentals or account switch. No saved title replacement, prompt freeze or TRUE run.

Exact baseline inputs (`./inputs-v21.json`), exact candidate inputs (`./inputs-v22.json`), all outputs and usage (`./comparison.json`), [run plan](./run-plan.json), verification (`./verification.json`).

The [official evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices#what-are-evals) informs scoped comparisons and calibration to human judgment, not the semantic verdicts.

**Publication status:** `collection:tracked-hdbv2-node-description-probe-v22` is selected as `title-studies/hdbv2-node-description-probe-v22` in the [publication catalog](../../../docs/experiments/publications.csv), with [dataset manifest](../../../docs/experiments/downloads.md#dataset-manifest). The local export preserves saved answers and recorded assessments; input AS lineage remains unverified. Nothing has been uploaded.
