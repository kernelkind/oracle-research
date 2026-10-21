# Selecting epsilon from saved merge distances — exploratory v1

Status: candidate numerical rule, not an approved or activated HiGen policy.
This investigation made no model calls, changed no frozen group membership,
and did not update the hierarchy review UI or production constructor.

## Reference and result

After considering a four-block grouping, the user reviewed the complete HR21
distance cut at epsilon 0.94 and said, "i like how this looks." This later
reference has **15 sections**, not four or six. It retains the nine-group
branch ending at G09, the G03/G16 pair, the G04/G10 pair, and twelve singleton
groups. It is a reviewed visual grouping, not independent semantic gold for
all possible section names.

A candidate rule based on the bend in the distance curve automatically
selects **epsilon 0.94062506360364** and reproduces this partition exactly.
It uses no G IDs, supplied target section count, or prescribed branch size.

The complete 15-section partition is unchanged throughout:

`0.9161756052325961 < epsilon < 0.9650745219746838`.

The nine-group branch itself survives over a slightly wider interval; the
upper boundary above additionally keeps the Ice group separate from the
Coffee/Coffee-shops pair. The proposed epsilon is the midpoint of the full
partition's interval, rather than an estimate of the manually supplied 0.94.

## Candidate rule

1. Preserve the original selected HDBSCAN groups as indivisible leaves. Use
   their saved ancestor connections, removing unassigned-only branches and
   collapsing ancestors with one surviving child, as the production section
   adapter already does.
2. Sort the distinct angular merge distances from largest to smallest. At
   each distance, record the number of sections after splitting all joins at
   that level. Equal-distance joins are processed together.
3. Use the middle approximately 80% of those distance levels to find the
   bend. Specifically, omit `ceil(0.10 * level_count)` levels from each end
   **only while fitting the curve**.
4. Normalize both section count and distance across those retained points.
   Select the point farthest above the straight line connecting the ends of
   the decreasing distance curve. A score tie favors fewer sections.
5. Set epsilon halfway between that point's distance and the next smaller
   distance in the **full original curve**. Apply the cut to the full tree.

No groups or notes are removed by the fitting step. Exceptionally tight
connections still participate in the final cut; they just cannot dictate the
range used to identify the main bend. The rule needs at least three retained
distance levels and a positive deviation to identify a bend. Construction
fallbacks for cases without one remain unspecified.

For retained curve points, define:

```text
x = (section_count - first_count) / (last_count - first_count)
y = (first_distance - distance) / (first_distance - last_distance)
score = x - y
```

This is equivalent to the geometric bend rule above. Using actual section
counts, rather than row numbers, handles simultaneous multi-branch splits.
Counts can be accumulated by adding `child_count - 1` at each split; a
production implementation need not repeatedly traverse the tree. Sorting and
selection take O(G log G) work for G fixed groups, without model requests.
This bound covers the added cutoff selection after projection, not HDBSCAN
itself or loading its full saved result.

## Why the complete curve is misleading on HR21

The Coffee/Coffee-shops connection has angular merge distance 0.302043, far
below the other displayed joins. The largest consecutive distance gap is
0.649871 to 0.302043. Choosing that gap gives epsilon 0.475957 and **24
sections**: almost every fixed group appears separately.

The untrimmed curve-bend rule and a curve measured using reciprocal density
also choose that overly fine partition. Fitting the central distance range
instead selects the interval 0.965075 to 0.916176: the cut separates weaker
connections while retaining the reviewed food/cooking branch.

HR21 gives the exact reviewed partition for every tested trimming fraction
from **5%, 10%, 15%, 20%, and 25% per end**. This is a sensitivity check on the
same fitted reference, not held-out validation.

## Checks on larger frozen trees

The identical 10% rule was applied without changes to four existing 100-note
trees. All fixed groups remained covered exactly once.

| Saved tree | Fixed groups | Selected epsilon | Sections | Largest section, fixed groups |
|---|---:|---:|---:|---:|
| HR21 | 25 | 0.940625 | 15 | 9 |
| HR22 | 62 | 0.826501 | 42 | 15 |
| HR23 | 42 | 0.885536 | 21 | 14 |
| HR24 | 46 | 0.885536 | 25 | 14 |
| HR25 | 39 | 0.883269 | 20 | 13 |

The larger partitions have no new user-reviewed targets. Their section
counts alone do not establish semantic quality or reduced browsing effort.
In particular, HR22's largest section includes **Domestic dogs** alongside
food-related groups. That group's fixed meaning includes companion, working
and feral dogs and is not restricted to food. This is a concrete review
concern, not an assigned prompt fault or a new human rejection.

