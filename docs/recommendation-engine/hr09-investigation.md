# HR09 investigation evidence

This is the maintained evidence source for the HR09 investigation. Record saved
observations separately from semantic judgments, hypotheses and experiments.
Evidence IDs remain stable as the investigation grows.

At the start of this investigation, the user instructed: **“we are not assigning
fault yet”**. Subsequent explicit user judgments and fault assignments are
recorded separately below and apply to their stated cases. E001 has no fault
assignment; E002 assigns fault to Bootstrap. No proposed correction has been
approved. Recording a model answer alone does not endorse it.
Existing investigation or prompt-trial findings elsewhere are not automatically
adopted as judgments in this record.

## E001 — Food and Dinner remain separate on the third placement

Status: **user-reviewed; the saved `neither` answer is correct for these exact
meanings**. Meaning generation remains unreviewed; no fault is assigned. This is the first case
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
record E001. The initial evidence entry contained no user semantic judgment;
the subsequent review is recorded separately below.

### User review

The user approved the saved Compare answer for this exact input:

> i think the compare answer is correct here. dinner cannot be fully within food bc it is not restricted to human consumption

Reviewed relation: **`neither`**. In particular, the user accepts that Dinner's
meaning admits nonhuman consumption while this Food meaning requires human
consumption, so Food does not contain Dinner's entire scope. This settles the
comparison judgment for E001. It does not establish whether either generated
meaning is the desired definition for its original local node, and does not
assign a meaning-generation failure or approve a change.

### Open questions

- Do the generated meanings represent the intended information scopes of the
  original local nodes?
- How does this reviewed separation contribute to the final hierarchy's
  structure and browsing decisions?

The comparison judgment is recorded above. These remaining questions have no
reviewed answers; no causal attribution or new experimental result is recorded.


## E002 — Food nests beneath Food on the fourth placement

Status: **user-reviewed; the comparison distinction is correct for the supplied
meanings; fault assigned to Bootstrap**. The user has not specified which
meaning should change or approved a prompt correction.

### Position and state transition

Saved step index `3` (zero-based), the fourth local placement. Selection phase:
`guaranteed_l1`. No consolidation had occurred.

Before:

```text
Rocket stoves · C001 (N001)
Dinner · C002 (N007)
Food · C003 (N063)
```

Incoming local: **Food (N037), original local number `1`**, from the cranberry,
rosemary, brown sugar and cinnamon sourdough post. Original context: “The
food-related hashtag and the description of sourdough bread establish the food
topic.” Original note ID:
`ab52ebc67eed9ae6d8e8bd327073ff0ed4e80e267f2b76dfcb8a4468d136c895`.
The existing Food is C003 from N063, whose provenance is recorded in E001.

### Exact comparison input

`A` is incoming local Food (N037); `B` is canonical Food · C003 (N063). The
comparison received only these titles and fixed meanings, not the posts or
local contexts.

```json
{
  "A": {
    "subject": "Food",
    "meaning": "Food is edible material intended for human consumption as nourishment or as an ingredient in something eaten. It includes prepared foods and edible culinary ingredients, including but not limited to bread, cranberries, rosemary, brown sugar and cinnamon."
  },
  "B": {
    "subject": "Food",
    "meaning": "Food is substances intended for human consumption as nourishment or as part of eating, encompassing prepared dishes and edible ingredients used to prepare or season them, including but not limited to mushroom risotto with shrimp and its culinary ingredients."
  }
}
```

### Saved comparison and consequence

Relation: **`B_contains_A`** — canonical C003 contains the incoming local Food.
The counterexample against the reverse direction was, verbatim:

> A deadly poisonous death-cap mushroom risotto mistakenly prepared and intended for humans to eat as nourishment.

The model's justification was:

> A risotto made with deadly poisonous death-cap mushrooms, mistakenly intended as human nourishment, satisfies B's general requirement of a substance intended for human consumption. B does not require every such substance to be edible. The poisonous dish fails A's edibility requirement, and information about that dish does not concern a qualifying edible food merely because its maker intended it as nourishment.

For canonical Food containing local Food, the saved answer was:

> B covers the entire A scope.

Its justification was:

> Every material in A is a substance intended for human consumption. A's nourishment purpose directly satisfies B's nourishment alternative, and A's intended use as an ingredient in something eaten satisfies B's part-of-eating alternative. A's prepared foods and edible culinary ingredients retain these requirements. B imposes no additional identity or consumer restriction absent from A.

The final reason was:

> A requires edibility as well as intended human consumption; B's general scope requires the intended consumption but does not guarantee edibility.

The incoming node was added as C004 beneath C003:

```text
Rocket stoves · C001 (N001)
Dinner · C002 (N007)
Food · C003 (N063)
└── Food · C004 (N037)
```

### User review and fault assignment

Verbatim user judgment:

> the counterexample provided by the compare model is correct here. bootstrap is at fault

The user accepts the edibility counterexample distinguishing the supplied
meanings and assigns fault to Bootstrap. The model's comparison is not recorded
as an error. The recorded generation consequence is an additional Food node
and edge produced from meanings that differ in their required edibility.

This assignment concerns the Bootstrap meanings in this case. It does not
establish that every same-titled node must have the same meaning, identify which
of these two definitions should be revised, or establish a general correction.
No prompt edit or new experiment has been authorized by this judgment.

### Provenance and verification

- [Frozen HR09 state](/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr09-v2/target/hierarchy-hr09-v2-24-note-v1/HR09/state.json), step index `3`;
  state SHA-256 `059840fdf8a43794392990ea40c685eb54019ecbd49657c465ff8101068af44e`.
- [Frozen comparison experiment](/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr09-v2/target/hierarchy-hr09-v2-24-note-v1/trial/batch-00006/experiment/experiment.json), case `C003`;
  [native results](/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr09-v2/target/hierarchy-hr09-v2-24-note-v1/trial/batch-00006/experiment/run/results.jsonl), line `2`.
- Canonical receipt-record SHA-256:
  `1ddcfa4f172c33f1b52d0860e9f1702d8bbee24c5427fd0b95d3b21805e3d4ef`.
- Bootstrap-v122 producers in the [original meaning batch](/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr09-v2/target/hierarchy-hr09-v2-24-note-v1/trial/batch-00000/experiment/experiment.json):
  `L00002` for N063 Food and `L00003` for N037 Food. Exact prompt references and
  hashes are recorded in E001; Compare is v192 in both cases.

The native report validates the receipt; its parsed answer matches the saved
step answer. The exact input comes from the prepared case. No model calls,
prompt changes, graph changes, UI updates or agent messages were made for this
record.

### Remaining questions

- Which generated meaning, or which aspect of the generation contract, should
  change to correct this Bootstrap outcome?
- What controlled experiment would distinguish candidate corrections while
  preserving valid distinctions between genuinely different meanings?

No correction or experimental result is recorded yet.
