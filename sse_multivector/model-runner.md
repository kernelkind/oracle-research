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

## Lower execution concurrency

`experiment.py run EXPERIMENT --max-concurrency N` caps live requests below the
prepared concurrency without changing prompts, provider/model settings or frozen
files. Each execution saves actual concurrency and the prepared limit in
`execution-settings.jsonl`; `show --json` includes these receipts. Existing valid
answers are reused and failed-attempt/retry rules remain enforced. A cap cannot
exceed the prepared limit. Bounded hierarchy builds keep their frozen settings.

## Offline corpus post samples

`experiment.py count-post-tokens SOURCE --tokenizer DIRECTORY --output RECEIPT`
counts complete original texts with the SSE tokenizer, special tokens included,
without truncation. `freeze-post-sample DEST --spec CONFIG --preview` saves pending
agent English/form reviews in corpus hash order. `review-post-sample SOURCE
--output REVIEWS --accept ORDINALS --reject ORDINALS --forms FORM:ORDINALS
--reason TEXT` saves explicit decisions bound to source, text and author. Ordinals
are one-based source positions; comma lists and inclusive ranges are supported.
These commands make no model calls.

`freeze-post-sample DEST --spec CONFIG` requires every selected post to have a
source-bound review. Config names candidates, token_counts, prior_review, reviews,
development_sources, seed, and train/validation/test counts under splits. It
preserves original text and authors, rejects source/token/review mismatches,
filters root/quote/reference/language/length failures, removes repeated templates
and near copies, and chooses exact-size complete author groups. Known development
IDs, authors and templates stay out of holdouts. Writing-form coverage is reported
without quotas. Final notes, original events, split references, hashes and a
selection manifest are published together. Missing reviews/counts fail before
publication. Native `prepare` accepts the saved notes or split source references.

`export-corpus-post-sample CONFIG OUTPUT` is the bounded Rust corpus reader:
it validates the frozen ID-order checksum, chooses lowest domain-separated hashes,
opens sealed NostrDB read-only without reader-table writes, exports original
events with verified canonical IDs, and uses the production English classifier
when configured. Run under its own user scope for per-process I/O pressure control.

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

