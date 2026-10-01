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
The next read-only investigation should examine that local-to-global link
assumption, using the saved source entries and actual inherited posts.
