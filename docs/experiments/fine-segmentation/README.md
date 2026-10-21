# Fine-segmentation qualification and characterization suite

Status: **controlled execution and automated scoring completed on 2026-09-01;
both candidates exceeded the semantic-review cap, so user dispositions remain
pending**. See the [v1 results](controlled-run-v1-results.md).

The controlled run evaluated two predeclared candidates as equal, separate
suite instances over the same fixtures, SSE vectors, opaque IDs, input orders,
and scoring rules:

- HDBSCAN* with `hdbscan-controlled-suite-config-v1`:
  `min_samples = 2`, `min_cluster_size = 2`, and excess-of-mass selection; and
- SNN with `snn-controlled-suite-config-v1`: `neighbor_count = 5`,
  `minimum_shared_neighbor_count = 2`, and
  `minimum_core_neighbor_count = 3`.

Neither candidate is selected or final-frozen by this declaration. One suite
instance evaluates exactly one candidate identity after that identity is
technically frozen, and the two instances preserve independent candidate
identities and outputs. Unless a document says otherwise, singular candidate
language and invocation counts in this suite are per instance. Shared fixture
and encoding work happens once.

Together, the two instances evaluate the requirements for repeated-subject
recovery, nearby-subject organization, lexical coincidence, unmasked context
and stability under irrelevant changes. The protocols below are their frozen
operational definitions. Experiment 2 characterizes organization
under unequal support and singleton sparsity; it does not impose a categorical
pass/fail rule for those conditions. Each experiment uses purpose-built
synthetic notes and manually specified masks. The old 53-vector collection is
not reused merely because it exists.

The suite is a dependency graph, not six independent pass/fail checklists.
Every check has one owner:

| Owner | What it establishes |
|---|---|
| Candidate conformance | The frozen candidate obeys its construction contract and does not change when one frozen input is permuted. |
| [`01-repeated-subject-recovery.md`](01-repeated-subject-recovery.md) | Basic repeated-subject recovery. |
| [`06-irrelevant-change-stability.md`](06-irrelevant-change-stability.md) | Stability under exact duplicates, an unrelated added subject, and combining independently recovered collections spanning separated semantic areas. |
| [`03-lexical-coincidence.md`](03-lexical-coincidence.md) | Shared words do not replace semantic relationships. |
| [`04-unmasked-context.md`](04-unmasked-context.md) | Unmasked material does not determine the fine-segment membership of a fixed mask. |
| [`02-nearby-subject-resolution.md`](02-nearby-subject-resolution.md) | Characterization of nearby-subject resolution under balanced, unequal, and sparse support, plus semantic-review capacity. |
| Final user review | Comparison of both complete frozen candidate records and the user's decision about what, if anything, advances to the next proof of concept. |

Experiment 2 owns density and sparsity. It does not also own unrelated-area
addition; Experiment 6 owns that concern.

Experiments 3 and 4 qualify the frozen SSE-plus-candidate combination. Their
candidate inputs remain opaque vectors, but their interventions re-encode
changed text or changed unmasked context through SSE and can change the
vectors. A failure can therefore arise from SSE geometry, candidate behavior,
or their interaction; it must not be attributed to the segmentation candidate
alone.

## Execution order and interpretation dependencies

Run both candidate instances through the same operational order:

```text
shared frozen representation boundary, fixtures, and exact inputs
                              |
                    +---------+---------+
                    |                   |
                    v                   v
            HDBSCAN* instance       SNN instance
                    |                   |
                    +---------+---------+
                              |
          each instance: candidate conformance
                              |
          Experiment 1 -> Experiment 6 -> Experiments 3 and 4
                              |
          Experiment 2 characterization for each instance
                              |
                 side-by-side evidence report
                              |
          assistant recommendation, then user decision
```

Experiments 3 and 4 may run in parallel after Experiment 6 execution.
Experiment 2 is last because it has the largest local workload and does not
produce one binary confirmation verdict. This order preserves artifact reuse
and simplifies reporting; it is not a semantic admission policy.

A valid semantic failure never suppresses a later experiment. Run every
semantically meaningful input for both candidates and preserve its result. Only
an integrity failure, including a candidate-conformance failure, may block the
affected candidate instance, exact input, or dependent comparison because those
outputs would be untrustworthy. The other candidate and independent inputs
continue. Local scientific prerequisites govern which conclusions are
available, not which routine candidate invocations are executed.

