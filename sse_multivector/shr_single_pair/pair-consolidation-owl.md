# Pair-consolidation-owl: experimental prompt line

`pair-consolidation-owl-v12` is the current experimental version. It ports the
normal V7 specificity objective into the OWL task wrappers: retain shared
identities and defining conditions, choose the most specific coherent covered
topic, and allow the same scope as a supplied node. Common writing rules, the
Bootstrap companion, reasoning guide, example and output format remain exact.

The matched nine-pair screen corrects four clear V11 specificity losses: water
in Coffee, the day-starting role in Breakfast, BTC identity and Dezeen identity.
Tomatoes was already retained by V11 and remains retained by V12. Five independent
V12 repeats preserve those targeted conditions, but the Coffee repeat exposes
a separate roasting condition represented only in English. Beets/MrBeast also
loses the stated content-attribution link in logic. Across nineteen V12 answers,
native agent reviews record fourteen qualified accepts, two representation
rejections and three uncertainties. V12 remains experimental and is not activated
in hierarchy generation. Full method and limits are recorded below.

`pair-consolidation-owl-v11` is the preceding tested version. The user approved
making negated activities explicit as activity classes. Its three-case targeted
check records three qualified agent accepts: never-painted surfaces now retain
the paint-application class and participant, while completed painting and coffee
equipment preserve their targeted conditions. An independent painting repeat and
an unseen detergent-washing case also retain explicit negative activities. The
repeat introduces a possible building-only restriction, recorded as a separate
scope uncertainty. V11 remains experimental, without broader qualification or
activation in hierarchy generation.

An unchanged-V11 screen of eight exact HR14 root pairs records three qualified
agent accepts, two concrete rejections and three uncertainties. The rejections
are an English/formal scope mismatch and a duplicate formal/English definition.
Several unrelated pairs still produce headings that list disconnected kinds.
Formal coverage alone does not repair those browsing groupings. This screen
does not regenerate HR14 or test fit within a supplied canonical parent; see
the HR14 findings below.

`pair-consolidation-owl-v10` is the preceding tested version. The user approved
replacing the inherited rule that activity topics automatically include plans
with explicit purpose/use and plan representation. Activity classes retain the
action's identity; plans relate separately to their proposed activities. A
purpose or intended use alone does not establish occurrence, while explicit
actual use remains supplied evidence. Its six-case check is complete: six
qualified agent accepts, with activity/plan identity and stated actual use
preserved. Its subsequent twelve-case panel records nine qualified agent accepts,
one action-representation failure for a negated condition, and two input/contract
scope uncertainties. V10 remains experimental and is not activated in hierarchy
generation.
The shared meaning-writing text, Bootstrap companion, guide and example are
unchanged; no new example or production code is introduced.

V9's three matched controls exposed the shelf storage action in both coffee
orders and passed the bottle action/object check. Two qualified agent accepts
and one scope uncertainty were recorded: the forward activity glossaries
included plans to perform the activities. A subsequent read of the complete
assembled prompt found the inherited plan-browsing rule in its after-wrapper.
That is a plausible contributor, not a demonstrated causal attribution. Original
receipts and earlier classifications remain evidence, not independent human gold.

V8's twelve-case panel passed its targeted checks under qualified agent review.
Its independent follow-ups preserved explicit coffee drinking and passed the
unseen bottle-activity control, but the reversed shelf translation compressed
storage into `designedToStore`, without an activity class. This remains a
formal-representation failure under the requested action-as-class rule, not
demonstrated wrong containment. These saved inputs and assessments remain
evidence, not independent human semantic gold.

V7's two-order consumer check passes the targeted formal conditions. Its broader
twelve-case panel exposes one remaining representation failure:
`CoffeeDrinking` leaves the drinking action and required coffee object only in
an English glossary. The fixed twelve-case inputs and agent assessments remain
evidence, not independent human semantic gold.

For `pair-consolidation-owl-v6`, the user approved
adding the rule that every input restriction and alternative must appear in its
OWL expression or a supporting formal class definition, rather than only in an
English glossary. Its [two-order consumer check](pair-consolidation-owl-v6-consumer-v1.md)
is complete: both answers expose human consumer and nourishment purpose, but
the forward answer still hides the eating-or-drinking alternative in English.
V6 therefore has a demonstrated formal-rule compliance failure and remains
experimental, without activation in hierarchy construction.

`pair-consolidation-owl-v5` remains the last fully reviewed and piloted reference.
The user approved its wording with "OK LGTM." This experimental line is not a
replacement for `Hierarchy-pair-consolidation-v6`. Its [v5 pilot](pair-consolidation-owl-pilot-v1.md)
completed sixteen GPT-6.1 Sol medium requests: twelve initial cases, two exact
repeats and two reversed-order cases. All passed structural checks and preserved
the targeted restrictions under agent review; one review remains uncertain about
how much meaning must be represented formally rather than in English glossaries.

The user approved proceeding with this separate experimental line and the
following contract:

- A supplied parent contains formal logic and English definitions for names
  that lack a formal definition, without a separate title or meaning. The
  model preserves those definitions instead of generating a parent translation.
- Both input nodes retain their fixed natural-language titles and meanings.
- Output first supplies the first node's formal definition and English
  definitions, then the second node's, then the consolidated topic's, followed
  by the consolidated natural-language title and meaning.
- Reused names preserve their supplied definitions. Required relationships
  must appear in the formal representation rather than being introduced as
  unstated English assumptions.
- Every restriction and alternative stated in an input meaning must appear in
  its `owl.expression` or a supporting definition in `owl.classes`. English
  definitions explain basic terms; they must not be the sole representation of
  those conditions. Every stated alternative uses `OR`, directly in the
  expression or a supporting class definition. A class name may abbreviate
  conditions when its formal definition exposes them. Every activity stated
  inside a purpose or use retains its action as a class and relations to its
  required objects or participants. Plans retain their distinct identity and
  relation to the proposed activity; admitted activity/plan alternatives use
  `OR` without adding plans to an activity primitive.
- Each `owl` object has `expression` first, for the topic's own expression,
  then `classes`, a JSON object of supporting class definitions. The entrypoint
  is always `owl.expression`; `owl.classes` may be empty. This same layout is
  used by the supplied parent and all three returned formal representations.
- Expressions retain the OWL-like operators. Each expression is one string;
  supporting definitions are separate JSON fields rather than newline-separated
  `Name = expression` statements in one string.
- English glossaries cover referenced names that lack a formal definition.
  They do not duplicate supporting class definitions or the topic's entry
  expression. `Parent`, `Node1`, `Node2` and `Consolidated` are guide labels for
  entry expressions, not additional class definitions. The consolidated
  natural-language title and meaning remain separate final outputs.

Wording approval and this bounded pilot do not establish general semantic
correctness or authorize activation or further inference. Outermost parentheses
are omitted from expression strings; nested parentheses preserve grouping.

## Sources and assembly

The [v10 draft](pair-consolidation-owl-v10.md) is built by its
[pinned assembly manifest](pair-consolidation-owl-v10.assembly.json). It includes
[OWL-like guide v5](prompt_parts/owl-reasoning-guide-v5.md) and
[explicit-meaning rules v6](prompt_parts/explicit-meaning-rules-v6.md)
byte-for-byte. Its matching definition-writing reference is
[Bootstrap-v129](Hierarchy-bootstrap-v129.md).

V10 retains the [v9 prompt](pair-consolidation-owl-v9.md)'s one
[complete input/output example](prompt_parts/pair-consolidation-owl-example-v3.md)
using the same display-panel case, with each entry expression separated from
its supporting classes. The guide distinguishes exact class definitions from
one-way containment checks; required membership implications are expressed in
the formal definitions. It does not encode a containment claim as an exact
equivalence. The shared meaning-writing rules and consolidated natural-language
meaning-writing instructions are unchanged. The only compiled-prompt change
from v9 replaces the automatic plan-browsing sentences in the final-check
wrapper with explicit purpose/use and plan representation. All earlier
published prompt and guide files retain their original bytes.

The notation is the simplified OWL-like notation described in the guide. The
model supplies formal definitions, not an executable OWL document or a
mechanically verified proof. There is no parser, reasoner, constructor change,
experiment adapter or activated configuration in this task.

Only two input nodes and an optional parent are supplied per call. The shared
guide adds fixed input text; formal definitions and their English definitions
add output tokens. No call reduction, token saving or general semantic
correctness gain has been measured against another prompt. The pilot used sixteen fresh calls with
complete saved API-equivalent cost of $0.216726; it did not generate a hierarchy.

## Offline checks

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 sse_multivector/prompt_assembly.py check \
  sse_multivector/shr_single_pair/pair-consolidation-owl-v10.assembly.json
