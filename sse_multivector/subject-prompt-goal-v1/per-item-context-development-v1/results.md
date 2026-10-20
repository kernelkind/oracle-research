# ASv6.23 — broader development comparison

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

ASv6.23 produced fully accepted subject lists for **27 of 28 notes**, compared with **25 of 28** for ASv6.13. The improvement is modest: one definite missing-context error was absent, and one uncertain wording was avoided. One uncertain interpretation remains.

A fully accepted list has no identified error, unresolved judgment or missing meaning. This is assistant semantic review, not a measured population accuracy.

| Result | ASv6.13 | ASv6.23 |
|---|---:|---:|
| Fully accepted note lists | 25/28 | 27/28 |
| Definite subject errors | 1 | 0 |
| Subjects with unresolved judgments | 2 | 1 |
| Accepted subjects | 281/284 (98.94%) | 267/268 (99.63%) |
| Missing distinct meanings identified | 0 | 0 |
| Fully accepted lists outside the two previously tested notes | 24/26 | 25/26 |

Both unchanged prompts ran once on each of the same 28 development notes, using Astra low: 56 fresh calls. Only ASv6.23's final subjects were scored; its context fields could not rescue incomplete subjects. All 552 subjects and all source notes were reviewed before prompt identities and context fields were revealed. Independent reviewers checked separate halves; disagreements and the main review's reconciliations are preserved.

The complete notes and outputs (`./full-outputs.md`) contain every subject and context field, unedited.

## The clear difference: hiring context

D10, complete original note:

> Riley Walz, the Jester of Silicon Valley, Is Joining OpenAI
>
> The software engineer known for online stunts is joining OpenAI to work on new ways for humans to use AI systems.
>
> Sector: Electronic Labour | Confidence: 96%
> Source: https://www.wired.com/story/openai-hires-riley-walz/
>
> ---
> Council (2 models): OpenAI hires Riley Walz, a high‑visibility internet personality, to embed cultural relevance into its AI offerings and sharpen user‑centric design. The move acts as a branding lever that shapes market perception, prompting heightened investor sentiment, prompting insurers to reassess liability exposures from new human‑AI interaction patterns, and driving data‑center planners to scale capacity for anticipated usage spikes. Analysts converge on the significance of this talent acquisition for brand and experience strategy, while noting that one analyst deviated by using predictive phrasing. The council highlights key metrics, valuation impacts, and cloud infrastructure adjustments for ongoing monitoring.
> Cross-sector: Finance, Insurance, Real Infrastructure
>
>   ? Which user‑experience metrics does OpenAI prioritize in evaluating the impact of culturally‑oriented talent?
>   ? How do investors incorporate talent announcements into valuation models for AI firms?
>   ? What adjustments do cloud providers make to support increased interactive AI workloads linked to engagement‑driven features?
>
> #FIRE #Circle #ai

ASv6.13, subject 23:

> One analyst deviating from the other analysis by using predictive phrasing.

ASv6.23, subject 20:

> One analyst deviated from the other analysis of OpenAI’s hiring of Riley Walz by using predictive phrasing.

The first item says “the other analysis” without identifying which analysis. The second identifies the Riley Walz/OpenAI hiring analysis. This is necessary context for that specific analyst comparison, not a requirement that every broad subject repeat the entire hiring event.

Both prompts handled the CEO note correctly in this run. The earlier three-trial comparison remains separate evidence; this run does not show a new CEO advantage.

## The remaining uncertain interpretation: snow

D08, complete original note:

> short ah snow was still fly❤️‍🩹
> https://blossom.primal.net/875482ecf94c2354db11dd2f23aeb8df50f5b6ee817ed07bc12eeccdd4e41149.jpg

ASv6.13:

1. A brief snowfall still being beautiful or cool despite its short duration.
2. Someone called Snow being short in stature but still stylish or attractive.
3. Affection and a sense of emotional healing associated with the short but still appealing snow.

ASv6.23:

1. A brief snowfall.
2. The snowfall was still cool or impressive despite being brief.
3. Snow was still flying through the air despite the snowfall being brief.
4. Affection for a brief snowfall.

“Still fly” naturally reads as slang for “still cool.” ASv6.13 additionally reads Snow as a short person. ASv6.23 additionally reads “fly” as literal motion through the air.

Neither extra interpretation is clearly grounded enough to accept confidently. They are recorded as **unresolved**, not definite failures. Both lists therefore count against the fully accepted-note threshold. The mending-heart emoji can support the rhetorical healing association; that was not treated as an invented causal claim.

ASv6.23's context for its uncertain third item was:

> The literal airborne meaning of “fly” in the description of snow.

Producing a context field does not guarantee a correct interpretation.

## The other uncertain wording: readers versus complainants

D27, complete original note:

