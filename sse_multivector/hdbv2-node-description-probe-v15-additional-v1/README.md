# Node-title v15: six new groups

Nine outputs look acceptable; three outputs need judgment, representing two distinct titles. Main and independent assistant reviewers agree on that split. These are assistant assessments, not user approvals or a general accuracy estimate.

V15 was unchanged. Each group received two fresh Sol-low calls; only the groups changed from the preceding test.

| Group | Trial 1 — exact response | Trial 2 — exact response | Assessment |
|---|---|---|---|
| Sbbd7d8dae4 | Flavor-focused coffee appreciation | Coffee Flavor Appreciation | Both accepted by assistants |
| Saadde5a7ec | Positive attitudes toward gardening and allotments | Enthusiasm for Gardening and Allotments | Both accepted by assistants |
| S6088798e3d | Daily greetings | Positive daytime greetings and check-ins | First uncertain; second accepted by assistants |
| S0c3094257f | Chinese cuisine | Chinese cuisine | Both accepted by assistants |
| S8077d349df | Meat | Meat | Both accepted by assistants |
| Sf5a4b23523 | Coffee chains | Coffee chains | Both uncertain; same title |

## Two questions for review

**Daily greetings — S6088798e3d, trial 1**

- V824: ⟦Good morning nostr⟧
- V861: ⟦Good morning world⟧
- V120: ⟦Good morning⟧
- V495: ⟦Glad⟧ ⟦coffee⟧ ⟦hot⟧ ⟦AM⟧
- V647: ⟦Good morning frens⟧
- V127: ⟦Good⟧ ⟦Afternoon Nostr⟧

The coffee observation is not an explicit greeting. It could still fit the ordinary social context of daily greetings, so we have not declared it a definite failure. Trial 2, Positive daytime greetings and check-ins, more clearly includes that status update. The question is whether the shorter title accurately describes this whole group, not whether every mask contains the word greeting.

**Coffee chains — Sf5a4b23523, both trials**

- V797: ⟦Sipping⟧ ⟦#coffeechain⟧
- V187: ⟦coffeechain⟧
- V656: ⟦#coffeechain⟧
- V297: ⟦#coffeechain⟧
- V865: ⟦#coffeechain⟧
- V126: ⟦#coffeechain⟧
- V043: ⟦coffeechain⟧

Coffee chains could suggest coffee-shop businesses. The masks give a tag-like expression and one sipping fragment, not evidence of multiple outlets. It may instead be a rendering of a social tag. This is an interpretation question, and the limited mask context means any problem cannot yet be assigned to the prompt alone.

The focused review shows this identical title once, with a comment that both calls returned it. All twelve raw responses remain available. No review decisions are prefilled.

## Review

Two cards, each with all its masks and separate assistant reasoning:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
  ./sse_multivector/hdbv2-node-description-probe-v15-additional-v1/run-review.sh
```

`run-review-all.sh` optionally shows all twelve outputs in a separate session. B shows the other trial of the same prompt, not a prior-version baseline.

## What the accepted outputs establish

The coffee titles capture flavour appreciation across decaf preferences and roasting for personal taste. Both gardening titles preserve the positive attitude. Chinese cuisine fits two different foods. Meat is broad but supported by both meat-related masks; no narrower compulsory title was imposed. The longer greeting/check-in title can describe alternatives without claiming each mask expresses both.

This extends the evidence to six new groups, but does not establish general reliability or justify freezing. The prior user acceptance of Brisket smoking remains intact. No exact reference titles, word blacklists or a newly invented universal rule about broad masks were used.

## Controls and provenance

- Six complete original HDBv2 groups: 24 distinct masks, 54 fragments, 17 notes.
- Earlier probes used 24 of 64 original groups; these six came from the 40 remaining groups.
- No selected group, exact note/span mask or complete fragment array had appeared in prior title probes. Nine source notes had appeared with different masks; eight had not. This remains the same food-centered 100-note corpus, not a new corpus.
- Selection used source masks and input variety, not earlier generated titles. Groups, order and fragments were not repaired, trimmed or deduplicated.
- Exact same v15 template, wrapper, pinned Codex 0.153.0, model gpt-5.6-sol and low effort as the previous run.
- Twelve new isolated process/thread/workspace calls, maximum three concurrent, one successful attempt each. No retries or best-of selection.
- Only the approved prompt and numbered quoted mask fragments were passed as user input. No full notes, group IDs, expected labels, examples, previous answers or reviewer comments in the generation prompt. Same minimal model instruction and service context; no tools, web or response schema.
- Usage: 21,674 input tokens; zero cached input; 1,147 output tokens including 1,032 reasoning tokens. Existing subscription only; no new API billing, rental, purchase or local model inference.

`run-plan.json` was saved before generation. `selection-audit.json` records prior exposure and the independent selection check. `source-packets.json` contains complete notes and byte spans for provenance only. `comparison.json` preserves every response, all masks and the main assessment. Raw calls remain under `trial-{1,2}/<group>/run/`. Integrity checks and UI checks are recorded in `verification.json`.

## Next decision

Get the user's judgment on the two uncertain titles before treating either as a prompt failure. Keep v15 unchanged and unfrozen; no further test or prompt edit has been authorized.

The [official GPT-5.6 guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6#prompt-migration-workflow) informed keeping the prompt and execution settings fixed. It does not determine the semantic judgments.
