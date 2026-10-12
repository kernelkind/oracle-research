# HR09 investigation evidence

This is the maintained evidence source for the HR09 investigation. Record saved
observations separately from semantic judgments, hypotheses and experiments.
Evidence IDs remain stable as the investigation grows.

User instruction, October 12, 2026: **“we are not assigning fault yet”**.
No expected relation, error label, responsible component or proposed correction
has been established for E001. Recording a model answer does not endorse it.
Existing investigation or prompt-trial findings elsewhere are not automatically
adopted as judgments in this record.

## E001 — Food and Dinner remain separate on the third placement

Status: **observed; correctness and fault unresolved**. This is the first case
entered into this investigation, not a claim that all earlier inputs have been
qualified or that this is the earliest possible defect.

### Position in construction

HR09 uses the saved ASv6.100 local hierarchies, Bootstrap-v122, Compare-v192,
Consolidation-v18 and PPv35-post-meaning-v1, with GPT-6.1 Sol medium.
The relevant saved construction step is index `2` (zero-based), the third local
placement. Its selection phase is `guaranteed_l1`. No consolidation had occurred.

Before this placement:

```text
Rocket stoves · C001 (N001)
Dinner · C002 (N007)
```

Incoming local node: **Food (N063), original local number `1`**. Its independently
generated meaning had already been saved. Both existing canonical nodes were
roots, with no canonical ancestors. The saved Food/Rocket stoves answer was
`neither`; this evidence item concerns the Food/Dinner answer.

### Exact comparison input

The request supplied only the two subjects and fixed meanings below. `A` is the
incoming local Food; `B` is the existing canonical Dinner. Original posts, local
contexts, note IDs and graph structure were absent from this comparison input.

```json
{
  "A": {
    "subject": "Food",
    "meaning": "Food is substances intended for human consumption as nourishment or as part of eating, encompassing prepared dishes and edible ingredients used to prepare or season them, including but not limited to mushroom risotto with shrimp and its culinary ingredients."
  },
  "B": {
    "subject": "Dinner",
    "meaning": "Dinner is a main meal of the day, eaten in the evening or at midday, comprising foods that can vary and optionally accompanied by drinks."
  }
}
```

### Saved answer

Relation: **`neither`**. The following are verbatim excerpts from the saved answer,
not investigator judgments.

For **Food contains Dinner**, the counterexample was:

> A dog's main evening meal consisting solely of dog food intended exclusively for canine consumption.

Its justification was:

> A dog's main meal eaten in the evening satisfies B's meal, timing and food requirements; B does not restrict the recipient to humans. Dog food intended exclusively for canine consumption does not satisfy A's human-consumption requirement. This meal concerns neither qualifying human food nor its preparation or consumption.

For **Dinner contains Food**, the counterexample was:

> An apple intended and eaten solely as a small human midmorning snack, with no dinner or other main-meal role.

Its justification was:

> An apple intended for human consumption as a snack satisfies A. A small midmorning snack is not a main meal eaten at midday or in the evening. Stipulating that the apple is intended and used only for that snack excludes a dinner-use connection; its potential suitability for dinner does not establish one.

The model's final reason was:

> B permits nonhuman main meals outside A's human-consumption scope, while A permits food with no connection to B's specified main meals.

### Resulting construction state

The local Food was added as canonical **C003**, without a parent or child edge:

```text
Rocket stoves · C001 (N001)
Dinner · C002 (N007)
Food · C003 (N063)
```

The three nodes were separate roots at this moment. The saved meanings were
retained. This record does not describe them as incorrect or specify a missing
edge.

### Original evidence behind the meanings

These original entries were available during meaning generation; they were not
part of the Food/Dinner comparison request.

| Node | Original note ID | Local number | Original context |
| --- | --- | --- | --- |
| Dinner · C002 (N007) | `26749e4bb8c7c7c2d53e303033b7f2641952894edd51bab1e9deafbf46be81b2` | `1` | The author describes dinner tonight and identifies its foods. |
| Food, later C003 (N063) | `a7475c940b50d31d115c9cea990b14b1c6c3b02232e9a005305e0257373fc5dc` | `1` | The dish title and ingredient list establish food as the main topic. |

N007 describes the writer's dinner of lamb, steamed seasoned broccoli and baby
potatoes, with wine available. N063 is a mushroom-risotto-with-shrimp recipe and
ingredient list. The complete original posts and AS entries remain in the
[frozen corpus](/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr09-v2/target/hierarchy-hr09-v2-24-note-v1/subjects.json). These descriptions establish provenance,
not a reviewed relation or a prescription for how broadly to define the nodes.

### Provenance and verification

- [Frozen HR09 state](/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr09-v2/target/hierarchy-hr09-v2-24-note-v1/HR09/state.json); SHA-256
  `059840fdf8a43794392990ea40c685eb54019ecbd49657c465ff8101068af44e`.
- [Frozen comparison experiment](/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr09-v2/target/hierarchy-hr09-v2-24-note-v1/trial/batch-00004/experiment/experiment.json), case `C002`;
  [native results](/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr09-v2/target/hierarchy-hr09-v2-24-note-v1/trial/batch-00004/experiment/run/results.jsonl), line `2`.
- Canonical receipt-record SHA-256:
  `6e0d91a0f4d771fe790db5d1c86a1f69feac22f24f911dbc22c11b461566e5d9`.
- Bootstrap producers: [original meaning batch](/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr09-v2/target/hierarchy-hr09-v2-24-note-v1/trial/batch-00000/experiment/experiment.json),
  cases `L00001` (Dinner) and `L00002` (Food).
- [Frozen Bootstrap-v122 prompt](/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr09-v2/sse_multivector/shr_single_pair/Hierarchy-bootstrap-v122.md);
  file SHA-256 `1d5df25cb5928d7623ea5f4a5427f3b74cfa37aa3fec11f10c2ea20109599039`.
- [Frozen Compare-v192 prompt](/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr09-v2/sse_multivector/shr_single_pair/Hierarchy-compare-v192.md);
  file SHA-256 `4d8968160cf06520f3d94b54e6ca7acf0b9486bf0e3b398bdbdaad72ca854946`.

The shared runner's read-only `show --case C002 --json` validated the native
receipt. The saved answer was matched to its receipt digest and to construction
step `2`; the exact input was read from the frozen prepared case. No new model
calls, prompt changes, graph changes, UI updates or agent messages were made to
record E001. No new semantic judgment was supplied by the user.

### Open questions

- What relation should these two supplied meanings establish?
- Do the generated meanings represent the intended information scopes of the
  original local nodes?
- Does the nonhuman-recipient counterexample respect Dinner's supplied meaning
  and the intended comparison contract?

These are questions for investigation. No answer, causal attribution or
experimental result is recorded yet.
