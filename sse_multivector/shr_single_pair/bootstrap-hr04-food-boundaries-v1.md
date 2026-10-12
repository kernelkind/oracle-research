# HR04 C003/C004 Bootstrap boundary diagnostic

The user approved investigating whether HR04's two Food roots deliberately
define different categories or whether their wording creates different
interpretations. This diagnostic preserves Bootstrap-v109, all historical
outputs and HR04's graph. It adds no Compare labels, prompt edits, hierarchy
generation or UI changes. The two meanings are independently generated; a
matching subject does not establish equivalence.

## Reusable inputs and provenance

[Input selection](hierarchy-bootstrap-hr04-food-boundaries-v1.json) uses the
native `hierarchy_local_nodes` adapter with local schema 4. It selects:

| HR04 node | Original note | Selected root | Complete root-tree entries |
|---|---|---|---:|
| C003 | N063, shrimp risotto | Food, `1` | 34 |
| C004 | N037, cranberry sourdough | Food, `1` | 24 |

The exact note IDs are in the source. Its corpus is HR04's retained
`subjects.json`, SHA-256
`18370b4772fee22c8d11f49a505f20f781f163e0512a8f32473d487ebdc8849a`.
Both posts, complete trees and original AS receipts were verified against
ASv6.100, template SHA-256
`0e3fdfb713128233ba65070c0092914a38b0059a2eb5e873c0d828add1c5d52f`.
No deprecated subject input or generated ancestor meaning enters the requests.

The [frozen test specification](hierarchy-bootstrap-v109-hr04-food-boundaries-v1.spec.json)
uses unchanged Bootstrap-v109, GPT-6.1 Sol medium, SSE, automatic prefix caching
and the main shared worker. The native adapter's exact `INPUT_JSON` strings,
rendered prompts, schemas and actual provider bodies match each original HR04
producer. The worker path changes from HR04's retained runner checkout to the
main runner, but the payload-relevant runner and request-code hashes match.

The original producers are case `meaning` under:

`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr04-twelve-note-v1/target/hierarchy-hr04-twelve-note-v1/trial/`

| Node | Experiment | Record SHA-256 |
|---|---|---|
| C003 | `batch-00002/experiment` | `b83db6d8faa50fd31a39ce33193aa7aed2dc15259915e50ee3c45ef23d4915c1` |
| C004 | `batch-00003/experiment` | `e8588abf3774dc011e9d566a5d90c0fb0e46eff3febdcf8a3b347a3a6e649547` |

## Historical distinction

C003 resolves Food as human consumption for nourishment or as components of
something eaten or drunk. Its second resolution specifically admits
ingredients intended to be incorporated into food, including seasonings and
liquid ingredients. The final wording says "components of something eaten or
drunk," leaving whether those components themselves qualify as culinary food
less explicit. It does not deliberately choose to include inedible poisons.

C004 resolves Food as edible substances intended for human consumption and
includes edible ingredients consumed as prepared-food components. It does not
require a nourishment purpose. That broad purpose choice is not automatically
a producer error under the user's evidence-consistent-boundary policy.

The historical comparison in `batch-00010/experiment`, case `C003`, returned
neither. It admits a lethal, non-edible chemical intended as a poisoned-drink
component under C003, and ceremonial edible gold consumed alone under C004.
The user subsequently accepted the poison witness as exposing insufficient
closure of the exact C003 meaning. Their judgment, verbatim, on October 12,
2026 UTC:

> while i hate to say it, i think the couterexample is doing it's job. the explicit meaning must be air-tight. and i don't think this one was

This settles the disputed poison admission under the stated component clause;
Compare should not supply an unstated condition merely to exclude that witness.
It does not establish that the producer deliberately wanted poisoned components
in its Food category. The ceremonial-gold witness and the whole C003/C004
relation remain unreviewed by the user. This partial judgment is bound to the
exact old meaning, not transferred to fresh definitions or other poison cases.
Do not silently add missing conditions or retroactively repair fixed meanings.

## Retained meaning-quality regression

The [versioned input selection](hierarchy-bootstrap-hr04-food-boundaries-v2.json)
retains both original inputs and adds the exact C003 meaning, accepted poison
witness, producer/comparison receipt references and verbatim user judgment to
C003's review evidence. The [ASv6.100 regression collection v4](hierarchy-bootstrap-asv6.100-regressions-v4.json)
includes that selection. The earlier selection and collection remain unchanged
for frozen experiments.

This is a review regression for whether each fresh meaning expresses its chosen
membership conditions clearly and consistently. The old meaning is not an
expected output; neither poison exclusion nor C003/C004 equivalence is a required
fresh label. Review the exact new wording before deciding which examples fit it.
The accepted old admission must not be repaired inside Compare.

