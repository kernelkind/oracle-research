# Category titles v21 versus v20

The [complete 61-group v21 title set](../hdbv2-node-titles-v21-astra-low/titles.json)
is now generated and reviewed by the assistant: 14 exact-input outputs reused and
47 missing outputs generated with the unchanged prompt and Astra low. Eight exact
same-note mask duplicates were removed before generation/review. Sixty titles are
now accepted by the assistant or user, including the user's subsequent approval
of Signs of autumn’s arrival. Coffee shop chains remains unresolved: the user
commented "yea should prob say coffee shop tags/hashtags" without recording an
approve/reject decision. That comment is not treated as an approved replacement
or a new prompt rule. The [focused review](../hdbv2-node-titles-v21-astra-low/run-review.sh)
and its original inputs remain unchanged. No new TRUE run occurred.

The initial six-group experiment and its original assistant judgments follow.
The user later approved its Visual Art response; that decision is preserved in
the complete set rather than reopening the initial objection below.

The approved same-note mask deduplication is now applied by
`../prepare_category_title_inputs.py` before both title generation and review.
The unchanged v21 rerun is saved in [hdbv21-dedup-v1](../hdbv21-dedup-v1/run-plan.json).
Only Food among this batch's six groups contained an exact duplicate. This original
experiment and its review decisions remain preserved; its inputs below include that duplicate.

V21 made some category relationships more explicit on this six-group development sample. It did not eliminate unsupported narrowing: one Art result still became Visual Art. This is evidence about title generation, not an improvement demonstrated in TRUE or the hierarchy.

Both unchanged prompts ran twice on every group with Astra low: 24 fresh calls. These were existing groups selected before generation, not an unseen holdout. Every output is retained; no best-of selection or title editing occurred.

## Results

Each cell contains both fresh responses, in trial order. Earlier saved v20 titles were not substituted for these new baseline calls.

| Group | v20 trials 1 / 2 | v21 trials 1 / 2 |
|---|---|---|
| S485994b768 | Cooking Ingredients / Cooking Ingredients | Foods featuring meat or seafood / Foods containing meat or seafood |
| S5ea79ac96e | Eggs / Poultry and eggs | Eggs and egg-laying animals / Eggs and egg-laying hens |
| Se66af3a9b7 | Preparing foods from poultry products / Poultry-based food preparation | Foods prepared from poultry-derived ingredients / Preparing Foods from Poultry-Derived Ingredients |
| S24afa84c49 | Coffee Bean Preparation / Coffee Bean Preparation | Coffee Bean Preparation / Coffee Bean Preparation |
| S8a6ab7afaf | Visual Arts / Visual Arts | Art / Visual Art |
| S49eb0ac749 | Food / Food | Food and meals / Food |

## What changed

**S485994b768:** The masks combine purchases of chorizo, rib eye and T-bone with ingredient lists for beef spaghetti and shrimp risotto. V21 explicitly names foods featuring those materials. Cooking Ingredients is also a plausible category, but leaves the ingredient-versus-food relationship implicit. Neither purchasing nor cooking should be forced onto every instance. Clearer wording is not yet proof of better containment decisions.

**S5ea79ac96e:** Masks include live hens, eggs being laid, egg preservation, and eggs used in meals. Both v21 titles explicitly cover eggs and live egg-laying animals/hens. The v20 title Eggs requires an unstated connection for the isolated mask Our / four hens. Poultry and eggs is plausible but leaves the bird-versus-meat reading less explicit. Animals is broader than hens; that wording difference is not itself a demonstrated error.

**Se66af3a9b7:** The two masks concern preserved poultry eggs and stock made from carcasses. Poultry-derived ingredients makes the inclusion of eggs clearer than poultry-based alone. However, one v20 response already said poultry products and was shorter. This is not a clean win for v21, and the outputs still vary between describing prepared foods and preparation activities. Both interpretations fit these masks; no uniquely correct title is assumed.

