# Unchanged v21: six additional groups

The approved same-note mask deduplication is now applied before both title generation
and review in [hdbv21-dedup-v1](../hdbv21-dedup-v1/run-plan.json). The mental-activity
and kindness/status groups were the two affected groups in this batch; each lost one
duplicate instance. The original results and user decisions below remain preserved.
Use `../hdbv21-dedup-v1/run-review.sh` to inspect the new outputs without duplicate masks.

Ten outputs were straightforwardly accepted by both reviewers. Two titles from the same kindness/status group need judgment: one adds an unreliable-indicator interpretation, while the other may narrow status to socioeconomic status. Both are in the focused review. No user decisions have been recorded by the assistant.

This tested the unchanged v21 prompt on six groups not used in its first test, twice each, with Astra low. All groups were already in the known 61-group collection; this is not a wholly unseen holdout. The 12 new calls succeeded on their first attempts. No new v20 calls were made, so saved v20 titles are historical context rather than matched comparisons.

## Exact outputs

| Group | Trial 1 | Trial 2 |
|---|---|---|
| Se7ebc25cf1 | Wine | Wine |
| S18bc272886 | Dogs | Dogs |
| Sa256265971 | States of mental activity | The mind being active or inactive |
| Sd6b13ec91f | Social status as an unreliable indicator of kindness and generosity | Kindness and generosity in relation to socioeconomic status |
| S8ea08f1aff | Music at Coffee Shops | Music at coffee shops |
| S0eafedb82e | Carrots as a food ingredient | Foods made with carrots |

Wine remained broad across drinking, refusal, food accompaniment and ingredient use. Dogs stayed simple. The mental-activity titles accommodate both off and started. The music titles express the setting; both carrot titles express a supported food-use relationship, although one names ingredient use and the other prepared foods. Different valid framings are not automatically errors, and no exact canonical title is imposed.

## The two questions

Both titles in question came from these complete mask instances:

- V630: ⟦not grant someone more priveleges based on status, or similar, but based on kindness and goodness⟧
- V461: ⟦poorest⟧ ⟦often⟧ ⟦most generous⟧
- V460: ⟦poorest⟧ ⟦often⟧ ⟦most generous⟧

**Trial 1:** The main reviewer leans too strong: the title turns a principle about granting privileges and an observation about poverty into a claim about status predicting character. That may be a plausible interpretation, but independent support is questionable. The independent reviewer rejected that added inference. This is surfaced as a judgment question, not silently treated as an agreed failure.

**Trial 2:** The main reviewer leans accepting: this names the relationship without asserting unreliability. The independent reviewer questioned whether socioeconomic imports the poverty context into V630's unspecified status. That narrower concern is also surfaced. Mere alternate word meanings are not automatically errors; the user can decide whether this is a material restriction.

The evidence supports continued consideration of v21, not a general accuracy estimate, a prompt freeze, or improved TRUE/hierarchy performance. No prompt edit or further model call was made in response to these results.

## Review

The focused view contains only the two questions, with every exact mask and a separate assistant comment. B displays the saved v20 title as historical context. No prior results or user review sessions are replaced.

Optional, all 12 new outputs:

Both views were opened with the unchanged production binary. Mask scrolling, moving between questions, baseline comparison and safe exit were checked using temporary sessions under /tmp/. Those sessions contain no decisions or user comments; the real sessions under target/ were not prefilled. No review-tool code changed.

## Evidence and isolation

- run-plan.json and all 12 configs were saved before generation. The original masks, duplicate fragments, instance order and per-instance quoted formatting were preserved.
- Exact v21 prompt SHA256: 616500bd7c28103a9686de22ff69d53323c44fa976db4c2238d0041c704f8541. The original prompt file and prior experiments remain unchanged.
- Model gpt-6-astra, effort low, Codex 0.153.0, unchanged codex_exec.py and the existing dedicated account home. The first call ran alone; the remaining scheduler allowed at most three concurrent calls.
- Every call had a distinct thread and empty temporary workspace. Rules, user configuration, tools, web, skills and extra runtime instructions were disabled. The minimal saved instruction remained Follow the user's instructions. This does not claim removal of service-side context.
- Only the prompt and numbered masks were supplied. No full notes, old titles, feedback, examples, selection reasons or vector IDs entered model input.
- All calls succeeded on attempt 1, with no retries, stderr warnings or model tool events. Prompt, config, manifest, event and output hashes and identities were checked; verification.json records the results.
- Usage: 27,378 input tokens, including 7,936 cached; 1,079 output tokens, including 956 reasoning. Total input plus output: 28,457. Cached and reasoning counts are subsets.
- Existing authorized subscription only; no new API billing, rental, purchase, credential changes or account switch. No mask corrections, clustering, TRUE calls or hierarchy changes.

comparison.json contains exact titles, historical context, masks, assessments and raw-result paths. assistant-review.json and independent-review.json preserve differing judgments. The independent reviewer received only semantic-review-input.json, without prior outputs or the main review. Source notes and byte spans remain available in ../hdbv2-node-titles-v20-astra-low/source-packets.json but were not supplied for title generation.
