# October 18 release decisions

Updated October 3, 2026. This is the written record of the planning discussion.
Agreed requirements, tentative choices and existing-data facts are distinguished
below. The overall plan is not approved. Approval of an individual requirement
or task-view edit does not approve the whole plan. Approved scheduling changes
are recorded below; other weekly targets and exact dates remain proposals.

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

**Parallel hierarchy-construction candidates confirmed October 3:** frontier-based
and vector-space approaches are both being tested within the existing hierarchy
investigation. Record their progress separately; neither is selected or accepted.
These are construction candidates, not new release tracks or additional tasks.

The [frontier-based investigation](../../../oracle-mvp-scalable-hierarchy-v12/sse_multivector/scalable-hierarchy-v1/README.md#sh5-200--actual-browsing-menu-construction-sprint)
completed a 200-note construction pass. Its initial combined answers contained
cycles; subsequent joint review produced a cycle-free candidate. That resolves
the structural issue for this candidate, not browsing quality or user acceptance.

The [vector-space investigation](../../../oracle-mvp-vector-hierarchy-v1/sse_multivector/vector-hierarchy-ten-hour-goal.md#result-and-review)
generated a 100-note hierarchy and completed a larger-model follow-up. The latter
recovered more valid relationships but also introduced more incorrect ones on
the previously inspected evaluation data. The workstream's recorded assessment
remains unsatisfactory; these measurements do not establish general accuracy.

[Subject-generation corrections](../../sse_multivector/subject-prompt-goal-v1/autonomous-sp-v1/README.md)
remain shared work: missing relationships and incorrect parent links are still
unresolved. Fixing source subjects does not establish that either construction
approach is correct. The useful 100-note hierarchy acceptance gate remains open;
tracks, dependencies, generation holds and production choices are unchanged.

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
saved outputs from 100 food/drink and 100 music notes: food has current subjects,
masks and vectors, while music has older-prompt outputs. This is experimental
construction, not an accepted validation run or release-corpus selection.
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

**Current task 02 status (October 3):** user browsing acceptance remains open.
Frontier-based and vector-space construction are both under investigation, with
separate results recorded above. Subject-generation errors remain unresolved.
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

**Scoring scope clarified September 30:** **04 · Define node sort score**
defines and validates one sorting score per note within a hierarchy node,
including its inputs and output format. **27 · Order notes within each node**
implements and validates ordering using that definition. Prominence may be a
component, but is not the task's required end state. The sorting mechanism is
still being developed; whether teachers or the distilled model need prominence
or other additional outputs is undecided. Existing prominence experiments and
frozen informal-pilot settings are unchanged; no production method is adopted.
Both tasks remain in progress. 04 is in launch scope and actively worked on,
superseding the earlier pause notes; it need not wait for the 100-note hierarchy
or title correction. Statuses and completion dependencies are unchanged.
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

- A genuinely useful, fully automated hierarchy snapshot over a 2,000–5,000-note
  corpus for discovering Nostr content, built without manual repair and judged by
  the user's browsing review.
- The full hierarchy-generation architecture and code.
- Tested service code and instructions for serving the snapshot over the custom
  Nostr protocol locally. Operating public infrastructure is not required.
- Notedeck browsing integration, delivered as a branch published on the user's
  fork and verified against a locally served snapshot.
- A roadmap to scalability: the fine-tuning path for replacing the expensive
  teacher calls at larger corpus sizes.

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
hierarchy over 2–5k notes demonstrates a correct process at small scale, and
the roadmap to scalability names fine-tuning models for the expensive steps as
the credible next step toward larger corpora. The user's browsing review
remains the acceptance bar. Teacher selection (17) stays on the release path
because teachers label the release corpus. Node sort score definition (04) is
in launch scope and active, superseding the earlier pause notes. Task 27 orders
notes using that definition. The mechanism and any additional teacher outputs
it needs are undecided; prominence is an experimental option, not a requirement.

The model-track quality gate requires acceptable masks and any agreed additional
outputs on unseen notes (08), plus a hierarchy that passes the user's browsing
review (11); “training ran” does not pass. The
September 27 training-data readiness target belongs to the model track and no
longer constrains the release. The validation ladder is kept and extended —
200 / 300 / 500 as approved, then a ~1–2k-note review rung, then the 2–5k
release build — because each rung gives diagnostic reference points when a
larger build misbehaves, and the release build must not be an uninstrumented
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

**Release corpus (PoC, decided September 27, 2026):** the release snapshot
covers 2,000–5,000 notes. The proof of concept demonstrates a correct
automated process at small corpus size — an actually good hierarchy is the
deliverable, not note count — and the roadmap to scalability covers larger
corpora. The exact subset remains open within that band and is frozen by task 09.

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
correctness and note ordering using the node sort score. The 300-note / 3-topic
build checks correctness while testing scalable construction choices; candidate-pair
filtering must preserve useful parent–child links, not just reduce relationship
checks.
The 500-note / 5-topic build checks the combined pipeline and profiles build
time and memory to find bottlenecks. All three increase subject coverage; none
is merely a test of handling more notes. The ladder extends past 500: a
~1–2k-note rung with full user review precedes the 2–5k release build (see the
release-shape revision above), so the release build is never an uninstrumented
jump in scale.

**Task ownership clarified September 29:** task 03 covers the 200 / 300 / 500
validation runs and the ~1–2k-note user-review rung. Task 12 alone owns the
final teacher-labeled, fully automated 2–5k build and its user browsing review.
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
validation and 200 final test notes and spending remain open. The GPU choice
is recorded below.
This pilot supplies subject evidence for model selection; it cannot establish
mask quality or downstream mask/SSE hierarchy quality. The completed combined
preliminary experiment and the eventual release task retain their own scope.

**October 2 GPU choice confirmed by the user:** use one **96GB RTX PRO 6000**
for separate preparation and the larger pilot. Keep the complete student model
on that GPU; run the three students sequentially. Prior NVLink alternatives are
research evidence, not the selected execution configuration. The subjects-only
scope, one continuing pass, approved training recipe and dynamic evaluation
batching remain unchanged. Numeric batching budgets, generation limits, the
specific card edition/power setting and rental offer, maximum charge and launch
remain open. This hardware choice does not authorize a paid commitment.

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
checked mechanically. The scoring scale, rubric, reviewer model, reliability
checks, and checkpoint/model selection rule remain design choices. The user deferred
review-prompt and grading details while the overall pilot pipeline is designed.
The walkthrough also keeps remaining data choices, remaining output format details,
remaining training settings, continuation rules, and new spending open. It authorizes no
new code changes, model calls, or rental.

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
Block membership, seed value, remaining model settings and validation/test
counts remain open. Loss was subsequently approved below. This corrects the
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
reviews. Comparable research does not establish the benefit of enabling thinking
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

The preliminary preparation cost was $1.56. This attempt left required Gemma work incomplete; the repaired run below completed it. No automatic timeout or
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
Preliminary preparation costs were $1.639 for this run and $1.620 for the earlier failed preparation: $3.259 combined. 

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
local import. Preliminary charges were $0.338.
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

**Conditional batched GPU reference (October 3):** the completed prep measured
all three subject-only setups on a 96GB/600 W RTX PRO 6000. Combining its
ASv6.48 batch shapes and incremental-token timings with saved historical answer
lengths gives about **5.6 hours training** and **22–24.5 hours generation** for
three baselines, fifteen validation checkpoints and only the winner's final
comparison. Assuming the proposed 100 validation / 200 final test notes,
1–2 hours extra lifecycle/startup/retrieval allowance, 25% headroom and $1
transfer fees gives **36–40 hours / $51–58** at the prep's historical $1.4153/hour;
an illustrative $1.60/hour gives $58–65. Brief generation plus a single long-cache
decode step is a projection, not measured full-output throughput. No full-pilot
spending is authorized. Preparation's preliminary total was $3.26.

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
pilot labels. Actual pilot notes/ASv6.100 labels still need their own checks.

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
The review rubric,
final-test collection arrangement, context/memory settings and the rental remain open.

**Pilot label generation partial October 5:** the initial WebSocket run at 32 concurrency saved 39 valid answers and 99 failed handshakes, with zero frames/bytes for those failures; failed handshakes reported HTTP 403. Its 138 attempts and
all receipts remain saved. The 1,162 untouched notes completed over SSE transport at 24
concurrency, without failed attempts or retries. Native cached reuse preserves
the earlier 39 answers with zero new calls. Native collection verified **1,201
labels: 919 train / 95 validation / 187 test**, with no text, author or split
mismatches. All labels retain the same full ASv6.100 prompt, teacher model,
reasoning effort and schema. Semantic review has not been performed.
**99 labels remain missing (81 train / 5 validation / 13 test).**
Repository AGENTS.md excludes unknown transport failures from automatic retry;
completion requires an explicit user exception. No rental or paid API was used.

**Approved fine-tuning candidates (September 24, 2026):** Qwen3.8-27B,
Gemma 4 31B instruction-tuned, and Gemma 4 26B-A4B instruction-tuned. The third
candidate replaces T5Gemma 9B–9B PrefixLM instruction-tuned. Compare its subjects,
hierarchy and total training-and-generation cost with the
dense candidates; lower active parameter count does not establish a cost
advantage. The larger pilot's remaining training settings, remaining output
format details, sorting-related output requirements and spending amounts remain open. The
informal subject/mask settings and $25 approval above apply only to the current
short experiment.

The [teacher research](../../sse_multivector/TOKEN-USAGE-ESTIMATE-1M-NOTES.md#lower-cost-annotation-models)
already identifies Muse. A later [12-note diagnostic](../../sse_multivector/frontier-model-comparison-v1/asv6.23-diagnostic-v2/results.md)
found it promising on subjects with ASv6.23, but with some context omissions.
That diagnostic tested neither masks nor prominence, and did not establish
equivalence to Astra. Its subject-only cost is not a complete labeling estimate.

Selecting the teachers and successfully completing the 500-note / 5-topic
hierarchy validation are both prerequisites for starting full training-data
generation (07). A finished but unsuccessful run does not clear this gate.
For the larger pilot, the same teachers must write both the pilot training data
(05) and the full training data (07), as the user directed on September 21, 2026.
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
  requirements, plus any additional outputs the chosen sorting method needs.
  Those additional outputs are undecided. Subject-only evidence does not
  establish mask quality or the quality of additional outputs.
- Whether hierarchies built from each candidate's own outputs on the same notes,
  with downstream construction and note sorting held fixed, offer useful
  browsing paths.
  Compare the hierarchies before selecting teachers; distinguish differences
  caused by teacher outputs from failures shared by the construction pipeline.
  Label-only parity does not settle the selection.
- Whether the selected teachers can supply the intended training data
  within the available time and budget.
- Whether provider data-use and output-use terms permit the intended training
  and open-weight release.

Completing 17 needs the validated subject/mask prompts from 01, completed prompt
stress-testing in 30, and the scoring definition from 04 to establish whether
additional teacher outputs are needed and what to evaluate. It does not
presuppose a prominence prompt. These are completion prerequisites; comparison
work may continue before stress-testing is complete. Final selection needs
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
directed node hierarchy. Prominence supports note ordering. The relationship
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
| **27 · Order notes within each node** | Implement and validate ordering using the node sort score defined in 04, including multiple masks from the same note where used. Recursive sorting and parent-child score transfer are out of scope. | Needs score definition 04; required to finish 03. |
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
audit below freezes the experimental choice for the next browsing build.

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

04 and 27 remain in progress. The saved candidate matches the eleven clear
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
Preliminary 200-note construction
can follow 02 before the node sort score is settled, but its ordering check needs
04 and 27. The 300-note
scalable-construction work can proceed without waiting for that ordering
check. Completing the combined 500-note validation (03) requires
27, plus 24 only if HDBSCAN is used. Relevant-content coverage is required
either way. The scoring dependency remains 04 → 27 → 03. The stages' internal
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
| **12 · Build launch hierarchy snapshot** | Build the final teacher-labeled, fully automated 2–5k snapshot and obtain the user's browsing acceptance. Prepare runnable hierarchy-generation code and instructions, architecture documentation matching the actual build, the agreed continual-update path, and the scalability roadmap. |
| **16 · Launch public hierarchy** | Publish the release package: the snapshot, code and documentation, tested serving instructions, the scalability roadmap, and the Notedeck fork branch. The model track publishes the open-weight model whenever it passes its gate; a hosted demo is optional. |

Preparation can accompany development; final verification requires the actual
release artifacts. Checking an internal training checkpoint alone does not
establish that the intended public files and instructions work together.
File formats, publishing locations and implementation methods remain open.
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
  2–5k release, combine available teacher generation measurements from 17 with
  stage measurements from 22 and observed subject/mask/node/pair counts from 03.
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
  freeze its IDs. Corpus size is not fixed before feasibility is investigated;
  the selected size still needs final validation.
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

1. After the good 100-note hierarchy, use 200 notes to test correctness and
   within-node note ordering, 300 to test correctness and scalable construction,
   and 500 to validate them together and profile the build. The 200-note
   construction can start before the node sort score is settled, but its ordering
   check cannot finish without 04 and 27. The 300-note work need not wait for that
   check. The combined 500-note validation still needs 27, plus 24 only if
   HDBSCAN is used. Relevant-content coverage remains required either way.
2. Start scale measurements during Week 2. Measure the complete chosen workflow,
   rather than relying only on distilled-model training or generation speed.
   Node 22 measures SSE and hierarchy-construction stages using saved inputs;
   separate node-title generation is measured only if used. Node 21's HDBSCAN
   assessment is required only if HDBSCAN is used. Node 20 combines those
   findings with teacher generation measurements and growing-build counts to
   inform release corpus selection in 09. It retains pilot-model measurements
   separately for the optional model track.
   Node 10 then checks time and cost for the distilled model's agreed outputs,
   hierarchy construction and the chosen note-sorting method across the intended
   launch corpus.
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
5. Target **September 27, 2026** for training-data readiness: suitable masks and
   prominence data available for training, with training/evaluation separation.
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
gating every build. Define and validate the node sort score (04)
and implement node-note ordering (27). Land membership recovery (24) if HDBSCAN
is used; 24 gates 03 only for HDBSCAN.
Define the Nostr hierarchy protocol (13), now in progress and independent.
Begin corpus selection inside
the decided 2–5k band (09).

**Week 2 · October 5 – 11: validate the process; select the teachers.** Run
the ladder with full user review at each rung: 200 (correctness + within-node
note ordering), 300 (correctness + scalable construction), 500 (combined +
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
reviews. Teacher labeling throughput and the cost of the chosen note-sorting
method are unmeasured at 2–5k notes. Task ownership remains unassigned.

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
extend through April 18, 2027. The hosting provider, capacity and cost remain
open.

The $1,000 lifetime paid-resource cap still applies, including prior spending,
Vast.ai training and snapshot GPU costs, hosting, storage, transfers and reruns.
Account for the intended hosting period before allocating the remaining budget.

Keep hosting costs and reserves out of `budget-ledger.json`. Hosting estimates
belong in release planning, separately from that ledger. This accounting decision
does not change the overall cap or approve the proposed $200 hosting reserve.
No allocation or new spending is approved by this document.

## Still open

- Final corpus subset within the decided 2–5k release band and its processed
  count; whether existing length and language filtering policies meet the
  release scope.
- Concrete release-quality judgments, informed by the expanding hierarchy builds.
- Teacher selection, the base model for the distilled model, both pilots' details and final training volume.
- Teacher-output quality checks and treatment of unsuitable outputs.
- Scale-measurement procedures, measured rates and counts, and the cosine cutoff.
- Measured costs and budget allocations; demo-hosting capacity and duration if
  the hosted demo runs.
- Detailed task ownership and a feasible calendar within the proposed five-week sequence.

The task graph reflects the approved dependency and status decisions. Other
calendar targets remain provisional until their dependencies, durations and
owners are settled.
