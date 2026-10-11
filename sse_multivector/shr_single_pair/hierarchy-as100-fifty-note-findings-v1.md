# Fresh ASv6.100 fifty-note hierarchy: observed failures

This record covers only the fresh ASv6.100 rebuild under
`target/hierarchy-as100-b96-c48-fifty-note-v1`, using unchanged
[Hierarchy-bootstrap-v96](Hierarchy-bootstrap-v96.md) and
[Hierarchy-compare-v48](Hierarchy-compare-v48.md), GPT-6.1 Sol medium, and native
selective construction with guarded16 comparisons. It does not reuse findings
from the deprecated AS<6.100 hierarchy as evidence for this rebuild.

The saved build is in
`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-bootstrap-v88-three-note-v1`,
at source commit `7f0a54b9e2fc9dcd47e62b7da0ac901056087904`. The constructor,
receipts and ignored target artifacts remain in that research checkout.
The writeup, evaluated prompt files and two menu recipes were integrated first;
the canonical constructor, continuation, selection, audit and shaping workflow
are now also integrated into main. The run's original source and receipt
bindings remain in the research checkout.

The prompt SHA-256 bindings are:

- Bootstrap-v96: `599e811307cfd3feac290ec91b0c763f1900cc244fccc4756d8255027a050845`.
- Compare-v48: `b225da8653af04dfbe41fc8ff9e4f9d8bf780df527e27ee3e2d088c0e7eb23af`.

The rebuild and bounded menu assessment completed. The candidate did not meet
the then-approved six-choice requirement; no prompt changes or forced
relationships were made to remove that limitation. Choice counts are now a
best-effort goal rather than a hard completion requirement; the saved assessment
and counts below remain unchanged.

## What failed

The strongest confirmed semantic problem is **inconsistent interpretation of
unchanged meanings**. Compare-v48 copies the supplied meaning correctly, yet
sometimes applies a different boundary when the other node changes. Three
families produce incompatible graph relationships; a fourth produces directly
incompatible reasons within one batch. The guards blocked those placements,
but accepted relationships can still assume restrictions they have not checked.

Bootstrap-v96 also produced three meanings whose defining process or identity
remained unresolved. All were stopped by receipt-bound agent review before
comparison. This demonstrates useful review coverage, not perfect Bootstrap
performance or human-approved correctness of the remaining definitions.

The visible hierarchy's main measured failure is **too many choices**: seven
roots, thirteen Food children and seven Food-preparation children, against six.
All fifty notes remain reachable individually, and every displayed edge narrows
the note set. Those successes do not settle semantic correctness, missing useful
views or the option-count failure.

| Final construction outcome | Count | Interpretation |
|---|---:|---|
| Added canonical nodes | 99 | Accepted construction decisions, not human gold. |
| Equivalences | 8 | Reused existing canonical meanings. |
| Holds for producer ambiguity | 3 | Unresolved meaning stopped before comparison. |
| Holds for graph contradictions | 11 | Proposed relationships disagreed with required ancestry or settled answers. |
| Hold for incompatible comparison reasons | 1 | Explicit review caught an inconsistency the graph guards had not caught. |
| Holds for uncertain relationships | 2 | Insufficiently settled evidence; uncertainty alone is not a model error. |

The seventeen holds are construction outcomes, **not seventeen independent
prompt failures**. Several repeat the same mechanism or share a post, meaning
and prior graph. They cannot be used as an accuracy or reliability estimate.
The fourteen recovered provider failures in the accounting section are a
separate service measure; they are not these fourteen comparison-related holds.

## How to read the evidence

A contradiction proves that the saved relationships cannot coexist under fixed
meanings and whole-child containment. It does **not** establish which individual
label is correct. Accepted edges and held entries are not human gold. Repeated
holds share meanings and graph history; they are not independent reliability
measurements. Copying a meaning exactly does not prove that its interpretation
stayed fixed.

All experiment references below are relative to the build directory above.
The receipt table identifies exact native result records. Inspect a witness with
the shared launcher, for example:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-bootstrap-v88-three-note-v1
../experiment-runner/bin/experiment-runner --project-root . show \
  target/hierarchy-as100-b96-c48-fifty-note-v1/roots-clean-v3/step-024/experiment \
  --case C005 --json
