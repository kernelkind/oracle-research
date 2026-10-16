# HiGen V5.3 coverage investigation

Status: experimental findings, 2026-10-16. This is not a new HiGen version,
production policy, human judgment set, or approval to change existing meanings.
No provider calls, hierarchy modifications, or UI updates were made. Separately
authorized full-meaning, first-sentence and member-support comparisons generated
608, 912 and 19,896 local SSE vectors, respectively; the earlier numerical panels
used saved vectors only.

## Current scope and finding

Prioritize recovering omitted notes that already fit the existing roots, using
full explicit meanings. Do not treat another root's membership as a negative
semantic label, or treat a shared density cluster as containment. The user has
explicitly excluded LLM calls and training from this investigation. The classifier
panels below are rejected methods; their separately reviewed cases remain useful
controls. Their hypothetical coverage gains are not an allowed automatic solution.

These comparisons are diagnostic probes, not admission requirements or proposed
production rules. The user identified comparison with **all groups or nodes
belonging to a canonical root**, rather than its synthetic definition, as the
useful direction for probing the relationships. Synthetic-root ranking, including
87/99, does not demonstrate admission quality. The 170-entry reference check
samples one original entry per group and does not compare every constituent
entry. No admission method, score aggregation, pooling policy or implementation
has been decided through these probes.

The saved-vector connection audit rejects the tested branch expansion rule. The
subsequent controlled full-meaning comparison improves known-root ranking but
worsens the difficult Food scope checks. First-sentence pooling does not resolve
that tradeoff: it loses known-root first-place results and worsens those Food
ordering checks. Neither supplies a qualified admission rule. HR35 still has 718
reachable notes; no additions were applied.

The subsequent member-support probe compares each Food case with all 175 original
entries actually supporting that root. Full-meaning pooling with a fixed,
moderate background adjustment improves the focused Food ordering count to 69/78.
All nine remaining ordering failures involve Caffeine. Stronger emphasis on
near-exact neighbors reverses much of the gain; this remains a probe, not a
qualified admission method or a measured coverage improvement.

Replacing the background with actual members of the other five roots improves
the focused full-meaning comparison to 77/78 at the same setting. The larger
panel improves only from 713/728 to 716/728: nine comparisons improve and six
worsen. This is another diagnostic probe, not adoption of an admission rule.

Giving each other root equal background weight has no net gain at the primary
full-meaning setting: 77/78 and 716/728 remain the totals. The focused comparisons
are identical; the larger panel trades one improved ordering for one worsened
ordering. Unequal root sizes do not explain the main remaining failures on this
panel. Neither background weighting is selected as a production policy.

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

### Verified input representation before the pooling comparison

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

The user subsequently authorized comparing title pooling with pooling the full
existing explicit meaning, using the same frozen SSE encoder. That comparison
is reported below. It does not change wording, root scope, hierarchy memberships
or trained weights and makes no LLM requests.

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

## Controlled title-versus-meaning pooling comparison

One local native `worker.py` run encoded 304 unchanged definition inputs and
returned 608 vectors. Each input was processed once; its title tokens and full
explicit-meaning tokens were pooled separately from the same contextual token
states. The input text remained `title + "\n\n" + explicit meaning`. The SSE
backbone, learned projection, checkpoint, 512-token limit and eight-input batch
size were unchanged. No text was truncated; the longest input was 344 tokens.

The run used CPU, with affinity and numerical thread limits of 24 on this
28-CPU allocation. No paid resource, provider request, LLM inference or training
was started. It used the production worker CLI directly, as supported by the
offline encoder workflow; no prompt experiment or hierarchy was constructed.
The saved configuration's container label was retained, but this was host CPU
execution, not a Docker invocation. Historical Torch 2.13.0+cpu, Transformers
4.57.1 and Tokenizers 0.22.2 versions were matched.

### Controls and reproducibility

