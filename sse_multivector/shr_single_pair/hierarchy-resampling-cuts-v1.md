# Note-subset recovery of candidate root sections

Experimental numerical investigation, 2026-10-18. **Not activated as a HiGen
policy.** The approved next construction boundary is recorded below; current
HiGen implementation is unchanged. The current target is at most six useful
root sections retaining at
least 90% of original corpus notes, with each section representing at least 10% of the
original corpus. Earlier measurements below retain their original 80% target.
The user prefers cut A
and explicitly accepts broad root topics because deeper levels provide
narrowing. Root breadth alone is not a failure criterion. The user further
clarified: "i don't care if the root nodes are wide in semantic width. but roots
should not cover the same information". Assess duplication of information
between roots, rather than treating a broad mix within one root as a defect.
This does not establish a numerical duplication threshold or a new algorithm.
Recovery under note
removal provides a diagnostic, without establishing better browsing choices.
No prompts, canonical hierarchies or review UIs changed. No model calls,
training or paid resources were used in the original resampling probes.
The full-meaning tree-cut follow-up adds local frozen-SSE encodings, with no
LLM calls or training, and reaches 91% in six complete branches. Later direct
partition tests and manual child-subdivision tests are recorded below.

## Root-partition requirements and research-test IDs

The initial test uses the existing 100-note corpus saved by HR22, rather than
a new subset of HR38. The subsequent root tests use the automatically
hash-selected thousand-note corpora saved by HR36 and HR37. All retain frozen
ASv6.100/Bootstrap-v133 original inputs. The root-level numerical requirements
are:

- At most six sections; six is a maximum, not a required count.
- At least 90% of the original corpus's distinct notes represented across them.
- Each section represents at least 10% of that original corpus's distinct notes.
- Roots should cover distinct information; broad semantic scope within a root
  is acceptable. Shared note IDs alone do not establish duplicate information.

For 100 notes, every section must represent at least ten notes and their union
must represent at least 90. Deduplicate note IDs within each section and across
the union separately; section note sets can overlap. Use the original corpus
size as denominator, rather than only the notes with usable inputs.

The user clarified that the six-choice ceiling also permits fewer children at
deeper levels. The existing tests fixed six as an experimental setting; that
setting is not a requirement to manufacture six groups. The numerical CLI
already accepts a specified `--sections` count, with six as its default, but
does not choose the count automatically. The approved next design splits pools
of more than six current intact groups and uses the existing groups directly
as leaves once at most six remain; see the approved construction boundary
below. Note display is outside this construction rule. This changes neither
the root
retention/size requirements nor any frozen result or current HiGen behavior.

Stopping an ordinary linkage tree at six branches alone does not enforce the
per-section minimum. The user rejected searching a prebuilt tree for branches
meeting these counts and authorized investigating direct six-way partitioning.
Average-linkage and Ward complete cuts can remain descriptive controls, rather
than the candidate construction rule. These numerical requirements do not
qualify section membership or deeper narrowing. Current HiGen behavior and
historical results are unchanged.

The user distinguishes these new research tests from their source experiments:

| Research test | Saved input source |
|---|---|
| Six-section-v1-01 | HR22's 100-note corpus |
| Six-section-v1-02 | HR36's hash-selected 1,000-note corpus |
| Six-section-v1-03 | HR37's hash-selected 1,000-note corpus |
| Six-section-v1-04 | The 557-note S05 section from Six-section-v1-03 |
| Six-section-v1-05 | The 485-note S02 section from Six-section-v1-03 |
| Six-section-v1-06 | The 125-note C03 child from Six-section-v1-05 |
| Six-section-v1-07 | The 16-note C03 child from Six-section-v1-06 |
| Six-section-v1-08 | Compare 2–5 children on Six-section-v1-07's same 19 entries; reuse its six-child control |

HR IDs identify the original experiments, not reruns of them. Existing artifact
paths retain their names to preserve frozen bindings. These research-test IDs
do not designate an approved HiGen version. The user requires manual tests of
specific parts before an integration proposal.

### Direct partition candidate: distinct-note-constrained cosine clustering

`sse_multivector/direct_section_partition.py` partitions original entries
directly. All supplied entries participate, including originally unassigned
ones. Existing fine groups are not indivisible constraints in this candidate.
This changes the unit from the preceding group-centroid probes; controls use
exactly the same entry vectors as the candidate.

