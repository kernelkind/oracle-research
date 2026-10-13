# Pair-consolidation-owl: experimental prompt line

`pair-consolidation-owl-v7` is the current experimental draft. The user approved
making the alternative instruction explicit: every stated alternative must use
`OR`, directly in `owl.expression` or in a supporting `owl.classes` definition.
Its two-order consumer check passes the targeted formal conditions. The broader
twelve-case panel is also complete and exposes one remaining representation
failure: `CoffeeDrinking` leaves the drinking action and required coffee object
only in an English glossary. V7 remains experimental and is not activated in
hierarchy construction. These are agent assessments, not human semantic gold.

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
  conditions when its formal definition exposes them.
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

The [v7 draft](pair-consolidation-owl-v7.md) is built by its
[pinned assembly manifest](pair-consolidation-owl-v7.assembly.json). It includes
[OWL-like guide v5](prompt_parts/owl-reasoning-guide-v5.md) and
[explicit-meaning rules v6](prompt_parts/explicit-meaning-rules-v6.md)
byte-for-byte. Its matching definition-writing reference is
[Bootstrap-v129](Hierarchy-bootstrap-v129.md).

V7 retains the [v6 prompt](pair-consolidation-owl-v6.md)'s one
[complete input/output example](prompt_parts/pair-consolidation-owl-example-v3.md)
using the same display-panel case, with each entry expression separated from
its supporting classes. The guide distinguishes exact class definitions from
one-way containment checks; required membership implications are expressed in
the formal definitions. It does not encode a containment claim as an exact
equivalence. The shared meaning-writing rules and consolidated natural-language
meaning are unchanged. The only compiled-prompt change from v6 is the approved
explicit-`OR` sentence in the node-translation instructions. All earlier published
prompt and guide files retain their original bytes.

The notation is the simplified OWL-like notation described in the guide. The
model supplies formal definitions, not an executable OWL document or a
mechanically verified proof. There is no parser, reasoner, constructor change,
experiment adapter or activated configuration in this task.

Only two input nodes and an optional parent are supplied per call. The shared
guide adds fixed input text; formal definitions and their English definitions
add output tokens. No call reduction, token saving or correctness gain has yet
been measured against another prompt. The pilot used sixteen fresh calls with
complete saved API-equivalent cost of $0.216726; it did not generate a hierarchy.

## Offline checks

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 sse_multivector/prompt_assembly.py check \
  sse_multivector/shr_single_pair/pair-consolidation-owl-v7.assembly.json
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

The recommended next revision should clarify the boundary for basic terms:
decompose the action and required objects, participants, purposes and states
explicitly specified in a supplied meaning; allow a name to abbreviate that
expression through `owl.classes`. Primitive English definitions can explain
concepts whose internal structure the supplied meaning does not specify. This
avoids requiring recursive technical definitions of every mentioned concept.
No next prompt version, extra inference or hierarchy change is part of this panel.

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
