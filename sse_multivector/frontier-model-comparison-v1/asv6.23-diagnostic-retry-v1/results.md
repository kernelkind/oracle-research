# GLM retries for the ASv6.23 diagnostic

Both missing outputs are now available. H06 (satellite texting) and H21 (garden plants) each succeeded on the first retry, with the original prompts, schemas, GLM model and low reasoning unchanged.

No clear semantic issue was found in either new output. All other models' outputs, the other ten GLM outputs, and the original failed receipts remain unchanged.

The existing `../asv6.23-diagnostic-v2/run-review.sh` launcher now opens this directory's completed `review.json`. Quit and reopen any already-running viewer to load the new data. The old review packet is preserved separately.

The two requests cost $0.000156075. The complete diagnostic now has 36 generated outputs from 38 attempts, plus the twelve reused historical Astra outputs. Total diagnostic charge including these retries: $0.012074026.

`glm/results.jsonl` preserves the new responses and exact requests. `plan.json` identifies both original failed receipts; `billing.json` records provider charges. No Astra calls or mask generation occurred.

## Publication files

Selected initial and retry evidence retains the saved answers, failed attempts, exact inputs, settings and recorded reviews. Full review posts and shortened text actually supplied to the model remain distinct.

`historical-studies/frontier-asv6.23-diagnostic-v2` appears in the
[catalog](../../../docs/experiments/publications.csv) and [dataset manifest](../../../docs/experiments/downloads.md#dataset-manifest).
These files are prepared locally for Hugging Face Datasets; downloads are not
available yet. Recorded pre-ASv6.100 derivatives remain deprecated historical evidence.
