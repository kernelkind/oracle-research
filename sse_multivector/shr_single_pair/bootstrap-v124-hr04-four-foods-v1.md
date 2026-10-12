# Bootstrap-v124: ambiguities introduced by a proposed definition

## Controlled change and status

Experimental [Bootstrap-v124](Hierarchy-bootstrap-v124.md) changes two phrases
in tested v123: the opening of `Identify category ambiguities` and the output
description of an ambiguity question. Both previously limited questions to
boundaries suggested by the input. The replacement also permits consequential
choices introduced by the proposed definition. The chosen interpretation must
still be supported by the subject and evidence; a category choice cannot settle
an unknown fact about a particular example.

The [native edits](hierarchy-bootstrap-v124-proposed-boundaries.edits.json) and
[revision receipt](Hierarchy-bootstrap-v124.md.revision.json) bind the change.
All other prompt bytes, both examples and the output schema are unchanged.
V124 SHA256 is `64d6d2d9230e30015388d75a3ea938be4285a6d4f18e6d448f7b4834112b312f`.
Two independent read-only reviewers found the source-only framing in tension
with v123's requirement to examine every proposed condition. This is a wording
hypothesis, not an established model mechanism or semantic approval.

The completed test establishes no systematic improvement. V124 remains
experimental and is not recommended for activation from these results.

## Exact inputs and execution

