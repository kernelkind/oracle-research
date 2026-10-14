# Hierarchy generation V3, V3.1 and V3.2

Status: the shared CLI constructor in `sse_multivector/hierarchy_generation.py`
implements V3, V3.1 and the approved V3.2 update. V3 and V3.1 remain available
in code; V2 is preserved in Git history.
Offline construction checks pass; model-based hierarchy-quality qualification
remains pending. HR11–HR14 retain Pair-consolidation-v6; HR15 and HR16 used
Pair-consolidation-v7. Experimental Pair-consolidation-v11 specifies the user's
2–5-word title requirement; all fifteen screened answers meet that limit.
Meaning and browsing-quality qualifications remain below. This record does not
activate the prompt or authorize model calls. The user's personal outline,
`docs/notes/MY-NOTES_10-12.md`, remains read-only. The preceding mechanisms are
V2 and V1; earlier variants need no formal naming.

## V3.2: Bootstrap-v133 titles for SSE and browsing

V3.2 requires [Bootstrap-v133](../../sse_multivector/shr_single_pair/Hierarchy-bootstrap-v133.md)
and its existing [five-field output schema](../../sse_multivector/shr_single_pair/Hierarchy-bootstrap-v130.output.schema.json).
Bootstrap returns an explicit `meaning` and a natural `title` derived from that
meaning. Use that exact title as the heading for the original construction item,
in its SSE input, in pair-consolidation inputs and in canonical browsing.
Retain the original local `subject` separately in the original-entry evidence;
do not overwrite the source hierarchy or generate another title.

SSE receives the title, two newlines, then the meaning. Pool only the title's
UTF-8 byte span; the meaning is unselected context. Existing encoding identities
therefore distinguish a changed title even when the meaning is unchanged.
Canonical nodes retain the construction item's heading in their existing
`subject` field. Synthetic items continue to use pair-consolidation's returned
title. Saved-state checks bind each original title to its validated Bootstrap
answer and verify item and canonical headings against it.

Select V3.2 with `"generation_policy": "hierarchy-generation-v3.2"` in the
schema-1 hierarchy definition and configure Bootstrap-v133 explicitly. Native
preparation rejects another Bootstrap version or a schema missing the five
required output fields before preparing a batch. Null meanings retain null
titles and remain excluded from encoding and construction.

V3.2 inherits V3.1's cutoff, discard and unpaired-entry rules, family-specific
round reset and two-note stopping rule. V3/V3.1 keep original local subjects for
SSE and browsing, including when their configured Bootstrap returns a title.
Historical prompts, definitions, producer answers and receipts remain unchanged.
Offline fixtures qualify this wiring; a real V3.2 hierarchy comparison remains
the next quality check.

## V3.1: shifted exponential cosine cutoff

The user approved an initial cutoff of **0.66**, a floor of **0.40**, and decay
that halves the distance to the floor after each consolidation round:

```text
cutoff(round) = 0.40 + (0.66 - 0.40) * 0.5^(round - 1)
```

The first four cutoffs are 0.66, 0.53, 0.465 and 0.4325. Each sibling family
starts at round 1, including roots and children of a canonical node. These are
temporary consolidation rounds, not canonical hierarchy levels.

Select the highest-scoring non-overlapping pairs as in V3, then filter them
using the unrounded cosine. A score equal to the cutoff passes. Only passing
pairs receive consolidation calls. Both topics in a below-cutoff pair disappear
from further construction in that family; preserve their original entries,
meanings, vectors and receipts as evidence. A lone odd entry carries forward
unchanged because it has no failed pair score.

Promote six or fewer remaining topics without another pairing round. If every
pair fails, finish the family without an empty model batch, retaining the odd
leftover when present. Nodes with at most two distinct notes still stop.
Children still restart from their parent's associated original local L1 entries.

V3.1 permits notes to disappear when their topics are discarded. Native summaries
report `discarded_by_cutoff` with family, round, score and original associations,
and `notes_not_in_hierarchy` after completion, counting notes available through
canonical leaves. Completion describes construction, not full-corpus coverage
or semantic qualification. State validation accounts separately for retained
and discarded original entries.

Select V3.1 with `"generation_policy": "hierarchy-generation-v3.1"` in the
schema-1 hierarchy definition. Omitting this field retains V3; explicit
`"hierarchy-generation-v3"` is also accepted. V3 continues to consolidate every
selected pair without a cutoff and retains its original coverage checks.
The frozen definition fixes the policy across resumes. Existing run definitions,
prompts, producer identities and receipts are unchanged.

The manual root-only V7 comparison produced five roots representing 40/50 notes
at floor 0.40, four roots and 39/50 at 0.30, and six roots and 42/50 with ordinary
halving. The 0.40 headings were judged more understandable by the agent; this
is not full-hierarchy qualification. That diagnostic discarded intermediate
odd leftovers. V3.1 carries them, following the user's rule that a topic that
has not failed the cutoff passes, so it does not claim to reproduce the
diagnostic's 40-note coverage exactly. Evidence remains in the retained
`oracle-mvp-hierarchy-root-shifted-cutoff-v7-v1` worktree under
`target/root-shifted-cutoff-v7-v1/`.

## Construction outline

Bootstrap requests an explicit meaning for every original local L1 entry.
Construction uses entries with non-null meanings, retaining null answers and
their original entries as audit evidence. Every selected note must still have
at least one entry available for construction.
Pairing and consolidation then repeatedly form temporary synthetic grouping
nodes. Only the final groups become nodes in one canonical level. Intermediate
synthetic nodes do not become canonical nodes or browsing steps.

To construct children of a canonical node, start again from the original local
L1 entries associated with that node, reusing their meanings and vectors. Do not
expose the temporary binary grouping tree as the next canonical level.

Six is the maximum number of nodes per sibling family, not an exact required
count. Stop expansion when a node has two or fewer distinct notes (rule 3.2).
Other unresolved details are listed below.

## Step 1.1: establish the original local L1 meanings

Run Bootstrap independently for every original local L1 entry and preserve its
answer and producer evidence. Finish the other Bootstrap requests when an
answer has a null meaning. After Bootstrap completes, omit null-meaning entries
from construction and report them as `skipped_bootstrap`; preserve their original
IDs, inputs, null answers and receipts. Do not encode null meanings or resample
them. If a selected note has no non-null L1 meaning, root construction remains
blocked so that the hierarchy cannot silently lose that note.

The user approved this change while continuing HR14 after two null meanings.
Earlier frozen runs retain their original generator commits and null policy.

