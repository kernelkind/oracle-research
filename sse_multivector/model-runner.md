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
is absent. Both chat transports request streaming; an explicitly different
response type is still respected. The observer leaves headers and forwarded
bytes unchanged, and captures body-error causes before the SDK reduces them to
messages such as `terminated`.

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

Only `run` performs inference. `prepare`, `show`, `revise`, `review` and
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

The shared prompt executor fills available concurrency slots independently; a
slow or failed case does not hold later cases behind a batch barrier. Only an
explicit temporary provider error (HTTP/stream error code 408, 429, 500, 502,
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

Once their wait expires, eligible retries run before untouched cases, ordered
by retry deadline. While a retry is still waiting, independent cases can run.
Already-running calls are not interrupted. This priority also applies on resume;
it changes neither retry eligibility nor the two-total-attempts limit.

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

`prepare --reuse-encoding COMPLETED_OUTPUT` permits new prominence assessments
to use a completed comparison's exact vectors. Every encoder note, selection
and row order must match. The saved comparison's vector and receipt hashes are
verified; its plan, request, comparison, receipt and vectors are protected
inputs. `collect` validates the original worker receipt against its original
request and plan and uses the existing raw vectors. The new comparison records
`encoding_source`. Run `collect` directly after preparation; no worker run is
needed. Changed encoder input or modified source artifacts are refused.

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

Both prominence alone and the sorting score also match the nine clear checks:

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

On September 30, the user reviewed the complete mixed diary (`eaa6a5e6`) as A
and coffee with raw cream and raw egg yolk (`f4c5aa5f`) as B inside Eggs, with
the image URL omitted, and answered "A". This adds an eighth clear expected
order. The node-title trial already puts the diary first, whereas v2 put the
raw-egg-yolk coffee post first (43.724941 > 33.703212). The user approved this
order, not the assessed percentages, formula or production adoption. No new
model calls, encoding, prompt edits or sorting calculations were needed.

The tentative roasting/short-post judgment remains separate from the nine
clear-check count. The earlier about-equal pair also remains separate: another
coffee has prominence 50 and sorting score 42.357665; errands has 60 and
41.622349. The difference is 0.735316 in the tentatively preferred direction,
without an agreed tolerance or a claim that closeness passed.

The user next reviewed the complete decaf-drinkers post (`2dc50a30`, A) and
roasting post (`056e6466`, B) inside Coffee, with the image URL omitted, and
answered "hm i'd say they're about the same" on September 30. Record about
equal with no preferred direction, separately from the nine clear orders.
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

Complete node-title prominence orders, descending by highest sorting score:

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

Relative to v2, 11 Coffee pair directions and one Eggs pair direction change.
The roasting/short-post direction matches the user's tentative judgment.
Putting the diary above coffee with raw egg yolk matches the new clear judgment.
Putting coffee with raw egg yolk above More coffee in cool places matches the
ninth clear judgment.
Decaf versus roasting was reviewed as about equal, without a preferred
direction. The other changed directions are not new user-approved orders.
PPv30-node-v1 is tested, not production-frozen. These results do not
establish general ordering quality, calibrated percentages, production adoption
or a general advantage from relevance over prominence alone.

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
