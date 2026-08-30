# Fine-segmentation qualification and characterization suite

Status: **draft; do not encode or run yet**.

This suite evaluates one frozen fine-segmentation candidate across the six
concerns that originated in [MY-NOTES.md](../../../notes/MY-NOTES.md). The
protocols here are their operational definitions. In particular, Experiment 2
characterizes density and sparsity; it does not impose a categorical
rare-subject absorption rule. Each experiment uses purpose-built synthetic
notes and manually specified masks. The old 53-vector collection is not reused
merely because it exists.

The suite is a dependency graph, not six independent pass/fail checklists.
Every check has one owner:

| Owner | What it establishes |
|---|---|
| Candidate conformance | The frozen candidate obeys its construction contract and does not change when one frozen input is permuted. |
| [Experiment 1](01-repeated-subject-recovery.md) | Basic repeated-subject recovery. |
| [Experiment 6](06-irrelevant-change-stability.md) | Stability under exact duplicates, an unrelated added subject, and combining independently recovered collections spanning separated semantic areas. |
| [Experiment 3](03-lexical-coincidence.md) | Shared words do not replace semantic relationships. |
| [Experiment 4](04-unmasked-context.md) | Unmasked material does not determine the fine-segment membership of a fixed mask. |
| [Experiment 2](02-nearby-subject-resolution.md) | Characterization of nearby-subject resolution under balanced, unequal, and sparse support, plus semantic-review capacity. |
| Final human review | Whether the complete frozen evidence is sufficient to use this candidate in the next proof of concept. |

[Experiment 5](05-density-and-sparsity.md) is retired because Experiment 2
owns density and sparsity. Experiment 2 does not also own unrelated-area
addition; Experiment 6 owns that concern.

## Dependency graph

Run the program in this fail-fast order:

```text
frozen candidate, representation boundary, and approved fixture
                         |
                         v
              candidate conformance
                         |
                         v
       Experiment 1: basic recovery qualification
                         |
                         v
       Experiment 6: stability qualification
                         |
             +-----------+
             |           |
             v           v
       Experiment 3  Experiment 4
       lexical test  context test
             |           |
             +-----+-----+
                   |
                   v
       Experiment 2: characterization
                   |
                   v
       frozen human review of the complete record
```

Experiments 3 and 4 may run in parallel after stability qualification.
Experiment 2 is last because it is much more expensive and does not produce
one binary confirmation verdict. Requiring the cheaper targeted tests first is
a budget policy, not a claim that their results scientifically validate
Experiment 2's fixture.

The graph ends in a human decision, not an automatic Experiment 2 pass.
Nearby-subject boundaries are deliberately not reduced to one universal
threshold. Before encoding, freeze the reviewer, the review-order derivation
procedure and seed, a finite semantic-review packet budget, the required
evidence fields, the choices `proceed`, `revise candidate`, and `stop`, and the
requirement for a written rationale. Derive the concrete review order only
after the evidence pool is immutable.
The review must inspect the balanced organization, every support-stress
change, every invalid or uncertain cross-subject segment, every rare or
singleton disposition, and every Experiment 2 output-contract, repeatability,
or local-prerequisite failure. Its rationale must explicitly address every
invalid false absorption and every neighborhood-specific failure before
choosing `proceed`. The decision cannot rewrite the recorded observations.

If Experiment 2's complete semantic-review pool exceeds the frozen packet
budget, do not sample or silently discard packets. Record a review-capacity
failure, preserve the automated characterization, and withhold `proceed`; the
available final choices are `revise candidate` or `stop`.

If every stage is admitted, the frozen plan uses:

| Stage | New SSE encodings | Exact candidate inputs | Fresh invocations |
|---|---:|---:|---:|
| Experiment 1 plus order conformance | 36 | 2 | 4 |
| Experiment 6 | 0; reuses 36 from Experiment 1 | 4 new; reuses Experiment 1's default input | 8 new; reuses Experiment 1's default pair |
| Experiment 3 | 48 | 10 | 20 |
| Experiment 4 | 27 | 2 | 4 |
| Experiment 2 | 96 | 512 | 1,024 |
| **Total** | **207** | **530** | **1,060** |

Experiment 6 reuses Experiment 1's 36 immutable SSE vectors, opaque IDs,
default order, and valid, repeatable default output as its combined-collection
artifact only after that output passes Experiment 1's recovery-and-purity
rule. Experiment 6 still runs its own local baselines and interventions. The
two documents own different preservation verdicts; they share one qualified
artifact instead of rerunning it.

