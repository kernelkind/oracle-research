# HiGen V5.3 coverage investigation

Status: experimental findings, 2026-10-16. This is not a new HiGen version,
production policy, human judgment set, or approval to change existing meanings.
No provider calls, new encodings, hierarchy modifications, or UI updates were made.

## Current scope and finding

Prioritize recovering omitted notes that already fit the existing roots, using
full explicit meanings. Do not treat another root's membership as a negative
semantic label, or treat a shared density cluster as containment. The user has
explicitly excluded LLM calls and training from this investigation. The classifier
panels below are rejected methods; their separately reviewed cases remain useful
controls. Their hypothetical coverage gains are not an allowed automatic solution.

The saved-vector connection audit at the end of this document rejects the tested
branch expansion rule. No recovery policy is qualified, and HR35 still has 718
reachable notes. The numerical evidence supports testing the vector representation
before another tree-cut sweep, not changing the hierarchy or forcing all notes in.

## Frozen source and baseline

State:

```
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr35-v53/target/hierarchy-hr35-v53-thousand-note-v1/HR35/state.json
```

SHA256:

```
aac564fa745ac4a1d753e3f96af0a8bfa56c9bafe9b751a992a8cd5f81d2dd79
```

| Quantity | Count |
|---|---:|
| Source notes | 1,000 |
| Notes with eligible original meanings | 999 |
| Eligible original L1 entries | 6,991 |
| Initial HDBSCAN groups | 687 |
| Notes in those initial groups | 976 |
| Notes reachable in completed HR35 | 718 |
| Missing notes that were initially grouped | 262 |
| Missing notes initially entirely ungrouped | 20 |

Thus most missing notes were not initially rejected as density outliers.
Counting notes outside all displayed roots would conceal the loss and is not a fix.

## Assumptions tested

### Reranking existing saved candidates will fix coverage

An exact maximum-coverage calculation selected at most six sets from 538 saved
root candidates. Their union contains 979 notes, but the optimum six-set coverage
is 670, equal to the saved root-stage result. Requiring preservation of all 670
root-stage notes gives the same optimum. Solver gap: zero.

This bounds only this recorded candidate pool. Candidates depend on the actual
construction history; this is not proof about all possible counterfactual runs.
It does show that reranking these candidates alone cannot repair the loss.

### More root anchors or another unchanged membership pass will fix it

Using the completed global untracked pool with each root's direct originals in
the native V5.3 numerical path proposes six additional notes. Replacing those
anchors with all recursive original supports proposes zero. Adding anchors is
not a monotone expansion of HDBSCAN membership.

Fitting HDBSCAN on root supports alone and using `approximate_predict` on omitted
entries proposes two notes with recursive supports. Both strengths are below
0.5. This does not provide a substantial replacement. Prediction strength is not
a probability of semantic containment.

### Existing graph membership supplies correct classifier labels

It does not. Two existing recursive memberships conflict with their fixed scope:

- `L06298`, **Money posting destination**, is supported under `C00154`, Monetary
  resources, despite defining a destination's name rather than money.
- `L00860`, **Musicians and people who know musicians**, is supported under
  `C00062`, Musical arts, despite also admitting acquaintances who need not make
  music or act in a musical role.

These are agent diagnoses from the saved meanings, not new human judgments.
They are training positives in the completed-graph classifier, so their later
acceptance is not an independent held-out error rate. It reveals incorrect input
labels instead. Conversely, a missing relationship to Food does not prove that an
entry supported by Life or Information lies outside Food.

### A high-purity numerical community supplies a safe semantic expansion

A graph of full-meaning lexical similarities produces 33 natural communities.
Requiring all existing support notes in a community to support the same root
still proposes BMI/Obesity and Hydrogen under Finance. Relaxing unanimity admits
more notes and more scope errors. This is not an adoption candidate.

Forced six-way partitions, ordinary linkage cuts, graph community methods and
block models also produced misleading mixtures. Mechanical coverage of 976 or
999 notes does not establish useful categories or valid membership.

## Rejected classifier panel and retained case evidence

The primary text screen uses stemmed full explicit meanings, TF-IDF unigrams and
bigrams, and six independent linear SVMs. It does not duplicate the heading in
its text features. Training uses 1,648 original entries recursively supporting
the completed roots. Five-fold calibration holds out entire original HDBSCAN
groups; the threshold is the largest held-out negative margin. Labels mean saved
membership, not human semantic gold. A second note-held-out calibration also
fails the scope controls and does not qualify the method.

Only notes absent from the completed hierarchy are candidates.

| Review result | Count |
|---|---:|
| Proposed entry/root assignments | 61 |
| Proposed distinct notes | 41 |
| Strongest route per note/root | 45 |
| Agent-supported entry/root assignments | 56 |
| Qualified entry/root assignments | 4 |
| Rejected entry/root assignments | 1 |
| Distinct notes with an agent-supported route | 39 |
| Additional notes relying on qualified routes | 2 |