The graph ends in the user's decision, not an automatic Experiment 2 pass or an
assistant selection. The assistant may analyze the evidence and recommend a
candidate, revision, or stop; only the user may select and final-freeze a
candidate. Nearby-subject boundaries are deliberately not reduced to one
universal threshold. The primary human semantic reviewer is the user who
approved this suite. Experiment 2's semantic-review cap is 100 unique
cross-subject packets per candidate. Before encoding, freeze the
review-order derivation procedure and seed, the required evidence fields, the
review dispositions `proceed`, `revise candidate`, and `stop`, and the
requirement for a written rationale.

Here `proceed` means that one candidate record is complete enough to enter the
final comparison; it does not select that candidate. Derive the concrete review
order only after the evidence pool is immutable.

Before encoding, also freeze the decision-report schema, coverage-manifest
schema, and machine-checkable coverage validator and completeness rules. The
generated report and manifest must account for all 32 balanced configurations,
all 480 unequal-support comparisons, every support-role and singleton
disposition, every eligible cross-subject segment occurrence and its reused
semantic-review packet and verdict, and every integrity, review-capacity, or
local-prerequisite failure. For each eligible cross-subject occurrence, the
coverage manifest must bind its configuration, canonical member set, review
packet and verdict, and every member's exact support role and count. When
semantic review is unavailable, bind the occurrence to that recorded cause
instead of a verdict.

The decision report must include mandatory summary tables with explicit
denominators. At minimum, provide separate summaries by neighborhood and
condition, by exact support role, and by schedule. Where each measure applies,
show total and eligible configurations or comparisons, matched baselines that
recovered, `survived`, `did not survive`, and unavailable comparisons, eligible
configurations with omission or fragmentation, and eligible cross-subject
occurrences classified as `valid`, `invalid`, `uncertain`, or unavailable.
Fields that do not apply must be marked as such rather than omitted. Additional
aggregation by result class is allowed, but every exact configuration must
occur once in the coverage manifest and remain traceable to its immutable raw
record.

For each candidate record, the primary human semantic reviewer inspects the
mandatory summary tables, the complete aggregate report, and every exceptional
invalid, uncertain, integrity-failure, and local-prerequisite record. The
reviewer does not manually inspect all 512 configuration records or all 1,024
raw invocation outputs for that candidate. Review is complete only when the
coverage manifest validates, all required exceptions have an explicit
disposition, and the written rationale addresses every required exception,
including every neighborhood-specific failure, before recording `proceed`.
Missing coverage or an incomplete review withholds `proceed` for that candidate
record; the available review dispositions are `revise candidate` or `stop`.
That disposition cannot rewrite the recorded observations and does not make the
final candidate choice. A decision to revise after Experiment 3 or 4 must first
determine whether SSE, the segmentation candidate, or their interaction needs
to change.

If one candidate's Experiment 2 semantic-review pool exceeds 100 unique
cross-subject packets, do not sample or silently discard packets. Record a
review-capacity failure, preserve the automated characterization, and withhold
`proceed`; the available review dispositions are `revise candidate` or `stop`.

The frozen plan uses:

| Stage | Shared new SSE encodings | Exact inputs per candidate | Fresh invocations per candidate | Fresh invocations across both candidates |
|---|---:|---:|---:|---:|
| Experiment 1 plus order conformance | 36 | 2 | 4 | 8 |
| Experiment 6 | 0; reuses 36 from Experiment 1 | 4 new; reuses Experiment 1's default input | 8 new; reuses Experiment 1's default pair | 16 new; reuses both candidates' Experiment 1 pairs |
| Experiment 3 | 48 | 10 | 20 | 40 |
| Experiment 4 | 27 | 10 | 20 | 40 |
| Experiment 2 | 96 | 512 | 1,024 | 2,048 |
| **Total** | **207** | **538** | **1,076** | **2,152** |

The 538 logical input specifications are shared. Applying them independently to
both candidate identities produces 1,076 candidate-instance input executions
and the 2,152 fresh invocations above.