The plan was frozen before encoding. It includes all six exact final canonical
root definitions, 99 assessed fitting entry/root combinations (96 earlier reviews
and three culinary Eggs contrasts), 28 Food outside-scope controls and a fixed
reference set of 170 selected entries.
The reference set uses the lowest still-selected original ID in each original
root reference group. Scope contrasts add exact saved definition pairs, including
the three Eggs meanings. Scope assessments are agent judgments, not new human
gold; the panel is retrospective and deliberately selected.

For 302 inputs with an available historical title vector, the fresh title vector
reproduced that vector within maximum absolute error 1.64e-7 and cosine error
2.18e-13. Both are well below the frozen replay limits. Request hashes, receipt
row identities, raw-vector hashes, model identities, source hashes and actual
selected token spans passed verification. No hierarchy state or meaning changed.

### Retrieval improves, admission is unresolved

| Known-fitting root ranked first | Title pooling | Meaning pooling |
|---|---:|---:|
| Information, communication and relationships | 7 / 11 | 10 / 11 |
| Finance, technology and society | 16 / 34 | 31 / 34 |
| Arts, sound and communication | 2 / 3 | 3 / 3 |
| Food and dining | 23 / 26 | 26 / 26 |
| Tools and techniques | 8 / 9 | 6 / 9 |
| Life and experience | 7 / 16 | 11 / 16 |
| All reviewed combinations | 63 / 99 | 87 / 99 |

The known-fitting root appears among the first three in 78/99 versus 97/99 cases.
Among the 18 positives from the earlier random-note scope sample, first-place
counts are 10/18 versus 14/18. These are ranking comparisons, not classification
accuracy: several roots can legitimately fit one entry, and other roots are not
assumed to be negative labels.

In the same fixed 170-entry reference set, at least one member of the known root
appears in the first five results in 93/99 versus 95/99 cases, and in the first
ten in 95/99 versus 98/99. These measurements do not establish that HDBSCAN
membership or a full hierarchy would improve.

An additional diagnostic reuses these vectors to separate changing the local
selection from changing the root selection. This is post-hoc, not a new frozen
policy test, and generates no further vectors:

| Local selection | Root selection | Known root first | Original Food pair orderings correct |
|---|---|---:|---:|
| Title | Title | 63 / 99 | 64 / 78 |
| Title | Meaning | 73 / 99 | 39 / 78 |
| Meaning | Title | 63 / 99 | 64 / 78 |
| Meaning | Meaning | 87 / 99 | 53 / 78 |

Changing only local pooling does not reproduce the overall ranking gain.
Changing only root pooling also worsens the Food ordering checks. The combined
result cannot be attributed solely to adding detail to the local definition.

The original difficult Food panel gives the opposite result:

| Food-versus-outside ordering check | Title pooling | Meaning pooling |
|---|---:|---:|
| Food example scores above outside example, original six controls | 64 / 78 (82.1%) | 53 / 78 (67.9%) |
| Same check with all 28 outside controls | 328 / 364 (90.1%) | 327 / 364 (89.8%) |
| Outside examples incorrectly ranking Food first, original six | 2 / 6 | 3 / 6 |
| Outside examples incorrectly ranking Food first, all 28 | 5 / 28 | 5 / 28 |

No acceptance threshold was fitted. Neither representation permits one threshold
to separate all 13 focused Food examples from even the original six controls.
Meaning pooling ranks Caffeine at 0.5378 against Food, above all focused valid
Coffee, Tea, Bread and Wine examples; the strongest of those is Bread at 0.4579.
Caffeine's definition permits consumption through foods, drinks **or other
preparations**; it does not restrict the chemical to a food role. General
Gardening also outranks most of the valid examples. Similarity is not containment.

### Meaning-sensitive distinctions improve selectively

| Pair | Title cosine | Meaning cosine |
|---|---:|---:|
| Reproductive/decorative Eggs versus culinary Eggs | 0.9874 | 0.6528 |
| Reproductive/decorative Eggs versus Eggs as food | 0.9604 | 0.6710 |
| Culinary Eggs versus Eggs as food | 0.9278 | 0.7704 |
| Social-media platforms versus X social-media platform | 0.5620 | 0.7975 |
| Emotional comfort versus Coziness | 0.3554 | 0.5716 |
| Software applications versus Apps | 0.7119 | 0.5211 |
| Publication versus Publishing | 0.7934 | 0.3903 |

