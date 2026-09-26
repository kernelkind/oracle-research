# General model runner

[run-model.sh](run-model.sh) sends one caller-supplied prompt through pi-ai.
It replaces the removed `codex_exec.py` execution tool. No subject, mask, title,
corpus, or model is selected for you.

Use this transport for standalone model calls. For prompt experiments, start with
[the shared experiment workflow](#prompt-experiments-one-supported-workflow).
The [extraction pipeline](extraction_pipeline.py)
and [frozen comparison adapter](frontier_runner/runner.mjs) are callers of the
same transport, not separate model-execution implementations.

For offline prompt revisions, run `experiment.py revise --help`.
It documents exact edits against a baseline hash, preservation and refusal checks,
diff-only output, and the automatically generated revision receipt. It makes no
model calls; revision instructions are kept in that command's help.

## Offline preview

Examples use this checkout's location; the tool itself has no fixed working
directory. This command reads no credentials and cannot send a model request:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./sse_multivector/run-model.sh preview <<'JSON'
{"provider":"openai-codex","model":"gpt-6-astra","reasoning":"low","prompt":"Describe the relationship between bread and sourdough."}
JSON
```

The JSON can also come from an existing file:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./sse_multivector/run-model.sh preview /absolute/path/request.json
```

Preview uses the actual SDK serializer with fabricated credentials and an
intercepted HTTP request. It prints the decoded request body and redacted headers,
not an approximation of the API input. It cannot establish server acceptance or
reveal hidden provider-side instructions.

`openai-codex` also accepts the exact model ID `gpt-6-sol`. Its metadata is
explicitly supplied because pi-ai 0.85.1 predates this model; it is not an alias
for GPT-5.6 Sol. Supported efforts are `low`, `medium`, `high`, `xhigh`, `max`,
and `off` (sent as `none`); `provider-default` omits the preference. `minimal`
is rejected rather than silently mapped. The existing subscription credential
service and output-cap restrictions are unchanged, with no paid API fallback.
Model limits and reference pricing come from the official
[model page](https://developers.openai.com/api/docs/models/gpt-6-sol) and
[release entry](https://developers.openai.com/api/docs/changelog#sep-22),
checked September 24, 2026. Catalog cost estimates are not subscription bills.

## Request

The exact subscription model `gpt-6-luna` is also supplied explicitly for the
pinned SDK. It accepts `off`, `low`, `medium`, `high`, `xhigh`, `max`, and
`provider-default`, but not `minimal`. See the official
[Luna model page](https://developers.openai.com/api/docs/models/gpt-6-luna).
Its API reference cost metadata is not a subscription-capacity estimate;
the teacher comparison uses the subscription route with no paid API fallback.

Required fields:

- `provider`: `openai-codex` for subscription access, or `openrouter`.
- `model`: the exact model ID.
- `reasoning`: a supported pi-ai effort, `provider-default`, or `on`.
  `provider-default` sends no reasoning preference. `on` is OpenRouter-only
  for reasoning models and sends exactly `reasoning: {"enabled": true}`,
  without choosing an effort or thinking budget. It does not impose an output cap.
- `prompt`: the exact string to send. Whitespace and Unicode are preserved.
  Invalid Unicode is rejected rather than silently changed.

Optional fields:

- `schema`: a JSON Schema for the response. Omit it for ordinary text.
- `timeout_seconds`: integer from 1 to 3600; default 300.
- `max_output_tokens`: optional for OpenRouter. Omit it or use null to send no
  caller token cap; the runner also removes the SDK's default cap. The provider
  can still impose its own limit. Positive integers retain the explicit cap.
  Rejected for subscription calls, because that SDK transport does not enforce it.
- `debug`: OpenRouter-only object containing `echo_upstream_body: true` or
  `false`. Omit it for ordinary calls. Enabling it requests OpenRouter's upstream
  request echo and records a bounded event timeline; it changes no model settings.

Unknown fields, models, reasoning settings, and unsupported transports fail
explicitly. The pinned pi-ai catalog supplies model metadata; OpenRouter entries
using `openai-completions` are supported. Other catalog transports are not silently
rerouted. DeepSeek V4.1 Flash, Xiaomi MiMo V2.6 Pro
(`xiaomi/mimo-v2.6-pro`) and Flash (`xiaomi/mimo-v2.6-flash`) have explicit catalog
additions because the pinned SDK predates those releases. MiMo Flash accepts
`on`, `off` and `provider-default`, not unverified graded effort levels.
Offline serialization verifies the requested settings, not provider acceptance
or the amount of reasoning a provider actually performs.

Schemas are checked locally without coercion, inserted defaults, removed
properties, or remote reference fetching. Draft-07, 2019-09, and 2020-12 are
supported. OpenRouter requests set `require_parameters: true` and
`allow_fallbacks: true`, allowing another compatible provider to serve the same
model if the first provider fails. The requested model, reasoning and schema
remain unchanged; unsupported parameters are not removed or relaxed. If no
compatible provider accepts the request, it fails rather than changing format.

Saved results include response status, request/generation IDs when supplied,
and `Retry-After` when visible through the credential service. Streaming error
codes, types, messages, provider names, and OpenRouter's `error_type` and
`provider_code` classifications are retained in
`response_metadata.error` before SDK normalization. Fetch/body failures retain
their phase and bounded cause details in `response_metadata.transport_error`;
local cancellation or timeout also records `abort_reason`. These diagnostic
fields use an allowlist, redact the local credential before truncating strings,
and omit arbitrary upstream bodies, headers, and stacks.

`timing` records milliseconds since execution began for headers, first/last
body bytes, first/last JSON events, observed errors, and normal stream end, plus
byte/event counts, comment count, longest byte/event gaps, and the last non-error
event time. Null means the event was not observed. Heartbeats may advance
byte timing without advancing JSON-event timing. This records what the runner
received, not when the provider generated tokens. It adds no retries, changes no
timeouts, and cannot recover details missing from older receipts. Missing final
usage after a failure does not establish zero cost.

With upstream debugging enabled, `timing.event_trace` retains the first 256 JSON
events' times, kinds, and delta field names, not their content. Dropped entries
are counted; aggregate timings still cover the complete observed stream.
`response_metadata.upstream_requests` retains up to 16 upstream-request
summaries: selected model settings and SHA-256 fingerprints of the body, input,
prompt text, instructions, and schema when present. It does not retain arbitrary
echoed bodies, credentials, or private reasoning. OpenRouter may omit its echo;
absence is not evidence of any particular upstream setting. Debugging adds no
retry and does not bypass the credential service or require upstream keys.

## Execution and credentials

### Anvil credential service

Ordinary subscription requests automatically use the selected account's service:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./sse_multivector/run-model.sh run request.json --send
```

The runner invokes `agent-account exec pi` internally for each subscription
request. The request process reads Pi's native `models.json` and `auth.json`
from that selected view once: the loopback endpoint selects the account, and
the token authorizes the local service only. The service owns the OpenAI
credential and renewal. `--pi-config` is the internal handoff, not a required
caller option. No Pi/Codex source is patched.

The frozen comparison adapter and saved batches use the same automatic route.
Set `auth_file` to null in new batch configs. `--auth-file` is rejected
with a migration message; no provider credential file is read or bearer exported.
Missing launcher or invalid/nonlocal configuration fails without falling back
to upstream access or paid OpenAI API billing. Preview remains credential-free.

Switching `agent-account use NAME` affects requests launched afterward, not a
running invocation. Batches start separate runner processes, so requests not
yet launched use the newly selected account. Existing conversations and stored
credential copies are not modified by this integration.

On 2026-09-19 the ordinary command and a saved prompt batch completed real
`gpt-6-astra` requests through the installed service. Offline checks cover the
real launcher/proxy, selection capture, both account routes, renewal, redacted
receipts, the frozen adapter, cancellation and failure without fallback.

OpenRouter also uses the local credential service through the same automatic Pi
configuration handoff. Its single shared provider key and `/openrouter/api/v1`
route do not change when the selected OpenAI subscription changes. The runner
never reads `OPENROUTER_API_KEY` or falls back to direct provider access. Anvil's
service route is active; the production runner's local configuration handoff was
verified without inference. On 2026-09-20, ten ASv6.48 Muse requests also completed
through the ordinary saved-batch launcher; their receipts and provider-reported
charges are in `frontier-model-comparison-v1/asv6.48-muse-v1/`.

The reader also accepts the native OpenRouter configuration whose `apiKey` is
exactly `$AGENT_OPENROUTER_CAPABILITY`: the launcher supplies that local capability
in the process environment, while `baseUrl` remains the validated loopback
`/openrouter/api/v1` route. This form does not read `auth.json`. Missing or malformed
capabilities, other environment references, key commands, and nonlocal endpoints
fail without falling back to stored or upstream credentials. No general-purpose
interpolation or command execution is added to the runner.

The existing literal `models.json` key plus matching `auth.json` entry remains
supported during the separate launcher rollout. OpenAI subscription configuration
is unchanged. Reader support does not mean the new launcher has been deployed.
Do not put credentials in request JSON or repository files. Returned request
headers redact the local capability. Offline checks cover both OpenRouter
configuration forms, ordinary and frozen adapter calls with the real pi-ai
transport, and refusal without fallback; no paid verification is implied.

**A send flag is not spending approval.** The [repository budget rules](../AGENTS.md)
authorize user-requested OpenRouter work roughly estimated at $1 or less without
another approval question or a provider-side cap; use a quick judgment, not a
detailed calculation. Other paid work still needs explicit spending approval,
but not a provider-enforced cap. Ledger accounting and the lifetime ceiling always apply.
Timeouts and output-token caps are not monetary hard caps.

Each call has one user message, empty application-supplied system instructions,
and no tools, history, AGENTS.md, skills, environment context, or added instruction
sentence. The model's response does not trigger tools or additional calls.
The runner makes no automatic retries, response repair, or model substitution.
OpenRouter may try multiple providers internally under the fallback policy above;
`http_attempts` counts the runner's HTTP attempts, not OpenRouter's provider attempts.

## Result

Standard output is one JSON result with:

- model, provider, effort, runner/SDK versions, and source/dependency hashes;
- exact request body, redacted headers, and provider-returned metadata when supplied;
- raw text, parsed output when a schema was requested, and structural validity;
- duration, token usage, HTTP attempts, stop reason, and errors.

A successful ordinary-text result has its text in both `raw_text` and `output`.
A schema failure preserves the raw response and returns exit status 1. Invalid
configuration, a missing launcher, or invalid local Pi configuration fails
before sending, on standard error. The credential service owns provider-token
validation and renewal; provider rejection remains a request failure.

Pi-ai's `usage.input` excludes `cacheRead` and `cacheWrite`;
`usage.output` includes reasoning. Its cost field is a catalog estimate,
not an invoice or a Codex subscription charge. Structural validity is not a
judgment of semantic correctness.

The JavaScript module [model.mjs](frontier_runner/model.mjs) also exports
`prepare`, `preview`, and `execute` for programmatic callers.
`run-model.sh --identity` prints the runner version and combined source,
dependency-lock, and launcher hash.

## Installation

The launcher uses Node 24+ when available, otherwise Nix's `nodejs_24`.
Install the pinned dependencies once:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/frontier_runner
nix shell nixpkgs#nodejs_24 --command npm ci --ignore-scripts --no-audit --no-fund
```

The SDK is pinned to pi-ai 0.85.1 in [package-lock.json](frontier_runner/package-lock.json).

## Prompt experiments: one supported workflow

Use [experiment.py](experiment.py) for saved prompt experiments. It owns input
rendering, batching, receipts, request reuse, comparisons, usage, revision diffs
and review exports. Do not write per-case configs, orchestrate waves, add inline
collection scripts, total usage by hand, or hand-edit review JSON.

Only `run` performs inference. `prepare`, `show`, `revise` and `review` do
not call a model. Preparation checks the local runner identity, not credentials
or provider acceptance. User approval and the repository spending rules still
apply before `run`; preparing an experiment does not authorize spending.

The general `run-model.sh` transport remains available to non-experiment callers.
Production extraction `extraction_pipeline.py run` / `subjects` and
`claim_exec.py` retain their separate extraction contracts. The former public
`extraction_pipeline.py prompt CONFIG`, `masks` and `revise-prompt` paths are
retired. Their reusable execution/validation functions are shared internally;
historical receipts and data are not deleted or rewritten.

### First experiment

Create one reusable spec with an explicitly versioned prompt. Paths in the spec
resolve relative to that spec. Model/provider/settings are choices, not defaults
selected by the experiment tool. This example spec is illustrative, not an
instruction to run this model:

```json
{
  "schema_version": 1,
  "prompt": {"id": "P1", "path": "prompts/P1.txt"},
  "dataset": {"adapter": "generic", "path": "cases.json"},
  "runner": {
    "provider": "openai-codex",
    "auth_file": null,
    "model": "gpt-6-astra",
    "reasoning_effort": "low",
    "concurrency": 4
  }
}
```

The optional `runner_binary` defaults to this repository's `run-model.sh`.
Use `provider: "openrouter"` and an explicitly chosen model for OpenRouter.
Set `reasoning_effort: "on"` (CLI: `--reasoning-effort on`) to request thinking
without selecting a graded effort. This uses the same transport setting above.
The transport's credential rules apply. Optional `timeout_seconds`,
`max_output_tokens` and `output_schema` are forwarded unchanged; schema property
order is preserved. Subscription transport does not accept an output-token cap.

Generic input data:

```json
{
  "cases": [
    {
      "id": "post-1",
      "inputs": {"POST": "Tea helps."},
      "evidence": {"review_context": "Not sent to the model."}
    }
  ]
}
```

P1's template contains `{POST}`. Any UPPER_CASE variable name is supported;
all supplied variables must occur in the template and all placeholders must
have values. Literal JSON braces are untouched. Substitution is single-pass:
a placeholder-looking string inside a post is never substituted again.
`evidence` is saved only for review, never implicitly appended to the prompt.

Save the spec at `experiment-spec.json`, then prepare:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py prepare experiments/E1 \
  --spec experiment-spec.json
```

Preparation prints the exact case/call count and current reuse availability,
saves the template/inputs/settings, and makes **zero model calls**. Inspect one
case before obtaining inference authorization:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py show experiments/E1 --case post-1
```

After authorization:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py run experiments/E1
```

No collect step is needed. Raw receipts and outputs are in `run/`;
`report.json` contains every case, validation, usage and comparison.
`show` re-reads the receipts rather than trusting a stale report, including
during incomplete runs. Default output is a compact case/status list;
`--case ID` shows the exact model input, output, baseline, validation and
review evidence. `--json` provides machine-readable output.

Experiment directories are **generated artifacts**, with a local `.gitignore`
ignoring their contents from the outset. Keep reusable prompts, specs, tests and
maintained documentation **outside** these directories. Do not force-add
experiment artifacts to Git.

### Next version and independent trials

`--from` names an existing experiment directory, not a prompt file. It inherits
its cases, evidence and settings; its current saved outputs become a frozen
comparison baseline. It never reruns that baseline:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py prepare experiments/E2 \
  --from experiments/E1 --prompt prompts/P2.txt --prompt-id P2
```

Optional `--model`, `--reasoning-effort`, `--provider`, `--concurrency` and
`--max-output-tokens` override only the stated settings during preparation.
Add `--only CASE_ID` once per case to prepare a subset, without copying inputs
or rerunning the baseline. Only selected cases and their matching saved baseline
entries are frozen; all other cases remain in the source experiment. Unknown
IDs are refused, and exact-request reuse remains enabled. This selection also
works with `--spec`, but not historical `--import-config`.
To change input content or other settings, prepare from a new spec and use
`--baseline experiments/E1`. Case IDs **and actual template-variable values**
must agree before outputs are paired. Same-ID/different-input cases are reported
as `input_mismatch`, not silently compared. Baseline-only case IDs are retained
in the report. Text changes are never reported as semantic improvement.

`run` executes the frozen setup, not subsequently edited source files.
Editing a frozen config, manifest or model transport is refused. Prepare a new
directory for different inputs/settings. After inspecting an approved workflow
code change, `run --runner-upgrade-reason "..."` records the old/new code hashes
and the saved-result prefix hash without rewriting the original plan or receipts.
Engine changes also use the existing `runner-upgrades.jsonl` provenance ledger.
Without that explicit reason, changed workflow code still refuses to run.

The shared prompt executor fills available concurrency slots independently; a
slow or failed case does not hold later cases behind a batch barrier. Only an
explicit temporary provider error (HTTP/stream error code 408, 429, 500, 502,
503 or 504) qualifies for automatic retry. Each case has at most two total
attempts across resumes, with a two-second minimum delay. `Retry-After` is
honored; invalid values or waits above 60 seconds leave the case unresolved
rather than retrying early. Local aborts override provider metadata. Our own
timeouts, validation/parsing errors and unknown transport failures are never
retried. Malformed completed output is retained, not repaired. The experiment
CLI no longer offers a blanket `--retry-failed` override.

Provider authentication, credit/permission or endpoint errors (401, 402, 403,
404) stop new scheduling, as do preflight/provenance errors or exhausted attempt
allowances. Already-running calls retain their receipts. Other failures remain
visible while independent cases continue; a partial run exits nonzero. Resuming
preserves completed answers and skips ineligible/exhausted failures.

`run --max-new-attempts N` caps newly sent calls, including retries, without
counting reuse. Without this optional tighter bound, the two-total-attempts rule
still applies to every case. Reserve spending for the full allowed attempt
count before running, including potentially billed failures; an attempt cap is
not a provider-side dollar cap. Each attempt retains its native receipt and
usage evidence. `show --case ID` identifies the failed case's `failure_kind`.
A lock prevents simultaneous runs of one experiment. Dependent production
extraction stages and the single-call transport retain their own contracts;
this policy applies to the shared independent prompt-batch executor.

For an independent repetition, prepare a new directory with `--repeat`:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py prepare experiments/E1-repeat \
  --from experiments/E1 --repeat
```

This disables cross-run reuse for that trial; resuming it still preserves its
own successful calls. For three repetitions, prepare three such directories.
Without `--repeat`, successful matching requests may be reused, including
historical pi-ai runs. Reuse is not another sample.

History defaults to the first experiment's parent directory and is inherited by
`--from`; use
`--history-root DIRECTORY` to share history with older runs elsewhere.
The request key includes full rendered text, provider, model, reasoning, schema
including property order, token cap, timeout and transport identity. Labels and
case IDs do not determine reuse. Original receipts remain necessary and are
verified; corrupt matching evidence stops execution instead of silently spending
again. Reused results contribute zero new attempts or usage. Reported costs are
catalog estimates, not invoices; missing usage is explicit. Reasoning tokens
are already included in output tokens.

### Title, mask and prominence preparation

The core workflow is task-independent. Optional adapters use the existing
production preparation and decoding functions:

- `dataset.adapter: "titles"`: `path` points to source packets with
  `packets[].packet` and `instances[]` (instance/vector/post IDs, original text,
  UTF-8 byte spans, fragments). Optional `select` lists exact packet IDs.
  The adapter verifies spans, deduplicates identical same-post masks, retains
  provenance and renders `{NUMBERED_INSTANCES}`. **Only the quoted masks go to
  the model.** Full posts and IDs remain review evidence. Expected output:
  `{"title":"..."}`.
- `dataset.adapter: "masks"`: `path` points to
  `{"schema_version":1,"notes":[{"note_id":"...","text":"...","subjects":[...]}]}`.
  Optional `select` lists exact post IDs. Each subject becomes a case; the
  preview reports both post and call counts. Subjects may be strings or objects
  using `subject` or `text`. Diagnostic context/heading numbers are not sent.
  Case IDs derive from post ID and subject, not batch order.
  Templates require `{POST}`, `{SUBJECT}`, and (for the default
  `mask_format: "word_positions"`) `{INDEXED_POST}`.
  Legacy `mask_format: "fragments"` is available for historical comparisons.
- `dataset.adapter: "prominence"`: `path` points to a `cases` array, with one
  saved mask per case. Optional `select` lists case IDs. Each case contains
  `id`, `node_id`, `node_title`, `note_id`, `text` (the complete original post),
  `mask_ids` (including aliases), and `byte_spans` (ordered, nonoverlapping
  UTF-8 byte offsets, end exclusive). For example:

  ```json
  {"cases":[{"id":"tea-V1","node_id":"tea","node_title":"Tea",
    "note_id":"N1","text":"I want tea.","mask_ids":["V1"],
    "byte_spans":[[7,10]]}]}
  ```

  The adapter verifies offsets and constructs `{INPUT_JSON}` containing only
  `mask` (fragment strings) and `marked_post` (the full post with `⟦…⟧` around
  each fragment of this one mask). Node titles and IDs are review-only; they
  never enter the model input. Expected output is exactly
  `{"prominence":INTEGER}`, from 0 through 100. Invalid scores are reported as
  malformed, not ranked. This supports **PPv10**, unchanged and experimentally
  tested, not production-frozen; the adapter does not choose the prompt/model.

  **PPv11** is [tested experimentally](prominence-prompt-goal-v1/ppv11-draft-v1/PPv11.md),
  not production-frozen. It replaces topic-centrality scoring with an estimate
  of the post's meaning expressed by the mask; inputs and output contract are
  unchanged. `experiments/ppv11-refresh-direct-v1` compares the same 24 masks
  against saved PPv10 answers using Astra low: 24 valid outputs, 24 attempts,
  no retries or baseline calls. All scores decreased. This establishes neither
  calibrated percentages nor improved ranking; agent assessments and remaining
  calibration questions are available through `experiment.py review`. The UI
  retains every case, including the known group/title mismatch. PPv10 evidence
  remains unchanged; no new cosine comparison or production promotion was made.

  The user judged most PPv11 scores too low and agreed to three provisional
  evaluation ranges: `Sa01eaf30fd-V0586` (tea in the short desire post), **60–80**;
  `S6dde8fffb9-V0974` (coffee shops in the laptop-ban incident), **20–40**;
  and `Sa01eaf30fd-V1298` (incidental tea in the long diary), **1–5**.
  These are human calibration judgments, not mathematically derived percentages.
  [PPv13](prominence-prompt-goal-v1/ppv13-draft-v1/PPv13.md) is approved for testing
  and tested experimentally, not production-frozen. It asks for the percentage of the
  post's semantic meaning represented by the mask in context, with only the
  endpoints defined: 0 means none; 100 means all. It removes the qualitative
  scoring bands and does not use PPv12's separate importance instruction.
  PPv12 remains an untested, unapproved prior draft; prompt versions are immutable.
  The three anchors remain outside the prompt. `experiments/ppv13-refresh-direct-v1`
  used the same 24 cases and Astra low with saved PPv11 baselines: 24 valid outputs,
  24 attempts, no retries or baseline calls. The anchors scored **40**, **16** and
  **1** respectively: short-post tea still misses the agreed range, coffee-shop
  coverage is closer but below range, and incidental tea is within range. This
  does not establish overall accuracy. Agent assessments are in the comment-enabled
  review UI. Inputs, JSON output, cosine and ranking behavior remain unchanged;
  no production promotion or further inference follows from this result.

  [PPv14](prominence-prompt-goal-v1/ppv14-draft-v1/PPv14.md) is approved and tested
  experimentally, not production-frozen. Its only change from PPv13 implements
  the approved exclusion of URLs and opaque encoded identifiers from the post's
  assessed semantic meaning;
  surrounding prose about them still counts. Scoring, input and output formats
  are unchanged. PPv13 and its saved results remain unchanged.
  `experiments/ppv14-short-tea-v1` tests three masks of the same short tea post
  with Astra low, reusing the saved PPv13 tea score as a baseline without
  rerunning it. All three calls returned valid outputs; the tea-only mask still
  missed the agreed range. This post contains no URLs or encoded identifiers,
  so the new exclusion rule's effect remains untested.
  `experiments/ppv14-tea-all-combinations-v1` extends that post to all 63
  nonempty whole-word subsets, merging adjacent selections. All outputs are
  valid: 60 new Astra-low calls and three exact-request reuses, with no retries.
  The shared prominence UI exposes every mask and separate agent assessments;
  exhaustive coverage of this one post does not establish calibrated scores.

  [PPv15](prominence-prompt-goal-v1/ppv15-draft-v1/PPv15.md) is approved for testing
  and tested experimentally, not production-frozen. Based on PPv14, it replaces its
  topic-focused guidance with the selected meaning's role in the particular
  message and the effect of what the mask leaves unspecified. Equivalent
  meanings within the same post should receive similar scores regardless of
  word count or grammatical completeness. The definition, URL/identifier
  exclusion, scoring range and input/output contract remain unchanged. No
  examples or numerical anchors were added. Following the manual walkthrough,
  the user authorized the small contrast test: `experiments/ppv15-tea-contrasts-v1`
  (eight masks), `experiments/ppv15-warning-health-v1` (six), and
  `experiments/ppv15-roasting-contrasts-v1` (two). All 16 Astra-low subscription
  calls returned valid scores, with no retries, reused answers or baseline calls.
  Warning and health comparisons favored the meaning motivating the message;
  compact and complete central roasting sentences scored similarly. The tea
  comparison did not show the agreed substantial loss when omitting the speaker.
  Agent assessments are recorded separately through the shared review command.
  These single trials check relative ordering, not calibrated percentages or
  repeatability. PPv15 and its predecessors remain unchanged; no production
  promotion follows from these trials.

  [PPv15-D1](prominence-prompt-goal-v1/ppv15-diagnostic-v1/PPv15-D1.md) is a
  tested diagnostic-only variant. It changes only the output instruction to
  request brief `represented_meaning` and `missing_meaning` fields before the
  score. `experiments/ppv15-diagnostic-v1` uses the generic adapter for this
  three-field response, with the exact saved prominence inputs for the two
  tea masks differing only in selection of "I". The user authorized two
  independent Astra-low subscription calls: both valid, no retries or reuse.
  Neither earlier scores nor the suspected explanation entered the prompts.
  Both responses counted the speaker's desire as represented, listed only
  hotness as missing, and scored 85. This supports contextual attribution of
  the speaker in the diagnostic; it does not prove why the earlier scoring-only
  responses occurred. The output intervention and single trial per case limit
  the inference. Agent assessment is saved separately. PPv15 remains unchanged
  and PPv15-D1 is not a production replacement.

  [PPv16](prominence-prompt-goal-v1/ppv16-draft-v1/PPv16.md) remains an
  unapproved, untested prior draft; its prompt is unchanged. The user questioned
  whether its distinction between interpreting and supplying information was
  clear enough and requested a revision of the main guidance.

  [PPv17](prominence-prompt-goal-v1/ppv17-draft-v1/PPv17.md) is approved for testing
  and tested experimentally, not production-frozen. It is based directly on
  PPv15 rather than PPv16 or diagnostic PPv15-D1.
  It separates determining what the fragments jointly express and leave open
  from judging the significance of preserved and missing meaning to the post.
  The post resolves word meanings for the first judgment and supplies the
  message against which the second is made. The semantic-percentage definition,
  URL/identifier exclusion, grammar/word-count guidance, scale and score-only
  JSON output are unchanged. No examples, fixed weights or diagnostic fields
  were added. The user authorized four new Astra-low subscription calls total,
  including retries: `experiments/ppv17-tea-contrast-v1` and
  `experiments/ppv17-roasting-contrast-v1`, each capped at two attempts. All four
  outputs were valid, with no retries or reuse and no baseline reruns. The tea
  contrast still lacks the intended loss for omitting the speaker: without
  "I" scored 90 and with "I" scored 85, versus saved PPv15 scores of 90 and 88.
  Compact/complete roasting scored 93/92, preserving approximate equivalence
  (saved PPv15: 92/90). Agent assessments are saved separately. These single
  trials do not establish calibrated percentages, repeatability or the cause
  of the tea result. PPv17 was not edited after testing; the four-call allowance
  is exhausted.

  [PPv17-D1](prominence-prompt-goal-v1/ppv17-diagnostic-v1/PPv17-D1.md) is a
  tested diagnostic-only variant with the same output extension as PPv15-D1;
  PPv17's scoring instructions are unchanged. In the separately authorized
  `experiments/ppv17-named-person-v1`, two Astra-low subscription calls compared
  masks including and omitting "Maya" in "Maya wants some hot tea too." Both
  outputs were valid, with no retries, reuse or baseline calls. The omitted-name
  mask scored 70 and explicitly listed Maya as missing; selecting Maya scored
  88 and represented her desire. This weakens a blanket context-restoration
  explanation but does not establish why the first-person case behaved
  differently. The earlier first-person diagnostic used PPv15-D1, so comparing
  explanations across the two probes also changes the scoring prompt. The
  proposed next check is the saved first-person pair under PPv17-D1 (two calls,
  not yet authorized), before another scoring-prompt edit. Agent assessment is
  recorded separately; numeric calibration and repeatability remain open.

  Alternatively, `path` may point to a saved title experiment's `report.json`
  (`adapter: "titles"` in that report). In this form, `select` names node IDs.
  Each selected title must be valid. Its original packet supplies all member
  masks and complete posts, with the same exact-span validation and same-post
  deduplication as title preparation. No membership expansion, title merging or
  title inference occurs. The report is hashed as an input and its contents are
  frozen into the prominence experiment; refresh the source report first if its
  upstream run has changed. Other unselected invalid title cases are ignored.

The mask decoder validates bounds, source text, ordering, overlap, within-word
uniqueness and the response contract. A valid empty mask is `empty`, not a
failure. Reports distinguish `valid`, `empty`, `malformed`, `invalid_receipt`,
`failed` and `unrun`. Mechanical validity is not semantic approval.

The frozen subject-mask baseline remains MPv3.43, identified in
[mask-prompt-versions.json](mask-prompt-versions.json). This infrastructure does
not choose, edit or promote prompts or models.

### Review without hand-editing files

Inspect exact evidence using `show --case ID`. Record agent assessment separately
from an explicit user decision:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py review experiments/E1 \
  --case post-1 --role agent --verdict uncertain \
  --comment "Needs the user's decision on scope."
```

Verdicts are `accept`, `reject` or `uncertain`. Use `--role user` **only to
record a decision the user actually made**. Reviews carry input/output hashes;
neither mechanical validation nor agent assessment becomes a user approval.

For titles or masks, `review experiments/E1 --ui` exports compatible cases and
launches the existing `target/release/sse-mask-review` UI. Override its path with
`--ui-binary` if necessary. It never builds the binary or calls a model.
Title comparisons may use the same prompt version on both sides, including
model comparisons; candidate and baseline roles remain distinct. Sessions are
tied to batch contents. Mask review includes empty, failed, malformed,
invalid-receipt and unrun results. These show the complete unhighlighted note,
an explicit result status and saved result/error details, never invented spans.
An empty mask is not automatically an error; a failed request is not an empty
answer. Invalid title outputs are still listed as excluded. Generic tasks use the same
inspection/judgment CLI without a special UI.
Agent assessments appear separately from user decisions in the existing UI.
`show` reads the UI's hashed sessions, alongside CLI-recorded reviews; it does not
invent approvals. Reviews of an earlier output remain visible but are marked
`current: false` if the output changes.

For titles, masks or prominence, add `--flagged-only` to `review EXPERIMENT --ui`.
It selects current agent `reject`/`uncertain` assessments and unresolved failed,
malformed, invalid-receipt or unrun results. Empty masks require an explicit flag.
The latest current user decision takes precedence: `accept` hides the case from
this view; `reject` or `uncertain` keeps it visible. Stale assessments do not flag
new outputs. With no matches, the command reports that and opens no viewer.
This is a saved-evidence filter, not a new model judgment or an accuracy measure.
To choose specific title, mask or prominence cases without editing reviews, use
`--only CASE_ID` once per case. Unknown IDs are refused. Combined with
`--flagged-only`, only flagged cases from that selection are shown. Existing
case order and within-node score ordering are retained, not the argument order.
Title filtering exports only selected cases into a content-addressed batch,
with their masks, agent assessments and matching review bindings. Unselected
cases are not presented or assigned decisions. Malformed title outputs remain
unsupported by the title viewer and are listed in `show`/`report.json`.

Title-card navigation stays in memory rather than synchronously saving on each
arrow press. Decisions, skips and comments still save durably; Ctrl-C also saves
the current card before exiting. A crash may lose navigation since the last
save, not previously saved decisions. Queued navigation keys survive card
changes; queued decisions and comment input are discarded so they cannot apply
to a card the user has not reviewed. Other review modes keep their existing
input and persistence behavior.

Mask filtering restricts navigation in the existing viewer (`--only` case IDs)
without changing the full batch or its session fingerprint. Full and focused
views therefore share decisions, comments and resume state. Cases outside the
selection are untouched. Agent reasoning stays separate from your decisions.
Prominence filtering preserves user comments across full and focused views;
it does not infer decisions. Masks and prominence remain separate reviews, so a mask-quality
comment copied to prominence may appear in both views.

For prominence, the same `review EXPERIMENT --ui` command opens the existing
`target/release/model-output-review` viewer (override with `--ui-binary`). Each
card shows the **complete post with one mask marked inline**, its node title/ID,
post ID, all mask IDs and score. Multiple masks on one post produce multiple
cards. Nodes retain their first appearance order; within each node, valid
scores descend, ties use case-ID order without implying a quality difference.
Failed, malformed, invalid-receipt and unrun cases remain visible as **unranked**
cards after that node's scored cards, with status/errors and any saved raw output.
Nothing is dropped or assigned an invented zero. Press `i` for the exact model
prompt. Current CLI assessments/decisions and available baseline scores appear
in the separate comment pane.

Press `c` (or `e`) to add/edit **Your comment**, separately from the agent's
assessment. Enter saves immediately, Esc cancels; pasted text is supported.
Comments are stored atomically in `ui-comments.json`, under the existing review
session lock/hash protections. Each comment follows its exact case, prompt and
output across sorting, ranking displays, filtering and reopening. Changed model
evidence keeps old comments visible as stale in `show`, never attached to the new
result. Save failures leave the editor and text intact with an error message.
Comments appear in `show`/`report.json` as user comments, not verdicts; they do not
clear agent flags or imply approval/rejection. Record explicit judgments with the
same `review --case ... --role ...` CLI above. Opening or exiting never implies
approval. The general `model-output-review` binary enables this behavior with
`--comments FILE`; without that option it remains read-only.
This duplicated, mask-sorted view is solely for prominence-prompt
evaluation. It neither combines mask scores nor defines production post ranking
or deduplication. Prominence review performs no inference or automatic build.

For an offline ranking comparison, add `--cosine-comparison FILE` to prominence
`review --ui`. FILE is a saved `prominence_cosine.py` or `prominence_centroid.py`
comparison. Each scored case must match its saved node title/ID, post ID, mask
IDs, fragments and prominence; missing/stale scores are refused. Other nodes in
the comparison file are permitted. Unscored experiment cases stay visible.
The viewer compares prominence alone against one linear normalization:

`score = prominence * (cosine + 1) / 2`

Cosine's native range −1..1 maps to weight 0..1: cosine zero gives weight 0.5,
not zero. Floating-point overshoot outside −1..1 is clipped. There are no fitted
thresholds or strength settings. Press `s` to switch ordering
at the same position: **the displayed post may change**. Nodes stay grouped,
each card still shows only one mask inline, and both scores and tied ranks
are visible. Case IDs stabilize ties; they do not establish quality differences.
These settings do not change PPv10, memberships, saved outputs or production
ranking. They neither aggregate posts nor establish a calibrated relevance score.

`prominence_cosine.py prepare` accepts either the historical normalized-vector
directory or a hierarchy-refresh directory containing `vector-map.json`,
`worker-request.json` and `worker-result/`. The latter reads the original raw
vectors without re-encoding them, verifies receipt hashes and row/span identity,
and freezes their hashes. Both formats require title encoding with the same
checkpoint/settings and replay checks before `collect` emits a comparison.
This diagnostic makes no prompt calls; the shared experiment runner remains the
only prompt-experiment workflow.

### Revision: explicit approved base, full-context diff

Use a new versioned destination and the last approved prompt as the base:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py revise prompts/P1.txt prompts/P2.txt \
  --edits prompt-edits.json
```

Edits file: `{"edits":[{"old":"exact text","new":"replacement"}]}`.
The tool computes the baseline hash automatically; an optional
`base_sha256` pins an expected hash. Every old string must match exactly once
in the original; edits cannot overlap or be no-ops. Unchanged bytes are
preserved, existing destinations are never overwritten, and the prompt and
`.revision.json` receipt are published together. Standard output is **only the
full-context unified diff**, suitable for piping to delta. No model calls occur.

### Importing existing results

A historical run requires a spec identifying its original template, actual
inputs and settings. Then:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py prepare experiments/imported-baseline \
  --spec baseline-spec.json --import-config path/to/saved-config.json
```

Import verifies the rendered prompts against the saved config and manifest and
validates successful receipts. Every saved job must map exactly once; it does
not reverse-engineer input variables from arbitrary rendered strings. Imported
experiments are read-only, reference the old results, and cannot be run. Use
`prepare --from experiments/imported-baseline` for a new candidate. The
original saved files must remain available.

Pre-pi Codex formats remain readable through
[generation_history.py](generation_history.py), not importable as native pi-ai
receipts. Old per-call preparation scripts and archived job commands are not
supported new-experiment entry points; use the workflow above. Their collectors
remain for historical evidence. The frozen comparison launcher remains a
separate frozen extraction adapter, not a general prompt-experiment interface.

### Offline verification and extension

Run the CLI and engine regression tests without credentials or inference:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 -m unittest sse_multivector.test_experiment \
  sse_multivector.test_prompt_revision \
  sse_multivector.test_extraction_pipeline \
  sse_multivector.test_category_title_inputs
```

Add task-specific preparation/validation in
[experiment_inputs.py](experiment_inputs.py) only when generic variables and
optional schema are insufficient. Keep rendering/review evidence separate.
Reuse the shared executor and receipts; do not add a second execution path or
an experiment-specific report script. Tests must exercise the actual CLI and
production engine using offline transport fixtures.
