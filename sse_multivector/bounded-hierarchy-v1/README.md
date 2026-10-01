# HG100-SOL01 — bounded build of the saved 100-post hierarchy

This process builds a separate browsing hierarchy from the saved **LG01
100-post run**. It does not regenerate SP, MP, SSE or LG01, and does not edit
previous hierarchies. The user authorized autonomous design and execution on
September 30, 2026, using **GPT-6.1 Sol**, with **2,000 new model attempts maximum**.
The numeric policies below are this build's explicit design decisions, not
claims that these values are universally optimal.

## Terms

- **SP subject entry:** one subject in one post's local hierarchy.
- **Hierarchy node:** one or more SP subject entries represented together in
  the combined hierarchy.
- **Mask:** only MP's selected fragments of the original post.
- **Subject vector:** SSE's encoding of the subject wording alone.
- **Mask vector:** SSE's encoding of an MP selection in the original post.

## The complete process

### HG1–HG3 — reuse the saved starting data

Use the original LG01 result, not a later Astra placement test. It contains
100 posts, 2,383 SP entries, 1,674 distinct nonempty masks and 1,766 hierarchy
nodes. Its 478 roots are starting points, not asserted global top-level subjects.
Preserve all SP relationships as ancestor-or-equal, including multiple parents
and entries whose MP result is empty. All original vectors remain separate.

### HG4.4 — build small candidate lists

For every distinct SP subject wording in a source post, find a nearby hierarchy
node not already represented in that post. This is subject-vector retrieval,
not a semantic relationship judgment. Include the post's own current nodes too.

From each retrieved node, inspect its current parents, including original SP
links and previously verified links: at most two parent steps, three parents
per inspected node, and eight visited nodes including the retrieved node.
Combine the results, keeping at most 60 candidate nodes per source post.
Rank by the number of distinct source-post subject wordings supplying the
candidate, then retrieval rank, parent distance and stable node ID. None of
these scores authorizes a merge or placement. Cap this ranked pool before
checking existing relationships. Candidate eligibility checks have a
2,048-operation allowance in each direction, including adjacency inspection;
an uncertified pair is excluded and recorded, not
assumed unrelated. Precompute the three-parent frontiers once per snapshot,
rather than sorting a wide parent set at every visit.

A hierarchy node is scheduled with its earliest original source post. Every
query retains its stable node ID. Existing relationships and previously judged
pairs are excluded from nominations. Matching wordings select comparisons;
they do not automatically combine nodes.

Retrieval has an indexed implementation and a small-corpus exact reference.
Index parameters and library identity belong in preparation provenance. The
exact reference must refuse unbounded larger inputs; it is not the production
million-post search. No full pairwise similarity matrix is needed.

### HG5.2 — nominate, then check

**PCPv2** receives up to 16 queried nodes and the bounded candidate list.
Candidate records supply IDs and at most two original subject wordings, not
all historical contexts. Query records supply bounded original SP evidence.
It nominates zero through three promising equivalent or ancestor comparisons
per query. It must not invent nodes or force a match. Nominations are not
accepted relationships.

**BCPv5** checks the nominated actual node pairs, using BCPv4's unchanged five
relation meanings: equivalent, A contains B, B contains A, neither, uncertain.
Parent answers mean ancestor containment, not necessarily an immediate parent.
Each batch contains at most 16 pairs. Every answer includes a short reason.

Both stages use JSON and a maximum of 4,000 tokens for the **actual rendered
prompt**, counted with `o200k_base`. This is a reproducible input-size proxy,
not exact provider billing. An oversized individual input stops preparation
with its identity and limit; it is never silently truncated. Duplicate unordered pairs are
checked once, and verified unchanged requests/answers are reused.

### HG5.3 — keep node evidence bounded

The earliest original SP entry is the node's fixed comparison reference.
Add the earliest entry with a different subject wording; if none exists, add
the earliest entry with a different context. At most two original entries are
sent. The second is a check, not permission to change the reference's scope.
Source context may disambiguate wording but must not narrow a broad heading
to the described example. Contradictory evidence calls for uncertainty.

