# Making the CEO references explicit

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

The original passage lost the CEO reference in all three outputs. The edited passage retained it for all four tested meanings in all three outputs.

## What changed

**Control:** the original D25 note, unchanged.

**Variable:** the second paragraph explicitly names the CEO when discussing the development, tracking, trajectory, and fundamentals. The quotation, clipped ending, URL, and remaining text are unchanged. The edited version is a diagnostic input, not an authentic Nostr note.

**Fixed:** ASv6.13, Astra low, the existing subject-generation runner and schema. Three fresh calls per condition; six calls total. No mask generation or prompt revision.

**Hypothesis:** spelling out those references will reduce subjects that omit the CEO context. Before generation, the recorded condition required errors in at least two original outputs, none in the three edited outputs, and all four meanings covered in every edited output.

## The complete inputs

Original:

> "CEO has all employee calls where he does questions at the end that you can ask via an anon chat. He always says ask me something hard. So I asked him if his wife knew about what he&#39;s up to with hi"
>
> this development changes my entire thesis. I've been tracking this for months and the trajectory is undeniable. the fundamentals are aligning in a way that's hard to ignore.
>
> https://mastodon.social/@fesshole/116810711404206903

Edited:

> "CEO has all employee calls where he does questions at the end that you can ask via an anon chat. He always says ask me something hard. So I asked him if his wife knew about what he&#39;s up to with hi"
>
> this development concerning the CEO changes my entire thesis. I've been tracking this matter concerning the CEO for months and the trajectory of this matter concerning the CEO is undeniable. the fundamentals of this matter concerning the CEO are aligning in a way that's hard to ignore.
>
> https://mastodon.social/@fesshole/116810711404206903

## Results

We checked four meanings in each output: the thesis change, tracking for months, the undeniable trajectory, and the aligning fundamentals. Each specific subject must identify the CEO-related matter on its own; an exact phrase is not required.

| Trial | Original: meanings with CEO context | Edited: meanings with CEO context | Meanings present in each output |
| --- | ---: | ---: | ---: |
| 1 | 0/4 | 4/4 | 4/4 |
| 2 | 0/4 | 4/4 | 4/4 |
| 3 | 1/4 | 4/4 | 4/4 |

These are four meaning checks within each output, not 24 independent statistical trials.

For example, trial 2 produced:

Original input → generated subject:

> A commentator says they have been tracking the matter under discussion for months.

Edited input → generated subject:

> A commentator claiming to have tracked a matter concerning a CEO for months.

The edited outputs did not avoid the problem by dropping the affected meanings. All four appeared in every output. The predeclared directional condition was met.

## What this tells us

The unchanged model and prompt can carry the CEO context into each of these generated subjects when that context is supplied locally in the source paragraph.

This does **not** establish why the original wording failed. The edit both spells out references and repeats “CEO” more often. Better reference resolution, greater salience, and easier copying of explicit wording remain compatible explanations. The experiment does not observe the model's internal understanding.

It also does not establish a general solution, validate automatic source rewriting, or make the current prompt pass the larger validation plan. The quoted passage remains clipped, and its interpretation questions remain outside this target contrast.

## Every generated subject

The wording below is copied unchanged from the recorded outputs. “Context missing” refers only to the four tested meanings. Other flags are recorded separately so they cannot be mistaken for this experiment's result.

### Original, trial 1

Complete input (`./inputs/original.json`) · Raw output (`./original-1/run/output.json`)

1. A CEO holding calls for all employees.
2. A CEO answering employee questions at the end of all-employee calls.
3. Employees submitting questions to their CEO through an anonymous chat.
4. A CEO repeatedly inviting employees to ask him difficult questions.
5. An employee responding to a CEO’s invitation for difficult questions by asking whether his wife knows what he is up to.
   - Unresolved: Clipped-question paraphrase: prior unresolved boundary retained.