## Step 1.2: SSE encoding of original local L1 entries

Use exactly this text layout:

```text
[[{heading}]]

{explicit meaning from Bootstrap}
```

For V3/V3.1, `heading` is the original local L1 subject. For V3.2, it is
Bootstrap-v133's returned title. The brackets mark the tokens selected for SSE
pooling; they are notation rather than literal text to encode. Pool only the
heading. The explicit meaning is unselected context available to the encoder.

## Step 1.3: cosine pairing within one family

Compute cosine similarity for every unordered pair of distinct vectors in the
current family's construction pool. Use all vectors in that pool, without a
candidate shortlist. Rank those pairs from highest similarity to lowest and
select non-overlapping pairs in that order: once a vector has been selected,
skip subsequent pairs containing it. Continue selecting pairs until no pair of
unused vectors remains. With ten nodes this selects five pairs, not four.
V3 consolidates all selected pairs. V3.1/V3.2 filter those selected pairs using the
round's shifted cutoff as specified above; it does not search for another
partner for a rejected pair.
When the node count is odd, carry the one unpaired node forward unchanged,
including its subject, explicit meaning, SSE vector and associated original
local L1 entries.

Families are separate. Do not pair entries belonging to different canonical
parents merely because their intended children are at the same depth. Root
construction has one pool containing the non-null original local L1 entries from the
whole selected corpus. Subsequent construction uses a separate pool for each
parent, containing its associated original local L1 entries. Later temporary
consolidation rounds stay within that same family.

In the user's notation, L is distance from the root, with roots at L1. The S
numbers identify the nodes in the example; parent relationships identify their
families:

```text
L1S1
├── L2S1
└── L2S2

L1S2
└── L2S3

L1S3
├── L2S4
├── L2S5
└── L2S6
```

L2S1 and L2S2 are compared together. Separately, every pair among L2S4, L2S5
and L2S6 is compared. L2S3 has no partner in its family. The six L2 nodes are
never one pairing pool. This illustration establishes family boundaries; it
does not attempt to demonstrate the distinct-note stopping rule 3.2.

## Step 1.4: consolidation of a selected pair

Follow the current consolidation prompt's overall structure, adapted to exactly
two supplied nodes, each with its subject and explicit meaning. Generate a
synthetic parent for that pair rather than selecting two or more nodes from a
larger supplied group.

For root construction, supply no parent. For deeper canonical levels, supply
the current canonical parent's subject and fixed explicit meaning. Use that
same canonical parent throughout the temporary consolidation steps constructing
its children. Do not supply recursive ancestors or use a temporary synthetic
node as the enclosing canonical parent.

The proposed synthetic meaning must cover both supplied meanings and fit wholly
within the supplied canonical parent's fixed meaning when one is present.
There is no selection of a subset from a larger supplied sibling group.

The pair prompt must always generate a synthetic parent whose explicit meaning
covers both supplied meanings. Return only its subject and explicit meaning;
`null` is not an allowed semantic result. This rule is approved. Transport or
invalid-output failures remain separate, unresolved operational cases.

Use this same consolidation rule for every selected pair. Do not add a
separate equivalence judgment, comparison call or equivalent-pair branch.
The proposed special case of recognizing equivalence and copying one supplied
meaning was withdrawn; it is not part of this design.

[Hierarchy-pair-consolidation-v6](../../sse_multivector/shr_single_pair/Hierarchy-pair-consolidation-v6.md)
is approved for the next hierarchy run. The user's decision was: "OK lgtm. we
will use this for the next hierarchy run". This approves the wording and next-run
selection; it does not establish measured accuracy. V6 retains V5's minimal
adaptation of Consolidation-v21 and removes the input-building sentence about
roots. It uses the exact shared definition-writing rules-v6 from Bootstrap-v129
and Consolidation-v21 through a pinned assembly; those prompts and shared rules
are unchanged. V6's saved HR14 outputs supply the specificity witnesses examined
in the experimental V7 screen below.

### Approved specificity objective and experimental V7

The user clarified that every pair uses the same consolidation mechanism:
choose the most specific coherent topic that covers both complete supplied
meanings and fits the supplied parent when present. Its meaning may have the
same scope as a supplied meaning. This introduces no equivalence mode, separate
comparison or output field. Keep defining conditions wherever complete coverage
permits them; check whether a more specific coherent meaning still covers both.

The HR14 tomato witness supplies fleshy edible fruits of Solanum lycopersicum
and edible fruits of that same plant. Under the user's reading, the first is
narrower and the second already covers both. V6 instead returned Edible fruits
at the root and Edible plant fruits under an existing parent. The latter survives
as C00053. Containment alone does not establish that this breadth is useful.
Other saved pairs lose Nostr, Bitcoin, Breakfast or Dezeen identity. These
observations motivate a specificity test; they do not establish which old
sentence caused the results.

[Pair-consolidation-v7](../../sse_multivector/shr_single_pair/Hierarchy-pair-consolidation-v7.md)
changes only the task wrappers: it requests the most specific coherent topic,
retains shared identities/conditions, and checks for a more specific proposal
that still satisfies full coverage and parent fit. It removes “new” from the
opening parent request. Shared definition-writing rules-v6, the Bootstrap-v129
companion, the existing example and the title/meaning output contract are exact.
The approach uses concise constraints and targeted tests, following [official
OpenAI reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively);
that guidance does not certify this semantic objective or its reliability.

The initial screen inherits nine exact HR14 root cases from batch-00001:
P00000 (Tomatoes), P00002 (Coffee/water extraction), P00004 (Nostr), P00010
(Cooking with different method scope), P00015 (Coffee shops), P00018 (Breakfast),
P00022 (Bitcoin), P00029 (Dezeen) and P00046 (Bread/Bread preparation). A second
batch inherits F00013-P00000 from batch-00023: the same tomato pair with its
fixed canonical parent. Use unchanged Sol 6.1 medium subscription/SSE settings,
native exact reuse, prefix warming and shared scheduling. Do not rerun baselines,
alter meanings or change the hierarchy. Only the assembled prompt changes.

Pre-call review criteria: retain tomato identity without excluding the broader
supplied meaning; preserve established identity and common conditions in the
other scope-loss cases; retain genuine method differences and explicitly cover
both product and activity roles. Preserve fixed-parent containment. A narrower
title alone is insufficient: independently review the final meaning for complete
coverage and unnecessary scope. Assessments remain agent-authored except for the
user's reviewed tomato containment decision. One draw per case cannot establish
reliability, a unique optimal heading or full hierarchy quality.