Experiment 6 reuses Experiment 1's 36 immutable SSE vectors, opaque IDs, and
default order for both candidates. For its combined-collection comparison, each
candidate instance reuses only its own valid, repeatable Experiment 1 default
output, and that comparison is interpretable only after the output passes
Experiment 1's recovery-and-purity rule. Experiment 6 still runs its own local
baselines and interventions for both candidates. The two documents own
different preservation verdicts; each candidate shares its own qualified output
artifact instead of rerunning it.

That reuse requires the human approval and technical freeze together to cover
Experiment 1 and Experiment 6's fixtures, both candidate identities, scoring
rules, ID mapping, orders, and exact inputs before either candidate's
Experiment 1 default run. Experiment 6's definition cannot be written or
changed after seeing either candidate's shared output.

The arrows above express artifact order, not semantic admission. Experiments 1
and 6 record qualification results, but a focal failure does not suppress
Experiments 3, 4, or 2. Experiment 2 deliberately has no automatic stage pass;
its complete characterization record—including local prerequisite failures and
missing survival verdicts—goes into the final side-by-side report.

They are not scientific shortcuts. A pass on one fixture never replaces a
baseline or control on a different fixture. Each downstream comparison must
still qualify its own exact inputs. This distinction prevents a focal
experiment from passing merely because the reference structure it was meant
to compare against disappeared.

The complete **local scientific dependency map** is below. Every predicate that
calls an input `valid` or `repeatable` also requires the shared execution
integrity checks, including actual-profile verification, to have passed.

| Owner | Exact prerequisite | Dependent comparison |
|---|---|---|
| Candidate conformance | Valid, repeatable default and alternate orders of the same Experiment 1 input | Cross-order equality; if the two repeatable outputs differ, the candidate has a candidate-integrity failure. |
| Experiment 1 | Valid, repeatable default-order input | Repeated-subject recovery verdict. |
| Experiment 6 | Experiment 1's valid, repeatable default artifact passes its recovery-and-purity rule | Imported combined-collection artifact. |
| Experiment 6 | Qualified local reference `L` | Duplicate condition, unrelated-addition condition, and the combined input's `L`-side preservation verdict. |
| Experiment 6 | Qualified local reference `R` | The combined input's `R`-side preservation verdict. |
| Experiment 6 | Both side results are available from a valid, repeatable combined input, whether they pass or fail | Complete combined-collection verdict; it passes only when both sides pass. |
| Experiment 3 | One trap's qualified baseline relationships | That trap's two one-sided-control comparisons. |
| Experiment 3 | Both one-sided controls preserve those relationships | That trap's simultaneous shared-word comparison. |
| Experiment 4 | All six anchor-only references qualify and one exact control has its expected one-hot profile | That control's three independent treatment runs have a usable baseline. |
| Experiment 4 | One treatment input is valid and repeatable, all six treatment references remain available, and its exact control retains the baseline profile | Comparison of that mixed vector's complete six-subject profile with its preserved control. |
| Experiment 4 | One eligible mixed-vector profile differs from its preserved control | Complete Experiment 4 failure; record every gained or lost relationship. |
| Experiment 4 | All nine treatment profiles are available and equal their preserved controls | Complete Experiment 4 pass. If none fails but any treatment is withheld, there is no overall verdict. |
| Experiment 2 | One valid, repeatable matched balanced configuration plus its valid, repeatable unequal configuration | The balanced-versus-unequal projected-output comparison for that exact pair. |
| Experiment 2 | One repeatable matched balanced configuration that recovered the cohort, plus its repeatable unequal configuration | A recovery-survival statement for that cohort. |
| Experiment 2 | Complete repeatable cross-subject segment pool contains at most 100 unique packets for that candidate | Cross-subject semantic review and final `proceed` eligibility. If the pool exceeds 100, automated characterization remains available but `proceed` is withheld. |

Failure of one row withholds only its dependent comparison. It does not suppress
routine execution of another row. Other rows remain scoreable when their own
integrity and local prerequisites hold. Experiment 2's other descriptive fields
remain observations even when a survival statement is unavailable.

## Result ownership

Use these result classes throughout the suite:

