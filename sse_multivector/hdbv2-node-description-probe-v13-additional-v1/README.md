# v13: six new HDBv2 groups

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

The prompt was unchanged. Each complete group received two fresh Sol-low calls.

The assistant initially accepted three groups and surfaced five distinct uncertain titles from the other three. The user has now completed that focused review: cooking and both communication titles were approved; both mental-state titles were rejected. These are judgments on a selected sample, not an accuracy estimate.

| Group | Trial 1 — raw response | Trial 2 — raw response | Assessment |
|---|---|---|---|
| S50475065d8 | Bitcoin | Bitcoin | Supported in both calls |
| S7dd75e5388 | Brisket | Brisket | Supported in both calls |
| S65c33de2ef | Cooking instructions with specified times | Cooking instructions with specified times | User approved trial 1; trial 2 is identical |
| Sd5f4538ab9 | Savory dishes with seasonings or toppings | Savory dishes with seasonings or garnishes | Supported in both calls |
| Sa256265971 | Mental faculties being inactive or starting up upon waking | **Mind/brain conceptualized as a machine** | User rejected both |
| Sae17bb57f6 | Communication maxims | Maxims about responsible communication | User approved both |

## What worked

- Bitcoin remains a subject title rather than a keywords/mentions label.
- Brisket remains broad enough for the bare brisket mask. The other instances do not force an unsupported smoker qualification onto it.
- Both savory-dish titles retain the food context and allow different seasonings or toppings without transferring particular ingredients.

## Completed user review

The user clarified the first mental-title rejection: “not concise enough. could've been mental state change or something along those lines”. This is an example of the desired brevity, not an exact required title or a confirmed objection to the waking context. The second rejection has no separately recorded user rationale.

The approvals show that instructions, maxims, and responsible are acceptable in these particular titles; no blanket ban on those words is warranted. The three groups not surfaced remain assistant-assessed, not user-approved. The original session and the separate chat clarification are preserved in the v14 baseline review record (`../hdbv2-node-description-probe-v14/baseline-user-review.json`).

## Assistant concerns before that review

- Cooking: both masks contain cooking durations. “Instructions” could be a legitimate category of procedural cooking advice, or an unnecessary description of the passage's form. A form word alone does not prove failure.
- Mental activity, trial 1: “upon waking” is supported for the starting-up instance, but not for the mind-off instances. The title can be read with that correct attachment; it should not be automatically rejected using the alternative reading.
- Mental activity, trial 2: “off” and “started” allow a machine metaphor. The concern is that the title makes that expressive device the subject, although the masks describe mental states. This is the strongest concern; the assistant leans reject.
- Communication: both masks express general advice about communication. “Maxims” can name that advice, but could also classify its form rather than its subject. “Responsible” is a plausible interpretation of the prescriptions, not a clearly disproven restriction.

Before the user review, the independent audit reached the same six supported / six uncertain-call split. That earlier uncertainty is not the current user verdict. The original assistant comments remain unchanged so the review's provenance is preserved.

## Review

Reopen the completed five-card focused review:

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/hdbv2-node-description-probe-v13-additional-v1/run-review.sh
```

The identical cooking title is shown once, not twice. Both mental and both communication variants remain separate cards. Every card shows all original member masks and separate assistant reasoning. The B comparison shows the other v13 trial, not an earlier prompt baseline. Only your choices record decisions.

The optional `run-review-all.sh` exposes all twelve calls. Its decisions are stored separately. Neither session has been prefilled.

## Scope and execution

- Original HDBv2 membership and exact UTF-8 source spans preserved: 20 mask instances, 19 unique exact masks, 41 fragments, 13 notes.
- All six groups and their exact masks were absent from 102 prior title calls. Six source notes had appeared before; seven had not. This is a new group sample from the same food-centered 100-note corpus, not a wholly unseen corpus.
- Selection was recorded before generation, based on complete masks and structural variety, without expected titles.
- V105 and V106 have identical masks. Both remain because this test changes neither group membership nor deduplication.
- Exact registered v13 prompt; Sol `gpt-5.6-sol`, low effort; pinned Codex 0.153.0; 12 calls, at most three concurrent, one attempt each.
- Fresh process, thread and empty workspace per call. No prior examples, full notes, group IDs, expected titles or audit rationale in prompt text. No tools, web, response schema, repository instructions or resumed conversations.
- The runner supplies the same minimal “Follow the user's instructions.” instruction as before. This does not claim absence of service-level system context.
- Usage: 21,448 input tokens; 1,379 output tokens, including 1,247 reasoning tokens. The input count includes 1,536 cached tokens; this is not a reused conversation.
- No downloads, local model loads, API billing, or new paid resources.

## Files

- `run-plan.json`: selection, question, fixed settings and assessment standard, recorded before calls.
- `prompt.txt`: unchanged v13 template.
- `source-packets.json`: every full source note and exact mask span; full notes were not sent to title generation.
- `trial-{1,2}/<group>/config.json` and `run/`: exact inputs, raw outputs, execution records and hashes.
- `analysis.json`: every raw title, complete masks and per-title assistant reasoning.
- `review*.json`: review inputs and separate assistant comments, not user decisions.
- `verification.json`: execution/provenance checks and independent audit.

## Next test

The user approved restoring “most precise and concise” in the opening, without adding a separate brevity instruction. The [v14 retest](../hdbv2-node-description-probe-v14/README.md) changes only that wording and has been completed on these same six groups. Neither candidate is frozen; frozen v1 remains unchanged.

**Publication status:** `collection:tracked-hdbv2-node-description-probe-v13-additional-v1` is selected as `title-studies/hdbv2-node-description-probe-v13-additional-v1` in the [publication catalog](../../docs/experiments/publications.csv), with [dataset manifest](../../docs/experiments/downloads.md#dataset-manifest). The local export preserves saved answers and recorded assessments; input AS lineage remains unverified. Nothing has been uploaded.