The initial screen completed on 2026-10-13: all ten saved-input cases return valid
title/meaning objects and receive qualified native agent accepts. Both tomato
requests return exactly the broader supplied meaning, “Tomatoes are the edible
fruits of the tomato plant, Solanum lycopersicum.” The supplied-parent version
also fits its unchanged biological-material/food parent. No new relation label,
equivalence mode or constructor behavior was introduced.

| Control | V7 finding |
|---|---|
| Tomatoes, root and supplied parent | Retains named-plant fruit identity; does not require fleshy membership |
| Coffee | Retains water-based extraction of roasted coffee beans |
| Nostr / Bitcoin | Retains the specific protocol/network or currency/network identity |
| Breakfast | Retains beginning the eating day after the main sleep period |
| Dezeen | Retains the named publication in its credited-original-publisher role |
| Coffee shops | Retains coffee preparation/service as a principal offering |
| Cooking | Covers heat-based and wider combining/transforming methods from the two meanings |
| Bread / Bread preparation | Explicitly covers the food product and partial production activities |

The five observed identity-loss results do not recur in this draw. This supports
the complete V7 revision; it does not attribute the gain to one sentence, prove
reliability, or certify every basic concept and necessary implication. The two
tomato requests differ by supplied parent and are not identical-request repeats.
No broader hierarchy was regenerated or activated during this screen.

Native accounting is complete: twelve fresh attempts including two prefix
warmups, ten comparison answers, zero reuses, failures or retries. Saved usage is
4,806 uncached input tokens, 11,520 cached input tokens and 1,371 output tokens,
with 677 reasoning tokens already included in output; reported cache-write tokens
are zero. API-equivalent catalogue cost, including warmups, is **$0.024474**.
This is comparison accounting, not an incremental subscription cash charge or a
matched policy-savings claim. V6 baselines were not rerun.

The worktree is retained for frozen prompt/source/code bindings and native
receipt validation:

```text
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-v7-specificity-v1
```

Ignored evidence is `target/pair-consolidation-v7-root-controls-v1`,
`target/pair-consolidation-v7-parent-control-v1`,
`target/pair-consolidation-v7-usage-source-v1.json` and
`target/pair-consolidation-v7-usage-summary-v1.json`. The original HR14 worktree
continues to supply the unchanged input and baseline receipts. Assembly and all
26 production-path assembly tests pass. The expanded qualification below extends
this initial screen without changing V7 or regenerating a hierarchy.

### Expanded saved-input V7 qualification

The user authorized a wider saved-pair test before a new hierarchy run. It
completed on 2026-10-13 with **65 valid answers: 63 qualified agent accepts,
two uncertain assessments and no confirmed rejects**. The user subsequently
accepted both uncertain outputs, so all 65 cases are accepted across the agent
reviews and those two user adjudications. The other 63 cases remain qualified
agent assessments, not independently validated human gold; this is not a
reliability estimate. Ten answers reuse the initial screen exactly; reuse adds
no sample.

The panel inherits root cases F00000-P00000 through F00000-P00059 inclusive
from HR14 batch-00001, plus five supplied-parent cases from batch-00023:
F00011-P00000 (Recipes), F00012-P00000 (Breakfast), F00012-P00001 (Food with
different consumer restrictions), F00012-P00003 (Frying/Forks) and
F00013-P00000 (Tomatoes). The root selection covers shared names with different
meanings as well as product/activity, device/function, material/quality
and other mixed-topic pairs. It is a bounded selection from the first root
round, not all 834 saved consolidations or a random sample of the hierarchy.
The original fifty-note corpus retains verified ASv6.100 provenance.

Native preparation preserves each complete INPUT_JSON, the fixed parent where
present, the saved V6 baseline, model/schema/settings and the isolated worker.
V7 is byte-identical to the initial screen. Use GPT-6.1 Sol medium subscription
over SSE, native exact reuse and automatic prefix warming; both ready batches
were submitted immediately through the shared queue. No baseline was rerun.
Review checks the final meaning for both full coverage and unnecessary breadth,
including whether conditions belong to every admitted kind or only one.

The initial identity controls survive exact reuse. New Coffee, Bitcoin, Nostr,
Breakfast, Dinner and named-hashtag pairs generally retain their identities.
Food cases explicitly preserve alternatives such as human consumption versus
animal nourishment, and nourishment versus enjoyment. Mixed-topic outputs
explicitly cover pancake cakes and dry/wet preparation mixtures, food-smoking
processes and equipment including cold smoking, lunch meals and containers,
exercise and unperformed workout plans, and salads including fictional
personifications. Frozen materials admits whole or partial freezing without
requiring every kind to be edible or solid water. All five supplied-parent
proposals receive qualified accepts for coverage and parent fit.

The two initial uncertainties were subsequently accepted by the user:

- **F00000-P00013, Coffeechain:** the inputs define the specific #coffeechain
  sharing tag and the informal Coffeechain community on Nostr. V7's title is
  *Coffeechain social-media sharing*. Its opening meaning is “Coffeechain
  social-media sharing is the connection of coffee-related posts in a shared
  social-media conversation.” Later sentences explicitly include the tag and
  named community. The agent questioned whether the opening could admit an
  unrelated coffee-post conversation. After seeing both inputs, the complete
  output and that concern, the user accepted it, verbatim: **“i think it's fine”**.
  This saved output is accepted; the concern is not a failure.
- **F00000-P00038, Diets:** the first input describes food-consumption patterns
  characterized by food kinds and amounts or relative proportions. The second
  describes food-consumption patterns/regimens without explicitly imposing
  those features. V7 returns “Diets are patterns or regimens of food consumption
  characterized by the kinds of food eaten and their amounts or relative
  proportions. They include habitual ways of eating and deliberately followed
  eating regimens.” The agent questioned whether a regimen defining only eating
  times would be excluded. After seeing both inputs, the complete output and
  that concern, the user accepted it, verbatim: **“i think it's fine”**. This
  saved output is accepted; the concern is not a failure.

Both decisions are recorded through native `review` with role `user`, preserving
the earlier agent assessments and exact input/output bindings. No additional
rationale or general rule was supplied; acceptance applies to these outputs.
No prompt revision, new hierarchy, activation or per-sentence causal claim
follows from this screen. V7 remains experimental; HR14 and its meanings retain
V6. A new hierarchy would be a separate end-to-end test rather than certification
from these pair answers.