- **candidate-integrity failure:** one frozen candidate violates the shared
  construction or order-conformance contract; no semantic output from that
  candidate instance is trusted or scored, while the other instance continues;
- **integrity failure:** approval, encoding, blinding, output validity, or
  exact-input repeatability failed, or an invocation did not match the frozen
  execution profile; the affected input and every comparison using it receive
  no verdict;
- **semantic qualification failure:** Experiment 1 or 6 produced an eligible
  focal failure; record it without suppressing later experiment execution, and
  withhold only comparisons that require that exact qualification;
- **local prerequisite failure:** an experiment's own baseline or control did
  not qualify; only dependent comparisons receive no verdict;
- **review-capacity failure:** one candidate's complete Experiment 2
  semantic-review pool exceeds 100 unique cross-subject packets; automated
  characterization remains available, but that candidate record cannot receive
  the `proceed` review disposition;
- **focal pass or failure:** an eligible comparison answers the assumption
  owned by that experiment; and
- **characterization:** Experiment 2 reports what happened without converting
  the observations into a universal pass threshold.

Record an underlying failure once under its owner. A dependent comparison says
`no verdict because <owner>`; it does not inherit the owner's failure as if it
had tested the same claim. Independent branches remain scoreable.

## Shared execution contract

### Fixture and SSE boundary

The recorded 2026-08-31 human approval covers every complete synthetic note,
exact mask, declared atomic subject, expected relationship, scoring rule, and
experiment-specific prerequisite. It applies to exact UTF-8 bytes, not rendered
text alone.

Each SSE input is one complete note plus one fixed byte span. SSE processes the
complete note, averages the contextual token representations selected by that
span, and applies its learned output transformation. The brackets `⟦...⟧` in
the experiment documents show selected text; the brackets are not input bytes.

All experiments use this checkpoint:

```text
Sentence-T5-base SSE
SHA-256 ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d
```

Before encoding, freeze the exact note bytes and spans and an encoder manifest
containing the worker source, model and tokenizer artifacts, their hashes, the
byte-span-to-token rule, and
`selected-contextual-token-mean-linear-relu-linear-v1` as the pooling and
learned-output-transform contract. Encode each unique input once. Then preserve
the raw `f32` output bytes and record each output's element count, byte count,
and SHA-256. The expected element count is 768; a mismatch is an encoder
failure, not a candidate result.

Cosine and other representation diagnostics use only these immutable raw
outputs. Any normalization, distance function, or other candidate-side
preprocessing belongs to the frozen candidate boundary.

### Candidate identity and conformance

Freeze the candidate before encoding or inspecting any fixture vector. Its
**identity tuple** is:

```text
(candidate-source-tree hash,
 executable or container hash,
 dependency-lock or runtime hash,
 configuration-bytes hash,
 preprocessing contract and parameters hash,
 candidate-input-adapter version,
 candidate-execution-profile hash,
 candidate seed,
 fine-output selector,
 deterministic tie-rule contract)
```

Record the exact tuple fields in a canonical manifest and record its SHA-256.
Changing any field creates a different candidate whose results must be kept
separate. One suite manifest also records that candidate-manifest hash, the
encoder-manifest hash, and the approved protocol-file hashes. Tuning the
candidate creates a new suite instance; results from the previous identity do
not admit the new one through any dependency edge.

The **candidate execution profile** is one canonical compact JSON object with
sorted keys and no trailing newline. It freezes the environment in which every
candidate invocation runs:

- schema version, a stable host-instance identifier, operating system, kernel,
  architecture, CPU model, and relevant CPU features;
- accelerator model and stable device identifier, such as its runtime UUID or
  PCI address, plus the driver and runtime when used;
- executable or container identity, fixed working directory, launcher, and
  command template;
- device selection, numeric type and precision, numerical-backend and
  determinism settings, and thread/process counts;
- the complete sanitized environment-variable map exposed to the candidate;
  the candidate process receives no unrecorded inherited variables; and
- resource limits and fresh-state/isolation policy.

