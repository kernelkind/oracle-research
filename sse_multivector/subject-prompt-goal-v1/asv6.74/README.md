# ASv6.74 C1 revision and fixed comparison

Status: candidate, offline checks passed; model comparison authorized, not yet
run. The user approved the C1 revision and comparison on 2026-10-02. ASv6.73
is the fixed comparison baseline. Frozen production SP remains ASv6.48;
MP and adoption are outside this task.

[ASv6.74](ASv6.74.md) changes only C1's complete example. All instruction bytes,
the other six complete examples and the output schema remain unchanged. Native
`experiment.py revise` assembled both the source and ordinary POST template,
with their revision receipts. This candidate introduces no additional rule.

## Example correctness and coverage

C1 now supplies a counted steel plate and two steel bolts for chair repair,
then refers to them in attachment to the chair. Separate steel-plate, steel-bolt
and chair topics remain alongside the action. The expressed repair-material
group appears beneath all three qualified plate copies and all three qualified
bolt copies. Its complete attachment appears beneath all six group copies,
all three repair-qualified attachment headings and the counted attachment
heading: ten copies in total. Descendants provide coverage without an additional
direct duplicate beside their containing branch.

Every displayed edge was reviewed using its headings alone. The complete action
states the same counted materials, attachment and chair-repair purpose; no
parent supplies a missing restriction. Generic counted materials and the
unqualified attachment remain outside Chair repair: the same materials and
attachment could be used to build furniture instead. Each context identifies
source support, including the list heading and resolved references. No drilling,
extra tools or calculated total is invented. Source participants, individual
counted materials, their expressed group and their action are all retained.

C1 has 35 entries and fourteen distinct headings, replacing sixteen entries
and eight headings. The complete source grows from 18,196 to 21,533 UTF-8 bytes,
an additional 3,337 bytes of fixed input per post. SP still makes one model
call per post; the hierarchy's repeated branches remain part of the existing
contract. This revision adds no production component or model pass.

The primary clause assignments stay those in the maintained
[34-clause map](../autonomous-sp-v1/README.md#rule-coverage-for-asv661).
C1 demonstrates its sixteen primary clauses as follows:

| Clauses | Demonstration |
| --- | --- |
| R01, R02, R04 | Understand the heading/list/action together; resolve `it` to one steel plate and `them` to two steel bolts with supported repair purpose. |
| R16 | The counted repair materials, expressed group and complete action remain beneath broader headings; no internal reasoning trace is added. |
| R20, R29 | Generic material and attachment headings retain their generality; their source context cannot place them beneath Chair repair. |
| R21, R22 | Shared qualified material, group and action subjects fill every compatible numbered parent occurrence. |
| R23, R25, R26 | Each entry has its own broad-to-specific section number, parents first, with fields ordered number/context/subject. |
| R27, R28 | Contexts name source support and may describe this repair instance for a general material topic. |
| R30, R31, R34 | Concise, standalone headings resolve references and retain their own restrictions without repeating the whole assertion at every level. |

R18's existing secondary demonstration now includes the two-material group;
R24 still contrasts nonempty C1 with empty C3. C1 additionally demonstrates
R19's participant retention, whose primary case stays C5. The five tracked
implications retain their original rule assignments. C2–C7 retain their
ASv6.73 mappings and earlier audit findings: C2's help/appreciation combination
remains unresolved. Do not claim that all seven examples have independent
semantic certification.

The participant test first failed against ASv6.73 for its missing Soup subject.
It now checks the replacement participants; another test preserves that old
failure as evidence. Production subjects validation precedes every example
check. The tests inspect every source-subject placement and displayed edge
against the reviewed semantic relationships, prohibited purpose/group edges,
field order, unchanged instructions and six unchanged examples. All forty
example/attempt-budget tests passed. These fixtures encode agent judgments;
they do not independently prove meaning or model generalization.

## Pre-generation comparison

Freeze ASv6.74 for all fifty-six planned candidate answers, without revising it
or stopping early based on quality:

- Twelve [interaction posts](../autonomous-sp-v1/interaction-cases.json),
  three independent medium trials each: thirty-six new answers, paired with
  all three saved ASv6.73 interaction trials.
- Original complete N063, N074, N096 and N100 posts, five independent medium
  trials each: twenty new answers, paired with all five saved fixed ASv6.73
  original-post trials. No baseline is rerun or selected by its quality.

Use native `prepare --from`, the ASv6.74 POST template and `--repeat`. Preserve
each corresponding baseline's exact source posts, evidence and runner settings:
subscription `openai-codex`, `gpt-6.1-sol`, medium, WebSocket, 1,800-second
timeout, no output-token cap or paid fallback. Interaction concurrency is
twelve; original-post concurrency is four. Each native run owns its scheduling.

Reuse the criteria committed before the ASv6.73 runs:
[interaction criteria](../autonomous-sp-v1/interaction-audit-v1.md#pre-generation-criteria)
and [original-post criteria](../autonomous-sp-v1/README.md#fixed-repeated-comparison-asv658-versus-asv673).
Inspect every numbered occurrence, not just distinct heading pairs. Retain
uncertain ingredient-group memberships and the open derived-heading-placement
boundary. Missing food/feeding parents do not count as successful edge tests.
Record each candidate's current output-bound native agent review separately
from user labels. Bounded acceptance is not a full-SP gold pass. Report scope,
source coverage, placement witnesses and exposure separately, including new
regressions. The repair diagnostic shares material/action structure with C1,
so it is development evidence; soup and original-post comparisons test transfer
within this already-used set, not unseen generalization.

The existing persistent attempt budget starts at 246 of 1,000 and is never
reset. Every run names `target/sp-autonomous-v1/attempt-budget.json`. Bound each
twelve-case run to twenty-four attempts and each four-case run to eight,
including any eligible provider retries. Native provider-only retry policy
permits at most two attempts per case; failures remain visible. If every answer
succeeds on its first attempt, the budget will reach 302. Subscription
incremental cash is zero, quota use is unmeasured and catalog estimates are
not bills. The lifetime ledger was inspected before launch; no paid commitment
is introduced.

Native directories are `as74-interactions-medium-r1` through `r3` and
`as74-original-medium-r1` through `r5`, under the ignored campaign experiment
root. Preserve all reports/receipts/reviews and verify exact frozen prompts,
inputs, settings, fresh-attempt counts and review bindings after completion.
No candidate is adopted by this experiment.
