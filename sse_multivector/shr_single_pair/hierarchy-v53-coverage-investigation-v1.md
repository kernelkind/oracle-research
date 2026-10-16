# HiGen V5.3 coverage investigation

Status: experimental findings, 2026-10-16. This is not a new HiGen version,
production policy, human judgment set, or approval to change existing meanings.
No provider calls, new encodings, hierarchy modifications, or UI updates were made.

## Decision supported by this investigation

Prioritize recovering omitted notes that already fit the existing roots, using
full explicit meanings. Do not treat another root's membership as a negative
semantic label, or treat a shared density cluster as containment. The tested
classifiers and clustering alternatives are **not qualified for automatic adoption**.

There is a useful partial candidate: a full-meaning text classifier proposed 41
previously unreachable notes. Reviewing every proposed entry/root assignment
supports 39 notes without the identified scope qualifications. This is a
counterfactual 718 → 757, not a generated hierarchy or human-validated result.
The classifier still fails semantic controls; the review is not proof of a general
admission rule. The remaining gap is substantial.

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

## Strongest partial result

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

## Where to focus next

A sample of 20 notes was drawn before scope review from the 241 omitted notes not
proposed by the primary classifier, using sorted IDs and `Random(20261016)`.
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

The next experiment should distinguish these two failure classes and evaluate
new-note/root routes against the actual fixed meanings. Reusing construction
membership as semantic truth would train the next method to repeat the misses.
No new provider calls are proposed by this finding.

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
