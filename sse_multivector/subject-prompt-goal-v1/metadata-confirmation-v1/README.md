# ASv6.17 versus ASv6.18: confirmation

The metadata improvement persisted, but ASv6.18 did not become a reliable overall replacement. Explicit source misattribution recurred, and both prompts sometimes lost the CEO context or commented on the unfinished text. Do not keep repeating these two notes to seek a passing run.

## What was tested

The [first comparison](../metadata-sentence-comparison-v1/README.md) changed one sentence about content versus presentation. It reduced metadata subjects but left mixed attribution and missing-text results.

This [predeclared confirmation](./proposal.json) repeated only the insurance report (D24) and clipped CEO anecdote (D25), without changing either prompt. Each prompt received three additional fresh calls per note, called trials 4–6: 12 calls total. All subjects and complete-note coverage were reviewed under the same requirements. The final validation set was not used.

## Results

Each cell is the number of outputs containing the specified problem, out of three. Original and confirmation trials are kept separate so neither batch replaces the other.

| Note and problem | ASv6.17 original | ASv6.18 original | ASv6.17 confirmation | ASv6.18 confirmation |
| --- | ---: | ---: | ---: | ---: |
| D24: confidence/classification subject | 2 | 0 | 3 | 0 |
| D24: analysis explicitly assigned to CIAB | 0 | 1 | 0 | 2 |
| D24: bare “The Council” leaves source unresolved | 1 | 2 | 3 | 0 |
| D25: commentary about missing source text | 1 | 2 | 1 | 1 |
| D25: individual item lacks CEO-event context | 0 | 0 | 1 | 2 |
| D25: “changes” becomes “confirms” a months-long thesis | 0 | 1 | 0 | 0 |

For D24, the complete source has a CIAB survey followed by a separately headed `Council (2 models)` analysis. The explicit wrong-source items assign the latter's interpretation to CIAB. The bare source name is recorded separately as unresolved, not automatically called a wrong attribution. Subjects without an explicit attribution are not automatically errors.

For D25, the source's `this development` follows the CEO/employee-question anecdote. An isolated output such as “The poster has been tracking the development for months” does not carry that available event context. A subject explaining that an unfinished phrase has no recoverable referent is commentary about the source, not a communicated subject.

Clean confirmation outputs: ASv6.17 1/6; ASv6.18 2/6. Accepted subjects: ASv6.17 70/82; ASv6.18 74/84. Across both batches, D24 was clean in 0/6 ASv6.17 outputs and 1/6 ASv6.18 outputs; D25 was clean in 3/6 and 2/6 respectively. Neither a few cleaner outputs nor a higher accepted-subject fraction overrides recurring fidelity problems.

## Decision

Keep the measured metadata improvement as evidence. Do not promote ASv6.18 as the next overall baseline. The source-attribution concern repeated; the missing-text difference did not repeat in the same direction, and new context omissions appeared under both prompts. These small counts do not isolate why the wording changes affected attribution.

The next comparison should return to ASv6.13, the earlier broadly tested reference, rather than automatically extending ASv6.18. ASv6.13 itself fails, but its full-development results provide a stronger starting reference than success on these two difficult notes. Test a general simplification of the output/fidelity instructions across the complete development set, retaining literal/nonliteral coverage, allowed overlapping subjects and every fixed validation requirement.

## Evidence

- [Complete source notes](./input.json), [all semantic judgments](./review.json), [runtime record](./runtime.json) and [verification](./verification.json).
- Raw outputs: [ASv6.17 trial 4](./asv6.17-trial-4/output.json), [trial 5](./asv6.17-trial-5/output.json), [trial 6](./asv6.17-trial-6/output.json); [ASv6.18 trial 4](./asv6.18-trial-4/output.json), [trial 5](./asv6.18-trial-5/output.json), [trial 6](./asv6.18-trial-6/output.json).

All 12 calls used unique fresh threads and working directories, one turn and no tools. Exact prompts, sources, outputs and raw hashes were verified, with no reuse across the 327 earlier calls checked. The unchanged production runner loaded every configuration. Verification checks provenance and review completeness, not the semantic judgments' truth.

Usage: 28,296 input and 6,427 output tokens, including 2,636 reasoning tokens. Minimum observed available memory was 105.23 GiB; both memory and I/O PSI avg10 maxima were zero. Calls were sequential with host monitoring and the existing launcher limits. No new paid resource, credential change, model change or downstream work occurred. The canonical ASv6.8 registry, acceptance criteria and final inputs are unchanged.
