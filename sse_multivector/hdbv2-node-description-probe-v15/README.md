# Node-title prompt v15

Both food titles now name food rather than phrases. One new output violates independent support: Brisket smoking, although one member mask says only brisket. The other call returned Brisket.

Main and independent reviewers accept eleven outputs and reject that one. This is a result on six reused development groups, not a general accuracy estimate.

Only the per-instance question changed from “must it belong” to “must its subject matter belong”. The concise opening, masks, model and execution settings were unchanged.

| Group | v15 trial 1 — exact response | v15 trial 2 — exact response | Assessment |
|---|---|---|---|
| S50475065d8 | Bitcoin | Bitcoin | Both supported under assistant assessment |
| S7dd75e5388 | Brisket smoking | Brisket | First adds unsupported smoking; second supported |
| S65c33de2ef | Cooking times and methods | Cooking instructions | Both supported under assistant assessment |
| Sd5f4538ab9 | Savory Dishes with Added Ingredients | Savory Dishes and Ingredients | Both supported under assistant assessment |
| Sa256265971 | Mental activity switching on or off | Changes in mental activity | Both supported under assistant assessment |
| Sae17bb57f6 | Communication Advice | Communication Principles | Both supported under assistant assessment |

## The remaining failure

S7dd75e5388, trial 1: **Brisket smoking**.

Every original mask, in its supplied order:

- V133: ⟦brisket⟧
- V134: ⟦brisket⟧ ⟦homemade barrel  smoker⟧
- V135: ⟦brisket on⟧ ⟦homemade barrel  smoker⟧
- V788: ⟦morning⟧ ⟦Brisket⟧ ⟦smoker⟧
- V786: ⟦Brisket on the smoker⟧

V133 does not require smoking: brisket can be prepared in other ways. The other four instances cannot supply that restriction for V133. This is an independent-support failure, not a demand for one exact title. Both v14 calls and v15 trial 2 returned Brisket.

The result does not establish that the wording change caused this error. We did not rerun v14 concurrently, and two calls are insufficient to estimate reliability.

## What improved and what remained sound

The food group returned Savory Dishes with Added Ingredients and Savory Dishes and Ingredients. Both concern the dishes, unlike v14's Recipe dish-and-ingredient phrases. No output in this run describes keywords or phrases.

Cooking/advice categories remain usable: Cooking times and methods, Cooking instructions, Communication Advice, and Communication Principles. Mental titles remain concise and concern mental activity rather than a machine theory. Bitcoin is unchanged.

The user approved both previously questioned broader titles in the saved v14 review. Those approvals are preserved in `baseline-user-review.json`; they are not treated as unresolved precision failures or copied into new review decisions. The user's separate chat confirmation of the phrases problem is recorded as conversation evidence, not a fabricated TUI verdict.

## Optional inspection

There are no additional uncertain judgments I need the user to resolve. This one-card view is available to inspect the failed title with every member mask and separate reasoning:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
  ./sse_multivector/hdbv2-node-description-probe-v15/run-review.sh
```

`run-review-all.sh` opens all twelve results in a separate session. B compares each candidate with the matching historical v14 response. No user decisions are prefilled.

## Controls and evidence

- Same six complete groups, 20 instances / 19 unique exact masks / 41 fragments / 13 source notes. Source packets are byte-identical to v14; duplicate masks and input order remain unchanged.
- Exact approved v15 prompt, identical to the reviewed temporary proposal. Prior versions and frozen v1 are unchanged.
- Twelve fresh Sol-low calls, two per group, at most three concurrent via the existing wrapper. Pinned Codex 0.153.0; one successful attempt each.
- Separate new process/thread/workspace for every call. No previous answers, example titles, reviewer feedback, full source notes or group IDs in the generation prompt text. Same minimal runner instruction and service context; no tools/web/schema.
- Independent audit verified prompts, source spans, settings, wrapper, execution and hashes; it did not independently reconstruct peak concurrency from timestamps.
- Usage: 21,496 input tokens, zero cached input; 1,011 output tokens including 903 reasoning tokens. Existing subscription only; no new API billing, model downloads or local inference.
- Historical v14 results, not fresh controls. This is a same-case development retest with limited repetitions, not new-data validation or causal proof.

`run-plan.json` was saved before calls. `comparison.json` contains both versions' raw outputs with full mask sets and per-title reasoning. `source-packets.json` preserves complete notes and byte spans for provenance only. Each `trial-{1,2}/<group>/run/` preserves raw output, usage, prompt hashes and execution evidence. `verification.json` records integrity and UI checks.

## Next decision

Do not freeze v15 or silently edit it again. The targeted wording error was absent in this run, but one broad/specific group still received unsupported specificity. A focused repeat comparison on groups containing broad and more specific masks would tell us more about that remaining failure than assuming this one occurrence proves the new wording is worse. That further test has not been authorized or run.

The [official GPT-5.6 guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6#prompt-migration-workflow) informed the isolated change and fixed-input retest, not the semantic judgments.
