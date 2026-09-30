# HG process — start here

The goal is a useful hierarchy for browsing posts. This is the SP-based process
we are testing on 100 posts, not a settled production workflow. **HG1–HG7** name
its stages; **LG01** names the technique used at HG3, regardless of post count.
The current tests reuse saved HG1–HG2 outputs rather than rerunning SP or MP.
Subsections use **HGx.y** labels, such as **HG3.2** for selecting post pairs.

## Definitions

- **SP subject entry:** a subject in one post's local hierarchy.
- **Hierarchy node:** a node in the combined global hierarchy, representing one or more SP subject entries.

<a id="hierarchy-generation-stages"></a>

## From posts to a combined hierarchy

1. **HG1 — Generate each post's subjects and masks.**

   **HG1.1 — Subjects.** For each post,
   prompt SP to produce its local subject hierarchies and a context description
   for each subject.

   **HG1.2 — Masks.** Then prompt MP for each supplied subject, selecting the
   exact fragments of that post that express that subject.

   A **mask** means only the exact fragments MP selects from the original post
   for that supplied subject. If MP selects no fragments (`[]`), retain that
   SP subject entry and its parent–child relationships; do not delete the entry.
   A post can have several subject trees; their top-level subjects need not be
   equally general or remain top-level in the global hierarchy.

2. **HG2 — Generate two separate types of SSE vector.**

   - **HG2.1 — Subject vectors.** Encode each SP subject's wording by itself:
     its **subject vector**.
     This does not run MP on the subject wording.
   - **HG2.2 — Mask vectors.** Encode the text selected by each nonempty MP mask in the context of its
     original post: its **mask vector**.

   A subject whose MP mask is empty still gets a subject vector, but no mask
   vector. Keep both vector types separate; retain the source posts, subjects,
   masks and SP parent–child relationships.