Native preparation keeps the post and complete selected-root tree in Bootstrap
input. The historical meaning, witness, judgment and review questions remain
outside the rendered prompt, in `evidence.review`; collection preparation
retains node-specific evidence under `historical_witnesses`. Receipt references
inside review metadata are descriptive, not automatic receipt validation; the
two original native receipts were inspected separately.

The [unchanged-v109 preparation specification](hierarchy-bootstrap-v109-asv6.100-regressions-v4.spec.json)
supports an offline input/isolation check. It does not select a new Bootstrap
candidate or authorize inference. No Bootstrap prompt or historical artifact
is changed by retaining this regression.

Offline native preparation in the Compare task worktree's
`target/bootstrap-hr04-poison-regression-retention-v1` validated all 346 collection
inputs, including the exact C003/C004 original input hashes and 34/24-entry trees.
The accepted C003 witness survives collection preparation outside the model
input and prompt. Three existing production-path checks passed for schema-4
inputs, review isolation and collection deduplication. All cases remain unrun;
no model calls were made for this retention. Older relative corpus bindings
resolve in the retained Bootstrap task worktree; their definition bytes match
the committed project copies.

## Fresh unchanged-prompt draws

Three native `--repeat` experiments each generated the same two entries from
their original full posts and trees. No old meaning, comparison answer,
counterexample, review criterion or relationship expectation enters model input.
Two independent semantic reviewers examined the six definitions; a separate
integrity reviewer checked original and fresh receipts and actual requests.

| Observation | Fresh risotto draws | Fresh sourdough draws |
|---|---:|---:|
| Human-consumption sense | 3/3 | 3/3 |
| Prepared foods and ingredient kinds admitted | 3/3 | 3/3 |
| Old C003 nourishment-or-component condition | 0/3 | 0/3 |
| Definite evidence contradiction established | 0 | 0 |

All six maintain broad categories with non-exhaustive examples. Risotto instead
uses "culinary category," "culinary ingredients," or an ingredient-in-a-dish
role. Sourdough retains edible food/ingredient scope. These shared features are
not an equivalence certification. Three draws are a bounded diagnostic, not a
reliability estimate, and fresh wording cannot repair or score old fixed strings.

Two residual expression concerns remain: risotto draw 3 makes ingredient
edibility explicit in its resolution but not in the final wording; sourdough
draw 2 partly uses the circular phrase "human consumption as food." Drinking
and edibility appear in different places across draws. An omitted word alone
does not establish deliberate exclusion or permission for a different sense.
No fresh output explicitly admits inedible components, but the outputs do not
directly adjudicate poisoning or ceremonial ingestion either.

The retained review questions are:

- Does each admitted kind preserve the chosen Food identity, or does a generic
  description accidentally admit all ingestible material?
- Is nourishment required, or can a culinary ingredient independently qualify
  through its component role?
- Are chosen edibility, consumer and ingredient-role conditions expressed
  consistently in both resolutions and the standalone meaning?
- Do examples illustrate those conditions or introduce another admitted kind?

## Native execution and accounting

Artifacts remain in the retained `oracle-mvp-shr-pair-correctness-v1` worktree:
`target/bootstrap-v109-hr04-food-boundaries-v1/draw1`, `draw2` and `draw3`.
Their cases are `hr04-food-risotto` and `hr04-food-sourdough`. Native `show`
exports are `draw1-native.json` through `draw3-native.json`; exact outputs and
receipt hashes remain there rather than being spliced into a preferred meaning.

All six final receipts and three automatic warmups validate; evidence quotes
occur verbatim in the supplied posts. Nine fresh attempts include six valid
definitions and three warmups, with zero reuses, failures or retries. All six
definition requests report cache hits. The existing attempt counter moved from
19,368 to 19,377 without reset.

[Native accounting](hierarchy-bootstrap-v109-hr04-food-boundaries-usage-v1.json)
records historical generation separately from this task's three fresh draws.
`usage-native-v1.json` reports a fresh API-equivalent total of $0.0477292,
including warmups; usage is complete. These are catalog estimates rather than
subscription charges, and reasoning is already included in output.

Exact source/input/request/receipt checks, native accounting, JSON validation
and documentation diff checks passed. No implementation behavior changed.

## Finding and next proposal

No source poisoning or mixed prompt inputs were found. The old C003 condition
did not recur in three identical-input draws; this does not establish a stable
category distinction caused by the source note. The producer issue is whether
final definitions faithfully carry each chosen kind's conditions. The user's
accepted poison witness now establishes a scope-closure gap in the old C003
wording; excluding it by repairing that wording inside Compare is not the
desired response. Other kind-interpretation questions, heading equivalence
and the complete historical neither label remain open.

The next proposed Bootstrap work is a small draft clarifying preservation of
the chosen kind and its conditions when writing the final meaning. It should
target that general mechanism, not add Food-specific exceptions or force these
two roots to merge. No prompt change or further inference is authorized by this
record itself.