The culinary Eggs pair now outranks the reproductive/culinary pairs, a useful
specific result. Other clear shared-topic comparisons become less similar.
This supports further diagnosis, not replacing production pooling or announcing
quality-preserving recovery.

### Patterns in selected and omitted explicit meanings

A separate descriptive check compares all 1,648 selected original entry/root
memberships with the 96 prior-reviewed omitted combinations, excluding the
three added culinary Eggs contrasts. It uses the saved definitions, not new
labels, training or a fitted word detector.

There is no consistent excess-length pattern: selected meanings have a median
of 27 words, versus 25 in the reviewed omissions. Within Information the medians
are 26 and 26; within Tools, 29 and 28; within Food, 26 and 29. The exact phrase
"including but not limited to" occurs in 549/1,648 selected meanings (33.3%)
and 20/96 omitted meanings (20.8%). These selected cohorts do not establish a
population effect, but they do not support excessive verbosity or examples as
a general distinguishing feature of the reviewed omissions.

The stronger observed pattern is related topics expressed through different
headings and defining classes:

- Selected **Software applications** says applications are software programs
  designed to help users perform tasks. Omitted **Apps** says software
  application programs designed to help users perform particular tasks.
- Selected **Computer code** and omitted **Code** both define programming
  instructions specifying a computer program's operations.
- Selected **Publication** and omitted **Publishing** both describe making
  content available to the public.
- Selected **Good wishes** and omitted **Holiday greetings** both explicitly
  describe expressing goodwill or benevolent wishes.
- Selected Food entry `L01112` expressly encompasses drinkable substances,
  prepared dishes and beverages. The omitted Coffee, Tea and Wine entries
  explicitly define beverages; the meaning connection is already present.

None of the 96 omitted combinations shares an exact case-insensitive heading
with an original entry selected under that root. This is an observation about
these reviewed source-entry headings, not all missing entries or synthetic
canonical headings. Whole topic families can be omitted even when their
definitions are clear.

The Food examples illustrate that concentration: only 2/175 selected Food
meanings contain "beverage" or "beverages", compared with 16/23 reviewed Food
omissions. The omissions were deliberately enriched with drink examples, so
this is a description of a known missing class, not a prevalence estimate.
Within Tools, 7/9 omitted meanings explicitly contain "software", although
only one of their headings does. Those definitions already carry domain
information not expressed in the short heading.

The Caffeine failure suggests a separate distinction worth testing: a required
defining class versus an optional use or example. Its food/drink wording is an
optional use, while Coffee's beverage class is required. The present comparison
does not isolate which clause causes the high score; a controlled clause-pooling
ablation would be a new test, not a result or approved policy here.

### Pooling-comparison evidence

Retained ignored directory in the same task worktree:

```
target/food-halves-v1/full-meaning-pooling-v1/
```

- `plan.json`, `worker-request.json`, `worker-config.json`: frozen cases,
  exact text, byte selections, reference membership, model and source identities.
- `preflight.json`: token-limit and selection validation.
- `worker-result/`: native worker receipt and 608 raw float32 vectors.
- `results.json`: every reviewed score, root/reference ranking, Food ordering
  comparison, scope-pair cosine and historical replay difference.
- `supplementary-root-ranks.json`: every outside Food control's six-root scores.
- `supplementary-factorial.json`: all four local/root selection combinations
  evaluated on the same existing vectors, without tuning an acceptance threshold.
- `meaning-patterns.json`: all compared IDs, per-root descriptive counts and
  exact selected/omitted definition pairs.
- `verification.json`: final source, span, receipt, replay and accounting checks.
- `preparation-error-v1/`: a duplicate selection-ID error caught by native input
  validation before inference; corrected globally unique IDs were then frozen.

The one-off evaluation scripts are tied to this frozen packet and do not replace
the production encoder or hierarchy constructor. All numerical source bindings
remain unchanged after synchronization with local main. No policy was activated;
actual reachable coverage is still 718 notes.

