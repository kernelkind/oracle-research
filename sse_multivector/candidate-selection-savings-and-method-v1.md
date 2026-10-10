# Candidate selection: savings and how the method works

**Result:** the strongest complete historical replay retained 2,049 comparisons
instead of 2,682, while reproducing all 181 construction steps. Its projected
known total API-equivalent cost fell from **$9.1301216 to $7.5400580: 17.42% less**.

**Status:** experimental offline research, not an adopted construction policy.
The fifty-note source uses deprecated ASv6.48 subjects and derived data. It is
historical evidence, not validation of the approved ASv6.100 pipeline. No new
teacher/provider calls were made. Production selection and prompts are unchanged.

## What the selection code does

When adding a local node, the constructor must choose which existing canonical
nodes to compare it against. Those local–canonical pairs go to the comparison
teacher, which judges equivalence, containment, neither or uncertainty.

The existing selection alternates heading-only SSE similarity and lexical text
matching to nominate up to sixteen canonical nodes. The new method **reranks
that same pool and selects up to twelve**, retaining the mapped canonical parent
first when present. The mapped parent is the canonical node corresponding to
the local node's original immediate parent. It counts toward the twelve.
Eligibility and same-note rules remain unchanged.

The score selects comparisons; it does not establish relationships. The teacher
and the existing placement, contradiction and implication checks still determine
whether anything enters the graph. Required implication-verification comparisons
can increase the total beyond the initial shortlist.

## How the new score works

Each local and canonical node has a heading and an independently established
explicit meaning. Canonical meanings stay fixed. For each unique heading/meaning
pair, use four SSE representations:

| Representation | Text encoded or span pooled |
|---|---|
| Existing subject vector | Heading alone |
| Auxiliary meaning vector | Explicit meaning alone |
| Auxiliary contextual heading vector | Heading span in `heading + newline + meaning` |
| Auxiliary contextual meaning vector | Meaning span in that same joined text |

The three auxiliary representations are not MP masks or mask vectors. Two new
text encodings produce their three pooled vectors. They are reusable; growing
canonical branches do not need to be encoded for each comparison.

For each possible local–canonical pair, calculate semantic similarities, lexical
matches and whether the headings are identical. Retain the existing SSE match
against the local heading and its original local ancestor headings. Also project
each contextual meaning vector to sixteen coordinates, then supply the local
coordinates, canonical coordinates, their differences and their products.
This lets the score distinguish pairs that have similar overall cosine scores.

A small ridge logistic regression learns how to combine those inputs. Saved
containment/equivalence answers are positive training examples; saved `neither`
answers are negative examples; uncertain answers are excluded. Its output is a
ranking score for finding a relationship, not a containment direction or semantic
proof. The winning variant, `no-graph-12`, uses 72 input features.

It excludes five canonical graph-derived features: ancestor count, descendant
count, supporting-entry count, maximum heading similarity across descendants,
and maximum meaning similarity across descendants. Local ancestor-heading
matching remains. Full graph evidence remains available to the teacher and guards.
Removing these features and retraining produced the best complete replay; this
does not establish that graph information is generally harmful.

For example, two canonical nodes called **Meals** have identical standalone
heading vectors, but one means eating occasions and the other means meal food.
Meaning representations let the selection code distinguish them. The teacher
must still judge each nominated relationship.

## What was preserved

Strict replay keeps only answers the new selection actually requested or
verified. It then runs the original placement and graph checks in construction
order, stopping if an outcome changes or a required saved answer is unavailable.
It does not borrow omitted historical negatives to make later decisions pass.

The winning replay matches all **181 entries: 146 additions, 16 equivalences and
19 holds**. Meanings, supports and parent relationships are unchanged. Therefore
the same user-reviewed fifty-note menu remains available: 76 nodes, six roots,
at most six choices per group, all notes reachable, and every displayed edge
strictly narrowing its distinct-note set.

Retaining contradiction evidence matters. A different learned variant omitted
an earlier **Eating practices / Gamey meat = neither** answer. Later **Meat eating**
created a chain inconsistent with that answer and was incorrectly admitted in
replay. The winning variant preserved the hold. Matching likely positives alone
would have missed this failure.

## Savings, including all priced token types

| Measure | Original | Retained replay | Reduction |
|---|---:|---:|---:|
| Valid comparison cases | 2,682 | 2,049 | 23.60% |
| Comparison uncached input tokens | 2,199,992 | 1,748,468 | 20.52% |
| Comparison cached input tokens | 3,607,808 | 2,772,352 | 23.16% |
| Comparison output tokens | 281,158 | 220,811 | 21.46% |
| Known comparison API-equivalent subtotal | $7.5723448 | $5.9822812 | 21.00% |
| Original meaning generation and warmup subtotal | $1.5577768 | $1.5577768 | 0% |
| **Known total API-equivalent subtotal** | **$9.1301216** | **$7.5400580** | **17.42%** |

The retained cases comprise 2,033 initial comparisons and sixteen verification
comparisons. The total reduction is
`(9.1301216 - 7.5400580) / 9.1301216 = 17.4156%`, or $1.5900636.
It uses the saved API-equivalent prices and native receipt accounting.
Reported cache writes are zero; reasoning is already included in output tokens
and is not charged twice. All original meaning generation and warmup costs are
retained. Historical answer reuse does not erase original generation cost.

These are **conditional saved-token projections**, not measured costs of a fresh
build. Seven original failed attempts lack usage, so complete totals are unknown;
three are comparison failures and remain in the retained attempt accounting.
Dispatching fewer requests could change cache behavior. Local encoding, training
and retrieval costs are outside these API subtotals.

## What remains unproven

The successful model screen splits fifty notes into forty development and ten
test notes. Development predictions exclude their own note fold; test predictions
use development data. However, this is corpus-wide training rather than learning
only from the construction's past. Later feature-removal experiments were chosen
after inspecting results, so the winning variant has no untouched final test set.

Replays trained only on earlier observed construction answers did **not** preserve
the whole hierarchy. The successful score also reranks only the original sixteen
candidates: it cannot recover an unqueried relationship outside that pool. Keeping
the historical graph preserves its existing semantic qualifications, not verified
general correctness.

The next useful validation is to train this method on approved ASv6.100 saved
comparisons, freeze it, and test an independent current-data construction. Check
the final hierarchy, important negatives, equivalence placements and total cost
together. Do not deploy these historical weights or lower the production cap yet.
The current research scans all candidates; a large-corpus implementation would
also need bounded indexed retrieval rather than an exhaustive per-query scan.

## Code and evidence

- [Full study, alternative rankings and transfer failures](candidate-ranking-fifty-note-study-v1.md).
- [Source-bound auxiliary vector preparation](canonical_ranking_vectors.py).
- [Scoring, strict replay and native receipt accounting](candidate_ranking_study.py).
- Frozen result: `target/candidate-ranking-study-v1/final-verification-v3.json` in
  `/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-candidate-rankings-v1`.

The underlying study passed 24 unit/worker tests and complete native offline
replay for both the original policy and `no-graph-12`. This writeup changes
documentation only; no prompt, constructor, runner, graph or UI was changed.