`target/bootstrap-v124-hr04-four-foods-v1/draw1` inherits all four exact inputs
from [v123's first draw](bootstrap-v123-hr04-four-foods-v1.md), with a fresh
prompt-specific request and intentional independent execution. The original
HR04 ASv6.100 posts, contexts and complete selected-root trees are byte-identical.
Only the rendered prompt and its derived prefix-cache identity differ in the
model request. Saved answers and Compare witness hypotheses remain outside
generation input. Matching Food headings do not supply semantic gold.

`target/bootstrap-v124-hr04-four-foods-v1/repeat` independently regenerates
risotto and brisket with identical v124 inputs, prompt and settings. It does
not replace the first outputs. Both cohorts use GPT-6.1 Sol medium, the main
shared runner, automatic execution concurrency and prefix warming. No obsolete
attempt counter, new attempt cap, paid fallback, Compare call, hierarchy build
or UI refresh is used.

All six definitions are valid, nonnull and fresh. Native accounting reports
eight attempts including two warmups, no retries, failures or answer reuses,
and complete usage. The [native usage source](hierarchy-bootstrap-v124-hr04-four-foods-usage-v1.json)
produces `target/bootstrap-v124-hr04-four-foods-v1/usage-native-v1.json`:
incremental API-equivalent cost is **$0.0979948**. This is not a reported
subscription cash charge. Caching was enabled throughout, but only the two
repeat definitions report cache hits; all four first-draw definitions report
zero cached input. Local prefix eligibility does not guarantee backend hits.

## Review of the exact meanings

Assessments below use the actual hypotheses preserved in the
[Compare witness reassessment](bootstrap-v122-hr04-four-foods-v1.md#compare-counterexamples-reassessment-of-the-exact-fresh-meanings).
They do not apply old labels to new definitions or require a universal Food
consumer/purpose boundary. Clinical or animal-feed admission alone is not
certified failure.

| First-draw case | Final defining condition | Assessment |
|---|---|---|
| Risotto | Material intended for human consumption by eating or drinking; later includes dishes and edible ingredients | Reject: the broad opening again admits the explicitly non-edible poison component intended for a human-drunk poisoned drink. The later edible-ingredient subset does not make edibility universal. |
| Sourdough | Substances intended for human eating; includes prepared foods and edible preparation/flavoring ingredients | Qualified accept: the explicitly eaten clinical wafer fits. Drinking-only hypotheses are not definitely admitted, and ceremonial swallowing remains conditional. No human-drinking or culinary-only condition is supplied silently. |
| Pie | Edible material intended for human consumption as nourishment, including dishes and ingredients | Qualified accept: the stated conditions exclude the specified non-edible, sole-medical, sole-ceremonial, animal-only and unintended-amoeba hypotheses. No lost original ingredient is demonstrated. |
| Brisket | Substances suitable and intended to be eaten or drunk for nourishment | Qualified accept: suitable animal feed is admitted, with no human condition imposed. Sole-medical/ceremonial purposes and the unintended amoeba episode fail stated conditions. |

Risotto's first head also admits the sole-diagnostic drink, the explicitly edible
clinical wafer and medicinal mineral oil. Edibility cannot exclude them because
it is absent from that head. Gold remains conditional on whether its ceremonial
swallowing is consumption by eating/drinking. These are consequences of the
exact string, not requirements that every Food meaning exclude every witness.

The fresh risotto repeat instead begins:

> Food is edible material intended for human consumption

That shared condition excludes the saved non-edible poison. The edible clinical
wafer and ceremonial edible gold still fit its unrestricted human-consumption
condition. Diagnostic drinks and medicinal oil now require edibility, which
their saved hypotheses do not establish. A later culinary list cannot supply a
missing purpose condition. The repeat receives a qualified accept, not a repair
to the rejected first draw.

Brisket's repeat retains intended eating/drinking for nourishment and omits
`suitable`. This is a different generated boundary, not an inconsistent reading
of an unchanged fixed meaning. It still admits animal feed and excludes the
specified sole-medical/ceremonial purposes and unintended amoeba episode. No
material consequence of removing suitability is established by those exact
witnesses. It receives a qualified accept.

All actual food-post examples fit; no false particular fact or concrete loss of
a named ingredient is established. This does not excuse the first risotto
definition's qualifying-kind gap. Independent reviewers agree on the stated
qualifications. Native agent reviews preserve one rejection and five qualified
accepts; these are not user judgments or a general accuracy estimate.

## Diagnostic finding and next hypothesis

Across all six answers, questions still concern broad category versus illustrated
example, ingredient inclusion or equipment. Consumer, edibility, suitability
and nourishment choices enter the resolutions/final meanings without direct
contrasting questions about their material alternatives. Sourdough's
justification expressly rejects animal feed, and the repeat risotto resolution
expressly calls edibility a category condition. These are limited visibility
improvements, not systematic boundary identification. More questions would not
by itself establish correctness; incomplete diagnostic wording alone does not
fail a clear final definition.

The first risotto draw loses shared edibility and the repeat restores it. This
variation prevents attributing that loss, or its restoration, to v124 from the
present evidence. No draw is spliced, rewritten or scored as a repair.

The next proposed controlled test would examine the whole proposed definition,
including its defining clause, rather than directing the two-direction check
only toward alternatives and relationships. A condition shared by legitimate
members is not necessarily sufficient to admit a new member. This is a plausible
attention gap, not a demonstrated cause. Replace the existing checking paragraph
in a new version rather than append a Food exception, then compare fresh
matched inputs and repeat consequential differences. No such edit or run is
included here.

## Receipt bindings and verification

Each record is in `run/results.jsonl` within the named native experiment.
Independent verification matched the production receipt digest and raw output
hash, exact input/prompt/settings identities and every post-quote substring.

| Cohort | Case | Producer record SHA256 |
|---|---|---|
| draw1 | hr04-food-risotto | `4164689299e8e5cf25bbf1644e97c0a9d9b40c92926520d17e1ee294367089a3` |
| draw1 | hr04-food-sourdough | `d37e6ec0f54a88c9dfd2a774949bc8366fed473a5258b6316360e6fd539293c2` |
| draw1 | hr04-food-pie | `53d8120068a27d5c711e27c7a4b51ecf8db74092a445380386e34dd04e40301b` |
| draw1 | hr04-food-brisket | `1e7a9972f079ae2aab230851824da810aa06da52c85a88af571a2833b2938d0a` |
| repeat | hr04-food-risotto | `164db0fe11dc85608faead28dacc4c1a59423ada04ccd65ca669beae59c26154` |
| repeat | hr04-food-brisket | `203ad68364584c7b953664f01e301db048c3f8b02bdf0e459423bcbeccbc7cd7` |

All 23 focused prompt-revision and saved-comparison tests pass. The exact
replacement check confirms only the two declared phrases changed. Historical
legacy-suite limitations remain recorded in the prior v123 report; this stage
does not claim that the full legacy integration suite passes.

After integration, all 20 current-main prompt-assembly tests also pass. Main's
native `prepare --from` frozen-input check at
`target/bootstrap-v124-main-frozen-input-check-v1` reproduces every input and
rendered prompt byte exactly, with four unrun cases and zero model attempts.
This checks the shared workflow with already frozen data; it is not a fresh
AS generation or a new semantic sample. A separate spec-based preflight was
interrupted during the large main experiment-history lookup, before creating
its experiment or making calls. No runner change was made to address that
inventory latency. The completed check uses the existing task history root.
