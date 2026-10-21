# HR09 investigation evidence

This is the maintained evidence source for the HR09 investigation. Record saved
observations separately from semantic judgments, hypotheses and experiments.
Evidence IDs remain stable as the investigation grows.

## Current review policy

The user clarified: disregard **all conclusions** previously drawn from the
evidence, while retaining the evidence itself. Original posts, prepared inputs,
model outputs, graph snapshots and receipts remain observations. Prior relation
judgments, scope approvals and fault assignments below are historical statements,
not current gold or established diagnoses. Reassess each case independently;
do not force a new result to preserve a former judgment. The
[review-reset record](../../../sse_multivector/shr_single_pair/bootstrap-test-case-reset.md)
describes restored data and the continuing ASv6.100 provenance requirement.

## E001 — Food and Dinner remain separate on the third placement

Status: **saved observation; semantic conclusions require fresh review**.
The previous comparison approval and consumer-scope discussion remain recorded
below but do not establish the current answer or intended topic boundaries.
No new model result or prompt correction is established by this clarification.

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
frozen corpus (original native evidence). These descriptions establish provenance,
not a reviewed relation or a prescription for how broadly to define the nodes.

### Provenance and verification

- Frozen HR09 state (original native evidence); SHA-256
  `059840fdf8a43794392990ea40c685eb54019ecbd49657c465ff8101068af44e`.
- Frozen comparison experiment (original native evidence), case `C002`;
  native results (original native evidence), line `2`.
- Canonical receipt-record SHA-256:
  `6e0d91a0f4d771fe790db5d1c86a1f69feac22f24f911dbc22c11b461566e5d9`.
- Bootstrap producers: original meaning batch (original native evidence),
  cases `L00001` (Dinner) and `L00002` (Food).
- Frozen Bootstrap-v122 prompt (original native evidence);
  file SHA-256 `1d5df25cb5928d7623ea5f4a5427f3b74cfa37aa3fec11f10c2ea20109599039`.
- Frozen Compare-v192 prompt (original native evidence);
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
comparison judgment for the original fixed meanings. That earlier review did
not establish whether either meaning was the desired definition for its local
node. The subsequent fresh review below addresses Dinner's consumer scope.

### Fresh Bootstrap review after the test-case reset

After retiring the existing Bootstrap test collection, the user explicitly
selected E001 for fresh consideration. Historical prompt-development judgments
are not assumed as gold for this review.

User replies, verbatim:

> i think the question here is, is the author of the dinner post human?

> we've already established that bootstrap can infer things

The assistant clarified that Bootstrap can infer a human speaker from this
first-person dinner account, and that generalizing beyond this particular dinner
should not automatically discard the human eating context from Dinner's meaning.
The user agreed:

> right

Recorded scope clarification: infer the human speaker from the original post
and retain the human eating context while defining the broader Dinner topic.
Under the latest conclusions reset, that prior agreement is not automatically a
current validation rule; the original evidence must be examined independently.
An explicit statement that the writer is human is not required. This approval
concerns E001; it does not make every inferred detail a restriction on every
category. The saved Dinner string lacks an explicit human-consumer condition.

The exact revised standalone wording remains open. The existing comparison
still concerns the original unchanged definitions; no new relation is certified
for a revised Dinner meaning. No prompt, test-case dataset, saved model output
or hierarchy has been changed, and no inference has been run for this review.

### Open questions

- What standalone Dinner wording faithfully expresses the approved human scope?
- Does Food's generated meaning represent its original local node's scope?
- How does this reviewed separation contribute to the final hierarchy's
  structure and browsing decisions?

The original comparison judgment and fresh Dinner scope clarification are
recorded separately above. These remaining questions have no reviewed answers;
no causal attribution or new experimental result is recorded.

## E002 — Food nests beneath Food on the fourth placement

Status: **saved observation; semantic conclusions require fresh review**.
The prior comparison approval and Bootstrap fault assignment are historical
judgments, not current diagnoses. No prompt correction is approved by the
conclusions reset.

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

- Frozen HR09 state (original native evidence), step index `3`;
  state SHA-256 `059840fdf8a43794392990ea40c685eb54019ecbd49657c465ff8101068af44e`.
- Frozen comparison experiment (original native evidence), case `C003`;
  native results (original native evidence), line `2`.
- Canonical receipt-record SHA-256:
  `1ddcfa4f172c33f1b52d0860e9f1702d8bbee24c5427fd0b95d3b21805e3d4ef`.
- Bootstrap-v122 producers in the original meaning batch (original native evidence):
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
