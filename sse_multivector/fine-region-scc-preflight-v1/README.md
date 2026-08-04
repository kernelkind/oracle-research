# SCC hierarchy preflight

## Question

Does the Sub-Cluster Component algorithm (SCC) turn the 22 accepted fine
segments into a more useful broad-to-narrow structure than the existing exact
average-linkage tree?

This is a preflight on the prior 50-note experiment, not a claim about the
future 500-note corpus.

## Frozen inputs

- The exact 22 accepted fine segments from
  `fine-region-hierarchy-result-v2/analysis.json`.
- The same normalized SSE vectors used by that experiment.
- Each fine segment has one vote in higher-level similarity, regardless of how
  many vectors it contains.
- Labels and note text did not influence SCC.
- The three threshold schedules were fixed before inspecting their semantic
  results.
- Semantic regression decisions come from
  `fine-region-hierarchy-title-candidates-v1/review-decisions.json` (SHA-256
  `28fe9c3ebed018e5fea9a41b081253b965a946f8c70fab9c9464cbc04090f405`).

The machine-readable result is [`analysis.json`](analysis.json). It binds the
input and implementation hashes and records every merging round, parent,
child, and admitted nearest-neighbor edge. Thresholds that produced no merge
remain in the frozen schedule but are not emitted as rounds.

## Schedules

`G200` is the published SCC cosine schedule: 200 geometrically spaced minimum
cosines from `1.0` through `0.001`.

`D2` uses the doubling form shown in the SCC theorem, applied to cosine
distance. It starts at `0.001`, doubles through `0.512`, and ends at `1.0`.
This choice does not claim the theorem's guarantees for our fine-segment
geometry.

`D√2` inserts one geometric midpoint between every `D2` threshold. It tests
whether the result is sensitive to one additional threshold per doubling
interval.

The SCC paper defines the algorithm and its doubling schedule. The authors'
released cosine example confirms that their empirical implementation uses
descending geometric cosine thresholds:

- [SCC paper](https://storage.googleapis.com/gweb-research2023-media/pubtools/6204.pdf)
- [Authors' cosine implementation](https://github.com/nmonath/scc/blob/main/examples/demo.py)

## Mechanical results

| Schedule | Thresholds | Parents | Binary parents | Largest child count | SCC parents also present in average linkage |
| --- | ---: | ---: | ---: | ---: | ---: |
| G200 | 200 | 21 | 21 | 2 | 21/21 |
| D2 | 11 | 7 | 2 | 6 | 7/7 |
| D√2 | 21 | 10 | 3 | 5 | 9/10 |

Facts:

- `G200` reproduced all 21 average-linkage parent leaf sets. It is the same
  binary tree on this pilot, with a different construction procedure.
- Every `D2` parent had exactly the same descendant fine segments as an
  existing average-linkage parent.
- Nine of ten `D√2` parents also matched existing average-linkage parents.
  `D√2` produced one new grouping containing `F000014`, `F000015`, `F000017`,
  `F000018`, `F000019`, and `F000020`.
- Both coarse schedules kept every displayed parent at six or fewer immediate
  children.
- `D2` made only the two strongest two-segment parents before its final
  zero-cosine threshold. Its four broad branches were all created after that
  final relaxation.
- The all-segment root is treated as a non-semantic container. It is not a
  subject that requires a shared label.

The preserved nearest-neighbor edges show how weak parents formed. For
example, the Nature and Plant Life segment selected the existing coffee/food
group as its nearest remaining group at cosine `0.202`; the coffee/food group
did not select it back. Under `D√2`, both Book recommendations and the new
authenticity/realization group independently selected Digital Privacy and
Surveillance as their nearest remaining group, at cosines `0.110` and `0.106`.
Neither choice was reciprocal. Once the threshold admitted those values,
SCC's connected-component rule merged the complete chain. This is expected
SCC behavior, not an implementation error.

## Reusing the prior semantic review

When an SCC parent has an exact average-linkage leaf-set match, the prior review
applies to the same underlying fine segments. This is stronger than comparing
generated titles, but the old decisions still combined title and membership
review; they are regression evidence, not perfect ground truth. The one new
`D√2` parent is inspected separately below.

### D2

The semantic root is excluded below.

| SCC parent | Same leaf set as | Prior decision | Prior reviewed subject or reason |
| --- | --- | --- | --- |
| S000000 | H000000 | Pass | Coffee Culture and Enjoyment |
| S000001 | H000001 | Pass | Integrity Over Approval |
| S000002 | H000015 | Reject | General solar systems and jobsite tasks do not necessarily concern Bitcoin-mining infrastructure. |
| S000003 | H000017 | Reject | The proposed parent concatenated food and beverages with general nature and plant life. |
| S000004 | H000013 | Pass | Digital Sovereignty and Freedom from Centralized Control |
| S000005 | H000016 | Reject | The conformity branch fit, but book recommendations and gradual realization did not. |

Result: three previously accepted and three previously rejected non-root
parents.

### D√2

The semantic root is excluded below.

| SCC parent | Same leaf set as | Prior decision | Prior reviewed subject or reason |
| --- | --- | --- | --- |
| S000000 | H000000 | Pass | Coffee Culture and Enjoyment |
| S000001 | H000001 | Pass | Integrity Over Approval |
| S000002 | H000011 | Reject | DIY Energy and Equipment Setup was a vague umbrella over mining, solar systems, and jobsite tasks. |
| S000003 | H000009 | Reject | General food preparation and eating was not predicted by a coffee-specific parent. |
| S000004 | H000012 | Pass | Digital Sovereignty and Freedom-Preserving Technology |
| S000005 | New | Reject | Most members concern independent thought, authenticity, or integrity, but `F000015` also contains a takeaway about a UAP book causing puzzle pieces to shift into place. That is not a narrower refinement of such a parent. |
| S000006 | H000015 | Reject | General solar systems and jobsite tasks do not necessarily concern Bitcoin-mining infrastructure. |
| S000007 | H000017 | Reject | The proposed parent concatenated food and beverages with general nature and plant life. |
| S000008 | H000018 | Reject | The parent joined digital sovereignty, authenticity, books, and realization under an abstract freedom theme. |

Result: three previously accepted, five previously rejected, and one newly
inspected but rejected non-root parent.

## Interpretation

SCC solves one real structural problem: a coarse schedule can replace a long
binary chain with a small number of multi-child decisions. On this pilot, its
largest decision had six children.

It did not solve the important semantic problem. The same bad parent contents
from average linkage survived. `D√2` created one new parent, but it still
contained an unrelated UAP-reading realization through `F000015`. More
thresholds did not help overall: `D√2` exposed more rejected levels than `D2`
and joined the useful digital-sovereignty branch to rejected
authenticity/books content before the root.

The honest conclusion is:

> SCC is a plausible, inexpensive structural baseline, but this pilot gives no
> evidence that it improves semantic parent-child correctness over average
> linkage.

For the later scaled algorithm comparison, `D2` is the only SCC variant worth
retaining. `G200` duplicates the average-linkage control, and `D√2` was both
more complex and worse under the existing review evidence. SCC should not be
selected as the hierarchy algorithm without beating alternatives on the
larger corpus.

## Reproduction

From the repository root:

```sh
./sse_multivector/run-fine-region-scc-preflight.sh
```

The command extracts the immutable baseline into a temporary directory,
verifies its hash, recomputes all three SCC variants, and refuses the replay if
it differs from `analysis.json`.