3. **HG3 — LG01: combine matching SP subject entries into hierarchy nodes.**
   Start with one hierarchy node per original SP subject entry. No model is
   prompted here.

   - **HG3.1 — Combine repeated subjects within one post.** SP can put the same
     subject wording in several places in a post's local subject hierarchies.
     Combine those SP subject entries only if their nonempty MP masks select
     exactly the same parts of that post. Keep all their parent relationships.

   - **HG3.2 — Use mask vectors to select post pairs.** If several SP subjects in one
     post have identical MP masks, count that mask vector once for this search.
     For each mask vector generated from a nonempty MP mask, compute cosine
     similarity against every mask vector from all other posts. Select the
     other-post mask vector with the highest cosine, retaining ties.
     The source posts of those two MP masks become a selected post pair.
     Multiple mask-vector matches selecting the same two posts still produce
     only one post pair. This selects posts to examine; it does not combine
     their subjects yet.

   - **HG3.3 — Compare subject vectors within each selected post pair.** Compare
     every original SP subject vector from the first post against every
     original SP subject vector from the second post. Find each subject's
     highest-cosine subject match in the other post, in both directions.
     Include subjects whose MP masks are empty when finding these best
     subject-vector matches.

   - **HG3.4 — Check both vector comparisons before accepting a subject match.** The
     two subjects must be each other's best match by subject-vector cosine
     within this post pair, with cosine at least **0.90**. The mask vectors from
     their corresponding MP masks must both exist and have cosine at least **0.80**.
     Ties qualify. If a best subject match fails these checks, do not fall back
     to a weaker match. These cutoffs are experimental.

   - **HG3.5 — Combine the SP subject entries that passed into hierarchy nodes.**
     If entry X matches Y, and Y matches Z, combine all three into one hierarchy node,
     even if X and Z did not pass a direct comparison. Retain each original
     SP subject entry, its MP mask and its SP relationships; do not blend their
     subject vectors or mask vectors. SP subject entries without a passing match
     remain represented by separate hierarchy nodes.

   **HG3.6 — Preserve SP relationships and check cycles.**
   Preserve every original SP ancestor relationship as either a path between
   the resulting hierarchy nodes or a relationship inside one combined node.
   If within-post combinations alone create a cycle between distinct hierarchy
   nodes, stop. If cross-post combinations create a cycle, undo every involved
   cross-post combination; never delete an SP relationship to repair it.
   LG01 does not add missing relationships between parent hierarchy nodes.
   See the [detailed LG01 rules](../subject-order-probe.md#lg01--subject-hierarchy-merging).

## From combined nodes to further relationships

4. **HG4 — Select pairs of parent hierarchy nodes for model comparison.** Look
   for a hierarchy node representing SP subject entries from at least two
   posts. If that node has two or more distinct immediate parent hierarchy
   nodes, select every pair of those parents for HG5. Count each pair of
   hierarchy nodes once, even if several shared children select it. Identical
   node names do not make two hierarchy nodes the same node.

   **Visual example: N037 and N072.** Parents are above children in these diagrams.

   **1. SP supplies two separate local hierarchies.** Every item here is an
   SP subject entry:

   ```text
          N037                       N072

    Food ingredients          Baking ingredients
           │                         │
      Cranberries               Cranberries
       entry #1                  entry #2
   ```

   **2. HG3 combines the two Cranberries entries.** Now these boxes are global
   hierarchy nodes:

   ```text
    ┌──────────────────┐     ┌────────────────────┐
    │ Food ingredients │     │ Baking ingredients │
    └────────┬─────────┘     └─────────┬──────────┘
             │                         │
             └────────────┬────────────┘
                 ┌────────┴────────┐
                 │   Cranberries   │
                 │ entries #1 + #2 │
                 └─────────────────┘
   ```

   **3. HG4 selects the two parents—not the child.**

   ```text
    ┌──────────── SELECTED FOR COMPARISON ────────────┐
    │                                                 │
    │ Food ingredients     vs     Baking ingredients  │
    │                                                 │
    └─────────────────────────────────────────────────┘

    Cranberries is WHY this pair was selected.
    Cranberries is NOT one of the two nodes compared.
   ```

   HG4 adds that pair to the comparison list for HG5. **The hierarchy itself
   remains unchanged.** The shared child does not decide how its parents relate.

5. **HG5 — Prompt BCPv4 for each selected hierarchy-node pair.** Use
   **BCPv4** (tested, not frozen) with **Astra low**.

   **HG5.1 — Model input.** The model receives the
   original SP subject wordings and SP context descriptions represented by
   each of the two hierarchy nodes. A combined node can supply several such
   entries; remove only exact duplicate subject/context entries. Do not send
   whole posts, MP masks, subject vectors, mask vectors or the shared child
   to this prompt.

   **HG5.2 — Model output.** The model returns equivalent, A ancestor of B, B ancestor of A, neither,
   or uncertain, plus a reason. A and B identify the two hierarchy nodes,
   not the source posts. Save the answer without changing the hierarchy yet.

   **Visual example: the pair selected in HG4.** Each hierarchy node represents
   one SP subject entry in this example.

   **1. HG5 prepares the model input:**

   ```text
   ┌── A: Food ingredients ─────────────────────────────────┐
   │ Subject: Food ingredients                              │
   │ Context: The post names cranberry, rosemary, brown     │
   │ sugar, and cinnamon as ingredients in the sourdough    │
   │ bread.                                                 │
   └────────────────────────────────────────────────────────┘

   ┌── B: Baking ingredients ───────────────────────────────┐
   │ Subject: Baking ingredients                            │
   │ Context: The post names fresh rosemary, cranberries,   │
   │ and currants in discussing soda bread.                 │
   └────────────────────────────────────────────────────────┘
   ```

   Cranberries, the hierarchy links, masks and full posts are **not sent**.

   **2. Both lists go into ONE call using [BCPv4](BCPv4.md) / Astra low.**

   **3. The saved JSON answer contains these fields:**

   ```text
   ┌── MODEL ANSWER ────────────────────────────────────────┐
   │ relation: a_parent_of_b                                │
   │                                                        │
   │ reason: Baking ingredients are a specific subset of    │
   │ food ingredients; the examples in the descriptions     │
   │ do not limit either subject's broader scope.           │
   └────────────────────────────────────────────────────────┘
   ```

   That means **Food ingredients is an ancestor of Baking ingredients**, not
   necessarily its immediate parent.

   HG5 **saves this answer without changing the hierarchy**. Applying ancestor
   answers happens at the proposed HG8 stage.

6. **HG6 — Combine hierarchy nodes judged equivalent at HG5.** Combine
   connected chains of equivalent node pairs. The resulting hierarchy node
   retains all contributing SP subject entries, context descriptions, MP masks
   and original SP relationships. Preserve SP ancestry and stop if the
   combinations create a cycle between distinct hierarchy nodes. No new
   prompt call or replacement-title generation happens here.

7. **HG7 — Recompare previously judged node pairs whose prompt inputs changed.**
   **HG7.1 — Update comparison pairs.** After HG6, replace each old node reference with its resulting combined-node
   reference. Drop a comparison if both sides now refer to the same hierarchy
   node. Count repeated pairs of resulting hierarchy nodes once.

   **HG7.2 — Reuse or recompare.** Rebuild each remaining pair's subject/context lists for BCPv4. Reuse its
   saved answer only if the exact prompt input and model settings still match.
   If the input changed, prompt **BCPv4 / Astra low** with the current lists.
   Combining nodes can add subject/context entries, so changing an old answer's
   node IDs is not enough to make that answer valid for the combined nodes.

## Apply answers, then browse

### HG8.1 — Apply ancestor answers (proposed HG8)

After HG7, the tested exporter uses saved, valid answers to add ancestor
relationships between hierarchy nodes, alongside the preserved SP relationships,
in a separate hierarchy. An A-ancestor-of-B answer means B is beneath A, but
other hierarchy nodes may sit between them. Neither and uncertain add no
relationship and do not delete existing SP relationships. A new equivalent
answer requires a separate HG6 decision. The exporter stops on conflicting
relationships; it does not choose a repair. This export makes **no model calls**.
Its proposed HG8 label and general conflict policy are not settled.

### HG8.2 — Browsing links (proposed HG8)

For browsing, omit a direct link between two hierarchy nodes only when another
path connects those same nodes. For example, show **Food → Bread → Sourdough
bread**, without a redundant Food → Sourdough bread shortcut. Keep every
hierarchy node, multiple parent routes and original relationships in the
underlying data. Each node's directly associated MP masks stay unchanged;
new ancestor links can provide additional routes to posts through child nodes.

## What is still missing?

HG4 is not a complete comparison-selection rule. A later test selected pairs
of top-level hierarchy nodes sharing a descendant hierarchy node at any depth.
Its **nine Food calls were HG5 comparisons of the Food node against nine other
hierarchy nodes**, not comparisons of those nine nodes against one another.
That shortlist is experimental, not an adopted replacement for HG4.

Selecting further comparisons, deciding when to repeat HG6–HG7, and general
conflict handling remain open. The tests preserve the saved LG01 hierarchy;
they do not establish a finished global hierarchy. This process does not use
HDBSCAN, TRUE/Jev, or a separate title-generation pass.

---

## BCPv4 — one-pair subject comparison

Status: **user-approved wording, tested on 49 original pairs, seven changed
combined-input pairs and nine further Food pairs, not frozen**. The user
approved six Astra-low calls, then the remaining 43 nominated comparisons.
All 49 returned valid JSON. Agent review accepted the first six; of the next
43, 36 were accepted and seven flagged as uncertain across four issues below.
These are agent assessments, not user decisions or a measured general accuracy
rate. HG6–HG7 subsequently tested an isolated combined-node preparation below.
The authorized [ancestor-application test](#saved-ancestor-application-test)
then applied 13 current ancestor answers in a separate view. A subsequent
[nine-pair Food test](#recovered-food-comparisons) returned nine ancestor answers,
now applied in a [separate continued export](#extended-food-test-export).
The saved LG01 hierarchy is unchanged; production adoption
and general conflict handling remain open.

[BCPv4.md](BCPv4.md) compares the subjects represented by two hierarchy nodes,
A and B. Each node represents SP subject entries originating in one or more
posts; their subject wordings and context descriptions form the prompt input.
The source posts themselves are not being compared. JSON output
is required. Whether the saved context
descriptions improve the judgments remains untested; including them is a trial
input choice, not a validated requirement.

[BCPv3.md](BCPv3.md) is the unchanged, untested delta baseline. BCPv4 clarifies
the distinction between a hierarchy node, its subject entries and their source
posts; the input fields, relation definitions and JSON output remain unchanged.
Earlier [BCPv2.md](BCPv2.md) and [BCPv1.md](BCPv1.md) remain the baselines for the
input reduction and narrowing from whole branches to one pair. These are not
previously approved prompts. Revision receipts record the exact changes.

The proposed candidate source is distinct pairs of immediate parents of an
LG01 node shared across posts, deduplicated by node identity. Sharing a child
nominates a comparison; it does not establish equivalence or containment.
The read-only investigation of the [LG01 100-post run](../subject-order-probe.md#smv2-100--unchanged-rules-on-all-100-posts)
did not adopt this as a construction rule or authorize model calls.

## Proposed HG8 — apply ancestor relationships

Status: **ancestor interpretation and browsing-link rule agreed and tested in
an isolated export; general application policy remains a draft**. HG8 is a proposed
label, not an extension of the approved HG1–HG7 labels. The separate test below
stops on conflicts; it does not implement this draft's cycle-withholding policy.
The prompt, response labels and saved LG01 hierarchy remain unchanged.

BCPv4 calls its answers `a_parent_of_b` and `b_parent_of_a`, but defines them
as one subject being a more specific topic within the other's scope. The user
agreed to treat these as **ancestor relationships**, not proof of immediate
parenthood. Other hierarchy nodes may sit between the compared nodes.

1. Start from the combined nodes and mapped SP links after HG6. Retain every
   original subject, mask and SP relationship as provenance. Check that SP
   ancestry is preserved as ancestor-or-equal and that distinct nodes form no
   cycle. If the merges already violate these conditions, stop and report the
   problem; the link-application stage must not repair those merges.
2. Use HG5 answers for unchanged inputs and HG7 answers for changed inputs.
   An answer must match the current A/B subject/context entries and the fixed
   prompt/model settings. Reusing a node's old answer merely by replacing its
   ID is not valid. Missing, invalid or stale answers remain unjudged; they
   are not treated as `neither`.
3. Translate the current answers into proposed ancestor relationships:

   | Answer | Action at HG8 |
   | --- | --- |
   | `a_parent_of_b` | Record A as an ancestor of B; not necessarily its immediate parent. |
   | `b_parent_of_a` | Record B as an ancestor of A; not necessarily its immediate parent. |
   | `neither` | Propose no additional ancestor relationship; retain the answer. |
   | `uncertain` | Propose no additional ancestor relationship; retain the unresolved answer. |
   | `equivalent` | Belongs to HG6, not an ancestor relationship. Newly returned HG7 equivalences remain pending; no automatic repeat of HG6–HG7 has been selected. |

4. Check all proposed ancestor relationships together with the existing SP
   relationships. Arrows in this check represent ancestry, not immediate
   parent placement. Withhold every new relationship that participates in a
   directed cycle, retaining the answers and the conflicting paths for review.
   Keep all existing SP relationships and all other proposals; deduplicate
   identical relationships. Do not select a winner by call order, delete an SP
   link, or infer an equivalence from a cycle of strict-ancestor answers.
5. Save the resulting ancestor relationships separately from the LG01 baseline.
   Record which answer supplied each new relationship, which proposals were
   withheld, and any disagreements between answers and the resulting ancestor paths.
   No node removal, replacement titles, membership expansion or display
   collapsing is part of this draft.

For example, the saved Food ingredients / Baking ingredients parent answer
would record **Food ingredients as an ancestor of Baking ingredients**. It
does not establish that Baking ingredients belongs immediately beneath Food
ingredients. Both nodes retain their SP relationships. If SP supplies A → B
and the model proposes B → A, withhold the new B → A relationship and record
the disagreement. If two new relationships jointly form a cycle, withhold
both rather than accepting whichever was processed first.

The proposed conflict policy needs explicit approval: a `neither` answer does
not remove an SP path or veto a path supplied by other parent answers. Such
disagreements are recorded, not silently resolved. Cycle checks establish
structural validity, not semantic correctness. HG6 merge handling and any
repeat rule for equivalences found at HG7 remain separate open decisions.

The user agreed to the following browsing-link rule, recorded as
[HD22](../../docs/planning/release-decisions.md#sp-based-hierarchy-rules):
omit a direct link A → B from the browsing view when another path of at least
two links connects A to B. Derive the view from the complete acyclic ancestor
graph, not by selecting one longest chain. Retain every node, multiple parent
routes, and all original relationships and provenance in the underlying data.
This is a browsing simplification, not deletion of source relationships.

For N037's saved Food → Bread → Sourdough bread branch, a separate
Food → Sourdough bread browsing link is redundant. Keep the route through
Bread and preserve Food's ancestor relationship with Sourdough bread.
The rule is implemented in the separate ancestor-application test; earlier
LG01 browser outputs remain unchanged. It never removes a hierarchy node.

## Input and output

Use the shared runner's [saved subject-pair adapter](../model-runner.md#saved-subject-pair-preparation)
with saved source paths and explicit A/B node IDs. It assembles `INPUT_JSON`
automatically; do not copy source entries into a case file. Keys `A` and `B`
identify the two nodes. Each value is a list containing only `subject` and its
saved `context`. The adapter retains every distinct subject/context pair and
removes only exact duplicates, without choosing a representative wording or
rewriting descriptions.

Keep node/post IDs, SP numbers, masks, byte spans, full posts and the mapping of
`A`/`B` to the original nodes in review evidence, outside the model input. Do not
send empty mask arrays or image URLs as separate fields. This reduces the model
input; it does not delete source data or omit subjects with empty masks.

Supply source evidence, not expected answers, previous model decisions or
cosine scores. Do not send the whole branches or graph. Keep the shared-child
references that nominated the pair in review evidence, outside the model input.
The model compares the subjects represented by the two nodes, not the source
posts, a new subject inferred only from masks, or a subject narrowed to the
examples in the context descriptions.

The output is a JSON object with exactly two string fields:

- `relation`: `equivalent`, `a_parent_of_b`, `b_parent_of_a`, `neither`, or
  `uncertain`.
- `reason`: one short justification.

The [six-pair experiment spec](../experiment_specs/lg01-bcpv4-six-pairs-astra-low-v1.json)
uses the shared runner's existing output JSON Schema validation. The adapter
can now derive an isolated combined-node preparation; it does not apply ancestor
answers or change the LG01 baseline. A
pairwise judgment does not check global graph consistency or authorize
overriding an SP relationship. LG01's preservation rules are unchanged.

## Six-pair test

Unchanged BCPv4 was run with `openai-codex / gpt-6-astra / low`, concurrency 3,
and six maximum new attempts. Six calls completed, without retries, reused
answers, earlier-prompt baseline calls or paid API fallback.

The six pairs were selected from the 49 distinct immediate-parent pairs found
in the saved LG01 100-post run. They cover same-wording and different-wording
equivalence, broader/narrower subjects, and overlapping subjects. The Food node
retained all 27 distinct subject/context entries. Expected relations and shared
children were not sent to the model.

The ignored artifact directory is
`target/branch-comparison-v1/bcpv4-six-pairs-v1/`. Its `cases.json` preserves the
source entries, full posts, node IDs, shared-child evidence and source hashes;
`experiment/` contains frozen inputs/settings, raw receipts, runner-generated
reports and separate agent reviews. The prompt and saved LG01 inputs/results
were hash-checked unchanged. No new subjects, masks, vectors or hierarchy
were generated.

The original test used the generic adapter. The reusable spec now uses
`subject_pairs` and a [small source/pair selection file](../experiment_specs/lg01-bcpv4-six-pairs-v1.json).
Offline preparation under `target/branch-comparison-v1/bcpv4-six-pairs-adapter-v1/`
reproduced all six prompts byte-for-byte with unchanged model settings and
identified six reusable saved answers. No new calls or results were generated.
Deriving review evidence from SP edges corrected B04's previously swapped
shared-child A/B post labels (Meals: N023; Food: N096). That metadata was never
sent to the model; the original experiment remains untouched.

The judgments preserved the Food ingredients / Baking ingredients distinction
despite both contexts discussing bread, and did not mistake shared subjects for
full containment. This selected sample supports further testing, not freezing
the prompt or claiming a validated placement stage. Whether context descriptions
help remains untested: there was no context-free comparison. No case exercised
the `uncertain` response.

## Remaining 43-pair test

The user authorized the remaining comparisons with unchanged BCPv4/Astra low.
The [spec](../experiment_specs/lg01-bcpv4-remaining-pairs-astra-low-v1.json) uses
the subject-pair adapter and [explicit source/pair selection](../experiment_specs/lg01-bcpv4-remaining-pairs-v1.json).
Offline checks confirmed that the six prior pairs plus these 43 exactly cover
the 49 pairs nominated by distinct immediate parents of cross-post shared LG01
nodes. Selection, source data, prompt and model settings were not changed.

All 43 subscription calls completed with valid JSON, no retries or reuse, and
no paid API fallback. Earlier pairs were not rerun. The runner-generated report,
receipts and separate agent reviews are under
`target/branch-comparison-v1/bcpv4-remaining-pairs-v1/experiment/`.

Agent review accepts 36 judgments and flags seven for user review:

| Cases | Issue |
| --- | --- |
| B20, B21, B30, B46 | Dining contains Meals twice, but neither contains the other twice. B22 equates the Dining nodes and B29 equates the Meals nodes, so these judgments are jointly inconsistent. The correct relation is not yet adjudicated. |
| B17 | Coffee / Coffee shops: neither was selected. Review whether beverage versus establishment is too narrow a reading of topic containment; B27 accepts dedicated food-smoking equipment beneath Food smoking. |
| B37 | Dietary practices / Diets: equivalence may erase a broader practices-versus-diets distinction; both can also mean approaches to eating. |
| B49 | Food ingredients / Vegetables: the parent judgment may be reasonable, but its justification narrows Vegetables to those "used in cooking." Review the full supplied scope. |

The seven flags are not seven proven failures. The model itself used no
`uncertain` answers; these flags are the reviewing agent's judgments. No prompt
revision, graph changes or new application rule follows automatically.

## HG6–HG7 combined-input test

The user authorized preparation of the proposed HG6 merges followed by seven
changed HG7 comparisons, with BCPv4 / Astra low unchanged. The shared
[source-reference spec](../experiment_specs/lg01-bcpv4-combined-pairs-v1.json)
uses the [reusable adapter](../model-runner.md#saved-subject-pair-preparation);
no case payloads, rendered prompts or review files were assembled manually.
Artifacts are isolated under
`target/branch-comparison-v1/bcpv4-hg6-hg7-v1/experiment/`.

The 14 saved equivalence answers combine 23 original nodes into ten combined
nodes: 1,766 becomes 1,753. Every original SP entry/mask remains represented,
SP ancestry survives as ancestor-or-equal, and there is no SP cycle. These are
mechanical checks, not validation of the 14 semantic judgments. In particular,
the earlier Dietary practices / Diets flag remains unresolved and retained.
The original LG01 inputs and hierarchy were not edited.

After combination, 14 old comparisons are internal to a node. The other 35
comparisons become 26 distinct current pairs: 19 unchanged and seven changed.
The preparation freezes the 19 earlier answers with their settings and receipt
references; only the seven changed inputs become model jobs. Three unchanged
requests had an older transport identity, so keeping them as saved judgments
avoided baseline reruns without weakening executor-cache validation.

All seven subscription calls returned valid JSON, with no retries, old-input
reruns or paid API fallback:

| Combined comparison | HG7 answer |
| --- | --- |
| Food/Foods / Dining | Food is an ancestor. |
| Food/Foods / Meals | Food is an ancestor. |
| Food/Foods / Cooking fats | Food is an ancestor. |
| Food/Foods / Diet and nutrition | Food is an ancestor. |
| Food/Foods / Cooking ingredients | Food is an ancestor. |
| Food/Foods / Food ingredients | Food is an ancestor. |
| Dining / Meals | Neither. |

Dining now includes both contexts: enjoying dinner and taking someone out for
dinner. Meals includes both saved dinner contexts. The new answer distinguishes
the dining activity/experience from meals as food or eating occasions. This
replaces conflicting old-input answers for the current pair, but does not prove
that interpretation correct. No new equivalence was returned; no automatic
repeat rule was needed or adopted. Ancestor answers were not applied during
HG6–HG7; the separate export below uses their completed results.

## Saved ancestor-application test

The user approved a separate hierarchy using the 26 current judgments, followed
by the agreed browsing-link simplification and inspection of its Food branch.
The read-only preflight found 13 ancestor answers and 13 `neither` answers,
without cycles or conflicts with preserved SP ancestry or each other.

The shared runner's [saved hierarchy export](../model-runner.md#saved-subject-hierarchy-export)
revalidates the frozen preparation, current model inputs, settings and receipts.
It applies all 13 ancestor proposals in a fresh directory and retains all
1,753 nodes and 2,383 original SP entries. The 1,661 mapped SP links plus 13 new
links remain in the underlying graph; the browsing view omits 15 redundant
links, preserving identical ancestry and multiple parents. No new inference,
titles or direct mask/post memberships were added. Artifacts are under
`target/branch-comparison-v1/bcpv4-ancestors-v1/run/`.

The exporter refuses a cycle, a `neither`/ancestry conflict or a newly returned
equivalence rather than choosing a repair policy. Missing, invalid or stale
judgments also stop export. This is a test guard, not approval of the broader
HG8 draft or a rule for production conflict resolution.

Food/Foods now connects to Dining, Meals, Cooking fats, Diet and nutrition,
Cooking ingredients and one Food ingredients node. Its recursive post count
changes from 48 to 50, but its direct membership is unchanged. Seven Food
preparation nodes, Food appreciation and three other Food ingredients nodes
remain outside that Food branch. No names-based combination was performed.
These are agent observations of a partial hierarchy, not user quality approval.

## Recovered Food comparisons

Status: **authorized test completed; answers applied only in a separate continued export**. Unchanged BCPv4 /
`openai-codex / gpt-6-astra / low` compared Food/Foods (`S0022`) with nine
disconnected Food nodes in the separate 100-post test hierarchy. The provider,
schema, concurrency 3 and timeout 300 seconds match the HG6–HG7 test.

The read-only nomination measurement paired distinct top-level nodes when they
shared any strict descendant, at any depth, including single-post descendants.
It found 393 pairs in the 456-root test graph: six had current saved answers,
leaving 387 comparisons. Nine of the 11 identified Food gaps qualified; the
bagel-making and pie-making Food preparation branches did not. This measured
rule is not adopted as HG4 or as a complete construction policy.

The user authorized only those nine recovered Food comparisons, not all 387.
The [source/pair selection](../experiment_specs/lg01-bcpv4-food-ancestors-v1.json)
references the saved ancestor-test graph and original SP inputs; the
[experiment spec](../experiment_specs/lg01-bcpv4-food-ancestors-astra-low-v1.json)
uses the existing `subject_pairs` adapter. It assembles and freezes the inputs,
posts, masks and provenance without manually copied cases. The model receives
only subject/context arrays: 31 distinct entries for Food/Foods and one for each
compared node. Shared-descendant information is not added to the prompt.

All nine new subscription calls returned valid JSON, with no reuse or failures.
Every answer was `a_parent_of_b`, meaning Food/Foods is an ancestor of B:

| Case | Compared node B | Source post |
| --- | --- | --- |
| F01 | S0142 — Food preparation | N007 |
| F02 | S0244 — Food preparation | N013 |
| F03 | S0290 — Food preparation | N015 |
| F04 | S0299 — Food preparation | N016 |
| F05 | S0524 — Food preparation | N026 |
| F06 | S0767 — Food ingredients | N037 |
| F07 | S0776 — Food appreciation | N037 |
| F08 | S0953 — Food ingredients | N046 |
| F09 | S1954 — Food ingredients | N083 |

The shared workflow saved the exact requests, outputs, validation and usage at
`target/branch-comparison-v1/bcpv4-food-ancestors-v1/experiment/`. The comparison
run changed no prompt, LG01 matching rule, source hierarchy or browsing export.
The subsequent application test below uses those saved answers. These nine
answers support the usefulness of the recovered comparisons on this selected
sample; they do not validate all 393 pairs or authorize broader inference.

## Extended Food test export

The user authorized applying the nine saved answers and inspecting Food, with
no new inference. The shared runner's `export-hierarchy --base` replays and
validates the original ancestor-test export, verifies the nine comparisons
against its exact nodes, and writes a separate test hierarchy at
`target/branch-comparison-v1/bcpv4-food-ancestors-v1/hierarchy/`. The earlier
export, saved LG01 data and model receipts remain unchanged.

All nine links passed the joint cycle and `neither`/ancestry checks. The export
retains 100 posts, 2,383 subject entries, 1,753 nodes, 1,674 mask vectors and all
direct post memberships. It has 447 top-level nodes, down from 456; its 1,683
underlying links include the original 1,661 SP links and all 22 ancestor answers.
The browsing view omits 15 redundant links, leaving 1,668, with identical ancestry.
It retains all 35 current judgments, including the earlier 13 `neither` answers.

Food/Foods still directly contains 31 posts and recursively reaches 50. Its
immediate browsing children increase from 46 to 55. The nine newly linked
branches supply additional browsing routes, not new posts. Five distinct Food
preparation nodes and four Food ingredients nodes now appear beneath Food; no
equal-name combination was performed. Three of those five preparation nodes and
all four ingredients nodes have empty masks, explaining part of LG01's refusal
to combine them. Empty-mask entries cannot pass its nonempty-mask matching rule.
The other two preparation nodes select `fix` and `prepared`, respectively;
matching subject names alone did not combine their different mask evidence.

The N046 Food preparation → Bagel making branch and N083 Food preparation →
Pie making / No-bake food preparation branch remain top-level. They were outside
the shared-descendant shortlist and received no new comparison. Thus this test
repairs the nine nominated browsing relationships, not all missing placements
or repeated-node clutter. These are agent observations, not user quality approval.

## Next step

Suggested, not started: inspect whether the existing comparison-selection rules
can nominate the repeated Food preparation and Food ingredients siblings before
expanding inference. The
[HG8 draft](#proposed-hg8--apply-ancestor-relationships) still requires review of
general conflict handling. Keep the saved LG01 hierarchy unchanged.

## Design references

The draft follows the existing
[SP hierarchy rules](../../docs/planning/release-decisions.md#sp-based-hierarchy-rules),
particularly HD08–11 and the open placement question HD21. Drafting a one-pair
prompt does not settle the placement question or change those rules.

The [official OpenAI reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively)
informed the direct task, delimited evidence and explicit output choices, without
worked examples or a prescribed reasoning trace. This is guidance for the draft,
not evidence that it works.