```

## Bootstrap failures stopped before placement

**Cooking leaves its defining action unresolved.** `root-meanings`, R02,
returns: "Cooking is the activity of preparing food for eating through culinary
techniques, including but not limited to heating and combining ingredients."
Its ambiguity diagnostics decide whether the activity is general or specific
and whether success or favorable results define membership. They never settle
whether heating is required or nonheated assembly independently qualifies.
Listing heating as an example does not resolve that boundary. The defect is
leaving a material choice implicit, not choosing one particular side of it.
The meaning was held at original-entry step 001.

**A particular cooking event repeats the activity name instead of defining its
process.** `coverage-meanings-v1`, U01, begins: "The author's act of preparing
food by cooking on the evening referred to as 'tonight'..." The post supports
the event, timing, reported small success and favorable but unspecified result.
"By cooking" still requires the next model to interpret the activity afresh.
Bootstrap needed to distinguish defining the activity from inventing how this
particular event occurred; the post does not describe a specific heating step.
The producer review held the entry at step 050. It shares R02's post and process
ambiguity, so these are related witnesses rather than independent trials.

**An unknown commercial affiliation is carried into a meaning.**
`isolation-meanings-v1`, I01, defines the author's amusement at a coffee-shop
rave as "an unusual coffee-chain experience that day." Both diagnostic arrays
are empty. The post says "Weird #coffeechain today" and "Rave at a coffee shop
lol"; the evidence interpretation nevertheless says "associated with a coffee
chain." It does not distinguish a hashtag/community reference from membership
in a commercial coffee chain. Unknown affiliation cannot be established by the
generated local subject. The entry was held at step 116.

All three responses supplied non-null meanings. Bootstrap-v96 instructs the
model to define the activity's process, identify material scope differences and
return null when a coherent meaning cannot be established. Agent uncertainty
holds caught the remaining issues before freezing them into canonical meanings.
They required alternative original entries for access, but did not prevent
eventual individual access to all fifty notes. These agent assessments remain
open to user review; they are not replacement human gold.

## Incompatible comparison interpretations

**Eating versus drinking changes within one batch.** The incoming Food meaning
at archived `roots/step-020/experiment` requires substances and preparations
"intended to be eaten as nourishment." C001 Food rejects containment because
its meaning also includes drinks; C019 Dinner likewise rejects the accompanying
drinks. C006 Coffee is nevertheless accepted as a consumable beverage within
that same incoming meaning. These reasons apply incompatible boundaries.
Native receipt-bound agent uncertainty reviews preserved the witnesses. The
clean replay held the entire incoming entry; graph implication checks alone had
not caught this reason-level inconsistency. The archived run is not the active
construction.

**Food changes from an information topic to edible material.** At
`roots-clean-v3/step-024`, the incoming meaning is "edible material intended for
human consumption." C005 Food preparation is contained, with the reason
explicitly covering its equipment descendants. C014 Cooking appliances is
rejected because edible material excludes devices and their design. Both cannot
hold given the existing C005→C014 relationship. Step 025 repeats this mechanism:
C008 Cookware is contained through its food-preparation purpose, expressly
including stockpots, but omitted-descendant verification rejects C015 Stockpots
as non-edible vessels. The native whole-child guard held both entries. Later
recurrences are the same failure family, not separate mechanisms.

**A purpose restriction disappears through an intermediate Food node.**
`verified-prefix-v3/step-005`, C001, rejects Coffee because its meaning lacks
Food's required nourishment purpose. At `roots-clean-v3/step-033`, C001 contains
a new Food meaning requiring human consumption but not nourishment; that new
meaning contains C006 Coffee. The proposed chain would imply the previously
rejected relationship. The settled-relationship guard held it; step 036 repeats
the chain. Human consumption and a stated nourishment purpose were not treated
consistently.

**The food-kind/activity boundary changes across a complete chain.**
`verified-prefix-v3/step-019`, C010, rejects Food dishes containing Bread
preparation because prepared meal foods are not the making activity. At
`coverage-children-v1/step-059`, Bread contains Bread preparation because making
bread directly concerns the food kind, while C020 Food dishes contains Bread.
That chain implies the earlier rejected relationship, so the settled-relation
guard held Bread. Step 067 admits a different Bread meaning and uses the
completed-product distinction against Bread preparation. Those two Bread
definitions differ; they are a diagnostic contrast, not an exact-input repeat.

## Accepted edges and unresolved scope qualifications

**Optional roles are tested unevenly.** At `coverage-children-v1/step-060`,
C005 accepts Butter because its meaning includes a cooking-ingredient role.
The whole meaning is "used as a food, spread or cooking ingredient"; the reason
does not address the other admitted roles. Step 063 rejects Tomatoes because
their meaning permits eating on their own or use as meal ingredients, rather
than only preparation. This is an accepted-edge qualification without a formal
graph contradiction or a replacement gold label. Guards did not flag Butter.

**Meal use is assumed in positives and required in a later guard.** C020 Food
dishes requires prepared foods "served or eaten as a meal or part of a meal."
Coverage step 067 accepts general Bread, and root step 029 accepts Salsa, by
asserting meal use that their fixed meanings do not require. Later
`menu-growth-v1/step-076`, C020, returns uncertain for Meals containing Food
dishes because those same Bread and Salsa descendants lack a meal-use
restriction. This is a conflict within the existing branch, not proof that the
Meals producer is defective.

Isolation step 097 accepts no-bake pie preparation beneath C020 without checking
that restriction. Step 098 accepts bagel-making and explicitly calls it food
"eaten as part of a meal," although neither the fixed local meaning nor its
post establishes meal use. C068 Bread also accepts bagel-making as information
directly concerning bread, carrying the unresolved C020 ancestor consequence.
These accepted batches repeat the earlier meal-role qualification; no native
formal contradiction was reported for them. In contrast, isolation steps
110–112 explicitly define lamb, broccoli and baby potatoes as components of the
author's dinner, so their meal role is present in the fixed meanings.

`last-access-children-v2/step-117`, C020, repeats the qualification for Preparing
sourdough bread: its positive reason asserts food "eaten as part of a meal,"
while the supplied meaning and post describe making sourdough bread without a
meal role. The omitted Food ancestor separately passed native verification.
That successful guard confirms the saved Food judgment; it does not resolve
the unestablished restriction on the already queried Food dishes relationship.

**One uncertainty reason misreads a conjunction.** At coverage step 066, C020,
Processed food is held partly because Salsa supposedly includes ingredients
"merely intended" for making it. The supplied Salsa meaning says "intended and
prepared." Breakfast's possible unaltered-food scope remains a separate concern;
correcting the Salsa reading alone would not establish a valid insertion.

**Final Eating placement retains an unchecked purpose qualification.**
`regrouping-roots-v1/step-122`, C001, accepts Eating beneath Food by citing Food's
consumption scope. Eating requires taking food into the mouth and swallowing;
neither its fixed meaning nor its membership resolution requires nourishment.
The positive reason does not address Food's human/nourishment limits. This
recurs in the earlier purpose-boundary family; no formal guard contradiction
was reported for this placement.

The same batch contains Lunches because their meaning explicitly establishes
intended eating, but rejects Dinners because planned meals, composition and
proposed additions need not involve the eating activity. These are different
fixed scopes, so this contrast alone does not prove inconsistent labels.
Cheese doodles and lunch-box Food were omitted candidates, leaving their
relationships to Eating unknown rather than rejected.

**A retained Coffee relationship skips the same nourishment condition.**
`selection-004/step-081`, C001, accepts the author's coffee beneath Food by
saying Food encompasses "beverages for human consumption." The local fixed
meaning identifies the author's own coffee and their complaint about
half-and-half; it does not establish Food's required nourishment purpose.
`menu-v2` retains Food→C082 while the general Coffee node remains a separate
root. A narrower child can fit two broader topics that contain neither other
topic in full, so those placements are not themselves a formal contradiction.
The unresolved issue is whether the positive checks the entire stated purpose
restriction. This is an accepted-edge qualification, not a negative gold label.

## A stable distinction: fatigue and sleepiness

The fixed C003 Mental states meaning covers cognitive or emotional conditions.
Fatigue-access step 090 defines the author's continuing pronounced tiredness.
C048 Fatigue contains it; C003 rejects it because experienced tiredness is not
necessarily a cognitive or emotional condition.

Step 091 defines the author's subjective drowsiness or inclination to sleep.
C048 contains the tiredness-with-sleepiness meaning; C003 contains it as a state
of alertness. Both entries were added with unchanged meanings and no implication
verification phase. This is a defensible distinction under the supplied scopes,
not a demonstrated comparison inconsistency. Food was an eligible omitted
candidate in both batches: its relationship remains **unknown**, not rejected.
This gives original note N034 a witnessed Mental states route through sleepiness
without merging or redefining its Fatigue node.

## What the guards establish

Whole-child, ancestor and settled-relationship checks prevented insertion of
the represented contradictions above. Omitted-implication verification actually
ran for root step 025 and found the stockpot conflict. Successful verification
also occurred for the particular cooking stove at root-access step 082 and for
Cast-iron cookware at isolation step 104, each checking the omitted Food ancestor.

The guards do not certify unsupported positives or detect every incompatible
reason. They also do not discover unrelated omitted relationships. For example,
Mental states was omitted for isolation step 108's explicit breakfast-energy
hope, leaving that possible route untested. Scope issues caught by producer
review—such as the unresolved Cooking action boundary or the named #coffeechain
interpretation—are distinct from Compare contradictions. The evidence supports
investigating both meaning construction and interpretation; it does not justify
attributing every hold to one prompt or weakening the guards.

## Attribution and the next useful review

The observed mechanisms require different responses. Bootstrap's three held
outputs leave a process or identity unsettled; their ambiguity diagnostics
do not cover the remaining difference. Compare's contradiction witnesses apply
different interpretations despite fixed strings and already stated boundaries.
The optional-role and meal/nourishment positives test a compatible part while
leaving other required restrictions unaddressed. An earlier accepted edge may
be the bad link in a blocked chain; the newest held entry is not automatically
the wrong judgment.

These observations identify failure mechanisms; they do not isolate which
wording caused them. Retrieval and selective entry construction also leave
relationships unknown: only 124 of 1,510 original
entries were processed, and unqueried pairs are not negative judgments. Missing
groups could reflect semantic restrictions, contradictory earlier decisions or
work not nominated; this run does not isolate their relative contributions.

The most useful next review is the **accepted relationships still visible**:
Food dishes→Bread/Salsa, Food→the author's coffee, Food→Eating, and the
Cuisine→bagel-making shortcut. Check the exact fixed meanings and decide which
whole information scope is justified before treating them as regressions. This
would distinguish a genuinely wrong positive from an overly restrictive earlier
meaning. Once those judgments are settled, use frozen complete chains and
contrasting counterparts to test interpretation stability, alongside the three
producer witnesses. These are proposed follow-ups; this writeup changes no
prompt, semantic verdict, graph edge or experiment.

## Completed construction and menu

The final raw checkpoint is `regrouping-roots-v1`. Its 124 processed original
entries yielded 99 canonical nodes, eight equivalences and 17 holds. Three
producer holds preserve unresolved meanings: Cooking's heat boundary, a
circular cooking-event definition, and #coffeechain's community-versus-chain
interpretation. The other fourteen holds preserve comparison uncertainty or
placement contradictions; they are not fourteen independent prompt defects.
The raw graph reaches all fifty notes and permits individual access to each.

The [preferred menu source](hierarchy-as100-fifty-note-shape-v2.json) shapes only
saved nodes and witnessed ancestry into `menu-v2`. Its native audit records:

| Measure | Result |
|---|---:|
| Reachable notes / individually isolatable notes | 50 / 50 |
| Canonical nodes / edges | 70 / 74 |
| Strictly narrowing edges / equal-note-set edges | 74 / 0 |
| Roots | 7 |
| Food children / Food-preparation children | 13 / 7 |
| Mean / maximum shortest topic selections | 2.68 / 4 |

Four notes need one topic selection, thirteen need two, twenty-eight need
three and five need four. This counts shortest paths to a singleton note set;
it excludes opening the note, scanning options and reading. Food retains its
full 35-note view, Mental states eight notes and Coffee six.

**K=6 fails in three places:** the root menu, Food and Food preparation.
`menu-plan-v1.json` gives a saved-graph lower bound of ten first-step Food
choices: N012, N021, N024, N032, N045, N001, N003, N002, N005 and N010 all
belong to Food, but none of its 66 proper raw descendants contains two of them.
Preserving the full Food view therefore requires at least ten choices with
currently witnessed nodes. The bound does not apply to unconstructed topics
or prove semantic infeasibility. New valid groupings could improve it.

The [cleaner alternative](hierarchy-as100-fifty-note-shape-v1.json), `menu-v1`,
has 70 nodes and 72 strictly narrowing edges. It omits two witnessed shortcuts,
Dinners→Lamb and Cuisine→bagel-making, and needs 136 rather than 134 total
shortest selections. It has the same three K violations. The Cuisine shortcut
uses a saved positive culinary-tradition interpretation; it is not independent
semantic validation. No candidate is claimed to satisfy the full stopping rule
or minimize browsing decisions globally. At the user's later request, the
preferred candidate was exported through the native path to `review-ui-v1`.
The existing protected viewer passed its check. Its 71 displayed records are
70 canonical nodes plus one display-only root container; the export preserves
all fifty original notes and does not change the hierarchy.

Shortest-path counts leave out the work of reading the menu. The two shortcuts
save only two topic selections over all fifty individual-access tasks; no
improvement in actual user effort was measured. Several headings are long:
C109's breakfast-energy hope is 137 characters, C098's pie-making activity 95,
and C083's particular rocket stove 73, before canonical-ID and note suffixes.
Two retained Dinner nodes, C019 and C056, share a heading but have different
fixed scopes. These are visible scanning and interpretability concerns, not
proof that the nodes should be merged or that their meanings are wrong.

Menu omissions retain the raw evidence and are not negative labels or merges.
Relative to the raw graph, retained views lose the following memberships:

- Food preparation: N023, after omitting Butter's qualified optional-role edge.
- Cuisine: N083's pie-preparation view.
- Food dishes: N007, N008, N015, N017, N025, N040, N046 and N083; omitted
  activity routes carry the meal-role qualifications described below.
- Bread: N015 and N046 activity routes.
- Japanese food: N020, so its retained view can isolate N011.

Cookware, Cooking appliances, Breakfast, Dinners, Amusement, Brain fog and
mental clarity, and Additional coffee retain their saved memberships.
Rocket stoves, Milk, Tea and Fatigue are omitted as separate roots; other
retained routes preserve their notes.
The broader physical-fatigue browsing view is lost, while sleepiness supplies
a witnessed Mental-states route for N034. Removing Raves could reduce roots
to six only with loss of the shared Amusement view in the reviewed shaping
alternatives; it would not resolve Food overcrowding. These are candidate
qualifications, not new user approvals or evidence that omitted containment
is false. Complete paths and omissions are in `menu-plan-v1.json`.

## Native accounting and provenance

`usage-source-v2.json` inventories 355 executed parent experiments, including
archived construction, replay, producer prefetch and final placement phases.
Nested cache-warmup experiments are charged through their parents and are not
also listed as independent inventory entries. Unrun preparation previews are
excluded. Native `usage-v2.json` records:

- 2,236 fresh provider attempts, including warmups, retries and failures.
- 538 exact answer reuses; all source generations are inside this fresh build.
- Fourteen failed attempts, all recovered; 2,611 valid case outputs and zero
  unresolved failed, malformed, invalid-receipt or unrun inventory cases.
- **Known API-equivalent subtotal: $7.296504.** All fourteen failed attempts
  lack usage and cost estimates, so the complete cost is unknown.
- Known token subtotals: 1,596,083 uncached input, 3,860,480 cached input and
  371,829 output. The 67,954 reasoning tokens are included in output.

This is catalog-equivalent accounting, not a provider invoice. Reused source
generations are included once; exact reuse is not represented as free original
generation. Other agents share the attempt counter, so its global delta is not
this task's usage. There is no matched savings comparison against the deprecated
AS<6.100 build or claim that a structural audit certifies semantic accuracy.

The source collection contains fifty valid ASv6.100 receipts and 1,510 original
entries. The local SSE probe encodes 693 exact headings from that collection;
it reads no deprecated subject vectors. Raw post bytes remain bound to the
original corpus. All meaning generation uses Bootstrap-v96 and all relationship
judgments use Compare-v48 with GPT-6.1 Sol medium. Receipt-bound producer reviews
are agent assessments, not human gold. Native model outputs and archived graph
snapshots remain unchanged.

Final independent read-only provenance review checked all fifty ASv6.100 notes,
361 parent plans (including previews and superseded trials), 149 matching
cache-warmup prefixes and all 538 reuse references. Each reuse remains inside
this build with matching request, source and output hashes. All 107 applied
local meanings have current receipt-bound agent accept reviews; the 70 retained
menu nodes preserve their raw meanings and all 74 menu edges have witnessed
ancestry. No deprecated-data contamination was found. This review made no
calls or edits and does not certify semantics, K=6 or optimality. Its inventory
counts are not additional provider attempts or the accounting inventory above.

Final checks passed: 105 constructor, selection, ranking and probe regressions,
plus nine subject-vector preparation tests. After synchronizing current main,
47 relevant regression checks passed and all 48 final-audit source bindings
still matched. The original 34 receipt witnesses were independently checked
through the native inspection path. This writeup additionally verifies the
three producer records and one retained Coffee comparison listed below.
All 34 maintained AS100 JSON sources parsed, all 252 original-entry pointers
were checked against the native collection, and all
Bootstrap prefetch specifications preserve identical prompt/schema/runner
settings. The writeup and its prompt/menu dependencies are integrated into main.
The research worktree remains because native artifacts and frozen source paths
still reference it. Current canonical runtime components are integrated into
main separately from the branch's inherited research history. Both menu recipes
retain their original relative
artifact bindings. Reproduction requires the original recipes and saved graph
in the research checkout; copying a recipe into main does not copy its graph.

Saved artifacts below are relative to the build directory:

- `subjects/{subjects,provenance}.json`: original ASv6.100 collection and receipts.
- `regrouping-roots-v1/state.json`: complete raw construction.
- `menu-v2/{state,audit}.json`: preferred candidate and structural violations.
- `menu-v1/{state,audit}.json`: cleaner shortcut alternative.
- `menu-plan-v1.json`: paths, lower bound and scope qualifications.
- `usage-source-v2.json` and `usage-v2.json`: native inventory and accounting.

## Exact native witnesses

`receipt` is the `record_sha256` in the native result receipt. Paths identify
the experiment; case IDs identify the selected comparison within it.

| Experiment / case | Receipt |
|---|---|
| `root-meanings`, R02 | `5812ceffd0f912fdbe031a6a14bc21aabdfacb5bf90392fab738fbcbef20ec78` |
| `coverage-meanings-v1`, U01 | `c7b894c6fb972d91bf8d12b0bbccd1c55a9d7800a487a8168916e155f6a83a64` |
| `isolation-meanings-v1`, I01 | `77e97bcb170bb73afc36fe6ff3c8eac9aba0301c5c7190dae136a7a81f9944ca` |
| `roots/step-020/experiment`, C001 | `195f22f10897b6dbd76773c8171b0c9716ae38701ac96ec86444d9e869713f11` |
| `roots/step-020/experiment`, C019 | `e45915c92fff22e70389d68c83f60a87d0da66bfc01e06c6f49358aa4df0f23a` |
| `roots/step-020/experiment`, C006 | `0b9a7695c6c45ce64688655738c3c8226bce483fcd452da8965201572fa2854f` |
| `roots-clean-v3/step-024/experiment`, C005 | `22edcd1642837277fdad217d12bc7c5ac49bf7d9f026f2ea4e76d088625fa882` |
| `roots-clean-v3/step-024/experiment`, C014 | `4f919a6bbd7cd82405c38b907b0afe9caa9d7e37741426dd6fa24572ef37625d` |
| `roots-clean-v3/step-025/experiment`, C008 | `a01f709a9f251aa2015e64958f2669b5486e3c0881d9230a58e64163363d2483` |
| `roots-clean-v3/step-025/verification/experiment`, C015 | `c05b3b792e955b02b8715c5480404f56f25a25f2e17d532033d2a0027ed8bf57` |
| `verified-prefix-v3/step-005/experiment`, C001 | `f817047fdd1f70b3ba8425f76cc4ea99e236ebc9a754df4529ff98a33eb78f74` |
| `roots-clean-v3/step-033/experiment`, C001 | `e2f6b134024680afce7dab3f41385889d1b359da08f7280c9741a6bce4cdedcc` |
| `roots-clean-v3/step-033/experiment`, C006 | `96f563a3989aeb712a99345c77dee964829d89c959645a5ffaa0eb60d907b62e` |
| `verified-prefix-v3/step-019/experiment`, C010 | `9aa38cc77cf6775ec400e2cf0d4150b391f210d75f4d2a7ec6b1e99e14502ca0` |
| `coverage-children-v1/step-059/experiment`, C010 | `a9388ace70f918be9be5959dede7093e4691c9bfc16127e1a8526c4f9350985d` |
| `coverage-children-v1/step-059/experiment`, C020 | `447dde5968a113e31c041d639da6b0774bb6f8ed4d1052184724c147cb1164fd` |
| `coverage-children-v1/step-060/experiment`, C005 | `50a56d8d84cec14d42c57da329628b86efc43b536560e326c3090fd86fb3eab1` |
| `coverage-children-v1/step-063/experiment`, C005 | `db19c210371769772f339892250270603584c45ac55671c0221425486cef8003` |
| `coverage-children-v1/step-066/experiment`, C020 | `14c2857cb9900fbc26a8e6b4794462580337cecba599c1eef2b2981682a67137` |
| `coverage-children-v1/step-067/experiment`, C020 | `1a9764fb0a088ba478f2da1423996dd62e038281b8a432f00336c72a7cc0bf69` |
| `roots-clean-v3/step-029/experiment`, C020 | `25f53a67b90435348f668e00ad77201b97130430efd6dfaf4037125593e007a0` |
| `menu-growth-v1/step-076/experiment`, C020 | `477be05b9eee5ee3875a20fd113485bf6052a717357af681c5833f5b9cf5112d` |
| `isolation-children-v1/step-097/experiment`, C020 | `5dd311335fe645d1b4d0e2fe3b5742ad571bb4e508514cdd3569f70dafac7050` |
| `isolation-children-v1/step-098/experiment`, C020 | `beb3c5aeda534018ffca51e402979e7f149094f570b4c8221d3a098d4c785e2f` |
| `isolation-children-v1/step-098/experiment`, C068 | `b57038ba415710918d45731df8a833ec33354c232cdb334fda4e951d33258dc7` |
| `fatigue-access-children-v1/step-090/experiment`, C003 | `e422d577e974119e41410aaab8cbbbe45e310ae720f94481cd482bb28cb42f34` |
| `fatigue-access-children-v1/step-090/experiment`, C048 | `62a067a9c88af2ff3fc733eef636e9a14392d2c1a242f72b00307cd2e05c7dbd` |
| `fatigue-access-children-v1/step-091/experiment`, C003 | `ba505fa4d116e6724269f77938999160678a5d5c1416c6bc83a7e9f85dbc5cb8` |
| `fatigue-access-children-v1/step-091/experiment`, C048 | `7fb3175ea11e6400dd62c2336a087fe807bd922e3425ed9b7d1c7c2669b6e4cc` |
| `root-access-children-v1/step-082/verification/experiment`, C001 | `285153668bdb78f415dd765d885b9b97a1f64e03ed2ce66ba9808bcc5267264a` |
| `isolation-children-v1/step-104/verification/experiment`, C001 | `0ec5da2cf2d1fb591075c3dd6e5e0febe20c25feda0a85b7c0ef1caa729dd687` |
| `last-access-children-v2/step-117/experiment`, C020 | `adff743641722e9ed3dcdeca43c97325ec43369ccd6b7a05dec495039a1889bd` |
| `last-access-children-v2/step-117/verification/experiment`, C001 | `26f0924e1fff0d2bdc563fac5fd5bfd47dfb8f14ab35bc402111bcfb0659d501` |
| `regrouping-roots-v1/step-122/meaning/experiment`, bootstrap | `530adef0fb5b48dd794469a434266c47082186854fe629f583ca95e5c0e4c31a` |
| `regrouping-roots-v1/step-122/experiment`, C001 | `81819a0acd980e4518692788399818a5e38de608c87a1aaaef73fe3ade85d923` |
| `regrouping-roots-v1/step-122/experiment`, C017 | `b6d90d0fef692422ab5052020eb324304b40eacaaf5f70611a12d3de6bc4e42c` |
| `regrouping-roots-v1/step-122/experiment`, C059 | `5d24ae55fa4412185fdaaea53608a7b01b663c70510ea76996519db0860cce9a` |
| `selection-004/step-081/experiment`, C001 | `176f5f09873e12240f1dfc1594a29071832eb65f45637017507f4ef87eeb7a61` |