That reuse requires Experiment 1 and Experiment 6 to be approved and frozen
together through their fixture, candidate identity, scoring rules, ID mapping,
orders, and exact inputs before Experiment 1's default run. The spending graph
may later skip Experiment 6 execution, but its definition cannot be written or
changed after seeing the shared output.

The fail-fast order therefore decides whether to spend the final 1,024
invocations; it does not remove any local scientific control.

The arrows above are **default spending edges**. Experiments 1 and 6 require a
qualification pass before the targeted tests run. Experiment 2 is scheduled
only if both targeted tests produce focal passes. At those pre-Experiment-2
edges, a stage-level failure or missing overall verdict stops default
downstream spending. This scheduling effect does not reclassify a focal
failure as a qualification failure. A skipped experiment may still be run for
diagnosis, but it must be labeled diagnostic and cannot reopen the stopped
edge. Once Experiment 2 is admitted and run, its characterization record—including
local prerequisite failures and missing survival verdicts—goes to final
human review; Experiment 2 deliberately has no automatic stage pass.

They are not scientific shortcuts. A pass on one fixture never replaces a
baseline or control on a different fixture. Each downstream comparison must
still qualify its own exact inputs. This distinction prevents a focal
experiment from passing merely because the reference structure it was meant
to compare against disappeared.

The complete **local scientific dependency map** is:

| Owner | Exact prerequisite | Dependent comparison |
|---|---|---|
| Candidate conformance | Valid, repeatable default and alternate orders of the same Experiment 1 input | Cross-order equality; if the two repeatable outputs differ, the candidate is ineligible. |
| Experiment 1 | Valid, repeatable default-order input | Repeated-subject recovery verdict. |
| Experiment 6 | Experiment 1's valid, repeatable default artifact passes its recovery-and-purity rule | Imported combined-collection artifact. |
| Experiment 6 | Qualified local reference `L` | Duplicate condition, unrelated-addition condition, and the combined input's `L`-side preservation verdict. |
| Experiment 6 | Qualified local reference `R` | The combined input's `R`-side preservation verdict. |
| Experiment 6 | Both side results are available from a valid, repeatable combined input, whether they pass or fail | Complete combined-collection verdict; it passes only when both sides pass. |
| Experiment 3 | One trap's qualified baseline relationships | That trap's two one-sided-control comparisons. |
| Experiment 3 | Both one-sided controls preserve those relationships | That trap's simultaneous shared-word comparison. |
| Experiment 4 | One subject's qualified anchor-only reference | Availability of that subject as a joint local prerequisite. |
| Experiment 4 | A mixed target's masked subject qualifies in the baseline and remains available in the joint output | Comparison with the exact no-context control for the masked target subject. |
| Experiment 4 | One foreign subject qualifies in the baseline; either control or mixed target has a direct relationship to that foreign subject | Direct foreign-subject comparison, even if the foreign pure joint reference disconnected. |
| Experiment 4 | The foreign subject qualifies in the baseline, neither vector has a direct relationship to it, and its joint reference remains available | Shared-absence pass for that foreign subject. |
| Experiment 4 | All six subject comparisons for one mixed target are available | That mixed target's complete context-stability result. |
| Experiment 4 | Any available mixed-target-to-subject comparison differs | Complete Experiment 4 failure, even if another comparison is withheld. |
| Experiment 4 | All 54 mixed-target-to-subject comparisons are available and pass | Complete Experiment 4 pass. If none fails but any is withheld, there is no overall verdict. |
| Experiment 2 | One valid, repeatable matched balanced configuration plus its valid, repeatable unequal configuration | The balanced-versus-unequal projected-output comparison for that exact pair. |
| Experiment 2 | One repeatable matched balanced configuration that recovered the cohort, plus its repeatable unequal configuration | A recovery-survival statement for that cohort. |
| Experiment 2 | Complete repeatable cross-subject segment pool does not exceed the frozen packet budget | Cross-subject semantic review and final `proceed` eligibility. If the pool exceeds the budget, automated characterization remains available but `proceed` is withheld. |

Failure of one row withholds only its dependent comparison. Other rows remain
scoreable unless the default spending graph stops their execution before they
run. Experiment 2's other descriptive fields remain observations even when a
survival statement is unavailable.

## Result ownership

Use these result classes throughout the suite:

- **candidate-ineligible:** the frozen candidate violates the shared
  construction or order-conformance contract; no semantic experiment is
  scored;
- **integrity failure:** approval, encoding, blinding, output validity, or
  exact-input repeatability failed; the affected input and every comparison
  using it receive no verdict;
- **program-qualification failure:** Experiment 1 or 6 produced an eligible
  focal failure; later experiments are skipped by default;
- **local prerequisite failure:** an experiment's own baseline or control did
  not qualify; only dependent comparisons receive no verdict;