The command template identifies the already frozen exact input manifest through
one declared placeholder; input-specific paths and hashes remain invocation
records rather than changing the execution profile. During verification,
require the executed argument vector to equal the frozen template after that
invocation's recorded input value is substituted. Store the template in the
actual-profile schema, not the varying path. Freeze the profile bytes and
SHA-256 before encoding. Before accepting each invocation's output, capture the
actual values from that process into the same canonical schema, recompute the
hash, and require byte-for-byte equality with the frozen profile. Merely
copying the expected hash into a run record is not verification. A missing or
different actual profile is an integrity failure for that exact input. Changing
the frozen profile creates a new candidate identity and suite instance.

For this controlled suite, all candidate invocations use the same host/device,
container or executable, fixed environment, and threading configuration.

The candidate must be permutation-invariant by construction: permuting the
same `(opaque ID, vector bytes)` pairs must produce the same unordered
fine-segment collection. Initialization, batching, traversal, and tie breaking
must not depend on arrival position. The candidate specification must explain
how it achieves this, such as by canonicalizing its input before any
order-sensitive operation.

The current SNN and HDBSCAN* candidates share the versioned input adapter
`opaque-id-order-bitwise-vector-alias-v1`. It performs these operations before
either algorithm core runs:

1. validate that every opaque ID is a unique 64-character lowercase hexadecimal
   string;
2. order inputs by their decoded 32-byte opaque IDs;
3. group inputs whose complete candidate-coordinate sequences have identical
   IEEE-754 bits;
4. use the lowest opaque ID in each group as its representative; and
5. give the core only those representatives, in opaque-ID order.

Thus, an exact vector alias does not add a geometric point or change a core's
neighborhood density. After the core returns, the adapter replaces every
representative membership with the complete corresponding alias group. If a
representative is unassigned, all its aliases are unassigned. It then sorts the
expanded opaque IDs and segments canonically and applies the shared output
validity checks. The complete alias groups and representative order remain in
the run artifact.

This equality test occurs after the frozen candidate-side decoding of the raw
`f32` vector bytes and before cosine construction. Because that decoding is
deterministic and lossless, byte-identical fixture vectors have identical
candidate coordinates. Numerically close vectors are not aliases.

The candidate receives only opaque IDs and vector bytes. It receives no notes,
masks, readable fixture IDs, subject names, conditions, support roles, expected
relationships, or scoring rules. Opaque IDs identify vectors and returned
members; their encoded values are not semantic features. No adversarial
opaque-ID-renaming test is required.

Before semantic scoring, run one empirical order-conformance preflight using
Experiment 1's complete 36-vector input. Its default order is the shared HMAC
order below. The alternate order is that 36-item sequence in reverse. Freeze
both orders before encoding. Run the alternate order twice from fresh
candidate state and require both canonical outputs to equal each other and the
canonical output from Experiment 1's default order.
An invalid or non-repeatable default or alternate input is an integrity failure
and yields no conformance or Experiment 1 verdict. If both orders are valid and
repeatable but their canonical outputs differ, the candidate is ineligible;
that difference is not an Experiment 1 recovery failure.

This finite preflight checks the implementation on one frozen input. It does
not prove invariance for every possible collection, so the construction-level
requirement remains part of the candidate identity.

The selected fine output may overlap and may leave vectors unassigned; no
shared rule requires a partition, exhaustive coverage, a fixed segment count,
or one membership per vector.

The selected output fields are also versioned candidate behavior:

- `snn-segments-members-v1` selects exactly every
  `SnnSegmentation.segments[*].members` set; and
- `hdbscan-clusters-members-v1` selects exactly every
  `HdbscanResult.clusters[*].members` set.

For both candidates, the core's `noise` ordinals become the adapter's
`unassigned` opaque IDs. Neighbor evidence, density, point roles, linkage
trees, membership strengths, and outlier scores remain diagnostics; they do
not independently create fine segments.

### Predeclared implementation configurations

The HDBSCAN* suite instance uses these exact parameter bytes, fixed before any
suite fixture is encoded or any resulting vector is inspected:

```json
{"min_samples":2,"min_cluster_size":2,"selection_method":"excess_of_mass"}
```

This is `hdbscan-controlled-suite-config-v1`. A cluster size of two leaves
Experiment 2's repeated two-instance cohorts representable. Two samples make
core distance depend on the nearest other vector; one degenerates to ordinary
single linkage, while three or more would make a two-instance cohort's density
depend on another subject. Excess-of-mass is the paper-defined flat extraction
and avoids preselecting the finer but more fragmentation-prone optional leaf
policy.