Native accounting is complete: **57 fresh attempts**, including two prefix
warmups and 55 consolidation answers, plus ten exact reuses. There are no
failed/retried attempts or missing usages. Fresh usage is 17,036 uncached input
tokens, 61,056 cached input tokens and 10,566 output tokens; 7,028 reasoning
tokens are already included in output, and reported cache writes are zero.
Complete fresh API-equivalent catalogue cost is **$0.1458376**. Native original
generation accounting, tracing reused producers and their warmups once, is
69 calls and **$0.1703116**. Neither total is an incremental subscription cash
charge, a policy-savings measurement or a contemporaneous V6 comparison.

The expanded worktree is retained for frozen sources and native receipt/review
validation:

```text
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-v7-expanded-v1
```

Ignored evidence is `target/pair-consolidation-v7-expanded-roots-v1`,
`target/pair-consolidation-v7-expanded-parents-v1`,
`target/pair-consolidation-v7-expanded-usage-source-v1.json` and
`target/pair-consolidation-v7-expanded-usage-summary-v1.json`. Reviews use native
`review` with role `agent`, including exact import of the ten initial reviews.
Preparation verified exact inherited inputs and isolated source bindings; fresh
receipts retain HTTP 200, the requested provider/model/effort and raw cache
usage. Assembly and all 26 production-path assembly tests pass. Historical V6,
shared-rules-v6 and the Bootstrap companion remain unchanged.

### Additional V7 Coffee supplied-parent regression

The user authorized HR14 F00015-P00000 from batch-00023 after inspecting its
V6 over-broadening. Both inputs define Coffee as a beverage made from a water
extract of roasted coffee beans. The supplied parent is Beverage and drinking
systems. V6 returned Plant-extract beverages, unnecessarily admitting beverages
from other plants while still fitting that parent.

On 2026-10-13, unchanged V7 returns **Coffee**, with the exact second supplied
meaning: **“Coffee is a beverage made from a water-based extract of roasted
coffee beans.”** Native agent review accepts full coverage, retained identity
and fixed-parent fit. This is one additional saved-input request, separate from
the 65-case panel above; the parent makes it a different complete request from
the previously tested root Coffee pair. No exact answer was available for reuse.

Native preparation inherits the exact inputs, parent, V6 baseline and Sol 6.1
medium subscription/SSE settings. Two fresh attempts include one prefix warmup
and one valid consolidation, with no failures, retries or missing usage. Usage
is 439 uncached input, 2,304 cached input and 225 output tokens; 152 reasoning
tokens are included in output, and reported cache writes are zero. Complete
API-equivalent catalogue cost is **$0.0033584**, not subscription cash billing.
One draw does not establish reliability or tighten the broad parent itself.

Evidence remains in the retained expanded worktree under
`target/pair-consolidation-v7-coffee-parent-v1`,
`target/pair-consolidation-v7-coffee-parent-usage-source-v1.json` and
`target/pair-consolidation-v7-coffee-parent-usage-summary-v1.json`. No prompt,
Bootstrap meaning or hierarchy was changed.

### Approved title requirement and experimental V8 cycle

The user requires: **“the title for the explicit meaning must be a concise
reflection of the explicit meaning content.”** The title should convey the
central kinds and relationships admitted by the final meaning. Illustrative
examples and optional variations need not be repeated in a title. This adds a
title criterion; it does not withdraw the earlier meaning-coverage accepts or
the user's Coffeechain/Diets decisions.

The user authorized one draft/test/review cycle. Experimental
[Pair-consolidation-v8](../../sse_multivector/shr_single_pair/Hierarchy-pair-consolidation-v8.md)
removes V7's unqualified preference for a single shared-category heading, adds
a final title-writing/check step, and makes title-to-meaning fidelity explicit
in the output description. It preserves the coherent most-specific parent
objective, full meaning coverage, fixed-parent checks, example, schema and exact
shared-rules-v6/Bootstrap-v129 companion. No historical prompt is rewritten.
The focused change follows [official reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively)
on clear constraints and concise instructions; that guidance does not certify
the naming rule. No reasoning trace or additional title example is requested.

Before authoring V8, native preparation/run reused the exact saved V7
Coffee/Coffee-chains answer F00000-P00042. Native agent review rejects its title
under the new criterion: Coffee names the beverage while its meaning also
admits branded multi-outlet coffee-shop businesses. This minimal failing
semantic check exercises saved production evidence with zero fresh calls; it
does not reject the earlier meaning-coverage assessment or establish human gold.
Evidence is `target/pair-consolidation-v8-title-baseline-v1` in the V8 worktree.

Pre-call panel: fourteen root requests from the saved V7 expanded run, P00000,
P00002, P00039, P00041, P00042, P00044, P00046, P00048, P00052, P00053,
P00054, P00057, P00058 and P00059; plus supplied-parent F00012-P00003
(Frying/Forks) and F00015-P00000 (Coffee/Coffee). Native `prepare --from`
preserves exact inputs/settings and V7 answers as baselines, without rerunning
V7. Use unchanged GPT-6.1 Sol medium subscription/SSE and frozen workers, native
prefix warming and one shared scheduling group for all ready V8 batches.

Review criteria fixed before calls: titles must reveal substantial admitted
kinds/relationships such as beverage/retail chain, meal/container,
process/equipment and activity/plan. Short natural wording should replace
elaborate abstractions; familiar accurate category names remain allowed.
No exact proposed caption is gold. Review the entire final meaning separately
for both-input coverage, specificity and supplied-parent fit: a clearer title
does not excuse a lost kind, new restriction or unnecessary meaning breadth.
The controls check retained identity and already informative short titles.
This is one candidate draw on sixteen requests, not a reliability estimate,
sentence-level ablation or authorization to activate a hierarchy prompt.

All sixteen V8 cases completed and received qualified native agent accepts for
title fidelity and full meaning coverage/parent fit in this initial panel.
Eight targeted cases improved under that criterion; eight controls remained
acceptable. Representative title changes:

| Saved V7 title | V8 title |
|---|---|
| Coffee (meaning also admits coffee-shop chains) | Coffee and coffee-shop chains |
| Lunch (meaning also admits lunch boxes) | Lunches and lunch boxes |
| Food smoking (meaning also admits smokers) | Food smoking and smokers |
| Exercise (meaning also admits workout plans) | Exercise and workout plans |
| Changes to whether or when undertakings proceed | Cancellation and postponement |
| Chicken carcasses and their stock derivatives | Chicken carcasses and stock |

