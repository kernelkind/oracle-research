# Coffee-shop mask experiment

Question: does selecting only “coffee shop” recover similarity between the coffee-shop music notes and the laptop-ban note?

The complete original notes, SSE checkpoint, tokenizer, worker and CPU FP32 inference are unchanged. Only mask ranges change. All original experiment data is preserved. HDBSCAN was not rerun.

N065 mentions two shops. Both occurrences were encoded separately. They were not combined, and neither result was selected after seeing its score.

## Inputs

### V035-replay

Original mask, rerun as a check.

> Weird #coffeechain today
> ⟦Rave at a coffee shop⟧ lol https://video.nostr.build/252e03e0d852e21d29e875ca7e1f381ad5559b8eee53b4a683babcb688b946ed.mp4 

### N004-shop1

New mask: only the shop phrase.

> Weird #coffeechain today
> Rave at a ⟦coffee shop⟧ lol https://video.nostr.build/252e03e0d852e21d29e875ca7e1f381ad5559b8eee53b4a683babcb688b946ed.mp4 

### V295-replay

Original mask, rerun as a check.

> Awwww yeah. Baby Got Back ⟦playing⟧ in the ⟦coffee shop⟧. 😂 #⟦music⟧str #coffeechain

### N038-shop1

New mask: only the shop phrase.

> Awwww yeah. Baby Got Back playing in the ⟦coffee shop⟧. 😂 #musicstr #coffeechain

### V566-replay

Original mask, rerun as a check.

> Coffee shop I liked now has a “⟦No laptops or tablets⟧” rule ⟦on weekends⟧. This is what happens if you let hipsters get too successful. Felt like changing their router/ap passwords so they could experience the true freedom from internet, but ⟦I⟧ simply ⟦went to another coffee shop⟧ and will remove this one from rotation. Personal growth on display.

### N065-shop1

New mask: only the shop phrase.

> ⟦Coffee shop⟧ I liked now has a “No laptops or tablets” rule on weekends. This is what happens if you let hipsters get too successful. Felt like changing their router/ap passwords so they could experience the true freedom from internet, but I simply went to another coffee shop and will remove this one from rotation. Personal growth on display.

### N065-shop2

New mask: only the shop phrase.

> Coffee shop I liked now has a “No laptops or tablets” rule on weekends. This is what happens if you let hipsters get too successful. Felt like changing their router/ap passwords so they could experience the true freedom from internet, but I simply went to another ⟦coffee shop⟧ and will remove this one from rotation. Personal growth on display.

## Results

| Notes | Saved detailed masks | Shop-only masks, N065 first occurrence | Shop-only masks, N065 second occurrence |
| --- | ---: | ---: | ---: |
| N004 rave / N038 music | 0.731218 | 0.987754 | Same pair |
| N004 rave / N065 laptop-ban note | 0.370578 | 0.965553 | 0.980879 |
| N038 music / N065 laptop-ban note | 0.264397 | 0.974720 | 0.985254 |

The saved masks in this table are V035, V295 and V566, shown above. The two N065 shop-only vectors have cosine 0.988306 with one another.

Changing only N065 also helps: its first shop-only vector has cosine 0.817142 with saved V035 and 0.741106 with saved V295. The second occurrence scores 0.826735 and 0.749591, respectively.

The three original-mask reruns match the saved vectors: cosine exceeds 0.9999999999999; the largest absolute component difference is 5.59e-8. This is negligible compared with the observed mask effects. All nine protected source, worker and result files retain their pre-run hashes.

## What this establishes

SSE can produce closely aligned coffee-shop representations from these three different complete notes when the mask isolates that shared subject. The earlier detailed masks encoded music or shop policies as well; none of N065’s 18 saved masks isolated only the shop phrase.

This does not show that the detailed masks were wrong. They represent different, more detailed subjects. Adding a shop-only representation is different from replacing those representations.

This test repeats the same words. It does not establish paraphrase generalization or automatic subject/mask extraction quality. Against the old corpus alone, shop-only vectors also match coffee and coffeechain masks strongly. The new shop vectors are closer to each other, but a usable HDBSCAN group remains untested.

Suggested next step, not executed: append these four vectors to the frozen 945-vector input and rerun unchanged HDBv2. Preserve the baseline and check both the shop group and changes elsewhere.

## Saved evidence

- experiment.json: hypotheses, exact notes/ranges, original IDs, preservation hashes.
- worker-request.json and worker-config.json: exact encoder inputs and configuration.
- execution-plan.json and execution.json: bounded local command and successful 38-second execution.
- result/worker-receipt.json and result/raw-vectors.f32le: exact token selections and seven encoded rows.
- result/analysis.json: replay checks, all six new pair cosines, mixed comparisons and nearest saved masks.
- result/new-vs-saved-cosines.csv: all four new vectors compared with all 945 saved vectors.
