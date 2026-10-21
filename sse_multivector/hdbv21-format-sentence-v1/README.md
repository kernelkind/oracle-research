# Removing v21’s wording-or-format sentence

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

Removing the sentence did not fix Coffeechain. Both versions returned **Coffee shop chains in all three trials**. The food and coffee-preparation controls stayed on their subjects.

The existing v21 prompt and 61 saved titles remain unchanged. This is a diagnostic, not a new frozen prompt.

## What changed

The candidate removes only this sentence and its paragraph break:

> Categorize what the text communicates, not its wording or format, unless those are themselves the subject being discussed.

Same exact masks, instance order, model (Astra low), wrapper and subscription account. Three fresh calls for each version on each group: 18 calls. Both versions were rerun; historical outputs are not baseline trials.

## Every result

The headings identify the groups for this report; they were not supplied to the title model. Each line below is one mask. Its quoted parts stay together as one numbered instance.

### Sf5a4b23523 — Coffeechain

- V797: ⟦Sipping⟧ ⟦#coffeechain⟧
- V187: ⟦coffeechain⟧
- V656: ⟦#coffeechain⟧
- V297: ⟦#coffeechain⟧
- V865: ⟦#coffeechain⟧
- V126: ⟦#coffeechain⟧
- V043: ⟦coffeechain⟧

| Trial | v21 unchanged | Sentence removed |
|---|---|---|
| 1 | Coffee shop chains | Coffee Shop Chains |
| 2 | Coffee Shop Chains | Coffee shop chains |
| 3 | Coffee shop chains | Coffee Shop Chains |

All six responses repeat the previously user-identified commercial-chain interpretation. The masks identify coffeechain/#coffeechain and sipping; none establishes shops or a commercial chain. Recognizing the hashtag category does not require a Nostr-specific association. This retains the existing semantic judgment; it does not prescribe an exact replacement title.

### Sd5f4538ab9 — Food control

- V901: ⟦omlette⟧ ⟦topped⟧ ⟦parm⟧
- V539: ⟦Mushroom Risotto with Shrimp⟧ ⟦Pepper⟧
- V881: ⟦Spaghetti Bolognaise⟧ ⟦Salt and pepper to taste⟧
- V902: ⟦omlette⟧ ⟦topped⟧ ⟦jalepenos⟧ ⟦parm⟧
- V532: ⟦Mushroom Risotto with Shrimp⟧ ⟦Parsley⟧

| Trial | v21 unchanged | Sentence removed |
|---|---|---|
| 1 | Dishes and Their Toppings or Seasonings | Savory dishes with toppings or seasonings |
| 2 | Toppings and seasonings for savory dishes | Seasonings and toppings for savory dishes |
| 3 | Savory dishes with seasonings or toppings | Savory Dishes with Toppings or Seasonings |

All six titles retain the shared food meaning and the topping/seasoning relationship. Some name the dishes, others their additions; both are reasonable for these masks. No output names phrases or keywords. Different capitalization or conjunction order is not a failure.

### S24afa84c49 — Coffee-preparation control

- V410: ⟦grind coffee beans⟧
- V411: ⟦Rise⟧ ⟦grind coffee beans⟧
- V793: ⟦coffee⟧ ⟦Roasting your own beans⟧

| Trial | v21 unchanged | Sentence removed |
|---|---|---|
| 1 | Preparing Coffee Beans | Coffee Bean Preparation |
| 2 | Preparing Coffee Beans | Coffee Bean Preparation |
| 3 | Coffee Bean Preparation | Preparing Coffee Beans for Brewing |

All six titles cover coffee-bean preparation, including grinding and roasting. For Brewing states an ordinary implied purpose, not an observed material regression; it is not rejected merely because that word is absent. None imposes grinding or roasting on every instance.

## What this establishes

Removing that sentence alone did not produce the improvement we hypothesized. This does not prove the sentence has no influence, and it does not identify the actual cause of the commercial-chain interpretation. No control returned a title about phrases or keywords, but three trials cannot establish that the sentence is generally unnecessary.

An independent, fresh-context reviewer accepted the commercial-chain title as a plausible interpretation. I disagree for the already user-established reason: the masks do not establish shops or businesses. That disagreement is preserved in `./independent-review.json`; the other review agrees on the controls. No semantic judgment here is recorded as a new user decision.

Recommendation: leave v21 unchanged. The Coffeechain issue remains unresolved; this deletion is not a demonstrated fix.

## Integrity and limits

- All 18 calls succeeded on attempt 1, with distinct threads and empty workspaces. No retries, response selection, tools, web, source-platform context or prior conversation was used in generation. The minimal runner instruction and unavoidable service context remain the same.
- The approved exact-mask preparation path produced both inputs. No selected group needed same-note deduplication. Repeated identical strings from different notes remain intact.
- Each prompt, raw response, manifest and usage record is saved in calls/. Configs and the run plan were prepared before the first call. Conditions were interleaved, with the first call alone and at most three concurrent afterward.
- All earlier generation artifacts are unchanged. Of 257 snapshotted files, 256 remain byte-identical; only the prior analysis file’s current-status fields were updated to link this diagnostic. Its raw results and user decisions are unchanged. Seven existing input-preparation tests passed. No production code changed.
- These are selected development groups, not an unseen holdout. The food control’s original wording failure came from an older prompt/model. Coffeechain and coffee preparation share one source note, through different masks.
- Generation usage: 41,046 input tokens (12,288 cached), 1,385 output tokens (1,189 reasoning); **42,431 input plus output tokens**. Cached and reasoning counts are subsets, not extra tokens. Main-agent work and independent reviews are not included.
- Existing authorized subscription only; no API billing, purchases, rental or account switch.

The [official evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices#what-are-evals) informed scoped comparisons, saved evidence and calibration to human judgment—not the semantic verdicts.

Exact prepared v21 inputs (`./inputs-v21.json`), exact candidate inputs (`./inputs-without-sentence.json`), all results and per-call usage (`./comparison.json`), integrity checks (`./verification.json`).

**Publication status:** `collection:tracked-hdbv21-format-sentence-v1` is selected as `title-studies/hdbv21-format-sentence-v1` in the [publication catalog](../../docs/experiments/publications.csv), with [dataset manifest](../../docs/experiments/downloads.md#dataset-manifest). The local export preserves saved answers and recorded assessments; input AS lineage remains unverified. Nothing has been uploaded.