Tomatoes, beverage-only Coffee and supplied-parent Coffee retain the chosen
supplied meanings exactly. Other bodies were reviewed rather than assumed
unchanged. This panel demonstrates clearer naming of small pairs, not good
titles after repeated consolidation. Its complete fresh API-equivalent cost
was $0.0608836 for nineteen attempts, including three warmups; the V7 failing
baseline was one exact reuse with zero fresh calls. The historical baseline's
producer is accounted separately in the native generation total.


#### HR16 review prompted by the user

The user rejected HR15 C00047's long inventory heading and reported that this
was a widespread V7 failure, directing attention to HR16. HR16's completed
50-note state uses Pair-consolidation-v7/Bootstrap-v129 and contains 410 canonical
nodes, including 106 produced by consolidation. The saved state SHA-256 is
`24a660a3e12fef7e235c76a30f4c5f9eaee9efc72e99049bf805a581fb530a43`.

Its six root titles are Biological and culinary materials, practices and
resources; Life, society, and the material world; Activity, experience, and
meaning; Entities; Materials, products, services, and engagement with them;
and Nostr. Five are broad abstractions or inventories. The Entities root
C00004 has children C00019 and C00022 also titled Entities. Its Food-related
branches use several similar inventories, including C00013 Biological and
culinary materials, activities and food resources and C00024 Food, drink,
and related activities and engagement. This is a browsing-quality failure;
word count alone cannot identify it. All canonical titles have at most eight
whitespace-separated words, yet a short Entities heading does not tell the
reader which information to choose.

The first root-round Beets/MrBeast input F00000-P00106 generated Entities.
Beets' supplied meaning defines edible table-beet roots; MrBeast's supplied
meaning defines Jimmy Donaldson's public online name. Later rounds propagate
that generic topic. Root-round input counts are 324, 162, 81, 41, 21 and 11;
median supplied meaning lengths rise from 26 to 44, 64, 102, 157 and 195 words.
These descriptive lengths do not establish semantic accuracy. They show that
the original V8 small-pair panel omitted repeated consolidation of already
broad synthetic meanings. A long title is one symptom; faithful naming of an
uninformative meaning remains uninformative.

Before extra V8 calls, extend this same one-revision cycle with ten exact saved
production requests: five final HR16 root pairs from batch-00006 and the carried Nostr root
from batch-00002; the first
Beets/MrBeast pair from batch-00001; supplied-parent C00013 from batch-00017
and C00024 from batch-00022; and the user's HR15 C00047 from batch-00015.
Native preparation preserves each original input, parent, settings and saved
V7 output. This is an extension after seeing the first panel's results, not a
preplanned holdout or another prompt revision. Evaluate title concision and
fidelity, full coverage/parent fit, and browsing usefulness separately. A
short generic abstraction or another inventory is not an acceptable fix merely
because the JSON and containment are valid. Do not shorten scope silently or
rewrite the saved hierarchy. One draw cannot establish reliable hierarchy
quality.

#### Extended V8 result: not a hierarchy-title fix

All ten extended cases completed. Qualified native agent review rejects eight
for browsing usefulness or specificity, accepts the Nostr identity control,
and leaves HR15 C00047's shorter inventory title uncertain. These are agent
assessments, not ten new human judgments. Full-scope formal certification is
not claimed; the rejected headings do not themselves prove containment errors.

| Saved node / exact production case | V8 title | Assessment |
|---|---|---|
| HR16 C00001 / F00000-P00000 | Food and related practices, gardening, and animal biological materials | Another long inventory |
| HR16 C00002 / F00000-P00001 | Life and the social, cultural, and material world | Broad abstraction, longer than V7 |
| HR16 C00003 / F00000-P00002 | Activity, meaning, and mental, bodily, and sensory phenomena | Elaborate inventory |
| HR16 C00004 / F00000-P00003 | Entities | Short but uninformative |
| HR16 C00005 / F00000-P00004 | Materials, products, services, and engagement with them | Unchanged vague heading |
| HR16 C00006 / earlier F00000-P00002 | Nostr | Retains a useful named identity |
| HR16 first Beets/MrBeast / F00000-P00106 | Root vegetables and YouTube creator identities | Unrelated kinds; unnecessary identity generalization |
| HR16 C00013 / F00001-P00002 | Food resources and activities, gardening and animal eggs | Another inventory |
| HR16 C00024 / F00005-P00001 | Food and drink: products, activities, and engagement | Inventory remains |
| HR15 C00047 / F00004-P00003 | Food and drink, preparation, and service | Shorter; not an established acceptable fix |

The Beets/MrBeast result covers both supplied meanings but generalizes the
specific table-beet kind and named creator identity without creating a useful
shared topic. At the final Entities input, one supplied meaning is already
Entities, so simply selecting a narrower familiar heading would exclude
admitted information. The final-root experiment holds all earlier V7 outputs
fixed; it is not a V8 hierarchy rerun and cannot determine how V8 would change
pairing in subsequent rounds.

The evidence supports a broader diagnosis than excessive title length:
consolidation can lose useful topic identity early and accumulate broad
inventories through repeated rounds. V8's title-after-meaning instruction
improves some small pairs but does not resolve this. Do not recommend V8 for
activation based on the sixteen initial accepts. A next prompt revision should
be qualified on early unrelated inputs and already synthetic later-round
inputs, with coherent grouping, useful natural names and scope preservation
evaluated separately. This recommendation does not change pair eligibility,
the constructor, shared rules or any immutable hierarchy meaning.

The native v2 usage summary covers ten experiments: twenty-six fresh V8
answers plus the reused V7 baseline; thirty-seven fresh attempts including nine
warmups and two recovered provider failures; one exact reuse; no terminal
failures. Two failed attempts have unknown usage, so the **$0.1412444** known
fresh API-equivalent subtotal is not a complete total. Known token subtotals
are 22,695 uncached input, 31,744 cached input, zero reported cache writes and
9,268 output, including 5,089 reasoning tokens. Original generation tracing
adds the reused baseline's two source calls once; its known subtotal is
$0.1466228 and also incomplete. These are catalogue equivalents, not cash
subscription charges or a matched cost-savings claim.

