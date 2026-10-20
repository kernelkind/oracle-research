# Explaining the Coffeechain masks

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

All three fresh Astra-low responses recognize hashtag notation but still interpret **coffeechain as a commercial coffee-shop chain**. The mistaken interpretation persists when the task asks for an explanation rather than a category title.

## Exact input

```text
Briefly explain what these instances refer to.

Interpret the quoted text within each instance together.

Instances:

1. “Sipping”; “#coffeechain”
2. “coffeechain”
3. “#coffeechain”
4. “#coffeechain”
5. “#coffeechain”
6. “#coffeechain”
7. “coffeechain”
```

No original notes, source platform, previous titles, reviewer feedback or suggested meaning were supplied. The masks, their order and their grouping are unchanged.

## Exact responses

### Trial 1

> 1. “Sipping” with “#coffeechain” likely refers to drinking coffee from a coffee-shop chain.
> 2–7. “coffeechain” or “#coffeechain” likely refers to a coffee-shop chain; the hashtag versions label the topic on social media.
>
> No specific brand can be identified from these words alone.

### Trial 2

> 1. **“Sipping”; “#coffeechain”** — Likely sipping coffee from a coffee-shop chain; the hashtag labels that context.
> 2. **“coffeechain”** — A coffee-shop business with multiple locations.
> 3.–6. **“#coffeechain”** — A hashtag referring to a coffee-shop chain or chains generally.
> 7. **“coffeechain”** — Same meaning as instance 2.
>
> None of the text identifies a specific brand.

### Trial 3

> 1. “Sipping” with “#coffeechain” likely refers to drinking coffee from a coffee-shop chain.
> 2. “coffeechain” refers to a business operating multiple coffee shops.
> 3–6. “#coffeechain” is a hashtag referring to a coffee-shop chain or discussing such chains.
> 7. “coffeechain” has the same likely meaning as instance 2.
>
> The text alone doesn’t identify a specific brand.

## What we learned

The model explicitly calls the marked strings hashtags in every trial. Trial 1 also says they label a topic on social media. It nevertheless interprets the name as a chain of coffee shops in every trial. These two observations must be kept separate: recognizing a hashtag does not ensure the intended reading of its name.

This makes the earlier theory—that the error occurs only while choosing a short title—insufficient. It does not reveal the internal reasoning behind previous outputs, identify a particular causal instruction, or show that another prompt could not obtain a better interpretation. All three preserve uncertainty about the exact brand; none supplies a Nostr-specific association.

The intended next discussion concerns the name’s interpretation, not teaching the model what hashtag notation means. No prompt revision or extra pipeline stage is implemented. V21 and all saved titles remain unchanged.

## Verification

- Three identical configurations; Astra low, same pinned CLI and wrapper, existing main Codex subscription.
- First call alone; the other two concurrently. Each used a fresh process, thread and empty workspace. No retries, tools, web, prior conversation, examples or output selection.
- Exact source-byte masks and rendered instance block match the previous diagnostic. An independent read-only audit checked provenance, prompt neutrality, execution and limits.
- All 107 snapshotted prior files, including the user’s review session, remain unchanged. Seven existing input-preparation tests passed. No production code changed.
- Generation usage: 6,510 input tokens (5,760 cached), 311 output tokens (46 reasoning); **6,821 input plus output tokens**. Cached and reasoning counts are subsets. Main-agent work and the independent audit are not included.
- No new API billing, rental, account switch or purchase. CREC-127 remains the tracking card; Plane tools were unavailable.

[Run plan](./run-plan.json), all raw responses and usage (`./responses.json`), analysis (`./analysis.json`), integrity checks (`./verification.json`), [previous title diagnostic](../hdbv21-format-sentence-v1/README.md).

The [official evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices#what-are-evals) informed the scoped test and preserved evidence, not its semantic conclusions.

**Publication status:** `collection:tracked-hdbv21-interpretation-v1` remains in the [conversion review list](../../docs/experiments/publication-gaps.csv); a complete compact-data conversion has not been established.