6. An employee using an anonymous workplace question session to challenge a CEO about his private conduct.
7. A question about whether a CEO’s wife knows about his activities.
8. An insinuation that a CEO is concealing activities from his wife.
9. An insinuation of marital infidelity in an employee’s question about a CEO’s wife knowing what he is up to.
   - Unresolved: Marital infidelity insinuation: prior unresolved boundary retained.
10. The contrast between a CEO’s invitation for difficult employee questions and an employee’s personally intrusive question about the CEO’s marriage.
11. A development completely changing the post’s commentator’s thesis.
   - Review: Specific target item does not identify the CEO-related matter.
12. The commentator having tracked the subject of their thesis for months.
   - Review: Specific target item does not identify the CEO-related matter.
13. The commentator describing the trajectory of the subject they have been tracking as undeniable.
   - Review: Specific target item does not identify the CEO-related matter.
14. The commentator describing fundamentals as aligning in a way that is hard to ignore.
   - Review: Specific target item does not identify the CEO-related matter.
15. The use of financial-analysis language to frame a reaction to an anecdote about an employee confronting a CEO with a question about his private conduct.

### Original, trial 2

Complete input (`./inputs/original.json`) · Raw output (`./original-2/run/output.json`)

1. A CEO holds calls for all employees.
2. A CEO takes employee questions at the end of all-employee calls.
3. Employees can submit questions to a CEO through an anonymous chat.
4. A CEO routinely invites employees to ask him difficult questions.
5. An employee responds to a CEO’s invitation for difficult questions by asking whether his wife knows what he has been up to.
   - Unresolved: Clipped-question paraphrase: prior unresolved boundary retained.
6. An employee uses a workplace question-and-answer session to confront a CEO about his private life.
7. An employee’s question insinuates that a CEO is engaging in conduct his wife may not know about.
8. An employee’s question insinuates marital impropriety by a CEO.
   - Unresolved: Marital impropriety insinuation: prior unresolved boundary retained.
9. The contrast between a CEO’s invitation for challenging questions and an employee’s personally provocative question about his wife.
10. An employee’s question about a CEO’s wife ends mid-sentence before specifying who or what is involved in the CEO’s conduct.
   - Review: The source excerpt is clipped; describing that missing text is extractor commentary, not a communicated subject. This violates the unchanged content-versus-source-presentation boundary.
11. A commentator says the reported development changes their entire thesis.
   - Review: Specific target item does not identify the CEO-related matter.
12. A commentator says they have been tracking the matter under discussion for months.
   - Review: Specific target item does not identify the CEO-related matter.
13. A commentator describes the trajectory of the matter they have been tracking as undeniable.
   - Review: Specific target item does not identify the CEO-related matter.
14. A commentator says underlying fundamentals are aligning in a way that is hard to ignore.
   - Review: Specific target item does not identify the CEO-related matter.
15. A commentator presents a workplace anecdote as a consequential development in an ongoing analysis.
   - Unresolved: Broad rhetorical subject versus omitted event context: independent reviewer accepted it; prior review rejected comparable wording. Kept unresolved here, outside the predeclared four-meaning contrast.
16. The use of investment-analysis language about a thesis, a trajectory, and fundamentals to react to an employee’s provocative question to a CEO.

### Original, trial 3

Complete input (`./inputs/original.json`) · Raw output (`./original-3/run/output.json`)

1. A CEO holding calls for all employees.
2. A CEO answering questions at the end of calls for all employees.
3. Employees being able to submit questions to their CEO through an anonymous chat.
4. A CEO repeatedly inviting employees to ask him difficult questions.
5. An employee responding to a CEO’s invitation to ask difficult questions by asking whether the CEO’s wife knew what he was up to.
   - Unresolved: Clipped-question paraphrase: prior unresolved boundary retained.
