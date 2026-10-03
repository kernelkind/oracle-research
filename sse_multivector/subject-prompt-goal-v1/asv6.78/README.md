# ASv6.78 shared-predicate example comparison

Status: tested, confirmed failures; not adopted. All three completed ASv6.76 N100 answers still
omit the full counted joint trimming subject. The partial trimming actions
elsewhere do not retain that expressed combination. The saved native answers
are the production-path failing behavior for this intervention.

[ASv6.78](ASv6.78.md) changes only C1 of ASv6.76. Its action becomes
“Cutting it and them” instead of “Mixing it with them.” The shared predicate
expresses cutting the counted tissue piece, cutting the two scraps and cutting
both together. The output keeps those partial actions and the complete joint
action, including the ingredient roles supplied by the enclosing heading.
The explanation identifies valid directions between complete and partial
subjects. The separate recipient-only tissue and food-seasoning salt still
demonstrate the previously fixed scope distinctions.

This adds a demonstration of the existing multiple-parts rule, not another
rule, example, model pass or output field. C1 retains its established primary
assignments in the [34-clause map](../autonomous-sp-v1/README.md); R17 additionally
tracks the shared-predicate aspect here, distinct from C2's nonliteral and
rhetorical meanings. R18 retains expressed combinations and R19 retains the
participants alongside events. The other six examples, all instructions,
all five tracked implications and the ordinary POST template remain intact.
ASv6.77's task-framing change is excluded to isolate this example intervention.

The minimal new offline check first failed on ASv6.76 because C1 did not
demonstrate the partial cutting action. After the replacement, 61 checks pass.
The production subjects adapter parses the example; an independently reviewed
21-edge meaning graph checks all 17 headings, all 54 explicitly authored
numbered occurrences, source placement below every compatible parent copy,
invalid reverse directions and food roles. The displayed tree is not generated
from the test graph. These checks audit example consistency, not model quality.

## Fixed screen before generation

Repeat the same eight minimized development posts and four full originals in
three medium trials: S002/S004/S006/D004/D005/D006/D007/D008 and
N063/N074/N096/N100. Native preparation inherits complete same-trial ASv6.76
inputs, evidence, settings and saved outputs. Keep the frozen scope-minimization
and bounded original-post criteria. Review source retention, heading-only
scope/direction and every returned compatible numbered source parent.
Equivalent wording counts; optional tree shapes and recorded semantic
uncertainties are excluded from confirmed failures. Review all 36 answers,
without stopping on a desirable result or rerunning a quality failure.

Use subscription `gpt-6.1-sol` medium, WebSocket, 1,800-second timeout and no
output cap or paid fallback. Each native runner has concurrency one, with at
most six active overall. Preserve native receipts and persistent history; all
attempts count against the existing 2,000 ceiling. After ASv6.77 reaches 748,
first-attempt completion of this screen reaches 784. Only explicitly transient
provider failures may be retried once; unknown failures are not retryable.
Commit the source, template, checks and frozen plan before generation.
Production SP remains one call per post; no candidate is adopted.

## Completed comparison

All 36 first attempts completed with valid native receipts, without request
failures, retries or reuse. All have output-bound native agent reviews: 23 accept, 12 reject and one uncertain
on the frozen bounded checks. These are agent judgments, not independent human
gold or overall SP certification. The persistent counter reached 784.

| Case | Trial 1 | Trial 2 | Trial 3 |
| --- | --- | --- | --- |
| S002 | accept | accept | accept |
| S004 | accept | accept | accept |
| S006 | accept | accept | reject |
| D004 | accept | accept | accept |
| D005 | accept | accept | accept |
| D006 | accept | accept | reject |
| D007 | reject | accept | accept |
| D008 | accept | accept | accept |
| N063 | accept | accept | uncertain |
| N074 | reject | reject | accept |
| N096 | reject | reject | reject |
| N100 | reject | reject | reject |

The changed example does not fix full-post joint-action retention: all N100 answers omit the complete quantified trim. S006 trial 3 loses recipe association; D006 trial 3 returns only five rows, omitting separate material participants and other source clauses despite valid JSON. D007 trial 1 omits the complete trim. N063 trial 3 preserves all fifteen qualified ingredients but uses only the ingredient-role group; the frozen alternative-group exclusion makes this uncertain. N074 trials 1/2 lose attributed advice or its compatible component placements. N096 trials 1/2 put generic olive oil under Food; trial 3 loses the oil amount in partial sautéing. D008 returns no Dog food heading in any trial, so its acceptance does not demonstrate correction of that edge.

Optional classifications and the unresolved chicken/myoglobin reference remain
excluded. Source presence alone is not placement success. Native receipts and
reviews are in `sse_multivector/experiments/sp-autonomous-v1/as78-*`.
