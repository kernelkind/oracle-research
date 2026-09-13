# Node-title prompt v14

The mental-state titles became concise and stayed on the subject. But shorter wording also lost useful detail elsewhere; this was not an unqualified improvement.

Only **and concise** was added to v13's opening. The separate brevity sentence from the earlier unrun proposal was not used. The per-instance support requirement, model, masks, and runner were unchanged.

| Group | v14 trial 1 — exact response | v14 trial 2 — exact response | Assistant assessment |
|---|---|---|---|
| S50475065d8 | Bitcoin | Bitcoin | Supported in both calls |
| S7dd75e5388 | Brisket | Brisket | Supported in both calls |
| S65c33de2ef | Timed cooking instructions | Cooking instructions | First supported; second loses the timing detail |
| Sd5f4538ab9 | Dish-and-ingredient combinations | Recipe dish-and-ingredient phrases | First loses seasoning/topping detail; second names text phrases |
| Sa256265971 | Changes in mental activity | Starting or Stopping Mental Activity | Supported in both calls |
| Sae17bb57f6 | Communication principles | Communication maxims | Supported in both calls |

## What changed

**Mental activity:** v13 produced “Mental faculties being inactive or starting up upon waking” and “Mind/brain conceptualized as a machine”. The user rejected both and clarified that the first was too wordy. V14 produced “Changes in mental activity” and “Starting or Stopping Mental Activity”. Both are shorter category names about mental activity. The user's suggested wording was not supplied to the generation calls or required as an exact answer.

**Cooking:** “Timed cooking instructions” keeps the shared duration information. “Cooking instructions” remains accurate but drops it. That is a precision question, not a false-membership finding.

**Food:** “Dish-and-ingredient combinations” remains accurate but loses the shared seasoning/topping relation. “Recipe dish-and-ingredient phrases” is the clearest problem: it names a category of wording instead of the food subject, and recipe is not independently required by every mask. This is not fixed by brevity.

**Other groups:** Bitcoin and Brisket are unchanged. Communication principles/maxims retain the already-accepted advice meaning. Instructions and maxims are not banned words.

The assistant accepts nine outputs, questions the precision of two, and rejects the phrases title. These are judgments on this selected development sample, not a general accuracy estimate or user decisions.

## Review

Only the two precision questions are surfaced:

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

Resolve whether the two broader but accurate titles lost too much useful meaning. Keep the phrases result recorded as an assistant-identified problem. Do not freeze v14 or silently replace it with another prompt. Frozen v1, prior prompts and raw outputs remain unchanged.

The [official GPT-5.6 guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6#prompt-migration-workflow) informed the small isolated edit and same-case retest, not the semantic verdicts.