This deliberately changes the older all-entry BCPv4 input policy. It relies on
LG01's provisional assumption that combined entries share a meaning and can
miss mixed-scope members. Keep every constituent entry, context, source post,
mask and vector in provenance; bounded comparison evidence is not deletion or
proof of homogeneous membership. The browser exposes the underlying entries.

### HG6–HG8 — apply verified answers reproducibly

Apply equivalent answers first in sorted pair-ID order. Combine only when the
result preserves original SP ancestry and cannot introduce a cycle or contradict
retained judgments. Keep the earliest SP reference and all original members.
An explicit model ancestor answer asserts different scope, so equivalence
merges must not collapse its two endpoints. Original SP ancestry may become
equality; the two kinds of relationship are not interchangeable.
Then apply verified ancestor answers in sorted order. Neither and uncertain
answers do not create links. Conflicting or uncertified proposals are recorded
as deferred; never delete an SP relationship to make a proposal work.
Each pass reconsiders the saved answers against the current node identities;
it does not create new model receipts for those applications. Earlier accepted
links remain in the starting graph. Deferred graph applications can become
eligible after the graph changes. Every snapshot and original answer remains
available for replay under a different documented policy.

Each proposal has a structural work allowance of 20,000 inspected operations,
including adjacency and existing-judgment work. Exhaustion means deferred,
not accepted. Check retained neither judgments through an endpoint index only
where the proposal could create new ancestry. Local checks and lazy node identity mapping avoid reconstructing
the entire graph for each decision. Validate the full DAG at snapshot export.

For browsing, omit a direct link when another path supplies the same ancestry.
Retain that relationship in the underlying graph. Keep multiple parent routes;
do not choose one longest path, hide nodes, or collapse identical post sets.
The existing browser's full reachability calculation is a 100-post snapshot
operation, not a million-post browser-export implementation.

### HG4.5 — bounded follow-up and completion

Run at most three documented passes: first all nodes; second current roots and
nodes affected by accepted changes; third remaining roots. Stop earlier if a
pass makes no accepted change. Each original reference has at most three
nomination opportunities per pass, nine over the build. Follow-up work shares
the same call budget; exhaustive sibling/parent pair expansion is not added.

The shared runner reserves an attempt **before** transport invocation in one
persistent cross-experiment counter. Provider retries and interrupted launches
count; exact-request reuse does not. Never exceed 2,000. Use only the existing
subscription route with `gpt-6.1-sol`, low reasoning, no paid API fallback.
Preparation freezes the JSON output schemas; the shared validator additionally
checks every supplied query/pair ID and nomination quota.

Completion means the documented finite build has run, the final snapshot and
receipts are exported, every source entry remains represented, and mechanical
invariants and browser validation pass. It does not mean every possible parent
was discovered. Retain unresolved decisions visibly and distinguish them from
unrun work or provider failures. Do not call a budget-interrupted build complete.

## Reproduction and evidence

The shared experiment workflow owns source loading, batching, preparation,
execution, request reuse, validation, graph application, usage and export.
The build manifest pins source hashes, policy, prompt IDs, model settings and
code identities. Run artifacts are ignored; reusable code, tests, prompts and
this maintained process are version controlled. A rerun can replay saved
answers deterministically; fresh model calls remain nondeterministic.

The original discovery investigation found a saved valid parent in the bounded
lists for eight of ten studied roots. This is candidate availability in a
selected sample, not measured nomination or placement accuracy. Missing cases
remain part of evaluation, not grounds for hand-edited placements.

## Run the documented build