Evidence is retained in
`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-v8-title-v1/target/`
under the `pair-consolidation-v8-title-*`, `pair-consolidation-v8-hr16-*` and
`pair-consolidation-v8-hr15-c47-v1` experiments. Native usage specifications and
summaries have v1/v2 suffixes; native reviews preserve case/input/output hashes.
The worktree must remain because these receipts bind absolute project source
and artifact paths. V8's compiled SHA-256 is
`91d6e0e2f9ee3a0455778c7dd9f0722890ff67e57889b5c632e2dab164396ad2`;
V7, Bootstrap-v129 and shared-rules-v6 remain unchanged. No saved hierarchy or
UI was edited, no new hierarchy was generated, and no second revision was made.

Exact answer reuse must match the complete request, including the optional
canonical parent. A root-consolidation answer cannot be reused for a request
with a supplied canonical parent merely because its two input nodes match.

### Experimental V9: summarize the topic in its title

The user clarified and approved that a title should be a **short, recognizable
topic name summarizing the meaning**, with detailed boundaries in the meaning.
The earlier V8 assessment that a title must name each substantial related kind
does not express this requirement. Prior records remain evidence of that
experiment, not the title criterion for future tests. Fixed meanings continue
to define containment; title concision does not authorize changing their scope.

[Pair-consolidation-v9](../../sse_multivector/shr_single_pair/Hierarchy-pair-consolidation-v9.md)
uses native revision against V7, replacing V8's title wording with one direct
instruction section: choose a short familiar topic name; let the name convey
directly related activities, products, participants and resources; keep detailed
conditions in the meaning; retain qualifiers that identify the topic; check the
title as a faithful summary while keeping the established meaning unchanged.
Its output description agrees with that distinction. V7's other wrapper text,
synthetic example, meaning checks and shared-rules-v6/Bootstrap-v129 companion
are preserved byte-for-byte. No new example, reasoning trace, hard title word
limit or hierarchy implementation is added. This follows the [official
reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively)
on concise direct constraints and representative evaluation; the guidance does
not prove that these semantic instructions work for Sol 6.1.

Before implementation, native preparation/run reproduced the user-rejected
HR15 C00047 heading through one exact reuse, zero fresh calls. Its user review
records the verbatim title and “this is way too long”, limited to naming.

Pre-call panel: the ten exact V8 extended HR15/HR16 inputs above, plus four
small-pair controls from V7's expanded root run (P00000 Tomatoes, P00002 Coffee,
P00042 Coffee/chains and P00048 Lunch/lunch boxes) and the exact supplied-parent
Coffee F00015-P00000. Native `prepare --from` retains saved V7 answers, inputs,
parents, model/settings and frozen workers. All ready batches run under one
shared scheduling group, with GPT-6.1 Sol medium subscription/SSE. Fifteen
requests, one candidate draw; no hierarchy rerun or prompt activation.

Review concise natural topic naming and fidelity to the final meaning, without
requiring any exact caption or every covered facet in the title. Separately
check full meaning coverage, identity, restrictions and parent fit. A familiar
heading may summarize related activities and products; a short generic
catch-all does not establish browsing usefulness. Root inputs whose earlier
V7 meanings are already universal remain diagnostic limits, not instructions
to hide or narrow their scope. Existing Bootstrap semantic conclusions are
not reinstated as gold by these title tests.

V9's fifteen comparisons completed. Qualified native agent assessment accepted
seven, rejected six, and left two uncertain under the clarified title criterion.
C00047 becomes **Food and drink**, preserving its preparation, ordering,
service, appreciation and establishment/chain scope. Coffee/chains becomes
Coffee; Lunch/lunch boxes becomes Lunch; Activity, experience, and meaning
becomes Activity and experience. V9 still returns Food, drink, and engagement
with them and several abstract inventories. The already universal Entities
input remains Entities. These results are partial improvements, not approval
or a complete title fix. The supplied-parent Coffee body's added water-extract
alternative remains a separate specificity qualification.

### Explicit 2–5-word requirement: experimental V11

The user added a mandatory requirement: **pair-consolidation titles must contain
2–5 words**. This applies to generated `title`, not historical supplied headings;
fixed meanings and coverage requirements still apply. V9's one-word titles do
not qualify under this new requirement, even though they were acceptable under
the earlier test criterion. Retain their results without retroactive approvals.

[Pair-consolidation-v10](../../sse_multivector/shr_single_pair/Hierarchy-pair-consolidation-v10.md)
was drafted after V9 to make inclusion of related facets in a title exceptional
and explain the title/meaning distinction through the existing display-panel
example. **No V10 model calls were made** before the user specified word count.
[Pair-consolidation-v11](../../sse_multivector/shr_single_pair/Hierarchy-pair-consolidation-v11.md)
incorporates that explicit requirement in the title instruction, final check
and output description. The existing example's three-word title agrees with
the constraint. It retains V7's exact definition-writing and containment rules
and the same shared-rules-v6/Bootstrap-v129 companion. No historical version,
fixed meaning, constructor policy or selected hierarchy prompt is changed.

Before V11 calls, freeze the same fifteen exact inputs and settings used by V9,
with saved V7 answers as baselines and the same shared scheduling group. Check
2–5 whitespace-separated words mechanically, then assess natural topic naming
and fidelity independently of the word count. Avoid counting a generic filler
phrase as success. Review full coverage, identity, restrictions and parent fit
separately; a short heading cannot justify changing the meaning to fit it.
One candidate draw, no hierarchy rerun, no activation or reliability claim.

All fifteen V11 comparisons completed; **15/15 titles contain 2–5
whitespace-separated words**. Historical inputs remain unchanged.
Representative exact results:

| Saved title / case | V11 title | Words |
|---|---|---:|
| HR15 C00047's food/preparation/provision/appreciation inventory | Food and drink | 3 |
| HR16 C00024: Food, drink, and related activities and engagement | Food and drink | 3 |
| HR16 C00005: Materials, products, services, and engagement with them | Materials, products, and services | 4 |
| HR16 C00001's biological/culinary materials/practices/resources inventory | Food and biological materials | 4 |
| HR16 C00006: Nostr | Nostr ecosystem | 2 |
| Tomatoes control | Tomato fruits | 2 |
| Lunch/lunch-box control | Midday meals | 2 |

C00047 and C00024 retain their major supplied kinds and relationships in the
meaning rather than in the title. Nostr retains its protocol/network,
applications, community and adoption scope. The two-word tomato heading
preserves edible tomato-fruit identity. The lunch meaning still covers actual
or intended midday meals and related packed-meal containers.