**Controls:** Coffee preparation stayed unchanged. Food remained broad enough for preparation, a chef, dinner appreciation and sharing a meal. Art failed the independent-support requirement in both v20 trials and one v21 trial: V377 is only art, which does not independently establish visual media. V21's other trial preserved Art.

The main assistant accepts 11 of 12 v21 outputs and flags the remaining scope issue. These are assistant judgments on a selected small sample, not user approvals or an estimated general accuracy rate. Baseline ambiguities are not counted as proven errors, and prior accepted titles have not been retroactively rejected.

An independent reviewer saw masks and unique outputs without prompt-version or trial identities. It accepted Cooking Ingredients as a plausible category and found Eggs borderline. It initially accepted the common visual reading of art; after clarification of independent support and the user's prior broad-Art decision, it marked the visual titles uncertain. That original disagreement and clarification are preserved in independent-review.json rather than hidden.

## Review

The focused view contains the one flagged v21 title, every exact member mask, and the assistant's reasoning in a separate comment. B shows the fresh v20 response from the same trial. No user decisions are prefilled.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
sse_multivector/hdbv2-node-description-probe-v21/run-review.sh
```

To inspect all 12 v21 outputs, with their matching v20 baselines:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
sse_multivector/hdbv2-node-description-probe-v21/run-review-all.sh
```

These use separate new sessions under target/. Existing review decisions are untouched. Both views were opened with the production binary; mask scrolling, baseline comparison, navigation and safe exit were checked using temporary sessions under /tmp/. Those smoke sessions contain no decisions or comments. No review-tool code changed.

## Reproducibility

- run-plan.json and all 24 configs were saved before the first call. The exact group masks, ordering, duplicate fragments and quoted per-instance presentation remain unchanged. There are 35 instances and 85 fragments across six groups.
- Only the prompt differs between conditions. Model: gpt-6-astra; reasoning effort: low; Codex 0.153.0; unchanged codex_exec.py wrapper and authorized dedicated account home.
- Every call uses a fresh process, thread and empty workspace. Rules, user config, tools, web, skills and extra runtime context are disabled. The saved minimal instruction is exactly Follow the user's instructions. This does not claim removal of service-side context.
- Neither the source notes, selection reasons, prior titles, reviewer feedback nor vector IDs enter generation input. Exact raw prompts and responses are preserved under calls/.
- The first call ran alone; remaining jobs were scheduled with at most three concurrent calls. All succeeded on attempt 1 with no retries, stderr warnings or model tool events. All 24 thread IDs and workspace paths are distinct.
- Independent integrity review passed 683 checks, including hashes, exact prompt substitution, source masks and raw-output identity. verification.json records the results and limits.
- Usage: 55,420 input tokens, including 11,776 cached; 2,124 output tokens, including 1,900 reasoning. Input plus output totals 57,544. Cached and reasoning counts are subsets, not additional tokens.
- Existing subscription only. No new API billing, rental, purchase, account switch or credential edit. No prompt edits during the test, upstream corrections, TRUE calls, group changes or hierarchy construction.

comparison.json contains every title, raw-result path, usage and main-assistant assessment. assistant-review.json preserves the per-output judgments; blind-review-input.json and blind-review-key.json preserve the independent review setup. Source notes and byte spans remain in the unchanged ../hdbv2-node-titles-v20-astra-low/source-packets.json.

V21 remains an un-frozen candidate. The [three-pair follow-up](../hdbv21-pairs-v1/analysis.json)
checks title-only interpretations against the masks. Two historical relationships became
clearer; the raw-milk comparison instead demonstrated a more specific category description.
The user accepted the questioned chicken-derived title after seeing the complete notes
and masks. No unresolved title question remains in this sample; the original reviewer
concern and the user's decision are recorded separately in the follow-up.
This is evidence about description clarity and scope, not TRUE accuracy or hierarchy quality.

Existing tracking card: CREC-127. Plane tools were unavailable, so no external card update or status change is claimed.