> An example of me being completely wrong:
> I was recently watching old Tex Avery cartoons and was drawn towards the ones banned from circulation. I watched one called Uncle Tom's Cabaña banned for depicting black people unfairly apparently after a newspaper complained about it. In the cartoon to my surprise the villain of the picture (Simon Legree) is depicted as a hook nosed money obsessed Dick Dastardly level villain who snakes across the ground looking to swindle people out of money. The instant I saw this I started to wonder if the real reason the cartoon was pulled was because it was actually insanely anti-semitic on a level I've never seen before. I looked into the complaints and found the original articles published in the Pittsburgh Courier negro newspaper about it expecting that the editor or owner of the paper would be Jewish and after hours of searching I had to give up as everybody involved was just black and offended by the cartoon on its own terms.
>
> https://media.shitposter.world/shitposter.club/9e/e2/c1/9ee2c1660b0e3f8ea15276a8dbad5345149fba0649ffbdf0ec6f613c29dede6b.webp?name=LK6feqLqs5CE6Q.webp

ASv6.13, subject 7:

> The unfair depiction of Black people in Uncle Tom's Cabaña and Black readers' objections to that depiction.

The note says the people involved in the newspaper complaints were Black. It does not establish a reader role. “Black readers” might be loose shorthand, but might add unsupported detail, so the judgment remains unresolved.

ASv6.23, subject 22:

> The author found that the Black people involved in the Pittsburgh Courier complaints were offended by Uncle Tom's Cabaña's depiction of Black people itself.

This does not add the reader role. This one uncertain wording accounts for the entire advantage outside the previously tested hiring and CEO notes; it is not strong evidence of a general improvement across new kinds of notes.

## Review corrections

The initial judgments are preserved, not silently overwritten. The final review (`./review.json`) explains each reconciliation.

- I initially flagged fee values for omitting block 923432. That was too strict: “a high-priority Bitcoin transaction fee level of 3” is a supported, independently understandable observation, not a universal rate. Broad and narrow subjects are allowed. This differs from earlier failures that omitted fee/mempool meaning itself or invented counts or units.
- Visible requests such as “Connect on LinkedIn,” “Visit Us” and “Contact Us” communicate actions. They are not merely subjects saying that a URL or address exists. Minor meanings are allowed.
- Report labels such as “Sector” and “Confidence” are not required subjects.
- A broad subject about planning data-center capacity can be valid without repeating the hiring event. That differs from “the other analysis,” which leaves the specific comparison unidentified.
- The broader insurance-financing inquiry remains understandable without repeating every capacity detail.

These corrections apply to both prompts before the versions were revealed. They are review corrections, not prompt improvements. Initial independent reviews do not constitute unanimous agreement with the final main review.

## What this supports next

ASv6.23 meets the existing **first-pass** development thresholds: at least 26/28 fully accepted lists and at least 95% accepted subjects. It has not completed the repeated-development or final-validation requirements, and ASv6.8 remains frozen.

Recommendation: keep ASv6.23 unchanged and obtain two more fresh outputs for each of the eight already designated difficult notes—16 calls. With this run, each would have three outputs. This checks repeatability without starting another speculative prompt revision. It is a recommendation, not a run already performed or authorized.

This comparison tests the changed prompt/output-format package, not an internal mechanism. For example, a D25 context field says “The commenter’s account of sustained attention to the situation,” while its final subject correctly names the CEO anecdote. The auxiliary field itself has not reliably resolved every reference.

## Run record

All 56 calls used separate ephemeral threads and temporary workspaces. Each had exactly one turn, one response and no tool events or retries. Input, prompt, schema and output hashes matched. The two schemas and both prompts were unchanged. The technical verification (`./technical-verification.json`) preserves the checks.

| Reported tokens | ASv6.13 | ASv6.23 |
|---|---:|---:|
| Input | 72,160 | 74,092 |
| Cached input | 21,504 | 13,824 |
| Output | 7,251 | 11,271 |
| Reasoning output, separately reported | 2,872 | 2,520 |

ASv6.23 reported about **55% more output tokens**, including its context fields. Reasoning tokens are not added again to the output total.

Five sequential batches used at most 12 concurrent calls. Generation ran from 19:54:13 to 19:57:11 UTC, including the gap between batches. Maximum sampled interval was 5.00017 seconds, minimum available memory was 105.23 GiB, and sampled memory/I/O pressure was zero. All owned units were inactive afterward. Sampling does not observe sub-interval spikes; per-unit limits cannot bound descendants launched into separate scopes.

Plan/config commit: `214764ea5acae42310949fb8649bd0a052eff058`. Goal generation-call total is now 588. No reserved final note was read, no new paid API/rental was used, and no personal notes document was edited. Existing final-data exposure remains a separate unresolved issue before final validation.

See [conversion gaps](../../../docs/experiments/publication-gaps.csv) for `collection:tracked-subject-prompt-goal-v1`.