Preparation is offline; only `run` sends model requests. The dependencies in
`requirements.txt` pin the indexed search and token counter. On Anvil, the
Python wheels also need the existing GCC and zlib runtime libraries:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
env LD_LIBRARY_PATH=/nix/store/1xw5xccqqh1xw3mvd70hyil6x418wxcm-gcc-14.3.0-lib/lib:/nix/store/ri9paa3mri4kqakljak8ldvbcp7lpmif-zlib-1.3.1/lib \
  OPENBLAS_NUM_THREADS=4 \
  uv run --offline --no-project --python python3.13 \
  --with-requirements sse_multivector/bounded-hierarchy-v1/requirements.txt \
  python -m sse_multivector.experiment prepare-bounded-hierarchy \
  target/hg100-sol01 \
  --spec sse_multivector/bounded-hierarchy-v1/HG100-SOL01.json
```

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
env LD_LIBRARY_PATH=/nix/store/1xw5xccqqh1xw3mvd70hyil6x418wxcm-gcc-14.3.0-lib/lib:/nix/store/ri9paa3mri4kqakljak8ldvbcp7lpmif-zlib-1.3.1/lib \
  OPENBLAS_NUM_THREADS=4 \
  uv run --offline --no-project --python python3.13 \
  --with-requirements sse_multivector/bounded-hierarchy-v1/requirements.txt \
  python -m sse_multivector.experiment run target/hg100-sol01
```

`show target/hg100-sol01` reports the persistent attempt count, completed
passes, unresolved work and the final browser export without inference.
Individual cases remain inspectable in each pass's ordinary discovery and
comparison experiment.

## Offline candidate measurements — RCMv1

`measure-root-candidates` measures an additional candidate-search option against
a saved build. It does **not** adopt that option, prepare an inference run, send
requests, change the hierarchy, or reset the completed build's pass/quota limits.
Another model pass needs separate authorization and a versioned policy.

Measure both querying every current hierarchy node and, for the root-only
follow-up, querying only current roots. The latter directly targets the crowded
starting view; it does not nominate new parents for internal nodes. Unqueried
nodes and existing relationships remain in the saved hierarchy.
Candidate nodes are current roots:
nodes with no parents in the underlying graph, not an artificial browsing root.
Compare their **subject vectors**, using at most two original SP wordings per
node. This does not assert that roots have equal generality or that a high cosine
establishes containment. Inspect at most 32 candidate nodes, excluding the query,
previously judged pairs, existing ancestry in either direction, and pairs whose
ancestry cannot be checked within the existing work allowance. No unbounded
refill follows exclusions.

The indexed search uses HNSW with pinned dependencies, seed 17, one thread,
`M=16`, `ef_construction=200`, and `ef_search=128`. Probe at most 64 indexed
wordings per query wording. The offline measurement also compares these results
with exact search, and refuses sources exceeding 5,000 SP entries before loading
vectors. Exact search and capacity calculation are small-corpus checks, not
million-post replacements for the indexed search.

Measure three candidate quotas: 3, 5 and 10. Each quota is tested in two ways:

- **Root-only follow-up:** offer only these eligible root candidates. Existing
  model answers and the saved hierarchy remain unchanged; the old candidate
  catalogue is not offered again in this proposed follow-up.
- **Combined catalogue:** supplement the existing per-post catalogue, retaining
  at least its first 0, 30, 45 or 55 candidates. Measure displaced candidate
  opportunities rather than assuming supplementation is free. Required root
  candidates are never silently dropped to fit a request.

The real discovery packer measures request count, rendered input tokens,
candidate count, and queries per request under the unchanged 60/16/4,000 limits.
An impossible profile is reported as refused, not truncated. Selected diagnostic
pairs show availability and direction in the resulting inputs; they are not a
gold set, nomination accuracy, or placement recall.

Verification has not run, so its exact count is unknown. Bound nominations by
three per query and the distinct eligible pair universe. The frozen-evidence
capacity check certifies a minimum number of pairs in every nonfinal greedy
verification batch using the production renderer and token counter. This gives
a conservative request ceiling, including one provider retry per request. Total
rendered-input ceilings include discovery plus up to 4,000 tokens per verification
request; they are not provider billing or output-token ceilings. Saved output
usage and timings are observations, not guarantees for a new pass.