```

Assembly checks establish exact reconstruction and unchanged shared sources.
They do not establish faithful translation, valid containment or useful
consolidation. Pilot reviews are manual and separately attributed, with no
automated reasoner proof or human semantic gold. The completed v6 check made
two fresh requests with complete saved API-equivalent cost of $0.035414; it
generated no hierarchy.

## V7 check: method and completed findings

The user authorized the v7 revision and the same human-food comparison in both
orders. Prepare from the saved v6 forward and reversed experiments, replacing
only the prompt and retaining their exact inputs and Sol medium settings. Use
the [same pre-call checks](pair-consolidation-owl-v6-consumer-v1.md#fixed-inputs-and-assessment):
consumer, nourishment purpose and the eating-or-drinking alternative must be
formal; evening meals must not borrow the consumer or purpose restriction.
Allow different names and supporting class definitions. Check JSON structure,
coverage and English/formal agreement separately. Two passing draws would not
establish general accuracy or authorize hierarchy activation. No warmup,
additional baseline calls or paid fallback is added.

Both authorized requests completed on 2026-10-13, with one fresh Sol medium
attempt per orientation. Native inputs exactly match their v6 baselines, and
all non-input request-body fields remain identical. Both use fresh single-user
messages without a previous response reference or prior model output in the
input. All JSON layout, vocabulary, expression-formatting and unchanged reused
definition checks pass. Native attributed reviews contain two qualified agent
accepts and no user judgments.

| Human-food condition | Human food first | Human food second |
|---|---|---|
| Intended consumption | Formal | Formal |
| Human consumer/performer | Formal | Formal |
| Nourishment purpose | Formal | Formal |
| Eating-or-drinking alternative | `Eating OR Drinking` | `Eating OR Drinking` |

The forward translation is:

```text
Substance AND (intendedFor SOME ((Eating OR Drinking) AND (performedBy SOME Person) AND (hasPurpose SOME Nourishment)))
```

The reversed translation uses `hasConsumer SOME Person` in place of
`performedBy SOME Person`, with a corresponding English relation definition.
Evening meals retain `Meal AND (servedDuring SOME Evening)` without borrowing
human-food consumer or purpose restrictions. Both consolidations are unions of
Meal and substances intended for eating or drinking, so coverage follows from
the returned expressions; their English meanings preserve that scope.

The targeted alternative failure observed in v6 does not recur in either v7
draw. This does not establish a reliable wording effect: there is only one
sample per orientation. Ordinary Meal food/occasion interpretation and the
Substance glossary's consumability wording remain scope qualifications. They
are not independently validated human gold or demonstrated semantic failures;
these checks do not certify complete translation fidelity or browsing quality.
No machine reasoner was used. These targeted results motivated the broader
panel below, including supplied-parent, `SOME`/`ONLY`, completion-state and role
controls; they did not themselves qualify hierarchy integration.

The native `experiment-usage-summary-v3` report is complete, with no accounting
warnings: two fresh attempts, zero failures, retries, reuses or warmups, 6,250
input tokens and 1,939 output tokens. The 988 reasoning tokens are already
included in output. Cached input and reported cache-write tokens are zero.
Saved API-equivalent cost is **$0.031890**, a catalogue estimate rather than
subscription billing. The saved v6 baselines were not rerun.

The worktree is retained because native plans, frozen sources and receipt
validation require its absolute paths:

```text
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-owl-v7-consumer-v1
```

Its ignored evidence is `target/pair-consolidation-owl-v7-consumer-forward-v1`,
`target/pair-consolidation-owl-v7-consumer-reversed-v1`,
`target/pair-consolidation-owl-v7-consumer-checks-v1.json`,
`target/pair-consolidation-owl-v7-consumer-usage-source-v1.json` and
`target/pair-consolidation-owl-v7-consumer-usage-summary-v1.json`. The earlier
v6 and v5 worktrees retain their original baseline/input bindings. All prompts,
source inputs and earlier receipts remain unchanged after preparation.

## V7 broader panel — 2026-10-13

The user authorized the existing [twelve-case panel](pair-consolidation-owl-pilot-v1.md#frozen-inputs-and-expectations),
using the same native v5 inputs/settings with only the prompt replaced. Its
frozen restrictions remain outside the model input. One case is the prompt's
worked example, assessed only for format; eleven are authored synthetic controls,
not original-post hierarchy evidence or independent human gold. Native history
lookup exactly reuses the earlier v7 human-food forward answer; it is not a new
sample. The other eleven cases completed with fresh Sol medium requests.

All twelve outputs pass JSON layout, expression-formatting, vocabulary closure
and unchanged reused-definition checks, including supplied parent definitions.
Manual review finds both translated inputs covered by each consolidation and
each supplied parent respected through the printed class definitions. `SOME`
permits additional emitted colours; `ONLY` admits empty containers. Completed
painting and reached boiling retain their state requirements, plans do not
require execution, and explicit never-painted absence uses `NOT` rather than
assuming missing facts false. The lamp/sign alternatives remain formal `OR`
branches with correctly attached colour conditions.

Native reviews record eleven qualified agent accepts, including the trained
format case and reused answer, and one formal-rule reject. These counts are not
an accuracy estimate or machine-reasoner proof. Rosemary's `partOf` timing and
primitive Food/Garden scope, Bead interpretation, and the supplied Material
role-versus-performed-use definition remain fidelity qualifications. No new
incorrect consolidation is established from those unresolved interpretations.

### Remaining action/object representation failure

Case `10-coffee-equipment-roles` supplies "Cups designed for drinking coffee"
and "Shelves designed to store cups used for drinking coffee." The first
translation is:

```text
Cup AND (designedFor SOME CoffeeDrinking)
```

`CoffeeDrinking` has no formal class definition. Its English glossary says "The
activity of drinking coffee." The shelf's formal storage-to-cup chain is present,
and both translations are formally covered by the consolidation, but neither
the drinking action nor its required coffee object is exposed inside that class.
The same opaque activity class occurs in the saved v5 answer: this is a remaining
representation problem, not a newly demonstrated semantic regression or loss of
the English meaning.

The user approved a v8 revision to clarify the boundary for basic terms:
decompose the action and required objects, participants, purposes and states
explicitly specified in a supplied meaning; allow a name to abbreviate that
expression through `owl.classes`. Primitive English definitions can explain
concepts whose internal structure the supplied meaning does not specify. This
avoids requiring recursive technical definitions of every mentioned concept.
The v7 panel itself generated no next prompt version or hierarchy change.
The separately authorized v8 revision and matched test are recorded below.

### Accounting and retained panel evidence

Native `experiment-usage-summary-v3` accounting is complete, with no warnings:

| Accounting basis | Requests | Input tokens | Output tokens | API-equivalent cost |
|---|---:|---:|---:|---:|
| Fresh execution | 11 | 34,992 | 8,223 | $0.152214 |
| Original generation of all panel answers, including reuse source | 12 | 38,117 | 9,223 | $0.168464 |

There are no provider failures, retries or warmups. Cached input and reported
cache-write tokens are zero. The 3,170 fresh reasoning tokens are already included
in output; they are not charged twice. The reused source cost is counted once in
original generation and not as fresh spending or a cache hit. These are saved
catalogue estimates, not subscription invoices or measured policy savings.

The retained worktree is:

```text
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-owl-v7-panel-v1
```

Its ignored native evidence is `target/pair-consolidation-owl-v7-panel-v1`,
`target/pair-consolidation-owl-v7-panel-checks-v1.json`,
`target/pair-consolidation-owl-v7-panel-usage-source-v1.json` and
`target/pair-consolidation-owl-v7-panel-usage-summary-v1.json`. Frozen source,
baseline and exact-reuse validation also require the retained earlier task
worktrees. All prompt bytes, original inputs and prior receipts remain unchanged.

## V8 matched panel: pre-call method

Prepare from the completed v7 broader panel, replacing only the prompt. Retain
all twelve exact inputs, authored expectations outside model input, model,
medium reasoning, SSE settings and ordinary native reuse. No intentional
repeats, extra baseline requests, warmup or paid fallback are included.

Assess the same structure, fixed vocabulary, full input fidelity, two-node
coverage, supplied-parent containment and English/formal agreement separately.
In case 10, the coffee-drinking activity must expose the drinking action and its
required coffee object in `owl.expression` or a supporting `owl.classes`
definition. Preserve the cup's design purpose and the shelf's storage-to-cup
relationship. Accept equivalent relation names; do not require unstated internal
structure for basic terms such as Coffee. Review the other activity cases for
lost completion, plan or target conditions. These are agent checks, not human
gold or a machine-reasoner proof. No unique grouping is predetermined.

## V8 matched panel: completed findings — 2026-10-13

All twelve cases completed with GPT-6.1 Sol medium. Native preparation preserves
every input and runner setting from the v7 panel; no prior answer is reused
because the prompt changed. The twelve successful HTTP 200 requests have one
fresh user message each, no previous-response reference, and identical non-input
request-body fields relative to v7. Frozen assembly/source hashes remain exact.
No extra baseline requests, warmups or paid fallback were used.

All outputs pass JSON field ordering, expression formatting, vocabulary closure
and unchanged reused-definition checks. Qualified manual review finds the saved
conditions preserved and both translations covered by their consolidation;
where supplied, the fixed parent is respected through the printed definitions.
These are twelve qualified native agent accepts, including the trained format
case, not an accuracy estimate, human gold or a machine-reasoner proof.

### Coffee action and object now exposed

Case `10-coffee-equipment-roles` still uses the exact original cup and shelf
meanings. V8 supplies this supporting class definition in all three returned
objects:

```json
{
  "CoffeeDrinking": "Drinking AND (hasBeverage SOME Coffee)"
}
```

The cup retains `Cup AND (designedFor SOME CoffeeDrinking)`. The shelf retains
`Shelf AND (designedFor SOME CoffeeCupStorage)`, with:

```json
{
  "CoffeeCupStorage": "Storage AND (hasStoredObject SOME (Cup AND (usedFor SOME CoffeeDrinking)))"
}
```

The consolidation is `designedFor SOME (CoffeeDrinking OR CoffeeCupStorage)`.
The drinking action, coffee object and storage-to-cup-to-coffee relationship are
now formal; Coffee's unspecified internal structure remains in its English
basic-term definition. Design purpose is not replaced with actual use. This
resolves the observed v7 opaque-action failure in this draw, without proving a
reliable wording effect from one matched sample.

### Other saved controls and limits

| Saved control | Targeted result under qualified agent review |
|---|---|
| Known panel example | Requested structure and fixed vocabulary; format evidence only |
| Completed wall/ceiling painting | Painting action, home/interior targets and completion remain formal within the supplied parent |
| Completed painting versus cabinet plans | Plans retain their painting action and target without requiring execution |
| Lamps emitting red/blue light | `SOME` permits additional emitted colours; supporting definitions derive the chosen broader light class |
| Bead-only containers | `ONLY` without `SOME` admits empty containers and both allowed colours |
| Lamp/sign alternatives | `OR` retains correct emission/background attachment; supplied definitions derive Device containment |
| Never-painted walls/ceilings | Explicit historical absence uses `NOT`, without inferring absence from silence |
| Rosemary roles | Culinary-leaf and garden-plant roles remain distinct |
| Material versus product | Designated-making role and product's made-from relation remain distinct |
| Identical boiling meanings | Heating target and reached-boiling state remain formal, including the supplied parent |
| Human food versus evening meals | Human consumer, nourishment purpose and eating-or-drinking alternative remain specific to human food |

This small authored panel does not establish full semantic fidelity or
browsing usefulness. Rosemary's `partOf` origin versus present-attachment interpretation,
primitive Food/Garden and Bead scopes, the supplied Material wording about actual
use, and Meal's food/occasion interpretation remain explicit qualifications.
V8 has not independently resolved these ordinary-language interpretations, and
they are not assigned new human-gold labels or counted as demonstrated semantic
failures. The notation is still not executable OWL and no reasoner was used.

The user separately authorized the independent repeat, reversed-order coffee
draw and unseen activity/object control recorded below. They are not part of
the completed twelve-case panel or authorization for hierarchy integration.

### Accounting and retained evidence

The native `experiment-usage-summary-v3` report records fifteen fresh provider
attempts for twelve successful answers: three first attempts returned the
provider's "servers are currently overloaded" error, each recovered on its one
allowed retry. There are zero terminal failures, reuses and warmups. The failed
attempts supplied no raw token usage, so the complete API-equivalent cost is
unknown rather than zero for those attempts.

| Known subtotal | Value |
|---|---:|
| Input tokens | 38,705 |
| Output tokens, including reasoning | 9,585 |
| Reasoning tokens already included in output | 3,798 |
| Reported cached input / cache-write tokens | 0 / 0 |
| API-equivalent catalogue estimate | $0.173260 |
| Attempts with missing usage/cost | 3 |

The native summary warns that these are known subtotals. This is not subscription
billing, complete trial cost, or a savings claim. All actual attempts remain in
the original receipts; no receipt or historical prompt has been modified.

The retained source/evidence worktree is:

```text
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-owl-v8-panel-v1
```

Its ignored evidence is `target/pair-consolidation-owl-v8-panel-v1`,
`target/pair-consolidation-owl-v8-panel-checks-v1.json`,
`target/pair-consolidation-owl-v8-panel-usage-source-v1.json` and
`target/pair-consolidation-owl-v8-panel-usage-summary-v1.json`. This worktree and
the retained v7/v6/v5 source worktrees remain necessary for native frozen-source,
baseline and receipt validation at their absolute paths.

## V8 independent follow-ups: pre-call method

The user authorized three follow-up cases without changing any V8 prompt bytes:

- Prepare case `10-coffee-equipment-roles` from the saved V8 panel with native
  `--only` and `--repeat`, forcing one independent answer rather than reuse.
- Use the [follow-up source](pair-consolidation-owl-v8-generalization-source-v1.json)
  for the exact coffee input with only its two-node order reversed, and one
  unseen authored pair: "Brushes designed for washing bottles" versus "Basins
  designed for soaking bottles." No parent is supplied in either case.
- Use the [native spec](pair-consolidation-owl-v8-generalization-v1.spec.json)
  with the same Sol medium, subscription and SSE settings. Start both ready
  native batches immediately; let the shared runner own scheduling and retries.
  No warmup, extra baseline request, paid fallback or hierarchy change is added.

Freeze assessment before inference: both coffee orientations must expose the
Drinking action and Coffee object, the shelf's storage-to-cup relationship, and
design purpose rather than required actual use. The unseen pair must expose
Washing and Soaking with each activity's required Bottle object, while retaining
the equipment's design purpose. Do not infer a cleaning purpose for soaking.
Accept equivalent relation names and supporting classes; no unique consolidated
title or unnecessary internal structure of basic concepts is prescribed. Check
structure, independently faithful node translations, coverage and English/formal
agreement separately. Preserve unresolved interpretations instead of assigning
new human-gold labels. Expectations remain outside the model input.

## V8 independent follow-ups: completed findings — 2026-10-13

All three authorized requests completed on Sol medium with one fresh attempt
each. The exact coffee repeat's complete wire request body matches the saved
panel request; its upstream response identity differs. All three requests have
one fresh user message, no prior-response reference, and identical non-input
request-body fields. The reversal changes only the original two-node order;
the unseen input is the pre-call authored washing/soaking pair. V8 and its shared
sources remain byte-identical. No earlier answer or expectation entered model
input, and no paid fallback, hierarchy edit or warmup occurred.

All three outputs pass JSON layout, expression formatting, vocabulary closure
and unchanged reused-definition checks. Native reviews record two qualified
agent accepts and one formal-rule reject; there are no user semantic labels.

| Follow-up | Result under agent review |
|---|---|
| Exact coffee repeat | Coffee drinking retains formal Drinking and Coffee; Storing and its required cup object are also formal. Design purpose and coverage pass. |
| Coffee order reversed | Coffee drinking remains formal, but the shelf's storage action is compressed into a primitive relation. Coverage still passes under the printed definitions. |
| Unseen bottle activities | Washing and Soaking each have a formal Bottle object. Equipment design purpose remains distinct from actual activity; Soaking receives no cleaning-purpose condition. |

The reversed shelf translation is:

```text
Shelf AND (designedToStore SOME (Cup AND (usedFor SOME CoffeeDrinking)))
```

Its `owl.classes` defines CoffeeDrinking as `Drinking AND (consumes SOME Coffee)`.
It does not define a storage activity. The glossary instead defines
`designedToStore` as "A relation from an item to the kinds of objects it is
designed to hold in storage." Thus the storage purpose is still represented by
a relationship, but the storing action is not a class as requested by V8's
activity decomposition rule. This is a representation-compliance judgment, not
proof that the translation lost its ordinary English meaning or that the
consolidation is semantically incorrect.

Both coffee follow-ups choose a union of cups used or designed for coffee
drinking and items designed to store those cups. Each full printed translation
is covered. Their union differs from the original panel's broader design-purpose
union; no unique consolidated scope was prescribed, and this difference alone
is not an error. The unseen output uses:

```text
Equipment AND (designedFor SOME ((Washing OR Soaking) AND (hasObject SOME Bottle)))
```

Both bottle translations fit that expression, and its English meaning retains
the same design-purpose alternatives. Primitive Brush/Basin/Equipment and
ordinary activity meanings remain interpretation qualifications, not human
gold or automated satisfiability/fidelity certification. No machine reasoner
was used. Two coffee follow-ups support the targeted drinking/object fix; the
storage compression shows the general representation rule still needs clarity.

The user separately authorized V9 to explicitly apply action-as-class
decomposition inside stated purposes or uses, retaining basic concepts whose
internal structure the supplied meaning does not specify. That revision and
its matched test are recorded below; they were not part of this completed V8
trial. No hierarchy activation was authorized.

Native `experiment-usage-summary-v3` accounting is complete, without warnings:
three attempts, zero failures, retries, reuses and warmups; 9,531 input tokens,
3,087 output tokens and 1,258 reasoning tokens already included in output.
Reported cache read/write tokens are zero. Complete saved API-equivalent cost is
**$0.049932**, a catalogue estimate rather than subscription billing. The old
panel and its original costs are not counted as new calls in this follow-up.

The worktree is retained for native frozen-source and receipt validation:

```text
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-owl-v8-generalization-v1
```

Its ignored evidence is `target/pair-consolidation-owl-v8-coffee-repeat-v1`,
`target/pair-consolidation-owl-v8-generalization-v1`,
`target/pair-consolidation-owl-v8-generalization-checks-v1.json`,
`target/pair-consolidation-owl-v8-generalization-usage-source-v1.json` and
`target/pair-consolidation-owl-v8-generalization-usage-summary-v1.json`. The
retained earlier worktrees still supply the exact native panel baseline/source
bindings. Original receipts, historical prompts and inputs remain unchanged.

## V9 matched controls: pre-call method

Prepare two native batches from the completed V8 follow-ups, replacing only the
prompt: the exact forward coffee case, and the saved reversed coffee plus
washing/soaking cases. Retain their inputs, model, medium reasoning, subscription
route, SSE settings and pre-call authored checks. No baseline is rerun, no
intentional repeat flag is needed for the changed prompt, and exact native reuse
remains available. Launch both ready batches without an outer concurrency limit.
No warmup, paid fallback or hierarchy edit is added.

In both coffee orientations, Drinking and its Coffee object must be formal; the
shelf's storage purpose must include a storage activity class and its required
cup object, inline or through `owl.classes`. A compound relation alone does not
meet that requested representation. Preserve design purpose, cups used for
coffee drinking and the separate fixed cup meaning. In the bottle case, preserve
formal Washing/Soaking actions with their Bottle objects, without requiring
actual activity or adding a cleaning purpose to Soaking. Retain the same JSON,
vocabulary, coverage and English/formal checks. Relation names and coherent
broader topics may vary. No model answer or expectation enters model input;
these are agent assessments, not human gold or an automated reasoner proof.

## V9 matched controls: completed findings — 2026-10-13

All three controls completed on GPT-6.1 Sol medium. The inputs and settings
exactly match their corresponding V8 follow-ups; only the prompt changed.
Successful requests contain one fresh user message, no previous-response
reference and unchanged non-input request-body fields. All source/assembly
hashes remain fixed. No old answer or authored expectation entered model input.

All three pass JSON layout, expression formatting, vocabulary closure and
unchanged-definition checks. The targeted activity decomposition passes in
both coffee orders and the bottle control. Native reviews contain two qualified
agent accepts and one independent scope uncertainty, with no user gold labels
or machine-reasoner proof.

| Saved control | Targeted result | Separate qualification |
|---|---|---|
| Coffee forward | Drinking/Coffee and Storing/required cups are formal; printed coverage passes | Action glossaries include "plans to perform" the activity; full fidelity remains uncertain |
| Coffee reversed | Shelf now has Storing and its required cup object; Drinking/Coffee remains formal | "Planned instances" wording remains an ordinary-language interpretation qualification |
| Bottle washing/soaking | Both activities and Bottle objects are formal; design purpose and English coverage pass | Primitive concepts are not independently human-validated |

The reversed shelf now starts:

```text
Shelf AND (designedFor SOME (Storing AND (storedObject SOME CoffeeCupInUse)))
```

`CoffeeCupInUse` is `Cup AND (usedFor SOME CoffeeDrinking)`;
`CoffeeDrinking` is `Drinking AND (consumedBeverage SOME Coffee)`. Storage is no
longer represented solely by `designedToStore`. The forward answer also exposes
Storing through `CoffeeCupStorage`. This corrects the observed representation
failure in this matched draw, not a proven reliable wording effect.

### Separate plan/activity scope uncertainty

The forward answer defines Drinking as "The activity of drinking a beverage,
including plans to perform that activity." Storing likewise includes "plans to
perform that activity." The fixed node meanings instead supply items designed
for drinking coffee or storing cups used for drinking coffee. They do not name
planning as an additional design purpose. The final English consolidation also
names drinking and storing, without a separate planning alternative.

If the primitive classes admit plans themselves, design-for-planning can be
admitted where the supplied meaning requires design-for-the-activity. If the
wording only denotes prospective, unperformed activities, that counterexample
does not follow. Record this as unresolved scope interpretation rather than
asserting a new semantic failure or silently calling the whole answer faithful.
The reversed answer's "planned instances" wording does not explicitly say
plans themselves are members, and is retained as a qualification. Both printed
consolidations still cover their translated nodes.

The user separately authorized the V10 replacement and the contrasts recorded
below. The completed V9 trial itself made no V10 calls or hierarchy changes.

### Accounting and retained evidence

Native `experiment-usage-summary-v3` records four fresh attempts for three
answers. The forward first attempt returned "Our servers are currently
overloaded" and recovered on its one allowed retry. There are zero terminal
failures, reuses and warmups. Known usage is 9,552 input tokens, 3,348 output
tokens and 1,338 reasoning tokens already included in output. Reported cache
read/write tokens are zero. Known API-equivalent catalogue subtotal is
**$0.052584**; the complete cost is unknown because the failed attempt supplied
no usage. Native accounting retains that warning. This is not subscription
billing or a savings claim; the V8 baselines were not rerun.

The worktree is retained for frozen-source and receipt validation:

```text
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-owl-v9-controls-v1
```

Ignored evidence is `target/pair-consolidation-owl-v9-coffee-forward-v1`,
`target/pair-consolidation-owl-v9-reversed-and-bottle-v1`,
`target/pair-consolidation-owl-v9-controls-checks-v1.json`,
`target/pair-consolidation-owl-v9-controls-usage-source-v1.json` and
`target/pair-consolidation-owl-v9-controls-usage-summary-v1.json`. Earlier
retained worktrees still supply exact baseline/source bindings. Historical
prompts, fixed inputs and original receipts remain unchanged.

## V10 purpose/use/plan check: pre-call method

The user authorized the replacement after a read-only audit found the inherited
plan-browsing sentence at line 7 of the [old after-wrapper](prompt_sources/pair-consolidation-owl-v5.after.md).
Replace that sentence pair with the proposed identity and representation rule;
leave the other assembly parts unchanged. The occurrence sentence explicitly
concerns purpose or intended use, preserving any actual use stated in input.

The approach follows official guidance on concise, direct constraints,
consistent examples and resolving competing instructions. This supports the
method, not the semantic correctness of this particular rule: [OpenAI reasoning
guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively)
and [prompt optimization example](https://developers.openai.com/cookbook/examples/gpt-5/prompt-optimization-cookbook#our-baseline-prompt).

Prepare the three exact V9 coffee-forward, reversed-coffee and bottle controls
with only the prompt replaced. Prepare three new authored contrasts through the
[native source](pair-consolidation-owl-v10-purpose-plan-source-v1.json) and
[spec](pair-consolidation-owl-v10-purpose-plan-v1.spec.json): designed washing
brushes, items explicitly used in past washing/soaking, and a washing activity
versus a plan to perform it. Six cases in three independent native batches;
launch all ready batches immediately on the same Sol medium subscription/SSE
settings. No intentional repeat, extra baseline call, warmup, paid fallback,
additional example or hierarchy change is included. Exact native reuse remains
available, and the shared runner owns scheduling and provider-only retries.

Assess structure, formal actions/objects, activity versus plan identity,
independent input fidelity, coverage and English/formal agreement separately.
Do not infer occurrence from intended use or erase explicitly stated actual
use. Plans require their distinct kind and a relation to the proposed activity;
combined activity/plan scope must be formally exposed rather than hidden in an
activity glossary. Basic concepts need no unstated technical decomposition.
Allow equivalent vocabulary and coherent broader topics, without predetermining
one consolidated title. Frozen expectations stay outside model input; assessments
are agent-authored, not human gold or automated reasoner certification. A passing
screen would not establish reliability or prove the old sentence caused the V9
wording. Test this replacement before deciding whether another example is needed.

## V10 purpose/use/plan check: completed findings — 2026-10-13

All six authorized cases completed with one fresh GPT-6.1 Sol medium attempt
each. The three V9 control inputs/settings are exact; the other three use the
pre-call authored source above. Only the prompt changes for matched controls.
All requests have one fresh user message, no prior-response reference and the
same non-input request-body fields. Frozen sources remain exact. No baseline
was rerun, old output supplied, example added or hierarchy changed.

All six outputs pass JSON layout, expression formatting, vocabulary closure and
unchanged-definition checks. Manual targeted review records six qualified native
agent accepts, without user gold or machine-reasoner proof. Both translations
are covered by their chosen consolidation and its English under the printed
definitions. Coherent broader scopes may differ between draws; no unique
consolidated title or scope was predetermined.

| Case | Targeted finding |
|---|---|
| Coffee forward | Drinking/Coffee and Storage/coffee-use cups remain formal; activity glossaries no longer include plans |
| Coffee reversed | Storing, cup role and Drinking/Coffee remain formal; design purpose does not assert occurrence |
| Bottle design roles | Washing/Soaking and Bottle remain formal; no cleaning purpose is imposed on Soaking |
| Designed washing brushes | Designed-for Washing with Bottle/Jar objects retained; no actual-use or planning-purpose requirement |
| Actual past use | `hasBeenUsedIn` retains explicitly stated actual use, without requiring whole-task completion |
| Washing versus plans | Activity and Plan remain distinct; the consolidation exposes their alternatives with `OR` |

The explicit-plan result separates the two kinds:

```json
{
  "activity": "Washing AND (hasObject SOME Bottle)",
  "plan": "Plan AND (proposes SOME BottleWashing)",
  "consolidated": "BottleWashing OR (Plan AND (proposes SOME BottleWashing))",
  "classes": {
    "BottleWashing": "Washing AND (hasObject SOME Bottle)"
  }
}
```

These fields excerpt the returned expressions; they are not a new output schema.
Its English meaning covers washing activities and plans to carry them out.
The purpose-bearing coffee expressions keep Drinking and Storage/Storing as
activity classes; their English definitions do not include plans. The actual-use
control keeps `hasBeenUsedIn`, defined as a relation to an activity that has
actually occurred and in which the item was used. Thus removing automatic plan
inclusion did not erase explicit past use in this screen.

The V9 plan-membership wording does not recur in these six draws. This supports
the replacement, but does not prove the old sentence caused the earlier wording:
V10 removes that sentence and supplies a positive representation rule, with one
sample per case and no deletion-only ablation. Primitive vocabulary and
intensional purpose/proposal interpretation remain unvalidated by independent
human gold. All six inputs are roots, so this screen did not test supplied-parent
fit. No new example is warranted from this passing screen. The user then
authorized the existing twelve-case panel, reported below; those calls are
accounted separately from this six-case trial. No hierarchy activation is
authorized.

Native `experiment-usage-summary-v3` accounting is complete without warnings:
six fresh attempts, zero failures, retries, reuses or warmups; 19,446 input
tokens, 5,185 output tokens and 2,049 reasoning tokens already included in output.
Reported cache read/write tokens are zero. Complete saved API-equivalent cost is
**$0.090742**, a catalogue estimate rather than subscription billing or a savings
claim. The V9 baseline generation and its missing failed usage are not charged
again as new work in this trial.

The worktree is retained for frozen code/source and native receipt validation:

```text
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-owl-v10-purpose-plan-v1
```

Its ignored evidence is `target/pair-consolidation-owl-v10-coffee-forward-v1`,
`target/pair-consolidation-owl-v10-reversed-and-bottle-v1`,
`target/pair-consolidation-owl-v10-purpose-plan-v1`,
`target/pair-consolidation-owl-v10-purpose-plan-checks-v1.json`,
`target/pair-consolidation-owl-v10-purpose-plan-usage-source-v1.json` and
`target/pair-consolidation-owl-v10-purpose-plan-usage-summary-v1.json`. Earlier
retained worktrees still supply exact baseline/source bindings. Historical
prompts, source inputs and original receipts remain unchanged.

## V10 twelve-case panel: pre-call method

The user authorized the existing twelve-case panel against unchanged V10. Native
preparation inherits the V7 panel's exact case IDs, input bytes and Sol 6.1 medium
subscription/SSE settings, with V10 replacing only the prompt. The V10 coffee
answer is an exact native reuse; eleven cases require fresh answers. No baseline
rerun, intentional repeat, warmup, extra example or hierarchy activation is
included. All preparation and execution bindings point to isolated worktrees.

Review the supplied-parent cases as well as completion, plans, `SOME` versus
`ONLY`, explicit absence, alternatives and material/ingredient roles. Check
independent input fidelity, coverage, parent containment and English/formal scope
separately. Do not infer relationships from class names alone or introduce
unstated conditions to make containment pass. Retain the material-use and basic
concept scope qualifications; these authored inputs do not establish human gold.
The worked-example case tests formatting, not unseen semantic generalization.

## V10 twelve-case panel: completed findings — 2026-10-13

All twelve cases completed: eleven fresh GPT-6.1 Sol medium calls and one exact
native reuse of the V10 coffee answer. There were no failures, retries, warmups
or baseline reruns. Each fresh receipt reports HTTP 200 and GPT-6.1 Sol; each
request uses one user message, without a prior-response reference. Inputs and
settings match the frozen V7 panel, and all source hashes remain exact. The
initial delay was shared queue admission, followed by reported recovery limits;
it was not a failure of this batch's requests.

All twelve outputs pass JSON layout, expression formatting, vocabulary closure
and unchanged-definition checks. Native manual reviews record **nine qualified
agent accepts, one formal-rule reject and two uncertainties**. These are agent
assessments of authored controls, not user gold or automatic reasoner proofs.

| Case | Assessment | Finding |
|---|---|---|
| Worked example | Format-only accept | Blue background and installed-component roles fit the supplied parent |
| Completed painting | Qualified accept | Completion, interior targets and supplied parent are retained |
| Completed activity / painting plans | Qualified accept | Activities and plans remain separate `OR` alternatives |
| Lamps emitting coloured light | Qualified accept | `SOME` permits other emitted light; no `ONLY` added |
| Containers restricted to beads | Qualified accept | `ONLY` retains empty containers; consolidation permits mixed red/blue contents |
| Lamp / sign alternatives | Qualified accept | Both input alternatives stay explicit; fixed definitions establish Device containment |
| Never-painted walls / ceilings | Formal-rule reject | Paint application is represented only through a relation and its glossary, without an activity class |
| Rosemary roles | Qualified accept | Ingredient Flavouring/Food and plant Cultivation/Garden are formal; consolidation covers plants and parts |
| Material / product | Uncertain | Formal coverage holds, but supplied Material wording versus intended designation remains ambiguous |
| Equivalent boiling | Uncertain | State/equivalence/parent checks pass; the fixed WaterHeating primitive leaves its object in a supplied glossary |
| Coffee equipment | Qualified accept, reused | Drinking/Coffee and Storage/cup-role conditions remain formal; no new draw |
| Human food / evening meals | Qualified accept | Consumer, purpose, alternatives and evening serving remain explicit; no human restriction transferred to meals |

### Negated activity representation

The never-painted wall translation is:

```text
Wall AND InteriorConstructionElement AND NOT (hasEverReceivedApplicationOf SOME Paint)
```

The ceiling substitutes `Ceiling` for `Wall`. The relation glossary says it
connects a physical element to material applied to it at any time. Thus the
negative condition is preserved, and both translations are covered by the
returned never-painted interior-element consolidation. However, there is no
paint-application activity class or formal activity/participant representation.
The current rule requires every stated activity to have that representation.
This is a rule-compliance failure, not a demonstrated wrong absence judgment or
containment result. A plausible explanation is that the model treated the
negative condition solely as a property of the wall; this draw does not establish
the cause or frequency. It is not established as a V10 regression: the earlier
panel assessments were targeted screens, not independent negative-action audits.

The supplied-parent conclusions hold through the printed definitions in all
eight parent cases. That is separate from independent input fidelity. The
material case retains the supplied `Material` definition, "A substance used to
make things," while translating designated material with an explicit Making/
Cookware purpose. Actual-use versus generic material-kind interpretation remains
unsettled; it is not new model-error gold. The boiling case preserves the exact
`WaterHeating AND BoilingReached` parent for both equivalent nodes. Its supplied
WaterHeating glossary says "Heating liquid water," so this does not independently
test formal action/object decomposition. The compatibility of that supplied
primitive with the decomposition requirement remains a contract qualification.

Basic Bead, Food, Garden and Meal interpretations remain qualified vocabulary,
without independent human validation. Rosemary's "whether still attached or
removed" wording is also a writing qualification under the preference for
positively stated optional variations; no changed membership condition is shown.
These qualifications must not be silently converted into full semantic passes.

The user subsequently approved an explicit activity representation for the
negative condition and authorized V11, documented below. No V11 edit or further
inference is part of this completed V10 panel.

### Accounting and retained evidence

Native `experiment-usage-summary-v3` accounting is complete without warnings:
eleven fresh attempts, one exact reuse and zero failures/retries/warmups; 36,241
fresh input tokens, 7,759 output tokens and 2,820 reasoning tokens already included
in output. Reported cache read/write tokens are zero. Fresh API-equivalent
catalogue cost is **$0.150072**. Original generation of all twelve answers,
including the coffee producer once, is **$0.168030**. Reuse is not a cache hit,
independent draw or measured policy saving; catalogue estimates are not
subscription billing.

The worktree remains necessary for frozen source/code and receipt validation:

```text
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-owl-v10-panel-v1
```

Ignored evidence is `target/pair-consolidation-owl-v10-panel-v1`,
`target/pair-consolidation-owl-v10-panel-checks-v1.json`,
`target/pair-consolidation-owl-v10-panel-usage-source-v1.json` and
`target/pair-consolidation-owl-v10-panel-usage-summary-v1.json`. Earlier retained
worktrees provide frozen inputs, baselines and the exact reused coffee producer.
Prompt bytes, old assessments and original receipts are unchanged.

## V11 negated-activity check: pre-call method

The user reviewed the V10 never-painted answer and approved an explicit
paint-application activity representation inside the negative condition, then
authorized the fix. The saved V10 `06-explicit-absence` answer supplies the
before-change failure; it is not rerun. Publish
[pair-consolidation-owl-v11](pair-consolidation-owl-v11.md) with one paragraph
changed: the existing activity rule explicitly includes negative conditions,
and non-occurrence negates a `SOME` connection to the activity expression while
preserving stated time scope. Shared rules, Bootstrap companion, guide, example,
output contract and historical prompt bytes remain unchanged.

Native preparation selects three exact V10 panel inputs: never-painted
walls/ceilings, completed interior painting and coffee equipment. Preserve their
Sol 6.1 medium subscription/SSE settings; change only the prompt. All three
require fresh calls, with native exact reuse available if a matching answer
exists. No intentional repeat, warmup, baseline rerun or hierarchy activation
is included.

Assess the negative case for an activity class and explicit paint participant,
an actual-occurrence relation to the stated surface, and the full never-applied
time scope. Do not introduce a completed-painting requirement. Accept equivalent
names and inline or supporting expressions rather than requiring the proposed
example verbatim. Check coverage and English/formal agreement separately. The
positive controls must preserve the supplied completed-painting parent and
coffee design/use roles without asserting occurrence from purpose alone.

This is a targeted representation check, not broader semantic certification or
proof of reliability. The short direct clarification follows [official reasoning
guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively);
no new worked example or reasoning narrative is requested.

## V11 negated-activity check: completed findings — 2026-10-13

All three cases completed with one fresh GPT-6.1 Sol medium attempt each, without
failures, retries, reuses or warmups. Exact inputs/settings remain bound to the
V10 panel; no old answer appears in model input. Raw receipts report HTTP 200
and GPT-6.1 Sol. All requests have one user message, identical non-input body
fields and no prior-response reference. Frozen source hashes remain unchanged.

All three outputs pass JSON layout, expression formatting, vocabulary closure
and unchanged-definition checks. Native reviews record three qualified agent
accepts. Names and grouping scopes were not prescribed. No executable reasoner
or independent human semantic gold is used.

The negative wall expression now uses:

```json
{
  "expression": "InteriorWall AND NOT (hasEverBeenTargetOf SOME PaintApplication)",
  "classes": {
    "InteriorWall": "InteriorArchitecturalElement AND Wall",
    "PaintApplication": "MaterialApplication AND (appliesMaterial SOME Paint)"
  }
}
```

The ceiling substitutes its own formally defined `InteriorCeiling`. The
consolidation retains `InteriorArchitecturalElement` and the identical negative
condition. `hasEverBeenTargetOf` connects a thing to an application activity
directed onto it at any time up to the present; `MaterialApplication` is the
activity of applying material onto a target; `appliesMaterial` connects that
activity to its material. The action and Paint participant are thus explicit.
No completion condition is introduced, so partial application still excludes
membership. Plans are not made members of the activity class. The final English
retains never-applied paint and covers the translated walls and ceilings.

The completed-painting control keeps `PaintingActivity`, `Completed` and its
target relation; formal interior classes inherit `HomeSurface`, establishing
the supplied-parent conclusion. The coffee control retains Drinking/Coffee and
Storage/cup-role conditions. Its broader CoffeeCup supporting definition admits
designed-for or used-for cups; its shelf alternative keeps the storage-design
relationship, covering both fixed inputs. English preserves those alternatives.
The coffee title lists cups and shelves rather than selecting a shared-category
heading; retain this as a writing qualification, not a containment failure.

The observed missing-activity-class defect is absent in this draw. Three targeted
answers do not establish reliability, broader-panel success or unique correct
primitive vocabulary. V10's material-use and supplied-WaterHeating qualifications
were not tested or resolved here. The user subsequently authorized the independent
repeat and unseen negative-action control reported below; their inference is
separate from this initial three-case screen.

Native `experiment-usage-summary-v3` accounting is complete without warnings:
three fresh attempts, 9,919 input tokens, 2,628 output tokens and 868 reasoning
tokens already included in output. Reported cache read/write tokens are zero.
Complete fresh API-equivalent catalogue cost is **$0.046118**; this is not
subscription billing or a savings claim. No baseline generation is charged again.

The worktree is retained for its frozen source/code bindings and saved receipts:

```text
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-owl-v11-negative-action-v1
```

Ignored evidence is `target/pair-consolidation-owl-v11-negative-action-v1`,
`target/pair-consolidation-owl-v11-negative-action-checks-v1.json`,
`target/pair-consolidation-owl-v11-negative-action-usage-source-v1.json` and
`target/pair-consolidation-owl-v11-negative-action-usage-summary-v1.json`.
Earlier worktrees retain the unchanged V10 baselines and source bindings.

## V11 negative-action follow-ups — 2026-10-13

The user authorized one intentional fresh repeat of the never-painted case and
one unseen negative-action case against unchanged V11. Native `prepare --from
--only 06-explicit-absence --repeat` preserves the first case's complete prompt,
input and settings while bypassing answer reuse. The
[authored transfer source](pair-consolidation-owl-v11-negative-transfer-source-v1.json)
and [native spec](pair-consolidation-owl-v11-negative-transfer-v1.spec.json) provide
bottles and jars that have never been washed using detergent. Pre-call conditions
require Washing and Detergent to be formal, preserving actual-history scope and
allowing washing without detergent. Expectations remain outside model input;
they are agent-authored conditions, not human gold or a prescribed grouping.
Both independent batches were submitted before waiting. No prompt edit,
additional example, warmup, paid fallback or hierarchy change is included.

Both cases completed with one fresh Sol 6.1 medium attempt each, without failures,
retries or reuses. All structural/vocabulary/definition checks pass. Raw receipts
report HTTP 200 and GPT-6.1 Sol. The repeat's complete request body exactly matches
the first V11 painting request and has a different upstream response reference.
Both requests have one user message and no prior-response reference; the unseen
case changes input data only. Frozen sources remain exact. Native reviews record
one qualified accept and one scope uncertainty, rather than two full semantic
passes.

The painting repeat retains the explicit activity inline:

```text
InteriorBuildingElement AND Wall
AND NOT (hasEverBeenTargetOf SOME (Application AND (appliesMaterial SOME Paint)))
```

The ceiling substitutes `Ceiling`; the consolidation drops the individual kind
while keeping the same interior and negative conditions. Application is an
activity of applying material, and the history relation covers any time up to
the present. The representation fix therefore survives this repeat. However,
`InteriorBuildingElement` is defined as "A physical element forming part of a
building's interior." The fixed inputs say only interior walls/ceilings. An
unpainted interior wall or ceiling of a ship is a plausible excluded case under
a broader reading of those inputs. Record this as an independent fidelity
uncertainty, not recurrence of the missing activity class or independently
validated semantic failure. Coverage of the translated nodes alone cannot
establish that the input meanings were translated faithfully.

The unseen washing case returns:

```json
{
  "node1": "Bottle AND NOT (hasEverUndergone SOME DetergentWashing)",
  "node2": "Jar AND NOT (hasEverUndergone SOME DetergentWashing)",
  "consolidated": "Container AND NOT (hasEverUndergone SOME DetergentWashing)",
  "classes": {
    "Bottle": "Container AND BottleKind",
    "Jar": "Container AND JarKind",
    "DetergentWashing": "Washing AND (uses SOME Detergent)"
  }
}
```

This excerpts expressions and supporting classes, not a new response schema.
`hasEverUndergone` connects the object to an activity performed on it at any time
up to the present. Only detergent washing is negated. Washing without detergent
is compatible, while detergent-and-water washing still satisfies the excluded
`SOME Detergent` condition. No `ONLY` or completion condition is added. Explicit
Bottle/Jar definitions establish containment under Container; the final English
preserves the same negative condition. This is one qualified authored transfer
control, not broad semantic certification.

The action-representation rule holds in both follow-ups. Preservation of an
explicit building-or-ship alternative remains untested; the unqualified noun
must not become new human gold. No further case, inference or prompt revision
was prepared in that follow-up task. The subsequent user-requested HR14 screen
below tests different real pairs against unchanged V11.

Native `experiment-usage-summary-v3` accounting is complete without warnings:
two fresh attempts, 6,548 input tokens, 1,700 output tokens and 625 reasoning
tokens already included in output. Cache read/write tokens are zero. Complete
fresh API-equivalent catalogue cost is **$0.030096**; this is not subscription
billing or a savings claim. The intentional repeat is a new draw, not a retry.

The worktree is retained for frozen source/code bindings and native receipts:

```text
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-owl-v11-generalization-v1
```

Ignored evidence is `target/pair-consolidation-owl-v11-negative-repeat-v1`,
`target/pair-consolidation-owl-v11-negative-transfer-v1`,
`target/pair-consolidation-owl-v11-generalization-checks-v1.json`,
`target/pair-consolidation-owl-v11-generalization-usage-source-v1.json` and
`target/pair-consolidation-owl-v11-generalization-usage-summary-v1.json`.
Earlier retained worktrees supply the unchanged first V11 answer and historical
source bindings; old outputs and assessments remain unchanged.

## V11 on HR14 real pair consolidations — 2026-10-13

The user requested viewing the fifty-note HR14 hierarchy, observing pair
consolidation failures, and testing how the current prompt handles them. The
existing review UI's exported tree and the immutable construction state were
inspected read-only. No UI refresh, hierarchy regeneration, prompt edit or
activation was performed.

### What HR14 shows

The saved hierarchy has 354 canonical nodes, 348 edges and six roots. Its roots
are Concrete and abstract entities and phenomena; Food, drink, and related
matters; Subjects and their relationships; The world and lived experience;
Biological materials and food-and-drink systems; and Activities, resources, and
outcomes. Several give little guidance about which branch to browse. The
construction repeatedly consolidates all selected pairs, including weakly
related pairs, into at most six nodes. The first family alone contains 162 pair
consolidations from 324 nonnull original L1 meanings.

Concrete saved branches include:

- C00003 → C00067 Semantic and functional relationships → C00215 Designation
  and reference → C00219 Beets, C00220 MrBeast, C00221 Calendar dates and
  C00222 BitcoinDayOfTheYear.
- C00003 → C00068 Life and activity in context → C00278 Communication and
  context → C00291 Greetings, C00292 Greetings, C00293 Time after 9 a.m. and
  C00294 Kings.

These are browsing-quality witnesses, not automatically false containment.
For example, HR14's initial Beets/MrBeast parent is General reference, explicitly
covering edible plant parts and public names. Its Time after 9 a.m./Kings parent
is Entities and circumstances, explicitly covering scene times and people with
social titles. Such broad coverage can be defensible while remaining unhelpful.
Likewise, an input's related actor, product or name must not be declared excluded
without reading the complete proposed meaning.

The frozen source is:

```text
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr14-v3
```

Its `target/hierarchy-hr14-v3-fifty-note-v1/HR14/state.json` SHA256 is
`5496b3b1e339dd67cd995efa87d277582f9b1a48a27ac64af8ef0dca8ff66956`.
The viewed artifact is `target/hr14-review-ui-v2/hierarchy.json`; its provenance
and validation files identify the saved construction. All fifty source notes
report ASv6.100 provenance. No deprecated extraction data was used.

### Frozen native test

The [source reference](pair-consolidation-owl-v11-hr14-source-v1.json) points to
the original native `trial/batch-00001/experiment`, pinning its manifest SHA256.
The [spec](pair-consolidation-owl-v11-hr14-v1.spec.json) selects eight exact cases
through the production generic prepared-experiment adapter. All eight are root
pairs: their original inputs have no parent. No natural-language parent was
silently omitted or converted to unvalidated logic.

Before dispatch, the original and prepared inputs were checked byte-for-byte,
the compiled V11 prompt was checked against its assembly, and source bindings
were verified to use isolated worktrees. The planned assessment distinguishes
fixed-meaning fidelity, coverage of both translations, unchanged definitions,
English/formal agreement and browsing usefulness. Two coherent product/role
pairs are controls; six probe weak grouping or association/identity boundaries.
No output title or unique consolidated scope was prescribed. Agent assessments
remain outside model input and are not human gold.

All eight new requests used GPT-6.1 Sol medium through the shared native runner,
subscription provider and SSE. The original HR14 answers are saved baselines,
not rerun calls. HR14 used Hierarchy-pair-consolidation-v6, a title/meaning output
schema and cached-prefix configuration. V11 uses the richer formal output
without that old strict schema or cache configuration. Therefore this is a
real-input diagnostic, not a prompt-only causal comparison or matched
cost-savings trial.

### Results

All eight requests completed, with eight fresh attempts, zero reuses, failures
or retries. Raw receipts report HTTP 200, GPT-6.1 Sol and medium reasoning; each
has one user message, no prior-response reference and a distinct upstream
response ID. Native text validity is separate from the assessments below.

| Case | Exact input pair | V11 title | Agent assessment |
|---|---|---|---|
| F00000-P00039 | Pancakes / Pancake mixtures | Pancake foods and preparations | Qualified accept: product and formulated-mixture kinds remain distinct and covered. |
| F00000-P00066 | Raw meat / Meat eaters | Meat in diets | Uncertain: the raw-meat translation requires an eating activity; the final meaning says consumed. Whether this narrows the supplied food-use role remains unresolved. |
| F00000-P00070 | coffeechain / Caffeine | Coffeehouse-chain hashtags and central nervous system stimulants | Uncertain: both translated kinds are covered, but the heading lists disconnected kinds. |
| F00000-P00106 | Beets / MrBeast | Cultivated vegetables and YouTube creator names | Reject: final English adds a human-consumption condition absent from its logic. Grouping also remains disconnected. |
| F00000-P00119 | Satoshi Nakamoto / Nostr | Digital technologies and creator pseudonyms | Qualified accept: preserves pseudonym/creator and protocol identities; explicit broader alternatives cover both. |
| F00000-P00134 | Pressure canning / Extractor fans | Food and air treatment processes and equipment | Reject: FanDevice is both a formal class and an English glossary entry. This is an output-contract failure. |
| F00000-P00140 | Lamb / wolf.0313 | Food and drink resources | Qualified accept: food and the credited source retain their separate kinds and source/video relationship. |
| F00000-P00161 | Time after 9 a.m. / Kings | Scene times and monarchs | Uncertain: translations are covered, but the union remains an unhelpful browsing group. |

Mechanical field-order, expression formatting, vocabulary closure and reused
definition checks pass for seven outputs. The eighth has the duplicate
FanDevice definition described below. Manual reading establishes coverage of
the returned translations in all eight, using their final definitions; this is
not executable reasoner certification and does not establish input fidelity.

**Beets/MrBeast: added condition in English.** The consolidation's plant
alternative is:

```text
EdiblePlantPart AND (cultivatedFor SOME VegetableConsumption)
VegetableConsumption = Consumption AND (consumesAsVegetable SOME EdiblePlantPart)
```

These are excerpts of the expression and supporting class, not new prompt
syntax. Consumption is defined as eating; neither its expression nor the
relation definitions require a human participant. The final English instead
says edible plant parts cultivated "for people to eat as vegetables." The
original Beets meaning says cultivated for consumption as vegetables, without
the added people condition. The English therefore fails the unchanged formal
scope requirement. The separate public-name/YouTube-creator alternative is
represented explicitly, but still does not make this a useful common category.

**Pressure canning/extractor fans: duplicate definition.** The node translation
includes:

```json
{
  "node2.definitions.FanDevice": "A device with a fan that moves air.",
  "consolidated.owl.classes.FanDevice": "Device AND FanMechanismDevice"
}
```

This shows the two saved paths, not the response schema. V11 explicitly forbids
an English glossary entry for a class formally defined anywhere in the returned
objects. The definitions can otherwise warrant the device membership needed by
the consolidated expression. Do not misreport this duplication as proof that
semantic containment fails.

**Forced unrelated pairs remain weak groups.** Beets/MrBeast, scene times/kings
and coffeechain/caffeine become explicit unions instead of opaque umbrella
headings. This makes their memberships clearer but still supplies little shared
topic guidance. The prompt itself states that its formal conclusions establish
coverage and parent fit, not a unique topic or usefulness for browsing. These
results do not show that adding logic alone will repair HR14's final hierarchy.
They also do not prove every historical broad parent false. No selected pair
has a supplied parent, so deeper parent-fit failures remain untested here.

That HR14 screen identified the English-only human restriction and the
formal/glossary duplication as controls for subsequent prompt work. Both are
included in the V12 screen below. Browsing usefulness remains a separate
assessment. No prompt change or further inference was included in that HR14 task.

Native `experiment-usage-summary-v3` accounting is complete without warnings:
26,434 input tokens, 14,450 output tokens and 6,586 reasoning tokens already
included in output. Cache read/write counts are zero. Complete fresh catalogue
API-equivalent cost is **$0.197368**; this is not subscription billing or a
savings claim. Agent reviews are three qualified accepts, two rejects and three
uncertainties, with distinct reasons rather than a generalized accuracy score.

The task worktree is retained for frozen source/code bindings and native receipts:

```text
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-owl-v11-hr14-v1
```

Ignored evidence is `target/pair-consolidation-owl-v11-hr14-v1`,
`target/pair-consolidation-owl-v11-hr14-checks-v1.json`,
`target/pair-consolidation-owl-v11-hr14-usage-source-v1.json` and
`target/pair-consolidation-owl-v11-hr14-usage-summary-v1.json`. Original HR14
answers, construction state and reviews remain unchanged in their retained
source worktree.

## V12 specificity port and matched checks — 2026-10-13

The user authorized porting the normal pair-consolidation prompt's tested
specificity change into this OWL line and requested current prompting practices.
[Normal V7](Hierarchy-pair-consolidation-v7.md) had already retained Tomatoes
in both its root and supplied-parent controls. This task changes only the OWL
wrappers, publishes [OWL V12](pair-consolidation-owl-v12.md), and tests the same
nine saved HR14 root controls against unchanged V11.

The opening no longer requires a **new** parent. The selection paragraphs copy
V7's objective, identity/condition retention and useful-heading preference
verbatim. A final specificity check uses the already-defined OWL expressions:
choose a more specific coherent expression when it still covers both fixed
node expressions and fits the supplied parent; an expression may have the same
scope as an input. There is no equivalence mode, new output field or constructor
change. The checked assembly pins unchanged shared-rules-v6, Bootstrap-v129,
guide-v5 and example-v3. Historical prompt bytes remain unchanged.

The wording follows official guidance to use direct instructions, explicit
success criteria and clear delimiters without requesting a reasoning narrative.
[Reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively)
supports those practices; it does not certify this semantic objective. The
[current model-family guide](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices)
recommends evaluating its starting guidance on the chosen model/workload, and
[evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
supports task-specific cases, fixed criteria and checking variability. The
selected model remains GPT-6.1 Sol medium.

### Method and unchanged controls

The [V11 baseline spec](pair-consolidation-owl-v11-close-baseline-v1.spec.json)
selects nine exact ASv6.100-derived HR14 root inputs using the existing native
prepared-experiment adapter. The first V11 Tomato answer already retained
Tomatoes. Coffee and Dezeen then reproduced unnecessary scope loss before V12
was drafted: Coffee removed water and Dezeen lost publication identity from
both its translations and consolidation. These are the observed failing
controls, not an invented claim that OWL V11 had failed Tomatoes.

The [V12 source reference](pair-consolidation-owl-v12-close-source-v1.json) and
[close-pair spec](pair-consolidation-owl-v12-close-v1.spec.json) freeze those
same inputs. Criteria inherited from the normal V7 screen require retaining
named identities and defining conditions without excluding either complete
meaning. Cooking's different method scopes and Bread's product/activity kinds
prevent treating identical titles as automatic equivalence. The reviewed
Tomato interpretation is user evidence; the other assessments are agent checks,
not independent human gold. No exact output heading was prescribed.

The [regression source](pair-consolidation-owl-v12-regression-source-v1.json) and
[spec](pair-consolidation-owl-v12-regression-v1.spec.json) preserve the prior
completed-painting parent, never-painted wall/ceiling and coffee-equipment cases.
The [HR14 control spec](pair-consolidation-owl-v12-hr14-controls-v1.spec.json)
retains Beets/MrBeast and pressure canning/extractor fans. All three ready V12
batches were submitted before waiting; the shared runner owns scheduling.

After the first draw, native `prepare --from ... --only ... --repeat` selected
Tomatoes, Coffee, Breakfast, Bitcoin and Dezeen for five independent V12 draws.
Inputs, schema, reasoning, provider, transport and complete request bodies are
exactly preserved between each first draw and repeat. Distinct upstream response
IDs establish fresh calls rather than answer reuse. Each request has one user
message and no previous-response reference. All nine matched V11/V12 bodies
have identical non-input fields; only the configured prompt text changes.

### Matched root findings

| Pair | V11 observation | V12 observation |
|---|---|---|
| Tomatoes / Tomatoes | Already retains tomato-species fruit identity. | Retains the same broader supplied scope, without first-only Fleshy; repeat agrees. |
| Coffee / Coffee | Removes both extraction-with-water and water-based-extract conditions. | Retains those distinct water conditions as OR alternatives; repeat retains water, with a separate representation failure below. |
| Nostr / Nostr | Retains identity but relaxes receiving/retrieval and social-use conditions. | Retains identity, protocol/network kinds, signed-event publication/reception and shared social communication. |
| Cooking / Cooking | Covers heat-based and wider ingredient preparation through broad preparation/constituent-activity scope. | Covers both under Food preparation for eating; most-specific method scope remains uncertain. |
| Coffee shops / Coffee shops | Retains café-style business and principal coffee preparation/service. | Retains those conditions, with separate preparing/serving activity classes. |
| Breakfast / Breakfast | Admits any meal after main sleep, dropping the day-starting condition. | Retains actual eating-day beginning OR intended day beginning after main sleep; repeat agrees. |
| Bitcoin / Bitcoin | Generalizes to proof-of-work networks and currencies, losing BTC identity. | Retains BTC currency/network identity with appropriate alternatives; repeat agrees. |
| Dezeen / Dezeen | Becomes generic architecture/design original article sources; translations also omit Dezeen. | Retains Dezeen and original-publication credit role; repeat agrees. |
| Bread / Bread preparation | Retains products and preparation activities; production occurrence remains qualified. | Retains both kinds; one-versus-multiple-step activity and production occurrence remain qualified. |

The first V12 Coffee expression keeps water at the two different locations:
water used in extraction versus water forming the extract's base. It does not
require an implication between those locations merely to make the grouping fit.
The first Breakfast result similarly retains actual beginning and intended
beginning as alternatives, rather than replacing both with the broad sleep
condition. These are improvements in conditions and scope, not just narrower
titles.

Native agent reviews for the matched roots are V11: two qualified accepts, four
rejections under the approved specificity objective and three uncertainties;
V12: seven qualified accepts and two uncertainties. The four clear scope-loss
controls do not recur in this first V12 draw or their repeats. Nostr strengthens
its retained conditions, but its prior uncertain finding is not relabeled as
independent human error. One draw per matched case and one repeat of five cases
do not establish a reliability rate, a unique optimum or full hierarchy quality.
This tests the complete wrapper revision, not the causal effect of one sentence.

### Remaining formal failures and qualifications

**MrBeast content attribution is missing from the logic.** The old extra-human
condition in Beets does not recur. However, the MrBeast translation's `knownFor`
filler is merely Content hosted on YouTube. Its separate VideoCreator definition
connects Jimmy Donaldson to a video-creation output, without linking that output
or the known-for content to each other. The input and final English both say
**his YouTube content**. The formal representation therefore does not preserve
the stated association with Jimmy Donaldson. Do not turn this into an assumed
sole-authorship requirement; the actual stated attribution must be represented.
Copying both translated expressions into a union establishes coverage of those
translations, not faithful translation of the fixed input.

**The Coffee repeat hides roasting in an English-defined class.** Water remains
formal in both branches, but the repeat defines `RoastedCoffeeBeans` only as
"Coffee beans that have been roasted." Neither CoffeeBean nor Roasting has a
formal supporting definition exposing the stated roasting condition/activity.
V12 says a class may abbreviate stated conditions only through `owl.classes`.
This is a representation-rule failure; it is not recurrence of the missing-water
failure. The first V12 Coffee draw had formally represented the roasting state.

Three other findings remain uncertain: Cooking's broad preparation scope, the
Bread translation's single-step versus one-or-more-step activity scope and
possible completed-product requirement, and the very broad Material treatment
processes and equipment consolidation. The latter fixes the specific duplicate
FanDevice glossary problem but does not establish useful specificity. The
literal Beets/MrBeast union is also weak for browsing; no synthetic shared
relationship was invented to conceal that limitation.

The three established OWL controls receive qualified accepts: completion and
home-surface conditions fit the unchanged painting parent; negated paint
application retains its activity, paint participant and history scope; cup
drinking and shelf storage retain their separate purpose/actual-use conditions.
Only the painting fixture supplies an OWL parent. No natural-language HR14 parent
was silently removed or converted, and actual HR14 parent-fit cases remain
untested in this screen.

Across all nineteen V12 answers, native reviews are fourteen qualified accepts,
two representation rejections and three uncertainties. Mechanical field order,
expression format, vocabulary closure and definition-consistency checks pass for
all twenty-eight receipts, including the nine V11 answers. These checks do not
certify fidelity or execute an OWL reasoner. All reviews are attributed separately
from user decisions and model input.

The next useful OWL work is a focused test of named-entity attribution and prior
activity/state representation before another prompt revision. Keep the observed
specificity gains as regression controls; a successful narrow heading must not
conceal missing conditions in the logic. No V13, hierarchy activation or further
inference is included here.

### Accounting and retained evidence

Native accounting reports **28 fresh attempts**: nine V11 baseline answers,
fourteen first-draw V12 answers and five independent V12 repeats. There are no
warmups, answer reuses, failures, retries, invalid receipts or missing usages.
The historical control baselines were read without rerunning them. Native
`experiment-usage-summary-v3` totals are 79,103 uncached input tokens, 15,616
cached input tokens, zero cache-write tokens and 49,732 output tokens; 18,475
reasoning tokens are already included in output. Complete catalogue
API-equivalent cost is **$0.6570876**, not subscription billing or a savings claim.

Retained worktrees preserve frozen inputs, source/code bindings and receipts:

```text
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-owl-v11-close-baseline-v1
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-owl-v12-specificity-v1
```

The first retains `target/pair-consolidation-owl-v11-close-baseline-v1`. The second
retains `target/pair-consolidation-owl-v12-{close,regression,hr14-controls,close-repeat}-v1`,
native agent reviews, `target/pair-consolidation-owl-v12-specificity-checks-v1.json`,
and `target/pair-consolidation-owl-v12-usage-{source,summary}-v1.json`. These ignored
artifacts remain separate from the reusable prompt/assembly/spec definitions and
maintained findings. Earlier retained worktrees supply unchanged historical
baselines; their receipts and source inputs are preserved.
