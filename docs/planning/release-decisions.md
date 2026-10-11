# October 18 release decisions

Updated October 10, 2026. This is the written record of the planning discussion.
Agreed requirements, tentative choices and existing-data facts are distinguished
below. The overall plan is not approved. Approval of an individual requirement
or task-view edit does not approve the whole plan. Approved scheduling changes
are recorded below; other weekly targets and exact dates remain proposals.

**Distillation preparation — October 10:** the user approved identifying one
student model for Bootstrap and one for Compare while both prompts remain
under development, so their eventual final fine-tunes can each run as one
planned campaign after freeze. Investigate model suitability and verify the
training paths before that handoff. The work is distillation preparation,
not prompt or hierarchy development. The user subsequently confirmed that
the distilled Compare model needs only the relation; teacher reasons remain
diagnostic evidence. This does not change either teacher prompt or select a
student. Bootstrap's final target format, training volume and recipes remain
open. Current subject-derived qualification
inputs require ASv6.100; pre-ASv6.100 results remain historical evidence.
The user then authorized small reviewed development training sets, GB10 pilot
fine-tunes against fixed development snapshots, and comparison of learning,
remaining errors and cost. Broaden Bootstrap candidate screens before narrowing
its pilot. These temporary pilots do not freeze the prompts or establish final
training volume, settings or student choices. The user confirmed meaning or null
for Bootstrap pilot outputs, represented by a single `meaning` field; the full
teacher responses remain review evidence. Their source-bound data roles and
qualification requirements are recorded in the owned preparation document.
The separate SP model decision, release gates, schedule and spending approvals
are unchanged. See the
[model investigation](../../sse_multivector/SHR-FINETUNING-MODEL-RESEARCH.md#bootstrap-and-compare-selection).

The user approved a read-only focused task graph backed by
[`release-plan.json`](release-plan.json). Agents maintain its task text, status
and dependencies from explicit instructions; Cytoscape and ELK render it without
manual coordinates. This document remains the source for decisions and their
rationale. On September 29 the user approved retiring the obsolete draw.io view
and opening this task graph at the existing planning root URL. The obsolete
diagram, viewer, renderer and their tests are removed; earlier versions remain
in Git. This changes the interface, not task contents, dependencies, scheduling
decisions or the proposal status of the calendar below.

**Track views approved September 30:** the graph defaults to Required release;
Optional model shows distillation work, and Both includes the full plan. Shared
foundation tasks appear in both views as the same records. Final snapshot,
protocol, service, Notedeck and publication work belong to the required release;
training data, training setup, fine-tuning pilots, model packaging and
model-generated-hierarchy checks belong to the optional model track. Earlier
cycle/navigation experiments remain historical and accessible in Both, not
current prerequisites. Shared HDBSCAN and separate-title work remains
conditional. The selector filters the graph and task picker; direct links
outside the view remain visible in task details and switch tracks when followed.
This changes navigation only: statuses, dependencies, approvals, release gates
and undecided implementation methods are unchanged.

**Node-label presentation approved October 1:** task titles are prominent;
track labels and hidden-link counts occupy a smaller, muted footer below a
divider. The displayed information, graph behavior and plan data are unchanged.

This discussion is for planning: outcomes, dependencies, open decisions and
timing. It does not select implementation methods or experimental procedures.
Readiness is not authorization to research, implement, assign agents or spend;
each task requires explicit approval to begin.

**Priority discussion — October 5:** the user proposed emphasizing useful
hierarchies and the SP distillation pilot, then explicitly clarified that this
was not a fixed ranking. Audit proposed priorities against the release goal
rather than treating them as settled. The efforts can proceed in parallel;
the SP pilot informs later fine-tuning but does not measure SHR performance.
SHR fine-tuning remains conditional on validating an SHR-built hierarchy; no
separate SHR pilot is approved here. Node sorting is deferred as nice-to-have.
The release requirements and deadline remain unchanged.

**Hierarchy planning focus — October 8:** the user expects results from the
compare-prompt hierarchy builder, specifically. Center planning on that effort
reaching a useful hierarchy and then a launch-sized build. Vector work remains
a parallel experiment, not a prerequisite or an equally expected release path.
This is a working expectation, not semantic acceptance, production adoption or
authorization to stop or redirect another agent. Publication and Notedeck work
are planned in parallel rather than used to pace hierarchy development; their
required completion gates remain unchanged. No new schedule is fixed.

**Task-summary convention approved October 1:** the graph is a planning view,
not an experiment log. Every task description gives a brief outcome, current
state and real blockers or start conditions. Keep model settings, experiment
counts, run histories and detailed findings in linked workstream records rather
than the UI. This applies to completed and historical tasks too. Scope, statuses,
tracks, dependencies and approvals are unchanged; concise summaries do not
replace the full decision record.

**Parallel work — status reconciled October 2:** corpus and Notedeck preparation
started September 30. A 200-note experimental hierarchy using saved outputs has
since been generated and is under further development. Task 03 remains in
progress; the planned validation ladder and 100-note acceptance gate remain open.
The Notedeck browser UI is approved and committed; task 15 is waiting for
protocol agreement and service implementation before integration. Completion
links, acceptance requirements and open implementation choices are unchanged.

**Parallel hierarchy-construction candidates — status reconciled October 8:**
Frontier-based and vector-space approaches are both being tested within the
existing hierarchy investigation. Record their progress separately; neither is
selected or accepted.
These are construction candidates, not new release tracks or additional tasks.

The [compare-prompt hierarchy builder](../../../oracle-mvp-shr-pair-correctness-v1/sse_multivector/shr_single_pair/README.md#resumed-hierarchy-iteration-fresh-construction-and-producer-diagnostics)
previously completed nine notes. Its latest shaped browsing menu has six roots,
at most six children per node and strictly narrowing distinct note sets; every note is
reachable in one or two selections. The underlying construction graph does
not meet those menu constraints. Semantic contradictions and full
meaningful-group coverage remain unresolved. A fresh nine-note construction
uses revised meaning generation and comparison wording. Root placement is
complete; deeper placements are being tested. Improved selected controls do
not establish whole-hierarchy consistency or 100-note acceptance.
[Candidate-selection replay](../../../oracle-mvp-canonical-sse-scale-v1/sse_multivector/shr_single_pair/README.md)
reduces comparisons on saved evidence but misses contradiction and uncertainty
checks. No scalable construction policy is adopted.

The current trials test manageable choices, including roots, and strict
narrowing of distinct recursive note sets at each downward step. The user also
requires useful discovery of meaningful groups, not only short paths to
individual notes. Six choices is a provisional trial bound, not an approved
production implementation or proof of browsing quality.

The [current vector investigation](../../../oracle-mvp-vector-hierarchy-planning-v1/sse_multivector/vector-hierarchy-experiments.md)
has run relationship-model fits, without qualifying transfer or selecting a
model. Its latest browsing prototype instead groups saved ASv6.100 subject
vectors into a six-choice tree covering all 213 notes, with three selections
to leaves. Agent finding review reports nine full matches, one partial match
and two misses across twelve requests. It improves access to some previously
hidden notes but makes some earlier routes harder; every root branch has
misleading labels. These are agent assessments, not user acceptance, a
controlled speed result or adoption of this construction method.

Earlier construction evidence remains relevant but does not describe the
current runs:

The earlier [frontier-based 200-note candidate](../../../oracle-mvp-scalable-hierarchy-v12/sse_multivector/scalable-hierarchy-v1/README.md#sh5-200--actual-browsing-menu-construction-sprint)
became cycle-free after joint review, without establishing browsing quality.
The subsequent [sequential construction run](../../../oracle-mvp-scalable-hierarchy-v12/sse_multivector/scalable-hierarchy-v1/local-hierarchy-connection-trial-v1.md)
ended at 5,000 attempts after processing 437 of 3,239 pairs. It did not meet the
hierarchy-quality goal; broader placement and reverse-order execution were
unfinished. Repeated ancestry checks consumed much of the allowance.

[Equivalence-aware construction reuse](../../../oracle-mvp-shr-scope-transfer-v1/sse_multivector/equivalence-reuse-replay.md)
was implemented in its worktree. A bounded two-order test produced a useful
Piano branch but exposed contradictory Diet judgments and order-dependent
retrieval. That evidence does not establish semantic quality or
complete-hierarchy scalability. The earlier
[single-pair relationship-prompt effort](../../../oracle-mvp-shr-single-pair-v1/sse_multivector/shr_single_pair/README.md)
exhausted its iteration allowance without meeting acceptance. Neither result
selects the current prompt or production construction method.

The earlier [vector-space 100-note builds](../../../oracle-mvp-vector-hierarchy-v1/sse_multivector/vector-hierarchy-ten-hour-goal.md#result-and-review)
remain unsatisfactory historical evidence. ASv6.48 is deprecated for new work
in the current vector investigation. Its prepared subject vectors and later
relationship-model fits are separate from the 213-note browsing prototype;
neither establishes accepted complete-hierarchy quality. The pilot's 200
final-test posts remain reserved for their agreed evaluation.

The user designated [ASv6.100](../../sse_multivector/subject-prompt-goal-v1/asv6.100/README.md)
as the current SOTA subject prompt and baseline for future comparisons on
October 4, following the [completed diverse-input assessment](../../sse_multivector/subject-prompt-goal-v1/asv6.100-generalization-v1/README.md).
Measured omissions, incorrect relationships and uncertainties remain; the
designation is not production adoption or whole-hierarchy acceptance.
The full prompt is separately frozen for the distillation pilot, whose 1,300
teacher labels are collected and structurally verified. All three students
have now completed training through 1,000 notes. Qwen's response collection
is complete; dense Gemma and Gemma MoE are still collecting evaluation
responses, according to the October 8 progress observation. The
[DSRv1 reviewer](../../sse_multivector/distillation-review-v1/README.md#october-8-qualification-evidence)
failed qualification; bulk semantic review has not run and no student is
selected. Output collection is not semantic acceptance. The
[pilot process](fine-tuning-pilot-process.md) records the evaluation safeguards.
Task 05 is complete and 06 is in progress. The October 4 pilot-specific teacher
approval makes 17 → 05 helpful rather than required; release teacher selection
and the full-training-data gates remain unchanged. The useful 100-note
acceptance gate, release tracks, broader generation hold and production choices
remain unchanged.

**Broader-corpus generation hold — October 1:** the user is undertaking prompt
stress-testing and has put generation of the additional notes on hold until that
testing is complete. Shared task **30 · Stress-test prompts** is in progress,
with a required 30 → 03 link. The start condition is specifically new corpus
subject/mask generation; corpus selection and offline preparation may continue.
Task 03 remains in progress for preparation and experimental construction using
saved outputs; completed prompt-development task 01 remains complete. Testing
methods, acceptance criteria and prompt changes belong to that workstream;
this planning update selects none.

Final teacher selection also waits for prompt stress-testing, through a required
30 → 17 completion link. Comparison work may continue; the choice needs evidence
for the prompts we will actually use. Any rechecking belongs to the comparison
workstream. Existing results remain useful evidence; no teachers are selected.

Reusable corpus-preparation code is committed. The 200-note experiment uses
unchanged saved outputs from 100 food/drink and 100 music notes, with their
original prompt/model provenance; it has not been regenerated with ASv6.100.
This is experimental construction, not an accepted validation run or
release-corpus selection.
The reviewed 100-note hierarchy remains a prerequisite for completing the
planned broader validation; other completion requirements are unchanged.
Clearing the stress-testing hold is not authorization for model calls or spending.

**300-note corpus selection — October 2:** the user approved selecting software
and computing as the third area, then replacing two address-based replies found
by direct event inspection. Software v2 keeps the other 98 entries and the
original food/drink and music posts unchanged. The current software addition has
89 authors, at most two posts each; the combined 300 have 270 authors. Every
complete text fits the existing 512-token limit. Counts refer to source posts,
not hierarchy nodes; the areas do not prescribe hierarchy branches.
[Selection, provenance and review evidence](../../sse_multivector/real-note-fine-segmentation-v1/README.md#software-selection-for-the-300-note-hierarchy)
remain separate from earlier generation results. The corrected source and
offline preparation are saved; the 300-note hierarchy has not been built.
Generation holds, open prompt/build choices and validation gates remain unchanged.

**400/500-note corpus preparation — October 2:** the user requested both
selections, then approved replacing four uncertain topic fits: one books/reading
post and three exercise/fitness posts. Those v2 corrections remain in place.
The user subsequently approved replacing the three address-based replies found
by a direct 500-event audit: software positions 19 and 62 and exercise position
85. The current 400-post reference uses software v2 and the unchanged books v2
posts; the reference-only books v3 adopts the software corrections. Exercise v3
replaces only position 85 of v2 and extends that exact 400-post source to 500.
Earlier frozen versions remain untouched. Original-text, local tokenizer, copy,
author and production input-preparation checks passed for all corrected sources.
[Books selection](../../sse_multivector/real-note-fine-segmentation-v1/README.md#books-selection-for-the-400-note-hierarchy)
and [exercise selection](../../sse_multivector/real-note-fine-segmentation-v1/README.md#exercise-selection-for-the-500-note-hierarchy)
record the corrections, retained assessments and hashes. The current event audit
reuses 497 unchanged inspections and directly inspects all three replacements;
all 500 IDs, original texts, authors, canonical event hashes and kind-1 values
match. None has an e-tag reply or mention, a q tag, or an a tag marked root/reply.
Eleven retained inline event references without q tags and five mixed-language
posts still require the previously requested policy choices; full requirements
satisfaction is not claimed. No independent semantic review or user judgment of
the replacement posts or hierarchies is claimed. Corrected source preparation
is saved; 300/400/500-note hierarchies have not been built. Generation holds,
open prompt/build choices and validation gates remain unchanged.

**Current task 02 status (October 8):** user browsing acceptance remains open.
Frontier-based and vector-space construction are both under investigation, with
separate results recorded above. Planning centers on the compare-prompt builder;
vector results do not gate progress. ASv6.100 is the approved subject baseline,
not proof of a correct global hierarchy. Relationship consistency and
construction quality remain unresolved.
The October 1 independent comparison favored the scalable subject-hierarchy
candidate (SH04); that earlier agent assessment is not acceptance or selection
of a production workflow.

The earlier
[bounded 100-post build](../../sse_multivector/bounded-hierarchy-v1/README.md#completed-build-and-browser-handoff)
completed its three scheduled passes on September 30. It reused the original
LG01 subjects, masks and vectors rather than regenerating them. The build used
522 new model attempts and two exact-request reuses, with no failed or unrun
model cases. The final browsing export contains 1,651 hierarchy nodes and 220
roots, retaining all 100 posts, 2,383 original subject entries and 1,674 masks.
Saved build records report that browser, ancestry, DAG and export-hash checks
passed. Mechanical completion does not establish semantic placement accuracy
or browsing acceptance.

The build exposed a quality problem: preserving original subject links can make
unrelated posts reachable beneath specific recipes once ingredient subjects are
combined across posts. The recipe-specific risotto ingredient entry, for
example, contains general Cooking fats and Cheese headings. The problem is
visible in the saved build, not repaired or hidden. Remaining roots and
duplicate branches also need review; the bounded selection is not complete.

The October 1 six-link diagnostic used the unchanged comparison prompt. Both
problematic risotto links returned neither contains the other, while four
controls returned parent contains child, matching pre-inference agent
expectations. This selected result does not establish corpus-wide accuracy or
a decision to filter original links. The bounded build's full original-link
check is prepared only: 1,755 comparisons in 110 batches, all unrun. Further
inference and any filtering or changed construction policy require separate
authorization; this planning update selects none.

Task 02 remains in progress until a useful 100-note hierarchy passes the user's
browsing review; finishing launch-scale construction is not this gate. Status,
track and dependencies are unchanged. No production workflow is selected.
The original LG01 hierarchy and earlier HR02/Astra tests remain unchanged as
evidence, not current next-step instructions. Task 25 stays complete for HR02.

**Task 23 dependency clarified September 29:** separate node-title generation
is required for 02 only if the chosen workflow includes that stage. Task 23
remains complete for the earlier HR02 work. While the workflow choice is open,
its link to 02 is helpful, labeled with the condition; make it required if that
stage is used. LG01 retains SP subject names instead of running the old
HDBSCAN-group naming pass. No production workflow is selected by this change.

The subject and mask prompts are finished (01 complete), confirmed by the user
on September 20. On September 24, the user confirmed that the node-title prompt
is finished (23 complete). The [frozen v38/Luna max title pass](../../sse_multivector/navigation-research-v1/README.md#current-title-prompt-experiment) has produced
valid titles for all 129 groups in the 100-note build: 108 new calls and 21
reused results. The saved HRv1 hierarchy still uses the older v21 titles.
The subsequent authorized HR02 Astra-low pass used unchanged v38 and identical
groups: 129 valid titles, 128 new calls and one reused result. Agent inspection
is complete with seven flagged cases. The user accepted `grownostr` and
`guarani`, rejected `Daily painting` and `Brands`, and approved proceeding to
TRUE with all Astra titles, retaining all nodes and flagging the two failures.
The Luna-title run is stopped with 5,092 completed answers preserved.
Task 02 resumed with the user's approval on September 25. The construction path
validated those saved v38 titles and prepared all 16,512 directed TRUE inputs.
Local Astra-title scoring completed: 12,896 fresh inputs and 1,629 reused
inputs cover all 16,512 directions. The provisional graph has 116 nodes and
56 reduced links. All six merged titles are now generated with unchanged
v38/Astra low, as subsequently approved, without changing merges or links.
The historical HRv1 runner and artifacts remain on v21. HR02 browser export
is complete. The user reviewed it and found it promising, but judged TRUE's
relationship decisions unsuitable. A frontier-call replacement was pursued as
a diagnostic for whether the other stages hold up, not as a production choice
or validation of those stages. For HR02, title-generation (23) and
TRUE-cycle-handling (25) implementation prerequisites were satisfied;
25 stays complete.
The user subsequently approved the simplified
[NSPv2 diagnostic prompt and four-pair pilot](../../sse_multivector/navigation-research-v1/README.md).
Eight Astra-low subscription calls checked both directions: all outputs were
valid and matched pre-run agent expectations, versus four of the saved TRUE
answers. This selected smoke test does not establish general accuracy or a
validated hierarchy. The user then approved eight further calls on real HR02
nodes, with judgments retained for reuse in the diagnostic. All were valid;
six matched pre-run agent expectations. Both coffee shop / coffeechain answers
assumed coffeechain meant a chain of coffee businesses; their justifications
are rejected in agent review and the intended title-only boundary remains
unresolved. No answer used the available `uncertain` option. The prompt,
settings and hierarchy are unchanged; neither batch reran earlier calls.
The user identified a title issue: this node should have retained `#coffeechain`,
not `coffeechain`. Some source masks already include the hashtag marker, so this
is not solely a masking issue. The authorized two-call test changed only this
title to `#coffeechain`, with NSPv2 / Astra low unchanged. Both valid answers
remained Yes / No and still justified them as coffee-shop business chains.
Preserving the marker did not prevent that interpretation in this draw; both
justifications are rejected in agent review. No baseline was rerun, and no
prompt, saved original title or hierarchy was changed.
The user then requested explicit social-media source context in the subsumption
prompt and approved NSPv3, which adds only "derived from social media posts"
to NSPv2's opening description. The authorized two-call Astra-low comparison
used the same hashtag titles and saved NSPv2 baseline without rerunning it.
Both outputs were valid: coffee shop contains #coffeechain changed from Yes to
Uncertain, recognizing that the hashtag alone does not establish containment.
The reverse stayed No with an unsupported coffee-shop-chain justification.
Agent review accepts the uncertainty and rejects the reverse explanation.
This is partial improvement in one draw, not resolved placement or general
validation; NSPv3 is tested, not production-frozen.
The next authorized small batch used three other original HR02 node pairs:
brisket / Brisket on a smoker, Meat consumption / Attitudes toward meat
consumption, and Good morning greetings / Early morning. Six new NSPv3 /
Astra-low calls were valid and matched the expectations recorded before
inference: Yes/No, Yes/No and No/No respectively. Agent review accepted all six
explanations; saved TRUE matched five of the six expectations. No retries,
reused calls, baseline reruns or prompt changes occurred. Original node IDs
and receipts are retained for later diagnostic reuse. This selected sample
does not establish general accuracy or graph consistency.
The user approved Luna max on the eight saved NSPv3 directions, assessing
semantics and token usage before any larger run. Both model-comparison batches
completed with eight valid new subscription calls, no retries or reuse, and no
Astra reruns. Luna matched five of the six clear pre-run expectations, missing
Meat consumption containing Attitudes toward meat consumption by treating the
parent as an action instead of a subject topic. Its reverse explanation calls
attitudes narrower, conflicting with that interpretation. The hashtag answers
remain Uncertain/No with unresolved or unsupported coffee-business-chain
reasoning. Luna remains a candidate, not an adopted relationship model.
Runner-reported output tokens (including reasoning) were 1,177 versus Astra's
331 on the six clear cases, and 961 versus 147 on the two hashtag cases; input
counts were unchanged at 562 and 184 respectively. Catalog estimates were
about 34x and 18x cheaper for Luna on these batches, not 100x cheaper per call.
These are subscription runs, not paid invoices or measured quota ratios.
The user approved testing a Luna-only wording change clarifying topic containment.
[NSP-Luna-v1](../../sse_multivector/node-subsumption-prompt-luna-v1/prompt.txt)
is tested, not adopted. It is scoped to
`gpt-6-luna` / `max`; do not use it for Astra. Astra retains unchanged NSPv3.
The eight-call comparison used saved Luna/NSPv3 answers without rerunning them.
All outputs were valid, with no retries or reuse. Five of six clear expectations
still matched: the meat-consumption miss and conflicting reverse explanation
persisted. Coffee shop containing #coffeechain regressed from Uncertain to Yes,
asserting a coffee-business-chain meaning; the reverse stayed No with the same
unsupported interpretation. The intended hashtag boundary remains unresolved.
This draw provides no semantic improvement supporting adoption of NSP-Luna-v1;
it does not establish Luna's general accuracy. Prompts and hierarchy are unchanged.
The user then approved a small fresh-pair check with unchanged NSPv3 / Luna max.
Six previously untested HR02 pairs were checked in both directions, covering
cuisine, exercise, psychology, enjoyment of food, temporal overlap and related
coffee topics. All 12 decisions matched agent expectations recorded before
inference, including Food and drink containing Enjoyment of food. All calls
were valid and new, with no retries, reuse, baseline reruns or Astra calls.
One explanation loosely called Early morning broader than Morning coffee,
although both directions correctly rejected containment. The fresh sample is
encouraging, not a general accuracy estimate or resolution of earlier failures.
No prompt or model is production-adopted by this result.
The user deferred the proposed connected-hierarchy test. Discussion of harder
pairs exposed title-interpretation ambiguity; those proposed expectations are
not agreed ground truth. After reviewing the TPv38-inspired NSP-Luna-v2 draft,
the user requested a task-specific rewrite rather than transplanted title rules.
[NSP-Luna-v3](../../sse_multivector/node-subsumption-prompt-luna-v3/prompt.txt)
asks: would every post about B also be
about A? It adds an uncertainty condition when title meanings do not establish
the answer, retaining the output contract. It is approved and tested, not frozen,
and only for
`gpt-6-luna` / `max`, not Astra. NSP-Luna-v2 remains a superseded, untested
draft; TPv38, NSPv3 and saved results are unchanged.
The authorized comparison checked the 20 existing Luna cases against saved
NSPv3 answers, with no baseline reruns. All 20 new calls validated without
retries or reuse. All 18 clear expectations matched, versus 17 in the saved
NSPv3 results: Meat consumption containing Attitudes toward meat consumption
changed to Yes with a consistent reverse No explanation. The two hashtag
directions remain Uncertain/No with unresolved or unsupported business-chain
reasoning. This is a single-draw improvement on reused cases, not general
validation. No harder-pair tests or connected-hierarchy work were performed.
The user then approved testing `typesafe/jev-1.13` through OpenRouter and
adding its separate System One transport to the shared runner. 
[NSP-Jev-v1](../../sse_multivector/node-subsumption-prompt-jev-v1/prompt.txt)
preserves NSP-Luna-v3's containment question and exact title inputs, replacing
generated JSON/reasons with native Yes/No/Uncertain Choice answers. It is
tested, not frozen or adopted. Twenty new calls completed with valid receipts,
no retries, reuse or baseline calls. Jev matched 17/18 previously recorded
clear expectations, versus saved Luna's 18/18; it rejected Psychology and
philosophy containing Psychological distress. Both hashtag directions were
No but remain unscored because their expectations are unresolved. Jev does
not explain its decisions; probability values do not establish calibration
or identify its interpretation of a title. The sample is reused and small.
The original prompts, hierarchy and construction rules remain unchanged.
The user approved a small harder sample with unchanged NSP-Jev-v1. Thirteen
new judgments covered six original HR02 title pairs in both directions plus
one identical Foods-title control. Nine expectations were recorded by the
agent before inference; four directions involving Christmas/Festive gatherings
and Food and cooking/Food and dining remained explicitly unscored. Jev matched
8/9 expectations, rejecting Food and drink containing Fasting (No 0.88 versus
the intended topic-containment Yes). On unresolved pairs it placed Christmas
under Festive gatherings, rejected the reverse, and rejected both directions
between the two food-topic titles. These are not user-approved relationships.
All 13 calls were valid without retries, reuse or baseline calls; native charge
was $0.000206136. No prompt or hierarchy change followed. Comparing Luna on
this sample was suggested but not run. The user subsequently accepted Jev's
No for Food and drink containing Fasting, correcting the agent's expected
boundary. With that human correction all nine scored judgments match the
current expectations; this does not make the other agent labels user-approved.
Four scope ambiguities remain unresolved. The user approved instead a small
connected Jev section in the existing hierarchy UI: nine original food/cooking,
cuisine and bread nodes, all 72 directed pairs, unchanged NSP-Jev-v1 and no
membership expansion. Every selected node is retained; this is a selected
diagnostic, not the complete food hierarchy or a full HR02 run. Cycles are
reported without silently deleting links or merging nodes.
The approved v1 section was built: 72 valid decisions (70 new calls and two
reused), 20 Yes links reduced to 11, one root and no cycles or Uncertain answers.
One rejected relationship is nevertheless reachable: Food and drink → Cooking
was No, while Food and drink → Food and cooking → Cooking was accepted. No
repair was applied. All nine nodes and original memberships are visible in the
existing viewer, whose check passed. Native charge was $0.001113504.
The user then approved NSP-Jev-v3 and its same-section comparison. All 72 new
calls validated without retries or baseline reruns ($0.001269072 native charge).
Four choices changed from Yes to No: Food and drink → Food and cooking, and
Cooking → Chinese cuisine / sourdough bread / Cranberry and rosemary bread.
The graph now has 16 raw links, 10 reduced links, two roots, no cycles and no
rejected-but-reachable pairs. Food and drink → Cooking remains No: the original
contradiction disappeared by removing a link, not accepting that relationship.
Consistency does not establish semantic improvement. All original nodes and
memberships are retained, and the v3 viewer check passed. The user subsequently
rejected using the assembled hierarchy to validate Jev's prompt. The approved
next direction is pairwise validation first: agree on expected answers for a
small set of actual node-title pairs, keep disputed labels separate, then test
the prompt with repetitions before returning to hierarchy evaluation. The
candidate pairs in the navigation research README were checked against saved
titles, and the user confirmed all proposed labels. The repeated test completed
with unchanged NSP-Jev-v3: 17 unique inputs, three observations each, two saved
v3 answers reused and 49 new valid calls, without retries. Each trial matched
16/17 labels. Meat consumption → Attitudes toward meat consumption was the
sole failure, returning No in all three trials against the agreed Yes. All
17 inputs retained their choices across repetitions; this is selected-sample
consistency, not general accuracy. The identical Foods/Foods directions count
as one input. Disputed labels remain separate and unscored. No prompt change
or hierarchy construction followed. The user rejected further investigation
of that single miss and approved a fresh balanced sample instead. The completed
test has twelve previously untested directions, six expected Yes and six No,
across art, emotions, cooking and coffee, with unchanged NSP-Jev-v3 and one
initial call per input. Expectations are recorded by the agent before inference,
not represented as new user approvals. The Daily painting label assumes its
ordinary artistic meaning; this assumption was disclosed before inference.
All twelve new calls validated without retries, reuse or baseline reruns.
Jev matched four of six expected Yes and all six expected No. It rejected
Coffee → Coffee flavor and Positive emotions and attitudes → Enjoyment of food.
The two discrepancies are against agent expectations, not newly user-confirmed
ground truth; Daily painting remains explicitly conditional. Cooking ideas and
Cooking times were accepted beneath Cooking, so this does not demonstrate a
blanket inability to recognize topic aspects. Those labels remain unresolved;
the user then approved proceeding with all 16,512 directional judgments across
the same 129 original nodes, using unchanged NSP-Jev-v3 and Jev provider-default
at ten concurrent calls. The completed experiment is
`sse_multivector/experiments/nsp-jev-v3-hr02-full-v1/`; preparation found 100
matching saved answers to reuse and 16,412 initially new requests. Execution
completed all 16,512 judgments: 14,426 new calls and 2,086 exact-request reuses,
including matches becoming available during the run. No calls failed or needed
retry; every response passed format and receipt checks. Native choices were
241 Yes, 16,271 No and zero uncertain; these are not accuracy measurements.
Native cost was $0.253775508. Runtime including local reporting was 45 minutes 25 seconds.
All original Astra-low TPv38 titles and upstream artifacts remain unchanged. Every answer,
probability and uncertainty is retained; uncertainty is not a No. The user
subsequently approved constructing the Jev hierarchy using the existing
provisional merge, naming and navigation rules. The reversible merge kernel
now accepts receipt-validated Jev decisions without fabricating TRUE scores;
HD01 uses native Jev Yes, while HD02–05 stay unchanged. The five cycle groups
involve repeated morning-greetings, Bitcoin, Nostr, Coffee and Foods titles.
Merged names used the existing v38/Astra-low workflow with reuse enabled:
five new valid subscription calls, no retries, produced Bitcoin, coffee,
nostr, Foods and Good morning greetings. The completed separate browser is
`target/hierarchy-build-v1/hr02-jev-browser-v1/`: 118 hierarchy nodes, 84 reduced
links, 52 roots and 98 represented posts. All 129 original nodes, 629 source
masks and 16,512 decisions remain traceable; the 27 rejected-but-reachable
pairs were recorded, not repaired. Naming preserved links and reachability.
The viewer passed `--check` and interactive leaf-note/O-view checks with the
existing equal-note navigation collapse. Saved TRUE artifacts are unchanged.
This is ready for user quality review, not a validated hierarchy or production
adoption. Scalable relationship inference and downstream gates remain open.

**HR02 placement diagnostic (approved September 26):** use Jev as the initial
node-placement solution, then correct its failures by hand in a separate
hierarchy so the other stages can be evaluated without placement errors
obscuring them. Preserve the untouched Jev baseline. Keep the same nodes,
titles and memberships; record every changed relationship reversibly, without
quietly repairing other stages. The user's “90% / 10%” framing is not a
measured accuracy claim. The 118-node parent audit is an agent assessment,
not approval of its proposed corrections. Review those proposals and unresolved
boundaries with the user before applying agreed corrections. The corrected
hierarchy is not built or validated yet. This does not adopt Jev/manual repair
as the scalable production method or authorize additional inference.

Approved placement decisions for that separate hierarchy (changes not yet applied):

| Parent | Child | User decision |
| --- | --- | --- |
| Eggs | Duck eggs | Add. The visible path becomes Foods → Eggs → Duck eggs; the direct Foods → Duck eggs shortcut becomes redundant. The Jev baseline remains unchanged. |
| coffee | Coffee beans | Add while retaining the existing Seeds and seed-derived products parent. Coffee beans will have both parents in the corrected hierarchy. The Jev baseline remains unchanged. |
| coffee | Coffee flavor | Add as the more-specific parent. Food and drink remains an ancestor; its direct Coffee flavor shortcut becomes redundant. The Jev baseline remains unchanged. |
| Foods | Clean, simple dishes | Add. The currently parentless node describes prepared food, not tableware, as supported by its dinner/dish masks. The Jev baseline remains unchanged. |
| Positive emotions and attitudes | Enjoyment of food | Add. Enjoyment denotes pleasure or satisfaction, so the child necessarily concerns a positive experience; the post need not itself express a positive emotion. The Jev baseline remains unchanged. |
| Food and drink | Enjoyment of food | Add alongside Positive emotions and attitudes. Discussing enjoyment of food necessarily concerns food. Both parents are approved for the corrected hierarchy; the Jev baseline remains unchanged. |
| Art | Music | Add. Music is an art form; the parent is Art, not Visual art. The currently parentless Music node gains this parent in the corrected hierarchy only. |
| Cooking | crockpot | Add. A crockpot is a cooking appliance, so it falls within the cooking topic; this is topic containment, not treating an appliance as an action. The Jev baseline remains unchanged. |
| Psychology and philosophy | Psychological distress | Add. Psychological distress falls within the psychology side of this parent; the masks express unhealthy stress and anxiety. The Jev baseline remains unchanged. |
| Personal habit changes | Fasting | Remove. Fasting can be an established practice rather than a change of habits, so containment is not necessary. Leave Fasting parentless for now in the corrected hierarchy; the Jev baseline remains unchanged. |
| Meat consumption | Chickens and chicken products | Remove. The child includes living hens and egg-laying, which do not necessarily concern meat consumption. Retain its existing Animals parent for now; the Jev baseline remains unchanged. |
| Meat consumption | Attitudes toward meat consumption | Add. The user reconfirmed carrying the previously approved relationship into this corrected hierarchy: discussing attitudes toward eating meat necessarily concerns meat consumption. The Jev baseline remains unchanged. |
| Foods | coffee | Remove. The user agreed to interpret Foods as excluding drinks. Its already-accepted Food and drink relationship becomes the direct displayed parent, alongside tea and Wine. Other affected placements still require review; the Jev baseline remains unchanged. |
| Foods | milk | Remove under the agreed food/drink distinction. Its already-accepted Food and drink relationship becomes the direct displayed parent. Retain milk → raw milk. The Jev baseline remains unchanged. |
| Raw food | raw milk | Remove under the agreed food/drink distinction, avoiding the remaining Foods → Raw food → raw milk path. Keep milk → raw milk. The Jev baseline remains unchanged. |
| Foods | Cream | Keep. The masks describe cream as a food ingredient, including when added to coffee, rather than a separate drink. No change to this baseline link is needed. |
| Foods | Ice and ice cream | Remove. The group also contains ice used to serve iced coffee; retain the already-accepted Food and drink parent to cover the whole group without treating ice itself as food. Keep the node intact and the Jev baseline unchanged. |
| Foods | Meat consumption | Keep. Discussing eating meat necessarily concerns food. The hierarchy organizes topics, so the child need not name a food item rather than an activity. No change to this baseline link is needed. |
| Meat consumption | Beef | Remove. Discussing beef, such as its cuts or storage, does not necessarily discuss eating it. Retain Beef's Meat and animal fat products parent. The Jev baseline remains unchanged. |

**Scoring scope clarified September 30; priority revised October 5:** **04 · Define node sort score**
defines and validates one sorting score per note within a hierarchy node,
including its inputs and output format. **27 · Order notes within each node**
implements and validates ordering using that definition. Prominence may be a
component, but is not the task's required end state. The sorting mechanism is
still being developed; whether teachers or the distilled model need prominence
or other additional outputs is undecided. Existing prominence experiments and
frozen informal-pilot settings are unchanged; no production method is adopted.
Both tasks are now paused as nice-to-have work. The user clarified that the
deferral applies to node sorting, not just prominence. The proposed ordering
of hierarchy work and the SP pilot was subsequently clarified as tentative,
not a fixed ranking. The pilot informs later fine-tuning; SHR fine-tuning still
depends on validation in a generated hierarchy. Sorting no longer gates hierarchy
validation, teacher selection, pilot training data or release. Retain 04 → 27
within the optional effort, change 27 → 03 to helpful, and remove 04 → 05 and
04 → 17. The saved
candidate and review evidence remain intact; when to resume sorting is open.
The user labels GPT-6.1 Sol low as the provisional favorite for SP
(subject generation), and GPT-6.1 Sol medium as the provisional favorite for
grouped masks (one call for all subjects in a post). These are provisional
preferences, not final teacher selection. Completed subject and fixed-subject
mask comparisons are summarized in the
[teacher-comparison evaluation plan](#teacher-comparison-pilot-evaluation-plan).
The combined Sol subject-and-mask process and resulting hierarchy comparison
remain unvalidated. Final teacher selection remains open.
Frozen ASv6.48 and production model settings are unchanged; Sol's subscription
quota consumption remains unmeasured. Task 17 stays in progress.
Dates are unchanged. The additional construction dependencies below expose
unfinished work. Completing 01 and 23 does not complete the hierarchy. This
records work and planning requirements, not authorization to start another
workstream or approval of the overall plan.

### Status checkpoint — September 25

Tasks 02, 18, 22 and 25 were updated on September 25; 23 on September 24.
Other rows were last confirmed with the user on September 23.
This is a dated checkpoint; current task status appears in `release-plan.json`.

| Task | Status at checkpoint |
| --- | --- |
| 01 · Subject and mask prompts | Finished. |
| 02 · Build and review 100-note hierarchy | In progress; HR02 was generated and reviewed. Promising, but TRUE's relationship decisions prevent validation. Frontier replacement is the next diagnostic; task 25's implementation gate is satisfied. |
| 23 · Fix and validate node-title prompt | Finished; 129 titles saved. |
| 04 · Define mask prominence | Paused. Earlier experimental results do not establish that work is active now. |
| 17 · Compare teachers | In progress; no completed selection established. |
| 26 · Collapse equal-note navigation steps | Implemented and regression-tested; validation on the rebuilt hierarchy is waiting. |
| 13 · Define Nostr hierarchy protocol | Not started. |
| 18 · Prepare training code for the fine-tuning pilot | Candidate recipes and Vast limits frozen locally; VM tests training and SSH deployment. Image published and verified; the September 29 run stopped after an agent monitoring error. Retrieval/deletion verified; no baseline or training completed. |
| 24 · Recover missing node memberships | Not started. |
| 25 · Handle node equivalence and TRUE cycles | Complete for HR02: exact-mask consolidation and reversible cycle handling are implemented and tested, with naming/browser integration. The merge rules remain provisional; hierarchy-quality review belongs to 02. |
| 21 · Assess HDBSCAN at launch scale | No further progress; earlier investigation remains evidence, not launch-scale validation. |
| 22 · Measure SSE, node-title and relationship-check costs | No further progress; TRUE timing remains baseline evidence, not an assumed launch method. |

This checkpoint records HR02-era statuses, not current prerequisites.
The HR02 finish dependency 25 → 02 has since been removed from the task graph.
Green cards identify work ready now, not work currently underway.

## Vocabulary

Naming approved by the user on September 21, 2026:

| Name | Meaning |
| --- | --- |
| **teachers** | The models that write the training data by running the prompts. More than one teacher is allowed. Replaces "annotation model", "training-data generator" and "annotator". |
| **the distilled model** | Takes a complete note and returns its masks. Any additional outputs needed for note sorting remain undecided. Trained in 06/08 and released in 16. Replaces "extractor", "fine-tuned model", "mask/prominence model", "embedding model" and "student". |
| **hierarchy node** | A grouping of masks that appears in the hierarchy. Replaces "category", "fine subject" and "segment"; compounds use "node": node titles, node descriptions, node links, node-note ordering. |
| subjects, masks, prominence | Unchanged. The older "takeaway" and "relevance" wording is retired. |
| **pilot training data** (05) and **full training data** (07) | Always qualify; avoid bare "training data". |

Task titles approved with this vocabulary: 17 · Compare teachers; 05 · Prepare
pilot training data; 06 · Choose model through larger fine-tuning pilot; 07 · Generate full training
data; 08 · Distill and package the model; 11 · Test hierarchy with the distilled
model; titles using "category" use "node" (22, 23, 24, 25, 27). This record uses
the new names. Task 29 separately tracks the preliminary 100-note fine-tuning
experiment; the retired diagram is recoverable from Git. Frozen
experiment and research evidence keeps the wording of its time.

Terminology clarified by the user on September 30, 2026:

- **Mask:** only the exact original-post fragments selected according to the
  mask prompt (MP) for one supplied subject.
- **Subject vector:** SSE's encoding of SP subject wording by itself; not a
  mask selected by MP.
- **Mask vector:** SSE's encoding using an MP mask in its original post context.

Use these names in current descriptions and explanations. This clarification
does not change the algorithm, prompts, vector generation or saved identifiers;
original transcript quotations and frozen evidence remain unchanged.

## Agreed release goal

By October 18, 2026 — a date the user declared non-negotiable — release **the
release**, the only must-deliver package:

- A genuinely useful, fully automated hierarchy snapshot for discovering Nostr
  content, built without manual repair and judged by the user's browsing review.
  The corpus-size target is 2,000–5,000 notes, not a minimum.
- The full hierarchy-generation architecture and code.
- Tested service code and instructions for serving the snapshot over the custom
  Nostr protocol locally. Operating public infrastructure is not required.
- Notedeck browsing integration, delivered as a branch published on the user's
  fork and verified against a locally served snapshot.
- A roadmap to scalability: the fine-tuning path for replacing the expensive
  teacher calls at larger corpus sizes.

**Corpus size revised October 8:** 2,000–5,000 notes is a target, not a hard
minimum. Ship the largest hierarchy that is genuinely useful and passes the
user's review within the remaining time. The October 18 deadline, quality,
automation and other deliverables remain unchanged. The exact size remains
open; this decision does not remove the existing validation milestones.

**Publication clarified October 8:** publish the final hierarchy's Nostr events
either to a paid relay or in a ZIP posted online. The user will choose based on
the hierarchy's quality; no route or quality threshold is settled. Notedeck
integration remains required with either route. This changes distribution
options, not the deadline, other deliverables or spending authorization.

Two optional tiers accompany the release:

- **The model track** (nice-to-have, not a bare necessity): the open-weight
  distilled model with usage docs, published whenever it passes its quality
  gate (08 + 11), inside or after the release window.
- **The hosted demo** (cherry on top): we operate the service ourselves, only
  if everything else lands.

A static launch snapshot is acceptable. Continual updates are not required for
launch, but the release documentation must describe a path to supporting them.
Agents write the code; the user directs their work and reviews results rather
than coding personally. The user can oversee overlapping efforts while agents
are working, though parallel capacity is not unlimited or quantified. Individual
agent assignments remain open.

### Release-shape revision — September 28, 2026

As the schedule slipped, the user re-cut the release shape on September 27–28:
the date is fixed and the process must stay automated, so scope — not quality
or automation — is the flexible knob. The names **the release**, **the model
track** and **the hosted demo** replace the informal “Plan A / Plan B” wording.
The release is the default path and always ships its snapshot; the model track
is additive, never a replacement. The earlier goal listed an open-weight
distilled model and an operated public service as launch deliverables; the
model is now an optional tier and operating infrastructure is no longer
required at all.

The corpus decision is a proof of concept: an actually good, fully automated
hierarchy demonstrates a correct process at small scale, targeting 2–5k notes
without making that a minimum. The roadmap to scalability names fine-tuning
models for the expensive steps as the credible next step toward larger corpora.
The user's browsing review
remains the acceptance bar. Teacher selection (17) stays on the release path
because teachers label the release corpus. Node sorting (04 and 27) is deferred
as nice-to-have work and is not a release or training prerequisite. Its mechanism
and any additional teacher outputs remain undecided; existing experiments are
preserved for later use.

The model-track quality gate requires acceptable masks and any agreed additional
outputs on unseen notes (08), plus a hierarchy that passes the user's browsing
review (11); “training ran” does not pass. The
September 27 training-data readiness target belongs to the model track and no
longer constrains the release. The validation ladder is kept and extended —
200 / 300 / 500 as approved, then a ~1–2k-note review rung, then the release
build — because each rung gives diagnostic reference points when a larger build
misbehaves, and the release build must not be an uninstrumented
jump in scale. The dependency graph follows: the release build (12) now takes
its inputs from the validated workflow (03), the validated launch-scale
implementation (28), the frozen corpus (09) and the selected teachers (17).
The distilled-model checks (10, 11) gate the model track instead of the release.

## Corpus scope and size

The launch is intended to cover subjects broadly, not a fixed list of topics.
Include English kind-1 top-level posts; exclude replies and quote posts.

The corpus must be large enough to plausibly provide useful content discovery.
More than one million notes was an initial estimate, not a fixed acceptance
threshold. Breadth and depth of useful coverage matter; raw note count does not
establish either. The final processed count and exact subset remain open.

Use the existing corpus as the starting point. Processing the whole candidate
pool is not committed, and additional collection is not currently a prerequisite.
Reconsider collection if a demonstrated coverage gap warrants it.

**Release corpus (PoC, revised October 8, 2026):** 2,000–5,000 notes is a
target, not a hard minimum. Ship the largest genuinely useful hierarchy that
passes the user's review by October 18, without relaxing quality or automation.
The proof of concept demonstrates a correct automated process at small corpus
size — an actually good hierarchy is the
deliverable, not note count — and the roadmap to scalability covers larger
corpora. The exact size and subset remain open and are frozen by task 09.

### Data already available

These are saved artifact counts, not claims of manually verified English or
adequate subject coverage:

| Collection or filtering stage | Available records |
| --- | ---: |
| Nine-relay acquisition, September 24, 2025–July 24, 2026; kind 1 before filtering | 15,782,558 |
| After root/non-quote and length filtering | 11,595,958 |
| After exact-content deduplication | 9,108,872 |
| After English-or-language-neutral classification | 3,774,156 |
| Same pool with usable text; source of the frozen 1,000-note sample | 3,510,335 |
| Separate older April 2025 Damus archive's English-or-language-neutral pool | 3,530,470 |

The current pool already excludes replies and quote posts. It also carries a
512-token ceiling from earlier embedding-model experiments, and its language
filter accepts language-neutral content and can make classification mistakes.
Those existing filter policies are not newly approved release requirements.
Do not add the older and newer counts together as a verified combined corpus.

Sources: [acquisition and derivation receipts](../../../damus_snapshot/runs/crec-105-fresh-corpus-v9/derivation/derivation-ledger.json),
[deduplication](../../../damus_snapshot/runs/crec-105-fresh-corpus-v9/publication/10m-adcf8f016f6a-v1/global-deduplicated/manifest.json),
[language filtering](../../../damus_snapshot/runs/crec-105-fresh-corpus-v9/publication/10m-adcf8f016f6a-v1/english-eligible/manifest.json),
[usable-text sample provenance](../../semantic_map/crec-120-sample-v1/manifest.json),
[older pool](../../../damus_snapshot/runs/crec-9-complete-cpu-audit-v6/work/english-eligible/manifest.json).

## What the hierarchy runs must validate

Judge complete browsing paths: do nodes offer understandable choices,
narrow meaningfully, and lead to relevant notes? Occasional errors can be
acceptable; repeatedly misleading navigation cannot. Concrete examples from
the builds should inform acceptance, not an invented accuracy percentage.

The 100-note work tests hierarchy correctness at minimal scope and must
establish an initial useful hierarchy; HR02 has not yet met that gate. The
planned 200-note / 2-topic build checks
correctness across more topics. Node sorting is optional and deferred, not a
completion condition for any rung. The 300-note / 3-topic
build checks correctness while testing scalable construction choices; candidate-pair
filtering must preserve useful parent–child links, not just reduce relationship
checks.
The 500-note / 5-topic build checks the combined pipeline and profiles build
time and memory to find bottlenecks. All three increase subject coverage; none
is merely a test of handling more notes. The ladder extends past 500: a
~1–2k-note rung with full user review precedes the release build (see the
release-shape revision above), so the release build is never an uninstrumented
jump in scale.

**Task ownership clarified September 29:** task 03 covers the 200 / 300 / 500
validation runs and the ~1–2k-note user-review rung. Task 12 alone owns the
final teacher-labeled, fully automated release build and its user browsing review.
Completing 03 does not accept the final release snapshot; completing 12 requires
the user's acceptance of that snapshot. The full ladder and existing dependency
arrows are unchanged.

Runtime, memory and million-note processing cost still require separate
measurements. Profiling 500 notes does not establish launch-scale feasibility.

The [fine-tuning pilot](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md)
must measure unseen-note subject correctness, coverage and hierarchy quality
before and after training, improvement with more training data, actual training
resources and cost, and
batched generation speed on representative notes. Compare quality against total
training-and-generation cost. This does not estimate the other hierarchy-build
stages or approve a dataset size, hardware rental or spending allocation.

## Two separate model pilots

**October 2 larger-pilot scope approved:** the user removed masks from this
pilot. Train and evaluate subjects and their hierarchy only: one teacher
subject-hierarchy example per note and one generated subject response per
evaluation note. Keep the three students, one complete 1,000-note pass,
200/400/600/800/1,000-note checkpoints, approved numerical recipe, merged
evaluation/resume lifecycle. Thinking stays off throughout the pilot, as
subsequently approved below. Eight examples
per update give **125 updates per student, 25 per block**. The proposed 100
validation and 200 final test counts were subsequently approved, along with the
$285 combined rental budget below. The GPU choice is recorded below.
This pilot supplies subject evidence for model selection; it cannot establish
mask quality or downstream mask/SSE hierarchy quality. The completed combined
preliminary experiment and the eventual release task retain their own scope.

**October 5 two-GPU execution approved:** implement and test concurrent execution
locally. Keep each complete student on one **96GB RTX PRO 6000**: GPU 0 runs
Gemma dense; GPU 1 runs Qwen followed by Gemma MoE. The paired prep→pilot flow
uses the same rental, with all three prep results and all three baselines verified
before any main training. Preserve the subjects-only scope, one continuing pass,
training recipe, dynamic per-GPU batching and 1,000/100/200 splits. GPU assignment
is frozen in the package; independent subprocesses receive separate CUDA device
bindings. A failed candidate blocks queued work while other active work finishes
and is preserved. Explicit stopping reaches both workers. No automatic timeout,
budget kill or deletion. The user subsequently approved private image publication
and **up to $285** for the combined two-GPU prep→pilot rental. Select compatible
96GB/600 W RTX PRO 6000 Server cards within the frozen $3.10/hour ceiling. Actual
GPU fit/timing and local semantic grading remain pending.

**October 2 dynamic subject evaluation batching approved:** before each batch,
tokenize waiting notes and choose their count from a frozen per-GPU memory
budget. Account for resident weights, padding, caches/state through the full
allowed output length, temporary buffers and headroom; free memory at the start
alone does not account for answers growing. Short notes can form larger batches
and long notes smaller ones. Freeze a batching policy per student and generation
mode and apply it to its untuned baseline and trained checkpoints. Preserve
separate note identities, raw/parsed answers and immediate response accounting.
Prepare the conservative calculation locally under the actual model placement.
The existing preparation run confirms the packaged path and measures
throughput; it is not a separate search for a batch size that happens to fit.
Numeric GPU allowances remain open. The user subsequently authorized local
implementation and VM verification. The worker now supports optional
subjects-only evaluation and memory-based grouping for one complete model on
one device. It saves a frozen plan, batch receipts and separate raw/parsed
answers; partial publication resumes from a saved receipt without regenerating,
while an unfinished generation attempt blocks an automatic retry. The training
and checkpoint implementation is recorded below.
Local verification passed 24 host checks and 39 VM tests, including all three
candidate architectures and shared SSH deployment/retrieval; the VM is stopped.
Physical training groups may also vary while preserving the approved eight
examples per update, example order and supervised-token loss normalization. The old single-note
timing estimate is a serial reference; batched pilot pricing needs throughput
evidence and cannot be obtained by simply dividing that estimate by batch size.

**Planning split approved September 29:** track the preliminary 100-note
fine-tuning experiment separately as **29 · Run preliminary 100-note fine-tuning
experiment**, in progress. It uses 80 training notes and 20 evaluation notes,
existing subject/mask annotations and no prominence. **06 · Choose model through
larger fine-tuning pilot** remains waiting for the larger pilot's data (05);
training setup (18) is complete for the preliminary experiment. The larger pilot
includes a comparison trained
on 1,000 notes, approved September 30; remaining data choices are open. Task 05 prepares the
larger pilot's data, not 29's already-prepared data. Tasks 01 and 18 are required
inputs to 29; 29's findings are helpful inputs to 06 and the optional
model-track estimates in 20, not new completion gates. The split does not change
either experiment's requirements, settings or spending approvals, select a
model, or block the required teacher-built release on either pilot.

**September 30 pilot-process clarification:** the user requested a
[process walkthrough](fine-tuning-pilot-process.md) to participate in the whole
experiment's design. That role does not assign the user example labeling or
semantic adjudication. Working prompts may be used before production wording
is final; their chosen versions remain fixed within a comparison.

Validation belongs throughout execution: check responses when they arrive and
baseline coverage before training. Missing calls and parsing failures must be
visible at those stages, well before retrieval or deletion. Current parsing
records note failures and can finish with missing mask calls; stronger reporting
and stage progression checks are intended changes, not implemented by this record.
Semantic review of saved results happens from the local workspace after retrieval,
without an active GPU rental. The proposed teacher reviewer performs evaluation;
its judgments are not automatically training labels or weight updates.
**Review structure approved September 30:** one prompt per note and model
version sees the full note, task prompt, subjects and hierarchy. It
returns separate **correctness** and **coverage** scores with evidence for each.
Correctness assesses returned subjects and relationships; coverage
assesses missing required subjects or information. Output reliability is
checked mechanically. At that point, the scoring scale, rubric, reviewer model,
reliability checks and model selection rule remained design choices. The primary comparison's
checkpoint is fixed by the October 5 decision below. The user deferred
review-prompt and grading details while the overall pilot pipeline is designed.
The walkthrough also keeps remaining data choices, remaining output format details,
remaining training settings, continuation rules, and new spending open. It authorizes no
new code changes, model calls, or rental.

**Semantic review method agreed October 7:** assume the audited ASv6.100 standard
is correct and use existing teacher answers as the coverage reference. The user
selected **GPT-6.1 Sol / xhigh**: if it cannot review reliably, rethink the
approach before bulk review. Review one answer in a fresh context with the full
post/task/reference, mechanical exact matches and no model/checkpoint identity.
Record explicit subject and incoming-link verdicts, full-meaning matches and all
required compatible placements. Code calculates separate correctness and
coverage fractions, averaging notes equally. Optional derived headings are not
mandatory; different valid wording and hierarchy are allowed. Invalid/truncated
outputs and empty answers to required tasks receive zeros; correct empty answers
pass. Missing or incomplete reviewer judgments remain ungraded evaluation failures.
Compare final validation versions primarily, retaining learning curves, failures,
speed/cost and paired uncertainty; freeze decisions before test unsealing.
The user authorized drafting [DSRv1](../../sse_multivector/distillation-review-v1/README.md):
review prompt, structured report and known-result qualification cases including
a full-size hierarchy. DSRv1 remains a draft. At that checkpoint, application
implementation and actual qualification were pending. This decision does not authorize model calls,
pilot semantic grading, test unsealing, extra spending or a teacher audit.

**DSRv1 offline implementation authorized October 7:** after receiving the draft,
the user authorized preparation, report validation and scoring, requesting a
concrete preview before any model calls. The shared experiment workflow now
prepares source-bound qualification definitions, keeps expected findings
outside the prompt, validates complete reports and calculates separate scores.
It checks known qualification findings and consistent teacher groups across
versions, including controlled changes to the large hierarchy. An authored Q17
report demonstrates `9/9` correctness and `1/2` coverage when the Cumin branch
copy is absent. This supplied fixture creates no model receipt or qualification
evidence. At that checkpoint, actual qualification and bulk grading had not run.

**Largest-generation stress preparation authorized October 7:** the user
requested the largest saved generations from the 1,300-note ASv6.100 data as
stress tests. Offline sizing checks all labels and frozen split assignments.
The union of the top five training answers by entry count and canonical JSON
length contains eight notes, including the overall maxima of 145 entries and
35,966 UTF-8 answer bytes. Q20 already covers one; Q23–Q29 add seven complete
unchanged hierarchies, taking DSRv1 to 29 cases. Held-out labels contribute
aggregate sizes only; no final-test content enters development inputs. The
new cases test completion and mechanical consistency without invented gold
scores; existing known-result controls test semantic behavior. At that checkpoint,
Sol / xhigh capability was untested and the requested preview still preceded calls.

**DSRv1 qualification authorized October 8:** after the prepared preview and
largest-generation selection, the user directed proceeding with Sol / xhigh
qualification on the 29-case set. The initial attempt preserved 29 HTTP 400
rejection receipts and produced no review text. A separately frozen experiment
removes unsupported `uniqueItems` from the provider schema while production
validation still rejects duplicate references. DSRv1's rendered inputs, semantic
method, model and reasoning effort are unchanged. This request repair is not a
semantic reviewer failure. Corrected requests subsequently generated complete
large reports, but qualification failed: Q04 disagrees with a trusted unchanged
worked example, and Q21/Q22 change unrelated requirement flags and placement
judgments across variants; Q21 also changes an untouched link verdict.
Q23 preserves a transport-interrupted, ungraded report near fifteen minutes.
All 29 cases were attempted once, yielding 28 complete reports and one interrupted
report. Seven of the eight largest generations completed. See the [DSRv1 qualification evidence](../../sse_multivector/distillation-review-v1/README.md#october-8-qualification-evidence).
Bulk grading, teacher auditing, test unsealing, process revisions and a different
model remain outside this authorization.

**DSRv1 concurrency directed October 8:** use **8**, with the existing provider
exponential backoff. The initial qualification experiment was frozen at 1;
only its final request remained in flight when the user directed the change.
Preserve its original settings and receipts. The maintained specification uses
8 for subsequent preparations; no repeated reviews are needed to change this
execution setting.

**DSRv2 draft and preview authorized October 8:** after read-only diagnosis of
the coverage failures, the user directed preparing the proposed wording and
inputs before further model calls. [DSRv2](../../sse_multivector/distillation-review-v1/prompt-v2.md)
clarifies that ASv6.100's worked examples are authoritative applications of its
rules; the standard and five review steps remain unchanged. Q20–Q22 share the
original Q20 receipt's 66 meaning groups and 44 required flags. Those groups
are provisional consistency inputs, not accepted pilot classifications or gold
subject/link verdicts. The shared preparation adapter verifies the saved receipt
and exact task/post/teacher binding instead of copying generated artifacts by
hand. All 29 cases are prepared with zero model calls, Sol / xhigh and concurrency
8. At this stage, DSRv1 remains failed and DSRv2 is untested. This authorizes
offline preparation, not calls, bulk grading, teacher auditing or test unsealing. The
[DSRv2 preview](../../sse_multivector/distillation-review-v1/README.md#dsrv2-draft-and-offline-preview)
shows the wording and inputs; qualification and adoption remain open.

**DSRv2 qualification authorized October 8:** after receiving the testing
sequence, the user directed proceeding with real Sol / xhigh calls. Check the
trusted URL control first, then the remaining small known controls, then all
eight large training hierarchies and Q21/Q22's controlled variants. Use
concurrency 8 and existing provider backoff. Check individual findings and
reasons, not only scores; incomplete reports remain ungraded failures.
Q04's first call passes all eight subjects, four links and both required meanings,
with `8/8` correctness and `2/2` coverage. The extra Identifiers placement is
absent and both meanings remain required. The small set finishes with 17 passes,
Q14's semantic regression and Q01's ungraded stream interruption. Q14 correctly
finds lost coverage and two bad links but also marks four supported shortened
subjects incorrect, yielding `6/10` correctness instead of `8/10`. Preserve the
known expectation; DSRv2 qualification has failed. Q01's HTTP 200 body stream
closes after 365.2 seconds with partial output and unavailable final usage; it
is not retried. The large trial finishes at concurrency 8: four of eight
unchanged hierarchies and both controlled variants return complete reports;
Q23, Q26, Q28 and Q29 have ungraded body socket interruptions and are not
retried. Q21 and Q22 preserve the 66 groups / 44 required flags and pass their
targeted Carstens checks, but both change the untouched Money transfers link
`4.2` → `4.2.1` from valid to invalid and remove compatible headings for its
meaning. Both fail cross-version consistency. Across the three preserved
qualification experiments, all 29 distinct cases are attempted once, producing
24 complete reports and five ungraded interruptions; Q04's reuse is not a new
sample. Adoption remains open and bulk review remains unqualified.
This authorizes qualification, not bulk review, teacher auditing, test unsealing,
new rubric revisions or model substitution. The 44 large-case requirement flags
remain provisional consistency inputs. See the
[DSRv2 qualification evidence](../../sse_multivector/distillation-review-v1/README.md#dsrv2-qualification-october-8).

**Matching-only preview authorized October 8:** after discussion and research
about reliability and scale, the user directed preparing a concrete preview
before calls. Draft DSMv1 compares one generated subject's complete meaning
against the same fixed teacher list for that note, returning an ID or none and
a brief reason. Mechanical exact matches need no model judgment. Prepare known
paraphrases and controlled near misses, including large training references;
keep expectations outside the prompt and reserve separate-note confirmation
controls from prompt tuning. ASv6.100 remains trusted. The source-bound adapter
and native reports implement this offline preview, not a replacement bulk
review process. Teacher required/optional flags are outside the matching task;
earlier provisional Sol groups are not gold. Sol / xhigh and concurrency 8 stay
fixed. At this preview stage, reliability, model calls, effort/batching experiments, adoption and
pilot final-test unsealing remain subsequent decisions. See the
[DSMv1 preview](../../sse_multivector/distillation-review-v1/README.md#matching-only-offline-preview).

**DSMv1 development trial authorized October 8:** after receiving the exact
preview, the user directed running the 16 development controls with the same
Sol / xhigh and concurrency 8 settings. All 16 complete reports match the
authored expectations: eight correct matches, eight correct nonmatches, no
semantic/mechanical failures, retries or reused answers. Native usage reports
17,110 input tokens, zero cached input and 1,822 output tokens including 1,066
reasoning tokens. This is an initial controlled matching check, not production
qualification or a comparison against batching/lower effort. The 16 reserved
confirmation controls and independent repeats were still unrun at that stage. Confirmation,
optimization experiments, full review adoption and test unsealing remain open.
See the [DSMv1 development evidence](../../sse_multivector/distillation-review-v1/README.md#dsmv1-development-trial-october-8).

**DSMv1 confirmation accepted October 8:** the user accepted the proposed
16-control confirmation run with DSMv1 unchanged, Sol / xhigh and concurrency 8.
All 16 match the authored expectations on their first attempt, with no failures,
retries or reuse. Both sets therefore pass 32/32 controls on separate source
notes. Native confirmation usage reports 16,592 input tokens, zero cached input
and 2,007 output tokens including 1,217 reasoning tokens. This supports matching
on the authored controls, not a production error rate or the full review process.
At that stage, independent repeats, effort/batching experiments, adoption and
test unsealing remained open. See the [DSMv1 confirmation evidence](../../sse_multivector/distillation-review-v1/README.md#dsmv1-confirmation-trial-october-8).

**DSMv1 independent repeat authorized October 8:** the user explicitly directed
repeating the confirmation calls to check whether fresh calls stay correct.
Native preparation inherited all 16 identical inputs/settings and disabled
saved-response reuse with `--repeat`. Sol / xhigh at concurrency 8 produces
16/16 correct reports with unchanged teacher IDs/null; 15 explanations are
reworded. There are no failures, retries or reused answers. Native usage reports
16,592 input tokens, zero cached input and 2,121 output tokens including 1,353
reasoning tokens. These repeat existing controls; they are not additional
distinct examples or evidence of accuracy on actual distilled wording.
More realistic matching tests, effort/batching comparisons, full review adoption
and final-test unsealing remain open. See the
[DSMv1 repeat evidence](../../sse_multivector/distillation-review-v1/README.md#dsmv1-independent-confirmation-repeat-october-8).

**Actual-wording matching preview authorized October 8:** the user accepted
preparing an offline matching test from saved distilled wording, with expected
answers established before further calls. The shared adapter binds evaluation
inputs, trusted ASv6.100 references and untouched saved generations by hashes;
it checks note/input identity and production parsing without opening reserved
test generations. DSMv1, Sol / xhigh and concurrency 8 stay fixed. The preview
selects sampled, lexically close and largest inputs from all three baselines
and final validation checkpoints: 24 selection hits produce 22 distinct inputs.
Eight expected matches and thirteen expected nonmatches are agent assessments,
not independently verified gold; one sampled phrase remains unresolved.
The initial preview had two unresolved phrases. The user subsequently accepted
the assessed nonmatch for `Fakery` under DSMv1's existing complete-meaning rule:
overlap with `Inauthenticity` or `Deception` is insufficient. Acceptance does
not promote the assessment to independently verified gold; `Club symbols`
remains unresolved. A fresh offline preparation preserves all input wording
and settings while recording R05's updated expectation status and reason.
Native qualification stays pending even if a reviewer agrees with all
assessments, and unresolved placeholders cannot become negative gold labels.
Preparation makes zero calls. Independent verification, resolving the meaning
boundaries, further calls, rubric changes, optimization, full review adoption
and test unsealing remain open. This is not an ASv6.100 audit. See the
[actual-wording preview](../../sse_multivector/distillation-review-v1/README.md#actual-distilled-wording-offline-preview-october-8).

**Post interpretation accepted October 8:** the user accepted including the
original post to interpret words or phrases already present in either subject.
The post cannot supply restrictions absent from a subject. Draft DSMv2 implements
this distinction through an optional `{POST}` template variable while preserving
DSMv1's tested prompt and inputs. Complete-meaning matching and ASv6.100's authority
remain unchanged. The new offline preview retains the same 22 targets and
Sol / xhigh, concurrency 8 settings, with zero reviewer calls. Prior assessments
remain unverified and need checking with the supplied posts; `Club symbols` is
still ungraded. Semantic reliability, further calls, full review adoption and
final-test unsealing remain open. See the
[DSMv2 draft and preview](../../sse_multivector/distillation-review-v1/README.md#dsmv2-post-interpretation-draft-october-8).

**DSMv2 club expectation assessed October 8:** the user authorized settling
the expected club verdict before reviewer calls. The offline agent assessment
sets R19 to teacher T06 / original number `4`, `Clubs suit symbol`: the post's
`♣` selects the card-suit sense of `Club symbols`, and the plural is a generic
subject label rather than an added count. This records an assessment, not user
acceptance of that verdict or independent gold verification. DSMv2's spec now
binds a separate source definition; DSMv1's unresolved expectation stays intact.
The fresh offline preview preserves all 22 prompts/settings and makes zero
calls. There are nine assessed matches, thirteen assessed nonmatches and no
unresolved placeholders, but all expectations remain unverified and qualification
is pending. The other 21 inherited assessments still need checking with posts
visible before calls. See the [club assessment](../../sse_multivector/distillation-review-v1/README.md#dsmv2-post-interpretation-draft-october-8).

**DSMv2 self-custody expectation checked October 8:** the user accepted checking
the missing Bitcoin restriction with the post visible. The offline agent
assessment retains R16's expected null: `Self-custody` names the custody
relationship but does not specify the Bitcoin asset in teacher T12. Its DSMv2
reason is clarified; the verdict, assessment status, all 22 prompts and runner
settings remain unchanged. A fresh offline preparation makes zero calls. This
does not decide whether the general heading is supported or whether the note
covers the teacher meaning elsewhere. Both R16 and R19 remain unverified agent
assessments; actual reviewer adherence has not been tested. The other 20
inherited assessments still need checking with posts visible before full-set
calls. See the [DSMv2 assessments](../../sse_multivector/distillation-review-v1/README.md#dsmv2-post-interpretation-draft-october-8).

**DSMv2 two-case trial authorized and completed October 8:** the user accepted
testing the club-symbol and self-custody cases with the unchanged DSMv2 prompt,
Sol / xhigh and concurrency 8. Both fresh calls are mechanically valid and
agree with the prior agent expectations: R19 returns T06 because the post's
`♣` disambiguates "club"; R16 returns null because `Self-custody` omits Bitcoin.
There are two first attempts, no retries and no response reuse. Native usage
records 1,735 input tokens, zero cached input tokens and 1,129 output tokens,
including 1,025 reasoning tokens. The catalog estimate is $0.01476, not an
invoice. Agent reviews accept the saved verdicts without asserting independent
gold verification or user acceptance of their semantics. Qualification remains
pending. This does not establish repeat stability, general reliability or
authorize the other 20 cases, bulk review or final-test unsealing. See the
[two-case result](../../sse_multivector/distillation-review-v1/README.md#dsmv2-two-case-post-interpretation-trial-october-8).

**DSMv2 remaining post checks authorized and completed October 8:** the user
accepted checking the other 20 expected verdicts against the subjects, complete
teacher catalogs and visible original posts before additional reviewer calls.
All 20 verdicts are retained: eight matches and twelve nonmatches. Only their
recorded reasons change; all 22 complete prompts, inputs, expected IDs and
assessment statuses are preserved. The full set remains nine assessed matches
and thirteen assessed nonmatches. The fresh offline preview makes zero calls,
attempts or reused answers. This is a recheck of known agent labels, not
independent gold verification or a teacher audit. Qualification remains pending;
additional reviewer calls, bulk review and final-test unsealing remain separate
decisions. See the
[post-visible recheck](../../sse_multivector/distillation-review-v1/README.md#dsmv2-remaining-post-visible-expectations-october-8).

**DSMv2 remaining trial authorized and completed October 8:** the user accepted
running the other 20 cases through `experiment-runner/bin/experiment-runner`
with unchanged Sol / xhigh, concurrency 8 settings. All 20 final reports are
mechanically valid; nineteen agree with the pre-recorded expectations. R05
matches `Fakery` to T17, `Inauthenticity`, instead of expected null. Native
scoring flags a false match against that label; agent review marks it uncertain
because contextual equivalence needs adjudication before attributing the
disagreement to reviewer error. The other nineteen agent reviews accept the
saved verdicts. Prompts, inputs, expected labels and assessment statuses are
preserved. There are 21 attempts, including a successful provider-overload retry
of R15, and zero reused answers. Native usage is 24,122 input tokens, zero
cached input and 5,703 output tokens, including 4,598 reasoning tokens; the
$0.105274 catalog estimate is not an invoice. Qualification remains pending;
this does not independently verify the labels, establish repeat stability or
approve reviewer adoption, further calls, prompt changes, bulk review or test
unsealing. See the
[remaining trial](../../sse_multivector/distillation-review-v1/README.md#dsmv2-remaining-20-case-trial-october-8).

**DSMv2 action/property controls authorized and completed October 8:** the user
accepted testing clear examples of the distinction raised by R05. The shared
CLI prepared and ran eight authored controls with the unchanged DSMv2 prompt,
Sol / xhigh, subscription SSE and concurrency 8. Four faithful paraphrases
match the intended action or property; four cases removing the complete match
return null. All reports and reasons are valid, and native agent review records
eight acceptances. Expectations were frozen before calls and withheld from the
prompt. There are eight new attempts, no retries and no reused answers. Native
usage is 3,333 input tokens, zero cached input and 1,023 output tokens, including
689 reasoning tokens; the $0.016896 catalog estimate is not an invoice. The
controls were authored after observing R05 and use explicit wording and one-
or two-entry catalogs. They establish success on this narrow distinction, not
the cause of R05's verdict, independent gold or production reliability.
R05's expected null and uncertain review are preserved; ASv6.100 remains trusted.
The generic adapter and native attributed reviews are sufficient for these
authored controls; no runner code or prompt changes occurred. The 14 matching
regression tests pass with the required cached tokenizer dependency. Further
calls, prompt changes, bulk review and test unsealing remain separate decisions.
See the [controls and evidence](../../sse_multivector/distillation-review-v1/README.md#dsmv2-actionproperty-controls-october-8).

**DSMv2 R05 fresh repeat authorized and completed October 8:** the user accepted
one fresh call with identical inputs/settings. The shared CLI prepared from the
remaining 20-case trial with `--only R05 --repeat`, preserving the baseline and
excluding response reuse. Preflight verifies identical complete prompts,
inputs, evidence and settings: DSMv2 / Sol / xhigh, subscription SSE and
concurrency 8. The repeat again returns T17, Inauthenticity, with a new
explanation equating Fakery with general fakeness. Both saved calls make that
match; neither reason addresses the expected practice/products versus property
distinction. This is repeat evidence, not independent semantic adjudication or
a general stability estimate. Native scoring still flags a false match against
the agent-assessed expected null, and native agent review marks the repeat
uncertain. One new attempt produces one valid report, without retry or reuse.
Native usage is 859 input tokens, zero cached input and 339 output tokens,
including 290 reasoning tokens; the $0.005108 catalog estimate is not an invoice.
No code, prompt or expectation changed; the original receipt/review and
ASv6.100's authority are preserved. Native receipt, baseline and input checks
pass. Further calls, prompt revisions, bulk review and test unsealing remain
separate decisions. See the [repeat evidence](../../sse_multivector/distillation-review-v1/README.md#dsmv2-r05-fresh-repeat-october-8).

**Coverage-matching qualification scope agreed October 8:** following the
read-only score trace, the user agreed to qualify matching of required complete
teacher meanings. Optional derived teacher headings are not mandatory coverage
targets. Every student heading still needs subject-support review, every
immediate parent-child link needs review, and required meanings must occur at
every compatible student heading occurrence, including general headings.
Complete-meaning matching criteria are unchanged. Establish required/optional
flags from the trusted teacher answer and post independently of candidates,
and freeze them across versions of each note before preparing revised cases.
The current adapter still supplies all distinct teacher strings and bypasses
required flags; no code, prompt, expectation or saved trial changes are implied.
R05's requirement flags remain unfrozen and its expected null remains a disputed
agent assessment. Broader qualification and adoption remain open. Revised
preparation, implementation, calls, bulk review and test unsealing remain
separate work. See the
[agreed scope](../../sse_multivector/distillation-review-v1/README.md#coverage-matching-qualification-scope-agreed-october-8).

**Teacher-relative qualification case preparation authorized October 8:** after
the user questioned the required/optional distinction and requested research,
the assistant proposed comparing teacher meanings and parent-child relationships,
allowing equivalent wording, renumbering and sibling reordering. Structural
allowances and final pilot scoring remain open. The user authorized one worked
example, then qualification-case preparation with exact inputs and expected
judgments shown before calls. The new case source binds ASv6.100's unchanged
cable example and contains six variants: unchanged, paraphrase, negation reversal,
invalid parent, omitted heading and renumbering. Every case specifies complete
matches for all ten teacher wordings and actual subject/link findings; no
required/optional classification or new numerical scores are asserted. The
omitted-heading case records a missing teacher meaning even though remaining
subjects/links are valid, without changing Q12 or the existing optional-row
scorer. The unchanged DSRv2 renderer is used solely for offline input inspection,
not adopted for the proposed comparison. Two non-exact targets are separately
prepared with unchanged DSMv2, the post and full ten-wording catalog. Both use
Sol / xhigh, subscription SSE and concurrency 8; preparation makes no calls.
These are previously seen worked-example development controls, not independent
confirmation. No prompt, scorer, saved label or trial changes are authorized by
this preparation; broader reviewer/rubric adoption and inference remain separate
work. See the
[case preview](../../sse_multivector/distillation-review-v1/README.md#teacher-relative-qualification-case-preview-october-8).

**Teacher-relative case judgments reviewed October 8:** the user accepted
TC05 with “ok”, then explicitly agreed to TC04, TC03, TC02, TC06 and TC01 as each
case was presented in conversation. Treat the trusted teacher as correct and
keep teacher agreement, post support and immediate parent-child validity as
separate findings:

- **TC05, omitted heading:** removing `2 m cables` fails teacher agreement.
  `2 m cable A` is a particular instance and does not reproduce the separate
  general heading. The remaining subjects and their incoming links are valid.
- **TC04, changed parent:** putting `3 m cables` under `2 m cables` fails
  teacher agreement and parent-child validity. Every subject meaning remains
  present and supported by the post.
- **TC03, reversed comparison:** removing `not` from all four comparison
  copies fails teacher agreement and post support. Their incoming links remain
  valid because the comparison still preserves the parent descriptions of
  the cables.
- **TC02, equivalent wording:** `Cable A, two metres long` preserves
  `2 m cable A`; teacher agreement, post support and parent-child validity
  all pass.
- **TC06, renumbering:** changing the complete number prefix from `1` to `9`
  preserves wording and parent-child relationships; all three checks pass.
  Check this case mechanically, without a semantic model call.
- **TC01, unchanged answer:** returning the teacher's complete answer with
  identical subjects, numbering and relationships passes all three checks by
  definition because the teacher is trusted. Check this mechanically, without
  a semantic model call.

All six case judgments are agreed. TC06 does not independently exercise
arbitrary sibling reordering. These approvals concern the six authored case
expectations, not model qualification, adoption of a final pilot rubric, or
numerical scoring.
The earlier required/optional scoring implementation, existing prompts,
case-source expectations and saved trials remain unchanged. A general
teacher-edge agreement check remains unimplemented. No model calls were made
during this review; broader structural allowances and final rubric/adoption
remain open. The [case table](../../sse_multivector/distillation-review-v1/README.md#teacher-relative-qualification-case-preview-october-8)
records each approval separately.

**DSMv2 meaning-matching instructions approved October 9:** the user reviewed
the exact DSMv2 instructions and prepared paraphrase request, confirmed that
the prompt answers only complete-meaning matching, and approved the wording.
Each request compares one generated subject with the complete distinct teacher
wording list for that note. The post interprets wording without supplying
restrictions missing from a subject. Return exactly one JSON object with
`teacher_id` (a supplied ID or JSON `null`) and `reason` (a brief explanation).
The existing return-format instruction was clarified in conversation; the
prompt and response schema are unchanged. The cable JSON is the request's
input, not a worked example in the instructions; the displayed T04/null
expectations remain outside the reviewer prompt. Subject support and
parent-child validity are separate judgments. This approves the instructions,
not model qualification, numerical scoring, bulk adoption or new calls.
The two prepared teacher-relative matching cases remain unrun, and R05's
disputed match remains unresolved. See the
[instruction approval](../../sse_multivector/distillation-review-v1/README.md#dsmv2-matching-instructions-approved-october-9).

**DSSv1 subject-support prompt drafting authorized October 9:** the user
accepted proceeding with a draft for review in the conversation. The proposed
judgment checks whether the complete post supports every meaning actually
expressed by one subject with no complete teacher match, including supported
broader headings. DSSv1 applies the relevant ASv6.100 rules and returns exactly
one JSON object with Boolean `valid` and string `reason`. Its input contains
only the full post and one subject; it does not receive a teacher catalog or
candidate hierarchy. The revised wording is accepted below; the proposed
`Lengths` / `4 m cable A` controls await approval and qualification. Deriving
post support from correct complete teacher matches remains a proposed process
change; semantic matches also require a qualified matcher. No support experiment,
adapter, schema, scorer change, inference or bulk adoption is authorized by drafting. Existing
prompts and saved evidence are preserved. See the
[DSSv1 draft](../../sse_multivector/distillation-review-v1/README.md#dssv1-subject-support-prompt-draft-october-9).

**DSSv1 authoritative-rule reuse and review wording accepted October 9:**
the user agreed to reuse ASv6.100's support rules unchanged, with a small review
task and return format, instead of maintaining a paraphrased second rulebook. The revised draft
uses `ASV6_100_SUPPORT_RULES` for ASv6.100's verbatim opening support-rule text,
ending after “Derive broader headings by generalizing source meanings without
adding restrictions.” Future shared-workflow preparation must load this text
from the original ASv6.100 source; the adapter added in the preparation below
now supplies it.
The input remains the full post and one subject, and the output remains Boolean
`valid` and string `reason`. After the full revised DSSv1 wrapper was displayed
in the conversation, the user accepted its exact wording with “ok, seems
reasonable”. This accepts the reuse decision and review instructions, not
authored controls, reviewer qualification, support inheritance, inference or
bulk adoption. DSSv1 was untested at wording approval; the later initial trial
is recorded below. ASv6.100, existing matching/review
prompts, schemas, scoring and saved evidence remain unchanged. See the
[revised DSSv1 draft](../../sse_multivector/distillation-review-v1/README.md#dssv1-subject-support-prompt-draft-october-9).

**DSLv1 parent-child validity prompt drafting authorized October 9:** the user
accepted proceeding with the proposed next step of drafting the third judgment
before qualification. The reusable draft quotes ASv6.100's parent-child rule
verbatim through `ASV6_100_PARENT_CHILD_RULES`, with one immediate parent/child
pair in `RELATIONSHIP_INPUT`. Only the two subject strings are supplied, as the
rule judges their relationship across possible posts. Return Boolean `valid`
and string `reason`; an invalid reason names the lost restriction and gives a
possible post fitting the child but not the parent. Post support and teacher
agreement remain separate judgments. TC04's agreed invalid cable edge is shown
as a human input example outside the instructions, not a model result or newly
prepared qualification case. After the full DSLv1 instructions were displayed
in the conversation, the user approved their wording with “ok lgtm”. The prompt
was unchanged and untested at wording approval. The later initial trial is
recorded below. This accepted the instructions without qualifying the reviewer or authorizing new calls.
No link adapter, schema, experiment preparation, inference, scoring change or
bulk adoption is authorized by drafting. Existing prompts and saved evidence
remain unchanged. See the
[DSLv1 draft](../../sse_multivector/distillation-review-v1/README.md#dslv1-parent-child-validity-prompt-draft-october-9).

**DSMv3 ASv6.100 wording amendment authorized October 9:** the user accepted
adding the relevant subject-wording guidance verbatim before qualifying a new
matching version. Native `revise` creates DSMv3 from approved DSMv2, changing
only its version label and an interpretive block containing ASv6.100's paragraph
beginning “Make each `subject` concise”. The teacher answer remains the trusted
reference and the task remains complete-meaning matching. Inputs, matching
criteria, response contract, cases, expected labels and saved trials are
unchanged. The full generation and hierarchy-placement instructions are
excluded. After the full DSMv3 instructions were displayed in the conversation,
the user approved their exact wording with “lgtm”. The prompt was unchanged
and untested at wording approval; broader qualification is pending after the
later initial trial below. This accepted the matching instructions without qualifying the reviewer or authorizing new calls. No
DSMv3 experiment was prepared during drafting or approval recording. The
subsequent preparation below adds inputs without model calls or accuracy/cost
measurements.
DSMv2 evidence does not qualify DSMv3, and R05 remains disputed. Support/link
judgments, scoring, bulk adoption and final-test sealing are unchanged. See the
[DSMv3 draft](../../sse_multivector/distillation-review-v1/README.md#dsmv3-asv6100-wording-guidance-draft-october-9).

**First three-check development preparation authorized October 9:** after the
user reconfirmed that DSLv1 judges the distilled model's immediate parent-child
pairs, the user accepted preparing and showing test inputs and expected
judgments before calling models. Preparation reuses the already-accepted TC02
paraphrase, TC03 reversed comparison and TC04 wrong-parent case. Native shared
runner preparations contain two DSMv3 requests, two DSSv1 requests and three
DSLv1 requests, initially unrun with zero attempts and zero reused answers. The
`distillation_verdict` project adapter loads hash-bound saved cases, derives
actual immediate parents from student numbering, extracts ASv6.100's rules
verbatim and keeps expected answers outside prompts. Its Boolean expectations
come from the existing agreed source judgments; selectors cannot rewrite
wording or override those verdicts. The shared Boolean response schema and
validator check output mechanics, with a separate comparison against the
prepared expectations. They do not qualify the reason's semantics or adopt
pilot scoring. Production-path tests use only an offline executable fixture.

The unchanged-answer and renumbering controls remain mechanical. The proposed
`Lengths` / `4 m cable A` cases are not added. Prompts stay unchanged; all three
current versions were untested at preparation. The later initial trial below
uses the same specifications, preserving GPT-6.1 Sol / xhigh, subscription SSE and concurrency 8. These seven development controls
are an initial preview, not sufficient qualification: larger controls and fresh
repeats remain necessary before bulk use. Support inheritance, structural
allowances, teacher-edge comparison, final rubric adoption, bulk grading and
final-test unsealing remain outside this preparation. R05 remains unresolved.
The exact seven inputs and expectations were subsequently displayed in the
conversation and the user accepted them. The subsequently authorized initial
xhigh trial with prefix warming is recorded below. See the
[prepared development inputs](../../sse_multivector/distillation-review-v1/README.md#first-three-check-development-inputs-october-9).

**Later reasoning-level comparison requested October 9:** after accepting the
displayed cases, the user expressed wanting to test which lower reasoning level
would suffice later. Establish reviewer reliability with GPT-6.1 Sol / xhigh
first; the existing initial settings remain fixed. Later comparisons should
hold the cases, expected judgments and prompts fixed and measure semantic
errors, latency and actual token usage, including cached tokens. This records
the requested future comparison, not a lower-effort fallback or approval of
specific experiment settings, new calls or bulk grading. No prompt, prepared
input, model setting or saved result changes in recording this decision.

**Initial three-check trial and prefix warming authorized October 9:** the user
instructed proceeding with the accepted seven inputs and explicitly requested
prefix warming. The shared runner prepared three native-prefix batches from
the original offline preparations and one instructions-only warmup for each.
Approved prompt bytes, inputs and expectations remain unchanged; warmup and
batch share their prompt-specific stable key, model, effort and output schema.
The route is subscription `openai-codex` / `gpt-6.1-sol` / `xhigh` / SSE, with
batch concurrency 8 and the existing provider-only two-attempt limit. A shared
persistent counter records 10/20 used: three warmups and seven verdicts, all
first-attempt completions, with no reused answers or failures.

DSMv3 passes 2/2 accepted expectations, DSSv1 2/2 and DSLv1 3/3. Native agent
reviews accept all seven explanations, including TL02's preserved parent
restrictions despite an unsupported comparison and TL03's missing restriction
with a possible counterexample. These are actual initial model results and
agent assessments, not fresh confirmation or user approval of reasons.
All requests report zero cached tokens and zero cache writes. Verdict inputs
are 355–733 tokens each, below the documented 1,024-visible-token cache minimum;
this trial demonstrates no cache savings. Warmup overhead, per-experiment
actual usage, request latency and API-equivalent estimates are preserved in the
[trial record](../../sse_multivector/distillation-review-v1/README.md#initial-warmed-three-check-trial-october-9). Catalog estimates are not subscription
charges, and provider cash costs are unreported. No paid API fallback occurred.

The seven small controls do not qualify bulk review. The larger training cases
and fresh repeat below extend the evidence; broader qualification remains
necessary. Lower-effort comparison
remains future work; support inheritance, structural allowances, teacher-edge
comparison, scoring adoption, bulk grading and test unsealing remain undecided
or unimplemented as before. R05 remains unresolved. The original offline
preparations remain unrun; actual outputs and receipts are in separate ignored
warmup/warmed experiment directories. No additional trial is launched by
recording this result.

**Larger training-control preparation authorized October 9:** after the initial
seven-case pass, the user accepted preparing harder controlled student changes
from the largest saved ASv6.100 training answers and presenting them before
calling models. The teacher answers remain trusted. The preview selects the
existing ranked maximum-entry note (145 entries), maximum-distinct-catalog note
(72 wordings) and longest-answer note (35,966 bytes), with training identity,
line and file hash verified against the saved ranking. No held-out post or
subject becomes development input.

Seven proposed variants cover numeric and long-composite paraphrases, changed
quantity, a lost time restriction, removed negation, first versus renewed ban,
and moving a trusted subject beneath a parent that excludes its named person.
Unchanged adapters prepare six DSMv3, six DSSv1 and four DSLv1 requests. The
teacher catalogs and original posts remain complete; selected link inputs derive
actual immediate parents from student numbering. Exact trusted wording in the
wrong-parent variant adds no matching/support calls. Expected decisions and
reasons remain outside prompts. The loss of the three-day window deliberately
proposes different results: no complete teacher match, supported remaining
subject, invalid parent-child link.

At preparation, all 16 inputs were unrun, with zero attempts/reuse and fixed
Sol / xhigh / subscription SSE / concurrency 8 settings. Matching preparation reports
14,208 rendered proxy tokens total, 2,260–2,441 per request; no provider usage or
caching measurement is claimed. Four edits reuse previous authored matching
controls; this is development evidence, not a fresh confirmation partition.
The [case preview](../../sse_multivector/distillation-review-v1/README.md#larger-training-controls-prepared-october-9) preserves exact changes,
expectations and native inspection/preparation commands. The user has accepted
LC03, LC04 and LC07 as recorded below. The user then delegated remaining
expectation review to the agent; LC01, LC02, LC05 and LC06 assessments are
complete as recorded below. The subsequent trial was separately authorized
and completed as recorded below. Thirty-six existing production
preparation/validation tests pass with the documented tokenizer dependency; default Python initially lacked it.
No prompt, adapter, general teacher-edge check or scoring implementation changes
are needed. Qualification, repeats and lower-effort comparison remain open;
R05, support inheritance, structural allowances, bulk grading and final-test
unsealing are unchanged or unresolved. The first case presented for discussion
is the dropped time restriction.

**LC03 judgments agreed October 9:** after the complete teacher subject, edited
student subject and unchanged immediate parent were presented, the user replied
“ok”. Dropping `in three days` receives no complete teacher match (LM03: null),
retains post support for the remaining expressed meaning (LS03: true), and
invalidates the link because the child omits the parent’s three-day restriction
(LL01: false). This accepts only this variant’s three expected judgments.

**LC07 judgment agreed October 9:** after the actual new student parent and
unchanged child were presented, the user replied “ok”. The parent, `Health
workers other than Dr. Abu Safiya abducted from Gaza`, explicitly excludes
the person named by `Dr. Abu Safiya, a health worker abducted from Gaza`, so
the link is invalid (LL04: false). Both strings remain exact trusted teacher
wording; no matching or post-support calls are needed. This accepts the expected
link judgment, not new model calls or a general teacher-edge implementation.

**LC04 judgments agreed October 9:** after the complete teacher subject, edited
student subject and original post excerpt were presented, the user replied
“ok”. The teacher subject is `The Bank for International Settlements designing
monetary rules rather than printing money`; the edited student subject is
`The Bank for International Settlements designing monetary rules and printing
money`. The original post states, `The BIS doesn’t print money; it designs the
rules of the game.` Changing `rather than` to `and` reverses the exclusion,
so no complete teacher meaning matches (LM04: null). The added claim of printing
money contradicts the post’s explicit negation, so post support fails
(LS04: false). This accepts only those two expectations and adds no model calls.
The preview includes no separate link call for LC04.

**Remaining control review delegated October 9:** the user said, “i don't want
to look at all of them myself”, after LC01 was presented. The agent reviews
the remaining authored expectations under the already agreed semantic rules,
without requiring individual user inspection of every case. This is delegation
of expectation review, not explicit user acceptance of each remaining label
or authorization for new model calls.

**Agent expectation assessments completed October 9:** native `show --case`
inspection covered complete catalogs and posts for LM01, LM02, LM05 and LM06;
complete posts and student subjects for LS01, LS02, LS05 and LS06; and actual
student pairs for LL02 and LL03:

- LC01 preserves the complete headline with `two` → `2`: LM01 matches T07,
  LS01 passes.
- LC02 changes the count to three while the trusted teacher and post say two:
  LM02 returns null, LS02 fails.
- LC05 preserves the account owner, banning platform, renewed ban, release
  purpose and every other clause under its paraphrase: LM05 matches T07,
  LS05 and LL02 pass.
- LC06 changes the renewed ban to a first ban: LM06 returns null, LS06 and
  LL03 fail. The post says `(again)`; a first-ever ban also fails to retain
  the actual parent’s renewed-ban restriction.

No authored expectation changes or material ambiguities were found. These are
agent assessments, separate from the three cases with explicit user acceptance
and from the subsequent model verdicts. All seven variants completed
expectation review; no further individual user case review was pending.
Expectation review itself added no inference authorization. All 16 inputs were
unrun at that point; frozen sources, prompts, settings and numerical scoring
were unchanged.

**Larger three-check trial authorized and completed October 9:** after the agent
reported expectation review complete and proposed the 16-call trial, the user
replied “proceed”. The shared stable launcher ran the three existing frozen
preparations at subscription `openai-codex` / `gpt-6.1-sol` / `xhigh`, concurrency
8. Native qualification passes DSMv3 6/6, DSSv1 6/6 and DSLv1 4/4. All 16 reasons
have separate native agent acceptances after inspection, including explicit
counterexamples for invalid links. Every request completed on its first
attempt, with no retry, failure, interruption or answer reuse. The batches ran
sequentially with six, six and four cases, so eight was the execution ceiling
rather than occupied slots. No code, prompt, label, source or model-setting
change was required.

The [trial record](../../sse_multivector/distillation-review-v1/README.md#larger-three-check-trial-october-9)
preserves verdict/latency evidence, per-experiment native usage and API-equivalent
catalog estimates. Requests took 5.98–17.24 seconds. Every receipt reports zero
cached input and cache-write tokens; these preparations have no explicit
cache-affinity key or prefix warmup, and no warmed/cold comparison is claimed.
Provider cash-cost fields remain null; there was no paid API fallback.

This is one successful development trial on authored changes in three previously
used training notes, not an independent confirmation partition or qualification
for arbitrary distilled answers. The separately authorized repeat below checks
the same controls again with eligible shared prefixes. Broader qualification, R05,
support inheritance, structural allowances, teacher-edge implementation, final
scoring, bulk grading and final-test unsealing remain open or unadopted.

**Fresh xhigh repeat with eligible caching authorized and completed October 9:**
the user accepted the proposed fresh repeat, requested caching, then required
skipping it when shared prefixes are too small. The same DSMv3/DSSv1/DSLv1
prompts, complete source inputs and authored expectations are reused through
native `prepare --from ... --repeat --only ...`; GPT-6.1 Sol, xhigh, subscription
SSE and the concurrency-8 ceiling are fixed. Naturally shared reference
prefixes are measured before calls, without padding. Only matching L3/L6
(2,324/2,361 proxy tokens) and support L6 (1,073) receive explicit keys,
prefixes and native warmups. Shorter shared prefixes and singleton cases do not.

All 16 fresh case-level verdict checks pass and match the baseline decisions:
6/6 matching, 6/6 support and 4/4 links. Every reason has separate native agent
acceptance after inspection. The 16 verdicts and three warmups complete on
first attempts, without failure or answer reuse; the stage budget finishes
at 19/38 attempts. Matching L3/L6 report 6,528/4,480 cached input tokens.
Support L6 reports none despite its eligible prefix; the reason is not established.
Matching/support subset reports retain the original full expectation sets and
remain pending for cases assigned elsewhere; each selected case passes.
This is a repeat of the same authored training controls, not new controls or
an independent confirmation partition.

The [repeat record](../../sse_multivector/distillation-review-v1/README.md#larger-three-check-repeat-with-eligible-prefixes-october-9)
preserves prefix eligibility, all warmup overhead, per-experiment native usage,
API-equivalent catalog estimates and latency. Provider cash-cost fields remain
null; no paid fallback is used. The native prefix route changes seven verdicts
from a single user message to developer-prefix/user-suffix messages, despite
identical concatenated text. Agreement holds under that route; cost/latency
differences do not isolate caching. Broader reviewer qualification and later
lower-effort comparison remain open. Further calls, bulk grading, final-test
unsealing and the undecided scoring/structure policies are not adopted by this
result.

**Broader actual-output trial approved October 9:** after the fresh xhigh repeat,
the user agreed to testing a broader sample of actual distilled outputs, then
explicitly selected all three approved checks. The prompts remain DSMv3,
DSSv1 and DSLv1 at Sol / xhigh / subscription SSE / concurrency 8. ASv6.100
remains trusted. Freeze selection and expected judgments before reviewer
calls; skip short-prefix warmups and mechanically duplicate work. This adds
no lower-effort comparison, bulk scoring or reserved-test access.

The [actual validation preparation](../../sse_multivector/distillation-review-v1/README.md#actual-validation-preparation-approved-october-9)
now supports source-bound saved outputs for all three checks through the shared
workflow. Support uses the complete original post; relationships use the actual
student parent. Agent expectations remain unverified and unresolved labels
receive no semantic pass/fail. Selection and expectations are frozen for 20
distinct subjects across 16 previously unused validation notes, spanning all
18 versions plus large-catalog additions. A duplicate shares all three checks.
The 60 verdicts and two eligible warmups now complete on first attempts,
without reuse or mechanical failure. Agreement with frozen agent expectations
is DSMv3 17/19 (A15 unscored), DSSv1 19/20 and DSLv1 17/20. Semantic disagreements
remain; qualification stays pending. Matching A19 was disputed before calls.
Matching caching reports hits; support caching reports none. The record keeps
all warmup overhead and per-experiment usage. This is a bounded development
challenge set, not population accuracy or authorization for bulk grading.

**Fresh confirmation of rejected actual cases authorized and completed October 9:**
the user directs proceeding with the unchanged-prompt confirmation. Four rejected
cases and four previously accepted contrasts repeat at Sol / xhigh / subscription
SSE / concurrency 8. All eight complete on first attempts with distinct fresh
receipts, no reuse, retry or warmup. Matching A01 and link A03 now match their
frozen expectations; support A20 and link A21 repeat their errors. All four
accepted contrasts stay accepted. Native agent review records six accept and
two reject; expectations remain unverified and qualification stays pending.
Naturally shared prefixes are below 1,024 tokens; native cache reads/writes are
zero. Request bodies, methods and URLs remain identical despite runner 1.2.0's
recorded provenance update. The [confirmation record](../../sse_multivector/distillation-review-v1/README.md#fresh-confirmation-of-four-rejected-cases-october-9)
preserves exact selections, reasons, native usage and latency. This shows repeated
errors and inconsistent decisions on selected cases, not an overall accuracy
estimate. Prompt changes, lower-effort work, bulk review and test access remain
unadopted.

**Support exception clarification drafting authorized October 9:** after the
fresh confirmation, the user directs proceeding with the recommendation to
address the repeated support exception error and show a proposed change before
further calls. [DSSv2](../../sse_multivector/distillation-review-v1/README.md#dssv2-exception-clarification-draft-october-9)
was first prepared as an untested draft, adding one claim-scope paragraph after
the unchanged ASv6.100 excerpt. It distinguishes dropping a limiting exception while retaining
its claim from permitted broader subject naming. Native revision preserves the
exact delta; the offline A08/A20 preview preserves inputs and settings and makes
no calls. Draft integrity and agent agreement do not establish effectiveness.
The user subsequently approves the exact wording and bounded semantic trial
below. DSMv3, DSLv1, existing expectations, teacher trust, qualification, bulk
review, scoring and test sealing remain unchanged.

**DSSv2 wording and bounded support trial approved October 9:** after reviewing
the exact clarification, the user directs proceeding. The
[bounded trial](../../sse_multivector/distillation-review-v1/README.md#dssv2-bounded-support-trial-october-9)
keeps all 20 original support expectations and adds three authored subjects on
A20's exact original post: retain its exception, name the broader topic, and
reverse its exception. A fresh DSSv1 comparison covers those variants and the
original failure. Native source-bound support preparation gains only an optional
subject variant, preserving saved generation/number/post/AS rules and keeping
expectations in review evidence. Sol / xhigh / subscription SSE / concurrency 8
stay fixed. The stage has 27 verdict calls, one eligible warmup and at most 56
attempts including provider-only retries. Only the three long-post support cases
receive a qualifying prefix; shorter groups are not warmed. Runner 1.2.1's
post-response cost statistics do not change requests. The completed trial
matches 20/20 actual DSSv2 labels and 3/3 DSSv2 controls; fresh DSSv1 matches
4/4 controls. All 27 verdicts and reasons pass attributed native agent review;
all 28 requests, including warmup, finish on first attempts without reuse.
Fresh DSSv1 correctly rejects the original exception case after two earlier
identical-request failures, preventing causal attribution of an improvement
to DSSv2. Cache reads/writes are zero; warmup adds $0.005884 in catalog
API-equivalent cost. Qualification stays pending on agent-assessed expectations.
This adopts no matching/link change, lower-effort trial, bulk grading, scoring
or reserved-test access. Addressing the remaining repeated DSLv1 error is a
recommendation at this point; the subsequent drafting authorization follows.

**DSLv2 parent-restriction clarification drafting authorized October 9:** the
user directs proceeding with the recommendation to address repeated DSLv1 A21
failure and show proposed wording before calls.
[DSLv2](../../sse_multivector/distillation-review-v1/README.md#dslv2-parent-restriction-clarification-draft-october-9)
adds one paragraph after the intact ASv6.100 rule: do not invent a presenting,
explaining or performing requirement absent from the parent; a clause or
modifier may preserve a restriction, but mere mention that drops or changes
it is insufficient. The same Boolean/reason and invalid-counterexample contract
remains. Native revision preserves the exact delta and hashes; no source,
expectation or model setting changes, and no calls or experiment preparation
occur. Independent wording assessment is not approval or evidence that the
reviewer applies the clarification reliably. Wording approval and a bounded
semantic test remain pending; qualification, other reviewers, scoring, bulk
adoption and test sealing remain unchanged. The subsequent trial authorization
follows.

**DSLv2 wording and bounded parent-child trial approved October 9:** after
reviewing the exact clarification, the user directs proceeding. The
[trial](../../sse_multivector/distillation-review-v1/README.md#dslv2-bounded-parent-child-trial-october-9)
uses 19 unchanged actual-output pairs excluding A06, seven existing training
controls, and fresh unchanged DSLv1 on the same A02/A13/A16/A21 pairs. A12's
response-target interpretation is flagged before calls, with its frozen false
label preserved and its evidence outside the 25 uncontested DSLv2 assessments.
Thirty verdicts share a 60-attempt budget; only provider failures may retry,
at most once per case. Sol / xhigh / subscription SSE / concurrency 8 and
authoritative AS wording stay fixed. Short prefixes receive no warming or
padding. Native preparations and receipts preserve source/code identity;
runner 1.2.1 is explicitly selected. The completed trial agrees with 24/25
assessed DSLv2 expectations; A12 matches its frozen false label but remains
uncertain and outside that count. A21 still returns false under both versions;
fresh DSLv1 agrees on 3/4 comparisons. Native reviews give 27 accept, two reject
and one uncertain. All 30 requests finish on first attempts without reuse,
retry, truncation or warmup; source/settings/receipt checks pass. No cached tokens
or net savings occur. Training-control qualification passes, while the actual
batches and broader reviewer qualification remain pending. The clarification
does not resolve this known failure at Sol/xhigh. Reconsidering the check using
trusted teacher relationships is recommended; this adopts no revised method
or structural policy and authorizes no further prompt/source repair,
lower-effort trial, bulk grading, scoring or reserved-test access.

**Mechanical decisions for every review prompt approved October 9:** the user
directs using mechanical processing wherever possible across teacher matching,
post support and parent-child validity. Given the trusted teacher answer, an
exact student subject match supplies the complete-meaning match and same-post
support without model calls. A validated empty teacher catalog establishes no
match; a missing or invalid reference is a preparation failure. An exact ordered
parent-child pair copied from an actual trusted teacher link supplies local
validity without a relationship call;
merely finding both subjects in the teacher catalog does not. Identical parent
and child wording also retains every parent restriction, without establishing
coverage or correct placement. No exact match does not mean invalid: remaining
semantic questions still need review under the unchanged ASv6.100 criteria.
Record mechanical origin, evidence and zero model attempts without a fabricated
model receipt. Identical requests may share saved results with frozen source,
prompt and runtime bindings, while every numbered occurrence remains visible
for placement and coverage. Explicit fresh repeats remain fresh inference.
Parsing, completeness, output
failure rules and score arithmetic remain mechanical and unchanged.

At approval, matching preparation supplied exact subject matches and rejected
exact targets from model controls; the shared runner reused identical requests,
but native zero-attempt results and general support/relationship acceptance
were unimplemented. The initial approval covered the design rule, not a prompt
change, implementation, further inference, final scoring policy,
bulk grading or test unsealing. The [process record](../../sse_multivector/distillation-review-v1/README.md#mechanical-decisions-for-all-three-checks-october-9)
distinguishes that rule from current behavior and preserves prior experiments.
The preceding read-only investigation finds that A21's `Proof setup` parent is
student-created and its child has complete-match null. Its true expectation is
an unadjudicated agent assessment, not a trusted teacher relationship; repeated
disagreement alone does not conclusively establish reviewer error or incapability.

**Mechanical review routing implementation subsequently authorized October 9:**
the user's `proceed` authorizes the selected-case adapters and shared runner
implementation of the approved rules. A preparation-local teacher index retains
every subject occurrence and actual ordered immediate-edge witness. Mechanical
output is independent of expected labels and validated through the selected
adapter. Native prepared/show results record mechanical origin, evidence, a sealed
digest and zero model attempts, without fabricated receipts or usage. Mixed runs
dispatch only semantic cases and charge no request budget or warmup for mechanical
cases; explicit fresh repeats bypass mechanical completion. Qualification reports
separate mechanical comparisons from model checks, preserve label disagreements
and leave agent-assessed expectations unverified. Complete prompt/config/source
bindings remain intact. Verification uses production paths and local workers;
this adds no real model calls, prompt changes, bulk scoring or test unsealing.

**Complete validation workload preview subsequently authorized October 9:**
the user's next `proceed` authorizes an offline count of all saved validation
outputs. A reusable project command in the shared launcher verifies the frozen
dataset, model provenance, sealed checkpoint metadata and production stage
receipts, then applies the existing mechanical teacher index. The
[native preview](../../sse_multivector/distillation-review-v1/README.md#complete-validation-workload-preview-october-9)
contains 1,800 outputs in 18 versions, with 142 invalid answers kept separate.
Mechanical rules settle 16,733 occurrences; 105,652 remaining occurrences contain
36,310 distinct semantic input questions under fixed prompts/settings, before
saved-answer reuse, warmups and retries. All per-note/version/model denominators
remain visible. Only evaluation reference content is decoded after checking the
mixed ledger's complete identity-header order; reserved files and checkpoint
weights are not opened. The report binds sources and counting code. This does
not prepare model requests, add inference, qualify reviewers, adjudicate A21,
change scoring or unseal test data.

**Validation review token and runtime estimate subsequently authorized October 9:**
the user authorizes an offline estimate of the remaining work, with zero new
model calls. The existing preview command gains `--estimate` and repeated
`--timing-experiment` inputs, requiring `tiktoken` only for estimation. The
[native estimate](../../sse_multivector/distillation-review-v1/README.md#validation-review-token-and-runtime-estimate-october-9)
binds the unchanged DSMv3/DSSv2/DSLv2 templates and verified fresh Sol / xhigh
receipts. The 36,310 distinct questions contain 24.195 million rendered input-text
tokens, versus 79.399 million across remaining occurrences, excluding provider
instructions, framing and output-schema overhead. Twenty matching, twenty support
and nineteen relationship verdicts project 15.050 million output tokens,
including reasoning once, and 15.34 service hours at eight continuously occupied
slots. The 10.86-hour median and 24.94-hour p90 scenarios are not confidence
bounds. These selected samples include disputed verdicts and mixed prefix-role
formats; configured concurrency does not establish measured slot occupancy or
batch wall time. Warmups, throttling, retries and review work are additional.

Current automatic template prefixes are 468/112/71 proxy tokens for matching,
support and relationships, all below the 1,024-token threshold. Separate natural
prefix analysis finds 19 matching and two support groups, with no eligible
relationship group: 21 hypothetical warmups contain 25,410 input-text tokens;
at most 4,757,034 proxy tokens could be cache reads, or 4,731,624 after a cold
first use. Hits are not guaranteed; the earlier eligible support sample had none.
Warmup output and request overhead are additional and not projected. This records
opportunities without adopting a cache mode or optimization. Prompts, mechanical
criteria, scoring, reviewer qualification, A21 and test sealing retain their
existing state; the estimate authorizes no inference.

**Complete-answer reviewer trial authorized October 9:** the user approves
running 50 randomized validation answers and 10 deliberately difficult answers
through the actual review workflow, including mechanical routing, reuse,
semantic checks and score assembly. Preserve DSMv3/DSSv2/DSLv2, trusted
ASv6.100, GPT-6.1 Sol / xhigh / subscription SSE and concurrency 8. Reuse the
previous manual eligible natural-prefix/key caching and native warmups; do not
enable automatic template-prefix caching or warm ineligible/single-use prefixes.
The pilot's reserved test remains sealed.

The frozen sample covers all 18 versions with seeded quotas of two or three
answers, preferring previously unused note identities. It contains 50 distinct
previously unused notes, including four truncated answers. The ten challenges
have distinct note identities and cycle teacher catalog size, nonexact composite
wording, student depth and same-note answer variation. Challenge results remain
separate from the randomized cohort; neither selection is a simple uniform
sample of all 1,800 outputs. Source hashes and selection policy are retained.

Candidate-independent teacher meaning groups and required flags are recorded
before answer assessments. Freeze independent agent-assessed expectations before
reviewer calls; they are not adjudicated gold. Preserve unresolved labels and
mechanical contradictions explicitly. Coverage uses the existing required-meaning
and every-compatible-heading rule, with unchanged DSLv2 comparing a candidate
heading as parent against the complete teacher meaning as child. Every numbered
occurrence is retained. The earlier primitive-check estimate excludes those
additional compatibility comparisons. New native project commands prepare,
inspect, assess, freeze, run and report the complete-answer trial through the
shared experiment runner. Reviewer extrapolation, lower reasoning effort and
bulk review adoption depend on the resulting evidence. See the
[trial record](../../sse_multivector/distillation-review-v1/README.md#complete-answer-reviewer-trial-october-9).

**Completed-check evidence, trial paused:** sealed references precede all
calls; all 958 mechanical proofs have been independently verified.
Matching and support finish with 569/591 and 585/600 resolved distinct semantic
agreements, excluding 24 and 15 unresolved inputs. Independent audits identify
four clear reviewer errors in each, preserving raw labels and separately
recording reference mistakes/ambiguities in 37 native agent reviews. Relationship
auditing has found two disjoint inconsistency families and explicit scoring
blockers. Matching caches 42.14% of comparison input; support has no reported
hits. A successfully retried transport interruption has unknown usage, so full
cost remains unknown. The user pauses the relationship phase to investigate
scalability; final qualification remains pending. The earlier runtime estimate
excludes compatibility: this trial adds 9,678 coverage requests to 2,086 primitive
checks. Saved matching decisions leave 278 of 513 required-meaning/answer groups
without a full match; their coverage fails regardless of placement. Omitting
only that work would save 5,764 requests across the whole selected workload,
conditional on the saved DSM decisions. At the pause, no execution or exhaustive-report contract had
changed; all completed receipts are preserved and workers have exited. See the
trial record for the paused native counts and investigation boundaries;
this evidence approves no prompt revision, lower effort, bulk grading or test
unsealing.

**Additional mechanical review implementation approved October 9:** the user
directs doing all sensible mechanical work. Exact endpoints of any numbered
trusted teacher ancestor path supply a positive DSL result with the original
path witness. Matching/support still require exact teacher wording or semantic
review; a model-confirmed match does not prove either other check. Missing exact
teacher placements do not certify negative relationships when an equivalent
paraphrase might represent the meaning.

New schema-2 evaluation preparations omit score-irrelevant questions after
completed matching/support: compatibility for required meanings with no full
match, compatibility of proper ancestors already containing a full match,
remaining placements after a compatible uncovered witness, and incoming edges
of unsupported subjects. Retain all matching-self compatibility checks and
already completed verdicts; contradictions block scores. These rules preserve
the score law conditional on the decisions used, without asserting those
semantic decisions are correct. Skipped rows carry status/rule/dependencies,
no invented Boolean and no qualification pass. Complete scores may have
incomplete diagnostics and reviewer qualification.

The shared runner supports selected frozen dispatch and suppression of repeated
warmups within one logical invocation; prompts, Sol/xhigh, concurrency 8,
natural-prefix eligibility, native reuse, budgets and provider-only retries
remain fixed. Schema-1 selections verify their original accounting; new
selections include path proofs. Prepare a separate evaluation against the same
selection/assessment and history; no original frozen input or receipt is
rewritten. A zero new-attempt allowance joins verified saved results without
inference. The trial remains paused, reviewer qualification and bulk adoption
remain open, and reserved test data stays sealed. The
[implementation record](../../sse_multivector/distillation-review-v1/README.md#additional-mechanical-review-work-approved-october-9)
retains measured savings and their conditional limits.

**Reasoning-level study approved October 9:** after accepting the mechanical
changes, the user authorizes finishing the same 60-answer trial at Sol/xhigh.
After completion, screen lower reasoning levels on a small subset, then expand
the lowest promising effort until all 60 answers are reviewed at that level.
If correctness degrades significantly, stop that effort and step back up one
level. The user explicitly accepts up to **2 percentage points** of correctness
loss versus xhigh. Compare reviewer judgments against source evidence; student
scores and xhigh agreement alone do not establish reviewer accuracy. Prompts,
data, mechanical rules, concurrency 8 and eligible natural-prefix caching stay
fixed. Preserve frozen references and original receipts. Bulk pilot grading and
reserved-test access remain unapproved. See the
[study record](../../sse_multivector/distillation-review-v1/README.md#reasoning-level-comparison-approved-october-9).

**October 10 execution checkpoint:** the same60 xhigh pipeline has finished.
It yields 43 complete scores, 13 ungraded reviewer contradictions and four
invalid student outputs. All 1,735 fixed-panel xhigh decisions are verified
and frozen before lower-effort calls. Independent source-only diagnosis of the
contradictions is continuing; reviewer qualification remains open. The
[completion evidence](../../sse_multivector/distillation-review-v1/README.md#xhigh-completion-and-baseline-freeze-october-10)
keeps pipeline work and supplemental panel calls separate. This checkpoint
adds no change to the approved prompts, semantics, mechanical rules or scope.

**October 10 lower-effort checkpoint:** the initial high screen has 297 complete
paired decisions, of which 289 agree with the frozen xhigh baseline. Source
adjudication now finds six high-only errors and two unresolved differences
(H=6, G=0, A=2): a 1.35–2.69 percentage-point overall loss bound, with larger
losses in support and teacher/student compatibility. High has not cleared this
small screen. This bound covers truth uncertainty, not statistical confidence.
No effort has qualified.
All 60 original source-only diagnostic judgments are preserved separately from
final exact-prompt adjudications. The [screen record](../../sse_multivector/distillation-review-v1/README.md#initial-high-effort-screen-october-10)
keeps adaptive pipeline expenses and supplemental panel calls separate. This is
an execution checkpoint; it changes no scoring rule, prompt or approval scope.

**October 10 medium checkpoint:** the same 297-question screen is complete,
with 285 agreements and 12 discordances. Source adjudication finds H=8, G=2,
A=2, giving a 1.35–2.69 percentage-point loss range, the same overall range as
high. Both relationship roles have larger losses. These bounds describe truth
uncertainty, not statistical confidence or population reliability. The fixed
chosen-response catalog estimate is 57.8% lower than xhigh's; shared warmups
and adaptive pipeline expenses remain separate. The
[medium screen record](../../sse_multivector/distillation-review-v1/README.md#initial-medium-effort-screen-october-10)
preserves the source assessment, cost comparison and role investigation.
Prompts, frozen references, mechanical rules and approval scope remain unchanged.

**October 10 low screen and next investigation:** all 297 paired questions are
complete, with 283 agreements and source-adjudicated H=10, G=1, A=3. The
2.02–4.04 percentage-point loss range and an independently checked specific
failure across two notes rule out expanding low. Medium was selected for the
frozen 10-answer investigation with 405 distinct questions, with high as its
fallback. No effort has qualified. This implements the
approved study, with unchanged prompts, rules and controls; it adds no release
policy or population guarantee. The
[low results and selection record](../../sse_multivector/distillation-review-v1/README.md#initial-low-effort-screen-and-next-stage-selection-october-10)
preserves the exact source assessments, original receipts and separate costs.

**October 10 ten-answer medium checkpoint:** the fixed 405-question comparison
is complete, retaining all prior 297 chosen answers and receipts. Source
adjudication finds H=11, G=3, A=4 and a 0.99–2.96 percentage-point loss range.
A specific added main-occurrence/action requirement recurs in compatibility
across R01 and R21; actual student parent-child failures for this mechanism
remain on R01 only. This triggered high on the same frozen 10 answers under
the existing step-up rule.
The numerical range alone is borderline; the verified recurring mechanism
requires stepping up. Role losses trigger investigation, without adding
per-role numerical acceptance thresholds.
No medium 20-answer expansion or qualification is established. The
[ten-answer record](../../sse_multivector/distillation-review-v1/README.md#ten-answer-medium-investigation-october-10)
preserves source uncertainty, the specific failure audit and separate costs.

**October 10 high result and xhigh selection:** high's same 405-question
comparison is complete: 392 agreements, H=8, G=1, A=4 and a 0.74–2.72
percentage-point loss range. The net loss is 7/405, or 1.73 points, within the
accepted two-point margin; the numerical range alone would prompt expansion.
The same explicit added main-subject/action requirement recurs across R01 and
R21, independently triggering the approved step-up rule. Compatibility alone
spans both notes; actual student parent-child failures for this mechanism
remain on R01 only. Role losses require investigation, without new per-role
acceptance thresholds.

The sealed decision retains the already-complete frozen Sol/xhigh baseline
of 60 answers and 1,735 questions, requiring no new calls. Low stopped at five
answers; medium and high stopped at ten. None qualified, and no lower-effort
20/40/60 expansion is authorized. Stopping early does not establish that a
lower effort would lose more than two points on the full 60 or in deployment.
The requested lower-than-xhigh result remains unachieved; this is not goal
completion or reviewer qualification. Prompts, data, rules and controls remain
unchanged; bulk pilot grading and reserved-test access remain unapproved. The
[final checkpoint and decision evidence](../../sse_multivector/distillation-review-v1/README.md#ten-answer-high-result-and-xhigh-selection-october-10)
preserve unresolved truths, source assessments and separate receipt costs.

**October 1 observation and transfer design approved:** the assistant observes
from launch through verified retrieval and explicit deletion, inspecting actual
subject responses during baseline before training, training progress
and GPU telemetry, and trained outputs as they arrive.
One background copier transfers subject responses and checkpoints
as soon as saving finishes while the experiment continues. Verify each local
copy and retain remote originals at least until verification. Limit transfer
bandwidth and disk activity to protect experiment throughput. This records the
intended design. The subject-response and checkpoint accounting checks are now
implemented. The copier implementation is recorded below.

**October 1 training-continuation correction approved:** the user requested
removing the separate fresh starts. The larger pilot uses **one continuing
training run per student**, with validation checkpoints every 200 training
notes through 1,000, approved October 1. Initialize each adapter and optimizer
once; carry learned weights, optimizer, learning-rate schedule, random state
and data-order position forward.
Save complete checkpoints and verify adapter reloads. At each milestone,
generate subject hierarchies on the same held-out validation notes without
updating training weights. The five checkpoints at **200, 400, 600, 800, and
1,000 notes** give fifteen trained versions across the three students, plus
three untuned baselines. With the proposed 100 validation notes, that is
1,800 note/model evaluations and semantic reviews, all with thinking off.
The schedule adds 600 subject evaluations over the earlier proposal. Training
labels are shared across checkpoints.
Reusing training state does not itself require repeating earlier notes or
establish a reduction in training compute. The complete-pass training amount and
stage allocation and batch construction were subsequently approved below.
Block membership, seed 17, model settings and the 100/200 validation/test
counts are now frozen by the subsequent approvals. Loss was subsequently approved below. This corrects the
intended design. The subjects-only continuation is now implemented locally;
execution and fit on the selected GPU still need preparation evidence.
No rental, model calls, or spending is authorized by this correction.

**October 1 complete-pass training budget approved after research:** use every
frozen subject-hierarchy training example **once, without replacement**.
Introduce five new 200-note blocks and finish each block's examples before its
checkpoint. Continue the same adapter, optimizer, schedule, random state and
data-order position; earlier blocks are not automatically replayed.
Check actual example coverage at every milestone. Record subject loss and
supervised tokens; block membership and seed value remain open. Loss, numerical
settings and additional MoE adapter coverage were subsequently approved below.
The subjects-only rows differ from the
preliminary 20/80 replacement sampler. One pass is a modest starting budget,
not an established optimum or a comparison of each architecture's maximum
capability. Select from generated correctness, coverage and output reliability;
loss remains a diagnostic. Implementation, spending and launch are separate
decisions.

**October 1 training-batch construction approved, scoped to subjects October 2:**
collect every subject example from the current 200-note block and shuffle using a
fixed random seed. Take consecutive groups of **N prompt–answer examples per
adapter update**, including a smaller final group when needed. Use each example
once and finish the block before its checkpoint. An update can include examples
from different notes. Freeze
the seed and save the data-order position so continuation preserves the same stream.
N was subsequently selected as 8 below; the seed value and block membership
remain open. This approves the batch construction design; loss was subsequently
approved below and implementation is separate.

**October 1 starting training settings approved after comparable-experiment research:**
all three students use **8 prompt–answer examples per adapter update, total across
all GPUs; constant learning rate 0.0001 with no warmup; LoRA rank 16 / alpha 32**.
Retain a smaller final group and the approved one-pass, five-block continuation.
These are a reasonable shared starting recipe, not established optima or each
model's maximum attainable quality. The later expert decision below specifies
Gemma MoE's additional adapter coverage and rank; the informal configuration
still leaves routed experts frozen. Loss was subsequently approved below.
The later numerical decision below settles optimizer, precision and LoRA defaults.
Block membership, seed value and spending remain open.
This approves the intended settings; the
legacy 128-step replacement sampler retains its earlier recipe. Local
implementation of the continuing subjects-only worker was subsequently
authorized and is recorded below. Launch requires separate authorization.

**October 1 Gemma MoE expert adapters approved:** add adapters to every routed
expert's gate/up and down projections at **rank 2 / alpha 32**, retaining
**rank 16 / alpha 32** for attention and shared MLP adapters. Keep original model
weights, router projection, and router scales frozen. The expert rank applies the
[controlled MoE study's active-expert convention](https://thinkingmachines.ai/blog/lora/):
nominal rank 16 divided by eight active experts. It is a research-grounded starting
choice transferred to Gemma, not a measured optimum for this task. The larger
pilot tests this single chosen MoE recipe. The continuing subjects-only worker
now targets both packed expert projections in every Gemma MoE layer at the
approved rank and alpha. Remaining runtime choices and GPU fit stay open.

**October 1 training loss approved after research:** use ordinary cross-entropy
on teacher-answer and native turn-ending tokens. For each adapter update, sum
these token losses across all its examples and divide by the actual number of
supervised tokens in that update. Prompt text, the note,
and padding receive no prediction loss. Use the actual denominator for a smaller
final group; splitting an update across GPUs or accumulated batches must preserve
this objective. Apply no additional task, answer, or note weighting. Longer
answers contribute more tokens within an update. Record subject loss,
supervised-token counts, and actual
example coverage. The [normalization guidance](https://huggingface.co/blog/gradient_accumulation)
and [comparable extraction implementation](https://github.com/hitz-zentroa/GoLLIE/blob/164c611743fdc1befe71bbdf03e08c5eb4e35957/src/trainer.py#L288-L300)
support this starting objective. This approves the larger-pilot design; implementation and verification
remain separate work.

**October 1 optimizer, precision and LoRA defaults approved:** retain PyTorch
AdamW (`adamw_torch`) with beta1 0.9, beta2 0.999, epsilon 1e-8, weight decay 0,
and aggregate gradient-norm clipping at 1 after accumulation and before each
adapter update. Load the frozen base in unquantized BF16 and use BF16 mixed
precision computation, retaining normal FP32-sensitive operations. Store LoRA
weights, their gradients and Adam moments in FP32. Retain LoRA dropout 0,
frozen biases (`bias="none"`, `lora_bias=False`), standard PEFT initialization
(`init_lora_weights=True`, Kaiming-uniform A and zero B), and ordinary alpha/r
scaling. The initial adapter contribution is zero. These carry forward the
preliminary numerical setup and supported defaults, not task-specific optima;
see [Trainer defaults](https://huggingface.co/docs/transformers/v5.17.0/en/main_classes/trainer)
and [PEFT precision guidance](https://huggingface.co/docs/peft/v0.21.0/en/developer_guides/troubleshooting#selecting-the-dtype-of-the-adapter).
Record these settings explicitly in the larger-pilot configuration. Hardware,
physical batch allocation, generation settings, runtime choices, exact expanded
MoE GPU fit, implementation and spending remain open. The later checkpoint
decision below settles merged BF16 validation and the save/evaluate/resume flow.

**October 2 checkpoint evaluation and resume approved:** at each completed
200-note block, finish the final adapter update, save the full unmerged training
checkpoint, and verify its files before publishing completion. Preserve the
adapter, optimizer, schedule, random state, update count and exact next-example
position; retain all five complete milestone checkpoints per student.
Release training from the GPU, load a fresh original pinned BF16 base with that
saved adapter, and merge its learned changes into this disposable evaluation
copy. Use this policy for all three students and every trained checkpoint;
untuned baselines use the original base. Verify saved-adapter reloads under the
selected inference policy; merged/unmerged BF16 answers need not be identical.
Generate validation subject hierarchies, preserve raw and parsed
responses, account for every expected note response immediately, and transfer finished files
with the approved background copier. Missing work or pipeline defects block
advancement; invalid model answers remain measured failures.
Discard the evaluation copy and restore the untouched full training checkpoint,
including random state after reconstruction, before using the next example.
Merging/unmerging the continuing BF16 training base is excluded. This keeps one
copy of that student's model resident at a time and adds cached-base reloads between stages.
Separate GPU preparation must verify the save/merge/evaluate/resume transition,
continuation, merge peak memory and elapsed overhead. The [PEFT expert-adapter
guidance](https://huggingface.co/docs/peft/v0.21.0/en/package_reference/lora#targeting-nnparameter-directly)
supports merging to remove generation overhead. The subjects-only worker now
retains all configured milestone checkpoints, evaluates a freshly merged copy,
and restores the full unmerged training state for the next block. The legacy
two-task recipe retains its endpoint evaluation and rolling checkpoints.
Generation limits, numeric batching budgets, preparation spending and launch
stay open.

**October 2 continuing subjects-only worker:** the user authorized local
implementation and VM verification. Offline preparation accepts subjects-only
labels without mask data or a mask prompt. Freeze block membership and shuffle
within each block; use every example once. Each eight-example update uses one
supervised-token denominator, with the actual smaller final group when needed.
Save adapters, Adam state, constant schedule, Python/NumPy/Torch/CUDA random
state, exact cursor and consumed-note IDs at each retained milestone. Validate
required checkpoint files, hashes, identities and update counts; check every
expected raw/parsed subject response before advancing. Reload adapters on a
fresh original base, verify saved weights, merge the disposable evaluation copy,
then restore untouched training state. Verification passed **29 host checks and
48 tests in the pinned VM container**, including all three tiny architectures
and full five-checkpoint jobs through shared SSH deployment/retrieval.
Intervening evaluation and recovery from interrupted response publication
preserved exact CPU adapter weights, Adam state, schedule, random state and
coverage. Unequal-length answers preserved the token objective across physical
groups of one or eight; missing responses and invalid checkpoint counters
blocked advancement. All twelve retrieved evaluation stages and ten checkpoints
reverified locally, and the VM is stopped. These tiny CPU checks do not establish
BF16 GPU fit or throughput. Ongoing transfer implementation is recorded below.

**October 2 background copying implemented locally:** the user authorized
implementation and VM verification of transfers during training. Subjects-only
evaluation publishes a completion record for each raw/parsed note response.
The shared frozen Vast operator starts one separate local copier under
`run --watch`. It discovers published responses and checkpoints, transfers
only new bytes with low remote CPU/disk priority and a frozen bandwidth limit,
verifies SHA256 and size before local publication, and retains remote originals.
Interrupted files retain their received bytes for resumption. Existing verified
files are reused; integrity failures retain evidence and are reported without
stopping training or deleting the instance. Final retrieval uses the original
terminal seal, reuses verified copies, and validates the complete retrieved file
set. Copy controls are explicit and frozen: software defaults are five-second
polling, 8 MiB/s and a 900-second transfer timeout. They are operational defaults,
not a measured throughput optimum or an approved rental configuration. GPU
impact and the larger pilot's complete checkpoint/transfer allowance still need
preparation evidence. Verification
passed 129 shared-controller regression tests, 27 host distillation checks and
50 tests in the pinned VM container. Real SSH execution transferred raw/parsed
responses and a complete checkpoint while training was running. Final retrieval
reused 174 work files and all 246 work files plus six preparation files reverified
locally. Partial reception, receipt loss, corrupt data, bandwidth limits and
copier start/status/exit failures were checked; copy failures did not stop
training. The final container export passed and the VM is stopped.

**October 2 thinking-off decision approved:** after reviewing comparable
research, the user chose thinking off throughout pilot preparation, answer-only
training, all three untuned validation baselines, all five checkpoints and the
selected adapter's matched untuned/fine-tuned final test. Remove the three
previously planned terminal thinking-on evaluations. With N validation notes,
there are **18N** subject responses and semantic reviews; at the proposed 100
notes, **1,800**. The proposed 200-note final comparison adds 400 responses and
reviews under that decision; the October 5 final-test decision below expands
the comparison to all three final adapters and baselines. Comparable research
does not establish the benefit of enabling thinking
after our particular answer-only fine-tune. Output limits, numeric batching
budgets, preparation scope, spending and launch remain open.

**Separate paid GPU preparation agreed October 1; confirmed October 3:** use
existing notes for a small preparation run while the larger pilot data is pending.
Prepare candidate settings and exact checks locally and rehearse the packaged
workflow before booking. The proposed minimum checks an adapter update,
checkpoint save/reload/merge, brief batched generation plus the maximum admitted
memory shape, and a further update after restoring training. Full hierarchy
comparisons, output-quality review and tuning sweeps are outside this preparation.
The proposed cases and cache method are now implemented and rehearsed locally.
This is not GPU evidence. Preparation verifies only its tested input/output
bounds; it cannot establish completeness of future pilot answers. When the real
data arrives, tokenize it locally against those bounds before the main rental.
Out-of-bounds data requires reconsidering the configuration locally.
The pilot runs its settled training and evaluation procedure. The exact frozen
preparation proposal, specific rental offer, maximum charge and launch approval
remain open; separate preparation in principle does not authorize a rental commitment.

**October 3 preparation cost priority approved:** minimize total billed preparation
cost on the selected 96GB GPU. Collect training, batched generation and lifecycle
timings during the same required checks to estimate the pilot's GPU duration/cost
range. Keep parser/recovery tests and automation rehearsal local; avoid adding
separate benchmarks, complete hierarchy comparisons or tuning sweeps. Compare
qualifying offers by expected total charge, including startup, storage and transfers.
Retrieve and verify the evidence, then explicitly delete promptly after checks
finish. Exact scope, offer and maximum spending approval remain open.

**October 3 local preparation implementation:** the existing runner now has an
explicit preparation mode. The frozen proposal selects 16 existing training
notes per student for two eight-example updates, puts the longest training
example after restoration, and performs one save/reload/merge/generate/restore
cycle. It saves brief subject responses separately, capped at 64 tokens, for the
20 existing evaluation notes. Native forwards fill the generation cache in
128-token chunks and check final decode at the full 4,096-token allowance;
synthetic continuation is memory evidence only. Timings and CUDA peaks come
from the same checks. The numerical memory policy remains a proposal.
The revised local VM rehearsal passed 55 tests, including the pinned real
tokenizers and timeout-free managed SSH deployment/retrieval; 65 local controller
checks passed. The user approved proceeding with the $5 preparation on
October 3. The exact VM image is now published and verified private, including
read-only pull and anonymous rejection. The refreshed selected compatible
600 W quote is offer [private ID removed] on machine [private ID removed] at $1.4522/hour including storage.
Three planned hours with transfer allowances cost $4.41, within the approved $5;
the $7 request is withdrawn. The original transfer-fee ceiling was unnecessarily
strict: the revised ceilings still prove admission under $5. All existing
hardware filters were satisfied.  Vast definitively rejected the request with HTTP 400. The unchanged operator completed its inventory
recovery and recorded no instance and zero charge; independent authenticated
inventory was empty.  No GPU preparation checks
ran. The helper did not retain the provider explanation, so the exact rejection
cause is unknown. That quote is no longer available. The user then approved
revised selection filters and proceeding within $5: 125 GiB host RAM and
450 Mbps download floors, with price/transfer ceilings that jointly fit $5.
A better refreshed 96GB/600 W quote is offer [private ID removed] on machine [private ID removed] at
$1.4656/hour including storage and $4.40 for three planned hours including
transfers. It also meets the original hardware floors. The tested private image and native package remain unchanged; a new frozen operation was prepared. On October 3, managed SSH, package verification and automatic worker startup succeeded. Qwen completed both updates, 20 brief responses and four cache
checks. Gemma dense completed its first update but failed before generation:
its head dimension differs by attention layer, and the batch-memory calculation
incorrectly read the global configuration. MoE never started. Retrieval and
independent rehashing account for all 125 work files and six startup files.

The preparation cost was initially estimated at $1.56 and later updated to $1.620. The final preparation cost was $1.620. This attempt left required Gemma work incomplete; the repaired run below completed it. No automatic timeout or
deletion occurred. Budget overruns must trigger a direct chat update, never an
automatic stop. Ask questions directly in chat; do not use question tools.

The minimal local production-path test reproduces the same per-layer attribute
error for both Gemma variants. The fix reads each layer's cache dimensions and
keeps the existing batching interface; integrated tiny-model lifecycle checks
now use distinct full/sliding head dimensions. Local pinned-image checks pass
50 tests, with nine deployment-VM tests skipped. The old package/image/results
remain immutable. The rebuilt VM subsequently passed all 56 tests, including
managed SSH, tokenizer preflights and verified retrieval, with source hashes
matching the committed repair. The corrected package subsequently completed the remaining Gemma checks,
recorded below. The first failure did not establish an OOM. The measured
preparation shapes do not settle full pilot data fit or duration/cost.
See the technical plan's
[preparation package](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md#small-gpu-preparation--local-package-ready-october-3).

**October 3 prep stopping exception approved by the user:** repair straightforward
failures immediately. If recovery requires substantial work, preserve and verify
all available data, then delete the prep rental promptly. This is standing user
approval to stop incomplete prep work; do not hold an idle rental while seeking
renewed approval or developing a substantial recovery change. The agent judges
repair scope; no fixed time cutoff was approved.

**GPU preparation completed October 3:** Qwen's verified earlier checks were reused; Gemma dense and MoE both completed two updates, save/reload/merge, 20 brief subject responses, native maximum-output cache checks and restored training on 96GB/600 W hardware at $1.4153/hour including storage. All 210 work files and six startup files
were retrieved and independently rehashed.  This rental lasted 65.5 minutes.
The two preparation runs cost $1.756 and $1.620, $3.376 combined.  

Direct SSH copying was slow; the verified provider proxy route completed retrieval using
the unchanged native transfer code. Small sealed responses and measurements were copied
ahead of remaining checkpoints. Frozen remote code, inputs and operation contract stayed
unchanged. The October 3 launcher update selects the provider proxy from the start
for new distillation operations, honoring an explicit direct SSH setting when supplied.
Both progressive and final transfers prioritize small sealed outputs, copying each
completion marker after its files. Streams carry at most 64 MiB; the background
copier rediscovers sealed files between streams so newly saved responses can
precede an unfinished checkpoint. Partial files are retained and checked
against the complete saved SHA256 before publication. New launches require a fresh
package and image from the updated source; historical operations stay frozen. Future
pilot data must fit the measured training and cache shapes. Rentals below $1.60/hour
need no further approval for the authorized prep; straightforward failures are repaired
promptly, otherwise available data is verified and the prep rental explicitly deleted.
No automatic timeout or deletion.

**Full pilot stopping rule:** never terminate the
fine-tuning job or its rental until all necessary data is complete, retrieved
and verified locally. If data is missing, retain the resource and add the work.
If stopping is preferable, ask for explicit user approval first. This withdraws
the proposed 2.5-hour worker deadline. Elapsed time, watcher errors/interruption
and spending alerts do not authorize termination. Continue observation until
verified retrieval and explicit deletion. Spending approval remains separate;
request extensions early when necessary.
The rebuilt package disables its execution timeout. The shared watcher no longer
stops this workload on expiry/error/interrupt, and both `stop` and direct deletion
require a recorded completeness review bound to the operation, instance and
verified retrieval. The operator rechecks local files. An incomplete stop
requires the actual user-approved reason and records that exception. For prep,
record the standing approval and the concrete failure/repair assessment using
`--incomplete-stop-approval`. Original frozen inputs and defect evidence remain
intact when additional work is needed.

**Autonomous pilot recovery approved October 5:** diagnose and fix errors
without asking the user to approve the repair, including necessary code or recipe
corrections. Preserve original frozen inputs and failure evidence, record each
change and interruption, restore verified saved state, and rerun comparisons
affected by changed conditions. This authorizes repairs; the approved spending
and complete-data requirements before stopping/deletion remain in force.

**Training-data reuse clarified September 30; milestones approved October 1:**
each larger training set retains the earlier notes and labels. Add 200 new
notes at each milestone through 1,000; the smaller sets are shared subsets.
Evaluation-note counts, rental grouping, duration, and spending remain open.

**September 25 informal start:** the user approved beginning the fine-tuning
pilot with available data from the latest subject and mask prompts, excluding
prominence for now and establishing untuned baselines. The teachers generate
subjects and masks. The user subsequently approved one fine-tune per candidate
on both existing prompted tasks: note → subject hierarchy, then note + subject
→ mask. Both tasks train the same model or adapter. Baseline and trained
evaluation each use that candidate's own generated subjects for the mask calls.
The user approved batching independent evaluation mask requests, with the same
batching and generation settings before and after training. The current recipe
uses up to four masks from one note per batch; training settings are unchanged.
Direct-mask generation is deferred for this informal pilot.
This initial informal experiment may use current saved annotations before
prominence and final teacher selection are ready. Local data is prepared;
the first September 29 rental stopped after an agent monitoring error, with no
completed baseline or training. Retrieval and deletion were verified. The
approved replacement subsequently completed Qwen's baseline, training, reload
check and trained evaluation; setup task 18 is complete, not model selection. See
[current pilot preparation](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md#status-and-scope).
Whether the release model needs prominence or other sorting-related outputs is
undecided. Candidate selection, the larger pilot's evaluation requirements,
full-data gates and paid-resource approval rules remain in force; the informal
result does not complete 06.
The user approved automating and testing the complete workflow in a local VM
before deploying on rented hardware. The local test uses a tiny model and
synthetic data, including actual weight updates, checkpoint interruption/resume,
save/reload and two-step evaluation. The local workflow tests passed;
interrupted training reproduced the uninterrupted adapter weights exactly.
The user clarified that the VM must rehearse the deployment process used on
Vast: prepare an immutable image and frozen inputs locally, upload the inputs,
start the experiment automatically, reconnect and retrieve verified results.
The approved integration uses the successful September 27 shared Vast runner
(`vast/runner.py`) for creation, managed SSH, transfers, execution, retrieval and
verified destruction. It replaces the separate distillation provider controller
and SSH operator. Managed SSH uses `ssh-keygen -A && service ssh start`; the
workload explicitly supplies its Python and runtime environment. The VM
rehearses the shared remote path against a separate container; provider calls
remain simulated. The current `run --watch` resumes command workloads through
execution and retrieval while its local process remains alive. Automatic
deletion was removed at the user's request after the first rental failed.
Completion and failures retain the instance. On expiry or interruption, the
watcher requests a workload stop and attempts retrieval without deleting the
instance, including when SSH is unavailable. Only an explicit `stop` command
deletes it. Billing continues until deletion; the operator must act within the
approved rental and spending limits. Local interruption requires resuming the
saved operation. No code edits or package
installs belong on a running rental. These tests cannot guarantee GPU execution
or provider availability. Candidate
quality, full-model memory use and CUDA compatibility are checked during
the actual pilot, without a separate throwaway GPU training run. Candidate
recipes and Vast limits are now frozen locally: BF16 LoRA, 128 steps per
candidate and one 96 GB GPU. On September 29 the user authorized publication
and one rental, then approved up to $1.66/hour including storage for at most
13 hours, retaining the 12-hour worker window and $25 total. The full planned
allowance is $23.78 including transfers. The exact tested image is published and its identity and read-only pulling are verified; launch-specific settings record the approved limits without changing the image.  The September 29 configuration cost $1.6555555556/hour including 300 GB storage. Image startup, direct SSH and
frozen-input verification passed. Qwen preflight and weight download completed. A local agent monitoring import
then wrote an unexpected Python cache file into the frozen transport. The supervisor rejected the changed file set, stopped the workload and verified retrieval. No baseline output or training
completed, and no GPU failure was reported. The cache is preserved outside
transport; its original manifest verifies, including after a bytecode-disabled
local import. Preliminary charges were $0.338. The final cost of the failed run was $0.395.
The manual-deletion policy is implemented and regression-tested locally. On
September 29, the rebuilt image and `package-v9` passed all 24 local VM tests,
including real SSH training/retrieval and all three candidate preflights. The
VM reused its disk and dependency cache with a new source snapshot. Tiny-model
weights and evaluation metrics match the prior rehearsal exactly. The rebuilt image is published and verified private; read-only image pulling is verified for its immutable digest. The user then approved proceeding and explicitly required
continuous observation throughout the rental. The operator must observe startup,
execution, retrieval and explicit deletion within the approved limits.
A 30-minute watch found no eligible 600 W offer. The user then approved the
450 W RTX PRO 6000 WS alternative: the same 96 GB GPU, with lower power that
may reduce speed; all other frozen offer checks pass. The launch-specific
`approved-settings-450w.json` overrides only that power requirement in addition
to the prior price/time overrides. The experiment used a $1.4167/hour configuration including 300 GB storage. All three candidates completed their 20-note baseline attempts,
128-step training, matching adapter reloads and trained evaluations in the frozen
image and package. The worker exited successfully on September 30 at 02:56:58
UTC. Retrieval of 671 work files was hash-verified, and local output verification passed. 
Teacher-agreement `f1_80` was 0.333 before and 0.346 after training for Qwen;
trained scores were 0.397 for Gemma dense and 0.313 for Gemma MoE. All 20
untuned subject responses from each Gemma candidate had Markdown code fences
and failed strict JSON parsing, producing zero baseline scores and no baseline
mask calls. Those comparisons therefore include formatting gains; semantic
quality review and model selection remain open. The user subsequently requested
parser support for Markdown-fenced JSON to recover the Gemma baselines. Subject
and position-mask decoding now accept bare JSON or one complete JSON/unlabelled
code fence, retaining duplicate-key, hierarchy and position validation. Replaying
saved answers with this decoder raises Qwen's baseline F1 to 0.344 and reduces
its baseline mask failures from 22 to 11; all three trained scores are unchanged.
All 40 saved Gemma subject answers validate, exposing 290 dense and 328 MoE
subjects. Completing their baselines requires generating those 618 missing
masks with the untuned models; training need not be repeated. New paid work
requires approval of its maximum charge under the repository spending rules.
GPU telemetry has 553 periodic
samples, including recorded sampling gaps. Preliminary charges for this run were $13.392.  The prior failed run's preliminary cost was $0.338. Posted charges for the two experiment runs totaled $13.73, within the unchanged $25 experiment maximum.
The old frozen operation and published image remain unchanged.
The user accepted a $25 total maximum for GPU setup, baselines and initial
fine-tunes across the three candidates, including storage, transfers and failed
attempts. Budget admission passed before the run; no replacement rental is authorized without discussing any failure with the user.

- **Teacher-comparison pilot (17):** choose the teachers that write the training
  data. GPT-6.1 Sol low is provisionally favored for SP, and GPT-6.1 Sol medium
  for grouped masks. Final selection remains open. Assess subjects, masks, any
  agreed additional outputs and the resulting hierarchies, along with generation
  time, cost and feasibility. How unsuitable annotations are handled remains
  open; repairing them is not an assumed workflow. Check the
  provider's data-use and output-use terms before producing training data at
  scale.
- **Larger fine-tuning pilot (06):** compare the pretrained models that we will
  train on those annotations and release as the distilled model. This is the
  [existing fine-tuning pilot](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md),
  not the teacher selection. Its preliminary 100-note experiment is tracked in 29.

**Historical conditional batched GPU reference (October 3):** the completed prep measured
all three subject-only setups on a 96GB/600 W RTX PRO 6000. Combining its
ASv6.48 batch shapes and incremental-token timings with saved historical answer
lengths gives about **5.6 hours training** and **22–24.5 hours generation** for
three baselines, fifteen validation checkpoints and only the winner's final
comparison. Assuming the proposed 100 validation / 200 final test notes,
1–2 hours extra lifecycle/startup/retrieval allowance, 25% headroom and $1
transfer fees gives **36–40 hours / $51–58** at the prep's historical $1.4153/hour;
an illustrative $1.60/hour gives $58–65. Brief generation plus a single long-cache
decode step is a projection, not measured full-output throughput. No full-pilot
spending is authorized. This former winner-only calculation does not price the
approved six-version final test or the frozen ASv6.100 inputs. The earlier preparation cost $3.376 combined.

**Subject prompt frozen for the pilot (October 4):** the user selected the full
[ASv6.100](../../sse_multivector/subject-prompt-goal-v1/asv6.100/ASv6.100.md),
including all worked examples, for training, untuned baselines, checkpoint
validation and final testing. Source SHA-256:
`76aa2c831ab6d65802de4c76a960f8618c7ec7ee4cd62e619621ec8a453b095d`.
This settles the pilot SP version. Record that version and hash in future
pilot data/package manifests. Historical ASv6.48 packages and results stay frozen.

**ASv6.100 input audit (October 4):** offline native tokenizer checks on the
existing 80 training / 20 held-out notes find 9,210–9,651 Qwen prompt tokens and
9,041–9,495 Gemma prompt tokens. With the existing 4,096-token output allowance,
the largest totals are 13,747 / 13,591. The 8,192-token preflight rejects all
three students; a 16,384-token context passes token checks on this diagnostic
collection. Old teacher answers were used solely to measure lengths, not as
pilot labels. Actual pilot notes/ASv6.100 labels were unavailable then; the
October 5 full-data audit below supersedes these diagnostic length bounds.

The current 88-GiB memory policy predicts one-note requirements of
88.32–91.50 GiB for Qwen, 110.70–115.27 GiB for dense Gemma and 75.27–77.55 GiB
for Gemma MoE. It rejects Qwen and dense Gemma even at batch size one.
These are planner calculations, not measured GPU requirements or proof of OOM.
Increasing the context limit alone does not establish that the worker can run.
Context/memory settings and the launch estimate still need updating for the full
ASv6.100 prompt; the ASv6.48 cost reference above does not price this pilot.

**Pilot data generation approved October 4:** select **1,000 train / 100 validation /
200 final test** notes by extending the existing fresh-corpus random hash draw.
Preserve complete original readable-English root posts and provenance; exclude
replies (including address-tag replies), quote posts, mixed-language prose, inline
Nostr note references and posts exceeding 512 SSE tokens. Check the existing
16 writing forms at their natural proportions, without topic or form quotas.
Keep authors and related copies within one split; known prompt-development
authors and repeated development templates belong in training. Freeze selection
and splits before teacher inference.

Generate all 1,300 SP labels using full frozen ASv6.100 with the tested
**GPT-6.1 Sol / medium** subscription configuration, native experiment workflow
and raw/parsed/receipt preservation. **32 concurrent calls** are approved; reduce
to 24 if limits or transport problems require it. No paid API fallback. This
settles the pilot-label teacher, not the general teacher comparison. Student
thinking stays off. The 1,300-note selection is frozen and verified; label
generation is authorized. All 16 writing forms occur in the full sample. Known
exposure checks cover 716 saved source files, with zero holdout conflicts;
original texts/authors match and full-post SSE lengths range from 2 to 505 tokens.
Validation contains no CREATIVE-form notes in this natural draw; final test has six.
The review rubric, context/memory settings and rental were open at that point.
The semantic method and DSRv1 reviewer decision are recorded above. The
final-test collection arrangement was subsequently settled on October 5 below.

**Pilot label generation complete October 5:** the initial WebSocket run at 32 concurrency saved 39 valid answers and 99 failed handshakes, with zero frames/bytes for those failures; failed handshakes reported HTTP 403. Its 138 attempts and
all receipts remain saved. The 1,162 untouched notes completed over SSE transport
at 24 concurrency, without failed attempts or retries. The user then explicitly
approved completing the 99 missing labels over SSE at 24, granting that exception
to the unknown-cause retry restriction. `asv6.100-sse-completion-v1` saved 99 valid
answers in 99 attempts, with no failures or retries. Native cached reuse preserves
the earlier 39 answers with zero new calls.

Native collection verified **all 1,300 labels: 1,000 train / 100 validation /
200 final test**, with no missing IDs, text/author/split mismatches or author
overlap. Earlier 1,201 labels are preserved exactly. All labels retain the same
full ASv6.100 prompt, teacher model, reasoning effort and schema. Structural and
receipt checks passed; semantic review has not been performed. The full collection
and verification are saved beside `sample-final/`. No rental or paid API was used.

**Full pilot input audit, October 5:** offline production tokenization of all
1,300 actual labels finds longest training sequences of **18,114 Qwen / 18,396
Gemma tokens**. Canonical answers require up to **8,452 / 8,881 tokens**, including
native turn endings; **53 / 57 training answers** exceed the frozen 4,096-token
output allowance. Seven training hierarchies exceed the 128-node output guard,
with a maximum of 145. Increasing context alone cannot fix the output bounds.
The current 88-GiB planner rejects every Qwen/dense input even at batch size one;
MoE's one-note estimates remain within budget. These are calculations, not GPU
measurements. Frozen inputs/configurations are unchanged; revised context/output/
memory settings, hardware validation and repricing remain open. The
[technical plan](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md#full-pilot-input-audit--october-5)
records native preflights, all split counts and artifact hashes. No rental or
additional model call was used for this audit.

**Local runtime memory investigation, October 5:** the user authorized tracing
attention and training memory. The pinned runtime defaults to SDPA, but old GPU
receipts do not identify the selected CUDA kernel. PyTorch 2.12.1 source includes
memory-efficient BF16 forward/backward paths for Gemma's 512-dimensional global
heads; Flash and cuDNN paths reject that dimension. A candidate that excludes math
fallback gives conditional one-note generation estimates of **58.39–58.60 GiB
Qwen / 71.73–72.32 dense Gemma / 55.79–56.07 MoE**, retaining cache, mask,
workspace and prefill allowances. This is not an approved replacement policy
or measured GPU fit.

Training also materializes scores for ignored prompt positions, followed by FP32
cross-entropy buffers. Released **Liger 0.8.4 fused linear cross-entropy** is a
candidate that preserves ignored labels, token averaging and Gemma's softcap
while processing scores in chunks. Its source has Qwen and Gemma integrations;
LoRA/MoE compatibility, loss/gradient agreement and CUDA execution remain to be
tested. No dependency, worker, frozen configuration or hardware was changed.
The technical plan records the implementation candidate and verification gates;
this investigation does not authorize a new rental or assert training fit.

**Runtime implementation approved and completed locally, October 5:** add
explicit SDPA with Flash/memory-efficient CUDA backends and no math fallback,
plus **Liger 0.8.4 fused linear cross-entropy for training only**. Retain the full
prompt, note, teacher target, ignored prompt labels, supervised-token averaging,
Gemma softcap 30 and existing LoRA/continuation recipe. New subjects-only
candidates use **20,480-token context / 10,240-token output** and omit the
128-node guard. The planner may omit headwise score matrices only with enforced
efficient CUDA attention. Pinned-container integration and SSH checks passed;
actual CUDA loss/gradient agreement, long-example memory fit, generation cache
and timing remain open. The configurations have since been frozen in the paired
prep→pilot input package (packaging status below). The preserved three-way data
package was prepared through the shared workflow without repartitioning (integrity safeguards below).
No rental, publication or additional teacher call occurred. The technical plan
records checks and limitations.

**Experiment integrity fixes authorized October 5:** freeze paired prep/pilot
stages locally; successful prep continues on the same rental with fresh pilot
adapters. Before pilot training, verify all three complete validation baselines.
Distinguish malformed model answers from missing work, parser defects and broken
receipts. Prep must cover the longest complete training example and planned full
validation cache shapes, and compare actual fused CUDA loss/adapter gradients
against the native path before its first update. Recheck all required responses,
continuing checkpoints and coverage locally before recording the deletion review.
The shared three-way data package preserves 1,000 train / 100 validation / 200
reserved final test notes. Local semantic grading need not be settled to collect
GPU outputs; its rubric/reviewer were then open. The October 7 DSRv1 design
above settled the reviewer and method, with qualification then pending. The
October 8 trial subsequently failed known semantic and cross-version checks.
Final-test collection is now
implemented locally (below). Actual hardware checks and new launch spending
remain open. These safeguards cannot guarantee
a clear performance difference between students.

**Primary pilot comparison and final-test collection approved October 5:**
compare the three students after the same 1,000 teacher-labeled notes, using
each final adapter and its corresponding untuned baseline. Keep the five
100-note validation checkpoints for learning progress and regressions; earlier
checkpoints remain saved but are not candidates for the primary test comparison.
During the main rental, collect all six versions' answers on the same 200
reserved test notes: **1,200 test responses**, alongside **1,800 validation
responses**. Keep test content and semantic scores sealed through local validation
review and model selection. Mechanical accounting, parsing and file verification
can proceed immediately; verify all six complete test collections before deletion.
Then unseal and score all three comparisons locally under frozen review criteria.

This supplies evidence about the tested recipes, not each student's optimal
checkpoint. An earlier validation peak can motivate separately authorized test
inference; do not use test results to select another checkpoint or revise the
experiment. Check the semantic grader locally and report uncertainty; close or
unconfirmed gains can remain inconclusive. Test collection and completeness
checks are now implemented locally: reuse the loaded base and final merged
evaluation copy, save separate test files bound to the run/checkpoint, and
require both complete test stages before completion review. Automatic reports
expose only test counts/locations; semantic grading and opening test content
remain separate local work after validation/model selection. Actual ASv6.100
GPU fit/throughput and launch duration remain unmeasured; the combined rental
was subsequently approved up to $285 below.
The shared SSH rehearsal passed after correcting one error-message assertion;
all three native tokenizers also passed the actual train/validation/test preflight.
The technical plan records evidence and limits. No rental or publication occurred.

**Final integrity audit fixes authorized October 5:** opted-in subject pilots
can explicitly continue a terminal worker on the same rental under a recorded
reason and the unchanged frozen package. Retrieve and verify the failed attempt
first, preserve its evidence, reuse saved answers/checkpoints, and require a
new retrieval and completion review. Saved malformed answers are never retried;
an interrupted generation with no saved answer needs an explicit continuation.
Publish immutable run provenance, batch plans, started-call records and receipts
early for background transfer. Retry failed copiers at most three times, with
exhausted failures visible and no worker stop. Freeze the detailed status command
and save mechanical progress plus GPU utilization/memory and disk observations
locally, excluding reserved-test content and failure counts. The training recipe
and frozen data are unchanged; actual ASv6.100 CUDA checks remain for the rental.
Image publication and $285 spending were subsequently approved below. The
technical plan records local recovery verification.

**Paired package frozen and priced October 5:** the user approved preparing the
combined prep→pilot inputs and updating the estimate. The shared packager froze
all three candidates with matched prep recipes, unchanged ASv6.100/data bindings
and no automatic timeout. Runtime hashes match the tested, stopped VM. All six
native-tokenizer preflights passed. Prep uses three complete training examples
in two continuing partial updates: one initializes Adam state, then two include
the longest example after gradient accumulation with restored Adam state. Fresh
main adapters retain eight examples per update and 125 updates per student.
The 300 GB storage draft allows 200 GB inbound / 60 GB outbound, covering the
approximately 27.25 GB checkpoint payload and a possible second retrieval copy.
The two-GPU update supersedes the single-card launch package and estimate.
A saved pair of 96GB/600 W RTX PRO 6000 Server cards costs $2.99/hour including
storage. Conditional scheduling gives 40–66 hours / $122–197; a quadratic
training sensitivity gives 80 hours / $239. These assumptions use
actual native token lengths and older GPU timings, with teacher answer lengths
as generation proxies; they are not measured ASv6.100 throughput or guarantees.
The user approved private image publication and a **$285 combined rental budget**.
The tested image is published and verified private: read-only pulling succeeds,
anonymous manifest access returns HTTP 401, and all runtime/file hashes match
the tested VM.  Actual GPU
checks and local semantic grading remain pending. The October 5 preparation used two-GPU hardware at $2.9889/hour including storage. Qwen prep passed; dense Gemma failed the
88 GiB cache-memory guard without CUDA OOM, and Gemma MoE failed native/fused
adapter-gradient agreement before its first update. The prep gate blocked every
main baseline and training run. All 86 available files (4.35 GB), available checkpoints and failure logs were retrieved and independently rehashed under the standing prep-only substantial-repair authorization. 
Preliminary charges were **$1.974**. Repairs were completed
locally before the new frozen version below. Failed checks now preserve numerical
evidence before rejecting work. The short Gemma reference promotes projected
logits to FP32 before softcapping, matching Liger 0.8.4's correctness reference;
CUDA tolerances and training computation are unchanged. Dense inference reserves
12 GiB scratch rather than 4 GiB under the same 88 GiB budget, before either
baseline or trained generation. Prep checks both validation and reserved-test
input shapes with synthetic continuations, without generating or semantically
reviewing reserved answers. The original frozen artifacts remain unchanged.
Local reproductions, 94 VM tests and six native tokenizer preflights pass; one
VM tokenizer test is skipped and covered by those separate preflights. Actual
GPU checks remain required. Singleton dense generation updates the conditional
timing to 53–83 hours, with a 93-hour sensitivity case; projected replacement
costs are $159–248 / $279 at the saved $2.99/hour quote. Including the earlier
preliminary bill, those scenarios fit the original $285 total. Current server-card
throughput and student answer lengths remain unmeasured.

The corrected VM export is published privately as
`sha256:c376ec124faabd71c018e52044faf9ee6bbc4b02b6d7a48bf90f1cbfa8f806e5`.
Its filesystem layers, runtime settings and all 15 source hashes match the VM;
Docker export normalizes empty metadata defaults without changing execution.
Read-only pulling succeeds and anonymous access returns HTTP 401. The replacement configuration remained within the original $285 experiment maximum.  The replacement two-GPU configuration cost **$2.9889/hour** including 300 GB storage. Container DNS failed before
SSH, inputs or worker startup; one reboot did not resolve it. Necessary startup logs and direct/proxy probes were saved and hashed under the standing prep-only policy.  Its preliminary cost was **$0.76**; the two failed attempts cost **$2.74**, within the original $285 experiment maximum.  Both attempts failed. Exclude machine 146170 from replacement searches. A different
compatible host now quotes $2.9389/hour. The frozen
recipe/image/package are unchanged. There is no automatic time/budget stop or
deletion.       A proposed $280 replacement projects
99,013 cents, leaving 987 cents beneath the lifetime cap; this does not add to
the original $285 pilot approval. The selected configuration has two 96GB/600 W server cards at $2.9389/hour including 300 GB storage. The verified
private image, package, 15 runtime source hashes and model recipe are unchanged.
Native frozen preparation passed without a paid action. The proposed experiment maximum was **$280**.  This remains within the original $285 experiment maximum, not a new allocation.
Evidence is `target/distillation-pilot-v1/launch-20261006-two-gpu-r2/`. The preparation used two-GPU hardware at **$2.9389/hour** including 300 GB storage. Startup and GPU prep were
observed; live exfiltration, unchanged prep/complete-baseline gates
and complete-data explicit deletion rules govern this run. No automatic stop or
deletion is enabled. The local $1 setup gate rejected worker admission: $0.314536 rental estimate plus the full $0.755209 planned transfer allowance exceeded $1. SSH, transfer and remote preparation had
succeeded. A production-path reproduction confirmed that refusal. Under standing autonomous repair authorization, a separate local Context with a $5 startup admission allowance started worker attempt 001; calling worker start again returned the same attempt. The original
Context/contract/transport, remote code, prompts and model recipe were not
modified; their hashes were verified again. Failed admission/old supervisor
receipts are archived under `launch/startup-recovery/001/`, with the effective
local configuration and repair result. The original frozen supervisor and
observer were restarted. Future launch settings use a $5 setup allowance. No main baseline or training preceded the
repair; there is no comparison change to rerun.

**October 6 verified prep closure:** Qwen passed. Dense completed both optimizer
updates, adapter reload/merge, brief generation and singleton cache checks, but
its **88.43 GiB** reserved training peak was wrongly compared with the **88 GiB
inference batch budget**. No CUDA OOM occurred. Earlier prep already recorded
training reservations above 88 GiB; this inference setting is not a training
acceptance limit. The local fix removes that check without changing training
computation or inference memory checks. A production-path regression first
failed on that cutoff, then both targeted checks passed. The published base
image with a local source mount passed 73 tests; 12 VM-only checks were skipped.
The new fix is not yet published or newly validated in the deployment VM.
Gemma MoE still failed native CUDA gradient agreement before its first update;
its finite gradient evidence records six failing elements out of 360,448,
maximum absolute error 0.015625 and relative L2 error 0.035727. Tolerances remain
unchanged; the cause is unresolved. The prep gate blocked all main baselines
and training. All **95 work + 6 startup files / 5,849,177,916 bytes** were independently rehashed; available checkpoint/response seals and complete Qwen prep were verified under the standing prep-only substantial-repair instruction.  Preliminary charges were **$2.543**.
 The three failed attempts cost $5.29 within the original $285 experiment maximum; no remote edit was made.
Integrity evidence is the launch directory’s `closure-evidence.json` and `operation/observations/full-pre-deletion-integrity-review.json`. MoE CUDA confirmation remains open; the subsequent local
repair and rebuilt runtime are recorded below.

**October 6 local MoE reference repair:** reproduce a false gradient rejection
with real BF16 Gemma MoE/PEFT and an emulation of Liger’s unavailable CUDA loss.
Liger caches the mean-loss hidden-state gradient during forward, then scales it
by the note’s weight during backward. The old native reference scaled CE before
LM-head backward, introducing different BF16 rounding. The short reference now
applies the weight at the same hidden-state boundary; training computation,
teacher-token weighting and atol=0.005 / rtol=0.05 stay unchanged. The new
production-path regression first fails on adapter agreement, then passes with
zero gradient difference and still rejects deliberately corrupted gradients.
The local workflow suite passes 89 tests, with 12 deployment-VM-only checks
skipped. The full original CUDA failure is not yet replayed; confirmation on
hardware remains required; the rebuilt runtime is recorded below. Evidence is
`target/distillation-pilot-v1/moe-gradient-repair-20261006/`.

**Persistent recovery storage approved:** retain model downloads and compatible
saved work on a separately rented local volume across failed-container
replacement. On October 6, choose a cheaper compatible Bulgarian host with a
volume for the next attempt; paying the Texas premium solely for additional
spare GPUs is not approved. Check current GPU and volume offers before launch.
A reliability score is uptime evidence, not proof of future free GPUs;
the volume attaches only on its physical machine.
**One-GPU download stage approved October 6:** use that host's cheaper one-card
rental to verify attachment and download all three students at their frozen
revisions onto the actual persistent volume. Verify required weights, tokenizer
and configuration files; retrieve completion evidence before deleting the
container. Retain the volume. The two-card rental then reattaches it, verifies
the cache without network downloads, and runs the full concurrent GPU prep
before any pilot work. This changes setup scheduling; models, inputs, recipe
and the existing combined spending limit stay fixed.
**Main rental layout reconfirmed October 6:** after comparing two separate
one-card rentals, retain one main rental with two GPUs following the approved
one-card download stage. The modest projected savings do not justify changing
the locally tested storage and shared prep/baseline checks. This decision
keeps the existing models, inputs, recipe, spending and deletion requirements;
fresh offer availability and actual CUDA fit/throughput remain open. Comparison
evidence: `target/distillation-pilot-v1/separate-rentals-comparison-20261006/`.
**Download handoff implemented and VM-tested October 6:** pin 42 required files
at the same revisions, totaling 169.81 GB, with size/content checksums and 32 GiB
reserved for saved work. Retrieve and locally review download, file and volume
evidence before deletion. The VM destroys the download container, retains its
volume, then completes offline prep and fresh pilot execution with two workers.
Missing/corrupt cache files block every worker; incomplete retrieved evidence
blocks completion review. Host regressions pass 181 checks (16 VM-only skips);
the rebuilt VM passes 109 checks, with the four checks executed
separately and one optional native-tokenizer check skipped. All six
configurations and data are unchanged. Evidence:
`target/distillation-pilot-v1/model-cache-stage-20261006/`. The rebuilt image
is now published at the immutable digest in `publication/publication-receipt.json`;
its filesystem/configuration match the VM, read-only pull succeeds, and anonymous
manifest access returns HTTP 401. Actual Vast attachment and full MoE CUDA
confirmation remain pending. A $2 volume reservation covers 24 hours of storage
for the approved download stage. The download configuration used 300 GB storage at $0.0833/hour. The quoted download-only rate was $1.4278/hour including storage. Its create request was definitively rejected with HTTP 400;
complete controller inventory probes confirm no instance and zero GPU charge.
 The old helper discarded the provider message, so the underlying
rejection reason is unknown. A production CLI regression first reproduced the
missing message; the helper now saves a bounded message after redacting registry
and API credentials. All nine pinned CLI checks and 68 controller checks pass;
the updated VM rehearsal passed before another creation request (109 passed
checks, with the unchanged native-tokenizer check using prior evidence). The
existing generalization guard was stale after approved volume recovery/child-lock
changes; its exact non-volume preparation-flow assertion is retained. All 81
generalization checks now pass; no controller behavior changed. No model,
prompt, data or training recipe changes. Evidence:
`target/distillation-pilot-v1/create-diagnostics-20261006/`.
The rebuilt private runtime is
`docker.io/kernelkind/oracle-mvp@sha256:da81c955532264e216653d0b742cecfc93fb63c99595a4fc8960f5ddeff2b642`.
Registry config/rootfs match the imported VM; both frozen packages verify inside
the image, read-only pull succeeds and anonymous access returns HTTP 401.   Combined rate
$1.4278/hour is below standing $1.60 approval. This retry has not started GPU execution.
Evidence: `target/distillation-pilot-v1/download-launch-20261006-v2/`.
The retry also received HTTP 400 before allocation; its captured reason is an
invalid `volume_info.mount_path` of `/workspace/oracle-full-build`. Completed
controller reconciliation and independent complete inventories confirm no GPU,
zero charge and an unattached volume.  The [official creation API guide](https://docs.vast.ai/api-reference/creating-instances-with-api#attaching-volumes)
uses `/workspace`; the launcher and mount checks now use that parent, retaining
all experiment/cache paths beneath it. Cache receipts name their logical
`volume_root` accurately. Both pinned CLI mount assertions failed first; the
receipt regression also failed first. Nine CLI, 149 controller/generalization,
four cache and 13 workload-spec checks pass. The initial VM rehearsal caught the
old mount assertion; the corrected full rehearsal subsequently passed. All six
configs,
data and required model files remain byte-identical; no recipe change or pilot
training. Evidence: `target/distillation-pilot-v1/workspace-volume-20261006/`.
The final VM rehearsal passes 109 checks and stops cleanly, including the actual
parent mount, replacement and offline two-worker handoff. Both packages verify
inside the imported image. Its private registry digest is
`docker.io/kernelkind/oracle-mvp@sha256:633c684c0b64d064df34e8de9de64c07bc0b764423073a2c7a25aa561bd57a4b`;
VM layers/effective configuration/source hashes match, read-only pull succeeds
and anonymous manifest access is HTTP 401.   Combined rate is $1.4278/hour. The download stage completed. Actual mounting, provider attachment and write/read receipts agreed. All 42 pinned
files (169,808,998,964 bytes) are checksum verified; download took 768.797
seconds. All 12 work and six preparation files were retrieved and verified locally, and production completion review passed.  No baseline or training.
Preliminary download-stage cost was $0.455.   
The original $285 approval is unchanged.
Cold private-image loading outlasted the controller readiness window. Original
failure/watcher evidence is preserved under `startup-recovery/001`; a guarded
retry of the unchanged controller on the same bound instance completed setup
without another create request or remote edits. The future command controller
now returns `instance_starting` after a readiness window and automatically
retries on the same instance; fatal identity errors still fail. The production
CLI regression failed first, then passed; 176 local tests succeed with three
VM-only skips. All six configs, data and model file requirements are byte
identical; only `vast/runner.py` changes in runtime hashes. The first updated
VM passed every runtime check but ran out of its 64GB disk during image export.
Five duplicate archives were checksum matched to preserved host copies before
removal, freeing 15.65GB. The standard rehearsal then completed: 109 checks
pass, four volume/cache checks rerun their earlier skips, the unchanged optional
candidate-tokenizer check remains skipped, and the VM stops cleanly. Export
SHA256 is `133a80cbd02c58d678f990c206321b958fbc1f9b0225ac0e1fee358488638d41`.
The rebuilt private image is
`docker.io/kernelkind/oracle-mvp@sha256:b99b4e9f23211bada17f37a5c73c8e26b1fde3bc66a1403783aee2d774567d1a`.
VM layers/effective configuration/source hashes and both frozen packages match;
read-only pull succeeds and anonymous manifest access is HTTP 401. Actual
concurrent CUDA prep remains a gate before every main baseline/training run.

No pilot baseline or training had started. Evidence:
`target/distillation-pilot-v1/download-launch-20261006-v3/` and
`target/distillation-pilot-v1/startup-retry-20261006/`.

**Deleted-rental accounting approved October 6:** the user rejected holding full
run budgets after confirmed deletion. For Vast command rentals, replace that
hold immediately with the bounded unbooked charge: elapsed time from reservation
through verified deletion at the approved maximum hourly rate, plus the full
approved transfer allowance, floored by posted exact-instance invoices. Round
time and cents upward; subtract all previously booked charges from the hold.
Keep final invoice confirmation and later adjustments without making their
24½-hour observation delay a gate for a new rental. Active rentals/volumes keep
their reservations; the lifetime $1,000 cap and original $285 experiment total
remain. Apply this policy in the local ledger.
The four pilot/preparation attempts had a bounded combined cost of $8.52. The four attempts' latest posted charges totaled $5.813.   
The production budget check rejects admission before this adjustment and passes
after it. Both exposure and admission checks pass; original records are intact.


  The replacement configuration used two 96GB/600W cards at $2.8139/hour plus $0.0833/hour for a 300GB volume. Hardware checks and volume capacity pass.
 A proposed $3 download allowance
leaves $256.48 for main GPU work inside the original $285 including failures.
 No automatic deletion or time/budget cutoff. The unchanged
tested private runtime and one-GPU download → two-GPU prep/pilot flow apply;
all cache checks and global prep/baseline gates remain required. Evidence:
`target/distillation-pilot-v1/host-switch-20261006/`.
The download cache held all **42 files / 169.8 GB**, checksum verified. The download completed successfully; local completeness review verified the retrieved evidence.
Its preliminary bill is $1.22, with 28 cents retained under the $1.50 bound.
The two-GPU run passed cache attachment and offline verification. Qwen and
Gemma dense passed full CUDA prep; Gemma MoE still failed gradient agreement.
**No pilot baseline or training started.** All **97 work files / 5.85 GB** and six preparation files were retrieved and independently rehashed. Preliminary charges were **$1.445**.
 The one-GPU diagnostic completed both cases without training updates. All **20 files / 3.17 MB**, including all four saved head-state/gradient pairs, were retrieved, independently rehashed and opened.  The preliminary diagnostic cost was **$0.21**.
 Head relative L2 error is **0.294–0.321%** with identical inputs;
296 of 156,119,040 adapter-gradient elements fail pointwise tolerance after
backpropagation. Disabling reduced-precision reductions improves head agreement
but does not resolve the deep comparison. A locally tested reference correction
checks head gradients separately, then compares native/fused adapter gradients
using the identical incoming head gradient. It adds a relative L2 check using
the existing rtol, so absolute tolerance cannot hide corrupted tiny gradients.
Both new production-path regressions failed before repair and pass afterward;
all five fused-loss tests pass. Full VM validation now passes: 10 candidate,
46 workflow, 48 deployment, four cache and four explicit replacement/handoff
checks; all four deployment skips are covered separately. Candidate tokenizer
preflight uses verified offline metadata. Caching reuses passed stages; the exact
VM export and refreshed package are published privately and verified, at image
digest `afa90bc64233b227da5db36f1336d7395138d9528bfb8c0d3a7dadc5f7256bad`.
All three actual CUDA loss/head/adapter-gradient checks now pass, with zero
backbone-gradient differences using the verified identical head gradient.
The preparation passed Qwen and dense Gemma full prep. MoE stopped on its
seven-note native generation-cache probe: **88.080 GiB reserved versus 88 GiB
budget**, without OOM. **No pilot baseline or training started.** All **116 work files / 6.82 GB**, six preparation files, five sealed checkpoints and the three gradient-check reports were retrieved, independently rehashed and reviewed.  Preliminary charges were **$1.361**.  The corrected two-GPU configuration cost **$2.8139/hour**. Only MoE inference workspace changes **4 → 12 GiB**, consistently
in prep and pilot; total inference budget stays 88 GiB and the widest predicted
batch falls **seven → five**. Exact image, code, prompts, data, models and
training recipe are unchanged. Package verification and native preparation pass.
The replacement passed all three full CUDA preps and started baselines in the same run. The widest real cache probes reserve **76.28 GiB Qwen
(seven notes), 77.07 GiB dense Gemma (one), and 76.80 GiB MoE (five)**, all below
88 GiB. Loss/gradient checks, merge/generation, long-input updates and saved
continuation checks pass for every student. No pilot training starts until
all three baselines pass. Observe continuously and progressively retrieve
frozen responses/checkpoints. Archive all verified prior work and retain the
model cache. No automatic stop or deletion. Evidence:
`target/distillation-pilot-v1/main-pilot-loss-boundary-20261006/` and
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/`.

**Baseline integrity, October 7 00:07 UTC:** Qwen and dense Gemma's 100-note
validation baselines are retrieved and verified locally: hashes, full inputs,
raw/parsed answers and batch receipts agree. Qwen's 13 and Gemma's two invalid
answers remain counted. Both 200-note test collections are underway and sealed.
MoE is queued; no main training has started. Receipts:
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/qwen-validation-baseline-integrity.json` and
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/gemma-dense-validation-baseline-integrity.json`.

**Qwen and dense Gemma baselines complete, October 7 05:36 UTC:** each
student has 100 validation and 200 reserved test responses verified locally by
the production checks. Full prompts, raw/parsed answers, batch receipts and
checksums agree. Reserved test content and quality remain unreviewed. MoE is
starting its baseline; no main training has started. Receipts:
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/qwen-reserved-baseline-integrity.json` and
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/gemma-dense-reserved-baseline-integrity.json`.

**All baselines verified, October 7 08:23 UTC:** each student has 100 validation
and 200 reserved test responses retrieved and checked locally by the production
validators. Prompts, raw/parsed answers, batch receipts and hashes agree; all invalid
answers remain counted. Reserved test semantics remain unreviewed. The pipeline
advanced to Qwen and dense Gemma training concurrently; MoE follows Qwen. Receipts:
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/gemma-moe-validation-baseline-integrity.json` and
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/gemma-moe-reserved-baseline-integrity.json`.

**Training progress verified, October 7 13:58 UTC:** Qwen has completed
400 distinct notes in 50 continuing updates; dense Gemma has completed 200 notes
in 25 updates. All three saved checkpoints, including adapter and optimizer/RNG
state, are local and passed hashes, exact note coverage and counter checks.
Qwen's two training blocks took 34.9 and 33.2 minutes; dense Gemma's first took
92.9 minutes. Both Qwen validation sets are fully retrieved and verified against
the same 100 inputs and batch plan as baseline. Each has 2 parsing failures,
versus 13 untuned; the two failures at 400 notes hit the output limit. Generation
took 121.4 and 143.1 minutes, versus 128.1 untuned. Semantic correctness/coverage
remain ungraded. Qwen continued training toward 600 notes; dense Gemma is
validating after 200 and MoE remains queued. Reserved test semantics remain
unreviewed. Receipts:
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/qwen-checkpoint-400-integrity.json`,
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/gemma-dense-checkpoint-200-integrity.json`,
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/qwen-checkpoint-200-validation-integrity.json` and
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/qwen-checkpoint-400-validation-integrity.json`.


Preliminary backup storage charges were **$0.884**.   

The launcher now mounts the selected volume, retains model downloads and
verifies saved work before replacement. It preserves work paths and worker
attempts while archiving the previous launch receipts. Reuse requires identical
image/data/recipe, verified local retrieval and confirmed prior deletion. An
explicit runtime repair may retain downloads while archiving all previous work
and starting a fresh comparison; its reason is frozen. A controller-crash
regression keeps the worker lock in live training children, blocking sealing
and reentry until writers exit. Host regressions pass 137 checks, with 16
VM/optional-SDK skips; the pinned SDK payload test passes. The rebuilt VM passes
101 checks: actual container replacement preserves 242 saved data files, logs
retain their original prefixes, and the model cache remains readable offline.
The exported image matches the frozen package; all six configurations/data are
unchanged. One optional native-tokenizer check remains covered by the prior
unchanged-input preflights. Full MoE CUDA replay and new private publication
remain pending. No volume or replacement is rented.
The actual Vast volume attachment remains untested; startup checks the mount
before setup or training. Recovery across container replacement is verified
in the VM.
The two-GPU VM passed 91 tests, with one optional native-tokenizer check skipped;
149 shared-controller regressions passed. Real concurrent CPU workers verified
prep→pilot, early copies from both workers, checkpoint continuation and complete
retrieval/review. All six native configurations/data are unchanged from their
passed preflights. The tested export and runtime hashes match the new frozen
package. This is automation evidence; server-card CUDA execution/fit/speed remain
open. The technical plan records hashes, quote evidence and the calculation.

**Approved fine-tuning candidates (September 24, 2026):** Qwen3.8-27B,
Gemma 4 31B instruction-tuned, and Gemma 4 26B-A4B instruction-tuned. The third
candidate replaces T5Gemma 9B–9B PrefixLM instruction-tuned. Compare its subjects,
hierarchy and total training-and-generation cost with the
dense candidates; lower active parameter count does not establish a cost
advantage. The larger pilot's numeric recipe, full ASv6.100, splits and
collection settings are frozen. Two-GPU launch spending is approved up to $285;
actual hardware measurements and local semantic review were pending at that
checkpoint. Current training and evaluation status is recorded above. The
informal subject/mask settings and $25 approval above apply only to the completed
preliminary experiment.

The [teacher research](../../sse_multivector/TOKEN-USAGE-ESTIMATE-1M-NOTES.md#lower-cost-annotation-models)
already identifies Muse. A later [12-note diagnostic](../../sse_multivector/frontier-model-comparison-v1/asv6.23-diagnostic-v2/results.md)
found it promising on subjects with ASv6.23, but with some context omissions.
That diagnostic tested neither masks nor prominence, and did not establish
equivalence to Astra. Its subject-only cost is not a complete labeling estimate.

Selecting the teachers and successfully completing the 500-note / 5-topic
hierarchy validation are both prerequisites for starting full training-data
generation (07). A finished but unsuccessful run does not clear this gate.
The September 21 direction to use the same teachers for pilot and full training
data was subsequently narrowed by the October 4 subjects-only pilot approval:
its label teacher is settled independently, without selecting release teachers.
Pilot data (05) is complete; general teacher selection no longer gates it.
The full training-data (07) teacher and successful-500-note requirements remain.
The informal start above may reuse existing annotations before selection. Work that
consumes no labels, such as 18's training-code preparation, may use any data and
need not wait for the teacher selection.

### Teacher-comparison pilot evaluation plan

Node 17 covers the teacher comparison, including its planning, and remains in
progress. GPT-6.1 Sol low is provisionally favored for SP after assessment on
20 posts. Sol xhigh grouped masks were assessed on 20 posts: 287 masks in the
first sample and 397 in the fresh sample, 684 total. These used saved Astra
subjects, not Sol's own generated subjects. Agent reviews found broadly
comparable mask quality to Astra, with minor omissions and unresolved cases.
The samples are small, purposive and food-heavy; these are agent assessments,
not user approval of the masks or evidence of corpus-wide parity.

The combined Sol subject-and-mask process and resulting hierarchy A/B
comparison remain unvalidated. Sol's subscription quota use is unmeasured.
Following subsequent medium comparisons, the user provisionally favors GPT-6.1
Sol medium for grouped masks. This preference does not establish corpus-wide
parity. Final selection remains open; frozen prompts and production
settings are unchanged. This progress does not complete 17 or establish
end-to-end hierarchy quality.

The comparison needs to establish:

- Whether candidates produce suitable subjects and masks under the validated
  requirements. Deferred node sorting adds no required teacher outputs.
  Subject-only evidence does not establish mask quality.
- Whether hierarchies built from each candidate's own outputs on the same notes,
  with downstream construction held fixed, offer useful
  browsing paths.
  Compare the hierarchies before selecting teachers; distinguish differences
  caused by teacher outputs from failures shared by the construction pipeline.
  Label-only parity does not settle the selection.
- Whether the selected teachers can supply the intended training data
  within the available time and budget.
- Whether provider data-use and output-use terms permit the intended training
  and open-weight release.

Completing 17 needs the validated subject/mask prompts from 01 and completed
prompt stress-testing in 30. Deferred node sorting and prominence are not
completion prerequisites. Comparison work may continue before stress-testing
is complete. Final selection needs
evidence for the prompts we will actually use; any rechecking belongs to the
comparison workstream.

The hierarchy A/B comparison is part of 17, not a separate task. The sample,
comparison procedure, review coverage, treatment of unsuitable annotations and
acceptance decisions remain open. No generate–repair–train workflow is
prescribed. Those details belong to the evaluation workstream, not to
assumptions made by this release plan.

Completing the full training data (07) also requires an agreed training volume,
informed by the fine-tuning pilot (06). Its evidence is an input to that decision;
this does not make completion of all of 06 a prerequisite for starting 07.
The September 27 target must be checked against the chosen volume and the
selected teachers. No model calls, experimental procedures or spending are
authorized here.

## Hierarchy construction and service dependencies

Training-data generation uses subject descriptions to guide mask generation.
The intended distilled model instead takes a complete note and produces grouped
source-text masks. Any additional teacher/model outputs needed for note sorting
remain undecided. It must discover subjects, but its output need not include
English subject descriptions. The plan does not require a separate
subject-generation call for each final-corpus note.

The shared hierarchy construction is masks → SSE vectors → flat HDBSCAN groups →
node descriptions → cosine-filtered candidate pairs → subsumption judgments →
directed node hierarchy. Prominence is part of the deferred note-ordering
candidate, not a required construction stage. The relationship
method remains open: TRUE generated HR02, but its judgments were not good
enough. The separate Jev hierarchy remains a diagnostic baseline; the earlier
manual-placement decisions remain preserved and unapplied. On September 28,
the user approved the wording of
[NSP-Astra-Masks-v1](../../sse_multivector/node-subsumption-prompt-astra-masks-v1/prompt.txt),
a separate mask-based parent–child prompt based on the accepted merge prompt.
It is tested experimentally, not frozen.
The test reuses the 148 pre-Jev HR02-NMP09 groups, existing merges and
titles, with comparisons selected automatically from tree links and the bounded
cross-branch shortlist. No new model calls or graph implementation are approved
by this wording approval. Combining merging and placement in one prompt is
deferred. The user subsequently authorized preparing and running HR02-NSP-MASKS01:
12 pairs selected reproducibly from the saved comparison sources, using Astra
low and unchanged NSP-Astra-Masks-v1. All 12 returned structurally valid answers
in 12 new subscription calls, without retries or reuse. Agent review accepts
10 answers, rejects one and leaves one uncertain; these are not an accuracy
benchmark. The user confirmed the rejection of Food consumption → Clean, simple
dishes: the expected answer is neither. This records a review decision, not a
hierarchy edit. Preservation → Preservation remains unresolved, and the ten
agent-accepted answers have not received user verdicts. The user approved
expanding the same test without resolving Preservation or changing the prompt.
HR02-NSP-MASKS02 completed 48 comparisons: 36 new Astra-low subscription calls
and 12 exact-request reuses, all structurally valid, without retries. The
unchanged deterministic selection now takes 24 pairs from each source instead
of six. Initial agent review of the 36 new answers accepted 29, rejected two
and left five uncertain; these are not measured accuracy. The user subsequently
agreed that the disputed group titled Meat consumption expresses Meat generally:
its bare `meat` masks do not specify eating. The agreed answers are neither
against the plain-Meat group (equivalent topics), neither against Food
consumption, and disputed-group-as-parent against Beef. These are separate user
reviews of the three saved answers, not authorization to merge, rename or place
nodes. The user also confirmed rejecting neither for Enjoyment of food versus
Positive emotions: the expected answer is Positive emotions as parent. The
flagged-case walkthrough is complete, with Fire/Ash, Pizza, Ice/ice cream and
the earlier Preservation comparison left unresolved. The agent withdrew its
likely-miss assessment of Ice/ice cream: mask-set inclusion alone does not
establish topic containment. No prompt revision or additional inference is
approved by these reviews. Existing
groups, merges, titles and existing hierarchies remain unchanged.
The user subsequently approved implementing offline construction against the
48 saved answers, without new calls. It is implemented: retain all existing
groups, derive strict parent links only from native choices, preserve neither,
uncertain and untested pairs separately, and apply no review corrections. A
strict-containment cycle is a contradiction, not equivalence: save the graph
and evidence, then stop browser export without merging nodes or removing
links. Rejected directions reachable through other accepted links are reported,
not repaired. Existing Jev/TRUE paths retain their earlier behavior.
The separate partial view contains 148 nodes and all 100 posts, 20 links, six
model-uncertain pairs and 518 untested candidate pairs. No cycles or
rejected-but-reachable directions occurred; the existing browser's check
passed. This is a construction check, not semantic approval or the completed
hierarchy. The user then approved HR02-NSP-MASKS03: complete all 566 pairs from
the existing candidate list with unchanged NSP-Astra-Masks-v1 / Astra low,
reusing the 48 saved answers and making 518 new subscription calls, at
concurrency four. No new groups, merges, titles, candidate-selection rule or
review overrides are introduced. HD07 still stops browser export on cycles.
The pass completed with 566 valid answers, 48 exact-request reuses and 520 new
attempts (518 requests plus two successful retries after HTTP 503). All 148
groups were compared. The separate browser export retains 148 nodes and all
100 posts: 129 accepted links reduce to 101 links, with 76 roots. There are no
cycles, 39 uncertain pairs and three rejected directions reachable through
accepted paths. These contradictions remain flagged and unrepaired. The browser
check passed, and a second offline build reproduced identical graph/browser
files. This is a completed diagnostic build, not semantic approval; reviewing
its browsing result is next. Conflict resolution and production adoption remain
open. See the
[test scope](../../sse_multivector/node-merge-prompt-jev-v1/README.md#parentchild-prompt--nsp-astra-masks-v1).
The cosine cutoff and its implementation remain open. Existing all-pairs
experiments do not establish filtered behavior; filtering must preserve useful
parent–child links, not merely reduce calls.

The formal process also requires identical same-post masks to be deduplicated
before SSE, nodes with identical mask sets to be merged before hierarchy
generation, and parent–child navigation steps with identical complete post sets
to be collapsed before hierarchy publication. Retain strict mask-set subsets;
they can represent useful narrower nodes. Preserve source references and
original node IDs. These rules do not decide semantic equivalence between
different mask sets. The
[required stages and their limits](../../sse_multivector/navigation-research-v1/README.md#required-hierarchy-processing-stages)
record the requirements. Shared-child collapse is implemented and tested in the
node browser, and enabled for both HRv1 comparison views without changing
saved memberships. Repeatable semantic-equivalence decisions remain open.
This is not a claim that the existing experimental pipeline implements all
these stages end to end.

**Merged-node naming (approved September 24):** once nodes are merged, generate
the merged node's displayed title from their combined, deduplicated masks using
the frozen v38 prompt. HR02 now uses Astra low for merged titles as well as
individual titles, explicitly approved after scoring completed; earlier
Luna-max artifacts remain unchanged. Do not arbitrarily
choose a member's title. Preserve every original title and node ID. This call
only names the merged node: it does not decide the merge, change its links or
trigger another round of TRUE comparisons. The offline preparation, verified
title collection and browser export are implemented; a four-node live check
is complete. TRUE's relationship quality prevented HR02 validation. The saved
Jev baseline and earlier manual-placement decisions remain intact; the current
parent–child prompt draft above changes neither naming nor saved graphs. This
does not authorize further model calls or settle the provisional merge policy.

### Reversible hierarchy design decisions

The user requested this register on September 24 so uncertain choices remain
explicit and can be unwound. These are experiment choices, not claims of
correctness or completion. Alternatives listed here are not approved work.
Bring changes to these choices, and newly discovered design choices, to the
user before implementation; do not resolve them through per-node exceptions.

| ID | Choice and status | Uncertainty / tradeoff | How to revisit it |
| --- | --- | --- | --- |
| HD01 | **Current experiment rule:** native TRUE Yes creates an edge; no score cutoff. | Native answers miss useful links; the tested cutoff adds both useful and incorrect links. Neither is assumed correct. | Preserve exact title inputs, generated answers, scores and runtime identity; rebuild edges from saved outputs under another explicitly selected rule. |
| HD02 | **Provisional merge rule:** merge mutually reachable nodes (strongly connected components). Implemented and tested; HR02 is exported for quality review under task 02. | Correct subsumption cycles imply equivalence, but predicted cycles can be wrong. The user identified Beef / Beef products as an incorrect NEv2 merge. Saved examples have pairwise mutual Yes answers; a synthetic regression also covers longer cycles without them. | Keep the original nodes, masks, titles, edges and component membership. Rebuild from the pre-merge graph instead of trying to split a merged record after originals were discarded. |
| HD03 | **Current HR02 experimental rule, mechanically tested but not settled:** retain any accepted incoming/outgoing connection of a merged member, preserving existing paths. | This favors accepted paths over contradictory direct No answers. The contradiction can exist before merging: Beef -> Beef products -> Steak, alongside a direct No for Beef -> Steak. Record the disagreement; do not silently repair it. | Preserve every Yes and No and the original edge contributors. A different conflict policy starts from those answers and may require recomputing merges and descendants, not merely editing the displayed links. |
| HD04 | **Implemented:** generate merged titles through the frozen title workflow; bind returned names to exact combined-mask inputs and change labels only. Four-node live check and all six HR02 merged titles are complete. | The new wording may suggest a different scope from the original titles used by TRUE. The naming call does not establish new relationship evidence. | Save member titles, combined-mask input, prompt/model settings and generated title. A naming-only alternative need not rerun extraction or TRUE; using new titles for relationships would be a separate design change. |
| HD05 | **Implemented and tested:** derive a new merged-node ID from the SHA-256 of the sorted original member-ID list, preserving every original ID. | The same members produce the same merged ID regardless of member order or displayed title. This identifies the merge, not independently verified semantic equivalence. | Keep the original-member mapping and ID-rule version. A different membership or ID rule can be rebuilt from that mapping; changing only the displayed title must not change the ID. |
| HD06 | **Approved comparison design, not implemented:** preserve the first run's original reviewed view and create a separate reprocessed view from its saved nodes and TRUE answers using the new run's merging and navigation rules. Compare the new run primarily against the reprocessed view. | The first run included manual extraction corrections, group exclusions and a title override. Matching downstream rules does not make those inputs an untouched automatic baseline. | Freeze the original subjects, masks, node titles, answers and reviewed artifacts; do not regenerate them. Record the reprocessing policies and historical interventions separately so the original and reprocessed views remain inspectable. |
| HD07 | **Approved and implemented for the NSP-Astra-Masks-v1 diagnostic:** keep existing merges; derive links from native strict-parent choices without review overrides. Keep neither, uncertain and untested pairs distinct. Save cycles and stop export without contraction; report other path contradictions without repairing them. | Strict-containment cycles cannot establish equivalence. Further conflict resolution, candidate coverage and semantic quality remain unvalidated. This does not replace HD02–03 for the earlier TRUE/Jev builds. | Preserve pair inputs, receipts, selection, source hashes and policy version `strict-mask-parent-child-v1`; rebuild a separate graph under another explicitly approved policy. |

#### SP-based hierarchy rules

**LG01 — subject hierarchy merging** is the technique's name, independent of
post count. Refer to its applications as the **LG01 six-post run** and the
**LG01 100-post run**. The current implementation and saved artifacts still use
`SMv2`; `SMv2-100` was the earlier name for the 100-post run. This naming decision
does not change the rules, saved data or implementation identifiers below.

On September 29 the user requested consolidation of the recent rules in this
version-controlled register. The current investigation preserves and combines
per-post SP hierarchies, using their subject vectors as diagnostic helpers
alongside the original mask evidence. It is not a selected production algorithm.
The goal remains a useful, automated browsing hierarchy; no method is expected
to be correct in every case. Small-sample success is not evidence of scalability
or permission to adopt a method.

The entries below separate **agreed constraints**, **agreed changes not yet
implemented**, **implemented experimental choices**, **tested but not adopted
methods**, and **open questions**. Approval to run an experiment is not adoption
of its settings. These entries apply to the SP-based investigation, not
retroactively to the older TRUE/Jev/HDBSCAN builds. HD01–07 and the earlier
exact-mask-set, merged-title and display-collapse rules retain their stated
scopes; do not silently apply them to SP subject nodes.

| ID | Rule, scope and status | Rationale / limitation | Implementation, evidence and how to revisit |
| --- | --- | --- | --- |
| HD08 | **Agreed constraint for combining SP hierarchies:** preserve every supplied ancestor relationship as ancestor-or-equal. Equivalent entries may combine; an ancestor need not remain a strictly distinct node. Allow multiple parents and retain all original subject occurrences and relationships as provenance. | Preserving graph order does not prove a proposed merge is semantically correct. Do not delete supplied relationships to make a merge work. | [SMv2](../../sse_multivector/subject-order-probe.md#smv2--exact-same-post-combination) checks ancestor-or-equal preservation. SOv1's stricter upstream constraint is a diagnostic limitation, not a replacement for this requirement; see HD17. |
| HD09 | **Agreed interpretation of local SP structure:** top-level subjects in different posts need not have equal generality or remain global roots. A relationship absent from SP is unknown, not rejected. | Local branches are incomplete. Neither a shared descendant nor overlapping post/mask membership alone establishes that one parent contains another. Local depth is not a common global scale. | Applies to interpretation of all SP-based experiments. Missing global parent relationships still need a separate justified method; see HD21. Do not convert missing edges into negative training/evaluation labels. |
| HD10 | **Investigation data contract:** retain mask vectors as source-grounded evidence from MP selections in their post context and keep subject vectors, encoding SP wording alone, distinct as diagnostic helpers. Preserve source post IDs/text, SP numbers, exact mask ranges, mask IDs and vector provenance. | Sharing an encoding for identical subject wording does not merge subject occurrences. Cosine between two subject vectors, between two mask vectors, and between a mask vector and a subject vector are different comparisons; one must not be reported as another. | [SOv1 inputs and encoding](../../sse_multivector/subject-order-probe.md#fixed-scope), [ACv1](../../sse_multivector/ancestor-cosine-probe.md) and [SMv2 implementation](../../sse_multivector/subject_matching_probe.py) retain these distinctions. Vector blending and learning an additional representation were discussed, not adopted. |
| HD11 | **Agreed exact same-post combination rule; implemented in SMv2:** combine SP entries only when post ID, exact subject wording and the same nonempty source-mask positions all match. Retain every parent, child and original SP reference; no title call or new placement judgment is required. | Equal selected words at different positions do not qualify. Different posts, different subject wording, merely similar masks and empty masks do not qualify. Identical mask requests can reuse one answer, so agreement is not independent semantic confirmation. Combining a shared child does not imply a relationship between its parents. | [SMv2](../../sse_multivector/subject-order-probe.md#smv2--exact-same-post-combination) records exact combinations separately from cross-post matches and preserves them during cycle rollback; see HD15. The six-post run uses saved vectors and a separate output directory; earlier saved graphs remain unchanged. [Mask deduplication before SSE](../../sse_multivector/hierarchy_refresh.py) shares identical masks while retaining separate SP entries; that is a different operation. |
| HD12 | **Implemented experimental choice — SMv1/SMv2 post-pair selection:** for each unique nonempty mask, find its nearest mask in another post, retaining numerical ties; deduplicate the resulting post pairs. Empty masks do not supply this search. | This uses mask–mask cosine to shortlist posts, not to decide parent placement. The small exhaustive calculation is not the approved million-post retrieval implementation. | [SMv1 procedure](../../sse_multivector/subject-order-probe.md#smv1--separate-mutual-subject-matching-experiment), steps 1–2. Preserve the shortlist and exact comparison inputs when testing another retrieval rule. |
| HD13 | **Implemented experimental choice — SMv1/SMv2 subject matching:** within each shortlisted post pair, require mutual best matches by subject-vector cosine, subject-vector cosine >= 0.90 and mask-vector cosine >= 0.80. Find best matches before applying the separate cutoffs or checking mask availability; no weaker fallback. Both MP masks must be nonempty. | Mutual best is within that post pair, not the whole corpus. The scores are not blended. The cutoffs are provisional, not validated semantic-equivalence or placement thresholds. | [SMv1 procedure](../../sse_multivector/subject-order-probe.md#smv1--separate-mutual-subject-matching-experiment), steps 2–3; saved comparison tables distinguish failure reasons. Changing a cutoff requires a separately identified experiment, not edits to old outputs. |
| HD14 | **Implemented experimental choice — SMv1/SMv2 cross-post combination:** combine connected chains of passing pairs once. A–B and B–C can combine A, B and C even if A–C would fail. Retain all constituent subjects and masks. | This assumes equivalence can be extended along passing chains; it does not establish that every member pair agrees. No iterative rematching, relaxed cutoffs or title-only merges are part of either version. | [SMv1 procedure](../../sse_multivector/subject-order-probe.md#smv1--separate-mutual-subject-matching-experiment), step 4. Original accepted pairs and members allow another combination policy to be tested without new inference. |
| HD15 | **Approved and implemented — SMv2 relationships and cycles:** map every original SP edge onto combined nodes; deduplicate identical edges and retain internal edges in provenance. First check HD11 combinations alone: if distinct combined nodes form a cycle, stop before export and report the involved SP references. After cross-post matching, undo every cross-post merge participating in any cycle, retaining HD11 combinations, and check again. | Do not discard SP edges, split exact same-post combinations, select one merge arbitrarily to blame or force further merges. This is not the older TRUE/Jev cycle-contraction rule HD02. | [SMv2 procedure](../../sse_multivector/subject-order-probe.md#smv2--exact-same-post-combination), saved exact groups, rollbacks and ancestor checks make the policy reproducible. The saved SMv1 baseline predates HD11 and split cyclic groups back into individual subjects; it remains unchanged. |
| HD16 | **Implemented experimental choice — SMv1/SMv2 browsing:** retain every remaining subject node, including disconnected nodes and empty-mask subjects with their source posts. Preserve individual masks/IDs. Display distinct constituent subject names together; do not generate replacement titles. | No inferred parent-placement pass, transitive-edge reduction, equal-post display collapse or membership expansion is included. Do not import HR02's naming or display rules without an explicit choice. Empty masks do not acquire synthetic vectors or fabricated selections. | [SMv1 export and browser](../../sse_multivector/subject-order-probe.md#run-and-inspect), [implementation](../../sse_multivector/subject_matching_probe.py). Saved browser inputs remain unchanged when testing another rule. |
| HD17 | **Tested, not adopted — SOv1:** use OPHAC 0.5.4 complete linkage with cosine distance between subject vectors, comparing constrained and unconstrained grouping on the same saved six posts. The upstream constrained algorithm preserves strict ancestry. | Strict ancestry prevents combining equivalent ancestor/descendant entries and is stricter than HD08. Order preservation does not decide semantic equivalence or discover missing parent links. No stopping rule was selected. | [SOv1 method and limitations](../../sse_multivector/subject-order-probe.md). Keep its saved merge sequence as diagnostic evidence, not as the browsing hierarchy or the current combination algorithm. |
| HD18 | **Tested diagnostic only — ACv1:** compare an exact saved mask vector with each subject vector along an explicitly selected SP path, including its endpoint, and report all tied maxima. | A maximum exists even along an unsuitable path. It ranks candidates; it does not establish a valid parent or a merge. The illustrative paths were not an automatic retrieval test, and no acceptance threshold was selected. | [ACv1](../../sse_multivector/ancestor-cosine-probe.md). Preserve exact mask IDs and SP path references; do not silently replace an occurrence with another path using the same subject wording. |
| HD19 | **Implemented and tested, not adopted — AVv1 ancestor voting:** retrieve 3, 5 or 10 distinct subject strings with positive subject–subject cosine, including boundary ties. Each string votes once per strict ancestor using its shortest remaining path: `cosine * decay ** (hops - 1)`, with decay 0.5 or 1.0. For a multi-name node, cosine uses the best constituent comparison, not blended vectors. | All six settings remain exploratory. Votes transfer a neighbor's ancestors without establishing shared scope. Sparse SP branches can provide no support. Scores are sums, not cosines; no score or rank authorizes a placement. | [AVv1 scoring](../../sse_multivector/ancestor-voting-probe.md#inputs-and-scoring). Original evidence records retain each supporting subject, source node, path length and contribution. No production placement rule was selected. |
| HD20 | **Implemented experimental evaluation choice — AVv1:** temporarily exclude the queried node, its descendants, other occurrences of those exact subject strings and their descendants, repeating to closure. Use the same remaining candidates for direct-cosine comparison. Keep zero-support cases and tie-aware ranks visible. | This deliberately withholds more than one link and can remove the target parent's only supporting branch. It is not a deletion policy for the real hierarchy. Recovery of saved direct parents is not overall semantic accuracy; missing-link inspections are separate from hidden-link counts. | [AVv1 evaluation boundaries](../../sse_multivector/ancestor-voting-probe.md#evaluation-boundaries). The six-post sample does not establish generalization. A changed holdout or branch-comparison design must be identified separately, not presented as the same test. |
| HD21 | **Open — discovering missing global parent relationships:** no complete automatic placement method has been selected for the combined SP hierarchy. Comparing complete branches is an investigation, not an implemented scoring or acceptance rule. | Exact combination, shared children, cosine peaks and neighbor votes do not by themselves resolve broader/narrower scope. How to accept zero, one or multiple additional parents remains open. | Keep earlier saved graphs untouched. Propose the next method and its assumptions for user review; documentation of an open choice does not authorize implementation, training or inference. |
| HD22 | **Agreed SP-based interpretation and browsing rule; implemented in authorized isolated exports:** BCPv4's parent labels express ancestor containment, not immediate parenthood. Omit a direct browsing link when another path of at least two links connects the same nodes. | Preserve every hierarchy node, original relationship and provenance. Retain multiple parent routes; do not choose one longest chain. The browsing view changes, not source evidence or saved LG01 outputs. | The [first ancestor-application test](../../sse_multivector/branch-comparison-prompt-v1/README.md#saved-ancestor-application-test) applies 13 proposals and omits 15 browsing shortcuts without inference. The [continued Food test](../../sse_multivector/branch-comparison-prompt-v1/README.md#extended-food-test-export) adds nine saved proposals while retaining that export. The [HG8 draft](../../sse_multivector/branch-comparison-prompt-v1/README.md#proposed-hg8--apply-ancestor-relationships) remains separate from the tests: general conflict handling and production adoption are open. |
| HD23 | **Implemented and tested in an authorized isolated HG6–HG7 experiment; not production-adopted:** combine connected chains of saved `equivalent` answers, preserve all entries and mapped SP ancestry, remap/deduplicate previously compared pairs, and prompt only changed inputs. | The test assumes all 14 equivalence answers, including the unresolved Dietary practices / Diets flag. Structural validity does not validate their meanings. Retain unchanged judgments with source settings/receipts, not as new samples; new HG7 equivalences do not automatically trigger another pass. | The [combined-input test](../../sse_multivector/branch-comparison-prompt-v1/README.md#hg6hg7-combined-input-test) and shared adapter freeze the original-to-combined mapping, source evidence and previous answers. Rebuild from saved LG01 inputs to test different judgments or a repeat policy; do not edit the baseline. |

Experiment method documents describe the implemented procedures and link back
here for decision status. Keep rule IDs stable; update status and rationale when
the user changes a choice. Git records superseded wording. Generated outputs,
vectors and detailed experimental assessments remain separate ignored artifacts;
they are not substitutes for this register. SMv2 implements HD11 and the approved
HD15 cycle policy without changing cross-post selection, cutoffs or saved baselines.

#### Recording and replaying hierarchy decisions

**Hierarchy run identifiers — approved October 11:** every hierarchy run must
have a specific, unique version identifier so runs can be referred to
unambiguously. Report it with the exact hierarchy output and experimental
parameters, linking the existing frozen inputs, configuration and native
receipts used to generate that hierarchy. The naming format remains open.

**NEv2 user review (September 25):** Coffee, Food, and morning-greetings merges
accepted ("the other 3 look fine"); Beef / Beef products remains rejected.
These four case decisions do not settle the provisional merge/link rules or
authorize another run. The selected stress sample is not an accuracy estimate.
The saved graph remains unchanged; no per-node correction was applied.

Before a future run, record the selected decision IDs, their exact policy
versions and source hashes in its manifest. Preserve raw outputs separately
from derived graphs and browser views; later experiments must not overwrite
earlier evidence. Reuse unaffected saved stages, but recompute downstream
merges, memberships and navigation when their inputs change. This is a build
requirement, not a claim that the current runner already implements it.
The [offline merge stage](../../sse_multivector/navigation-research-v1/README.md#reversible-merge-stage)
records policy versions, source hashes and reversible inputs. Saved NEv2 and
TRUE10 replays preserve paths and post membership. The [offline construction
path](../../sse_multivector/navigation-research-v1/README.md#offline-construction-path)
now connects exact-mask-set consolidation, receipt-validated v38 titles, TRUE
input preparation, cycle merging, naming and browser export. HD04's subsequent
four-case naming run produced four valid titles without changing the sample's
links. The 19-node browser passed mechanical and interactive checks. Node IDs
are now hidden during browsing to avoid title truncation and remain available
in `?` analysis; stored IDs and displayed mask IDs are unchanged. HD06 still lacks a
published reprocessed browser view.

**HR02 — second 100-post hierarchy:** the existing goal, reaffirmed by the user on
September 25, is to generate a hierarchy the user is pleased with, not to
optimize cost, speed or teacher selection. Model comparisons are not its success
criterion. The user subsequently authorized individual title generation and
inspection with Astra low and unchanged v38, reusing all upstream data, then
approved TRUE scoring of those titles with all nodes retained and the two
user-rejected titles flagged. After scoring, the user also approved Astra low
for the six merged titles with unchanged v38. This does not authorize an
all-Luna comparison. The architecture is unchanged.
HR02 is the experiment's discussion ID; existing artifact paths and frozen
internal run IDs are retained; the new scoring run is `HR02-v38-gpt-6-astra`.

**HR02 execution (authorized September 25):** local TRUE scoring completed
for all 129 saved nodes, with exact-input cache reuse. The frozen plan
is `target/hierarchy-build-v1/astra-true-v1/plan.json`; it records policy versions,
source/input hashes and cache provenance. HD01–05 remain unchanged, including
the provisional HD02/03 rules. No membership expansion or Beef-specific repair
is included. The earlier Luna-title run is stopped, not complete; its saved
prefix supplied only verified exact-input answers to the new run. Six merged
titles completed in `experiments/hr02-merged-titles-v38-astra-low/` with six
subscription calls, no retries, and verified unchanged links/reachability.
The 116-node graph and 56 reduced links remain provisional. Browser export is
saved in `target/hierarchy-build-v1/hr02-browser-v1/`; the existing viewer passed
`--check` and interactive navigation/mask checks. It shows 98 represented posts
and adds an All notes entry. Both user-rejected titles remain flagged in analysis.
The user reviewed the hierarchy and found it promising but not validated:
TRUE's relationship decisions were not a good fit. The subsequent Jev baseline
and approved manual-placement diagnostic are recorded above. Completed inference
and this review do not settle the provisional merge policies.

**Hierarchy execution recovery (clarified September 24):** retry failed model
calls and reuse successful results. Preserve failed-attempt receipts and the
original inputs/settings; failure is not a No answer or permission to drop a
node. This is routine recovery, not an unresolved hierarchy-design choice. It
does not authorize a new run, unlimited retries or changes to the general
runner's current retry implementation.

For HD06, original node titles remain frozen; naming a newly merged node is
the separate HD04 operation, not regeneration of those original titles. Keep
the new comparison free of the excluded membership-expansion experiment.
Recording these designs, or HD03 as a candidate, does not authorize
implementation, inference or another hierarchy run.

Recovering missing node memberships is a separate operation. HDBSCAN's raw
tree is not the specified launch hierarchy.

### Remaining construction work and completion dependencies

The user approved surfacing the audit findings in the dependency map. These
separate required outcomes from conditional HDBSCAN-specific work; they do not
select implementation methods or new dates:

| Task | Required result | Completion dependency |
| --- | --- | --- |
| **24 · Recover missing node memberships** | If HDBSCAN is used, a repeatable recovery process beyond the six Coffee/Tea nodes, covering masks left unassigned or grouped elsewhere. Measure its work and cost. | Required to finish 03 only if HDBSCAN is used; available measurements inform 20 without waiting for all of 24. |
| **25 · Handle node equivalence and TRUE cycles** | Apply exact mask-set consolidation and a reversible, repeatable rule for HR02's equivalence candidates and cyclic TRUE answers. Provisional contraction does not prove that a cycle or equal title means semantic equivalence. | Complete for HR02; not a prerequisite for 02 or 03. The newer hierarchy's merging and conflict decisions remain within 02. |
| **26 · Collapse equal-note navigation steps** | Earlier mask-group navigation rule, implemented and regression-tested including shared children; validation remains pending. Preserve note sets, masks and provenance. | Not a prerequisite for 03. Any reuse in the newer hierarchy needs an explicit decision within 02; useful navigation remains required in 03. |
| **27 · Order notes within each node** | Optional, deferred implementation and validation using the node sort score defined in 04. Recursive sorting and parent-child score transfer are out of scope. | Needs score definition 04 if resumed; helpful to 03, not required. |
| **28 · Implement and validate the launch-scale build** | Turn the strategies tested in 03 and the scale findings into a runnable launch-scale build preserving validated hierarchy behavior, including cosine-filtered relationship checks. Handle large-group title inputs only if separate node-title generation is used. The relationship method is open. | Needs 03 + 22, plus 21 only if HDBSCAN is used; required to complete release snapshot 12 and model-track feasibility check 10. |

Task 24's recovery work is waiting for the workflow choice and is needed only
if HDBSCAN is selected. Its link to 03 stays helpful while the choice is open
and becomes required if HDBSCAN is selected. Relevant-content coverage remains
part of 03's required hierarchy-quality validation for any workflow; this does
not select a recovery method for a workflow without HDBSCAN.

25 is complete for
HR02: both merge stages, provenance-preserving naming and browser export are
implemented and tested. The four-merge user review accepted three and rejected
Beef; it was not blanket approval of the provisional rule. Further quality
validation of that HR02 evidence does not establish the newer hierarchy's
merging or conflict policy. The user approved removing 25's arrows into 02 and
03; the current merging and conflict decisions remain within 02. This does not
reopen 25, select a replacement rule or complete 02.
For 26, the earlier mask-group [browser implementation and regression checks](../../sse_multivector/navigation-research-v1/README.md#shared-child-collapse)
are complete; validation remains pending. The user approved removing 26's link
to 03. Any reuse in the newer hierarchy needs an explicit decision within 02.
Equal post-ID sets do not establish subject equivalence. This rule is separate
from HD22's redundant-link simplification, which retains every hierarchy node.
Understandable choices, meaningful narrowing and relevant-content coverage
remain required in 03; no replacement navigation rule is selected here.
On September 29, the user dropped recursive sorting from 27 and limited the work
to sorting within a node. A child's score is not transferred to its parent.
Earlier trials used prominence times relevance. The September 30 scope
clarification made the node sort score the required outcome, not that
particular formula. At that point its inputs and treatment of multiple masks
remained open under 04; 27 applies the selected definition. The later October 2
audit below froze an experimental choice. The October 5 deferral preserves it
without requiring its use in the next browsing build.

**Good-enough sorting evaluation approved October 2:** The user rejects
perfect prompts or identical repeated percentages as acceptance requirements.
Evaluate the existing experimental **PPv35-post-meaning-v1** candidate first
on twelve varied hierarchy-node meanings with posts not used in earlier sorting
trials. Agent assessment covers each complete order, especially its first ten
posts where available; actual smaller cohorts remain explicit. Earlier user
judgments and permitted about-equal swaps remain separate reference evidence.
Count mistakes that noticeably hurt browsing, such as incidental mentions
repeatedly preceding posts mainly about the node. Isolated mistakes, small
differences and close-order reversals are acceptable. Change the method only
for a substantial recurring problem across nodes or an independent rerun;
percentage variation alone does not warrant more tuning. If the finite audit
passes, freeze the candidate for the next browsing build and stop prompt or
architecture search. Later substantial recurring browsing failures can reopen
it. This authorizes the audit and stopping rule, not an inference that it has
passed, new user labels, hierarchy-membership changes or production deployment.
The sorting formula, saved meanings, SSE learned layers and earlier experiments
remain unchanged during this evaluation.

**Finite sorting audit completed October 2:** The current PPv35 candidate
passes the approved good-enough rule and is frozen for the next browsing build.
Two agent-reviewed complete-order passes cover twelve fixed meanings, 101
post/node diagnostic assignments and 62 complete posts fresh to sorting.
All node-related selected SP entries participate: 760 initially prepared entries
plus six source-only completeness additions, 766 total. Actual cohort sizes are
Music 10, Art 10, nostr 10, Effective communication 8, Family 10, Physical
movement 8, Festive gatherings 10, Food and drink 10, Chocolate and cacao 4,
Animals 4, Positive emotions and attitudes 10, and coffee 7. Focused posts
precede incidental mentions in the clear contrasts; close/mixed swaps and two
possible isolated lower-order swaps are acceptable. No substantial recurring
browsing failure appeared in either pass. These are agent assessments, not new
user labels or a general accuracy estimate; music-heavy sources, shared posts,
Communication's limited positives, Chocolate's weak contrasts and Coffee's
flavor/beverage boundaries remain explicit limitations.

The frozen experimental sorting score uses PPv35 prominence for the complete
post against the same saved NodeDescription-v3 meaning, multiplied by SSE
relevance for saved SP subject plus newline plus context against the existing
standalone node title. Relevance is `(clip(cosine, -1, 1) + 1) / 2`; retain SSE's
final learned layers. A post takes the highest entry sorting score among its
SP entries selected in that node. Keep the formula, prompt, saved meanings and
encoder fixed for the next browsing build; stop prompt/architecture search.
Reopen only for a concrete substantial recurring browsing failure. The audit
did not change the hierarchy or deploy sorting, and does not complete task 27
or launch-scale validation. Native evidence and accounting are recorded in
[model-runner.md](../../sse_multivector/model-runner.md).

User-approved Coffee/Eggs post-ordering checks for 27 (September 29–30): the user reviewed the
complete wording with URLs omitted and established ten clear expected orders.
These judgments establish expected post order; they do not select
a scoring formula, approve mask-prominence outputs or adopt a mask-aggregation
rule.

| Hierarchy node | Post expected higher | Post expected lower |
| --- | --- | --- |
| coffee | Decaf drinkers valuing experience and flavour (`2dc50a30`) | Sunday weather with hot coffee (`82d3d344`) |
| Eggs | Explanation of preserved century eggs (`11d2afb1`) | Rocket stove with eggs among the foods cooked (`99e6a514`) |
| Eggs | Mixed diary with laying hens and several egg preparations (`eaa6a5e6`) | Rocket stove with eggs among the foods cooked (`99e6a514`) |
| coffee | Roasting your own beans (`056e6466`) | Afternoon errands and morning coffee (`e0508834`) |
| Eggs | Mixed diary with laying hens and several egg preparations (`eaa6a5e6`) | Four-egg dinner (`fbd52a1d`) |
| coffee | Iced coffee served in ice (`76e19c3e`) | Afternoon errands and morning coffee (`e0508834`) |
| coffee | Roasting your own beans (`056e6466`) | Hashtag-heavy second-coffee post (`862486d8`) |
| Eggs | Mixed diary with laying hens and several egg preparations (`eaa6a5e6`) | Coffee with raw cream and raw egg yolk (`f4c5aa5f`) |
| coffee | Coffee with raw cream and raw egg yolk (`f4c5aa5f`) | More coffee in cool places (`37f44e1f`) |
| coffee | Iced coffee served in ice (`76e19c3e`) | Coffee with raw cream and raw egg yolk (`f4c5aa5f`) |

For another coffee and Sunday wishes (`737eaa89`) versus errands (`e0508834`),
the user judged the posts about equal, with a tentative tiny preference for
another coffee because of "but I need another one." Record this separately
from the ten clear ordering checks. No numeric tolerance for "about equal"
has been agreed.

On September 30, the user reviewed decaf drinkers (`2dc50a30`, A) versus
roasting your own beans (`056e6466`, B) inside Coffee, with complete wording
and the image URL omitted, and answered "hm i'd say they're about the same".
Record them as about equal, with no preferred direction, separately from the
ten clear orders. PPv30-node-v1 gives prominence 100 and 98 and sorting
scores 90.154658 and 87.301384 respectively, a difference of 2.853274. No
numeric tolerance or tie rule is approved; this comparison is not counted as
passed or failed and does not approve the assessed percentages or formula.

The user next reviewed roasting your own beans (`056e6466`, A) against
"Is there coffee for me?" (`78462b92`, B) inside Coffee, with complete wording
and image URLs omitted, and said "they seem decently evenly matched. maybe A".
Record roughly equal with a tentative preference for A, separately from the
ten clear orders. Saved PPv30-node-v1 prominence is 98 < 100; sorting scores
are 87.301384 > 83.173849, a difference of 4.127535. The sorting-score direction
agrees with the tentative preference, but no numerical tolerance for closeness
or tie rule was approved, so this pair is not counted as passed or failed.
No formula, exact percentages or production rule was selected.

The user next reviewed decaf drinkers (`2dc50a30`, A) versus "Is there coffee
for me?" (`78462b92`, B), with complete wording and B's image URL omitted,
before seeing sorting scores, and answered "about equal maybe". Record a
fourth, tentative about-equal Coffee judgment with no preferred direction.
Both saved PPv30-node-v1 prominence values are 100; highest SP-context
relevance is 0.901547 and 0.831738, producing sorting scores 90.154658 and
83.173849. The difference, 6.980809 toward A, comes entirely from relevance.
No numerical tolerance or production tie rule is approved; this judgment
does not approve the percentages, formula or a change to relevance. No new
inference, encoding or result changes were required.

The user then confirmed that either order is acceptable for pairs judged about
equal. This applies to all four recorded Coffee comparisons, including the two
with tentative small preferences: neither direction is an ordering mismatch.
Keep them separate from the eleven clear expected Coffee/Eggs/Music pairs and
Photography's three-post judgment; they do not distinguish prominence from
prominence × relevance. No equal sorting scores, numerical gap limit,
production tie handling or rule for identifying other about-equal pairs was
selected. The sorting calculation and saved results stay unchanged.

The user next reviewed the complete original wording of all seven Eggs posts,
with URLs omitted and highest sorting score first, and answered "lgtm".
The accepted displayed order is century eggs (`11d2afb1`), avoiding eggs and
snacking on chocolate (`612fa3c5`), mixed diary with hens and egg preparations
(`eaa6a5e6`), coffee with raw egg yolk (`f4c5aa5f`), four-egg dinner (`fbd52a1d`),
duck-egg breakfast burrito (`ee3404d5`), then rocket stove (`99e6a514`).
Record one accepted seven-post Eggs order, separately from the eleven clear
Coffee/Eggs/Music pair checks, Photography's three-post judgment and the four
about-equal Coffee pairs. Do not infer 21 independent pair judgments or require
strict differences between every adjacent post. Both saved prominence alone
and sorting score produce this accepted order. This review does not select a
formula, approve numerical values or adopt production sorting. No new model
calls, encoding or saved-result changes were needed.

The user then reviewed the complete original wording of all fourteen Coffee
posts, with URLs omitted and highest sorting score first, and answered "lgtm".
The accepted displayed order is decaf (`2dc50a30`), roasting (`056e6466`), iced
coffee (`76e19c3e`), coffee request (`78462b92`), raw-cream/egg-yolk coffee
(`f4c5aa5f`), coffee in cool places (`37f44e1f`), second coffee (`862486d8`),
half & half (`143fee76`), another coffee/Sunday wishes (`737eaa89`), errands
(`e0508834`), coffee/movement/stretching (`8a025f69`), Sunday weather/hot coffee
(`82d3d344`), breakfast burrito/coffee (`ee3404d5`), then the Tolstoy quotation
with `#Coffee` (`be8d07d4`). Record one accepted fourteen-post Coffee order,
alongside the accepted seven-post Eggs order. Both remain separate from the
eleven clear pair checks, Photography's three-post judgment and the four
about-equal Coffee pairs; do not infer 91 independent new pair judgments or
strict differences between every adjacent post. The earlier slight weather
preference remains recorded, but movement/stretching above weather is now
acceptable in this complete-order review. This approval does not select the
formula, numerical values or production rule. No new model calls, encoding or
saved-result changes were needed.

The user directs the agent to observe sorting on other subjects using the
established examples; obtaining new user ordering labels or asking the user
to inspect each new order is not required. Agent assessments remain distinct
from user judgments. The agent selected Children, Literature, Psychological
distress and Bitcoin from the saved raw hierarchy, covering nineteen distinct
post/node-title inputs and twenty-five matching SP entries. Test the unchanged
PPv30-node-v1 prominence × SP-context relevance calculation, taking each post's
highest sorting score, and compare with prominence alone. Keep existing
judgments, source memberships, prompt and production decisions intact. This
authorizes the bounded experiment and agent observation, not adoption or a
change to the calculation. The run allows at most thirty-eight new Astra-low
subscription attempts including eligible retries, with no paid fallback;
selected-context SSE encoding runs locally on CPU.

The completed transfer run has twenty-five valid SP cases from nineteen new
assessments and six exact-request reuses, with no failures or retries. Agent
inspection of all nineteen post/node inputs found no clear ordering error:
the baby-development update leads Children; the audiobook discussion leads
Literature; the personal anxiety/chemotherapy update leads Psychological
distress; Bitcoin payments, the workshop and community commentary precede
incidental Bitcoin tags. Prominence alone and prominence × relevance produce
the same complete order in all four nodes, so this sample adds no demonstrated
ordering benefit from relevance. Literature and Psychological distress have
few posts, and fine distinctions among incidental Bitcoin mentions remain
uncertain; this is not broad validation or new user approval.

Relevance nearly removes one meaningful prominence difference in Children:
the son's ice-cream conversation has prominence 55 and relevance 0.515541,
while the Lunchly market argument has 40 and 0.707843. Their sorting scores
are 28.354729 and 28.313701, only 0.041028 apart, still in the agent's preferred
direction. This is a concern about the narrowed gap, not an observed reversal
or an agreed minimum difference. The SP context says "son" without stating an
age, so that comparison alone did not establish the cause. The user authorized
the saved-input relevance diagnostic on October 1, and it is now completed.
Prompt, formula, memberships and production decisions remain unchanged.
The detailed orders, agent assessments, usage and replay checks are recorded in
[model-runner.md](../../sse_multivector/model-runner.md).

The diagnostic verifies the correct Children title, complete content-token
selection and unchanged encoder provenance. With prominence fixed at 55,
the original words "My son" have relevance 0.754024 and sorting score
41.471298. The original opening ice-cream paragraph has relevance 0.502639
and sorting score 27.645136, below the unchanged Lunchly control's 28.313700.
The saved SP context's 0.515541 lies close to the full story result. Added
story detail lowers relevance in both original prose and the SP context;
the low relevance is not merely an SP summary-wording effect. These inputs
also retain the son's unspecified age, so age ambiguity alone does not
explain the difference. This is evidence about these inputs, not a general
causal model or approval to change production sorting. Two local five-row
SSE comparisons completed with replay parity; twelve existing comparison
tests passed. No teachers were called.

Replacing every context with SP subject wording alone cannot preserve the
accepted iced-coffee-above-raw-yolk order: both SP subjects are Coffee, giving
the same relevance multiplier to prominence 95 and 100. The user then approved
comparing relevance from SP subject plus its unchanged context, with prominence
fixed and existing accepted orders checked. That comparison is now completed
across seventy-one SP entries, forty-five post/node memberships and eight nodes,
with no new teacher calls.

All eleven clear Coffee/Eggs/Music comparisons retain their accepted
directions. Eggs, Photography, Music and the four transfer nodes keep their
complete orders. Coffee only swaps errands and another coffee, a pair the
user judged about equal with either direction acceptable. The son's Children
relevance rises from 0.515541 to 0.541385; its sorting-score lead over Lunchly
rises from 0.041028 to 0.178627. This is a modest numerical change with no
clear ordering failure corrected or agreed minimum gap. The agent recommended
keeping context-only relevance for the next broader subject trial. The larger
October 1 comparison below subsequently corrects a restaurant reversal; no
production input or formula change is adopted. The small shared comparison
option, nineteen comparison tests and 118 runner/worker checks are recorded
in [model-runner.md](../../sse_multivector/model-runner.md).

**Further non-food sorting trial approved and completed October 1:** the user
approved the agent's bounded assessment using context-only relevance. Every
direct member of Dogs, Sleep and tiredness, Christmas, Workouts and Moral
goodness was included: fifty-one saved SP cases, sixteen post/node inputs and
thirteen original posts. Fixed PPv30-node-v1 / Astra low produced sixteen new
valid assessments and thirty-five exact-request reuses without failures or
retries. Native usage is 13,510 input and 5,010 output tokens, including 447
reasoning tokens; catalog reference is $0.3856 and incremental cash is zero.

All five complete sorting-score orders match prominence-only orders. The
agent found no clear wrong order: dog-feeding posts precede dog hashtags;
sleep/tiredness accounts precede embedded advice; the Christmas-lunch headline
leads mixed-topic mentions; gym session precedes workout joke and brief advice.
The generosity story leads the conduct list in Moral goodness. The pre-run
reverse preference was explicitly uncertain, and the story's sharing and
hospitality give the observed direction a defensible basis; its scope and
allocation remain uncertain. Forty-three native agent case reviews accept
ordering and eight correlated Moral goodness cases remain uncertain, covering
two distinct inputs. These are agent assessments, not new user labels or an
accuracy rate. Five original-mask replay controls, independent products and
post maxima, unchanged source hashes and twenty-three workflow tests passed.

The agent recommends fresh non-food posts outside the original 100-post
sample, rather than further wording changes without an observed failure. The
user approved the bounded saved-input trial described below. Prompts, hierarchy,
source posts, masks, formula and production adoption remain unchanged or open
as before; detailed orders and
provenance are in [model-runner.md](../../sse_multivector/model-runner.md).

**Fresh-post sorting trial completed October 1:** nine posts from the saved
music corpus are disjoint from the original 100. Forty-three unchanged ASv6.23
SP entries were selected for existing Music, Photography and Bitcoin titles,
covering eleven post/node inputs. These are explicit diagnostic assignments,
not new hierarchy memberships or validation of automated placement.
PPv30-node-v1 / Astra low, context-only relevance and highest prominence ×
relevance per post remained fixed. Eleven new valid assessments and thirty-two
exact-request reuses completed without failures or retries. Native usage is
7,916 input and 1,873 output tokens, including 204 reasoning tokens; catalog
reference is $0.17281 and incremental cash is zero. No SP/MP generation ran.

Photography orders band photographs before photographing a drumming father
before photography incidental to song inspiration. Bitcoin support instructions
precede incidental Bitcoin associations. Both match the pre-run agent
observations and prominence-only orders. In Music, four focused posts lead the
two mixed posts, but relevance moves the wholly musical question “What does
music mean to you?” below the Goa-track appraisal and the AI-track credit with
community tags. Those subtle directions remain uncertain; this is neither a
proven failure nor a demonstrated improvement from relevance. Thirty-four
native agent case reviews accept ordering; nine uncertain cases share the three
Music inputs. These are not user labels or an accuracy rate. All source hashes,
complete context selections, independent products and post maxima passed;
139 relevant source/regression tests passed before generation. Older SP wording
and music-corpus selection limit generalization. The user then approved the
question-text check below. Production adoption remains open.
[model-runner.md](../../sse_multivector/model-runner.md) records full orders,
source protection and native evidence.

**Music question relevance check completed October 1:** both selected SP
contexts for “What does music mean to you?” were replaced as relevance inputs
by its exact original post, including the trailing space. All saved prominence
values and other relevance inputs stayed fixed. Question prominence remains
100; relevance changes from the best context's .853925 to .845908 and its
sorting score from 85.392473 to 84.590802. All three full orders stay unchanged;
the question remains below the Goa appraisal and AI-track credit in Music.
Replacing its SP wording with the question itself does not remove that position
or demonstrate an ordering improvement. The agent still finds these focused
Music comparisons uncertain and recommends returning to broader saved-input
transfer tests with context-only relevance and the formula fixed. The user
then approved the three-node saved-input trial below; no production input
change is adopted. Native offline CPU
preparation/collection used forty-four complete rows, with source hashes,
independent products and post maxima verified. Re-encoding four other cases
changed their sorting scores by at most .000001598; all input text and orders
are preserved. Fourteen existing comparison tests passed; no teacher calls,
new user judgments, paid resources or task accounting changes occurred.

**Three fresh subjects approved October 1:** the user approved five fresh posts
each for three existing nodes outside food and music, with the calculation
fixed and agent observation. The completed `ppv30-fresh-nonfood-v2` trial uses
fifteen posts from the saved 48-post coverage expansion for Literature,
Psychology and philosophy, and Bitcoin. Their IDs are disjoint from the original
100 and the prior nine-post sorting trial. Ninety-nine exact reviewed ASv6.23
SP entries are explicitly selected: twenty-one Literature, thirty-three
Psychology and philosophy, and forty-five Bitcoin. None of these entries has
an explicit saved subject correction. This is a selected earlier development
corpus, not unseen data or an automatic-membership test; the graph is unchanged.
The agent recorded fifteen pre-run observations, including uncertainty among
focused posts and the poem's interpretation, without new user labels.

PPv30-node-v1 / Astra low, context-only relevance and highest prominence ×
relevance per post remain fixed. Fifteen distinct complete-post/title inputs
share prominence answers across SP entries. Native preparation and 139 relevant
workflow tests passed without source changes. The zero-cash reservation bounds
new attempts to thirty, including eligible provider retries; saved SP/MP,
source posts, titles, hierarchy and earlier results are protected. No new SP/MP
or broader-corpus generation runs, respecting the separate generation hold.
Local encoding scales with selected contexts and titles, and complete-post
inference with selected post/node inputs rather than every post/node pair.
All ninety-nine cases are valid from fifteen new calls and eighty-four exact-
request reuses, with no retries or failures. Local CPU encoding covered ninety-
nine complete contexts and three unchanged titles. All three orders preserve
the clear pre-run focused-versus-mixed comparisons: book/reading posts and the
poem precede the fear-of-thinking argument; focused reflections/advice precede
mixed year-end gratitude; three Bitcoin technology posts precede Bitcoin/Nostr
optimism, which precedes mostly Nostr hardware. Changes from prominence alone
mainly resolve ties; the Alan Watts post also moves above two prominence-100
posts. No clear ordering improvement is established among focused posts.

The Bitcoin privacy post has prominence 100 but highest context relevance
.662586 and sorting score 66.258643, below block transmission 91.148035 and
scaling 88.740711, also prominence 100. All fourteen saved privacy contexts omit
Bitcoin and retain only parts of the technical connections, although the
teacher recognizes the complete post's Bitcoin meaning. Missing context or
technical-domain recognition may explain the gap; the cause and strict
within-focus direction remain uncertain. The poem's contexts mostly describe
imagery rather than retaining the full literary framing, giving a similar
unresolved question. Fifteen final native agent reviews accept four clear mixed-
post comparisons and retain uncertainty for eleven focused inputs; these are
not ninety-nine independent labels or an accuracy rate. No new user judgments,
exact-percentage approvals or numeric tie threshold are introduced.

Independent source, allocation, encoder, product and post-maximum checks pass;
protected sources and earlier comparisons are unchanged. A concurrent unrelated
CLI addition caused a pre-inference stop and was reviewed/audited through the
native code-upgrade mechanism before any teacher call. The result uses $0 incremental cash and a $0.225350 catalogue reference estimate. The user approved comparing the complete Bitcoin
privacy post with saved contexts as the relevance input, holding prominence 100
and the formula fixed. The completed diagnostic is recorded below. The transfer
trial is complete and production adoption remains open. Native source selectors,
full orders and provenance are described in
[model-runner.md](../../sse_multivector/model-runner.md).

**Bitcoin privacy complete-post relevance check completed October 1:** only
the fourteen privacy entries in the existing five-post Bitcoin trial use the
exact complete original post as relevance input; they share one encoder row.
All 356 original UTF-8 bytes are retained. Saved prominence stays 100, the
formula and Bitcoin title stay fixed, and the other thirty-one context inputs
are unchanged. Relevance drops from the highest context's .662586 to .542481,
and the sorting score from 66.258643 to 54.248130. The Bitcoin order remains
block transmission, scaling, privacy, Bitcoin/Nostr optimism, and Nostr
hardware with zaps. The other four post maxima and winners are bit-identical.
The Literature and Psychology and philosophy comparisons are untouched.

The replacement does not close the privacy post's gap to the other focused
Bitcoin posts. Its complete meaning still concerns Bitcoin privacy, but this
result does not identify the cause of its lower relevance or establish a
benefit from the strict focused-post order. The user approved a
bounded wording diagnostic: replace “a node” with “a Bitcoin node” in the
opening of a diagnostic copy, keeping other words, title, prominence and formula
fixed. This checks sensitivity to explicitly naming Bitcoin; the completed check is
recorded below. Original source posts and production input policy remain unchanged.

Native offline CPU preparation/collection used thirty-three complete rows with
the unchanged SSE checkpoint/model/runtime. Exact inputs, complete token
selections, forty-five independent products, five post maxima, full orders and
twenty protected hashes were verified. Five nonwinning context cases differ
on re-encoding by at most .000002768269 sorting-score points; all other inputs
and post maxima remain fixed. Fourteen comparison tests passed. Fourteen native
uncertain agent comments preserve original history and represent one privacy
post, not independent labels. No teacher calls, new token usage, user judgments,
paid resources or task accounting changes occurred. Production adoption remains
open; [model-runner.md](../../sse_multivector/model-runner.md) records provenance.

**Bitcoin privacy wording check completed October 1:** native preparation keeps
the same forty-five cases/five posts and replaces only the privacy post's
opening “a node” with “a Bitcoin node” in its relevance input. Fourteen privacy
entries share one complete 364-byte diagnostic copy; the exact 356-byte original
and its source spans are separately retained. Prominence 100, title, formula
and other contexts stay fixed. Thirty-three offline CPU rows were encoded with
the unchanged SSE model; no teacher generation or paid resources are involved.
The shared `--relevance-source-replace` option adds explicit source-bound
replacement support while preserving the default exact-text requirement. Its
production-path integration test failed before implementation and passed after;
142 relevant comparison, ranking, selection, experiment and worker tests passed.
Saved subjects, masks, source posts, hierarchy, earlier comparisons and task
accounting remain unchanged. Relevance rises from .542481 for the original
complete post to .566381 for the named copy; sorting score rises from 54.248130
to 56.638104 (+2.389974). This remains below the highest original SP-context
score 66.258643 and the focused block/scaling posts. The full Bitcoin order
does not change. All thirty-one other case cosines/products and all four other
post maxima/winners are bit-identical. The intervention shows that explicitly
naming Bitcoin affects this copy but does not close the gap, identify its full
cause or demonstrate an ordering improvement. Strict focused-post directions
remain uncertain; no exact-share approval, numeric tie threshold, new user
judgment or policy of rewriting posts is introduced.

Independent derivation, complete-selection, encoder-identity, product,
post-maximum/order and twenty-five protected-hash checks passed. Fourteen native
uncertain agent comments preserve history and represent one post/title input.
No new teacher calls/tokens or cash were used. The user subsequently authorized
the following comparison before and after SSE's final learned projection.
Production adoption remains open. Native provenance and workflow semantics are recorded in
[model-runner.md](../../sse_multivector/model-runner.md).

**SSE projection comparison approved October 1:** The user's "proceeed"
authorizes a bounded local comparison using the agreed Coffee/Eggs examples
and fixed Bitcoin posts. Native preparation freezes all twenty-one Coffee/Eggs
posts and five Bitcoin posts: eighty-two saved SP contexts plus three node
titles, with identical text, token-selection spans and saved PPv30-node-v1
prominence in both runs. Only the worker pooling descriptor changes between
the checkpoint's selected-token mean and its existing mean → linear → ReLU →
linear output. The same SSE-trained encoder weights are used in both; this
does not recover the pretrained model's original encoder weights.

The formula and highest-context post maximum stay fixed. This authorizes
testing the component, not removing it from production or rewriting source
posts. Ten clear Coffee/Eggs expected pair directions, four about-equal pairs
accepting either direction, and two accepted complete-node orders remain
distinct observations. Bitcoin focused-versus-mixed orders remain agent
assessments, with strict directions among focused posts uncertain. No new user
labels, numeric tie threshold, teacher calls or paid resources are introduced.
The two eighty-five-row worker runs and native collection are complete. Both
modes retain ten of ten clear Coffee/Eggs directions, including iced coffee
above raw-yolk coffee (82.647530 > 74.316804 before the projection). Prominence
alone still reverses that pair, so relevance cannot be eliminated on this
evidence. Eggs and Bitcoin keep identical complete orders. Coffee swaps three
pair directions: coffee request above iced coffee, hashtag-heavy second coffee
above More coffee in cool places, and errands above another coffee/Sunday
wishes. The last is an approved about-equal pair accepting either direction;
the other swaps show no clear agent-assessed benefit or separately agreed
strict pair preference. The previously accepted Coffee sequence changes;
all ten clear checks still pass, and the new complete order has not been
approved by the user.

Bitcoin privacy's sorting score rises from 66.258643 to 73.438592 before the
projection. It remains below block transmission and scaling, and above both
mixed posts. This changes its numerical gap without demonstrating a better
order or approving a target gap. The agent recommends keeping the existing
projection; there is no clear sorting improvement from removing it. The user
has now approved the unchanged calculation on the remaining hierarchy nodes
with at least two posts in the saved corpus, using saved SP contexts and agent
observation. The preparation below records this transfer test; adoption
remains open.

Independent application of the saved projection reproduces all eighty-five
vectors exactly. All 164 cosine/products, fifty-two post maxima and six full
orders verify; the projected rerun reproduces all three original node orders.
Thirty-eight protected source/artifact hashes stay unchanged. Twenty-six
native uncertain agent comments preserve history, one per post/title, without
new user decisions. Native generation accounting is unchanged; no new teacher
calls/tokens or cash are used. Worker/CLI support passes forty-five relevant
tests; the broader experiment suite passes 101 of 102, with the unrelated new
parent-guide test blocked by missing `tiktoken`.
[Model-runner results](../../sse_multivector/model-runner.md) record the frozen
scope, both comparison hashes, workflow semantics and check evidence.

**Remaining-node transfer approved October 1 (completed):** The latest
"proceed" authorized fixed PPv30-node-v1 / Astra-low prominence, saved SP-context
relevance with SSE's final learned layers, prominence × relevance and the
highest selected-context sorting score per post. Native execution completed
104 remaining direct-member nodes, 354 post/title inputs across 94 original
posts and 587 context cases. All are valid; 233 exact-request case reuses and
one successful HTTP 503 retry yield 355 sent attempts. No source posts, graph,
prompt, earlier comparisons, weights or production behavior were changed.

The agent froze 104 pre-run node observations, read all complete posts and
resulting orders, then recorded one post-run assessment per node. Clear
pre-run directions hold in forty-nine of fifty such nodes; Food and drink
reverses the expected restaurant-post/mixed-diary order, 42.752028 < 43.444485,
although prominence is 85 > 61. Its sole selected context names Khyber Pass
without saying restaurant; the saved SP subject explicitly says restaurant.
Relevance causes the numerical reversal; omitted subject meaning is a
hypothesis to test. Five modest directions hold but remain tentative, and
forty-nine nodes had no fixed strict direction. These are related agent node
observations, not independent pair labels or population accuracy. Relevance
also puts the pizza-restaurant plan above the pizza-day greeting where
prominence alone reverses them, adding one concrete agent-assessed benefit.

Ambiguous title meaning remains unresolved: `grownostr` is interpreted as
homegrown food/self-sufficiency for chicken stock (prominence 85) and growing
Nostr for the steak/preservation diary (2). The trial does not repair node
meaning or membership. Five suspect irrelevant memberships receive prominence
and sorting score zero. All 587 own-node cosine/products, 354 post maxima and
104 orders verify, with 687 CPU encoder rows and sixty unchanged protected
hashes. Fifty-two relevant existing tests pass; three adapter checks reran
successfully after an unrelated preparation-only provenance addition. Native
accounting reports 267,585 input and 73,855 output tokens, including 12,138
reasoning tokens; API catalog reference $6.368600 is separate from subscription
cash $0 and unmeasured quota. 

The user subsequently approved testing saved SP subject plus context against
context alone, with prominence, SSE and formula fixed and earlier agreed
checks retained. The completed comparison below addresses this restaurant
reversal; it does not settle ambiguous title meaning by itself. This remains
saved developmental-corpus coverage, not unseen accuracy
or production adoption. Teacher/encoder work scales with selected memberships
and texts. The native offline diagnostic additionally emits 587 × 104 title
cosines; this bounded cross-product is not a production design. New SP/MP or
broader corpus generation, hierarchy changes and recursion remain outside
this test. [Model-runner results](../../sse_multivector/model-runner.md) record
provenance, exact inputs, comparison hash and review limits.

**Remaining-node subject plus context approved October 1 (completed):** The
latest "proceed" authorized an offline paired comparison on the same 104 nodes
plus Coffee, Eggs, Music and Photography. Native preparation, the local CPU
SSE worker and native collection completed 633 saved SP entries across 380
post/node inputs, 96 original posts and 108 nodes. Only the candidate relevance
input changes: saved SP subject, newline, unchanged SP context. Existing
complete-post/title prominence, SSE checkpoint and final learned layers, node
titles, formula and highest selected-entry sorting score per post stay fixed.
No new teacher calls, source changes, paid resources or ledger edits occurred.
The existing shared option sufficed; context alone remains the CLI default.

The Food and drink restaurant post (`add487c4`) now has relevance 0.542109 and
sorting score 46.079266, above the mixed diary (`eaa6a5e6`) at 42.367180.
Context alone put them at 42.752028 < 43.444485. Prominence remains 85 and 61.
The added subject is "Khyber Pass restaurant". All fifty earlier clear agent
node expectations now hold, versus forty-nine with context alone; five modest
directions remain tentative and forty-nine nodes had no strict expectation.
All eleven earlier clear Coffee/Eggs/Music comparisons and the accepted Eggs
and Photography complete orders remain intact. Coffee only swaps the already
acceptable about-equal errands/another-coffee pair. No new user labels, exact
percentages, gap thresholds or population accuracy claims are introduced.

Eleven complete node orders change, ninety-seven remain identical. Other
changes affect previously unsettled comparisons; coffee-shop rave versus
laptop-rule, focused dinner/tea/bread posts and ambiguous hashtag nodes remain
uncertain. Native reviews record 108 related node assessments bound to both
comparison hashes: 54 accept the stated clear directions or agreed checks,
54 retain uncertainty. Original review history and 77 protected hashes are
preserved. The `grownostr` prominence discrepancy remains: homegrown-food
meaning gives stock preservation 85, while growing-Nostr meaning gives the
steak/preservation diary 2. This fixed-input relevance trial cannot repair it.

Both sets of 633 own-node cosine/products, 380 post maxima and 108 orders verify;
1,475 complete encoder selections have no truncation. Forty-five relevant tests
pass, including actual local T5 worker integration. Work grows with selected
entries, adding one short saved subject per context. The native 633 × 108 title
diagnostic per mode remains bounded and is not a production design.
[Model-runner results](../../sse_multivector/model-runner.md) record exact
inputs, paired hashes, changed orders, verification and review limits.

The agent recommends saved SP subject plus context for subsequent sorting
experiments, keeping prominence, SSE and formula fixed; production adoption
remains open. The user subsequently approved the bounded fixed-meaning
`grownostr` prominence trial completed below. Hierarchy changes and recursion
are outside both comparisons.

**Fixed GrowNostr meaning approved October 1 (completed):** The
latest "proceed" authorizes one consistent meaning across the fifteen existing
direct-member posts. The node contains fourteen hashtag masks and one
food-growing mask. The [original GrowNostr announcement](https://www.thesurvivalpodcast.com/grow-nostr)
describes growing Nostr participation and communities through diverse content
and interaction. Its use as the fixed trial meaning is grounded in that source;
the earlier title acceptance does not adopt a definition or repair membership.

Tested **PPv30-grownostr-v1** changes only the title-interpretation paragraph,
retaining the allocation instructions, complete post/title inputs, output
schema, Astra-low subscription settings and fifteen saved baselines. Native
preparation and four pre-run agent observations preceded fifteen fresh valid
calls, without failures, retries or reuses. The bounded run permitted at most
thirty attempts including eligible provider retries, with zero incremental
cash and no paid fallback. Relevance reuses the exact saved SP subject-plus-context vectors. SSE,
node title, formula and highest selected-entry post rule stay fixed. Forty-five
relevant existing checks pass. No workflow/production code, hierarchy, SP/MP or
other-node change occurred; production adoption and broader validation remain
open. [Model-runner results](../../sse_multivector/model-runner.md) record the
source-grounded meaning, prompt revision and frozen scope.

The stock-preservation post's prominence changes from 85 to 7 and the steak
diary's from 2 to 5. Both now separate food work from their GrowNostr community
connection under the same meaning. Their sorting scores become 5.913327 and
3.984306 using unchanged relevance. The salsa/Nostr-sale post drops from 60
to 11. These interpretation corrections do not approve exact percentages or
a complete node order. The food-growing outlier drops from 80 to 15 because
its Nostr profile reference is credited as community recognition; whether
that warrants nonzero prominence remains uncertain under identifier exclusion.
Membership is preserved. Fifteen native post-run agent assessments accept
three topic-separation corrections and retain twelve uncertainties, preserving
the original pre-run comments and all user labels.

All fifteen exact inputs, baselines, allocations, cosine/products, maxima and
the complete order verify, with bit-identical reused relevance and 99 unchanged
original protected hashes. No SSE worker or new encoder selection is needed;
all other 107 nodes and earlier agreed checks remain untouched. Native usage
is 12,202 input and 2,560 output tokens including 80 reasoning tokens; catalog
reference $0.250020 remains separate from cash $0 and unmeasured quota. 

The agent recommended checking the same fixed-meaning approach on `coffeechain`
next, with relevance, SSE and formula fixed; the user approved the completed
trial below. These developmental trials do not establish a general description
method, broader sorting quality or production adoption.

**Fixed coffeechain meaning approved October 1 (completed):** The user's
"proceed" authorized one consistent meaning across the eleven saved direct-member
posts in `coffeechain` (`S3c005e1a4f`). Their existing prominence answers already
mostly used a coffee-sharing community meaning. The
[Nostr community guide](https://quillie.github.io/nostr-wegweiser/),
[a public author greeting](https://thegrinder.npub.pro/post/note1atxm208fgp2nq8fklknqseglftssann06r8y09gmq0re3ea6dt7q0xern2/)
and complete saved posts ground the trial definition: the #coffeechain community
on Nostr, where people share coffee experiences and exchange morning greetings.
The earlier user correction to preserve `#` remains recorded; neither the saved
sorting title nor hierarchy changes in this comparison.

Tested **PPv30-coffeechain-v1** revises only the interpretation paragraph,
retaining complete original post/title inputs, schema, allocation instructions,
Astra-low subscription settings and eleven saved baselines. Four pre-run agent
observations prescribed no exact percentages, gaps or strict complete order.
Eleven fresh valid calls completed with no retries, failures or reuse, within
the twenty-two-attempt bound and zero-cash reservation. Relevance reuses exact
SP subject-plus-context encoding; all 738 cached rows and eleven relevance
values stay bit-identical. SSE learned layers, title, formula and highest-entry
post rule stay fixed, with no new worker run or encoder selection.

Home roasting changes from prominence 12 to 100 and sorting score 10.240937 to
85.341143: the supplied coffee-community meaning now counts the coffee
experience itself. Coffee with cream/egg yolk stays at prominence 100 and
sorting score 92.622641. Red-flag jokes retain represented zero in their body,
with only a small tag affiliation (2 to 1). Those semantic checks are accepted
by agent review; exact percentages and the strict complete order remain open.
The meaning includes morning greetings, increasing several mixed-post shares
while unrelated weather, travel, workout, household and food details remain
separate. The weather/greeting post moves above the rave after unchanged
relevance (59.313610 versus 56.411241); that pair is unsettled. These changes do
not prove every new value/order is better. No prior Coffee-node user judgment
is transferred to this different node or overwritten.

Eleven post-run native agent reviews record three semantic accepts and eight
uncertainties, preserving the four pre-run comments and all user labels.
Forty-five relevant tests pass, including actual local T5 integration. Exact
inputs/baselines/allocations, reused cosines, products, post maxima and complete
order verify; all 110 protected earlier source/result/review hashes remain
unchanged. The optional native viewer check is unavailable for `subject_contexts`
inputs; saved posts and answers are reviewed through native `show` and
`review --case`, with no UI extension. A concurrent unused graph-module change
is separately audited in native code-upgrade provenance before the first call;
this task makes no workflow/production code change or hierarchy repair.
[Model-runner results](../../sse_multivector/model-runner.md) retain the full
ordering, source grounding, hashes and verification limits.

Native usage is 8,184 input and 1,721 output tokens including 234 reasoning;
catalog reference $0.167890 is separate from incremental cash $0 and unmeasured
quota. 
All other nodes, source memberships, SP/MP data and earlier agreed checks are
untouched. The proposed SP-only meaning-generation check was not approved and
is withdrawn: coffeechain's saved contexts mostly name the hashtag without
explaining it. The user approved the general prompt trial below instead.
General description generation, calibrated prominence and production adoption
remain open; no broader work or recursion is authorized.

**General Nostr context approved October 1 (completed):** The user's "sure"
authorized one shared prominence-prompt change on twenty-six exact post/node
inputs in `grownostr` and `coffeechain`, covering twenty-two original posts.
Tested **PPv30-nostr-v1** changes only the interpretation paragraph: titles
come from Nostr posts, where hashtags can identify communities, and should be
interpreted as used on Nostr. Neither node name nor manual definition occurs
in the template. Native revision/preparation retains exact posts/titles,
evidence, schema, allocation instructions, Astra-low subscription settings and
original PPv30-node-v1 baselines. The two completed fixed-definition trials
remain separate references, not new samples or relabeled user decisions.

Eight pre-run agent observations preceded twenty-six fresh valid calls with
no retries, failures or reuse, within the fifty-two-attempt bound. Relevance
reuses all 738 cached SP subject-plus-context rows; all twenty-six values are
bit-identical to the original and fixed-definition comparisons. SSE final
learned layers, titles, formula and highest-entry post rule remain fixed, with
no worker, new vectors, SP/MP or definition-generation step.

The two main semantic improvements hold: GrowNostr outputs use Nostr growth/
community rather than food cultivation, and coffeechain's roasting experience
retains prominence 100 / sorting score 85.341143. GrowNostr stock and steak
food work receive represented zero, with prominence four and two; salsa work
is separate from considering a Nostr sale. The food-growing member receives
zero instead of the fixed-definition draw's uncertain profile-reference credit.
Coffee with cream/egg yolk stays at 100 and unrelated joke bodies remain
represented zero. Exact percentages and full strict orders are not approved.

The general prompt still treats coffeechain greetings inconsistently. The
household morning/closing wishes receive represented 12+11 and the gym greeting
25, but weather's GM Nostr/Sunday greeting receives zero out of 20 and the
another-coffee greeting zero out of 45. The fixed definition included them all.
Agent review rejects the two omissions as inconsistent inclusion, not exact
percentage mismatch. Another-coffee's sorting score falls from 90.001991 to 47.369469,
below the rave's 48.352492. Those consequences are not new user-labeled pairs.
The instruction is helpful on the main cases but is not adopted as a complete
replacement for explicit shared node meaning.

Twenty-six native post-run agent reviews record seven semantic accepts, two
rejects and seventeen uncertainties, preserving eight pre-run comments and all
prior user labels. Exact full inputs/baselines/allocations, reused cosines,
products, maxima and both complete orders verify, with all 123 earlier
protected hashes unchanged. Sixteen prominence values change versus original,
twenty versus fixed definitions; text changes are not quality grades.
Forty-five relevant existing tests pass with local T5 integration. The optional
subject-context prominence viewer remains unsupported, not reported passed;
native saved-case review is used without extending it. No code upgrade was
needed. [Model-runner results](../../sse_multivector/model-runner.md) record
full paired tables, exact greeting failures, hashes and limits.

Native usage is 19,382 input and 5,367 output tokens including 864 reasoning;
API catalog reference $0.462170 is separate from incremental cash $0 and
unmeasured quota. 
The task changes no production/workflow code, hierarchy, source membership,
other-node result or old SP/MP data. Earlier agreed checks remain untouched.
The subsequently approved title-input inspection is complete: current TPv38
calls receive repeated names/mask fragments, with full posts saved only as
review evidence. Those fragments do not establish enough information to supply
an explicit shared meaning. Frozen v38 remains unchanged; SP-only generation
remains withdrawn for insufficient explanatory context.

**General sorting investigation approved October 1 (in progress):** The user
authorizes architectural choices and independent agent assessment until
satisfactory or two hours pass, stopping at October 2, 02:09:48 UTC. The total
ceiling is 2,000 OpenAI subscription calls using 6.1 Sol at medium effort or
lower. Preserve earlier user judgments; no new user ordering labels are
required. This is authority to investigate and implement reusable support,
not a production deployment, push, paid fallback or resource rental.

An exact twenty-six-input Sol-medium control completed valid first attempts.
It reproduces coffeechain's inconsistent greeting inclusion and adds one
GrowNostr food-growing interpretation failure. One bounded, source-bound
meaning is now supplied to every post in a node through opt-in experimental
inputs. NodeDescription-v1 was tested and rejected for inventing GrowNostr's
purpose from tagged food posts. NodeDescription-v2 distinguishes the community
from subjects its members discuss; all 108 sorting-node descriptions completed
valid, retaining unresolved meanings explicitly. An independent twenty-node
scope audit found no hard changes and two uncertainties. All 108 descriptions
were then inspected, with additional existing title/mask mismatches recorded.
These are experimental descriptions, not adopted production meanings.

PPv31-node-description-v1 completed twenty-six fresh valid prominence calls.
It fixes coffeechain's inconsistent greetings while keeping food/community
separation, but GrowNostr still counts some greetings and omits others.
PPv32-community-meaning-v1 was tested and rejected for dropping coffee's
substantive focus while counting community interaction. Experimental PPv33-
community-meaning-v2 explicitly includes both; its two-node trial restores
focused coffee and consistent greetings. Exact percentages remain uncalibrated.

The separate 108-node Sol control completed 633 SP cases/380 post-node inputs
with 354 fresh calls and 279 verified reuses. Combined sorting preserves all
eleven clear user directions and the accepted Eggs, Music and Photography orders.
Coffee's complete order changes beyond allowed about-equal swaps. Of thirty-five
additional agent subject-transfer comparisons, thirty-four pass; the pizza
restaurant-plan comparison reverses. Prominence alone loses the accepted iced-
coffee comparison, so removing relevance is not established. Native cached
encoding is unchanged. The broad PPv31 description trial now completes all cases
and passes all thirty-five agent comparisons, but fails one protected Coffee
direction: its places clause makes cool-places coffee entirely about Coffee,
and fixed relevance then ranks it above cream/yolk coffee. Music and Photography
orders hold; Eggs' accepted complete order swaps two displayed positions.
NodeDescription-v3 tests a definition focused on the title's subject without
cataloguing sampled settings; all 108 descriptions completed and scope review
found no hard changes. These are regression checks, not new user labels or
unseen-corpus validation. All 108 descriptions were reviewed; uncertainties
mostly identify
existing title/mask mismatches. Source membership is preserved for investigation.

Reusable preparation, offline collection and sorting comparison validate exact
IDs, titles, description records and source hashes. The request preserves titles,
uses at most eight complete posts and bounds JSON to 12,000 characters. Skipped
whole posts and all original evidence are retained. Descriptions are at most
1,200 characters; default contracts, memberships and frozen title prompts stay
intact. Compatibility support reuses unchanged SSE vectors and starts with a
failing production-path test.

A new experimental `node_sorting` workflow gives the teacher the complete post
and one saved node meaning and asks for the sorting score directly. It tests
removing separate prominence, SSE relevance and highest-SP selection. Native
collection deduplicates identical post/node judgments, rejects conflicts and
preserves source provenance. NodeSorting-v1 is a draft superseded before calls;
NodeSorting-v2 adds a general community-tag clarification and has been tested. Scores
express relative focus/relevance, not calibrated percentages. No product adoption
is implied. Minimal production-path tests fail before implementation; 159
relevant regression/integration tests pass and legacy tests remain intact.

A separate direct trial uses fifteen saved Literature, Psychology/philosophy
and Bitcoin posts disjoint from the original 98 description-source posts. Their
three meanings use only original source evidence. Ten agent directions were
recorded before new scoring; the posts were previously studied, so this is a
check on transfer beyond the description sample, not a fresh unseen corpus.

The direct broad trial fails one clear user direction and ties two others,
reverses Photography's accepted order, and loses three of thirty-five agent
comparisons through one reversal and two ties. It is rejected as a general
replacement. Revised NodeDescription-v3 with PPv33 preserves all eleven clear
user directions and thirty-five agent comparisons after including every SP
entry of the selected 122 post/node inputs (202 entries). Partial SP selections
must not be compared as if they retain the complete highest-SP sorting score.
Photography, Coffee and Eggs complete orders still differ.

Experimental PPv34 distinguishes meanings in mixed lists/attributions without
splitting synonyms or prescribing ratios. It preserves the eleven and thirty-five
comparisons and restores Photography's order. The 46-answer independent repeat
also preserves complete Eggs and Music orders; the first run still swaps two
Eggs positions. Coffee's complete order remains unsettled, and repeated identical
inputs receive varying prominence. The default workflow reuses identical requests;
the stress test deliberately asks for independent answers per SP entry.

A separate PPv33 nonfood comparison preserves all ten agent directions with current
SP subject-plus-context relevance. Its older reference used context only; 102 rows
were encoded locally rather than asserting invalid cache reuse. Literature remains
uncertain. Experimental PPv35 keeps comparisons/criticism attached to the subject
they address while preserving separately meaningful other subjects. Its complete
202-case comparison passes all eleven clear user directions and thirty-five agent
directions, and preserves complete Eggs, Music and Photography orders. A separate
nonfood trial preserves all ten agent directions with unchanged current relevance.
Coffee's complete order still differs; its nineteen-answer stress test preserves
six clear directions but identical inputs vary. The complete run reused those
parallel Coffee answers, so this is not independent replication.

The final session uses 1,920 subscription provider attempts including one retry,
all gpt-6.1-sol / medium, below the 2,000-call ceiling. Inference finishes before
the October 2, 02:09:48 UTC stop. The agent remains unsatisfied: Coffee's complete
order, stable prominence, uncertain node meanings and new-corpus transfer are open.
Pause and report at the two-hour deadline. The strongest experimental candidate
retains prominence times SP subject-plus-context relevance with PPv35 and one fixed
node meaning. No candidate is adopted into the product; the formula, SSE learned
layers, titles, memberships and earlier judgments remain fixed.

Initial experiments keep SP subject-plus-context relevance, SSE learned layers
and the sorting formula fixed. One bounded request per node and one bounded
description per selected post/node input avoid an all-post/all-node matrix.
Production adoption, description quality and general transfer remain open.
[Model-runner investigation](../../sse_multivector/model-runner.md) records
the native experiments, capability tests, model control and context limits.

The [saved-score comparison](../../sse_multivector/model-runner.md) records
the original mask comparisons, SP-context results and node-title trial for
these ten checks, plus the four about-equal judgments and separate slight
preference for the weather post described below.
They are reference pairs, not a claim of general ranking quality.

The **node sort score** is the existing **sorting score** used to order posts
within each hierarchy node. The user authorized a
five-post SP-context experiment: assess prominence for each saved SP context,
encode the complete context and hierarchy node title separately with SSE,
calculate relevance as `(clip(cosine, -1, 1) + 1) / 2`, then calculate sorting
score as prominence × relevance. This trial replaces Inverse combined rather
than keeping its inverse contribution. **PPv30-context-v1** is tested, not
production-frozen. All three reference pairs pass in this draw, and prominence
alone also passes all three. Relevance alone still favors the stove over the
diary and century eggs. Formula adoption and general ordering quality remain
open; the trial is not a replacement production ranking rule.

The user subsequently authorized comparing complete Coffee and Eggs orders
using every saved SP context whose mask belongs directly to that node. For
this experiment, each post uses its highest context prominence in the
prominence-only order and its highest context sorting score in the other
order. The two maxima are chosen independently and can come from different
SP contexts. This is authorization to test the rule, not production adoption.
The completed comparison covers Coffee's 14 posts and Eggs' seven posts across
37 contexts. Both methods pass the three original agreed pairs. Relevance reverses
four additional pair orders: errands falls below roasting, another coffee and
iced coffee; the diary rises above the four-egg dinner. The user reviewed all
four changed pairs and approved the sorting-score orders for roasting versus
errands, iced coffee versus errands, and diary versus four-egg dinner. Another
coffee versus errands was judged about equal, with a tentative tiny preference
for another coffee. The user also judged roasting above the hashtag-heavy
second-coffee post; both methods reverse that expected order (prominence
46 < 60; sorting score 40.978201 < 55.578774). The saved sorting score matches
six of seven clear expected orders; prominence alone matches three of seven.
The about-equal judgment is excluded from that count. The [complete orders and verification](../../sse_multivector/model-runner.md)
record 32 new assessments, five exact-request reuses and 201 passing tests.

The user approved testing a revised prominence definition: the percentage of
the complete post's meaning that concerns the saved SP subject. This replaces
SP-context meaning coverage in that trial. The new experimental prompt is
**PPv30-subject-v1**. It receives only the saved SP subject and complete original
post; the exact saved SP context continues to supply relevance. The same 37
entries, seven clear expected orders, separate about-equal judgment, highest
per-post aggregation and sorting-score formula are retained. Existing SSE
vectors are reused exactly. This authorizes the experiment, not production
adoption or changes to hierarchy membership or SP outputs.
The completed trial has 37 valid cases from 33 new assessments and four
exact-request reuses, with no failures or retries. All 37 relevance values and
the raw vectors match the preceding experiment exactly. Both prominence alone
and the sorting score match all seven clear expected orders. Roasting now has
prominence 100 and sorting score 89.083045, above second coffee's 70 and
64.841903. The about-equal pair remains separate: another coffee has sorting
score 42.357665 versus errands' 41.622349; prominence alone puts errands higher
(60 versus 50). No numeric tolerance for that judgment is inferred.
**PPv30-subject-v1** is tested, not production-frozen. The complete orders,
allocation checks and 201 passing regression/integration tests are recorded in
the [experiment results](../../sse_multivector/model-runner.md). Broader ordering
quality and the value of relevance beyond these checks remain open.

The user subsequently reviewed More coffee in cool places (`37f44e1f`, A)
against roasting your own beans (`056e6466`, B), with image URLs omitted, and
answered "probably B". Record roasting above the short post as a tentative
preference, separately from the seven clear checks and the about-equal judgment.
Both have highest subject prominence 100, so prominence alone ties them. The
saved sorting score puts A first: 93.490294 versus B's 89.083045, using relevance
0.934903 versus 0.890830. This reverses the tentative preference. The seven clear
checks still pass; this additional judgment does not approve a formula change
or select a production ranking rule.
On September 30, the user clarified the reason: B only talks about coffee,
whereas A also talks about "cool places". A's saved Coffee assessment assigns all 100
points to enjoying coffee in cool places and counts all of them toward Coffee.
The tentative preference remains separate from the seven clear checks; no
revised prominence rule or exact percentages have been approved.

The user then authorized testing that distinction in prominence with relevance
unchanged. **PPv30-subject-v2** asks for meaning about each subject to be
distinguished even within one statement; it supplies no post-specific examples
or expected orders. The same 37 frozen inputs completed with 33 new assessments
and four exact-request reuses, without failures, retries or new SSE encoding.
All relevance values, vectors, the formula and independent highest-per-post
aggregation match the preceding experiment. Both prominence alone and the
sorting score still match the seven clear expected orders.
For SP subject Coffee, the short post now has prominence 75, leaving 25 points
for its places meaning; roasting has 96. However, the short post's broader SP
subject Continued experiences of coffee in appealing places retains prominence
100 and supplies its highest sorting score, 86.860927. Roasting's is 85.519723,
so the final order still reverses the separate tentative preference. The prompt
distinguishes the Coffee meaning, but taking the highest sorting score across
SP subjects still chooses the broader meaning. The about-equal pair remains
uncounted and has no agreed tolerance. **PPv30-subject-v2** is tested, not
production-frozen; the [saved results and 91 passing workflow/comparison tests](../../sse_multivector/model-runner.md)
do not approve exact percentages, a production rule or a change to aggregation.

The user then authorized testing that distinction in prominence with relevance
unchanged. **PPv30-subject-v2** asks for meaning about each subject to be
distinguished even within one statement; it supplies no post-specific examples
or expected orders. The same 37 frozen inputs completed with 33 new assessments
and four exact-request reuses, without failures, retries or new SSE encoding.
All relevance values, vectors, the formula and independent highest-per-post
aggregation match the preceding experiment. Both prominence alone and the
sorting score still match the seven clear expected orders.
For SP subject Coffee, the short post now has prominence 75, leaving 25 points
for its places meaning; roasting has 96. However, the short post's broader SP
subject Continued experiences of coffee in appealing places retains prominence
100 and supplies its highest sorting score, 86.860927. Roasting's is 85.519723,
so the final order still reverses the separate tentative preference. The prompt
distinguishes the Coffee meaning, but taking the highest sorting score across
SP subjects still chooses the broader meaning. The about-equal pair remains
uncounted and has no agreed tolerance. **PPv30-subject-v2** is tested, not
production-frozen; the [saved results and 91 passing workflow/comparison tests](../../sse_multivector/model-runner.md)
do not approve exact percentages, a production rule or a change to aggregation.

The user authorized the next trial: assess prominence using the hierarchy node
title for every post in that node, with relevance and the sorting-score formula
unchanged. **PPv30-node-v1** receives exactly the saved node title and complete
post. The shared adapter supports `prominence_basis: "node_title"`; SP subjects,
contexts and membership evidence remain saved for review and relevance. The same
37 entries completed with 21 new assessments and 16 exact-request reuses, giving
one prominence assessment per post/node. No baseline, SP output or SSE encoding
was regenerated. All 37 relevance values, raw vectors and receipt hashes match
the preceding trial exactly.
The short coffee/places post now has Coffee prominence 70 across all five SP
entries; roasting has 98. Its broader SP subjects cannot supply a different
prominence. Their final sorting scores are 65.443206 and 87.301384 respectively,
matching the separate tentative roasting preference. With the tenth reviewed
pair below, the sorting score matches all ten clear expected orders, while
prominence alone matches nine. The four about-equal
comparisons and the separate slight preference for the weather post remain
outside that count, with no agreed tolerance. The [complete orders and verification](../../sse_multivector/model-runner.md)
include two failing-first workflow/comparison checks and 202 passing regression
and integration tests. **PPv30-node-v1** is tested, not production-frozen; this
does not adopt a production ranking rule or approve exact percentages.

On September 30, the user reviewed the complete mixed diary (`eaa6a5e6`, A)
and coffee with raw cream and raw egg yolk (`f4c5aa5f`, B) in Eggs, with the
image URL omitted, and answered "A". This adds the eighth clear expected order.
PPv30-node-v1 already follows it: prominence 42 > 35 and sorting score
38.818971 > 32.538029. PPv30-subject-v2 reversed it (33.703212 < 43.724941).
The decision approves this post order, not exact prominence percentages,
the formula or production adoption. The tentative roasting preference and
about-equal judgments remain separate.

The user next reviewed coffee with raw cream and raw egg yolk (`f4c5aa5f`, A)
against More coffee in cool places (`37f44e1f`, B) inside Coffee, with complete
wording and the image URL omitted, and answered "A". This adds the ninth clear
expected order. PPv30-node-v1 already follows it: prominence 100 > 70 and
sorting score 75.582818 > 65.443206. PPv30-subject-v2 reversed it
(75.582818 < 86.860927). This approves the post order, not the assessed
percentages, formula or production adoption. No new model calls, encoding or
prompt changes were needed.

After reviewing the complete Sunday-weather post (`82d3d344`, A) and coffee,
movement and stretching post (`8a025f69`, B) inside Coffee, and receiving an
explanation of the calculation, the user said "A seems more related to coffee".
The user then clarified that the difference is "pretty subtle": A's "glad the
coffee is hot this AM" is about the same as B's "fetching coffee as a ritual
of motion", with A's `#coffeechain` "prob the tie breaker". Record a slight,
tentative preference for A separately from the ten clear orders; the main
coffee statements are about equal. This supersedes treating the pair as a
tenth clear order or clear failure.
PPv30-node-v1's sorting-score direction still reverses this slight preference:
both posts have prominence 35, while relevance is 0.823400 for A and 0.957202
for B, giving sorting scores 28.819013 < 33.502067. Prominence alone ties them.
The complete-post prominence input already includes A's hashtag, and its
35-point coffee allocation describes sharing with the coffee community.
Neither of A's saved SP contexts mentions the hashtag. No isolated hashtag
contribution or exact percentages were approved; no numerical tolerance for
the slight preference was agreed.
The preceding PPv30-subject-v2 trial put A above B: A had prominence 35
and B 25, giving 28.819013 > 23.930048 with the same relevance values. The
node-title trial raised B's prominence to 35; relevance was reused unchanged.
The clarification does not change the prominence definition, relevance input,
formula or production rule. No new inference or encoding was needed; the
calculation remains as tested.

The user then authorized testing relevance with the original coffee statements,
including A's `#coffeechain`, while keeping prominence and the sorting-score
formula fixed. The exact inputs are A's "Glad the coffee is hot this AM!",
a blank line and `#coffeechain`, and B's "Fetching coffee as a ritual of motion".
The shared comparison workflow verifies the selected text against each saved
complete post, preserves the original SP evidence and uses the existing
PPv30-node-v1 prominence 35 for both. No new prominence or SP assessment ran.
The local CPU SSE diagnostic encoded only the title, two statements and two
original-vector replays. Checkpoint, model artifacts, settings and worker code
match the prior SP-context calculation; runtime package versions differ,
with both replay checks agreeing within 3.1e-8 normalized component error.
A's relevance becomes 0.836787 and sorting score 29.287528; B's becomes
0.907297 and 31.755387. B still comes first. The gap shrinks from 4.683055
to 2.467859 but still reverses the user's separate slight preference for A.
This changes wording and hashtag inclusion together, so it does not isolate
the hashtag's effect or establish a general replacement relevance input.
The [saved inputs, runtime limits and results](../../sse_multivector/model-runner.md)
record a failing-first source-text CLI check and 211 passing regression and
integration tests. There were no provider calls, paid resources or baseline
prompt reruns. The full-node results and the original nine clear checks remain intact;
this two-post diagnostic is not production adoption or a prompt revision.

The user next authorized isolating the hashtag's effect on A's relevance input.
The shared workflow encoded `Glad the coffee is hot this AM!` without the blank
line and `#coffeechain`, retaining the original post, SP evidence, prominence 35
and formula. Compared with the preceding original-statement trial, the title,
B's statement, two original MP-mask replays, row positions, model settings,
worker code and runtime versions were unchanged. All four unchanged vectors
reproduced exactly, and both replay checks passed. A's relevance without the
hashtag is 0.786343 and sorting score 27.522017; with it they are 0.836787 and
29.287528. Including the hashtag therefore increases this sorting score by
1.765511. B remains at 31.755387 and above A in both versions. This confirms
an increase from including the hashtag in this exact relevance input, not a
general hashtag bonus or a complete-post prominence change. No new teacher
assessments, provider calls, paid resources, source-code changes or production
rule adoption occurred. The [experiment evidence](../../sse_multivector/model-runner.md)
records exact inputs, unchanged controls and the focused workflow checks.

The user then reviewed coffee with raw cream and a raw egg yolk (`f4c5aa5f`, A)
against iced coffee served in ice (`76e19c3e`, B) inside Coffee, with complete
wording and media URLs omitted, and answered "B". This adds the tenth clear
expected order: iced coffee above the raw-cream/egg-yolk coffee post.
The saved PPv30-node-v1 sorting score follows that order, 85.118002 > 75.582818;
prominence alone reverses it, 95 < 100. Those values use the original saved
SP-context relevance, 0.895979 and 0.755828 respectively, not the later two-post
original-statement diagnostics. Across all ten clear checks, the sorting score
now matches ten and prominence alone nine. This is the first clear reviewed
pair in this node-title trial where including relevance changes the direction
to the user's expected order. It does not establish a general advantage,
approve exact percentages or select a production formula. The about-equal
judgments and slight weather preference remain separate. No inference,
encoding, prompt change or saved-result modification was needed.

The user next reviewed Photography's three distinct complete posts, with URLs
omitted and no sorting scores shown, and answered "A, B, C": A, forgetting to
take photos while cooking (`bca8827b`); B, island lunch with photographer
credits (`d6628bf3`); C, the Tolstoy quotation with `#Photography` (`be8d07d4`).
Record one clear complete-order judgment, A > B > C, before inference. The
user authorized applying the same PPv30-node-v1 prominence × SP-context
relevance calculation to this node. The reusable Photography selector prepares
six saved SP entries from all five direct masks, with three distinct complete
post/node-title requests. The run is bounded to three new Astra-low
subscription attempts, with repeated requests reused, followed by local CPU
SSE encoding. No production formula, percentages, tie rule or multiple-entry
rule is approved by this judgment; the ten Coffee/Eggs clear checks and three
about-equal judgments retain their existing classifications.
The completed trial gives A, B and C prominence 12, 7 and 1; highest SP-context
relevance 0.760010, 0.780966 and 0.870545; and sorting scores 9.120122, 5.466762
and 0.870545. Both prominence and sorting score follow A > B > C. Relevance
alone gives C > B > A, so this case depends on prominence to put brief hashtag
association below the other mentions. Record a matching three-post order
separately from the ten Coffee/Eggs pair checks, not three independent new
samples. Three new assessments and three exact-request reuses completed
without failures; local CPU SSE encoded twelve rows and all five original-mask
replays passed. The shared workflow suites passed 107 tests. These posts each
mention Photography briefly, so the result does not cover posts primarily
about Photography. [Exact inputs and verification](../../sse_multivector/model-runner.md)
remain experiment evidence; production sorting is still undecided.

The user then reviewed Music's two distinct complete posts, with URLs omitted
and no sorting scores shown, and answered "A": Baby Got Back playing in a
coffee shop (`46ed60cb`) above the island-lunch post with `#Music` (`d6628bf3`).
This is one additional clear expected pair, separate from Photography's
three-post ordering judgment and the three about-equal Coffee judgments.
The authorized `ppv30-music-node-v1` experiment keeps PPv30-node-v1 and
prominence × SP-context relevance fixed. The production adapter prepares three
saved SP entries from all three direct Music masks, with two distinct original
post/title requests. Inference is bounded to two new Astra-low subscription
attempts, followed by local CPU SSE encoding and original-mask replay checks.
The expected order is review evidence, not an input to either calculation.
No exact percentages, production formula or multiple-entry rule is approved.

The completed Music trial gives A prominence 85 and highest SP-context
relevance 0.835578, yielding sorting score 71.024162; B has prominence 3,
relevance 0.939429 and sorting score 2.818288. Both prominence and sorting
score follow A > B; relevance alone favors B. With this pair, the same tested
method matches eleven of eleven clear Coffee/Eggs/Music pairs, while
prominence alone matches ten. Photography's matching three-post judgment
remains separate, as do the three about-equal Coffee judgments and tentative
preferences. Two new assessments and one exact-request reuse completed
without failures or retries. Local CPU SSE encoded seven rows, all three
original-mask replays matched exactly, and eleven focused workflow tests
passed. [Exact inputs and verification](../../sse_multivector/model-runner.md)
remain evidence for the candidate calculation, not production adoption.

The user authorized one fresh prominence assessment each for iced coffee
(`76e19c3e`) and coffee with raw cream and raw egg yolk (`f4c5aa5f`), retaining
both original relevance values and the prominence × relevance formula.
`ppv30-node-orders-repeat-iced-raw-v1` inherits only their two original Coffee
cases through the shared workflow's `--from`, `--only` and intentional
`--repeat` controls. Prompt PPv30-node-v1, complete posts, title, schema and
Astra-low subscription settings are identical. The run allows two new
attempts and no regenerated embeddings. The existing expected order remains
iced coffee above raw-egg-yolk coffee; this is another trial of that same
judgment, not a twelfth independent expected pair. Original comparison
results and user judgments remain intact; production sorting remains open.

Both fresh assessments completed without reuse, failures or retries and
returned the original prominence values: iced coffee 95, raw-egg-yolk coffee
100. With exactly the same saved relevance, 0.895979 and 0.755828, sorting
scores repeat exactly: 85.118002 > 75.582818. Prominence alone again reverses
the expected order. Thus the earlier result repeats in one additional trial;
it does not establish a general benefit or approve the percentages/formula.
No SSE worker ran. Original vectors, receipts, five replay results and
source artifacts are unchanged. The shared subset-reuse change passed its
failing-first CLI test and 141 relevant regression/integration tests; 22
focused checks also passed after an unrelated concurrent input-adapter addition.
The first collector refused a changed shared-code hash; a new read-only
preparation used unchanged inputs and collected successfully, without repeating
model calls or editing frozen plans. [Exact results and verification](../../sse_multivector/model-runner.md)
are saved with this repeated pair, separate from the eleven original clear
Coffee/Eggs/Music checks and the Photography ordering judgment.

04 and 27 are paused as nice-to-have work. The saved candidate matches the
eleven clear
Coffee/Eggs/Music pair preferences, Photography's three-post order and the
accepted fourteen-post Coffee and seven-post Eggs orders; one Coffee comparison
repeated successfully.
Either order is acceptable for the four about-equal Coffee pairs, without
requiring identical scores. These selected reviews do not establish general
ordering quality. 04 defines and validates the node sort score; 27 implements
ordering using that definition. The formula, inputs, any treatment of multiple
masks and production adoption remain open, as does broader-hierarchy validation.
Finishing 27 still needs 04.
28 waits for the validated small-corpus workflow and scale findings. Readiness does not authorize execution. Membership
methods, final node-equivalence/cycle policy, ranking rules and scale
implementation choices remain open.

The 100-note build exposed a relationship-quality blocker at minimal scope,
without membership expansion or a claim to exercise scalable construction.
Task 25 is complete for HR02 and no longer gates 02 or 03. Task 02 remains open
for the current merging and conflict decisions and the user's browsing review.
The 200-note correctness and 300-note scalable-construction work do not wait
for node sorting. Completing the combined 500-note validation (03) also does
not require sorting; 24 remains required only if HDBSCAN is used.
Relevant-content coverage is required either way. The optional sorting effort
retains 04 → 27, with only a helpful link from 27 to 03. The stages' internal
processing order must respect their inputs, but this does not impose a serial
development schedule.

Pilot **06** also includes a small hierarchy built from pilot-model outputs before
model selection. Use that check to detect downstream consequences of extraction
errors; distinguish those from failures in the shared hierarchy pipeline. **11**
still verifies the final distilled model before model-track publication, not
before the required release snapshot. The new pilot
check belongs within 06 rather than a separate node or a dependency on finishing
the final fine-tune.

Early scale assessment 20 includes graph-processing costs and membership-recovery
costs where recovery is used, not only model calls. It can use available evidence
from 24 and the growing hierarchy builds; it does not wait for the finished
implementation in 28.

**Protocol and client status reconciled October 2:** 13 remains in progress.
The [protocol draft](../recommendation-engine/design/hierarchy-serving-protocol-decisions.md)
now covers opening a hierarchy, node events, note lists and indexes. Proposals
remain under review; service implementation and client integration await
agreement. The Notedeck browser UI is approved and committed; task 15 is waiting
for service integration. This does not establish end-to-end readiness. Tracks
and completion links are unchanged. Protocol design and UI work remain with
their assigned agents; this update makes no technical choice.

Service testing needs both the protocol and a saved hierarchy snapshot. The
100-note hierarchy can supply the initial snapshot; service development need
not wait for the final corpus build. Public launch requires the final snapshot.

Pilot-model measurements can inform scaling work before the release model is
trained. They are useful early input, not a requirement to start investigating
scaling and not a substitute for release-model measurements.

### Publication preparation

Publication preparation belongs to the existing tasks, not a new workstream:

| Task | Required result for publication |
| --- | --- |
| **06 · Choose model through larger fine-tuning pilot** | Confirm permission to release fine-tuned weights before selecting the base model and committing to the larger training run. Teacher provider permissions remain in 17. |
| **08 · Distill and package the model** | Prepare trained weights, necessary supporting files, usage instructions and evaluation results. Verify that the intended release files load and generate masks and any agreed additional outputs. |
| **12 · Build launch hierarchy snapshot** | Build the final teacher-labeled, fully automated snapshot, targeting 2–5k notes without a hard minimum, and obtain the user's browsing acceptance. Prepare runnable hierarchy-generation code and instructions, architecture documentation matching the actual build, the agreed continual-update path, and the scalability roadmap. |
| **16 · Launch public hierarchy** | Publish the hierarchy events to a paid relay or as an online ZIP, alongside generation code and documentation, tested serving instructions, the scalability roadmap, and the Notedeck fork branch. Choose distribution after reviewing hierarchy quality. The model track publishes whenever it passes its gate; a hosted demo is optional. |

Preparation can accompany development; final verification requires the actual
release artifacts. Checking an internal training checkpoint alone does not
establish that the intended public files and instructions work together.
The specific relay or ZIP-hosting location, event-file layout and publication
implementation remain open. Notedeck integration is required with either route.
Publishing the training dataset is not an additional release requirement.
No dates, dependency arrows, model choices or spending approvals change.

### Scale measurements and final validation

**September 29 clarification:** whether HDBSCAN will be used remains open.
Task 21 is required only if the chosen workflow uses HDBSCAN. While that choice
is open, its links to 20 and 28 are helpful inputs, not unconditional completion
prerequisites; make those links required if HDBSCAN is selected. Time and cost
checks for the chosen workflow remain required. This neither selects an
alternative nor authorizes implementation, measurements or spending.

The [scalability record](scalability.md) distinguishes findings, user decisions
and proposed next steps from the separately authorized read-only investigation.
It does not approve implementation, benchmarks, spending or diagram changes.

- **21 · Assess HDBSCAN at launch scale:** determine whether HDBSCAN can form our
  mask-vector groups at the intended corpus size within budget and deadline,
  preserving our grouping rules, and identify any work required. This assessment
  has had a separately authorized read-only code/evidence investigation;
  launch-scale feasibility remains unproven. Implementation and performance
  runs have not been authorized by that investigation.
  It does not presume that HDBSCAN or its implementation must be replaced. Its
  findings are needed for 20 and 28 only if HDBSCAN is used; they do not block
  completion of those tasks for a workflow without HDBSCAN.
- **22 · Measure SSE and hierarchy-construction costs:** measure time, memory
  and cost for the stages used in the chosen workflow, using saved masks, subjects
  and nodes. Include subject matching, merging, relationship checks and graph
  processing where used. Separate node-title generation is conditional, not an
  assumed stage: measure it only if the chosen workflow includes it, accounting
  for title input growth with group size. LG01 retains subject names from SP;
  it does not run the old HDBSCAN-group naming pass. This does not select LG01
  as the production workflow or rule out a later naming stage. Preserve TRUE's
  historical rate as evidence, but measure the selected relationship method
  before completing build-cost estimates.
  This is ready independently of 21's HDBSCAN assessment. No measurement
  procedure, hardware choice or spending is approved here.
- **20 · Assess full hierarchy-build resources:** keep the required-release
  estimate separate from the optional model-track estimate. For the teacher-built
  release, use 2–5k notes as a target rather than a minimum. Combine available
  teacher generation measurements from 17 with stage measurements from 22 and
  observed subject/mask/node/pair counts from 03.
  Include HDBSCAN requirements from 21 only if HDBSCAN is used. Estimate release
  time, memory and cost to inform corpus selection in 09 while preserving quality.
  Retain pilot/distilled-model generation measurements from 06 separately for
  the model track; they do not estimate teacher generation or block completing
  the release estimate. Shared construction measurements can inform both where
  applicable; check workload differences rather than assuming identical counts.
  Include graph-processing costs and membership-recovery costs where recovery
  is used; available measurements from 24 are an additional dashed input.
  It waits for 22, plus 21 only if HDBSCAN is used. The dashed inputs from 17,
  06 and 03 can inform the corresponding estimate before those tasks finish.
  Per-pair relationship cost alone does not establish total hierarchy-build cost.
- **09 · Choose notes for launch hierarchy:** use the early measurements, agreed
  corpus scope and useful-coverage requirements to choose the intended corpus and
  freeze its IDs. Target 2–5k notes without a hard minimum; choose the largest
  genuinely useful hierarchy that can pass review by October 18. Corpus size is
  not fixed before feasibility is investigated; the selected size still needs
  final validation.
- **10 · Check distilled-model build time and cost:** establish whether the distilled model
  can generate the agreed outputs for the selected launch corpus, and the
  remaining pipeline can construct and order its full hierarchy, within the
  remaining budget and available time. This is a model-track check, not an October 18
  release gate. It needs the trained model, corpus selection,
  resource measurements and the runnable build from 28; early estimates alone
  do not establish feasibility.
- **11 · Test hierarchy with the distilled model:** build a sample hierarchy from
  that model's outputs and the chosen note-sorting method; check browsing and
  whether the complete pipeline works before publishing the optional model. It does not gate the
  teacher-built release snapshot.

10 and 11 are distinct model-track checks: whether a build using the distilled
model fits the resources, and whether its outputs produce a useful hierarchy.
Neither blocks 12 or is required to finish before the other. They may share
construction measurements with the teacher-built release, but their generation
measurements and acceptance decisions remain separate.

**18 · Prepare training code for the fine-tuning pilot** is complete for the
preliminary experiment's setup.
Local VM rehearsals cover all three candidate families, real adapter updates,
interruption/resume, save/reload and SSH deployment; the rebuilt image is
published and verified private. Preliminary candidate execution and quality
review are tracked in 29; larger-pilot model selection is tracked in 06.
Setup completion does not verify the newer larger-pilot worker or configuration,
select a model, prove all full-size candidates work or complete the model track.
Further larger-run preparation remains within 06.

**October 6 VM verification decision:** the existing local launcher defaults to
automatic reuse of successful stages with matching source, test, dependency and
input hashes and intact saved evidence. An agent may choose `--full` to rerun
every check while retaining Docker build caching. Changed or uncertain
dependencies force checks; there is no forced stale-evidence mode. Successful
retrieved stages survive export failures, and identical complete results can be
verified without starting the VM. Implementation and initial verification used
a separate worktree and VM directory. **Cutover approved October 6:** integrate
into `main` and transfer matching verified evidence into the existing VM
directory. The unchanged parent invocation verifies in 2.22 seconds; all
53 host regressions pass. Future launches need an image and frozen packages
built from the updated Dockerfile; existing publication evidence is preserved.
This changes local rehearsal, with the pilot recipe and hardware decisions
unchanged. Full-size CUDA fit remains the GPU preparation gate. Operational
details are in the technical plan's **Local VM workflow** section.

Final training-example formatting and output-quality evaluation remain within
**06 · Choose model through larger fine-tuning pilot**. Its completion needs the
agreed output format and quality criteria, reviewed pilot data and training
setup (05 + 18). Additional model outputs needed for sorting remain undecided.
The September 25 informal subject-and-mask experiment is separate task 29;
its preparation and Qwen execution have proceeded using available data while
06's requirements remain outstanding. The $25 approval above bounds that
experiment, not the larger pilot; frozen settings and ledger admission still
govern execution.

These are planning dependencies, not approval for measurements, model calls or
paid runs in this discussion. Measurement procedures, sample sizes, the cosine
cutoff, measured rates and counts, and the final corpus size remain open.

## Approved scheduling changes

1. After the good 100-note hierarchy, use 200 notes to test correctness across
   more topics, 300 to test correctness and scalable construction, and 500 to
   validate them together and profile the build. The October 5 decision defers
   node sorting as nice-to-have work; it does not gate any rung. The combined
   500-note validation needs 24 only if HDBSCAN is used. Relevant-content
   coverage remains required either way.
2. Start scale measurements during Week 2. Measure the complete chosen workflow,
   rather than relying only on distilled-model training or generation speed.
   Node 22 measures SSE and hierarchy-construction stages using saved inputs;
   separate node-title generation is measured only if used. Node 21's HDBSCAN
   assessment is required only if HDBSCAN is used. Node 20 combines those
   findings with teacher generation measurements and growing-build counts to
   inform release corpus selection in 09. It retains pilot-model measurements
   separately for the optional model track.
   Node 10 then checks time and cost for the distilled model's agreed outputs
   and hierarchy construction across the intended launch corpus. Deferred
   sorting is not required for either resource check.
3. Bring protocol work and basic service/Notedeck integration forward, using a
   small saved hierarchy snapshot rather than waiting for the final corpus.
   Do not leave the first complete integration to Week 5; preserve time then
   for verification and fixes. Show this work as an explicit parallel track on
   the task graph, alongside hierarchy/model development rather than mainly
   under Weeks 4–5. Service development can begin after the protocol; testing
   with the saved hierarchy needs the 100-note snapshot as well.
   Notedeck can start from the protocol and finish integration with the service.
   Launch still needs the final snapshot. The track adds no week assignments or
   dates; the earlier integration date remains open.
4. Include a separate teacher-comparison pilot before generating the full
   training data, alongside the fine-tuning pilot. Muse is the leading teacher
   candidate to evaluate, not an approved production choice. Week 2 is the proposed window for both
   pilots; their exact schedules remain open.
5. Target **September 27, 2026** for training-data readiness: suitable masks
   available for training, with training/evaluation separation. The October 5
   deferral removes node-sorting data from the required scope.
   The volume, quality checks and handling of unsuitable annotations remain
   open; the target does not prescribe a correction workflow.

The October 18 deadline and release requirements are unchanged. Full
training-data generation starts only after successful completion of the
500-note hierarchy validation and teacher selection; the September 27 target
does not override this gate. Starting the final fine-tune requires both the
selected base model and sufficient reviewed training data. September 27 is an
agreed readiness target, not a demonstrated completion forecast. Training
volume and the time required to produce suitable data remain unresolved. These
timing decisions do not authorize work to begin or establish that the full
schedule fits.

### Proposed release calendar — September 28, 2026 (proposal, not approved)

Three weeks remain to the non-negotiable October 18 date. This re-cut of the
efficient five-week sequence matches the release shape above; it is a proposal
that authorizes nothing. Model-track and scale work (05–08, 10, 11, 20, 21,
22) proceeds opportunistically in parallel and is not scheduled here.
Launch-scale implementation (28) is required to complete snapshot 12; its
schedule remains open. This calendar supersedes the earlier weekly-targets
proposal. The retired draw.io
page is recoverable from Git, not a second current planning view.

**Week 1 · September 28 – October 4: settle the quality foundation.** Review
the completed mask-based parent-child diagnostic and settle the automated
relationship method the user is pleased with (02) — the release's top risk,
gating every build. Node sorting (04 and 27) is now deferred as nice-to-have
work. Land membership recovery (24) if HDBSCAN
is used; 24 gates 03 only for HDBSCAN.
Define the Nostr hierarchy protocol (13), now in progress and independent.
Begin corpus selection toward
the 2–5k target, not a required band (09).

**Week 2 · October 5 – 11: validate the process; select the teachers.** Run
the ladder with full user review at each rung: 200 (correctness across more
topics), 300 (correctness + scalable construction), 500 (combined +
profile), then the ~1–2k review rung. The four reviews are the week's
bottleneck; if review time slips, the proposal is to drop rungs from the
bottom (200 first, then 300) and never from the top. Freeze the corpus IDs
(09) at the start of the week, complete the teacher A/B hierarchy comparison
and selection (17), and have the selected teachers label the frozen corpus.
In parallel, verify the service code locally (14) against the 100-note
snapshot and publish the Notedeck branch (15) on the user's fork.

**Week 3 · October 12 – 18: build, verify, publish.** Build the release
snapshot from the teacher labels (12) — hours to a day at this scale, subject
to budget admission. Verify 14 and 15 against the final snapshot and fix what
that exposes; this is the reserved buffer. On October 18 publish the package
(16): snapshot, code and architecture, tested serving instructions,
scalability roadmap, and the Notedeck fork branch. The model track and hosted
demo publish only if they have already earned it.

**Known risks.** If the relationship-quality review (02) absorbs week 1, it
eats ladder time. Week 2 assumes the user's attention for consecutive-day
reviews. Teacher labeling throughput is unmeasured at 2–5k notes. Task
ownership remains unassigned; deferred node sorting is not a release blocker.

## Compute, hosting and budget

| Work | Agreed location |
| --- | --- |
| Model fine-tuning, including the planned pilot fine-tunes | Vast.ai |
| GPU work for generating the hierarchy snapshot | Vast.ai |
| Local processing and orchestration | The user's own servers; detailed allocation remains open |
| Serving the completed snapshot through the Nostr protocol | Wherever the user runs it; the release ships tested instructions. Operating rented hosting is the optional hosted demo |

Do not assume that training or snapshot GPU work will run on the user's own
GPUs. A hosted endpoint, if run at all, serves completed data; it does not
build the hierarchy or require live model inference for browsing.

Hosting is optional — the cherry-on-top demo — and not a release requirement.
If the user elects to run it, six months remains a **provisional planning
target**, not a finalized commitment; from an October 18 launch that would
extend through April 18, 2027. Operating duration, capacity and total cost remain
open.

**Hierarchy publication options clarified October 8:** the final hierarchy
events will go to a paid relay or into a ZIP posted online, with the choice
informed by hierarchy quality. Notedeck integration remains required with either
route; operating our own public service remains optional. No route is selected yet.

Cellar (`wss://cellar.nostr.wine`) remains the provisional candidate for the
paid-relay route, as discussed October 5. That discussion preferred its metered
1-sat-per-event/year model for the expected larger-than-average upload; the
relay need not retain original posts, only hierarchy events and references.
[Paid-relay findings](../recommendation-engine/research/paid-hierarchy-relays.md)
record policies, live limits, read checks and alternatives. Protocol kinds
remain experimental; funded custom-kind writes and upload pacing still need
verification if the paid-relay route is chosen. Neither route approves spending
or publication execution.

The $1,000 lifetime paid-resource cap still applies, including prior spending,
Vast.ai training and snapshot GPU costs, hosting, storage, transfers and reruns.
Account for the intended hosting period before allocating the remaining budget.

Keep hosting costs and reserves out of `budget-ledger.json`. Hosting estimates
belong in release planning, separately from that ledger. This accounting decision
does not change the overall cap or approve the proposed $200 hosting reserve.
No allocation or new spending is approved by this document.

## Still open

- Final corpus size and subset, targeting 2–5k notes without a hard minimum;
  whether existing length and language filtering policies meet the
  release scope.
- Concrete release-quality judgments, informed by the expanding hierarchy builds.
- Paid-relay or online event-ZIP publication, informed by hierarchy quality;
  the specific destination and publication procedure.
- Teacher selection, the base model for the distilled model, both pilots' details and final training volume.
- Teacher-output quality checks and treatment of unsuitable outputs.
- Scale-measurement procedures, measured rates and counts, and the cosine cutoff.
- Measured costs and budget allocations; demo-hosting capacity and duration if
  the hosted demo runs.
- Detailed task ownership and a feasible calendar within the proposed five-week sequence.

The task graph reflects the approved dependency and status decisions. Other
calendar targets remain provisional until their dependencies, durations and
owners are settled.