The runner verifies source/export/prompt/vector hashes, records measurement-code
identities, and writes a separate ignored `report.json`. It refuses an existing
destination. Runtime, whole-process peak resident memory and normalized vector
buffer sizes are recorded separately: the process peak includes loading and
hashing the archived build, not just candidate search. For example, use a new
destination for each measurement:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
env LD_LIBRARY_PATH=/nix/store/1xw5xccqqh1xw3mvd70hyil6x418wxcm-gcc-14.3.0-lib/lib:/nix/store/ri9paa3mri4kqakljak8ldvbcp7lpmif-zlib-1.3.1/lib \
  OPENBLAS_NUM_THREADS=4 \
  uv run --offline --no-project --python python3.13 \
  --with-requirements sse_multivector/bounded-hierarchy-v1/requirements.txt \
  python -m sse_multivector.experiment measure-root-candidates \
  target/hg100-sol01 target/hg100-sol01-root-measurements-new \
  --pair S0346:S0874
```

Here the optional diagnostic pair identifies the saved Coffee and Beverages
references. Other pairs must use two distinct original `S####` entry IDs.

## PCPv3 — draft broader-subject nomination supplement

Status: **draft, not behavior-tested or adopted**. The user authorized the draft
and offline full-corpus sizing, not another model pass. HG100-SOL01 remains
unchanged and its frozen nomination prompt remains PCPv2.

The proposed supplementary pass works as follows:

1. For every current **hierarchy node**, give Sol low the same one or two saved
   **SP subject entries** used by PCPv2/BCPv5. Batch at most 16 queried nodes and
   4,000 rendered `o200k_base` input tokens. The earliest source post determines
   batching only; neither query nor candidate eligibility depends on that post.
2. [PCPv3](PCPv3.md) proposes zero through three broader subject names, each at
   most 160 Unicode characters. These are search text, not new hierarchy nodes,
   equivalence judgments, or accepted ancestors. No global node catalogue is
   sent to this prompt.
3. Search existing nodes using the proposed names. Exact wording lookup can
   reuse saved wordings; approximate lookup would require separately authorized
   SSE encoding of new names and indexed subject-vector search. Repeated names
   do not establish equivalence. Limit alias expansion, candidate inspections,
   and the **total to three resolved existing nodes per query**, not three per
   proposed name. The resolver and its ranking policy are not implemented or
   selected by this measurement.
4. Reuse BCPv5 to compare the queried node against each resolved existing node,
   using only their unchanged saved SP evidence, not the generated search name.
   The generated name cannot redefine either node. Filter existing ancestry and
   judgments whose evidence is unchanged; only separately verified answers
   could enter the existing application process.

For example, the Butter query could propose "Dairy products". Lookup would find
an existing Dairy products node, and BCPv5 would then compare the actual Butter
and Dairy products nodes. This does not depend on those two subject vectors
being nearest neighbours and does not assert the proposal will be generated.

The naming prompt follows the [official OpenAI prompting guidance](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices):
keep the task and output explicit, avoid repeated instructions, and evaluate
the prompt with the chosen model and workload. Existing source interpretations
and reference selection are retained rather than redesigned here.

### Offline sizing through the shared runner

`measure-parent-guides BUILD DESTINATION --prompt FILE --prompt-id PCPv3` reads
a saved bounded build and writes a separate ignored report. It makes no model
calls, prepares no inference run, loads no vectors, and changes no hierarchy or
completed-build quotas. Source, prompt, export, budget, and measurement-code
identities are recorded and checked.

The report measures the actual query-only batches and rendered input counts.
For N queried nodes, at most 3N names and 3N resolved comparisons are possible.
Because the future names and pairs are unknown, verification is a conservative
ceiling, not an exact count or a measured candidate-coverage result. The existing
comparison packer is bounded against any two distinct supplied nodes using
fixed-width ID records and the largest saved evidence records; it does not
enumerate all node pairs. Include one provider retry per request when checking
the remaining lifetime attempt budget. Token counts are rendered proxies, not
provider billing.

