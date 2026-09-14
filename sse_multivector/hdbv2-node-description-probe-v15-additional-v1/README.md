# Node-title v15: six new groups

The user approved both titles raised for review: Daily greetings and Coffee chains. No unresolved title objections remain in this sample. The other nine outputs were accepted by the assistant reviewers, not individually approved by the user.

The initial main and independent assessments accepted nine outputs and marked three uncertain, representing two distinct titles. Both Coffee chains calls returned the same title for the same masks, so the focused review showed it once. The saved session contains two explicit approvals, not twelve. This is not a general accuracy estimate.

V15 was unchanged. Each group received two fresh Sol-low calls; only the groups changed from the preceding test.

| Group | Trial 1 — exact response | Trial 2 — exact response | Assessment |
|---|---|---|---|
| Sbbd7d8dae4 | Flavor-focused coffee appreciation | Coffee Flavor Appreciation | Both accepted by assistants |
| Saadde5a7ec | Positive attitudes toward gardening and allotments | Enthusiasm for Gardening and Allotments | Both accepted by assistants |
| S6088798e3d | Daily greetings | Positive daytime greetings and check-ins | User approved first; second accepted by assistants |
| S0c3094257f | Chinese cuisine | Chinese cuisine | Both accepted by assistants |
| S8077d349df | Meat | Meat | Both accepted by assistants |
| Sf5a4b23523 | Coffee chains | Coffee chains | User approved the shared title on the trial-1 card |

## Completed review

**Daily greetings — S6088798e3d, trial 1**

- V824: ⟦Good morning nostr⟧
- V861: ⟦Good morning world⟧
- V120: ⟦Good morning⟧
- V495: ⟦Glad⟧ ⟦coffee⟧ ⟦hot⟧ ⟦AM⟧
- V647: ⟦Good morning frens⟧
- V127: ⟦Good⟧ ⟦Afternoon Nostr⟧

The initial question was whether Daily greetings reasonably covers the coffee observation alongside the explicit greetings. The user approved it and commented: “ehhh i think rejecting would be pedantic”. For this group, the difference is not a reason to reject the title or require the longer second-trial wording. It remains an accepted case, not an unresolved failure.

**Coffee chains — Sf5a4b23523, both trials**

- V797: ⟦Sipping⟧ ⟦#coffeechain⟧
- V187: ⟦coffeechain⟧
- V656: ⟦#coffeechain⟧
- V297: ⟦#coffeechain⟧
- V865: ⟦#coffeechain⟧
- V126: ⟦#coffeechain⟧
- V043: ⟦coffeechain⟧

The initial concern was that Coffee chains might suggest coffee-shop businesses rather than the tag-like subject in these masks. The user approved the title without a comment. That resolves its acceptability for this group; it does not establish which interpretation the user or model had in mind.

The focused review showed this identical title once, with a comment that both calls returned it. All twelve raw responses remain available. No additional decisions have been filled in for the other trial or the all-results review.

The saved session is `target/hdbv2-node-description-v15-additional-v1-review-session.json`, SHA256 `318768f9ed4baff2db604237672a18bf0cd0f50914ccba7805c82e6d1b06b0f8` at this update. It records `S6088798e3d-trial-1` and `Sf5a4b23523-trial-1` as `approved`; the former has the comment quoted above and the latter has an empty comment. Original assistant comments and assessments are retained as pre-review evidence, not current objections.

## Review

Reopen the two completed cards, each with all its masks and original assistant reasoning:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
  ./sse_multivector/hdbv2-node-description-probe-v15-additional-v1/run-review.sh
```

`run-review-all.sh` optionally shows all twelve outputs in a separate session. B shows the other trial of the same prompt, not a prior-version baseline.

## What the accepted outputs establish

The coffee titles capture flavour appreciation across decaf preferences and roasting for personal taste. Both gardening titles preserve the positive attitude. Chinese cuisine fits two different foods. Meat is broad but supported by both meat-related masks; no narrower compulsory title was imposed. The longer greeting/check-in title can describe alternatives without claiming each mask expresses both.

This extends the evidence to six new groups without an unresolved title objection. It does not establish general reliability. The prior user acceptance of Brisket smoking remains intact. These case-specific approvals do not establish a universal rule that every adjacent meaning or ambiguous title is acceptable.

## Controls and provenance

- Six complete original HDBv2 groups: 24 distinct masks, 54 fragments, 17 notes.
- Earlier probes used 24 of 64 original groups; these six came from the 40 remaining groups.
- No selected group, exact note/span mask or complete fragment array had appeared in prior title probes. Nine source notes had appeared with different masks; eight had not. This remains the same food-centered 100-note corpus, not a new corpus.
- Selection used source masks and input variety, not earlier generated titles. Groups, order and fragments were not repaired, trimmed or deduplicated.
- Exact same v15 template, wrapper, pinned Codex 0.153.0, model gpt-5.6-sol and low effort as the previous run.
- Twelve new isolated process/thread/workspace calls, maximum three concurrent, one successful attempt each. No retries or best-of selection.
- Only the approved prompt and numbered quoted mask fragments were passed as user input. No full notes, group IDs, expected labels, examples, previous answers or reviewer comments in the generation prompt. Same minimal model instruction and service context; no tools, web or response schema.
- Usage: 21,674 input tokens; zero cached input; 1,147 output tokens including 1,032 reasoning tokens. Existing subscription only; no new API billing, rental, purchase or local model inference.

`run-plan.json` was saved before generation. `selection-audit.json` records prior exposure and the independent selection check. `source-packets.json` contains complete notes and byte spans for provenance only. `comparison.json` preserves every response, all masks and the initial main assessment. Raw calls remain under `trial-{1,2}/<group>/run/`. `verification.json` records the pre-review integrity and UI checks; the subsequent user decisions are recorded above rather than rewriting those checks.

## Next decision

The two review questions in this sample are resolved. The user subsequently approved completing v15 title coverage for the remaining 49 accepted HDBv2 groups. The [complete run](../hdbv2-node-titles-v15/README.md) assembles all 61 outputs, reusing these first trials and preserving the alternatives. The user approved its three uncertain titles, confirmed four other failures in chat, and authorized a targeted v16 test. The [v16 results](../hdbv2-node-description-probe-v16/README.md) show usable titles twice for three former failure groups; dog still fails, and one new control title is uncertain. Those are assistant assessments. Earlier approvals and raw v15 outputs remain unchanged; neither v15 nor v16 is frozen, and no hierarchy links were constructed.

The [official GPT-5.6 guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6#prompt-migration-workflow) informed keeping the prompt and execution settings fixed. It does not determine the semantic judgments.