## First-sentence pooling on the same cases

The user requested testing the first sentence of the explicit meaning. This
comparison retains all 304 input texts unchanged: `title + "\n\n" + full meaning`.
It pools title, full-meaning and first-sentence tokens separately from the same
contextual states. This changes the vector selection, not the canonical meaning
or supplied context. The frozen checkpoint, projection, runtime, 512-token limit
and eight-input batch size match the preceding run. Execution again used local
CPU with four allocated cores reserved; there were no LLM calls or training.

Sentence boundaries follow sentence-ending punctuation, preserving initialisms
and common abbreviations. The saved Federal Reserve definition retains the
internal `U.S.` rather than treating it as a sentence ending. All 128 shortened
definitions and their exact removed suffixes are retained for inspection; the
other 176 are already one sentence. All six root definitions have multiple
sentences. The longest complete contextual input remains 344 tokens.

The plan, 99 assessed combinations, Food controls and 170-entry reference set
were frozen unchanged before encoding. The production worker returned 912
vectors. Its 608 title/full-meaning controls reproduce the preceding run
exactly; all 176 first-sentence/full-meaning identity controls also match
exactly. Source hashes, request/receipt identities, vector hashes and selected
UTF-8 spans passed validation. The earlier 302 historical title replays still
pass. These checks establish a controlled representation comparison, not
semantic qualification of the cases.

### Results and which side causes the loss

| Local entry pooled text | Root pooled text | Known-fitting root first | Known-fitting root in first three | Original Food orderings | Expanded Food orderings |
|---|---|---:|---:|---:|---:|
| Title | Title | 63 / 99 | 78 / 99 | 64 / 78 | 328 / 364 |
| Full meaning | Full meaning | 87 / 99 | 97 / 99 | 53 / 78 | 327 / 364 |
| First sentence | Full meaning | 84 / 99 | 98 / 99 | 50 / 78 | 285 / 364 |
| Full meaning | First sentence | 70 / 99 | 95 / 99 | 50 / 78 | 332 / 364 |
| First sentence | First sentence | 69 / 99 | 94 / 99 | 49 / 78 | 314 / 364 |

The two mixed-side rows are supplementary calculations on the same saved
vectors, not separately tuned policies. All nine local/root selection
combinations are retained. Most first-place ranking loss occurs when root
pooling is shortened. Keeping full root pooling and shortening only the local
entry loses four first-place results (Discounts, Tea, Bots and Desires) and gains
one (reproductive Eggs). How-to guides improves from fourth to third. That small
top-three gain does not establish better admission or coverage.

Root first sentences can omit substantial scope rather than just examples.
Food's first sentence names food, production, culinary culture, preparation,
preservation, provision and consumption. Later sentences explicitly define
food and include beverages, equipment, food-service operations and food-related
communication. Those sentences remain encoder context, but are no longer pooled
when selecting only its first sentence.

With both sides using the first sentence, a known-root entry appears among the
first five reference results in 94/99 cases, versus 95/99 for full meanings.
Keeping full reference meanings and shortening only the incoming entry gives
96/99. These are retrieval measurements in the fixed reference set, not a
demonstration of reliable containment.

### What the sentence boundary does and does not isolate

Caffeine is already one sentence, including its optional consumption through
foods, drinks **or other preparations**. With full root pooling, its Food score
therefore remains exactly 0.537832, above all focused valid Food examples.
First-sentence selection is not equivalent to selecting a required defining
class: optional examples and uses can occur within that sentence, while later
sentences can add admitted kinds or required distinctions.

Eggs contrasts also change unevenly:

| Definition pair | Full meaning cosine | First-sentence cosine |
|---|---:|---:|
| Reproductive/decorative Eggs versus culinary Eggs | 0.6528 | 0.7480 |
| Reproductive/decorative Eggs versus Eggs as food | 0.6710 | 0.5876 |
| Culinary Eggs versus Eggs as food | 0.7704 | 0.7713 |