The 160-character contract bounds validated name text, not provider output or
reasoning tokens. Saved subscription settings have no hard output cap; future
output usage cannot be certified before inference. At most 3N new standalone
subject-vector encodings could be needed, with exact-name reuse reducing that
number. This measurement performs none and does not estimate their latency or
provider cost. The saved archive loader and the 5,000-entry measurement guard
are small-corpus tools, not a million-post implementation.

Full 100-post measurement (`target/hg100-sol01-parent-guide-measurements-v1/report.json`):

| Quantity | Measured count or conservative ceiling |
| --- | ---: |
| Current hierarchy nodes queried | 1,651 |
| Nomination requests, packed from actual saved evidence | 151 |
| Nomination rendered input tokens, total / maximum per request | 122,152 / 1,290 |
| Proposed names / resolved comparisons, maximum each | 4,953 |
| Guaranteed verification pairs per nonfinal batch | 13 |
| Verification requests, maximum | 381 |
| First-attempt requests, maximum | 532 |
| Attempts allowing one provider retry each, maximum | 1,064 |
| Remaining lifetime attempts before this measurement | 1,478 |
| Total rendered input tokens, first-attempt ceiling | 1,646,152 |

This establishes that one proposed pass fits the remaining attempt budget.
There were **zero model calls and zero new vectors**. Name generation quality,
candidate resolution, and browsing improvement remain untested; budget
feasibility does not establish hierarchy completeness. Keep this separate from
the finished build, including its original three-pass and nomination limits.

## Completed build and browser handoff

HG100-SOL01 completed its three scheduled passes on September 30, 2026:
522 new attempts, two exact-request reuses, and no failed or unrun model cases.
The final snapshot is `target/hg100-sol01/exports/final-004/`; its saved
summary and provenance contain the detailed counts and receipt bindings.
All 100 posts, 2,383 SP entries and 1,674 masks were retained. The native browser
check passed, along with ancestry, DAG and export-hash checks. Mechanical
completion does not establish semantic placement accuracy or browsing quality.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
target/infomap-review-build/debug/sse-subject-navigation \
  --categories target/hg100-sol01/exports/final-004/categories.json \
  sse_multivector/hierarchy-refresh-v1/masked-posts.json
```

### Important limitation of preserving every local SP relationship

A generic ingredient subject underneath a specific recipe in a local SP
hierarchy can become a cross-post ingredient node. Preserving that parent link
then makes unrelated posts reachable beneath the specific recipe. Verified
new placements can extend the leakage without violating any graph invariant.
This occurred in the finished build; it was not manually repaired or hidden.

BCPv5 checks nominated global pairs, not every retained local SP relationship.
Consequently, this build does not establish that every local link can safely
become unconditional ancestry between combined global nodes. Remaining roots
and duplicate branches also show that the bounded selection is not complete.
The source trace confirmed that the recipe-specific SP entry directly contains
general ingredient headings. Whether construction should validate original SP
links before accepting global ancestry remains open; the completed build and
its unconditional-preservation policy are unchanged.

### Checking original SP links with unchanged BCPv5

The shared `bounded_comparisons` adapter also accepts a source selection with
exactly `schema_version`, `inputs`, and `original_sp_edges`. `inputs` is the saved
SP-input path, optionally pinned with a `path`/`sha256` reference. Select a list
of original `[parent_entry_index, child_entry_index]` pairs, or use `"all"` for
all saved direct SP links. This mode cannot include a global hierarchy or
discovery experiments.

Preparation checks each selected link against the saved SP graph. Each endpoint
is represented separately using its exact original subject and context, not an
LG01 or later combined reference. It reuses BCPv5's existing 16-pair/4,000-token
batching and response validator. The original link direction, source posts,
masks and entry provenance remain review evidence; the model receives only the
ordinary node entries and supplied pairs, without expected answers or an
instruction to accept the SP link. Preparing or running this check does not
change any hierarchy.

The user approved a six-link diagnostic using **BCPv5 unchanged / GPT-6.1 Sol
low**. The expectations below were chosen before inference and are agent
assessments, not newly established user decisions:

| Original parent entry | Original child entry | Expected relationship |
| --- | --- | --- |
| N063 SP2.1 Ingredients for mushroom risotto with shrimp | SP2.1.8 Cooking fats | Neither contains the other |
| N063 SP2.1 Ingredients for mushroom risotto with shrimp | SP2.1.3 Cheese | Neither contains the other |
| N063 SP2.1.8 Cooking fats | SP2.1.8.2 Butter | Parent contains child |
| N063 SP2.1.2 Rice | SP2.1.2.1 Arborio rice | Parent contains child |
| N042 SP1 Beverages | SP1.1 Tea | Parent contains child |
| N015 SP3 Bread | SP3.1 Sourdough bread | Parent contains child |

The maintained [selection](../experiment_specs/hg100-sol01-sp-links-six-v1.json)
contains source indices and a hash-bound source reference, not copied case data.
The [spec](../experiment_specs/hg100-sol01-sp-links-sol-low-v1.json) pins the
existing prompt, subscription model and comparison schema. Preparation creates
the actual prompts, review evidence and manifests automatically:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
uv run --offline --no-project --python python3.13 \
  --with-requirements sse_multivector/bounded-hierarchy-v1/requirements.txt \
  python -m sse_multivector.experiment prepare \
  target/hg100-sol01-sp-links-v1/experiment \
  --spec sse_multivector/experiment_specs/hg100-sol01-sp-links-sol-low-v1.json \
  --history-root target/hg100-sol01/passes
```