`openai-codex` also accepts the exact model ID `gpt-6.1-sol`, with explicit
metadata for the pinned SDK. It supports `low`, `medium`, `high`, `xhigh`, `max`,
and `provider-default`; `off` and `minimal` are rejected. The subscription route
and no-output-cap contract are unchanged. Reference API pricing is $2/M input,
$0.10/M cached input, and $10/M output for short-context Standard requests;
these rates are not subscription charges or measured quota use. Metadata was
checked against the official [model page](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
and [pricing](https://developers.openai.com/api/docs/pricing) on September 29, 2026.

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

- `transport`: `sse` (default) or `websocket`. WebSocket is subscription-only:
  one connection and one `response.create` frame, with no reconnect, continuation
  or SSE fallback. It uses the same credential-proxy route and SDK serializer
  and answer parser. The frame omits `stream` and `background`; model, prompt,
  schema and reasoning are unchanged. See the official
  [Responses WebSocket protocol](https://developers.openai.com/api/docs/guides/websocket-mode).
- `schema`: a JSON Schema for the response. Omit it for ordinary text.
- `timeout_seconds`: integer from 1 to 3600; default 300. This is the overall
  request deadline, including streaming. Chat streams have no separate body-idle
  cutoff: silence between chunks does not cancel a request before this deadline.
- `max_output_tokens`: optional for OpenRouter. Omit it or use null to send no
  caller token cap; the runner also removes the SDK's default cap. The provider
  can still impose its own limit. Positive integers retain the explicit cap.
  Rejected for subscription calls, because that SDK transport does not enforce it.
- `debug`: OpenRouter-only object containing `echo_upstream_body: true` or
  `false`. Omit it for ordinary calls. Enabling it requests OpenRouter's upstream
  request echo and records a bounded event timeline; it changes no model settings.

### Jev / System One

`typesafe/jev-1.13` uses OpenRouter's `/api/v1/systemone` endpoint, not chat
completions. The shared runner implements this non-streaming transport directly
because the pinned pi-ai SDK has no System One transport. It still uses the
same local credential service, request identity, experiment workflow, and
single-attempt receipts. There is no upstream credential fallback or redirect.

For this model, `prompt` must be a JSON-encoded object containing exactly
`state` and `questions`, using the [System One request format](https://openrouter.ai/docs/guides/community/typesafe-sdk).
No model ID belongs inside that object; the caller's `model` setting supplies it.
Each question has `type`, `instructions` and, when applicable, `criteria`.
Choice supports up to 255 named options; Noul returns a yes probability; Score
uses 2–10 ordered levels. Multiple questions may share one state. This is a
general interface, not restricted to hierarchy comparisons.

Use `reasoning: "provider-default"`; output caps and chat debug settings are
unsupported. Optional `schema` validates the returned answers locally, not on
the wire. `output` contains the native answers, including probabilities and
confidence; `raw_text` is their JSON serialization, not generated prose.
Cross-run reuse recovers the local schema from the saved source runner config
and checks it against the immutable receipt hash; no schema is invented from
the schema-free System One wire body. Preserve the source config with receipts.
`raw_response` preserves the response body, with local credentials redacted.
Native billing stays in `response_metadata.usage.cost`; the experiment report
separately totals `provider_reported_cost_usd`, reporting null if any attempted
call lacks a charge. It does not relabel native charges as catalog estimates.

The normal generic adapter can render a JSON prompt template. Its substitutions
are literal, not JSON-escaped: check that each rendered prompt parses and retains
the exact state values before sending. Programmatic callers should serialize
their complete state/questions object using a JSON serializer.
NSP-Jev-v1 uses this interface for the approved 20-case comparison; it does not
replace the Luna-only or Astra prompts.

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

SSE diagnostics also observe a successful streaming response when `Content-Type`
is absent. Both SSE chat routes request streaming; an explicitly different
response type is still respected. The observer leaves headers and forwarded
bytes unchanged, and captures body-error causes before the SDK reduces them to
messages such as `terminated`.

WebSocket receipts record the actual GET upgrade URL, redacted headers and
`response.create` frame, not an HTTP POST. `http_status: 101` means the upgrade
succeeded. Metadata includes frame/byte counts, the terminal event and observed
close code/reason. The SDK consumes the same events through an in-process SSE
parser interface; its synthetic HTTP status is never reported as server evidence.
`timing` byte counts include that parser framing; `websocket_bytes` counts the
original message payloads. A close without a terminal event is a failure, even
if a partial answer has arrived. Successful transport does not establish answer
quality or a longer upstream request lifetime.

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

Each chat call has one user message, empty application-supplied system instructions,
and no tools, history, AGENTS.md, skills, environment context, or added instruction
sentence. The model's response does not trigger tools or additional calls.
The runner makes no automatic retries, response repair, or model substitution.
OpenRouter may try multiple providers internally under the fallback policy above;
`http_attempts` counts the runner's HTTP attempts, not OpenRouter's provider attempts.
For WebSockets it counts the single upgrade attempt; no additional model request
is made. The experiment CLI accepts `prepare --transport websocket`, freezes it
in the manifest and request identity, and cannot reuse an SSE response for it.
Omitting transport retains historical SSE request keys.

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
Undici 7.24.4 supplies a runner-owned dispatcher for both chat-streaming routes,
with its body-idle timeout disabled. The runner passes it per request; it does
not change Node's global dispatcher, model parameters, automatic retry policy,
or the non-streaming System One route. The existing overall abort deadline and
caller cancellation still apply.
Jev's separate System One transport does not pass through that SDK.

## Prompt experiments: one supported workflow

Use [experiment.py](experiment.py) for saved prompt experiments. It owns input
rendering, batching, receipts, request reuse, comparisons, usage, revision diffs
and review exports. Do not write per-case configs, orchestrate waves, add inline
collection scripts, total usage by hand, or hand-edit review JSON.

If a required capability is missing, add reusable, tested support to the shared
workflow or its input adapters before continuing. Do not work around the gap by
doing the mechanical work by hand or in a one-off script. This includes input
preparation, not just execution; see [extension rules](#offline-verification-and-extension).
If the extension exceeds the authorized task, request approval rather than
bypassing the tool.

Only `run` performs inference. `prepare`, `show`, `revise`, `review`, `collect` and
`export-hierarchy` do not call a model. Preparation checks the local runner identity, not credentials
or provider acceptance. User approval and the repository spending rules still
apply before `run`; preparing an experiment does not authorize spending.

The general `run-model.sh` transport remains available to non-experiment callers.
For OpenRouter experiments, `run --max-cost-usd N --max-request-cost-usd M`
can bound total experiment spending without imposing an output-token limit.
Both arguments are required together. The caller must verify M against the
selected provider's prices, maximum response length, and actual input bounds;
it is a reservation, not a model parameter. The runner includes prior charged
attempts, reserves M for each new in-flight call, waits when existing calls hold
the available allowance, and replaces reservations with provider-reported costs.
Exact-request reuse is free. Unknown billing retains the full per-request
reservation instead of stopping unrelated calls. Reports still show the charge
as unknown, never zero or an invented bill. On resume, unbilled attempts count
against the largest recorded per-request reservation (or the current bound,
if larger), so reducing a later bound cannot discount earlier attempts.
An actual charge exceeding the verified per-request bound still stops new calls.
The existing provider-only retry policy is unchanged. Limits are recorded
in `run/spend-limits.jsonl`. They do not replace ledger admission or authorize
spending, and responses are never truncated to fit the dollar allowance.

`experiment.py reconcile-costs EXPERIMENT` retrieves missing OpenRouter charges
through the credential service's read-only generation lookup; it performs no
inference. It saves separate `run/cost-receipts.jsonl` entries bound to each
original receipt's hash and generation ID, without rewriting outputs or usage.
Reports and resumed dollar budgets use these verified charges instead of the
worst-case reserves. Failed lookups remain unknown; repeated reconciliation
skips charges already known. Invalid IDs, negative/nonfinite charges, conflicting
billing and mismatched receipt bindings are rejected. Ledger accounting remains
the caller's responsibility. This does not change model settings or retry rules.

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

Instead of embedding `runner.output_schema`, a spec may use
`runner.output_schema_path` relative to the spec. Preparation loads and hashes
that schema source, then freezes the same schema object into the runner config.
Supplying both fields is rejected.

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

Request-history lookup is needed only when unrun cases can reuse answers.
Completed experiments and intentional repeats skip that scan, including when
opening or closing the review UI. Receipt and comment validation still run;
unfinished non-repeat experiments still check reuse normally. On the 17-mask
Coffee review, removing the unnecessary scans reduced the local `review --check`
open-and-close measurement from 2.63 seconds to 0.08 seconds. This is a startup
and exit improvement, not a change to rendering or scrolling.

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

The shared prompt executor fills available concurrency slots independently;
slow calls and local failures do not hold later cases behind a batch barrier.
Temporary provider failures pause new requests throughout the running batch,
regardless of configured concurrency. Only an explicit temporary provider error
(HTTP/stream error code 408, 429, 500, 502,
503 or 504) qualifies for automatic retry. The Codex HTTP-200 stream failure
beginning `Codex error: An error occurred while processing your request. You can
retry your request, or contact us` also qualifies, only with provider
`openai-codex` and stop reason `error`; arbitrary error prose does not.
Each case has at most two total
attempts across resumes, with a two-second minimum delay. `Retry-After` is
honored; invalid values or waits above 60 seconds leave the case unresolved
rather than retrying early. Local aborts override provider metadata. Our own
timeouts, validation/parsing errors and unknown transport failures are never
retried. Malformed completed output is retained, not repaired. The experiment
CLI no longer offers a blanket `--retry-failed` override.

Provider backoff starts at two seconds and doubles after another failure following
the wait, up to 60 seconds. Already-running failures share the current wait;
any longer valid `Retry-After` extends it, even above the internal 60-second cap
and even when the failed case has no retry left. Fresh cases and eligible retries
both wait. A new successful request sent after the wait resets the exponential
delay; saved/reused answers and calls sent before the wait do not establish
recovery. Local failures do not trigger provider backoff.

Once the shared wait expires, eligible retries run before untouched cases, ordered by
retry deadline. Already-running calls are not interrupted. Resuming also applies
the shared wait from saved transient failures, without changing retry eligibility
or the two-total-attempts limit. The backoff is internal to one batch invocation,
which uses one configured provider/credential route; it does not coordinate
separate runner processes or ordinary Codex chats.

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

For comparisons that need original generation costs, use
`experiment.py show EXPERIMENT --generation-costs --json`, optionally with
`--only CASE_ID` or `--note NOTE_ID`. This read-only view adds `generation_usage`
without changing the existing `usage` totals, which still measure new attempts
in the selected run. It verifies reused answers against their original receipts
and counts each source call once by its resolved receipt file and line number.
Duplicate answers do not count twice; distinct repeated calls do. Selected
attempts and earlier attempts needed to obtain a reused source answer remain
included, even when they failed. `sources` provides the verified receipt links;
`source_calls_added` identifies calls absent from the new-attempt total.

Missing usage, including an interrupted call with only SDK-normalized zero
counters, makes the complete generation estimate null rather than zero.
`known_catalog_cost_estimate_usd` and `known_provider_reported_cost_usd` retain
only known subtotals. Token totals likewise cover only calls with known usage.
Verified source billing reconciliations are honored without new lookups, model
calls, edits to receipts, or changes to spending reservations. These totals
include observed cache discounts, not an assumed production cache-hit rate.
Compare completion/failure counts as well as cost; a successful-output subtotal
is not the price of completing an unfinished batch or measured subscription
quota consumption.

Reuse checks share parsed manifests/configs, manifest hashes and verified runner
provenance within one operation. Source receipt files are indexed by byte offset;
each requested receipt is still read and checked against its saved hash and
invocation. This avoids rereading whole files for each comparison. Caches are
thread-safe, discarded between operations, and invalidated by changes to file
identity, size, mtime or ctime. Concurrent changes to a receipt file fall back to
reading the requested line directly. No receipt-verification result or model
answer is trusted merely because it was cached. On HR02-NMP09, the 21,756-case
read-only inspection completed in 5.5 seconds after preparation had spent over
19 minutes in repeated file reads. Request identities and reuse decisions are
unchanged; the measurement does not describe model latency.

### Saved subject-pair preparation

Use `dataset.adapter: "subject_pairs"` for comparisons between saved SP
hierarchy nodes. Its `path` names a small selection file, not a copied dataset:

```json
{
  "schema_version": 1,
  "inputs": "../saved-inputs/inputs.json",
  "hierarchy": "../saved-hierarchy/results.json",
  "pairs": [{"id": "pair-1", "A": "S0000", "B": "S0002"}]
}
```

Paths resolve relative to that selection file. `inputs` supplies the saved
`subjects`, `posts` and SP `edges`; `hierarchy` supplies `groups`,
`member_to_group` and mapped `edges`, as written by
[subject_matching_probe.py](subject_matching_probe.py). Node IDs use the
browser's `S` plus zero-padded first subject index in each group, not the group
index or title. Optional `dataset.select` names pair IDs; A/B order is retained.

The adapter builds `{INPUT_JSON}` with `A` and `B` arrays of distinct exact
`subject`/`context` pairs, in saved member order. Only identical pairs are
deduplicated; different wordings/contexts and entries with empty masks remain.
Original entries, masks, full source posts, node IDs and shared-child references
stay in review evidence. Shared-child source-post labels follow the selected
A/B order. No manual case-file generation or copying through patches is needed.

Preparation hashes the selection file and both referenced sources, checks
subject/group identities and membership, and freezes the resulting inputs and
evidence. It rejects unknown/self-pairs, duplicate pair IDs, invalid membership
or edges, and missing source posts. It does not judge semantics, select pairs,
infer relationships, modify the hierarchy or send model calls. Use the normal
prompt, model, schema, baseline and request-reuse settings.

The [BCPv4 six-pair spec](experiment_specs/lg01-bcpv4-six-pairs-astra-low-v1.json)
now uses this adapter. Offline preparation reproduced all six prior prompts
byte-for-byte and found all six saved answers reusable; no inference was run.

To prepare comparisons after combining nodes judged equivalent, replace `pairs`
with references to completed shared experiments:

```json
{
  "schema_version": 1,
  "inputs": "../saved-inputs/inputs.json",
  "hierarchy": "../saved-hierarchy/results.json",
  "comparisons": ["../comparisons/first", "../comparisons/remaining"]
}
```

The same `subject_pairs` adapter obtains receipt-validated reports through the
shared workflow. It checks source hashes, original node entries, exact inputs
and rendered prompt before using the saved five-label relation/reason answers.
Invalid or unfinished answers stop preparation; they are not re-prompted.
Only `equivalent` combines nodes, including connected chains. Every original
subject entry remains; combined groups use sorted original indices and the
existing first-subject node identity. Mapped SP ancestry must survive as
ancestor-or-equal, without a cycle. A failed check stops without repairing or
writing to the source hierarchy.

Preparation remaps only those previously compared pairs, removes self-pairs
from model jobs, and deduplicates unordered current pairs. It prepares **only
changed inputs** as new cases. For an unchanged pair it retains the saved A/B
orientation, answer, settings and receipt reference in
`plan.preparation.unchanged_comparisons`. Those are earlier judgments, not new
samples or executor-cache reuse. This avoids resending unchanged inputs when
transport identity has changed, without relaxing the executor's exact-request
reuse checks. An answer is not retained merely because node IDs match.

`plan.preparation` also freezes the combined partition, mapped SP links,
original-to-combined node mapping, equivalence answers, internal comparisons
and full selection counts. Changed cases retain their previous comparisons and
all distinct subject/context entries, original masks and full posts as evidence.
No ancestor answer is applied, no new pair is nominated, and new equivalences
from this run do not automatically trigger another combination pass.
The [HG6–HG7 spec](experiment_specs/lg01-bcpv4-combined-pairs-astra-low-v1.json)
uses this preparation on the saved LG01 data. Author source references/specs,
not copied case files; use the ordinary runner and attempt cap afterward.

### Saved subject hierarchy export

`export-hierarchy` consumes a completed combined `subject_pairs` experiment,
or completed additional `subject_pairs` comparisons with `--base` naming their
existing test export. It is an explicitly authorized, separate test, not
automatic post-run behavior.
It revalidates source hashes, receipts, model settings, the HG6 partition and
each current input. HG5 judgments are used only for unchanged inputs; changed
inputs require valid HG7 answers. Older relative source paths resolve only to
their exact hash-bound files in the frozen preparation.

The command retains every original entry, mask and SP relationship, adds the
current ancestor proposals, and derives browsing links by omitting shortcuts
already supplied through another path. All ancestry and multiple parents must
survive. Direct memberships are unchanged; recursive browsing memberships follow
the resulting graph. It does not generate titles, nominate new pairs or send calls.
Cycles, `neither`/ancestry conflicts, pending new equivalences and stale or
unfinished judgments stop export before writing; no general repair policy is selected.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py export-hierarchy \
  target/branch-comparison-v1/bcpv4-hg6-hg7-v1/experiment \
  --source sse_multivector/hierarchy-refresh-v1 \
  --output target/branch-comparison-v1/bcpv4-ancestors-replay-v1
```

For additional comparisons, their frozen hierarchy reference must be exactly
`BASE/results.json`, with the same original SP inputs, prompt and model settings.
The exporter reconstructs the base from its saved source experiments in memory,
checks all four export files against that reconstruction, retains its answers
and adds the completed new ones. First-generation exports without an explicit
replay descriptor are supported only when their protected sources identify one
unique combined experiment. New provenance records the experiment, source corpus
and base path for reproducible continuation. Duplicate compared pairs or case IDs
stop rather than choosing a replacement answer. The same joint conflict checks
apply to old and new answers; no source export or receipt is rewritten.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py export-hierarchy \
  target/branch-comparison-v1/bcpv4-food-ancestors-v1/experiment \
  --base target/branch-comparison-v1/bcpv4-ancestors-v1/run \
  --source sse_multivector/hierarchy-refresh-v1 \
  --output target/branch-comparison-v1/bcpv4-food-ancestors-replay-v1
```

The output must be fresh and outside the source/model-experiment directories.
`results.json` retains the full graph, SP links, answer-bound proposals and
separate browsing links. `provenance.json` retains source hashes, the preparation,
answers/receipts/settings, original entries/SP links and masks. `summary.json`
reports mechanical checks, not semantic accuracy; `new_ancestor_links` counts
links added relative to the supplied base, or relative to SP links for the first
export. `ancestor_answers` and `comparisons` count all retained current answers.
`categories.json` reuses the
existing browser with individual masks, IDs, full post context and empty-mask posts:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
target/infomap-review-build/debug/sse-subject-navigation \
  --categories target/branch-comparison-v1/bcpv4-food-ancestors-v1/hierarchy/categories.json \
  sse_multivector/hierarchy-refresh-v1/masked-posts.json
```

Do not enable display-collapse options. Append `--check` for noninteractive
validation. No saved LG01 output is rewritten.

### Collect subjects, masks and node descriptions into reusable inputs

`collect` is offline. It validates saved answers and receipts through the same
report loader as `show`, then writes a fresh output directory. Collection paths,
prompt versions, teacher settings and saved-answer reuse are data supplied to
`prepare`; no collection name, topic or post count is hardcoded into this path.

- Collect completed `subjects` experiments into `subjects.json`, retaining
  complete posts, IDs, source metadata, numbered SP entries and contexts. Supply
  that file to the existing `masks` or `grouped_masks` adapter.
- Collect completed `masks` (word-position format) or `grouped_masks` experiments
  into `masked-posts.json`, `vector-map.json` and, when masks are nonempty,
  `worker-request.json`. Keep every original SP entry, including valid empty MP
  masks and selected posts with no subjects. Encode exactly identical nonempty
  source-byte ranges within one post once, retaining all subject associations.
- Collect completed `node_descriptions` experiments into `node-descriptions.json`.
  Each record preserves the supplied `node_id` and `node_title` and adds a
  nonempty description of at most 1,200 characters. Duplicate nodes are rejected;
  collection does not choose between trials or generate descriptions.
- Multiple experiment paths can combine disjoint collections or complete partial
  mask batches. Reject duplicate subject answers, conflicting posts, missing
  masks, invalid receipts and changed source data. Collection does not choose
  between repeated trials or treat generated semantics as user approvals.
- Each output includes `provenance.json` with source hashes, experiment settings
  and receipts. Outputs cannot overwrite existing directories or be placed
  inside source experiments. Their generated data is ignored from the outset.

For illustrative already-completed experiment paths:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 sse_multivector/experiment.py collect \
  target/subjects-food target/subjects-music \
  --output target/combined-subjects
```

After separately authorized MP calls have completed, collection can also bind
an explicitly supplied SSE worker configuration to the new request:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 sse_multivector/experiment.py collect \
  target/music-masks \
  --output target/music-sse-inputs \
  --worker-config sse_multivector/hierarchy-refresh-v1/worker-config.json
```

The generated worker configuration preserves the supplied model, checkpoint,
runtime paths and batch settings, updating only request/output paths and the
request hash. It does not run SSE or establish compatibility with existing
vectors; verify worker/runtime provenance before later encoding or reuse.
If every mask is empty, no worker request or configuration is needed.

This replaces experiment-specific assembly for new work. The historical
`hierarchy_refresh.py` preparation and saved HRv1 artifacts remain unchanged;
its mask-to-SSE conversion uses the same reusable implementation. Older
experiments without a saved dataset path can be imported using a current spec;
collection never reruns their answers. Source hashing and input assembly add
no model calls or cross-post comparisons. Collection reads each distinct source
once and hashes each result ledger once per validation pass. Existing SP/MP
request sizes and repeated post context remain unchanged.

### Subject, title, mask and prominence preparation

The core workflow is task-independent. Optional adapters use the existing
production preparation and decoding functions:

- `dataset.adapter: "distillation_review"`: source-bound
  [DSRv1 qualification definitions](distillation-review-v1/qualification-source.json)
  select complete frozen AS examples or a saved training control. Preparation
  preserves the full task/post/teacher, applies specified candidate changes and
  supplies all exact subject matches. Expected answers remain outside the prompt.
  The report validator checks complete subject/link verdicts, teacher partitions,
  fixed requirement flags and known references before calculating correctness
  and coverage. Duplicate coverage references are checked in application code;
  the provider response schema omits unsupported `uniqueItems`.
  `show --json` includes qualification checks after saved results.
  The October 8 DSRv1 trial fails known semantic and cross-version checks despite
  complete large reports; one stream is interrupted near fifteen minutes and
  remains ungraded. All 29 cases were attempted once, with 28 complete reports;
  seven of the eight largest generations completed. The maintained specification
  uses user-directed concurrency 8 with existing backoff; the original frozen
  trial used 1. See the
  [DSRv1 qualification evidence](distillation-review-v1/README.md#october-8-qualification-evidence).
  The current specification prepares
  [DSRv2 preview](distillation-review-v1/README.md#dsrv2-draft-and-offline-preview).
  A reference may supply `teacher_meanings_from` with `experiment`, `case_id`
  and `record_sha256`. Native report validation must yield a valid review of
  the same task, post and teacher; preparation pins the receipt and protects its
  experiment/configuration/manifest/ledger hashes. Only meaning groups and
  requirement flags enter the candidate input; their receipt provenance remains
  review evidence. Shared saved groups cannot be overridden by a candidate and
  are not promoted to known gold. Q20–Q22 use provisional groups for consistency
  checks. Each report's prompt ID must match its rendered reviewer version.
  Preparing DSRv2 adds no inference or authorization for calls.
  The user subsequently authorized DSRv2 qualification in small-control then
  large-case order. Q04 passes `8/8` correctness and `2/2` coverage, with both
  meanings required; its exact receipt is reused for the small set. Seventeen
  controls pass, Q14 fails semantically, and Q01's HTTP 200 body stream closes
  with an ungraded partial report after 365.2 seconds. Qualification has failed;
  Q20–Q29 run separately at concurrency 8 without resending Q01. Native
  `show --generation-costs` counts Q04's original call once and marks Q01's final
  usage unavailable; SDK zero placeholders are not measured zero usage. See the
  [DSRv2 qualification evidence](distillation-review-v1/README.md#dsrv2-qualification-october-8).
  `show EXPERIMENT --case CASE --prompt-only` prints the exact rendered prompt.
  `score-review EXPERIMENT --case CASE --report FILE` scores a supplied report
  offline, optionally saving it with `--output FILE`. It does not create a model
  receipt or mark a case run. See the [DSRv1 preview](distillation-review-v1/README.md#offline-preparation-and-preview).
  `rank-distillation-generations MANIFEST --top 5 --output FILE` checks a frozen
  subjects-only pilot's prepared hashes and split identities, sizes every saved
  hierarchy, and returns the union of the top five training answers by entry
  count and canonical JSON UTF-8 bytes. Held-out labels contribute aggregate
  sizes only; the output contains training references without posts or subjects.
  The ranking is offline and does not prepare requests or perform inference.

- `dataset.adapter: "subjects"`: `path` points to
  `{"schema_version":1,"notes":[{"note_id":"...","text":"..."}]}`.
  It uses the `posts` adapter's `{POST}` inputs and optional case-ID `select`;
  `origin.prompt_id`, when supplied, preserves historical prompt identities.
  Other saved fields remain source evidence. Expected output is a `subjects`
  array of `number`, `context`, `subject` entries. Require unique section-style
  numbers and each parent before its children; preserve repeated subject wording
  and an empty array. No semantic repairs or prompt/model defaults are applied.
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
  Repeated identical subject entries retain separate cases with occurrence
  suffixes; they are not silently dropped. Historical mask imports can use the
  original `item_id` only when the saved prompt matches exactly.
  Templates require `{POST}`, `{SUBJECT}`, and (for the default
  `mask_format: "word_positions"`) `{INDEXED_POST}`.
  Legacy `mask_format: "fragments"` is available for historical comparisons.
- `dataset.adapter: "grouped_masks"`: the same saved-post/subject source and
  optional post-ID `select`, but one case/call per post. Templates use `{POST}`,
  `{INDEXED_POST}` and `{SUBJECTS}`; the last is a JSON array of `id`/`subject`
  entries. Context and existing masks remain evidence, never model inputs.
  Output is `{"results":[{"id":"S1","meaning":"...","expressible":true,
  "evidence":"...","mask":[[1,1]]},...]}` in input order, including empty masks.
  Missing, duplicate, foreign or reordered IDs fail validation; every mask uses
  the production position decoder. Different subjects may overlap. `show`
  includes per-subject `mask_results`, decoded spans and optional exact-span
  comparison with validated saved `byte_spans`/`fragments`. Baselines are not
  ground truth; these comparisons are mechanical, not semantic judgments.
  For read-only subset accounting, `show --only CASE_ID` or `show --note NOTE_ID`
  (repeatable) scopes cases, attempts and usage to that selection. Unknown or
  duplicate IDs fail; no calls are made and the saved experiment is unchanged.
  Cases include saved `elapsed_seconds` when available. This supports matching
  a grouped trial to the same individual-mask calls, including cache use.
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

  The adapter also accepts a saved hierarchy's `memberships.nodes` directly;
  `select` then names node IDs. Only `matched_instances` become cases, never
  recursive/descendant memberships. Original mask IDs are recovered from
  `origins`, with exact post/span identity checks; fragments are checked against
  source bytes before rendering. No hand-built intermediate case file is needed.
  With an explicit `runner.output_schema`, additional diagnostic fields such as
  PPv30's allocation are allowed under that schema. The integer prominence range
  check remains mandatory; without a schema, the single-field contract remains.
  See `experiment_specs/ppv30-eggs-node-v1.json` for a direct-hierarchy example.

  For a separate post-ordering experiment, optional `dataset.combine_masks: true`
  produces one case per node/post from the union of that node's selected masks.
  Overlapping and adjacent spans merge; gaps remain unselected. Original mask IDs
  remain in the evidence. Each original mask is validated before combination,
  and hierarchy inputs still use only direct memberships. The default remains
  one original mask per case. Unchanged rendered requests reuse saved answers;
  a different selection requires a new prominence answer. See
  `experiment_specs/ppv30-coffee-combined-masks-v1.json`.

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
  88 and represented her desire. `experiments/ppv17-first-person-diagnostic-v1`
  then tested the saved first-person pair under the same PPv17-D1 prompt and
  Astra-low settings: two valid subscription calls, no retries, reuse or
  baseline calls. Without "I", the response explicitly listed the speaker and
  hotness as missing and scored 79; with "I", it represented the speaker's
  desire and scored 85. This weakens both blanket context-restoration and
  first-person-shorthand explanations: the diagnostic recognized the omission
  but assigned it a small score difference. It does not establish why earlier
  scoring-only responses differed, calibrated percentages or repeatability.
  Agent assessments are recorded separately; PPv17 and PPv17-D1 are unchanged.
  The six-point gap alone does not establish a scoring failure: the desired
  numerical separation has not been calibrated.

  [PPv17-D2](prominence-prompt-goal-v1/ppv17-pairwise-diagnostic-v1/PPv17-D2.md)
  is a tested diagnostic-only pairwise variant derived directly from PPv17.
  It retains the meaning-assessment guidance but compares two masks without
  numerical scores, allowing a tie or uncertainty and requesting a brief
  explanation. `experiments/ppv17-pairwise-diagnostic-v1` used one valid
  Astra-low subscription call, with no retries, reuse or baseline calls. For
  "I want some hot tea too.", A retained "I want some" + "tea too." and B
  retained "want some hot tea too." The model chose B because it considered
  the speaker "naturally implicit", not because it explicitly judged temperature
  more important than a fully missing speaker. This disagrees with the intended
  comparison and shows that recognizing missing meaning remains unsettled,
  even without numerical scoring. The input contained neither the intended
  answer nor previous scores. One trial in one order does not establish
  repeatability, position independence or the cause of prior responses.
  Agent assessment is recorded separately; PPv17 remains unchanged.

  [PPv18](prominence-prompt-goal-v1/ppv18-draft-v1/PPv18.md) is an unapproved,
  untested draft. The user rejected its clarification as insufficient: telling
  the model to count unspecified information as missing does not establish
  which information the mask leaves unspecified. The approved direction is to
  reconsider interpretation around what could differ about the post's message
  while remaining compatible with the selected meaning, then assess how
  important those differences are to this particular post. This distinguishes
  what the mask leaves possible from a reader's likely reconstruction; it is
  not a blanket prohibition on interpreting idioms or references.

  [PPv21](prominence-prompt-goal-v1/ppv21-draft-v1/PPv21.md) is now the latest
  user-approved wording and the baseline for future revisions. It is tested
  experimentally, not production-frozen. It asks for alternative posts consistent
  with the mask's meaning but differing in the complete post's meaning, then assesses
  the importance of represented and missing meaning. It consistently uses
  post, mask, fragments, and meaning. The numerical scale, URL/identifier
  exclusion and score-only JSON contract remain unchanged. PPv17 and the
  intervening drafts remain immutable; approval of PPv21's wording does not
  establish improved scores or authorize a broad experiment.

  The user authorized four Astra-low subscription calls, bounded at two
  attempts each for `experiments/ppv21-tea-contrast-v1` and
  `experiments/ppv21-roasting-contrast-v1`. All four outputs were valid, with
  no retries, reuse or baseline reruns. Tea without/with "I" scored 90/87
  (saved PPv17: 90/85), still not demonstrating the intended loss from omitting
  the speaker. Compact/complete roasting scored 93/91 (saved PPv17: 93/92),
  retaining approximate equivalence. Small differences and reversals should
  not be overinterpreted from one trial per case. Score-only responses do not
  show whether alternative posts were identified or what missing meaning was
  recognized. Agent assessments are saved separately; PPv21 is unchanged and
  the four-call allowance is exhausted.

  [PPv21-D1](prominence-prompt-goal-v1/ppv21-diagnostic-v1/PPv21-D1.md) is a
  tested diagnostic-only variant. Only the output instruction changes: return
  `alternative_posts`, `missing_meaning`, and `prominence`.
  `experiments/ppv21-diagnostic-v1` reuses the exact tea inputs through the
  generic adapter and compares against saved PPv21 outputs. The user authorized
  two Astra-low subscription calls: both valid, with no retries, reuse or
  baseline reruns. Without "I", the alternatives were "I want some iced tea
  too." and "They want some hot tea too."; the response identified the speaker
  and hotness as missing and scored 75. With "I", both alternatives retained
  the speaker and changed the temperature; it identified hotness as missing
  and scored 90. This matches the intended distinction in this diagnostic
  trial, unlike saved score-only PPv21 (90/87). Output-format effects and trial
  variation remain unresolved; this is not access to prior responses' reasoning
  or evidence of calibrated percentages. Agent assessments are separate from
  user decisions. PPv21 is unchanged.

  The user clarified that the model must identify a class, not merely give
  example posts, and authorized defining it as all possible posts that
  represent everything the mask represents, while allowing whatever it leaves
  unspecified to vary. PPv21-D1's examples demonstrate recognition of
  particular missing meaning but do not establish that class.
  [PPv24](prominence-prompt-goal-v1/ppv24-draft-v1/PPv24.md) is approved for
  testing and experimentally tested, not production-frozen. It was drafted
  against PPv21. The user found PPv23's abstract class
  comparison unclear and authorized rebuilding the instruction around what
  the fragments specify and leave unspecified, then identifying what the
  complete post specifies that the mask does not. "Class" names that
  description rather than introducing the operation. PPv24 requests
  `post_class`, `missing_meaning`, and `prominence`; scoring instructions are
  unchanged. PPv22 and PPv23 remain unapproved, untested prior drafts. PPv21
  and prior versions remain unchanged.

  `experiments/ppv24-tea-contrast-v1` used two Astra-low subscription calls
  with identical saved tea inputs and PPv21-D1 as the saved baseline. Both
  responses were valid; no retries, reuse or baseline reruns occurred. The
  generic adapter validates the three diagnostic fields. Without "I", the
  class left speaker identity and temperature unspecified and scored 75;
  with "I", it retained the speaker, left temperature and quantity unspecified,
  and scored 85 (saved PPv21-D1: 75/90). These are class descriptions rather
  than example posts and recognize the intended speaker distinction. However,
  only the second response mentions the omitted vague quantity "some", and
  neither calibrated percentages nor repeatability are established. Agent
  assessments remain uncertain and separate from user decisions. The initially
  proposed roasting regression was not run: its saved source uses the
  score-only prominence adapter, which rejects diagnostic fields. Preparing
  that source directly as generic input failed before inference. No runner
  code or saved input was changed to work around that incompatibility.

  `experiments/ppv24-warning-v1` tested "Careful—the tea is hot!" with the
  single-word masks "tea" and "hot" in two Astra-low subscription calls.
  Generic diagnostic inputs were verified identical to the saved PPv15
  warning inputs before inference. Both responses were valid, with no retries,
  reuse or baseline reruns. "Tea" scored 20 and described posts referring to
  tea without its condition or a warning; "hot" scored 40 and described high
  temperature without object identity or explicit caution. This matches the
  user-endorsed ordering, but saved PPv15 already had that ordering (25/55).
  It is not evidence of improvement, calibrated percentages or repeatability.
  The user subsequently judged 30–40 reasonable for "hot", resolving the
  agent's concern about that score, and predicted about 80 for "Careful" +
  "hot". That score judgment is recorded separately as a user review, not
  general approval of PPv24 or its calibration.

  `experiments/ppv24-warning-combined-v1` tested the combined mask in one
  Astra-low subscription call without supplying the expected score to the
  model. It returned 80, with class "Posts warning someone to be careful
  because something is hot." and missing meaning "The hot thing being warned
  about is tea." The response was valid, with no retry or reuse; the hot-only
  score of 40 was read from the saved run, not rerun. This matches the user's
  prior expectation and recognizes the warning across separate fragments.
  The agent accepted this case; it does not establish general calibration or
  repeatability. PPv24 is unchanged and not production-frozen.

  `experiments/ppv24-health-v1` tested the saved health-concern post with
  "drank" + "tea" and "drank over a gallon" + "in less than 24 hours".
  Both generic diagnostic inputs were verified identical to saved PPv15
  inputs. Two Astra-low subscription calls returned valid responses without
  retries, reuse or baseline reruns. Scores were 25 and 60 (saved PPv15:
  25/55), matching the user-endorsed ordering. The first class correctly left
  drinker identity, amount, temperature, timeframe and health concern
  unspecified. The second class incorrectly specified "the author" as the
  drinker even though "I" was unselected, and did not list identity as missing.
  The agent accepted the first case and rejected the second class description;
  this does not reject its score or establish how the identity error affected
  scoring. User judgment and score calibration remain open.

  `experiments/ppv24-health-identity-repeat-v1` independently repeated only
  the quantity/timeframe case with `--repeat`, identical inputs/settings and
  one Astra-low subscription call. It returned 60 again. The class described
  consumption of more than a gallon of an unspecified drink in under 24 hours,
  without specifying an attitude; it did not identify the drinker as the
  author. The author inference therefore did not recur in this second trial.
  Missing meaning named hot tea and the health concern, without explicitly
  enumerating missing drinker identity. The response was valid, with no retry
  or request reuse. The agent accepted the revised class description; this
  does not establish general reliability, exhaustive missing-meaning reporting
  or that class-description errors cannot affect scores. PPv24 is unchanged.

  `experiments/ppv24-real-posts-v1` tested three diverse saved real-post masks
  from the earlier review: `S29074d29b6-V1524` (fragmented decaf-drinker
  motivation), `Sa01eaf30fd-V1298` (incidental tea in the long diary), and
  `S6dde8fffb9-V0974` (coffee shops in the laptop-ban incident). Generic
  inputs were mechanically copied from saved PPv13 inputs and equality was
  verified before inference. Three Astra-low subscription calls were valid,
  without retries, reuse or baseline reruns. Scores were 52/1/7 versus saved
  PPv13's 64/1/16. The decaf description combines fragments coherently but
  its absolute score has no user target. Diary tea remains in the provisional
  1–5 range, though its class adds "desired" despite only "tea" being selected.
  Coffee shops scores well below the prior provisional 20–40 range, although
  its class correctly leaves the incident, attitudes and actions unspecified.
  The initial agent assessments were uncertain for these distinct reasons.
  After reviewing the marked coffee-shop post, the user judged 7 probably
  reasonable, superseding the earlier provisional 20–40 expectation for this
  case. That acceptance is recorded separately as a user review. The other
  two cases have no new user judgment. PPv24 remains unchanged and not
  production-frozen.

  `experiments/ppv24-other-topics-v1` tested three saved masks from
  `ppv10-mixed-notes-v1/inputs.json`: M05 (cabin bathroom safety bars), M07
  (reading before bedtime in a lifestyle list), and M09 (six guitar mentions
  in a capo/retuning question). Generic inputs were mechanically copied from
  the saved input objects; no expectations were included in model inputs.
  Three Astra-low subscription calls returned valid responses without retries,
  reuse or baseline reruns. Scores were 39/4/8. The classes respectively
  represented the fall concern and installation judgment, the one reading
  recommendation, and guitars without the tuning issue. Missing meaning
  identified the surrounding daily update and older guests/shopping details,
  other advice and invitation for additions, and the detailed tuning question.
  The agent accepted all three as plausible, not as user-approved or calibrated
  percentages. PPv24 is unchanged.

  `experiments/ppv24-high-coverage-v1` tested three saved masks from
  `hierarchy-refresh-v1/masked-posts.json`, selected before inference to
  represent most of their real posts. The production prominence preparation
  helper reconstructed the exact fragments from saved UTF-8 spans; the generic
  adapter retained PPv24's diagnostic output contract. Three Astra-low
  subscription calls returned valid responses with no retries, reuse or
  baseline reruns. M174 (the entire meal-planning statement) scored 100 with
  no missing meaning; M394 (fragmented lunch-packing statement) scored 98,
  omitting only "just" and the effort/strain emoji; M2033 (the detailed
  linoleic-acid claim) scored 92, identifying "Horrifying" as the missing
  author judgment. The agent accepted the first two and initially marked the
  third uncertain. The user subsequently rejected 92 as too high, judging
  "Horrifying" worth substantially more than the remaining eight points; no
  replacement percentage was specified. This assesses representation of the
  health claim, not its medical accuracy. PPv24 is unchanged.

  [PPv24-D1](prominence-prompt-goal-v1/ppv24-diagnostic-v1/PPv24-D1.md) is a
  tested diagnostic-only variant against PPv24. It assesses a supplied saved
  response without rescoring or claiming access to original hidden reasoning.
  `experiments/ppv24-diagnostic-v1` made one valid Astra-low subscription call,
  with no retry or reuse. The input includes M2033 and its saved response but
  excludes the user's judgment. It supported 92, describing the claim as
  "nearly all of the substantive message" and the omitted reaction as
  "meaningful negative framing". This is a fresh score-conditioned assessment,
  not proof of the original cause; anchoring remains possible. It suggests
  examining factual versus evaluative weighting. PPv24 explicitly asks how the
  complete post supports represented meaning, but does not apply that same
  question to missing meaning. That asymmetry was a candidate to test, not
  an established cause.

  [PPv25](prominence-prompt-goal-v1/ppv25-draft-v1/PPv25.md) is approved for
  testing and experimentally tested, not production-frozen. Its sole change
  against PPv24 asks how the post develops, supports or depends on each of
  represented and missing meaning. `experiments/ppv25-high-coverage-v1`
  inherited the same three inputs/settings and saved PPv24 baseline without
  rerunning it. Three Astra-low subscription calls returned valid responses,
  with no retries or reuse. M174/M394/M2033 scored 100/97/92 versus 100/98/92.
  The disputed health-claim score remains 92 despite correctly identifying
  the missing emotional judgment. The agent accepted the two controls and
  rejected M2033 against the user's prior judgment. This trial demonstrates
  no improvement on the target case; a one-point control change is not a
  meaningful quality finding. PPv24 and PPv25 remain unchanged.

  `experiments/ppv25-reaction-only-v1` selected only "Horrifying" in the
  same M2033 post. One Astra-low subscription call returned a valid score of
  12, with class "Posts expressing horror or alarm about something unspecified."
  Missing meaning identified the detailed health claim and that its claimed
  persistence is what the author finds horrifying. No retry, reuse or baseline
  rerun occurred; the claim-only score of 92 remains saved evidence. The agent
  marked this diagnostic uncertain: the user has not judged reaction-only
  coverage, and a low standalone score does not settle the loss from omitting
  that reaction from a near-complete mask. The user subsequently clarified
  that prominence allocates a fixed 100 points among parts of the complete
  post's meaning. Represented and missing shares must exhaust that budget;
  importance is assessed within the complete post, not in isolation. This
  supersedes the agent's proposed non-additive interpretation, without
  establishing replacement scores for either mask. PPv25 is unchanged.

  [PPv26](prominence-prompt-goal-v1/ppv26-draft-v1/PPv26.md) is approved and
  untested, not production-frozen. Against PPv25 it makes the fixed-budget allocation explicit
  while retaining the class interpretation and output contract. No inference
  was performed for this revision; scoring consistency remains untested.

  [PPv26-D1](prominence-prompt-goal-v1/ppv26-diagnostic-v1/PPv26-D1.md) is an
  tested diagnostic variant against approved PPv26. Only the output instructions
  change: an allocation array describes each part of meaning and its allocated,
  represented and missing points. Allocated points total 100; represented points
  total prominence; each entry's represented and missing points exhaust its
  allocation. This is an inspectable model output, not access to hidden reasoning.
  PPv26 remains unchanged. No inference calls were made during drafting.

  `experiments/ppv26-allocation-v1` subsequently tested the saved M2033 claim
  and reaction-only masks in two Astra-low subscription calls, without retries,
  reuse or baseline reruns. Both responses were valid and all allocation sums
  checked out. Claim-only scored 85 (40 for the half-life claim, 45 for its
  seed-oil application, 15 missing for the reaction). Reaction-only scored 15
  (45/40 missing for the two factual parts, 15 represented for the reaction).
  The pair sums to 100, but the factual weights shifted between calls. The
  agent marked both uncertain: reaction weighting and possible overlap between
  the claim and its explanatory restatement require judgment; arithmetic alone
  does not establish semantic quality or repeatability. No replacement score
  has been approved by the user. PPv26-D1 wording remains unchanged.

  The user approved a mask-independent allocation diagnostic, not a production
  architecture change. [PPv26-D2A](prominence-prompt-goal-v1/ppv26-independent-v1/PPv26-D2A.md)
  allocates meaning from the unmarked post alone;
  [PPv26-D2B](prominence-prompt-goal-v1/ppv26-independent-v1/PPv26-D2B.md)
  assesses each mask against that saved allocation without changing it. Both
  are diagnostic variants derived against approved PPv26, which remains unchanged.
  `experiments/ppv26-independent-allocation-v1` and
  `experiments/ppv26-independent-scoring-v1` used three Astra-low subscription
  calls total, without retries, reuse or baseline reruns. The first allocated
  85 points to the combined claim/explanation and 15 to horror. This does not
  support the agent's suspicion that separate repetition entries caused 85/15.
  Both scoring calls preserved the allocation verbatim and passed arithmetic
  checks. Claim-only scored 85; reaction-only scored 10, withholding five of
  the reaction's 15 points because the mask did not specify what prompted it.
  Thus fixed weights did not produce complementary scores: the pair totals 95.
  Interpretation of the reaction in context remains unresolved, as does whether
  85/15 is a good allocation. The agent marked all three results uncertain.
  The runner flags the prior D1 baseline as input-mismatched because D2B adds
  the allocation; the old outputs remain evidence, not an identical-input test.

  The user set aside the word-allocation pivot (PPv28/PPv29 drafts) and returned
  to assessing the mask-independent meaning allocation. These drafts were not
  tested or adopted. PPv27's reference-interpretation revision also remains an
  untested draft; approved PPv26 is unchanged.

  A second post, synthetic and explicitly authorized, was tested using unchanged
  PPv26-D2A in `experiments/ppv26-relief-v1`, with the reusable spec
  `experiment_specs/ppv26-relief-v1.json`. The post described a daughter's scans
  showing no sign of cancer after three years of treatment, followed by the
  parent's overwhelming relief. One Astra-low subscription call, without masks
  or suggested scores, allocated 60 to the scan result, 18 to the treatment
  duration, and 22 to relief. The total is 100; no retries, reuse, or baseline
  reruns occurred. The agent initially marked the result uncertain. After
  reviewing the complete post and allocation, the user accepted 60/18/22 as
  reasonable; this is recorded separately as a user acceptance in the runner.
  The earlier 85/15 allocation remains unresolved. Two posts do not establish
  systematic reaction underweighting or calibrated percentages. No prompt
  changed for this test.

  The user authorized an ablation of the alternative-post-class operation.
  [PPv26-D3](prominence-prompt-goal-v1/ppv26-no-class-v1/PPv26-D3.md) retains
  PPv26-D2B's fixed-allocation scoring, drops the class-analysis paragraph after
  its initial contextual-interpretation sentence, and removes `post_class` from
  output. No reaction/reference-specific rule was added. The versioned revision
  receipt compares against approved PPv26; the ablation comparison is against
  tested PPv26-D2B. `experiments/ppv26-no-class-v1` uses the two exact saved
  inputs and 85/15 allocation with two new Astra-low subscription calls, no
  retries, reuse, allocation calls, or baseline reruns. Claim-only remains 85;
  reaction-only changes from 10 to 15, with zero factual credit. Both outputs
  retain every allocation meaning and weight and pass all point-sum checks.
  Agent reviews accept the local behavior; no user acceptance is recorded.
  This supports investigating removal of the class operation, but a single
  sample per mask does not establish causality, repeatability, or calibration.
  PPv26 remains the approved main prompt; PPv26-D3 is a tested diagnostic.

  Unchanged PPv26-D3 was then tested against the accepted relief allocation in
  `experiments/ppv26-relief-scoring-v1` (reusable spec:
  `experiment_specs/ppv26-relief-scoring-v1.json`). Three Astra-low subscription
  calls assessed separate masks for the scan-result clause, treatment-duration
  phrase, and relief sentence. They scored 60, 18, and 22 respectively, each
  with zero credit for the other two meanings. All retained the exact saved
  allocation and passed point-sum checks. No allocation calls, baseline reruns,
  retries, or reuse occurred. Agent reviews accept this local behavior; these
  mask scores have not received a separate user judgment. The masks closely
  match whole allocation entries, motivating the partial-mask test below.
  No prompt changed.

  `experiments/ppv26-relief-partial-v1` then tested four masks using unchanged
  PPv26-D3 and the same accepted allocation (reusable spec:
  `experiment_specs/ppv26-relief-partial-v1.json`). Four Astra-low subscription
  calls, without retries, reuse, or allocation calls, returned: fragmented scan
  result 60, fragmented relief 22, relief alone 12, cancer alone 8. The scan
  fragments omitted "show"; the relief fragments omitted "with". Both retained
  their whole-meaning scores. The single-word masks received only partial
  credit in their relevant allocation entries, zero in the others. All outputs
  preserved allocation meanings/weights and passed point-sum checks. Agent
  reviews accept the two fragmented cases and the direction of the cancer-only
  result; relief-only is uncertain because the exact 12/10 split needs judgment,
  not because a failure is established. No user verdicts on these four masks
  are recorded. These observations do not establish precise calibration or
  general reliability for partial masks. No prompt changed.

  The authorized small diverse test used three synthetic posts about an update
  not deleting files, a camera loan/return, and opposition to a parking fee.
  `experiments/ppv26-diverse-allocation-v1` used unchanged PPv26-D2A for three
  mask-independent allocations; `experiments/ppv26-diverse-scoring-v1` used
  unchanged PPv26-D3 for two masks per post. Corresponding reusable specs are
  under `experiment_specs/` with the same names. Nine Astra-low subscription
  calls total completed without retries, reuse, or baseline reruns. Allocations
  were 45/55 (non-deletion/hidden folder), 60/40 (loan/return), and 25/35/40
  (approval/opposition/reason). These allocations have no user approval.
  Fragmented versus partial scores were 45/20, 60/48, and 75/32 respectively.
  Partial outputs explicitly identified missing actor/negation, borrower, or
  stance rather than filling them from context; all six preserved the exact
  allocation and passed arithmetic checks. The negation pair removed both the
  actor and negation, so it does not isolate the effect of negation alone.
  Agent reviews accept the qualitative behavior, not precise calibration; no
  user mask verdicts are recorded. No clear semantic failure was identified in
  this small constructed sample, which does not establish real-corpus quality
  or repeatability. No prompt changed or was promoted.

  The following real-post sample reused exact saved masks: decaf motivation
  S29074d29b6-V1524, bathroom safety bars M05, six guitar mentions M09, and
  near-complete lunch packing M394. `experiments/ppv26-real-allocation-v1`
  and `experiments/ppv26-real-scoring-v1` used unchanged PPv26-D2A and PPv26-D3
  (matching reusable specs under `experiment_specs/`). Eight Astra-low
  subscription calls completed: four allocations and four scores, without
  retries, reuse, or baseline reruns. All original mask inputs were verified
  unchanged; every allocation totals 100 and every scoring output preserves
  its meanings/weights and passes arithmetic checks. Scores were 38/27/5/95.
  Agent reviews accept the qualitative low guitar-topic and high lunch-coverage
  behavior; decaf 38 and safety bars 27 remain uncertain weighting judgments,
  not established failures. On reviewing the full marked safety-bar post, the
  user judged 27 probably on the high side but plausible. This is recorded as
  an uncertain user review, not a rejection or a replacement score target.
  No unqualified user approval of these allocations or scores is recorded.
  Older PPv24 scores (52/39/8/98) are saved context only: the two-stage workflow
  differs, so changes cannot be attributed solely to removing class analysis.
  No prompt changed or was promoted. The tentative numerical judgments do not
  establish a failure requiring another scoring revision.

  An ordering test retained all five original direct members of Coffee taste
  and flavor (S29074d29b6) from `experiments/ppv13-refresh-direct-v1`, including
  the gamey-meat member despite its apparent grouping/title mismatch. No
  membership expansion, merging, filtering, title relevance, or post deduplication
  was applied. Three masks share the decaf post; its saved allocation and V1524
  score were reused directly, not rerun. `experiments/ppv26-ordering-allocation-v1`
  made two new PPv26-D2A calls, and `experiments/ppv26-ordering-scoring-v1` made
  four new PPv26-D3 calls, all Astra-low subscription, without retries or request
  reuse in those new runs. Matching reusable specs are under `experiment_specs/`.
  Exact saved masks, complete original membership, fixed allocations, and score
  arithmetic were verified. Descending order: V1524 38, V1532 30, V1397 13,
  V1521 8, V0488 5 (all under S29074d29b6). The same-post fuller-to-thinner
  ordering 38 > 30 > 8 is plausible to the agent. Low cross-post ordering at
  13/8/5 remains uncertain; no user ordering verdict is recorded. All five
  masks remain visible, including repeated posts and the grouping mismatch.
  This tests mask prominence only, not title relevance or final post ordering.
  Neither prompt was changed or promoted.

  The next ordering diagnostic retained all four original Bitcoin-node masks
  (S1fe681cb8e), verified to come from four distinct posts. Experiments
  `ppv26-bitcoin-allocation-v1` and `ppv26-bitcoin-scoring-v1` under `experiments/`
  used unchanged PPv26-D2A/PPv26-D3, with matching reusable specs under
  `experiment_specs/`. Eight Astra-low subscription calls completed without
  retries, reuse, or baseline reruns. Inputs preserved the saved masks exactly;
  titles and grouping metadata were review evidence only. Allocations totaled
  100; scoring retained every meaning/weight and passed all arithmetic checks.
  Descending scores: V0180 calendar trivia with Bitcoin hashtags 9, V0441
  second-coffee hashtag post 7, V0745 island-life heading/hashtag mentions 6,
  V0794 workshop/hospitality story 5. All select only Bitcoin mentions, not the
  surrounding narrative. Agent reviews mark all uncertain for fine cross-post
  ordering: consistently low coverage is plausible, but the narrow 5–9 range
  is weak evidence of meaningful rank differences. No clear semantic failure
  or user ordering verdict is established. No prompt or membership changed.

  The tea ordering diagnostic retained all four original masks of Sa01eaf30fd
  across three posts, sharing one allocation for the two health-concern masks.
  `experiments/ppv26-tea-allocation-v1` and `experiments/ppv26-tea-scoring-v1`
  used unchanged PPv26-D2A/PPv26-D3, with matching reusable specs under
  `experiment_specs/`. Seven Astra-low subscription calls completed without
  retries, reuse, or baseline reruns. Exact saved masks, original membership,
  shared allocation identity, allocation preservation and arithmetic all passed
  checks. Descending order: V0586 tea in a short desire statement 25, V1171
  drank plus tea in the health-concern post 15, V1169 tea alone in that post 5,
  V1298 incidental diary tea 1. Agent reviews accept this qualitative ordering
  and the identified missing meanings; no user ordering verdict or calibrated
  percentage is established. This provides a clearer cross-post contrast than
  the narrow Bitcoin scores. It remains evidence for the two-stage diagnostic,
  not verification of the approved single-call PPv26 or a prompt promotion.

  The user then authorized testing the class-step removal in a single call.
  `prominence-prompt-goal-v1/ppv30-draft-v1/PPv30.md` revises approved PPv26,
  removes class analysis, retains the instruction not to fill in unspecified
  meaning, and returns the full allocation alongside prominence. It generates
  the allocation with the mask visible rather than receiving a saved allocation.
  PPv30 is tested, not approved or frozen; PPv26 remains the approved main prompt.
  `experiments/ppv30-horror-v2` and `experiments/ppv30-tea-v2` used the matching
  `experiment_specs/ppv30-horror-v1.json` and `ppv30-tea-v1.json` specs. Initial
  v1 preparations made no calls: a concurrent runner change triggered the code
  identity guard. Fresh v2 preparations used the inspected runner, with no
  guard bypass. Six Astra-low subscription calls completed without retries,
  reuse, allocation calls, or baseline reruns. Posts, masks, and model settings
  match the saved two-stage comparisons; only supplied allocation was removed.
  The runner correctly labels these comparisons input mismatches, not matched
  input experiments. All six outputs passed schema and 100-point arithmetic.

  Saved two-stage versus PPv30 scores: claim 85 to 90; Horrifying 15 to 15;
  short-post tea 25 to 35; health-post drank plus tea 15 to 20; health-post tea
  5 to 10; diary tea 1 to 1. Tea ordering is unchanged. However, the claim call
  allocates 90 to claim/explanation and 10 to reaction; the reaction call
  allocates 85 and 15. Thus valid per-call totals do not establish a shared
  allocation across masks. One pair cannot distinguish mask influence from
  sampling variability. The two health-post masks also produce different
  decompositions, both giving health concern 25 versus the saved allocation's
  45. Meaning labels need care: the short-post tea entry includes desired, and
  the drank-plus-tea entry includes the speaker, despite those words being
  unselected. Agent reviews flag these labels as uncertain, not proven score
  failures. No user score verdict, calibration, or need for a separate
  allocation stage is established by this small comparison.

  The subsequent health-post diagnostic used unchanged PPv30 in
  `experiments/ppv30-health-parts-v1`, prepared from the matching reusable spec.
  Two Astra-low subscription calls tested the approved masks: over a gallon
  plus in less than 24 hours scored 45; the complete final concern sentence,
  including the emoji, scored 40. Exact post text, selected fragments, unchanged
  prompt hash, schema, and allocation arithmetic passed checks. No retries,
  reuse, or baseline reruns occurred. Both exceed saved drank-plus-tea 20 and
  tea-only 10, a plausible qualitative distinction. However, concern receives
  25 allocated points when the quantity/time mask is selected, matching the
  two earlier narrow masks, versus 40 when concern itself is selected. The
  concern call assigns the remaining 60 to the consumption/realization and
  credits none of those points to the mask. Agent assessments leave exact
  weights and cross-mask consistency uncertain: these calls cannot separate
  mask influence from sampling variability. There is no user score verdict
  or prompt promotion. The earlier 45-to-25 concern-allocation change alone
  is not established as a failure, since the quantity/time meaning supporting
  the concern carries substantial points separately.

  The user agreed to stop dissecting the health post and assess practical
  ordering with unchanged PPv30, then authorized the five original masks of
  Coffee taste and flavor (S29074d29b6). `experiments/ppv30-ordering-v1` uses
  the matching reusable spec and all five saved masks across three posts,
  including the gamey-meat member. Five Astra-low subscription calls completed
  without retries, reuse, or baseline reruns. Exact input/settings checks,
  unchanged prompt hash, schema, and allocation arithmetic passed. Inputs
  omit only the previously supplied allocation. Four saved comparisons come
  from `ppv26-ordering-scoring-v1`; V1524 comes from `ppv26-real-scoring-v1`.
  The runner records four input mismatches and one absent attached baseline;
  the fifth saved result was inspected separately, not recreated.

  New order, with saved two-stage scores in parentheses: V1524 fuller decaf
  motivation 40 (38), V1532 coffee-drinker motivation 37 (30), V1521 coffee
  plus flavour 13 (8), V1397 taste profile plus coffee 12 (13), V0488 meat
  flavor/taste mentions 5 (5). Agent assessment accepts the broad ordering;
  the only swap is the near-tied topic masks at 13 and 12, both marked uncertain
  for precise relative placement. No clear ranking failure or need for an
  immediate edit is established. This small sample does not calibrate scores,
  establish title relevance, or resolve cross-mask allocation consistency.
  PPv30 remains a tested candidate, not approved or frozen; there is no user
  verdict on this ordering yet.

  The user rejected further fine-grained score analysis and authorized a small
  test outside coffee/tea, looking for obvious scoring or ordering failures.
  `experiments/ppv30-diverse-nodes-v1` uses unchanged PPv30 and its matching
  reusable spec. The production prominence input preparer validated all original
  members from the saved title report: Kindness, goodness, and generosity
  (Sdc00def87d, 7), Photography (S45e455e0be, 5), and Stress and anxiety
  (S69c628e2ff, 2). Generic schema validation supports PPv30's allocation output;
  full posts, exact spans and node evidence are preserved, with no membership
  filtering or node titles in model input. Fourteen Astra-low subscription
  calls completed without retries, reuse, or baseline calls. Membership/input
  equality, unchanged prompt hash, schema and allocation arithmetic all passed.

  Scores by descending order: kindness V0806 20, V1080 7, V1075 6, V1079 5,
  V0805 4, V1072 3, V1071 3; photography V0964 13, V0765 8, V0963 4,
  V0767 2, V0688 1; stress/anxiety V0123 10, V1051 1. Agent assessment found
  no obvious coarse ranking failure: the full generosity claim outranks its
  adjective alone; forgetting to take photos outranks take photos; photographer
  credit outranks Photographer alone; an incidental photography hashtag ranks
  last. Anxiety framing a short chemotherapy update outranks stress wording
  within a long advice list. These are agent assessments, not user verdicts.
  The sample mostly contains narrow masks and does not validate the upper
  score range or calibrated percentages. No prompt edit or promotion occurred.
  Saved two-stage diagnostics are not normative targets for PPv30.

  The user has authorized small, in-scope prominence diagnostics, explicitly
  including prompt ablations, without repeated permission requests. Prepare
  versioned diagnostic variants and run these ablations without pausing for
  approval of each delta; still provide the deltas and report the results.
  This does not authorize broad experiments, unrelated prompt changes, or
  promotion of a diagnostic to the approved scoring prompt, and does not waive
  spending authorization or ledger rules. Keep calls bounded and reuse saved
  baselines.

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

The frozen mask-prompt baseline remains MPv3.43, identified in
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

For generic experiments containing saved prominence diagnostics (such as PPv30),
use `review --ui --view prominence`. This is an explicit renderer selection,
not a change to the frozen experiment adapter. The runner verifies the exact
model input against source text and mask spans, and requires valid prominence
scores before ranking scored cases. Unscored cases remain visible. `--node ID`
selects all masks of a node; it can be repeated and combined with `--only` or
`--flagged-only`. Unknown IDs are refused. `--ordering 'Linear cosine'` starts
in the combined-score ordering; without it the existing default is unchanged.
`--check` validates the generated batch using the existing viewer without a
terminal or comment writes. Interactive `c` comments persist separately and
are available in `show`, including for generic experiments; no approval is
inferred. None of these review options performs inference.

The Photography-only PPv30 review uses the existing `model-output-review` UI,
not the hierarchy browser. It retains all five original masks as separate
full-post cards and starts in prominence × rescaled-cosine order:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector && \
python3 experiment.py review experiments/ppv30-diverse-nodes-v1 \
  --ui --view prominence --node S45e455e0be \
  --cosine-comparison experiments/ppv30-diverse-nodes-v1/photography-cosine-v1/comparison.json \
  --ordering 'Linear cosine'
```

Left/Right steps through the ordered masks; `c` adds a comment, and `s` switches
between the saved orderings. The label Linear cosine denotes the combined
score, not cosine alone. The raw Jev hierarchy, masks and model outputs remain
unchanged. Offline validation and interactive first-to-last navigation passed;
these checks establish UI behavior, not a user verdict on ranking quality.

`prominence_cosine.py prepare` accepts either the historical normalized-vector
directory or a hierarchy-refresh directory containing `vector-map.json`,
`worker-request.json` and `worker-result/`. The latter reads the original raw
vectors without re-encoding them, verifies receipt hashes and row/span identity,
and freezes their hashes. Both formats require matching checkpoint/settings
and replay checks before `collect` emits a comparison.
This diagnostic makes no prompt calls; the shared experiment runner remains the
only prompt-experiment workflow.

For an explicitly authorized encoder comparison, `prepare --pooling` accepts
`selected-contextual-token-mean-linear-relu-linear-v1` (the existing SSE
projection) or `selected-contextual-token-mean-v1` (the same checkpoint's
selected-token mean before that projection). The option changes the frozen
worker model descriptor, not source text, token selections or prominence.
Every relevance row must have an encoder-request selection; direct use of saved
mask vectors and original mask replays are refused, preventing comparisons
between vectors from different representations.
The worker checks output dimensions against the projection or encoder backbone,
respectively; the config's dimensions must already match the chosen output.
Encoding reuse must match checkpoint, model artifacts, complete model descriptor
and batch size, in addition to exact notes/selections. Collection rejects a
receipt with a different pooling rule. Without this option the original behavior
is retained. Neither pooling choice changes production sorting policy.

`prepare --reuse-encoding COMPLETED_OUTPUT` permits new prominence assessments
to use a completed comparison's exact vectors, including a selected subset.
Each selected row must match the original note ID, complete text, selection ID
and byte spans exactly. Title, context and replay indices are mapped to their
original rows; the complete original encoder request is retained so receipt
validation still covers every vector. A replay outside the selected posts can
be retained from that encoding after checking its original mask identity.
The saved comparison's vector and receipt hashes are verified; its plan,
request, comparison, receipt and vectors are protected inputs. `collect`
validates the original worker receipt against its original request and plan
and uses the existing raw vectors. The new comparison records `encoding_source`.
Run `collect` directly after preparation; no worker run is needed. Changed
encoder input or modified source artifacts are refused.

The `subject_contexts` adapter's `prominence_basis` can be `context` (the default),
`subject`, or `node_title`. It renders only that saved field and the complete
post as prominence input. SP subjects, contexts and original membership evidence
remain available for review and SP-context relevance. The comparison reconstructs
the chosen input from frozen evidence; exact-request reuse gives matching
node-title/post inputs one assessment across repeated SP entries.

For prominence experiments with `dataset.combine_masks: true`, the diagnostic
checks the selected spans against the union of the referenced original vectors'
spans. If an original vector already has that exact selection, it is reused.
Otherwise the combined selection is encoded in its unchanged complete post;
`collect` uses that new vector. Replays always select the original mask spans,
and original vectors/results remain intact. Without the option, every referenced
mask must still match the evidence's exact spans.

`prominence_cosine.py prepare --node NODE_ID` selects a complete node from the
supplied experiments (repeat the flag for several nodes). It also accepts generic
experiments carrying prominence evidence, such as PPv30's allocation-debug
output. The production prominence preparer validates the full post and exact
spans and reconstructs the model input; mismatches and non-integer/out-of-range
scores are refused. Unselected nodes are not encoded or required to be scored.
`collect` preserves the historical raw `product` and adds `linear_product` plus
its ordering, using the viewer's rescaled-cosine formula above. The explicit
`linear_formula` distinguishes the two; raw product is not the combined score
chosen for this trial.

Optional `--only CASE_ID` (repeatable) selects exact saved cases across the supplied
experiments. Unknown case IDs fail before encoding. This can combine unchanged
original cases with newly scored selections without rerunning the originals.

`prepare --relevance-source-text CASE_ID TEXT` selects an exact, nonempty
statement from that case's saved complete post as standalone relevance input.
Repeat the option for multiple cases; cases without it retain their previous
representation. Duplicate or unknown case IDs and rewritten text are refused
before output preparation. The plan records `representation: "source_text"`,
the exact text and its UTF-8 byte spans in the original post. Saved prominence,
SP context, membership evidence and original MP mask identities remain intact.
The worker encodes the selected statement as its own complete text, alongside
the node title and original-vector replays. Highest-per-post ordering supports
both SP-context and source-text cases. Literal inverse diagnostics cannot be
combined with this option, and changed text cannot reuse a different encoding.

For an explicit wording diagnostic, add
`--relevance-source-replace CASE_ID OLD NEW` to that case's source-text option.
The original selection must still be exact saved-post text; the replacement
phrase must be nonempty and occur exactly once. Duplicate replacements,
unselected/unknown cases, no-op replacements and empty resulting text fail
before output preparation. The plan and comparison retain the original
`relevance_source_text` and its original byte spans, record
`relevance_source_replacement` as `before`/`after`, and carry the actual copy in
`relevance_text`. Only that copy is encoded, with its complete byte span. Saved
post text, model inputs, prominence, SP context and source bindings remain
intact; the copy cannot reuse vectors from different text. The default path
still encodes exact original text. This is an offline input diagnostic, not a
new prominence assessment or a production input policy.

`prominence_cosine.py prepare --include-inverse` additionally prepares each
mask's exact UTF-8 byte complement and one full-post selection per distinct
post. Both are encoded in the unchanged complete post. Selections are grouped
by post and identical selections are reused within the request. Saved mask
vectors and prominence answers are unchanged; the normal encoder replay check
still applies. No new prominence inference is involved.

`collect` adds two orderings to the same comparison file and review UI:

- **Inverse combined**: `P * w(mask cosine) + (100 - P) * w(inverse cosine)`.
- **Full-post cosine**: `100 * w(full-post cosine)`.

Here `P` is saved prominence on 0–100 and `w(c) = (clip(c, -1, 1) + 1) / 2`.
The existing **Prominence** and **Linear cosine** orderings remain available.
All three cosine-based scores are ranking heuristics, not percentages of
meaning. The inverse is a text complement, not a guaranteed partition of
semantic meaning. An empty or whitespace-only inverse is not encoded and
requires prominence 100; otherwise preparation refuses the case rather than
inventing a similarity. The literal complement and full-post selection retain
URLs and identifiers, unlike the prominence prompt's meaning assessment.
This difference must be considered when interpreting the comparison.

For a controlled exclusion test, add `--exclude-references` alongside
`--include-inverse` and use a new output directory. The versioned
`url-nip19-hex64-v1` rule excludes HTTP(S)/WS(S) URLs, existing NIP-19 identifier
matches, and standalone 64-character hexadecimal identifiers from the inverse
and full-post selections. Surrounding wording, sentence punctuation and
hashtags remain selected. It is a mechanical rule for these encoded forms,
not a general semantic identifier detector. Exact excluded and retained UTF-8
spans are saved in the plan/comparison. The original post remains the encoder
context, and original mask vectors, prominence scores and title are unchanged.
An empty full-post selection is refused. The UI labels this comparison
**references excluded**; earlier URL-inclusive comparisons remain available.

The Coffee inverse trial is available in the existing UI; press `s` to compare
orderings. The view still shows one original mask inline per card, preserves
all cases and comments, and does not aggregate posts or alter memberships:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector && \
python3 experiment.py review experiments/ppv30-coffee-node-v1 \
  --ui --view prominence \
  --cosine-comparison experiments/ppv30-coffee-node-v1/inverse-cosine-v1/comparison.json \
  --ordering 'Inverse combined'
```

On September 29, the user initially approved two expected post orders after
reading the complete wording with URLs omitted: decaf above weather in coffee, and the
century-eggs explanation above the rocket-stove post in Eggs. The
[decision record](../docs/planning/release-decisions.md#remaining-construction-work-and-completion-dependencies)
identifies the posts. These are post-ordering judgments, not mask-prominence
verdicts or adoption of a scoring formula.

The saved `inverse-no-references-v1/comparison.json` under each of
`experiments/ppv30-coffee-node-v1` and `experiments/ppv30-eggs-node-v1` supplies
both candidate scores. For this comparison only, `node_sorting.note_scores`
takes each post's highest Inverse combined score; Full-post cosine already
gives one score per post. The highest-score aggregation remains a candidate.

| Expected higher / lower cases | Highest Inverse combined | Full-post cosine |
| --- | --- | --- |
| coffee: decaf V1519 / weather V0862 | 63.77 < 65.47: fails | 63.57 < 65.25: fails |
| Eggs: century eggs V1447 / stove V0024 | 69.04 > 68.49: passes | 65.88 < 74.36: fails |

These two reviewed pairs do not establish overall accuracy. Original posts,
mask vectors, prominence scores and memberships are preserved.

The next authorized Coffee trial combined the union of existing direct-node mask
spans into one selection per post. The reusable spec is
`experiment_specs/ppv30-coffee-combined-masks-v1.json`; its frozen preparation
is `experiments/ppv30-coffee-combined-masks-v1`. It contains fourteen posts from
seventeen original masks. Twelve posts have one original mask. More coffee in
cool places has three nested masks whose union already equals V0504. Only the
weather post needs a new selection: `coffee is hot` plus `coffee` within
`#coffeechain`, at byte spans `[[116,129],[141,147]]`.

Thirteen rendered inputs match saved original cases exactly. The transport's
identity changed since those runs, so the runner conservatively offered no
automatic reuse. Those thirteen cases were selected directly from the original
experiment for the cosine comparison, rather than rerun. Only the new weather
selection ran through `experiment.py`, in the `weather` child experiment: one
valid Astra-low subscription call, no retries, unchanged **PPv30** and schema.
It scored prominence 18; allocation points sum to 100, represented points to 18,
and missing points to 82. This is a new answer, not a user approval. There was no
incremental cash charge; the $0.01575 catalog estimate is not an invoice.

`inverse-no-references-v2/comparison.json` under the combined-mask trial freezes
all fourteen selected cases, using the same checkpoint and local cached CPU
runtime as the original exclusion test. Five original-mask replays passed with
cosine above 0.9999999999999 and maximum normalized component error below
4.8e-8. The new combined mask is encoded in the unchanged weather post; the
other thirteen mask vectors are reused. Reference exclusions and the Inverse
combined formula are unchanged. Every selection was checked against the frozen
union preparation. The first local encoding attempt remains in
`inverse-no-references-v1`, without an accepted comparison: unrelated concurrent
edits changed a protected adapter file before collection. The local encoding was
repeated with fresh provenance; no prominence calls were repeated.

| Post | Highest individual-mask Inverse combined | Combined-mask Inverse combined |
| --- | --- | --- |
| Decaf drinkers valuing experience and flavour | 63.77 | 63.77 |
| Sunday weather with hot coffee | 65.47 | 63.37 |

The weather selection has mask cosine 0.898960 and inverse cosine 0.128776.
Selecting the hashtag's `coffee` as well reduces the coffee similarity of the
remaining text. Its prominence rose from V0862's 15 to 18, but its final score
fell from 65.47 to 63.37. Decaf remains unchanged at 63.767836, ahead of weather
at 63.370444 by only 0.397392 points. This one trial passes the user's expected
Coffee pair; it does not establish stability or overall ranking quality.

The complete fourteen-post order is below. Only decaf and weather swap positions
relative to the highest individual-mask baseline; all other positions remain.

| Position | Post | Inverse combined |
| --- | --- | --- |
| 1 | More coffee in cool places | 88.43 |
| 2 | Is there coffee for me? | 86.54 |
| 3 | Coffee with raw cream and raw egg yolk | 75.13 |
| 4 | Iced coffee served in ice | 74.70 |
| 5 | Roasting one's own beans | 73.95 |
| 6 | Half & half versus cream | 69.71 |
| 7 | Hashtag-heavy second-coffee post | 69.40 |
| 8 | Another coffee and Sunday wishes | 67.68 |
| 9 | Duck-egg breakfast burrito and coffee | 65.87 |
| 10 | Afternoon errands and morning coffee | 65.57 |
| 11 | Decaf drinkers valuing experience and flavour | 63.77 |
| 12 | Sunday weather with hot coffee | 63.37 |
| 13 | Movement, stretching and coffee ritual | 59.06 |
| 14 | Tolstoy animal-ethics post with Coffee hashtag | 42.84 |

No new user ordering judgments were inferred for these twelve unchanged posts.
That Coffee trial did not test combined masks in Eggs. Combining masks remains
a tested candidate; recursive sorting remains abandoned. The shared workflow,
cosine, ranking, node-sorting, worker and extraction regression suites passed
198 tests, including failing-first checks for union preparation, saved-answer
reuse, exact combined-mask encoding and selecting saved cases across experiments.

The subsequent authorized Eggs trial uses
`experiment_specs/ppv30-eggs-combined-masks-v1.json` and the same **PPv30** prompt,
schema and Astra-low subscription settings. Its frozen preparation,
`experiments/ppv30-eggs-combined-masks-v1`, unions fifteen direct-node masks into
seven post selections. Four selections exactly match original saved cases:
stove V0024, breakfast burrito V1125, coffee with raw egg yolk V0886, and dinner
V0310. Those four answers are kept directly; no baseline calls were rerun.

Only three changed selections were sent through the `changed-masks` child
experiment. Chocolate snacking (Pcf738f7f189508697732b562) scored prominence 37;
the mixed diary (Pd3503350f1556978382da064) scored 10. Both allocations satisfy
the fixed 100-point total and represented/missing sums. Century eggs
(Pde87f624d765af78a16a664a) was interrupted after HTTP 200 and a partial response:
the saved transport error is `terminated`, with no explicit temporary provider
error code. Three initial attempts produced two valid answers and one failure;
there were no retries. The unknown-cause failure is ineligible for automatic
retry under AGENTS.md. Its receipt and partial text are preserved; no prominence
value was inferred or copied from either original century-eggs mask.

The six scored posts are saved in `inverse-no-references-v1/comparison.json`
under the combined-mask Eggs preparation. The frozen seven-post input set is
retained separately, so this partial result does not hide the missing post.
The local CPU run used the same checkpoint/settings and cached runtime as the
Coffee trial, encoding twenty rows. All five original-mask replays passed:
cosine above 0.9999999999999, maximum normalized component error below 3.2e-8.
The two changed scored masks were encoded in their original complete posts;
the other four mask vectors were reused. All six selections match the frozen
union inputs. Reference exclusions and the Inverse combined formula are unchanged.

| Order among six scored posts | Post | Highest individual-mask Inverse combined | Combined-mask Inverse combined |
| --- | --- | --- | --- |
| 1 | Coffee with raw cream and raw egg yolk | 84.52 | 84.52 |
| 2 | Avoiding cooking eggs and snacking on chocolate | 73.81 | 73.77 |
| 3 | Duck-egg breakfast burrito | 70.40 | 70.40 |
| 4 | Dinner with four eggs | 69.41 | 69.41 |
| 5 | Rocket-stove post | 68.49 | 68.49 |
| 6 | Mixed diary with laying hens and several egg preparations | 70.66 | 65.78 |
| Unscored; position unknown | Century-eggs explanation | 69.04 | Missing after interrupted call |

Among the same six completed posts, the diary falls from third to sixth,
crossing the burrito, dinner and stove posts. Its remaining text's egg-title
cosine falls from the highest individual case's 0.399260 to 0.248475; combined
mask cosine is 0.918896 and prominence 10. The resulting score is 65.775835,
4.879346 points below its former maximum and below the stove's 68.492325. This
was a new result to review; diary versus stove had not yet been judged by the user.
At that checkpoint, the user-approved century-eggs-above-stove check was unresolved
for combined masks, and a complete seven-post order was unavailable. The existing
individual-mask result passed that pair; it was not the new union result.

The 33 relevant shared union, cosine, ranking, node-sorting and worker checks
passed, as did the production review UI check displaying all three changed
cases, including the unscored failure. The successful calls' $0.0518 catalog
estimate is a subtotal, not an invoice or measured subscription quota. The
interrupted call emitted partial text but normalized its usage to zeros; its
actual token usage is unknown. No incremental cash charge or paid fallback was
introduced. Completion required a century-eggs prominence answer and an explicit
user exception to the unknown-cause retry rule for another attempt.

The user subsequently approved one additional century-eggs attempt. It ran
through the shared workflow in `completed-masks-v1`, prepared from the original
three changed cases with unchanged inputs, **PPv30**, schema and Astra-low
settings. Preparation verified one new request and two exact-request reuses;
`run --max-new-attempts 1` bounded the exception to the single authorized call.
Century eggs returned a valid prominence of 30, with allocation totals 100,
represented 30 and missing 70. The chocolate and diary answers were reused,
not sampled again. The original interrupted receipt is preserved in
`changed-masks`; this does not change the normal retry policy. The earlier
one-case `century-retry-v1` preparation remains unrun; the three-case completion
allowed both successful answers and the new answer to share a scored experiment
without rerunning them or changing the cosine workflow.

The final seven-post comparison is
`experiments/ppv30-eggs-combined-masks-v1/inverse-no-references-v2/comparison.json`.
It selects four original cases and three cases from `completed-masks-v1`.
All seven selections match the frozen union preparation. The local CPU worker
encoded 23 rows, including five original-mask replays (V0024, V1447, V0226,
V1270, V0886). All passed with cosine above 0.9999999999999 and maximum normalized
component error below 4.7e-8. Checkpoint, reference exclusions and the Inverse
combined formula remain unchanged. No baseline prominence calls were rerun.

| Final position | Post | Highest individual-mask Inverse combined | Combined-mask Inverse combined |
| --- | --- | --- | --- |
| 1 | Coffee with raw cream and raw egg yolk | 84.52 | 84.52 |
| 2 | Avoiding cooking eggs and snacking on chocolate | 73.81 | 73.77 |
| 3 | Duck-egg breakfast burrito | 70.40 | 70.40 |
| 4 | Dinner with four eggs | 69.41 | 69.41 |
| 5 | Century-eggs explanation | 69.04 | 68.52 |
| 6 | Rocket-stove post | 68.49 | 68.49 |
| 7 | Mixed diary with laying hens and several egg preparations | 70.66 | 65.78 |

Century eggs scores 68.517903 and the stove 68.492325: the user's expected order
passes by only 0.025578 points. The combined century mask has cosine 0.905204,
inverse cosine 0.141138 and prominence 30. A read-only calculation using the
production `ranking_scores` shows that, with these vectors fixed, a hypothetical
prominence of 29 would score 68.135870 and reverse the pair. That hypothetical
value is not a model answer or a changed artifact. At completion, the trial passed
both reviewed pairs (Coffee and Eggs), but these small margins do not establish
stability or general ranking quality. The diary remained below the stove; that
pair was still awaiting user review. Combining masks remains a candidate, not an
adopted rule.

The 33 relevant checks passed again, as did the production review UI check for
the three completed cases. The authorized call used 672 input and 218 output
tokens with no reported reasoning tokens; its $0.01762 catalog estimate is not
an invoice or measured subscription quota. The first interrupted call's actual
token usage remains unknown. There was no incremental cash charge or paid
fallback. The combined-mask Eggs comparison is complete; no further calls were
made under the single-attempt exception.

The user then reviewed the complete diary and stove posts with image links
omitted and chose A, the diary, as the higher post in Eggs. This adds a third
expected-order check. It does not approve either prominence answer or adopt a
scoring formula. The diary's combined case is Pd3503350f1556978382da064; the
stove is S629f5c9bc7-V0024. Their saved scores were verified by recomputing them
through the production `ranking_scores` function; no new inference ran.

| Expected higher / lower posts | Highest individual-mask Inverse combined | Combined-mask Inverse combined |
| --- | --- | --- |
| coffee: decaf / weather | 63.77 < 65.47: fails | 63.77 > 63.37: passes |
| Eggs: century eggs / stove | 69.04 > 68.49: passes | 68.52 > 68.49: passes |
| Eggs: diary / stove | 70.66 > 68.49: passes | 65.78 < 68.49: fails |

The combined-mask trial therefore passes two of the three user-approved pairs.
The diary's fall below the stove is now a confirmed ordering failure, rather
than an unreviewed movement. How to change the score remains open.

The next user-authorized trial uses saved SP context for both prominence and
relevance, with **sorting score = prominence × relevance**. It replaces Inverse
combined in this experiment. The reusable spec is
`experiment_specs/ppv30-context-sorting-v1.json`; its source selector contains
only five post/node/SP-number references, not copied contexts or generated
inputs. The shared `subject_contexts` adapter loads and hashes the existing
masked-post and hierarchy sources, verifies each SP entry against a direct node
membership, and freezes its exact context and complete original post. Node
titles, masks and SP subjects remain review-only metadata in prominence inputs.

[PPv30-context-v1](prominence-prompt-goal-v1/ppv30-context-v1/PPv30-context-v1.md)
is an experimental context adaptation of PPv30's allocation diagnostics. The
shared revision workflow records its full delta against the last approved
main prompt, PPv26. It assesses the meaning represented by the supplied SP
context in the original post; existing mask prominence values are not reused.
The 100-point allocation and represented/missing totals are mechanically checked.
This is a tested candidate, not approval of the new prominence values or a
production-frozen prompt.

`experiments/ppv30-context-sorting-v1` completed five valid Astra-low subscription
calls, bounded by `--max-new-attempts 5`. There were no failures, retries, reused
answers, baseline calls or new SP calls. Input tokens total 3,330 and output
tokens 1,089, with no reported reasoning tokens. The $0.08775 catalog estimate
is not an invoice or measured subscription quota; there was no incremental cash
charge or paid fallback.

`relevance-v1/comparison.json` under that experiment uses the existing SSE worker
and checkpoint. Each complete SP context is encoded as its own text; the
original post is not its encoder context. The two hierarchy node titles are
encoded separately. Five original-mask replays (V0024, V1268, V1447, V1519,
V0862) passed with cosine above 0.9999999999999 and maximum normalized component
error below 4.7e-8. The local CPU worker encoded twelve rows. The collector
verifies exact original SP context/number/subject identity, rejects a literal
inverse for context inputs, and uses the unchanged production `ranking_scores`
calculation. Original mask vectors remain provenance/parity controls; they are
not used as the contexts' relevance vectors.

| Post | SP number | Prominence | Relevance | Sorting score |
| --- | --- | --- | --- | --- |
| Decaf drinkers valuing experience and flavour | 1 | 29 | 0.901547 | 26.144851 |
| Sunday weather with hot coffee | 6.1 | 14 | 0.823400 | 11.527605 |
| Century-eggs explanation | 2.1 | 28 | 0.882428 | 24.707985 |
| Mixed diary with laying hens and several egg preparations | 5 | 20 | 0.910898 | 18.217952 |
| Rocket-stove post | 6.2 | 7 | 0.966325 | 6.764276 |

All three user-approved pairs pass. Sorting score differences are 14.617246 for
decaf above weather, 17.943709 for century eggs above stove, and 11.453676 for
diary above stove.
Prominence alone gives the same orders. Relevance alone favors the stove over
both other Eggs posts, so this trial does not establish that relevance improves
ordering. It tests one explicitly selected existing SP context per post, not a
rule for combining or choosing multiple contexts. All five encoded selections
and final calculations were independently checked against frozen inputs and raw
vectors. The shared experiment, cosine, ranking, node-sorting, worker and
extraction suites passed 200 tests, including failing-first checks for exact
source preparation, answer reuse, allocation validation and complete-context
encoding. No production ranking, membership, recursive sorting or parent-child
transfer was introduced.

The complete-node follow-up uses
`experiment_specs/ppv30-context-node-orders-v1.json` with the unchanged tested
**PPv30-context-v1** prompt and Astra-low subscription settings. Its source
selector supplies only `nodes` plus the saved subject and hierarchy paths.
The `subject_contexts` adapter enumerates every SP entry whose exact mask spans
match a direct node membership, including distinct SP contexts sharing a mask.
It rejects duplicate or unknown node selections and direct masks without a
saved SP context. Descendant memberships do not supply cases. Preparation
freezes 19 contexts from Coffee's 14 posts and 18 from Eggs' seven posts.
The five earlier prominence requests match exactly and are reused.

`prominence_cosine.py prepare --post-order highest` records the user-authorized
experimental aggregation choice. After SSE encoding, `collect` retains the
individual context results and adds `posts` and `post_rankings` to its comparison.
Each post's highest prominence determines its prominence-only order; its
highest `linear_product` determines its sorting-score order. These maxima are
independent, with each winning case and the context count saved. Case-ID order
breaks ties between contexts; note-ID order breaks ties between posts. This
comparison does not establish a production aggregation rule.

`experiments/ppv30-context-node-orders-v1` completed all 37 valid cases:
32 new assessments and five exact-request reuses, with no failures, retries,
baseline reruns or new SP calls. New-attempt usage was 19,511 input tokens and
6,014 output tokens, including 397 reasoning tokens. The $0.49581 catalog
estimate is not an invoice or subscription quota measurement; there was no
incremental cash charge or paid fallback.

The saved complete orders are in `relevance-v1/comparison.json`. The matching
offline CPU SSE worker encoded 44 rows: two node titles, 37 complete SP contexts
and five original-mask replays. Every replay cosine exceeded 0.9999999999999;
the largest normalized component error was 4.66e-8. All 37 context selections,
source identities, cosine calculations, sorting scores, post maxima and final
orders were independently checked against the original sources and raw vectors.
The experiment, cosine, ranking, node-sorting, worker and extraction suites
passed 201 tests. Failing-first checks covered complete direct-node selection,
answer reuse and independent post maxima with different winning contexts.

The following tables list posts in descending sorting-score order. Prominence
is the post's highest context prominence, which need not be the prominence of
its highest-sorting-score context. Both orders use note IDs to break exact ties.

Coffee:

| Post (note-ID prefix) | Prominence rank | Highest prominence | Sorting-score rank | Highest sorting score |
| --- | ---: | ---: | ---: | ---: |
| More coffee in cool places (`37f44e1f`) | 1 | 100 | 1 | 86.860927 |
| Coffee with raw cream and raw egg yolk (`f4c5aa5f`) | 2 | 95 | 2 | 71.803677 |
| Is there coffee for me? (`78462b92`) | 3 | 85 | 3 | 70.697771 |
| Hashtag-heavy second-coffee post (`862486d8`) | 4 | 60 | 4 | 55.578774 |
| Roasting your own beans (`056e6466`) | 6 | 46 | 5 | 40.978201 |
| Another coffee and Sunday wishes (`737eaa89`) | 7 | 45 | 6 | 38.121899 |
| Iced coffee served in ice (`76e19c3e`) | 8 | 40 | 7 | 35.839159 |
| Afternoon errands and morning coffee (`e0508834`) | 5 | 47 | 8 | 32.604173 |
| Half & half versus cream (`143fee76`) | 9 | 30 | 9 | 26.917507 |
| Duck-egg breakfast burrito and coffee (`ee3404d5`) | 10 | 30 | 10 | 26.729323 |
| Decaf drinkers (`2dc50a30`) | 11 | 29 | 11 | 26.144851 |
| Sunday weather with hot coffee (`82d3d344`) | 12 | 27 | 12 | 21.245928 |
| Coffee, movement and stretching (`8a025f69`) | 13 | 14 | 13 | 13.400827 |
| Tolstoy quotation with Coffee hashtag (`be8d07d4`) | 14 | 1 | 14 | 0.917359 |

Eggs:

| Post (note-ID prefix) | Prominence rank | Highest prominence | Sorting-score rank | Highest sorting score |
| --- | ---: | ---: | ---: | ---: |
| Avoiding eggs and snacking on chocolate (`612fa3c5`) | 1 | 57 | 1 | 50.215997 |
| Coffee with raw egg yolk (`f4c5aa5f`) | 2 | 55 | 2 | 48.097435 |
| Century-eggs explanation (`11d2afb1`) | 3 | 35 | 3 | 27.137100 |
| Duck-egg breakfast burrito (`ee3404d5`) | 4 | 30 | 4 | 24.794540 |
| Mixed diary with hens and egg preparations (`eaa6a5e6`) | 6 | 20 | 5 | 18.217952 |
| Four-egg dinner (`fbd52a1d`) | 5 | 23 | 6 | 17.145254 |
| Rocket stove (`99e6a514`) | 7 | 7 | 7 | 6.764276 |

The three original agreed comparisons pass under both methods: decaf above weather
(prominence 29 > 27; sorting score 26.144851 > 21.245928), century eggs above
stove (35 > 7; 27.137100 > 6.764276), and diary above stove (20 > 7;
18.217952 > 6.764276). The weather and century-eggs post maxima now select
different SP entries from the initial five-post trial; those original context
assessments remain intact.

Relevance reverses four pairs with unequal prominence. In Coffee, errands falls
from fifth to eighth, below roasting, another coffee and iced coffee. Its
prominence 47 and relevance 0.693706 produce sorting score 32.604173; roasting's
46 and 0.890830 produce 40.978201. In Eggs, the diary rises above the four-egg
dinner: 20 × 0.910898 gives 18.217952, while 23 × 0.745446 gives 17.145254.
The user then reviewed the complete wording of roasting versus errands and
diary versus four-egg dinner with URLs omitted, answering "coffee A. eggs, A."
This establishes two additional expected post orders:

| Hierarchy node | Expected higher / lower | Prominence alone | Sorting score |
| --- | --- | --- | --- |
| coffee | Roasting (`056e6466`) above errands (`e0508834`) | 46 < 47: fails | 40.978201 > 32.604173: passes |
| Eggs | Diary (`eaa6a5e6`) above four-egg dinner (`fbd52a1d`) | 20 < 23: fails | 18.217952 > 17.145254: passes |

The user subsequently reviewed the two remaining changed Coffee pairs. Iced
coffee (`76e19c3e`) should be above errands (`e0508834`): sorting score
35.839159 > 32.604173 matches this judgment; prominence 40 < 47 reverses it.
Another coffee (`737eaa89`) versus errands was judged "about equal," with a
tentative tiny preference for another coffee because of "but I need another
one." Its sorting score is 38.121899 versus errands' 32.604173; its prominence
is 45 versus 47. The sorting-score direction agrees with the tentative
preference, but this is not a clear expected higher/lower order. No numeric
tolerance for "about equal" has been agreed, so the size of the sorting-score
difference is not marked as passing or failing that judgment.

The user next reviewed the complete wording of the hashtag-heavy second-coffee
post (`862486d8`, A) versus roasting your own beans (`056e6466`, B), with URLs
omitted, and chose B. This adds a clear expected order that both methods fail:
roasting has prominence 46 versus second coffee's 60, and sorting score
40.978201 versus 55.578774. Roasting's relevance is 0.890830 versus second
coffee's 0.926313, so both prominence and relevance favor second coffee in the
saved experiment. Each post has exactly one matching SP context; choosing among
multiple contexts did not cause this failure.

Across the seven clear user-reviewed orders, the saved SP-context sorting score
matches six and prominence alone matches three. The about-equal comparison is
recorded separately and excluded from these counts. Relevance improves three
clear reviewed comparisons in this saved experiment; this does not establish
general ordering quality or approve the prominence values, prompt or production
formula. All four changed pair orders have now been reviewed. No new inference
or encoding was needed to check the new judgments.
Production adoption remains open; no recursive sorting or parent-child transfer
was changed.

The user then approved testing prominence as the percentage of the complete
post's meaning that concerns the saved SP subject. The experimental
[PPv30-subject-v1](prominence-prompt-goal-v1/ppv30-subject-v1/PPv30-subject-v1.md)
prompt retains the fixed 100-point allocation. `represented` now means points
concerning the SP subject; `missing` means points not concerning it, and
`missing_meaning` describes that latter meaning. This is a semantic change to
prominence, not a change to the output arithmetic. Its shared revision receipt
records the full delta against last-approved main prompt PPv26. No expected
orders or post-specific examples are supplied to the prompt.

`experiment_specs/ppv30-subject-node-orders-v1.json` sets
`dataset.prominence_basis: "subject"` on the existing `subject_contexts` adapter.
Model input contains exactly `subject` and `post`. Node titles, SP contexts,
masks and provenance remain review-only evidence. Omitting that option retains
the previous context-and-post input; unsupported values or use on another
adapter are refused. The new run preserves all 37 source entries and identical
Astra-low subscription settings. There are 33 distinct subject/post inputs;
four repeated entries can reuse exact requests. The context baseline remains
saved and is not rerun; the shared comparison correctly marks all 37 changed
inputs as `input_mismatch`.

Relevance continues to use each complete saved SP context and the original
node title. `prominence_cosine.py prepare --reuse-encoding` reuses
`experiments/ppv30-context-node-orders-v1/relevance-v1` exactly. Only the new
prominence values change the sorting scores. The seven clear user-reviewed
orders and the separate about-equal judgment remain the checks, with independent
highest prominence and highest sorting score per post. This experiment does
not adopt a production ranking rule, revise SP entries or expand membership.

`experiments/ppv30-subject-node-orders-v1` completed 37 valid cases with 33 new
Astra-low subscription assessments and four reuses of identical requests from
this run. There were no failures, retries, baseline reruns, new SP calls or new
SSE worker calls. New-attempt usage was 20,157 input tokens and 5,772 output
tokens, including 534 reasoning tokens. The $0.49017 catalog estimate is not an
invoice or measured subscription quota; there was no incremental cash charge
or paid fallback. **PPv30-subject-v1** is tested, not production-frozen; approved
main prompt PPv26 is unchanged.

`relevance-v1/comparison.json` reuses the preceding run's raw vectors and worker
receipt. All 37 contexts, encoder notes, selections, cosine values and relevance
values match exactly. The five original-mask replay results are identical.
Every new allocation, prominence input, sorting score, independent post maximum
and final order was checked against the frozen sources and existing raw vectors.
The shared experiment, cosine, ranking, node-sorting, worker and extraction
suites passed 201 tests. Failing-first checks cover the subject/post input,
exact request reuse and collecting new prominence with existing encodings;
changed contexts and modified vector artifacts are refused.

Both prominence alone and the sorting score now match all seven clear expected
orders. The about-equal judgment remains separate from the counts:

| Hierarchy node | Expected higher / lower | Subject prominence | Sorting score |
| --- | --- | --- | --- |
| coffee | Decaf / Sunday weather | 100 > 35 | 90.154658 > 28.819013 |
| Eggs | Century eggs / rocket stove | 100 > 10 | 88.242803 > 9.663252 |
| Eggs | Mixed diary / rocket stove | 38 > 10 | 34.614109 > 9.663252 |
| coffee | Roasting / errands | 100 > 60 | 89.083045 > 41.622349 |
| Eggs | Mixed diary / four-egg dinner | 38 > 30 | 34.614109 > 25.872700 |
| coffee | Iced coffee / errands | 95 > 60 | 85.118002 > 41.622349 |
| coffee | Roasting / second coffee | 100 > 70 | 89.083045 > 64.841903 |

The roasting assessment counts its opening contrast, personal taste profile,
home-roasting journey, comparison with pre-roasted coffee and coffee-community
sign-off as concerning Coffee: all 100 points. The second-coffee assessment
assigns 70 points concerning Coffee and 30 to the remaining affiliations. The
previous context's missing claims no longer reduce roasting's prominence.
These are mechanically valid assessments, not user approval of exact percentages.

Another coffee (`737eaa89`) has sorting score 42.357665 versus errands'
41.622349, a difference of 0.735316 in the user's tentatively preferred direction.
Subject prominence alone gives 50 versus 60 in the opposite direction. No
numeric tolerance for "about equal" is inferred or marked as passed.

The complete current orders below use descending sorting score. The preceding
context-prominence orders remain saved for comparison; these changes are not
new user-approved orders. The highest prominence column can refer to a different
SP entry from the highest sorting score.

Coffee:

| Post (note-ID prefix) | Highest subject prominence | Highest sorting score |
| --- | ---: | ---: |
| More coffee in cool places (`37f44e1f`) | 100 | 93.490294 |
| Decaf drinkers (`2dc50a30`) | 100 | 90.154658 |
| Roasting your own beans (`056e6466`) | 100 | 89.083045 |
| Iced coffee served in ice (`76e19c3e`) | 95 | 85.118002 |
| Is there coffee for me? (`78462b92`) | 100 | 83.173849 |
| Half & half versus cream (`143fee76`) | 90 | 80.752521 |
| Coffee with raw cream and raw egg yolk (`f4c5aa5f`) | 100 | 75.582818 |
| Hashtag-heavy second-coffee post (`862486d8`) | 70 | 64.841903 |
| Another coffee and Sunday wishes (`737eaa89`) | 50 | 42.357665 |
| Afternoon errands and morning coffee (`e0508834`) | 60 | 41.622349 |
| Sunday weather with hot coffee (`82d3d344`) | 35 | 28.819013 |
| Coffee, movement and stretching (`8a025f69`) | 30 | 28.716058 |
| Duck-egg breakfast burrito and coffee (`ee3404d5`) | 25 | 22.274436 |
| Tolstoy quotation with Coffee hashtag (`be8d07d4`) | 1 | 0.917359 |

Eggs:

| Post (note-ID prefix) | Highest subject prominence | Highest sorting score |
| --- | ---: | ---: |
| Century-eggs explanation (`11d2afb1`) | 100 | 88.242803 |
| Avoiding eggs and snacking on chocolate (`612fa3c5`) | 85 | 74.883505 |
| Coffee with raw egg yolk (`f4c5aa5f`) | 65 | 56.842423 |
| Duck-egg breakfast burrito (`ee3404d5`) | 45 | 37.191810 |
| Mixed diary with hens and egg preparations (`eaa6a5e6`) | 38 | 34.614109 |
| Four-egg dinner (`fbd52a1d`) | 30 | 25.872700 |
| Rocket stove (`99e6a514`) | 10 | 9.663252 |

The next user review presented More coffee in cool places (`37f44e1f`) as A and
roasting your own beans (`056e6466`) as B, using the complete wording with image
URLs omitted. The user answered "probably B". This is a tentative preference
for roasting above the short post, recorded separately from the seven clear
checks and the earlier about-equal judgment:

| Post | Highest subject prominence | Relevance of highest sorting-score entry | Highest sorting score |
| --- | ---: | ---: | ---: |
| A: More coffee in cool places (`37f44e1f`) | 100 | 0.934903 | 93.490294 |
| B: Roasting your own beans (`056e6466`) | 100 | 0.890830 | 89.083045 |

Both winning entries have SP subject Coffee. A's SP context is "The post
explicitly mentions 'More coffee.'" B's is "The post discusses drinking coffee,
roasting coffee beans, and discovering a personal taste profile." Their
relevance values are respectively `(0.8698058827170315 + 1) / 2` and
`(0.7816608935627184 + 1) / 2`. With prominence 100 in both entries, relevance
alone puts A first, opposite to the user's tentative preference. Prominence
alone ties the posts. No additional inference or encoding was needed; the
formula and seven-clear-check counts remain unchanged. The preference does not
authorize a production change.

On September 30, the user clarified that B only talks about coffee, while A
talks about coffee and also "cool places". In A's winning Coffee case
`context-fce457df09c3838440927e0e`, the saved assessment assigns 100 points to
"Continuing to enjoy coffee in cool places." It allocates `represented: 100` and
`missing: 0`, counting the combined meaning entirely toward Coffee, and returns
prominence 100. **PPv30-subject-v1** explicitly permits a part to concern the SP
subject alongside other subjects. The saved result does not distinguish the
additional meaning the user identified. No revised prominence rule or exact
percentage is approved by this clarification; the pair remains tentative.

This draw resolves the seven saved clear checks. It does not establish general
ordering quality, calibrated percentages or production adoption. Prominence
alone also passes all seven, so they do not establish an advantage from relevance
under the revised definition. The separate about-equal result is consistent in
direction with the user's tentative preference, without an agreed tolerance.

The user authorized testing the coffee/places distinction in prominence while
keeping relevance unchanged. Tested experimental candidate
[PPv30-subject-v2](prominence-prompt-goal-v1/ppv30-subject-v2/PPv30-subject-v2.md)
replaces only v1's permission for meaning to concern multiple subjects with an
instruction to distinguish the meaning about each subject, including within
one statement, and divide the allocated points accordingly. Details developing
the SP subject itself still count; descriptive words are not automatically
separate subjects. The prompt contains no post-specific examples or expected
orders. Its shared revision receipt records the full delta against approved
main prompt PPv26, which remains unchanged. The reusable spec is
`experiment_specs/ppv30-subject-node-orders-v2.json`.

`experiments/ppv30-subject-node-orders-v2` was prepared with `--from` the v1
experiment and the new prompt. All 37 case IDs, subject/post inputs, review
evidence and runner settings match exactly. The original expected order check
failed before the revision: roasting's 89.083045 was below the short post's
93.490294. The new run completed 37 valid cases from 33 new Astra-low subscription
assessments and four exact-request reuses within the run. There were no failures,
retries, baseline reruns, new SP calls or new SSE worker calls. New-attempt usage
was 23,028 input tokens and 6,095 output tokens, including 640 reasoning tokens;
the $0.53503 catalog estimate is not an invoice or measured subscription quota.
There was no incremental cash charge or paid fallback. The 35 changed and two
unchanged response comparisons describe text changes, not ordering quality.

`relevance-v1` was prepared with the same vectors, worker settings, five replays
and `--post-order highest`, reusing the original completed context encoding with
`--reuse-encoding`. Collection used the existing raw vectors directly. All 37
contexts, subjects, cosine values and title cosines are unchanged; raw-vector
and receipt hashes and replay parity match exactly. Each allocation, sorting
score, independently selected post maximum and complete order was verified.
The shared experiment and prominence-cosine suites passed 91 tests; no workflow
implementation or production ranking code changed.

The Coffee assessment now allocates 65 points to continuing coffee experiences
and 35 to their setting, of which ten count toward Coffee and 25 toward places:
Coffee prominence is 75. Roasting's Coffee assessment assigns 96 points to
Coffee and four to community-tagging/hot-take framing. These percentages are
experimental assessments, not user-approved values. The distinction is visible
in the Coffee entries, but the final post order still reverses the tentative
preference because the highest sorting score can come from another SP subject:

| Post / SP subject | Prominence | Relevance | Sorting score |
| --- | ---: | ---: | ---: |
| A: More coffee in cool places / Coffee | 75 | 0.934903 | 70.117721 |
| A: More coffee in cool places / Continued experiences of coffee in appealing places | 100 | 0.868609 | 86.860927 |
| B: Roasting your own beans / Coffee | 96 | 0.890830 | 85.519723 |

A's highest sorting-score case is now `context-80cc7d69d7a09c762d6412a9`, whose
SP subject includes both coffee and places. The post uses 86.860927 rather than
its Coffee entry's 70.117721, so it remains above B's 85.519723. Prominence alone
also puts A's highest value, 100, above B's 96. The prompt change therefore does
not resolve this separate tentative ordering check. Aggregation remains the
original tested rule and is not changed or approved for production.

Both prominence alone and the sorting score still match the seven clear checks:

| Hierarchy node | Expected higher / lower | Highest subject prominence | Highest sorting score |
| --- | --- | --- | --- |
| coffee | Decaf / Sunday weather | 70 > 35 | 63.108260 > 28.819013 |
| Eggs | Century eggs / rocket stove | 100 > 7 | 88.242803 > 6.764276 |
| Eggs | Mixed diary / rocket stove | 37 > 7 | 33.703212 > 6.764276 |
| coffee | Roasting / errands | 96 > 60 | 85.519723 > 41.622349 |
| Eggs | Mixed diary / four-egg dinner | 37 > 28 | 33.703212 > 24.147853 |
| coffee | Iced coffee / errands | 95 > 60 | 85.118002 > 41.622349 |
| coffee | Roasting / second coffee | 96 > 55 | 85.519723 > 50.947210 |

The earlier about-equal pair remains separate: another coffee has highest
prominence 53 and sorting score 44.899125; errands has 60 and 41.622349. The
sorting-score difference is 3.276776 in the tentatively preferred direction,
without an agreed closeness tolerance. It is not counted as passed.

Complete v2 orders, descending by highest sorting score:

Coffee:

| Post (note-ID prefix) | Highest subject prominence | Highest sorting score |
| --- | ---: | ---: |
| More coffee in cool places (`37f44e1f`) | 100 | 86.860927 |
| Roasting your own beans (`056e6466`) | 96 | 85.519723 |
| Iced coffee served in ice (`76e19c3e`) | 95 | 85.118002 |
| Is there coffee for me? (`78462b92`) | 95 | 79.015156 |
| Coffee with raw cream and raw egg yolk (`f4c5aa5f`) | 100 | 75.582818 |
| Decaf drinkers (`2dc50a30`) | 70 | 63.108260 |
| Half & half versus cream (`143fee76`) | 60 | 53.835014 |
| Hashtag-heavy second-coffee post (`862486d8`) | 55 | 50.947210 |
| Another coffee and Sunday wishes (`737eaa89`) | 53 | 44.899125 |
| Afternoon errands and morning coffee (`e0508834`) | 60 | 41.622349 |
| Sunday weather with hot coffee (`82d3d344`) | 35 | 28.819013 |
| Coffee, movement and stretching (`8a025f69`) | 25 | 23.930048 |
| Duck-egg breakfast burrito and coffee (`ee3404d5`) | 25 | 22.274436 |
| Tolstoy quotation with Coffee hashtag (`be8d07d4`) | 1 | 0.917359 |

Eggs:

| Post (note-ID prefix) | Highest subject prominence | Highest sorting score |
| --- | ---: | ---: |
| Century-eggs explanation (`11d2afb1`) | 100 | 88.242803 |
| Avoiding eggs and snacking on chocolate (`612fa3c5`) | 65 | 57.263857 |
| Coffee with raw egg yolk (`f4c5aa5f`) | 50 | 43.724941 |
| Mixed diary with hens and egg preparations (`eaa6a5e6`) | 37 | 33.703212 |
| Four-egg dinner (`fbd52a1d`) | 28 | 24.147853 |
| Duck-egg breakfast burrito (`ee3404d5`) | 22 | 18.182663 |
| Rocket stove (`99e6a514`) | 7 | 6.764276 |

The seven clear passes do not establish general ordering quality or production
adoption. PPv30-subject-v2 is tested, not production-frozen; the compound-SP
choice still defeats the user's coffee/places distinction in the final order.

The user authorized testing the coffee/places distinction in prominence while
keeping relevance unchanged. Tested experimental candidate
[PPv30-subject-v2](prominence-prompt-goal-v1/ppv30-subject-v2/PPv30-subject-v2.md)
replaces only v1's permission for meaning to concern multiple subjects with an
instruction to distinguish the meaning about each subject, including within
one statement, and divide the allocated points accordingly. Details developing
the SP subject itself still count; descriptive words are not automatically
separate subjects. The prompt contains no post-specific examples or expected
orders. Its shared revision receipt records the full delta against approved
main prompt PPv26, which remains unchanged. The reusable spec is
`experiment_specs/ppv30-subject-node-orders-v2.json`.

`experiments/ppv30-subject-node-orders-v2` was prepared with `--from` the v1
experiment and the new prompt. All 37 case IDs, subject/post inputs, review
evidence and runner settings match exactly. The original expected order check
failed before the revision: roasting's 89.083045 was below the short post's
93.490294. The new run completed 37 valid cases from 33 new Astra-low subscription
assessments and four exact-request reuses within the run. There were no failures,
retries, baseline reruns, new SP calls or new SSE worker calls. New-attempt usage
was 23,028 input tokens and 6,095 output tokens, including 640 reasoning tokens;
the $0.53503 catalog estimate is not an invoice or measured subscription quota.
There was no incremental cash charge or paid fallback. The 35 changed and two
unchanged response comparisons describe text changes, not ordering quality.

`relevance-v1` was prepared with the same vectors, worker settings, five replays
and `--post-order highest`, reusing the original completed context encoding with
`--reuse-encoding`. Collection used the existing raw vectors directly. All 37
contexts, subjects, cosine values and title cosines are unchanged; raw-vector
and receipt hashes and replay parity match exactly. Each allocation, sorting
score, independently selected post maximum and complete order was verified.
The shared experiment and prominence-cosine suites passed 91 tests; no workflow
implementation or production ranking code changed.

The Coffee assessment now allocates 65 points to continuing coffee experiences
and 35 to their setting, of which ten count toward Coffee and 25 toward places:
Coffee prominence is 75. Roasting's Coffee assessment assigns 96 points to
Coffee and four to community-tagging/hot-take framing. These percentages are
experimental assessments, not user-approved values. The distinction is visible
in the Coffee entries, but the final post order still reverses the tentative
preference because the highest sorting score can come from another SP subject:

| Post / SP subject | Prominence | Relevance | Sorting score |
| --- | ---: | ---: | ---: |
| A: More coffee in cool places / Coffee | 75 | 0.934903 | 70.117721 |
| A: More coffee in cool places / Continued experiences of coffee in appealing places | 100 | 0.868609 | 86.860927 |
| B: Roasting your own beans / Coffee | 96 | 0.890830 | 85.519723 |

A's highest sorting-score case is now `context-80cc7d69d7a09c762d6412a9`, whose
SP subject includes both coffee and places. The post uses 86.860927 rather than
its Coffee entry's 70.117721, so it remains above B's 85.519723. Prominence alone
also puts A's highest value, 100, above B's 96. The prompt change therefore does
not resolve this separate tentative ordering check. Aggregation remains the
original tested rule and is not changed or approved for production.

Both prominence alone and the sorting score still match the seven clear checks:

| Hierarchy node | Expected higher / lower | Highest subject prominence | Highest sorting score |
| --- | --- | --- | --- |
| coffee | Decaf / Sunday weather | 70 > 35 | 63.108260 > 28.819013 |
| Eggs | Century eggs / rocket stove | 100 > 7 | 88.242803 > 6.764276 |
| Eggs | Mixed diary / rocket stove | 37 > 7 | 33.703212 > 6.764276 |
| coffee | Roasting / errands | 96 > 60 | 85.519723 > 41.622349 |
| Eggs | Mixed diary / four-egg dinner | 37 > 28 | 33.703212 > 24.147853 |
| coffee | Iced coffee / errands | 95 > 60 | 85.118002 > 41.622349 |
| coffee | Roasting / second coffee | 96 > 55 | 85.519723 > 50.947210 |

The earlier about-equal pair remains separate: another coffee has highest
prominence 53 and sorting score 44.899125; errands has 60 and 41.622349. The
sorting-score difference is 3.276776 in the tentatively preferred direction,
without an agreed closeness tolerance. It is not counted as passed.

Complete v2 orders, descending by highest sorting score:

Coffee:

| Post (note-ID prefix) | Highest subject prominence | Highest sorting score |
| --- | ---: | ---: |
| More coffee in cool places (`37f44e1f`) | 100 | 86.860927 |
| Roasting your own beans (`056e6466`) | 96 | 85.519723 |
| Iced coffee served in ice (`76e19c3e`) | 95 | 85.118002 |
| Is there coffee for me? (`78462b92`) | 95 | 79.015156 |
| Coffee with raw cream and raw egg yolk (`f4c5aa5f`) | 100 | 75.582818 |
| Decaf drinkers (`2dc50a30`) | 70 | 63.108260 |
| Half & half versus cream (`143fee76`) | 60 | 53.835014 |
| Hashtag-heavy second-coffee post (`862486d8`) | 55 | 50.947210 |
| Another coffee and Sunday wishes (`737eaa89`) | 53 | 44.899125 |
| Afternoon errands and morning coffee (`e0508834`) | 60 | 41.622349 |
| Sunday weather with hot coffee (`82d3d344`) | 35 | 28.819013 |
| Coffee, movement and stretching (`8a025f69`) | 25 | 23.930048 |
| Duck-egg breakfast burrito and coffee (`ee3404d5`) | 25 | 22.274436 |
| Tolstoy quotation with Coffee hashtag (`be8d07d4`) | 1 | 0.917359 |

Eggs:

| Post (note-ID prefix) | Highest subject prominence | Highest sorting score |
| --- | ---: | ---: |
| Century-eggs explanation (`11d2afb1`) | 100 | 88.242803 |
| Avoiding eggs and snacking on chocolate (`612fa3c5`) | 65 | 57.263857 |
| Coffee with raw egg yolk (`f4c5aa5f`) | 50 | 43.724941 |
| Mixed diary with hens and egg preparations (`eaa6a5e6`) | 37 | 33.703212 |
| Four-egg dinner (`fbd52a1d`) | 28 | 24.147853 |
| Duck-egg breakfast burrito (`ee3404d5`) | 22 | 18.182663 |
| Rocket stove (`99e6a514`) | 7 | 6.764276 |

The seven clear passes do not establish general ordering quality or production
adoption. PPv30-subject-v2 is tested, not production-frozen; the compound-SP
choice still defeats the user's coffee/places distinction in the final order.

The user next authorized using the hierarchy node title as prominence input for
every post in that node, keeping relevance and the sorting-score formula fixed.
Tested experimental candidate
[PPv30-node-v1](prominence-prompt-goal-v1/ppv30-node-v1/PPv30-node-v1.md)
retains v2's meaning allocation and distinction between subjects, but assesses
the topic named by the hierarchy node title. Its input is exactly `node_title`
and `post`; no SP subject or context is supplied to the prominence assessment.
The prompt contains no post-specific examples or expected orders. The shared
revision receipt records the full delta against approved main prompt PPv26,
which remains unchanged. The reusable spec is
`experiment_specs/ppv30-node-orders-v1.json`.

`prominence_basis: "node_title"` is a third supported choice in the existing
`subject_contexts` adapter. The default context input and explicit SP-subject
input retain their previous contracts. Tests through the shared CLI verify
node-title/post rendering, SP evidence retention, reuse across SP entries in
the same node, separation between different node titles, refusal to reuse an
old assessment for a changed title, and reuse on a later matching experiment.
The shared cosine test collects common post prominence with the unchanged SP
context encodings and checks the resulting post maximum. Both tests failed
before implementation because `node_title` was unsupported, then passed. The
experiment, cosine, ranking, node-sorting, worker and extraction suites passed
202 tests. No production ranking implementation changed.

`experiments/ppv30-node-orders-v1` was prepared from the reusable spec with the
completed v2 experiment as baseline. All 37 case IDs, source evidence and runner
settings match exactly; only the prominence input and prompt change. The shared
comparison correctly records all 37 baseline inputs as `input_mismatch`, rather
than reusing assessments of different subjects. All 37 new cases are valid:
21 new Astra-low subscription assessments and 16 exact-request reuses within
this run. This gives one assessment per post/node across Coffee's 14 posts and
Eggs' seven posts. There were no failures, retries, baseline reruns, new SP calls
or new SSE worker calls. New-attempt usage was 14,837 input tokens and 3,406
output tokens, including 307 reasoning tokens; the $0.31867 catalog estimate is
not an invoice or measured subscription quota. There was no incremental cash
charge or paid fallback.

`relevance-v1` reuses the original completed context encoding exactly. All 37
contexts, SP subjects, cosine values and title cosines match v2; raw-vector and
receipt hashes and five replay checks are identical. All allocations, input
payloads, common prominence values per post/node, sorting scores, independent
post maxima and complete orders were checked. With prominence common across a
post's SP entries, its highest sorting score equals that prominence multiplied
by its highest unchanged SP-context relevance. The existing maximum rule and
formula remain unchanged; a broader SP subject cannot substitute a different
prominence assessment.

The short post's Coffee assessment allocates 70 points to continuing coffee
experiences and 30 to the appeal of the places. All five SP entries receive that
same prominence 70. Roasting's Coffee assessment assigns 98 points to Coffee and
two to its community check-in. These percentages are experimental assessments,
not user-approved values. The final sorting scores now follow the separate
tentative preference:

| Post | Common Coffee prominence | Highest SP-context relevance | Highest sorting score |
| --- | ---: | ---: | ---: |
| A: More coffee in cool places (`37f44e1f`) | 70 | 0.934903 | 65.443206 |
| B: Roasting your own beans (`056e6466`) | 98 | 0.890830 | 87.301384 |

In Coffee/Eggs, the sorting score matches all ten clear checks; prominence
alone matches nine:

| Hierarchy node | Expected higher / lower | Node-title prominence | Highest sorting score |
| --- | --- | --- | --- |
| coffee | Decaf / Sunday weather | 100 > 35 | 90.154658 > 28.819013 |
| Eggs | Century eggs / rocket stove | 100 > 8 | 88.242803 > 7.730602 |
| Eggs | Mixed diary / rocket stove | 42 > 8 | 38.818971 > 7.730602 |
| coffee | Roasting / errands | 98 > 60 | 87.301384 > 41.622349 |
| Eggs | Mixed diary / four-egg dinner | 42 > 26 | 38.818971 > 22.423007 |
| coffee | Iced coffee / errands | 95 > 60 | 85.118002 > 41.622349 |
| coffee | Roasting / second coffee | 98 > 70 | 87.301384 > 64.841903 |
| Eggs | Mixed diary / coffee with raw egg yolk | 42 > 35 | 38.818971 > 32.538029 |
| coffee | Coffee with raw egg yolk / More coffee in cool places | 100 > 70 | 75.582818 > 65.443206 |
| coffee | Iced coffee / coffee with raw egg yolk | 95 < 100: fails | 85.118002 > 75.582818 |

On September 30, the user reviewed the complete mixed diary (`eaa6a5e6`) as A
and coffee with raw cream and raw egg yolk (`f4c5aa5f`) as B inside Eggs, with
the image URL omitted, and answered "A". This adds an eighth clear expected
order. The node-title trial already puts the diary first, whereas v2 put the
raw-egg-yolk coffee post first (43.724941 > 33.703212). The user approved this
order, not the assessed percentages, formula or production adoption. No new
model calls, encoding, prompt edits or sorting calculations were needed.

The tentative roasting/short-post judgment remains separate from the ten
clear-check count. The earlier about-equal pair also remains separate: another
coffee has prominence 50 and sorting score 42.357665; errands has 60 and
41.622349. The difference is 0.735316 in the tentatively preferred direction,
without an agreed tolerance or a claim that closeness passed.

The user next reviewed the complete decaf-drinkers post (`2dc50a30`, A) and
roasting post (`056e6466`, B) inside Coffee, with the image URL omitted, and
answered "hm i'd say they're about the same" on September 30. Record about
equal with no preferred direction, separately from the ten clear orders.
PPv30-node-v1 assigns prominence 100 and 98 and sorting scores 90.154658 and
87.301384 respectively, a difference of 2.853274. No numeric tolerance or tie
rule was approved, so this comparison is not counted as passed or failed.
The user did not approve the assessed percentages, formula or production
adoption. No new inference, encoding or prompt change was needed.

The user then reviewed coffee with raw cream and raw egg yolk (`f4c5aa5f`, A)
against More coffee in cool places (`37f44e1f`, B) inside Coffee, showing the
complete wording with the image URL omitted, and answered "A". This adds the
ninth clear expected order. PPv30-node-v1 already follows it: prominence
100 > 70 and sorting score 75.582818 > 65.443206. V2 reversed it
(75.582818 < 86.860927), while prominence alone tied at 100. The user approved
the post order, not the percentages, formula or production adoption. No new
inference, encoding or prompt change was needed.

The user next reviewed the complete Sunday-weather post (`82d3d344`, A) and
coffee, movement and stretching post (`8a025f69`, B) inside Coffee. After an
explanation of prominence, SP-context relevance and the sorting-score formula,
the user said "A seems more related to coffee", then clarified that the
difference is "pretty subtle". A's "glad the coffee is hot this AM" is about
the same as B's "fetching coffee as a ritual of motion"; A also has
`#coffeechain`, which is "prob the tie breaker". Record a slight, tentative
preference for A separately from the ten clear orders, with the main coffee
statements about equal. This supersedes the earlier clear-order classification.
Both posts have prominence 35. Relevance still favors B, producing sorting
scores 28.819013 < 33.502067, opposite to the slight preference. Prominence
alone ties them; no numerical tolerance or exact percentages were approved.
The complete-post prominence input includes A's `#coffeechain`; its 35-point
coffee allocation describes sharing with the coffee community. This does not
isolate how much meaning the hashtag contributes.
A's selected SP context is "'Glad the coffee is hot this AM!' explicitly
identifies hot coffee." Its cosine with the node title is 0.646801, giving
relevance 0.823400. Neither of A's two saved SP contexts mentions `#coffeechain`.
B's context is "The writer describes fetching coffee." Its cosine is
0.914404, giving relevance 0.957202. The preceding PPv30-subject-v2
trial used those identical contexts and relevance values, but B's prominence
was 25 rather than 35, giving sorting score 23.930048 below A's 28.819013.
The node-title trial changed the prominence assessment; relevance was reused
unchanged. Removing relevance would leave a tie and would not express the
slight preference for A. This review does not approve revised percentages, a new
relevance input, formula or production adoption. No new inference, encoding
or prompt change was needed.

The user authorized a two-post relevance diagnostic using the original coffee
statements, including A's `#coffeechain`, with prominence and the sorting-score
formula fixed. The saved PPv30-node-v1 prominence assessments are both 35; no
new prominence or SP calls were made. The shared `prominence_cosine.py prepare`
source-text option verifies both statements against the complete original posts
and retains the original SP evidence. The inputs are exactly:

- A (`82d3d344`, `context-44202493a51f611a1448bd9a`):
  `Glad the coffee is hot this AM!`, then a blank line, then `#coffeechain`.
- B (`8a025f69`, `context-d8d12ef0759430f4cc75b15e`):
  `Fetching coffee as a ritual of motion`.

The source spans are respectively `[[107, 152]]` and `[[106, 143]]`. The output
is `experiments/ppv30-node-orders-v1/original-coffee-statements-v1`. One local CPU
SSE run encoded five rows: the unchanged `coffee` title, the two statements and
two original MP-mask replays (V0862 and V0601). Both replay cosines exceeded
0.9999999999999, with maximum normalized component error below 3.1e-8.
Checkpoint, base-model artifact hashes, model settings, batch size and worker
code match the SP-context encoding. Runtime packages differ: this run used
Python 3.13.12, torch 2.13.0+cpu, transformers 4.57.1 and tokenizers 0.22.2;
the SP-context baseline used Python 3.12.3, torch 2.12.1+cu130, transformers
5.17.0 and tokenizers 0.23.2. The replay checks establish agreement for those
original selections, not identical runtime metadata or every possible input.
The first local startup stopped while importing torch because `libstdc++.so.6`
was missing from the process library path, before inference or output creation.
The installed library path resolved it without installing packages, accessing
the network or changing the frozen inputs. Logs are preserved with the ignored
artifacts. No paid resource or provider request was used.

| Post | Fixed prominence | SP-context relevance | Original-statement relevance | Previous sorting score | New sorting score |
| --- | ---: | ---: | ---: | ---: | ---: |
| A: Sunday weather and hot coffee | 35 | 0.823400 | 0.836787 | 28.819013 | 29.287528 |
| B: Coffee, movement and stretching | 35 | 0.957202 | 0.907297 | 33.502067 | 31.755387 |

B remains higher. The sorting-score gap narrows from 4.683055 to 2.467859,
but the direction still reverses the separate slight preference for A.
Both the wording and inclusion of the hashtag changed relative to SP-context
input, and runtime package versions differ, so this is not an isolated
measurement of the hashtag's contribution.
It covers only these two cases and does not adopt a new relevance rule or
update the complete node orders. The source-text CLI test failed before the
option existed, then passed; the experiment, cosine, ranking, node-sorting,
worker and extraction suites passed 211 tests. The test exercises preparation
and collection, verifies unchanged prominence/evidence and exact UTF-8 source
text, and rejects rewritten/empty text, duplicate/unknown cases and mismatched
encoding reuse. PPv30-node-v1 remains tested, not production-frozen.

The subsequent authorized hashtag diagnostic uses the same shared CLI and
saved PPv30-node-v1 cases, with only A's standalone relevance text changed to
`Glad the coffee is hot this AM!` at original-post byte spans `[[107, 138]]`.
The blank line and `#coffeechain` are removed from that input; the complete
original post and prominence assessment still contain the hashtag. The output
is `experiments/ppv30-node-orders-v1/coffee-hashtag-without-v1`.
The five-row request retains the same title, B statement, V0862/V0601 original
MP-mask replays and row positions. The local CPU worker uses the identical
checkpoint, base-model artifact hashes, model settings, batch size, worker code
and runtime metadata as `original-coffee-statements-v1`: Python 3.13.12,
torch 2.13.0+cpu, transformers 4.57.1 and tokenizers 0.22.2. It uses the same
installed library path, offline settings and two CPU threads. One encoding
completed without a retry, provider request, package install or paid resource.
All four unchanged control vectors reproduce byte for byte. Both original
MP-mask replay checks pass with the same errors below 3.1e-8. The saved
with-hashtag artifacts remain unchanged.

| Relevance input | Fixed prominence | Cosine with `coffee` | Relevance | Sorting score |
| --- | ---: | ---: | ---: | ---: |
| A: `Glad the coffee is hot this AM!` | 35 | 0.572687 | 0.786343 | 27.522017 |
| A: same statement, blank line and `#coffeechain` | 35 | 0.673573 | 0.836787 | 29.287528 |
| B: `Fetching coffee as a ritual of motion` | 35 | 0.814594 | 0.907297 | 31.755387 |

Including the hashtag increases A's relevance by 0.050443 and sorting score
by 1.765511. B remains above A in both versions. This isolates including the
blank line and hashtag in this exact standalone relevance input; it does not
establish a general hashtag bonus, assess new prominence or change the user's
separate slight preference for A. Receipt/input hashes, source spans, row
identities, runtime equality, preserved baseline hashes and independently
recomputed cosines and sorting scores all pass. The focused prominence-cosine
suite passed 11 tests; its log is preserved with the ignored experiment artifacts.
The workflow code, prompts, original complete-node results and production
status remain unchanged.

The user subsequently reviewed the complete raw-cream/egg-yolk coffee post
(`f4c5aa5f`, A) against iced coffee served in ice (`76e19c3e`, B), inside Coffee
with media URLs omitted, and answered "B". Record iced coffee above the
raw-cream/egg-yolk coffee post as the tenth clear expected order. A's complete
wording is `Made my coffee with raw cream and a raw egg yolk today #coffeechain`;
B's is `Iced coffee, served in ice`, then a blank line and `📹 wolf.0313`, with
the two media URLs omitted from the review. The original posts remain intact.
The saved `relevance-v1` comparison supplies these unchanged values:

| Post | Coffee prominence | Highest SP-context relevance | Highest sorting score |
| --- | ---: | ---: | ---: |
| A: Coffee with raw cream and raw egg yolk | 100 | 0.755828 | 75.582818 |
| B: Iced coffee served in ice | 95 | 0.895979 | 85.118002 |

B's highest sorting-score entry is `context-22008019e5987f70ab3df075`, with SP
context "The post names iced coffee as the drink being served." A's is
`context-1a161fcf30ad4a372fcaabe4`, with "The writer reports making coffee today
with raw cream and a raw egg yolk." Multiplying the saved prominence by
relevance puts B first, matching the user; prominence alone puts A first.
The original comparison and encoding hashes are unchanged. No new teacher
calls, encoding, prompt changes or saved-result modifications were needed.
This is the first clear reviewed pair in PPv30-node-v1 where including
relevance changes the direction to the expected order: the sorting score
matches all ten clear checks, prominence alone nine. The about-equal judgments
and separate slight weather preference remain uncounted. One such case does
not establish a general advantage or select a production formula.

The user then reviewed roasting your own beans (`056e6466`, A) against
"Is there coffee for me?" (`78462b92`, B) inside Coffee, with complete wording
and image URLs omitted, and said "they seem decently evenly matched. maybe A".
Record roughly equal with a tentative preference for A, separately from the
ten clear checks. Saved PPv30-node-v1 values are unchanged:

| Post | Coffee prominence | Highest SP-context relevance | Highest sorting score |
| --- | ---: | ---: | ---: |
| A: Roasting your own beans | 98 | 0.890830 | 87.301384 |
| B: Is there coffee for me? | 100 | 0.831738 | 83.173849 |

The sorting-score difference is 4.127535 in the tentatively preferred direction;
prominence alone points toward B. No numerical tolerance for closeness or tie
rule was approved, so this is not a passed or failed clear comparison. There
are now three separate about-equal judgments, alongside the tentative
roasting/coffee-places judgment and slight weather preference. The clear-check
counts remain ten for the sorting score and nine for prominence alone, out of
ten. No new inference, encoding, prompt change or saved-result modification
was needed; this review does not select a production formula.

**Photography: node-title prominence and SP-context relevance.**

The user reviewed all three distinct posts in the raw Jev Photography node
`S45e455e0be`, with complete wording, URLs omitted and no scores shown. The
answer "A, B, C" establishes one complete ordering judgment:

| Review label | Post (note-ID prefix) | Expected position |
| --- | --- | ---: |
| A | Forgot to take photos while cooking (`bca8827b`) | 1 |
| B | Island lunch with photographer credits (`d6628bf3`) | 2 |
| C | Tolstoy quotation with `#Photography` (`be8d07d4`) | 3 |

The authorized experiment is `experiments/ppv30-photography-node-v1`, prepared
using `experiment_specs/ppv30-photography-node-v1.json` and the production
`subject_contexts` adapter with `prominence_basis: "node_title"`. All five
direct masks (V0964, V0963, V0765, V0767, V0688) match six saved SP entries
across these three posts. Every prominence input contains only the unchanged
Photography title and complete original post; repeated post/title inputs are
identical. PPv30-node-v1, its schema, Astra-low subscription settings and the
prominence × relevance formula match the Coffee/Eggs node-title trial. The
shared run is bounded to three new attempts, with repeated requests reused.
The user order is review evidence, not a prompt input. This does not reuse the
older Photography mask-prominence/mask-vector calculation as the same method.

All six cases completed validly with three new assessments and three exact
request reuses, without failures or retries. Each post has common prominence
across its SP entries. Native generation accounting reports 2,499 input tokens,
611 output tokens and zero reported reasoning tokens, with no missing usage.
The $0.05554 catalog reference estimate is not a subscription invoice or quota
measurement; incremental cash is zero and no paid fallback was used.

The shared `prominence_cosine.py` workflow prepared `relevance-v1` and encoded
one standalone title, six complete standalone SP contexts and five original
MP-mask replay controls: twelve rows across ten encoder notes. The masks are
controls, not the relevance input. The local CPU worker uses the existing
sentence-t5-base/SSE checkpoint and model artifacts, 768 dimensions, maximum
512 tokens, unchanged pooling and batch size eight. Receipt runtime is Python
3.13.12, torch 2.13.0+cpu, transformers 4.57.1 and tokenizers 0.22.2. All five
replays passed (cosine at least 0.9999999999999624, maximum normalized component
error at most 3.285e-8). The collector validated protected hashes, request and
row identities, model settings and replay parity.

Sorting score remains `prominence * (clip(cosine, -1, 1) + 1) / 2`. Each post
uses its highest SP-context sorting score:

| Post | SP entries | Prominence | Highest SP-context relevance | Highest sorting score |
| --- | ---: | ---: | ---: | ---: |
| A: Forgot to take photos while cooking | 2 | 12 | 0.760010 | 9.120122 |
| B: Island lunch with photographer credits | 3 | 7 | 0.780966 | 5.466762 |
| C: Tolstoy quotation with `#Photography` | 1 | 1 | 0.870545 | 0.870545 |

The winning A entry is `context-de2c82937271074d2f85c96f`, with context "The
writer explicitly says they forgot to take photos." B uses
`context-7cf5810209f3518f2bca31fa`, with "'The respective ... Photographer'
identifies an unnamed photographer as a credit recipient." C uses
`context-a8b79d95c89b9cce65e811c8`, with "The hashtag #Photography explicitly
names photography."

A's assessment assigns 12 of 100 points to forgetting to take photos; B's
assigns ten to author/photographer credits, of which seven concern Photography;
C's assigns 15 to all hashtags, of which one concerns Photography. These are
experimental assessments, not approved percentages. Both prominence and
sorting score follow the user's A > B > C order; relevance alone gives
C > B > A. This one three-post order matches in all pair directions, but the
directions are not three independent judgments and are recorded separately
from the ten clear Coffee/Eggs pair checks. The three about-equal judgments and
tentative Coffee preferences retain their existing classifications. All three
Photography posts mention the subject briefly; this does not test posts
primarily about Photography or establish general sorting quality.

All allocations, exact node-title/post inputs, standalone context selections,
independently recomputed cosines/formulas and per-post maxima passed. The
shared experiment and prominence-cosine suites passed 107 tests; the log is
saved at `experiments/ppv30-photography-node-v1/workflow-tests.log`. The original
hierarchy, masked posts, vector map, Coffee/Eggs comparison and prompt hashes
are unchanged. Comparison SHA-256 is
`60fddf522334b14c1d834d4eb9ecfa6d5b3b893eb0b21eceb4b1b926464fbee6`.
No baseline calls, SP generation, prompt or source-code changes, membership
changes, paid resources or production rule adoption occurred. This run uses
the current local runtime; it does not claim the older Coffee/Eggs runtime
packages are identical. PPv30-node-v1 remains tested, not production-frozen.

**Music: node-title prominence and SP-context relevance.**

The user authorized the next node test, then reviewed complete wording with
URLs omitted and no sorting scores shown. A is the Baby Got Back/coffee-shop
post (`46ed60cb`); B is the island-lunch/photographer-credits post (`d6628bf3`)
with `#Music`. The answer "A" establishes a clear A > B Music pair before
inference. This judgment does not approve prominence percentages or a formula.

`experiments/ppv30-music-node-v1` uses the reusable specification
`experiment_specs/ppv30-music-node-v1.json` and the production subject-context
adapter with node-title prominence. Node `S9f8ab11969` has three direct masks
(V0522, V0528, V0770), matching three saved SP entries across two posts. Every
prominence input contains exactly the unchanged Music title and complete
original post. Prompt PPv30-node-v1, schema, Astra-low subscription settings,
standalone SP-context relevance and the prominence × relevance formula match
the preceding Coffee/Eggs and Photography node-title tests. Expected order is
kept only as review evidence. All three cases completed validly with two new
assessments and one exact-request reuse, without failures or retries. Native
generation accounting traces both original calls and reports 1,618 input
and 391 output tokens, including 59 reasoning tokens, with no missing usage.
The $0.03573 catalog reference estimate is not a subscription invoice or quota
measurement. Incremental cash is zero.

The shared `prominence_cosine.py` workflow prepared and collected `relevance-v1`.
One local CPU worker encoded seven rows: one standalone Music title, three
complete standalone saved SP contexts and three original MP-mask controls.
All three replays matched the original vectors exactly (cosine 1.0, maximum
normalized component error 0.0). Checkpoint, model artifacts, 768 dimensions,
512-token maximum, pooling and batch size eight match the preceding node-title
SP-context tests. Worker code and runtime match the Photography run: Python
3.13.12, torch 2.13.0+cpu, transformers 4.57.1 and tokenizers 0.22.2.

Sorting score remains `prominence * (clip(cosine, -1, 1) + 1) / 2`, and each
post uses its highest sorting score among its matching SP entries:

| Post | SP entries | Prominence | Highest SP-context relevance | Highest sorting score |
| --- | ---: | ---: | ---: | ---: |
| A: Baby Got Back playing in a coffee shop | 2 | 85 | 0.835578 | 71.024162 |
| B: Island lunch with `#Music` | 1 | 3 | 0.939429 | 2.818288 |

A's prominence assessment assigns 85 points to the song playing, enthusiasm
and music-community association, and 15 to the coffee-shop setting and
coffee-community association. B's assigns two points to a possible song
allusion in "Sitting,waiting, wishing" and one to the Music hashtag. That
possible allusion and the percentages are teacher assessments, not user
judgments. Both prominence and sorting score put A first, matching the prior
user answer; relevance alone favors B.

A's winning entry is `context-e590ad3dbf0eaec94cdb1bfd`, with SP context "The
writer tags the music-related post with #musicstr." Its other entry,
`context-283858545185a45fe46b887b`, has context "The post reports a named song
playing and includes the hashtag #musicstr.", relevance 0.815989 and sorting
score 69.359080. Both A entries use the same prominence 85. B uses
`context-7edfeaf44a6159063a4846a8`, with "#Music explicitly identifies music
as a subject."

With this additional clear pair, the tested method matches eleven of eleven
Coffee/Eggs/Music pair checks; prominence alone matches ten. The single
Photography three-post ordering judgment also matches and stays separate
from that count. Three about-equal Coffee judgments and the tentative
preferences stay uncounted. This Music pair does not show an added benefit
from relevance over prominence or select a production rule.

Exact inputs, all point allocations, standalone context selections, receipt
and protected-file hashes, row identities, independently recomputed cosines,
sorting-score formulas and per-post maxima passed. Eleven focused
prominence-cosine workflow tests passed; the log is saved at
`experiments/ppv30-music-node-v1/workflow-tests.log`. Comparison SHA-256 is
`0344a891768976b47b903ffb6d324195f881e38e373025c3f531b5c01b8aa20a`.
The original hierarchy, masked posts, vector map, prompt and Coffee/Eggs and
Photography comparisons remain unchanged. No baseline calls, SP generation,
prompt or source-code changes, paid resources or production adoption occurred.
PPv30-node-v1 remains tested, not production-frozen.

**Fresh prominence for iced coffee and raw-egg-yolk coffee.**

The user authorized reassessing these two posts while holding their existing
SP-context relevance fixed. The expected order is unchanged: iced coffee
(`76e19c3e`) above coffee with raw cream and raw egg yolk (`f4c5aa5f`). This is
an independent generation for the same existing pair judgment, not a new
user judgment or a replacement for the original Coffee/Eggs trial.

`experiments/ppv30-node-orders-repeat-iced-raw-v1` was prepared with:

```sh
python3 sse_multivector/experiment.py prepare \
  sse_multivector/experiments/ppv30-node-orders-repeat-iced-raw-v1 \
  --from sse_multivector/experiments/ppv30-node-orders-v1 \
  --only context-22008019e5987f70ab3df075 \
  --only context-1a161fcf30ad4a372fcaabe4 \
  --repeat --history-root sse_multivector/experiments
```

Both cases, complete inputs, PPv30-node-v1 prompt and Astra-low subscription
settings match their original cases exactly. `--repeat` requests two fresh
assessments rather than reusing their saved answers; two new attempts are
allowed. No baseline or SP calls, new SSE encoding, changed source text or
production sorting changes are included. Both independent assessments
completed validly with two new calls and zero reused answers, without failures
or retries. Native generation accounting reports 1,337 input and 193 output
tokens, including 48 reasoning tokens, with complete usage. The $0.02302
catalog reference estimate is not a subscription invoice or quota measurement;
incremental cash is zero.

The existing shared `--reuse-encoding` support now permits selecting a subset
of a completed encoding. It maps exact unchanged note/text/selection/span
identities to original rows and retains the full request for receipt
validation, including replay controls outside the selected posts. A production
CLI test first failed because partial notes were refused, then passed after
the minimal change. The test verifies changed prominence with identical
cosine, vector/receipt hashes, selected-node output and both selected and
unselected-post replay controls. Existing changed-text and modified-artifact
refusal checks still pass. The focused suite passes twelve tests; all 141 relevant
regression checks passed. Relevance was collected directly from the
original context encoding, preserving the original values exactly.

The first `relevance-v1` collector refused to proceed because an unrelated
concurrent addition of the `posts` adapter changed `experiment_inputs.py` after
preparation. Its frozen files are retained unchanged and no comparison was
emitted. Inspection confirmed that the prominence, context-prominence and
subject-context preparation functions were unchanged. A separate read-only
`relevance-v2` preparation froze the current code, using the same completed
prominence results and original encoding; collection passed. No model call,
embedding or failed receipt was retried. The current prominence-cosine and
experiment-selection suites subsequently passed all 22 tests.

`relevance-v2` retains the original 44-row encoder request and uses only the
two selected context rows and Coffee title for this comparison. All five
original MP-mask replay checks are preserved and pass exactly as before. Raw
vectors, worker receipt hashes and both relevance values match the original
Coffee/Eggs comparison exactly. No new worker ran and no result directory was
created for this collection.

| Post | Original prominence | Fresh prominence | Fixed relevance | Fresh sorting score |
| --- | ---: | ---: | ---: | ---: |
| Iced coffee served in ice (`76e19c3e`) | 95 | 95 | 0.895979 | 85.118002 |
| Coffee with raw cream and raw egg yolk (`f4c5aa5f`) | 100 | 100 | 0.755828 | 75.582818 |

The fresh iced-coffee assessment assigns 95 points to its unusual serving
method and five to crediting the video's creator. The fresh raw-egg-yolk
assessment assigns all 100 points to preparing coffee and its ingredients,
shared with a coffee-related hashtag. These are new teacher assessments,
not approved percentages. Multiplying by the original relevance values repeats
the earlier expected direction exactly; prominence alone still puts raw-egg-yolk
coffee first. This is one additional successful trial of the same judged pair,
not a new pair or a general demonstration that relevance improves sorting.
Original eleven-pair results and the separate Photography ordering judgment
remain intact. Formula adoption and production sorting remain open.

Exact original case inputs/settings, independent generation provenance, all
point allocations, selected-row identities, frozen-source hashes, preserved
vectors/receipts/replay results, independently recomputed cosines and sorting
scores, and per-post maxima passed. Comparison SHA-256 is
`7df9193c3c8b0c1c68a5d7b3efd23e72daf8d990e1b62cbd20f288f3a3a86577`.
Failing-first, regression and current-code check logs are preserved in the
ignored experiment directory. Original hierarchy, masked posts, vector map,
prompt and Coffee/Eggs, Photography and Music comparisons are unchanged. No
baseline generation, SP calls, new encoding, paid resource, prompt edits or
production ranking changes occurred.

**Decaf versus a coffee request: tentative about-equal judgment.**

The user reviewed the complete decaf-drinkers post (`2dc50a30`, A) and
"Is there coffee for me?" (`78462b92`, B) inside Coffee, with B's image URL
omitted and no sorting scores shown, and answered "about equal maybe".
Record tentative about equality with no preferred direction, separately
from the eleven clear Coffee/Eggs/Music pairs and the Photography ordering
judgment. This makes four about-equal Coffee judgments. The later approval
below accepts either order for these pairs and leaves numerical tolerance and
production tie handling unspecified.

The unchanged original `ppv30-node-orders-v1/relevance-v1` results give:

| Post | Prominence | Highest SP-context relevance | Highest sorting score |
| --- | ---: | ---: | ---: |
| A: Decaf drinkers | 100 | 0.901547 | 90.154658 |
| B: Is there coffee for me? | 100 | 0.831738 | 83.173849 |

A's winning entry is `context-35e7f2bb8ff33f9b31f98632`, with SP context
"The post discusses coffee, contrasting decaffeinated coffee drinking with
caffeine-driven consumption." B's is `context-d3139bbd11ca832d461643a4`,
with "The post explicitly asks, 'Is there coffee for me?' and includes a
coffee-cup emoji." Both complete-post prominence assessments give 100.
The common prominence means the 6.980809 sorting-score difference toward A
comes entirely from the saved relevance values; prominence alone ties them.
The user did not approve this numerical gap, select a tie rule, reject the
relevance calculation or authorize changing it.

Native `show --case` evidence, per-post maxima and independently recomputed
relevance/products match the saved comparison. Its SHA-256 remains
`77f1e9bf073a504f76b26d1c8f667df85254fefc1640d94d4cf575c6bf51bbec`.
No new teacher calls, encoding, prompt changes or saved-result modifications
were needed. The original clear-check counts remain eleven matched sorting
orders and ten matched prominence orders out of eleven; this tentative
about-equal judgment stays outside those counts. Production sorting remains
open.

**About-equal judgments: either order is acceptable.**

The user answered "sure" to "For pairs you judge about equal, is either order
acceptable?" Either direction is now acceptable for the four reviewed Coffee
pairs: another coffee/Sunday wishes versus errands; decaf versus roasting;
roasting versus "Is there coffee for me?"; and decaf versus that coffee request.
The two tentative small preferences remain recorded, but the opposite orders
are also acceptable. Both saved prominence-only and sorting-score orders meet
this condition for all four pairs. Keep these pairs separate from the eleven
clear expected orders and Photography's three-post judgment, because they do
not distinguish between the two calculations.

This approval does not require equal sorting scores or set a numerical gap
limit. It does not identify unreviewed pairs as about equal or select production
tie handling. Prominence, relevance, formula, prompts, code and saved results
are unchanged; no new model calls or encoding were needed.

Complete original node-title prominence orders, using saved SP-context
relevance and descending by highest sorting score:

Coffee:

| Post (note-ID prefix) | Coffee prominence | Highest sorting score |
| --- | ---: | ---: |
| Decaf drinkers (`2dc50a30`) | 100 | 90.154658 |
| Roasting your own beans (`056e6466`) | 98 | 87.301384 |
| Iced coffee served in ice (`76e19c3e`) | 95 | 85.118002 |
| Is there coffee for me? (`78462b92`) | 100 | 83.173849 |
| Coffee with raw cream and raw egg yolk (`f4c5aa5f`) | 100 | 75.582818 |
| More coffee in cool places (`37f44e1f`) | 70 | 65.443206 |
| Hashtag-heavy second-coffee post (`862486d8`) | 70 | 64.841903 |
| Half & half versus cream (`143fee76`) | 70 | 62.807517 |
| Another coffee and Sunday wishes (`737eaa89`) | 50 | 42.357665 |
| Afternoon errands and morning coffee (`e0508834`) | 60 | 41.622349 |
| Coffee, movement and stretching (`8a025f69`) | 35 | 33.502067 |
| Sunday weather with hot coffee (`82d3d344`) | 35 | 28.819013 |
| Duck-egg breakfast burrito and coffee (`ee3404d5`) | 25 | 22.274436 |
| Tolstoy quotation with Coffee hashtag (`be8d07d4`) | 1 | 0.917359 |

The user reviewed the complete original wording of all fourteen Coffee posts
in the displayed order, with URLs omitted, and answered "lgtm". Record one
accepted full-node Coffee order, exactly as shown above, alongside the accepted
seven-post Eggs order below. Keep both separate from the eleven clear
Coffee/Eggs/Music pair checks, Photography's three-post judgment and the four
about-equal Coffee comparisons. Do not count this review as 91 independent
pair judgments or infer strict differences between every adjacent post.

The accepted Coffee order includes coffee/movement/stretching above Sunday
weather/hot coffee. The earlier slight weather preference remains recorded;
its opposite direction is acceptable in this complete-order review. All
fourteen post maxima and sorting-score products match the unchanged original
comparison, whose SHA-256 remains
`77f1e9bf073a504f76b26d1c8f667df85254fefc1640d94d4cf575c6bf51bbec`.
This approves the displayed order, without selecting numerical values, the
formula or production adoption. Prompts, calculations and saved results are
unchanged; no new teacher calls or encoding were needed.

Eggs:

| Post (note-ID prefix) | Eggs prominence | Highest sorting score |
| --- | ---: | ---: |
| Century-eggs explanation (`11d2afb1`) | 100 | 88.242803 |
| Avoiding eggs and snacking on chocolate (`612fa3c5`) | 52 | 45.811085 |
| Mixed diary with hens and egg preparations (`eaa6a5e6`) | 42 | 38.818971 |
| Coffee with raw egg yolk (`f4c5aa5f`) | 35 | 32.538029 |
| Four-egg dinner (`fbd52a1d`) | 26 | 22.423007 |
| Duck-egg breakfast burrito (`ee3404d5`) | 25 | 20.662117 |
| Rocket stove (`99e6a514`) | 8 | 7.730602 |

The user reviewed the complete original wording of all seven Eggs posts in
the displayed order, with URLs omitted, and answered "lgtm". Record one
accepted full-node Eggs order, exactly as shown above. Both prominence alone
and sorting score give this order, so this review does not distinguish between
the two calculations. It remains separate from the eleven clear
Coffee/Eggs/Music pair checks, Photography's three-post judgment and the four
about-equal Coffee comparisons. Do not count it as 21 independent pair
judgments or infer strict differences between every adjacent post.

The seven post maxima and both complete orders were checked against the
unchanged original comparison, whose SHA-256 remains
`77f1e9bf073a504f76b26d1c8f667df85254fefc1640d94d4cf575c6bf51bbec`.
This is approval of the displayed order, not the numerical values, formula or
production adoption. Prompts, calculations and saved results are unchanged;
no new teacher calls or encoding were needed.

Relative to v2, 11 Coffee pair directions and one Eggs pair direction change.
The roasting/short-post direction matches the user's tentative judgment.
Putting the diary above coffee with raw egg yolk matches the new clear judgment.
Putting coffee with raw egg yolk above More coffee in cool places matches the
ninth clear judgment.
Putting coffee, movement and stretching above Sunday weather reverses the
earlier slight preference, but is acceptable in the subsequent complete Coffee
review; that tentative preference stays outside the eleven clear pair checks.
Decaf versus roasting was reviewed as about equal, with either order acceptable.
The full Coffee review accepts the displayed placements without establishing
additional independent pair judgments.
PPv30-node-v1 is tested, not production-frozen. These results do not
establish general ordering quality, calibrated percentages, production adoption
or a general advantage from relevance over prominence alone.

**Agent assessment across other subjects: PPv30-node-v1.**

On September 30, the user directed the agent to assess transfer to other
subjects from the established sorting examples, without asking for new user
ordering labels or user inspection of each order.

`experiment_specs/ppv30-transfer-nodes-v1.json` and its reusable source selector
use the native `subject_contexts` adapter with node-title prominence. The agent
selected all direct members of four existing raw-hierarchy nodes: Children
(`Sdd9ab7afc6`, five posts), Literature (`Scfde838bff`, four), Psychological
distress (`S69c628e2ff`, two), and Bitcoin
(`merged-6e49fa93d6348e573dd61acffecd6b266eaeeaf0219a48ffaeba5b88232ab730`, eight).
Native preparation validates twenty-five matching saved SP cases, with nineteen
distinct complete-post/title inputs. Repeated SP entries share the same
prominence request. No new subjects or masks are generated.

Prompt PPv30-node-v1, Astra-low subscription settings, relevance from standalone
SP context and node title, and highest sorting score per post remain unchanged.
The agent observes the complete resulting orders and compares prominence alone
with prominence × relevance, using the established distinction between meaning
about the topic, additional meaning and incidental mentions. About-equal
placements may appear in either order. These are agent assessments, not new
user judgments or an accuracy rate. Broader validation and production adoption
remain open.

The experiment is bounded to nineteen node/post inputs and at most thirty-eight
new attempts including only eligible provider retries. Input work is proportional
to selected node/post memberships and full-post length, with exact-request
reuse across SP entries; it does not compare all posts with all hierarchy nodes.
Local CPU SSE encodes only the selected contexts/titles and saved-mask replay
controls. The zero-cash subscription reservation is recorded in the lifetime
ledger; API-reference costs and subscription quota are separate. The selector,
preparation and protected inputs passed native validation. Original comparisons,
source data and prompt remain intact; no production code or rule changes occur.

The completed `experiments/ppv30-transfer-nodes-v1` run has twenty-five valid
cases: nineteen new assessments and six within-run exact-request reuses, with
no failures, invalid outputs or retries. These cover seventeen original posts
and nineteen post/node memberships, not twenty-five independent assessments.
Native usage is 15,087 input tokens, zero cached input, and 4,162 output tokens
including 448 reasoning tokens. The catalog reference is $0.35897, not a
subscription invoice or quota measurement; incremental cash is zero.

`relevance-v1` encodes twenty-five standalone SP contexts, four exact node
titles and four original-mask replay controls locally on CPU. The replay
cosines are at least 0.9999999999999446, with maximum normalized component
error 3.73e-8. Original masks are controls, not relevance inputs. The native
comparison SHA-256 is
`7c2f74c0026d1d014d0b3b618b56aa204db65d31e40094d57eefbf832df99f0f`.
All products, independently selected post maxima, complete orders and original
protected inputs were verified. The existing experiment-selection and
prominence-cosine suites passed twenty-two tests. No workflow implementation
changed.

Complete orders below descend by highest sorting score. Prominence alone gives
the same order in all four nodes. Relevance shown is from the winning SP context;
values are rounded for display, with products calculated from full precision.

Children:

| Post (note-ID prefix) | Prominence | Relevance | Sorting score |
| --- | ---: | ---: | ---: |
| Baby development and food interest (`cf50b578`) | 100 | 0.644050 | 64.405028 |
| Son's ice-cream conversation (`7e7eeee7`) | 55 | 0.515541 | 28.354729 |
| Lunchly market argument (`38862a72`) | 40 | 0.707843 | 28.313701 |
| Pancake recipe prompted by child (`4bb3dd6e`) | 15 | 0.668220 | 10.023303 |
| Mental clarity with passing mention of kids (`89cdcfbb`) | 5 | 0.758104 | 3.790522 |

Literature:

| Post (note-ID prefix) | Prominence | Relevance | Sorting score |
| --- | ---: | ---: | ---: |
| Diary discussing audiobooks and a murder mystery (`eaa6a5e6`) | 22 | 0.706732 | 15.548097 |
| Lifestyle list with reading advice (`05f275f4`) | 4 | 0.765525 | 3.062102 |
| Island lunch with Literature hashtag (`d6628bf3`) | 1 | 0.961959 | 0.961959 |
| Morning work routine, "first minutes written" (`8a025f69`) | 0 | 0.613817 | 0.000000 |

Psychological distress:

| Post (note-ID prefix) | Prominence | Relevance | Sorting score |
| --- | ---: | ---: | ---: |
| Personal chemotherapy update with anxiety framing (`5305db5e`) | 40 | 0.805911 | 32.236439 |
| Lifestyle list with stress advice (`05f275f4`) | 21 | 0.781278 | 16.406843 |

Bitcoin:

| Post (note-ID prefix) | Prominence | Relevance | Sorting score |
| --- | ---: | ---: | ---: |
| Bitcoin Pizza Day and planned restaurant acceptance (`7258eaac`) | 50 | 0.742142 | 37.107083 |
| Bitcoin workshop followed by a shared meal (`1c964a41`) | 35 | 0.831849 | 29.114720 |
| Criticism of the bitcoin carnivore narrative (`fbd37967`) | 18 | 0.777065 | 13.987178 |
| Second coffee with Bitcoin hashtag (`862486d8`) | 15 | 0.902435 | 13.536523 |
| Island-life/lunch post with Bitcoin heading and tags (`d6628bf3`) | 14 | 0.816560 | 11.431840 |
| Cheese Doodle Day with Bitcoin tags (`896b0a29`) | 10 | 0.863585 | 8.635846 |
| Workout/food/ice-cream joke with Bitcoin tags (`41efa59d`) | 6 | 0.926204 | 5.557222 |
| Animal-ethics quotation with Bitcoin/payment tags (`be8d07d4`) | 5 | 0.917214 | 4.586071 |

Agent observation found no clear wrong complete order. Developed discussion
leads each node; incidental mentions generally remain below it. The anxiety
hashtag frames a personal update rather than an unrelated tag list. The work
routine's "minutes written" does not establish discussion of literary writing;
its zero prominence is plausible, with node membership a separate question.
Directions among incidental Bitcoin posts are subtle. These observations use
the user's established preferences but do not create new user judgments or a
global accuracy rate. Literature and Psychological distress are small samples
with limited subject-focused discussion.

Relevance does not improve any complete order in this sample. It narrows two
potentially useful prominence differences: the son conversation remains above
the Lunchly argument by only 0.041028 sorting-score points, and the Bitcoin
community opinion remains above the second-coffee hashtag by 0.450655.
Neither is an observed reversal or a violation of an agreed numerical gap.
For Children, the exact contexts are "The writer's son eats the ice cream,
proposes using a plate, and confirms the reason" and "The product is discussed
as a lunch a mother buys for her child." Their cosines against Children are
0.031081 and 0.415685. This establishes the inputs and difference, not its cause;
the son's age is not specified. The two related Children cases are marked
agent `uncertain` through native review, with all twenty-five matching SP cases
inspected and separately recorded. The other twenty-three agent assessments
accept the plausible relative placements, not calibrated percentages.

The user authorized investigating the saved Children relevance difference on
October 1. The completed diagnostic is recorded below.
PPv30-node-v1 remains tested, not production-frozen. No prompt, formula, source
membership or previous user judgment changed, and no user review was requested.

**Children relevance diagnostic: fixed PPv30-node-v1 prominence.**

The original transfer request and worker receipt select every content token
of the eighty-five-byte SP context, with twenty-seven tokens including EOS.
The correct Children title is encoded separately; no context is truncated,
no word is omitted by span selection, and case IDs, vector rows and saved
sorting-score products match. The worker averages the selected contextual
token states before its existing projection. Here the selection covers the
complete SP context, including the ice-cream and plate details, rather than
only the subject wording.

Native `prominence_cosine.py prepare` created `children-short-source-v1` and
`children-story-source-v1` under the transfer experiment. Both select only
`context-641ea6563f1a2c0ab80ee60b` (son) and
`context-d4dcb5e113d5948405a18d4b` (Lunchly), with `--post-order highest`.
`--relevance-source-text` changes only the son's relevance input to an exact
original-post fragment: "My son" for the short comparison, and the opening
paragraph through "It is easier to eat all of the ice cream." for the story
comparison. Complete-post/title prominence remains 55 and 40; saved SP
subjects, contexts, masks and source posts are not edited. The Lunchly
SP-context input is an unchanged control.

Each native preparation contains five encoder rows: Children, original-mask
replays V1026 and V0064, the Lunchly context, and the son's exact source
fragment. Both run locally on CPU with the original checkpoint, model,
pooling and runtime packages. The title replay cosine is 1.0; original-mask
replay cosines are at least 0.9999999999999398, with maximum normalized
component error 3.78e-8. The control's sorting score differs from the original
by less than one millionth, consistent with the small batching-related vector
differences. Every request remains below the 512-token limit, with no
truncation. This is two bounded five-row comparisons, with no teacher
calls, prompt changes, paid resources or new execution code.

| Son's relevance input | Prominence | Relevance | Sorting score |
| --- | ---: | ---: | ---: |
| Saved SP context | 55 | 0.515541 | 28.354729 |
| Original words "My son" alone | 55 | 0.754024 | 41.471298 |
| Original opening ice-cream paragraph | 55 | 0.502639 | 27.645136 |

Lunchly remains at prominence 40, relevance 0.707843 and sorting score
28.313700 in both new comparisons. The original-story variant therefore puts
the son below Lunchly, reversing the agent's preferred direction; it is a
diagnostic input change, not a newly observed failure of the unchanged
SP-context candidate. The short phrase has no age claim either. SSE can
connect "My son" with Children; adding story detail greatly reduces that
connection in both the original prose and the saved context. This rules out
an SP summary-wording effect as the sole explanation and does not establish
the encoder's internal causal mechanism. The code's complete-context
selection and averaging are verified; the semantic interpretation remains
an agent assessment.

The separate original-mask comparison uses V1026's contextual selection
"My son" and "son", not standalone source wording or a subject vector. Its
relevance against the saved Children title is 0.774211, versus V0064's
"kid"/"lunch" relevance 0.804175. That supports checking the choice of
relevance input, without adopting mask relevance. A read-only check with the
same node-title prominence finds that original-mask relevance reverses the
accepted Coffee pair: iced coffee sorts at 93.756406 below raw-yolk coffee's
97.620856. Both inputs have SP subject Coffee; subject-only relevance likewise
cannot produce iced above raw-yolk when the fixed prominence is 95 versus
100, because the relevance multiplier would be identical and nonnegative.
Neither simpler input is a general correction established by this diagnostic.

The user then approved comparing relevance from SP subject plus the unchanged
SP context, keeping prominence and the sorting formula fixed and checking
all accepted Coffee, Eggs, Photography and Music orders as well as the four
transfer nodes. The completed comparison follows. This does not select a
production relevance input.

Both new native comparisons, fixed prominence, products, exact source spans,
unchanged control and protected original files passed verification. The
prominence-cosine suite passed twelve tests, including its production
preparation/collection path for source-text relevance. The son case retains
agent `uncertain` with a native review recording these findings and hashes;
no user decision was added. Comparison SHA-256:

- `children-short-source-v1`: `7d420910e012a2abf566e9f29293302e2ca97e3960820e8b0082430db0412457`.
- `children-story-source-v1`: `be7973a582b2de6e2b318c7d993e91f23fb9417d29561c34f85dc0ca583c01a8`.

**SP subject plus context: fixed PPv30-node-v1 prominence.**

The shared `prominence_cosine.py prepare --include-subject` option encodes
each saved SP subject followed by one newline and its unchanged saved context.
It requires the `subject_contexts` adapter and cannot combine with an exact
source-text override. Without the option, preparation still encodes context
alone. The plan identifies the new input as `subject_context`; original SP
fields, complete-post prominence inputs, masks and post aggregation remain
unchanged. Existing context-only encoding cannot be reused for the new text.
No arbitrary replacement context or per-post tuning is added.

The minimal production preparation/collection test first failed because only
the context was encoded. It now verifies the combined UTF-8 text and complete
byte selection, fixed prominence and source evidence, original-mask control,
CLI option, resulting sorting score, unchanged default and invalid input/reuse
rejection. Nineteen comparison/ranking tests and 118 experiment, selection and
worker regression tests passed. No production extraction, worker, teacher
prompt, sorting formula or recursive transfer implementation changed.

`experiments/ppv30-subject-context-relevance-v1` uses all saved cases from
`ppv30-node-orders-v1`, `ppv30-photography-node-v1`, `ppv30-music-node-v1` and
`ppv30-transfer-nodes-v1`. There are seventy-one SP entries across forty-five
post/node memberships in eight nodes. The native preparation encodes eight
titles, seventy-one subject/context texts and ten original-mask controls:
eighty-nine rows in the same local CPU worker. Each input adds only one saved
SP subject to its context; encoding work grows with the selected entries.
There are no new complete-post teacher inputs or outputs, global all-post/all-
node evaluation, provider calls or paid resources. Every encoded input is
within the existing 512-token limit; the maximum observed length is 478.

The completed run used this native preparation command, then the generated
worker configuration and native collection:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/prominence_cosine.py prepare \
  sse_multivector/experiments/ppv30-subject-context-relevance-v1 \
  --experiments \
  sse_multivector/experiments/ppv30-node-orders-v1 \
  sse_multivector/experiments/ppv30-photography-node-v1 \
  sse_multivector/experiments/ppv30-music-node-v1 \
  sse_multivector/experiments/ppv30-transfer-nodes-v1 \
  --include-subject --post-order highest \
  --vectors sse_multivector/hierarchy-refresh-v1 \
  --worker-config sse_multivector/experiments/ppv30-transfer-nodes-v1/relevance-v1/worker-config.json \
  --replay V0507 V0882 V1268 V0964 V0522 V1026 V0064 V1051 V1063 V0794
```

The completed directory is immutable; use a new output path for a deliberate
repeat. Its native comparison SHA-256 is
`57985e0d3ff19059b67fe3224dc3e6f3d97b5677b776313cda7ef8cd9496792d`.
All ten controls pass: replay cosine is at least 0.9999999999999452 and maximum
normalized component error at most 4.08e-8. Original prompt, teacher receipts,
SP/MP data, source hierarchy and preceding comparisons retain their hashes.
All seventy-one sorting-score products and forty-five post maxima were
verified; all prominence-only orders remain identical.

| Hierarchy node | Posts | Change from context-only sorting order |
| --- | ---: | --- |
| coffee | 14 | Only errands/another-coffee swap; either direction already accepted |
| Eggs | 7 | Identical |
| Photography | 3 | Identical |
| Music | 2 | Identical |
| Children | 5 | Identical |
| Literature | 4 | Identical |
| Psychological distress | 2 | Identical |
| Bitcoin | 8 | Identical |

All eleven clear Coffee/Eggs/Music comparisons retain their accepted directions.
The accepted seven-post Eggs order and three-post Photography order remain
exactly intact, separately from that count. Coffee's only change puts errands
at 45.192466 above another coffee at 44.407089, rather than 41.622349 below
42.357665. The user judged this pair about equal and subsequently accepted
either direction. The other three about-equal judgments remain acceptable;
none is converted into a strict pair or numerical gap test. No new user
judgments or global accuracy claims are added.

The targeted Children result changes only slightly:

| Post | Fixed prominence | Context-only relevance | Subject plus context relevance | New sorting score |
| --- | ---: | ---: | ---: | ---: |
| Son's ice-cream conversation (`7e7eeee7`) | 55 | 0.515541 | 0.541385 | 29.776167 |
| Lunchly market argument (`38862a72`) | 40 | 0.707843 | 0.739939 | 29.597540 |

The son's lead rises from 0.041028 to 0.178627 sorting-score points; the relative
order is retained and no agreed minimum gap exists. Adding the subject has not
removed the earlier concern about the context's low relevance to Children.
The four transfer orders remain plausible on agent inspection, with Literature
and Psychological distress still small samples. Native agent reviews record
the two Children uncertainties and the acceptable Coffee swap, bound to this
comparison hash; existing user judgments remain unchanged.

The agent recommended retaining context-only relevance for the next broader
subject trial: in this eight-node comparison, the additional input gave little
benefit and corrected no demonstrated wrong order. The larger October 1
comparison below subsequently corrects a newly observed restaurant reversal.
Testing more non-food subjects for actual ordering
failures was recommended and the user subsequently approved the bounded trial
below. The new option is diagnostic support, not production adoption.
PPv30-node-v1 and the sorting formula remain
tested candidates, with production input selection and broader validation open.

**Further non-food agent assessment: fixed PPv30-node-v1 and context relevance.**

The user approved proceeding with more non-food subjects and retained agent
observation instead of asking for additional user ordering labels.
`experiment_specs/ppv30-transfer-nodes-v2.json` uses the existing
`subject_contexts` adapter, with node-title prominence and the unchanged
PPv30-node-v1 prompt and Astra-low subscription settings. Its source selector
includes all direct members of Dogs (`S1ca3bbb104`, four posts), Sleep and
tiredness (`Saa62bc7939`, three), Christmas (`S5b66e451d0`, four), Workouts
(`Sc9583cd381`, three) and Moral goodness (`Sdc00def87d`, two).

Native preparation validates fifty-one saved SP cases sharing sixteen exact
complete-post/title inputs across thirteen original posts. Pre-run agent
observations are recorded through native `review` on each distinct input:
dog feeding before dog hashtags; the sleep/tiredness accounts before brief
sleep advice within the long list; the Christmas-lunch headline before mixed
Christmas mentions; gym session before the workout-plans joke before the
long-list workout advice. The two moral-goodness posts have an uncertain
mutual order, with a tentative preference for the list's several conduct
recommendations. Either order is acceptable where stated; these observations
are agent expectations, not new user judgments.

The approved run was bounded to thirty-two new attempts, including eligible
provider retries. Repeated SP entries reuse each complete-post/title assessment;
no baseline or SP/MP generation is needed. Total input work grows with direct
selected post/node memberships and complete-post length, not all-post/all-node
pairs. Local CPU SSE encodes only fifty-one standalone SP contexts, five exact
titles and original-mask replay controls. Prominence × context-only relevance,
highest sorting score per post, source posts, masks and hierarchy remain fixed.
The zero-cash subscription reservation is recorded in the lifetime ledger;
reference API cost and subscription quota are separate. Production adoption
remains open.

The completed `experiments/ppv30-transfer-nodes-v2` trial has fifty-one valid
cases: sixteen new complete-post/title assessments and thirty-five within-run
exact-request reuses, with no failures, invalid outputs or retries. Native
original-generation accounting reports 13,510 input tokens, zero cached input,
and 5,010 output tokens including 447 reasoning tokens. Catalog reference is
$0.3856, not a subscription invoice or measured quota; incremental cash is zero.
The zero-cash reservation is settled without changing lifetime monetary totals
or unrelated commitments.

The completed native relevance preparation was:

```sh
python3 sse_multivector/prominence_cosine.py prepare \
  sse_multivector/experiments/ppv30-transfer-nodes-v2/relevance-v1 \
  --experiments sse_multivector/experiments/ppv30-transfer-nodes-v2 \
  --post-order highest \
  --vectors sse_multivector/hierarchy-refresh-v1 \
  --worker-config sse_multivector/experiments/ppv30-transfer-nodes-v1/relevance-v1/worker-config.json \
  --replay V0392 V0957 V0497 V0332 V1075
```

This is the historical command for the existing immutable output; use a new
output directory for a deliberately repeated encoding. The local offline CPU
worker encoded sixty-one rows: fifty-one unchanged standalone SP contexts,
five exact titles and five original-mask controls. All context content tokens
are selected; the longest context has 31 tokens and the longest replay input
336, below the unchanged 512-token limit. Checkpoint, model artifacts, pooling
and runtime match the original comparison. Replay cosines are at least
0.9999999999999302, with maximum normalized component error 4.79e-8. Original
MP masks are controls, not relevance inputs. Comparison SHA-256 is
`a279fb7fc1bb9e882c814319a45a64b6bce6b6933bd5dd9cb5b02adefa50c9aa`.

Every node below descends by each post's highest sorting score. Relevance
shown belongs to that post's winning SP context; displayed numbers are rounded,
while products use full precision. All five prominence-only orders are the
same. Christmas's two prominence-30 posts are tied by prominence; relevance
separates them in a plausible direction that was not a clear pre-run judgment.

| Hierarchy node | Post (note-ID prefix) | Prominence | Relevance | Sorting score |
| --- | --- | ---: | ---: | ---: |
| Dogs | Chihuahua raw-diet transition (`f7ed481e`) | 19 | 0.762887 | 14.494857 |
| Dogs | Preparing dog scraps and myoglobin (`f67c7c54`) | 17 | 0.684255 | 11.632333 |
| Dogs | Island lunch with dog hashtag (`d6628bf3`) | 2 | 0.808076 | 1.616151 |
| Dogs | Tolstoy quotation with dog hashtag (`be8d07d4`) | 1 | 0.833549 | 0.833549 |
| Christmas | Christmas-lunch costs headline (`7160694f`) | 95 | 0.836045 | 79.424276 |
| Christmas | Slowing down after Christmas (`bca8827b`) | 30 | 0.911125 | 27.333753 |
| Christmas | Island lunch after Santa did not arrive (`d6628bf3`) | 30 | 0.747616 | 22.428493 |
| Christmas | Long diary with Christmas-card printing (`eaa6a5e6`) | 6 | 0.771970 | 4.631821 |
| Sleep and tiredness | Tired despite caffeine (`8cf2c204`) | 75 | 0.874081 | 65.556083 |
| Sleep and tiredness | Detailed sleep and clarity account (`89cdcfbb`) | 60 | 0.913289 | 54.797361 |
| Sleep and tiredness | Eighteen-item advice list (`05f275f4`) | 16 | 0.941514 | 15.064225 |
| Workouts | Morning gym session (`bd357fcf`) | 65 | 0.885325 | 57.546102 |
| Workouts | Workout-plans red-flag joke (`41efa59d`) | 33 | 0.940079 | 31.022611 |
| Workouts | Eighteen-item advice list (`05f275f4`) | 8 | 0.796563 | 6.372503 |
| Moral goodness | Shared-meal generosity story (`1c964a41`) | 64 | 0.732755 | 46.896329 |
| Moral goodness | Eighteen-item advice list (`05f275f4`) | 25 | 0.865191 | 21.629782 |

Agent inspection found no clear wrong order in Dogs, Sleep and tiredness,
Christmas or Workouts. Both dog-feeding posts lead both dog hashtags, although
hashtag contexts have higher relevance. Both sleep/tiredness accounts lead
sleep advice in the long list, although the advice has the highest winning
relevance. Gym session leads workout joke and brief advice, matching the clear
pre-run expectation. Christmas-lunch costs lead three mixed mentions. The
stated about-equal directions remain acceptable; do not invent strict expected
orders among those pairs from their displayed numbers.

Moral goodness remains uncertain. Its generosity story leads the conduct
list, reversing the agent's explicitly tentative pre-run preference. The story
also says knowledge and joy must be shared and treats a shared meal as sacred;
it illustrates hospitality and praises generosity. The teacher assigns those
parts 30, 12 and 18 represented points, plus four for humility, for prominence
64. The list assigns 25 to several conduct recommendations amid other advice.
This supplies a defensible basis for the observed direction; whether all of
that opening and hospitality meaning warrants its moral-goodness allocation
remains uncertain. A tentative agent preference is not a clear failure or a
user-approved ordering constraint. No changed prompt or corrective trial was
initiated.

Native post-run agent reviews accept ordering on forty-three correlated SP
cases and mark the eight Moral goodness cases uncertain; the latter share only
two complete-post/title assessments. Earlier pre-run observations are retained,
and no user reviews were created. These counts are not an accuracy rate or
approval of exact prominence percentages. All fifty-one saved contexts and
complete selections, five titles, point allocations, independent cosines and
sorting-score products, sixteen post maxima and complete orders were verified.
Protected source/prompt/prior-comparison hashes remain unchanged. The existing
experiment-selection and prominence-cosine suites passed twenty-three tests;
`experiments/ppv30-transfer-nodes-v2/workflow-tests.log` retains the check log.
No production code change was needed.

This five-node sample adds no demonstrated ordering benefit from relevance
over prominence alone and exposes no clear reversal caused by relevance.
It uses thirteen posts from the same original 100-post corpus, so it does not
establish transfer to fresh posts or broad non-food coverage. The agent
recommends a bounded trial on fresh non-food posts outside that corpus before
further relevance-input changes. The user approved the saved-input trial below;
PPv30-node-v1, the formula, input selection and production adoption remain
tested candidates or open decisions, not frozen production behavior.

**Fresh non-food posts: saved SP contexts and fixed PPv30-node-v1.**

The user approved a bounded sorting trial on posts outside the original 100,
keeping the calculation fixed and delegating observation to the agent. The
selector `experiment_specs/ppv30-fresh-nonfood-v1-source.json` references the
unchanged saved music100 subjects and the unchanged raw HR02 graph for exact
existing Music, Photography and Bitcoin titles. Nine original posts have IDs
disjoint from the old 100. Forty-three exact ASv6.23 SP entries cover eleven
selected post/node inputs: six Music, three Photography and two Bitcoin.
These are explicit diagnostic assignments, not new hierarchy memberships or
validation of an automatic placement rule. No SP or MP answers are generated;
the broader-corpus generation hold is respected. ASv6.23 is older than the
current SP prompt, so this evaluates saved-input sorting and cannot isolate
current SP quality.

The shared `subject_contexts` adapter now accepts explicit `subject_id`
selections against a saved SP carrier and existing graph titles. It preserves
the exact post, subject, context and source hashes, without inventing MP masks
or SP numbers for older flat SP records. Existing numbered-SP/direct-membership
selection keeps its original validation. `prominence_cosine.py` can prepare and
collect these context-only cases without `--vectors` or `--replay`; saved MP
comparisons still require vectors. Context-only inputs use the supplied worker
config's checkpoint/model identity, with source and code hashes frozen and
checked. A source file is hashed once per preparation, not once per SP entry.
No original-mask controls are present on this new path; do not report them as
replay checks. The calculation is unchanged: prominence from the complete post
and exact title; relevance from the standalone unchanged SP context and title;
sorting score is prominence × rescaled cosine; highest sorting score among the
explicitly selected SP entries is used for each post.

Two production-path tests first failed for the expected unsupported-input
reasons: the preparer required hierarchy membership data and the comparison
required `mask_ids`. They now verify native selection by exact saved SP ID,
unchanged full-post/title inputs, source preservation and unknown-subject
refusal, native CLI context encoding without MP masks or vectors, full content
selection, unchanged product and per-post maximum, and protected-source refusal.
Thirty-one comparison/selection/ranking tests and 108 experiment/worker tests
passed. An initial regression command named a nonexistent test module; the
corrected existing suites passed. Logs are in the ignored
`experiments/ppv30-fresh-nonfood-v1-preparation` directory.

The reusable `experiment_specs/ppv30-fresh-nonfood-v1.json` retains fixed
PPv30-node-v1 / Astra-low subscription settings. Native preparation freezes
forty-three SP cases but only eleven exact complete-post/title requests; SP
entries for the same post/title share one prominence answer. The agent recorded
pre-run observations natively: focused musical posts should lead the mixed
reposting/travel accounts; band photographs before the father-photography
account before photography incidental to song inspiration; Bitcoin support
instructions before a song's incidental Bitcoin association. Subtle directions
remain open, and none of these are new user labels.

The run completed all forty-three valid cases with eleven new complete-post/
title assessments and thirty-two exact-request reuses, no failures or retries.
Native usage and generation accounting both report 7,916 input, zero cached
input and 1,873 output tokens including 204 reasoning tokens. The API catalog
reference is $0.17281; incremental subscription cash is zero and subscription
quota was not measured. Only this zero-cash reservation is settled, preserving
lifetime monetary totals and unrelated accounting. There were no baseline, SP,
MP, hierarchy-generation or paid-fallback calls.

Two SP entries have an identical context. Local offline CPU SSE encoded
forty-two distinct contexts and three exact titles. All forty-five rows select
their entire UTF-8 text and all non-special tokens; the longest has
23 tokens including the special token. Checkpoint, model artifact, worker and
runtime identities are unchanged. No replay controls exist on this path, so
there is no claim of original-mask parity. Work scales with selected post/node
inputs and full-post length rather than every post against every hierarchy
node; repeated SP entries reuse the complete-post prominence answer. Source
lookup is linear in the saved carrier and selected entries.

Descending sorting-score order, with original music-corpus ranks identifying
posts and the exact winning SP retained in `comparison.json`:

| Title | Original rank and post | Prominence | Highest relevance | Sorting score |
| --- | --- | ---: | ---: | ---: |
| Music | 1: classical listening and enjoyment | 100 | .911088 | 91.108842 |
| Music | 13: iconic Goa-track appraisal | 98 | .917322 | 89.897579 |
| Music | 81: AI-track and lyric credits | 94 | .913821 | 85.899190 |
| Music | 4: “What does music mean to you?” | 100 | .853925 | 85.392473 |
| Music | 80: song influence and Lisbon inspiration | 81 | .884162 | 71.617087 |
| Music | 35: daily listening, reposting and algorithm defiance | 70 | .813962 | 56.977332 |
| Photography | 40: band photographs around video recording | 52 | .836664 | 43.506529 |
| Photography | 46: photographing a drumming father | 30 | .755091 | 22.652723 |
| Photography | 80: incidental photography in song inspiration | 10 | .654409 | 6.544092 |
| Bitcoin | 21: vinyl contest and Lightning support instructions | 24 | .893909 | 21.453820 |
| Bitcoin | 80: incidental Bitcoin associations in song promotion | 3 | .784576 | 2.353728 |

Photography and Bitcoin match the pre-run agent observations and their
prominence-only orders. The band post develops two photograph-sharing occasions;
the father post also concerns drumming, learning guitar and family; the song
mentions photography within its inspiration story. Bitcoin Lightning support
instructions develop the subject beyond the song's incidental associations.

Music's focused group still leads the mixed posts. The mixed song develops
musical influence, inspiration and listening availability; its order before the
repost with algorithm defiance is defensible. Within the focused group,
relevance moves the pure music question below the Goa appraisal and AI-track
credit. Prominence is 100 for the question versus 98 and 94 for those tracks;
its winning saved context is “The question asks the reader what music means to
them.” The winning track contexts are “The musical content shared in the post.”
and “The post shares a musical track and includes #music.” The lower question
relevance is verified, but the reason and the benefit of those subtle directions
remain uncertain. No numeric gap was approved as a semantic threshold.

Thirty-four native agent case reviews accept ordering; nine uncertain reviews
share the question, Goa and AI-track inputs. These are correlated SP cases,
not independent comparisons, user labels, exact-percentage approvals or an
accuracy rate. Pre-run observations remain attributable and no user judgments
were created. The agent found no clear wrong order, but this trial demonstrates
no added relevance benefit. It uses older ASv6.23 contexts and nine posts from
one music corpus, with diagnostic assignments rather than automatic placement;
it does not establish broad fresh-subject transfer or current SP quality.
The user approved using the question's exact original text as its relevance
input with prominence and all other inputs fixed. The completed diagnostic is
recorded below. Production adoption remains open; prompt, formula and original
artifacts remain unchanged.

Native artifacts are under `experiments/ppv30-fresh-nonfood-v1`: frozen
`experiment.json`, original `run/results.jsonl`, `after-run.json`, native
`reviews.jsonl` and `after-review.json`, plus `relevance-v1` worker request,
receipt, vectors and `comparison.json`. The comparison SHA256 is
`1e9da852aebd69d15edde5037685a49057b60e43be369a937da14855570ebdf3`.
`verification-checks.log` records exact carrier/context/title binding,
disjoint post IDs, all point allocations, independent cosines/products,
eleven post maxima, full orders and protected source/prompt/prior-comparison
hashes. Tests were completed before generation; no further source changes
were made for the result. Preparation source/specifications and zero-cash
reservation were committed in `c67fff10`.

Native commands after preparation:

```sh
python3 sse_multivector/experiment.py run sse_multivector/experiments/ppv30-fresh-nonfood-v1 --max-new-attempts 22
python3 sse_multivector/experiment.py show sse_multivector/experiments/ppv30-fresh-nonfood-v1 --generation-costs --json
python3 sse_multivector/prominence_cosine.py prepare sse_multivector/experiments/ppv30-fresh-nonfood-v1/relevance-v1 --experiments sse_multivector/experiments/ppv30-fresh-nonfood-v1 --post-order highest --worker-config sse_multivector/experiments/ppv30-transfer-nodes-v1/relevance-v1/worker-config.json
python3 sse_multivector/prominence_cosine.py collect sse_multivector/experiments/ppv30-fresh-nonfood-v1/relevance-v1
```

The existing cached offline CPU runtime ran `worker.py` with the prepared
worker config between `prepare` and `collect`; `worker.log` records forty-five
rows. `native-review.log` records the forty-three CLI agent reviews, with zero
model calls. All artifacts remain ignored from the outset.

**Music question: exact original text as relevance input.**

The user approved the bounded diagnostic. Native `prominence_cosine.py prepare`
keeps all forty-three original cases, three titles, complete posts and saved
PPv30-node-v1 prominence answers. Only
`fresh-S9f8ab11-N004-S001` and `fresh-S9f8ab11-N004-S002` use the exact original
`What does music mean to you? ` as their standalone relevance text. Both select
the full 29 UTF-8 bytes, including the trailing space, and share one encoder
row. The SP carrier itself is unchanged. The existing `--relevance-source-text`
option supports this directly; no workflow or production source change was
needed. Native output is `experiments/ppv30-fresh-nonfood-v1/relevance-question-text-v1`.

| Question relevance input | Relevance | Sorting score, prominence 100 |
| --- | ---: | ---: |
| Best saved SP context: “The question asks the reader what music means to them.” | .853925 | 85.392473 |
| Exact original question | .845908 | 84.590802 |

The sorting score decreases by .801671 and Music's order remains classical
listening, Goa appraisal, AI-track credit, question, song inspiration/travel,
and repost/algorithm defiance. Photography and Bitcoin orders are unchanged.
The other question context, “The post's central topic.”, originally gave
relevance .528183, so replacing it improves that individual case; however,
the per-post maximum already came from the stronger second context. Replacing
both makes their sorting scores identical and does not remove the question's
lower position. This does not establish that all SP wording is irrelevant;
it shows that exact question wording does not resolve this observed direction.
The focused Music comparisons remain uncertain, with no clear error or
benefit established. The agent recommends returning to broader saved-input
transfer checks with context-only relevance and the formula fixed. The user
then approved the three-node saved-input trial below; production input choice
remains open.

The same cached offline CPU SSE runtime encoded forty-four rows: three titles,
forty unchanged distinct contexts and the question's exact text. All complete
byte spans and non-special token selections were verified, with unchanged
checkpoint, model artifacts, worker and runtime identities. Thirty-seven other
case node cosines/products are bit-identical; four differ on re-encoding by at
most 6.143e-8 cosine and 1.598e-6 sorting-score points. All other input text and
all complete orders remain unchanged. These numerical tolerances are checks
on repeated encoding, not a semantic tie threshold. No original MP-mask replay
controls exist on this path or are claimed. Forty-three independent
cosines/products, eleven post maxima and all protected source/prompt/previous
comparison hashes passed. Fourteen existing comparison tests passed in
`workflow-tests.log`; there were no teacher calls, new teacher-token usage,
paid resources or task budget-ledger edits. Another workstream's appended
reservation was preserved without treating it as a sorting input change.

Native `experiment.py review` recorded two additional uncertain agent comments
on the question's two original cases, explicitly bound in their text to this
comparison, preserving prior review history without creating user judgments.
They share one complete-post/title input and are not independent observations.
`native-review.log` records zero model calls; `verification-checks.log` records
the protected-input, numerical and complete-order checks. Plan, request, worker
receipt, vectors and comparison remain ignored from preparation onward.
Comparison SHA256:
`d64ce1d4cb0d5c7e88afd11a8447e4284a19175bb92adee2a80a5108bba94662`.

**Further fresh posts: Literature, Psychology and philosophy, Bitcoin.**

The user approved three existing nodes outside food and music with about five
fresh posts each, retaining the calculation and delegating observations to the
agent. The saved coverage-expansion carrier contains 48 earlier development
posts, with reviewed ASv6.23 subjects and contexts. The trial selects fifteen
posts whose IDs are disjoint from the original 100 and the previous nine-post
sorting trial. Original coverage-expansion generation, manual subject/mask
reviews and HDBv2 decisions remain unchanged; none of the ninety-nine selected
SP entries has an explicit saved subject correction. Older prompt wording and
purposive developmental selection limit generalization and current SP-quality
conclusions. No new SP or MP generation is required, respecting the separate
broader-corpus generation hold.

`experiment_specs/ppv30-fresh-nonfood-v2-source.json` references the unchanged
`real-note-fine-segmentation-v1/coverage-expansion-v1/subjects-reviewed.json`
and unchanged raw HR02 graph. It preserves exact SP IDs, post text, subjects,
contexts and existing titles. These are explicit diagnostic assignments, not
changes to graph membership or validation of automatic placement. The shared
saved-SP input path already suffices; no workflow or production code change was
needed. `experiment_specs/ppv30-fresh-nonfood-v2.json` keeps PPv30-node-v1,
Astra-low subscription settings, output schema and complete-post/title
prominence inputs identical in method to the earlier trial.

| Existing title | Original coverage ranks | Selected SP entries | Distinct post/title inputs |
| --- | --- | ---: | ---: |
| Literature | 7, 9, 11, 13, 14 | 21 | 5 |
| Psychology and philosophy | 17, 18, 22, 23, 24 | 33 | 5 |
| Bitcoin | 19, 38, 40, 41, 45 | 45 | 5 |

The agent recorded fifteen native pre-run observations. Literature includes
book-recommendation questions, a shared poem, the argument about fearing
thought rather than books, and audiobook appreciation with an EarPods detail.
Focused book discussion should precede the fear-of-thinking argument; the poem
should be assessed as literature rather than simply counting its imagery as
unrelated topics. Differences within the focused group remain uncertain.
Philosophical reflection and happiness advice should precede the mixed
bodily-activity/cannabis/year-end account with gratitude. For Bitcoin, the three
technology discussions should precede optimism attributed jointly to Bitcoin
and Nostr, which should precede the mostly Nostr hardware proposal with zap
controls. Within-focus directions remain uncertain, with no numeric tie rule or
new user judgment. Pre-run comments are observations, not exact-percentage
approvals or fixed truth labels.

Native preparation froze ninety-nine cases but fifteen exact complete-post/
title requests; repeated SP entries reuse the same prominence answer. Prominence
× standalone SP-context relevance and highest sorting score among the selected
entries per post remain fixed. The zero-cash reservation bounded the run at
thirty new attempts including eligible provider retries, no paid fallback. Local
offline CPU SSE encoded ninety-nine complete contexts and three existing titles
with the unchanged checkpoint/model/runtime identity. Work scales with selected
post/node inputs and text length, not every post against every hierarchy node;
source lookup is linear in the saved carrier and selected entries. No baseline,
SP/MP, title or hierarchy generation, rentals, UI or production adoption is
included. Native generation costs and subscription cash remain separate.

All ninety-nine cases are valid: fifteen new complete-post/title calls and
eighty-four exact-request reuses, no failures, malformed outputs or retries.
The first run stopped before inference because another session added the
unrelated `measure-root-candidates` command to `experiment.py`. Review confirmed
that this was the only changed frozen code file and left the prominence paths
unchanged. The native `--runner-upgrade-reason` audit records that change with
an empty result prefix; frozen inputs/settings and manifest were not rewritten.

The full post orders below use the highest sorting score among the explicitly
selected contexts. Relevance is the rescaled cosine, not a calibrated percentage.

| Literature, in sorting order | Prominence | Relevance | Sorting score |
| --- | ---: | ---: | ---: |
| Audiobooks and reading anywhere (`05f24382`) | 100 | 0.817159 | 81.715856 |
| Books for an 18-year-old (`650ee6fe`) | 100 | 0.757302 | 75.730245 |
| Five favorite books (`1814c48f`) | 100 | 0.695630 | 69.563026 |
| Terry Tempest Williams poem (`237edb1b`) | 95 | 0.682086 | 64.798217 |
| Fear of books versus thinking (`2e71ddd3`) | 60 | 0.808773 | 48.526372 |

| Psychology and philosophy, in sorting order | Prominence | Relevance | Sorting score |
| --- | ---: | ---: | ---: |
| Alan Watts on life and achievement (`ee76234e`) | 94 | 0.838122 | 78.783443 |
| Advice for happiness (`48e78e7a`) | 100 | 0.673511 | 67.351122 |
| Destiny and choice in the present (`991c3225`) | 100 | 0.626722 | 62.672241 |
| Emmet Fox on living in the present (`4b43f03e`) | 80 | 0.760248 | 60.819813 |
| Mixed year-end activities and gratitude (`62b103a0`) | 60 | 0.603501 | 36.210034 |

| Bitcoin, in sorting order | Prominence | Relevance | Sorting score |
| --- | ---: | ---: | ---: |
| Block transmission and verification (`c9224e91`) | 100 | 0.911480 | 91.148035 |
| Scaling debate and remaining problems (`e36fad15`) | 100 | 0.887407 | 88.740711 |
| Node, mempool, Tor and Sparrow privacy (`7ef38052`) | 100 | 0.662586 | 66.258643 |
| Bitcoin and Nostr optimism (`51161520`) | 35 | 0.828469 | 28.996428 |
| Physical Nostr client with zap controls (`9942031f`) | 10 | 0.564978 | 5.649778 |

All three orders preserve the clear pre-run focus comparisons: focused books,
reading and the poem precede the broader fear-of-thinking argument; four focused
reflections/advice posts precede mixed year-end activities; three Bitcoin
technology discussions precede joint Bitcoin/Nostr optimism, which precedes the
mostly Nostr hardware proposal. The prominence allocations retain details that
develop the node's subject, including the poem's imagery and Bitcoin privacy,
without counting all shared-topic meaning toward the node. Exact percentages
are not approved. Within-focus directions were not established independently.
All three deterministic full orders differ from prominence alone, but Literature
and Bitcoin changes only resolve prominence ties; Psychology and philosophy moves
the prominence-94 Alan Watts post above two prominence-100 posts. These changes
are not demonstrated ordering improvements.

The Bitcoin privacy post exposes a question about relevance. Its complete post
is recognized as entirely concerning Bitcoin without the literal word Bitcoin,
but all fourteen saved contexts also omit Bitcoin and retain only parts of the
technical connections. Its best context describes running a node over Tor when
broadcasting transactions. The sorting score is 66.258643 against 91.148035 and
88.740711 for two other prominence-100 Bitcoin posts. The strict direction and
large gap remain uncertain. Missing context or weak technical-domain recognition
are possible explanations, not established causes. The poem presents a related
question: its eleven SP contexts mostly describe imagery, and the winning text
is only “The assertion that concludes the poem.” The teacher correctly counts
the poem as Literature, but the relevance-created placement below all three
book/reading posts is not an established improvement.

Fifteen native final agent reviews cover complete post/title inputs and their
selected contexts: four accept the clear mixed-post comparisons, eleven retain
uncertainty about focused-post directions or shares. These are observations,
not ninety-nine independent quality labels or a population accuracy estimate.
No new user judgments or numeric tie threshold were introduced. The user
approved comparing relevance from the complete Bitcoin privacy post with
relevance from its saved contexts, keeping prominence 100 and the formula
fixed. The completed diagnostic is recorded below; no input change is adopted.

Native generation accounting records 10,170 input tokens, no cached input,
2,473 output tokens including 573 reasoning tokens and a $0.225350 catalogue
reference estimate. Original calls are fifteen, source calls added zero;
historical SP/MP generation is not booked again. Incremental subscription cash
is zero; provider-reported dollar charges are unavailable and weekly quota is
unmeasured. Only this zero-cash reservation is settled, preserving lifetime
totals and unrelated accounting.

Thirty-one selection/comparison/ranking tests and 108 experiment/worker tests
passed. Logs are in the ignored `experiments/ppv30-fresh-nonfood-v2-preparation`
directory. Prepared data and native observations are under the ignored
`experiments/ppv30-fresh-nonfood-v2` directory. Independent verification checks
all ninety-nine exact source entries, fifteen complete-post/title allocations,
102 complete encoder selections with no truncation, unchanged encoder identity,
ninety-nine cosine/products, fifteen post maxima and three full orders. Saved
SP/MP, original source posts, raw graph, prompt and both prior comparison hashes
remain unchanged. The native result is `relevance-v1/comparison.json`, SHA256
`5e0f3a6c0ffedbf7ccf3eb6ef919c6f15eb08ed3d4586fcd26b64ff26ce7f599`.
The transfer trial is complete; production adoption remains open.

**Bitcoin privacy: exact complete post as relevance input.**

The user approved this bounded check. Native `prominence_cosine.py prepare`
selects only the existing Bitcoin node's forty-five cases and five posts from
`ppv30-fresh-nonfood-v2`, retaining all saved PPv30-node-v1 prominence answers.
The fourteen `fresh2-merged-6-N041-*` privacy entries replace their standalone
SP-context relevance inputs with the exact complete original post. All 356
UTF-8 bytes, including its original paragraph breaks, are selected. Those
fourteen entries share one complete-post encoder row; they are not fourteen
independent observations. The other thirty-one contexts and the Bitcoin title
remain exact. The existing `--relevance-source-text` and `--node` options suffice;
no workflow or production source changes were needed.

| Privacy-post relevance input | Prominence | Relevance | Sorting score |
| --- | ---: | ---: | ---: |
| Highest saved SP context, describing node/Tor broadcast privacy | 100 | .662586 | 66.258643 |
| Exact complete original post | 100 | .542481 | 54.248130 |

The sorting score decreases by 12.010514. The full Bitcoin order remains block
transmission (91.148035), scaling (88.740711), privacy (54.248130), Bitcoin/Nostr
optimism (28.996428), and Nostr hardware with zap controls (5.649778). All four
other post maxima and their winning cases are bit-identical to the original.
All fourteen privacy cases now have identical relevance and sorting score, so
the native per-post maximum selects the first case ID only to break that tie.
Literature and Psychology and philosophy are not re-encoded; their original
comparison remains unchanged.

The complete post's node, mempool, Tor and Sparrow details still develop
Bitcoin privacy, consistent with its saved prominence 100. Replacing its SP
contexts with the original post does not close its gap to the other focused
Bitcoin posts or demonstrate an ordering improvement. This is not proof that
all SP wording is irrelevant or that a particular SSE/model/title limitation
causes the gap. The strict within-focus direction remains uncertain. The user
approved a bounded wording diagnostic: replace the opening “a node” with
“a Bitcoin node” in a diagnostic copy, holding all other words, the title,
prominence and formula fixed. That would test sensitivity to explicitly naming
Bitcoin. The completed check is recorded below; the original post and production input
policy remain unchanged.

The same cached offline CPU SSE checkpoint, model artifacts, worker and runtime
encoded thirty-three complete rows: one title, thirty-one other contexts and
one complete privacy post. Every byte span and non-special token selection is
complete, with no truncation. Twenty-six other case cosines/products are
bit-identical; five change on re-encoding by at most 5.537e-8 cosine and
.000002768269 sorting-score points, without changing any other post maximum or
order. These are numerical checks, not a semantic tie threshold. Independent
checks verify all forty-five cosine/products, five post maxima, full Bitcoin
orders and twenty protected artifact/source hashes. Original prominence
receipts, SP/MP sources, raw graph, prompt and earlier comparisons remain
unchanged. Fourteen existing comparison tests passed. No new teacher calls,
tokens, paid resources, user judgments or task budget-ledger edits occurred.

Native `experiment.py review` appended fourteen uncertain agent comments to
the original privacy cases, explicitly bound to this diagnostic's comparison
hash. They preserve the original history and represent one complete-post/title
input. Native generation accounting remains fifteen original calls and
eighty-four reuses; those are the earlier trial's calls, not new diagnostic
usage. Ignored artifacts are under
`experiments/ppv30-fresh-nonfood-v2/relevance-privacy-post-v1`: plan, request,
config, receipt, vectors, comparison, verification and review/test logs.
The comparison SHA256 is
`d26ab11ff6ae33591560271e2ae65b737c596dd60ae3bb9953ef301f3a32a0c4`.

**Bitcoin privacy wording check: completed.**

The user approved changing only the opening “a node” to “a Bitcoin node” in
the complete privacy post's relevance input. Native preparation selects the
same forty-five cases and five Bitcoin posts. Fourteen privacy cases share a
single 364-byte copy derived from the exact 356-byte original, preserving the
original source text/spans and declaring the one substitution. Saved prominence
100, the title, formula, thirty-one other contexts and highest-per-post
ordering remain fixed. Thirty-three rows were encoded: one title, one copy and
thirty-one complete contexts. Preparation is linear in selected text and
case count, with identical copies deduplicated; this does not add every
post/node pair or any teacher generation. Offline CPU SSE uses the unchanged
checkpoint, model and runtime, with no paid resources or task ledger changes.

The previous shared option intentionally refused rewritten source text, so
the smallest reusable extension is `--relevance-source-replace`. The native
CLI integration test first failed for the missing option, then passed after
implementation. Three integration tests exercise actual experiment preparation,
runner receipts with the fixture provider, source-bound comparison preparation
and collection. They verify original inputs/receipts stay unchanged, identical
copies share a row, unbound/ambiguous/empty edits are refused before writing,
and old-text encoding cannot be reused. Thirty-four comparison/ranking/selection
tests and 108 experiment/worker tests passed. The tests use existing production
seams; no API was added solely for tests. Logs and prepared artifacts remain ignored under
`experiments/ppv30-fresh-nonfood-v2/relevance-privacy-bitcoin-name-v1-preparation`
and `relevance-privacy-bitcoin-name-v1`.

| Privacy-post relevance input | Prominence | Relevance | Sorting score |
| --- | ---: | ---: | ---: |
| Highest original SP context | 100 | .662586 | 66.258643 |
| Exact complete original post | 100 | .542481 | 54.248130 |
| Copy changing only “a node” to “a Bitcoin node” | 100 | .566381 | 56.638104 |

The named copy raises the sorting score by 2.389974 over the original complete
post, but stays below the original highest-context score and the other two
focused Bitcoin posts. The full Bitcoin order remains block transmission
(91.148035), scaling (88.740711), privacy (56.638104), Bitcoin/Nostr optimism
(28.996428), and Nostr hardware with zaps (5.649778). All thirty-one other
context cosines/products and all four other post maxima/winning cases are
bit-identical to the complete-post diagnostic. Literature and Psychology and
philosophy remain untouched.

Explicitly naming Bitcoin affects this copy's relevance, but this intervention
does not close the gap or demonstrate a sorting improvement. It does not show
that omission of the name alone explains the gap, nor establish which part of
the relevance calculation causes it. Both original and clarified wording
develop Bitcoin privacy. The strict focused-post direction remains uncertain;
this one wording comparison is not a broad robustness result, an exact-share
approval or a numeric tie threshold. Rewriting posts is not adopted.

The user subsequently authorized the comparison below using the same saved
inputs before and after SSE's final learned projection. This tests whether that
component helps standalone-context sorting; it does not assume the projection
caused this gap. Existing cached weights suffice, with no new pretrained-model
download or teacher inference. Production adoption remains open.

Independent verification checks all forty-five original case identities and
saved prominence values, fourteen exact one-substitution derivations with
separate original byte spans, thirty-three complete encoder/token selections,
unchanged checkpoint/model/runtime, forty-five cosine/products, five post maxima
and full Bitcoin orders. All twenty-five protected source/artifact hashes remain
unchanged, including the original source posts, SP/MP carrier, raw graph, PP
prompt, receipts and both earlier Bitcoin comparisons. No numerical differences
occur in the other context products on this encoding run. Native reviews append
fourteen uncertain agent comments explicitly bound to this comparison, retaining
the original history and creating no user labels; they share one post/title
input. Native generation accounting remains fifteen original calls/eighty-four
reuses from the prior trial. This check adds no teacher calls, teacher-token
usage, paid resources or task accounting changes.

The ignored `relevance-privacy-bitcoin-name-v1` directory contains native plan,
request, config, worker receipt/vectors, comparison, independent verification
and native review logs. Comparison SHA256:
`74c23cd3347dbb6424f4f825aae52d7626a1a133b61dbc726291b838ed57ddac`.

**Completed comparison: relevance before and after SSE projection.**

The user's next "proceeed" authorizes comparing the same checkpoint's
selected-token mean with the existing mean → linear → ReLU → linear output.
This is a bounded local CPU experiment, not a different pretrained model or a
new teacher assessment. Prominence remains PPv30-node-v1, relevance remains
`(clip(title cosine, -1, 1) + 1) / 2`, sorting score remains prominence ×
relevance, and each post retains its highest selected SP-context sorting score.
The encoder checkpoint itself was trained for SSE; omitting its final projection
does not restore the pretrained encoder's original weights.

Native preparation freezes Coffee's fourteen posts and Eggs' seven from
`experiments/ppv30-node-orders-v1`, plus Bitcoin's five original posts from
`experiments/ppv30-fresh-nonfood-v2`. This is thirty-seven plus forty-five SP
entries: eighty-two complete contexts and three node titles, eighty-five encoder
rows in each run. Both requests contain identical text, order and byte spans;
case evidence and prominence also match exactly. The earlier rewritten privacy
copy is not an input. There are no original-mask replay rows, no inverse term,
no teacher calls or paid resources. At this bounded size the work is two linear
encoder passes over the saved contexts/titles, with CPU batch size eight; it
does not introduce per-post pairwise inference or a recursive hierarchy pass.

The native outputs `ppv30-node-orders-v1/relevance-projection-v1` and
`ppv30-node-orders-v1/relevance-before-projection-v1` are complete under the
ignored `experiments/` history. Both worker runs encode eighty-five rows with
the same cached checkpoint/model artifacts, CPU runtime and batch size eight;
native collection calculates eighty-two case products and twenty-six post
maxima per mode. No encoding from the other representation is reused.

Both modes retain all ten clear Coffee/Eggs expected pair directions. The
important iced-coffee-above-raw-yolk comparison remains 85.118001 > 75.582815
with the projection and 82.647530 > 74.316804 before it. Prominence alone,
95 < 100, still reverses that approved direction, so this does not justify
removing relevance. Four about-equal Coffee pairs accept either direction;
they have no numerical gap requirement and are not counted as four more
strict-order successes. The two accepted complete-node orders remain two
review observations, not every implied pair as an independent label.

Coffee changes exactly three pair directions:

| Posts | With SSE projection | Before projection | Assessment |
| --- | --- | --- | --- |
| Iced coffee / coffee request | 85.118001 > 83.173847 | 82.647530 < 83.420752 | Both complete posts concern Coffee; the swap has uncertain benefit and no separately agreed strict pair direction. |
| More coffee in cool places / hashtag-heavy second coffee | 65.443207 > 64.841901 | 62.883447 < 63.346777 | Both have fixed prominence 70 and additional place/tag meaning; no clear improvement is established. |
| Another coffee/Sunday wishes / errands | 42.357666 > 41.622349 | 41.426023 < 44.515389 | The user judged these about equal and accepted either direction; this swap is acceptable. |

The agent read all six complete posts and the winning saved SP contexts before
making these assessments. Coffee's fourteen-post order therefore changes from
the previously accepted displayed sequence, without failing a clear pair check
or establishing a better full order. Eggs' seven-post order stays identical
and reproduces the accepted sequence. Bitcoin's five-post order also stays
identical, with focused posts above both mixed posts:

| Bitcoin post | Fixed prominence | With SSE projection | Before projection |
| --- | ---: | ---: | ---: |
| Block transmission (`c9224e91`) | 100 | 91.148035 | 91.302657 |
| Scaling (`e36fad15`) | 100 | 88.740711 | 90.002860 |
| Privacy (`7ef38052`) | 100 | 66.258643 | 73.438592 |
| Bitcoin/Nostr optimism (`51161520`) | 35 | 28.996428 | 29.756177 |
| Nostr hardware zap controls (`9942031f`) | 10 | 5.649778 | 5.387452 |

The privacy post rises by 7.179949 sorting-score points, but remains below the
other two focused posts. This changes the earlier numerical gap without
demonstrating an ordering improvement. No strict order or target score gap
among those focused posts has been approved. The agent recommends retaining
the existing projection: this comparison gives no clear sorting advantage
from omitting it. The user has now approved the unchanged calculation on the
remaining hierarchy nodes with at least two posts in the saved corpus; the
completed transfer test below records that approval. No new prompt, user
labels, source-text policy, recursion or production sorting adoption is
introduced.

Independent verification confirms identical source text, token indices/IDs
and all eighty-two prominence/evidence rows. Applying the saved linear → ReLU
→ linear weights independently to each pre-projection vector reproduces all
eighty-five projected vectors exactly, with maximum component error zero.
All 164 independent title cosines/products, fifty-two post maxima and six
complete node orders match native collection exactly. The rerun of the
existing projection reproduces all three original node orders; maximum
original-versus-rerun cosine drift is 1.44463e-7, with no ordering change.
This is re-encoding reproducibility, not an original-mask replay assertion.
All thirty-eight protected original source/artifact hashes remain unchanged.

Native reviews append twenty-one Coffee/Eggs and five Bitcoin uncertain agent
comments, one per post/title, explicitly bound to both comparison hashes.
Original review history remains intact; these do not add twenty-six user
decisions or eighty-two independent SP-level labels. Native generation
accounting remains the original twenty-one calls/sixteen reuses for Coffee/Eggs
and fifteen calls/eighty-four reuses for fresh-v2. No new calls, teacher-token
usage, paid resource or budget-ledger change occurs in this task. The ignored
outputs preserve worker logs, receipts/vectors, comparisons, verification,
native review logs and native after-review accounting reports. Comparison
SHA-256 values are `5dc1aafc008ce2a011bec5200f3cd2f784b1865c9f9a0f1189323a8f63043436`
(with projection) and
`1836a4013623fb53ad0de646edcf96310875d6085d7e50dc23ecc5f9b2fa5289`
(before projection).

Minimal tests failed first for the unsupported worker pooling rule and missing
comparison option. The production worker integration uses a tiny real T5
checkpoint and fast tokenizer, checks both projection and selected-token mean,
discontinuous UTF-8 selections, shared tokens/receipts and distinct output
dimensions. Native experiment/CLI/collector tests check unchanged source inputs,
wrong-mode receipts and encoding reuse, and refusal of original mask replays.
Thirty-six comparison/ranking/selection and nine worker tests pass, with no
inference-dependency skips. The broader experiment suite passes 101 of 102;
the concurrently added parent-guide test fails because the default Python lacks
`tiktoken`. That unrelated work is not changed by this task.

**Remaining-node transfer approved October 1 (completed):** The user's
"proceed" authorized unchanged PPv30-node-v1 / Astra-low complete-post/title
prominence, standalone saved SP-context relevance through SSE's existing final
projection, `P × (clip(cosine, -1, 1) + 1) / 2`, and the highest sorting score
among the selected contexts for each post. Observation was delegated to the
agent. The untouched 100-post source and raw named hierarchy supplied 104
remaining direct-member nodes, 354 distinct post/title inputs, 94 distinct
posts and 587 context cases, excluding fourteen previously tested nodes.
This expands coverage of the developmental saved corpus, not unseen or
representative population accuracy.

Reusable selectors/specs are
`experiment_specs/ppv30-remaining-nodes-v1-source.json` and
`experiment_specs/ppv30-remaining-nodes-v1.json`. Native results live in
`experiments/ppv30-remaining-nodes-v1`, with comparison
`relevance-v1/comparison.json` SHA-256
`e29073a29b34415a385277963a08972416247d827b279d7efd18b00ee9b985cf`.
The existing workflow sufficed; this task changes no production or workflow
behavior. Concurrency eight changes scheduling only. All 587 cases are valid:
354 distinct complete-post/title requests, 233 exact-request case reuses and
355 sent attempts. One HTTP 503 was retried under the existing provider-only
two-attempt limit and succeeded; there are no unresolved failures, malformed
answers or invalid receipts. The maximum reservation was 708 attempts.
A concurrent preparation-only provenance addition for bounded parent adapters
was inspected and accepted through the native code-upgrade audit before any
model result; frozen plan, inputs, settings and manifest were preserved.

Local CPU SSE encoded 583 distinct exact context texts and 104 unchanged
titles, 687 rows total, with the checkpoint, projection, model artifacts and
runtime of the most recent projected comparison. The mask-linked source
adapter references the original saved vector carrier for validation; it does
not encode MP masks or add replay rows. Independent source/allocation checks,
all 587 own-node cosine/products, 354 post maxima and 104 complete orders pass.
Token IDs and selections match independent fast-tokenizer output, with no
truncation and at most forty tokens per input. Sixty protected source, graph,
prompt and previous-result hashes stay unchanged. Fifty-two relevant existing
tests passed; the three production adapter checks were also rerun after the
concurrent preparation-only code change and passed.

The agent read all 94 complete posts and all 104 resulting orders. Native
history preserves 104 pre-run uncertain node comments and appends 104
post-run node assessments, plus two display-precision corrections. Among
fifty nodes with clear pre-run directions, forty-nine retain all stated
directions and one fails. Five modest directions hold but remain tentative;
forty-nine nodes had no fixed strict direction. The post-run verdicts are
forty-nine accept, one reject and fifty-four uncertain, each for one related
node assessment. Accept applies only to the stated agent directions, not all
unspecified pairs, numerical gaps, a complete user-approved order or a
population accuracy claim. Existing user labels are unchanged.

| Node / post | Fixed prominence | Relevance | Sorting score |
| --- | ---: | ---: | ---: |
| Food and drink: Khyber Pass restaurant (`add487c4`) | 85 | 0.502965 | 42.752028 |
| Food and drink: mixed painting/food diary (`eaa6a5e6`) | 61 | 0.712205 | 43.444485 |
| Pizza and restaurants: restaurant plan (`7258eaac`) | 75 | 0.957021 | 71.776557 |
| Pizza and restaurants: pizza-day greeting (`9e811e03`) | 85 | 0.811376 | 68.966981 |

The restaurant post was expected above the mixed diary. Its sole selected
context says, "The writer specifically names Khyber Pass, identifying it
parenthetically with St Marks Place." The saved SP subject is "Khyber Pass
restaurant"; that subject is not currently supplied to SSE. Relevance reverses
the sensible prominence direction here. Omitted restaurant meaning is a
candidate explanation, not a proven cause. Conversely, relevance retains the
expected pizza-restaurant plan above the greeting where prominence alone
reverses them. This adds one clear agent-assessed case for retaining relevance,
in addition to the previously agreed iced-coffee/raw-yolk case.

Ambiguous title interpretation remains unresolved. For `grownostr`, chicken
stock/canning (`25f5a4c0`) receives prominence 85 under a homegrown-food and
self-sufficiency reading. The steak/preservation diary (`f67c7c54`) receives 2
under a growing-Nostr reading. The title is identical; the teacher's saved
allocations demonstrate different meanings across posts. `coffeechain`,
combined Food and Paraguay, and weak `satoshi` memberships are also recorded
as uncertain. Suspect tomato-joke/Onions, gamey-meat/Coffee flavor,
chicken-enclosure/Motor vehicles, red-flags/Daily painting and
chocolate-product/guarani memberships receive prominence zero, hence sorting
score zero. The source hierarchy is preserved, not repaired by this trial.

Native usage is 267,585 input tokens, 73,855 output tokens including 12,138
reasoning tokens, no reported cache tokens, and API catalog reference estimate
$6.368600. Incremental subscription cash is $0; provider-reported billing is
unavailable and weekly quota is unmeasured. The zero-cash reservation and
settlement preserve all monetary totals and unrelated ledger entries. Teacher
work scales with direct selected memberships and repeated full-post tokens;
encoder work uses distinct selected contexts/titles. Native offline collection
also reports 61,048 selected-context/title cosines (587 × 104); only the 587
own-node values enter sorting. That bounded diagnostic cross-product is not a
production design, and must not grow to all-post/all-node comparisons.

The user subsequently approved comparing saved SP subject plus context against
context alone, with prominence, SSE and formula fixed and earlier agreed checks
retained. The completed comparison below tests the restaurant reversal; it does
not resolve ambiguous node meaning in prominence. New SP/MP generation,
hierarchy changes, broader corpus generation, recursion and production adoption
remain outside this test.

**Remaining-node subject plus context approved October 1 (completed):**

The user's "proceed" authorized this offline paired comparison. Native
`prominence_cosine.py prepare --post-order highest` selects the existing
`ppv30-remaining-nodes-v1`, `ppv30-node-orders-v1`, `ppv30-music-node-v1` and
`ppv30-photography-node-v1` experiments. These supply 633 saved SP entries,
380 post/node inputs and 96 original posts in 108 nodes: the 104 remaining
nodes plus Coffee, Eggs, Music and Photography. All native cases are valid.
The existing `--include-subject` option changes only the candidate relevance
input to the saved SP subject, one newline and its unchanged saved SP context.
Complete-post/title PPv30-node-v1 prominence answers, selected memberships,
node titles, original SSE checkpoint and final learned layers, formula and
highest selected-entry sorting score per post are fixed. No new source or
workflow capability was needed; the default remains context alone.

Two local offline CPU worker runs encode 737 context-only rows and 738 subject
plus context rows, including the same 108 title rows. Repeated identical input
texts share rows. Total encoder input grows from 44,156 to 56,557 UTF-8 bytes;
the maximum token count grows from 40 to 56, both below the fixed 512 limit.
The paired worker receipts have identical checkpoint, model, pooling,
batch size, device and runtime identities. Title vectors are bit-identical.
No original-post masks or replay controls are re-encoded in this comparison.
The native `collect` command produces both comparisons:

| Relevance input | Native output under `experiments/ppv30-remaining-nodes-v1/` | Comparison SHA256 |
| --- | --- | --- |
| Saved SP context | `relevance-context-checks-v1/comparison.json` | `dbd044e4bb2f86082a3bf4e13e41986bcec61c108a07023cf265e607501e3143` |
| Saved SP subject + newline + context | `relevance-subject-context-v1/comparison.json` | `a829768d4a8f2292894405998a86d2e11c4b8d556c8c89309a942a199781a292` |

The restaurant input now begins with `Khyber Pass restaurant`, followed by
"The writer specifically names Khyber Pass, identifying it parenthetically
with St Marks Place." The original post, saved fields and prominence are
unchanged. The resulting Food and drink order corrects the one clear failure
from the preceding remaining-node trial:

| Food and drink post | Fixed prominence | Context-only relevance | Context-only sorting score | Subject plus context relevance | Subject plus context sorting score |
| --- | ---: | ---: | ---: | ---: | ---: |
| Restaurant (`add487c4`) | 85 | 0.502965034 | 42.752027871 | 0.542109016 | 46.079266351 |
| Mixed painting/food diary (`eaa6a5e6`) | 61 | 0.712204677 | 43.444485285 | 0.694543940 | 42.367180353 |
| Homegrown food (`7d538c44`) | 82 | 0.704432005 | 57.763424419 | 0.688892428 | 56.489179075 |

The diary's highest entry changes from the general Kreik context to its gift
bottle context. Both food-focused posts now precede the mixed diary; no
strict direction was set between those two focused posts. Adding the saved
subject corrects this observed order, but the comparison does not isolate the
word "restaurant" or establish a general causal rule.

All fifty originally clear agent node expectations now hold, versus forty-nine
with context alone. The five modest directions remain intact and tentative;
the other forty-nine remaining nodes still lack a fixed strict direction.
These are the earlier related node observations, not newly collected labels
or a population accuracy measure. All eleven earlier clear Coffee/Eggs/Music
comparisons hold in both modes. The accepted seven-post Eggs and three-post
Photography complete orders are unchanged. Coffee swaps only errands and
another coffee, the pair already judged about equal with either direction
acceptable. Existing user judgments are unchanged; no numerical gap or tie
threshold is introduced.

Complete sorting orders change in eleven nodes; the other ninety-seven orders
are identical. Agent inspection retains uncertainty for directions that were
never settled:

| Node | Change from context alone |
| --- | --- |
| Food and drink | Restaurant moves above mixed diary, correcting the prior clear failure |
| Food and cooking | Twenty-one pair directions change within the previously unspecified 41-post order; all stated focused-versus-mixed directions hold |
| Food and dining | Three dinner descriptions reorder; no strict direction was fixed among them |
| coffee shop | Rave moves above laptop-rule post; this comparison remains uncertain, while laptop-rule remains above song playing |
| Good morning greetings | Short breakfast greeting moves above household diary; earlier focused greeting directions hold |
| tea | Two focused tea posts swap; both remain above diary |
| Bread | Two focused bread posts swap; both remain above mixed dinner |
| nostr | Two hashtag-only posts swap; their strict direction remains uncertain |
| coffeechain | Weather/coffee and music/coffee-shop posts swap; node meaning remains ambiguous |
| grownostr | Identical old sorting scores become a small subject-wording difference; node meaning remains ambiguous |
| coffee | Only the already acceptable errands/another-coffee swap |

There are 32 deterministic pair reversals, including one old exact tie in
`grownostr`; these are not 32 independent quality judgments. The `grownostr`
prominence discrepancy remains 85 for stock preservation under a homegrown-food
reading versus 2 for the steak/preservation diary under a growing-Nostr reading.
Relevance input cannot repair these fixed saved prominence answers. Five
previously identified irrelevant memberships still have sorting score zero.

Native `experiment.py review` appends one hash-bound agent assessment per node
to the original experiments: 54 accept the exact earlier clear directions or
agreed checks, and 54 retain uncertainty. Unspecified focused-post orders,
percentages and gaps are not approved. Original review prefixes, teacher
receipts, SP/MP sources, graph and all 77 protected hashes remain unchanged.
Independent checks verify all 633 exact source/membership entries, literal
paired inputs, all 1,475 complete byte/token selections, both sets of 633
own-node cosine/products, 380 post maxima and 108 orders. Fresh context-only
orders reproduce all four earlier comparison subsets; maximum sorting-score
drift is 0.000006451, without an order change. The verification log also records
two corrected verifier assumptions about merged mask aliases and the earlier
eight-node projection comparison's selected subset; no production fix was
required. All prominence-only orders remain identical.

Forty-five existing comparison, ranking, selection and worker tests pass,
including the actual local T5 worker integration. Ignored plans, requests,
configs, receipts, vectors and comparisons are under the two output directories;
verification, native review and test logs are under
`experiments/ppv30-remaining-nodes-subject-context-v1-checks`. There are no new
teacher calls, tokens, paid resources or budget-ledger changes. Encoding work
grows with selected subject/context texts, adding one short saved subject per
entry. Native offline diagnostics emit 633 × 108 title cosines per mode, but
only the 633 own-node values enter sorting. That bounded diagnostic is not a
production all-post/all-node design.

The agent now recommends saved SP subject plus context for subsequent sorting
experiments, retaining prominence, SSE's final learned layers and the formula.
Production adoption remains open. The user subsequently approved the bounded
fixed-meaning `grownostr` prominence trial completed below, because changing
relevance does not resolve the inconsistent meanings already observed.

**Fixed GrowNostr meaning approved October 1 (completed):**

The user approved testing one meaning across the fifteen direct-member posts
in `grownostr` (`Sa233efc2db`). Inspection found fourteen hashtag masks and
one food-growing mask; the earlier user acceptance of the title does not
establish a food-growing definition or authorize changing membership.
[Jack Spirko's original announcement](https://www.thesurvivalpodcast.com/grow-nostr)
and [initiative description](https://www.thesurvivalpodcast.com/lets-grow-nostr)
describe growing Nostr participation and networks through diverse content and
community interaction. They include gardening and food among many possible
subjects; they do not define the initiative as food cultivation.

Tested **PPv30-grownostr-v1** changes one paragraph of PPv30-node-v1 through
native `experiment.py revise`: the meaning is the GrowNostr initiative,
growing Nostr participation, personal networks and communities through diverse
content and interaction. It is identical for every post. All other allocation
instructions and the output schema are unchanged. This is a source-grounded
trial definition, not a production decision or proof of every author's intent.
The new [prompt](prominence-prompt-goal-v1/ppv30-grownostr-v1/PPv30-grownostr-v1.md),
exact edits and native revision receipt are maintained sources.

Native `prepare --from` with fifteen `--only` IDs preserves complete original
post/title inputs, source evidence, Astra-low subscription settings and all
fifteen saved baselines in `experiments/ppv30-grownostr-fixed-meaning-v1`.
Four pre-run agent observations record the stock/steak inconsistency, the
food-growing member and the salsa/Nostr connection. They set no exact
percentage, numerical gap or strict complete order. Native execution completed
all fifteen cases with fifteen fresh calls, no reuses, failures or retries.
Forty-five comparison, ranking, selection and actual local T5 worker checks
pass. No workflow or production code change was necessary.

The authorized run is bounded to thirty attempts including eligible provider
retries, for fifteen distinct post/title inputs. Subscription incremental cash
is zero, with no paid fallback or rentals. Prominence uses the fixed meaning;
relevance reuses the preceding subject-plus-context SSE vectors exactly,
without new encoder work. Native `prominence_cosine.py prepare --include-subject
--post-order highest --reuse-encoding` and `collect` produce the new comparison.
All 738 saved encoding rows remain unchanged; only fifteen own-node values
are used. SSE's learned layers, title, formula and highest
selected-entry post rule remain fixed. Work grows with selected memberships
and full-post text plus one short repeated definition, not all-post/all-node
inputs. The source hierarchy, earlier teacher answers and 99 protected hashes
are preserved. All other 107 nodes in the preceding comparison are untouched;
earlier accepted checks are preserved, not rerun.

| GrowNostr post | Old prominence | Fixed-meaning prominence | Old sorting score | New sorting score |
| --- | ---: | ---: | ---: | ---: |
| Stock preservation (`25f5a4c0`) | 85 | 7 | 71.804681 | 5.913327 |
| Steak/preservation diary (`f67c7c54`) | 2 | 5 | 1.593722 | 3.984306 |
| Food preparation / possible salsa sale on Nostr (`f7ed481e`) | 60 | 11 | 49.151388 | 9.011088 |
| Food growing / another user's allotment (`7d538c44`) | 80 | 15 | 52.349315 | 9.815497 |

The stock and steak allocations now use the same GrowNostr meaning. Their
food preparation and preservation receive represented zero; only their
community framing receives seven and five respectively. The salsa post also
separates food work from explicitly considering a Nostr sale. This corrects
the earlier switch from homegrown food to growing Nostr across those posts;
it does not approve the exact percentages or establish a strict complete order.
Fourteen of fifteen prominence values change; the jetlag greeting stays at 25.
The largely hashtag-based second-coffee update leads the new sorting order at
26.009181, followed by the breakfast greeting at 20.275159 and stove invitation
at 18.162986. Their precise shares and strict ordering remain uncertain.

The food-growing member still has no `#grownostr` tag. Its new fifteen points
come from interpreting the `nostr:npub` reference as recognition of another
Nostr user. Whether this warrants nonzero GrowNostr prominence is unresolved,
especially under the instruction to ignore opaque identifiers; the explicit
food-growing statements themselves receive represented zero. The mixed member
set remains intact. A fixed meaning does not establish correct membership or
prove each author's intended hashtag use.

Fifteen native post-run agent reviews accept three topic-separation/consistency
corrections and retain twelve uncertainties. The four pre-run comments remain
as their original prefix. No user labels, exact percentages or numerical gap
thresholds are added. Native text comparison reports changed outputs; it does
not grade semantic improvement. Agent inspection, rather than that mechanical
change label, supports the interpretation correction.

Independent checks verify every exact complete-post/title input, saved baseline,
allocation total, unchanged SP subject/context and bit-identical reused
relevance value, all fifteen cosine/products, post maxima and the complete
order. The native comparison is
`experiments/ppv30-grownostr-fixed-meaning-v1/relevance-v1/comparison.json`, SHA256
`79a91df5136313d7c2d9920047af451d659d3759a111b9db5be05ae50bba413b`.
Its raw-vector and worker-receipt hashes exactly match the earlier 108-node
subject-plus-context comparison. No worker is run and no new byte/token
selections occur. Original 99 protected hashes, all old experiment comments
and new frozen prompt/receipt/result hashes verify unchanged. Native plans,
receipts, results and reviews are ignored; preparation, execution, verification,
review and test logs are under
`experiments/ppv30-grownostr-fixed-meaning-v1-checks`.

Native usage reports 12,202 input tokens and 2,560 output tokens, including 80
reasoning tokens, with no reported cache tokens. Catalog reference estimate is
$0.250020, separately from subscription incremental cash $0; provider billing
is unavailable and weekly quota is unmeasured. Only this zero-cash reservation
is settled, preserving lifetime monetary totals and unrelated ledger entries.

The result supports supplying one node meaning consistently when assessing
prominence, but this single-node developmental trial does not select a general
node-description method or production prompt. Next recommended work is the
same bounded consistency check for `coffeechain`, using one source-grounded
meaning and fixed relevance/SSE/formula. The user approved the completed trial
below. Broader generation, hierarchy repairs, recursion and production adoption
remain open or outside the authorized comparison.

**Fixed coffeechain meaning approved October 1 (completed):**

The user approved the same check across the eleven saved direct-member posts
in `coffeechain` (`S3c005e1a4f`). All eleven include the hashtag. Unlike the
GrowNostr baseline, their saved prominence answers already mostly describe a
coffee-sharing community, not a chain of businesses. Earlier relationship
experiments did use that unsupported business meaning even after the user's
hashtag-title correction; this trial does not change those results or titles.
The [Nostr community guide](https://quillie.github.io/nostr-wegweiser/)
describes morning coffee and accompanying greetings, and an
[author's public coffeechain greeting](https://thegrinder.npub.pro/post/note1atxm208fgp2nq8fklknqseglftssann06r8y09gmq0re3ea6dt7q0xern2/)
supports that use. Together with the complete saved posts, they ground the
trial meaning: the #coffeechain community on Nostr, where people share coffee
experiences and exchange morning greetings. This is a trial interpretation,
not proof of every author's intent or a production node-description method.

Tested **PPv30-coffeechain-v1** changes only PPv30-node-v1's interpretation
paragraph through native revision. The allocation instructions, schema,
complete post/title inputs, Astra-low subscription settings and eleven saved
baselines stay fixed. Its [prompt](prominence-prompt-goal-v1/ppv30-coffeechain-v1/PPv30-coffeechain-v1.md),
exact edits and revision receipt are maintained sources. Native
`prepare --from` with eleven `--only` IDs produces
`experiments/ppv30-coffeechain-fixed-meaning-v1`. Four native pre-run agent
observations inspected coffee experience versus hashtag association, unrelated
jokes, morning greetings versus household details, and the unusual coffee-shop
occasion. They prescribed no exact prominence, numerical gap or strict order.

All eleven cases completed in eleven fresh, valid calls, without retries,
failures or reuse. The authorized bound was twenty-two attempts including
eligible provider retries, with zero subscription incremental cash and no paid
fallback or rentals. Forty-five existing comparison, ranking, selection and
actual local T5 worker checks pass. Relevance reuses the exact preceding SP
subject-plus-context SSE encoding; native `prominence_cosine.py prepare
--include-subject --post-order highest --reuse-encoding` and `collect` perform
no worker run, new vectors or byte/token selections. All 738 encoding rows
and eleven relevance values are bit-identical. Node title, SSE learned layers,
formula and highest selected-entry post rule remain fixed. Work grows with
selected memberships and full-post text plus one short repeated meaning.
Only eleven own-node cosine values are emitted, not a new cross-node matrix.

| Post (note-ID prefix) | Old prominence | Fixed-meaning prominence | Fixed relevance | Old sorting score | New sorting score |
| --- | ---: | ---: | ---: | ---: | ---: |
| Coffee with cream and egg yolk (`f4c5aa5f`) | 100 | 100 | 0.926226 | 92.622641 | 92.622641 |
| Another coffee / Sunday greeting (`737eaa89`) | 55 | 95 | 0.947389 | 52.106416 | 90.001991 |
| Personal home roasting (`056e6466`) | 12 | 100 | 0.853411 | 10.240937 | 85.341143 |
| Weather / hot coffee / greeting (`82d3d344`) | 30 | 65 | 0.912517 | 27.375512 | 59.313610 |
| Weird coffeechain / coffee-shop rave (`ccbd903d`) | 80 | 70 | 0.805875 | 64.469989 | 56.411241 |
| Greeting / burrito / coffee / pet (`ee3404d5`) | 25 | 48 | 0.944882 | 23.622053 | 45.354342 |
| Music in the coffee shop (`46ed60cb`) | 30 | 45 | 0.914767 | 27.443021 | 41.164532 |
| Greeting / jetlag / breakfast (`a9b49c0a`) | 18 | 35 | 0.804268 | 14.476828 | 28.149388 |
| Greeting / household plans (`61bdef2b`) | 10 | 27 | 0.951503 | 9.515030 | 25.690581 |
| Greeting / gym / breakfast (`bd357fcf`) | 10 | 25 | 0.914744 | 9.147436 | 22.868590 |
| Red-flag jokes / many tags (`41efa59d`) | 2 | 1 | 0.974300 | 1.948600 | 0.974300 |

The home-roasting post now represents its coffee experience and personal taste
journey, not just the twelve-point hashtag association. The coffee-with-cream/
egg-yolk post retains prominence 100 and unchanged sorting score. The red-flag
jokes remain unrelated: their body receives represented zero and only the
hashtag affiliation receives one point. These are the three agent-accepted
interpretation/separation or preservation checks, not new user judgments or
approval of calibrated percentages and the complete strict order.

The fixed meaning also includes morning greetings. This increases prominence
for several mixed greetings while household safety, chicks, workout, travel,
weather, burrito ingredients and pet observations remain separate meaning.
Breakfast is not automatically treated as coffee in the jetlag or gym posts.
Ten prominence values change; coffee with cream and egg yolk stays at 100.

The weather/greeting post has prominence 65 below the rave's 70, but fixed
relevance 0.912517 above 0.805875 makes its sorting score 59.313610 above
56.411241. This reverses their saved sorting order without establishing an
improvement or regression: that strict pair remains unsettled. Another-coffee/
Sunday-greeting also ranks above home roasting after relevance, despite
prominence 95 below 100. Their exact shares and strict relative placement are
uncertain. The result supports explicit shared meaning for this developmental
node; it does not prove that every increased prominence or changed order is
better. The separate Coffee node and all earlier user-accepted checks are
untouched, not relabeled or rerun.

Eleven native post-run agent assessments accept the three stated semantic
checks and retain eight uncertainties. The original four pre-run comments are
preserved; no user labels are added. Comments bind exact prompt/input/output
and this native comparison hash. The native text-change report is mechanical,
not a quality grade. The optional native prominence-viewer check is unavailable
for this experiment: `subject_contexts` is not supported by that view. Review
uses native `show` and `review --case`; no UI/workflow extension is performed.
Both the initially missing `--ui` flag and the corrected unsupported-adapter
result are preserved in the check log; the viewer check is not reported passed.

Independent checks verify all eleven exact complete-post/title inputs, saved
baselines, allocations, unchanged subjects/contexts, cosine/products, post
maxima and the complete native order. The largest difference from an
independent cosine recomputation is 1.1102230246251565e-16. The comparison is
`experiments/ppv30-coffeechain-fixed-meaning-v1/relevance-v1/comparison.json`,
SHA256 `4354f4f3b2a7e06c7fee4e330280e1f5ed5b17550d1caf39fbdc638d838bedf0`.
All 110 earlier protected source/prompt/hierarchy/result/review hashes and
new frozen prompt/plan/receipt/result/comparison hashes remain unchanged.
A concurrent change to `bounded_hierarchy_graph.py` was inspected before
inference and recorded through native code-upgrade provenance with an empty
result prefix. That unrelated module is not called by this subject-context
prominence run; actual input/rendering/execution code and settings were
unchanged. The task changes no workflow or production code, hierarchy, source
memberships, SP/MP inputs or other-node results. Plans, model outputs, reviews
and checks remain ignored artifacts under the experiment and
`experiments/ppv30-coffeechain-fixed-meaning-v1-checks`.

Native usage is 8,184 input tokens and 1,721 output tokens including 234
reasoning tokens, with no reported cache tokens. Catalog reference $0.167890
is separate from incremental subscription cash $0, unavailable provider billing
and unmeasured weekly quota. Only this zero-cash reservation is settled;
lifetime monetary totals and unrelated ledger entries remain unchanged.

The earlier recommendation to derive node meanings from saved SP subjects and
contexts was not approved and is withdrawn. The coffeechain SP contexts mostly
name the hashtag without explaining its community meaning, so those inputs do
not establish a sufficient description source. The user instead approved the
single general prominence-prompt change completed below. General description
generation, calibrated prominence and production adoption remain open.

**General Nostr context approved October 1 (completed):**

The user's "sure" approved one shared prompt on the twenty-six saved post/node
inputs in `grownostr` (`Sa233efc2db`, fifteen) and `coffeechain`
(`S3c005e1a4f`, eleven). They cover twenty-two unique original posts; four
appear in both nodes with different title inputs. Tested **PPv30-nostr-v1**
replaces only PPv30-node-v1's interpretation paragraph: the title comes from
Nostr posts, where hashtags can identify communities, and the complete post
should interpret the title as used on Nostr. Neither node is named in the
template and neither manual definition is supplied. The same
[prompt](prominence-prompt-goal-v1/ppv30-nostr-v1/PPv30-nostr-v1.md) is used for
both. Allocation instructions, schema and Astra-low subscription settings
stay fixed; no definition-generation call or SP/MP step is added.

Native revision and `prepare --from` with twenty-six `--only` IDs preserve all
complete original post/title inputs, source evidence and original PPv30-node-v1
baselines in `experiments/ppv30-nostr-context-v1`. Both completed fixed-definition
experiments remain separate saved references, not newly paired baselines or
new model samples. Every selected input and source entry matches its original,
fixed-definition and new versions. Eight native pre-run agent observations
checked GrowNostr meaning and food/community separation, salsa sale, the
uncertain food-growing member, coffee roasting, focused preparation, unrelated
jokes and mixed weather/greetings. They set no exact percentages, gaps or full
strict order.

All twenty-six cases completed in twenty-six fresh valid calls, with no
failures, retries or reuses, within the fifty-two-attempt bound. Relevance
reuses exact saved SP subject-plus-context SSE encoding through native
`prominence_cosine.py prepare --include-subject --post-order highest
--reuse-encoding` and `collect`. All 738 cached rows and twenty-six relevance
values are bit-identical to both reference versions, with no worker run,
new vectors or selections. SSE final learned layers, titles, formula and
highest selected-entry post rule remain fixed. Work grows with selected
memberships and full-post tokens plus two short sentences. The offline
comparison emits fifty-two selected-title cosines; only twenty-six own-node
values enter sorting. This is not a production cross-node matrix.

GrowNostr order, highest sorting score first:

| Post (note-ID prefix) | Original prominence | Fixed-definition prominence | General Nostr prominence | Fixed-definition sorting score | General Nostr sorting score |
| --- | ---: | ---: | ---: | ---: | ---: |
| Greeting / jetlag / breakfast (`a9b49c0a`) | 25 | 25 | 25 | 16.464491 | 16.464491 |
| Second coffee / hashtags (`862486d8`) | 25 | 40 | 25 | 26.009181 | 16.255738 |
| Food work / possible Nostr salsa sale (`f7ed481e`) | 60 | 11 | 16 | 9.011088 | 13.107037 |
| Greeting / household plans (`61bdef2b`) | 12 | 17 | 12 | 14.658919 | 10.347472 |
| Stove / invitation (`99e6a514`) | 10 | 20 | 10 | 18.162986 | 9.081493 |
| Gianduja store (`b3c0ab8f`) | 8 | 5 | 5 | 3.891874 | 3.891874 |
| Baby / family (`cf50b578`) | 7 | 5 | 5 | 3.559984 | 3.559984 |
| Tolstoy / tags (`be8d07d4`) | 4 | 6 | 5 | 4.140899 | 3.450749 |
| Stock preservation (`25f5a4c0`) | 85 | 7 | 4 | 5.913327 | 3.379044 |
| Greeting / burrito / coffee / pet (`ee3404d5`) | 10 | 30 | 3 | 20.275159 | 2.027516 |
| Steak / preservation / sealer (`f67c7c54`) | 2 | 5 | 2 | 3.984306 | 1.593722 |
| Omelette (`3202cb94`) | 2 | 15 | 2 | 10.570288 | 1.409372 |
| Red-flag jokes / many tags (`41efa59d`) | 2 | 4 | 2 | 2.749973 | 1.374986 |
| High-altitude bread (`03313183`) | 3 | 6 | 2 | 3.977921 | 1.325974 |
| Food growing / allotment (`7d538c44`) | 80 | 15 | 0 | 9.815497 | 0.000000 |

The general instruction preserves the two main GrowNostr interpretation
corrections: stock and steak food work receive represented zero under the
Nostr-growth/community meaning, with prominence four and two respectively.
The salsa post also separates food work from explicitly considering a Nostr
sale. All fifteen outputs use Nostr growth/community rather than substituting
literal food cultivation. The food-growing member now receives zero: unlike
the fixed-definition draw's uncertain fifteen points, its opaque profile
reference is not credited as initiative participation. This fits identifier
exclusion and the same supplied reference meaning; membership is unchanged.
These four agent-accepted interpretation/separation checks do not approve
exact percentages or the complete strict order. Greeting/tag shares remain
uncertain, including the breakfast greeting's three points versus thirty with
the explicit definition. A shared title interpretation does not prove stable
allocation of every community activity.

Coffeechain order, highest sorting score first:

| Post (note-ID prefix) | Original prominence | Fixed-definition prominence | General Nostr prominence | Fixed-definition sorting score | General Nostr sorting score |
| --- | ---: | ---: | ---: | ---: | ---: |
| Coffee with cream and egg yolk (`f4c5aa5f`) | 100 | 100 | 100 | 92.622641 | 92.622641 |
| Personal home roasting (`056e6466`) | 12 | 100 | 100 | 85.341143 | 85.341143 |
| Weird coffeechain / coffee-shop rave (`ccbd903d`) | 80 | 70 | 60 | 56.411241 | 48.352492 |
| Another coffee / Sunday greeting (`737eaa89`) | 55 | 95 | 50 | 90.001991 | 47.369469 |
| Greeting / burrito / coffee / pet (`ee3404d5`) | 25 | 48 | 35 | 45.354342 | 33.070874 |
| Weather / hot coffee / greeting (`82d3d344`) | 30 | 65 | 35 | 59.313610 | 31.938098 |
| Music in the coffee shop (`46ed60cb`) | 30 | 45 | 30 | 41.164532 | 27.443021 |
| Greeting / gym / breakfast (`bd357fcf`) | 10 | 25 | 25 | 22.868590 | 22.868590 |
| Greeting / household plans (`61bdef2b`) | 10 | 27 | 23 | 25.690581 | 21.884569 |
| Greeting / jetlag / breakfast (`a9b49c0a`) | 18 | 35 | 25 | 28.149388 | 20.106706 |
| Red-flag jokes / many tags (`41efa59d`) | 2 | 1 | 2 | 0.974300 | 1.948600 |

Home roasting keeps prominence 100 and sorting score 85.341143, preserving the
fixed-definition correction from the original twelve-point hashtag-only
interpretation. Coffee with cream and egg yolk remains at 100 / 92.622641.
The red-flag joke body remains represented zero; only its community tag gets
two points. Agent review accepts these three checks, not general numerical
calibration or every strict position.

The general prompt does not preserve coffeechain's shared greeting boundary.
In the household post, "Good morning nostr" receives twelve represented points,
and the closing Saturday wishes eleven. In the gym post, "Good morning"
receives twenty-five. Yet the weather post's "GM Nostr!" / "Happy Sunday!"
receives zero represented points out of twenty, and the another-coffee post's
morning/Sunday wishes zero out of forty-five. All four contain #coffeechain.
The saved fixed definition included these greetings; no exact share is needed
to identify the inconsistent inclusion rule. Agent review rejects those two
omissions as failures to preserve that meaning, rather than rejecting 35 or
50 merely because they differ from 65 or 95.

This affects the order: another-coffee drops from sorting score 90.001991 with
the fixed definition to 47.369469 and falls below the rave's 48.352492. Weather/
coffee drops from 59.313610 to 31.938098. Those are observed consequences, not
new user-labeled pairs or calibrated gap limits. Exact shares and other
mixed-post positions remain uncertain. The general instruction helps on the
stated interpretation failures but is not a complete substitute for one
explicit node meaning; it is tested, not adopted as the production prompt.
Sixteen of twenty-six prominence values change versus the original and twenty
versus the fixed-definition references, while all twenty-six output texts
change. The native text-change report is mechanical, not a quality grade.

Twenty-six native post-run agent reviews record seven semantic accepts, two
greeting-consistency rejects and seventeen uncertainties. The eight original
pre-run comments and all prior user labels remain unchanged. Comments bind
exact input/output hashes and this native comparison, SHA256
`d59df07efa70fd5ab0e7b00cc82a3c97c8209f6af94ede005ae7f2f9bb2a1be0`, under
`experiments/ppv30-nostr-context-v1/relevance-v1/comparison.json`.
Independent checks verify all twenty-six exact full inputs and baselines,
allocations, unchanged subjects/contexts, bit-identical relevance, products,
post maxima and both complete orders. Maximum independent cosine difference is
1.1102230246251565e-16. All 123 earlier protected source/prompt/hierarchy/result/
review hashes and new frozen prompt/plan/receipt/result/comparison hashes are
unchanged. No code upgrade was required during execution. Forty-five existing
comparison/ranking/selection/worker tests pass, including local T5 integration.
The optional prominence viewer remains unsupported for subject-context inputs;
it is not claimed passed or extended. Review uses native `show --case` and
`review --case`, with exact critical posts inspected. The task changes no
workflow/production code, hierarchy, membership, other-node result or SP/MP
source. Earlier accepted Coffee/Eggs/Music and full-order checks are preserved,
not rerun or relabeled. Plans, results, reviews and checks are ignored under
the experiment and `experiments/ppv30-nostr-context-v1-checks`.

Native usage is 19,382 input tokens and 5,367 output tokens including 864
reasoning tokens, with no reported cache tokens. Catalog reference $0.462170
is separate from incremental subscription cash $0, unavailable provider billing
and unmeasured weekly quota. Only this zero-cash reservation is settled;
lifetime monetary totals and unrelated accounting are unchanged.

The subsequently approved read-only inspection is complete. Both current
TPv38 calls sent only the selected mask fragments: eleven repetitions of
coffeechain's name, and fourteen GrowNostr names plus one food-growing mask.
Full source posts are review evidence, not model input. These inputs do not
establish a sufficient shared description source. Frozen TPv38 remains intact;
the earlier SP-only generation proposal remains withdrawn.

**General sorting investigation approved October 1 (in progress):**

The user authorizes architectural choices and experiments until satisfactory
or two hours pass, with a deadline of October 2 at 02:09:48 UTC. The ceiling
is 2,000 OpenAI subscription calls using 6.1 Sol at medium effort or lower.
The agent assesses transfer without requesting new user labels, preserves prior
user judgments, commits completed checkpoints and reports status at the stop.
No paid fallback, rental, push or production deployment is included.

The first control, `experiments/sorting-general-v1-nostr-sol-control`, keeps
PPv30-nostr-v1 and all twenty-six original inputs fixed and changes only the
model to gpt-6.1-sol / medium. Twenty-six fresh first-attempt calls are valid.
Eight pre-run agent observations prescribe no exact percentages. Sol preserves
the focused roasting/preparation and food/community separation checks, but
still counts household/gym greetings while omitting weather/another-coffee
greetings. One stove output newly substitutes gardening/food growing for
GrowNostr. Model choice alone therefore does not establish consistent meaning.

The shared workflow now supports `node_descriptions` source selections with
`schema_version`, `source_packets`, `hierarchy` and optional `nodes`. It checks
original mask spans and references, combines original source groups for merged
nodes, deduplicates masks within posts and selects at most eight distinct
complete posts in note-ID order. JSON input is bounded to 12,000 characters.
Whole posts that exceed the bound are skipped with reasons; nothing is silently
truncated. All original evidence, selected/skipped identities and source hashes
remain frozen. This is a mechanical sample, not proven semantic coverage.

**NodeDescription-v1 (tested, rejected for GrowNostr)** generated two valid
first-attempt descriptions, but inferred a gardening/homesteading purpose from
the subjects in tagged posts. That description was rejected before prominence.
**NodeDescription-v2 (tested, experimental)** explicitly distinguishes a named
community's purpose from subjects its members discuss. The two fresh outputs
retain coffeechain's coffee/community meaning and leave GrowNostr's purpose
unresolved instead of inventing a gardening definition. The same prompt then
produced all 108 sorting-node descriptions: 106 fresh calls and two verified
reuses, all valid. An independent twenty-node scope audit found eighteen
acceptable and two uncertain (GrowNostr's unresolved purpose; Brands' ambiguous
zap mask), with no hard scope changes. This is an agent assessment, not new user
approval or proof of unseen-corpus transfer.

Collected descriptions are opt-in `subject_contexts` inputs through the
selection's `descriptions` reference and `prominence_basis: "node_title"`.
Preparation checks IDs/titles and supplies the same meaning to every post.
**PPv31-node-description-v1 (tested, experimental)** preserves allocations and
schema. Its two-node trial completed twenty-six fresh valid requests. Coffeechain
now represents greetings consistently while separating weather, exercise and
household subjects; focused roasting and cream/yolk preparation remain fully
coffee-centered. GrowNostr food cultivation remains zero, and food work stays
separate from community association/Nostr commerce. GrowNostr still omits the
household/burrito greetings while counting jetlag's greeting: two native rejects
record that inconsistency, without prescribed percentages.

**PPv32-community-meaning-v1 (tested, rejected)** adds a general community
interaction rule. Twenty-six valid fresh calls fix GrowNostr's greetings but
incorrectly reduce focused coffee roasting/preparation to the sharing act.
Three native rejects preserve that regression. **PPv33-community-meaning-v2
(tested, experimental)** clarifies that both the description's substantive
subjects and community interaction count. Its twenty-six valid fresh calls
restore focused coffee to 100 and retain consistent greetings across the two
nodes. GrowNostr's exact purpose remains unresolved; percentages are not
calibrated or approved.

The separate Sol control across 108 nodes completed all 633 SP cases/380
post-node inputs: 354 fresh requests and 279 verified reuses, no failures or
provider retries. Thirty-five additional subject-transfer directions were
identified from exact complete posts independently of new outputs. The combined
sorting score passes 34; the pizza restaurant plan versus Pizza-Day greeting
reverses, because prominence 75 versus 90 outweighs relevance. All eleven clear
user directions pass; prominence alone loses iced coffee versus cream/yolk.
Eggs, Music and Photography accepted orders hold. Coffee's complete order
changes beyond permitted about-equal swaps, recorded as one discrepancy rather
than new strict pair labels. The twenty additional agent directions each pass
both formulas. These are same-corpus regression observations, not fresh user
labels or proof of general transfer. Relevance reused all 738 cached rows.

The 108-node PPv31 shared-description comparison completed 633 valid cases with
355 fresh attempts (one provider retry) and 279 verified reuses. All 633 relevance
cosines and the raw-vector hash match the control, with no new encoding. Its
combined sorting passes all thirty-five agent directions, including the pizza
comparison, but only ten of eleven clear user directions. The Coffee description
explicitly includes “enjoying coffee in different places”; the cool-places post
then receives prominence 100, as does focused cream/yolk coffee. Fixed relevance
puts cool places above cream/yolk, violating the prior user direction. Music and
Photography orders hold; Eggs swaps two accepted displayed positions, and Coffee's
complete order still differs. This is not an adopted improvement.

**NodeDescription-v3 (tested on seven nodes, experimental)** requests the title's
subject and explicit relationships without a catalogue of sampled settings or
activities. Seven fresh valid descriptions remove Coffee's places clause and keep
Eggs broad across raw/cooked/preserved forms. GrowNostr remains unresolved; Food
and drink's establishment extension and Pizza-Day elaboration remain uncertain.
The same version completed all 108 nodes with 101 fresh calls and seven verified
reuses; scope review is complete with eighteen accepts and seven uncertainties in
twenty-five native reviews; no hard scope changes were identified.

The native **node_sorting** adapter tests direct complete-post sorting scores.
It uses the existing source-bound memberships and optional shared descriptions;
SP entries identify saved membership only and are not model scoring inputs.
Each identical post/title/meaning request is reused across those entries.
Outputs are exactly integer `sorting_score` 0–100 and a nonempty `reason`.
Offline collection emits `node-sorting.json` with one judgment and descending
order per node/post, rejects conflicting duplicates and protects all source
references. There are no SSE requests or highest-SP aggregation in this trial.
Default prominence adapters and the existing candidate formula remain intact.

**NodeSorting-v1 (draft, superseded before inference)** states relative focus and
semantic relevance as one within-node sorting score. **NodeSorting-v2
(tested, rejected as a replacement)** adds the general community-tag clarification
from independent prompt review. Neither version claims a calibrated percentage.
The fifteen-post nonfood trial
completed 99 SP cases with fifteen fresh calls and 84 reuses; all ten fixed agent
directions pass, with no failures or ties. Literature ordering remains uncertain.
The v2 broad trial uses the 108 v2 descriptions and preserves original user and
agent observations. A separate trial uses fifteen saved posts in Literature,
Psychology and philosophy, and Bitcoin. All fifteen are disjoint from the 98
original description-source posts, but were previously studied; they are
held out from the description request, not a new corpus. Three v2 descriptions
were generated from original masks/posts only and independently reviewed before
these scoring inputs. Ten additional agent directions were fixed beforehand;
Literature's full order remains uncertain. No new user labels are requested.

The direct broad trial completed 633 valid cases with 380 fresh calls and
253 reuses. It preserves eight of eleven clear user directions, reverses one
Eggs direction and ties two Coffee directions; ties are not strict passes.
Photography reverses its accepted first two posts. Of thirty-five additional
agent directions, thirty-two pass, one fails and two tie. Multiple maximum
sorting scores lose distinctions between posts. Nonfood success therefore does
not establish a general replacement for prominence times relevance.

The revised-description prominence trial uses **PPv33-community-meaning-v2** and
NodeDescription-v3 across forty-one selected nodes. Its first 142-SP selection
omitted some other SP entries of the same posts; that can alter the highest-SP
sorting score. Native preparation expanded the same 122 post/node inputs to
all 202 SP entries, reusing every prominence answer with zero new calls. Final
comparison passes all thirty-five agent directions and eleven clear user
comparisons. Photography still reverses its accepted order; Coffee and Eggs
complete orders differ. All 202 cosines and cached vector hashes remain exact.
Coffeechain greetings are consistent; GrowNostr's bare-tag participation boundary
remains uncertain, without inventing a food-growing community purpose.

A separate bare-title control stress test requests independent answers for all
46 protected SP entries, including identical post inputs. All eleven clear
comparisons pass, but an Eggs direction has only a 0.072130 sorting-score gap.
Prominence varies across six identical-input groups, and highest-SP collection
also selects among those answers. This differs from the default reuse of one
judgment per identical post/title/meaning input; it exposes variation rather
than establishing calibrated uncertainty or a new production aggregation rule.

**PPv34-mixed-meaning-v1 (tested, experimental)** clarifies separate meanings in
lists and attributions without splitting synonyms or assigning fixed ratios.
The 202-case trial completes with 120 fresh calls and 82 reuses, preserving
all thirty-five agent directions and eleven clear user comparisons. Photography's
accepted order is restored. Eggs still swaps burrito and dinner in this run;
Coffee's complete order differs. The independent 46-answer protected repeat
preserves all eleven directions and complete Eggs, Music and Photography orders,
while Coffee still differs. Its smallest observed diary sorting score exceeds
the largest raw-yolk sorting score by 1.336308, compared with the control stress
test's near-tie. These are observed answers, not calibrated confidence bounds.

PPv33 also passes all ten nonfood directions with prominence alone and with
SP subject-plus-context relevance. The historical nonfood comparison encoded
context alone; native cache reuse correctly rejected that representation change.
A local offline SSE run encoded 102 current rows (99 contexts plus three titles).
No provider encoder calls were made. Memberships and model settings are unchanged;
all 99 cosines differ from the context-only reference, so exact relevance reuse
is not claimed. Literature's complete order remains uncertain.

**PPv35-post-meaning-v1 (tested, experimental)** keeps an argument's comparison,
criticism or invitation attached to the subject it addresses unless it adds
separately meaningful content about another subject. It adds no node names,
post examples, numerical targets or percentage calibration. All 202 cases
complete with 108 fresh calls and 94 reuses. Combined sorting preserves all
eleven clear user directions and thirty-five agent directions, plus the accepted
Eggs, Music and Photography complete orders. Coffee's fourteen-post order still
differs beyond its four about-equal pairs: the request is above iced coffee,
half-and-half above the second-coffee post, and weather/burrito above movement.
These complete-order differences remain uncertain rather than new strict labels;
the earlier slight weather preference and subsequent complete review remain saved.

The separate Coffee stress test uses nineteen fresh answers and passes all six
clear Coffee directions. Decaf's preference argument, comparison and invitation
now all concern Coffee: prominence is 100 instead of the PPv34 stress answer's
85, without prescribing either percentage. Identical places inputs still vary
from 70 to 80. The 202-case run reused these fourteen Coffee post answers from
the parallel stress test through the normal memo; it is not independent Coffee
replication. The separate fifteen-call nonfood trial passes all ten earlier
agent directions. All 99 current SP-context cosines and 102 vector/receipt rows
are exact reuses; Literature ordering and religious/philosophical overlap remain
uncertain. No new labels, node-specific examples or numeric exceptions were added.

Final session accounting records **1,920 subscription provider attempts**, including
one retry, across twenty-three native trials, all gpt-6.1-sol / medium and below
the 2,000-call limit. Inference is complete before the 02:09:48 UTC deadline.
The strongest current candidate remains prominence times SP subject-plus-context
relevance, using a fixed node meaning and PPv35. It is experimental: Coffee's
complete order, answer variation, uncertain node meanings, representation choice
and transfer to a new corpus remain open. The investigation is not satisfactory
for product adoption; pause and report at the two-hour deadline. Completed support,
prompts, configurations and maintained evidence are committed locally.

**PPv35 good-enough audit approved October 2:** The subsequent user decision
replaces percentage repeatability as a stopping criterion with useful browsing
order. Evaluate the current PPv35-post-meaning-v1 candidate across twelve varied
node meanings using fresh-to-sorting posts. Review complete orders and their
first ten posts where available, retaining smaller cohort sizes explicitly.
Allow isolated mistakes and close swaps; revise only for a substantial recurring
browsing problem across nodes or an independent rerun. Keep all existing strict
judgments, accepted orders and permitted swaps distinct. If the audit passes,
freeze the candidate for the next browsing build and stop searching for another
prompt or architecture. This is a bounded evaluation, not a requirement for
identical percentages, a numeric accuracy claim, new user labels or production
deployment. Fixed meanings, prominence × SP subject-plus-context relevance,
SSE learned layers and highest-entry selection remain the audit's controls.

**Finite PPv35 audit completed October 2 — freeze for the next browsing build:**
The first and genuinely independent repeat both pass the agreed browsing rule.
Twelve native agent reviews accept complete orders for twelve meanings and 101
diagnostic post/node assignments from 62 complete fresh-to-sorting posts.
The two original source carriers prepared 760 SP cases; before order review,
six related saved entries were added through native supplements while retaining
the immutable original inputs. Final comparison covers 766 entries and 639
local SSE rows. Supplements reuse full-post/node prominence; they add no
first-pass calls. Existing SP subjects/contexts, hierarchy titles, NodeDescription-v3
meanings and final learned SSE layers remain fixed. Native post aggregation
uses the maximum entry `P * (clip(cosine, -1, 1) + 1) / 2`, never separately
combining maxima of P and relevance.

First-pass prominence uses 101 new subscription answers. An isolated empty
history root supplies another 101 independent answers with normal duplicate
reuse retained; do not use `--repeat`, which disables that reuse. The repeat's
one runner-exit failure remains saved in `ppv35-good-enough-v1-music-repeat`.
Native resume leaves that terminal failure unchanged, so a clean native
`--from` preparation, `ppv35-good-enough-v1-music-repeat-completed`, reuses all
542 successful same-repeat-root answers with zero new calls. All entries for
each post/node share the same prominence answer. The persistent native budget
records **203 attempts: 202 fresh successful answers plus one runner failure**,
below the admitted 404 ceiling; incremental subscription cash is zero. Native
per-experiment usage and catalog estimates remain separate from actual cash;
no manual token/cost aggregation, paid fallback or rented compute.

The first complete orders are in
`experiments/ppv35-good-enough-v1-relevance/comparison.json`; the repeat is in
`experiments/ppv35-good-enough-v1-relevance-repeat/comparison.json`, reusing the
exact first encoding. Full score-hidden views and frozen source assessments
are ignored artifacts under `experiments/ppv35-good-enough-v1-inputs/`.
The Music/Art/nostr/Family/Movement/Festive/Food/Positive-emotions orders change
among close or mixed posts; Communication/Animals/Coffee/Chocolate orders do
not change. Clear focused-versus-incidental contrasts survive both passes.
The first possible Food-list/cats swap reverses; a lower Festive restaurant/
prospective-party swap is acceptable. No substantial recurring browsing error
was found. Communication has one clear positive, Chocolate only four topical
posts, Coffee no wholly beverage-focused positive; music-heavy sources and
shared posts limit transfer claims. Diagnostic assignments are not saved or
new production hierarchy memberships. Earlier user labels remain separate.

This later audit applies the user's stopping rule and supersedes continued
prompt search based on the earlier session's dissatisfaction or percentage
variation. Freeze PPv35, NodeDescription-v3 meanings, prominence times SP
subject-plus-context relevance and highest-entry selection for the next
browsing build. Production implementation and launch-scale validation remain
open; reopen tuning only after a concrete substantial recurring browsing
failure. No prompt, scorer, SSE architecture, node-specific correction or
production deployment was changed. The existing native workflow checks pass:
135 of 136 initially pass; the remaining check lacked `tiktoken` and passes
with the cached dependency, alongside nine additional relevant checks. All
133 earlier protected artifact hashes still match.

The minimal direct-sorting production CLI tests first failed for the missing
adapter, then passed. The 159 relevant workflow, selection, description,
collection, legacy sorting, title and hierarchy tests pass under `uv` with
`tiktoken`. Legacy sorting tests remain unchanged. All 133 earlier protected
artifact hashes verify. Direct scores are an architecture experiment, not a
replacement adopted into the product. These earlier direct-score trials did
not select a production scoring method.

All 108 v2 descriptions were independently
reviewed against masks and ninety unique complete source posts. No hard generated
scope redefinition was found; twenty-five native reviews record eighteen accepts
and seven uncertainties, chiefly existing title/mask mismatches (Brands/zap,
Coffee flavor/gamey meat, Onions/tomato joke, guarani/gianduja, Daily painting/daily,
Motor vehicles/chicken enclosure) and GrowNostr's unresolved purpose. Other
outputs were inspected without prescribing numerical values.

Default contracts remain intact. Changed inputs retain native `input_mismatch`.
Offline sorting preparation validates the description record and exact source
hash against the saved experiment before reusing unchanged title/SP-context
vectors. The compatibility test first reproduced the input/evidence mismatch;
the implementation introduces no new encoding or changed relevance.

One description request per node has bounded context; subsequent prominence
requests add one description bounded to 1,200 characters per post/node pair.
Work follows existing memberships, not all posts against all nodes. Initial
comparisons retain the existing SP subject-plus-context relevance, SSE learned
layers and formula, so interpretation changes can be isolated. Production
adoption, description quality, sampling coverage and any formula change remain
open. Source-changing tests demonstrate the missing capabilities before the
implementation; collection validates receipts and every referenced source.

The user selected Photography in the untouched raw Jev hierarchy for the first
combined-score trial. This is not prominence-only hierarchy sorting: the intended
within-node score is prominence times mask relevance. On September 29, the user
dropped recursive sorting: scores are evaluated within each node, without
parent-child score transfer. Rescaled title cosine remains a candidate for
relevance, not a calibrated percentage. This trial does not decide deduplicated
post ordering.
The saved result is
`experiments/ppv30-diverse-nodes-v1/photography-cosine-v1/comparison.json`.
The five original masks retain their saved PPv30 scores and contextual SSE
vectors. Only the Photography title and a V0964 replay were encoded locally,
with the same checkpoint, model artifacts and runtime versions. Replay cosine
was 0.9999999999999587; maximum normalized component error was 3.29e-8.
Descending combined order: V0964 10.4013 (prominence 13, cosine .600198),
V0765 7.0840 (8, .770990), V0963 3.5640 (4, .782018), V0767 1.8620
(2, .861961), V0688 .9651 (1, .930152). Ordering is unchanged from prominence
alone; weights range from .800099 to .965076, so this is not evidence of an
ordering improvement. No prominence/Jev/title-generation calls, UI changes,
manual placement corrections or membership changes occurred. The default
Python lacked torch, and an offline uv resolution failed before inference;
the existing cached matching runtime completed the single two-row SSE job
without installing packages or accessing the network.

The subsequent authorized Coffee trial uses `experiments/ppv30-coffee-node-v1`
and its matching reusable spec. Its 17 masks across 14 posts are exactly the
direct `matched_instances` of raw Jev node
`merged-426504446eac3b0f75ffa4893679c656567164616668f15f579713918a00a869`
in `target/hierarchy-build-v1/hr02-jev-browser-v1/named-graph.json`.
Original mask IDs are recovered from membership origins; no descendant masks,
membership expansion or manual corrections are included. Production prominence
preparation validates the spans and constructs the same input representation
used for Photography. PPv30, its schema and Astra-low subscription settings
are unchanged. Exact-request lookup found no reusable answers: 17 new calls
completed, all valid, without retries or baseline calls. Allocation sums and
exact membership/input checks passed; no prompt promotion is implied.

Scores span 1–100. The three masks of More coffee in cool places scored 100
(complete text, V0504), 85 (coffee in cool places, V0503), and 40 (coffee alone,
V0502). The incidental Coffee hashtag beneath the Tolstoy quotation scored 1
(V0690). This supplies a wider range than Photography; it does not establish
calibration or a user verdict. The saved combined comparison is
`experiments/ppv30-coffee-node-v1/cosine-v1/comparison.json`. Existing SSE mask
vectors are reused; only the exact node title coffee and one V0504 replay were
encoded locally with the matching checkpoint/runtime. Replay cosine was
0.999999999999949 and maximum normalized component error 4.40e-8. Rescaled
title-cosine weights span .8815–.9912 and change only prominence ties, not the
ordering of unequal prominence scores. No ordering improvement is established.

Review all 17 direct masks in combined order, one inline mask per full post:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector && \
python3 experiment.py review experiments/ppv30-coffee-node-v1 \
  --ui --view prominence \
  --cosine-comparison experiments/ppv30-coffee-node-v1/cosine-v1/comparison.json \
  --ordering 'Linear cosine'
```

The next step is user review of this ordering, not additional inference or a
prompt edit. The UI retains comments and the original hierarchy is unchanged.

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

First check whether existing generic variables, schemas or adapters cover the
task. If not, extend the appropriate shared capability with the smallest reusable
change. Keep the runner general-purpose; do not hard-code an experiment's cases
or add a second execution path or experiment-specific report script.

For missing source-data preparation or validation, extend
[experiment_inputs.py](experiment_inputs.py). A generic adapter accepting an
already-assembled `cases.json` does not automate gathering those cases from saved
data. Do not fill that gap by manually copying subject entries, posts, IDs or
hashes into large case files, or passing generated payloads through patches.
Reusable preparation code must assemble the model inputs and separate review
evidence from the saved sources. Authoring prompts/specs, choosing cases and
assessing results remain deliberate inputs, not mechanical artifact assembly.

Reuse the shared executor, receipts and reporting. For each behavior change,
first add a failing test through the actual CLI or production codepath, implement
the capability, then run the relevant regression tests with offline transport
fixtures. Do not rerun model calls merely to add a preparation capability.