6. An employee questioning a CEO about his private conduct in a workplace question-and-answer session.
7. An employee challenging a CEO’s willingness to answer difficult questions by asking a personal question about his wife’s awareness of his conduct.
8. The insinuation that a CEO is engaging in conduct concealed from his wife.
9. The insinuation of marital infidelity in an employee’s question about whether a CEO’s wife knows what he is up to.
   - Unresolved: Marital infidelity insinuation: prior unresolved boundary retained.
10. An account of an employee’s provocative question to a CEO being treated as a development that changes a commentator’s entire thesis.
11. A commentator reporting that they have tracked the situation described in the post for months.
   - Review: Specific target item does not identify the CEO-related matter.
12. A commentator describing the trajectory of the situation they have been tracking as undeniable.
   - Review: Specific target item does not identify the CEO-related matter.
13. A commentator describing underlying fundamentals as aligning in a way that is difficult to ignore.
   - Review: Specific target item does not identify the CEO-related matter.
14. The use of financial or investment-analysis language to discuss an anecdote about an employee asking a CEO a provocative personal question.
15. A rhetorically exaggerated treatment of a workplace anecdote as a consequential development in a months-long analysis.
   - Unresolved: Broad rhetorical subject versus omitted event context: independent reviewer accepted it; prior review rejected comparable wording. Kept unresolved here, outside the predeclared four-meaning contrast.

### Edited, trial 1

Complete input (`./inputs/explicit.json`) · Raw output (`./explicit-1/run/output.json`)

1. A CEO holds calls for all employees.
2. A CEO takes questions at the end of calls for all employees.
3. Employees can submit questions to a CEO through an anonymous chat during calls for all employees.
4. A CEO repeatedly invites employees to ask him difficult questions.
5. An employee responds to a CEO's invitation to ask difficult questions by asking whether the CEO's wife knows what he is up to.
   - Unresolved: Clipped-question paraphrase: prior unresolved boundary retained.
6. An employee questions a CEO about his wife's awareness of his activities in a workplace question-and-answer setting.
7. An employee's question insinuates that a CEO is engaging in activities his wife may not know about.
8. An employee's question about a CEO's wife's knowledge of his activities functions as a personally uncomfortable question rather than a difficult business question.
9. A CEO's invitation to ask difficult questions is turned into an opportunity to confront him about his private life.
10. The quoted account of an employee questioning a CEO about his wife's knowledge of his activities is presented as a development in an ongoing matter concerning the CEO.
11. A commentator says a development concerning a CEO changes the commentator's entire thesis about the matter.
12. A commentator says they have been tracking a matter concerning a CEO for months.
13. A commentator describes the trajectory of a matter concerning a CEO as undeniable.
14. A commentator says the fundamentals of a matter concerning a CEO are aligning in a way that is hard to ignore.
15. A commentator portrays a matter concerning a CEO as an unfolding situation with a discernible trajectory and increasingly aligned underlying factors.
16. A commentator uses the language of investment analysis, including a thesis, trajectory, and fundamentals, to discuss a matter concerning a CEO.
17. An anecdote about an employee's provocative personal question to a CEO receives an elaborate, rhetorically serious analytical response.

### Edited, trial 2

Complete input (`./inputs/explicit.json`) · Raw output (`./explicit-2/run/output.json`)

1. A CEO holds calls for all employees.
2. A CEO answers questions at the end of all-employee calls.
3. Employees can submit questions to a CEO through an anonymous chat during all-employee calls.
4. A CEO repeatedly invites employees to ask difficult questions.
5. An employee responds to a CEO's invitation for difficult questions by asking whether the CEO's wife knows what the CEO is up to.
   - Unresolved: Clipped-question paraphrase: retained as unresolved under the prior review boundary; not the target of this diagnostic.
6. A CEO's wife's awareness of the CEO's activities.
7. An employee's question insinuating that a CEO is engaged in activities concealed from the CEO's wife.
8. An employee's question insinuating marital misconduct by a CEO.
   - Unresolved: Marital misconduct is a plausible insinuation, but the prior experiment kept the strength of this reading unresolved.
