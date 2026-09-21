# General model runner

[run-model.sh](run-model.sh) sends one caller-supplied prompt through pi-ai.
It replaces the removed `codex_exec.py` execution tool. No subject, mask, title,
corpus, or model is selected for you.

Use this tool for new model calls. The [extraction pipeline](extraction_pipeline.py)
and [frozen comparison adapter](frontier_runner/runner.mjs) are callers of the
same transport, not separate model-execution implementations.

For offline prompt revisions, run `extraction_pipeline.py revise-prompt --help`.
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

## Request

Required fields:

- `provider`: `openai-codex` for subscription access, or `openrouter`.
- `model`: the exact model ID.
- `reasoning`: a supported pi-ai effort, or `provider-default`.
- `prompt`: the exact string to send. Whitespace and Unicode are preserved.
  Invalid Unicode is rejected rather than silently changed.

Optional fields:

- `schema`: a JSON Schema for the response. Omit it for ordinary text.
- `timeout_seconds`: integer from 1 to 3600; default 300.
- `max_output_tokens`: required for OpenRouter. Rejected for subscription calls,
  because that SDK transport does not enforce it.
- `debug`: OpenRouter-only object containing `echo_upstream_body: true` or
  `false`. Omit it for ordinary calls. Enabling it requests OpenRouter's upstream
  request echo and records a bounded event timeline; it changes no model settings.

Unknown fields, models, reasoning settings, and unsupported transports fail
explicitly. The pinned pi-ai catalog supplies model metadata; OpenRouter entries
using `openai-completions` are supported. Other catalog transports are not silently
rerouted. DeepSeek V4.1 Flash has an explicit catalog addition because the pinned
SDK predates that release.

Schemas are checked locally without coercion, inserted defaults, removed
properties, or remote reference fetching. Draft-07, 2019-09, and 2020-12 are
supported. Provider support can be narrower: the exact schema is requested,
and a provider rejection stays a failure rather than causing a format fallback.

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
Do not put credentials in request JSON or repository files. Returned request
headers redact the local capability. Offline checks cover ordinary and frozen
adapter calls with the real pi-ai transport; no paid verification is implied.

**A send flag is not spending approval.** The [repository budget rules](../AGENTS.md)
authorize user-requested OpenRouter work roughly estimated at $1 or less without
another approval question or a provider-side cap; use a quick judgment, not a
detailed calculation. Other paid work still needs explicit spending approval and
a provider-side limit. Ledger accounting and the lifetime ceiling always apply.
Timeouts and output-token caps are not monetary hard caps.

Each call has one user message, empty application-supplied system instructions,
and no tools, history, AGENTS.md, skills, environment context, or added instruction
sentence. The model's response does not trigger tools or additional calls.
No automatic retries, response repair, or model substitution occurs.

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

## Preserved batches and extraction workflows

[extraction_pipeline.py](extraction_pipeline.py) retains arbitrary prompt batches,
subject extraction, and the existing takeaway/prominence/mask workflows.
[claim_exec.py](claim_exec.py) retains claim extraction. These scripts construct
task inputs and save progress; they invoke `run-model.sh` for model execution.

Saved run artifacts are experiment data and must not be committed. Preserve them
outside Git for reuse and investigation; this policy does not authorize deleting
existing results. Reusable code, tests, prompts and maintained documentation are
separate from run data even when stored beside it. Repository ignore rules now
exclude data files in versioned SSE experiment directories, including rendered
per-run configurations and generated schema copies, without hiding whole
directories. Source schemas, prompt-version metadata and test fixtures remain
eligible for tracking. Numeric arrays and model-weight files under
`sse_multivector/` are also ignored. Existing tracked experiment data is unchanged:
ignore rules do not remove files already in Git.

A prompt-batch configuration uses:

```json
{
  "schema_version": 1,
  "runner_binary": "/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-model.sh",
  "provider": "openai-codex",
  "auth_file": null,
  "run_directory": "new-run",
  "model": "gpt-6-astra",
  "reasoning_effort": "low",
  "concurrency": 16,
  "prompts": [
    {"prompt_id": "example", "text": "Your exact prompt"}
  ]
}
```