The HDBSCAN* algorithm-level contracts are:

- algorithm: `hdbscan-star-exact-angular-v1`;
- input adapter: `opaque-id-order-bitwise-vector-alias-v1`;
- fine-output selector: `hdbscan-clusters-members-v1`;
- tie rule: `hdbscan-angular-ordinal-equal-tier-v1`; and
- configuration: `hdbscan-controlled-suite-config-v1`.

The equal, separate SNN suite instance uses these exact parameter bytes:

```json
{"neighbor_count":5,"minimum_shared_neighbor_count":2,"minimum_core_neighbor_count":3}
```

This is `snn-controlled-suite-config-v1`. In Experiment 1, each six-instance
subject can supply all five of a vector's neighbors. That makes five the
smallest neighborhood size that can directly expose the complete intended
Experiment 1 cohort to every member. In Experiment 2's balanced four-instance
cohorts, each vector has only three same-subject peers, so a five-neighbor list
necessarily also contains two vectors from nearby subjects. This is deliberate:
Experiment 2 characterizes whether a fixed SNN candidate preserves or crosses
those nearby boundaries; it does not qualify or tune the candidate. Within a
four-member cohort, a pair can share the other two subject members and each
member can have three same-subject links. Those facts support the thresholds
two and three. They do not imply that five is a monotonic “stronger” setting.

These are two distinct candidate definitions, not a grid and not two algorithms
within one suite instance. The controlled run evaluates one separate suite
instance for each. Experiment 1 may qualify or reject either already
predeclared candidate; its output must never choose or tune either
configuration. A changed tuple or selection method creates a new candidate and
a new suite instance.

Declaring either configuration does not by itself complete that candidate's
identity freeze. Each instance still requires its source tree,
executable/runtime, execution profile, explicit no-random-seed convention,
approved Experiment 1/6 protocols, and blinding artifacts under the lifecycle
below.

### Opaque-ID blinding

By default, use the experiment document's filename without `.md` as its UTF-8
namespace. After fixture approval and candidate freeze, draw one 32-byte seed
from the operating-system CSPRNG. For every readable fixture ID, derive:

```text
opaque_id = HMAC-SHA-256(
  seed,
  "fine-segmentation-id-v1\0" || namespace || "\0" || fixture_id
)

order_key = HMAC-SHA-256(
  seed,
  "fine-segmentation-order-v1\0" || namespace || "\0" || fixture_id
)
```

Represent an opaque ID as the 32 digest bytes encoded as 64 lowercase
hexadecimal characters. The default global input order is ascending
`order_key`, breaking a collision by opaque-ID bytes; a run containing a subset
filters that global order. An experiment may declare an order intervention,
but every exact order must be frozen before encoding.

Before encoding, record this commitment:

```text
SHA-256(
  "fine-segmentation-blinding-commit-v1\0" || namespace || "\0" || seed
)
```

Because the approved readable IDs and derivation are already frozen, this
commits the complete mapping and default order. Keep the seed, mapping, and
order in a private scorer artifact. Reveal them only after every candidate
output is immutable, then verify the commitment and every derivation before
scoring.

Experiment 6 declares one transported-artifact exception. Its 36 base vectors
retain Experiment 1's opaque IDs and order keys so Experiment 1's exact default
input and output can be reused. Only Experiment 6's six new duplicate IDs use
the `06-irrelevant-change-stability` namespace and a new committed seed. The
duplicate input sorts the union of the existing base order keys and the six new
order keys by the same rule above. Both protocols and the duplicate commitment
must be frozen before Experiment 1's default output is generated. Revealing
Experiment 1's mapping to score its recovery result does not authorize changing
either already frozen candidate or the Experiment 6 inputs.

### Output validity and canonicalization

The selected fine output contains an unordered collection of unordered
member-ID sets named `segments` and an unordered set named `unassigned`.
`unassigned` must contain exactly the input IDs that occur in no selected
segment. Validate each raw output before projection, identity reveal, or
scoring:

- every segment must be nonempty;
- every member must be a 64-character lowercase hexadecimal opaque ID present
  in that exact input;