Rejected: generic **Work** under Tools and techniques. That same note has an
accepted **Code** route, so rejecting Work does not lose the note.

Qualified: two AI-field meanings, a Master of Music credential, and nonmonetary
value-for-value contributions. The credential's note also has a clear Piano
route; one AI note also has a financial route. Only two distinct notes depend on
qualified routes.

Hypothetical supported-only coverage is **757/1,000**, a 3.9 percentage-point
increase, recovering 13.8% of the 282 omitted notes. Including qualified proposals
would give 759. Neither count is an applied result. Do not report quality
preservation from this review alone.

A useful operational distinction is to consider an omitted note once and retain
its best supporting entry for each proposed root, rather than admit every
positively scored entry. This avoids redundant unsupported evidence such as
Work when Code provides the stronger valid route. It is not a semantic guarantee:
a highest-scoring union can still contain an out-of-scope alternative.

## Focused label correction: Food

A final controlled test kept the same full-meaning features and SVM, replacing
other-root negatives with eight explicit agent-assessed meanings outside Food.
No new positive examples or hyperparameter changes were introduced. The model
proposes eight omitted notes and rejects five separately withheld negative
entry/root controls. This tests the label assumption rather than another
clustering algorithm.

Reviewing the full source notes supports seven proposals. The eighth is a real
coverage error: **Caffeine**, from “I've had a stupid amount of caffeine today and
I still feel so tired. 4 more hours of work.” Neither the note nor its supplied
meanings establishes food or drink rather than pills or another preparation.
The classifier must not be automatically adopted despite passing the five
negative controls. It also proposes generic Knives, whose complete meaning is
not culinary; that note independently contains a valid Burgers topic.

The seven supported Food notes combined with the primary screen's 39 supported
notes cover **45 distinct previously unreachable notes**, a counterfactual
**718 → 763** (+4.5 percentage points; 16.0% of the missing notes). These are
agent-reviewed recovery opportunities, not an automatic policy result. Where
review used a different original entry from the classifier's proposal, that
alternative is explicitly recorded, not credited to the classifier.

This points toward a separate coverage-completion stage that distinguishes
**a note providing information about a node's topic** from **promoting a whole
local topic beneath that node**. Notes can have several independent topics.
Attaching a note need not create a new canonical node or admit every local topic
in it. This is a design proposal, not a change to the approved membership contract.
It still needs valid topic evidence: the caffeine counterexample remains a failure
at note level, so simply taking the highest lexical score is insufficient.

## Existing-root scope review

A sample of 20 notes was drawn before scope review from the 240 remaining omitted
notes with eligible meanings that the primary classifier did not propose, using
sorted IDs and `Random(20261016)`. One additional omitted note has no eligible
meaning and was outside this sampling population.
Against the fixed root meanings, agent review found 18 clear existing-root routes,
one qualified route, and one unresolved case. Examples include Tea → Food,
Imagination → Life, AI processors → Tools, and Petitions → Information. This small
agent-reviewed sample is not a human-gold recall estimate. It supports focusing on
membership recovery before changing the root count or pursuing another broad
clustering panel.

There are also genuine scope holes: one omitted note supplies only **Weather**,
and another only **Plants**. The first is atmospheric conditions; the second is
Plantae. Neither whole meaning is included in the six fixed roots; Life explicitly
names human/animal biology. Communication *about* those things does not turn the
things themselves into communication. These cases need different root coverage,
not relaxed admission into an existing fixed meaning.

The current investigation focuses on the reviewed cases that fit existing roots.
The Weather and Plants examples establish limits of that scope; they are not a
request to generate more roots. The saved-vector audit below evaluates numerical
connections without using construction membership as semantic truth.

## Evidence and reproduction

Retained ignored artifacts in the task worktree:

```
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-food-halves-v1/target/food-halves-v1/coverage-investigation-v2/
```

Primary evidence:

- `audit.json`: original grouping and final missing-note histories.
- `candidate-cover-results.json`: exact saved-candidate coverage calculation.
- `completed-definition-membership-results.json`: all 61 classifier proposals.
- `completed-definition-membership-agent-review.json`: all proposed assignments,
  scope qualifications, and best note/root witnesses; agent assessments only.
- `definition-membership-validation-results.json`: group- and note-held-out
  calibration, scope checks and current-label contamination.
- `unrecovered-scope-sample-input.json` and
  `unrecovered-scope-sample-agent-review.json`: frozen sample and separate review.