Execute with `python3 sse_multivector/extraction_pipeline.py prompt CONFIG.json`
from the repository root. For subscription calls, set `auth_file` to null to use
the selected account's credential service. File paths are no longer
supported. Preserve historical configs and use a fresh run directory for the
changed runner identity.
For OpenRouter set `auth_file` to null and supply
`max_output_tokens`. Paths resolve relative to the configuration file.
Extraction-specific normalization, schemas, note loading, and prompt registries
belong to the workflow, not the general runner.

Saved `prompt` batches default to **16 concurrent calls**. Set `concurrency` to
any positive integer to override that limit; `1` requests sequential execution.
The existing executor limits both active and queued work in waves. If a call
fails, already-started calls finish and save their receipts, but later waves do
not start. Final responses remain in input order even when calls finish out of
order. Concurrency is recorded in the batch manifest, not sent to the model or
included in the identical-request reuse key. It is a local scheduling limit,
not a statement of the provider's rate limits. The single-call `run-model.sh`
transport and the separate `masks` concurrency settings below are unchanged.

Batches save manifests, per-attempt results, and final output. Repeating an
unchanged configuration reuses completed jobs; failed jobs require an explicit
`--retry-failed`. Changes in inputs, settings, or transport identity require a new
run directory. Workflow-code changes also require one by default. Pipeline batch
mode retains the explicit `--runner-upgrade-reason` exception for wrapper-only
changes, recording the boundary in its upgrade ledger; this cannot change the
transport or disguise historical Codex calls as pi-ai calls.
New subject and claim manifests use schema version 2
to distinguish the new execution provenance.

### Reusing requests across saved runs

Saved `prompt` and `masks` batches look up identical successful requests before
sending. The SHA-256 key includes the **complete rendered prompt** (including the
note and subject), provider, model, reasoning setting, output schema and property
order, output-token limit, timeout, and transport identity. Run paths, job IDs,
prompt-version labels, and credential-file paths do not determine equivalence.
Changing an instruction or the source text therefore requires a new call.

By default, history is searched under the configuration's Git repository, or its
directory when outside a repository. `--history-root DIRECTORY` selects a shared
location explicitly. Saved pi-ai receipts from before this feature are eligible;
legacy Codex calls with different context are not. The ignored
`.model-request-history/` directory contains request locks and receipt references,
not additional copies of prompts or credentials. Batches sharing a history root
serialize only identical requests; unrelated requests remain concurrent.

Reuse verifies the original manifest, exact request, and response hashes.
Corrupt matching evidence stops execution rather than silently spending again.
Failed calls and mechanically invalid masks are not reused. A valid receipt is
not semantic approval: an unwanted but structurally valid answer requires an
intentional repeat or a changed prompt.

The new run records `execution: "cross_run_reuse"`, `request_sha256`, and
`reused_from`, pointing to the original receipt. It records zero new usage and
does not count the result as another independent trial. Keep the original files
available for verification. Mask summaries distinguish `reused_results` from
`new_attempts` and `saved_attempts`, which count actual model calls.

For an **intentional independent trial**, use a new run directory and `--repeat`:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 sse_multivector/extraction_pipeline.py masks repeat-config.json --repeat
```

This choice is recorded in the manifest. Resuming that run still reuses its own
completed jobs; `--repeat` does not overwrite results. `prompt CONFIG.json`
accepts the same option. The bare `run-model.sh` transport, unsaved `prompt --text`
calls, and the older full-pipeline/subject/claim workflows are unchanged; their
existing explicit reuse mechanisms remain separate.

### Saved subjects → masks → review

Use `extraction_pipeline.py masks CONFIG.json` for this workflow. One config
covers the whole selection; do not create a config per subject or launch waves
manually. The general pi-ai runner is unchanged and remains usable for arbitrary
prompts, text responses, and caller-provided schemas.

The input is a saved JSON document with `schema_version: 1` and `notes`. Each note
has `note_id`, the complete original `text`, and a `subjects` array. Subjects may
be strings, ASv6.37 objects with `subject`, or existing pipeline objects with
`text`. Extra provenance, heading numbers, and context fields are retained in
the input snapshot but **are not sent** to mask calls. Optional `note_ids` selects
notes by their exact IDs; every subject from each selected note is included.

```json
{
  "schema_version": 1,
  "runner_binary": "/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-model.sh",
  "provider": "openai-codex",
  "auth_file": null,
  "input_path": "saved-subjects.json",
  "prompt_path": "mask-prompt.md",
  "run_directory": "mask-run",
  "model": "gpt-6-astra",
  "reasoning_effort": "low",
  "concurrency": 10
}
```

The caller supplies the prompt and model. The template must contain `{POST}` and
`{SUBJECT}` exactly once each. The default `mask_format: "fragments"` preserves
the legacy fragment-array output. For positional prompts such as MPv3.43, set
`mask_format: "word_positions"` and supply the prompt's `output_schema`; the
template must also contain `{INDEXED_POST}` exactly once. This inserts numbered
words alongside the unchanged original post. No extra instructions are added.
Each new call gets a fresh isolated context;
identical saved requests are reused as described above. OpenRouter
uses the same explicit auth/output-cap rules as other pipeline modes.

From the repository root, with your config saved as `mask-config.json`:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 sse_multivector/extraction_pipeline.py masks mask-config.json
```

