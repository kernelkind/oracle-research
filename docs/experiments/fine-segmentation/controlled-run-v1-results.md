# Controlled fine-segmentation run v1

Status: **technical execution and automated scoring completed on 2026-09-01;
no final candidate disposition was recorded**.

This is the decision record for the two configurations declared in the
[qualification suite](README.md). It reports observations separately from
interpretation. It does not select a candidate.

## Frozen run

- Protocol source: commit `00277fe5534bef106cda3f00e5e5ad2ebfc1915a`
- Suite implementation: commit
  `6b788656eeb46c03c19ff0540d53092e5a336f97`
- Protocol SHA-256:
  `166b87490ccdb25042772d3746407afca9207bc8285a710d30749128b8f65dcd`
- Technical-freeze SHA-256:
  `a25a5fe5db30eecd8a07153c5e56099d3dcef1592e3291350ea6b86fdfc97d84`
- Normalized-vector SHA-256:
  `da93dc55e35551e3a6bef37f63421a768013516f73730915955ba055c8e022ec`
- Candidate-run record-set SHA-256:
  `a1e2e76700558f7863eb8d33d78ac33235de126b157f853d0851e4735b490baf`
- Scoring-manifest SHA-256:
  `026a2f00f5490f779c46b94d4f694159e648d2b374bf123eef3bd7a314aba07b`

The shared encoder produced 207 vectors of 768 dimensions. The suite then ran
538 exact inputs twice for each candidate: 2,152 fresh candidate invocations.
Every invocation passed its integrity checks, and all 1,076 repeated output
pairs were byte-for-byte identical after canonicalization.

The complete local artifact is under
`target/fine-segmentation-controlled-suite-v1/`. It is approximately 539 MiB
and is not committed.

## Automated observations

| Check | HDBSCAN* | SNN |
|---|---|---|
| Candidate conformance | Pass | Pass |
| Experiment 1: six repeated-subject cohorts | Five recovered; `BIKE-TUBE` split | All six recovered |
| Experiment 6: irrelevant changes | No verdict because the transported Experiment 1 baseline did not qualify | Duplicate, unrelated-addition, and combined-collection checks passed |
| Experiment 3: three lexical traps | All three passed | No verdict for all three because their local baseline relationships did not qualify |
| Experiment 4: nine unmasked-context treatments | Six passed; three coffee treatments had no verdict after the coffee reference relationship stopped qualifying | No verdict for all nine because the shared baseline did not qualify |
| Experiment 2: eligible configurations | 512 of 512 | 512 of 512 |
| Experiment 2: projected comparisons represented | 480 of 480 | 480 of 480 |
| Experiment 2: unique cross-subject review packets | 177 | 280 |
| Experiment 2: review outcome | Capacity failure: over the frozen cap of 100 | Capacity failure: over the frozen cap of 100 |

The SNN baseline failure in Experiment 3 was concrete: it mixed the river-bank,
sports-coach, and container-pitcher cohorts. Its Experiment 4 baseline likewise
mixed several unrelated reference areas, so the context intervention could not
be isolated. These are prerequisite failures, not scored failures of the
interventions themselves.

In HDBSCAN*'s three Experiment 4 no-verdicts, the coffee anchors still grouped
together, but the masked coffee control moved into a separate segment with the
new context-bearing input. The required three-member coffee relationship was
therefore no longer intact. This happened for all three unrelated context
subjects.

Experiment 2 produced these additional automated measurements:

| Measurement | HDBSCAN* | SNN |
|---|---:|---:|
| Unequal-support comparisons whose matched balanced cohort existed | 682 / 1,056 | 275 / 1,056 |
| Existing matched cohorts that survived the support change | 440 / 682 | 147 / 275 |
| Configurations with fragmentation | 316 / 512 | 72 / 512 |
| Configurations with at least one omitted vector | 254 / 512 | 339 / 512 |
| Cross-subject occurrences lacking a semantic verdict | 191 | 295 |

These numbers are descriptive. In particular, a cross-subject segment is not
automatically wrong: it may represent a valid alternative fine subject. The
approved protocol required human semantic review to distinguish valid from
invalid cross-subject membership. The fragmentation, omission, and survival
counts can overlap and must not be added into an overall defect score.

## Protocol outcome

Both candidates exceeded the predeclared 100-packet review cap. The protocol
therefore forbids sampling a smaller subset, withholds `proceed`, and permits
only `revise candidate` or `stop` for each candidate. This is the outcome even
though the automated evidence remains useful.

Neither candidate received a final recorded disposition under that protocol.
The automated measurements therefore do not establish a selected candidate.

## Separate exploratory HDBSCAN* review v2

The initial post-hoc v1 session used each retained exact vector set as one
human-review unit, requiring 177 judgments for 191 occurrences. That session
remains unchanged. A later methodological audit found that this was unsuitable
for the human task: the 177 exact packets map to nine distinct sorted sets of
approved synthetic subjects.

The separately versioned v2 characterization:

- makes each approved-subject set one review packet;
- presents the union of that group's opaque vectors, deduplicated by
  opaque-vector identity, under deterministic neutral instance IDs with
  complete mask fragments;
- records one `valid`, `invalid`, or `uncertain` judgment and no subject label;
- deterministically replays that judgment to every exact packet with the same
  subject set and then to every formal occurrence, so nine judgments cover 177
  exact packets and 191 occurrences;
- preserves explicit exact-packet and occurrence mappings in the reviewed
  artifact; and
- leaves the frozen HDBSCAN* candidate and evidence, original v1 session, SNN
  record, capacity failure, unavailable `proceed` disposition, and final user
  selection unchanged.

This is an exploratory methodological correction, not a continuation or
rewrite of the frozen qualification protocol. The review is pending, and its
judgments must be reported only as post-hoc v2 evidence.

## Interpretation

HDBSCAN* showed the stronger evidence of semantic separation: it passed every
lexical trap, established a usable unmasked-context baseline, and yielded fewer
cross-subject review packets. Its current configuration is still not ready to
advance: it missed one basic cohort, fragmented many configurations, and
exceeded the review cap.

SNN recovered the six easy repeated cohorts and was stable under the three
irrelevant-change checks. In the more heterogeneous Experiment 3 and 4
collections, however, it merged unrelated reference subjects so broadly that
none of those intervention questions could be answered. It also produced more
cross-subject review packets and more omissions than HDBSCAN*.

The recorded interpretation favored revising the HDBSCAN* candidate over
continuing this frozen SNN configuration. No candidate was selected by these
automated measurements.
