# ASv6.50

Status: draft, untested. The user authorized preparing this replacement for
review; its wording and inference have not been approved. This supersedes the
ASv6.49 draft. ASv6.48 remains the frozen subject baseline. MPv3.43 remains the
frozen mask working baseline.

[ASv6.50.md](ASv6.50.md) replaces the existing hierarchy paragraph in
[ASv6.48](../asv6.48/ASv6.48.md). It makes the relationship explicit using the
`subject` headings: every post about the child subject must also be about the
parent. The existing requirements to retain every enumerated subject, combine
shared headings and include a subject in each applicable branch remain.

ASv6.48 already required refinement, broad-to-specific ordering and independently
understandable headings. ASv6.49 added a paragraph that substantially repeated
those instructions. ASv6.50 clarifies the existing paragraph without adding
another rule paragraph. All other instructions and both worked examples remain
byte-identical to ASv6.48.

The shared `experiment.py revise` command generated the draft and revision
receipt directly against ASv6.48 SHA-256
`e1d5740e68b5f5c29e139ad3fbb37839f91784784aaa31b3bdbdc4a829a4bacc`.
The draft SHA-256 is
`2ab157eb34f49edd2a443799c439be8eff512fe61df96f6d508434f4d3807a1c`.
No model calls were made while preparing this draft. Mechanical checks do not
establish semantic improvement.

The [agreed regression set](../asv6.49/README.md#agreed-regression-set) remains
N063, N074, N096 and N100, using complete original posts and saved ASv6.48
outputs. The proposed next comparison remains three independent candidate
outputs per post, reviewing complete hierarchies for preserved coverage and
new errors. It has not been started or authorized.

## Frozen-baseline reproduction on GPT-6.1 Sol xhigh

On October 1, 2026, the user authorized testing unchanged, frozen ASv6.48 on
the four regression posts with GPT-6.1 Sol xhigh before testing this draft.
The [reusable experiment spec](../../experiment_specs/sol61-xhigh-sp-scope-regression-v1.json)
uses the shared `subjects` adapter and the complete original posts. Each
rendered prompt's SHA-256 matches its original Astra-low request. The run used
the subscription WebSocket route, four concurrent requests, a 1,800-second
deadline, no output cap, no paid fallback and `--repeat` to prevent request reuse.

Four requests were sent, with three mechanically valid hierarchies and one
provider failure. No retries, request reuse or baseline regeneration occurred.
This was a reproduction run, not a prompt A/B comparison; native cases have no
paired baseline. The agent assessed complete outputs against the original posts
and the saved Astra hierarchies, using headings to judge parent relationships.

| Post | Original branch failure | Complete-output finding |
| --- | --- | --- |
| N063 | Unavailable | The provider returned `server_is_overloaded` / `service_unavailable_error` without an answer. The runner classified it as `unknown`, so it was not retried. This gives no subject-quality evidence. |
| N074 | Reproduced | 9.1.2, Michael Pollan's combined real-food/moderation/mostly-plants advice, has single-part children at 9.1.2.1–9.1.2.3. Each drops the other restrictions. The separate general-advice branch correctly makes the individual recommendations siblings of the combination. |
| N096 | Not reproduced in its original form | The general cooking steps sit under general techniques. The same pattern appears at 3.3.1.1, sautéing finely chopped onion, celery and carrot in olive oil, → 3.3.1.1.2, adding garlic after sautéing those vegetables. The child drops olive oil and finely chopped. |
| N100 | Not reproduced in its original form | 3.3's byproduct-use children describe uses, with general materials preserved elsewhere. The same pattern appears at 7.1.2.1, providing chickens with cold water and sunflower seeds tomorrow, → separate water-only and seeds-only children. The combination also splits under 9.1. |

The completed outputs retain the original useful subjects and details: N074's
individual and combined recommendations, comparisons, controversy, parent/child
example and attribution; N096's ingredients, quantities, recipe/yield, preparation
steps, simmering heat/duration and packet instructions; N100's purchase, cutting,
trimming, materials and intended uses, chicken provisions, and sealer details.
Coverage is an agent assessment, not proof of exhaustive extraction. N100 also
leaves separate grounding uncertainties: interpreting the duplicated "some some"
as myoglobin for chickens, and inferring that the steaks were the vacuum-sealed
object. Neither uncertainty is needed to establish its conjunction failure.

The same parent-scope failure pattern appears in all three completed outputs.
One output per post demonstrates recurrence, not a failure rate or general
model comparison. Native receipts, complete answers and four agent reviews
remain in ignored `sse_multivector/experiments/sol61-xhigh-sp-scope-regression-v1/`.
There are no new user verdicts. ASv6.50 remains untested and unapproved; the
recommended next step is testing it against these saved Sol outputs without
rerunning completed ASv6.48 cases.
