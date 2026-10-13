# Hierarchy generation V3

Status: approved canonical generation mechanism, implemented as the sole shared
CLI constructor in `sse_multivector/hierarchy_generation.py`, replacing V2.
Offline construction checks pass; model-based hierarchy-quality qualification
remains pending. HR11–HR14 used approved Pair-consolidation-v6. The specificity
revision, Pair-consolidation-v7, is experimental; saved runs and current run
definitions retain V6. This document does not authorize model calls. The user's personal outline,
`docs/notes/MY-NOTES_10-12.md`, remains read-only. The preceding mechanisms are
V2 and V1; earlier variants need no formal naming.

## Approved provisional cutoff for the next run

The user approved a minimum cosine similarity of **0.66** for the next
hierarchy run. Pair eligibility uses the unrounded score: `cosine >= 0.66`.
Retain entries that are not paired, with their meanings, vectors and associated
original local L1 entries, so the cutoff does not silently remove notes.

This is an approved next-run setting. The current constructor has no cosine
cutoff; its implemented pairing behavior is described below. HR11–HR14 retain
their frozen settings and saved evidence. The approval does not establish that
0.66 separates every useful grouping from an unhelpful one.

One decision remains open before implementation: when a family still contains
more than six nodes and no pair reaches 0.66, whether construction should pause
for review or permit the larger menu. No below-cutoff fallback is approved.

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
[[{local L1 subject}]]

{explicit meaning from Bootstrap}
```

The brackets mark the tokens selected for SSE pooling; they are notation rather
than literal text to encode. Pool only the subject. The explicit meaning is
unselected context available to the encoder.

## Step 1.3: cosine pairing within one family

Compute cosine similarity for every unordered pair of distinct vectors in the
current family's construction pool. Use all vectors in that pool, without a
candidate shortlist. Rank those pairs from highest similarity to lowest and
select non-overlapping pairs in that order: once a vector has been selected,
skip subsequent pairs containing it. Continue selecting pairs until no pair of
unused vectors remains. With ten nodes this selects five pairs, not four.
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

Exact answer reuse must match the complete request, including the optional
canonical parent. A root-consolidation answer cannot be reused for a request
with a supplied canonical parent merely because its two input nodes match.

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
parent for each selected pair, following step 1.4. Its inputs are the two
synthetic nodes' subjects and explicit meanings, plus the current canonical
parent when constructing a deeper level. Root construction has no parent.

## Step 1.8: repeat until at most six nodes remain

Repeat steps 1.5–1.7 until there are six or fewer nodes in the sibling family.
Select all the highest-scoring unique pairs as described in step 1.3; do not
limit pairing to force exactly six nodes.

With ten nodes, generate ten SSE vectors and calculate cosine similarity for
all 45 distinct pairs. Select five non-overlapping pairs. If each consolidation
returns a synthetic parent, five consolidation calls produce five synthetic
nodes. Five is within the maximum, so no further consolidation is needed for
that family. These final nodes become canonical; intermediate synthetic nodes
remain outside the canonical hierarchy.

If construction starts with more than six nodes and each consolidation
successfully returns one parent for its pair, the final node count is four,
five or six. The last consolidation starts with seven to twelve nodes: seven
or eight become four; nine or ten become five; eleven or twelve become six.
For seven nodes, three pairs produce three synthetic parents and the unpaired
node carries forward, giving four nodes total. This range is acceptable.

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
consolidate each pair. Generate SSE vectors for the resulting synthetic nodes
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

Use the shared stable launcher from an isolated task worktree. V3 has three
commands: `prepare-hierarchy`, `advance-hierarchy` and `run-hierarchy`. V2's
constructor and its commands are removed; their source remains in Git history.
Historical traversal research and saved-data readers remain available.

The schema-1 construction definition contains `corpus`, `note_ids`,
`local_schema_version` (4), `bootstrap_spec`, `consolidation_spec` and
`worker_config`. Teacher specifications use the existing native prompt/runner
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

Each unchanged subject/meaning encoding is reused within the construction.
SSE text contains the subject, two newlines, then the explicit meaning. Only
the subject's UTF-8 byte span is selected for pooling. The input brackets in
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
