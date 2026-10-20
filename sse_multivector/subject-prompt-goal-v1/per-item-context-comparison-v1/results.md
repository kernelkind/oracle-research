# Per-item context: ASv6.13 versus ASv6.23

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

The new format improved the final subjects in this small comparison. This is a result on two known development notes, not general validation.

We kept the original notes and Astra low unchanged. Each prompt ran three times per note in a fresh isolated call. ASv6.23 added a generated `context` field before each final `subject`. Reviewers judged the subjects alone before seeing those context fields.

| Result | ASv6.13 | ASv6.23 |
| --- | ---: | ---: |
| Outputs with no identified error | 3/6 | 6/6 |
| CEO-note outputs missing necessary context | 2/3 | 0/3 |
| Hiring-note outputs missing necessary context | 1/3 | 0/3 |
| Accepted subjects | 140/148 | 134/134 |

All 282 subjects were reviewed. Broad, overlapping and duplicate subjects remained allowed. Two independent reviewers and the main reviewer agreed on the eight context errors after clarifying the existing standard, while prompt identities were still hidden.

Read both original notes and every generated subject and context field (`./full-outputs.md`).

## CEO note

> "CEO has all employee calls where he does questions at the end that you can ask via an anon chat. He always says ask me something hard. So I asked him if his wife knew about what he&#39;s up to with hi"
>
> this development changes my entire thesis. I've been tracking this for months and the trajectory is undeniable. the fundamentals are aligning in a way that's hard to ignore.
>
> https://mastodon.social/@fesshole/116810711404206903

The four later assertions are about the CEO-related situation: a changed thesis, tracking for months, an undeniable trajectory, and aligning fundamentals. Every output included those assertions. The difference was whether each assertion identified what it concerned.

| Necessary CEO context | Trial 1 | Trial 2 | Trial 3 |
| --- | ---: | ---: | ---: |
| ASv6.13 | 1/4 assertions | 0/4 assertions | 4/4 assertions |
| ASv6.23 | 4/4 assertions | 4/4 assertions | 4/4 assertions |

For example, these are the trial-1 subjects about tracking for months.

ASv6.13:

> The commentator describes having tracked the matter under discussion for months.

ASv6.23:

> The post's writer says they have been tracking the situation surrounding the reported CEO anecdote for months.

The second subject identifies the CEO-related matter. The first leaves its reader asking what “the matter under discussion” means. Another subject cannot supply the missing context because each subject is used independently.

This judgment does not require the precise alleged conduct or the missing end of the quotation. “The CEO anecdote” satisfies the predeclared requirement. An insinuation of infidelity was allowed; no generated subject asserted an actual affair.

## Hiring note

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

The missing context occurred in ASv6.13 trial 2:

> One analyst's deviation from other analysts through the use of predictive phrasing.

ASv6.23 trial 2 produced:

> One analyst deviated from the other analysis of OpenAI’s hiring of Riley Walz by using predictive phrasing.

The new subject identifies the analysis as being about Riley Walz joining OpenAI. All three ASv6.23 outputs did this. Monitoring subjects retained the hiring context under both prompts in every trial, and all six outputs covered the three closing questions.

The three electronic-labour subjects were accepted as broad descriptions of hiring/software/AI work. They were not rejected merely because a sector label also named that topic.

## What this does and does not show

The approved prompt/output-format change met the predeclared condition for a positive local result: fewer CEO context failures, the same four assertions retained, no increase in hiring failures, and no identified offsetting semantic regression.

The auxiliary context fields did **not** consistently spell out the references themselves. For the successful trial-1 tracking subject, the preceding context was:

> The writer's claimed history of following the situation discussed in the post.

That field is still generic; the final subject supplies the CEO context. Therefore, we cannot say the result proves that explicitly writing resolved references first caused the improvement. The changed output structure, instructions, repetition or extra generation may matter. This comparison tested them together.

Reported output tokens rose from 3,132 to 5,189—about 66%. Reported input tokens were 15,897 and 16,311. Reasoning-token counts were 741 and 711 respectively; these are reported separately, not added to output-token totals.

Keep ASv6.23 unchanged for proposed broader confirmation. These two notes do not justify freezing it as the replacement. ASv6.8 remains the frozen default.

## Record

- [Predeclared comparison](./proposal.json)
- Final review and reconciliation (`./review.json`), independent review A (`./reviewer-a.json`), independent review B (`./reviewer-b.json`)
- Integrity and resource verification (`./verification.json`)

All 12 calls had distinct threads and working directories, one turn each, and no tool use. Exact prompts, source text, schemas and raw outputs passed verification. The comparison used the existing Codex wrapper's new optional schema support; it did not use a two-call generation pipeline. The wrapper requests schema-constrained output through [Codex's documented interface](https://developers.openai.com/codex/noninteractive#create-structured-outputs-with-a-schema).

The calls completed in 41.4 seconds. Resource sampling continued throughout, with a maximum interval of 5.0001 seconds. Available memory stayed above 105.58 GiB; sampled memory and I/O pressure averages remained zero. All owned units finished. Per-unit limits do not cover descendants that start independent units, and samples cannot rule out changes between observations.

The runner passed 60 regression/consumer tests; the resource driver passed nine tests. Both changes were tested with expected failures before implementation. No reserved final data was used, and the earlier final-note exposure remains outside this experiment.

See [conversion gaps](../../../docs/experiments/publication-gaps.csv) for `collection:tracked-subject-prompt-goal-v1`.