Removing the decorative-egg sentence makes one generic/culinary pair more
similar and the other less similar. The culinary pair stays close. Publication
versus Publishing improves from 0.3903 to 0.4451, still below title pooling's
0.7934. This is not a consistent solution to the observed meaning distinctions.
No acceptance threshold or production representation was selected. Actual
reachable HR35 coverage remains 718 notes.

### First-sentence evidence

Retained ignored directory in this task worktree:

```
target/food-halves-v1/first-sentence-pooling-v1/
```

- `plan.json`, `worker-request.json`, `worker-config.json`: frozen source,
  evaluation and native encoder bindings; plan SHA256
  `ba980f6219a2895be690518bd3b61f08c5d667f4b3d964c989657f2151b95f79`.
- `sentence-boundaries.json`: every selected first sentence and removed suffix.
- `preflight.json`, `worker-result/`: validated inputs, native receipt and vectors.
- `results.json`: all three representations, exact replay checks and scope pairs.
- `supplementary-factorial.json`: all nine local/root selection combinations,
  with every score and ranking; no fitted acceptance threshold.
- `local-sentence-rank-changes.json`: the six changed known-root rankings when
  shortening only local pooling, with the exact selected and removed text.
- `verification.json`: final protected-source, span, receipt and replay checks.

These are frozen local encoding diagnostics, not another hierarchy construction
or a new HiGen policy. No production encoder behavior changed.

## Member-support and background-adjusted probes

### Actual reference collection and frozen cases

The user authorized literature-informed probes against actual members, rather
than the synthetic root definition. Food and dining recursively contains 175
original entries from 89 notes. Of those entries, 137 belong to 15 original
HDBSCAN groups and 38 were originally ungrouped. All 175 participate. The 38 are
shown separately as an evidence cohort, not invented as another semantic group.
Every initial group's individual support calculations remain available.

The query set contains the same 26 previously assessed fitting Food entries and
28 outside controls, including the 13 focused Coffee/Tea/Bread/Wine examples and
six original difficult controls. All 54 queries are absent from the reference
collection. These are provisional prior agent assessments, not independently
validated human gold. Saved reference membership is also not semantic gold.

The background is all 6,991 eligible original entries, not just entries under
other roots. It includes omitted Coffee and other potentially fitting entries;
it supplies a comparison distribution, not negative labels. The exact query is
excluded from its background. A supplementary calculation excludes all entries
from the query's source note from both the reference and background collections.

### Two declared numerical probes