The command saves raw receipts, verifies request isolation, validates exact source
fragments and their order, and writes the existing mask-review format to
`mask-run/review.json`. In legacy fragment mode it flags ambiguous occurrence
positions and displays the first occurrence compatible with source order; this
is not a model-supplied position. In word-position mode it decodes inclusive
word ranges and unique within-word selections into exact character ranges,
rejecting invalid bounds, order, overlaps and ambiguous matches. Valid empty
masks are retained in `validation.json`, alongside MPv3.43 diagnostic fields,
but omitted from the existing nonempty-only review cards. Invalid output is
never converted into an empty mask. Full URLs and encoded Nostr identifiers in returned fragments are
rejected mechanically. Semantic correctness still requires review: the tool
does not approve masks, invent assessments, edit responses, or fill user decisions.
Its compact JSON summary reports new attempts, validation counts and cumulative
token usage across all saved attempts, including failures. Reasoning tokens are
already included in output tokens; missing usage is reported rather than assumed
free. These are usage receipts, not subscription invoices.

- `--prepare-only` saves the input snapshot and exact rendered prompts in the
  manifest without reading credentials or making model calls. It still checks
  the local runner's identity; this is not a provider wire preview.
- `--collect-only` verifies saved receipts and rebuilds validation/review files
  without credentials or inference. It never adopts unrelated historical runs.
- Resume with the same command. Successful calls are reused; failed calls require
  explicit `--retry-failed`. Invalid mask text is preserved, not automatically
  repaired or regenerated.
- `concurrency` defaults to 1 and accepts 1–12. It limits active and queued work,
  not operating-system memory. Failure stops later waves; calls already running
  finish and save their receipts. A lock prevents simultaneous execution of the
  same mask run. Existing external memory limits can still wrap the command.
- A nonzero exit status and `validation.json` identify failed, invalid, or unrun
  items. Only mechanically valid masks enter the review file. A partial review
  is therefore not evidence that every requested mask succeeded.

Open the results separately:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./target/release/sse-mask-review review-masks \
  mask-run/review.json mask-run/review-session.json
```

Review decisions remain separate and are never overwritten by generation. If
additional results change a partial review, the UI rejects the old session's
fingerprint; use a new session path and preserve the earlier decisions.

The real-note experiment's older `generation.py` and `omission_calls.py`
preparation commands still require `--auth-file PATH`; they cannot launch new
service-backed runs unchanged. Use the canonical saved-batch configs above for
new calls. Their collection commands still read saved legacy runs without
invoking the retired tool. The CREC-119 launchers require a new configuration
path rather than silently reusing their archived Codex configurations.

## Historical experiments

Existing configs and results remain untouched as historical evidence. Old
`codex_binary`/`codex_home` configs cannot silently resume through pi-ai.
Choose explicit new runtime settings and a fresh run directory.

[generation_history.py](generation_history.py) only reads historical formats and
reconstructs their recorded metadata. It has no model-execution entry point.
When an old audit checks the retired runner's source hash, the source bytes are
read from a pinned Git revision and never executed. The review tool separately
recognizes legacy and new manifests, preserving their provenance checks.

The [frozen comparison launcher](run-frontier-comparison.sh) still loads the
approved ASv6.23/MPv3.5 inputs. It is an experiment-specific adapter; other agents
should use `run-model.sh` for arbitrary prompts.