Word count is established; comprehensive quality is not. Qualified native
agent assessment accepts six, leaves eight uncertain, and rejects the generic
Concrete and abstract entities heading for usefulness, despite its four words.
Some broad roots remain abstract and some generated meanings generalize roles
or alter extraction/nourishment wording. These qualifications are recorded
separately from the successful length check. No new human semantic approvals,
reliable success rate, complete hierarchy improvement or causal attribution to
a particular sentence is claimed. V9 and V11 each have one draw, and the
constraint changed between them. No V10 inference occurred.

Native accounting: V9 has fifteen fresh answers, twenty-three attempts including
warming, zero failures/reuses, and complete API-equivalent catalogue cost
$0.097938. V11 has fifteen fresh answers, twenty-five attempts including warming
and two recovered provider failures, zero reuses and no terminal failure. Its
known subtotal is $0.110756; two failed attempts have unknown usage. Across
both versions and the reused baseline: forty-eight fresh attempts, one exact
reuse, known subtotal $0.208694; full cost remains unknown. Known fresh tokens
are 31,782 uncached input, 44,800 cached input, zero reported cache writes and
14,065 output, including 8,391 reasoning tokens. Original-generation tracing
adds the baseline's two source calls once: fifty calls, known subtotal
$0.2132424, also incomplete. These are saved catalogue equivalents, not cash
subscription charges or a matched savings claim.

Source and evidence remain in
`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-v9-topic-title-v1/`.
Ignored native experiments are under `target/pair-consolidation-v9-*` and
`target/pair-consolidation-v11-*`; the usage source/summary are
`target/pair-consolidation-title-usage-{source,summary}-v1.json`. Revisions and
paired assemblies preserve V7, Bootstrap-v129 and shared-rules-v6. V11's
compiled SHA-256 is
`9250707f50fd6469247499b20bcf3535edbc403b4e9f53c8c291be3c9fe735eb`.
Retain the worktree for its frozen absolute source/receipt paths. Integrate
through a separate worktree based on latest main so its newer constructor
changes do not invalidate the completed experiments' source bindings.

## Step 1.5: SSE encoding of temporary synthetic nodes

Use the same layout and pooling boundary as for original local L1 entries:

```text
[[{synthetic subject}]]

{synthetic explicit meaning}
```

Pool only the synthetic subject. The synthetic explicit meaning is unselected
encoder context. As above, the brackets indicate the selected tokens and are
not literal text to encode.

## Steps 1.6–1.7: pair and consolidate the synthetic nodes

Use cosine similarity across all the synthetic nodes' SSE vectors within the
same sibling family to select the highest-scoring unique pairs, following the
non-overlapping selection in step 1.3. Consolidation generates a synthetic
parent for each eligible pair, following step 1.4. V3.1/V3.2 apply the current
round's cutoff before consolidation. Its inputs are the two
synthetic nodes' subjects and explicit meanings, plus the current canonical
parent when constructing a deeper level. Root construction has no parent.

## Step 1.8: repeat until at most six nodes remain

Repeat steps 1.5–1.7 until there are six or fewer nodes in the sibling family.
Select all the highest-scoring unique pairs as described in step 1.3; do not
limit pairing to force exactly six nodes.

In V3, with ten nodes, generate ten SSE vectors and calculate cosine similarity for
all 45 distinct pairs. Select five non-overlapping pairs. If each consolidation
returns a synthetic parent, five consolidation calls produce five synthetic
nodes. Five is within the maximum, so no further consolidation is needed for
that family. These final nodes become canonical; intermediate synthetic nodes
remain outside the canonical hierarchy.

In V3, if construction starts with more than six nodes and each consolidation
successfully returns one parent for its pair, the final node count is four,
five or six. The last consolidation starts with seven to twelve nodes: seven
or eight become four; nine or ten become five; eleven or twelve become six.
For seven nodes, three pairs produce three synthetic parents and the unpaired
node carries forward, giving four nodes total. This range is acceptable.
V3.1/V3.2 can finish below four nodes, including zero, because below-cutoff topics
are discarded. Only passing pairs need consolidation calls.

If the starting set already has six or fewer nodes, no consolidation is needed;
the final count can be below four.

## Step 1.9: make the final nodes canonical

Only the final nodes become canonical roots. Each retains all original local
L1 entries associated with it through the consolidations. Intermediate
synthetic nodes do not enter the canonical hierarchy. The same construction
is repeated separately for each canonical parent's next level, using that
parent's associated original local L1 entries.

## Steps 2.1–2.4: construct canonical L2

For each canonical root, take the exact original local L1 entries associated
with it through consolidation. Reuse those entries' Bootstrap meanings and
original SSE vectors. Do not use the intermediate synthetic nodes, original
local L2 nodes, or every L1 from the notes represented by that root.

Within this separate family, find the highest-scoring unique cosine pairs and
apply the selected policy's eligibility rule before consolidation. Generate
SSE vectors for the resulting synthetic nodes
and repeat pairing and consolidation until six or fewer nodes remain. Only
those final nodes become the root's canonical L2 children. Each retains the
original local L1 entries associated with it. Process each root separately,
subject to the stopping rule below.

## Steps 3.1–3.2: repeat for deeper canonical levels

Repeat the same construction beneath each canonical L2 node to construct L3,
and continue recursively. At each canonical node, start from its associated
original local L1 entries and reuse their original meanings and SSE vectors.
The local input remains L1 even as canonical depth increases.

Stop expanding a canonical node once it contains two or fewer distinct notes,
counting each note once even when multiple associated local L1 entries come
from it. A node already containing one note is finished and is not expanded.

## Details still to settle

- Model-based consolidation qualification and meaning validation.
- Cases where further grouping does not provide useful refinement despite
  a node containing more than two distinct notes.

These open details are not implementation decisions.

## Implementation and native workflow

Use the shared stable launcher from an isolated task worktree. V3, V3.1 and V3.2
use three commands: `prepare-hierarchy`, `advance-hierarchy` and `run-hierarchy`. V2's
constructor and its commands are removed; their source remains in Git history.
Historical traversal research and saved-data readers remain available.

The schema-1 construction definition contains `corpus`, `note_ids`,
`local_schema_version` (4), `bootstrap_spec`, `consolidation_spec` and
`worker_config`, with optional `generation_policy` as specified above.
Teacher specifications use the existing native prompt/runner
format. `worker_config` is an ordinary pinned SSE worker configuration used as
a template; each encoding gets its own frozen request and output paths. Run
the automatic command in the SSE worker's Python environment with its required
packages and local model artifacts available. Prompt versions are deliberate
configuration, not selected by latest filename.