The member-affinity component of
[Tip-Adapter (2022)](https://arxiv.org/abs/2207.09519) motivates a positive weight
for each member: `K(q,x) = exp[-beta * (1 - cosine(q,x))]`. Mean affinity over all
175 Food members is the first score. Mean affinity within each original group
is retained separately. Using the mean avoids treating a larger group as
stronger merely because it has more entries.

The second score is `log(mean_food_affinity / mean_background_affinity)`.
[Bayesian Sets (2005)](https://proceedings.neurips.cc/paper_files/paper/2005/file/182e6c2d3d78eef40e5dac7da77a748f-Paper.pdf)
motivates comparing support from supplied examples with background support.
This is a kernel-density-ratio adaptation, not the paper's Bayesian model or
an estimated probability of containment. Neither full Tip-Adapter nor SetExpan
or EgoSet is implemented here. No synthetic-root vector contributes to a score.

The plan freezes beta 5.5 as the primary setting, borrowing a published moderate
Tip-Adapter setting without fitting SSE labels. Beta 1 and 20 are predeclared
sensitivity probes. No threshold, classifier or representation was fitted or
selected from the results. Title, full-meaning and first-sentence pooling use
the same complete `title + "\n\n" + meaning` context.

### Ordering results

Each focused count compares one of 13 fitting entries with one of six outside
controls: 78 pair orderings from 19 entries, not 78 independent cases.

| Score at beta 5.5 | Title pooling | Full meaning | First sentence |
|---|---:|---:|---:|
| Closest member cosine, baseline | 42 / 78 | 42 / 78 | 48 / 78 |
| Mean similarity-weighted member support | 53 / 78 | 65 / 78 | 59 / 78 |
| Background-adjusted support | 45 / 78 | **69 / 78** | 63 / 78 |

With all 28 outside controls, full-meaning weighted support orders 351/364 pairs
correctly; background adjustment orders 355/364. All nine remaining failures are
Caffeine ranking above valid Coffee, Tea or Wine entries. The other 27 controls
score below all 13 focused positives. The expanded panel includes many easier
Basketball and Video games controls, so its percentage is not an independent
accuracy estimate or stronger evidence than the difficult panel.

Across all 26 previously assessed fitting entries and 28 outside controls,
adjusted full-meaning support orders 713/728 pairs correctly. Fourteen failures
involve Caffeine; one involves Chicks ranking above Drinks. Generic
reproductive/decorative Eggs scores below the culinary Eggs entries. These
specific distinctions do not establish a general admission boundary.

### Sensitivity and the remaining mechanism

| Beta | Full-meaning member support | Full-meaning adjusted support | Adjusted support excluding the query's whole source note |
|---|---:|---:|---:|
| 1 | 64 / 78 | 69 / 78 | 69 / 78 |
| 5.5 | 65 / 78 | 69 / 78 | 69 / 78 |
| 20 | 53 / 78 | 23 / 78 | 20 / 78 |

At beta 5.5, the same-note exclusion leaves all focused ordering counts
unchanged. Eight query notes have Food references removed by this check.
It does not imply that their individual scores are unchanged.

The sharper beta 20 result exposes a limitation of background adjustment.
Coffee `L00228` has other omitted Coffee entries at cosine 0.9993, 0.9916 and
0.9786, while its closest Food reference is `L00445`, Food, at
0.5731. That reference explicitly defines food as substances suitable for people
to eat or drink for nourishment. With full-meaning pooling, the Food/background
support ratio for this Coffee is 2.056 at beta 5.5 but only 0.00496 at beta 20.
Omitted near-equivalent entries dominate the sharp background calculation.
This is a failure of that score at that setting, not evidence against Coffee's
Food relationship. Background adjustment is not uniformly beneficial.

Caffeine remains problematic even with moderate weighting. Its full definition
has optional consumption through foods, drinks or other preparations. It strongly
matches actual Food definitions and Diets, although its defining class is a
chemical stimulant. Its moderate adjusted ratio is 3.156, above nine focused
beverage examples. The probe exposes this mismatch without resolving it.

### Encoding, controls and evidence

The probe reuses vectors for 302 original entries from the previous exact-text
packet. The worker encodes 6,617 distinct new contexts and 15 replay contexts, yielding
19,896 new vectors; further exact-text duplicates share those vectors. All
three selections share each encoder forward pass. CPU execution reserves four
allocated cores. Inputs are sorted by length and batched at 32; the longest is
165 tokens, with no truncation. The backbone, checkpoint, projection and matched
runtime are unchanged. This uses the existing native worker, not a new provider
execution path; no LLM inference, training, paid resource or hierarchy change
was introduced.

All 45 replay vectors pass the frozen limits: maximum absolute error 5.59e-8
and cosine error 5.94e-14. All 6,991 title vectors also reproduce their native
historical encodings within maximum cosine error 1.82e-13. Native request,
receipt, span, model and source hashes pass. Independent scalar summation checks
the kernel means; reference duplication and equal-set ratio controls pass.
The calculation stores a 54-by-6,991 cosine matrix per representation, never an
all-corpus pairwise matrix. A production all-entry pass is not proposed by this
bounded probe; no hierarchy coverage gain is claimed. HR35 remains at 718 notes.

Retained ignored evidence in this task worktree:

```
target/food-halves-v1/member-support-probes-v1/
```

- `plan.json`: frozen cases, references, all background IDs, reuse mappings,
  formulas and settings; SHA256
  `502f2b17668e3686270c7f898bd4f7166ff1e1e273763daf3b4f464497bc05fc`.
- `worker-request.json`, `worker-config.json`, `preflight.json`, `worker-result/`:
  native encoder inputs, receipt, selections and raw outputs.
- `cosines.npz`: every query-to-original score, including all 175 references,
  for all three representations, with exact ID mappings.
- `scores.json`: every declared weighting setting, original-group cosine
  ranges and affinities, complete-root support, background support and ratio,
  nearest reference definitions, and the same-note controls.
- `metrics.json`: every focused/expanded ordering, including failures; all
  fixed beta settings and same-note variants remain visible.
- `reference-group-evidence.json`, `query-evidence.json`: exact source meanings,
  headings, notes and reference membership.
- `background-neighbor-diagnostics.json`: exact background connections that
  explain the sharp Coffee penalty and other selected contrasts.
- `report.md`, `verification.json`: compact tables and final integrity checks.

## Other-root background probe

The user proposed replacing whole-corpus background similarity with similarity
to entries belonging to the other roots. This probe changes only that denominator;
Food's 175 original reference entries, every cosine, every provisional case,
pooling method, weight setting and source-note control remain fixed. It reuses
the preceding saved matrices without encoding, LLM calls, training or graph edits.

The five roots contain 1,473 unique original entries: Information 463, Finance
421, Arts 225, Tools 91 and Life 273. The calculation pools those entries once
each, so larger roots contribute proportionately more members. Separate per-root
means and cosine ranges are saved, not replaced with synthetic-root vectors.
This source has no original-entry overlap between roots, although notes can
occur under several roots. Other-root membership is comparison evidence, not a
negative semantic label; an incoming topic can legitimately fit several roots.

The new score is `log(mean_food_affinity / mean_other_root_affinity)`. As before,
the exact query is excluded from the denominator, and a separate calculation
excludes its whole source note. No threshold or root-weighting policy is chosen.

| Pooled text, beta 5.5 | Whole-corpus background, focused 78 | Other-root background, focused 78 | Whole-corpus background, expanded 364 | Other-root background, expanded 364 |
|---|---:|---:|---:|---:|
| Title | 45 / 78 | 55 / 78 | 309 / 364 | 319 / 364 |
| Full meaning | 69 / 78 | **77 / 78** | 355 / 364 | 363 / 364 |
| First sentence | 63 / 78 | 68 / 78 | 344 / 364 | 352 / 364 |

For full meanings, eight focused orderings improve and none worsen. The remaining
failure is Wine `L04121` scoring below Caffeine `L00225`. The same eight changes
occur in the 13-by-28 expanded panel. These remain pair orderings over selected
entries, not independent cases, classification accuracy or measured admissions.

The larger 26-by-28 panel reveals a tradeoff: 713/728 becomes 716/728, with nine
improved and six worsened comparisons. Newly worsened cases put Chicks above
Slush drinks or Beverages, generic Eggs above Beverages or Drinks, and Gardening
above Drinks. All twelve remaining failures and all changed pairs are retained.
The focused 77/78 result therefore does not establish that the adjustment is
uniformly better or supplies a safe admission boundary.

The changed reference collection explains the Coffee/Caffeine improvement:

| Entry, full meaning at beta 5.5 | Food / whole-corpus support | Food / other-root support |
|---|---:|---:|
| Coffee `L00228` | 2.056 | 3.089 |
| Coffee `L00560` | 2.042 | 2.976 |
| Caffeine `L00225` | 3.156 | 2.853 |

Coffee's numerator is unchanged, but its denominator no longer includes omitted
near-equivalent Coffee entries outside the roots. Caffeine's mean affinity to
the selected other-root members is higher than its whole-corpus mean, reducing
its relative Food score. This establishes what changed numerically without
asserting that either score measures semantic containment.

| Full-meaning beta | Whole corpus, focused 78 | Other roots, focused 78 | Other roots excluding same-post entries |
|---|---:|---:|---:|
| 1 | 69 / 78 | 72 / 78 | 72 / 78 |
| 5.5 | 69 / 78 | 77 / 78 | 77 / 78 |
| 20 | 23 / 78 | 46 / 78 | 46 / 78 |

The stronger weight remains substantially worse than moderate weighting.
Excluding source-note matches does not alter the primary full-meaning counts.
All 972 Food numerator calculations agree with the earlier run; independent
scalar sums and recombining the five root contributions verify the changed
denominator. All protected hashes pass. Actual HR35 coverage remains 718 notes.

Retained ignored evidence:

```
target/food-halves-v1/other-root-background-probe-v1/
```

- `plan.json`: complete root memberships and frozen calculation; SHA256
  `eee8a2524eb364622e45f3b57cdbce2d156ea8ee46e4509112f95101297ddc78`.
- `scores.json`: both denominator scores, all per-root contributions and group
  scores, all three representations and weight settings, and source-note controls.
- `metrics.json`: every pair ordering and every improvement/regression.
- `report.md`, `verification.json`: compact comparisons, all larger-panel
  failures, sensitivity and integrity checks. Every member cosine remains in
  the preceding probe's source-bound `cosines.npz`.

## Equal-root background weighting probe

The user authorized testing equal weights for the other five roots. The previous
denominator pooled their 1,473 original entries, so Information's 463 entries
contributed more total weight than Tools' 91. The new denominator first takes
each root's mean member affinity, then averages those five means. Every root
therefore supplies 20%, while members within each root remain equally weighted.
Food's own 175 references retain their previous weights.

Only this combination of the saved root means changes. All source meanings,
memberships, vectors, cases, fixed beta values and same-note exclusions remain
unchanged. The score remains `log(food_support / background_support)`. No new
encoding, LLM inference, training, hierarchy modification or fitted threshold
is involved. Both alternatives compare original members, not synthetic roots.

| Pooled text, beta 5.5 | Pooled other-root entries, focused 78 | Equal roots, focused 78 | Pooled entries, all 728 | Equal roots, all 728 |
|---|---:|---:|---:|---:|
| Title | 55 / 78 | 54 / 78 | 657 / 728 | 657 / 728 |
| Full meaning | 77 / 78 | 77 / 78 | 716 / 728 | 716 / 728 |
| First sentence | 68 / 78 | 69 / 78 | 712 / 728 | 712 / 728 |

For full meanings, none of the focused orderings changes. Caffeine still scores
above Wine `L04121`. On the broader panel, Drinks `L01143` improves above
Gardening `L03273`, but Beverages `L06837` worsens below generic Eggs `L02984`.
The totals conceal this one-for-one exchange. The same exchange occurs when
all references from the candidate's source note are excluded.

| Full-meaning beta | Pooled entries, focused 78 | Equal roots, focused 78 | Pooled entries, all 728 | Equal roots, all 728 |
|---|---:|---:|---:|---:|
| 1 | 72 / 78 | 72 / 78 | 712 / 728 | 711 / 728 |
| 5.5 | 77 / 78 | 77 / 78 | 716 / 728 | 716 / 728 |
| 20 | 46 / 78 | 46 / 78 | 644 / 728 | 645 / 728 |

The focused full-meaning outcomes are unchanged at all three fixed settings,
including the source-note exclusion variant. Small effects on other pooling
methods or the larger panel do not establish an overall improvement. This probe
does not support unequal root size as the main remaining mechanism here.

All 972 candidate/setting calculations retain their original Food numerator and
individual root means. Recombining member counts independently reproduces the
old denominator; equal-weight means lie between the individual root means and
are invariant to root order. All input/output hashes and improved/worsened pair
counts reconcile. Actual HR35 reachable coverage remains 718 notes.

Retained ignored evidence:

```
target/food-halves-v1/equal-root-background-probe-v1/
```

- `plan.json`: frozen weighting contrast and protected inputs; SHA256
  `715d668d6f5bb3638f8ca21c743e17ff3c5090b251bf0396b9393492276aeb9c`.
- `scores.json`: all original root means, old/new root weights, unchanged Food
  support and both background scores for every fixed setting.
- `metrics.json`: every old/new pair ordering and all individual changes.
- `report.md`, `verification.json`: compact results, complete failure lists,
  sensitivity and integrity checks. These are probes, not admission requirements.