- `fixed-root-scope-holes.json`: full six-root meanings and the Weather/Plants cases.
- `completed-root-membership-results.json`: native direct/recursive support tests.
- `fixed-reference-prediction-results.json`: fixed-reference HDBSCAN prediction.
- `entry-communities-results.json`: full-meaning community admission failures.
- `food-semantic-negatives-plan.json` and `food-semantic-negatives-results.json`: frozen label correction and predictions.
- `food-semantic-negatives-agent-review.json`: all eight proposed notes, the caffeine rejection and alternative witnesses.
- `findings-summary.json`: machine-readable final counts and source identity.
- `final_evidence.py`: source-hash/count assertions and assembly of separate
  agent-assessment artifacts, without modifying the source hierarchy.

Other panels are retained as rejected hypotheses, not additional independent
semantic trials. Local numerical work used saved vectors and text only. No prompt,
constructor, transport, budget, source corpus or historical receipt was changed.
The task worktree remains necessary for these evidence paths.

## Rejected note-level classifier panel

The user authorized investigating a separate coverage pass. That did not establish
approval of classifier training; the user subsequently explicitly ruled it out.
The rejected offline test changed the prediction unit from original entries to
whole notes, keeping all canonical meanings, original memberships and graph
edges unchanged. Two input views were compared with the same TF-IDF/linear-SVM
settings: source-post text with URLs removed, and all eligible explicit meanings
for the note. No provider calls or new encodings were made.

Training uses the 718 currently reachable notes and their saved root memberships.
Five-fold note-held-out calibration uses the maximum negative out-of-fold margin.
These labels remain incomplete: absence from one root is not a reliable semantic
negative. This test isolates whether changing the prediction unit alone resolves
the earlier failure; it does not qualify those labels.

The frozen agent-reviewed screen contains 68 valid note/root pairs and three
abstention cases: caffeine-only intake, weather-only, and general plants under
Food. Every screen note is outside the training notes. The positive screen was
selected during earlier investigations and is not a representative recall set.

| Input | Proposed new notes | Reviewed positive routes recovered | Abstention violations | Unreviewed proposed pairs |
|---|---:|---:|---:|---:|
| Post text | 4 | 1 / 68 | 0 / 3 | 3 |
| All explicit meanings | 11 | 3 / 68 | 0 / 3 | 8 |

Post-only proposals include Arts assignments for a Prince Harry news headline
and the bare text “why was he like this?” plus a link. The supplied text does not
establish artistic or sound-related content. Passing the three abstention cases
is therefore insufficient. Meanings-only proposals need further review and
recover too few of the valid controls to qualify the pass. No admission or
automatic policy is approved by these results.

Changing the prediction unit did not resolve the admission failures. Further
classifier training or calibration is outside the current scope. The retained
review cases can be used to evaluate deterministic calculations on saved vectors.

Follow-up artifacts in the same ignored evidence directory:
`note-coverage-pass-plan.json`, `note-coverage-pass-results.json`, and
`note_coverage_pass.py`. The script is a one-off numerical diagnostic, not a
production constructor or a model-experiment execution path.

## Saved-vector connection audit

This follow-up uses only saved SSE vectors, fixed definitions and deterministic
calculations. No LLM requests, training, new encodings, hierarchy changes or UI
updates occurred. It verifies ASv6.100 provenance for all 1,000 source notes and
the frozen HR35 state hash above. Scope judgments are prior agent assessments,
not independently validated human gold.

### What whole-branch expansion necessarily brings along

Construct average linkage on the existing 687-group density-separation matrix.
For every group and root, trace the first merge connecting it to any of that
root's original reference groups. Keep all original group memberships fixed.

| Desired Food group | Incoming branch groups | Food-side branch groups | Merge distance | Other members brought along |
|---|---:|---:|---:|---|
| G142 Bread and bread preparation | 10 | 18 | 1.279689 | G145 includes Chicks and Chickens without a food restriction |
| G309 Coffee | 10 | 18 | 1.279689 | Same resulting 28-group branch |
| G529 Wine | 10 | 18 | 1.279689 | Same resulting 28-group branch |
| G207 Drinks and Beverages | 10 | 18 | 1.279689 | Same resulting 28-group branch |
| G644 Pizza and Pizza Day | 2 | 28 | 1.320454 | G224 includes Italy and Gianni Infantino |
| G095 Tea and tea culture | 25 | 118 | 1.463172 | The same incoming branch includes G402 Motor vehicles |

Distances are the existing angular density-separation values, in radians. They
are not normalized confidence scores. Every one of the 686 linkage joins was
independently checked against its full cross-branch mean distance.

The Tea result is stronger than a poorly chosen cutoff: every subtree containing
Tea and any original Food reference group necessarily contains Motor vehicles.
Choosing several such subtrees does not remove those intervening members.
Likewise, the inspected 28-group branch is not clean at entry level: `L00667`
defines Chicks as young chickens, without a food-production or culinary role.
Grouping a relevant member does not establish containment of every other member.

These are limits of whole-subtree admission on this particular tree, not proof
that all graph or clustering methods fail.