- **review-capacity failure:** Experiment 2's complete semantic-review pool
  exceeds its frozen packet budget; automated characterization remains
  available, but the final review cannot choose `proceed`;
- **focal pass or failure:** an eligible comparison answers the assumption
  owned by that experiment; and
- **characterization:** Experiment 2 reports what happened without converting
  the observations into a universal pass threshold.

Record an underlying failure once under its owner. A dependent comparison says
`no verdict because <owner>`; it does not inherit the owner's failure as if it
had tested the same claim. Independent branches remain scoreable.

## Shared execution contract

### Fixture and SSE boundary

Before any experiment runs, a human must approve every complete synthetic
note, exact mask, declared atomic subject, expected relationship, scoring rule,
and experiment-specific prerequisite. Approval applies to exact UTF-8 bytes,
not rendered text alone.

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

The candidate must be permutation-invariant by construction: permuting the
same `(opaque ID, vector bytes)` pairs must produce the same unordered
fine-segment collection. Initialization, batching, traversal, and tie breaking
must not depend on arrival position. The candidate specification must explain
how it achieves this, such as by canonicalizing its input before any
order-sensitive operation.

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
Experiment 1's mapping to score its fail-fast gate does not authorize changing
the already frozen candidate or Experiment 6 inputs.

### Output validity and canonicalization

The selected fine output is an unordered collection of unordered member-ID
sets. Validate each raw output before projection, identity reveal, or scoring:

- every segment must be nonempty;
- every member must be a 64-character lowercase hexadecimal opaque ID present
  in that exact input;
- a raw segment must not repeat a member ID; and
- two segments must not have the same member set.

A duplicate member set is invalid and must never be silently deduplicated.
Singletons, overlaps, and an empty outer collection remain valid under the
shared contract; an experiment-specific rubric may still reject them.

Canonicalize a valid output as follows:

1. decode and sort member IDs by their 32-byte values;
2. encode each segment as a compact JSON array of its lowercase-hex strings;
3. use those encodings as sort keys and sort the segment arrays
   lexicographically by the keys' UTF-8 bytes;
4. encode the resulting array of segment arrays—not an array of quoted JSON
   strings—as compact UTF-8 JSON with no trailing newline;
   and
5. compute SHA-256 over those exact bytes.

Canonicalization removes only member and segment ordering. Preserve the raw
output, canonical JSON bytes, and hash.

### Lifecycle

For each experiment admitted by the dependency graph:

1. obtain human approval of the fixture, rubric, and prerequisite graph;
2. freeze the candidate identity tuple and document its construction-level
   permutation invariance;
3. derive the opaque-ID mapping and order and record their private artifact and
   public commitment;
4. freeze the SSE artifacts, exact input bytes, spans, and all exact run-input
   specifications;
5. encode each unique SSE input once, then record output dimensions and hashes
   and freeze the vector bytes;
6. run every exact candidate input twice from fresh candidate state with the
   same identity tuple, opaque IDs, vector bytes, and order;
7. preserve both raw outputs, validate them independently, canonicalize valid
   outputs, and require their canonical bytes—not only hashes—to match;
8. after all outputs are immutable, reveal and verify the blinding artifact;
   and
9. restore readable identities and apply the approved scoring rules.

No invocation may train, prime, or provide mutable cached state to another.
Two matching repetitions establish repeatability only for that exact input.
Complete the candidate order-conformance preflight before giving Experiment 1
a semantic recovery verdict. Then apply the default spending graph above.
The shared Experiment 1/6 freeze described above is completed before this
lifecycle begins; admission controls execution, not post-output protocol
design.

### Prerequisite scope

Missing approval, boundary drift, candidate ineligibility, an encoder failure,
or failed blinding verification supplies no semantic verdict. An invalid raw
output is an output-contract failure for that exact input. Two valid but
unequal canonical outputs are a repeatability failure for that exact input.
Either blocks that input and every comparison that depends on it from semantic
scoring.

An experiment-specific baseline or other semantic prerequisite blocks only the
conditions that explicitly depend on it. Independent conditions may retain
their own scoped results. A prerequisite failure is not evidence that the
dependent hypothesis is false; report it separately from a scored failure.

The same rule applies across documents: a successful result transports only
when a later comparison literally reuses the same immutable candidate input
and output artifact under the same identity tuple. Experiment 6's
combined-collection condition deliberately reuses Experiment 1's default
artifact; no other current comparison transports an earlier output.
Similar-looking subjects or a previous recovery pass are not substitutes for
a later fixture's local baseline.

These are controlled development experiments, not corpus-wide validation. If
their results are used to modify a candidate, later validation requires newly
frozen holdout fixtures.