Preparation validates settings and prompt assemblies and prepares all original
L1 Bootstrap cases without inference. Advancement collects native answers and
SSE receipts, preserves their identities, and prepares the next work without
inference. Automatic execution runs those ordinary native batches and SSE
jobs, then advances after completions. The shared runner controls provider
concurrency, retries, cache warming, exact answer reuse and usage accounting.
The constructor submits every ready model batch immediately; the shared runner
queues and admits individual model requests. There is no constructor batch cap.
All consolidation pairs ready in one advancement are prepared together, with
each request retaining its own family's pair and enclosing parent. A failed
family does not prevent other families' valid answers from advancing. At most
one local SSE job runs at a time; graph updates remain serialized.
Advancement and teacher execution invoke fresh processes through the shared
stable launcher, so compatible runner repairs are picked up on the next attempt.

Each unchanged heading/meaning encoding is reused within the construction.
SSE text contains the heading, two newlines, then the explicit meaning. Only
the heading's UTF-8 byte span is selected for pooling. The input brackets in
this document are notation, not encoded characters. Worker identities,
selected spans, receipt hashes and raw vector hashes are checked before use.

Every distinct cosine pair is scored. Equal scores use the saved family order
of the two nodes for deterministic ties. Sorted pair data spills into bounded
chunks and is merged with bounded open files, preserving exact global ordering
without a candidate shortlist. This bounds sort memory; total cosine work and
temporary pair storage remain quadratic in family size. State preserves the
selected pairs, scores, total comparison count and original L1 associations.

Progress is saved atomically. A completed resume dispatches no new work;
unfinished native requests follow the runner's existing resume/retry policy.
Failed or malformed results remain unresolved with case-level diagnostics and
retain all original entries; independent families continue. Null pair outputs
are malformed. Null Bootstrap meanings are retained and reported separately
from the non-null entries used for construction. A selected note with no
non-null L1 meaning still blocks root construction. The constructor does not
repeatedly resample null answers.

Runner failures during advancement retry only after checking the existing frozen
state and receipts. Failed execution invocations retry when unsent cases remain
and existing case and latest warmup receipts contain no terminal model failure.
Restarts wait 5, 10, 20, 40, then 60 seconds, continuing at 60 seconds until
recovery or interruption. The same native experiment resumes; successful answers
are reused, and provider/model retry limits are not reset. Invalid evidence,
malformed answers, failed warmups and exhausted explicitly supplied allowances
remain blocked. `runner-backoff.jsonl` records errors, delays and recoveries;
`runner-invocations/` retains each CLI process's stdout and stderr. Cancellation
interrupts the backoff wait; admitted native work follows the existing pause rules.

There is no default model-attempt cap. `--attempt-budget` is available only for
an explicitly supplied allowance, and the same allowance is retained across
resumes. A reviewed `--runner-upgrade-reason` records permitted constructor-code
changes while retaining frozen inputs and producer receipts. Finish active work
before editing or rebinding its source. The saved `run-summary.json` separates
construction status from execution status and lists unresolved cases, skipped
Bootstrap entries and errors.

The existing original-note hierarchy viewer can export a completed or partial
saved V3 graph when requested; construction does not refresh a UI automatically.
Inspection retains the fixed definitions and supporting original L1 references.
Offline fixture results test this workflow, not semantic accuracy or optimality.

## First three-note model trial

The user authorized a three-note V3 test, completed on 2026-10-13. Its
[configuration](../../sse_multivector/hierarchy-runs/v3-three-note-v1/hierarchy.spec.json)
selects the ASv6.100 rocket-stove, lamb-dinner and mushroom-risotto notes, with
9, 8 and 3 original L1 entries respectively. The copied corpus SHA-256 is
`18370b4772fee22c8d11f49a505f20f781f163e0512a8f32473d487ebdc8849a`.
The frozen prompts are Bootstrap-v129 and pair-consolidation-v6, using
GPT-6.1 Sol medium subscription inference and the pinned local CPU SSE model.

Construction completed unattended: 20 original meanings, ten pair proposals,
five final root proposals and three SSE encoding jobs. The resulting graph
has five roots, 17 nodes and 12 edges; all three notes are represented, every
leaf represents at most two distinct notes, and no family exceeds six nodes.
Native sources, model receipts, vector receipts and fixed definitions passed
the constructor's offline validation. Construction did not refresh a UI; the
user subsequently requested the review export below. No human quality approval
is recorded.

The native usage summary records 35 valid cases and 36 fresh attempts including
one Bootstrap prefix warmup: zero failures, retries, missing usage or answer
reuses. It reports 87,268 input tokens, including 47,360 cached input tokens,
and 18,190 output tokens, including 7,423 reasoning tokens. The complete saved
API-equivalent catalogue estimate is $0.361172; it is not a subscription cash
charge. Warmup usage is included.

One concrete grouping merits review. The initial selected pairs include
Appreciation / Satisfaction at cosine 0.642221 and J-tubes / Enjoyment of
experimentation at cosine 0.070914. The final C00004 heading is Behavior and
mental life and its meaning also admits equipment supporting people's actions.
Its four associated original entries are those two pairs. The low-scoring pair
was still selected under the approved rule of pairing every available node.
This records the construction witness; it does not assign a semantic error to
Bootstrap, SSE, consolidation or the pairing rule. The Food and meals / Food
roots and the broad Activities and supporting resources root also merit browsing
review before a quality claim or larger trial.

Retained source worktree:
`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-v3-three-note-v1`.
Ignored evidence under `target/hierarchy-v3-three-note-v1/` includes
`construction-run-v1/state.json`, native `batch-*/experiment/` receipts,
`encoding-*/` worker receipts, `usage.json`, `run.log` and the native single-case
`root-c4-evidence.json`. The worktree remains necessary for these frozen source
and model-artifact bindings. Two earlier preparation-only directories failed
before state creation because the supplied history directory did not yet exist;
they made no model calls and are retained separately. This diagnostic has no
official HR identifier.

### Requested review UI

The existing terminal hierarchy viewer was exported on user request. It retains
all 17 canonical nodes, one display-only root and the three full original notes.
The HR05 viewer binary was copied unchanged; its production `--check` passed.
The ignored export includes the checked files and their SHA-256 provenance.

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-v3-three-note-v1/target/hierarchy-v3-three-note-v1/review-ui-v1/launch.sh
```

Use `j` / `k` to select, `l` or Enter to open, `?` for definitions and `q` to exit.
