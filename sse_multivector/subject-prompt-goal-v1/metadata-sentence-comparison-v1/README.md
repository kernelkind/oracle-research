# ASv6.17 versus ASv6.18: content and presentation

ASv6.18 reduced unwanted metadata on three of the four targeted notes. The result is mixed: source attribution and commentary about missing text still need investigation. Neither prompt is ready to freeze, and the changed sentence is not yet retained as the next development baseline.

## What changed

Everything stayed fixed except one sentence in ASv6.17.

ASv6.17:
> Use labels, credits and identifiers as context for understanding the message they accompany, not to describe how the message is labeled, credited or categorized.

ASv6.18:
> Subjects concern the communicated content, not labels, credits or identifiers used merely to present it.

The [proposal](../asv6.18/proposal.json) was saved before generation. Nine development notes received three fresh outputs from each prompt: 54 calls. Model, effort, source text, normalization and runner stayed fixed. Calls ran one at a time with alternating prompt order. All outputs were reviewed against the complete notes; duplicate, overlapping and broad subjects were allowed.

## What the repeated comparison found

Each number below counts outputs containing the specified problem, out of three. These are counts from deliberately selected difficult notes, not corpus error rates.

| Note | Problem checked | ASv6.17 | ASv6.18 |
| --- | --- | ---: | ---: |
| D14: mirroring-only post | Mirroring credit treated as a subject | 2 | 0 |
| D21: meditation quotation | Separate bibliographic-credit subject | 3 | 1 |
| D24: insurance report | Confidence/classification treated as a subject | 2 | 0 |
| D26: spaceflight crew | Caption position treated as a subject | 1 | 1 |
| D10: Riley Walz report | Confidence/classification treated as a subject | 3 | 3 |
| D19: Bitcoin dashboard | Name taken only from the URL | 3 | 3 |
| D23: fee-priority list | Numeric item lacks its fee/mempool context | 3 | 3 |
| D25: clipped CEO anecdote | Commentary about what the source leaves unstated | 1 | 2 |

D14, D21, D24 and D26 were the four predeclared metadata targets. D10 was a context-regression check that also contained metadata. D22, the hacking-services advertisement, was clean in all three outputs under both versions; the URL-derived provider name from the earlier broad comparison did not recur.

The insurance case also exposed a tradeoff. ASv6.17 explicitly distinguished the two-model analysis in one trial, left the bare source name “The Council” unresolved in another, and did not make an explicit wrong-source attribution in the third. ASv6.18 explicitly assigned the later analysis to CIAB in one trial and used the unresolved bare source name in the other two. An unresolved source is not a proven wrong attribution, but it is not a pass.

ASv6.18's third CEO output introduced a separate distortion. The source says:
> this development changes my entire thesis. I've been tracking this for months

The generated subject says:
> The poster rhetorically describes the CEO anecdote as a consequential development that confirms a months-long thesis through an undeniable trajectory and aligning fundamentals.

“Changes” became “confirms,” and the duration of tracking became the duration of the thesis. This is a fidelity error, not a complaint about figurative language. It occurred once, so the comparison does not establish that the changed metadata sentence caused it.

## What this establishes

The shorter content-versus-presentation sentence improved the targeted behavior across several source forms. It did not solve metadata extraction generally, URL-derived naming, or per-item numerical context.

Across all 27 outputs per version, ASv6.17 had 8 clean outputs and 183/227 accepted subjects; ASv6.18 had 11 clean outputs and 174/210 accepted subjects. A clean output has no identified error or unresolved judgment and no identified missing meaning. These totals do not erase serious errors or establish a better overall prompt.

Those are the original recorded review totals. The later [review correction](../semantic-review-audit-v2.json) accepts two ASv6.17 trial-2 subjects that reasonably express possibilities supported by the Riley Walz post. The adjusted ASv6.17 total is 185/227 accepted subjects. Its 8/27 clean outputs and this comparison's overall conclusion are unchanged; original reviews and verification outputs remain preserved.

The predeclared metadata-improvement condition was met. The context tradeoff remains mixed: missing-text commentary occurred under both versions, but more often in ASv6.18, and attribution was worse or unresolved. This is not enough to infer a reliable causal regression or to retain the change automatically.

The [subsequent confirmation](../metadata-confirmation-v1/README.md) completed three additional fresh outputs per prompt on D24 and D25. Metadata improvement persisted, but explicit wrong-source attribution recurred under ASv6.18. It was not promoted as an overall replacement. The [current goal status](../status.json) records the later full-development work; the original final-validation requirements remain mandatory.

## Evidence and execution

- [Exact source notes](../asv6.18/input.json).
- [Every subject judgment and whole-note coverage review](./review.json), preserving the generated wording and recording reviewer uncertainty separately.
- Raw outputs: [ASv6.17 trial 1](./asv6.17-trial-1/output.json), [trial 2](./asv6.17-trial-2/output.json), [trial 3](./asv6.17-trial-3/output.json); [ASv6.18 trial 1](./asv6.18-trial-1/output.json), [trial 2](./asv6.18-trial-2/output.json), [trial 3](./asv6.18-trial-3/output.json).
- [Verification](./verification.json): 54 unique fresh threads and working directories, one turn and no tools per call, exact prompts and raw hashes, all semantic reviews present, no reuse across the 273 earlier calls checked. This verifies provenance and review completeness, not the correctness of the judgments themselves.
- [Runtime record](./runtime.json): sequential admission and host-pressure observations. Minimum observed available memory was 104.25 GiB; maximum memory PSI avg10 was 0.29 and I/O PSI avg10 was 5.32. Launcher limits do not bound separately scoped Codex children; host monitoring remained active.

Usage: 123,438 input tokens and 17,006 output tokens, including 7,561 reasoning tokens; 1,920 input tokens were cached. No new paid API or rental resources were used. The canonical ASv6.8 registry, validation plan and unseen final inputs remain unchanged.