9. An employee challenging a CEO about personal conduct in a workplace question-and-answer session.
10. The tension between a CEO's invitation for hard questions and an employee's personally intrusive response.
11. A commentator saying that a development concerning a CEO changes the commentator's entire thesis about the matter.
12. A commentator claiming to have tracked a matter concerning a CEO for months.
13. A commentator asserting that the trajectory of a matter concerning a CEO is undeniable.
14. A commentator asserting that the fundamentals of a matter concerning a CEO are aligning in a way that is hard to ignore.
15. The use of investment-analysis language to discuss a personal controversy concerning a CEO.
16. A humorous portrayal of workplace gossip about a CEO as a subject of sustained, consequential analysis.

### Edited, trial 3

Complete input (`./inputs/explicit.json`) · Raw output (`./explicit-3/run/output.json`)

1. A CEO holds calls for all employees.
2. A CEO answers employee questions at the end of all-employee calls.
3. Employees can submit questions to a CEO through an anonymous chat during all-employee calls.
4. A CEO repeatedly invites employees to ask him difficult questions.
5. An employee responds to a CEO’s invitation to ask difficult questions by asking whether his wife knows what he is up to.
   - Unresolved: Clipped-question paraphrase: prior unresolved boundary retained.
6. An employee uses a workplace question session to confront a CEO about his private conduct.
7. An employee’s question insinuates that a CEO is engaged in conduct his wife may not know about.
8. An employee’s question insinuates possible marital infidelity by a CEO.
   - Unresolved: Marital infidelity insinuation: prior unresolved boundary retained.
9. The contrast between a CEO’s invitation to ask difficult questions and an employee’s personally challenging question about what his wife knows.
10. A commentator says a development concerning a CEO changes the commentator’s entire thesis about the CEO-related matter.
11. A commentator says they have been tracking a matter concerning a CEO for months.
12. A commentator describes the trajectory of a matter concerning a CEO as undeniable.
13. A commentator says the fundamentals of a matter concerning a CEO are aligning in a way that is hard to ignore.
14. A CEO-related anecdote is framed using the language of investment analysis, including a thesis, a trajectory, and fundamentals.
15. Mock-serious analysis of a matter concerning a CEO as though it were a major investment development.

## Review and execution notes

The main assistant and an independent reviewer read all 94 subjects with the full condition-specific source. They agree on the four-meaning comparison. Trial labels were hidden from the independent reviewer; the input edit was visible, so the conditions were not blinded.

The independent reviewer accepted the clipped-question paraphrases and infidelity insinuations as plausible. The main review retains the earlier uncertainty rather than declaring these old disputes solved. Two broad rhetorical subjects also remain unresolved because earlier reviews treated comparable wording more strictly. None changes the target result. Original trial 2 additionally generated commentary about source clipping; the main review counts that as an error under the unchanged rule against such commentary.

Six calls completed in 29.217 seconds from first admission to observed completion. All had fresh thread IDs and workdirs, the frozen prompt/settings, and no recorded tool/web events or fast override. Independent artifact checks passed. Recorded usage: 15,435 input tokens (1,920 cached), 2,273 output tokens including 544 reasoning tokens. Cache use does not mean conversation reuse; provider internals are not independently observable.

Minimum sampled available memory was 106.77 GiB; sampled memory and I/O pressure stayed zero. Polling targeted five seconds, with a maximum observed gap of 8.606 seconds during admission/status collection. No new paid API or rental was used; no cost in subscription credits was measured.

[Predeclared plan](./proposal.json) · Main review (`./review.json`) · Independent review (`./independent-review.json`) · Assessment (`./assessment.json`) · Artifact checks (`./verification.json`) · Runtime (`./runtime.json`)

Method reference: [OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices#single-turn-model-interactions), distinguishing input/instruction behavior from output correctness. The findings above come from this experiment, not from the guidance.

See [conversion gaps](../../../docs/experiments/publication-gaps.csv) for `collection:tracked-subject-prompt-goal-v1`.