Trimming sensitivity also differs by tree:

- HR22: 5–15% selects 42 sections; 20–25% selects 35.
- HR23: all five tested fractions select the same 21-section partition.
- HR24: selects 24 or 25 sections, depending on the fraction.
- HR25: all five tested fractions select the same 20-section partition.

The fitting result is therefore promising but not a certified general rule.
It does not enforce a six-option menu. Grouping or selecting further levels
would be separate construction work.

## Alternative controls

- **Fixed epsilon 0.94:** gives 15, 28, 17, 21 and 16 sections on HR21–HR25.
  Keep this simple baseline; an adaptive rule must earn its added complexity
  through reviewed grouping quality, not merely return a different epsilon.
- **Largest distance gap:** chooses 24 sections on HR21; it is dominated by
  the unusually tight pair described above.
- **Persistence after a substantial fork:** choose a largest child born at
  a split with at least two children each containing two or more fixed
  groups, then use the midpoint of its longest survival interval. This
  reproduces HR21 at epsilon 0.941940, but the density-based version produces
  almost-singleton partitions on the larger trees, including 57 of 62
  sections on HR22.
- **Weight fork persistence by group count or pair count:** still reproduces
  HR21, but can select very broad mixed-topic branches elsewhere. HR22's
  chosen branch contains 51 of 62 groups, including food, music, finance,
  people and mental states. This does not solve the broad-branch problem.
- **Three fitted line segments:** on HR21 chooses epsilon 0.966389 and 14
  sections. It retains the nine-group branch but keeps Ice together with the
  Coffee/Coffee-shops pair, unlike the reviewed reference.

These controls explain why simply choosing the biggest gap, longest-lived
branch, or most heavily supported branch is insufficient. They do not prove
that every possible use of persistence or stability fails.

## Retained evidence

Frozen source paths and hashes, production-plan validation, complete split
curves, all proposed cuts and memberships, trimming sensitivity, weighted
fork controls, and projected trees are saved in the ignored artifact:

`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hr21-persistence-partitions-v1/target/hr21-epsilon-study-v1/analysis.json`

The prior four-block investigation remains separately recorded in
[hr21-root-partition-controls-v1.md](hr21-root-partition-controls-v1.md).
The full 0.94 reference SVG is retained at:

`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hr21-persistence-partitions-v1/target/hr21-root-partition-study-v1/hr21-epsilon-094-all-sections-v1.svg`.

Subsequent numerical comparisons are recorded for
[100 Food & Drink notes](food-drink-hundred-epsilon-v1.md),
[50 Music notes](music-fifty-epsilon-v1.md) and
[a mixed Food/Music sample](food-music-fifty-epsilon-v1.md).
They preserve the distinction between a numerical cut and semantic review.

## Offline review command

`sse_multivector/hdbscan_epsilon_review.py` applies this exact experimental rule
to a saved native HDBSCAN state. It validates the native state, vector receipts,
request identity and selected memberships. It writes the complete colored SVG,
compact group/section tables and numerical evidence to an ignored output
directory. It makes no model calls and changes no saved state or production
construction policy. It fails explicitly when the candidate has too few
retained distance levels or no positive bend; no fallback has been approved.

From a task worktree, with the frozen state's absolute path:

```bash
python3 -m sse_multivector.hdbscan_epsilon_review \
  /absolute/path/to/state.json \
  --output target/epsilon-review-v1 \
  --title 'HDBSCAN groups · automatic epsilon candidate'
```

The production-path checks reproduce HR21's exact reviewed partition, count
tied splits together and verify that every displayed group has a section color.
An independently loaded HR21 native state also reproduced all 25 groups, all
15 sections and epsilon 0.94062506360364. This qualifies the mechanical review
tool, not the semantic quality of a new corpus's automatically selected cut.

To recluster subsets from several saved sources, pass their state paths and
`--notes-per-source N`. The command selects the first N notes of each source,
reuses their original L1 Bootstrap titles/meanings and exact vectors, and runs
the same production angular HDBSCAN executable on the combined inputs. It does
not combine the sources' old groups. Bootstrap-v133 wording, teacher settings
and SSE model identities must match; duplicate note IDs, unfinished Bootstrap
results and different HDBSCAN executables are rejected. This offline mode
performs no model calls or encoding and preserves every source artifact.
