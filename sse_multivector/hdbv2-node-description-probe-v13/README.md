# Node-title prompt v13

Both art calls returned Art; both wine calls returned Wine. All twelve outputs are acceptable under assistant assessment on this six-group test. No title describes the inputs as keywords, hashtags, or mentions.

V13 changes only the opening of v12 to request a category title for subject matter. The approved text is preserved in [prompt.txt](prompt.txt); the earlier two-sentence v13 proposal was not run. V13 is a candidate, not frozen.

| Group | Trial 1, exact response | Trial 2, exact response |
| --- | --- | --- |
| Art | Art | Art |
| Coffee-shop music | Music Playing at a Coffee Shop | Music Playing in a Coffee Shop |
| Wine | Wine | Wine |
| Coffee preparation | Coffee Bean Preparation | Coffee Bean Preparation and Processing |
| Sea-salt foods | Foods featuring sea salt as an ingredient or seasoning | Foods featuring sea salt |
| Weekend wishes | Weekend Day Well-Wishes | Saturday and Sunday Well-Wishes |

Art and Wine are broad for a reason: individual masks do not support a narrower category. That is consistent with the intended per-instance requirement, not a regression by itself. The other four groups retain useful context. Some wording remains redundant or lengthy, but I see no material membership error.

Both v12 trials, both current trials, complete masks, and reasoning are in [comparison.json](comparison.json). Full original notes and exact mask byte ranges remain in [source-packets.json](source-packets.json), for provenance only; generation received the numbered masks, not the full notes.

Optional inspection in the existing review tool:

```sh
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/hdbv2-node-description-probe-v13/run-review.sh
```

This opens all twelve outputs with masks and separate assistant comments. It is not a request to adjudicate twelve uncertainties. No user decisions were prefilled.

Execution: twelve fresh isolated Sol-low calls, two per group, maximum three concurrent; same CLI, wrapper, inputs, grouping, and ordering as v12. No schema, examples, extra prompt text, expected titles, tools, retries, or prior conversation. Exact raw outputs and token usage are saved per call.

Usage: 21,554 input tokens and 1,643 output tokens, including 1,523 reasoning tokens; zero cached input. Existing subscription only; no new API billing or paid compute.

These are six reused development groups, not a holdout accuracy estimate. Historical v12 results are not fresh controls, so the comparison does not isolate causation. Two successful calls per group do not establish general reliability. The next useful step is a small diverse new-group test with v13 unchanged, not another speculative prompt edit. That next test has not been run.
