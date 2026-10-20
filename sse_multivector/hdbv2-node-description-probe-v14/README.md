# Node-title prompt v14

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

The mental-state titles became concise and stayed on the subject. The user has since approved both broader titles and confirmed the remaining problem: the food title about phrases describes wording rather than its subject.

Only **and concise** was added to v13's opening. The separate brevity sentence from the earlier unrun proposal was not used. The per-instance support requirement, model, masks, and runner were unchanged.

| Group | v14 trial 1 — exact response | v14 trial 2 — exact response | Assistant assessment |
|---|---|---|---|
| S50475065d8 | Bitcoin | Bitcoin | Supported in both calls |
| S7dd75e5388 | Brisket | Brisket | Supported in both calls |
| S65c33de2ef | Timed cooking instructions | Cooking instructions | First assistant-accepted; user approved second |
| Sd5f4538ab9 | Dish-and-ingredient combinations | Recipe dish-and-ingredient phrases | User approved first; confirmed phrases problem |
| Sa256265971 | Changes in mental activity | Starting or Stopping Mental Activity | Supported in both calls |
| Sae17bb57f6 | Communication principles | Communication maxims | Supported in both calls |

## What changed

**Mental activity:** v13 produced “Mental faculties being inactive or starting up upon waking” and “Mind/brain conceptualized as a machine”. The user rejected both and clarified that the first was too wordy. V14 produced “Changes in mental activity” and “Starting or Stopping Mental Activity”. Both are shorter category names about mental activity. The user's suggested wording was not supplied to the generation calls or required as an exact answer.

**Cooking:** “Timed cooking instructions” keeps the shared duration information. “Cooking instructions” remains accurate but drops it. The user approved that broader title; it is not an unresolved failure.

**Food:** “Dish-and-ingredient combinations” remains accurate but omits the shared seasoning/topping relation. The user approved it. The user separately confirmed that “Recipe dish-and-ingredient phrases” is a problem because it names wording rather than food. The earlier assistant concern about recipe scope was not separately confirmed by the user.

**Other groups:** Bitcoin and Brisket are unchanged. Communication principles/maxims retain the already-accepted advice meaning. Instructions and maxims are not banned words.

The initial assistant assessment accepted nine outputs, questioned two, and rejected the phrases title. The user subsequently approved the two questioned titles in the focused review and confirmed the phrases problem in chat. The original calls and assistant comments remain unchanged. The baseline review record for v15 (`../hdbv2-node-description-probe-v15/baseline-user-review.json`) preserves these sources separately; it does not fabricate a TUI rejection or convert other assistant judgments into user approvals.

## Review

Reopen the completed two-card review:

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/hdbv2-node-description-probe-v14/run-review.sh
```

The cards show every exact member mask and separate assistant reasoning. The B comparison shows the matching saved v13 trial. It is historical context, not a fresh control or a second decision.

`run-review-all.sh` optionally shows all twelve calls, including the clear phrases problem and the improved mental-state titles. Its session is separate. No new decisions were prefilled.

## Evidence and controls

- Same six complete HDBv2 groups as the v13 additional test: 20 instances, 19 unique exact masks, 41 fragments, 13 source notes. Exact duplicates and instance order preserved.
- Two fresh Sol-low calls per group, twelve total, maximum three concurrent. Same pinned Codex 0.153.0 and wrapper, one successful attempt each.
- Each call had its own process, thread and empty workspace. No examples, source notes, group IDs, expected titles, review comments or prior responses appeared in the prompt text.
- Same minimal runner instruction and service context; no tools, web or response schema. Previous conversation was not resumed.
- Usage: 21,472 input tokens, including 3,200 cached input tokens; 1,081 output tokens, including 974 reasoning tokens. No new API billing, rental, model download or local inference.
- Both historical v13 outputs are preserved. No fresh v13 calls were made, so the changed results do not prove that the two added words caused every difference. Two calls per group are a limited variability check.
- Word counts in the comparison are descriptive whitespace-delimited counts. They are not a success criterion; shortening does not excuse lost meaning.
- The full baseline review and the separate user clarification are in `baseline-user-review.json`. Unreviewed baseline cards were not converted into approvals.

## Files

- `prompt.txt`, `run-plan.json`: approved candidate and pre-call plan.
- `source-packets.json`: unchanged masks, byte spans and full notes for provenance; only the masks were sent to generation.
- `trial-{1,2}/<group>/config.json` and `run/`: exact prompts, outputs, usage and execution evidence.
- `comparison.json`: both versions' exact titles with complete masks and per-title reasoning.
- `review*.json`: review inputs and separate assistant comments.
- `verification.json`: integrity checks, independent audit and review smoke test.

## Next decision

The broader-title questions are resolved by user approval. The [completed v15 test](../hdbv2-node-description-probe-v15/README.md) changes only the membership check from “it” to “its subject matter”, aiming to prevent categories of wording. Concision, per-instance support, masks, model and settings remain unchanged. V15 is a test candidate, not a freeze; prior prompts, outputs and frozen v1 remain unchanged.

The [official GPT-5.6 guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6#prompt-migration-workflow) informed the small isolated edit and same-case retest, not the semantic verdicts.

**Publication status:** `collection:tracked-hdbv2-node-description-probe-v14` is selected as `title-studies/hdbv2-node-description-probe-v14` in the [publication catalog](../../docs/experiments/publications.csv), with [exact files and hashes](../../docs/experiments/publication-files.csv). The local export preserves saved answers and recorded assessments; input AS lineage remains unverified. Nothing has been uploaded.