- a raw segment must not repeat a member ID; and
- two segments must not have the same member set;
- `unassigned` must not repeat an ID or contain an ID present in any segment;
  and
- the union of every segment and `unassigned` must equal the complete input-ID
  set.

A duplicate member set is invalid and must never be silently deduplicated.
Singletons, overlaps, and an empty outer collection remain valid under the
shared contract; an experiment-specific rubric may still reject them.

Canonicalize a valid output as follows:

1. decode and sort member IDs by their 32-byte values;
2. encode each segment as a compact JSON array of its lowercase-hex strings;
3. use those encodings as sort keys and sort the segment arrays
   lexicographically by the keys' UTF-8 bytes;
4. decode and sort `unassigned` IDs by their 32-byte values;
5. encode the object
   `{"segments":[...],"unassigned":[...]}` as compact UTF-8 JSON with the
   keys in that literal order and no trailing newline—the `segments` value is
   an array of segment arrays, not an array of quoted JSON strings; and
6. compute SHA-256 over those exact bytes.

Canonicalization removes only member and segment ordering. Preserve the raw
output, canonical JSON bytes, and hash.

The in-memory candidate artifact records those exact canonical JSON bytes and
their SHA-256 separately from the hash of the complete diagnostic run. It also
records the exact compact configuration JSON and its SHA-256 and binds the
exact shared adapter, normalization/cosine preprocessing, and chosen
algorithm-core source files compiled into the build. The suite manifest still
binds the complete candidate source tree, executable, dependency/runtime, and
execution-profile identities from the candidate identity tuple above.

### Lifecycle

For each candidate instance and every planned experiment input whose integrity
prerequisites permit execution:

1. verify the recorded 2026-08-31 human approval of the fixture, rubric, and
   prerequisite graph;
2. freeze the candidate identity tuple and candidate execution profile, and
   document construction-level permutation invariance;
3. derive the opaque-ID mapping and order and record their private artifact and
   public commitment;
4. freeze the SSE artifacts, exact input bytes, spans, and all exact run-input
   specifications;
5. encode each unique SSE input once, then record output dimensions and hashes
   and freeze the vector bytes;
6. run every exact candidate input twice from fresh candidate state with the
   same identity tuple, frozen execution profile, opaque IDs, vector bytes, and
   order;
7. capture and verify each invocation's actual execution profile, preserve both
   raw outputs, validate them independently, canonicalize valid outputs, and
   require their canonical bytes—not only hashes—to match;
8. after all outputs are immutable, reveal and verify the blinding artifact;
   and
9. restore readable identities and apply the approved scoring rules.

No invocation may train, prime, or provide mutable cached state to another.
Two matching repetitions establish repeatability only for that exact input.
Complete the candidate order-conformance preflight before giving Experiment 1
a semantic recovery verdict. Then execute the complete local schedule for that
candidate without using semantic outcomes to suppress later invocations. The
shared Experiment 1/6 freeze described above is completed before this lifecycle
begins; interpretation dependencies do not permit post-output protocol design.

### Prerequisite scope

Missing approval, boundary drift, a candidate-integrity failure, an encoder
failure, a missing or mismatched actual execution profile, or failed blinding
verification supplies no semantic verdict. An invalid raw output is an
output-contract failure for that exact input. Two valid but unequal canonical
outputs are a repeatability failure for that exact input. Any of these blocks
that input and every comparison that depends on it from semantic scoring.

An experiment-specific baseline or other semantic prerequisite blocks only the
conditions that explicitly depend on it. Independent conditions may retain
their own scoped results. A prerequisite failure is not evidence that the
dependent hypothesis is false; report it separately from a scored failure. It
does not by itself suppress a planned invocation.

The same rule applies across documents: a successful result transports only
when a later comparison literally reuses the same immutable candidate input
and output artifact under the same identity tuple and verified
execution-profile hash. Experiment 6's
combined-collection condition deliberately reuses Experiment 1's default
artifact; no other current comparison transports an earlier output.
Similar-looking subjects or a previous recovery pass are not substitutes for
a later fixture's local baseline.

These are controlled development experiments, not corpus-wide validation. If
their results are used to modify a candidate, later validation requires newly
frozen holdout fixtures.
