# Node-title prompt v15

Both food titles now name food rather than phrases. The user accepted Brisket smoking, the only title flagged by the assistant reviewers. No unresolved title objections remain in this sample.

The initial main and independent assessments accepted eleven outputs and rejected that one. The user's subsequent approval resolves the flagged item; it does not turn the other eleven assistant assessments into user approvals. This is a result on six reused development groups, not a general accuracy estimate.

Only the per-instance question changed from “must it belong” to “must its subject matter belong”. The concise opening, masks, model and execution settings were unchanged.

| Group | v15 trial 1 — exact response | v15 trial 2 — exact response | Assessment |
|---|---|---|---|
| S50475065d8 | Bitcoin | Bitcoin | Both supported under assistant assessment |
| S7dd75e5388 | Brisket smoking | Brisket | User approved first; second supported under assistant assessment |
| S65c33de2ef | Cooking times and methods | Cooking instructions | Both supported under assistant assessment |
| Sd5f4538ab9 | Savory Dishes with Added Ingredients | Savory Dishes and Ingredients | Both supported under assistant assessment |
| Sa256265971 | Mental activity switching on or off | Changes in mental activity | Both supported under assistant assessment |
| Sae17bb57f6 | Communication Advice | Communication Principles | Both supported under assistant assessment |

## The reviewed brisket title

S7dd75e5388, trial 1: **Brisket smoking**.

Every original mask, in its supplied order:

- V133: ⟦brisket⟧
- V134: ⟦brisket⟧ ⟦homemade barrel  smoker⟧
- V135: ⟦brisket on⟧ ⟦homemade barrel  smoker⟧
- V788: ⟦morning⟧ ⟦Brisket⟧ ⟦smoker⟧
- V786: ⟦Brisket on the smoker⟧

The initial assistant objection was that V133 alone does not establish smoking, whereas the other four masks include a smoker. Both v14 calls and v15 trial 2 returned Brisket. The user subsequently approved Brisket smoking in the focused review and said in chat, “i think it's fine”. It is accepted for this group, not retained as an unresolved failure.

The saved review at `target/hdbv2-node-description-v15-review-session.json` records `S7dd75e5388-trial-1` as `approved`, with an empty comment. Its SHA256 at this update is `93f9fdcff00021fcbbcf61d33790d7058e9a2a760d79ce3b1caccb3efdd69d6b`. The raw outputs and original assistant assessments remain unchanged. This case-specific approval does not establish a new general rule for broad masks or authorize a prompt change.

We did not rerun v14 concurrently, and two calls are insufficient to estimate reliability or attribute changes to the prompt wording.

## What improved and what remained sound

The food group returned Savory Dishes with Added Ingredients and Savory Dishes and Ingredients. Both concern the dishes, unlike v14's Recipe dish-and-ingredient phrases. No output in this run describes keywords or phrases.

Cooking/advice categories remain usable: Cooking times and methods, Cooking instructions, Communication Advice, and Communication Principles. Mental titles remain concise and concern mental activity rather than a machine theory. Bitcoin is unchanged.

The user approved both previously questioned broader titles in the saved v14 review. Those approvals are preserved in `baseline-user-review.json`; they are not treated as unresolved precision failures or copied into new review decisions. The user's separate chat confirmation of the phrases problem is recorded as conversation evidence, not a fabricated TUI verdict.

## Optional inspection

There are no outstanding judgments requiring user review. This one-card view reopens the accepted title with every member mask and the original assistant objection:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
  ./sse_multivector/hdbv2-node-description-probe-v15/run-review.sh
```

`run-review-all.sh` opens all twelve results in a separate session. B compares each candidate with the matching historical v14 response. No user decisions were prefilled; the focused session now contains the user's approval.

## Controls and evidence

- Same six complete groups, 20 instances / 19 unique exact masks / 41 fragments / 13 source notes. Source packets are byte-identical to v14; duplicate masks and input order remain unchanged.
- Exact approved v15 prompt, identical to the reviewed temporary proposal. Prior versions and frozen v1 are unchanged.
- Twelve fresh Sol-low calls, two per group, at most three concurrent via the existing wrapper. Pinned Codex 0.153.0; one successful attempt each.
- Separate new process/thread/workspace for every call. No previous answers, example titles, reviewer feedback, full source notes or group IDs in the generation prompt text. Same minimal runner instruction and service context; no tools/web/schema.
- Independent audit verified prompts, source spans, settings, wrapper, execution and hashes; it did not independently reconstruct peak concurrency from timestamps.
- Usage: 21,496 input tokens, zero cached input; 1,011 output tokens including 903 reasoning tokens. Existing subscription only; no new API billing, model downloads or local inference.
- Historical v14 results, not fresh controls. This is a same-case development retest with limited repetitions, not new-data validation or causal proof.

`run-plan.json` was saved before calls. `comparison.json` contains both versions' raw outputs with full mask sets and the initial assistant reasoning, before user review. `source-packets.json` preserves complete notes and byte spans for provenance only. Each `trial-{1,2}/<group>/run/` preserves raw output, usage, prompt hashes and execution evidence. `verification.json` records the pre-review integrity and UI checks. The subsequent approval is recorded above rather than rewriting those historical checks or judgments.

## Next decision

Keep v15 unchanged. There is no remaining user-confirmed failure in this sample to motivate another prompt edit. The user subsequently authorized the [six-new-group test](../hdbv2-node-description-probe-v15-additional-v1/README.md), which is now complete: nine outputs are assistant-accepted and three are uncertain, representing two distinct titles awaiting user judgment. V15 remains an unfrozen candidate; the accepted brisket title is not being treated as an outstanding failure.

The [official GPT-5.6 guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6#prompt-migration-workflow) informed the isolated change and fixed-input retest, not the semantic judgments.
