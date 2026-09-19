# General model runner

[run-model.sh](run-model.sh) sends one caller-supplied prompt through pi-ai.
It replaces the removed `codex_exec.py` execution tool. No subject, mask, title,
corpus, or model is selected for you.

Use this tool for new model calls. The [extraction pipeline](extraction_pipeline.py)
and [frozen comparison adapter](frontier_runner/runner.mjs) are callers of the
same transport, not separate model-execution implementations.

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

Unknown fields, models, reasoning settings, and unsupported transports fail
explicitly. The pinned pi-ai catalog supplies model metadata; OpenRouter entries
using `openai-completions` are supported. Other catalog transports are not silently
rerouted. DeepSeek V4.1 Flash has an explicit catalog addition because the pinned
SDK predates that release.

Schemas are checked locally without coercion, inserted defaults, removed
properties, or remote reference fetching. Draft-07, 2019-09, and 2020-12 are
supported. Provider support can be narrower: the exact schema is requested,
and a provider rejection stays a failure rather than causing a format fallback.

## Execution and credentials

### Anvil credential service

For isolated subscription credentials, run the model command inside the selected
Pi view and pass `--pi-config`:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
agent-account exec pi -- bash sse_multivector/run-model.sh \
  run request.json --send --pi-config
```

This reads Pi's native `models.json` and `auth.json` in that process's view once:
the loopback endpoint selects the account, and the token authorizes the local
service only. The service owns the OpenAI credential and renewal. Switching
`agent-account use NAME` affects future launches, not a running invocation.
No Pi/Codex source is patched. Missing or invalid local configuration fails
before sending, without falling back to bearer export or upstream access.
`--pi-config` cannot be combined with `--auth-file` or OpenRouter.

On 2026-09-19 this command completed a live `gpt-6-astra` request through
the installed service. Offline checks cover selection capture, both account
routes, credential refresh, redacted receipts and invalid configuration.

This is an explicit mode, not a change to the default invocation. Existing batch
commands and the frozen comparison adapter do not yet pass `--pi-config`;
wrapping those commands in `agent-account exec pi` alone is insufficient. Their
callers still need migration before old credentials can be retired. Preview
remains credential-free. Existing conversations and stored credentials are not
modified by this integration.

### Native credentials without service routing

Change `preview` to `run --send` to execute. Subscription calls additionally
require `--auth-file /absolute/path/auth.json`; explicitly select the intended
Codex or pi OAuth file. The runner never changes accounts, refreshes credentials,
or falls back to normal OpenAI API billing.

OpenRouter reads only `OPENROUTER_API_KEY`. Do not put credentials in request
JSON or repository files. Returned request headers redact credentials.

**A send flag is not spending approval.** Paid calls remain subject to the
repository's approved maximum spend, ledger commitment, and external provider-side
limit. Timeouts and output-token caps are not monetary hard caps.

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
configuration, missing credentials, and malformed or expired OAuth tokens fail
before sending, on standard error. The server still decides whether an otherwise
well-formed credential is authentic and authorized.

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

A prompt-batch configuration uses:

```json
{
  "schema_version": 1,
  "runner_binary": "/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-model.sh",
  "provider": "openai-codex",
  "auth_file": "/absolute/path/to/your/auth.json",
  "run_directory": "new-run",
  "model": "gpt-6-astra",
  "reasoning_effort": "low",
  "prompts": [
    {"prompt_id": "example", "text": "Your exact prompt"}
  ]
}
```

Execute with `python3 sse_multivector/extraction_pipeline.py prompt CONFIG.json`
from the repository root. For OpenRouter set `auth_file` to null and supply
`max_output_tokens`. Paths resolve relative to the configuration file.
Extraction-specific normalization, schemas, note loading, and prompt registries
belong to the workflow, not the general runner.

Batches save manifests, per-attempt results, and final output. Repeating an
unchanged configuration reuses completed jobs; failed jobs require an explicit
`--retry-failed`. Changes in inputs, settings, or transport identity require a new
run directory. Workflow-code changes also require one by default. Pipeline batch
mode retains the explicit `--runner-upgrade-reason` exception for wrapper-only
changes, recording the boundary in its upgrade ledger; this cannot change the
transport or disguise historical Codex calls as pi-ai calls.
New subject and claim manifests use schema version 2
to distinguish the new execution provenance.

The real-note experiment's `generation.py` and `omission_calls.py` preparation
commands now require `--auth-file PATH` and optionally accept `--runner-binary`.
Their collection commands still read saved legacy runs without invoking the
retired tool. The CREC-119 launchers require a new configuration path rather than
silently reusing their archived Codex configurations.

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