Minimum-size constraints during assignment follow the approach in
[Bradley, Bennett and Demiriz, Constrained K-Means Clustering](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-2000-65.pdf).
Cosine distances and normalized center updates follow
[Spherical k-Means Clustering](https://www.jstatsoft.org/article/view/v050i10).
The distinct-note counting below is an adaptation for this task, not a claimed
result from either paper or a new trained encoder.

For the specified fixed centers, minimize summed entry-to-center cosine
dissimilarity. Each original entry is assigned once. A note/section witness can count at most
once and requires an assigned entry from that note. Each section requires its
configured minimum number of witnesses. This is a sparse minimum-cost-flow
linear program; implementation uses SciPy's dual-simplex solver and checks
integral assignments, optimal fixed-center cost and actual distinct-note
counts. Shared notes across sections remain permitted. It does not replace
distinct-note counts with entry counts or constrain the sections to be
equal in size.

Alternate assignment and normalized mean-center updates. Eight fixed starts
use the same initial centers for the constrained and unconstrained controls;
choose the lowest summed cosine dissimilarity, without looking at semantic
review labels. Preserve all starts and records of entries displaced from their
closest final center. The objective is local and is not semantic certification.
Sparse assignment storage grows with `sections * (entries + notes)`; vector
comparison grows with `entries * sections * dimensions` per update. There is
no all-pairs matrix, teacher call, training or HiGen activation.

Before real data, production-path tests compare the assignment to exhaustive
optima and cover repeated notes, multi-section note support, infeasibility,
deterministic clustering, monotone costs and the native numerical CLI.

### Six-section-v1-01: roots from HR22's saved corpus

Use the **existing HR22 hundred-note corpus**, not a new sample of HR38.
Saved initial inputs contain 728 usable original entries representing all 100
notes, from ASv6.100 and Bootstrap-v133. Original title/meaning bytes are
unchanged. Reuse nine exact cached meaning vectors and encode the remaining
716 distinct contexts locally, plus eight cached replays, through the existing
native SSE adapter and worker. This produces 1,448 title/meaning span vectors.
No LLM calls, training or paid resources were used.

All 724 encoded title views match the native HR22 vectors within 1.06e-7
maximum absolute error. The eight full-meaning replays agree within 4.74e-8.
Frozen checkpoint, model settings, source hashes and native receipt mappings
pass validation. The maximum context length is 120 tokens, below the existing
512-token limit. This completes the uniform full-meaning representation;
titles are not mixed into the clustering vectors.

All methods below use **the same 728 entry vectors**, include originally
ungrouped entries, and retain every supplied entry exactly once. HDBSCAN's 62
original fine groups are provenance only, not indivisible input units. Counts
refer to distinct original note IDs; different sections' note sets overlap.

| Method | Sections | Distinct notes retained | Smallest section | Largest section | All numerical requirements |
|---|---:|---:|---:|---:|---|
| Direct cosine partition | 6 | 100 / 100 | 34 | 79 | Pass |
| Complete Ward entry-tree cut | 6 | 100 / 100 | 25 | 76 | Pass |
| Complete cosine average-linkage entry-tree cut | 6 | 100 / 100 | 1 | 98 | Fail: sections with 1, 7 and 8 notes |

The direct result's six sections represent **46, 34, 52, 43, 55 and 79 notes**.
Their entry counts are 83, 71, 124, 79, 124 and 247. Their closest headings
suggest positive feelings; sleep and daily routines; coffee/drinks; Nostr and
Bitcoin; ideas/creative activity; and food/cooking respectively. These are
descriptive agent summaries, not generated canonical meanings or human gold.

All eight fixed starts converge. The best seed is `20261025`, with summed
cosine dissimilarity 328.6627484934107. The eight constrained runs take 0.302
seconds combined, excluding model encoding, preparation and rendering. The
**entire constrained and unconstrained panels have identical final
assignments for each matched seed**. Even the unconstrained iterations never
fall below 18 notes per section. Thus this corpus supports direct cosine
partitioning as a numerical candidate; it does **not** demonstrate an observed
benefit from minimum-size constraints. Their behavior is verified separately
against exhaustive small assignment problems. Ward also passes the user's
requirements, so no semantic superiority over Ward is established.

Coverage is complete because nothing is discarded. Weak placements therefore
remain visible: for example, `L00180` Rome is in the section centered on
positive feelings, and `L00103` MrBeast is in the Nostr/Bitcoin-centered
section. The actual root meanings have not been generated, so these are
agent-flagged review candidates rather than validated semantic errors. The
direct result splits 35 of 62 original fine groups across sections; this is
allowed by the candidate's entry-level assignment and is explicitly shown as
provenance in the viewer. No lower-level hierarchy or narrowing was built.

Ignored evidence is under `target/food-halves-v1/hr22-direct-six-sections-v1/`
in this task worktree, on the external drive. It includes the source-bound
preparation, native worker inputs and receipts, exact reuse/replay checks,
aligned numerical input, all sixteen constrained/unconstrained trials,
complete tree controls, independent membership validation, a PNG overview
and a standalone HTML viewer showing every entry and full meaning. The viewer
can switch methods and reverse the ordering to show weak connections first;
control columns are aligned by entry overlap solely for viewing. Saved source
hierarchies and official review UIs are untouched.

Seventeen partition/resampling checks pass after integration on `main`.
The broader 35-test adapter/worker panel passes with two optional Torch tests
skipped in the numerical environment. This remains a research prototype, not
an adopted HiGen version. Numerical success does not establish semantic
superiority over Ward or the quality of a recursive hierarchy.

### Six-section-v1-02: roots from HR36's saved corpus

The user next directed moving this investigation to the hash-selected
1,000-note corpus rather than the manually selected corpus. Six-section-v1-02
uses **HR36's saved corpus**:
its frozen corpus manifest selects the first eligible original posts in
domain-separated event-ID hash order, seed `hr36-corpus-v1`, with no manual
reviews or topic/author quotas. There are 602 authors. The source state remains
`94a7f7d6d2e4ad8fac895c0c44ef4d444bece47fff60a4cbd30aaa3205a70a07`.
ASv6.100 and Bootstrap-v133 are unchanged frozen source versions; later prompt
development does not change these saved inputs.

Apply the same entry-level full-meaning representation and direct cosine
partition candidate as Six-section-v1-01, keeping every usable original entry
separately, including repeated titles and entries originally unassigned by
HDBSCAN.
The 5,336 initial entries represent **937 of the original 1,000 notes**.
The other 63 have no usable saved meaning and remain outside this test.
The minimum is 100 distinct notes per section and 900 in the union, both
measured against the original thousand-note corpus.

Reuse 2,579 exact title/meaning vector bindings from compatible saved banks.
The native adapter/worker encodes 2,744 missing distinct contexts and eight
saved-context controls, producing 5,504 title/meaning span vectors. The
maximum input is 166 tokens, below the frozen 512-token limit. New title
views match native vectors within `1.08e-7` maximum absolute error; cached
title views within `7.68e-8`; all eight meaning replays within `4.93e-8`.
Source hashes, checkpoint identity, row mappings and normalized vectors pass
validation. No teacher calls, training or paid resources were used.

| Section | Descriptive main themes | Original entries | Distinct notes |
|---|---|---:|---:|
| S01 | Finance and cryptocurrency | 1,005 | 316 |
| S02 | Feelings, thought and personal life | 823 | 415 |
| S03 | Countries, places and public figures | 556 | 330 |
| S04 | Technology, organizations and organized activities | 1,081 | 537 |
| S05 | Social media, communication and news | 798 | 427 |
| S06 | AI, digital content and creative work | 1,073 | 527 |

The union is **937 / 1,000 notes (93.7%)**. Note counts overlap across sections;
every supplied original entry is assigned exactly once. These descriptions
are agent summaries of the contents, not generated canonical definitions or
human-approved memberships. Several sections include unrelated material:
for example, `L03042`'s Chinese garlic definition is assigned to S01, while
`L01358`'s Japanese Nix package-manager definition is assigned to S02. The
numerical pass does not establish understandable section boundaries.

Keep the same eight seeds, `20261018` through `20261025`, and select by the
unchanged summed cosine-dissimilarity objective before semantic assessment.
The chosen seed, `20261020`, converges in 32 iterations with objective
`2801.4616378299197`. Six of eight starts converge; two reach the existing
50-iteration limit and remain recorded. Every matched constrained and
unconstrained start has identical final assignments. The selected result
displaces no entry from its closest final center. As in Six-section-v1-01,
these data do not demonstrate an observed benefit from the minimum-size
constraints.

Independent checks verify section sizes, union coverage, all 5,336 entry IDs,
normalized mean centers, the reported objective, exact control equality and
unchanged frozen sources. Seventeen relevant partition/resampling tests pass.
Ignored evidence is under `target/hr36-direct-sections-v1/` in the retained
`oracle-mvp-hr36-direct-sections-v1` task worktree, backed by external storage.
It includes the source-bound plan, native worker inputs/receipt, aligned
vectors, all sixteen trials, full memberships and verification records.
No official HiGen experiment, canonical hierarchy or review UI changed.

### Six-section-v1-03: roots from HR37's saved corpus

The user approved Six-section-v1-03 using **HR37's saved corpus**, without
retuning, and requested a compact result plus an agent recommendation. Broad root
topics and practical imperfection remain acceptable; this transfer does not
introduce a semantic-purity requirement or a new grouping algorithm.

HR37 contains 1,000 automatically hash-selected posts from 571 authors, seed
`hr37-corpus-v1`, with no manual topic or author quotas. Its original note IDs
are disjoint from HR36's. The frozen source state SHA256 is
`5b73c39d8ff7a377da1819a3a3987d1580291670df122425d2dbc8c81a300d19`.
Retain ASv6.100, Bootstrap-v133 and the same frozen SSE checkpoint. The 5,189
usable initial entries represent 912 notes; 88 notes lack usable saved
meanings. All usable entries, including repeated titles and originally
ungrouped entries, participate separately.

Reuse 2,457 exact contextual meaning-vector bindings. Encode 2,718 missing
distinct contexts plus eight cached controls through the native adapter and
worker, producing 5,452 title/meaning span vectors. The maximum input has 132
tokens; none reaches the frozen 512-token limit. New title views match native
vectors within `1.20e-7` maximum absolute error, cached title views within
`8.65e-8`, and eight meaning replays within `4.98e-8`. Frozen source hashes,
checkpoint identity, row mappings and normalized vectors pass validation.
No LLM calls, encoder training or paid resources were used.

The numerical implementation is byte-identical to Six-section-v1-02. Keep six
sections, 100 distinct notes per section, at least 900 in the union, equal entry
weights, the same eight seeds and summed cosine-dissimilarity selection
rule, and the existing 50-iteration limit. The chosen seed `20261019`
converges in 41 iterations, objective `2762.2833547731043`. Five of eight
starts converge; three reach the existing limit and remain recorded.

| HR37 section | Descriptive main themes | Original entries | Distinct notes |
|---|---|---:|---:|
| S01 | Finance and cryptocurrency | 902 | 327 |
| S02 | Society and organized activities | 990 | 485 |
| S03 | Social media, news and communication | 820 | 401 |
| S04 | Countries, places and public figures | 597 | 343 |
| S05 | Science, technology and creative work | 1,084 | 557 |
| S06 | Personal experiences, feelings and choices | 796 | 441 |

The union is **912 / 1,000 notes (91.2%)**. Each section exceeds the 100-note
minimum. Note sets overlap, and every supplied entry is assigned exactly
once. Every matched constrained/unconstrained start has identical final
assignments; the selected result displaces no entry from its nearest final
center. Thus this third corpus still shows no observed numerical benefit
from enforcing the minimum during assignment. Retention follows from
keeping all usable inputs and is not an independent quality measure.

For comparison only, matching the six centers from Six-section-v1-02 and
Six-section-v1-03 by maximum total cosine similarity pairs the same broad
topic families. The six matched similarities range from `0.9559` to `0.9955`;
no memberships or settings change to produce that alignment. This is
descriptive repeatability across two
hash-selected samples of the same source corpus, not independent semantic
validation or author-independent generalization.

Agent review covers central representatives with distinct titles, a fixed
12-entry ID-hash sample per section, frequent titles and weak assignments.
The summaries above describe recognizable broad themes. S02 and S05 are
especially broad, and imperfect placements remain. These results support
retaining the candidate. The user requires manual tests of specific parts
before integration design; Six-section-v1-04 is the first subdivision probe.
This is not human approval, a formal accuracy estimate or a completed
recursive hierarchy.

Independent checks verify section sizes, note unions, all 5,189 entry IDs,
normalized mean centers, objective values, unchanged source bytes, the
unchanged Six-section-v1-02 settings and exact matched-control equality.
Seventeen partition/resampling tests pass. Ignored evidence is under
`target/hr37-direct-sections-v1/` in the retained
`oracle-mvp-hr37-direct-sections-v1` task worktree, backed by external storage.
It includes the frozen plan, native encoder inputs and receipt, all sixteen
trials, full memberships, verification and source-bound provisional agent
assessment. No official HiGen version, hierarchy or review UI changed.

### Six-section-v1-04: manually subdivide one broad section

The user approved testing the same procedure on the **Science, technology
and creative work** section from Six-section-v1-03 (source section S05).
Use only its 1,084 assigned original entries from 557 distinct notes, not all
entries from those notes or entries from other root sections. Every vector is
reused bit-for-bit from the parent test; no new encoding, LLM calls or training
occurs. The displayed parent name remains an agent description of a numerical
group, not a generated canonical definition.

Keep six children, the same eight seeds and objective, and the existing
50-iteration limit. Scale the minimum to the current parent's note set:
`ceil(0.1 * 557) = 56` notes per child and `ceil(0.9 * 557) = 502` in the union.
The implementation is unchanged. The selected seed `20261019` converges in
15 iterations, objective `434.65725659848465`; all eight constrained starts
converge. No child membership is edited after selection.

| Child | Descriptive main themes | Original entries | Distinct notes |
|---|---|---:|---:|
| C01 | Art, images and visual expression | 194 | 132 |
| C02 | AI, science, research and learning | 190 | 142 |
| C03 | Dates, timestamps and change | 109 | 99 |
| C04 | Music, audio, video and film | 134 | 92 |
| C05 | Software, tools and technical work | 255 | 157 |
| C06 | Data, identifiers, versions and comparisons | 202 | 161 |

All **557 / 557 parent notes** remain represented, and every child has a
strictly smaller note set than the parent. The largest child contains 161
notes (28.9% of the parent). No two children have identical note sets, and
all 1,084 parent entries occur exactly once. Note sets overlap between
children. This subdivision does not change the source test's root memberships
or its original-corpus coverage.

The unconstrained control also selects seed `20261019`, with objective
`434.6751512098334` and child note counts 131, 140, 99, 92, 157 and 163.
The selected constrained/control assignments differ on four entries. Seven
of eight matched starts differ, unlike the earlier root probes. The selected
constrained result still displaces no entry from its nearest final center.
This records a trajectory difference, not a demonstrated semantic benefit
from the size constraint.

Provisional agent review covers complete title inventories, distinct-title
central representatives, ten entry-ID-hash samples per child and weak
assignments. Recognizable thematic cores emerge, while time/data choices are
more generic and some memberships remain unrelated to their child summary.
The numerical narrowing check passes; this alone does not certify semantic
containment or useful browsing throughout a recursive hierarchy. The result
is a manual component test, not an integration proposal or HiGen activation.

Independent checks verify source hashes, exact parent-vector reuse, objective
values, normalized centers, entry coverage, note unions and strict child-note
subsets. Seventeen relevant partition/resampling tests pass. Evidence is under
`target/six-section-v1-04/` in the retained `oracle-mvp-six-section-v1-04`
task worktree, backed by external storage. It includes the frozen parent
selection and thresholds, aligned inputs, all sixteen trials, child
memberships, verification and provisional agent review. No review UI changed.

### Six-section-v1-05: manually subdivide society and organized activities

The user approved another manual component test using the **Society and
organized activities** section from Six-section-v1-03 (source section S02).
Select only its 990 assigned original entries representing 485 distinct notes.
Reuse their vectors bit-for-bit; do not add other entries from the same notes
or change any root memberships. No new encoding, LLM calls, training or
canonical definitions are involved.

Keep the same six-child method, objective, eight seeds and 50-iteration limit.
The note minimum is `ceil(0.1 * 485) = 49` per child and
`ceil(0.9 * 485) = 437` in their union. Select seed `20261022` by its lowest
summed cosine dissimilarity, `479.40774258867623`, before reviewing contents.
It converges in 17 iterations. Seven of eight constrained starts converge;
the remaining start reaches the 50-iteration limit and remains recorded.

| Child | Descriptive main themes | Original entries | Distinct notes |
|---|---|---:|---:|
| C01 | Government, politics and institutions | 155 | 99 |
| C02 | Conflict, war and public safety | 123 | 89 |
| C03 | People, relationships and society | 176 | 125 |
| C04 | Food, nature and physical surroundings | 171 | 95 |
| C05 | Business, services and infrastructure | 231 | 153 |
| C06 | Sports, exercise and travel | 134 | 86 |

All **485 / 485 parent notes** remain represented. Every child has a strictly
smaller note set than the parent; the largest contains 153 notes (31.5%).
No two children have identical note sets. All 990 entries occur exactly once,
while notes can occur in several children through different entries.

The selected unconstrained control has exactly the same assignments, seed and
objective. Five of eight matched constrained/control starts differ, so the
selected equality does not extend to the entire panel. The selected result
displaces no entry from its closest final center. These observations do not
establish a semantic benefit from the size constraint.

Provisional agent review covers complete title inventories, seven distinct-title
central meanings, ten deterministic entry-ID-hash samples and three weak
assigned-center matches per child. Government/politics, conflict/war,
business/infrastructure and sports have recognizable thematic cores. The other
two children remain mixed: C03 also includes astronomy, diseases and biological
topics; C04 includes clothing and other physical materials alongside food and
nature. Broad agent descriptions do not establish semantic containment. The
numeric narrowing and retention checks pass, but useful browsing throughout
a complete recursive hierarchy remains untested. No membership was edited to
improve the assessment.

Independent checks verify exact parent-row reuse, unchanged source hashes,
all entry IDs, normalized mean centers, objective, note unions and proper
child-note subsets. Seventeen relevant partition/resampling tests pass.
Ignored evidence is under `target/six-section-v1-05/` in the retained
`oracle-mvp-six-section-v1-05` task worktree, backed by external storage.
The frozen plan, input rows, all sixteen trials, full child memberships,
verification and provisional agent review remain available. This is a manual
component test, not an integration proposal or an official HiGen experiment;
no hierarchy, prompt or review UI changed.

### Six-section-v1-06: subdivide the mixed people/society child

The user approved subdividing the **People, relationships and society** child
from Six-section-v1-05 (C03), to check whether another level separates its
mixed contents. Its 176 assigned original entries represent 125 distinct
notes. Reuse exactly those entries and their saved vectors, without other
entries from the same notes, new encoding, LLM calls or training. The preceding
root and child memberships remain unchanged.

Use the unchanged six-child method, objective, eight seeds and 50-iteration
limit. The minima are `ceil(0.1 * 125) = 13` notes per child and
`ceil(0.9 * 125) = 113` notes in their union. The selected seed `20261022`
converges in 13 iterations, with objective `66.76775852136385`; all eight
constrained starts converge. Selection uses the lowest objective before
review, without editing memberships afterward.

| Child | Descriptive main themes | Original entries | Distinct notes |
|---|---|---:|---:|
| C01 | People and human affairs | 34 | 31 |
| C02 | Biology, animals and health | 24 | 21 |
| C03 | Family, heredity and aging | 19 | 16 |
| C04 | Society, culture and religion | 46 | 43 |
| C05 | Places, environment and space | 32 | 27 |
| C06 | Friendship, romance and social life | 21 | 17 |

All **125 / 125 parent notes** remain represented, and all 176 entries occur
exactly once. Every child has a strictly smaller note set than the parent;
the largest has 43 notes (34.4%). No two children have identical note sets.
The counts overlap because different entries from one note may enter different
children. Names in the table are agent summaries, not canonical definitions.

The best unconstrained control also uses seed `20261022`, with objective
`67.77027143211795` and note counts 36, 23, 15, 43, 30 and 10. Its smallest
child misses the 13-note requirement. Seven of eight matched starts have
different final assignments. The selected constrained result displaces no
entry from its nearest final center: constraints changed the trajectory,
without forcing final assignments away from the closest center. This does
not establish a semantic advantage over the control.

Provisional agent review reads all 176 full meanings. This additional level
separates much of the earlier mixture into recognizable biological, familial,
cultural, geographical/astronomical and interpersonal themes, alongside a
general people group. Clear mistakes remain: static methods are with people,
senators and headphones with biology, climate change with family/heredity,
and cars, earbuds and PCIe devices with relationships. Practical imperfection
does not erase the observed thematic separation, but the numerical result
does not certify semantic containment or complete browsing usefulness.

Independent checks verify source hashes, bit-for-bit parent-vector reuse,
all entry IDs, normalized mean centers, every trial's objective and note counts,
union coverage and proper child-note subsets. Seventeen partition/resampling
tests pass. Ignored evidence is under `target/six-section-v1-06/` in the retained
`oracle-mvp-six-section-v1-06` task worktree, backed by external storage.
It includes the frozen inputs, all sixteen trials, full memberships,
verification and provisional assessment. This is another manual component
test; no HiGen policy, source hierarchy, prompt or review UI changed.

### Conditional browsing-cost test on the saved subdivisions

The user rejected a fixed six-note stopping threshold and approved testing
whether a subdivision's smaller lists repay its added navigation. This is a
diagnostic on Six-section-v1-04, -05 and -06, not another partition, an adopted
stopping rule or a change to any HiGen version.

`sse_multivector/section_browsing_cost.py` reads the unchanged saved assignments
and deduplicates original note IDs within each child. Its assumptions are
explicit: one target note is selected uniformly from the parent's distinct
notes; inspection stops at that note in a random-order note list. An m-note
list then requires `(m + 1) / 2` expected inspections. This is a single-note
retrieval proxy, not a measured topic-browsing session.

For each target note, enumerate its containing children. Record three
conditional routes: choose the smallest such child, choose uniformly among
them, or choose the largest. Average over distinct target notes, not over
entries or child memberships. All three scenarios assume successful selection
of a child containing the target and exclude wrong turns. They are not
confidence bounds or observed user behavior. Menu reading and clicking have
no assumed conversion to note inspections: report the maximum extra navigation
cost that the conditional list savings would repay, in note-inspection units.

| Saved subdivision | Parent notes | Parent-list inspections | Child-list inspections, uniform valid route | Maximum extra navigation cost |
|---|---:|---:|---:|---:|
| Six-section-v1-04 | 557 | 279.0 | 68.45 | 210.55 |
| Six-section-v1-05 | 485 | 243.0 | 57.17 | 185.83 |
| Six-section-v1-06 | 125 | 63.0 | 15.10 | 47.90 |

The additional-navigation figures are break-even budgets, not actual menu costs
or click counts. The best/worst valid-route budgets span 207.52–213.74,
183.03–188.46 and 47.09–48.66 respectively. Thus the saved splits shorten
lists under these assumptions; none establishes where further subdivision
should stop.

Use 64 preconfigured entry-label shuffles per case, seed `20261018`. Preserve
each child's original entry count and the complete entry/note multiset while
breaking the selected memberships. Note-set sizes and overlap can change.
These controls stress the interpretation of the cost, without assigning
semantic labels or computing a significance threshold.

| Saved subdivision | Shuffled child-list inspection range | Shuffles with list savings | Shuffles scoring better than the selected split |
|---|---:|---:|---:|
| Six-section-v1-04 | 80.92–85.54 | 64 / 64 | 0 / 64 |
| Six-section-v1-05 | 71.27–75.31 | 64 / 64 | 0 / 64 |
| Six-section-v1-06 | 14.53–16.32 | 64 / 64 | 9 / 64 |

**This cost is insufficient as a standalone stopping rule.** It rewards random
memberships too because it assumes the user can choose a containing child.
It does not establish that the topics help someone make that choice. Conversely,
with no information about the target, any fixed traversal that inspects every
distinct note once still averages `(N + 1) / 2` inspections for a uniform target,
before navigation overhead. Smaller lists alone do not supply the missing
routing information. This finding does not reject the manually reviewed
subdivisions or establish that their real navigation benefit is zero.

Seven production-path diagnostic tests cover hand-worked overlap and routing
cases, duplicate-entry weighting, identical child note sets, deterministic
shuffles, source-bound CLI behavior and changed-input rejection. Together with
the existing partition/resampling panel, 24 tests pass. Independent exact-
rational calculations from the saved child memberships match all observed
costs; source hashes and all control counts/coverage pass verification.
Ignored plans, every per-note calculation and all shuffled assignments are
under `target/six-section-browsing-cost-v1/` in the retained
`oracle-mvp-six-section-browsing-cost-v1` worktree, backed by external storage.
No encoding, LLM calls, training, hierarchy changes or UI work occurred.
The automatic stopping criterion remains open.

### Six-section-navigation-v1: manual topic-route audit

The user approved checking whether the child headings offer clear routes to
relevant notes. Use the six saved children of Six-section-v1-06, without changing
their headings or memberships. This is a manual agent audit, **not a blinded
user study**: the agent previously reviewed all 176 entries and their placements.
The current target sample and route predictions are frozen before the current
membership lookup, but prior exposure cannot be undone.

Select twelve distinct case-folded titles from the parent's original entries
in SHA256 order of `Six-section-navigation-v1:` plus entry ID, without selection
by child or similarity. These twelve topic/entry queries span eleven supporting
notes; Atheism and Religion share one note. Review each target's full fixed
meaning against only the six existing descriptive headings. Record one primary
route, any alternatives, confidence and reason; allow no obvious route. The
headings remain provisional agent summaries rather than generated canonical
definitions. No inference requests or new encodings occur.

Lookup against the saved assignments gives:

- Eight of twelve primary routes contain the selected entry.
- Nine of twelve primary routes contain its supporting note, including one
  route supported through another entry from the same note.
- Eight route predictions were marked clear beforehand; seven reach the note.
- Two were marked as having overlapping choices, one tentative and one with
  no obvious first choice. No prediction is revised after lookup.

The nonmatching or ambiguous cases illustrate different issues:

| Target | Predicted first choice | Saved evidence |
|---|---|---|
| Atheism | Society, culture and religion | The Atheism entry is in People, but the same note is reachable through its Religion entry. |
| The author's neighborhoods | Places, environment and space | Neither the selected entry nor its note is there; the note is represented in People and Society. |
| Genetics | Biology, animals and health | The note is in Family, heredity and aging, the alternative declared before lookup. |
| Complexity | No obvious first choice | The generic systems definition offers no direct heading match. Its note is represented in Biology, Family and Society; two were declared as alternatives. |

Collectibles reaches its note through the tentatively selected Culture heading,
although none of the headings explicitly advertises collections or hobbies.
These are route observations rather than independently validated semantic
judgments. A matching note can be reached through another entry; an entry
placement mismatch alone therefore does not establish a browsing failure.
Conversely, co-membership by itself does not certify the whole group's relevance.

The audit supports useful topic choices in this example while exposing missed
and ambiguous routes. It supplies neither a user success-rate estimate nor an
automatic stopping criterion. It does not settle whether an issue comes from
grouping, descriptive naming or the chosen target interpretation. The saved
subdivision remains unchanged.

Ignored protocol, deterministic targets, frozen predictions, full lookup
evidence and verification are under `target/six-section-navigation-v1/` in the
retained `oracle-mvp-six-section-navigation-v1` worktree on external storage.
Mechanical checks reproduce the sample and compare all entry/note lookups with
the original label array; all frozen source and prediction hashes agree.
No code behavior, HiGen policy, prompt, canonical hierarchy or review UI changed.

### Six-section-v1-07: test another level inside the 16-note child

The user approved splitting Six-section-v1-06's **Family, heredity and aging**
child (C03) with the unchanged method, to examine whether another six-way split
offers useful choices. Its 19 original entries represent 16 notes. Reuse only
their exact saved vectors. Keep six children, eight seeds and the same objective
and iteration limit. The scaled minima become two distinct notes per child
and fifteen in their union. This tests those settings; it does not approve
either minimum as a final rule for deeper levels.

Seed `20261021` has the lowest constrained objective, `2.3707149236255156`,
and converges in two iterations. All eight constrained starts converge. Review
all 19 full meanings after selection without editing the memberships.

| Child | Contents summarized from the original entries | Original entries | Distinct notes |
|---|---|---:|---:|
| C01 | Evolution, genetics and aging | 5 | 3 |
| C02 | People, daughters and fatherhood | 3 | 3 |
| C03 | Young people | 3 | 3 |
| C04 | Climate change and measles | 2 | 2 |
| C05 | Families and relatives | 4 | 4 |
| C06 | Genetics and infertility | 2 | 2 |

All sixteen notes and all nineteen entries remain represented. Each child
has a proper subset of the parent's notes, with no identical child note sets.
One note appears in two children. The numerical checks pass, but they do not
justify displaying all six children: Climate change and Measles offer no
clear useful joint topic in their supplied meanings. Other distinctions,
including young people and family relationships, remain recognizable.

The matched unconstrained control also selects seed `20261021`, with objective
`2.3028385409404297` and note counts 5, 3, 3, 1, 4 and 1. Measles and Infertility
are singleton groups there. Both Genetics entries and Climate change are in
the broader evolution/genetics/aging group. This control also retains an
inherited mixed topic; removing the minimum does not certify its semantics.

To isolate the minimum's effect, call the existing production `assign` function
twice on the **same fixed initial-center cost matrix**, changing only
`minimum_notes` from zero to two. The minimum moves Climate change from C01
to the Measles group C04 and moves one Genetics entry from C01 to the Infertility
group C06. Their added fixed-center costs are `0.2534572007435255` and
`0.19659671561079994`. Both initial assignments equal their respective final
cluster assignments. The selected constrained run nevertheless reports zero
displacements from its final centers: that field alone cannot establish that
the minimum had no effect.

This is evidence of a specific size-constraint problem, **not a sixteen-note
stopping threshold** or a reason to reject all further refinement. The number
of children and whether a whole extra level is worthwhile remain open. No
minimum, root requirement or HiGen behavior is changed by the test.

Independent checks verify exact parent-row reuse, source hashes, all entries,
every trial's objective and note counts, normalized mean centers, union coverage
and proper child-note subsets. The existing 24 partition/resampling/cost tests
pass. Ignored frozen inputs, all sixteen trials, full memberships, fixed-center
minimum-effect evidence and full agent assessment are under
`target/six-section-v1-07/` in the retained `oracle-mvp-six-section-v1-07`
worktree on external storage. No encoding, inference, training or UI change
occurred, and all earlier memberships remain unchanged.

### Six-section-v1-08: compare fewer children on the same small section

After clarifying that six is a ceiling, the user approved comparing 2–5 children
on the same 19 entries from 16 notes. Reuse Six-section-v1-07's complete saved
**unconstrained** six-child panel as the baseline. Keep the minimum per child
at zero for every count, so this isolates child count after the separate
minimum-size effect in Six-section-v1-07. The root coverage/size requirements
are unchanged; this is a deeper-level research comparison.

Input and entry files are byte-identical to the baseline. Keep all eight seeds,
the same objective and the 50-iteration limit. At each seed, the initial centers
for a smaller count are exactly the prefix of the baseline's initial centers.
Select the lowest objective **within each count**, before manual assessment;
do not use the raw decreasing objective to choose between counts.

| Children | Selected seed | Objective | Distinct notes per child |
|---:|---:|---:|---|
| 2 | 20261021 | 5.227026 | 7, 10 |
| 3 | 20261020 | 3.884805 | 7, 4, 6 |
| 4 | 20261021 | 3.321688 | 6, 7, 3, 1 |
| 5 | 20261025 | 2.780831 | 1, 7, 1, 5, 3 |
| 6, saved baseline | 20261021 | 2.302839 | 5, 3, 3, 1, 4, 1 |

All eight starts converge at every count. Each selected result keeps all sixteen
notes and nineteen entries, and every child has a proper, distinct subset of
the parent's notes. Counts overlap. The CLI's constrained/unconstrained panels
are identical when the supplied minimum is zero; those duplicate executions
are not additional independent samples. The six-child baseline is not rerun.

Full manual review finds four children a reasonable provisional balance:

| Descriptive choice | Notes |
|---|---:|
| Biology/heredity, including evolution, aging and infertility | 6 |
| Family relationships | 7 |
| Young people | 3 |
| Measles | 1 |

The first choice also contains Climate change, an inherited odd placement
present on the biology side at every count. Reducing the count does not repair
it. Two children remain a plausible coarser menu. Three combines Measles with
young people. Five separately exposes Infertility; six additionally separates
family roles from families/relatives. The preference for four is an agent
tradeoff judgment, not human approval or proof of an optimum. No automatic
count-selection or stopping rule is established by this comparison.

Independent checks verify frozen sources, exact input reuse, every trial's
objective and note counts, normalized selected centers, initialization
prefixes and duplicate-panel equality. The existing 24 relevant tests pass.
Ignored plans, all new panels, the baseline reference, full memberships,
verification and provisional assessment are under `target/six-section-v1-08/`
in the retained `oracle-mvp-six-section-v1-08` worktree on external storage.
No new code behavior, encoding, inference, training, hierarchy or UI change
occurred. All earlier results remain unchanged.

## Question and controlled inputs

Does removing different notes break the previously flagged sports/war/politics
mixture, and can repeatability select better roots? These mixtures are agent
concerns, not new human semantic gold.

Use the same exact saved full-meaning vectors and original HDBSCAN group
identities as the preceding retention-cut probe. Exclude the previously audited
contexts with no recognized lexical tokens, identically for all controls.
Meanings are from the existing ASv6.100-derived source runs. No unmatched entry
inherits its group's placement. These are partial original groups when only
some members have saved full-meaning vectors.

| Corpus | Total notes | Available matched notes | Available groups |
|---|---:|---:|---:|
| HR36 | 1,000 | 853 | 425 |
| HR37 | 1,000 | 828 | 410 |
| HR38 | 2,000 | 1,714 | 779 |

This rebuilds broad **Ward trees**, holding original fine-group identities
fixed. It does not rerun HDBSCAN or measure the stability of initial group
discovery. All input/state/vector hashes are retained and verified.

## Measurement

1. Independently select 80% of available notes without replacement 64 times
   per corpus, seed `20261019`. All entries from a selected note stay together.
   The 80% sampling fraction is a diagnostic setting, not an admission cutoff.
2. Recompute unit group centroids from surviving members, then rebuild the Ward
   tree. A surviving original group keeps its identity even with one member.
3. For each original branch, restrict its membership to surviving groups. Find
   the sampled branch with the greatest Jaccard agreement: shared groups divided
   by the union of groups. Fewer than two surviving groups are uninformative.
4. Use the first 32 subsets to select roots; report recovery on the other 32
   without using them for selection. This is within-corpus replication, not
   untouched-corpus generalization.

The selection minimizes `group_count * (1 - mean_recovery)`, summed over six
disjoint original-tree branches, subject to the actual union of note IDs
exceeding 80% of the whole corpus. Omissions are allowed. Singleton branches
have no nontrivial connection to test and zero instability cost; their reported
recovery value of one is a bookkeeping convention, not empirical evidence.
The mixed-integer solver has a 1% relative objective tolerance, not an exact
optimality guarantee or semantic similarity cutoff.

The control minimizes within-section squared differences of group centroids
under identical tree, membership and coverage constraints.

## Result: repeatability favors one large section and five small sections

| Corpus | Variance control | Recovery selection | Largest recovery section |
|---|---:|---:|---:|
| HR36 | 802 / 1,000 | 819 / 1,000 | 761 notes; 381 groups |
| HR37 | 802 / 1,000 | 801 / 1,000 | 711 notes; 358 groups |
| HR38 | 1,603 / 2,000 | 1,607 / 2,000 | 1,428 notes; 654 groups |

All choices have six sections and exceed the numerical retention floor. But
the recovery objective selects a large mixed section and five tiny sections,
mostly financial/cryptocurrency topics. HR38's large section includes AI, news,
people, countries, art, greetings and technology. Its held-out recovery remains
high (0.962). This reproduces the size imbalance; it does not establish whether
subsequent narrowing makes the hierarchy useful. The user's later review
accepts broad roots and must not be described as a rejection of root breadth.

## Shuffle control for the size advantage

Large branches match other broad branches well even without informative group
identity. For each of the same 64 sampled trees, independently shuffle surviving
group IDs eight times, preserving tree shape and branch sizes. Repeat the
**same best-branch search** for every shuffle. Adjust observed recovery by
`(observed - mean_null) / (1 - mean_null)`. A guaranteed match under the null,
including the complete tree, contributes zero evidence. Negative adjusted
values are retained. Shuffle seeds are `20261019 + 1000000 + repeat`.

This was specified after seeing the raw selection's section-size imbalance; it is an
adaptive diagnostic, not a prospectively chosen primary result.

| Corpus | Adjusted selection | Largest section |
|---|---:|---:|
| HR36 | 826 / 1,000 (82.6%) | 761 notes; 381 groups |
| HR37 | 801 / 1,000 (80.1%) | 711 notes; 358 groups |
| HR38 | 1,602 / 2,000 (80.1%) | 1,428 notes; 654 groups |

Correction changes some small sections but retains the same large section
in every corpus. It does not materially change the root choices. Eight
shuffles are a finite diagnostic, not an exact null-distribution calculation.

## Sports/war diagnostic

HR38's variance-selected 87-group branch has two immediate children: a sports
branch of 17 groups/49 notes and a war/politics/institutions branch of 70
groups/159 notes. Their note sets overlap; counts must not be added as coverage.

| Original branch | Discovery agreement | Held-out agreement |
|---|---:|---:|
| Sports child | 0.708 | 0.727 |
| War/politics child | 0.483 | 0.475 |
| Combined parent | 0.456 | 0.446 |

These are mean best-branch Jaccard agreements, not semantic accuracy scores.
The smaller sports child is more reproducible than the selected parent, while
the 125-group finance section has held-out agreement 0.835. Thus the diagnostic
does distinguish some more-repeatable smaller sections from less-repeatable
broader branches. That distinction is not a semantic or usability judgment.

Using fixed agent-selected headings only for inspection:

- The smallest branch containing Basketball and Sports also contains War in
  **1 of 64** subsets. All three groups survive in all 64.
- Adding Association football and American football as sports anchors includes
  War in **2 of 64** subsets. All four sports anchors survive in 63 subsets;
  only three survive in the remaining subset.

The broad tree therefore usually has a sports branch separate from War before
the six-section choice. The cut selects their broader ancestor. This localizes
the combined placement to the branch choice in this probe; it does not prove
individual notes caused the merge or establish a general semantic boundary.
The user's later review explicitly accepts this broad-root choice in A.

## Visual comparison of two six-section cuts

A manual alternative from the same saved tree separates the sports and
war/politics children while combining the greetings and technology/news/art
branches at their existing common ancestor. That ancestor also includes a
54-group branch with Data, Analysis, Scientists, Life, Testing, Rankings and
other topics. No canonical definition was generated or changed.

| Choice | Sections | Distinct notes | Coverage | Change from A |
|---|---:|---:|---:|---|
| A: earlier variance cut | 6 | 1,603 | 80.15% | Baseline |
| B: separate sports; combine the other branches | 6 | 1,633 | 81.65% | 30 gained, zero lost |

A selects saved tree nodes `1516,1533,1544,1547,1551,1553`; B selects
`1516,1533,1506,1543,1551,1554`. Node numbers refer only to the frozen
779-group Ward tree. Group memberships remain disjoint within each cut;
note memberships can overlap. A's 202-note sports/war branch becomes
49-note sports and 159-note war/politics branches. Its 247-note greetings
and 810-note technology/news/art branches become a single 1,037-note branch
also containing the 54 additional groups. These per-branch counts must not be
summed as distinct-note coverage.

This illustrates an actual trade between available cuts, not a new automatic
selection rule or a claim that B is semantically superior. Both meet the
numerical requirements. The user reviewed the PNGs, preferred A, and explained
that broad root topics are acceptable because deeper levels provide narrowing.
This is a research preference, not activation of a new HiGen policy. The official
HR38 HiGen hierarchy is untouched.

Ignored review artifacts alongside `note-resampling-v1/`, in
`competing-cuts-review-v1/`, contain the side-by-side PNG, collapsed-tree PNG,
exact note/group memberships, input hashes and the single-comparison renderer.
Image filenames are `hr38-competing-six-section-cuts-v1.png` and
`hr38-competing-cut-branches-v1.png`. Actual set-union checks verify all counts,
30 gained notes, zero lost notes and exactly six disjoint branches in both cuts.

## Ninety-percent coverage probe

The user next requested exploration of 90% coverage. The fixed original
975 HDBSCAN groups contain only 1,778/2,000 notes (88.9%): no cut over just
those groups can reach 90%. The original clustering input also contains 3,580
unassigned entries. Together, all 10,188 valid native inputs represent
1,829 notes (91.45%). The other 171 notes have no entry in this saved native
clustering input; this probe assigns no fault for their absence.

The three saved full-meaning banks have exact matches for 4,648 original
entries across 1,778 notes, also below 90%. This follow-up therefore uses the
complete **native title-pooled vectors with each meaning as context**, uniformly
for groups and unassigned entries. A used full-meaning pooling and partial
original groups. Both representation and eligibility change, so the resulting
coverage is not a matched quality improvement over A.

Keep each original HDBSCAN group intact with all original members. Make each
originally unassigned entry an additional eligible singleton unit; none is
automatically admitted. Construct unit centroids, rebuild the Ward tree and
reuse the variance cut objective with six disjoint branches and at least 1,800
distinct original note IDs. No HDBSCAN parameter changes, new encodings or
teacher calls. No mixture of title-pooled and meaning-pooled vectors.

| Eligible units and cut | Sections | Distinct notes | Coverage |
|---|---:|---:|---:|
| Original groups only; complete six-way cut | 6 | 1,778 | 88.9% |
| Original groups plus unassigned entries; constrained cut | 6 | 1,800 | 90.0% |
| Same expanded pool; complete six-way cut | 6 | 1,829 | 91.45% |

The constrained result selects 739 original groups and 2,643 originally
unassigned entries. It gains 42 notes outside the original grouped-note set
and omits 20 of that original set: a net gain of 22. Relative to A it gains
214 notes and loses 17, but the changed representation/eligibility prevent a
controlled causal attribution. Per-section note counts are 329, 1,074, 713,
776, 931 and 441; these overlap and must not be added. The complete cut keeps
all available native notes and loses none of A's represented notes. Neither
result establishes the usefulness of a complete hierarchy with deeper levels.

Plans, exact memberships, vector/tree arrays and numerical results are ignored
under `ninety-percent-cut-v1/attempt-2/`, beside the other probes. A first local
attempt stopped on NumPy integer JSON serialization before optimization; its
source, plan and failure status are retained. The corrected numerical run
finished in 18.4 seconds and reached a 0.61% solver objective gap. Its coverage
and disjointness are independently checked from original entry/note IDs.

Numerically, 90% is attainable using existing vectors once unassigned entries
are eligible. A fair comparison with A's pooling needs additional frozen-SSE
meaning encodings; none were performed in this probe.

## Matched full-meaning follow-up: 91% in six complete branches

The user authorized completing the full-meaning vectors and repeating the
expanded-pool test. This follow-up restores A's exact representation: context
is `title + two newlines + complete explicit meaning`, pooling the complete
meaning. It does not pool the original post, shorten the definition, rewrite
headings or meanings, train a model, or call an LLM.

### Completion and validation

Reuse 4,648 exact original-entry vectors from the three existing banks. The
remaining 5,540 entries have 5,505 distinct contexts. The existing native
`title_selection_probe` adapter now accepts an ASv6.100 native hierarchy state
and prepares contextual whole-title/whole-meaning views. It binds the original
entries, corpus, model settings and source files; deprecated AS versions and
non-original native inputs are rejected. The normal native `worker.py` and
adapter `collect` paths run and validate the encoding; no separate execution
service or teacher runner is introduced.

The local offline CPU worker encodes 5,505 missing contexts plus eight
deterministically selected cached replay contexts, producing 11,026 span
vectors. Title and meaning vectors share each encoder forward pass. The frozen
checkpoint, base-model artifacts and pooling rule are unchanged. New encoding
uses native batch size eight; the prior meaning banks used 32. Replay checks
verify the resulting numerical agreement rather than assuming identical runtime
settings. CPU affinity allows 24 of the machine's 28 CPUs, leaving four.

| Check | Result |
|---|---:|
| Newly encoded title contexts checked against native vectors | 5,513 |
| Maximum normalized title-vector absolute difference | 1.16e-7 |
| Cached full-meaning replay contexts | 8 |
| Maximum normalized meaning-vector absolute difference | 6.85e-8 |

Frozen pre-result bounds were 1e-5 maximum absolute difference and 1e-6 cosine
error, matching the earlier replay checks. All checks pass; the model is not
refitted or otherwise changed.

### Matched numerical comparison

Apply A's zero-known-lexical-context check to both representations. It excludes
37 original entries, leaving 10,151 entries representing 1,820 notes. The
eligible units are identical for title and meaning: 975 original HDBSCAN groups
with eligible members, plus 3,580 eligible originally unassigned entries as
singleton units. No fine groups are reclustered. Unit weights, Ward algorithm,
root count and numerical objective are identical between the two views.

| Representation | Cut | Sections | Distinct notes | Coverage |
|---|---|---:|---:|---:|
| Title | Variance objective with 90% floor | 6 | 1,800 | 90.0% |
| Full meaning | Same objective and floor | 6 | 1,800 | 90.0% |
| Title | Complete six-way tree cut | 6 | 1,820 | 91.0% |
| Full meaning | Complete six-way tree cut | 6 | 1,820 | 91.0% |

The complete cuts cover the same notes by construction; these equal totals do
not show that either representation is semantically better. Their branch
memberships differ. For example, the largest complete meaning section represents
1,170 notes, versus 1,666 for title. Root breadth alone is not an error under
the user's clarified goal. No lower-level narrowing or finished-hierarchy
quality is established by this root-only probe.

With broad roots acceptable, the **complete six-way cut removes the need to
prune toward a 90% target**. It retains all 1,820 usable input notes, preserving
all of A's 1,603 represented notes and adding 217. Of those additions, 164 have
eligible routes through original groups omitted by A, and 53 require an
originally unassigned entry after the common lexical check. The constrained
90% meaning cut instead gains 211 and loses 14 relative to A, so it is not
necessary for this coverage goal.

The six complete meaning branches represent 665, 861, 630, 917, 512 and 1,170
notes respectively. These overlap; the total is the union, not their sum.
Remaining omissions are 171 notes without any saved native clustering input
and nine whose available contexts have no recognized lexical tokens in the
frozen encoder. No fault or new semantic rejection is assigned to those notes.

### Evidence and status

All new artifacts are ignored under `meaning-completion-v1/`, alongside the
earlier probes. They include preparation/preflight plans, exact cache bindings,
native worker inputs/config/receipt, raw span vectors, complete normalized
meaning vectors, replay checks, matched unit centroids, both trees and cuts,
independent note/group membership checks, and
`hr38-full-meaning-91-percent-six-sections-v1.png`. Data stays on the external
drive. All protected source hashes remain unchanged. Eighteen adapter/worker
tests pass in the actual cached CPU environment with no skips, including the
native-source and pooling paths.

This is a successful numerical coverage result using A's pooling, not an
official HiGen run or policy activation. Missing meaning vectors were computed
locally; LLM calls, training and paid resources remain zero. Inspecting the next
level of the broad branches is the next useful check before claiming useful
hierarchy narrowing.

## Reproduction and verification

### Fixed child-count panel: protocol

The user approved broader comparisons after the 19-entry family-section probe:
one provisional preference cannot establish an automatic child-count rule.
`Section-count-panel-v1` is offline research, not a HiGen version or policy.
It fixes 24 development sections from the food corpus and the hash-selected
mixed corpus used in HR37, spanning roots through four subdivision levels.
The cases include every saved root section, smallest/largest children selected
by note count, narrow young-people/family sections, and singleton leaves.
Sizes range from one to 5,189 entries and one to 912 distinct notes. These
overlapping parent/child sections are correlated evidence, not 24 independent
corpora. Neither narrowness nor the previous four-child preference is gold.

Eleven cases from the corpus used in HR36 are reserved for later unchanged-rule
validation: its root, all six saved root sections, and four original groups
selected by deterministic group-ID hash. Their 937 distinct note IDs do not
overlap the 1,012 development note IDs. HR36 was used in earlier research; the
reservation concerns these new child-count comparisons, not an unseen corpus.
No reserved count fit is part of this development run.

Each case compares the unsplit baseline with two through six children where
entry count permits, using the same eight seeds, cosine partitioner and saved
whole-meaning vectors. The unsplit baseline is a numerical control, not a new
same-note-set child. Root cases retain their original ten-percent note minimum;
deeper cases use no minimum. All supplied entries remain eligible. Empty,
duplicate-note-set or non-narrowing children are reported rather than repaired.
Within each count, retain the lowest-dissimilarity start and all other starts.
Do not select across counts using raw dissimilarity: adding centers lowers
that objective without establishing useful browsing choices.

`sse_multivector/section_count_panel.py` freezes source hashes, original rows,
case roles and code before execution. It imports exact saved numerical panels
only when vectors, note ordering, seeds, constraints and producer settings
agree, and resumes completed counts without rewriting them. The fixed plan
has nine such imports. Preparation is separate from explicit case execution;
it does not execute reserved cases. Artifacts are ignored in the retained
`oracle-mvp-section-count-panel-v1/target/section-count-panel-v1` worktree path,
stored on the external drive. No LLM calls, training or new encoding is used.
No automatic count or stopping rule is selected or qualified by this protocol.

### Fixed child-count panel: development results

All 24 development cases completed: 129 count comparisons, each retaining eight
starts. Nine count panels reuse 72 exact saved starts; 120 new panels compute
960 numerical fits. Every selected best fit converged within the frozen
50-iteration limit. Twelve other starts reached that limit and remain recorded;
they were not silently retried or substituted. Independent reconstruction
checks every trial's original-note union, per-child note counts, note minimum
and objective. All supplied notes remain represented. All eleven reserved case
directories remain absent. The frozen source and code hashes still agree.

The ignored `panel/audit.json` records those checks and result hashes;
`panel/inspection.json` retains every best partition's complete title counts
and central entries with their full meanings. It supplements rather than
replaces the raw per-count trials and exact source rows.

The following are agent inspections of saved assignments, not semantic gold or
new canonical names:

| Section | Observed change as count increases | Consequence for count selection |
|---|---|---|
| Science/technology/creative, 557 notes (D13) | Four choices separate software, AI/science, arts/media, and numerical/data topics; six additionally separate music/video and time-related topics. | Extra choices can expose useful distinctions in a broad section. |
| Family/relatives, four notes (D22) | Two choices both contain a `Families` entry. Four choices become `Relatives`, `Families`, `Family`, `Families`, each holding one note. | Lower dissimilarity and singleton note sets do not establish understandable choices. |
| Young people, three notes (D21) | Two choices distinguish `Juveniles` from two `Young people` entries; three choices separate the two `Young people` definitions as well. | Count can separate a meaningful boundary or merely separate similar definitions; no reviewed optimum is assigned. |
| Society/culture/religion, 43 notes (D20) | Four choices produce a group containing Donald Trump, Conventions and Environmental science; six produce a Donald Trump/Privacy group. | Adding choices does not monotonically improve semantic coherence. |

Numerical dissimilarity falls at every available count increase in all 22
non-singleton cases. In D21 the one-to-two reduction is 91.0% of unsplit error;
in D22 it is 53.8%. Large relative improvement therefore also occurs in narrow
sections, not only in broad mixtures. This does not establish that those splits
are wrong; it rules out interpreting numerical improvement itself as evidence
of useful browsing refinement.

In the 100-note food root, two and three choices each leave one child covering
all 100 notes. These are the only two best partitions failing the recorded
strict-proper/distinct-note-set diagnostic. This is a stronger diagnostic than
merely counting choices and is not a new semantic rejection or HiGen guard.

The panel supplies the broader comparison evidence requested by the user.
It does not yet establish an automatic child count, a stopping threshold or a
finished recursive hierarchy. Any proposed selector should first be fixed and
examined across this development panel, then evaluated unchanged on the
reserved sections; the previous preference for four remains provisional.

### Gap-statistic screen: frozen protocol

The user authorized testing the gap statistic on the development panel before
integration. `Section-count-gap-v1` reuses the original assignments; no observed
clustering is rerun, no reserved count fit is executed, and no HiGen behavior
changes. It adds no LLM calls, encoding or encoder training. Its reusable CLI is
`sse_multivector/section_count_gap.py` with production-path tests in
`sse_multivector/test_section_count_gap.py`.

Settings fixed before the development screen:

- Use the 24 development cases and their original entry/note rows, note minima,
  eight initialization seeds, 50-iteration limit and cosine partitioner.
- Measure dispersion as the sum of squared Euclidean distances to each group's
  arithmetic mean. This equals the paper's pair-distance definition without an
  all-pairs matrix. Reuse the saved lowest-cosine-objective labels for each count;
  dispersion evaluates those labels rather than changing the clustering method.
- Generate 32 reference samples per nondegenerate case, seeds 20261101–20261132.
  Center the original vectors, rotate into their full nonzero PCA coordinates,
  sample uniformly within each coordinate's original minimum/maximum, then rotate
  back and restore the original mean. Do not reduce nonzero dimensions, whiten,
  add post context, or project reference samples onto the unit sphere. The
  unchanged partitioner normalizes its inputs internally for assignments;
  dispersion uses the supplied coordinates for both real and reference data.
- Refit each reference/count with the same eight starts for counts two through
  six. The one-cluster assignment is unique and is calculated directly.
- Compute `gap(k) = mean(log W_reference(k)) - log W_observed(k)` and
  `s(k) = population_SD(log W_reference(k)) * sqrt(1 + 1/32)`. Select the smallest
  count satisfying `gap(k) >= gap(k+1) - s(k+1)`; otherwise choose the largest
  tested count. This is the paper's rule, not R's different default `firstSEmax`.
- Exclude counts at or above the entry count: all-singleton dispersion is zero
  and its logarithm undefined. An input with numerically zero total dispersion
  stops unsplit; other zero-dispersion comparisons remain unresolved rather than
  being assigned an artificial positive floor. Singleton cases require no
  random reference work. Count one remains an unsplit baseline, not an added
  same-note-set hierarchy child.
- Separately report the choices from the first and last 16 reference samples
  using the same rule. This diagnoses Monte Carlo sensitivity without tuning
  the final rule or treating 32 samples as a precision guarantee.

The PCA box is an explicit reference-distribution assumption. A statistical
preference does not establish useful semantic choices. Inspect the actual
selected topics across broad and narrow cases; a rule that fails clear topic
mixtures or repeatedly separates near-duplicate choices is not qualified by
its score. Only a promising development result would justify unchanged
evaluation on the eleven reserved cases.

The bounded screen needs at most 32 reference datasets per nondegenerate case
and at most eight starts per multi-child count. It uses linear-size vector and
assignment arrays, no dense entry-pair matrix. Reference jobs can execute on
24 local CPU workers, leaving four of the host's 28 CPUs available. This is an
offline method screen, not a production scalability claim. Plans, exact source
and producer hashes, PCA bounds, reference seeds, reference matrix hashes,
per-start costs/convergence and selected labels remain ignored under the
retained `oracle-mvp-section-count-gap-v1/target/section-count-gap-v1` worktree
path on the external drive. Completed references are immutable and reusable.

Primary references: [Tibshirani, Walther and Hastie, gap-statistic paper](https://web.stanford.edu/~hastie/Papers/gap.pdf),
especially the reference construction and algorithm on pages 414–415;
[R cluster documentation](https://stat.ethz.ch/R-manual/R-devel/library/cluster/html/clusGap.html)
documents its alternative selection rules and squared-distance setting. These
sources motivate the method, not its suitability for SSE topics.

### Gap screen: early results and faster screening

The initial full screen was too large for deciding whether the method merited
further work: 704 reference samples and 26,368 multi-start fits, before checking
the small stopping cases. The first execution received SIGTERM after 32 saved
references, with no Python error or kernel OOM record; its cause is unproven.
A persistent local job resumed the exact settings and reused those references.
After the user emphasized iteration speed, that queue was intentionally stopped.
It retains 370/704 reference records: ten complete 32-reference cases plus
24 references for D02 and 26 for D12. This is an incomplete screen, not a full
24-case result or a new HiGen experiment. All partial data remains preserved.

The CLI now accepts explicit development `--cases` so cheap diagnostic cases
can precede expensive confirmation work. Unknown or reserved IDs are rejected.
The reference generation, dispersion, statistical selection and execution
functions are unchanged; AST comparisons verify this. In a separate source
worktree, the priority subset D19–D24 reuses the original observed assignments,
keeps the identical 32 seeds and all statistical settings, and completes in
under one second. It is a subset of the same development panel, not independent
validation. Artifacts are ignored under
`oracle-mvp-section-count-gap-priority-v1/target/section-count-gap-priority-v1`.

| Completed section | Notes | Selected count | Counts from separate 16-reference halves |
|---|---:|---:|---|
| Food corpus root (D01) | 100 | 6 | 6, 6 |
| Positive feelings/social topics (D03) | 46 | 6 | 6, 4 |
| Waking/fatigue/time topics (D04) | 34 | 2 | 2, 2 |
| Coffee and associated materials/food (D05) | 52 | 2 | 2, 5 |
| Nostr/community topics (D06) | 43 | 5 | 5, 5 |
| Knowledge/content topics (D07) | 55 | 4 | 4, 4 |
| Food/preparation topics (D08) | 79 | 6 | 6, 6 |
| Finance/cryptocurrency topics (D09) | 327 | 6 | 6, 6 |
| Society/organized activities (D10) | 485 | 6 | 6, 6 |
| Communication/social media (D11) | 401 | 6 | 6, 6 |
| Family/biology/disease mixture (D19) | 16 | 1 | 1, 1 |
| Society/culture/religion (D20) | 43 | 1 | 1, 1 |
| Young people (D21) | 3 | 1 | 1, 1 |
| Family/relatives (D22) | 4 | 1 | 1, 1 |
| Measles (D23) | 1 | 1 | No random references needed |
| Infertility (D24) | 1 | 1 | No random references needed |

Topic names are inspection summaries, not new canonical definitions. The narrow
near-duplicate sections stop, but D19 also stops despite containing distinct
family, biology and disease topics. This is an agent assessment of inadequate
narrowing, not human gold for a particular alternative child count.

The saved D19 curve identifies a concrete mechanism: gaps for counts one through
six are `0.0821, 0.0794, 0.1558, 0.1601, 0.1903, 0.2561`. The reference uncertainty
at count two is `0.0724`. The published adjacent-count condition therefore accepts
one immediately, even though larger counts have substantially higher gaps.
This is not a transport failure or merely a shortage of Monte Carlo samples:
both 16-sample halves make the same decision. The evidence identifies the local
stopping condition's behavior, not which alternative rule is correct.

All 128 priority reference matrices are independently reconstructed from their
frozen seeds. Matrix hashes, every selected-label dispersion, cosine objective
and distinct-note count agree. All eleven reserved cases remain unrun. Neither
this selector nor any replacement is activated. The comparison below uses the
already-computed gap curves, retaining these original results unchanged.

### Saved-curve comparison: global selection avoids the early stop

The user authorized comparing decision rules on existing scores, without more
simulations. `Section-count-rules-v1` compares three established formulas on
identical gap curves: the original adjacent-count rule, the highest gap over all
tested counts (`globalmax`), and the smallest count within one reference-error
unit of that highest gap (`globalSEmax`). The error is taken at the maximum,
not separately at each candidate. These selection formulas follow
[R cluster's source](https://github.com/cran/cluster/blob/master/R/clusGap.R);
the original population-SD convention and all saved statistics remain unchanged.
This is exploratory comparison after observing the original failure, not blind
qualification or a new HiGen version.

Sixteen development cases have complete usable statistics: fourteen with 32
reference samples and two zero-dispersion singleton controls. Eight other cases
remain incomplete and are excluded; no partial-reference estimate is substituted
for the planned 32. Parent/child cases remain correlated. Reading, validating
source identities and comparing all three formulas takes 4.1 seconds, with zero
new references, clustering fits, encodings, training or model calls. This is the
cost of reusing existing scores, not the cost of generating scores for new nodes.

| Section | Notes | Original adjacent rule | Highest gap | Smallest within maximum's error |
|---|---:|---:|---:|---:|
| Waking/fatigue/time (D04) | 34 | 2 | 6 | 5 |
| Coffee/materials/food (D05) | 52 | 2 | 6 | 5 |
| Knowledge/content (D07) | 55 | 4 | 6 | 6 |
| Family/biology/disease (D19) | 16 | 1 | 6 | 5 |
| Society/culture/religion (D20) | 43 | 1 | 6 | 5 |
| Young people (D21) | 3 | 1 | 2 | 1 |
| Family/relatives (D22) | 4 | 1 | 1 | 1 |

The five changed choices under `globalSEmax` were inspected using the saved
memberships and original meanings. Agent assessment: D19's five choices expose
Family, Young people, Biology/heredity, Infertility and Measles; D07 exposes
separate writing, visual-art, knowledge, questioning, shopping and calendar
topics. These are more useful distinctions than leaving D19 unsplit, without
claiming five or six is human gold. Inherited odd memberships remain, including
Privacy grouped with Donald Trump in D20 and Climate change on D19's biology
side. Changing the count decision does not repair those assignments.

The highest-gap rule chooses six in all twelve larger mixed sections; this is
not itself proof those counts are wrong, but it ignores the uncertainty that
allows smaller choices. `globalSEmax` chooses five or six in those sections,
while leaving both near-duplicate controls and both singletons unsplit. Comparing
the separate 16-reference halves, the adjacent rule changes in 2/14 nondegenerate
cases, versus 1/14 for `globalSEmax`. D19 is still sensitive: five versus three.
Half-sample agreement is Monte Carlo evidence, not semantic accuracy.

A cheap effort check reuses four disjoint eight-reference blocks from each
completed case. Under `globalSEmax`, 52/56 block choices match the full 32-sample
choice, and all four blocks agree in 11/14 cases. The exceptions are D04
`5,5,5,6`, D05 `5,5,6,5`, and D19 `5,5,3,3`. No new samples are generated.
This suggests investigating reduced reference work, but does not qualify an
eight-reference setting or equate count agreement with preserved menu quality.

As an additional structural check, compose the saved 100-note root partition
with its six saved child partitions. Both rules keep all 100 notes, six roots,
at most six children at any parent, and strictly smaller note sets for every
child. The adjacent rule yields 25 child groups; `globalSEmax` yields 33. This
is a paired numerical two-level check, not a completed hierarchy, a review UI,
or proof of fewer browsing decisions. No new canonical meanings are generated.

The experimental `select_count(..., method=...)` helper now supports these
comparisons; its default and HiGen behavior remain unchanged. Tests cover the
early-stop counterexample, uncertainty at the global peak, unsplit cases, ties
and unchanged default output. Exact curves, decisions, half-sample decisions,
consumed input hashes and the two-level checks are ignored in
`oracle-mvp-section-count-rules-v1/target/section-count-rules-v1/comparison.json`
on the external drive. Original receipts and numerical outputs are untouched.

`globalSEmax` is the more promising next candidate, not an activated policy.
The useful next check is unchanged validation on a smaller mixed section and
narrow controls from the reserved corpus, rather than restarting the full large
queue. All eleven reserved cases remain unrun at this checkpoint.

### Frozen small reserved validation

The next approved screen fixes `globalSEmax` before observing its reserved
results. It uses V04, the saved root section with the fewest entries (556
entries, 330 distinct notes), and the four already selected small groups
V08–V11 (6, 4, 3 and 3 entries respectively). Selection uses the frozen panel
metadata, not new gap scores. These small groups are controls for unnecessary
splitting, not independently established homogeneous human gold.

The reserved source is hash-selected HR36, with 937 usable notes disjoint from
the development panel's note IDs. HR36 appeared in earlier grouping research;
it is reserved for this count-selection comparison, not an unseen corpus in
all prior work. Other reserved cases and the stopped large development queue
remain unrun in this phase.

Use the unchanged full-meaning vectors, original observed count assignments,
PCA-box reference distribution, dispersion, eight starts, constraints and
population-SD convention. Generate 32 references with seed 20261101, and compare
the full decision with each independent 16-reference half. Local workers may
use 24 cores, leaving four available. There are no new encodings, LLM calls,
training, canonical definitions or HiGen activation. Inspect selected entries
and meanings as well as the count; stability alone does not establish accuracy.

The numerical CLI now freezes `--method` and `--role` in preparation. Its
defaults remain adjacent/development. Reserved execution requires explicit
case IDs, and original case roles remain unchanged. Ignored evidence will live
under `oracle-mvp-section-count-validation-v1/target/section-count-validation-v1/`
on the external drive.

### Reserved validation result: a small-group over-split blocks adoption

All five authorized cases completed without errors. Reference execution took
16 seconds wall time, about 321 CPU-seconds, using 24 workers with one BLAS
thread each; peak recorded memory was 666 MB. It generated 160 reference
samples. The large development queue was not restarted.

| Reserved case | Original entries / notes | Selected children | Independent halves |
|---|---:|---:|---|
| V04: mixed countries, places, people and related subjects | 556 / 330 | 5 | 5, 5 |
| V08: US dollar | 6 / 6 | 4 | 5, 4 |
| V09: lanterns, light and magic lanterns | 4 / 4 | 1 | 1, 1 |
| V10: diplomacy, diplomatic talks and summonses | 3 / 3 | 1 | 1, 1 |
| V11: deadlines and delays | 3 / 3 | 1 | 1, 1 |

V04's five children retain all 330 notes and each narrows its parent's note set.
Their distinct-note counts are 51, 43, 60, 126 and 140; these overlap and must
not be added as if disjoint. Agent inspection finds broad distinctions around
people/bodies, Britain, Israel-related subjects, other international subjects,
and the United States. Peripheral assignments remain awkward, including animals
and food in the people/body cluster. This is a numerical partition, not five
approved canonical definitions or semantic certification.

V08 exposes the important defect. All six meanings define the US dollar as the
official currency of the United States. Three short descriptions stay together;
three longer descriptions become singleton groups: international payments and
reserve currency, economic strength/global monetary role, and its quoted
Bitcoin exchange-rate use. These are unnecessary browsing distinctions by agent
assessment, not four independently established different topics. The selected
four-way split is also sensitive to reference sampling (five versus four).

For V08, gaps for counts 1–5 are `-0.64725, -0.72161, -0.71734, -0.18885,
0.19014`; the peak's uncertainty is `0.58804`. Thus the rule's acceptance level
is about `-0.39790`: count four qualifies and count one does not. This traces
the result to the unchanged global decision applied to this reference curve;
it does not prove whether the reference distribution, vector differences or
decision formula is the underlying cause. Do not add an exception for dollars
or retune the rule from this single case.

Independent reconstruction checked 130 raw reference matrices (all small
controls and the first/last mixed-section references), their hashes, dispersions,
cosine objectives, note counts and convergence. All 15 full/half selections
were recomputed directly from saved dispersions; the 18 eligible observed
partitions preserve their note unions. Production validation checks the frozen
bindings for all 160 saved references. These mechanical checks passed; they do
not remove the semantic over-split.

Exact plans, raw reference outputs, results, execution log and separate
`independent-verification.json` remain ignored at the external artifact path
above. The source worktree is retained because these results bind its exact
code and data paths. No reserved case outside V04/V08–V11 ran, and no production
HiGen setting changed. The candidate is not ready for adoption. The next useful
step is to diagnose the US-dollar control from the saved data before paying
for another large numerical panel.

### US-dollar diagnosis: a dense wording pair drives the late peak

The approved diagnosis uses only saved vectors, assignments and reference
samples. It does not create new encodings, reference samples, model calls or
clustering-policy changes. The comparison remains based on whole explicit
meanings, with titles as unchanged encoder context.

All six definitions identify the US dollar as the official currency of the
United States. Short formulations L01246 and L02850 have cosine similarity
`0.976701`. The short L00144 definition versus L01616's international-payment
and reserve-currency definition scores `0.5840`; versus L02137's economic-role
definition it scores `0.6186`. The vectors thus contain large differences
despite their shared topic. Extra clauses coincide with those differences;
these saved inputs alone do not isolate a causal effect of particular words
or establish a general pooling defect.

Enumerating all 203 partitions of six entries, and evaluating the 202 with
one through five groups, confirms every saved observed count attains both
the minimum cosine objective and minimum squared-distance dispersion. This
rules out insufficient initialization as the explanation for these observed
splits. Reconstructing the same 32 reference matrices finds 157/160 saved
reference/count solutions attain the exact cosine minimum. Substituting exact
solutions for the remaining three still chooses four. Independently minimizing
squared-distance dispersion for both observed and reference partitions also
chooses four. The discrepancy between the fitted cosine objective and measured
dispersion therefore does not explain this failure.

The late peak has a concrete source. At five groups, only two entries remain
together: L01246 and L02850. For unit vectors, their pair contributes dispersion
`1 - cosine = 0.023299`; the four singletons contribute zero. Relative to the
unsplit dispersion, the observed residual is `0.014667`, versus `0.033886` for
the geometric-mean reference residual. The rule detects that unusually close
pair against the wider surrounding definitions. That geometric structure does
not establish five useful currency topics.

| Largest count considered, same saved samples | Global rule chooses |
|---:|---:|
| 2 | 1 |
| 3 | 1 |
| 4 | 1 |
| 5 | 4 |

Adding the nearly all-singleton candidate changes the peak and therefore the
uncertainty band used to choose the count. It makes the existing four-group
partition qualify while the unsplit case no longer qualifies. This is an
explanation, not a proposal to cap all cases at four or remove every singleton.
The same exact audit leaves the other three small controls unsplit, as before.
It completes in under one second; no larger numerical batch is needed for this
diagnosis.

The count criterion is implemented as intended but is not a direct test of
useful topic distinctions. A tiny repeated-topic control exposes a failure;
it does not establish its frequency or invalidate all useful mixed-section
results. More restarts cannot improve the already optimal observed fits.
The next useful check is the unchanged rule on a larger repeated-topic section
from saved inputs, to distinguish a small-sample problem from a recurring
source of unnecessary levels. That test is not begun here. No fixed six-note
stopping threshold is introduced; the user's earlier rejection remains in force.

Ignored `oracle-mvp-section-count-dollar-diagnosis-v1/target/section-count-dollar-diagnosis-v1/exact-audit.json`
on the external drive retains input/result hashes, complete pairwise cosines,
exact per-count optima, every checked reference/count, alternate-objective
curves and the candidate-range calculation. Source receipts are unchanged.
The worktree is retained for that reproducible artifact path. No HiGen setting
is changed or qualified by this diagnosis.

### Larger repeated-topic control: frozen protocol

The approved follow-up fixes the same `globalSEmax` rule on original HR36 group
G036: 62 Nostr entries from 62 distinct notes. It is selected before computing
new count results as the largest original group with exactly one title after
case normalization. Selection uses saved group metadata, not gap scores. It
is an additional diagnostic from the already used reserved corpus, not a new
independent corpus or human gold.

Read all original meanings before execution. They define the Nostr protocol,
network and/or ecosystem, with variations in optional communication, community,
payment and relay details. Their shared title does not itself prove identical
meanings; inspection of any proposed children must check whether they offer
distinct useful topics rather than merely redistribute these descriptions.

Use the existing section-count panel and gap CLIs, frozen whole-meaning vectors,
counts one through six, the same eight starts and constraints as prior deeper
sections (zero minimum notes), 32 PCA-box references with seed 20261101, and
the unchanged population-SD convention. Compare both independent 16-reference
halves. No new encodings, model calls, training, policy changes or stopping
thresholds are part of this screen. Ignored evidence is stored externally at
`oracle-mvp-section-count-nostr-control-v1/target/section-count-nostr-control-v1/`.

### Larger repeated-topic result: stable splitting of Nostr descriptions

The unchanged rule selects six children for the 62-entry, 62-note Nostr group.
Both independent 16-reference halves also choose six. Their note counts are
13, 12, 18, 3, 10 and 6; these are disjoint in this particular control and their
union preserves all 62 notes. Every selected child strictly narrows the note
set. Those structural properties do not establish useful topic distinctions.

| Observed group | Notes | Wording emphasized in its original meanings |
|---|---:|---|
| 0 | 13 | All explicitly mention public keys. |
| 1 | 12 | Mostly list sharing, promotion and commenting among social uses. |
| 2 | 18 | Mostly describe the general protocol supporting social networking and other applications. |
| 3 | 3 | General protocol descriptions, including relay-choice architecture. |
| 4 | 10 | Emphasize social networking, the associated network or community. |
| 5 | 6 | Five contain the literal phrase `called events`. |

These descriptions are post-hoc agent inspection, not generated canonical
titles, semantic gold or rules used to select the count. A shared Nostr title
alone would not prove equivalent scope. Some protocol/network/ecosystem
differences could matter; the six-way result nevertheless separates overlapping
general definitions rather than six clearly distinct narrow subjects.

For example, group 2's L02673 defines an open decentralized protocol for social
networking and other applications, in which clients publish and receive signed
events through independent relays. Group 5's L03082 defines an open decentralized
protocol in which clients publish signed messages **called events** to relay
servers and retrieve them, supporting applications such as social networking.
Both establish the same core role and mechanism. Merely naming those messages
events does not supply a useful navigation distinction. Full original meanings
and memberships are retained in the inspection artifact.

Gaps at counts one through six are `0.67312, 0.71737, 0.85231, 0.87834,
0.88325, 0.93671`. Peak uncertainty is `0.03267`, giving an acceptance level
near `0.90405`; only count six qualifies. Agreement across the halves therefore
coexists with the semantic problem. This is not a significance test or proof
that the reference model captures semantic variation.

The effect is not limited to the six-entry dollar case or nearly all-singleton
candidates. Nostr's selected children all contain at least three notes. More
reference precision or an exception for tiny inputs does not address the
observed distinction between definition wording and useful topics.

Observed fits took about 0.58 seconds; reference execution took 0.83 seconds
wall time, 4.35 CPU-seconds and about 280 MB peak memory. There were 48 observed
fits and 32 new reference samples. Independent checks reconstructed all 32
matrices and checked 192 reference/count dispersions, objectives, note counts,
bindings and selected convergence states; all passed. All 48 observed trials
also passed native validation, and all three full/half count choices were
recomputed from saved dispersions. No LLM, encoding, training or HiGen change
was made. Fourteen relevant production-path tests pass.

The next candidate to test is keeping existing HDBSCAN groups together when
forming broader choices, with originally unassigned entries still eligible.
Nostr would then be one input group rather than 62 definitions to subdivide.
This would change the current direct-entry candidate's explicit treatment of
fine groups, and requires a separate approved component test. Original groups
are not semantic gold; useful mixed-section splits and note coverage must be
checked. No such rule is activated or tested in this result.

The external artifact directory contains the frozen spec, observed panel,
reference screen, execution log and `inspection-and-verification.json`, with
complete selected meanings and per-group note IDs. The task worktree is
retained because these artifacts bind its exact source paths.

### Preserved-group comparison: frozen component protocol

The approved next test keeps existing HDBSCAN groups together in the same
mixed section V04 previously used for reserved validation: 556 original
entries from 330 notes. Within this frozen parent there are 89 original groups
and 189 originally ungrouped entries. Every ungrouped entry remains independently
eligible. Members of a group outside this parent are not imported; this bounded
test does not repair earlier fragmentation between roots.

Keep every original vector and its entry weight unchanged. For a fixed set
of centers, sum the costs of each group's members and assign the whole group
to the cheapest child. Center updates still use all original entry vectors.
This is equivalent to keeping group members together under the existing
entry-weighted objective; it does not introduce equal group weights, a new
centroid representation or re-encoding. Preserve initial centers/seeds, six
candidate counts, reference matrix seeds and the global count rule.

Apply the same group constraint to the real data and each reference fit. The
PCA box and raw reference matrices must match the saved entry-level baseline
exactly. Refit the constrained assignments on those same 32 matrices, rather
than claiming reused unconstrained fits are matched answers. Compare full and
half count choices, note unions, actual selected topics, and how many original
groups cross child boundaries in each result. No outcome is fixed in advance.

Native support is an explicit per-case `preserve_groups` option. It derives
group IDs from the saved original `source_group`, gives each ungrouped entry
its own ID, validates all observed/reference assignments, and caps candidate
counts at the available groups. A single preserved group stays unsplit without
reference work. This component supports the deeper-section zero-note-minimum
case only: positive note minima and unmatched producer reuse are explicitly
rejected rather than silently bypassed. Defaults and HiGen are unchanged.

Use 24 local workers and one BLAS thread each; there are no teacher calls,
training or new encodings. Ignored artifacts live externally at
`oracle-mvp-section-count-preserved-groups-v1/target/section-count-preserved-groups-v1/`.

### Preserved-group result: fragmentation fixed, topic quality remains mixed

The grouped mixed-section test completes with six children; both independent
reference halves choose six. All 330 original notes remain covered. The
entry-level baseline chose five, so compare both the independently chosen
layouts and their saved five-child fits rather than attributing count changes
to topic quality.

| Quantity | Entry-level baseline | Preserved groups, same five children | Preserved groups, selected six |
|---|---:|---:|---:|
| Original notes covered | 330 | 330 | 330 |
| Original groups split across children | 24 / 89 | 0 / 89 | 0 / 89 |
| Distinct notes per child | 51, 43, 60, 126, 140 | 60, 56, 153, 40, 106 | 105, 118, 40, 46, 28, 91 |

All child note sets strictly narrow this parent; their counts overlap and
must not be summed. The 189 ungrouped entries remain eligible as independent
items. No note or entry is imported from outside the frozen parent.

Examples of repaired fragmentation include G011's 39 entries (United States,
United States of America and Americans), previously split 38/1; G115's 31
Iran-related entries, previously split 20/2/9; and G296's six Donald Trump
entries, previously split 2/4. Keeping the same five-child count retains broad
people/body, Israel-related, international, Britain and US-oriented choices.
This is provisional agent inspection, not human approval or a measured
reduction in browsing decisions.

The constraint also preserves weaker original combinations. G320 contains
James Corden, Cameroon, Curaçao, Brad Cooper, Stephen Colbert and Colombia.
Their full meanings identify people and countries, not one narrow shared
topic. G088 combines Ottawa, Oklahoma, the Sea of Oman and Odessa. These are
existing groups, not new mistakes introduced by the grouping adapter. Making
all groups indivisible retains such combinations alongside useful ones.

At the automatically selected six-child count, the Britain-oriented entries
join a broader European/international child; women/nudity form another child,
while a separate body/animals/daily-topics child still has weakly related
entries. The result demonstrates intact membership, not clear overall
superiority or six approved category names. No optimal child count is
established by this comparison.

Matched checks confirm bit-identical original vectors, note IDs, PCA bounds
and all 32 raw reference matrix hashes. Every observed trial uses the same
initial center indices as its baseline counterpart. Thus the numerical change
is the group-assignment constraint applied to both real and reference data,
with the entry weights, pooling and decision rule unchanged. All 48 observed
trials and 192 reference/count group checks pass; all selected reference fits
converge. Independent reconstruction checks first/last reference matrices,
objectives and dispersions, and reproduces all three count choices. Reference
refitting takes 16.89 seconds wall time, about 232 CPU-seconds and 674 MB peak
memory. These are paired refits on existing deterministic samples, not 32 new
independent samples relative to the baseline. Forty-three relevant tests pass.

The proposal solves fragmentation by construction and reproduces the benefit
on a real mixed parent. It does not justify treating every existing HDBSCAN
group as semantically reliable. The useful next component test is whether
meaning-based grouping can separate the mixed-name examples while keeping
Nostr's shared topic together. That test is proposed, not run or adopted here.
Positive-minimum root construction remains outside this component's support;
no HiGen policy or complete hierarchy changes.

Ignored `comparison-and-verification.json` retains every selected membership
and full original meaning for the three layouts, all 24 previously split
groups, source bindings and verification results. The external artifact and
frozen source paths require retaining this task worktree.

### Meaning-based fine grouping: frozen small controls

The approved next test asks whether meaning-vector HDBSCAN can separate the
mixed-name examples while keeping Nostr together. Freeze four pools from the
same HR36 originals by group ID: G036, G320, G088, and their complete union.
Preparation mistakenly described G320/G088 as six/four entries and the union
as 72, using counts from their earlier V04 parent fragments. The frozen full
groups actually contain eight/seven entries; the union has 77 entries and 76
notes. This discrepancy was identified after execution and is retained here
explicitly; no input membership was changed after results. Geographic locations
may legitimately share a broader topic; G088 is not assumed to be human
rejection gold. Interpret actual memberships, not group count alone.

Run both saved title-pooled and whole-meaning-pooled vectors on each identical
pool. Matched title controls distinguish representation changes from the effect
of taking a small subset out of the original corpus. Preserve native opaque
point IDs and their canonical order across both views. Use the same frozen
native angular HDBSCAN executable, min_samples=3, min_cluster_size=2 and EOM.
Do not tune parameters or add a bend cut, consolidation, new encoding, model
call or training. Record unassigned entries and their notes explicitly; a lack
of selected groups is not successful topic separation.

The reusable `hdbscan_vector_probe` prepare/run CLI reads frozen original
meaning packets and native title requests, validates matching title/meaning/
note evidence, snapshots selected views and calls the existing production
`hierarchy_hdbscan.round_for` route. It retains the raw requests/results,
validates their identities, and resumes without rewriting saved reports.
Eight numerical cases can run independently with one native worker each.
No source hierarchy or HiGen version is changed. Ignored evidence is stored
externally under `oracle-mvp-hdbscan-meaning-controls-v1/target/hdbscan-meaning-controls-v1/`.

### Meaning-based controls: improved separation with two unwanted additions

All eight numerical cases complete through the same native route, without
changing parameters or encoding new vectors. The table records complete
original groups, not their earlier parent fragments.

| Pool | Entries / notes | Title: selected group sizes; unassigned entries | Meaning: selected group sizes; unassigned entries |
|---|---:|---|---|
| Nostr G036 | 62 / 62 | 25, 7, 7; 23 unassigned | 7, 4, 12, 10, 3; 26 unassigned |
| Mixed people/countries G320 | 8 / 8 | no groups; 8 unassigned | no groups; 8 unassigned |
| Mixed O-titled entries G088 | 7 / 7 | no groups; 7 unassigned | no groups; 7 unassigned |
| Complete combined pool | 77 / 76 | 62, 7, 8; none unassigned | 64, 6; 7 unassigned |

G320's two additional entries outside the earlier V04 fragment are Amy Colgan
and coco. G088 additionally contains Oaths, Ovens and Oval shapes. These make
the inherited mixed-topic problem clearer; the full groups are not just
people/countries and geographic places respectively.

In the combined title view, the selected partition exactly reproduces the
three original groups. The meaning view changes their composition:

- One group contains all 62 Nostr entries **plus Oaths and coco**. Those two
  additions are agent-flagged mismatches, not new human judgments.
- A six-entry group contains Cameroon, Curaçao, Colombia, the Sea of Oman,
  Oklahoma and Odessa. It crosses the old group boundaries around geographic
  meaning, a useful provisional distinction from the mixed-name groups.
- Ottawa, Amy Colgan, James Corden, Brad Cooper, Stephen Colbert, Ovens and
  Oval shapes remain unassigned. All remain eligible original inputs; they
  were not deleted or semantically rejected. The selected meaning groups
  represent 69 distinct notes; that is not a root-coverage measurement.

Standalone cases require special care: the native implementation excludes the
all-data root from EOM selection. Its `eom_subtree` returns the children's
selection when `node == root`; see the
[native implementation](../../src/fine_region_hdbscan.rs). Thus the isolated
Nostr case cannot select its entire all-input root, and no-group outputs for
the small mixed examples are not proof of correct semantic separation. The
matched combined pool is the useful comparison here. These results also
demonstrate why clustering a group alone is not equivalent to retaining it
as a branch among other topics.

### Exploratory cross-tab: retain membership supported by both views

Inspecting intersections of the combined title and meaning groups yields
blocks of `62, 1, 3, 1, 3` entries. The two singleton intersections are Oaths
and coco. The three blocks of at least the existing two-entry minimum are:

| Shared block | Entries |
|---|---:|
| Exactly the original Nostr members, with neither extra | 62 |
| Oklahoma, Sea of Oman and Odessa | 3 |
| Cameroon, Curaçao and Colombia | 3 |

This is a post-hoc cross-tab of existing outputs, not a separately frozen or
validated new grouping algorithm. It suggests testing group membership
supported by both vector views. Other entries would remain independent
eligible inputs rather than being discarded. Those three blocks contain 68
entries from 67 notes; the other nine entries remain available. Both views
use the same frozen encoder, so agreement is not independent-model evidence
or proof of semantic correctness. It could also over-fragment useful groups.

The next proposed component test is to freeze this agreement rule and evaluate
it unchanged on the existing HR22 hundred-note corpus, including its originally
ungrouped entries. That uses another saved corpus and realistic mixed context
before considering integration. No further test is run here. The saved direct
root partition already divides HR36's Nostr entries 53/9 across two roots;
future preservation must be evaluated before that partition if its purpose is
to prevent that split. This result does not change any root or hierarchy.

### Native verification and retained evidence

Independent checks verify all source/prepared hashes, bit-exact snapshots of
both views, identical opaque point IDs/order, unchanged configuration, complete
group/unassigned input unions, distinct-note counts, and the combined title
partition's exact match to original membership. Independent normalization
differs from request coordinates by at most `2.78e-17`; an initial bit-equality
assertion was too strict for independently ordered floating-point sums and was
replaced by a `1e-14` check. Source vectors and native results were unchanged.
All native grouping results and the corrected verification pass. Fifty-six
relevant tests pass, including two tests against the real executable with no
mocked transport or skipped native checks. Individual native-route durations
range from 0.025 to 0.206 seconds; eight CLI processes launched concurrently.

The ignored artifact directory contains the frozen spec/plan, selected paired
vector snapshots, all eight native requests/results and reports, and separate
`paired-view-audit.json` with the complete cross-tab and limitations. Original
sources are validated during preparation; execution validates the materialized
inputs and executable it actually consumes. No LLM, new SSE encoding, training,
parameter tuning, consolidation, UI update or HiGen activation occurred. The
task worktree is retained for its frozen source and artifact paths.

### Manual agreement test on the complete hundred-note source

At the user's request, test the proposed agreement rule manually on HR22's
saved source corpus: 728 original entries from 100 notes, ASv6.100 and
Bootstrap-v133. This is a numerical component test, not a new HR experiment.
Before execution, freeze two complete views, the unchanged native angular
HDBSCAN configuration (`min_samples=3`, `min_cluster_size=2`, EOM), and the
rule: intersect selected title and meaning groups, retain intersections with
at least two entries, and leave every other entry independently eligible.
Include all 361 originally ungrouped entries. Do not tune parameters, encode
new vectors, call models, generate a hierarchy or integrate the agreement rule.

Both native jobs run concurrently with twelve workers each on CPUs 0–23,
leaving four cores available. Each CLI finishes in about 1.9 seconds. The
title partition exactly reproduces all 62 original groups, providing an
input and execution control.

| View | Groups | Entries in groups | Distinct notes in groups | Independent entries |
|---|---:|---:|---:|---:|
| Title | 62 | 367 | 94 | 361 |
| Meaning | 52 | 289 | 94 | 439 |
| Agreement | 49 | 186 | 80 | 542 |

All 728 entries and all 100 notes remain available in the agreement result:
independent entries are not discarded. The 80-note figure measures membership
in fine groups, not finished-root retention. Only six original groups remain
exactly intact, but that count alone does not distinguish useful repairs from
unwanted fragmentation. Intersections cannot recover a useful group across
different title groups, even when the meaning view supports that connection.

Manual inspection finds both useful separation and loss of useful grouping:

- Nostr retains fifteen protocol/network definitions together. Two Nostr
  community definitions form a separate group; the referenced person and
  Nostr zaps remain independent. These distinctions are defensible provisional
  groupings, not new human semantic labels.
- The mixed original Matcha/Melangers/Myoglobin group disappears; all three
  entries remain independent. Agreement does not certify the retained groups:
  one still combines Foodstr and Foodchain hashtags, another combines Human
  bodies with People/Humans. Their browsing usefulness remains unreviewed.
- Coffee's original fifteen-entry group contains fourteen Coffee definitions
  and one Coffee preparation entry. Agreement makes groups of seven and four,
  leaving three Coffee definitions and Coffee preparation independent. The
  four-entry group emphasizes instant coffee and includes one definition that
  also covers beans; the seven-entry group still includes a definition allowing
  instant coffee. This does not establish a clean distinction for browsing.
- Only three of six Breakfast definitions remain together. Their group includes
  “Breakfast is the first meal of the day.” The other three describe the same
  meal with examples such as fried tomatoes, a breakfast burrito and scrambled
  eggs; all become independent. Three closely similar Recipes definitions and
  Recipe creation also all become independent.
- Food's original 39-entry group becomes groups of four, two and two, with 31
  independent entries. Many independent entries still explicitly define edible
  material intended for nourishment. This is substantial loss of useful
  grouping, not evidence that those entries should be semantically rejected.

Conclusion: strict agreement repairs some mixed title groups but is too
fragmenting to adopt on this evidence. HDBSCAN leaving an entry unassigned is
an absence of selected group support, not positive evidence of a different
meaning. A narrower follow-up could distinguish that absence from an actual
competing meaning group; it has not been tested or approved here. Neither
this table nor the manual examples measure the quality of a finished hierarchy.

The reusable probe gains only an explicit all-entry selector and validation
against the resolved Bootstrap title (falling back to original subject when
no resolved title exists). HR22 has 51 resolved titles that differ from the
original subject wording. Meanings and note identities match exactly. Both
changes have failing-first tests through production preparation/native paths;
58 relevant checks pass with no skipped native tests. HiGen remains unchanged.

Ignored evidence is external under
`oracle-mvp-hdbscan-agreement-manual-v1/target/hdbscan-agreement-manual-v1/`:
frozen spec/plan, paired vectors, both native requests/results, complete
`agreement-audit.json` cross-tab and compact `agreement-groups.md`. Independent
checks validate source/code hashes, paired opaque IDs/order, configuration,
disjoint complete group/unassigned partitions and the original title partition.
The task worktree remains for these frozen source/artifact paths. No model,
training, new encoding, consolidation, UI update or production policy change
occurred.

### Manual follow-up: unassigned meaning entries are inconclusive

The user authorized the proposed follow-up on the same saved hundred-note
results. Freeze the following interpretation before calculating its output:
within each title group, count the distinct selected meaning groups represented.
If there are zero or one, preserve the entire title group. If there are two
or more, retain their intersections of at least two entries; leave singleton
intersections and meaning-unassigned entries independent. In that second case,
the absence of an assignment cannot justify attaching an entry to either group
or bridging them together. Entries outside all title groups remain independent.
This rule tests numerical grouping evidence, not semantic truth.

| Rule on the same 728 entries / 100 notes | Groups | Grouped entries | Distinct notes in groups | Independent entries |
|---|---:|---:|---:|---:|
| Original title partition | 62 | 367 | 94 | 361 |
| Strict agreement | 49 | 186 | 80 | 542 |
| Unassigned meaning is inconclusive | 71 | 305 | 92 | 423 |

The follow-up preserves 51 title groups and splits 11. Twelve preserved groups
have no meaning-group assignments; 39 have exactly one represented meaning
group. It restores 119 entries to groups compared with strict agreement, adding
12 notes to grouped membership. All 728 entries and 100 notes remain eligible
under every rule; these are fine-group statistics, not finished-root retention.

Manual controls expose the trade-off:

- All six Breakfast definitions and all four Recipe/Recipe creation entries
  stay together, fixing their strict-agreement fragmentation. The five-entry
  Eggs group also stays together, including culinary Eggs, yolks and breakage.
- Matcha/Melangers/Myoglobin also stays together: none has a selected meaning
  group, so the rule has no evidence with which to separate them. It also
  preserves the original Tomatoes/Tallow group, where Tallow is unassigned.
- Coffee remains split into seven and four entries, with three Coffee
  definitions and Coffee preparation independent. Food still yields groups
  of four, two and two with 31 independent entries. Its original title group
  intersects six meaning groups, three of those at only one entry each.
- Nostr retains the previous fifteen-entry protocol/network group and the
  two-entry community group, with the referenced person and zaps independent.

Conclusion: distinguishing missing assignment from a competing selected group
repairs some useful groups, but it also restores clear mixed-topic groups and
does not repair the major Coffee/Food fragmentation. This is not sufficient
evidence to adopt the rule. Fewer ungrouped entries alone is not improved
semantic quality. The results suggest testing title and meaning similarities
together before HDBSCAN, rather than interpreting its two separate hard
partitions as semantic agreement or disagreement. That is a proposed next
test, not a tested method or production decision.

No source capability, parameter, vector or native result changed. The frozen
manual protocol, source hashes, complete cross-tab and compact group listing
are saved under the existing ignored evidence path in
`unassigned-inconclusive-v1/{protocol.json,audit.json,groups.md}`. A second
calculation reconstructs every group directly from set intersections, verifies
the complete disjoint input union, and confirms every strict-agreement block
remains intact within a resulting group. All checks pass. Source hashes remain
unchanged. No new encoding, model call, training, hierarchy, UI or HiGen policy
change occurred. The existing task worktree remains for frozen evidence paths.

### Combined title and meaning similarity before HDBSCAN

The user authorized the next manual component test. Freeze equal weights before
execution: concatenate each entry's saved unit title and meaning vectors and
divide by `sqrt(2)`. Their combined cosine is the arithmetic mean of the two
cosines; the native executable then converts that cosine to angular distance
before its usual HDBSCAN calculation. This averages similarities, not angles,
hard group labels or cross-title/meaning dot products. No weight search is run.

Use all 728 original HR22 entries, including formerly ungrouped ones, with
unchanged ASv6.100/Bootstrap-v133 evidence, executable, opaque point IDs/order,
and `min_samples=3`, `min_cluster_size=2`, EOM. Reuse the exact existing title
and meaning control outputs. Preselect Breakfast, Coffee, Nostr, Food, Recipes,
Matcha/Melangers/Myoglobin and Tomatoes/Tallow for manual inspection. The new
saved-vector CLI `combined` view uses the same production native path and
report/resume validation; it does not activate a HiGen policy.

| View or rule | Groups | Grouped entries | Distinct notes in groups | Independent entries |
|---|---:|---:|---:|---:|
| Title | 62 | 367 | 94 | 361 |
| Meaning | 52 | 289 | 94 | 439 |
| Strict agreement | 49 | 186 | 80 | 542 |
| Unassigned meaning is inconclusive | 71 | 305 | 92 | 423 |
| Equal-weight combined similarity | 58 | 329 | 91 | 399 |

Manual inspection shows several improvements together:

- All six Breakfast definitions stay together, as do three Recipes definitions
  with Recipe creation. Both avoid the strict-agreement fragmentation.
- Twenty-eight of the 32 exact-title Food entries join one 34-entry group,
  alongside Food dishes, Food enjoyment, Food appeal, two Food preparation
  entries and Meal preparation. Four Food definitions remain independent;
  they still describe food and are not semantic rejection gold. This restores
  substantially more of the repeated Food topic than either agreement rule.
- Matcha, Melangers and Myoglobin are all independent rather than one mixed
  title group. Three Tomatoes entries join Potatoes; Tallow stays independent.
  This avoids mixed groups restored by the inconclusive-unassigned rule.
- Coffee still forms groups of seven and four, with three Coffee definitions
  and Coffee preparation independent. The earlier ambiguous split survives.
- The Nostr group again contains the fifteen protocol/network definitions,
  two Nostr community entries, Nostr zaps **and the person referenced by a
  Nostr mention**. That person remains an agent-flagged mixed-topic inclusion.
  Combining similarities does not eliminate title-driven unwanted matches.

This is a promising component result on the preselected controls, not semantic
certification or a finished hierarchy. All 728 entries and 100 notes remain
eligible; 91 notes occurring in fine groups is not root coverage. Equal weights
are an unoptimized probe, not an established best setting. Before considering
integration or tuning weights, test the unchanged combination on another saved
corpus. That follow-up has not run here.

The one new native job takes 2.46 seconds with 24 workers on CPUs 0–23, leaving
four cores available. Concatenation doubles vector dimension and native input
size; its own transformation is linear in entries times dimension and does not
construct a new all-corpus matrix. This bounded probe does not remove the native
clustering's existing scaling costs. The full pairwise matrix used to verify
the cosine formula is a small-test audit, not added to the execution path.

A failing-first test exercises the real CLI and native executable, checks
mean-cosine behavior using contrasting title/meaning views, verifies matched
point identities/configuration and unchanged resume results. All 59 relevant
tests pass with no skipped native checks. Independent checks validate all
source/code/baseline hashes, raw request/result hashes, the complete disjoint
group/unassigned partition, and all pairwise combined cosines: maximum error
against the saved-view mean is `5.55e-16`.

External ignored evidence is retained in
`oracle-mvp-hdbscan-combined-view-v1/target/hdbscan-combined-view-v1/`:
frozen spec/plan and paired input, raw combined request/result, complete
`audit.json` and compact `groups.md`. The task worktree remains for these frozen
source/artifact paths. No new SSE encoding, model call, training, consolidation,
hierarchy generation, UI update or HiGen integration occurred.

### Unchanged combined similarity on the HR36 source corpus

The user authorized a cross-corpus check before integration. Use the saved,
hash-selected HR36 thousand-post source, ASv6.100 and Bootstrap-v133, without
changing weights, vector selection, native executable or HDBSCAN settings.
All 5,336 saved entries from 937 notes participate, including originally
ungrouped entries. The other 63 source posts have no usable saved entries and
cannot be assessed by this test. HR36 appeared in previous diagnostics,
including the 77-entry grouping control; this is a larger, different corpus
from the hundred-note source, not an untouched holdout.

Freeze title, meaning and equal-weight combined runs on identical inputs,
point IDs/order and `min_samples=3`, `min_cluster_size=2`, EOM. Preselect the
same exact-title topics, original G036/G320/G088, and the five largest combined
groups for inspection. Launch all three native jobs concurrently with eight
workers each on CPUs 0–23, leaving four cores available. They take 12.26,
12.32 and 16.23 seconds respectively. These are new numerical calculations,
not new encoder or model calls and not an official HR experiment.

| View | Groups | Grouped entries | Distinct notes in groups | Independent entries |
|---|---:|---:|---:|---:|
| Title | 527 | 3,212 | 907 | 2,124 |
| Meaning | 385 | 2,184 | 820 | 3,152 |
| Equal-weight combined | 451 | 2,818 | 883 | 2,518 |

All 5,336 entries and 937 usable notes remain eligible in every result. These
are fine-group counts: 883 notes occurring in combined groups is neither
finished-root coverage nor a claim to meet 90% retention of all 1,000 posts.
The title run exactly reproduces all 527 original groups.

Manual comparisons of the same inputs show:

- Nostr: title and combined each keep all 62 definitions in one group with no
  extras. Meaning-only forms groups of 12, 10, 7, 4 and 3, leaving 26 independent.
  Thus the combination avoids that fragmentation without the Oaths/coco
  additions seen in the much smaller 77-entry pool. Corpus context matters.
- Coffee: all nine definitions stay together in all three views. Food: title
  and combined keep all nine together, whereas meaning groups three and leaves
  six independent. The combined Food group has 27 entries, including Cooking,
  Recipes, food-related activities and general Cravings with food as an example.
  It is broad; this is not a fixed canonical Food definition or proof every
  member is contained by Food. Both Recipes entries join that group. There are
  no Breakfast entries here: the earlier Breakfast control is not revalidated.
- Original mixed people/countries G320: title reproduces the eight-member mix.
  Combined separates Cameroon and Colombia into a nine-entry geographic group
  with Portugal, Argentina, Spain, Brazil, Mexico, Venezuela and Texas. Stephen
  Colbert, James Corden and Brad Cooper form a four-person group with Jeremy
  Corbyn. Amy Colgan, Curaçao and coco remain independent. These are plausible
  broad distinctions, not new human gold or equivalence labels.
- Original mixed O-titled G088: title again keeps Ottawa, Oaths, Ovens,
  Oklahoma, Sea of Oman, Oval shapes and Odessa together. Combined groups Sea
  of Oman and Odessa with two Strait of Hormuz entries; the other five stay
  independent. The original unrelated-title mix disappears, though maritime
  geography is broader than a single place or region.
- The five largest combined groups cover Nostr (62 entries), AI/models/training
  (41), Bitcoin (38), timestamps/time-related records (34), and Iran-related
  topics (34). Definitions support these general themes, but boundaries remain
  broad: the last group also contains Iraq, and the time group includes
  countdowns and timelines. None is semantically certified by a title summary.

This supports advancing the unchanged combination to a browsing-section test,
rather than tuning weights around one remaining example. It preserves useful
repeated topics while repairing the inspected mixed-name groups, but grouping
statistics and a bounded manual review do not establish general accuracy or a
better finished hierarchy. The next proposed test is whether these fine groups
improve the at-most-six broader choices and their note coverage. No section
partition, synthetic definition, hierarchy or production integration runs here.

Independent checks validate frozen source/code and native request/result
hashes, identical point IDs/order/settings, complete disjoint input partitions,
exact recovery of the original title partition, and every combined pairwise
cosine using bounded row blocks. Maximum error against the mean of the two
saved-view cosines is `6.66e-16`. Five production-route probe tests pass. No
source-code change was required. The previous Python environment was no longer
installed; the local replacement is recorded and retained with a Nix GC root:
Python 3.13.12, NumPy 2.3.4, SciPy 1.16.3. The native executable remains identical.

Ignored evidence is in the retained combined-view task worktree under
`target/hdbscan-combined-view-v1/hr36-unchanged-v1/`: frozen spec/plan and paired
vectors, all three raw native requests/results, runtime details, complete
`audit.json`, and all 451 combined groups with entry titles in `groups.md`.
Artifacts remain on the external drive. HiGen, prompts, canonical meanings and
review UI are unchanged; no training, new encoding or model calls occurred.

### Matched broader-section comparison using the two fine groupings

The user authorized testing whether the improved fine groups yield better
broader choices. Freeze a matched comparison on all 5,336 original HR36 entries
and 937 usable notes. Only the fine-group memberships differ: original title
groups versus the equal-weight combined groups. Both retain all unassigned
entries as independent items. Keep the original full-meaning vectors and entry
weights, eight starting seeds, 50-iteration bound, candidate counts 1–6,
32 paired PCA-box reference matrices and `globalSEmax` count rule unchanged.

Use the existing zero-minimum group-preserving calculation. It cannot enforce
positive section minima; check the 100-note threshold afterward rather than
changing the optimizer. Both arms assign every supplied entry once, so their
note coverage is identical by construction, not evidence of improved admission.
The 63 source posts without saved inputs remain outside this comparison.

Reusable preparation now accepts a completed native grouping producer per case.
It validates matching entry evidence, exact meaning vectors and note rows,
then freezes the native groups and source hashes. Original defaults remain
unchanged. Preparation rejects incomplete/copy-only native evidence rather
than running fresh numerical work. Production-path tests cover actual native
group ingestion, intact section assignments, changed evidence, foreign input
rows and copied reports without their native artifacts. All 60 relevant tests
pass. The executed source checkpoint is `81b16788` in the retained experiment
worktree. A separate integration worktree strengthens the completed-artifact
guard without modifying frozen execution source or the numerical calculation.

Both observed panels and all 64 reference samples complete. The 96 observed
fits have identical initial center indices for every paired count/seed and
intact native groups in all assignments. All selected observed fits converge.
The two PCA reference input packets are bit-identical. Both full reference
screens select six sections; both independent halves also select six in each
arm. Reference execution uses 24 workers on CPUs 0–23 and one BLAS thread per
worker. Of 320 selected multi-section reference fits, 27 reach the 50-iteration
bound without converging. Count agreement is a bounded numerical result, not
semantic validation or a claim of exact global optimization.

The same-count six-section control has these distinct-note counts; note sets
overlap and should not be summed:

| Fine groups | Notes per section | Unique notes covered |
|---|---|---:|
| Title | 395, 540, 443, 441, 347, 341 | 937 |
| Combined | 466, 436, 438, 549, 308, 341 | 937 |

Both meet the six-choice, at-least-100-notes-per-section and 900-of-1,000 coverage
checks: each covers 93.7% of the original corpus. Neither is a finished hierarchy
or human-approved topic layout. These same-count fits are also both arms'
automatically selected fits.
After matching section labels by maximum entry overlap, 1,357 of 5,336 entry
assignments differ. This is not an accuracy score. Bounded manual inspection finds
no clear overall topic improvement: Food/Coffee join a publishing-oriented
section in the combined fit, while sports share a section with networking.
Nostr's 62 definitions stay together in both arms. The combined fit slightly
lowers the numerical cosine objective (2,828.785 versus 2,857.895), which does
not establish better browsing choices.

Read-only assignment scores explain one weakness. The 15-entry Coffee group
has mean cosine 0.2067 against the publishing-oriented section and 0.1361
against its next-best section. Fourteen of its fifteen members individually
prefer that same section. The partitioner must choose an available section;
it does not test whether any section is a suitable semantic placement. The
14-entry Association football group likewise individually prefers the
networking-oriented section. Thus the group-preservation constraint alone
does not explain these awkward placements. Root themes here are agent
descriptions of saved memberships, not generated or fixed canonical titles.

The title/meaning combination has only been used to form fine groups. The
broader calculation deliberately still uses the original meaning vectors,
holding that factor fixed in this comparison. The next proposed component
test is a quick matched six-section fit using combined vectors for that stage
as well, before further expensive count-reference work. No such fit, production
policy or HiGen version is introduced here. The observed fine-group gains
remain useful evidence; this test does not demonstrate a better finished
hierarchy or justify integrating the whole candidate.

Independent verification reproduces all six full/half count choices, checks
all 384 reference assignments for intact groups and distinct-note counts,
reconstructs first/last raw reference matrices and checks their objectives and
dispersions. Paired reconstructions agree exactly. Frozen source, code and
native evidence hashes remain valid. Reference-work span is approximately
748 seconds, estimated from output timestamps and recorded sample durations;
the count check dominates this bounded probe's computation. All 60 relevant
tests pass on the combined main checkout. The copied-artifact guard changes
only preparation failure behavior and does not alter the executed numeric fits.

Ignored external evidence is retained under
`oracle-mvp-combined-groups-sections-v1/target/combined-groups-sections-v1/`:
the frozen spec, observed panels, paired reference plan/results,
`same-count-audit.json`, `six-section-assignment-scores.json`,
`reference-reconstruction-checks.json` and complete final
`comparison-and-verification.json`. No LLM calls, training, new encodings, synthetic
definitions or UI updates occur. The task worktree must remain for its frozen
execution and artifact paths.

Reusable numerical CLI: `sse_multivector/cluster_resampling_probe.py`; tests:
`sse_multivector/test_cluster_resampling_probe.py`. Input NPZ contains unit
`vectors`, aligned compact zero-based original `groups`, and aligned `notes`.
It has no inference or HiGen integration. Dense best-match matrices require
quadratic group-count space; this is a bounded research probe, not a proposed
large-corpus production step. Sixty-four repeats across 425–779 groups took
6–20 seconds per corpus in the recorded runs with one BLAS thread each.

Artifacts are ignored under the retained task worktree:

`target/food-halves-v1/hr38-six-branch-distance-probe-v1/note-resampling-v1/`

That directory is stored on the external drive. It includes frozen input
plans/hashes, numerical inputs, exact original-entry bindings, every sample's
notes, raw/null/adjusted agreements, discovery/held-out results, chosen group
and note memberships, source snapshots and independent verification. Raw and
shuffle controls use exactly identical note subsets and raw recovery arrays.
Four full-note controls recover all nontrivial original branches exactly.
Independent checks reconstruct selected-note unions and set-based Jaccard
values on fixed subsets in every corpus. Source states and vectors are unchanged.

Cluster recovery by resampling is established methodology; stable output still
does not establish semantic correctness. See [Hennig, Cluster-wise assessment
of cluster stability](https://www.homepages.ucl.ac.uk/~ucakche/papers/clusta.pdf).
The specific note-level sampling, constrained root objective and shuffle
adjustment above are experimental choices here, not claims from that paper.

**Conclusion:** retain resampling as diagnostic evidence. Neither raw nor
chance-adjusted recovery is justified as the automatic root-selection rule.

### Combined-vector broader-section control

The user authorized a quick fixed-six-section comparison on the same HR36
inputs. Keep the completed combined HDBSCAN groups, all unassigned entries,
original-entry weights, eight seeds and 50-iteration limit fixed. Change only
the broader calculation's representation from full meanings to equal-weight
title and meaning vectors. This tests whether the fine-group improvements
carry through when the broader calculation uses the same representation.
Six is fixed for this component test; no new count-reference screen is run.
Initialization uses the same seeds, but the changed distances may select
different initial entries. Coverage remains identical by construction.

The existing research panel accepts a frozen `vector_view` of `combined`,
`meaning` or `title` from an existing paired-vector packet; its default
`vectors` contract is unchanged. Combined scoring concatenates unit title and
meaning rows and divides by square root of two, giving the mean of their two
cosines. Both components must be aligned and individually normalized. Saved
native-group validation checks exact rows for the declared scoring view as
well as original titles, meanings and note identities. There is no new encoding,
training, inference, HiGen activation or automatic count decision. Preparation,
actual CLI scoring, native grouping provenance, changed component rows and
existing default paths pass 61 production-path checks.

The fixed-six fit completes using the same 5,336 entries, 937 notes and exact
451 combined fine groups. All 2,518 unassigned entries remain independent
items. Selected section note counts are 341, 543, 296, 459, 462 and 400;
their unions cover 937/1,000 source notes (93.7%), unchanged by construction.
Each section exceeds 100 notes and strictly narrows the input note set.
There is no new automatic count-selection result: six was fixed in advance.

Agent descriptions of the selected fit's common titles are:

| Section | Common topics | Distinct notes |
|---|---|---:|
| 1 | Countries, places, geopolitics and public figures | 341 |
| 2 | Food, shopping, sports, music, politics and everyday activities | 543 |
| 3 | Bitcoin, cryptocurrency, finance and markets | 296 |
| 4 | Nostr, networking, news, publishing and links | 459 |
| 5 | AI, technology, software, art and media | 462 |
| 6 | People, greetings, feelings and social responses | 400 |

These descriptions are neither generated canonical titles nor human-reviewed
scope definitions. Note sets overlap and should not be summed. The changed
representation removes the two specific awkward placements inspected in the
meaning-only fit: the full 15-entry Coffee group and 27-entry Food group leave
the publishing-oriented section, and the 14-entry Association football group
leaves the networking-oriented section. They now share section 2. Its breadth
is acceptable under the user's clarified criterion. These control changes
alone do not establish that the six roots cover distinct information; that
cross-root assessment and useful deeper narrowing have not been tested here.

Across the eight predeclared starts, Food and Coffee share a section in five;
Food and Association football share one in six; football never shares Nostr's
section. The selected best start is seed 20261018. All eight converge within
50 iterations. The six-section fits together take about 6.36 seconds of recorded
fit time with eight BLAS threads on CPUs 0–23. No expensive reference screen
is repeated. After matching section labels by maximum original-entry overlap,
1,317/5,336 entries move relative to meaning-only broader scoring with exactly
the same fine groups. This is a change count, not an accuracy measure. Objective
values across the two vector representations are not directly comparable.

Independent verification checks all original identities and group assignments,
normalized member-mean centers, objectives, note counts and every start's
intact groups. Sampled pairwise combined cosines match the mean of title and
meaning cosines to floating-point precision. Completed fit bytes are unchanged
on resume; frozen source/code/native hashes remain valid. All 61 tests also
pass on combined main. No model calls, new encoding, training, HiGen policy,
canonical graph, synthetic definition or UI change occurs.

Ignored evidence is on the external drive, linked from the retained task
worktree `oracle-mvp-combined-section-scoring-v1/target/combined-section-scoring-v1/`:
`spec.json`, the frozen panel and complete `comparison-and-verification.json`.
Executed source is `5061f8d5`; the worktree remains for frozen source and artifact
paths. Before repeating the representation comparison on another corpus,
inspect whether separate roots duplicate information in this saved result.
This directly tests the user's clarified quality criterion; breadth alone is
not a reason to change the grouping. A later unchanged comparison on the other
saved hash-selected 1,000-note corpus would test generalization. Both are
suggestions, not started or authorized by this record.

### Information duplicated between the six combined-vector sections

The user authorized inspecting the saved six-section fit for repeated information.
This is read-only analysis of existing ASv6.100/Bootstrap-v133 meanings, vectors,
fine groups and assignments. No clustering, encoding, model calls or policy
changes are performed. Section numbers below refer to numerical fit labels,
not generated canonical titles or immutable canonical meanings.

Across 5,336 entries, 27 exact title wordings occur in multiple sections,
covering 76 entries. The matched meaning-only broader fit split 51 title
wordings covering 230 entries, with exactly the same fine groups. These are
retrieval counts, not semantic error counts: Strategy means an overall plan in
section 5 and the company formerly named MicroStrategy in section 3. Rooms
means physical rooms in section 2 and logical communication rooms in section 5.
Inquiries separates investigations in section 5 from information-seeking
questions in section 6. These different senses should not be merged by title.

No byte-identical full meaning occurs in different sections. Manual inspection
nevertheless finds duplication under paraphrases and alternative names:

| Topic and original entries | Combined sections | Information shared by the meanings |
|---|---|---|
| Cinema: L05044 / L05305 | 5 / 2 | The art and medium of motion pictures |
| Construction: L04117 / L05185 | 2 / 5 | Physically creating buildings, infrastructure and structures |
| Commenting: L00217 / L04959 | 4 / 6 | Communicating remarks or observations about a topic |
| Claims: L02403 / L03937 | 4 / 6 | Assertions presenting something as true |
| Rebates: L00076 / L01606 | 3 / 2 | Returning or crediting transaction payments to the payer |
| Zap payments / Zaps: L05275 / L05325 | 3 / 4 | Lightning bitcoin tips expressing social-media support |
| United States Department of Justice / U.S. Department of Justice: L02948 / L00948 | 1 / 2 | The same federal law-enforcement and justice department |

These are agent-inspected witnesses, not new human labels or a sampled error
rate. Definition differences can affect exact equivalence; the table identifies
shared information, which is the user's review concern. Cinema and Rebates were
together in the meaning-only fit and separate in the combined fit. The other
five inspected witnesses were already split. The combined representation thus
reduces the literal-title split screen overall while introducing some new splits.

Six of these seven pairs are reciprocal nearest other entries by combined
cosine over all 5,336 inputs: Cinema, Construction, Commenting, Claims, Rebates
and the Justice department. Their combined pair scores range from 0.7977 to
0.9784. The Zap pair has still-closer variants within its own respective fine
groups. The vectors already contain useful connections; their absence from the
section layout is not solely absence of similarity signal. A cosine cutoff is
not adopted, and high similarity alone is not treated as equivalence. Nearest
meaning searches also retrieve related but distinct topics such as a news
portal and its reported subject, or content and its display device.

The saved state explains two mechanisms. HDBSCAN groups are kept intact, but
different groups and unassigned entries are routed independently by summed
entry-to-center cost. There is no requirement to coassign a close pair across
those units. Both Rebates entries are independent: one prefers finance at
0.3810 versus 0.3644 for section 2; the other prefers section 2 at 0.3693 versus
0.3662 for finance. Their pair similarity is 0.9784, yet those small independent
center preferences split them. Construction L05185 individually prefers
section 2, but its nine-entry Builds/Lego/Construction fine group goes to
section 5. The Justice-department synonym similarly moves with a five-entry
Courts/Judges group. Assigning each original entry once and keeping every fine
group intact does not ensure that paraphrased information stays in one root.

All source/code/native hashes, original identities, group constraints, selected
costs and member-mean centers validate through the existing research paths.
Audit evidence is ignored on the external drive, linked at
`oracle-mvp-root-information-audit-v1/target/root-information-audit-v1/audit.json`.
It retains all 27 split-title families with complete meanings, ranked cross-root
meaning matches for every section pair, seven inspected witnesses, their
nearest entries and center/group routing, plus different-sense controls.
The task worktree remains for this evidence path; source hierarchies and saved
producer files are unchanged.

The next suggested component test is whether requiring reciprocal nearest
matches to stay together can reduce these splits while preserving different
senses and the coverage/size requirements. This targets connections already
present in the saved vectors without choosing a new fixed similarity cutoff.
It remains an untested hypothesis; the seven post-selected witnesses alone do
not establish that such a rule generalizes or is safe to adopt.

### Reciprocal nearest matches before broader section assignment

The user authorized this component test following the cross-root information
audit. Use the same 5,336 HR36 entries, paired title/meaning vectors, 451 completed
combined HDBSCAN groups, 2,518 independent entries, six sections, eight seeds
and 50-iteration limit. Reuse the saved combined-scoring result as baseline.
No reference-count screen, new encoding, model call or training is needed.

The existing research-panel preparation accepts `reciprocal_nearest: true`
only with `preserve_groups: true`. Each selected entry chooses its closest other
entry by combined cosine across the selected inputs. A pair joins only if both
choose each other; exact score ties choose the first original input row. Existing
fine groups remain intact, so joins between their members connect entire groups,
including any resulting chains. The resulting units use the unchanged summed
original-entry cost and original-entry mean-center updates. Pair indices and
resulting memberships are frozen before section assignment. No similarity
cutoff or semantic review labels enter selection.

This bounded exact reference search uses blocked products, O(n squared times
dimensions) arithmetic and O(256 times n) temporary scores rather than a full
stored pair matrix. At 5,336 entries it examines about 28.5 million ordered
pairs in 1,536 dimensions, once before the eight starts. It does not establish
that exact all-pairs search is suitable for a much larger corpus; a scalable
neighbor index would need separate qualification before production adoption.
Stored pairs and group memberships are linear in entry count. HiGen is unchanged.

Predeclared inspection includes the seven duplicate witnesses from the preceding
audit and the Strategy, Rooms and Inquiries different-sense controls. Same-root
membership alone does not establish that different meanings were conflated:
roots may be broad. Inspect which meanings the new pair constraints actually
join, as well as residual split topics, complete section memberships, distinct
note coverage and per-section counts. These selected controls are diagnostic
evidence, not an independent semantic accuracy estimate.

Two failing-first production-path tests demonstrate missing joins before the
change, then pass through preparation, actual section CLI execution and saved
resume. They cover transitive joins across existing groups, intact memberships,
reciprocal-only tie behavior, self-exclusion, singleton input and invalid flags.
All 63 relevant checks pass, including current native HDBSCAN validation and
default panel behavior. This adds a research option, not a HiGen policy.

The matched six-section fit completes. Preparation finds 1,176 reciprocal entry
pairs, of which 461 cross the original indivisible units. Joining them reduces
2,969 units to 2,508. The largest resulting unit has 62 entries; there is no
collapse to one giant component. All original fine groups remain intact.
All eight starts converge, using the same initial center entries as the saved
baseline for each seed. The selected seed remains 20261018. Its section note
counts are 334, 554, 294, 479, 442 and 406. Coverage remains 937/1,000 (93.7%)
by construction, every section exceeds 100 notes, and the six choices retain
the same broad themes as before. After matching labels, 263/5,336 entry
assignments change. Recorded fit time across eight starts is 5.79 seconds,
excluding input preparation and nearest-neighbor calculation.

| Diagnostic | Saved baseline | Reciprocal constraint |
|---|---:|---:|
| Inspected duplicate witnesses split between sections | 7/7 | 1/7 |
| Exact-title families occurring in multiple sections | 27 | 9 |
| Entries belonging to those split-title families | 76 | 41 |
| Distinct source notes retained | 937 | 937 |

Cinema, Construction, Commenting, Claims, Rebates and the two Justice-department
names now each share a section. Zap payments versus Zaps remains split between
finance (3) and networking/publishing (4). These are seven post-selected
agent-inspected witnesses, not independent semantic gold. The literal-title
screen is likewise not an error count: Strategy and Inquiries still have
legitimate different senses in separate sections.

There are two important limitations. First, the new rule also joins physical
Rooms (L00685) with logical communication Rooms (L01303), moving the latter from
section 5 to section 2. Their title cosine is 0.9851, meaning cosine about 0.5053,
and combined cosine 0.7452. In meaning space their nearest other entries are
Floors and Probe acknowledgments respectively. Their combined mutual match
therefore does not establish shared meaning. Broad roots may contain different
meanings; coassignment itself is not proof of a wrong root, but this control
shows why reciprocal matching cannot be treated as an equivalence detector.
The Strategy plan/company distinction and Inquiries investigation/question
distinction remain in separate units and their respective original sections.

Second, Payments becomes a new split: L01784 and L03918 remain in finance (3),
while L02582 goes to section 2. These definitions all describe transfers of
money or value. The first two form a reciprocal pair; the third chooses L03918,
but L03918 chooses its closer Payments counterpart, so no reciprocal edge joins
the third. Keeping all mutual pairs intact thus does not preserve an entire
topic with several variants. This is a new counterexample, not hidden inside
the improved aggregate screen. Nineteen previously split title families stop
splitting, eight remain, and Payments is added, giving nine total.

Adding a requirement for meaning-only reciprocity is not an established fix.
On these same inspected witnesses it would remove the Rooms edge, but also
remove the direct Cinema, Commenting and Claims edges; their closest meaning
neighbors are other related headings. No additional constrained fit using that
requirement was run.

Independent blocked nearest-neighbor reconstruction reproduces all pairs.
A separate sparse connected-component calculation reproduces every final unit
from original groups plus those pairs. Existing native/panel validation checks
frozen hashes, original rows, all original and new group constraints, normalized
centers, objectives and note counts for every start. Completed fit bytes are
unchanged on resume. All 63 checks pass on combined main. Generated evidence is
ignored on the external drive, linked from the retained executed worktree at
`oracle-mvp-reciprocal-section-groups-v1/target/reciprocal-section-groups-v1/`:
the frozen spec/panel, runtime and complete `comparison-and-verification.json`.
Source checkpoint is `100fdb6b`; the worktree remains for frozen execution and
artifact paths. No inference, encoding, training, UI or HiGen activation occurs.

Next suggested component test: allow an entry that points into a reciprocal
group to join that group, while measuring unwanted connections and any large
components. Payments motivates this directly: a third definition finds its
matching topic but is excluded solely by one-to-one reciprocity. This would
test that remaining mechanism without introducing a fixed cosine threshold.
It is not yet implemented, run or approved for adoption; the present improvement
does not establish a general root-distinctness guarantee.

### One-pass attachments into reciprocal groups

The user authorized testing whether an entry can join the reciprocal group
containing its nearest other entry. The Payments witness motivates this directly.
Use exactly the same saved HR36 inputs, combined vectors, original fine groups,
eight seeds, six sections and limits. Reuse the completed reciprocal-only panel
as baseline. No new encoder work, inference, training or count screen is needed.

Research-panel preparation adds `attach_nearest: true`, requiring
`reciprocal_nearest: true` and the existing group-preservation option. First
form the reciprocal groups as before. Freeze which resulting units contain
reciprocal pairs. An entry in an unmatched unit can attach if its nearest other
entry is in one of those frozen matched units. Compute all attachment choices
before applying them; an entry newly attached during this pass cannot attract
another entry. Already matched units do not initiate attachments. Existing fine
groups stay intact, so attaching one member brings that whole unit. Multiple
members pointing into different matched units can indirectly connect those
units; record resulting component sizes rather than silently choosing one.

Nearest entries and reciprocal pairs are unchanged and computed only once.
This adds linear work over the existing nearest-neighbor results plus group
unions. It does not solve the exact-search scaling limitation described above.
Original entry weights and section scoring remain unchanged. The frozen plan
retains both reciprocal pairs and directed `nearest_attachments` indices.

Failing-first CLI/preparation tests show the missing third-entry attachment,
then pass with the new option. They cover the bounded one-pass rule, preserving
an existing group during attachment, unchanged reciprocal-only behavior,
singleton inputs, invalid flags, actual section fits and immutable saved resume.
All 65 current checks pass. This remains a component experiment, not a HiGen
change or evidence that a nearest match establishes semantic equivalence.

The matched fit completes with 1,215 attachments from 1,215 previously unmatched
units into the 818 frozen matched units. Total units fall from 2,508 to 1,293.
No two matched units are merged indirectly in this dataset. The largest unit
grows from 62 to 71 entries. The six selected section note counts are 337, 511,
363, 340, 410 and 463; their union remains 937/1,000 (93.7%), with every section
above 100 notes. All eight starts converge using the same per-seed initial
entries as the reciprocal-only baseline. The best seed changes from 20261018
to 20261024. Eight fits take 4.15 seconds total, excluding preparation/search.
After matching labels, 1,558/5,336 entry assignments change. This is not an
accuracy score or evidence that every change improves browsing.

| Diagnostic | Reciprocal-only baseline | One attachment pass |
|---|---:|---:|
| Seven original duplicate witnesses split in the selected fit | 1/7 | 0/7 |
| Roots containing the three Payments definitions | 2 | 1 |
| Exact-title families appearing in multiple roots | 9 | 4 |
| Entries belonging to split-title families | 41 | 22 |
| Distinct source notes retained | 937 | 937 |

Payments' third definition now joins the other two in the same unit, addressing
the proposed mechanism. The six earlier directly constrained witness pairs
remain intact. Zaps shares a root in the selected fit but remains in separate
units: it shares a root in seven of eight new starts, versus six of eight
baseline starts. Its apparent repair is not a new must-stay-together constraint
and is not guaranteed across starts.

Remaining split titles are Donald Trump, Communication, Deals and Strategy.
Fifteen Trump definitions share section 4; the CNN/Dana Bash wording L02400
lands in section 1. Communication spans broad human/artificial message exchange
in section 2 and interpersonal communication in section 6. These retain shared
information or need scope review. Deals distinguishes agreements from favorable
purchase offers; Strategy distinguishes planning from the company. Thus four
split names are not four independently validated errors. The previous nine
split names lose seven and gain Deals and Communication, leaving four.

The different-meaning controls also expose forced coassignment. Physical and
logical Rooms remain in one unit, now also containing Floors. The question
meaning of Inquiries joins its two investigation meanings in another unit.
Strategy's plan/company meanings remain separate. Broad roots may contain
different meanings; these joins are not by themselves proof of wrong root
membership, but nearest-neighbor constraints must not be described as semantic
equivalence. Original titles, meanings, IDs and note evidence are unchanged.

Independent nearest-neighbor reconstruction reproduces every reciprocal pair
and all frozen one-pass attachment eligibility. Sparse connected components
independently reproduce all final units. Original group preservation, attachment
constraints, normalized centers, costs, notes, frozen hashes and byte-preserving
resume validate. All 65 current checks pass on combined main. Source checkpoint
is `bbde4812`; ignored evidence is on the external drive, linked under the
retained executed worktree's `target/nearest-group-attachments-v1/`:
the frozen spec/panel, runtime and `comparison-and-verification.json`.
The worktree remains for frozen code and artifact paths. No inference, encoding,
training, UI refresh or HiGen activation occurs.

The next suggested test is the unchanged method on the other saved hash-selected
1,000-note corpus. This would check whether the reduction in split information
and the size/coverage results generalize beyond the corpus that supplied these
post-selected witnesses, while exposing further joins between different meanings.
That test has not been started or authorized by this record.

### Manual unchanged attachment test on the second thousand-note corpus

The user approved manually testing the unchanged method on HR37's saved corpus,
without HiGen integration. Use existing numerical CLIs only: ASv6.100 and
Bootstrap-v133 meanings, saved title vectors, equal-weight title/meaning cosine,
native HDBSCAN minimum cluster size 2 / minimum samples 3 / EOM, six sections,
the same eight seeds 20261018–20261025 and 50 iterations. No new source code,
encoding, model calls, training or parameter changes occur. This is not a new
official HR experiment. Full raw-corpus IDs confirm no overlap with HR36.

HR37 provides 5,189 usable entries from 912 of its 1,000 hash-selected notes;
88 lack usable saved inputs. Matched HDBSCAN produces 436 groups and 2,378
independent entries. Compare three existing stages with identical entry rows,
weights and per-seed initial centers. Notes remain fully eligible in every arm.

| Stage | Indivisible units | Largest unit, entries | Split-title families | Entries in that screen |
|---|---:|---:|---:|---:|
| Combined vectors and existing fine groups | 2,814 | 91 | 24 | 115 |
| Add reciprocal nearest matches | 2,346 | 92 | 8 | 70 |
| Add one frozen attachment pass | 1,154 | 104 | 1 | 4 |

There are 1,154 reciprocal pairs and 1,192 attachments into 764 matched units.
No matched units merge indirectly. The final six section note counts are
383, 553, 325, 306, 414 and 475. Their union is 912/1,000 (91.2%), unchanged by
construction; every section exceeds 100 notes. These note sets overlap and
should not be summed. The selected final seed is 20261019. All eight final
starts converge. One unselected reciprocal-only start, seed 20261023, reaches
50 iterations without convergence; its limit and result are preserved.

The only residual split title is Trends: three definitions describe general
directions or patterns of change over time, while another describes topics
gaining audience attention. Their separation is plausibly a meaning distinction,
not an established error. Manual checks also find Bill Gates aliases, organized
Events, Knowledge and both logical communication Rooms definitions together.
Different roles under Peace—emotional tranquility and nonviolent relations—now
share a root. Broad root membership does not establish equivalent meanings.

Differently named topics still expose shared or related information across
roots. Suggestions in section 5 and Recommendations in section 6 overlap;
Central banks in section 1 and US Federal Reserve in section 3 form a broader/
narrower relationship. The method does not enforce semantic parent-child
constraints or guarantee complete root distinctness. All 15 pairs of sections
retain ranked cross-section vector matches for manual inspection. This is a
cross-corpus numerical improvement with bounded agent checks, not an exhaustive
semantic accuracy measurement. No canonical titles or meanings were generated.

Native grouping takes 12.84 seconds. The three observed panels run concurrently
on CPU sets 0–7, 8–15 and 16–23, leaving four cores free; their eight six-section
fits sum to 11.31, 11.21 and 12.15 seconds per arm respectively, excluding
preparation and search. These concurrent timings are not a speedup benchmark.
Independent nearest-neighbor reconstruction, one-pass eligibility, sparse group
components, original group preservation, centers, costs, note counts, frozen
hashes and byte-preserving resume all validate. No behavior changed, so no new
implementation tests or additional count-reference screen were introduced.

Ignored evidence is on the external drive, linked from
`oracle-mvp-second-corpus-attachments-manual-v1/target/second-corpus-attachments-manual-v1/`:
the frozen grouping and section specs, actual native groups, all three panels,
runtime, `cross-section-matches.json` and complete `comparison-and-verification.json`.
Executed source checkpoint is `f23e861c`; the task worktree remains for frozen
code and artifact paths. No HiGen policy, hierarchy or review UI is changed.

A useful next manual component test is one child level beneath the largest
resulting root. Root breadth is permitted because deeper levels should narrow
the choices; that test would check whether the same method actually provides
useful narrowing before a hierarchy-construction integration proposal. This
further test has not been started or authorized by this record.

### Manual child subdivision beneath the largest second-corpus root

The user authorized one child level beneath the largest root in the preceding
manual result. This selects numerical section 2 of NearestAttachments: 1,307
original entries representing 553 notes. Keep its existing native fine groups
intact and recompute reciprocal matches plus the single attachment pass within
these selected rows. There is no new native HDBSCAN grouping, encoding, prompt
or HiGen integration. Keep equal-weight title/meaning vectors, six fixed child
sections, eight seeds and 50 iterations. This tests subdivision at a fixed
width, not automatic child-count selection or a recursive stopping rule.

Reuse the existing research-panel label selector with the frozen actual parent
result and original full source rows. A minimal compatibility change lets that
selector read this CLI's wrapped `panel.best.labels` output as well as existing
direct `best.labels` files. It does not change selection or scoring for existing
inputs. A failing-first test reproduces the unsupported native parent format,
then verifies actual CLI child selection, original row/note identities, useful
toy subdivision and rejection after a frozen parent result changes. All 66
relevant production-path checks pass.

Use a zero assignment minimum as before; inspect every child's distinct-note
set against the 553-note parent and check duplicated information between the
children. The 100-note root requirement is not silently imposed on children.
All parent entries stay eligible. Any note-set overlap between children is
separate from repeated information, as in the root-level review.

The completed split keeps all 1,307 entries and all 553 notes. Every child
represents a distinct, strictly smaller note set. The following descriptions
summarize common existing headings; they are not generated canonical names.

| Child | Common existing headings | Distinct notes |
|---|---|---:|
| 1 | Music, Cooking, Diet, Recipes, Trees, Outdoors, Coffee | 154 |
| 2 | Basketball, War, Sports, Games, Military personnel | 162 |
| 3 | Food, Companies, Travel, Economy, Energy, Houses | 196 |
| 4 | Donald Trump, Art, Films, Entertainment, Photography | 146 |
| 5 | Murder, Imprisonment, Crime, Punishment, Lawsuits | 44 |
| 6 | Politics, Police, Regulation, Voting, Protests | 91 |

Note sets overlap and should not be summed. All eight starts converge. The
selected seed is 20261019; its six-section fit takes 0.039 seconds, and the eight
fits together take 0.386 seconds, excluding preparation and verification.
The selected fit splits no repeated exact title between children. This is a
numerical narrowing result, not proof that the choices contain distinct
information. Broad or mixed topics alone are not rejection criteria.

Full meanings expose remaining overlapping information. Cooking in child 1
includes preparing food, while Food preparation L02693 in child 3 explicitly
includes cooking. Fighting in armed conflict L00006 is in child 2; Attacks in
armed conflict L01275 is in child 5. President Donald Trump L03320 is in child
4, while Presidents L03212 in child 6 explicitly includes Donald Trump. These
are overlapping scopes or broader/narrower relationships, not automatically
equivalent meanings. They are bounded manual witnesses, not an error rate.

Food preparation supplies a concrete attachment witness. It is unassigned in
the original combined-vector native grouping. The frozen attachment pass joins
it to Food L02692; its direct combined cosine with that entry is 0.8245, versus
0.7441 with Cooking L00001. The resulting 16-entry unit is assigned to child 3.
Against the selected final centers, Food preparation individually favors child
1 (0.4749 versus 0.4374 for child 3), but the whole unit's summed cost controls
its assignment. Thus the attachment constraint, rather than an original native
group, forces this entry away from its individually preferred child. This
does not establish that all attachments should be removed: Cooking and Food
preparation share a child in seven of eight total starts, while the minimum-cost
selected fit separates them. Combat/attacks share a child in four starts;
Trump/presidents in five. Reviewing the saved starts also finds no repeated
exact-title splits in any start. Four starts keep all three witness pairs
together, with costs 1.71–2.53% above the selected fit. The second-lowest-cost
start, 0.23% above the selected fit, keeps Food preparation with Cooking but
still separates the other two pairs. These post-selected checks do not qualify
an alternative fit or establish a semantic accuracy score. The numerical
objective does not certify the information boundaries.

Independent dense nearest-neighbor reconstruction reproduces all 301 reciprocal
pairs and all 356 frozen attachments. Sparse connected components reproduce
the 255 final units without merging matched units indirectly. Original native
fine groups and the inherited parent units remain intact. Parent bindings and
selected original rows, frozen source hashes, centers, costs, note counts for
all starts, and byte-preserving completed resume validate. Source checkpoint
is `44081e94`; its 66 relevant production-path checks pass on combined main.
Ignored evidence is retained on the external drive, linked under
`oracle-mvp-second-corpus-child-manual-v1/target/second-corpus-child-manual-v1/`:
the frozen spec/panel, cross-child matches, `all-starts-review.json` and complete
`comparison-and-verification.json`. The worktree remains for frozen source and
artifact paths. No model calls, new encoding, training, HiGen activation or UI
refresh occur.

A useful next component test is a matched child split without the optional
attachment pass, keeping the original fine groups, reciprocal constraints,
vectors, seeds and objective fixed. Food preparation supplies a concrete reason
to isolate this constraint. Check both the information boundaries and any
return of split definitions: removing attachments may improve one at the
expense of the other. This would test the component's net contribution at
child level rather than picking a preferred start from reviewed witnesses.
That further fit has not been started or authorized by this record.

### Manual unchanged child splits beneath all six second-corpus roots

The user questioned whether separating Cooking and Food preparation was bad.
The clarification is that related scopes, shared notes, or an entry being
assigned away from its individually closest center do not establish a bad
browsing choice. The attachment-removal proposal above was not authorized or
run. The user instead approved keeping the method unchanged and testing the
other five roots, then reviewing retention, useful narrowing and clearly
redundant or confusing choices across the two levels.

Reuse the completed section-2 child result exactly. The existing numerical
panel CLI prepares and runs sections 1, 3, 4, 5 and 6 from the same frozen
original entry rows and actual parent labels. Native fine groups stay intact;
reciprocal matches and one frozen attachment pass are recomputed within each
parent. Vectors, six fixed children, eight seeds, zero assignment minimum and
50 iterations are unchanged. The five runs execute concurrently on CPU sets
0–23, leaving four logical CPUs free. No source implementation changes occur.

| Numerical root | Parent notes | Six children: distinct notes | Largest child / parent |
|---|---:|---|---:|
| 1 | 383 | 87, 50, 66, 195, 76, 119 | 50.9% |
| 2, reused | 553 | 154, 162, 196, 146, 44, 91 | 35.4% |
| 3 | 325 | 92, 41, 80, 102, 67, 45 | 31.4% |
| 4 | 306 | 30, 74, 60, 137, 72, 60 | 44.8% |
| 5 | 414 | 193, 43, 85, 122, 116, 80 | 46.6% |
| 6 | 475 | 238, 109, 87, 54, 60, 120 | 50.1% |

Every one of the 36 children represents a strictly smaller subset of its
parent's notes; within each parent, the six child note sets are distinct.
Each parent's children retain its complete original
note set. The two-level union remains 912/1,000 notes (91.2%); the 88 notes
without usable saved inputs remain unavailable. All 5,189 usable entries stay
assigned once at each level. Note sets overlap and must not be summed.
All 48 six-section starts converge, including the eight previously saved
section-2 starts. The 40 new six-section fits sum to 1.849 seconds of observed
fit time, excluding preparation, verification and scheduling. This is not an
end-to-end speed benchmark.

Common headings show several interpretable distinctions. Section 1's children
separate money/payments, network relays, prices/fees, Bitcoin, financial markets,
and Nostr. Section 4 offers work/upkeep, computers/debugging, science/testing,
software/tools, AI, and named products/companies. Section 6 separates knowledge/
questions, people/support, positive feelings, privacy/freedom, humor, and
problems/warnings. These are agent summaries of membership, not synthetic
canonical titles or fixed definitions. Geographic section 3 is less intuitive:
its U.S. Midwest entries share a child with European places, while Iran is
apart from Israel/Bahrain. Mixed membership warrants review but does not alone
prove duplication or a false semantic relationship.

Only one of 549 repeated exact-title families within these parents is split
between selected children: Data availability L01855/L05187, between section
5's timestamp and data/version choices. Its meanings retain different amounts
of post-specific interval detail, so the title screen is not a semantic error
rate. Neither entry is originally grouped in the current combined-vector
producer; old `source_group` labels are not the producer used by this test.
L01855 points toward L05187, which itself attaches to Data. Frozen one-pass
eligibility leaves L01855 separate because L05187 was not in a matched unit
when eligibility was established. This records the mechanism without silently
turning the method into recursive attachment.

A clearer differently named duplication is Bitcoin satoshis L01557 in section
1 child 4 versus Satoshis L00097 in child 6. Both explicitly define a unit equal
to 0.00000001 BTC. L01557 attaches to Bitcoin amounts L04424: combined cosine
0.8295 versus 0.7922 with L00097. Against L00097, meaning cosine is 0.9714 but
title cosine is 0.6130. Thus the unchanged equal-weight combination favors the
broader amount wording; the two synonymous unit definitions remain in
different indivisible units and selected children. Both individually favor
their assigned centers, so this is not the earlier Food preparation center-
override mechanism. This is an agent-assessed duplicate-information witness,
not new human gold or a measured corpus-wide error rate. Preserve it as a
regression rather than treating one case as grounds for a redesign.

Independent dense nearest search and sparse connected components reproduce
every parent's reciprocal pairs, frozen attachment eligibility and final units,
without indirectly merging matched units. Original native groups and inherited
parent units stay intact. All source hashes, parent bindings/row selections,
per-start costs/centers/note counts, note-set refinement and byte-preserving
completed resumes validate. Source checkpoint is `f4df4c6d`; no source behavior
changed and no additional implementation test suite was needed.

Ignored evidence extends the retained child-test worktree's
`target/second-corpus-child-manual-v1/remaining-roots-v1/`: the frozen spec/panel,
`comparison-and-verification.json`, all 90 child-pair ranked match lists in
`cross-child-matches.json`, and original definitions plus routing evidence in
`review-witnesses.json`. Prior section-2 evidence remains unchanged. The
worktree remains for these frozen source and artifact paths. No model calls,
new encoding, training, HiGen activation, official HR registration, or UI
refresh occur.

The result supports continuing the unchanged method, with the retained
duplication and geographic qualifications. A useful next manual component test
is one further split beneath the largest remaining child, section 6 child 1
(238 notes). This would test whether substantial narrowing continues at the
next depth before attempting recursive construction. Six remains a fixed test
count, not an adopted child-count or stopping rule. That deeper test has not
been started or authorized by this record.

### Manual third-level split within second-corpus section 6 child 1

The user authorized the proposed further split of the largest remaining child:
section 6 child 1, containing 328 original entries from 238 notes. Keep the
original native fine groups and recompute reciprocal matches plus one frozen
attachment pass within these entries. Use unchanged equal-weight title/meaning
vectors, six children, eight seeds, zero assignment minimum and 50 iterations.
This is one further manual component test, not automatic recursion or adoption
of a six-child stopping policy. No encoding, training or model calls occur.

This requires selecting labels from a saved case that already uses a subset
of the full source rows. The existing label selector gains an optional `plan`
path to that saved result's actual producer plan. Both result and plan must be
hash-pinned in the source's `files`. Preparation validates the result's producer
binding, exact original vectors/notes/entry metadata, row mapping, grouping
dependencies and saved costs/centers/counts, then maps selected local positions
through the producer's original row indices. The default full-row selectors
are unchanged. Earlier frozen worktree source files and artifacts stay intact.

A failing-first production CLI test uses noncontiguous original rows 1, 3 and 5,
selects two rows from their completed saved partition and runs the next split.
Before the extension, preparation fails because the three saved labels cannot
align directly with six original rows. The test then verifies exact original
IDs/notes, a real two-child split, rejection of a mismatched result/producer
binding, rejection of an unpinned producer plan, and failure after that frozen
plan changes. All 67 relevant checks pass, including native HDBSCAN and existing
selector/group/attachment/numerical checks.

The completed split retains all 328 selected entries and all 238 parent notes.
All six child note sets are distinct and strict subsets of that parent. The
largest contains 78/238 notes (32.8%). The full corpus's previously observed
912/1,000 coverage is unchanged. Counts below overlap and must not be summed.
These descriptions summarize existing headings; no synthetic canonical title
or meaning has been generated.

| Child | Common existing headings | Distinct notes |
|---|---|---:|
| 1 | Truth, Verification, Skepticism, Honesty, Truthfulness | 31 |
| 2 | Knowledge, Uncertainty, Learning, Interpretation, Discovery | 78 |
| 3 | Predictions, Recommendations, Expectations, Advice, Plans | 74 |
| 4 | Time, Calendar dates, Morning, Clocks, Time intervals | 16 |
| 5 | Opinions, Arguments, Comparisons, Opinion formation, Analysis | 38 |
| 6 | Requests, Questions, Reminders, Appeals, Conversation | 51 |

All 49 repeated exact-title families stay together in the selected fit. The
bounded cross-child review finds related but distinct roles: uncertainty about
the future versus expectations, taking action versus calls to action, and
opinions versus requests for opinions. Related wording does not make those
automatic duplication errors. Verification versus assessment of claims and
interpretation versus detailed analysis retain some overlapping scope for
review; no new equally clear Satoshis-style duplicate is established by the
inspected matches. This is an agent assessment, not semantic certification or
a measured accuracy rate. The result supports useful narrowing at this next
depth without a new reason to change the method.

The selected seed is 20261021; all eight starts converge. Their fit times sum
to 0.043 seconds, excluding preparation and verification. Filtering the
original native fine groups gives 194 initial units. There are 75 reciprocal
pairs and 92 frozen attachments into 57 matched units, producing 74 final
units. Independent dense nearest search and sparse connected components
reproduce these constraints without indirectly merging matched units.
Immediate parent units also remain intact. Frozen source/code/grouping hashes,
nested producer bindings and exact original rows, all per-start costs/centers/
notes, strict refinement and byte-preserving completed resume validate.

Executed source checkpoint is `0019a0ce`, also verified on combined main with
all 67 relevant checks passing. Ignored evidence is on the external drive,
linked under `oracle-mvp-third-level-child-manual-v1/target/third-level-child-manual-v1/`:
the frozen spec/panel, `comparison-and-verification.json`, and ranked matches
for all 15 child pairs in `cross-child-matches.json`. The worktree stays for
these frozen source and artifact paths. No model calls, new encoding, training,
HiGen activation, official HR registration or UI refresh occur.

Six was fixed for these component tests; they do not implement automatic
child-count selection or recursive construction. The subsequent investigation
and approved next construction boundary are recorded below. These saved
results remain unchanged.

### Approved construction boundary: finish at the existing intact groups

The user authorized investigating stopping and fewer-than-six children. First
review the earlier failures rather than repeat the same reference simulations:
the adjacent gap rule stopped some broad mixtures; the global rule split US
dollar descriptions and Nostr wording into artificial choices. Those results
did not qualify an automatic semantic stopping score. The current method has
since gained group constraints, which already define the smallest parts it
can separate. Test that existing resolution boundary before adding a new score.

After the manual checks below, the user approved this construction rule and
explicitly separated review-UI note display from hierarchy construction:

1. With more than six current intact groups, retain the existing six-way
   broader subdivision.
2. With at most six current intact groups, use those existing groups directly
   as leaves; do not recluster them or create empty extra choices. A single
   remaining group is already a leaf, without an additional copy beneath it.

This construction rule neither specifies how the review UI reveals notes nor
uses a one-note count as a separate construction stopping condition.

These are the groups already fixed by the completed parent calculation,
including its reciprocal and one-pass attachment constraints. Apply the
boundary before another context-local matching pass. Six is the user's browsing
limit, not a learned similarity threshold or a six-note stopping threshold.
The preference for using the available width in larger pools is a practical
short-path baseline; it is not proof that six always minimizes navigation or
that smaller broad counts are never better. Note-set refinement remains a
required check. This approved design does not introduce a repair policy for an
invalid terminal menu or activate a production stopping rule.

The read-only test validates nine existing producers from both saved thousand-
note corpora, including all current second-corpus root/child results and the
238-note deeper result. Inspect their 54 saved child cases. Fifty-one retain
more than six fixed groups and would continue. Three already fit the terminal
menu limit:

| Existing branch | Parent notes | Fixed groups / direct choices | Notes per direct choice |
|---|---:|---:|---|
| Time/calendar branch beneath section 6 child 1 | 16 | 4 | 6, 3, 6, 1 |
| Requests/conversation branch beneath section 6 child 1 | 51 | 6 | 17, 18, 6, 5, 4, 2 |
| Timestamp branch beneath section 5 | 43 | 4 | 34, 7, 1, 1 |

Every direct choice in these three cases is a distinct, strictly smaller note
set; every parent note remains represented. Counts overlap and must not be
summed. The cases are overlapping saved branches, not independent corpora or
new fitted partitions. No new cluster fit, reference simulation, encoding,
training or model call occurs.

Manual content review prevents treating that structural result as semantic
certification. The time branch separates clocks/time, dates/month names,
parts of the day, and two elements of one Frost poem. Its clocks/time group
also contains Our Time, explicitly a UATV news-video title. The timestamp menu
separates generic timestamps from specific publication times, plus Data
availability and a 2:1 ratio. The requests menu separates questions/requests,
conversation, appeals/verdicts, reminders, calls for attention/action, and probe
acknowledgments. Some inherited combinations or possible redundancies remain;
ending at fixed groups cannot repair their membership or certify good titles.

Repeated-topic controls demonstrate the intended protection without proving
accuracy. In the first corpus, all 62 Nostr headings occupy one 71-entry,
68-note unit, and the US dollar variants occupy one 20-entry, 20-note unit.
In the second, the currency variants occupy one 13-entry, 12-note unit.
Stopping at these units avoids splitting their wording again. The whole units
include other titles as well: the first Nostr unit includes InformNapalm,
Nansen and Wisp; the first Coffee unit also includes tea and beer. Those are
inherited grouping qualifications, not newly approved single-topic meanings.
The second corpus's Nostr headings span two units, so the proposal does not
magically resolve every alias or sense distinction.

A separate tiny diagnostic uses real entries from the saved time branch and
the production reciprocal/attachment function. With only Clocks and Calendar
dates, reciprocal matching necessarily joins them. Adding the yellow wood in
The Road Not Taken attaches it to that pair. The output has one group in both
cases. This does not establish that the inputs lack useful distinctions:
two entries have no other nearest-neighbor option. It supports exposing the
already accepted small set directly, rather than deriving a stopping signal
from forced matches after shrinking the pool.

All nine complete producer/source checks and byte-preserving resumes pass.
Direct choices reconstruct every selected entry, preserve all parent notes
and keep the existing groups intact. No implementation changed; the grouping
boundary is approved next design, not implemented HiGen behavior. The
independent source rows,
all direct-choice definitions, fixed protocol and validations are retained in
`/mnt/external/algos-archive/oracle-mvp/section-stopping-manual-v1/` as
`protocol.json`, `comparison-and-verification.json` and
`small_pool-nearest-diagnostic.json`. Source checkpoint is `abd5c8b7`. The
temporary documentation worktree is not a frozen execution dependency and can
be removed after integration; all retained producer worktrees stay unchanged.

The grouping boundary is approved with the qualifications above; note display
remains outside this design. Before integration, a complete small-corpus manual
construction would
test actual depth, note coverage and terminal menus together. That would be
more informative than another isolated successful split or a newly tuned
count statistic. Such a construction has not been run by this record.

### Complete small-corpus construction: research workflow

The user authorized that complete manual numerical test on the existing
100-note corpus, with the approved group boundary. `section_tree.py` provides
reusable offline construction from a validated completed six-section
`section_count_panel` case. This is research support, not a HiGen activation,
official HR run, synthetic-title generator or review-UI change.

Prepare freezes the root plan/result, code and original-corpus/root-minimum
checks. Run loads and validates the original source once, reuses the completed
root partition, and carries its fixed groups into each child. Before another
local nearest-neighbor pass, at most six groups become direct leaves; one
group is already a leaf. Larger pools receive the existing reciprocal and
frozen one-pass attachments, preserving every inherited group. If more than
six remain, use the unchanged six-section partitioner, fixed original-entry
weights and seeds, with zero assignment minimum. If the local pass leaves at
most six groups, expose those directly. A non-progressing fit is unresolved;
no arbitrary depth limit, note-count stop or automatic repair is introduced.

Per-node fits are bound to the frozen plan, original row indices and exact
groups. Resume validates costs, centers and assignments and preserves saved
bytes. Every original selected row must occur in exactly one terminal group;
all source notes must remain represented. Reports distinguish numerical
completion from root coverage/minimum and note-set-narrowing requirements.
Shortest and longest leaf routes count category edges only, without claiming
actual user effort or semantic accuracy. Existing headings describe the
result; no new canonical definitions are inferred.

Failing-first production CLI tests start with the absent complete-construction
command. The implementation tests an actual nested fit, intact group leaves,
the pre-matching six-group boundary, byte-preserving resume, and frozen
source/result rejection. An all-one-note fixture must still subdivide by
groups and report non-narrowing edges, explicitly preventing a UI note-display
rule from becoming a construction shortcut. The complete 100-note result and
content review will be recorded separately below.

### Completed 100-note fixed-group tree

Executed the approved complete numerical test from the existing HR22 corpus,
without changing or relabeling HR22. Inputs remain ASv6.100 / Bootstrap-v133:
728 original entries from 100 notes, with equal-weight saved title/meaning
vectors. All original entries are eligible, including the 399 left unassigned
by the initial native grouping. The 58 original HDBSCAN groups remain intact.
The initial reciprocal/frozen-attachment pass produces 204 fixed units.

The root calculation uses the unchanged six-section objective, eight seeds
20261018 through 20261025, 50 iterations, zero assignment minimum and a
30-second assignment limit. Its selected seed is 20261023. The ten additional
six-section fits use those same settings. All 88 fitted starts converge.
Root constraints are checked after fitting; they are not used to select a
different seed or reshape the result.

| Result | Observed |
|---|---:|
| Distinct notes represented | 100/100 |
| Root choices | 6 |
| Notes per root, in saved order | 64, 50, 76, 46, 44, 29 |
| Non-container nodes | 176 |
| Terminal intact groups | 132 |
| Maximum choices per menu | 6 |
| Maximum leaf depth | 4 |
| Mean shortest leaf depth per note | 2.71 |
| Median / P90 shortest leaf depth | 3 / 3 |
| Non-narrowing edges / duplicate sibling note sets | 0 / 0 |
| Unresolved subdivisions | 0 |

Root note counts overlap and must not be summed. Coverage is a retention
result, not semantic accuracy: the procedure assigns every input entry.
Each root exceeds the ten-note minimum; every child has a strictly smaller
distinct-note set. Every original entry occurs in exactly one final leaf,
every original native group and every initial fixed unit stays intact, and
all parent rows and notes survive their subdivision. The 132 leaves occur at
depths two (7), three (102) and four (23). Route depth counts numerical category
edges from the invisible container to a leaf; it does not include reading or
selecting notes and is not a measured navigation effort.

There are 34 direct terminal menus, containing two through six already-fixed
groups. They follow the pre-matching boundary without a further forced merge.
No separate note-count stopping rule is used. The largest leaf holds 44 notes;
this is the broad Food unit, rather than evidence that more numerical splits
within that unit were authorized.

Content review finds useful concentration and inherited limitations. All 32
Food headings end in leaf `3.2.1.1`, all 15 Nostr headings in `6.2`, and all
eight Bitcoin headings in `5.5.1`. All 61 repeated exact-title families stay
within one root. Four families span multiple leaves: Coffee, Foodstr, Food
preferences and Meat. This count is a diagnostic, not four semantic errors:
Foodstr's hashtag versus community and other contextual scope differences
need not be equivalent. Coffee remains a concrete redundancy concern:
four, eight and two Coffee entries occupy sibling leaves `2.2.2`, `2.2.3`
and `2.2.5`. Several are near-duplicate beverage definitions with optional
preparation variations; one also admits coffee beans. The split already
exists among the three initial fixed units, so the stopping rule preserves
it rather than causing a new split.

Some mixed leaves expose why structural success does not certify grouping:

- Leaf `2.1.1` combines cashews, coconut butter, cacao and the audience
  addressed as "Champs". The root pass attached audience entry `L00085` to
  cashews `L00052`; the mismatch predates recursive stopping.
- Leaf `3.3.5` combines Staub, stew, steaks and St Marks Place. The initial
  root pass paired stew `L00063` with steaks `L00479`, then attached both
  Staub `L00024` and the street `L00679` to stew. These four were already one
  fixed unit before the first root partition.
- Leaf `2.2.1` combines Buster + Punch, metal handles, matcha and melangers.
  Matcha `L00051` paired with melangers `L00601` in the initial root pass;
  handles `L00026` attached to melangers. In the smaller second-root pool,
  Buster + Punch `L00023` reciprocally matched the handles, joining that
  already-mixed unit. This isolates an additional local matching effect,
  rather than attributing every issue to the original native groups.

These are bounded agent assessments. They do not justify rejecting every
broad root, merging every repeated title, or changing the approved boundary.
The test supports complete construction with short paths and note retention;
remaining membership quality is upstream of the stopping choice. No canonical
titles/meanings or UI have been generated, and no HiGen policy is activated.

Source checkpoint `7069565e` is landed on local main. All 70 relevant production
and integration tests pass in the task worktree and on the combined main
checkout. A completed rerun validates the frozen files/results and preserves
them. Ignored evidence is under
`/mnt/external/algos-archive/oracle-mvp/hundred-note-group-tree-v1/`:
`spec.json`, `root-panel/`, `tree/plan.json`, per-node `tree/fits/`, complete
`tree/tree.json`, and compact all-node `tree/contents.txt`. The task worktree
`oracle-mvp-hundred-note-group-tree-v1` remains because these plans bind its
exact code paths. Existing producer worktrees and outputs remain unchanged.
No model calls, encoding, training, official HR registration or UI refresh
occurred.

### One-way attachment ablation: frozen at every depth

The user authorized comparing the same complete 100-note construction with
and without one-way nearest attachments. Preserve the corpus, paired vectors,
original native groups, reciprocal matching, seeds, assignment settings and
approved stopping boundary. This toggles attachments both initially and during
larger child-pool matching; it does not disable reciprocal matching or exclude
previously unassigned entries. Numerical assignment still includes every row.

The research tree previously required attachments at the root and hard-coded
them during deeper matching. It now accepts either existing root-panel
`attach_nearest` setting, freezes that value in its own plan, checks agreement
on resume and applies it at every depth. True retains the existing behavior;
false omits only that one-way pass. Historical saved source paths and plans
remain unchanged. No production HiGen behavior is activated.

A failing-first production CLI test adds an unmatched entry beside a matched
pair. With attachments it must join that fixed unit; without them it must
remain its own terminal group through real nested construction. Both modes
use the same original vectors and reciprocal groups. The test also checks
that every deeper attachment list is empty when disabled and rejects a tree
setting that disagrees with its frozen root producer. This qualifies the
experimental toggle, not its semantic outcome.

### Complete 100-note attachment comparison

Both constructions completed under source checkpoint `9678b36d`. The enabled
control reproduces every node, assignment, heading count and summary value
of the earlier complete 100-note tree exactly. The two prepared cases share
all source/vector rows, native groups, reciprocal pairs, seeds and numerical
settings; only `attach_nearest` differs. Both assign all original entries and
keep all 58 original native groups intact. Neither result has unresolved
subdivisions. No repairs or new stopping rules were applied.

| Measure | Attachments enabled | Attachments disabled |
|---|---:|---:|
| Notes retained | 100/100 | 100/100 |
| Root choices / maximum menu width | 6 / 6 | 6 / 6 |
| Initial fixed units | 204 | 386 |
| Non-container nodes | 176 | 499 |
| Terminal groups | 132 | 372 |
| Maximum leaf depth | 4 | 6 |
| Mean shortest leaf depth | 2.71 | 3.17 |
| Median / P90 shortest leaf depth | 3 / 3 | 3 / 4 |
| Non-narrowing edges | 0 | 8 |
| Menus containing duplicate child note sets | 0 | 12 |
| Food-heading leaves | 1 | 4 |
| Coffee-heading leaves | 3 | 4 |

These are structural category-edge depths, not measured user decisions or
semantic accuracy. The disabled result fails the existing strict note-set
narrowing check; this experiment does not decide how to repair such menus.
Its root note counts are 66, 50, 77, 47, 46 and 31, all above the ten-note
minimum. Root counts overlap. Disabling attachments retains coverage because
unattached entries remain independent inputs to numerical assignment.

The 158 initial reciprocal pairs are identical. Enabling the one-way step
adds 182 initial attachment links, reducing 386 units to 204, and 69 further
links across 11 child matching rounds. With attachments disabled there are
35 child matching rounds and 35 deeper six-section fits, versus ten deeper
fits with attachments. These link counts describe calculations, not labeled
correct relationships. Increased fragmentation appears both in extra small
leaves and in repeated descriptions: Food's 32 entries occupy one leaf with
attachments, versus four leaves containing 29, one, one and one entries
without them. Nostr and Bitcoin headings remain one leaf each in both modes.

The prespecified suspicious pairs do separate when attachments are disabled:

| Pair | Enabled | Disabled |
|---|---|---|
| Audience addressed as "Champs" / Cashews | One leaf | Separate leaves |
| St Marks Place / Stew | One leaf | Separate leaves |
| Buster + Punch / Matcha | One leaf | Separate leaves |

This is not three fully repaired groupings. Matcha and melangers remain
together without any one-way attachment because they are an initial
reciprocal pair. Thus attachment errors and reciprocal-pair errors both
exist. Conversely, removing all attachments loses useful concentration:
near-duplicate Food and Coffee descriptions gain extra leaves. Not every
repeated title implies equivalence; this is bounded content review rather
than a gold accuracy score.

The result supports retaining attachments as the current experimental
baseline, with a demonstrated quality tradeoff rather than blanket removal.
It does not establish an automatic selective attachment rule. A next
controlled test could separate initial from deeper attachments, because this
comparison disables both and cannot identify which stage contributes the
useful compression versus the additional mixed units. That further test is
a recommendation, not yet executed or adopted here.

All 71 relevant production/integration tests pass in the task worktree and
combined main. Both completed resumes preserve all 49 tree/plan/fit JSON
files byte-for-byte. Ignored evidence is external at
`/mnt/external/algos-archive/oracle-mvp/hundred-note-attachment-ablation-v1/`:
the two-case `spec.json`, `root-panel/`, `tree-AttachmentOn/`,
`tree-AttachmentOff/`, per-node fits and compact `contents.txt` in both trees,
and independent `verification.txt` / `resume-before.json`.
The task worktree `oracle-mvp-hundred-note-attachment-ablation-v1` remains
for the frozen code bindings. Earlier source worktrees and receipts remain
unchanged. No model calls, encoding, training, official HR registration,
HiGen activation or UI change occurred.

### Separate initial and deeper attachment settings

The user authorized the two missing combinations: initial attachments only
and deeper attachments only. This completes a two-by-two numerical comparison
with the existing all-enabled and all-disabled controls, on the same 100
notes. Reuse both completed root producers exactly rather than recluster
the roots. Keep all vectors, original groups, reciprocal matching, seeds,
assignment settings and the approved stopping boundary unchanged.

`section_tree prepare --child-attachments inherit|on|off` freezes an optional
independent deeper setting. The default still inherits the root producer's
setting. The root setting must continue to match its frozen source; the child
setting must be a boolean and is covered by the tree plan/result/fit bindings.
This is an experimental component-test option, not an activated HiGen policy.

The production CLI test first fails on the unavailable option. It then checks
both mixed combinations with an unmatched entry beside an intact matched
pair: an initial attachment survives when later attachments are disabled,
and a previously unattached entry can join during deeper matching when that
setting is enabled. Both modes retain their frozen original root grouping,
resume byte-for-byte and reject an invalid deeper setting. Existing tests
also require the default to inherit the original setting.