Only the separately authorized `run` command sends model requests. This pilot
does not authorize checking all SP links, exporting a replacement hierarchy,
removing links, modifying ASv6.48, or adopting a new construction policy.

The pilot completed on October 1, 2026, in one subscription call with no retry
or reused answer. Both problematic risotto links returned `neither`; all four
controls returned `a_parent_of_b`, matching the pre-inference expectations.
The shared runner saved the receipt and attributed agent review in
`target/hg100-sol01-sp-links-v1/experiment/`. This selected six-link result does
not establish corpus-wide accuracy or a decision to filter SP links. The
original HG100-SOL01 snapshot remains byte-for-byte unchanged.

### Full SP-link check: offline preparation only

The user subsequently approved preparing all saved SP links to measure workload,
not sending the full check. The [all-links source selection](../experiment_specs/hg100-sol01-sp-links-all-v1.json)
uses the same hash-bound original inputs and `original_sp_edges: "all"`.
The [all-links spec](../experiment_specs/hg100-sol01-sp-links-all-sol-low-v1.json)
keeps BCPv5, GPT-6.1 Sol low, the schema and model settings unchanged.

The shared runner's `prepared_inputs` report summarizes the selected comparison
batches and their total/minimum/maximum rendered input tokens. These are
`o200k_base` input-size proxies, separate from `usage`, which measures actual
attempts. The summary respects `show --only` filtering; it neither projects
output tokens nor assumes cache discounts, provider overhead or free retries.

Preparation on October 1, 2026 produced **110 batches for 1,755 comparisons**:
**186,304 rendered input tokens**, with **1,335–1,966 tokens per batch**. All
requests are unrun; no saved whole request was reusable. The six pilot links
remain included, but rebatching does not reuse their individual answers.
The source data and original hierarchy remain unchanged.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
uv run --offline --no-project --python python3.13 \
  --with-requirements sse_multivector/bounded-hierarchy-v1/requirements.txt \
  python -m sse_multivector.experiment prepare \
  target/hg100-sol01-sp-links-all-v1/experiment \
  --spec sse_multivector/experiment_specs/hg100-sol01-sp-links-all-sol-low-v1.json \
  --history-root target/hg100-sol01
```

Use `show` on the existing directory to inspect this preparation without
inference. A first pass would require 110 new calls; the existing provider-only
retry rule permits at most two attempts per batch. Sending the full check or
changing global ancestry requires approval beyond this offline preparation;
no full-check outputs exist yet.