### One automatic rule, unchanged across all roots

The rule was written before execution: start from each root's original reference
groups, ascend while a branch introduces no reference group exclusive to another
root, and union the maximal branches. No fitted parameters or scope labels choose
the cut. Existing reference groups are preserved.

| Root | Reference groups | Selected groups | Previously reviewed positive entry routes selected |
|---|---:|---:|---:|
| Information, communication and relationships | 51 | 110 | 0 / 11 |
| Finance, technology and society | 37 | 158 | 16 / 34 |
| Arts, sound and communication | 19 | 66 | 0 / 3 |
| Food and dining | 15 | 143 | 1 / 1 |
| Tools and techniques | 14 | 36 | 4 / 9 |
| Life and experience | 34 | 74 | 0 / 16 |

The reviewed routes come from the earlier proposal review and the separately
drawn scope sample. These are descriptive checks on a selected agent-reviewed
panel, not a general recall estimate or independent human-gold validation.

On the separate focused Food panel, the rule selects all 13 positive entries but
also two of six outside-scope entries: generic reproductive/decorative Eggs and
general Gardening. It includes the Dogs, Animals and Motor vehicles groups.
Tools retrieves four of its six earlier group probes, missing Web technologies
and Digital security.

This rejects the rule. The proposed overlapping interpretation also fails a
structural check: with disjoint root reference sets, the rule's outputs on one
tree cannot overlap. G444 Web technologies is an Information reference and a
plausible Tools topic; its Information membership cannot justify excluding Tools.
Avoiding other roots is not a semantic boundary.

The 133 omitted notes occurring in the selected Food branches are therefore not
reported as recovered notes. No additions were applied.

### Direct vector matching does not resolve the scope controls

Nearest existing recursive Food-member cosine gives Coffee `L00228` 0.3604,
whereas the caffeine-only `L00225` scores 0.3775. The same cutoff cannot admit
that Coffee entry while rejecting that caffeine example.

An additional diagnostic uses each root's latest already encoded synthetic
representative, selected without consulting outcomes. Five roots have one;
Life has none. Food's saved representative is an earlier definition, so its scores
are diagnostic rather than results for the exact final immutable meaning.

Food-representative cosine scores are 0.2298 for Coffee, 0.1696 for Tea, and
0.2945 for generic reproductive/decorative Eggs. It does not supply a useful
single cutoff for those cases either. Exact title-and-meaning reuse, and exact
saved-vector reuse, provide zero new-note matches.

### Verified input representation and its next test

The actual frozen encoder request supplies `title + "\n\n" + explicit meaning`
but selects only the title's byte span for pooling. The meaning is context, not
the selected text. Actual request rows for Coffee, Tea and three Eggs entries
were verified against their saved identities and byte spans.

| Saved pair | Cosine |
|---|---:|
| Reproductive/decorative Eggs versus culinary Eggs | 0.98738 |
| Reproductive/decorative Eggs versus Eggs as food | 0.96038 |
| Culinary Eggs versus Eggs as food | 0.92776 |
| Two Coffee beverage definitions | 0.99834 |

The scope distinction is weak in these saved similarities, and matching the same
heading can outrank a pair sharing the culinary role. This does not prove the
encoder ignores context, nor prove a different representation will succeed.

The proposed next test is a controlled comparison of title pooling with pooling
the full existing explicit meaning, using the same frozen SSE encoder and the
same fixed positive and outside-scope cases. No wording, root scope, training or
LLM changes are proposed. That would require new SSE encodings and has not been
performed or approved by this saved-vector investigation. Its purpose is to test
the representation before further cutoff changes, not to promise full coverage.

### Retained numerical evidence

Ignored artifact directory in the retained task worktree:

```
target/food-halves-v1/root-connection-audit-v1/
```

- `plan.json`: frozen inputs, control IDs, rule and scope before execution.
- `tree.json`, `traces.json`: one compact tree and every group/root connection.
- `group-evidence.json`: every original group's titles and fixed meanings.
- `rule-results.json`, `unchanged-root-checks.json`, `rule-limitations.json`:
  all selected memberships, descriptive controls and the overlap limitation.
- `entry-diagnostics.json`: nearest Food members for every focused scope case.
- `representative-plan.json`, `representative-results.json`: frozen synthetic
  version selection and every eligible entry's direct cosine.
- `scope-pair-diagnostics.json`, `encoding-input-verification.json`: matched
  scope pairs and actual frozen pooling-span verification.
- `exact-reuse-results.json`, `verification.json`: reuse and numerical checks.

The one-off `calculate.py` is tied to this frozen HR35 packet; it is not a
production constructor or provider-execution script. Dense all-pairs linkage is
a bounded diagnostic here, not a proposed construction step at arbitrary scale.
The source hierarchy hash is unchanged and actual reachable coverage remains 718.
