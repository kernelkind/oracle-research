# Do the two examples help Astra keep each subject self-contained?

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

Not reliably in this comparison. They helped the hiring note, but did not fix the CEO note that motivated this test. ASv6.21 is not adopted.

We ran the unchanged ASv6.13 and ASv6.21 prompts on the same six original notes: three fresh calls per prompt per note, all using Astra low. ASv6.21 adds only the existing swimming-pool and tapestry examples. There were 36 calls and 631 generated subjects. Every subject and each note's meaning coverage were reviewed.

| Result | ASv6.13 | ASv6.21, with examples |
| --- | ---: | ---: |
| Hiring-note outputs missing event context | 3 of 3 | 1 of 3 |
| CEO-note outputs missing CEO context | 2 of 3 | 3 of 3 |
| CEO meanings with the necessary context | 4 of 12 | 4 of 12 |
| Outputs with no error, unresolved judgment or omission | 12 of 18 | 13 of 18 |

All four tested CEO meanings were generated in every output. Omitting a meaning therefore does not explain that result.

## The CEO note

This is the complete, unchanged source, including its unfinished quotation:

> "CEO has all employee calls where he does questions at the end that you can ask via an anon chat. He always says ask me something hard. So I asked him if his wife knew about what he&#39;s up to with hi"
>
> this development changes my entire thesis. I've been tracking this for months and the trajectory is undeniable. the fundamentals are aligning in a way that's hard to ignore.
>
> https://mastodon.social/@fesshole/116810711404206903

The four later meanings concern the changed thesis, months of tracking, the trajectory, and the fundamentals. A subject about one of those specific claims needs to identify the CEO-related matter; “the situation” alone does not do that.

ASv6.21, trial 3, generated:

> The author says they have been tracking the situation described in the CEO account for months.

That item identifies what was being tracked. But the next item was:

> The author describes the trajectory of the situation they have been tracking as undeniable.

Read alone, the second item does not say what situation it concerns. The preceding item supplies its context, which is the failure we were trying to prevent.

Here is every tested CEO meaning, not just that example. “Yes” means the generated item independently identifies the CEO-related matter.

| Meaning | ASv6.13 trial 1 | Trial 2 | Trial 3 | ASv6.21 trial 1 | Trial 2 | Trial 3 |
| --- | --- | --- | --- | --- | --- | --- |
| Changed thesis | No | No | Yes | Yes | Yes | Yes |
| Tracking for months | No | No | Yes | No | No | Yes |
| Undeniable trajectory | No | No | Yes | No | No | No |
| Aligning fundamentals | No | No | Yes | No | No | No |

The examples changed which items retained context, but the total remained 4 of 12. One ASv6.13 output got all four right; no ASv6.21 output did.

## Where the examples helped

Complete hiring note:

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

All three ASv6.13 outputs omitted the hiring event from the analyst-disagreement subject. For example, trial 1 returned:

> One analyst deviating from other analysts by using predictive phrasing.

Two of the three ASv6.21 outputs supplied that context. Trial 1 returned:

> One analyst diverging from other analysts by using predictive phrasing in an assessment of OpenAI's hiring of Riley Walz.

The third ASv6.21 output still omitted it. This is a useful local improvement, not a reliable fix across the two context problems.

## Other findings

Complete fee note:

> Block 923432
>
> 3 - high priority
> 1 - medium priority
> 1 - low priority
> 1 - no priority
> 1 - purging
>
> #bitcoinfees #mempool

Both prompts kept the fee/mempool context without inventing units or arithmetic. However, ASv6.21 trial 3 omitted block 923432 entirely; the other five fee outputs included it.

No subject errors were identified in the dashboard, insurance or Iran/Bitcoin outputs under either prompt. In particular, the earlier URL-derived dashboard name and incorrect insurance attribution did not recur here.

One ASv6.13 CEO subject's infidelity interpretation remains unresolved because the quotation is clipped. Whether ASv6.21 trial 3 lost the overall investment-analysis framing is also unresolved. Neither uncertainty is silently counted as success. Every source, output and individual judgment (`./full-outputs.md`) is preserved.

## What this establishes

These two examples did not meet the predeclared CEO-context improvement criterion. The one-output increase in fully accepted results does not establish a dependable overall improvement from three repeats on six known notes.

This does not show that examples can never help, or explain how Astra internally resolves references. It shows that these examples were insufficient for this particular failure.

ASv6.8 stays frozen. No final-validation notes were used. No additional run or prompt change follows automatically.

## Record

Three fresh independent reviewers each checked 12 outputs with prompt/trial identities hidden, covering all 36 outputs between them. I also reviewed everything and recorded disagreements separately. These are assistant judgments, not new user approvals.

All 36 calls used unique threads and working directories. The isolated runner, prompts, original notes and recorded hashes passed verification. Generation took 104.745 seconds with at most 12 calls active. During execution, available memory stayed above 102.96 GiB; sampled memory and I/O pressure remained zero. The longest host-check gap was 7.126 seconds against a nominal five-second cadence.

Token usage: ASv6.13 used 47,331 input and 6,751 output tokens; ASv6.21 used 51,435 input and 6,291 output tokens. Reasoning tokens are already included in those output totals. Provider prefix caching does not imply conversation reuse.

[Predeclared comparison](./proposal.json) · Assessment (`./assessment.json`) · Review reconciliation (`./review-reconciliation.json`) · Verification (`./verification.json`)

See conversion gaps (`03bd9e45:docs/experiments/publication-gaps.csv`) for `collection:tracked-subject-prompt-goal-v1`.
